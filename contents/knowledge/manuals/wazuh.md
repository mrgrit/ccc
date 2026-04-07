# Wazuh SIEM 레퍼런스

## 개요

Wazuh는 오픈소스 보안 모니터링 플랫폼으로, SIEM(보안 정보 및 이벤트 관리), XDR(확장 탐지 및 대응), 규정 준수 모니터링 기능을 제공한다. OSSEC에서 파생되어 대폭 확장되었다.

---

## 1. 아키텍처

### 구성 요소

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Wazuh Agent │────▶│ Wazuh Manager   │────▶│ Wazuh        │
│ (10.20.30.x)│     │ (10.20.30.1)    │     │ Indexer      │
│             │     │ - Analysis      │     │ (OpenSearch) │
│ - 로그 수집  │     │ - Rule Engine   │     │              │
│ - FIM       │     │ - Active Resp.  │     └──────┬───────┘
│ - 취약점 탐지│     │ - API (:55000)  │            │
└─────────────┘     └─────────────────┘     ┌──────▼───────┐
                                            │ Wazuh        │
                                            │ Dashboard    │
                                            │ (:443)       │
                                            └──────────────┘
```

| 구성 요소         | 역할                                    | 기본 포트    |
|-------------------|-----------------------------------------|-------------|
| Wazuh Manager     | 이벤트 분석, 룰 매칭, 경고 생성         | 1514, 1515  |
| Wazuh Agent       | 호스트에서 로그/이벤트 수집             | —           |
| Wazuh Indexer     | 경고/이벤트 저장 및 검색 (OpenSearch)   | 9200        |
| Wazuh Dashboard   | 웹 UI (OpenSearch Dashboards)           | 443         |
| Wazuh API         | RESTful 관리 API                        | 55000       |

---

## 2. Agent 관리

### Agent 등록

```bash
# Manager에서 agent 등록 (agent-auth 사용)
# Agent 측에서 실행:
/var/ossec/bin/agent-auth -m 10.20.30.1

# 또는 Manager에서 수동 등록
/var/ossec/bin/manage_agents
# (A)dd, (E)xtract, (L)ist, (R)emove
```

### Agent 상태 확인

```bash
# Manager에서 모든 agent 목록
/var/ossec/bin/agent_control -l

# 특정 agent 상태
/var/ossec/bin/agent_control -i 001

# 연결된 agent만
/var/ossec/bin/agent_control -lc

# agent 재시작
/var/ossec/bin/agent_control -R 001

# Agent 측 상태 확인
systemctl status wazuh-agent
```

### Agent 그룹 관리

```bash
# 그룹 생성
/var/ossec/bin/agent_groups -a -g webservers

# agent를 그룹에 할당
/var/ossec/bin/agent_groups -a -i 001 -g webservers

# 그룹 목록
/var/ossec/bin/agent_groups -l

# 그룹별 설정 파일
# /var/ossec/etc/shared/webservers/agent.conf
```

---

## 3. ossec.conf 설정

경로: `/var/ossec/etc/ossec.conf`

### Manager 기본 설정

```xml
<ossec_config>
  <!-- 글로벌 설정 -->
  <global>
    <jsonout_output>yes</jsonout_output>
    <alerts_log>yes</alerts_log>
    <logall>no</logall>
    <email_notification>no</email_notification>
  </global>

  <!-- 원격 연결 (agent 수신) -->
  <remote>
    <connection>secure</connection>
    <port>1514</port>
    <protocol>tcp</protocol>
  </remote>

  <!-- Syslog 수신 -->
  <remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>udp</protocol>
    <allowed-ips>10.20.30.0/24</allowed-ips>
  </remote>

  <!-- 로그 분석 -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>

  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>

  <localfile>
    <log_format>apache</log_format>
    <location>/var/log/nginx/access.log</location>
  </localfile>

  <!-- 파일 무결성 모니터링 (FIM) -->
  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <directories check_all="yes" realtime="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories check_all="yes">/var/www</directories>
    <ignore>/etc/mtab</ignore>
    <ignore>/etc/resolv.conf</ignore>
  </syscheck>

  <!-- 루트킷 탐지 -->
  <rootcheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
  </rootcheck>

  <!-- 취약점 탐지 -->
  <vulnerability-detector>
    <enabled>yes</enabled>
    <interval>5m</interval>
    <run_on_start>yes</run_on_start>
    <provider name="canonical">
      <enabled>yes</enabled>
      <os>jammy</os>
    </provider>
  </vulnerability-detector>

  <!-- 룰 파일 포함 -->
  <ruleset>
    <decoder_dir>ruleset/decoders</decoder_dir>
    <rule_dir>ruleset/rules</rule_dir>
    <rule_exclude>0215-policy_rules.xml</rule_exclude>
    <list>etc/lists/audit-keys</list>

    <!-- 커스텀 룰/디코더 -->
    <decoder_dir>etc/decoders</decoder_dir>
    <rule_dir>etc/rules</rule_dir>
  </ruleset>
