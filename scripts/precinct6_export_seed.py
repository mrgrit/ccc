#!/usr/bin/env python3
"""P1 Phase 5 — 배포용 Precinct 6 seed bundle 생성.

폐쇄망 고객사 배포 시 1억 raw 데이터 다운로드 회피.
대신 top-N 추출 산출물만 동봉:

  precinct6-seed-vYYYY.MM/
    anchors.jsonl          # top breach_record + ioc + breach_pair
    concepts.jsonl         # MITRE technique + compliance framework + product
    manifest.json          # 생성 시각, source dataset version, 압축 규칙
    README.md              # 배포 가이드 + 임포트 명령

사용:
  python3 scripts/precinct6_export_seed.py
  python3 scripts/precinct6_export_seed.py --top 100000 --out /tmp/seed
"""
from __future__ import annotations
import argparse, sqlite3, json, tarfile, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DB = ROOT / "data" / "bastion_graph.db"


def export(top: int, out_dir: Path) -> dict:
    if not GRAPH_DB.exists():
        return {"error": f"{GRAPH_DB} 없음 — import_precinct6.py 먼저 실행"}
    out_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(GRAPH_DB); cur = con.cursor()

    # anchors export
    anchor_path = out_dir / "anchors.jsonl"
    n_breach = n_ioc = 0
    with anchor_path.open("w", encoding="utf-8") as f:
        for kind in ("breach_record", "ioc"):
            rows = cur.execute(
                "SELECT label, body, kind FROM history_anchors WHERE kind=? "
                "ORDER BY id DESC LIMIT ?", (kind, top)
            ).fetchall()
            for label, body, k in rows:
                f.write(json.dumps({"label": label, "body": body, "kind": k},
                                    ensure_ascii=False) + "\n")
                if k == "breach_record": n_breach += 1
                else: n_ioc += 1

    # concepts export
    concept_path = out_dir / "concepts.jsonl"
    n_concept = 0
    with concept_path.open("w", encoding="utf-8") as f:
        rows = cur.execute(
            "SELECT id, name, content, meta FROM nodes WHERE type='Concept'"
        ).fetchall()
        for nid, name, content, meta in rows:
            try:
                cobj = json.loads(content) if content else {}
            except Exception:
                cobj = {"raw": content}
            try:
                mobj = json.loads(meta) if meta else {}
            except Exception:
                mobj = {}
            f.write(json.dumps({"id": nid, "name": name, "content": cobj, "meta": mobj},
                                ensure_ascii=False) + "\n")
            n_concept += 1

    # manifest
    manifest = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_dataset": "witfoo/precinct6-cybersecurity-100m + witfoo/precinct6-cybersecurity",
        "license": "Apache 2.0",
        "sanitization": "RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN — WitFoo 4-layer (regex + format + ML/NER + Claude review)",
        "counts": {"breach_record": n_breach, "ioc": n_ioc, "concept": n_concept},
        "top_limit": top,
        "schema_version": "v1.0.0",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # README
    readme = f"""# Precinct 6 Seed Bundle

생성: {manifest['generated_at']}

## 내용
- `anchors.jsonl` : breach_record {n_breach} + ioc {n_ioc} (총 {n_breach + n_ioc})
- `concepts.jsonl`: MITRE technique + compliance framework + security product Concept {n_concept}
- `manifest.json` : 출처/라이선스/sanitization 메타

## 임포트 (배포처에서)

```bash
python3 scripts/import_seed_bundle.py --bundle precinct6-seed-vYYYY.MM/
```

이 명령은 `data/bastion_graph.db` 의 history_anchors / nodes 에 추가한다 (중복 skip).

## 사용
- Bastion 의 RAG lookup 시 자동 참조 (`/chat` 의 lookup_decision 단계)
- 학생/평가자가 lab 시작 전 `precinct6_cases.md` 부록 자동 노출
- battle scenario `precinct6-data-theft.yaml` 에서 이미 검증된 패턴 재현

## 라이선스
WitFoo Precinct 6 Cybersecurity Dataset, Apache 2.0.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    con.close()
    return manifest


def make_tar(out_dir: Path) -> Path:
    parent = out_dir.parent
    tar_path = parent / f"{out_dir.name}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(out_dir, arcname=out_dir.name)
    return tar_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=100000,
                    help="anchor kind 별 상한 (default 100k)")
    ap.add_argument("--out", default=str(ROOT / "dist" / f"precinct6-seed-v{datetime.date.today():%Y.%m}"),
                    help="출력 디렉토리 (자동 tar.gz 생성)")
    args = ap.parse_args()
    out_dir = Path(args.out)
    print(f"=== Precinct 6 seed bundle export ===")
    print(f"  out: {out_dir}")
    print(f"  top: {args.top}")
    manifest = export(args.top, out_dir)
    print(f"  manifest: {manifest}")
    tar_path = make_tar(out_dir)
    sz = os.path.getsize(tar_path)
    print(f"  ✓ {tar_path}  ({sz:,} bytes = {sz/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
