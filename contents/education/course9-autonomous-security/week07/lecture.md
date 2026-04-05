# Week 07: 강화학습(RL)과 보상

## 학습 목표
- 강화학습(Reinforcement Learning)의 기본 개념과 보안 적용 원리를 이해한다
- Q-learning 알고리즘의 동작 원리를 설명하고 간단한 구현을 할 수 있다
- UCB1(Upper Confidence Bound) 탐색-활용 전략을 이해한다
- OpsClaw의 RL 학습·추천 API를 활용하여 risk_level 최적화를 수행할 수 있다
- 보상 설계가 자율보안시스템의 행동에 미치는 영향을 분석할 수 있다

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

## 용어 해설 (자율보안시스템 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **강화학습** | Reinforcement Learning (RL) | 보상/벌점으로 최적 행동을 학습하는 AI 기법 | 시행착오로 배우는 아기 |
| **에이전트** | Agent (RL) | 환경과 상호작용하며 학습하는 주체 | 게임 플레이어 |
| **환경** | Environment | 에이전트가 행동하는 세계 | 게임 세계 |
| **상태** | State | 환경의 현재 상황 | 게임 화면 |
| **행동** | Action | 에이전트가 취할 수 있는 선택 | 방향키 입력 |
| **보상** | Reward | 행동의 결과에 대한 점수 | 게임 점수 |
| **Q-value** | Q-value | 상태-행동 쌍의 기대 보상값 | "이 상황에서 이 행동의 예상 점수" |
| **Q-table** | Q-table | 모든 상태-행동의 Q-value를 저장하는 표 | 공략집 |
| **UCB1** | Upper Confidence Bound 1 | 탐색과 활용의 균형을 맞추는 알고리즘 | 새 식당 vs 단골 식당 선택 전략 |
| **탐색** | Exploration | 새로운 행동을 시도하여 정보 수집 | 새 식당 가보기 |
| **활용** | Exploitation | 알려진 최적 행동을 반복 | 단골 식당 가기 |
| **epsilon-greedy** | epsilon-greedy | 확률적으로 탐색과 활용을 전환 | 10% 확률로 새 식당, 90%는 단골 |
| **학습률** | Learning Rate (alpha) | 새 정보를 반영하는 비율 | 경험 반영 속도 |
| **할인율** | Discount Factor (gamma) | 미래 보상의 현재 가치 | 내일의 100만원 vs 오늘의 100만원 |
| **정책** | Policy | 상태별 최적 행동을 결정하는 규칙 | 게임 공략 전략 |
| **Reward Shaping** | Reward Shaping | 학습 효율을 높이기 위해 보상을 설계 | 단계별 보너스 |
| **수렴** | Convergence | 학습이 안정적인 최적 정책에 도달 | 실력이 안정되어 더 이상 변하지 않음 |

---

# Week 07: 강화학습(RL)과 보상

## 학습 목표
- 강화학습 기본 개념을 이해한다
- Q-learning 동작 원리를 이해하고 구현한다
- UCB1을 이해한다
- OpsClaw RL API를 활용한다

## 전제 조건
- Week 01-06 완료 (PoW, 보상 개념)
- Python 기초
- 확률/통계 기본 개념

---

## 1. 강화학습 기초 (40분)

### 1.1 강화학습이란

강화학습은 에이전트가 환경과 상호작용하면서 보상을 최대화하는 행동을 학습하는 AI 기법이다.

```
  에이전트  | ← 보상/벌점을 바탕으로 정책 업데이트
  (OpsClaw)
  행동 (action)
  risk_level 선택
↓
  환경  | ← 보안 인프라 (서버, 네트워크)
  (서버들)
  상태 + 보상
  exit_code, 실행 시간, 보상 점수
↓
(다시 에이전트로 피드백)
```

### 1.2 보안에서의 RL 적용

| 요소 | 일반 RL | OpsClaw 보안 RL |
|------|---------|----------------|
| 에이전트 | 게임 캐릭터 | OpsClaw Master |
| 환경 | 게임 세계 | 보안 인프라 (secu/web/siem) |
| 상태 | 게임 화면 | 서버 상태, 위협 수준, 이전 결과 |
| 행동 | 방향키 입력 | risk_level 선택 (low/medium/high/critical) |
| 보상 | 게임 점수 | 성공 보상, 실패 벌점 |
| 정책 | 공략 전략 | 상황별 최적 risk_level 결정 |

