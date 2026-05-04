# Week 11: 에러 처리 / 정보 노출 점검

## 학습 목표
- 부적절한 에러 처리가 보안에 미치는 영향을 이해한다
- 스택 트레이스, 디버그 모드에서 노출되는 정보를 분석한다
- 디렉터리 리스팅 취약점을 점검한다
- 정보 노출의 다양한 경로를 체계적으로 점검할 수 있다

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
- HTTP 응답 코드 이해 (200, 404, 500 등)
- curl 사용법

---

## 1. 정보 노출의 위험 (15분)

### 1.1 OWASP에서의 위치

**A05:2021 Security Misconfiguration** 카테고리.
잘못된 설정으로 인한 정보 노출은 공격의 첫 단추가 된다.

### 1.2 노출 가능한 정보

| 정보 유형 | 노출 경로 | 위험 |
|----------|----------|------|
| 서버 버전 | HTTP 헤더 | CVE 검색 → 공격 |
| 파일 경로 | 스택 트레이스 | 내부 구조 파악 |
| DB 정보 | SQL 에러 | SQLi 공격 보조 |
| 소스 코드 | 디버그 모드 | 로직 분석 |
| 사용자 목록 | 열거 공격 | 무차별 대입 대상 |
| API 키/토큰 | 소스 코드, 설정 파일 | 인증 우회 |

---

## 2. 스택 트레이스 / 에러 메시지 (30분)

> **이 실습을 왜 하는가?**
> "에러 처리 / 정보 노출 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 에러 유도 기법

> **실습 목적**: 에러 메시지와 HTTP 헤더를 통한 정보 노출 취약점을 점검한다
>
> **배우는 것**: 스택 트레이스, 디버그 정보, 서버 버전 등 공격에 활용 가능한 정보 노출을 탐지하는 방법을 배운다
>
> **결과 해석**: 에러 페이지에 DB 종류, 파일 경로, 프레임워크 버전이 노출되면 정보 유출 취약점이다
>
> **실전 활용**: 정보 노출은 그 자체로 위험하진 않지만, 후속 공격(SQLi, 버전별 익스플로잇)의 핵심 정보를 제공한다

```bash
echo "=== 6 에러 유도 시나리오 매트릭스 ==="
test_err() {
  local name="$1" cmd="$2"
  local body=$(eval "$cmd" 2>/dev/null | head -c 200)
  local has_stack=$(echo "$body" | grep -ciE "at .*\.(js|ts):[0-9]+" | head -1)
  local has_path=$(echo "$body" | grep -ciE "/app/|/home/|/usr/|node_modules" | head -1)
  local has_dbms=$(echo "$body" | grep -ciE "sqlite|mysql|postgres|sequelize" | head -1)
  printf "%-25s stack:%s path:%s dbms:%s\n" "$name" "$has_stack" "$has_path" "$has_dbms"
}
test_err "404 (없는 경로)"      "curl -s 'http://10.20.30.80:3000/nonexistent_xyz123'"
test_err "타입 에러 /api/x/abc"  "curl -s 'http://10.20.30.80:3000/api/Products/abc'"
test_err "SQL 에러 (q=')"        "curl -s \"http://10.20.30.80:3000/rest/products/search?q=%27\""
test_err "빈 JSON body"          "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H 'Content-Type: application/json' -d '{}'"
test_err "잘못된 Content-Type"   "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H 'Content-Type: text/plain' -d 'not json'"
test_err "매우 긴 입력 (10K)"    "curl -s \"http://10.20.30.80:3000/rest/products/search?q=\$(python3 -c 'print(\"A\"*10000)')\""
```

**예상 출력**:
```
=== 6 에러 유도 시나리오 매트릭스 ===
404 (없는 경로)           stack:0 path:0 dbms:0
타입 에러 /api/x/abc      stack:1 path:1 dbms:1
SQL 에러 (q=')            stack:1 path:0 dbms:1
빈 JSON body              stack:0 path:0 dbms:0
잘못된 Content-Type       stack:1 path:1 dbms:0
매우 긴 입력 (10K)        stack:0 path:0 dbms:0
```

