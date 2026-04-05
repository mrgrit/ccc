# Week 14: 자동화 침투 테스트 (OpsClaw 활용)

## 학습 목표
- OpsClaw 플랫폼의 아키텍처와 API를 이해한다
- execute-plan API로 다단계 공격을 자동 실행할 수 있다
- Playbook 기반 공격 재현의 장점을 설명할 수 있다
- PoW(Proof of Work) 증거 체인의 원리와 감사 활용을 이해한다
- 수동 침투 테스트와 자동화 테스트의 차이를 비교한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (이 과목에서 자주 나오는 용어)

> 대학 1~2학년이 처음 접할 수 있는 보안/IT 용어를 정리한다.
> 강의 중 모르는 용어가 나오면 이 표를 참고하라.

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **페이로드** | Payload | 공격에 사용되는 실제 데이터/코드. 예: `' OR 1=1--` | 미사일의 탄두 |
| **익스플로잇** | Exploit | 취약점을 악용하는 기법 또는 코드 | 열쇠 없이 문을 여는 방법 |
| **셸** | Shell | 운영체제와 사용자를 연결하는 명령어 해석기 (bash, sh 등) | OS에게 말 걸 수 있는 창구 |
| **리버스 셸** | Reverse Shell | 대상 서버가 공격자에게 역방향 연결을 맺는 것 | 도둑이 집에서 밖으로 전화를 거는 것 |
| **포트** | Port | 서버에서 특정 서비스를 식별하는 번호 (0~65535) | 아파트 호수 |
| **데몬** | Daemon | 백그라운드에서 실행되는 서비스 프로그램 | 24시간 근무하는 경비원 |
| **패킷** | Packet | 네트워크로 전송되는 데이터의 단위 | 택배 상자 하나 |
| **프록시** | Proxy | 클라이언트와 서버 사이에서 중개하는 서버 | 대리인, 중간 거래자 |
| **해시** | Hash | 임의 길이 데이터를 고정 길이 값으로 변환하는 함수 (SHA-256 등) | 지문 (고유하지만 원본 복원 불가) |
| **토큰** | Token | 인증 정보를 담은 문자열 (JWT, API Key 등) | 놀이공원 입장권 |
| **JWT** | JSON Web Token | Base64로 인코딩된 JSON 기반 인증 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리 데이터를 텍스트로 인코딩하는 방법 | 암호가 아닌 "포장" (누구나 풀 수 있음) |
| **CORS** | Cross-Origin Resource Sharing | 다른 도메인에서의 API 호출 허용 설정 | "외부인 출입 허용" 표지판 |
| **API** | Application Programming Interface | 프로그램 간 통신 규약 | 식당의 메뉴판 (주문 양식) |
| **REST** | Representational State Transfer | URL + HTTP 메서드로 자원을 조작하는 API 스타일 | 도서관 대출 시스템 (책 이름으로 검색/대출/반납) |
| **SSH** | Secure Shell | 원격 서버에 안전하게 접속하는 프로토콜 | 암호화된 전화선 |
| **sudo** | SuperUser DO | 관리자(root) 권한으로 명령 실행 | "사장님 권한으로 실행" |
| **SUID** | Set User ID | 실행 시 파일 소유자 권한으로 실행되는 특수 권한 | 다른 사람의 사원증을 빌려 출입 |
| **IPS** | Intrusion Prevention System | 네트워크 침입 방지 시스템 (악성 트래픽 차단) | 공항 보안 검색대 |
| **SIEM** | Security Information and Event Management | 보안 로그를 수집·분석하는 통합 관제 시스템 | CCTV 관제실 |
| **WAF** | Web Application Firewall | 웹 공격을 탐지·차단하는 방화벽 | 웹사이트 전용 경비원 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 (iptables 후계) | 건물 출입구 차단기 |
| **Suricata** | Suricata | 오픈소스 IDS/IPS 엔진 | 공항 X-ray 검색기 |
| **Wazuh** | Wazuh | 오픈소스 SIEM 플랫폼 | CCTV + AI 관제 시스템 |
| **ATT&CK** | MITRE ATT&CK | 실제 공격 전술·기법을 분류한 데이터베이스 | 범죄 수법 백과사전 |
| **OWASP** | Open Web Application Security Project | 웹 보안 취약점 연구 국제 단체 | 웹 보안의 표준 기관 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 (0~10점) | 질병 위험도 등급 |
| **CVE** | Common Vulnerabilities and Exposures | 취약점 고유 식별 번호 | 질병의 고유 코드 (예: COVID-19) |
| **OpsClaw** | OpsClaw | 보안 작업 자동화·증적 관리 플랫폼 (이 수업에서 사용) | 보안 작업 일지 + 자동화 시스템 |

