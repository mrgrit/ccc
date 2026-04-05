# Week 09: Experience와 4-Layer Memory

## 학습 목표

- OpsClaw의 4계층 메모리 구조(Evidence, Task Memory, Experience, Retrieval)를 이해한다
- Evidence에서 Task Memory로의 자동 승격(auto-promote) 메커니즘을 실습한다
- Experience DB의 FTS(Full-Text Search) 검색을 활용하여 과거 지식을 재활용한다
- 자율 에이전트가 축적된 경험을 기반으로 의사결정하는 과정을 구현한다
- 분산 환경에서 Experience 동기화와 교차 검증의 필요성을 이해한다

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
| 0:00-0:25 | Part 1 | 4-Layer Memory 아키텍처 개요 | 이론 |
| 0:25-0:50 | Part 2 | Evidence 계층 — 실행 증적의 자동 기록 | 이론+실습 |
| 0:50-1:15 | Part 3 | Task Memory와 Auto-Promote | 실습 |
| 1:15-1:25 | — | 휴식 | — |
| 1:25-1:55 | Part 4 | Experience DB와 FTS 검색 | 실습 |
| 1:55-2:30 | Part 5 | Retrieval — 경험 기반 의사결정 | 실습 |
| 2:30-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **Evidence** | OpsClaw가 태스크 실행 시 자동 기록하는 증적 데이터 | stdout, stderr, exit_code, timestamp |
| **Task Memory** | 단일 프로젝트 내에서 태스크 간 공유되는 단기 기억 | "이전 스캔에서 포트 22 열림 확인" |
| **Experience** | 프로젝트를 넘어 장기 보존되는 구조화된 지식 | "SSH 브루트포스 → nftables rate-limit 적용이 효과적" |
| **Retrieval** | Experience DB에서 현재 컨텍스트와 관련된 지식을 검색하는 과정 | FTS로 "SSH 브루트포스" 검색 → 과거 대응 방법 반환 |
| **FTS (Full-Text Search)** | PostgreSQL의 전문 검색 기능으로 텍스트를 토큰화하여 검색 | `to_tsvector('english', content) @@ to_tsquery('ssh & brute')` |
| **Auto-Promote** | 특정 조건 충족 시 Evidence가 자동으로 Experience로 승격 | 성공한 태스크의 결과가 자동 저장 |
| **4-Layer Memory** | Evidence → Task Memory → Experience → Retrieval의 4계층 기억 구조 | 단기 → 중기 → 장기 → 활용 |
| **PoW (Proof of Work)** | 태스크 실행의 무결성을 증명하는 해시 체인 블록 | SHA-256 연결 블록 |
| **execute-plan** | 여러 태스크를 배열로 전달하여 순차 실행하는 API | `POST /projects/{id}/execute-plan` |
| **dispatch** | 단일 명령을 즉시 실행하는 API | `POST /projects/{id}/dispatch` |
| **completion-report** | 프로젝트 완료 시 요약 보고서를 생성하는 API | `POST /projects/{id}/completion-report` |
| **SubAgent** | 실제 명령을 실행하는 원격 에이전트 | http://10.20.30.1:8002 |
| **Manager API** | 프로젝트/실행/증적을 관리하는 중앙 API 서버 | http://localhost:8000 |
| **Embedding** | 텍스트를 벡터로 변환하여 의미적 유사도 검색에 사용 | 384차원 벡터 |
| **tsvector** | PostgreSQL에서 텍스트를 검색 가능한 토큰 벡터로 변환한 것 | `to_tsvector('보안 경보 분석')` |
| **risk_level** | 태스크의 위험도 (low/medium/high/critical) | low: 조회, critical: 삭제 |

---

## Part 1: 4-Layer Memory 아키텍처 개요 (0:00-0:25)

### 1.1 왜 자율 에이전트에게 기억이 필요한가?

인간 보안 운영자는 과거 인시던트 경험을 바탕으로 새로운 사건에 빠르게 대응한다.
자율 보안 에이전트도 동일한 능력이 필요하다.

**기억이 없는 에이전트의 문제점:**
- 매번 동일한 실수를 반복한다
- 과거에 성공한 대응 방법을 재사용하지 못한다
- 컨텍스트가 프로젝트 단위로 소멸되어 학습이 축적되지 않는다

### 1.2 OpsClaw 4-Layer Memory 구조

