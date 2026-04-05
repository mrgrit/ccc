# Week 13: MITRE ATT&CK 프레임워크

## 학습 목표
- MITRE ATT&CK 프레임워크의 구조(전술, 기법, 하위기법)를 이해한다
- Cyber Kill Chain과 ATT&CK의 관계를 설명할 수 있다
- ATT&CK Navigator를 활용하여 공격 매핑을 시각화할 수 있다
- 본 과정(Week 02~12)에서 수행한 모든 공격을 ATT&CK에 매핑한다

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

# Week 13: MITRE ATT&CK 프레임워크

## 학습 목표

- MITRE ATT&CK 프레임워크의 구조(전술, 기법, 하위기법)를 이해한다
- Cyber Kill Chain과 ATT&CK의 관계를 설명할 수 있다
- ATT&CK Navigator를 활용하여 공격 매핑을 시각화할 수 있다
- 본 과정(Week 02~12)에서 수행한 모든 공격을 ATT&CK에 매핑한다

---

## 1. MITRE ATT&CK 개요

### 1.1 ATT&CK이란?

MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge)은 실제 사이버 공격에서 관찰된 공격자 행동을 체계적으로 분류한 지식 기반이다.

- **목적**: 공격자가 "무엇을" "어떻게" 하는지 표준화된 언어로 기술
- **활용**: 위협 인텔리전스, 방어 체계 평가, 침투 테스트 계획, 보안 교육
- **URL**: https://attack.mitre.org

### 1.2 ATT&CK 구조

```
ATT&CK 매트릭스
+-- 전술 (Tactics)          -- "왜?" (공격자의 목적)
    +-- 기법 (Techniques)       -- "무엇을?" (구체적 방법)
        +-- 하위기법 (Sub-techniques) -- "어떻게?" (세부 변형)
        +-- 절차 (Procedures)         -- "누가, 어떤 도구로?"
```

**예시:**
```
전술: Initial Access (초기 접근)
  +-- 기법: T1190 - Exploit Public-Facing Application
       +-- 하위기법: 없음 (기법 자체가 구체적)
       +-- 절차: SQL Injection으로 JuiceShop 공격 (Week 05)
```

### 1.3 ATT&CK ID 체계

```
T1059.001

각 필드 설명:
  T      --> Technique
  1059   --> 기법 번호 (Command and Scripting Interpreter)
  .001   --> 하위기법 번호 (PowerShell)
```

- **TA00XX**: 전술 (Tactic)
- **T1XXX**: 기법 (Technique)
- **T1XXX.XXX**: 하위기법 (Sub-technique)

---

## 2. 14가지 전술 (Tactics)

> **이 실습을 왜 하는가?**
> "MITRE ATT&CK 프레임워크" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 사이버보안 공격/웹해킹/침투테스트 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

ATT&CK Enterprise 매트릭스의 14가지 전술이다. 공격의 단계별 목적을 나타낸다.

| # | 전술 ID | 전술명 | 설명 | 본 과정 해당 주차 |
|---|---------|--------|------|-------------------|
| 1 | TA0043 | Reconnaissance (정찰) | 대상 정보 수집 | Week 02, 09 |
| 2 | TA0042 | Resource Development (자원 개발) | 공격 인프라 준비 | - |
| 3 | TA0001 | Initial Access (초기 접근) | 네트워크 진입 | Week 03, 04, 05 |
| 4 | TA0002 | Execution (실행) | 악성 코드 실행 | Week 06, 07, 08 |
| 5 | TA0003 | Persistence (지속성) | 접근 유지 | Week 12 |
| 6 | TA0004 | Privilege Escalation (권한 상승) | 높은 권한 획득 | Week 11 |
| 7 | TA0005 | Defense Evasion (방어 회피) | 탐지 우회 | Week 10, 12 |
| 8 | TA0006 | Credential Access (자격증명 접근) | 비밀번호/토큰 탈취 | Week 04, 05 |
| 9 | TA0007 | Discovery (탐색) | 환경 정보 수집 | Week 02, 09 |
| 10 | TA0008 | Lateral Movement (수평 이동) | 다른 시스템으로 이동 | Week 09 |
| 11 | TA0009 | Collection (수집) | 목표 데이터 수집 | Week 07 |
| 12 | TA0011 | Command and Control (C2) | 원격 제어 채널 | Week 10 |
| 13 | TA0010 | Exfiltration (유출) | 데이터 외부 전송 | Week 07 |
| 14 | TA0040 | Impact (영향) | 시스템 파괴/조작 | Week 08 |

