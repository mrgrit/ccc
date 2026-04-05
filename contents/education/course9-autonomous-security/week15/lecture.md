# Week 15: 기말고사 — 자율 Purple Team 구축

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (자율 보안 시스템 구축 + 운용 + 분석) |
| 시간 | 3시간 (180분) |
| 배점 | 100점 |
| 환경 | OpsClaw (localhost:8000), Ollama (192.168.0.105:11434), 실습 서버 4대 |
| 제출 | OpsClaw completion-report + 분석 스크린샷 |
| 참고 | 오픈 북 (강의 자료, 인터넷 검색 가능. 타인과 공유 금지) |

## 시험 범위

| 주차 | 주제 | 출제 범위 |
|------|------|---------|
| Week 09 | Experience와 4-Layer Memory | Evidence/Experience 축적, FTS 검색, Auto-Promote |
| Week 10 | Schedule과 Watcher | cron 스케줄, 이상 탐지, 인시던트 자동 생성 |
| Week 11 | 자율 Blue Agent | LLM 경보 분석, 5분 관제, Slack 알림, 오탐 처리 |
| Week 12 | 자율 Red Agent | 자동 스캐닝, 공격 시나리오 생성, Purple Team 설계 |
| Week 13 | 분산 지식 아키텍처 | SubAgent별 Experience, 지식 교환, PoW 교차 검증 |
| Week 14 | RL Steering과 정책 최적화 | reward 가중치, Q-learning, 정책 추천/해석 |

---

## 학습 목표

- Red Agent + Blue Agent를 동시에 구성하고 운용할 수 있다
- 30분간의 자율 Purple Team 운용에서 축적된 Evidence를 분석할 수 있다
- RL 학습을 통해 정책 수렴과 에이전트 행동 변화를 관찰하고 해석할 수 있다
- 종합 보안 자동화 파이프라인을 설계하고 OpsClaw completion-report로 보고할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

## 강의 시간 배분 (3시간)

| 시간 | 파트 | 내용 | 배점 |
|------|------|------|------|
| 0:00-0:15 | Part 1 | 문제 읽기 + 환경 확인 | — |
| 0:15-0:50 | Part 2 | 문제 1: Red Agent 구성 (자동 스캔 + 공격) | 25점 |
| 0:50-1:25 | Part 3 | 문제 2: Blue Agent 구성 (자동 탐지 + 대응) | 25점 |
| 1:25-1:35 | — | 휴식 | — |
| 1:35-2:10 | Part 4 | 문제 3: Purple Team 동시 운용 (30분) | 25점 |
| 2:10-2:45 | Part 5 | 문제 4: Evidence 분석 + RL 수렴 확인 | 15점 |
| 2:45-3:00 | Part 6 | 문제 5: completion-report 작성 | 10점 |

## 용어 해설 (자율보안시스템 과목)

| 용어 | 설명 | 예시 |
|------|------|------|
| **Purple Team** | Red(공격) + Blue(방어) 동시 운용 | 공격→탐지→대응→학습 |
| **Red Agent** | 자동 취약점 스캐닝/공격 에이전트 | gemma3:12b 기반 |
| **Blue Agent** | 자동 경보 분석/대응 에이전트 | llama3.1:8b 기반 |
| **Evidence** | 태스크 실행 증적 | stdout, stderr, exit_code |
| **Experience** | 장기 보존 지식 | 프로젝트를 넘어 유지 |
| **PoW** | Proof of Work — 태스크 무결성 증명 | SHA-256 해시 체인 |
| **RL Steering** | 보상으로 에이전트 행동 유도 | risk_penalty 조절 |
| **Q-learning** | 상태-행동 가치 학습 | Q(s,a) 업데이트 |
| **convergence** | Q-value가 안정 값에 수렴 | 변화량 < 0.01 |
| **MTTD** | Mean Time To Detect — 평균 탐지 시간 | 공격→탐지 시간 |
| **MTTR** | Mean Time To Respond — 평균 대응 시간 | 탐지→대응 시간 |
| **Detection Rate** | 탐지율 = 탐지 공격 / 전체 공격 | 80% = 5건 중 4건 탐지 |
| **FP Rate** | 오탐률 = 오탐 / (오탐 + 정상판정) | 10% = 10건 중 1건 오탐 |
| **completion-report** | OpsClaw 프로젝트 최종 보고서 | summary + outcome + details |
| **execute-plan** | 여러 태스크를 순차 실행하는 API | tasks 배열 전달 |
| **dispatch** | 단일 명령 즉시 실행 | 명령 1개 전달 |

