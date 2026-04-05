# Week 04: LLM 기반 로그 분석

## 학습 목표
- Wazuh SIEM 알림의 구조를 이해한다
- LLM을 활용하여 보안 로그를 자동 분석할 수 있다
- 분석 결과를 구조화된 인시던트 보고서로 변환할 수 있다
- 대량 알림에서 중요 이벤트를 우선순위로 분류할 수 있다

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

# Week 04: LLM 기반 로그 분석

## 학습 목표
- Wazuh SIEM 알림의 구조를 이해한다
- LLM을 활용하여 보안 로그를 자동 분석할 수 있다
- 분석 결과를 구조화된 인시던트 보고서로 변환할 수 있다
- 대량 알림에서 중요 이벤트를 우선순위로 분류할 수 있다

---

## 1. 보안 로그 분석의 과제

SOC(Security Operations Center)에서 분석가는 하루 수천~수만 건의 알림을 처리한다.
대부분은 오탐(False Positive)이지만, 소수의 진짜 위협을 놓치면 사고로 이어진다.

### LLM이 도울 수 있는 영역

| 작업 | 수동 분석 | LLM 보조 |
|------|----------|---------|
| 알림 분류 | 1건당 5분 | 1건당 10초 |
| 패턴 인식 | 분석가 경험 의존 | 다양한 패턴 인식 |
| 보고서 작성 | 30분~1시간 | 2~3분 |
| 맥락 파악 | 여러 도구 참조 | 프롬프트로 맥락 제공 |

---

## 2. Wazuh 알림 구조

> **이 실습을 왜 하는가?**
> "LLM 기반 로그 분석" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> AI/LLM 보안 활용 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 알림 JSON 구조

```json
{
  "timestamp": "2026-03-27T10:30:00.000+0900",
  "rule": {
    "id": "5710",
    "level": 10,
    "description": "sshd: Attempt to login using a denied user.",
    "groups": ["syslog", "sshd", "authentication_failed"]
  },
  "agent": {
    "id": "002",
    "name": "web",
    "ip": "10.20.30.80"
  },
  "data": {
    "srcip": "203.0.113.50",
    "srcport": "54321",
    "dstuser": "root"
  },
  "full_log": "Mar 27 10:30:00 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2"
}
```

### 2.2 Wazuh Rule Level

| Level | 의미 | 예시 |
|-------|------|------|
| 0-3 | 정보 | 성공 로그인 |
| 4-7 | 경고 | 실패한 인증 |
| 8-11 | 높은 경고 | 반복 실패, 정책 위반 |
| 12-15 | 심각 | 공격 탐지, 무결성 위반 |

---

## 3. LLM으로 알림 분석

### 3.1 단일 알림 분석

> **실습 목적**: RAG(검색 증강 생성)로 LLM에게 보안 지식(CVE 데이터, 과거 인시던트)을 제공하여 정확도를 높이기 위해 수행한다
>
> **배우는 것**: 벡터 검색으로 관련 문서를 찾아 프롬프트에 포함시키면 LLM의 환각(hallucination)이 줄어드는 원리를 이해한다
>
> **결과 해석**: RAG 적용 전후 응답을 비교하여, 구체적 CVE 번호나 대응 절차가 포함되었는지로 품질 향상을 판단한다
>
> **실전 활용**: 조직 내부 보안 정책/SOP를 RAG로 연결하여 AI가 조직 맞춤형 보안 답변을 제공하도록 구축하는 데 활용한다

Wazuh 알림 JSON을 변수에 저장한 뒤 LLM에 전달하여 위협수준, MITRE ATT&CK 매핑, 대응 조치를 자동 분석시킨다.

```bash
# Wazuh 알림 JSON을 변수에 저장 (쉘 변수 → curl에서 치환)
ALERT='{
  "rule": {"id": "5710", "level": 10, "description": "sshd: Attempt to login using a denied user."},
  "agent": {"name": "web", "ip": "10.20.30.80"},
  "data": {"srcip": "203.0.113.50", "dstuser": "root"},
  "full_log": "Mar 27 10:30:00 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2"
}'

# LLM에 알림 전달 → 위협수준/MITRE ATT&CK/대응 형식으로 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC Tier-2 분석가입니다. Wazuh 알림을 분석하고 다음 형식으로 응답하세요:\\n- 요약: (한 줄)\\n- 위협수준: CRITICAL/HIGH/MEDIUM/LOW\\n- MITRE ATT&CK: (해당 기법)\\n- 대응: (즉시 수행할 조치)\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 알림을 분석하세요:\\n$ALERT\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.2 복수 알림 상관 분석

시간순으로 나열된 여러 알림을 LLM에게 전달하여 공격 킬체인(정찰 -> 침투 -> 거점 확보)을 자동 추론시킨다.

```bash
# 5개 알림을 시간순 배열로 구성 (SSH 실패 → 성공 → 계정 생성)
ALERTS='[
  {"time": "10:30:00", "rule": "5710", "src": "203.0.113.50", "msg": "SSH 로그인 실패 (root)"},
  {"time": "10:30:05", "rule": "5710", "src": "203.0.113.50", "msg": "SSH 로그인 실패 (admin)"},
  {"time": "10:31:00", "rule": "5715", "src": "203.0.113.50", "msg": "SSH 브루트포스 탐지"},
  {"time": "10:35:00", "rule": "5501", "src": "203.0.113.50", "msg": "SSH 로그인 성공 (deploy)"},
  {"time": "10:36:00", "rule": "550",  "src": "10.20.30.80",  "msg": "사용자 추가: hacker"}
]'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC 분석가입니다. 여러 알림을 시간순으로 상관 분석하여 공격 시나리오를 추론하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 알림들을 상관 분석하세요. 공격 킬체인을 추론하세요:\\n$ALERTS\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. 알림 우선순위 분류

