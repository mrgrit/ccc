# Week 09: Bastion (1) - 기본

## 학습 목표
- Bastion의 프로젝트 생명주기를 이해한다
- dispatch와 execute-plan의 차이를 구분하고 적절히 사용한다
- 증거(evidence) 시스템과 PoW 체인을 이해한다
- Bastion를 활용한 보안 점검 자동화를 실습한다

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

## 1. Bastion 아키텍처 한눈에

> **왜 배우는가.** 직접 SSH 로 명령을 치면 "누가, 언제, 어디서, 무엇을" 이 남지 않는다.
> Bastion을 경유하면 자연어 지시 한 번이 자산 라우팅 → 명령 위임 → 결과 수집 → 증거 기록까지
> 자동 처리된다. 감사·재현·협업의 기반이다.
>
> **이걸 하면 무엇을 알 수 있는가:**
> - Bastion이 외부에 노출하는 2개의 I/F (`/ask`, `/chat`)
> - Skill / Playbook / Assets / Evidence 개념과 조회 방법
> - 3계층(ccc-api · Bastion · SubAgent) 역할 분담

```
 사용자 ──(자연어)──> Bastion (manager :8003) ──(위임)──> SubAgent (각 자산 :8002)
                        │  ├── /ask, /chat        (외부 I/F)
                        │  ├── /skills,/playbooks (내부 도구 인벤토리)
                        │  ├── /assets            (자산 인벤토리)
                        │  └── /evidence          (감사 로그)
                        └── Ollama(:11434) 로 LLM 호출
```

ccc-api(`localhost:9100`)는 학생·랩 운영을 담당하며 Bastion과는 다른 시스템이다.

---

## 2. 외부 I/F: `/ask`, `/chat`

Bastion은 워크플로 상태머신(plan/execute/dispatch 등)을 외부에 노출하지 않는다.
사용자는 "무엇을 원하는지"만 말하고, 계획·실행·증거화는 Bastion 내부가 담당한다.

### 2.1 `/ask` — 단일 자연어 질의

```bash
# 동기 단일 응답 {"answer": "..."}
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 hostname과 uptime을 알려줘"}'
```

**무엇이 일어나는가:** Bastion이
(1) 자연어에서 의도 분류 → "자산 정보 조회"
(2) `/assets` 에서 `web → 10.20.30.80` 확인
(3) 적절한 Skill(예: `system.status`) 선택
(4) web SubAgent(:8002)에 명령 위임
(5) 결과를 요약해 `answer` 로 반환
(6) `/evidence` 에 {asset, command, exit, stdout, ts} 기록

### 2.2 `/chat` — 대화형 NDJSON 스트림

긴 작업·단계적 대화는 `/chat` 이 낫다. 한 줄 = 한 이벤트의 NDJSON 스트림이다.

```bash
# -N: 버퍼링 해제, 스트림 그대로 출력
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "web의 최근 로그인 이력을 점검하고, 의심 IP가 있으면 MITRE ATT&CK로 매핑해줘"}'
```

이벤트 종류(예):
- `{"type":"think", ...}` — 추론 중간
- `{"type":"tool", "skill":"system.status", ...}` — Skill 호출
- `{"type":"evidence", ...}` — 증거 기록
- `{"type":"final", "answer": "..."}` — 최종 답변

---

## 3. 내부 인벤토리: Skills / Playbooks / Assets

### 3.1 Skill 목록

Skill은 **결정론적 도구**이다. LLM이 매번 다르게 생성하는 명령이 아니라,
파라미터만 바뀌는 재현 가능한 단위이다.

```bash
curl -s http://10.20.30.200:8003/skills | python3 -m json.tool | head -40
```

응답 예 (발췌):
```json
{
  "skills": [
    {"name": "system.status",     "risk": "low",    "params": ["asset"]},
    {"name": "network.scan_tcp",  "risk": "medium", "params": ["asset","port"]},
    {"name": "fw.block_ip",       "risk": "high",   "params": ["asset","ip"]},
    {"name": "suricata.reload",   "risk": "medium", "params": ["asset"]}
  ]
}
```

`risk` 는 게이트 기준이다. `high`/`critical` 은 사용자 확인이 붙어야 실제 실행된다.

### 3.2 Playbook 목록

Playbook은 **Skill의 순서화된 묶음** — 표준 작업 지침서(SOP)이다.

```bash
curl -s http://10.20.30.200:8003/playbooks | python3 -m json.tool | head -40
```

응답 예:
```json
{
  "playbooks": [
    {"name": "baseline.web",  "steps": ["system.status","network.scan_tcp","http.headers"]},
    {"name": "ir.block_bruteforce", "steps": ["log.fetch_recent","fw.block_ip","suricata.reload"]}
  ]
}
```

### 3.3 Assets — 자산 인벤토리

자연어 지시에서 자산 이름만 말해도 Bastion이 IP로 변환하는 이유.

```bash
curl -s http://10.20.30.200:8003/assets | python3 -m json.tool
```

예:
```json
{
  "assets": [
    {"name":"secu","ip":"10.20.30.1","role":"firewall/ips","subagent":"http://10.20.30.1:8002"},
    {"name":"web","ip":"10.20.30.80","role":"webapp","subagent":"http://10.20.30.80:8002"},
    {"name":"siem","ip":"10.20.30.100","role":"siem","subagent":"http://10.20.30.100:8002"}
  ]
}
```

---

## 4. 감사: `/evidence`

`/ask`·`/chat` 호출로 발생한 모든 실행은 `/evidence` 에 남는다.
감사·사고 조사·리플레이의 근거이다.

```bash
# 최근 20건
curl -s "http://10.20.30.200:8003/evidence?limit=20" | python3 -m json.tool

# 특정 자산의 증거
curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=10" | python3 -m json.tool
```

