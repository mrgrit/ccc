# Week 03: OpsClaw 프로젝트 생명주기

## 학습 목표
- OpsClaw 프로젝트의 6단계 생명주기를 완전히 이해한다
- 각 Stage 전환 규칙과 제약 조건을 설명할 수 있다
- Evidence 기록 체계와 감사 추적 원리를 파악한다
- 프로젝트 생성부터 종료까지 전 과정을 직접 실행할 수 있다
- Completion Report와 Replay를 활용한 사후 분석을 수행할 수 있다

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
| **프로젝트** | Project | OpsClaw에서 하나의 작업 단위를 관리하는 컨테이너 | 업무 처리 건 |
| **Stage** | Stage | 프로젝트의 현재 진행 상태 | 주문 처리 상태 (접수→조리→배달→완료) |
| **Evidence** | Evidence | 실행 결과를 기록한 감사 증거 | 작업 완료 증빙 서류 |
| **Completion Report** | Completion Report | 프로젝트 종료 시 작성하는 요약 보고서 | 프로젝트 최종 보고서 |
| **Replay** | Replay | 프로젝트의 전체 이력을 시간순 재생 | 블랙박스 재생 |
| **State Machine** | State Machine | 정해진 규칙에 따라 상태가 전이되는 시스템 | 자판기 (동전→선택→배출) |
| **master_mode** | master_mode | 프로젝트 실행 모드 (native/external) | 자율주행 모드 vs 수동 모드 |
| **request_text** | request_text | 프로젝트의 작업 요청 내용 | 업무 지시서 |
| **risk_level** | risk_level | 작업의 위험 수준 (low/medium/high/critical) | 작업 위험도 등급 |
| **dry_run** | dry_run | 실제 실행 없이 시뮬레이션만 수행 | 소방 훈련 (실제 불 없이) |
| **감사 추적** | Audit Trail | 모든 작업의 이력을 추적 가능하게 기록 | CCTV 녹화 |
| **멱등성** | Idempotency | 같은 작업을 여러 번 실행해도 결과가 동일 | 엘리베이터 버튼 여러 번 눌러도 한 번만 이동 |
| **Stage Gate** | Stage Gate | 다음 단계로 진행하기 위한 조건/검증 | 공항 보안 검색대 |
| **POST** | POST | HTTP 요청 메서드 (데이터 생성/전송) | 편지 보내기 |
| **GET** | GET | HTTP 요청 메서드 (데이터 조회) | 편지 받기 |
| **JSON** | JavaScript Object Notation | 데이터 교환 형식 | 구조화된 메모 양식 |

---

# Week 03: OpsClaw 프로젝트 생명주기

## 학습 목표
- 6단계 생명주기를 완전히 이해한다
- Stage 전환 규칙과 제약을 설명할 수 있다
- Evidence 체계를 파악한다
- 프로젝트 전 과정을 직접 실행한다

## 전제 조건
- Week 01-02 완료 (OpsClaw API, LLM 기초)
- curl, JSON 기본 이해
- REST API 개념

---

## 1. 프로젝트 생명주기 6단계 (40분)

### 1.1 전체 흐름

OpsClaw 프로젝트는 다음 6단계를 순서대로 거친다:

```
created  | →| planning | →| executing | →| validating | →| reporting | →| closed
  (생성)  |  |  (계획)  |  |  (실행)  |  |  (검증)  |  |  (보고)  |  | (종료)
프로젝트  계획 수립  명령 실행  결과 검증  보고서 작성  아카이브
등록  (수동/AI)  (SubAgent)  (자동/수동)  (completion)
```

### 1.2 각 단계 상세

| 단계 | API 호출 | 목적 | 허용 동작 |
|------|---------|------|----------|
| **created** | `POST /projects` | 프로젝트 등록 | 메타데이터 수정 |
| **planning** | `POST /projects/{id}/plan` | 실행 계획 수립 | 계획 검토, 수정 |
| **executing** | `POST /projects/{id}/execute` | 실제 명령 실행 | dispatch, execute-plan |
| **validating** | 자동 전환 | 결과 검증 | evidence 확인 |
| **reporting** | 자동 전환 | 보고서 작성 | completion-report |
| **closed** | completion-report 후 | 프로젝트 종료 | 조회만 가능 |

### 1.3 Stage 전환 규칙

