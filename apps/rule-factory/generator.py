#!/usr/bin/env python3
"""CCC Rule Factory — CTI(CVE)로부터 Suricata/Wazuh 방어 룰 자동 생성.

로드맵 P4. 3-Layer의 Master(콘텐츠 제작) 역할:
- 입력: contents/threats/*/CVE-*.json (P2 collector 결과)
- 출력:
    contents/rules/suricata/YYYY-MM-DD-<cve>.rules
    contents/rules/wazuh/YYYY-MM-DD-<cve>.xml
- 단계: staging용 생성만 (배포는 별도 승인 절차 필요)

안전 원칙:
- 자동 배포 금지 — staging 파일 생성까지만
- 생성된 룰은 반드시 `suricata -T` / `wazuh-logtest` 문법 검증 후 수동 배포
- 파괴적 액션(drop all, reset) 제한

LLM 우선순위: Anthropic Claude → Ollama Manager fallback
(battle-factory와 동일 패턴)

배포 이식성:
- 모든 경로 __file__ 기준 상대 해석
- LLM·대역 IP 등은 환경변수 override

실행:
    python3 -m apps.rule-factory.generator --cve CVE-2026-XXXX
    python3 -m apps.rule-factory.generator --latest 5
    python3 -m apps.rule-factory.generator --day 2026-04-18 --validate
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
THREATS_DIR = pathlib.Path(os.getenv("CTI_OUT_DIR", str(ROOT / "contents" / "threats")))
RULES_DIR = pathlib.Path(os.getenv("RULES_OUT_DIR", str(ROOT / "contents" / "rules")))
(RULES_DIR / "suricata").mkdir(parents=True, exist_ok=True)
(RULES_DIR / "wazuh").mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.getenv("LLM_BASE_URL", "http://192.168.0.105:11434")
MGR_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")

HOME_NET = os.getenv("SURICATA_HOME_NET", "10.20.30.0/24")
SID_BASE = int(os.getenv("SURICATA_SID_BASE", "1000000"))  # 1000000~1999999: local

# ── LLM 추상화 ──────────────────────────────────────────

def _chat_anthropic(prompt: str, system: str = "", timeout: int = 90) -> str | None:
    if not ANTHROPIC_API_KEY:
        return None
    payload = {
        "model": ANTHROPIC_MODEL, "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        }, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        for b in data.get("content") or []:
            if b.get("type") == "text":
                return b.get("text", "")
        return ""
    except Exception as e:
        print(f"[anthropic 실패, fallback: {e}]", file=sys.stderr)
        return None


def _chat_ollama(prompt: str, system: str = "", timeout: int = 120, json_mode: bool = True) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": MGR_MODEL, "messages": messages, "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2500},
    }
    if json_mode:
        body["format"] = "json"
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        return (d.get("message") or {}).get("content", "")
    except Exception as e:
        return f"[ollama 실패: {e}]"


def llm_chat(prompt: str, system: str = "", json_mode: bool = True) -> tuple[str, str]:
    """Master 우선, 실패 시 Manager fallback."""
    if ANTHROPIC_API_KEY:
        text = _chat_anthropic(prompt, system)
        if text:
            return text, f"anthropic:{ANTHROPIC_MODEL}"
    return _chat_ollama(prompt, system, json_mode=json_mode), f"ollama:{MGR_MODEL}"


# ── 시스템 프롬프트 ────────────────────────────────────

_SCHEMA = """{
  "suricata_rules": [
    "alert tcp $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS (msg:\\"...\\"; content:\\"...\\"; http_uri; classtype:web-application-attack; sid:<SID>; rev:1;)"
  ],
  "wazuh_rules": [
    {
      "id": 100200,
      "level": 8,
      "description": "...",
      "if_sid": 31100,
      "match": "...",
      "group": "web,attack,"
    }
  ],
  "notes": "룰의 작동 원리, false positive 위험, 튜닝 힌트를 한글 2-3문장"
}"""

SYSTEM_PROMPT = (
    "너는 CCC 자율보안시스템의 IDS/SIEM 룰 설계자다.\n"
    "주어진 CVE 정보로 Suricata(네트워크 IDS) + Wazuh(로그 SIEM) 방어 룰을 생성한다.\n\n"
    "## 원칙\n"
    "- Suricata: action=alert 기본 (drop 금지 — staging에서 사람 승인 후에만 drop으로 전환)\n"
    "- Wazuh: level은 5-12 범위 (12 이상 금지, 알림 폭주)\n"
    "- 외부 네트워크(EXTERNAL_NET)에서 내부($HOME_NET)로 들어오는 트래픽 탐지 중심\n"
    "- content/match는 CVE와 직접 관련된 구체 payload 패턴 (너무 일반적 패턴 금지 — false positive)\n"
    "- classtype은 suricata 기본값 활용 (web-application-attack, attempted-user, trojan-activity 등)\n"
    "- sid는 <SID>로 표기 (자동 할당됨)\n"
    "- Wazuh rule id는 100000~199999 범위 (local 규칙)\n"
    "- if_sid는 기반 룰 (31100=web log, 5716=sshd, 5500=pam 등) — 확실하지 않으면 생략\n"
    "- 파괴적/우회적 액션 금지 (drop all, reset, redirect to sinkhole)\n\n"
    "## 출력\n"
    "**JSON만 출력** (코드블록·설명 금지). 스키마:\n" + _SCHEMA
)


def build_prompt(cve: dict) -> str:
    return (
        f"## CVE\n"
        f"- ID: {cve.get('id','')}\n"
        f"- Severity: {cve.get('severity','?')} (CVSS {cve.get('cvss_score','?')})\n"
        f"- 요약: {cve.get('summary','')}\n"
        f"- 영향: {cve.get('impact','')}\n"
        f"- 공격 벡터: {cve.get('attack_vector','')}\n"
        f"- 태그: {', '.join(cve.get('tags', []))}\n\n"
        f"위 CVE에 대한 Suricata 알림 룰과 Wazuh 로그 탐지 룰을 생성하라.\n"
        f"HOME_NET={HOME_NET}"
    )


def extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*\n([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# ── 룰 저장 ────────────────────────────────────────────

_SID_COUNTER_FILE = RULES_DIR / ".sid_counter"


def _next_sid() -> int:
    """SID 전역 카운터 (충돌 방지)."""
    if _SID_COUNTER_FILE.exists():
        try:
            cur = int(_SID_COUNTER_FILE.read_text().strip())
        except Exception:
            cur = SID_BASE
    else:
        cur = SID_BASE
    nxt = cur + 1
    _SID_COUNTER_FILE.write_text(str(nxt))
    return nxt


def save_suricata_rules(cve_id: str, day: str, rules: list[str], notes: str) -> pathlib.Path:
    """Suricata .rules 파일 저장. <SID>를 고유 번호로 치환."""
    out = RULES_DIR / "suricata" / f"{day}-{cve_id.lower()}.rules"
    lines = [f"# CVE: {cve_id}", f"# 생성: battle factory (staging only)", f"# 비고: {notes}", ""]
    for r in rules:
        if "<SID>" in r:
            r = r.replace("<SID>", str(_next_sid()))
        lines.append(r)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def save_wazuh_rules(cve_id: str, day: str, rules: list[dict], notes: str) -> pathlib.Path:
    """Wazuh local_rules XML 저장. group 래핑 필수."""
    out = RULES_DIR / "wazuh" / f"{day}-{cve_id.lower()}.xml"
    lines = [f"<!-- CVE: {cve_id} -->", f"<!-- 비고: {notes} -->", ""]
    lines.append(f'<group name="cve,{cve_id.lower()},auto_generated,">')
    for r in rules:
        rid = int(r.get("id") or 100200)
        level = max(5, min(12, int(r.get("level") or 7)))
        desc = str(r.get("description") or "Auto-generated rule")
        match = str(r.get("match") or "")
        if_sid = r.get("if_sid")
        group = str(r.get("group") or "attack,")
        # XML escape — match 값은 regex지만 <, >, & 는 반드시 엔티티화
        def _xml_esc(s: str) -> str:
            return (s.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;")
                     .replace('"', "&quot;"))
        desc = _xml_esc(desc)
        match_s = _xml_esc(match)
        group_s = _xml_esc(group)
        lines.append(f'  <rule id="{rid}" level="{level}">')
        if if_sid:
            lines.append(f'    <if_sid>{int(if_sid)}</if_sid>')
        if match_s:
            lines.append(f'    <match>{match_s}</match>')
        lines.append(f'    <description>{desc}</description>')
        lines.append(f'    <group>{group_s}</group>')
        lines.append(f'  </rule>')
    lines.append(f'</group>')
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ── 검증 (선택) ────────────────────────────────────────

def validate_suricata(path: pathlib.Path) -> dict:
    """secu VM에 복사해 suricata -T 로 문법 검증 — 원격 sudo 필요. MVP 단계라 옵션."""
    # 원격 검증은 복잡하므로 1차: 로컬 문법 체크 (괄호·sid·msg 필드 존재 여부)
    issues = []
    text = path.read_text(encoding="utf-8")
    rules = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    for r in rules:
        if not re.match(r"^(alert|log|drop|pass|reject)\s+", r):
            issues.append(f"action 키워드 누락: {r[:60]}")
        if "sid:" not in r:
            issues.append(f"sid 누락: {r[:60]}")
        if "msg:" not in r:
            issues.append(f"msg 누락: {r[:60]}")
        if not r.rstrip(";").endswith(")") :
            issues.append(f"괄호 미닫힘: {r[:60]}")
    return {"path": str(path), "rules": len(rules), "issues": issues}


def validate_wazuh(path: pathlib.Path) -> dict:
    """Wazuh XML 로컬 문법 체크 (xml.etree로 파싱)."""
    import xml.etree.ElementTree as ET
    text = path.read_text(encoding="utf-8")
    try:
        # local_rules는 여러 <group> 가능, 최상위 래핑 필요
        root = ET.fromstring(f"<wazuh_local_rules>{text}</wazuh_local_rules>")
    except ET.ParseError as e:
        return {"path": str(path), "ok": False, "error": str(e)}
    groups = root.findall(".//group")
    rules = root.findall(".//rule")
    return {"path": str(path), "ok": True, "groups": len(groups), "rules": len(rules)}


# ── CVE 로드 (battle-factory와 동일) ────────────────────

def load_cve(cve_id: str) -> dict | None:
    for p in THREATS_DIR.glob(f"*/{cve_id}.json"):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def load_latest(n: int = 5) -> list[dict]:
    items = []
    for p in THREATS_DIR.glob("*/CVE-*.json"):
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    sev = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    items.sort(key=lambda x: (sev.get(x.get("severity", "UNKNOWN"), 9), -float(x.get("cvss_score") or 0)))
    return items[:n]


def load_day(day: str) -> list[dict]:
    dd = THREATS_DIR / day
    if not dd.exists():
        return []
    return [json.loads(p.read_text()) for p in sorted(dd.glob("CVE-*.json"))]


# ── 파이프라인 ──────────────────────────────────────────

def generate_rules(cve: dict, validate: bool = False) -> dict:
    cve_id = cve.get("id", "CVE-UNKNOWN")
    day = cve.get("published", "")[:10] or "2026-01-01"
    text, source = llm_chat(build_prompt(cve), SYSTEM_PROMPT)
    data = extract_json(text)
    if not data:
        return {"ok": False, "cve": cve_id, "error": "JSON 파싱 실패", "source": source}
    suri_list = [str(r) for r in (data.get("suricata_rules") or []) if r]
    wazu_list = [r for r in (data.get("wazuh_rules") or []) if isinstance(r, dict)]
    notes = str(data.get("notes") or "")
    if not suri_list and not wazu_list:
        return {"ok": False, "cve": cve_id, "error": "룰 생성 없음", "source": source}
    result = {"ok": True, "cve": cve_id, "source": source, "notes": notes}
    if suri_list:
        p1 = save_suricata_rules(cve_id, day, suri_list, notes)
        result["suricata_path"] = str(p1)
        result["suricata_count"] = len(suri_list)
        if validate:
            result["suricata_validation"] = validate_suricata(p1)
    if wazu_list:
        p2 = save_wazuh_rules(cve_id, day, wazu_list, notes)
        result["wazuh_path"] = str(p2)
        result["wazuh_count"] = len(wazu_list)
        if validate:
            result["wazuh_validation"] = validate_wazuh(p2)
    return result


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cve")
    g.add_argument("--latest", type=int)
    g.add_argument("--day")
    ap.add_argument("--validate", action="store_true", help="생성 후 로컬 문법 체크")
    args = ap.parse_args()

    if args.cve:
        doc = load_cve(args.cve)
        if not doc:
            print(f"[ERR] CVE 파일 없음: {args.cve}", file=sys.stderr)
            sys.exit(1)
        targets = [doc]
    elif args.latest:
        targets = load_latest(args.latest)
    elif args.day:
        targets = load_day(args.day)

    if not targets:
        print("[ERR] 대상 없음", file=sys.stderr)
        sys.exit(1)

    print(f"[rule-factory] {len(targets)}건 생성 시작 "
          f"(LLM: {'Anthropic Master' if ANTHROPIC_API_KEY else 'Ollama Manager(' + MGR_MODEL + ')'})")
    ok = 0
    for cve in targets:
        print(f"  → {cve['id']}", end=" ", flush=True)
        r = generate_rules(cve, validate=args.validate)
        if r["ok"]:
            ok += 1
            extras = []
            if r.get("suricata_count"):
                extras.append(f"suricata {r['suricata_count']}건")
            if r.get("wazuh_count"):
                extras.append(f"wazuh {r['wazuh_count']}건")
            print(f"OK {' · '.join(extras)} [{r['source']}]")
            if args.validate:
                sv = r.get("suricata_validation") or {}
                wv = r.get("wazuh_validation") or {}
                if sv.get("issues"):
                    print(f"    ⚠ suricata 문제 {len(sv['issues'])}: {sv['issues'][:2]}")
                if not wv.get("ok", True):
                    print(f"    ⚠ wazuh 파싱 실패: {wv.get('error','')[:100]}")
        else:
            print(f"FAIL {r.get('error','')}")
    print(f"\n결과: {ok}/{len(targets)} 성공")


if __name__ == "__main__":
    main()
