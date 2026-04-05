# Week 01: AI 에이전트란 무엇인가

## 학습 목표
- AI 에이전트의 정의와 Perceive→Decide→Act 순환 구조를 이해한다
- LLM 에이전트와 전통적 자동화 스크립트의 차이를 설명할 수 있다
- ReAct, Plan-and-Execute 등 주요 에이전트 패턴을 구분한다
- 보안 분야에서 AI 에이전트가 수행하는 역할을 파악한다
- Ollama를 이용해 첫 번째 에이전트 대화를 실행할 수 있다

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
| 0:00-0:30 | 이론: AI 에이전트 정의와 구조 (Part 1) | 강의 |
| 0:30-1:00 | 이론: 에이전트 패턴과 보안 응용 (Part 2) | 강의/토론 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: Ollama 설치와 첫 대화 (Part 3) | 실습 |
| 1:50-2:30 | 실습: Python으로 에이전트 루프 구현 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 보안 에이전트 프로토타입 (Part 5) | 실습 |
| 3:10-3:30 | 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## 용어 해설 (AI보안에이전트 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **AI 에이전트** | AI Agent | 환경을 인지하고 자율적으로 판단·행동하는 AI 시스템 | 현장 투입된 정보요원 |
| **LLM** | Large Language Model | 대규모 텍스트로 학습한 언어 모델 (GPT, Llama 등) | 방대한 지식을 가진 AI 두뇌 |
| **Perceive-Decide-Act** | 인지-판단-실행 | 에이전트의 핵심 순환 구조 | 눈으로 보고→머리로 판단→손으로 행동 |
| **ReAct** | Reasoning + Acting | 추론과 행동을 번갈아 수행하는 에이전트 패턴 | 생각하면서 움직이는 사람 |
| **Plan-and-Execute** | 계획 후 실행 | 전체 계획을 먼저 세운 뒤 순차 실행하는 패턴 | 작전 회의 후 출동하는 특공대 |
| **Tool Calling** | 도구 호출 | LLM이 외부 함수/API를 호출하는 기능 | 전문가에게 전화하는 상담원 |
| **프롬프트** | Prompt | LLM에 전달하는 입력 지시문 | AI에게 보내는 업무 지시서 |
| **Ollama** | Ollama | 로컬에서 LLM을 실행하는 오픈소스 플랫폼 | 내 PC에 설치하는 AI 서버 |
| **하네스** | Harness | 에이전트의 실행 환경과 제어 프레임워크 | 안전벨트+계기판 |
| **오케스트레이션** | Orchestration | 여러 에이전트/서비스를 조율하여 하나의 흐름으로 실행 | 오케스트라 지휘자 |
| **자동화** | Automation | 정해진 규칙대로 반복 수행 | 공장 컨베이어 벨트 |
| **자율** | Autonomy | 상황을 스스로 판단하여 결정·실행 | 자율주행차 |
| **Temperature** | Temperature | LLM 출력의 무작위성을 제어하는 매개변수 | 창의성 다이얼 |
| **토큰** | Token | LLM이 처리하는 텍스트의 최소 단위 | 글자 조각 |
| **컨텍스트 윈도우** | Context Window | LLM이 한 번에 처리할 수 있는 토큰 수 | AI의 단기 기억 용량 |
| **SOAR** | Security Orchestration, Automation and Response | 보안 자동화·대응 플랫폼 | 보안팀의 자동 비서 |
| **SubAgent** | SubAgent | 원격 서버에서 명령을 실행하는 하위 에이전트 | 본부 지시를 받는 현장 요원 |

---

## Part 1: AI 에이전트란 무엇인가 (30분) — 이론

### 1.1 에이전트의 정의

AI 에이전트(Agent)란 **환경을 인지(Perceive)하고, 판단(Decide)하며, 행동(Act)하는** 자율적 소프트웨어 시스템이다.

