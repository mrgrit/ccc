# W01 — 웹 보안 개요 + OWASP Top 10 + 6v6 의 7 vuln vhost 가시화

> **본 주차의 한 줄 요약**
>
> 웹 보안 의 *전체 지도* 를 그린다. OWASP Top 10 (2021) 의 10 카테고리 + CWE Top 25
> 의 매핑 + 6v6 환경 의 7 vuln vhost (JuiceShop / DVWA / NeoBank / GovPortal /
> MediForum / AdminConsole / AICompanion) 의 가시화 + ModSec CRS 4.0 의 20 rule
> family 의 *방어 측 도구* 인지. 본 주차 가 14 weeks 의 *학습 backbone*.
>
> **운영자 한 줄 결론**: 웹 의 *공격 면* 은 OWASP Top 10 의 10 카테고리. *방어 면*
> 은 WAF (ModSec) + 인증/세션 + 데이터 무결성 의 3 축. 본 과목 은 *공격 → 탐지 →
> 방어* 의 3 단계 hands-on.

---

## 학습 목표

본 주차 종료 시 학생은 다음 7 가지 를 **본인 손으로** 할 수 있어야 한다.

1. 웹 의 *6 핵심 통신 흐름* (브라우저 → DNS → HTTP → 서버 → DB → 응답) + 각 단계 의
   *공격 면* 인지.
2. OWASP Top 10 (2021) 10 카테고리 의 *이름 + 핵심 CWE + 발생 빈도* 30 초 내 응답.
3. CWE Top 25 의 *상위 10* 의 의미 + OWASP 와 의 *중복 영역* 인지.
4. 6v6 의 7 vuln vhost 모두 *실 응답* + 각 의 *주요 vuln 카테고리* 인지.
5. ModSec CRS 4.0 의 *20 rule family* + *paranoia level* 1-4 의 *trade-off* 인지.
6. 본 과목 의 14 weeks 학습 계획서 의 *5 영역 자가 진단* + *졸업 목표 구체*.
7. 본인 의 *학습 환경 의 RoE* (Rules of Engagement) — 학습 환경 만, 외부 거부.

---

## 강의 시간 배분 (3시간 30분)

| 차시 | 주제 | 시간 |
|:----:|------|------|
| 1차시 | 웹 보안 의 전체 지도 + 6 핵심 통신 흐름 + 공격 면 | 50 분 |
| 2차시 | OWASP Top 10 (2021) 10 카테고리 + CWE Top 25 | 60 분 |
| 3차시 | ModSec CRS 4.0 의 20 rule family + 6v6 의 적용 | 50 분 |
| 4차시 | 학습 계획 + RoE + 자가 진단 | 30 분 |
| 휴식 | 차시 사이 + 마지막 | 20 분 |

---

## 0. 용어 해설 (먼저 인지)

본 과목 에서 가장 자주 등장 하는 *15 용어* 의 한 줄 정의. 모든 lab + lecture 의
전제.

| # | 용어 | 한 줄 정의 |
|:-:|------|----------|
| 1 | **OWASP** | Open Web Application Security Project — 비영리, 표준 보안 가이드 |
| 2 | **OWASP Top 10** | 가장 위험 한 10 web vuln 카테고리. 3 년 주기 갱신 |
| 3 | **CWE** | Common Weakness Enumeration — MITRE 의 weakness 분류 |
| 4 | **CVE** | Common Vulnerabilities and Exposures — 실 발견 된 취약점 식별자 |
| 5 | **WAF** | Web Application Firewall — HTTP 트래픽 의 *공격 패턴* 차단 |
| 6 | **ModSec** | Apache 의 WAF module (most popular open-source WAF) |
| 7 | **CRS** | Core Rule Set — OWASP 의 표준 ModSec 룰셋 (현재 4.0) |
| 8 | **paranoia level** | CRS 의 *엄격도* (1=production / 4=stricter) |
| 9 | **anomaly score** | CRS 의 *위험도 점수* (5+ = 차단 default) |
| 10 | **vhost** | virtual host — HAProxy/Apache 의 *호스트 헤더* 별 라우팅 |
| 11 | **HAProxy** | TCP/HTTP load balancer (6v6 의 fw 컨테이너) |
| 12 | **PTES** | Penetration Testing Execution Standard — 침투 7 단계 |
| 13 | **ATT&CK** | MITRE 의 *공격자 행동* 분류 (Tactic + Technique) |
| 14 | **payload** | 공격 요청 의 *실제 위험 코드* (예: `' OR 1=1--`) |
| 15 | **RoE** | Rules of Engagement — 침투 의 *허용 범위* (학습 환경 만) |

