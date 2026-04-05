# Week 07: 클라이언트 사이드 하네스 활용 — Claude Code

## 학습 목표
- Claude Code의 설치와 기본 설정을 완료할 수 있다
- CLAUDE.md를 작성하여 프로젝트 컨텍스트를 정의할 수 있다
- MCP 서버를 연동하여 외부 도구를 확장할 수 있다
- Hooks를 설정하여 자동화된 사전/사후 처리를 구현할 수 있다
- OpsClaw를 Claude Code에서 호출하는 하이브리드 구성을 구축한다

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
| 0:00-0:25 | 이론: Claude Code 아키텍처 (Part 1) | 강의 |
| 0:25-0:50 | 이론: CLAUDE.md, MCP, Hooks 개념 (Part 2) | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:45 | 실습: Claude Code 설치와 CLAUDE.md 작성 (Part 3) | 실습 |
| 1:45-2:30 | 실습: MCP 서버 연동과 Hooks 설정 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:15 | 실습: 하이브리드 구성 — Claude Code + OpsClaw (Part 5) | 실습 |
| 3:15-3:30 | 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **Claude Code** | Claude Code | Anthropic의 공식 AI 코딩 에이전트 CLI | AI 개발 비서 |
| **CLAUDE.md** | CLAUDE.md | 프로젝트별 AI 에이전트 규칙/컨텍스트 파일 | 프로젝트 헌법 |
| **MCP** | Model Context Protocol | LLM에 외부 도구/데이터를 연결하는 프로토콜 | USB 허브 |
| **MCP 서버** | MCP Server | MCP 프로토콜로 도구를 제공하는 서비스 | USB 장치 |
| **MCP 클라이언트** | MCP Client | MCP 서버에 접속하여 도구를 사용하는 주체 | USB 포트 |
| **Hook** | Hook | 특정 이벤트 전후에 자동 실행되는 코드 | 문 앞 센서 알람 |
| **PreToolUse** | PreToolUse | 도구 실행 전에 실행되는 Hook | 출발 전 안전 점검 |
| **PostToolUse** | PostToolUse | 도구 실행 후에 실행되는 Hook | 귀환 후 보고 |
| **settings.json** | settings.json | Claude Code 설정 파일 | 시스템 설정 |
| **에이전트 모드** | Agent Mode | Claude Code가 자율적으로 작업하는 모드 | 자율 비서 모드 |
| **슬래시 명령** | Slash Command | /로 시작하는 Claude Code 명령 | 단축 명령 |
| **컨텍스트** | Context | AI에게 제공되는 배경 정보 | 업무 브리핑 자료 |
| **하이브리드** | Hybrid | Client+Server 하네스를 결합한 구성 | 자율+원격 조종 결합 |
| **오케스트레이션** | Orchestration | 여러 도구/서비스를 조율하여 실행 | 지휘자의 지휘 |
| **stdin/stdout** | Standard I/O | MCP 서버 통신에 사용하는 표준 입출력 | 대화 채널 |
| **JSON-RPC** | JSON-RPC | MCP 통신에 사용하는 원격 호출 프로토콜 | 택배 송장 표준 |

---

## Part 1: Claude Code 아키텍처 (25분) — 이론

### 1.1 Claude Code란?

Claude Code는 Anthropic이 만든 **AI 코딩 에이전트 CLI**이다. 터미널에서 실행하며, Claude LLM이 파일 읽기, 코드 작성, 명령 실행 등을 수행한다.

```
  Claude Code 아키텍처
  사용자 (터미널)
  ↓
  Claude Code CLI
  ↓
  |  Claude LLM (Anthropic API)  |
  |  - 대화 이해  |
  |  - 계획 수립  |
  |  - 도구 선택  |
  ↓
  |  내장 도구 (Tools)  |
  |  Bash, Read, Write, Edit, Grep, ...  |
  ↓
  |  확장 도구  |
  |  MCP 서버, Hooks, 슬래시 명령  |
  설정: CLAUDE.md + .claude/settings.json
```