### 1.3 탐색 vs 활용 딜레마

```
상황: 새로운 보안 위협이 탐지되었다

활용(Exploitation):
  "이전에 성공한 risk_level=low를 다시 사용하자"
  → 안전하지만 최적이 아닐 수 있음

탐색(Exploration):
  "risk_level=medium을 시도해보자"
  → 더 좋은 결과를 발견할 수 있지만, 실패 위험도 있음

해결: epsilon-greedy 전략
  ε=0.1 → 10% 확률로 탐색, 90% 확률로 활용
```

### 1.4 Q-learning 알고리즘

Q-learning은 상태-행동 쌍의 가치(Q-value)를 반복적으로 업데이트하여 최적 정책을 학습한다.

```
Q-table 업데이트 공식:

Q(s, a) ← Q(s, a) + α × [R + γ × max Q(s', a') - Q(s, a)]

여기서:
  s = 현재 상태
  a = 현재 행동
  R = 받은 보상
  s' = 다음 상태
  α = 학습률 (0~1, 새 정보 반영 비율)
  γ = 할인율 (0~1, 미래 보상의 현재 가치)
```

**직관적 해석**: "기존에 알던 가치(Q)에, 새로 경험한 것(R + 미래 기대)과의 차이를 학습률만큼 반영한다."

---

## 2. Q-learning 구현 실습 (30분)

### 2.1 간단한 Q-learning 시뮬레이션

> **실습 목적**: 자율보안 에이전트 간 협업(Multi-Agent)의 원리와 효과를 체험하기 위해 수행한다
>
> **배우는 것**: Master-SubAgent 계층 구조에서 역할 분담과 메시지 전달의 원리, A2A 프로토콜의 구조를 이해한다
>
> **결과 해석**: 각 SubAgent의 실행 결과가 Master에 통합되는 과정에서 성공/실패 비율과 소요 시간을 확인한다
>
> **실전 활용**: 분산 보안 모니터링, 다중 서버 동시 패치, 협업형 인시던트 대응 시스템 구축에 활용한다

```bash
# opsclaw 서버 접속
ssh opsclaw@10.20.30.201
```

```bash
# Q-learning 시뮬레이션: 보안 작업의 최적 risk_level 학습
python3 << 'PYTHON'
import random

# 상태 정의: 위협 수준
states = ["no_threat", "low_threat", "high_threat"]

# 행동 정의: risk_level
actions = ["low", "medium", "high", "critical"]

# Q-table 초기화 (상태 x 행동)
Q = {}
for s in states:
    Q[s] = {}
    for a in actions:
        Q[s][a] = 0.0

# 하이퍼파라미터
alpha = 0.1    # 학습률
gamma = 0.9    # 할인율
epsilon = 0.2  # 탐색 확률

# 보상 함수 (시뮬레이션용)
def get_reward(state, action):
    """상태와 행동에 따른 보상"""
    # no_threat 상태에서는 low가 최적
    if state == "no_threat":
        rewards = {"low": 1.0, "medium": 0.5, "high": 0.0, "critical": -0.5}
    # low_threat에서는 medium이 최적
    elif state == "low_threat":
        rewards = {"low": 0.0, "medium": 2.0, "high": 1.0, "critical": 0.5}
    # high_threat에서는 high가 최적
    else:
        rewards = {"low": -1.0, "medium": 0.5, "high": 3.0, "critical": 2.0}
    return rewards[action] + random.uniform(-0.3, 0.3)

# 학습 루프
print("=== Q-learning 학습 시작 ===")
for episode in range(500):
    # 랜덤 상태에서 시작
    state = random.choice(states)

    # epsilon-greedy로 행동 선택
    if random.random() < epsilon:
        action = random.choice(actions)  # 탐색
    else:
        action = max(actions, key=lambda a: Q[state][a])  # 활용

    # 보상 받기
    reward = get_reward(state, action)

    # 다음 상태 (랜덤)
    next_state = random.choice(states)

    # Q-value 업데이트
    best_next = max(Q[next_state].values())
    Q[state][action] += alpha * (reward + gamma * best_next - Q[state][action])

    # 100 에피소드마다 진행 상황 출력
    if (episode + 1) % 100 == 0:
        print(f"Episode {episode+1}: 학습 진행 중...")

# 최종 Q-table 출력
print("\n=== 학습된 Q-table ===")
print(f"{'상태':>15} {'low':>8} {'medium':>8} {'high':>8} {'critical':>8} {'최적':>8}")
print("-" * 60)
for s in states:
    best = max(actions, key=lambda a: Q[s][a])
    values = " ".join(f"{Q[s][a]:>8.2f}" for a in actions)
    print(f"{s:>15} {values} {best:>8}")

print("\n=== 학습된 정책 ===")
for s in states:
    best = max(actions, key=lambda a: Q[s][a])
    print(f"  {s} → {best} (Q={Q[s][best]:.2f})")
PYTHON
# 500번 시행착오 후 각 상태에서의 최적 risk_level이 학습된다
```

