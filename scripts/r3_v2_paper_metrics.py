#!/usr/bin/env python3
"""R3-V2 fix-effect 측정 → paper §6.2 표.

이전: r3_paper_metrics.py (R3 main 결과 단독)
이번: V2 결과 + R3 main 과 비교 (course 별 회복률).

Output:
- results/retest/v2_paper_metrics.json (full)
- 콘솔: 회복 표 (course × verdict before/after)
"""
from __future__ import annotations
import argparse
import json
import re
import pathlib
import collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_V2_LOG = ROOT / "results/retest/run_r3_noexec_v2.log"
DEFAULT_R3_LOG = ROOT / "results/retest/run_r3.log"
DEFAULT_R3_QUEUE = ROOT / "results/retest/queue_r3.tsv"
DEFAULT_V2_QUEUE = ROOT / "results/retest/queue_r3_noexec.tsv"
DEFAULT_OUT = ROOT / "results/retest/v2_paper_metrics.json"

VERDICT_RE = re.compile(r"VERDICT:\s+(\w+)\s+skill=(\S*)\s+elapsed=(\S+)s")
V2_CASE_RE = re.compile(r"V2 #(\d+)/(\d+)\s+(\S+)\s+(\S+)\s+(\S+)")


def parse_v2_log(path: pathlib.Path):
    """course 별 verdict 분포 + skill + elapsed."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    course_verdicts = collections.defaultdict(lambda: collections.Counter())
    course_skills = collections.defaultdict(lambda: collections.Counter())
    course_elapsed = collections.defaultdict(lambda: collections.defaultdict(list))
    overall_verdicts = collections.Counter()
    overall_skills = collections.Counter()
    overall_elapsed = collections.defaultdict(list)

    cur_course = None
    for line in lines:
        cm = V2_CASE_RE.search(line)
        if cm:
            cur_course = cm.group(3)
            continue
        vm = VERDICT_RE.search(line)
        if vm and cur_course:
            verdict = vm.group(1)
            skill = vm.group(2)
            try:
                elapsed = float(vm.group(3))
            except ValueError:
                elapsed = 0.0
            course_verdicts[cur_course][verdict] += 1
            overall_verdicts[verdict] += 1
            if skill:
                course_skills[cur_course][skill] += 1
                overall_skills[skill] += 1
            course_elapsed[cur_course][verdict].append(elapsed)
            overall_elapsed[verdict].append(elapsed)
            cur_course = None  # one verdict per case

    return {
        "course_verdicts": {c: dict(v) for c, v in course_verdicts.items()},
        "course_skills": {c: dict(s) for c, s in course_skills.items()},
        "course_elapsed_avg": {
            c: {v: round(sum(els) / len(els), 1) for v, els in vd.items()}
            for c, vd in course_elapsed.items()
        },
        "overall_verdicts": dict(overall_verdicts),
        "overall_skills": dict(overall_skills),
        "overall_elapsed_avg": {
            v: round(sum(els) / len(els), 1) for v, els in overall_elapsed.items()
        },
    }


def parse_r3_main(log: pathlib.Path, queue: pathlib.Path):
    """R3 main: queue 의 course 순서 기반 매핑."""
    text = log.read_text(encoding="utf-8", errors="ignore")
    verdicts = [m.group(1) for m in VERDICT_RE.finditer(text)]

    queue_courses = []
    if queue.exists():
        for line in queue.read_text().splitlines():
            parts = line.split("\t")
            if parts and parts[0]:
                queue_courses.append(parts[0])

    course_verdicts = collections.defaultdict(lambda: collections.Counter())
    for i, v in enumerate(verdicts):
        if i < len(queue_courses):
            course_verdicts[queue_courses[i]][v] += 1
    return {c: dict(d) for c, d in course_verdicts.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-log", type=pathlib.Path, default=DEFAULT_V2_LOG)
    ap.add_argument("--r3-log", type=pathlib.Path, default=DEFAULT_R3_LOG)
    ap.add_argument("--r3-queue", type=pathlib.Path, default=DEFAULT_R3_QUEUE)
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    v2 = parse_v2_log(args.v2_log)
    r3_main = parse_r3_main(args.r3_log, args.r3_queue)

    overall_total = sum(v2["overall_verdicts"].values())
    pass_n = v2["overall_verdicts"].get("pass", 0)
    fail_n = v2["overall_verdicts"].get("fail", 0)
    exec_n = pass_n + fail_n

    # elapsed bucket — timeout 280s 가 fix 의 dominant 효과인지 검증
    elapsed_buckets = collections.Counter()
    for els in [v2["overall_elapsed_avg"]]:
        pass  # placeholder
    # re-extract per-case elapsed
    text = args.v2_log.read_text(encoding="utf-8", errors="ignore")
    for m in VERDICT_RE.finditer(text):
        try:
            e = float(m.group(3))
        except ValueError:
            continue
        if e < 60:
            elapsed_buckets["<60s"] += 1
        elif e < 120:
            elapsed_buckets["60-120s"] += 1
        elif e < 240:
            elapsed_buckets["120-240s"] += 1
        elif e < 280:
            elapsed_buckets["240-280s (pre-fix limit)"] += 1
        elif e < 400:
            elapsed_buckets["280-400s (post-fix only)"] += 1
        elif e < 550:
            elapsed_buckets["400-550s (post-fix only)"] += 1
        else:
            elapsed_buckets[">=550s"] += 1
    over_pre_fix = sum(c for b, c in elapsed_buckets.items() if "post-fix" in b)
    pre_fix_total = overall_total
    over_pct = round(over_pre_fix / pre_fix_total, 4) if pre_fix_total else 0.0

    metrics = {
        "round": "R3-noexec-V2 (post-fix)",
        "v2_progress": overall_total,
        "v2_overall_verdicts": v2["overall_verdicts"],
        "v2_overall_pass_rate": round(pass_n / overall_total, 4) if overall_total else 0.0,
        "v2_overall_exec_rate": round(exec_n / overall_total, 4) if overall_total else 0.0,
        "v2_active_skill_count": len(v2["overall_skills"]),
        "v2_active_skills_top": sorted(v2["overall_skills"].items(), key=lambda x: -x[1])[:10],
        "v2_overall_elapsed_avg": v2["overall_elapsed_avg"],
        "v2_elapsed_buckets": dict(elapsed_buckets),
        "v2_pct_over_280s_pre_fix_limit": over_pct,
        "v2_course_breakdown": v2["course_verdicts"],
        "r3_main_course_breakdown": r3_main,
    }

    args.out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))

    # Console: course 별 비교 표
    print(f"=== V2 paper metrics → {args.out.relative_to(ROOT)} ===")
    print(f"V2 total: {overall_total} / pass {pass_n} ({pass_n/overall_total:.1%})")
    print(f"V2 active skills: {len(v2['overall_skills'])}")
    print(f"\n--- elapsed bucket (timeout fix 효과) ---")
    for b in sorted(elapsed_buckets.keys()):
        print(f"  {b:30s}  {elapsed_buckets[b]:4d}")
    print(f"\n  pre-fix 280s limit 초과: {over_pre_fix} / {pre_fix_total} ({over_pct:.1%}) → 이전 timeout 처리되었을 비율")
    print(f"\n--- Course pass rate (R3 main vs V2, V2 measured 만) ---")
    for course in sorted(v2["course_verdicts"]):
        v2c = v2["course_verdicts"].get(course, {})
        r3c = r3_main.get(course, {})
        v2_total = sum(v2c.values())
        r3_total = sum(r3c.values())
        v2_pass = v2c.get("pass", 0)
        r3_pass = r3c.get("pass", 0)
        v2_pct = (v2_pass / v2_total * 100) if v2_total else 0
        r3_pct = (r3_pass / r3_total * 100) if r3_total else 0
        delta = v2_pct - r3_pct
        marker = "★★" if delta > 15 else ("★" if delta > 5 else ("⚠️" if delta < -5 else " "))
        print(f"  {marker} {course:20s}  R3 {r3_pass:3d}/{r3_total:3d}={r3_pct:5.1f}%  →  V2 {v2_pass:3d}/{v2_total:3d}={v2_pct:5.1f}%  Δ {delta:+.1f}pt")


if __name__ == "__main__":
    main()
