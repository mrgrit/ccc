# Week 13: 분산 지식

## 학습 목표
- 분산 지식 아키텍처의 개념과 필요성을 이해한다
- local_knowledge.json의 구조와 역할을 파악한다
- SubAgent 간 지식 전달(knowledge transfer) 메커니즘을 이해한다
- 분산 지식을 활용한 보안 운영 개선을 실습한다

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

# Week 13: 분산 지식

## 학습 목표
- 분산 지식 아키텍처의 개념과 필요성을 이해한다
- local_knowledge.json의 구조와 역할을 파악한다
- SubAgent 간 지식 전달(knowledge transfer) 메커니즘을 이해한다
- 분산 지식을 활용한 보안 운영 개선을 실습한다

---

## 1. 왜 분산 지식이 필요한가?

### 중앙 집중 vs 분산

| 방식 | 장점 | 단점 |
|------|------|------|
| 중앙 집중 | 단일 관리 지점 | 단일 장애점, 네트워크 의존 |
| 분산 | 네트워크 장애에 강함 | 동기화 필요 |

각 SubAgent가 자신의 환경에 대한 지식을 로컬에 저장하면:
- 네트워크 장애 시에도 기본 운영 가능
- 로컬 컨텍스트로 더 정확한 판단
- 중앙 서버 부하 감소

---

## 2. local_knowledge.json

> **이 실습을 왜 하는가?**
> "분산 지식" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

각 SubAgent는 `local_knowledge.json` 파일에 로컬 지식을 저장한다.

### 2.1 구조

```json
{
  "agent_id": "http://10.20.30.1:8002",
  "hostname": "secu",
  "role": "nftables + Suricata IPS",
  "last_updated": "2026-03-27T10:00:00Z",
  "system_info": {
    "os": "Ubuntu 22.04",
    "kernel": "6.8.0-106-generic",
    "services": ["nftables", "suricata", "sshd"]
  },
  "security_baseline": {
    "open_ports": [22, 8002],
    "users": ["root", "opsclaw", "student"],
    "firewall_rules_count": 45
  },
  "learned_patterns": [
    {
      "pattern": "SSH brute force from 203.0.113.0/24",
      "first_seen": "2026-03-25",
      "action_taken": "IP blocked via nftables",
      "effectiveness": "high"
    }
  ],
  "local_policies": {
    "auto_block_threshold": 10,
    "alert_level_minimum": 8
  }
}
```

### 2.2 지식 카테고리

| 카테고리 | 내용 | 갱신 주기 |
|---------|------|----------|
| system_info | OS, 서비스, 설정 | Explore 시 |
| security_baseline | 포트, 사용자, 규칙 | Daemon 주기 |
| learned_patterns | 학습된 공격 패턴 | 이벤트 발생 시 |
| local_policies | 로컬 대응 정책 | 관리자 설정 |

---

## 3. Knowledge Transfer

### 3.1 지식 전달 흐름

```
SubAgent A (secu)          Manager            SubAgent B (web)
    │                         │                     │
    │ ── 지식 공유 요청 ──→   │                     │
    │                         │ ── 지식 전달 ──→    │
    │                         │                     │
    │   "secu에서 발견된       │   "secu 에서 공격    │
    │    공격 패턴 공유"       │    패턴 수신"        │
```

### 3.2 지식 전달 시나리오

> **실습 목적**: AI 시스템 전체의 보안 위협을 체계적으로 분석하는 위협 모델링을 수행하기 위해 실습한다
>
> **배우는 것**: STRIDE/OWASP ML Top 10 프레임워크로 AI 시스템의 위협을 분류하고, 각 위협에 대한 완화 전략을 도출하는 방법을 이해한다
>
> **결과 해석**: 위협 모델링 결과의 위험도(높음/중간/낮음)와 완화 전략의 실현 가능성으로 우선순위를 결정한다
>
> **실전 활용**: AI 서비스 출시 전 보안 검토, 보안 아키텍처 리뷰, 컴플라이언스 심사 대응에 활용한다

