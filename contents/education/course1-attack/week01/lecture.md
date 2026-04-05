# Week 01: 보안 개론 + 실습 환경 구축

## 학습 목표
- 사이버보안의 기본 개념, 역사, 주요 용어를 이해한다
- CIA Triad, AAA, Defense in Depth 등 보안 원칙을 설명할 수 있다
- 실습 인프라(4대 서버)에 접속하고 각 서버의 역할과 구성을 파악한다
- 기본 리눅스 명령어와 네트워크 도구를 능숙하게 사용할 수 있다
- OpsClaw 플랫폼의 기본 사용법을 익히고, 증적 기반 작업의 중요성을 이해한다
- 보안 윤리와 법적 책임을 인지한다

## 전제 조건
- 리눅스 터미널 기본 사용 경험 (ls, cd, cat 수준)
- SSH 클라이언트 설치 (Windows: PuTTY 또는 WSL, Mac/Linux: 내장 ssh)
- 웹 브라우저 (Chrome/Firefox)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 사이버보안 개론 (이론) | 강의 |
| 0:40-1:10 | 보안 원칙과 프레임워크 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 인프라 소개 + 접속 실습 | 실습 |
| 2:00-2:40 | 리눅스/네트워크 기본 도구 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | OpsClaw 플랫폼 실습 | 실습 |
| 3:20-3:40 | 보안 윤리 + 복습 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 사이버보안 개론 (40분)

## 1.1 사이버보안이란?

사이버보안(Cybersecurity)은 컴퓨터 시스템, 네트워크, 데이터를 무단 접근, 손상, 도난으로부터 보호하는 모든 활동을 말한다.

### 왜 중요한가?

디지털 전환이 가속화되면서 기업·정부·개인의 핵심 자산이 온라인으로 이동하고 있다. 이에 따라 사이버 공격의 빈도와 피해 규모도 급증하고 있다.

**주요 통계 (2024~2025 기준):**
- 글로벌 사이버 범죄 피해액: 연간 약 10.5조 달러 (Cybersecurity Ventures)
- 랜섬웨어 평균 피해 복구 비용: 약 185만 달러 (Sophos 2024)
- 데이터 유출 평균 탐지 시간: 약 194일 (IBM Cost of a Data Breach 2024)
- 한국 개인정보 유출 신고 건수: 연간 300건 이상 (KISA)

### 보안의 역사 간략 타임라인

```
1970s: 최초의 컴퓨터 바이러스 (Creeper, 1971)
1980s: Morris Worm (1988) — 인터넷 최초의 대규모 웜, 6000대 감염
1990s: 웹의 등장 → 웹 해킹의 시작 (SQL Injection 개념 등장)
2000s: 대규모 DDoS, APT 공격 등장 (Stuxnet, 2010)
2010s: 랜섬웨어 대유행 (WannaCry 2017), 클라우드 보안 이슈
2020s: 공급망 공격 (SolarWinds 2020), AI 기반 공격/방어, LLM 보안
```

## 1.2 핵심 용어 상세 해설

### 기본 용어

| 용어 | 정의 | 비유 | 실제 예시 |
|------|------|------|---------|
| **취약점 (Vulnerability)** | 시스템의 보안 약점 | 잠금장치가 없는 창문 | SQL Injection이 가능한 로그인 폼 |
| **위협 (Threat)** | 취약점을 악용할 수 있는 잠재적 위험 | 도둑의 존재 | 해커가 SQLi로 DB를 탈취할 수 있음 |
| **공격 (Attack/Exploit)** | 위협이 실제로 실행된 것 | 도둑이 창문을 열고 침입 | `' OR 1=1--` 페이로드 전송 |
| **자산 (Asset)** | 보호해야 할 대상 | 집 안의 귀중품 | 사용자 DB, 웹 서버, 소스코드 |
| **리스크 (Risk)** | 위협 × 취약점 × 영향도 | 도둑이 와서 귀중품을 훔칠 확률 × 피해액 | SQLi로 10만 건 개인정보 유출 가능성 |
| **대응 (Countermeasure)** | 리스크를 줄이기 위한 조치 | 창문 잠금장치 설치 | 입력값 검증, WAF 배치 |

### 보안 식별자 체계

| 식별자 | 정식 명칭 | 관리 기관 | 역할 | 예시 |
|--------|---------|---------|------|------|
| **CVE** | Common Vulnerabilities and Exposures | MITRE | 취약점에 고유 번호 부여 | CVE-2021-44228 (Log4Shell) |
| **CWE** | Common Weakness Enumeration | MITRE | 취약점의 유형(카테고리) 분류 | CWE-89 (SQL Injection) |
| **CVSS** | Common Vulnerability Scoring System | FIRST | 취약점 심각도 점수 (0~10) | CVSS 10.0 (Log4Shell) |
| **CPE** | Common Platform Enumeration | NIST | 영향받는 소프트웨어 식별 | cpe:2.3:a:apache:log4j:2.14.1 |

