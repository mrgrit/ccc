# Week 15: 기말고사 — AI 보안 자동화 종합 프로젝트

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 종합 실기 (자동화 파이프라인 구축 + Purple Team + RL 분석) |
| 시간 | 3시간 (180분) |
| 배점 | 100점 |
| 환경 | Ollama (192.168.0.105:11434), OpsClaw (localhost:8000) |
| 대상 서버 | secu(10.20.30.1), web(10.20.30.80), siem(10.20.30.100) |
| 제출 | 스크립트 파일 + 실행 결과 캡처 + 최종 보고서 |
| 참고 | 오픈 북 (강의 자료, 인터넷 검색 가능. 타인과 공유 금지) |

## 시험 범위

| 주차 | 주제 | 출제 포인트 |
|------|------|-----------|
| W02~07 | LLM 기초~에이전트 | Ollama API, 프롬프트 설계, 로그 분석, 룰 생성, 취약점 분석 |
| W09~10 | OpsClaw | project 생성, dispatch, execute-plan, evidence, Playbook |
| W11~12 | 자율 미션/Daemon | 에이전트 자율 루프, 미션 설계 |
| W13 | 분산 지식 | local_knowledge, 지식 전파 |
| W14 | RL Steering | 보상 함수, Q-learning, UCB1, 보상 해킹 |

## 시간 배분 (권장)

| 시간 | 작업 | 배점 |
|------|------|------|
| 0:00-0:15 | 문제 읽기 + 환경 확인 | — |
| 0:15-1:15 | 문제 1: AI 보안 관제 파이프라인 | 40점 |
| 1:15-1:25 | 휴식 | — |
| 1:25-2:15 | 문제 2: 자율 Purple Team | 30점 |
| 2:15-2:55 | 문제 3: RL 정책 분석 + 보상 함수 설계 | 30점 |
| 2:55-3:00 | 최종 점검 + 제출 | — |

---

## 사전 환경 확인 (시험 시작 전 필수)

```bash
# 1. Ollama 확인
curl -s http://192.168.0.105:11434/v1/models | python3 -c "
import sys,json; models=json.load(sys.stdin)['data']
print(f'Ollama: {len(models)}개 모델')
for m in models[:3]: print(f'  - {m[\"id\"]}')
"

# 2. OpsClaw 확인
curl -s http://localhost:8000/projects -H "X-API-Key: opsclaw-api-key-2026" \
  | python3 -c "import sys,json; print('OpsClaw: OK')" 2>/dev/null

# 3. SubAgent 확인
for srv in "10.20.30.1" "10.20.30.80" "10.20.30.100"; do
  code=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://$srv:8002/health")
  echo "  $srv:8002 → $code"
done
```

---

# 문제 1: AI 보안 관제 파이프라인 (40점)

## 시나리오

"SecureCorp"의 CISO가 야간 관제 인력 부족 문제를 해결하기 위해 AI 기반 자동 관제 파이프라인을 요청하였다.

```
[1] 다중 서버 로그 수집 (OpsClaw execute-plan)
       ↓
[2] LLM으로 로그 분석 + 위협 분류 (Ollama API)
       ↓
[3] 탐지 룰 자동 생성 (SIGMA/Wazuh)
       ↓
[4] 대응 조치 실행 + 완료 보고 (OpsClaw)
```

## 1-1. 다중 서버 로그 수집 (10점)