---

## Part 1: 사전 환경 확인 (0:00-0:15)

시험 시작 전 다음을 확인하라. 하나라도 실패하면 감독관에게 보고한다.

> **실습 목적**: 한 학기 동안 학습한 자율보안 기술을 종합하여 조직 맞춤형 자율보안 아키텍처를 설계하기 위해 수행한다
>
> **배우는 것**: OODA Loop, Playbook, PoW, RL, Multi-Agent, 안전 경계를 통합한 자율보안 아키텍처 설계 능력을 기른다
>
> **결과 해석**: 설계한 아키텍처의 자율화 수준(Level 0~5), 커버리지, MTTR 예상치로 설계 품질을 평가한다
>
> **실전 활용**: 조직의 보안 자동화 전략 수립, 자율보안 시스템 도입 계획서 작성, 예산 확보를 위한 효과 분석에 활용한다

```bash
# 1. OpsClaw Manager API 연결 확인
curl -s http://localhost:8000/projects \
  -H "X-API-Key: opsclaw-api-key-2026" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OpsClaw: 정상 (프로젝트 {len(d.get(\"projects\",[]))}개)')"
# 기대 결과: OpsClaw: 정상 (프로젝트 N개)

# 2. Ollama LLM 연결 확인
curl -s http://192.168.0.105:11434/v1/models | python3 -c "
import sys,json
models = json.load(sys.stdin)['data']
print(f'Ollama: 정상 ({len(models)}개 모델)')
for m in models[:5]:
    print(f'  - {m[\"id\"]}')
"
# 기대 결과: gemma3:12b, llama3.1:8b 등 모델 목록

# 3. 원격 서버 접속 확인
for srv in "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv "hostname" 2>/dev/null || echo "$srv: 접속 실패"
done
# 기대 결과: secu, web, siem 출력

# 4. SubAgent 연결 확인
for agent in "http://10.20.30.1:8002" "http://10.20.30.80:8002" "http://10.20.30.100:8002"; do
  echo -n "$agent: "
  curl -s --connect-timeout 3 "$agent/health" 2>/dev/null && echo "" || echo "연결 실패"
done
# 기대 결과: 각 SubAgent의 health 응답

# 5. RL API 확인
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print(f'RL Policy: 정상')
" 2>/dev/null || echo "RL API: 확인 필요"
# 기대 결과: RL Policy: 정상
```

```bash
# 환경 변수 설정 (시험 전체에서 사용)
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
# Manager API 주소
export MGR="http://localhost:8000"
```

---

# 문제 1: Red Agent 구성 — 자동 스캔 + 공격 (25점)

## 1.1 과제 설명

JuiceShop(10.20.30.80:3000)을 대상으로 자율 Red Agent를 구성하라.
Red Agent는 다음을 수행해야 한다:

1. **정찰 (8점)**: 포트 스캔, HTTP 헤더 분석, 기술 스택 식별
2. **취약점 분석 (8점)**: LLM으로 OWASP Top 10 취약점 자동 식별
3. **공격 시나리오 실행 (9점)**: 최소 3가지 취약점 검증 시나리오 실행

## 1.2 채점 기준

