"""ccc-api — Cyber Combat Commander 교육 플랫폼 API (:9100)"""
from __future__ import annotations
import os
import uuid
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Config ─────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ccc:ccc@127.0.0.1:5434/ccc")
API_KEY = os.getenv("CCC_API_KEY", "ccc-api-key-2026")

# ── Pydantic Models ────────────────────────────────

class StudentCreate(BaseModel):
    name: str
    student_id: str  # 학번
    email: str = ""
    group: str = ""  # 반/조
    metadata: dict[str, Any] = {}

class StudentUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    group: str | None = None

class InfraRegister(BaseModel):
    student_id: str
    infra_name: str
    ip: str
    vm_config: dict[str, Any] = {}  # VM 구성 정보
    subagent_port: int = 8002

class LabStart(BaseModel):
    student_id: str
    lab_id: str  # e.g. "course1-week01"

class LabSubmit(BaseModel):
    student_id: str
    lab_id: str
    evidence: dict[str, Any] = {}  # 실습 결과 증거

class CTFSubmit(BaseModel):
    student_id: str
    challenge_id: str
    flag: str

class BattleRequest(BaseModel):
    challenger_id: str  # 학생 ID (도전자)
    defender_id: str | None = None  # 상대 (없으면 자동 매칭)
    battle_type: str = "1v1"  # 1v1 | team | ffa
    mode: str = "manual"  # manual | ai | mixed
    rules: dict[str, Any] = {}

class AITaskRequest(BaseModel):
    student_id: str
    instruction: str
    target_infra: str | None = None  # 대상 인프라 ID

# ── Auth ───────────────────────────────────────────
def verify_api_key(request: Request):
    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ── DB ─────────────────────────────────────────────
import psycopg2
from psycopg2.extras import RealDictCursor, Json

def _conn():
    return psycopg2.connect(DATABASE_URL)

