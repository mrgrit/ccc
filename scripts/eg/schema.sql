CREATE TABLE defense_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER REFERENCES defense_rules(id),
            experiment_id INTEGER,
            severity TEXT,
            target TEXT,
            message TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE defense_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kind TEXT,                -- 'fol' | 'anomaly' | 'centrality' | 'embedding'
            body TEXT NOT NULL,       -- rule body / config
            enabled INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE edges (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        src         TEXT NOT NULL,
        dst         TEXT NOT NULL,
        type        TEXT NOT NULL,
        weight      REAL DEFAULT 1.0,
        meta        TEXT DEFAULT '{}',
        created_at  TEXT DEFAULT (datetime('now')),
        UNIQUE(src, dst, type)
    );

CREATE TABLE experiment_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
            phase TEXT,                -- 'attack' | 'defense' | 'replay'
            payload TEXT DEFAULT '{}',
            result TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,        -- 'manipulation' | 'pentest' | 'defense'
            title TEXT,
            description TEXT,
            params TEXT DEFAULT '{}',
            status TEXT DEFAULT 'planned',
            created_at TEXT DEFAULT (datetime('now')),
            started_at TEXT,
            finished_at TEXT
        );

CREATE TABLE history_anchors (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,            -- ioc / regulatory / policy_decision / breach_record
    label       TEXT NOT NULL,            -- 사람 가독 이름
    body        TEXT NOT NULL,            -- 영구 보존 본문 (verbatim)
    related_ids TEXT DEFAULT '[]',        -- ['asset:web', 'playbook:apt-phase1']
    created_at  TEXT DEFAULT (datetime('now')),
    valid_from  TEXT,
    valid_until TEXT,                     -- NULL = 영구
    immune      INTEGER DEFAULT 1         -- 1 = 압축 면역 (언제나 1, 명시 표시용)
);

CREATE TABLE history_changelogs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    target_kind TEXT NOT NULL,            -- asset / rule / policy / playbook
    target_id   TEXT NOT NULL,            -- 대상 식별자
    version     INTEGER NOT NULL,         -- 단조 증가
    ts          TEXT NOT NULL,
    actor       TEXT DEFAULT '',
    diff        TEXT NOT NULL,            -- 변경 내용 (textual diff 또는 JSON patch)
    rationale   TEXT DEFAULT '',          -- 변경 이유 (decision rationale)
    audit_seq   INTEGER DEFAULT 0,
    UNIQUE(target_kind, target_id, version)
);

CREATE TABLE history_events (
    id           TEXT PRIMARY KEY,
    ts           TEXT NOT NULL,           -- ISO 8601 (UTC), strict
    kind         TEXT NOT NULL,           -- task_done / policy_change / ioc_seen / handoff / decision / ...
    actor        TEXT DEFAULT '',         -- operator id 또는 'manager' / 'subagent:host'
    asset_id     TEXT DEFAULT '',         -- 관련 자산 (FK 느슨)
    narrative_id TEXT DEFAULT '',         -- 속한 narrative
    audit_seq    INTEGER DEFAULT 0,       -- §3.6 hash chain seq
    summary      TEXT NOT NULL,           -- 한 줄 요약
    payload      TEXT DEFAULT '{}'        -- JSON: 자세한 컨텍스트
);

CREATE TABLE history_narratives (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    status      TEXT DEFAULT 'open',      -- open / closed
    summary     TEXT DEFAULT '',          -- narrative-level 요약 (압축 후도 유지)
    tags        TEXT DEFAULT '[]',
    meta        TEXT DEFAULT '{}'
);

CREATE TABLE infra_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT, op TEXT, status TEXT, output TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE kg_snapshot_edges (
            snapshot_id INTEGER REFERENCES kg_snapshots(id) ON DELETE CASCADE,
            src TEXT, dst TEXT, type TEXT, weight REAL, meta TEXT
        );

CREATE TABLE kg_snapshot_nodes (
            snapshot_id INTEGER REFERENCES kg_snapshots(id) ON DELETE CASCADE,
            id TEXT, type TEXT, name TEXT, content TEXT, meta TEXT
        );

CREATE TABLE kg_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            description TEXT,
            node_count INTEGER,
            edge_count INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE memory_trace (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            agent TEXT,
            op TEXT,                  -- 'write' | 'read' | 'rollback'
            node_id TEXT,
            content TEXT,
            ts TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE nodes (
        id          TEXT PRIMARY KEY,
        type        TEXT NOT NULL,
        name        TEXT NOT NULL,
        content     TEXT DEFAULT '{}',
        embedding   BLOB,
        meta        TEXT DEFAULT '{}',
        created_at  TEXT DEFAULT (datetime('now')),
        updated_at  TEXT DEFAULT (datetime('now'))
    );

CREATE VIRTUAL TABLE nodes_fts USING fts5(
        id UNINDEXED,
        type UNINDEXED,
        name,
        content_text,
        tokenize='unicode61 remove_diacritics 1'
    );

CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            tag TEXT,
            body TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE poison_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            recipe TEXT NOT NULL,
            target_node TEXT,
            payload TEXT,
            stealth_score REAL,
            asr REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE TABLE rag_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            query TEXT,
            retrieved TEXT,           -- json: list[node_id]
            generation TEXT,
            poisoned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

CREATE INDEX idx_anc_kind  ON history_anchors(kind);

CREATE INDEX idx_anc_label ON history_anchors(label);

CREATE INDEX idx_chg_target ON history_changelogs(target_kind, target_id);

CREATE INDEX idx_chg_ts     ON history_changelogs(ts);

CREATE INDEX idx_edges_dst ON edges(dst);

CREATE INDEX idx_edges_src ON edges(src);

CREATE INDEX idx_edges_type ON edges(type);

CREATE INDEX idx_hev_asset     ON history_events(asset_id);

CREATE INDEX idx_hev_kind      ON history_events(kind);

CREATE INDEX idx_hev_narrative ON history_events(narrative_id);

CREATE INDEX idx_hev_ts        ON history_events(ts);

CREATE INDEX idx_nar_status ON history_narratives(status);

CREATE INDEX idx_nodes_name ON nodes(name);

CREATE INDEX idx_nodes_type ON nodes(type);

CREATE INDEX idx_snap_e_snap ON kg_snapshot_edges(snapshot_id);

CREATE INDEX idx_snap_n_snap ON kg_snapshot_nodes(snapshot_id);
