# Week 13: 퍼플팀 — Red+Blue 협업, ATT&CK Gap 분석, 보안 성숙도

## 학습 목표
- 퍼플팀(Purple Team)의 개념과 Red/Blue 팀 협업 방법론을 이해한다
- ATT&CK 기반 탐지 Gap 분석을 수행하여 조직의 보안 사각지대를 식별할 수 있다
- 공격 시뮬레이션 결과를 바탕으로 탐지 규칙을 개선하고 검증할 수 있다
- 보안 성숙도 모델(CMM)을 적용하여 조직의 현재 수준을 평가할 수 있다
- OpsClaw의 AI Red/Blue 에이전트를 퍼플팀 워크플로에 통합할 수 있다
- ATT&CK Navigator를 활용하여 탐지 커버리지를 시각화하고 개선 계획을 수립할 수 있다

## 전제 조건
- Week 11 레드팀 운영 + Week 12 블루팀 운영 이수 완료
- MITRE ATT&CK 프레임워크 이해 (전술, 기법, 절차)
- Wazuh 규칙 작성 경험
- OpsClaw execute-plan, evidence API 사용 경험

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 퍼플팀 Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh 4.11.2) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: 퍼플팀 방법론과 ATT&CK Gap 분석 | 강의 |
| 0:40-1:20 | Part 2: 공격 시뮬레이션과 탐지 규칙 개선 사이클 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: 자동화된 퍼플팀 — OpsClaw AI 에이전트 활용 | 실습 |
| 2:10-2:50 | Part 4: 보안 성숙도 평가와 개선 로드맵 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 퍼플팀 최종 리뷰 + 토론 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **퍼플팀** | Purple Team | Red+Blue 팀 협업으로 방어력을 체계적으로 향상 | 공격과 방어의 합동 훈련 |
| **Gap 분석** | Gap Analysis | 현재 탐지 역량과 목표 간의 차이 식별 | 건강 검진 |
| **탐지 커버리지** | Detection Coverage | ATT&CK 기법 중 탐지 가능한 비율 | 레이더 탐지 범위 |
| **규칙 튜닝** | Rule Tuning | 오탐 감소/미탐 개선을 위한 규칙 조정 | 레이더 감도 조정 |
| **보안 성숙도** | Security Maturity | 조직의 보안 프로세스 완성도 수준 | 성장 단계 |
| **CMM** | Capability Maturity Model | 역량 성숙도 모델 (1-5단계) | 학년 |
| **DETT&CT** | Detection & TTP Characterization | ATT&CK 기반 탐지 능력 평가 프레임워크 | 보안 체력 측정표 |
| **Atomic Test** | Atomic Red Team Test | 개별 ATT&CK 기법을 단위 테스트하는 것 | 개별 기술 시험 |
| **탐지 로직** | Detection Logic | 특정 공격을 탐지하는 규칙/알고리즘 | 비밀번호 검사 규칙 |
| **오탐 튜닝** | False Positive Tuning | 정상 활동 오탐을 제거하는 규칙 조정 | 민감도 조정 |
| **킬 체인 인터셉트** | Kill Chain Intercept | 킬체인의 특정 단계에서 공격을 차단 | 미사일 요격 지점 |
| **컨트롤 매핑** | Control Mapping | 보안 통제를 ATT&CK 기법에 대응시키는 것 | 방패와 무기 짝짓기 |

---

# Part 1: 퍼플팀 방법론과 ATT&CK Gap 분석 (40분)

## 1.1 퍼플팀의 정의와 가치

퍼플팀은 **Red Team(공격)과 Blue Team(방어)이 정보를 공유하며 협력**하여 조직의 방어력을 체계적으로 향상하는 방법론이다.

### Red/Blue/Purple 비교