### 1.2 핵심 구성요소

| 구성요소 | 파일/위치 | 역할 |
|---------|----------|------|
| **CLAUDE.md** | 프로젝트 루트 | 프로젝트 규칙, API 가이드, 안전 규칙 |
| **settings.json** | `.claude/settings.json` | 도구 허용/차단, Hooks, MCP 서버 |
| **MEMORY.md** | `.claude/projects/.../MEMORY.md` | 자동 기억 (세션 간 유지) |
| **MCP 서버** | settings.json에 등록 | 외부 도구 확장 |
| **Hooks** | settings.json에 정의 | 이벤트 전후 자동 실행 |

### 1.3 Claude Code vs OpsClaw

| 특성 | Claude Code | OpsClaw |
|------|-------------|---------|
| 실행 위치 | 로컬 터미널 | 원격 서버 |
| LLM | Claude (Anthropic) | Ollama (로컬 LLM) |
| 제어 방식 | 대화형 | API 기반 |
| 다중 서버 | SSH/MCP | SubAgent |
| 증적 | MEMORY.md | PoW + Evidence |
| 비용 | API 사용량 과금 | 로컬 LLM 무료 |

---

## Part 2: CLAUDE.md, MCP, Hooks 개념 (25분) — 이론

### 2.1 CLAUDE.md의 구조

```markdown
# 프로젝트명 — Claude Code 가이드

## 역할
당신은 보안 관리자 AI이다.

## 인프라 정보
| 서버 | IP | 역할 |
|------|-----|------|
| ...  | ... | ...  |

## 규칙
- 파괴적 명령 금지
- 변경 전 반드시 백업

## API 가이드
curl -X POST http://localhost:8000/...

## 도구/스킬
- run_command: 명령 실행
- fetch_log: 로그 수집
```

### 2.2 MCP 프로토콜

```
JSON-RPC
  Claude Code | ← → | MCP Server
  (Client)  |  stdin/stdout  | (도구 제공)

MCP Server가 제공하는 것:
- Tools: 외부 기능 (DB 쿼리, API 호출 등)
- Resources: 데이터 소스 (파일, DB 레코드)
- Prompts: 재사용 가능한 프롬프트 템플릿
```

### 2.3 Hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '[LOG] Command about to run' >> /tmp/claude_audit.log"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '[LOG] Command completed' >> /tmp/claude_audit.log"
          }
        ]
      }
    ]
  }
}
```

---

## Part 3: Claude Code 설치와 CLAUDE.md 작성 (45분) — 실습

### 3.1 Claude Code 설치

> **실습 목적**: 에이전트가 RAG로 보안 지식을 검색하여 정확한 보안 판단을 내리도록 구현하기 위해 수행한다
>
> **배우는 것**: 보안 문서/CVE 데이터를 벡터 DB에 저장하고, 에이전트가 질의 시 관련 정보를 검색하여 판단에 활용하는 구조를 이해한다
>
> **결과 해석**: RAG 적용 전후 보안 분석의 구체성(CVE 번호, 대응 절차 포함 여부)으로 품질 향상을 판단한다
>
> **실전 활용**: 조직 보안 정책 기반 자동 판단, 과거 인시던트 유사 사례 검색, 보안 지식 관리 시스템 구축에 활용한다

```bash
# Node.js 확인 (Claude Code 요구사항)
node --version 2>/dev/null || echo "Node.js 미설치"

# Node.js 설치 (없는 경우)
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt-get install -y nodejs

# Claude Code 설치 (npm)
npm install -g @anthropic-ai/claude-code 2>/dev/null || \
  echo "Claude Code 설치 실패 — npm 또는 네트워크 확인 필요"

# 설치 확인
claude --version 2>/dev/null || echo "Claude Code CLI를 찾을 수 없음"
```

### 3.2 보안 프로젝트용 CLAUDE.md 작성

```bash
mkdir -p ~/lab/week07/security-project

