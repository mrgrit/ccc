# Week 03: 프롬프트 엔지니어링 for 보안

## 학습 목표
- 프롬프트 엔지니어링의 핵심 기법을 익힌다
- 보안 로그 분석용 프롬프트를 설계할 수 있다
- 취약점 설명 및 대응 방안 생성 프롬프트를 작성할 수 있다
- Few-shot, Chain-of-Thought 기법을 보안 업무에 적용할 수 있다

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

# Week 03: 프롬프트 엔지니어링 for 보안

## 학습 목표
- 프롬프트 엔지니어링의 핵심 기법을 익힌다
- 보안 로그 분석용 프롬프트를 설계할 수 있다
- 취약점 설명 및 대응 방안 생성 프롬프트를 작성할 수 있다
- Few-shot, Chain-of-Thought 기법을 보안 업무에 적용할 수 있다

---

## 1. 프롬프트 엔지니어링이란?

LLM에 전달하는 입력(프롬프트)을 설계하여 원하는 출력을 이끌어내는 기술이다.
좋은 프롬프트 = 좋은 결과이다.

### 프롬프트의 구성요소

| 요소 | 설명 | 예시 |
|------|------|------|
| **역할** | AI의 전문 분야 설정 | "SOC 분석가로서" |
| **맥락** | 배경 정보 제공 | "Wazuh SIEM에서 수집된 로그" |
| **작업** | 구체적인 요청 | "위협 수준을 평가하라" |
| **형식** | 출력 형태 지정 | "JSON으로 응답하라" |
| **제약** | 제한 조건 | "200자 이내로" |

---

## 2. 핵심 프롬프트 기법

> **이 실습을 왜 하는가?**
> "프롬프트 엔지니어링 for 보안" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 Zero-shot (예시 없이 요청)

> **실습 목적**: LLM에게 도구(Tool)를 제공하여 자율적으로 명령을 실행하고 결과를 분석하는 에이전트 동작을 체험하기 위해 수행한다
>
> **배우는 것**: Tool Calling의 구조(function name, arguments)와 LLM이 어떤 도구를 선택하는지의 판단 과정을 이해한다
>
> **결과 해석**: tool_calls 필드에 호출할 함수명과 인자가 포함되며, 함수 실행 결과를 다시 LLM에 전달하여 최종 분석을 얻는다
>
> **실전 활용**: 보안 자동 점검 에이전트 개발, SOAR 플랫폼의 AI 기반 자동 대응 시나리오 구축에 활용한다

예시 없이 역할(system)과 질문(user)만으로 보안 로그를 분석시킨다. python3 파이프로 응답 본문만 추출한다.

