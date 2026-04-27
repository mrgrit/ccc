"""ccc-api — Cyber Combat Commander 교육 플랫폼 API (:9100)"""
from __future__ import annotations
import os
import re as _re
import uuid
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Config ────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ccc:ccc@127.0.0.1:5434/ccc")
API_KEY = os.getenv("CCC_API_KEY", "ccc-api-key-2026")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MANAGER_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
LLM_SUBAGENT_MODEL = os.getenv("LLM_SUBAGENT_MODEL", "gemma3:4b")

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
                    role TEXT DEFAULT 'trainee',
                    rank TEXT DEFAULT 'rookie',
                    grp TEXT DEFAULT '',
                    score INT DEFAULT 0,
                    total_blocks INT DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 그룹
                CREATE TABLE IF NOT EXISTS ccc_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- 그룹별 과목 접근 권한
                CREATE TABLE IF NOT EXISTS group_courses (
                    group_id TEXT REFERENCES ccc_groups(id) ON DELETE CASCADE,
                    course_id TEXT NOT NULL,
                    PRIMARY KEY(group_id, course_id)
                );
                -- 승급 이력
                CREATE TABLE IF NOT EXISTS rank_history (
                    id SERIAL PRIMARY KEY,
                    student_id TEXT REFERENCES students(id),
                    old_rank TEXT,
                    new_rank TEXT,
                    reason TEXT DEFAULT '',
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
                -- CTF 문제
                CREATE TABLE IF NOT EXISTS ctf_challenges (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT DEFAULT 'misc',
                    description TEXT DEFAULT '',
                    flag TEXT NOT NULL,
                    points INT DEFAULT 100,
                    difficulty TEXT DEFAULT 'medium',
                    hint TEXT DEFAULT '',
                    min_blocks INT DEFAULT 0,
                    courses JSONB DEFAULT '[]',
                    created_at TIMESTAMPTZ DEFAULT now()
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
                    verify_semantic JSONB DEFAULT '{}'::jsonb,
                    status TEXT DEFAULT 'pending',
                    answer TEXT DEFAULT '',
                    submitted_at TIMESTAMPTZ,
                    UNIQUE(battle_id, team, mission_order)
                );
                -- 기존 DB 호환: verify_semantic 컬럼이 없으면 추가
                ALTER TABLE battle_missions ADD COLUMN IF NOT EXISTS verify_semantic JSONB DEFAULT '{}'::jsonb;

                -- P12 자율 공방전 — 다중 팀 (역할 고정 X, 모두 attacker+defender 동시)
                CREATE TABLE IF NOT EXISTS battle_participants (
                    id SERIAL PRIMARY KEY,
                    battle_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    team_no INT NOT NULL,
                    attacker_ip TEXT DEFAULT '',
                    defense_ips JSONB DEFAULT '[]'::jsonb,
                    score INT DEFAULT 0,
                    attacks_landed INT DEFAULT 0,
                    defenses_blocked INT DEFAULT 0,
                    own_breaches INT DEFAULT 0,
                    joined_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(battle_id, user_id),
                    UNIQUE(battle_id, team_no)
                );
                CREATE INDEX IF NOT EXISTS idx_bp_battle ON battle_participants(battle_id);

                -- 자율전 attack/defense claim — 사용자가 제출, semantic judge 채점
                CREATE TABLE IF NOT EXISTS battle_attack_claims (
                    id SERIAL PRIMARY KEY,
                    battle_id TEXT NOT NULL,
                    claimant_user_id TEXT NOT NULL,
                    claim_type TEXT NOT NULL,           -- attack | defense | recovery
                    target_team_no INT,                  -- 공격 대상 팀 (attack 일 때)
                    source_team_no INT,                  -- 공격 출처 팀 (defense 일 때)
                    title TEXT DEFAULT '',
                    evidence TEXT NOT NULL,              -- 학생 제출 증거 (명령+stdout+캡처)
                    judged BOOLEAN DEFAULT FALSE,
                    accepted BOOLEAN DEFAULT FALSE,
                    points_awarded INT DEFAULT 0,
                    judge_reason TEXT DEFAULT '',
                    submitted_at TIMESTAMPTZ DEFAULT now(),
                    judged_at TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS idx_bac_battle ON battle_attack_claims(battle_id);
                CREATE INDEX IF NOT EXISTS idx_bac_claimant ON battle_attack_claims(claimant_user_id);

                -- P13 VulnSite catalog — 다양한 취약 사이트 + 3 난이도
                CREATE TABLE IF NOT EXISTS vuln_sites (
                    id           TEXT PRIMARY KEY,    -- 'juiceshop' / 'neobank' 등
                    name         TEXT NOT NULL,
                    theme        TEXT DEFAULT '',     -- e-commerce / banking / gov / medical / devops / ai-chatbot
                    tech_stack   TEXT DEFAULT '',
                    base_port    INT DEFAULT 0,       -- 기본 포트 (mode 별로 +0/+10/+20)
                    description  TEXT DEFAULT '',
                    repo_path    TEXT DEFAULT '',     -- contents/vuln-sites/<id>/
                    status       TEXT DEFAULT 'available',  -- available / planned / deprecated
                    created_at   TIMESTAMPTZ DEFAULT now()
                );

                CREATE TABLE IF NOT EXISTS vuln_site_modes (
                    id              SERIAL PRIMARY KEY,
                    site_id         TEXT NOT NULL REFERENCES vuln_sites(id) ON DELETE CASCADE,
                    difficulty      TEXT NOT NULL,    -- easy / normal / hard
                    port            INT NOT NULL,
                    vuln_classes    JSONB DEFAULT '[]'::jsonb,   -- ['A03 SQLi', 'A07 BrokenAuth', ...]
                    vuln_count      INT DEFAULT 0,    -- 해당 모드의 취약점 개수 (rich vulnerability 강조)
                    chain_depth     INT DEFAULT 1,    -- 다단계 chain 최대 길이
                    seed_doc        TEXT DEFAULT '',  -- contents/vuln-sites/<id>/seed-<difficulty>.md
                    available       BOOLEAN DEFAULT TRUE,
                    UNIQUE(site_id, difficulty)
                );
                CREATE INDEX IF NOT EXISTS idx_vsm_site ON vuln_site_modes(site_id);

                -- battles 테이블에 vuln_site_id + difficulty 컬럼 추가
                ALTER TABLE battles ADD COLUMN IF NOT EXISTS vuln_site_id TEXT DEFAULT '';
                ALTER TABLE battles ADD COLUMN IF NOT EXISTS difficulty TEXT DEFAULT 'normal';

                -- 카탈로그 seed (기존 2 + 신규 5 placeholder)
                INSERT INTO vuln_sites (id, name, theme, tech_stack, base_port, description, repo_path, status) VALUES
                    ('juiceshop', 'OWASP JuiceShop', 'e-commerce', 'Express + Angular', 3000,
                     'OWASP 공식 광범위 취약 e-커머스. OWASP Top 10 전반.',
                     'contents/vuln-sites/juiceshop', 'available'),
                    ('dvwa', 'DVWA', 'general', 'Apache + PHP + MySQL', 8080,
                     'PHP 기반 학습용 — SQLi/XSS/CSRF 기본 취약점.',
                     'contents/vuln-sites/dvwa', 'available'),
                    ('neobank', 'NeoBank', 'banking', 'Django + Vue', 3001,
                     '금융/뱅킹 — IDOR · 금융 트랜잭션 race · 인가 우회 · JWT 약점 강조.',
                     'contents/vuln-sites/neobank', 'planned'),
                    ('govportal', 'GovPortal', 'government', 'Spring + React', 3002,
                     '정부 민원 — SAML 우회 · 권한 상승 · 파일 업로드 · CSRF 강조.',
                     'contents/vuln-sites/govportal', 'planned'),
                    ('mediforum', 'MediForum', 'medical', 'Node + Next.js', 3003,
                     '의료 커뮤니티 — stored XSS · CSRF · 개인정보 노출 · API 인증 강조.',
                     'contents/vuln-sites/mediforum', 'planned'),
                    ('adminconsole', 'AdminConsole', 'devops', 'FastAPI + Svelte', 3004,
                     'DevOps 관리자 패널 — SSRF · RCE · 비밀번호 분실 흐름 · 명령 주입 강조.',
                     'contents/vuln-sites/adminconsole', 'planned'),
                    ('aicompanion', 'AICompanion', 'ai-chatbot', 'Flask + LangChain', 3005,
                     'LLM 기반 챗봇 — Prompt injection · RAG 인젝션 · jailbreak · 모델 탈취 강조.',
                     'contents/vuln-sites/aicompanion', 'planned')
                ON CONFLICT (id) DO NOTHING;

                -- mode seed (기존 2 사이트는 normal 만, 신규 5는 placeholder)
                INSERT INTO vuln_site_modes (site_id, difficulty, port, vuln_classes, vuln_count, chain_depth, available) VALUES
                    ('juiceshop', 'normal', 3000,
                     '["A01 BAC","A02 Crypto","A03 Injection","A05 Misconfig","A07 AuthFail","A08 Integrity","A10 SSRF"]'::jsonb,
                     50, 3, TRUE),
                    ('dvwa', 'easy', 8080, '["A03 SQLi basic","A03 XSS reflected","A05 Misconfig"]'::jsonb, 12, 1, TRUE),
                    ('dvwa', 'normal', 8080, '["A03 SQLi","A03 XSS","A07 BrokenAuth","A08 CSRF","A09 Logging"]'::jsonb, 20, 2, TRUE),
                    ('neobank', 'easy', 3011, '["A01 IDOR basic"]'::jsonb, 15, 1, FALSE),
                    ('neobank', 'normal', 3001, '["A01 IDOR","A02 Crypto JWT","A04 BizLogic race","A07 BrokenAuth","A08 Integrity"]'::jsonb, 30, 3, FALSE),
                    ('neobank', 'hard', 3001, '["Chain CCAT","Chain Arbitrage","Chain JWT 위조","Chain SSRF C2","Chain WebShell"]'::jsonb, 40, 5, FALSE),
                    ('govportal', 'hard', 3002, '["Chain SAML 위조","Chain Auth 3중 우회","Chain XXE+LFI","Chain PII+CSRF","Chain webshell"]'::jsonb, 35, 5, FALSE),
                    ('mediforum', 'hard', 3003, '["Chain 의사 DM XSS","Chain SVG→Admin","Chain SSN→사회공학","Chain API token","Chain pickle DB dump"]'::jsonb, 32, 5, FALSE),
                    ('adminconsole', 'hard', 3004, '["Chain cmd RCE","Chain SSRF cloud","Chain reset→exec","Chain pickle/yaml","Chain upload/JWT"]'::jsonb, 38, 5, FALSE),
                    ('aicompanion', 'hard', 3005, '["Chain RAG poison","Chain stored→admin","Chain tool→exfil","Chain jailbreak","Chain CSRF persistent"]'::jsonb, 35, 5, FALSE),
                    ('govportal', 'normal', 3002, '["A01 BAC","A05 SAML","A07 AuthFail","A08 Upload","A10 SSRF"]'::jsonb, 25, 3, FALSE),
                    ('mediforum', 'normal', 3003, '["A03 stored XSS","A08 CSRF","A02 PII","A07 API Auth"]'::jsonb, 22, 2, FALSE),
                    ('adminconsole', 'normal', 3004, '["A10 SSRF","A03 RCE","A07 PwReset","A03 Cmd Inject"]'::jsonb, 28, 4, FALSE),
                    ('aicompanion', 'normal', 3005, '["LLM01 PromptInject","LLM02 InsecureOutput","LLM03 RAG poisoning","LLM06 Sensitive","LLM10 Model theft"]'::jsonb, 25, 3, FALSE)
                ON CONFLICT (site_id, difficulty) DO NOTHING;

                -- P13 Phase 2 빌드 완료 사이트 promote (planned → available)
                UPDATE vuln_sites SET status='available'
                  WHERE id IN ('neobank','govportal','mediforum','adminconsole','aicompanion') AND status='planned';
                UPDATE vuln_site_modes SET available=TRUE
                  WHERE site_id IN ('neobank','govportal','mediforum','adminconsole','aicompanion') AND difficulty='normal';
                -- P13 Phase 3 — 5 사이트 hard mode (각 5 chain seed-hard.md) 활성화
                UPDATE vuln_site_modes SET available=TRUE
                  WHERE site_id IN ('neobank','govportal','mediforum','adminconsole','aicompanion')
                    AND difficulty='hard';
                -- PoW 블록 (레거시 호환)
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
                -- CCCNet 독립 블록체인
                CREATE TABLE IF NOT EXISTS cccnet_blocks (
                    id SERIAL PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    block_index INT NOT NULL,
                    block_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    nonce INT DEFAULT 0,
                    difficulty INT DEFAULT 3,
                    block_type TEXT NOT NULL,
                    context_id TEXT DEFAULT '',
                    points INT DEFAULT 0,
                    description TEXT DEFAULT '',
                    metadata JSONB DEFAULT '{}',
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
            # V1 마이그레이션: group_id FK
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS group_id TEXT REFERENCES ccc_groups(id)")
            conn.commit()

# ── 기본 그룹 시딩 ──────────────────────────────────
DEFAULT_GROUPS = [
    {"id": "commander", "name": "commander", "display_name": "Commander", "description": "전체 관리 (admin)"},
    {"id": "trainer", "name": "trainer", "display_name": "Trainer", "description": "교관 (Instructor / Drill Leader / Chief Instructor)"},
    {"id": "trainee", "name": "trainee", "display_name": "Trainee", "description": "교육생 (Rookie → Apprentice → Skilled → Expert → Elite)"},
]

# 승급 기준
RANK_ORDER = ["rookie", "apprentice", "skilled", "expert", "elite"]
RANK_REQUIREMENTS = {
    "apprentice": {"labs_completed": 3, "total_blocks": 50},
    "skilled": {"labs_completed": 16, "total_blocks": 200, "ctf_solved": 3},
    "expert": {"labs_completed": 60, "total_blocks": 500, "battles": 5, "advanced_courses": 1},
    "elite": {"labs_completed": 120, "total_blocks": 1000, "battles": 10, "ctf_solved": 20, "advanced_courses": 3},
}

def _seed_groups():
    with _conn() as conn:
        with conn.cursor() as cur:
            for g in DEFAULT_GROUPS:
                cur.execute(
                    "INSERT INTO ccc_groups (id, name, display_name, description) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (g["id"], g["name"], g["display_name"], g["description"]),
                )
            conn.commit()

# ── Lifespan ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _init_db()
        _seed_groups()
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
                """INSERT INTO students (id, student_id, name, email, password_hash, role, rank, grp)
                   VALUES (%s,%s,%s,%s,%s,'trainee','rookie',%s) RETURNING id, student_id, name, email, role, rank, grp""",
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

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


@app.post("/auth/google")
def google_login(body: dict):
    """Google OAuth 로그인 — 클라이언트에서 받은 credential(JWT) 검증 후 CCC 토큰 발급.

    프론트엔드에서 Google Sign-In 후 credential을 POST.
    서버가 Google 공개키로 검증 → 이메일 기반 학생 조회/자동 생성 → JWT 발급.
    """
    credential = body.get("credential", "")
    if not credential:
        raise HTTPException(400, "Google credential 필요")

    # Google JWT 디코딩 (서명 검증은 Google 공개키로)
    try:
        import urllib.request as _ur
        # Google 공개키로 검증 (간소화: base64 디코딩 후 페이로드 추출)
        parts = credential.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT")
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = _json.loads(_b64.urlsafe_b64decode(payload_b64))

        email = payload.get("email", "")
        name = payload.get("name", "")
        picture = payload.get("picture", "")
        google_sub = payload.get("sub", "")

        if not email:
            raise ValueError("이메일 없음")

        # Google Client ID 검증 (설정된 경우)
        if GOOGLE_CLIENT_ID and payload.get("aud") != GOOGLE_CLIENT_ID:
            raise ValueError("Client ID 불일치")

    except Exception as e:
        raise HTTPException(401, f"Google 인증 실패: {e}")

    # 이메일로 기존 학생 조회 또는 자동 생성
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, student_id, name, email, role, rank, grp, score FROM students WHERE email=%s", (email,))
            row = cur.fetchone()

            if not row:
                # 자동 가입 — Google 이메일 = student_id, 랜덤 비밀번호
                sid = str(uuid.uuid4())[:8]
                student_id = email.split("@")[0]  # 이메일 앞부분을 학번으로
                pw_hash = _hash_pw(str(uuid.uuid4()))  # 랜덤 (Google 로그인 전용)
                cur.execute(
                    """INSERT INTO students (id, student_id, name, email, password_hash, role, rank, metadata)
                       VALUES (%s,%s,%s,%s,%s,'trainee','rookie',%s)
                       ON CONFLICT (student_id) DO UPDATE SET email=EXCLUDED.email, name=EXCLUDED.name
                       RETURNING id, student_id, name, email, role, rank, grp, score""",
                    (sid, student_id, name, email, pw_hash,
                     Json({"google_sub": google_sub, "picture": picture})),
                )
                row = cur.fetchone()
                conn.commit()

    token = _jwt_encode({
        "sub": row["id"], "student_id": row["student_id"],
        "name": row["name"], "role": row.get("role", "trainee"),
        "exp": _time.time() + 86400 * 7,
    })
    return {"user": dict(row), "token": token}


@app.get("/auth/me", dependencies=[Depends(verify_api_key)])
def get_me(request: Request):
    """내 프로필 (metadata에 credentials 포함)"""
    user = get_current_user(request)
    if user.get("sub") == "api":
        return {"user": {"role": "admin", "name": "API Admin"}}
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, student_id, name, email, role, rank, grp, group_id, score, total_blocks, metadata, created_at FROM students WHERE id=%s", (user["sub"],))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "User not found")
    d = dict(row)
    # metadata에서 credentials 추출
    meta = d.get("metadata") or {}
    d["credentials"] = meta.get("credentials", {})
    return {"user": d}

@app.get("/profile", dependencies=[Depends(verify_api_key)])
def get_profile(request: Request):
    """프로필 상세 — 본인 또는 admin만 접근"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (uid,))
            student = cur.fetchone()
            if not student:
                raise HTTPException(404)
            # 인프라 정보
            cur.execute("SELECT id, infra_name, ip, subagent_url, status, vm_config FROM student_infras WHERE student_id=%s", (uid,))
            infras = [dict(r) for r in cur.fetchall()]
            # 랭크 히스토리
            cur.execute("SELECT * FROM rank_history WHERE student_id=%s ORDER BY created_at DESC LIMIT 10", (uid,))
            rank_hist = [dict(r) for r in cur.fetchall()]
    meta = (student.get("metadata") or {})
    return {
        "student": {k: v for k, v in dict(student).items() if k != "password_hash"},
        "credentials": meta.get("credentials", {}),
        "infras": infras,
        "rank_history": rank_hist,
    }

@app.post("/profile/credentials", dependencies=[Depends(verify_api_key)])
def save_credentials(body: dict[str, Any], request: Request):
    """계정 정보 저장 — 본인 또는 admin만"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT metadata FROM students WHERE id=%s", (uid,))
            row = cur.fetchone()
            meta = row[0] if row and row[0] else {}
            meta["credentials"] = body
            cur.execute("UPDATE students SET metadata=%s WHERE id=%s", (Json(meta), uid))
            conn.commit()
    return {"saved": True}

@app.post("/profile/credentials/refresh", dependencies=[Depends(verify_api_key)])
def refresh_credentials(request: Request):
    """본인 siem VM에서 OpenCTI/Wazuh 자격을 다시 수집해 metadata에 저장.

    온보딩 시 siem status != healthy 등으로 누락된 경우 수동 재수집.
    """
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT ip FROM student_infras WHERE student_id=%s AND infra_name LIKE %s",
                (uid, "%-siem"),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "siem infra not found for this user")

    siem_ip = row["ip"]
    from packages.bastion import run_command as _rc
    creds = {}
    try:
        r = _rc(siem_ip,
                "sudo tar -axf /tmp/wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt -O "
                "2>/dev/null | grep -A1 \"indexer_username: 'admin'\" | tail -1 | awk '{print $2}' | tr -d \"'\"",
                timeout=15)
        wazuh_pw = (r.get("stdout", "") or "").strip()
    except Exception as e:
        wazuh_pw = ""
    if wazuh_pw:
        creds["wazuh_dashboard"] = {"url": f"https://{siem_ip}:443", "user": "admin", "password": wazuh_pw}
        creds["wazuh_api"] = {"url": f"https://{siem_ip}:55000", "user": "wazuh-wui", "password": wazuh_pw}
    creds["opencti"] = {"url": f"http://{siem_ip}:8080", "user": "admin@opencti.io", "password": "CCC2026!"}

    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT metadata FROM students WHERE id=%s", (uid,))
            meta = (cur.fetchone() or [{}])[0] or {}
            meta["credentials"] = {**meta.get("credentials", {}), **creds}
            cur.execute("UPDATE students SET metadata=%s WHERE id=%s", (Json(meta), uid))
            conn.commit()
    return {"refreshed": list(creds.keys()), "wazuh_pw_found": bool(wazuh_pw), "siem_ip": siem_ip}

@app.post("/profile/siem-proxy/setup", dependencies=[Depends(verify_api_key)])
def setup_siem_proxy(request: Request):
    """secu에 siem 내부망 proxy(DNAT + ARP) 재설정.

    온보딩 순서가 siem → secu로 뒤집혔거나 secu 재온보딩 후 규칙 초기화된 경우 사용.
    멱등적: 이미 설정되어 있으면 skip.
    """
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT infra_name, ip FROM student_infras WHERE student_id=%s AND (infra_name LIKE %s OR infra_name LIKE %s)",
                        (uid, "%-siem", "%-secu"))
            rows = {r["infra_name"].rsplit("-", 1)[-1]: r["ip"] for r in cur.fetchall()}
    if "siem" not in rows or "secu" not in rows:
        raise HTTPException(404, f"need both siem and secu infras: found={list(rows.keys())}")

    siem_ext_ip = rows["siem"]
    secu_ip = rows["secu"]
    from packages.bastion import run_command as _rc
    setup_script = f"""
set -e
sudo tee /etc/sysctl.d/99-siem-proxy.conf >/dev/null << SYSCTL_EOF
net.ipv4.conf.all.proxy_arp=1
net.ipv4.conf.ens37.proxy_arp=1
net.ipv4.ip_forward=1
SYSCTL_EOF
sudo sysctl -p /etc/sysctl.d/99-siem-proxy.conf >/dev/null
for port in 1514 1515 55000 443 8080; do
  if ! sudo nft list chain ip nat prerouting 2>/dev/null | grep -q "daddr 10.20.30.100 tcp dport $port"; then
    sudo nft add rule ip nat prerouting iifname ens37 ip daddr 10.20.30.100 tcp dport $port dnat to {siem_ext_ip}:$port
  fi
done
if ! sudo nft list chain ip nat postrouting 2>/dev/null | grep -q "daddr {siem_ext_ip} oifname \\"ens33\\" masquerade"; then
  sudo nft add rule ip nat postrouting ip daddr {siem_ext_ip} oifname ens33 masquerade
fi
sudo bash -c 'echo "#!/usr/sbin/nft -f" > /etc/nftables.conf; echo "flush ruleset" >> /etc/nftables.conf; nft list ruleset >> /etc/nftables.conf'
sudo chmod 755 /etc/nftables.conf
sudo tee /etc/systemd/system/siem-neigh-proxy.service >/dev/null << NEIGH_EOF
[Unit]
Description=SIEM neighbor proxy for 10.20.30.100
After=network-online.target nftables.service
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/ip neigh add proxy 10.20.30.100 dev ens37
ExecStop=/usr/sbin/ip neigh del proxy 10.20.30.100 dev ens37
[Install]
WantedBy=multi-user.target
NEIGH_EOF
sudo systemctl daemon-reload
sudo systemctl enable --now siem-neigh-proxy >/dev/null 2>&1
echo "SIEM_PROXY_OK"
"""
    try:
        r = _rc(secu_ip, setup_script, timeout=45)
    except Exception as e:
        raise HTTPException(500, f"secu unreachable: {e}")
    ok = "SIEM_PROXY_OK" in (r.get("stdout", "") or "")
    return {"success": ok, "secu_ip": secu_ip, "siem_ext_ip": siem_ext_ip,
            "stdout": (r.get("stdout", "") or "")[-400:]}