> **해석 — 6 시나리오 중 3개에서 critical 정보 노출**:
> - **타입 에러 (3/3 jackpot)** = stack + path + dbms 모두 노출 = ★ critical. CVSS 7.5.
> - **SQL 에러 (2/3)** = stack + dbms 노출 (path X — query 매개라 응답에 file 경로 안 나옴).
> - **잘못된 Content-Type (2/3)** = stack + path 노출. Express 가 JSON parse 실패 시 stack 응답에 포함.
> - **404 / 빈 body / 긴 입력 (0/3)** = 양호. JuiceShop 의 일관 처리.
> - **권고**: `NODE_ENV=production` + Express error handler:
>   ```js
>   app.use((err, req, res, next) => {
>     console.error(err.stack);  // 서버 로그만
>     res.status(500).json({ error: 'Internal Server Error' });  // 클라이언트는 일반 메시지
>   });
>   ```
> - **OWASP A05** + **CWE-209** Information Exposure Through an Error Message.

### 2.2 스택 트레이스 분석

```bash
# 에러 응답에서 민감 정보 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q='" | python3 -c "  # silent 모드
import sys, json

data = sys.stdin.read()
try:
    parsed = json.loads(data)
    error = parsed.get('error', {})
    if isinstance(error, dict):
        message = error.get('message', '')
        stack = error.get('stack', '')
    else:
        message = str(error)
        stack = ''
except:
    message = data[:500]
    stack = ''

print('=== 에러 메시지 분석 ===')
print(f'메시지: {message[:200]}')

if stack:
    print(f'\n스택 트레이스 (처음 5줄):')
    for i, line in enumerate(stack.split('\n')[:5]):   # 반복문 시작
        print(f'  {line.strip()}')

# 노출된 정보 식별
info_found = []
full_text = message + stack
if 'SQLITE' in full_text.upper() or 'sqlite' in full_text:
    info_found.append('DB 종류: SQLite')
if '/app/' in full_text or '/home/' in full_text:
    info_found.append('파일 경로 노출')
if 'node_modules' in full_text:
    info_found.append('Node.js 사용 확인')
if 'at ' in full_text and '.js:' in full_text:
    info_found.append('JS 파일명 + 줄번호')

print(f'\n노출된 정보: {info_found if info_found else \"없음\"}')" 2>/dev/null
```

### 2.3 에러 응답 비교 (JuiceShop vs Apache)

```bash
echo "=== 4 endpoint 의 404 페이지 비교 ==="
compare_404() {
  local label="$1" url="$2"
  read code size < <(curl -s -o /tmp/404.html -w "%{http_code} %{size_download}" "$url/nonexistent_xyz")
  server=$(curl -sI "$url/nonexistent_xyz" | grep -i '^server:' | head -1 | tr -d '\r' | head -c 50)
  version_leak=$(grep -ciE "apache/[0-9]|nginx/[0-9]|express|version|server at" /tmp/404.html | head -1)
  echo "[$label]"
  echo "  $server"
  echo "  code=$code size=${size}B / version_leak_lines=$version_leak"
  echo "  body 첫 줄: $(head -1 /tmp/404.html | head -c 80)"
}
compare_404 "JuiceShop" "http://10.20.30.80:3000"
compare_404 "Apache+ModSec" "http://10.20.30.80:80"
compare_404 "Wazuh" "https://10.20.30.100:443"
compare_404 "OpenCTI" "http://10.20.30.100:8080"
```

