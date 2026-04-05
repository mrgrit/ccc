#!/usr/bin/env python3
"""bastion — CCC 운영 관리 에이전트 (대화형 TUI)

Claude Code의 대화형 TUI를 참고한 인터랙티브 에이전트.
자연어로 인프라 관리 작업을 지시하면 LLM이 스킬을 선택/실행한다.

Usage:
    python -m apps.bastion.main
    ./dev.sh bastion
"""
from __future__ import annotations
import os
import sys
import json
import time
import signal
import textwrap
from typing import Any

# ── 의존성 체크 ──
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.prompt import Prompt
    from rich import box
except ImportError:
    print("rich 라이브러리가 필요합니다: pip install rich")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("httpx 라이브러리가 필요합니다: pip install httpx")
    sys.exit(1)

# CCC 패키지
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from packages.bastion import (
    LLM_BASE_URL, LLM_MODEL, SKILLS, PROMPT_SECTIONS,
    build_system_prompt, dispatch_skill, health_check,
    onboard_vm, run_command, system_status, diagnose_vm,
    shell_exec, ccc_manage,
)

# ── Console Setup ─────────────────────────────────
console = Console()
ORANGE = "orange3"
GRAY = "bright_black"
GREEN = "green"
RED = "red"
BLUE = "dodger_blue2"
PURPLE = "medium_purple"

# ── State ─────────────────────────────────────────
MAX_CONTEXT_CHARS = 8000  # LLM에 보낼 히스토리 최대 크기
MAX_MSG_CHARS = 600       # 개별 메시지 최대 길이

class BastionState:
    """세션 상태 — bastion/src/state/AppStateStore.ts 참고

    컨텍스트 관리 전략 (bastion의 REACTIVE_COMPACT 참고):
    1. 최근 대화를 우선 유지 (recency bias)
    2. 오래된 대화는 요약으로 압축 (compaction)
    3. 총 크기를 MAX_CONTEXT_CHARS 이내로 유지
    """
    def __init__(self):
        self.infras: list[dict] = []
        self.history: list[dict] = []
        self.summary: str = ""  # 오래된 대화 요약
        self.session_start = time.time()
        self.task_count = 0

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content, "ts": time.time()})
        self._compact()

    def _compact(self):
        """히스토리가 너무 길면 오래된 부분을 요약으로 압축"""
        total = sum(len(m["content"]) for m in self.history)
        if total <= MAX_CONTEXT_CHARS:
            return

        # 앞쪽 절반을 요약으로 압축
        mid = len(self.history) // 2
        old_msgs = self.history[:mid]
        self.history = self.history[mid:]

        old_text = "\n".join(
            f"{'사용자' if m['role']=='user' else '에이전트'}: {m['content'][:200]}"
            for m in old_msgs
        )
        if self.summary:
            self.summary += f"\n---\n{old_text[:1000]}"
        else:
            self.summary = old_text[:1000]

        # 요약도 너무 길면 자르기
        if len(self.summary) > 2000:
            self.summary = self.summary[-2000:]

    def build_messages(self) -> list[dict]:
        """LLM에 보낼 대화 히스토리 구성"""
        messages = []

        # 요약이 있으면 첫 메시지로 추가
        if self.summary:
            messages.append({
                "role": "user",
                "content": f"[이전 대화 요약]\n{self.summary}"
            })
            messages.append({
                "role": "assistant",
                "content": "이전 대화 내용을 확인했습니다. 계속하겠습니다."
            })

        # 최근 히스토리
        for msg in self.history:
            content = msg["content"]
            if len(content) > MAX_MSG_CHARS:
                content = content[:MAX_MSG_CHARS] + "...(truncated)"
            messages.append({"role": msg["role"], "content": content})

        return messages

    def get_context(self) -> dict:
        return {
            "infras": self.infras,
            "session_duration": int(time.time() - self.session_start),
            "tasks_completed": self.task_count,
        }

state = BastionState()


# ── UI Components (bastion/src/components 참고) ───

def render_banner():
    """시작 배너 — bastion의 App.tsx 초기 렌더링 참고"""
    banner = Text()
    banner.append("  ____            _   _             \n", style=ORANGE)
    banner.append(" | __ )  __ _ ___| |_(_) ___  _ __  \n", style=ORANGE)
    banner.append(" |  _ \\ / _` / __| __| |/ _ \\| '_ \\ \n", style=ORANGE)
    banner.append(" | |_) | (_| \\__ \\ |_| | (_) | | | |\n", style=ORANGE)
    banner.append(" |____/ \\__,_|___/\\__|_|\\___/|_| |_|\n", style=ORANGE)
    console.print(banner)
    console.print(f"  CCC 운영 관리 에이전트", style=GRAY)
    console.print(f"  LLM: {LLM_BASE_URL} / {LLM_MODEL}", style=GRAY)
    console.print()


