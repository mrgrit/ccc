# Week 12 — OpenCTI (1) — STIX 2.1 / TAXII 2.1 / CTI 표준

> **CTI (Cyber Threat Intelligence)** 의 표준 (STIX 2.1) + 교환 프로토콜 (TAXII 2.1)
> + 통합 플랫폼 (OpenCTI) 의 개론. 본 주차는 OpenCTI 설치 전 STIX / TAXII 표준
> 학습 + 무료 IOC feed 5 종 평가 + OpenCTI 아키텍처 + W13-W14 의 Wazuh 통합 준비.

## 학습 목표

학생은 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. **CTI 의 정의** + 5 종류 (Strategic / Operational / Tactical / Technical / IOC)
2. **STIX 2.1** 의 18 SDO + 2 SCO + Relationship + Pattern
3. **TAXII 2.1** 의 client / server 모델 + collection + envelope
4. **OpenCTI 아키텍처** (Platform + Workers + Connectors + Elasticsearch / Redis / RabbitMQ / MinIO)
5. **무료 IOC feed 5 종** (MISP / AlienVault OTX / abuse.ch / OpenPhish / CISA AIS)
6. **CTI Pyramid of Pain** (Bianco) + actionable intelligence
7. **운영 시나리오** (SOC / Threat Hunting / IR / 분기 review)
8. W13-W14 의 Wazuh CDB list 통합 준비

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용                                                                | 유형 |
|-----------|---------------------------------------------------------------------|------|
| 0:00–0:30 | 이론 — CTI 정의 + 5 종류 + Pyramid of Pain                          | 강의 |
| 0:30–1:00 | 이론 — STIX 2.1 표준 + 18 SDO                                       | 강의 |
| 1:00–1:10 | 휴식                                                                 | —    |
| 1:10–1:40 | 이론 — TAXII 2.1 + collection                                       | 강의 |
| 1:40–2:00 | 이론 — OpenCTI 아키텍처                                              | 강의 |
| 2:00–2:30 | 실습 1, 2 — STIX JSON 분석 + TAXII 조회                             | 실습 |
| 2:30–2:40 | 휴식                                                                 | —    |
| 2:40–3:10 | 실습 3, 4 — 무료 IOC feed + MITRE ATT&CK Navigator                 | 실습 |
| 3:10–3:30 | 실습 5 — OpenCTI 도입 계획                                           | 실습 |
| 3:30–3:40 | 정리 + W13 (CTI Wazuh 통합) 예고                                    | 정리 |

---

## 1. CTI (Cyber Threat Intelligence) 의 정의

### 1.1 정의

```
CTI = 사이버 위협 정보 — 공격자 / 캠페인 / TTP (Technique, Tactic, Procedure) /
       IOC (Indicator of Compromise) 등 의 사전 정보를 수집·분석·공유하는 활동

목표: 사고 발생 전 / 발생 시 / 발생 후 의 의사결정에 actionable intelligence 제공
```

### 1.2 CTI 의 가치

```
1. Proactive detection — 룰 작성 전에 IOC matching 으로 사전 차단
2. Context — alert 가 "왜 발생" 했는지 + "누구" 인지 파악
3. Prioritization — 1000+ alert 중 critical 만 SOC 분석가 손
4. Sharing — 같은 산업 / 국가의 다른 회사와 정보 공유
```

### 1.3 5 종류 (Pyramid)

```
              Strategic    ← 경영진 (CEO / CISO)
              ┌────────┐    의사결정 — 산업 위협 트렌드 / 지정학 위험
              │  높음  │
              ├────────┤
            Operational    ← CISO / SOC 분석가
              │        │    캠페인 / 적 분석 — APT 그룹 의 동향
              │        │
              ├────────┤
             Tactical      ← SOC 분석가
              │        │    TTP — 공격 기법 (MITRE ATT&CK Technique)
              │        │
              ├────────┤
             Technical     ← 보안 엔지니어
              │        │    IOC — IP / domain / hash / file
              │        │
              ├────────┤
                IOC        ← 자동화 도구 (SOC platform)
              │  낮음  │    Indicator of Compromise (단순 매칭)
              └────────┘

낮을수록 자동화 친화, 높을수록 사람 분석 필요.
```

### 1.4 Pyramid of Pain (David Bianco, 2013)

