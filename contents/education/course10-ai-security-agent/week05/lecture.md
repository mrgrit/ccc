# Week 05: 서버 사이드 하네스 구축 (1) — OpsClaw

## 학습 목표
- OpsClaw Native Mode의 구조와 설정 방법을 이해한다
- Master Service와 Ollama LLM 연동을 구성할 수 있다
- 자연어 요청에서 실행까지의 전체 파이프라인을 구축한다
- CLI(opsclaw run)로 자율 작업을 실행할 수 있다
- Project 생명주기(생성→계획→실행→보고)를 실습한다

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
| 0:00-0:25 | 이론: OpsClaw Native Mode 아키텍처 (Part 1) | 강의 |
| 0:25-0:50 | 이론: 자연어→실행 파이프라인 (Part 2) | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:45 | 실습: OpsClaw 서비스 기동과 설정 (Part 3) | 실습 |
| 1:45-2:30 | 실습: Native Mode 자율 실행 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:15 | 실습: 다중 서버 점검 자동화 (Part 5) | 실습 |
| 3:15-3:30 | 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **Native Mode** | Native Mode | OpsClaw 내부 LLM이 자율 계획·실행하는 모드 | 자율주행 모드 |
| **External Mode** | External Mode | 외부 에이전트(Claude Code)가 API로 제어하는 모드 | 수동 운전 모드 |
| **Master Service** | Master Service | LLM 기반 계획 수립 서비스 (:8001) | 참모본부 |
| **Manager API** | Manager API | 상태 관리·실행 제어 서비스 (:8000) | 작전 사령부 |
| **SubAgent** | SubAgent Runtime | 원격 명령 실행 서비스 (:8002) | 현장 실행팀 |
| **Project** | Project | 작업 단위: 생성→계획→실행→완료 | 프로젝트 관리 티켓 |
| **Stage** | Stage | 프로젝트 진행 단계 | 공정 단계 |
| **dispatch** | Dispatch | 단일 명령을 SubAgent에 전달·실행 | 지시서 한 장 전달 |
| **execute-plan** | Execute Plan | 여러 Task를 일괄 실행 | 작전 계획서 전체 실행 |
| **evidence** | Evidence | 작업 수행 증적 (로그, 결과) | 수사 증거물 |
| **completion-report** | Completion Report | 프로젝트 완료 보고서 | 결과 보고서 |
| **request_text** | Request Text | 프로젝트 생성 시 자연어 요청 | 고객 요구사항 |
| **master_mode** | Master Mode | 프로젝트 제어 방식 (native/external) | 운전 모드 선택 |
| **A2A** | Agent-to-Agent | 에이전트 간 통신 프로토콜 | 요원 간 무전 채널 |
| **LangGraph** | LangGraph | 상태 기계 기반 워크플로우 프레임워크 | 공정 흐름도 엔진 |
| **uvicorn** | Uvicorn | ASGI 웹 서버 (FastAPI 실행용) | 웹 서비스 구동기 |

---

## Part 1: OpsClaw Native Mode 아키텍처 (25분) — 이론

### 1.1 두 가지 작동 모드

```
  Mode A: Native Mode (자율 실행)
  사용자 → Manager API → Master Service(LLM)
  ↓  ↓ 계획 수립
  SubAgent(secu)  SubAgent(web)
  ↓  ↓ 명령 실행
  결과 → Evidence → 완료보고서
  특징: LLM이 자율적으로 계획-실행-보고

  Mode B: External Mode (외부 제어)
  Claude Code → Manager API → SubAgent
  ↑  ↓
  결과 해석 ← Evidence
  특징: Claude Code가 API를 호출하여 제어
```

### 1.2 서비스 구성

| 서비스 | 포트 | 역할 | Native Mode |
|--------|------|------|-------------|
| Manager API | :8000 | 상태 관리, API 게이트웨이 | 필수 |
| Master Service | :8001 | LLM 기반 계획 수립 | Native에서만 사용 |
| SubAgent Runtime | :8002 | 명령 실행 | 필수 |

### 1.3 자연어→실행 파이프라인