| 항목 | 배점 | 채점 기준 |
|------|------|---------|
| 프로젝트 생성 + 스테이지 전환 | 2점 | 올바른 API 호출 |
| 정찰 execute-plan | 4점 | 최소 3개 태스크, 포트/헤더/기술스택 식별 |
| Evidence 수집 | 2점 | evidence/summary 조회 성공 |
| LLM 취약점 분석 | 4점 | Ollama API 호출, OWASP 관련 취약점 식별 |
| 공격 시나리오 LLM 생성 | 4점 | 최소 3가지 시나리오, curl 기반 |
| 공격 시나리오 execute-plan 실행 | 5점 | 시나리오 실행 + Evidence 기록 |
| 공격 결과 LLM 분석 | 4점 | 결과 해석, CVSS 추정, 대응 권고 |

## 1.3 실행 가이드

```bash
# === 문제 1: Red Agent ===

# Step 1: Red Agent 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "final-red-agent-학번",
    "request_text": "기말 Red Agent — JuiceShop 자동 취약점 스캐닝 및 검증",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 RED_PID 변수에 저장한다
```

```bash
export RED_PID="반환된-프로젝트-ID"

# Step 2: 스테이지 전환 (plan → execute)
# plan 스테이지로 전환
curl -s -X POST $MGR/projects/$RED_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지로 전환
curl -s -X POST $MGR/projects/$RED_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Step 3: 정찰 (Reconnaissance) — 최소 3개 태스크
# TODO (학생 작성): execute-plan으로 포트 스캔, HTTP 헤더, 기술 스택 식별
# 힌트:
#   - Task 1: ss -tlnp | grep LISTEN (포트 스캔)
#   - Task 2: curl -sI http://localhost:3000 (HTTP 헤더)
#   - Task 3: curl -s http://localhost:3000 | grep -ioE "(express|angular|node)" (기술 스택)
#   - subagent_url: http://10.20.30.80:8002
```

```bash
# Step 4: Evidence 수집
# TODO (학생 작성): evidence/summary 조회
# curl -s "$MGR/projects/$RED_PID/evidence/summary" -H "X-API-Key: $OPSCLAW_API_KEY"
```

```bash
# Step 5: LLM 취약점 분석
# TODO (학생 작성): Ollama API로 정찰 결과 분석
# 힌트: gemma3:12b 모델, temperature 0.2
# system prompt: "Red Team 분석가. OWASP Top 10 취약점 식별."
```

```bash
# Step 6: 공격 시나리오 생성 + 실행
# TODO (학생 작성): LLM이 생성한 시나리오를 execute-plan으로 실행
# 최소 3가지 취약점 검증 시나리오
# 힌트: SQL Injection, XSS, Access Control 등
```

```bash
# Step 7: 공격 결과 LLM 분석
# TODO (학생 작성): 공격 Evidence를 LLM으로 분석하여 보고서 생성
```

---

# 문제 2: Blue Agent 구성 — 자동 탐지 + 대응 (25점)

## 2.1 과제 설명

3개 서버(secu/web/siem)를 대상으로 자율 Blue Agent를 구성하라.
Blue Agent는 다음을 수행해야 한다:

1. **경보 수집 (8점)**: 3개 서버에서 보안 경보/로그 수집
2. **LLM 분석 (8점)**: 수집된 경보의 위험도 분류 및 오탐 필터링
3. **대응 권고 (9점)**: 분석 결과에 따른 대응 방안 생성

## 2.2 채점 기준

| 항목 | 배점 | 채점 기준 |
|------|------|---------|
| 프로젝트 생성 + 스테이지 전환 | 2점 | 올바른 API 호출 |
| 경보 수집 execute-plan | 4점 | 3개 서버에서 경보 수집 |
| Evidence 조회 | 2점 | evidence/summary 조회 성공 |
| LLM 경보 분석 | 4점 | 위험도 분류 (severity), 분류 (TP/FP) |
| 오탐 필터링 | 4점 | FP 식별 근거, 필터링 로직 |
| 대응 권고 생성 | 5점 | 위험도별 대응 방안, 구체적 명령어 포함 |
| 대응 기록 (dispatch) | 4점 | 분석 결과를 Evidence에 기록 |

## 2.3 실행 가이드

