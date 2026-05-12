# Week 10 — Wazuh dashboard + 통합 운영 (osquery + ModSec audit + FIM + Active Response)

> **본 주차의 한 줄 요약**
>
> W09 의 manager (analysisd + 11 daemon + 3 agent) 위에서 **dashboard** (Web UI 5601 HTTPS)
> + **OpenSearch indexer** (9200) 의 visualization 활용 + 4 통합 패턴 (① ModSec audit
> ingest 활성 / ② osquery 통합 설계 / ③ syscheck FIM / ④ Active Response). 6v6 의 현
> 상태 — **sysmon-for-linux 미설치** (W11 본격), **osquery daemon 미운영** (ad-hoc only)
> 등 운영 갭 인지 + 보완 계획. 학습 마지막에 **R/B/P 통합 시나리오** (5 source XSS →
> dashboard 1 화면 통합) 수행.
>
> **운영자 한 줄 결론**: dashboard 가 SOC 의 single pane of glass. 모든 source 의 alert
> 이 1 화면에 모이고, 운영자가 5 초 안에 우선순위 판단.

---

## 학습 목표

본 주차 종료 시 학생은 다음 9가지를 **본인 손으로** 할 수 있어야 한다.

1. dashboard 의 5 main panel (Overview / Agents / Modules / Discovery / Rules) +
   접근 방법 (HAProxy `siem.6v6.lab` → dashboard:5601 TLS passthrough).
2. **OpenSearch indexer** (9200) 의 색인 + 쿼리 + dashboard 의 backend 역할.
3. **인증** — admin / 또는 LDAP / SSO 통합 + RBAC.
4. **ModSec audit ship** — web agent 의 ossec.conf 의 `<localfile>` 에 modsec_audit.log
   json 추가 + decoder (0025 Apache / 0250 Apache rule) 매핑.
5. **osquery 통합 설계** — 6v6 의 osqueryd 미운영 → daemon enable + scheduled query +
   /var/log/osquery/osqueryd.results.log ship.
6. **syscheck FIM** — manager + agent 측 `<syscheck>` directive + frequency + 알림 룰.
7. **Active Response** — manager 측 명령 정의 + agent 측 실행 + nftables 자동 차단.
8. **dashboard 트러블슈팅 4 패턴** — indexer 동기화 / login 실패 / panel 빈 화면 / alert
   지연.
9. **R/B/P 시나리오** — Red 가 XSS 5 burst → 5 source (Suricata / ModSec / Apache /
   osquery / syscheck) → dashboard 1 화면 통합 + Active Response 시뮬.

---

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용                                                                   | 유형     |
|-----------|-----------------------------------------------------------------------|----------|
| 0:00–0:25 | 이론 — dashboard 의 역할 + 5 main panel + 인증 모델                     | 강의     |
| 0:25–0:55 | 이론 — OpenSearch indexer + RBAC + 6v6 의 운영 갭 (osquery/sysmon 미운영) | 강의     |
| 0:55–1:05 | 휴식                                                                  | —        |
| 1:05–1:30 | 6v6 실측 — dashboard 접근 + ModSec audit 미설정 + sysmon 미설치          | 강의/토론|
| 1:30–2:00 | 실습 1, 2 — dashboard 인증 + panel navigation                          | 실습     |
| 2:00–2:30 | 실습 3, 4 — ModSec audit ship 설정 + osquery 통합 설계                  | 실습     |
| 2:30–2:40 | 휴식                                                                  | —        |
| 2:40–3:10 | 실습 5, 6 — syscheck FIM + Active Response 시뮬                        | 실습     |
| 3:10–3:30 | 실습 7 — **R/B/P** (XSS 5 burst → 5 source 통합)                        | 실습     |
| 3:30–3:40 | 정리 + W11 (sysmon-for-linux) 예고                                    | 정리     |

---

## 0. 용어 해설

| 용어 | 영문 | 뜻 |
|------|------|----|
| **dashboard** | — | Wazuh 의 Web UI (Kibana fork) |
| **OpenSearch** | — | Elasticsearch fork (Wazuh indexer 가 사용) |
| **panel** | — | dashboard 의 화면 단위 (Overview / Agents / Modules / Discovery / Rules) |
| **Overview panel** | — | 전체 alert 통계 (level / rule / agent 분포) |
| **Agents panel** | — | agent 별 상태 + alert |
| **Modules panel** | — | FIM / SCA / VD / Office365 / GCP 등 모듈 별 화면 |
| **Discovery** | — | OpenSearch 쿼리 + Kibana 식 visualization |
| **RBAC** | Role-Based Access Control | dashboard 의 권한 관리 |
| **filebeat** | — | manager 가 alerts.json 을 indexer 로 ship 하는 도구 |
| **indexer** | — | OpenSearch 백엔드 (색인 + 검색) |
| **syscheck** | — | Wazuh 의 FIM 모듈 |
| **SCA** | Security Configuration Assessment | CIS benchmark 자동 점검 |
| **VD** | Vulnerability Detection | CVE 기반 취약점 점검 |
| **Active Response** | AR | alert 시 자동 명령 (firewall-drop / disable-account 등) |
| **firewall-drop** | — | nftables 의 drop set 에 IP 추가 |
| **disable-account** | — | usermod -L lock |
| **CDB list** | — | constant database (key-value, IOC 화이트리스트 등) |

---

## 1. dashboard 의 자리 — SOC 의 single pane of glass

W09 의 manager (analysisd + alerts.json) 가 raw alert source. **dashboard 가 운영자
UI** — alerts.json 의 모든 라인을 OpenSearch 색인 → 운영자가 쿼리 + filter + chart.

### 1.1 데이터 흐름

