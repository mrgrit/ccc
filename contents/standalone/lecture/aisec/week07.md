# W07 — AI 에이전트 (3): Bastion 활용 보안 운영 / 취약점 / 모의해킹

> 본 주차는 **인공지능보안 (입문)** 의 7 주차이며, AI 에이전트 시리즈 의 마지막 주차이다.
> W05 (에이전트 / Claude Code / 하네스) + W06 (컨텍스트 / KG / Bastion architecture) 의 학습 위에,
> **Bastion 의 실 운영** 의 3 case (보안 운영 / 취약점 분석 / 모의해킹 보조) 의 통합 실습.

---

## 본 주차 의도

W05-W06 의 학습 은 **이론 / 개념 / architecture** 에 집중. 본 주차 는 **실 운영 / 실 명령 / 실 응답** 의 hands-on.

운영 의 의의 — 학생 이 본 주차 의 종료 후 다음 3 task 의 본인 실 수행 가능 해야 함:

1. **보안 운영** — Bastion 의 chat 으로 alert triage / correlation / 보고서 작성.
2. **취약점 분석** — Bastion 의 chat 으로 CVE / 환경 / 권장 패치 의 통합 분석.
3. **모의해킹 보조** — Bastion 의 chat 으로 학습 환경 의 침투 step 의 권장 + ATT&CK 매핑.

본 주차 의 한계 — Bastion 의 운영 의 **자율 수준 의 100% 의 신뢰 는 아직** 의 점 의 명확 한 인식. AI Safety (W08-W10) 의 학습 이 필수.

---

## 1 차시 — Bastion 의 활용 보안 운영

### 1-1. 운영 의 시나리오 의 분류

| 시나리오 | task | Bastion 의 역할 |
|----------|------|-----------------|
| **alert triage** | 새 alert 의 위험도 / 5W / 권장 | 즉시 분석 + 운영자 의 판단 보조 |
| **alert correlation** | 여러 alert 의 인과 / chain | KG 의 PE 의 reuse + ATT&CK 매핑 |
| **enrichment** | srcip 의 GeoIP / CTI / asset 의 결합 | 외부 (가능 시) + 내부 의 통합 |
| **reporting** | shift / weekly / incident 의 보고서 | 형식 의 자동 + 사실 의 확인 |
| **proactive hunting** | 가설 의 KQL / SPL / Sigma 의 자동 생성 | 운영자 의 가설 의 form 화 |
| **post-incident** | 사고 의 timeline / root cause / lesson | KG 의 anchor + 의 회상 |

### 1-2. alert triage 의 표준 워크플로우

Bastion 의 운영 의 alert triage 의 표준 step:

```mermaid
flowchart TB
    A[Wazuh / Suricata / ModSec alert] --> B[Bastion /chat 호출]
    B --> C[KG context 검색<br/>유사 alert / Playbook]
    C --> D[ReAct loop<br/>Thought / Action / Observation]
    D --> E[skill 호출<br/>geoip / cti / asset]
    E --> F[종합 응답<br/>5W + 위험도 + 권장]
    F --> G[운영자 의 판단]
    G --> H[task_outcome anchor 기록]
```

운영자 의 prompt 의 표준 template:

```
다음 alert 의 분석:
- timestamp: ...
- rule.id: ...
- rule.level: ...
- agent: ...
- srcip: ...
- raw log: ...

응답 형식:
1. 5W (when / where / who / what / why)
2. 위험도 (low / medium / high / critical)
3. 권장 (즉시 차단 / 모니터링 / 무시)
4. ATT&CK 매핑 (있는 경우)
5. 추가 정보 의 필요 (있는 경우)
```

### 1-3. 실 운영 의 case 1 — Wazuh alert 5710 (sshd brute)

```bash
ssh 6v6-bastion '
curl -s -X POST \
    -H "X-API-Key: ccc-api-key-2026" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"다음 Wazuh alert 의 5W + 위험도 + 권장 분석:\n{\\\"rule\\\":{\\\"id\\\":\\\"5710\\\",\\\"level\\\":5,\\\"description\\\":\\\"Attempt to login using a non-existent user\\\"},\\\"agent\\\":{\\\"name\\\":\\\"web\\\"},\\\"data\\\":{\\\"srcip\\\":\\\"192.168.0.112\\\",\\\"srcuser\\\":\\\"admin\\\"},\\\"timestamp\\\":\\\"2026-05-12T14:30:00\\\"}\", \"agent\":\"master\"}" \
    http://localhost:9100/chat
'
```