```bash
# === 문제 2: Blue Agent ===

# Step 1: Blue Agent 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "final-blue-agent-학번",
    "request_text": "기말 Blue Agent — 3개 서버 자동 관제 및 경보 분석",
    "master_mode": "external"
  }' | python3 -m json.tool
# 프로젝트 ID를 BLUE_PID 변수에 저장한다
```

```bash
export BLUE_PID="반환된-프로젝트-ID"

# Step 2: 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$BLUE_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$BLUE_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Step 3: 경보 수집 — 3개 서버에서 보안 로그 수집
# TODO (학생 작성): execute-plan으로 3개 서버 경보 수집
# 힌트:
#   - secu: journalctl --since "30 min ago" -p warning (방화벽/IPS 경보)
#   - web: journalctl --since "30 min ago" -p err (웹 서버 에러)
#   - siem: tail -10 /var/ossec/logs/alerts/alerts.json (Wazuh 경보)
```

```bash
# Step 4: LLM 경보 분석 (위험도 분류 + 오탐 필터링)
# TODO (학생 작성): Ollama API로 경보 분석
# 필수 포함:
#   - severity (critical/high/medium/low/info)
#   - classification (true_positive/false_positive/needs_investigation)
#   - 판단 근거
# 힌트: 내부 IP(10.x.x.x) 소량 실패 = FP 가능성 높음
```

```bash
# Step 5: 대응 권고 생성
# TODO (학생 작성): LLM으로 위험도별 대응 방안 생성
# 필수: 구체적인 명령어 포함 (nftables, wazuh, systemctl 등)
```

```bash
# Step 6: 분석 결과를 Evidence에 기록
# TODO (학생 작성): dispatch로 Blue Agent 분석 결과 기록
```

---

# 문제 3: Purple Team 동시 운용 (25점)

## 3.1 과제 설명

Red Agent와 Blue Agent를 **동시에 운용**하여 Purple Team을 구성하라.
30분간 다음을 수행한다:

1. **Red Agent 공격 (10점)**: 5분 간격으로 다른 공격 시나리오 실행 (최소 3라운드)
2. **Blue Agent 탐지 (10점)**: 각 공격 후 경보 수집 + LLM 분석 (최소 3라운드)
3. **효과 측정 (5점)**: 탐지율, MTTD, 오탐률 계산

## 3.2 채점 기준

| 항목 | 배점 | 채점 기준 |
|------|------|---------|
| Purple Team 프로젝트 생성 | 2점 | 올바른 프로젝트 생성 |
| Red 공격 라운드 (최소 3회) | 6점 | 각 라운드별 다른 공격 시나리오 |
| Blue 탐지 라운드 (최소 3회) | 6점 | 공격 후 경보 수집 + LLM 분석 |
| Red-Blue 교대 패턴 | 2점 | 공격→탐지→공격→탐지 순서 |
| 탐지율 계산 | 2점 | 탐지 공격 수 / 전체 공격 수 |
| MTTD 계산 | 2점 | 공격→탐지 시간 차이 |
| 오탐률 계산 | 1점 | FP 식별 비율 |
| PoW 블록 축적 확인 | 2점 | pow/blocks 조회 |
| Experience 축적 확인 | 2점 | evidence/summary 조회 |

## 3.3 실행 가이드

```bash
# === 문제 3: Purple Team ===

# Step 1: Purple Team 프로젝트 생성
curl -s -X POST $MGR/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "final-purple-team-학번",
    "request_text": "기말 Purple Team — Red+Blue 동시 운용, 30분 자율 보안",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PURPLE_PID="반환된-프로젝트-ID"

# Step 2: 스테이지 전환
# plan 스테이지
curl -s -X POST $MGR/projects/$PURPLE_PID/plan -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
# execute 스테이지
curl -s -X POST $MGR/projects/$PURPLE_PID/execute -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# Step 3: Purple Team 라운드 1 — Red 공격 + Blue 탐지
# TODO (학생 작성): execute-plan으로 Red 공격 + Blue 탐지를 한 세트로 실행
# 예시 패턴:
#   Task 1 (RED):  curl -s "http://10.20.30.80:3000/rest/products/search?q=test'" (SQL Injection)
#   Task 2 (BLUE): journalctl --since "2 min ago" -p warning | grep -ciE "injection|error"
#   Task 3 (BLUE): LLM 분석 결과 기록
```

