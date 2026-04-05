# Week 10: Wazuh SIEM (2) — 탐지 룰

## 학습 목표
- Wazuh 룰의 XML 구조를 이해한다
- local_rules.xml에 커스텀 룰을 작성할 수 있다
- 디코더(decoder)의 역할을 이해하고 작성할 수 있다
- wazuh-logtest로 룰을 검증할 수 있다

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

# Week 10: Wazuh SIEM (2) — 탐지 룰

## 학습 목표

- Wazuh 룰의 XML 구조를 이해한다
- local_rules.xml에 커스텀 룰을 작성할 수 있다
- 디코더(decoder)의 역할을 이해하고 작성할 수 있다
- wazuh-logtest로 룰을 검증할 수 있다

---

## 1. Wazuh 룰 처리 흐름

```
로그 수신 → 디코더 (파싱) → 룰 매칭 → 알림 생성
```

| 단계 | 설명 |
|------|------|
| **디코더** | 원시 로그를 파싱하여 필드를 추출 (srcip, user, action 등) |
| **룰** | 추출된 필드를 조건과 비교하여 알림 생성 |

---

## 2. 실습 환경 접속

> **이 실습을 왜 하는가?**
> "Wazuh SIEM (2) — 탐지 룰" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

> **실습 목적**: Wazuh 커스텀 탐지 룰을 작성하여 특정 보안 이벤트를 식별하고 알림을 생성한다
>
> **배우는 것**: Wazuh 룰 XML 문법과 디코더 구조를 이해하고, 로그 패턴에 맞는 탐지 룰을 작성한다
>
> **결과 해석**: 테스트 이벤트 발생 후 alerts.json에 해당 룰 ID의 알림이 기록되면 룰이 정상 동작한다
>
> **실전 활용**: 조직 환경에 특화된 탐지 룰 작성은 SIEM 운영의 핵심이며, 미탐을 줄이는 핵심 방법이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100
```

---

## 3. 기본 룰 구조

> **이 실습의 목적:**
> Wazuh 탐지 룰은 SIEM의 **두뇌**이다. 로그가 수집되면 룰에 매칭하여 경보를 생성한다.
> 기본 룰(약 3,000개)은 SSH 실패, 파일 변경, 악성코드 등 일반적 위협을 탐지하지만,
> 우리 환경에 특화된 위협(SQLi, JuiceShop 공격 등)을 탐지하려면 **커스텀 룰**을 작성해야 한다.
>
> **실무 활용:** SOC 운영에서 새로운 위협이 보고되면 분석가가 커스텀 룰을 작성하여
> local_rules.xml에 추가하고, `wazuh-logtest`로 테스트한 후 배포한다.
>
> **검증 완료:** siem 서버의 local_rules.xml에 62줄의 커스텀 룰 존재 (이전 Blue Team에서 작성)

### 3.1 룰 파일 위치

> **왜 두 곳에 룰이 있는가?**
> `/var/ossec/ruleset/rules/`는 Wazuh가 제공하는 **기본 룰**이다. 업데이트 시 덮어쓰이므로 수정하면 안 된다.
> `/var/ossec/etc/rules/local_rules.xml`은 **사용자가 작성하는 커스텀 룰** 파일이다.
> 커스텀 룰은 기본 룰보다 우선 평가되며, 여기에 환경 특화 탐지 로직을 작성한다.

```bash
# 기본 룰 디렉토리 (수정 금지 — Wazuh 업데이트 시 덮어쓰임)
echo 1 | sudo -S ls /var/ossec/ruleset/rules/ | head -20
# 커스텀 룰 파일 (여기에 우리 환경 룰 작성)
echo 1 | sudo -S ls /var/ossec/etc/rules/
```

| 경로 | 설명 |
|------|------|
| `/var/ossec/ruleset/rules/` | Wazuh 기본 룰 (수정 금지) |
| `/var/ossec/etc/rules/local_rules.xml` | **커스텀 룰 (여기에 작성)** |

### 3.2 룰 XML 문법

```xml
<group name="그룹명,">
  <rule id="100001" level="5">
    <decoded_as>sshd</decoded_as>
    <match>Failed password</match>
    <description>SSH 로그인 실패</description>
  </rule>