def _init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                -- 학생
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    student_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT DEFAULT '',
                    grp TEXT DEFAULT '',
                    score INT DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 학생 인프라
                CREATE TABLE IF NOT EXISTS student_infras (
                    id TEXT PRIMARY KEY,
                    student_id TEXT REFERENCES students(id),
                    infra_name TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    subagent_url TEXT,
                    vm_config JSONB DEFAULT '{}',
                    status TEXT DEFAULT 'registered',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 실습 완료 기록 (블록체인 연동)
                CREATE TABLE IF NOT EXISTS lab_completions (
                    id TEXT PRIMARY KEY,
                    student_id TEXT REFERENCES students(id),
                    lab_id TEXT NOT NULL,
                    status TEXT DEFAULT 'in_progress',
                    evidence JSONB DEFAULT '{}',
                    block_hash TEXT,
                    started_at TIMESTAMPTZ DEFAULT now(),
                    completed_at TIMESTAMPTZ,
                    UNIQUE(student_id, lab_id)
                );
                -- CTF 제출
                CREATE TABLE IF NOT EXISTS ctf_submissions (
                    id TEXT PRIMARY KEY,
                    student_id TEXT REFERENCES students(id),
                    challenge_id TEXT NOT NULL,
                    flag TEXT NOT NULL,
                    correct BOOLEAN DEFAULT false,
                    points INT DEFAULT 0,
                    submitted_at TIMESTAMPTZ DEFAULT now()
                );
                -- 대전 기록
                CREATE TABLE IF NOT EXISTS battles (
                    id TEXT PRIMARY KEY,
                    battle_type TEXT DEFAULT '1v1',
                    mode TEXT DEFAULT 'manual',
                    challenger_id TEXT REFERENCES students(id),
                    defender_id TEXT REFERENCES students(id),
                    status TEXT DEFAULT 'pending',
                    rules JSONB DEFAULT '{}',
                    result JSONB DEFAULT '{}',
                    block_hash TEXT,
                    started_at TIMESTAMPTZ,
                    ended_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- PoW 블록
                CREATE TABLE IF NOT EXISTS pow_blocks (
                    id SERIAL PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    block_index INT NOT NULL,
                    block_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    nonce INT DEFAULT 0,
                    difficulty INT DEFAULT 4,
                    task_id TEXT,
                    context_type TEXT DEFAULT 'lab',
                    context_id TEXT,
                    reward_amount REAL DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 리더보드 뷰
                CREATE TABLE IF NOT EXISTS rankings (
                    student_id TEXT REFERENCES students(id),
                    category TEXT NOT NULL,
                    score INT DEFAULT 0,
                    rank INT DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT now(),
                    PRIMARY KEY(student_id, category)
                );
            """)
            conn.commit()

# ── Lifespan ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _init_db()
    except Exception as e:
        print(f"[CCC] DB init warning: {e}")
    yield

# ── App ────────────────────────────────────────────
app = FastAPI(
    title="Cyber Combat Commander API",
    description="사이버보안 교육 플랫폼 — CTF, 실습, 대전",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════
#  Health
# ══════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "ccc-api", "version": "0.1.0"}

# ══════════════════════════════════════════════════
#  Students (학생 관리)
# ══════════════════════════════════════════════════
@app.post("/students", dependencies=[Depends(verify_api_key)])
def create_student(body: StudentCreate):
    sid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO students (id, student_id, name, email, grp, metadata)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
                (sid, body.student_id, body.name, body.email, body.group, Json(body.metadata)),
            )
            conn.commit()
            row = cur.fetchone()
    return {"student": dict(row)}

@app.get("/students", dependencies=[Depends(verify_api_key)])
def list_students(group: str | None = None):
    q = "SELECT * FROM students"
    params: list = []
    if group:
        q += " WHERE grp=%s"; params.append(group)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"students": [dict(r) for r in rows]}

@app.get("/students/{sid}", dependencies=[Depends(verify_api_key)])
def get_student(sid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM students WHERE id=%s OR student_id=%s", (sid, sid))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Student not found")
    return {"student": dict(row)}

@app.get("/students/{sid}/progress", dependencies=[Depends(verify_api_key)])
def get_student_progress(sid: str):
    """학생 진도 현황"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 실습 완료
            cur.execute("SELECT * FROM lab_completions WHERE student_id=%s ORDER BY started_at DESC", (sid,))
            labs = cur.fetchall()
            # CTF 정답
            cur.execute("SELECT * FROM ctf_submissions WHERE student_id=%s AND correct=true ORDER BY submitted_at DESC", (sid,))
            ctf = cur.fetchall()
            # 대전
            cur.execute(
                "SELECT * FROM battles WHERE (challenger_id=%s OR defender_id=%s) ORDER BY created_at DESC",
                (sid, sid),
            )
            battles = cur.fetchall()
    return {
        "student_id": sid,
        "labs": {"completed": sum(1 for l in labs if l["status"] == "completed"), "total": len(labs), "records": [dict(l) for l in labs]},
        "ctf": {"solved": len(ctf), "records": [dict(c) for c in ctf]},
        "battles": {"total": len(battles), "records": [dict(b) for b in battles]},
    }

# ══════════════════════════════════════════════════
#  Student Infrastructure (학생 인프라)
# ══════════════════════════════════════════════════
@app.post("/infras", dependencies=[Depends(verify_api_key)])
def register_infra(body: InfraRegister):
    iid = str(uuid.uuid4())[:8]
    subagent_url = f"http://{body.ip}:{body.subagent_port}"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO student_infras (id, student_id, infra_name, ip, subagent_url, vm_config)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
                (iid, body.student_id, body.infra_name, body.ip, subagent_url, Json(body.vm_config)),
            )
            conn.commit()
            row = cur.fetchone()
    return {"infra": dict(row)}

@app.get("/infras", dependencies=[Depends(verify_api_key)])
def list_infras(student_id: str | None = None):
    q = "SELECT * FROM student_infras"
    params: list = []
    if student_id:
        q += " WHERE student_id=%s"; params.append(student_id)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"infras": [dict(r) for r in rows]}

@app.get("/infras/{iid}/health", dependencies=[Depends(verify_api_key)])
def check_infra_health(iid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM student_infras WHERE id=%s", (iid,))
            infra = cur.fetchone()
    if not infra:
        raise HTTPException(404, "Infra not found")
    import httpx
    try:
        r = httpx.get(f"{infra['subagent_url']}/health", timeout=5.0)
        healthy = r.status_code == 200
    except Exception:
        healthy = False
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE student_infras SET status=%s WHERE id=%s", ("healthy" if healthy else "unreachable", iid))
            conn.commit()
    return {"infra_id": iid, "healthy": healthy, "subagent_url": infra["subagent_url"]}

# ══════════════════════════════════════════════════
#  Labs (실습)
# ══════════════════════════════════════════════════
@app.post("/labs/start", dependencies=[Depends(verify_api_key)])
def start_lab(body: LabStart):
    lid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO lab_completions (id, student_id, lab_id, status)
                   VALUES (%s,%s,%s,'in_progress')
                   ON CONFLICT (student_id, lab_id) DO UPDATE SET status='in_progress', started_at=now()
                   RETURNING *""",
                (lid, body.student_id, body.lab_id),
            )
            conn.commit()
            row = cur.fetchone()
    return {"lab": dict(row)}

@app.post("/labs/submit", dependencies=[Depends(verify_api_key)])
def submit_lab(body: LabSubmit):
    """실습 결과 제출 → 검증 → 블록체인 기록"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM lab_completions WHERE student_id=%s AND lab_id=%s",
                (body.student_id, body.lab_id),
            )
            lab = cur.fetchone()
            if not lab:
                raise HTTPException(404, "Lab session not found. Start the lab first.")

            # TODO: lab_engine 검증 로직 연동
            verified = True  # stub

            if verified:
                # PoW 블록 생성 (간이)
                import hashlib
                prev_hash = "0" * 64
                cur.execute("SELECT block_hash FROM pow_blocks ORDER BY id DESC LIMIT 1")
                prev = cur.fetchone()
                if prev:
                    prev_hash = prev["block_hash"]
                nonce = 0
                block_data = f"{body.student_id}:{body.lab_id}:{prev_hash}:{nonce}"
                block_hash = hashlib.sha256(block_data.encode()).hexdigest()

                cur.execute(
                    """INSERT INTO pow_blocks (agent_id, block_index, block_hash, prev_hash, nonce, context_type, context_id, reward_amount)
                       VALUES (%s, (SELECT COALESCE(MAX(block_index),0)+1 FROM pow_blocks WHERE agent_id=%s), %s, %s, %s, 'lab', %s, %s)""",
                    (body.student_id, body.student_id, block_hash, prev_hash, nonce, body.lab_id, 10.0),
                )
                cur.execute(
                    """UPDATE lab_completions SET status='completed', evidence=%s, block_hash=%s, completed_at=now()
                       WHERE student_id=%s AND lab_id=%s""",
                    (Json(body.evidence), block_hash, body.student_id, body.lab_id),
                )
                conn.commit()
                return {"status": "completed", "verified": True, "block_hash": block_hash, "reward": 10.0}
            else:
                return {"status": "failed", "verified": False, "message": "실습 검증 실패"}

@app.get("/labs", dependencies=[Depends(verify_api_key)])
def list_labs(student_id: str | None = None, status: str | None = None):
    q = "SELECT * FROM lab_completions WHERE 1=1"
    params: list = []
    if student_id:
        q += " AND student_id=%s"; params.append(student_id)
    if status:
        q += " AND status=%s"; params.append(status)
    q += " ORDER BY started_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"labs": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  CTF
# ══════════════════════════════════════════════════
@app.post("/ctf/submit", dependencies=[Depends(verify_api_key)])
def submit_ctf_flag(body: CTFSubmit):
    """플래그 제출 → 중앙서버 검증 or 로컬 검증"""
    # TODO: CentralProtocol.submit_flag() 연동
    correct = False  # stub — 중앙서버에서 검증
    points = 100 if correct else 0
    sid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO ctf_submissions (id, student_id, challenge_id, flag, correct, points)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
                (sid, body.student_id, body.challenge_id, body.flag, correct, points),
            )
            if correct:
                cur.execute("UPDATE students SET score=score+%s WHERE id=%s", (points, body.student_id))
            conn.commit()
            row = cur.fetchone()
    return {"submission": dict(row)}