각 entry 필드 (예):
```json
{
  "ts": "2026-04-23T10:05:11Z",
  "asset": "web",
  "skill": "system.status",
  "command": "hostname && uptime",
  "exit_code": 0,
  "stdout_head": "web\n 10:05:11 up 3 days...",
  "request_id": "req_...",
  "user": "ccc"
}
```

**왜 이게 중요한가:** 동일한 자연어 지시라도 Bastion 내부에서 어떤 Skill이 선택되고,
어떤 명령으로 번역됐는지가 남아야 사후 감사가 가능하다. "AI가 했어요" 는 책임 소재가 된다.

---

## 5. Risk Level과 승인 게이트

Skill/Playbook 메타데이터에는 risk 가 명시되어 있다.

| 수준 | 설명 | Bastion 동작 |
|------|------|--------------|
| low | 읽기 전용 | 즉시 실행 |
| medium | 설정 변경 가능 | 즉시 실행, 증거 강조 |
| high | 서비스 영향 | `/chat` 에서 사용자 승인 이벤트 요구 |
| critical | 파괴적 가능성 | 기본 dry-run, 명시적 승인 필요 |

`/ask` 는 동기 단발이므로 high/critical 요청이 오면 "승인 필요" 응답을 돌려주고 실행하지 않는다.
대화형 `/chat` 에서 승인 확인 이벤트를 수신해야 실제 실행된다.

---

## 6. 실습: 자연어 지시로 엔드투엔드 흐름 체험

### 실습 1: 인프라 확인 → 단일 자연어 지시 → 증거 조회

```bash
# (1) 3계층 헬스체크
curl -s http://localhost:9100/health -H "X-API-Key: ccc-api-key-2026" | python3 -m json.tool
curl -s http://10.20.30.200:8003/health | python3 -m json.tool
curl -s http://10.20.30.80:8002/health  | python3 -m json.tool

# (2) Bastion에 등록된 Skill/Playbook/Asset 한 번 훑기
curl -s http://10.20.30.200:8003/skills    | python3 -m json.tool | head -20
curl -s http://10.20.30.200:8003/playbooks | python3 -m json.tool | head -20
curl -s http://10.20.30.200:8003/assets    | python3 -m json.tool

# (3) 자연어 지시 한 번으로 web 점검
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "web 자산의 호스트네임·커널·열린 포트·최근 로그인 5건을 요약해줘"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer',d))"

# (4) 방금 어떤 명령들이 실제 실행됐는지 증거로 확인
curl -s "http://10.20.30.200:8003/evidence?asset=web&limit=10" | python3 -m json.tool
```

### 실습 2: 다중 자산 병렬 점검

```bash
# 한 번의 요청으로 secu/web/siem 모두 점검
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "secu/web/siem 세 자산의 상태를 병렬로 점검해줘. 각 자산의 hostname·uptime·listening ports를 표로 정리해줘"}'
```

Bastion은 자산 3개에 대한 명령 위임을 내부에서 병렬화한다. 사용자는 parallelism을 말하지 않는다.

### 실습 3: 대화형 심화 — `/chat`

```bash
# 실습 2에서 이상치가 보이면 /chat 으로 파고든다
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "방금 점검 결과 중 비정상 포트를 식별하고, MITRE ATT&CK T 번호로 매핑해줘"}'
```

스트림이 끝나면 `final` 이벤트의 `answer` 가 요약이다.

### 실습 4: 고위험 Skill 승인 흐름 관찰

```bash
# fw.block_ip 는 high 위험 — /ask 로는 실행되지 않고 승인 요구만 돌아와야 한다
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "secu에서 203.0.113.50 IP를 즉시 차단해줘"}'

# 올바른 Bastion은 {"answer": "승인 필요: risk=high, skill=fw.block_ip ..."} 와 유사한 응답을 준다.
# 실제 적용은 /chat 승인 이벤트로만 진행한다.
```

---

## 7. 핵심 정리

1. Bastion이 외부에 제공하는 I/F는 `/ask`·`/chat` 2개뿐이다. 상태머신 엔드포인트(plan/execute 등)는 없다.
2. 자연어 지시 → 자산 라우팅 → Skill/Playbook 선택 → SubAgent 위임 → 증거 기록이 내부에서 일어난다.
3. `/skills`, `/playbooks`, `/assets` 로 Bastion이 아는 것을 조회할 수 있다.
4. 모든 실행은 `/evidence` 에 남아야 감사·재현이 가능하다.
5. 고위험 Skill은 승인 게이트를 거친다. `/ask` 는 동기 단발이므로 승인 요구 응답만 돌려준다.

---

## 다음 주 예고
- Week 10: Bastion (2) — Playbook·Skill의 재현성과 RL 연동

---

---

## 심화: AI/LLM 보안 활용 보충

### Ollama API 상세 가이드

#### 기본 호출 구조

```bash
# Ollama는 OpenAI 호환 API를 제공한다 (포트 11434)
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
POST /ask          → 단일 자연어 질의, 동기 응답 {"answer": "..."}
POST /chat         → 대화형 NDJSON 스트림
GET  /evidence     → 과거 실행 증거 (자산·명령·exit·시각)
GET  /skills       → 등록된 Skill(결정론 도구) 목록
GET  /playbooks    → 등록된 Playbook(Skill 시나리오) 목록
GET  /assets       → 자산 인벤토리 (이름↔IP↔역할)
POST /onboard      → 신규 자산 온보딩
GET  /health       → 헬스체크

Bastion(:8003)은 내부망 접근 가정 — API 키 불필요.
ccc-api(:9100)은 학생/랩 운영용 별도 시스템 — `X-API-Key` 필요.
```

---

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://localhost:8003`

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

