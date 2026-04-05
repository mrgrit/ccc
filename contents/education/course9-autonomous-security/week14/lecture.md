# Week 14: RL Steering과 정책 최적화

## 학습 목표

- 강화학습(RL)을 통한 에이전트 행동 제어(Steering)의 원리를 이해한다
- OpsClaw의 reward 가중치(risk_penalty, speed_bonus)를 조절하여 에이전트 행동을 유도한다
- Q-learning 기반 정책 학습과 최적 risk_level 추천 메커니즘을 실습한다
- 다양한 reward 설정이 에이전트 행동에 미치는 영향을 실험적으로 관찰한다
- RL 정책의 수렴(convergence)을 확인하고 해석하는 방법을 학습한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

## 강의 시간 배분 (3시간)

| 시간 | 파트 | 내용 | 형태 |
|------|------|------|------|
| 0:00-0:30 | Part 1 | RL Steering 개요와 Q-learning | 이론 |
| 0:30-1:00 | Part 2 | OpsClaw RL 파이프라인 | 이론+실습 |
| 1:00-1:25 | Part 3 | reward 가중치 조절 실험 | 실습 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:05 | Part 4 | 정책 학습과 추천 | 실습 |
| 2:05-2:35 | Part 5 | 수렴 분석과 정책 해석 | 실습 |
| 2:35-3:00 | Part 6 | 종합 실습 + 퀴즈 | 실습+평가 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **RL (Reinforcement Learning)** | 보상 신호를 통해 최적 행동을 학습하는 기법 | Q-learning, SARSA |
| **Steering** | 보상 가중치를 조절하여 에이전트의 행동 방향을 유도하는 것 | risk_penalty 증가 → 보수적 행동 |
| **Q-learning** | 상태-행동 쌍의 가치(Q-value)를 학습하는 알고리즘 | Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)] |
| **Q-value** | 특정 상태에서 특정 행동의 기대 보상 값 | Q(low_risk, secu) = 0.85 |
| **reward** | 태스크 실행 후 받는 보상 신호 | 성공: +1, 실패: -1 |
| **risk_penalty** | 높은 risk_level 태스크에 부과하는 감점 | critical: -0.5 |
| **speed_bonus** | 빠른 실행 완료에 대한 보너스 점수 | 10초 이내: +0.2 |
| **policy** | 각 상태에서 최적 행동을 결정하는 규칙 | state=ssh_brute → action=rate_limit |
| **epsilon-greedy** | 탐색(exploration)과 활용(exploitation)을 균형 잡는 전략 | ε=0.1 → 10% 탐색, 90% 최적 행동 |
| **discount factor (γ)** | 미래 보상의 현재 가치 할인율 | γ=0.9: 미래 보상도 중시 |
| **learning rate (α)** | Q-value 업데이트 속도 | α=0.1: 점진적 학습 |
| **convergence** | Q-value가 안정적인 값에 수렴하는 것 | 변화량 < 0.01 |
| **state** | 에이전트가 관찰하는 현재 환경 상태 | (agent_id, risk_level, task_type) |
| **action** | 에이전트가 선택할 수 있는 행동 | (risk_level: low/medium/high/critical) |
| **episode** | 하나의 프로젝트 실행 사이클 (시작→완료) | 프로젝트 1개 = 1 에피소드 |
| **task_reward** | 개별 태스크에 대해 계산된 보상 값 | PoW 블록에 기록 |

---

## Part 1: RL Steering 개요와 Q-learning (0:00-0:30)

### 1.1 왜 RL Steering이 필요한가?

자율 보안 에이전트의 행동을 제어하는 두 가지 방법:

| 방법 | 규칙 기반 제어 | RL Steering |
|------|--------------|-------------|
| 동작 | 명시적 규칙 (if-then) | 보상 신호로 학습 |
| 유연성 | 낮음 (규칙 수정 필요) | 높음 (가중치 조절만) |
| 적응성 | 없음 | 환경 변화에 자동 적응 |
| 예시 | "critical은 항상 dry_run" | "risk_penalty=0.5이면 에이전트가 자연스럽게 low risk 선호" |

