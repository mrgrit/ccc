# Week 03: 정보수집 점검

## 학습 목표
- 웹 애플리케이션 점검의 첫 단계인 정보수집의 중요성을 이해한다
- 디렉터리/파일 스캐닝 기법을 curl 기반으로 실습한다
- 대상 서버의 기술 스택을 식별하는 방법을 익힌다
- SSL/TLS 설정을 점검하고 취약한 구성을 판별할 수 있다

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
- Week 02 도구 환경 구축 완료
- curl 기본 사용법 숙지

---

## 1. 정보수집이 중요한 이유 (15분)

### 1.1 점검 프로세스에서의 위치

```
[정보수집] → 취약점 탐색 → 취약점 검증 → 보고서 작성
  ↑ 지금 여기
```

정보수집(Reconnaissance)은 공격 표면(Attack Surface)을 파악하는 단계이다.
무엇이 있는지 모르면 무엇을 점검할지도 모른다.

### 1.2 수집 대상

| 항목 | 예시 | 활용 |
|------|------|------|
| 디렉터리/파일 구조 | /admin, /api, /.env | 숨겨진 기능, 설정 파일 노출 |
| 기술 스택 | Node.js, Express, Angular | 알려진 취약점 검색 |
| HTTP 헤더 | Server, X-Powered-By | 버전 정보 → CVE 매핑 |
| 에러 메시지 | Stack trace, DB 에러 | 내부 구조 유추 |
| robots.txt, sitemap | 크롤링 제외 경로 | 민감한 경로 힌트 |

### 1.3 수동 vs 자동 정보수집

| 방식 | 장점 | 단점 |
|------|------|------|
| 수동 (curl) | 정밀, 은밀, 맞춤형 | 느림, 경험 필요 |
| 자동 (dirb, gobuster) | 빠름, 대량 스캔 | 노이즈 많음, 탐지 쉬움 |

---

## 2. robots.txt / sitemap 분석 (15분)

> **이 실습을 왜 하는가?**
> "정보수집 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 robots.txt 확인

> **실습 목적**: robots.txt, 디렉터리 구조, 기술 스택 등 웹 애플리케이션의 공개 정보를 수집한다
>
> **배우는 것**: 수동/자동 정보수집 기법으로 점검 대상의 구조와 기술 스택을 파악하는 방법을 배운다
>
> **결과 해석**: robots.txt에 숨긴 경로, 서버 헤더의 기술 정보, 디렉터리 리스팅 등이 발견되면 정보 노출 취약점이다
>
> **실전 활용**: 취약점 점검 보고서의 '정보수집' 섹션에서 발견된 정보 노출 항목을 기록한다

```bash
# JuiceShop의 robots.txt 확인
curl -s http://10.20.30.80:3000/robots.txt
echo '---'
# Apache 의 robots.txt 비교
curl -s -o /dev/null -w "Apache code=%{http_code}\n" http://10.20.30.80:80/robots.txt
```

**예상 출력**:
```
User-agent: *
Disallow: /ftp
---
Apache code=404
```

> **해석 — robots.txt 가 점검자에게 주는 정보**: JuiceShop 의 `Disallow: /ftp` 는 **점검 시작점**. 운영자가 검색엔진에서 숨기려 명시 = 그 자체가 노출 신호. 공격자는 무시 → 직접 접근. **/ftp 가 200 이면 디렉토리 리스팅 + 백업 파일 가능성** (week06 LFI 학습 재료). Apache 의 404 = robots.txt 미배치 = 양호 (또는 Apache 자체가 정적 정보 없음). 양 서비스 비교 = 점검 첫 순간의 공격 표면 정량화.

> **OSS 대안 — robots.txt + sitemap 일괄 추출**:
>
> ```bash
> # waybackurls — Wayback Machine 의 과거 robots.txt 도 추출 (운영자가 삭제한 경로 찾기)
> echo http://10.20.30.80:3000 | waybackurls | grep -E 'robots|sitemap'
>
> # gau (GetAllUrls) — 다중 source (Wayback/CommonCrawl/AlienVault) 통합
> echo example.com | gau | head -20
> ```

### 2.2 sitemap.xml 확인

```bash
curl -s -o /tmp/sitemap_3000.xml -w "code=%{http_code} size=%{size_download}\n" http://10.20.30.80:3000/sitemap.xml
curl -s -o /tmp/sitemap_80.xml -w "code=%{http_code} size=%{size_download}\n" http://10.20.30.80:80/sitemap.xml
head -3 /tmp/sitemap_3000.xml 2>/dev/null
```

