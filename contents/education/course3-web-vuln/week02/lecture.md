# Week 02: 점검 도구 환경 구축

## 학습 목표
- 웹 취약점 점검에 사용되는 대표 도구의 역할과 차이를 이해한다
- OWASP ZAP 프록시의 기본 동작 원리를 파악한다
- nikto, sqlmap, curl을 실습 환경에서 직접 설치하고 실행한다
- curl 고급 옵션을 활용하여 HTTP 요청을 세밀하게 제어할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 전제 조건
- SSH로 실습 서버 접속 가능 (Week 01 완료)
- HTTP 요청/응답의 기본 구조를 이해함

---

## 1. 웹 취약점 점검 도구 개요 (20분)

### 1.1 도구 분류

| 분류 | 도구 | 역할 |
|------|------|------|
| **프록시 도구** | Burp Suite, OWASP ZAP | 브라우저↔서버 사이에서 요청/응답 가로채기 |
| **스캐너** | nikto, Nessus | 알려진 취약점 자동 탐지 |
| **특화 도구** | sqlmap, XSSer | 특정 취약점(SQLi, XSS) 자동 공격 |
| **범용 도구** | curl, wget, httpie | 수동 HTTP 요청 전송 |

### 1.2 점검 워크플로우

```
1. 정보수집 (nikto, curl)
   ↓
2. 프록시 설정 (ZAP/Burp)
   ↓
3. 수동 점검 (프록시로 요청 변조)
   ↓
4. 자동 점검 (sqlmap, ZAP Scanner)
   ↓
5. 결과 분석 및 보고서 작성
```

### 1.3 합법적 점검의 원칙

> **중요**: 취약점 점검은 반드시 **허가된 대상**에서만 수행한다.
> 이 수업에서는 실습 전용 서버(JuiceShop)만 대상으로 한다.

- 점검 전 서면 동의서 확보 (실무)
- 점검 범위와 시간을 명확히 정의
- 발견된 취약점은 책임 있게 보고 (Responsible Disclosure)

---

## 2. 실습 환경 접속 확인 (10분)

> **이 실습을 왜 하는가?**
> "점검 도구 환경 구축" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 web 서버 접속

> **실습 목적**: web 서버에 접속하여 웹 취약점 점검에 필요한 도구 환경을 구축한다
>
> **배우는 것**: curl, Burp Suite, ZAP 등 점검 도구의 설치 확인과 기본 사용법을 익힌다
>
> **결과 해석**: 도구가 정상 실행되고 대상 서버와 통신이 되면 점검 환경이 준비된 것이다
>
> **실전 활용**: 웹 취약점 점검 프로젝트의 첫 단계는 항상 도구 환경 구축과 대상 연결 확인이다

```bash
# bastion 서버에서 web 서버로 SSH 접속
ssh ccc@10.20.30.80
```

### 2.2 JuiceShop 동작 확인

```bash
# HTML body 첫 줄 + HTTP 응답 코드
curl -s -o /tmp/juice_index.html -w "code=%{http_code} size=%{size_download}\n" http://10.20.30.80:3000
head -3 /tmp/juice_index.html
```

**예상 출력**:
```
code=200 size=1987
<!--
  ~ Copyright (c) 2014-2024 Bjoern Kimminich & the OWASP Juice Shop contributors.
  ~ SPDX-License-Identifier: MIT
```

> **해석**: code=200 = 정상 가동. size 가 1KB 미만이면 SPA shell 만 떨어짐 (정상 — Angular 가 JS 로 본 페이지 렌더). HTML 첫 줄에 OWASP Juice Shop 라이센스 주석이 박혀 있어 *대상 식별 1차 증빙* 으로 사용 가능. code≠200 (502/503) = JuiceShop 컨테이너 다운 → ssh ccc@web 후 `docker ps | grep juice` 확인.

> **OSS 대안 — 동일 정보 더 빠르게**:
>
> ```bash
> # httpie (색상 + JSON pretty)
> http --print=Hh GET http://10.20.30.80:3000/   # 헤더+상태
>
> # whatweb (1줄로 기술 스택 식별)
> whatweb http://10.20.30.80:3000
> # → JuiceShop[..], Express, Angular[16.x], JS-Library
> ```

### 2.3 Apache + ModSecurity 확인

```bash
# Apache 80 포트 응답 + 서버 헤더 + ModSecurity 동작 검증
curl -sI http://10.20.30.80:80 | head -8
echo '---'
# 의도적 SQLi 페이로드로 WAF 차단 응답 확인
curl -s -o /dev/null -w "code=%{http_code}\n" "http://10.20.30.80:80/?id=1' OR '1'='1"
```

