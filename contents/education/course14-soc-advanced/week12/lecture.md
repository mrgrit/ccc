# Week 12: 로그 엔지니어링

## 학습 목표
- Wazuh 커스텀 디코더를 작성하여 비표준 로그를 파싱할 수 있다
- 정규표현식 기반 로그 파서를 개발할 수 있다
- 로그 정규화(normalization) 방법론을 이해하고 적용할 수 있다
- 로그 보존 정책을 수립하고 구현할 수 있다
- OpsClaw를 활용하여 다중 소스 로그 수집 파이프라인을 구축할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 로그 엔지니어링 이론 + 정규화 (Part 1) | 강의 |
| 0:50-1:30 | Wazuh 디코더 심화 (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 커스텀 디코더 작성 실습 (Part 3) | 실습 |
| 2:30-3:10 | 보존 정책 + 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **디코더** | Decoder | 로그를 파싱하여 구조화된 필드로 분리 | 외국어 통역사 |
| **파서** | Parser | 텍스트를 구문 분석하는 프로그램 | 문장 구조 분석기 |
| **정규화** | Normalization | 다양한 포맷의 로그를 통일된 형식으로 변환 | 도량형 통일 |
| **정규표현식** | Regular Expression (regex) | 문자열 패턴 매칭 언어 | 만능 검색 도구 |
| **syslog** | Syslog | 시스템 로그 전송 표준 프로토콜 | 보고서 전달 시스템 |
| **CEF** | Common Event Format | ArcSight의 이벤트 로그 형식 | 표준 보고서 양식 |
| **ECS** | Elastic Common Schema | Elastic의 표준 필드 스키마 | 표준 데이터베이스 구조 |
| **로그 로테이션** | Log Rotation | 오래된 로그를 압축/삭제하는 관리 | 문서 보관/폐기 |
| **보존 정책** | Retention Policy | 로그 보관 기간/방법 규정 | 서류 보관 기한 규정 |

---

# Part 1: 로그 엔지니어링 이론 + 정규화 (50분)

## 1.1 로그 엔지니어링이란?

로그 엔지니어링은 **다양한 소스에서 생성되는 로그를 수집, 파싱, 정규화, 저장, 분석 가능한 형태로 가공**하는 기술이다.

```
[로그 엔지니어링 파이프라인]

소스            수집          파싱          정규화        저장/분석
+-------+     +------+     +------+     +-------+     +-------+
|syslog | --> |rsyslog| --> |decoder| --> |정규화  | --> |Wazuh  |
|Apache | --> |agent  | --> |parser | --> |필드통일| --> |ES     |
|Suricata| -> |filebeat|    |regex  |     |시간통일| --> |분석   |
|nftables| -> |        |    |       |     |        |     |       |
+-------+     +------+     +------+     +-------+     +-------+
```

## 1.2 로그 포맷 비교

```
[Apache Access Log]
10.20.30.201 - - [04/Apr/2026:10:15:23 +0900] "GET /api/test HTTP/1.1" 200 1234

[Suricata EVE JSON]
{"timestamp":"2026-04-04T10:15:23.456+0900","event_type":"alert",
 "src_ip":"10.20.30.201","dest_ip":"10.20.30.80","alert":{"signature":"ET SCAN"}}

[auth.log]
Apr  4 10:15:23 web sshd[12345]: Failed password for root from 10.20.30.201 port 54321

[nftables log]
Apr  4 10:15:23 secu kernel: nft_log: IN=eth0 SRC=10.20.30.201 DST=10.20.30.80 PROTO=TCP DPT=80

→ 4개의 서로 다른 포맷을 통일된 구조로 정규화해야 함
```

## 1.3 Wazuh 디코더 구조

```xml
<!-- 디코더 기본 구조 -->
<decoder name="custom_app">
  <prematch>^custom_app:</prematch>         <!-- 1차 필터 -->
</decoder>

<decoder name="custom_app_detail">
  <parent>custom_app</parent>                <!-- 부모 디코더 -->
  <regex>user=(\S+) action=(\S+) ip=(\S+)</regex>  <!-- 필드 추출 -->
  <order>user, action, srcip</order>         <!-- 필드 이름 매핑 -->
</decoder>
```

### 디코더 필드 타입

| 필드 | 설명 | 예시 |
|------|------|------|
| `srcip` | 출발지 IP | 10.20.30.201 |
| `dstip` | 목적지 IP | 10.20.30.80 |
| `srcuser` | 사용자명 | root |
| `dstuser` | 대상 사용자 | admin |
| `srcport` | 출발지 포트 | 54321 |
| `dstport` | 목적지 포트 | 80 |
| `protocol` | 프로토콜 | TCP |
| `action` | 수행 동작 | login_failed |
| `status` | 상태 | success/failure |
| `extra_data` | 추가 데이터 | 자유 형식 |

---

# Part 2: Wazuh 디코더 심화 (40분)

## 2.1 기존 디코더 분석

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'
echo "=== Wazuh 기본 디코더 수 ==="
find /var/ossec/ruleset/decoders/ -name "*.xml" | wc -l

echo ""
echo "=== SSH 디코더 예시 ==="
grep -A5 "decoder name=\"sshd\"" /var/ossec/ruleset/decoders/0310-ssh_decoders.xml 2>/dev/null | head -20

echo ""
echo "=== Apache 디코더 예시 ==="
grep -A5 "decoder name=\"apache\"" /var/ossec/ruleset/decoders/0025-apache_decoders.xml 2>/dev/null | head -20

echo ""
echo "=== 커스텀 디코더 ==="
cat /var/ossec/etc/decoders/local_decoder.xml 2>/dev/null || echo "(커스텀 디코더 없음)"
REMOTE
```

## 2.2 정규표현식 핵심 패턴

```bash
cat << 'SCRIPT' > /tmp/regex_patterns.py
#!/usr/bin/env python3
"""로그 파싱을 위한 정규표현식 핵심 패턴"""
import re

patterns = {
    "IP 주소": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "포트 번호": r":(\d{1,5})\b",
    "타임스탬프 (syslog)": r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
    "타임스탬프 (ISO)": r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
    "타임스탬프 (Apache)": r"\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4})\]",
    "HTTP 메서드": r"\"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s",
    "HTTP 상태코드": r"\"\s(\d{3})\s",
    "이메일": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "MAC 주소": r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}",
    "사용자명 (SSH)": r"for\s+(invalid\s+user\s+)?(\S+)\s+from",
    "PID": r"\[(\d+)\]:",
}