---

## 3. Cyber Kill Chain과 ATT&CK 비교

### 3.1 Lockheed Martin Kill Chain

```
1. Reconnaissance (정찰)
   ↓
2. Weaponization (무기화)
   ↓
3. Delivery (전달)
   ↓
4. Exploitation (공격 실행)
   ↓
5. Installation (설치)
   ↓
6. Command & Control (C2)
   ↓
7. Actions on Objectives (목표 달성)
```

### 3.2 Kill Chain vs ATT&CK 매핑

| Kill Chain | ATT&CK 전술 |
|------------|-------------|
| Reconnaissance | TA0043 Reconnaissance |
| Weaponization | TA0042 Resource Development |
| Delivery | TA0001 Initial Access |
| Exploitation | TA0002 Execution |
| Installation | TA0003 Persistence, TA0004 Privilege Escalation |
| C2 | TA0011 Command and Control |
| Actions | TA0009~TA0010, TA0040 Collection/Exfiltration/Impact |

**ATT&CK의 장점:**
- Kill Chain은 7단계 선형 구조 → ATT&CK은 14전술 병렬/반복 구조
- Kill Chain은 "단계"만 표현 → ATT&CK은 "구체적 기법"까지 분류
- ATT&CK은 실제 APT 그룹의 절차(Procedure)까지 매핑

---

## 4. ATT&CK Navigator

### 4.1 Navigator란?

ATT&CK Navigator는 ATT&CK 매트릭스를 웹 브라우저에서 시각화하고 편집할 수 있는 도구이다.

- **URL**: https://mitre-attack.github.io/attack-navigator/
- **용도**: 공격 시나리오 매핑, 방어 커버리지 분석, 보고서 작성

### 4.2 Navigator 사용법

1. 웹 브라우저에서 Navigator 접속
2. "Create New Layer" → "Enterprise" 선택
3. 사용한 기법 셀을 클릭하여 색상 표시
4. 코멘트 추가로 상세 설명 작성
5. JSON으로 내보내기 가능

### 4.3 Layer JSON 구조

```json
{
  "name": "Course 1 Attack Mapping",
  "versions": {
    "attack": "14",
    "navigator": "4.9"
  },
  "domain": "enterprise-attack",
  "techniques": [
    {
      "techniqueID": "T1190",
      "color": "#ff6666",
      "comment": "Week 05: SQL Injection on JuiceShop",
      "score": 1
    },
    {
      "techniqueID": "T1059.004",
      "color": "#ff6666",
      "comment": "Week 06: Bash command execution",
      "score": 1
    }
  ]
}
```

---

## 5. 본 과정 공격의 ATT&CK 매핑

### 5.1 전체 매핑 표

이 표는 Week 02부터 Week 12까지 수행한 모든 공격을 ATT&CK 기법에 매핑한 것이다.

