# Week 09: Wazuh SIEM (1) — 설치와 구성

## 학습 목표
- SIEM의 역할과 필요성을 이해한다
- Wazuh의 Manager/Agent 아키텍처를 파악한다
- Wazuh 대시보드의 기본 기능을 사용할 수 있다
- Agent를 등록하고 연결 상태를 확인할 수 있다

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

# Week 09: Wazuh SIEM (1) — 설치와 구성

## 학습 목표

- SIEM의 역할과 필요성을 이해한다
- Wazuh의 Manager/Agent 아키텍처를 파악한다
- Wazuh 대시보드의 기본 기능을 사용할 수 있다
- Agent를 등록하고 연결 상태를 확인할 수 있다

---

## 1. SIEM이란?

SIEM(Security Information and Event Management)은 보안 이벤트를 **수집, 분석, 상관분석, 시각화**하는 통합 보안 관제 플랫폼이다.

### 1.1 SIEM의 핵심 기능

| 기능 | 설명 |
|------|------|
| 로그 수집 | 다양한 소스에서 로그를 중앙 집중 수집 |
| 정규화 | 서로 다른 형식의 로그를 통일된 형식으로 변환 |
| 상관분석 | 여러 이벤트를 연결하여 위협 식별 |
| 알림 | 위협 탐지 시 알림 발생 |
| 대시보드 | 보안 상태 시각화 |
| 컴플라이언스 | PCI-DSS, GDPR 등 규정 준수 보고 |

### 1.2 왜 SIEM이 필요한가?

```
방화벽 로그   --+
IPS 로그     --+
WAF 로그     --+--> [SIEM] --> 종합 분석 --> 위협 탐지
서버 로그    --+                상관분석      알림
인증 로그    --+                대시보드      보고서
```

개별 장비의 로그만으로는 전체 그림을 볼 수 없다. SIEM이 모든 로그를 모아서 **상관분석**한다.

---

## 2. Wazuh 아키텍처

Wazuh 4.11.2는 3개 컴포넌트로 구성된다:

```
[Wazuh Dashboard]
  웹 UI, Kibana 기반
  https://10.20.30.100
       |
       v
[Wazuh Indexer]
  로그 저장, OpenSearch 기반
  :9200
       |
       v
[Wazuh Manager]
  분석 엔진, 룰 처리
  :1514 (agent), :1515 (register), :55000 (API)
       |
       +----------+----------+
       |          |          |
       v          v          v
  [Agent 1]  [Agent 2]  [Agent 3]
    secu       web        siem
```

| 컴포넌트 | 역할 | 포트 |
|----------|------|------|
| Manager | 이벤트 분석, 룰 매칭, Agent 관리 | 1514, 1515, 55000 |
| Indexer | 이벤트 저장, 검색 (OpenSearch) | 9200 |
| Dashboard | 웹 UI (시각화, 관리) | 443 |
| Agent | 호스트에서 로그 수집, 전송 | (아웃바운드) |

---

## 3. 실습 환경 접속

> **이 실습을 왜 하는가?**
> SIEM(Security Information and Event Management)은 보안 관제의 **중추 신경계**이다.
> 모든 서버의 로그를 수집하고, 알려진 공격 패턴과 매칭하여 경보를 발생시킨다.
> Wazuh는 오픈소스 SIEM 중 가장 널리 사용되며, OSSEC에서 발전한 제품이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - Wazuh의 4개 컴포넌트(Manager/Indexer/Dashboard/Agent)의 역할
> - SIEM이 실제로 어떤 디렉토리 구조와 설정 파일을 사용하는지
> - 에이전트가 어떻게 연결되고, 로그가 어떻게 분석되는지
>
> **실무 활용:**
> - SOC 구축 시 SIEM 플랫폼 선정 및 설치
> - 에이전트 배포/관리
> - 커스텀 탐지 룰 작성 (W10에서 심화)
>
> **검증 완료:** siem 서버에서 Wazuh Manager v4.11.2 active, Agent 1개(자체 server) 확인

### 3.1 siem 서버 접속

> **실습 목적**: siem 서버에서 Wazuh SIEM의 설치 상태와 에이전트 연결을 확인한다
>
> **배우는 것**: Wazuh Manager 서비스 상태, 에이전트 등록/연결, 기본 알림 구조를 이해한다
>
> **결과 해석**: Manager가 active이고 에이전트가 connected 상태이면 SIEM이 정상 수집 중이다
>
> **실전 활용**: SOC 구축 시 SIEM 플랫폼 설치와 에이전트 배포가 첫 번째 단계이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100
```

### 3.2 Wazuh 서비스 상태 확인

```bash
echo 1 | sudo -S systemctl status wazuh-manager
```

**예상 출력:**
```
● wazuh-manager.service - Wazuh manager
     Loaded: loaded (/lib/systemd/system/wazuh-manager.service; enabled; ...)
     Active: active (running) since ...
