#!/usr/bin/env python3
"""Extract attack-ai ERROR cases from R3 main log → supplemental queue.

R3 main 의 attack-ai 94 ERROR (Connection refused / Remote end closed) 를
재측정용 queue 로 추출. V2 driver 와 동일한 형식 (course\twk\torder).
"""
from __future__ import annotations
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = ROOT / "results/retest/run_r3.log"
OUT = ROOT / "results/retest/queue_r3_attack_supplemental.tsv"

# pattern: R3 #N/T course wW oO (...)
RX = re.compile(r"R3 #\d+/\d+ ([\w-]+) (w\d+) (o\d+)")

text = LOG.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

cases = []
for i, line in enumerate(lines):
    if "VERDICT: error" not in line:
        continue
    # find preceding R3 #N marker
    for j in range(max(0, i - 30), i):
        m = RX.search(lines[j])
        if m:
            course, wk, order = m.group(1), m.group(2), m.group(3)
            if course == "attack-ai":
                cases.append((course, wk, order))
            break

# dedupe preserving order
seen = set()
uniq = []
for c in cases:
    if c not in seen:
        seen.add(c)
        uniq.append(c)

OUT.write_text("\n".join(f"{c[0]}\t{c[1]}\t{c[2]}" for c in uniq) + "\n")
print(f"attack-ai error → {len(uniq)} cases → {OUT}")