```bash
# Step 4: Purple Team 라운드 2 — 다른 공격 시나리오
# TODO (학생 작성): 라운드 1과 다른 공격 (예: XSS, Directory Traversal)
```

```bash
# Step 5: Purple Team 라운드 3 — 또 다른 공격 시나리오
# TODO (학생 작성): 라운드 1,2와 다른 공격 (예: API Enumeration, Security Headers)
```

```bash
# Step 6: 효과 측정 — 탐지율, MTTD, 오탐률 계산
# Evidence에서 공격/탐지 시간을 추출하여 효과를 측정한다
curl -s "$MGR/projects/$PURPLE_PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /tmp/purple_evidence.json

# TODO (학생 작성): python3 스크립트로 효과 측정
# 필수 계산:
#   - 탐지율 (Detection Rate) = 탐지된 공격 / 전체 공격
#   - MTTD (평균 탐지 시간) = 각 라운드의 (탐지시각 - 공격시각) 평균
#   - 오탐률 (FP Rate) = 오탐 수 / 전체 탐지 수
```

```bash
# Step 7: PoW 블록 축적 확인
# secu SubAgent의 PoW 블록 확인
curl -s "$MGR/pow/blocks?agent_id=http://10.20.30.1:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
print(f'secu PoW 블록: {len(blocks)}개')
"

# web SubAgent의 PoW 블록 확인
curl -s "$MGR/pow/blocks?agent_id=http://10.20.30.80:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
print(f'web PoW 블록: {len(blocks)}개')
"

# siem SubAgent의 PoW 블록 확인
curl -s "$MGR/pow/blocks?agent_id=http://10.20.30.100:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
blocks = data.get('blocks', [])
print(f'siem PoW 블록: {len(blocks)}개')
"
```

---

# 문제 4: Evidence 분석 + RL 수렴 확인 (15점)

## 4.1 과제 설명

Purple Team 운용에서 축적된 데이터를 분석하고, RL 학습을 통해 정책 수렴을 확인하라.

1. **Evidence 분석 (5점)**: 전체 Purple Team Evidence를 LLM으로 종합 분석
2. **RL 학습 (5점)**: rl/train 실행 후 정책 변화 관찰
3. **수렴 확인 (5점)**: 3회 반복 학습 후 Q-value 안정성 확인

## 4.2 채점 기준

| 항목 | 배점 | 채점 기준 |
|------|------|---------|
| Evidence 종합 분석 (LLM) | 3점 | 전체 Evidence를 LLM으로 분석, 주요 발견사항 도출 |
| PoW 교차 검증 | 2점 | 3개 SubAgent pow/verify 실행 |
| RL 학습 실행 | 2점 | rl/train 실행 성공 |
| RL 추천 조회 | 2점 | 3개 SubAgent rl/recommend 조회 |
| 반복 학습 + 수렴 확인 | 3점 | 3회 학습, Q-value 변화 관찰 |
| 리더보드 확인 | 1점 | pow/leaderboard 조회 |
| Replay 확인 | 2점 | 프로젝트 replay 조회 |

## 4.3 실행 가이드

```bash
# === 문제 4: Evidence 분석 + RL ===

# Step 1: Purple Team Evidence 종합 분석
curl -s "$MGR/projects/$PURPLE_PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /tmp/final_evidence.json

# TODO (학생 작성): LLM으로 종합 분석
# 분석 항목:
#   - 전체 태스크 성공/실패 비율
#   - Red Agent 공격 성공률
#   - Blue Agent 탐지율
#   - 주요 발견사항 TOP 3
#   - 개선 권고사항
```