### 2.2 UCB1 알고리즘

```bash
# UCB1 시뮬레이션
python3 << 'PYTHON'
import math
import random

# 행동별 보상 분포 (실제 환경에서는 미지)
true_rewards = {
    "low": 1.0,      # 평균 보상
    "medium": 1.5,
    "high": 2.0,
    "critical": 1.2
}

# 기록
counts = {a: 0 for a in true_rewards}    # 각 행동 시도 횟수
rewards = {a: 0.0 for a in true_rewards}  # 누적 보상
total = 0

print("=== UCB1 탐색-활용 전략 ===")
for t in range(1, 101):
    # UCB1 계산
    ucb_values = {}
    for a in true_rewards:
        if counts[a] == 0:
            ucb_values[a] = float('inf')  # 한 번도 시도 안 한 행동 우선
        else:
            avg = rewards[a] / counts[a]
            confidence = math.sqrt(2 * math.log(total) / counts[a])
            ucb_values[a] = avg + confidence

    # UCB1이 가장 높은 행동 선택
    action = max(ucb_values, key=ucb_values.get)

    # 보상 받기 (실제 환경에서 관측)
    reward = true_rewards[action] + random.gauss(0, 0.5)

    # 기록 업데이트
    counts[action] += 1
    rewards[action] += reward
    total += 1

    # 20회마다 현황 출력
    if t % 20 == 0:
        print(f"\n--- Round {t} ---")
        for a in true_rewards:
            avg = rewards[a]/counts[a] if counts[a] > 0 else 0
            print(f"  {a:>10}: 시도 {counts[a]:>3}회, 평균보상 {avg:.2f}")

print(f"\n=== 최종 결과: 가장 많이 선택된 행동 = {max(counts, key=counts.get)} ===")
PYTHON
# UCB1이 자동으로 높은 보상의 행동(high)을 더 많이 선택하게 된다
```

---

## 3. OpsClaw RL API 실습 (40분)

### 3.1 RL 학습 실행

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

```bash
# RL 학습 실행 (기존 task_reward 데이터 기반)
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  | python3 -m json.tool
# 학습 결과: 에피소드 수, Q-table 크기, 수렴 여부 등이 반환된다
```

### 3.2 RL 정책 조회

```bash
# 현재 학습된 RL 정책 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/rl/policy \
  | python3 -m json.tool
# 상태별 최적 행동(risk_level)과 Q-value가 출력된다
```

### 3.3 RL 추천 조회

```bash
# 특정 에이전트와 risk_level에 대한 RL 추천
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/rl/recommend?agent_id=http://10.20.30.1:8002&risk_level=low" \
  | python3 -m json.tool
# 해당 에이전트의 해당 risk_level에 대한 추천 정보가 반환된다
```

```bash
# 다른 에이전트의 추천
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/rl/recommend?agent_id=http://10.20.30.80:8002&risk_level=medium" \
  | python3 -m json.tool
```

### 3.4 보상 데이터 생성을 위한 작업 실행

```bash
# 다양한 risk_level로 작업 실행하여 학습 데이터 축적
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week07-rl-data-collection",
    "request_text": "RL 학습 데이터 수집: 다양한 risk_level 실행",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"
# stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
```

```bash
# 다양한 risk_level로 task 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "ss -tlnp | wc -l",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "sudo nft list ruleset | wc -l",
        "risk_level": "high",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 6개 task (low x3, medium x2, high x1)가 실행되고 보상 데이터가 축적된다
```

### 3.5 학습 데이터 축적 후 재학습

```bash
# 새 데이터 축적 후 RL 재학습
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  | python3 -m json.tool
# 추가 데이터를 반영하여 정책이 업데이트된다
```

