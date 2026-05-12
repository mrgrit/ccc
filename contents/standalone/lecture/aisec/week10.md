# W10 — AI Safety (3): 에이전트 위협 / LLM Red Teaming / 평가 프레임워크

> 본 주차는 **인공지능보안 (입문)** 의 10 주차이며, AI Safety 시리즈 (W08-W10) 의 마지막 주차이다.
> W08 (개론·악성fine-tune·injection·poisoning) + W09 (jailbreak·adversarial·RAG/KG 보안) 의 학습 위에,
> 본 주차 는 **에이전트 의 추가 위협** + **LLM Red Teaming** + **평가 framework** 의 마무리.

---

## 본 주차 의도

지난 2 주차 의 학습 — LLM 의 **모델 측면** 의 안전.

본 주차 는 **에이전트 측면** 의 안전 — LLM 의 단발 호출 의 안전 만으로 부족 한 에이전트 의 고유 위협 의 학습.

학습 목표:

1. **에이전트 위협** — multi-turn / tool 호출 / 자율 cycle 의 고유 위험.
2. **LLM Red Teaming** — 산업 표준 의 체계.
3. **평가 framework** — 모델 / 에이전트 의 정량 평가 의 도구.

본 주차 후 학생 은 본인 의 에이전트 의 **공식 평가** 의 첫 step 의 가능 해야 함.

---

## 1 차시 — 에이전트 의 고유 위협

### 1-1. 에이전트 의 단일 LLM 대비 의 추가 위험

| 위험 | 단일 LLM | 에이전트 |
|------|----------|----------|
| **multi-turn 누적** | 1 turn 만 | N turn — context 의 오염 의 누적 |
| **tool 호출** | 응답 만 | 실 시스템 의 변경 |
| **자율 cycle** | 사용자 의 매번 confirm | 무인 의 의사결정 |
| **외부 데이터** | user input 만 | RAG / KG / web / file |
| **메모리** | session 만 | 영구 의 episodic / semantic |
| **체인 효과** | 1 응답 의 영향 | 다단계 의 cascading |

### 1-2. OWASP LLM08 — Excessive Agency

OWASP Top 10 for LLM 의 LLM08:

> 에이전트 가 운영자 의 의도 보다 **과도 한 권한** / **과도 한 자율** / **과도 한 기능** 의 부여 의 결과 의 사고.

3 종 의 over-X:

- **Excessive Permissions** — tool 의 RBAC 의 약함.
- **Excessive Autonomy** — confirm 의 부족.
- **Excessive Functionality** — 불필요 한 tool 의 노출.

### 1-3. 에이전트 의 공격 vector

#### (a) **Multi-turn Persuasion**

여러 turn 의 누적 의 점진 의 안전 의 우회.

```
turn 1: 일반 질문
turn 2: 가설 시나리오 의 빌드
turn 3: 가설 의 정당 화
turn 4: 가설 의 구체 화
turn 5: 본 의 unsafe 응답
```

#### (b) **Tool Abuse**

LLM 의 tool 호출 의 인자 의 조작:

```
사용자: 다음 URL 의 내용 요약: http://internal.6v6.lab/secret
LLM 의 tool: WebFetch(url=...) → 비밀 의 노출
```

#### (c) **Context Cascade**

이전 turn 의 출력 의 다음 turn 의 input — 의도 한 prompt 의 누적.

#### (d) **Memory Poisoning**

agent 의 영구 memory 의 변조 → 다음 세션 의 영향.

#### (e) **Hallucinated Tool**

존재 하지 않는 tool 의 호출 의 시도 → 사용자 의 fallback 의 의도 변경.

#### (f) **Confused Deputy**

agent 가 사용자 의 권한 의 사용 의 의도 하지 않은 작업 수행.

### 1-4. CCC 의 Bastion 의 에이전트 안전

memory 의 기록 (project_bastion_kg_integration.md):

- `auto_approve: False` — 모든 위험 작업 의 사용자 의 confirm.
- `approval_mode: normal | danger_danger | danger_danger_danger` — 위험 단계 의 권한 의 escalation.
- `INTERNAL_IPS` 의 화이트리스트 — 외부 의 거부.
- KG 의 모든 chat 의 record — 사후 audit.

```python
# packages/bastion/agent.py (예 pseudocode)
SAFE_TARGETS = ["192.168.0.0/24", "*.6v6.lab"]

def guard_target(target):
    if not is_in_subnet(target, SAFE_TARGETS):
        raise SafetyError(f"Target {target} 학습 환경 외부 — 거부")
```

### 1-5. 에이전트 안전 의 운영 원칙

1. **principle of least privilege** — 최소 권한.
2. **explicit confirm** — 위험 작업 의 사용자 confirm.
3. **audit trail** — 모든 action 의 기록.
4. **timeout / budget** — step / token / time 의 상한.
5. **kill switch** — 즉시 중단 의 mechanism.
6. **safe defaults** — 거부 의 기본.
7. **separation of concerns** — agent 별 역할 분담.

---

