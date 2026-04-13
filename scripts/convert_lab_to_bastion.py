#!/usr/bin/env python3
"""AI 실습 YAML 파일에 bastion 자연어 프롬프트 추가

변환 전략:
1. 기존 script는 유지 (auto-verify용)
2. 각 단계에 bastion_prompt 필드 추가 — 학생이 bastion 채팅으로 같은 작업 수행
3. 기존 script의 LLM URL을 bastion 프록시로 교체 (호환성)
4. hint에 "또는 bastion에 요청하세요" 안내 추가
5. verify expect가 영어 단어이고 /ask 변환된 경우 → 한국어/빈 값으로 완화

bastion 접속 방법:
  - TUI: python apps/bastion/main.py
  - API: POST http://localhost:8003/chat -d '{"message": "..."}'
  - API (/ask): POST http://localhost:8003/ask -d '{"message": "..."}'
  - Ollama 호환: POST http://localhost:8003/api/generate (기존 스크립트 호환)

사용법:
    python3 scripts/convert_lab_to_bastion.py [--dry-run] [--verbose]
    python3 scripts/convert_lab_to_bastion.py --file contents/labs/ai-security-ai/week01.yaml
"""
import glob
import os
import re
import sys
import argparse
import yaml

BASTION_URL_VAR = "${BASTION_URL:-http://localhost:8003}"

STATUS_PATTERNS = ["api/version", "api/tags", "api/show"]

# 영어 expect 단어 → 한국어 또는 완화
ENGLISH_EXPECTS_TO_RELAX = {
    "I": "",  # LLM 자기소개에서 "I" → 아무 출력이나 OK
    "injection": "인젝션",
    "security": "보안",
    "agent": "에이전트",
    "attack": "",
    "Artificial Intelligence": "인공지능",
    "TEMP=": "",  # temperature 비교는 형식 의존적
    "temperature": "",
}


def is_status_check(script: str) -> bool:
    return any(p in script for p in STATUS_PATTERNS)


def has_llm_call(script: str) -> bool:
    return any(p in script for p in ["LLM_URL", "api/generate", "api/chat", "11434"])


def is_simple_curl(script: str) -> bool:
    """단순 curl 한 줄 (복잡한 Python 로직 없음)"""
    lines = [l.strip() for l in script.splitlines() if l.strip()]
    has_logic = any(re.match(r"^(if |for |def |class |while |try:|import )", l) for l in lines)
    return "curl" in script and not has_logic


def extract_prompt_from_generate(script: str) -> str | None:
    m = re.search(r'"prompt"\s*:\s*"([^"]{10,})"', script)
    return m.group(1) if m else None


def extract_user_message(script: str) -> str | None:
    matches = re.findall(r'"role"\s*:\s*"user"\s*,\s*"content"\s*:\s*"([^"]{5,})"', script)
    return matches[-1] if matches else None


def generate_bastion_prompt(step: dict, script: str, instruction: str) -> str:
    """단계 내용에서 bastion 자연어 프롬프트 생성"""
    # 이미 있으면 유지
    if step.get("bastion_prompt"):
        return step["bastion_prompt"]

    # 스크립트에서 프롬프트 추출
    raw_prompt = None
    if "api/generate" in script:
        raw_prompt = extract_prompt_from_generate(script)
    elif "api/chat" in script or "urllib" in script:
        raw_prompt = extract_user_message(script)

    if raw_prompt and len(raw_prompt) > 10:
        return raw_prompt

    # instruction을 기반으로 bastion 프롬프트 생성
    # instruction에서 핵심 작업 추출
    instr = instruction.strip()
    if instr:
        # "하시오", "하라", "하세요" 등 명령형 → bastion에 요청하는 형태로
        bp = re.sub(r"(하시오|하라|하세요|하라\.?)\.?\s*$", "해줘", instr)
        bp = re.sub(r"하시오\s*\.", "해줘", bp)
        return bp[:200]

    return instruction[:200]


def url_replace_script(script: str) -> str:
    """스크립트 내 LLM URL → bastion 프록시 URL"""
    new = re.sub(r"\$\{LLM_URL[^}]*\}", BASTION_URL_VAR, script)
    new = re.sub(r"http://(?:10\.20\.30\.200|localhost):11434", "http://localhost:8003", new)
    return new


