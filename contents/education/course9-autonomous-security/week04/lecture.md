# Week 04: SubAgent와 원격 실행

## 학습 목표
- A2A(Agent-to-Agent) 프로토콜의 구조와 동작 원리를 이해한다
- dispatch(단일 명령)와 execute-plan(병렬 실행)의 차이와 적절한 사용 시나리오를 구분한다
- 멀티서버 병렬 실행 패턴을 설계하고 실행할 수 있다
- SubAgent 상태 모니터링 및 장애 시 대응 방법을 파악한다
- subagent_url을 활용한 서버별 타겟 실행을 능숙하게 수행한다

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
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (자율보안시스템 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SubAgent** | SubAgent | 원격 서버에서 명령을 실행하는 하위 에이전트 | 현장에 파견된 요원 |
| **A2A 프로토콜** | Agent-to-Agent Protocol | 에이전트 간 표준 통신 규약 | 무전기 교신 규약 |
| **dispatch** | dispatch | 단일 서버에 단일 명령을 전송·실행 | 택배 1건 배송 |
| **execute-plan** | execute-plan | 여러 서버에 여러 명령을 병렬 실행 | 택배 다건 동시 배송 |
| **subagent_url** | subagent_url | SubAgent의 네트워크 주소 | 요원의 위치/주소 |
| **병렬 실행** | Parallel Execution | 여러 작업을 동시에 실행 | 여러 줄 동시에 계산 |
| **순차 실행** | Sequential Execution | 작업을 하나씩 순서대로 실행 | 줄 서서 차례로 |
| **Health Check** | Health Check | 서비스의 생존 상태를 확인 | 맥박 확인 |
| **Timeout** | Timeout | 응답을 기다리는 최대 시간 | 택배 배달 기한 |
| **Idempotent** | Idempotent | 같은 작업을 여러 번 실행해도 결과가 동일 | 전등 스위치 (켜진 상태에서 켜기 = 변화 없음) |
| **Fan-out** | Fan-out | 하나의 요청을 여러 대상에 동시 전송 | 방송 (1→다수) |
| **Fan-in** | Fan-in | 여러 대상의 응답을 하나로 취합 | 설문 결과 집계 |
| **exit_code** | exit_code | 명령 실행 결과 코드 (0=성공) | 시험 합격/불합격 |
| **stdout** | Standard Output | 명령의 표준 출력 | 답변 내용 |
| **stderr** | Standard Error | 명령의 오류 출력 | 에러 메시지 |
| **fallback** | Fallback | 주 경로 실패 시 대안 경로 | 비상구 |

---

# Week 04: SubAgent와 원격 실행

## 학습 목표
- A2A 프로토콜 구조를 이해한다
- dispatch와 execute-plan의 차이를 구분한다
- 멀티서버 병렬 실행을 설계·실행한다
- SubAgent 장애 대응을 수행한다

## 전제 조건
- Week 01-03 완료 (프로젝트 생명주기)
- curl, JSON 능숙
- 기본 리눅스 명령어

---

## 1. A2A 프로토콜과 SubAgent 구조 (40분)

### 1.1 A2A 프로토콜이란

A2A(Agent-to-Agent)는 OpsClaw에서 Manager와 SubAgent 사이의 통신 규약이다.

```
Manager API (:8000)
    │
    │ POST /a2a/invoke
    │ {
    │   "tool": "run_command",
    │   "params": {"command": "hostname"}
    │ }
    │
    ↓
SubAgent (:8002)
    │
    │ 명령 실행
    │ $ hostname
    │
    │ 응답 반환
    │ {
    │   "exit_code": 0,
    │   "stdout": "secu",
    │   "stderr": ""
    │ }
    ↓
Manager API
    │
    │ Evidence 기록
    │ PoW 블록 생성
    ↓
```

### 1.2 SubAgent 엔드포인트

각 SubAgent는 다음 API를 노출한다:

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 생존 상태 확인 |
| `/a2a/invoke` | POST | Tool 호출 (run_command 등) |
| `/a2a/invoke_llm` | POST | LLM 호출 (Ollama 연동) |
| `/a2a/analyze` | POST | 데이터 분석 요청 |

### 1.3 SubAgent 배치 현황

```
[Internal Network: 10.20.30.0/24]

  secu (10.20.30.1)       web (10.20.30.80)       siem (10.20.30.100)
  :8002                   :8002                   :8002
  nftables, Suricata      JuiceShop, Apache       Wazuh, OpenCTI

  opsclaw (10.20.30.201) ← Control Plane
  :8000 :8001 :8002

[외부 네트워크]

  dgx-spark (192.168.0.105)
  :8002 :11434
  GPU + Ollama
```

### 1.4 dispatch vs execute-plan

| 구분 | dispatch | execute-plan |
|------|----------|-------------|
| 대상 | 단일 서버 | 다수 서버 |
| 명령 수 | 1개 | N개 (tasks 배열) |
| 실행 방식 | 동기 | 병렬 |
| 사용 시나리오 | 빠른 확인, 디버깅 | 대규모 점검, 자동화 |
| Evidence | 1건 | N건 (task 당 1건) |
| PoW | 1블록 | N블록 |

**선택 기준**:
- "이 서버의 이것만 확인" → dispatch
- "모든 서버에서 동시에 점검" → execute-plan

---

## 2. SubAgent 상태 모니터링 (30분)

### 2.1 Health Check

> **실습 목적**: SubAgent를 통해 원격 서버에 보안 명령을 안전하게 실행하는 방법을 익히기 위해 수행한다
>
> **배우는 것**: Manager API의 dispatch/execute-plan이 SubAgent URL을 통해 원격 서버에 명령을 전달하는 구조와, risk_level에 따른 안전 제어를 이해한다
>
> **결과 해석**: dispatch 응답의 stdout/stderr/exit_code로 원격 명령 실행 결과를 판단하고, risk_level=critical은 dry_run이 강제된다
>
> **실전 활용**: 다중 서버 보안 자동화, 원격 패치 관리, 분산 환경의 보안 운영 자동화에 활용한다

```bash
# opsclaw 서버 접속
ssh opsclaw@10.20.30.201
```

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

```bash
# 전체 SubAgent 상태를 한 번에 확인하는 스크립트
for server in "10.20.30.201:8002" "10.20.30.1:8002" "10.20.30.80:8002" "10.20.30.100:8002"; do
  # 각 SubAgent에 health check 요청 (2초 타임아웃)
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://$server/health)
  # 결과 출력 (200이면 정상, 그 외 비정상)
  if [ "$status" = "200" ]; then
    echo "[OK]   $server"
  else
    echo "[FAIL] $server (HTTP $status)"
  fi
done
# 4대 SubAgent의 상태가 한 줄씩 출력된다
```

### 2.2 SubAgent 상세 정보 조회

```bash
# secu SubAgent 상세 정보
curl -s http://10.20.30.1:8002/health | python3 -m json.tool
# hostname, uptime, 지원 tool 목록 등이 반환된다
```

```bash
# web SubAgent 상세 정보
curl -s http://10.20.30.80:8002/health | python3 -m json.tool
```

```bash
# siem SubAgent 상세 정보
curl -s http://10.20.30.100:8002/health | python3 -m json.tool
```

---

## 3. dispatch 심화 실습 (40분)

### 3.1 기본 dispatch

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week04-subagent-practice",
    "request_text": "SubAgent 원격 실행 심화 실습",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID 기록
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"
# stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
```

```bash
# dispatch: secu 서버에서 Suricata 상태 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "systemctl is-active suricata 2>/dev/null && suricata --build-info | head -5 || echo suricata-not-found",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# Suricata의 실행 상태와 빌드 정보가 반환된다
```

### 3.2 서버별 특화 명령

```bash
# secu 서버: 방화벽 통계 조회
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "sudo nft list counters 2>/dev/null || echo no-counters",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# nftables 카운터(패킷/바이트 통계)가 출력된다
```

```bash
# web 서버: JuiceShop 프로세스 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "ps aux | grep -i juice | grep -v grep | head -5",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
# JuiceShop 관련 프로세스 목록이 출력된다
```

```bash
# siem 서버: Wazuh 에이전트 연결 수 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "/var/ossec/bin/agent_control -l 2>/dev/null | tail -10 || echo wazuh-agent-control-not-found",
    "subagent_url": "http://10.20.30.100:8002"
  }' | python3 -m json.tool