```bash
# Zero-shot: 예시 없이 LLM에 직접 분석 요청
# python3 파이프: JSON 응답에서 content 필드만 추출
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석가로서 보안 이벤트를 분석합니다."},
      {"role": "user", "content": "다음 로그를 분석하세요:\nMar 27 10:15:33 web sshd[1234]: Failed password for root from 192.168.1.100 port 54321 ssh2"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.2 Few-shot (예시 포함)

이전 분석 예시를 assistant 메시지로 포함시켜 LLM이 동일한 형식과 기준으로 응답하도록 유도한다.

```bash
# Few-shot: user/assistant 쌍으로 분석 예시를 제공
# 마지막 user 메시지가 실제 분석 대상
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 로그를 분석하여 위협 수준을 평가하세요."},
      {"role": "user", "content": "로그: Failed password for admin from 10.0.0.5"},
      {"role": "assistant", "content": "위협수준: LOW\n분석: 단일 실패 시도. 내부 IP에서 발생. 사용자 실수 가능성 높음."},
      {"role": "user", "content": "로그: Failed password for root from 203.0.113.50 (5회 반복)"},
      {"role": "assistant", "content": "위협수준: HIGH\n분석: 외부 IP에서 root 계정 반복 시도. 브루트포스 공격 의심."},
      {"role": "user", "content": "로그: Accepted publickey for deploy from 10.20.30.80 port 22"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.3 Chain-of-Thought (단계적 추론)

시간순 이벤트를 제공하고 "단계별로 추론하세요"라는 지시로 LLM이 사고 경위를 논리적으로 재구성하도록 유도한다.

```bash
# Chain-of-Thought: "단계별로 추론하세요" 지시로 논리적 분석 유도
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 분석가입니다. 단계별로 추론하세요."},
      {"role": "user", "content": "다음 이벤트들을 시간순으로 분석하고, 단계별로 사고 경위를 추론하세요:\n\n1. 10:00 - web 서버에서 SQL 에러 로그 급증\n2. 10:05 - DB 서버에서 비정상 쿼리 실행\n3. 10:10 - DB 서버에서 외부로 대량 데이터 전송\n4. 10:15 - web 서버 접근 로그에 union select 패턴\n\n단계별로 추론하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 3. 보안 업무별 프롬프트 템플릿

### 3.1 로그 분석 프롬프트

```
[System]
당신은 SOC(Security Operations Center) Tier-2 분석가입니다.
아래 보안 로그를 분석하고 다음 형식으로 응답하세요:

- 이벤트 요약: (한 줄)
- 위협 수준: (CRITICAL/HIGH/MEDIUM/LOW/INFO)
- 공격 유형: (해당 시)
- 영향 범위: (영향받는 시스템)
- 대응 권고: (즉시 수행할 조치)

[User]
{로그 데이터 입력}
```

### 3.2 취약점 설명 프롬프트

```
[System]
보안 교육 전문가로서 취약점을 초보자도 이해할 수 있게 설명합니다.

[User]
다음 CVE를 분석해주세요:
- CVE ID: {CVE-YYYY-NNNNN}
- 영향 소프트웨어: {소프트웨어명}

다음 형식으로 응답:
1. 취약점 요약 (2줄)
2. 위험도와 이유
3. 공격 시나리오 (비유 사용)
4. 패치/대응 방법
```

### 3.3 보안 보고서 생성 프롬프트

```
[System]
CISO에게 보고할 보안 인시던트 보고서를 작성합니다.
비전문가도 이해할 수 있는 언어로 작성하되, 기술적 세부사항도 포함합니다.

[User]
다음 정보로 인시던트 보고서를 작성하세요:
- 발생 시각: {시각}
- 영향 시스템: {시스템}
- 공격 유형: {유형}
- 현재 상태: {상태}
- 수행 조치: {조치}
```

---

## 4. 구조화된 출력

### 4.1 JSON 형식 요청

LLM 응답을 JSON 형식으로 받아 자동화 파이프라인에서 파싱할 수 있게 한다. temperature를 0으로 설정하면 일관된 구조를 얻기 쉽다.

```bash
# JSON 구조화 출력: 자동화 연동용 (severity, type, source_ip, action)
# temperature 0: 일관된 JSON 구조를 보장
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 이벤트를 분석하고 반드시 JSON 형식으로만 응답하세요."},
      {"role": "user", "content": "다음 로그를 분석하세요. JSON으로 응답: {\"severity\": \"\", \"type\": \"\", \"source_ip\": \"\", \"action\": \"\"}\n\nMar 27 14:22:01 secu suricata[5678]: [1:2001219:20] ET SCAN Potential SSH Scan from 45.33.32.156"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 테이블 형식 요청

마크다운 테이블 형식을 지정하면 보고서에 바로 삽입할 수 있는 구조화된 출력을 얻을 수 있다.

```bash
# 마크다운 테이블 형식 출력 요청
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "OWASP Top 10 (2021)을 마크다운 테이블로 정리해주세요. 컬럼: 순위, 취약점명, 설명(한 줄), 위험도"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: 로그 분석 프롬프트 비교

```bash
# 나쁜 프롬프트
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "이 로그 분석해줘: Failed password for root from 203.0.113.50"}
    ]
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

