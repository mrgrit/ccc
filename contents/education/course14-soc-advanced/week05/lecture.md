# Week 05: 위협 인텔리전스

## 학습 목표
- STIX/TAXII 표준의 구조와 활용 방법을 이해한다
- MISP 플랫폼에서 IOC를 생성, 공유, 검색할 수 있다
- OpenCTI를 사용하여 위협 인텔리전스를 시각화하고 분석할 수 있다
- IOC 피드를 Wazuh SIEM과 연동하여 실시간 탐지에 활용할 수 있다
- 위협 인텔리전스의 전략적/운영적/전술적 수준을 구분할 수 있다

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
| 0:00-0:50 | 위협 인텔리전스 이론 + STIX/TAXII (Part 1) | 강의 |
| 0:50-1:30 | MISP + OpenCTI (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | IOC 관리 + 피드 연동 실습 (Part 3) | 실습 |
| 2:30-3:10 | Wazuh 연동 + OpsClaw 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **TI** | Threat Intelligence | 위협 인텔리전스 - 사이버 위협에 대한 정보 | 범죄 정보 데이터베이스 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술, 기법, 절차 | 범행 수법 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표현 표준 (JSON) | 국제 수배서 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | 위협 정보 교환 프로토콜 | 국제 수배서 전송 시스템 |
| **MISP** | Malware Information Sharing Platform | 오픈소스 위협 인텔리전스 공유 플랫폼 | 경찰 간 수배 정보 공유 시스템 |
| **OpenCTI** | Open Cyber Threat Intelligence | 오픈소스 CTI 분석 플랫폼 | 범죄 분석 대시보드 |
| **피드** | Feed | IOC 데이터 자동 수신 채널 | 수배 정보 뉴스 구독 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 인텔리전스 (TI와 동의어) | 사이버 범죄 정보 |
| **APT** | Advanced Persistent Threat | 지능형 지속 위협 (국가급 공격) | 국가 지원 스파이 조직 |

---

# Part 1: 위협 인텔리전스 이론 + STIX/TAXII (50분)

## 1.1 위협 인텔리전스 개요

위협 인텔리전스(TI)는 **사이버 위협에 대한 증거 기반 지식**으로, 의사결정을 지원하는 컨텍스트가 포함된 정보다.

### TI의 3가지 수준

```
+--[전략적 TI]--+   +--[운영적 TI]--+   +--[전술적 TI]--+
| (Strategic)    |   | (Operational)  |   | (Tactical)     |
|                |   |                |   |                |
| 대상: CISO,경영|   | 대상: SOC 매니저|   | 대상: SOC 분석가|
|                |   |                |   |                |
| 내용:          |   | 내용:          |   | 내용:          |
| - 위협 동향    |   | - 캠페인 분석  |   | - IOC          |
| - 산업별 위험  |   | - 공격 그룹    |   | - 악성 IP/도메인|
| - 지정학적 요인|   | - TTP 분석     |   | - 파일 해시    |
| - 투자 방향    |   | - 인프라 분석  |   | - SIGMA/YARA룰 |
|                |   |                |   |                |
| 형식: 보고서   |   | 형식: 분석문서 |   | 형식: 기계판독 |
| 주기: 월/분기  |   | 주기: 주/월    |   | 주기: 실시간   |
+----------------+   +----------------+   +----------------+
```

### TI 생명주기

```
Step 1: 계획 (Planning)
  → 수집 요구사항 정의
  → 우선순위 설정
  ↓
Step 2: 수집 (Collection)
  → OSINT, 피드, 공유 플랫폼
  → 내부 로그, 인시던트 데이터
  ↓
Step 3: 처리 (Processing)
  → 정규화, 중복 제거
  → 신뢰도 평가
  ↓
Step 4: 분석 (Analysis)
  → 상관관계 분석
  → ATT&CK 매핑
  → 영향도 평가
  ↓
Step 5: 배포 (Dissemination)
  → SIEM 룰 업데이트
  → 보고서 작성
  → IOC 공유
  ↓
Step 6: 피드백 (Feedback)
  → 탐지 효과 평가
  → 요구사항 수정
  → (Step 1으로 순환)
```

## 1.2 STIX 2.1 표준

STIX(Structured Threat Information eXpression)는 OASIS가 관리하는 위협 정보 표현 표준이다.

### STIX 도메인 객체 (SDO)

```
+-- SDO (STIX Domain Objects) --+
|                                |
| [Attack Pattern]  공격 패턴    |
| [Campaign]        공격 캠페인  |
| [Course of Action] 대응 방안   |
| [Grouping]        그룹핑       |
| [Identity]        신원 정보    |
| [Indicator]       탐지 지표    |
| [Infrastructure]  인프라       |
| [Intrusion Set]   침입 세트    |
| [Location]        위치         |
| [Malware]         악성코드     |
| [Malware Analysis] 분석 결과  |
| [Note]            메모         |
| [Observed Data]   관찰 데이터  |
| [Opinion]         의견         |
| [Report]          보고서       |
| [Threat Actor]    위협 행위자  |
| [Tool]            도구         |
| [Vulnerability]   취약점       |
+--------------------------------+
```

### STIX 관계 객체 (SRO)

```
[Threat Actor] --uses--> [Malware]
      |                      |
      +--targets--> [Identity]
      |                      |
[Indicator] --indicates--> [Attack Pattern]
      |
      +--based-on--> [Observed Data]
```

### STIX Indicator 예시

```json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created": "2026-04-04T10:00:00.000Z",
  "modified": "2026-04-04T10:00:00.000Z",
  "name": "Malicious IP - C2 Server",
  "description": "Known C2 server for APT campaign",
  "indicator_types": ["malicious-activity"],
  "pattern": "[ipv4-addr:value = '203.0.113.50']",
  "pattern_type": "stix",
  "valid_from": "2026-04-04T10:00:00.000Z",
  "kill_chain_phases": [
    {
      "kill_chain_name": "mitre-attack",
      "phase_name": "command-and-control"
    }
  ],
  "labels": ["c2", "apt"]
}
```

## 1.3 TAXII 2.1 프로토콜

TAXII는 STIX 데이터를 **HTTP/HTTPS를 통해 교환**하는 프로토콜이다.

### TAXII 서비스 모델

```
[TAXII Server]
     |
     +-- API Root: /taxii2/
     |      |
     |      +-- Collections: /collections/
     |      |      |
     |      |      +-- Collection A (IOC 피드)
     |      |      |      |
     |      |      |      +-- Objects (STIX 번들)
     |      |      |
     |      |      +-- Collection B (APT 보고서)
     |      |
     |      +-- Status: /status/{id}
     |
     +-- Discovery: /taxii2/

[클라이언트 요청 예시]
GET /taxii2/collections/            → 컬렉션 목록
GET /taxii2/collections/{id}/       → 컬렉션 상세
GET /taxii2/collections/{id}/objects → STIX 객체 조회
POST /taxii2/collections/{id}/objects → STIX 객체 추가
```

### TAXII 통신 흐름

```
[생산자]                    [TAXII Server]               [소비자]
                                |
Producer --POST objects-->      |
  (STIX 데이터 전송)            |
                                |
                                | <--GET objects-- Consumer
                                |   (STIX 데이터 수신)
                                |
                                | <--Poll-- Consumer
                                |   (주기적 폴링)
```

## 1.4 IOC 유형과 품질

### IOC 유형별 특성

| IOC 유형 | 수명 | 오탐 위험 | 활용도 | 예시 |
|----------|------|----------|--------|------|
| **파일 해시 (MD5/SHA)** | 중간 | 매우 낮음 | 높음 | `d41d8cd98f...` |
| **IP 주소** | 짧음 | 중간 | 높음 | `203.0.113.50` |
| **도메인** | 중간 | 낮음 | 높음 | `evil.example.com` |
| **URL** | 짧음 | 낮음 | 중간 | `http://evil.com/payload` |
| **이메일 주소** | 길음 | 낮음 | 중간 | `attacker@evil.com` |
| **YARA 룰** | 길음 | 낮음 | 높음 | 행위 기반 패턴 |
| **SIGMA 룰** | 길음 | 낮음 | 높음 | 로그 기반 패턴 |

### IOC 품질 평가

```
[신뢰도 등급]
  A: 자체 확인된 IOC (자사 인시던트에서 추출)
  B: 신뢰할 수 있는 소스 (CERT, 정부 기관)
  C: 오픈소스 피드 (AbuseIPDB, VirusTotal)
  D: 미검증 소스
  E: 의심스러운 소스

[유효 기간]
  IP 주소: 7-30일 (C2는 자주 변경)
  도메인:  30-90일
  해시:    수년 (변형 없는 한)
  TTP:     수년 (행위 패턴)
```

---

# Part 2: MISP + OpenCTI (40분)

## 2.1 MISP 개요

MISP(Malware Information Sharing Platform)는 **위협 인텔리전스를 공유하고 협업**하기 위한 오픈소스 플랫폼이다.

### MISP 핵심 개념

```
[MISP 데이터 모델]

Organization (조직)
  └── Event (이벤트 = 인시던트/캠페인)
        ├── Attribute (속성 = IOC)
        │     ├── ip-dst: 203.0.113.50
        │     ├── domain: evil.example.com
        │     ├── md5: abc123...
        │     └── url: http://evil.com/mal
        │
        ├── Object (객체 = 구조화된 IOC)
        │     └── file object
        │           ├── filename: payload.exe
        │           ├── md5: abc123...
        │           └── sha256: def456...
        │
        ├── Galaxy (갤럭시 = 분류 체계)
        │     ├── MITRE ATT&CK
        │     ├── Threat Actor
        │     └── Malware Family
        │
        └── Tag (태그)
              ├── tlp:amber
              ├── type:osint
              └── misp-galaxy:threat-actor="APT28"
```

### TLP (Traffic Light Protocol)

```
[TLP:RED]    매우 제한적 공유 (지정된 수신자만)
[TLP:AMBER]  제한적 공유 (조직 내부 + 필요한 파트너)
[TLP:GREEN]  커뮤니티 공유 (같은 커뮤니티/섹터)
[TLP:WHITE]  무제한 공유 (공개 가능)
```

## 2.2 MISP API 활용

```bash
# MISP API 예시 (실습 환경에 MISP가 없는 경우 시뮬레이션)
cat << 'SCRIPT' > /tmp/misp_simulation.py
#!/usr/bin/env python3
"""MISP API 활용 시뮬레이션"""
import json
from datetime import datetime

# MISP 이벤트 생성 시뮬레이션
event = {
    "Event": {
        "info": "APT Campaign targeting Korean organizations",
        "date": "2026-04-04",
        "threat_level_id": "2",  # 1=High, 2=Medium, 3=Low
        "analysis": "2",  # 0=Initial, 1=Ongoing, 2=Complete
        "distribution": "1",  # 0=Org, 1=Community, 2=Connected, 3=All
        "Tag": [
            {"name": "tlp:amber"},
            {"name": "misp-galaxy:threat-actor=\"Lazarus Group\""},
            {"name": "misp-galaxy:mitre-attack-pattern=\"T1566.001\""}
        ],
        "Attribute": [
            {
                "type": "ip-dst",
                "category": "Network activity",
                "value": "203.0.113.50",
                "to_ids": True,
                "comment": "C2 server"
            },
            {
                "type": "domain",
                "category": "Network activity",
                "value": "malicious-update.example.com",
                "to_ids": True,
                "comment": "Phishing domain"
            },
            {
                "type": "md5",
                "category": "Payload delivery",
                "value": "d41d8cd98f00b204e9800998ecf8427e",
                "to_ids": True,
                "comment": "Dropper hash"
            },
            {
                "type": "url",
                "category": "External analysis",
                "value": "http://malicious-update.example.com/update.exe",
                "to_ids": True,
                "comment": "Payload download URL"
            },
            {
                "type": "email-src",
                "category": "Payload delivery",
                "value": "admin@fake-ministry.example.com",
                "to_ids": True,
                "comment": "Spear-phishing sender"
            }
        ]
    }
}

print("=== MISP 이벤트 시뮬레이션 ===")
print(json.dumps(event, indent=2, ensure_ascii=False))

# IOC 추출
print("\n=== 추출된 IOC 목록 ===")
for attr in event["Event"]["Attribute"]:
    if attr["to_ids"]:
        print(f"  [{attr['type']:12s}] {attr['value']:40s} ({attr['comment']})")

# MISP API 호출 예시 (실제 환경)
print("\n=== MISP API 사용법 ===")
print("# 이벤트 생성")
print("curl -X POST https://misp.example.com/events \\")
print("  -H 'Authorization: YOUR_API_KEY' \\")
print("  -H 'Content-Type: application/json' \\")
print("  -d @event.json")
print("")
print("# IOC 검색")
print("curl https://misp.example.com/attributes/restSearch \\")
print("  -H 'Authorization: YOUR_API_KEY' \\")
print("  -d '{\"type\":\"ip-dst\",\"to_ids\":true,\"last\":\"7d\"}'")
SCRIPT

python3 /tmp/misp_simulation.py
```

> **배우는 것**: MISP의 이벤트-속성 데이터 모델과 API를 통한 IOC 관리 방법

## 2.3 OpenCTI 개요

OpenCTI는 STIX 2.1 기반의 **위협 인텔리전스 분석 및 시각화 플랫폼**이다.

```
+--[OpenCTI 아키텍처]--+
|                       |
| [Connectors]          |  ← 데이터 수집
|   - MISP              |
|   - AlienVault OTX    |
|   - VirusTotal        |
|   - AbuseIPDB         |
|   - CVE               |
|                       |
| [Core Platform]       |  ← 분석/저장
|   - STIX 2.1 기반     |
|   - Graph DB (Neo4j)  |
|   - Elasticsearch     |
|   - RabbitMQ          |
|                       |
| [Frontend]            |  ← 시각화
|   - 관계 그래프       |
|   - 타임라인          |
|   - 대시보드          |
|   - 보고서            |
+------------------------+
```

### OpenCTI 접속 확인

```bash
# OpenCTI 접속 테스트
echo "=== OpenCTI 접속 테스트 ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  http://10.20.30.100:9400 2>/dev/null)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "[OK] OpenCTI 접근 가능 (HTTP $HTTP_CODE)"
    echo "URL: http://10.20.30.100:9400"
else
    echo "[INFO] OpenCTI 미가동 (HTTP $HTTP_CODE)"
    echo "시뮬레이션 모드로 진행합니다."
fi
```

---

# Part 3: IOC 관리 + 피드 연동 실습 (50분)

## 3.1 오픈소스 IOC 피드 수집

> **실습 목적**: 무료 오픈소스 IOC 피드를 수집하고 파싱하여 SIEM에 적용 가능한 형태로 변환한다.
>
> **배우는 것**: IOC 피드 소스, 데이터 파싱, 정규화 방법
>
> **실전 활용**: 실제 SOC에서 IOC 피드를 자동 수집하여 방화벽/SIEM 룰에 반영하는 프로세스

```bash
# 오픈소스 IOC 피드 수집 스크립트
cat << 'SCRIPT' > /tmp/ioc_collector.py
#!/usr/bin/env python3
"""오픈소스 IOC 피드 수집기"""
import json
from datetime import datetime

# 시뮬레이션 데이터 (실제 환경에서는 API 호출)
feeds = {
    "AbuseIPDB": {
        "type": "ip",
        "url": "https://api.abuseipdb.com/api/v2/blacklist",
        "iocs": [
            {"value": "203.0.113.10", "confidence": 95, "category": "brute-force"},
            {"value": "203.0.113.20", "confidence": 88, "category": "web-attack"},
            {"value": "203.0.113.30", "confidence": 92, "category": "port-scan"},
            {"value": "198.51.100.50", "confidence": 75, "category": "spam"},
            {"value": "198.51.100.60", "confidence": 99, "category": "c2"},
        ]
    },
    "URLhaus": {
        "type": "url",
        "url": "https://urlhaus-api.abuse.ch/v1/urls/recent/",
        "iocs": [
            {"value": "http://evil.example.com/malware.exe", "threat": "malware_download"},
            {"value": "http://phish.example.com/login.php", "threat": "phishing"},
            {"value": "http://c2.example.com/beacon", "threat": "c2_communication"},
        ]
    },
    "MalwareBazaar": {
        "type": "hash",
        "url": "https://mb-api.abuse.ch/api/v1/",
        "iocs": [
            {"value": "a" * 64, "malware": "Emotet", "filetype": "exe"},
            {"value": "b" * 64, "malware": "AgentTesla", "filetype": "exe"},
            {"value": "c" * 64, "malware": "Remcos", "filetype": "dll"},
        ]
    },
    "FeodoTracker": {
        "type": "ip",
        "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.json",
        "iocs": [
            {"value": "192.0.2.10", "malware": "Dridex", "port": 443},
            {"value": "192.0.2.20", "malware": "TrickBot", "port": 447},
            {"value": "192.0.2.30", "malware": "QakBot", "port": 995},
        ]
    }
}

print("=" * 70)
print("  오픈소스 IOC 피드 수집 결과")
print(f"  수집 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

total_iocs = 0
for feed_name, feed_data in feeds.items():
    count = len(feed_data["iocs"])
    total_iocs += count
    print(f"\n--- {feed_name} ({feed_data['type']}) ---")
    print(f"  소스: {feed_data['url']}")
    print(f"  IOC 수: {count}건")
    for ioc in feed_data["iocs"]:
        extra = {k: v for k, v in ioc.items() if k != "value"}
        print(f"  [{feed_data['type']:6s}] {ioc['value'][:50]:50s} {extra}")

print(f"\n총 수집: {total_iocs}건 (피드 {len(feeds)}개)")

# Wazuh CDB 리스트 형식으로 변환
print("\n=== Wazuh CDB 리스트 형식 변환 ===")
print("# /var/ossec/etc/lists/malicious_ips")
for feed_name, feed_data in feeds.items():
    if feed_data["type"] == "ip":
        for ioc in feed_data["iocs"]:
            source = feed_name.lower()
            print(f"{ioc['value']}:{source}")
SCRIPT

python3 /tmp/ioc_collector.py
```

> **결과 해석**: 여러 피드에서 수집한 IOC를 Wazuh CDB(Constant Database) 리스트 형식으로 변환하면 SIEM에서 실시간 매칭에 사용할 수 있다.

## 3.2 IOC 품질 관리

```bash
cat << 'SCRIPT' > /tmp/ioc_quality.py
#!/usr/bin/env python3
"""IOC 품질 관리 + 중복/만료 처리"""
from datetime import datetime, timedelta

# IOC 저장소 시뮬레이션
ioc_db = [
    {"type": "ip", "value": "203.0.113.10", "source": "abuseipdb",
     "added": "2026-04-01", "confidence": 95, "hits": 3},
    {"type": "ip", "value": "203.0.113.10", "source": "feodotracker",
     "added": "2026-04-02", "confidence": 88, "hits": 1},
    {"type": "ip", "value": "198.51.100.50", "source": "abuseipdb",
     "added": "2026-02-15", "confidence": 60, "hits": 0},
    {"type": "domain", "value": "evil.example.com", "source": "urlhaus",
     "added": "2026-04-03", "confidence": 92, "hits": 5},
    {"type": "hash", "value": "a" * 64, "source": "malwarebazaar",
     "added": "2026-03-01", "confidence": 99, "hits": 2},
    {"type": "ip", "value": "10.20.30.1", "source": "unknown",
     "added": "2026-04-04", "confidence": 30, "hits": 0},
]

today = datetime(2026, 4, 4)

print("=== IOC 품질 점검 ===\n")

# 1. 중복 탐지
print("--- 중복 IOC ---")
seen = {}
for ioc in ioc_db:
    key = f"{ioc['type']}:{ioc['value']}"
    if key in seen:
        print(f"  중복: {key} (소스: {seen[key]} + {ioc['source']})")
    seen[key] = ioc["source"]

# 2. 만료 IOC (IP: 30일, 도메인: 90일, 해시: 365일)
print("\n--- 만료된 IOC ---")
expiry = {"ip": 30, "domain": 90, "hash": 365}
for ioc in ioc_db:
    added = datetime.strptime(ioc["added"], "%Y-%m-%d")
    max_age = expiry.get(ioc["type"], 30)
    if (today - added).days > max_age:
        print(f"  만료: [{ioc['type']}] {ioc['value'][:40]} "
              f"(추가: {ioc['added']}, {(today-added).days}일 경과)")

# 3. 낮은 신뢰도 IOC
print("\n--- 낮은 신뢰도 (50 미만) ---")
for ioc in ioc_db:
    if ioc["confidence"] < 50:
        print(f"  저신뢰: [{ioc['type']}] {ioc['value'][:40]} "
              f"(신뢰도: {ioc['confidence']})")

# 4. 내부 IP 오등록
print("\n--- 내부 IP 오등록 ---")
for ioc in ioc_db:
    if ioc["type"] == "ip" and ioc["value"].startswith("10."):
        print(f"  오등록: {ioc['value']} (내부 IP가 IOC에 포함됨!)")

# 5. 미사용 IOC (hits = 0)
print("\n--- 미사용 IOC (탐지 0건) ---")
for ioc in ioc_db:
    if ioc["hits"] == 0:
        print(f"  미사용: [{ioc['type']}] {ioc['value'][:40]} "
              f"(소스: {ioc['source']})")

print("\n=== 품질 점검 완료 ===")
SCRIPT

python3 /tmp/ioc_quality.py
```

> **실전 활용**: IOC 저장소를 주기적으로 점검하여 만료, 중복, 저품질 IOC를 정리해야 한다. 방치된 IOC가 쌓이면 SIEM 성능이 저하된다.

## 3.3 Wazuh CDB 리스트 생성

```bash
# Wazuh CDB(Constant Database) 리스트로 IOC 배포
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# CDB 리스트 디렉토리 확인
ls -la /var/ossec/etc/lists/ 2>/dev/null

# 악성 IP 리스트 생성
sudo tee /var/ossec/etc/lists/malicious_ips << 'LIST'
203.0.113.10:abuseipdb_bruteforce
203.0.113.20:abuseipdb_webattack
203.0.113.30:abuseipdb_portscan
198.51.100.60:abuseipdb_c2
192.0.2.10:feodo_dridex
192.0.2.20:feodo_trickbot
192.0.2.30:feodo_qakbot
LIST

# 악성 도메인 리스트 생성
sudo tee /var/ossec/etc/lists/malicious_domains << 'LIST'
evil.example.com:urlhaus_malware
phish.example.com:urlhaus_phishing
c2.example.com:urlhaus_c2
malicious-update.example.com:campaign_apt
LIST

# CDB 컴파일
cd /var/ossec/etc/lists/
sudo /var/ossec/bin/wazuh-makelists 2>/dev/null || echo "makelists 실행 완료"

echo ""
echo "=== CDB 리스트 파일 ==="
ls -la /var/ossec/etc/lists/

# ossec.conf에 리스트 등록 확인
echo ""
echo "=== 등록된 리스트 ==="
sudo grep "list" /var/ossec/etc/ossec.conf 2>/dev/null | head -10

REMOTE
```

> **명령어 해설**:
> - CDB 리스트는 `key:value` 형식으로, Wazuh 룰에서 `<list>` 태그로 참조한다
> - `wazuh-makelists`: CDB 텍스트 파일을 바이너리 형식으로 컴파일
>
> **트러블슈팅**:
> - "Permission denied" → `sudo` 사용 확인
> - 리스트가 룰에서 인식 안 됨 → ossec.conf에 `<list>` 경로 등록 필요

## 3.4 IOC 기반 Wazuh 탐지 룰

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# IOC 기반 탐지 룰 추가
sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,threat_intel,ioc,">

  <!-- 알려진 악성 IP 접근 탐지 -->
  <rule id="100600" level="12">
    <if_group>syslog</if_group>
    <list field="srcip" lookup="address_match_key">etc/lists/malicious_ips</list>
    <description>[TI] 알려진 악성 IP로부터의 접근: $(srcip)</description>
    <group>threat_intel,malicious_ip,</group>
  </rule>

  <!-- 악성 IP로의 아웃바운드 연결 탐지 (C2 의심) -->
  <rule id="100601" level="14">
    <if_group>syslog</if_group>
    <list field="dstip" lookup="address_match_key">etc/lists/malicious_ips</list>
    <description>[TI-CRITICAL] 악성 IP로의 아웃바운드 연결 - C2 의심: $(dstip)</description>
    <group>threat_intel,c2_communication,critical_alert,</group>
  </rule>

  <!-- C2 IP 반복 통신 (5분 내 3회) -->
  <rule id="100602" level="15" frequency="3" timeframe="300">
    <if_matched_sid>100601</if_matched_sid>
    <same_source_ip/>
    <description>[TI-APT] C2 서버 반복 통신 탐지 - APT 활동 의심!</description>
    <group>threat_intel,apt,critical_alert,</group>
  </rule>

</group>
RULES

# 문법 검사
sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

> **배우는 것**: CDB 리스트를 Wazuh 룰의 `<list>` 태그로 참조하여 IOC 기반 실시간 탐지를 구현하는 방법

---

# Part 4: Wazuh 연동 + OpsClaw 자동화 (40분)

## 4.1 IOC 피드 자동 업데이트

```bash
# IOC 피드 자동 업데이트 스크립트
cat << 'SCRIPT' > /tmp/ioc_updater.sh
#!/bin/bash
# IOC 피드 자동 업데이트 (cron에 등록하여 주기 실행)
LOG="/var/log/ioc_update.log"
LISTS_DIR="/var/ossec/etc/lists"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] IOC 업데이트 시작" >> $LOG

# 1. AbuseIPDB 블랙리스트 다운로드 (API 키 필요)
# curl -s -H "Key: YOUR_API_KEY" \
#   "https://api.abuseipdb.com/api/v2/blacklist?confidenceMinimum=90" \
#   | python3 -c "
#     import sys,json
#     data = json.load(sys.stdin)
#     for item in data.get('data',[]):
#         print(f\"{item['ipAddress']}:abuseipdb\")
#   " > $LISTS_DIR/malicious_ips_new

# 2. FeodoTracker C2 리스트
# curl -s "https://feodotracker.abuse.ch/downloads/ipblocklist.json" \
#   | python3 -c "
#     import sys,json
#     for item in json.load(sys.stdin):
#         print(f\"{item['ip_address']}:feodo_{item.get('malware','unknown')}\")
#   " >> $LISTS_DIR/malicious_ips_new

# 시뮬레이션 (실제 환경에서는 위 curl 명령 사용)
echo "203.0.113.10:abuseipdb_bruteforce" > $LISTS_DIR/malicious_ips_new
echo "203.0.113.20:abuseipdb_webattack" >> $LISTS_DIR/malicious_ips_new
echo "[$DATE] 새 IOC: $(wc -l < $LISTS_DIR/malicious_ips_new)건" >> $LOG

# 3. 기존 리스트와 병합 (중복 제거)
sort -u $LISTS_DIR/malicious_ips $LISTS_DIR/malicious_ips_new \
  > $LISTS_DIR/malicious_ips_merged 2>/dev/null
mv $LISTS_DIR/malicious_ips_merged $LISTS_DIR/malicious_ips
rm -f $LISTS_DIR/malicious_ips_new

# 4. CDB 재컴파일
cd $LISTS_DIR && /var/ossec/bin/wazuh-makelists 2>/dev/null

echo "[$DATE] IOC 업데이트 완료" >> $LOG
SCRIPT

echo "IOC 자동 업데이트 스크립트 작성 완료"
echo ""
echo "# cron 등록 예시 (매 6시간)"
echo "0 */6 * * * /tmp/ioc_updater.sh"
```

## 4.2 OpsClaw를 활용한 TI 워크플로우

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# TI 워크플로우 프로젝트
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "ti-ioc-deployment",
    "request_text": "위협 인텔리전스 IOC 수집 및 SIEM 배포",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# IOC 배포 + 검증 자동화
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "wc -l /var/ossec/etc/lists/malicious_ips 2>/dev/null && echo IOC_COUNT_OK || echo IOC_LIST_MISSING",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "grep -c \"threat_intel\" /var/ossec/etc/rules/local_rules.xml 2>/dev/null && echo TI_RULES_OK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "tail -5 /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -c \"TI\" && echo TI_ALERTS_CHECK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://10.20.30.100:8002"
  }'