def relax_verify_expect(expect: str, script: str) -> str:
    """영어 expect 완화 — bastion이 한국어로 답하기 때문"""
    if not expect:
        return expect
    # 복잡한 구현 스크립트 (BLOCKED, SAFE, Analysis:) → 유지
    if expect in ("BLOCKED", "SAFE", "Analysis:", "Analysis", "DENY", "BLOCK",
                  "VERDICT", "PHONE", "Monitoring", "Bypass rate", "prompt_hash", "Score:"):
        return expect
    # 영어 단어 완화
    relaxed = ENGLISH_EXPECTS_TO_RELAX.get(expect)
    if relaxed is not None:
        return relaxed
    return expect


def add_bastion_hint(hint: str) -> str:
    """힌트에 bastion 사용 안내 추가"""
    if not hint or "bastion" in hint.lower():
        return hint
    return hint + "\n\n**bastion 사용**: bastion 채팅에 자연어로 요청하거나 `POST http://localhost:8003/ask`를 사용하세요."


def convert_yaml_file(filepath: str, dry_run: bool = False) -> dict:
    """YAML 파일 변환 — bastion_prompt 추가 + URL 교체 + verify 완화"""
    with open(filepath, "r") as f:
        data = yaml.safe_load(f)

    if not data or "steps" not in data:
        return {"file": filepath, "status": "skip"}

    changes = []
    for step in data["steps"]:
        script = step.get("script", "")
        instruction = step.get("instruction", "")

        if not has_llm_call(script):
            continue

        step_changes = []

        # 1. bastion_prompt 추가 (status check가 아닌 경우만)
        if not step.get("bastion_prompt") and not is_status_check(script):
            bp = generate_bastion_prompt(step, script, instruction)
            if bp:
                step["bastion_prompt"] = bp
                step_changes.append("bastion_prompt")

        # 2. hint에 bastion 안내 추가
        old_hint = step.get("hint", "")
        new_hint = add_bastion_hint(old_hint)
        if new_hint != old_hint:
            step["hint"] = new_hint
            step_changes.append("hint")

        # 3. script URL 교체
        new_script = url_replace_script(script)
        if new_script != script:
            step["script"] = new_script
            step_changes.append("script-url")

        # 4. answer URL 교체
        answer = step.get("answer", "")
        if answer:
            new_answer = url_replace_script(answer)
            if new_answer != answer:
                step["answer"] = new_answer
                step_changes.append("answer-url")

        # 5. verify expect 완화 (단순 curl은 LLM이 한국어로 답하므로)
        verify = step.get("verify", {})
        if verify and is_simple_curl(script):
            old_expect = verify.get("expect", "")
            new_expect = relax_verify_expect(old_expect, script)
            if new_expect != old_expect:
                verify["expect"] = new_expect
                step["verify"] = verify
                step_changes.append(f"verify:{old_expect!r}→{new_expect!r}")

        if step_changes:
            changes.append({"order": step.get("order"), "changes": step_changes})

    if not changes:
        return {"file": filepath, "status": "no-change"}

    if not dry_run:
        with open(filepath, "w") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False, width=200)

    return {"file": filepath, "status": "changed", "steps_changed": len(changes), "details": changes[:3]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dir", default="contents/labs")
    parser.add_argument("--pattern", default="*-ai")
    parser.add_argument("--file", help="Single file")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if args.file:
        files = [args.file]
    else:
        files = sorted(glob.glob(os.path.join(args.dir, args.pattern, "*.yaml")))

    print(f"Processing {len(files)} files {'(dry-run)' if args.dry_run else ''}...")

    stats = {"changed": 0, "no-change": 0, "skip": 0}
    for f in files:
        result = convert_yaml_file(f, args.dry_run)
        status = result["status"]
        stats[status] = stats.get(status, 0) + 1
        if status == "changed":
            n = result.get("steps_changed", 0)
            name = f"{os.path.basename(os.path.dirname(f))}/{os.path.basename(f)}"
            print(f"  ✓ {name}: {n} steps")
            if args.verbose:
                for d in result.get("details", []):
                    print(f"    Step {d['order']}: {', '.join(d['changes'])}")

    print(f"\nDone: {stats['changed']} files changed, {stats['no-change']} unchanged")


if __name__ == "__main__":
    main()
