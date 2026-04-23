# Week 15: 기말고사 — AI 보안 자동화 종합 프로젝트

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 종합 실기 (자동화 파이프라인 구축 + Purple Team + RL 분석) |
| 시간 | 3시간 (180분) |
| 배점 | 100점 |
| 환경 | Ollama (10.20.30.200:11434), Bastion (10.20.30.200:8003), ccc-api (localhost:9100) |
| 대상 서버 | secu(10.20.30.1), web(10.20.30.80), siem(10.20.30.100) |
| 제출 | 스크립트 파일 + 실행 결과 캡처 + 최종 보고서 |
| 참고 | 오픈 북 (강의 자료, 인터넷 검색 가능. 타인과 공유 금지) |

## 시험 범위

| 주차 | 주제 | 출제 포인트 |
|------|------|-----------|
| W02~07 | LLM 기초~에이전트 | Ollama API, 프롬프트 설계, 로그 분석, 룰 생성, 취약점 분석 |
| W09~10 | Bastion | /ask·/chat 자연어 I/F, /evidence 감사, /skills·/playbooks·/assets 인벤토리 |
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
# 1. Ollama 확인 (원시 LLM, 포트 11434)
curl -s http://10.20.30.200:11434/v1/models | python3 -c "
import sys,json; models=json.load(sys.stdin)['data']
print(f'Ollama: {len(models)}개 모델')
for m in models[:3]: print(f'  - {m[\"id\"]}')
"

# 2. Bastion 확인 (운영 에이전트, 포트 8003)
curl -s http://10.20.30.200:8003/health | python3 -m json.tool
curl -s http://10.20.30.200:8003/skills | python3 -c "
import sys,json; d=json.load(sys.stdin); print(f'Skills: {len(d.get(\"skills\",[]))} 개')
"
curl -s http://10.20.30.200:8003/assets | python3 -m json.tool | head -20

# 3. ccc-api 확인 (학생/랩 관리, 포트 9100)
curl -s -H "X-API-Key: ccc-api-key-2026" http://localhost:9100/health | python3 -m json.tool

# 4. SubAgent 확인 (현장 에이전트, 포트 8002)
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
[1] 다중 서버 로그 수집 (Bastion /ask 자연어 지시)
       ↓
[2] LLM으로 로그 분석 + 위협 분류 (Ollama API)
       ↓
[3] 탐지 룰 자동 생성 (SIGMA/Wazuh)
       ↓
[4] 대응 조치 실행 + 완료 보고 (Bastion)
```

## 1-1. 다중 서버 로그 수집 (10점)

Bastion에게 **자연어 한 번**으로 3대 서버의 보안 로그를 병렬 수집 지시하라.
Bastion은 자산 인벤토리에서 secu/web/siem을 찾아 각 SubAgent에 명령을 위임하고,
결과를 `/evidence` 에 자동 기록한다.

```bash
# 자연어 지시 한 번으로 3자산 병렬 수집
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "secu/web/siem 세 자산에서 다음을 동시에 수집해줘 — secu: /var/log/auth.log 최근 30줄과 nftables 룰셋 상위 20줄, web: auth.log 최근 30줄과 listening ports 상위 15줄, siem: /var/ossec/logs/alerts/alerts.json 최근 10건"}'

