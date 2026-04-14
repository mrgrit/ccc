#!/usr/bin/env python3
"""non-AI → AI 실습 동기화.

non-AI 원본에서 instruction, hint, answer, answer_detail, points, category, verify 필드를
AI 버전에 동기화한다. AI 전용 필드(bastion_prompt, script, target_vm, risk_level)는 유지.

Usage:
    python3 scripts/sync_nonai_to_ai.py          # 전체 동기화
    python3 scripts/sync_nonai_to_ai.py --dry-run # 변경 미리보기
    python3 scripts/sync_nonai_to_ai.py secops    # 특정 과정만
"""
import glob
import os
import sys
import yaml

LABS_DIR = os.path.join(os.path.dirname(__file__), "..", "contents", "labs")

COURSE_PAIRS = [
    ("attack-nonai", "attack-ai"),
    ("attack-adv-nonai", "attack-adv-ai"),
    ("secops-nonai", "secops-ai"),
    ("web-vuln-nonai", "web-vuln-ai"),
    ("compliance-nonai", "compliance-ai"),
    ("soc-nonai", "soc-ai"),
    ("soc-adv-nonai", "soc-adv-ai"),
    ("cloud-container-nonai", "cloud-container-ai"),
    ("ai-security-nonai", "ai-security-ai"),
    ("ai-safety-nonai", "ai-safety-ai"),
    ("ai-safety-adv-nonai", "ai-safety-adv-ai"),
    ("ai-agent-nonai", "ai-agent-ai"),
    ("battle-nonai", "battle-ai"),
    ("battle-adv-nonai", "battle-adv-ai"),
    ("physical-pentest-nonai", "physical-pentest-ai"),
]

# non-AI에서 AI로 복사할 필드
SYNC_FIELDS = [
    "instruction", "hint", "answer", "answer_detail",
    "points", "category", "verify",
]

# AI 전용 필드 (non-AI에서 덮어쓰지 않음)
AI_ONLY_FIELDS = [
    "bastion_prompt", "script", "target_vm", "risk_level",
]


def sync_file(nonai_path: str, ai_path: str, dry_run: bool = False) -> dict:
    """non-AI → AI 단일 파일 동기화."""
    with open(nonai_path, encoding="utf-8") as f:
        nonai = yaml.safe_load(f)
    with open(ai_path, encoding="utf-8") as f:
        ai = yaml.safe_load(f)

    nonai_steps = {s["order"]: s for s in nonai.get("steps", [])}
    ai_steps_list = ai.get("steps", [])

    synced = 0
    for ai_step in ai_steps_list:
        order = ai_step.get("order")
        if order == 99:  # multi-task 스텝은 건너뜀
            continue
        nonai_step = nonai_steps.get(order)
        if not nonai_step:
            continue

        for field in SYNC_FIELDS:
            nonai_val = nonai_step.get(field)
            ai_val = ai_step.get(field)
            if nonai_val is not None and nonai_val != ai_val:
                if not dry_run:
                    ai_step[field] = nonai_val
                synced += 1

    if synced > 0 and not dry_run:
        with open(ai_path, "w", encoding="utf-8") as f:
            yaml.dump(ai, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {"synced": synced}


def main():
    dry_run = "--dry-run" in sys.argv
    filter_course = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            filter_course = arg

    total = 0
    for nonai_name, ai_name in COURSE_PAIRS:
        if filter_course and filter_course not in nonai_name and filter_course not in ai_name:
            continue

        nonai_dir = os.path.join(LABS_DIR, nonai_name)
        ai_dir = os.path.join(LABS_DIR, ai_name)

        if not os.path.isdir(nonai_dir) or not os.path.isdir(ai_dir):
            continue

        course_synced = 0
        for nonai_file in sorted(glob.glob(os.path.join(nonai_dir, "week*.yaml"))):
            week = os.path.basename(nonai_file)
            ai_file = os.path.join(ai_dir, week)
            if not os.path.exists(ai_file):
                continue

            result = sync_file(nonai_file, ai_file, dry_run)
            course_synced += result["synced"]

        if course_synced > 0:
            total += course_synced
            print(f"{'[DRY] ' if dry_run else ''}{ai_name}: {course_synced} fields synced")

    print(f"\n{'DRY RUN — ' if dry_run else ''}Total: {total} fields synced")


if __name__ == "__main__":
    main()