기대 응답 의 형태:

```
1. 5W
   - When: 2026-05-12 14:30 KST
   - Where: agent=web (학습 환경 의 web VM)
   - Who: srcip=192.168.0.112 (학습 환경 의 attacker VM)
   - What: 비존재 사용자 admin 의 로그인 시도
   - Why: brute force 의 정찰 단계 의 가능성

2. 위험도: medium
   (rule.level=5 의 권장 / 학습 환경 의 attacker VM 이므로 실 환경 의 critical 대비)

3. 권장
   - 모니터링: 5 분 의 동일 srcip 의 추가 시도 확인
   - rule 100400 (chain) 의 trigger 시 level 12 의 의의

4. ATT&CK
   - T1110.001 (Brute Force: Password Guessing)

5. 추가
   - srcip 의 asset DB (있는 경우) 의 확인
   - CTI feed 의 IoC 매칭 (가능 시)
```

### 1-4. 실 운영 의 case 2 — alert correlation

여러 alert 의 chain 의 분석:

```
운영자: 다음 5 alert 의 인과 / chain 의 분석:
- t0: Suricata ET WEB_SPECIFIC_APPS Joomla SQLi
- t0+1m: ModSec 941100 (XSS / SQLi)
- t0+2m: Wazuh 5710 (sshd Failed)
- t0+5m: Wazuh 92053 (ssh Accepted Root)
- t0+10m: auditd execve /tmp/x

Bastion 의 응답:
가설: SQLi 의 익스플로잇 → web 의 webshell → sshd brute → root 의 ssh 의 성공 →
임의 명령 의 execve 의 chain. ATT&CK kill chain — Initial Access (T1190) →
Persistence (T1505.003) → Credential Access (T1110.001) → Lateral Movement →
Execution (T1059).
```

### 1-5. enrichment 의 운영 의 예

학습 환경 외부 (가능 시) 또는 내부 의 정보 의 결합:

```
운영자: srcip=192.168.0.112 의 enrichment:
1. asset DB 의 hostname / 소유자
2. GeoIP (가능 시)
3. 과거 의 동일 srcip 의 alert history
4. CTI feed 의 IoC 매칭

Bastion 의 응답:
1. hostname=black, owner=학습 환경 의 attacker VM, ccc/1 의 standard creds
2. private IP (RFC1918) → GeoIP 의 의의 없음
3. KG 의 query — 과거 의 4 alert (rule.id 5710 의 5 회 / 941100 의 3 회)
4. CTI 의 의의 없음 (학습 환경)
```

### 1-6. reporting 의 운영 의 예

```
운영자: shift report (4 시간) 의 작성. 지표 + top alerts + 권장.

Bastion 의 응답:
=== Shift Report (2026-05-12 10:00 - 14:00 KST) ===

지표
- 총 alerts: 142
- high+: 8
- agent transition: 모두 OK

Top 3 alerts
1. rule 5710 (sshd Failed) x 25 from 192.168.0.112
2. rule 941100 (ModSec XSS/SQLi) x 12 from 192.168.0.112
3. rule 5712 (sshd brute level 10) x 3 from 192.168.0.112

권장
- 192.168.0.112 의 학습 환경 attacker VM 의 정상 패턴 확인
- rule 100400 의 chain rule 의 trigger 확인 필요
- 야간 의 monitoring 강화
```

### 1-7. 운영 의 한계 와 운영자 의 책임

Bastion 의 한계:

- **환각** — 가짜 의 IoC / CVE / hostname 의 응답 의 가능성.
- **편향** — 학습 데이터 의 편향 의 응답 의 편향.
- **컨텍스트 의 누락** — 운영자 의 prompt 의 누락 의 영향.
- **신뢰도 의 미보장** — confidence 의 명시 의 부재.

운영자 의 책임:

