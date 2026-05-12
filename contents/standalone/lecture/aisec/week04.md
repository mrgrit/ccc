# Week 04 — AI Powered Cyber Security (2) — LLM 활용 보안로그 / 탐지룰 / 취약점·모의해킹

> W03 의 ML/DL 보안 활용 위에, **LLM 의 본격 보안 작업** 학습. SOC 분석가 의 일상
> 작업 (로그 분석 / 탐지룰 작성 / 취약점 분석 / 모의해킹 보조) 를 LLM 으로 자동화·
> 가속. 본 과목 W05+ (AI 에이전트) 의 직접 선수.

## 학습 목표

학생은 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. **LLM 의 보안 로그 분석 패턴** — Triage / Correlation / Enrichment / Reporting
2. **alert 의 LLM 처리 흐름** — Wazuh alert → LLM → 의사결정 (acknowledge / escalate)
3. **탐지룰 생성 의 LLM 활용** — Sigma / Suricata / Wazuh / ModSec 룰 자동 생성
4. **CVE 의 LLM 분석** — CVE description → 영향 분석 + 권장 패치
5. **모의해킹 보조** — Penetration testing 의 step 별 LLM 조언 + Burp Suite 통합
6. **운영 권장** — token 비용 / hallucination 방지 / 인간 검토
7. **LLM as Judge** — LLM 이 다른 LLM 의 응답 / 보안 분석 평가
8. W04 R/B/P 1 사이클

## 강의 시간 배분 (3시간 — 3 차시)

| 차시 | 시간 | 내용 | 유형 |
|------|------|------|------|
| 1차시 | 0:00–1:00 | **LLM 활용 보안로그 분석** — 4 패턴 + Wazuh alert + Bastion 시뮬 | 강의 |
| 휴식 | 1:00–1:10 | | |
| 2차시 | 1:10–2:10 | **LLM 활용 탐지룰 생성** — Sigma / Suricata / Wazuh / ModSec 룰 자동 | 강의 |
| 휴식 | 2:10–2:20 | | |
| 3차시 | 2:20–3:00 | **LLM 활용 취약점 분석 + 모의해킹** — CVE / Burp / sqlmap 통합 | 실습 |

---

## 1차시 — LLM 활용 보안 로그 분석

### 1.1 SOC 분석가의 일상 task

```
1. Triage — alert 의 우선순위 (false-positive vs real)
2. Correlation — 여러 alert 의 연관 사고 식별
3. Enrichment — alert 의 context 보강 (IOC / 사용자 / 자산)
4. Reporting — IR 보고서 작성
5. Hunting — proactive hunt (W14 secuops 참조)
6. Tool 운영 — Wazuh / Suricata / ModSec 의 룰 관리
```

LLM 이 1-4 모두 가속 가능 + 5-6 보조.

### 1.2 LLM 의 alert 처리 흐름

```mermaid
graph LR
    A["📋 Wazuh alert<br/>(JSON)"]

    L1["1. Pre-process<br/>(parse + dedup)"]
    L2["2. LLM 분석<br/>(triage prompt)"]
    L3["3. Enrichment<br/>(CTI / asset)"]
    L4["4. Decision<br/>(ack / escalate)"]

    OUT1["📋 자동 ack"]
    OUT2["📋 SOC 분석가"]
    OUT3["📋 자동 IR"]

    A --> L1 --> L2 --> L3 --> L4
    L4 -->|low risk| OUT1
    L4 -->|medium| OUT2
    L4 -->|high| OUT3

    style A fill:#d29922,color:#fff
    style L2 fill:#bc8cff,color:#fff
    style OUT3 fill:#f85149,color:#fff
```

### 1.3 LLM 의 alert 분석 prompt 패턴

```python
system_prompt = """
당신은 SOC Tier 2 분석가 입니다.

다음 Wazuh alert 를 분석:
1. alert 의 핵심 사실 (5 W: when / who / where / what / why)
2. 위험도 평가 (low / medium / high / critical)
3. false-positive 가능성 (high / medium / low / very low)
4. 권장 조치 (자동 ack / SOC 검토 / 즉시 IR)
5. 관련 ATT&CK Technique

응답 형식: JSON
"""

user_message = f"""
[alert]
{wazuh_alert_json}

[자산 정보]
{asset_info}

[CTI]
{cti_match}
"""

# LLM 호출
response = ollama.chat(
    model="gemma3:4b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ],
    format="json"
)
```

### 1.4 응답 예 (LLM 의 분석 결과)

