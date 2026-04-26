#!/usr/bin/env python3
"""고객사 / 배포처에서 Precinct 6 seed bundle 을 자기 Bastion KG 에 import.

precinct6_export_seed.py 가 생성한 bundle (anchors.jsonl + concepts.jsonl + manifest.json)
을 받아 packages/bastion 의 HistoryLayer / KG 에 dedup append.

사용:
  # tar.gz 압축 해제 후 디렉토리 지정
  tar xzf precinct6-seed-v2026.04.tar.gz
  python3 scripts/import_seed_bundle.py --bundle precinct6-seed-v2026.04/

  # dry-run
  python3 scripts/import_seed_bundle.py --bundle precinct6-seed-v2026.04/ --dry-run
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def import_bundle(bundle: Path, dry_run: bool = False) -> dict:
    if not bundle.is_dir():
        return {"error": f"{bundle} 디렉토리 아님"}
    manifest_path = bundle / "manifest.json"
    if not manifest_path.exists():
        return {"error": f"{manifest_path} 없음 — 잘못된 bundle"}
    manifest = json.loads(manifest_path.read_text())
    print(f"=== seed bundle: {bundle.name} ===")
    print(f"  generated_at: {manifest.get('generated_at')}")
    print(f"  source: {manifest.get('source_dataset')}")
    print(f"  license: {manifest.get('license')}")
    print(f"  counts: {manifest.get('counts')}")

    anchor_path = bundle / "anchors.jsonl"
    concept_path = bundle / "concepts.jsonl"

    if dry_run:
        a_cnt = sum(1 for _ in anchor_path.open()) if anchor_path.exists() else 0
        c_cnt = sum(1 for _ in concept_path.open()) if concept_path.exists() else 0
        return {"would_anchors": a_cnt, "would_concepts": c_cnt, "manifest": manifest}

    # bastion 모듈 로드 (.env 필요)
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    sys.path.insert(0, str(ROOT))
    from packages.bastion.history import HistoryLayer
    from packages.bastion.graph import get_graph
    h = HistoryLayer()
    g = get_graph()

    # anchors
    a_added = a_skip = 0
    if anchor_path.exists():
        with anchor_path.open() as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                label = rec.get("label", "")
                if not label: continue
                if h.is_anchored(label):
                    a_skip += 1
                    continue
                try:
                    h.add_anchor(kind=rec.get("kind","breach_record"),
                                 label=label, body=rec.get("body","") or "",
                                 related_ids=[])
                    a_added += 1
                except Exception:
                    a_skip += 1

    # concepts
    c_added = c_skip = 0
    if concept_path.exists():
        with concept_path.open() as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                nid = rec.get("id", "")
                name = rec.get("name", "")
                if not nid: continue
                try:
                    g.add_node(nid, "Concept", name,
                               content=rec.get("content") or {},
                               meta=rec.get("meta") or {})
                    c_added += 1
                except Exception:
                    c_skip += 1

    return {"anchors_added": a_added, "anchors_skipped": a_skip,
            "concepts_added": c_added, "concepts_skipped": c_skip,
            "manifest": manifest}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, help="seed bundle 디렉토리")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    r = import_bundle(Path(args.bundle), dry_run=args.dry_run)
    print(f"\nresult: {json.dumps({k:v for k,v in r.items() if k != 'manifest'}, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
