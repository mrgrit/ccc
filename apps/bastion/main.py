#!/usr/bin/env python3
"""bastion — CCC 운영 관리 에이전트 (대화형 TUI)

Claude Code 아키텍처를 참고한 인터랙티브 에이전트.
- Ollama tool calling으로 자연어 → 도구 실행 → 결과 설명 (단일 대화 루프)
- 스트리밍 출력 (토큰 단위 실시간)
- 권한 확인 시스템 (위험 명령 사전 확인)
- 세션 저장/복원 (.ccc/sessions/)
- 파일 도구 (read/write/glob/grep)

Usage:
    python -m apps.bastion.main
    ./dev.sh bastion
"""
from __future__ import annotations
import os
import sys
import json
import time
import glob as _glob
import re
import uuid
from pathlib import Path
from typing import Any

# ── 의존성 ──
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich import box
except ImportError:
    print("pip install rich"); sys.exit(1)

try:
    import httpx
except ImportError:
    print("pip install httpx"); sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from packages.bastion import (
    LLM_BASE_URL, LLM_MODEL, SKILLS, CCC_DIR,
    build_system_prompt, dispatch_skill, health_check,
    onboard_vm, run_command, system_status, diagnose_vm,
    shell_exec, ccc_manage,
)

# ── Console ───────────────────────────────────────
console = Console()
O = "orange3"; G = "bright_black"; GR = "green"; R = "red"; B = "dodger_blue2"; P = "medium_purple"

# ── Paths ─────────────────────────────────────────
CCC_HOME = Path.home() / ".ccc"
SESSIONS_DIR = CCC_HOME / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════
#  1. 세션 저장/복원 (.ccc/sessions/)
# ══════════════════════════════════════════════════
MAX_CTX = 8000
MAX_MSG = 600

class Session:
    def __init__(self, session_id: str = None):
        self.id = session_id or time.strftime("%Y%m%d_%H%M%S")
        self.history: list[dict] = []
        self.summary: str = ""
        self.infras: list[dict] = []
        self.start = time.time()
        self.tasks = 0
        self.file = SESSIONS_DIR / f"{self.id}.json"

    # ── persist ──
    def save(self):
        data = {"id": self.id, "history": self.history, "summary": self.summary,
                "infras": self.infras, "start": self.start, "tasks": self.tasks}
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, session_id: str) -> "Session":
        s = cls(session_id)
        if s.file.exists():
            d = json.loads(s.file.read_text())
            s.history, s.summary = d.get("history", []), d.get("summary", "")
            s.infras, s.start, s.tasks = d.get("infras", []), d.get("start", time.time()), d.get("tasks", 0)
        return s

    @classmethod
    def list_sessions(cls) -> list[dict]:
        sessions = []
        for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True)[:10]:
            try:
                d = json.loads(f.read_text())
                turns = len(d.get("history", []))
                sessions.append({"id": d["id"], "turns": turns, "tasks": d.get("tasks", 0)})
            except Exception:
                pass
        return sessions

    # ── message & compaction ──
    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content, "ts": time.time()})
        self._compact()
        self.save()

    def _compact(self):
        total = sum(len(m["content"]) for m in self.history)
        if total <= MAX_CTX:
            return
        mid = len(self.history) // 2
        old = self.history[:mid]
        self.history = self.history[mid:]
        txt = "\n".join(f"{'user' if m['role']=='user' else 'assistant'}: {m['content'][:200]}" for m in old)
        self.summary = (self.summary + "\n---\n" + txt)[-2000:] if self.summary else txt[:2000]

    def build_messages(self) -> list[dict]:
        msgs = []
        if self.summary:
            msgs.append({"role": "user", "content": f"[이전 대화 요약]\n{self.summary}"})
            msgs.append({"role": "assistant", "content": "확인했습니다. 계속하겠습니다."})
        for m in self.history:
            c = m["content"]
            msgs.append({"role": m["role"], "content": c[:MAX_MSG] + "..." if len(c) > MAX_MSG else c})
        return msgs

    def context(self) -> dict:
        return {"infras": self.infras, "duration": int(time.time() - self.start), "tasks": self.tasks}


