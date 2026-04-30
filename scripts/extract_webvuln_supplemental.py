#!/usr/bin/env python3
"""web-vuln-ai 의 비-pass step 을 supplemental queue 로 추출."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "bastion_test_progress.json"
OUT = ROOT / "results/retest/queue_r3_webvuln_supplemental.tsv"

d = json.loads(PROGRESS.read_text())
results = d.get("results", {})
wv = results.get("web-vuln-ai", {})

queue = []
verdicts = {"pass": 0, "fail": 0, "error": 0, "no_execution": 0, "qa_fallback": 0}
for week, weeks in wv.items():
    for order, info in weeks.items():
        if order == "99":
            continue
        v = info.get("status", "")
        verdicts[v] = verdicts.get(v, 0) + 1
        if v != "pass":
            queue.append((week, int(order), v))

queue.sort(key=lambda x: (int(x[0].replace("week", "")), x[1]))

with OUT.open("w") as f:
    for week, order, v in queue:
        w = week.replace("week", "w") if week.startswith("week") else week
        f.write(f"web-vuln-ai\t{w}\to{order}\n")

print(f"web-vuln-ai 전체 step (week01-15, exclude order 99): {sum(verdicts.values())}")
for v, c in sorted(verdicts.items(), key=lambda x: -x[1]):
    print(f"  {v}: {c}")
print(f"queue → {OUT.relative_to(ROOT)}: {len(queue)} cases")