```mermaid
graph LR
    AGT[3 agent ship]
    MGR[manager analysisd]
    AL[alerts.json]
    FB[filebeat]
    IDX[indexer OpenSearch 9200]
    DASH[dashboard 5601 HTTPS]
    USER[운영자 browser]
    AGT -->|1514 encrypted| MGR
    MGR --> AL
    AL --> FB
    FB --> IDX
    IDX --> DASH
    DASH --> USER
    style DASH fill:#1f6feb,color:#fff
```

### 1.2 6v6 접근

```
학생 PC browser → http(s)://siem.6v6.lab → HAProxy 80/443 → dashboard:5601 TLS passthrough
```

HAProxy 의 `is_siem` ACL 매칭 → backend dashboard → dashboard 의 self-signed cert →
HTTP/HTTPS 응답 → 인증 페이지.

### 1.3 인증 — default admin

```
URL: https://siem.6v6.lab/
User: admin
Password: admin (default — production 즉시 변경)
```

OR LDAP / SSO 통합 (관리자가 설정). 6v6 학습 환경은 default.

---

## 2. 5 main panel — 운영자 화면

### 2.1 Overview panel

전체 통계:
- alert level 분포 (parallel coordinate)
- rule.id top 10
- agent 별 alert 수
- timeline (24h / 7d / 30d)

### 2.2 Agents panel

- agent 별 상태 (Active / Disconnected / Pending)
- 마지막 keepalive
- agent IP / OS / version

### 2.3 Modules panel — 8+ 모듈

| 모듈 | 화면 |
|------|------|
| **Security events** | 모든 alert (default view) |
| **Integrity monitoring** | syscheck FIM 결과 |
| **Vulnerability detection** | CVE 검출 |
| **Configuration assessment** | SCA CIS 점검 |
| **Regulatory compliance** | PCI / HIPAA / GDPR |
| **MITRE ATT&CK** | T1xxx 매핑 |
| **Suricata** | Suricata 통합 (custom)  |
| **Docker listener** | Docker daemon 이벤트 |

### 2.4 Discovery panel — Kibana 식 query

- OpenSearch DSL 또는 KQL (Kibana Query Language)
- 예: `rule.level: 7 AND agent.name: web`
- 시각화 — bar / pie / area / data table

### 2.5 Management 의 Rules / Decoders

- 250+ default decoder + 700+ default rule list
- 검색 + edit (manager API 경유)

---

## 3. 6v6 의 운영 갭 — W10 의 책임

6v6 의 현재 상태 점검 (실측 2026-05-12):

| 갭 | 현재 | 운영 권장 |
|----|------|----------|
| **dashboard 인증** | admin/admin default | 강력 password + RBAC + LDAP |
| **ModSec audit ship** | web ossec.conf 의 localfile 미설정 | `<localfile>` 추가 + decoder 매핑 |
| **osquery daemon** | 미운영 (osqueryi only) | osqueryd 활성 + osquery.conf + log ship |
| **sysmon-for-linux** | 미설치 | W11 에서 본격 설치 |
| **integratord** | 미운영 | Slack / Virustotal 통합 |
| **clusterd** | 미운영 | HA 2+ manager |
| **bastion agent** | 미등록 | 등록 (W09 §4.2 참조) |
| **Active Response** | 미설정 | nftables drop + 자동화 |

본 주차는 ① ModSec audit ship ② osquery 통합 설계 ③ syscheck FIM ④ Active Response
4 갭을 보완.

---

## 4. ModSec audit ship — web agent 의 localfile 추가

### 4.1 현재 상태

```bash
ssh 6v6-web 'sudo grep -B1 -A3 "modsec" /var/ossec/etc/ossec.conf'
# 결과: 비어 있음 (미설정)
```

### 4.2 추가 패치 (시뮬)

```xml
<!-- /var/ossec/etc/ossec.conf 의 <ossec_config> 안 -->
<localfile>
  <log_format>json</log_format>
  <location>/var/log/apache2/modsec_audit.log</location>
</localfile>
```

`log_format json` → Wazuh 가 JSON 라인 그대로 파싱 → audit_data.messages[] 의 `[id "X"]`
embedded 가 0250-apache 룰의 regex 로 매핑.

### 4.3 적용 + 검증

```bash
# patch 적용 (실 적용 — 시뮬은 manager 측 shared config)
ssh 6v6-web 'sudo systemctl restart wazuh-agent'
sleep 5

# attacker XSS 트리거
ssh 6v6-attacker 'curl -s -o /dev/null -H "Host: juice.6v6.lab" "http://10.20.30.1/?q=<script>"'
sleep 8

# manager alerts.json 의 web agent + modsec 매치
ssh 6v6-siem 'sudo tail -20 /var/ossec/logs/alerts/alerts.json | jq "select(.agent.name==\"web\") | {rule_id:.rule.id, desc:.rule.description}"'
```

---

## 5. osquery 통합 설계 — daemon enable + log ship

### 5.1 현재 상태

W07 에서 본 것처럼 6v6 의 osquery 는 osqueryi only. osqueryd 미운영 → scheduled query
없음 → /var/log/osquery/ 비어 있음.

### 5.2 통합 설계 (3 단계)

**1단계 — osquery.conf 작성** (W07 §7-8 참조):
```json
{
  "options": { "logger_path": "/var/log/osquery", "host_identifier": "hostname" },
  "file_paths": { "system_etc": [...], "ssh_keys": [...], "cron_paths": [...] },
  "schedule": {
    "process_snapshot": {"query":"...","interval":60,"snapshot":true},
    "new_users": {"query":"...","interval":600,"removed":false},
    "listening_ports": {"query":"...","interval":60}
  }
}
```

**2단계 — osqueryd enable**:
```bash
sudo systemctl enable --now osqueryd
```

**3단계 — Wazuh agent 의 localfile 추가**:
```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/log/osquery/osqueryd.results.log</location>
</localfile>
```