```

```bash
echo 1 | sudo -S systemctl status wazuh-indexer
echo 1 | sudo -S systemctl status wazuh-dashboard
```

### 3.3 Wazuh 버전 확인

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-control info
```

**예상 출력:**
```
WAZUH_VERSION="v4.11.2"
WAZUH_REVISION="40112"
WAZUH_TYPE="server"
```

---

## 4. 핵심 디렉터리 구조

```bash
echo 1 | sudo -S ls /var/ossec/
```

| 디렉터리 | 설명 |
|----------|------|
| `/var/ossec/etc/` | 설정 파일 (ossec.conf) |
| `/var/ossec/rules/` | 탐지 룰 |
| `/var/ossec/decoders/` | 로그 디코더 |
| `/var/ossec/logs/` | Wazuh 로그 |
| `/var/ossec/logs/alerts/` | 알림 로그 |
| `/var/ossec/bin/` | 실행 파일 |
| `/var/ossec/queue/` | 큐 디렉터리 |

---

## 5. 핵심 설정 파일 (ossec.conf)

### 5.1 설정 파일 확인

```bash
echo 1 | sudo -S cat /var/ossec/etc/ossec.conf | head -50
```

### 5.2 주요 설정 항목

**로그 수집 설정:**

```xml
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
  <location>/var/log/apache2/access.log</location>
</localfile>
```

**Agent 연결 설정 (Manager측):**

```xml
<remote>
  <connection>secure</connection>
  <port>1514</port>
  <protocol>tcp</protocol>
</remote>
```

**알림 설정:**

```xml
<alerts>
  <log_alert_level>3</log_alert_level>
  <email_alert_level>12</email_alert_level>
</alerts>
```

> `log_alert_level`: 이 레벨 이상의 알림만 기록 (1~16, 기본: 3)

---

## 6. Wazuh API

### 6.1 API 인증 토큰 획득

```bash
# 기본 관리자 계정으로 토큰 획득
TOKEN=$(curl -s -u wazuh-wui:wazuh-wui -k -X POST \
  "https://10.20.30.100:55000/security/user/authenticate?raw=true")
echo $TOKEN | head -c 50
```

### 6.2 Manager 정보 조회

```bash
curl -s -k -X GET "https://10.20.30.100:55000/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool  # 인증 토큰
```

**예상 출력:**
```json
{
    "data": {
        "title": "Wazuh API REST",
        "api_version": "4.11.2",
        "revision": 40112,
        "license_name": "GPL 2.0",
        "hostname": "siem",
        "timestamp": "2026-03-27T10:00:00Z"
    }
}
```

### 6.3 Agent 목록 조회

```bash
curl -s -k -X GET "https://10.20.30.100:55000/agents?pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40  # 인증 토큰
```

**예상 출력:**
```json
{
    "data": {
        "affected_items": [
            {
                "id": "000",
                "name": "siem",
                "status": "active",
                "manager": "siem",
                "node_name": "node01",
                "ip": "127.0.0.1",
                "version": "Wazuh v4.11.2"
            }
        ],
        "total_affected_items": 1
    }
}
```

---

## 7. Agent 등록 및 관리

### 7.1 Agent 등록 (API 방식)

secu 서버를 Agent로 등록:

```bash
# siem 서버에서 Agent 등록
curl -s -k -X POST "https://10.20.30.100:55000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"secu","ip":"10.20.30.1"}' | python3 -m json.tool  # 요청 데이터(body)
```

**예상 출력:**
```json
{
    "data": {
        "id": "001",
        "key": "MDAxIHNlY3UgMTAuMjAuMzAuMSBhYmNkZWYxMjM0NTY3ODkw..."
    }
}
```

### 7.2 Agent 측 설정

secu 서버에 접속하여 Agent를 설정:

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# Agent 설치 확인
echo 1 | sudo -S /var/ossec/bin/wazuh-control info

# Agent 설정 파일 확인
echo 1 | sudo -S cat /var/ossec/etc/ossec.conf | grep -A 5 "<server>"
```

**Agent ossec.conf의 서버 연결 설정:**

```xml
<client>
  <server>
    <address>10.20.30.100</address>
    <port>1514</port>
    <protocol>tcp</protocol>
  </server>
</client>
```

### 7.3 Agent 시작 및 확인

```bash
# Agent 서비스 시작
echo 1 | sudo -S systemctl restart wazuh-agent
echo 1 | sudo -S systemctl status wazuh-agent
```

### 7.4 Manager에서 Agent 상태 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# siem 서버에서
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

echo 1 | sudo -S /var/ossec/bin/agent_control -l
```

**예상 출력:**
```
Wazuh agent_control. List of available agents:
   ID: 000, Name: siem (server), IP: 127.0.0.1, Active/Local
   ID: 001, Name: secu, IP: 10.20.30.1, Active
   ID: 002, Name: web, IP: 10.20.30.80, Active
```

---

