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

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

