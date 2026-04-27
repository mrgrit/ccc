# Week 03: 웹 애플리케이션 구조 이해

## 학습 목표
- HTTP 프로토콜의 요청/응답 구조를 이해한다
- HTTP 메서드, 상태 코드, 헤더의 의미를 파악한다
- HTTPS와 TLS 핸드셰이크의 기본 원리를 이해한다
- 쿠키, 세션, JWT 토큰의 차이와 동작 원리를 실습한다
- REST API 구조를 이해하고 직접 호출한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 실습 기지 (Bastion API :8003) |
| web | 10.20.30.80 | JuiceShop :3000, Apache :80 |
| siem | 10.20.30.100 | Wazuh Dashboard :443 (HTTPS 실습) |

Bastion API는 `http://10.20.30.200:8003`, ccc-api는 `http://localhost:9100`.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | HTTP 프로토콜·메서드·상태코드 (Part 1~3) | 강의 |
| 0:40-1:10 | 헤더·HTTPS (Part 4~5) | 강의+실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 쿠키·JWT (Part 6~7) | 실습 |
| 2:00-2:40 | REST API·JuiceShop 분석 (Part 8~9) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | Bastion 자연어 웹 분석 (Part 10) | 실습 |
| 3:30-3:40 | 정리 + 과제 안내 | 정리 |

---

# Part 1: HTTP 프로토콜 기초

HTTP(HyperText Transfer Protocol)는 웹 브라우저와 웹 서버가 통신하는 규약이다. 모든 웹 해킹의 기반이므로 반드시 이해해야 한다.

## 1.1 HTTP 요청(Request) 구조

브라우저가 서버에 보내는 메시지의 형태:

```
[메서드] [경로] HTTP/[버전]
[헤더1]: [값1]
[헤더2]: [값2]
(빈 줄)
[본문 - POST 등에서 사용]
```

**실제 예시:**
```
GET /api/Products HTTP/1.1
Host: 10.20.30.80:3000
User-Agent: curl/7.88.1
Accept: */*
```

## 1.2 HTTP 응답(Response) 구조

서버가 브라우저에 보내는 메시지:

```
HTTP/[버전] [상태코드] [상태메시지]
[헤더1]: [값1]
[헤더2]: [값2]
(빈 줄)
[본문 - HTML, JSON 등]
```

## 1.3 실습: HTTP 요청/응답 직접 관찰

**이것은 무엇인가?** `curl -v`는 HTTP 통신을 "verbose"하게 출력한다. 브라우저가 숨기는 요청/응답 원문을 눈으로 확인할 수 있는 가장 기본적인 도구다.

**왜 필요한가?** 웹 해킹의 본질은 HTTP 요청을 조작하는 것이다. 원문을 읽지 못하면 조작할 수도 없다.

```bash
curl -v http://10.20.30.80:3000/ 2>&1 | head -20
```

**명령 분해:**
- `-v`: verbose (요청·응답 헤더 전부 출력)
- `2>&1`: stderr를 stdout으로 병합 (verbose 출력이 stderr로 가기 때문)
- `| head -20`: 긴 출력을 앞부분 20줄만

**예상 출력:**
```
> GET / HTTP/1.1                      ← 요청: GET 메서드, / 경로
> Host: 10.20.30.80:3000              ← 요청: 대상 서버
> User-Agent: curl/7.81.0             ← 요청: 클라이언트 정보
> Accept: */*                         ← 요청: 모든 형식 수용
>
< HTTP/1.1 200 OK                     ← 응답: 성공
< Access-Control-Allow-Origin: *      ← 응답: CORS 완전 개방 ⚠️
< X-Content-Type-Options: nosniff     ← 응답: MIME 스니핑 방지
< X-Frame-Options: SAMEORIGIN         ← 응답: 클릭재킹 방지
< Feature-Policy: payment 'self'      ← 응답: 결제 기능 제한
< X-Recruiting: /#/jobs               ← 응답: JuiceShop 이스터에그
```

**결과 해석:**
- `>`는 **내가 보낸 것(요청)**, `<`는 **서버가 응답한 것**
- `Access-Control-Allow-Origin: *` → 모든 도메인이 이 API 호출 가능 (보안 이슈)
- `X-Recruiting: /#/jobs` → 불필요한 정보 노출. 공격자에게 앱의 경로 구조 힌트
- `X-Powered-By`가 없지만, 다른 응답에서 `Express`가 노출될 수 있음

---

# Part 2: HTTP 메서드

HTTP 메서드는 서버에게 "무엇을 하라"고 알려주는 동사(verb)다.