```
공격자에게 가장 "변경 어려운" 것이 가장 "value 높은" IOC

위에서 아래 = 변경 어려움 (공격자에게 pain)
              ┌────────┐
              │ TTPs   │    ← Tough (변경 가장 어려움)
              ├────────┤
              │ Tools  │    ← Challenging
              ├────────┤
              │Network │    ← Annoying
              │Artifacts│
              ├────────┤
              │ Host   │
              │Artifacts│
              ├────────┤
              │Domain  │
              │Names   │
              ├────────┤
              │ IP     │    ← Easy (공격자가 쉽게 변경)
              │Addrs   │
              ├────────┤
              │ Hash   │    ← Trivial (1 byte 만 변경해도 다른 hash)
              │Values  │
              └────────┘

운영 권장: TTPs / Tools 까지 식별 + 차단 (단순 IP / hash 만으로는 부족)
```

### 1.5 한국 환경의 CTI

```
- KISA 보호나라 — 한국 침해 사고 분석 + IOC 공유
- K-ISAC — 산업별 보안 정보 공유
- KrCERT — 한국 CERT (정부)
- KCMVP — 암호 모듈 검증
- 일부 SOC SaaS (안랩 / 이글루시큐리티 / SK인포섹) 가 CTI 통합 제공
```

---

## 2. STIX 2.1 — 표준 객체 모델

### 2.1 STIX 의 정의

```
STIX = Structured Threat Information eXpression
출시: 2012 MITRE (1.x) → 2017 OASIS 표준화 (2.0) → 2021 2.1 (현재)
형식: JSON (이전 1.x 는 XML)
표준 문서: https://docs.oasis-open.org/cti/stix/v2.1/
```

### 2.2 STIX 의 객체 카테고리

```
1. SDO (STIX Domain Objects) — 18 종
   — Indicator, Threat Actor, Malware, Attack Pattern 등

2. SCO (STIX Cyber Observables) — 19 종
   — file, IP, domain, URL, registry-key 등 (실 관찰된 데이터)

3. SRO (STIX Relationship Objects)
   — Relationship (양방향 connection)
   — Sighting (관측 결과)

4. STIX Bundle
   — 여러 객체를 묶은 envelope
```

### 2.3 핵심 SDO 18 종

| SDO | 의미 | 예 |
|-----|------|-----|
| **Indicator** | IOC (탐지 가능한 패턴) | 악성 IP / domain |
| **Threat Actor** | 공격 주체 (개인 / 그룹) | APT29 / Lazarus |
| **Intrusion Set** | 캠페인 묶음 | Cozy Bear |
| **Campaign** | 일련의 공격 시도 | SolarWinds attack |
| **Malware** | 악성코드 family | Emotet / TrickBot |
| **Attack Pattern** | 공격 기법 (ATT&CK 매핑) | T1190 Public-Facing App |
| **Tool** | 정상 도구의 악성 사용 | Mimikatz / PsExec |
| **Vulnerability** | CVE | CVE-2024-1234 |
| **Course of Action** | 대응 절차 | "Patch CVE-2024-1234" |
| **Identity** | 사람 / 조직 | "KISA" / "Financial Firm A" |
| **Location** | 지역 | 한국 / 미국 / 러시아 |
| **Report** | 위협 보고서 | "Q1 2026 APT Trends" |
| **Note** | 메모 (개인) | 분석가 메모 |
| **Opinion** | 동료 의견 (peer review) | "confirmed" / "likely false" |
| **Observed Data** | 관찰된 데이터 | "IP 1.2.3.4 seen at ..." |
| **Marking Definition** | 표시 (TLP / GPDR 등) | TLP:GREEN |
| **Grouping** | 객체 묶음 | 한 incident 의 모든 객체 |
| **Infrastructure** | C2 서버 등 | "Amazon EC2 IP block X" |

### 2.4 SDO JSON 예시 — Indicator

```json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--12345678-1234-1234-1234-123456789012",
  "created": "2026-05-12T10:00:00.000Z",
  "modified": "2026-05-12T10:00:00.000Z",
  "name": "Malicious C2 IP",
  "description": "APT29 의 C2 서버 IP — confirmed 2026-05",
  "indicator_types": ["malicious-activity"],
  "pattern": "[ipv4-addr:value = '1.2.3.4']",
  "pattern_type": "stix",
  "pattern_version": "2.1",
  "valid_from": "2026-05-12T10:00:00.000Z",
  "valid_until": "2026-12-31T23:59:59.999Z",
  "labels": ["malicious-activity", "apt29"],
  "kill_chain_phases": [
    {
      "kill_chain_name": "mitre-attack",
      "phase_name": "command-and-control"
    }
  ]
}
```