```bash
# 업데이트된 정책 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/rl/policy \
  | python3 -m json.tool
# Q-value가 변경되었는지 확인
```

---

## 4. 보상 설계의 영향 분석 (40분)

### 4.1 보상 설계란

보상 설계(Reward Shaping)는 RL 에이전트가 원하는 행동을 학습하도록 보상 함수를 설계하는 과정이다.

```
잘못된 보상 설계 예:
  "성공하면 +1, 실패하면 0"
  → 에이전트가 항상 가장 안전한(low risk) 작업만 선택
  → 위험하지만 필요한 작업을 회피

올바른 보상 설계 예:
  "성공하면 risk_level에 비례한 보상, 실패하면 벌점"
  → low 성공: +1.0
  → medium 성공: +2.0
  → high 성공: +3.0
  → 실패: -2.0
  → 에이전트가 적절한 위험을 감수하며 효과적으로 대응
```

### 4.2 보상 설계 시뮬레이션

```bash
# 보상 설계에 따른 에이전트 행동 변화 시뮬레이션
python3 << 'PYTHON'
import random

def simulate_rl(reward_func, name, episodes=300):
    """주어진 보상 함수로 Q-learning 시뮬레이션"""
    actions = ["low", "medium", "high"]
    Q = {a: 0.0 for a in actions}
    counts = {a: 0 for a in actions}
    alpha, epsilon = 0.1, 0.15

    for ep in range(episodes):
        # epsilon-greedy
        if random.random() < epsilon:
            action = random.choice(actions)
        else:
            action = max(actions, key=lambda a: Q[a])

        # 보상 받기
        reward = reward_func(action)
        Q[action] += alpha * (reward - Q[action])
        counts[action] += 1

    print(f"\n=== {name} ===")
    print(f"  선택 비율: " + ", ".join(f"{a}={counts[a]/episodes*100:.0f}%" for a in actions))
    print(f"  최종 Q: " + ", ".join(f"{a}={Q[a]:.2f}" for a in actions))

# 설계 A: 균일 보상 (성공=1, 실패=0)
def reward_a(action):
    success_rate = {"low": 0.95, "medium": 0.80, "high": 0.60}
    return 1.0 if random.random() < success_rate[action] else 0.0

# 설계 B: 위험 비례 보상
def reward_b(action):
    success_rate = {"low": 0.95, "medium": 0.80, "high": 0.60}
    base_reward = {"low": 1.0, "medium": 2.0, "high": 3.0}
    if random.random() < success_rate[action]:
        return base_reward[action]
    else:
        return -1.0

# 설계 C: 위험 회피 벌점 강화
def reward_c(action):
    success_rate = {"low": 0.95, "medium": 0.80, "high": 0.60}
    base_reward = {"low": 1.0, "medium": 2.0, "high": 3.0}
    if random.random() < success_rate[action]:
        return base_reward[action]
    else:
        return -5.0  # 큰 벌점

simulate_rl(reward_a, "설계A: 균일 보상")
simulate_rl(reward_b, "설계B: 위험 비례 보상")
simulate_rl(reward_c, "설계C: 높은 벌점")
PYTHON
# 보상 설계에 따라 에이전트의 행동이 크게 달라짐을 관찰한다
# 설계A: low 위주 선택 (안전 지향)
# 설계B: medium/high 비율 증가 (균형)
# 설계C: low 위주 회귀 (벌점 회피)
```

### 4.3 리더보드와 보상 확인

```bash
# PoW 리더보드 조회 (보상 합계 순위)
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard | python3 -m json.tool
```

```bash
# 프로젝트 완료
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Week07 강화학습과 보상 실습 완료",
    "outcome": "success",
    "work_details": [
      "Q-learning 시뮬레이션 구현 및 실행",
      "UCB1 탐색-활용 전략 시뮬레이션",
      "OpsClaw RL train/policy/recommend API 활용",
      "다양한 risk_level task 실행으로 학습 데이터 축적",
      "보상 설계 3가지 시뮬레이션 비교 분석"
    ]
  }' | python3 -m json.tool
```

---

## 5. PoW → RL 연결 아키텍처 (30분)

### 5.1 데이터 흐름