Wazuh 의 `0545-osquery_rules.xml` 룰이 osquery 결과를 매핑 → alerts.json 에 적재.

### 5.3 통합 효과

- 4 호스트의 host visibility 가 dashboard 의 1 panel 로
- FIM (file_events) + scheduled query 모두 자동 alert
- baseline diff — 분기 검토

---

## 6. syscheck FIM — Wazuh 자체 FIM 모듈

osquery 의 FIM 외에 Wazuh 자체 FIM (syscheck daemon) 도 운영.

### 6.1 ossec.conf 의 `<syscheck>` directives

```xml
<syscheck>
  <disabled>no</disabled>
  <frequency>3600</frequency>
  <scan_on_start>yes</scan_on_start>

  <!-- 핵심 시스템 경로 -->
  <directories realtime="yes" check_all="yes">/etc/passwd,/etc/shadow,/etc/sudoers</directories>
  <directories realtime="yes" check_all="yes">/etc/cron.d,/etc/cron.daily,/etc/cron.hourly</directories>
  <directories realtime="yes" check_all="yes">/root/.ssh</directories>
  <directories realtime="yes" check_all="yes">/etc/apache2/sites-enabled</directories>

  <!-- 무시할 path -->
  <ignore>/etc/mtab</ignore>
  <ignore>/etc/resolv.conf</ignore>
</syscheck>
```

- `realtime="yes"`: inotify 기반 실시간 (FIM)
- `frequency 3600`: 1시간 마다 전체 스캔
- `check_all="yes"`: 모든 속성 (size / hash / mtime / owner)

### 6.2 syscheck 룰 — Wazuh default

| rule.id | 의미 |
|---------|------|
| 550 | Integrity checksum changed |
| 551 | Integrity checksum changed again |
| 553 | File deleted |
| 554 | File added |

운영 — `<directories>` 의 변경 시 자동 alert (default level 7).

### 6.3 osquery FIM 과의 비교

| 항목 | Wazuh syscheck | osquery file_events |
|------|----------------|---------------------|
| 매커니즘 | inotify + scheduled scan | inotify only |
| 결과 | alerts.json | osqueryd.results.log → Wazuh ship |
| 룰 | 550/551/553/554 | 사용자 정의 rule |
| 추가 정보 | hash / mtime / owner | category |

**보완 관계**: 두 도구 동시 운영 권장. Wazuh syscheck = manager 중심 (default), osquery
file_events = 추가 query 기능 (SQL 활용).

---

## 7. Active Response — 자동 차단

### 7.1 동작 원리

```mermaid
graph LR
    A[alert level 7+ 매치]
    EX[manager execd]
    AG[agent 측 execd]
    SCR["/var/ossec/active-response/bin/firewall-drop"]
    NFT[nftables drop set]
    A --> EX
    EX -->|agent ID 전달| AG
    AG --> SCR
    SCR --> NFT
    style NFT fill:#f85149,color:#fff
```

### 7.2 manager 측 ossec.conf

```xml
<active-response>
  <command>firewall-drop</command>
  <location>local</location>     <!-- agent 자기 자신에서 실행 -->
  <rules_id>5712,9009001</rules_id>
  <timeout>600</timeout>          <!-- 10분 후 자동 해제 -->
</active-response>
```

rule 5712 = SSH brute force, rule 9009001 = 사용자 정의 (예: sqlmap UA Wazuh 룰).

### 7.3 agent 측 — firewall-drop 스크립트

```bash
#!/bin/sh
# /var/ossec/active-response/bin/firewall-drop
ACTION=$1     # add / delete
SRCIP=$2

case $ACTION in
add)
    nft add element ip six_nat blocklist { $SRCIP }
    ;;
delete)
    nft delete element ip six_nat blocklist { $SRCIP }
    ;;
esac
```

(실 6v6 은 nftables 의 blocklist set + active-response 가 추가/삭제).

### 7.4 위험 + 운영 권장

- **자기 차단 위험**: 운영자 IP 가 IOC 매치 시 자기 차단
- **방어**: `<allow_list>` 에 운영자 IP / subnet 추가
- **timeout**: 너무 짧으면 효과 없음, 너무 길면 정상 사용자 차단 지속
- **로그**: `/var/ossec/logs/active-responses.log` 에 모든 AR 기록 + git audit

---

## 8. 트러블슈팅 — dashboard 운영 4 패턴

### 8.1 패턴 1 — login 실패

증상: admin/admin 도 안 됨.

진단: dashboard container log + indexer 의 password 검증.

```bash
ssh 6v6-wazuh-dashboard 'tail /var/log/wazuh-dashboard/*.log 2>&1 | tail'
```

해결: `wazuh-passwords-tool` 또는 indexer 의 internal_users.yml 의 password hash 변경.

### 8.2 패턴 2 — panel 빈 화면

증상: dashboard 의 Discovery 또는 Overview 가 비어 있음.

원인:
1. filebeat 가 manager 와 indexer 사이 ship 안 됨
2. indexer 의 색인 부재
3. dashboard 의 time range 가 잘못된 기간

진단:
```bash
ssh 6v6-siem 'sudo systemctl status filebeat'
ssh 6v6-wazuh-indexer 'curl -k -u admin:<pw> https://localhost:9200/_cat/indices/wazuh-*'
```

### 8.3 패턴 3 — alert 지연

증상: Suricata alert 발생 → 30+ 초 후 dashboard 에 표시.

원인:
1. manager analysisd 부하
2. filebeat queue 부담
3. indexer refresh interval (기본 1s)

해결: 보통 < 10 초 OK. 30+ 초 면 manager / indexer 자원 확인.

### 8.4 패턴 4 — RBAC 권한 오류

증상: 일부 사용자가 Modules 또는 Agents panel 못 봄.