# 테스트 로그
test_logs = [
    'Apr  4 10:15:23 web sshd[12345]: Failed password for root from 10.20.30.201 port 54321 ssh2',
    '10.20.30.201 - - [04/Apr/2026:10:15:23 +0900] "GET /api/test HTTP/1.1" 200 1234',
    '{"timestamp":"2026-04-04T10:15:23","src_ip":"10.20.30.201","alert":{"signature":"ET SCAN"}}',
]

print("=" * 60)
print("  로그 파싱 정규표현식 패턴")
print("=" * 60)

for name, pattern in patterns.items():
    print(f"\n  {name}:")
    print(f"    패턴: {pattern}")

print("\n" + "=" * 60)
print("  테스트 로그 파싱 결과")
print("=" * 60)

for log in test_logs:
    print(f"\n  로그: {log[:60]}...")
    ips = re.findall(patterns["IP 주소"], log)
    if ips:
        print(f"    IP: {ips}")
    ts_syslog = re.findall(patterns["타임스탬프 (syslog)"], log)
    if ts_syslog:
        print(f"    시각: {ts_syslog}")
    user = re.findall(patterns["사용자명 (SSH)"], log)
    if user:
        print(f"    사용자: {user}")
SCRIPT

python3 /tmp/regex_patterns.py
```

---

# Part 3: 커스텀 디코더 작성 실습 (50분)

## 3.1 OpsClaw 로그용 커스텀 디코더

> **실습 목적**: OpsClaw API 로그를 Wazuh에서 파싱하는 커스텀 디코더를 작성한다.

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# OpsClaw 로그 디코더 작성
sudo tee /var/ossec/etc/decoders/local_decoder.xml << 'DECODERS'
<!-- OpsClaw Manager API 로그 디코더 -->
<decoder name="opsclaw">
  <prematch>^opsclaw-manager:</prematch>
</decoder>

<decoder name="opsclaw_api">
  <parent>opsclaw</parent>
  <regex>user=(\S+) method=(\S+) path=(\S+) status=(\d+) ip=(\S+)</regex>
  <order>srcuser, action, url, status, srcip</order>
</decoder>

<!-- Suricata EVE JSON 커스텀 디코더 -->
<decoder name="suricata_custom">
  <prematch>^suricata_alert:</prematch>
</decoder>

<decoder name="suricata_custom_detail">
  <parent>suricata_custom</parent>
  <regex>src=(\S+) dst=(\S+) sig="([^"]+)" severity=(\d+)</regex>
  <order>srcip, dstip, extra_data, status</order>
</decoder>

<!-- nftables 로그 디코더 -->
<decoder name="nftables_custom">
  <prematch>^nft_log:</prematch>
</decoder>

<decoder name="nftables_custom_detail">
  <parent>nftables_custom</parent>
  <regex>IN=(\S+) SRC=(\S+) DST=(\S+) \.+PROTO=(\S+) \.+DPT=(\d+)</regex>
  <order>extra_data, srcip, dstip, protocol, dstport</order>
</decoder>

<!-- 커스텀 애플리케이션 로그 디코더 -->
<decoder name="custom_app">
  <prematch>^\[APP\]</prematch>
</decoder>

<decoder name="custom_app_detail">
  <parent>custom_app</parent>
  <regex>level=(\S+) user=(\S+) action=(\S+) resource=(\S+) result=(\S+)</regex>
  <order>status, srcuser, action, url, extra_data</order>
</decoder>
DECODERS

# 디코더 문법 검사
sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

> **명령어 해설**:
> - `<prematch>`: 로그의 첫 부분을 매칭하여 해당 디코더를 선택
> - `<parent>`: 부모 디코더가 매칭된 후에만 이 디코더 적용
> - `<regex>`: 괄호 그룹으로 필드 값 추출
> - `<order>`: 추출된 값을 Wazuh 필드에 매핑

## 3.2 wazuh-logtest로 디코더 검증

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# 테스트 로그로 디코더 검증
echo "=== OpsClaw 로그 테스트 ==="
echo 'opsclaw-manager: user=admin method=POST path=/projects status=201 ip=10.20.30.201' | \
  sudo /var/ossec/bin/wazuh-logtest -q 2>/dev/null | tail -15

echo ""
echo "=== nftables 로그 테스트 ==="
echo 'nft_log: IN=eth0 SRC=203.0.113.50 DST=10.20.30.80 LEN=60 PROTO=TCP SPT=54321 DPT=80' | \
  sudo /var/ossec/bin/wazuh-logtest -q 2>/dev/null | tail -15

echo ""
echo "=== 커스텀 앱 로그 테스트 ==="
echo '[APP] level=ERROR user=admin action=delete resource=/etc/passwd result=denied' | \
  sudo /var/ossec/bin/wazuh-logtest -q 2>/dev/null | tail -15

REMOTE
```