```bash
# Step 2: PoW 교차 검증 — 3개 SubAgent 체인 무결성 확인
# secu PoW 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.1:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# web PoW 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.80:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# siem PoW 검증
curl -s "$MGR/pow/verify?agent_id=http://10.20.30.100:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Step 3: RL 학습 — 3회 반복으로 수렴 확인
# 1차 학습 실행
echo "=== RL 학습 1차 ==="
curl -s -X POST "$MGR/rl/train" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# 2차 학습 실행
echo "=== RL 학습 2차 ==="
curl -s -X POST "$MGR/rl/train" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# 3차 학습 실행
echo "=== RL 학습 3차 ==="
curl -s -X POST "$MGR/rl/train" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Step 4: RL 추천 조회 — 학습 후 정책 변화 확인
# secu 추천 확인
echo "=== secu 추천 ==="
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.1:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# web 추천 확인
echo "=== web 추천 ==="
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.80:8002&risk_level=medium" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# siem 추천 확인
echo "=== siem 추천 ==="
curl -s "$MGR/rl/recommend?agent_id=http://10.20.30.100:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Step 5: 리더보드 + Replay 확인
# PoW 리더보드 — SubAgent별 기여도 순위
curl -s "$MGR/pow/leaderboard" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# Purple Team 프로젝트 Replay — 실행 타임라인
curl -s "$MGR/projects/$PURPLE_PID/replay" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Step 6: 전체 RL 정책 테이블 출력 및 수렴 분석
curl -s "$MGR/rl/policy" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# 정책 테이블 전체 출력
print('=== 최종 RL 정책 ===')
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
"
# TODO (학생 작성): Q-value의 안정성을 분석하여 수렴 여부를 판단하라
```

---

# 문제 5: Completion Report 작성 (10점)

## 5.1 과제 설명

전체 시험 과정을 종합하여 OpsClaw completion-report를 작성하라.

## 5.2 채점 기준

| 항목 | 배점 | 채점 기준 |
|------|------|---------|
| summary 작성 | 2점 | 전체 시험 요약 (1-2문장) |
| outcome 선택 | 1점 | success/partial/failure 중 적절한 선택 |
| work_details 작성 | 5점 | 최소 8항목, 구체적인 수치/결과 포함 |
| 구조화 수준 | 2점 | 논리적 순서, 항목별 명확한 구분 |

## 5.3 실행 가이드

```bash
# === 문제 5: Completion Report ===

# Red Agent 프로젝트 완료 보고서
curl -s -X POST $MGR/projects/$RED_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "(학생 작성) Red Agent 자동 스캐닝/공격 완료 요약",
    "outcome": "success",
    "work_details": [
      "(학생 작성) 정찰 결과",
      "(학생 작성) 취약점 분석 결과",
      "(학생 작성) 공격 시나리오 실행 결과"
    ]
  }' | python3 -m json.tool
# Red Agent 프로젝트의 최종 보고서를 제출한다
```

```bash
# Blue Agent 프로젝트 완료 보고서
curl -s -X POST $MGR/projects/$BLUE_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "(학생 작성) Blue Agent 자동 관제/분석 완료 요약",
    "outcome": "success",
    "work_details": [
      "(학생 작성) 경보 수집 결과",
      "(학생 작성) LLM 분석 결과",
      "(학생 작성) 대응 권고 사항"
    ]
  }' | python3 -m json.tool
# Blue Agent 프로젝트의 최종 보고서를 제출한다
```

```bash
# Purple Team 종합 완료 보고서 (가장 중요)
curl -s -X POST $MGR/projects/$PURPLE_PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "(학생 작성) Purple Team 자율 보안 운용 종합 보고",
    "outcome": "success",
    "work_details": [
      "(학생 작성) [RED] 공격 시나리오 N건 실행, 성공률 X%",
      "(학생 작성) [BLUE] 경보 수집 N건, 분석 완료",
      "(학생 작성) [DETECT] 탐지율 X%, MTTD X분, 오탐률 X%",
      "(학생 작성) [POW] 3개 SubAgent PoW 검증 결과",
      "(학생 작성) [RL] Q-learning 3회 학습, 수렴 상태",
      "(학생 작성) [RL] 최적 정책: secu=X, web=X, siem=X",
      "(학생 작성) [FINDING] 주요 발견사항 TOP 3",
      "(학생 작성) [RECOMMEND] 보안 개선 권고사항"
    ]
  }' | python3 -m json.tool
# Purple Team 종합 보고서 — 전체 시험의 최종 제출물
```