# ══════════════════════════════════════════════════
#  2. 권한 시스템
# ══════════════════════════════════════════════════
DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+/", "루트 디렉토리 삭제"),
    (r"mkfs\.", "디스크 포맷"),
    (r"dd\s+if=.*/dev/zero.*of=.*/dev/", "디스크 초기화"),
    (r"DROP\s+(TABLE|DATABASE)", "DB 삭제"),
    (r"reset_db", "DB 전체 초기화"),
    (r":(){ :\|:& };:", "포크 폭탄"),
    (r">\s*/dev/sd", "디스크 직접 쓰기"),
]

CONFIRM_PATTERNS = [
    (r"apt.*(remove|purge|autoremove)", "패키지 삭제"),
    (r"systemctl\s+(stop|disable)", "서비스 중지"),
    (r"kill\s+-9", "프로세스 강제 종료"),
    (r"reboot|shutdown|poweroff", "시스템 재시작/종료"),
    (r"firewall_close", "방화벽 포트 차단"),
    (r"stop", "서비스 중지"),
    (r"pip.*uninstall", "패키지 삭제"),
    (r"docker\s+(rm|rmi|prune)", "컨테이너/이미지 삭제"),
    (r"git\s+(reset|push\s+--force)", "git 위험 작업"),
]

def check_permission(skill_name: str, params: dict) -> bool:
    """권한 확인 — Claude Code의 3단계 permission 참고
    Returns True if allowed, False if denied.
    """
    # 검사 대상 문자열 조합
    check_str = json.dumps(params, ensure_ascii=False) + " " + skill_name
    if skill_name == "shell":
        check_str += " " + params.get("command", "")
    elif skill_name == "ccc":
        check_str += " " + params.get("action", "")

    # 절대 거부
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, check_str, re.IGNORECASE):
            console.print(f"  [bold {R}]⛔ 거부:[/] {desc} — 이 작업은 실행할 수 없습니다.")
            return False

    # 확인 필요
    for pattern, desc in CONFIRM_PATTERNS:
        if re.search(pattern, check_str, re.IGNORECASE):
            console.print(f"  [yellow]⚠ {desc}[/]")
            return Confirm.ask(f"  실행하시겠습니까?", default=False)

    return True  # 자동 허용


# ══════════════════════════════════════════════════
#  3. 파일 도구
# ══════════════════════════════════════════════════
def file_read(path: str, offset: int = 0, limit: int = 200) -> dict:
    try:
        p = Path(path).expanduser()
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[offset:offset + limit]
        numbered = "\n".join(f"{i+offset+1:4d}\t{l}" for i, l in enumerate(selected))
        return {"path": str(p), "lines": len(lines), "showing": f"{offset+1}-{offset+len(selected)}", "content": numbered}
    except Exception as e:
        return {"error": str(e)}

def file_write(path: str, content: str) -> dict:
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "bytes": len(content), "status": "written"}
    except Exception as e:
        return {"error": str(e)}

def file_edit(path: str, old_string: str, new_string: str) -> dict:
    try:
        p = Path(path).expanduser()
        text = p.read_text(encoding="utf-8")
        if old_string not in text:
            return {"error": f"old_string not found in {path}"}
        count = text.count(old_string)
        text = text.replace(old_string, new_string, 1)
        p.write_text(text, encoding="utf-8")
        return {"path": str(p), "replacements": 1, "total_occurrences": count, "status": "edited"}
    except Exception as e:
        return {"error": str(e)}

def file_glob(pattern: str, path: str = ".") -> dict:
    try:
        matches = sorted(_glob.glob(os.path.join(path, pattern), recursive=True))[:50]
        return {"pattern": pattern, "count": len(matches), "files": matches}
    except Exception as e:
        return {"error": str(e)}