</ossec_config>
```

### Agent 설정

```xml
<ossec_config>
  <client>
    <server>
      <address>10.20.30.1</address>
      <port>1514</port>
      <protocol>tcp</protocol>
    </server>
    <enrollment>
      <enabled>yes</enabled>
      <manager_address>10.20.30.1</manager_address>
    </enrollment>
  </client>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>

  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <directories check_all="yes" realtime="yes">/etc</directories>
    <directories check_all="yes">/var/www/html</directories>
  </syscheck>
</ossec_config>
```

---

## 4. 커스텀 룰 작성

경로: `/var/ossec/etc/rules/local_rules.xml`

### 룰 문법

```xml
<group name="custom_rules,">

  <!-- 기본 룰 구조 -->
  <rule id="100001" level="10">
    <decoded_as>sshd</decoded_as>
    <match>Failed password</match>
    <description>SSH 로그인 실패</description>
    <group>authentication_failed,</group>
  </rule>

  <!-- 빈도 기반 룰 (5분 내 10회 실패) -->
  <rule id="100002" level="12" frequency="10" timeframe="300">
    <if_matched_sid>100001</if_matched_sid>
    <same_source_ip />
    <description>SSH 브루트포스 공격 탐지 — 5분 내 10회 실패</description>
    <group>authentication_failures,</group>
  </rule>

</group>
```

### 주요 룰 속성

| 속성               | 설명                                |
|--------------------|-------------------------------------|
| `id`               | 룰 고유 ID (100000 이상 권장)       |
| `level`            | 심각도 (0=무시 ~ 15=긴급)          |
| `frequency`        | 빈도 조건 (N회 이상)               |
| `timeframe`        | 시간 범위 (초)                      |
| `if_sid`           | 부모 룰 ID (하위 룰)               |
| `if_matched_sid`   | 빈도 룰의 대상 SID                 |
| `same_source_ip`   | 같은 출발지 IP 조건                 |
| `same_user`        | 같은 사용자 조건                    |

### 매칭 조건

| 태그               | 설명                                |
|--------------------|-------------------------------------|
| `<match>`          | 문자열 매칭                         |
| `<regex>`          | 정규표현식 (OSSEC 정규식)           |
| `<pcre2>`          | Perl 호환 정규표현식                |
| `<decoded_as>`     | 디코더 이름                         |
| `<srcip>`          | 출발지 IP 매칭                      |
| `<dstip>`          | 목적지 IP 매칭                      |
| `<user>`           | 사용자 이름                         |
| `<program_name>`   | 프로그램 이름                       |
| `<hostname>`       | 호스트 이름                         |
| `<status>`         | 상태 값                             |
| `<field>`          | 디코더 필드 매칭                    |

### 레벨 가이드

| 레벨  | 의미                          | 예시                        |
|-------|-------------------------------|-----------------------------|
| 0     | 무시                          | —                           |
| 2     | 시스템 저우선순위 알림        | 상태 변경                   |
| 3     | 성공 이벤트                   | 로그인 성공                 |
| 5     | 사용자 생성 오류              | 잘못된 비밀번호             |
| 7     | 잘못된 출처                   | 비정상 IP 접근              |
| 10    | 다중 사용자 오류              | 다수 로그인 실패            |
| 12    | 심각한 이벤트                 | 브루트포스 탐지             |
| 14    | 심각도 높은 공격              | 루트킷 탐지                 |
| 15    | 즉시 대응 필요                | 공격 성공 확인              |

---

## 5. 커스텀 디코더

경로: `/var/ossec/etc/decoders/local_decoder.xml`

```xml
<!-- CCC 앱 로그 디코더 -->
<decoder name="ccc-app">
  <prematch>^CCC-APP: </prematch>