```
execute-plan 실행
↓
  Task 실행
  (SubAgent)
  exit_code, stdout, 실행 시간
↓

  PoW 블록 생성 | →| task_reward
  (해시 체인)  |  | DB 기록
  학습 데이터
↓
  RL Train
  (Q-learning)
  학습된 정책
↓
  RL Recommend
  (추천 API)
↓
다음 작업의 risk_level 결정에 활용
```

### 5.2 자율 개선 루프

```
1. 작업 실행 → 보상 수집
2. 보상 데이터로 RL 학습
3. 학습된 정책으로 다음 작업의 risk_level 추천
4. 추천된 risk_level로 작업 실행
5. 1로 돌아감 → 반복

시간이 지날수록:
  - 각 서버/상황에 맞는 최적 risk_level이 학습됨
  - 불필요하게 높은 risk_level 사용을 줄임
  - 필요할 때는 적절히 높은 risk_level을 선택
```

---

## 6. 복습 퀴즈 + 과제 안내 (20분)

### 토론 주제

1. **보상 해킹**: RL 에이전트가 보상을 부정하게 높이는 행동(의미 없는 작업 반복)을 어떻게 방지하는가?
2. **안전한 RL**: critical 작업의 보상이 높다고 해서 자율적으로 critical 작업을 실행해도 되는가?
3. **초기 학습 위험**: 데이터가 부족한 초기에 RL 추천을 신뢰해도 되는가?

---

## 과제

### 과제 1: Q-learning 구현 (필수)
3-상태(정상/경고/위험) x 4-행동(무시/모니터링/경고발송/자동차단) 환경에서 Q-learning을 구현하라. 500 에피소드 후의 Q-table과 최적 정책을 제출한다.

### 과제 2: 보상 설계 실험 (필수)
3가지 이상의 서로 다른 보상 함수를 설계하고, 각각의 학습 결과(에이전트 행동 패턴)를 비교 분석하라. 어떤 보상 설계가 보안 운영에 가장 적합한지 논증한다.

### 과제 3: OpsClaw RL 활용 보고서 (선택)
OpsClaw RL API를 사용하여 10개 이상의 다양한 task를 실행하고, train → policy → recommend 흐름을 기록하라. 정책 변화를 관찰하고 보고서를 작성한다.

---

## 검증 체크리스트

- [ ] 강화학습의 에이전트-환경-상태-행동-보상 개념을 설명할 수 있는가?
- [ ] Q-learning의 업데이트 공식을 말할 수 있는가?
- [ ] 탐색과 활용의 딜레마를 설명할 수 있는가?
- [ ] UCB1 알고리즘의 동작 원리를 설명할 수 있는가?
- [ ] OpsClaw RL train API를 호출하여 학습을 실행할 수 있는가?
- [ ] RL policy와 recommend API를 사용할 수 있는가?
- [ ] 보상 설계가 에이전트 행동에 미치는 영향을 설명할 수 있는가?

---

## 다음 주 예고

**Week 08: 중간고사 — 자율 보안 점검 CTF**
- 4대 서버 종합 점검 CTF
- OpsClaw execute-plan으로 병렬 실행
- Week 01~07 전체 지식 종합 평가
- 팀별 점수 경쟁

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** Q-learning에서 Q(s,a)가 나타내는 것은?
- (a) 상태의 확률  (b) **상태 s에서 행동 a를 취할 때의 기대 보상**  (c) 행동의 빈도  (d) 에피소드 수

**Q2.** epsilon-greedy에서 epsilon=0.1의 의미는?
- (a) 10% 속도 향상  (b) **10% 확률로 탐색(새로운 행동 시도)**  (c) 10개 에피소드  (d) 10% 할인

**Q3.** UCB1의 핵심 아이디어는?
- (a) 항상 최고 보상 선택  (b) 항상 랜덤 선택  (c) **적게 시도한 행동에 보너스를 주어 탐색-활용 균형**  (d) 가장 빠른 행동 선택

**Q4.** 보상 설계에서 벌점을 너무 크게 하면?
- (a) 학습이 빨라진다  (b) **에이전트가 위험 회피적이 되어 안전한 행동만 선택**  (c) 에이전트가 공격적이 된다  (d) 변화 없음

**Q5.** OpsClaw에서 RL 학습 데이터의 원천은?
- (a) 사용자 입력  (b) 외부 API  (c) **execute-plan 실행 시 생성되는 task_reward (PoW 연동)**  (d) 이메일 알림

**정답:** Q1:b, Q2:b, Q3:c, Q4:b, Q5:c

---
---
