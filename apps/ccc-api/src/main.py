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

# ── Config (Central 우선, 환경변수 폴백) ──────────
def _cfg(key: str, fallback: str) -> str:
    try:
        from packages.opsclaw_common.config_client import get_config
        return get_config(key, fallback=os.getenv(key.upper().replace(".", "_"), fallback))
    except Exception:
        return os.getenv(key.upper().replace(".", "_"), fallback)

DATABASE_URL = os.getenv("DATABASE_URL", _cfg("db.ccc.url", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/ccc"))
API_KEY = os.getenv("CCC_API_KEY", _cfg("auth.ccc.api_key", "ccc-api-key-2026"))

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

# ── Auth (JWT + API Key) ──────────────────────────
import hashlib as _hl
import json as _json
import base64 as _b64
import hmac as _hmac
import time as _time

JWT_SECRET = os.getenv("JWT_SECRET", "ccc-jwt-secret-2026")

def _hash_pw(pw: str) -> str:
    return _hl.sha256(f"ccc:{pw}:salt".encode()).hexdigest()

def _jwt_encode(payload: dict) -> str:
    header = _b64.urlsafe_b64encode(_json.dumps({"alg":"HS256","typ":"JWT"}).encode()).decode().rstrip("=")
    body = _b64.urlsafe_b64encode(_json.dumps(payload).encode()).decode().rstrip("=")
    sig = _hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), _hl.sha256).hexdigest()[:43]
    return f"{header}.{body}.{sig}"