---

## 1차시 — 웹 보안 의 전체 지도 + 6 핵심 통신 흐름

### 1-1. 왜 웹 이 가장 자주 공격 받는가

전 세계 의 사이버 공격 의 **80%+ 가 웹 을 시작점** 으로 한다 (Verizon DBIR 2024).
이유 는 3 가지:

1. **모든 회사 가 웹 을 사용**: 회사 사이트 / 로그인 / API / 결제 — 외부 노출 가
   가장 많은 시스템.
2. **공격 면 이 다양**: HTTP 헤더 / URL / 파라미터 / 쿠키 / JSON body / WebSocket
   등 *입력 경로* 가 매우 많음.
3. **취약점 패턴 이 표준화 가능**: SQL injection / XSS 같은 *패턴 화* 된 공격 이
   가능 — 자동화 도구 (sqlmap / Burp / OWASP ZAP) 가 잘 발달.

본 과목 은 *80% 를 차지하는 웹 공격 의 모든 카테고리* 를 14 weeks 에 *공격 측 +
방어 측* 양면 학습.

### 1-2. 웹 의 6 핵심 통신 흐름

학생 이 *www.example.com* 의 로그인 페이지 에 *id 입력 + 비밀번호 입력 + 로그인
버튼 클릭* 시 발생 하는 6 단계. 각 단계 가 *공격 면*.

```
  ① 브라우저 → ② DNS 조회 → ③ TCP 연결 + TLS handshake →
  ④ HTTP 요청 → ⑤ 서버 의 처리 (인증 / DB) → ⑥ HTTP 응답
```

각 단계 의 *대표 공격*:

| 단계 | 정상 동작 | 공격 면 | OWASP 매핑 |
|:----:|---------|--------|----------|
| ① 브라우저 | URL 입력 / 폼 제출 | XSS — 응답 의 악성 JS 실행 | A03 |
| ② DNS | example.com → IP | DNS hijack / cache poisoning | A05 |
| ③ TCP+TLS | TLS handshake / cert 검증 | TLS downgrade / weak cipher | A02 |
| ④ HTTP 요청 | GET /login + body | SQLi / XSS / SSRF / IDOR 의 payload | A01-A10 |
| ⑤ 서버 처리 | DB query / 인증 / 세션 | Auth bypass / IDOR / 권한 우회 | A01 / A07 |
| ⑥ HTTP 응답 | HTML / JSON / 200 | 정보 노출 / 헤더 누락 / 캐싱 결함 | A04 / A05 |

본 과목 의 14 weeks 의 *대부분* 이 *④ HTTP 요청* + *⑤ 서버 처리* 단계 의 공격
다룬다. ②/③/⑥ 은 *심화* (network security 또는 cryptography 별 과목).

### 1-3. 웹 의 3 계층 모델 (학생 친화 비유)

웹 서비스 의 3 계층 — *프론트엔드 + 백엔드 + 데이터베이스*. 학생 이 *식당* 비유로
이해.

```
  [브라우저]            ←  손님 (학생)
    ↓
  [Frontend (HTML/JS)] ←  메뉴판 + 종업원 (주문 받음)
    ↓
  [Backend (서버)]     ←  주방 (요리 만듦)
    ↓
  [Database]           ←  창고 (식재료 저장)
```

각 계층 의 *대표 공격*:

| 계층 | 식당 비유 | 대표 공격 |
|------|---------|---------|
| Frontend | 메뉴판 변조 | XSS (메뉴 에 악성 코드 삽입) |
| Backend | 주방 의 명령 변조 | RCE (주방 에 *나쁜 요리* 시킴) |
| Database | 창고 의 데이터 절도 | SQLi (창고 의 *모든 데이터* 조회) |