echo "---"

# 좋은 프롬프트
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC Tier-2 분석가입니다. 위협수준(CRITICAL/HIGH/MEDIUM/LOW), 공격유형, 대응방안을 포함하여 분석하세요."},
      {"role": "user", "content": "환경: 웹 서버(Ubuntu 22.04), 인터넷 노출\n로그:\nMar 27 10:15:33 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2\nMar 27 10:15:35 web sshd[1234]: Failed password for root from 203.0.113.50 port 54322 ssh2\nMar 27 10:15:37 web sshd[1234]: Failed password for root from 203.0.113.50 port 54323 ssh2\n(총 50회 반복)"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: CVE 분석 프롬프트

CVE 번호를 LLM에게 전달하여 요약, 비유 설명, 공격 과정, 대응 방법을 자동 생성시킨다.

```bash
# CVE-2021-44228(Log4Shell) 분석: 5개 항목 형식 지정
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 교육 전문가입니다. 대학 1학년 학생도 이해할 수 있게 설명하세요."},
      {"role": "user", "content": "CVE-2021-44228 (Log4Shell)을 설명해주세요.\n\n형식:\n1. 한 줄 요약\n2. 비유로 설명 (일상 생활 비유)\n3. 공격 과정 (단계별)\n4. 대응 방법\n5. 교훈"}
    ],
    "temperature": 0.5
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 대응 플레이북 자동 생성

공격 상황 정보를 전달하면 LLM이 실제 명령어를 포함한 단계별 대응 플레이북을 생성한다.

```bash
# SSH 브루트포스 대응 플레이북 자동 생성
# 실제 실행 명령어를 포함한 단계별 절차 요청
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "인시던트 대응 전문가입니다. 구체적이고 실행 가능한 대응 절차를 작성합니다."},
      {"role": "user", "content": "SSH 브루트포스 공격이 탐지되었습니다.\n소스 IP: 203.0.113.50\n대상: web 서버 (10.20.30.80)\n시도 횟수: 500회/10분\n\n대응 플레이북을 단계별로 작성하세요. 각 단계에 실제 명령어를 포함하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 프롬프트 엔지니어링 팁

### 좋은 프롬프트의 특징

1. **구체적**: "분석해줘" → "위협수준, 공격유형, 대응방안을 포함하여 분석"
2. **맥락 제공**: 환경, 시스템 정보, 배경을 포함
3. **형식 지정**: 출력 형식을 명확히 지정 (JSON, 테이블, 단계별)
4. **역할 부여**: 전문가 역할을 system 메시지로 설정
5. **예시 포함**: Few-shot으로 원하는 출력 패턴 제시

### 나쁜 프롬프트 vs 좋은 프롬프트

| 나쁜 프롬프트 | 좋은 프롬프트 |
|-------------|-------------|
| "이 로그 봐줘" | "SOC 분석가로서 이 Wazuh 알림의 위협수준을 평가하세요" |
| "보안 강화해" | "Ubuntu 22.04 SSH 서버의 보안 설정 5가지를 설명하세요" |
| "해킹 방법" | "SQL Injection의 원리와 방어 방법을 교육 목적으로 설명하세요" |

---

## 핵심 정리

1. 프롬프트 엔지니어링은 역할+맥락+작업+형식+제약으로 구성한다
2. Few-shot으로 예시를 제공하면 더 정확한 출력을 얻는다
3. Chain-of-Thought로 복잡한 보안 분석의 추론 과정을 이끌어낸다
4. JSON/테이블 형식 지정으로 자동화에 활용 가능한 구조화된 출력을 얻는다
5. temperature를 낮게 설정하면 보안 분석에 적합한 일관된 답변을 얻는다

---

## 다음 주 예고
- Week 04: LLM 기반 로그 분석 - Wazuh 알림을 LLM으로 분석

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
