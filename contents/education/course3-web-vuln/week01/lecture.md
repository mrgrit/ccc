# Week 01: 웹취약점 점검 개론

## 학습 목표
- 해킹과 취약점 점검의 차이를 명확히 이해한다
- 취약점 점검의 법적 근거와 윤리적 기준을 파악한다
- OWASP Testing Guide 기반 점검 방법론의 전체 흐름을 이해한다
- 주요 취약점 점검 도구의 종류와 용도를 파악한다
- JuiceShop 실습 환경에 접속하여 구조를 탐색할 수 있다

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

## 용어 해설 (웹취약점 점검 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **취약점 점검** | Vulnerability Assessment | 시스템의 보안 약점을 체계적으로 찾는 활동 | 건물 안전 진단 |
| **모의해킹** | Penetration Testing | 실제 공격자처럼 취약점을 악용하여 검증 | 소방 훈련 (실제로 불을 피워봄) |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 0~10점 (9.0+ Critical) | 질병 위험 등급표 |
| **SQLi** | SQL Injection | SQL 쿼리에 악성 입력 삽입 | 주문서에 가짜 지시를 끼워넣기 |
| **XSS** | Cross-Site Scripting | 웹페이지에 악성 스크립트 삽입 | 게시판에 함정 쪽지 붙이기 |
| **CSRF** | Cross-Site Request Forgery | 사용자 모르게 요청을 위조 | 누군가 내 이름으로 송금 요청 |
| **SSRF** | Server-Side Request Forgery | 서버가 내부 자원에 요청하도록 조작 | 직원에게 기밀 문서를 가져오라 속이기 |
| **LFI** | Local File Inclusion | 서버의 로컬 파일을 읽는 취약점 | 사무실 서류함을 몰래 열람 |
| **RFI** | Remote File Inclusion | 외부 파일을 서버에 로드하는 취약점 | 외부에서 악성 서류를 사무실에 반입 |
| **RCE** | Remote Code Execution | 원격에서 서버 코드 실행 | 전화로 사무실 컴퓨터 조작 |
| **WAF 우회** | WAF Bypass | 웹 방화벽의 탐지를 피하는 기법 | 보안 검색대를 우회하는 비밀 통로 |
| **인코딩** | Encoding | 데이터를 다른 형식으로 변환 (URL, Base64 등) | 택배 재포장 (내용물은 같음) |
| **난독화** | Obfuscation | 코드를 읽기 어렵게 변환 (탐지 회피) | 범인이 변장하는 것 |
| **세션** | Session | 서버가 사용자를 식별하는 상태 정보 | 카페 단골 인식표 |
| **쿠키** | Cookie | 브라우저에 저장되는 작은 데이터 | 가게에서 받은 스탬프 카드 |
| **Burp Suite** | Burp Suite | 웹 보안 점검 프록시 도구 (PortSwigger) | 우편물 검사 장비 |
| **OWASP ZAP** | OWASP ZAP | 오픈소스 웹 보안 스캐너 | 무료 보안 검사 장비 |
| **점검 보고서** | Assessment Report | 발견된 취약점과 대응 방안을 정리한 문서 | 건물 안전 진단 보고서 |

---

# Week 01: 웹취약점 점검 개론

## 학습 목표
- 해킹과 취약점 점검의 차이를 명확히 이해한다
- 취약점 점검의 법적 근거와 윤리적 기준을 파악한다
- OWASP Testing Guide 기반 점검 방법론의 전체 흐름을 이해한다
- 주요 취약점 점검 도구의 종류와 용도를 파악한다
- JuiceShop 실습 환경에 접속하여 구조를 탐색할 수 있다

## 전제 조건
- Course 1 (모의해킹 기초) 수강 완료 또는 동등 수준
- HTTP 프로토콜 기본 이해 (GET/POST, 상태 코드, 헤더)
- 리눅스 터미널에서 curl 명령어 사용 경험
- 실습 인프라 SSH 접속 가능

---

## 1. 해킹 vs 취약점 점검 (30분)

### 1.1 해킹이란?

**해킹(Hacking)**은 넓은 의미에서 시스템의 기술적 취약점을 이용하여 의도하지 않은 동작을 유발하는 행위이다. 그러나 일반적으로 "해킹"이라 하면 **불법적인 침입 행위**를 떠올린다.