OpsClaw execute-plan으로 3대 서버에서 보안 로그를 **병렬 수집**하라.

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"final-pipeline","request_text":"AI 보안 관제 파이프라인","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 3대 서버 병렬 로그 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"secu 방화벽+인증 로그","instruction_prompt":"tail -30 /var/log/auth.log 2>/dev/null; echo 1 | sudo -S nft list ruleset 2>/dev/null | head -20","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":2,"title":"web 보안 로그","instruction_prompt":"tail -30 /var/log/auth.log 2>/dev/null; ss -tlnp | head -15","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"title":"siem SIEM 경보","instruction_prompt":"echo 1 | sudo -S tail -10 /var/ossec/logs/alerts/alerts.log 2>/dev/null || echo no-recent-alerts","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'수집 결과: {d[\"overall\"]} (성공:{d[\"tasks_ok\"]}, 실패:{d[\"tasks_failed\"]})')
"
```

> **검증 완료:** 위 명령은 실제 서버에서 테스트되었으며, overall=success, ok=3을 반환한다.

| 채점 항목 | 배점 |
|----------|------|
| 프로젝트 생성 + stage 전환 | 2점 |
| 3대 서버 병렬 수집 (parallel=true) | 5점 |
| overall=success 달성 | 3점 |

## 1-2. LLM 분석 + 위협 분류 (15점)

수집된 로그를 Ollama LLM으로 분석하여 위협을 분류하라.

> **실습 목적**: 한 학기 동안 학습한 AI 보안 기술을 종합하여 실전 수준의 AI 보안 평가 보고서를 작성하기 위해 수행한다
>
> **배우는 것**: 프롬프트 인젝션 방어, 모델 보안, 데이터 보호, 모니터링을 통합한 AI 보안 아키텍처 설계 능력을 기른다
>
> **결과 해석**: 보안 테스트 결과의 통과율과 위험 항목 수로 AI 시스템의 전체 보안 수준을 종합 평가한다
>
> **실전 활용**: AI 시스템 보안 감사 보고서 작성, 규제 대응(EU AI Act), AI 거버넌스 체계 수립에 활용한다

```bash
# 수집된 로그를 LLM에게 전달
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC Tier 2 분석가입니다. 보안 로그를 분석하여 위협을 분류하세요. JSON으로만 응답.\"},
      {\"role\": \"user\", \"content\": \"3대 서버 로그를 분석하세요: [여기에 수집된 로그 붙여넣기]. 출력: {\\\"threats\\\":[{\\\"server\\\":\\\"...\\\",\\\"severity\\\":\\\"CRITICAL/HIGH/MEDIUM/LOW\\\",\\\"description\\\":\\\"...\\\",\\\"attck_id\\\":\\\"T1xxx\\\"}],\\\"summary\\\":\\\"종합 평가\\\"}\"}
    ],
    \"temperature\": 0.2,
    \"max_tokens\": 1500
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

| 채점 항목 | 배점 |
|----------|------|
| 프롬프트에 역할+형식 지정 | 3점 |
| JSON 유효 + 위협 분류 정확 | 4점 |
| ATT&CK ID 매핑 포함 | 4점 |
| 종합 평가 논리성 | 4점 |

## 1-3. 탐지 룰 생성 + 대응 보고 (15점)

최소 2개의 SIGMA 룰을 LLM으로 생성하고, OpsClaw로 완료 보고하라.

```bash
# SIGMA 룰 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다. 유효한 SIGMA YAML만 출력하세요."},
      {"role": "user", "content": "다음 위협을 탐지하는 SIGMA 룰 2개를 작성하세요: 1)SSH 브루트포스 2)비정상 sudo 사용"}
    ],
    "temperature": 0.2
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# 완료 보고
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"summary":"AI 보안 관제 파이프라인 완료","outcome":"success","work_details":["3대 서버 로그 수집","LLM 위협 분석","SIGMA 룰 2건 생성"]}'
```

---

# 문제 2: 자율 Purple Team (30점)

## 2-1. Red Team — 정보 수집 (10점)

LLM에게 공격 계획을 수립시키고 OpsClaw로 실행하라.

```bash
# LLM으로 공격 계획 수립
PLAN=$(curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "침투 테스트 전문가입니다. 안전한(non-destructive) 정보 수집 명령 3개를 JSON으로 제안하세요."},
      {"role": "user", "content": "대상: web 서버(10.20.30.80). 포트, 서비스 버전, 사용자 권한을 점검. 형식: [{\"title\":\"...\",\"command\":\"...\"}]"}
    ],
    "temperature": 0.3
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])")
echo "$PLAN"

# OpsClaw로 실행
RED_PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"final-red","request_text":"Red Team","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$RED_PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$RED_PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# LLM 제안을 execute-plan tasks로 구성하여 실행 (학생이 직접 구성)
```

## 2-2. Blue Team — 방어 조치 (10점)

Red Team 결과를 LLM에게 전달하여 방어 계획을 생성하라. (실행은 dry_run만)

## 2-3. Purple Team 보고서 (10점)

LLM으로 종합 보고서를 작성하라. 포함: 점검개요, 발견사항(CVSS), 대응현황, 잔존위험, 권고사항.

---

