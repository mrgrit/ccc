# Week 01 — Wazuh Dashboard 와 KQL 기초, 일반 보안시스템 로그 분석

> **특강 1주차**. Wazuh Dashboard 에 로그인부터 KQL 검색 문법, 그리고 6v6 의
> 일반 보안 컨테이너 (nftables/Suricata/ModSec/Wazuh agent) 의 alert 를 직접
> 검색·분석하는 실전 방법까지. 2주차 (에이전트 로그) 의 사전 학습.

## 학습 목표

- Wazuh Dashboard 의 5 가지 핵심 모듈 (Discover, Security events, Modules, Visualize, Dashboard) 인지
- KQL (Kibana Query Language) 12 가지 필수 문법 자유 사용
- 일반 보안 시스템 (firewall, IDS, WAF, EDR) 의 alert 구조 파악
- 6v6 환경의 실제 alert 를 검색·필터·시각화

## 1. Wazuh 가 무엇을 보고 있는가 (5 분)

### 1-1. 6v6 4-tier 와 4 종 보안 솔루션

```
[학생 PC]
   │ HTTPS/SSH
   ▼
[fw 10.20.30.1]            ──── nftables (firewall) + HAProxy (reverse proxy)
   │ HAProxy backend
   ▼
[ips 10.20.31.1]           ──── Suricata (IDS, 2 NIC: eth0 sniff + eth1 management)
   │
   ▼
[web 10.20.32.80]          ──── Apache + ModSecurity (WAF) + osquery (호스트 가시화)
   │
   ▼
[siem 10.20.32.100]        ──── Wazuh Manager (모든 로그 수집 + alert 생성)
```

각 컨테이너는 **Wazuh Agent** 가 설치되어 로그를 SIEM 으로 송신.
- `fw`: nftables drop 카운트, HAProxy access/error log
- `ips`: Suricata `eve.json` (alert, flow, http, dns, tls)
- `web`: ModSec `audit log`, Apache access/error, osquery diff events
- `bastion`: SSH login, sudo, **bastion API audit + lifecycle (특강 2주차)**

### 1-2. 모든 alert 가 모이는 곳

Wazuh Manager 는 받은 모든 alert 를 **2 곳** 에 저장:

| 위치 | 형식 | 용도 |
|------|------|------|
| `/var/ossec/logs/alerts/alerts.log` | text | 사람이 읽기 |
| `/var/ossec/logs/alerts/alerts.json` | JSON 1줄 | indexer 송신 → Dashboard |

`alerts.json` 은 **Wazuh Indexer** (OpenSearch 기반) 가 매 초 polling →
`wazuh-alerts-4.x-YYYY.MM.DD` index 에 저장 → Dashboard 에서 KQL 로 검색.

## 2. Wazuh Dashboard 접속 (5 분)

### 2-1. 사전 조건 — `/etc/hosts` 등록

학생 PC 의 `/etc/hosts` 에 다음 1 줄 추가 (Linux/Mac):
```bash
sudo tee -a /etc/hosts <<EOF
192.168.0.110  siem.6v6.lab juice.6v6.lab dvwa.6v6.lab portal.6v6.lab bastion.6v6.lab
EOF
```

Windows: `C:\Windows\System32\drivers\etc\hosts` 동일 한 줄 추가 (관리자 권한).

### 2-2. 접속

| 항목 | 값 |
|------|-----|
| URL | https://siem.6v6.lab/ |
| 로그인 | `admin` / `SecretPassword` |
| 인증서 | self-signed → 브라우저 경고 "고급 → 안전하지 않음으로 이동" |

처음 접속 시 "Welcome to Wazuh" 화면 → **Explore** → **Discover** 로 이동.

### 2-3. 5 핵심 메뉴

