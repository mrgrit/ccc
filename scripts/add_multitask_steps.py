#!/usr/bin/env python3
"""AI 실습 YAML에 multi-task 복합 스텝(order:99) 추가.

각 주차의 bastion_prompt를 3~5개 묶어 하나의 복합 프롬프트로 구성.
Bastion의 다중 작업 처리 능력을 검증하기 위한 테스트 케이스.

Usage:
    python3 scripts/add_multitask_steps.py
    python3 scripts/add_multitask_steps.py --dry-run
"""
import glob
import os
import sys
import yaml

LABS_DIR = os.path.join(os.path.dirname(__file__), "..", "contents", "labs")

COURSES = [
    "attack-ai", "attack-adv-ai", "secops-ai", "web-vuln-ai", "compliance-ai",
    "soc-ai", "soc-adv-ai", "cloud-container-ai", "ai-security-ai", "ai-safety-ai",
    "ai-safety-adv-ai", "ai-agent-ai", "battle-ai", "battle-adv-ai", "physical-pentest-ai",
]

MAX_GROUP = 5  # 복합 프롬프트에 묶을 최대 스텝 수


def build_multitask_prompt(steps: list[dict]) -> str:
    """스텝들의 bastion_prompt를 묶어 복합 프롬프트 생성."""
    prompts = []
    for i, s in enumerate(steps, 1):
        bp = s.get("bastion_prompt", "")
        if bp:
            prompts.append(f"{i}) {bp}")
    return "다음 작업들을 순서대로 수행해줘:\n" + "\n".join(prompts)


def process_file(yaml_path: str, dry_run: bool = False) -> dict:
    """단일 YAML 파일에 multi-task 스텝 추가. 이미 있으면 스킵."""
    with open(yaml_path, encoding="utf-8") as f:
        lab = yaml.safe_load(f)

    steps = lab.get("steps", [])

    # 이미 multi_task 스텝이 있으면 스킵
    if any(s.get("category") == "multi_task" for s in steps):
        return {"file": yaml_path, "action": "skip", "reason": "already_exists"}

    # bastion_prompt가 있는 스텝만 추출 (최대 MAX_GROUP개)
    valid_steps = [s for s in steps if s.get("bastion_prompt")]
    group = valid_steps[:MAX_GROUP]

    if len(group) < 2:
        return {"file": yaml_path, "action": "skip", "reason": "too_few_steps"}

    multi_prompt = build_multitask_prompt(group)

    multi_step = {
        "order": 99,
        "instruction": f"[Multi-task] 이번 주 핵심 작업 {len(group)}개를 한 번에 수행하라.",
        "bastion_prompt": multi_prompt,
        "hint": "복합 작업은 Bastion이 순서대로 계획하고 실행해야 한다",
        "category": "multi_task",
        "points": len(group) * 10,
        "verify": {"type": "output_contains", "expect": "", "field": "stdout"},
        "target_vm": group[0].get("target_vm", "attacker"),
        "risk_level": "low",
        "answer": "",
        "answer_detail": f"Bastion이 {len(group)}개 작업을 순차적으로 계획(planning)하고 실행(executing)한 뒤 종합 분석(validating)하는 다단계 작업.",
        "script": "",
    }

    if not dry_run:
        steps.append(multi_step)
        lab["steps"] = steps
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(lab, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {"file": yaml_path, "action": "added", "group_size": len(group),
            "prompt_preview": multi_prompt[:120]}


def main():
    dry_run = "--dry-run" in sys.argv
    added = 0
    skipped = 0

    for course in COURSES:
        course_dir = os.path.join(LABS_DIR, course)
        if not os.path.isdir(course_dir):
            print(f"[SKIP] {course} — directory not found")
            continue

        for yaml_file in sorted(glob.glob(os.path.join(course_dir, "week*.yaml"))):
            result = process_file(yaml_file, dry_run)
            week = os.path.basename(yaml_file).replace(".yaml", "")

            if result["action"] == "added":
                added += 1
                print(f"[{'DRY' if dry_run else 'ADD'}] {course}/{week} — {result['group_size']} steps grouped")
            else:
                skipped += 1

    print(f"\n{'DRY RUN — ' if dry_run else ''}Done: {added} added, {skipped} skipped")


if __name__ == "__main__":
    main()