```json
{
  "facts": {
    "when": "2026-05-12T14:32:18Z",
    "who": "ccc",
    "where": "10.20.30.201 (bastion)",
    "what": "SSH failed login from 1.2.3.4",
    "why": "5 회 반복 — brute force 의심"
  },
  "risk": "high",
  "false_positive_probability": "low",
  "recommendation": "즉시 IR — 1.2.3.4 의 fw drop + 분석가 검토",
  "attack_pattern": ["T1110.001 Password Guessing"]
}
```

### 1.5 alert 의 correlation (다중 alert 분석)

```python
# 1 hour 안의 모든 alert 의 LLM 분석
recent_alerts = get_wazuh_alerts(since="1 hour ago")  # 100+ alert

prompt = f"""
다음 100 alert 가 모두 같은 사고 의 일부 인가?
또는 별 사고 인가?
사고 그룹 화 + 우선순위.

[alerts]
{json.dumps(recent_alerts)}
"""

# LLM 응답:
# {
#   "incidents": [
#     {"id": "INC-001", "alerts": ["alert-1", "alert-3", ...], "tactic": "TA0001"},
#     {"id": "INC-002", "alerts": ["alert-5"], "tactic": "TA0007"}
#   ]
# }
```

### 1.6 enrichment — CTI / 자산 통합

```python
# alert 의 srcip → CTI 검색 + asset 검색
def enrich_alert(alert):
    srcip = alert['data']['srcip']

    # CTI lookup
    cti = opencti_search(srcip)

    # asset lookup
    asset = cmdb_search(alert['agent']['name'])

    # LLM 의 통합 분석
    enriched = llm_analyze({
        "alert": alert,
        "cti": cti,
        "asset": asset
    })

    return enriched
```

### 1.7 비용 + 속도

```
LLM 의 token 비용 / 응답 시간:

클라우드:
  GPT-4o: $5 / 1M input token, $15 / output
  Claude 3.5 Sonnet: $3 / 1M input, $15 / output
  Gemini 1.5: $3.5 / 1M input

로컬:
  gemma3:4b: 자유 (전기만)
  qwen2.5:7b: 자유
  Bastion gpt-oss:120b: 자유 + 단일 GPU

운영 시:
  1000 alert / 일 × 1K token / alert = 1M token / 일
  GPT-4o = $20 / 일 = $600 / 월 → 운영 부담
  로컬 = 0 (전기만)
```

본 lab 의 권장: 로컬 (Ollama 또는 Bastion).

---

## 2차시 — LLM 활용 탐지룰 생성

### 2.1 탐지룰 생성 의 표준 도구

| 도구 | 룰 형식 | 용도 |
|------|---------|------|
| **Sigma** | YAML (generic) | SIEM 의 통합 표준 |
| **Suricata** | Sigma syntax | 네트워크 IDS |
| **Wazuh** | XML | SIEM (log analysis) |
| **ModSecurity** | SecRule (Apache config) | WAF |
| **YARA** | YARA syntax | malware 탐지 |
| **Sentinel** | KQL (Microsoft) | Azure SIEM |
| **Splunk** | SPL | Splunk SIEM |

### 2.2 Sigma 룰 (가장 표준)

```yaml
title: SSH Brute Force from Single IP
id: 12345678-1234-1234-1234-123456789012
status: stable
description: SSH 의 5+ failed login from same IP in 60 seconds
references:
  - https://attack.mitre.org/techniques/T1110/
tags:
  - attack.credential_access
  - attack.t1110.001
logsource:
  product: linux
  service: sshd
detection:
  selection:
    failure_msg: 'Failed password for'
  timeframe: 60s
  condition: selection | count() by src_ip > 5
falsepositives:
  - 직원 의 비밀번호 잊음
level: high
```

### 2.3 LLM 으로 Sigma 룰 자동 생성

```python
system = """
당신은 SOC Detection Engineer.
주어진 침해 시나리오 의 Sigma 룰 YAML 형식 으로 작성.
필수 field: title / id / description / tags / logsource / detection / falsepositives / level
ATT&CK Technique ID 매핑.
"""

user = """
시나리오: web 의 ModSec audit log 에 941xxx (XSS) 룰 매치가
60 초에 3 건 이상 같은 src_ip 에서 발생.

해당 시나리오의 Sigma 룰 작성.
"""

# LLM 응답: 완성된 Sigma YAML
```

### 2.4 Wazuh 룰 의 LLM 생성