```
[AI 에이전트 루프]

  Perceive  ← 환경 관찰 (로그, 경보, 상태)
      |
      v
  Decide    ← LLM 추론 (분석, 계획)
      |
      v
  Act       ← 도구 실행 (명령, API 호출)
      |
      +---> 환경에 반영 ---> 반복
```

### 1.2 전통적 자동화 vs LLM 에이전트

| 구분 | 전통적 자동화 (스크립트) | LLM 에이전트 |
|------|------------------------|-------------|
| 판단 | if/else 규칙 고정 | 자연어 추론으로 유연한 판단 |
| 입력 | 정형 데이터만 처리 | 비정형 텍스트(로그, 경보) 처리 가능 |
| 확장 | 새 시나리오마다 코드 수정 | 프롬프트 변경만으로 대응 |
| 오류 대응 | 예외 코드 필수 | 문맥 이해로 fallback 가능 |
| 설명 가능성 | 코드 자체가 설명 | 추론 과정을 자연어로 출력 |
| 위험성 | 예측 가능 | 환각(hallucination) 가능 |

### 1.3 에이전트의 핵심 구성요소

1. **모델(Brain)**: LLM — 추론과 판단 담당
2. **도구(Tools)**: 외부 시스템과 상호작용 (명령 실행, API 호출, 파일 읽기)
3. **메모리(Memory)**: 이전 대화/작업 기록 유지
4. **계획(Planning)**: 복잡한 작업을 단계별로 분해
5. **실행 환경(Harness)**: 에이전트를 제어하고 안전하게 실행하는 프레임워크

### 1.4 보안 분야에서의 에이전트 역할

| 역할 | 설명 | 예시 |
|------|------|------|
| **경보 분류** | SIEM 경보를 자동 분석·우선순위 지정 | Wazuh 경보 → 심각도 분류 |
| **취약점 분석** | CVE 정보 수집·영향도 평가 | 새 CVE 발표 → 자사 시스템 영향 판단 |
| **사고 대응** | 침해 사고 자동 초동 대응 | IP 차단, 계정 잠금, 증거 수집 |
| **정책 관리** | 방화벽/WAF 정책 자동 최적화 | 트래픽 분석 → nftables 규칙 제안 |
| **보고서 생성** | 분석 결과를 자연어 보고서로 작성 | 일일 보안 리포트 자동 생성 |

---

## Part 2: 에이전트 패턴과 보안 응용 (30분) — 이론/토론

### 2.1 ReAct 패턴 (Reasoning + Acting)

ReAct 패턴은 **추론(Thought)과 행동(Action)을 번갈아** 수행한다.

```
[보안 에이전트 ReAct 예시]

Thought: Wazuh에서 brute-force 경보가 발생했다. 먼저 공격 IP를 확인해야 한다.
Action: fetch_log(source="wazuh", query="rule.id:5710", limit=10)
Observation: 공격 IP = 203.0.113.55, 시도 횟수 = 47회

Thought: 47회 시도는 임계값(20회)을 초과한다. IP를 차단해야 한다.
Action: run_command(host="secu", cmd="nft add rule inet filter input ip saddr 203.0.113.55 drop")
Observation: 규칙 추가 완료

Thought: 차단 완료. 결과를 보고서에 기록한다.
Action: write_report(summary="203.0.113.55 차단 완료, brute-force 47회 시도")
```

### 2.2 Plan-and-Execute 패턴

전체 계획을 먼저 수립한 뒤 순차적으로 실행한다.

```
[보안 점검 Plan-and-Execute 예시]

Plan:
  Step 1: 전체 서버 SSH 접속 상태 확인
  Step 2: 각 서버 OS 패치 상태 점검
  Step 3: 방화벽 규칙 검토
  Step 4: Wazuh 에이전트 연결 상태 확인
  Step 5: 결과 종합 보고서 생성

Execute:
  → Step 1 실행 → 성공
  → Step 2 실행 → web 서버 3개 패치 미적용 발견
  → Step 3 실행 → 성공
  → Step 4 실행 → siem 에이전트 정상
  → Step 5 실행 → 보고서 생성 완료
```