### 1.2 취약점 점검이란?

**취약점 점검(Vulnerability Assessment)**은 시스템의 보안 약점을 **합법적으로, 체계적으로** 찾아내어 보고하는 전문 활동이다.

### 1.3 핵심 차이

| 구분 | 해킹 (불법) | 취약점 점검 (합법) |
|------|-----------|-----------------|
| **목적** | 정보 탈취, 파괴, 금전적 이익 | 보안 강화, 취약점 발견 및 수정 |
| **권한** | 무단 접근 | **사전 서면 허가** 필수 |
| **범위** | 제한 없음 | 계약서에 정의된 범위만 |
| **시간** | 공격자 마음대로 | 합의된 일정 내 |
| **결과** | 피해 발생 | **보고서** 작성 → 보안 개선 |
| **법적 지위** | **범죄** (형사 처벌 대상) | **합법** (계약에 의거) |
| **산출물** | 없음 (흔적 제거) | 취약점 보고서, 조치 권고안 |

### 1.4 취약점 점검의 종류

```
취약점 점검 (Vulnerability Assessment)
+-- 자동 스캔 (Automated Scanning)
|   +-- 도구를 사용한 대규모 자동 점검
|       예: Nessus, OpenVAS, nikto
|
+-- 수동 점검 (Manual Testing)
|   +-- 전문가가 직접 분석하는 정밀 점검
|       예: Burp Suite를 이용한 파라미터 변조
|
+-- 모의해킹 (Penetration Testing)
    +-- 실제 공격자 관점에서 침투 시도
        예: SQL Injection으로 DB 접근 --> 권한 상승
```

> **중요**: 취약점 점검은 "취약점을 찾는 것"이 목적이고, 모의해킹은 "취약점을 이용하여 실제로 어디까지 침투 가능한지 증명"하는 것이 목적이다.

---

## 2. 법적 프레임워크 (30분)

> **이 실습을 왜 하는가?**
> "웹취약점 점검 개론" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 왜 법을 알아야 하는가?

취약점 점검 전문가에게 법적 지식은 **선택이 아닌 필수**이다. 아무리 좋은 의도라도 법적 근거 없이 타인의 시스템을 점검하면 **범죄**가 된다.

### 2.2 대한민국 관련 법률

#### (1) 정보통신망 이용촉진 및 정보보호 등에 관한 법률 (정보통신망법)

**제48조 (정보통신망 침해행위 등의 금지)**

```
① 누구든지 정당한 접근권한 없이 또는 허용된 접근권한을
   넘어 정보통신망에 침입하여서는 아니 된다.

② 누구든지 정당한 사유 없이 정보통신시스템, 데이터
   또는 프로그램 등을 훼손·멸실·변경·위조하거나 그
   운용을 방해할 수 있는 프로그램을 전달 또는 유포하여서는
   아니 된다.
```

**벌칙**: 5년 이하 징역 또는 5천만원 이하 벌금

> **핵심**: "정당한 접근권한" = 사전 서면 허가. 구두 허가만으로는 부족하다.

#### (2) 개인정보 보호법

- 취약점 점검 중 개인정보를 발견할 수 있다
- 발견한 개인정보를 수집/저장/유출하면 별도의 법적 책임
- 점검 결과 보고서에 개인정보가 포함되지 않도록 주의

#### (3) 전자금융거래법

- 금융기관 대상 취약점 점검 시 추가 규제 적용
- 금융감독원 규정에 따른 점검 기준 준수 필요

### 2.3 합법적 취약점 점검을 위한 필수 조건

```
합법적 점검 = 다음 4가지 모두 충족

1. ✅ 서면 허가 (점검 계약서 / ROE)
   → 고객사 대표 또는 권한 있는 자의 서명

2. ✅ 범위 명시
   → IP 대역, 도메인, 시스템 목록이 명확히 정의

3. ✅ 기간 명시
   → 시작일, 종료일, 점검 시간대 합의

4. ✅ 제한 사항 명시
   → DoS 테스트 가능 여부, 소셜 엔지니어링 포함 여부 등
```

### 2.4 ROE (Rules of Engagement)

ROE는 "교전 규칙"이라는 군사 용어에서 유래했으며, 취약점 점검에서는 **점검의 범위와 한계를 정의하는 문서**이다.