**예상 출력**:
```
code=404 size=139
code=404 size=274
<!DOCTYPE html>
<html lang="en">
```

> **해석**: 둘 다 404 = sitemap.xml 미배포. body 가 HTML (404 페이지 자체) 인지 확인 (`head -3` 결과). **운영 환경에서는 200 + XML 본문**. sitemap 의 `<url><loc>` 태그가 모든 공개 경로 노출 → 점검 1차 매핑. SEO 친화 + 공격 표면 노출 trade-off — 점검자는 운영자에게 *공개 페이지만* sitemap 권장.

### 2.3 .well-known 디렉터리

```bash
# RFC 8615 표준 경로들
for path in security.txt openid-configuration change-password apple-app-site-association assetlinks.json; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/.well-known/$path")
  echo "$code  /.well-known/$path"
done
```

**예상 출력**:
```
404  /.well-known/security.txt
404  /.well-known/openid-configuration
404  /.well-known/change-password
404  /.well-known/apple-app-site-association
404  /.well-known/assetlinks.json
```

> **해석**: 모든 경로 404 = JuiceShop 미배포. **security.txt** (RFC 9116) = 보안 신고 채널 — 200 이면 PGP 키·연락처 노출 (양호 / 운영자 식별). **openid-configuration** = OAuth/OIDC 자동 발견 — 200 이면 issuer/jwks_uri 노출 → JWT 분석 입력 (week04 인증 우회). **apple-app-site-association** = iOS Universal Link — 모바일 + 웹 자산 연결. 모두 404 = 점검 대상 단순. 운영 환경이면 *security.txt 만 권장* (책임 있는 disclosure).

---

## 3. 디렉터리 스캐닝 (40분)

### 3.1 개념: dirb/gobuster

**dirb**와 **gobuster**는 사전 파일(wordlist)을 이용해 웹 서버의 숨겨진 디렉터리와 파일을 찾는 도구이다.

```
# dirb 동작 원리 (개념)
# wordlist의 각 단어를 URL에 붙여서 요청 → 200/301/403 등 확인
# /admin → 200 OK (존재!)
# /secret → 404 Not Found (없음)
# /backup → 403 Forbidden (접근 차단 = 존재함!)
```

### 3.2 curl 기반 디렉터리 스캐닝 (직접 구현 — 학습용)

**가장 먼저 권장되는 OSS 도구 (실무 표준)**:

```bash
# gobuster (Go 기반, 가장 빠름)
sudo apt install gobuster
gobuster dir -u http://10.20.30.80:3000 -w /usr/share/wordlists/dirb/common.txt -t 30 -x html,php,bak

# ffuf (단일 wordlist 퍼징, 멀티스레드)
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://10.20.30.80:3000/FUZZ -mc 200,301,403 -t 50

# dirb (가장 단순, 초보자 권장)
sudo apt install dirb
dirb http://10.20.30.80:3000 /usr/share/wordlists/dirb/common.txt
```

**도구 vs curl 직접 구현**: 도구는 (1) 멀티스레드, (2) 사이즈/응답 시간 자동 비교, (3) recursive 모드, (4) JSON/XML 결과 보고서 등을 제공한다. 학습 목적은 직접 구현이지만 **실제 점검은 도구를 쓴다**.

이하 curl 버전은 **도구 동작 원리 이해용**:

```bash
# 기본 wordlist 생성
cat > /tmp/webdirs.txt << 'WORDLIST'
admin
api
login
register
console
debug
backup
test
.env
.git
.git/config
.git/HEAD
config
robots.txt
sitemap.xml
swagger
api-docs
graphql
rest
ftp
WORDLIST

# curl 기반 디렉터리 스캔 스크립트
while IFS= read -r path; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[${code}] /$path"
  fi
done < /tmp/webdirs.txt
```

### 3.3 JuiceShop 숨겨진 경로 탐색

JuiceShop 특화 경로 sweep — code + size 동시 측정.

```bash
for path in \
  "ftp" "api/Products/1" "rest/products/search?q=test" \
  "rest/user/whoami" "api/SecurityQuestions" "api/Challenges" \
  "api/Complaints" "api/Feedbacks" "api/Quantitys" \
  "rest/languages" "rest/memories" "rest/chatbot/status" \
  "metrics" "promotion" "video" "encryptionkeys" \
  "assets/public/images/uploads"; do
  read code size < <(curl -o /dev/null -s -w "%{http_code} %{size_download}" "http://10.20.30.80:3000/$path")
  echo "[${code}] (${size}B) /$path"
done
```

