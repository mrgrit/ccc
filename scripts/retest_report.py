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
QUEUE_R3 = ROOT / "results/retest/queue_r3.tsv"
CURSOR_R3 = ROOT / "results/retest/cursor_r3.txt"
LOG_R3 = ROOT / "results/retest/run_r3.log"


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

    # ── R3 round 진행 (queue_r3.tsv 별도 추적) ─────────────────────
    if QUEUE_R3.exists() and CURSOR_R3.exists():
        try:
            r3_total = sum(1 for _ in open(QUEUE_R3) if _.strip())
            r3_cur = int(open(CURSOR_R3).read().strip() or 0)
            r3_pct = r3_cur*100//max(r3_total,1)
            lines.append("## R3 round (post-R2 잔여 비-pass 재테스트)")
            lines.append("")
            lines.append(f"- 진행: **{r3_cur}/{r3_total}** ({r3_pct}%)")
            lines.append(f"- 잔여: {r3_total - r3_cur} steps")
            # 마지막 5건
            if LOG_R3.exists():
                tail = []
                with open(LOG_R3, errors='replace') as f:
                    for L in f:
                        if L.startswith('[') and 'R3 #' in L:
                            tail.append(L.rstrip())
                tail = tail[-5:]
                if tail:
                    lines.append("")
                    lines.append("**최근 5 step**:")
                    lines.append("```")
                    lines.extend(tail)
                    lines.append("```")
            lines.append("")
        except Exception as _e:
            lines.append(f"<!-- R3 진행 읽기 오류: {_e} -->")
            lines.append("")

    lines.append("---")
    lines.append("*자동 생성: scripts/retest_report.py*")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({cursor}/{qsize} processed, fixed={fixed}, pass delta={pass_delta:+d})")

    # 5e) KPI 자동 record — pass_rate / fail_rate / fixed 를 KPI 노드 history 에 기록
    try:
        _record_retest_kpis(overall, fixed, cursor, qsize)
    except Exception as _e:
        print(f"  [warn] KPI record skipped: {_e}")


# ── Phase 5e: KPI 자동 record ─────────────────────────────────────────────

_KPI_SEEDS = {
    "kpi:retest:pass_rate":   {"name": "Retest pass rate", "target": 75.0, "unit": "%"},
    "kpi:retest:fail_rate":   {"name": "Retest fail rate", "target": 15.0, "unit": "%"},
    "kpi:retest:fix_count":   {"name": "Retest 누적 fix 건수", "target": 500, "unit": "건"},
    "kpi:retest:processed":   {"name": "Retest 누적 처리 건수", "target": 3089, "unit": "건"},
}


def _ensure_kpi_seeds():
    """KPI 노드 4종이 KG 에 없으면 자동 생성. 첫 호출 시 1회."""
    try:
        from packages.bastion.graph import get_graph
        g = get_graph()
    except Exception:
        return
    for kid, spec in _KPI_SEEDS.items():
        try:
            existing = g.get_node(kid)
            if existing:
                continue
            g.add_node(kid, "KPI", spec["name"],
                       content={"target": spec["target"],
                                "unit": spec["unit"],
                                "measures": "Bastion retest 자동 측정",
                                "history": []},
                       meta={"tier": "strategic", "auto_seeded": True})
        except Exception:
            pass


def _record_retest_kpis(overall, fixed, cursor, qsize):
    """work_domain.record_kpi 호출. 실패 시 silent."""
    _ensure_kpi_seeds()
    try:
        from packages.bastion.work_domain import record_kpi
    except Exception:
        return
    total = overall.get("total", 0) or 1
    pass_rate = overall["pass"] * 100 / total
    fail_rate = overall["fail"] * 100 / total
    note = f"cursor={cursor}/{qsize}"
    record_kpi("kpi:retest:pass_rate", round(pass_rate, 2), note=note)
    record_kpi("kpi:retest:fail_rate", round(fail_rate, 2), note=note)
    record_kpi("kpi:retest:fix_count", float(fixed), note=note)
    record_kpi("kpi:retest:processed", float(cursor), note=note)


if __name__ == "__main__":
    main()