**CVE와 CWE의 관계:**
```
CWE-89 (SQL Injection이라는 약점 유형)
  +-- CVE-2024-XXXXX (특정 제품 A의 SQLi 취약점)
  +-- CVE-2024-YYYYY (특정 제품 B의 SQLi 취약점)
  +-- CVE-2024-ZZZZZ (특정 제품 C의 SQLi 취약점)
```

### MITRE ATT&CK 프레임워크 소개

MITRE ATT&CK는 실제 관찰된 공격 행위를 체계적으로 분류한 지식 기반이다.

```
전술(Tactic) = "왜?" (공격 목적)
  +-- 기법(Technique) = "어떻게?" (공격 방법)
        +-- 절차(Procedure) = "구체적으로?" (실제 명령/도구)

예시:
  전술: Initial Access (초기 접근)
    +-- 기법: T1190 Exploit Public-Facing Application
          +-- 절차: JuiceShop에 ' OR 1=1-- 전송하여 로그인 우회
```

**14개 전술 요약:**

| 순서 | 전술 | 설명 |
|------|------|------|
| 1 | Reconnaissance | 목표 정보 수집 |
| 2 | Resource Development | 공격 인프라 준비 |
| 3 | Initial Access | 최초 침투 |
| 4 | Execution | 악성 코드 실행 |
| 5 | Persistence | 지속적 접근 확보 |
| 6 | Privilege Escalation | 권한 상승 |
| 7 | Defense Evasion | 탐지 회피 |
| 8 | Credential Access | 인증 정보 탈취 |
| 9 | Discovery | 내부 정보 수집 |
| 10 | Lateral Movement | 내부 이동 |
| 11 | Collection | 데이터 수집 |
| 12 | Command and Control | 원격 제어 |
| 13 | Exfiltration | 데이터 유출 |
| 14 | Impact | 시스템 파괴/변조 |

> 이 과목에서는 14개 전술 중 실습 인프라에서 재현 가능한 기법들을 직접 실행해본다.

### OWASP Top 10 (2021)

| 순위 | 카테고리 | 설명 | 실습 주차 |
|------|---------|------|---------|
| A01 | Broken Access Control | 접근 제어 실패 | Week 06 |
| A02 | Cryptographic Failures | 암호화 실패 | Week 06 |
| A03 | Injection | SQLi, XSS, Command Injection | Week 04, 05 |
| A04 | Insecure Design | 안전하지 않은 설계 | Week 03 |
| A05 | Security Misconfiguration | 보안 설정 오류 | Week 07 |
| A06 | Vulnerable Components | 취약한 구성요소 | Week 07 |
| A07 | Auth Failures | 인증/세션 관리 실패 | Week 06 |
| A08 | Software/Data Integrity | 무결성 실패 | Week 12 |
| A09 | Logging/Monitoring Failures | 로깅 실패 | Week 13 |
| A10 | SSRF | 서버 측 요청 위조 | Week 07 |

---

# Part 2: 보안 원칙과 프레임워크 (30분)

## 2.1 CIA Triad (보안의 3요소)

```
              기밀성
           Confidentiality
              ╱╲
             ╱  ╲
            ╱    ╲
           ╱  CIA  ╲
          ╱   Triad  ╲
         ╱____________╲
   무결성              가용성
  Integrity         Availability
```

### 기밀성 (Confidentiality)
- **정의:** 인가된 사용자만 정보에 접근할 수 있도록 보장
- **위반 사례:** 해커가 DB를 덤프하여 고객 개인정보 유출
- **보호 방법:** 암호화(AES, RSA), 접근 제어(RBAC), 인증(MFA)
- **실습 연관:** Week 04에서 SQLi로 DB 데이터를 추출하면 기밀성 위반

### 무결성 (Integrity)
- **정의:** 정보가 무단으로 변경되지 않음을 보장
- **위반 사례:** 공격자가 웹 페이지를 변조(defacement)
- **보호 방법:** 해시 함수(SHA-256), 디지털 서명, FIM(File Integrity Monitoring)
- **실습 연관:** Week 11에서 SUID 바이너리를 악용하면 시스템 파일 무결성 위반

### 가용성 (Availability)
- **정의:** 필요할 때 정보와 시스템에 접근 가능하도록 보장
- **위반 사례:** DDoS 공격으로 웹 서비스 다운
- **보호 방법:** 이중화, 로드 밸런서, DDoS 방어, 백업
- **실습 연관:** Week 10에서 방화벽 우회 시 가용성과 보안의 트레이드오프

## 2.2 AAA 프레임워크

| 요소 | 정의 | 예시 |
|------|------|------|
| **Authentication (인증)** | "너 누구?" | 아이디/비밀번호, 생체인증, MFA |
| **Authorization (인가)** | "너 뭐 할 수 있어?" | RBAC, 파일 퍼미션, sudo 권한 |
| **Accounting (감사)** | "너 뭐 했어?" | 로그 기록, SIEM, OpsClaw evidence |

