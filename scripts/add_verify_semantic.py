#!/usr/bin/env python3
"""verify.semantic 필드를 YAML 에 안전 삽입하는 도구.

사용:
  python3 scripts/add_verify_semantic.py <course> <week> <order> [semantic.json]
  # semantic.json 생략 시 stdin 에서 JSON 읽음.

semantic.json 형식:
  {
    "intent": "...",
    "success_criteria": ["...", "..."],
    "acceptable_methods": ["..."],
    "negative_signs": ["..."]
  }

- ruamel.yaml 로 포맷 보존 라운드트립
- 존재하는 step 을 order 기준으로 찾아 verify.semantic 덮어쓰기(신규 추가·갱신 모두)
- 실패 시 원본 그대로 유지
"""
from __future__ import annotations
import sys
import json
import pathlib
from ruamel.yaml import YAML

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    course, week_s, order_s = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        week = int(week_s.replace("week", "").lstrip("0") or "0")
        order = int(order_s)
    except ValueError:
        sys.exit(f"week/order 정수 파싱 실패: {week_s} {order_s}")

    if len(sys.argv) >= 5:
        sem = json.loads(pathlib.Path(sys.argv[4]).read_text(encoding="utf-8"))
    else:
        sem = json.loads(sys.stdin.read())

    for k in ("intent", "success_criteria", "acceptable_methods", "negative_signs"):
        if k not in sem:
            sys.exit(f"semantic 필수 키 누락: {k}")
    if not isinstance(sem["success_criteria"], list):
        sys.exit("success_criteria 는 list 이어야 함")

    yaml_path = ROOT / "contents" / "labs" / course / f"week{week:02d}.yaml"
    if not yaml_path.exists():
        sys.exit(f"YAML 없음: {yaml_path}")

    y = YAML()
    y.preserve_quotes = True
    y.width = 140
    y.indent(mapping=2, sequence=2, offset=0)
    with yaml_path.open(encoding="utf-8") as f:
        data = y.load(f)

    target = None
    for s in data.get("steps") or []:
        if s.get("order") == order:
            target = s
            break
    if target is None:
        sys.exit(f"step order={order} 없음 in {yaml_path}")

    verify = target.get("verify") or {}
    if not isinstance(verify, dict):
        sys.exit(f"verify 가 dict 아님: {type(verify)}")
    verify["semantic"] = {
        "intent": sem["intent"],
        "success_criteria": list(sem["success_criteria"]),
        "acceptable_methods": list(sem.get("acceptable_methods", [])),
        "negative_signs": list(sem.get("negative_signs", [])),
    }
    target["verify"] = verify

    with yaml_path.open("w", encoding="utf-8") as f:
        y.dump(data, f)

    import yaml as _y
    with yaml_path.open(encoding="utf-8") as f:
        _y.safe_load(f)
    print(f"ok: {course}/week{week:02d}/{order} verify.semantic 갱신")


if __name__ == "__main__":
    main()
