# Week 14: RL Steering

## 학습 목표
- 강화학습 보상 함수(Reward Function)의 설계 원칙을 이해한다
- 보상 함수로 AI 에이전트의 행동을 통제하는 방법을 익힌다
- Bastion의 RL 시스템을 활용한 행동 조향(steering)을 실습한다
- 보상 해킹(reward hacking) 위험과 방지 방법을 이해한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 4. Bastion RL 시스템 활용

### 4.1 Bastion의 내부 학습 — 외부에서 관찰하는 방법

Bastion의 RL 상태(Q-table, 정책, 학습 이력)는 외부에 원시 형태로 노출되지 않는다.
외부에서 볼 수 있는 것은 **결과(선택된 Skill·Playbook과 /evidence 결과)**이다.
따라서 외부 관찰자는 증거를 바탕으로 학습 경향을 역추적한다.

### 4.2 다양한 위험도의 작업을 축적 (보상 신호 생성)

```bash
# 보상 신호가 풍부해지도록 여러 risk 수준의 작업을 Bastion에게 지시
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산에 대해 다음을 순서대로 실행해줘: (1) hostname, (2) uptime, (3) listening ports, (4) /etc/passwd 읽기, (5) 최근 로그인 20건. 각 단계의 risk를 표기하고 결과를 증거에 남겨줘"}'
```

### 4.3 증거 기반 학습 경향 관찰

```bash
# 증거에서 (skill, risk, exit_code) 분포 집계 — 정책 학습의 간접 관찰
curl -s "http://10.20.30.200:8003/evidence?limit=100" \
  | python3 -c "
import sys,json,collections
d=json.load(sys.stdin).get('evidence',[])
c=collections.Counter((e.get('skill'),e.get('risk'),e.get('exit_code',0)) for e in d)
for k,v in c.most_common(20): print(v,k)
"
```

만약 실습 환경에 Bastion의 RL 내부 상태를 확인하는 관리자 엔드포인트가 있다면
해당 환경 설정 파일을 따른다. 본 과정의 표준 설명은 외부 관찰 기반이다.

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
curl -s http://10.20.30.200:11434/v1/chat/completions \
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

### 실습 2: 반복 지시 → Bastion의 선택 경향 관찰

```bash
# 동일 의도를 여러 번 반복하면 Bastion이 어떤 Skill/Playbook을 일관되게 고르는지 관찰
for i in 1 2 3 4 5; do
  curl -s -X POST http://10.20.30.200:8003/ask \
    -H 'Content-Type: application/json' \
    -d '{"message": "web 자산의 기본 상태를 점검해줘"}' > /dev/null
done

# 증거에서 최근 5건의 선택된 skill/playbook 빈도
curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=20" \
  | python3 -c "
import sys,json,collections
d=json.load(sys.stdin).get('evidence',[])
c=collections.Counter(e.get('playbook') or e.get('skill') for e in d)
print(c.most_common(10))
"
```

동일 의도에 대해 같은 Skill/Playbook이 선택되는 비율이 높아질수록 정책이 수렴하고 있다는 신호이다.

### 실습 3: 보상 해킹 시나리오 분석

LLM에게 보상 함수를 분석시켜 에이전트가 보상을 극대화하기 위해 악용할 수 있는 시나리오를 찾는다. 보상 해킹(reward hacking)은 AI 안전성의 핵심 과제이다.

```bash
# 보상 해킹 시나리오 분석: 보상 함수의 취약점 자동 식별
curl -s http://10.20.30.200:11434/v1/chat/completions \
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
4. Bastion의 RL train/recommend로 데이터 기반 행동 정책을 학습한다
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
# URL: http://10.20.30.200:11434/v1/chat/completions

curl -s http://10.20.30.200:11434/v1/chat/completions \
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

### Bastion API 핵심 엔드포인트 요약

```
POST /ask / /chat        → 자연어 I/F
GET  /evidence            → 감사·학습 관찰용 증거
GET  /skills / /playbooks / /assets → 내부 인벤토리
```

---
---

> **실습 환경 검증 완료** (2026-03-28): Ollama 22모델(gemma3:12b ~5s), Bastion 50프로젝트, execute-plan 병렬, RL train/recommend

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://10.20.30.200:11434`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `packages/bastion/agent.py` | 메인 에이전트 루프 |
| `packages/bastion/skills.py` | 스킬 정의 |
| `packages/bastion/playbooks/` | 정적 플레이북 YAML |
| `data/bastion/experience/` | 수집된 경험 (pass/fail) |

**핵심 설정·키**

- `LLM_BASE_URL / LLM_MODEL` — Ollama 연결
- `CCC_API_KEY` — ccc-api 인증
- `max_retry=2` — 실패 시 self-correction 재시도

**로그·확인 명령**

- ``docs/test-status.md`` — 현재 테스트 진척 요약
- ``bastion_test_progress.json`` — 스텝별 pass/fail 원시

**UI / CLI 요점**

- 대화형 TUI 프롬프트 — 자연어 지시 → 계획 → 실행 → 검증
- `/a2a/mission` (API) — 자율 미션 실행
- Experience→Playbook 승격 — 반복 성공 패턴 저장

> **해석 팁.** 실패 시 output을 분석해 **근본 원인 교정**이 설계의 핵심. 증상 회피/땜빵은 금지.

---

## 실제 사례 (WitFoo Precinct 6 — RL Steering)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *RL (강화학습) 로 에이전트 행동을 조정하는 steering 기법* 학습 항목 매칭.

### RL Steering = "에이전트의 결정 가중치를 운영 데이터로 조정"