def file_grep(pattern: str, path: str = ".", glob_filter: str = "") -> dict:
    try:
        cmd = f"grep -rn '{pattern}' {path}"
        if glob_filter:
            cmd += f" --include='{glob_filter}'"
        cmd += " | head -30"
        r = shell_exec(cmd, timeout=10)
        return {"pattern": pattern, "matches": r.get("stdout", ""), "exit_code": r.get("exit_code", -1)}
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════
#  4. Tool Definitions (Ollama function calling)
# ══════════════════════════════════════════════════
TOOL_DEFS = [
    {"type": "function", "function": {
        "name": "ccc",
        "description": "CCC 플랫폼 관리: start, stop, restart, status, logs, logs_error, build_ui, deploy, update, start_api, stop_api, start_db, stop_db, reset_db, backup_db, env, set_env, create_admin, student_list, firewall_open, firewall_close, check_port",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string"}, "port": {"type": "string"}, "key": {"type": "string"},
            "value": {"type": "string"}, "id": {"type": "string"}, "name": {"type": "string"}, "password": {"type": "string"},
        }, "required": ["action"]},
    }},
    {"type": "function", "function": {
        "name": "shell",
        "description": "로컬 쉘 명령 실행. 파일 조회, 패키지 설치, 프로세스 관리, 네트워크 확인 등",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "실행할 쉘 명령어"},
        }, "required": ["command"]},
    }},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "파일 내용 읽기 (줄번호 포함)",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "offset": {"type": "integer", "description": "시작 줄 (0-based)"},
            "limit": {"type": "integer", "description": "읽을 줄 수 (기본 200)"},
        }, "required": ["path"]},
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "파일 생성/덮어쓰기",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"},
        }, "required": ["path", "content"]},
    }},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "파일 내 문자열 치환 (old_string → new_string)",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"},
        }, "required": ["path", "old_string", "new_string"]},
    }},
    {"type": "function", "function": {
        "name": "glob",
        "description": "파일 패턴 검색 (예: **/*.py)",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"}, "path": {"type": "string", "description": "검색 시작 경로 (기본: CCC_DIR)"},
        }, "required": ["pattern"]},
    }},
    {"type": "function", "function": {
        "name": "grep",
        "description": "파일 내용 검색 (정규식)",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"}, "path": {"type": "string", "description": "검색 경로"},
            "glob_filter": {"type": "string", "description": "파일 필터 (예: *.py)"},
        }, "required": ["pattern"]},
    }},
    {"type": "function", "function": {
        "name": "onboard",
        "description": "학생 VM에 SSH로 SubAgent 설치 + 역할별 소프트웨어 배포",
        "parameters": {"type": "object", "properties": {
            "ip": {"type": "string"}, "role": {"type": "string", "enum": ["attacker","secu","web","siem","manager","windows"]},
            "ssh_user": {"type": "string"}, "ssh_password": {"type": "string"},
        }, "required": ["ip", "role"]},
    }},
    {"type": "function", "function": {
        "name": "health_check",
        "description": "SubAgent 상태 확인 (A2A)",
        "parameters": {"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]},
    }},
    {"type": "function", "function": {
        "name": "run_command",
        "description": "원격 VM SubAgent에 명령 실행 (A2A)",
        "parameters": {"type": "object", "properties": {
            "ip": {"type": "string"}, "script": {"type": "string"},
        }, "required": ["ip", "script"]},
    }},
]


# ══════════════════════════════════════════════════
#  5. 도구 디스패치 (권한 확인 포함)
# ══════════════════════════════════════════════════
def dispatch_tool(name: str, params: dict) -> dict:
    """도구 실행 — 권한 확인 후 디스패치"""
    # 권한 확인
    if not check_permission(name, params):
        return {"status": "denied", "message": "사용자가 실행을 거부했습니다."}

    if name == "read_file":
        return file_read(params["path"], params.get("offset", 0), params.get("limit", 200))
    elif name == "write_file":
        return file_write(params["path"], params["content"])
    elif name == "edit_file":
        return file_edit(params["path"], params["old_string"], params["new_string"])
    elif name == "glob":
        return file_glob(params["pattern"], params.get("path", CCC_DIR))
    elif name == "grep":
        return file_grep(params["pattern"], params.get("path", CCC_DIR), params.get("glob_filter", ""))
    else:
        return dispatch_skill(name, params)