</group>
```

| 요소 | 설명 |
|------|------|
| `id` | 룰 고유 ID (커스텀: 100000~) |
| `level` | 알림 레벨 (0~15) |
| `decoded_as` | 디코더 이름 매칭 |
| `match` | 로그 문자열 매칭 |
| `regex` | 정규표현식 매칭 |
| `srcip` | 출발지 IP 조건 |
| `user` | 사용자 조건 |
| `frequency` | 빈도 조건 (X초 내 Y회) |
| `timeframe` | 빈도 계산 시간 범위 |
| `if_sid` | 부모 룰 ID (연쇄 룰) |
| `if_matched_sid` | 빈도 기반 부모 룰 |
| `description` | 알림 설명 |
| `group` | 룰 그룹 (MITRE 매핑 등) |

---

## 4. 기본 룰 살펴보기

### 4.1 SSH 룰

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/rules/0095-sshd_rules.xml | head -40
```

**예시:**
```xml
<group name="syslog,sshd,">
  <rule id="5710" level="5">
    <if_sid>5700</if_sid>
    <match>illegal user|invalid user</match>
    <description>sshd: Attempt to login using a non-existent user</description>
    <group>authentication_failed,</group>
  </rule>

  <rule id="5712" level="10" frequency="8" timeframe="120" ignore="60">
    <if_matched_sid>5710</if_matched_sid>
    <description>sshd: brute force trying to get access to the system. Non existent user.</description>
    <group>authentication_failures,</group>
  </rule>
</group>
```

> Rule 5712는 Rule 5710이 120초 내 8회 발생하면 Level 10 알림을 생성한다 (브루트포스 탐지).

### 4.2 웹 공격 룰

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/rules/0260-nginx_rules.xml | head -30
```

---

## 5. 커스텀 룰 작성

### 5.1 local_rules.xml 확인

```bash
echo 1 | sudo -S cat /var/ossec/etc/rules/local_rules.xml
```

### 5.2 룰 1: 특정 사용자 로그인 감시

```bash
echo 1 | sudo -S tee /var/ossec/etc/rules/local_rules.xml << 'EOF'
<group name="local,custom,">

  <!-- 룰 1: root 사용자 SSH 로그인 -->
  <rule id="100001" level="10">
    <if_sid>5715</if_sid>
    <user>root</user>
    <description>경고: root 사용자 SSH 직접 로그인 감지</description>
    <group>authentication_success,pci_dss_10.2.5,</group>
  </rule>

  <!-- 룰 2: 업무시간 외 로그인 (22시~06시) -->
  <rule id="100002" level="8">
    <if_sid>5715</if_sid>
    <time>22:00-06:00</time>
    <description>주의: 업무시간 외 SSH 로그인 감지</description>
    <group>authentication_success,</group>
  </rule>

  <!-- 룰 3: sudo 실행 감시 -->
  <rule id="100003" level="5">
    <decoded_as>sudo</decoded_as>
    <match>COMMAND=</match>
    <description>sudo 명령 실행 감지</description>
    <group>audit,sudo,</group>
  </rule>

  <!-- 룰 4: 위험한 sudo 명령 -->
  <rule id="100004" level="12">
    <if_sid>100003</if_sid>
    <match>rm -rf|mkfs|dd if=|chmod 777|iptables -F</match>
    <description>심각: 위험한 sudo 명령 실행 감지</description>
    <group>audit,sudo,</group>
  </rule>

  <!-- 룰 5: 다수 인증 실패 후 성공 (침입 의심) -->
  <rule id="100005" level="12">
    <if_sid>5715</if_sid>
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>심각: 다수 인증 실패 후 로그인 성공 - 침입 의심</description>
    <group>authentication_success,attack,</group>
  </rule>

  <!-- 룰 6: Suricata 알림 연동 (높은 심각도) -->
  <rule id="100006" level="10">
    <decoded_as>json</decoded_as>
    <field name="event_type">alert</field>
    <field name="alert.severity">1</field>
    <description>Suricata 고심각도 알림 감지</description>
    <group>ids,suricata,</group>
  </rule>

  <!-- 룰 7: 새로운 서비스 포트 열림 -->
  <rule id="100007" level="7">
    <decoded_as>syslog</decoded_as>
    <match>Listening on</match>
    <description>새로운 네트워크 서비스 시작 감지</description>
    <group>service_start,</group>
  </rule>

  <!-- 룰 8: 패키지 설치 감시 -->
  <rule id="100008" level="7">
    <decoded_as>dpkg-decoder</decoded_as>
    <match>install </match>
    <description>새로운 패키지 설치 감지</description>
    <group>audit,software,</group>
  </rule>

