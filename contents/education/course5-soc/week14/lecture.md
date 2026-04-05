# Week 14: 자동화 관제 - OpsClaw Agent Daemon

## 학습 목표
- AI 기반 자율 보안 관제의 개념을 이해한다
- OpsClaw Agent Daemon의 explore/daemon/stimulate 기능을 사용한다
- 자율 탐지 에이전트를 구성하고 자극 테스트를 수행한다
- 자동화 관제의 장점과 한계를 분석한다

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

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |

---

# Week 14: 자동화 관제 - OpsClaw Agent Daemon

## 학습 목표
- AI 기반 자율 보안 관제의 개념을 이해한다
- OpsClaw Agent Daemon의 explore/daemon/stimulate 기능을 사용한다
- 자율 탐지 에이전트를 구성하고 자극 테스트를 수행한다
- 자동화 관제의 장점과 한계를 분석한다

---

## 1. 자동화 관제 개념

### 1.1 전통적 관제 vs AI 자동화 관제

| 항목 | 전통적 관제 | AI 자동화 관제 |
|------|-----------|--------------|
| 탐지 | 시그니처 룰 기반 | 시그니처 + AI 판단 |
| 분석 | 분석관 수동 분석 | LLM 자동 분석 + 분석관 검증 |
| 대응 | 매뉴얼 기반 | 자동 대응 + 승인 체계 |
| 24/7 | 교대 근무 필요 | 에이전트 상시 가동 |
| 확장성 | 인력 비례 | 에이전트 추가 |

### 1.2 OpsClaw Agent Daemon 아키텍처

```
+---------------------------------------------+
|              OpsClaw Manager API              |
|              (http://localhost:8000)           |
+-----------+-----------+-----------------------+
|           |           |                       |
|  Explore  |  Daemon   |  Stimulate            |
|  (탐색)    |  (감시)    |  (자극 테스트)         |
|           |           |                       |
|  환경 파악  |  주기적    |  의도적 공격           |
|  자산 조사  |  로그 조회  |  탐지 능력 검증        |
+-----------+-----------+-----------------------+
         |           |            |
         +-----------+------------+
                     |
              SubAgent (각 서버)
```

---

## 2. Explore: 환경 탐색

> **이 실습을 왜 하는가?**
> "자동화 관제 - OpsClaw Agent Daemon" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 OpsClaw API로 환경 탐색

> **실습 목적**: OpsClaw API를 활용하여 자동화된 관제 워크플로우를 구축한다
>
> **배우는 것**: 경보 수집, 분석, 대응을 API 기반으로 자동화하여 관제 효율을 높이는 방법을 배운다
>
> **결과 해석**: API 호출로 경보 수집과 대응이 자동 실행되면 자동화 관제 파이프라인이 정상 동작한다
>
> **실전 활용**: SOAR(Security Orchestration, Automation and Response)는 SOC 운영 효율화의 핵심 기술이다

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

# 프로젝트 생성
echo "=== Phase 1: 프로젝트 생성 ==="
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"soc-explore-demo","request_text":"보안 관제 환경 탐색","master_mode":"external"}')  # 요청 데이터(body)
PROJECT_ID=$(echo "$PROJECT" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null         # API 인증 키
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null         # API 인증 키
echo "Stage: execute"
```

### 2.2 secu 서버 탐색

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

echo "=== secu 서버 탐색 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uname -a && echo --- && ss -tlnp | head -10 && echo --- && systemctl list-units --type=service --state=running | grep -E \"suricata|nftables|wazuh|ssh\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):                      # 반복문 시작
    print(f'Task {r.get(\"order\",\"?\")}: {r.get(\"status\",\"?\")}')
    output = r.get('output','')
    print(output[:500] if output else '(출력 없음)')
"
```

### 2.3 siem 서버 탐색

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

echo "=== siem 서버 탐색 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && echo --- && systemctl status wazuh-manager 2>/dev/null | head -5 && echo --- && ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://10.20.30.100:8002"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):                      # 반복문 시작
    print(f'Task {r.get(\"order\",\"?\")}: {r.get(\"status\",\"?\")}')
    print(r.get('output','')[:500])