본 과목 의 *공격 측* 은 *각 계층* 의 *입력 변조* — 공격자 가 *주문지 / 명령 / 쿼리* 를 변조 → 서버 가 *예상 외* 동작 → 데이터
유출 / 권한 우회 / 코드 실행.

### 1-4. 실 사고 사례 — 한국 의 web 공격 3 종

학생 의 이해 를 위 한국 의 *실 사고 3 종* (공개 자료, KISA 보고).

**사례 1 (2023-04): 대학교 학적 시스템 의 SQLi → 학생 정보 5 만 건 유출**
- 공격 면: 학생 검색 페이지 의 `학번` 파라미터
- payload: `1' OR '1'='1`
- 영향: 학생 5 만 명 의 이름 + 학번 + 주소 + 전화 노출
- 본 과목 매핑: W04 (SQLi + sqlmap) 의 실습 대상

**사례 2 (2023-09): 금융 회사 의 JWT alg=none → 무권한 출금 시도**
- 공격 면: 모바일 앱 의 JWT 토큰 의 *header* 변조
- payload: `{"alg":"none","typ":"JWT"}` + 임의 payload
- 영향: 시도 만 — 서버 측 검증 추가 후 차단
- 본 과목 매핑: W03 (Cryptographic Failures) 의 실습 대상

**사례 3 (2024-02): 공공 기관 의 SSRF → 내부 metadata 노출**
- 공격 면: 이미지 URL 입력 폼 (썸네일 생성)
- payload: `http://169.254.169.254/latest/meta-data/` (AWS metadata)
- 영향: AWS IAM credentials 노출 → 내부 S3 buckets 의 *주민등록번호 의 평문 csv*
  발견 → 즉시 차단 + 키 회전 + 분기 별 모의해킹 의무화
- 본 과목 매핑: W13 (SSRF) 의 실습 대상

3 사례 의 *공통 패턴* — **사용자 입력 의 무검증** + **권한 / 인증 의 허술** +
**로그 의 부재**. 본 과목 의 14 weeks 가 *각 패턴* 의 *원인 → 탐지 → 방어* 의
hands-on.

---

## 2차시 — OWASP Top 10 (2021) 의 10 카테고리 + CWE Top 25

### 2-1. OWASP Top 10 의 *역할*

OWASP Top 10 은 *전 세계 web 보안 의 공용 어휘*. 회사 의 보안 정책 / 침투 보고서 /
취업 면접 의 표준 질문. 본 과목 졸업 = **A01~A10 의 이름 + CWE + 본인 환경 의 적용
30 초 응답 가능**.

### 2-2. A01 — Broken Access Control (94% 응용프로그램 발견)

가장 흔한 vuln. **인증 후 의 권한 검증 실패**.

| 대표 패턴 | 예시 |
|---------|------|
| IDOR (Insecure Direct Object Reference) | `/api/Users/2` 의 *본인 외* user 조회 |
| Path Traversal | `?file=../../etc/passwd` 의 시스템 파일 접근 |
| Force Browsing | `/admin/secret` 직접 입력 → 권한 검사 누락 |
| 방법 변경 | `GET /user/1` → `DELETE /user/1` 검증 없음 |

**6v6 의 실습 대상**: JuiceShop 의 `/api/Users` IDOR + DVWA 의 Path Traversal.

### 2-3. A02 — Cryptographic Failures (이전 명: Sensitive Data Exposure)

암호화 결함 — *약한 알고리즘 / 키 노출 / TLS 결함*.

| 대표 패턴 | 예시 |
|---------|------|
| 약한 hash | MD5 / SHA1 의 *비밀번호 해시* — rainbow table 가능 |
| 약한 cipher | TLS 의 RC4 / 3DES — 2020 deprecated |
| 키 hardcode | 코드 의 `API_KEY="abc123"` git push |
| JWT alg=none | 토큰 검증 우회 — 본 과목 W03 의 hands-on |

**6v6 의 실습 대상**: JuiceShop JWT (alg=none / RS256 confusion) + NeoBank 의
session cookie 분석.