```python
system = """
당신은 Wazuh Detection Engineer.
주어진 시나리오 의 Wazuh XML 룰 작성.
형식:
<rule id="..." level="...">
  <if_sid>...</if_sid>
  <field name="...">...</field>
  <description>...</description>
</rule>
ID 범위: 100000+ (사용자 정의)
"""

user = """
ModSec 의 941100 (XSS via libinjection) 매치가
60 초에 3 건 + 같은 src_ip → level 12 alert + AR (firewall-drop 30분)
"""

# LLM 응답
```

### 2.5 Suricata 룰

```python
system = """
당신은 Suricata 룰 작성자.
주어진 페이로드 의 Suricata 룰 작성.
sid 범위: 9000000+
classtype 명시.
"""

user = """
페이로드: User-Agent 가 "sqlmap" 인 HTTP 요청
60 초에 1 회만 alert (threshold)
"""

# LLM 응답 (W04 attack 의 9000042 와 비슷)
```

### 2.6 룰 작성 후 검증

```python
# LLM 응답 의 자동 검증 절차
def validate_rule(rule_text, rule_type):
    if rule_type == "sigma":
        # sigma 의 schema 검증
        return sigma_lint(rule_text)
    elif rule_type == "wazuh":
        # XML syntax + wazuh-logtest
        return subprocess.run(["wazuh-logtest", "-r", rule_text])
    elif rule_type == "suricata":
        # suricata -T -S
        return subprocess.run(["suricata", "-T", "-S", rule_path])
```

LLM 응답 → 자동 검증 → 실 환경 적용 (after human review).

### 2.7 ModSec custom rule

```python
system = """
당신은 ModSec / OWASP CRS rule 작성자.
SecRule + chain + transformation + actions.
"""

user = """
다음 차단 조건:
- POST request body 에 한국 주민번호 패턴 (6digit-7digit)
- 응답: 403 + log
- audit 의 message: "RRN exposure attempt"
"""

# LLM 응답
# SecRule REQUEST_BODY "@rx \\d{6}-[1-4]\\d{6}" \
#     "id:9000001, ..."
```

### 2.8 룰 생성 의 hallucination 위험

LLM 가 잘못된 룰 생성 가능 — 사용자 검증 + 자동 검증 + dry-run 필수.

```python
# 안전한 룰 적용 절차
1. LLM 의 룰 생성
2. syntax 검증 (lint)
3. 별 test 환경 적용
4. 사람의 review
5. production 적용 (DetectionOnly 먼저)
6. 1주일 baseline 후 활성
```

---

## 3차시 — LLM 활용 취약점 분석 + 모의해킹

### 3.1 CVE 의 LLM 분석

```python
system = """
당신은 보안 컨설턴트.
CVE 의 description + CVSS + 영향 분석 + 권장 패치 작성.
응답:
  1. CVE 핵심 (어떤 vuln)
  2. CVSS 3.1 점수 의 의미
  3. 영향 범위 (어떤 시스템 / 어떤 행위)
  4. 익스플로잇 가용성 (PoC 공개 / 실 사용)
  5. 권장 패치 + 우선순위
"""

user = """
CVE: CVE-2024-XXXX
description: Apache HTTP Server 2.4.x 의 mod_rewrite 의 ...
CVSS: 9.8 (Critical)
"""
```

### 3.2 LLM 의 SAST (Static Analysis)

```python
# 코드 분석 의 LLM
def analyze_code(code, language):
    return llm.complete(
        system="당신은 코드 보안 분석가. CWE 기반 vuln 찾기.",
        user=f"""
        다음 {language} 코드 의 보안 약점:
        {code}

        분석:
        1. 발견 vuln 의 CWE 매핑
        2. 익스플로잇 가능성
        3. 수정 권장 (diff 형식)
        """
    )
```

### 3.3 LLM 의 DAST (Dynamic Analysis)

```python
# Burp Suite + LLM 통합
def analyze_request_response(burp_req, burp_resp):
    return llm.complete(
        system="당신은 web 침투 테스터. Burp 의 request/response 분석.",
        user=f"""
        Request:
        {burp_req}

        Response:
        {burp_resp}

        분석:
        1. 가능한 vuln (SQLi / XSS / IDOR / 등)
        2. 다음 시도 페이로드 (3+)
        3. ATT&CK Technique 매핑
        """
    )
```

### 3.4 LLM 의 모의해킹 보조

```
시나리오:
  1. 학생 (또는 침투 테스터) 가 정찰 시작
  2. nmap 결과 → LLM 분석 → 다음 시도 추천
  3. 발견 vuln → LLM 의 exploit 가설 + 안전 페이로드
  4. PTES 의 각 단계 LLM 조언

본 lab 의 6v6 환경 + LLM 의 보조 운영:
  W05+ 의 AI 에이전트 (Claude Code / Bastion) 의 기반
```

