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
import signal
import threading
import subprocess
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
MEMORY_DIR = CCC_HOME / "memory"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# ── Interrupt (AbortController 패턴) ─────────────
_interrupted = threading.Event()

def _sigint_handler(sig, frame):
    if _interrupted.is_set():
        console.print(f"\n  [{R}]강제 종료[/]")
        sys.exit(1)
    _interrupted.set()
    console.print(f"\n  [yellow]⚠ 중단 요청 (한번 더 누르면 강제 종료)[/]")

signal.signal(signal.SIGINT, _sigint_handler)


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
#  4. Git 도구
# ══════════════════════════════════════════════════
def git_exec(subcmd: str) -> dict:
    return shell_exec(f"cd {CCC_DIR} && git {subcmd}", timeout=30)

def git_status() -> dict:
    return git_exec("status -sb")

def git_diff(target: str = "") -> dict:
    return git_exec(f"diff {target}")

def git_log(count: int = 10) -> dict:
    return git_exec(f"log --oneline -{count}")

def git_commit(message: str) -> dict:
    return git_exec(f'add -A && git commit -m "{message}"')

def git_push(remote: str = "origin", branch: str = "") -> dict:
    b = branch or "$(git branch --show-current)"
    return git_exec(f"push {remote} {b}")


# ══════════════════════════════════════════════════
#  5. 메모리 시스템 (.ccc/memory/)
# ══════════════════════════════════════════════════
def memory_save(name: str, content: str, mem_type: str = "project") -> dict:
    """메모리 저장 — YAML frontmatter + markdown"""
    safe = re.sub(r'[^\w\-]', '_', name)[:60]
    fpath = MEMORY_DIR / f"{safe}.md"
    desc = content.split("\n")[0][:100]
    md = f"---\nname: {name}\ndescription: {desc}\ntype: {mem_type}\n---\n\n{content}\n"
    fpath.write_text(md, encoding="utf-8")
    # MEMORY.md 인덱스 업데이트
    idx = MEMORY_DIR / "MEMORY.md"
    entry = f"- [{name}]({safe}.md) — {desc}"
    existing = idx.read_text(encoding="utf-8") if idx.exists() else ""
    if safe not in existing:
        idx.write_text(existing.rstrip() + "\n" + entry + "\n", encoding="utf-8")
    return {"status": "saved", "path": str(fpath), "name": name}

def memory_search(query: str) -> dict:
    """메모리 검색"""
    results = []
    for f in MEMORY_DIR.glob("*.md"):
        if f.name == "MEMORY.md":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if query.lower() in text.lower():
            # frontmatter 파싱
            lines = text.split("\n")
            name = desc = mtype = ""
            for l in lines[:6]:
                if l.startswith("name:"): name = l.split(":", 1)[1].strip()
                if l.startswith("description:"): desc = l.split(":", 1)[1].strip()
                if l.startswith("type:"): mtype = l.split(":", 1)[1].strip()
            results.append({"name": name, "type": mtype, "desc": desc, "file": f.name})
    return {"query": query, "count": len(results), "results": results}

def memory_list() -> dict:
    """메모리 목록"""
    idx = MEMORY_DIR / "MEMORY.md"
    if idx.exists():
        return {"content": idx.read_text(encoding="utf-8")}
    return {"content": "(비어있음)"}

def memory_load_context() -> str:
    """시스템 프롬프트에 포함할 메모리 컨텍스트"""
    idx = MEMORY_DIR / "MEMORY.md"
    if not idx.exists():
        return ""
    content = idx.read_text(encoding="utf-8").strip()
    if not content:
        return ""
    return f"\n\n[기억된 정보]\n{content[:1500]}"