```
규칙 1: 순방향 전환만 허용
  created → planning → executing → validating → reporting → closed
  (역방향 전환 불가: executing → planning ✗)

규칙 2: Stage 건너뛰기 불가
  created → executing ✗ (planning을 거쳐야 함)

규칙 3: executing 단계에서만 명령 실행 가능
  planning 단계에서 dispatch 호출 → 에러

규칙 4: critical risk_level은 dry_run 강제
  risk_level=critical → 자동으로 dry_run=true
  → "confirmed": true 추가 시 실제 실행
```

### 1.4 master_mode 비교

| 모드 | 계획 주체 | 실행 주체 | 사용 시나리오 |
|------|----------|----------|-------------|
| **external** | 외부 마스터 (Claude Code 등) | Manager → SubAgent | 높은 정확도, 인간 감독 |
| **native** | 내장 LLM (Ollama) | Master → Manager → SubAgent | 완전 자율, 비용 절약 |

---

## 2. Evidence 기록 체계 (30분)

### 2.1 Evidence란

Evidence는 프로젝트에서 수행한 모든 작업의 실행 결과를 기록한 감사 증거이다.

```
┌─────────────────────────────────────┐
│           Evidence Record            │
│                                      │
│  project_id: "abc-123"              │
│  task_order: 1                       │
│  command: "hostname"                 │
│  subagent_url: "http://10.20.30.1"  │
│  exit_code: 0                        │
│  stdout: "secu"                      │
│  stderr: ""                          │
│  started_at: "2026-03-25T10:00:00Z" │
│  completed_at: "2026-03-25T10:00:01Z"│
│  risk_level: "low"                   │
└─────────────────────────────────────┘
```

### 2.2 Evidence의 중요성

| 목적 | 설명 |
|------|------|
| **감사 추적** | 누가 언제 어떤 명령을 실행했는지 추적 |
| **재현성** | 같은 evidence를 기반으로 동일 작업 재실행 가능 |
| **규정 준수** | 보안 점검 결과를 규제 기관에 제출하는 증거 |
| **사후 분석** | 사고 발생 시 어떤 대응이 이루어졌는지 검증 |
| **PoW 연동** | 각 evidence가 PoW 블록과 연결되어 위변조 방지 |

### 2.3 Evidence와 PoW의 관계

```
execute-plan 실행
       │
       ├──→ Task 1 실행 → Evidence #1 기록 → PoW Block #1 생성
       ├──→ Task 2 실행 → Evidence #2 기록 → PoW Block #2 생성
       └──→ Task 3 실행 → Evidence #3 기록 → PoW Block #3 생성
                                                    │
                                              SHA-256 해시 체인
                                              (위변조 불가)
```

---

## 3. 프로젝트 전체 실습: 보안 점검 시나리오 (40분)

### 3.1 시나리오 설정

**목표**: 4대 서버의 보안 상태를 종합 점검하는 프로젝트를 생명주기 전체를 거쳐 실행한다.

점검 항목:
1. 디스크 사용량 확인 (전 서버)
2. 활성 서비스 목록 확인 (전 서버)
3. 방화벽 규칙 확인 (secu)
4. 웹 서비스 응답 확인 (web)
5. SIEM 에이전트 상태 확인 (siem)

> **실습 목적**: OpsClaw의 Playbook 시스템으로 보안 대응 절차를 자동화하기 위해 수행한다
>
> **배우는 것**: Playbook의 step 구조(순서, 명령, 조건)와 execute-plan API로 다중 서버에 순차 명령을 실행하는 원리를 이해한다
>
> **결과 해석**: 각 step의 exit_code가 0이면 성공, 0이 아니면 실패이며, evidence에서 실행 로그를 확인한다
>
> **실전 활용**: 인시던트 대응 SOP 자동화, 보안 패치 자동 배포, 컴플라이언스 점검 자동화에 활용한다

```bash
# opsclaw 서버 접속
ssh opsclaw@10.20.30.201
```

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

### 3.2 Stage 1: created (프로젝트 생성)

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week03-security-audit",
    "request_text": "4대 서버 보안 상태 종합 점검: 디스크, 서비스, 방화벽, 웹, SIEM",
    "master_mode": "external"
  }' | python3 -m json.tool
# stage: "created" 확인
# 반환된 id를 기록한다
```

```bash
# 프로젝트 ID 설정
export PROJECT_ID="반환된-프로젝트-ID"
# 프로젝트 상세 조회로 stage 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID \
  | python3 -m json.tool
# "stage": "created" 확인
```

### 3.3 Stage 2: planning (계획 수립)

```bash
# plan 단계로 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# "stage": "planning" 확인
```

```bash
# (참고) planning 단계에서 dispatch를 시도하면 에러 발생
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"hostname","subagent_url":"http://localhost:8002"}' \
  | python3 -m json.tool