# 증거 조회 — 실행된 명령·자산·exit 확인
curl -s "http://10.20.30.200:8003/evidence?limit=10" | python3 -m json.tool
```

> **검증 완료:** 위 방식은 Bastion manager에서 3자산 병렬 수집으로 동작한다.

| 채점 항목 | 배점 |
|----------|------|
| /ask 자연어 지시 1회로 3자산 수집 | 4점 |
| 자산 이름만으로 라우팅 (IP 하드코딩 X) | 3점 |
| `/evidence` 에 3자산 모두 exit=0 기록 확인 | 3점 |

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
# 방법 A: Bastion /ask 로 증거 기반 분석 (자산 라우팅·증거 참조까지 위임)
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "최근 /evidence 에 남은 3자산(secu/web/siem)의 로그를 근거로 위협을 분류해줘. 출력은 {\"threats\":[{\"server\",\"severity(CRITICAL/HIGH/MEDIUM/LOW)\",\"description\",\"attck_id\"}],\"summary\"} JSON만."}'

# 방법 B: 원시 LLM 직접 호출 (로그를 직접 복사·붙여넣기)
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC Tier 2 분석가. 보안 로그를 분석해 위협 분류. JSON만.\"},
      {\"role\": \"user\", \"content\": \"3자산 로그(붙여넣기): [LOGS]. 출력: {\\\"threats\\\":[{\\\"server\\\":\\\"...\\\",\\\"severity\\\":\\\"...\\\",\\\"description\\\":\\\"...\\\",\\\"attck_id\\\":\\\"T1xxx\\\"}],\\\"summary\\\":\\\"...\\\"}\"}
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

## 1-3. 탐지 룰 생성 + 최종 보고 (15점)

최소 2개의 SIGMA 룰을 LLM으로 생성하고, 전체 파이프라인을 최종 보고서로 정리하라.

```bash
# SIGMA 룰 생성 (원시 LLM 직접 호출)
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가. 유효한 SIGMA YAML만 출력."},
      {"role": "user", "content": "다음 위협을 탐지하는 SIGMA 룰 2개를 작성: 1) SSH 브루트포스 2) 비정상 sudo 사용"}
    ],
    "temperature": 0.2
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# 최종 파이프라인 보고서 — Bastion이 /evidence 를 근거로 작성
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{"message": "최근 /evidence 를 근거로 AI 보안 관제 파이프라인 실행 보고서를 작성해줘. 섹션: 1)수집 요약 2)위협 분류 3)생성된 SIGMA 룰 요약 4)제안 조치"}'
```

---

# 문제 2: 자율 Purple Team (30점)

## 2-1. Red Team — 정보 수집 (10점)

Red 관점을 얻어 자연어 지시로 Bastion에 실행시킨다. 읽기 전용(non-destructive)만 허용.

```bash
# (1) Red 관점 LLM 제안 — gemma3:12b
PLAN=$(curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "침투 테스트 전문가. 안전한(non-destructive) 정보 수집 명령 3개를 JSON으로 제안."},
      {"role": "user", "content": "대상: web(10.20.30.80). 포트/서비스 버전/사용자 권한 점검. 형식: [{\"title\":\"...\",\"command\":\"...\"}]"}
    ],
    "temperature": 0.3
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])")
echo "$PLAN"

# (2) Bastion /ask 로 자연어 실행 지시 — 위 $PLAN 을 참조 메시지에 붙여 넣는다
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d "{\"message\": \"web 자산에 대해 다음 읽기 전용 점검 명령들을 수행하고 결과를 요약해줘: $PLAN\"}"
```

## 2-2. Blue Team — 방어 조치 (10점)

Red Team 결과를 LLM에게 전달하여 방어 계획을 생성하라. (실행은 dry_run만)

## 2-3. Purple Team 보고서 (10점)

LLM으로 종합 보고서를 작성하라. 포함: 점검개요, 발견사항(CVSS), 대응현황, 잔존위험, 권고사항.

---

# 문제 3: RL 정책 분석 + 보상 함수 설계 (30점)

## 3-1. 보상 데이터 축적 (10점)

low/medium/high/fail 을 섞어 Bastion 에 여러 번 자연어 지시를 보내 `/evidence` 에
다양한 신호가 쌓이게 한다.

```bash
# 성공/실패·위험도 혼합
for q in \
  "web 자산에서 echo ok 만 실행해줘" \
  "web 자산의 uptime 을 알려줘" \
  "web 자산의 df -h 를 알려줘" \
  "web 자산에서 intentionally-failing-command 실행 (실패 기대)" \
  "secu 자산에서 nftables 룰셋을 읽기 전용으로 보여줘"
