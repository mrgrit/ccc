# Week 15: 기말 종합 인시던트 대응 훈련

## 학습 목표
- Red Team(공격)과 Blue Team(방어) 역할을 수행한다
- 전체 인시던트 대응 사이클(탐지-분석-격리-제거-복구-교훈)을 완수한다
- 14주간 학습한 관제/분석/대응 기술을 종합 적용한다
- 실전 수준의 인시던트 대응 보고서를 작성한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 전제 조건
- Week 01~14 전체 내용 숙지
- Wazuh, Suricata, nftables 운용 능력

---

## 1. 훈련 개요 (10분)

### 1.1 훈련 구성

```
Phase 1: 환경 점검 + 팀 구성 (15분)
Phase 2: Red Team 공격 (30분)
Phase 3: Blue Team 탐지/분석 (40분)
Phase 4: 격리/제거/복구 (30분)
Phase 5: 보고서 + 발표 (40분)
Phase 6: Lessons Learned (15분)
총 소요 시간: 3시간
```

### 1.2 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 탐지 속도 | 20% | 공격 시작부터 탐지까지 시간 |
| 분석 정확도 | 25% | ATT&CK 매핑, 영향 범위 파악 |
| 대응 적절성 | 25% | 격리/제거/복구 절차 |
| 보고서 품질 | 20% | 타임라인, 증거, 권고사항 |
| 팀워크 | 10% | 역할 분담, 커뮤니케이션 |

---

## 2. Phase 1: 환경 점검 (15분)

> **이 실습을 왜 하는가?**
> "기말 종합 인시던트 대응 훈련" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 Blue Team - 방어 환경 확인

> **실습 목적**: 기말 종합 훈련으로 Blue Team과 Red Team 역할을 모두 수행하며 실전 인시던트에 대응한다
>
> **배우는 것**: 공격 탐지, 분석, 격리, 복구, 보고까지 인시던트 대응 전 과정을 시간 압박 속에 수행한다
>
> **결과 해석**: 모든 공격을 탐지하고 ATT&CK 매핑 타임라인이 포함된 보고서가 완성되면 성공이다
>
> **실전 활용**: SOC 관제사의 역량은 실제 사고 상황에서 체계적으로 대응하는 능력으로 평가된다

```bash
echo "=== Blue Team: 방어 환경 점검 ==="

echo "--- [1] Suricata IPS (secu) ---"
ssh ccc@10.20.30.1 \
  "systemctl is-active suricata 2>/dev/null && echo 'Suricata: OK' || echo 'Suricata: DOWN'"

echo "--- [2] nftables (secu) ---"
ssh ccc@10.20.30.1 \
  "echo 1 | sudo -S nft list tables 2>/dev/null | wc -l | xargs -I{} echo 'nftables 테이블: {}'"

echo "--- [3] Wazuh SIEM (siem) ---"
ssh ccc@10.20.30.100 \
  "systemctl is-active wazuh-manager 2>/dev/null && echo 'Wazuh: OK' || echo 'Wazuh: DOWN'"

echo "--- [4] JuiceShop (web) ---"
ssh ccc@10.20.30.80 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ | xargs -I{} echo 'JuiceShop: HTTP {}'"
```

### 2.2 기준선 확보

```bash
echo "=== 기준선 확보 ==="

SURICATA_COUNT=$(ssh ccc@10.20.30.1 \
  "wc -l /var/log/suricata/fast.log 2>/dev/null | awk '{print \$1}'" 2>/dev/null)
echo "Suricata 기준선: ${SURICATA_COUNT:-0}줄"

WAZUH_COUNT=$(ssh ccc@10.20.30.100 \
  "wc -l /var/ossec/logs/alerts/alerts.json 2>/dev/null | awk '{print \$1}'" 2>/dev/null)
echo "Wazuh 기준선: ${WAZUH_COUNT:-0}줄"

echo "기준선 시간: $(date '+%Y-%m-%d %H:%M:%S')"
```

---

## 3. Phase 2: Red Team 공격 (30분)

### 3.1 Stage 1: 정찰

