# Week 10: Schedule과 Watcher

## 학습 목표

- OpsClaw의 Schedule 기능으로 정기 보안 점검 작업을 자동화한다
- Watcher를 구성하여 실시간 시스템 이상 징후를 감지한다
- Schedule과 Watcher의 차이점과 적절한 사용 시나리오를 구분한다
- 이상 탐지 시 인시던트 프로젝트를 자동 생성하는 파이프라인을 구축한다
- cron 표현식을 작성하고 다양한 스케줄 패턴을 설계한다

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
| 0:00-0:25 | Part 1 | Schedule vs Watcher 개요 | 이론 |
| 0:25-0:55 | Part 2 | Cron 표현식과 Schedule 등록 | 이론+실습 |
| 0:55-1:20 | Part 3 | Schedule 기반 정기 보안 점검 | 실습 |
| 1:20-1:30 | — | 휴식 | — |
| 1:30-2:00 | Part 4 | Watcher 구성과 이상 탐지 | 실습 |
| 2:00-2:35 | Part 5 | 인시던트 자동 생성 파이프라인 | 실습 |
| 2:35-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **Schedule** | cron 기반 정기 실행 작업 | 매일 02:00 보안 점검 |
| **Watcher** | 조건 기반 지속 모니터링 | CPU > 90% → 경보 |
| **Cron 표현식** | 분/시/일/월/요일로 실행 주기를 지정하는 문법 | `0 2 * * *` = 매일 02:00 |
| **Incident** | 보안 이벤트가 탐지되어 대응이 필요한 사건 | SSH 브루트포스 탐지 |
| **Auto-Create** | 이상 탐지 시 프로젝트를 자동 생성하는 기능 | Watcher 조건 충족 → 프로젝트 생성 |
| **Threshold** | 경보 발생 기준 값 | 로그인 실패 5회 이상 |
| **Polling** | 주기적으로 상태를 확인하는 방식 | 5분마다 디스크 사용량 확인 |
| **Event-Driven** | 이벤트 발생 시 즉시 반응하는 방식 | 로그 발생 즉시 분석 |
| **scheduler-worker** | Schedule 작업을 실행하는 OpsClaw 내부 워커 프로세스 | 등록된 cron 작업을 주기적으로 확인하고 실행 |
| **watch-worker** | Watcher를 실행하는 OpsClaw 내부 워커 프로세스 | 등록된 감시 조건을 지속적으로 확인 |
| **Notification** | 이상 탐지 시 발송되는 알림 | Slack, Email, Webhook |
| **Playbook** | 사전 정의된 자동화 작업 절차 | 인시던트 대응 Playbook |
| **jitter** | 스케줄 실행 시 의도적으로 추가하는 시간 편차 | +-30초 (동시 실행 방지) |
| **dead letter** | 실행 실패한 예약 작업을 보관하는 큐 | 3회 실패 → dead letter 이동 |
| **SLA** | Service Level Agreement, 서비스 수준 협약 | 경보 후 15분 내 1차 대응 |

---

## Part 1: Schedule vs Watcher 개요 (0:00-0:25)

### 1.1 자동화의 두 축

자율 보안 시스템에서 자동화는 두 가지 패턴으로 나뉜다:

| 패턴 | Schedule | Watcher |
|------|----------|---------|
| 트리거 | 시간 기반 (cron) | 조건 기반 (threshold) |
| 실행 주기 | 고정 (매일, 매시간 등) | 실시간 모니터링 |
| 목적 | 정기 점검/유지보수 | 이상 탐지/긴급 대응 |
| 예시 | 매일 02:00 패치 확인 | CPU > 95% → 경보 |
| 적합 상황 | 예측 가능한 반복 작업 | 예측 불가능한 이벤트 |

### 1.2 아키텍처에서의 위치

```
  OpsClaw Manager API (:8000)
  | Schedule  |  | Watcher  |
  | (cron 기반)  |  | (조건 기반)  |
  ▼  ▼
  scheduler-worker  watch-worker
  ▼  ▼
  프로젝트 자동 생성 → SubAgent 실행 → Evidence
```

### 1.3 실제 운영 시나리오

**Schedule 사용 시나리오:**
- 매일 02:00: 전체 서버 패치 상태 확인
- 매주 월요일 09:00: 방화벽 규칙 감사
- 매 6시간: SSL 인증서 만료일 확인
- 매월 1일: 보안 규정 준수(compliance) 점검

**Watcher 사용 시나리오:**
- SSH 로그인 실패 5회/분 이상 → 브루트포스 경보
- 디스크 사용량 90% 초과 → 용량 경보
- Wazuh 경보 Level 12+ 발생 → 인시던트 생성
- 웹 응답시간 3초 초과 → 성능 경보