### 2.5 Pattern 의 syntax (STIX Pattern)

```
# IP 단일
[ipv4-addr:value = '1.2.3.4']

# domain
[domain-name:value = 'evil.com']

# hash
[file:hashes.SHA256 = 'abc...']
[file:hashes.'MD5' = '123...']

# URL
[url:value = 'http://evil.com/malware']

# 조합
[ipv4-addr:value = '1.2.3.4' OR ipv4-addr:value = '5.6.7.8']
[file:hashes.SHA256 = 'abc...' AND file:name = 'evil.exe']

# 시간 조건
[network-traffic:dst_port = 4444]
  WITHIN 60 SECONDS
[file:created = '2026-05-12T10:00:00.000Z']
```

### 2.6 Relationship Object

```json
{
  "type": "relationship",
  "spec_version": "2.1",
  "id": "relationship--abc...",
  "created": "...",
  "modified": "...",
  "relationship_type": "attributed-to",
  "source_ref": "indicator--12345678-...",
  "target_ref": "threat-actor--apt29-..."
}
```

자주 사용하는 relationship_type:
- `attributed-to` : Indicator → ThreatActor
- `indicates` : Indicator → Malware
- `targets` : ThreatActor → Identity (산업 / 회사)
- `uses` : Malware → AttackPattern
- `mitigates` : CourseOfAction → AttackPattern
- `related-to` : 일반 (덜 specific)

### 2.7 Bundle (envelope)

```json
{
  "type": "bundle",
  "id": "bundle--xyz...",
  "objects": [
    { "type": "indicator", "...": "..." },
    { "type": "threat-actor", "...": "..." },
    { "type": "relationship", "...": "..." }
  ]
}
```

---

## 3. TAXII 2.1 — 교환 프로토콜

### 3.1 정의

```
TAXII = Trusted Automated eXchange of Intelligence Information
출시: 2014 MITRE (1.x) → 2019 OASIS (2.1 — 현재)
형식: REST API + HTTPS
표준: https://docs.oasis-open.org/cti/taxii/v2.1/
```

### 3.2 endpoint 구조

```
GET /taxii2/                                  # 서버 메타
GET /taxii2/api1/                              # API root
GET /taxii2/api1/collections/                  # collection 목록
GET /taxii2/api1/collections/<id>/             # collection 상세
GET /taxii2/api1/collections/<id>/objects      # STIX 객체 조회 (페이지)
POST /taxii2/api1/collections/<id>/objects     # STIX 업로드 (권한 시)
GET /taxii2/api1/collections/<id>/objects/<id> # 단일 객체
GET /taxii2/api1/collections/<id>/manifest     # 객체 메타
GET /taxii2/api1/status/<status-id>            # async 작업 상태
```

### 3.3 collection 의 의미

```
collection = 논리적 그룹의 STIX 객체 묶음
예:
  - "AbuseIPDB Critical" (high-confidence IP)
  - "MISP Daily Threats" (일별 threat)
  - "Industry Sector — Financial" (산업별)

권한 단위로 분리:
  - public collection: 모든 사용자 read
  - private collection: 인증된 사용자 only
```

### 3.4 인증 + TLS

```
표준:
  - HTTPS 필수
  - Bearer JWT 또는 Basic auth
  - mutual TLS (mTLS) 권장 (회사 간)

요청 예:
  curl -H "Accept: application/taxii+json;version=2.1" \
       -H "Authorization: Bearer <JWT>" \
       https://taxii.example.com/taxii2/api1/collections/
```

### 3.5 자주 사용하는 TAXII source

| Source | URL | 라이선스 |
|--------|-----|----------|
| **MITRE ATT&CK** | https://attack.mitre.org/api/ | CC BY 4.0 |
| **MISP** | (회사별 self-hosted) | 무료 / 유료 |
| **Anomali** | https://anomali.com/api/ | 유료 |
| **OASIS demo** | https://oasis-open.github.io/cti-taxii-server/ | 학습용 |
| **OpenCTI** | (self-hosted) | 무료 |
| **AlienVault OTX** | https://otx.alienvault.com/api/v1/ | 무료 (API key 등록) |

---

## 4. OpenCTI 아키텍처

### 4.1 OpenCTI 의 정의

```
OpenCTI = Open Cyber Threat Intelligence Platform
출시: 2019 Filigran (Luatix → Filigran)
라이선스: Apache 2.0
언어: TypeScript (Platform) + Python (Workers / Connectors) + React (UI)
홈페이지: https://www.opencti.io
GitHub: https://github.com/OpenCTI-Platform/opencti
```

