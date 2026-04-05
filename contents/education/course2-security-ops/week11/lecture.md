# Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response

## 학습 목표
- FIM(File Integrity Monitoring)을 설정하고 파일 변경을 탐지할 수 있다
- SCA(Security Configuration Assessment)로 보안 설정을 평가할 수 있다
- Active Response를 구성하여 위협에 자동 대응할 수 있다

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

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |

---

# Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response

## 학습 목표

- FIM(File Integrity Monitoring)을 설정하고 파일 변경을 탐지할 수 있다
- SCA(Security Configuration Assessment)로 보안 설정을 평가할 수 있다
- Active Response를 구성하여 위협에 자동 대응할 수 있다

---

## 1. FIM (File Integrity Monitoring)

### 1.1 FIM이란?

FIM은 중요 파일의 변경(생성, 수정, 삭제)을 실시간으로 감지하는 기능이다.

**왜 필요한가?**
- 공격자가 설정 파일을 변조하면 시스템이 장악된다
- `/etc/passwd`, `/etc/shadow` 변경 = 계정 추가/변조
- 웹쉘 업로드 = 웹 디렉터리에 새 파일 생성

### 1.2 FIM 동작 방식

```
초기 스캔 → 파일 해시(checksum) 저장
  ↓
주기적/실시간 스캔 → 해시 비교
  ↓
변경 감지 시 → 알림 생성 (who changed, when, what)
```

---

## 2. 실습 환경 접속

> **이 실습을 왜 하는가?**
> "Wazuh SIEM (3) — FIM, SCA, Active Response" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

> **실습 목적**: Wazuh의 FIM(파일 무결성 모니터링), SCA(보안 구성 평가), Active Response를 실습한다
>
> **배우는 것**: 중요 파일 변경 감지, 보안 설정 기준선 점검, 자동 대응 설정 방법을 배운다
>
> **결과 해석**: FIM 알림이 발생하면 모니터링 대상 파일이 변경된 것이고, SCA 점수가 낮으면 보안 설정이 미흡하다
>
> **실전 활용**: 컴플라이언스 감사에서 FIM과 SCA는 필수 보안 통제 증적이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100
```

---

## 3. FIM 설정

### 3.1 현재 FIM 설정 확인

```bash
echo 1 | sudo -S grep -A 30 "<syscheck>" /var/ossec/etc/ossec.conf | head -40
```

### 3.2 FIM 설정 항목

ossec.conf 내 `<syscheck>` 섹션:

```xml
<syscheck>
  <!-- 스캔 주기 (초) -->
  <frequency>600</frequency>

  <!-- 실시간 모니터링 디렉터리 -->
  <directories realtime="yes" check_all="yes">/etc,/usr/bin,/usr/sbin</directories>

  <!-- 웹 디렉터리 (웹쉘 탐지) -->
  <directories realtime="yes" check_all="yes" report_changes="yes">/var/www</directories>

  <!-- 감시 제외 -->
  <ignore>/etc/mtab</ignore>
  <ignore>/etc/resolv.conf</ignore>
  <ignore type="sregex">.log$</ignore>

  <!-- who-data (감사 로그 기반 - 누가 변경했는지 추적) -->
  <directories whodata="yes">/etc/passwd,/etc/shadow,/etc/sudoers</directories>
</syscheck>
```

| 옵션 | 설명 |
|------|------|
| `frequency` | 전체 스캔 주기 (초) |
| `realtime="yes"` | inotify 기반 실시간 감시 |
| `whodata="yes"` | audit 기반 변경자 추적 |
| `check_all="yes"` | 모든 속성 검사 (해시, 권한, 소유자 등) |
| `report_changes="yes"` | 파일 내용 변경 diff 기록 |
| `ignore` | 감시 제외 경로/패턴 |

### 3.3 FIM 설정 추가 (실습)

원격 서버에 접속하여 명령을 실행합니다.

```bash
# secu 서버 Agent 설정에 추가
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1  # 비밀번호 자동입력 SSH