# ══════════════════════════════════════════════════
#  6. UI 렌더링
# ══════════════════════════════════════════════════
def render_banner():
    banner = Text()
    banner.append("  ____            _   _             \n", style=O)
    banner.append(" | __ )  __ _ ___| |_(_) ___  _ __  \n", style=O)
    banner.append(" |  _ \\ / _` / __| __| |/ _ \\| '_ \\ \n", style=O)
    banner.append(" | |_) | (_| \\__ \\ |_| | (_) | | | |\n", style=O)
    banner.append(" |____/ \\__,_|___/\\__|_|\\___/|_| |_|\n", style=O)
    console.print(banner)
    console.print(f"  CCC 운영 관리 에이전트", style=G)
    console.print(f"  LLM: {LLM_BASE_URL} / {LLM_MODEL}", style=G)
    console.print(f"  세션: {SESSIONS_DIR}", style=G)
    console.print()

def render_tool_call(name: str, params: dict):
    p = " ".join(f"{k}={v}" for k, v in params.items() if k not in ("infras","content") and len(str(v)) < 80)
    console.print(f"\n  ⚡ [bold {O}]{name}[/] {p}", highlight=False)

def render_result(result: dict):
    if "error" in result:
        console.print(f"  [bold {R}]✗ Error:[/] {result['error']}"); return
    if "status" in result and result["status"] == "denied":
        return
    if "content" in result and "path" in result:  # file_read
        console.print(f"  [{G}]✓[/] {result.get('path','')} ({result.get('showing','')}/{result.get('lines','')} lines)")
        content = result["content"]
        if len(content) > 3000:
            content = content[:3000] + "\n..."
        console.print(Syntax(content, "text", theme="monokai", line_numbers=False, padding=1))
        return
    if "files" in result:  # glob
        console.print(f"  [{G}]✓[/] {result.get('count', 0)} files")
        for f in result["files"][:20]:
            console.print(f"    {f}", style=G)
        return
    if "matches" in result:  # grep
        console.print(Syntax(result["matches"][:3000], "text", theme="monokai", line_numbers=False, padding=1))
        return
    if "stdout" in result:  # shell/ccc
        code = result.get("exit_code", -1)
        icon, color = ("✓", GR) if code == 0 else ("✗", R)
        console.print(f"  [{color}]{icon} {'성공' if code==0 else f'실패 (exit {code})'}[/]")
        stdout = result.get("stdout", "").strip()
        if stdout:
            console.print(Syntax(stdout[:5000], "bash", theme="monokai", line_numbers=False, padding=1))
        stderr = result.get("stderr", "").strip()
        if stderr:
            console.print(f"  [{R}]{stderr[:500]}[/]")
        return
    if "healthy" in result:
        h, color = ("✓ healthy", GR) if result["healthy"] else ("✗ failed", R)
        console.print(f"  [{color}]{h}[/]")
        for step in result.get("steps", []):
            s = "✓" if step.get("success") else "✗"
            console.print(f"    {s} {step.get('step','')}", style=G)
        return
    if "diagnosis" in result:
        console.print(Panel(result["diagnosis"], title="진단 결과", border_style=B)); return
    # fallback
    console.print(Syntax(json.dumps(result, ensure_ascii=False, indent=2)[:3000], "json", theme="monokai", line_numbers=False, padding=1))

