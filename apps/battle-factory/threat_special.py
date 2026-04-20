#!/usr/bin/env python3
"""CVE 승인 시 관련 과목에 '최신 보안이슈' 특강 자동 생성.

입력: approved CVE → CVE의 courses 매핑 (예: "C3 web-vuln", "C6 cloud-container")
생성물:
  contents/education/<course>/latest-threats/<cve_id>/
    lecture.md   — 상세 분석 + 대응 교안
    lab.yaml     — 실습 시나리오 (bastion 검증 가능)

LLM: Master(Claude) 우선, Ollama Manager fallback.

배포 이식성:
- 모든 경로 __file__ 상대 해석
- LLM env override 가능
"""
from __future__ import annotations
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
EDU_DIR = ROOT / "contents" / "education"
THREATS_DIR = pathlib.Path(os.getenv("CTI_OUT_DIR", str(ROOT / "contents" / "threats")))

OLLAMA_URL = os.getenv("LLM_BASE_URL", "http://192.168.0.105:11434")
MGR_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-7")

# 과목 코드 → 디렉토리 매핑 (수집기의 COURSE_KEYWORDS 키와 일치)
COURSE_DIRS = {
    "C1 attack": "course1-attack",
    "C2 security-ops": "course2-security-ops",
    "C3 web-vuln": "course3-web-vuln",
    "C4 compliance": "course4-compliance",
    "C5 soc": "course5-soc",
    "C6 cloud-container": "course6-cloud-container",
    "C7 ai-security": "course7-ai-security",
    "C8 ai-safety": "course8-ai-safety",
    "C9 autonomous": "course9-autonomous-security",
    "C10 ai-security-agent": "course10-ai-security-agent",
    "C11 battle": "course11-battle",
    "C12 battle-advanced": "course12-battle-advanced",
    "C13 attack-adv": "course13-attack-advanced",
    "C14 soc-advanced": "course14-soc-advanced",
    "C15 ai-safety-advanced": "course15-ai-safety-advanced",
    "C16 physical": "course16-physical-pentest",
    "C17 iot": "course17-iot-security",
    "C18 autonomous-systems": "course18-autonomous-systems",
    "C19 agent-ir": "course19-agent-incident-response",
    "C20 agent-ir-adv": "course20-agent-ir-advanced",
}

# ── LLM 호출 ────────────────────────────────────────────