**예상 출력**:
```
HTTP/1.1 200 OK
Date: ...
Server: Apache/2.4.52 (Ubuntu)
Content-Type: text/html
---
code=403
```

> **해석**: `Server: Apache/2.4.52` 노출 = 정보 노출 취약 (week08·week09 의 헤더 점검 주제). 두 번째 요청은 SQLi 패턴 → ModSecurity CRS 942100 (SQL injection) rule 매치 → **403 Forbidden** 반환. *403 = WAF 가동 정상*. 200 이면 WAF rule 미적용 → secu 서버에서 modsecurity audit log 점검 필요.

> **OSS 대안 — WAF 존재 자체를 1초 내 확인**:
>
> ```bash
> # wafw00f — WAF 종류·생산자 자동 식별 (40+ WAF 시그니처 DB)
> wafw00f http://10.20.30.80:80
> # 예: The site is behind ModSecurity (Trustwave SpiderLabs)
> ```

---

## 3. Burp Suite 개념 이해 (15분)

### 3.1 Burp Suite란?

Burp Suite는 PortSwigger사에서 만든 웹 취약점 점검의 표준 도구이다.
Community Edition(무료)과 Professional Edition(유료)이 있다.

**핵심 기능:**

| 기능 | 설명 |
|------|------|
| **Proxy** | 브라우저 트래픽 가로채기 (Intercept) |
| **Repeater** | 요청을 수정하여 재전송 |
| **Intruder** | 페이로드 자동 삽입 (무차별 대입) |
| **Scanner** | 자동 취약점 스캔 (Pro 전용) |
| **Decoder** | 인코딩/디코딩 변환 |

### 3.2 프록시 동작 원리

```
[브라우저] → [프록시:8080] → [웹서버]
                  ↑
            요청을 가로채서
            확인/수정 후 전달
```

- 브라우저의 프록시 설정을 `127.0.0.1:8080`으로 변경
- HTTPS 트래픽 가로채기 위해 Burp CA 인증서 설치 필요
- **이 수업에서는 설치하지 않고 개념만 이해** (대신 ZAP과 curl 사용)

---

## 4. OWASP ZAP 설치 및 사용 (30분)

### 4.1 OWASP ZAP이란?

OWASP Zed Attack Proxy(ZAP)는 무료 오픈소스 웹 보안 점검 도구이다.
Burp Suite의 무료 대안으로, 자동 스캔 기능이 무료로 제공된다.

### 4.2 ZAP CLI 설치 (실습 서버)

```bash
# Python 기반 ZAP CLI 도구 확인 (ZAP API 호출용)
pip3 install python-owasp-zap-v2.4 2>&1 | tail -3
python3 -c "from zapv2 import ZAPv2; print('ZAP API client ready')"
```

**예상 출력**:
```
Requirement already satisfied: python-owasp-zap-v2.4 in ...
ZAP API client ready
```

> **해석**: pip 메시지가 'Requirement already satisfied' 이면 사전 설치됨. import 성공 = API 호출 코드 작성 가능. `from zapv2 import ZAPv2` 가 표준 진입점 — `ZAPv2(apikey=KEY, proxies={'http': 'http://localhost:8090'})` 로 인스턴스화 후 `zap.spider.scan(url)`/`zap.ascan.scan(url)` 호출. *GUI 없이 헤드리스 + REST* 가 ZAP 의 본 강점.

### 4.3 ZAP daemon 모드 + Baseline 스캔

```bash
# ZAP daemon 실행 (포트 8090)
# (실행 X — 데모 명령. lab 환경에서는 Week 13 에서 본격 사용)
echo 'zap.sh -daemon -port 8090 -config api.key=zap-api-key &'

# Baseline 스캔 (zap-baseline.py — 5분 내 비파괴 점검)
echo 'docker run -t owasp/zap2docker-stable zap-baseline.py -t http://10.20.30.80:3000 -r /tmp/zap_baseline.html'

# 또는 daemon 가동 시 API 호출
echo 'curl "http://localhost:8090/JSON/spider/action/scan/?url=http://10.20.30.80:3000&apikey=zap-api-key"'
```