**예상 출력**:
```
=== 4 endpoint 의 404 페이지 비교 ===
[JuiceShop]
  
  code=200 size=1987B / version_leak_lines=0
  body 첫 줄: <!DOCTYPE html>
[Apache+ModSec]
  Server: Apache/2.4.52 (Ubuntu)
  code=404 size=276B / version_leak_lines=2
  body 첫 줄: <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
[Wazuh]
  
  code=200 size=4567B / version_leak_lines=0
  body 첫 줄: <!DOCTYPE html>
[OpenCTI]
  Server: nginx/1.21.6
  code=404 size=153B / version_leak_lines=1
  body 첫 줄: <html><head><title>404 Not Found</title></head>
```

> **해석 — 4 endpoint 의 404 처리 비교**:
> - **JuiceShop 200 + SPA HTML** = Angular routing — 모든 unknown path 가 index.html 반환. 보안상 양호 (path 노출 X).
> - **Apache 404 + Server 헤더 노출** = ★ critical. 'Apache/2.4.52 (Ubuntu)' = 정확한 버전 + OS. CVE-2022-22720 등 검색.
> - **Apache body 의 'Server at <hostname> Port 80' 푸터** = ServerSignature on (default). `ServerSignature Off` + `ServerTokens Prod` 로 제거 권장.
> - **Wazuh 200 + SPA** = JuiceShop 과 동일 패턴 — 양호.
> - **OpenCTI nginx/1.21.6** = nginx 정확 버전 노출. CVE-2021-23017 (off-by-one) 등 매핑.
> - **권고 (nginx)**: `server_tokens off;` + `proxy_hide_header Server`. (Apache) `ServerTokens Prod` + `ServerSignature Off`.

---

## 3. 디버그 모드 점검 (20분)

### 3.1 디버그 엔드포인트 탐색

```bash
echo "=== 24 디버그 endpoint sweep — 200/403 만 출력 ==="
PATHS=(
  "debug" "console" "status" "health" "healthcheck"
  "info" "env" "config" "metrics" "trace"
  "actuator" "actuator/env" "actuator/health"
  "_debug" "__debug__" "phpinfo.php"
  "server-status" "server-info"
  "elmah.axd" "trace.axd"
  ".env" "config.json" "package.json" "robots.txt"
)
hits=0
for path in "${PATHS[@]}"; do
  read code size < <(curl -s -o /dev/null -w "%{http_code} %{size_download}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code ${size}B] /$path"
    [ "$code" = "200" ] && hits=$((hits+1))
  fi
done
echo "---"
echo "노출 endpoint: $hits 건"
```

**예상 출력**:
```
=== 24 디버그 endpoint sweep — 200/403 만 출력 ===
[500 78B] /debug
[403 89B] /env
[200 1234B] /metrics
[200 89B] /robots.txt
---
노출 endpoint: 2 건
```

> **해석 — 24 endpoint 중 2건 노출 + 2건 응답**:
> - **/metrics 200 (1234B)** = ★ critical (Prometheus 형식 노출). 다음 step §3.2 분석.
> - **/debug 500** = endpoint 존재 + 에러 응답. 500 = 운영자가 차단 안 했고 처리 도중 fail. CVSS 5.3.
> - **/env 403** = endpoint 존재 (404 아니라 403) = JuiceShop 이 explicit 차단 시도. 운영 시 인증 우회 시 노출 가능.
> - **/robots.txt 200** = 정상 (week03 학습).
> - **권고**: `/metrics`, `/health`, `/actuator/*` 등 운영 endpoint 는 internal network only (nginx `allow 10.0.0.0/8; deny all;`).
> - **JuiceShop challenge ID**: 'Forgotten Sales Backup' / 'Confidential Document' — 일부 노출 endpoint 활용.

### 3.2 JuiceShop 메트릭 엔드포인트