| 메뉴 | 경로 | 용도 |
|------|------|------|
| **Discover** | ☰ → Explore → Discover | 자유 검색, KQL 입력, 핵심 분석 도구 |
| **Security events** | ☰ → Modules → Security events | Wazuh 표준 alert 모니터링 (자동 chart) |
| **Modules** | ☰ → Modules → ... | PCI/HIPAA/NIST 등 컴플라이언스 별 view |
| **Visualize** | ☰ → Visualize Library | 사용자 정의 chart |
| **Dashboards** | ☰ → Dashboards | chart 여러 개 + filter 모아 화면 구성 |

학생은 **90% Discover 만 쓰면 충분**.

## 3. Discover 사용 흐름 (10 분)

### 3-1. Index pattern 선택

좌상단 인덱스 패턴 드롭다운 → `wazuh-alerts-*` 선택.
(처음 1회만 — 그 후 기억됨)

### 3-2. 시간 범위 설정

우상단 시계 아이콘 클릭:
- **Quick**: Last 15 minutes, Last 1 hour, Last 24 hours
- **Relative**: 30 minutes ago
- **Absolute**: 2026-05-19 10:00 ~ 11:00

특강 실습에서는 **Last 15 minutes** 또는 **Last 1 hour** 가 적절.

### 3-3. 검색창 (KQL)

상단 검색창에 KQL 입력 → Enter (또는 Refresh 버튼).
**자동완성** 지원 — field 이름 일부 타이핑 → 후보 표시.

### 3-4. 좌측 fields 패널

검색 결과의 모든 field 가 좌측 패널에 listing. 자주 쓰는 field:
- `@timestamp` — alert 발생 시각
- `rule.id` — Wazuh rule ID (예: 5710 = SSH brute, 100200 = bastion audit)
- `rule.level` — 0-15, 높을수록 위험
- `rule.description` — 사람이 읽는 설명
- `rule.groups` — rule 분류 태그 ([authentication, ssh, ...])
- `agent.name` — 어느 컨테이너에서 온 alert (fw, ips, web, siem, bastion)
- `data.*` — alert 의 추출된 정보 (decoder 가 parse)

field 이름 옆 `+` → 표 컬럼으로 추가. `Visualize` → 즉시 chart.

### 3-5. 결과 row 클릭

각 alert 의 전체 JSON 확인. "JSON" 탭 → raw alert. "Table" → field-value 표.

## 4. KQL 12 가지 필수 문법 (15 분)

### 4-1. 자유 텍스트 (free text)

```
sshd
```
모든 field 에서 "sshd" 포함 검색. 빠르지만 부정확.

### 4-2. Field 매치

```
rule.id:5710
agent.name:bastion
```
정확한 일치. 가장 자주 쓰는 형식.

### 4-3. 문자열 (공백/특수문자)

```
rule.description:"sshd: authentication failed"
```
쌍따옴표로 감싸면 정확한 phrase.

### 4-4. 와일드카드

```
rule.description:*authentication*
agent.name:*web*
```
`*` 또는 `?` 사용. 단 field 가 keyword 타입일 때만.

### 4-5. 숫자 비교 (range)

```
rule.level:>10              # 10 초과
rule.level:>=10             # 10 이상
data.duration_ms:[1000 TO 5000]   # 1-5초 사이
data.duration_ms:>60000     # 1분 이상
```

### 4-6. 시간 비교

```
@timestamp:>now-1h           # 1시간 이내
@timestamp:[now-1d TO now]   # 24시간 이내
```

### 4-7. AND / OR / NOT

```
agent.name:web AND rule.level:>5
rule.id:5710 OR rule.id:5712
agent.name:fw AND NOT rule.level:0
```

대소문자 무관. 우선순위는 NOT > AND > OR. 괄호로 명시 권장:
```
(rule.id:5710 OR rule.id:5712) AND agent.name:bastion
```

### 4-8. 존재 여부

```
data.srcip:*                # data.srcip 가 존재
NOT data.srcip:*            # data.srcip 가 없음
```

