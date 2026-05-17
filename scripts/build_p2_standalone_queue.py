#!/usr/bin/env python3
"""P2 Track B — standalone 6v6 lab 큐 빌더.

contents/standalone/lab/{secuops,attack,aisec}/weekNN.yaml 를 스캔하여
(course, weekNN.yaml, step_order) tuple 의 TSV 큐 생성. driver_p2_standalone.sh 가 소비.

기존 R5 driver 와 동일 포맷 (course_path<TAB>order, course_path 는 contents/standalone/lab/... prefix).

cursor 0 부터 새로 시작. 이미 진행된 step 은 driver 에서 progress JSON 보고 skip.
"""
from __future__ import annotations
import pathlib, yaml, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "contents" / "standalone" / "lab"
OUT = ROOT / "results" / "retest" / "queue_p2_standalone.tsv"
COURSES = ["secuops", "attack", "aisec"]


def main():
    rows = []
    for course in COURSES:
        cdir = BASE / course
        if not cdir.is_dir():
            print(f"[skip] {course}: dir not found", file=sys.stderr)
            continue
        for yfile in sorted(cdir.glob("week*.yaml")):
            try:
                y = yaml.safe_load(open(yfile))
            except Exception as e:
                print(f"[skip] {yfile.name}: parse error {e}", file=sys.stderr)
                continue
            for s in y.get("steps", []):
                order = s.get("order")
                if order is None:
                    continue
                # course_path = contents/standalone/lab/<course>/weekNN.yaml
                rel = yfile.relative_to(ROOT).as_posix()
                rows.append((rel, order))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for rel, order in rows:
            f.write(f"{rel}\t{order}\n")
    print(f"[ok] {OUT} ({len(rows)} steps across {len(COURSES)} courses)")

    # course / week 별 분포
    from collections import Counter
    per_course = Counter(r[0].split("/")[3] for r in rows)
    for c, n in per_course.items():
        print(f"  {c}: {n} steps")


if __name__ == "__main__":
    main()