---

## Part 2: Cron 표현식과 Schedule 등록 (0:25-0:55)

### 2.1 Cron 표현식 문법

```
┌───────────── 분 (0-59)
│ ┌───────────── 시 (0-23)
│ │ ┌───────────── 일 (1-31)
│ │ │ ┌───────────── 월 (1-12)
│ │ │ │ ┌───────────── 요일 (0-7, 0과 7은 일요일)
│ │ │ │ │
* * * * *
```

### 2.2 주요 Cron 패턴

| 표현식 | 의미 | 보안 운용 예시 |
|--------|------|---------------|
| `0 2 * * *` | 매일 02:00 | 야간 보안 점검 |
| `*/5 * * * *` | 5분마다 | 시스템 상태 모니터링 |
| `0 9 * * 1` | 매주 월요일 09:00 | 주간 보안 감사 |
| `0 0 1 * *` | 매월 1일 00:00 | 월간 컴플라이언스 점검 |
| `30 */6 * * *` | 6시간마다 (30분) | SSL 인증서 확인 |
| `0 */1 * * *` | 매시간 | 로그 수집 및 분석 |

### 2.3 Schedule 등록 실습

> **실습 목적**: 자율보안 에이전트의 분산 지식 아키텍처를 구축하여 서버별 맞춤 대응을 가능하게 하기 위해 수행한다
>
> **배우는 것**: 서버별 로컬 지식(설정, 이력)과 글로벌 지식(CVE, 위협 인텔)을 결합하여 맥락에 맞는 보안 판단을 내리는 원리를 이해한다
>
> **결과 해석**: 로컬 지식 포함 시 대응 정확도 향상과 오탐 감소로 분산 지식의 효과를 측정한다
>
> **실전 활용**: 대규모 인프라의 서버별 맞춤 보안 정책, 환경별 특화 대응, 지식 기반 보안 자동화에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소
export MGR="http://localhost:8000"

# 1. Schedule 목록 조회 — 현재 등록된 예약 작업 확인
curl -s "$MGR/schedules" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 등록된 Schedule 목록이 출력된다
```

```bash
# 2. 새 Schedule 등록 — 5분마다 secu 서버 방화벽 상태 점검
curl -s -X POST "$MGR/schedules" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "secu-firewall-check-5m",
    "schedule_type": "cron",
    "cron_expr": "*/5 * * * *",
    "metadata": {
      "instruction_prompt": "nft list ruleset | wc -l && echo rules-ok",
      "risk_level": "low",
      "subagent_url": "http://10.20.30.1:8002",
      "description": "5분마다 secu 서버 nftables 규칙 수 확인"
    }
  }' | python3 -m json.tool
# Schedule ID를 확인한다
```

```bash
# 3. 매시간 웹 서버 상태 점검 Schedule 등록
curl -s -X POST "$MGR/schedules" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "web-health-hourly",
    "schedule_type": "cron",
    "cron_expr": "0 */1 * * *",
    "metadata": {
      "instruction_prompt": "curl -so /dev/null -w \"%{http_code}\" http://localhost:3000 && echo ok || echo fail",
      "risk_level": "low",
      "subagent_url": "http://10.20.30.80:8002",
      "description": "매시간 JuiceShop(3000) HTTP 상태 코드 확인"
    }
  }' | python3 -m json.tool
# 매시간 정각에 웹 서버 상태를 확인하는 Schedule이 등록된다
```

```bash
# 4. 매일 새벽 2시 SIEM 로그 요약 Schedule 등록
curl -s -X POST "$MGR/schedules" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "siem-daily-summary",
    "schedule_type": "cron",
    "cron_expr": "0 2 * * *",
    "metadata": {
      "instruction_prompt": "ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -5 || echo log-check-done",
      "risk_level": "low",
      "subagent_url": "http://10.20.30.100:8002",
      "description": "매일 02:00 Wazuh 경보 로그 현황 확인"
    }
  }' | python3 -m json.tool
```

### 2.4 Schedule 관리

```bash
# 5. 등록된 Schedule 목록 재확인
curl -s "$MGR/schedules" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
schedules = data if isinstance(data, list) else data.get('schedules', [])
# 등록된 Schedule 목록 출력
print(f'등록된 Schedule: {len(schedules)}개')
for s in schedules:
    name = s.get('name', 'unnamed')
    cron = s.get('cron_expr', '?')
    enabled = s.get('enabled', False)
    status = 'ACTIVE' if enabled else 'PAUSED'
    print(f'  [{status}] {name}: {cron}')