### 1.2 Q-learning 기본 원리

```
Q-learning 업데이트 공식:
Q(s, a) ← Q(s, a) + α · [r + γ · max_a' Q(s', a') - Q(s, a)]

여기서:
- s: 현재 상태 (agent_id, 현재 위험 수준)
- a: 선택한 행동 (risk_level)
- r: 받은 보상 (task_reward)
- s': 다음 상태
- α: 학습률 (0.1)
- γ: 할인율 (0.9)
```

### 1.3 OpsClaw에서의 RL 흐름

```
태스크 실행
    |
    v
PoW 블록 생성 (자동)
    |
    v
task_reward 계산
    |   reward = base_reward
    |          - risk_penalty
    |          + speed_bonus
    |          + success_bonus
    v
Q-value 업데이트
    |
    v
정책(policy) 개선
    |
    v
다음 태스크 시 최적 risk_level 추천
```

### 1.4 보상 구성 요소

| 구성 요소 | 설명 | 기본값 | 범위 |
|-----------|------|--------|------|
| base_reward | 태스크 완료 기본 보상 | 1.0 | 0.0~2.0 |
| risk_penalty | risk_level별 감점 | low:0, medium:0.1, high:0.3, critical:0.5 | 0.0~1.0 |
| speed_bonus | 빠른 실행 보너스 | 실행시간 < 10초: +0.2 | 0.0~0.5 |
| success_bonus | exit_code=0 보너스 | +0.3 | 0.0~1.0 |
| failure_penalty | exit_code!=0 감점 | -0.5 | -1.0~0.0 |

---

## Part 2: OpsClaw RL 파이프라인 (0:30-1:00)

### 2.1 RL API 엔드포인트

| API | 메서드 | 설명 |
|-----|--------|------|
| `/rl/train` | POST | PoW 블록의 task_reward 데이터로 Q-learning 학습 실행 |
| `/rl/recommend` | GET | 특정 agent_id/risk_level에 대한 최적 행동 추천 |
| `/rl/policy` | GET | 현재 학습된 Q-table/정책 전체 조회 |

### 2.2 RL 파이프라인 기본 실습

> **실습 목적**: 자율보안 시스템의 장기 운영 전략과 지속적 개선 프로세스를 설계하기 위해 수행한다
>
> **배우는 것**: 모델 드리프트 대응, 위협 정보 업데이트, 정책 버저닝, 성능 모니터링의 지속적 운영 전략을 이해한다
>
> **결과 해석**: 시간 경과에 따른 정확도 변화(드리프트)와 업데이트 후 성능 회복으로 운영 전략의 효과를 판단한다
>
> **실전 활용**: 자율보안 시스템의 운영 SLA 정의, 장기 운영 로드맵 수립, 팀 역량 개발 계획에 활용한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소
export MGR="http://localhost:8000"

# 1. 현재 RL 정책 상태 확인
curl -s "$MGR/rl/policy" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 학습된 Q-table과 정책 상태를 확인한다
```

```bash
# 2. RL 학습 데이터 생성 — 여러 risk_level로 태스크 실행
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-rl-training-data",
    "request_text": "RL 학습 데이터 생성 — 다양한 risk_level 태스크 실행",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PID="반환된-프로젝트-ID"

# 3. 스테이지 전환
# plan 스테이지 전환
curl -s -X POST $MGR/projects/$PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지 전환
curl -s -X POST $MGR/projects/$PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 4. 다양한 risk_level로 태스크 실행 — RL 학습 데이터 생성
curl -s -X POST $MGR/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"low-risk task on secu\" && hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"medium-risk task on web\" && curl -sI http://localhost:3000 | head -5",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"low-risk task on siem\" && ls /var/ossec/logs/ 2>/dev/null | head -5 || echo log-check-done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"high-risk task on secu\" && nft list ruleset 2>/dev/null | wc -l || echo 0",
        "risk_level": "high",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 4개 태스크가 서로 다른 risk_level로 실행되어 RL 학습 데이터를 생성한다