def _chat(prompt: str, system: str = "", json_mode: bool = False, timeout: int = 120) -> str:
    if ANTHROPIC_API_KEY:
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({
                    "model": ANTHROPIC_MODEL, "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                    "system": system or "",
                }).encode(),
                headers={"Content-Type": "application/json",
                         "x-api-key": ANTHROPIC_API_KEY,
                         "anthropic-version": "2023-06-01"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
            for b in d.get("content") or []:
                if b.get("type") == "text":
                    return b.get("text", "")
        except Exception as e:
            print(f"[anthropic 실패, fallback: {e}]", file=sys.stderr)
    # Ollama fallback
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {"model": MGR_MODEL, "messages": messages, "stream": False,
            "options": {"temperature": 0.3, "num_predict": 3500}}
    if json_mode:
        body["format"] = "json"
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/chat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        return (d.get("message") or {}).get("content", "")
    except Exception as e:
        return f"[ollama 실패: {e}]"


# ── Lecture 생성 ────────────────────────────────────────

LECTURE_SYSTEM = """너는 CCC 교육 플랫폼의 '최신 보안이슈' 특강 설계자다.
주어진 CVE에 대해 학생용 상세 분석·대응 교안을 markdown으로 작성한다.

## 구조 (markdown)
# [CVE ID] 제목

## 1. 개요
- 발표일, 심각도, 영향 범위

## 2. 취약점 상세
- 공격 원리 (재현 가능한 수준)
- 공격 벡터
- 관련 MITRE ATT&CK 매핑

## 3. 영향 받는 시스템
- 버전, 제품, 조건

## 4. 공격 시나리오 (Red 관점)
- 단계별 재현 절차
- 예시 명령/페이로드

## 5. 탐지·대응 (Blue 관점)
- Suricata/Wazuh 룰 개요
- 로그 패턴
- 차단 방법

## 6. 복구·예방
- 패치·설정 변경
- 장기 개선

## 7. 학습 체크
- 이해 확인 질문 3-5개

## 원칙
- 학생 수준 (대학 학부~석사)
- 실제 shell 명령·설정 구체적으로 제시
- 마크다운 표·코드블록 적극 활용
- 2000~3000자 분량

## 출력
Markdown 본문만 (코드블록 감싸지 말 것).
"""


def generate_lecture(cve: dict, course: str) -> str:
    prompt = (
        f"## CVE 정보\n"
        f"- ID: {cve.get('id','')}\n"
        f"- Severity: {cve.get('severity','?')} (CVSS {cve.get('cvss_score','?')})\n"
        f"- Published: {cve.get('published','')[:10]}\n"
        f"- 요약: {cve.get('summary','')}\n"
        f"- 영문 설명: {cve.get('description_en','')[:1500]}\n"
        f"- 영향: {cve.get('impact','')}\n"
        f"- 공격 벡터: {cve.get('attack_vector','')}\n"
        f"- 태그: {', '.join(cve.get('tags', []))}\n"
        f"- 대상 과목: {course}\n\n"
        f"위 CVE에 대한 '최신 보안이슈' 특강 교안을 markdown으로 작성하라."
    )
    return _chat(prompt, LECTURE_SYSTEM, timeout=120)


# ── Lab 생성 ────────────────────────────────────────────

LAB_SYSTEM = """너는 CCC 교육 플랫폼의 실습 시나리오 설계자다.
CVE에 대한 실습 Lab YAML을 JSON 형식으로 출력한다.

## 인프라 (실습 대역)
- attacker VM (10.20.30.201): nmap, hydra, sqlmap, nikto, curl
- web VM (10.20.30.80): Apache, ModSecurity, JuiceShop:3000
- secu VM (10.20.30.1): nftables, Suricata
- siem VM (10.20.30.100): Wazuh Manager

## 규칙
- 총 6~10 steps
- category: recon, scan, exploit, detect, analyze, remediate
- verify.type=output_contains, expect는 실제 shell 출력 키워드
- target_vm: attacker/web/secu/siem
- bastion_prompt: 실행형 ("siem VM에서 ...")
- script: shell 한 줄
- 파괴적 명령 금지

## 출력
JSON만 (코드블록·설명 금지):
{
  "lab_id": "latest-<cve>-<course>",
  "title": "...",
  "version": "ai",
  "course": "latest-threats",
  "week": 0,
  "description": "...",
  "difficulty": "medium",
  "duration_minutes": 60,
  "objectives": ["..."],
  "pass_threshold": 0.5,
  "steps": [
    {
      "order": 1,
      "instruction": "...",
      "hint": "...",
      "category": "recon",
      "points": 10,
      "answer": "프롬프트: ...",
      "answer_detail": "...",
      "verify": {"type": "output_contains", "expect": "...", "field": "stdout"},
      "target_vm": "attacker",
      "script": "...",
      "risk_level": "low",
      "bastion_prompt": "..."
    }
  ]
}
"""


def generate_lab(cve: dict, course: str) -> dict | None:
    prompt = (
        f"CVE {cve.get('id','')} ({cve.get('severity','?')}) 대상 과목 {course} 용 실습 Lab 생성.\n"
        f"CVE 요약: {cve.get('summary','')}\n"
        f"영향: {cve.get('impact','')}\n"
        f"공격 벡터: {cve.get('attack_vector','')}\n\n"
        f"위 CVE를 재현·탐지·대응하는 6~10 steps lab을 JSON으로 출력하라."
    )
    text = _chat(prompt, LAB_SYSTEM, json_mode=True, timeout=120)
    # JSON 추출
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# ── 저장 + 검증 ────────────────────────────────────────

def create_special_content(cve: dict, course_label: str) -> dict:
    """과목별 '최신 보안이슈' 디렉토리 생성 + lecture + lab 저장."""
    course_dir_name = COURSE_DIRS.get(course_label)
    if not course_dir_name:
        return {"ok": False, "course": course_label, "error": "unknown course label"}
    course_root = EDU_DIR / course_dir_name
    if not course_root.exists():
        return {"ok": False, "course": course_label, "error": f"course dir not found: {course_root}"}

    cve_id = cve.get("id", "CVE-UNKNOWN")
    dest = course_root / "latest-threats" / cve_id
    dest.mkdir(parents=True, exist_ok=True)

    # Lecture
    lecture_md = generate_lecture(cve, course_label)
    if not lecture_md or lecture_md.startswith("[ollama 실패"):
        return {"ok": False, "course": course_label, "error": "lecture 생성 실패"}
    (dest / "lecture.md").write_text(lecture_md, encoding="utf-8")

    # Lab
    lab = generate_lab(cve, course_label)
    if lab:
        try:
            import yaml as _y
            (dest / "lab.yaml").write_text(
                _y.safe_dump(lab, allow_unicode=True, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )
        except Exception as e:
            return {"ok": True, "course": course_label, "dest": str(dest),
                    "lecture": True, "lab": False, "lab_error": str(e)}
        return {"ok": True, "course": course_label, "dest": str(dest),
                "lecture": True, "lab": True, "lab_steps": len(lab.get("steps") or [])}
    return {"ok": True, "course": course_label, "dest": str(dest), "lecture": True, "lab": False}


def generate_for_approved_threat(cve_id: str) -> list[dict]:
    """승인된 threat 1건에 대해 관련 과목 모두에 특강 생성."""
    # CVE 파일 로드
    cve = None
    for p in THREATS_DIR.glob(f"*/{cve_id}.json"):
        try:
            cve = json.loads(p.read_text(encoding="utf-8"))
            break
        except Exception:
            continue
    if not cve:
        return [{"ok": False, "error": f"CVE 파일 없음: {cve_id}"}]

    courses = cve.get("courses") or []
    if not courses:
        return [{"ok": False, "cve": cve_id, "error": "관련 과목 매핑 없음"}]

    results = []
    for course_label in courses:
        results.append(create_special_content(cve, course_label))
    return results


# ── CLI ────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cve", required=True)
    args = ap.parse_args()
    rs = generate_for_approved_threat(args.cve)
    for r in rs:
        print(r)


if __name__ == "__main__":
    main()