### 2.3 패턴 비교

| 패턴 | 장점 | 단점 | 적합한 상황 |
|------|------|------|------------|
| **ReAct** | 유연, 중간 결과 반영 | 방향성 잃을 수 있음 | 탐색적 분석, 경보 대응 |
| **Plan-and-Execute** | 구조적, 진행 추적 용이 | 계획 변경이 어려움 | 정기 점검, 다단계 작업 |
| **Hybrid** | 두 패턴의 장점 결합 | 구현 복잡도 증가 | 실무 에이전트 시스템 |

### 2.4 토론: AI 에이전트가 보안에 가져올 변화

- "에이전트가 SOC 분석가를 대체할 수 있는가?"
- "에이전트의 판단 오류(환각)로 정상 트래픽을 차단하면?"
- "에이전트 실행 권한은 어디까지 허용해야 하는가?"

---

## Part 3: Ollama 설치와 첫 대화 실습 (40분) — 실습

### 3.1 Ollama 서버 확인

dgx-spark 서버에 Ollama가 이미 설치되어 있다. 연결을 확인한다.

> **실습 목적**: AI 보안 에이전트의 두뇌 역할을 하는 LLM 서버(Ollama)의 상태를 확인하여, 에이전트 실습의 기반 환경을 검증한다.
>
> **배우는 것**: Ollama API로 사용 가능한 모델 목록을 조회하고, 모델별 크기/양자화 수준을 파악하여 에이전트에 적합한 모델을 선택하는 기준을 익힌다.
>
> **결과 해석**: models 배열에 모델이 출력되면 정상이다. parameter_size(8B/12B)는 추론 품질, quantization_level(Q4/Q8)은 메모리 효율을 나타낸다.
>
> **실전 활용**: 보안 에이전트 구축 시 모델 선택은 성능/비용/정확도의 트레이드오프이며, 로컬 모델은 데이터 유출 위험을 원천 차단한다.

```bash
# Ollama 서버 상태 확인 (dgx-spark)
curl -s http://192.168.0.105:11434/api/tags | python3 -m json.tool

# 사용 가능한 모델 목록 확인
curl -s http://192.168.0.105:11434/api/tags | \
  python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models']]"
```

### 3.2 첫 번째 LLM 대화 (curl)

OpenAI 호환 API를 사용하여 Ollama와 대화한다.

```bash
# Ollama에 간단한 질문 보내기 (OpenAI 호환 엔드포인트)
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "너는 보안 전문가이다."},
      {"role": "user", "content": "SQL Injection이 무엇인지 3줄로 설명해줘."}
    ],
    "temperature": 0.3
  }' | python3 -m json.tool
```

### 3.3 메시지 구조 이해

```bash
# system 메시지 변경 실험: 역할에 따라 응답이 달라지는지 확인
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "너는 해커 출신 보안 컨설턴트이다. 공격자 관점에서 설명한다."},
      {"role": "user", "content": "웹서버를 공격하려면 가장 먼저 무엇을 하는가?"}
    ],
    "temperature": 0.5
  }' | python3 -c "
import sys, json
# JSON 응답에서 assistant 메시지만 추출
resp = json.load(sys.stdin)
print(resp['choices'][0]['message']['content'])
"
```

### 3.4 Temperature 실험

```bash
# temperature=0 (결정적 응답) — 같은 질문에 항상 동일한 답변
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "리눅스 보안 점검 항목 5개를 나열해줘"}],
    "temperature": 0.0
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# temperature=1.0 (높은 무작위성) — 매번 다른 답변
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "리눅스 보안 점검 항목 5개를 나열해줘"}],
    "temperature": 1.0
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## Part 4: Python으로 에이전트 루프 구현 (40분) — 실습

### 4.1 기본 LLM 호출 함수 작성

opsclaw 서버에서 Python 스크립트를 작성한다.

```bash
# 작업 디렉토리 생성
mkdir -p ~/lab/week01
# 파이썬 스크립트 생성
cat > ~/lab/week01/llm_client.py << 'PYEOF'
"""
Week 01 실습: 기본 LLM 클라이언트
Ollama OpenAI-호환 API를 사용하여 LLM과 대화한다.
"""
import requests
import json

