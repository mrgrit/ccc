# Week 11: 자율 미션

## 학습 목표
- 자율 미션(Autonomous Mission)의 개념을 이해한다
- Red Team / Blue Team 자율 에이전트의 동작 원리를 익힌다
- /a2a/mission API를 통한 자율 미션 실행을 실습한다
- Purple Team 자동화의 보안적 가치를 설명할 수 있다

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

## 1. 자율 미션이란?

자율 미션은 SubAgent가 **LLM의 추론 능력**을 활용하여 사람의 개입 없이 보안 작업을 수행하는 기능이다.

### 수동 실행 vs 자율 미션

| 항목 | 수동 (dispatch) | 자율 (mission) |
|------|---------------|---------------|
| 명령 | 사람이 직접 지정 | LLM이 스스로 결정 |
| 판단 | 사람이 결과 해석 | LLM이 결과 분석 후 다음 행동 결정 |
| 범위 | 단일 명령 | 목표 기반 다중 단계 |
| 자율성 | 없음 | 높음 |

---

## 2. Red Team vs Blue Team

> **이 실습을 왜 하는가?**
> "자율 미션" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 역할 정의

| 팀 | 목표 | LLM 모델 | 성격 |
|----|------|---------|------|
| **Red Team** | 취약점 탐색, 공격 시뮬레이션 | gemma3:12b | 공격적, 탐색적 |
| **Blue Team** | 방어, 탐지, 대응 | llama3.1:8b | 방어적, 분석적 |

### 2.2 Purple Team

Red와 Blue를 동시에 운영하여 서로 상호작용하게 한다.

```
Red Team: 취약점 발견 → 공격 시도
    ↕ (정보 공유)
Blue Team: 공격 탐지 → 방어 강화
    ↕ (결과 피드백)
보안 수준 지속 향상
```

---

## 3. 자율 미션을 Bastion에게 지시하기

Bastion은 `/ask`·`/chat` 을 통해 자연어 미션을 받는다. 복잡한 미션은 `/chat` NDJSON 스트림이
더 적합하다 — 단계별 생각·Skill 호출·증거 수집 이벤트를 실시간으로 관찰할 수 있다.

### 3.1 Red Team 자율 미션

```bash
# Red Team 공격 시뮬레이션 (교육/테스트 환경 전용)
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "RED_MISSION: web 자산(10.20.30.80)의 열린 포트·서비스·버전 헤더를 탐색하고 취약 가능성이 있는 지점을 보고서로 정리해줘. 실제 익스플로잇은 금지, 정보 수집·분석만."}'
```

Bastion이 내부에서 수행하는 것(예):
- `network.scan_tcp{asset=web, ports=1-1024}`
- `http.headers{asset=web, path=/}`
- `service.fingerprint{asset=web, ports=[80,8000,8002]}`
- `/evidence` 에 각 단계 저장, 최종 요약을 `answer`/`final` 이벤트로 반환

### 3.2 미션의 실행 흐름 (논리)

`/chat` 스트림에서 관찰 가능한 이벤트 흐름:

```
1. think   — 미션 목표를 Skill 조합으로 분해
2. tool    — 첫 Skill 호출 (대상 자산의 SubAgent 경유)
3. evidence — 결과가 /evidence 에 기록됨
4. think   — 결과 해석, 다음 Skill 선택
5. ... (반복)
6. final   — 최종 보고서 (answer)
```

### 3.3 Blue Team 자율 미션

```bash
# Blue Team은 의도적으로 다른 관점 — 탐지·방어
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "BLUE_MISSION: web 자산에서 방금 수집된 Red 결과에 대응해 방어 조치 후보를 제시하고, 저위험 조치(예: SSH 설정 교정·Apache 헤더 마스킹)는 자동 적용, 고위험(방화벽 규칙 추가)은 승인 요구만 해줘."}'
```

Bastion은 각 조치의 `risk` 를 보고 low/medium은 즉시 실행, high는 승인 이벤트를 발행한다.

### 3.4 Red·Blue 모델 분리 — LLM 다각화