"
```

---

## Part 3: Schedule 기반 정기 보안 점검 (0:55-1:20)

### 3.1 종합 보안 점검 Schedule 설계

실제 SOC(보안관제센터)에서 운용하는 정기 점검 Schedule을 설계한다.

| 점검 항목 | 주기 | 대상 서버 | 명령어 |
|-----------|------|----------|--------|
| 방화벽 규칙 수 | 5분 | secu | `nft list ruleset \| wc -l` |
| IPS 경보 카운트 | 10분 | secu | `suricata-update list-sources 2>/dev/null; echo done` |
| 웹 서비스 가용성 | 1시간 | web | `curl -so /dev/null -w "%{http_code}" http://localhost:3000` |
| 디스크 사용량 | 30분 | 전체 | `df -h / \| tail -1` |
| 프로세스 이상 | 15분 | 전체 | `ps aux --sort=-%mem \| head -5` |

### 3.2 다중 서버 점검 Schedule

```bash
# 1. 전 서버 디스크 사용량 점검 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week10-disk-check-all",
    "request_text": "전 서버 디스크 사용량 점검 — Schedule 시뮬레이션",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지 전환
curl -s -X POST $MGR/projects/$PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지 전환
curl -s -X POST $MGR/projects/$PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 전 서버 디스크 점검 실행 (Schedule이 실행하는 것과 동일한 패턴)
curl -s -X POST $MGR/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== secu ===\"; df -h / | tail -1; free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== web ===\"; df -h / | tail -1; free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== siem ===\"; df -h / | tail -1; free -h | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 3개 서버의 디스크와 메모리 상태를 순차 수집한다
```

```bash
# 4. 결과 분석 — 디스크 사용량 임계값 확인
curl -s "$MGR/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 각 서버의 디스크 사용량에서 임계값(80%) 초과 여부 확인
print('=== 디스크 사용량 점검 결과 ===')
for ev in data.get('evidences', data.get('evidence', [])):
    stdout = ev.get('stdout', '')
    # 출력에서 사용률 확인
    for line in stdout.split('\\n'):
        if '%' in line:
            print(f'  {line.strip()}')
"
```

### 3.3 Schedule 실행 이력 관리

```bash
# 5. 완료 보고서 작성 — Schedule 실행 결과를 Experience로 보존
curl -s -X POST $MGR/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "전 서버 디스크/메모리 정기 점검 완료",
    "outcome": "success",
    "work_details": [
      "secu(10.20.30.1): 디스크/메모리 정상",
      "web(10.20.30.80): 디스크/메모리 정상",
      "siem(10.20.30.100): 디스크/메모리 정상",
      "임계값(80%) 초과 서버: 없음"
    ]
  }' | python3 -m json.tool
```

---

## Part 4: Watcher 구성과 이상 탐지 (1:30-2:00)

### 4.1 Watcher의 동작 원리

Watcher는 지정된 조건을 주기적으로 확인하고, 임계값을 초과하면 액션을 실행한다.

```
  Watcher 정의
  - check_command: "df / | awk ..."
  - threshold: 80
  - operator: ">"
  - action: "create_project"
  - interval: 300 (5분)
▼ (5분마다 실행)
check_command 실행 → 결과값 추출
▼ (결과 > threshold?)
Yes: action 실행
No:  대기 후 재확인
```

### 4.2 Watcher 등록 실습

```bash
# 1. Watcher 목록 조회 — 현재 등록된 Watcher 확인
curl -s "$MGR/watchers" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# 2. 디스크 사용량 Watcher 등록 — web 서버 80% 초과 시 경보
curl -s -X POST "$MGR/watchers" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "web-disk-high",
    "watch_type": "threshold",
    "metadata": {
      "check_command": "df / | awk \"NR==2{print \\$5}\" | tr -d \"%\"",
      "threshold": 80,
      "operator": ">",
      "subagent_url": "http://10.20.30.80:8002",
      "interval_seconds": 300,
      "action": "create_project",
      "action_config": {
        "project_name": "auto-disk-alert-web",
        "request_text": "web 서버 디스크 사용량 80% 초과 탐지 — 자동 생성"
      },
      "description": "web 서버 디스크 80% 초과 시 인시던트 자동 생성"
    }
  }' | python3 -m json.tool
# Watcher ID를 확인한다
```

