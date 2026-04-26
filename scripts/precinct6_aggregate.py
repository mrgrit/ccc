#!/usr/bin/env python3
"""P1 — top-N hot IoC 자동 anchor (전략 D).

Precinct 6 의 1억 raw signals 에서 출현 빈도 높은 IP 를 frequency rank 로 추출.
top-N (default 1000) IP 만 hot_ioc anchor 로 등록 — Bastion 운영 시 lookup 매칭에서
가장 자주 마주칠 IP 들을 KG 에 사전 노출.

전략 비교:
  A. 모든 incident IP 를 anchor — too noisy
  B. malicious-only IP 만 — 본 import_real_edges 가 이미 처리
  C. 수동 큐레이션 — 비효율
  D. (이 스크립트) 빈도 기반 자동 → noise 자동 필터, top-N 만 hot 로

사용:
  python3 scripts/precinct6_aggregate.py --top 1000
  python3 scripts/precinct6_aggregate.py --top 100 --dry-run
"""
from __future__ import annotations
import argparse, os, sys, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env():
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def aggregate(src: Path, top: int, scan_limit: int, dry_run: bool = False) -> dict:
    """edges.jsonl 의 src/dst IP 빈도 집계 → top-N 추출."""
    edges_path = src / "graph" / "edges.jsonl"
    if not edges_path.exists():
        return {"error": f"{edges_path} 없음"}
    counter = Counter()
    scanned = 0
    with edges_path.open() as f:
        for line in f:
            scanned += 1
            if scanned > scan_limit:
                break
            try:
                e = json.loads(line)
            except Exception:
                continue
            for ip_field in ("src", "dst"):
                ip = e.get(ip_field)
                if ip and isinstance(ip, str):
                    counter[ip] += 1
    top_ips = counter.most_common(top)
    if dry_run:
        return {"scanned": scanned, "unique_ips": len(counter),
                "top_sample": top_ips[:10]}
    load_env()
    sys.path.insert(0, str(ROOT))
    from packages.bastion.history import HistoryLayer
    h = HistoryLayer()
    added = skipped = 0
    for ip, freq in top_ips:
        label = f"hot_ioc:p6:{ip}"
        if h.is_anchored(label):
            skipped += 1
            continue
        try:
            h.add_anchor(kind="ioc", label=label,
                         body=f"Precinct6 hot IoC freq={freq} (rank≤{top})",
                         related_ids=[])
            added += 1
        except Exception:
            skipped += 1
    return {"scanned": scanned, "unique_ips": len(counter),
            "hot_anchors_added": added, "hot_anchors_skipped": skipped,
            "top_sample": [(ip, freq) for ip, freq in top_ips[:5]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "data" / "precinct6_100m"),
                    help="precinct6 dataset 디렉토리")
    ap.add_argument("--top", type=int, default=1000,
                    help="hot IoC 상한 (default 1000)")
    ap.add_argument("--scan-limit", type=int, default=5_000_000,
                    help="edges.jsonl 라인 스캔 상한 (default 5M)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    src = Path(args.src)
    print(f"=== precinct6 hot IoC aggregate ===")
    print(f"  src: {src}")
    print(f"  top: {args.top}, scan_limit: {args.scan_limit}, dry_run: {args.dry_run}")
    r = aggregate(src, args.top, args.scan_limit, args.dry_run)
    print(f"\nresult:")
    for k, v in r.items():
        if k == "top_sample":
            print(f"  {k}:")
            for ip, freq in v: print(f"    {freq:>6}  {ip}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