```

### 2.3 RL 학습 실행

```bash
# 5. Q-learning 학습 실행
curl -s -X POST "$MGR/rl/train" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# PoW 블록에 기록된 task_reward 데이터로 Q-learning을 실행한다
# 출력: 학습된 에피소드 수, Q-table 크기, 수렴 상태
```

```bash
# 6. 학습 후 정책 확인
curl -s "$MGR/rl/policy" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Q-table과 정책 상태 출력
print('=== RL 정책 상태 ===')
print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
"
```

---

## Part 3: reward 가중치 조절 실험 (1:00-1:25)

### 3.1 가중치 조절의 효과

| 설정 | 에이전트 행동 변화 |
|------|-------------------|
| risk_penalty 증가 | 보수적 (low risk 선호) |
| risk_penalty 감소 | 공격적 (high risk 허용) |
| speed_bonus 증가 | 빠른 실행 선호 (간단한 명령 위주) |
| success_bonus 증가 | 성공률 중시 (안전한 명령 위주) |

### 3.2 보수적 정책 실험

```bash
# 1. 보수적 정책 프로젝트 — risk_penalty가 높은 환경에서 태스크 실행
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-conservative-policy",
    "request_text": "보수적 RL 정책 실험 — high risk_penalty 환경",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export CONS_PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$CONS_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$CONS_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. RL 추천 기반 태스크 실행 — 현재 정책이 추천하는 risk_level 확인
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.1:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# RL이 secu SubAgent에 대해 추천하는 행동을 확인한다
```

```bash
# 4. 추천된 risk_level로 태스크 실행
curl -s -X POST $MGR/projects/$CONS_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"conservative: read-only check\" && cat /etc/hostname && uptime",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"conservative: status check\" && systemctl is-active sshd",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 보수적 정책에서는 low risk 태스크만 실행한다
```

### 3.3 공격적 정책 실험

```bash
# 5. 공격적 정책 프로젝트 — risk_penalty가 낮은 환경
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-aggressive-policy",
    "request_text": "공격적 RL 정책 실험 — low risk_penalty 환경",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export AGG_PID="반환된-프로젝트-ID"

# 6. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$AGG_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$AGG_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 7. 공격적 정책에서는 medium/high risk 태스크도 포함
curl -s -X POST $MGR/projects/$AGG_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"aggressive: service probe\" && ss -tlnp | head -20",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"aggressive: vuln check\" && curl -s http://localhost:3000/api/SecurityQuestions | head -20 2>/dev/null || echo check-done",
        "risk_level": "high",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
# 공격적 정책에서는 high risk 태스크도 허용한다
```

### 3.4 정책 비교

```bash
# 8. 두 실험의 PoW 보상 비교
echo "=== 보수적 정책 결과 ==="
# 보수적 정책의 Evidence 확인
curl -s "$MGR/projects/$CONS_PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'태스크 수: {len(data.get(\"evidences\", data.get(\"evidence\", [])))}')
"

echo "=== 공격적 정책 결과 ==="
# 공격적 정책의 Evidence 확인
curl -s "$MGR/projects/$AGG_PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'태스크 수: {len(data.get(\"evidences\", data.get(\"evidence\", [])))}')
"
```

---

## Part 4: 정책 학습과 추천 (1:35-2:05)

### 4.1 반복 학습으로 정책 개선

```bash
# 1. 추가 학습 데이터 생성 — 더 많은 태스크 실행
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-rl-more-data",
    "request_text": "RL 추가 학습 데이터 생성",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export MORE_PID="반환된-프로젝트-ID"