def render_skills_table():
    """사용 가능한 스킬 목록 — bastion의 SkillTool 참고"""
    table = Table(box=box.ROUNDED, border_style=GRAY, title="Skills", title_style=ORANGE)
    table.add_column("스킬", style=PURPLE, width=16)
    table.add_column("설명", style="white")
    table.add_column("필요 파라미터", style=GRAY)
    for name, info in SKILLS.items():
        table.add_row(name, info["description"], ", ".join(info["requires"]))
    console.print(table)
    console.print()


def render_help():
    """도움말"""
    console.print(Panel(
        "[bold]사용법[/]\n\n"
        "자연어로 작업을 지시하세요. LLM이 적절한 스킬을 선택하여 실행합니다.\n"
        "예: 'API 서버 시작해줘', '디스크 용량 확인', 'nginx 설치해줘'\n\n"
        "[bold]CCC 관리[/]\n"
        f"  [{ PURPLE }]/start[/]       API + DB 시작\n"
        f"  [{ PURPLE }]/stop[/]        전체 중지\n"
        f"  [{ PURPLE }]/restart[/]     API 재시작\n"
        f"  [{ PURPLE }]/svc[/]         서비스 상태 (프로세스/헬스/리소스/설정)\n"
        f"  [{ PURPLE }]/logs[/]        API 로그 (최근 100줄)\n"
        f"  [{ PURPLE }]/errors[/]      API 에러 로그만\n"
        f"  [{ PURPLE }]/deploy[/]      원클릭 배포 (pull + build + restart)\n"
        f"  [{ PURPLE }]/build[/]       UI 빌드만\n"
        f"  [{ PURPLE }]/env[/]         환경변수 확인\n\n"
        "[bold]로컬 명령[/]\n"
        f"  [{ PURPLE }]![/] <CMD>      로컬 쉘 명령 실행 (예: ! df -h)\n\n"
        "[bold]인프라 관리[/]\n"
        f"  [{ PURPLE }]/status[/]      전체 VM 인프라 상태\n"
        f"  [{ PURPLE }]/health[/] IP   특정 VM 헬스체크\n"
        f"  [{ PURPLE }]/onboard[/]     VM 온보딩\n"
        f"  [{ PURPLE }]/run[/] IP CMD  SubAgent에 원격 명령\n\n"
        "[bold]기타[/]\n"
        f"  [{ PURPLE }]/skills[/]      스킬 목록\n"
        f"  [{ PURPLE }]/infras[/]      등록된 인프라\n"
        f"  [{ PURPLE }]/history[/]     대화 히스토리\n"
        f"  [{ PURPLE }]/clear[/]       화면 지우기\n"
        f"  [{ PURPLE }]/help[/]        이 도움말\n"
        f"  [{ PURPLE }]/exit[/]        종료\n",
        title="Bastion Help", border_style=ORANGE,
    ))


def render_infra_status(infras: list[dict]):
    """인프라 상태 테이블 — bastion의 CoordinatorAgentStatus 참고"""
    if not infras:
        console.print("  등록된 인프라가 없습니다.", style=GRAY)
        return

    table = Table(box=box.ROUNDED, border_style=GRAY)
    table.add_column("역할", style=PURPLE, width=12)
    table.add_column("IP", style="white", width=18)
    table.add_column("상태", width=14)
    table.add_column("호스트명", style=GRAY)

    for infra in infras:
        status = infra.get("status", "unknown")
        if status == "healthy":
            status_text = Text(status, style=GREEN)
        elif status == "unreachable":
            status_text = Text(status, style=RED)
        else:
            status_text = Text(status, style="yellow")
        table.add_row(
            infra.get("role", "?"),
            infra.get("ip", "?"),
            status_text,
            infra.get("hostname", ""),
        )
    console.print(table)


def render_tool_call(skill_name: str, params: dict):
    """스킬 실행 표시 — bastion의 AgentTool/UI.tsx 참고"""
    param_str = " ".join(f"{k}={v}" for k, v in params.items() if k != "infras")
    console.print(f"  ⚡ [bold {ORANGE}]{skill_name}[/] {param_str}", highlight=False)