- **모든 응답 의 검증** — 사실 / IoC / CVE 의 외부 출처 의 확인.
- **결정 의 책임** — Bastion 의 응답 은 보조 의 의의, 결정 의 주체 는 운영자.
- **사후 의 학습** — task_outcome anchor 의 분석 + Playbook 의 업데이트.
- **사고 의 escalation** — 자동 처리 불가 의 사고 의 인간 의 escalation.

---

## 2 차시 — Bastion 의 활용 취약점 분석

### 2-1. 취약점 분석 의 task 의 분류

| task | Bastion 의 역할 |
|------|-----------------|
| **CVE 분석** | description / CVSS / CWE / EPSS / 영향 의 통합 |
| **환경 의 영향 의 평가** | 6v6 의 어떤 자산 의 영향 |
| **패치 의 우선순위** | CVSS + EPSS + 자산 의 중요도 |
| **mitigation 의 권장** | 패치 / 차단 / 우회 의 단계 |
| **PoC 의 분석** | 가능 한 exploit 의 학습 환경 의 시뮬 |

### 2-2. CVE 분석 의 표준 워크플로우

```mermaid
flowchart TB
    A[CVE 의 알림] --> B[Bastion /chat]
    B --> C[KG 의 유사 CVE / Playbook]
    C --> D[ReAct loop]
    D --> E[skill 호출<br/>cve_lookup / cvss_calc / asset_match]
    E --> F[종합 응답<br/>5 항목]
    F --> G[운영자 의 패치 의 계획]
```

### 2-3. 실 case — CVE 분석

```
운영자: CVE-2024-1234 의 분석:
description: Apache HTTP Server 2.4.x 의 mod_rewrite 의 buffer overflow → RCE.
CVSS: 9.8 (Critical)
attack vector: Network / no auth required.

Bastion 의 응답:
1. 핵심
   buffer overflow → RCE. CWE-120 (Buffer Copy without Checking Size).

2. CVSS 의 의의
   9.8 = Critical. attack vector network / no auth / no UI → 원격 의 무인증 의 익스플로잇.

3. 영향 의 범위
   6v6 의 web VM 의 Apache 2.4.x 의 가용. 패치 우선순위 critical.

4. PoC 의 가용성
   CVE-2024-1234 는 가상 의 예시. 실 운영 의 경우 exploit-db / GitHub / metasploit 의
   검색 의 필요.

5. 권장 패치
   - 즉시: WAF (ModSec) 의 mod_rewrite 의 anomaly 의 차단 룰
   - 1 시간 내: vendor advisory 의 확인 + 패치 적용
   - 사후: 동일 모듈 의 추가 vuln 의 가능성 의 monitoring
```

### 2-4. CVE 의 운영 의 가시화 의 도구

- **NVD API** — https://nvd.nist.gov/developers (외부, 가능 시).
- **CVE5 schema** — JSON 의 표준.
- **EPSS** — https://www.first.org/epss/ (Exploit Prediction Scoring System).
- **MITRE CWE** — Common Weakness Enumeration.
- **vendor advisory** — Apache / Nginx / MS / Cisco 등.

CCC 의 폐쇄망 의 한계 — 외부 API 의 직접 호출 불가. 대안 — 사전 sync 의 mirror DB (CVE local cache).

### 2-5. 환경 의 매칭 의 운영

CCC 의 6v6 의 자산 list:

```yaml
6v6_assets:
  - hostname: web
    ip: 192.168.0.103
    services: [Apache 2.4, PHP 8, MariaDB]
    role: external_web

  - hostname: dmz
    ip: 192.168.0.108
    services: [Nginx 1.24, Node.js 20]
    role: dmz_proxy

  - hostname: int
    ip: 192.168.0.111
    services: [PostgreSQL 16]
    role: internal_db

  # ... etc
```

CVE 의 도착 시 — Bastion 의 위 list 의 매칭 + 영향 의 즉시 응답.

### 2-6. 패치 의 우선순위 의 알고리즘

```
score = CVSS × EPSS_factor × asset_critical_factor

- CVSS = 0-10
- EPSS_factor = exploit 의 1 개월 의 가능성 (0-1)
- asset_critical_factor = 1.0 (internal critical) / 0.5 (dmz) / 0.3 (external 일반)

score > 5 → 즉시 (24h)
score > 3 → 단기 (7d)
score > 1 → 일반 (30d)
score < 1 → 검토 (next maintenance window)
```