## 8. 알림 로그 확인

### 8.1 실시간 알림

```bash
echo 1 | sudo -S tail -f /var/ossec/logs/alerts/alerts.json | python3 -c "
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        rule = e.get('rule', {})
        agent = e.get('agent', {})
        print(f\"[{e.get('timestamp','')}] Level:{rule.get('level','')} Rule:{rule.get('id','')} {rule.get('description','')}\")
        print(f\"  Agent: {agent.get('name','local')} ({agent.get('ip','127.0.0.1')})\")
    except: pass
" &
```

Ctrl+C로 종료.

### 8.2 최근 알림 확인

```bash
echo 1 | sudo -S tail -10 /var/ossec/logs/alerts/alerts.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        print(f\"Level {r.get('level','?'):>2} | Rule {r.get('id','?'):>6} | {r.get('description','?')}\")
    except: pass
"
```

**예상 출력:**
```
Level  5 | Rule   5715 | sshd: authentication success.
Level  3 | Rule    530 | Wazuh agent started.
Level  7 | Rule   5710 | sshd: attempt to login using a denied user.
```

### 8.3 알림 레벨 의미

| 레벨 | 설명 | 예시 |
|------|------|------|
| 0~2 | 무시 | 시스템 정보 |
| 3~5 | 낮음 | 로그인 성공, 서비스 시작 |
| 6~8 | 중간 | 인증 실패, 설정 변경 |
| 9~11 | 높음 | 다수 인증 실패, 무결성 변경 |
| 12~15 | **심각** | **루트킷 탐지, 침입 시도** |

---

## 9. Wazuh Dashboard

### 9.1 대시보드 접속

웹 브라우저에서 다음 URL 접속:

```
https://10.20.30.100
```

- 기본 계정: `admin` / `admin` (또는 설치 시 설정한 계정)

### 9.2 주요 메뉴

| 메뉴 | 설명 |
|------|------|
| Overview | 전체 보안 현황 대시보드 |
| Agents | Agent 목록 및 상태 |
| Security Events | 보안 이벤트 검색 |
| Integrity Monitoring | 파일 무결성 모니터링 |
| Vulnerabilities | 취약점 스캔 결과 |
| MITRE ATT&CK | 공격 기법 매핑 |
| SCA | 보안 설정 평가 |

### 9.3 이벤트 검색 예시

대시보드에서 다음을 검색해보라:

```
rule.level >= 7
```

```
agent.name:secu AND rule.groups:authentication_failed
```

---

## 10. Suricata 로그 연동

Suricata의 eve.json을 Wazuh가 수집하도록 설정:

### 10.1 Agent 측 설정 (secu 서버)

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1  # 비밀번호 자동입력 SSH

# ossec.conf에 Suricata 로그 수집 추가
echo 1 | sudo -S tee -a /var/ossec/etc/ossec.conf << 'XMLEOF'
<ossec_config>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>
</ossec_config>
XMLEOF

# Agent 재시작
echo 1 | sudo -S systemctl restart wazuh-agent
```

### 10.2 연동 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# siem 서버에서 Suricata 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100  # 비밀번호 자동입력 SSH

echo 1 | sudo -S cat /var/ossec/logs/alerts/alerts.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if 'suricata' in str(e.get('rule',{}).get('groups',[])):
            r = e['rule']
            print(f\"[Suricata] Level {r['level']} | {r['description']}\")
    except: pass
" | tail -5
```

---

## 11. 실습 과제

### 과제 1: 서비스 확인

1. Wazuh Manager, Indexer, Dashboard가 모두 동작하는지 확인
2. API로 Manager 버전 정보를 조회
3. 등록된 Agent 목록을 조회

### 과제 2: Agent 상태

1. secu, web 서버의 Agent가 Active 상태인지 확인
2. 비활성 Agent가 있으면 원인을 파악하고 재시작

### 과제 3: 알림 분석

1. 최근 1시간 내 Level 7 이상 알림을 조회
2. 가장 많이 발생한 알림 Rule ID를 확인
3. 특정 Agent(secu)의 알림만 필터링

---

## 12. 핵심 정리

| 개념 | 설명 |
|------|------|
| SIEM | 보안 이벤트 통합 관제 플랫폼 |
| Wazuh Manager | 분석 엔진, 룰 매칭 (1514, 55000) |
| Wazuh Indexer | 이벤트 저장/검색 (OpenSearch) |
| Wazuh Dashboard | 웹 시각화 (443) |
| Agent | 호스트 로그 수집, Manager로 전송 |
| ossec.conf | 핵심 설정 파일 |
| alerts.json | 알림 로그 |
| Rule Level | 1~15 (높을수록 심각) |
| API | REST API (55000 포트) |

---

## 다음 주 예고

Week 10에서는 Wazuh 탐지 룰을 다룬다:
- local_rules.xml에 커스텀 룰 작성
- 디코더 작성
- logtest로 룰 검증

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