def render_help():
    console.print(Panel(
        "[bold]사용법[/]\n\n"
        "자연어로 작업을 지시하세요. 예: 'API 시작해줘', 'main.py 보여줘', '.env 수정해줘'\n\n"
        f"[bold]CCC 관리[/]               [{P}]![/] CMD  로컬 쉘 직접 실행\n"
        f"  [{P}]/start[/] /stop /restart /svc /logs /errors /deploy /build /env\n\n"
        f"[bold]인프라[/]                  [bold]세션[/]\n"
        f"  [{P}]/status[/] /health /onboard /run   [{P}]/save[/] /load /sessions\n\n"
        f"  [{P}]/skills[/] /infras /history /clear /help /exit[/]\n",
        title="Bastion Help", border_style=O))


# ══════════════════════════════════════════════════
#  7. 스트리밍 Tool Calling Loop (Claude Code query.ts)
# ══════════════════════════════════════════════════
def execute_interactive(instruction: str, session: Session):
    """Claude Code 스타일 대화 루프 — 스트리밍 + tool calling"""
    session.add("user", instruction)
    ctx = session.context()

    system = build_system_prompt(
        f"등록된 인프라: {json.dumps(ctx['infras'], ensure_ascii=False)}\n"
        f"세션: {ctx['duration']}초, 완료: {ctx['tasks']}건\n"
        f"CCC 경로: {CCC_DIR}"
    )

    messages = [{"role": "system", "content": system}]
    messages.extend(session.build_messages())
    messages.append({"role": "user", "content": instruction})

    full_response = ""

    for iteration in range(5):  # max 5 tool call rounds
        try:
            # 스트리밍 + tool calling
            with httpx.stream("POST", f"{LLM_BASE_URL}/api/chat", json={
                "model": LLM_MODEL, "messages": messages, "tools": TOOL_DEFS,
                "stream": True, "options": {"temperature": 0.1},
            }, timeout=120.0) as r:

                streamed_text = ""
                tool_calls = []
                current_tc = None

                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg = chunk.get("message", {})

                    # 텍스트 토큰 스트리밍
                    token = msg.get("content", "")
                    if token:
                        if not streamed_text:
                            console.print()  # first token → newline
                        console.print(token, end="", highlight=False)
                        streamed_text += token

                    # tool call 수집
                    tcs = msg.get("tool_calls", [])
                    if tcs:
                        tool_calls.extend(tcs)

                    if chunk.get("done"):
                        break

                if streamed_text:
                    console.print()  # final newline
                    full_response += streamed_text

        except Exception as e:
            console.print(f"\n  [{R}]LLM 연결 실패: {e}[/]")
            break

        # tool call이 없으면 종료
        if not tool_calls:
            break

        # assistant 메시지를 대화에 추가
        messages.append({"role": "assistant", "content": streamed_text, "tool_calls": tool_calls})

        # 각 tool call 실행
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            params = fn.get("arguments", {})
            if isinstance(params, str):
                try: params = json.loads(params)
                except: params = {}

            render_tool_call(name, params)

            with console.status("[bold]실행 중...", spinner="dots", spinner_style=O):
                result = dispatch_tool(name, params)

            render_result(result)
            session.tasks += 1

            result_json = json.dumps(result, ensure_ascii=False)
            if len(result_json) > 3000:
                result_json = result_json[:3000] + "..."
            messages.append({"role": "tool", "content": result_json})

        tool_calls = []  # reset for next iteration

    if full_response:
        session.add("assistant", full_response[:500])
    session.save()
    console.print()