echo 1 | sudo -S cat >> /var/ossec/etc/ossec.conf << 'FIMEOF'
<ossec_config>
  <syscheck>
    <frequency>300</frequency>

    <!-- 핵심 시스템 파일 실시간 감시 -->
    <directories realtime="yes" check_all="yes">/etc/passwd,/etc/shadow,/etc/sudoers</directories>

    <!-- nftables 설정 감시 -->
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/nftables.conf</directories>

    <!-- Suricata 설정/룰 감시 -->
    <directories realtime="yes" check_all="yes">/etc/suricata/suricata.yaml</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/suricata/rules</directories>

    <!-- 테스트용 디렉터리 -->
    <directories realtime="yes" check_all="yes" report_changes="yes">/tmp/fim_test</directories>
  </syscheck>
</ossec_config>
FIMEOF

# Agent 재시작
echo 1 | sudo -S systemctl restart wazuh-agent
```

### 3.4 FIM 테스트

```bash
# secu 서버에서 테스트
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# 테스트 디렉터리 생성
echo 1 | sudo -S mkdir -p /tmp/fim_test

# 파일 생성
echo 1 | sudo -S bash -c 'echo "original content" > /tmp/fim_test/test.txt'

# 잠시 대기 (초기 스캔)
sleep 10

# 파일 수정
echo 1 | sudo -S bash -c 'echo "modified content" >> /tmp/fim_test/test.txt'

# 새 파일 생성
echo 1 | sudo -S bash -c 'echo "suspicious" > /tmp/fim_test/webshell.php'
```

### 3.5 FIM 알림 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# siem 서버에서 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

echo 1 | sudo -S cat /var/ossec/logs/alerts/alerts.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        if 'syscheck' in str(r.get('groups',[])) or r.get('id','') in ['550','553','554']:
            sd = e.get('syscheck',{})
            print(f\"[FIM] {r.get('description','')} | File: {sd.get('path','?')}\")
            if sd.get('changed_attributes'):
                print(f\"  Changed: {sd['changed_attributes']}\")
    except: pass
" | tail -10
```

**예상 출력:**
```
[FIM] File added to the system. | File: /tmp/fim_test/test.txt
[FIM] Integrity checksum changed. | File: /tmp/fim_test/test.txt
  Changed: ['mtime', 'size', 'md5', 'sha1', 'sha256']
[FIM] File added to the system. | File: /tmp/fim_test/webshell.php
```

---

## 4. SCA (Security Configuration Assessment)

### 4.1 SCA란?

SCA는 시스템 설정이 보안 기준에 부합하는지 자동으로 검사하는 기능이다.

| 기준 | 설명 |
|------|------|
| CIS Benchmark | Center for Internet Security 벤치마크 |
| PCI-DSS | 카드결제 보안 표준 |
| HIPAA | 의료정보 보안 |

### 4.2 SCA 정책 파일 확인

```bash
echo 1 | sudo -S ls /var/ossec/ruleset/sca/
```

**예상 출력:**
```
cis_debian10.yml
cis_debian11.yml
cis_ubuntu22-04.yml
sca_unix_audit.yml
...
```

### 4.3 SCA 설정

ossec.conf:

```xml
<sca>
  <enabled>yes</enabled>
  <scan_on_start>yes</scan_on_start>
  <interval>12h</interval>
  <skip_nfs>yes</skip_nfs>
</sca>
```

### 4.4 SCA 결과 확인 (API)

```bash
# 토큰 획득
TOKEN=$(curl -s -u wazuh-wui:wazuh-wui -k -X POST \
  "https://10.20.30.100:55000/security/user/authenticate?raw=true")

# Agent 001(secu)의 SCA 결과
curl -s -k -X GET "https://10.20.30.100:55000/sca/001?pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40  # 인증 토큰
```

**예상 출력:**
```json
{
    "data": {
        "affected_items": [
            {
                "name": "CIS Benchmark for Debian/Ubuntu",
                "description": "CIS provides benchmarks...",
                "pass": 45,
                "fail": 12,
                "invalid": 3,
                "total_checks": 60,
                "score": 75
            }
        ]
    }
}
```

### 4.5 SCA 상세 결과

```bash
# 실패한 검사 항목 확인
curl -s -k -X GET \
  "https://10.20.30.100:55000/sca/001/checks/cis_debian11?result=failed&pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -60  # 인증 토큰
```

**예상 출력 (일부):**
```json
{
    "id": 6012,
    "title": "Ensure SSH root login is disabled",
    "description": "PermitRootLogin should be set to no",
    "rationale": "Disabling root login forces...",
    "remediation": "Edit /etc/ssh/sshd_config and set: PermitRootLogin no",
    "result": "failed"
}
```

