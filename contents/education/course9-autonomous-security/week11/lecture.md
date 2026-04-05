# Week 11: 자율 Blue Agent

## 학습 목표

- 자율 Blue Agent의 역할과 동작 원리를 이해한다
- LLM 기반 실시간 경보 분석 파이프라인을 구축한다
- 5분 주기 자동 관제 시스템을 OpsClaw로 구현한다
- Slack 알림 연동으로 인시던트 즉시 통보 체계를 완성한다
- Blue Agent의 오탐(False Positive) 처리 전략을 설계한다

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
| 0:00-0:30 | Part 1 | Blue Agent 아키텍처와 역할 | 이론 |
| 0:30-1:00 | Part 2 | LLM 기반 경보 분석 엔진 | 이론+실습 |
| 1:00-1:25 | Part 3 | 5분 주기 자동 관제 구현 | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:05 | Part 4 | Slack 알림 연동 | 실습 |
| 2:05-2:35 | Part 5 | 오탐 처리와 튜닝 전략 | 실습 |
| 2:35-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **Blue Agent** | 방어 측 자율 에이전트 (탐지+대응) | LLM 기반 경보 분석, 자동 차단 |
| **Blue Team** | 보안 방어를 담당하는 팀 | SOC 관제, 인시던트 대응 |
| **SOAR** | Security Orchestration, Automation and Response | 보안 오케스트레이션 자동화 |
| **경보 피로 (Alert Fatigue)** | 과도한 경보로 인해 중요 경보를 놓치는 현상 | 하루 1만건 경보 → 관제사 마비 |
| **False Positive** | 오탐 — 정상을 공격으로 잘못 판정 | 정상 로그인을 브루트포스로 판정 |
| **True Positive** | 정탐 — 실제 공격을 올바르게 탐지 | 실제 스캔 행위를 탐지 |
| **Triage** | 경보 우선순위 분류 | Critical > High > Medium > Low |
| **Enrichment** | 경보에 추가 정보를 보강하는 과정 | IP → GeoIP, Reputation, WHOIS |
| **Playbook** | 사전 정의된 대응 절차 | SSH 브루트포스 대응 Playbook |
| **Wazuh** | 오픈소스 SIEM/XDR 플랫폼 | 경보, 무결성 검사, 취약점 스캐닝 |
| **Suricata** | 오픈소스 IDS/IPS 엔진 | 네트워크 기반 탐지 |
| **nftables** | Linux 방화벽 프레임워크 | 패킷 필터링, NAT |
| **Slack Webhook** | Slack 채널로 메시지를 전송하는 HTTP API | 경보 알림 전송 |
| **temperature** | LLM 출력의 무작위성 조절 파라미터 | 분석: 0.1~0.3 (결정론적) |
| **system prompt** | LLM에게 역할과 규칙을 부여하는 메시지 | "보안관제 전문가 역할" |
| **confidence score** | LLM이 분석 결과에 대해 부여하는 확신 점수 | 0.95 = 95% 확신 |

---

## Part 1: Blue Agent 아키텍처와 역할 (0:00-0:30)

### 1.1 Blue Agent란?

Blue Agent는 방어 측(Blue Team)의 자율 에이전트로, 다음 기능을 수행한다:

| 기능 | 설명 | 자동화 수준 |
|------|------|------------|
| 경보 수집 | Wazuh/Suricata에서 경보 수집 | 완전 자동 |
| 경보 분석 | LLM으로 경보의 위험도/의미 분석 | 완전 자동 |
| Triage | 우선순위 분류 및 필터링 | 자동+사람 검증 |
| 대응 권고 | 대응 방안 생성 | 자동 생성, 사람 승인 |
| 자동 차단 | low-risk 차단 규칙 자동 적용 | 조건부 자동 |
| 알림 | Slack/Email로 관제 팀에 통보 | 완전 자동 |

### 1.2 Blue Agent 아키텍처

```
[Blue Agent 루프 (5분 주기)]

  1.Collect(경보수집) -> 2.Analyze(LLM분석) -> 3.Triage(분류)
                                                    |
  6.Learn(경험축적)  <- 5.Notify(알림)     <- 4.Respond(대응)
```