sleep 3
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool 2>/dev/null | head -30
```

> **실전 활용**: OpsClaw로 IOC 배포를 자동화하면, 새로운 위협 인텔리전스가 발표될 때 신속하게 모든 SIEM에 반영할 수 있다.

## 4.3 STIX 파일 파싱 실습

```bash
cat << 'SCRIPT' > /tmp/stix_parser.py
#!/usr/bin/env python3
"""STIX 2.1 번들 파싱 및 IOC 추출"""
import json

# STIX 2.1 번들 예시
stix_bundle = {
    "type": "bundle",
    "id": "bundle--a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "objects": [
        {
            "type": "threat-actor",
            "id": "threat-actor--56f3f0db-b5d5-431c-ae56-c18f02caf500",
            "name": "APT28",
            "aliases": ["Fancy Bear", "Sofacy", "Pawn Storm"],
            "description": "Russian state-sponsored threat group",
            "threat_actor_types": ["nation-state"],
            "first_seen": "2004-01-01T00:00:00Z",
        },
        {
            "type": "indicator",
            "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
            "name": "APT28 C2 IP",
            "pattern": "[ipv4-addr:value = '203.0.113.50']",
            "pattern_type": "stix",
            "valid_from": "2026-04-01T00:00:00Z",
            "indicator_types": ["malicious-activity"],
        },
        {
            "type": "indicator",
            "id": "indicator--9f3f3e3c-28e5-5dcg-a49g-a9ff57c4de4g",
            "name": "APT28 Malware Hash",
            "pattern": "[file:hashes.'SHA-256' = 'abc123def456']",
            "pattern_type": "stix",
            "valid_from": "2026-04-01T00:00:00Z",
            "indicator_types": ["malicious-activity"],
        },
        {
            "type": "malware",
            "id": "malware--fdd60b30-b67c-11e3-b0b9-f01faf20d111",
            "name": "X-Agent",
            "malware_types": ["backdoor", "remote-access-trojan"],
            "is_family": True,
        },
        {
            "type": "relationship",
            "id": "relationship--44298a74-ba52-4f0c-87a3-1824e67032fc",
            "relationship_type": "uses",
            "source_ref": "threat-actor--56f3f0db-b5d5-431c-ae56-c18f02caf500",
            "target_ref": "malware--fdd60b30-b67c-11e3-b0b9-f01faf20d111",
        },
        {
            "type": "relationship",
            "id": "relationship--55309b85-cb63-5g1d-98b4-2935f78143gd",
            "relationship_type": "indicates",
            "source_ref": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
            "target_ref": "malware--fdd60b30-b67c-11e3-b0b9-f01faf20d111",
        },
    ]
}

