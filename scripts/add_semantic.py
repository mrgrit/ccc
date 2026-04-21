#!/usr/bin/env python3
"""verify.semantic 을 특정 lab step 에 안전 삽입/갱신.

사용:
  echo '{"intent":"...", "success_criteria":["..."], "acceptable_methods":["..."], "negative_signs":["..."]}' | \
    python3 scripts/add_semantic.py <course> <week> <step>

또는 파일로:
  python3 scripts/add_semantic.py <course> <week> <step> --file path/to/semantic.json

원리: yaml.safe_load → dict 수정 → yaml.safe_dump. raw Edit 의 다중 라인 script 파손을 회피.
"""
from __future__ import annotations
import sys, json, yaml, pathlib, argparse

ROOT = pathlib.Path("/home/opsclaw/ccc/contents/labs")

REQUIRED = {"intent"}
OPTIONAL = {"success_criteria", "acceptable_methods", "negative_signs"}
ALLOWED = REQUIRED | OPTIONAL


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("course")
    ap.add_argument("week", type=int)
    ap.add_argument("step", type=int)
    ap.add_argument("--file", help="JSON 파일 경로 (없으면 stdin)")
    ap.add_argument("--dry", action="store_true", help="파일 저장 안 함")
    args = ap.parse_args()

    src = open(args.file) if args.file else sys.stdin
    try:
        semantic = json.load(src)
    except json.JSONDecodeError as e:
        return sys_fail(f"JSON parse error: {e}")
    if not isinstance(semantic, dict):
        return sys_fail("semantic must be an object")
    keys = set(semantic.keys())
    extra = keys - ALLOWED
    if extra:
        return sys_fail(f"unexpected keys: {extra}")
    missing = REQUIRED - keys
    if missing:
        return sys_fail(f"missing required keys: {missing}")
    for k in ("success_criteria", "acceptable_methods", "negative_signs"):
        v = semantic.get(k)
        if v is not None and not isinstance(v, list):
            return sys_fail(f"{k} must be a list")

    path = ROOT / args.course / f"week{args.week:02d}.yaml"
    if not path.exists():
        return sys_fail(f"lab not found: {path}")

    with open(path) as f:
        y = yaml.safe_load(f)
    steps = y.get("steps") or []
    target = None
    for s in steps:
        if s.get("order") == args.step:
            target = s
            break
    if target is None:
        return sys_fail(f"step order={args.step} not in {path}")

    verify = target.setdefault("verify", {})
    verify["semantic"] = semantic

    if args.dry:
        print(yaml.safe_dump(target, allow_unicode=True, sort_keys=False, default_flow_style=False, width=200))
        return 0

    with open(path, "w") as f:
        yaml.safe_dump(y, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=200)
    print(f"ok: {args.course} w{args.week} s{args.step} · semantic fields={sorted(keys)}")
    return 0


def sys_fail(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