**예상 출력 (Baseline 스캔 결과 일부)**:
```
PASS: Cross-Domain JavaScript Source File Inclusion [10017]
WARN-NEW: Strict-Transport-Security Header Not Set [10035] x 12
WARN-NEW: X-Content-Type-Options Header Missing [10021] x 23
FAIL-NEW: 0      FAIL-INPROG: 0      WARN-NEW: 4      WARN-INPROG: 0
INFO: 0 IGNORE: 0 PASS: 56
```

> **해석**: Baseline = 페이로드 주입 X / 응답 헤더·동적 분석만 (CI/CD 안전). PASS 56 = 통과 룰 / WARN 4 = 의심 / FAIL 0 = 명시 실패. WARN-NEW = 이번 스캔에서 처음 발견. Active Scan (`zap-full-scan.py`) 은 실 페이로드 주입 → Week 13 에서 다룸.

> **OSS 대안 — daemon 없이 1줄 스캔**:
>
> ```bash
> # nuclei (template 5,000+ — ZAP Baseline 보다 빠름)
> nuclei -u http://10.20.30.80:3000 -t http/misconfiguration/ -severity medium,high
> ```

---

## 5. nikto 설치 및 사용 (30분)

### 5.1 nikto란?

nikto는 웹 서버의 알려진 취약점, 기본 파일, 잘못된 설정을 스캔하는 도구이다.
6,700개 이상의 위험한 파일/프로그램을 검사한다.

### 5.2 설치

```bash
# bastion 서버에서 실행
which nikto || echo "1" | sudo -S apt-get install -y nikto
```

### 5.3 기본 스캔

```bash
# JuiceShop 대상 nikto 스캔 (60초 제한)
nikto -h http://10.20.30.80:3000 -maxtime 60s 2>/dev/null | tail -20
```

**예상 출력**:
```
- Nikto v2.5.0
+ Target IP:          10.20.30.80
+ Target Hostname:    10.20.30.80
+ Target Port:        3000
+ Server: No banner retrieved
+ /: Retrieved x-powered-by header: Express.
+ /: The anti-clickjacking X-Frame-Options header is not present. See: ...
+ /: The X-Content-Type-Options header is not set. See: ...
+ /robots.txt: Entry '/ftp/' is returned a non-forbidden or redirect HTTP code (200). See: ...
+ /ftp/: Directory indexing found.
+ No CGI Directories found (use '-C all' to force check all possible dirs)
+ 1 host(s) tested
```

> **해석**: 7+ 항목 발견 = JuiceShop 의 의도적 취약점 검출 정상. **X-Frame-Options 누락** = clickjacking 가능 (악성 사이트가 <iframe> 으로 JuiceShop 임베딩 → 사용자 클릭 탈취). **X-Content-Type-Options 누락** = MIME 스니핑 가능 (브라우저가 .txt 를 .js 로 추정 실행). **/ftp 디렉토리 리스팅** = 백업 파일 노출 (week06 LFI/디렉터리 점검에서 본격 활용).

### 5.4 주요 옵션 + 결과 파일 저장

```bash
# HTML 보고서 + CSV 동시 저장
nikto -h http://10.20.30.80:3000 -o /tmp/nikto_juice -Format htm -maxtime 60s 2>/dev/null > /dev/null
nikto -h http://10.20.30.80:3000 -o /tmp/nikto_juice.csv -Format csv -maxtime 60s 2>/dev/null > /dev/null
ls -l /tmp/nikto_juice* | awk '{print $5,$9}'

# 튜닝 옵션 (1=흥미로운 파일 / 2=잘못된 설정 / 3=정보 노출 / 4=XSS)
nikto -h http://10.20.30.80:3000 -Tuning 1234 -maxtime 30s 2>/dev/null | grep -c '^+'
```

**예상 출력**:
```
8421 /tmp/nikto_juice.htm
6203 /tmp/nikto_juice.csv
12
```

> **해석**: 보고서 양식은 4종 (txt/htm/csv/xml). HTML = 클라이언트 제출용 / CSV = SIEM/Excel 통계 / XML = 다른 도구 (Metasploit/Faraday) 임포트. `-Tuning 1234` = 4 카테고리만 (전체 12 카테고리 중) → 빠름. *grep -c '^+' = 12* 가 발견 항목 수 — 자동 카운팅 → 분기 점검 KPI 추적.

> **OSS 대안 — 같은 작업 더 빠른 도구**:
>
> ```bash
> # nikto 약점: 60s+ 시간 소요. 대안으로:
> nuclei -u http://10.20.30.80:3000 -t http/misconfiguration/ -severity medium,high   # 5초 내 완료
> wapiti -u http://10.20.30.80:3000 -m all -f json -o /tmp/wapiti.json                # OWASP 카테고리 분류
> ```