### 4.6 SCA 점검 항목 예시

```bash
# 직접 확인할 수 있는 보안 설정들
echo "=== SSH 설정 ==="
echo 1 | sudo -S grep "PermitRootLogin" /etc/ssh/sshd_config

echo "=== 패스워드 정책 ==="
echo 1 | sudo -S grep "PASS_MAX_DAYS" /etc/login.defs

echo "=== 불필요한 서비스 ==="
echo 1 | sudo -S systemctl list-unit-files --state=enabled | grep -E "telnet|rsh|rlogin"
```

---

## 5. Active Response (자동 대응)

### 5.1 Active Response란?

특정 알림이 발생하면 자동으로 대응 조치를 실행하는 기능이다.

```
알림 발생 (Level 7+) → Active Response 트리거
  → 대응 스크립트 실행 (IP 차단, 서비스 재시작 등)
  → 일정 시간 후 자동 해제 (timeout)
```

### 5.2 기본 제공 대응 스크립트

```bash
echo 1 | sudo -S ls /var/ossec/active-response/bin/
```

| 스크립트 | 설명 |
|----------|------|
| `firewall-drop` | iptables/nftables로 IP 차단 |
| `host-deny` | /etc/hosts.deny에 추가 |
| `disable-account` | 계정 비활성화 |
| `restart-wazuh` | Wazuh 재시작 |

### 5.3 Active Response 설정

ossec.conf (Manager측):

```xml
<!-- 대응 명령 정의 -->
<command>
  <name>firewall-drop</name>
  <executable>firewall-drop</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<!-- 대응 규칙 -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5712</rules_id>     <!-- SSH 브루트포스 -->
  <timeout>600</timeout>         <!-- 10분 후 자동 해제 -->
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <level>12</level>              <!-- Level 12 이상 모든 알림 -->
  <timeout>3600</timeout>        <!-- 1시간 후 해제 -->
</active-response>
```

| 옵션 | 설명 |
|------|------|
| `command` | 실행할 대응 명령 |
| `location` | 실행 위치 (local/all/defined-agent) |
| `rules_id` | 트리거할 룰 ID |
| `level` | 트리거할 최소 레벨 |
| `timeout` | 대응 조치 지속 시간 (초) |

### 5.4 커스텀 Active Response 스크립트

nftables 방화벽 규칙을 설정합니다.

```bash
# 커스텀 대응 스크립트 생성
echo 1 | sudo -S tee /var/ossec/active-response/bin/custom-block.sh << 'AREOF'
#!/bin/bash

LOCAL=$(dirname $0)
cd $LOCAL
cd ../

PWD=$(pwd)
ACTION=$1
USER=$2
IP=$3
ALERTID=$4
RULEID=$5

# 로그 기록
echo "$(date) $ACTION $IP Rule:$RULEID" >> /var/ossec/logs/active-responses.log

if [ "$ACTION" = "add" ]; then
    # IP 차단 (nftables)
    nft add element inet filter blocklist "{ $IP }" 2>/dev/null  # nftables 규칙 조회
    echo "$(date) BLOCKED $IP" >> /var/ossec/logs/active-responses.log
elif [ "$ACTION" = "delete" ]; then
    # IP 차단 해제
    nft delete element inet filter blocklist "{ $IP }" 2>/dev/null  # nftables 규칙 조회
    echo "$(date) UNBLOCKED $IP" >> /var/ossec/logs/active-responses.log
fi

exit 0
AREOF

echo 1 | sudo -S chmod 750 /var/ossec/active-response/bin/custom-block.sh
echo 1 | sudo -S chown root:wazuh /var/ossec/active-response/bin/custom-block.sh
```

### 5.5 Active Response 테스트

```bash
# 수동으로 Active Response 실행 (테스트)
echo 1 | sudo -S /var/ossec/active-response/bin/firewall-drop add - 192.168.99.99 1234 5712

# 차단 확인
echo 1 | sudo -S iptables -L -n | grep 192.168.99.99

# 수동 해제
echo 1 | sudo -S /var/ossec/active-response/bin/firewall-drop delete - 192.168.99.99 1234 5712
```

### 5.6 Active Response 로그 확인

```bash
echo 1 | sudo -S cat /var/ossec/logs/active-responses.log | tail -10
```

---

## 6. FIM + Active Response 연동

파일 변조 감지 시 자동 대응:

