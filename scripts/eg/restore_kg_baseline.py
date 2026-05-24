"""EG KG pristine 복원 — eval(05-24) 오염 anchor/node/edge 제거 → 265 anchor baseline.

안전: 원본 미변경. /tmp/graph_clean.db 복사본에서 삭제+검증만. 교체는 별도(검증 후).
컨테이너(UTC) 기준 created_at>=CUTOFF 행 = 이번 세션 eval run 산물(soc-ops/web-vuln full).

사용: docker exec -u root 6v6-bastion python3 /tmp/restore_kg_baseline.py [--apply]
  (기본 dry: 복사본 정리+검증만 / --apply: 정리된 복사본을 원본에 교체 — bastion 정지 후)
"""
import shutil
import sqlite3
import sys

SRC = "/opt/ccc-src/data/bastion_graph.db"
CLEAN = "/tmp/graph_clean.db"
CUTOFF = "2026-05-24"      # 이 날짜 이후(UTC) 생성 = eval 오염
EXPECT_ANCHORS = 265       # pristine 기대치
EXPECT_NODES = 497

def counts(con):
    return (con.execute("SELECT COUNT(*) FROM history_anchors").fetchone()[0],
            con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0],
            con.execute("SELECT COUNT(*) FROM edges").fetchone()[0])

def clean_copy():
    shutil.copy2(SRC, CLEAN)
    con = sqlite3.connect(CLEAN)
    before = counts(con)
    # 삭제 대상 node id
    ids = [r[0] for r in con.execute(
        "SELECT id FROM nodes WHERE created_at>=?", (CUTOFF,)).fetchall()]
    # edges: 오늘 생성 OR 삭제될 node 참조
    con.execute("DELETE FROM edges WHERE created_at>=?", (CUTOFF,))
    if ids:
        q = ",".join("?" * len(ids))
        con.execute(f"DELETE FROM edges WHERE src IN ({q}) OR dst IN ({q})", ids + ids)
    con.execute("DELETE FROM history_anchors WHERE created_at>=?", (CUTOFF,))
    con.execute("DELETE FROM nodes WHERE created_at>=?", (CUTOFF,))
    con.commit()
    # FTS 정합성 재구축 (external-content FTS5)
    try:
        con.execute("INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild')")
        con.commit()
        fts = "rebuilt"
    except Exception as e:
        fts = f"rebuild_skip:{type(e).__name__}"
    after = counts(con)
    con.execute("PRAGMA integrity_check")
    ic = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    return before, after, len(ids), fts, ic

def main():
    before, after, ndel, fts, ic = clean_copy()
    print(f"[원본] anchors/nodes/edges = {before}")
    print(f"[정리본] anchors/nodes/edges = {after}  (삭제 node {ndel}개)")
    print(f"FTS: {fts} | integrity_check: {ic}")
    ok = after[0] == EXPECT_ANCHORS and after[1] == EXPECT_NODES and ic == "ok"
    print(f"검증: anchors {after[0]}=={EXPECT_ANCHORS}? nodes {after[1]}=={EXPECT_NODES}? → {'PASS' if ok else 'CHECK'}")
    if "--apply" in sys.argv:
        if not ok:
            print("★ 검증 실패 — 교체 안 함"); sys.exit(1)
        shutil.copy2(SRC, SRC + ".polluted.bak")
        shutil.copy2(CLEAN, SRC)
        print(f"교체 완료: {SRC} ← 정리본 (원본은 {SRC}.polluted.bak 백업)")
    else:
        print("dry-run (교체 안 함). --apply 로 교체.")

if __name__ == "__main__":
    main()
