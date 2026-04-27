# Week 08: 중간고사 — LLM 보안 도구 구축

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (도구 구축 + 분석 보고서) |
| 시간 | 3시간 (180분) |
| 배점 | 100점 |
| 환경 | Ollama (10.20.30.200:11434), Bastion (10.20.30.200:8003), ccc-api (localhost:9100) |
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
| 1:50-2:30 | 문제 3: Bastion 오케스트레이션 | 30점 |
| 2:30-3:00 | 보고서 정리 + 제출 | — |

---

## 용어 해설 (시험에서 사용되는 주요 용어)

> 시험 중 헷갈리면 이 표를 참고하라.

| 용어 | 설명 | 예시 |
|------|------|------|
| **Ollama API** | 로컬 LLM을 HTTP API로 호출하는 인터페이스 | `curl http://10.20.30.200:11434/v1/chat/completions` |
| **system 메시지** | LLM에게 역할과 규칙을 부여하는 메시지 | `"role":"system","content":"보안 분석가입니다"` |
| **user 메시지** | 사용자의 실제 요청/데이터 | `"role":"user","content":"이 로그를 분석하세요"` |
| **temperature** | LLM 출력의 창의성/무작위성 조절 (0=결정론, 1=창의적) | 분석: 0~0.3, 룰 생성: 0.2~0.5 |
| **few-shot** | 예시를 함께 제공하여 출력 품질을 높이는 프롬프트 기법 | "예시: 입력X→출력Y. 이제 입력Z를 처리하세요" |
| **SIGMA 룰** | SIEM에 독립적인 범용 탐지 룰 포맷 (YAML) | `detection: selection: EventID: 4625` |
| **상관 분석** | 여러 이벤트를 연결하여 공격 시나리오를 추론하는 것 | SSH 실패 3회→성공→계정 추가 = 브루트포스→침투 |
| **킬체인** | 공격의 단계별 진행 과정 | 정찰→침투→권한상승→지속성→유출 |
| **IOC** | Indicator of Compromise, 침해 지표 | 악성 IP: 203.0.113.50 |
| **CVSS** | 취약점 심각도 점수 (0~10점) | 9.8 = Critical |
| **Bastion `/ask`** | 자연어 단일 질의 엔드포인트 | `POST /ask {"message":"..."}` |
| **Bastion `/chat`** | NDJSON 스트림 대화 엔드포인트 | `POST /chat {"message":"..."}` |
| **evidence** | Bastion이 자동 기록하는 실행 증적 (명령·자산·exit·시각) | `GET /evidence?limit=N` |
| **Skill** | Bastion에 등록된 결정론적 도구 | `GET /skills` 로 목록 확인 |
| **Playbook** | 결정론 시나리오(다단계 Skill 조합) | `GET /playbooks` 로 목록 확인 |

---

## 사전 환경 확인 (시험 시작 전 필수)

시험 시작 전 다음을 확인하라. 하나라도 실패하면 감독관에게 보고한다.