원시 LLM 관점에서 Red/Blue에 **다른 모델을 쓰면** 독립성이 커진다. 이는 Ollama :11434 에서 직접 호출하는 구간에 쓸 수 있다:

```bash
# Red 관점: gemma3:12b
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 분석가. 교육/테스트 환경 전용."},
      {"role": "user", "content": "web 서버(10.20.30.80)의 22/80/8000/8002 포트가 열려 있다. 공격 가능 경로 3개를 우선순위로 정리해줘."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# Blue 관점: llama3.1:8b (모델 벤더를 분리해 편향 완화)
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "Blue Team 방어 전문가."},
      {"role": "user", "content": "web(10.20.30.80): SSH 22 외부노출, nginx 버전 헤더 노출, Docker 소켓 접근 가능 — 각 취약점에 대한 구체 방어 명령/설정을 제시."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. Purple Team 자동화

### 4.1 Red → Blue 루프 (Bastion 경유)

```bash
# Step 1: Bastion에게 Red 관점 점검 요청 → 결과는 자동으로 /evidence 에 남는다
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 SSH·HTTP 노출 상태를 읽기 전용으로 확인해줘"}'

# Step 2: 직전 증거를 근거로 Blue 관점 방어 제안
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "최근 /evidence 에 남은 web 점검 결과를 근거로 방어 조치(명령/설정)를 제시해줘. low는 실행 제안, high는 승인 요구로 분리"}'

# Step 3: 실행은 /chat 에서 승인 이벤트에 응답한 뒤 Bastion이 수행
```

### 4.2 자동화 스크립트 — Ollama 직접 호출(편향 완화)

Bastion을 경유하지 않고 Red/Blue 관점을 **서로 다른 모델**로 독립적으로 얻을 때 사용한다.
실제 변경 적용은 여전히 Bastion을 통해야 한다(증거·승인 게이트 때문).

```python
#!/usr/bin/env python3
"""purple_team_auto.py — Red/Blue 관점을 다른 모델로 분리 수집"""
import requests

OLLAMA  = "http://10.20.30.200:11434/v1/chat/completions"
BASTION = "http://10.20.30.200:8003"

def red_view(target):
    r = requests.post(OLLAMA, json={
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": "Red Team 분석가. 교육/테스트 환경 전용. JSON 리스트로 보고."},
            {"role": "user", "content": f"대상 {target}의 일반적 Linux 서버 공격 표면 3가지를 우선순위로 식별."}
        ],
        "temperature": 0.3
    })
    return r.json()["choices"][0]["message"]["content"]

def blue_view(findings):
    r = requests.post(OLLAMA, json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": "Blue Team 방어 전문가. 각 항목에 구체 명령/설정 제시."},
            {"role": "user", "content": f"다음 표면에 대한 방어 조치:\n{findings}"}
        ],
        "temperature": 0.3
    })
    return r.json()["choices"][0]["message"]["content"]

def bastion_evidence(limit=5):
    return requests.get(f"{BASTION}/evidence?limit={limit}").json()

findings = red_view("10.20.30.80")
print("=== Red 관점(gemma3:12b) ===\n", findings)
print("\n=== Blue 관점(llama3.1:8b) ===\n", blue_view(findings))
print("\n=== 최근 Bastion 증거 ===\n", bastion_evidence(5))
```

---

## 5. 실습

### 실습 1: Bastion에게 Red 미션을 자연어로 지시

```bash
# 읽기 전용 Red 점검 — web 자산의 노출 표면 파악
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 listening ports, HTTP 서버 헤더, 로그인 가능한 로컬 사용자 목록을 읽기 전용으로 수집해줘"}'