| 주차 | 공격 내용 | ATT&CK 기법 ID | 기법명 | 전술 |
|------|-----------|-----------------|--------|------|
| **Week 02** | 웹 정찰, 디렉토리 스캔 | T1595.002 | Active Scanning: Vulnerability Scanning | Reconnaissance |
| Week 02 | robots.txt, 소스코드 분석 | T1592.004 | Gather Victim Host Information: Client Configurations | Reconnaissance |
| **Week 03** | HTML/JS 분석, 쿠키 조작 | T1189 | Drive-by Compromise | Initial Access |
| **Week 04** | XSS (Reflected, Stored) | T1059.007 | Command and Scripting Interpreter: JavaScript | Execution |
| Week 04 | 세션 토큰 탈취 | T1539 | Steal Web Session Cookie | Credential Access |
| **Week 05** | SQL Injection | T1190 | Exploit Public-Facing Application | Initial Access |
| Week 05 | DB 데이터 추출 | T1005 | Data from Local System | Collection |
| Week 05 | 인증 우회 | T1078 | Valid Accounts | Initial Access |
| **Week 06** | OS Command Injection | T1059.004 | Command and Scripting Interpreter: Unix Shell | Execution |
| **Week 07** | 파일 업로드 공격 | T1105 | Ingress Tool Transfer | Command and Control |
| Week 07 | 디렉토리 트래버설 | T1083 | File and Directory Discovery | Discovery |
| Week 07 | 민감 파일 읽기 | T1530 | Data from Cloud Storage | Collection |
| **Week 08** | CSRF 공격 | T1185 | Browser Session Forgery | Collection |
| Week 08 | SSRF 공격 | T1090 | Proxy | Command and Control |
| **Week 09** | 포트 스캐닝 | T1046 | Network Service Scanning | Discovery |
| Week 09 | 패킷 캡처 | T1040 | Network Sniffing | Credential Access |
| Week 09 | ARP 스푸핑 | T1557.002 | Adversary-in-the-Middle: ARP Cache Poisoning | Credential Access |
| **Week 10** | 방화벽 우회 | T1562.004 | Impair Defenses: Disable or Modify System Firewall | Defense Evasion |
| Week 10 | IPS 우회 (인코딩) | T1027 | Obfuscated Files or Information | Defense Evasion |
| Week 10 | ICMP 터널링 | T1572 | Protocol Tunneling | Command and Control |
| Week 10 | HTTP C2 비콘 | T1071.001 | Application Layer Protocol: Web Protocols | Command and Control |
| **Week 11** | SUID 악용 | T1548.001 | Abuse Elevation Control: Setuid and Setgid | Privilege Escalation |
| Week 11 | sudo 악용 | T1548.003 | Abuse Elevation Control: Sudo and Sudo Caching | Privilege Escalation |
| Week 11 | Cron 악용 | T1053.003 | Scheduled Task/Job: Cron | Privilege Escalation |
| Week 11 | PATH 하이재킹 | T1574.007 | Hijack Execution Flow: Path Interception | Privilege Escalation |
| **Week 12** | SSH 키 인젝션 | T1098.004 | Account Manipulation: SSH Authorized Keys | Persistence |
| Week 12 | Cron 백도어 | T1053.003 | Scheduled Task/Job: Cron | Persistence |
| Week 12 | systemd 서비스 | T1543.002 | Create or Modify System Process: Systemd Service | Persistence |
| Week 12 | 히스토리 삭제 | T1070.003 | Indicator Removal: Clear Command History | Defense Evasion |
| Week 12 | 로그 삭제 | T1070.002 | Indicator Removal: Clear Linux or Mac System Logs | Defense Evasion |
| Week 12 | 타임스탬프 조작 | T1070.006 | Indicator Removal: Timestomp | Defense Evasion |

### 5.2 전술별 커버리지

```
Reconnaissance      ████░░░░░░ 2개 기법
Resource Development░░░░░░░░░░ 0개 (미실습)
Initial Access      ███░░░░░░░ 3개 기법
Execution           ██░░░░░░░░ 2개 기법
Persistence         ███░░░░░░░ 3개 기법
Privilege Escalation████░░░░░░ 4개 기법
Defense Evasion     ████░░░░░░ 4개 기법
Credential Access   ███░░░░░░░ 3개 기법
Discovery           ██░░░░░░░░ 2개 기법
Lateral Movement    ░░░░░░░░░░ 0개 (미실습)
Collection          ███░░░░░░░ 3개 기법
Command and Control ███░░░░░░░ 3개 기법
Exfiltration        ░░░░░░░░░░ 0개 (미실습)
Impact              ░░░░░░░░░░ 0개 (미실습)
```

---

## 6. 실습

### 실습 1: ATT&CK 매트릭스 탐색