cat > ~/lab/week07/security-project/CLAUDE.md << 'MDEOF'
# 보안 점검 프로젝트 — Claude Code 가이드

> AI 에이전트 필독: 이 파일은 프로젝트 규칙을 정의한다. 모든 작업에 이 규칙을 따르라.

## 역할
당신은 IT 보안 관리자 AI이다. 다음 인프라의 보안 상태를 점검하고 관리한다.

## 인프라 구성

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane | ssh opsclaw@10.20.30.201 |
| secu | 10.20.30.1 | 방화벽/IPS | sshpass -p1 ssh secu@10.20.30.1 |
| web | 10.20.30.80 | 웹서버 | sshpass -p1 ssh web@10.20.30.80 |
| siem | 10.20.30.100 | SIEM | sshpass -p1 ssh siem@10.20.30.100 |

## OpsClaw API

모든 API 호출에 인증 헤더 필수:
```
-H "X-API-Key: opsclaw-api-key-2026"
```

### 주요 API
- 프로젝트 생성: `POST http://localhost:8000/projects`
- 실행: `POST http://localhost:8000/projects/{id}/execute-plan`
- 결과: `GET http://localhost:8000/projects/{id}/evidence/summary`

## 안전 규칙 (필수 준수)

1. **파괴적 명령 금지**: rm -rf, mkfs, dd, DROP TABLE, shutdown 등은 사용자 명시적 승인 없이 실행하지 마라
2. **변경 전 백업**: 설정 파일 수정 시 반드시 .bak 백업을 먼저 생성하라
3. **내부 IP 보호**: 10.x.x.x, 192.168.x.x 대역 IP는 차단 대상에서 제외하라
4. **증적 기록**: 모든 점검 결과를 OpsClaw evidence에 기록하라
5. **최소 권한**: 필요한 최소 권한으로만 명령을 실행하라

## 작업 절차

1. 현재 상태 확인 (read-only 명령만)
2. 문제 분석 및 계획 수립
3. 사용자에게 계획 보고
4. 승인 후 실행
5. 결과 검증 및 보고

## 보고서 형식

```json
{
  "server": "서버명",
  "check_items": ["항목1", "항목2"],
  "status": "정상|주의|위험",
  "findings": ["발견사항"],
  "recommendations": ["권고사항"]
}
```
MDEOF