</group>
EOF
```

### 5.3 룰 검증

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-analysisd -t
```

**예상 출력 (정상):**
```
wazuh-analysisd: Configuration check passed. Exiting.
```

오류가 있으면 해당 줄 번호와 메시지가 출력된다.

---

## 6. wazuh-logtest로 룰 테스트

### 6.1 logtest 실행

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-logtest
```

대화형 프롬프트가 나타난다. 로그 메시지를 입력하면 어떤 디코더와 룰이 매칭되는지 보여준다.

### 6.2 테스트 예시: SSH 로그인 실패

```
Type one log per line

Mar 27 10:30:15 secu sshd[12345]: Failed password for invalid user admin from 10.20.30.80 port 54321 ssh2
```

**예상 출력:**
```
**Phase 1: Completed pre-decoding.
       full event: 'Mar 27 10:30:15 secu sshd[12345]: Failed password for invalid user admin from 10.20.30.80 port 54321 ssh2'
       hostname: 'secu'
       program_name: 'sshd'

**Phase 2: Completed decoding.
       name: 'sshd'
       parent: 'sshd'
       srcip: '10.20.30.80'
       srcuser: 'admin'

**Phase 3: Completed filtering (rules).
       id: '5710'
       level: '5'
       description: 'sshd: Attempt to login using a non-existent user.'
       groups: '['syslog', 'sshd', 'authentication_failed']'
```

### 6.3 테스트 예시: root SSH 로그인 성공

```
Mar 27 10:35:00 secu sshd[12346]: Accepted password for root from 10.20.30.80 port 54322 ssh2
```

**예상 출력:**
```
**Phase 3: Completed filtering (rules).
       id: '100001'
       level: '10'
       description: '경고: root 사용자 SSH 직접 로그인 감지'
```

### 6.4 테스트 예시: 위험한 sudo 명령

```
Mar 27 10:40:00 secu sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/rm -rf /tmp/test
```

Ctrl+C로 logtest를 종료한다.

---

## 7. 디코더 (Decoder)

### 7.1 디코더란?

디코더는 원시 로그 메시지에서 구조화된 필드를 추출하는 파서이다.

```
원시 로그:  "Mar 27 10:30:15 secu sshd[12345]: Failed password for admin from 10.20.30.80"
           ↓ 디코더
추출 필드:  program=sshd, srcuser=admin, srcip=10.20.30.80
```

### 7.2 기본 디코더 확인

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/decoders/0310-ssh_decoders.xml | head -30
```

### 7.3 커스텀 디코더 작성

애플리케이션 로그용 커스텀 디코더:

```bash
echo 1 | sudo -S tee /var/ossec/etc/decoders/local_decoder.xml << 'EOF'
<decoder name="opsclaw-app">
  <program_name>opsclaw</program_name>
</decoder>

<decoder name="opsclaw-app-fields">
  <parent>opsclaw-app</parent>
  <regex>user=(\S+) action=(\S+) target=(\S+) status=(\S+)</regex>
  <order>user, action, extra_data, status</order>
</decoder>

<decoder name="opsclaw-login">
  <parent>opsclaw-app</parent>
  <regex>LOGIN (\S+) from (\S+) status=(\S+)</regex>
  <order>user, srcip, status</order>
</decoder>
EOF
```

### 7.4 디코더와 연동된 룰

```bash
# local_rules.xml에 추가
echo 1 | sudo -S tee -a /var/ossec/etc/rules/local_rules.xml << 'RULEEOF'

<group name="opsclaw,">
  <rule id="100010" level="3">
    <decoded_as>opsclaw-app</decoded_as>
    <description>OpsClaw 애플리케이션 이벤트</description>
  </rule>

  <rule id="100011" level="5">
    <if_sid>100010</if_sid>
    <status>failed</status>
    <description>OpsClaw 로그인 실패</description>
  </rule>

  <rule id="100012" level="10" frequency="5" timeframe="120">
    <if_matched_sid>100011</if_matched_sid>
    <same_source_ip />
    <description>OpsClaw 브루트포스 공격 의심</description>
  </rule>
</group>
RULEEOF
```