```bash
echo "=== /metrics 내용 분석 (Prometheus format) ==="
curl -s http://10.20.30.80:3000/metrics | head -30
echo "---"
echo "=== 메트릭에서 추출 가능한 민감 정보 ==="
M=$(curl -s http://10.20.30.80:3000/metrics)
echo "  Node.js 버전: $(echo "$M" | grep -oE 'nodejs_version_info\{version="[^"]+"' | head -1)"
echo "  메모리 사용량: $(echo "$M" | grep -oE 'process_resident_memory_bytes [0-9.e+]+' | head -1)"
echo "  CPU 시간: $(echo "$M" | grep -oE 'process_cpu_seconds_total [0-9.]+' | head -1)"
echo "  HTTP 요청 수: $(echo "$M" | grep -oE 'http_requests_total\{[^}]+\} [0-9]+' | wc -l) 라인"
echo "  ★ challenges_solved: $(echo "$M" | grep -oE 'challenges_solved\{[^}]+\}[ ]+[0-9]+' | head -3)"
```

**예상 출력**:
```
=== /metrics 내용 분석 (Prometheus format) ===
# HELP process_cpu_user_seconds_total Total user CPU time spent in seconds.
# TYPE process_cpu_user_seconds_total counter
process_cpu_user_seconds_total 12.34

# HELP nodejs_version_info Node.js version info.
nodejs_version_info{version="v18.16.1",major="18",minor="16",patch="1"} 1
...
=== 메트릭에서 추출 가능한 민감 정보 ===
  Node.js 버전: nodejs_version_info{version="v18.16.1"
  메모리 사용량: process_resident_memory_bytes 245678080
  CPU 시간: process_cpu_seconds_total 23.45
  HTTP 요청 수: 47 라인
  ★ challenges_solved: challenges_solved{difficulty="1"} 3
```

> **해석 — /metrics 가 점검자에게 주는 정보**:
> - **nodejs_version_info v18.16.1** = ★ Node.js 정확 버전 → CVE 매핑. `v18.16.0` 이하 = CVE-2023-30581 (path traversal) 등.
> - **process_resident_memory 245MB** = 운영자에게 정상 / 공격자에게는 DoS 입력 크기 가늠.
> - **HTTP 요청 47 라인** = endpoint 분포 = OAS 없이도 API 카탈로그 추정.
> - **challenges_solved** = JuiceShop 의 chl 진행 상태 노출 = 점검자가 어느 challenge solved 됐는지 정보 획득.
> - **권고**: `/metrics` 는 prometheus scraper 만 (BasicAuth 또는 internal IP 제한). 또는 `/internal/metrics` 등 unguessable path.

### 3.3 소스맵 파일 노출

```bash
# Angular 앱의 소스맵(.map) 파일이 노출되는지 확인
# 소스맵이 있으면 프론트엔드 원본 소스 코드를 복원할 수 있음
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS 파일: $MAIN_JS"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/${MAIN_JS}.map")
  echo "소스맵 ($MAIN_JS.map): HTTP $code"
  if [ "$code" = "200" ]; then
    echo "소스맵 노출됨! 소스 코드 복원 가능"
    curl -s "http://10.20.30.80:3000/${MAIN_JS}.map" | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin)
sources = data.get('sources', [])
print(f'소스 파일 수: {len(sources)}')
for s in sources[:10]:                                 # 반복문 시작
    print(f'  {s}')
if len(sources) > 10:
    print(f'  ... 외 {len(sources)-10}개')
" 2>/dev/null
  fi
fi
```

---

## 4. 디렉터리 리스팅 (25분)

### 4.1 디렉터리 리스팅이란?

디렉터리 리스팅은 웹 서버가 디렉터리의 파일 목록을 보여주는 기능이다.
개발/테스트 환경에서는 편리하지만, 운영 환경에서는 보안 위험이다.

### 4.2 디렉터리 리스팅 점검

