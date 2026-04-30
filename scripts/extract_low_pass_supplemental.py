#!/usr/bin/env python3
"""autonomous-ai + physical-pentest-ai 의 비-pass step 추출 + queue 생성."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "bastion_test_progress.json"

d = json.loads(PROGRESS.read_text())
results = d.get("results", {})

for course in ("autonomous-ai", "physical-pentest-ai"):
    weeks = results.get(course, {})
    queue = []
    verdicts = {}
    for wk, ords in weeks.items():
        for od, info in ords.items():
            if od == "99":
                continue
            v = info.get("status", "")
            verdicts[v] = verdicts.get(v, 0) + 1
            if v != "pass":
                queue.append((wk, int(od), v))
    queue.sort(key=lambda x: (int(x[0].replace("week", "")), x[1]))

    out = ROOT / f"results/retest/queue_r3_{course.replace('-ai', '')}_supplemental.tsv"
    with out.open("w") as f:
        for wk, od, _ in queue:
            w = wk.replace("week", "w") if wk.startswith("week") else wk
            f.write(f"{course}\t{w}\to{od}\n")

    total = sum(verdicts.values())
    print(f"{course}: total {total}, queue {len(queue)}")
    for v, c in sorted(verdicts.items(), key=lambda x: -x[1]):
        print(f"  {v}: {c}")
    print(f"  → {out.relative_to(ROOT)}")
    print()