해결: dashboard 의 Security > Roles 설정 + 사용자 매핑.

---

## 9. 사례 분석

### 9.1 ISMS-P 매핑

| Sub-control | 본 주차 활동 |
|-------------|-------------|
| 2.9.4 (모니터링 통합) | dashboard 의 single pane of glass |
| 2.9.6 (이상 행위 감지) | Active Response + level 7+ 자동 차단 |
| 2.10.3 (보안 점검) | SCA 모듈 + CIS benchmark |

### 9.2 NIST CSF — RS.RP (Response Planning)

Active Response 가 RS.RP-1 의 자동화 구현.

### 9.3 운영 사고 3 사례

**사례 1 — Active Response 자기 차단**:
```
운영자: AR firewall-drop 활성 → 자기 IP 가 IOC 매치 → 자기 차단
복구: bastion 의 console 접속 + AR allow_list 추가 + IP 해제
교훈: AR 도입 전 allow_list 사전 정의 + 시뮬 1주
```

**사례 2 — dashboard 의 alert 지연 100+ 초**:
```
운영자: manager 부하 시 alerts.json 적재 30+ 초 지연
원인: filebeat queue full + indexer disk I/O 부족
복구: filebeat의 spool size + indexer SSD
```

**사례 3 — dashboard 의 빈 화면 (filebeat 실패)**:
```
운영자: filebeat 가 indexer 연결 실패 → dashboard 빈 화면 → "SIEM 다운" 으로 인식
복구: filebeat restart + 연결 keystore 재구성
```

---

## 10. 실습 시나리오 (4 축)

### 실습 1 — dashboard 접근 + 인증

```bash
# Wazuh dashboard 의 외부 응답 — HAProxy 의 is_siem ACL 매칭 검증
#   -k: self-signed cert 무시 (학습 환경)
#   -o /dev/null: body 버림 (응답 코드만 확인)
#   -w "%{http_code}": HTTP 응답 코드 출력
#   -H "Host: siem.6v6.lab": HAProxy 가 dashboard backend 라우팅
curl -k -o /dev/null -s -w "%{http_code}\n" \
    -H "Host: siem.6v6.lab" "https://10.20.30.1/"
# 예상 응답:
#   302 → /app/login 으로 redirect (정상)
#   401 → 인증 필요
#   503 → backend (dashboard 컨테이너) down
#   200 → 이미 인증된 세션

# 학생 PC 브라우저로 https://siem.6v6.lab 접근
#   credential: admin / admin (default — production 즉시 변경)
#   첫 로그인 후 5 main panel (Overview / Agents / Modules / Discover / Settings)
```

### 실습 2 — OpenSearch indexer 의 색인

```bash
# Wazuh manager 가 alerts.json 을 filebeat 로 → wazuh-indexer 가 색인
#   wazuh-* 인덱스 패턴: wazuh-alerts-4.x-YYYY.MM.DD (일별 분리)
#   _cat/indices: 모든 인덱스 list (-h 로 출력 필드 제한)
#     index: 인덱스 이름
#     docs.count: 색인된 alert 갯수
docker exec 6v6-wazuh-indexer curl -k \
    -u admin:SecretPassword \
    "https://localhost:9200/_cat/indices/wazuh-*?h=index,docs.count"
# 예상 출력:
#   wazuh-alerts-4.x-2026.05.12 1234
#   wazuh-monitoring-4.x-2026.05.W19 567
#   wazuh-statistics-4.x-2026.05.W19 89
# docs.count = 0 면 manager → indexer ingestion 실패 (filebeat 점검)
```

### 실습 3 — ModSec audit ship (web agent.conf 패치 시뮬)

```bash
# web 의 Wazuh agent 가 modsec_audit.log 를 manager 에 ship 하려면 localfile 추가
#   /var/ossec/etc/agent.conf 또는 manager 의 shared/default/agent.conf 에 추가:
#     <localfile>
#       <log_format>json</log_format>
#       <location>/var/log/apache2/modsec_audit.log</location>
#     </localfile>
ssh 6v6-web 'sudo cat /var/ossec/etc/ossec.conf | grep -A3 modsec | head -10'
# 적용 후 wazuh-agent restart → manager 의 0245-modsec_rules.xml 가 매칭
# 검증: tail -f /var/ossec/logs/alerts/alerts.json | grep modsecurity
```

### 실습 4 — osquery 통합 설계 (시뮬, 실 적용은 W11)

```bash
# osquery → Wazuh agent localfile → manager → alerts.json 흐름
# 3 단계:
#   1. osquery daemon enable: systemctl enable --now osqueryd
#   2. /var/log/osquery/osqueryd.results.log 가 JSON 라인 형식 출력
#   3. agent.conf 의 localfile 추가:
#      <localfile>
#        <log_format>json</log_format>
#        <location>/var/log/osquery/osqueryd.results.log</location>
#      </localfile>
ssh 6v6-web 'sudo ls -la /var/log/osquery/ 2>/dev/null || echo "osqueryd 미시작"'
# 결과: 디렉토리 비어있음 → osqueryd 비활성 → W11 에서 활성화 후 통합
```

### 실습 5 — syscheck FIM 검증

```bash
# manager 의 ossec.conf 의 syscheck 섹션 확인
#   <syscheck>
#     <disabled>no</disabled>
#     <frequency>43200</frequency>      # 12시간 주기
#     <directories realtime="yes">/etc</directories>  # inotify 즉시 감지
#     <directories>/usr/bin,/usr/sbin</directories>   # 주기적 hash 비교
ssh 6v6-siem 'sudo grep -B1 -A5 "<syscheck>" /var/ossec/etc/ossec.conf | head -20'

# 변경 트리거 — web 에서 /etc/hosts 끝에 주석 추가
ssh 6v6-web 'echo "# fim_test_$(date +%s)" | sudo tee -a /etc/hosts'
sleep 60
# 60초 후 alert (realtime=yes 면 즉시, frequency 면 12시간)
ssh 6v6-siem 'sudo grep -m1 "rule.*550" /var/ossec/logs/alerts/alerts.json | jq ".syscheck"'
# 예상 출력:
#   {"path":"/etc/hosts","md5_before":"abc","md5_after":"def","size_after":...}
```