# 에러: executing 단계가 아니므로 실행 불가
```

### 3.4 Stage 3: executing (실행)

```bash
# execute 단계로 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# "stage": "executing" 확인
```

```bash
# Task 그룹 1: 전 서버 디스크 사용량 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "df -h / | tail -1 && echo --- && free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "df -h / | tail -1 && echo --- && free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "df -h / | tail -1 && echo --- && free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "df -h / | tail -1 && echo --- && free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4대 서버의 디스크/메모리 사용량이 병렬로 수집된다
```

```bash
# Task 그룹 2: 보안 서비스 상태 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 5,
        "instruction_prompt": "sudo nft list ruleset | wc -l && echo rules-count",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000 && echo --- && curl -s -o /dev/null -w \"%{http_code}\" http://localhost:80",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 7,
        "instruction_prompt": "systemctl is-active wazuh-manager 2>/dev/null || echo wazuh-not-found",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 방화벽 규칙 수, 웹서비스 응답 코드, SIEM 상태가 반환된다
```

### 3.5 Evidence 조회

```bash
# evidence 요약 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
# 7개 task의 실행 결과가 모두 기록되어 있다
```

### 3.6 Stage 4-5: validating & reporting

```bash
# 완료 보고서 작성 (validating → reporting → closed 자동 전환)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "4대 서버 보안 상태 종합 점검 완료",
    "outcome": "success",
    "work_details": [
      "4대 서버 디스크/메모리 사용량 정상 확인",
      "secu 방화벽 규칙 수 확인",
      "web JuiceShop(3000) 및 Apache(80) 응답 정상",
      "siem Wazuh Manager 상태 확인",
      "전체 7개 task 실행, evidence 기록 완료"
    ]
  }' | python3 -m json.tool
# stage: "closed" 확인
```

### 3.7 Stage 6: closed (Replay)

```bash
# 프로젝트 전체 이력 재생
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/replay \
  | python3 -m json.tool
# 프로젝트의 전체 생명주기가 시간순으로 출력된다:
# created → planning → executing → (각 task 실행) → closed
```

---

## 4. Stage 전환 오류 실험 (40분)

### 4.1 잘못된 순서로 전환 시도

```bash
# 새 프로젝트 생성 (오류 실험용)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week03-error-test",
    "request_text": "Stage 전환 오류 실험",
    "master_mode": "external"
  }' | python3 -m json.tool
# 새 프로젝트 ID를 기록한다
```

```bash
export ERR_PROJECT="새-프로젝트-ID"
# 실험 1: created에서 바로 execute로 전환 시도
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 예상: planning을 거쳐야 한다는 에러 메시지
```

```bash
# 실험 2: planning으로 전환 후 dispatch 시도
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# planning 단계에서 dispatch 시도
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"hostname","subagent_url":"http://localhost:8002"}' \
  | python3 -m json.tool
# 예상: executing 단계가 아니라는 에러
```

### 4.2 risk_level에 따른 동작 차이

```bash
# execute 단계로 전환
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
```

```bash
# low risk: 즉시 실행
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order": 1, "instruction_prompt": "echo hello-low", "risk_level": "low", "subagent_url": "http://localhost:8002"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 즉시 실행되어 결과가 반환된다
```

```bash
# critical risk: dry_run 강제
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order": 2, "instruction_prompt": "echo hello-critical", "risk_level": "critical", "subagent_url": "http://localhost:8002"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# dry_run=true가 자동 적용되어 실제 실행되지 않는다
```

```bash
# critical risk + confirmed: 실제 실행
curl -s -X POST http://localhost:8000/projects/$ERR_PROJECT/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order": 3, "instruction_prompt": "echo hello-critical-confirmed", "risk_level": "critical", "subagent_url": "http://localhost:8002"}
    ],
    "subagent_url": "http://localhost:8002",
    "confirmed": true
  }' | python3 -m json.tool