### 4.2 아키텍처

```
┌──────────────────────┐
│   OpenCTI Platform    │  GraphQL API + Web UI (port 8080)
│   (TypeScript)        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Elasticsearch (검색) │  port 9200
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Redis (cache)         │  port 6379
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ RabbitMQ (queue)      │  port 5672
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ MinIO (S3 storage)    │  port 9001
└──────────────────────┘

추가 component:
  - Workers (Python) — 데이터 처리 백그라운드
  - Connectors — 외부 source 통합 (40+)
  - Telemetry (선택) — Prometheus / Grafana
```

### 4.3 의존성 + Docker compose

```yaml
# 공식 docker-compose-opencti.yml (간소)
services:
  opencti:
    image: opencti/platform:6.0
    ports: ["8080:8080"]
    depends_on: [redis, elasticsearch, rabbitmq, minio]
  elasticsearch:
    image: elasticsearch:8.10
  redis:
    image: redis:7
  rabbitmq:
    image: rabbitmq:3-management
  minio:
    image: minio/minio
    command: server /data
  worker:
    image: opencti/worker:6.0
    depends_on: [opencti]
```

대략 **4 GB RAM 추가** 필요 — 본 lab 의 6v6 VM (8GB) 에는 부담. 별 lab 또는 reduced
config 권장.

### 4.4 OpenCTI 의 6 main view

| View | 용도 |
|------|------|
| **Investigations** | 사고 분석 + timeline |
| **Threats** | Threat Actor / Intrusion Set / Campaign |
| **Arsenal** | Malware / Tool / Vulnerability |
| **Techniques** | ATT&CK Tactic / Technique |
| **Entities** | Identity / Location / Sector |
| **Observations** | Indicator / Observable / Sighting |

---

## 5. Connector

### 5.1 Connector 3 종

#### 5.1.1 External Connector (외부 → OpenCTI)

```
외부 source 의 데이터를 OpenCTI 에 ingest

대표:
  - MITRE ATT&CK
  - MISP
  - Anomali
  - AbuseIPDB
  - OTX AlienVault
  - VirusTotal
  - URLhaus / ThreatFox (abuse.ch)
```

#### 5.1.2 Internal Enrichment (내부 객체 확장)

```
이미 OpenCTI 에 있는 객체를 enrich:
  - IP → GeoIP / WHOIS / ASN
  - Domain → VirusTotal / DomainTools
  - Hash → VirusTotal / MalwareBazaar
```

#### 5.1.3 Stream Connector (OpenCTI → 외부)

```
OpenCTI 의 데이터를 외부 시스템에 push:
  - **OpenCTI → Wazuh** (CDB list — W13 학습)
  - OpenCTI → Splunk
  - OpenCTI → MISP (양방향 sync)
  - OpenCTI → ELK
```

### 5.2 본 lab 의 핵심 — Wazuh Stream Connector

W13 에서 본격 학습. 패턴:

```
OpenCTI → 30분 주기 polling → STIX Indicator → CDB list 변환
→ /var/ossec/etc/lists/opencti-iocs → Wazuh reload → alert 의 level 자동 상승
```

---

## 6. 5 무료 IOC Feed

| Feed | source | type | 라이선스 |
|------|--------|------|----------|
| **MISP** | community + 회사 self-hosted | IOC + TTP | 무료 |
| **OTX AlienVault** | community + AT&T | IOC + Pulses | 무료 (API key) |
| **abuse.ch** | URLhaus / Feodotracker / SSLBL | 악성 URL / C2 / TLS cert | 무료 (CC0) |
| **OpenPhish** | community | phishing URL | 무료 |
| **CISA AIS** | 미국 정부 | IOC + indicator | 무료 (등록) |

본 lab 의 W13-W14 에서 이 중 1-2 개 통합.

---

## 7. CTI 운영 시나리오

### 7.1 SOC 분석 (Tier 1-2)

```
1. SIEM 의 alert 발생 (예: SSH brute force from 1.2.3.4)
2. 분석가 가 OpenCTI 에서 1.2.3.4 검색
3. 발견: APT29 의 C2 IP (TLP:GREEN)
4. 우선순위 상승 + IR 시작
```

### 7.2 Threat Hunting (Tier 3)

```
1. CTI 의 새 IOC 받음 (예: APT29 의 새 TTP)
2. 본 환경의 historical 데이터에 매칭
3. 과거 침해 흔적 발견 또는 부재 확인
4. Detection 룰 강화
```