# ══════════════════════════════════════════════════
#  6. 플랜 모드
# ══════════════════════════════════════════════════
class PlanMode:
    """복잡한 작업 → 계획 수립 → 승인 → 실행"""
    def __init__(self):
        self.active = False
        self.plan: list[dict] = []
        self.current_step = 0

    def enter(self, steps: list[dict]):
        self.active = True
        self.plan = steps
        self.current_step = 0

    def exit(self):
        self.active = False
        self.plan = []
        self.current_step = 0

    def next_step(self) -> dict | None:
        if self.current_step >= len(self.plan):
            return None
        step = self.plan[self.current_step]
        self.current_step += 1
        return step

    def render(self):
        console.print(Panel(
            "\n".join(
                f"  [{'green' if i < self.current_step else 'yellow' if i == self.current_step else 'dim'}]"
                f"{'✓' if i < self.current_step else '→' if i == self.current_step else '○'} "
                f"Step {i+1}: {s.get('description', '')}[/]"
                for i, s in enumerate(self.plan)
            ),
            title=f"Plan ({self.current_step}/{len(self.plan)})", border_style=O,
        ))

plan_mode = PlanMode()


# ══════════════════════════════════════════════════
#  7. 에이전트 분기 (서브에이전트)
# ══════════════════════════════════════════════════
def spawn_agent(task: str, timeout: int = 120) -> dict:
    """서브에이전트 — 별도 스레드에서 LLM + 도구 실행"""
    result_holder = {"status": "running", "output": ""}

    def _run():
        try:
            r = httpx.post(f"{LLM_BASE_URL}/api/chat", json={
                "model": LLM_MODEL, "tools": TOOL_DEFS, "stream": False,
                "messages": [
                    {"role": "system", "content": build_system_prompt(f"CCC 경로: {CCC_DIR}")},
                    {"role": "user", "content": task},
                ],
                "options": {"temperature": 0.1},
            }, timeout=float(timeout))
            msg = r.json().get("message", {})
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            outputs = [content] if content else []
            for tc in tool_calls:
                fn = tc.get("function", {})
                name, params = fn.get("name", ""), fn.get("arguments", {})
                if isinstance(params, str):
                    try: params = json.loads(params)
                    except: params = {}
                res = dispatch_tool(name, params)
                outputs.append(f"[{name}] {json.dumps(res, ensure_ascii=False)[:500]}")

            result_holder["output"] = "\n".join(outputs)
            result_holder["status"] = "done"
        except Exception as e:
            result_holder["output"] = str(e)
            result_holder["status"] = "error"

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        result_holder["status"] = "timeout"
    return result_holder


# ══════════════════════════════════════════════════
#  8. Tool Definitions (Ollama function calling)
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
    # git
    {"type": "function", "function": {
        "name": "git",
        "description": "Git 작업: status, diff, log, commit, push, pull, branch, checkout",
        "parameters": {"type": "object", "properties": {
            "subcmd": {"type": "string", "description": "git 서브커맨드 (예: status -sb, log --oneline -5, commit -m 'msg', push origin main)"},
        }, "required": ["subcmd"]},
    }},
    # memory
    {"type": "function", "function": {
        "name": "memory_save",
        "description": "정보를 영구 메모리에 저장 (.ccc/memory/). 세션 간 기억 유지. type: user/feedback/project/reference",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "메모리 이름"},
            "content": {"type": "string", "description": "저장할 내용"},
            "type": {"type": "string", "enum": ["user","feedback","project","reference"]},
        }, "required": ["name", "content"]},
    }},
    {"type": "function", "function": {
        "name": "memory_search",
        "description": "영구 메모리에서 검색",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
        }, "required": ["query"]},
    }},
    # plan
    {"type": "function", "function": {
        "name": "plan",
        "description": "복잡한 작업을 단계별 계획으로 분해. action: create(계획수립), show(현재계획), next(다음단계실행), cancel(취소)",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["create","show","next","cancel"]},
            "steps": {"type": "string", "description": "JSON 배열: [{\"description\":\"설명\",\"tool\":\"도구명\",\"params\":{}}]"},
        }, "required": ["action"]},
    }},
    # agent
    {"type": "function", "function": {
        "name": "agent",
        "description": "서브에이전트 생성 — 독립 작업을 백그라운드에서 병렬 실행. 복잡한 작업을 분할할 때 사용",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string", "description": "서브에이전트에게 맡길 작업 설명"},
            "timeout": {"type": "integer", "description": "타임아웃 (초, 기본 120)"},
        }, "required": ["task"]},
    }},
]


