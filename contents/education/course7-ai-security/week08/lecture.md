# Week 08: 중간고사 — LLM 보안 도구 구축

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (도구 구축 + 분석 보고서) |
| 시간 | 3시간 (180분) |
| 배점 | 100점 |
| 환경 | Ollama (192.168.0.105:11434), OpsClaw (localhost:8000) |
| 제출 | 스크립트 파일 + 실행 결과 캡처 + 분석 보고서 |
| 참고 | 오픈 북 (강의 자료, 인터넷 검색 가능. 타인과 공유 금지) |

## 시험 범위

| 주차 | 주제 | 출제 범위 |
|------|------|---------|
| Week 02 | LLM 기초, Ollama API | Ollama API 호출, 모델 선택, 파라미터 설정 |
| Week 03 | 프롬프트 엔지니어링 | system/user 메시지 설계, few-shot, 출력 형식 제어 |
| Week 04 | LLM 기반 로그 분석 | 로그 파싱, 이상 탐지, 상관 분석 |
| Week 05 | 탐지 룰 자동 생성 | SIGMA 룰 작성, Wazuh/Suricata 시그니처 |
| Week 06 | 취약점 분석 | CVE 분석, CVSS 점수 산출, 패치 권고 |
| Week 07 | AI 에이전트 아키텍처 | 에이전트 루프, 도구 호출, 계획-실행 패턴 |

---

## 시험 시간 배분 (권장)

| 시간 | 작업 | 배점 |
|------|------|------|
| 0:00-0:15 | 문제 읽기 + 환경 확인 | — |
| 0:15-1:00 | 문제 1: 보안 로그 분석 도구 | 40점 |
| 1:00-1:10 | 휴식 | — |
| 1:10-1:50 | 문제 2: 탐지 룰 생성 + 검증 | 30점 |
| 1:50-2:30 | 문제 3: OpsClaw 오케스트레이션 | 30점 |
| 2:30-3:00 | 보고서 정리 + 제출 | — |

---

## 용어 해설 (시험에서 사용되는 주요 용어)

> 시험 중 헷갈리면 이 표를 참고하라.

| 용어 | 설명 | 예시 |
|------|------|------|
| **Ollama API** | 로컬 LLM을 HTTP API로 호출하는 인터페이스 | `curl http://192.168.0.105:11434/v1/chat/completions` |
| **system 메시지** | LLM에게 역할과 규칙을 부여하는 메시지 | `"role":"system","content":"보안 분석가입니다"` |
| **user 메시지** | 사용자의 실제 요청/데이터 | `"role":"user","content":"이 로그를 분석하세요"` |
| **temperature** | LLM 출력의 창의성/무작위성 조절 (0=결정론, 1=창의적) | 분석: 0~0.3, 룰 생성: 0.2~0.5 |
| **few-shot** | 예시를 함께 제공하여 출력 품질을 높이는 프롬프트 기법 | "예시: 입력X→출력Y. 이제 입력Z를 처리하세요" |
| **SIGMA 룰** | SIEM에 독립적인 범용 탐지 룰 포맷 (YAML) | `detection: selection: EventID: 4625` |
| **상관 분석** | 여러 이벤트를 연결하여 공격 시나리오를 추론하는 것 | SSH 실패 3회→성공→계정 추가 = 브루트포스→침투 |
| **킬체인** | 공격의 단계별 진행 과정 | 정찰→침투→권한상승→지속성→유출 |
| **IOC** | Indicator of Compromise, 침해 지표 | 악성 IP: 203.0.113.50 |
| **CVSS** | 취약점 심각도 점수 (0~10점) | 9.8 = Critical |
| **OpsClaw project** | 보안 작업 단위 (생성→plan→execute→evidence→report) | `POST /projects` |
| **evidence** | OpsClaw가 자동 기록하는 실행 증적 | stdout, stderr, exit_code, 타임스탬프 |
| **execute-plan** | 여러 태스크를 한 번에 실행하는 OpsClaw API | `POST /projects/{id}/execute-plan` |

---

## 사전 환경 확인 (시험 시작 전 필수)

시험 시작 전 다음을 확인하라. 하나라도 실패하면 감독관에게 보고한다.