```
"secu 서버의 방화벽 규칙을 점검하고 불필요한 포트를 찾아줘"
    ↓
[Manager API] Project 생성 (request_text 저장)
    ↓
[Master Service] LLM이 계획 수립:
  Task 1: nft list ruleset (secu)
  Task 2: ss -tlnp (secu)
  Task 3: 결과 분석 → 불필요 포트 식별
    ↓
[Manager API] execute-plan → SubAgent(secu) 실행
    ↓
[SubAgent] 명령 실행 → 결과 반환
    ↓
[Manager API] Evidence 기록 + PoW 블록 생성
    ↓
[Master Service] 결과 분석 → 완료 보고서
```

---

## Part 2: Project 생명주기 (25분) — 이론

### 2.1 Stage 전환 흐름

```
created → planning → executing → reporting → completed
   │          │           │           │          │
   │          │           │           │          └─ 최종 완료
   │          │           │           └─ 보고서 작성 중
   │          │           └─ Task 실행 중
   │          └─ 계획 수립 중
   └─ 프로젝트 생성됨
```

### 2.2 각 Stage에서 호출 가능한 API

| Stage | 호출 가능 API | 설명 |
|-------|-------------|------|
| created | POST /projects/{id}/plan | planning으로 전환 |
| planning | POST /projects/{id}/execute | executing으로 전환 |
| executing | POST /projects/{id}/execute-plan | Task 실행 |
| executing | POST /projects/{id}/dispatch | 단일 명령 실행 |
| executing | POST /projects/{id}/completion-report | 보고서 작성 |
| 모든 Stage | GET /projects/{id} | 상태 조회 |
| 모든 Stage | GET /projects/{id}/evidence/summary | 증적 요약 |

---

## Part 3: OpsClaw 서비스 기동과 설정 (45분) — 실습

### 3.1 PostgreSQL 기동 확인

> **실습 목적**: 멀티 에이전트 시스템에서 에이전트 간 역할 분담과 협업 패턴을 구현하기 위해 수행한다
>
> **배우는 것**: Manager-Worker, Pipeline, 경쟁적 협업 등 멀티 에이전트 패턴과, 에이전트 간 메시지 전달 구조를 이해한다
>
> **결과 해석**: 각 에이전트의 역할별 출력이 올바르게 통합되고, 전체 작업이 완료되는지로 협업 효과를 판단한다
>
> **실전 활용**: 분산 보안 모니터링, Red/Blue 자동 대결, 대규모 인프라 동시 점검 시스템 구축에 활용한다

```bash
# Docker 상태 확인
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep postgres

# PostgreSQL이 미기동이면 시작
echo "1" | sudo -S docker compose -f /home/opsclaw/opsclaw/docker/postgres-compose.yaml up -d

# DB 연결 테스트
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c "SELECT version();" 2>/dev/null || \
  echo "PostgreSQL 연결 실패 — Docker 컨테이너를 확인하세요"
```

### 3.2 환경 변수 설정

```bash
# .env 파일 확인
cat /home/opsclaw/opsclaw/.env | head -20

# 환경 변수 로딩
cd /home/opsclaw/opsclaw
# .env 파일의 모든 변수를 현재 셸에 로딩
set -a && source .env && set +a

# PYTHONPATH 설정 (모듈 경로)
export PYTHONPATH=/home/opsclaw/opsclaw

# 주요 변수 확인
echo "OPSCLAW_API_KEY: $OPSCLAW_API_KEY"
echo "OLLAMA_BASE_URL: $OLLAMA_BASE_URL"
echo "DATABASE_URL: $DATABASE_URL"
```

### 3.3 Manager API 기동

```bash
# 기존 프로세스 확인
pgrep -af "manager-api" || echo "Manager API 미기동"

# Manager API 시작 (백그라운드)
cd /home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &

# 기동 대기 (최대 10초)
for i in $(seq 1 10); do
  # health 엔드포인트 확인
  curl -s http://localhost:8000/health > /dev/null 2>&1 && break
  sleep 1
done

# 기동 확인
curl -s http://localhost:8000/health | python3 -m json.tool
```

### 3.4 SubAgent Runtime 기동