**OpsClaw와의 연관:**
- Authentication: API Key (`X-API-Key: opsclaw-api-key-2026`)
- Authorization: risk_level에 따른 dry_run 강제 (critical → 사전 승인 필요)
- Accounting: 모든 태스크의 evidence + PoW 블록 자동 기록

## 2.3 Defense in Depth (심층 방어)

단일 방어에 의존하지 않고, 여러 계층의 보안을 중첩하는 전략이다.

```
[Layer 1] 물리적 보안      -- 서버실 출입 통제
  [Layer 2] 네트워크 보안   -- 방화벽, IPS
    [Layer 3] 호스트 보안    -- 패치, AV, FIM
      [Layer 4] 애플리케이션 보안 -- WAF, 코드 검증
        [Layer 5] 데이터 보안     -- 암호화, DLP

  외부 --> [물리] --> [네트워크] --> [호스트] --> [앱] --> [데이터]
            secu       secu         각 서버     web      DB 암호화
            출입통제   nftables     패치/AV     WAF
                       Suricata
```

**우리 실습 인프라에서의 Defense in Depth:**

| 계층 | 인프라 구성 | 역할 |
|------|-----------|------|
| 네트워크 | secu (nftables) | 트래픽 필터링 |
| 네트워크 | secu (Suricata IPS) | 악성 패턴 탐지/차단 |
| 애플리케이션 | web (Apache+ModSecurity WAF) | 웹 공격 차단 |
| 호스트 | web (Linux 권한 관리) | OS 수준 접근 제어 |
| 모니터링 | siem (Wazuh) | 로그 수집·분석·경보 |
| 관리 | opsclaw (OpsClaw) | 작업 오케스트레이션·증적 |

## 2.4 공격자의 유형과 동기

| 유형 | 동기 | 기술 수준 | 사용 도구 | 실제 사례 |
|------|------|---------|---------|---------|
| 스크립트 키디 | 호기심, 과시 | 낮음 | 공개 도구 (Metasploit, SQLmap) | 학교 서버 해킹 시도 |
| 핵티비스트 | 정치/사회적 목적 | 중간 | DDoS, 웹 변조 | Anonymous, LulzSec |
| 사이버 범죄자 | 금전적 이익 | 높음 | 랜섬웨어, 피싱 | REvil, Conti 랜섬웨어 그룹 |
| 국가 지원 해커 (APT) | 첩보, 파괴 | 매우 높음 | 제로데이, 공급망 공격 | Lazarus(북한), APT28(러시아) |
| 내부자 위협 | 불만, 금전 | 시스템 지식 보유 | 권한 남용 | Snowden, 퇴직 직원 데이터 유출 |

## 2.5 모의해킹(Penetration Testing)의 단계

이 과목 전체는 모의해킹의 체계적 방법론을 따른다.

```
[1] 사전 협의    → 범위, 규칙, 일정 합의 (Week 01)
[2] 정보 수집    → 대상 시스템 정찰 (Week 02~03)
[3] 취약점 분석  → 발견된 정보로 약점 식별 (Week 04~07)
[4] 공격 실행    → 취약점 악용 (Week 09~12)
[5] 권한 상승    → 더 높은 권한 확보 (Week 11)
[6] 지속성 확보  → 재접근 방법 설치 (Week 12)
[7] 보고서 작성  → 발견사항 문서화 (Week 14~15)
```

---

# Part 3: 실습 인프라 소개 + 접속 실습 (40분)

## 3.1 인프라 구성도 (상세)

```
학생 PC (192.168.x.x)
  |
  | SSH
  v
[opsclaw] 10.20.30.201
  Manager API :8000 / SubAgent :8002
  |
  | 내부 네트워크 (10.20.30.0/24)
  |
  +-------+-------+
  |       |       |
  v       v       v

[secu] 10.20.30.1          [web] 10.20.30.80          [siem] 10.20.30.100
  - nftables (방화벽)         - Apache :80                - Wazuh Dashboard :443
  - Suricata IPS              - JuiceShop :3000           - Wazuh API :55000
  - SubAgent :8002            - ModSecurity WAF           - OpenCTI :9400
  - SSH: secu@ / pass: 1     - SubAgent :8002            - SubAgent :8002
                              - SSH: web@ / pass: 1      - SSH: siem@ / pass: 1

[dgx-spark] 192.168.0.105 (외부)
  - Ollama LLM :11434
```

## 3.2 각 서버의 보안 역할 (상세)

### secu — 네트워크 보안 게이트웨이
| 항목 | 상세 |
|------|------|
| 비유 | 건물 입구 경비원 + 금속탐지기 |
| 핵심 SW | nftables (방화벽), Suricata (IPS) |
| 하는 일 | 모든 네트워크 트래픽을 검사, 허용/차단/경보 |
| 학습 주차 | Week 09~10 (네트워크 공격, IPS 우회) |