</decoder>

<decoder name="ccc-app-login">
  <parent>ccc-app</parent>
  <regex>LOGIN (\S+) from (\S+) status:(\S+)</regex>
  <order>user, srcip, status</order>
</decoder>
```

---

## 6. 알림/로그 구조

### alerts.json

경로: `/var/ossec/logs/alerts/alerts.json`

```json
{
  "timestamp": "2024-12-15T10:30:45.000+0900",
  "rule": {
    "level": 10,
    "description": "SSH 브루트포스 공격 탐지",
    "id": "100002",
    "groups": ["authentication_failures"]
  },
  "agent": {
    "id": "001",
    "name": "web-server",
    "ip": "10.20.30.10"
  },
  "manager": {
    "name": "wazuh-manager"
  },
  "full_log": "Dec 15 10:30:45 web-server sshd[12345]: Failed password for admin from 192.168.1.100 port 54321 ssh2",
  "data": {
    "srcip": "192.168.1.100",
    "srcuser": "admin"
  },
  "location": "/var/log/auth.log",
  "decoder": {
    "name": "sshd"
  }
}
```

### 로그 파일 경로

| 파일                                     | 설명                  |
|------------------------------------------|-----------------------|
| `/var/ossec/logs/alerts/alerts.json`     | JSON 형식 경고        |
| `/var/ossec/logs/alerts/alerts.log`      | 텍스트 형식 경고      |
| `/var/ossec/logs/ossec.log`              | Manager/Agent 로그    |
| `/var/ossec/logs/archives/archives.json` | 전체 이벤트 아카이브  |

```bash
# 최근 경고 확인
tail -f /var/ossec/logs/alerts/alerts.json | jq .

# 레벨 10 이상 경고
jq 'select(.rule.level >= 10)' /var/ossec/logs/alerts/alerts.json

# 특정 룰 ID
jq 'select(.rule.id == "100002")' /var/ossec/logs/alerts/alerts.json

# agent별 경고 수
jq -r '.agent.name' /var/ossec/logs/alerts/alerts.json \
  | sort | uniq -c | sort -rn
```

---

## 7. Wazuh API

### 인증

```bash
# 토큰 발급
TOKEN=$(curl -s -u wazuh-wui:wazuh-wui -k \
  -X POST "https://10.20.30.1:55000/security/user/authenticate" \
  | jq -r '.data.token')

# 이후 요청에 토큰 사용
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/"
```

### 주요 API 엔드포인트

```bash
# Manager 정보
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/manager/info" | jq .

# Agent 목록
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/agents?pretty=true" | jq .

# 특정 Agent 정보
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/agents?agents_list=001" | jq .

# Agent 재시작
curl -s -k -H "Authorization: Bearer $TOKEN" \
  -X PUT "https://10.20.30.1:55000/agents/001/restart"

# 룰 목록
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/rules?limit=10&level=12-15" | jq .

# 최근 경고 조회
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/alerts?limit=10&sort=-timestamp" | jq .

# 시스템 취약점
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/vulnerability/001" | jq .