| 항목 | Red Team | Blue Team | Purple Team |
|------|----------|-----------|-------------|
| **목표** | 방어 능력 평가 | 공격 탐지/차단 | 탐지 Gap 개선 |
| **정보 공유** | 비공유 (블라인드) | 자체 데이터만 | **완전 공유** |
| **시점** | 사후 보고 | 실시간 모니터링 | **실시간 협업** |
| **산출물** | 침투 보고서 | 탐지/대응 기록 | **개선된 탐지 규칙** |
| **효과** | 약점 발견 | 약점 방어 | **약점 발견+방어 동시** |

### 퍼플팀 워크플로

```
+--------------------------------------------------+
|              퍼플팀 워크플로                        |
|                                                    |
|  1. 계획                                           |
|     Red + Blue가 함께 테스트할 ATT&CK 기법 선정    |
|                    |                               |
|                    ▼                               |
|  2. 공격 실행                                       |
|     Red가 선정된 기법을 실행 (Blue에게 사전 통보)   |
|                    |                               |
|                    ▼                               |
|  3. 탐지 확인                                       |
|     Blue가 탐지 여부 확인 + 로그/알림 분석          |
|                    |                               |
|           +--------+--------+                      |
|           ▼                 ▼                      |
|  4a. 탐지 성공           4b. 탐지 실패             |
|     규칙 문서화               Gap 식별              |
|     다음 기법으로             규칙 개발/개선         |
|                              재테스트               |
|           |                 |                      |
|           +--------+--------+                      |
|                    ▼                               |
|  5. 문서화 + Gap 리포트                             |
|     ATT&CK Navigator 업데이트                       |
|     탐지 커버리지 변화 측정                          |
+--------------------------------------------------+
```

## 1.2 ATT&CK Gap 분석 방법론

Gap 분석은 조직의 **현재 탐지 역량과 목표 역량 사이의 차이**를 체계적으로 식별하는 과정이다.

### Gap 분석 프로세스

| 단계 | 활동 | 도구 | 산출물 |
|------|------|------|--------|
| **1. 범위 설정** | 평가할 ATT&CK 전술/기법 선정 | ATT&CK Navigator | 평가 범위 문서 |
| **2. 현황 조사** | 현재 탐지 규칙/도구 인벤토리 | Wazuh, Suricata, EDR | 현재 커버리지 맵 |
| **3. 매핑** | 현재 탐지를 ATT&CK 기법에 매핑 | Navigator 레이어 | 커버리지 히트맵 |
| **4. 테스트** | 각 기법별 공격 시뮬레이션 | Atomic Red Team, OpsClaw | 테스트 결과 |
| **5. Gap 식별** | 미탐지 기법 목록화 | Navigator 비교 | Gap 리포트 |
| **6. 개선 계획** | 우선순위 정하여 규칙 개발 | 위험도 × 가능성 | 개선 로드맵 |

### 탐지 수준 분류 (DL: Detection Level)

| 수준 | 설명 | Navigator 색상 | 예시 |
|------|------|---------------|------|
| **DL0** | 탐지 불가 | 빨강 | 알려지지 않은 기법 |
| **DL1** | 로그만 수집 | 주황 | 로그는 있지만 규칙 없음 |
| **DL2** | 기본 규칙 존재 | 노랑 | 일반적 시그니처 매칭 |
| **DL3** | 정교한 규칙 | 연두 | 상관 분석, 행위 기반 |
| **DL4** | 자동 대응 포함 | 초록 | SOAR 플레이북 연동 |

## 1.3 실습 환경의 ATT&CK 커버리지 현황

현재 실습 환경(OpsClaw 인프라)의 탐지 역량을 ATT&CK 전술별로 분석한다.

### 현재 탐지 역량 평가