### 2-7. mitigation 의 단계 의 학습

| 단계 | 의의 | 예 |
|------|------|----|
| **즉시 차단** | WAF / IPS / firewall 의 rule | ModSec 의 anomaly rule |
| **임시 우회** | 서비스 의 비활성 / 포트 의 차단 | mod_rewrite 의 disable |
| **공식 패치** | vendor 의 의 패치 의 적용 | apt update + apache restart |
| **장기 강화** | 동일 vuln class 의 monitoring | CWE-120 의 monitoring rule |

---

## 3 차시 — Bastion 의 활용 모의해킹 보조

### 3-1. 모의해킹 의 정의 와 윤리

> **모의해킹 (penetration testing)** = 합의 된 범위 / 시간 / 도구 의 인가 의 실 침투 시도.

본 강의 의 학습 환경 — CCC 의 6v6 + attacker VM (192.168.0.112) + JuiceShop (192.168.0.100). **학습 환경 외부 의 시스템 의 침투 시도 의 절대 금지**.

윤리:

- **인가** — 사전 의 서면 동의.
- **범위** — 사전 의 RoE (Rules of Engagement) 의 명시.
- **목적** — 방어 의 강화, 공격 의 의 의도 아님.
- **공개** — 사후 의 보고서 의 stakeholder 의 공유.

### 3-2. 모의해킹 의 PTES (Penetration Testing Execution Standard)

7 단계:

| 단계 | 의의 |
|------|------|
| 1. **Pre-engagement** | RoE 의 합의 |
| 2. **Intelligence Gathering** | 정찰 (passive + active) |
| 3. **Threat Modeling** | 위협 의 가설 |
| 4. **Vulnerability Analysis** | vuln 의 식별 |
| 5. **Exploitation** | 실 익스플로잇 |
| 6. **Post-Exploitation** | 데이터 / lateral / persistence |
| 7. **Reporting** | 결과 의 보고 |

Bastion 의 역할 — 각 단계 의 LLM 의 보조 (즉시 의 step 권장 + ATT&CK 매핑).

### 3-3. 정찰 의 Bastion 의 보조

```
운영자: 학습 환경 의 web (192.168.0.103) 의 passive recon 의 첫 step 의 권장 + 명령.

Bastion 의 응답:
1. nmap -sV -p- 192.168.0.103 — full TCP scan + service 의 확인
2. whatweb http://192.168.0.103 — web framework / CMS 의 식별
3. nikto -h http://192.168.0.103 — web 의 vuln 의 스캔
4. dirb http://192.168.0.103 — 디렉토리 의 brute

ATT&CK 매핑:
- T1595 Active Scanning
- T1593 Search Open Websites/Domains
```

### 3-4. 익스플로잇 의 Bastion 의 보조

```
운영자: JuiceShop 의 SQLi vuln 의 익스플로잇 의 step 의 권장.

Bastion 의 응답:
1. /api/Users 의 POST 의 email 의 ' OR '1'='1 의 시도
2. sqlmap -u "http://juice.6v6.lab/api/Users" --batch --dbs

ATT&CK 매핑: T1190 (Exploit Public-Facing Application)
CWE 매핑: CWE-89 (SQL Injection)
OWASP 매핑: A03:2021 (Injection)

주의: 본 권장 의 학습 환경 만, 외부 시스템 의 적용 의 금지.
```

### 3-5. 모의해킹 의 LLM 보조 의 안전

위험:

- LLM 이 의도 하지 않게 외부 시스템 의 공격 step 의 응답.
- LLM 이 가짜 의 payload 의 응답 (환각).
- LLM 이 RoE 의 외부 의 target 의 응답.

대응:

- **system prompt** 의 명시 — "학습 환경 만, 외부 의 거부".
- **target 의 사전 인가** — 운영자 의 사전 confirm.
- **출력 의 검증** — 응답 의 IoC / payload 의 검증.
- **사용 의 logging** — 모든 prompt + 응답 의 기록.

CCC 의 Bastion 의 학습 환경 의 한정:

```python
# packages/bastion/agent.py (예 pseudocode)
SAFE_TARGETS = ["192.168.0.0/24", "juice.6v6.lab", "*.6v6.lab"]

def guard_target(target):
    if not is_in_subnet(target, SAFE_TARGETS):
        raise SafetyError(f"Target {target} 의 학습 환경 외부 — 거부")
```

