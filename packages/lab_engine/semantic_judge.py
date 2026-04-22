"""lab_engine.semantic_judge — LLM 기반 semantic 채점 공통 모듈.

test_step.py (Bastion 자동 실증) + lab_engine (학생 UI 제출) +
ccc_api battle submit-mission 이 공용으로 사용.

원칙 (사용자 지침 2026-04-22):
- verify.semantic 블록에 실질 내용(intent 또는 success_criteria) 있으면 LLM 판정이 1차.
- LLM fail 시 keyword match 무관하게 fail.
- semantic 없으면 기존 keyword fallback 유지 (하위호환).
"""
from __future__ import annotations
import os
import json
import urllib.request
import re
from typing import Any

# 환경변수로 오버라이드 가능 — 내부 테스트/배포 분리용
OLLAMA_URL = os.environ.get("CCC_JUDGE_OLLAMA", "http://192.168.0.105:11434")
JUDGE_MODEL = os.environ.get("CCC_JUDGE_MODEL", "gpt-oss:120b")
JUDGE_TIMEOUT = int(os.environ.get("CCC_JUDGE_TIMEOUT", "45"))


def has_semantic(verify: dict | None) -> bool:
    """verify 블록에 실질 내용이 있는 semantic 이 들어있는지."""
    if not verify:
        return False
    sem = verify.get("semantic") or {}
    return bool(sem.get("intent") or sem.get("success_criteria"))


def llm_semantic_judge(
    instruction: str,
    verify: dict | None,
    answer: str,
    *,
    ollama_url: str | None = None,
    judge_model: str | None = None,
    timeout: int | None = None,
) -> tuple[bool, str, str]:
    """LLM 으로 응답이 step 의도에 부합하는지 판정.

    Args:
      instruction: 스텝 instruction (공개 지시문)
      verify: step.verify dict — semantic / expect / type 포함
      answer: 학생/에이전트 응답 (끝 2500자만 사용)

    Returns:
      (pass: bool, keyword: str, reason: str)
      - keyword: 응답에서 뽑은 대표 단어 (verify.expect 누적용)
      - reason: 판정 근거 한 문장
    """
    answer_trim = (answer or "")[-2500:]
    if not instruction or not answer_trim.strip():
        return False, "", "empty instruction or answer"

    verify = verify or {}
    sem = verify.get("semantic") or {}
    sem_intent = sem.get("intent", "")
    sem_success = sem.get("success_criteria") or []
    sem_methods = sem.get("acceptable_methods") or []
    sem_negative = sem.get("negative_signs") or []
    expects_raw = verify.get("expect") or []
    if isinstance(expects_raw, str):
        expects = [expects_raw] if expects_raw else []
    else:
        expects = [str(e) for e in expects_raw if str(e).strip()]

    parts = [
        "너는 보안 실습의 엄정한 채점관이다. 학생이 실습 스텝을 수행한 결과를 평가한다.",
        "아래 형식의 JSON 만 출력하라(코드블록/설명 문장 금지):",
        '{"pass": true|false, "keyword": "응답에서 핵심을 대표하는 단어(한/영)", "reason": "한문장 이유"}',
        "",
        f"## 실습 스텝 instruction\n{instruction}",
    ]
    if sem_intent:
        parts.append(f"\n## 의도(intent) — Master 기술\n{sem_intent}")
    if sem_success:
        parts.append("\n## 합격 기준(success_criteria) — 하나 이상 충족해야 pass")
        parts.extend(f"- {c}" for c in sem_success)
    if sem_methods:
        parts.append("\n## 허용 방법(acceptable_methods) — 이 중 아무 방법이라도 인정")
        parts.extend(f"- {m}" for m in sem_methods)
    if sem_negative:
        parts.append("\n## 불합격 신호(negative_signs)")
        parts.extend(f"- {n}" for n in sem_negative)
    if expects:
        parts.append("\n## 기대 키워드(expect) — 토픽 힌트, 정확 매치는 필수 아님")
        parts.append(", ".join(expects[:10]))
    parts.append(f"\n## 학생 응답 (끝 2500자)\n{answer_trim}")
    parts.append(
        "\n## 판정 규칙\n"
        "- success_criteria 중 하나 이상을 충족했거나, acceptable_methods 중 하나의 의도/방법이 응답에 드러나면 pass=true.\n"
        "- 응답이 전혀 다른 주제를 다루거나 negative_signs에 해당하면 pass=false.\n"
        "- 단순 무응답/에러 텍스트/도구 실행 실패는 pass=false.\n"
        "- 의도와 방법이 동일하면 출력 형식이 기대와 달라도 pass=true (예: JSON 대신 표, 영어 키워드 대신 한국어 설명)."
    )
    prompt = "\n".join(parts)

    base = ollama_url or OLLAMA_URL
    model = judge_model or JUDGE_MODEL
    to = timeout or JUDGE_TIMEOUT
    try:
        req = urllib.request.Request(
            f"{base}/api/chat",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 800},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=to) as r:
            body = json.loads(r.read())
        content = body.get("message", {}).get("content", "")
        parsed = json.loads(content)
        return (
            bool(parsed.get("pass")),
            str(parsed.get("keyword", "") or "").strip(),
            str(parsed.get("reason", "") or "").strip(),
        )
    except Exception as e:
        return False, "", f"judge_error: {type(e).__name__}"