```xml
<!-- ossec.conf에 추가 -->
<command>
  <name>notify-admin</name>
  <executable>custom-notify.sh</executable>
  <timeout_allowed>no</timeout_allowed>
</command>

<active-response>
  <command>notify-admin</command>
  <location>server</location>
  <rules_id>550,553,554</rules_id>  <!-- FIM 알림 -->
</active-response>
```

---

## 7. 종합 실습: 침입 시나리오

### 시나리오: SSH 브루트포스 → 로그인 성공 → 파일 변조

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 1단계: 브루트포스 시뮬레이션 (secu에서 siem으로)
for i in $(seq 1 10); do                               # 반복문 시작
  sshpass -p wrong ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 \
    wrongsiem@10.20.30.100 2>/dev/null
done

# 2단계: 정상 로그인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

# 3단계: 파일 변조
echo 1 | sudo -S bash -c 'echo "hacked" >> /tmp/fim_test/test.txt'
```

### 기대되는 Wazuh 알림 흐름:

```
1. Rule 5710 (Level 5): SSH 로그인 실패 x 10
2. Rule 5712 (Level 10): SSH 브루트포스 탐지
3. Active Response: 공격자 IP 차단
4. Rule 5715 (Level 3): SSH 로그인 성공
5. Rule 100005 (Level 12): 실패 후 성공 - 침입 의심
6. Rule 550 (Level 7): FIM - 파일 변경 감지
```

---

## 8. 실습 과제

### 과제 1: FIM 설정

1. secu 서버에서 `/etc/ssh/sshd_config` 파일을 FIM 감시 대상으로 추가
2. 파일을 수정하고 FIM 알림이 발생하는지 확인
3. 변경 내용(diff)이 기록되는지 확인

### 과제 2: SCA 분석

1. secu 서버의 SCA 결과를 조회
2. 실패한 항목 3개를 선택하여 원인과 조치 방안을 작성
3. 1개 항목을 실제로 수정하고 SCA를 재실행

### 과제 3: Active Response

1. SSH 브루트포스 탐지 시 IP를 차단하는 Active Response를 설정
2. 브루트포스를 시뮬레이션하여 자동 차단이 동작하는지 확인
3. timeout 후 자동 해제되는지 확인

---

## 9. 핵심 정리

| 개념 | 설명 |
|------|------|
| FIM | 파일 무결성 모니터링 (변경 탐지) |
| realtime | inotify 기반 실시간 감시 |
| whodata | audit 기반 변경자 추적 |
| report_changes | 파일 내용 diff 기록 |
| SCA | 보안 설정 자동 평가 (CIS 기반) |
| Active Response | 알림 기반 자동 대응 |
| firewall-drop | IP 차단 대응 스크립트 |
| timeout | 자동 대응 지속 시간 |

---

## 다음 주 예고

Week 12에서는 OpenCTI를 다룬다:
- 위협 인텔리전스 플랫폼 설치와 구성
- STIX/TAXII 기초
- 데이터 소스 연동

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** nftables에서 policy drop의 의미는?
- (a) 모든 트래픽 허용  (b) **명시적으로 허용하지 않은 모든 트래픽 차단**  (c) 로그만 기록  (d) 특정 IP만 차단

**Q2.** Suricata가 nftables와 다른 핵심 차이는?
- (a) IP만 검사  (b) **패킷 페이로드(내용)까지 검사**  (c) 포트만 검사  (d) MAC 주소만 검사

**Q3.** Wazuh에서 level 12 경보의 의미는?
- (a) 정보성 이벤트  (b) **높은 심각도 — 즉시 분석 필요**  (c) 정상 활동  (d) 시스템 시작

**Q4.** ModSecurity CRS의 Anomaly Scoring이란?
- (a) 모든 요청 차단  (b) **규칙 매칭 점수를 누적하여 임계값 초과 시 차단**  (c) IP 기반 차단  (d) 시간 기반 차단

**Q5.** 보안 솔루션 배치 순서(외부→내부)는?
- (a) WAF → 방화벽 → IPS  (b) **방화벽 → IPS → WAF → 애플리케이션**  (c) IPS → WAF → 방화벽  (d) 애플리케이션 → WAF

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): nftables(inet filter+ip nat), Suricata 8.0.4(65K룰), Apache+ModSecurity(:8082→403), Wazuh v4.11.2(local_rules 62줄), OpenCTI(200)