### 3-6. 모의해킹 의 보고서

LLM 의 보조 의 강점 — 형식 의 자동 + step 의 timeline 의 종합 + 권장 의 일관성.

```
운영자: 본 침투 의 보고서 의 작성:
- 정찰: nmap 의 22/80/443
- vuln: JuiceShop 의 /api/Users 의 SQLi
- 익스플로잇: sqlmap 의 dump
- impact: 사용자 DB 의 전체 dump

Bastion 의 응답:
=== Penetration Test Report — 2026-05-12 ===

target: JuiceShop (juice.6v6.lab) 학습 환경
RoE: 학습 환경 만, exploit 의 한정

Executive Summary
JuiceShop 의 /api/Users endpoint 의 SQLi vuln 의 익스플로잇 의 성공. 사용자 DB
의 전체 dump 의 가능. severity critical.

Detailed Findings
1. nmap 의 22/80/443 의 open
2. /api/Users 의 SQLi (CWE-89 / A03 / T1190)
3. sqlmap 의 dump 의 성공

Remediation
1. /api/Users 의 prepared statement
2. ModSec 의 SQLi rule 의 추가
3. WAF 의 monitoring

ATT&CK Coverage
Initial Access (T1190) ← 본 시뮬 의 단계.
```

### 3-7. R/B/P — 본 주차 의 시나리오

```mermaid
flowchart LR
    subgraph Red [🔴 Red — 모의해킹]
        R1[정찰 nmap]
        R2[SQLi 시도]
        R3[sqlmap dump]
    end

    subgraph Blue [🔵 Blue — 방어]
        B1[ModSec 941100]
        B2[Wazuh 100400 chain]
        B3[운영자 의 검토]
    end

    subgraph Purple [🟣 Purple — Bastion]
        P1[Red 보조<br/>step 권장]
        P2[Blue 보조<br/>alert triage]
        P3[보고서 의 통합]
    end

    R1 --> R2 --> R3
    R3 --> B1 --> B2 --> B3
    P1 -.-> R1
    P1 -.-> R2
    P2 -.-> B1
    P2 -.-> B2
    P3 --> B3
```

### 3-8. 본 주차 의 hands-on

본 주차 의 lab 의 5 step (lab yaml 참조):

1. **alert triage** 의 Bastion 의 실 호출 + 응답 의 분석.
2. **alert correlation** 의 Bastion 의 실 호출 + ATT&CK 매핑.
3. **CVE 분석** 의 Bastion 의 5 항목 의 응답.
4. **모의해킹 의 정찰 step 의 권장** 의 Bastion 의 응답.
5. **보고서 의 LLM 보조** 의 마무리.

---

## 본 주차 의 정리

1. Bastion 의 **운영 의 6 task** — triage / correlation / enrichment / reporting / hunting / post-incident.
2. **alert triage** 의 표준 workflow — KG → ReAct → skill → 5W + 위험도 + 권장 + ATT&CK.
3. **CVE 분석** 의 5 항목 — 핵심 / CVSS / 영향 / PoC / 패치.
4. **모의해킹 보조** 의 PTES 의 7 단계 의 각 의 LLM 의 역할.
5. **안전** — 학습 환경 만, 외부 거부, 출력 검증, logging.
6. **운영자 의 책임** — 모든 응답 의 검증, 결정 의 주체, 사후 학습, escalation.

---

## 자기 점검

- alert triage 의 응답 의 5 항목 의 응답 가능?
- CVE 분석 의 5 항목 의 응답 가능?
- PTES 의 7 단계 의 응답 가능?
- 모의해킹 의 LLM 보조 의 4 안전 의 응답 가능?

---

## 다음 주차

**W08 — AI Safety (1): 개론 / 악성 파인튜닝 / 프롬프트 인젝션·Poisoning**

- AI Safety 의 정의 와 표준 (MITRE ATLAS / OWASP LLM Top 10 / NIST AI RMF).
- 악성 파인튜닝 의 위협.
- 프롬프트 인젝션 의 패턴.
- 데이터 / 모델 poisoning.

본 주차 까지 의 운영 의 신뢰 의 위협 의 본격 학습 의 시작.