@app.get("/ctf/scoreboard", dependencies=[Depends(verify_api_key)])
def ctf_scoreboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.name, s.student_id, s.score,
                       count(cs.id) FILTER (WHERE cs.correct) as solved
                FROM students s
                LEFT JOIN ctf_submissions cs ON cs.student_id = s.id
                GROUP BY s.id ORDER BY s.score DESC
            """)
            rows = cur.fetchall()
    return {"scoreboard": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  Battles (대전)
# ══════════════════════════════════════════════════
@app.post("/battles", dependencies=[Depends(verify_api_key)])
def create_battle(body: BattleRequest):
    bid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO battles (id, battle_type, mode, challenger_id, defender_id, rules, status)
                   VALUES (%s,%s,%s,%s,%s,%s,'pending') RETURNING *""",
                (bid, body.battle_type, body.mode, body.challenger_id, body.defender_id, Json(body.rules)),
            )
            conn.commit()
            row = cur.fetchone()
    return {"battle": dict(row)}

@app.post("/battles/{bid}/start", dependencies=[Depends(verify_api_key)])
def start_battle(bid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE battles SET status='active', started_at=now() WHERE id=%s AND status='pending' RETURNING *",
                (bid,),
            )
            conn.commit()
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Battle not found or not pending")
    return {"battle": dict(row)}