```bash
echo "=== JuiceShop + Apache 디렉토리 리스팅 매트릭스 ==="
test_listing() {
  local server="$1" base="$2" dir="$3"
  read code size < <(curl -s -o /tmp/listing.html -w "%{http_code} %{size_download}" "$base$dir")
  listing=$(grep -ciE "index of|listing|directory|<a href=" /tmp/listing.html | head -1)
  flag=""
  [ "$code" = "200" -a "$listing" -gt 5 ] && flag="★ 리스팅 활성"
  printf "%-12s %-20s %-6s %-6s %-3s %s\n" "$server" "$dir" "$code" "$size" "$listing" "$flag"
}
printf "%-12s %-20s %-6s %-6s %-3s %s\n" "server" "dir" "code" "size" "ah" "verdict"
for d in "/" "/ftp" "/ftp/" "/assets" "/assets/public" "/encryptionkeys"; do
  test_listing "JuiceShop" "http://10.20.30.80:3000" "$d"
done
for d in "/" "/icons/" "/manual/" "/cgi-bin/"; do
  test_listing "Apache" "http://10.20.30.80:80" "$d"
done
```

**예상 출력**:
```
=== JuiceShop + Apache 디렉토리 리스팅 매트릭스 ===
server       dir                  code   size   ah  verdict
JuiceShop    /                    200    1987   12  
JuiceShop    /ftp                 200    2345   18  ★ 리스팅 활성
JuiceShop    /ftp/                200    2345   18  ★ 리스팅 활성
JuiceShop    /assets              404    139    0   
JuiceShop    /assets/public       200    1234   8   ★ 리스팅 활성
JuiceShop    /encryptionkeys      200    567    6   ★ 리스팅 활성
Apache       /                    200    11321  54  ★ 리스팅 활성
Apache       /icons/              200    45678  120 ★ 리스팅 활성
Apache       /manual/             200    8901   24  ★ 리스팅 활성
Apache       /cgi-bin/            403    89     0   
```

> **해석 — 8/10 리스팅 활성 = OWASP A05 광범위**:
> - **/ftp 활성** = week03 학습 — 9 백업 파일 노출 (package.json.bak / coupons / suspicious_errors).
> - **/encryptionkeys 활성** = ★ critical = JuiceShop challenge. RSA private key 노출 → JWT 변조 가능 (week04 alg confusion).
> - **/assets/public 활성** = 업로드 파일 + 이미지 노출. 사용자 업로드 파일 직접 접근.
> - **Apache /icons/ 120 항목** = 기본 설치 아이콘 노출. 운영 환경에서 `Options -Indexes` 적용 누락.
> - **Apache /manual/ 활성** = Apache 매뉴얼 노출 = 정확한 버전 식별 + CVE 매핑.
> - **권고 (Apache)**: `<Directory /var/www/html>` `Options -Indexes` + `IndexIgnore *`. (Express) `express.static()` 의 `index: false`.

### 4.3 JuiceShop /ftp 상세 탐색

```bash
# /ftp 디렉터리의 파일 목록과 내용 확인
echo "=== /ftp 파일 목록 ==="
curl -s http://10.20.30.80:3000/ftp/ | python3 -c "    # silent 모드
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for f in data:                                 # 반복문 시작
            print(f'  {f}')
    elif isinstance(data, dict):
        for f in data.get('data', data.get('files', [])):  # 반복문 시작
            if isinstance(f, str):
                print(f'  {f}')
            else:
                print(f'  {f.get(\"name\", f)}')
except:
    print(sys.stdin.read()[:500])
" 2>/dev/null

# 각 파일 내용 확인
echo ""
echo "=== 주요 파일 내용 ==="
for file in "legal.md" "acquisitions.md" "package.json.bak" "coupons_2013.md.bak" "eastere.gg"; do  # 반복문 시작
  echo "--- $file ---"
  curl -s "http://10.20.30.80:3000/ftp/$file" 2>/dev/null | head -5  # silent 모드
  echo ""
done
```

---

## 5. 사용자 열거 (User Enumeration) (20분)

### 5.1 열거 공격이란?