---

## 채점 총괄표

| 문제 | 배점 | 핵심 평가 항목 |
|------|------|--------------|
| 문제 1: Red Agent | 25점 | 정찰 + 취약점 분석 + 공격 시나리오 실행 |
| 문제 2: Blue Agent | 25점 | 경보 수집 + LLM 분석 + 오탐 필터링 + 대응 |
| 문제 3: Purple Team | 25점 | Red+Blue 동시 운용 + 효과 측정 |
| 문제 4: Evidence + RL | 15점 | 종합 분석 + RL 학습 + 수렴 확인 |
| 문제 5: Report | 10점 | completion-report 구조화 + 수치 포함 |
| **합계** | **100점** | |

## 감점 기준

| 항목 | 감점 |
|------|------|
| 프로젝트 이름에 학번 미포함 | -2점 |
| API Key 누락 | -3점 |
| 스테이지 전환 누락 (plan → execute) | -2점 |
| LLM 호출 시 temperature > 0.5 | -1점 |
| 파괴적 명령 실행 시도 (rm -rf 등) | -10점 |
| scope 밖 공격 시도 (외부 IP) | -10점 |

---

## 퀴즈 (보너스, 5점)

본 시험에는 별도의 퀴즈가 없다. 위 5문제의 실기 평가로 100점 만점을 채점한다.

다만, 다음 5문제를 맞추면 보너스 점수를 부여한다 (최대 5점, 총점 105점 가능).

**보너스 1.** Purple Team에서 Red가 공격하고 Blue가 탐지하는 사이클의 목적은?

- A) Red의 공격 성공률을 높이기 위해
- B) Blue의 탐지 능력을 테스트하고 전체 보안 수준을 개선하기 위해
- C) Manager API의 성능을 측정하기 위해
- D) PoW 블록을 최대한 많이 생성하기 위해

**정답: B) Blue의 탐지 능력을 테스트하고 전체 보안 수준을 개선하기 위해**

---

**보너스 2.** RL 학습에서 3회 반복 후 Q-value 변화가 0.01 미만이면?

- A) 학습이 실패했다
- B) 데이터가 부족하다
- C) 정책이 수렴(convergence)에 근접했다
- D) SubAgent가 종료되었다

**정답: C) 정책이 수렴(convergence)에 근접했다**

---

**보너스 3.** OpsClaw에서 completion-report의 work_details에 포함해야 하는 것은?

- A) SubAgent의 소스 코드
- B) 구체적인 실행 결과와 수치
- C) 다른 학생의 결과 비교
- D) Manager API의 내부 로그

**정답: B) 구체적인 실행 결과와 수치**

---

**보너스 4.** 4-Layer Memory에서 프로젝트를 넘어 영구 보존되며 FTS 검색이 가능한 계층은?

- A) Evidence
- B) Task Memory
- C) Experience
- D) Retrieval

**정답: C) Experience**

---

**보너스 5.** PoW 교차 검증에서 `valid: true, orphans: 2`의 의미는?

- A) 체인이 손상되었고 2개 블록이 변조되었다
- B) 메인 체인은 무결하지만 2개의 분기 블록이 존재한다
- C) 2개의 SubAgent가 검증에 실패했다
- D) 체인에 2개의 블록만 존재한다

**정답: B) 메인 체인은 무결하지만 2개의 분기 블록이 존재한다**

---

## 수고하셨습니다

이로써 "Course 9: 자율보안시스템" 전 과정이 완료되었습니다.
OpsClaw를 활용한 자율 보안 에이전트의 설계, 구현, 운용, 학습의 전체 사이클을 경험하셨습니다.