def render_result(result: dict):
    """실행 결과 표시"""
    if "error" in result:
        console.print(f"  [bold {RED}]Error:[/] {result['error']}")
        return

    if "answer" in result:
        console.print()
        console.print(Markdown(result["answer"]))
        return

    if "diagnosis" in result:
        console.print()
        console.print(Panel(result["diagnosis"], title="진단 결과", border_style=BLUE))
        return

    if "stdout" in result:
        stdout = result.get("stdout", "").strip()
        stderr = result.get("stderr", "").strip()
        code = result.get("exit_code", -1)
        color = GREEN if code == 0 else RED
        if stdout:
            console.print(f"  [dim]stdout:[/]")
            console.print(Syntax(stdout, "bash", theme="monokai", line_numbers=False, padding=1))
        if stderr:
            console.print(f"  [{RED}]stderr:[/] {stderr[:500]}")
        console.print(f"  [dim]exit_code:[/] [{color}]{code}[/]")
        return

    if "healthy" in result:
        h = "✓ healthy" if result["healthy"] else "✗ failed"
        color = GREEN if result["healthy"] else RED
        console.print(f"  [{color}]{h}[/]")
        if "steps" in result:
            for step in result["steps"]:
                s = "✓" if step.get("success") else "✗"
                console.print(f"    {s} {step.get('step', '')}", style=GRAY)
        return

    # generic JSON
    console.print(Syntax(json.dumps(result, ensure_ascii=False, indent=2), "json",
                         theme="monokai", line_numbers=False, padding=1))


# ── LLM Streaming ────────────────────────────────

def llm_chat(messages: list[dict], stream: bool = True) -> str:
    """LLM 호출 — bastion의 services/api/claude.ts 참고"""
    try:
        if stream:
            return _llm_stream(messages)
        else:
            r = httpx.post(f"{LLM_BASE_URL}/api/chat", json={
                "model": LLM_MODEL,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.1},
            }, timeout=60.0)
            return r.json().get("message", {}).get("content", "")
    except Exception as e:
        return f"[LLM 연결 실패: {e}]"


def _llm_stream(messages: list[dict]) -> str:
    """스트리밍 응답 — bastion의 query loop streaming 참고"""
    full_text = ""
    try:
        with httpx.stream("POST", f"{LLM_BASE_URL}/api/chat", json={
            "model": LLM_MODEL,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.1},
        }, timeout=120.0) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        console.print(token, end="", highlight=False)
                        full_text += token
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        console.print()  # newline after stream
    except Exception as e:
        full_text = f"[LLM 연결 실패: {e}]"
        console.print(full_text, style=RED)
    return full_text


# ── Task Execution (대화형) ──────────────────────

def execute_interactive(instruction: str):
    """자연어 지시 실행 — bastion의 query.ts 메인 루프 참고

    1. 사용자 입력 → 시스템 프롬프트 조합
    2. LLM에게 스킬 선택 요청 (JSON)
    3. 스킬 실행 + 결과 표시
    4. 필요시 LLM에게 결과 요약 요청
    """
    state.add_message("user", instruction)
    context = state.get_context()
    skill_list = json.dumps(SKILLS, ensure_ascii=False, indent=2)

    system = build_system_prompt(
        f"등록된 인프라: {json.dumps(context['infras'], ensure_ascii=False)}\n"
        f"세션 경과: {context['session_duration']}초, 완료 작업: {context['tasks_completed']}건"
    )

    # 대화 히스토리 포함 (스마트 컨텍스트 관리)
    messages = [{"role": "system", "content": system}]
    messages.extend(state.build_messages())

    # 현재 지시에 스킬 선택 안내 추가
    messages.append({"role": "user", "content": f"""지시: {instruction}

사용 가능한 스킬:
{skill_list}

스킬 실행이 필요하면 반드시 아래 JSON 형식으로만 응답:
{{"skill": "스킬명", "params": {{...}}, "reason": "선택 이유"}}

스킬 없이 직접 답변 가능하면:
{{"skill": "none", "params": {{}}, "reason": "직접 답변", "answer": "답변 내용"}}"""})

    # LLM 응답 (스킬 선택)
    with console.status("[bold]생각하는 중...", spinner="dots", spinner_style=ORANGE):
        reply = llm_chat(messages, stream=False)

    # JSON 파싱
    import re
    match = re.search(r'\{[\s\S]*\}', reply)
    if not match:
        # JSON이 아니면 직접 답변으로 취급
        console.print()
        console.print(Markdown(reply))
        state.add_message("assistant", reply)
        return

    try:
        plan = json.loads(match.group())
    except json.JSONDecodeError:
        console.print()
        console.print(Markdown(reply))
        state.add_message("assistant", reply)
        return

    skill_name = plan.get("skill", "none")
    reason = plan.get("reason", "")

    if skill_name == "none":
        answer = plan.get("answer", reply)
        console.print()
        console.print(Markdown(answer))
        state.add_message("assistant", answer)
        return

    # 스킬 실행
    console.print(f"\n  [dim]이유:[/] {reason}", highlight=False)
    params = plan.get("params", {})
    render_tool_call(skill_name, params)
    console.print()

    with console.status("[bold]실행 중...", spinner="dots", spinner_style=ORANGE):
        result = dispatch_skill(skill_name, params)

    render_result(result)
    state.task_count += 1

    # 실행 결과를 히스토리에 저장 (LLM이 다음 대화에서 참조)
    result_summary = json.dumps(result, ensure_ascii=False)
    if len(result_summary) > 800:
        result_summary = result_summary[:800] + "...(truncated)"
    state.add_message("assistant", f"[{skill_name}] {reason}\n결과: {result_summary}")

    # 결과 요약 (복잡한 결과일 때)
    if skill_name in ("diagnose", "system_status"):
        console.print()