| ATT&CK 전술 | 탐지 도구 | 현재 DL | Gap |
|-------------|----------|---------|-----|
| TA0043 정찰 | Suricata (포트스캔 탐지) | DL2 | 은밀 스캔 미탐지 |
| TA0001 초기접근 | Wazuh (웹 공격 규칙) | DL2 | SQLi 변형 미탐지 |
| TA0002 실행 | Wazuh (프로세스 모니터링) | DL1 | 명령 실행 규칙 부재 |
| TA0003 지속성 | Wazuh (파일 무결성) | DL2 | 서비스 등록 미탐지 |
| TA0004 권한상승 | Wazuh (sudo 로그) | DL1 | 커널 익스플로잇 미탐지 |
| TA0005 방어회피 | Suricata (시그니처) | DL1 | 인코딩 우회 미탐지 |
| TA0006 자격증명 | Wazuh (인증 실패) | DL2 | 패스워드 스프레이 미탐지 |
| TA0007 발견 | Wazuh (기본 규칙) | DL1 | 내부 탐색 미탐지 |
| TA0008 측면이동 | - | DL0 | **완전 사각지대** |
| TA0009 수집 | - | DL0 | **완전 사각지대** |
| TA0011 C2 | Suricata (알려진 C2) | DL1 | DNS 터널 미탐지 |
| TA0010 유출 | - | DL0 | **완전 사각지대** |
| TA0040 영향 | Wazuh (파일 삭제) | DL1 | 랜섬웨어 미탐지 |

### 우선 개선 대상 (Gap이 큰 순)

| 우선순위 | 전술 | 현재 DL | 목표 DL | 개선 방안 |
|---------|------|---------|---------|----------|
| 1 | TA0008 측면이동 | DL0 | DL2 | SSH 횡이동 규칙, 네트워크 세그먼트 모니터링 |
| 2 | TA0010 유출 | DL0 | DL2 | 대용량 전송 탐지, DNS 이상 탐지 |
| 3 | TA0009 수집 | DL0 | DL1 | 파일 접근 모니터링, 클립보드 감시 |
| 4 | TA0001 초기접근 | DL2 | DL3 | SQLi 변형 규칙, WAF 강화 |
| 5 | TA0005 방어회피 | DL1 | DL2 | 인코딩 우회 탐지, 행위 분석 |

---

# Part 2: 공격 시뮬레이션과 탐지 규칙 개선 사이클 (40분)

## 2.1 Atomic Red Team 접근법

Atomic Red Team은 **개별 ATT&CK 기법을 독립적으로 테스트**하는 방법론이다. 각 테스트(Atomic Test)가 하나의 기법만 검증한다.

### Atomic Test 구조

| 요소 | 설명 | 예시 |
|------|------|------|
| **기법 ID** | 테스트할 ATT&CK 기법 | T1190 (Exploit Public-Facing Application) |
| **사전 조건** | 테스트에 필요한 환경 | 대상 서버 접근 가능, curl 설치 |
| **실행 명령** | 공격 시뮬레이션 명령 | `curl "http://target/search?q=' OR 1=1--"` |
| **탐지 기대** | Blue Team이 탐지해야 할 것 | Wazuh level 12 알림, Apache 로그 패턴 |
| **정리** | 테스트 후 환경 복원 | 없음 (비파괴적 테스트) |

### OpsClaw로 Atomic Test 실행

```
OpsClaw execute-plan 1개 task = 1개 Atomic Test
  +- instruction_prompt: 공격 명령
  +- risk_level: 기법 위험도에 따라
  +- evidence: 자동 기록 → 결과 분석
```

## 2.2 탐지 규칙 개선 사이클

퍼플팀의 핵심은 **"공격→탐지확인→규칙개선→재테스트"** 의 반복 사이클이다.

```
공격 실행 --▶ 탐지 확인 --▶ 결과 분류
                              |
                    +---------+---------+
                    ▼                   ▼
               탐지 성공            탐지 실패
               기록/문서화          원인 분석
                    |                   |
                    |           +-------+-------+
                    |           ▼               ▼
                    |      규칙 추가         규칙 수정
                    |      (새 시그니처)     (임계값 조정)
                    |           |               |
                    |           +-------+-------+
                    |                   ▼
                    |              재테스트
                    |                   |
                    +-------------------+
                              |
                              ▼
                    다음 기법으로 진행
```

---

# Part 3: 자동화된 퍼플팀 — OpsClaw AI 에이전트 활용 (40분)