### 2-4. A03 — Injection (이전 #1 → #3, 단 *영향 도* 최고)

*사용자 입력* 이 *명령 / 쿼리* 로 *실행*. 가장 *영향 큰* 카테고리.

| 종류 | 예시 |
|------|------|
| SQL Injection | `' OR '1'='1` — DB 의 모든 데이터 조회 |
| Command Injection | `; cat /etc/passwd` — OS 명령 실행 |
| XSS (Cross-Site Scripting) | `<script>fetch('/api/data')</script>` — 브라우저 실행 |
| LDAP / NoSQL / XPath Injection | 각 query 언어 의 syntax |

**6v6 의 실습 대상**: DVWA SQLi + AdminConsole NoSQL + MediForum XSS + JuiceShop
Command Injection.

### 2-5. A04 — Insecure Design (2021 신규)

*설계 단계* 의 결함. *코드 가 아닌 architecture* 의 문제.

| 예시 | 의미 |
|------|------|
| 송금 시 *2FA 없음* | 비밀번호 만 으로 송금 가능 |
| 비밀번호 재설정 *질문* 의 *유추 가능* | "어머니 성함" — 공개 정보 |
| 결제 *서버 측 가격 검증* 없음 | `price=0` body 변조 가능 |
| API rate limit 없음 | brute force 무한 시도 |

**6v6 의 실습 대상**: NeoBank 의 *송금 workflow* 분석 + GovPortal 의 *비밀번호
재설정* 의 logic flaw.

### 2-6. A05 — Security Misconfiguration

*설정 의 default 또는 약함*. *모든 시스템* 에 적용.

| 예시 | 의미 |
|------|------|
| Apache default page | `/server-status` 노출 |
| TLS *self-signed cert* 의 production 사용 | 신뢰 X |
| `X-Frame-Options` 누락 | clickjacking 가능 |
| `X-Content-Type-Options` 누락 | MIME 추론 공격 |

**6v6 의 실습 대상**: 7 vhost 의 *HTTP 헤더 매트릭스* 분석.

### 2-7. A06 — Vulnerable and Outdated Components

*외부 라이브러리* 의 *알려진 vuln 사용*. *직접 코드 X*.

| 예시 | 의미 |
|------|------|
| 오래 된 jQuery (XSS vuln) | npm audit / retire.js 의 탐지 |
| Log4Shell (Log4j 2.0-2.14) | 2021 의 *역대 최대* 취약점 |
| Spring4Shell (Spring Framework) | 2022 의 RCE |
| `npm install` 의 *malicious package* | dependency confusion |

**6v6 의 실습 대상**: JuiceShop 의 `npm audit` + 본 과목 W11 의 *dependency
confusion 시뮬*.

### 2-8. A07 — Identification and Authentication Failures

*인증 의 결함*. *brute force / session / MFA bypass*.

| 예시 | 의미 |
|------|------|
| 비밀번호 brute force 의 *rate limit 없음* | hydra 의 무한 시도 |
| session ID 의 *예측 가능* | 1, 2, 3, 4 … 의 순차 |
| MFA bypass — *복구 코드* 의 약함 | 4 자리 숫자 |
| 비밀번호 재설정 의 *예전 토큰 의 reuse* | TOCTOU |

**6v6 의 실습 대상**: JuiceShop login 의 hydra brute + GovPortal MFA bypass 시뮬.

### 2-9. A08 — Software and Data Integrity Failures

*무결성 검증 없음*. *공급망 + deserialization + auto-update* 의 결함.

| 예시 | 의미 |
|------|------|
| Java deserialization | `readObject()` 의 *클래스 자유 인스턴스화* |
| auto-update *서명 X* | malicious update 의 자동 적용 |
| supply chain (xz-utils 2024) | npm/PyPI 의 *변조 package* |
| CI/CD *signing 없음* | 빌드 의 *임의 변조* |

**6v6 의 실습 대상**: W11 (xz-utils 사례 분석 + npm dependency confusion 시뮬).

### 2-10. A09 — Security Logging and Monitoring Failures