# ── Slash Commands ────────────────────────────────

def handle_slash(cmd: str) -> bool:
    """슬래시 명령 처리 — bastion의 commands/ 패턴 참고"""
    parts = cmd.strip().split(None, 2)
    command = parts[0].lower()

    if command in ("/exit", "/quit", "/q"):
        console.print("\n  [dim]세션 종료[/]")
        return False

    elif command in ("/start",):
        render_tool_call("ccc", {"action": "start"})
        with console.status("[bold]CCC 시작 중...", spinner="dots", spinner_style=ORANGE):
            result = ccc_manage("start")
        render_result(result)

    elif command in ("/stop",):
        render_tool_call("ccc", {"action": "stop"})
        result = ccc_manage("stop")
        render_result(result)

    elif command in ("/restart",):
        render_tool_call("ccc", {"action": "restart"})
        with console.status("[bold]API 재시작 중...", spinner="dots", spinner_style=ORANGE):
            result = ccc_manage("restart")
        render_result(result)

    elif command in ("/svc", "/service"):
        render_tool_call("ccc", {"action": "status"})
        result = ccc_manage("status")
        render_result(result)

    elif command in ("/logs",):
        result = ccc_manage("logs")
        render_result(result)

    elif command in ("/errors",):
        result = ccc_manage("logs_error")
        render_result(result)

    elif command in ("/deploy",):
        render_tool_call("ccc", {"action": "deploy"})
        with console.status("[bold]배포 중 (pull + build + restart)...", spinner="dots", spinner_style=ORANGE):
            result = ccc_manage("deploy")
        render_result(result)

    elif command in ("/env",):
        result = ccc_manage("env")
        render_result(result)

    elif command in ("/build",):
        render_tool_call("ccc", {"action": "build_ui"})
        with console.status("[bold]UI 빌드 중...", spinner="dots", spinner_style=ORANGE):
            result = ccc_manage("build_ui")
        render_result(result)

    elif command == "/help":
        render_help()

    elif command == "/skills":
        render_skills_table()

    elif command == "/clear":
        console.clear()
        render_banner()

    elif command == "/status":
        if not state.infras:
            console.print("  등록된 인프라가 없습니다. /infras add 로 추가하세요.", style=GRAY)
        else:
            with console.status("[bold]상태 확인 중...", spinner="dots", spinner_style=ORANGE):
                result = system_status(state.infras)
            console.print(f"\n  전체: {result['total']}  [{ GREEN }]정상: {result['healthy']}[/]  [{ RED }]불가: {result['unreachable']}[/]\n")
            render_infra_status(result["details"])

    elif command == "/health":
        if len(parts) < 2:
            console.print("  사용법: /health <IP>", style=GRAY)
        else:
            ip = parts[1]
            with console.status(f"[bold]{ip} 확인 중...", spinner="dots", spinner_style=ORANGE):
                result = health_check(ip)
            status = result.get("status", "unknown")
            color = GREEN if status == "healthy" else RED
            console.print(f"  [{color}]{ip}: {status}[/]")
            if result.get("hostname"):
                console.print(f"  [dim]hostname: {result['hostname']}[/]")

    elif command == "/onboard":
        ip = parts[1] if len(parts) > 1 else Prompt.ask("  VM IP")
        role = parts[2] if len(parts) > 2 else Prompt.ask("  역할", choices=["attacker", "secu", "web", "siem", "manager", "windows"])
        user = Prompt.ask("  SSH 사용자", default="ccc")
        password = Prompt.ask("  SSH 비밀번호", password=True, default="1")
        console.print(f"\n  온보딩 시작: {ip} ({role})")
        with console.status(f"[bold]{ip} SubAgent 설치 중...", spinner="dots", spinner_style=ORANGE):
            result = onboard_vm(ip=ip, role=role, user=user, password=password)
        render_result(result)
        if result.get("healthy"):
            state.infras.append({"ip": ip, "role": role, "status": "healthy"})
            console.print(f"  [{ GREEN }]인프라 목록에 추가됨[/]")

    elif command == "/run":
        if len(parts) < 3:
            console.print("  사용법: /run <IP> <명령어>", style=GRAY)
        else:
            ip, script = parts[1], parts[2]
            render_tool_call("run_command", {"ip": ip, "script": script})
            with console.status(f"[bold]실행 중...", spinner="dots", spinner_style=ORANGE):
                result = run_command(ip, script)
            render_result(result)

    elif command == "/infras":
        if len(parts) > 1 and parts[1] == "add":
            ip = Prompt.ask("  IP")
            role = Prompt.ask("  역할", choices=["attacker", "secu", "web", "siem", "manager", "windows"])
            state.infras.append({"ip": ip, "role": role, "status": "registered"})
            console.print(f"  [{ GREEN }]추가됨: {role} @ {ip}[/]")
        else:
            if not state.infras:
                console.print("  등록된 인프라 없음. /infras add 로 추가", style=GRAY)
            else:
                render_infra_status(state.infras)

    elif command == "/history":
        for msg in state.history[-20:]:
            role_color = ORANGE if msg["role"] == "user" else BLUE
            console.print(f"  [{role_color}]{msg['role']}[/]: {msg['content'][:100]}")

    else:
        console.print(f"  알 수 없는 명령: {command}. /help 참고", style=GRAY)

    return True