## 실습 3.1: 퍼플팀 프로젝트 셋업 및 ATT&CK 기법 선정

> **실습 목적**: 퍼플팀 작전의 첫 단계로 테스트할 ATT&CK 기법을 선정하고 OpsClaw 프로젝트를 구성한다.
>
> **배우는 것**: 퍼플팀 작전의 체계적 시작 절차, ATT&CK 기법 선정 기준, Red/Blue 역할 분배 방법을 이해한다.
>
> **결과 해석**: 프로젝트가 정상 생성되고 Stage 전환이 완료되면 퍼플팀 시뮬레이션을 시작할 수 있다.
>
> **실전 활용**: 실무에서 퍼플팀은 분기별로 5-10개 ATT&CK 기법을 선정하여 집중 테스트한다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 퍼플팀 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week13-purple-team",
    "request_text": "퍼플팀 ATT&CK Gap 분석: T1190(SQLi), T1110(BruteForce), T1059(명령실행), T1083(디렉토리탐색), T1071(C2 프로토콜) 5개 기법 테스트",
    "master_mode": "external"
  }' | python3 -m json.tool
# PROJECT_ID 메모
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

> **명령어 해설**: 5개의 ATT&CK 기법(T1190, T1110, T1059, T1083, T1071)을 선정하여 퍼플팀 테스트 범위로 설정한다. 각 기법은 높은 발생 빈도와 실습 환경에서의 테스트 가능성을 기준으로 선정하였다.
>
> **트러블슈팅**: Stage 전환 실패 시 프로젝트 상태를 `GET /projects/{id}`로 확인한다.

## 실습 3.2: Atomic Test — 5개 기법 순차 시뮬레이션

> **실습 목적**: 선정된 5개 ATT&CK 기법을 순차적으로 실행(Red)하고, 각 기법에 대한 탐지 여부를 확인(Blue)한다.
>
> **배우는 것**: Atomic Test의 실행-탐지-평가 사이클, OpsClaw execute-plan으로 다수 기법을 효율적으로 테스트하는 방법, 탐지 결과의 DL 수준 판정을 이해한다.
>
> **결과 해석**: 각 기법의 탐지 성공/실패를 기록하여 Gap 매트릭스를 작성한다. DL0(미탐지)인 기법이 개선 대상이다.
>
> **실전 활용**: 이 순환은 실제 퍼플팀 운영의 일일 워크플로이다. 자동화하면 지속적 보안 검증(Continuous Validation)이 가능하다.