"
```

---

## 3. Daemon: 주기적 관제 순환

### 3.1 관제 순환 스크립트

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
cat << 'SCRIPT' > /tmp/soc_daemon.sh
#!/bin/bash
OLLAMA_URL="http://192.168.0.105:11434/v1/chat/completions"

echo "=== SOC Daemon 시작 ($(date)) ==="

# 1. Suricata 최신 경보 수집
echo "[1] Suricata 경보 수집"
SURICATA_ALERTS=$(sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "tail -20 /var/log/suricata/fast.log 2>/dev/null" 2>/dev/null)
echo "  수집: $(echo "$SURICATA_ALERTS" | wc -l)줄"

# 2. Wazuh 최신 경보 수집
echo "[2] Wazuh 경보 수집"
WAZUH_ALERTS=$(sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null" 2>/dev/null)
echo "  수집: $(echo "$WAZUH_ALERTS" | wc -l)줄"

# 3. LLM 분석
echo "[3] LLM 분석 요청"
ANALYSIS=$(curl -s "$OLLAMA_URL" \
  -H "Content-Type: application/json" \
  -d "{                                                # 요청 데이터(body)
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC L1 자동 분석 에이전트입니다. 경보를 분석하여 심각도와 대응 필요 여부를 판단합니다. 한국어로 간결하게.\"},
      {\"role\": \"user\", \"content\": \"보안 경보 분석:\\nSuricata: ${SURICATA_ALERTS:-(없음)}\\nWazuh: ${WAZUH_ALERTS:-(없음)}\\n\\n1) 요약 2) 위험도 3) 대응 필요 여부\"}
    ],
    \"temperature\": 0.2
  }" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null)

echo ""
echo "=== LLM 분석 결과 ==="
echo "$ANALYSIS"
SCRIPT

chmod +x /tmp/soc_daemon.sh                            # 파일 권한 변경
bash /tmp/soc_daemon.sh
ENDSSH
```

### 3.2 경보 임계값 기반 에스컬레이션

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
alerts = [
    {"time": "09:01", "source": "suricata", "severity": "low", "desc": "HTTP 스캔 탐지"},
    {"time": "09:02", "source": "suricata", "severity": "low", "desc": "포트 스캔 탐지"},
    {"time": "09:03", "source": "suricata", "severity": "medium", "desc": "SQL Injection 시도"},
    {"time": "09:04", "source": "wazuh", "severity": "medium", "desc": "SSH 인증 실패 (3회)"},
    {"time": "09:05", "source": "suricata", "severity": "high", "desc": "리버스셸 탐지"},
    {"time": "09:06", "source": "wazuh", "severity": "high", "desc": "파일 무결성 변경"},
    {"time": "09:07", "source": "wazuh", "severity": "critical", "desc": "root 계정 로그인"},
]

THRESHOLDS = {"critical": 1, "high": 2, "medium": 5, "low": 10}

counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
for a in alerts:                                       # 반복문 시작
    counts[a["severity"]] += 1

print("=== 경보 에스컬레이션 분석 ===")
print(f"총 경보: {len(alerts)}건\n")

escalate = False
for sev in ["critical", "high", "medium", "low"]:      # 반복문 시작
    t = THRESHOLDS[sev]
    c = counts[sev]
    status = "ESCALATE" if c >= t else "OK"
    if c >= t: escalate = True
    print(f"  {sev:<10} {c}건 / 임계값 {t} -> [{status}]")

print(f"\n판정: {'에스컬레이션 - SOC L2 호출' if escalate else '정상'}")

if escalate:
    print("\n에스컬레이션 사유:")
    for a in alerts:                                   # 반복문 시작
        if a["severity"] in ["critical", "high"]:
            print(f"  [{a['time']}] [{a['severity'].upper()}] {a['desc']}")
PYEOF
ENDSSH
```

---

## 4. Stimulate: 자극 테스트

### 4.1 탐지 능력 검증

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

echo "=== 자극 테스트: 포트 스캔 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "command": "for port in 22 80 443 3306 5432 8080; do timeout 1 bash -c \"echo > /dev/tcp/10.20.30.1/$port\" 2>/dev/null && echo \"Port $port: OPEN\" || echo \"Port $port: CLOSED\"; done",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:300])"
```

### 4.2 SQL Injection 자극

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

echo "=== 자극: SQLi 시도 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "command": "curl -s -o /dev/null -w \"%{http_code}\" \"http://localhost:3000/rest/products/search?q=test%27+OR+1=1--\" && echo \" (SQLi 전송)\"",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:200])"
```

### 4.3 탐지 확인

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

echo "=== 탐지 확인: Suricata ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "command": "tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -iE \"sql|scan|injection\" || echo \"관련 경보 없음\"",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:300])"
```

---

## 5. 자동 대응 파이프라인