```bash
echo "=== Red Team: 정찰 ==="

ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "--- 포트 스캔 ---"
for port in 22 80 443 3000 8000 8080 3306 5432; do     # 반복문 시작
  (echo > /dev/tcp/10.20.30.1/$port) 2>/dev/null && echo "secu:$port OPEN" &
  (echo > /dev/tcp/10.20.30.100/$port) 2>/dev/null && echo "siem:$port OPEN" &
done
wait 2>/dev/null

echo ""
echo "--- 기술 스택 ---"
curl -sI http://localhost:3000/ | grep -iE "^(server|x-powered)"

echo ""
echo "--- 디렉토리 탐색 ---"
for path in admin api api-docs robots.txt .git package.json ftp; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  [ "$CODE" != "404" ] && echo "/$path -> HTTP $CODE"
done
ENDSSH
```

### 3.2 Stage 2: 초기 침투

```bash
echo "=== Red Team: 초기 침투 ==="

ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "--- SQL Injection ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')      # 요청 데이터(body)
echo "$RESULT" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    if 'authentication' in d:
        print('SQLi 인증 우회 성공')
    else:
        print('SQLi 실패')
except: print('파싱 오류')
" 2>/dev/null

echo ""
echo "--- 사용자 정보 수집 ---"
curl -s http://localhost:3000/api/Users 2>/dev/null | python3 -c "  # silent 모드
import json,sys
try:
    d = json.load(sys.stdin)
    users = d.get('data',[])
    print(f'사용자 목록: {len(users)}명')
    for u in users[:3]:                                # 반복문 시작
        print(f'  {u.get(\"email\",\"\")} (role: {u.get(\"role\",\"\")})')
except: print('접근 실패')
" 2>/dev/null
ENDSSH
```

### 3.3 Stage 3: SSH 무차별 대입

```bash
echo "=== Red Team: SSH 무차별 대입 시뮬레이션 ==="

ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
for i in 1 2 3; do                                     # 반복문 시작
  sshpass -p"wrong${i}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    badccc@10.20.30.1 echo "success" 2>/dev/null || echo "시도 $i: 실패"
done
echo "공격 완료. Blue Team 차례."
ENDSSH
```

---

## 4. Phase 3: Blue Team 탐지/분석 (40분)

### 4.1 경보 수집

```bash
echo "=== Blue Team: 경보 수집 ==="

echo "--- Suricata ---"
ssh ccc@10.20.30.1 \
  "tail -20 /var/log/suricata/fast.log 2>/dev/null"

echo ""
echo "--- Wazuh ---"
ssh ccc@10.20.30.100 << 'ENDSSH'  # 비밀번호 자동입력 SSH
tail -10 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "  # 파일 끝부분 출력
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        rule = a.get('rule',{})
        ts = a.get('timestamp','')[:19]
        agent = a.get('agent',{}).get('name','')
        print(f'  [{rule.get(\"level\",0):>2}] {ts} {agent} - {rule.get(\"description\",\"\")}')
    except: pass
" 2>/dev/null
ENDSSH
```

### 4.2 ATT&CK 매핑

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
attacks = [
    ("Reconnaissance", "T1046", "Network Service Discovery", "포트 스캔"),
    ("Initial Access", "T1190", "Exploit Public-Facing App", "SQL Injection"),
    ("Credential Access", "T1110", "Brute Force", "SSH 무차별 대입"),
    ("Collection", "T1213", "Data from Info Repositories", "/api/Users 접근"),
    ("Discovery", "T1083", "File and Directory Discovery", "디렉토리 탐색"),
]

print(f"{'단계':<20} {'기법':<45} {'증거'}")
print("=" * 80)
for phase, tid, tech, evidence in attacks:             # 반복문 시작
    print(f"{phase:<20} {tid} {tech:<35} {evidence}")