### web — 웹 서버 (공격 대상)
| 항목 | 상세 |
|------|------|
| 비유 | 은행 창구 (고객이 접근하는 서비스) |
| 핵심 SW | Apache(:80), JuiceShop(:3000), Apache+ModSecurity WAF |
| 하는 일 | 웹 서비스 제공, 의도적으로 취약한 앱(JuiceShop) 운영 |
| 학습 주차 | Week 03~07 (웹 공격 전반), Week 11~12 (권한 상승) |
| 중요 정보 | 사용자: web, 비밀번호: 1, **sudo NOPASSWD: ALL** (의도적 취약 설정) |

> **JuiceShop란?**
> OWASP에서 만든 의도적으로 취약한 웹 애플리케이션이다. SQL Injection, XSS, CSRF 등
> 100개 이상의 보안 챌린지를 포함하고 있어 보안 학습에 최적화되어 있다.

### siem — 보안 모니터링 센터
| 항목 | 상세 |
|------|------|
| 비유 | CCTV 관제실 + 경보 시스템 |
| 핵심 SW | Wazuh 4.11.2 (SIEM), OpenCTI (위협 인텔리전스) |
| 하는 일 | 모든 서버의 로그를 수집·분석, 이상 행위 탐지 후 경보 |
| 학습 주차 | Week 13 (ATT&CK), Week 14 (자동화) |

### opsclaw — 관리/오케스트레이션 플랫폼
| 항목 | 상세 |
|------|------|
| 비유 | 보안 관리 본부 (지시, 기록, 분석) |
| 핵심 SW | OpsClaw Manager API, SubAgent Runtime |
| 하는 일 | 보안 작업 지시, 실행 증적 기록, 보상/성과 관리 |
| 학습 주차 | 매주 (OpsClaw 경유 실습) |

---

## 실습 3.1: SSH 접속 (기본)

### Step 1: opsclaw 서버 접속

> **실습 목적**: SSH 접속은 모든 보안 실습의 출발점이며, 서버 원격 관리의 기본 기술이다.
>
> **배우는 것**: SSH 프로토콜로 원격 서버에 안전하게 접속하는 방법과, 접속 후 현재 사용자/호스트를 확인하는 습관을 익힌다.
>
> **결과 해석**: 프롬프트에 `opsclaw@opsclaw:~$`가 표시되면 접속 성공이다. `Connection refused`는 서버 미기동, `Permission denied`는 비밀번호 오류이다.
>
> **실전 활용**: 보안 엔지니어는 매일 수십 대의 서버에 SSH로 접속하여 점검, 패치, 사고 대응을 수행한다.

```bash
# 학생 PC 터미널에서 실행
sshpass -p1 ssh -o StrictHostKeyChecking=no opsclaw@10.20.30.201
# 비밀번호: 1
```

**예상 출력:**
```
opsclaw@10.20.30.201's password: (1 입력)
Welcome to Ubuntu 22.04.x LTS
Last login: ...
opsclaw@opsclaw:~$
```

**접속 확인:**
```bash
hostname
# 예상 출력: opsclaw

whoami
# 예상 출력: opsclaw

pwd
# 예상 출력: /home/opsclaw
```

> **왜 이렇게 하는가?**
> 모의해킹의 첫 단계는 공격 기지(opsclaw)에 접속하는 것이다. 실제 침투 테스트에서도
> 테스터는 고객이 제공한 VPN/SSH 접근을 통해 내부 네트워크에 진입한 후 작업을 시작한다.

### Step 2: 다른 서버에 SSH 접속

opsclaw에서 다른 서버로 접속한다.

```bash
# web 서버
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 'hostname && whoami'
# 예상 출력:
# web
# web

# secu 서버
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 'hostname && whoami'
# 예상 출력:
# secu
# secu

# siem 서버
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 'hostname && whoami'
# 예상 출력:
# siem
# siem
```

> **명령어 해설:**
> - `sshpass -p1`: 비밀번호 "1"을 자동 입력 (실습 편의, 실무에서는 키 기반 인증 사용)
> - `-o StrictHostKeyChecking=no`: 최초 접속 시 호스트 키 자동 수락
> - `web@10.20.30.80`: 사용자명@IP주소
> - `'hostname && whoami'`: 원격 서버에서 실행할 명령 (따옴표로 묶음)

> **트러블슈팅:**
> - "Connection refused": SSH 서비스가 꺼져 있거나 방화벽에서 차단
> - "Permission denied": 사용자명 또는 비밀번호 오류
> - "No route to host": 네트워크 경로 문제, IP 확인 필요

---

## 실습 3.2: 시스템 정보 수집 (상세)

### 운영체제 정보

```bash
# 현재 서버 (opsclaw)
cat /etc/os-release | head -4
# 예상 출력:
# PRETTY_NAME="Ubuntu 22.04.x LTS"
# NAME="Ubuntu"
# VERSION_ID="22.04"
# VERSION="22.04.x LTS (Jammy Jellyfish)"

# 커널 버전
uname -a
# 예상 출력: Linux opsclaw 6.8.0-106-generic #106-Ubuntu ... x86_64 GNU/Linux
# 해석: Linux [호스트명] [커널버전] ... [아키텍처]
```

