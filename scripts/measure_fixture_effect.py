"""Fixture-driven retest 효과 측정.

R3 main (no fixture) 의 동일 step 결과 vs R4-fixture 결과 비교.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = ROOT / "bastion_test_progress.json"
SAMPLE_QUEUE = ROOT / "results/retest/queue_r4_fixture_sample30.tsv"
FULL_QUEUE = ROOT / "results/retest/queue_r4_fixture_full.tsv"


def load_queue(path: Path):
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        cw, order = line.split("\t")
        course, week_str = cw.split("/")
        week = int(week_str.replace("week", ""))
        out.append((course, week, int(order)))
    return out


def lookup_status(progress: dict, course: str, week: int, order: int):
    try:
        rec = progress["results"][course][f"week{week:02d}"]
    except KeyError:
        return None
    return rec.get(str(order)) or rec.get(order)


def main(scope: str = "sample30"):
    queue_path = FULL_QUEUE if scope == "full" else SAMPLE_QUEUE
    queue = load_queue(queue_path)
    progress = json.loads(PROGRESS.read_text())

    counts = Counter()
    courses = Counter()
    skill_dist = Counter()
    pass_steps = []
    fail_steps = []
    for (course, week, order) in queue:
        rec = lookup_status(progress, course, week, order)
        if rec is None:
            counts["missing"] += 1
            continue
        status = rec.get("status", "unknown")
        skill = rec.get("skill", "unknown")
        counts[status] += 1
        courses[course] += 1
        skill_dist[(status, skill)] += 1
        ident = f"{course}/w{week:02d}/o{order}"
        if status == "pass":
            pass_steps.append(ident)
        elif status == "fail":
            fail_steps.append(ident)

    total = sum(counts.values())
    pass_rate = counts["pass"] / total * 100 if total else 0
    print(f"=== R4 Fixture Sample {scope} ({total} steps) ===")
    for st, c in counts.most_common():
        print(f"  {st}: {c} ({c/total*100:.1f}%)" if total else f"  {st}: {c}")
    print(f"\npass rate: {pass_rate:.1f}%")
    print(f"\n=== R3 main 21.54% 대비 변화: {pass_rate - 21.54:+.1f}pt ===")
    print()
    print("== top skills (status, skill) ==")
    for (s, sk), c in skill_dist.most_common(10):
        print(f"  {s}/{sk}: {c}")
    if pass_steps:
        print()
        print(f"== pass ({len(pass_steps)}) ==")
        for p in pass_steps[:10]:
            print(f"  {p}")
    if fail_steps:
        print()
        print(f"== fail ({len(fail_steps)}) ==")
        for p in fail_steps[:10]:
            print(f"  {p}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample30")