```bash
# 1. Ollama LLM 연결 확인
curl -s http://192.168.0.105:11434/v1/models | python3 -c "
import sys,json
models = json.load(sys.stdin)['data']
print(f'사용 가능한 모델: {len(models)}개')
for m in models[:5]:
    print(f'  - {m[\"id\"]}')
"
# 기대 결과: gemma3:12b, llama3.1:8b 등 모델 목록

# 2. Ollama 응답 테스트
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[{"role":"user","content":"hello"}],"max_tokens":10}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
# 기대 결과: 짧은 응답 텍스트

# 3. OpsClaw API 연결 확인
curl -s http://localhost:8000/projects -H "X-API-Key: opsclaw-api-key-2026" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OpsClaw: 정상 (프로젝트 {len(d.get(\"projects\",[]))}개)')"
# 기대 결과: OpsClaw: 정상 (프로젝트 N개)

# 4. 원격 서버 접속 확인
for srv in "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "hostname" 2>/dev/null || echo "$srv: 접속 실패"
done
# 기대 결과: secu, web, siem 출력
```

---

# 문제 1: 보안 로그 분석 도구 (40점)

## 1.1 배경

SOC(보안관제센터) 분석가가 Wazuh SIEM에서 수집된 보안 알림을 빠르게 분류하고, 공격 시나리오를 추론하며, 즉시 대응 방안을 도출해야 한다. 이를 LLM으로 자동화하는 도구를 구축한다.

## 1.2 입력 데이터

다음 6건의 보안 알림이 시간 순서대로 발생하였다.

```json
[
  {"id":1,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:00"},
  {"id":2,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:01"},
  {"id":3,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:02"},
  {"id":4,"rule_id":"5501","level":5,"desc":"SSH login success","src":"203.0.113.50","dst":"web","time":"10:05"},
  {"id":5,"rule_id":"550","level":8,"desc":"User added: backdoor","src":"web","dst":"web","time":"10:06"},
  {"id":6,"rule_id":"510","level":12,"desc":"File integrity changed: /etc/passwd","src":"web","dst":"web","time":"10:07"}
]
```

> **데이터 해석 힌트:**
> - 알림 1~3: 같은 IP(203.0.113.50)에서 SSH 로그인 3회 연속 실패 → 브루트포스 징후
> - 알림 4: 같은 IP에서 SSH 로그인 성공 → 브루트포스 성공?
> - 알림 5: web 서버에서 "backdoor" 사용자 생성 → 백도어 계정
> - 알림 6: /etc/passwd 파일 변조 → 사용자 추가의 결과

## 1.3 요구사항

### Task A: 알림 분류 (10점)

각 알림의 위협 수준을 CRITICAL/HIGH/MEDIUM/LOW로 분류하라.

**요구 출력 형식 (JSON):**
```json
{
  "classifications": [
    {"alert_id": 1, "severity": "MEDIUM", "reason": "단일 SSH 실패는 일반적"},
    {"alert_id": 2, "severity": "..."},
    ...
  ]
}
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 6개 알림 전부 분류 | 4점 | 누락 없이 전부 |
| 심각도 적절성 | 4점 | 알림 5,6은 HIGH/CRITICAL이어야 함 |
| 근거 설명 | 2점 | reason 필드의 논리성 |

**구현 힌트:**
```bash
#!/bin/bash
OLLAMA_URL="http://192.168.0.105:11434/v1/chat/completions"
MODEL="gemma3:12b"

# 알림 데이터
ALERTS='[{"id":1,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:00"},{"id":2,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:01"},{"id":3,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:02"},{"id":4,"rule_id":"5501","level":5,"desc":"SSH login success","src":"203.0.113.50","dst":"web","time":"10:05"},{"id":5,"rule_id":"550","level":8,"desc":"User added: backdoor","src":"web","dst":"web","time":"10:06"},{"id":6,"rule_id":"510","level":12,"desc":"File integrity changed: /etc/passwd","src":"web","dst":"web","time":"10:07"}]'

echo "=== Task A: 알림 분류 ==="
curl -s $OLLAMA_URL \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"당신은 SOC 분석가입니다. 보안 알림을 CRITICAL/HIGH/MEDIUM/LOW로 분류하세요. 반드시 JSON으로만 응답하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 알림들을 분류하세요:\\n$ALERTS\\n\\n출력 형식: {\\\"classifications\\\": [{\\\"alert_id\\\": 1, \\\"severity\\\": \\\"...\\\", \\\"reason\\\": \\\"...\\\"}]}\"}
    ],
    \"temperature\": 0.1,
    \"max_tokens\": 1000
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