에러 메시지의 차이를 이용하여 유효한 사용자명/이메일을 알아내는 공격이다.

```
존재하는 계정: "비밀번호가 틀렸습니다" ← 계정 존재 확인!
미존재 계정: "계정을 찾을 수 없습니다" ← 계정 없음 확인!

안전한 메시지: "이메일 또는 비밀번호가 올바르지 않습니다"
                (존재 여부를 알 수 없음)
```

### 5.2 JuiceShop 사용자 열거 테스트

```bash
echo "=== 사용자 열거 — 로그인 + 회원가입 + 비번 재설정 3 채널 ==="
test_enum() {
  local label="$1" payload="$2" url="$3"
  start=$(date +%s%N)
  body=$(curl -s -X POST "$url" -H 'Content-Type: application/json' -d "$payload" 2>/dev/null)
  ms=$(( ($(date +%s%N) - start) / 1000000 ))
  msg=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); err=d.get('error',''); print(str(err)[:60] if err else '(no error)')" 2>/dev/null)
  printf "  %-30s %-5sms %s\n" "$label" "$ms" "$msg"
}
echo "[1] 로그인 endpoint:"
test_enum "존재 admin + wrong" '{"email":"admin@juice-sh.op","password":"wrong"}' "http://10.20.30.80:3000/rest/user/login"
test_enum "미존재 + wrong"     '{"email":"nobody@nowhere.com","password":"wrong"}' "http://10.20.30.80:3000/rest/user/login"
echo ""
echo "[2] 회원가입 endpoint:"
test_enum "존재 admin"          '{"email":"admin@juice-sh.op","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' "http://10.20.30.80:3000/api/Users/"
test_enum "신규 brand_new_xyz"  '{"email":"brand_new_xyz999@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' "http://10.20.30.80:3000/api/Users/"
```

**예상 출력**:
```
=== 사용자 열거 — 로그인 + 회원가입 + 비번 재설정 3 채널 ===
[1] 로그인 endpoint:
  존재 admin + wrong              52   ms Invalid email or password.
  미존재 + wrong                  47   ms Invalid email or password.

[2] 회원가입 endpoint:
  존재 admin                      89   ms {'message': 'email must be unique', 'name': 'SequelizeUniqueConstraintError'}
  신규 brand_new_xyz              156  ms (no error)
```

> **해석 — 로그인 안전 / 회원가입 ★ 열거 가능**:
> - **[1] 로그인** = 두 메시지 동일 ('Invalid email or password.') = ★ 양호. 응답 시간도 ~50ms 일정 = timing attack 면역.
> - **[2] 회원가입** = ★ critical. 'email must be unique' 메시지가 *존재하는 이메일* 만 노출 → 공격자가 SecLists 의 email list 1줄 단위로 가입 시도하면 가입자 list 추출 가능.
> - **응답 시간 차이**: 회원가입 89ms vs 156ms = ★ timing attack 가능 (DB INSERT vs query failure 차이).
> - **CVSS 5.3** (Information Disclosure). 회원가입 + brute force 결합 = 정확한 사용자 list 획득.
> - **권고**: 모든 인증 채널에서 *동일 메시지 + 동일 응답 시간*. "이메일 / 비번 X" / "재설정 링크 발송" (이메일 존재 무관하게 동일).
> - **JuiceShop challenge**: 'GDPR Data Erasure' / 'CSRF' 등에서 활용.

### 5.3 회원가입에서의 열거

```bash
# 이미 존재하는 이메일로 가입 시도
echo ""
echo "=== 회원가입 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null  # 요청 데이터(body)

echo ""
echo "새 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"brand_new_user@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null  # 요청 데이터(body)
```

### 5.4 비밀번호 찾기에서의 열거

```bash
# 비밀번호 재설정 기능에서 열거
echo ""
echo "=== 비밀번호 재설정 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3  # 요청 데이터(body)

echo ""
echo "미존재 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@test.com","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3  # 요청 데이터(body)
```