# SCA (보안 설정 평가) 결과
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.1:55000/sca/001" | jq .
```

---

## 8. Active Response

공격 탐지 시 자동으로 대응 액션을 실행한다.

### Manager 설정 (ossec.conf)

```xml
<!-- 방화벽 차단 커맨드 정의 -->
<command>
  <name>firewall-drop</name>
  <executable>firewall-drop</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<!-- Active Response 설정 -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100002</rules_id>      <!-- SSH 브루트포스 룰 -->
  <timeout>600</timeout>             <!-- 600초 후 자동 해제 -->
</active-response>

<!-- 커스텀 스크립트 -->
<command>
  <name>custom-block</name>
  <executable>custom-block.sh</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<active-response>
  <command>custom-block</command>
  <location>server</location>
  <level>12</level>                  <!-- 레벨 12 이상 -->
  <timeout>3600</timeout>
</active-response>
```

### 커스텀 Active Response 스크립트

경로: `/var/ossec/active-response/bin/custom-block.sh`

```bash
#!/bin/bash
# Active Response 스크립트 구조
ACTION=$1       # add 또는 delete
USER=$2         # 사용자 (없으면 -)
SRCIP=$3        # 출발지 IP

case "$ACTION" in
  add)
    # 차단 동작
    nft add element inet filter blocked_ips "{ $SRCIP }"
    logger -t active-response "Blocked IP: $SRCIP"
    ;;
  delete)
    # 해제 동작
    nft delete element inet filter blocked_ips "{ $SRCIP }"
    logger -t active-response "Unblocked IP: $SRCIP"
    ;;
esac

exit 0
```

---

## 9. 실습 예제

### 예제 1: 웹 공격 탐지 룰

```xml
<group name="ccc_web,">

  <!-- Suricata 경고 연동 -->
  <rule id="100010" level="10">
    <decoded_as>json</decoded_as>
    <field name="event_type">^alert$</field>
    <field name="alert.category">Web Application Attack</field>
    <description>Suricata 웹 공격 경고: $(alert.signature)</description>
    <group>ids,web_attack,</group>
  </rule>

  <!-- 웹쉘 접근 탐지 -->
  <rule id="100011" level="12">
    <decoded_as>nginx-accesslog</decoded_as>
    <pcre2>GET\s+/.*\.(php|jsp|asp)\?.*cmd=</pcre2>
    <description>웹쉘 명령 실행 시도</description>
    <group>web_attack,webshell,</group>
  </rule>

</group>
```

### 예제 2: 파일 무결성 변경 알림

```xml
<group name="ccc_fim,">

  <!-- 웹 루트 파일 변경 -->
  <rule id="100020" level="10">
    <if_sid>550</if_sid>
    <match>/var/www/html</match>
    <description>웹 루트 파일 변경 탐지: $(file)</description>
    <group>syscheck,web_integrity,</group>
  </rule>

  <!-- 설정 파일 변경 -->
  <rule id="100021" level="12">
    <if_sid>550</if_sid>
    <match>/etc/shadow</match>
    <description>패스워드 파일 변경 탐지</description>
    <group>syscheck,critical_file,</group>
  </rule>

</group>
```

### 예제 3: Suricata 로그 연동 설정

```xml
<!-- ossec.conf에 추가 -->
<localfile>
  <log_format>json</log_format>
  <location>/var/log/suricata/eve.json</location>
</localfile>
```

---

## 10. 운영 명령어

```bash
# 서비스 관리
systemctl status wazuh-manager
systemctl restart wazuh-manager

# 설정 검증
/var/ossec/bin/wazuh-analysisd -t

# 룰 테스트 (로그 라인으로)
echo 'Dec 15 10:30:45 server sshd[12345]: Failed password for root from 10.20.30.50 port 54321 ssh2' \
  | /var/ossec/bin/wazuh-logtest

# 클러스터 상태
/var/ossec/bin/cluster_control -l
/var/ossec/bin/cluster_control -i

# Agent 키 관리
/var/ossec/bin/manage_agents -l
```

---

## 참고

- 공식 문서: https://documentation.wazuh.com
- 룰셋: https://github.com/wazuh/wazuh-ruleset
- API 레퍼런스: https://documentation.wazuh.com/current/user-manual/api/reference.html