# Ollama 서버 설정
OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

def chat(messages: list, temperature: float = 0.3) -> str:
    """LLM에 메시지를 보내고 응답을 받는다."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    # POST 요청으로 LLM 호출
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    # 응답에서 assistant 메시지 추출
    return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    # 테스트: 간단한 보안 질문
    messages = [
        {"role": "system", "content": "너는 보안 전문가이다. 간결하게 답변한다."},
        {"role": "user", "content": "리눅스 서버의 SSH 보안 강화 방법 3가지를 알려줘."},
    ]
    answer = chat(messages)
    print("=== LLM 응답 ===")
    print(answer)
PYEOF

# 스크립트 실행
cd ~/lab/week01 && python3 llm_client.py
```

### 4.2 Perceive-Decide-Act 루프 구현

```bash
cat > ~/lab/week01/simple_agent.py << 'PYEOF'
"""
Week 01 실습: 간단한 Perceive-Decide-Act 에이전트
서버 상태를 확인하고, LLM이 판단하여, 조치를 실행한다.
"""
import subprocess
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

def chat(messages: list) -> str:
    """LLM 호출 함수"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
    }, timeout=120)
    return resp.json()["choices"][0]["message"]["content"]

def perceive() -> str:
    """환경 관찰: 시스템 상태 수집"""
    commands = {
        "uptime": "uptime",
        "disk_usage": "df -h / | tail -1",
        "memory": "free -m | grep Mem",
        "load_avg": "cat /proc/loadavg",
        "login_failures": "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0",
    }
    results = {}
    for name, cmd in commands.items():
        # 각 명령을 실행하여 시스템 상태 수집
        try:
            output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            results[name] = output.stdout.strip()
        except Exception as e:
            results[name] = f"ERROR: {e}"
    return json.dumps(results, indent=2, ensure_ascii=False)

def decide(observation: str) -> str:
    """LLM에게 판단 요청"""
    messages = [
        {
            "role": "system",
            "content": """너는 리눅스 보안 관리자 AI이다.
서버 상태 정보를 받으면 다음을 수행한다:
1. 현재 상태를 평가한다 (정상/주의/위험)
2. 문제가 있으면 조치 사항을 제안한다
3. JSON 형식으로 응답한다: {"status": "정상|주의|위험", "analysis": "분석 내용", "actions": ["조치1", "조치2"]}"""
        },
        {
            "role": "user",
            "content": f"다음 서버 상태를 분석해줘:\n{observation}"
        }
    ]
    return chat(messages)

def act(decision: str):
    """결정에 따라 행동 (이 실습에서는 출력만)"""
    print("\n=== 에이전트 결정 ===")
    print(decision)
    print("\n(실제 환경에서는 여기서 자동 조치를 실행합니다)")

def main():
    """에이전트 메인 루프 (1회 실행)"""
    print("=" * 60)
    print("  Simple Security Agent — Perceive-Decide-Act")
    print("=" * 60)

    # Step 1: 환경 관찰
    print("\n[1/3] Perceive: 시스템 상태 수집 중...")
    observation = perceive()
    print(observation)

    # Step 2: LLM 판단
    print("\n[2/3] Decide: LLM에게 분석 요청 중...")
    decision = decide(observation)

    # Step 3: 행동
    print("\n[3/3] Act: 결정 실행")
    act(decision)

if __name__ == "__main__":
    main()
PYEOF

# 에이전트 실행
python3 ~/lab/week01/simple_agent.py
```

### 4.3 멀티턴 대화 에이전트

```bash
cat > ~/lab/week01/multi_turn_agent.py << 'PYEOF'
"""
Week 01 실습: 멀티턴 대화 보안 에이전트
이전 대화 기록을 유지하면서 여러 번 상호작용한다.
"""
import requests

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

