# Week 13: OpenCTI (2) — 위협 인텔리전스 활용

## 학습 목표
- IOC(침해 지표)를 체계적으로 관리할 수 있다
- 공격 그룹을 분석하고 프로파일링할 수 있다
- 위협 헌팅의 기본 프로세스를 수행할 수 있다
- OpenCTI 데이터를 실제 보안 운영에 활용할 수 있다

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

# Week 13: OpenCTI (2) — 위협 인텔리전스 활용

## 학습 목표

- IOC(침해 지표)를 체계적으로 관리할 수 있다
- 공격 그룹을 분석하고 프로파일링할 수 있다
- 위협 헌팅의 기본 프로세스를 수행할 수 있다
- OpenCTI 데이터를 실제 보안 운영에 활용할 수 있다

---

## 1. IOC(Indicator of Compromise) 관리

### 1.1 IOC의 종류

| 유형 | 설명 | 예시 |
|------|------|------|
| IP 주소 | C2 서버, 스캐너 | 1.2.3.4 |
| 도메인 | 피싱, 악성 사이트 | evil.example.com |
| URL | 악성코드 배포 | http://evil.com/malware.exe |
| 파일 해시 | 악성 파일 식별 | MD5, SHA256 |
| 이메일 | 피싱 발송자 | attacker@phish.com |
| YARA 룰 | 파일 패턴 | rule Emotet { ... } |

### 1.2 IOC 수명주기

```
수집 → 검증 → 등록 → 배포 → 탐지 → 만료/갱신
```

| 단계 | 설명 |
|------|------|
| 수집 | 피드, 보고서, 인시던트에서 IOC 수집 |
| 검증 | 오탐 확인, 신뢰도 평가 |
| 등록 | OpenCTI에 STIX 형식으로 등록 |
| 배포 | SIEM, IPS, 방화벽으로 전달 |
| 탐지 | 보안 장비에서 IOC 매칭 |
| 만료 | 유효기간 지나면 비활성화 |

---

## 2. 실습 환경 접속

> **이 실습을 왜 하는가?**
> "OpenCTI (2) — 위협 인텔리전스 활용" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

> **실습 목적**: OpenCTI에서 수집된 위협 인텔리전스를 Wazuh/Suricata와 연동하여 탐지에 활용한다
>
> **배우는 것**: IOC(침해지표)를 SIEM/IPS 룰에 자동 반영하는 CTI 운영 워크플로우를 배운다
>
> **결과 해석**: CTI에서 수집한 IP/도메인이 탐지 룰에 반영되고, 해당 트래픽 발생 시 알림이 생성되면 연동이 정상이다
>
> **실전 활용**: 위협 인텔리전스 기반 선제 방어(Proactive Defense)는 APT 대응의 핵심 전략이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

# API 토큰 설정 (대시보드에서 확인한 값)
OPENCTI_TOKEN="your-api-token-here"
```

---

## 3. IOC 등록 및 관리

### 3.1 API로 IOC 생성

```bash
# 악성 IP 지표 생성
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{                                                # 요청 데이터(body)
    "query": "mutation { indicatorAdd(input: { name: \"Malicious C2 Server\", pattern: \"[ipv4-addr:value = '"'"'203.0.113.50'"'"']\", pattern_type: \"stix\", x_opencti_main_observable_type: \"IPv4-Addr\", valid_from: \"2026-03-27T00:00:00.000Z\" }) { id name } }"
  }' | python3 -m json.tool
```

### 3.2 대량 IOC 등록

실무에서는 CSV나 STIX 번들로 대량 등록한다:

```bash
# IOC 목록에서 STIX 번들 자동 생성
cat << 'PYEOF' > /tmp/create_stix_bundle.py
import json, uuid
from datetime import datetime