PYEOF
ENDSSH
```

### 4.3 LLM 종합 분석

```bash
curl -s http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC L2 분석관입니다. 인시던트를 종합 분석합니다. 한국어로 간결하게."},
      {"role": "user", "content": "보안 이벤트 분석:\n1. 포트 스캔 (secu/siem 대상)\n2. SQL Injection 인증 우회 성공\n3. /api/Users 사용자 목록 획득\n4. SSH 무차별 대입 3회\n5. .git, api-docs 탐색\n\n1) 위험도 2) 공격자 의도 3) 즉시 대응 권고"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. Phase 4: 격리/제거/복구 (30분)

### 5.1 즉시 대응

```bash
echo "=== Blue Team: 즉시 대응 ==="

echo "--- [1] 공격 IP 차단 (시뮬레이션) ---"
echo "  nft add rule inet filter input ip saddr 10.20.30.80 tcp dport 22 drop"

echo "--- [2] WAF 룰 강화 (시뮬레이션) ---"
echo "  SecRule ARGS \"@rx (?i)(union.*select|or.*1.*=.*1)\" \"deny,status:403\""

echo "--- [3] 세션 무효화 ---"
echo "  JuiceShop 관리자 세션 토큰 갱신 필요"
```

### 5.2 취약점 재점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "--- SQL Injection 재시도 ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')      # 요청 데이터(body)
if echo "$RESULT" | grep -q "authentication"; then
  echo "[STILL VULNERABLE] SQLi 동작 - 코드 수정 필요"
else
  echo "[FIXED] SQLi 차단됨"
fi

echo "--- /api/Users 접근 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/Users)
echo "API Users: HTTP $CODE"
ENDSSH
```

---

## 6. Phase 5: 보고서 (40분)

### 6.1 인시던트 대응 보고서

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
from datetime import datetime

report = f"""
{'='*70}
          인시던트 대응 보고서
{'='*70}

1. 개요
   분류: 웹 애플리케이션 침해 (SQLi + 정보 유출)
   심각도: High
   영향: JuiceShop 전체 사용자 데이터

2. 타임라인
   +00:00  포트 스캔 탐지 (Suricata)
   +00:05  SQL Injection 탐지
   +00:10  인증 우회 성공 확인
   +00:15  사용자 데이터 접근
   +00:20  SSH 무차별 대입
   +00:25  공격 IP 차단

3. ATT&CK 매핑
   T1046  Network Service Discovery
   T1190  Exploit Public-Facing Application
   T1110  Brute Force
   T1213  Data from Information Repositories

4. 대응 조치
   [완료] 공격 IP 방화벽 차단
   [완료] Suricata 룰 강화
   [필요] SQL Injection 코드 수정
   [필요] API 접근제어 강화

5. 권고사항
   [즉시] Parameterized Query 적용
   [즉시] /api/Users 인증 필수화
   [단기] WAF 룰 고도화
   [장기] 정기 취약점 점검 도입

6. Lessons Learned
   - SQL Injection은 여전히 최대 위협
   - Defense in Depth 전략 필수
   - 인시던트 훈련 정기 실시 필요

{'='*70}
"""
print(report)
PYEOF
ENDSSH
```

---

## 7. Phase 6: Lessons Learned (15분)

### 7.1 과목 총정리

```
Week 01-03: 기초       -> SOC 개론, 시스템/네트워크/웹 로그
Week 04-07: 분석       -> Wazuh, 경보 분석, SIGMA 룰
Week 08:    중간고사   -> 로그 분석 실습 시험
Week 09-10: 대응(1)    -> 인시던트 절차, 웹 공격 대응
Week 11-12: 대응(2,3)  -> 악성코드, 내부 위협
Week 13:    CTI        -> 위협 인텔리전스, IOC, 위협 헌팅
Week 14:    자동화     -> Bastion Agent Daemon
Week 15:    기말       -> 종합 인시던트 대응 훈련
```

### 7.2 핵심 역량 자가 진단

| 역량 | 확인 |
|------|------|
| Suricata 경보를 읽고 공격을 분류할 수 있는가? | |
| Wazuh에서 위협을 탐지할 수 있는가? | |
| ATT&CK 프레임워크에 공격을 매핑할 수 있는가? | |
| SIGMA 룰을 작성할 수 있는가? | |
| 인시던트 대응 보고서를 작성할 수 있는가? | |
| IOC 기반 위협 헌팅을 수행할 수 있는가? | |
| Bastion로 자동화 관제를 구성할 수 있는가? | |

---

## 핵심 정리

1. 인시던트 대응은 탐지-분석-격리-제거-복구-교훈의 체계적 사이클이다
2. Red/Blue Team 훈련은 실전 대응 능력을 키우는 최선의 방법이다
3. ATT&CK 매핑은 공격 이해와 방어 전략의 공통 언어다
4. 자동화와 인간 분석관의 협업이 최적 보안 관제 모델이다
5. Lessons Learned를 통한 지속적 개선이 보안 성숙도를 높인다

---

---

## 웹 UI 실습: Dashboard + OpenCTI 종합 관제 실습

> **목적**: 기말 종합 훈련에서 Wazuh Dashboard와 OpenCTI를 동시에 활용하여
> 실전 수준의 종합 관제를 수행한다.

### Wazuh Dashboard (https://10.20.30.100)

1. 브라우저 탭 1에서 `https://10.20.30.100` 접속
2. admin / 비밀번호 입력

### OpenCTI (http://10.20.30.100:8080)

1. 브라우저 탭 2에서 `http://10.20.30.100:8080` 접속
2. `admin@opencti.io` / `CCC2026!` 입력

### 실습 1: Blue Team - 실시간 Dashboard 관제

1. Wazuh Dashboard에서 **Events** 화면 열기
2. 시간 범위: "Last 15 minutes", 자동 새로고침 활성화
3. Red Team 공격 시작 후 경보가 나타나는 순서 기록:
   - 첫 번째 탐지 시간 (포트 스캔)
   - SQL Injection 관련 경보 시간
   - SSH 무차별 대입 경보 시간
4. 각 경보의 rule.level, 출발지 IP, ATT&CK 매핑 기록

### 실습 2: MITRE ATT&CK 실시간 매핑

1. **MITRE ATT&CK** 뷰에서 공격 진행에 따라 새 기법이 추가되는 것 관찰
2. 탐지된 전술 흐름 기록:
   - Reconnaissance → Initial Access → Credential Access → ...
3. 각 전술별 대표 경보 1건씩 스크린샷 또는 메모

### 실습 3: OpenCTI 인시던트 기록

1. OpenCTI에서 **Events** > **Incidents** 이동
2. 기말 훈련 인시던트 생성:
   - **Name**: `Final Exercise - Web Attack + SSH Brute Force`
   - **Severity**: `High`
   - **Description**: Red Team 공격 요약
3. 관련 IoC(공격자 IP), Attack Pattern(T1190, T1110) 연결
4. 타임라인에 Phase별 주요 이벤트 기록

### 실습 4: 종합 보고서를 위한 데이터 수집

1. Wazuh Dashboard에서 시간 범위를 훈련 전체 시간으로 설정
2. 다음 데이터 수집:
   - 총 경보 건수
   - Level 10+ 경보 건수
   - 탐지된 ATT&CK 기법 수
   - 에이전트별 경보 분포
3. OpenCTI에서 생성한 인시던트 페이지의 관계 그래프 캡처
4. 수집한 데이터를 인시던트 대응 보고서에 포함

> **핵심**: Wazuh Dashboard(실시간 탐지/분석)와 OpenCTI(위협 인텔리전스/인시던트 관리)를
> 동시에 활용하는 것이 현대 SOC의 표준 관제 모델이다.

---

> **실습 환경 검증 완료** (2026-03-28): Wazuh alerts.json/logtest/agent_control, SIGMA 룰, 경보 분석

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Wazuh SIEM (4.11.x)
> **역할:** 에이전트 기반 로그·FIM·SCA 통합 분석 플랫폼  
> **실행 위치:** `siem (10.20.30.100)`  
> **접속/호출:** Dashboard `https://10.20.30.100` (admin/admin), Manager API `:55000`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/var/ossec/etc/ossec.conf` | Manager 메인 설정 (원격, 전송, syscheck 등) |
| `/var/ossec/etc/rules/local_rules.xml` | 커스텀 룰 (id ≥ 100000) |
| `/var/ossec/etc/decoders/local_decoder.xml` | 커스텀 디코더 |
| `/var/ossec/logs/alerts/alerts.json` | 실시간 JSON 알림 스트림 |
| `/var/ossec/logs/archives/archives.json` | 전체 이벤트 아카이브 |
| `/var/ossec/logs/ossec.log` | Manager 데몬 로그 |
| `/var/ossec/queue/fim/db/fim.db` | FIM 기준선 SQLite DB |

**핵심 설정·키**

- `<rule id='100100' level='10'>` — 커스텀 룰 — level 10↑은 고위험
- `<syscheck><directories>...` — FIM 감시 경로
- `<active-response>` — 자동 대응 (firewall-drop, restart)

**로그·확인 명령**

- `jq 'select(.rule.level>=10)' alerts.json` — 고위험 알림만
- `grep ERROR ossec.log` — Manager 오류 (룰 문법 오류 등)

**UI / CLI 요점**

- Dashboard → Security events — KQL 필터 `rule.level >= 10`
- Dashboard → Integrity monitoring — 변경된 파일 해시 비교
- `/var/ossec/bin/wazuh-logtest` — 룰 매칭 단계별 확인 (Phase 1→3)
- `/var/ossec/bin/wazuh-analysisd -t` — 룰·설정 문법 검증

> **해석 팁.** Phase 3에서 원하는 `rule.id`가 떠야 커스텀 룰 정상. `local_rules.xml` 수정 후 `systemctl restart wazuh-manager`, 문법 오류가 있으면 **분석 데몬 전체가 기동 실패**하므로 `-t`로 먼저 검증.

### OpenCTI (Threat Intelligence Platform)
> **역할:** STIX 2.1 기반 위협 인텔리전스 통합 관리  
> **실행 위치:** `siem (10.20.30.100)`  
> **접속/호출:** UI `http://10.20.30.100:8080`, GraphQL `:8080/graphql`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/opt/opencti/config/default.json` | 포트·DB·ElasticSearch 접속 설정 |
| `/opt/opencti-connectors/` | MITRE/MISP/AlienVault 등 커넥터 |
| `docker compose ps (프로젝트 경로)` | ElasticSearch/RabbitMQ/Redis 상태 |

**핵심 설정·키**

- `app.admin_email/password` — 초기 관리자 계정 — 변경 필수
- `connectors: opencti-connector-mitre` — MITRE ATT&CK 동기화

**로그·확인 명령**

- `docker logs opencti` — 메인 플랫폼 로그
- `docker logs opencti-worker` — 백엔드 인제스트 워커

**UI / CLI 요점**

- Analysis → Reports — 위협 보고서 원문과 IOC
- Events → Indicators — IOC 검색 (hash/ip/domain)
- Knowledge → Threat actors — 위협 행위자 프로파일과 TTP
- Data → Connectors — 외부 소스 동기화 상태

> **해석 팁.** IOC 1건을 **관측(Observable)** → **지표(Indicator)** → **보고서(Report)**로 승격해 컨텍스트를 쌓아야 헌팅에 활용 가능. STIX relationship(`uses`, `indicates`)이 분석의 핵심.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://localhost:8003`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `packages/bastion/agent.py` | 메인 에이전트 루프 |
| `packages/bastion/skills.py` | 스킬 정의 |
| `packages/bastion/playbooks/` | 정적 플레이북 YAML |
| `data/bastion/experience/` | 수집된 경험 (pass/fail) |

**핵심 설정·키**

- `LLM_BASE_URL / LLM_MODEL` — Ollama 연결
- `CCC_API_KEY` — ccc-api 인증
- `max_retry=2` — 실패 시 self-correction 재시도

**로그·확인 명령**

- ``docs/test-status.md`` — 현재 테스트 진척 요약
- ``bastion_test_progress.json`` — 스텝별 pass/fail 원시

**UI / CLI 요점**

- 대화형 TUI 프롬프트 — 자연어 지시 → 계획 → 실행 → 검증
- `/a2a/mission` (API) — 자율 미션 실행
- Experience→Playbook 승격 — 반복 성공 패턴 저장

> **해석 팁.** 실패 시 output을 분석해 **근본 원인 교정**이 설계의 핵심. 증상 회피/땜빵은 금지.

---

## 실제 사례 (WitFoo Precinct 6 — 기말 IR 종합 훈련 채점 reference)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *기말 종합 IR 훈련* 학습 항목 매칭. 14주 record 인용 + 6단계 IR + 만점 양식.

### 14주 record 인용 통합 표

| 본 과목 주차 | dataset record |
|------------|------------|
| w01 SOC 개론 | 5,673 events/일 funnel |
| w02 Windows event | top 10 = 38만 |
| w03 네트워크 로그 | Cisco ASA + WAF CEF |
| w04 Wazuh 환경 | winlogbeat 38만 |
| w05 경보 분석 | severity × suspicion 매트릭스 |
| w06 ATT&CK | message_type → Tactic 매핑 |
| w07 SIGMA | dataset 595K edges P/R |
| w09 IR 절차 | lifecycle (none 91.7% / initial 2.2% / complete 6.1%) |
| w10 웹 IR | WAF POST + JSESSIONID |
| w11 악성코드 IR | 4688 + 4690 + 4663 chain |
| w12 내부 위협 | top user Pareto + 4798/4799 |
| w13 CTI | STIX 75만 객체 |
| w14 Bastion 자동화 | R3 +243 fix, 66.3% |

### 만점 채점 양식

dataset 의 *6 단계 IR + 4-layer 익명화 + 7+ framework 매핑* 갖춘 보고서 = 만점.

**학생 액션**: 기말 시험에 14주 record 인용 표 부록 첨부 → dataset 양식 모방 = 만점 보장.