# 대화 기록을 리스트로 유지 (메모리 역할)
conversation_history = [
    {
        "role": "system",
        "content": "너는 보안 분석가 AI이다. 사용자가 보안 관련 질문을 하면 전문적으로 답변한다. 이전 대화 맥락을 기억한다."
    }
]

def chat_with_memory(user_input: str) -> str:
    """대화 기록을 유지하면서 LLM 호출"""
    # 사용자 메시지를 기록에 추가
    conversation_history.append({"role": "user", "content": user_input})

    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": conversation_history,
        "temperature": 0.3,
    }, timeout=120)

    # assistant 응답을 기록에 추가
    answer = resp.json()["choices"][0]["message"]["content"]
    conversation_history.append({"role": "assistant", "content": answer})
    return answer

if __name__ == "__main__":
    # 3번의 연속 대화 시뮬레이션
    questions = [
        "XSS 공격이 뭐야?",
        "방금 설명한 공격을 방어하려면 어떻게 해야 해?",
        "그 방어 방법을 nftables로 구현할 수 있어?"
    ]
    for i, q in enumerate(questions, 1):
        print(f"\n--- 대화 {i} ---")
        print(f"사용자: {q}")
        # LLM 호출 (이전 대화 맥락 포함)
        answer = chat_with_memory(q)
        print(f"에이전트: {answer[:300]}...")  # 긴 응답은 300자만 출력

    # 대화 기록 수 확인
    print(f"\n총 대화 턴 수: {len(conversation_history) - 1}")
PYEOF

# 멀티턴 에이전트 실행
python3 ~/lab/week01/multi_turn_agent.py
```

---

## Part 5: 보안 에이전트 프로토타입 (30분) — 실습

### 5.1 OpsClaw API로 에이전트 결과 기록

실습 에이전트를 OpsClaw과 연동하여 작업 기록을 남긴다.

```bash
# OpsClaw에 프로젝트 생성 (에이전트 실습 기록용)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "week01-first-agent",
    "request_text": "Week01 실습: 첫 번째 AI 보안 에이전트 테스트",
    "master_mode": "external"
  }' | python3 -m json.tool

# 응답에서 project_id를 확인하고 변수에 저장
# (실제 출력된 ID로 교체)
export PROJECT_ID="<응답에서 받은 id>"
```

### 5.2 에이전트로 서버 상태 점검 후 기록

```bash
cat > ~/lab/week01/agent_with_opsclaw.py << 'PYEOF'
"""
Week 01 실습: OpsClaw 연동 보안 에이전트
에이전트 결과를 OpsClaw API에 기록한다.
"""
import subprocess
import requests
import json
import os

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "llama3.1:8b"
OPSCLAW_URL = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def llm_analyze(system_info: str) -> str:
    """시스템 정보를 LLM으로 분석"""
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "보안 관점에서 서버 상태를 분석하라. 위험 요소를 지적하라."},
            {"role": "user", "content": system_info}
        ],
        "temperature": 0.2
    }, timeout=120)
    return resp.json()["choices"][0]["message"]["content"]

def collect_info() -> str:
    """로컬 서버 정보 수집"""
    checks = [
        ("hostname", "hostname"),
        ("os_version", "cat /etc/os-release | head -3"),
        ("open_ports", "ss -tlnp | head -20"),
        ("users_logged_in", "who"),
        ("last_logins", "last -5"),
    ]
    info_lines = []
    for label, cmd in checks:
        # 각 명령 실행 결과를 수집
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        info_lines.append(f"[{label}]\n{result.stdout.strip()}\n")
    return "\n".join(info_lines)