### 4.1 배치 분류 프롬프트

대량의 알림을 한 번에 LLM에게 전달하여 우선순위(P1~P4)를 일괄 분류시킨다. SOC에서 알림 피로도를 줄이는 핵심 기법이다.

```bash
# 배치 알림 분류: 여러 알림을 한 번에 우선순위 분류
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석가입니다. 알림을 우선순위별로 분류하세요.\n분류: CRITICAL(즉시 대응), HIGH(1시간 내), MEDIUM(24시간 내), LOW(정기 검토)\n\nJSON 배열로 응답: [{\"id\": N, \"priority\": \"...\", \"reason\": \"...\"}]"},
      {"role": "user", "content": "분류할 알림 목록:\n1. SSH root 로그인 성공 (외부 IP)\n2. 파일 무결성 변경 (/etc/passwd)\n3. 디스크 사용량 90%\n4. nginx 404 에러 증가\n5. sudo 권한 실행 (웹 서버에서 wget)"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 자동화 스크립트

### 5.1 Python으로 Wazuh 알림 자동 분석

```python
#!/usr/bin/env python3
"""wazuh_llm_analyzer.py - Wazuh 알림을 LLM으로 분석"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "gemma3:12b"

SYSTEM_PROMPT = """SOC Tier-2 분석가입니다. Wazuh 알림을 분석하고
정확히 다음 JSON 형식으로만 응답하세요:
{"severity": "CRITICAL|HIGH|MEDIUM|LOW", "summary": "한줄요약",
 "attack_type": "공격유형", "action": "대응조치"}"""

def analyze_alert(alert_json):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"알림: {json.dumps(alert_json, ensure_ascii=False)}"}
        ],
        "temperature": 0
    })
    return response.json()["choices"][0]["message"]["content"]

# 사용 예시
sample_alert = {
    "rule": {"id": "5710", "level": 10,
             "description": "sshd: Attempt to login using a denied user."},
    "agent": {"name": "web"},
    "data": {"srcip": "203.0.113.50", "dstuser": "root"}
}

result = analyze_alert(sample_alert)
print(result)
```

---

## 6. 실습

### 실습 1: 실제 Wazuh 알림 분석

```bash
# siem 서버에서 최근 알림 가져오기 (OpsClaw 활용)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "wazuh-log-analysis",
    "request_text": "Wazuh 최근 알림 수집 및 분석",
    "master_mode": "external"
  }'

# 프로젝트 ID 확인 후 dispatch로 알림 수집
# curl -X POST http://localhost:8000/projects/{id}/dispatch ...
```

### 실습 2: 공격 시나리오별 프롬프트 설계

```bash
# 시나리오: 웹 서버에서 의심스러운 활동 탐지
SCENARIO="다음은 웹 서버(10.20.30.80)에서 30분간 수집된 로그입니다:
10:00 - 정상 웹 트래픽
10:05 - /admin 페이지 접근 시도 (403)
10:06 - SQL Injection 시도 (?id=1' OR '1'='1)
10:08 - /admin 접근 성공 (200)
10:10 - 파일 업로드 (webshell.php)
10:15 - webshell.php에서 시스템 명령 실행
10:20 - /etc/passwd 읽기 시도
10:25 - 리버스 셸 연결 시도"

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"인시던트 대응 전문가입니다. 공격 킬체인을 분석하고 각 단계의 MITRE ATT&CK 기법을 매핑하세요.\"},
      {\"role\": \"user\", \"content\": \"$SCENARIO\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 분석 결과를 인시던트 보고서로 변환

```bash
# 이전 분석 결과를 CISO용 보고서로 변환
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "CISO에게 보고할 인시던트 보고서를 작성합니다. 비기술적 경영진도 이해할 수 있되, 기술 세부사항도 포함하세요."},
      {"role": "user", "content": "다음 분석 결과를 인시던트 보고서로 변환하세요:\n- 공격: SQL Injection → 웹셸 업로드 → 시스템 침입\n- 대상: web 서버 (10.20.30.80)\n- 공격자 IP: 203.0.113.50\n- 시간: 2026-03-27 10:00~10:25\n- 피해: 관리자 페이지 접근, 시스템 명령 실행 시도\n\n보고서 형식: 1.개요 2.타임라인 3.영향분석 4.대응현황 5.재발방지"}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. LLM 로그 분석의 한계

1. **환각**: 존재하지 않는 위협을 만들어낼 수 있다
2. **최신 위협**: 학습 데이터 이후의 새로운 공격 패턴을 모를 수 있다
3. **정밀도**: 자동 분류의 정확도를 지속적으로 검증해야 한다
4. **민감 데이터**: 실제 IP, 비밀번호 등을 외부 LLM에 전송하면 안 된다

해결 방법: 로컬 LLM(Ollama) 사용 + 사람 검증 + 지속적 피드백

---

## 핵심 정리

1. LLM은 대량의 보안 알림을 빠르게 분류하고 분석하는 도구이다
2. 시간순 상관 분석으로 공격 킬체인을 추론할 수 있다
3. 구조화된 프롬프트로 일관된 분석 결과를 얻는다
4. 자동화 스크립트로 Wazuh 알림을 실시간 분석할 수 있다
5. LLM 분석 결과는 반드시 사람이 검증해야 한다

---

## 다음 주 예고
- Week 05: 탐지 룰 자동 생성 - 공격 패턴에서 SIGMA/Wazuh 룰 자동 생성

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