**예상 출력 (발췌)**:
```
[200] (1987B) /ftp
[200] (435B) /api/Products/1
[200] (8421B) /rest/products/search?q=test
[401] (87B) /rest/user/whoami
[200] (5621B) /api/SecurityQuestions
[200] (245B) /api/Challenges
[401] (87B) /api/Complaints
[200] (12340B) /api/Feedbacks
[404] (139B) /api/Quantitys
[200] (892B) /rest/languages
[401] (87B) /rest/memories
[404] (139B) /rest/chatbot/status
[200] (1234B) /metrics
[404] (139B) /promotion
[200] (3128B) /encryptionkeys
[200] (245B) /assets/public/images/uploads
```

> **해석 — code + size 두 축 분석**: **200 (정상 응답)** = 즉시 노출. **401** = 인증 필요 (존재 확인됨, week04 의 인증 우회 입력). **404 size=139B** = 동일 크기 = JuiceShop 의 통일 404 페이지 — 다른 size 면 false-positive. **/encryptionkeys** = 암호화 키 디렉토리 — 운영 환경 노출 = 즉시 critical. **/metrics** = Prometheus endpoint? = 운영 정보 노출. **/api/Feedbacks 12KB** = 다수 피드백 데이터 노출 (BOLA week05). **/api/Quantitys 404** = 오타 명시 (*Quantity 정상 / 의도적 typo) — JuiceShop 의 challenge.

### 3.4 FTP 디렉터리 탐색

```bash
# JuiceShop /ftp 디렉토리 listing 확인
curl -s http://10.20.30.80:3000/ftp/ | head -30
echo '---'
# 백업 파일 직접 다운
curl -s -o /tmp/legal.md -w "legal.md code=%{http_code} size=%{size_download}\n" http://10.20.30.80:3000/ftp/legal.md
curl -s -o /tmp/acquisitions.md -w "acquisitions.md code=%{http_code} size=%{size_download}\n" http://10.20.30.80:3000/ftp/acquisitions.md
ls -l /tmp/legal.md /tmp/acquisitions.md 2>/dev/null
```

**예상 출력**:
```
<html><head><title>listing directory /ftp</title></head>
<body>
<h1>files within directory /ftp</h1>
<ul>
  <li><a href="acquisitions.md">acquisitions.md</a></li>
  <li><a href="announcement_encrypted.md">announcement_encrypted.md</a></li>
  <li><a href="coupons_2013.md.bak">coupons_2013.md.bak</a></li>
  <li><a href="eastere.gg">eastere.gg</a></li>
  <li><a href="encrypt.pyc">encrypt.pyc</a></li>
  <li><a href="incident-support.kdbx">incident-support.kdbx</a></li>
  <li><a href="legal.md">legal.md</a></li>
  <li><a href="package.json.bak">package.json.bak</a></li>
  <li><a href="suspicious_errors.yml">suspicious_errors.yml</a></li>
</ul>
---
legal.md code=200 size=1834
acquisitions.md code=200 size=2956
```

> **해석 — 디렉토리 리스팅 + 백업 파일**: **`Apache Directory Listing`** = OWASP A05 Security Misconfiguration. 9 파일 노출 = 즉시 비고서 critical 항목. **package.json.bak** = Node.js 의존성 + 버전 노출 → SCA + CVE 매핑 (week08). **incident-support.kdbx** = KeePass DB 파일 → 마스터 비번 brute (week04). **coupons_2013.md.bak** = 백업 = 옛 데이터 = 영업 비밀 가능. **suspicious_errors.yml** = 운영자가 'suspicious' 라고 명시한 파일 = JuiceShop 의 의도적 challenge. *모든 .bak/.old/.swp 확장자는 자동 점검 항목*.

> **OSS 대안 — 백업 확장자 brute**:
>
> ```bash
> # ffuf 의 확장자 fuzzing (점검 표준)
> ffuf -u http://10.20.30.80:3000/FUZZ -w wordlist.txt -e .bak,.old,.swp,.zip,.tar.gz,.tar
> # 또는 파일명·확장자 동시 fuzzing
> ffuf -u http://10.20.30.80:3000/FUZZ.FUZZ2 -w names.txt:FUZZ -w exts.txt:FUZZ2 -mode pitchfork
> ```