| 메서드 | 용도 | 예시 |
|--------|------|------|
| **GET** | 데이터 조회 | 웹 페이지 열기, API 데이터 가져오기 |
| **POST** | 데이터 생성 | 회원가입, 로그인, 글 작성 |
| **PUT** | 데이터 전체 수정 | 프로필 업데이트 |
| **PATCH** | 데이터 일부 수정 | 비밀번호만 변경 |
| **DELETE** | 데이터 삭제 | 계정 삭제 |
| **OPTIONS** | 허용 메서드 확인 | CORS 프리플라이트 |
| **HEAD** | 헤더만 조회 (본문 없음) | 파일 존재 여부 확인 |

## 2.1 실습: 메서드별 반응 비교

**이것은 무엇인가?** 동일한 URL에 메서드만 바꿔 요청하여, 서버가 어떤 메서드에 어떻게 반응하는지 관찰한다.

**왜 필요한가?** REST API는 메서드별로 권한이 다른 경우가 많다. GET은 누구나, POST/PUT/DELETE는 인증 필요. 공격자는 각 메서드의 반응을 보고 인증 우회·엔드포인트 추정의 단서를 얻는다.

```bash
# GET - 제품 목록 조회 (인증 불필요)
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -20

# HEAD - 본문 없이 헤더만 (빠른 존재 확인)
curl -sI http://10.20.30.80:3000/api/Products | head -5

# OPTIONS - 이 엔드포인트가 허용하는 메서드 확인
curl -s -X OPTIONS -v http://10.20.30.80:3000/api/Products 2>&1 | grep -i "access-control"
```

**예상 출력 (OPTIONS):**
```
< Access-Control-Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE
```

**결과 해석:** OPTIONS 응답에서 DELETE까지 허용되어 있음 → 실무에서는 필요한 메서드(GET, POST)만 허용하고 나머지는 차단해야 함.

## 2.2 메서드별 상태 코드 비교

```bash
for method in GET POST PUT DELETE OPTIONS HEAD; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://10.20.30.80:3000/api/Products/)
  echo "  $method → HTTP $code"
done
```

**예상 출력:**
```
  GET     → HTTP 200    ← 정상 조회
  POST    → HTTP 401    ← 인증 필요 (관리자만 제품 생성 가능)
  PUT     → HTTP 500    ← 서버 에러 (잘못된 요청 형식)
  DELETE  → HTTP 500    ← 서버 에러
  OPTIONS → HTTP 204    ← 메서드 목록만 반환 (No Content)
  HEAD    → HTTP 200    ← 헤더만 반환
```

**결과 해석:**
1. GET은 인증 없이 접근 가능 → 누구나 제품 목록 열람
2. POST 401 → 관리자 토큰 필요 → Week 04에서 SQLi로 탈취
3. PUT/DELETE가 500을 반환 → 서버가 입력 검증 없이 처리 시도하다 크래시 → **정보 유출 가능**

---

# Part 3: HTTP 상태 코드

| 범위 | 의미 | 대표 예시 |
|------|------|-----------|
| **1xx** | 정보 | 100 Continue |
| **2xx** | 성공 | 200 OK, 201 Created, 204 No Content |
| **3xx** | 리다이렉트 | 301 Moved Permanently, 302 Found |
| **4xx** | 클라이언트 오류 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| **5xx** | 서버 오류 | 500 Internal Server Error, 502 Bad Gateway |

## 3.1 실습: 의도적으로 각 상태 코드 유발

**이것은 무엇인가?** 상태 코드는 서버의 "표정"이다. 공격자는 상태 코드 변화로 공격 성공·실패를 판단한다. 200→500 변화는 "SQL 구문이 서버에 전달되어 오류가 났다"는 의미일 수 있다.

```bash
# 200 OK - 정상 응답
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/

# 404 Not Found - Apache에서 존재하지 않는 경로
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:80/nonexistent_page
# → 404 (Apache는 존재하지 않는 페이지에 404 반환)

# 참고: JuiceShop은 SPA라서 없는 경로에도 200 반환
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/nonexistent
# → 200 (SPA는 모든 경로를 프론트엔드에서 처리)

# 401 Unauthorized - 인증 필요한 API
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/api/Products/
# → 401

# 500 Internal Server Error - SQL 특수문자로 오류 유발
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"'","password":"x"}'
# → 500 (SQL 구문 오류)
```

**결과 해석:**
- 같은 웹 서버(`10.20.30.80`)인데 포트(:80 vs :3000)에 따라 404/200이 다르다 → **서버 종류(Apache vs SPA)를 상태코드로 판별 가능**
- 500 에러는 서버 내부 상태를 누출할 가능성이 있는 공격자 호재