> **왜 temperature를 0.1로 설정하는가?**
> 분류 작업은 일관된 결과가 필요하다. temperature가 높으면 같은 알림을 매번 다르게 분류할 수 있다.
> 분석/분류: 0~0.3, 창의적 작성: 0.5~0.8

### Task B: 상관 분석 (15점)

6개 알림을 연결하여 **공격 킬체인(kill chain)**을 추론하라.

**요구 출력 형식 (JSON):**
```json
{
  "kill_chain": {
    "phase_1": {"alerts": [1,2,3], "tactic": "Credential Access", "technique": "T1110 Brute Force", "description": "..."},
    "phase_2": {"alerts": [4], "tactic": "Initial Access", "technique": "T1078 Valid Accounts", "description": "..."},
    "phase_3": {"alerts": [5,6], "tactic": "Persistence", "technique": "T1136 Create Account", "description": "..."}
  },
  "overall_assessment": "...",
  "confidence": "HIGH/MEDIUM/LOW",
  "ioc": ["203.0.113.50", "backdoor"]
}
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 킬체인 단계 식별 | 5점 | 최소 3단계로 올바르게 구분 |
| ATT&CK 매핑 | 5점 | 전술/기법 ID 정확성 |
| IOC 추출 | 3점 | 공격자 IP, 백도어 계정명 |
| 전체 평가 | 2점 | 종합 위험도 판단의 논리성 |

**프롬프트 설계 팁:**
- system 메시지에 "MITRE ATT&CK 전문가" 역할을 부여
- few-shot으로 킬체인 분석 예시를 1개 포함
- "JSON으로만 응답" 지시 (마크다운 금지)

### Task C: 대응 방안 (10점)

분석 결과를 기반으로 **즉시 수행할 대응 조치 목록**을 생성하라.

**요구 출력 형식:**
```json
{
  "immediate_actions": [
    {"priority": 1, "action": "203.0.113.50 IP 차단 (nftables)", "command": "nft add rule inet filter input ip saddr 203.0.113.50 drop", "target": "secu"},
    {"priority": 2, "action": "...", "command": "...", "target": "..."}
  ],
  "investigation_steps": ["..."],
  "long_term_recommendations": ["..."]
}
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 즉시 조치 3개 이상 | 4점 | IP 차단, 계정 비활성화, 비밀번호 변경 등 |
| 실행 가능한 명령 포함 | 3점 | 실제 실행할 수 있는 bash 명령 |
| 대상 서버 지정 | 3점 | 각 조치의 target 정확성 |

### Task D: JSON 출력 통합 (5점)

Task A~C의 결과를 하나의 JSON 보고서로 통합하라.

---

# 문제 2: 탐지 룰 생성 + 검증 (30점)

## 2.1 SIGMA 룰 생성 (15점)

다음 3가지 공격 시나리오에 대한 SIGMA 탐지 룰을 LLM으로 생성하라.

### 시나리오 A: SSH 브루트포스

> **상황:** 5분 내 동일 IP에서 10회 이상 SSH 인증 실패

**기대하는 SIGMA 룰 구조:**
```yaml
title: SSH Brute Force Detection
status: experimental
description: ...
logsource:
    product: linux
    service: sshd
detection:
    selection:
        # 탐지 조건
    condition: selection
    timeframe: 5m
    count: 10
level: high
tags:
    - attack.credential_access
    - attack.t1110
```

> **SIGMA 룰이란?** (Week 05 복습)
> - SIEM 벤더에 독립적인 범용 탐지 룰 포맷
> - YAML로 작성
> - `logsource`: 어떤 로그를 볼 것인가 (OS, 서비스)
> - `detection`: 어떤 패턴을 찾을 것인가 (조건, 시간, 횟수)
> - `level`: 심각도 (informational, low, medium, high, critical)
> - `tags`: ATT&CK 기법 매핑

### 시나리오 B: 웹 디렉토리 스캔

> **상황:** 1분 내 동일 IP에서 20개 이상 HTTP 404 응답

### 시나리오 C: 권한 상승 시도

> **상황:** 일반 사용자가 /etc/shadow 파일 접근 시도