# ══════════════════════════════════════════════════
#  8. Slash Commands
# ══════════════════════════════════════════════════
def handle_slash(cmd: str, session: Session) -> bool:
    parts = cmd.strip().split(None, 2)
    c = parts[0].lower()

    if c in ("/exit", "/quit", "/q"):
        session.save()
        console.print(f"\n  [dim]세션 저장됨: {session.id}[/]")
        return False

    elif c == "/start":
        render_tool_call("ccc", {"action": "start"})
        with console.status("[bold]CCC 시작 중...", spinner="dots", spinner_style=O):
            r = ccc_manage("start")
        render_result(r)
    elif c == "/stop":
        if Confirm.ask("  CCC 전체를 중지하시겠습니까?", default=False):
            r = ccc_manage("stop"); render_result(r)
    elif c == "/restart":
        render_tool_call("ccc", {"action": "restart"})
        with console.status("[bold]재시작 중...", spinner="dots", spinner_style=O):
            r = ccc_manage("restart")
        render_result(r)
    elif c in ("/svc", "/service"):
        r = ccc_manage("status"); render_result(r)
    elif c == "/logs":
        r = ccc_manage("logs"); render_result(r)
    elif c == "/errors":
        r = ccc_manage("logs_error"); render_result(r)
    elif c == "/deploy":
        if Confirm.ask("  배포 (pull + build + restart) 하시겠습니까?", default=True):
            with console.status("[bold]배포 중...", spinner="dots", spinner_style=O):
                r = ccc_manage("deploy")
            render_result(r)
    elif c == "/build":
        with console.status("[bold]UI 빌드 중...", spinner="dots", spinner_style=O):
            r = ccc_manage("build_ui")
        render_result(r)
    elif c == "/env":
        r = ccc_manage("env"); render_result(r)

    elif c == "/help":
        render_help()
    elif c == "/skills":
        t = Table(box=box.ROUNDED, border_style=G, title="Tools", title_style=O)
        t.add_column("도구", style=P, width=14); t.add_column("설명", style="white")
        for td in TOOL_DEFS:
            fn = td["function"]
            t.add_row(fn["name"], fn["description"][:80])
        console.print(t)
    elif c == "/clear":
        console.clear(); render_banner()

    elif c == "/status":
        if not session.infras:
            console.print("  인프라 없음. /infras add", style=G)
        else:
            with console.status("[bold]확인 중...", spinner="dots", spinner_style=O):
                r = system_status(session.infras)
            console.print(f"\n  전체: {r['total']}  [{GR}]정상: {r['healthy']}[/]  [{R}]불가: {r['unreachable']}[/]")
    elif c == "/health":
        if len(parts) < 2: console.print("  /health <IP>", style=G)
        else:
            r = health_check(parts[1])
            color = GR if r.get("status") == "healthy" else R
            console.print(f"  [{color}]{parts[1]}: {r.get('status','?')}[/]")
    elif c == "/onboard":
        ip = parts[1] if len(parts) > 1 else Prompt.ask("  IP")
        role = Prompt.ask("  역할", choices=["attacker","secu","web","siem","manager","windows"])
        pw = Prompt.ask("  SSH 비밀번호", password=True, default="1")
        with console.status(f"[bold]{ip} 온보딩 중...", spinner="dots", spinner_style=O):
            r = onboard_vm(ip=ip, role=role, password=pw)
        render_result(r)
        if r.get("healthy"):
            session.infras.append({"ip": ip, "role": role, "status": "healthy"})
    elif c == "/run":
        if len(parts) < 3: console.print("  /run <IP> <CMD>", style=G)
        else:
            with console.status("[bold]실행 중...", spinner="dots", spinner_style=O):
                r = run_command(parts[1], parts[2])
            render_result(r)
    elif c == "/infras":
        if len(parts) > 1 and parts[1] == "add":
            ip = Prompt.ask("  IP"); role = Prompt.ask("  역할", choices=["attacker","secu","web","siem","manager","windows"])
            session.infras.append({"ip": ip, "role": role, "status": "registered"})
            console.print(f"  [{GR}]추가: {role} @ {ip}[/]")
        elif not session.infras:
            console.print("  인프라 없음. /infras add", style=G)
        else:
            for inf in session.infras:
                color = GR if inf.get("status") == "healthy" else G
                console.print(f"  [{color}]{inf.get('role','?'):12s} {inf.get('ip','?')}  {inf.get('status','')}[/]")
    elif c == "/history":
        for m in session.history[-20:]:
            color = O if m["role"] == "user" else B
            console.print(f"  [{color}]{m['role']}[/]: {m['content'][:100]}")

    # 세션 관리
    elif c == "/save":
        session.save()
        console.print(f"  [{GR}]세션 저장됨: {session.id}[/]")
    elif c == "/sessions":
        for s in Session.list_sessions():
            console.print(f"  {s['id']}  ({s['turns']} turns, {s['tasks']} tasks)")
    elif c == "/load":
        sid = parts[1] if len(parts) > 1 else Prompt.ask("  세션 ID")
        return sid  # special return: switch session

    else:
        console.print(f"  알 수 없는 명령. /help 참고", style=G)
    return True