> **왜 이렇게 하는가?**
> 운영체제와 커널 버전은 공격자가 가장 먼저 확인하는 정보다.
> 특정 커널 버전에 알려진 권한 상승 취약점(예: DirtyPipe CVE-2022-0847)이 있을 수 있다.
> Week 11에서 이 정보를 활용하여 권한 상승을 시도한다.

### 하드웨어 정보

```bash
# CPU 정보
echo "=== CPU ===" && nproc && echo "cores" && lscpu | grep "Model name"
# 예상 출력:
# === CPU ===
# 4
# cores
# Model name: Intel(R) Core(TM) ...

# 메모리 정보
echo "=== 메모리 ===" && free -h
# 예상 출력:
#                total    used    free    shared  buff/cache  available
# Mem:           7.8Gi    2.1Gi   3.2Gi   45Mi    2.5Gi       5.4Gi
# Swap:          2.0Gi    0B      2.0Gi

# 디스크 정보
echo "=== 디스크 ===" && df -h | grep -v tmpfs | grep -v loop
# 예상 출력:
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       50G   15G   33G  31% /
```

### 네트워크 정보

```bash
# IP 주소 확인
ip addr show | grep "inet " | grep -v 127.0.0.1
# 예상 출력:
#     inet 10.20.30.201/24 brd 10.20.30.255 scope global ens37
#     inet 192.168.208.142/24 brd 192.168.208.255 scope global ens33  ← 외부 인터페이스

# 라우팅 테이블
ip route show
# 예상 출력:
# default via 10.20.30.1 dev ens37
# 10.20.30.0/24 dev ens37 proto kernel scope link src 10.20.30.201

# 열린 포트 확인
ss -tlnp | head -20
# 예상 출력:
# State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
# LISTEN 0       128     0.0.0.0:8000         0.0.0.0:*          users:(("uvicorn",...))
# LISTEN 0       128     0.0.0.0:8002         0.0.0.0:*          users:(("uvicorn",...))
# LISTEN 0       128     0.0.0.0:22           0.0.0.0:*          users:(("sshd",...))
```

> **왜 이렇게 하는가?**
> 네트워크 정보는 공격 대상을 식별하는 핵심이다:
> - IP 주소: 어떤 네트워크에 속해 있는지 파악
> - 라우팅: 다른 서버에 어떻게 접근할 수 있는지 확인
> - 열린 포트: 어떤 서비스가 실행 중인지 (공격 표면 파악)

### 4개 서버 일괄 정보 수집 스크립트

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 모든 서버 정보를 한 번에 수집하는 스크립트
for server in "opsclaw@localhost" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do  # 반복문 시작
  user=$(echo $server | cut -d@ -f1)
  host=$(echo $server | cut -d@ -f2)
  echo "========================================"
  echo "=== $user @ $host ==="
  echo "========================================"
  if [ "$host" = "localhost" ]; then
    hostname && uname -r && echo "---" && free -h | head -2 && echo "---" && df -h / | tail -1
  else
    sshpass -p1 ssh -o StrictHostKeyChecking=no $server "hostname && uname -r && echo '---' && free -h | head -2 && echo '---' && df -h / | tail -1" 2>/dev/null  # 비밀번호 자동입력 SSH
  fi
  echo ""
done
```

---

## 실습 3.3: 네트워크 도구 실습

### ping — 연결 확인

```bash
# web 서버 연결 확인
ping -c 3 10.20.30.80
# 예상 출력:
# PING 10.20.30.80 (10.20.30.80) 56(84) bytes of data.
# 64 bytes from 10.20.30.80: icmp_seq=1 ttl=64 time=0.882 ms
# 64 bytes from 10.20.30.80: icmp_seq=2 ttl=64 time=0.654 ms
# 64 bytes from 10.20.30.80: icmp_seq=3 ttl=64 time=0.712 ms
# --- 10.20.30.80 ping statistics ---
# 3 packets transmitted, 3 received, 0% packet loss, time 2004ms
```

> **해석 포인트:**
> - `ttl=64`: TTL이 64이면 Linux 서버 (Windows는 보통 128)
> - `time=0.882 ms`: 응답 시간 (1ms 미만이면 같은 네트워크)
> - `0% packet loss`: 패킷 손실 없음 (연결 정상)

### curl — 웹 서버 접근

```bash
# JuiceShop 접근 확인
curl -s http://10.20.30.80:3000 | head -5
# 예상 출력: HTML 코드 (<!DOCTYPE html>...)

# HTTP 헤더만 확인
curl -s -I http://10.20.30.80:3000 | head -10
# 예상 출력:
# HTTP/1.1 200 OK
# X-Powered-By: Express
# Access-Control-Allow-Origin: *
# X-Content-Type-Options: nosniff
# ...