### 실습 6 — Active Response 시뮬

```bash
# Active Response 설정 — 특정 룰 매치 시 자동 명령 실행
#   <command>: 실행 binary 정의
#   <active-response>: trigger 룰 + location (local/agent) + timeout
ssh 6v6-siem 'sudo grep -B1 -A5 "active-response" /var/ossec/etc/ossec.conf | head -15'
# 예상:
#   <command><name>firewall-drop</name><executable>firewall-drop</executable></command>
#   <active-response><command>firewall-drop</command><rules_id>5712</rules_id>
#                    <timeout>600</timeout></active-response>

# Active Response 발생 history
ssh 6v6-siem 'sudo tail -20 /var/ossec/logs/active-responses.log 2>/dev/null'
# 예상:
#   <date> ossec-execd: firewall-drop add 10.20.30.99 (rule 5712)
#   <date+600> ossec-execd: firewall-drop delete 10.20.30.99 (timeout)
```

### 실습 7 — **R/B/P** XSS 5 burst → 5 source 통합

§11 참조.

---

## 11. R/B/P 통합 — XSS 5 burst → 5 source dashboard 통합

**Red**:
```bash
for i in 1 2 3 4 5; do
    ssh 6v6-attacker "curl -s -o /dev/null -H 'Host: juice.6v6.lab' 'http://10.20.30.1/?q=<script>$i</script>'"
done
```

**Blue — 5 source 추적**:
1. Suricata (이미 ingest) — ips agent rule 86xxx
2. ModSec (활성 시) — web agent Apache 0250 룰
3. Apache access log — web agent 의 access.log
4. osquery (활성 시) — process / socket / file
5. syscheck (변경 발생 시) — rule 550/554

```bash
DELTA=$(ssh 6v6-siem 'sudo wc -l /var/ossec/logs/alerts/alerts.json | awk "{print \$1}"')
ssh 6v6-siem "sudo tail -50 /var/ossec/logs/alerts/alerts.json | jq -r '.rule.groups | join(\",\")' | sort | uniq -c"
```

**Purple — dashboard 통합 visualization**:
- Overview: alert level 분포 + timeline
- Discovery: `rule.id: 86601 OR rule.id: 30xxx`
- MITRE ATT&CK panel: T1190 (Exploit Public-Facing App)

---

## 11.5 R/B/P 공격 분석 케이스 확장 (본 주차 추가)

### 11.5.0 R/B/P 일상 비유 — SOC 운영실의 한 화면

본 절은 Wazuh Dashboard 의 운영을 SOC 운영실의 한 화면 비유로 시작한다.

학생이 회사 SOC 운영실에 신입으로 입사했다고 상상해보자. 운영실 한가운데 큰 모니터가 한 대 있고, 그 화면에는 모든 시스템의 상태가 한 눈에 보인다. 화면은 5개 panel 로 나뉘어 있다.

- **Overview panel** — 오늘 발생한 alert 의 총합과 시간순 timeline.
- **Agents panel** — 현재 살아 있는 host 와 끊긴 host 의 목록.
- **Modules panel** — Security events, Integrity monitoring, MITRE ATT&CK 등 모듈 카드.
- **Discover panel** — Kibana 식 query 로 임의의 alert 를 검색.
- **Management panel** — rule, decoder, configuration 의 운영자 화면.

운영자는 한 화면에서 다섯 panel 을 모두 보면서, 같은 사건이 여러 source 에서 어떻게 보이는지 cross-cutting 으로 확인한다. 다섯 panel 의 통합이 SOC 의 single pane of glass 다.

| 일상 비유 | Wazuh Dashboard |
|-----------|-----------------|
| 운영실 큰 모니터 | Wazuh Dashboard 의 한 화면 |
| 5 panel | 5 main panel |
| 한눈에 보기 | single pane of glass |
| 같은 사건의 여러 측면 | 통합 (Suricata + ModSec + osquery + syscheck) |
| 운영자의 임시 query | Discover 의 free-text 검색 |

본 절은 다음 세 케이스를 다룬다.

- 케이스 1 — 한 XSS payload 가 web agent (ModSec) + ips agent (Suricata) 의 두 source 로 dashboard 에 통합되는 흐름.
- 케이스 2 — syscheck FIM 의 `/etc/passwd` 변경 alert 가 Integrity monitoring 모듈에서 어떻게 가시화되는지.
- 케이스 3 — MITRE ATT&CK panel 로 한 침해의 kill chain 을 시각화하기.

원칙은 W01 ~ W09 와 같다. 재현 가능성, 도구 위주 분석, 신입생 친화, 학습 환경 한정.

### 11.5.1 케이스 1 — XSS 한 건의 두 source 통합 표시

**0. 일상 비유 — 같은 강도 사건이 두 cctv 영상에 동시 출현.**

은행 정문 cctv (Suricata) 와 atm cctv (ModSec) 가 동시에 같은 사건을 녹화한다. SOC 운영자가 모니터의 timeline 을 보면 같은 시각에 두 source 에서 alert 가 동시각으로 표시된다. 한 사건의 두 측면이 한 화면에 보이므로 운영자가 단일 source 의 false positive 가능성을 즉시 판단할 수 있다.