```
  Layer 4: Retrieval (검색/활용)
  "현재 상황과 유사한 과거 경험을 검색하여 활용"

  Layer 3: Experience (장기 기억)
  "프로젝트를 넘어 영구 보존되는 구조화된 지식"

  Layer 2: Task Memory (단기 기억)
  "프로젝트 내 태스크 간 공유되는 컨텍스트"

  Layer 1: Evidence (증적)
  "태스크 실행의 원시 기록 (stdout/stderr/exit_code)"
```

### 1.3 계층별 특성 비교

| 속성 | Evidence | Task Memory | Experience | Retrieval |
|------|----------|-------------|------------|-----------|
| 수명 | 프로젝트 내 | 프로젝트 내 | 영구 | 실시간 |
| 크기 | 원시 데이터 (KB~MB) | 요약 (수백 바이트) | 구조화 (수 KB) | 쿼리 결과 |
| 생성 | 자동 (실행 시) | 자동 (요약) | Auto-Promote 또는 수동 | 검색 시 |
| 검색 | project_id로 조회 | project_id로 조회 | FTS/벡터 검색 | 컨텍스트 매칭 |

### 1.4 데이터 흐름

```
태스크 실행
  │
  ▼
Evidence 기록 (자동)
  │
  ▼
Task Memory 업데이트 (자동 요약)
  │
  ▼ (Auto-Promote 조건 충족?)
Experience DB 저장 (장기)
  │
  ▼ (새 태스크 시작 시)
Retrieval: FTS로 관련 Experience 검색
  │
  ▼
에이전트 의사결정에 활용
```

---

## Part 2: Evidence 계층 — 실행 증적의 자동 기록 (0:25-0:50)

### 2.1 Evidence란?

Evidence는 OpsClaw가 태스크를 실행할 때 자동으로 기록하는 원시 데이터이다.
모든 명령의 stdout, stderr, exit_code, 실행 시간이 기록된다.

### 2.2 실습: Evidence 생성 및 조회

> **실습 목적**: 자율 Purple Team(Red+Blue) 시뮬레이션을 AI 에이전트로 자동화하는 방법을 체험하기 위해 수행한다
>
> **배우는 것**: Red Agent(공격)와 Blue Agent(방어)가 동시에 동작하는 자율 대결 시뮬레이션의 구조와, 양측의 전략 진화 과정을 이해한다
>
> **결과 해석**: Red의 공격 성공률과 Blue의 차단률 변화 추이로 방어 체계의 강건성을 평가한다
>
> **실전 활용**: 자동화된 보안 테스트 체계 구축, 지속적 보안 검증(Continuous Validation), BAS(Breach & Attack Simulation)에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소 설정
export MGR="http://localhost:8000"

# 1. 프로젝트 생성 — Experience 학습용
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-evidence-lab",
    "request_text": "Evidence 계층 학습 — 보안 점검 명령 실행 및 증적 기록",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 확인하여 변수에 저장한다
```

```bash
# 반환된 project_id를 변수에 저장
export PID="반환된-프로젝트-ID"

# 2. plan → execute 스테이지 전환 (필수)
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$PID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$PID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# 3. 보안 점검 태스크 실행 — 3개 서버에서 시스템 정보 수집
curl -s -X POST $MGR/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uname -a && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "ss -tlnp | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "systemctl status wazuh-manager --no-pager | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3개 서버에서 순차적으로 명령이 실행되고 Evidence가 자동 기록된다
```

### 2.3 Evidence 조회

```bash
# 4. 프로젝트의 전체 Evidence 요약 조회
curl -s "$MGR/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 각 태스크별 stdout, stderr, exit_code, 실행 시간 확인

# 5. 프로젝트 상세 조회 — tasks 배열에서 개별 Evidence 확인
curl -s "$MGR/projects/$PID" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 프로젝트 기본 정보 출력
print(f'프로젝트: {data[\"name\"]}')
print(f'스테이지: {data[\"stage\"]}')
# tasks 배열에서 Evidence 확인
for t in data.get('tasks', []):
    print(f'\\nTask {t.get(\"order\",\"?\")}: {t.get(\"instruction_prompt\",\"\")[:50]}')
    print(f'  exit_code: {t.get(\"exit_code\")}')
    print(f'  stdout 길이: {len(t.get(\"stdout\",\"\"))} bytes')