### 7.5 디코더 테스트

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-logtest
```

입력:
```
Mar 27 11:00:00 siem opsclaw: LOGIN admin from 10.20.30.80 status=failed
```

**예상 출력:**
```
**Phase 2: Completed decoding.
       name: 'opsclaw-login'
       parent: 'opsclaw-app'
       srcip: '10.20.30.80'
       srcuser: 'admin'
       status: 'failed'

**Phase 3: Completed filtering (rules).
       id: '100011'
       level: '5'
       description: 'OpsClaw 로그인 실패'
```

---

## 8. 고급 룰 기법

### 8.1 복합 조건 (AND)

```xml
<rule id="100020" level="10">
  <if_sid>5715</if_sid>
  <srcip>!10.20.30.0/24</srcip>
  <user>root</user>
  <description>외부 IP에서 root SSH 접근</description>
</rule>
```

### 8.2 정규표현식 매칭

```xml
<rule id="100021" level="7">
  <decoded_as>syslog</decoded_as>
  <regex>CRON\[\d+\]: \(root\) CMD</regex>
  <description>root cron job 실행</description>
</rule>
```

### 8.3 연쇄 룰 (Composite)

```xml
<!-- 기본: 파일 변경 감지 -->
<rule id="100030" level="7">
  <if_sid>550</if_sid>
  <match>/etc/passwd</match>
  <description>passwd 파일 변경 감지</description>
</rule>

<!-- 연쇄: passwd 변경 후 새 프로세스 -->
<rule id="100031" level="12" timeframe="300">
  <if_sid>100030</if_sid>
  <description>passwd 변경 후 5분 이내 — 계정 추가 의심</description>
</rule>
```

### 8.4 MITRE ATT&CK 매핑

```xml
<rule id="100040" level="10">
  <if_sid>5712</if_sid>
  <description>SSH 브루트포스 공격</description>
  <mitre>
    <id>T1110.001</id>
  </mitre>
</rule>
```

---

## 9. 룰 적용 및 확인

### 9.1 설정 검증

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-analysisd -t
```

### 9.2 Manager 재시작

```bash
echo 1 | sudo -S systemctl restart wazuh-manager
echo 1 | sudo -S systemctl status wazuh-manager
```

### 9.3 알림 모니터링

```bash
echo 1 | sudo -S tail -f /var/ossec/logs/alerts/alerts.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        if int(r.get('id',0)) >= 100000:
            print(f\"[CUSTOM] Level {r['level']:>2} | Rule {r['id']} | {r['description']}\")
    except: pass
"
```

---

## 10. 실습 과제

### 과제 1: 커스텀 룰 작성

다음 이벤트를 탐지하는 룰을 작성하라:

1. `su` 명령으로 root 전환 시 Level 8 알림
2. `/etc/shadow` 파일 읽기 시도 시 Level 10 알림
3. 10분 내 SSH 로그인 실패 20회 시 Level 14 알림

### 과제 2: 커스텀 디코더 작성

다음 형식의 로그를 파싱하는 디코더를 작성하라:

```
Mar 27 12:00:00 web nginx: ACCESS src=10.20.30.80 method=GET uri=/admin status=403
```

추출할 필드: srcip, extra_data(method), url, status

### 과제 3: logtest 검증

작성한 디코더와 룰을 wazuh-logtest로 검증하라.

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| Decoder | 원시 로그 → 구조화 필드 추출 |
| Rule | 필드 조건 매칭 → 알림 생성 |
| local_rules.xml | 커스텀 룰 파일 |
| local_decoder.xml | 커스텀 디코더 파일 |
| `if_sid` | 부모 룰 기반 연쇄 |
| `if_matched_sid` | 빈도 기반 연쇄 |
| `frequency/timeframe` | X초 내 Y회 발생 조건 |
| `wazuh-logtest` | 대화형 룰 테스트 도구 |
| `wazuh-analysisd -t` | 설정 검증 |
| 커스텀 ID 범위 | 100000~ |

---

## 다음 주 예고

Week 11에서는 Wazuh의 고급 기능을 다룬다:
- FIM (File Integrity Monitoring)
- SCA (Security Configuration Assessment)
- Active Response (자동 대응)

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