| 일상 비유 | 두 source 통합 |
|-----------|----------------|
| 정문 cctv | ips 의 Suricata agent |
| atm cctv | web 의 ModSec agent (audit ship) |
| 한 사건 동시각 | 같은 src_ip + 같은 시각 |
| 한 화면 표시 | Wazuh Dashboard 의 Discover |
| 신뢰도 상승 | 두 source 결합 alert 의 P1 priority |

**0a. 사용 도구 사전 안내.**

- **Wazuh Dashboard 의 Modules → Security events.**
- **Discover 의 free-text query.**
- **`agent.name` 필드 + `rule.groups` 필드.**

**1. Red — 공격 재현.**

attacker VM 에서 XSS payload 한 줄을 보낸다. 학습 환경 한정으로 실행한다.

```bash
ssh ccc@192.168.0.112
# password: 1
```

```bash
# attacker VM 내부 (학습 환경 한정)
curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://192.168.0.103/search?q=%3Cscript%3Ealert(1)%3C/script%3E"
```

ips 의 Suricata 가 packet 단에서 XSS signature 를 인식한다. web 의 Apache 도 ModSec 로 같은 요청을 인식하고 audit log 에 한 줄 남긴다.

**2. 발생하는 로그/아티팩트.**

- ips 의 `/var/log/suricata/eve.json` → siem 의 alerts.json (agent.name=ips, rule.groups=suricata).
- web 의 `/var/log/apache2/modsec_audit.log` → siem 의 alerts.json (agent.name=web, rule.groups=modsecurity).

같은 src_ip + 같은 시각 범위 안에 두 줄이 동시 추가된다.

**3. Blue — Dashboard 의 Discover 에서 두 source 한 query.**

학생이 자기 host 의 web browser 에서 Wazuh Dashboard 에 접속한다.

- URL: `https://dashboard.6v6.lab`.

UI 클릭 흐름은 다음과 같다.

1. 좌측 햄버거 메뉴 → `Discover` 선택.
2. Index pattern 을 `wazuh-alerts-*` 로 바꾼다.
3. Time picker `Last 15 minutes`.
4. Search bar 에 `data.srcip:192.168.0.112 AND (agent.name:ips OR agent.name:web)` 입력 후 Enter.
5. 좌측 `Available fields` 에서 `agent.name`, `rule.groups`, `rule.description`, `data.alert.signature` 를 columns 에 추가한다.

결과 화면에서 두 줄이 같은 시각에 보인다.

```
14:30:00  agent=ips   rule.groups=suricata,attack    desc="ET WEB_SPECIFIC XSS ..."
14:30:01  agent=web   rule.groups=modsecurity,attack desc="ModSec 941100 XSS ..."
```

다음으로 상단의 `Visualize` 버튼을 눌러 timeline 시각화를 만든다.

1. Aggregation: `Count`.
2. X-axis: `Date Histogram` (timestamp).
3. Split series: `agent.name.keyword`.

같은 시각에 ips 와 web 두 source 가 각각 한 막대씩 보이면 통합 가시화 완료다.

**4. Blue — 대응 의사결정.**

학생이 다음 세 가지를 판단한다.

- **두 source 결합 alert 의 우선순위.** P2 (단일 source) → P1 (두 source 결합) 로 상향.
- **단일 source 의 false positive 가능성.** ips 단독 alert 는 packet 단의 pattern matching, web 단독 alert 는 application 단의 매칭. 두 결합은 false positive 가능성이 매우 낮다.
- **다음 단계 추적.** 같은 src_ip 가 다른 host 에서도 시도하고 있는지 Discover 의 query 로 확장 검색한다.

**5. Purple — Dashboard panel 추가.**

다음 세 가지를 적용한다.

- **`Saved search` 등록.** `data.srcip:* AND agent.name:(ips OR web)` 의 query 를 저장. 운영자가 매일 같은 query 를 즉시 호출 가능.
- **`Visualization` 등록.** Top src_ip × agent.name 의 매트릭스 시각화.
- **`Dashboard` 카드 등록.** 위 두 visualization 을 한 dashboard 카드에 묶어 운영실 모니터에 고정.

본 케이스 cycle 한 바퀴는 약 25분 정도다.

### 11.5.2 케이스 2 — syscheck FIM 의 `/etc/passwd` 변경 가시화

**0. 일상 비유 — 회원 명부 페이지 한 장이 새로 추가된 즉시 운영자에게 알람.**

도서관 회원 명부의 페이지가 한 장 새로 추가되면 즉시 운영자에게 알람이 간다. 운영자는 추가된 페이지의 내용 (누가 추가했는지, 어떤 정보가 적혀 있는지) 을 한 화면에서 본다. Wazuh 의 Integrity monitoring 모듈이 같은 역할을 한다.

| 일상 비유 | syscheck FIM |
|-----------|--------------|
| 명부 페이지 변경 | 감시 디렉토리의 파일 변경 |
| 즉시 알람 | realtime FIM event |
| 추가된 페이지 내용 | syscheck.path, syscheck.diff |
| 한 화면 보기 | Modules → Integrity monitoring |
| 변경 히스토리 | wazuh-states-fim-* 인덱스 |

**0a. 사용 도구 사전 안내.**

- **ossec.conf 의 `<syscheck>` 섹션.**
- **`<directories realtime="yes">`** — 실시간 감시.
- **Modules → Integrity monitoring.**

**1. Red — 공격 재현.**

attacker VM 에서 web VM 에 SSH 로 들어가 신규 사용자를 추가한다.

```bash
ssh ccc@192.168.0.112
ssh -o StrictHostKeyChecking=no admin@192.168.0.103

# web VM 안 (학습 환경 한정)
sudo useradd -m -s /bin/bash testfim
```

`/etc/passwd` 와 `/etc/shadow` 에 한 줄이 추가된다. syscheck realtime 이 즉시 인식한다.

**2. 발생하는 로그/아티팩트.**