"
```

### 2.4 Evidence의 한계

Evidence는 원시 데이터이므로 다음과 같은 한계가 있다:
- 프로젝트가 종료되면 접근이 어렵다
- 구조화되지 않은 텍스트 → 검색이 비효율적이다
- 새 프로젝트에서 과거 Evidence를 참조할 수 없다

이러한 한계를 극복하기 위해 상위 계층(Task Memory, Experience)이 필요하다.

---

## Part 3: Task Memory와 Auto-Promote (0:50-1:15)

### 3.1 Task Memory의 역할

Task Memory는 프로젝트 내에서 태스크 간 컨텍스트를 공유하는 중기 기억이다.
이전 태스크의 결과를 요약하여 다음 태스크의 의사결정에 활용한다.

### 3.2 Task Memory 시뮬레이션

실제 OpsClaw에서 Task Memory는 execute-plan 내부에서 자동 관리된다.
여기서는 수동으로 태스크 체이닝을 구현하여 메커니즘을 이해한다.

```bash
# 1. 새 프로젝트 생성 — Task Memory 체이닝 실습
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-task-memory-chain",
    "request_text": "Task Memory 체이닝 — 포트 스캔 후 발견된 서비스 상세 조사",
    "master_mode": "external"
  }' | python3 -m json.tool
# 새 프로젝트 ID 확인
```

```bash
# 반환된 프로젝트 ID를 변수에 저장
export PID2="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$PID2/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$PID2/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 1단계: 포트 스캔 (Task Memory 시작점)
curl -s -X POST $MGR/projects/$PID2/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "ss -tlnp | grep LISTEN | awk \"{print \\$4}\" | sort -u",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
# web 서버의 열린 포트 목록을 수집한다
```

```bash
# 4. Evidence에서 결과 확인 후 다음 태스크에 활용
curl -s "$MGR/projects/$PID2/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Evidence에서 열린 포트 정보를 추출한다
print('=== Task Memory: 이전 태스크 결과 ===')
for ev in data.get('evidences', data.get('evidence', [])):
    stdout = ev.get('stdout', '')
    if stdout:
        print(stdout[:500])
"
# 이 결과를 바탕으로 다음 태스크의 명령을 결정한다
```

```bash
# 5. 2단계: 발견된 포트의 서비스 상세 조사 (Task Memory 활용)
curl -s -X POST $MGR/projects/$PID2/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -sI http://localhost:3000 | head -10 && echo --- && curl -sI http://localhost:80 | head -10",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
# 1단계에서 발견된 포트 3000(JuiceShop)과 80(Apache)의 HTTP 헤더를 확인한다
```

### 3.3 Auto-Promote: Evidence에서 Experience로의 자동 승격

Auto-Promote는 다음 조건을 만족하는 Evidence를 자동으로 Experience DB에 저장한다:

| 조건 | 설명 |
|------|------|
| 성공한 태스크 | exit_code가 0인 경우 |
| 보안 관련 키워드 | "vulnerability", "exploit", "patch", "firewall" 등 |
| 반복 패턴 | 동일 명령이 3회 이상 성공한 경우 |
| 수동 태그 | 사용자가 `promote: true`를 지정한 경우 |

```bash
# 6. Auto-Promote 시뮬레이션 — 성공한 보안 점검 결과를 Experience로 승격
# completion-report를 통해 프로젝트 요약을 Experience로 저장한다
curl -s -X POST $MGR/projects/$PID2/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "web 서버 포트 스캔 → 서비스 식별 완료",
    "outcome": "success",
    "work_details": [
      "web(10.20.30.80) 열린 포트: 22, 80, 3000",
      "포트 3000: OWASP JuiceShop (Express)",
      "포트 80: Apache httpd",
      "Auto-Promote: 서비스 식별 결과를 Experience DB에 저장"
    ]
  }' | python3 -m json.tool
# completion-report의 work_details가 장기 Experience로 보존된다
```

---

## Part 4: Experience DB와 FTS 검색 (1:25-1:55)

### 4.1 Experience DB 구조

Experience DB는 PostgreSQL 기반으로, 다음 필드를 가진다:

| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | 고유 식별자 |
| agent_id | TEXT | 경험을 생성한 SubAgent |
| category | TEXT | 카테고리 (scan, exploit, defense, monitor) |
| title | TEXT | 경험 제목 |
| content | TEXT | 상세 내용 (FTS 검색 대상) |
| tags | TEXT[] | 태그 배열 |
| created_at | TIMESTAMP | 생성 시각 |
| search_vector | tsvector | FTS용 검색 벡터 (자동 생성) |

### 4.2 Experience 축적 실습

```bash
# 1. 보안 점검 프로젝트 실행 — 여러 서버의 보안 상태를 점검하여 Experience를 축적
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-experience-accumulation",
    "request_text": "3개 서버 보안 점검 후 Experience DB에 결과 축적",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 PID3에 저장