iocs = [
    ("Lazarus C2 #1", "ipv4-addr", "203.0.113.10"),
    ("Lazarus C2 #2", "ipv4-addr", "203.0.113.11"),
    ("Lazarus C2 #3", "ipv4-addr", "203.0.113.12"),
    ("Phishing Domain #1", "domain-name", "login-secure-update.example.com"),
    ("Phishing Domain #2", "domain-name", "account-verify-now.example.com"),
    ("Malware Hash - Backdoor", "file:hashes.SHA-256", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"),
]

now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
objects = []

for name, obs_type, value in iocs:                     # 반복문 시작
    indicator_id = f"indicator--{uuid.uuid4()}"
    if "hashes" in obs_type:
        pattern = f"[file:hashes.'SHA-256' = '{value}']"
    else:
        pattern = f"[{obs_type}:value = '{value}']"

    objects.append({
        "type": "indicator",
        "spec_version": "2.1",
        "id": indicator_id,
        "created": now,
        "modified": now,
        "name": name,
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": now,
        "labels": ["malicious-activity"],
        "confidence": 85
    })

bundle = {
    "type": "bundle",
    "id": f"bundle--{uuid.uuid4()}",
    "objects": objects
}

with open("/tmp/lazarus_iocs.json", "w") as f:
    json.dump(bundle, f, indent=2)

print(f"Generated {len(objects)} IOCs")
PYEOF

python3 /tmp/create_stix_bundle.py                     # Python 스크립트 실행
cat /tmp/lazarus_iocs.json | python3 -m json.tool | head -30
```

---

## 4. 공격 그룹 분석

### 4.1 Threat Actor 등록

```bash
# 위협 행위자 STIX 번들 생성
cat << 'STIXEOF' > /tmp/threat_actor.json
{
  "type": "bundle",
  "id": "bundle--ta-lab-001",
  "objects": [
    {
      "type": "threat-actor",
      "spec_version": "2.1",
      "id": "threat-actor--lab-lazarus",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab-Lazarus Group",
      "description": "실습용 위협 행위자. 북한 연계 APT 그룹을 모방한 시나리오.",
      "threat_actor_types": ["nation-state"],
      "aliases": ["Hidden Cobra", "ZINC"],
      "goals": ["Financial gain", "Espionage"],
      "sophistication": "advanced",
      "resource_level": "government",
      "primary_motivation": "organizational-gain"
    },
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--lab-backdoor",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab-DreamBot",
      "description": "실습용 백도어 악성코드",
      "malware_types": ["backdoor", "remote-access-trojan"],
      "is_family": true
    },
    {
      "type": "attack-pattern",
      "spec_version": "2.1",
      "id": "attack-pattern--lab-spearphish",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Spearphishing Attachment",
      "description": "표적 피싱 메일에 악성 첨부파일을 포함하여 전달",
      "external_references": [
        {
          "source_name": "mitre-attack",
          "external_id": "T1566.001"
        }
      ]
    },
    {
      "type": "relationship",
      "spec_version": "2.1",
      "id": "relationship--lab-001",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "relationship_type": "uses",
      "source_ref": "threat-actor--lab-lazarus",
      "target_ref": "malware--lab-backdoor"
    },
    {
      "type": "relationship",
      "spec_version": "2.1",
      "id": "relationship--lab-002",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "relationship_type": "uses",
      "source_ref": "threat-actor--lab-lazarus",
      "target_ref": "attack-pattern--lab-spearphish"
    }
  ]
}
STIXEOF
```

### 4.2 관계 그래프 확인

OpenCTI 웹 UI에서:
1. Threats > Threat Actors 메뉴
2. "Lab-Lazarus Group" 클릭
3. Knowledge 탭 → 관계 그래프 확인

```
Lab-Lazarus Group
  ├── uses → Lab-DreamBot (malware)
  ├── uses → Spearphishing Attachment (attack-pattern)
  └── indicates → IOC (IP, Domain, Hash)
```

### 4.3 공격 그룹 프로파일 작성

분석 보고서 형식:

| 항목 | 내용 |
|------|------|
| 그룹명 | Lab-Lazarus Group |
| 별칭 | Hidden Cobra, ZINC |
| 국적/소속 | 북한 (nation-state) |
| 동기 | 금전적 이득, 정보 수집 |
| 기술 수준 | 고급 (advanced) |
| 주요 TTPs | T1566.001 (Spearphishing), T1059 (Command Execution) |
| 주요 도구 | Lab-DreamBot (RAT) |
| IOC | 203.0.113.10-12, login-secure-update.example.com |
| 표적 산업 | 금융, 암호화폐 거래소 |

---

## 5. 위협 헌팅 (Threat Hunting)

### 5.1 위협 헌팅이란?

기존 보안 장비의 알림에 의존하지 않고, **능동적으로 위협을 탐색**하는 활동이다.

```
가설 설정 → 데이터 수집 → 분석 → 결론
```

### 5.2 헌팅 시나리오: Lazarus IOC 매칭

**가설**: "우리 네트워크에서 Lab-Lazarus의 C2 서버와 통신하는 호스트가 있을 수 있다."

**Step 1: IOC 목록 추출**

```bash
# OpenCTI에서 Lazarus 관련 IP IOC 추출
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{                                                # 요청 데이터(body)
    "query": "{ indicators(search: \"Lazarus\", first: 50) { edges { node { name pattern } } } }"
  }' | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