- web 의 `/etc/passwd` 와 `/etc/shadow` 에 한 줄 추가.
- siem 의 alerts.json 에 syscheck event (rule.id 550 또는 554 시리즈).
- siem 의 `wazuh-states-fim-*` 인덱스에 변경 state 한 줄.

**3. Blue — Integrity monitoring 모듈로 직접 확인.**

Wazuh Dashboard 의 클릭 흐름은 다음과 같다.

1. 좌측 햄버거 메뉴 → `Wazuh` → `Modules` → `Integrity monitoring` 선택.
2. 상단 agent selector 를 `web` 으로 설정.
3. Time picker `Last 15 minutes`.
4. 화면 중앙의 `Files` table 에서 `/etc/passwd` 행을 찾는다. 변경 시각, mtime, hash before/after 가 보인다.
5. 같은 화면 상단의 `Events` 탭으로 이동.
6. 좌측 `Available fields` 에서 `syscheck.path`, `syscheck.event`, `syscheck.diff` 를 columns 에 추가한다.

이벤트 한 줄을 펼치면 다음 정보가 보인다.

- `syscheck.path` — `/etc/passwd`.
- `syscheck.event` — `modified` 또는 `added`.
- `syscheck.diff` — 추가된 한 줄의 내용 (예: `+testfim:x:1002:1002::/home/testfim:/bin/bash`).
- `syscheck.size_after` 와 `syscheck.md5_after` — 변경 후 파일 정보.

**4. Blue — 대응 의사결정.**

학생이 다음 세 가지를 판단한다.

- **계획된 변경 vs 침해.** 신규 사용자 추가가 운영팀의 계획된 작업인지, 침해 흔적인지 먼저 확인한다.
- **diff 의 내용 검토.** 추가된 사용자가 uid >= 1000 의 일반 사용자인가, uid 0 의 root 권한 위장인가.
- **확산 검증.** 같은 시각에 다른 host 에서도 비슷한 변경이 있는지 Discover 의 cross-host query 로 확인.

**5. Purple — FIM baseline 강화.**

다음 세 가지를 적용한다.

- **`<directories realtime="yes">` 범위 확장.** `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/cron.d/`, `/etc/systemd/system/`, `/root/.ssh/` 모두 realtime 으로 감시.
- **`<directories report_changes="yes">` 옵션 추가.** diff 내용까지 alert 에 포함되도록 한다.
- **알람 level 상향.** `/etc/passwd`, `/etc/shadow`, `/etc/sudoers` 의 변경은 level 10 이상으로 상향하는 custom rule 추가.

```xml
<group name="syscheck,local,">
  <rule id="100400" level="12" overwrite="yes">
    <if_matched_sid>550</if_matched_sid>
    <field name="syscheck.path">/etc/(passwd|shadow|sudoers)</field>
    <description>LOCAL critical system file changed: $(syscheck.path)</description>
  </rule>
</group>
```

cleanup 은 다음 한 줄이다.

```bash
sudo userdel -r testfim
```

### 11.5.3 케이스 3 — MITRE ATT&CK panel 의 kill chain 가시화

**0. 일상 비유 — 도둑의 행위 단계를 단계 별 카드로 정리.**

도둑의 행위가 한 사건에서 끝나지 않고 여러 단계로 진행되는 경우가 많다. 외부 정찰 → 출입 시도 → 직원 사칭 → 금고 접근 → 데이터 탈취. MITRE ATT&CK 은 도둑의 이런 행위 단계 (kill chain) 를 표준 카드로 정리한 분류 체계다. SOC 운영자가 ATT&CK panel 에서 카드 별로 alert 수를 보면 도둑이 어느 단계까지 진행했는지 한눈에 파악할 수 있다.

| 일상 비유 | MITRE ATT&CK |
|-----------|--------------|
| 외부 정찰 | Reconnaissance (TA0043) |
| 출입 시도 | Initial Access (TA0001, T1190 web exploit) |
| 직원 사칭 | Credential Access (TA0006, T1110 brute force) |
| 금고 접근 | Lateral Movement (TA0008) |
| 데이터 탈취 | Exfiltration (TA0010) |
| 카드 별 alert 수 | ATT&CK panel 의 tactic 별 카드 |

**0a. 사용 도구 사전 안내.**

- **Modules → MITRE ATT&CK** — ATT&CK 매트릭스 panel.
- **`rule.mitre.id`** — alert 에 매핑된 ATT&CK 의 technique ID (T1190 등).
- **`rule.mitre.tactic`** — alert 에 매핑된 ATT&CK 의 tactic (Initial Access 등).

**1. Red — 공격 재현 (W05 의 SSH brute force + W06 의 XSS 결합).**

attacker VM 에서 두 단계를 짧은 시간에 보낸다.

```bash
ssh ccc@192.168.0.112

# attacker VM 내부 (학습 환경 한정)
# 1단계 — Initial Access (web XSS 시도)
curl -s -o /dev/null -H "Host: juice.6v6.lab" \
    "http://192.168.0.103/search?q=%3Cscript%3Ealert(1)%3C/script%3E"

# 2단계 — Credential Access (SSH brute 5건)
for i in $(seq 1 5); do
    sshpass -p "wrong${i}" ssh -o ConnectTimeout=3 \
        -o StrictHostKeyChecking=no \
        admin@192.168.0.103 'whoami' 2>/dev/null
done
```

두 단계가 같은 src_ip 에서 짧은 시간에 발생했다.

**2. 발생하는 로그/아티팩트.**

- siem 의 alerts.json 에 두 시리즈 alert.
  - rule.id 86xxx (Suricata XSS) — rule.mitre.id T1190.
  - rule.id 5710, 5712 (sshd Failed + chain) — rule.mitre.id T1110.

ATT&CK panel 이 자동으로 두 tactic 카드에 alert 수를 누적 표시한다.

