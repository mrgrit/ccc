# Week 11: 인시던트 대응 실습 (2) - 악성코드

## 학습 목표
- 의심 파일과 프로세스를 조사하는 기법을 수행한다
- 악성코드 감염 징후를 시스템 로그에서 탐지한다
- Wazuh FIM/SCA를 활용한 악성코드 탐지를 이해한다
- 악성코드 격리와 제거 절차를 수행한다

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

# Week 11: 인시던트 대응 실습 (2) - 악성코드

## 학습 목표
- 의심 파일과 프로세스를 조사하는 기법을 수행한다
- 악성코드 감염 징후를 시스템 로그에서 탐지한다
- Wazuh FIM/SCA를 활용한 악성코드 탐지를 이해한다
- 악성코드 격리와 제거 절차를 수행한다

---

## 1. 시나리오: 서버 악성코드 감염 의심

### 1.1 환경

```
감염 의심 서버: secu (10.20.30.1) - 방화벽/IPS 서버
모니터링: siem (10.20.30.100) - Wazuh SIEM
분석 도구: web (10.20.30.80) - 파일 분석

공격 시나리오:
  1) 공격자가 웹 취약점을 통해 리버스셸 설치
  2) 지속성 확보를 위한 cron/systemd backdoor
  3) 정보 유출을 위한 외부 통신
```

### 1.2 악성코드 분류

| 유형 | 행위 | 탐지 포인트 |
|------|------|-----------|
| 웹셸 | 웹 경로에 실행 파일 생성 | FIM, 웹 로그 |
| 리버스셸 | 외부 서버로 연결 | 네트워크 로그, 프로세스 |
| 백도어 | cron/systemd에 등록 | auditd, FIM |
| 랜섬웨어 | 파일 암호화 | FIM (대량 변경), CPU 급증 |
| 코인 마이너 | CPU/GPU 점유 | 리소스 모니터링 |

---

## 2. 탐지 (Detection)

> **이 실습을 왜 하는가?**
> "인시던트 대응 실습 (2) - 악성코드" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 Wazuh 경보에서 악성코드 징후

> **실습 목적**: Wazuh FIM 경보를 분석하여 악성코드 감염 징후를 탐지하고 대응한다
>
> **배우는 것**: 파일 무결성 변경, 비정상 프로세스, 네트워크 연결 패턴에서 악성코드를 식별하는 방법을 배운다
>
> **결과 해석**: 시스템 파일 변경 + 외부 통신 증가 + 비정상 프로세스가 동시 발생하면 악성코드 감염을 의심한다
>
> **실전 활용**: 악성코드 인시던트 대응에서 FIM 기반 초기 탐지는 감염 확산을 막는 골든 타임 확보의 핵심이다

```bash
# Wazuh SIEM에서 파일 무결성 변경 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== Wazuh FIM 경보 확인 ==="

# FIM 관련 경보 (rule.group: syscheck)
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
alerts = []
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        if 'syscheck' in str(a.get('rule',{}).get('groups',[])):
            alerts.append(a)
    except: pass

print(f'FIM 경보 수: {len(alerts)}')
for a in alerts[-5:]:                                  # 반복문 시작
    rule = a.get('rule',{})
    syscheck = a.get('syscheck',{})
    print(f'  [{rule.get(\"level\",0)}] {rule.get(\"description\",\"\")}')
    print(f'       파일: {syscheck.get(\"path\",\"N/A\")}')
    print(f'       이벤트: {syscheck.get(\"event\",\"N/A\")}')
" 2>/dev/null || echo "FIM 경보 없음 (정상 환경)"

echo ""
echo "=== 높은 심각도 경보 (Level >= 10) ==="
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        if a.get('rule',{}).get('level',0) >= 10:
            rule = a['rule']
            print(f'  [{rule[\"level\"]}] {rule.get(\"id\",\"\")} - {rule.get(\"description\",\"\")}')
    except: pass
" 2>/dev/null | tail -10 || echo "고심각도 경보 없음"
ENDSSH
```

### 2.2 secu 서버 프로세스 조사

파일 시스템을 검색하여 보안 관련 항목을 찾습니다.

