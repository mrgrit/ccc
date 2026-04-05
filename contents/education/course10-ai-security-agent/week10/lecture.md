# Week 10: 멀티에이전트 오케스트레이션

## 학습 목표

- 다중 SubAgent를 병렬로 제어하는 오케스트레이션 패턴을 이해한다
- Red/Blue Agent를 동시에 운영하여 자율 Purple Team을 구성한다
- Agent간 지식 교환 API를 활용한 협업 시스템을 구축한다
- LangGraph 상태기계로 복잡한 워크플로우를 설계한다
- Master → Manager → SubAgent 전체 흐름을 실습으로 검증한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

## 강의 시간 배분 (3시간)

| 시간 | 파트 | 내용 | 형태 |
|------|------|------|------|
| 0:00-0:25 | Part 1 | 멀티에이전트 아키텍처 패턴 | 이론 |
| 0:25-0:55 | Part 2 | 다중 SubAgent 병렬 제어 | 실습 |
| 0:55-1:25 | Part 3 | Red/Blue Agent 동시 운영 | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:10 | Part 4 | Agent간 지식 교환 API | 실습 |
| 2:10-2:40 | Part 5 | LangGraph 상태기계 워크플로우 | 실습 |
| 2:40-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **오케스트레이션** | 여러 에이전트/서비스를 조율하여 하나의 작업을 수행 | Manager가 3개 SubAgent를 병렬 실행 |
| **Master Agent** | 전체 작업 계획을 수립하는 최상위 에이전트 | Claude Code, OpsClaw Master |
| **Manager API** | 상태 관리와 실행 제어를 담당하는 중간 계층 | OpsClaw Manager (:8000) |
| **SubAgent** | 실제 명령을 실행하는 말단 에이전트 | secu/web/siem SubAgent (:8002) |
| **Red Agent** | 공격 측 자율 에이전트 (취약점 탐색/익스플로잇) | gemma3:12b 기반 공격 에이전트 |
| **Blue Agent** | 방어 측 자율 에이전트 (탐지/대응) | llama3.1:8b 기반 방어 에이전트 |
| **Purple Team** | Red+Blue 동시 운영으로 보안 수준을 검증 | 자율 공방 시뮬레이션 |
| **LangGraph** | LLM 애플리케이션을 상태기계로 구성하는 프레임워크 | 노드=함수, 에지=조건 전이 |
| **State Machine** | 상태와 전이로 시스템 동작을 정의하는 모델 | init→plan→execute→done |
| **Fan-out** | 하나의 작업을 여러 에이전트에 동시 분배 | 3개 서버에 동시에 점검 명령 전송 |
| **Fan-in** | 여러 에이전트의 결과를 하나로 수집/합산 | 3개 결과를 종합하여 리포트 생성 |
| **Knowledge Exchange** | 에이전트간 경험/지식을 공유하는 API | experience publish/pull |
| **execute-plan** | 복수 태스크를 한 번에 실행하는 Manager API | POST /projects/{id}/execute-plan |
| **evidence** | 에이전트 실행 결과의 감사 기록 | stdout, exit_code, 타임스탬프 |
| **agent_id** | 각 SubAgent를 고유 식별하는 URL | http://10.20.30.1:8002 |
| **PoW (Proof of Work)** | 에이전트 작업 증명 블록체인 | 작업 해시 체인으로 변조 불가 |

---

## Part 1: 멀티에이전트 아키텍처 패턴 (0:00-0:25)

### 1.1 단일 에이전트 vs 멀티에이전트

| 특성 | 단일 에이전트 | 멀티에이전트 |
|------|-------------|-------------|
| 구조 | LLM 1개 + Tool N개 | LLM N개 + 역할 분담 |
| 확장성 | 프롬프트 길이 한계 | 수평 확장 가능 |
| 전문성 | 범용 | 역할별 전문화 |
| 장애 격리 | 전체 중단 | 부분 장애 허용 |
| 복잡도 | 낮음 | 높음 (통신, 동기화) |

### 1.2 OpsClaw 멀티에이전트 아키텍처

