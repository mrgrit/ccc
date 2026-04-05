# Week 12: Agent Daemon

## 학습 목표
- Agent Daemon의 3가지 모드(explore, daemon, stimulate)를 이해한다
- 자율 보안 관제의 개념과 동작 원리를 설명할 수 있다
- Daemon 모드의 지속적 모니터링 기능을 실습한다
- Stimulate 모드로 능동적 보안 테스트를 수행할 수 있다

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

# Week 12: Agent Daemon

## 학습 목표
- Agent Daemon의 3가지 모드(explore, daemon, stimulate)를 이해한다
- 자율 보안 관제의 개념과 동작 원리를 설명할 수 있다
- Daemon 모드의 지속적 모니터링 기능을 실습한다
- Stimulate 모드로 능동적 보안 테스트를 수행할 수 있다

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
curl -s http://192.168.0.105:11434/v1/chat/completions \
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

### 2.2 OpsClaw로 Explore 실행

OpsClaw execute-plan으로 대상 서버의 시스템 정보(OS, 포트, 사용자, 서비스, 디스크)를 자동 수집한다. 수집된 데이터는 OODA Loop의 Observe 단계에 해당한다.

```bash
# OODA Observe: 5가지 정보 수집 태스크 (uname, ss, passwd, systemctl, df)
PID="프로젝트_ID"

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a && cat /etc/os-release | head -5", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":3, "instruction_prompt":"cat /etc/passwd | wc -l && who", "risk_level":"low"},
      {"order":4, "instruction_prompt":"systemctl list-units --type=service --state=running | head -20", "risk_level":"low"},
      {"order":5, "instruction_prompt":"df -h && mount | grep -v cgroup | head -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
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

### 3.2 Daemon 루프 개념

```python
"""daemon_loop.py - 개념 코드 (실제 OpsClaw Daemon은 내부 구현)"""
import time
import requests

OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def check_ports(pid):
    """열린 포트 변화 감지"""
    return requests.post(
        f"{OPSCLAW}/projects/{pid}/dispatch",
        headers=HEADERS,
        json={"command": "ss -tlnp", "subagent_url": "http://localhost:8002"}
    ).json()

def check_users(pid):
    """로그인 사용자 변화 감지"""
    return requests.post(
        f"{OPSCLAW}/projects/{pid}/dispatch",
        headers=HEADERS,
        json={"command": "who", "subagent_url": "http://localhost:8002"}
    ).json()

def analyze_with_llm(data):
    """LLM으로 이상 탐지"""
    resp = requests.post(
        "http://192.168.0.105:11434/v1/chat/completions",
        json={
            "model": "gemma3:12b",
            "messages": [
                {"role": "system", "content": "보안 관제 에이전트. 이상을 탐지하면 ALERT, 정상이면 OK를 응답."},
                {"role": "user", "content": f"점검 결과:\n{data}\n\n이상 여부를 판단하세요."}
            ],
            "temperature": 0
        }
    )
    return resp.json()["choices"][0]["message"]["content"]
```

### 3.3 변화 탐지 원리

```
이전 상태 (baseline)    현재 상태          비교 결과
열린 포트: 22,80        열린 포트: 22,80,4444   새 포트 4444 발견!
사용자: opsclaw         사용자: opsclaw,hacker  새 사용자 hacker!
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
# 안전한 stimulation: 존재하지 않는 사용자로 SSH 시도
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "ssh -o BatchMode=yes -o ConnectTimeout=3 testuser@localhost echo test 2>&1 || true",
    "subagent_url": "http://localhost:8002"
  }'

# 이후 Wazuh에서 알림이 발생하는지 확인
```

### 4.3 LLM으로 Stimulate 계획 수립

LLM에게 SIEM 탐지 능력 검증을 위한 안전한 stimulation 시나리오를 자동 설계시킨다. 실제 피해를 주지 않는 테스트 이벤트만 생성한다.

```bash
# LLM으로 SIEM 탐지 검증용 안전한 시나리오 5가지 자동 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
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

### 실습 1: Explore 실행

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"daemon-lab","request_text":"Agent Daemon 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# Explore: 기준선 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"ss -tlnp | grep LISTEN", "risk_level":"low"},
      {"order":2, "instruction_prompt":"who 2>/dev/null; last -5", "risk_level":"low"},
      {"order":3, "instruction_prompt":"ps aux --sort=-%mem | head -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: Daemon 점검 시뮬레이션

```bash
# 30초 간격으로 2번 점검하여 변화 비교
for i in 1 2; do
  echo "=== 점검 $i ==="
  curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: opsclaw-api-key-2026" \
    -d '{"command":"ss -tlnp | grep LISTEN | md5sum","subagent_url":"http://localhost:8002"}' \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result','')[:100])"
  sleep 5
done
```

### 실습 3: Stimulate + 탐지 확인

```bash
# SSH 인증 실패 이벤트 생성
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "for i in 1 2 3; do ssh -o BatchMode=yes -o ConnectTimeout=1 -o StrictHostKeyChecking=no fakeuser@localhost 2>&1; done || true",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 결과를 LLM으로 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "SSH 인증 실패 이벤트를 3회 생성했습니다. Wazuh SIEM에서 이를 탐지했다면 어떤 룰이 발동되었을까요? 예상 룰 ID와 설명을 알려주세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
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