> **결과 해석**: "decoder" 항목에 커스텀 디코더 이름이 표시되면 파싱 성공이다. "srcip", "srcuser" 등의 필드에 올바른 값이 들어가는지 확인한다.

## 3.3 다중 소스 로그 정규화

```bash
cat << 'SCRIPT' > /tmp/log_normalizer.py
#!/usr/bin/env python3
"""다중 소스 로그 정규화"""
import re
import json
from datetime import datetime

def normalize_syslog(line):
    """syslog 형식 정규화"""
    match = re.match(
        r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?:\s+(.*)',
        line
    )
    if match:
        return {
            "timestamp": match.group(1),
            "hostname": match.group(2),
            "program": match.group(3),
            "pid": match.group(4),
            "message": match.group(5),
            "source_type": "syslog",
        }
    return None

def normalize_apache(line):
    """Apache access log 정규화"""
    match = re.match(
        r'(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\d+)',
        line
    )
    if match:
        return {
            "src_ip": match.group(1),
            "timestamp": match.group(2),
            "method": match.group(3),
            "uri": match.group(4),
            "status_code": int(match.group(5)),
            "bytes": int(match.group(6)),
            "source_type": "apache_access",
        }
    return None

# 테스트
logs = [
    'Apr  4 10:15:23 web sshd[12345]: Failed password for root from 10.20.30.201 port 54321 ssh2',
    '10.20.30.201 - - [04/Apr/2026:10:15:23 +0900] "GET /api/test HTTP/1.1" 200 1234',
]

print("=" * 60)
print("  로그 정규화 결과")
print("=" * 60)

for log in logs:
    result = normalize_syslog(log) or normalize_apache(log)
    if result:
        print(f"\n원본: {log[:60]}...")
        print(f"정규화: {json.dumps(result, indent=2, ensure_ascii=False)}")
SCRIPT

python3 /tmp/log_normalizer.py
```

