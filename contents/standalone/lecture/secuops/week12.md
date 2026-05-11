# Week 12 — OpenCTI (1) — 설치·STIX·TAXII

> 본 주차는 **OpenCTI (Open Cyber Threat Intelligence)** 플랫폼이 학습 대상.
> Threat Intelligence (CTI) 데이터의 표준 (STIX 2.1) + 교환 프로토콜 (TAXII 2.1) 을
> 학습 + 6v6 인프라에 보조 컨테이너로 OpenCTI 추가하여 IOC feed → Wazuh 통합 path
> 준비.

## 학습 목표

1. CTI 의 정의 + 5 종류 (Strategic / Operational / Tactical / Technical / IOC)
2. STIX 2.1 데이터 모델 — Object 18 종 (Indicator, Threat Actor, Malware, ...)
3. TAXII 2.1 collection 의 push/pull 구조
4. OpenCTI 아키텍처 (Platform + Workers + Connectors + Elasticsearch)
5. 무료 IOC feed 5종 (MISP / OTX AlienVault / Abuse.ch / OpenPhish / URLhaus)
6. W13-14 에서 Wazuh 와 통합 path 학습 준비

## 1. CTI 가 왜 필요한가?

기존 보안 솔루션은 시그니처 + 룰 기반. 새 위협 등장 시 룰 업데이트 시간 (lag). CTI 는:

- **외부 위협 정보 (IP / domain / hash / TTP) 사전 공유** → lag 감소
- **MITRE ATT&CK 기반 행위 분석** → 단순 시그니처 회피 공격 탐지
- **위협 actor (APT 그룹) profile** → context 기반 우선순위
- **자동화 가능 (STIX 표준)** → SOAR / 알람 자동 처리

## 2. CTI 5 종류

| 종류 | 청중 | 예시 |
|------|------|------|
| Strategic | 경영진 | 산업별 위협 트렌드, 지정학 위험 |
| Operational | CISO / 분석가 | APT 그룹 캠페인 동향 |
| Tactical | SOC 분석가 | 공격 기법 (TTP) 매핑 |
| Technical | 보안 엔지니어 | IOC (IP/domain/hash) feed |
| IOC | 자동화 도구 | malware C2 IP 리스트 |

OpenCTI 는 모든 5 종류를 한 플랫폼에 통합.

## 3. STIX 2.1 데이터 모델

STIX (Structured Threat Information eXpression) 는 OASIS 표준의 CTI 표현 언어. JSON
기반.

### 3.1 핵심 Object 18 종 (일부)

| Object | 의미 |
|--------|------|
| Indicator | IOC (IP / domain / hash / file) |
| Threat Actor | 공격 주체 (APT29 등) |
| Malware | 악성코드 family |
| Attack Pattern | 공격 기법 (MITRE ATT&CK 매핑) |
| Campaign | 일련의 공격 캠페인 |
| Course of Action | 대응 절차 |
| Vulnerability | CVE |
| Identity | 사람 / 조직 |
| Location | 지역 |
| Tool | 정상 도구 의 악성 사용 (mimikatz 등) |

### 3.2 STIX JSON 예시 (Indicator)

```
{
  "type": "indicator",
  "id": "indicator--abc...",
  "created": "2026-05-11T...",
  "name": "Malicious C2 IP",
  "pattern": "[ipv4-addr:value = '1.2.3.4']",
  "pattern_type": "stix",
  "valid_from": "2026-05-11T...",
  "labels": ["malicious-activity"],
  "indicator_types": ["malicious-activity"]
}
```

### 3.3 Relationship

Object 간 관계를 표현. 예: "Indicator IP 가 Threat Actor APT29 와 attributed-to".

```
{
  "type": "relationship",
  "relationship_type": "attributed-to",
  "source_ref": "indicator--abc...",
  "target_ref": "threat-actor--apt29..."
}
```

## 4. TAXII 2.1 — 교환 프로토콜

TAXII (Trusted Automated eXchange of Intelligence Information) 는 STIX 데이터의
REST API 기반 교환. HTTPS + Bearer auth.

### 4.1 endpoint 구조

```
GET /taxii2/                          # 서버 메타
GET /taxii2/api1/collections          # collection 목록
GET /taxii2/api1/collections/<id>/objects?match[type]=indicator  # IOC 다운로드
POST /taxii2/api1/collections/<id>/objects  # IOC 업로드
```