---

# Part 4: HTTP 헤더

## 4.1 주요 요청 헤더

| 헤더 | 용도 | 보안 관련성 |
|------|------|-------------|
| `Host` | 대상 서버 지정 | 가상 호스트 구분 |
| `User-Agent` | 클라이언트 정보 | 브라우저 위장 가능 |
| `Cookie` | 세션 정보 전송 | 세션 하이재킹 대상 |
| `Authorization` | 인증 토큰 | Bearer JWT 등 |
| `Content-Type` | 본문 형식 | MIME 타입 조작 가능 |
| `Referer` | 이전 페이지 URL | 정보 유출 가능 |

## 4.2 주요 응답 헤더

| 헤더 | 용도 | 보안 설정 |
|------|------|-----------|
| `Server` | 서버 소프트웨어 | 버전 노출 위험 |
| `Set-Cookie` | 쿠키 설정 | HttpOnly, Secure 플래그 |
| `X-Powered-By` | 프레임워크 | 제거 권장 |
| `X-Frame-Options` | 클릭재킹 방지 | DENY 또는 SAMEORIGIN |
| `X-Content-Type-Options` | MIME 스니핑 방지 | nosniff |
| `Content-Security-Policy` | XSS 방지 | 스크립트 소스 제한 |
| `Strict-Transport-Security` | HTTPS 강제 | HSTS |

## 4.3 실습: 보안 헤더 점검

**이것은 무엇인가?** 웹 서버의 응답 헤더에는 "어떤 보안 설정이 되어 있는지"가 드러난다. 보안 헤더 누락 자체가 취약점이다.

**왜 필요한가?** OWASP Testing Guide의 OTG-CONFIG-006 "HTTP Security Headers"는 모든 웹 보안 감사의 기본 항목이다.

```bash
echo "=== JuiceShop 보안 헤더 체크 ==="
curl -sI http://10.20.30.80:3000/ | grep -iE "x-frame|x-content|x-powered|content-security|strict-transport|x-xss|access-control"
```

**예상 출력:**
```
Access-Control-Allow-Origin: *          ← ⚠️ CORS 완전 개방
X-Content-Type-Options: nosniff         ← ✓ MIME 스니핑 방지
X-Frame-Options: SAMEORIGIN             ← ✓ 클릭재킹 방지
```

**결과 해석 — 누락된 것에 주목:**
- `Content-Security-Policy` **없음** → XSS 공격 시 어떤 스크립트도 실행 가능
- `Strict-Transport-Security` **없음** → HTTP로 평문 쿠키 전송 가능

## 4.4 User-Agent 변경 (IDS 우회 전조)

```bash
# 일반 브라우저로 위장
curl -sI -H "User-Agent: Mozilla/5.0 Chrome/120.0.0.0" http://10.20.30.80:3000/ | head -3

# 공격 도구 지문 (sqlmap 등은 IPS가 자동 차단)
curl -sI -H "User-Agent: sqlmap/1.0" http://10.20.30.80:3000/ | head -3
```

**왜 필요한가?** 일부 WAF/IPS는 `User-Agent`에 "sqlmap", "nikto", "nmap" 같은 도구명이 포함되면 즉시 차단한다. Week 10(IPS 우회)에서 이 기법을 심화 학습한다.

---

# Part 5: HTTPS와 TLS

## 5.1 HTTP vs HTTPS

| 항목 | HTTP | HTTPS |
|------|------|-------|
| 포트 | 80 | 443 |
| 암호화 | 없음 (평문) | TLS로 암호화 |
| 도청 가능 | 가능 | 불가능 |
| URL 시작 | http:// | https:// |

## 5.2 TLS 핸드셰이크 (간소화)

HTTPS 연결이 시작될 때 클라이언트와 서버가 암호화 방법을 협상하는 과정이다:

```
1. 클라이언트 → 서버: "안녕, 나는 이런 암호화를 지원해" (ClientHello)
2. 서버 → 클라이언트: "이 방법으로 하자, 내 인증서야" (ServerHello + Certificate)
3. 클라이언트: 인증서 검증 후, 비밀 키 교환
4. 양쪽: 공유된 키로 암호화 통신 시작
```

## 5.3 실습: TLS 인증서 확인

우리 인프라에서 HTTPS를 사용하는 서비스는 **Wazuh Dashboard** (siem:443)이다.

**이것은 무엇인가?** `openssl s_client`는 TLS 연결의 로우레벨 도구. 서버가 제시하는 인증서를 직접 관찰할 수 있다.

