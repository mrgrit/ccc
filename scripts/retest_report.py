#!/usr/bin/env python3
"""Generate retest progress report.

Reads bastion_test_progress.json + results/retest/baseline.json + cursor.txt,
emits results/retest/report.md that can be committed/pushed.
"""
from __future__ import annotations
import json, pathlib, time, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROG = ROOT / "bastion_test_progress.json"
BASE = ROOT / "results/retest/baseline.json"
QUEUE = ROOT / "results/retest/queue.tsv"
CURSOR = ROOT / "results/retest/cursor.txt"
OUT = ROOT / "results/retest/report.md"


def count(progress):
    per_course = collections.defaultdict(lambda: collections.Counter())
    overall = collections.Counter()
    for course, weeks in progress["results"].items():
        if not isinstance(weeks, dict): continue
        for week, steps in weeks.items():
            if not isinstance(steps, dict): continue
            for o, v in steps.items():
                if not isinstance(v, dict): continue
                st = v.get("status", "")
                if not st: continue
                per_course[course][st] += 1
                per_course[course]["total"] += 1
                overall[st] += 1
                overall["total"] += 1
    return overall, per_course


def load_queue_statuses():
    """Re-read current status of each queued step."""
    prog = json.load(open(PROG))
    flips = collections.Counter()
    by_prev = collections.defaultdict(lambda: collections.Counter())
    with open(QUEUE) as f:
        lines = [l.rstrip("\n").split("\t") for l in f if l.strip()]
    for course, wk, order, prev in lines:
        wkey = f"week{int(wk):02d}"
        v = prog["results"].get(course, {}).get(wkey, {}).get(order) or \
            prog["results"].get(course, {}).get(wkey, {}).get(int(order), {})
        cur = (v or {}).get("status", "?")
        by_prev[prev][cur] += 1
        flips[(prev, cur)] += 1
    return by_prev, flips, len(lines)


def main():
    prog = json.load(open(PROG))
    base = json.load(open(BASE))
    cursor = int(open(CURSOR).read().strip() or 0) if CURSOR.exists() else 0
    overall, per_course = count(prog)
    by_prev, flips, qsize = load_queue_statuses()

    baseline_counts = base["baseline"]
    pass_delta = overall["pass"] - baseline_counts["pass"]
    fail_delta = overall["fail"] - baseline_counts["fail"]
    qa_delta = overall["qa_fallback"] - baseline_counts["qa_fallback"]
    nx_delta = overall["no_execution"] - baseline_counts["no_execution"]

    # flip accounting — only steps that have been revisited (cursor-many)
    fixed = sum(by_prev[prev].get("pass", 0) for prev in ["fail", "qa_fallback", "no_execution", "error"])
    still_broken = sum(by_prev[prev].get(cur, 0) for prev in by_prev for cur in by_prev[prev] if cur != "pass")

    lines = [
        f"# Bastion Retest Progress",
        "",
        f"생성: {time.strftime('%Y-%m-%d %H:%M:%S')} (KST)",
        f"세션 시작: {base.get('started_at', '-')}",
        f"진행: **{cursor}/{qsize}** ({cursor*100//max(qsize,1)}%)",
        "",
        "## 전체 pass 추이",
        "",
        f"| 지표 | Baseline | 현재 | Δ |",
        f"|------|----------|------|---|",
        f"| pass | {baseline_counts['pass']} | {overall['pass']} | **{pass_delta:+d}** |",
        f"| fail | {baseline_counts['fail']} | {overall['fail']} | {fail_delta:+d} |",
        f"| qa_fallback | {baseline_counts['qa_fallback']} | {overall['qa_fallback']} | {qa_delta:+d} |",
        f"| no_execution | {baseline_counts['no_execution']} | {overall['no_execution']} | {nx_delta:+d} |",
        "",
        f"**전체 케이스** {overall['total']} · **전체 pass율** {overall['pass']*100/max(overall['total'],1):.1f}%",
        "",
        "## Retest 큐 플립 현황",
        "",
        "| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |",
        "|------|------|------|-------------|--------------|--------|",
    ]
    for prev in ["fail", "qa_fallback", "no_execution", "error"]:
        row = by_prev.get(prev, {})
        same_prev = row.get(prev, 0)
        prev_total = sum(row.values())
        # 미진행 = queue 항목 중 아직 baseline 상태 그대로(plus 아직 retest 전은 current==prev)
        pass_ = row.get("pass", 0)
        fail_ = row.get("fail", 0)
        qa_ = row.get("qa_fallback", 0)
        nx_ = row.get("no_execution", 0)
        lines.append(f"| {prev} ({prev_total}) | **{pass_}** | {fail_} | {qa_} | {nx_} | - |")
    lines.append("")
    lines.append(f"**개선 누적**: fail/qa/noexec → pass = **{fixed}** 건")
    lines.append("")

    # per-course table
    lines.append("## 과목별 현재")
    lines.append("")
    lines.append("| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |")
    lines.append("|------|------|------|------|-------|---------|--------|")
    for c in sorted(per_course.keys()):
        cc = per_course[c]
        total = cc["total"]
        p = cc["pass"]
        lines.append(f"| {c} | {total} | {p} | {cc['fail']} | {cc['qa_fallback']} | {cc['no_execution']} | {p*100/max(total,1):.0f}% |")
    lines.append("")
    lines.append("---")
    lines.append("*자동 생성: scripts/retest_report.py*")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({cursor}/{qsize} processed, fixed={fixed}, pass delta={pass_delta:+d})")


if __name__ == "__main__":
    main()
