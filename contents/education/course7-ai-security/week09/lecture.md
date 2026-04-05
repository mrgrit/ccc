# Week 09: OpsClaw (1) - 기본

## 학습 목표
- OpsClaw의 프로젝트 생명주기를 이해한다
- dispatch와 execute-plan의 차이를 구분하고 적절히 사용한다
- 증거(evidence) 시스템과 PoW 체인을 이해한다
- OpsClaw를 활용한 보안 점검 자동화를 실습한다

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

# Week 09: OpsClaw (1) - 기본

## 학습 목표
- OpsClaw의 프로젝트 생명주기를 이해한다
- dispatch와 execute-plan의 차이를 구분하고 적절히 사용한다
- 증거(evidence) 시스템과 PoW 체인을 이해한다
- OpsClaw를 활용한 보안 점검 자동화를 실습한다

---

## 1. OpsClaw 프로젝트 생명주기

> **이 실습을 왜 하는가?**
> OpsClaw는 보안 작업을 **자동화하고 증적을 관리**하는 하네스 플랫폼이다.
> 직접 SSH로 명령을 실행하면 아무런 기록이 남지 않지만,
> OpsClaw를 경유하면 **모든 명령, 결과, 시간, 보상이 자동으로 기록**된다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 프로젝트 라이프사이클 (created→planned→executing→done)
> - dispatch(단일 명령)와 execute-plan(다중 태스크 병렬)의 차이
> - evidence/replay로 작업 이력을 추적하는 방법
> - PoW 블록과 보상(reward)의 의미
>
> **실무 활용:**
> - 보안 감사: "어떤 명령을 어떤 서버에서 실행했는가?" → replay API로 즉시 답변
> - 성과 관리: 에이전트별 보상 누적 → 리더보드
> - 반복 작업: Playbook으로 동일 점검을 매주 자동 실행
>
> **검증 완료:** OpsClaw API 정상 동작, execute-plan 병렬 실행, evidence/replay 확인

```
created → planned → executing → done
   ↓         ↓          ↓
 생성      계획 수립    실행 중     완료
```

### Stage 전환 규칙

| 현재 → 다음 | API | 설명 |
|------------|-----|------|
| created → planned | POST /projects/{id}/plan | 계획 단계 진입 |
| planned → executing | POST /projects/{id}/execute | 실행 단계 진입 |
| executing → done | POST /projects/{id}/completion-report | 완료 보고 |

---

## 2. 프로젝트 생성

> **실습 목적**: LLM 자체의 보안 취약점(프롬프트 인젝션, 탈옥)을 직접 시도하여 공격 표면을 이해하기 위해 수행한다
>
> **배우는 것**: 프롬프트 인젝션으로 시스템 프롬프트를 우회하는 원리와, DAN/역할극 등 탈옥 기법의 작동 방식을 이해한다
>
> **결과 해석**: LLM이 시스템 프롬프트의 지시를 무시하고 금지된 내용을 출력하면 공격 성공이다
>
> **실전 활용**: AI 서비스 출시 전 Red Teaming, 프롬프트 인젝션 방어 가드레일 설계, AI 보안 감사에 활용한다

```bash
# external 모드: Claude Code(사람)가 오케스트레이션
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "security-audit-web",
    "request_text": "web 서버 보안 점검",
    "master_mode": "external"
  }' | python3 -m json.tool

# 응답에서 id 필드를 기록해둔다
```

### master_mode 옵션

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **external** | 외부 도구(Claude Code)가 계획/실행 | 수동 오케스트레이션 |
| **native** | Master Service가 LLM으로 자동 | 자동 오케스트레이션 |

---

## 3. Dispatch (단일 명령 실행)

dispatch는 **단일 명령**을 특정 SubAgent에 전달하여 실행한다.

```bash
# 프로젝트 ID를 변수에 저장
PID="프로젝트_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026"
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026"

# 로컬 SubAgent에서 명령 실행
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "hostname && uptime",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 원격 SubAgent에서 명령 실행 (secu 서버)
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "sudo nft list ruleset | head -20",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
```

---

## 4. Execute-plan (다중 태스크 실행)

execute-plan은 **여러 태스크를 순차적으로** 실행한다.
각 태스크에 risk_level과 SubAgent를 지정할 수 있다.

3대 서버에 각각 다른 명령을 순차 실행하는 예시이다. 각 태스크에 대상 서버 SubAgent URL과 risk_level을 지정한다.

```bash
# 3개 태스크를 순차 실행: 각각 다른 서버의 SubAgent에 전달
# order: 실행 순서 / risk_level: low/medium/high/critical
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "cat /etc/os-release",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "docker ps --format table",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### Risk Level

| 수준 | 설명 | 동작 |
|------|------|------|
| low | 읽기 전용, 안전 | 즉시 실행 |
| medium | 설정 변경 가능 | 즉시 실행 |
| high | 서비스 영향 가능 | 확인 후 실행 |
| critical | 파괴적 가능성 | dry_run 자동 강제 |

---

## 5. 증거(Evidence) 시스템

모든 실행 결과는 증거로 기록된다.

```bash
# 증거 요약 조회
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool
```

### PoW (Proof of Work) 체인

모든 태스크 실행은 PoW 블록으로 기록되어 변조를 방지한다.

```bash
# PoW 블록 조회
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" | python3 -m json.tool

# 체인 무결성 검증
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool
# 정상: {"valid": true, "blocks": N, "orphans": 0}
```

---

## 6. 완료 보고서

프로젝트 완료 시 결과 보고서를 작성한다. outcome과 work_details로 작업 결과를 기록하며, 이 데이터는 RL 학습에도 활용된다.

```bash
# 프로젝트 완료 보고서 작성 (outcome: success/failure/partial)
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "web 서버 보안 점검 완료",
    "outcome": "success",
    "work_details": [
      "호스트 정보 수집 완료",
      "OS 버전 확인 완료",
      "Docker 컨테이너 목록 확인 완료"
    ]
  }' | python3 -m json.tool
```

---

## 7. 실습: 보안 점검 자동화

### 실습 1: 전체 플로우 체험

```bash
# 1. 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"lab-audit","request_text":"실습 보안 점검","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project: $PID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 3. 보안 점검 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":3, "instruction_prompt":"last -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 4. 증거 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool

# 5. 완료 보고
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"summary":"보안 점검 완료","outcome":"success","work_details":["시스템 정보 수집","열린 포트 확인","최근 로그인 이력 확인"]}'
```

### 실습 2: 다중 서버 점검

```bash
# 여러 서버에 동시에 명령 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://10.20.30.1:8002"},
      {"order":3, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 3: PoW 체인 확인

```bash
# 보상 랭킹 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/pow/leaderboard | python3 -m json.tool

# 프로젝트 작업 리플레이
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/replay" | python3 -m json.tool
```

---

## 핵심 정리

1. OpsClaw 프로젝트는 created → planned → executing → done 순으로 진행한다
2. dispatch는 단일 명령, execute-plan은 여러 태스크를 순차 실행한다
3. risk_level로 태스크의 위험도를 관리하고, critical은 자동으로 dry_run된다
4. 모든 작업은 증거로 기록되고 PoW 체인으로 무결성을 보장한다
5. API 호출 시 반드시 X-API-Key 헤더를 포함해야 한다

---

## 다음 주 예고
- Week 10: OpsClaw (2) - Playbook과 강화학습(RL) 연동

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
