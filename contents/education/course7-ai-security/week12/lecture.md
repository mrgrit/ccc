# Week 12: Agent Daemon

## 학습 목표
- Agent Daemon의 3가지 모드(explore, daemon, stimulate)를 이해한다
- 자율 보안 관제의 개념과 동작 원리를 설명할 수 있다
- Daemon 모드의 지속적 모니터링 기능을 실습한다
- Stimulate 모드로 능동적 보안 테스트를 수행할 수 있다

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

## 1. Agent Daemon이란?

Agent Daemon은 SubAgent가 **백그라운드에서 지속적으로** 보안 관제를 수행하는 기능이다.
단발성 명령 실행을 넘어 자율적인 보안 모니터링을 가능하게 한다.

### 3가지 모드

| 모드 | 목적 | 동작 |
|------|------|------|
| **explore** | 환경 탐색 | 시스템 상태 파악, 자산 목록 작성 |
| **daemon** | 지속 감시 | 주기적 점검, 이상 탐지 |
| **stimulate** | 능동 테스트 | 보안 이벤트 생성, 탐지 능력 검증 |

---

## 2. Explore 모드

> **이 실습을 왜 하는가?**
> "Agent Daemon" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

시스템 환경을 자동으로 탐색하여 보안 기준선(baseline)을 수립한다.

### 2.1 Explore 실행

> **실습 목적**: AI 모델에 대한 추출/추론 공격의 원리를 이해하고 방어 전략을 수립하기 위해 수행한다
>
> **배우는 것**: 모델 추출(Model Extraction) 공격으로 API 호출만으로 모델을 복제하는 원리와, 멤버십 추론으로 학습 데이터를 유추하는 기법을 이해한다
>
> **결과 해석**: 복제 모델의 정확도가 원본에 근접할수록 추출 공격이 성공적이며, 방어책 적용 후 정확도 저하로 효과를 측정한다
>
> **실전 활용**: AI 모델 API 설계 시 Rate Limiting, 출력 라운딩, 워터마킹 등 모델 보호 전략 수립에 활용한다

```bash
# LLM이 환경을 파악하기 위한 탐색 수행
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 관제 에이전트입니다. 시스템 환경을 탐색하여 보안 기준선을 수립합니다. 실행해야 할 명령어 목록을 제시하세요."},
      {"role": "user", "content": "Linux 서버의 보안 기준선을 수립하기 위해 수집해야 할 정보를 나열하세요. 각 항목에 대한 명령어를 포함하세요.\n\n범주: 시스템정보, 네트워크, 사용자, 서비스, 파일시스템"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.2 Bastion에게 Explore 자연어 지시

자연어 한 번이면 Bastion이 시스템정보·포트·사용자·서비스·디스크 Skill 을 묶어 수행한다.
결과는 `/evidence` 에 남아 이후 비교(baseline) 의 기준이 된다.

```bash
# OODA Observe 단계 — 한 번의 /ask 로 baseline 수집
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 시스템정보·listening ports·로컬사용자·실행중 서비스·디스크 사용량을 한 번에 수집해 baseline 로 기록해줘"}'

# 증거 조회 (baseline 보관용)
curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=10" | python3 -m json.tool
```

---

## 3. Daemon 모드

주기적으로 보안 상태를 점검하고 이상을 탐지한다.

### 3.1 Daemon 점검 항목

```
매 5분마다:
├── 열린 포트 변화 확인
├── 로그인 사용자 변화 확인
├── 프로세스 이상 확인
└── 로그 이상 패턴 확인

매 1시간마다:
├── 파일 무결성 확인
├── 디스크 사용량 확인
├── 보안 업데이트 확인
└── 설정 파일 변경 확인
```

### 3.2 Daemon 루프 개념 — Bastion 자연어 + Ollama 결정

실제 Bastion Daemon은 내부 구현이지만, 외부에서 동일 로직을 조합할 수 있다.

```python
"""daemon_loop.py — 개념 코드. 운영에서는 Bastion이 내부 데몬으로 수행."""
import time, requests

BASTION = "http://10.20.30.200:8003"
OLLAMA  = "http://10.20.30.200:11434/v1/chat/completions"

def bastion_ask(message):
    # Bastion은 자산 라우팅·Skill 선택·증거 기록까지 담당한다
    return requests.post(f"{BASTION}/ask", json={"message": message}).json().get("answer","")

def check_ports():   return bastion_ask("web 자산의 현재 listening ports 만 수집해줘")
def check_users():   return bastion_ask("web 자산의 현재 로그인 사용자(who) 만 수집해줘")

