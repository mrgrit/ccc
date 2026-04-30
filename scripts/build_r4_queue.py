#!/usr/bin/env python3
"""R4 round queue 생성 — bastion_test_progress.json 의 non-pass step 추출.

Fix #1~#5 모두 deployed 상태에서 R4 round 재측정용 queue 생성.
- 입력: bastion_test_progress.json (best_verdict 있으면 우선, 없으면 status)
- 출력: results/retest/queue_r4.tsv (course\\tweek\\torder)
- 우선순위: error > no_execution > qa_fallback > fail (다른 fail 패턴 분리)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CCC = Path(__file__).resolve().parent.parent
PROG = CCC / "bastion_test_progress.json"
OUT = CCC / "results/retest/queue_r4.tsv"


def main() -> None:
    if not PROG.exists():
        print(f"ERROR: {PROG} not found", file=sys.stderr)
        sys.exit(1)
    d = json.loads(PROG.read_text())
    res = d.get("results", {})
    # priority order — error 먼저 (인프라 불안정 회복), 그 다음 no_exec, qa_fallback, fail
    bucket: dict[str, list[tuple[str, str, str]]] = {
        "error": [], "no_execution": [], "qa_fallback": [], "fail": [],
    }
    for course, weeks in sorted(res.items()):
        for week, steps in sorted(weeks.items()):
            for order, s in sorted(steps.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                st = s.get("best_verdict") or s.get("status", "unk")
                if st in bucket:
                    bucket[st].append((course, week, order))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with OUT.open("w") as f:
        for cat in ("error", "no_execution", "qa_fallback", "fail"):
            for course, week, order in bucket[cat]:
                f.write(f"{course}\t{week}\to{order}\n")
                total += 1
    by_cat = {k: len(v) for k, v in bucket.items()}
    print(f"Wrote {OUT} (total {total})")
    print(f"By verdict: {by_cat}")


if __name__ == "__main__":
    main()