---

# Part 4: 보존 정책 + 자동화 (40분)

## 4.1 로그 보존 정책 수립

```bash
cat << 'SCRIPT' > /tmp/retention_policy.py
#!/usr/bin/env python3
"""로그 보존 정책"""

policy = {
    "보안 경보 (Wazuh alerts)": {"보존": "1년", "압축": "30일 후", "근거": "개인정보보호법"},
    "접근 로그 (auth.log)": {"보존": "6개월", "압축": "7일 후", "근거": "정보통신망법"},
    "웹 접근 로그": {"보존": "6개월", "압축": "7일 후", "근거": "개인정보보호법"},
    "방화벽 로그": {"보존": "1년", "압축": "30일 후", "근거": "정보통신망법"},
    "IDS/IPS 로그": {"보존": "1년", "압축": "30일 후", "근거": "보안 감사"},
    "시스템 로그 (syslog)": {"보존": "3개월", "압축": "7일 후", "근거": "운영"},
    "애플리케이션 로그": {"보존": "3개월", "압축": "7일 후", "근거": "운영"},
    "DNS 쿼리 로그": {"보존": "3개월", "압축": "7일 후", "근거": "위협 헌팅"},
}

print("=" * 70)
print("  로그 보존 정책")
print("=" * 70)
print(f"\n{'로그 유형':25s} {'보존':>8s} {'압축':>10s} {'근거':>15s}")
print("-" * 65)

for log_type, info in policy.items():
    print(f"{log_type:25s} {info['보존']:>8s} {info['압축']:>10s} {info['근거']:>15s}")
SCRIPT

python3 /tmp/retention_policy.py
```

## 4.2 로그 로테이션 구성

```bash
# Wazuh 로그 로테이션 확인
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'
echo "=== Wazuh 로그 크기 ==="
du -sh /var/ossec/logs/ 2>/dev/null
du -sh /var/ossec/logs/alerts/ 2>/dev/null

echo ""
echo "=== logrotate 설정 ==="
cat /etc/logrotate.d/wazuh-manager 2>/dev/null || echo "(wazuh logrotate 없음)"

echo ""
echo "=== 로그 파일 목록 ==="
ls -lh /var/ossec/logs/alerts/ 2>/dev/null | tail -10
REMOTE
```