### 7.3 IR (Incident Response)

```
1. 사고 발생 시 OpenCTI 의 attribution 분석
2. 알려진 TTP 와 매칭 → 다음 단계 예측
3. CTI 의 IOC 로 영향 확산 차단
```

### 7.4 분기 review

```
1. 본 환경에 매치된 IOC 통계
2. 가장 빈번한 ThreatActor / Malware
3. Coverage Matrix 갱신
4. CTI source 의 신뢰도 평가
```

---

## 8. R/B/P 시나리오 — OpenCTI 의 자리

```mermaid
graph LR
    EXT["🌍 외부 CTI Source<br/>MISP / OTX / abuse.ch /<br/>OpenPhish / CISA"]
    OC["📋 OpenCTI Platform<br/>External Connector<br/>+ Internal Enrichment"]

    CDB["🔵 Wazuh CDB list<br/>opencti-iocs<br/>(W13 학습)"]
    WZ["🔵 Wazuh manager<br/>alerts.json"]
    DBSH["🔵 Wazuh dashboard"]

    R["🔴 Red — attacker"]
    INF["🌐 6v6 인프라"]
    SUR["🔵 Suricata / ModSec / osquery"]

    P["🟣 Purple Team<br/>CTI + Detection 통합"]

    EXT -->|TAXII pull| OC
    OC -.->|Stream Connector| CDB
    CDB --> WZ

    R --> INF --> SUR --> WZ
    WZ -.->|alert| DBSH
    WZ --> P
    OC --> P

    style EXT fill:#d29922,color:#fff
    style OC fill:#bc8cff,color:#fff
    style WZ fill:#1f6feb,color:#fff
    style P fill:#bc8cff,color:#fff
```

---

## 9. 실습 1~5

### 실습 1 — STIX 2.1 Indicator JSON 작성 + 분석

```bash
ssh 6v6-attacker '
echo "=== STIX 2.1 Indicator 예시 ==="
cat <<EOF | tee /tmp/indicator.json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--$(uuidgen)",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "modified": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "name": "6v6 Lab Test IOC",
  "description": "학습 환경의 가상 IOC",
  "indicator_types": ["malicious-activity"],
  "pattern": "[ipv4-addr:value = \"1.2.3.4\"]",
  "pattern_type": "stix",
  "valid_from": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "labels": ["c2", "test"]
}
EOF

echo ""
echo "=== jq 로 분석 ==="
jq . /tmp/indicator.json

echo ""
echo "=== pattern 부분 만 ==="
jq -r .pattern /tmp/indicator.json
'
```

### 실습 2 — MITRE ATT&CK 의 STIX 다운로드 + 분석

```bash
ssh 6v6-attacker '
echo "=== MITRE ATT&CK Enterprise — JSON 다운로드 ==="
curl -s https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json -o /tmp/attack.json 2>&1 | head -3
ls -la /tmp/attack.json

echo ""
echo "=== Bundle 의 object 종류 통계 ==="
jq -r ".objects[].type" /tmp/attack.json | sort | uniq -c | sort -rn

echo ""
echo "=== Threat Actor (intrusion-set) 10 개 ==="
jq -r ".objects[] | select(.type==\"intrusion-set\") | .name" /tmp/attack.json 2>/dev/null | head -10

echo ""
echo "=== Attack Pattern (Technique) 10 개 ==="
jq -r ".objects[] | select(.type==\"attack-pattern\") | .name" /tmp/attack.json 2>/dev/null | head -10
'
```

### 실습 3 — TAXII 2.1 collection 조회 (OASIS demo)

```bash
ssh 6v6-attacker '
echo "=== TAXII 2.1 서버 메타 ==="
curl -s -H "Accept: application/taxii+json;version=2.1" \
    https://oasis-open.github.io/cti-taxii-server/ 2>&1 | head -30 | head

echo ""
echo "=== 또는 OpenCTI 공개 demo ==="
curl -s -H "Accept: application/taxii+json;version=2.1" \
    https://app.opencti.io/taxii2/ 2>&1 | head -30 | head
'
```

### 실습 4 — abuse.ch URLhaus 의 IOC 다운로드