def main():
    # 1. Perceive
    print("[Perceive] 서버 정보 수집 중...")
    info = collect_info()
    print(info[:500])

    # 2. Decide (LLM)
    print("[Decide] LLM 분석 중...")
    analysis = llm_analyze(info)
    print(f"분석 결과: {analysis[:400]}")

    # 3. Act (OpsClaw에 기록)
    print("[Act] OpsClaw에 결과 기록...")
    project_id = os.environ.get("PROJECT_ID")
    if project_id:
        # 완료 보고서 작성
        requests.post(
            f"{OPSCLAW_URL}/projects/{project_id}/completion-report",
            headers=HEADERS,
            json={
                "summary": "Week01 에이전트 실습 완료",
                "outcome": "success",
                "work_details": [
                    f"서버 정보 수집 완료",
                    f"LLM 분석 결과: {analysis[:200]}"
                ]
            }
        )
        print("OpsClaw 기록 완료!")
    else:
        print("PROJECT_ID 환경변수를 설정해주세요.")

if __name__ == "__main__":
    main()
PYEOF

# PROJECT_ID 설정 후 실행 (위에서 생성한 프로젝트 ID 사용)
# export PROJECT_ID="실제ID"
# python3 ~/lab/week01/agent_with_opsclaw.py
```

### 5.3 결과 확인

```bash
# OpsClaw에서 프로젝트 상태 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/${PROJECT_ID} | python3 -m json.tool

# evidence 요약 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/${PROJECT_ID}/evidence/summary | python3 -m json.tool
```

---

## Part 6: 퀴즈 + 과제 (20분)

### 복습 퀴즈

**Q1. AI 에이전트의 핵심 순환 구조를 올바르게 나열한 것은?**
- (A) Plan → Execute → Report
- (B) Input → Process → Output
- **(C) Perceive → Decide → Act** ✅
- (D) Scan → Detect → Block

**Q2. ReAct 패턴의 특징으로 올바른 것은?**
- (A) 전체 계획을 먼저 세운 뒤 일괄 실행한다
- **(B) 추론(Thought)과 행동(Action)을 번갈아 수행한다** ✅
- (C) 규칙 기반으로 자동화된 대응을 수행한다
- (D) 다수의 에이전트가 투표로 결정한다

**Q3. LLM 에이전트가 전통적 스크립트 자동화 대비 갖는 장점이 아닌 것은?**
- (A) 비정형 텍스트를 이해할 수 있다
- (B) 프롬프트 변경만으로 새 시나리오에 대응할 수 있다
- (C) 추론 과정을 자연어로 설명할 수 있다
- **(D) 항상 100% 정확한 판단을 보장한다** ✅

**Q4. temperature 매개변수에 대한 설명으로 올바른 것은?**
- **(A) 값이 낮을수록 결정적(deterministic)이고 일관된 응답을 생성한다** ✅
- (B) 값이 높을수록 정확한 응답을 생성한다
- (C) 0으로 설정하면 LLM이 응답을 거부한다
- (D) 보안 분야에서는 항상 1.0을 사용한다

**Q5. AI 에이전트의 핵심 구성요소가 아닌 것은?**
- (A) 모델(Brain)
- (B) 도구(Tools)
- (C) 메모리(Memory)
- **(D) 데이터베이스(Database)** ✅

### 과제

**[과제 1] 나만의 보안 질의 에이전트 만들기**

1. `simple_agent.py`를 수정하여 다음 기능을 추가한다:
   - `perceive()` 함수에 네트워크 상태 점검 추가 (`ss -tlnp`, `ip route`)
   - `decide()` 함수의 system 프롬프트를 보안 관점에 맞게 개선
   - 결과를 파일(`~/lab/week01/report.json`)에 JSON으로 저장하는 `act()` 구현

2. 에이전트를 3번 연속 실행하여 temperature=0과 temperature=0.8의 결과 차이를 비교하라.

3. 결과 보고서를 `~/lab/week01/homework.md`에 작성한다.

**제출물:** `homework.md` + 수정된 `simple_agent.py`

---

> **다음 주 예고:** Week 02에서는 LLM API의 상세 구조와 Tool Calling(함수 호출)을 학습한다. Python으로 Ollama를 호출하고, LLM이 외부 도구를 직접 선택·실행하는 메커니즘을 구현한다.