```

```bash
export PID3="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$PID3/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$PID3/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 종합 보안 점검 — 방화벽/웹서버/SIEM 상태를 한 번에 수집
curl -s -X POST $MGR/projects/$PID3/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nft list ruleset | head -30",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "suricata --build-info | grep -E \"(Version|Features)\" | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -sk https://localhost:443/api/agents -H \"Authorization: Bearer $(cat /var/ossec/api_token 2>/dev/null || echo none)\" | head -20 || echo Wazuh-API-check-done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 방화벽 규칙, Suricata 버전, Wazuh 에이전트 상태를 수집한다
```

### 4.3 FTS (Full-Text Search) 검색 원리

PostgreSQL의 FTS는 텍스트를 토큰(lexeme)으로 분해하고 인덱싱한다.

```sql
-- FTS 검색 예시 (PostgreSQL)
-- 'nftables'와 'firewall'이 포함된 Experience 검색
SELECT title, content
FROM experiences
WHERE search_vector @@ to_tsquery('english', 'nftables & firewall')
ORDER BY ts_rank(search_vector, to_tsquery('english', 'nftables & firewall')) DESC
LIMIT 5;
```

### 4.4 OpsClaw API를 통한 Experience 검색

```bash
# 4. Evidence 요약 조회 — 축적된 보안 점검 결과 확인
curl -s "$MGR/projects/$PID3/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Evidence 전체를 순회하며 주요 정보 출력
print('=== Experience 후보 (성공한 태스크) ===')
for i, ev in enumerate(data.get('evidences', data.get('evidence', [])), 1):
    ec = ev.get('exit_code', -1)
    status = 'SUCCESS' if ec == 0 else 'FAILED'
    print(f'{i}. [{status}] {ev.get(\"command\",ev.get(\"instruction\",\"\"))[:60]}')
"

# 5. 프로젝트 Replay — 실행 과정을 시간순으로 재현
curl -s "$MGR/projects/$PID3/replay" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# Replay는 태스크 실행 순서, 소요 시간, 결과를 타임라인으로 보여준다
```

### 4.5 PoW 블록과 Experience의 연결

```bash
# 6. PoW 블록 조회 — 태스크 실행의 무결성 증명 확인
curl -s "$MGR/pow/blocks?agent_id=http://10.20.30.1:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
# 최근 3개 블록의 해시 체인 확인
print(f'총 PoW 블록: {len(blocks)}개')
for b in blocks[-3:]:
    print(f'  Block {b.get(\"height\",\"?\")}: hash={b.get(\"hash\",\"\")[:16]}... prev={b.get(\"prev_hash\",\"\")[:16]}...')
"
# PoW 블록은 Experience의 신뢰성을 보장한다
```

---

## Part 5: Retrieval — 경험 기반 의사결정 (1:55-2:30)

### 5.1 Retrieval의 동작 원리

Retrieval은 새로운 태스크를 시작할 때 Experience DB에서 관련 지식을 검색한다.
검색된 Experience는 LLM의 컨텍스트에 포함되어 의사결정을 보조한다.

```
새 인시던트 발생: "SSH 브루트포스 탐지"
       │
       ▼
Retrieval: Experience DB 검색
  "SSH" AND "브루트포스" → 2건 매칭
       │
       ▼
과거 경험 #1: "nftables rate-limit 적용으로 차단 성공"
과거 경험 #2: "fail2ban 설치 후 재발 방지 확인"
       │
       ▼
에이전트: 경험을 참조하여 최적 대응 방안 선택
```

### 5.2 Retrieval 파이프라인 실습

```bash
# 1. 새 프로젝트 — SSH 브루트포스 대응 시나리오
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-retrieval-ssh-brute",
    "request_text": "SSH 브루트포스 탐지 후 과거 Experience 기반 자동 대응",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PID4="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$PID4/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$PID4/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. Step 1: 현재 SSH 로그인 실패 현황 조사 (Evidence 수집)
curl -s -X POST $MGR/projects/$PID4/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "journalctl -u sshd --since \"1 hour ago\" --no-pager | grep -c \"Failed password\" || echo 0",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# SSH 로그인 실패 횟수를 카운트한다
```

```bash
# 4. Step 2: LLM에게 과거 Experience를 포함하여 대응 방안 질의
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "보안 운영 전문가. 과거 경험을 참조하여 최적의 대응 방안을 제시하라."
      },
      {
        "role": "user",
        "content": "현재 상황: secu 서버(10.20.30.1)에서 SSH 브루트포스 시도 탐지.\n\n과거 Experience:\n1. nftables rate-limit 규칙 적용 → SSH 브루트포스 95% 감소\n2. fail2ban 설치 → 반복 공격자 자동 차단\n3. SSH 포트 변경 → 스캔 기반 공격 차단\n\n위 경험을 참조하여 최적의 대응 방안을 3단계로 제시하라. 각 단계에 실행할 명령어를 포함하라."
      }
    ],
    "temperature": 0.3,
    "max_tokens": 800
  }' | python3 -c "