echo "CLAUDE.md 작성 완료: ~/lab/week07/security-project/CLAUDE.md"
# CLAUDE.md 내용 확인
wc -l ~/lab/week07/security-project/CLAUDE.md
```

### 3.3 CLAUDE.md 효과 테스트

```bash
cat > ~/lab/week07/test_claudemd.py << 'PYEOF'
"""
Week 07 실습: CLAUDE.md 효과 테스트
CLAUDE.md가 있을 때와 없을 때 LLM 응답을 비교한다.
(Claude Code 대신 Ollama로 시뮬레이션)
"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

# CLAUDE.md 읽기
with open("/root/lab/week07/security-project/CLAUDE.md") as f:
    claudemd = f.read()

QUESTION = "secu 서버의 방화벽 상태를 확인하고 싶어"

# 테스트 1: CLAUDE.md 없이
resp1 = requests.post(OLLAMA_URL, json={
    "model": MODEL,
    "messages": [
        {"role": "user", "content": QUESTION}
    ],
    "temperature": 0.2,
}, timeout=120)
answer1 = resp1.json()["choices"][0]["message"]["content"]

# 테스트 2: CLAUDE.md 포함
resp2 = requests.post(OLLAMA_URL, json={
    "model": MODEL,
    "messages": [
        {"role": "system", "content": f"다음은 프로젝트 규칙이다:\n\n{claudemd}"},
        {"role": "user", "content": QUESTION}
    ],
    "temperature": 0.2,
}, timeout=120)
answer2 = resp2.json()["choices"][0]["message"]["content"]

print("=" * 60)
print("[CLAUDE.md 없이]")
print(answer1[:400])
print(f"\n{'='*60}")
print("[CLAUDE.md 포함]")
print(answer2[:400])
print(f"\n{'='*60}")
print("비교: CLAUDE.md가 있으면 구체적 IP, API, 안전 규칙이 반영됨")
PYEOF

# CLAUDE.md 효과 테스트 실행
python3 ~/lab/week07/test_claudemd.py
```

---

## Part 4: MCP 서버 연동과 Hooks 설정 (45분) — 실습

### 4.1 MCP 서버 개념 이해

```bash
cat > ~/lab/week07/mcp_concept.py << 'PYEOF'
"""
Week 07 실습: MCP 서버 구조 이해
간단한 MCP 서버를 Python으로 구현하여 프로토콜을 이해한다.
"""
import json
import sys

# MCP 서버가 제공하는 도구 목록 정의
MCP_TOOLS = {
    "tools": [
        {
            "name": "opsclaw_create_project",
            "description": "OpsClaw에 새 프로젝트를 생성한다",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "프로젝트 이름"},
                    "request_text": {"type": "string", "description": "작업 요청 내용"}
                },
                "required": ["name", "request_text"]
            }
        },
        {
            "name": "opsclaw_dispatch",
            "description": "OpsClaw를 통해 원격 서버에서 명령을 실행한다",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "command": {"type": "string"},
                    "server": {"type": "string", "enum": ["opsclaw", "secu", "web", "siem"]}
                },
                "required": ["project_id", "command", "server"]
            }
        },
        {
            "name": "opsclaw_evidence",
            "description": "프로젝트의 증적 요약을 조회한다",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"}
                },
                "required": ["project_id"]
            }
        }
    ]
}

print("MCP 서버가 Claude Code에 제공하는 도구 목록:")
print(json.dumps(MCP_TOOLS, indent=2, ensure_ascii=False))

print("\n이 도구들이 등록되면 Claude Code는:")
print("  1. 사용자가 '보안 점검해줘'라고 하면")
print("  2. opsclaw_create_project 도구를 선택")
print("  3. opsclaw_dispatch로 명령 실행")
print("  4. opsclaw_evidence로 결과 확인")
print("  → 대화만으로 OpsClaw 전체 파이프라인을 실행")
PYEOF

# MCP 개념 이해
python3 ~/lab/week07/mcp_concept.py
```

### 4.2 OpsClaw MCP 서버 구현

```bash
cat > ~/lab/week07/opsclaw_mcp_server.py << 'PYEOF'
"""
Week 07 실습: OpsClaw MCP 서버 (스탠드얼론 버전)
Claude Code에서 OpsClaw API를 도구로 사용할 수 있게 한다.
실제 MCP 프로토콜 대신 HTTP API로 구현한다.
"""
import requests
import json

OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# SubAgent URL 매핑
SERVER_MAP = {
    "opsclaw": "http://localhost:8002",
    "secu": "http://192.168.208.150:8002",
    "web": "http://192.168.208.151:8002",
    "siem": "http://192.168.208.152:8002",
}

class OpsCLawMCPTools:
    """OpsClaw MCP 도구 모음"""

    @staticmethod
    def create_project(name: str, request_text: str) -> dict:
        """프로젝트 생성"""
        resp = requests.post(f"{OPSCLAW}/projects", headers=HEADERS, json={
            "name": name,
            "request_text": request_text,
            "master_mode": "external"
        })
        project = resp.json()
        pid = project["id"]
        # 자동 stage 전환
        requests.post(f"{OPSCLAW}/projects/{pid}/plan", headers=HEADERS)
        requests.post(f"{OPSCLAW}/projects/{pid}/execute", headers=HEADERS)
        return {"project_id": pid, "status": "ready"}

    @staticmethod
    def dispatch(project_id: str, command: str, server: str) -> dict:
        """원격 명령 실행"""
        subagent_url = SERVER_MAP.get(server, SERVER_MAP["opsclaw"])
        resp = requests.post(
            f"{OPSCLAW}/projects/{project_id}/dispatch",
            headers=HEADERS,
            json={"command": command, "subagent_url": subagent_url}
        )
        return resp.json()

    @staticmethod
    def execute_plan(project_id: str, tasks: list, server: str = "opsclaw") -> dict:
        """다중 태스크 실행"""
        subagent_url = SERVER_MAP.get(server, SERVER_MAP["opsclaw"])
        opsclaw_tasks = [
            {"order": i+1, "instruction_prompt": t, "risk_level": "low", "subagent_url": subagent_url}
            for i, t in enumerate(tasks)
        ]
        resp = requests.post(
            f"{OPSCLAW}/projects/{project_id}/execute-plan",
            headers=HEADERS,
            json={"tasks": opsclaw_tasks, "subagent_url": subagent_url}
        )
        return resp.json()

    @staticmethod
    def get_evidence(project_id: str) -> dict:
        """증적 요약 조회"""
        resp = requests.get(
            f"{OPSCLAW}/projects/{project_id}/evidence/summary",
            headers=HEADERS
        )
        return resp.json()

    @staticmethod
    def complete(project_id: str, summary: str) -> dict:
        """완료 보고서 작성"""
        resp = requests.post(
            f"{OPSCLAW}/projects/{project_id}/completion-report",
            headers=HEADERS,
            json={"summary": summary, "outcome": "success", "work_details": [summary]}
        )
        return resp.json()

# 사용 데모
if __name__ == "__main__":
    tools = OpsCLawMCPTools()

    print("=" * 60)
    print("OpsClaw MCP Tools 데모")
    print("=" * 60)

    # 1. 프로젝트 생성
    print("\n[1] 프로젝트 생성...")
    project = tools.create_project("week07-mcp-demo", "MCP 도구 테스트")
    pid = project["project_id"]
    print(f"    Project ID: {pid}")

    # 2. execute-plan 실행
    print("\n[2] 보안 점검 실행...")
    result = tools.execute_plan(pid, [
        "hostname && uptime",
        "df -h / | tail -1",
        "ss -tlnp | grep -c LISTEN",
    ], "opsclaw")
    for r in result.get("results", result.get("task_results", [])):
        output = str(r.get("output", r.get("result", "")))[:80]
        print(f"    Task {r.get('order','?')}: {output}")

    # 3. 증적 확인
    print("\n[3] 증적 확인...")
    evidence = tools.get_evidence(pid)
    print(f"    {json.dumps(evidence, ensure_ascii=False)[:200]}")

    # 4. 완료
    print("\n[4] 완료 보고서...")
    tools.complete(pid, "MCP 도구 테스트 완료")
    print("    완료!")
PYEOF

# OpsClaw MCP 도구 테스트
python3 ~/lab/week07/opsclaw_mcp_server.py
```

### 4.3 Claude Code settings.json 설정

```bash
# Claude Code 설정 디렉토리 생성
mkdir -p ~/lab/week07/security-project/.claude

# settings.json 작성 (MCP + Hooks)
cat > ~/lab/week07/security-project/.claude/settings.json << 'JSONEOF'
{
  "permissions": {
    "allow": [
      "Bash(curl *localhost:8000*)",
      "Bash(ssh *)",
      "Bash(sshpass *)",
      "Bash(python3 *)",
      "Read(*)",
      "Write(~/lab/*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(mkfs *)",
      "Bash(dd if=*)",
      "Bash(shutdown *)",
      "Bash(reboot *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date '+%Y-%m-%d %H:%M:%S') PRE $CLAUDE_TOOL_INPUT\" >> /tmp/claude_security_audit.log"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date '+%Y-%m-%d %H:%M:%S') POST exit=$CLAUDE_EXIT_CODE\" >> /tmp/claude_security_audit.log"
          }
        ]
      }
    ]
  }
}
JSONEOF

echo "settings.json 작성 완료"
# 설정 확인
cat ~/lab/week07/security-project/.claude/settings.json | python3 -m json.tool
```

### 4.4 Hooks 시뮬레이션

```bash
cat > ~/lab/week07/hooks_simulation.py << 'PYEOF'
"""
Week 07 실습: Hooks 시뮬레이션
Claude Code의 PreToolUse/PostToolUse Hook 동작을 시뮬레이션한다.
"""
import subprocess
import datetime
import json

AUDIT_LOG = "/tmp/claude_security_audit.log"

def pre_hook(tool_name: str, tool_input: str):
    """PreToolUse Hook: 명령 실행 전 감사 로깅"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} PRE [{tool_name}] {tool_input}"
    # 감사 로그에 기록
    with open(AUDIT_LOG, "a") as f:
        f.write(log_entry + "\n")
    print(f"  [PRE HOOK] {log_entry}")

    # 위험 명령 차단
    blocked = ["rm -rf", "mkfs", "dd if=", "shutdown"]
    for pattern in blocked:
        if pattern in tool_input:
            print(f"  [PRE HOOK] BLOCKED: '{pattern}' detected!")
            return False
    return True