### 5.1 탐지-분석-대응 자동화

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
def detect(log_entry):
    keywords = {
        "critical": ["reverse shell", "root login", "data exfiltration"],
        "high": ["sql injection", "brute force", "privilege escalation"],
        "medium": ["port scan", "directory traversal", "xss"],
        "low": ["404 error", "invalid user agent"],
    }
    for severity, patterns in keywords.items():        # 반복문 시작
        for pattern in patterns:                       # 반복문 시작
            if pattern in log_entry.lower():
                return severity, pattern
    return "info", "unknown"

def respond(severity, pattern):
    if severity == "critical":
        return f"[AUTO] 즉시 차단 + SOC L2 알림 ({pattern})"
    elif severity == "high":
        return f"[MANUAL] SOC L1 분석 필요 ({pattern})"
    else:
        return f"[LOG] 기록 ({pattern})"

test_logs = [
    "192.168.1.100: Reverse Shell connection on port 4444",
    "10.0.0.5: SQL Injection attempt on /api/login",
    "172.16.0.1: Port scan detected (SYN, 100 ports)",
    "192.168.1.50: 404 error on /nonexistent",
    "10.0.0.10: Root login from unknown IP",
]

print("=== 탐지-분석-대응 파이프라인 ===\n")
for log in test_logs:                                  # 반복문 시작
    severity, pattern = detect(log)
    action = respond(severity, pattern)
    print(f"로그: {log[:60]}...")
    print(f"  탐지: {severity.upper()} ({pattern})")
    print(f"  대응: {action}\n")
PYEOF
ENDSSH
```

---

## 6. 자동화 관제의 한계와 인간 역할

### 6.1 역할 분담

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
roles = {
    "자동화(AI) 담당": [
        "대량 로그 수집 및 정규화",
        "알려진 패턴 매칭 (시그니처)",
        "반복적 1차 분류 (L1 티켓팅)",
        "IOC 자동 업데이트 및 매칭",
        "정기 보고서 자동 생성",
        "규칙 기반 자동 차단",
    ],
    "인간(분석관) 담당": [
        "제로데이 공격 분석",
        "비즈니스 컨텍스트 판단",
        "오탐/정탐 최종 판별",
        "법적/규제 대응 결정",
        "위협 헌팅 가설 수립",
        "경영진 커뮤니케이션",
        "사고 대응 의사결정",
    ],
}

for role, tasks in roles.items():                      # 반복문 시작
    print(f"\n{role}")
    print("=" * 40)
    for task in tasks:                                 # 반복문 시작
        print(f"  - {task}")

print("\n핵심: AI는 인간을 '대체'가 아닌 '증강(augment)'한다")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. OpsClaw Agent Daemon은 explore/daemon/stimulate 3단계로 자율 관제한다
2. LLM은 경보 1차 분석과 분류를 자동화하여 분석관 부담을 줄인다
3. 에스컬레이션 임계값으로 자동 경보 분류와 상위 통보를 구현한다
4. 자극 테스트로 탐지 능력을 지속적으로 검증해야 한다
5. 자동 대응 파이프라인은 탐지-분석-대응을 연결한다
6. AI는 인간을 대체가 아닌 증강하며, 최종 판단은 인간이 수행한다

---

## 다음 주 예고
- Week 15: 기말 종합 인시던트 대응 훈련 - Red Team vs Blue Team

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** SOC에서 False Positive(오탐)란?
- (a) 공격을 정확히 탐지  (b) **정상 활동을 공격으로 잘못 탐지**  (c) 공격을 놓침  (d) 로그 미수집

**Q2.** SIGMA 룰의 핵심 장점은?
- (a) 특정 SIEM에서만 동작  (b) **SIEM 벤더에 독립적인 범용 포맷**  (c) 자동 차단 기능  (d) 로그 압축

**Q3.** TTD(Time to Detect)를 줄이기 위한 방법은?
- (a) 경보를 비활성화  (b) **실시간 경보 규칙 최적화 + 자동화**  (c) 분석 인력 감축  (d) 로그 보관 기간 단축

**Q4.** 인시던트 대응 NIST 6단계에서 첫 번째는?
- (a) 탐지(Detection)  (b) **준비(Preparation)**  (c) 격리(Containment)  (d) 근절(Eradication)

**Q5.** Wazuh logtest의 용도는?
- (a) 서버 성능 측정  (b) **탐지 룰을 실제 배포 전에 테스트**  (c) 네트워크 속도 측정  (d) 디스크 점검

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Wazuh alerts.json/logtest/agent_control, SIGMA 룰, 경보 분석