```bash
# SubAgent 기동 확인
pgrep -af "subagent" || echo "SubAgent 미기동"

# SubAgent 시작 (로컬)
cd /home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.subagent-runtime.src.main:app \
  --host 0.0.0.0 --port 8002 --log-level warning > /tmp/subagent.log 2>&1 &

# 기동 확인
sleep 3
curl -s http://localhost:8002/health | python3 -m json.tool
```

### 3.5 Master Service 기동 (Native Mode용)

```bash
# Master Service 기동 확인
pgrep -af "master-service" || echo "Master Service 미기동"

# Master Service 시작
cd /home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.master-service.src.main:app \
  --host 0.0.0.0 --port 8001 --log-level warning > /tmp/master.log 2>&1 &

# 기동 확인
sleep 3
curl -s http://localhost:8001/health | python3 -m json.tool
```

### 3.6 전체 서비스 상태 확인 스크립트

```bash
mkdir -p ~/lab/week05

cat > ~/lab/week05/check_services.sh << 'SHEOF'
#!/bin/bash
# OpsClaw 전체 서비스 상태 확인 스크립트

echo "=== OpsClaw 서비스 상태 ==="
echo ""

# Manager API (:8000)
printf "%-20s " "Manager API"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
# HTTP 상태 코드로 판정
if [ "$HEALTH" = "200" ]; then
    echo "OK (port 8000)"
else
    echo "DOWN (HTTP $HEALTH)"
fi

# Master Service (:8001)
printf "%-20s " "Master Service"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "OK (port 8001)"
else
    echo "DOWN (HTTP $HEALTH)"
fi

# SubAgent Runtime (:8002)
printf "%-20s " "SubAgent Runtime"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "OK (port 8002)"
else
    echo "DOWN (HTTP $HEALTH)"
fi

# PostgreSQL
printf "%-20s " "PostgreSQL"
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c "SELECT 1" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "OK (port 5432)"
else
    echo "DOWN"
fi

# Ollama (dgx-spark)
printf "%-20s " "Ollama (dgx-spark)"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://192.168.0.105:11434/api/tags 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "OK (port 11434)"
else
    echo "UNREACHABLE (HTTP $HEALTH)"
fi

echo ""
echo "=== 원격 SubAgent ==="
# 원격 SubAgent 상태
for host in "secu:192.168.208.150" "web:192.168.208.151" "siem:192.168.208.152"; do
    NAME=$(echo $host | cut -d: -f1)
    IP=$(echo $host | cut -d: -f2)
    printf "%-20s " "$NAME ($IP)"
    # 2초 타임아웃으로 확인
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://${IP}:8002/health 2>/dev/null)
    if [ "$HEALTH" = "200" ]; then
        echo "OK"
    else
        echo "DOWN/UNREACHABLE"
    fi
done
SHEOF

# 실행 권한 부여 및 실행
chmod +x ~/lab/week05/check_services.sh
bash ~/lab/week05/check_services.sh
```

---

## Part 4: Native Mode 자율 실행 (45분) — 실습

### 4.1 External Mode: 수동 API 호출 (복습)

```bash
# 1. 프로젝트 생성 (external mode)
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week05-external-demo",
    "request_text": "opsclaw 서버의 디스크와 메모리 상태를 확인해줘",
    "master_mode": "external"
  }')
PID_EXT=$(echo $PROJECT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "External Project: $PID_EXT"

# 2. Stage 전환
# plan 단계로 전환
curl -s -X POST http://localhost:8000/projects/${PID_EXT}/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# execute 단계로 전환
curl -s -X POST http://localhost:8000/projects/${PID_EXT}/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 3. 수동으로 Task 배열 구성 및 실행
curl -s -X POST http://localhost:8000/projects/${PID_EXT}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order": 1, "instruction_prompt": "df -h / /tmp /home", "risk_level": "low"},
      {"order": 2, "instruction_prompt": "free -m", "risk_level": "low"},
      {"order": 3, "instruction_prompt": "cat /proc/loadavg", "risk_level": "low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 각 태스크 결과 출력
for task in data.get('results', data.get('task_results', [])):
    print(f\"Task {task.get('order','?')}: {str(task.get('output', task.get('result','')))[:100]}\")
"

# 4. 완료 보고서
curl -s -X POST http://localhost:8000/projects/${PID_EXT}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"summary":"External Mode 수동 실행 완료","outcome":"success","work_details":["디스크/메모리 상태 확인 완료"]}'
```