---

# Week 14: 자동화 침투 테스트 (OpsClaw 활용)

## 학습 목표

- OpsClaw 플랫폼의 아키텍처와 API를 이해한다
- execute-plan API로 다단계 공격을 자동 실행할 수 있다
- Playbook 기반 공격 재현의 장점을 설명할 수 있다
- PoW(Proof of Work) 증거 체인의 원리와 감사 활용을 이해한다
- 수동 침투 테스트와 자동화 테스트의 차이를 비교한다

---

## 1. OpsClaw 플랫폼 개요

### 1.1 아키텍처

```
[Claude Code (외부 마스터)]
  계획 수립 --> API 호출 --> 결과 분석
       |
       | HTTP API
       v
[Manager API (:8000)]
  프로젝트 관리 / 태스크 분배 / 증거 기록
  PoW 블록체인 / 보상 시스템
       |
       +-------------+-------------+
       |             |             |
       v             v             v
  [SubAgent]    [SubAgent]    [SubAgent]
   secu:8002     web:8002     siem:8002
```

### 1.2 핵심 개념

| 개념 | 설명 |
|------|------|
| **Project** | 작업 단위. 한 번의 침투 테스트 = 하나의 프로젝트 |
| **Stage** | 프로젝트 상태: created → planning → executing → completed |
| **Task** | 개별 실행 명령. execute-plan에 배열로 전달 |
| **Evidence** | 각 Task의 실행 결과 (stdout, stderr, exit_code) |
| **PoW Block** | Task 실행의 암호학적 증명. 변조 불가능한 감사 증적 |
| **SubAgent** | 실제 명령을 실행하는 에이전트 (각 서버에 배포) |

### 1.3 API 인증

모든 API 호출에 인증 헤더가 필요하다.

> **실습 목적**: OpsClaw API를 사용하여 자동화된 침투 테스트를 수행하고 증적을 체계적으로 관리한다
>
> **배우는 것**: API 인증, 프로젝트 생성, 태스크 디스패치 등 자동화 침투 테스트 파이프라인 구축 방법을 배운다
>
> **결과 해석**: API 응답의 exit_code가 0이면 명령 실행 성공이며, evidence에서 전체 실행 이력을 확인할 수 있다
>
> **실전 활용**: 대규모 인프라의 정기 침투 테스트를 자동화하여 일관성 있는 점검과 증적 관리를 수행한다

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 모든 curl 요청에 포함
-H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 2. OpsClaw API 워크플로우

> **이 실습을 왜 하는가?**
> "자동화 침투 테스트 (OpsClaw 활용)" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 사이버보안 공격/웹해킹/침투테스트 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 기본 흐름

```
1. 프로젝트 생성 (POST /projects)
   ↓
2. 계획 단계 전환 (POST /projects/{id}/plan)
   ↓
3. 실행 단계 전환 (POST /projects/{id}/execute)
   ↓
4. 태스크 실행 (POST /projects/{id}/execute-plan)
   ↓
5. 결과 확인 (GET /projects/{id}/evidence/summary)
   ↓
6. 완료 보고서 (POST /projects/{id}/completion-report)
```

### 2.2 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /projects | 프로젝트 생성 |
| POST | /projects/{id}/plan | 계획 단계 전환 |
| POST | /projects/{id}/execute | 실행 단계 전환 |
| POST | /projects/{id}/execute-plan | 태스크 배열 실행 |
| POST | /projects/{id}/dispatch | 단일 명령 실행 |
| GET | /projects/{id}/evidence/summary | 증거 요약 |
| POST | /projects/{id}/completion-report | 완료 보고서 생성 |
| GET | /pow/blocks | PoW 블록 조회 |
| GET | /pow/verify | 체인 무결성 검증 |
| GET | /pow/leaderboard | 보상 랭킹 |
| GET | /projects/{id}/replay | 작업 재생 |

---

## 3. execute-plan: 다단계 공격 실행

### 3.1 Task 구조

```json
{
  "tasks": [
    {
      "order": 1,
      "instruction_prompt": "실행할 명령어",
      "risk_level": "low|medium|high|critical",
      "subagent_url": "http://대상서버:8002"
    }
  ],
  "subagent_url": "http://기본서버:8002"
}
```

### 3.2 risk_level 설명

| 레벨 | 설명 | 동작 |
|------|------|------|
| low | 읽기 전용 (스캔, 조회) | 즉시 실행 |
| medium | 제한적 변경 (파일 생성) | 즉시 실행 |
| high | 시스템 변경 (설정 수정) | 즉시 실행 |
| critical | 파괴적 변경 (삭제, 초기화) | dry_run 강제, confirmed:true 필요 |