**구현:**
> **실습 목적**: 전반기에 학습한 LLM 보안 활용 기술을 종합하여 실전 수준의 보안 분석 시스템을 구축하기 위해 수행한다
>
> **배우는 것**: 프롬프트 설계, Tool Calling, RAG를 결합한 종합 보안 분석 파이프라인의 설계와 구현 능력을 기른다
>
> **결과 해석**: 분석 정확도(F1-Score), 응답 시간, 오탐/미탐 비율로 시스템 품질을 종합 평가한다
>
> **실전 활용**: SOC 자동 분석 시스템 구축, AI 기반 인시던트 대응 자동화, 보안 운영 효율화에 활용한다

```bash
# 3개 시나리오를 하나의 스크립트로 처리
for scenario in \
  "SSH 브루트포스: 5분 내 동일 IP에서 10회 이상 SSH 인증 실패. 로그소스: linux/sshd" \
  "웹 디렉토리 스캔: 1분 내 동일 IP에서 20개 이상 HTTP 404 응답. 로그소스: apache/access" \
  "권한 상승: 일반 사용자의 /etc/shadow 접근 시도. 로그소스: linux/auditd"
do
  echo "=== SIGMA 룰 생성: $scenario ==="
  curl -s http://192.168.0.105:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"gemma3:12b\",
      \"messages\": [
        {\"role\": \"system\", \"content\": \"SIGMA 룰 전문가입니다. 유효한 SIGMA YAML만 출력하세요. 설명 없이 YAML만.\"},
        {\"role\": \"user\", \"content\": \"다음 공격을 탐지하는 SIGMA 룰을 작성하세요: $scenario\"}
      ],
      \"temperature\": 0.2,
      \"max_tokens\": 500
    }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
  echo ""
done
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| YAML 문법 정확성 | 5점 | 유효한 YAML (파싱 가능) |
| detection 조건 논리 | 5점 | timeframe, count, 필드명 정확 |
| ATT&CK 태그 매핑 | 3점 | 올바른 기법 ID |
| logsource 정확성 | 2점 | product, service 적절 |

## 2.2 룰 품질 검증 (15점)

생성된 3개의 룰을 **다른 LLM 모델** (또는 다른 프롬프트)로 교차 검증하라.

**검증 관점:**
1. **오탐 가능성 (False Positive):** 정상 행위가 탐지될 수 있는가?
2. **미탐 가능성 (False Negative):** 공격자가 쉽게 우회할 수 있는가?
3. **개선 사항:** 조건을 더 정교하게 만들 수 있는가?

```bash
# 예: gemma3:12b가 생성한 룰을 llama3.1:8b로 검증
SIGMA_RULE="(생성된 룰 내용)"
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llama3.1:8b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 룰 검증 전문가입니다. SIGMA 룰의 품질을 평가하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 SIGMA 룰을 검증하세요:\\n$SIGMA_RULE\\n\\n평가 항목: 1) 오탐 가능성 2) 미탐 가능성 3) 개선 사항\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

> **왜 다른 모델로 검증하는가?**
> 같은 모델은 자기가 생성한 룰의 문제를 잘 발견하지 못한다 (self-bias).
> 다른 모델(또는 다른 프롬프트)로 검증하면 독립적인 시각을 얻을 수 있다.
> 이는 "Red Team이 만든 것을 Blue Team이 검증"하는 원리와 동일하다.

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 3개 룰 전부 검증 | 5점 | 누락 없이 전부 |
| 오탐/미탐 분석 깊이 | 5점 | 구체적 시나리오 제시 |
| 개선 제안의 실현 가능성 | 5점 | 실제 적용 가능한 수정안 |

---

# 문제 3: OpsClaw 오케스트레이션 (30점)

## 3.1 프로젝트 생성 및 보안 점검 실행 (15점)

OpsClaw API를 사용하여 3대 서버(secu, web, siem)의 보안 상태를 자동 점검하라.

### Step 1: 프로젝트 생성

OpsClaw에 external 모드 프로젝트를 생성하여 Claude Code가 직접 오케스트레이션할 수 있도록 한다. 반환된 project ID를 변수에 저장한다.

```bash
# OpsClaw 프로젝트 생성 (master_mode=external: 외부 오케스트레이션)
# python3 파이프로 응답 JSON에서 project ID만 추출
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"midterm-security-check","request_text":"3대 서버 보안 상태 자동 점검","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"
```

### Step 2: Stage 전환

execute-plan 호출 전에 반드시 plan -> execute 순서로 Stage를 전환해야 한다. 순서를 건너뛰면 400 에러가 발생한다.

```bash
# plan → execute 단계 전환 (필수 선행 조건)
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
echo "Stage: execute 준비 완료"
```