---

## 6. 종합 정보 노출 점검 스크립트 (20분)

```bash
# 자동 점검 스크립트
python3 << 'PYEOF'                                     # Python 스크립트 실행
import requests, json

BASE = "http://10.20.30.80:3000"
findings = []

print("=" * 60)
print("정보 노출 종합 점검")
print("=" * 60)

# 1. 서버 헤더
r = requests.head(BASE, timeout=5)
for header in ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]:  # 반복문 시작
    val = r.headers.get(header)
    if val:
        findings.append(f"헤더 정보 노출: {header}: {val}")
        print(f"[!] {header}: {val}")

# 2. 보안 헤더 미설정
for header in ["X-Frame-Options", "X-Content-Type-Options",  # 반복문 시작
               "Content-Security-Policy", "Strict-Transport-Security"]:
    if header not in r.headers:
        findings.append(f"보안 헤더 미설정: {header}")
        print(f"[-] {header}: 미설정")

# 3. 에러 정보 노출
r = requests.get(f"{BASE}/rest/products/search?q='", timeout=5)
try:
    err = r.json()
    if "error" in err:
        error_msg = str(err["error"])
        if "SQLITE" in error_msg.upper() or "stack" in error_msg.lower():
            findings.append("에러 메시지에 DB/스택 정보 노출")
            print(f"[!] 에러에 내부 정보 포함")
except:
    pass

# 4. 디렉터리/파일 노출
sensitive_paths = ["ftp", "metrics", ".env", "package.json", "encryptionkeys"]
for path in sensitive_paths:                           # 반복문 시작
    r = requests.get(f"{BASE}/{path}", timeout=5)
    if r.status_code == 200:
        findings.append(f"민감 경로 접근 가능: /{path}")
        print(f"[!] /{path}: 접근 가능 (HTTP {r.status_code})")

# 5. 요약
print(f"\n{'=' * 60}")
print(f"총 발견 사항: {len(findings)}건")
for i, f in enumerate(findings, 1):                    # 반복문 시작
    print(f"  {i}. {f}")
PYEOF
```

---

## 7. 실습 과제

### 과제 1: 에러 메시지 분석
1. 다양한 방법으로 JuiceShop에 에러를 유발하라 (최소 5가지)
2. 각 에러 응답에서 노출되는 정보를 분석하라
3. 가장 많은 정보를 노출하는 에러 패턴을 보고하라

### 과제 2: 정보 노출 점검
1. JuiceShop과 Apache의 디렉터리 리스팅 상태를 비교하라
2. 디버그/상태 엔드포인트를 모두 탐색하라
3. 소스맵 파일 노출 여부를 확인하라

### 과제 3: 사용자 열거
1. 로그인, 회원가입, 비밀번호 재설정에서 사용자 열거가 가능한지 테스트하라
2. 열거 가능/불가능한 기능을 구분하고 에러 메시지를 비교하라
3. 안전한 에러 메시지 예시를 제안하라

---

## 8. 요약

| 취약점 | 확인 방법 | 위험도 | 방어 |
|--------|----------|--------|------|
| 스택 트레이스 노출 | 에러 유도 | 중 | 운영 환경 에러 숨김 |
| 서버 버전 노출 | 헤더 확인 | 하 | 헤더 제거/변경 |
| 디렉터리 리스팅 | 디렉터리 URL 접근 | 중 | Options -Indexes |
| 디버그 모드 | 엔드포인트 탐색 | 상 | 운영 환경 비활성화 |
| 소스맵 노출 | .map 파일 접근 | 중 | 운영 빌드에서 제거 |
| 사용자 열거 | 에러 메시지 비교 | 중 | 일관된 에러 메시지 |

**다음 주 예고**: Week 12 - API 보안 점검. REST API 인증, Rate Limiting, Swagger 노출을 학습한다.

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

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

---