> **실습 목적**: MITRE ATT&CK 프레임워크를 사용하여 공격 기법을 체계적으로 분류하고 매핑한다
>
> **배우는 것**: ATT&CK 매트릭스에서 전술(Tactic)과 기법(Technique)의 관계를 이해하고, 실제 공격을 ATT&CK ID로 매핑하는 방법을 배운다
>
> **결과 해석**: 각 기법 ID(예: T1190)와 연관된 탐지 방법, 완화 조치를 확인하여 방어 전략을 수립할 수 있다
>
> **실전 활용**: SOC 분석가와 침투 테스터 모두 ATT&CK 프레임워크로 공격을 문서화하고 커뮤니케이션한다

```bash
# ATT&CK 데이터를 커맨드라인에서 조회
# T1190 (SQL Injection 관련) 정보 확인

# ATT&CK STIX 데이터 다운로드 (JSON)
curl -sL "https://raw.githubusercontent.com/mitre/ctt/master/enterprise-attack/enterprise-attack.json" \
  -o /tmp/attack.json 2>/dev/null && echo "다운로드 완료" || echo "오프라인 환경"

# 또는 간단한 조회
echo "=== T1190: Exploit Public-Facing Application ==="
echo "전술: Initial Access (TA0001)"
echo "설명: 인터넷에 노출된 애플리케이션의 취약점을 악용하여 초기 접근 획득"
echo "예시: SQL Injection, Command Injection, File Upload"
echo "방어: WAF, 입력 검증, 정기 패치, 침투 테스트"
echo ""
echo "=== 본 과정 관련 ==="
echo "Week 05: JuiceShop SQL Injection → T1190"
echo "Week 06: Command Injection → T1190 + T1059.004"
```

### 실습 2: OpsClaw로 ATT&CK 기반 공격 체인 실행

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# OpsClaw 프로젝트 생성: ATT&CK 매핑된 공격 체인
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "name": "week13-attack-mapping",
    "request_text": "ATT&CK 기반 공격 체인 실행 및 매핑",
    "master_mode": "external"
  }' | python3 -m json.tool

# 프로젝트 ID 확인 후 Stage 전환 (예: id=1)
curl -s -X POST http://localhost:8000/projects/1/plan \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키
curl -s -X POST http://localhost:8000/projects/1/execute \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키

# ATT&CK 기법별 태스크 실행
curl -s -X POST http://localhost:8000/projects/1/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sT -p 22,80,3000 10.20.30.80",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/products/search?q=test",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1--",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/1/evidence/summary | python3 -m json.tool