```bash
# 의심 프로세스 탐색
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 의심 프로세스 탐색 ==="

# 1. 비정상 네트워크 연결 프로세스
echo "--- 외부 연결 프로세스 ---"
ss -tnp 2>/dev/null | grep -v "127.0.0.1\|::1\|10.20.30" | head -10  # 소켓 상태: TCP

echo ""
echo "--- ESTABLISHED 연결 ---"
ss -tnp state established 2>/dev/null | head -10       # 소켓 상태: TCP

echo ""
# 2. 의심 프로세스 (숨김 파일에서 실행)
echo "--- /dev/shm, /tmp, /var/tmp 에서 실행 중인 프로세스 ---"
ls -la /dev/shm/ /tmp/ /var/tmp/ 2>/dev/null | grep -E "^-.*x" | head -10
ps aux 2>/dev/null | grep -E "/dev/shm|/tmp/\.|/var/tmp" | grep -v grep  # 프로세스 목록 조회

echo ""
# 3. 최근 생성/수정된 실행 파일
echo "--- 최근 24시간 내 변경된 실행 파일 ---"
find /usr/local/bin /usr/bin /opt -newer /tmp -maxdepth 2 -type f 2>/dev/null | head -10  # 시간 기준 파일 검색

echo ""
# 4. 숨김 파일 탐색
echo "--- 숨김 실행 파일 ---"
find /tmp /dev/shm /var/tmp -name ".*" -type f 2>/dev/null | head -10  # 이름 기준 파일 검색

echo ""
# 5. CPU 사용량 상위 프로세스
echo "--- CPU 상위 5개 프로세스 ---"
ps aux --sort=-%cpu 2>/dev/null | head -6              # 프로세스 목록 조회
ENDSSH
```

### 2.3 cron/systemd 백도어 탐색

시스템 서비스를 관리합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== cron 백도어 탐색 ==="

# 모든 사용자 crontab
echo "--- 전체 crontab ---"
for user in $(cut -d: -f1 /etc/passwd); do             # 반복문 시작
  CRON=$(crontab -l -u $user 2>/dev/null)
  if [ -n "$CRON" ]; then
    echo "[$user]"
    echo "$CRON"
    echo ""
  fi
done

# /etc/cron.d 디렉토리
echo "--- /etc/cron.d ---"
ls -la /etc/cron.d/ 2>/dev/null

echo ""
echo "=== systemd 서비스 탐색 ==="
# 최근 생성된 서비스 파일
echo "--- 사용자 정의 서비스 ---"
find /etc/systemd/system /usr/lib/systemd/system -name "*.service" -newer /etc/hostname 2>/dev/null | head -10  # 이름 기준 파일 검색

# 활성 상태의 의심 서비스
echo ""
echo "--- 활성 서비스 (사용자 정의) ---"
systemctl list-units --type=service --state=running 2>/dev/null | \
  grep -v -E "systemd|ssh|cron|docker|suricata|nftables|rsyslog|wazuh|dbus|getty" | head -10  # 패턴 검색

echo ""
echo "=== 로그인 기록 점검 ==="
echo "--- 최근 로그인 ---"
last -10 2>/dev/null                                   # 로그인 이력 조회

echo ""
echo "--- SSH 인증 실패 ---"
grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5  # 패턴 검색
ENDSSH
```

---

## 3. 분석 (Analysis)

### 3.1 의심 파일 정적 분석

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 의심 파일이 발견되었다고 가정하고 분석 절차 실습
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 파일 분석 시뮬레이션 ==="

# 분석용 샘플 파일 생성 (교육용)
cat > /tmp/.hidden_test << 'SAMPLE'
#!/bin/bash
# 교육용 샘플 - 실제 악성코드 아님
while true; do
  curl -s http://evil.example.com/beacon >/dev/null 2>&1  # silent 모드
  sleep 300
done
SAMPLE

# 1. 파일 유형 확인
echo "--- file 명령 ---"
file /tmp/.hidden_test                                 # 파일 유형 확인

# 2. 문자열 추출
echo ""
echo "--- strings 분석 ---"
strings /tmp/.hidden_test | grep -iE "http|curl|wget|nc|bash|eval|exec|base64"  # 바이너리 문자열 추출

# 3. 해시 계산 (IOC용)
echo ""
echo "--- 파일 해시 ---"
md5sum /tmp/.hidden_test 2>/dev/null                   # 해시값 계산
sha256sum /tmp/.hidden_test 2>/dev/null                # 해시값 계산

# 4. 파일 타임스탬프
echo ""
echo "--- 타임스탬프 ---"
stat /tmp/.hidden_test 2>/dev/null | grep -E "Access|Modify|Change|Birth"

# 정리
rm -f /tmp/.hidden_test                                # 파일 삭제
ENDSSH
```

### 3.2 네트워크 IOC 분석

로그나 설정에서 특정 패턴을 검색합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 네트워크 IOC 분석 ==="

# 1. DNS 쿼리 로그 (의심 도메인)
echo "--- DNS 쿼리 확인 ---"
grep -r "query" /var/log/syslog 2>/dev/null | grep -viE "local|arpa|ubuntu" | tail -5  # 디렉터리 재귀 검색