### 1.3 전통적 SOAR vs LLM Blue Agent

| 항목 | 전통 SOAR | LLM Blue Agent |
|------|----------|----------------|
| 규칙 작성 | 수동 (인간이 작성) | 자동 (LLM이 분석) |
| 신종 공격 | 규칙 없으면 탐지 불가 | 맥락 기반 추론 가능 |
| 오탐 처리 | 규칙 수정 필요 | 경험 학습으로 개선 |
| 확장성 | 규칙 수에 비례 | LLM 컨텍스트 크기에 비례 |
| 설명 가능성 | 매칭된 규칙 번호 | 자연어 분석 보고서 |

---

## Part 2: LLM 기반 경보 분석 엔진 (0:30-1:00)

### 2.1 경보 분석 프롬프트 설계

Blue Agent의 핵심은 LLM에게 보안 경보를 분석시키는 프롬프트이다.

### 2.2 경보 분석 실습

> **실습 목적**: 자율보안 시스템의 안전 경계(Safety Boundary)와 인간 개입 메커니즘을 설계하기 위해 수행한다
>
> **배우는 것**: risk_level에 따른 자동 실행/dry_run/인간 승인의 3단계 안전 제어와, critical 작업의 확인 절차를 이해한다
>
> **결과 해석**: risk_level=critical에서 dry_run이 자동 강제되면 안전 장치가 정상 동작하는 것이다
>
> **실전 활용**: 자율 시스템의 안전 정책 설계, 인간-AI 협업 워크플로, 자동화 범위 결정에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소
export MGR="http://localhost:8000"

# 1. secu 서버에서 최근 시스템 로그 수집
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week11-blue-agent-lab",
    "request_text": "Blue Agent 경보 분석 실습 — LLM 기반 관제",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 확인한다
```

```bash
export PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 경보 데이터 수집 — 3개 서버에서 동시 수집
curl -s -X POST $MGR/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "journalctl --since \"1 hour ago\" --no-pager -p warning 2>/dev/null | tail -30 || echo no-warnings",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "journalctl --since \"1 hour ago\" --no-pager -p warning 2>/dev/null | tail -30 || echo no-warnings",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5 || echo no-wazuh-alerts",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# secu/web/siem 서버의 경보 데이터를 수집한다
```

### 2.3 LLM 경보 분석

```bash
# 4. 수집된 경보를 LLM으로 분석
curl -s "$MGR/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /tmp/blue_evidence.json

# 5. LLM 경보 분석 — Blue Agent의 핵심 로직
python3 -c "
import json, requests

# Evidence 로드
with open('/tmp/blue_evidence.json') as f:
    evidence = json.load(f)

# Evidence를 텍스트로 정리
evidence_text = json.dumps(evidence, indent=2, ensure_ascii=False)[:3000]

# Blue Agent 시스템 프롬프트
system_prompt = '''당신은 SOC Blue Agent입니다. 다음 규칙을 따르세요:

1. 수집된 보안 경보를 분석하여 JSON 형식으로 보고하라
2. 각 경보에 대해 severity(critical/high/medium/low/info), 분류(true_positive/false_positive/unknown), 권고 대응을 포함하라
3. 전체 보안 상황 요약을 제공하라

출력 형식:
{
  \"overall_status\": \"green/yellow/red\",
  \"alerts_analyzed\": N,
  \"findings\": [
    {
      \"source\": \"서버명\",
      \"description\": \"경보 설명\",
      \"severity\": \"high\",
      \"classification\": \"true_positive\",
      \"recommendation\": \"권고 대응\"
    }
  ],
  \"summary\": \"전체 요약\"
}'''