## 2 차시 — LLM Red Teaming

### 2-1. LLM Red Teaming 의 정의

> **LLM Red Teaming** = LLM / 에이전트 의 안전 / robustness / alignment 의 **적대 적 평가** 의 체계.

전통 적 의 IT 의 red team (침투 테스트) 의 LLM 의 확장. 그러나 차이:

- **target** — 단일 시스템 의 vuln 이 아닌 모델 의 거동 의 평가.
- **method** — exploit 의 사용 의 의 아니라 prompt / 시나리오 의 사용.
- **outcome** — RCE 의 데모 의 아니라 **harm rate** / **refusal rate** / **bias** 의 측정.

### 2-2. Red Teaming 의 체계 — Microsoft AI Red Team

Microsoft 2022 ~ 발간 의 PyRIT (Python Risk Identification Toolkit) 의 분류:

| 단계 | 의의 |
|------|------|
| 1. **Plan** | 평가 의 scope / 위험 / 기준 의 사전 정의 |
| 2. **Generate** | adversarial prompts 의 의 생성 (manual + auto) |
| 3. **Orchestrate** | 실 모델 의 호출 + 응답 수집 |
| 4. **Score** | 응답 의 평가 (자동 + 인간) |
| 5. **Report** | 발견 의 정리 + 권장 |

### 2-3. Red Teaming 의 방법론

#### (a) **Manual**

- 사람 의 창의 적 prompt.
- 다양한 background / 전문 분야.
- 윤리 / 다양성 / 문화 의 검토.

#### (b) **Automated**

- PAIR / TAP / AutoDAN (W09 의 학습).
- benchmark dataset 의 대량 평가.

#### (c) **Hybrid**

- 인간 의 seed prompt → 자동 의 변형.
- 자동 의 발견 → 인간 의 검토.

### 2-4. 산업 의 Red Teaming 표준

#### (a) **MLCommons AI Safety v0.5** (2024)

- 산업 의 표준 benchmark.
- 7 위험 의 평가 — toxicity / bias / privacy / 등.

#### (b) **AILuminate** (MLCommons 2024)

- safe / unsafe / questionable 의 자동 분류.

#### (c) **DEF CON Generative Red Team Challenge** (2023~)

- 4000+ hacker 의 대규모 평가.
- White House 의 후원.

#### (d) **NIST GenAI Red Team Pilot** (2024)

- 정부 의 표준 의 마련.

#### (e) **EU AI Act** 의 Red Teaming 의무 (2024)

- High-risk AI 의 conformity assessment 의 일부.

### 2-5. CCC 의 자체 Red Teaming

CCC 의 학습 환경 의 R5 main 의 학습 loop (memory 의 기록):

- 12 attack courses 의 attack-ai / battle-ai 등 의 prompt catalog.
- 매 chat 의 task_outcome 의 KG anchor 의 기록.
- 4940+ graph nodes / 5338+ history anchors 의 누적 (Bastion 의 /health 의 응답).

이 모든 의 자체 red teaming 의 데이터 의 paper §7 의 source.

### 2-6. Red Teaming 의 운영 의 윤리

- **인가** — 사전 의 명시 적 동의.
- **scope 의 명시** — 평가 범위.
- **outcome 의 비공개 / 공개** 의 명시.
- **harm 의 최소 화** — 평가 의 자체 의 위험.
- **responsible disclosure** — 발견 의 vendor 의 사전 통보.

---

## 3 차시 — 평가 framework

### 3-1. 평가 의 분류

| 분류 | 의의 | 예 |
|------|------|----|
| **Capability** | 모델 의 기본 능력 | MMLU / HellaSwag |
| **Truthfulness** | 사실 응답 의 정확 | TruthfulQA |
| **Safety** | 위험 응답 의 거부 | HarmBench |
| **Bias** | 편향 의 측정 | BBQ / BOLD |
| **Robustness** | 변형 의 응답 의 일관성 | AdvGLUE |
| **Alignment** | 인간 의 가치 의 일치 | HHH evaluation |

### 3-2. 주요 benchmark

#### (a) **MMLU** (Hendrycks 2020)

- 57 의 다양 한 도메인 의 multiple-choice.
- 모델 의 일반 의 능력 의 표준.
- 2024 의 SOTA — Claude 3.5 Sonnet 의 88.7%.

#### (b) **HellaSwag** (Zellers 2019)

- 상식 / 추론 의 multiple-choice.

#### (c) **TruthfulQA** (Lin 2022)

- 모델 의 거짓 / 잘못 된 통념 의 거부.

#### (d) **GSM8K** (Cobbe 2021)

- 초등 수학 의 reasoning.

#### (e) **HumanEval** (Chen 2021)

- code 의 생성 의 평가.

#### (f) **MT-Bench / Chatbot Arena**

- 인간 의 평가 의 multi-turn 의 대화.

#### (g) **Safety benchmarks**

- AdvBench (520 prompts, Zou 2023)
- HarmBench (400 prompts, Mazeika 2024)
- JailbreakBench (100 prompts, Chao 2024)
- ToxicChat (Lin 2023)
- TrustLLM (Sun 2024)

