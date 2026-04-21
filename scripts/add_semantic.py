#!/usr/bin/env python3
"""verify.semantic 안전 삽입 헬퍼 (Master Agent 전용).

사용:
  cat semantic.json | python3 scripts/add_semantic.py <course> <week> <order> [--hash-sensitive]
  python3 scripts/add_semantic.py <course> <week> <order> --file semantic.json [--hash-sensitive]
  python3 scripts/add_semantic.py <course> <week> <order> --inline '{"intent": "...", ...}'

- YAML 을 yaml.safe_load → dict 수정 → yaml.safe_dump 로 안전 삽입 (raw text 편집 부작용 없음)
- --hash-sensitive: intent / success_criteria / acceptable_methods / negative_signs 안에서 위험 payload 패턴
  감지 시 SHA256(16자) 로 치환하고 원본은 contents/.sensitive/<hash>.txt 에 저장 (gitignored).
  복원은 admin API /admin/sensitive/<hash> 에서만 가능.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SENSITIVE_DIR = ROOT / "contents" / ".sensitive"
SENSITIVE_DIR.mkdir(parents=True, exist_ok=True)

DANGER_PATTERNS = [
    r"_\$\$ND_FUNC\$\$_",
    r"child_process.*exec",
    r"system\(['\"]",
    r"eval\(['\"]",
    r"base64 -d.*\|.*sh",
    r"bash -i.*>& */dev/tcp",
    r"nc -e ?/bin/",
    r"mkfifo.*\|.*sh.*\|.*nc",
    r"\bshellcode\b",
    r"\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}",
    r"metasploit|meterpreter",
    r"' OR 1=1--",
    r"UNION SELECT.*FROM",
    r"<script>[^<]{20,}",
    r"exploit-db.com/exploits/\d+",
]


def is_sensitive(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in DANGER_PATTERNS)


def hash_redact(text: str) -> str:
    """원본을 .sensitive/<hash>.txt 에 저장하고 플레이스홀더 반환."""
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    dst = SENSITIVE_DIR / f"{h}.txt"
    if not dst.exists():
        dst.write_text(text, encoding="utf-8")
    return f"<SENSITIVE:{h}>"


def redact_semantic(sem: dict) -> tuple[dict, int]:
    redacted_count = 0
    out: dict = {}
    for k, v in sem.items():
        if isinstance(v, list):
            new_list = []
            for item in v:
                if is_sensitive(item):
                    new_list.append(hash_redact(item))
                    redacted_count += 1
                else:
                    new_list.append(item)
            out[k] = new_list
        elif isinstance(v, str):
            if is_sensitive(v):
                out[k] = hash_redact(v)
                redacted_count += 1
            else:
                out[k] = v
        else:
            out[k] = v
    return out, redacted_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course")
    ap.add_argument("week", type=int)
    ap.add_argument("order", type=int)
    ap.add_argument("--hash-sensitive", action="store_true",
                    help="위험 payload 감지 시 SHA256 hash 로 치환")
    ap.add_argument("--file", help="semantic JSON/YAML 파일 경로")
    ap.add_argument("--inline", help="semantic JSON 문자열")
    ap.add_argument("--dry", action="store_true", help="파일 저장하지 않고 미리보기")
    args = ap.parse_args()

    if args.inline:
        raw = args.inline
    elif args.file:
        raw = open(args.file).read()
    else:
        raw = sys.stdin.read()

    raw = raw.strip()
    if not raw:
        sys.exit("semantic 입력 없음")

    try:
        sem = json.loads(raw)
    except json.JSONDecodeError:
        sem = yaml.safe_load(raw)

    if not isinstance(sem, dict):
        sys.exit("semantic 은 dict 여야 함 (intent, success_criteria, ...)")

    allowed = {"intent", "success_criteria", "acceptable_methods", "negative_signs"}
    extra = set(sem.keys()) - allowed
    if extra:
        print(f"warn: 알 수 없는 키 {extra} — 그대로 저장", file=sys.stderr)

    redacted = 0
    if args.hash_sensitive:
        sem, redacted = redact_semantic(sem)

    yaml_path = ROOT / "contents" / "labs" / args.course / f"week{args.week:02d}.yaml"
    if not yaml_path.exists():
        sys.exit(f"lab not found: {yaml_path}")

    y = yaml.safe_load(open(yaml_path))
    target = None
    for s in y.get("steps", []):
        if s.get("order") == args.order:
            target = s
            break
    if target is None:
        sys.exit(f"step order={args.order} not in {yaml_path}")

    v = target.setdefault("verify", {})
    v["semantic"] = sem

    if args.dry:
        print(yaml.safe_dump({"verify": v}, allow_unicode=True, sort_keys=False,
                             default_flow_style=False, width=100))
        print(f"[dry] redacted={redacted}")
        return

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(y, f, allow_unicode=True, sort_keys=False,
                       default_flow_style=False, width=100)

    print(f"OK: {args.course}/w{args.week}/s{args.order} verify.semantic 삽입 "
          f"(redacted={redacted})")


if __name__ == "__main__":
    main()