*로그 / 모니터 의 부재*. 사고 발생 시 *추적 불가*.

| 예시 | 의미 |
|------|------|
| 로그인 실패 *log X* | brute force 의 *탐지 불가* |
| ModSec audit log *비활성* | WAF 차단 *추적 불가* |
| SIEM 미설치 | 실시간 분석 *불가* |
| 보존 *7 일 미만* | 사고 *과거 분석 불가* |

**6v6 의 실습 대상**: ModSec audit log 의 분석 + Wazuh 통합 + 보존 정책.

### 2-11. A10 — Server-Side Request Forgery (SSRF) (2021 신규)

*서버* 가 *공격자 의 의도* 로 *내부 요청*. *cloud metadata 노출* 의 주 원인.

| 예시 | 의미 |
|------|------|
| 이미지 URL 입력 → `http://169.254.169.254/...` | AWS metadata 의 IAM credentials |
| webhook URL → 내부 admin API | 외부 우회 의 권한 |
| URL preview → 내부 redis (`http://localhost:6379/`) | 내부 service 노출 |

**6v6 의 실습 대상**: AdminConsole 의 SSRF + AWS metadata 시뮬.

### 2-12. CWE Top 25 — OWASP 와 의 차이

CWE Top 25 = MITRE 의 *weakness 분류*. OWASP 와 *부분 중복* + *추가 영역*.

| 상위 5 CWE | 이름 | OWASP 매핑 |
|----------|------|----------|
| CWE-79 | XSS | A03 |
| CWE-787 | Out-of-bounds Write | (system) |
| CWE-89 | SQL Injection | A03 |
| CWE-416 | Use After Free | (system) |
| CWE-78 | OS Command Injection | A03 |

OWASP 가 *web 특화* 면, CWE 는 *전체 소프트웨어* (web + native + kernel). 본 과목
은 *OWASP 중심* + CWE 의 *web 관련 25 종* 만.

---

## 3차시 — ModSec CRS 4.0 의 20 rule family + 6v6 의 적용

### 3-1. ModSec 의 *역할*

ModSec = *Apache 의 WAF module*. HTTP 요청 의 *공격 패턴* 사전 차단. 본 과목 의
*방어 측* 의 핵심.

**원리** = `SecRule` 의 *정규식 + 조건 + action*. 매칭 시 *anomaly score* 누적 →
임계 (5+) 시 차단.

```apache
SecRule REQUEST_URI "@rx (?i)select.*from" \
    "id:942100,phase:2,t:none,t:lowercase,setvar:tx.sql_injection_score=+5"
```

### 3-2. 6v6 의 ModSec 위치 — *fw 가 아닌 web*

**중요** — 6v6 의 ModSec 은 *fw 컨테이너* 가 아닌 **web 컨테이너** 에 위치.

- **fw**: HAProxy 만 (L4/L7 load balancer + SSL termination)
- **web**: Apache + ModSec + CRS (HTTP 의 *실 차단*)

**실측 (2026-05-16)**:
- `/usr/share/modsecurity-crs/rules/` — 20 family 의 conf 파일
- `/etc/modsecurity/crs/crs-setup.conf` — paranoia / anomaly 설정
- `/var/log/apache2/modsec_audit.log` — 19766 line (운영 누적)

### 3-3. CRS 4.0 의 20 rule family (실측)

```
901 init                    — CRS 초기화
903 exclusion before crs    — exclusion rule
905 common exception        — 흔한 false positive 예외
910 IP reputation           — IP 평판
911 method                  — HTTP method 제한
912 DOS                     — DDoS 패턴
913 scanner                 — nmap / nikto 등 도구 차단
920 protocol enforcement    — HTTP 표준
921 protocol attack         — request smuggling 등
930 LFI                     — Local File Inclusion
931 RFI                     — Remote File Inclusion
932 RCE                     — Remote Code Execution
933 PHP                     — PHP 특화 공격
934 deserialization         — Java/PHP deserialization
941 XSS                     — Cross-Site Scripting
942 SQLi                    — SQL Injection
943 session                 — session fixation
944 java                    — Java application attack
949 blocking                — anomaly score 의 *최종 차단 결정*
```