# 2. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$MORE_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$MORE_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 추가 태스크 실행 — 다양한 시나리오
curl -s -X POST $MGR/projects/$MORE_PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo rl-data-1 && df -h / | tail -1",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo rl-data-2 && free -m | head -2",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo rl-data-3 && ps aux --sort=-%cpu | head -5",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

```bash
# 4. 재학습 실행
curl -s -X POST "$MGR/rl/train" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 추가 데이터를 포함하여 Q-learning 재학습

# 5. 각 SubAgent에 대한 RL 추천 확인
echo "=== secu 추천 ==="
# secu SubAgent의 최적 risk_level 추천
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.1:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

echo "=== web 추천 ==="
# web SubAgent의 최적 risk_level 추천
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.80:8002&risk_level=medium" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

echo "=== siem 추천 ==="
# siem SubAgent의 최적 risk_level 추천
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.100:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

### 4.2 추천 결과 해석

```bash
# 6. 전체 정책 테이블 조회 및 분석
curl -s "$MGR/rl/policy" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 정책 테이블의 구조와 Q-value 분석
print('=== Q-Table 분석 ===')
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
print()
print('해석 가이드:')
print('  Q-value가 높을수록 해당 상태-행동 조합이 더 많은 보상을 기대할 수 있다')
print('  각 상태에서 Q-value가 가장 높은 행동이 정책이 추천하는 행동이다')
"
```

---

## Part 5: 수렴 분석과 정책 해석 (2:05-2:35)

### 5.1 수렴(Convergence) 판단 기준

| 지표 | 수렴 판단 기준 |
|------|--------------|
| Q-value 변화량 | max |ΔQ| < 0.01 |
| 정책 변화 | 10회 연속 동일 추천 |
| 평균 보상 | 이동 평균 변화 < 1% |
| 에피소드 수 | 일반적으로 50~200회 필요 |

### 5.2 수렴 시뮬레이션

```bash
# 1. 반복 학습으로 수렴 확인
# 3회 연속 학습을 실행하여 Q-value 변화를 관찰한다
for i in 1 2 3; do
  echo "=== 학습 라운드 $i ==="
  # Q-learning 학습 실행
  curl -s -X POST "$MGR/rl/train" \
    -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  결과: {json.dumps(data, ensure_ascii=False)[:200]}')
"
done
# 학습을 반복할수록 Q-value 변화가 줄어드는지 관찰한다
```

### 5.3 정책 해석과 활용

```bash
# 2. 최종 정책 기반 의사결정 시뮬레이션
python3 -c "
import requests, json

API = 'http://localhost:8000'
KEY = 'opsclaw-api-key-2026'
headers = {'X-API-Key': KEY}

# 각 SubAgent에 대해 모든 risk_level의 추천을 조회
agents = [
    ('secu', 'http://10.20.30.1:8002'),
    ('web', 'http://10.20.30.80:8002'),
    ('siem', 'http://10.20.30.100:8002'),
]

risk_levels = ['low', 'medium', 'high']

print('=== RL 정책 기반 추천 매트릭스 ===')
print(f'{\"Agent\":<10} {\"Low\":<15} {\"Medium\":<15} {\"High\":<15}')
print('-' * 55)

for name, agent_id in agents:
    row = f'{name:<10}'
    for rl in risk_levels:
        try:
            resp = requests.get(
                f'{API}/rl/recommend?agent_id={agent_id}&risk_level={rl}',
                headers=headers, timeout=5
            )
            data = resp.json()
            rec = str(data.get('recommended_risk_level', data.get('recommendation', '?')))[:12]
            row += f' {rec:<15}'
        except:
            row += f' {\"error\":<15}'
    print(row)

print()
print('해석: 각 셀은 현재 risk_level에서 RL이 추천하는 최적 행동')
"
# SubAgent별, risk_level별 RL 추천 매트릭스를 생성한다
```

### 5.4 RL 정책의 실무 적용

```bash
# 3. RL 추천을 실제 태스크 실행에 반영하는 파이프라인
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-rl-guided-execution",
    "request_text": "RL 정책 기반 태스크 실행 — 추천된 risk_level 적용",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export RL_PID="반환된-프로젝트-ID"

