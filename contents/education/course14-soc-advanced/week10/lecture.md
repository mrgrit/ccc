# Week 10: SOAR 자동화

## 학습 목표
- SOAR(Security Orchestration, Automation and Response) 개념과 아키텍처를 이해한다
- 인시던트 유형별 자동 대응 플레이북을 설계할 수 있다
- Wazuh Active Response를 설정하여 자동 차단/격리를 구현할 수 있다
- REST API를 활용한 보안 도구 간 연동 자동화를 구현할 수 있다
- OpsClaw를 SOAR 엔진으로 활용하여 다중 서버 자동 대응을 수행할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | SOAR 이론 + 플레이북 설계 (Part 1) | 강의 |
| 0:50-1:30 | Wazuh Active Response (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 자동 대응 실습 (Part 3) | 실습 |
| 2:30-3:10 | OpsClaw SOAR + API 연동 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOAR** | Security Orchestration, Automation and Response | 보안 오케스트레이션/자동화/대응 | 자동 소방 시스템 |
| **플레이북** | Playbook | 자동 대응 절차 스크립트 | 소방 매뉴얼의 자동화 버전 |
| **오케스트레이션** | Orchestration | 여러 보안 도구를 연계 조율 | 오케스트라 지휘 |
| **Active Response** | Active Response | Wazuh의 자동 대응 기능 | 자동 소화기 |
| **enrichment** | Enrichment | 경보에 추가 컨텍스트 첨부 | 보고서에 배경 정보 추가 |
| **워크플로우** | Workflow | 자동화된 작업 흐름 | 공장 조립 라인 |
| **webhook** | Webhook | 이벤트 발생 시 HTTP 콜백 | 알림 벨 |
| **idempotent** | Idempotent | 여러 번 실행해도 동일 결과 | 멱등성 |

---

# Part 1: SOAR 이론 + 플레이북 설계 (50분)

## 1.1 SOAR란?

SOAR는 **보안 운영의 3가지 핵심 영역을 자동화**하는 플랫폼이다.

```
S - Security Orchestration (보안 오케스트레이션)
    → 여러 보안 도구(SIEM, EDR, FW, TI)를 하나의 워크플로우로 연결
    
O - Orchestration (continued)
    
A - Automation (자동화)
    → 반복적인 SOC 작업을 스크립트/플레이북으로 자동 실행
    
R - Response (대응)
    → 인시던트 발생 시 자동으로 차단, 격리, 알림 수행
```

### SOAR 없는 SOC vs SOAR 있는 SOC

```
[SOAR 없는 SOC]
경보 발생 → 분석가가 SIEM 확인 → 수동으로 IP 조회 →
수동으로 VirusTotal 확인 → 수동으로 방화벽 차단 →
수동으로 티켓 생성 → 수동으로 보고서 작성
→ 소요 시간: 30-60분

[SOAR 있는 SOC]
경보 발생 → [자동] IP 조회 + TI 조회 →
[자동] 위험도 판정 → [자동] 방화벽 차단 →
[자동] 티켓 생성 + Slack 알림 →
분석가: 결과 검토 + 보고서 승인
→ 소요 시간: 2-5분
```

## 1.2 플레이북 설계 원칙

```
[좋은 플레이북의 5가지 원칙]

1. 멱등성 (Idempotent)
   → 여러 번 실행해도 동일 결과
   → 이미 차단된 IP를 다시 차단해도 에러 없음

2. 관찰 가능성 (Observable)
   → 모든 단계의 실행 결과를 기록
   → 실패 시 어디서 실패했는지 추적 가능

3. 안전 장치 (Safety)
   → 내부 IP는 자동 차단하지 않음
   → Critical 조치는 사람 승인 필요

4. 원복 가능 (Reversible)
   → 모든 자동 조치는 취소 가능
   → 차단 해제, 격리 해제 절차 포함

5. 점진적 확대 (Graduated)
   → Low: 로그만 기록
   → Medium: 알림 + 추가 모니터링
   → High: 자동 차단 + 알림
   → Critical: 격리 + 긴급 호출
```

## 1.3 인시던트 유형별 플레이북

### 무차별 대입 공격 플레이북

```
[Playbook: Brute Force Response]

Trigger: SSH 실패 10회/5분 (동일 IP)
    |
    v
Step 1: IOC 수집
    → 공격 IP, 대상 계정, 시도 횟수
    |
Step 2: TI 조회
    → AbuseIPDB, VirusTotal 평판 확인
    |
Step 3: 판정
    → 외부 IP + 평판 나쁨 → 자동 차단
    → 내부 IP → 알림만 (수동 확인)
    → 알려진 파트너 IP → 알림 + 에스컬레이션
    |
Step 4: 대응
    → nftables IP 차단 (secu 서버)
    → 대상 계정 임시 잠금
    |
Step 5: 알림
    → Slack 채널 알림
    → 티켓 생성
    |
Step 6: 기록
    → evidence 저장
    → 24시간 후 자동 차단 해제 (또는 수동)
```

## 1.4 Wazuh Active Response 아키텍처

```
[Wazuh Active Response 흐름]

경보 발생
    |
    v
[analysisd]
    → 룰 매칭 + level 확인
    → Active Response 조건 충족?
    |
    v (Yes)
[execd]
    → 대응 스크립트 실행
    → /var/ossec/active-response/bin/<script>
    |
    v
[대응 실행]
    → IP 차단, 프로세스 종료, 계정 잠금 등
    → timeout 후 자동 해제 (선택)
```

---

# Part 2: Wazuh Active Response (40분)

## 2.1 Active Response 기본 설정

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

echo "=== 현재 Active Response 설정 ==="
sudo grep -A20 "active-response" /var/ossec/etc/ossec.conf 2>/dev/null | head -30

echo ""
echo "=== 사용 가능한 대응 스크립트 ==="
ls -la /var/ossec/active-response/bin/ 2>/dev/null

REMOTE
```

> **명령어 해설**: Wazuh의 Active Response는 ossec.conf에서 설정하며, 경보 레벨/룰 ID에 따라 자동으로 대응 스크립트를 실행한다.

## 2.2 IP 차단 Active Response 구성

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# 커스텀 IP 차단 스크립트 생성
sudo tee /var/ossec/active-response/bin/block_ip.sh << 'SCRIPT'
#!/bin/bash
# Wazuh Active Response - nftables IP 차단
# OpsClaw 연동 가능

LOG="/var/ossec/logs/active-responses.log"
ACTION=$1
USER=$2
IP=$3
ALERT_ID=$4
RULE_ID=$5

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 내부 IP 보호
if echo "$IP" | grep -qE "^10\.20\.30\.|^127\.|^192\.168\."; then
    echo "[$TIMESTAMP] BLOCKED: Internal IP $IP skipped (Rule: $RULE_ID)" >> $LOG
    exit 0
fi

if [ "$ACTION" = "add" ]; then
    # IP 차단 (로컬 iptables)
    iptables -I INPUT -s "$IP" -j DROP 2>/dev/null
    iptables -I FORWARD -s "$IP" -j DROP 2>/dev/null
    echo "[$TIMESTAMP] BLOCKED: $IP (Rule: $RULE_ID, Alert: $ALERT_ID)" >> $LOG
    
elif [ "$ACTION" = "delete" ]; then
    # IP 차단 해제
    iptables -D INPUT -s "$IP" -j DROP 2>/dev/null
    iptables -D FORWARD -s "$IP" -j DROP 2>/dev/null
    echo "[$TIMESTAMP] UNBLOCKED: $IP (Rule: $RULE_ID)" >> $LOG
fi

exit 0
SCRIPT

sudo chmod 750 /var/ossec/active-response/bin/block_ip.sh
sudo chown root:wazuh /var/ossec/active-response/bin/block_ip.sh

echo "IP 차단 Active Response 스크립트 생성 완료"

REMOTE
```

> **실습 목적**: Wazuh가 경보를 발생시키면 자동으로 공격 IP를 차단하는 Active Response를 구성한다.
>
> **배우는 것**: Active Response 스크립트 구조, 안전 장치(내부 IP 보호), 로깅

## 2.3 Active Response 테스트

```bash
# Active Response 로그 확인
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'
echo "=== Active Response 로그 ==="
tail -20 /var/ossec/logs/active-responses.log 2>/dev/null || echo "(로그 없음)"

echo ""
echo "=== 수동 테스트 ==="
sudo /var/ossec/active-response/bin/block_ip.sh add - 203.0.113.99 12345 100002
echo "차단 테스트 결과:"
sudo iptables -L INPUT -n 2>/dev/null | grep "203.0.113.99" && echo "  [OK] IP 차단됨" || echo "  [SKIP] iptables 미사용"

# 정리
sudo /var/ossec/active-response/bin/block_ip.sh delete - 203.0.113.99 12345 100002

REMOTE
```

---

# Part 3: 자동 대응 실습 (50분)

## 3.1 무차별 대입 자동 차단 플레이북

> **실습 목적**: SSH 무차별 대입 공격을 탐지하면 자동으로 공격 IP를 차단하는 전체 파이프라인을 구축한다.

```bash
cat << 'SCRIPT' > /tmp/soar_bruteforce.py
#!/usr/bin/env python3
"""SOAR 플레이북: 무차별 대입 공격 자동 대응"""
import json
import time
from datetime import datetime

class SOARPlaybook:
    def __init__(self, name):
        self.name = name
        self.log = []
        self.start_time = datetime.now()
    
    def step(self, step_num, description, action, result):
        entry = {
            "step": step_num,
            "time": datetime.now().strftime("%H:%M:%S"),
            "description": description,
            "action": action,
            "result": result,
        }
        self.log.append(entry)
        status = "OK" if "success" in result.lower() or "정상" in result else "WARN"
        print(f"  [{status}] Step {step_num}: {description}")
        print(f"       → {result}")
    
    def report(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*50}")
        print(f"  플레이북 완료: {self.name}")
        print(f"  소요 시간: {elapsed:.1f}초")
        print(f"  단계: {len(self.log)}개")
        print(f"{'='*50}")

# 시뮬레이션 실행
pb = SOARPlaybook("Brute Force Auto Response")

print("=" * 50)
print("  SOAR 플레이북 실행: 무차별 대입 대응")
print("=" * 50)

# 트리거
print("\n[트리거] SSH 무차별 대입 탐지")
print("  공격 IP: 203.0.113.50")
print("  대상: 10.20.30.100:22")
print("  실패 횟수: 15회/5분")
print("")

# Step 1: IOC 수집
pb.step(1, "IOC 수집",
    "Wazuh 경보에서 공격 IP, 대상, 횟수 추출",
    "Success - IP:203.0.113.50, Target:10.20.30.100, Count:15")

# Step 2: TI 조회
pb.step(2, "위협 인텔리전스 조회",
    "AbuseIPDB, CDB 리스트 조회",
    "Success - AbuseIPDB 점수:92, CDB:brute_force 기록 있음")

# Step 3: 판정
pb.step(3, "위험도 판정",
    "외부 IP + TI 점수 90+ = 자동 차단 대상",
    "정상 판정 - 자동 차단 승인")

# Step 4: 방화벽 차단
pb.step(4, "방화벽 IP 차단",
    "secu(10.20.30.1) nftables에 차단 룰 추가",
    "Success - nft add rule ip filter input ip saddr 203.0.113.50 drop")

# Step 5: Wazuh AR
pb.step(5, "SIEM Active Response",
    "siem(10.20.30.100) iptables 차단",
    "Success - iptables -I INPUT -s 203.0.113.50 -j DROP")

# Step 6: 알림
pb.step(6, "알림 전송",
    "Slack #soc-alerts 채널 알림",
    "Success - 알림 전송 완료")

# Step 7: 티켓 생성
pb.step(7, "인시던트 티켓 생성",
    "OpsClaw evidence에 기록",
    "Success - Evidence ID: ev_20260404_001")

# Step 8: 스케줄
pb.step(8, "차단 해제 스케줄",
    "24시간 후 자동 차단 해제 예약",
    "Success - 해제 시각: 2026-04-05 10:15:00")

pb.report()
SCRIPT

python3 /tmp/soar_bruteforce.py
```

## 3.2 웹 공격 자동 대응 플레이북

```bash
cat << 'SCRIPT' > /tmp/soar_webattack.py
#!/usr/bin/env python3
"""SOAR 플레이북: 웹 공격 자동 대응"""

print("=" * 50)
print("  SOAR 플레이북: 웹 공격 대응")
print("=" * 50)

steps = [
    ("트리거", "SQL Injection 반복 탐지 (5회/5분)", "Wazuh Rule 100102"),
    ("Step 1", "공격 패턴 분석", "GET /api/products?id=1 OR 1=1-- (SQLi)"),
    ("Step 2", "WAF 룰 확인", "BunkerWeb WAF: SQLi 룰 활성화 확인"),
    ("Step 3", "공격 IP 차단", "nftables: 203.0.113.50 → DROP"),
    ("Step 4", "웹서버 로그 수집", "Apache access.log에서 관련 요청 추출"),
    ("Step 5", "DB 무결성 확인", "데이터 변조 여부 점검 쿼리 실행"),
    ("Step 6", "IOC 업데이트", "CDB malicious_ips 리스트에 IP 추가"),
    ("Step 7", "보고서 생성", "인시던트 보고서 자동 생성"),
]

for name, desc, detail in steps:
    print(f"\n  [{name}] {desc}")
    print(f"    → {detail}")

print(f"\n=== 플레이북 완료 (7단계, 예상 소요: 30초) ===")
SCRIPT

python3 /tmp/soar_webattack.py
```

## 3.3 OpsClaw를 이용한 실제 자동 대응

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# SOAR 플레이북 프로젝트
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "soar-bruteforce-response",
    "request_text": "무차별 대입 공격 자동 대응 플레이북 실행",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 다중 서버 동시 대응
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== 방화벽 상태 ===\" && nft list ruleset 2>/dev/null | head -20 && echo FIREWALL_CHECK_OK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== Wazuh AR 로그 ===\" && tail -5 /var/ossec/logs/active-responses.log 2>/dev/null && echo AR_LOG_OK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== 웹서버 접근 로그 ===\" && tail -10 /var/log/apache2/access.log 2>/dev/null || tail -10 /var/log/nginx/access.log 2>/dev/null && echo WEB_LOG_OK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

sleep 3
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool 2>/dev/null | head -30
```

> **실전 활용**: OpsClaw의 execute-plan으로 여러 서버에 동시에 대응 조치를 실행하고, evidence로 모든 조치를 기록한다. 이것이 실질적인 SOAR 동작이다.

---

# Part 4: OpsClaw SOAR + API 연동 (40분)

## 4.1 API 기반 보안 도구 연동

```bash
cat << 'SCRIPT' > /tmp/soar_api_integration.py
#!/usr/bin/env python3
"""SOAR API 연동 패턴"""

integrations = {
    "Wazuh API": {
        "용도": "경보 조회, 에이전트 관리",
        "예시": "curl -k -u user:pass https://siem:55000/security/user/authenticate",
        "자동화": "경보 발생 → 상세 조회 → 판정",
    },
    "nftables (via SSH)": {
        "용도": "방화벽 IP 차단/해제",
        "예시": "nft add rule ip filter input ip saddr <IP> drop",
        "자동화": "IP 차단 → 타이머 설정 → 자동 해제",
    },
    "VirusTotal API": {
        "용도": "IP/도메인/해시 평판 조회",
        "예시": "curl https://www.virustotal.com/api/v3/ip_addresses/<IP>",
        "자동화": "IOC 자동 조회 → 점수 기반 판정",
    },
    "Slack Webhook": {
        "용도": "SOC 팀 알림",
        "예시": "curl -X POST -d '{\"text\":\"Alert!\"}' webhook_url",
        "자동화": "경보 → Slack 알림 → 대응 결과 보고",
    },
    "OpsClaw API": {
        "용도": "다중 서버 명령 실행, 증거 수집",
        "예시": "curl -X POST http://localhost:8000/projects/{id}/dispatch",
        "자동화": "플레이북 → 다중 서버 동시 대응",
    },
}

print("=" * 60)
print("  SOAR API 연동 매트릭스")
print("=" * 60)

for name, info in integrations.items():
    print(f"\n--- {name} ---")
    print(f"  용도: {info['용도']}")
    print(f"  예시: {info['예시'][:60]}")
    print(f"  자동화: {info['자동화']}")
SCRIPT

python3 /tmp/soar_api_integration.py
```

## 4.2 SOAR 효과 측정

```bash
cat << 'SCRIPT' > /tmp/soar_metrics.py
#!/usr/bin/env python3
"""SOAR 도입 효과 측정"""

metrics = {
    "SOAR 도입 전": {
        "MTTR(분)": 45,
        "일일_경보_처리": 200,
        "자동_대응_비율(%)": 0,
        "분석가_수동_작업(%)": 100,
        "티켓_생성_시간(분)": 15,
        "오탐_확인_시간(분)": 10,
    },
    "SOAR 도입 후": {
        "MTTR(분)": 5,
        "일일_경보_처리": 800,
        "자동_대응_비율(%)": 70,
        "분석가_수동_작업(%)": 30,
        "티켓_생성_시간(분)": 0,
        "오탐_확인_시간(분)": 2,
    },
}

print("=" * 60)
print("  SOAR 도입 효과 분석")
print("=" * 60)
print(f"\n{'지표':25s} {'도입 전':>10s} {'도입 후':>10s} {'개선':>10s}")
print("-" * 60)

for metric in metrics["SOAR 도입 전"]:
    before = metrics["SOAR 도입 전"][metric]
    after = metrics["SOAR 도입 후"][metric]
    if before > 0:
        change = (after - before) / before * 100
        sign = "+" if change > 0 else ""
        print(f"{metric:25s} {before:>10} {after:>10} {sign}{change:>8.0f}%")
    else:
        print(f"{metric:25s} {before:>10} {after:>10} {'N/A':>10s}")

print("\n핵심 개선:")
print("  - MTTR 89% 단축 (45분 → 5분)")
print("  - 처리량 4배 증가 (200 → 800건/일)")
print("  - 분석가 수동 작업 70% 감소")
SCRIPT

python3 /tmp/soar_metrics.py
```

---

## 체크리스트

- [ ] SOAR의 3가지 구성 요소(Orchestration, Automation, Response)를 설명할 수 있다
- [ ] 플레이북 설계 5원칙(멱등성, 관찰가능성, 안전장치, 원복, 점진적확대)을 알고 있다
- [ ] 인시던트 유형별 플레이북 흐름을 설계할 수 있다
- [ ] Wazuh Active Response의 동작 원리를 이해한다
- [ ] IP 차단 Active Response 스크립트를 작성할 수 있다
- [ ] OpsClaw execute-plan으로 다중 서버 자동 대응을 수행할 수 있다
- [ ] API 기반 보안 도구 연동 패턴을 이해한다
- [ ] SOAR 도입 효과를 KPI로 측정할 수 있다
- [ ] 안전 장치(내부 IP 보호, Critical 승인)를 구현할 수 있다
- [ ] 자동 차단 + 자동 해제 사이클을 설정할 수 있다

---

## 복습 퀴즈

**Q1.** SOAR의 "Orchestration"과 "Automation"의 차이는?

<details><summary>정답</summary>
Orchestration은 여러 보안 도구(SIEM, 방화벽, TI)를 하나의 워크플로우로 연결하는 것이고, Automation은 개별 작업(IP 차단, 티켓 생성)을 자동 실행하는 것이다. Orchestration이 "무엇을 연결할지"이고, Automation이 "어떻게 실행할지"이다.
</details>

**Q2.** 플레이북의 "멱등성"이 중요한 이유는?

<details><summary>정답</summary>
동일 경보가 반복 발생할 때 플레이북이 여러 번 실행되어도 부작용이 없어야 한다. 예: 이미 차단된 IP를 다시 차단해도 에러가 나지 않고, 중복 티켓이 생성되지 않아야 한다.
</details>

**Q3.** 자동 대응에서 내부 IP를 보호해야 하는 이유는?

<details><summary>정답</summary>
공격자가 의도적으로 내부 IP를 소스로 위장하여 자동 차단을 유발할 수 있다. 내부 서버 IP를 차단하면 서비스 장애가 발생하므로, 내부 IP 대역은 자동 차단 대상에서 제외해야 한다.
</details>

**Q4.** Wazuh Active Response의 "timeout" 설정의 역할은?

<details><summary>정답</summary>
자동 차단 후 지정된 시간이 지나면 차단을 자동으로 해제하는 기능이다. 오탐으로 정상 IP가 차단된 경우 영구 차단을 방지하고, 관리자의 수동 해제 부담을 줄인다.
</details>

**Q5.** SOAR 도입 시 MTTR이 45분에서 5분으로 줄어든 이유는?

<details><summary>정답</summary>
1) TI 조회/IP 확인이 자동화되어 수동 조사 시간 절감, 2) 방화벽 차단이 자동으로 실행되어 대응 지연 제거, 3) 티켓/알림이 자동 생성되어 커뮤니케이션 지연 제거, 4) 분석가는 결과 검토만 하면 됨.
</details>

**Q6.** OpsClaw를 SOAR로 활용하는 장점은?

<details><summary>정답</summary>
1) 다중 서버에 동시 명령 실행(execute-plan), 2) 모든 대응 조치가 evidence로 자동 기록, 3) PoW 기반 실행 증명, 4) SubAgent를 통한 안전한 원격 실행. 별도 SOAR 도입 없이 기존 인프라를 활용할 수 있다.
</details>

**Q7.** 플레이북에서 "점진적 확대"가 필요한 이유는?

<details><summary>정답</summary>
모든 경보에 최대 강도로 대응하면 오탐 시 서비스 장애를 유발한다. Low는 로그만, Medium은 알림, High는 자동 차단, Critical은 격리+긴급호출로 위험도에 비례한 대응을 하여 비용/위험의 균형을 맞춘다.
</details>

**Q8.** webhook 기반 알림과 polling 기반 알림의 차이는?

<details><summary>정답</summary>
webhook은 이벤트 발생 시 서버가 클라이언트로 즉시 HTTP 요청을 보내는 push 방식. polling은 클라이언트가 주기적으로 서버에 새 이벤트를 확인하는 pull 방식. webhook이 실시간성이 높고 리소스 효율적이다.
</details>

**Q9.** Active Response 스크립트에서 로깅이 중요한 이유는?

<details><summary>정답</summary>
1) 자동 대응이 실제로 실행되었는지 확인, 2) 오탐으로 차단된 경우 원인 추적, 3) 감사(audit) 요구사항 충족, 4) 차단/해제 이력 관리로 문제 해결에 활용.
</details>

**Q10.** SOAR 자동화 비율이 100%가 아닌 70-80%인 이유는?

<details><summary>정답</summary>
1) Critical 수준의 대응은 사람의 승인이 필요, 2) 복잡한 APT 사고는 자동 판정이 어려움, 3) 새로운 유형의 공격은 플레이북이 없음, 4) 오탐 가능성이 있는 경우 사람의 판단이 필요. 완전 자동화보다 사람+자동의 하이브리드가 현실적이다.
</details>

---

## 과제

### 과제 1: SOAR 플레이북 3개 설계 (필수)

다음 시나리오에 대한 플레이북을 설계하라:
1. **웹 스캔 + SQL Injection 복합 공격** 대응
2. **랜섬웨어 의심 파일 암호화** 대응
3. **내부자 위협 (비인가 데이터 접근)** 대응

각 플레이북에 트리거, 단계별 액션, 안전 장치, 롤백 절차를 포함할 것.

### 과제 2: OpsClaw SOAR 구현 (선택)

과제 1의 플레이북 중 1개를 OpsClaw execute-plan으로 구현하고:
1. 실제 실행 결과 (evidence 포함)
2. 자동 대응 시간 측정
3. 개선 사항 제안

---

## 보충: SOAR 플레이북 상세 설계

### 랜섬웨어 대응 플레이북

```bash
cat << 'SCRIPT' > /tmp/soar_ransomware.py
#!/usr/bin/env python3
"""SOAR 플레이북: 랜섬웨어 대응"""

print("=" * 60)
print("  SOAR 플레이북: 랜섬웨어 대응")
print("=" * 60)

steps = [
    {
        "step": 1,
        "name": "트리거",
        "trigger": "Wazuh FIM: 다수 파일 확장자 변경 탐지 (.encrypted, .locked)",
        "auto": True,
    },
    {
        "step": 2,
        "name": "즉시 격리",
        "action": "감염 서버 네트워크 즉시 차단 (nftables DROP ALL)",
        "auto": True,
        "command": "nft add rule ip filter input drop; nft add rule ip filter output drop",
        "safety": "내부 관리 IP(OpsClaw)는 예외",
    },
    {
        "step": 3,
        "name": "확산 방지",
        "action": "동일 네트워크 서버의 SMB/NFS 포트 일시 차단",
        "auto": True,
        "command": "nft add rule ip filter forward tcp dport {139,445,2049} drop",
        "safety": "비즈니스 영향 평가 후 실행",
    },
    {
        "step": 4,
        "name": "증거 수집",
        "action": "메모리 덤프 + 디스크 이미지 수집",
        "auto": False,
        "command": "insmod lime.ko path=/evidence/mem.lime format=lime",
        "safety": "증거 해시 즉시 기록",
    },
    {
        "step": 5,
        "name": "영향 범위 파악",
        "action": "암호화된 파일 목록 + 랜섬노트 수집",
        "auto": True,
        "command": "find / -name '*.encrypted' -o -name 'README_DECRYPT*' 2>/dev/null",
        "safety": "읽기 전용 접근만",
    },
    {
        "step": 6,
        "name": "백업 확인",
        "action": "최신 정상 백업 존재 여부 + 무결성 확인",
        "auto": False,
        "command": "ls -la /backup/ && sha256sum /backup/latest.tar.gz",
        "safety": "백업 서버가 감염되지 않았는지 확인",
    },
    {
        "step": 7,
        "name": "알림",
        "action": "경영진 + CERT + 법률팀 알림",
        "auto": True,
        "command": "Slack #incident-critical + 이메일 + 전화",
        "safety": "TLP:RED로 공유 범위 제한",
    },
    {
        "step": 8,
        "name": "복구 결정",
        "action": "백업 복원 vs 복호화 도구 vs 몸값 지불(비권장)",
        "auto": False,
        "command": "경영진 의사결정 필요",
        "safety": "FBI/KISA 신고 검토",
    },
]

for step in steps:
    auto_mark = "[자동]" if step.get("auto") else "[수동]"
    print(f"\n  Step {step['step']}: {step['name']} {auto_mark}")
    if "trigger" in step:
        print(f"    트리거: {step['trigger']}")
    if "action" in step:
        print(f"    조치: {step['action']}")
    if "command" in step:
        print(f"    명령: {step['command'][:60]}")
    if "safety" in step:
        print(f"    안전: {step['safety']}")
SCRIPT

python3 /tmp/soar_ransomware.py
```

### 내부자 위협 대응 플레이북

```bash
cat << 'SCRIPT' > /tmp/soar_insider_threat.py
#!/usr/bin/env python3
"""SOAR 플레이북: 내부자 위협 대응"""

print("=" * 60)
print("  SOAR 플레이북: 내부자 위협 대응")
print("=" * 60)

steps = [
    ("트리거", "비인가 데이터 접근 또는 대량 다운로드 탐지", "[자동]"),
    ("Step 1", "접근 로그 수집 (who, what, when, where)", "[자동]"),
    ("Step 2", "사용자 프로파일 확인 (정상 행위 대비)", "[자동]"),
    ("Step 3", "HR 부서 확인 (퇴사 예정, 징계 이력)", "[수동]"),
    ("Step 4", "추가 모니터링 강화 (DLP, 화면 녹화)", "[수동]"),
    ("Step 5", "데이터 유출 여부 확인 (USB, 이메일, 클라우드)", "[자동]"),
    ("Step 6", "법률/HR 협의 후 계정 조치 결정", "[수동]"),
    ("Step 7", "증거 보존 (법적 절차 대비)", "[자동]"),
    ("Step 8", "보고서 작성 (비밀 유지)", "[수동]"),
]

for name, action, auto in steps:
    print(f"\n  [{name}] {auto}")
    print(f"    {action}")

print("""
주의사항:
  - 내부자 위협 조사는 극비로 진행
  - HR/법률팀과 사전 협의 필수
  - 무고한 직원의 프라이버시 보호
  - 모든 증거는 법적 요건 충족
""")
SCRIPT

python3 /tmp/soar_insider_threat.py
```

### SOAR 플레이북 테스트 프레임워크

```bash
cat << 'SCRIPT' > /tmp/soar_test_framework.py
#!/usr/bin/env python3
"""SOAR 플레이북 테스트 프레임워크"""

test_cases = [
    {
        "id": "TC-001",
        "playbook": "Brute Force Response",
        "input": "SSH 실패 15회/5분, 외부 IP",
        "expected": "IP 자동 차단 + Slack 알림",
        "result": "PASS",
    },
    {
        "id": "TC-002",
        "playbook": "Brute Force Response",
        "input": "SSH 실패 15회/5분, 내부 IP(OpsClaw)",
        "expected": "차단 안 함 + 알림만",
        "result": "PASS",
    },
    {
        "id": "TC-003",
        "playbook": "Web Attack Response",
        "input": "SQL Injection 5회/5분",
        "expected": "WAF 룰 강화 + IP 차단",
        "result": "PASS",
    },
    {
        "id": "TC-004",
        "playbook": "Ransomware Response",
        "input": "100개 파일 확장자 변경",
        "expected": "서버 격리 + 긴급 알림",
        "result": "PASS",
    },
    {
        "id": "TC-005",
        "playbook": "Brute Force Response (중복)",
        "input": "이미 차단된 IP에서 다시 경보",
        "expected": "에러 없이 무시 (멱등성)",
        "result": "PASS",
    },
]

print("=" * 60)
print("  SOAR 플레이북 테스트 결과")
print("=" * 60)

pass_count = sum(1 for t in test_cases if t['result'] == 'PASS')
total = len(test_cases)

for tc in test_cases:
    mark = "[PASS]" if tc['result'] == 'PASS' else "[FAIL]"
    print(f"\n  {mark} {tc['id']}: {tc['playbook']}")
    print(f"    입력: {tc['input']}")
    print(f"    예상: {tc['expected']}")

print(f"\n=== 결과: {pass_count}/{total} 통과 ===")
SCRIPT

python3 /tmp/soar_test_framework.py
```

### 경보 인리치먼트(Enrichment) 자동화

```bash
cat << 'SCRIPT' > /tmp/alert_enrichment.py
#!/usr/bin/env python3
"""경보 인리치먼트 자동화"""

# 원본 경보
alert = {
    "rule_id": "100002",
    "description": "SSH 무차별 대입 공격 (10회/5분)",
    "src_ip": "203.0.113.50",
    "dst_ip": "10.20.30.100",
    "timestamp": "2026-04-04T10:15:23",
}

# 인리치먼트 결과
enrichment = {
    "GeoIP": {"country": "RU", "city": "Moscow", "asn": "AS12345"},
    "AbuseIPDB": {"score": 92, "reports": 47, "category": "brute-force"},
    "CDB_Match": {"list": "malicious_ips", "tag": "brute_force"},
    "VirusTotal": {"malicious": 12, "total": 87, "harmless": 60},
    "Internal_History": {"seen_before": True, "last_seen": "2026-04-02", "total_alerts": 8},
    "Target_Info": {"hostname": "siem", "role": "SIEM서버", "criticality": "HIGH"},
    "ATT&CK": {"technique": "T1110.001", "tactic": "Credential Access", "name": "Password Guessing"},
}

print("=" * 60)
print("  경보 인리치먼트 결과")
print("=" * 60)

print(f"\n원본 경보: {alert['description']}")
print(f"출발지: {alert['src_ip']} → 목적지: {alert['dst_ip']}")

print(f"\n=== 인리치먼트 추가 정보 ===")
for source, data in enrichment.items():
    print(f"\n  [{source}]")
    for key, value in data.items():
        print(f"    {key}: {value}")

# 종합 위험도 판정
risk_score = 0
if enrichment["AbuseIPDB"]["score"] > 80: risk_score += 30
if enrichment["CDB_Match"]["list"]: risk_score += 20
if enrichment["VirusTotal"]["malicious"] > 5: risk_score += 15
if enrichment["Internal_History"]["total_alerts"] > 5: risk_score += 15
if enrichment["Target_Info"]["criticality"] == "HIGH": risk_score += 20

print(f"\n=== 종합 위험도: {risk_score}/100 ===")
if risk_score >= 80:
    print(f"  판정: Critical → 즉시 자동 차단")
elif risk_score >= 60:
    print(f"  판정: High → 자동 차단 + 알림")
elif risk_score >= 40:
    print(f"  판정: Medium → 추가 분석 필요")
else:
    print(f"  판정: Low → 모니터링")
SCRIPT

python3 /tmp/alert_enrichment.py
```

> **배우는 것**: 경보에 GeoIP, TI 평판, 내부 이력, 대상 자산 정보를 자동으로 추가하면 분석가의 판단 시간을 크게 단축할 수 있다. 이것이 SOAR의 "Enrichment" 단계다.

### SOAR ROI 계산

```bash
cat << 'SCRIPT' > /tmp/soar_roi.py
#!/usr/bin/env python3
"""SOAR 투자 대비 효과(ROI) 계산"""

print("=" * 60)
print("  SOAR 도입 ROI 분석")
print("=" * 60)

# 비용 계산
analyst_salary = 60_000_000  # 연봉 6천만원
analysts = 5
hours_per_year = 2080

cost_before = {
    "분석가 인건비": analyst_salary * analysts,
    "수동 작업 시간 (시간/년)": 1500,
    "수동 작업 비용": int(1500 * (analyst_salary / hours_per_year)),
}

cost_after = {
    "분석가 인건비": analyst_salary * analysts,
    "SOAR 라이선스": 0,  # OpsClaw 오픈소스
    "자동화 후 수동 작업 (시간/년)": 450,
    "수동 작업 비용": int(450 * (analyst_salary / hours_per_year)),
    "구축/유지보수 비용": 10_000_000,
}

saving_hours = cost_before["수동 작업 시간 (시간/년)"] - cost_after["자동화 후 수동 작업 (시간/년)"]
saving_cost = cost_before["수동 작업 비용"] - cost_after["수동 작업 비용"] - cost_after["구축/유지보수 비용"]

print(f"\n--- 도입 전 ---")
print(f"  수동 작업: {cost_before['수동 작업 시간 (시간/년)']:,}시간/년")
print(f"  비용: {cost_before['수동 작업 비용']:,}원/년")

print(f"\n--- 도입 후 ---")
print(f"  수동 작업: {cost_after['자동화 후 수동 작업 (시간/년)']:,}시간/년")
print(f"  비용: {cost_after['수동 작업 비용']:,}원/년")
print(f"  구축비: {cost_after['구축/유지보수 비용']:,}원/년")

print(f"\n--- ROI ---")
print(f"  절감 시간: {saving_hours:,}시간/년 ({saving_hours/cost_before['수동 작업 시간 (시간/년)']*100:.0f}% 감소)")
print(f"  절감 비용: {saving_cost:,}원/년")
print(f"  추가 효과: MTTR 89% 단축, 야간 대응 가능, 일관성 향상")
SCRIPT

python3 /tmp/soar_roi.py
```

---

## 다음 주 예고

**Week 11: 인시던트 대응 심화**에서는 NIST IR 프레임워크를 기반으로 봉쇄 전략, 증거 수집, 증거 체인을 학습한다.