# 연결된 Wazuh 에이전트 목록이 출력된다
```

---

## 4. execute-plan 병렬 실행 패턴 (40분)

### 4.1 Fan-out 패턴: 동일 명령을 전 서버에

```bash
# 패턴 1: 전 서버에 동일한 점검 명령 병렬 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo $(hostname): $(uptime -s) / Load: $(cat /proc/loadavg | cut -d\" \" -f1-3) / Disk: $(df -h / | tail -1 | awk \"{print \\$5}\")",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo $(hostname): $(uptime -s) / Load: $(cat /proc/loadavg | cut -d\" \" -f1-3) / Disk: $(df -h / | tail -1 | awk \"{print \\$5}\")",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo $(hostname): $(uptime -s) / Load: $(cat /proc/loadavg | cut -d\" \" -f1-3) / Disk: $(df -h / | tail -1 | awk \"{print \\$5}\")",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo $(hostname): $(uptime -s) / Load: $(cat /proc/loadavg | cut -d\" \" -f1-3) / Disk: $(df -h / | tail -1 | awk \"{print \\$5}\")",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4대 서버의 부팅시간, 로드, 디스크 사용률이 동시에 수집된다
```

### 4.2 특화 패턴: 서버 역할에 맞는 명령

```bash
# 패턴 2: 서버별 역할에 맞는 특화 명령 병렬 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 5,
        "instruction_prompt": "sudo nft list ruleset | grep -c \"rule\" && echo firewall-rules",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code} %{time_total}s\" http://localhost:3000 && echo --- && curl -s -o /dev/null -w \"%{http_code} %{time_total}s\" http://localhost:80",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 7,
        "instruction_prompt": "ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -3 && wc -l /var/ossec/logs/alerts/alerts.log 2>/dev/null || echo no-wazuh",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# secu: 방화벽 규칙 수, web: 웹 응답시간, siem: 경보 로그 크기
