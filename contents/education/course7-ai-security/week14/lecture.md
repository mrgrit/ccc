# Week 14: RL Steering

## 학습 목표
- 강화학습 보상 함수(Reward Function)의 설계 원칙을 이해한다
- 보상 함수로 AI 에이전트의 행동을 통제하는 방법을 익힌다
- OpsClaw의 RL 시스템을 활용한 행동 조향(steering)을 실습한다
- 보상 해킹(reward hacking) 위험과 방지 방법을 이해한다

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

# Week 14: RL Steering

## 학습 목표
- 강화학습 보상 함수(Reward Function)의 설계 원칙을 이해한다
- 보상 함수로 AI 에이전트의 행동을 통제하는 방법을 익힌다
- OpsClaw의 RL 시스템을 활용한 행동 조향(steering)을 실습한다
- 보상 해킹(reward hacking) 위험과 방지 방법을 이해한다

---

## 1. RL Steering이란?

보상 함수를 설계하여 AI 에이전트의 행동을 원하는 방향으로 유도하는 기술이다.

### 핵심 아이디어

```
보상이 높은 행동 → 에이전트가 더 자주 선택
보상이 낮은 행동 → 에이전트가 회피
```

보안 관점에서:
- 안전한 행동에 높은 보상 → 에이전트가 안전하게 행동
- 위험한 행동에 패널티 → 에이전트가 위험 행동 회피

---

## 2. 보상 함수 설계

> **이 실습을 왜 하는가?**
> "RL Steering" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 보안 에이전트의 보상 요소

| 요소 | 높은 보상 | 낮은 보상/패널티 |
|------|----------|----------------|
| 작업 성공 | 명령 성공적 실행 | 실행 실패, 에러 |
| 안전성 | low risk 사용 | critical risk 남용 |
| 효율성 | 빠른 실행 | 불필요하게 느림 |
| 정확성 | 올바른 탐지 | 오탐(false positive) |
| 영향 최소화 | 읽기 전용 작업 | 파괴적 작업 |

### 2.2 보상 함수 예시

```python
def calculate_reward(task_result):
    """보안 에이전트 보상 함수"""
    reward = 0.0

    # 기본 성공/실패
    if task_result["success"]:
        reward += 1.0
    else:
        reward -= 0.5

    # 위험도에 따른 보상 조정
    risk_weights = {
        "low": 0.2,      # 안전한 작업은 소소한 보상
        "medium": 0.5,    # 중간 위험은 중간 보상
        "high": 1.0,      # 높은 위험을 성공하면 높은 보상
        "critical": 2.0   # 크리티컬 성공은 큰 보상
    }
    reward *= risk_weights.get(task_result["risk_level"], 0.1)

    # 파괴적 명령 패널티
    destructive = ["rm -rf", "DROP TABLE", "mkfs", "dd if="]
    if any(d in task_result.get("command", "") for d in destructive):
        reward -= 5.0     # 큰 패널티

    # 실행 시간 보너스 (10초 이내면 보너스)
    if task_result.get("duration_sec", 999) < 10:
        reward += 0.1

    return reward
```

---

## 3. 행동 통제 패턴

### 3.1 보수적 에이전트 (안전 우선)

```python
CONSERVATIVE_REWARDS = {
    "low_success": +1.0,
    "medium_success": +0.5,
    "high_success": +0.3,
    "critical_success": -0.5,    # critical은 성공해도 패널티!
    "any_failure": -2.0,
    "destructive": -10.0
}
```

### 3.2 적극적 에이전트 (탐색 우선)

```python
AGGRESSIVE_REWARDS = {
    "low_success": +0.1,
    "medium_success": +0.5,
    "high_success": +2.0,
    "critical_success": +5.0,    # 높은 위험 성공에 큰 보상
    "any_failure": -0.5,
    "new_discovery": +3.0        # 새로운 발견에 보너스
}
```

### 3.3 상황에 따른 전환

```
평시: 보수적 정책 → 안전한 모니터링
인시던트: 적극적 정책 → 빠른 정보 수집
복구: 보수적 정책 → 안정적 복구
```

---

## 4. OpsClaw RL 시스템 활용

### 4.1 현재 정책 확인

> **실습 목적**: AI 보안 테스트를 자동화하는 파이프라인을 구축하여 지속적 보안 검증 체계를 만들기 위해 수행한다
>
> **배우는 것**: 프롬프트 인젝션, 탈옥, 적대적 예제 테스트를 자동화하는 스크립트 작성법과, CI/CD에 통합하는 방법을 이해한다
>
> **결과 해석**: 자동 테스트의 통과/실패 비율로 AI 모델의 보안 수준을 정량적으로 평가한다
>
> **실전 활용**: AI 모델 업데이트 시 자동 보안 회귀 테스트, AI Red Team 자동화 도구 개발에 활용한다

현재 RL 정책(Q-테이블)을 조회하여 각 risk_level별 학습된 최적 전략을 확인한다.

