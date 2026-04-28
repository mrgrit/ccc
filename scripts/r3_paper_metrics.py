#!/usr/bin/env python3
"""R3 retest 결과 → paper §6.2 표 metadata JSON.

run_r3.log 의 verdict / skill / elapsed 추출 후 paper 가 사용할 통계 계산:
- verdict 분포 (pass / fail / no_execution / qa_fallback / error)
- pass rate
- active skill 카운트 (catalog 33 중 활성)
- skill 별 사용 빈도
- 평균 elapsed
- 과목별 분포

Output: results/retest/r3_paper_metrics.json (paper-draft.md 참조)
"""
from __future__ import annotations
import json
import re
import pathlib
import collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = ROOT / "results/retest/run_r3.log"
QUEUE = ROOT / "results/retest/queue_r3.tsv"
OUT = ROOT / "results/retest/r3_paper_metrics.json"

VERDICT_RE = re.compile(r"VERDICT:\s+(\w+)\s+skill=(\S*)\s+elapsed=(\S+)s")
CASE_RE = re.compile(r"R3 #(\d+)/575\s+(\S+)\s+(\S+)\s+(\S+)")


def main():
    log_text = LOG.read_text()
    verdicts = []
    for m in VERDICT_RE.finditer(log_text):
        verdicts.append({
            "verdict": m.group(1),
            "skill": m.group(2),
            "elapsed_s": float(m.group(3)),
        })

    # case 별 course 매핑 (queue.tsv)
    queue_courses = []
    if QUEUE.exists():
        for line in QUEUE.read_text().splitlines():
            parts = line.split("\t")
            if parts and parts[0]:
                queue_courses.append(parts[0])

    # verdict 분포
    verdict_counts = collections.Counter(v["verdict"] for v in verdicts)
    total = sum(verdict_counts.values())
    pass_rate = verdict_counts.get("pass", 0) / total if total else 0.0
    exec_rate = (verdict_counts.get("pass", 0) + verdict_counts.get("fail", 0)) / total if total else 0.0

    # skill 분포 (active 카운트)
    skill_counts = collections.Counter(v["skill"] for v in verdicts if v["skill"])
    active_skills = sorted(skill_counts.keys())

    # 평균 elapsed (verdict 별)
    elapsed_by_verdict = collections.defaultdict(list)
    for v in verdicts:
        elapsed_by_verdict[v["verdict"]].append(v["elapsed_s"])
    avg_elapsed = {k: round(sum(vs) / len(vs), 1) for k, vs in elapsed_by_verdict.items() if vs}

    # 과목별 verdict (queue 와 매핑 — 단순 idx 기반)
    course_verdicts = collections.defaultdict(lambda: collections.Counter())
    for i, v in enumerate(verdicts):
        if i < len(queue_courses):
            course_verdicts[queue_courses[i]][v["verdict"]] += 1

    # paper §6.2 metadata
    metrics = {
        "round": "R3",
        "total_cases": total,
        "verdict_distribution": dict(verdict_counts),
        "pass_rate": round(pass_rate, 4),
        "execution_rate": round(exec_rate, 4),
        "active_skill_count": len(active_skills),
        "active_skills": active_skills,
        "skill_distribution": dict(skill_counts.most_common()),
        "avg_elapsed_s_by_verdict": avg_elapsed,
        "course_distribution": {
            c: dict(cnt) for c, cnt in sorted(course_verdicts.items())
        },
    }

    OUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\n=== R3 paper metrics → {OUT.relative_to(ROOT)} ===")
    print(f"total: {total} / pass: {verdict_counts.get('pass', 0)} ({pass_rate:.1%})")
    print(f"exec_rate: {exec_rate:.1%} (pass+fail / total)")
    print(f"active_skills: {len(active_skills)} / 33 catalog")
    print(f"top 5 skill:")
    for sk, n in skill_counts.most_common(5):
        print(f"  {sk}: {n}")
    print(f"avg elapsed (pass): {avg_elapsed.get('pass', 0):.1f}s")
    print(f"avg elapsed (fail): {avg_elapsed.get('fail', 0):.1f}s")


if __name__ == "__main__":
    main()