def classify(data):
    # 원시 LLM에게 이상 여부 판단 요청 (결정론)
    r = requests.post(OLLAMA, json={
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": "보안 관제 에이전트. 이상이면 ALERT, 정상이면 OK 한 토큰만."},
            {"role": "user",   "content": f"점검 결과:\n{data}\n\n이상 여부?"}
        ],
        "temperature": 0
    })
    return r.json()["choices"][0]["message"]["content"].strip()

while True:
    p = check_ports(); u = check_users()
    print(classify(p + "\n" + u))
    time.sleep(60)
```

### 3.3 변화 탐지 원리

```
이전 상태 (baseline)    현재 상태          비교 결과
열린 포트: 22,80        열린 포트: 22,80,4444   새 포트 4444 발견!
사용자: bastion         사용자: bastion,hacker  새 사용자 hacker!
/etc/passwd hash: a1b2  /etc/passwd hash: c3d4  파일 변조 감지!
```

---

## 4. Stimulate 모드

보안 탐지 시스템이 제대로 작동하는지 **의도적으로 보안 이벤트를 생성**하여 검증한다.

### 4.1 Stimulate 시나리오

| 시나리오 | 생성 이벤트 | 예상 탐지 |
|---------|-----------|----------|
| SSH 브루트포스 | 잘못된 비밀번호로 반복 시도 | Wazuh rule 5710 |
| 파일 변조 | 테스트 파일 수정 | Wazuh FIM 알림 |
| 포트 스캔 | nmap 스캔 | Suricata alert |
| 웹 공격 | SQL Injection 시도 | WAF 차단 |

### 4.2 Stimulate 실행 예시

```bash
# 안전한 stimulation: 존재하지 않는 사용자로 SSH 실패 이벤트 발생
# Bastion 에게 명시적으로 "테스트 이벤트 생성"을 지시하면 Skill로 위임된다
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "STIMULATE: web 자산에서 존재하지 않는 사용자(testuser)로 SSH 1회 시도해 Wazuh SIEM 탐지 테스트 이벤트를 생성해줘. 실제 로그인은 실패해야 함"}'

# siem 자산에서 알림 확인
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "siem 자산의 /var/ossec/logs/alerts/alerts.json 최근 5건에서 rule.id 5710(Authentication failure) 관련 항목을 보여줘"}'
```

### 4.3 LLM으로 Stimulate 계획 수립

LLM에게 SIEM 탐지 능력 검증을 위한 안전한 stimulation 시나리오를 자동 설계시킨다. 실제 피해를 주지 않는 테스트 이벤트만 생성한다.

```bash
# LLM으로 SIEM 탐지 검증용 안전한 시나리오 5가지 자동 생성
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 테스트 전문가입니다. SIEM 탐지 능력을 검증하기 위한 안전한 테스트 시나리오를 설계합니다. 실제 피해를 주지 않는 안전한 방법만 사용합니다."},
      {"role": "user", "content": "Wazuh SIEM의 탐지 능력을 검증하기 위한 안전한 stimulation 시나리오 5가지를 설계하세요.\n\n각 시나리오에:\n1. 생성할 이벤트\n2. 실행 명령어\n3. 예상 탐지 룰\n4. 확인 방법\n을 포함하세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: Explore 기준선 수집

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 listening ports, who/last -5, top 10 메모리 프로세스를 수집해 baseline 로 기록해줘"}'

curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=5" | python3 -m json.tool
```

### 실습 2: Daemon 점검 반복 (변화 비교)

```bash
# 30초 간격 2회 점검 → 두 번째 호출에서 Bastion이 baseline과 자동 비교
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 현재 listening ports 를 baseline(실습1 결과)과 비교해 변화만 알려줘. 변화 없으면 OK 출력"}'

sleep 30

curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 현재 listening ports 를 baseline과 다시 비교해줘"}'
```

### 실습 3: Stimulate + SIEM 탐지 확인

```bash
# 테스트 이벤트 생성
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "STIMULATE: web 자산에서 fakeuser로 SSH 3회 실패 이벤트 발생 (BatchMode, ConnectTimeout=1)"}'