# ── Main REPL (bastion/src/query.ts 메인 루프 참고) ──

def load_infras_from_api():
    """CCC API에서 인프라 목록 로드"""
    api_url = os.getenv("CCC_API_URL", "http://localhost:9100")
    api_key = os.getenv("CCC_API_KEY", "ccc-api-key-2026")
    try:
        r = httpx.get(f"{api_url}/api/infras/my", headers={"X-API-Key": api_key}, timeout=5.0)
        if r.status_code == 200:
            infras = r.json().get("infras", [])
            for inf in infras:
                cfg = inf.get("vm_config", {}) or {}
                state.infras.append({
                    "ip": inf.get("ip", ""),
                    "role": cfg.get("role", ""),
                    "status": inf.get("status", "registered"),
                })
            if state.infras:
                console.print(f"  [dim]API에서 인프라 {len(state.infras)}대 로드됨[/]")
    except Exception:
        pass  # API 연결 실패 시 무시


def main():
    """메인 REPL — Claude Code의 대화 루프 참고"""
    # .env 로드
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    render_banner()

    # LLM 연결 확인
    with console.status("[bold]LLM 연결 확인...", spinner="dots", spinner_style=ORANGE):
        try:
            r = httpx.get(f"{LLM_BASE_URL}/api/tags", timeout=5.0)
            models = [m["name"] for m in r.json().get("models", [])]
            if models:
                console.print(f"  [dim]사용 가능 모델: {', '.join(models[:5])}[/]")
            else:
                console.print(f"  [yellow]모델 없음 — ollama pull {LLM_MODEL} 실행 필요[/]")
        except Exception:
            console.print(f"  [{RED}]LLM 서버 연결 실패: {LLM_BASE_URL}[/]")
            console.print(f"  [dim]Ollama 서버를 시작하거나 .env의 LLM_BASE_URL을 확인하세요[/]")

    # API에서 인프라 로드
    load_infras_from_api()

    console.print(f"  [dim]/help 로 도움말 확인. 자연어로 작업을 지시하세요.[/]\n")

    # REPL
    while True:
        try:
            console.print(f"[bold {ORANGE}]bastion >[/] ", end="")
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            console.print(f"\n  [dim]세션 종료[/]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            if not handle_slash(user_input):
                break
            console.print()
            continue

        # ! 접두사: 로컬 쉘 직접 실행
        if user_input.startswith("!"):
            cmd = user_input[1:].strip()
            if cmd:
                render_tool_call("shell", {"command": cmd})
                result = shell_exec(cmd)
                render_result(result)
            console.print()
            continue

        # 자연어 지시 실행
        try:
            execute_interactive(user_input)
        except KeyboardInterrupt:
            console.print(f"\n  [dim]작업 취소됨[/]")
        except Exception as e:
            console.print(f"  [{RED}]Error: {e}[/]")

        console.print()


if __name__ == "__main__":
    main()