### 5.5 결과 해석

nikto 결과에서 주의할 항목:

| 표시 | 의미 |
|------|------|
| `+` | 정보성 메시지 |
| `OSVDB-XXXX` | Open Source Vulnerability Database 항목 |
| `X-Frame-Options not set` | 클릭재킹 취약 가능 |
| `X-Content-Type-Options not set` | MIME 스니핑 가능 |
| `Server: Express` | 서버 기술 스택 노출 |

---

## 6. sqlmap 설치 및 기본 사용 (20분)

### 6.1 sqlmap이란?

sqlmap은 SQL Injection 취약점 탐지 및 공격 자동화 도구이다.
다양한 DBMS(MySQL, PostgreSQL, SQLite 등)를 지원한다.

### 6.2 설치 + 버전 확인

```bash
# 설치 확인 (이미 있으면 경로 출력)
which sqlmap || echo "1" | sudo -S apt-get install -y sqlmap
sqlmap --version
```

**예상 출력**:
```
/usr/bin/sqlmap
1.7.2#stable
```

> **해석**: sqlmap = Python 기반 단일 binary. apt 설치 시 1.6+ / pip 설치 시 1.8+ (최신). Kali 기본 포함. *주요 버전*: 1.5 (UTF-8 강화) / 1.6 (NoSQL 일부 지원) / 1.7 (HTTP/2). 운영 환경은 venv + git clone 으로 최신 유지 권장.

### 6.3 기본 사용법 (맛보기 — Week 05 에서 상세 학습)

```bash
# JuiceShop /rest/products/search 에 SQLi 자동 테스트
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch --level=1 --risk=1 2>&1 | grep -E "Type:|Title:|Payload:|back-end DBMS|web application technology|^---" | head -15
```

**예상 출력**:
```
[INFO] testing connection to the target URL
[INFO] testing if the target URL content is stable
back-end DBMS: SQLite
web application technology: Express
---
Parameter: q (GET)
    Type: error-based
    Title: Generic SQL error-based - WHERE or HAVING clause
    Payload: q=test')) UNION SELECT NULL...
```

> **해석**: sqlmap 가 JuiceShop의 SQLite DBMS 자동 식별 (Express + SQLite stack). `Type: error-based` = SQL 에러 메시지 기반 탐지 (가장 흔한 — week05 의 학습 핵심). `Payload` 의 `'))` = JuiceShop 의 `LIKE ('%test%')` 쿼리 종료 트릭. `--batch` = 대화형 질문 자동 Y. `--level=1 --risk=1` = 가장 가벼운 탐지 (운영 안전). week05 에서는 `--level=5 --risk=3 --tamper=...` 로 강도 올림.

> **주의**: JuiceShop 은 일부 endpoint 가 NoSQL (MongoDB-like) 이라 전통 SQLi 가 안 통한다. `/rest/products/search` 는 SQLite — 정상 SQLi. `/rest/user/login` 은 NoSQL injection (`{"$ne": null}` 패턴) — week05 에서 비교.

---

## 7. curl 고급 활용 (40분)

### 7.1 curl 기본 복습

```bash
# 응답 헤더만 (-I = HEAD)
curl -sI http://10.20.30.80:3000 | head -8
```

**예상 출력**:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Feature-Policy: payment 'self'
Content-Type: text/html; charset=utf-8
ETag: W/"7c3-..."
Date: ...
```

> **해석**: HEAD 요청 = 본문 미수신 = 빠름·대역폭 절감. 점검 1차 fingerprinting 표준. *주의*: JuiceShop 는 X-Frame-Options/X-Content-Type-Options 가 *부분 설정* 되어 있음 (의도적 — 학생이 nikto 결과와 비교하면 nikto 가 특정 path 에서만 헤더 누락 보고하는지 확인 가능). 운영 시 `-I` 가 405 Method Not Allowed 면 `-X HEAD` 강제 또는 `-r 0-0` (1바이트만 GET).

### 7.2 POST 요청 — 인증 실패 응답 분석

```bash
# JuiceShop 로그인 — 잘못된 자격증명
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' | python3 -m json.tool
```

**예상 출력**:
```json
{
    "error": {
        "name": "Error",
        "message": "Invalid email or password.",
        "stack": "Error: Invalid email or password.\n    at ..."
    }
}
```

> **해석 — 정보 노출 평가**: (1) `message` 가 'Invalid email or password.' (포괄적) = 양호 — 'email not found' / 'wrong password' 처럼 분리하면 username enumeration 가능. (2) `stack` 트레이스가 응답에 포함 = **A05 Security Misconfiguration** — 운영 환경이면 잘라내야 함. JuiceShop 은 의도적 노출. (3) 응답 시간 비교 (정상 vs 잘못된 비번) = timing attack 가능성 — sqlmap `--technique=T` 로 검증.

> **OSS 대안 — POST 자동화**:
>
> ```bash
> # httpie — JSON 기본 (헤더 자동)
> http POST http://10.20.30.80:3000/rest/user/login email=admin@juice-sh.op password=wrong
>
> # ffuf — 자격 brute-force (week05 권한 우회 학습 시)
> ffuf -u http://10.20.30.80:3000/rest/user/login -X POST -H 'Content-Type: application/json' \
>      -d '{"email":"admin@juice-sh.op","password":"FUZZ"}' -w pwlist.txt -fc 401
> ```

### 7.3 쿠키 다루기

```bash
# 쿠키 저장
curl -c /tmp/cookies.txt http://10.20.30.80:3000