```

### 4.3 연쇄 패턴: 결과를 다음 작업에 활용

```bash
# 패턴 3: web 서버 접근 로그 수집 → 분석
# Step 1: 로그 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "tail -50 /var/log/apache2/access.log 2>/dev/null || tail -50 /var/log/httpd/access_log 2>/dev/null || echo no-access-log",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
# 반환된 로그 내용을 다음 단계에서 LLM 분석에 활용할 수 있다
```

### 4.4 오류 처리 패턴

```bash
# 존재하지 않는 SubAgent로 명령 전송 (오류 실험)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "hostname",
    "subagent_url": "http://10.20.30.99:8002"
  }' | python3 -m json.tool
# 예상: 연결 실패 에러 (Connection refused 또는 timeout)
# execute-plan에서 일부 task가 실패해도 나머지는 정상 실행된다
```

---

## 5. 종합 실습: 자동화 보안 점검 시나리오 (30분)

### 5.1 시나리오: "긴급 보안 점검"

외부 공격이 의심되는 상황에서 전체 인프라를 빠르게 점검한다.

```bash
# 긴급 점검: 네트워크 연결, 보안 서비스, 이상 프로세스 동시 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 10,
        "instruction_prompt": "ss -tlnp | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 11,
        "instruction_prompt": "ss -tlnp | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 12,
        "instruction_prompt": "ss -tlnp | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 13,
        "instruction_prompt": "ps aux --sort=-%mem | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 14,
        "instruction_prompt": "last -10 | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 전 서버의 열린 포트, 메모리 사용량 Top 10, 최근 로그인 이력이 수집된다