@app.post("/battles/{bid}/end", dependencies=[Depends(verify_api_key)])
def end_battle(bid: str, result: dict[str, Any] = {}):
    """대전 종료 + 결과 블록체인 기록"""
    import hashlib
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404, "Battle not found")

            # PoW 블록 생성
            prev_hash = "0" * 64
            cur.execute("SELECT block_hash FROM pow_blocks ORDER BY id DESC LIMIT 1")
            prev = cur.fetchone()
            if prev:
                prev_hash = prev["block_hash"]
            block_data = f"battle:{bid}:{prev_hash}:0"
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()

            cur.execute(
                """INSERT INTO pow_blocks (agent_id, block_index, block_hash, prev_hash, nonce, context_type, context_id, reward_amount)
                   VALUES (%s, (SELECT COALESCE(MAX(block_index),0)+1 FROM pow_blocks WHERE agent_id=%s), %s, %s, 0, 'battle', %s, %s)""",
                ("battle-engine", "battle-engine", block_hash, prev_hash, bid, 20.0),
            )
            cur.execute(
                "UPDATE battles SET status='completed', result=%s, block_hash=%s, ended_at=now() WHERE id=%s",
                (Json(result), block_hash, bid),
            )
            conn.commit()
    return {"status": "completed", "battle_id": bid, "block_hash": block_hash}

@app.get("/battles", dependencies=[Depends(verify_api_key)])
def list_battles(status: str | None = None):
    q = "SELECT * FROM battles"
    params: list = []
    if status:
        q += " WHERE status=%s"; params.append(status)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"battles": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  AI Tasks (M9: bastion 연동)
# ══════════════════════════════════════════════════
@app.post("/ai/task", dependencies=[Depends(verify_api_key)])
def ai_task(body: AITaskRequest):
    """AI 작업 요청 → bastion 연동 (M9 구현 예정)"""
    return {
        "status": "stub",
        "message": "AI 작업 기능은 M9에서 bastion 연동 후 활성화됩니다",
        "instruction": body.instruction,
    }