### 3.5 sqlmap + LLM 통합

```python
# sqlmap 실행 후 LLM 의 결과 분석
sqlmap_output = subprocess.run(["sqlmap", "-u", target_url, "--batch"], capture_output=True)

llm.analyze(
    system="sqlmap 결과 분석",
    user=f"sqlmap 출력:\n{sqlmap_output.stdout}\n\n분석 + 다음 시도 추천."
)
```

### 3.6 본 lab 의 W05+ 의 직접 선수

본 주차 의 LLM 활용 = AI 에이전트 (W05) 의 기반:
- Claude Code 가 자동 코드 분석 + vuln fix
- Bastion 가 자동 침투 시도 + 결과 분석
- W08 의 AI Agent Hijacking (악의적 활용)

### 3.7 윤리적 한계

```
✅ 허용:
  - 6v6 환경 + 본인 환경의 vuln 분석
  - 학습 목적 의 exploit 가설
  - Penetration testing 의 보조 (RoE 내)

❌ 금지:
  - 외부 시스템 의 무허가 vuln 분석
  - 실 exploit 코드 의 외부 공개
  - 0-day 의 무책임한 공유 (Responsible Disclosure 위반)
```

---

## 4. ATT&CK + 표준 매핑

### 4.1 SOC 의 LLM 활용 표준

```
- Microsoft Security Copilot (2023) — Microsoft 의 SOC AI
- IBM watsonx.ai for Cybersecurity
- Anthropic 의 Claude for Government (2024)
- 한국 안랩 / 이글루시큐리티 의 AI SOC (2024-2025)
```

### 4.2 MITRE ATLAS 의 본 주차 매핑

- **AML.T0024**: Exfiltration via ML Inference API (LLM 의 token 비용)
- **AML.T0048**: Backdoor ML Model (W08 학습)

### 4.3 OWASP Top 10 for LLM 본 주차 매핑

- **LLM02**: Insecure Output Handling — LLM 의 룰 생성 시 검증 부족
- **LLM03**: Training Data Poisoning — W08 학습
- **LLM06**: Sensitive Information Disclosure — alert 의 PII 의 LLM 노출
- **LLM09**: Overreliance — LLM 의 hallucination 신뢰

---

## 5. R/B/P 시나리오 — LLM 활용 SOC

```mermaid
graph LR
    SOC["🛡️ SOC<br/>(secuops 의 운영자)"]
    LOGS["📋 Wazuh + Suricata + ModSec<br/>1000+ alert / 일"]

    LLM["🧠 LLM (Ollama / Bastion)<br/>4 패턴 분석"]

    R["🔴 attacker<br/>(W08-W10 의 LLM 공격)"]

    B1["🔵 Triage 자동화"]
    B2["🔵 Correlation"]
    B3["🔵 Enrichment + CTI"]
    B4["🔵 룰 자동 생성"]

    P["🟣 SOC 효율 측정<br/>(alert 처리 시간 / FP rate)"]

    SOC --> LOGS --> LLM
    LLM --> B1
    LLM --> B2
    LLM --> B3
    LLM --> B4
    B1 --> P
    B2 --> P
    B3 --> P
    B4 --> P

    R -.->|W08+ 학습| LLM

    style LLM fill:#bc8cff,color:#fff
    style R fill:#f85149,color:#fff
    style P fill:#bc8cff,color:#fff
```

---

## 6. 실습 1~5

### 실습 1 — LLM 의 alert triage (zero-shot)

```bash
ssh 6v6-bastion '
# 실 Wazuh alert 의 LLM 분석
ALERT=$(sudo tail -1 /var/ossec/logs/alerts/alerts.json | head -1)
echo "Alert: $ALERT" | head -c 200

curl -s -X POST -H "X-API-Key: ccc-api-key-2026" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"다음 Wazuh alert 를 한국어로 5W + 위험도 + 권장으로 분석: $ALERT\", \"agent\":\"master\"}" \
    http://localhost:9100/chat 2>&1 | head -50
'
```