# ══════════════════════════════════════════════════
#  9. Main REPL
# ══════════════════════════════════════════════════
def load_infras(session: Session):
    api_url = os.getenv("CCC_API_URL", "http://localhost:9100")
    api_key = os.getenv("CCC_API_KEY", "ccc-api-key-2026")
    try:
        r = httpx.get(f"{api_url}/api/infras/my", headers={"X-API-Key": api_key}, timeout=5.0)
        if r.status_code == 200:
            for inf in r.json().get("infras", []):
                cfg = inf.get("vm_config", {}) or {}
                session.infras.append({"ip": inf.get("ip",""), "role": cfg.get("role",""), "status": inf.get("status","")})
            if session.infras:
                console.print(f"  [dim]인프라 {len(session.infras)}대 로드[/]")
    except Exception:
        pass

def main():
    # .env
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    render_banner()

    # LLM 체크
    with console.status("[bold]LLM 연결 확인...", spinner="dots", spinner_style=O):
        try:
            r = httpx.get(f"{LLM_BASE_URL}/api/tags", timeout=5.0)
            models = [m["name"] for m in r.json().get("models", [])]
            console.print(f"  [dim]모델: {', '.join(models[:5]) if models else '없음'}[/]")
        except Exception:
            console.print(f"  [{R}]LLM 연결 실패: {LLM_BASE_URL}[/]")

    # 세션 (이전 세션 이어받기 또는 새 세션)
    sessions = Session.list_sessions()
    session = Session()
    if sessions and len(sys.argv) <= 1:
        latest = sessions[0]
        if latest["turns"] > 0:
            console.print(f"  [dim]이전 세션: {latest['id']} ({latest['turns']} turns)[/]")
            if Confirm.ask("  이전 세션을 이어서 하시겠습니까?", default=False):
                session = Session.load(latest["id"])
                console.print(f"  [{GR}]세션 복원: {session.id}[/]")

    # CLI에서 세션 ID 지정
    if len(sys.argv) > 1:
        session = Session.load(sys.argv[1])
        console.print(f"  [{GR}]세션 로드: {session.id}[/]")

    load_infras(session)
    console.print(f"  [dim]세션: {session.id} | /help 도움말 | 자연어로 작업 지시[/]\n")

    # REPL
    while True:
        try:
            console.print(f"[bold {O}]bastion >[/] ", end="")
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            session.save()
            console.print(f"\n  [dim]세션 저장: {session.id}[/]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            result = handle_slash(user_input, session)
            if result is False:
                break
            elif isinstance(result, str):
                # /load 로 세션 전환
                session = Session.load(result)
                console.print(f"  [{GR}]세션 전환: {session.id}[/]")
            console.print()
            continue

        if user_input.startswith("!"):
            cmd = user_input[1:].strip()
            if cmd:
                if check_permission("shell", {"command": cmd}):
                    render_tool_call("shell", {"command": cmd})
                    r = shell_exec(cmd)
                    render_result(r)
            console.print()
            continue

        try:
            execute_interactive(user_input, session)
        except KeyboardInterrupt:
            console.print(f"\n  [dim]취소됨[/]")
        except Exception as e:
            console.print(f"  [{R}]{e}[/]")
        console.print()

if __name__ == "__main__":
    main()