**ROE에 포함되어야 할 항목**:

| 항목 | 내용 예시 |
|------|---------|
| 점검 대상 | web 서버 (10.20.30.80), 포트 80/443/3000 |
| 점검 제외 대상 | siem 서버 (운영 중단 시 영향 큼) |
| 허용된 기법 | SQL Injection, XSS, CSRF 테스트 |
| 금지된 기법 | DoS/DDoS, 물리적 접근, 소셜 엔지니어링 |
| 점검 기간 | 2026-03-27 ~ 2026-04-10, 09:00-18:00 |
| 비상 연락처 | 고객사 보안팀장: 010-XXXX-XXXX |
| 데이터 처리 | 발견된 개인정보는 즉시 삭제, 보고서에 마스킹 |

> **이 수업의 실습**: 수업에서 제공하는 JuiceShop은 **의도적으로 취약하게 만든 교육용 앱**이며, 실습 인프라 내에서만 점검한다. 이것이 우리의 "ROE"이다.

---

## 3. 취약점 점검 방법론 (30분)

### 3.1 OWASP Testing Guide

**OWASP (Open Web Application Security Project)**는 웹 보안 분야의 대표적인 비영리 단체이다. OWASP Testing Guide는 웹 애플리케이션 보안 점검의 **사실상 표준(de facto standard)**이다.

### 3.2 점검 단계 (5단계)

```
Phase 1: 계획 (Planning)
  --> 범위 정의, ROE 작성, 팀 구성, 도구 준비
       |
       v
Phase 2: 정보 수집 (Reconnaissance)
  --> 대상 시스템 정보 수집 (기술 스택, 구조 파악)
       |
       v
Phase 3: 자동 스캔 (Automated Scanning)
  --> 도구를 이용한 대규모 취약점 스캔
       |
       v
Phase 4: 수동 점검 (Manual Testing)
  --> 자동 스캔으로 찾지 못한 취약점 수동 확인
  --> 비즈니스 로직 취약점, 인증/인가 우회 등
       |
       v
Phase 5: 보고서 작성 (Reporting)
  --> 발견 사항 문서화, 위험도 평가, 조치 권고안
```

### 3.3 각 단계 상세

#### Phase 1: 계획 (Planning)

| 활동 | 산출물 |
|------|-------|
| 고객과 미팅 | 요구사항 정의서 |
| 범위 확정 | 점검 대상 목록 (IP, URL, 기능) |
| ROE 작성 | 교전 규칙 문서 |
| 일정 수립 | 점검 일정표 |
| 도구 준비 | 도구 설치 및 설정 완료 |

#### Phase 2: 정보 수집 (Reconnaissance)

```
정보 수집
+-- 수동적 정보 수집 (Passive)
|   +-- WHOIS 조회
|   +-- DNS 정보 수집
|   +-- Google Dorking
|   +-- Shodan/Censys 검색
|
+-- 능동적 정보 수집 (Active)
    +-- 포트 스캔 (nmap)
    +-- 디렉토리 브루트포싱 (gobuster)
    +-- 기술 스택 식별 (Wappalyzer)
    +-- API 엔드포인트 탐색
```

#### Phase 3: 자동 스캔

자동화 도구로 알려진 취약점을 빠르게 탐색한다:
- **nikto**: 웹 서버 취약점 스캐너
- **OWASP ZAP**: 웹 앱 자동 스캐너
- **sqlmap**: SQL Injection 전용 도구
- **Nessus/OpenVAS**: 범용 취약점 스캐너

#### Phase 4: 수동 점검

자동 도구가 찾지 못하는 취약점을 전문가가 직접 확인한다:
- **비즈니스 로직 취약점**: 정상 기능을 악용 (예: 음수 금액 결제)
- **인증/인가 우회**: 다른 사용자의 데이터에 접근
- **경쟁 조건(Race Condition)**: 동시 요청으로 이상 동작 유발

#### Phase 5: 보고서 작성

| 섹션 | 내용 |
|------|------|
| 요약 (Executive Summary) | 경영진을 위한 1-2페이지 요약 |
| 점검 범위 및 방법 | 무엇을, 어떻게 점검했는지 |
| 발견 사항 | 각 취약점의 상세 설명 |
| 위험도 평가 | CVSS 점수, 비즈니스 영향도 |
| 재현 절차 | 취약점을 재현하는 단계별 설명 |
| 조치 권고안 | 취약점 수정 방법 |
| 부록 | 스크린샷, 로그 등 증거 자료 |