### 4-9. 다중 값 (IN)

```
rule.id:(5710 OR 5712 OR 5715)
agent.name:(fw OR ips OR web)
```

### 4-10. 부분 매치 (contains)

KQL 은 substring 직접 안 됨 — wildcard 우회:
```
rule.description:*brute*
data.srcuser:*admin*
```

### 4-11. 부정

```
NOT agent.name:siem
-rule.level:0
```
`-` 또는 `NOT` 사용.

### 4-12. nested 필드

```
data.win.eventdata.image:*powershell*
rule.mitre.id:T1110
```
점(`.`) 으로 nested 접근.

## 5. 실전 query 10 가지 (10 분)

| 의도 | KQL |
|------|------|
| 최근 1시간 모든 high alert | `rule.level:>=10 AND @timestamp:>now-1h` |
| fw 의 SSH brute force | `agent.name:fw AND rule.id:(5710 OR 5712 OR 5715)` |
| Suricata 의 XSS 탐지 | `agent.name:ips AND rule.description:*xss*` |
| ModSec 941xxx (XSS rule) | `agent.name:web AND data.id:[941000 TO 942000]` |
| 특정 IP 의 모든 활동 | `data.srcip:"10.20.30.202"` |
| MITRE T1110 (brute force) | `rule.mitre.id:T1110` |
| PCI compliance alert | `rule.pci_dss:*` |
| 모든 컨테이너의 인증 실패 | `rule.groups:authentication_failed` |
| 1분 이상 걸린 작업 | `data.duration_ms:>60000` |
| 어제 0시-1시 사이 모든 alert | `@timestamp:[2026-05-18T00:00 TO 2026-05-18T01:00]` |

## 6. 일반 보안시스템 로그 4 종 (15 분)

### 6-1. nftables (firewall) — agent `fw`

```kql
agent.name:fw AND rule.groups:firewall
```

대표 alert:
- `rule.id:1001` — drop 카운터 임계치 초과
- `rule.description` 예: "Multiple iptables drop"
- 관심 field: `data.srcip`, `data.dstip`, `data.dstport`, `data.protocol`

**실습 시나리오**: 학생이 attacker (10.20.30.202) 에서 fw 80 포트 SYN flood
시도 → fw 의 nftables 가 drop → Wazuh agent 가 `/var/log/syslog` 의 drop 메시지
ship → manager 의 firewall decoder 가 parse → alert 생성.

### 6-2. Suricata (IDS) — agent `ips`

```kql
agent.name:ips AND rule.groups:suricata
```

대표 alert:
- Wazuh rule ID `86601` = Suricata Alert 전체 wrapping
- custom signature ID 는 `data.alert.signature_id` 에 (예: 1000003 = sqlmap)
- 관심 field: `data.alert.signature`, `data.alert.severity`, `data.src_ip`, `data.dest_ip`, `data.alert.category`

**실제 query**:
```kql
agent.name:ips AND data.alert.signature_id:1000003       # sqlmap UA 탐지
agent.name:ips AND data.alert.severity:1                  # critical 만
agent.name:ips AND data.alert.category:*Web*              # 웹 공격만
```

### 6-3. ModSecurity (WAF) — agent `web`

```kql
agent.name:web AND rule.groups:modsecurity
```

대표 alert:
- ModSec rule ID 는 `data.id` 에 (예: 941100 = XSS detected, 942100 = SQLi, 980130 = 5+ rule 매치 = high anomaly)
- 관심 field: `data.id`, `data.msg`, `data.uri`, `data.client_ip`, `data.severity`

**OWASP CRS rule 카테고리** (학생 암기):
| ID 범위 | 의미 |
|---------|------|
| 910xxx | Reputation / IP blacklist |
| 920xxx | Protocol enforcement (악성 헤더) |
| 930xxx | LFI |
| 931xxx | RFI |
| 932xxx | RCE |
| 933xxx | PHP injection |
| 941xxx | **XSS** |
| 942xxx | **SQLi** |
| 943xxx | Session fixation |
| 944xxx | Java |
| 980xxx | Anomaly score summary |