### 3.5 디렉터리 스캔 결과 분석

| 응답 코드 | 의미 | 점검 시 행동 |
|-----------|------|-------------|
| 200 | 정상 접근 | 내용 확인, 민감 정보 여부 |
| 301/302 | 리다이렉트 | 리다이렉트 대상 확인 |
| 403 | 접근 거부 | 존재 확인됨, 우회 시도 가능 |
| 404 | 미존재 | 무시 |
| 500 | 서버 에러 | 에러 메시지에 정보 노출 가능 |

---

## 4. 기술 스택 식별 (30분)

### 4.1 HTTP 응답 헤더 분석

```bash
# 응답 헤더에서 기술 스택 정보 추출
echo "=== JuiceShop (포트 3000) ==="
curl -sI http://10.20.30.80:3000 | grep -iE "server|x-powered|x-generator|x-aspnet|set-cookie"
echo ""
echo "=== Apache (포트 80) ==="
curl -sI http://10.20.30.80:80 | grep -iE "server|x-powered|x-generator|x-aspnet|set-cookie"
```

**예상 출력**:
```
=== JuiceShop (포트 3000) ===
X-Powered-By: Express
Set-Cookie: language=en; Path=/

=== Apache (포트 80) ===
Server: Apache/2.4.52 (Ubuntu)
Set-Cookie: PHPSESSID=abc123; path=/; HttpOnly
```

> **해석 — 헤더 1줄당 1개 CVE 후보**: **`X-Powered-By: Express`** = Node.js + Express 백엔드. Express 기본 헤더 = `app.disable('x-powered-by')` 1줄로 제거 가능 — 미제거 = OWASP A05 노출. **`Server: Apache/2.4.52 (Ubuntu)`** = Apache 정확 버전 + OS 노출. CVE 자동 매핑: `searchsploit Apache 2.4.52` → CVE-2022-22720 (HTTP Smuggling) 등. 운영 시 `ServerTokens Prod` 설정으로 `Apache` 만 노출. **`PHPSESSID`** = PHP 7+ 사용 → DVWA endpoint 라는 신호. **`connect.sid`** 쿠키가 보이면 Express, **`JSESSIONID`** = Java/Tomcat. 헤더만으로 stack 90% 식별.

**OSS 도구로 자동화** (whatweb/httpx 추천):
```bash
# whatweb — 헤더+HTML+쿠키+favicon 시그니처로 자동 식별
whatweb -v http://10.20.30.80:3000
whatweb -v http://10.20.30.80                  # Apache 도 동시에

# httpx (projectdiscovery) — 대량 호스트 자동 핑거프린팅
echo -e "http://10.20.30.80:3000\nhttp://10.20.30.80" | httpx -tech-detect -title -status-code
```
whatweb 의 출력은 한 줄에 **프레임워크 + 라이브러리 + CMS + 서버 + WAF** 까지 묶여 있어 curl + grep 의 수십 줄 작업을 1 명령으로 대체한다.

### 4.2 쿠키 분석

```bash
# 쿠키 이름 + Secure/HttpOnly/SameSite 플래그 동시 점검
curl -sI http://10.20.30.80:3000 | grep -i set-cookie
echo '---'
# 다양한 endpoint 의 쿠키 차이
for path in "/" "/rest/products/search?q=test" "/api/Users"; do
  echo "[$path]"
  curl -sI "http://10.20.30.80:3000$path" | grep -i 'set-cookie' || echo '(no Set-Cookie)'
done
```

**예상 출력**:
```
Set-Cookie: language=en; Path=/
---
[/]
Set-Cookie: language=en; Path=/
[/rest/products/search?q=test]
(no Set-Cookie)
[/api/Users]
(no Set-Cookie)
```

> **해석 — 쿠키 이름 → 기술 스택 + 플래그 누락 = 즉시 취약**:
> - **`language=en`** = JuiceShop 의 i18n 쿠키. 비표준 명 = JuiceShop 자체 구현 (Express middleware).
> - **누락 플래그**: `HttpOnly` 없음 → JS 접근 가능 → XSS 시 쿠키 탈취. `Secure` 없음 → HTTP 평문 전송. `SameSite=Strict` 없음 → CSRF 가능.
> - **쿠키 이름 → 스택 매핑** (이름 보면 즉시 식별):
>   - `PHPSESSID` → PHP (DVWA)
>   - `JSESSIONID` → Java/Tomcat/Spring
>   - `ASP.NET_SessionId` → ASP.NET
>   - `connect.sid` → Node.js Express
>   - `_csrf`, `XSRF-TOKEN` → CSRF token 사용
>   - `token`, `accessToken` → JWT Bearer (Authorization 헤더)
> - **JuiceShop 은 JWT 사용** (`Authorization: Bearer eyJ...`) — Set-Cookie X = stateless 인증 패턴 식별.