# Apache 웹 서버 확인
curl -s -I http://10.20.30.80:80 | head -5
# 예상 출력:
# HTTP/1.1 200 OK
# Server: Apache/2.4.xx (Ubuntu)
```

> **왜 이렇게 하는가?**
> 웹 서버의 응답 헤더에서 많은 정보를 얻을 수 있다:
> - `X-Powered-By: Express` → Node.js Express 프레임워크 사용
> - `Access-Control-Allow-Origin: *` → CORS 설정 개방 (보안 이슈 가능)
> - `Server: Apache/2.4.xx` → 웹 서버 소프트웨어와 버전

### 포트 스캔 — bash 기본 방법

```bash
# nmap 없이 bash로 포트 스캔
echo "=== web 서버 (10.20.30.80) 포트 스캔 ==="
for port in 22 80 443 3000 8002 8080 8081 8082 8443; do
    timeout 1 bash -c "echo >/dev/tcp/10.20.30.80/$port" 2>/dev/null \
      && echo "  $port: OPEN" \
      || echo "  $port: closed"
done
# 예상 출력:
#   22: OPEN
#   80: OPEN
#   443: closed
#   3000: OPEN
#   8002: OPEN
#   8080: closed
#   8081: OPEN
#   8082: OPEN
#   8443: closed
```

> **왜 bash로 하는가?**
> 실제 침투 테스트에서 nmap이 설치되어 있지 않은 경우가 많다.
> bash의 /dev/tcp를 이용하면 추가 도구 없이 포트를 확인할 수 있다.
> 이것은 "Living off the Land" 기법의 기초이다.

### nmap — 전문 포트 스캔

```bash
# 기본 스캔 (상위 1000개 포트)
nmap 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 3000/tcp open  ppp
# 8002/tcp open  teradataordbms
# 8081/tcp open  blackice-icecap
# 8082/tcp open  blackice-alerts

# 서비스 버전 탐지
nmap -sV -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE VERSION
# 22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.x
# 80/tcp   open  http    Apache httpd 2.4.xx
# 3000/tcp open  http    Node.js Express framework

# OS 탐지 (sudo 필요)
echo 1 | sudo -S nmap -O 10.20.30.80 2>/dev/null | grep "OS details"
# 예상 출력: OS details: Linux 5.x - 6.x
```

> **nmap 옵션 해설:**
> - `-sV`: 서비스 버전 탐지 (배너 그래빙)
> - `-p 22,80,3000`: 특정 포트만 스캔
> - `-O`: OS 탐지 (TCP/IP 스택 fingerprinting)
> - `-sS`: SYN 스캔 (스텔스, sudo 필요)
> - `-A`: 종합 스캔 (-sV -O -sC --traceroute)

> **⚠️ 법적 주의:**
> nmap은 강력한 도구이다. 허가 없는 대상에 사용하면 **불법**이다.
> 정보통신망 이용촉진 및 정보보호 등에 관한 법률 제48조 위반 시 5년 이하 징역.
> 본 실습에서는 교육용으로 구성된 내부 서버에서만 사용한다.

---

# Part 4: OpsClaw 플랫폼 실습 (30분)

## 4.1 OpsClaw이란?

OpsClaw는 보안 작업을 **자동화**하고 **기록**하는 오케스트레이션 플랫폼이다.

**핵심 가치:** 직접 SSH로 명령을 실행하면 아무런 기록도 남지 않는다. OpsClaw를 통해 실행하면:
- 모든 명령과 결과가 **evidence**(증적)로 자동 기록된다
- 각 태스크에 **보상(reward)**이 산출되어 성과를 추적한다
- **해시 체인**으로 기록의 무결성을 검증할 수 있다
- **Playbook**으로 동일 작업을 재현할 수 있다

```
직접 SSH 실행:    명령 → 결과 → (아무것도 남지 않음)
OpsClaw 경유:     명령 → 결과 → evidence + PoW블록 + reward + replay
```

## 4.2 OpsClaw 기본 워크플로

```
[1] 프로젝트 생성  POST /projects
[2] 계획 단계     POST /projects/{id}/plan
[3] 실행 단계     POST /projects/{id}/execute
[4] 태스크 실행   POST /projects/{id}/execute-plan 또는 /dispatch
[5] 결과 확인     GET  /projects/{id}/evidence/summary
[6] 완료 보고     POST /projects/{id}/completion-report
```

## 실습 4.1: 첫 OpsClaw 프로젝트

### Step 1: 프로젝트 생성

```bash
# 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week01-my-first-project","request_text":"Week 01 실습: 환경 파악","master_mode":"external"}')  # 요청 데이터(body)

# project_id 추출
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"
# 예상 출력: Project ID: prj_xxxxxxxx (고유 ID)
```

### Step 2: Stage 전환

```bash
# plan 단계로 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "import sys,json; print(json.load(sys.stdin).get('current_stage'))"
# 예상 출력: plan

# execute 단계로 전환
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "import sys,json; print(json.load(sys.stdin).get('current_stage'))"
# 예상 출력: execute
```

> **왜 stage 전환이 필요한가?**
> OpsClaw는 8단계 상태 머신으로 프로젝트를 관리한다.
> plan→execute 순서를 건너뛰면 400 에러가 발생한다.
> 이는 "계획 없이 실행하지 마라"라는 보안 운영 원칙의 구현이다.

### Step 3: 단일 명령 실행 (dispatch)

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# web 서버에서 hostname 실행
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"command":"hostname && uptime && uname -r","subagent_url":"http://10.20.30.80:8002"}' \
  | python3 -m json.tool
# 예상 출력: web 서버의 hostname, uptime, 커널 버전
```