for edge in data.get('data',{}).get('indicators',{}).get('edges',[]):  # 반복문 시작
    node = edge['node']
    m = re.search(r\"value\s*=\s*'([^']+)'\", node.get('pattern',''))
    if m:
        print(f\"{m.group(1)}  # {node['name']}\")
"
```

**Step 2: Suricata 로그에서 IOC 검색**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1  # 비밀번호 자동입력 SSH

# Suricata 로그에서 C2 IP 검색
echo 1 | sudo -S grep -E "203\.0\.113\.(10|11|12)" /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        print(f\"{e.get('timestamp','')} {e.get('src_ip','')} -> {e.get('dest_ip','')} {e.get('event_type','')}\")
    except: pass
" | head -20
```

**Step 3: Wazuh 로그에서 IOC 검색**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

echo 1 | sudo -S grep -E "203\.0\.113\.(10|11|12)" /var/ossec/logs/alerts/alerts.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        print(f\"{e.get('timestamp','')} [{r.get('level','')}] {r.get('description','')}\")
    except: pass
" | head -10
```

**Step 4: 결론 작성**

```bash
cat << 'EOF' > /tmp/hunting_report.txt
=== 위협 헌팅 보고서 ===
날짜: 2026-03-27
분석가: [이름]
가설: Lab-Lazarus C2 서버 통신 탐지

IOC 검색 범위:
  - 203.0.113.10, 203.0.113.11, 203.0.113.12
  - login-secure-update.example.com

검색 결과:
  - Suricata 로그: 매칭 없음
  - Wazuh 알림: 매칭 없음
  - 방화벽 로그: 매칭 없음

결론: 현재 네트워크에서 해당 IOC와 통신하는 호스트는 발견되지 않음.
권장조치: IOC를 Suricata 룰과 nftables 차단 목록에 등록하여 선제 방어.
EOF

cat /tmp/hunting_report.txt
```

---

## 6. IOC를 보안 장비에 배포

### 6.1 Suricata 룰로 변환

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1  # 비밀번호 자동입력 SSH

# OpenCTI IOC를 Suricata 룰로 변환
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
# Lab-Lazarus C2 Server Detection
alert ip $HOME_NET any -> 203.0.113.10 any (msg:"CTI - Lab-Lazarus C2 #1"; sid:9200001; rev:1; classtype:trojan-activity;)
alert ip $HOME_NET any -> 203.0.113.11 any (msg:"CTI - Lab-Lazarus C2 #2"; sid:9200002; rev:1; classtype:trojan-activity;)
alert ip $HOME_NET any -> 203.0.113.12 any (msg:"CTI - Lab-Lazarus C2 #3"; sid:9200003; rev:1; classtype:trojan-activity;)
alert dns $HOME_NET any -> any any (msg:"CTI - Lab-Lazarus Phishing Domain"; dns.query; content:"login-secure-update.example.com"; nocase; sid:9200004; rev:1; classtype:trojan-activity;)
EOF

echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

### 6.2 nftables 차단 목록으로 변환

```bash
# 악성 IP 차단
echo 1 | sudo -S nft add set inet filter cti_blocklist '{ type ipv4_addr; }'
echo 1 | sudo -S nft add element inet filter cti_blocklist \
  '{ 203.0.113.10, 203.0.113.11, 203.0.113.12 }'
echo 1 | sudo -S nft add rule inet filter input ip saddr @cti_blocklist drop
echo 1 | sudo -S nft add rule inet filter output ip daddr @cti_blocklist drop
```

### 6.3 Wazuh CDB List로 변환

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100

# CDB 리스트 생성
echo 1 | sudo -S tee /var/ossec/etc/lists/cti-malicious-ips << 'EOF'
203.0.113.10:Lazarus-C2
203.0.113.11:Lazarus-C2
203.0.113.12:Lazarus-C2
EOF

# ossec.conf에 리스트 등록
# <ruleset><list>etc/lists/cti-malicious-ips</list></ruleset>

# Wazuh 룰에서 CDB 활용
# <rule id="100050" level="12">
#   <list field="srcip" lookup="address_match_key">etc/lists/cti-malicious-ips</list>
#   <description>CTI IOC 매칭: $(srcip) - Lazarus C2</description>
# </rule>
```

---

## 7. 자동화 파이프라인

### 7.1 IOC 자동 동기화 스크립트

```bash
cat << 'PYEOF' > /tmp/sync_iocs.py
#!/usr/bin/env python3
"""OpenCTI IOC를 Suricata 룰과 nftables 차단 목록으로 동기화"""
import json, re, subprocess, requests

OPENCTI_URL = "http://10.20.30.100:9400/graphql"
OPENCTI_TOKEN = "your-api-token-here"

# 1. OpenCTI에서 IOC 가져오기
query = '{ indicators(first: 500) { edges { node { name pattern pattern_type } } } }'
resp = requests.post(OPENCTI_URL,
    headers={"Authorization": f"Bearer {OPENCTI_TOKEN}", "Content-Type": "application/json"},
    json={"query": query})

data = resp.json()
ips = []
domains = []

for edge in data.get('data',{}).get('indicators',{}).get('edges',[]):  # 반복문 시작
    pattern = edge['node'].get('pattern','')
    m_ip = re.search(r"ipv4-addr:value\s*=\s*'([^']+)'", pattern)
    m_domain = re.search(r"domain-name:value\s*=\s*'([^']+)'", pattern)
    if m_ip:
        ips.append(m_ip.group(1))
    if m_domain:
        domains.append(m_domain.group(1))

print(f"수집된 IOC: IP {len(ips)}개, Domain {len(domains)}개")

# 2. Suricata 룰 생성
sid_base = 9300000
rules = []
for i, ip in enumerate(ips):                           # 반복문 시작
    rules.append(f'alert ip $HOME_NET any -> {ip} any (msg:"CTI-AUTO - Malicious IP {ip}"; sid:{sid_base+i}; rev:1;)')
for i, dom in enumerate(domains):                      # 반복문 시작
    rules.append(f'alert dns $HOME_NET any -> any any (msg:"CTI-AUTO - Malicious Domain {dom}"; dns.query; content:"{dom}"; nocase; sid:{sid_base+len(ips)+i}; rev:1;)')

with open("/tmp/cti_auto_rules.rules", "w") as f:
    f.write("\n".join(rules))

print(f"생성된 Suricata 룰: {len(rules)}개")
print("파일: /tmp/cti_auto_rules.rules")
PYEOF

python3 /tmp/sync_iocs.py                              # Python 스크립트 실행
```

---

## 8. 실습 과제

### 과제 1: IOC 등록

1. 실습용 악성 IP 5개, 도메인 3개, 파일 해시 2개를 STIX 번들로 생성
2. OpenCTI에 업로드
3. API로 등록된 IOC를 조회하여 확인

### 과제 2: 공격 그룹 프로파일

1. 실습용 위협 행위자를 생성 (이름, 동기, 기술 수준 포함)
2. 행위자와 악성코드, 공격 기법 간의 관계를 생성
3. 웹 UI에서 관계 그래프를 확인

### 과제 3: 위협 헌팅

1. 등록한 IOC를 기반으로 Suricata/Wazuh 로그에서 매칭을 검색
2. IOC를 Suricata 룰로 변환하여 적용
3. 헌팅 결과 보고서를 작성

---

## 9. 핵심 정리

| 개념 | 설명 |
|------|------|
| IOC | 침해 지표 (IP, 도메인, 해시) |
| IOC 수명주기 | 수집 → 검증 → 등록 → 배포 → 탐지 → 만료 |
| Threat Actor | 위협 행위자 프로파일 |
| Relationship | STIX 객체 간 관계 (uses, targets) |
| Threat Hunting | 능동적 위협 탐색 |
| IOC 배포 | CTI → Suricata/nftables/Wazuh |
| CDB List | Wazuh IOC 룩업 리스트 |

---

## 다음 주 예고

Week 14에서는 모든 보안 시스템을 통합하는 아키텍처를 다룬다:
- FW → IPS → WAF → SIEM → CTI 통합
- 트래픽 흐름과 보안 계층
- 종합 모니터링

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