### 4.3 에러 페이지 분석

```bash
# 존재하지 않는 경로로 404 에러 유도
curl -s http://10.20.30.80:3000/nonexistent_path_12345

# 잘못된 API 요청으로 에러 유도
curl -s http://10.20.30.80:3000/api/Products/abc

# 에러 메시지에서 기술 정보 추출
# - Express 버전
# - Node.js 버전
# - 스택 트레이스(stack trace) 중 파일 경로
```

### 4.4 JavaScript 소스 분석

```bash
# HTML에서 JS 파일 경로 추출
curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*\.js"' | head -10
echo '---'
# main.js 등에서 API 엔드포인트 + secret 패턴 추출
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
echo "Main JS: $MAIN_JS"
curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '/api/[a-zA-Z/]+|/rest/[a-zA-Z/]+' | sort -u | head -10
echo '---'
# 노출된 secret/key 패턴 정규식 검색
curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '(AKIA[0-9A-Z]{16}|sk_live_[0-9a-zA-Z]{24,}|api[_-]?key[\"'\'' :=]+[a-zA-Z0-9]{16,})' | head -5
```

**예상 출력**:
```
src="runtime.6271bf12036d6dd16b56.js"
src="polyfills.4dd0bf48c11ddd96fa1f.js"
src="main.bb5070bf0f9ce9b58d7c.js"
---
Main JS: main.bb5070bf0f9ce9b58d7c.js
/api/Addresss
/api/BasketItems
/api/Cards
/api/Challenges
/api/Complaints
/api/Feedbacks
/api/Quantitys
/api/Recycles
/api/SecurityAnswers
/api/SecurityQuestions
---
```

> **해석 — JS bundle 이 점검자에게 주는 보물**:
> - **endpoint 추출 10+** = REST API 매핑 자동화 — 수기 brute force 보다 100% 정확.
> - **`/api/Quantitys` (오타 — Quantities 정상)** = 의도적 이름. JuiceShop challenge.
> - **secret 패턴**: AKIA (AWS), sk_live (Stripe), api_key= 노출 없음 = 양호. 운영 환경에서는 **truffleHog / gitleaks** 정규식 200+ 패턴 자동 검색.
> - JS bundle 의 hash (`bb5070bf...`) = **build fingerprint** — 동일 hash 면 재빌드 X (운영자 게으름 신호).

> **OSS 대안 — JS bundle 분석 자동화**:
>
> ```bash
> # LinkFinder (Python) — JS 에서 endpoint·URL·variable 자동 추출
> pip install jsbeautifier && python3 LinkFinder.py -i http://10.20.30.80:3000/main.js -o cli
>
> # SecretFinder — JS 에서 secret/key 정규식 자동 매치
> python3 SecretFinder.py -i http://target/main.js -o cli
>
> # truffleHog v3 — 정규식 + 엔트로피 기반 secret hunting (file/git/url 모드)
> trufflehog filesystem /path/to/cloned/site
> ```

### 4.5 기술 스택 정리 템플릿

```
대상: http://10.20.30.80:3000
---
웹 서버: Express (Node.js)
프레임워크: Angular (프론트엔드)
DB: SQLite (JuiceShop 기본)
인증 방식: JWT (Bearer Token)
추가 정보:
- /ftp 디렉터리 노출
- robots.txt 존재
```

---

## 5. SSL/TLS 점검 (20분)

### 5.1 TLS의 중요성

| 항목 | HTTP | HTTPS |
|------|------|-------|
| 데이터 암호화 | X | O |
| 서버 인증 | X | O |
| 무결성 보장 | X | O |
| 중간자 공격 | 취약 | 방어 |

### 5.2 openssl을 이용한 TLS 점검

```bash
# TLS 연결 테스트 (대상이 HTTPS를 지원하는 경우)
# 실습 서버는 HTTP이므로, 개념 이해용 명령
# openssl s_client -connect example.com:443 -servername example.com < /dev/null 2>/dev/null | head -20

# 인증서 정보 확인
# openssl s_client -connect example.com:443 < /dev/null 2>/dev/null | openssl x509 -noout -dates -subject

# 지원 프로토콜 확인
# openssl s_client -connect example.com:443 -tls1_2 < /dev/null 2>&1 | grep "Protocol"
```