def keyword_match(verify: dict | None, text: str, *, exit_code: int | None = None) -> bool:
    """하위호환용 keyword match — semantic 없는 step 의 fallback 에 사용."""
    if not verify:
        return False
    vtype = verify.get("type") or "output_contains"
    expect = verify.get("expect", "")
    expects = expect if isinstance(expect, list) else ([expect] if expect else [])
    expects = [str(e) for e in expects if str(e).strip()]

    low = (text or "").lower()
    if vtype == "output_contains":
        return bool(expects) and any(e.lower() in low for e in expects)
    if vtype == "output_regex":
        return bool(expects) and any(
            re.search(e, text or "", re.IGNORECASE) is not None for e in expects
        )
    if vtype in ("exit_code", "exit_code_zero"):
        expected_code = 0 if vtype == "exit_code_zero" else (int(expect) if str(expect).lstrip("-").isdigit() else 0)
        return exit_code is not None and exit_code == expected_code
    return bool(expects) and any(e.lower() in low for e in expects)


def semantic_first_judge(
    instruction: str,
    verify: dict | None,
    answer: str,
    *,
    exit_code: int | None = None,
    use_instruction_fallback: bool = True,
    ollama_url: str | None = None,
    judge_model: str | None = None,
) -> tuple[bool, str, str, dict]:
    """통합 판정 함수 — semantic-first 원칙.

    순서:
      1. verify.semantic 있으면 → LLM 판정이 최종 (LLM fail → fail, keyword 무시)
      2. semantic 없으면 → keyword match
      3. keyword 도 없으면 → use_instruction_fallback=True 일 때 instruction 기반 LLM 판정

    Returns:
      (pass, keyword, reason, meta)
      meta 에는 has_semantic / used_judge / verify_match 플래그
    """
    meta = {
        "has_semantic": has_semantic(verify),
        "used_judge": False,
        "verify_match": False,
    }
    kw_match = keyword_match(verify, answer, exit_code=exit_code)
    meta["verify_match"] = kw_match

    if meta["has_semantic"]:
        ok, kw, reason = llm_semantic_judge(
            instruction, verify, answer,
            ollama_url=ollama_url, judge_model=judge_model,
        )
        meta["used_judge"] = True
        return ok, kw, reason, meta

    # semantic 없음 → keyword 우선
    if kw_match:
        return True, "", "keyword_match", meta

    # keyword 도 없으면 instruction fallback (battle / 미작성 step 대비)
    if use_instruction_fallback:
        ok, kw, reason = llm_semantic_judge(
            instruction, verify, answer,
            ollama_url=ollama_url, judge_model=judge_model,
        )
        meta["used_judge"] = True
        return ok, kw, reason, meta

    return False, "", "no_semantic_and_no_keyword_match", meta