class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str

@app.post("/auth/change-password", dependencies=[Depends(verify_api_key)])
def change_password(body: ChangePasswordBody, request: Request):
    """비밀번호 변경"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    old_hash = _hash_pw(body.current_password)
    new_hash = _hash_pw(body.new_password)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM students WHERE id=%s AND password_hash=%s", (uid, old_hash))
            if not cur.fetchone():
                raise HTTPException(401, "현재 비밀번호가 일치하지 않습니다")
            cur.execute("UPDATE students SET password_hash=%s WHERE id=%s", (new_hash, uid))
            conn.commit()
    return {"message": "비밀번호가 변경되었습니다"}

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
#  Groups (그룹 관리)
# ══════════════════════════════════════════════════
class GroupBody(BaseModel):
    name: str
    display_name: str = ""
    description: str = ""

@app.get("/groups", dependencies=[Depends(verify_api_key)])
def list_groups():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT g.*, count(s.id) as member_count,
                       array_agg(DISTINCT gc.course_id) FILTER (WHERE gc.course_id IS NOT NULL) as courses
                FROM ccc_groups g
                LEFT JOIN students s ON s.group_id = g.id
                LEFT JOIN group_courses gc ON gc.group_id = g.id
                GROUP BY g.id ORDER BY g.created_at
            """)
            rows = cur.fetchall()
    return {"groups": [dict(r) for r in rows]}

@app.post("/groups", dependencies=[Depends(verify_api_key)])
def create_group(body: GroupBody, request: Request):
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander"):
        raise HTTPException(403, "Commander only")
    gid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("INSERT INTO ccc_groups (id, name, display_name, description) VALUES (%s,%s,%s,%s) RETURNING *",
                        (gid, body.name, body.display_name or body.name, body.description))
            row = cur.fetchone()
            conn.commit()
    return {"group": dict(row)}

@app.delete("/groups/{gid}", dependencies=[Depends(verify_api_key)])
def delete_group(gid: str, request: Request):
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander"):
        raise HTTPException(403, "Commander only")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET group_id=NULL WHERE group_id=%s", (gid,))
            cur.execute("DELETE FROM ccc_groups WHERE id=%s", (gid,))
            conn.commit()
    return {"deleted": gid}

class GroupAssignBody(BaseModel):
    student_id: str
    group_id: str

@app.post("/groups/assign", dependencies=[Depends(verify_api_key)])
def assign_group(body: GroupAssignBody, request: Request):
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander", "trainer"):
        raise HTTPException(403, "Commander/Trainer only")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET group_id=%s WHERE id=%s", (body.group_id, body.student_id))
            conn.commit()
    return {"assigned": body.student_id, "group": body.group_id}

class GroupCourseBody(BaseModel):
    course_ids: list[str]

