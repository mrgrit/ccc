# Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response

## 학습 목표
- FIM(File Integrity Monitoring)을 설정하고 파일 변경을 탐지할 수 있다
- SCA(Security Configuration Assessment)로 보안 설정을 평가할 수 있다
- Active Response를 구성하여 위협에 자동 대응할 수 있다

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
ssh ccc@10.20.30.100
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
ssh ccc@10.20.30.1  # 비밀번호 자동입력 SSH

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
ssh ccc@10.20.30.1

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
ssh ccc@10.20.30.100  # 비밀번호 자동입력 SSH

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

**예상 출력**:
```
=== SSH 설정 ===
#PermitRootLogin prohibit-password
=== 패스워드 정책 ===
PASS_MAX_DAYS	99999
=== 불필요한 서비스 ===
```

> **해석 — 학생 호스트의 SCA 항목 즉시 진단**:
> - **`#PermitRootLogin`** 이 주석 (#) 처리 = SCA id 6012 `Ensure SSH root login is disabled` **fail** 가능성 높음. 조치: 주석 해제 + `PermitRootLogin no` 명시.
> - **`PASS_MAX_DAYS 99999`** = 비밀번호 만료 사실상 없음 = CIS 5.4.1.1 `Ensure password expiration is 365 days or less` **fail**. 조치: `PASS_MAX_DAYS 90` 또는 365 미만으로 변경.
> - **불필요 서비스 출력 비어있음** = telnet/rsh/rlogin 미설치 = CIS 2.1.x **pass**. 양호.
> - 이 3 항목 = SCA report 의 fail 항목 중 가장 빈번한 것 = 학습 우선순위 top.
> - SCA 자동 결과 (§ 4.4) 와 비교 — score 가 65 미만이면 즉시 본 항목들 조치 후 재실행.

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

**예상 출력 — `add` 직후**:
```
DROP       all  --  192.168.99.99        0.0.0.0/0
```

**예상 출력 — `delete` 직후**:
```
(출력 없음 — 룰 제거됨)
```

> **해석 — Active Response 동작 검증**:
> - **`DROP all 192.168.99.99 → 0.0.0.0/0`** = `firewall-drop` 스크립트가 `iptables -I INPUT -s 192.168.99.99 -j DROP` 실행 = 정상 동작.
> - **delete 후 출력 없음** = 룰 자동 해제 = `timeout` 또는 `delete` 액션 정상.
> - 운영 위험: `firewall-drop` 은 INPUT chain 에 INSERT 하므로 우선순위가 가장 높음 → **자기 IP 실수 차단 시 SSH 즉시 끊김**. 화이트리스트 (`/var/ossec/etc/lists/whitelist.cdb`) 등록 필수.
> - nftables 환경에서는 `firewall-drop` 이 `iptables-translate` 호환 모드로 동작 = `nft list ruleset | grep 99.99` 로도 확인.

### 5.6 Active Response 로그 확인

```bash
echo 1 | sudo -S cat /var/ossec/logs/active-responses.log | tail -10
```

**예상 출력**:
```
Wed May  6 14:22:18 KST 2026 add 192.168.99.99 Rule:5712
Wed May  6 14:22:18 KST 2026 BLOCKED 192.168.99.99
Wed May  6 14:22:35 KST 2026 delete 192.168.99.99 Rule:5712
Wed May  6 14:22:35 KST 2026 UNBLOCKED 192.168.99.99
```

> **해석 — AR audit trail**:
> - **add → BLOCKED → delete → UNBLOCKED** = 4 줄 1 cycle = 정상.
> - **timestamp 17 초 간격** = 수동 테스트 (delete 즉시 실행). 실제 운영은 `<timeout>600</timeout>` 으로 10 분 후 자동 unblock.
> - **Rule:5712** = SSH 브루트포스 룰 매치로 트리거된 사실 기록 = 사후 분석 / 컴플라이언스 evidence.
> - 본 로그 미출력 시: ① `<active-response>` 설정 누락, ② `manage_agents` 비활성, ③ wazuh-execd 데몬 inactive 점검.

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
    wrongccc@10.20.30.100 2>/dev/null
done

# 2단계: 정상 로그인
ssh ccc@10.20.30.100  # 비밀번호 자동입력 SSH

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

## 웹 UI 실습: Dashboard 알림에서 OpenCTI IoC 등록 워크플로우

> **실습 목적**: Wazuh Dashboard에서 탐지된 위협 알림의 IP/도메인을 OpenCTI에 IoC(침해 지표)로 등록하는 전체 워크플로우를 실습한다
>
> **배우는 것**: SIEM 알림 확인 -> 위협 정보 추출 -> CTI 플랫폼 등록의 실무 프로세스
>
> **실전 활용**: SOC 분석가의 핵심 업무 중 하나가 SIEM 알림에서 IoC를 추출하여 CTI 플랫폼에 등록하고, 이를 다시 탐지 룰에 반영하는 피드백 루프이다

### 1단계: Wazuh Dashboard에서 위협 알림 확인

1. **https://10.20.30.100:443** 접속 후 로그인
2. 왼쪽 메뉴 > **Security events** 클릭
3. 검색창에 다음 쿼리로 높은 심각도 알림 필터링:

```
rule.level >= 10
```

4. 결과에서 의심스러운 IP가 포함된 알림을 찾는다
5. 해당 알림을 클릭하여 상세 정보에서 다음을 메모한다:
   - **data.srcip**: 공격 출발지 IP (예: 192.168.99.99)
   - **rule.description**: 알림 설명
   - **rule.mitre.id**: MITRE ATT&CK 기법 ID (있을 경우)

### 2단계: OpenCTI에 IoC 등록

1. 새 탭에서 **http://10.20.30.100:8080** 접속
2. 로그인: `admin@opencti.io` / `CCC2026!`
3. 왼쪽 메뉴에서 **Observations** > **Indicators** 클릭
4. 우측 상단 **+** (추가) 버튼 클릭
5. Indicator 생성 양식 작성:
   - **Name**: 설명적 이름 (예: "SSH 브루트포스 공격 IP - 2026-04-08")
   - **Pattern type**: `stix`
   - **Pattern**: `[ipv4-addr:value = '의심 IP']` (예: `[ipv4-addr:value = '192.168.99.99']`)
   - **Valid from**: 오늘 날짜
   - **Score**: 위험도에 따라 50~100 설정
   - **Labels**: `malicious-activity` 선택
6. **Create** 버튼 클릭하여 저장

### 3단계: OpenCTI에서 등록된 IoC 확인

1. **Observations** > **Indicators** 목록에서 방금 등록한 항목 확인
2. 해당 Indicator를 클릭하면 상세 페이지에서:
   - **Overview**: 기본 정보 및 패턴
   - **Relationships**: 관련된 위협 행위자/캠페인 (연결 시)
   - **History**: 변경 이력
3. 우측 상단 **Export** > **STIX 2.1 bundle** 클릭하면 STIX JSON 파일로 내보내기 가능

### 4단계: 결과 저장 및 증적 확보

1. Wazuh Dashboard에서 해당 알림의 **CSV 내보내기** 수행
2. OpenCTI에서 Indicator 화면 캡처 또는 STIX 번들 다운로드
3. 이 두 자료를 연결하면 "알림 탐지 -> IoC 등록"의 완전한 증적이 된다

> **핵심 포인트**: 이 워크플로우를 자동화하면 Wazuh의 알림이 OpenCTI에 자동으로 등록되고, OpenCTI의 IoC가 다시 Wazuh CDB에 반영되는 **폐쇄 루프(closed loop)** 위협 관리가 가능하다. 수동 워크플로우를 먼저 이해한 후 자동화를 구현하는 것이 올바른 순서이다.

---

> **실습 환경 검증 완료** (2026-03-28): nftables(inet filter+ip nat), Suricata 8.0.4(65K룰), Apache+ModSecurity(:8082→403), Wazuh v4.11.2(local_rules 62줄), OpenCTI(200)

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

---

## 실제 사례 (WitFoo Precinct 6 — FIM 후보 + Active Response 트리거)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Wazuh — FIM·SCA·Active Response* 학습 항목과 매핑되는 dataset 의 *file 객체 변경* + *권한 변경* 트리거.

### Case 1: FIM 모니터링 대상 — dataset 의 *변경 추적* event

| message_type | FIM/SCA/AR 매핑 | 건수 | 의미 |
|--------------|---------------|------|------|
| 4663 (object access) | **FIM 트리거** | 98 | 모니터링 디렉토리 접근 |
| 4670 (permission change) | **FIM + AR** | 188 | 권한 변경 시 즉시 alert + active response |
| 4656 (handle open) | FIM 약함 | 79,311 | 베이스라인 (정상 운영) |
| 5136 (DS modified) | **AR critical** | 380 | AD 변경 즉시 격리 |
| 5140 (share access) | FIM medium | 2,623 | 공유 폴더 접근 추적 |
| security_audit_event | SCA 입력 | 381,552 | 보안 정책 준수 검증 |
| 4798/4799 (group enum) | **AR 의심** | 7,686 | enumeration 시 active response |

### Case 2: 권장 FIM/SCA/AR 설정

```xml
<!-- ossec.conf 의 syscheck (FIM) -->
<syscheck>
  <directories check_all="yes" report_changes="yes" realtime="yes">
    /etc, /usr/bin, /usr/sbin
  </directories>
  <directories check_all="yes" realtime="yes">
    /home, /root, /var/spool/cron
  </directories>
  <ignore>/var/log</ignore>
  <frequency>3600</frequency>  <!-- 1h 풀 스캔 -->
</syscheck>

<!-- SCA (Security Configuration Assessment) -->
<sca>
  <enabled>yes</enabled>
  <interval>12h</interval>
  <policies>
    <policy>cis_ubuntu_22.04.yml</policy>
    <policy>cis_distribution_independent_linux.yml</policy>
  </policies>
</sca>

<!-- Active Response — 4625 brute force 5회 시 24h block -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100221</rules_id>  <!-- 위 w10 의 brute force suspect 룰 -->
  <timeout>86400</timeout>
</active-response>
```

**해석 — 본 lecture (FIM/SCA/AR) 와의 매핑**

| 학습 항목 | 본 record 의 증거 |
|-----------|------------------|
| **FIM trigger 빈도** | 4663 = 98건 / 2.07M = 0.0047% = *극히 드문* event → FIM realtime 모니터링 가치 |
| **권한 변경 추적** | 4670 188건 + 5136 380건 — FIM 가 *감지 후 즉시 active response* 격리 권장 |
| **SCA baseline** | dataset 의 security_audit_event 38만건 — SCA 정책 적용 후 *fail count* 측정 가능 |
| **active response timeout** | brute force 5회 후 24h block — dataset 의 baseline 4625=0 (audit 미설정) 상태에서도 자체 룰로 가능 |

**학생 운영 액션**:
1. ossec.conf 에 4663 / 4670 / 5136 모두 alert 룰 정의 → dataset baseline 빈도와 비교 (5배 spike 시 FIM critical)
2. SCA `cis_ubuntu_22.04.yml` 적용 후 *pass/fail* 비율 측정 — dataset 의 security_audit_event 분포와 vendor 별 매칭
3. Active Response 의 24h block 정책 외에 *manual override* 절차 (오탐 시 unblock) 학생 syllabus 추가



---

## 부록: 학습 OSS 도구 매트릭스 (Course2 SecOps — Week 11 Wazuh FIM/SCA/AR)

| 작업 | 도구 |
|------|------|
| FIM | Wazuh syscheck / Tripwire / AIDE / Samhain |
| SCA | Wazuh SCA (CIS benchmarks) / OpenSCAP / Lynis |
| Active Response | Wazuh AR / fail2ban / shorewall / OSSEC AR |
| 무결성 baseline | wazuh-syscheckd / aide --init |
| 컨테이너 무결성 | Falco / Tetragon / Tracee |

### 학생 환경 준비
```bash
ssh ccc@10.20.30.80
sudo apt install -y aide tripwire lynis
sudo apt install -y libopenscap1 openscap-scanner
# Tracee — kernel-level (eBPF)
curl -L https://github.com/aquasecurity/tracee/releases/latest/download/tracee.tar.gz -o /tmp/tracee.tar.gz
```

### 핵심 시나리오
```bash
# 1) Wazuh FIM — 핵심 디렉토리 모니터링
sudo nano /var/ossec/etc/ossec.conf
# <syscheck> <directories check_all="yes">/etc</directories> ...
sudo systemctl restart wazuh-agent

# 2) AIDE 초기 baseline
sudo aide --init
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
# 일정 후
sudo aide --check                                                # 변경 보고

# 3) Lynis — 시스템 hardening 점검
sudo lynis audit system

# 4) OpenSCAP — CIS benchmark 자동 점검
sudo apt install -y libopenscap1 openscap-scanner ssg-base
sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
  --report /tmp/scan-report.html /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# 5) Wazuh Active Response (자동 차단)
# /var/ossec/etc/ossec.conf
# <command>name=firewall-drop, executable=firewall-drop, ...</command>
# <active-response>command=firewall-drop, location=local, level=10</active-response>
```

학생은 본 11주차에서 **FIM (AIDE/Wazuh) + SCA (Lynis/OpenSCAP) + Active Response (Wazuh AR/fail2ban)** 의 3 축 통합을 익힌다.