# SIEM 알림 확인 + LLM 해석 요청
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "siem 자산의 alerts.json 에서 방금 생성한 SSH 실패 이벤트에 매칭되는 Wazuh rule.id를 찾아주고, MITRE ATT&CK T1110(Brute Force)과의 연관성을 설명해줘"}'
```

---

## 6. Daemon의 보안적 가치

```
전통적 보안 관제                 Agent Daemon
──────────────                  ────────────
사람이 대시보드 모니터링          LLM이 자동 분석
정해진 룰로만 탐지               패턴 추론 가능
느린 대응 (시간~일)              빠른 대응 (분)
피로도 누적                     24/7 일관된 관제
```

---

## 핵심 정리

1. Explore는 시스템 환경을 탐색하여 보안 기준선을 수립한다
2. Daemon은 주기적으로 상태를 점검하여 변화와 이상을 탐지한다
3. Stimulate는 보안 이벤트를 생성하여 탐지 시스템을 검증한다
4. 세 모드를 조합하면 자율 보안 관제 사이클이 완성된다
5. LLM이 결과를 분석하므로 미리 정의되지 않은 이상도 탐지 가능하다

---

## 다음 주 예고
- Week 13: 분산 지식 - local_knowledge, knowledge transfer

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
POST /ask       → 자연어 단일 질의 (동기 {"answer": "..."})
POST /chat      → NDJSON 스트림 (think/tool/evidence/final)
GET  /evidence  → 실행 증거 (자산·skill·exit·stdout_head·시각)
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

### Wazuh SIEM (4.11.x)
> **역할:** 에이전트 기반 로그·FIM·SCA 통합 분석 플랫폼  
> **실행 위치:** `siem (10.20.30.100)`  
> **접속/호출:** Dashboard `https://10.20.30.100` (admin/admin), Manager API `:55000`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/var/ossec/etc/ossec.conf` | Manager 메인 설정 (원격, 전송, syscheck 등) |
| `/var/ossec/etc/rules/local_rules.xml` | 커스텀 룰 (id ≥ 100000) |
| `/var/ossec/etc/decoders/local_decoder.xml` | 커스텀 디코더 |
| `/var/ossec/logs/alerts/alerts.json` | 실시간 JSON 알림 스트림 |
| `/var/ossec/logs/archives/archives.json` | 전체 이벤트 아카이브 |
| `/var/ossec/logs/ossec.log` | Manager 데몬 로그 |
| `/var/ossec/queue/fim/db/fim.db` | FIM 기준선 SQLite DB |

**핵심 설정·키**

- `<rule id='100100' level='10'>` — 커스텀 룰 — level 10↑은 고위험
- `<syscheck><directories>...` — FIM 감시 경로
- `<active-response>` — 자동 대응 (firewall-drop, restart)

**로그·확인 명령**

- `jq 'select(.rule.level>=10)' alerts.json` — 고위험 알림만
- `grep ERROR ossec.log` — Manager 오류 (룰 문법 오류 등)

**UI / CLI 요점**

- Dashboard → Security events — KQL 필터 `rule.level >= 10`
- Dashboard → Integrity monitoring — 변경된 파일 해시 비교
- `/var/ossec/bin/wazuh-logtest` — 룰 매칭 단계별 확인 (Phase 1→3)
- `/var/ossec/bin/wazuh-analysisd -t` — 룰·설정 문법 검증

> **해석 팁.** Phase 3에서 원하는 `rule.id`가 떠야 커스텀 룰 정상. `local_rules.xml` 수정 후 `systemctl restart wazuh-manager`, 문법 오류가 있으면 **분석 데몬 전체가 기동 실패**하므로 `-t`로 먼저 검증.

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (12주차) 학습 주제와 직접 연관된 *실제* incident:

### Data Theft (T1041) — 99.99% 의 dataset 패턴

> **출처**: WitFoo Precinct 6 / `complete-mission cluster` (anchor: `anc-a0364e702393`) · sanitized
> **시점**: 다중 (전체 99.99%)

**관찰**: Precinct 6 의 incident 10,442건 중 mo_name=Data Theft + lifecycle=complete-mission 이 99.99%. T1041 (Exfiltration over C2 Channel).

**MITRE ATT&CK**: **T1041 (Exfiltration over C2 Channel)**

**IoC**:
  - `다양한 src→dst (sanitized)`
  - `suspicion≥0.7`

**학습 포인트**:
- *가장 많이 일어나는 공격* 의 baseline — 모든 IR 시나리오의 출발점
- C2 채널 (HTTP/HTTPS/DNS) 에 데이터 mixed → 정상 트래픽 위장
- 탐지: outbound 에 데이터 흐름 모니터링 (bytes_out 분포), CTI feed 매칭
- 방어: DLP (Data Loss Prevention), egress filter, 데이터 분류·암호화


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