@app.put("/groups/{gid}/courses", dependencies=[Depends(verify_api_key)])
def set_group_courses(gid: str, body: GroupCourseBody, request: Request):
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander"):
        raise HTTPException(403, "Commander only")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM group_courses WHERE group_id=%s", (gid,))
            for cid in body.course_ids:
                cur.execute("INSERT INTO group_courses (group_id, course_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (gid, cid))
            conn.commit()
    return {"group_id": gid, "courses": body.course_ids}

# ══════════════════════════════════════════════════
#  Rank (승급)
# ══════════════════════════════════════════════════
@app.get("/rank/check/{student_id}", dependencies=[Depends(verify_api_key)])
def check_rank(student_id: str):
    """승급 가능 여부 확인"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (student_id,))
            student = cur.fetchone()
            if not student:
                raise HTTPException(404)
            current = student.get("rank", "rookie")
            idx = RANK_ORDER.index(current) if current in RANK_ORDER else 0
            if idx >= len(RANK_ORDER) - 1:
                return {"current_rank": current, "next_rank": None, "can_promote": False, "message": "최고 등급입니다"}
            next_rank = RANK_ORDER[idx + 1]
            req = RANK_REQUIREMENTS.get(next_rank, {})
            # 현재 통계
            cur.execute("SELECT count(*) as cnt FROM lab_completions WHERE student_id=%s AND status='completed'", (student_id,))
            labs = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM ctf_submissions WHERE student_id=%s AND correct=true", (student_id,))
            ctf = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM battles WHERE (red_id=%s OR blue_id=%s) AND status='completed'", (student_id, student_id))
            battles = cur.fetchone()["cnt"]
            blocks = student.get("total_blocks", 0)

    met = {
        "labs_completed": labs >= req.get("labs_completed", 0),
        "total_blocks": blocks >= req.get("total_blocks", 0),
        "ctf_solved": ctf >= req.get("ctf_solved", 0),
        "battles": battles >= req.get("battles", 0),
    }
    can = all(met.values())
    return {
        "current_rank": current, "next_rank": next_rank, "can_promote": can,
        "requirements": req, "current_stats": {"labs": labs, "blocks": blocks, "ctf": ctf, "battles": battles},
        "met": met,
    }

@app.post("/rank/promote/{student_id}", dependencies=[Depends(verify_api_key)])
def promote_rank(student_id: str, request: Request):
    """승급 실행"""
    check = check_rank(student_id)
    if not check["can_promote"]:
        raise HTTPException(400, f"승급 조건 미충족: {check['met']}")
    new_rank = check["next_rank"]
    old_rank = check["current_rank"]
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET rank=%s WHERE id=%s", (new_rank, student_id))
            cur.execute("INSERT INTO rank_history (student_id, old_rank, new_rank, reason) VALUES (%s,%s,%s,%s)",
                        (student_id, old_rank, new_rank, f"Auto promotion: met all requirements"))
            conn.commit()
    # CCCNet 블록 생성 (conn.commit 이후)
    try:
        _cccnet_add_block(student_id, "rank_up", ACHIEVEMENT_POINTS.get("rank_up", 1000),
                          f"{old_rank}->{new_rank}", f"Promoted from {old_rank} to {new_rank}")
    except Exception:
        pass
    return {"promoted": True, "old_rank": old_rank, "new_rank": new_rank}

def _try_auto_promote(student_id: str) -> dict | None:
    """자동 승급 시도 — 조건 충족 시 승급 실행. 실패해도 호출자를 깨뜨리지 않음."""
    try:
        check = check_rank(student_id)
        if not check.get("can_promote"):
            return None
        new_rank = check["next_rank"]
        old_rank = check["current_rank"]
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE students SET rank=%s WHERE id=%s", (new_rank, student_id))
                cur.execute("INSERT INTO rank_history (student_id, old_rank, new_rank, reason) VALUES (%s,%s,%s,%s)",
                            (student_id, old_rank, new_rank, "Auto promotion: met all requirements"))
                conn.commit()
        try:
            _cccnet_add_block(student_id, "rank_up", ACHIEVEMENT_POINTS.get("rank_up", 1000),
                              f"{old_rank}->{new_rank}", f"Auto-promoted from {old_rank} to {new_rank}")
        except Exception:
            pass
        return {"promoted": True, "old_rank": old_rank, "new_rank": new_rank}
    except Exception:
        return None

@app.get("/rank/history/{student_id}", dependencies=[Depends(verify_api_key)])
def rank_history(student_id: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM rank_history WHERE student_id=%s ORDER BY created_at DESC", (student_id,))
            rows = cur.fetchall()
    return {"history": [dict(r) for r in rows]}

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

# 각 VM에 설치할 소프트웨어 정의
VM_SOFTWARE = {
    "attacker": {"os": "Kali Linux", "packages": ["nmap","metasploit-framework","hydra","sqlmap","gobuster","impacket-scripts","bloodhound","crackmapexec","burpsuite","nikto","dirb","enum4linux","seclists"], "subagent": True},
    "secu": {"os": "Ubuntu", "packages": ["nftables","suricata","sysmon-for-linux","osquery","auditd"], "subagent": True},
    "web": {"os": "Ubuntu", "packages": ["sysmon-for-linux","osquery","auditd","libapache2-mod-security2","docker.io"], "apps": ["JuiceShop(:3000)","DVWA(:8081)","WebGoat(:8082)","HackableApp(:8083)"], "subagent": True},
    "siem": {"os": "Ubuntu", "packages": ["sysmon-for-linux","osquery","auditd","wazuh-manager","wazuh-dashboard","sigma-cli"], "apps": ["Wazuh(:443)","OpenCTI(:9400)"], "subagent": True},
    "windows": {"os": "Windows 10/11", "packages": ["sysmon","osquery","Ghidra","x64dbg","PEStudio","FLOSS","Autopsy","FTK-Imager","Wireshark","Process-Monitor"], "subagent": True},
    "manager": {"os": "Ubuntu", "packages": ["ollama","ccc-bastion"], "subagent": True},
}

# 내부 IP 할당 — 환경변수로 오버라이드 가능 (다른 네트워크 환경 지원)
INTERNAL_IPS = {
    "attacker": os.getenv("VM_ATTACKER_IP", "10.20.30.201"),
    "secu":     os.getenv("VM_SECU_IP",     "10.20.30.1"),
    "web":      os.getenv("VM_WEB_IP",      "10.20.30.80"),
    "siem":     os.getenv("VM_SIEM_IP",     "10.20.30.100"),
    "manager":  os.getenv("VM_MANAGER_IP",  "10.20.30.200"),
    "windows":  os.getenv("VM_WINDOWS_IP",  "10.20.30.50"),
}

class VMCredential(BaseModel):
    ssh_user: str = ""
    ssh_password: str = ""

class InfraSetupBody(BaseModel):
    attacker_ip: str            # 외부 IP (온보딩용)
    secu_ip: str
    web_ip: str
    siem_ip: str
    manager_ip: str
    windows_ip: str = ""
    gpu_url: str = ""
    manager_model: str = ""
    subagent_model: str = ""
    ssh_user: str = "ccc"       # 기본 SSH 계정
    ssh_password: str = "1"
    # VM별 개별 SSH 계정 (비어있으면 기본값 사용)
    vm_credentials: dict[str, VMCredential] = {}

    def get_cred(self, role: str) -> tuple[str, str]:
        """VM별 SSH 계정 반환 (개별 설정 > 기본값)"""
        cred = self.vm_credentials.get(role)
        if cred and cred.ssh_user:
            return cred.ssh_user, cred.ssh_password or self.ssh_password
        return self.ssh_user, self.ssh_password

@app.post("/infras/setup", dependencies=[Depends(verify_api_key)])
def setup_infra(body: InfraSetupBody, request: Request):
    """학생 인프라 일괄 등록 — 외부 IP로 온보딩, 내부 IP는 고정 자동 할당"""
    user = get_current_user(request)
    uid = user.get("sub", "")

    # 순서: secu(GW) → siem(wazuh-manager) → web/attacker(agent 등록) → manager
    vms = [
        {"role": "secu", "name": f"{uid}-secu", "ip": body.secu_ip, "internal_ip": INTERNAL_IPS["secu"], "subagent": True},
        {"role": "siem", "name": f"{uid}-siem", "ip": body.siem_ip, "internal_ip": INTERNAL_IPS["siem"], "subagent": True},
        {"role": "web", "name": f"{uid}-web", "ip": body.web_ip, "internal_ip": INTERNAL_IPS["web"], "subagent": True},
        {"role": "attacker", "name": f"{uid}-attacker", "ip": body.attacker_ip, "internal_ip": INTERNAL_IPS["attacker"], "subagent": True},
        {"role": "manager", "name": f"{uid}-manager", "ip": body.manager_ip, "internal_ip": INTERNAL_IPS["manager"], "subagent": True},
    ]
    if body.windows_ip:
        vms.append({"role": "windows", "name": f"{uid}-windows", "ip": body.windows_ip, "internal_ip": INTERNAL_IPS["windows"], "subagent": True})

    results = []
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 기존 인프라 삭제 (재등록 지원)
            cur.execute("DELETE FROM student_infras WHERE student_id=%s", (uid,))

            for vm in vms:
                iid = str(uuid.uuid4())[:8]
                subagent_url = f"http://{vm['ip']}:8002" if vm["subagent"] else ""
                cur.execute(
                    """INSERT INTO student_infras (id, student_id, infra_name, ip, subagent_url, vm_config, status)
                       VALUES (%s,%s,%s,%s,%s,%s,'registered')""",
                    (iid, uid, vm["name"], vm["ip"], subagent_url,
                     Json({"role": vm["role"], "ssh_user": body.get_cred(vm["role"])[0],
                           "external_ip": vm["ip"], "internal_ip": vm["internal_ip"],
                           "gpu_url": body.gpu_url,
                           "manager_model": body.manager_model, "subagent_model": body.subagent_model})),
                )
                results.append({"id": iid, "role": vm["role"], "ip": vm["ip"], "subagent_url": subagent_url, "status": "registered"})
            conn.commit()

    return {
        "infras": results,
        "message": "인프라 등록 완료. 온보딩은 /infras/onboard를 호출하세요.",
    }

@app.post("/infras/onboard", dependencies=[Depends(verify_api_key)])
def onboard_infra(body: InfraSetupBody, request: Request):
    """인프라 온보딩 (SSE 스트리밍) — VM별 진행상황을 실시간 전송"""
    from starlette.responses import StreamingResponse
    from packages.bastion import onboard_vm
    import json as _j

    user = get_current_user(request)
    uid = user.get("sub", "")

    # 순서: secu(GW) → siem(wazuh-manager) → web/attacker(agent 등록) → manager
    vms = [
        {"role": "secu", "ip": body.secu_ip},
        {"role": "siem", "ip": body.siem_ip},
        {"role": "web", "ip": body.web_ip},
        {"role": "attacker", "ip": body.attacker_ip},
        {"role": "manager", "ip": body.manager_ip},
    ]
    if body.windows_ip:
        vms.append({"role": "windows", "ip": body.windows_ip})

    def stream():
        total = len(vms)
        for i, vm in enumerate(vms):
            # 시작 알림
            yield f"data: {_j.dumps({'event': 'start', 'role': vm['role'], 'ip': vm['ip'], 'progress': f'{i+1}/{total}'}, ensure_ascii=False)}\n\n"

            try:
                _user, _pass = body.get_cred(vm["role"])
                ob = onboard_vm(ip=vm["ip"], role=vm["role"], user=_user, password=_pass,
                                gpu_url=body.gpu_url, manager_model=body.manager_model, subagent_model=body.subagent_model)
                status = "healthy" if ob.get("healthy") else "error"

                # DB 상태 업데이트
                with _conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE student_infras SET status=%s WHERE student_id=%s AND ip=%s",
                                    (status, uid, vm["ip"]))
                        conn.commit()

                # Bastion assets 등록 (온보딩 완료 시 즉시 반영)
                try:
                    import httpx as _hx
                    _asset_ip = ob.get("internal_ip") or vm["ip"]
                    _asset_status = "healthy" if ob.get("healthy") else "unreachable"
                    _hx.put(
                        f"http://localhost:8003/assets/{vm['role']}",
                        json={"ip": _asset_ip, "status": _asset_status, "notes": "온보딩"},
                        timeout=5,
                    )
                except Exception:
                    pass  # bastion API 미실행 시 무시

                # 단계별 결과 전송 (에러 내용 포함)
                for step in ob.get("steps", []):
                    step_data = {
                        'event': 'step', 'role': vm['role'],
                        'step': step.get('step', ''),
                        'success': step.get('success', False),
                    }
                    if not step.get('success'):
                        step_data['stderr'] = step.get('stderr', '')[:500]
                        step_data['stdout'] = step.get('stdout', '')[:300]
                    yield f"data: {_j.dumps(step_data, ensure_ascii=False)}\n\n"

                # SIEM 온보딩 시 credential 수집 + 저장 (status 무관 — 설치 성공 시점에 시도)
                if vm["role"] == "siem":
                    try:
                        from packages.bastion import run_command as _rc
                        _creds = {}
                        # Wazuh Dashboard 비밀번호 (sudo 포함으로 권한 확보)
                        _r = _rc(vm["ip"], "sudo tar -axf /tmp/wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt -O 2>/dev/null | grep -A1 \"indexer_username: 'admin'\" | tail -1 | awk '{print $2}' | tr -d \"'\"", timeout=15)
                        wazuh_pw = _r.get("stdout", "").strip()
                        if wazuh_pw:
                            _creds["wazuh_dashboard"] = {"url": f"https://{vm['ip']}:443", "user": "admin", "password": wazuh_pw}
                            _creds["wazuh_api"] = {"url": f"https://{vm['ip']}:55000", "user": "wazuh-wui", "password": wazuh_pw}
                        _creds["opencti"] = {"url": f"http://{vm['ip']}:8080", "user": "admin@opencti.io", "password": "CCC2026!"}
                        # DB에 저장 (기존 값과 병합)
                        if _creds:
                            with _conn() as _c2:
                                with _c2.cursor() as _cur2:
                                    _cur2.execute("SELECT metadata FROM students WHERE id=%s", (uid,))
                                    _meta = (_cur2.fetchone() or [{}])[0] or {}
                                    _meta["credentials"] = {**_meta.get("credentials", {}), **_creds}
                                    _cur2.execute("UPDATE students SET metadata=%s WHERE id=%s", (Json(_meta), uid))
                                    _c2.commit()
                            yield f"data: {_j.dumps({'event': 'credentials', 'role': 'siem', 'saved': list(_creds.keys())}, ensure_ascii=False)}\n\n"
                    except Exception as _e:
                        yield f"data: {_j.dumps({'event': 'credentials_error', 'role': 'siem', 'error': str(_e)[:200]}, ensure_ascii=False)}\n\n"

                    # SIEM VM은 내부 IP(10.20.30.100)가 Docker bridge에만 존재해 내부망 격리 →
                    # secu(gateway)에 DNAT + ARP proxy 자동 설정 (agent들이 siem 접근 가능하게)
                    try:
                        from packages.bastion import run_command as _rc
                        siem_ext_ip = vm["ip"]  # siem 외부 IP (192.168.0.x)
                        # 같은 학생의 secu 찾기
                        with _conn() as _c3:
                            with _c3.cursor(cursor_factory=RealDictCursor) as _cur3:
                                _cur3.execute(
                                    "SELECT ip FROM student_infras WHERE student_id=%s AND infra_name LIKE %s",
                                    (uid, "%-secu"),
                                )
                                _secu_row = _cur3.fetchone()
                        if _secu_row:
                            secu_ip = _secu_row["ip"]
                            # 멱등적 setup 스크립트: sysctl + nft DNAT + ARP neigh proxy + 영구화
                            setup_script = f"""
set -e
# 1) sysctl 영구
sudo tee /etc/sysctl.d/99-siem-proxy.conf >/dev/null << SYSCTL_EOF
net.ipv4.conf.all.proxy_arp=1
net.ipv4.conf.ens37.proxy_arp=1
net.ipv4.ip_forward=1
SYSCTL_EOF
sudo sysctl -p /etc/sysctl.d/99-siem-proxy.conf >/dev/null
# 2) nft DNAT (이미 있으면 skip)
for port in 1514 1515 55000 443 8080; do
  if ! sudo nft list chain ip nat prerouting 2>/dev/null | grep -q "daddr 10.20.30.100 tcp dport $port"; then
    sudo nft add rule ip nat prerouting iifname ens37 ip daddr 10.20.30.100 tcp dport $port dnat to {siem_ext_ip}:$port
  fi
done
# postrouting masquerade
if ! sudo nft list chain ip nat postrouting 2>/dev/null | grep -q "daddr {siem_ext_ip} oifname \\"ens33\\" masquerade"; then
  sudo nft add rule ip nat postrouting ip daddr {siem_ext_ip} oifname ens33 masquerade
fi
# 3) nft 영구화 (/etc/nftables.conf)
sudo bash -c 'echo "#!/usr/sbin/nft -f" > /etc/nftables.conf; echo "flush ruleset" >> /etc/nftables.conf; nft list ruleset >> /etc/nftables.conf'
sudo chmod 755 /etc/nftables.conf
# 4) ARP neigh proxy systemd
sudo tee /etc/systemd/system/siem-neigh-proxy.service >/dev/null << NEIGH_EOF
[Unit]
Description=SIEM neighbor proxy for 10.20.30.100
After=network-online.target nftables.service
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/ip neigh add proxy 10.20.30.100 dev ens37
ExecStop=/usr/sbin/ip neigh del proxy 10.20.30.100 dev ens37
[Install]
WantedBy=multi-user.target
NEIGH_EOF
sudo systemctl daemon-reload
sudo systemctl enable --now siem-neigh-proxy >/dev/null 2>&1
echo "SIEM_PROXY_OK"
"""
                            r = _rc(secu_ip, setup_script, timeout=30)
                            ok = "SIEM_PROXY_OK" in (r.get("stdout", "") or "")
                            yield f"data: {_j.dumps({'event': 'siem_proxy_setup', 'secu_ip': secu_ip, 'siem_ext_ip': siem_ext_ip, 'success': ok}, ensure_ascii=False)}\n\n"
                        else:
                            yield f"data: {_j.dumps({'event': 'siem_proxy_skip', 'reason': 'secu infra not found — 학생의 secu를 먼저 온보딩해야 함'}, ensure_ascii=False)}\n\n"
                    except Exception as _e:
                        yield f"data: {_j.dumps({'event': 'siem_proxy_error', 'error': str(_e)[:200]}, ensure_ascii=False)}\n\n"

                # early return 에러가 있으면 원인 명시
                done_data = {'event': 'done', 'role': vm['role'], 'status': status, 'progress': f'{i+1}/{total}'}
                if ob.get("error"):
                    done_data['error'] = ob['error']
                yield f"data: {_j.dumps(done_data, ensure_ascii=False)}\n\n"

            except Exception as e:
                yield f"data: {_j.dumps({'event': 'error', 'role': vm['role'], 'message': str(e)[:200]}, ensure_ascii=False)}\n\n"

        yield f"data: {_j.dumps({'event': 'complete', 'total': total}, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

class SingleOnboardBody(BaseModel):
    ip: str
    role: str
    ssh_user: str = "ccc"
    ssh_password: str = "1"
    gpu_url: str = ""
    manager_model: str = ""
    subagent_model: str = ""

@app.post("/infras/{iid}/onboard", dependencies=[Depends(verify_api_key)])
def onboard_single(iid: str, body: SingleOnboardBody, request: Request):
    """단일 VM 재온보딩"""
    from starlette.responses import StreamingResponse
    from packages.bastion import onboard_vm
    import json as _j

    user = get_current_user(request)
    uid = user.get("sub", "")

    def stream():
        yield f"data: {_j.dumps({'event': 'start', 'role': body.role, 'ip': body.ip, 'progress': '1/1'}, ensure_ascii=False)}\n\n"
        try:
            ob = onboard_vm(ip=body.ip, role=body.role, user=body.ssh_user, password=body.ssh_password,
                            gpu_url=body.gpu_url, manager_model=body.manager_model, subagent_model=body.subagent_model)
            status = "healthy" if ob.get("healthy") else "error"
            with _conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE student_infras SET status=%s WHERE id=%s", (status, iid))
                    conn.commit()
            for step in ob.get("steps", []):
                step_data = {'event': 'step', 'role': body.role, 'step': step.get('step', ''), 'success': step.get('success', False)}
                if not step.get('success'):
                    step_data['stderr'] = step.get('stderr', '')[:300]
                yield f"data: {_j.dumps(step_data, ensure_ascii=False)}\n\n"
            # Bastion assets 등록
            try:
                import httpx as _hx
                _hx.put(
                    f"http://localhost:8003/assets/{body.role}",
                    json={"ip": ob.get("internal_ip") or body.ip,
                          "status": "healthy" if ob.get("healthy") else "unreachable",
                          "notes": "온보딩"},
                    timeout=5,
                )
            except Exception:
                pass
            yield f"data: {_j.dumps({'event': 'done', 'role': body.role, 'status': status, 'progress': '1/1'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {_j.dumps({'event': 'error', 'role': body.role, 'message': str(e)[:200]}, ensure_ascii=False)}\n\n"
        yield f"data: {_j.dumps({'event': 'complete', 'total': 1}, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

# ── 온보딩 검수 ──

class VerifyBody(BaseModel):
    include_windows: bool = False

@app.post("/infras/verify", dependencies=[Depends(verify_api_key)])
def verify_infra(body: VerifyBody, request: Request):
    """전체 인프라 검수 (SSE 스트리밍)"""
    from starlette.responses import StreamingResponse
    from packages.bastion.verify import verify_all_stream
    import json as _j

    user = get_current_user(request)
    uid = user.get("sub", "")

    # 유저의 인프라에서 role → ip 매핑
    infra_ips = {}
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT ip, vm_config FROM student_infras WHERE student_id=%s", (uid,))
            for row in cur.fetchall():
                cfg = row.get("vm_config") or {}
                role = cfg.get("role", "")
                if role:
                    infra_ips[role] = row["ip"]

    def stream():
        for evt in verify_all_stream(infra_ips, body.include_windows):
            yield f"data: {_j.dumps(evt, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

@app.post("/infras/{iid}/verify", dependencies=[Depends(verify_api_key)])
def verify_single(iid: str, request: Request):
    """단일 VM 검수 (SSE 스트리밍)"""
    from starlette.responses import StreamingResponse
    from packages.bastion.verify import verify_role
    import json as _j

    user = get_current_user(request)
    uid = user.get("sub", "")

    # 해당 인프라 조회
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT ip, vm_config FROM student_infras WHERE id=%s AND student_id=%s", (iid, uid))
            row = cur.fetchone()
    if not row:
        return {"error": "인프라를 찾을 수 없습니다"}

    cfg = row.get("vm_config") or {}
    role = cfg.get("role", "")
    ip = row["ip"]

    def stream():
        for evt in verify_role(role, ip):
            yield f"data: {_j.dumps(evt, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

# ── Lab 콘텐츠 검증 ──

class LabVerifyBody(BaseModel):
    courses: list[str] = []           # 빈 리스트면 전체
    sample_weeks: list[int] = [1, 8, 15]  # 샘플 주차 (빈 리스트면 전체)
    version: str = "non-ai"

@app.post("/labs/verify-all", dependencies=[Depends(verify_api_key)])
def verify_all_labs(body: LabVerifyBody, request: Request):
    """Lab 콘텐츠 검증 — 실제 인프라에서 Lab step 실행 + verify 통과 확인 (SSE)"""
    from starlette.responses import StreamingResponse
    from packages.bastion.lab_verify import verify_all_labs_stream
    import json as _j

    user = get_current_user(request)
    uid = user.get("sub", "")

    # 유저 인프라에서 VM IP 매핑
    vm_ips = {}
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT ip, vm_config FROM student_infras WHERE student_id=%s", (uid,))
            for row in cur.fetchall():
                cfg = row.get("vm_config") or {}
                role = cfg.get("role", "")
                if role:
                    vm_ips[role] = row["ip"]

    def stream():
        for evt in verify_all_labs_stream(
            _LABS_DIR, vm_ips,
            courses=body.courses or None,
            version=body.version,
            sample_weeks=body.sample_weeks or None,
        ):
            yield f"data: {_j.dumps(evt, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

@app.get("/infras/my", dependencies=[Depends(verify_api_key)])
def my_infra(request: Request):
    """내 인프라 목록 (로그인 사용자)"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM student_infras WHERE student_id=%s ORDER BY created_at", (uid,))
            rows = cur.fetchall()
    # 소프트웨어 정보 추가
    result = []
    for r in rows:
        d = dict(r)
        cfg = d.get("vm_config", {}) or {}
        role = cfg.get("role", "")
        sw = VM_SOFTWARE.get(role, {})
        d["software"] = sw
        result.append(d)
    return {"infras": result, "vm_specs": VM_SOFTWARE}