# LLM 호출
resp = requests.post(
    'http://192.168.0.105:11434/v1/chat/completions',
    json={
        'model': 'gemma3:12b',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'다음 서버별 경보 데이터를 분석하라:\\n{evidence_text}'}
        ],
        'temperature': 0.1,
        'max_tokens': 1000
    }
)
# 분석 결과 출력
result = resp.json()['choices'][0]['message']['content']
print('=== Blue Agent 분석 결과 ===')
print(result)
"
```

### 2.4 분석 결과를 OpsClaw에 기록

```bash
# 6. Blue Agent 분석 결과를 dispatch로 기록
curl -s -X POST $MGR/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"Blue Agent Analysis Complete - $(date +%Y%m%d_%H%M%S)\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 분석 완료 타임스탬프를 Evidence에 기록한다
```

---

## Part 3: 5분 주기 자동 관제 구현 (1:00-1:25)

### 3.1 자동 관제 루프 설계

Blue Agent는 5분마다 다음 사이클을 반복한다:

```
[T+0분]  경보 수집 (Collect)
[T+1분]  LLM 분석 (Analyze)
[T+2분]  위험도 분류 (Triage)
[T+3분]  대응 실행 (Respond, low-risk만 자동)
[T+4분]  알림 발송 (Notify)
[T+5분]  경험 축적 (Learn)
→ 다음 사이클 시작
```

### 3.2 자동 관제 스크립트

```bash
# 1. Blue Agent 자동 관제 1회 사이클 실행 스크립트
# 실제 운영에서는 Schedule에 등록하여 5분마다 자동 실행한다

# Step 1: 프로젝트 생성 (매 사이클마다 새 프로젝트)
CYCLE_PID=$(curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d "{
    \"name\": \"blue-agent-cycle-$(date +%H%M)\",
    \"request_text\": \"Blue Agent 5분 관제 사이클 — $(date)\",
    \"master_mode\": \"external\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
# 사이클별 고유 프로젝트 ID를 변수에 저장
echo "Cycle PID: $CYCLE_PID"
```

```bash
# Step 2: 스테이지 전환 (plan → execute)
# plan 스테이지 전환
curl -s -X POST $MGR/projects/$CYCLE_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지 전환
curl -s -X POST $MGR/projects/$CYCLE_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Step 3: 경보 수집 + 시스템 상태 확인
curl -s -X POST $MGR/projects/$CYCLE_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[COLLECT] secu - $(date)\"; journalctl --since \"5 min ago\" --no-pager -p err 2>/dev/null | tail -10 || echo clean",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[COLLECT] web - $(date)\"; journalctl --since \"5 min ago\" --no-pager -p err 2>/dev/null | tail -10 || echo clean",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[COLLECT] siem - $(date)\"; tail -3 /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo no-recent-alerts",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 5분간의 신규 경보를 3개 서버에서 수집한다
```

### 3.3 관제 사이클 완료 처리

```bash
# Step 4: 사이클 완료 보고
curl -s -X POST $MGR/projects/$CYCLE_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Blue Agent 5분 관제 사이클 완료",
    "outcome": "success",
    "work_details": [
      "[COLLECT] 3개 서버 경보 수집 완료",
      "[ANALYZE] LLM 분석 완료 — 위험 경보 0건",
      "[STATUS] 전체 보안 상태: GREEN"
    ]
  }' | python3 -m json.tool
# 관제 사이클 결과를 Experience로 보존한다
```

---

## Part 4: Slack 알림 연동 (1:35-2:05)

### 4.1 Slack 알림 아키텍처

```
Blue Agent 분석 결과
      │
      ▼ (severity >= high?)
Slack 알림 전송
      │
      ├── #security-alerts 채널: 고위험 경보
      ├── #soc-daily 채널: 일일 요약
      └── DM: 담당자 직접 알림
```

### 4.2 Slack 알림 구성

OpsClaw의 Notification API를 활용하여 Slack 알림을 설정한다.

```bash
# 1. Notification 채널 목록 조회
curl -s "$MGR/notifications/channels" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 현재 등록된 알림 채널 확인
```

```bash
# 2. Slack Notification 채널 등록
curl -s -X POST "$MGR/notifications/channels" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "blue-agent-slack",
    "channel_type": "slack",
    "config": {
      "channel": "#bot-cc",
      "severity_filter": "high"
    },
    "enabled": true
  }' | python3 -m json.tool