```bash
# Wazuh Dashboard 인증서 subject와 유효기간
echo | openssl s_client -connect 10.20.30.100:443 2>/dev/null \
  | openssl x509 -noout -subject -dates -issuer
```

**명령 분해:**
- `echo |`: stdin을 비워 `s_client`가 즉시 종료되게 함 (수동 입력 필요 없음)
- `-connect IP:PORT`: TLS 연결 대상
- `2>/dev/null`: 경고 메시지 숨김
- `| openssl x509 -noout ...`: 파이프로 넘어온 인증서에서 필드 추출

**예상 출력:**
```
subject=C = US, L = California, O = Wazuh, OU = Wazuh, CN = wazuh-dashboard
notBefore=Mar 24 05:23:34 2026 GMT
notAfter=Mar 21 05:23:34 2036 GMT
issuer=C = US, L = California, O = Wazuh, OU = Wazuh, CN = wazuh-root-ca
```

**결과 해석:**
- `subject CN = wazuh-dashboard`: 인증서가 가리키는 서비스 이름 (실제 FQDN 대신)
- `issuer CN = wazuh-root-ca`: **자체 서명** (subject와 issuer가 Wazuh 조직) → 브라우저가 "안전하지 않음" 경고
- 유효기간 10년: 자체서명의 흔한 설정. 공개 인증기관(Let's Encrypt)은 90일

**curl로 동일 확인:**
```bash
curl -vk https://10.20.30.100:443/ 2>&1 | grep -A3 "Server certificate"
```

- `-k`: 인증서 검증 무시 (실습 환경에서만 사용, 실무에선 위험)

---

# Part 6: 쿠키(Cookie)와 세션(Session)

## 6.1 쿠키란?

쿠키는 서버가 브라우저에 저장하는 작은 데이터 조각이다. 브라우저는 같은 서버에 요청할 때마다 쿠키를 자동으로 함께 보낸다.

**쿠키 동작 흐름:**
```
1. 브라우저 → 서버: 로그인 요청 (ID/PW)
2. 서버 → 브라우저: "로그인 성공! 이 쿠키를 저장해" (Set-Cookie 헤더)
3. 브라우저 → 서버: 이후 모든 요청에 쿠키 자동 첨부
```

## 6.2 쿠키 속성

| 속성 | 의미 | 보안 영향 |
|------|------|-----------|
| `HttpOnly` | JavaScript에서 접근 불가 | XSS로 쿠키 탈취 방지 |
| `Secure` | HTTPS에서만 전송 | 네트워크 도청 방지 |
| `SameSite` | 동일 사이트에서만 전송 | CSRF 공격 방지 |
| `Path` | 특정 경로에서만 전송 | 범위 제한 |
| `Expires/Max-Age` | 만료 시간 | 세션 수명 관리 |

## 6.3 JuiceShop의 인증 방식 관찰

**이것은 무엇인가?** 인증이 쿠키 기반인지, 토큰 기반인지 확인한다. 공격 표면이 달라진다.

```bash
curl -v -c /tmp/cookies.txt -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}' 2>&1 | grep -iE "set-cookie|token|authentication"
```

**명령 분해:**
- `-c /tmp/cookies.txt`: 수신한 쿠키를 Netscape 형식으로 저장
- 응답 본문과 헤더에서 `token`, `authentication`, `set-cookie` 키워드 grep

**결과 해석 (실제 관찰):**
- JuiceShop은 `Set-Cookie` 헤더를 **쓰지 않고** JSON 응답 본문에 JWT 토큰을 담아 반환
- 이는 SPA(Single Page Application)의 일반적 패턴
- 클라이언트가 토큰을 localStorage에 저장하고, 이후 요청에 `Authorization: Bearer <token>` 헤더로 실어 보냄

**차이점 — 쿠키 vs 토큰:**

| 항목 | 쿠키 세션 | JWT 토큰 |
|------|-----------|----------|
| 서버 상태 | 서버에 세션 저장 필요 | 서버 stateless |
| 전송 방식 | 브라우저 자동 첨부 | 명시적 헤더 첨부 |
| CSRF 위험 | 있음 (자동 첨부) | 낮음 (직접 첨부) |
| XSS 탈취 | HttpOnly로 방어 가능 | localStorage는 XSS로 탈취 가능 |
| 만료 취소 | 서버가 세션 삭제 | 토큰 자체는 만료까지 유효 |

---

# Part 7: JWT (JSON Web Token)

## 7.1 JWT란?

JWT는 JSON 형식의 자가 포함형(self-contained) 인증 토큰이다. 서버가 세션을 저장하지 않고, 토큰 자체에 사용자 정보가 들어있다.

## 7.2 JWT 구조

JWT는 점(`.`)으로 구분된 3개 부분이다:

```
[헤더].[페이로드].[서명]
eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhZG1pbkBqdWljZS1zaC5vcCJ9.xxxxx
```

각 부분은 **Base64URL**로 인코딩되어 있다. **암호화가 아니다** — 누구나 디코딩하여 읽을 수 있다.

**헤더 (Header):**
```json
{
  "alg": "RS256",   // 서명 알고리즘
  "typ": "JWT"      // 토큰 타입
}
```

**페이로드 (Payload):**
```json
{
  "sub": "1",                          // 사용자 ID
  "email": "admin@juice-sh.op",       // 이메일
  "role": "admin",                     // 역할
  "iat": 1711526400,                   // 발급 시간
  "exp": 1711612800                    // 만료 시간
}
```

**서명 (Signature):** 헤더+페이로드에 대한 암호 서명. 위·변조 방지만 담당.

## 7.3 JWT 디코딩 실습

**이것은 무엇인가?** JuiceShop의 JWT를 직접 디코딩하여 어떤 정보가 담겼는지 확인한다.

**왜 중요한가?** 많은 개발자가 JWT를 "암호화된 토큰"으로 오해하여 **패스워드 해시, 개인정보**를 넣는다. 실제로는 Base64일 뿐, 누구나 읽을 수 있다.

```bash
# Step 1: 계정 생성 (이미 있으면 실패 — 다른 이메일 사용)
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}' \
  | python3 -m json.tool | head -10

# Step 2: 로그인하여 JWT 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "JWT (처음 50자): ${TOKEN:0:50}..."

# Step 3: 페이로드 디코딩 (Base64URL)
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
p = sys.stdin.read().strip()
p += '=' * (4 - len(p) % 4)  # Base64 패딩 보정
d = json.loads(base64.urlsafe_b64decode(p))
print(json.dumps(d, indent=2, ensure_ascii=False))
"
```

**명령 분해:**
- `cut -d. -f2`: JWT를 `.`로 나눠 두 번째 조각(페이로드)만 추출
- `base64.urlsafe_b64decode`: URL-safe Base64 디코드 (`+` 대신 `-`, `/` 대신 `_`)
- `p += '=' * (4 - len(p) % 4)`: Base64는 4의 배수 길이 필요 → 부족한 만큼 `=` 추가

**실제 출력 예시:**
```json
{
  "status": "success",
  "data": {
    "id": 24,
    "username": "",
    "email": "student@test.com",
    "password": "c4fcbdb8c2d1d663181e4dcdccef5f65",
    "role": "customer",
    "deluxeToken": "",
    "lastLoginIp": "0.0.0.0",
    "isActive": true
  }
}
```

**결과 해석 — CRITICAL 발견:**
- `password` 필드에 **MD5 해시값**이 그대로 포함되어 있다
- JWT는 누구나 디코딩 가능 → **패스워드 해시 노출**
- MD5는 레인보우 테이블로 쉽게 역산 가능
- 공격자가 다른 사용자의 JWT를 탈취하면(Week 05 XSS), 해시까지 획득하여 오프라인 크래킹 가능
- 이것은 JuiceShop의 **의도적 취약점** — OWASP A02 (Cryptographic Failures) 예시

**교훈:** JWT에는 최소한의 정보만 넣어야 한다 — user_id, role, 만료시간 등.

## 7.4 JWT로 인증된 API 호출

**이것은 무엇인가?** JWT는 "입장권". 이 토큰을 Authorization 헤더에 실어 보내면 서버가 "이 사용자"로 인식한다.

```bash
# JWT 토큰으로 API 호출
curl -s http://10.20.30.80:3000/api/Feedbacks \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"data\",[]))}개 피드백 수신')"

# 인증 없이 같은 API 호출
NO_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:3000/api/Feedbacks)
echo "인증 없이: HTTP $NO_AUTH_CODE"
```

**결과 해석:** JuiceShop의 Feedbacks API는 인증 없이도 200을 반환한다 — 실제 서비스였다면 **접근제어 취약점**. Week 06에서 BOLA/IDOR로 이어진다.

---

# Part 8: REST API 구조

## 8.1 REST란?

REST(Representational State Transfer)는 웹 API 설계 규칙이다. **URL로 자원(Resource)을 표현**하고, **HTTP 메서드로 행위(Action)를 표현**한다.

| 행위 | HTTP 메서드 | URL 예시 | 설명 |
|------|-------------|----------|------|
| 조회 | GET | /api/Products | 전체 목록 |
| 조회 | GET | /api/Products/1 | 특정 항목 |
| 생성 | POST | /api/Products | 새 항목 생성 |
| 수정 | PUT | /api/Products/1 | 항목 전체 수정 |
| 삭제 | DELETE | /api/Products/1 | 항목 삭제 |

## 8.2 JuiceShop REST API 탐색

**이것은 무엇인가?** 모의해킹의 "API 엔드포인트 열거" 단계. 어떤 API가 있고, 어떤 데이터를 반환하고, 어떤 인증이 필요한지 파악한다.

```bash
# 제품 전체 목록 (인증 불필요)
curl -s http://10.20.30.80:3000/api/Products | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'상품 수: {len(d.get(\"data\",[]))}')
for p in d['data'][:3]:
    print(f'  [{p[\"id\"]}] {p[\"name\"]} - \${p[\"price\"]}')
"

# 특정 제품 조회
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -m json.tool | head -15

# 검색 기능
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -m json.tool | head -20
```

**예상 출력 (Products):**
```
상품 수: 36
  [1] Apple Juice (1000ml) - $1.99
  [2] Orange Juice (1000ml) - $2.99
  [3] Eggfruit Juice (500ml) - $8.99
```

**결과 해석:** 36개 상품 전체가 인증 없이 노출. `rest/products/search?q=apple`도 누구나 접근 가능. 이 search 엔드포인트는 Week 04에서 SQLi 실습 대상이다.

## 8.3 API 응답 구조의 일관성

JuiceShop API의 일관된 응답 패턴:

```json
{
    "status": "success",
    "data": [ ... ]    // 또는 단일 객체 { ... }
}
```

에러 시:
```json
{
    "error": {
        "message": "...",
        "name": "..."
    }
}
```

**왜 일관성이 중요한가?** 일관된 응답 구조는 자동화된 공격/방어 도구가 에러·성공을 판별하기 쉽게 한다. 공격자도 스크립트를 짤 때 유리하다.

---

# Part 9: 종합 분석 — JuiceShop API 열거

## 9.1 JavaScript 소스에서 엔드포인트 추출

**이것은 무엇인가?** SPA는 프론트엔드 JavaScript 번들에 모든 API URL이 하드코딩되어 있다. JS 파일만 받아서 `/api/*`, `/rest/*` 패턴을 grep하면 전체 API 목록을 뽑을 수 있다.

**왜 중요한가?** 공격자는 이 목록 하나만으로 공격 표면을 완전 파악한다.

```bash
curl -s http://10.20.30.80:3000/main.js | grep -oE '/api/[A-Za-z]+' | sort -u
```

**예상 출력 (14개 엔드포인트):**
```
/api/Addresss
/api/BasketItems
/api/Cards
/api/Challenges
/api/Complaints
/api/Deliverys
/api/Feedbacks
/api/Hints
/api/Products
/api/Quantitys
/api/Recycles
/api/SecurityAnswers
/api/SecurityQuestions
/api/Users
```

```bash
# /rest/ 경로도 추출
curl -s http://10.20.30.80:3000/main.js | grep -oE '/rest/[A-Za-z/]+' | sort -u | head -15
```

**결과 해석:** 14 + N개 엔드포인트 확보. 각각에 GET/POST/PUT/DELETE를 시도하고 상태 코드를 관찰하면 **어떤 API가 인증 필요인지** 지도 작성 가능.

## 9.2 API 인증 매트릭스 작성

```bash
echo "=== API 인증 매트릭스 ==="
for endpoint in Products Users Feedbacks SecurityQuestions Challenges; do
  no_auth=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/api/$endpoint")
  with_auth=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://10.20.30.80:3000/api/$endpoint")
  echo "  /api/$endpoint — 무인증: $no_auth, customer인증: $with_auth"
done
```

**결과 해석 (모의해킹 보고서 예시):**
```
  /api/Products          — 무인증: 200, 인증: 200       ← 누구나 조회
  /api/Users             — 무인증: 401, 인증: 200       ← customer도 Users 조회 가능 (IDOR 가능성)
  /api/Feedbacks         — 무인증: 200, 인증: 200       ← 누구나 피드백 조회
  /api/SecurityQuestions — 무인증: 200, 인증: 200       ← 공개 목록
  /api/Challenges        — 무인증: 200, 인증: 200       ← JuiceShop 특수 API
```

- `/api/Users`가 customer 토큰으로도 조회 가능 → 실무라면 **HIGH 위험**. Week 06 BOLA 실습.

---

# Part 10: Bastion 자연어 웹 분석

## 10.1 왜 Bastion를 쓰는가

위 실습에서 수행한 작업(헤더 수집, API 열거, JWT 디코딩, 인증 매트릭스)은 매번 타이핑하기 번거롭다. Bastion에게 자연어로 한 번 지시하면 전체를 실행하고 자연어로 요약해준다.

## 10.2 /ask — 자연어 지시

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "http://10.20.30.80:3000 JuiceShop의 응답 헤더를 수집해서 보안 헤더(X-Frame-Options, CSP, HSTS, X-Content-Type-Options) 설정 여부를 표로 정리하고, 누락된 헤더에 대한 위험 분석을 해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답 (자연어):**
```
JuiceShop 보안 헤더 점검 결과:

| 헤더 | 설정 | 상태 |
|------|------|------|
| X-Frame-Options | SAMEORIGIN | ✓ |
| X-Content-Type-Options | nosniff | ✓ |
| Content-Security-Policy | (없음) | ✗ |
| Strict-Transport-Security | (없음) | ✗ |
| Access-Control-Allow-Origin | * | ⚠️ |

위험 분석:
- CSP 부재로 XSS 공격 시 임의 스크립트 실행 가능 (위험: HIGH)
- HSTS 부재로 HTTP→HTTPS 강제 불가, 쿠키 평문 노출 위험 (위험: MEDIUM)
- CORS 완전 개방(*)으로 다른 도메인에서 API 호출 허용 (위험: HIGH)
```

## 10.3 /ask — API 열거 자동화

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop의 main.js에서 /api/*와 /rest/* 패턴으로 API 엔드포인트를 추출하고, 각 엔드포인트에 무인증 GET 요청을 보내 상태 코드를 수집해서 표로 정리해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

## 10.4 Evidence 확인

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=10" | python3 -c "
import sys, json
for e in json.load(sys.stdin):
    msg = e.get('user_message','')[:70]
    skill = e.get('skill','?')
    ok = '✓' if e.get('success') else '✗'
    print(f'  {ok} [{skill:15s}] {msg}')
"
```

위의 자연어 지시 두 건이 evidence에 기록되어 있음을 확인한다. 이것이 바로 **Bastion의 가치** — 반복 작업의 자동화와 증적의 영속화.

---

## 과제 (다음 주까지)

### 과제 1: JuiceShop 종합 HTTP 분석 보고서 (60점)

1. **계정 생성·로그인·JWT 획득** (10점)
   - 본인 이메일로 계정 생성
   - 로그인하여 JWT 토큰 획득
   - 토큰의 3개 부분(header/payload/signature) 각각 디코딩

2. **JWT 페이로드 분석** (15점)
   - 포함된 필드 모두 나열
   - 보안 이슈 식별 (예: 패스워드 해시 노출)
   - 개선 방안 제안

3. **API 엔드포인트 열거** (15점)
   - main.js에서 /api/*, /rest/* 추출
   - 최소 10개 엔드포인트 목록화
   - 각 엔드포인트에 무인증 GET 요청 → 상태 코드 기록

4. **보안 헤더 점검** (10점)
   - `curl -I`로 JuiceShop(:3000)과 Apache(:80) 응답 헤더 비교
   - OWASP 권장 헤더 누락분 식별

5. **TLS 인증서 분석** (10점)
   - `openssl s_client`로 Wazuh(10.20.30.100:443) 인증서 분석
   - Subject, Issuer, 유효기간, 자체서명 여부 보고

### 과제 2: Bastion 자연어 분석 (40점)

**각 10점:**
1. Bastion `/ask`로 "JuiceShop 보안 헤더 점검 + 위험 분석" 결과 제출
2. Bastion `/ask`로 "JuiceShop API 14개 엔드포인트 무인증 매트릭스" 결과 제출
3. Bastion `/ask`로 "내가 획득한 JWT 토큰 `<TOKEN>` 을 디코드해서 취약점 분석해줘" 결과 제출
4. `/evidence`에 위 3건이 기록되어 있음을 캡처

---

## 다음 주 예고

**Week 04: SQL Injection**
- SQL 문법 복습 (SELECT, WHERE, UNION, 주석)
- JuiceShop 로그인 폼 SQLi (OWASP A03)
- 관리자 권한 우회 (`' OR 1=1--`)
- UNION 기반 데이터 추출
- sqlmap 자동화 도구 사용

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **HTTP** | HyperText Transfer Protocol | 웹 통신 규약 (:80) | 우편 시스템 |
| **HTTPS** | HTTP Secure | TLS로 암호화된 HTTP (:443) | 등기 봉투 우편 |
| **TLS** | Transport Layer Security | 전송 계층 암호화 프로토콜 | 봉투 봉인 |
| **SPA** | Single Page Application | 한 페이지에서 JS로 내용 교체하는 웹 앱 | 극장 (무대는 하나, 장면만 바뀜) |
| **JWT** | JSON Web Token | JSON 기반 자가포함 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리를 텍스트로 변환 | 포장지 (누구나 풀 수 있음) |
| **Base64URL** | Base64URL | URL에 안전한 Base64 변형 (`+`→`-`, `/`→`_`) | URL용 포장지 |
| **REST** | Representational State Transfer | URL+HTTP 메서드로 자원 조작하는 API 스타일 | 도서관 대출 시스템 |
| **엔드포인트** | Endpoint | 특정 기능을 제공하는 URL | 특정 창구 번호 |
| **Bearer Token** | Bearer Token | Authorization 헤더에 실어 보내는 토큰 | "이 표 보여주면 들여보내줌" |
| **CSP** | Content-Security-Policy | 허용 스크립트 소스 제한 (XSS 방어) | 출입 허가 화이트리스트 |
| **HSTS** | Strict-Transport-Security | HTTPS 강제 지시 헤더 | "여기는 HTTPS만" 표지판 |
| **자체서명** | Self-signed | 공개 CA가 아닌 스스로 서명한 인증서 | 자작 인감 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 실제로 사용한 도구와 솔루션의 요점.

### curl

> **역할:** HTTP 요청·응답 분석의 기본 도구
> **실행 위치:** manager 또는 학생 PC

**이번 주 사용 옵션**

| 옵션 | 의미 | 이번 주 사용 예 |
|------|------|-----------------|
| `-v` | verbose (요청/응답 헤더 출력) | HTTP 원문 관찰 |
| `-s` | silent (진행률 숨김) | 스크립트에서 |
| `-I` | HEAD 요청 (헤더만) | 보안 헤더 점검 |
| `-X METHOD` | 메서드 지정 | OPTIONS/DELETE 등 |
| `-H 'K: V'` | 커스텀 헤더 | Authorization, Content-Type |
| `-d '본문'` | 요청 본문 | POST JSON |
| `-c 파일` | 응답 쿠키 저장 | 세션 관찰 |
| `-o /dev/null -w '%{http_code}'` | 상태 코드만 | 자동화 |
| `-k` | 인증서 검증 무시 | 자체서명 HTTPS (실습만) |

### openssl s_client

> **역할:** TLS 연결 로우레벨 진단
> **이번 주 사용:** Wazuh Dashboard(10.20.30.100:443) 자체서명 인증서 분석

| 옵션 | 의미 |
|------|------|
| `-connect HOST:PORT` | TLS 연결 대상 |
| `-showcerts` | 인증서 체인 전체 |
| `echo \| ...` | stdin 비워 즉시 종료 |
| `\| openssl x509 -noout -subject -dates -issuer` | 주요 필드만 추출 |

### JuiceShop 인증 구조

> **실제 사용한 엔드포인트만 정리.** (Week 04~06에서 추가 엔드포인트 사용 예정)

| 엔드포인트 | 메서드 | 인증 | 용도 |
|-----------|--------|------|------|
| `/api/Users/` | POST | 불필요 | 계정 생성 |
| `/rest/user/login` | POST | 불필요 | 로그인, JWT 발급 |
| `/api/Products` | GET | 불필요 | 제품 조회 |
| `/api/Products/1` | GET | 불필요 | 특정 제품 |
| `/api/Users/` | GET | Bearer | 사용자 목록 |
| `/api/Feedbacks` | GET | 불필요 | 피드백 조회 |
| `/api/Challenges` | GET | 불필요 | JuiceShop 챌린지 |
| `/rest/products/search?q=` | GET | 불필요 | 제품 검색 |
| `/main.js` | GET | 불필요 | 프론트엔드 번들 (엔드포인트 추출 대상) |
| `/rest/admin/application-configuration` | GET | 불필요 | 애플리케이션 설정 (보안 이슈) |

### Bastion API (:8003) — 이번 주 사용 엔드포인트

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 질문 → 자동 실행 → 자연어 요약 응답 |
| GET | `/evidence?limit=N` | 최근 N건 작업 기록 조회 |

> `/chat`, `/skills`, `/playbooks`, `/assets`, `/onboard`는 이번 주 사용하지 않음.

---

<!--
사례 폐기 (2026-04-27 수기 검토): w03 웹 애플리케이션 구조 이해 — 인프라·
프레임워크 학습 주차. T1041 generic Exfil tag 매핑 X. 폐기.
-->