def _jwt_decode(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        body = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = _json.loads(_b64.urlsafe_b64decode(body))
        if payload.get("exp", 0) < _time.time():
            return None
        return payload
    except Exception:
        return None

def verify_api_key(request: Request):
    """API 키 또는 JWT 토큰으로 인증"""
    # JWT 먼저 체크
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = _jwt_decode(auth[7:])
        if payload:
            request.state.user = payload
            return
    # API 키 폴백
    key = request.headers.get("X-API-Key", "")
    if key == API_KEY:
        request.state.user = {"sub": "api", "role": "admin"}
        return
    raise HTTPException(status_code=401, detail="Not authenticated")

def get_current_user(request: Request) -> dict:
    """현재 로그인 사용자 반환"""
    return getattr(request.state, "user", {"sub": "anonymous", "role": "guest"})

# ── DB ─────────────────────────────────────────────
import psycopg2
from psycopg2.extras import RealDictCursor, Json

def _conn():
    return psycopg2.connect(DATABASE_URL)

def _init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                -- 학생 (인증 포함)
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    student_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT DEFAULT '',
                    password_hash TEXT DEFAULT '',
                    role TEXT DEFAULT 'student',
                    grp TEXT DEFAULT '',
                    score INT DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- password_hash 컬럼 추가 (기존 테이블 호환)
                DO $$ BEGIN
                    ALTER TABLE students ADD COLUMN IF NOT EXISTS password_hash TEXT DEFAULT '';
                    ALTER TABLE students ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'student';
                EXCEPTION WHEN others THEN NULL;
                END $$;
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
                    scenario_id TEXT DEFAULT '',
                    red_id TEXT,
                    blue_id TEXT,
                    challenger_id TEXT,
                    defender_id TEXT,
                    red_score INT DEFAULT 0,
                    blue_score INT DEFAULT 0,
                    red_ready BOOLEAN DEFAULT false,
                    blue_ready BOOLEAN DEFAULT false,
                    status TEXT DEFAULT 'waiting',
                    time_limit INT DEFAULT 1800,
                    rules JSONB DEFAULT '{}',
                    result JSONB DEFAULT '{}',
                    block_hash TEXT,
                    started_at TIMESTAMPTZ,
                    ended_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 대전 이벤트 (영속)
                CREATE TABLE IF NOT EXISTS battle_events (
                    id SERIAL PRIMARY KEY,
                    battle_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    team TEXT DEFAULT '',
                    target TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    points INT DEFAULT 0,
                    detail JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 대전 미션 진행
                CREATE TABLE IF NOT EXISTS battle_missions (
                    id SERIAL PRIMARY KEY,
                    battle_id TEXT NOT NULL,
                    team TEXT NOT NULL,
                    mission_order INT NOT NULL,
                    instruction TEXT NOT NULL,
                    hint TEXT DEFAULT '',
                    points INT DEFAULT 10,
                    verify_type TEXT DEFAULT '',
                    verify_expect TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    answer TEXT DEFAULT '',
                    submitted_at TIMESTAMPTZ,
                    UNIQUE(battle_id, team, mission_order)
                );
                -- 스키마 업그레이드
                DO $$ BEGIN
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS scenario_id TEXT DEFAULT '';
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS red_id TEXT;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS blue_id TEXT;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS red_score INT DEFAULT 0;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS blue_score INT DEFAULT 0;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS red_ready BOOLEAN DEFAULT false;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS blue_ready BOOLEAN DEFAULT false;
                    ALTER TABLE battles ADD COLUMN IF NOT EXISTS time_limit INT DEFAULT 1800;
                EXCEPTION WHEN others THEN NULL;
                END $$;
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

# /api prefix → 실제 경로로 리라이트 (UI에서 /api/xxx 호출)
from starlette.middleware.base import BaseHTTPMiddleware
class ApiPrefixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/"):
            request.scope["path"] = request.url.path[4:]  # strip /api
        return await call_next(request)
app.add_middleware(ApiPrefixMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════
#  Root redirect
# ══════════════════════════════════════════════════
@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/app/")

# ══════════════════════════════════════════════════
#  Health
# ══════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok", "service": "ccc-api", "version": "0.1.0"}

# ══════════════════════════════════════════════════
#  Auth (회원가입/로그인/프로필)
# ══════════════════════════════════════════════════
class RegisterBody(BaseModel):
    student_id: str
    name: str
    password: str
    email: str = ""
    group: str = ""

class LoginBody(BaseModel):
    student_id: str
    password: str

@app.post("/auth/register")
def register(body: RegisterBody):
    """회원가입"""
    sid = str(uuid.uuid4())[:8]
    pw_hash = _hash_pw(body.password)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM students WHERE student_id=%s", (body.student_id,))
            if cur.fetchone():
                raise HTTPException(409, "이미 등록된 학번입니다")
            cur.execute(
                """INSERT INTO students (id, student_id, name, email, password_hash, role, grp)
                   VALUES (%s,%s,%s,%s,%s,'student',%s) RETURNING id, student_id, name, email, role, grp""",
                (sid, body.student_id, body.name, body.email, pw_hash, body.group),
            )
            row = cur.fetchone()
            conn.commit()
    token = _jwt_encode({"sub": sid, "student_id": body.student_id, "name": body.name, "role": "student", "exp": _time.time() + 86400 * 7})
    return {"user": dict(row), "token": token}

@app.post("/auth/login")
def login(body: LoginBody):
    """로그인"""
    pw_hash = _hash_pw(body.password)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, student_id, name, email, role, grp, score FROM students WHERE student_id=%s AND password_hash=%s", (body.student_id, pw_hash))
            row = cur.fetchone()
    if not row:
        raise HTTPException(401, "학번 또는 비밀번호가 잘못되었습니다")
    token = _jwt_encode({"sub": row["id"], "student_id": row["student_id"], "name": row["name"], "role": row["role"], "exp": _time.time() + 86400 * 7})
    return {"user": dict(row), "token": token}

@app.get("/auth/me", dependencies=[Depends(verify_api_key)])
def get_me(request: Request):
    """내 프로필"""
    user = get_current_user(request)
    if user.get("sub") == "api":
        return {"user": {"role": "admin", "name": "API Admin"}}
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, student_id, name, email, role, grp, score, created_at FROM students WHERE id=%s", (user["sub"],))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    return {"user": dict(row)}

@app.post("/auth/create-admin")
def create_admin(body: RegisterBody):
    """관리자 계정 생성 (첫 번째 관리자만 가능, 이후는 기존 관리자가 생성)"""
    sid = str(uuid.uuid4())[:8]
    pw_hash = _hash_pw(body.password)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 관리자가 이미 있는지 확인
            cur.execute("SELECT id FROM students WHERE role='admin' OR role='instructor'")
            existing = cur.fetchone()
            if existing:
                # 기존 관리자가 있으면 API 키 필수
                raise HTTPException(403, "관리자가 이미 존재합니다. API 키로 인증 후 생성하세요.")
            cur.execute(
                """INSERT INTO students (id, student_id, name, email, password_hash, role, grp)
                   VALUES (%s,%s,%s,%s,%s,'admin',%s) RETURNING id, student_id, name, role""",
                (sid, body.student_id, body.name, body.email, pw_hash, body.group),
            )
            row = cur.fetchone()
            conn.commit()
    token = _jwt_encode({"sub": sid, "student_id": body.student_id, "name": body.name, "role": "admin", "exp": _time.time() + 86400 * 30})
    return {"user": dict(row), "token": token}

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
#  Education (교안 — opsclaw 교육 콘텐츠)
# ══════════════════════════════════════════════════
import pathlib as _pathlib
_EDUCATION_DIR = os.getenv("EDUCATION_DIR", "/home/opsclaw/opsclaw/contents/education")
_LABS_DIR = str(_pathlib.Path(__file__).parent.parent.parent.parent / "contents" / "labs")

# 과목 매핑 (opsclaw course dir → CCC lab course name) + 그룹
_COURSE_MAP = {
    "course1-attack": {"name": "attack", "title": "사이버 공격/해킹/침투 테스트", "group": "공격 기술", "group_color": "#f85149", "icon": "⚔️", "description": "SQL Injection, XSS, 권한 상승, 네트워크 공격 등 실제 해킹 기법을 학습하고, MITRE ATT&CK 프레임워크에 매핑하여 체계적으로 이해합니다."},
    "course2-security-ops": {"name": "secops", "title": "보안 솔루션 운영", "group": "방어 운영", "group_color": "#3fb950", "icon": "🛡️", "description": "nftables 방화벽, Suricata IPS, Wazuh SIEM, WAF 등 실제 보안 솔루션을 설치하고 운영합니다."},
    "course3-web-vuln": {"name": "web-vuln", "title": "웹 취약점 점검", "group": "공격 기술", "group_color": "#f85149", "icon": "🕷️", "description": "OWASP Top 10 기반 웹 취약점을 체계적으로 점검하고, JuiceShop에서 실습합니다."},
    "course4-compliance": {"name": "compliance", "title": "정보보안 컴플라이언스", "group": "방어 운영", "group_color": "#3fb950", "icon": "📋", "description": "개인정보보호법, ISMS-P, ISO27001, GDPR 등 법규와 인증 체계를 학습합니다."},
    "course5-soc": {"name": "soc", "title": "보안관제 (SOC)", "group": "방어 운영", "group_color": "#3fb950", "icon": "📡", "description": "SOC 분석가의 업무 — 로그 분석, 경보 분류, 인시던트 대응, SIGMA 룰, 위협 인텔리전스를 실습합니다."},
    "course6-cloud-container": {"name": "cloud-container", "title": "클라우드/컨테이너 보안", "group": "방어 운영", "group_color": "#3fb950", "icon": "☁️", "description": "Docker, Kubernetes, AWS 보안, 서버리스 보안을 학습합니다."},
    "course7-ai-security": {"name": "ai-security", "title": "AI/LLM 보안", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🤖", "description": "OpsClaw를 활용한 보안 자동화 — Ollama LLM, 프롬프트 엔지니어링, 탐지 룰 자동 생성을 구축합니다."},
    "course8-ai-safety": {"name": "ai-safety", "title": "AI Safety / Red Teaming", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🧠", "description": "LLM 탈옥, 프롬프트 인젝션, 가드레일, 적대적 입력, RAG 보안, AI Red Teaming을 학습합니다."},
    "course9-autonomous-security": {"name": "autonomous", "title": "자율보안시스템", "group": "AI 보안", "group_color": "#bc8cff", "icon": "⚡", "description": "PoW 작업증명, 강화학습(RL), Experience 메모리, 자율 Red/Blue/Purple Team을 구축합니다."},
    "course10-ai-security-agent": {"name": "ai-agent", "title": "AI 보안 에이전트", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🕹️", "description": "AI 에이전트 기본부터 하네스 구축, 멀티에이전트, RAG, 에이전트 보안까지 실습합니다."},
    "course11-battle": {"name": "battle", "title": "공방전 기초 (Cyber Battle)", "group": "실전", "group_color": "#f97316", "icon": "⚔️", "description": "인프라 간 공격/방어 대전 기초 — 정찰, 취약점, 방화벽, IDS, 1v1, 팀전"},
    "course12-battle-advanced": {"name": "battle-adv", "title": "공방전 심화 (Advanced Battle)", "group": "실전", "group_color": "#f97316", "icon": "🔥", "description": "APT 시나리오, 다단계 침투, 실시간 공방, AI vs AI 대전, 종합 레드/블루팀 운영"},
}
_GROUP_ORDER = ["공격 기술", "방어 운영", "AI 보안", "실전"]

@app.get("/education/courses", dependencies=[Depends(verify_api_key)])
def list_education_courses():
    """교과목 목록 (교안 + 실습 통합)"""
    import glob as _glob
    result = []
    for course_dir in sorted(_glob.glob(os.path.join(_EDUCATION_DIR, "course*/"))):
        dirname = os.path.basename(course_dir.rstrip("/"))
        meta = _COURSE_MAP.get(dirname, {"name": dirname, "title": dirname, "icon": "📖", "description": ""})
        weeks = len([d for d in os.listdir(course_dir) if d.startswith("week")])
        # 대응하는 CCC lab 수
        lab_nonai = len(_glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-nonai", "*.yaml")))
        lab_ai = len(_glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-ai", "*.yaml")))
        result.append({
            "course_dir": dirname,
            "course_id": meta["name"],
            "title": meta["title"],
            "group": meta.get("group", "기타"),
            "group_color": meta.get("group_color", "#8b949e"),
            "icon": meta["icon"],
            "description": meta["description"],
            "weeks": weeks,
            "labs_nonai": lab_nonai,
            "labs_ai": lab_ai,
        })
    # 그룹별 정렬
    groups = []
    for gname in _GROUP_ORDER:
        courses_in_group = [c for c in result if c.get("group") == gname]
        if courses_in_group:
            groups.append({"group": gname, "color": courses_in_group[0]["group_color"], "courses": courses_in_group})
    return {"courses": result, "groups": groups, "total": len(result)}

@app.get("/education/courses/{course_id}/weeks", dependencies=[Depends(verify_api_key)])
def list_course_weeks(course_id: str):
    """과목의 주차별 목록 (교안 제목 + 실습 연결)"""
    # 과목 디렉토리 찾기
    course_dir = None
    for k, v in _COURSE_MAP.items():
        if v["name"] == course_id:
            course_dir = os.path.join(_EDUCATION_DIR, k)
            break
    weeks = []
    if course_dir and os.path.isdir(course_dir):
        import glob as _g
        for wd in sorted(_g.glob(os.path.join(course_dir, "week*/"))):
            wname = os.path.basename(wd.rstrip("/"))
            wnum = int(wname.replace("week", ""))
            lecture_path = os.path.join(wd, "lecture.md")
            title = ""
            if os.path.isfile(lecture_path):
                with open(lecture_path, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    title = first_line.lstrip("# ").replace(f"Week {wnum:02d}: ", "").replace(f"Week {wnum}: ", "")
            weeks.append({
                "week": wnum,
                "title": title,
                "has_lecture": os.path.isfile(lecture_path),
                "lab_nonai_id": f"{course_id}-nonai-week{wnum:02d}",
                "lab_ai_id": f"{course_id}-ai-week{wnum:02d}",
            })
    else:
        # 교안 없는 과목 (battle 등) — lab만
        for w in range(1, 16):
            weeks.append({
                "week": w,
                "title": f"Week {w}",
                "has_lecture": False,
                "lab_nonai_id": f"{course_id}-nonai-week{w:02d}",
                "lab_ai_id": f"{course_id}-ai-week{w:02d}",
            })
    return {"course_id": course_id, "weeks": weeks}

@app.get("/education/lecture/{course_id}/{week}", dependencies=[Depends(verify_api_key)])
def get_lecture(course_id: str, week: int):
    """교안 내용 (markdown)"""
    course_dir = None
    for k, v in _COURSE_MAP.items():
        if v["name"] == course_id:
            course_dir = os.path.join(_EDUCATION_DIR, k)
            break
    if not course_dir:
        raise HTTPException(404, "Course not found")
    lecture_path = os.path.join(course_dir, f"week{week:02d}", "lecture.md")
    if not os.path.isfile(lecture_path):
        raise HTTPException(404, "Lecture not found")
    with open(lecture_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"course_id": course_id, "week": week, "content": content}

# ══════════════════════════════════════════════════
#  Lab Catalog (lab_engine 연동)
# ══════════════════════════════════════════════════

@app.get("/labs/courses", dependencies=[Depends(verify_api_key)])
def lab_courses():
    """교과목 그룹 목록 (로딩 최적화)"""
    from packages.lab_engine import load_all_labs
    labs = load_all_labs(_LABS_DIR)
    groups: dict[str, dict] = {}
    for l in labs:
        base = l.course.replace("-nonai", "").replace("-ai", "")
        if base not in groups:
            groups[base] = {"course": base, "title": "", "versions": set(), "weeks": 0, "total_labs": 0}
        groups[base]["versions"].add(l.version)
        groups[base]["total_labs"] += 1
        groups[base]["weeks"] = max(groups[base]["weeks"], l.week)
        if not groups[base]["title"] and l.title:
            # 첫 번째 제목에서 과목명 추출
            groups[base]["title"] = l.title.split("—")[0].split("(")[0].strip() if "—" in l.title or "(" in l.title else l.title
    result = []
    for g in sorted(groups.values(), key=lambda x: x["course"]):
        g["versions"] = sorted(g["versions"])
        result.append(g)
    return {"courses": result, "total": len(result)}

@app.get("/labs/catalog", dependencies=[Depends(verify_api_key)])
def lab_catalog(course: str | None = None, version: str | None = None):
    """등록된 실습 YAML 목록 (course 필터로 교과목별 로드)"""
    from packages.lab_engine import load_all_labs, lab_summary, validate_lab
    labs = load_all_labs(_LABS_DIR)
    if course:
        labs = [l for l in labs if l.course == course or l.course.startswith(course)]
    if version:
        labs = [l for l in labs if l.version == version]
    result = []
    for l in labs:
        s = lab_summary(l)
        errors = validate_lab(l)
        s["valid"] = len(errors) == 0
        s["errors"] = errors
        result.append(s)
    return {"labs": result, "total": len(result)}

@app.get("/labs/catalog/{lab_id}", dependencies=[Depends(verify_api_key)])
def get_lab_detail(lab_id: str, request: Request):
    """실습 상세 (steps 포함). admin=true 쿼리파라미터 + API키로 정답 노출"""
    from packages.lab_engine import load_all_labs
    is_admin = request.query_params.get("admin") == "true"
    labs = load_all_labs(_LABS_DIR)
    for l in labs:
        if l.lab_id == lab_id:
            steps = []
            for s in l.steps:
                step_data = {
                    "order": s.order, "instruction": s.instruction,
                    "hint": s.hint, "category": s.category, "points": s.points,
                }
                if l.version == "ai" and s.script:
                    step_data["script"] = s.script
                    step_data["risk_level"] = s.risk_level
                if s.verify:
                    step_data["verify"] = {"type": s.verify.type, "expect": s.verify.expect, "field": s.verify.field}
                # admin만 정답 노출
                if is_admin:
                    if s.answer:
                        step_data["answer"] = s.answer
                    if s.answer_detail:
                        step_data["answer_detail"] = s.answer_detail
                steps.append(step_data)
            return {
                "lab_id": l.lab_id, "title": l.title, "version": l.version,
                "course": l.course, "week": l.week, "description": l.description,
                "objectives": l.objectives, "difficulty": l.difficulty,
                "duration_minutes": l.duration_minutes, "total_points": l.total_points,
                "pass_threshold": l.pass_threshold, "steps": steps,
                "has_answers": any(s.answer for s in l.steps),
            }
    raise HTTPException(404, "Lab not found")

@app.post("/labs/evaluate", dependencies=[Depends(verify_api_key)])
def evaluate_lab_submission(lab_id: str, student_id: str, submissions: list[dict[str, Any]] = []):
    """실습 결과 평가 (lab_engine 검증)"""
    from packages.lab_engine import load_all_labs, evaluate_lab
    labs = load_all_labs(_LABS_DIR)
    lab = next((l for l in labs if l.lab_id == lab_id), None)
    if not lab:
        raise HTTPException(404, "Lab not found")
    result = evaluate_lab(lab, submissions, student_id)
    return {
        "lab_id": result.lab_id, "student_id": result.student_id,
        "passed": result.passed, "total_points": result.total_points,
        "earned_points": result.earned_points,
        "step_results": [
            {"order": sr.order, "passed": sr.passed, "points_earned": sr.points_earned, "message": sr.message}
            for sr in result.step_results
        ],
    }

class AutoVerifyRequest(BaseModel):
    lab_id: str
    student_id: str
    subagent_url: str  # 학생 인프라의 SubAgent URL

@app.post("/labs/auto-verify", dependencies=[Depends(verify_api_key)])
def auto_verify_lab_endpoint(body: AutoVerifyRequest):
    """SubAgent를 통해 학생 인프라에서 실습 완료 여부를 자동 검증.
    학생이 제출한 evidence가 아니라, 실제 인프라 상태를 직접 확인한다."""
    from packages.lab_engine import load_all_labs, auto_verify_lab
    labs = load_all_labs(_LABS_DIR)
    lab = next((l for l in labs if l.lab_id == body.lab_id), None)
    if not lab:
        raise HTTPException(404, "Lab not found")

    result = auto_verify_lab(lab, body.subagent_url, body.student_id)

    # 통과 시 DB에 기록 + PoW 블록 생성
    if result.passed:
        import hashlib as _hl
        with _conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # lab_completion 기록
                lid = str(uuid.uuid4())[:8]
                cur.execute(
                    """INSERT INTO lab_completions (id, student_id, lab_id, status, evidence, completed_at)
                       VALUES (%s,%s,%s,'completed',%s,now())
                       ON CONFLICT (student_id, lab_id) DO UPDATE SET status='completed', evidence=EXCLUDED.evidence, completed_at=now()""",
                    (lid, body.student_id, body.lab_id,
                     Json({"auto_verified": True, "subagent_url": body.subagent_url,
                           "earned_points": result.earned_points, "total_points": result.total_points,
                           "steps_passed": sum(1 for sr in result.step_results if sr.passed)})),
                )
                # PoW 블록
                prev_hash = "0" * 64
                cur.execute("SELECT block_hash FROM pow_blocks ORDER BY id DESC LIMIT 1")
                prev = cur.fetchone()
                if prev:
                    prev_hash = prev["block_hash"]
                block_data = f"auto-verify:{body.student_id}:{body.lab_id}:{prev_hash}:{result.earned_points}"
                block_hash = _hl.sha256(block_data.encode()).hexdigest()
                cur.execute(
                    """INSERT INTO pow_blocks (agent_id, block_index, block_hash, prev_hash, nonce, context_type, context_id, reward_amount)
                       VALUES (%s, (SELECT COALESCE(MAX(block_index),0)+1 FROM pow_blocks WHERE agent_id=%s), %s, %s, 0, 'lab-auto', %s, %s)""",
                    (body.student_id, body.student_id, block_hash, prev_hash, body.lab_id, float(result.earned_points)),
                )
                conn.commit()
        result.block_hash = block_hash

    return {
        "lab_id": result.lab_id, "student_id": result.student_id,
        "passed": result.passed, "total_points": result.total_points,
        "earned_points": result.earned_points,
        "block_hash": result.block_hash,
        "verification_method": "auto (SubAgent direct)",
        "step_results": [
            {"order": sr.order, "passed": sr.passed, "points_earned": sr.points_earned,
             "message": sr.message, "evidence": {k: str(v)[:200] for k, v in sr.evidence.items()} if sr.evidence else {}}
            for sr in result.step_results
        ],
    }

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
#  Battle Scenarios (시나리오 관리)
# ══════════════════════════════════════════════════
import yaml as _yaml
_SCENARIOS_DIR = str(_pathlib.Path(__file__).parent.parent.parent.parent / "contents" / "battle-scenarios")

@app.get("/battles/scenarios", dependencies=[Depends(verify_api_key)])
def list_scenarios():
    """사용 가능한 대전 시나리오 목록"""
    import glob
    scenarios = []
    for f in sorted(glob.glob(os.path.join(_SCENARIOS_DIR, "*.yaml"))):
        with open(f, encoding="utf-8") as fh:
            d = _yaml.safe_load(fh)
        scenarios.append({
            "id": d["id"], "title": d["title"], "description": d.get("description", ""),
            "difficulty": d.get("difficulty", "medium"), "time_limit": d.get("time_limit", 1800),
            "red_missions": len(d.get("red_missions", [])), "blue_missions": len(d.get("blue_missions", [])),
        })
    return {"scenarios": scenarios}

def _load_scenario(scenario_id: str) -> dict | None:
    import glob
    for f in glob.glob(os.path.join(_SCENARIOS_DIR, "*.yaml")):
        with open(f, encoding="utf-8") as fh:
            d = _yaml.safe_load(fh)
        if d.get("id") == scenario_id:
            return d
    return None

# ══════════════════════════════════════════════════
#  Battles (대전)
# ══════════════════════════════════════════════════
class BattleCreateBody(BaseModel):
    scenario_id: str
    mode: str = "manual"
    time_limit: int | None = None  # None이면 시나리오 기본값

@app.post("/battles/create", dependencies=[Depends(verify_api_key)])
def create_battle(body: BattleCreateBody, request: Request):
    """대전 개설 (admin/instructor 또는 학생)"""
    user = get_current_user(request)
    scenario = _load_scenario(body.scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    bid = str(uuid.uuid4())[:8]
    tl = body.time_limit or scenario.get("time_limit", 1800)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO battles (id, battle_type, mode, scenario_id, status, time_limit, rules)
                   VALUES (%s, %s, %s, %s, 'waiting', %s, %s) RETURNING *""",
                (bid, scenario.get("battle_type", "1v1"), body.mode, body.scenario_id, tl, Json({"created_by": user.get("sub", "")})),
            )
            row = cur.fetchone()
            conn.commit()
    return {"battle": dict(row), "scenario": {"title": scenario["title"], "description": scenario.get("description", "")}}

class BattleJoinBody(BaseModel):
    team: str  # "red" or "blue"

@app.post("/battles/{bid}/join", dependencies=[Depends(verify_api_key)])
def join_battle(bid: str, body: BattleJoinBody, request: Request):
    """대전 참가 (역할 선택: red/blue)"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    team = body.team.lower()
    if team not in ("red", "blue"):
        raise HTTPException(400, "team must be 'red' or 'blue'")
    col = "red_id" if team == "red" else "blue_id"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404, "Battle not found")
            if battle["status"] != "waiting":
                raise HTTPException(400, "Battle is not waiting for players")
            if battle.get(col):
                raise HTTPException(400, f"{team} team already has a player")
            cur.execute(f"UPDATE battles SET {col}=%s WHERE id=%s RETURNING *", (uid, bid))
            row = cur.fetchone()
            conn.commit()
    return {"battle": dict(row), "joined_as": team}

@app.post("/battles/{bid}/ready", dependencies=[Depends(verify_api_key)])
def ready_battle(bid: str, request: Request):
    """Ready 표시. 양측 모두 ready면 자동 시작 + 미션 로드."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404)
            # 어느 팀인지
            if battle["red_id"] == uid:
                cur.execute("UPDATE battles SET red_ready=true WHERE id=%s", (bid,))
            elif battle["blue_id"] == uid:
                cur.execute("UPDATE battles SET blue_ready=true WHERE id=%s", (bid,))
            else:
                raise HTTPException(403, "You are not in this battle")
            conn.commit()
            # 양측 모두 ready?
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if battle["red_ready"] and battle["blue_ready"] and battle["red_id"] and battle["blue_id"]:
                # 시작! 미션 로드
                cur.execute("UPDATE battles SET status='active', started_at=now() WHERE id=%s", (bid,))
                # 시나리오 미션 DB에 삽입
                scenario = _load_scenario(battle["scenario_id"])
                if scenario:
                    for m in scenario.get("red_missions", []):
                        cur.execute(
                            "INSERT INTO battle_missions (battle_id, team, mission_order, instruction, hint, points, verify_type, verify_expect) VALUES (%s,'red',%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                            (bid, m["order"], m["instruction"], m.get("hint",""), m.get("points",10), m.get("verify",{}).get("type",""), m.get("verify",{}).get("expect","")),
                        )
                    for m in scenario.get("blue_missions", []):
                        cur.execute(
                            "INSERT INTO battle_missions (battle_id, team, mission_order, instruction, hint, points, verify_type, verify_expect) VALUES (%s,'blue',%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                            (bid, m["order"], m["instruction"], m.get("hint",""), m.get("points",10), m.get("verify",{}).get("type",""), m.get("verify",{}).get("expect","")),
                        )
                conn.commit()
                cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
                battle = cur.fetchone()
    started = battle["status"] == "active"
    return {"battle": dict(battle), "started": started}

@app.get("/battles/{bid}/my-missions", dependencies=[Depends(verify_api_key)])
def get_my_missions(bid: str, request: Request):
    """내 미션 목록 (진행 상태 포함)"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404)
            team = "red" if battle["red_id"] == uid else "blue" if battle["blue_id"] == uid else None
            if not team:
                raise HTTPException(403, "Not in this battle")
            cur.execute("SELECT * FROM battle_missions WHERE battle_id=%s AND team=%s ORDER BY mission_order", (bid, team))
            missions = cur.fetchall()
            # 상대 점수
            cur.execute("SELECT COALESCE(sum(points),0) as pts FROM battle_missions WHERE battle_id=%s AND team=%s AND status='completed'", (bid, "red"))
            red_pts = cur.fetchone()["pts"]
            cur.execute("SELECT COALESCE(sum(points),0) as pts FROM battle_missions WHERE battle_id=%s AND team=%s AND status='completed'", (bid, "blue"))
            blue_pts = cur.fetchone()["pts"]
    # 남은 시간
    remaining = battle["time_limit"]
    if battle["started_at"]:
        import datetime
        elapsed = (datetime.datetime.now(datetime.timezone.utc) - battle["started_at"].replace(tzinfo=datetime.timezone.utc)).total_seconds()
        remaining = max(0, battle["time_limit"] - elapsed)
    return {
        "battle_id": bid, "team": team, "status": battle["status"],
        "red_score": red_pts, "blue_score": blue_pts,
        "time_remaining": round(remaining),
        "missions": [dict(m) for m in missions],
    }

class MissionSubmitBody(BaseModel):
    mission_order: int
    answer: str

@app.post("/battles/{bid}/submit-mission", dependencies=[Depends(verify_api_key)])
def submit_mission(bid: str, body: MissionSubmitBody, request: Request):
    """미션 답변 제출 + 검증"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle or battle["status"] != "active":
                raise HTTPException(400, "Battle not active")
            team = "red" if battle["red_id"] == uid else "blue" if battle["blue_id"] == uid else None
            if not team:
                raise HTTPException(403, "Not in this battle")
            cur.execute("SELECT * FROM battle_missions WHERE battle_id=%s AND team=%s AND mission_order=%s", (bid, team, body.mission_order))
            mission = cur.fetchone()
            if not mission:
                raise HTTPException(404, "Mission not found")
            if mission["status"] == "completed":
                return {"status": "already_completed", "points": mission["points"]}
            # 검증
            passed = False
            msg = ""
            if mission["verify_type"] == "output_contains":
                if mission["verify_expect"].lower() in body.answer.lower():
                    passed = True
                    msg = f"Found '{mission['verify_expect']}'"
                else:
                    msg = f"'{mission['verify_expect']}' not found"
            elif mission["verify_type"]:
                # 기타 검증 타입은 일단 통과
                passed = bool(body.answer.strip())
                msg = "Answer submitted"
            else:
                passed = bool(body.answer.strip())
                msg = "No verification rule"
            if passed:
                cur.execute("UPDATE battle_missions SET status='completed', answer=%s, submitted_at=now() WHERE id=%s", (body.answer, mission["id"]))
                # 이벤트 기록
                cur.execute(
                    "INSERT INTO battle_events (battle_id, event_type, actor, team, description, points) VALUES (%s,'mission_complete',%s,%s,%s,%s)",
                    (bid, uid, team, f"Mission {body.mission_order} completed", mission["points"]),
                )
                # 점수 갱신
                score_col = "red_score" if team == "red" else "blue_score"
                cur.execute(f"UPDATE battles SET {score_col}={score_col}+%s WHERE id=%s", (mission["points"], bid))
            conn.commit()
    return {"passed": passed, "message": msg, "points": mission["points"] if passed else 0}

@app.post("/battles/{bid}/start", dependencies=[Depends(verify_api_key)])
def force_start_battle(bid: str, request: Request):
    """관리자 강제 시작"""
    user = get_current_user(request)
    if user.get("role") not in ("admin", "instructor"):
        raise HTTPException(403, "Admin only")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("UPDATE battles SET status='active', started_at=now() WHERE id=%s RETURNING *", (bid,))
            row = cur.fetchone()
            conn.commit()
    return {"battle": dict(row) if row else None}

class BattleEventInput(BaseModel):
    event_type: str   # attack, defend, detect, block, exploit, alert
    actor: str        # student_id
    target: str = ""
    description: str = ""
    points: int = 0
    detail: dict[str, Any] = {}

@app.post("/battles/{bid}/event", dependencies=[Depends(verify_api_key)])
def add_battle_event(bid: str, body: BattleEventInput):
    """대전 이벤트 추가 (실시간 스트리밍)"""
    from packages.battle_engine import add_event, BattleEvent, get_battle
    event = BattleEvent(
        event_type=body.event_type, actor=body.actor, target=body.target,
        description=body.description, points=body.points, detail=body.detail,
    )
    try:
        state = add_event(bid, event)
    except ValueError:
        raise HTTPException(404, "Battle not found in engine")
    # DB에 결과 동기화
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE battles SET result=result || %s WHERE id=%s",
                (Json({"last_event": body.event_type, "challenger_score": state.challenger_score, "defender_score": state.defender_score}), bid),
            )
            conn.commit()
    return {"state": state.to_dict(), "event": event.to_dict()}

@app.get("/battles/{bid}/events", dependencies=[Depends(verify_api_key)])
def get_battle_events(bid: str, since: float = 0):
    """대전 이벤트 목록 (실시간 폴링용)"""
    from packages.battle_engine import get_events, get_battle
    state = get_battle(bid)
    events = get_events(bid, since)
    return {
        "battle": state.to_dict() if state else None,
        "events": [e.to_dict() for e in events],
        "total": len(events),
    }

@app.get("/battles/{bid}/stats", dependencies=[Depends(verify_api_key)])
def get_battle_stats(bid: str):
    """대전 통계"""
    from packages.battle_engine import battle_stats
    stats = battle_stats(bid)
    if not stats:
        raise HTTPException(404, "Battle not found")
    return stats

@app.get("/battles/active", dependencies=[Depends(verify_api_key)])
def get_active_battles():
    """진행 중인 대전 목록 (관전용)"""
    from packages.battle_engine import get_active_battles
    return {"battles": [b.to_dict() for b in get_active_battles()]}

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
    q = "SELECT b.*, s1.name as red_name, s2.name as blue_name FROM battles b LEFT JOIN students s1 ON b.red_id=s1.id LEFT JOIN students s2 ON b.blue_id=s2.id"
    params: list = []
    if status:
        q += " WHERE b.status=%s"; params.append(status)
    q += " ORDER BY b.created_at DESC"
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

@app.get("/blockchain/stats", dependencies=[Depends(verify_api_key)])
def blockchain_stats():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT count(*) as total_blocks, COALESCE(sum(reward_amount),0) as total_reward FROM pow_blocks")
            row = cur.fetchone()
            cur.execute("SELECT count(DISTINCT agent_id) as agents FROM pow_blocks")
            agents = cur.fetchone()["agents"]
    return {"total_blocks": row["total_blocks"], "total_reward": float(row["total_reward"]), "agents": agents}

@app.get("/battles/events/recent", dependencies=[Depends(verify_api_key)])
def recent_battle_events():
    """최근 대전 이벤트 (UI용)"""
    from packages.battle_engine import get_all_battles
    events = []
    for b in get_all_battles():
        for e in b.events[-5:]:
            events.append({**e.to_dict(), "battle_id": b.battle_id})
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return events[:20]

# ══════════════════════════════════════════════════
#  WebSocket (대전 실시간)
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
from fastapi.responses import FileResponse

_ui_dist = pathlib.Path(__file__).parent.parent.parent / "ccc-ui" / "dist"
if _ui_dist.exists():
    @app.get("/app/{path:path}")
    def spa_fallback(path: str):
        fpath = _ui_dist / path
        if fpath.is_file():
            return FileResponse(str(fpath))
        return FileResponse(str(_ui_dist / "index.html"))

    app.mount("/app", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