```bash
# Red Phase: 5개 ATT&CK 기법 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [RED] T1190: Exploit Public-Facing App (SQLi) ===\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=%27%20OR%201=1--\" 2>/dev/null | head -3; echo \"결과: SQLi 페이로드 전송 완료\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [RED] T1110: Brute Force (로그인 반복 시도) ===\"; for i in $(seq 1 5); do curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"admin@juice-sh.op\\\",\\\"password\\\":\\\"wrong$i\\\"}\" 2>/dev/null | head -1; done; echo \"결과: 5회 로그인 실패 생성\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== [RED] T1059: Command-Line Interface ===\"; echo \"시뮬레이션: 원격 명령 실행 시도\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"id; whoami; uname -a\" 2>/dev/null; echo \"결과: 원격 명령 실행 완료\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== [RED] T1083: File and Directory Discovery ===\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"ls -la /etc/passwd /etc/shadow /var/www/ 2>/dev/null; find /tmp -maxdepth 1 -type f 2>/dev/null | head -10\"; echo \"결과: 파일/디렉토리 탐색 완료\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== [RED] T1071: Application Layer Protocol (HTTP C2 시뮬레이션) ===\"; for i in $(seq 1 3); do curl -s -o /dev/null -w \"Beacon $i: %{http_code}\" http://10.20.30.80:3000/api/ 2>/dev/null; echo; sleep 1; done; echo \"결과: HTTP 비콘 3회 전송 (C2 시뮬레이션)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

```bash
# Blue Phase: 각 기법에 대한 탐지 확인
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [BLUE] T1190 탐지 확인 ===\"; echo \"[Suricata]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -i sql || echo MISS\"; echo \"[Wazuh]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -30 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep -i sql | tail -3 || echo MISS\"; echo \"[Apache]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -20 /var/log/apache2/access.log 2>/dev/null | grep -i \\\"OR 1=1\\\" | tail -3 || echo MISS\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== [BLUE] T1110 탐지 확인 ===\"; echo \"[Wazuh 인증 실패]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -30 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep -iE \\\"authentication|login|failed\\\" | tail -3 || echo MISS\"; echo \"[Apache 401/403]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -20 /var/log/apache2/access.log 2>/dev/null | grep -E \\\"401|403\\\" | tail -3 || echo MISS\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== [BLUE] T1059+T1083+T1071 탐지 확인 ===\"; echo \"[Wazuh 명령 실행]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -50 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep -iE \\\"command|exec|shell\\\" | tail -3 || echo MISS\"; echo \"[Wazuh 파일 접근]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"tail -50 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep -iE \\\"file|directory|passwd\\\" | tail -3 || echo MISS\"; echo \"[Suricata C2 패턴]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -iE \\\"c2|beacon|callback\\\" || echo MISS\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - Red Phase: 5개 ATT&CK 기법을 순서대로 실행. 각 task가 하나의 Atomic Test에 대응한다
> - Blue Phase: 각 기법에 대해 Suricata IPS, Wazuh SIEM, Apache 로그 세 곳을 교차 확인한다
> - "MISS" 출력은 해당 도구에서 탐지하지 못했음을 의미한다 (Gap)
>
> **트러블슈팅**: 모든 탐지가 MISS이면 Wazuh/Suricata가 비활성 상태이거나 에이전트가 설치되지 않은 것이다. 서비스 상태를 확인한다.

## 실습 3.3: 탐지 규칙 개선 및 재테스트

> **실습 목적**: Gap으로 식별된 기법에 대해 탐지 규칙을 개선하고 재테스트하여 탐지 수준을 향상시킨다.
>
> **배우는 것**: 탐지 규칙 개선의 구체적 절차, 규칙 테스트 방법, 개선 전후 비교 분석을 이해한다.
>
> **결과 해석**: 규칙 개선 후 이전에 MISS였던 기법이 탐지되면 Gap이 해소된 것이다. DL 수준이 상승해야 한다.
>
> **실전 활용**: 이 개선 사이클을 주기적으로 반복하면 조직의 탐지 커버리지가 지속적으로 향상된다.

```bash
# 규칙 개선 제안 생성 (LLM 분석 활용)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -s -X POST http://localhost:8002/a2a/analyze -H \"Content-Type: application/json\" -d \"{\\\"context\\\": \\\"퍼플팀 테스트 결과: T1190(SQLi)은 Apache 로그에만 기록, Wazuh/Suricata 미탐지. T1110(BruteForce)은 Wazuh 기본 규칙으로 부분 탐지. T1059(명령실행), T1083(파일탐색), T1071(C2)은 전부 미탐지(DL0).\\\", \\\"question\\\": \\\"각 미탐지 기법에 대해 1) Wazuh 규칙 XML 2) Suricata 규칙 3) 탐지 로직 설명을 제안하라.\\\"}\" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -50",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**: `/a2a/analyze`를 통해 LLM에게 Gap 분석 결과를 전달하고, 각 미탐지 기법에 대한 규칙 개선안을 생성한다. LLM은 보안 지식을 활용하여 구체적인 Wazuh XML 규칙과 Suricata 규칙을 제안한다.
>
> **트러블슈팅**: LLM 응답이 일반적이면 context에 더 구체적인 로그 형식과 환경 정보를 추가한다.

```bash
# 재테스트: 규칙 개선 후 동일 기법 재실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== [RETEST] T1190 재테스트 ===\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=%27%20UNION%20SELECT%201--\" 2>/dev/null | head -3; echo \"---\"; echo \"[탐지 확인]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"tail -5 /var/log/apache2/access.log 2>/dev/null | grep -i union || echo 로그 확인 필요\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== Gap 분석 종합 ===\"; echo \"기법          | 1차 DL | 2차 DL | 변화\"; echo \"--------------┼--------┼--------┼-----\"; echo \"T1190 SQLi    |  DL1   |  DL2   | 개선\"; echo \"T1110 BruteF  |  DL2   |  DL2   | 유지\"; echo \"T1059 CmdExec |  DL0   |  DL1   | 개선\"; echo \"T1083 FileDis |  DL0   |  DL0   | 미개선\"; echo \"T1071 C2 HTTP |  DL0   |  DL0   | 미개선\"; echo \"--------------┼--------┼--------┼-----\"; echo \"탐지 커버리지: 2/5 → 3/5 (40% → 60%)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**: 재테스트에서 동일 공격을 실행하고 탐지 여부를 재확인한다. Gap 종합표에서 DL 변화를 추적한다. 탐지 커버리지가 40%에서 60%로 향상되면 퍼플팀 활동의 효과가 입증된 것이다.
>
> **트러블슈팅**: 규칙을 실제로 추가하지 않았으므로 DL 변화는 이론적 기대값이다. 실제 규칙 추가 후 재테스트해야 정확한 결과를 얻는다.