print("=== STIX 2.1 번들 파싱 ===\n")

# 객체 유형별 분류
type_count = {}
for obj in stix_bundle["objects"]:
    t = obj["type"]
    type_count[t] = type_count.get(t, 0) + 1

print("객체 유형 분포:")
for t, c in type_count.items():
    print(f"  {t:20s}: {c}개")

# IOC(Indicator) 추출
print("\n=== 추출된 IOC ===")
import re
for obj in stix_bundle["objects"]:
    if obj["type"] == "indicator":
        pattern = obj["pattern"]
        # STIX 패턴에서 값 추출
        match = re.search(r"'([^']+)'", pattern)
        value = match.group(1) if match else pattern
        print(f"  [{obj['name']}]")
        print(f"    Pattern: {pattern}")
        print(f"    Value:   {value}")
        print(f"    Valid:   {obj.get('valid_from', 'N/A')}")

# 관계 매핑
print("\n=== 관계 그래프 ===")
obj_names = {}
for obj in stix_bundle["objects"]:
    obj_names[obj["id"]] = obj.get("name", obj["type"])

for obj in stix_bundle["objects"]:
    if obj["type"] == "relationship":
        src = obj_names.get(obj["source_ref"], "?")
        tgt = obj_names.get(obj["target_ref"], "?")
        rel = obj["relationship_type"]
        print(f"  {src} --{rel}--> {tgt}")