def post_hook(tool_name: str, exit_code: int, output: str):
    """PostToolUse Hook: 명령 실행 후 감사 로깅"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} POST [{tool_name}] exit={exit_code}"
    # 감사 로그에 기록
    with open(AUDIT_LOG, "a") as f:
        f.write(log_entry + "\n")
    print(f"  [POST HOOK] {log_entry}")

    # 실패 시 경고
    if exit_code != 0:
        print(f"  [POST HOOK] WARNING: 명령 실패 (exit={exit_code})")

def execute_with_hooks(command: str):
    """Hooks가 적용된 명령 실행"""
    print(f"\n명령: {command}")

    # Pre Hook
    allowed = pre_hook("Bash", command)
    if not allowed:
        return

    # 실제 실행
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)

    # Post Hook
    post_hook("Bash", result.returncode, result.stdout[:100])

    if result.stdout:
        print(f"  결과: {result.stdout.strip()[:100]}")

# 테스트
print("=" * 60)
print("Hooks 시뮬레이션")
print("=" * 60)

commands = [
    "hostname",          # 정상 실행
    "df -h /",           # 정상 실행
    "rm -rf /tmp/test",  # 차단될 명령
    "uptime",            # 정상 실행
    "cat /nonexistent",  # 실패할 명령
]

for cmd in commands:
    execute_with_hooks(cmd)

# 감사 로그 확인
print(f"\n{'='*60}")
print(f"감사 로그 ({AUDIT_LOG}):")
try:
    with open(AUDIT_LOG) as f:
        # 최근 10줄만 출력
        lines = f.readlines()
        for line in lines[-10:]:
            print(f"  {line.strip()}")
except FileNotFoundError:
    print("  (로그 없음)")
PYEOF

# Hooks 시뮬레이션 실행
python3 ~/lab/week07/hooks_simulation.py
```

---

## Part 5: 하이브리드 구성 — Claude Code + OpsClaw (35분) — 실습

### 5.1 하이브리드 아키텍처

```bash
cat > ~/lab/week07/hybrid_architecture.py << 'PYEOF'
"""
Week 07 실습: 하이브리드 아키텍처 데모
Claude Code(LLM 판단) + OpsClaw(분산 실행)을 결합한다.
"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"
OPSCLAW = "http://localhost:8000"
HEADERS = {"X-API-Key": "opsclaw-api-key-2026", "Content-Type": "application/json"}