---

# Part 4: 보안 성숙도 평가와 개선 로드맵 (40분)

## 4.1 보안 성숙도 모델 (CMM)

| 수준 | 이름 | 특징 | ATT&CK 커버리지 |
|------|------|------|----------------|
| **Level 1** | 초기 (Initial) | 임시적, 비체계적 대응 | < 20% |
| **Level 2** | 반복 (Repeatable) | 기본 프로세스 존재, 수동 | 20-40% |
| **Level 3** | 정의 (Defined) | 표준화된 프로세스, 문서화 | 40-60% |
| **Level 4** | 관리 (Managed) | 메트릭 기반 관리, 부분 자동화 | 60-80% |
| **Level 5** | 최적화 (Optimizing) | 지속적 개선, 완전 자동화 | > 80% |

## 실습 4.2: 실습 환경 보안 성숙도 평가

> **실습 목적**: 실습 환경의 현재 보안 성숙도를 CMM 모델로 평가하고 개선 로드맵을 수립한다.
>
> **배우는 것**: 보안 성숙도 평가 방법, 다차원 평가 기준(기술/프로세스/인력), 개선 로드맵 수립 방법을 이해한다.
>
> **결과 해석**: 현재 수준이 Level 2-3이면 업계 평균 수준이다. 각 차원별 수준 차이를 파악하여 약한 영역을 우선 개선한다.
>
> **실전 활용**: 보안 성숙도 평가는 CISO의 핵심 보고 도구이다. 경영진에게 투자 근거를 제공한다.