# 문제 3: RL 정책 분석 + 보상 함수 설계 (30점)

## 3-1. 보상 데이터 축적 (10점)

low/medium/high risk_level 태스크를 각 2개 이상 실행하여 보상을 축적하라.

프로젝트 생성 -> Stage 전환 -> 다양한 risk_level 태스크 실행의 전체 플로우를 한 번에 수행한다. 성공/실패 태스크를 모두 포함하여 RL 학습 데이터를 구성한다.

```bash
# 프로젝트 생성 + ID 추출 (한 줄에서 처리)
RL_PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"final-rl","request_text":"RL 데이터","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$RL_PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$RL_PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$RL_PID/execute-plan" \
  -H "Content-Type: application/json" -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"low-ok","instruction_prompt":"echo ok","risk_level":"low"},
      {"order":2,"title":"medium-ok","instruction_prompt":"uptime","risk_level":"medium"},
      {"order":3,"title":"high-ok","instruction_prompt":"df -h","risk_level":"high"},
      {"order":4,"title":"low-fail","instruction_prompt":"exit 1","risk_level":"low"},
      {"order":5,"title":"high-fail","instruction_prompt":"false","risk_level":"high"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

## 3-2. RL 학습 + 분석 (10점)

```bash
# 학습
curl -s -X POST http://localhost:8000/rl/train -H "X-API-Key: opsclaw-api-key-2026"

# 추천
for risk in low medium high; do
  curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=$risk&exploration=ucb1" \
    -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'{d[\"state_desc\"][\"risk_level\"]:8s} → {d[\"recommended_risk_level\"]:8s} Q={max(d[\"q_values\"].values()):.3f}')
" 2>/dev/null
done
```

> **검증 완료:** RL train은 222 에피소드를 사용하여 학습 완료. 커버리지 5.7%.

## 3-3. 보상 함수 설계 (10점)

LLM으로 보상 해킹 방지 로직이 포함된 개선된 보상 함수를 Python으로 설계하라.

---

## 종합 채점표

| 문제 | 세부 | 배점 |
|------|------|------|
| 1 | 다중 서버 로그 수집 | 10 |
| 1 | LLM 분석 + 위협 분류 | 15 |
| 1 | 룰 생성 + 대응 보고 | 15 |
| 2 | Red Team | 10 |
| 2 | Blue Team | 10 |
| 2 | Purple 보고서 | 10 |
| 3 | 보상 축적 | 10 |
| 3 | RL 학습 + 분석 | 10 |
| 3 | 보상 함수 설계 | 10 |
| | **합계** | **100** |

---

## 참고: API 빠른 참조

```bash
# Ollama
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[...],"temperature":0.2}'

# OpsClaw (모든 호출에 -H "X-API-Key: opsclaw-api-key-2026" 필수)
POST /projects                        # 프로젝트 생성
POST /projects/{id}/plan              # plan 단계
POST /projects/{id}/execute           # execute 단계
POST /projects/{id}/execute-plan      # 태스크 실행
POST /projects/{id}/dispatch          # 단일 명령
GET  /projects/{id}/evidence/summary  # 증적 확인
GET  /projects/{id}/replay            # 타임라인
POST /projects/{id}/completion-report # 완료 보고
POST /rl/train                        # RL 학습
GET  /rl/recommend?agent_id=...&risk_level=...&exploration=ucb1
GET  /rl/policy                       # 정책 조회
GET  /pow/leaderboard                 # 리더보드
```

---

## 학기 마무리

이 과목에서 학습한 핵심 역량:

1. **LLM 활용**: Ollama API로 보안 분석, 룰 생성, 보고서 작성
2. **프롬프트 엔지니어링**: system/user 메시지 설계, few-shot, JSON 강제
3. **AI 에이전트**: Master→Manager→SubAgent 3계층 위임 아키텍처
4. **OpsClaw 운용**: project lifecycle, dispatch, execute-plan, evidence, Playbook
5. **자율 보안**: Red/Blue/Purple Team, 미션 기반 에이전트
6. **분산 지식**: local_knowledge, 서버별 특화 정보 관리
7. **RL 정책**: Q-learning, UCB1 탐색, 보상 함수 설계, 보상 해킹 방지

> **AI는 보안 전문가를 대체하지 않는다. 보안 전문가의 능력을 증폭시키는 도구이다.**