# ATT&CK 매핑 기록
echo "Task 1 → T1046 (Network Service Scanning)"
echo "Task 2 → T1595.002 (Active Scanning: Vulnerability Scanning)"
echo "Task 3 → T1190 (Exploit Public-Facing Application)"
```

### 실습 3: ATT&CK Navigator Layer 생성

본 과정에서 사용한 기법을 Navigator Layer JSON으로 작성한다.

```bash
# Navigator Layer JSON 생성
cat > /tmp/course1_attack_layer.json << 'LAYER'
{
  "name": "Course 1 - 사이버보안 공격 실습 매핑",
  "versions": {
    "attack": "14",
    "navigator": "4.9.1"
  },
  "domain": "enterprise-attack",
  "description": "Week 02~12에서 실습한 공격 기법 매핑",
  "sorting": 0,
  "layout": {
    "layout": "side",
    "aggregateFunction": "average",
    "showID": true,
    "showName": true
  },
  "techniques": [
    {"techniqueID": "T1595", "tactic": "reconnaissance", "color": "#ff6666", "comment": "W02: 웹 정찰, 디렉토리 스캔", "score": 1},
    {"techniqueID": "T1592", "tactic": "reconnaissance", "color": "#ff6666", "comment": "W02: robots.txt, 소스코드 분석", "score": 1},
    {"techniqueID": "T1190", "tactic": "initial-access", "color": "#ff3333", "comment": "W05: SQL Injection, W06: Command Injection", "score": 3},
    {"techniqueID": "T1078", "tactic": "initial-access", "color": "#ff3333", "comment": "W05: 인증 우회", "score": 2},
    {"techniqueID": "T1059", "tactic": "execution", "color": "#ff9900", "comment": "W04: XSS(JS), W06: Command Injection(Bash)", "score": 2},
    {"techniqueID": "T1053", "tactic": "persistence", "color": "#cc33ff", "comment": "W12: Cron 백도어", "score": 2},
    {"techniqueID": "T1098", "tactic": "persistence", "color": "#cc33ff", "comment": "W12: SSH 키 인젝션", "score": 2},
    {"techniqueID": "T1543", "tactic": "persistence", "color": "#cc33ff", "comment": "W12: systemd 서비스 백도어", "score": 1},
    {"techniqueID": "T1548", "tactic": "privilege-escalation", "color": "#ff6600", "comment": "W11: SUID, sudo 악용", "score": 3},
    {"techniqueID": "T1574", "tactic": "privilege-escalation", "color": "#ff6600", "comment": "W11: PATH 하이재킹", "score": 1},
    {"techniqueID": "T1027", "tactic": "defense-evasion", "color": "#3399ff", "comment": "W10: 인코딩 기반 IPS 우회", "score": 1},
    {"techniqueID": "T1070", "tactic": "defense-evasion", "color": "#3399ff", "comment": "W12: 로그 삭제, 히스토리 제거, 타임스탬프 조작", "score": 3},
    {"techniqueID": "T1562", "tactic": "defense-evasion", "color": "#3399ff", "comment": "W10: 방화벽 우회 시도", "score": 1},
    {"techniqueID": "T1539", "tactic": "credential-access", "color": "#ffcc00", "comment": "W04: XSS를 통한 세션 토큰 탈취", "score": 2},
    {"techniqueID": "T1040", "tactic": "credential-access", "color": "#ffcc00", "comment": "W09: 패킷 스니핑", "score": 1},
    {"techniqueID": "T1557", "tactic": "credential-access", "color": "#ffcc00", "comment": "W09: ARP 스푸핑", "score": 1},
    {"techniqueID": "T1046", "tactic": "discovery", "color": "#66cc66", "comment": "W09: nmap 포트 스캐닝", "score": 2},
    {"techniqueID": "T1083", "tactic": "discovery", "color": "#66cc66", "comment": "W07: 디렉토리 트래버설", "score": 1},
    {"techniqueID": "T1005", "tactic": "collection", "color": "#9966cc", "comment": "W05: DB 데이터 추출", "score": 2},
    {"techniqueID": "T1185", "tactic": "collection", "color": "#9966cc", "comment": "W08: CSRF 공격", "score": 1},
    {"techniqueID": "T1071", "tactic": "command-and-control", "color": "#cc6699", "comment": "W10: HTTP C2 비콘", "score": 1},
    {"techniqueID": "T1572", "tactic": "command-and-control", "color": "#cc6699", "comment": "W10: ICMP 터널링", "score": 1},
    {"techniqueID": "T1105", "tactic": "command-and-control", "color": "#cc6699", "comment": "W07: 파일 업로드(웹쉘)", "score": 2}
  ],
  "gradient": {
    "colors": ["#ffffff", "#ff6666"],
    "minValue": 0,
    "maxValue": 3
  }
}
LAYER

echo "Navigator Layer 파일 생성: /tmp/course1_attack_layer.json"
echo "ATT&CK Navigator에서 'Open Existing Layer' → 이 JSON 파일을 업로드하면 시각화됨"
wc -l /tmp/course1_attack_layer.json                   # 줄/단어/바이트 수 카운트
```

### 실습 4: 주차별 공격 체인 분석

```bash
# 전체 공격 체인을 Kill Chain 단계별로 정리
cat << 'CHAIN'
============================================
  Course 1 전체 공격 체인 (Kill Chain 매핑)
============================================

[1. Reconnaissance - 정찰]
  Week 02: 웹 정찰 → robots.txt, 디렉토리 스캔, 기술 스택 파악
  Week 09: 네트워크 정찰 → 포트 스캐닝, 서비스 버전 탐지

[2. Weaponization - 무기화]
  (본 과정에서 도구 직접 개발은 미포함)