**3. Blue — MITRE ATT&CK panel 직접 가시화.**

Wazuh Dashboard 의 클릭 흐름은 다음과 같다.

1. 좌측 햄버거 메뉴 → `Wazuh` → `Modules` → `MITRE ATT&CK` 선택.
2. Time picker `Last 15 minutes`.
3. 화면에 ATT&CK 매트릭스 (Tactics × Techniques) 가 표시된다.
4. `Initial Access` 카드 위에 마우스를 올리면 카드 안의 technique 별 alert 수가 나온다. `T1190` 카드를 클릭한다.
5. 우측 Detail panel 에 본 technique 의 alert 목록이 표시된다.
6. 같은 방식으로 `Credential Access` → `T1110` 도 본다.

ATT&CK panel 의 한 화면에서 두 tactic 의 카드가 모두 활성화 (색이 진해짐) 되어 있으면 두 단계가 같은 src 에서 진행 중인 직접 증거다.

다음으로 Discover 에서 두 technique 의 timeline 을 본다.

1. 좌측 햄버거 메뉴 → `Discover` 선택.
2. Index pattern `wazuh-alerts-*`.
3. Search bar 에 `rule.mitre.id:(T1190 OR T1110) AND data.srcip:192.168.0.112` 입력.
4. Visualize → Date Histogram + Split series: `rule.mitre.id.keyword`.

같은 시간 안에 두 technique 의 막대가 함께 보이면 kill chain 의 시간순 진행이 가시화된다.

**4. Blue — 대응 의사결정.**

학생이 다음 세 가지를 판단한다.

- **kill chain 의 진행 단계.** Initial Access + Credential Access 까지면 침해 초기. Lateral Movement 와 Exfiltration 이 추가되면 후기. 단계 별 대응 강도가 다르다.
- **단일 vs 결합 alert.** 단일 tactic 의 단발 alert 는 모니터링. 두 tactic 의 결합은 즉시 IR 시작.
- **kill chain coverage.** 어떤 단계가 alert 로 잡히지 않았는지 본다. coverage 의 빈 공간은 다음 운영 보완의 우선순위다.

**5. Purple — ATT&CK coverage 확장.**

다음 세 가지를 적용한다.

- **MITRE rule mapping 확장.** 6v6 의 각 rule.id 에 `<mitre><id>T1xxx</id></mitre>` 매핑이 모두 등록되어 있는지 점검. 빠진 매핑이 있으면 보강.
- **coverage 매트릭스 작성.** 14 tactic 별로 학습 환경에서 매핑된 technique 수를 정리. coverage 50% 이하의 tactic 은 다음 분기 우선 작업.
- **Dashboard 카드 등록.** ATT&CK panel 의 한 줄짜리 saved visualization 을 운영실 모니터에 고정.

### 11.5.4 본 절 정리

본 절은 W10 의 Wazuh Dashboard 학습을 실제 공격 분석 cycle 에 연결했다. 학생이 다음 능력을 갖춘다.

- 한 사건의 두 source (Suricata + ModSec) alert 를 Discover 의 한 query 로 통합 가시화한다.
- syscheck FIM 의 critical system file 변경을 Integrity monitoring 모듈에서 직접 확인하고 alert level 을 상향한다.
- MITRE ATT&CK panel 로 kill chain 의 진행 단계를 시각화하고 coverage 의 빈 공간을 식별한다.

다음 주차 W11 에서는 sysmon-for-linux 의 호스트 이벤트 stream 을 같은 R/B/P cycle 로 학습한다.

---

## 12. 과제

### A. ModSec audit ship 적용 (필수, 30점)

§4 의 patch 실 적용 + 5 XSS burst + alerts.json 의 web agent + apache 룰 매치 검증.

### B. osquery 통합 설계 (심화, 30점)

§5 의 3 단계 설계 문서 + osquery.conf draft + Wazuh agent.conf draft.

### C. R/B/P 보고서 (정성, 30점)

실습 7 결과 + 5 source 매핑 + Active Response 권장.

### D. dashboard 트러블슈팅 시뮬 (정성, 10점)

§8 의 4 패턴 중 1 패턴 시뮬 + 진단 + 복구.

---

## 13. 평가 기준

| 항목 | 비중 |
|------|------|
| ModSec ship (A) | 30% |
| osquery 설계 (B) | 30% |
| R/B/P (C) | 30% |
| 트러블슈팅 (D) | 10% |

---

## 14. 핵심 정리 (8 줄)

1. **dashboard = SOC single pane of glass** — 5 main panel + RBAC + 인증
2. **OpenSearch indexer** (9200) + **filebeat** ship 흐름
3. **6v6 운영 갭 4** — dashboard 인증 / ModSec ship / osquery daemon / sysmon 미설치
4. **ModSec audit ship** — web ossec.conf 의 `<localfile>` JSON + 0250 decoder 매핑
5. **osquery 통합** — osqueryd enable + osquery.conf + Wazuh agent 의 ship
6. **syscheck FIM** — `<directories realtime="yes">` + rule 550/551/553/554
7. **Active Response** — manager 의 `<active-response>` + agent 의 firewall-drop +
   nftables drop set + allow_list
8. **R/B/P** — XSS 5 burst → 5 source 통합 → dashboard 1 화면

---

## 15. 다음 주차 (W11) 예고

- **주제**: sysmon-for-linux 본격 설치 + decoder + ProcessCreate / NetworkConnect / FileCreate event
- **6v6 현 상태**: sysmon 미설치 — W11 에서 본격 설치
- **연결**: osquery 의 snapshot vs sysmon 의 event stream 비교 (W07 §9 참조)
- **R/B/P 시나리오**: Red 가 의심 process spawn → sysmon ProcessCreate event → Wazuh
  rule 0800-sysmon_id_1 매치 → dashboard