## 실제 사례 (WitFoo Precinct 6 — HTTP 4xx/5xx 응답 분포)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *에러 처리 / 정보 노출 점검* 학습 항목 (5xx 시 stack trace · 4xx 시 정보 누설) 과 매핑되는 dataset 의 HTTP-status message_type 분포.

### Case 1: HTTP error code 별 dataset 분포

| message_type | 의미 | 건수 |
|--------------|------|------|
| **403** Forbidden | 인증/인가 실패 | 522 |
| **404** Not Found | 자원 부재 | 176 |
| **410** Gone | 영구 삭제 | 523 |
| **412** Precondition Failed | 조건부 요청 실패 | 267 |
| **413** Payload Too Large | 본문 초과 | 292 |
| **431** Request Header Too Large | 헤더 초과 | 348 |
| **510** Not Extended | 확장 필요 | 699 |
| 합계 | — | 2,827 |

### Case 2: 410 Gone — 본 dataset 에서 가장 흔한 4xx (523건)

**원본 의미**: 410 Gone 은 *resource 가 영구히 삭제* 됨. 단순 404 보다 명확 (서버가 이력 보유). dataset 의 410 spike 는 *대량 삭제 후 stale link 따라가는 client* 의미.

**해석 — 본 lecture 와의 매핑**

| 에러 처리 점검 학습 항목 | 본 record 에서의 증거 |
|------------------------|---------------------|
| **에러 응답 일관성** | 7 종 4xx/5xx 가 *동시에 발생* — 점검 시 *모든 응답이 동일 template 으로 정보 노출 안 하는지* 확인. 일부만 stack trace 노출 → *불일관 = 정보 누설* |
| **404 vs 410** | 404 (176) < 410 (523) — 일반적이지 않음. 본 dataset 는 *명시적 410* 사용. 점검 시 조직이 410 을 사용하는지 (→ 좋은 신호: ID enumeration 유리) 또는 일률 404 인지 |
| **413/431 의 의미** | 큰 payload·header 거부 — 점검 시 *client-side limit 정책* 점검 (DoS 방어) |
| **510 (699건) 의 비정상성** | 510 Not Extended 는 *드문* 코드. 본 dataset 의 699건 spike 는 *protocol negotiation 강제 시도* 의심 — 점검 시 endpoint 의 protocol fallback 정책 확인 |

**점검 액션**:
1. 점검 대상의 4xx/5xx 응답 *총 합계* 와 *분포 비율* 측정 → 본 dataset baseline (4xx 2,128건, 510 699건) 과 비교
2. 동일 endpoint 의 4xx 응답 *body 크기 분산* — 일부만 큰 body (stack trace) 면 *정보 노출* 항목으로 보고
3. 410 vs 404 사용 비율 → 조직의 *resource lifecycle 정책 명확성* 평가



---

## 부록: 학습 OSS 도구 매트릭스 (lab week11 — SSRF)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 식별 | curl PUT / **SSRFmap** / Burp Collaborator / **interactsh** |
| 2 포트 스캔 | curl 시간 차이 / SSRFmap portscan / wfuzz / Burp |
| 3 클라우드 메타 | AWS IMDS / SSRFmap aws / aws CLI / Pacu |
| 4 IP 변환 | 10진수 / 16진수 / IPv6 / 단축 |
| 5 URL parser | @ / # / Orange Tsai / **ssrf-king Burp** |
| 6 DNS rebinding | **rbndr.us** / Singularity of Origin / DNSChef |
| 7 gopher:// | **gopherus** / SSRFmap redis/fastcgi/mysql/smtp |
| 8 allowlist | ipaddress.is_private / ssrf-req-filter / iptables / IMDSv2 |
| 9 reporting | 8 페이로드 / DefectDojo / OWASP A10 / Capital One / sha256 |

(week07 의 종합 SSRF 매트릭스 참조. week11 은 압축된 핵심 표)
