#!/usr/bin/env python3
"""eg-6v6.db 빈 DB 초기화.

6bq5 의 schema (scripts/eg/schema.sql) 를 그대로 적용. 데이터는 없음.
카탈로그 import 는 별도 (`import_catalog.py`).

사용:
  python3 scripts/eg/init_db.py [--db /path/to/eg-6v6.db] [--force]

기본 경로: ~/eg-6v6/data/eg-6v6.db (또는 EG_DB 환경변수)
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DB = Path(os.environ.get("EG_DB", str(Path.home() / "eg-6v6" / "data" / "eg-6v6.db")))
SCHEMA_SQL = HERE / "schema.sql"


def init(db_path: Path, force: bool = False) -> None:
    if db_path.exists() and not force:
        raise SystemExit(f"이미 존재: {db_path} — --force 로 덮어쓰기")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript("PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;")
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()

    # 검증
    conn = sqlite3.connect(str(db_path))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    counts = {}
    for t in tables:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = "(virtual)"
    conn.close()

    print(f"[OK] {db_path}")
    print(f"     tables: {len(tables)}, rows: {sum(v for v in counts.values() if isinstance(v,int))}")
    for t, n in counts.items():
        print(f"       {t:30} {n}")


def main():
    p = argparse.ArgumentParser(description="eg-6v6 빈 DB 초기화")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"기본: {DEFAULT_DB}")
    p.add_argument("--force", action="store_true", help="기존 DB 덮어쓰기")
    args = p.parse_args()
    init(args.db, force=args.force)


if __name__ == "__main__":
    main()