```
Master (Claude Code / Native LLM)
  - 전체 계획 수립
  - 태스크 분배 결정
  API 호출
  |
  Manager API (:8000)
  - 프로젝트/상태 관리
  - execute-plan → 태스크별 SubAgent 라우팅
  - PoW 블록 생성, evidence 기록

  SubAgent|  | SubAgent|  | SubAgent
  secu  |  |  web  |  |  siem
  :8002  |  | :8002  |  | :8002
```

### 1.3 오케스트레이션 패턴

| 패턴 | 설명 | 사용 사례 |
|------|------|----------|
| **Sequential** | 순차 실행 (A → B → C) | 의존성 있는 태스크 |
| **Parallel (Fan-out/Fan-in)** | 동시 실행 후 결과 수집 | 다중 서버 동시 점검 |
| **Conditional** | 조건에 따라 다른 경로 | 위험도별 대응 분기 |
| **Loop** | 반복 실행 | 주기적 모니터링 |
| **Hierarchical** | 상위 에이전트가 하위 에이전트를 관리 | Master→Manager→SubAgent |

---

## Part 2: 다중 SubAgent 병렬 제어 (0:25-0:55)

### 2.1 프로젝트 생성과 Stage 전환

> **실습 목적**: 에이전트의 보안 분석 정확도를 체계적으로 평가하고 개선하기 위한 벤치마크를 구축하기 위해 수행한다
>
> **배우는 것**: 보안 에이전트 평가를 위한 테스트 데이터셋 구축, 자동 평가 스크립트 작성, 성능 메트릭 수집 방법을 이해한다
>
> **결과 해석**: 정확도, 재현율, F1-Score, 평균 응답 시간으로 에이전트 성능을 정량적으로 평가한다
>
> **실전 활용**: AI 에이전트 도입 PoC 평가, 모델/프롬프트 업그레이드 효과 측정, 에이전트 성능 SLA 정의에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 멀티에이전트 테스트 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week10-multi-agent",
    "request_text": "멀티에이전트 병렬 제어 실습",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID 확인

# 프로젝트 ID를 변수에 저장
PROJECT_ID="위에서 받은 ID"

# plan → execute stage 전환
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 단계로 전환
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
echo "Stage 전환 완료"
```

### 2.2 다중 서버 동시 점검 (Fan-out)

```bash
# 3개 서버에 동시에 시스템 정보 수집 명령 전송
export OPSCLAW_API_KEY=opsclaw-api-key-2026

curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uptime && df -h",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "hostname && uptime && df -h",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "hostname && uptime && df -h",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3개 태스크가 각기 다른 SubAgent에서 실행됨
```

### 2.3 결과 수집 (Fan-in)

```bash
# 전체 evidence를 수집하여 결과를 종합
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# evidence 요약 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${PROJECT_ID}/evidence/summary" | python3 -m json.tool

# PoW 리더보드로 각 에이전트별 작업량 비교
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/leaderboard" | python3 -m json.tool
```

### 2.4 서버별 특화 태스크

```bash
# 각 서버에 역할에 맞는 다른 명령을 전송
export OPSCLAW_API_KEY=opsclaw-api-key-2026

curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nft list ruleset | head -50",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -sk https://localhost:443/api/agents -o /dev/null -w \"%{http_code}\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# secu: 방화벽 규칙 조회, web: JuiceShop 상태 확인, siem: Wazuh API 상태 확인
```

---

## Part 3: Red/Blue Agent 동시 운영 (0:55-1:25)

### 3.1 Purple Team 아키텍처

```
[Master (오케스트레이터)]
        |                  |
        v                  v
  Red Agent           Blue Agent
  (gemma3:12b)        (llama3.1:8b)
  공격 계획/실행        탐지/대응
        |                  |
        v                  v
  web SubAgent        secu SubAgent