### 3.4 OWASP Top 10 (2021)

웹 애플리케이션에서 가장 흔하고 위험한 취약점 10가지:

| 순위 | 취약점 | 설명 |
|------|--------|------|
| A01 | **Broken Access Control** | 권한 없는 리소스에 접근 가능 |
| A02 | **Cryptographic Failures** | 암호화 부재 또는 취약한 암호화 |
| A03 | **Injection** | SQL, OS, LDAP 인젝션 |
| A04 | **Insecure Design** | 설계 단계의 보안 결함 |
| A05 | **Security Misconfiguration** | 잘못된 보안 설정 |
| A06 | **Vulnerable Components** | 취약한 라이브러리/프레임워크 사용 |
| A07 | **Authentication Failures** | 인증 메커니즘 결함 |
| A08 | **Software/Data Integrity** | 무결성 검증 부재 |
| A09 | **Logging/Monitoring Failures** | 로깅 부재로 공격 감지 불가 |
| A10 | **SSRF** | Server-Side Request Forgery |

---

## 4. 주요 취약점 점검 도구 (20분)

### 4.1 도구 분류

| 카테고리 | 도구 | 용도 | 라이선스 |
|---------|------|------|---------|
| **프록시** | Burp Suite | HTTP 트래픽 가로채기/변조 | Community(무료)/Pro(유료) |
| **프록시** | OWASP ZAP | 웹 앱 자동/수동 점검 | 오픈소스 (무료) |
| **웹 스캐너** | nikto | 웹 서버 취약점 스캔 | 오픈소스 |
| **SQL Injection** | sqlmap | SQL Injection 자동화 | 오픈소스 |
| **디렉토리 스캔** | gobuster | 숨겨진 경로/파일 탐색 | 오픈소스 |
| **범용 스캐너** | Nessus | 네트워크/웹 취약점 종합 스캔 | 유료 (Essentials 무료) |

### 4.2 Burp Suite (프록시 도구)

**Burp Suite**는 웹 취약점 점검에서 가장 많이 사용되는 도구이다.

```
브라우저 → Burp Suite (Proxy) → 웹 서버
           ↕
         가로채기/변조/분석
```

**주요 기능**:
- **Proxy**: HTTP 요청/응답 가로채기 및 변조
- **Scanner**: 자동 취약점 스캔 (Pro 버전)
- **Repeater**: 요청을 수정하여 반복 전송
- **Intruder**: 파라미터 변조 자동화 (퍼징)
- **Decoder**: 인코딩/디코딩 변환

### 4.3 OWASP ZAP

**ZAP(Zed Attack Proxy)**는 OWASP에서 개발한 무료 오픈소스 웹 보안 스캐너이다.

- Burp Suite와 유사한 프록시 기능
- **자동 스캔** 기능이 무료로 제공됨 (Burp는 Pro 필요)
- 스크립팅 지원 (Python, JavaScript)
- CI/CD 파이프라인에 통합 가능

### 4.4 nikto

**nikto**는 웹 서버의 알려진 취약점을 빠르게 스캔하는 도구이다.

```bash
# 기본 사용법
nikto -h http://대상서버                                   # 웹 서버 취약점 스캐너

# 출력 예시
+ Server: Apache/2.4.52
+ /admin: Admin login page found
+ /backup.sql: Database backup file found
```

### 4.5 sqlmap

**sqlmap**은 SQL Injection 취약점을 자동으로 탐지하고 악용하는 도구이다.

```bash
# 기본 사용법
sqlmap -u "http://대상/search?q=test" --batch

# 데이터베이스 목록 추출
sqlmap -u "http://대상/search?q=test" --dbs
```

> **주의**: sqlmap은 매우 강력한 도구이다. **반드시 허가된 대상에서만** 사용해야 한다.

---

## 5. 실습 1: JuiceShop 접속 및 기본 탐색 (30분)

### 5.1 JuiceShop이란?

**OWASP Juice Shop**은 OWASP에서 만든 **의도적으로 취약한 웹 애플리케이션**이다. 실제 온라인 쇼핑몰과 유사한 기능을 가지고 있으며, OWASP Top 10을 포함한 100개 이상의 취약점이 심어져 있다.