**OSS 도구로 자동화** (TLS 점검 표준):
```bash
# sslscan — 모든 cipher suite/protocol 자동 점검 + 약점 표시 (RC4/DES/SSLv3 등)
sudo apt install sslscan
sslscan example.com

# testssl.sh — 사실상 업계 표준 (Heartbleed/POODLE/BEAST 등 CVE 자동 검출)
git clone https://github.com/drwetter/testssl.sh.git ~/testssl
~/testssl/testssl.sh https://example.com           # 종합 진단
~/testssl/testssl.sh -p https://example.com        # 프로토콜만
~/testssl/testssl.sh --vulnerable https://example.com   # CVE 만

# nmap NSE — 빠른 1회성 점검
nmap --script ssl-enum-ciphers,ssl-cert -p 443 example.com
```
testssl.sh 는 **CVE-2014-0160 (Heartbleed)** 등 알려진 TLS 취약점을 한 번에 진단한다.

### 5.3 curl로 TLS 정보 확인

```bash
# Wazuh Dashboard 의 HTTPS 인증서 (실습 가능 대상)
curl -vI -k https://10.20.30.100:443 2>&1 | grep -E "SSL|TLS|subject|expire|issuer|ALPN" | head -10
echo '---'
# JuiceShop 은 HTTP 전용 — HTTPS 시도 시 에러 확인
curl -vI https://10.20.30.80:3000 2>&1 | head -8
```

**예상 출력**:
```
*  ALPN: server accepted h2
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
*  subject: CN=wazuh-dashboard
*  start date: Jan  1 00:00:00 2026 GMT
*  expire date: Dec 31 23:59:59 2027 GMT
*  issuer: CN=wazuh-dashboard
---
*   Trying 10.20.30.80:3000...
* Connected to 10.20.30.80 (10.20.30.80) port 3000
* ALPN: curl offers h2,http/1.1
* (304) (OUT), TLS handshake, Client hello (1):
* OpenSSL/3.0.2: error:0A00010B:SSL routines::wrong version number
* Closed connection
```