본 과목 의 *공격 측* 은 *각 family 의 우회* 시도. *방어 측* 은 *false positive 의
exception* 작성.

### 3-4. Paranoia Level — 의 *trade-off*

CRS 의 *엄격도* 1-4. 6v6 default = **1** (production safe).

| Level | 차단 비율 | False Positive | 운영 적합 |
|:-----:|---------|---------------|---------|
| 1 | 80% | < 1% | ✓ production default |
| 2 | 90% | 1-3% | finance / healthcare |
| 3 | 95% | 5-10% | classified / military |
| 4 | 99% | 10-30% | nuclear / national defense |

**Paradox** — *paranoia ↑* → *공격 차단 ↑* + *false positive ↑*. 실 운영 = *1
default + exception 추가* 의 hybrid.

### 3-5. Anomaly Score 의 *합산 로직*

CRS 4.0 = *anomaly score model* (이전 의 *threshold model* 대체). 각 룰 매칭 시
score 누적, *임계 도달* 시 차단.

```
임계 (default):
  Inbound (요청): 5
  Outbound (응답): 4
```

예시 — SQL injection 의 5 변형:
- 평문 `' OR '1'='1` → 942100 매칭 → +5 → 차단
- URL encoded `%27 OR %271%27=%271` → 942130 매칭 → +5 → 차단
- nested `' OR 1=1 -- ` → 942110 매칭 → +5 → 차단

각 변형 의 *별 룰* — *5 변형 모두 차단 OR 일부 통과* 가능.

### 3-6. 6v6 의 audit log 분석 baseline (19766 line)

본 과목 의 *방어 측* 의 시작 = audit log 의 *읽기*.

```
[2026-05-16T08:00:00.000+0900] AeOmABCDEFG 192.168.0.112 56789 10.20.32.80 80
--AeOmABCDEFG-A--
[16/May/2026:08:00:00 +0900] ... GET /?file=../../etc/passwd HTTP/1.1
--AeOmABCDEFG-H--
Message: Access denied with code 403 ... [id "930100"]
ModSecurity: Warning. detected SQLi using libinjection [id "942100"]
```

각 record = *한 차단 또는 의심 event*. 본 과목 의 *분석 도구* = grep / jq / awk.

---

## 4차시 — 학습 계획 + RoE + 자가 진단

### 4-1. 14 weeks 의 학습 지도

본 과목 의 14 weeks (W02-W15) 의 *전체 흐름*:

```
[W02-W07] 공격 측 — A01 ~ A05 (가장 흔한 5)
    ↓
[W08] 중간고사 — W01-W07 종합
    ↓
[W09-W13] 공격 측 — A06 ~ A10 (심화 5)
    ↓
[W14] 심화 — API Security Top 10 (2023)
    ↓
[W15] 기말 — 7 vhost 종합 침투 + PTES 보고서
```

각 weekly = *lecture 4 차시 + lab 5-7 step*. 평균 *주 5-10 시간* 학습.

### 4-2. 자가 진단 — 5 영역

본인 의 *현재 수준* 측정. 본 과목 의 *맞춤 학습* 의 input.

```
[ ] OWASP Top 10 인지: ____% (0-100)
    - 0-25%: 입문 — lecture 정독 + lab 의 *기본 step* 우선
    - 25-75%: 중급 — lab 의 *우회* + *심화* 우선
    - 75%+: 심화 — *본인 의 도구* 작성 + GitHub PoC 분석

[ ] SQLi / XSS 실습 경험: 횟수 ___
    - 0 회: W04-W05 의 *모든 step* 정성껏
    - 5-10 회: W04-W05 의 *변형 + 우회* 우선
    - 10+ 회: W04-W05 *스킵 가능* + W11/W13 의 *심화* 우선

[ ] JWT / session 분석 경험: 횟수 ___
[ ] 모의해킹 도구 (sqlmap / Burp / OWASP ZAP) 사용: 횟수 ___
[ ] 보고서 작성 경험: 횟수 ___
```

### 4-3. RoE — 학생 의 *평생 책임*