**실제 query**:
```kql
agent.name:web AND data.id:[941000 TO 941999]    # 모든 XSS
agent.name:web AND data.id:980130                 # 5+ rule 매치 (정말 위험)
agent.name:web AND data.client_ip:"10.20.30.202" # attacker 의 모든 ModSec hit
```

### 6-4. Wazuh agent 자체 (FIM, SCA, osquery) — 모든 agent

```kql
rule.groups:syscheck                # 파일 무결성 (FIM)
rule.groups:rootcheck               # 루트킷 탐지
rule.groups:sca                     # Security Configuration Assessment
rule.groups:osquery                 # osquery 결과
```

대표 alert:
- `rule.id:550` — 새 파일 생성 (FIM)
- `rule.id:554` — 파일 수정
- `rule.id:597` — osquery diff event
- 관심 field: `syscheck.path`, `syscheck.size_after`, `syscheck.sha256_after`

**실제 query**:
```kql
syscheck.path:/etc/passwd                                          # 핵심 시스템 파일 변경
agent.name:web AND syscheck.path:/var/www/*                        # web root 변경
rule.id:597 AND data.osquery.name:processes                        # 새 프로세스
```

## 7. Visualize — 간단한 chart 만들기 (10 분)

### 7-1. 예: 시간대별 alert 추세

1. ☰ → Visualize Library → **Create new visualization**
2. **Line** 선택
3. Index pattern: `wazuh-alerts-*`
4. Y-axis (Metric): **Count**
5. X-axis (Bucket): **Date Histogram** field=`@timestamp` interval=`1h`
6. Filter (좌측 위): `rule.level:>=10`
7. **Save** → "High Alert Trend"

### 7-2. 예: agent 별 alert 분포 (Pie)

1. **Pie**
2. Metric: Count
3. Buckets → Split slices → **Terms** field=`agent.name.keyword` size=5
4. Save → "Alert by Agent"

### 7-3. 예: rule.id Top 10 (Bar)

1. **Vertical Bar**
2. Y-axis: Count
3. X-axis: Terms `rule.id.keyword` size=10 order desc
4. Save → "Top 10 Rules"

## 8. Dashboard — chart 모으기 (5 분)

1. ☰ → Dashboards → **Create new dashboard**
2. **Add panel** → 위에서 저장한 chart 들 추가
3. Time picker → "Last 24 hours"
4. Filter 추가: `agent.name:(fw OR ips OR web)` (특정 컨테이너만)
5. **Save** → "6v6 Security Overview"

이후 학생/관리자 누구나 같은 화면으로 모니터링.

## 9. 흔한 실수 5 가지

| 실수 | 증상 | 해결 |
|------|------|------|
| Index 안 선택 | "No results" + 좌측 field 없음 | 좌상단 `wazuh-alerts-*` 선택 |
| 시간 범위 너무 좁음 | 결과 0건 | 우상단 시계 → Last 1 hour |
| keyword vs text 혼동 | wildcard 안 됨 | field 명 끝에 `.keyword` 붙이기 |
| 따옴표 누락 | "Syntax error" | 공백 있는 값은 `"..."` |
| `=` 와 `:` 혼동 | error | KQL 은 `field:value` (콜론) |

## 10. 다음 주차 예고

W02: **에이전트 (bastion) 로그 분석**

- bastion 의 lifecycle 8 단계
- request_id correlation 으로 1 mission timeline
- 자가 수정 (KG-3 Adapt) 패턴 탐지
- KG-2 Reuse 통계 (학습 효과 측정)
- 위험 mission 알림 (rule 100204, 100217)

W01 의 KQL 기초 + 일반 시스템 로그 분석 능력이 W02 의 에이전트 로그 분석의 기반.