### 4.2 collection

논리적 그룹. 예: "AbuseIPDB Critical", "MISP Daily Threats". 권한 단위로 분리.

## 5. OpenCTI 아키텍처

```
┌──────────────────────┐
│  OpenCTI Platform     │  GraphQL API + 대시보드 (3000)
│  (Node.js)            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Elasticsearch (검색) │  (9200)
│  + Redis (cache)      │  (6379)
│  + RabbitMQ (queue)   │  (5672)
│  + MinIO (file)       │  (9001)
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Workers              │  중대 처리 (Indicator → Elasticsearch indexing)
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Connectors           │  외부 source 통합 (MISP, AlienVault, ...)
│  (Python / NodeJS)    │
└──────────────────────┘
```

### 5.1 의존성

- Elasticsearch 8.x (검색)
- Redis (cache)
- RabbitMQ (queue)
- MinIO (S3-compatible file storage)
- Node.js (platform)
- Python 3 (workers + connectors)

### 5.2 docker-compose 표준

OpenCTI 의 공식 docker-compose.yml 는 8 컨테이너 (platform + workers + 4 dependencies +
prometheus + grafana). 6v6 환경에 추가 시 ~4GB RAM 추가 필요.

## 6. 5 무료 IOC feed 의 OpenCTI connector

| feed | OpenCTI connector |
|------|--------------------|
| MISP | opencti-connector-misp |
| OTX AlienVault | opencti-connector-alienvault |
| Abuse.ch (URLhaus / Feodotracker) | opencti-connector-abuseipdb-ipblocklist |
| OpenPhish | opencti-connector-openphish |
| Disrupt the Vortex (CISA AIS) | opencti-connector-cisa |

connector 가 24시간 주기로 feed pull → STIX 변환 → OpenCTI 의 collection 에 push.

## 7. 6v6 의 OpenCTI 추가 (W13 인프라 변경)

W13 부터 6v6 docker-compose 에 OpenCTI stack 추가:

```
services:
  opencti:
    image: opencti/platform:5.x
    networks:
      dmz:
        ipv4_address: 10.20.32.130
    # 의존성: elastic, redis, rabbitmq, minio
```

vhost: `cti.6v6.lab` → fw HAProxy → OpenCTI 3000. 학생 PC 에서 `http://cti.6v6.lab/` 접근.

## 8. 본 주차 실습 (W13 전 사전)

OpenCTI 자체를 6v6 에 설치하기 전에 STIX / TAXII 형식 + 무료 feed sample 분석.

### 1 — STIX JSON 분석

```
# 예시 STIX 다운로드 (URLhaus)
curl -s https://urlhaus.abuse.ch/downloads/csv_recent/ | head -10
# CSV → STIX 변환 표준 (Python 의 stix2 패키지)
```

### 2 — TAXII collection 조회 (public)

```
# OpenCTI 의 공개 demo
curl -s -H "Accept: application/taxii+json;version=2.1" \
  "https://app.opencti.io/taxii2/" | jq
```

### 3 — IOC 통합 시뮬

```
# AbuseIPDB blacklist 다운로드
wget -O /tmp/abuse_blacklist.txt https://lists.blocklist.de/lists/all.txt 2>/dev/null
head -10 /tmp/abuse_blacklist.txt
# 이 IP 리스트가 STIX Indicator 로 변환되어야 함
```

### 4 — MITRE ATT&CK 매핑

```
curl -s https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json | jq ".objects | length"
# 800+ object
```

### 5 — 6v6 환경에 OpenCTI 설치 계획 검토

(docker-compose 수정 + minimum RAM 8GB 권장)

## 9. 과제

A. STIX 분석 (필수) — Indicator / Threat Actor / Attack Pattern 의 STIX JSON 작성 (가상 예시)
B. TAXII 통신 (심화) — OpenCTI demo 의 collection 1개 조회 + STIX 다운로드
C. 5 무료 feed 평가 (정성) — 본 lab 환경에 적합한 3 feed 선택 + 이유

## 10. W13 (IOC Feed + Wazuh 통합) 예고

OpenCTI 의 IOC → Wazuh 의 CDB list 통합 → alert 자동 부여.
