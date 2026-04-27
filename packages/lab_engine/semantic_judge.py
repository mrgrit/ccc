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


def multi_step_judge(
    lab_steps: list[dict],
    transcript: dict | None = None,
    answers: dict[str, str] | None = None,
    *,
    ollama_url: str | None = None,
    judge_model: str | None = None,
    timeout: int | None = None,
) -> tuple[list[dict], str, str]:
    """전체 lab transcript + answers 를 1회 LLM 호출로 multi-step 채점.

    Args:
      lab_steps: [{order, instruction, points, input_mode, verify_semantic: {intent, success_criteria, ...}}]
      transcript: {commands: [{ts, cmd, stdout, stderr, exit}]}
      answers: {step_order_str: text}

    Returns:
      (step_results, overall_feedback, used_judge)
        step_results: [{order, passed, reason, feedback, graded_via}]
        overall_feedback: 전체 흐름 평가 (학생용)
        used_judge: "multi_step" / "error_fallback"
    """
    transcript = transcript or {}
    answers = answers or {}
    commands = transcript.get("commands") or []

    # transcript 합본 (8000자 제한 — context 제어)
    cmd_lines = []
    for c in commands:
        if not isinstance(c, dict):
            continue
        cmd_lines.append(f"$ {(c.get('cmd') or '')[:300]}")
        out = (c.get('stdout') or '') or (c.get('stderr') or '')
        if out:
            cmd_lines.append(out[:400])
    joined_cmds = "\n".join(cmd_lines)[:8000]

    # answers 합본
    answers_lines = []
    for k, v in answers.items():
        if (v or '').strip():
            answers_lines.append(f"[step {k}] {v[:600]}")
    joined_answers = "\n\n".join(answers_lines)[:4000]

    # 각 step 프롬프트
    step_lines = []
    for s in lab_steps:
        order = s.get("order")
        instr = (s.get("instruction") or "")[:300]
        pts = s.get("points", 0)
        mode = s.get("input_mode", "command")
        sem = s.get("verify_semantic") or {}
        intent = (sem.get("intent") or "")[:300]
        succ = sem.get("success_criteria") or []
        meth = sem.get("acceptable_methods") or []
        neg = sem.get("negative_signs") or []
        line = f"\n--- step {order} ({mode}, {pts}pts) ---\n[instruction] {instr}"
        if intent: line += f"\n[intent] {intent}"
        if succ:   line += "\n[success_criteria] " + " | ".join(c[:120] for c in succ[:5])
        if meth:   line += "\n[acceptable_methods] " + " | ".join(m[:120] for m in meth[:4])
        if neg:    line += "\n[negative_signs] " + " | ".join(n[:120] for n in neg[:3])
        step_lines.append(line)

    parts = [
        "너는 보안 실습의 엄정한 채점관이다. 학생이 lab 전체를 진행한 결과를 step별로 채점한다.",
        "출력은 다음 JSON 만 (코드블록·설명 문장 금지):",
        '{"step_results": [{"order": int, "passed": bool, "reason": "한문장", "feedback": "왜 fail / 무엇을 보강 (학습 도움)", "graded_via": "command_transcript|text_answer|both|missing"}, ...], "overall_feedback": "lab 전체 흐름·강점·약점 요약 1~2문장"}',
        "",
        "## 전체 lab steps + 합격 기준",
        *step_lines,
        "",
        "## 학생 명령 transcript (실행 흐름)",
        joined_cmds or "(commands 없음)",
        "",
        "## 학생 작성 답변 (text 모드)",
        joined_answers or "(answers 없음)",
        "",
        "## 채점 규칙",
        "- 각 step 의 input_mode 가 'command' 면 transcript 에서 해당 의도/방법 발견 시 pass.",
        "- input_mode 가 'text' 면 answers 의 해당 step 에서 의도 충족 시 pass.",
        "- success_criteria 중 1개 이상 충족 또는 acceptable_methods 의 의도 드러나면 pass=true.",
        "- negative_signs 매칭 또는 무응답이면 pass=false.",
        "- feedback 은 '왜 fail / 무엇을 보강' 1문장 — 학생 학습에 즉시 도움되는 구체적 지적.",
        "- 모든 step 의 order 를 빠짐없이 출력. 합격 step 도 reason+feedback 모두 채움.",
    ]
    prompt = "\n".join(parts)

    base = ollama_url or OLLAMA_URL
    model = judge_model or JUDGE_MODEL
    # multi-step 은 더 긴 응답 + 더 긴 timeout
    to = timeout or max(JUDGE_TIMEOUT * 2, 90)
    try:
        req = urllib.request.Request(
            f"{base}/api/chat",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 4000},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=to) as r:
            body = json.loads(r.read())
        content = body.get("message", {}).get("content", "")
        parsed = json.loads(content)
        sr = parsed.get("step_results") or []
        # 각 항목 형식 정규화
        norm = []
        for r in sr:
            try:
                norm.append({
                    "order": int(r.get("order", 0)),
                    "passed": bool(r.get("passed", False)),
                    "reason": str(r.get("reason", "")).strip(),
                    "feedback": str(r.get("feedback", "")).strip(),
                    "graded_via": str(r.get("graded_via", "")).strip(),
                })
            except Exception:
                continue
        overall = str(parsed.get("overall_feedback", "") or "").strip()
        return norm, overall, "multi_step"
    except Exception as e:
        # 실패 시 빈 결과 — caller 가 step별 fallback 결정
        return [], f"multi_step_error: {type(e).__name__}", "error_fallback"


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