```bash
# 1. Ollama LLM 연결 확인
curl -s http://10.20.30.200:11434/v1/models | python3 -c "
import sys,json
models = json.load(sys.stdin)['data']
print(f'사용 가능한 모델: {len(models)}개')
for m in models[:5]:
    print(f'  - {m[\"id\"]}')
"
# 기대 결과: gemma3:12b, llama3.1:8b 등 모델 목록

# 2. Ollama 응답 테스트
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[{"role":"user","content":"hello"}],"max_tokens":10}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
# 기대 결과: 짧은 응답 텍스트

# 3. Bastion API 연결 확인 (manager VM :8003)
curl -s http://10.20.30.200:8003/health | python3 -m json.tool
# 기대 결과: {"status": "ok", ...}

curl -s http://10.20.30.200:8003/skills | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Bastion Skill: {len(d.get(\"skills\",[]))}개 등록')
"

# 4. 원격 서버 접속 확인
for srv in "ccc@10.20.30.1" "ccc@10.20.30.80" "ccc@10.20.30.100"; do
  ssh $srv "hostname" 2>/dev/null || echo "$srv: 접속 실패"
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
OLLAMA_URL="http://10.20.30.200:11434/v1/chat/completions"
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
  curl -s http://10.20.30.200:11434/v1/chat/completions \
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
curl -s http://10.20.30.200:11434/v1/chat/completions \
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

# 문제 3: Bastion 오케스트레이션 (30점)

## 3.1 자연어 지시를 통한 다중 자산 보안 점검 (15점)

Bastion(Manager 에이전트, `10.20.30.200:8003`)에게 **자연어로** 3대 서버
(secu / web / siem)의 보안 상태 점검을 지시하고, 증거가 `/evidence`에 남는지 확인하라.

Bastion은 내부적으로 자산 인벤토리(`/assets`)와 Skill/Playbook을 조합해
해당 자산의 SubAgent(:8002)에 명령을 위임하고 결과를 수집한다.

### Step 1: 사전 점검 (헬스체크 + 자산 확인)

```bash
# 3계층 헬스체크
curl -s -H "X-API-Key: ccc-api-key-2026" http://localhost:9100/health | python3 -m json.tool
curl -s http://10.20.30.200:8003/health | python3 -m json.tool
curl -s http://10.20.30.1:8002/health   | python3 -m json.tool
curl -s http://10.20.30.80:8002/health  | python3 -m json.tool
curl -s http://10.20.30.100:8002/health | python3 -m json.tool