# CLAUDE.md 컨텍스트 로드
with open("/root/lab/week07/security-project/CLAUDE.md") as f:
    context = f.read()

def claude_thinks(question: str) -> str:
    """Claude Code 역할: LLM이 분석/판단"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": f"프로젝트 규칙:\n{context}\n\n너는 Claude Code처럼 동작한다. 보안 점검 계획을 세우고, 실행할 명령을 JSON 배열로 제시하라.\n형식: [{{\"server\":\"서버명\",\"command\":\"명령어\",\"purpose\":\"목적\"}}]"},
            {"role": "user", "content": question}
        ],
        "temperature": 0.2,
    }, timeout=120)
    return resp.json()["choices"][0]["message"]["content"]

def opsclaw_executes(project_id: str, plan: list) -> list:
    """OpsClaw 역할: 분산 실행"""
    SERVER_MAP = {
        "opsclaw": "http://localhost:8002",
        "secu": "http://192.168.208.150:8002",
        "web": "http://192.168.208.151:8002",
        "siem": "http://192.168.208.152:8002",
    }
    results = []
    for task in plan:
        server = task.get("server", "opsclaw")
        subagent_url = SERVER_MAP.get(server, SERVER_MAP["opsclaw"])
        try:
            # OpsClaw dispatch로 실행
            resp = requests.post(
                f"{OPSCLAW}/projects/{project_id}/dispatch",
                headers=HEADERS,
                json={"command": task["command"], "subagent_url": subagent_url},
                timeout=15
            )
            results.append({
                "server": server,
                "command": task["command"],
                "result": resp.json()
            })
        except Exception as e:
            results.append({
                "server": server,
                "command": task["command"],
                "error": str(e)
            })
    return results

def claude_analyzes(results: list) -> str:
    """Claude Code 역할: 결과 분석"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "너는 보안 분석가이다. 점검 결과를 분석하여 종합 보고서를 작성하라."},
            {"role": "user", "content": f"점검 결과:\n{json.dumps(results, indent=2, ensure_ascii=False)[:3000]}"}
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }, timeout=120)
    return resp.json()["choices"][0]["message"]["content"]