### Step 4: 병렬 실행 (execute-plan)

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 4개 서버 동시 점검
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {"order":1,"title":"opsclaw 점검","instruction_prompt":"hostname && uptime && free -h | head -2","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"secu 점검","instruction_prompt":"hostname && uptime && free -h | head -2","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":3,"title":"web 점검","instruction_prompt":"hostname && uptime && free -h | head -2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":4,"title":"siem 점검","instruction_prompt":"hostname && uptime && free -h | head -2","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'전체 결과: {d[\"overall\"]}')
print(f'성공: {d[\"tasks_ok\"]}개, 실패: {d[\"tasks_failed\"]}개')
for t in d.get('task_results',[]):                     # 반복문 시작
    print(f'  [{t[\"order\"]}] {t[\"title\"]:15s} → {t[\"status\"]} (dur={t.get(\"duration_s\",\"?\")}s)')
"
# 예상 출력:
# 전체 결과: success
# 성공: 4개, 실패: 0개
#   [1] opsclaw 점검     → ok (dur=0.1xs)
#   [2] secu 점검        → ok (dur=0.1xs)
#   [3] web 점검         → ok (dur=0.1xs)
#   [4] siem 점검        → ok (dur=0.1xs)
```

> **핵심 개념: 병렬 실행**
> `"parallel":true`로 4개 서버에 동시에 명령을 보낸다.
> 순차 실행이면 ~0.6초 × 4 = 2.4초, 병렬이면 ~0.6초 (가장 느린 서버 기준).
> 서버가 10대, 100대로 늘어나도 병렬이면 시간이 거의 동일하다.

### Step 5: 증적 확인

```bash
# Evidence 요약
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
# 예상 출력:
# {
#     "total": 5,        ← 총 5건 기록 (dispatch 1 + execute-plan 4)
#     "success_count": 5,
#     "success_rate": 1.0
# }

# Replay (타임라인 재구성)
curl -s "http://localhost:8000/projects/$PID/replay" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'총 단계: {d[\"steps_total\"]}')
print(f'총 보상: {d[\"total_reward\"]}')
for s in d.get('timeline',[]):
    print(f'  [{s[\"task_order\"]}] {s[\"task_title\"]:15s} exit={s[\"exit_code\"]} reward={s[\"total_reward\"]}')