```bash
# secu에서 공격 패턴 발견
KNOWLEDGE='{
  "source": "http://10.20.30.1:8002",
  "type": "threat_intelligence",
  "data": {
    "attack_type": "SSH brute force",
    "source_ip": "203.0.113.50",
    "timestamp": "2026-03-27T10:00:00Z",
    "action": "blocked"
  }
}'

# Manager를 통해 다른 SubAgent에 지식 전달
# 실제 구현에서는 Manager API의 knowledge endpoint 사용
```

### 3.3 지식 동기화 패턴

```
시나리오: secu에서 공격 IP 차단 → web/siem에도 알림

1. secu SubAgent: 공격 IP 203.0.113.50 탐지 및 차단
2. secu → Manager: 위협 인텔리전스 공유
3. Manager → web SubAgent: "이 IP에서 웹 공격 가능성, 모니터링 강화"
4. Manager → siem SubAgent: "이 IP 관련 알림 우선순위 상향"
```

---

## 4. LLM과 분산 지식의 결합

### 4.1 로컬 지식을 LLM 프롬프트에 활용

SubAgent가 수집한 로컬 지식(열린 포트, 최근 알림, 베이스라인 변경)을 LLM 프롬프트에 포함시켜 서버 맞춤형 분석을 수행한다.

```bash
# web 서버의 로컬 지식을 JSON으로 구성
LOCAL_KNOWLEDGE='{
  "hostname": "web",
  "role": "웹 서버",
  "open_ports": [22, 80, 443, 8080],
  "recent_alerts": ["SQL Injection 시도 3건", "XSS 시도 1건"],
  "baseline_change": "포트 8080이 새로 열림"
}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 관제 에이전트입니다. 로컬 지식을 기반으로 현재 상황을 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"로컬 지식:\\n$LOCAL_KNOWLEDGE\\n\\n현재 보안 상황을 분석하고 조치가 필요한 항목을 우선순위로 나열하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 교차 지식 분석

```bash
# 여러 SubAgent의 지식을 통합하여 분석
COMBINED='{
  "secu": {"alerts": 15, "blocked_ips": 3, "top_threat": "SSH brute force"},
  "web":  {"alerts": 8,  "blocked_ips": 1, "top_threat": "SQL Injection"},
  "siem": {"total_events": 5000, "critical": 2, "high": 15}
}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC 매니저입니다. 여러 보안 시스템의 데이터를 종합 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"3개 서버의 보안 현황:\\n$COMBINED\\n\\n종합 위협 평가와 우선 대응 사항을 제시하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: 로컬 지식 수집

```bash
# 프로젝트 준비
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"knowledge-lab","request_text":"분산 지식 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 여러 서버에서 지식 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname && uname -r && ss -tlnp | grep LISTEN | wc -l", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"hostname && uname -r && ss -tlnp | grep LISTEN | wc -l", "risk_level":"low", "subagent_url":"http://10.20.30.1:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: 지식 기반 LLM 분석

```bash
# 수집된 정보를 LLM으로 종합 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "분산 시스템 보안 분석가입니다."},
      {"role": "user", "content": "2개 서버의 로컬 지식을 비교 분석하세요:\n\nopsclaw 서버: 커널 6.8.0-106, 열린 포트 5개 (22,8000,8001,8002,5432)\nsecu 서버: 커널 6.8.0-106, 열린 포트 3개 (22,8002,8443)\n\n각 서버의 보안 수준을 평가하고 개선 사항을 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 분산 지식의 보안 고려사항

| 위험 | 대응 |
|------|------|
| 지식 변조 | PoW 체인으로 무결성 검증 |
| 오래된 지식 | TTL(Time-To-Live) 설정 |
| 과도한 공유 | need-to-know 원칙 적용 |
| 동기화 충돌 | 타임스탬프 기반 최신 우선 |

---

## 핵심 정리

1. 분산 지식은 각 SubAgent가 로컬 환경 정보를 자체 저장하는 구조이다
2. local_knowledge.json에 시스템 정보, 보안 기준선, 학습된 패턴을 저장한다
3. Manager를 통해 SubAgent 간 지식을 전달하여 전체 보안 수준을 높인다
4. LLM 프롬프트에 로컬 지식을 포함하면 더 정확한 맥락 분석이 가능하다
5. 지식의 무결성과 최신성을 유지하기 위한 검증 메커니즘이 필요하다

---

## 다음 주 예고
- Week 14: RL Steering - 보상 함수 설계와 행동 통제

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