SCRIPT

python3 /tmp/stix_parser.py
```

## 4.4 TI 효과 측정

```bash
cat << 'SCRIPT' > /tmp/ti_effectiveness.py
#!/usr/bin/env python3
"""위협 인텔리전스 효과 측정"""

# 시뮬레이션 데이터
ti_metrics = {
    "TI 도입 전": {
        "탐지율": 45,
        "오탐률": 35,
        "MTTD_분": 180,
        "IOC_수": 0,
        "자동차단": 0,
    },
    "TI 도입 후": {
        "탐지율": 78,
        "오탐률": 12,
        "MTTD_분": 15,
        "IOC_수": 5000,
        "자동차단": 65,
    }
}

print("=" * 60)
print("  위협 인텔리전스 도입 효과 분석")
print("=" * 60)
print(f"\n{'지표':12s} {'도입 전':>10s} {'도입 후':>10s} {'변화':>10s}")
print("-" * 50)

for metric in ["탐지율", "오탐률", "MTTD_분", "IOC_수", "자동차단"]:
    before = ti_metrics["TI 도입 전"][metric]
    after = ti_metrics["TI 도입 후"][metric]
    if before > 0:
        change = (after - before) / before * 100
        sign = "+" if change > 0 else ""
        print(f"{metric:12s} {before:>10} {after:>10} {sign}{change:>8.0f}%")
    else:
        print(f"{metric:12s} {before:>10} {after:>10} {'N/A':>10s}")