# 저장된 쿠키로 요청
curl -b /tmp/cookies.txt http://10.20.30.80:3000/rest/basket/1

# 쿠키 직접 지정
curl -b "token=abc123" http://10.20.30.80:3000/rest/basket/1
```

### 7.4 HTTP 헤더 조작

```bash
# User-Agent 변경
curl -H "User-Agent: Mozilla/5.0 (Security Scanner)" http://10.20.30.80:3000

# Referer 위조
curl -H "Referer: http://10.20.30.80:3000/admin" http://10.20.30.80:3000

# 여러 헤더 동시 설정
curl -H "Accept: application/json" \
     -H "Authorization: Bearer fake-token" \
     http://10.20.30.80:3000/api/Products/1
```

### 7.5 상세 정보 + 응답 시간 분석

```bash
# 응답 시간 4단계 분리
curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\nSize: %{size_download} bytes\n" http://10.20.30.80:3000/rest/products/search?q=apple
```

**예상 출력**:
```
DNS: 0.000038s
Connect: 0.000341s
TTFB: 0.067s
Total: 0.069s
Size: 285 bytes
```

> **해석**: 4단계 시간 분리 = 네트워크 → 서버 처리 → 응답 어디서 느린지 진단. **TTFB (Time To First Byte) 0.067s** = 서버 SQL 처리 + Express 응답 시간. SQLi blind time-based (week05) 는 `' AND SLEEP(5)--` 페이로드 → TTFB 5초+ → 비교로 탐지. **DNS 0.00003s** = `/etc/hosts` 또는 캐시 (정상). 실 운영 시 0.5s+ = DNS 서버 문제. 본 측정값을 *baseline* 으로 저장 → 점검 후 비교 → 점검 활동의 부하 영향 평가.

> **OSS 대안 — 본격 부하 측정**:
>
> ```bash
> ab -n 100 -c 10 http://10.20.30.80:3000/             # Apache Bench, 100 요청 / 동시 10
> wrk -t4 -c50 -d10s http://10.20.30.80:3000/          # wrk, 10초 부하 시험
> hey -n 100 -c 10 http://10.20.30.80:3000/            # hey, Go binary 가벼움
> ```

### 7.6 파일 업로드 테스트

```bash
# 테스트 파일 생성
echo "test file content" > /tmp/test_upload.txt

# multipart form 업로드
curl -X POST http://10.20.30.80:3000/file-upload \
  -F "file=@/tmp/test_upload.txt" \
  -v 2>&1 | tail -20
```