# ══════════════════════════════════════════════════
#  5. 도구 디스패치 (권한 확인 포함)
# ══════════════════════════════════════════════════
def dispatch_tool(name: str, params: dict) -> dict:
    """도구 실행 — 권한 확인 후 디스패치"""
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
    elif name == "git":
        return git_exec(params.get("subcmd", "status"))
    elif name == "memory_save":
        return memory_save(params["name"], params["content"], params.get("type", "project"))
    elif name == "memory_search":
        return memory_search(params["query"])
    elif name == "plan":
        return _handle_plan(params)
    elif name == "agent":
        return spawn_agent(params["task"], params.get("timeout", 120))
    else:
        return dispatch_skill(name, params)

def _handle_plan(params: dict) -> dict:
    action = params.get("action", "show")
    if action == "create":
        try:
            steps = json.loads(params.get("steps", "[]"))
        except: steps = []
        if not steps:
            return {"error": "steps 파라미터 필요 (JSON 배열)"}
        plan_mode.enter(steps)
        plan_mode.render()
        return {"status": "plan_created", "steps": len(steps)}
    elif action == "show":
        if not plan_mode.active:
            return {"status": "no_plan"}
        plan_mode.render()
        return {"status": "showing", "step": plan_mode.current_step, "total": len(plan_mode.plan)}
    elif action == "next":
        step = plan_mode.next_step()
        if not step:
            plan_mode.exit()
            return {"status": "plan_complete"}
        plan_mode.render()
        # 단계에 도구가 지정되어 있으면 실행
        tool = step.get("tool")
        if tool:
            result = dispatch_tool(tool, step.get("params", {}))
            return {"status": "step_executed", "step": step["description"], "result": result}
        return {"status": "step_ready", "step": step["description"]}
    elif action == "cancel":
        plan_mode.exit()
        return {"status": "cancelled"}
    return {"error": f"Unknown plan action: {action}"}


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
        f"[bold]인프라[/]                  [bold]세션/메모리[/]\n"
        f"  [{P}]/status[/] /health /onboard /run   [{P}]/save[/] /load /sessions /memory\n\n"
        f"[bold]기타[/]                    Ctrl+C: 스트리밍 중단\n"
        f"  [{P}]/skills[/] /infras /history /plan /clear /help /exit[/]\n",
        title="Bastion Help", border_style=O))


# ══════════════════════════════════════════════════
#  7. 스트리밍 Tool Calling Loop (Claude Code query.ts)
# ══════════════════════════════════════════════════
def execute_interactive(instruction: str, session: Session):
    """Claude Code 스타일 대화 루프 — 스트리밍 + tool calling"""
    session.add("user", instruction)
    ctx = session.context()

    mem_ctx = memory_load_context()
    system = build_system_prompt(
        f"등록된 인프라: {json.dumps(ctx['infras'], ensure_ascii=False)}\n"
        f"세션: {ctx['duration']}초, 완료: {ctx['tasks']}건\n"
        f"CCC 경로: {CCC_DIR}{mem_ctx}"
    )

    messages = [{"role": "system", "content": system}]
    messages.extend(session.build_messages())
    messages.append({"role": "user", "content": instruction})

    full_response = ""
    _interrupted.clear()

    for iteration in range(5):  # max 5 tool call rounds
        if _interrupted.is_set():
            console.print(f"  [yellow]⚠ 중단됨 (응답 일부 보존)[/]")
            break
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

                    # Ctrl+C 체크
                    if _interrupted.is_set():
                        break

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

            # 실행 + 자동 에러 복구 (1회 재시도)
            with console.status("[bold]실행 중...", spinner="dots", spinner_style=O):
                result = dispatch_tool(name, params)
                # 연결 에러 시 1회 재시도
                if result.get("exit_code", 0) != 0 and "Connection refused" in result.get("stderr", ""):
                    console.print(f"  [yellow]↻ 재시도...[/]")
                    time.sleep(2)
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

    elif c == "/memory":
        r = memory_list(); render_result(r)
    elif c == "/plan":
        if plan_mode.active:
            plan_mode.render()
        else:
            console.print("  플랜 없음. 자연어로 '계획 세워줘' 지시", style=G)

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
        _interrupted.clear()
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
