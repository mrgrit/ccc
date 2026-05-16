#!/usr/bin/env python3
"""contents/eg-catalog/ 의 fixture YAML 을 eg-6v6.db 로 import.

import 동작:
1. missions.yaml → nodes.type='Mission' upsert (9 row)
2. skills.yaml   → nodes.type='Skill' upsert + Skill `belongs_to` Mission edge (primary/secondary)
3. concepts.yaml → nodes.type='Concept' upsert + Concept `relates_to` Mission edge

primary 와 secondary 는 edge type 으로 구분:
- primary_belongs_to (1 개)
- belongs_to        (0~N 개, secondary 포함)

idempotent — 반복 실행해도 같은 결과.

사용:
  python3 scripts/eg/import_catalog.py [--db /path/to/eg-6v6.db] [--catalog /path/to/eg-catalog/]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_DB = Path(os.environ.get("EG_DB", str(Path.home() / "eg-6v6" / "data" / "eg-6v6.db")))
DEFAULT_CATALOG = REPO_ROOT / "contents" / "eg-catalog"


def _upsert_node(c: sqlite3.Connection, *, node_id: str, type_: str, name: str,
                 content: dict, meta: dict) -> None:
    c.execute(
        """INSERT INTO nodes (id, type, name, content, meta, updated_at)
           VALUES (?,?,?,?,?, datetime('now'))
           ON CONFLICT(id) DO UPDATE SET
               name=excluded.name, content=excluded.content,
               meta=excluded.meta, updated_at=datetime('now')""",
        (node_id, type_, name,
         json.dumps(content, ensure_ascii=False),
         json.dumps(meta, ensure_ascii=False)),
    )
    # FTS 동기화
    c.execute("DELETE FROM nodes_fts WHERE id=?", (node_id,))
    fts_text = (name or "") + " " + (content.get("statement", "") or content.get("description", ""))
    c.execute(
        "INSERT INTO nodes_fts (id, type, name, content_text) VALUES (?,?,?,?)",
        (node_id, type_, name, fts_text),
    )


def _upsert_edge(c: sqlite3.Connection, *, src: str, dst: str, type_: str,
                 weight: float = 1.0, meta: dict | None = None) -> None:
    c.execute(
        """INSERT INTO edges (src, dst, type, weight, meta)
           VALUES (?,?,?,?,?)
           ON CONFLICT(src, dst, type) DO UPDATE SET
               weight=excluded.weight, meta=excluded.meta""",
        (src, dst, type_, weight, json.dumps(meta or {}, ensure_ascii=False)),
    )


def import_missions(c: sqlite3.Connection, doc: dict) -> int:
    n = 0
    for m in doc.get("missions", []):
        _upsert_node(
            c,
            node_id=m["id"],
            type_="Mission",
            name=m["name"],
            content={
                "code": m["code"],
                "name_en": m["name_en"],
                "statement": m["statement"],
                "dod": m.get("dod", ""),
                "primary_cross_cutting_tag": m.get("primary_cross_cutting_tag", []),
            },
            meta={
                "owner": m["owner"],
                "tier": m.get("tier", "operational"),
                "catalog_source": "missions.yaml",
                "read_only": True,
            },
        )
        n += 1
    # often_chains relationship 도 edge 로 박음
    for pair in doc.get("relationships", {}).get("often_chains", []):
        a, b = f"mission:{pair[0]}-*", f"mission:{pair[1]}-*"
        # code 만 알려져 있으므로 실제 id 매핑
        a_id = next((m["id"] for m in doc["missions"] if m["code"] == pair[0]), None)
        b_id = next((m["id"] for m in doc["missions"] if m["code"] == pair[1]), None)
        if a_id and b_id:
            _upsert_edge(c, src=a_id, dst=b_id, type_="often_chains")
    return n


def import_skills(c: sqlite3.Connection, doc: dict, missions_doc: dict) -> tuple[int, int]:
    mission_id_by_code = {m["code"]: m["id"] for m in missions_doc["missions"]}
    n_nodes = 0
    n_edges = 0
    for s in doc.get("skills", []):
        _upsert_node(
            c,
            node_id=s["id"],
            type_="Skill",
            name=s["name"],
            content={
                "description": s["description"],
                "typical_tools": s.get("typical_tools", []),
            },
            meta={
                "risk_level": s.get("risk_level", "low"),
                "requires_audit": s.get("requires_audit", False),
                "catalog_source": "skills.yaml",
                "read_only": True,
            },
        )
        n_nodes += 1
        # primary
        pm = mission_id_by_code.get(s["primary_mission"])
        if pm:
            _upsert_edge(c, src=s["id"], dst=pm, type_="primary_belongs_to", weight=1.0)
            n_edges += 1
        # secondary
        for sm_code in s.get("secondary_missions", []):
            sm = mission_id_by_code.get(sm_code)
            if sm:
                _upsert_edge(c, src=s["id"], dst=sm, type_="belongs_to", weight=0.5)
                n_edges += 1
    return n_nodes, n_edges


def import_concepts(c: sqlite3.Connection, doc: dict, missions_doc: dict) -> tuple[int, int]:
    mission_id_by_code = {m["code"]: m["id"] for m in missions_doc["missions"]}
    n_nodes = 0
    n_edges = 0
    for k in doc.get("concepts", []):
        _upsert_node(
            c,
            node_id=k["id"],
            type_="Concept",
            name=k["name"],
            content={
                "standard": k["standard"],
                "kind": k["kind"],
                "code": k["code"],
            },
            meta={
                "catalog_source": "concepts.yaml",
                "read_only": True,
            },
        )
        n_nodes += 1
        pm = mission_id_by_code.get(k.get("primary_mission"))
        if pm:
            _upsert_edge(c, src=k["id"], dst=pm, type_="primary_belongs_to", weight=1.0)
            n_edges += 1
        for sm_code in k.get("secondary_missions", []):
            sm = mission_id_by_code.get(sm_code)
            if sm:
                _upsert_edge(c, src=k["id"], dst=sm, type_="relates_to", weight=0.3)
                n_edges += 1
    return n_nodes, n_edges


def main():
    p = argparse.ArgumentParser(description="EG catalog import")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = p.parse_args()

    if not args.db.exists():
        raise SystemExit(f"DB 없음: {args.db} — init_db.py 먼저 실행")

    missions_doc = yaml.safe_load((args.catalog / "missions.yaml").read_text(encoding="utf-8"))
    skills_doc = yaml.safe_load((args.catalog / "skills.yaml").read_text(encoding="utf-8"))
    concepts_doc = yaml.safe_load((args.catalog / "concepts.yaml").read_text(encoding="utf-8"))

    conn = sqlite3.connect(str(args.db))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        n_m = import_missions(conn, missions_doc)
        n_s_nodes, n_s_edges = import_skills(conn, skills_doc, missions_doc)
        n_c_nodes, n_c_edges = import_concepts(conn, concepts_doc, missions_doc)
        conn.commit()
    finally:
        conn.close()

    print(f"[OK] {args.db}")
    print(f"     Mission nodes: {n_m}")
    print(f"     Skill nodes:   {n_s_nodes}  (edges: {n_s_edges})")
    print(f"     Concept nodes: {n_c_nodes}  (edges: {n_c_edges})")
    print(f"     total nodes:   {n_m + n_s_nodes + n_c_nodes}")


if __name__ == "__main__":
    main()