### 3.3 SubAgent URL 목록

| 서버 | SubAgent URL |
|------|-------------|
| opsclaw (로컬) | http://localhost:8002 |
| secu | http://10.20.30.1:8002 또는 http://10.20.30.1:8002 |
| web | http://10.20.30.80:8002 또는 http://10.20.30.80:8002 |
| siem | http://10.20.30.100:8002 또는 http://10.20.30.100:8002 |

---

## 4. PoW 증거 체인

### 4.1 PoW(Proof of Work)란?

각 Task 실행 결과를 암호학적 해시로 연결한 블록체인 구조이다.

```
Block 1              Block 2              Block 3
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ prev_hash: 0 │←───│ prev_hash    │←───│ prev_hash    │
│ task: nmap   │    │ task: curl   │    │ task: sqlmap  │
│ result: ...  │    │ result: ...  │    │ result: ...   │
│ nonce: 12345 │    │ nonce: 67890 │    │ nonce: 11111  │
│ hash: abc... │    │ hash: def... │    │ hash: ghi...  │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 4.2 PoW의 감사 활용

- **변조 감지**: 하나의 블록이라도 수정되면 해시 체인이 깨짐
- **실행 증명**: 특정 시간에 특정 명령이 실행되었음을 증명
- **감사 추적**: 침투 테스트의 모든 단계를 투명하게 기록
- **보고서 작성**: 자동화된 증거 수집으로 보고서 품질 향상

---

## 5. 실습

### 실습 1: 프로젝트 생성 및 기본 워크플로우

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"          # 환경 변수 설정

# 1. 프로젝트 생성
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "name": "week14-automated-pentest",
    "request_text": "JuiceShop 대상 자동화 침투 테스트",
    "master_mode": "external"
  }')

echo "$PROJECT" | python3 -m json.tool

# 프로젝트 ID 추출
PROJECT_ID=$(echo "$PROJECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "프로젝트 ID: $PROJECT_ID"

# 2. Stage 전환: created → planning → executing
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool  # API 인증 키

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool  # API 인증 키
```

### 실습 2: 정찰 단계 자동화 (T1046, T1595)

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 정찰 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sT -p 22,80,3000,443,8080 10.20.30.80",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000/",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/products/search?q=test | head -c 500",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 예상 출력:
# {
#   "project_id": "...",
#   "results": [
#     {"order": 1, "status": "success", "exit_code": 0, ...},
#     {"order": 2, "status": "success", "exit_code": 0, ...},
#     {"order": 3, "status": "success", "exit_code": 0, ...}
#   ]
# }
```

### 실습 3: 웹 공격 단계 자동화 (T1190)

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# SQL Injection 테스트 태스크
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 4,
        "instruction_prompt": "curl -s \"http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1--\" | python3 -c \"import sys,json; data=json.load(sys.stdin); print(f\\\"결과 수: {len(data.get(\\\\\\\"data\\\\\\\", []))}개\\\")\" 2>/dev/null || echo \"응답 파싱 실패\"",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d '{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}' | head -c 300",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d '{\"email\":\"\\\" or 1=1--\",\"password\":\"a\"}' | head -c 300",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 4: 증거 확인

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 증거 요약 조회
echo "===== 증거 요약 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | python3 -m json.tool

# 프로젝트 재생 (모든 태스크 타임라인)
echo ""
echo "===== 작업 재생 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/replay" | python3 -m json.tool
```

### 실습 5: PoW 체인 검증

```bash
# PoW 블록 조회
echo "===== PoW 블록 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" | python3 -m json.tool

# 체인 무결성 검증
echo ""
echo "===== 체인 무결성 검증 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool

# 예상 출력:
# {
#   "valid": true,
#   "blocks": 6,
#   "orphans": 0,
#   "tampered": []
# }

# 보상 랭킹
echo ""
echo "===== 보상 랭킹 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/leaderboard" | python3 -m json.tool
```

### 실습 6: 완료 보고서 생성

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 완료 보고서 작성
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "summary": "JuiceShop 대상 자동화 침투 테스트 완료",
    "outcome": "success",
    "work_details": [
      "정찰: nmap 포트 스캔 (22, 80, 3000 포트 발견)",
      "웹 분석: REST API 엔드포인트 확인",
      "SQL Injection: 제품 검색 API에서 SQLi 취약점 확인",
      "인증 우회: 로그인 API에서 SQL Injection으로 인증 우회 시도",
      "증거: 모든 실행 결과가 PoW 체인에 기록됨"
    ]
  }' | python3 -m json.tool