"
# 예상 출력: 각 태스크의 순서, 결과, 보상이 타임라인으로 표시
```

> **왜 증적이 중요한가?**
> 보안 작업에서 "무엇을 했는지" 증명할 수 없으면:
> 1. 감사(audit)에서 증거 불충분
> 2. 사고 발생 시 책임 소재 불명확
> 3. 동일 작업 재현 불가
> OpsClaw는 이 모든 것을 자동으로 해결한다.

---

# Part 5: 보안 윤리와 법적 책임 (20분)

## 5.1 모의해킹의 법적 근거

모의해킹은 **반드시 사전 서면 허가**가 있어야 합법이다.

| 구분 | 합법 | 불법 |
|------|------|------|
| 허가 | 고객과 서면 계약 체결 후 실행 | 허가 없이 타인 시스템 스캔/공격 |
| 범위 | 합의된 IP/도메인만 대상 | 범위 밖 시스템 접근 |
| 시간 | 합의된 기간 내 실행 | 계약 기간 외 활동 |
| 보고 | 발견사항을 고객에게 보고 | 발견한 취약점을 악용/유출 |

### 관련 법률 (한국)

| 법률 | 조항 | 내용 | 벌칙 |
|------|------|------|------|
| 정보통신망법 | 제48조 | 정보통신망 침입 금지 | 5년 이하 징역 |
| 정보통신망법 | 제49조 | 타인 비밀 침해 금지 | 5년 이하 징역 |
| 개인정보보호법 | 제71조 | 개인정보 부정 취득 | 5년 이하 징역/5천만원 벌금 |
| 형법 | 제316조 | 비밀침해 | 3년 이하 징역 |

## 5.2 이 수업에서의 규칙

1. **실습 서버에서만 작업한다** (10.20.30.0/24 네트워크)
2. **외부 시스템을 절대 스캔하거나 공격하지 않는다**
3. **발견한 취약점은 수업 내에서만 논의한다**
4. **다른 학생의 작업을 방해하지 않는다**
5. **모든 작업은 가능한 OpsClaw를 통해 실행하여 증적을 남긴다**

---

# Part 6: 복습 퀴즈 + 과제

## 자가 점검 퀴즈 (10문항)

**Q1.** CIA Triad에서 "인가된 사용자만 정보에 접근"하는 것은 어떤 요소인가?
- (a) Integrity  (b) Availability  (c) Confidentiality  (d) Authentication

**Q2.** MITRE ATT&CK에서 "Reconnaissance"는 무엇을 의미하는가?
- (a) 악성코드 실행  (b) 정보 수집  (c) 권한 상승  (d) 데이터 유출

**Q3.** CVE-2021-44228은 어떤 취약점인가?
- (a) SQL Injection  (b) Log4Shell  (c) Heartbleed  (d) Shellshock

**Q4.** nmap -sV 옵션은 무엇을 하는가?
- (a) OS 탐지  (b) 서비스 버전 탐지  (c) UDP 스캔  (d) 스텔스 스캔

**Q5.** OpsClaw에서 execute-plan 실행 전에 반드시 거쳐야 하는 단계는?
- (a) report → close  (b) plan → execute  (c) validate → close  (d) execute → report

**Q6.** OWASP Top 10 A03은 어떤 유형의 취약점인가?
- (a) 접근 제어 실패  (b) Injection  (c) 암호화 실패  (d) SSRF

**Q7.** 우리 실습에서 SIEM 역할을 하는 서버는?
- (a) opsclaw  (b) secu  (c) web  (d) siem

**Q8.** Defense in Depth의 핵심 원칙은?
- (a) 단일 방어를 강하게  (b) 여러 계층으로 방어 중첩  (c) 공격을 먼저  (d) 방화벽만 사용

**Q9.** 허가 없이 타인의 서버에 nmap 스캔을 하면?
- (a) 합법  (b) 정보통신망법 위반  (c) 윤리적 해킹  (d) 문제 없음

**Q10.** `sshpass -p1 ssh web@10.20.30.80 'hostname'`에서 `-p1`의 의미는?
- (a) 포트 1번  (b) 프로토콜 1  (c) 비밀번호 "1"  (d) 우선순위 1

**정답:** Q1:c, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:d, Q8:b, Q9:b, Q10:c

---

## 과제 (다음 주까지)

### 과제 1: 인프라 파악 보고서 (60점)

4개 서버(opsclaw, secu, web, siem)에 접속하여 다음 정보를 수집하고 보고서를 작성하라.

**수집 항목:**
| 항목 | 명령어 |
|------|--------|
| 운영체제/버전 | `cat /etc/os-release \| head -3` |
| 커널 | `uname -r` |
| CPU 코어 수 | `nproc` |
| 전체/사용 메모리 | `free -h` |
| 디스크 사용량 | `df -h /` |
| 열린 포트 | `ss -tlnp` |
| 주요 서비스 | `systemctl list-units --type=service --state=running` |

**제출 형식:**
```
[서버명] opsclaw (10.20.30.201)
  OS: Ubuntu 22.04.x
  커널: 6.8.0-106-generic
  CPU: 4 cores
  메모리: 7.8Gi total / 2.1Gi used
  디스크: 50G total / 15G used (31%)
  열린 포트: 22(ssh), 8000(manager-api), 8002(subagent)
  주요 서비스: ssh, uvicorn(manager), uvicorn(subagent), docker
```

**채점 기준:**
- 4개 서버 모두 수집 (각 15점)
- 정보의 정확성과 완전성

### 과제 2: OpsClaw 프로젝트 실행 (40점)

OpsClaw를 사용하여 과제 1의 정보 수집을 자동화하라.

**요구사항:**
1. 프로젝트 생성 (`POST /projects`) — 5점
2. stage 전환 (plan → execute) — 5점
3. execute-plan으로 4개 서버 병렬 점검 — 15점
4. evidence/summary 조회 결과 캡처 — 10점
5. replay 조회 결과 캡처 — 5점

**보너스 (10점):** 각 서버에서 `ss -tlnp`까지 수집하여, 전체 인프라의 열린 포트 목록표를 작성

---

## 검증 체크리스트

- [ ] 4개 서버에 SSH 접속 성공
- [ ] 각 서버의 hostname, OS, 커널 확인
- [ ] bash /dev/tcp로 포트 스캔 수행
- [ ] nmap으로 web 서버 스캔 성공
- [ ] curl로 JuiceShop (포트 3000) HTML 응답 확인
- [ ] curl로 Apache (포트 80) 헤더 확인
- [ ] OpsClaw 프로젝트 생성 성공
- [ ] OpsClaw dispatch 명령 실행 성공
- [ ] OpsClaw execute-plan 4개 서버 병렬 실행 성공
- [ ] OpsClaw evidence/summary 조회 성공
- [ ] OpsClaw replay 타임라인 확인
- [ ] 자가 점검 퀴즈 8/10 이상 정답

---

## 다음 주 예고
**Week 02: 정보수집과 정찰 (Reconnaissance)**
- nmap 고급 스캔 기법 (SYN, FIN, ACK, NULL 스캔)
- DNS 정보 수집 (dig, nslookup, 역방향 조회)
- 웹 서버 핑거프린팅 (whatweb, wappalyzer)
- 디렉토리/파일 열거 (gobuster, dirb)
- robots.txt, sitemap.xml 분석
- Google Dorking 기법
- OpsClaw로 정찰 자동화

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

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