# 2. Suricata 알림에서 C2 통신 징후
echo ""
echo "--- Suricata C2 관련 알림 ---"
grep -iE "trojan|malware|c2|command.and.control|botnet|coinminer" \
  /var/log/suricata/fast.log 2>/dev/null | tail -10 || echo "C2 알림 없음"

# 3. 비정상 포트 연결
echo ""
echo "--- 비표준 포트 외부 연결 ---"
ss -tnp 2>/dev/null | awk '$4 !~ /:(22|80|443|8000|8002|3000)$/' | \
  grep -v "127.0.0.1\|::1" | head -10                  # 패턴 검색

# 4. iptables/nftables 로그에서 차단된 연결
echo ""
echo "--- 방화벽 차단 로그 ---"
dmesg 2>/dev/null | grep -iE "drop|reject|block" | tail -5  # 커널 메시지 조회
ENDSSH
```

### 3.3 LLM 기반 로그 분석

```bash
# Ollama로 의심 로그 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석관입니다. 보안 로그를 분석하여 악성코드 감염 여부를 판단합니다. 한국어로 답변하세요."},
      {"role": "user", "content": "다음 로그를 분석하세요:\n\n1. /dev/shm에 .cache라는 실행 파일 발견\n2. crontab에 \"*/5 * * * * /dev/shm/.cache\" 등록\n3. ss 출력에서 외부 IP 45.33.xx.xx:4444로 ESTABLISHED 연결\n4. 해당 프로세스 CPU 사용량 98%\n\n1) 악성코드 유형 추정\n2) MITRE ATT&CK 매핑\n3) 대응 우선순위\n를 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. 격리 (Containment)

### 4.1 네트워크 격리

nftables 방화벽 규칙을 설정합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 네트워크 격리 시뮬레이션 ==="

# 실제 격리는 수행하지 않음 - 규칙 예시만 표시
echo "--- 외부 통신 차단 nftables 규칙 (예시) ---"
cat << 'RULES'
# 감염 서버 외부 통신 차단 (관리 SSH만 허용)
nft add rule inet filter output ip daddr != 10.20.30.0/24 drop  # nftables 규칙 추가
nft add rule inet filter output tcp dport 22 ip daddr 10.20.30.0/24 accept  # nftables 규칙 추가

# 특정 C2 IP 차단
nft add rule inet filter output ip daddr 45.33.0.0/16 drop  # nftables 규칙 추가
nft add rule inet filter input ip saddr 45.33.0.0/16 drop  # nftables 규칙 추가
RULES

echo ""
echo "--- 현재 nftables 규칙 확인 ---"
echo "1" | sudo -S nft list ruleset 2>/dev/null | head -20
ENDSSH
```

### 4.2 프로세스 격리

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 프로세스 격리 절차 (교육용) ==="

cat << 'PROCEDURE'
악성 프로세스 격리 절차:

1. 프로세스 정보 수집 (kill 전에 반드시)
   $ ps aux | grep [의심PID]
   $ ls -la /proc/[PID]/exe
   $ cat /proc/[PID]/cmdline
   $ ls -la /proc/[PID]/fd/

2. 메모리 덤프 (포렌식용)
   $ gcore [PID]

3. 프로세스 중지
   $ kill -STOP [PID]    # 먼저 일시 중지
   $ kill -9 [PID]       # 확인 후 종료

4. 지속성 제거
   $ crontab -l | grep -v "의심파일" | crontab -
   $ systemctl disable 의심서비스

5. 의심 파일 격리
   $ mkdir -p /evidence/$(date +%Y%m%d)
   $ cp -p /dev/shm/.cache /evidence/$(date +%Y%m%d)/
   $ sha256sum /evidence/$(date +%Y%m%d)/.cache > /evidence/$(date +%Y%m%d)/hash.txt
   $ rm /dev/shm/.cache
PROCEDURE
ENDSSH
```

---

## 5. 제거 및 복구 (Eradication & Recovery)

### 5.1 시스템 무결성 검증

파일 시스템을 검색하여 보안 관련 항목을 찾습니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 시스템 무결성 검증 ==="

# 1. 패키지 무결성 확인
echo "--- dpkg 패키지 무결성 ---"
dpkg --verify 2>/dev/null | head -10 || echo "dpkg verify 미지원"

# 2. 중요 바이너리 해시 확인
echo ""
echo "--- 핵심 바이너리 해시 ---"
for bin in /usr/bin/ssh /usr/bin/sudo /usr/bin/curl /bin/bash; do  # 반복문 시작
  if [ -f "$bin" ]; then
    HASH=$(sha256sum "$bin" 2>/dev/null | cut -d' ' -f1)
    echo "$bin: ${HASH:0:16}..."
  fi
done

# 3. SSH 키 점검
echo ""
echo "--- SSH authorized_keys ---"
for home in /home/* /root; do                          # 반복문 시작
  if [ -f "$home/.ssh/authorized_keys" ]; then
    echo "[$home]"
    wc -l "$home/.ssh/authorized_keys" 2>/dev/null     # 줄/단어/바이트 수 카운트
    cat "$home/.ssh/authorized_keys" 2>/dev/null | head -3
  fi
done

# 4. SUID 파일 점검
echo ""
echo "--- 비정상 SUID 파일 ---"
find / -perm -4000 -type f 2>/dev/null | \
  grep -v -E "^/(usr/(bin|lib|sbin)|bin|sbin)/" | head -5 || echo "비정상 SUID 없음"  # 패턴 검색
ENDSSH
```

### 5.2 Wazuh SCA 활용

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== Wazuh SCA 결과 확인 ==="

cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
sca_alerts = []
for line in sys.stdin:                                 # 반복문 시작
    try:
        a = json.loads(line.strip())
        groups = a.get('rule',{}).get('groups',[])
        if 'sca' in groups or 'policy_monitoring' in str(groups):
            sca_alerts.append(a)
    except: pass

if sca_alerts:
    print(f'SCA 경보 수: {len(sca_alerts)}')
    for a in sca_alerts[-5:]:                          # 반복문 시작
        rule = a.get('rule',{})
        print(f'  [{rule.get(\"level\",0)}] {rule.get(\"description\",\"\")}')
else:
    print('SCA 경보 없음 (정책 점검 미구성 또는 정상)')
" 2>/dev/null
ENDSSH
```

---

## 6. 사후 분석과 보고 (Post-Incident)

### 6.1 인시던트 타임라인 작성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "인시던트 대응 보고서 작성 전문가입니다. 한국어로 작성합니다."},
      {"role": "user", "content": "다음 사건의 인시던트 대응 보고서 타임라인을 작성하세요:\n\n- 09:00 Wazuh FIM 경보: /dev/shm/.cache 파일 생성 탐지\n- 09:05 Suricata 경보: 외부 IP 45.33.x.x:4444 연결 시도\n- 09:10 SOC 분석관 확인: crontab에 5분마다 .cache 실행 등록\n- 09:15 CPU 98% 사용 확인 (코인 마이너 의심)\n- 09:20 네트워크 격리 (nftables 외부 차단)\n- 09:25 프로세스 중지, 파일 격리 및 해시 보존\n- 09:30 crontab 백도어 제거, 시스템 무결성 검증\n- 09:45 서비스 정상화 확인\n\nMITRE ATT&CK 매핑과 교훈(Lessons Learned)도 포함하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 6.2 ATT&CK 매핑 실습

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
attack_mapping = [
    ("Initial Access", "T1190", "Exploit Public-Facing App", "웹 취약점으로 초기 침입"),
    ("Execution", "T1059.004", "Unix Shell", "/dev/shm/.cache 실행"),
    ("Persistence", "T1053.003", "Cron", "crontab 등록으로 지속성 확보"),
    ("Defense Evasion", "T1564.001", "Hidden Files", ".cache 숨김 파일 사용"),
    ("Defense Evasion", "T1036", "Masquerading", "정상 파일명(.cache)으로 위장"),
    ("C2", "T1071.001", "Web Protocols", "HTTP로 C2 비콘 통신"),
    ("Impact", "T1496", "Resource Hijacking", "코인 마이너로 CPU 점유"),
]

print(f"{'Tactic':<20} {'ID':<14} {'Technique':<30} {'분석'}")
print("=" * 90)
for tactic, tid, tech, analysis in attack_mapping:     # 반복문 시작
    print(f"{tactic:<20} {tid:<14} {tech:<30} {analysis}")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. 악성코드 탐지는 FIM, 프로세스 모니터링, 네트워크 분석을 조합한다
2. /dev/shm, /tmp의 숨김 파일과 비정상 cron 항목이 주요 탐지 포인트다
3. 분석 전에 반드시 증거(해시, 메모리 덤프)를 보존한다
4. 격리는 네트워크 차단 후 프로세스 중지 순서로 수행한다
5. 사후 분석에서 ATT&CK 매핑과 Lessons Learned가 핵심이다
6. Wazuh FIM/SCA는 악성코드 탐지의 핵심 모니터링 도구다

---

## 다음 주 예고
- Week 12: 인시던트 대응 실습 (3) - 내부 위협 (sudo 남용, 비인가 접근)

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