```bash
# 3. SSH 브루트포스 Watcher — secu 서버에서 로그인 실패 감시
curl -s -X POST "$MGR/watchers" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "secu-ssh-brute",
    "watch_type": "threshold",
    "metadata": {
      "check_command": "journalctl -u sshd --since \"5 min ago\" --no-pager 2>/dev/null | grep -c \"Failed password\" || echo 0",
      "threshold": 5,
      "operator": ">=",
      "subagent_url": "http://10.20.30.1:8002",
      "interval_seconds": 300,
      "action": "create_project",
      "action_config": {
        "project_name": "auto-ssh-brute-alert",
        "request_text": "SSH 브루트포스 탐지 — 5분간 로그인 실패 5회 이상"
      },
      "description": "5분간 SSH 로그인 실패 5회 이상 시 인시던트 생성"
    }
  }' | python3 -m json.tool
```

```bash
# 4. Wazuh 고위험 경보 Watcher — Level 12 이상 경보 감시
curl -s -X POST "$MGR/watchers" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "project_name": "siem-high-alert",
    "watch_type": "threshold",
    "metadata": {
      "check_command": "grep -c \"level.*\\\"1[2-5]\\\"\" /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 0",
      "threshold": 1,
      "operator": ">=",
      "subagent_url": "http://10.20.30.100:8002",
      "interval_seconds": 300,
      "action": "create_project",
      "action_config": {
        "project_name": "auto-wazuh-high-alert",
        "request_text": "Wazuh Level 12+ 고위험 경보 탐지 — 자동 분석 필요"
      },
      "description": "Wazuh Level 12 이상 경보 발생 시 분석 프로젝트 생성"
    }
  }' | python3 -m json.tool
```

### 4.3 Watcher 상태 확인

```bash
# 5. 등록된 Watcher 목록 확인
curl -s "$MGR/watchers" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
watchers = data if isinstance(data, list) else data.get('watchers', [])
# 등록된 Watcher 현황 출력
print(f'등록된 Watcher: {len(watchers)}개')
for w in watchers:
    name = w.get('name', 'unnamed')
    threshold = w.get('threshold', '?')
    op = w.get('operator', '?')
    enabled = w.get('enabled', False)
    status = 'ACTIVE' if enabled else 'PAUSED'
    print(f'  [{status}] {name}: threshold {op} {threshold}')
"
```

---

## Part 5: 인시던트 자동 생성 파이프라인 (2:00-2:35)

### 5.1 전체 파이프라인 설계

```
Watcher 감시
     │
     ▼ (임계값 초과)
인시던트 프로젝트 자동 생성
     │
     ▼
자동 조사 태스크 실행
     │
     ▼
Evidence 기록 + LLM 분석
     │
     ▼
Slack/Email 알림 발송
     │
     ▼
대응 권고 + Experience 축적
```

### 5.2 인시던트 자동 대응 시뮬레이션

Watcher가 이상을 탐지했다고 가정하고, 자동 대응 파이프라인을 수동으로 실행한다.

```bash
# 1. 인시던트 프로젝트 생성 (Watcher가 자동 생성하는 것을 시뮬레이션)
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "auto-incident-ssh-brute-sim",
    "request_text": "[AUTO] SSH 브루트포스 탐지 — secu(10.20.30.1)에서 5분간 로그인 실패 12회 발생. 자동 조사 및 대응 필요.",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export INCIDENT_PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$INCIDENT_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$INCIDENT_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 자동 조사 태스크 실행 — 인시던트 원인 분석
curl -s -X POST $MGR/projects/$INCIDENT_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "journalctl -u sshd --since \"30 min ago\" --no-pager | grep \"Failed password\" | awk \"{print \\$11}\" | sort | uniq -c | sort -rn | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "lastb 2>/dev/null | head -20 || echo no-lastb-data",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "nft list ruleset 2>/dev/null | grep -c \"drop\" || echo 0",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 공격 IP, 실패 계정, 현재 방화벽 차단 규칙 수를 조사한다
```

### 5.3 LLM 기반 인시던트 분석

```bash
# 4. Evidence 수집 후 LLM으로 인시던트 분석
curl -s "$MGR/projects/$INCIDENT_PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /tmp/incident_evidence.json

# 5. LLM에게 인시던트 분석 요청
python3 -c "
import json, requests

# Evidence 로드
with open('/tmp/incident_evidence.json') as f:
    evidence = json.load(f)

# Evidence를 텍스트로 변환
evidence_text = json.dumps(evidence, indent=2, ensure_ascii=False)[:2000]

# LLM에게 분석 요청
resp = requests.post(
    'http://192.168.0.105:11434/v1/chat/completions',
    json={
        'model': 'gemma3:12b',
        'messages': [
            {'role': 'system', 'content': '보안관제 전문가. 인시던트 증적을 분석하여 위험도, 공격자 정보, 권고 대응을 JSON으로 출력하라.'},
            {'role': 'user', 'content': f'다음 인시던트 Evidence를 분석하라:\\n{evidence_text}'}
        ],
        'temperature': 0.2,
        'max_tokens': 600
    }
)
# LLM 분석 결과 출력
print(resp.json()['choices'][0]['message']['content'])
"
# LLM이 인시던트를 분석하여 위험도와 대응 권고를 생성한다
```