```

### 3.2 Red Agent 공격 계획 생성

```bash
# Red Agent가 LLM을 사용해 공격 계획을 수립
curl -s http://192.168.0.105:11434/api/chat \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 보안 점검 전문가(Red Team)입니다. JuiceShop(OWASP 취약 웹앱)에 대한 보안 점검 계획을 수립하세요. 각 단계에서 사용할 구체적 명령어를 포함하세요. 점검 범위: HTTP 응답 확인, 디렉토리 탐색, SQL Injection 테스트."
      },
      {
        "role": "user",
        "content": "JuiceShop(http://10.20.30.80:3000)에 대한 보안 점검 계획을 3단계로 수립해줘. 각 단계마다 curl 명령어를 포함해줘."
      }
    ],
    "stream": false
  }' | python3 -c "
import sys, json
# LLM 응답에서 메시지 내용만 추출
resp = json.load(sys.stdin)
print(resp['message']['content'][:2000])
"
```

### 3.3 Red Agent 공격 실행

```bash
# Red Agent의 공격을 OpsClaw를 통해 실행
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# Red Agent 프로젝트 생성
RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"week10-red-agent","request_text":"Red Agent 공격 시뮬레이션","master_mode":"external"}')
# 프로젝트 ID 추출
RED_PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/${RED_PID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 단계로 전환
curl -s -X POST "http://localhost:8000/projects/${RED_PID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Red Agent 공격 태스크 실행
curl -s -X POST "http://localhost:8000/projects/${RED_PID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000/",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/api/products | head -200",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/admin/application-configuration | head -100",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3단계 공격 시뮬레이션 실행
```

### 3.4 Blue Agent 동시 방어

```bash
# Blue Agent가 동시에 방어 활동 수행
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# Blue Agent 프로젝트 생성
RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"week10-blue-agent","request_text":"Blue Agent 방어 모니터링","master_mode":"external"}')
# 프로젝트 ID 추출
BLUE_PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/${BLUE_PID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 단계로 전환
curl -s -X POST "http://localhost:8000/projects/${BLUE_PID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Blue Agent 방어 태스크 실행
curl -s -X POST "http://localhost:8000/projects/${BLUE_PID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "tail -50 /var/log/suricata/eve.json | python3 -c \"import sys,json; [print(json.dumps(json.loads(l),indent=2)) for l in sys.stdin if json.loads(l).get(\\\"event_type\\\")==\\\"alert\\\"]\" 2>/dev/null || echo no-alerts",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "nft list ruleset | grep -c drop",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -sk -u wazuh-wui:MyS3cr3tP4ssw0rd* https://localhost:55000/security/user/authenticate 2>/dev/null | head -5 || echo wazuh-api-check",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# Blue Agent: Suricata 경보 확인, 방화벽 규칙 수 확인, Wazuh API 상태 확인
```

### 3.5 Red/Blue 결과 비교

```bash
# 양쪽 프로젝트의 evidence를 비교
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== Red Agent 결과 ==="
# Red Agent evidence 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${RED_PID}/evidence/summary" | python3 -m json.tool

echo ""
echo "=== Blue Agent 결과 ==="
# Blue Agent evidence 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${BLUE_PID}/evidence/summary" | python3 -m json.tool
```

---

## Part 4: Agent간 지식 교환 API (1:35-2:10)

### 4.1 지식 교환 개념

OpsClaw는 Agent간 경험(experience)을 공유하는 API를 제공한다.
Red Agent가 발견한 취약점을 Blue Agent가 참조하여 방어를 강화할 수 있다.

```
publish
  Red Agent  | →|  Experience
  (발견자)  |  |  Store (DB)
  pull
  |
  Blue Agent
  (참조자)
```

### 4.2 Experience 게시

```bash
# Red Agent가 발견한 취약점을 Experience로 게시
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# SubAgent의 experience/publish API 사용 (Manager를 통해)
curl -s -X POST "http://localhost:8000/projects/${RED_PID}/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo {\"finding\": \"JuiceShop /rest/admin 접근 가능\", \"severity\": \"high\", \"target\": \"10.20.30.80:3000\", \"timestamp\": \"2026-03-30T10:00:00Z\"}",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# Red Agent의 발견 내용을 기록
```

### 4.3 LLM을 통한 지식 교환

```bash
# Blue Agent가 Red Agent의 발견 내용을 LLM에게 전달하여 대응 방안 수립
curl -s http://192.168.0.105:11434/api/chat \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 보안 방어 전문가(Blue Team)입니다. Red Team이 발견한 취약점에 대한 대응 방안을 수립하세요."
      },
      {
        "role": "user",
        "content": "Red Team 발견 내용:\n1. JuiceShop /rest/admin 엔드포인트 접근 가능 (severity: high)\n2. /api/products에서 전체 상품 정보 노출\n\n이에 대한 방어 대응 방안을 OpsClaw 명령 형태로 3가지 제안해줘."
      }
    ],
    "stream": false
  }' | python3 -c "