# confirmed=true로 인해 실제 실행된다
```

---

## 5. 프로젝트 관리 고급 기능 (30분)

### 5.1 프로젝트 목록 조회 및 필터링

```bash
# 전체 프로젝트 목록 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects | python3 -c "
import sys, json
# 프로젝트 목록을 표 형태로 출력
projects = json.load(sys.stdin)
if isinstance(projects, list):
    print(f\"{'ID':>5} {'Name':30s} {'Stage':12s} {'Mode':10s}\")
    print('-' * 60)
    for p in projects[-10:]:
        pid = str(p.get('id',''))[:5]
        print(f\"{pid:>5} {p.get('name',''):30s} {p.get('stage',''):12s} {p.get('master_mode',''):10s}\")
"
# 최근 10개 프로젝트의 상태가 표시된다
```

### 5.2 PoW 블록 조회

```bash
# 이번 실습에서 생성된 PoW 블록 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$PROJECT_ID" \
  | python3 -c "
import sys, json
# PoW 블록 목록 출력
blocks = json.load(sys.stdin)
if isinstance(blocks, list):
    for b in blocks:
        print(f\"Block #{b.get('id','')} | Hash: {str(b.get('block_hash',''))[:16]}... | Task: {b.get('task_order','')}\")
"
# 각 task에 대응하는 PoW 블록이 생성되어 있다
```

### 5.3 PoW 리더보드

```bash
# 보상 랭킹 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard | python3 -m json.tool
# 각 SubAgent의 누적 보상 점수가 순위별로 출력된다
```

---

## 6. 복습 퀴즈 + 과제 안내 (20분)

### 토론 주제

1. **Stage Gate의 필요성**: planning 단계 없이 바로 실행하면 안 되는 이유는?
2. **Evidence의 법적 가치**: OpsClaw evidence가 실제 보안 감사에서 증거로 인정받으려면 어떤 요건을 충족해야 하는가?
3. **risk_level 기준**: 어떤 작업을 critical로 분류해야 하는가? 기준을 토론하라.

---

## 과제

### 과제 1: 생명주기 완전 실습 (필수)
본인이 설계한 보안 점검 시나리오(최소 5개 task)를 OpsClaw 프로젝트로 생성하여 6단계 전체를 실행하라. evidence 요약과 replay 결과를 제출한다.

### 과제 2: Stage 전환 다이어그램 (필수)
OpsClaw 프로젝트의 State Machine을 직접 그리고, 각 전환에서 발생하는 API 호출과 제약 조건을 표로 정리하라.

### 과제 3: risk_level 정책 설계 (선택)
가상의 보안 운영 환경에서 low/medium/high/critical 각 등급에 해당하는 작업 목록을 10개 이상 분류하고, 분류 기준을 문서화하라.

---

## 검증 체크리스트

- [ ] 프로젝트 6단계(created→planning→executing→validating→reporting→closed)를 순서대로 말할 수 있는가?
- [ ] 각 단계에서 허용되는 동작과 금지되는 동작을 구분하는가?
- [ ] master_mode external과 native의 차이를 설명할 수 있는가?
- [ ] evidence가 무엇이고 왜 필요한지 설명할 수 있는가?
- [ ] risk_level=critical 시 동작(dry_run 강제)을 이해하는가?
- [ ] confirmed=true의 역할을 설명할 수 있는가?
- [ ] completion-report를 작성하여 프로젝트를 종료할 수 있는가?
- [ ] replay로 프로젝트 이력을 확인할 수 있는가?

---

## 다음 주 예고

**Week 04: SubAgent와 원격 실행**
- A2A(Agent-to-Agent) 프로토콜의 구조와 동작 원리
- dispatch(단일 명령)와 execute-plan(병렬 실행) 심화
- 멀티서버 병렬 실행 패턴과 오류 처리
- SubAgent 상태 모니터링과 장애 대응

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** OpsClaw 프로젝트의 올바른 Stage 순서는?
- (a) created → executing → planning → closed  (b) **created → planning → executing → validating → reporting → closed**  (c) planning → created → executing → closed  (d) executing → planning → reporting → closed

**Q2.** planning 단계에서 dispatch를 호출하면?
- (a) 정상 실행  (b) dry_run으로 실행  (c) **에러 발생 (executing 단계가 아님)**  (d) 프로젝트 삭제

**Q3.** risk_level=critical인 task를 실제 실행하려면?
- (a) admin 권한으로 로그인  (b) **execute-plan body에 "confirmed": true 추가**  (c) 별도 인증 없이 가능  (d) 프로젝트를 다시 생성

**Q4.** Evidence의 주요 목적이 아닌 것은?
- (a) 감사 추적  (b) 재현성 보장  (c) PoW 블록과 연결  (d) **SubAgent 자동 배포**

**Q5.** Replay 기능의 용도는?
- (a) 프로젝트 삭제  (b) **프로젝트의 전체 작업 이력을 시간순으로 재생**  (c) 프로젝트 복제  (d) Stage 되돌리기

**정답:** Q1:b, Q2:c, Q3:b, Q4:d, Q5:b

---
---