### 3-3. 에이전트 의 평가

#### (a) **AgentBench** (Liu 2023)

- 다양 한 도메인 의 에이전트 의 평가.

#### (b) **GAIA** (Mialon 2024)

- General AI Assistant 의 benchmark.

#### (c) **SWE-bench** (Jimenez 2024)

- 실 software engineering task 의 평가.

#### (d) **τ-bench** (Yao 2024)

- 회의 / 회복 의 에이전트 의 평가.

### 3-4. CCC 의 자체 평가

CCC 의 학습 환경 의 평가 KPI:

- **lab pass rate** — 학생 의 lab 의 합격 률.
- **verify success** — 자동 채점 의 통과.
- **deferred queue** — 모델 의 한계 의 격리.
- **R5 main** — 12 courses × N weeks × M steps 의 retry.

### 3-5. 평가 의 도구

#### (a) **lm-evaluation-harness** (EleutherAI)

- Python 의 표준 evaluation framework.
- pip install lm-eval.
- 200+ benchmark.

#### (b) **HELM** (Stanford)

- Holistic Evaluation of Language Models.

#### (c) **PyRIT** (Microsoft)

- 안전 평가 의 framework.

#### (d) **OpenCompass** (Shanghai)

- 70+ benchmark 의 통합.

#### (e) **garak** (Leon Derczynski 2023)

- LLM 의 vulnerability scanner.

### 3-6. LLM-as-Judge

평가 의 사람 의 비용 의 LLM 의 자동 대체:

- **GPT-4-as-judge** — Zheng 2024 의 MT-Bench.
- **자체 judge** — Anthropic 의 Claude 의 자체 평가.
- **JudgeLM** — judge 의 전용 fine-tune.

장점: 빠름 / 저렴 / 일관.
단점: 편향 의 가능 / 자기 의 모델 의 favoring.

### 3-7. R/B/P — 본 주차 의 시나리오

```mermaid
flowchart LR
    subgraph Red [🔴 Red — 평가 의 적]
        R1[adversarial prompts]
        R2[multi-turn persuasion]
        R3[tool abuse]
    end

    subgraph Blue [🔵 Blue — 평가 의 보호]
        B1[approval_mode]
        B2[INTERNAL_IPS guard]
        B3[KG audit]
    end

    subgraph Purple [🟣 Purple — Red Teaming]
        P1[PyRIT plan]
        P2[Generate prompts]
        P3[Orchestrate Bastion]
        P4[Score harm rate]
        P5[Report]
    end

    R1 --> P2
    R2 --> P2
    R3 --> P2
    B1 -.-> P3
    B2 -.-> P3
    B3 -.-> P3
    P1 --> P2 --> P3 --> P4 --> P5
```

### 3-8. 본 주차 의 hands-on

본 주차 의 lab 의 5 step (lab yaml 참조):

1. **multi-turn persuasion** 의 시뮬 — 5 turn 의 누적 의 응답 변화.
2. **excessive agency** 의 시뮬 — tool 의 인자 의 우회 시도.
3. **benchmark 의 미니 실행** — TruthfulQA 의 5 sample 의 응답.
4. **LLM-as-judge** 의 미니 demo — gemma3:4b 의 응답 의 다른 모델 의 평가.
5. **CCC 의 R5 의 평가 결과** 의 가시화 — results/retest 의 학습.

---

## 본 주차 의 정리

1. **에이전트 의 6 추가 위협** — multi-turn / tool / cycle / 외부 / memory / cascade.
2. **OWASP LLM08 Excessive Agency** — permissions / autonomy / functionality.
3. **LLM Red Teaming** 의 5 단계 — Plan / Generate / Orchestrate / Score / Report.
4. **표준** — MLCommons / AILuminate / DEF CON / NIST / EU AI Act.
5. **benchmark** — MMLU / HellaSwag / TruthfulQA / GSM8K / HumanEval / safety benchmarks.
6. **에이전트 평가** — AgentBench / GAIA / SWE-bench / τ-bench.
7. **도구** — lm-evaluation-harness / HELM / PyRIT / garak.
8. **LLM-as-Judge** 의 장단점.

---

## 자기 점검

- 에이전트 의 6 추가 위협 의 응답 가능?
- OWASP LLM08 의 3 종 의 응답 가능?
- Red Teaming 의 5 단계 의 응답 가능?
- benchmark 5 의 응답 가능?
- LLM-as-Judge 의 장단점 의 응답 가능?

---

## 다음 주차

**W11 — 자율보안 (1): 개요 / 강화학습 / 스케줄러·왓처**

- 자율보안 시스템 의 개요 — 본인 의 에이전트 의 자율 운영.
- 강화학습 (RL) 의 보안 의 적용.
- 스케줄러 / 왓처 의 패턴.

본 주차 까지 의 모델 의 안전 의 학습 → 다음 의 자율 시스템 의 안전 으로 의 도약.