> JuiceShop는 **교육 목적으로 만들어진 앱**이다. 이 수업에서 실습 대상으로 사용한다.

### 5.2 웹 브라우저로 접속

웹 브라우저에서 다음 주소로 접속한다:

```
http://10.20.30.80:3000
```

메인 페이지에 과일 주스 상품 목록이 표시되면 정상이다.

### 5.3 curl로 접속 확인

opsclaw 서버 터미널에서:

> **실습 목적**: 취약점 점검 대상(JuiceShop)이 정상 동작하는지 확인하고, HTTP 응답 코드와 응답 시간을 측정하는 기본기를 익힌다.
>
> **배우는 것**: curl 명령으로 웹 서버 상태를 확인하는 방법과, HTTP 상태 코드(200/403/500 등)의 의미를 이해한다.
>
> **결과 해석**: HTTP 200은 정상 응답이다. 403은 접근 거부(WAF 차단 가능), 502/503은 서버 장애를 의미한다. 응답 시간이 1초 이상이면 성능 문제를 의심한다.
>
> **실전 활용**: 취약점 점검 시작 전 대상 웹 서비스의 가용성을 반드시 확인해야 한다. 서비스가 다운된 상태에서 점검하면 무의미하다.

```bash
# 기본 접속 테스트
curl -s -o /dev/null -w "HTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" http://10.20.30.80:3000/
```

**예상 출력**:
```
HTTP Status: 200
Response Time: 0.045s
```

### 5.4 HTTP 응답 헤더 분석

```bash
# 응답 헤더만 확인
curl -sI http://10.20.30.80:3000/
```

**예상 출력**:
```
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/html; charset=utf-8
...
```

> **보안 포인트**: `X-Powered-By: Express` 헤더가 노출되고 있다. 이 정보를 통해 공격자는 서버가 Node.js + Express로 구축되었음을 알 수 있다. 실제 운영 환경에서는 이 헤더를 제거해야 한다.

### 5.5 기술 스택 파악

```bash
# HTML 소스에서 기술 스택 힌트 찾기
curl -s http://10.20.30.80:3000/ | head -30

# JavaScript 프레임워크 확인
curl -s http://10.20.30.80:3000/ | grep -i "angular\|react\|vue" | head -5
```

JuiceShop은 **Angular** 프레임워크를 사용하는 SPA(Single Page Application)이다.

---

## 6. 실습 2: API 엔드포인트 탐색 (30분)

### 6.1 REST API 발견

JuiceShop은 프론트엔드(Angular)와 백엔드(Express API)가 분리된 구조이다. API 엔드포인트를 찾아보자.

```bash
# 상품 목록 API
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -30
```

**예상 출력**:
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "name": "Apple Juice (1000ml)",
            "description": "The all-time...",
            "price": 1.99,
            "deluxePrice": 0.99,
            "image": "apple_juice.jpg"
        },
        ...
    ]
}
```

### 6.2 사용자 관련 API 탐색

```bash
# 사용자 등록 페이지 확인
curl -s -o /dev/null -w "Status: %{http_code}\n" http://10.20.30.80:3000/#/register

# 로그인 API 구조 확인 (빈 요청)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | python3 -m json.tool           # 요청 데이터(body)
```

### 6.3 검색 기능 탐색

```bash
# 검색 API 테스트
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -m json.tool | head -20

# 빈 검색어
curl -s "http://10.20.30.80:3000/rest/products/search?q=" | python3 -m json.tool | head -20
```

### 6.4 알려진 경로 탐색

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 관리자 페이지 존재 여부
for path in "/administration" "/admin" "/api-docs" "/ftp" "/assets/public" "/robots.txt" "/security.txt"; do  # 반복문 시작
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path")
  echo "$path → HTTP $status"
done
```

**예상 출력**:
```
/administration → HTTP 200
/admin → HTTP 200
/api-docs → HTTP 200
/ftp → HTTP 200
/assets/public → HTTP 200
/robots.txt → HTTP 200
/security.txt → HTTP 200
```

> `/ftp` 경로에서 파일 목록이 노출되고, `/api-docs`에서 API 문서가 공개될 수 있다. 이들은 모두 잠재적 취약점이다.