import sys, json
# LLM 응답 추출
resp = json.load(sys.stdin)
print(resp['message']['content'][:1500])
"
```

### 4.4 지식 교환 자동화 스크립트

```python
#!/usr/bin/env python3
"""knowledge_exchange.py — Agent간 지식 교환 자동화"""
import json
import time
import requests

MANAGER_URL = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
OLLAMA_URL = "http://192.168.0.105:11434"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}

def create_project(name: str, description: str) -> str:
    """프로젝트를 생성하고 ID를 반환한다."""
    resp = requests.post(
        f"{MANAGER_URL}/projects",
        headers=HEADERS,
        json={
            "name": name,
            "request_text": description,
            "master_mode": "external",
        },
    )
    project_id = resp.json()["id"]
    # plan → execute 전환
    requests.post(f"{MANAGER_URL}/projects/{project_id}/plan", headers=HEADERS)
    requests.post(f"{MANAGER_URL}/projects/{project_id}/execute", headers=HEADERS)
    return project_id

def dispatch_command(project_id: str, command: str, agent_url: str) -> dict:
    """SubAgent에 명령을 전송한다."""
    resp = requests.post(
        f"{MANAGER_URL}/projects/{project_id}/dispatch",
        headers=HEADERS,
        json={"command": command, "subagent_url": agent_url},
    )
    return resp.json()