### Step 3: 보안 점검 태스크 실행

**최소 요구:** 3개 태스크, parallel=true

3대 서버(secu/web/siem)에 대한 보안 점검 태스크를 동시에(parallel) 실행한다. 각 태스크에 대상 서버의 SubAgent URL을 지정한다.

```bash
# 3대 서버 보안 점검을 병렬 실행 (parallel=true)
# 각 task의 subagent_url: 해당 서버의 SubAgent 주소
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"secu 방화벽 점검","instruction_prompt":"nft list ruleset 2>/dev/null | head -30 || echo no-nftables","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":2,"title":"web 사용자/포트 점검","instruction_prompt":"last -5 && ss -tlnp | head -15 && sudo -l 2>/dev/null","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"title":"siem Wazuh 상태","instruction_prompt":"systemctl is-active wazuh-manager 2>/dev/null && curl -sk -u wazuh-wui:PASSWORD https://localhost:55000/security/user/authenticate 2>/dev/null | head -1 || echo wazuh-check-failed","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]} (성공:{d[\"tasks_ok\"]}, 실패:{d[\"tasks_failed\"]})')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]} → {t[\"status\"]}')
"
```

> **주의사항:**
> - `plan` → `execute` 순서를 건너뛰면 400 에러 발생
> - `X-API-Key` 헤더를 빠뜨리면 401 에러 발생
> - `subagent_url`을 대상 서버에 맞게 설정해야 해당 서버에서 실행됨

### Step 4: Evidence 확인

실행된 태스크의 결과(명령 출력, 종료 코드 등)가 evidence로 기록된다. summary 엔드포인트로 전체 결과를 조회한다.

```bash
# 프로젝트의 전체 evidence(실행 결과) 요약 조회
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### Step 5: Replay 확인

프로젝트의 작업 히스토리를 시간순으로 재현하여 각 태스크의 실행 순서, 종료 코드, PoW 보상을 확인한다.

```bash
# 프로젝트 작업 Replay: 시간순 실행 이력 + PoW 보상 확인
curl -s "http://localhost:8000/projects/$PID/replay" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'총 단계: {d[\"steps_total\"]}, 총 보상: {d[\"total_reward\"]}')
for s in d.get('timeline',[]):
    print(f'  [{s[\"task_order\"]}] {s[\"task_title\"]:25s} exit={s[\"exit_code\"]} reward={s[\"total_reward\"]}')
"
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 프로젝트 생성 성공 | 2점 | project_id 획득 |
| Stage 전환 성공 | 2점 | plan→execute |
| execute-plan 실행 (3개 이상) | 5점 | overall=success |
| parallel=true 사용 | 2점 | 병렬 실행 확인 |
| evidence/summary 조회 | 2점 | 총 건수 확인 |
| replay 조회 | 2점 | 타임라인 확인 |

## 3.2 결과 분석 보고서 (15점)

OpsClaw 실행 결과를 **LLM으로 분석**하여 보안 상태 보고서를 작성하라.

### 보고서에 포함할 내용

```
1. 점검 개요
   - 점검 일시, 대상 서버, 점검 항목
   - OpsClaw project_id, 사용한 SubAgent URL

2. 발견 사항
   - 각 서버별 주요 발견 (방화벽 룰, 열린 포트, 사용자 권한 등)
   - 정상/이상 판정 근거

3. 위험도 평가
   - CVSS 또는 자체 기준으로 위험도 산정
   - 우선순위별 정리

4. 대응 권고
   - 즉시 조치 (Critical/High)
   - 중기 조치 (Medium)
   - 장기 개선 (Low)

5. 증적 정보
   - evidence/summary 캡처
   - replay 타임라인
```