do
  curl -s -X POST http://10.20.30.200:8003/ask \
    -H 'Content-Type: application/json' \
    -d "{\"message\": \"$q\"}" > /dev/null
done

# 축적된 증거 요약
curl -s "http://10.20.30.200:8003/evidence?limit=50" | python3 -m json.tool | head -60
```

## 3-2. 학습 경향 분석 (10점)

Bastion의 내부 RL 상태는 외부로 열리지 않는다. 따라서 증거에서 경향을 집계한다.

```bash
# (skill, risk, exit_code) 분포 — 정책이 어디로 수렴하는지 역추적
curl -s "http://10.20.30.200:8003/evidence?limit=100" \
  | python3 -c "
import sys,json,collections
d=json.load(sys.stdin).get('evidence',[])
c=collections.Counter((e.get('skill') or e.get('playbook'), e.get('risk'), e.get('exit_code',0)) for e in d)
for k,v in c.most_common(20): print(v,k)
"

# 원시 LLM에게 위 분포로 학습 경향 해석 요청
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[{"role":"system","content":"RL 분석가. 증거 분포에서 정책 수렴 여부를 판단."},{"role":"user","content":"다음 (skill,risk,exit) 분포를 보고 Bastion이 특정 skill에 편향되는 신호가 있는지 분석해줘: [위 집계 붙여넣기]"}],"temperature":0.3}'
```

> **관찰 포인트:** 동일 의도에 대해 특정 skill/playbook의 비율이 높고, exit=0 의 비중이 올라가면
> 정책이 수렴하고 있다는 신호이다.

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
# Ollama — 원시 LLM (포트 11434, OpenAI 호환)
curl -s http://10.20.30.200:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[...],"temperature":0.2}'

# Bastion — 운영 에이전트 (포트 8003, 내부망)
POST /ask       # 자연어 단일 질의 (동기) {"answer":"..."}
POST /chat      # NDJSON 스트림 (think/tool/evidence/final)
GET  /evidence  # 실행 증거 (자산·skill·exit·시각)
GET  /skills    # Skill 목록
GET  /playbooks # Playbook 목록
GET  /assets    # 자산 인벤토리
GET  /health    # 헬스체크

# ccc-api — 학생/랩 관리 (포트 9100, X-API-Key 필요)
GET  /health, /students, ... (학생/랩 CRUD)
```

---

## 학기 마무리

이 과목에서 학습한 핵심 역량:

1. **LLM 활용**: Ollama(:11434) API로 보안 분석, 룰 생성, 보고서 작성
2. **프롬프트 엔지니어링**: system/user 메시지 설계, few-shot, JSON 강제
3. **AI 에이전트 계층**: 외부 사용자(Master) → Bastion(Manager, :8003) → SubAgent(:8002)
4. **Bastion 운용**: `/ask`·`/chat` 자연어 I/F, `/evidence` 감사, `/skills`·`/playbooks`·`/assets` 인벤토리
5. **자율 보안**: Red/Blue/Purple 관점을 자연어 지시·스트림 대화로 구현
6. **분산 지식**: 자산별 local_knowledge 개념과 Bastion 자산 인벤토리 통합
7. **RL 정책**: 보상 신호(assertions·exit_code·지연)·/evidence 기반 경향 관찰·보상 해킹 방지

> **AI는 보안 전문가를 대체하지 않는다. 보안 전문가의 능력을 증폭시키는 도구이다.**

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### CCC Bastion Agent
> **역할:** CCC 자율 운영 에이전트 — 스킬/플레이북/경험 학습  
> **실행 위치:** `bastion (10.20.30.201)`  
> **접속/호출:** TUI `./dev.sh bastion`, API `http://10.20.30.200:8003`

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

