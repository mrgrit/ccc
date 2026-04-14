#!/usr/bin/env python3
"""bastion_prompt 최적화 — qa_fallback/no_execution 패턴 수정.

문제 패턴:
1. "구현 방법과 예시를 설명해줘" → Bastion이 Q&A로 폴백
2. "구현 방법을 설명하고 예시 코드를 보여줘" → 같은 문제
3. target_vm 미지정 → 잘못된 VM으로 라우팅

수정 방법:
- instruction + script/answer 필드를 분석하여 실행 가능한 프롬프트 재생성
- target_vm을 프롬프트에 명시

Usage:
    python3 scripts/optimize_bastion_prompts.py
    python3 scripts/optimize_bastion_prompts.py --dry-run
"""
import glob
import os
import re
import sys
import yaml

LABS_DIR = os.path.join(os.path.dirname(__file__), "..", "contents", "labs")

COURSES = [
    "attack-ai", "attack-adv-ai", "secops-ai", "web-vuln-ai", "compliance-ai",
    "soc-ai", "soc-adv-ai", "cloud-container-ai", "ai-security-ai", "ai-safety-ai",
    "ai-safety-adv-ai", "ai-agent-ai", "battle-ai", "battle-adv-ai", "physical-pentest-ai",
]

VM_NAMES = {
    "attacker": "attacker VM",
    "secu": "secu VM(보안게이트웨이)",
    "web": "web VM",
    "siem": "siem VM(Wazuh)",
    "manager": "manager VM",
}

# 스크립트에서 핵심 도구 추출
TOOL_PATTERNS = [
    (r"python3", "python3 스크립트로"),
    (r"curl\s", "curl로"),
    (r"nmap\s", "nmap으로"),
    (r"grep\s", "grep으로"),
    (r"cat\s", "cat으로"),
    (r"docker\s", "docker 명령으로"),
    (r"systemctl\s", "systemctl로"),
    (r"nft\s", "nft 명령으로"),
    (r"openssl\s", "openssl로"),
    (r"nikto\s", "nikto로"),
]

# qa_fallback 유발 접미사 — 제거 대상
QA_SUFFIXES = [
    "구현 방법과 예시를 설명해줘",
    "구현 방법을 설명하고 예시 코드를 보여줘",
]


def extract_tool_hint(script: str) -> str:
    """스크립트에서 핵심 도구명 추출."""
    for pattern, hint in TOOL_PATTERNS:
        if re.search(pattern, script):
            return hint
    return ""


def optimize_prompt(step: dict) -> str | None:
    """단일 스텝의 bastion_prompt를 최적화. 변경 없으면 None 반환."""
    bp = step.get("bastion_prompt", "")
    instruction = step.get("instruction", "")
    script = step.get("script", "") or step.get("answer", "")
    target_vm = step.get("target_vm", "attacker")

    if not bp:
        return None

    new_bp = bp
    changed = False

    # 1. qa_fallback 접미사 제거 + 실행 가능한 프롬프트 생성
    for suffix in QA_SUFFIXES:
        if suffix in new_bp:
            # 접미사 앞의 핵심 내용 추출
            core = new_bp.replace(suffix, "").strip()
            if not core:
                core = instruction.split(".")[0] if instruction else bp
            # 어미 정리: "~하시오", "~하라" 등 제거
            core = re.sub(r"(을|를|하시오|해줘|하라|해라)\s*$", "", core).strip()
            # 조사 정리
            core = re.sub(r"\s+$", "", core)

            tool_hint = extract_tool_hint(script)
            vm_name = VM_NAMES.get(target_vm, f"{target_vm} VM")

            if tool_hint:
                new_bp = f"{vm_name}에서 {tool_hint} {core} 작업을 수행해줘"
            else:
                new_bp = f"{vm_name}에서 {core} 작업을 수행해줘"

            changed = True
            break

    # 2. "설명해줘"로만 끝나는데 script가 있는 경우 → 실행 프롬프트로 변환
    if not changed and new_bp.endswith("설명해줘") and script:
        # instruction의 첫 문장을 핵심으로 사용
        core = instruction.split("하시오")[0].split("하라")[0].strip() if instruction else ""
        core = re.sub(r"(을|를|해줘|해라)\s*$", "", core).strip()
        if core:
            tool_hint = extract_tool_hint(script)
            vm_name = VM_NAMES.get(target_vm, f"{target_vm} VM")
            if tool_hint:
                new_bp = f"{vm_name}에서 {tool_hint} {core} 작업을 수행해줘"
            else:
                new_bp = f"{vm_name}에서 {core} 작업을 수행해줘"
            changed = True

    # 3. 깨진 프롬프트 수정 ("가드레일을구현" 등)
    if "을구현" in new_bp or "를구현" in new_bp:
        new_bp = new_bp.replace("을구현", "을 구현").replace("를구현", "를 구현")
        changed = True

    return new_bp if changed else None


def process_file(yaml_path: str, dry_run: bool = False) -> dict:
    """단일 YAML 파일의 모든 스텝 bastion_prompt를 최적화."""
    with open(yaml_path, encoding="utf-8") as f:
        lab = yaml.safe_load(f)

    modified = 0
    for step in lab.get("steps", []):
        new_bp = optimize_prompt(step)
        if new_bp:
            if not dry_run:
                step["bastion_prompt"] = new_bp
            modified += 1

    if modified > 0 and not dry_run:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(lab, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {"file": yaml_path, "modified": modified}


def main():
    dry_run = "--dry-run" in sys.argv
    total_modified = 0
    total_files = 0

    for course in COURSES:
        course_dir = os.path.join(LABS_DIR, course)
        if not os.path.isdir(course_dir):
            continue

        course_modified = 0
        for yaml_file in sorted(glob.glob(os.path.join(course_dir, "week*.yaml"))):
            result = process_file(yaml_file, dry_run)
            if result["modified"] > 0:
                week = os.path.basename(yaml_file).replace(".yaml", "")
                course_modified += result["modified"]
                total_files += 1

        if course_modified > 0:
            total_modified += course_modified
            print(f"{'[DRY] ' if dry_run else ''}{course}: {course_modified} prompts optimized")

    print(f"\n{'DRY RUN — ' if dry_run else ''}Total: {total_modified} prompts in {total_files} files")


if __name__ == "__main__":
    main()