### 7.7 curl을 이용한 간이 스캐닝

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 민감 경로 순회 — 200/301 = 노출, 404 = 차단, 403 = 존재(권한 X)
for path in admin robots.txt .env .git/config sitemap.xml ftp api-docs swagger.json package.json; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  echo "$code - /$path"
done
```

**예상 출력**:
```
404 - /admin
200 - /robots.txt
404 - /.env
404 - /.git/config
404 - /sitemap.xml
200 - /ftp
404 - /api-docs
404 - /swagger.json
200 - /package.json
```

> **해석**: **/robots.txt 200** = SEO 정책 노출 (점검 시작 표준). **/ftp 200** = nikto 가 발견한 디렉토리 — 백업 파일 nature (week06 LFI 학습 시). **/package.json 200** = Node.js 의존성 노출 = 라이브러리·버전 식별 = CVE 매핑 가능 (week08 의 SCA 학습). **/.env 404** = 양호 (운영 비밀 미노출). 이 9-경로 sweep 가 점검 1차 OSINT — 분기 자동화 권장.

> **OSS 대안 — 본격 디렉토리 brute (week03 에서 본격 학습)**:
>
> ```bash
> # ffuf — Go binary, 빠름 + JSON 출력
> ffuf -u http://10.20.30.80:3000/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -mc 200,301,302 -t 50
>
> # gobuster — 동일 작업, 다른 wordlist 출력 형식
> gobuster dir -u http://10.20.30.80:3000 -w /usr/share/wordlists/dirb/common.txt -t 50 -x bak,old,zip
>
> # feroxbuster — Rust 작, 재귀 brute (서브 디렉토리 자동 탐색)
> feroxbuster -u http://10.20.30.80:3000 -w /usr/share/seclists/Discovery/Web-Content/common.txt
> ```
>
> ★ ffuf 의 `-mc 200,301,302` (match code) + `-fs 0` (filter size) 조합으로 오탐 90% 감소 — week03 의 핵심 학습 포인트.

---

## 8. 실습 과제

### 과제 1: nikto 스캔 결과 분석
1. nikto로 JuiceShop(포트 3000)을 스캔하라
2. 결과를 `/tmp/nikto_result.txt`로 저장하라
3. 발견된 항목 중 보안상 의미 있는 3가지를 골라 설명하라

### 과제 2: curl로 JuiceShop 탐색
1. JuiceShop의 REST API 엔드포인트 5개를 찾아라 (힌트: `/api/`, `/rest/`)
2. 각 엔드포인트의 응답 코드와 Content-Type을 기록하라
3. 로그인 API에 잘못된 인증 정보를 보내고 에러 응답을 분석하라

### 과제 3: HTTP 헤더 보안 점검
1. curl -I로 JuiceShop의 응답 헤더를 확인하라
2. 다음 보안 헤더의 존재 여부를 확인하라:
   - `X-Frame-Options`
   - `X-Content-Type-Options`
   - `Content-Security-Policy`
   - `Strict-Transport-Security`
3. 누락된 헤더가 있으면 어떤 공격에 취약한지 서술하라

---

## 9. 요약

| 도구 | 용도 | 이번 수업 실습 |
|------|------|----------------|
| Burp Suite | 프록시 + 수동점검 | 개념 이해 |
| OWASP ZAP | 프록시 + 자동스캔 | 설치 확인 |
| nikto | 웹서버 취약점 스캔 | 기본 스캔 실행 |
| sqlmap | SQL Injection 자동화 | 설치 확인 (Week 05 상세) |
| curl | 수동 HTTP 요청 | 고급 옵션 실습 |

**다음 주 예고**: Week 03 - 정보수집 점검. 디렉터리 스캐닝, 기술 스택 식별, SSL/TLS 점검을 학습한다.

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### DVWA 보안 레벨 변경 방법 (웹 UI)

> **DVWA URL:** `http://10.20.30.80:8080`

1. 브라우저에서 `http://10.20.30.80:8080` 접속
2. 로그인: ID `admin` / PW `password`
3. 좌측 메뉴에서 **DVWA Security** 클릭
4. **Security Level** 드롭다운에서 레벨 선택:
   - **Low**: 보안 장치 없음 (취약점 학습용)
   - **Medium**: 기본적인 필터링 적용 (우회 실습용)
   - **High**: 강화된 필터링 (고급 우회 실습용)
   - **Impossible**: 안전한 구현 (방어 코드 참조용)
5. **Submit** 버튼 클릭하여 레벨 변경 적용
6. 좌측 메뉴에서 실습할 취약점 항목(SQL Injection, XSS 등) 선택
7. 각 항목 페이지 하단 **View Source** 클릭 → 현재 레벨의 소스 코드 확인

> **실습 순서:** Low에서 취약점 확인 → Medium에서 우회 시도 → High에서 고급 우회 → Impossible에서 안전한 코드 학습

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Burp Suite Community
> **역할:** 웹 프록시 기반 수동/반자동 취약점 점검 도구  
> **실행 위치:** `작업 PC → web (10.20.30.80:3000)`  
> **접속/호출:** GUI `burpsuite`, CA 인증서 신뢰 필요 (`http://burp`)

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `Proxy → HTTP history` | 모든 캡처된 요청/응답 |
| `Intruder` | 페이로드 페이즈·위치 기반 자동화 |
| `Repeater` | 단건 요청 수동 반복 |