**구현:**
```bash
# 실행 결과를 변수에 저장
EVIDENCE=$(curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026")

# LLM으로 분석 보고서 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 컨설턴트입니다. 보안 점검 결과를 분석하여 전문적인 보고서를 작성하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 보안 점검 결과를 분석하세요:\\n$EVIDENCE\\n\\n보고서에 포함: 1)점검개요 2)발견사항 3)위험도평가 4)대응권고\"}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 2000
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 점검 개요 완성도 | 3점 | 일시, 대상, 항목 명시 |
| 발견 사항 정확성 | 4점 | 실제 결과와 일치하는 분석 |
| 위험도 평가 논리 | 4점 | 등급 산정 근거의 타당성 |
| 대응 권고 실현가능성 | 4점 | 구체적이고 실행 가능한 조치 |

---

## 종합 채점표

| 문제 | 항목 | 배점 |
|------|------|------|
| **1** | 알림 분류 (Task A) | 10 |
| **1** | 상관 분석 + 킬체인 (Task B) | 15 |
| **1** | 대응 방안 (Task C) | 10 |
| **1** | JSON 통합 출력 (Task D) | 5 |
| **2** | SIGMA 룰 3개 생성 | 15 |
| **2** | 룰 교차 검증 | 15 |
| **3** | OpsClaw 프로젝트 실행 | 15 |
| **3** | LLM 분석 보고서 | 15 |
| | **합계** | **100** |

---

## 핵심 팁 (시험 전 반드시 확인)

### 프롬프트 작성 팁

| 상황 | 권장 temperature | system 메시지 핵심 |
|------|----------------|------------------|
| 알림 분류 | 0~0.2 | "SOC 분석가. 정확한 분류만 출력." |
| 킬체인 분석 | 0.2~0.3 | "ATT&CK 전문가. 킬체인을 JSON으로." |
| 대응 방안 | 0.3~0.5 | "보안 대응 전문가. 실행 가능한 명령 포함." |
| SIGMA 룰 | 0.1~0.3 | "SIGMA 전문가. YAML만 출력." |
| 보고서 | 0.3~0.5 | "보안 컨설턴트. 전문적 보고서 작성." |

### 자주 하는 실수

| 실수 | 결과 | 해결 |
|------|------|------|
| JSON에서 따옴표 이스케이핑 누락 | curl 오류 | `\"` 사용 또는 파일로 분리 |
| OpsClaw plan/execute 순서 건너뜀 | 400 에러 | 반드시 plan → execute 순서 |
| X-API-Key 헤더 누락 | 401 에러 | 모든 API 호출에 포함 |
| temperature가 너무 높음 | 매번 다른 결과 | 분석 업무는 0~0.3 |
| max_tokens 미설정 | 응답 잘림 | 충분한 값 설정 (1000~2000) |
| LLM 출력을 검증 없이 제출 | 부정확한 결과 | 반드시 사람이 확인 |

### 모델 선택 가이드

| 모델 | 크기 | 속도 | 품질 | 권장 용도 |
|------|------|------|------|---------|
| gemma3:12b | 12B | 빠름 (~5s) | 양호 | 분류, 룰 생성, 빠른 분석 |
| llama3.1:8b | 8B | 매우 빠름 (~3s) | 보통 | 검증, 간단한 분석 |
| qwen3:8b | 8B | 빠름 (~5s) | 보통 | 교차 검증용 |

---

## 제출 양식

```
제출 파일:
1. midterm_task1.sh    — 문제 1 스크립트
2. midterm_task2.sh    — 문제 2 스크립트
3. midterm_task3.sh    — 문제 3 스크립트
4. midterm_report.md   — 분석 보고서
5. screenshots/        — 실행 결과 캡처 (선택)

파일 상단에 반드시 포함:
# 학번:
# 이름:
# 제출 일시:
# OpsClaw Project ID: prj_xxxxxxxx
```

---

## 검증 체크리스트

- [ ] Ollama API 연결 확인
- [ ] OpsClaw API 연결 확인
- [ ] 문제 1: 6개 알림 전부 분류 완료
- [ ] 문제 1: 킬체인 3단계 이상 식별
- [ ] 문제 1: 대응 조치 3개 이상 (실행 가능 명령 포함)
- [ ] 문제 1: JSON 통합 출력 생성
- [ ] 문제 2: SIGMA 룰 3개 생성 (YAML 유효)
- [ ] 문제 2: 3개 룰 교차 검증 완료
- [ ] 문제 3: OpsClaw 프로젝트 생성 + plan + execute
- [ ] 문제 3: execute-plan 3개 이상 태스크 (parallel=true)
- [ ] 문제 3: evidence/summary + replay 결과 캡처
- [ ] 문제 3: LLM 분석 보고서 작성
- [ ] 모든 스크립트 파일 상단에 학번/이름 기재

---

## 다음 주 예고
**Week 09: OpsClaw (1) — 기본**
- project, dispatch, execute-plan 실전 활용
- Playbook 생성과 실행
- evidence, PoW, reward 이해
- 프로젝트 라이프사이클 전체 체험

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