# 4. 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$RL_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$RL_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 5. RL 추천 기반 태스크 실행 (추천된 risk_level 적용)
curl -s -X POST $MGR/projects/$RL_PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"RL-guided task: optimized risk_level applied\" && hostname && uptime",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
# RL이 추천한 risk_level로 태스크를 실행한다

# 6. 완료 보고서
curl -s -X POST $MGR/projects/$RL_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "RL 정책 기반 태스크 실행 완료",
    "outcome": "success",
    "work_details": [
      "RL 추천 risk_level 적용하여 태스크 실행",
      "Q-learning 3회 반복 학습 수행",
      "SubAgent별 추천 매트릭스 생성",
      "정책 수렴 확인"
    ]
  }' | python3 -m json.tool
```

---

## Part 6: 종합 실습 + 퀴즈 (2:35-3:00)

### 6.1 종합 실습 과제

**과제**: RL Steering 파이프라인을 구축하고 정책을 분석하라.

1. 프로젝트 생성 (`week14-rl-final`)
2. 다양한 risk_level로 태스크 실행 (execute-plan, 최소 5개)
3. RL 학습 실행 (rl/train)
4. 추천 조회 (rl/recommend) 3개 SubAgent
5. 정책 분석 (rl/policy)
6. 결과 해석 + completion-report

### 6.2 퀴즈 (4지선다)

**문제 1.** Q-learning에서 Q(s, a) 값의 의미는?

- A) 상태 s에서 행동 a를 선택할 확률
- B) 상태 s에서 행동 a를 선택했을 때의 기대 보상
- C) 행동 a의 실행 시간
- D) 상태 s의 발생 빈도

**정답: B) 상태 s에서 행동 a를 선택했을 때의 기대 보상**

---

**문제 2.** risk_penalty를 높이면 에이전트의 행동이 어떻게 변하는가?

- A) 더 공격적으로 high risk 태스크를 실행한다
- B) 보수적으로 low risk 태스크를 선호하게 된다
- C) 실행 속도가 빨라진다
- D) SubAgent 수가 증가한다

**정답: B) 보수적으로 low risk 태스크를 선호하게 된다**

---

**문제 3.** OpsClaw RL에서 학습 데이터의 출처는?

- A) 외부 데이터셋을 수동으로 입력한다
- B) PoW 블록에 자동 기록된 task_reward 데이터를 사용한다
- C) LLM이 생성한 가상 데이터를 사용한다
- D) SubAgent가 직접 보상을 결정한다

**정답: B) PoW 블록에 자동 기록된 task_reward 데이터를 사용한다**

---

**문제 4.** RL 정책이 수렴(convergence)했다는 것의 의미는?

- A) 학습 데이터가 모두 소진되었다
- B) Q-value의 변화가 충분히 작아져 더 이상 크게 변하지 않는다
- C) 모든 태스크가 실패했다
- D) SubAgent가 종료되었다

**정답: B) Q-value의 변화가 충분히 작아져 더 이상 크게 변하지 않는다**

---

**문제 5.** epsilon-greedy 전략에서 epsilon=0.1의 의미는?

- A) 학습률이 0.1이다
- B) 10%의 확률로 무작위 탐색, 90%의 확률로 최적 행동을 선택한다
- C) 할인율이 0.1이다
- D) 보상의 10%를 감점한다

**정답: B) 10%의 확률로 무작위 탐색, 90%의 확률로 최적 행동을 선택한다**

---

### 6.3 다음 주 예고

Week 15는 **기말고사 — 자율 Purple Team 구축**이다.
Red+Blue 동시 운영, Experience 축적, RL 학습, 종합 보안 자동화를 실습 평가한다.