def ask_llm(model: str, system_prompt: str, user_prompt: str) -> str:
    """Ollama LLM에 질의한다."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        },
    )
    return resp.json()["message"]["content"]

def purple_team_cycle(red_pid: str, blue_pid: str):
    """Red/Blue Agent 1회 교환 사이클을 수행한다."""
    # 1. Red Agent가 정찰 실행
    print("[RED] 정찰 실행...")
    red_result = dispatch_command(
        red_pid,
        'curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:3000/rest/admin/application-configuration',
        "http://10.20.30.80:8002",
    )
    print(f"  결과: {json.dumps(red_result, indent=2, ensure_ascii=False)[:300]}")

    # 2. Red Agent가 LLM으로 분석
    print("[RED] LLM 분석...")
    red_analysis = ask_llm(
        "gemma3:12b",
        "보안 점검 전문가입니다. 발견 내용을 JSON으로 보고하세요.",
        f"HTTP 응답 결과를 분석하세요: {json.dumps(red_result, ensure_ascii=False)[:500]}",
    )
    print(f"  분석: {red_analysis[:300]}")

    # 3. Blue Agent가 Red의 분석을 참조하여 방어
    print("[BLUE] 방어 대응 수립...")
    blue_response = ask_llm(
        "llama3.1:8b",
        "보안 방어 전문가입니다. 구체적 방어 명령을 제안하세요.",
        f"Red Team 분석 결과에 대한 방어 방안을 수립하세요:\n{red_analysis[:500]}",
    )
    print(f"  대응: {blue_response[:300]}")

    return {"red_analysis": red_analysis, "blue_response": blue_response}

if __name__ == "__main__":
    print("=== Purple Team 지식 교환 데모 ===")
    # 실행 시 PROJECT_ID를 인자로 전달
    # 실제 사용 시에는 create_project로 생성
    print("(실제 실행 시 프로젝트 ID 필요)")
```

---

## Part 5: LangGraph 상태기계 워크플로우 (2:10-2:40)

### 5.1 LangGraph 개념

LangGraph는 LLM 애플리케이션을 상태기계(State Machine)로 구성하는 프레임워크이다.
OpsClaw의 프로젝트 라이프사이클도 상태기계로 설계되어 있다.

```
/plan  /execute  /complete
  init | → | plan | → | execute | →  | done
태스크 실행
  |
  SubAgent 1..N
```

### 5.2 LangGraph 기본 구조

```python
#!/usr/bin/env python3
"""langgraph_demo.py — LangGraph 상태기계 기본 구조"""
# LangGraph가 설치되어 있지 않으면 pip install langgraph
from typing import TypedDict, Literal
import json

# LangGraph 임포트 (설치 필요: pip install langgraph)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("LangGraph 미설치 — 개념만 설명합니다")

# 상태 정의
class AgentState(TypedDict):
    """에이전트 워크플로우 상태"""
    stage: str                     # 현재 단계
    task_queue: list               # 실행할 태스크 목록
    results: list                  # 실행 결과
    risk_level: str                # 최고 위험 수준
    approved: bool                 # 승인 여부

def plan_node(state: AgentState) -> AgentState:
    """계획 수립 노드"""
    print("[PLAN] 태스크 계획 수립")
    state["stage"] = "plan"
    state["task_queue"] = [
        {"cmd": "hostname", "risk": "low", "agent": "secu"},
        {"cmd": "nft list ruleset", "risk": "medium", "agent": "secu"},
        {"cmd": "systemctl restart nginx", "risk": "critical", "agent": "web"},
    ]
    # 최고 위험 수준 계산
    risk_order = ["low", "medium", "high", "critical"]
    max_risk = max(state["task_queue"], key=lambda t: risk_order.index(t["risk"]))
    state["risk_level"] = max_risk["risk"]
    return state

def approve_node(state: AgentState) -> AgentState:
    """승인 게이트 노드"""
    print(f"[APPROVE] 최고 위험도: {state['risk_level']}")
    if state["risk_level"] in ("high", "critical"):
        # 시뮬레이션에서는 자동 승인
        print("  -> 사람 승인 필요 (시뮬레이션: 자동 승인)")
        state["approved"] = True
    else:
        state["approved"] = True
    state["stage"] = "approve"
    return state

def execute_node(state: AgentState) -> AgentState:
    """실행 노드"""
    print("[EXECUTE] 태스크 실행")
    state["stage"] = "execute"
    state["results"] = []
    for task in state["task_queue"]:
        # 시뮬레이션 실행 결과
        result = {
            "cmd": task["cmd"],
            "agent": task["agent"],
            "exit_code": 0,
            "dry_run": task["risk"] == "critical" and not state["approved"],
        }
        state["results"].append(result)
        # 각 태스크 실행 결과 출력
        mode = "DRY-RUN" if result["dry_run"] else "EXECUTE"
        print(f"  [{mode}] {task['cmd']} on {task['agent']}")
    return state

def report_node(state: AgentState) -> AgentState:
    """보고 노드"""
    print("[REPORT] 완료 보고서 생성")
    state["stage"] = "done"
    total = len(state["results"])
    success = sum(1 for r in state["results"] if r["exit_code"] == 0)
    # 보고서 요약 출력
    print(f"  총 {total}건 중 {success}건 성공")
    return state

def should_execute(state: AgentState) -> Literal["execute", "end"]:
    """승인 여부에 따라 실행 또는 종료 분기"""
    if state["approved"]:
        return "execute"
    return "end"

if LANGGRAPH_AVAILABLE:
    # 그래프 구성
    graph = StateGraph(AgentState)
    # 노드 추가
    graph.add_node("plan", plan_node)
    graph.add_node("approve", approve_node)
    graph.add_node("execute", execute_node)
    graph.add_node("report", report_node)
    # 엣지 추가
    graph.set_entry_point("plan")
    graph.add_edge("plan", "approve")
    graph.add_conditional_edges("approve", should_execute, {
        "execute": "execute",
        "end": END,
    })
    graph.add_edge("execute", "report")
    graph.add_edge("report", END)
    # 컴파일 및 실행
    app = graph.compile()
    # 초기 상태
    initial_state = {
        "stage": "init",
        "task_queue": [],
        "results": [],
        "risk_level": "low",
        "approved": False,
    }
    print("=== LangGraph 워크플로우 실행 ===")
    # 워크플로우 실행
    final = app.invoke(initial_state)
    print(f"\n최종 상태: {json.dumps(final, indent=2, ensure_ascii=False)}")
else:
    # LangGraph 없이 수동 실행
    print("=== 수동 워크플로우 실행 ===")
    state = {"stage": "init", "task_queue": [], "results": [], "risk_level": "low", "approved": False}
    state = plan_node(state)
    state = approve_node(state)
    state = execute_node(state)
    state = report_node(state)
```

### 5.3 OpsClaw 실제 워크플로우

```bash
# OpsClaw의 실제 프로젝트 라이프사이클 확인
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 프로젝트 상태 전이 실습
# init → plan → execute → completion-report
RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"week10-workflow","request_text":"워크플로우 실습","master_mode":"external"}')
# 프로젝트 ID 추출
WF_PID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project: $WF_PID"

# 1. plan 단계 전환
curl -s -X POST "http://localhost:8000/projects/${WF_PID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; print('Stage:', json.load(sys.stdin).get('stage','?'))"

# 2. execute 단계 전환
curl -s -X POST "http://localhost:8000/projects/${WF_PID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; print('Stage:', json.load(sys.stdin).get('stage','?'))"

# 3. 태스크 실행
curl -s -X POST "http://localhost:8000/projects/${WF_PID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"tasks":[{"order":1,"instruction_prompt":"hostname","risk_level":"low"}],"subagent_url":"http://localhost:8002"}' | python3 -m json.tool

# 4. 완료 보고서 작성
curl -s -X POST "http://localhost:8000/projects/${WF_PID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "멀티에이전트 워크플로우 실습 완료",
    "outcome": "success",
    "work_details": ["3개 서버 병렬 점검 완료", "Red/Blue Agent 동시 운영 성공"]
  }' | python3 -m json.tool

# 5. 프로젝트 replay로 전체 흐름 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${WF_PID}/replay" | python3 -m json.tool
```

---

## Part 6: 종합 실습 + 퀴즈 (2:40-3:00)

### 6.1 종합 과제

다음 시나리오를 OpsClaw를 사용하여 구현하라:

1. 프로젝트 생성 (master_mode=external)
2. 3개 서버(secu, web, siem)에 동시에 상태 점검 명령 전송
3. Red Agent가 web 서버에 보안 점검 수행
4. Blue Agent가 secu 서버에서 방어 상태 확인
5. 전체 결과를 evidence로 수집하고 completion-report 생성

### 6.2 퀴즈

**Q1.** Fan-out과 Fan-in 패턴을 설명하고, OpsClaw에서 어떻게 구현되는지 서술하시오.

**Q2.** Red Agent와 Blue Agent의 역할 차이를 설명하고, 동시에 운영할 때의 이점 3가지를 나열하시오.

**Q3.** 다음 execute-plan 요청에서 각 태스크가 어떤 서버에서 실행되는지 분석하시오:
```json
{
  "tasks": [
    {"order":1, "instruction_prompt":"nft list ruleset", "subagent_url":"http://10.20.30.1:8002"},
    {"order":2, "instruction_prompt":"curl localhost:3000", "subagent_url":"http://10.20.30.80:8002"},
    {"order":3, "instruction_prompt":"df -h"}
  ],
  "subagent_url": "http://localhost:8002"
}
```

**Q4.** LangGraph 상태기계에서 conditional edge의 역할을 설명하고, 보안 에이전트에서의 활용 사례를 2가지 제시하시오.

**Q5.** agent_id가 서버별로 고유해야 하는 이유를 PoW 체인 관점에서 설명하시오.