### 4.2 Native Mode: LLM 자율 실행

```bash
# Native Mode 프로젝트 생성
# master_mode를 "native"로 설정하면 Master Service가 자율 실행
PROJECT_N=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week05-native-demo",
    "request_text": "opsclaw 서버의 보안 상태를 점검해줘. 디스크, 메모리, 열린 포트, 최근 로그인 기록을 확인하라.",
    "master_mode": "native"
  }')
PID_NAT=$(echo $PROJECT_N | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Native Project: $PID_NAT"

# Native Mode에서는 Master Service가 자동으로 plan/execute 진행
# 진행 상태 모니터링 (10초 간격, 최대 2분)
for i in $(seq 1 12); do
    # 프로젝트 상태 조회
    STATUS=$(curl -s -H "X-API-Key: opsclaw-api-key-2026" \
      http://localhost:8000/projects/${PID_NAT} | \
      python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stage','unknown'))")
    echo "[$i] Stage: $STATUS"
    # 완료되면 종료
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "reporting" ]; then
        break
    fi
    sleep 10
done

# 결과 확인
echo ""
echo "=== Evidence 요약 ==="
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/${PID_NAT}/evidence/summary | python3 -m json.tool
```

### 4.3 External Mode로 수동 제어 (LLM 활용)

Native Mode가 동작하지 않을 경우, External Mode에서 LLM을 직접 활용한다.

```bash
cat > ~/lab/week05/external_with_llm.py << 'PYEOF'
"""
Week 05 실습: External Mode + LLM 조합
Claude Code 방식으로 OpsClaw API를 호출한다.
LLM이 계획을 세우고, 프로그램이 execute-plan으로 실행한다.
"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"
OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def ask_llm_for_plan(request: str) -> list:
    """LLM에게 실행 계획을 요청"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": """너는 IT 운영 자동화 계획가이다.
사용자 요청을 분석하여 실행할 쉘 명령을 계획하라.
반드시 다음 JSON 배열로 응답하라:
[{"order":1,"command":"명령어","risk":"low|medium|high","description":"설명"}, ...]
JSON 배열만 출력하라."""
            },
            {"role": "user", "content": request}
        ],
        "temperature": 0.1,
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"]
    # JSON 배열 추출
    start = content.find("[")
    end = content.rfind("]") + 1
    return json.loads(content[start:end])

def execute_plan_via_opsclaw(project_id: str, tasks: list):
    """OpsClaw execute-plan API로 실행"""
    opsclaw_tasks = []
    for t in tasks:
        opsclaw_tasks.append({
            "order": t["order"],
            "instruction_prompt": t["command"],
            "risk_level": t.get("risk", "low"),
        })

    resp = requests.post(
        f"{OPSCLAW}/projects/{project_id}/execute-plan",
        headers=HEADERS,
        json={"tasks": opsclaw_tasks, "subagent_url": "http://localhost:8002"}
    )
    return resp.json()

def main():
    user_request = "서버의 보안 상태를 점검해줘: 디스크, 메모리, 열린 포트, SSH 설정, 최근 실패 로그인"

    print("=" * 60)
    print(f"요청: {user_request}")
    print("=" * 60)

    # 1. LLM이 계획 수립
    print("\n[1] LLM 계획 수립 중...")
    plan = ask_llm_for_plan(user_request)
    for t in plan:
        print(f"  Task {t['order']}: {t['command']} ({t.get('risk','low')})")

    # 2. OpsClaw 프로젝트 생성
    print("\n[2] OpsClaw 프로젝트 생성...")
    project = requests.post(f"{OPSCLAW}/projects", headers=HEADERS, json={
        "name": "week05-llm-plan",
        "request_text": user_request,
        "master_mode": "external"
    }).json()
    pid = project["id"]
    print(f"  Project ID: {pid}")

    # 3. Stage 전환
    requests.post(f"{OPSCLAW}/projects/{pid}/plan", headers=HEADERS)
    requests.post(f"{OPSCLAW}/projects/{pid}/execute", headers=HEADERS)

    # 4. execute-plan 실행
    print("\n[3] execute-plan 실행 중...")
    results = execute_plan_via_opsclaw(pid, plan)
    for r in results.get("results", results.get("task_results", [])):
        output = str(r.get("output", r.get("result", "")))[:150]
        print(f"  Task {r.get('order','?')}: {output}")

    # 5. 완료 보고서
    print("\n[4] 완료 보고서 작성...")
    requests.post(f"{OPSCLAW}/projects/{pid}/completion-report", headers=HEADERS, json={
        "summary": "LLM 계획 기반 보안 점검 완료",
        "outcome": "success",
        "work_details": [f"Task {t['order']}: {t['command']}" for t in plan]
    })
    print("  완료!")

if __name__ == "__main__":
    main()
PYEOF

# LLM 계획 기반 실행
python3 ~/lab/week05/external_with_llm.py
```