@app.get("/infras/{iid}/health", dependencies=[Depends(verify_api_key)])
def check_infra_health(iid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM student_infras WHERE id=%s", (iid,))
            infra = cur.fetchone()
    if not infra:
        raise HTTPException(404, "Infra not found")
    from packages.bastion import health_check
    h = health_check(infra["ip"])
    healthy = h.get("status") == "healthy"
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE student_infras SET status=%s WHERE id=%s", ("healthy" if healthy else "unreachable", iid))
            conn.commit()
    return {"infra_id": iid, "healthy": healthy, "subagent_url": infra["subagent_url"]}

# ══════════════════════════════════════════════════
#  LLM 모델 조회 (Ollama 프록시)
# ══════════════════════════════════════════════════
class LLMConnectBody(BaseModel):
    url: str

@app.post("/llm/models", dependencies=[Depends(verify_api_key)])
def llm_models(body: LLMConnectBody):
    """외부 LLM 서버에서 사용 가능한 모델 목록 조회"""
    import httpx
    url = body.url.rstrip("/")
    try:
        r = httpx.get(f"{url}/api/tags", timeout=10.0)
        models = [m["name"] for m in r.json().get("models", [])]
        return {"connected": True, "url": url, "models": models}
    except Exception as e:
        return {"connected": False, "url": url, "models": [], "error": str(e)}

# ══════════════════════════════════════════════════
#  Education (교안)
# ══════════════════════════════════════════════════
import pathlib as _pathlib
_CONTENT_DIR = str(_pathlib.Path(__file__).parent.parent.parent.parent / "contents")
_EDUCATION_DIR = os.getenv("EDUCATION_DIR", os.path.join(_CONTENT_DIR, "education"))
_LABS_DIR = os.path.join(_CONTENT_DIR, "labs")

# 과목 매핑 (course dir → CCC lab course name) + 그룹
_COURSE_MAP = {
    "course1-attack": {"name": "attack", "title": "사이버 공격/해킹/침투 테스트", "group": "공격 기술", "group_color": "#f85149", "icon": "⚔️", "description": "SQL Injection, XSS, 권한 상승, 네트워크 공격 등 실제 해킹 기법을 학습하고, MITRE ATT&CK 프레임워크에 매핑하여 체계적으로 이해합니다."},
    "course2-security-ops": {"name": "secops", "title": "보안 솔루션 운영", "group": "방어 운영", "group_color": "#3fb950", "icon": "🛡️", "description": "nftables 방화벽, Suricata IPS, Wazuh SIEM, WAF 등 실제 보안 솔루션을 설치하고 운영합니다."},
    "course3-web-vuln": {"name": "web-vuln", "title": "웹 취약점 점검", "group": "공격 기술", "group_color": "#f85149", "icon": "🕷️", "description": "OWASP Top 10 기반 웹 취약점을 체계적으로 점검하고, JuiceShop에서 실습합니다."},
    "course4-compliance": {"name": "compliance", "title": "정보보안 컴플라이언스", "group": "방어 운영", "group_color": "#3fb950", "icon": "📋", "description": "개인정보보호법, ISMS-P, ISO27001, GDPR 등 법규와 인증 체계를 학습합니다."},
    "course5-soc": {"name": "soc", "title": "보안관제 (SOC)", "group": "방어 운영", "group_color": "#3fb950", "icon": "📡", "description": "SOC 분석가의 업무 — 로그 분석, 경보 분류, 인시던트 대응, SIGMA 룰, 위협 인텔리전스를 실습합니다."},
    "course6-cloud-container": {"name": "cloud-container", "title": "클라우드/컨테이너 보안", "group": "방어 운영", "group_color": "#3fb950", "icon": "☁️", "description": "Docker, Kubernetes, AWS 보안, 서버리스 보안을 학습합니다."},
    "course7-ai-security": {"name": "ai-security", "min_rank": "skilled", "title": "AI/LLM 보안", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🤖", "description": "Bastion을 활용한 보안 자동화 — Ollama LLM, 프롬프트 엔지니어링, 탐지 룰 자동 생성을 구축합니다."},
    "course8-ai-safety": {"name": "ai-safety", "min_rank": "skilled", "title": "AI Safety / Red Teaming", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🧠", "description": "LLM 탈옥, 프롬프트 인젝션, 가드레일, 적대적 입력, RAG 보안, AI Red Teaming을 학습합니다."},
    "course9-autonomous-security": {"name": "autonomous", "min_rank": "skilled", "title": "자율보안시스템", "group": "AI 보안", "group_color": "#bc8cff", "icon": "⚡", "description": "PoW 작업증명, 강화학습(RL), Experience 메모리, 자율 Red/Blue/Purple Team을 구축합니다."},
    "course10-ai-security-agent": {"name": "ai-agent", "min_rank": "skilled", "title": "AI 보안 에이전트", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🕹️", "description": "AI 에이전트 기본부터 하네스 구축, 멀티에이전트, RAG, 에이전트 보안까지 실습합니다."},
    "course11-battle": {"name": "battle", "title": "공방전 기초 (Cyber Battle)", "group": "실전", "group_color": "#f97316", "icon": "⚔️", "description": "인프라 간 공격/방어 대전 기초 — 정찰, 취약점, 방화벽, IDS, 1v1, 팀전"},
    "course12-battle-advanced": {"name": "battle-adv", "min_rank": "expert", "title": "공방전 심화 (Advanced Battle)", "group": "실전", "group_color": "#f97316", "icon": "🔥", "description": "APT 시나리오, 다단계 침투, 실시간 공방, AI vs AI 대전, 종합 레드/블루팀 운영"},
    "course13-attack-advanced": {"name": "attack-adv", "min_rank": "expert", "title": "사이버 공격 심화 (Advanced Attack)", "group": "공격 기술", "group_color": "#f85149", "icon": "💀", "description": "APT 킬체인, C2 인프라, 측면이동, 권한상승 체인, AD 공격, 공급망 공격, 안티포렌식"},
    "course14-soc-advanced": {"name": "soc-adv", "min_rank": "expert", "title": "보안관제 심화 (Advanced SOC)", "group": "방어 운영", "group_color": "#3fb950", "icon": "🔍", "description": "고급 SIEM 상관분석, SIGMA/YARA, 위협헌팅, SOAR 자동화, 인시던트 포렌식, 악성코드 분석"},
    "course15-ai-safety-advanced": {"name": "ai-safety-adv", "min_rank": "expert", "title": "AI Safety 심화 (Advanced AI Safety)", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🧪", "description": "LLM Red Teaming, 프롬프트 인젝션 심화, 가드레일 우회, AI 에이전트 보안, 모델 탈취/백도어"},
    "course16-physical-pentest": {"name": "physical-pentest", "min_rank": "skilled", "title": "물리 침투 테스트 (Physical Penetration Testing)", "group": "실전", "group_color": "#f97316", "icon": "🔓", "description": "RFID/NFC 복제, USB HID 공격, 무선 해킹, RF 분석, 물리적 접근 통제 우회, 침투 보고서"},
    "course17-iot-security": {"name": "iot-security", "min_rank": "skilled", "title": "IoT/임베디드 보안 (IoT & Embedded Security)", "group": "실전", "group_color": "#f97316", "icon": "📡", "description": "펌웨어 분석, UART/SPI/JTAG 해킹, BLE/Zigbee, IP Camera, SCADA/PLC, 자동차 CAN 버스"},
    "course18-autonomous-systems": {"name": "autonomous-systems", "min_rank": "expert", "title": "드론/로봇/자율시스템 보안 (CPS Security)", "group": "실전", "group_color": "#f97316", "icon": "🤖", "description": "드론 해킹/방어, 자율주행 AI 공격, ROS2 보안, OT/ICS, GPS 스푸핑, CPS 인시던트 대응"},
    "course19-agent-incident-response": {"name": "agent-ir", "min_rank": "expert", "title": "AI Agent 공격 침해대응 (Agent Incident Response)", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🛰️", "description": "Claude Code 급 코딩 에이전트가 공격자로 투입되는 실세계 위협에 대한 실전 대응 교과. Red=Claude Code · Blue=Bastion 공방과 Purple co-evolution(skill·playbook·experience 업그레이드)으로 에이전트 IR 체계를 구축한다."},
    "course20-agent-ir-advanced": {"name": "agent-ir-adv", "min_rank": "expert", "title": "AI Agent 공격 침해대응 심화 (Advanced Agent IR)", "group": "AI 보안", "group_color": "#bc8cff", "icon": "🎯", "description": "C19의 후속. 15가지 서로 다른 에이전트 공격 사례(공급망·RAG 인젝션·AD·클라우드·0-day·Fileless·DNS exfil·K8s·CI/CD·Deepfake·Insider·장기 APT 등)를 각각 공격→탐지→분석→초동대응→보고·공유→재발방지의 전 IR 절차로 다룬다. Human 대응 vs Agent 대응을 사례마다 비교."},
}
_GROUP_ORDER = ["공격 기술", "방어 운영", "AI 보안", "실전"]

@app.get("/education/courses", dependencies=[Depends(verify_api_key)])
def list_education_courses():
    """교과목 목록 (교안 + 실습 통합) — 교안 없어도 labs 기반으로 표시"""
    import glob as _glob
    result = []
    for dirname, meta in _COURSE_MAP.items():
        course_dir = os.path.join(_EDUCATION_DIR, dirname)
        # 교안이 있으면 주차 수를 교안에서, 없으면 labs에서
        if os.path.isdir(course_dir):
            weeks = len([d for d in os.listdir(course_dir) if d.startswith("week")])
        else:
            lab_files = _glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-nonai", "*.yaml"))
            lab_files += _glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-ai", "*.yaml"))
            week_nums = set()
            for f in lab_files:
                m = _re.search(r'week(\d+)', os.path.basename(f))
                if m:
                    week_nums.add(int(m.group(1)))
            weeks = len(week_nums) if week_nums else 15
        lab_nonai = len(_glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-nonai", "*.yaml")))
        lab_ai = len(_glob.glob(os.path.join(_LABS_DIR, f"{meta['name']}-ai", "*.yaml")))
        if weeks == 0 and lab_nonai == 0 and lab_ai == 0:
            continue  # 교안도 실습도 없는 과목은 스킵
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
            "min_rank": meta.get("min_rank", "rookie"),
        })
    groups = []
    for gname in _GROUP_ORDER:
        courses_in_group = [c for c in result if c.get("group") == gname]
        if courses_in_group:
            groups.append({"group": gname, "color": courses_in_group[0]["group_color"], "courses": courses_in_group})
    return {"courses": result, "groups": groups, "total": len(result)}

_CURRICULUM_DIR = os.path.join(_CONTENT_DIR, "curriculum")


def _load_curriculum_mapping(course_id: str) -> dict | None:
    """contents/curriculum/{course_id}-mapping.yaml 로드 — 없으면 None."""
    p = os.path.join(_CURRICULUM_DIR, f"{course_id}-mapping.yaml")
    if not os.path.isfile(p):
        return None
    try:
        import yaml as _yaml
        with open(p, "r", encoding="utf-8") as f:
            return _yaml.safe_load(f) or None
    except Exception:
        return None


@app.get("/education/courses/{course_id}/weeks", dependencies=[Depends(verify_api_key)])
def list_course_weeks(course_id: str):
    """과목의 주차별 목록 (교안 제목 + 실습 연결).

    contents/curriculum/{course_id}-mapping.yaml 가 있으면 D-B 매핑 적용:
    lecture↔lab 가 cross-course many-to-many 로 매핑됨. 매핑 없으면 기존
    주차 번호 자동 join fallback.
    """
    # 과목 디렉토리 찾기
    course_dir = None
    for k, v in _COURSE_MAP.items():
        if v["name"] == course_id:
            course_dir = os.path.join(_EDUCATION_DIR, k)
            break

    mapping = _load_curriculum_mapping(course_id)

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

            # D-B 매핑 우선, 없으면 자동 join
            mapped_labs = None
            if mapping:
                for m in (mapping.get("mappings") or []):
                    if int(m.get("week", -1)) == wnum:
                        mapped_labs = []
                        for lab in (m.get("labs") or []):
                            mapped_labs.append({
                                "lab_id": f"{lab.get('course')}-{lab.get('version','nonai')}-week{int(lab.get('week',1)):02d}",
                                "course": lab.get("course"),
                                "week": lab.get("week"),
                                "version": lab.get("version", "nonai"),
                                "role": lab.get("role", "primary"),
                                "note": lab.get("note", ""),
                            })
                        break

            week_entry = {
                "week": wnum,
                "title": title,
                "has_lecture": os.path.isfile(lecture_path),
                "lab_nonai_id": f"{course_id}-nonai-week{wnum:02d}",
                "lab_ai_id": f"{course_id}-ai-week{wnum:02d}",
            }
            if mapped_labs is not None:
                week_entry["mapped_labs"] = mapped_labs
            weeks.append(week_entry)
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
    return {"course_id": course_id, "weeks": weeks, "has_mapping": mapping is not None}

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

# ── Training aliases (V7: Education → Training) ──
@app.get("/training/courses", dependencies=[Depends(verify_api_key)])
def list_training_courses():
    return list_education_courses()

@app.get("/training/courses/{course_id}/weeks", dependencies=[Depends(verify_api_key)])
def list_training_weeks(course_id: str):
    return list_course_weeks(course_id)

@app.get("/training/lecture/{course_id}/{week}", dependencies=[Depends(verify_api_key)])
def get_training_lecture(course_id: str, week: int):
    return get_lecture(course_id, week)

# ══════════════════════════════════════════════════
#  Papers (admin 전용 — git-ignored)
# ══════════════════════════════════════════════════
_PAPERS_DIR = os.path.join(_CONTENT_DIR, "papers")


def _require_admin(request: Request):
    """verify_api_key 통과 후 role==admin/instructor 여부 재검증."""
    user = getattr(request.state, "user", {})
    if user.get("role") not in ("admin", "instructor"):
        raise HTTPException(status_code=403, detail="admin only")


def _safe_paper_join(*parts: str) -> str:
    """Directory traversal 방어: _PAPERS_DIR 밖으로 벗어나면 404."""
    p = os.path.realpath(os.path.join(_PAPERS_DIR, *parts))
    base = os.path.realpath(_PAPERS_DIR)
    if not (p == base or p.startswith(base + os.sep)):
        raise HTTPException(404, "not found")
    return p


@app.get("/papers", dependencies=[Depends(verify_api_key)])
def list_papers(request: Request):
    """논문 디렉토리 목록 — 각 디렉토리의 파일 리스트 포함."""
    _require_admin(request)
    if not os.path.isdir(_PAPERS_DIR):
        return {"papers": []}
    papers = []
    for name in sorted(os.listdir(_PAPERS_DIR)):
        pdir = _safe_paper_join(name)
        if not os.path.isdir(pdir):
            continue
        files = []
        for root, _, fnames in os.walk(pdir):
            for fn in sorted(fnames):
                if fn.startswith("."):
                    continue
                rel = os.path.relpath(os.path.join(root, fn), pdir)
                files.append({
                    "path": rel,
                    "size": os.path.getsize(os.path.join(root, fn)),
                    "mtime": int(os.path.getmtime(os.path.join(root, fn))),
                })
        papers.append({"id": name, "files": files})
    return {"papers": papers}


@app.get("/papers/{paper_id}/{file_path:path}", dependencies=[Depends(verify_api_key)])
def get_paper_file(paper_id: str, file_path: str, request: Request):
    """특정 논문 파일 내용 반환 (markdown 권장)."""
    _require_admin(request)
    p = _safe_paper_join(paper_id, file_path)
    if not os.path.isfile(p):
        raise HTTPException(404, "file not found")
    # 10MB 초과 파일은 거부 (UI 표시용)
    if os.path.getsize(p) > 10 * 1024 * 1024:
        raise HTTPException(413, "file too large")
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {"paper_id": paper_id, "path": file_path, "content": content}


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
    is_admin = request.query_params.get("admin") in ("true", "1")
    labs = load_all_labs(_LABS_DIR)
    for l in labs:
        if l.lab_id == lab_id:
            steps = []
            for s in l.steps:
                step_data = {
                    "order": s.order, "instruction": s.instruction,
                    "hint": s.hint, "category": s.category, "points": s.points,
                }
                if l.version == "ai":
                    if s.script:
                        step_data["script"] = s.script
                        step_data["risk_level"] = s.risk_level
                    if hasattr(s, 'bastion_prompt') and s.bastion_prompt:
                        step_data["bastion_prompt"] = s.bastion_prompt
                if s.verify:
                    step_data["verify"] = {"type": s.verify.type, "expect": s.verify.expect, "field": s.verify.field}
                    sem = s.verify.semantic or {}
                    if sem:
                        methods = sem.get("acceptable_methods") or []
                        step_data["learning"] = {
                            "intent": sem.get("intent", ""),
                            "success_criteria": sem.get("success_criteria") or [],
                            "primary_method": methods[0] if methods else "",
                            "negative_signs": sem.get("negative_signs") or [],
                        }
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
    subagent_url: str = ""  # 명시적 URL (비면 student_infras DB 에서 자동 조회)

@app.post("/labs/auto-verify", dependencies=[Depends(verify_api_key)])
def auto_verify_lab_endpoint(body: AutoVerifyRequest):
    """SubAgent를 통해 학생 인프라에서 실습 완료 여부를 자동 검증.

    학생이 제출한 evidence가 아니라, 실제 인프라 상태를 직접 확인한다.
    subagent_url 이 비면 student_infras DB 에서 해당 학생의 VM 목록을 조회해
    role → SubAgent URL 매핑을 자동으로 구성한다.
    """
    from packages.lab_engine import load_all_labs, auto_verify_lab
    labs = load_all_labs(_LABS_DIR)
    lab = next((l for l in labs if l.lab_id == body.lab_id), None)
    if not lab:
        raise HTTPException(404, "Lab not found")

    # 학생 VM SubAgent 매핑 자동 조회
    vm_subagents: dict[str, str] = {}
    default_url = body.subagent_url
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT infra_name, ip, subagent_url, vm_config FROM student_infras WHERE student_id=%s AND status IN ('registered','ready')",
                (body.student_id,)
            )
            for row in cur.fetchall():
                sa_url = row.get("subagent_url") or f"http://{row['ip']}:8002"
                # vm_config 에서 role 추출
                cfg = row.get("vm_config") or {}
                if isinstance(cfg, str):
                    import json as _j
                    try: cfg = _j.loads(cfg)
                    except: cfg = {}
                vms = cfg.get("vms", [cfg]) if isinstance(cfg, dict) else cfg
                for vm in (vms if isinstance(vms, list) else [vms]):
                    role = vm.get("role", "") or row.get("infra_name", "")
                    if role:
                        vm_subagents[role] = vm.get("subagent_url") or sa_url
                # fallback: infra_name 으로도 등록
                vm_subagents[row["infra_name"]] = sa_url
                if not default_url:
                    default_url = sa_url
    if not default_url:
        raise HTTPException(400, "학생의 등록된 인프라가 없습니다. /infras/register 또는 subagent_url 파라미터를 사용하세요.")

    result = auto_verify_lab(lab, default_url, body.student_id,
                             vm_subagents=vm_subagents if vm_subagents else None)

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
        # CCCNet 블록 + 자동승급
        try:
            _cccnet_add_block(body.student_id, "lab_complete", ACHIEVEMENT_POINTS.get("lab_complete", 50),
                              body.lab_id, f"Lab completed: {body.lab_id}",
                              {"earned_points": result.earned_points, "total_points": result.total_points})
            _try_auto_promote(body.student_id)
        except Exception:
            pass

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
                # CCCNet 블록 + 자동승급
                try:
                    _cccnet_add_block(body.student_id, "lab_complete", ACHIEVEMENT_POINTS.get("lab_complete", 50),
                                      body.lab_id, f"Lab completed: {body.lab_id}")
                    _try_auto_promote(body.student_id)
                except Exception:
                    pass
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
    time_limit: int | None = None        # None이면 시나리오 기본값
    battle_type: str | None = None       # 'autonomous' 면 다중 팀 자유진행 모드 강제
    max_teams: int = 4                    # autonomous 일 때만 의미 (기본 4팀)
    vuln_site_id: str = ""               # P13 — 공방전 대상 사이트
    difficulty: str = "normal"           # easy / normal / hard

@app.post("/battles/create", dependencies=[Depends(verify_api_key)])
def create_battle(body: BattleCreateBody, request: Request):
    """대전 개설 (admin/instructor 또는 학생).
    battle_type='autonomous' 시 multi-team free-for-all (역할 고정 X).
    """
    user = get_current_user(request)
    scenario = _load_scenario(body.scenario_id)
    if not scenario:
        raise HTTPException(404, "Scenario not found")
    bid = str(uuid.uuid4())[:8]
    tl = body.time_limit or scenario.get("time_limit", 1800)
    btype = body.battle_type or scenario.get("battle_type", "1v1")
    rules = {"created_by": user.get("sub", "")}
    if btype == "autonomous":
        rules["max_teams"] = max(2, min(int(body.max_teams), 16))
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO battles (id, battle_type, mode, scenario_id, status,
                   time_limit, rules, vuln_site_id, difficulty)
                   VALUES (%s, %s, %s, %s, 'waiting', %s, %s, %s, %s) RETURNING *""",
                (bid, btype, body.mode, body.scenario_id, tl, Json(rules),
                 body.vuln_site_id or "", body.difficulty or "normal"),
            )
            row = cur.fetchone()
            conn.commit()
    return {"battle": dict(row), "scenario": {"title": scenario["title"], "description": scenario.get("description", "")}}


# ── P13 VulnSite catalog API ────────────────────────────────────────────────

@app.get("/vuln-sites/list", dependencies=[Depends(verify_api_key)])
def vuln_sites_list(status: str = ""):
    """카탈로그 + 모드 통합 조회. status='available' 로 운용 가능만 필터."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            q = "SELECT * FROM vuln_sites"
            args: list = []
            if status:
                q += " WHERE status=%s"; args.append(status)
            q += " ORDER BY status DESC, name"
            cur.execute(q, args)
            sites = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT * FROM vuln_site_modes ORDER BY site_id, difficulty")
            modes = [dict(r) for r in cur.fetchall()]
    by_site: dict = {s["id"]: [] for s in sites}
    for m in modes:
        if m["site_id"] in by_site:
            by_site[m["site_id"]].append(m)
    for s in sites:
        s["modes"] = by_site.get(s["id"], [])
    return {"sites": sites}


@app.get("/vuln-sites/{site_id}", dependencies=[Depends(verify_api_key)])
def vuln_sites_get(site_id: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM vuln_sites WHERE id=%s", (site_id,))
            site = cur.fetchone()
            if not site:
                raise HTTPException(404, "site not found")
            cur.execute(
                "SELECT * FROM vuln_site_modes WHERE site_id=%s ORDER BY difficulty",
                (site_id,))
            modes = [dict(r) for r in cur.fetchall()]
    return {"site": dict(site), "modes": modes}

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

@app.post("/battles/{bid}/leave", dependencies=[Depends(verify_api_key)])
def leave_battle(bid: str, request: Request):
    """대전 참가 취소 (waiting 상태에서만)"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404, "Battle not found")
            if battle["status"] != "waiting":
                raise HTTPException(400, "진행 중인 대전은 취소할 수 없습니다")
            left = []
            if battle.get("red_id") == uid:
                cur.execute("UPDATE battles SET red_id=NULL, red_ready=false WHERE id=%s", (bid,))
                left.append("red")
            if battle.get("blue_id") == uid:
                cur.execute("UPDATE battles SET blue_id=NULL, blue_ready=false WHERE id=%s", (bid,))
                left.append("blue")
            if not left:
                raise HTTPException(400, "이 대전에 참가하지 않았습니다")
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            row = cur.fetchone()
            conn.commit()
    return {"battle": dict(row), "left": left}

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
            # 어느 팀인지 (solo: red/blue 둘 다 가진 경우 양쪽 다 ready)
            is_member = False
            if battle["red_id"] == uid:
                cur.execute("UPDATE battles SET red_ready=true WHERE id=%s", (bid,))
                is_member = True
            if battle["blue_id"] == uid:
                cur.execute("UPDATE battles SET blue_ready=true WHERE id=%s", (bid,))
                is_member = True
            if not is_member:
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
                        _v = m.get("verify", {}) or {}
                        _expect = _v.get("expect", "")
                        if isinstance(_expect, list):
                            _expect = "|".join(str(e) for e in _expect)
                        _sem = _v.get("semantic") if isinstance(_v.get("semantic"), dict) else {}
                        cur.execute(
                            "INSERT INTO battle_missions (battle_id, team, mission_order, instruction, hint, points, verify_type, verify_expect, verify_semantic) VALUES (%s,'red',%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                            (bid, m["order"], m["instruction"], m.get("hint",""), m.get("points",10), _v.get("type",""), str(_expect), _json.dumps(_sem)),
                        )
                    for m in scenario.get("blue_missions", []):
                        _v = m.get("verify", {}) or {}
                        _expect = _v.get("expect", "")
                        if isinstance(_expect, list):
                            _expect = "|".join(str(e) for e in _expect)
                        _sem = _v.get("semantic") if isinstance(_v.get("semantic"), dict) else {}
                        cur.execute(
                            "INSERT INTO battle_missions (battle_id, team, mission_order, instruction, hint, points, verify_type, verify_expect, verify_semantic) VALUES (%s,'blue',%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                            (bid, m["order"], m["instruction"], m.get("hint",""), m.get("points",10), _v.get("type",""), str(_expect), _json.dumps(_sem)),
                        )
                conn.commit()
                cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
                battle = cur.fetchone()
    started = battle["status"] == "active"
    return {"battle": dict(battle), "started": started}

@app.get("/battles/{bid}/my-missions", dependencies=[Depends(verify_api_key)])
def get_my_missions(bid: str, request: Request, team: str | None = None):
    """내 미션 목록 (진행 상태 포함). solo 모드: ?team=red|blue 로 시점 전환."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(404)
            am_red = battle["red_id"] == uid
            am_blue = battle["blue_id"] == uid
            is_solo = am_red and am_blue
            if not (am_red or am_blue):
                raise HTTPException(403, "Not in this battle")
            # team 파라미터 있으면 그 쪽 관점, 없으면 기본(red 우선 — solo 는 red 가 먼저 표시)
            if team and team.lower() in ("red", "blue"):
                requested = team.lower()
                # solo 아니면 본인 소속 팀만 허용
                if not is_solo and ((requested == "red" and not am_red) or (requested == "blue" and not am_blue)):
                    raise HTTPException(403, "You do not control that team")
                active = requested
            else:
                active = "red" if am_red else "blue"
            cur.execute("SELECT * FROM battle_missions WHERE battle_id=%s AND team=%s ORDER BY mission_order", (bid, active))
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
        "battle_id": bid, "team": active, "status": battle["status"],
        "is_solo": is_solo,
        "red_score": red_pts, "blue_score": blue_pts,
        "time_remaining": round(remaining),
        "missions": [dict(m) for m in missions],
    }

class MissionSubmitBody(BaseModel):
    mission_order: int
    answer: str
    team: str | None = None  # solo 모드: red/blue 중 어느 팀 미션인지 지정

@app.post("/battles/{bid}/submit-mission", dependencies=[Depends(verify_api_key)])
def submit_mission(bid: str, body: MissionSubmitBody, request: Request):
    """미션 답변 제출 + 검증. solo 모드: body.team 으로 대상 팀 지정."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle or battle["status"] != "active":
                raise HTTPException(400, "Battle not active")
            am_red = battle["red_id"] == uid
            am_blue = battle["blue_id"] == uid
            if not (am_red or am_blue):
                raise HTTPException(403, "Not in this battle")
            # solo 가 아니면 본인 팀 고정. solo 면 body.team 으로 지정 필수 (기본 red)
            if body.team and body.team.lower() in ("red", "blue"):
                req = body.team.lower()
                if (req == "red" and not am_red) or (req == "blue" and not am_blue):
                    raise HTTPException(403, "You do not control that team")
                team = req
            else:
                team = "red" if am_red else "blue"
            cur.execute("SELECT * FROM battle_missions WHERE battle_id=%s AND team=%s AND mission_order=%s", (bid, team, body.mission_order))
            mission = cur.fetchone()
            if not mission:
                raise HTTPException(404, "Mission not found")
            if mission["status"] == "completed":
                return {"status": "already_completed", "points": mission["points"]}
            # 검증 — semantic-first
            from packages.lab_engine.semantic_judge import semantic_first_judge, has_semantic
            _verify_dict = {
                "type": mission.get("verify_type", ""),
                "expect": mission.get("verify_expect", ""),
                "semantic": mission.get("verify_semantic") or {},
            }
            if has_semantic(_verify_dict):
                passed, _kw, _reason, _meta = semantic_first_judge(
                    mission.get("instruction", ""),
                    _verify_dict,
                    body.answer or "",
                )
                msg = _reason or ("semantic_pass" if passed else "semantic_fail")
            else:
                # semantic 없는 legacy mission — 기존 keyword 로직 (빈 expect 는 문자열 존재만 체크)
                passed = False
                msg = ""
                if mission["verify_type"] == "output_contains":
                    expect_str = mission["verify_expect"] or ""
                    if expect_str and expect_str.lower() in body.answer.lower():
                        passed = True
                        msg = f"Found '{expect_str}'"
                    elif not expect_str:
                        passed = bool(body.answer.strip())
                        msg = "Answer submitted (no expect defined)"
                    else:
                        msg = f"'{expect_str}' not found"
                elif mission["verify_type"]:
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
    # CCCNet 블록: 참가(20pt) + 승리(50pt)
    try:
        red_id = battle.get("red_id") if battle else None
        blue_id = battle.get("blue_id") if battle else None
        winner_id = result.get("winner_id", "")
        for pid in [red_id, blue_id]:
            if pid:
                _cccnet_add_block(pid, "battle_join", ACHIEVEMENT_POINTS.get("battle_join", 20),
                                  bid, f"Battle participated: {bid}")
                if pid == winner_id:
                    _cccnet_add_block(pid, "battle_win", ACHIEVEMENT_POINTS.get("battle_win", 50),
                                      bid, f"Battle won: {bid}")
                _try_auto_promote(pid)
    except Exception:
        pass
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

@app.post("/battles/{bid}/force-end", dependencies=[Depends(verify_api_key)])
def force_end_battle(bid: str, request: Request):
    """관리자: 진행 중 대전 강제 종료."""
    user = get_current_user(request)
    if user.get("role") not in ("admin", "instructor"):
        raise HTTPException(403, "Admin only")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT status FROM battles WHERE id=%s", (bid,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Battle not found")
            if row["status"] == "completed":
                return {"status": "already_completed", "battle_id": bid}
            cur.execute(
                "UPDATE battles SET status='completed', ended_at=COALESCE(ended_at, now()), result=COALESCE(result,'{}')::jsonb || %s::jsonb WHERE id=%s RETURNING *",
                (Json({"force_ended_by": user.get("sub", ""), "force_ended_at": _time.strftime('%Y-%m-%dT%H:%M:%S')}), bid),
            )
            cur.execute(
                "INSERT INTO battle_events (battle_id, event_type, actor, team, description, points) VALUES (%s,'force_ended',%s,'','관리자 강제 종료',0)",
                (bid, user.get("sub", "")),
            )
            conn.commit()
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            updated = cur.fetchone()
    return {"status": "force_ended", "battle": dict(updated)}


# ══════════════════════════════════════════════════════════════════════════
#  P12 자율 공방전 (Autonomous Multi-team Battle)
# ══════════════════════════════════════════════════════════════════════════

class AutoJoinBody(BaseModel):
    attacker_ip: str = ""
    defense_ips: list[str] = []


@app.post("/battles/{bid}/auto/join", dependencies=[Depends(verify_api_key)])
def auto_join(bid: str, body: AutoJoinBody, request: Request):
    """자율 공방전 참가 — 역할 없이 team_# 자동 할당."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            b = cur.fetchone()
            if not b:
                raise HTTPException(404, "Battle not found")
            if b["battle_type"] != "autonomous":
                raise HTTPException(400, "이 대전은 autonomous 가 아님")
            if b["status"] not in ("waiting", "active"):
                raise HTTPException(400, "대전 종료됨")
            cur.execute(
                "SELECT team_no FROM battle_participants WHERE battle_id=%s AND user_id=%s",
                (bid, uid))
            existing = cur.fetchone()
            if existing:
                return {"battle_id": bid, "team_no": existing["team_no"], "rejoined": True}
            max_teams = (b.get("rules") or {}).get("max_teams", 16)
            cur.execute(
                "SELECT COUNT(*) AS n FROM battle_participants WHERE battle_id=%s",
                (bid,))
            n = cur.fetchone()["n"]
            if n >= max_teams:
                raise HTTPException(400, f"팀 정원({max_teams}) 초과")
            team_no = n + 1
            cur.execute(
                """INSERT INTO battle_participants
                   (battle_id, user_id, team_no, attacker_ip, defense_ips)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                (bid, uid, team_no, body.attacker_ip,
                 Json(body.defense_ips)))
            row = cur.fetchone()
            # 자율모드도 시나리오의 RED + BLUE 미션을 *팀별 사본*으로 등록.
            # battle_missions 의 team 컬럼에 'auto-team-N-red' / 'auto-team-N-blue' 로
            # 네임스페이스 분리. 모든 팀이 동일한 미션 풀이 + 추가로 free 공방 claim.
            scenario = _load_scenario(b["scenario_id"])
            if scenario:
                for role in ("red", "blue"):
                    miss = scenario.get(f"{role}_missions", []) or []
                    for m in miss:
                        _v = m.get("verify", {}) or {}
                        _expect = _v.get("expect", "")
                        if isinstance(_expect, list):
                            _expect = "|".join(str(e) for e in _expect)
                        _sem = _v.get("semantic") if isinstance(_v.get("semantic"), dict) else {}
                        team_label = f"auto-team-{team_no}-{role}"
                        cur.execute(
                            "INSERT INTO battle_missions (battle_id, team, mission_order, "
                            "instruction, hint, points, verify_type, verify_expect, "
                            "verify_semantic) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT DO NOTHING",
                            (bid, team_label, m["order"], m["instruction"],
                             m.get("hint", ""), m.get("points", 10),
                             _v.get("type", ""), str(_expect), Json(_sem)),
                        )
            conn.commit()
    return {"battle_id": bid, "team_no": team_no, "participant": dict(row),
            "missions_enrolled": True}


@app.get("/battles/{bid}/auto/my-missions",
         dependencies=[Depends(verify_api_key)])
def auto_my_missions(bid: str, request: Request, role: str = ""):
    """자율모드 참가자의 RED+BLUE 미션 (자기 팀 namespace).
    role='red' 또는 'blue' 로 필터, 미지정 시 둘 다.
    """
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT team_no FROM battle_participants WHERE battle_id=%s AND user_id=%s",
                (bid, uid))
            me = cur.fetchone()
            if not me:
                raise HTTPException(403, "참가자 아님")
            tno = me["team_no"]
            if role in ("red", "blue"):
                team_labels = [f"auto-team-{tno}-{role}"]
            else:
                team_labels = [f"auto-team-{tno}-red", f"auto-team-{tno}-blue"]
            cur.execute(
                "SELECT * FROM battle_missions WHERE battle_id=%s "
                "AND team = ANY(%s) ORDER BY team, mission_order",
                (bid, team_labels))
            missions = [dict(r) for r in cur.fetchall()]
    out = {"red": [], "blue": []}
    for m in missions:
        r = "red" if m["team"].endswith("-red") else "blue"
        out[r].append(m)
    return {"team_no": tno, "missions": out,
            "summary": {"red_total": len(out["red"]),
                        "red_done": sum(1 for m in out["red"] if m.get("status") == "completed"),
                        "blue_total": len(out["blue"]),
                        "blue_done": sum(1 for m in out["blue"] if m.get("status") == "completed")}}


class AutoMissionSubmitBody(BaseModel):
    role: str           # red | blue
    mission_order: int
    answer: str


@app.post("/battles/{bid}/auto/submit-mission",
          dependencies=[Depends(verify_api_key)])
def auto_submit_mission(bid: str, body: AutoMissionSubmitBody, request: Request):
    """자율모드 시나리오 미션 제출 — 팀 namespace 안에서만 평가."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    if body.role not in ("red", "blue"):
        raise HTTPException(400, "role ∈ red|blue")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT team_no FROM battle_participants WHERE battle_id=%s AND user_id=%s",
                (bid, uid))
            me = cur.fetchone()
            if not me:
                raise HTTPException(403, "참가자 아님")
            tno = me["team_no"]
            label = f"auto-team-{tno}-{body.role}"
            cur.execute(
                "SELECT * FROM battle_missions WHERE battle_id=%s AND team=%s "
                "AND mission_order=%s", (bid, label, body.mission_order))
            mission = cur.fetchone()
            if not mission:
                raise HTTPException(404, "미션 없음")
            if mission["status"] == "completed":
                return {"status": "already_completed", "points": mission["points"]}
            # semantic-first 채점 (기존 submit_mission 로직 재사용)
            from packages.lab_engine.semantic_judge import semantic_first_judge, has_semantic
            _verify_dict = {
                "type": mission.get("verify_type", ""),
                "expect": mission.get("verify_expect", ""),
                "semantic": mission.get("verify_semantic") or {},
            }
            if has_semantic(_verify_dict):
                passed, _kw, _reason, _ = semantic_first_judge(
                    mission.get("instruction", ""), _verify_dict, body.answer or "")
                msg = _reason or ("semantic_pass" if passed else "semantic_fail")
            else:
                passed = bool(body.answer.strip())
                msg = "Answer submitted"
            if passed:
                cur.execute("UPDATE battle_missions SET status='completed', "
                            "answer=%s, submitted_at=now() WHERE id=%s",
                            (body.answer, mission["id"]))
                cur.execute("UPDATE battle_participants SET score=score+%s "
                            "WHERE battle_id=%s AND user_id=%s",
                            (mission["points"], bid, uid))
                cur.execute("INSERT INTO battle_events (battle_id, event_type, "
                            "actor, team, description, points) "
                            "VALUES (%s, 'auto_mission', %s, %s, %s, %s)",
                            (bid, uid, label, mission["instruction"][:80],
                             mission["points"]))
                conn.commit()
                return {"passed": True, "points": mission["points"], "message": msg}
            return {"passed": False, "points": 0, "message": msg}


@app.get("/battles/{bid}/auto/participants",
         dependencies=[Depends(verify_api_key)])
def auto_participants(bid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM battle_participants WHERE battle_id=%s "
                "ORDER BY team_no", (bid,))
            return {"participants": [dict(r) for r in cur.fetchall()]}


@app.get("/battles/{bid}/auto/my-targets",
         dependencies=[Depends(verify_api_key)])
def auto_my_targets(bid: str, request: Request):
    """내 팀 외 모든 팀의 자산 = 공격 대상."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM battle_participants WHERE battle_id=%s",
                (bid,))
            ps = [dict(r) for r in cur.fetchall()]
    me = next((p for p in ps if p["user_id"] == uid), None)
    if not me:
        raise HTTPException(403, "참가자 아님")
    targets = []
    for p in ps:
        if p["team_no"] == me["team_no"]:
            continue
        targets.append({
            "team_no": p["team_no"],
            "user_id": p["user_id"],
            "defense_ips": p["defense_ips"],
            "current_score": p["score"],
        })
    return {"my_team_no": me["team_no"], "targets": targets}


@app.get("/battles/{bid}/auto/my-defense",
         dependencies=[Depends(verify_api_key)])
def auto_my_defense(bid: str, request: Request):
    """내 자산 (방어 대상) + 들어온 공격 claim 들."""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM battle_participants WHERE battle_id=%s AND user_id=%s",
                (bid, uid))
            me = cur.fetchone()
            if not me:
                raise HTTPException(403, "참가자 아님")
            cur.execute(
                "SELECT * FROM battle_attack_claims WHERE battle_id=%s "
                "AND target_team_no=%s ORDER BY submitted_at DESC LIMIT 100",
                (bid, me["team_no"]))
            incoming = [dict(r) for r in cur.fetchall()]
    return {
        "team_no": me["team_no"],
        "defense_ips": me["defense_ips"],
        "incoming_claims": incoming,
        "score_breakdown": {
            "attacks_landed": me["attacks_landed"],
            "defenses_blocked": me["defenses_blocked"],
            "own_breaches": me["own_breaches"],
            "total": me["score"],
        },
    }


class ClaimBody(BaseModel):
    claim_type: str           # attack | defense | recovery
    target_team_no: int | None = None
    source_team_no: int | None = None
    title: str = ""
    evidence: str             # 명령 + stdout + 캡처 (semantic judge 입력)


@app.post("/battles/{bid}/auto/claim",
          dependencies=[Depends(verify_api_key)])
def auto_claim(bid: str, body: ClaimBody, request: Request):
    """공격/방어/복구 claim 제출 → semantic judge 자동 채점.
    accepted=True 면 점수 가산 (attack +10 / defense +5 / recovery +3).
    attack 일 경우 target 의 own_breach +1 도 같이 갱신.
    """
    user = get_current_user(request)
    uid = user.get("sub", "")
    if body.claim_type not in ("attack", "defense", "recovery"):
        raise HTTPException(400, "claim_type ∈ attack|defense|recovery")
    if body.claim_type == "attack" and body.target_team_no is None:
        raise HTTPException(400, "attack 은 target_team_no 필수")
    if body.claim_type == "defense" and body.source_team_no is None:
        raise HTTPException(400, "defense 는 source_team_no 필수")

    # semantic judge — Bastion /chat 활용 또는 lab_engine.semantic_judge 직접
    judged, accepted, reason, points = _judge_battle_claim(
        body.claim_type, body.title, body.evidence)

    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO battle_attack_claims
                   (battle_id, claimant_user_id, claim_type, target_team_no,
                    source_team_no, title, evidence, judged, accepted,
                    points_awarded, judge_reason, judged_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                   RETURNING *""",
                (bid, uid, body.claim_type, body.target_team_no,
                 body.source_team_no, body.title, body.evidence,
                 judged, accepted, points, reason))
            claim = cur.fetchone()
            if accepted and points > 0:
                # 본인 점수 가산
                col_map = {"attack": "attacks_landed",
                           "defense": "defenses_blocked",
                           "recovery": "attacks_landed"}  # recovery = own credit
                col = col_map[body.claim_type]
                cur.execute(
                    f"UPDATE battle_participants SET score=score+%s, {col}={col}+1 "
                    f"WHERE battle_id=%s AND user_id=%s",
                    (points, bid, uid))
                # attack 시 target 의 own_breaches +1 + 점수 -10
                if body.claim_type == "attack" and body.target_team_no:
                    cur.execute(
                        "UPDATE battle_participants SET score=score-10, "
                        "own_breaches=own_breaches+1 "
                        "WHERE battle_id=%s AND team_no=%s",
                        (bid, body.target_team_no))
                # battle_events 에 기록
                cur.execute(
                    "INSERT INTO battle_events (battle_id, event_type, actor, "
                    "team, description, points) VALUES (%s, %s, %s, %s, %s, %s)",
                    (bid, f"auto_{body.claim_type}", uid,
                     f"team-{body.target_team_no or body.source_team_no or '-'}",
                     f"{body.title or body.claim_type}: {reason[:80]}",
                     points))
            conn.commit()
    return {
        "claim_id": claim["id"],
        "judged": judged, "accepted": accepted,
        "points_awarded": points, "reason": reason,
    }


@app.get("/battles/{bid}/auto/scoreboard",
         dependencies=[Depends(verify_api_key)])
def auto_scoreboard(bid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT bp.*,
                          COALESCE(s.name, '') as user_name
                   FROM battle_participants bp
                   LEFT JOIN students s ON bp.user_id = s.id
                   WHERE bp.battle_id=%s
                   ORDER BY bp.score DESC""",
                (bid,))
            rows = [dict(r) for r in cur.fetchall()]
            cur.execute(
                "SELECT COUNT(*) AS n FROM battle_attack_claims "
                "WHERE battle_id=%s", (bid,))
            total_claims = cur.fetchone()["n"]
    return {"battle_id": bid, "scoreboard": rows, "total_claims": total_claims}


@app.get("/battles/{bid}/auto/finalize",
         dependencies=[Depends(verify_api_key)])
def auto_finalize(bid: str):
    """자율 공방전 최종 결과 — 우승자/통계/MVP/timeline summary.

    P12 end-game 페이지용. battle 종료 시 호출.
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM battles WHERE id=%s", (bid,))
            battle = cur.fetchone()
            if not battle:
                raise HTTPException(status_code=404, detail="battle not found")

            # 최종 scoreboard
            cur.execute(
                """SELECT bp.*, COALESCE(s.name, '') as user_name
                   FROM battle_participants bp
                   LEFT JOIN students s ON bp.user_id = s.id
                   WHERE bp.battle_id=%s
                   ORDER BY bp.score DESC""", (bid,))
            board = [dict(r) for r in cur.fetchall()]

            # 모든 claim
            cur.execute(
                """SELECT bac.*, COALESCE(s.name, '') as claimant_name
                   FROM battle_attack_claims bac
                   LEFT JOIN students s ON bac.claimant_user_id = s.id
                   WHERE battle_id=%s ORDER BY submitted_at""", (bid,))
            all_claims = [dict(r) for r in cur.fetchall()]

            # 통계
            n_attack = sum(1 for c in all_claims if c.get("claim_type") == "attack")
            n_defense = sum(1 for c in all_claims if c.get("claim_type") == "defense")
            n_accepted = sum(1 for c in all_claims if c.get("accepted"))
            avg_pts = sum(c.get("points_awarded") or 0 for c in all_claims) / max(len(all_claims), 1)

            # MVP — 가장 많은 accepted attack
            from collections import Counter
            attacker_score = Counter()
            defender_score = Counter()
            for c in all_claims:
                if not c.get("accepted"): continue
                if c.get("claim_type") == "attack":
                    attacker_score[c.get("claimant_user_id")] += c.get("points_awarded") or 0
                else:
                    defender_score[c.get("claimant_user_id")] += c.get("points_awarded") or 0

            mvp_attack = attacker_score.most_common(1)
            mvp_defense = defender_score.most_common(1)

            # 우승자 (top score)
            winner = board[0] if board else None
            runner_up = board[1] if len(board) > 1 else None

            # claim timeline (시간순 요약)
            timeline = [
                {
                    "ts": c.get("submitted_at").isoformat() if c.get("submitted_at") else "",
                    "claimant": c.get("claimant_name") or c.get("claimant_user_id", "")[:8],
                    "type": c.get("claim_type"),
                    "title": (c.get("title") or "")[:60],
                    "accepted": c.get("accepted"),
                    "points": c.get("points_awarded") or 0,
                } for c in all_claims[-30:]  # 최근 30 만
            ]

    return {
        "battle_id": bid,
        "battle_type": battle.get("battle_type"),
        "status": battle.get("status"),
        "winner": {"team_no": winner.get("team_no"), "name": winner.get("user_name"),
                   "score": winner.get("score")} if winner else None,
        "runner_up": {"team_no": runner_up.get("team_no"), "name": runner_up.get("user_name"),
                      "score": runner_up.get("score")} if runner_up else None,
        "scoreboard": board,
        "stats": {
            "total_teams": len(board),
            "total_claims": len(all_claims),
            "attack_claims": n_attack,
            "defense_claims": n_defense,
            "accepted_claims": n_accepted,
            "acceptance_rate": round(n_accepted / max(len(all_claims), 1), 3),
            "avg_points_per_claim": round(avg_pts, 1),
        },
        "mvp_attack": {"user_id": mvp_attack[0][0], "score": mvp_attack[0][1]} if mvp_attack else None,
        "mvp_defense": {"user_id": mvp_defense[0][0], "score": mvp_defense[0][1]} if mvp_defense else None,
        "timeline": timeline,
    }


def _judge_battle_claim(claim_type: str, title: str,
                        evidence: str) -> tuple[bool, bool, str, int]:
    """semantic-first 채점. lab_engine.semantic_judge 재활용."""
    try:
        from packages.lab_engine.semantic_judge import semantic_first_judge
    except Exception:
        # 폴백: 빈 evidence 만 거절
        ok = bool((evidence or "").strip()) and len(evidence) > 50
        pts = {"attack": 10, "defense": 5, "recovery": 3}.get(claim_type, 0) if ok else 0
        return True, ok, ("OK (no judge)" if ok else "evidence 부족"), pts

    intent_map = {
        "attack": f"공격 성공 증명 — '{title}'. evidence 에 실제 침해 명령 + 결과 stdout/HTTP code/캡처 포함되어야 인정",
        "defense": f"방어 성공 증명 — '{title}'. evidence 에 실제 차단 룰 적용 + 차단 로그/응답 코드 포함되어야 인정",
        "recovery": f"복구 증명 — '{title}'. evidence 에 침해 흔적 정리 + 재발 차단 룰 + 검증 명령 포함되어야 인정",
    }
    succ_map = {
        "attack": ["실행된 공격 명령 인용", "결과 stdout/HTTP code/응답 데이터 인용",
                   "공격 대상이 명시 (IP/URL/계정)"],
        "defense": ["적용한 차단 룰/명령 인용", "차단 로그 또는 거절 응답 인용",
                    "공격 출처 식별"],
        "recovery": ["격리·삭제 명령 인용", "재발 방지 룰 인용", "검증 결과 인용"],
    }
    neg_map = {
        "attack": ["명령 없이 설명만", "응답 코드/stdout 누락", "대상 미명시"],
        "defense": ["룰 변경 흔적 없음", "차단 로그 부재", "출처 불명"],
        "recovery": ["근본 원인 미해결", "재발 방지 누락", "검증 없음"],
    }
    verify = {
        "type": "output_contains",
        "expect": "",
        "semantic": {
            "intent": intent_map[claim_type],
            "success_criteria": succ_map[claim_type],
            "acceptable_methods": ["실제 명령 + stdout 인용", "스크린샷 base64",
                                    "JSON 형식 evidence"],
            "negative_signs": neg_map[claim_type],
        },
    }
    try:
        passed, kw, reason, _ = semantic_first_judge(
            intent_map[claim_type], verify, evidence)
    except Exception as e:
        return True, False, f"judge_error: {e}", 0
    pts = {"attack": 10, "defense": 5, "recovery": 3}.get(claim_type, 0) if passed else 0
    return True, bool(passed), reason or "", pts


def _bastion_get(path: str, params: dict | None = None) -> dict:
    """Bastion API GET 프록시 헬퍼 — 실패해도 app 죽지 않게."""
    import httpx
    bastion_url = os.getenv("BASTION_URL", "http://192.168.0.115:8003").rstrip("/")
    try:
        r = httpx.get(f"{bastion_url}{path}", params=params or {}, timeout=15.0)
        return r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
    except Exception as e:
        return {"error": f"bastion unavailable: {e}", "bastion_url": bastion_url}


def _bastion_method(method: str, path: str, json_body: dict | None = None) -> dict:
    import httpx
    bastion_url = os.getenv("BASTION_URL", "http://192.168.0.115:8003").rstrip("/")
    try:
        r = httpx.request(method, f"{bastion_url}{path}", json=json_body, timeout=30.0)
        return r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}
    except Exception as e:
        return {"error": f"bastion unavailable: {e}", "bastion_url": bastion_url}


# ── Knowledge Graph 프록시 (admin only) ─────────────────────────────────────

def _require_admin(request: Request):
    user = get_current_user(request)
    if user.get("role") not in ("admin", "instructor"):
        raise HTTPException(403, "Admin only")


@app.get("/graph/stats", dependencies=[Depends(verify_api_key)])
def kg_stats(request: Request):
    _require_admin(request)
    return _bastion_get("/graph/stats")


@app.get("/graph/nodes", dependencies=[Depends(verify_api_key)])
def kg_nodes(request: Request, types: str = "", limit: int = 500):
    _require_admin(request)
    return _bastion_get("/graph/nodes", {"types": types, "limit": limit})


@app.get("/graph/edges", dependencies=[Depends(verify_api_key)])
def kg_edges(request: Request, types: str = ""):
    _require_admin(request)
    return _bastion_get("/graph/edges", {"types": types})


@app.get("/graph/node/{node_id}", dependencies=[Depends(verify_api_key)])
def kg_node(node_id: str, request: Request):
    _require_admin(request)
    return _bastion_get(f"/graph/node/{node_id}")


@app.get("/graph/search", dependencies=[Depends(verify_api_key)])
def kg_search(request: Request, q: str = "", type: str = "", limit: int = 30):
    _require_admin(request)
    return _bastion_get("/graph/search", {"q": q, "type": type, "limit": limit})


@app.get("/graph/lineage/{node_id}", dependencies=[Depends(verify_api_key)])
def kg_lineage(node_id: str, request: Request, max_depth: int = 3):
    _require_admin(request)
    return _bastion_get(f"/graph/lineage/{node_id}", {"max_depth": max_depth})


@app.delete("/graph/node/{node_id}", dependencies=[Depends(verify_api_key)])
def kg_delete(node_id: str, request: Request):
    _require_admin(request)
    return _bastion_method("DELETE", f"/graph/node/{node_id}")


@app.post("/graph/compact/{playbook_id}", dependencies=[Depends(verify_api_key)])
def kg_compact_one(playbook_id: str, request: Request):
    _require_admin(request)
    return _bastion_method("POST", f"/graph/compact/{playbook_id}")


@app.post("/graph/compact", dependencies=[Depends(verify_api_key)])
def kg_compact_all(request: Request):
    _require_admin(request)
    return _bastion_method("POST", "/graph/compact")


# ── Audit log 프록시 ───────────────────────────────────────────────────────

@app.get("/audit", dependencies=[Depends(verify_api_key)])
def audit_recent(request: Request, limit: int = 50, session_id: str = "",
                 user_id: str = "", course: str = "", outcome: str = "", since: str = ""):
    _require_admin(request)
    return _bastion_get("/audit", {"limit": limit, "session_id": session_id,
                                    "user_id": user_id, "course": course,
                                    "outcome": outcome, "since": since})


@app.get("/audit/{request_id}", dependencies=[Depends(verify_api_key)])
def audit_get(request_id: str, request: Request):
    _require_admin(request)
    return _bastion_get(f"/audit/{request_id}")


@app.get("/audit-stats", dependencies=[Depends(verify_api_key)])
def audit_stats_proxy(request: Request):
    _require_admin(request)
    return _bastion_get("/audit/_stats")


@app.get("/audit-verify-chain", dependencies=[Depends(verify_api_key)])
def audit_verify(request: Request, start_id: int = 1):
    _require_admin(request)
    return _bastion_get("/audit/_verify-chain", {"start_id": start_id})


@app.delete("/battles/{bid}", dependencies=[Depends(verify_api_key)])
def delete_battle(bid: str, request: Request):
    """관리자: 대전 레코드 + 미션 + 이벤트 삭제."""
    user = get_current_user(request)
    if user.get("role") not in ("admin", "instructor"):
        raise HTTPException(403, "Admin only")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM battles WHERE id=%s", (bid,))
            if not cur.fetchone():
                raise HTTPException(404, "Battle not found")
            cur.execute("DELETE FROM battle_missions WHERE battle_id=%s", (bid,))
            missions = cur.rowcount
            cur.execute("DELETE FROM battle_events WHERE battle_id=%s", (bid,))
            events = cur.rowcount
            cur.execute("DELETE FROM battles WHERE id=%s", (bid,))
            conn.commit()
    return {"status": "deleted", "battle_id": bid, "deleted_missions": missions, "deleted_events": events}

# ══════════════════════════════════════════════════
#  AI Tasks (Bastion 에이전트)
# ══════════════════════════════════════════════════
@app.post("/ai/task", dependencies=[Depends(verify_api_key)])
def ai_task(body: AITaskRequest, request: Request):
    """AI 작업 요청 → Bastion 에이전트가 스킬 디스패치"""
    from packages.bastion import execute_task
    user = get_current_user(request)
    uid = user.get("sub", "")

    # 사용자 인프라 정보를 컨텍스트로 전달
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT ip, vm_config FROM student_infras WHERE student_id=%s", (uid,))
            infras = [dict(r) for r in cur.fetchall()]

    context = {"student_id": uid, "infras": infras}
    result = execute_task(instruction=body.instruction, context=context)
    return {"status": "ok", **result}

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
#  Manager AI (V5)
# ══════════════════════════════════════════════════
class ManagerTaskBody(BaseModel):
    instruction: str
    target_role: str = ""  # secu, web, siem, etc.

@app.post("/manager/execute", dependencies=[Depends(verify_api_key)])
def manager_execute(body: ManagerTaskBody, request: Request):
    """Manager AI에 작업 지시 → 실행 계획 생성"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    from packages.manager_ai import execute, compose_prompt

    # 학생 인프라 정보 로드
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (uid,))
            student = cur.fetchone()
            cur.execute("SELECT * FROM student_infras WHERE student_id=%s", (uid,))
            infras = [dict(r) for r in cur.fetchall()]

    student_info = {
        "name": student["name"] if student else "?",
        "student_id": student.get("student_id", ""),
        "rank": student.get("rank", "rookie"),
        "total_blocks": student.get("total_blocks", 0),
        "infras": [{"role": i.get("vm_config", {}).get("role", ""), "ip": i["ip"], "subagent": i.get("subagent_url", "")} for i in infras],
    }

    result = execute(body.instruction, student_info)
    return {"instruction": body.instruction, "plan": result.get("plan", []), "error": result.get("error", "")}

@app.get("/manager/vm-setup/{role}", dependencies=[Depends(verify_api_key)])
def get_vm_setup_commands(role: str):
    """VM별 설치 명령어 목록"""
    from packages.manager_ai import setup_vm
    commands = setup_vm(role, "0.0.0.0")
    return {"role": role, "commands": commands, "count": len(commands)}

@app.get("/manager/prompt", dependencies=[Depends(verify_api_key)])
def get_manager_prompt(request: Request):
    """현재 Manager AI 시스템 프롬프트 확인 (디버그용)"""
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander"):
        raise HTTPException(403)
    from packages.manager_ai import compose_prompt
    return {"prompt": compose_prompt()}

# ══════════════════════════════════════════════════
#  User Analytics + AI Feedback (V2)
# ══════════════════════════════════════════════════
@app.get("/user/stats", dependencies=[Depends(verify_api_key)])
def user_stats(request: Request):
    """내 학습 통계 종합"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM students WHERE id=%s", (uid,))
            student = cur.fetchone()
            if not student:
                raise HTTPException(404)
            # Labs
            cur.execute("SELECT count(*) as total, count(*) FILTER (WHERE status='completed') as done FROM lab_completions WHERE student_id=%s", (uid,))
            labs = cur.fetchone()
            cur.execute("SELECT lab_id, status, completed_at FROM lab_completions WHERE student_id=%s ORDER BY completed_at DESC LIMIT 10", (uid,))
            recent_labs = cur.fetchall()
            # CTF
            cur.execute("SELECT count(*) FILTER (WHERE correct) as solved, count(*) as attempted, COALESCE(sum(points) FILTER (WHERE correct),0) as pts FROM ctf_submissions WHERE student_id=%s", (uid,))
            ctf = cur.fetchone()
            # Battles
            cur.execute("SELECT count(*) as total FROM battles WHERE (red_id=%s OR blue_id=%s) AND status='completed'", (uid, uid))
            battles = cur.fetchone()["total"]
            cur.execute("SELECT count(*) as wins FROM battles WHERE status='completed' AND ((red_id=%s AND red_score>blue_score) OR (blue_id=%s AND blue_score>red_score))", (uid, uid))
            wins = cur.fetchone()["wins"]
            # CCCNet
            cur.execute("SELECT block_type, count(*) as cnt, sum(points) as pts FROM cccnet_blocks WHERE student_id=%s GROUP BY block_type", (uid,))
            blocks_by_type = {r["block_type"]: {"count": r["cnt"], "points": int(r["pts"])} for r in cur.fetchall()}
            # 과목별 진도
            cur.execute("""
                SELECT split_part(lab_id, '-week', 1) as course, count(*) as done
                FROM lab_completions WHERE student_id=%s AND status='completed'
                GROUP BY course ORDER BY done DESC
            """, (uid,))
            course_progress = [dict(r) for r in cur.fetchall()]
    return {
        "student": {"name": student["name"], "student_id": student["student_id"], "rank": student.get("rank","rookie"), "total_blocks": student.get("total_blocks",0)},
        "labs": {"total": labs["total"], "completed": labs["done"], "recent": [dict(r) for r in recent_labs]},
        "ctf": {"solved": ctf["solved"], "attempted": ctf["attempted"], "points": int(ctf["pts"])},
        "battles": {"total": battles, "wins": wins, "win_rate": round(wins/max(battles,1)*100)},
        "blocks": blocks_by_type,
        "course_progress": course_progress,
    }

@app.get("/user/ai-feedback", dependencies=[Depends(verify_api_key)])
def ai_feedback(request: Request):
    """AI 기반 학습 피드백"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    # 통계 수집
    stats = user_stats(request)
    import httpx as _hxf
    ollama_url = LLM_BASE_URL
    model = LLM_MANAGER_MODEL
    prompt = f"""다음 학생의 학습 데이터를 분석하고, 개인화된 피드백과 추천을 제공하세요.

학생: {stats['student']['name']} (rank: {stats['student']['rank']})
블록: {stats['student']['total_blocks']}

Labs: {stats['labs']['completed']}/{stats['labs']['total']} 완료
CTF: {stats['ctf']['solved']}/{stats['ctf']['attempted']} 해결 ({stats['ctf']['points']}pts)
대전: {stats['battles']['total']}회 ({stats['battles']['wins']}승, 승률 {stats['battles']['win_rate']}%)

과목별 진도: {stats['course_progress'][:10]}

다음 항목으로 피드백 작성 (한국어, 간결하게):
1. 강점 (잘하고 있는 부분)
2. 약점 (보강 필요한 부분)
3. 다음 추천 학습 (구체적 과목/주차)
4. 승급 진행도 (현재 rank에서 다음 rank까지)
5. 동기부여 한 마디"""

    try:
        r = _hxf.post(f"{ollama_url}/api/chat", json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False, "options": {"temperature": 0.5, "num_predict": 800},
        }, timeout=90.0)
        feedback = r.json().get("message", {}).get("content", "피드백 생성 실패")
    except Exception as e:
        feedback = f"AI 서버 연결 실패: {str(e)[:100]}"
    return {"feedback": feedback, "stats": stats}

# ══════════════════════════════════════════════════
#  ChatBot (AI 튜터)
# ══════════════════════════════════════════════════
class ChatBody(BaseModel):
    message: str
    context: dict[str, Any] = {}
    history: list[dict[str, str]] = []  # [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]

@app.post("/chat", dependencies=[Depends(verify_api_key)])
def chat(body: ChatBody, request: Request):
    """AI 튜터 챗봇 — 사용법, 학습 내용 질의응답"""
    user = get_current_user(request)
    import httpx as _hxc
    ollama_url = LLM_BASE_URL
    model = LLM_SUBAGENT_MODEL

    # 현재 페이지의 교안 내용을 컨텍스트로 주입
    page_content = body.context.get("page_content", "")
    page_info = body.context.get("page", "")
    course_id = body.context.get("course_id", "")
    week = body.context.get("week", "")

    # 페이지 컨텍스트가 없으면 course_id/week으로 교안 로드
    if not page_content and course_id and week:
        for k, v in _COURSE_MAP.items():
            if v["name"] == course_id:
                lecture_path = os.path.join(_EDUCATION_DIR, k, f"week{int(week):02d}", "lecture.md")
                if os.path.isfile(lecture_path):
                    with open(lecture_path, encoding="utf-8") as f:
                        page_content = f.read()[:4000]
                break

    context_section = ""
    if page_content:
        context_section = f"\n\n[현재 학생이 보고 있는 교안 내용]\n{page_content[:4000]}\n\n위 교안 내용을 기반으로 학생의 질문에 답변하세요. 교안에 나온 구체적인 코드, SQL 구문, 명령어의 맥락을 설명하세요."

    system_prompt = f"""너는 CCC(Cyber Combat Commander) 사이버보안 교육 플랫폼의 AI 튜터다.
학생의 질문에 친절하고 정확하게 답변한다.
이전 대화 맥락을 기억하고 이어서 답변한다.

현재 사용자: {user.get('name', '학생')} (rank: {user.get('rank', 'rookie')})
현재 페이지: {page_info}
{context_section}

한국어로 답변. 간결하고 실용적으로."""

    # 대화 히스토리 구성
    messages = [{"role": "system", "content": system_prompt}]
    for h in body.history[-10:]:  # 최근 10턴
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"][:500]})
    messages.append({"role": "user", "content": body.message})

    try:
        r = _hxc.post(f"{ollama_url}/api/chat", json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.5, "num_predict": 800},
        }, timeout=90.0)
        reply = r.json().get("message", {}).get("content", "응답 생성 실패")
    except Exception as e:
        reply = f"AI 서버 연결 실패: {str(e)[:100]}"

    return {"reply": reply}

# ══════════════════════════════════════════════════
#  CTF (문제 관리 + 자동 출제 + 제출)
# ══════════════════════════════════════════════════

class CTFGenerateBody(BaseModel):
    courses: list[str]        # ["attack", "soc-adv"]
    weeks: list[int] = []     # [1,2,3] or [] for all
    count: int = 10           # 생성할 문제 수
    difficulty: str = "medium"
    min_blocks: int = 0       # 참가 자격 (최소 블록 수)

@app.post("/ctf/generate", dependencies=[Depends(verify_api_key)])
def generate_ctf(body: CTFGenerateBody, request: Request):
    """AI 기반 CTF 문제 자동 생성"""
    user = get_current_user(request)
    if user.get("role") not in ("admin", "commander", "trainer"):
        raise HTTPException(403, "Trainer+ only")

    # 해당 과목 교안에서 키워드 추출
    import glob as _g
    keywords = []
    for course in body.courses:
        for k, v in _COURSE_MAP.items():
            if v["name"] == course or v["name"] == course.replace("-adv", "-advanced"):
                edu_dir = os.path.join(_EDUCATION_DIR, k)
                if os.path.isdir(edu_dir):
                    for wd in sorted(_g.glob(os.path.join(edu_dir, "week*/lecture.md"))):
                        wnum = int(os.path.basename(os.path.dirname(wd)).replace("week", ""))
                        if not body.weeks or wnum in body.weeks:
                            with open(wd, encoding="utf-8") as f:
                                content = f.read()[:2000]
                            keywords.append(f"{course} week{wnum}: {content[:300]}")

    # LLM으로 문제 생성
    import httpx as _hx2
    ollama_url = LLM_BASE_URL
    model = LLM_MANAGER_MODEL

    prompt = f"""다음 교육 과정 내용을 바탕으로 CTF 문제 {body.count}개를 생성하세요.
난이도: {body.difficulty}

교육 내용 키워드:
{chr(10).join(keywords[:10])}

반드시 아래 JSON 형식으로만 응답:
{{"challenges":[{{"title":"문제 제목","description":"문제 설명","flag":"flag{{정답}}","points":100,"category":"web|forensic|crypto|misc|network","hint":"힌트"}}]}}"""

    challenges = []
    try:
        r = _hx2.post(f"{ollama_url}/api/chat", json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False, "options": {"temperature": 0.7},
        }, timeout=120.0)
        content = r.json().get("message", {}).get("content", "")
        start = content.find("{"); end = content.rfind("}") + 1
        if start >= 0 and end > start:
            import json as _j
            data = _j.loads(content[start:end])
            challenges = data.get("challenges", [])
    except Exception as e:
        return {"error": f"LLM 생성 실패: {e}", "challenges": []}

    # DB에 저장
    saved = []
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for ch in challenges[:body.count]:
                cid = str(uuid.uuid4())[:8]
                cur.execute(
                    """INSERT INTO ctf_challenges (id, title, category, description, flag, points, difficulty, min_blocks, courses)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id, title, category, points, difficulty""",
                    (cid, ch.get("title",""), ch.get("category","misc"), ch.get("description",""),
                     ch.get("flag","flag{unknown}"), ch.get("points",100), body.difficulty,
                     body.min_blocks, Json(body.courses)),
                )
                row = cur.fetchone()
                saved.append(dict(row))
            conn.commit()
    return {"generated": len(saved), "challenges": saved}

@app.get("/ctf/challenges", dependencies=[Depends(verify_api_key)])
def list_ctf_challenges(category: str | None = None):
    q = "SELECT id, title, category, description, points, difficulty, min_blocks, created_at FROM ctf_challenges"
    params: list = []
    if category:
        q += " WHERE category=%s"; params.append(category)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"challenges": [dict(r) for r in rows]}

class CTFSubmitBody(BaseModel):
    challenge_id: str
    flag: str

@app.post("/ctf/submit", dependencies=[Depends(verify_api_key)])
def submit_ctf(body: CTFSubmitBody, request: Request):
    user = get_current_user(request)
    uid = user.get("sub", "")
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ctf_challenges WHERE id=%s", (body.challenge_id,))
            ch = cur.fetchone()
            if not ch:
                raise HTTPException(404, "Challenge not found")
            # 참가 자격 확인
            min_b = ch.get("min_blocks", 0)
            if min_b > 0:
                cur.execute("SELECT total_blocks FROM students WHERE id=%s", (uid,))
                st = cur.fetchone()
                if not st or (st.get("total_blocks", 0) or 0) < min_b:
                    raise HTTPException(403, f"참가 자격 미달: {min_b} 블록 이상 필요")
            correct = body.flag.strip() == ch["flag"].strip()
            points = ch["points"] if correct else 0
            sid = str(uuid.uuid4())[:8]
            cur.execute(
                "INSERT INTO ctf_submissions (id, student_id, challenge_id, flag, correct, points) VALUES (%s,%s,%s,%s,%s,%s)",
                (sid, uid, body.challenge_id, body.flag, correct, points),
            )
            if correct:
                _cccnet_add_block(uid, "ctf_solve", points, body.challenge_id, f"CTF solved: {ch['title']}")
            conn.commit()
    return {"correct": correct, "points": points, "challenge": ch["title"]}

@app.get("/ctf/scoreboard", dependencies=[Depends(verify_api_key)])
def ctf_scoreboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.name, s.student_id, s.rank, sum(cs.points) as total_points,
                       count(*) FILTER (WHERE cs.correct) as solved
                FROM students s
                LEFT JOIN ctf_submissions cs ON cs.student_id = s.id
                GROUP BY s.id HAVING count(*) FILTER (WHERE cs.correct) > 0
                ORDER BY total_points DESC
            """)
            rows = cur.fetchall()
    return {"scoreboard": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  CCCNet Blockchain (독립 블록체인)
# ══════════════════════════════════════════════════

# 성과 점수 테이블
ACHIEVEMENT_POINTS = {
    "lab_step": 0,        # 해당 스텝 points (동적)
    "lab_complete": 50,   # 실습 전체 완료 보너스
    "ctf_solve": 0,       # 문제 points (동적)
    "battle_join": 20,
    "battle_win": 50,
    "bug_report": 100,
    "improvement": 200,
    "monthly_top": 500,
    "rank_up": 1000,
}

def _cccnet_add_block(student_id: str, block_type: str, points: int, context_id: str = "", description: str = "", metadata: dict = {}) -> str:
    """CCCNet에 블록 추가 + 학생 total_blocks 갱신"""
    import hashlib as _h
    conn = _conn()
    try:
        with conn.cursor() as cur:
            # 이전 블록 해시
            cur.execute("SELECT block_hash FROM cccnet_blocks WHERE student_id=%s ORDER BY id DESC LIMIT 1", (student_id,))
            prev = cur.fetchone()
            prev_hash = prev[0] if prev else "0" * 64
            # 블록 인덱스
            cur.execute("SELECT COALESCE(MAX(block_index),0)+1 FROM cccnet_blocks WHERE student_id=%s", (student_id,))
            idx = cur.fetchone()[0]
            # 해시 생성 (difficulty=3)
            nonce = 0
            import time as _t
            data = f"{student_id}:{block_type}:{context_id}:{prev_hash}:{nonce}:{_t.time()}"
            block_hash = _h.sha256(data.encode()).hexdigest()
            # 삽입
            cur.execute(
                """INSERT INTO cccnet_blocks (student_id, block_index, block_hash, prev_hash, nonce, difficulty, block_type, context_id, points, description, metadata)
                   VALUES (%s,%s,%s,%s,%s,3,%s,%s,%s,%s,%s)""",
                (student_id, idx, block_hash, prev_hash, nonce, block_type, context_id, points, description, Json(metadata)),
            )
            # total_blocks 갱신
            cur.execute("UPDATE students SET total_blocks=total_blocks+%s WHERE id=%s", (points, student_id))
            conn.commit()
        return block_hash
    finally:
        conn.close()

@app.get("/cccnet/blocks", dependencies=[Depends(verify_api_key)])
def cccnet_blocks(student_id: str | None = None, block_type: str | None = None, limit: int = 50):
    q = "SELECT * FROM cccnet_blocks WHERE 1=1"
    params: list = []
    if student_id:
        q += " AND student_id=%s"; params.append(student_id)
    if block_type:
        q += " AND block_type=%s"; params.append(block_type)
    q += " ORDER BY id DESC LIMIT %s"; params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"blocks": [dict(r) for r in rows]}

@app.get("/cccnet/stats", dependencies=[Depends(verify_api_key)])
def cccnet_stats(student_id: str | None = None):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if student_id:
                cur.execute("SELECT count(*) as total_blocks, COALESCE(sum(points),0) as total_points FROM cccnet_blocks WHERE student_id=%s", (student_id,))
                row = cur.fetchone()
                cur.execute("SELECT block_type, count(*) as cnt, sum(points) as pts FROM cccnet_blocks WHERE student_id=%s GROUP BY block_type", (student_id,))
                by_type = {r["block_type"]: {"count": r["cnt"], "points": int(r["pts"])} for r in cur.fetchall()}
            else:
                cur.execute("SELECT count(*) as total_blocks, COALESCE(sum(points),0) as total_points FROM cccnet_blocks")
                row = cur.fetchone()
                cur.execute("SELECT block_type, count(*) as cnt, sum(points) as pts FROM cccnet_blocks GROUP BY block_type")
                by_type = {r["block_type"]: {"count": r["cnt"], "points": int(r["pts"])} for r in cur.fetchall()}
    return {"total_blocks": row["total_blocks"], "total_points": int(row["total_points"]), "by_type": by_type}

@app.get("/cccnet/verify", dependencies=[Depends(verify_api_key)])
def cccnet_verify(student_id: str | None = None):
    q = "SELECT * FROM cccnet_blocks"
    params: list = []
    if student_id:
        q += " WHERE student_id=%s"; params.append(student_id)
    q += " ORDER BY student_id, block_index"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    by_student: dict = {}
    for r in rows:
        by_student.setdefault(r["student_id"], []).append(r)
    results = {}
    for sid, blocks in by_student.items():
        valid = True; tampered = []
        for i in range(1, len(blocks)):
            if blocks[i]["prev_hash"] != blocks[i-1]["block_hash"]:
                valid = False; tampered.append(blocks[i]["block_index"])
        results[sid] = {"valid": valid, "blocks": len(blocks), "tampered": tampered}
    return {"verification": results, "total_blocks": len(rows)}

@app.get("/cccnet/leaderboard", dependencies=[Depends(verify_api_key)])
def cccnet_leaderboard(limit: int = 20):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT s.id, s.name, s.student_id, s.rank, s.total_blocks,
                       count(cb.id) as block_count, COALESCE(sum(cb.points),0) as total_points
                FROM students s
                LEFT JOIN cccnet_blocks cb ON cb.student_id = s.id
                GROUP BY s.id ORDER BY total_points DESC LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
    return {"leaderboard": [dict(r) for r in rows]}

@app.post("/cccnet/report-bug", dependencies=[Depends(verify_api_key)])
def report_bug(request: Request, description: str = "", course_id: str = "", week: int = 0):
    """교안/실습 오류 발견 보고 → 100점"""
    user = get_current_user(request)
    uid = user.get("sub", "")
    bh = _cccnet_add_block(uid, "bug_report", 100, f"{course_id}-week{week}", description)
    return {"block_hash": bh, "points": 100, "message": "오류 보고 감사합니다!"}

# ══════════════════════════════════════════════════
#  Blockchain (레거시 호환)
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

# ── CTI Threats (SubAgent 수집물) ────────────────────

@app.get("/threats/recent", dependencies=[Depends(verify_api_key)])
def recent_threats(limit: int = 10, days: int = 7):
    """최근 수집된 CVE/위협 목록 — collector.py가 저장한 JSON 파일 조회.

    반환: [{id, severity, cvss_score, summary, tags, courses, published, references}, ...]
    """
    import glob
    import json
    import datetime as _dt
    # __file__ = .../apps/ccc_api/src/main.py
    threats_dir = pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats"
    if not threats_dir.exists():
        return []
    cutoff = _dt.datetime.now() - _dt.timedelta(days=days)
    items = []
    for path in threats_dir.glob("*/CVE-*.json"):
        try:
            st_mtime = _dt.datetime.fromtimestamp(path.stat().st_mtime)
            if st_mtime < cutoff:
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append({
            "id": doc.get("id", ""),
            "published": doc.get("published", ""),
            "severity": doc.get("severity", "UNKNOWN"),
            "cvss_score": doc.get("cvss_score", 0),
            "summary": doc.get("summary", "")[:300],
            "impact": doc.get("impact", "")[:120],
            "tags": doc.get("tags", []),
            "courses": doc.get("courses", []),
            "references": (doc.get("references") or [])[:2],
        })
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    items.sort(key=lambda x: (sev_order.get(x["severity"], 9), -float(x.get("cvss_score") or 0)))
    return items[:limit]


@app.get("/threats/digest/{day}", dependencies=[Depends(verify_api_key)])
def threat_digest(day: str):
    """일일 다이제스트 markdown 반환 — day: YYYY-MM-DD"""
    threats_dir = pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats"
    path = threats_dir / day / "digest.md"
    if not path.exists():
        raise HTTPException(404, f"no digest for {day}")
    return {"day": day, "content": path.read_text(encoding="utf-8")}


@app.get("/news/recent", dependencies=[Depends(verify_api_key)])
def recent_news(limit: int = 20, days: int = 7, category: str = ""):
    """뉴스/커뮤니티 이슈 목록 — AI 에이전트 공격 우선순위 정렬.

    category 필터: ai_agent_attack | ai_under_attack | attack_technique | general
    """
    import json as _j
    import datetime as _dt
    threats_dir = pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats"
    if not threats_dir.exists():
        return []
    cutoff = _dt.datetime.now() - _dt.timedelta(days=days)
    items = []
    for path in threats_dir.glob("*/news/*.json"):
        try:
            st = _dt.datetime.fromtimestamp(path.stat().st_mtime)
            if st < cutoff:
                continue
            doc = _j.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if category and doc.get("category") != category:
            continue
        slug = path.stem  # 파일명(확장자 제외) = slug
        items.append({
            "slug": slug,
            "title": doc.get("title", ""),
            "source": doc.get("source", ""),
            "published": doc.get("published", ""),
            "link": doc.get("link", ""),
            "summary": doc.get("summary", "")[:300],
            "tags": doc.get("tags", []),
            "severity": doc.get("severity", ""),
            "category": doc.get("category", "general"),
            "priority": doc.get("priority", 0),
            "has_deep": bool(doc.get("deep_analysis_path")),
        })
    items.sort(key=lambda x: -x.get("priority", 0))
    return items[:limit]


@app.get("/trending/features", dependencies=[Depends(verify_api_key)])
def list_features():
    """지속 화제 특집 목록 (trending/)"""
    import json as _j
    trending_dir = pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats" / "trending"
    if not trending_dir.exists():
        return []
    features = []
    for topic_dir in trending_dir.iterdir():
        if not topic_dir.is_dir():
            continue
        meta_path = topic_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = _j.loads(meta_path.read_text(encoding="utf-8"))
            features.append({
                "topic": meta.get("topic", topic_dir.name),
                "article_count": meta.get("article_count", 0),
                "day_span": meta.get("day_span", 0),
                "first_seen": meta.get("first_seen", ""),
                "last_seen": meta.get("last_seen", ""),
                "avg_priority": meta.get("avg_priority", 0),
                "updated": meta.get("updated", ""),
                "has_analysis": (topic_dir / "analysis.md").exists(),
            })
        except Exception:
            continue
    features.sort(key=lambda x: (-float(x.get("avg_priority", 0) or 0), -int(x.get("day_span", 0) or 0)))
    return features


@app.get("/trending/features/{topic}", dependencies=[Depends(verify_api_key)])
def get_feature(topic: str):
    """특집 상세 — analysis.md + sources.json"""
    import json as _j
    trending_dir = pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats" / "trending"
    topic_dir = trending_dir / topic
    if not topic_dir.exists():
        raise HTTPException(404, f"no feature: {topic}")
    md_path = topic_dir / "analysis.md"
    sources_path = topic_dir / "sources.json"
    meta_path = topic_dir / "meta.json"
    return {
        "topic": topic,
        "content": md_path.read_text(encoding="utf-8") if md_path.exists() else "",
        "sources": _j.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else [],
        "meta": _j.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {},
    }


# ── 관리자: 자동 생성 콘텐츠 목록 + 승인 흐름 ────────

def _approvals_path() -> pathlib.Path:
    p = pathlib.Path(__file__).resolve().parents[3] / "contents" / ".approvals.json"
    if not p.exists():
        p.write_text("{}", encoding="utf-8")
    return p


def _load_approvals() -> dict:
    import json as _j
    try:
        return _j.loads(_approvals_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_approvals(d: dict):
    import json as _j
    _approvals_path().write_text(_j.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/admin/auto-content", dependencies=[Depends(verify_api_key)])
def list_auto_content(request: Request):
    """자동 생성된 threats/battles/rules 일괄 조회 (관리자 전용)."""
    _require_admin(request)
    import json as _j
    root = pathlib.Path(__file__).resolve().parents[3] / "contents"
    approvals = _load_approvals()

    threats, battles, rules = [], [], []
    # Threats
    for p in (root / "threats").glob("*/CVE-*.json") if (root / "threats").exists() else []:
        try:
            d = _j.loads(p.read_text(encoding="utf-8"))
            key = f"threat:{d.get('id','')}"
            threats.append({
                "id": d.get("id", ""),
                "severity": d.get("severity", "?"),
                "cvss_score": d.get("cvss_score", 0),
                "summary": d.get("summary", "")[:200],
                "tags": d.get("tags", []),
                "courses": d.get("courses", []),
                "path": str(p.relative_to(root.parent)),
                "status": approvals.get(key, "pending"),
            })
        except Exception:
            continue
    # Battles
    for p in (root / "labs" / "battle-auto").glob("*.yaml") if (root / "labs" / "battle-auto").exists() else []:
        try:
            import yaml as _y
            d = _y.safe_load(p.read_text(encoding="utf-8"))
            key = f"battle:{p.name}"
            battles.append({
                "file": p.name,
                "lab_id": d.get("lab_id", ""),
                "title": d.get("title", "")[:120],
                "difficulty": d.get("difficulty", ""),
                "steps": len(d.get("steps") or []),
                "path": str(p.relative_to(root.parent)),
                "status": approvals.get(key, "pending"),
            })
        except Exception:
            continue
    # Rules
    for subdir in ["suricata", "wazuh"]:
        for p in (root / "rules" / subdir).glob("*") if (root / "rules" / subdir).exists() else []:
            if p.suffix not in (".rules", ".xml"):
                continue
            key = f"rule:{subdir}:{p.name}"
            content = p.read_text(encoding="utf-8")
            rules.append({
                "type": subdir,
                "file": p.name,
                "lines": content.count("\n"),
                "preview": content[:200],
                "path": str(p.relative_to(root.parent)),
                "status": approvals.get(key, "pending"),
            })

    threats.sort(key=lambda x: -float(x.get("cvss_score") or 0))
    return {"threats": threats, "battles": battles, "rules": rules}


@app.post("/admin/auto-content/approve", dependencies=[Depends(verify_api_key)])
def approve_auto_content(body: dict[str, Any], request: Request):
    """콘텐츠 승인/거부. body: {key: 'threat:CVE-..' | 'battle:...yaml' | 'rule:suricata:...',
                              action: 'approve' | 'reject' | 'pending',
                              auto_generate: bool=True}

    threat을 승인하면 관련 과목에 '최신 보안이슈' 특강 (lecture + lab) 자동 생성.
    auto_generate=False로 비활성 가능.
    """
    _require_admin(request)
    key = str(body.get("key", ""))
    action = str(body.get("action", ""))
    auto_generate = body.get("auto_generate", True)
    if action not in ("approve", "reject", "pending"):
        raise HTTPException(400, "action must be approve/reject/pending")
    if not key:
        raise HTTPException(400, "key required")
    approvals = _load_approvals()
    prev = approvals.get(key, "pending")
    approvals[key] = action
    _save_approvals(approvals)

    result: dict[str, Any] = {"key": key, "status": action, "previous": prev}

    # news 승인 시 뉴스 기반 3-way 생성 (news → CVE-like 변환)
    if key.startswith("news:") and action == "approve" and auto_generate and prev != "approve":
        slug = key.split(":", 1)[1]

        def _dyn_import_news(mod_name: str, rel_path: str):
            import importlib.util
            p = pathlib.Path(__file__).resolve().parents[3] / rel_path
            spec = importlib.util.spec_from_file_location(mod_name, p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m

        generation = {}
        try:
            ts = _dyn_import_news("threat_special", "apps/battle-factory/threat_special.py")
            generation["special"] = ts.generate_for_approved_news(slug)
            news = ts.load_news_by_slug(slug)
            if news:
                cve_like = ts.news_to_cve_like(news)
                try:
                    bf = _dyn_import_news("battle_generator", "apps/battle-factory/generator.py")
                    generation["battle"] = bf.generate_battle(cve_like)
                except Exception as e:
                    generation["battle_error"] = str(e)[:300]
                try:
                    rf = _dyn_import_news("rule_generator", "apps/rule-factory/generator.py")
                    generation["rule"] = rf.generate_rules(cve_like, validate=False)
                except Exception as e:
                    generation["rule_error"] = str(e)[:300]
        except Exception as e:
            generation["error"] = str(e)[:300]
        result["generation"] = generation
        return result

    # threat 승인 시 3-way 자동 생성: 특강(과목별) + battle + rule
    if key.startswith("threat:") and action == "approve" and auto_generate and prev != "approve":
        cve_id = key.split(":", 1)[1]

        def _dyn_import(mod_name: str, rel_path: str):
            import importlib.util
            p = pathlib.Path(__file__).resolve().parents[3] / rel_path
            spec = importlib.util.spec_from_file_location(mod_name, p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m

        def _load_cve(cid: str):
            troot = pathlib.Path(os.getenv("CTI_OUT_DIR",
                str(pathlib.Path(__file__).resolve().parents[3] / "contents" / "threats")))
            import json as _j
            for p in troot.glob(f"*/{cid}.json"):
                try:
                    return _j.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
            return None

        generation = {}
        # 1) 특강 (과목별 lecture + lab)
        try:
            ts = _dyn_import("threat_special", "apps/battle-factory/threat_special.py")
            generation["special"] = ts.generate_for_approved_threat(cve_id)
        except Exception as e:
            generation["special_error"] = str(e)[:300]

        # 2) Battle 시나리오
        try:
            bf = _dyn_import("battle_generator", "apps/battle-factory/generator.py")
            cve = _load_cve(cve_id)
            if cve:
                generation["battle"] = bf.generate_battle(cve)
            else:
                generation["battle_error"] = "CVE 파일 없음"
        except Exception as e:
            generation["battle_error"] = str(e)[:300]

        # 3) Rule (Suricata + Wazuh)
        try:
            rf = _dyn_import("rule_generator", "apps/rule-factory/generator.py")
            cve = _load_cve(cve_id)
            if cve:
                generation["rule"] = rf.generate_rules(cve, validate=False)
            else:
                generation["rule_error"] = "CVE 파일 없음"
        except Exception as e:
            generation["rule_error"] = str(e)[:300]

        result["generation"] = generation

    return result


@app.post("/admin/auto-content/regenerate-special", dependencies=[Depends(verify_api_key)])
def regenerate_special(body: dict[str, Any], request: Request):
    """승인된 threat 1건에 대해 '최신 보안이슈' 특강 재생성 (수동)."""
    _require_admin(request)
    cve_id = str(body.get("cve_id", ""))
    if not cve_id:
        raise HTTPException(400, "cve_id required")
    try:
        import importlib.util
        ts_path = pathlib.Path(__file__).resolve().parents[3] / "apps" / "battle-factory" / "threat_special.py"
        spec = importlib.util.spec_from_file_location("threat_special", ts_path)
        ts_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ts_mod)
        rs = ts_mod.generate_for_approved_threat(cve_id)
        return {"cve_id": cve_id, "results": rs}
    except Exception as e:
        raise HTTPException(500, f"생성 실패: {e}")


@app.post("/admin/auto-content/deploy", dependencies=[Depends(verify_api_key)])
def deploy_auto_content(body: dict[str, Any], request: Request):
    """승인된 rule/battle을 실제 인프라에 배포. body: {key, dry_run=true}

    안전 장치:
    - 'approve' 상태인 콘텐츠만 배포 가능
    - dry_run=true (기본): 문법 체크만, 실제 apply 안 함
    - dry_run=false: 실제 VM에 append + reload (backup 자동)

    Rule 배포 경로:
    - suricata: secu VM /etc/suricata/rules/ccc-auto.rules (append), suricata-update + reload
    - wazuh: siem VM /var/ossec/etc/rules/local_rules.xml (append in group), manager restart

    Battle 배포: contents/labs/battle-auto-approved/<file>.yaml symlink (공식 과목 편입)
    """
    _require_admin(request)
    key = str(body.get("key", ""))
    dry_run = bool(body.get("dry_run", True))
    approvals = _load_approvals()
    if approvals.get(key) != "approve":
        raise HTTPException(403, f"not approved (current status: {approvals.get(key, 'pending')})")

    root = pathlib.Path(__file__).resolve().parents[3] / "contents"

    if key.startswith("rule:suricata:"):
        fname = key.split(":", 2)[2]
        rule_path = root / "rules" / "suricata" / fname
        if not rule_path.exists():
            raise HTTPException(404, f"rule file not found: {fname}")
        return _deploy_suricata_rule(rule_path, dry_run)
    elif key.startswith("rule:wazuh:"):
        fname = key.split(":", 2)[2]
        rule_path = root / "rules" / "wazuh" / fname
        if not rule_path.exists():
            raise HTTPException(404, f"rule file not found: {fname}")
        return _deploy_wazuh_rule(rule_path, dry_run)
    elif key.startswith("battle:"):
        fname = key.split(":", 1)[1]
        src = root / "labs" / "battle-auto" / fname
        if not src.exists():
            raise HTTPException(404, f"battle file not found: {fname}")
        dst_dir = root / "labs" / "battle-auto-approved"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / fname
        if dry_run:
            return {"dry_run": True, "src": str(src), "dst": str(dst), "would_copy": True}
        import shutil
        shutil.copy2(src, dst)
        return {"dry_run": False, "copied_to": str(dst)}
    else:
        raise HTTPException(400, f"unknown key prefix: {key}")


def _deploy_suricata_rule(rule_path: pathlib.Path, dry_run: bool) -> dict:
    """secu VM에 suricata rule append + syntax check + reload.

    배포 이식성: VM_SECU_IP env로 override 가능.
    """
    from packages.bastion import run_command as _rc
    secu_ip = os.getenv("VM_SECU_IP", "10.20.30.1")
    # 실제 관리 네트워크(외부)에서 접근 시 override
    secu_ext = os.getenv("VM_SECU_EXT_IP", "192.168.0.114")
    target = secu_ext  # run_command는 외부 IP 기반 SSH

    rule_content = rule_path.read_text(encoding="utf-8")
    # 1) 임시 파일로 업로드
    temp_path = f"/tmp/ccc-rule-{rule_path.name}"
    # base64로 안전 전송
    import base64 as _b64
    b64 = _b64.b64encode(rule_content.encode()).decode()
    upload_cmd = f"echo '{b64}' | base64 -d > {temp_path} && wc -l {temp_path}"
    r1 = _rc(target, upload_cmd, timeout=15)
    if not r1.get("stdout"):
        return {"error": "upload 실패", "stderr": r1.get("stderr", "")[:300]}

    # 2) suricata -T 문법 체크 (임시 파일 포함한 룰셋 dry-run)
    test_cmd = (
        f"sudo cp {temp_path} /etc/suricata/rules/ccc-auto-test.rules 2>&1 && "
        f"sudo suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -20; "
        f"sudo rm -f /etc/suricata/rules/ccc-auto-test.rules"
    )
    r2 = _rc(target, test_cmd, timeout=30)
    test_out = r2.get("stdout", "") + r2.get("stderr", "")
    has_error = "ERROR" in test_out or "error" in test_out.lower() or "parse error" in test_out.lower()
    syntax_ok = not has_error and "Configuration provided was successfully loaded" in test_out

    if dry_run or not syntax_ok:
        return {
            "dry_run": dry_run,
            "syntax_ok": syntax_ok,
            "test_output": test_out[-500:],
            "applied": False,
        }

    # 3) 실제 적용: ccc-auto.rules 파일에 append + suricata.yaml에 include (한번만)
    apply_cmd = (
        f"sudo cp -n /etc/suricata/rules/ccc-auto.rules /etc/suricata/rules/ccc-auto.rules.bak 2>/dev/null; "
        f"sudo cat {temp_path} >> /etc/suricata/rules/ccc-auto.rules && "
        f"sudo grep -q 'ccc-auto.rules' /etc/suricata/suricata.yaml || "
        f"sudo sed -i '/rule-files:/a\\    - ccc-auto.rules' /etc/suricata/suricata.yaml && "
        f"sudo systemctl reload suricata 2>&1 && echo APPLIED_OK"
    )
    r3 = _rc(target, apply_cmd, timeout=30)
    applied = "APPLIED_OK" in r3.get("stdout", "")
    return {
        "dry_run": False,
        "syntax_ok": True,
        "applied": applied,
        "apply_output": (r3.get("stdout", "") + r3.get("stderr", ""))[-500:],
    }


@app.get("/admin/monitor/alerts", dependencies=[Depends(verify_api_key)])
def monitor_alerts(request: Request, limit: int = 20):
    """siem VM alerts.json에서 최근 N건 가져오기 (관리자 모니터링 용)."""
    _require_admin(request)
    from packages.bastion import run_command as _rc
    siem_ext = os.getenv("VM_SIEM_EXT_IP", "192.168.0.111")
    cmd = f"echo '1' | sudo -S -p '' tail -n {limit} /var/ossec/logs/alerts/alerts.json 2>/dev/null"
    r = _rc(siem_ext, cmd, timeout=10)
    lines = (r.get("stdout", "") or "").strip().split("\n")
    out = []
    import json as _j
    for ln in lines[-limit:]:
        if not ln.strip():
            continue
        try:
            alert = _j.loads(ln)
            out.append({
                "timestamp": alert.get("timestamp", ""),
                "rule_id": (alert.get("rule") or {}).get("id", ""),
                "level": (alert.get("rule") or {}).get("level", 0),
                "description": (alert.get("rule") or {}).get("description", "")[:120],
                "agent_name": (alert.get("agent") or {}).get("name", ""),
                "src_ip": alert.get("src_ip", ""),
                "full_log": (alert.get("full_log") or "")[:200],
            })
        except Exception:
            continue
    return {"alerts": out, "source": f"siem({siem_ext})"}


@app.get("/admin/monitor/test-stats", dependencies=[Depends(verify_api_key)])
def monitor_test_stats(request: Request):
    """Bastion 실증 테스트 현황 요약 (연구자·관리자용)."""
    _require_admin(request)
    progress_path = pathlib.Path(__file__).resolve().parents[3] / "bastion_test_progress.json"
    if not progress_path.exists():
        return {"error": "no test progress file"}
    import json as _j, collections
    try:
        d = _j.loads(progress_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": str(e)}
    t = collections.Counter()
    per_course = {}
    for c, weeks in d.get("results", {}).items():
        ct = collections.Counter()
        for wk, steps in (weeks or {}).items():
            if not isinstance(steps, dict):
                continue
            for s, info in steps.items():
                if not isinstance(info, dict):
                    continue
                status = info.get("status", "?")
                ct[status] += 1
                t[status] += 1
        per_course[c] = dict(ct)
    total = d.get("total_steps", sum(t.values()))
    return {
        "total": total,
        "pass_rate": round(100 * t.get("pass", 0) / max(total, 1), 1),
        "totals": dict(t),
        "per_course": per_course,
    }


@app.get("/admin/sensitive", dependencies=[Depends(verify_api_key)])
def list_sensitive(request: Request):
    """위험 payload hash 목록 (admin only). verify.semantic 에서 <SENSITIVE:xxx> 로 redact 된 원본 색인."""
    _require_admin(request)
    sdir = pathlib.Path(__file__).resolve().parents[3] / "contents" / ".sensitive"
    if not sdir.exists():
        return {"items": []}
    items = []
    for f in sorted(sdir.glob("*.txt")):
        try:
            content = f.read_text(encoding="utf-8")
            items.append({
                "hash": f.stem,
                "preview": content[:120],
                "size": len(content),
                "mtime": f.stat().st_mtime,
            })
        except Exception:
            continue
    return {"items": items, "count": len(items)}


@app.get("/admin/sensitive/{h}", dependencies=[Depends(verify_api_key)])
def get_sensitive(h: str, request: Request):
    """위험 payload hash → 원본 텍스트 복원 (admin only)."""
    _require_admin(request)
    if not h.isalnum() or len(h) > 64:
        raise HTTPException(400, "invalid hash")
    sdir = pathlib.Path(__file__).resolve().parents[3] / "contents" / ".sensitive"
    target = sdir / f"{h}.txt"
    if not target.exists():
        raise HTTPException(404, f"sensitive hash not found: {h}")
    content = target.read_text(encoding="utf-8")
    return {"hash": h, "content": content}


def _deploy_wazuh_rule(rule_path: pathlib.Path, dry_run: bool) -> dict:
    """siem VM에 Wazuh rule append + wazuh-logtest 검증 + manager restart."""
    from packages.bastion import run_command as _rc
    siem_ext = os.getenv("VM_SIEM_EXT_IP", "192.168.0.111")
    target = siem_ext

    rule_content = rule_path.read_text(encoding="utf-8")
    import base64 as _b64
    b64 = _b64.b64encode(rule_content.encode()).decode()
    temp_path = f"/tmp/ccc-wazuh-{rule_path.name}"
    upload_cmd = f"echo '{b64}' | base64 -d > {temp_path} && wc -l {temp_path}"
    r1 = _rc(target, upload_cmd, timeout=15)
    if not r1.get("stdout"):
        return {"error": "upload 실패", "stderr": r1.get("stderr", "")[:300]}

    # wazuh xml 문법 체크 — xmllint 사용 (group 래핑 필요)
    check_cmd = (
        f"(echo '<wazuh_local_rules>'; cat {temp_path}; echo '</wazuh_local_rules>') | "
        f"xmllint --noout - 2>&1; "
        f"echo CHECK_END"
    )
    r2 = _rc(target, check_cmd, timeout=15)
    check_out = r2.get("stdout", "") + r2.get("stderr", "")
    syntax_ok = "parser error" not in check_out.lower() and "error" not in check_out.lower().split("check_end")[0]

    if dry_run or not syntax_ok:
        return {"dry_run": dry_run, "syntax_ok": syntax_ok,
                "test_output": check_out[-500:], "applied": False}

    apply_cmd = (
        f"echo '1' | sudo -S -p '' cp /var/ossec/etc/rules/local_rules.xml /var/ossec/etc/rules/local_rules.xml.bak-$(date +%s) && "
        f"echo '1' | sudo -S -p '' bash -c 'cat {temp_path} >> /var/ossec/etc/rules/local_rules.xml' && "
        f"echo '1' | sudo -S -p '' chown wazuh:wazuh /var/ossec/etc/rules/local_rules.xml && "
        f"echo '1' | sudo -S -p '' systemctl restart wazuh-manager && "
        f"sleep 3 && "
        f"echo '1' | sudo -S -p '' systemctl is-active wazuh-manager && echo APPLIED_OK"
    )
    r3 = _rc(target, apply_cmd, timeout=45)
    applied = "APPLIED_OK" in r3.get("stdout", "")
    return {"dry_run": False, "syntax_ok": True, "applied": applied,
            "apply_output": (r3.get("stdout", "") + r3.get("stderr", ""))[-500:]}


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


# ── 콘텐츠 검색 ───────────────────────────────────

@app.get("/search", dependencies=[Depends(verify_api_key)])
def search_content(q: str, limit: int = 30):
    """교안/실습/Cyber Range 전체 콘텐츠에서 키워드 검색.

    반환: [{type, course, week, title, context, link}, ...]
    type: lecture | lab_nonai | lab_ai
    """
    import re
    q_lower = q.lower()
    results = []

    # 1. 교안 검색 (lecture.md)
    edu_dir = os.path.join(_CONTENT_DIR, "education")
    if os.path.isdir(edu_dir):
        for course_dir in sorted(os.listdir(edu_dir)):
            course_path = os.path.join(edu_dir, course_dir)
            if not os.path.isdir(course_path):
                continue
            for week_dir in sorted(os.listdir(course_path)):
                lec_path = os.path.join(course_path, week_dir, "lecture.md")
                if not os.path.exists(lec_path):
                    continue
                try:
                    content = open(lec_path, encoding="utf-8").read()
                except Exception:
                    continue
                if q_lower not in content.lower():
                    continue
                # 첫 번째 제목 추출
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else week_dir
                # 매칭 컨텍스트 추출 (키워드 주변 텍스트)
                idx = content.lower().find(q_lower)
                start = max(0, idx - 40)
                end = min(len(content), idx + len(q) + 60)
                context = content[start:end].replace('\n', ' ').strip()
                week_num = re.search(r'(\d+)', week_dir)
                results.append({
                    "type": "lecture",
                    "course": course_dir,
                    "week": int(week_num.group(1)) if week_num else 0,
                    "title": title[:80],
                    "context": f"...{context}...",
                    "link": f"/app/training?course={course_dir}&view=lecture&week={week_num.group(1) if week_num else 1}",
                })

    # 2. 실습 검색 (lab YAML)
    if os.path.isdir(_LABS_DIR):
        for lab_dir in sorted(os.listdir(_LABS_DIR)):
            lab_path = os.path.join(_LABS_DIR, lab_dir)
            if not os.path.isdir(lab_path):
                continue
            version = "ai" if lab_dir.endswith("-ai") else "non-ai"
            for yml_file in sorted(os.listdir(lab_path)):
                if not yml_file.endswith(".yaml"):
                    continue
                try:
                    import yaml
                    y = yaml.safe_load(open(os.path.join(lab_path, yml_file), encoding="utf-8"))
                except Exception:
                    continue
                # 타이틀 + 전체 step 텍스트에서 검색
                full_text = y.get("title", "") + " " + y.get("description", "")
                for s in y.get("steps", []):
                    full_text += " " + (s.get("instruction", "") or "")
                    full_text += " " + (s.get("bastion_prompt", "") or "")
                    full_text += " " + (s.get("hint", "") or "")
                if q_lower not in full_text.lower():
                    continue
                idx = full_text.lower().find(q_lower)
                context = full_text[max(0, idx - 30):idx + len(q) + 50].replace('\n', ' ').strip()
                lab_id = y.get("lab_id", "")
                results.append({
                    "type": f"lab_{version.replace('-', '')}",
                    "course": y.get("course", lab_dir),
                    "week": y.get("week", 0),
                    "title": y.get("title", yml_file)[:80],
                    "context": f"...{context}...",
                    "link": f"/app/{'training' if version == 'ai' else 'labs'}?course={y.get('course', lab_dir).replace('-ai', '').replace('-nonai', '')}&view=lab&lab={lab_id}",
                })

    results.sort(key=lambda r: (r["course"], r["week"], r["type"]))
    return {"query": q, "total": len(results), "results": results[:limit]}


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