[3. Delivery + Exploitation - 전달 + 공격 실행]
  Week 03: 클라이언트 측 공격 → HTML/JS 분석, 쿠키 조작
  Week 04: XSS → 스크립트 인젝션, 세션 탈취
  Week 05: SQL Injection → DB 데이터 추출, 인증 우회
  Week 06: Command Injection → OS 명령 실행
  Week 07: 파일 업로드 → 웹쉘, 디렉토리 트래버설
  Week 08: CSRF/SSRF → 요청 위조

[4. Installation - 설치 (지속성)]
  Week 12: SSH 키 인젝션, Cron 백도어, systemd 서비스

[5. Privilege Escalation - 권한 상승]
  Week 11: SUID, sudo, Cron, PATH 하이재킹

[6. Command & Control - C2]
  Week 10: ICMP 터널링, HTTP C2 비콘

[7. Defense Evasion - 방어 회피]
  Week 10: IPS 우회 (인코딩, 분할)
  Week 12: 로그 삭제, 히스토리 제거, 타임스탬프 조작

[8. Actions on Objectives - 목표 달성]
  Week 05: 데이터 탈취 (DB)
  Week 07: 파일 탈취 (디렉토리 트래버설)
CHAIN
```

---

## 7. 방어 매핑: Detection Coverage

ATT&CK을 방어자 관점에서 활용하는 방법이다.

### 7.1 탐지 데이터 소스

| ATT&CK 기법 | 탐지 데이터 소스 | 실습 환경의 탐지 도구 |
|-------------|-----------------|---------------------|
| T1190 (웹 공격) | HTTP 로그, WAF 로그 | Apache+ModSecurity (web), Suricata (secu) |
| T1046 (포트 스캔) | 네트워크 플로우, IDS | Suricata (secu) |
| T1548 (권한 상승) | sudo 로그, 프로세스 모니터링 | Wazuh (siem) |
| T1053 (Cron) | 파일 변경 감시 | Wazuh FIM (siem) |
| T1098 (SSH 키) | 파일 변경 감시 | Wazuh FIM (siem) |
| T1070 (로그 삭제) | 로그 무결성 검사 | Wazuh (siem) |

### 7.2 탐지 갭 분석

```
본 실습 환경의 탐지 커버리지:

  탐지 가능:    ████████░░ 80%
  탐지 불가/미확인: ██░░░░░░░░ 20%

탐지 갭:
  - ICMP 터널링 (T1572): Suricata 규칙 부재 시 미탐지
  - PATH 하이재킹 (T1574): 호스트 기반 모니터링 필요
  - 메모리 실행 (/dev/shm): 디스크 기반 검사로는 탐지 불가
```

---

## 8. 실습 과제

1. **ATT&CK 매핑 완성**: 본 과정 전체 공격을 ATT&CK Navigator Layer JSON으로 작성하고, 각 기법에 대한 코멘트(어떤 도구/명령을 사용했는지)를 추가하라.
2. **방어 갭 분석**: 실습 환경(secu + Wazuh)에서 탐지 가능한 기법과 불가능한 기법을 분류하고, 탐지 갭을 해소할 방법을 3가지 이상 제안하라.
3. **APT 그룹 연구**: MITRE ATT&CK에서 한국을 대상으로 활동하는 APT 그룹(예: Lazarus, Kimsuky)을 1개 선택하여, 해당 그룹이 사용하는 기법을 본 과정에서 실습한 기법과 비교하라.

---

## 9. 핵심 정리

- MITRE ATT&CK은 사이버 공격을 **14가지 전술과 수백 가지 기법**으로 체계화한 프레임워크이다
- **전술(Tactic)**은 공격의 목적, **기법(Technique)**은 구체적 방법을 나타낸다
- ATT&CK Navigator로 공격과 방어를 **시각화**하여 갭 분석이 가능하다
- 본 과정에서 **22개 이상의 ATT&CK 기법**을 직접 실습했다
- 동일한 프레임워크를 **공격자와 방어자 모두** 활용할 수 있다

**다음 주 예고**: Week 14에서는 OpsClaw 플랫폼을 활용하여 이 모든 공격을 자동화하는 방법을 학습한다.

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