## 4.3 OpsClaw로 로그 수집 자동화

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "log-engineering-audit",
    "request_text": "전체 서버 로그 수집 상태 감사",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "du -sh /var/log/ 2>/dev/null && ls /var/log/*.log 2>/dev/null | wc -l && echo LOG_AUDIT_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "du -sh /var/log/ 2>/dev/null && ls /var/log/*.log 2>/dev/null | wc -l && echo LOG_AUDIT_DONE",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "du -sh /var/ossec/logs/ 2>/dev/null && echo WAZUH_LOG_AUDIT",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 체크리스트

- [ ] Wazuh 디코더의 prematch, parent, regex, order 구조를 설명할 수 있다
- [ ] 정규표현식으로 IP, 타임스탬프, 사용자명을 추출할 수 있다
- [ ] 커스텀 디코더를 작성하고 wazuh-logtest로 검증할 수 있다
- [ ] 다중 소스 로그를 통일된 형식으로 정규화할 수 있다
- [ ] 로그 보존 정책의 법적 근거를 이해한다
- [ ] logrotate 설정을 확인하고 수정할 수 있다
- [ ] syslog, Apache, JSON 등 주요 로그 포맷을 파싱할 수 있다
- [ ] Wazuh의 디코더→룰 파이프라인을 이해한다
- [ ] OpsClaw로 다중 서버 로그 상태를 감사할 수 있다
- [ ] 로그 수집 누락을 진단하고 해결할 수 있다

---

## 복습 퀴즈

**Q1.** Wazuh 디코더에서 prematch와 regex의 차이는?

<details><summary>정답</summary>
prematch는 로그의 시작 부분을 매칭하여 이 디코더를 적용할지 결정하는 1차 필터다. regex는 prematch를 통과한 로그에서 실제 필드 값을 추출하는 패턴이다.
</details>

**Q2.** parent 디코더가 필요한 이유는?

<details><summary>정답</summary>
로그 파싱을 단계적으로 수행하기 위해서다. 부모 디코더가 로그 유형을 식별하고, 자식 디코더가 세부 필드를 추출한다. 이렇게 하면 디코더를 모듈화하고 성능을 최적화할 수 있다.
</details>

**Q3.** 로그 정규화가 필요한 이유는?

<details><summary>정답</summary>
서로 다른 소스(Apache, sshd, nftables)의 로그가 각기 다른 포맷이므로, 통일된 필드명과 형식으로 변환해야 SIEM에서 상관분석이 가능하다. 예: src_ip 필드가 소스마다 다른 위치/형식에 있으면 상관 룰이 동작하지 않는다.
</details>

**Q4.** 한국의 개인정보보호법에 따른 접근 로그 최소 보존 기간은?

<details><summary>정답</summary>
최소 6개월이다. 개인정보의 안전성 확보조치 기준에 따라 개인정보처리시스템의 접속기록을 최소 6개월(5만명 이상 정보주체인 경우 1년) 이상 보관해야 한다.
</details>

**Q5.** wazuh-logtest의 용도를 설명하시오.

<details><summary>정답</summary>
테스트 로그를 입력하면 어떤 디코더가 매칭되고, 어떤 필드가 추출되며, 어떤 룰이 적용되는지 확인할 수 있는 디버깅 도구다. 새 디코더/룰 작성 후 실서비스 적용 전 반드시 검증해야 한다.
</details>

**Q6.** 정규표현식 `(\S+)`와 `(.+)`의 차이는?

<details><summary>정답</summary>
`(\S+)`는 공백이 아닌 문자를 1개 이상 매칭(단어 단위). `(.+)`는 모든 문자를 1개 이상 매칭(줄 끝까지). `\S+`가 필드 추출에 더 정확하고, `.+`는 과도하게 매칭할 수 있다.
</details>

**Q7.** 로그 로테이션에서 compress 옵션의 역할은?

<details><summary>정답</summary>
오래된 로그 파일을 gzip으로 압축하여 디스크 공간을 절약한다. 보통 rotate 후 1세대 이전 파일부터 압축한다(delaycompress 옵션).
</details>

**Q8.** CEF(Common Event Format)의 장점은?

<details><summary>정답</summary>
보안 벤더 간 로그 형식을 표준화하여 SIEM 연동을 단순화한다. key=value 형식으로 파싱이 쉽고, 확장 필드로 유연성도 보장한다.
</details>

**Q9.** 로그 수집이 누락되는 일반적 원인 3가지는?

<details><summary>정답</summary>
1) Wazuh 에이전트 미설치 또는 비활성, 2) rsyslog/syslog 전송 설정 오류, 3) 방화벽에서 syslog 포트(514) 차단. 추가로 로그 파일 권한 문제, 디스크 용량 부족도 원인이 된다.
</details>

**Q10.** OpsClaw로 로그 감사를 자동화하는 이점은?

<details><summary>정답</summary>
여러 서버의 로그 수집 상태를 동시에 점검하고, 누락/이상을 중앙에서 파악할 수 있다. 주기적으로 실행하면 로그 수집 문제를 조기에 발견하여 탐지 사각지대를 방지한다.
</details>

---

## 과제

### 과제 1: 커스텀 디코더 3개 작성 (필수)

다음 로그 형식에 대한 Wazuh 커스텀 디코더를 작성하라:
1. OpsClaw dispatch 로그
2. JuiceShop 애플리케이션 로그
3. 커스텀 보안 감사 로그

각 디코더에 wazuh-logtest 검증 결과를 포함하라.

### 과제 2: 로그 보존 정책서 (선택)

실습 환경에 대한 로그 보존 정책서를 작성하라:
1. 로그 유형별 보존 기간 (법적 근거 포함)
2. 로테이션 설정
3. 저장 용량 계산
4. 백업 절차

---

## 보충: 로그 엔지니어링 고급 기법

### 고급 정규표현식 패턴

```bash
cat << 'SCRIPT' > /tmp/advanced_regex.py
#!/usr/bin/env python3
"""로그 파싱을 위한 고급 정규표현식"""
import re

# 고급 패턴
advanced_patterns = {
    "Named Groups": {
        "pattern": r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<program>\S+?)(?:\[(?P<pid>\d+)\])?:\s+(?P<message>.*)",
        "test": "Apr  4 10:15:23 web sshd[12345]: Failed password for root from 10.20.30.201",
        "description": "명명된 그룹으로 필드 추출",
    },
    "Lookahead": {
        "pattern": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?=:\d{1,5})",
        "test": "Connection from 10.20.30.201:54321 to 10.20.30.100:22",
        "description": "포트가 뒤따르는 IP만 매칭 (포트 제외)",
    },
    "Lookbehind": {
        "pattern": r"(?<=from\s)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
        "test": "Failed password for root from 10.20.30.201 port 54321",
        "description": "'from' 뒤의 IP만 매칭",
    },
    "Non-greedy": {
        "pattern": r'"(.*?)"',
        "test": '"GET /api/test HTTP/1.1" 200 1234 "Mozilla/5.0"',
        "description": "따옴표 내 최소 매칭",
    },
    "Conditional": {
        "pattern": r"(Failed|Accepted)\s+password\s+for\s+(invalid\s+user\s+)?(\S+)",
        "test": "Failed password for invalid user admin from 10.20.30.201",
        "description": "성공/실패 + 유효/무효 사용자 동시 처리",
    },
}

print("=" * 70)
print("  고급 정규표현식 패턴 가이드")
print("=" * 70)

for name, info in advanced_patterns.items():
    print(f"\n  --- {name} ---")
    print(f"  설명: {info['description']}")
    print(f"  패턴: {info['pattern'][:60]}")
    print(f"  테스트: {info['test'][:60]}")
    
    match = re.search(info['pattern'], info['test'])
    if match:
        if match.groupdict():
            print(f"  결과: {match.groupdict()}")
        else:
            print(f"  결과: {match.group(0)}")
    else:
        print(f"  결과: (매칭 없음)")
SCRIPT

python3 /tmp/advanced_regex.py
```

### 로그 수집 파이프라인 아키텍처

```bash
cat << 'SCRIPT' > /tmp/log_pipeline.py
#!/usr/bin/env python3
"""로그 수집 파이프라인 아키텍처"""

print("""
================================================================
  로그 수집 파이프라인 아키텍처
================================================================

[수집 계층]
+--------+   +--------+   +--------+   +--------+
| rsyslog|   | Wazuh  |   | filebeat|  | fluentd|
| (syslog|   | Agent  |   | (파일) |   | (범용) |
|  514)  |   | (1514) |   |        |   |        |
+---+----+   +---+----+   +---+----+   +---+----+
    |             |             |             |
    v             v             v             v
+---------------------------------------------------+
|              로그 버퍼 / 큐                        |
|  (Kafka, Redis, Wazuh Manager)                    |
+---------------------------------------------------+
    |
    v
+---------------------------------------------------+
|              파싱 / 정규화                         |
|  (Wazuh Decoder, Logstash, Fluentd)              |
+---------------------------------------------------+
    |
    v
+---------------------------------------------------+
|              저장 / 인덱싱                         |
|  (Elasticsearch, Wazuh Indexer)                   |
+---------------------------------------------------+
    |
    v
+---------------------------------------------------+
|              분석 / 시각화                         |
|  (Wazuh Dashboard, Kibana, Grafana)              |
+---------------------------------------------------+

성능 지표:
  - EPS (Events Per Second): 초당 이벤트 처리량
  - 권장: 소규모 SOC 1,000 EPS, 중규모 10,000 EPS
  - 지연: 수집~분석 1초 이내 권장
  - 저장: 1,000 EPS x 86,400초 = 86.4M 이벤트/일
""")
SCRIPT

python3 /tmp/log_pipeline.py
```

### syslog 심화 설정

```bash
echo "=== syslog 심화 설정 가이드 ==="

cat << 'INFO'
# rsyslog에서 원격 로그 수집 (UDP/TCP)

# 1. UDP 수신 활성화 (/etc/rsyslog.conf)
module(load="imudp")
input(type="imudp" port="514")

# 2. TCP 수신 활성화 (더 안정적)
module(load="imtcp")
input(type="imtcp" port="514")

# 3. 소스별 분리 저장
template(name="RemoteLog" type="string"
  string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
*.* ?RemoteLog

# 4. JSON 형식 출력 (SIEM 연동용)
template(name="JsonFormat" type="list") {
  constant(value="{")
  property(name="timestamp" format="jsonf")
  constant(value=",")
  property(name="hostname" format="jsonf")
  constant(value=",")
  property(name="syslogtag" format="jsonf")
  constant(value=",")
  property(name="msg" format="jsonf")
  constant(value="}\n")
}

# 5. 소스 IP 기반 필터링
if $fromhost-ip == '10.20.30.80' then /var/log/web_server.log

# 6. Wazuh로 전달
*.* @@10.20.30.100:1514   # TCP 전달
*.* @10.20.30.100:514     # UDP 전달
INFO
```

### 로그 품질 점검 자동화

```bash
cat << 'SCRIPT' > /tmp/log_quality_check.py
#!/usr/bin/env python3
"""로그 품질 점검 자동화"""
from datetime import datetime

checks = [
    {
        "항목": "로그 수집 연속성",
        "기준": "모든 소스에서 최근 5분 내 로그 존재",
        "방법": "각 소스의 마지막 로그 타임스탬프 확인",
        "명령": "tail -1 /var/log/<source>.log | awk '{print $1,$2,$3}'",
    },
    {
        "항목": "로그 형식 일관성",
        "기준": "파싱 실패율 1% 미만",
        "방법": "Wazuh 디코더 미매칭 로그 수 확인",
        "명령": "grep 'decoder:' /var/ossec/logs/alerts/alerts.json | grep -c 'unknown'",
    },
    {
        "항목": "타임스탬프 동기화",
        "기준": "서버 간 시각 차이 1초 미만",
        "방법": "NTP 상태 확인",
        "명령": "timedatectl status | grep 'synchronized'",
    },
    {
        "항목": "로그 무결성",
        "기준": "로그 파일 변조 없음",
        "방법": "Wazuh FIM으로 로그 파일 모니터링",
        "명령": "grep 'syscheck' /var/ossec/logs/alerts/alerts.log | grep '/var/log'",
    },
    {
        "항목": "저장 용량",
        "기준": "디스크 사용률 80% 미만",
        "방법": "로그 파티션 사용량 확인",
        "명령": "df -h /var/log/ | awk 'NR==2{print $5}'",
    },
    {
        "항목": "로테이션 정상",
        "기준": "최근 7일 내 로테이션 실행됨",
        "방법": "로테이션 로그 확인",
        "명령": "grep 'logrotate' /var/log/syslog | tail -1",
    },
]

print("=" * 60)
print("  로그 품질 점검 체크리스트")
print("=" * 60)

for check in checks:
    print(f"\n  --- {check['항목']} ---")
    print(f"    기준: {check['기준']}")
    print(f"    방법: {check['방법']}")
    print(f"    명령: {check['명령']}")
SCRIPT

python3 /tmp/log_quality_check.py
```

### 로그 파이프라인 성능 모니터링

```bash
cat << 'SCRIPT' > /tmp/log_pipeline_monitor.py
#!/usr/bin/env python3
"""로그 파이프라인 성능 모니터링"""

print("=" * 60)
print("  로그 파이프라인 성능 모니터링")
print("=" * 60)

metrics = {
    "수집 계층": {
        "EPS (Events/sec)": "1,200",
        "지연 시간": "< 1초",
        "손실률": "0.01%",
        "모니터링": "wazuh-analysisd.state 파일",
    },
    "파싱 계층": {
        "파싱 성공률": "99.2%",
        "디코더 미매칭": "0.8%",
        "평균 파싱 시간": "0.5ms/이벤트",
        "모니터링": "디코더 미매칭 로그 카운트",
    },
    "저장 계층": {
        "인덱싱 속도": "800 docs/sec",
        "디스크 사용": "12GB/일",
        "쿼리 응답": "< 2초",
        "모니터링": "Elasticsearch _cluster/health",
    },
    "분석 계층": {
        "룰 매칭 속도": "50,000 룰/sec",
        "경보 생성": "45/분",
        "Active Response": "< 5초",
        "모니터링": "alerts/min 추세",
    },
}

for layer, data in metrics.items():
    print(f"\n  [{layer}]")
    for metric, value in data.items():
        print(f"    {metric:20s}: {value}")

print("""
=== 성능 임계치 경보 ===
  EPS > 5,000: 파싱 지연 가능 → 스케일 아웃 검토
  파싱 실패 > 5%: 디코더 추가 필요
  디스크 사용 > 80%: 로테이션/보존 정책 조정
  쿼리 응답 > 10초: 인덱스 최적화 필요
""")
SCRIPT

python3 /tmp/log_pipeline_monitor.py
```

### ECS(Elastic Common Schema) 정규화

```bash
cat << 'SCRIPT' > /tmp/ecs_normalization.py
#!/usr/bin/env python3
"""ECS(Elastic Common Schema) 정규화 예시"""
import json

# 원본 로그
raw_logs = [
    {
        "source": "sshd",
        "raw": "Apr  4 10:15:23 web sshd[12345]: Failed password for root from 10.20.30.201 port 54321",
    },
    {
        "source": "apache",
        "raw": '10.20.30.201 - - [04/Apr/2026:10:15:23 +0900] "GET /api/test HTTP/1.1" 200 1234',
    },
]

# ECS 정규화 결과
ecs_events = [
    {
        "@timestamp": "2026-04-04T10:15:23.000+09:00",
        "event": {"category": "authentication", "type": "start", "outcome": "failure"},
        "source": {"ip": "10.20.30.201", "port": 54321},
        "destination": {"ip": "10.20.30.80"},
        "user": {"name": "root"},
        "process": {"name": "sshd", "pid": 12345},
        "host": {"name": "web"},
        "ecs": {"version": "8.0"},
    },
    {
        "@timestamp": "2026-04-04T10:15:23.000+09:00",
        "event": {"category": "web", "type": "access", "outcome": "success"},
        "source": {"ip": "10.20.30.201"},
        "http": {"request": {"method": "GET"}, "response": {"status_code": 200, "bytes": 1234}},
        "url": {"path": "/api/test"},
        "host": {"name": "web"},
        "ecs": {"version": "8.0"},
    },
]

print("=" * 60)
print("  ECS 정규화 예시")
print("=" * 60)

for raw, ecs in zip(raw_logs, ecs_events):
    print(f"\n원본 ({raw['source']}):")
    print(f"  {raw['raw'][:70]}")
    print(f"\nECS 정규화:")
    print(f"  {json.dumps(ecs, indent=2, ensure_ascii=False)[:300]}")
SCRIPT

python3 /tmp/ecs_normalization.py
```

### Wazuh 디코더 디버깅 기법

```bash
echo "=== Wazuh 디코더 디버깅 기법 ==="

cat << 'INFO'
1. wazuh-logtest 단계별 분석

   # 테스트 모드 실행
   echo 'test log line' | /var/ossec/bin/wazuh-logtest -q
   
   출력 해석:
   - "decoder": 어떤 디코더가 매칭되었는가
   - "rule": 어떤 룰이 매칭되었는가
   - "srcip": IP가 올바르게 추출되었는가
   - "srcuser": 사용자명이 올바르게 추출되었는가

2. 디코더 매칭 안 될 때 체크리스트

   [ ] prematch가 로그 시작 부분과 일치하는가?
   [ ] parent 디코더가 먼저 매칭되는가?
   [ ] regex의 그룹 수와 order의 필드 수가 일치하는가?
   [ ] 특수문자가 올바르게 이스케이프되었는가?
   [ ] XML 태그가 올바르게 닫혔는가?

3. 흔한 실수

   실수: <regex>user=(.+) ip=(.+)</regex>
   문제: .+는 greedy하여 첫 그룹이 모든 것을 매칭
   해결: <regex>user=(\S+) ip=(\S+)</regex>
         (\S+는 공백이 아닌 문자만 매칭)

   실수: <prematch>error</prematch>
   문제: 로그 어디에나 있는 error와 매칭
   해결: <prematch>^myapp: error</prematch>
         (^로 시작 위치 고정)

4. 성능 최적화

   - prematch를 가능한 구체적으로
   - regex에서 .* 대신 \S+ 사용
   - 불필요한 캡처 그룹 제거
   - parent 디코더로 계층화
INFO
```

---

## 다음 주 예고

**Week 13: 레드팀 연동**에서는 Purple Team 운영, 탐지 격차 분석, 룰 개선 방법을 학습한다.