```bash
ssh 6v6-attacker '
echo "=== URLhaus 의 최근 malicious URL ==="
curl -s https://urlhaus.abuse.ch/downloads/csv_recent/ -o /tmp/urlhaus.csv 2>&1 | head -3
wc -l /tmp/urlhaus.csv
echo ""
echo "=== 상위 5 entry ==="
head -10 /tmp/urlhaus.csv | tail -5

echo ""
echo "=== CSV → STIX 변환 예시 (pseudocode) ==="
echo "각 URL 의 row → STIX Indicator JSON 변환"
echo "  pattern: [url:value = \"...\"]"
echo "  indicator_types: [malicious-activity]"
echo "  valid_from: ..."
'
```

### 실습 5 — OpenCTI 도입 계획 작성

```markdown
# 6v6 환경의 OpenCTI 도입 계획

## 1. 현황
- 6v6 환경: 16 컨테이너 + 8 vuln + 4 인프라
- 현재 CTI 통합: 없음 (Wazuh CDB list 가 manual)
- 본인 환경: 8GB RAM VM

## 2. 도입 목표
- 6v6-secuops 의 detection 능력 향상 (Coverage 90%+)
- 외부 IOC feed 의 자동 ingest → Wazuh CDB
- 분기별 Threat Hunting session

## 3. 아키텍처 plan
- 별 docker-compose 의 OpenCTI stack (또는 별 VM)
- 4GB RAM 추가 (Elasticsearch + Redis + RabbitMQ + MinIO)
- 6v6 의 dmz subnet 에 추가 컨테이너 (10.20.32.130)

## 4. 통합 plan
- W13: Wazuh Stream Connector 작성
- W14: 분기 Threat Hunting (Sighting + Report)

## 5. CTI source 선택
- MITRE ATT&CK (필수)
- abuse.ch URLhaus / Feodotracker (무료)
- OTX AlienVault (API key 등록)
- MISP (옵션 — community 가입)
```

---

## 10. ATT&CK + 한국 표준

### 10.1 ATT&CK 의 STIX 표현

```
ATT&CK 자체가 STIX 2.1 형식으로 배포
  Tactic = x-mitre-tactic (custom SDO)
  Technique = attack-pattern
  Mitigation = course-of-action
  Group = intrusion-set
  Software = malware / tool
```

### 10.2 ISMS-P 매핑

| ISMS-P | 본 주차 |
|--------|---------|
| 2.10.7 보안위협 대응 | CTI 의 actionable intelligence |
| 2.11.3 정보보호 인식 제고 | CTI 의 분기 review |

### 10.3 NIST CSF + Cyber Threat Framework

```
- NIST CSF Identify : CTI 의 자산 위협 매핑
- NIST CSF Detect   : IOC matching
- NIST CTF (CSF v2) : Strategic / Operational / Tactical 매핑
```

---

## 11. 과제

### A. STIX 분석 (필수, 40점)

MITRE ATT&CK 의 STIX bundle 다운로드 + 다음 분석:
1. object 종류별 갯수
2. intrusion-set (APT 그룹) 10+ list
3. attack-pattern (Technique) 의 Tactic 별 분포

### B. TAXII 통신 (심화, 30점)

OASIS demo 또는 OpenCTI 공개 demo 의 collection 1+ 조회 + STIX Indicator
다운로드.

### C. OpenCTI 도입 plan (정성, 30점)

본 6v6 환경에 OpenCTI 도입하는 plan 작성:
- 자원 요구사항
- 통합 시나리오 (Wazuh / Suricata)
- 분기 운영 사이클

---

## 12. 평가 기준

| 항목 | 비중 |
|------|------|
| STIX 분석 (A) | 40% |
| TAXII 통신 (B) | 30% |
| 도입 plan (C) | 30% |

---

## 13. 핵심 정리 (10 줄)

1. **CTI 5 종류** — Strategic / Operational / Tactical / Technical / IOC
2. **Pyramid of Pain** (Bianco) — TTP / Tool 까지 detect 가 가장 가치
3. **STIX 2.1** — 18 SDO + Relationship + Pattern + Bundle
4. **TAXII 2.1** — REST API + collection + envelope
5. **OpenCTI** = Platform + Workers + Connectors + ES/Redis/RabbitMQ/MinIO
6. **Connector 3 종** — External / Internal Enrichment / Stream
7. **5 무료 IOC feed** — MISP / OTX / abuse.ch / OpenPhish / CISA AIS
8. **운영 시나리오 4** — SOC / Threat Hunting / IR / 분기 review
9. **W13 (CTI Wazuh 통합)** = OpenCTI → Wazuh CDB list (Stream Connector)
10. **W14 (Threat Hunting)** = OpenCTI 의 Sighting + Report