**핵심 설정·키**

- `Proxy listener 127.0.0.1:8080` — 브라우저 프록시 포트
- `Target → Scope` — in-scope 호스트만 처리

**로그·확인 명령**

- `Logger` — 세션 전체 요청 타임라인

**UI / CLI 요점**

- Ctrl+R — 요청을 Repeater로 전송
- Ctrl+I — Intruder로 전송 후 위치(§) 설정
- Intruder Attack type: Sniper/Cluster bomb — 단일/다중 페이로드 조합

> **해석 팁.** Community 버전은 **Intruder 속도 제한**이 있어 대량 브루트포스는 비현실적. 취약점 재현과 보고서 증적 확보에 집중.

### OWASP ZAP
> **역할:** 오픈소스 자동 웹 취약점 스캐너·프록시  
> **실행 위치:** `작업 PC / Docker`  
> **접속/호출:** GUI `zaproxy`, API `http://zap:8090/JSON/...`, Docker `owasp/zap2docker-stable`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.ZAP/session-*` | 세션 저장소 |
| `context.xml` | 스캔 컨텍스트(범위/인증) |

**핵심 설정·키**

- `Active Scan policy` — 룰별 강도 및 활성화 여부
- `Authentication: form-based` — 로그인이 필요한 페이지 스캔

**로그·확인 명령**

- `~/.ZAP/zap.log` — 스캐너 실행 로그

**UI / CLI 요점**

- Spider — 링크 탐색 크롤링
- Active Scan — 실제 페이로드 주입 점검
- Report → Generate HTML report — 표준 보고서 출력

> **해석 팁.** 인증 필요 페이지는 **Context에 로그인 폼**을 등록하지 않으면 로그아웃 상태로 스캔되어 커버리지가 급감. `zap-baseline.py`는 수동 확인용 경량 모드.

### gobuster + nikto
> **역할:** 디렉토리 브루트포싱 + 웹 서버 기본 취약점 스캔  
> **실행 위치:** `공격자 측 CLI`  
> **접속/호출:** `gobuster dir -u <url> -w <wordlist>`, `nikto -h <url>`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/usr/share/wordlists/dirb/common.txt` | 기본 워드리스트 |
| `/usr/share/seclists/` | SecLists — 실전 워드리스트 |

**핵심 설정·키**

- `-t 50` — gobuster 동시 스레드
- `-x php,html,bak` — 확장자 조합 탐색
- `-Tuning 9` — nikto 고급 룰 포함

**로그·확인 명령**

- `-o gobuster.out` — 결과 저장
- ``nikto -o nikto.html -Format htm`` — HTML 리포트

**UI / CLI 요점**

- gobuster 상태 204/301/302 — 존재는 하지만 리다이렉트되는 경로
- nikto `OSVDB-...` — 공개 취약점 DB 매핑

> **해석 팁.** 응답 크기와 상태코드의 **공통 패턴**을 `-s 200,204,301` / `-b 123`으로 제외하면 오탐이 급감한다.

### sqlmap
> **역할:** SQL Injection 탐지·악용 자동화  
> **실행 위치:** `공격자 측 CLI`  
> **접속/호출:** `sqlmap -u <url>` 또는 `-r request.txt`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.local/share/sqlmap/output/<host>/` | 세션·덤프 결과 |
| `session.sqlite` | 재실행 시 단계 스킵용 캐시 |

**핵심 설정·키**

- `--risk=1~3 --level=1~5` — 탐지 공격 폭 조절
- `--technique=BEUSTQ` — B)lind E)rror U)nion S)tacked T)ime Q)uery

**로그·확인 명령**

- `output/<host>/log` — 요청·응답 로그

**UI / CLI 요점**

- `sqlmap -u ... --dbs` — DB 목록
- `sqlmap -u ... -D juice -T users --dump` — 특정 테이블 덤프
- `sqlmap -r req.txt --batch --crawl=2` — Burp 저장 요청 기반 크롤링

> **해석 팁.** `--batch`로 대화형 프롬프트 자동 Y 처리. WAF가 있을 땐 `--tamper=space2comment,between` 조합으로 우회 시도.

---

## 실제 사례 (WitFoo Precinct 6 — 점검 도구가 만드는 트래픽 vs 정상 트래픽)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 / ORG-NNNN / HOST-NNNN 으로 익명화됨.
> 본 lecture *점검 도구 환경 구축* 의 **점검 도구 트래픽이 운영 환경에서 어떻게 보이는지** 비교를 위해 dataset 의 정상 GoogleImageProxy 와 동일 단일 src 의 4018건 GET 통계를 발췌.

### Case 1: 단일 src `100.64.1.37` — 동일 시각 4018건 GET (정상 proxy 패턴)

**메타**

| 항목 | 값 |
|------|---|
| src | `100.64.1.37` (정상 proxy 출구) |
| dst | `10.0.145.98` (보호 대상) |
| 총 GET 건수 | 4018 (전체 dataset 의 GET 100%) |
| 시간 분포 | 단일 timestamp window 내 burst |
| User-Agent 다양성 | `GoogleImageProxy` (단일 정체) |
| WAF outcome | 200/302 (정상) |

**원본 발췌**: 
```text
<190>Jul 26 06:13:46 ... CEF:0|...|WAF|...|GET|5| ...
  USER-9484USER-CRED-30678Application="USER-7922 (ORG-0407 NT 5.1; rv:11.0) ORG-0492 Firefox/11.0
                                       (via ggpht.com GoogleImageProxy)"
  outcome=200 ...