---

## Part 5: 다중 서버 점검 자동화 (35분) — 실습

### 5.1 다중 SubAgent 점검

```bash
cat > ~/lab/week05/multi_server_check.py << 'PYEOF'
"""
Week 05 실습: 다중 서버 보안 점검
여러 SubAgent에 Task를 분배하여 병렬 점검한다.
"""
import requests
import json

OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# 서버별 SubAgent URL
SERVERS = {
    "opsclaw": "http://localhost:8002",
    "secu": "http://192.168.208.150:8002",
    "web": "http://192.168.208.151:8002",
    "siem": "http://192.168.208.152:8002",
}

# 점검 항목
CHECKS = [
    {"command": "hostname && uptime", "description": "서버 식별 및 가동 시간"},
    {"command": "df -h / | tail -1", "description": "루트 디스크 사용량"},
    {"command": "free -m | grep Mem", "description": "메모리 사용량"},
    {"command": "ss -tlnp | grep -c LISTEN", "description": "리슨 포트 수"},
]

def check_server(server_name: str, subagent_url: str, project_id: str):
    """단일 서버 점검"""
    tasks = []
    for i, check in enumerate(CHECKS, 1):
        tasks.append({
            "order": i,
            "instruction_prompt": check["command"],
            "risk_level": "low",
            "subagent_url": subagent_url,
        })

    try:
        resp = requests.post(
            f"{OPSCLAW}/projects/{project_id}/execute-plan",
            headers=HEADERS,
            json={"tasks": tasks, "subagent_url": subagent_url},
            timeout=30
        )
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    # 프로젝트 생성
    project = requests.post(f"{OPSCLAW}/projects", headers=HEADERS, json={
        "name": "week05-multi-server",
        "request_text": "전체 인프라 보안 점검",
        "master_mode": "external"
    }).json()
    pid = project["id"]

    # Stage 전환
    requests.post(f"{OPSCLAW}/projects/{pid}/plan", headers=HEADERS)
    requests.post(f"{OPSCLAW}/projects/{pid}/execute", headers=HEADERS)

    print(f"Project: {pid}")
    print("=" * 60)

    # 각 서버 점검
    all_results = {}
    for name, url in SERVERS.items():
        print(f"\n--- {name} ({url}) ---")
        result = check_server(name, url, pid)
        all_results[name] = result

        if "error" in result:
            print(f"  오류: {result['error']}")
        else:
            for r in result.get("results", result.get("task_results", [])):
                output = str(r.get("output", r.get("result", "")))[:80]
                print(f"  Task {r.get('order','?')}: {output}")

    # 결과 저장
    with open("/root/lab/week05/multi_server_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # 완료 보고서
    success_count = sum(1 for r in all_results.values() if "error" not in r)
    requests.post(f"{OPSCLAW}/projects/{pid}/completion-report", headers=HEADERS, json={
        "summary": f"다중 서버 점검 완료: {success_count}/{len(SERVERS)} 서버 성공",
        "outcome": "success" if success_count == len(SERVERS) else "partial",
        "work_details": [f"{name}: {'OK' if 'error' not in r else 'FAIL'}" for name, r in all_results.items()]
    })

    print(f"\n=== 완료: {success_count}/{len(SERVERS)} 서버 점검 성공 ===")

if __name__ == "__main__":
    main()
PYEOF

# 다중 서버 점검 실행
python3 ~/lab/week05/multi_server_check.py
```