def main():
    request = "opsclaw 서버의 전체 보안 상태를 점검해줘"

    print("=" * 60)
    print("하이브리드 구성: Claude Code(판단) + OpsClaw(실행)")
    print("=" * 60)

    # Phase 1: Claude thinks (계획)
    print(f"\n[Phase 1] Claude Code가 계획 수립...")
    plan_text = claude_thinks(request)
    print(f"  LLM 응답: {plan_text[:300]}")

    # JSON 파싱
    try:
        start = plan_text.find("[")
        end = plan_text.rfind("]") + 1
        plan = json.loads(plan_text[start:end])
    except (ValueError, json.JSONDecodeError):
        # 파싱 실패 시 기본 계획 사용
        plan = [
            {"server": "opsclaw", "command": "df -h /", "purpose": "디스크 확인"},
            {"server": "opsclaw", "command": "free -m", "purpose": "메모리 확인"},
            {"server": "opsclaw", "command": "ss -tlnp", "purpose": "포트 확인"},
        ]

    print(f"  계획 ({len(plan)}개 태스크):")
    for t in plan:
        print(f"    [{t.get('server','?')}] {t.get('command','?')} — {t.get('purpose','')}")

    # Phase 2: OpsClaw executes (실행)
    print(f"\n[Phase 2] OpsClaw가 실행...")
    # 프로젝트 생성
    project = requests.post(f"{OPSCLAW}/projects", headers=HEADERS, json={
        "name": "week07-hybrid",
        "request_text": request,
        "master_mode": "external"
    }).json()
    pid = project["id"]
    requests.post(f"{OPSCLAW}/projects/{pid}/plan", headers=HEADERS)
    requests.post(f"{OPSCLAW}/projects/{pid}/execute", headers=HEADERS)

    results = opsclaw_executes(pid, plan)
    for r in results:
        output = str(r.get("result", r.get("error", "")))[:80]
        print(f"    [{r['server']}] {r['command'][:30]}: {output}")

    # Phase 3: Claude analyzes (분석)
    print(f"\n[Phase 3] Claude Code가 결과 분석...")
    analysis = claude_analyzes(results)
    print(f"  {analysis[:500]}")

    # Phase 4: OpsClaw records (기록)
    print(f"\n[Phase 4] OpsClaw에 보고서 기록...")
    requests.post(f"{OPSCLAW}/projects/{pid}/completion-report", headers=HEADERS, json={
        "summary": "하이브리드 보안 점검 완료",
        "outcome": "success",
        "work_details": [analysis[:500]]
    })
    print(f"  Project {pid} 완료!")