### 5.4 인시던트 완료 보고

```bash
# 6. 인시던트 완료 보고서 작성
curl -s -X POST $MGR/projects/$INCIDENT_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "SSH 브루트포스 인시던트 자동 조사 완료",
    "outcome": "success",
    "work_details": [
      "[탐지] Watcher: 5분간 SSH 로그인 실패 12회 탐지",
      "[조사] 공격 IP 분석, 실패 계정 확인, 방화벽 상태 점검",
      "[분석] LLM 분석: 외부 IP에서 root 계정 브루트포스 시도",
      "[권고] nftables rate-limit 규칙 추가, fail2ban 활성화"
    ]
  }' | python3 -m json.tool
# 인시던트 대응 결과가 Experience DB에 축적된다
```

---

## Part 6: 종합 실습 + 퀴즈 (2:35-3:00)

### 6.1 종합 실습 과제

**과제**: 다음 3가지 자동화를 설계하고 시뮬레이션하라.

1. **Schedule**: 15분마다 3개 서버의 CPU 로드 점검
2. **Watcher**: web 서버 HTTP 응답코드가 200이 아닌 경우 경보
3. **인시던트 파이프라인**: Watcher 트리거 시 자동 조사 + LLM 분석

```bash
# 종합 실습 힌트
# 1. CPU 로드 점검 Schedule
# cron: */15 * * * *
# command: "uptime | awk -F'load average:' '{print $2}' | awk -F, '{print $1}'"

# 2. HTTP 상태 Watcher
# check_command: "curl -so /dev/null -w '%{http_code}' http://localhost:3000"
# threshold: 200, operator: "!="

# 3. 인시던트 파이프라인: 프로젝트 생성 → plan → execute → execute-plan → completion-report
```

### 6.2 퀴즈 (4지선다)

**문제 1.** Schedule과 Watcher의 핵심적인 차이점은?

- A) Schedule은 Python으로, Watcher는 Go로 구현되어 있다
- B) Schedule은 시간 기반 트리거, Watcher는 조건 기반 트리거이다
- C) Schedule은 읽기 전용이고, Watcher는 쓰기도 가능하다
- D) Schedule은 로컬 실행, Watcher는 원격 실행만 지원한다

**정답: B) Schedule은 시간 기반 트리거, Watcher는 조건 기반 트리거이다**

---

**문제 2.** Cron 표현식 `0 */6 * * *`의 의미는?

- A) 6분마다 실행
- B) 매일 6시에 실행
- C) 6시간마다 정각에 실행
- D) 매주 6번 실행

**정답: C) 6시간마다 정각에 실행**

---

**문제 3.** Watcher의 `operator: ">="`, `threshold: 5` 설정에서 경보가 발생하는 조건은?

- A) check_command 결과가 5 미만일 때
- B) check_command 결과가 정확히 5일 때만
- C) check_command 결과가 5 이상일 때
- D) check_command가 5번 이상 실행되었을 때

**정답: C) check_command 결과가 5 이상일 때**

---

**문제 4.** 인시던트 자동 생성 파이프라인의 올바른 순서는?

- A) 경보 → LLM 분석 → Evidence → 프로젝트 생성
- B) Watcher 탐지 → 프로젝트 자동 생성 → 조사 실행 → Evidence 기록 → 분석
- C) Schedule 실행 → Evidence → Watcher → 프로젝트 생성
- D) LLM 분석 → Watcher → 프로젝트 생성 → Evidence

**정답: B) Watcher 탐지 → 프로젝트 자동 생성 → 조사 실행 → Evidence 기록 → 분석**

---

**문제 5.** Cron 표현식 `30 2 * * 1`이 실행되는 시점은?

- A) 매일 02:30
- B) 매주 월요일 02:30
- C) 매월 1일 02:30
- D) 매월 2일 01:30

**정답: B) 매주 월요일 02:30**

---

### 6.3 다음 주 예고

Week 11에서는 **자율 Blue Agent**를 학습한다.
LLM 기반 실시간 경보 분석과 5분 주기 자동 관제, Slack 알림 연동을 실습한다.