# Bastion에 등록된 자산 목록 확인 — 이름으로 지시할 수 있어야 한다
curl -s http://10.20.30.200:8003/assets | python3 -m json.tool
```

### Step 2: 자연어 지시로 3대 서버 동시 점검

```bash
# 한 번의 자연어 요청으로 Bastion이 자산 루팅·명령 위임·결과 정리까지 수행
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "secu/web/siem 세 자산의 보안 상태를 동시에 점검해줘. secu는 nftables 룰셋 상위 30줄, web은 최근 로그인·열린 포트·sudoers, siem은 wazuh-manager 상태와 alerts.json 최근 3건을 각각 수집해 요약해줘"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer',d))"
```

**무엇을 확인하는가:**
- `answer` 필드에 3자산 × 3항목의 결과 요약이 구조적으로 들어있는가
- Bastion이 자산 이름(`web`, `secu`, `siem`)만으로 올바른 IP를 찾아 위임했는가
- 민감 정보(예: 토큰, 해시)를 응답에서 마스킹 처리하는가

### Step 3: Evidence 감사 추적

```bash
# 방금 /ask 로 실행된 명령들이 어떻게 기록됐는지 확인
curl -s "http://10.20.30.200:8003/evidence?limit=20" | python3 -m json.tool
```

각 entry에는 최소한 `{asset, command, exit_code, stdout_head, ts}` 가 있어야 하며,
감사 관점에서 "누가/언제/어디서/무엇을/결과"가 재현 가능해야 한다.

### Step 4: 이상 징후 심화 분석 (/chat 스트림)

```bash
# /ask 결과에서 의심 항목이 있으면 대화로 파고든다 (NDJSON 스트림)
curl -N -s -X POST http://10.20.30.200:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "방금 점검에서 이상치가 있으면 MITRE ATT&CK로 매핑하고, secu에 즉시 적용 가능한 차단 룰을 제안해줘"}'
```

> **주의사항:**
> - Bastion에는 `/projects/{id}/plan|execute|dispatch` 같은 상태머신 엔드포인트가 없다. 자연어 API 한 종류(`/ask`, `/chat`)만 사용한다.
> - SubAgent(:8002)를 직접 호출하지 말 것 — 반드시 Bastion을 거친다(감사·권한 게이트를 위해).
> - `ccc-api` 호출(`localhost:9100/*`)에만 `X-API-Key: ccc-api-key-2026` 를 붙인다.

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 3계층 헬스체크 완료 | 3점 | ccc-api/Bastion/SubAgent 모두 ok |
| 자연어 지시 1회로 3자산 점검 | 5점 | `/ask` 응답에 3자산 결과가 모두 포함 |
| 자산 이름만으로 라우팅 확인 | 2점 | IP 하드코딩 없이 web/secu/siem로 지시 |
| /evidence 에 실행 이력 확인 | 3점 | 최근 항목에 명령·자산·exit 기록 |
| /chat 로 이상치 심화 분석 | 2점 | ATT&CK 매핑 or 차단 룰 제안 |

## 3.2 결과 분석 보고서 (15점)

`/evidence` 와 `/ask` 의 답변을 근거로 **보안 상태 보고서**를 작성하라.
LLM 보조는 Ollama(:11434) 또는 Bastion(:8003 `/ask`) 둘 다 허용된다.

### 보고서에 포함할 내용

```
1. 점검 개요
   - 점검 일시, 대상 자산, 점검 항목
   - 사용한 Bastion 엔드포인트(/ask·/chat) 요약

2. 발견 사항
   - 각 자산별 주요 발견 (방화벽 룰, 열린 포트, 사용자 권한 등)
   - 정상/이상 판정 근거 (evidence 인용)

3. 위험도 평가
   - CVSS 또는 자체 기준으로 위험도 산정
   - 우선순위별 정리

4. 대응 권고
   - 즉시 조치 (Critical/High)
   - 중기 조치 (Medium)
   - 장기 개선 (Low)

5. 증적 정보
   - /evidence 원문 발췌
   - /ask 답변 원문 발췌
```

**구현 예 (Ollama 직접 호출):**
```bash
# 증거 원문을 변수에 저장
EVIDENCE=$(curl -s "http://10.20.30.200:8003/evidence?limit=30")

# Ollama에게 보고서 초안 요청
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 컨설턴트입니다. Bastion evidence를 근거로 전문적인 보고서를 작성하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 evidence를 근거로 보고서를 작성하세요. 1)점검개요 2)발견사항 3)위험도평가 4)대응권고. evidence:\\n$EVIDENCE\"}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 2000
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

**구현 예 (Bastion `/ask` 직접 사용):**
```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "최근 /evidence 상위 30건을 근거로 보안 점검 보고서를 작성해줘(점검개요/발견/위험도/대응)"}'
```

**채점 기준:**
| 항목 | 배점 | 기준 |
|------|------|------|
| 점검 개요 완성도 | 3점 | 일시, 대상, 항목, 사용 엔드포인트 명시 |
| 발견 사항 정확성 | 4점 | 실제 evidence와 일치하는 분석 |
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
| **3** | Bastion 프로젝트 실행 | 15 |
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
| Bastion `/projects/...` 호출 시도 | 404 | Bastion은 `/ask`·`/chat`·`/evidence`만 제공 |
| `ccc-api` 호출에 `X-API-Key` 누락 | 401 에러 | `localhost:9100/*` 는 헤더 필수 |
| Ollama와 Bastion 포트 혼동 | 엉뚱한 응답 | 11434=Ollama, 8003=Bastion |
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
# Bastion Project ID: prj_xxxxxxxx
```

---

## 검증 체크리스트

- [ ] Ollama API 연결 확인 (`10.20.30.200:11434`)
- [ ] Bastion API 연결 확인 (`10.20.30.200:8003/health`, `/skills`, `/assets`)
- [ ] 문제 1: 6개 알림 전부 분류 완료
- [ ] 문제 1: 킬체인 3단계 이상 식별
- [ ] 문제 1: 대응 조치 3개 이상 (실행 가능 명령 포함)
- [ ] 문제 1: JSON 통합 출력 생성
- [ ] 문제 2: SIGMA 룰 3개 생성 (YAML 유효)
- [ ] 문제 2: 3개 룰 교차 검증 완료
- [ ] 문제 3: 자연어 지시 1회로 3자산(web/secu/siem) 점검
- [ ] 문제 3: `/evidence` 에 실행 이력 기록 확인
- [ ] 문제 3: `/chat` 으로 이상치 심화 분석
- [ ] 문제 3: LLM 분석 보고서 작성
- [ ] 모든 스크립트 파일 상단에 학번/이름 기재

---

## 다음 주 예고
**Week 09: Bastion (1) — 기본**
- `/ask`·`/chat` 엔드포인트 실전 활용
- Skill·Playbook 목록과 호출 패턴
- `/evidence` 감사 추적
- 자산 온보딩(`/onboard`)과 라우팅

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

Bastion은 워크플로 상태머신을 외부에 노출하지 않는다.
자연어 I/F 2종(`/ask`, `/chat`)과 조회 엔드포인트 몇 개가 전부이다.

```
POST /ask          → 단일 자연어 질의, 동기 응답 {"answer": "..."}
POST /chat         → 대화형 NDJSON 스트림 (한 줄 = 한 이벤트)
GET  /evidence     → 과거 실행 증거 (자산/명령/결과/시각)
GET  /skills       → 등록된 Skill(도구) 목록
GET  /playbooks    → 등록된 Playbook(결정론 시나리오) 목록
GET  /assets       → 자산 인벤토리(이름↔IP↔역할)
POST /onboard      → 신규 자산 온보딩
GET  /health       → 헬스체크

ccc-api(:9100)은 별도이며 X-API-Key: ccc-api-key-2026 필요.
Bastion(:8003)은 내부망 접근 가정 — API 키 불필요.
```

---

## 실습 부록: 취약 모델 생성과 QLoRA 파인튜닝

AI Security 관점에서 모델의 안전장치를 약화시키는 파인튜닝 공격(fine-tuning attack)을 
직접 실습하고 방어 방안을 학습한다. 상세 방법은 `finetune/` 디렉터리와 
AI Safety 과정 Week 07 교안을 참고.

### 핵심 요약

| 방법 | 시간 | 수정 대상 | 위험도 |
|------|------|----------|--------|
| Modelfile (시스템 프롬프트) | 5분 | 프롬프트만 | 낮음 — 프롬프트 교체로 복구 가능 |
| QLoRA (가중치 수정) | 30분 | 모델 가중치 | 높음 — 모델 자체가 변경됨 |

### 방어 관점 학습 포인트
- 30건의 데이터 + 72초 학습으로 안전 동작 변경 가능
- 모델 접근 제어(API key, rate limit)의 중요성
- 정기적 안전 벤치마크로 모델 변질 감지
- 파인튜닝 이력 추적(provenance)의 필요성

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Ollama + LangChain
> **역할:** 로컬 LLM 서빙(Ollama) + 체인 오케스트레이션(LangChain)  
> **실행 위치:** `bastion (LLM 서버)`  
> **접속/호출:** `OLLAMA_HOST=http://10.20.30.201:11434`, Python `from langchain_ollama import OllamaLLM`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.ollama/models/` | 다운로드된 모델 블롭 |
| `/etc/systemd/system/ollama.service` | 서비스 유닛 |

**핵심 설정·키**

- `OLLAMA_HOST=0.0.0.0:11434` — 외부 바인드
- `OLLAMA_KEEP_ALIVE=30m` — 모델 유휴 유지
- `LLM_MODEL=gemma3:4b (env)` — CCC 기본 모델

**로그·확인 명령**

- `journalctl -u ollama` — 서빙 로그
- `LangChain `verbose=True`` — 체인 단계 출력

**UI / CLI 요점**

- `ollama list` — 설치된 모델
- `curl -XPOST $OLLAMA_HOST/api/generate -d '{...}'` — REST 생성
- LangChain `RunnableSequence | parser` — 체인 조립 문법

> **해석 팁.** Ollama는 **첫 호출에 모델 로드**가 커서 지연이 크다. 성능 실험 시 워밍업 호출을 배제하고 측정하자.

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

본 주차 (8주차) 학습 주제와 직접 연관된 *실제* incident:

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