### 실습 2 — LLM 의 Sigma 룰 자동 생성

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b",
  "prompt": "다음 시나리오의 Sigma rule YAML 작성:\n\n시나리오: SSH 의 5+ failed login from same IP in 60 seconds.\n\n형식 (YAML):\n  title: ...\n  id: ...\n  description: ...\n  tags:\n    - attack.credential_access\n    - attack.t1110.001\n  logsource:\n    product: linux\n    service: sshd\n  detection:\n    selection:\n      ...\n    timeframe: 60s\n    condition: ...\n  falsepositives:\n    - ...\n  level: high",
  "stream": false
}' | jq -r .response | head -30
```

### 실습 3 — LLM 의 Wazuh 룰 자동 생성

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b",
  "prompt": "다음 시나리오의 Wazuh XML rule 작성 (id 100400 / level 12):\n\n시나리오: ModSec 의 941100 (XSS) 매치가 60 초에 3 건 이상 같은 src_ip → level 12 alert.\n\n형식:\n<group name=...>\n  <rule id=... level=...>\n    <if_sid>...</if_sid>\n    <field name=...>...</field>\n    <description>...</description>\n  </rule>\n</group>",
  "stream": false
}' | jq -r .response | head -30
```

### 실습 4 — LLM 의 CVE 분석

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b",
  "prompt": "다음 CVE 를 한국어로 분석. 응답 5 항목 (핵심 / CVSS 의미 / 영향 / 익스플로잇 가용성 / 권장 패치):\n\nCVE: CVE-2024-XXXX (가상)\ndescription: Apache HTTP Server 2.4.x 의 mod_rewrite 의 buffer overflow → RCE\nCVSS: 9.8 (Critical)\nattack_vector: Network",
  "stream": false
}' | jq -r .response | head -30
```

### 실습 5 — LLM 의 모의해킹 보조

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b",
  "prompt": "당신은 학습 환경의 침투 테스트 보조 AI.\n\n현재 상황:\n- target: juice.6v6.lab (학습 환경의 OWASP Juice Shop)\n- 정찰 결과: REST API + JWT 인증 + ModSec WAF 가동\n- 발견 endpoint: /api/Users (200 응답)\n\n다음 시도 권장 3 + 각 시도의 ATT&CK Technique 매핑.",
  "stream": false
}' | jq -r .response | head -30
```

---

## 7. 한국 사례 + 표준

### 7.1 KISA 의 AI SOC

```
2024-2025 한국 의 AI SOC 도입 가속:
  - 안랩 V3 AI
  - 이글루시큐리티 의 AI 분석
  - SK인포섹 의 LLM 통합
  - 국가정보원 의 AI 사이버 위협 분석
```

### 7.2 ISMS-P 2.10.7 + AI

```
2.10.7 보안위협 대응 의 AI 자동화:
  - LLM 의 alert triage
  - 자동 IR 의 일부
  - 분기 review 의 AAR (W14 secuops 참조)
```

---

## 8. 과제

### A. LLM 의 alert 분석 매트릭스 (필수, 40점)

본인 환경의 10+ Wazuh alert × 4 패턴 (Triage / Correlation / Enrichment /
Reporting) 의 LLM 응답 quality 표.

### B. LLM 의 룰 생성 + 검증 (심화, 30점)

본인 작성 3 시나리오 의 Sigma / Wazuh / Suricata 룰 LLM 생성 + syntax 검증 +
실 환경 적용 (after human review).

### C. 모의해킹 보조 시뮬 (정성, 30점)

본 6v6 환경 의 1 vuln (예: SQLi on dvwa.6v6.lab) 의 침투 시도 + 각 step 의 LLM
조언 + 결과 보고.

---

## 9. 평가 기준

| 항목 | 비중 |
|------|------|
| alert 분석 (A) | 40% |
| 룰 생성 (B) | 30% |
| 모의해킹 보조 (C) | 30% |

---

## 10. 핵심 정리 (10 줄)

1. **SOC 의 LLM 활용 4 패턴** — Triage / Correlation / Enrichment / Reporting
2. **alert → LLM → 의사결정** flow (자동 ack / SOC / 자동 IR)
3. **token 비용** — 클라우드 vs 로컬 의 큰 차이 → 로컬 권장
4. **룰 자동 생성** — Sigma (표준) / Wazuh XML / Suricata / ModSec / YARA
5. **룰 검증 필수** — LLM hallucination → 자동 lint + 사람 review + dry-run
6. **CVE 의 LLM 분석** — CVSS / 영향 / 익스플로잇 가용성 / 권장 패치
7. **SAST / DAST** 의 LLM 통합 — Burp + sqlmap + LLM
8. **모의해킹 보조** — PTES 의 각 단계 LLM 조언 (W05+ 의 AI 에이전트 기반)
9. **OWASP Top 10 for LLM** — LLM02 / LLM03 / LLM06 / LLM09 매핑
10. **W05 (AI 에이전트 1)** 다음 주차 — 에이전트 + Claude Code + 하네스