# 예상 출력:
# {
#   "project_id": "...",
#   "status": "completed",
#   "report": { ... }
# }
```

### 실습 7: 다중 서버 공격 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 새 프로젝트: 전체 인프라 스캔
PROJECT2=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "name": "week14-multi-server-scan",
    "request_text": "전체 인프라 정찰 스캔",
    "master_mode": "external"
  }')
PID2=$(echo "$PROJECT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID2/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null         # API 인증 키
curl -s -X POST "http://localhost:8000/projects/$PID2/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null         # API 인증 키

# 각 서버별 SubAgent로 명령 분배
curl -s -X POST "http://localhost:8000/projects/$PID2/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

echo ""
echo "===== 전체 서버 정보 수집 결과 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PID2/evidence/summary" | python3 -m json.tool
```

---

## 6. 수동 vs 자동화 침투 테스트 비교

| 항목 | 수동 테스트 | OpsClaw 자동화 |
|------|------------|---------------|
| **속도** | 느림 (사람이 직접 입력) | 빠름 (API 일괄 실행) |
| **재현성** | 낮음 (매번 다르게 실행) | 높음 (동일 Playbook 재실행) |
| **증거 수집** | 수동 스크린샷/메모 | 자동 PoW 체인 기록 |
| **다중 서버** | 번거로움 (서버별 SSH) | 간편 (SubAgent URL만 변경) |
| **창의성** | 높음 (즉흥적 판단) | 낮음 (사전 정의된 시나리오) |
| **비용** | 높음 (전문가 시간) | 낮음 (한 번 작성, 반복 사용) |
| **오류 가능성** | 있음 (타이핑 실수) | 낮음 (검증된 명령어) |
| **감사 추적** | 부분적 | 완전 (블록체인 증명) |

### 최선의 접근: 하이브리드

```
자동화로 할 일:
  - 정찰 스캔 (포트, 서비스, 버전)
  - 알려진 취약점 테스트 (SQLi, XSS 패턴)
  - 반복적인 확인 작업
  - 증거 수집 및 기록

수동으로 할 일:
  - 비즈니스 로직 취약점 분석
  - 다단계 공격 체인 설계
  - 예상치 못한 취약점 탐색
  - 결과 해석 및 위험도 평가
```

---

## 7. 실습 과제

1. **자동화 공격 체인**: OpsClaw를 사용하여 JuiceShop에 대한 5단계 이상의 공격 체인을 설계하고 실행하라. 각 단계의 ATT&CK 기법 ID를 명시할 것.
2. **PoW 검증 보고서**: 실행된 모든 태스크의 PoW 블록을 조회하고, 체인 무결성이 유지되었음을 확인하는 보고서를 작성하라.
3. **비교 분석**: 동일한 공격을 수동(Week 05 방식)과 자동화(OpsClaw)로 각각 수행하고, 소요 시간, 정확도, 증거 품질을 비교하라.

---

## 8. 핵심 정리

- OpsClaw는 **프로젝트 → 계획 → 실행 → 증거 → 보고**의 체계적 워크플로우를 제공한다
- **execute-plan**으로 다단계 공격을 한 번에 자동 실행할 수 있다
- **PoW 체인**은 변조 불가능한 감사 증적을 자동 생성한다
- **SubAgent**를 통해 여러 서버에 동시에 명령을 분배할 수 있다
- 자동화는 수동 테스트를 **대체하는 것이 아니라 보완**하는 것이다

**다음 주 예고**: Week 15(기말)에서는 전체 인프라에 대한 종합 침투 테스트를 수행하고, 전문적인 보고서를 작성한다.

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** 이 공격 기법이 OWASP Top 10에서 분류되는 카테고리는?
- (a) Broken Access Control(A01)  (b) **Injection(A03)**  (c) Cryptographic Failures(A02)  (d) SSRF(A10)

**Q2.** 공격자가 가장 먼저 실행하는 정찰 활동은?
- (a) 랜섬웨어 배포  (b) **포트 스캔 및 서비스 핑거프린팅**  (c) DDoS 공격  (d) 방화벽 비활성화

**Q3.** SQLi에서 '--'의 역할은?
- (a) 문자열 연결  (b) **SQL 주석 (이후 쿼리 무시)**  (c) 변수 선언  (d) 함수 호출

**Q4.** MITRE ATT&CK에서 이 기법의 전술(Tactic)은?
- (a) Impact만  (b) **해당 전술 ID 확인 필요**  (c) 모든 전술  (d) 해당 없음

**Q5.** 방어자가 이 공격을 탐지하기 위해 확인해야 하는 로그는?
- (a) CPU 사용률만  (b) **SIEM 경보 + 해당 서비스 로그**  (c) 디스크 용량만  (d) 네트워크 대역폭만

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