# Slack 알림 채널이 등록된다
```

### 4.3 Slack 메시지 형식 설계

```bash
# 3. Blue Agent 경보 알림 시뮬레이션 — OpsClaw를 통해 Slack 메시지 전송
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "blue-agent-slack-test",
    "request_text": "Blue Agent Slack 알림 테스트",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export SLACK_PID="반환된-프로젝트-ID"

# 4. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$SLACK_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$SLACK_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 5. Slack 알림 테스트 메시지 전송
curl -s -X POST $MGR/projects/$SLACK_PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"[BLUE AGENT ALERT] $(date +%Y-%m-%d_%H:%M:%S) | Status: GREEN | High alerts: 0 | Medium alerts: 2 | Servers: secu/web/siem all normal\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# Slack 채널에 Blue Agent 상태 메시지가 전송된다
```

### 4.4 경보 에스컬레이션

| 위험도 | 알림 대상 | 응답 SLA | 자동 대응 |
|--------|----------|---------|----------|
| Critical | Slack + SMS + 전화 | 5분 | 즉시 차단 |
| High | Slack + Email | 15분 | 조건부 차단 |
| Medium | Slack | 1시간 | 모니터링 강화 |
| Low | 일일 요약 | 24시간 | 없음 |
| Info | 로그만 | — | 없음 |

---

## Part 5: 오탐 처리와 튜닝 전략 (2:05-2:35)

### 5.1 오탐의 유형과 원인

| 유형 | 원인 | 예시 |
|------|------|------|
| 규칙 과민 | 임계값이 너무 낮음 | 로그인 실패 1회로 경보 |
| 컨텍스트 부족 | 정상 활동을 공격으로 판단 | 관리자의 대량 파일 접근 |
| 환경 차이 | 테스트 환경 활동을 탐지 | 개발자의 스캔 도구 사용 |
| 시간대 미고려 | 야간 배치 작업을 이상으로 판단 | 새벽 백업 작업 |

### 5.2 LLM 기반 오탐 필터링

```bash
# 1. 오탐 필터링 프롬프트 실습
python3 -c "
import requests, json

# 모의 경보 데이터 (오탐 포함)
alerts = [
    {'source': 'secu', 'type': 'SSH Failed Login', 'count': 2, 'user': 'admin', 'ip': '10.20.30.201', 'time': '09:30'},
    {'source': 'web', 'type': 'SQL Injection Attempt', 'count': 1, 'path': '/api/search?q=test', 'ip': '10.20.30.201', 'time': '09:31'},
    {'source': 'secu', 'type': 'Port Scan Detected', 'count': 50, 'ip': '203.0.113.50', 'time': '09:32'},
    {'source': 'siem', 'type': 'File Integrity Change', 'count': 1, 'file': '/etc/crontab', 'time': '09:33'},
]

# LLM에게 오탐 필터링 요청
system_prompt = '''당신은 SOC 경보 분석가입니다. 각 경보에 대해:
1. true_positive / false_positive / needs_investigation으로 분류하라
2. 판단 근거를 간략히 설명하라
3. 내부 IP(10.x.x.x)에서 발생한 소량의 실패는 대부분 오탐이다
4. 외부 IP에서 대량 발생한 이벤트는 true_positive 가능성이 높다

JSON 배열로 출력하라.'''

resp = requests.post(
    'http://192.168.0.105:11434/v1/chat/completions',
    json={
        'model': 'gemma3:12b',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'다음 경보를 분류하라:\\n{json.dumps(alerts, indent=2, ensure_ascii=False)}'}
        ],
        'temperature': 0.1,
        'max_tokens': 800
    }
)
# 오탐 필터링 결과 출력
print('=== 오탐 필터링 결과 ===')
print(resp.json()['choices'][0]['message']['content'])
"
# LLM이 내부 IP의 소량 실패를 오탐으로, 외부 IP의 포트 스캔을 정탐으로 분류한다
```

### 5.3 오탐률 측정과 튜닝

```bash
# 2. 오탐 필터링 성능 측정 프로젝트
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "blue-agent-fp-tuning",
    "request_text": "Blue Agent 오탐 필터링 성능 측정 및 튜닝",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export FP_PID="반환된-프로젝트-ID"