### 6.5 FTP 디렉토리 탐색

```bash
# FTP 공개 디렉토리 확인
curl -s http://10.20.30.80:3000/ftp/ | python3 -m json.tool 2>/dev/null || curl -s http://10.20.30.80:3000/ftp/
```

### 6.6 robots.txt 확인

```bash
# 검색 엔진 크롤링 제어 파일
curl -s http://10.20.30.80:3000/robots.txt
```

> **보안 포인트**: `robots.txt`는 검색 엔진에게 크롤링하지 말 것을 **요청**하는 파일이지, 접근을 **차단**하는 파일이 아니다. 공격자는 이 파일에서 숨기고 싶은 경로 정보를 얻을 수 있다.

---

## 7. 실습 3: HTTP 요청/응답 분석 (20분)

### 7.1 상세 HTTP 통신 분석

```bash
# -v 옵션으로 전체 HTTP 통신 과정 확인
curl -v http://10.20.30.80:3000/ 2>&1 | head -40
```

**출력 분석**:
```
> GET / HTTP/1.1           ← 요청 라인 (메서드, 경로, 프로토콜)
> Host: 10.20.30.80:3000   ← 요청 헤더
> User-Agent: curl/7.xx    ← 클라이언트 정보
> Accept: */*              ← 수락 가능한 콘텐츠 타입
>
< HTTP/1.1 200 OK          ← 응답 상태 라인
< X-Powered-By: Express    ← 서버 기술 스택 노출
< Content-Type: text/html  ← 응답 콘텐츠 타입
```

### 7.2 쿠키 분석

```bash
# 로그인 후 쿠키 확인
curl -s -c - http://10.20.30.80:3000/ | head -5
```

### 7.3 사용자 등록 및 로그인 테스트

```bash
# 테스트 사용자 등록
curl -s -X POST http://10.20.30.80:3000/api/Users \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "email": "student@test.com",
    "password": "Test1234!",
    "passwordRepeat": "Test1234!",
    "securityQuestion": {
      "id": 1,
      "question": "Your eldest siblings middle name?"
    },
    "securityAnswer": "test"
  }' | python3 -m json.tool

# 로그인
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -m json.tool  # 요청 데이터(body)
```

**예상 출력** (로그인 성공 시):
```json
{
    "authentication": {
        "token": "eyJhbGciOiJSUzI1NiIs...",
        "bid": 1,
        "umail": "student@test.com"
    }
}
```

> 반환된 `token`은 **JWT (JSON Web Token)**이다. 이 토큰의 구조와 취약점은 이후 수업에서 다룬다.

### 7.4 JWT 토큰 기초 분석

```bash
# JWT 토큰을 받아서 디코딩 (Base64)
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")  # 요청 데이터(body)

# JWT의 3부분 (Header.Payload.Signature) 중 Payload 디코딩
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

**예상 출력**:
```json
{
    "status": "success",
    "data": {
        "id": 1,
        "email": "student@test.com",
        "role": "customer"
    },
    "iat": 1711500000,
    "exp": 1711536000
}
```

> 토큰에 사용자의 역할(`role`)이 포함되어 있다. 만약 이를 변조할 수 있다면? (이후 수업에서 다룸)

---

## 8. 실습 4: 취약점 점검 사전 조사 체험 (20분)

실제 취약점 점검의 Phase 2(정보 수집) 과정을 체험해보자.

### 8.1 기술 스택 요약 정리

지금까지 수집한 정보를 정리한다:

```bash
echo "=== JuiceShop 기술 스택 정보 수집 결과 ==="
echo ""

# 서버 응답 헤더에서 정보 추출
echo "[1] 서버 헤더 정보:"
curl -sI http://10.20.30.80:3000/ | grep -iE "server|x-powered|x-frame|content-security"

echo ""
echo "[2] API 엔드포인트:"
echo "  - /api/Products (상품 목록)"
echo "  - /rest/user/login (로그인)"
echo "  - /rest/products/search (검색)"
echo "  - /api/Users (사용자 등록)"

echo ""
echo "[3] 발견된 경로:"
for path in "/administration" "/ftp" "/api-docs" "/robots.txt"; do  # 반복문 시작
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path")
  echo "  - $path → HTTP $status"
done