print("\n핵심 개선:")
print("  - 탐지율 33%p 향상 (45% → 78%)")
print("  - MTTD 92% 단축 (3시간 → 15분)")
print("  - 오탐률 23%p 감소 (35% → 12%)")
SCRIPT

python3 /tmp/ti_effectiveness.py
```

---

## 체크리스트

- [ ] 위협 인텔리전스의 3가지 수준(전략/운영/전술)을 구분할 수 있다
- [ ] TI 생명주기 6단계를 설명할 수 있다
- [ ] STIX 2.1의 SDO와 SRO 개념을 이해한다
- [ ] TAXII 프로토콜의 역할과 동작 방식을 설명할 수 있다
- [ ] IOC 유형별 특성(수명, 오탐 위험)을 알고 있다
- [ ] MISP의 이벤트-속성 데이터 모델을 이해한다
- [ ] TLP 4단계를 구분할 수 있다
- [ ] Wazuh CDB 리스트를 생성하고 룰에 연동할 수 있다
- [ ] IOC 품질 관리(만료, 중복, 신뢰도)를 수행할 수 있다
- [ ] OpsClaw로 IOC 배포를 자동화할 수 있다

---

## 복습 퀴즈

**Q1.** 전술적 TI와 전략적 TI의 주요 차이점은?

<details><summary>정답</summary>
전술적 TI는 SOC 분석가가 사용하는 기계 판독 가능한 IOC(IP, 해시, 도메인)로 실시간 탐지에 활용된다. 전략적 TI는 CISO/경영진을 위한 위협 동향 보고서로 투자 의사결정에 활용된다.
</details>

**Q2.** STIX와 TAXII의 관계를 설명하시오.

<details><summary>정답</summary>
STIX는 위협 정보를 표현하는 데이터 형식(JSON)이고, TAXII는 STIX 데이터를 교환하는 전송 프로토콜(HTTP/HTTPS)이다. STIX가 "편지 내용"이라면 TAXII는 "우체국"에 해당한다.
</details>

**Q3.** IOC로서 IP 주소의 약점은 무엇인가?

<details><summary>정답</summary>
수명이 짧다. 공격자가 C2 서버의 IP를 자주 변경(1-7일)하므로 오래된 IP IOC는 의미가 없다. 또한 CDN이나 클라우드 IP를 사용하면 정상 서비스와 겹쳐 오탐이 발생할 수 있다.
</details>

**Q4.** TLP:AMBER의 공유 범위는?

<details><summary>정답</summary>
조직 내부와 업무상 필요한 파트너까지만 공유할 수 있다. 일반 공개나 커뮤니티 전체 공유는 불가하다.
</details>

**Q5.** Wazuh CDB 리스트의 형식과 용도를 설명하시오.

<details><summary>정답</summary>
"key:value" 형식의 텍스트 파일로, Wazuh 룰에서 `<list>` 태그로 참조하여 실시간 IOC 매칭에 사용한다. IP, 도메인 등의 블랙리스트를 관리하며, wazuh-makelists로 바이너리 형식으로 컴파일한다.
</details>

**Q6.** MISP에서 "to_ids" 플래그의 의미는?

<details><summary>정답</summary>
해당 IOC를 IDS/SIEM 탐지 룰에 사용해도 좋다는 표시다. to_ids=True인 속성만 자동으로 SIEM에 연동하고, False인 것은 참고 정보로만 활용한다. 오탐 위험이 높은 IOC는 False로 설정한다.
</details>

**Q7.** IOC 품질 관리에서 "만료" 처리가 필요한 이유는?

<details><summary>정답</summary>
1) 오래된 IOC는 더 이상 유효하지 않아 오탐을 유발한다. 2) 누적된 IOC가 SIEM 성능을 저하시킨다. 3) IP 주소는 재할당되어 정상 서버가 차단될 수 있다.
</details>

**Q8.** OpenCTI가 MISP와 다른 점은?

<details><summary>정답</summary>
OpenCTI는 STIX 2.1 기반 그래프 데이터베이스(Neo4j)를 사용하여 위협 객체 간 관계를 시각화하고 분석하는 데 강점이 있다. MISP는 IOC 공유와 협업에 초점이 맞춰져 있다. 두 플랫폼은 커넥터로 연동하여 상호 보완적으로 사용한다.
</details>

**Q9.** STIX Indicator의 pattern 필드 예시를 하나 작성하시오.

<details><summary>정답</summary>
`[ipv4-addr:value = '203.0.113.50']` 또는 `[file:hashes.'SHA-256' = 'abc123...']` 형식이다. 대괄호 안에 객체타입:속성 = '값' 형식으로 작성한다.
</details>

**Q10.** 위협 인텔리전스 도입 시 가장 먼저 해야 할 것은?

<details><summary>정답</summary>
수집 요구사항을 정의하는 것이다. 자사의 산업, 규모, 위협 프로필에 맞는 TI 소스를 선정하고, 어떤 유형의 IOC가 필요한지, 어떤 SIEM/도구에 연동할지를 먼저 계획해야 한다. 무작정 피드를 연동하면 오탐과 노이즈만 늘어난다.
</details>

---

## 과제

### 과제 1: IOC 수집 + SIEM 연동 (필수)

오픈소스 IOC 피드 3개 이상에서 데이터를 수집하고:
1. Wazuh CDB 리스트로 변환
2. IOC 기반 탐지 룰 3개 작성
3. 시뮬레이션으로 탐지 확인
4. 품질 점검 (만료, 중복, 신뢰도)

### 과제 2: STIX 2.1 보고서 작성 (선택)

가상의 APT 캠페인에 대한 STIX 2.1 번들을 작성하라:
1. Threat Actor, Malware, Indicator, Attack Pattern 각 1개 이상
2. Relationship으로 연결
3. 파이썬으로 파싱하여 관계 그래프 출력

---

## 다음 주 예고

**Week 06: 위협 헌팅 심화**에서는 가설 기반 위협 헌팅 방법론을 학습하고, ATT&CK 매핑과 베이스라인 이탈 분석으로 숨겨진 위협을 찾아낸다.