# ══════════════════════════════════════════════════
#  Dashboard
# ══════════════════════════════════════════════════
@app.get("/dashboard", dependencies=[Depends(verify_api_key)])
def dashboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT count(*) as cnt FROM students")
            students = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM student_infras")
            infras = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM lab_completions WHERE status='completed'")
            labs_done = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM ctf_submissions WHERE correct=true")
            ctf_solved = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM battles")
            battles = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM pow_blocks")
            blocks = cur.fetchone()["cnt"]
    return {
        "students": students,
        "infras": infras,
        "labs_completed": labs_done,
        "ctf_solved": ctf_solved,
        "battles": battles,
        "blockchain_blocks": blocks,
    }

# ══════════════════════════════════════════════════
#  Leaderboard (종합 리더보드)
# ══════════════════════════════════════════════════
@app.get("/leaderboard", dependencies=[Depends(verify_api_key)])
def leaderboard(category: str = "total"):
    """종합 리더보드 (total | lab | ctf | battle)"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if category == "lab":
                cur.execute("""
                    SELECT s.name, s.student_id, count(lc.id) as score
                    FROM students s LEFT JOIN lab_completions lc ON lc.student_id=s.id AND lc.status='completed'
                    GROUP BY s.id ORDER BY score DESC
                """)
            elif category == "ctf":
                cur.execute("""
                    SELECT s.name, s.student_id, s.score
                    FROM students s ORDER BY s.score DESC
                """)
            elif category == "battle":
                cur.execute("""
                    SELECT s.name, s.student_id,
                           count(b.id) FILTER (WHERE b.status='completed') as score
                    FROM students s
                    LEFT JOIN battles b ON b.challenger_id=s.id OR b.defender_id=s.id
                    GROUP BY s.id ORDER BY score DESC
                """)
            else:  # total
                cur.execute("""
                    SELECT s.name, s.student_id, s.score as ctf_score,
                           count(DISTINCT lc.id) FILTER (WHERE lc.status='completed') as lab_score,
                           count(DISTINCT b.id) FILTER (WHERE b.status='completed') as battle_score
                    FROM students s
                    LEFT JOIN lab_completions lc ON lc.student_id=s.id
                    LEFT JOIN battles b ON b.challenger_id=s.id OR b.defender_id=s.id
                    GROUP BY s.id
                    ORDER BY (s.score + count(DISTINCT lc.id) FILTER (WHERE lc.status='completed') * 10) DESC
                """)
            rows = cur.fetchall()
    return {"category": category, "leaderboard": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  Blockchain
# ══════════════════════════════════════════════════
@app.get("/blockchain/blocks", dependencies=[Depends(verify_api_key)])
def list_blocks(agent_id: str | None = None, limit: int = 50):
    q = "SELECT * FROM pow_blocks WHERE 1=1"
    params: list = []
    if agent_id:
        q += " AND agent_id=%s"; params.append(agent_id)
    q += " ORDER BY id DESC LIMIT %s"; params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"blocks": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  WebSocket (대전 실시간 — M10 stub)
# ══════════════════════════════════════════════════
_battle_connections: dict[str, list[WebSocket]] = {}

@app.websocket("/ws/battle/{bid}")
async def battle_ws(websocket: WebSocket, bid: str):
    await websocket.accept()
    _battle_connections.setdefault(bid, []).append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 브로드캐스트
            for ws in _battle_connections.get(bid, []):
                if ws != websocket:
                    await ws.send_text(data)
    except WebSocketDisconnect:
        _battle_connections.get(bid, []).remove(websocket)

# ══════════════════════════════════════════════════
#  Central Server (중앙서버 연동 — M6 stub)
# ══════════════════════════════════════════════════
@app.post("/central/register", dependencies=[Depends(verify_api_key)])
def register_central(central_url: str = "http://localhost:7000"):
    return {"status": "stub", "message": "중앙서버 연동은 M6에서 구현"}

# ── Static files ───────────────────────────────────
import pathlib
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_ui_dist = pathlib.Path(__file__).parent.parent.parent / "ccc-ui" / "dist"
if _ui_dist.exists():
    app.mount("/app", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