echo ""
echo "[4] 프레임워크: Angular (SPA) + Express (Node.js)"
```

### 8.2 점검 대상 프로파일 작성

위 결과를 바탕으로 점검 대상 프로파일을 작성한다:

```
[점검 대상 프로파일]

대상: OWASP Juice Shop
IP: 10.20.30.80
포트: 3000 (HTTP)
서버: Node.js + Express
프론트엔드: Angular (SPA)
인증: JWT (JSON Web Token)
API: REST API (/api/*, /rest/*)

발견된 정보 노출:
  - X-Powered-By 헤더 노출
  - /ftp 디렉토리 공개
  - /api-docs API 문서 공개
  - /robots.txt 존재

우선 점검 대상 기능:
  - 로그인/회원가입 (인증 취약점)
  - 검색 기능 (Injection 취약점)
  - 상품 조회 (접근 제어 취약점)
```

---

## 과제

### 과제 1: 점검 계약서 작성 (개인)
다음 시나리오를 가정하고 간이 점검 계약서(ROE)를 작성하라:
> "A 기업이 자사 웹 애플리케이션(JuiceShop)에 대한 취약점 점검을 의뢰했다."

포함할 항목:
- 점검 대상 (IP, 포트, URL)
- 점검 범위 (허용된 기법, 금지된 기법)
- 점검 기간
- 비상 연락처
- 데이터 처리 방침

### 과제 2: 정보 수집 보고서 (개인)
JuiceShop에 대해 추가 정보 수집을 수행하고 다음을 보고서로 작성하라:
- 발견한 모든 API 엔드포인트 목록
- `/ftp` 디렉토리에서 발견한 파일 목록
- `/api-docs`에서 확인한 API 문서 내용 요약
- 발견한 보안 문제점 3가지 이상

### 과제 3: OWASP Top 10 매핑 (조별)
JuiceShop의 기능들을 분석하여 OWASP Top 10의 각 항목에 해당하는 잠재적 취약점 위치를 예측하라.

---

## 검증 체크리스트

- [ ] JuiceShop (http://10.20.30.80:3000) 접속 성공
- [ ] curl로 HTTP 상태 코드 200 확인
- [ ] 응답 헤더에서 `X-Powered-By` 정보 확인
- [ ] `/api/Products` API에서 상품 목록 JSON 수신
- [ ] `/rest/products/search?q=` 검색 API 동작 확인
- [ ] `/ftp`, `/api-docs`, `/robots.txt` 경로 접근 확인
- [ ] 테스트 사용자 등록 성공
- [ ] 로그인 후 JWT 토큰 수신
- [ ] JWT 토큰의 Payload 디코딩 성공
- [ ] 점검 대상 프로파일 작성 완료

---

## 다음 주 예고

**Week 02: 정보 수집 심화 + 자동 스캔 도구 실습**

- nmap을 이용한 포트 스캔 및 서비스 식별
- nikto를 이용한 웹 서버 취약점 스캔
- gobuster를 이용한 숨겨진 디렉토리/파일 탐색
- 실습: JuiceShop에 대한 자동 스캔 수행 및 결과 분석

> 다음 주부터 본격적인 취약점 스캐닝이 시작됩니다. 이번 주 과제를 통해 정보 수집의 기본기를 다져두세요!

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** CVSS 9.8은 어떤 심각도 등급인가?
- (a) High  (b) **Critical**  (c) Medium  (d) Low

**Q2.** 취약점 점검 시 가장 먼저 수행하는 단계는?
- (a) 익스플로잇 실행  (b) **대상 범위 확인 및 정보 수집**  (c) 보고서 작성  (d) 패치 적용

**Q3.** SQLi 취약점의 CWE 번호는?
- (a) CWE-79  (b) **CWE-89**  (c) CWE-352  (d) CWE-22

**Q4.** 점검 보고서에서 취약점의 '재현 절차'가 중요한 이유는?
- (a) 분량을 늘리기 위해  (b) **고객이 직접 확인하고 수정할 수 있도록**  (c) 법적 요건  (d) 점검 시간 기록

**Q5.** WAF(:8082)가 SQLi를 차단할 때 반환하는 HTTP 코드는?
- (a) 200 OK  (b) **403 Forbidden**  (c) 500 Internal Error  (d) 301 Redirect

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성