```

### 5.2 결과 취합 및 보고

```bash
# evidence 요약으로 전체 결과 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

```bash
# 프로젝트 완료
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Week04 SubAgent 원격 실행 실습 완료",
    "outcome": "success",
    "work_details": [
      "4대 SubAgent health check 확인",
      "dispatch로 서버별 특화 명령 실행",
      "execute-plan Fan-out 패턴 (동일 명령 4대 서버)",
      "execute-plan 특화 패턴 (역할별 명령)",
      "긴급 보안 점검 시나리오 5개 task 병렬 실행"
    ]
  }' | python3 -m json.tool
```

---

## 6. 복습 퀴즈 + 과제 안내 (20분)

### 토론 주제

1. **병렬 실행의 리스크**: 4대 서버에 동시에 "service restart" 명령을 보내면 어떤 문제가 발생할 수 있는가?
2. **SubAgent 보안**: SubAgent가 해킹당하면 어떤 위험이 있고, 어떻게 방어하는가?
3. **네트워크 분리**: 내부 네트워크(10.20.30.x)와 외부(192.168.0.x)의 분리 이유와 장단점은?

---

## 과제

### 과제 1: 멀티서버 점검 시나리오 설계 (필수)
최소 8개의 task를 포함하는 보안 점검 시나리오를 설계하라. 3가지 실행 패턴(Fan-out, 특화, 연쇄)을 각각 1개 이상 포함해야 한다. execute-plan JSON을 작성하고 실행 결과를 제출한다.

### 과제 2: SubAgent 장애 대응 매뉴얼 (필수)
SubAgent가 응답하지 않는 상황의 진단 절차를 단계별로 작성하라. health check, 프로세스 확인, 로그 확인, 재시작 순서를 포함한다.

### 과제 3: 실행 시간 비교 (선택)
동일한 5개 명령을 (a) SSH로 순차 실행, (b) dispatch로 순차 실행, (c) execute-plan으로 병렬 실행하여 총 소요 시간을 비교하라.

---

## 검증 체크리스트

- [ ] A2A 프로토콜의 요청/응답 흐름을 설명할 수 있는가?
- [ ] dispatch와 execute-plan의 차이를 3가지 이상 말할 수 있는가?
- [ ] SubAgent health check를 수행할 수 있는가?
- [ ] Fan-out 패턴으로 전 서버 동시 명령을 실행할 수 있는가?
- [ ] 서버별 subagent_url을 정확히 지정할 수 있는가?
- [ ] SubAgent 연결 실패 시 에러 메시지를 해석할 수 있는가?
- [ ] evidence 요약으로 병렬 실행 결과를 확인할 수 있는가?

---

## 다음 주 예고

**Week 05: Playbook 자동화**
- Playbook 설계 원칙과 구조
- Playbook 등록, 실행, 결과 확인
- 결정론적 재현: 같은 Playbook = 같은 결과
- Playbook 버전 관리와 변경 이력 추적

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** dispatch와 execute-plan의 가장 큰 차이는?
- (a) 인증 방식  (b) **dispatch는 단일 명령, execute-plan은 다수 명령 병렬 실행**  (c) 사용 서버  (d) 로그 형식

**Q2.** SubAgent의 기본 포트는?
- (a) 8000  (b) 8001  (c) **8002**  (d) 11434

**Q3.** execute-plan에서 task별로 다른 서버에 명령을 보내려면?
- (a) 프로젝트를 여러 개 생성  (b) **각 task의 subagent_url을 다르게 지정**  (c) SSH로 접속  (d) Manager를 재시작

**Q4.** SubAgent health check의 HTTP 상태 코드가 200이면?
- (a) 서버 과부하  (b) 인증 실패  (c) **정상 작동**  (d) 점검 중

**Q5.** Fan-out 패턴의 장점은?
- (a) 보안 강화  (b) **동일 점검을 전 서버에 동시 실행하여 시간 절약**  (c) 비용 절감  (d) 로그 축소

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:b

---
---