```

**해석 — 본 lecture 와의 매핑**

| 도구 환경 학습 항목 | 본 record 의 시사점 |
|--------------------|---------------------|
| **Burp/ZAP 의 트래픽 지문** | GoogleImageProxy 는 *명시적 UA* 로 정체 노출 — 마찬가지로 Burp 기본 UA `Mozilla/5.0 ... BurpSuite` 도 *명시적*. *기본 설정 = 들킨다* |
| **점검 도구 isolation** | 정상 proxy 도 단일 src 가 4018건 발생 → 점검 도구 가동 시 동일 burst 가 *오탐* 으로 분류되지 않도록 *사전 화이트리스트* 신청 필요 |
| **속도 조절 (Throttle)** | 본 record 는 *수 초 burst* — 점검 시 `--scan-delay`·`-T2`·rate-limit 옵션으로 정상 트래픽과 구분되는 burst 회피 |

**환경 구축 액션 아이템**:
1. 점검 PC 의 IP 를 사전에 SOC·WAF 화이트리스트 등록 (운영 차단 회피)
2. 점검 도구 UA 를 *기본 그대로 두기* (탐지 룰 검증 목적) vs *위장* (회피 효과 평가) 두 모드로 점검 — 본 dataset 은 *기본 UA 가 그대로 남는다* 는 증거




---

## 부록: 학습 OSS 도구 매트릭스 (lab week02 — SQL Injection)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 sqli_detection | curl 수동 페이로드 / **sqlmap --batch --level --risk** / **ghauri** / **wapiti** |
| 2 sqli_error | curl 페이로드 / sqlmap --technique=E / DBMS 별 에러 매핑 (MySQL/PostgreSQL/SQLite/MSSQL/Oracle) |
| 3 sqli_auth_bypass | curl 다양 페이로드 / sqlmap --forms / **Burp Intruder** / payload-list github |
| 4 sqli_union | ORDER BY 컬럼 결정 / sqlmap --tables / **DBeaver GUI** |
| 5 sqli_union dump | curl + jq / sqlmap --dump / **hashid** / DBeaver |
| 6 sqli_blind boolean | curl size 비교 / sqlmap --string --not-string / **bbqsql** |
| 7 sqli_blind time | curl + time / sqlmap --technique=T / **sqlninja** (MSSQL 전용) |
| 8 sqli_tool | sqlmap 종합 (level/risk/technique/dbs/tables/dump/tamper/cookie/POST/RCE) |
| 9 second-order | curl 2 단계 / sqlmap --second-url / PortSwigger Academy |
| 10 file r/w | DBMS 함수 매핑 / sqlmap --file-read --file-write --os-shell |
| 11 header SQLi | curl -H / sqlmap --headers --level=5 / **Burp Active Scan** |
| 12 defense | 5층 방어 / **bandit** Python / **semgrep** / **sqlfluff** / ModSecurity |
| 13 WAF | **wafw00f** / OWASP CRS 942 / sqlmap --tamper / nuclei waf-detect |
| 14 hash crack | **hashid** / **hashcat** / **john** / 알고리즘 강도 비교 표 |
| 15 verification | sqlmap session / markdown 통합 / sha256 / asciinema PoC |

### 학생 환경 준비
```bash
sudo apt install -y sqlmap hashid hashcat john wapiti exploitdb wafw00f
pip install ghauri bbqsql bandit semgrep sqlfluff
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git ~/PATT
# DBeaver: snap install dbeaver-ce
```