import sys, json
resp = json.load(sys.stdin)
# LLM 응답에서 대응 방안 출력
print(resp['choices'][0]['message']['content'])
"
# LLM이 과거 Experience를 참조하여 구체적인 명령어와 함께 대응 방안을 생성한다
```

```bash
# 5. Step 3: LLM 추천 대응 방안 중 rate-limit 적용 (Experience 기반 실행)
curl -s -X POST $MGR/projects/$PID4/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "nft list chain inet filter input 2>/dev/null | grep -c \"ct state\" || echo nftables-check-done",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# 현재 nftables 규칙 상태를 확인한다 (실제 변경은 승인 후)
```

### 5.3 Experience 축적과 Retrieval의 선순환

```
실행 → Evidence → Task Memory → Experience (축적)
                                     │
                                     ▼
새 인시던트 → Retrieval (검색) → 의사결정 개선
                                     │
                                     ▼
                            더 나은 실행 → 더 나은 Experience
```

이 선순환이 자율 보안 에이전트의 **학습 능력**의 핵심이다.

---

## Part 6: 종합 실습 + 퀴즈 (2:30-3:00)

### 6.1 종합 실습: 4-Layer Memory 전체 파이프라인

**과제**: 다음 시나리오를 완성하라.

1. 프로젝트 생성 (name: `week09-final-lab`)
2. 3개 서버에서 보안 점검 태스크 실행 (execute-plan)
3. Evidence 요약 조회
4. 성공한 태스크 결과를 LLM으로 요약 (Experience 후보 생성)
5. completion-report 작성

```bash
# 종합 실습 템플릿
# 1. 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-final-lab",
    "request_text": "4-Layer Memory 종합 실습",
    "master_mode": "external"
  }' | python3 -m json.tool

# 2. (학생 작성) 스테이지 전환 + execute-plan 작성
# TODO: plan → execute → execute-plan

# 3. (학생 작성) Evidence 조회 + LLM 요약
# TODO: evidence/summary → Ollama API로 요약 생성

# 4. (학생 작성) completion-report 작성
# TODO: 요약, outcome, work_details 포함
```

### 6.2 퀴즈 (4지선다)

**문제 1.** OpsClaw 4-Layer Memory에서 프로젝트를 넘어 영구 보존되는 계층은?

- A) Evidence
- B) Task Memory
- C) Experience
- D) Retrieval

**정답: C) Experience**

---

**문제 2.** Auto-Promote가 Evidence를 Experience로 승격하는 조건이 아닌 것은?

- A) exit_code가 0인 성공한 태스크
- B) 보안 관련 키워드가 포함된 결과
- C) 실행 시간이 10초 이상인 태스크
- D) 사용자가 promote: true를 지정한 태스크

**정답: C) 실행 시간이 10초 이상인 태스크**

---

**문제 3.** PostgreSQL FTS에서 "SSH"와 "brute"를 모두 포함하는 문서를 검색하는 올바른 쿼리는?

- A) `to_tsquery('ssh | brute')`
- B) `to_tsquery('ssh & brute')`
- C) `to_tsquery('ssh + brute')`
- D) `to_tsquery('ssh brute')`

**정답: B) `to_tsquery('ssh & brute')`**

---

**문제 4.** Retrieval 계층의 주요 목적은?

- A) Evidence를 삭제하여 저장 공간을 확보한다
- B) 과거 Experience를 검색하여 현재 의사결정에 활용한다
- C) SubAgent의 네트워크 연결을 관리한다
- D) PoW 블록의 해시를 검증한다

**정답: B) 과거 Experience를 검색하여 현재 의사결정에 활용한다**

---

**문제 5.** 4-Layer Memory의 데이터 흐름 순서로 올바른 것은?

- A) Evidence → Experience → Task Memory → Retrieval
- B) Task Memory → Evidence → Retrieval → Experience
- C) Evidence → Task Memory → Experience → Retrieval
- D) Retrieval → Experience → Evidence → Task Memory

**정답: C) Evidence → Task Memory → Experience → Retrieval**

---

### 6.3 다음 주 예고

Week 10에서는 **Schedule과 Watcher**를 학습한다.
정기 작업 자동화(cron)와 지속 모니터링(Watcher)으로 인시던트를 자동 생성하는 방법을 다룬다.