```bash
# 성숙도 평가 데이터 수집
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== 보안 성숙도 평가: 기술 차원 ===\"; echo \"[SIEM 상태]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"systemctl is-active wazuh-manager 2>/dev/null || echo inactive\"; echo \"[IPS 상태]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"systemctl is-active suricata 2>/dev/null || echo inactive\"; echo \"[방화벽 규칙 수]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"nft list ruleset 2>/dev/null | grep -c rule || echo 0\"; echo \"[커스텀 탐지 규칙 수]\"; sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \"cat /var/ossec/etc/rules/local_rules.xml 2>/dev/null | grep -c '<rule' || echo 0\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== 보안 성숙도 평가: 자동화 차원 ===\"; echo \"[OpsClaw 프로젝트 수]\"; curl -s http://localhost:8000/projects -H \"X-API-Key: $OPSCLAW_API_KEY\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"총 프로젝트: {len(d) if isinstance(d,list) else d.get(\\x27count\\x27,\\x27?\\x27)}\\\")\" 2>/dev/null; echo \"[PoW 블록 수]\"; curl -s \"http://localhost:8000/pow/blocks\" -H \"X-API-Key: $OPSCLAW_API_KEY\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"총 블록: {len(d) if isinstance(d,list) else \\x27?\\x27}\\\")\" 2>/dev/null; echo \"[RL 정책 상태]\"; curl -s http://localhost:8000/rl/policy -H \"X-API-Key: $OPSCLAW_API_KEY\" 2>/dev/null | head -3",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== 성숙도 종합 평가 ===\"; echo; echo \"차원          | 현재 수준  | 목표 수준  | Gap\"; echo \"--------------┼----------┼----------┼------\"; echo \"탐지 기술      | Level 2   | Level 3   | 규칙 강화\"; echo \"자동화 대응    | Level 2   | Level 4   | SOAR 구축\"; echo \"프로세스       | Level 2   | Level 3   | IR 절차 문서화\"; echo \"인력/교육      | Level 1   | Level 3   | 교육 프로그램\"; echo \"증적/감사      | Level 3   | Level 4   | PoW 활용\"; echo \"--------------┼----------┼----------┼------\"; echo \"종합           | Level 2   | Level 3+  | 6개월 목표\"; echo; echo \"우선 개선: 자동화 대응(SOAR), 인력 교육\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: SIEM, IPS, 방화벽, 커스텀 규칙의 현재 상태를 수집하여 기술 차원을 평가
> - task 2: OpsClaw 프로젝트, PoW 블록, RL 정책을 통해 자동화 수준을 평가
> - task 3: 5개 차원(기술, 자동화, 프로세스, 인력, 증적)의 종합 성숙도 매트릭스를 생성
>
> **트러블슈팅**: 서비스가 inactive 상태이면 성숙도 평가에서 해당 항목을 "미구성"으로 기록한다.

```bash
# 퍼플팀 완료 보고서 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "퍼플팀 ATT&CK Gap 분석 완료. 5개 기법 테스트, 탐지 커버리지 40%→60% 향상.",
    "outcome": "success",
    "work_details": [
      "5개 ATT&CK 기법(T1190,T1110,T1059,T1083,T1071) Atomic Test 실행",
      "현재 탐지 커버리지: 2/5 기법 (40%)",
      "규칙 개선 후 목표: 3/5 기법 (60%)",
      "미탐지 Gap: T1083(파일탐색), T1071(C2) — 추가 규칙 개발 필요",
      "보안 성숙도: Level 2 (반복) → Level 3 (정의) 목표",
      "개선 로드맵: SOAR 자동화, 커스텀 규칙 세트 확충, 교육 강화"
    ]
  }' | python3 -m json.tool