```bash
# RL 정책 조회: 각 상태(agent_id + risk_level)별 Q-값 확인
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 4.2 보상 데이터 축적

```bash
# 다양한 risk_level의 태스크를 실행하여 보상 데이터 축적
PID="프로젝트_ID"

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname", "risk_level":"low"},
      {"order":2, "instruction_prompt":"uptime", "risk_level":"low"},
      {"order":3, "instruction_prompt":"ss -tlnp", "risk_level":"medium"},
      {"order":4, "instruction_prompt":"cat /etc/passwd", "risk_level":"medium"},
      {"order":5, "instruction_prompt":"last -20", "risk_level":"high"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 4.3 학습 및 추천 확인

```bash
# RL 학습 실행
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# risk_level별 추천 확인
for level in low medium high critical; do
  echo "--- $level ---"
  curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=$level" \
    -H "X-API-Key: opsclaw-api-key-2026"
  echo ""
done
```

---

## 5. 보상 해킹 (Reward Hacking)

에이전트가 보상을 최대화하기 위해 **의도하지 않은 방법**을 찾는 현상이다.

### 5.1 예시

| 보상 설계 | 해킹 행동 | 문제 |
|----------|----------|------|
| 작업 수 보상 | 무의미한 작업 반복 | 리소스 낭비 |
| 성공률 보상 | 쉬운 작업만 선택 | 어려운 문제 회피 |
| 탐지 수 보상 | 오탐 대량 생성 | 신호 대 잡음비 하락 |

### 5.2 방지 방법

```python
# 방법 1: 다목적 보상 (여러 지표 균형)
reward = 0.4 * success_score + 0.3 * safety_score + 0.2 * efficiency_score + 0.1 * novelty_score

# 방법 2: 보상 상한 (과도한 보상 방지)
reward = min(reward, MAX_REWARD)

# 방법 3: 사람 검증 (주기적 감사)
if random.random() < 0.1:  # 10% 확률로 사람 검증
    reward = human_evaluate(task_result)
```

---

## 6. 실습

### 실습 1: 보상 함수 설계

```bash
# LLM에게 보상 함수 설계를 요청
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "강화학습 보상 함수 설계 전문가입니다."},
      {"role": "user", "content": "보안 관제 AI 에이전트를 위한 보상 함수를 설계해주세요.\n\n에이전트 행동: 로그 분석, 취약점 스캔, 방화벽 규칙 변경, 서비스 재시작\n목표: 안전하게 위협을 탐지하고 대응하되, 서비스 가용성을 유지\n\n각 행동에 대한 보상/패널티를 Python 함수로 작성하세요. 보상 해킹 방지 로직도 포함하세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: 정책 변화 관찰

```bash
# 여러 차례 태스크 실행 후 학습하여 정책 변화 관찰

# 1차 실행 (low risk 위주)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"tasks":[{"order":1,"instruction_prompt":"date","risk_level":"low"},{"order":2,"instruction_prompt":"whoami","risk_level":"low"}],"subagent_url":"http://localhost:8002"}'

# 학습
curl -s -X POST http://localhost:8000/rl/train -H "X-API-Key: opsclaw-api-key-2026"

# 추천 확인
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 실습 3: 보상 해킹 시나리오 분석

LLM에게 보상 함수를 분석시켜 에이전트가 보상을 극대화하기 위해 악용할 수 있는 시나리오를 찾는다. 보상 해킹(reward hacking)은 AI 안전성의 핵심 과제이다.

```bash
# 보상 해킹 시나리오 분석: 보상 함수의 취약점 자동 식별
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "AI 안전성 연구자입니다."},
      {"role": "user", "content": "다음 보상 함수에서 가능한 보상 해킹 시나리오를 3가지 찾고 각각의 방지 방법을 제시하세요:\n\nreward = task_count * 0.1 + success_rate * 2.0 + alerts_detected * 0.5\n\n(task_count: 실행 태스크 수, success_rate: 성공률, alerts_detected: 탐지 알림 수)"}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. RL Steering의 미래

```
현재: 단순 Q-learning (상태-행동 테이블)
      ↓
발전: Deep RL (신경망 기반 정책)
      ↓
목표: RLHF (사람 피드백 기반 학습)
      ↓
비전: 자율 보안 에이전트의 안전한 행동 보장
```

---

## 핵심 정리

1. 보상 함수 설계로 에이전트의 행동 방향을 결정한다
2. 안전 우선(보수적) vs 탐색 우선(적극적) 정책을 상황에 따라 전환한다
3. 보상 해킹을 방지하기 위해 다목적 보상, 상한 설정, 사람 검증을 적용한다
4. OpsClaw의 RL train/recommend로 데이터 기반 행동 정책을 학습한다
5. RL Steering은 자율 AI 에이전트의 안전성을 보장하는 핵심 기술이다

---

## 다음 주 예고
- Week 15: 기말고사 - AI 보안 자동화 종합 과제

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