본 과목 의 *모든 hands-on* 은 **학습 환경 의 6v6 + 본인 자산** 만. 외부 시스템
의 *시도 절대 금지*.

**한국 법 (2024 기준)**:
- **정보통신망법 제48조** — *허가 없는 침투* = 5 년 이하 징역 또는 5천만원 이하 벌금
- **개인정보보호법** — *개인정보 무단 수집* = 5 년 이하 징역 또는 5천만원 이하 벌금
- **부정경쟁방지법** — *영업 비밀 의 부정 취득* = 10 년 이하 징역 또는 5억원 이하
  벌금

**본 과목 의 *명시 적 RoE***:
- ✅ 6v6 의 7 vhost (`*.6v6.lab`) — 학습 환경
- ✅ 본인 의 학습 PC / VM — 본인 자산
- ❌ 외부 회사 / 공공 기관 / 친구 의 서버 — 모두 거부
- ❌ HackerOne / Bugcrowd 외 — 사전 인가 없는 시도 거부
- ❌ 본인 의 *재학 학교 의 시스템* — 학교 의 사전 인가 없으면 거부

### 4-4. 졸업 목표 — 본인 구체

본 과목 졸업 시점 의 *측정 가능* 목표:

```
1. W15 기말 의 PTES 보고서 ___ 점 (목표: 80+)
2. 본인 의 *학습 도구* 1 종 작성 (예: JWT 변조 자동화 Python)
3. GitHub 의 *learn-by-doing* repo (PoC + writeup) ___ 개 (목표: 3+)
4. 본인 의 *학습 환경 의 vuln 발견* 1 회 (학교 의 사전 인가 후)
5. HackerOne / Bugcrowd 의 *프로필* 생성 (참여 X — 학습 만)
```

### 4-5. 다음 주차 (W02) 예고

W02 = **A01 Broken Access Control + IDOR + JWT**. JuiceShop 의 `/api/Users` IDOR
+ JWT 토큰 의 *3 부분* (header / payload / signature) 분석 + alg=none 우회 시도.

본 주차 의 lab step 4 의 *학습 계획서* 가 W02 의 *준비 점검* — 의 *완성* 여부 가
W02 의 *효과* 결정.

---

## 본 주차 정리

본 W01 을 마치면 학생 은:

1. ✅ 웹 보안 의 *전체 지도* + 6 핵심 통신 흐름 + 공격 면 인지
2. ✅ OWASP Top 10 (2021) 10 카테고리 의 이름 + CWE + 6v6 vhost 매핑
3. ✅ ModSec CRS 4.0 의 20 family + paranoia level + audit log 분석 baseline
4. ✅ 14 weeks 학습 계획서 + 자가 진단 + 졸업 목표
5. ✅ RoE 의 *평생 책임* 인지 + 한국 법 3 종 (정보통신망 / 개인정보 / 부정경쟁)

---

## 자기 점검

본 주차 의 *5 자기 평가 질문* — 모두 *yes* 면 W02 진입 가능. 1 개 라도 *no* 면
해당 영역 *재 학습* 권장.

```
[ ] OWASP Top 10 (2021) 의 10 카테고리 이름 + 각 의 핵심 CWE 30 초 내 응답?
[ ] 6v6 의 7 vhost 의 *URL + 주요 vuln 카테고리* 매트릭스 작성?
[ ] ModSec CRS 의 20 family 중 *XSS / SQLi / LFI / RCE / SSRF* 5 족 의 family
    ID 응답?
[ ] paranoia level 1-4 의 *trade-off* (차단 % vs false positive %) 응답?
[ ] 본인 학습 계획서 (5 영역 자가 진단 + 14 weeks 시간 + 졸업 목표) 작성?
```

---

## 다음 주차 — W02

**W02 — A01 Broken Access Control + IDOR + JWT** (JuiceShop hands-on).

- lecture: IDOR 5 패턴 + JWT 3 segment + Bearer token 의 흐름
- lab 5 step: JuiceShop login → JWT decode → IDOR 시퀀스 → alg=none 변조 → 보고
- 예상 시간: 8 시간 (lecture 3 + lab 5)