```

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] 퍼플팀의 정의와 Red/Blue 팀과의 차이를 설명할 수 있는가?
- [ ] ATT&CK Gap 분석의 6단계 프로세스를 나열할 수 있는가?
- [ ] 탐지 수준(DL0-DL4)의 정의와 각 수준의 특징을 설명할 수 있는가?
- [ ] Atomic Red Team 방식으로 개별 ATT&CK 기법을 테스트할 수 있는가?
- [ ] "공격→탐지확인→규칙개선→재테스트" 사이클을 실행할 수 있는가?
- [ ] OpsClaw를 활용하여 퍼플팀 워크플로를 자동화할 수 있는가?
- [ ] CMM 5단계 보안 성숙도 모델의 각 수준을 설명할 수 있는가?
- [ ] 탐지 커버리지를 정량적으로 측정하고 개선 효과를 보여줄 수 있는가?
- [ ] LLM을 활용하여 탐지 규칙 개선안을 생성할 수 있는가?
- [ ] 보안 성숙도 개선 로드맵을 수립할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** 퍼플팀과 레드팀의 가장 큰 차이점은?
- (a) 사용 도구  (b) 비용  (c) **Red/Blue 간 정보 공유 및 실시간 협업 여부**  (d) 보고서 형식

**Q2.** ATT&CK Gap 분석에서 DL0의 의미는?
- (a) 완벽한 탐지  (b) 부분 탐지  (c) **전혀 탐지 불가 (사각지대)**  (d) 자동 대응 포함

**Q3.** Atomic Red Team 방식의 핵심 원칙은?
- (a) 전체 킬체인을 한 번에 테스트  (b) **개별 ATT&CK 기법을 독립적으로 단위 테스트**  (c) 랜덤 공격  (d) Blue팀 비인지

**Q4.** 퍼플팀 워크플로에서 탐지 실패 시 다음 단계는?
- (a) 작전 종료  (b) 다른 기법으로 이동  (c) **원인 분석 후 규칙 개발/개선 및 재테스트**  (d) 보고서 작성

**Q5.** CMM Level 3 "정의(Defined)"의 특징은?
- (a) 임시적 대응  (b) **표준화된 프로세스 존재, 문서화**  (c) 완전 자동화  (d) 메트릭 기반 관리

**Q6.** 실습 환경에서 탐지 커버리지가 가장 낮은 ATT&CK 전술은?
- (a) TA0043 정찰  (b) TA0001 초기접근  (c) **TA0008 측면이동 (DL0)**  (d) TA0003 지속성

**Q7.** 탐지 규칙 개선 사이클의 올바른 순서는?
- (a) 규칙개선→공격→탐지→문서화  (b) **공격→탐지확인→규칙개선→재테스트**  (c) 문서화→공격→탐지→보고  (d) 탐지→공격→규칙→종료

**Q8.** 보안 성숙도 평가의 5개 차원에 포함되지 않는 것은?
- (a) 탐지 기술  (b) 자동화 대응  (c) **매출 규모**  (d) 인력/교육

**Q9.** OpsClaw가 퍼플팀에서 수행하는 핵심 역할은?
- (a) 로그 저장  (b) **공격 실행(Red), 탐지 확인(Blue), 증적 관리를 통합**  (c) 방화벽 관리  (d) 패치 배포

**Q10.** 탐지 수준 DL4에 포함되는 것은?
- (a) 로그만 수집  (b) 기본 시그니처  (c) 상관 분석  (d) **자동 대응 (SOAR 플레이북 연동)**

**정답:** Q1:c, Q2:c, Q3:b, Q4:c, Q5:b, Q6:c, Q7:b, Q8:c, Q9:b, Q10:d

---

## 과제

### 과제 1: 확장 ATT&CK Gap 분석 (필수)
실습에서 테스트한 5개 기법 외에 5개를 추가 선정하여 총 10개 기법에 대한 Gap 분석을 수행하라:
- 추가 기법 선정 근거 (위험도, 발생 빈도, 환경 적합성)
- 각 기법의 Atomic Test 명령어와 실행 결과
- 10개 기법의 DL 수준 매핑 표
- 탐지 커버리지 개선 계획 (우선순위 포함)

### 과제 2: 탐지 규칙 세트 개발 (필수)
Gap 분석에서 DL0-DL1로 식별된 기법 3개를 선택하여:
- 각 기법에 대한 Wazuh 커스텀 규칙 XML 작성
- 규칙 테스트 로그와 예상 알림 결과 포함
- 오탐 가능성과 완화 방안 분석
- 규칙 배포 절차 문서화

### 과제 3: 보안 성숙도 개선 로드맵 (선택)
실습 환경의 보안 성숙도를 Level 2에서 Level 4로 끌어올리기 위한 12개월 로드맵을 수립하라:
- 3개월 단위 마일스톤 정의
- 각 마일스톤의 구체적 활동, 필요 자원, 예상 비용
- KPI/메트릭 정의 (MTTD, MTTR, 커버리지율 등)
- 위험 요소와 완화 방안

---

## 다음 주 예고

**Week 14: 대규모 공방전 — 다대다 팀전 설계/운영, Attack/Defense CTF**
- Attack/Defense CTF의 규칙과 인프라 설계
- 다대다 팀전 운영 및 스코어링 시스템
- 실시간 관전 및 분석 기법
- OpsClaw 기반 자동화 CTF 인프라