if __name__ == "__main__":
    main()
PYEOF

# 하이브리드 데모 실행
python3 ~/lab/week07/hybrid_architecture.py
```

### 5.2 감사 로그 분석

```bash
# 전체 감사 로그 확인
echo "=== Claude Code 감사 로그 ==="
cat /tmp/claude_security_audit.log 2>/dev/null || echo "(감사 로그 없음)"

# 로그 통계
echo ""
echo "=== 통계 ==="
if [ -f /tmp/claude_security_audit.log ]; then
    # PRE/POST 카운트
    echo "PRE Hook 실행: $(grep -c 'PRE' /tmp/claude_security_audit.log)회"
    echo "POST Hook 실행: $(grep -c 'POST' /tmp/claude_security_audit.log)회"
    # 차단 카운트
    echo "차단된 명령: $(grep -c 'BLOCKED' /tmp/claude_security_audit.log 2>/dev/null || echo 0)회"
fi
```

---

## Part 6: 퀴즈 + 과제 (15분)

### 복습 퀴즈

**Q1. CLAUDE.md의 주요 역할은?**
- (A) LLM 모델을 학습시킨다
- **(B) 프로젝트 규칙과 컨텍스트를 AI에게 제공한다** ✅
- (C) 데이터베이스 스키마를 정의한다
- (D) MCP 서버를 실행한다

**Q2. MCP 프로토콜의 역할은?**
- (A) 데이터베이스 통신
- (B) 파일 암호화
- **(C) LLM에 외부 도구와 데이터를 연결** ✅
- (D) 네트워크 패킷 분석

**Q3. PreToolUse Hook의 실행 시점은?**
- **(A) 도구 실행 전** ✅
- (B) 도구 실행 후
- (C) 프로젝트 생성 시
- (D) LLM 응답 생성 시

**Q4. 하이브리드 구성에서 Claude Code와 OpsClaw의 역할 분담으로 올바른 것은?**
- (A) Claude Code가 명령 실행, OpsClaw가 분석
- **(B) Claude Code가 판단/분석, OpsClaw가 분산 실행** ✅
- (C) Claude Code가 DB 관리, OpsClaw가 LLM 실행
- (D) 두 시스템 모두 동일한 역할

**Q5. settings.json의 permissions.deny에 등록된 명령의 동작은?**
- (A) 경고 후 실행
- (B) 로그만 기록
- **(C) 실행이 차단된다** ✅
- (D) 자동으로 대체 명령이 실행된다

### 과제

**[과제] 하이브리드 보안 에이전트 구축**

1. CLAUDE.md에 다음을 추가하라:
   - Wazuh API 접속 정보
   - Suricata 로그 경로
   - 경보 분석 프롬프트 템플릿

2. Hooks를 확장하여 다음을 구현하라:
   - 모든 Bash 명령의 실행 시간 기록
   - 위험 패턴(rm, kill, shutdown) 탐지 시 별도 경고 로그

3. 하이브리드 스크립트를 수정하여 secu, web 서버까지 점검하라.

4. 결과를 `~/lab/week07/homework.md`에 정리하라.

**제출물:** CLAUDE.md + settings.json + 수정된 스크립트 + homework.md

---

> **다음 주 예고:** Week 08 중간 실습에서는 지금까지 배운 모든 것을 종합하여 "나만의 보안 에이전트"를 구축한다. Ollama 모델 선택, 프롬프트 설계, OpsClaw 프로젝트 생성, execute-plan으로 4대 서버 자동 점검, 결과 분석과 보고서 작성까지 전 과정을 수행한다.