### 5.2 점검 결과 LLM 분석

```bash
cat > ~/lab/week05/analyze_results.py << 'PYEOF'
"""
Week 05 실습: 점검 결과를 LLM으로 분석
다중 서버 점검 결과를 종합 분석한다.
"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

# 점검 결과 로드
try:
    with open("/root/lab/week05/multi_server_results.json") as f:
        results = json.load(f)
except FileNotFoundError:
    results = {"opsclaw": {"results": [{"output": "sample data"}]}}

# LLM 분석 요청
resp = requests.post(OLLAMA_URL, json={
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": """너는 IT 인프라 보안 감사관이다.
다중 서버 점검 결과를 분석하여 다음을 제공하라:
1. 서버별 상태 요약 (정상/주의/위험)
2. 발견된 보안 문제점
3. 개선 권고 사항
4. 종합 점수 (100점 만점)
한국어로 작성하라."""
        },
        {
            "role": "user",
            "content": f"다음 서버 점검 결과를 분석해줘:\n{json.dumps(results, indent=2, ensure_ascii=False)[:3000]}"
        }
    ],
    "temperature": 0.2,
    "max_tokens": 2048,
}, timeout=180)

analysis = resp.json()["choices"][0]["message"]["content"]
print("=" * 60)
print("다중 서버 점검 종합 분석")
print("=" * 60)
print(analysis)

# 분석 결과 저장
with open("/root/lab/week05/analysis_report.md", "w") as f:
    f.write(f"# 다중 서버 점검 종합 분석\n\n{analysis}")
print("\n보고서 저장: ~/lab/week05/analysis_report.md")
PYEOF

# 종합 분석 실행
python3 ~/lab/week05/analyze_results.py
```

---

## Part 6: 퀴즈 + 과제 (15분)

### 복습 퀴즈

**Q1. OpsClaw의 Native Mode와 External Mode의 가장 큰 차이는?**
- (A) 사용하는 데이터베이스가 다르다
- **(B) LLM이 자율 계획·실행하느냐, 외부에서 API로 제어하느냐의 차이** ✅
- (C) SubAgent 수가 다르다
- (D) 보안 수준이 다르다

**Q2. OpsClaw의 Project Stage 순서로 올바른 것은?**
- **(A) created → planning → executing → completed** ✅
- (B) planning → created → executing → completed
- (C) executing → planning → completed → created
- (D) created → executing → planning → completed

**Q3. execute-plan API의 역할은?**
- (A) 프로젝트를 생성한다
- (B) LLM 모델을 학습시킨다
- **(C) 여러 Task를 SubAgent에 전달하여 일괄 실행한다** ✅
- (D) 보고서를 생성한다

**Q4. Manager API의 기본 포트는?**
- (A) 8001
- **(B) 8000** ✅
- (C) 8002
- (D) 5432

**Q5. SubAgent의 역할로 가장 적절한 것은?**
- (A) LLM을 실행한다
- (B) 데이터베이스를 관리한다
- **(C) 원격 서버에서 명령을 실행한다** ✅
- (D) API 인증을 처리한다

### 과제

**[과제] 자율 보안 점검 파이프라인 구축**

1. `external_with_llm.py`를 확장하여 다음을 구현하라:
   - LLM에게 "웹 서버 보안 점검" 계획을 요청
   - web 서버(http://192.168.208.151:8002)에 Task 실행
   - 결과를 LLM으로 분석
   - 최종 보고서를 OpsClaw completion-report로 기록

2. 점검 항목: Apache 설정, SSL 인증서, 열린 포트, Wazuh 에이전트 상태

3. 결과를 `~/lab/week05/homework.md`에 정리하라.

**제출물:** 수정된 스크립트 + `homework.md`

---

> **다음 주 예고:** Week 06에서는 Playbook 설계/등록, execute-plan 병렬 실행, PoW 보상 시스템, Q-learning 정책 학습을 실습한다.