# 3. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$FP_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$FP_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 4. 오탐률 측정 — 실제 경보 데이터로 LLM 분류 정확도 평가
curl -s -X POST $MGR/projects/$FP_PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"FP Rate Measurement: Total=20, TP=15, FP=3, FN=1, TN=1 | Precision=83% | Recall=94% | F1=88%\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 오탐 필터링 성능 지표를 Evidence에 기록한다
```

### 5.4 튜닝 전략

| 전략 | 방법 | 효과 |
|------|------|------|
| Whitelist | 내부 IP/관리자 활동 제외 | FP 30% 감소 |
| 시간 필터 | 야간 배치 시간대 제외 | FP 15% 감소 |
| 임계값 조정 | 최소 카운트 상향 | FP 20% 감소 (FN 주의) |
| 컨텍스트 강화 | GeoIP/Reputation 데이터 추가 | 분류 정확도 향상 |
| Experience 학습 | 과거 FP 패턴 참조 | 지속적 개선 |

---

## Part 6: 종합 실습 + 퀴즈 (2:35-3:00)

### 6.1 종합 실습 과제

**과제**: Blue Agent 관제 사이클 1회를 완전히 구현하라.

1. 프로젝트 생성 (`week11-blue-final`)
2. 3개 서버에서 경보 수집 (execute-plan)
3. LLM으로 경보 분석 (Ollama API)
4. 오탐 필터링 적용
5. 분석 결과를 Evidence에 기록 (dispatch)
6. completion-report 작성

```bash
# 종합 실습 템플릿
# 1. 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week11-blue-final",
    "request_text": "Blue Agent 종합 실습 — 관제 사이클 구현",
    "master_mode": "external"
  }' | python3 -m json.tool

# 2. (학생 작성) 스테이지 전환 + 경보 수집 execute-plan
# TODO

# 3. (학생 작성) LLM 경보 분석
# TODO

# 4. (학생 작성) 오탐 필터링 + dispatch로 결과 기록
# TODO

# 5. (학생 작성) completion-report 작성
# TODO
```

### 6.2 퀴즈 (4지선다)

**문제 1.** Blue Agent의 5분 관제 사이클에서 가장 먼저 수행하는 단계는?

- A) LLM 분석
- B) Slack 알림 발송
- C) 경보 수집 (Collect)
- D) 대응 실행 (Respond)

**정답: C) 경보 수집 (Collect)**

---

**문제 2.** LLM 기반 경보 분석에서 temperature를 낮게 설정하는 이유는?

- A) 모델의 응답 속도를 높이기 위해
- B) 일관성 있고 결정론적인 분석 결과를 얻기 위해
- C) 더 창의적인 대응 방안을 생성하기 위해
- D) 메모리 사용량을 줄이기 위해

**정답: B) 일관성 있고 결정론적인 분석 결과를 얻기 위해**

---

**문제 3.** False Positive(오탐)에 해당하는 것은?

- A) 실제 SQL Injection 공격을 탐지한 경우
- B) 관리자의 정상 로그인을 브루트포스로 판단한 경우
- C) 포트 스캔 공격을 정확히 탐지한 경우
- D) 랜섬웨어 활동을 파일 변경으로 탐지한 경우

**정답: B) 관리자의 정상 로그인을 브루트포스로 판단한 경우**

---

**문제 4.** Blue Agent의 경보 에스컬레이션에서 Critical 등급 경보의 응답 SLA는?

- A) 24시간
- B) 1시간
- C) 15분
- D) 5분

**정답: D) 5분**

---

**문제 5.** 전통적 SOAR 대비 LLM Blue Agent의 가장 큰 장점은?

- A) 규칙 없이도 신종 공격을 맥락 기반으로 추론할 수 있다
- B) 하드웨어 자원을 적게 사용한다
- C) 100% 정확한 분석이 가능하다
- D) 규칙 작성이 더 간단하다

**정답: A) 규칙 없이도 신종 공격을 맥락 기반으로 추론할 수 있다**

---

### 6.3 다음 주 예고

Week 12에서는 **자율 Red Agent**를 학습한다.
자동 취약점 스캐닝, 공격 시나리오 자동 생성, Purple Team 설계를 실습한다.