> **해석 — HTTPS 점검 vs 미지원**:
> - **Wazuh (10.20.30.100:443)**: TLS 1.3 ✓ + ALPN h2 (HTTP/2) ✓ — 표준 정상 통신. 그러나 **`subject: CN=wazuh-dashboard` + `issuer: CN=wazuh-dashboard`** = **자체 서명 인증서** = 운영 환경에서는 critical (CA 검증 X = MITM 가능). `-k` 가 없으면 curl 거부 = 운영자가 인증서 신뢰 체인 무시 신호.
> - **expire date** 가 1년 이상이면 정상 (Let's Encrypt 90일 / 일반 1년).
> - **JuiceShop HTTPS 시도**: `wrong version number` = HTTP 평문 응답을 TLS 로 파싱 → HTTPS 미지원 확정. 운영 환경에서 HTTP 전용 = OWASP A02 Cryptographic Failures. **HSTS preload list** 등록도 못함.
> - **점검 보고서**: HTTP-only 서비스 = critical, 자체 서명 cert = high, 만료 임박 = high.

### 5.4 점검 체크리스트

```
[ ] HTTPS 지원 여부
[ ] HTTP → HTTPS 리다이렉트 여부
[ ] TLS 1.2 이상만 허용하는지
[ ] 인증서 유효기간
[ ] 인증서 발급자 (자체 서명 여부)
[ ] 취약한 암호 스위트 (RC4, DES, 3DES 등)
[ ] HSTS 헤더 설정 여부
```

---

## 6. 종합 실습: 정보수집 보고서 작성 (30분)

### 6.1 보고서 템플릿

```bash
cat > /tmp/recon_report.md << 'EOF'
# 정보수집 보고서

## 1. 대상 정보
- URL: http://10.20.30.80:3000
- 서비스: OWASP JuiceShop
- 점검 일시: $(date)

## 2. 기술 스택
- 웹 서버:
- 프레임워크:
- 데이터베이스:
- 인증 방식:

## 3. 발견된 디렉터리/파일
| 경로 | 응답코드 | 설명 |
|------|---------|------|
| / | 200 | 메인 페이지 |
| /ftp | | |
| /api | | |

## 4. 보안 헤더 점검
| 헤더 | 존재여부 | 값 |
|------|---------|-----|
| X-Frame-Options | | |
| X-Content-Type-Options | | |
| Content-Security-Policy | | |

## 5. TLS 설정
- HTTPS 지원:
- HSTS 설정:

## 6. 정보 노출 항목
(에러 메시지, 버전 정보 등)

## 7. 요약 및 다음 단계
EOF

echo "보고서 템플릿이 /tmp/recon_report.md에 생성되었습니다."
```

---

## 7. 실습 과제

### 과제 1: 디렉터리 스캐닝
1. 제공된 wordlist로 JuiceShop의 숨겨진 경로를 모두 찾아라
2. 발견된 각 경로의 내용을 확인하고 위험도를 평가하라
3. `/ftp` 디렉터리에서 다운로드 가능한 파일 목록을 작성하라

### 과제 2: 기술 스택 식별
1. JuiceShop의 기술 스택을 모두 식별하라 (서버, 프레임워크, DB, 인증)
2. Apache(포트 80)의 기술 스택도 동일하게 식별하라
3. 두 서비스의 보안 헤더를 비교 분석하라

### 과제 3: 정보수집 보고서
1. 위 템플릿을 기반으로 JuiceShop 정보수집 보고서를 완성하라
2. 발견된 정보 중 공격에 활용될 수 있는 항목을 3가지 이상 서술하라

---

## 8. 요약

| 기법 | 도구/명령 | 발견 가능한 것 |
|------|----------|----------------|
| robots.txt 분석 | curl | 숨겨진 경로 힌트 |
| 디렉터리 스캐닝 | curl + wordlist | 숨겨진 페이지, 파일 |
| 헤더 분석 | curl -I | 서버 종류, 버전 |
| 에러 분석 | curl + 잘못된 요청 | 내부 구조, 파일 경로 |
| TLS 점검 | openssl, curl -v | 암호화 설정 |

**다음 주 예고**: Week 04 - 인증/세션 관리 점검. 비밀번호 정책, 세션 타임아웃, JWT 검증을 학습한다.

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### DVWA 보안 레벨 변경 방법 (웹 UI)

> **DVWA URL:** `http://10.20.30.80:8080`

1. 브라우저에서 `http://10.20.30.80:8080` 접속 → 로그인 (admin / password)
2. 좌측 메뉴 **DVWA Security** 클릭
3. **Security Level** 드롭다운에서 실습 목적에 맞는 레벨 선택:
   - **Low**: 필터 없음 → 정보수집 기법이 모두 동작
   - **Medium**: 일부 헤더 제한 → 정보수집 우회 필요
   - **High**: 강화된 접근 제어 → 고급 정보수집 기법 실습
   - **Impossible**: 안전한 구현 참조
4. **Submit** 클릭하여 적용
5. 좌측 메뉴에서 실습 항목 선택 후 각 레벨에서의 차이점 비교
6. 각 항목 페이지 하단 **View Source** 로 레벨별 소스 코드 비교 분석

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

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

---

## 실제 사례 (WitFoo Precinct 6 — 정찰 패턴 1:1 매칭)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.
> 본 lecture *정보수집 (T1595·T1592)* 학습 목표에 매칭되는 *외부 mass discovery scan* record 추출.

### Case 1: 단일 external IP × 30 internal hosts × 54 ports — 1초 burst

**메타**

| 항목 | 값 |
|------|---|
| 시각 | 2023-07-10 01:33:46 UTC (timestamp `1688960026`) |
| src | `100.64.20.230` (외부 단일 IP) |
| dst | 172.16.x ~ 172.31.x **30개 distinct host** |
| dst ports | **54 distinct** (대표: 22·88·623·1433·5060·5632·8333·9418·31337) |
| 이벤트 수 | 208 (firewall_action=block, severity=warning) |
| Precinct 6 suspicion_score | 0.92 |

**원본 firewall 로그 발췌** (`message_sanitized`):

```text
<180>Jul 09 USER-9564 21:56:51: USER-0010-0324
  Deny tcp src outside:100.64.20.230/CRED-250460
  dst DMZ:172.28.21.208/22  by ORG-1738-group "outside_ORG-1738_in"

<180>Jul 09 USER-9564 21:56:51: USER-0010-0324
  Deny tcp src outside:100.64.20.230/CRED-250460
  dst DMZ:172.16.249.139/1433 by ORG-1738-group "outside_ORG-1738_in"

<180>Jul 09 USER-9564 21:56:51: USER-0010-0324
  Deny udp src outside:100.64.20.230/CRED-250460
  dst DMZ:172.27.35.73/623  by ORG-1738-group "outside_ORG-1738_in"

<180>Jul 09 USER-9564 21:56:51: USER-0010-0324
  Deny tcp src outside:100.64.20.230/CRED-250460
  dst DMZ:172.31.224.33/31337 by ORG-1738-group "outside_ORG-1738_in"
```

**해석 — 본 lecture 와의 매핑**

| 정보수집 학습 항목 | 본 record 에서의 증거 |
|--------------------|---------------------|
| **호스트 식별** | 30개 distinct dst IP (172.16~172.31 대역 sweep) |
| **서비스 지문 (port)** | 54 distinct port — SSH(22)·Kerberos(88)·IPMI(623)·MSSQL(1433)·SIP(5060)·PCAnywhere(5632)·Bitcoin(8333)·git(9418)·elite(31337) |
| **속도/패턴** | 모든 이벤트 동일 timestamp → 자동화 도구 (사람 손 아님) |
| **결과** | 외부 firewall 가 *block* 으로 차단했으나 **scan 자체는 완료** — 닫힌 포트는 RST/timeout 응답으로 attacker 가 "이 호스트엔 이 서비스 없음" 정보 획득 |

**점검 관점 액션 아이템**:
1. 본 패턴은 외부 *공격 표면 매핑* 에 해당하므로 점검 보고서 §정찰 단계 *attacker view* 항목에 *동일 실험 시 유사 결과 가능* 명시.
2. 31337·5632·623 등 *드물게 열려 있어선 안 되는 포트* 가 dst 에 포함된 경우 별도 *비표준 포트 노출* 챕터로 분리.
3. 점검 도구 (nmap·masscan) 가 동일 burst pattern 을 만들지 않도록 *--scan-delay* 또는 *-T2* 사용 — 본 record 가 *완전 burst* 인 이유는 자동화 + 의도적 비식별이라는 점 강조.




---

## 부록: 학습 OSS 도구 매트릭스 (lab week03 — XSS)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 reflected | curl / **XSStrike** / **dalfox** / Burp Active Scan |
| 2 reflected payload | curl batch / **PayloadsAllTheThings** / XSStrike --fuzzer / OWASP Cheatsheet |
| 3 stored | curl 2 단계 / XSStrike --crawl / dalfox PUT / **XSS Hunter** OOB |
| 4 DOM | curl + grep sink / XSStrike --dom / **DevTools Sources** / **RetireJS** |
| 5 cookie steal | mock 서버 (python http.server) / **webhook.site** / **BeEF C2** / DNS exfil |
| 6 bypass | 5 인코딩 카테고리 (대소문자/엔티티/URL/Unicode/이중) / dalfox --waf-evasion / **wfuzz** 인코딩 |
| 7 CSP | curl -I / **Google CSP Evaluator** / **Mozilla Observatory** / nonce 누출 / JSONP 우회 |
| 8 keylogger | JS payload / BeEF Get Form Values / XSS Hunter screenshot |
| 9 phishing | innerHTML 가짜 폼 / **BeEF Pretty Theft** / **Gophish** 캠페인 |
| 10 framework | **RetireJS** / Angular/React/Vue 위험 함수 표 / **semgrep p/react** / **eslint-plugin-security** |
| 11 polyglot | Mathias / 0xsobky / **PortSwigger Cheatsheet** / wfuzz |
| 12 auto scan | XSStrike / dalfox / **OWASP ZAP** / wapiti / nuclei (5 도구 비교표) |
| 13 defense | **DOMPurify** / **bleach** Python / **OWASP Java Encoder** / **Trusted Types** |
| 14 auto script | bash for / Python requests + BS / **Playwright** headless / CI/CD GitHub Actions |
| 15 verification | 자동 보고서 / **DefectDojo** Finding 관리 / sha256 |

### 학생 환경 준비
```bash
git clone --depth 1 https://github.com/s0md3v/XSStrike.git ~/XSStrike
sudo apt install -y dalfox wapiti
docker run -d -p 3000:3000 --name beef beefproject/beef
docker run -d --name xsshunter -p 8080:8080 mandatoryprogrammer/xsshunter_express
npm install -g retire wappalyzer
pip install playwright; playwright install chromium
# Gophish: https://github.com/gophish/gophish/releases
```