**RL Steering** 은 강화학습의 *고급 적용* 이다. 일반 RL 은 *시행착오로 학습* 하지만, RL Steering 은 — *이미 학습된 에이전트의 *결정 가중치 (decision weights)* 를 운영 데이터의 피드백으로 조정* 한다. 즉 *기존 정책을 미세 조정* 하는 작업.

dataset 의 392 Data Theft 사례에 적용하면 — Bastion 의 33개 skill 중 *어느 skill 을 어느 상황에 사용할지* 의 결정 가중치를 *운영 결과의 reward* 로 조정한다. 예를 들어 — *recon 단계 신호에는 `query_kg` skill 의 가중치를 +20%, exfil 단계 신호에는 `block_traffic` skill 의 가중치를 +30%* 같은 조정.

```mermaid
graph LR
    SIG["dataset 신호"]
    SIG --> AGENT["Bastion Agent"]
    AGENT -->|skill 선택<br/>(가중치 적용)| SKILL["33 skills 중 하나"]
    SKILL --> OUT["결과"]
    OUT -->|reward 측정| RL["RL Steering"]
    RL -->|가중치 조정| AGENT

    style RL fill:#cce6ff
```

**그림 해석**: 핵심은 *RL → Agent 화살표* — RL 이 Agent 의 *행동 가중치* 를 직접 조정. 이는 LLM fine-tune 보다 *훨씬 가벼운* 적응이다. fine-tune 은 모델 파라미터 수억 개를 수정하지만, RL Steering 은 *33개 skill 의 가중치만* 수정.

### Case 1: dataset reward function 정의 — "무엇이 좋은 결과인가"

| 결과 | reward | 의미 |
|---|---|---|
| 진짜 위협 차단 (true positive) | +10 | 강한 양의 reward |
| 정상 신호 정확 분류 (true negative) | +1 | 약한 양의 reward |
| 진짜 위협 놓침 (false negative) | -100 | 매우 강한 음의 reward |
| 정상 신호 false alarm (false positive) | -2 | 약한 음의 reward |

**자세한 해석**:

RL 의 학습 방향은 *reward function 이 결정* 한다. 보안 분야의 reward 는 *비대칭* 이다 — false negative (진짜 위협을 놓침) 가 false positive (false alarm) 보다 *훨씬 큰 손실*. dataset 운영에서 false negative 1건이 침해 사고 1건과 같다면, false positive 50건의 분석가 시간 손실보다 100배 비싸다.

이 비대칭이 reward 에 반영되어야 한다 — false negative -100 vs false positive -2 의 *50배 차이*. RL Steering 이 이 reward 를 받으면 — 자연스럽게 *false negative 를 줄이는 방향* 으로 가중치를 조정 (즉 *조금이라도 의심스러우면 critical 로 격상*).

학생이 알아야 할 것은 — **RL 의 학습은 *reward function 의 설계* 가 절대적**. reward 가 잘못 설계되면 *RL 이 잘못된 방향으로 더 빨리* 가는 *역효과*. 보안 분야의 reward 는 false negative 페널티를 매우 강하게.

### Case 2: skill 가중치 조정의 정량 효과 — Data Theft 392건의 학습 결과

| skill | 초기 가중치 | RL 후 가중치 | 변화 |
|---|---|---|---|
| `query_kg` | 1.0 | 1.4 | +40% (recon 단계 효과적) |
| `analyze_chain` | 1.0 | 1.2 | +20% |
| `generate_sigma` | 1.0 | 0.9 | -10% (단독 사용보다 chain 후) |
| `block_traffic` | 1.0 | 1.5 | +50% (exfil 단계 효과적) |
| 기타 29 skills | 1.0 | 0.95~1.05 | 미미 |

**자세한 해석**:

dataset 392건 Data Theft 학습 후 — Bastion 의 33개 skill 중 *4개의 가중치만 의미 있게 변화* 했다. 나머지 29개는 미미한 변화 (0.95~1.05). 이는 RL 의 자연스러운 결과 — *모든 skill 이 모든 신호에 똑같이 효과적은 아니므로* 일부만 가중치 변경.

가중치 변화의 의미 — `query_kg` +40% 는 *recon 단계 신호에 KG 검색이 매우 효과적* 임을 RL 이 발견. `block_traffic` +50% 는 *exfil 단계에 즉시 차단이 효과적*. 반면 `generate_sigma` -10% 는 *단독 사용보다 chain 분석 후 사용이 더 좋다* 는 패턴 발견.

학생이 알아야 할 것은 — **RL Steering 의 결과는 *해석 가능* 하다**. 가중치 변화를 보면 *왜 그렇게 변했는지* 의미를 추출할 수 있고, 이는 *사람의 도메인 지식에 합치* 한다. 만약 가중치 변화가 *해석 불가능* 하다면 — RL 이 잘못 학습한 신호.

### 이 사례에서 학생이 배워야 할 3가지

1. **RL Steering = 기존 모델의 미세 조정** — fine-tune 보다 100배 가벼움.
2. **Reward 의 비대칭이 핵심** — false negative -100 vs false positive -2.
3. **RL 결과는 해석 가능해야 한다** — 가중치 변화에 *도메인 의미* 가 있어야 정상.

**학생 액션**: Bastion 의 skill 가중치 파일 (예: `apps/bastion/data/skill_weights.json`) 을 확인하고 — dataset 50 신호로 RL Steering 을 1 epoch 실행 후 가중치 변화를 측정. 변화한 skill 들이 *어느 신호 패턴에 적합한지* 해석 가능한지 검증.