# 방금 실행된 흐름을 증거로 확인
curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=10" | python3 -m json.tool
```

### 실습 2: Red 결과를 Ollama에게 심화 분석 요청

```bash
# 증거에서 원문 발췌 후 분석 (원시 LLM 직접 호출)
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 분석가. 교육/테스트 환경 전용. 수집 정보에서 공격 경로·MITRE ATT&CK 매핑을 제시."},
      {"role": "user", "content": "수집 결과(요약):\n- 열린 포트: 22/80/8000/8002\n- HTTP 헤더: Server: nginx/1.24.0\n- 로컬 사용자: root, bastion, student\n\n공격 가능 경로 3개를 우선순위로 정리하고 각각 ATT&CK 기법 ID를 붙여줘."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: Blue 대응을 Bastion에서 제안 → 저위험만 자동 적용

```bash
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "실습 1의 결과에 대응해 web 자산에 적용할 방어 조치를 제안해줘. low는 실행 제안, high/critical은 승인 요구만. 각 조치에 Skill 이름을 명시."}'
```

---

## 6. 안전 고려사항

자율 미션은 강력하지만 위험할 수 있다.

| 위험 | 방어 |
|------|------|
| 과도한 스캔 | rate limiting, 대상 화이트리스트 |
| 파괴적 명령 실행 | risk_level + dry_run |
| 정보 유출 | 미션 결과 접근 제어 |
| 무한 루프 | 최대 단계 수 제한 |

### 안전 규칙

1. 자율 미션은 **테스트 환경에서만** 실행한다
2. critical risk 명령은 **사용자 확인 필수**이다
3. 모든 미션 결과는 **PoW 체인에 기록**된다
4. **프로덕션 환경**에서는 읽기 전용 미션만 허용한다

---

## 핵심 정리

1. 자율 미션은 LLM이 스스로 판단하고 행동하는 보안 작업이다
2. Red Team은 공격 시뮬레이션, Blue Team은 방어 강화를 수행한다
3. Purple Team은 Red/Blue를 결합하여 보안 수준을 지속 향상시킨다
4. 안전 장치(risk_level, dry_run, PoW)로 자율 미션의 위험을 관리한다
5. 자율 미션은 보조 도구이며, 최종 판단은 사람이 내린다

---

## 다음 주 예고
- Week 12: Agent Daemon - explore + daemon + stimulate

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
POST /ask       → 단일 자연어 질의
POST /chat      → NDJSON 스트림 대화 (think/tool/evidence/final 이벤트)
GET  /evidence  → 실행 증거 (자산·skill·exit·시각)
GET  /skills    → Skill 목록
GET  /playbooks → Playbook 목록
GET  /assets    → 자산 인벤토리
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

## 실제 사례 (WitFoo Precinct 6 — 자율 미션)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *AI 에이전트의 자율 미션 수행 능력* 학습 항목 매칭.

### 자율 미션 = "사람의 지시 없이 목표를 향해 다단계 작업 수행"

**자율 미션 (Autonomous Mission)** 은 AI 에이전트의 가장 진화된 형태다. 일반 에이전트는 *사람이 명령을 내리면* 그 명령을 수행하지만, 자율 미션 에이전트는 — *추상적 목표만 받고, 구체적 단계를 스스로 계획하고 실행* 한다.

dataset 에 적용하면 — 사람이 *"오늘 들어온 13K 신호 중 critical 인 것들을 찾아 차단 룰까지 작성하고 보고서를 만들라"* 라는 *추상 목표* 만 주면, Bastion 이 자동으로 — (1) 신호 분류, (2) critical 묶음 분석, (3) chain 추출, (4) 룰 생성, (5) 룰 검증, (6) 보고서 작성 의 6 단계를 *스스로* 수행한다. 사람의 추가 지시 없이.

```mermaid
graph TB
    GOAL["사람의 추상 목표:<br/>'오늘 신호 분석 + 룰 + 보고서'"]
    GOAL -->|Bastion 받음| PLAN["LLM 으로<br/>실행 계획 작성"]
    PLAN --> S1["1. 13K 신호 분류"]
    S1 --> S2["2. critical 묶음 분석"]
    S2 --> S3["3. attack chain 추출"]
    S3 --> S4["4. SIGMA 룰 생성"]
    S4 --> S5["5. 룰 검증<br/>(dataset recall/precision)"]
    S5 --> S6["6. 보고서 작성"]
    S6 -->|결과| RESULT["사람에게 결과 보고"]
    S5 -->|실패 시| RETRY["재시도 / 계획 수정"]
    RETRY --> S2

    style GOAL fill:#ffe6cc
    style RESULT fill:#ccffcc
```

**그림 해석**: Bastion 은 *추상 목표 → 실행 계획 6단계 → 단계별 자율 실행* 를 한 번의 호출에 수행. 단계 5의 검증 실패 시 *재시도/계획 수정* 의 자기 회복 메커니즘이 있어야 자율 미션이 성립.

### Case 1: dataset 13K 신호 분석의 자율 미션 — 정량 KPI

| 평가 축 | 임계값 | 의미 |
|---|---|---|
| 작업 완료율 | ≥95% | 6 단계 모두 완료 |
| 단계별 정확도 | ≥90% | 각 단계의 결과 품질 |
| 자기 회복 | 1회 실패 시 재시도 성공 | 자율성의 정량 |
| 사람 개입 | 0회 (이상적) | 진짜 자율 미션 |

**자세한 해석**:

자율 미션의 평가는 *"사람 개입 없이 끝났는가"* 가 본질이다. 6단계 중 1단계라도 사람의 추가 입력이 필요하면 — 그것은 *반자율 미션* 이고, 자율 미션의 가치는 *0회 사람 개입* 으로만 입증된다.

**작업 완료율 ≥95%** 는 — 100번 시도하면 95번 완료. 5번은 자기 회복 후에도 실패하여 사람에게 escalation. 100% 완료를 목표로 하면 *너무 보수적이라 진척 없음*, 90% 미만이면 *너무 위험해서 사람 부담 증가*. 95% 가 운영 균형점.

**자기 회복** 은 — 단계 5의 검증이 실패해도 (예: 생성한 SIGMA 룰의 recall 80% 미만), Bastion 이 *스스로 단계 2로 돌아가 다시 실행* 하는 능력. 이 회복 메커니즘이 없으면 — 첫 실패에서 모든 작업이 멈추는 fragile 시스템.

학생이 알아야 할 것은 — **자율 미션의 성공 = 정량 KPI + 자기 회복 + 0 사람 개입의 3가지 조건 동시 만족** 이라는 점. 이 3가지를 모두 측정하는 평가 framework 이 있어야 자율 미션이 검증된다.

### Case 2: 자율 미션 vs 일반 에이전트 — 정량 비교

| 항목 | 일반 에이전트 | 자율 미션 에이전트 |
|---|---|---|
| 입력 방식 | 구체적 명령 1개 | 추상 목표 1개 |
| 작업 분해 | 사람이 한 단계씩 지시 | 에이전트가 자동 분해 |
| 실패 대응 | 사람이 재지시 | 자기 회복 |
| 운영 부담 | 사람 시간 ~50% | 사람 시간 ~5% |
| 학습 매핑 | §"자율성의 운영 효과" | 사람 시간 10배 절감 |

**자세한 해석**:

자율 미션의 운영 효과는 *사람 시간 10배 절감* 이다. 일반 에이전트는 분석가가 *매 단계마다 다음 명령을 내려야* 하므로 분석가 시간의 ~50% 가 에이전트 조작에 소비된다. 자율 미션 에이전트는 *추상 목표 한 번 + 결과 검토* 만 분석가가 하면 되므로 ~5% 시간 소비.

이 차이가 SOC 운영의 *규모 가능성* 을 결정한다 — 분석가 1명이 일반 에이전트로는 ~10건/일 처리, 자율 미션으로는 ~100건/일 처리. *동일 인력으로 10배의 사고 처리* 가능.

학생이 알아야 할 것은 — **자율성은 *AI 의 똑똑함* 이 아니라 *사람의 시간을 절약* 하는 도구** 라는 점. 자율 미션의 가치 측정도 *"AI 가 얼마나 잘하는가"* 가 아니라 *"분석가의 시간이 얼마나 줄었는가"* 로 한다.

### 이 사례에서 학생이 배워야 할 3가지

1. **자율 미션 = 추상 목표 → 자동 분해 → 자기 회복** — 사람 개입 0회가 핵심.
2. **3가지 KPI 동시 측정** — 완료율 95% + 단계 정확도 90% + 자기 회복 + 사람 개입 0.
3. **자율성의 가치는 시간 절감** — 분석가 시간 50% → 5% 로 10배 효율.

**학생 액션**: Bastion 에 *"오늘 dataset 의 임의 1,000 신호를 분류하고 critical 5건의 chain 분석 + 룰 생성"* 의 단일 추상 목표를 입력. 진행 중 사람 개입 횟수와 최종 완료 시점을 기록. 결과를 *"우리 Bastion 이 lecture 의 자율 미션 정의를 만족하는가"* 평가.


---

## 부록: 학습 OSS 도구 매트릭스 (Course7 AI Security — Week 11 LLM 모니터링/로깅)

### LLM Observability OSS 도구

| 영역 | OSS 도구 |
|------|---------|
| LLM 전용 | **Langfuse** (OSS Self-host) / **Phoenix-Arize** / Helicone-OSS |
| Trace + Metric | **OpenTelemetry** + OpenLLMetry / Jaeger / Tempo |
| Prompt management | **Langfuse** prompts / Helicone Templates / PromptLayer-OSS |
| 비용 추적 | LiteLLM cost callback / Langfuse cost tracking |
| Quality 평가 | Ragas / DeepEval / TruLens |
| Anomaly detection | LangSmith (commercial) / 자체 ML on Langfuse data |

### 핵심 — Langfuse (OSS LangSmith 대안)

```bash
# self-host
docker run -d -p 3001:3000 \
  -e DATABASE_URL=postgresql://langfuse:secret@postgres:5432/langfuse \
  -e SALT=secret \
  -e NEXTAUTH_SECRET=secret \
  -e NEXTAUTH_URL=http://localhost:3001 \
  -e LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-xxx \
  -e LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-xxx \
  langfuse/langfuse:latest

# Python SDK 통합
python3 << 'EOF'
from langfuse import Langfuse
from langfuse.openai import openai                                # 자동 wrapper

langfuse = Langfuse(
  host="http://localhost:3001",
  public_key="pk-xxx",
  secret_key="sk-xxx",
)

client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
# 모든 호출 자동 trace
r = client.chat.completions.create(
  model="gemma3:4b",
  messages=[{"role":"user","content":"Hello"}]
)
EOF
# → http://localhost:3001 에서 모든 호출 시각화
```

### 학생 환경 준비

```bash
source ~/.venv-llm/bin/activate
pip install langfuse phoenix-arize openllmetry-sdk \
  ragas deepeval trulens-eval

# Phoenix (Arize OSS — 시각화 강력)
python3 -m phoenix.server.main serve

# OpenLLMetry — OpenTelemetry-based
pip install traceloop-sdk
```

### 핵심 사용

```bash
# 1) Langfuse 자동 로깅 (모든 LLM 호출)
# 위 langfuse SDK + openai wrapper

# 2) Phoenix (LangChain 통합)
python3 << 'EOF'
import phoenix as px
session = px.launch_app()                                         # http://localhost:6006

from phoenix.trace.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument()

# 이제 모든 LangChain 호출이 phoenix 에 자동 기록
EOF

# 3) Ragas (RAG 품질 평가)
python3 << 'EOF'
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

dataset = [...]                                                   # question, answer, contexts
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
print(result)
EOF

# 4) TruLens (LLM eval)
python3 << 'EOF'
from trulens_eval import Tru, Feedback
tru = Tru()
@tru.app(app_id="my_app")
def my_app(prompt):
    ...
EOF

# 5) OpenLLMetry (OTel 표준)
python3 << 'EOF'
from traceloop.sdk import Traceloop
Traceloop.init(app_name="my_llm_app")
# 모든 LLM 호출 자동 OTel trace
EOF
```

### 모니터링 대시보드 (학생 목표)

```
[Langfuse] - 모든 호출 trace + cost
[Phoenix] - LangChain chain 시각화
[Grafana] - Prometheus metric (latency, tokens/s, error rate)
[Loki] - 모든 LLM 응답 로그 검색
[Ragas] - RAG 품질 정량 평가 (분기)
```

학생은 본 11주차에서 **Langfuse + Phoenix + Ragas + OpenLLMetry + LiteLLM callbacks** 5 도구로 LLM observability 4 축 (trace / metric / cost / quality) 통합 모니터링을 OSS 만으로 구축한다.
