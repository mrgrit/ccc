# Week 03: 웹 애플리케이션 구조 이해

## 학습 목표
- HTTP 프로토콜의 요청/응답 구조를 이해한다
- HTTP 메서드, 상태 코드, 헤더의 의미를 파악한다
- HTTPS와 TLS 핸드셰이크의 기본 원리를 이해한다
- 쿠키, 세션, JWT 토큰의 차이와 동작 원리를 실습한다
- REST API 구조를 이해하고 직접 호출한다


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
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000, Apache:80 |

---

## 1. HTTP 프로토콜 기초

HTTP(HyperText Transfer Protocol)는 웹 브라우저와 웹 서버가 통신하는 규약이다. 모든 웹 해킹의 기반이므로 반드시 이해해야 한다.

### 1.1 HTTP 요청(Request) 구조

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

### 1.2 HTTP 응답(Response) 구조

서버가 브라우저에 보내는 메시지:

```
HTTP/[버전] [상태코드] [상태메시지]
[헤더1]: [값1]
[헤더2]: [값2]
(빈 줄)
[본문 - HTML, JSON 등]
```

### 1.3 실습: HTTP 요청/응답 직접 관찰

> **이 실습을 왜 하는가?**
> 웹 해킹의 본질은 HTTP 통신을 조작하는 것이다. 브라우저는 HTTP를 시각적으로 숨기지만,
> 보안 전문가는 요청/응답의 원문(raw)을 읽을 수 있어야 한다.
> `curl -v`는 HTTP 통신의 전 과정을 투명하게 보여주는 가장 기본적인 도구이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 서버가 어떤 소프트웨어/프레임워크를 사용하는지 (Server, X-Powered-By 헤더)
> - 어떤 보안 헤더가 설정되어 있는지 (X-Frame-Options, CSP 등)
> - 응답 데이터의 형식과 크기
>
> **실무 활용:** 모의해킹 보고서에서 "서버 핑거프린팅" 섹션에 이 분석 결과를 기재한다.

> **실습 목적**: HTTP 요청/응답 헤더를 분석하여 웹 서버의 기술 스택과 보안 설정을 파악한다
>
> **배우는 것**: curl을 사용한 HTTP 헤더 분석으로 서버 소프트웨어, 프레임워크, 보안 헤더 설정 여부를 확인하는 방법을 배운다
>
> **결과 해석**: Server, X-Powered-By 헤더에서 기술 스택을 확인하고, CSP/X-Frame-Options 부재 시 보안 미흡으로 판단한다
>
> **실전 활용**: 모의해킹 보고서의 '서버 핑거프린팅' 섹션에서 이 분석 결과를 증적으로 활용한다

```bash
# -v 옵션으로 요청과 응답 헤더를 모두 볼 수 있다
curl -v http://10.20.30.80:3000/ 2>&1 | head -20
```

**실행 결과 (검증 완료):**
```
> GET / HTTP/1.1                      ← 요청: GET 메서드, / 경로
> Host: 10.20.30.80:3000              ← 요청: 대상 서버
> User-Agent: curl/7.81.0             ← 요청: 클라이언트 정보
> Accept: */*                         ← 요청: 모든 형식 수용
>
< HTTP/1.1 200 OK                     ← 응답: 성공
< Access-Control-Allow-Origin: *      ← 응답: CORS 완전 개방 ⚠️
< X-Content-Type-Options: nosniff     ← 응답: MIME 스니핑 방지 ✓
< X-Frame-Options: SAMEORIGIN         ← 응답: 클릭재킹 방지 ✓
< Feature-Policy: payment 'self'      ← 응답: 결제 기능 제한
< X-Recruiting: /#/jobs               ← 응답: JuiceShop 이스터에그
```

> **읽는 방법:** `>`는 **내가 보낸 것(요청)**, `<`는 **서버가 보낸 것(응답)**이다.
>
> **보안 분석 포인트:**
> - `Access-Control-Allow-Origin: *` → 모든 도메인에서 이 API를 호출할 수 있다. 실무에서는 특정 도메인만 허용해야 한다.
> - `X-Recruiting: /#/jobs` → 불필요한 정보 노출. 공격자에게 앱의 경로 구조를 알려준다.
> - `X-Powered-By` 헤더가 없지만, 다른 응답에서는 `Express`가 노출될 수 있다.
>
> **주의:** `curl -v`의 출력은 stderr(2)로 나오므로, `2>&1`로 리다이렉트해야 `head`로 자를 수 있다.

---

## 2. HTTP 메서드

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

### 실습: 다양한 HTTP 메서드 실험

> **이 실습을 왜 하는가?**
> 웹 애플리케이션은 HTTP 메서드에 따라 다르게 동작한다. 공격자는 GET 대신 PUT/DELETE를
> 보내거나, OPTIONS로 허용된 메서드를 확인하여 공격 가능성을 탐색한다.
> 각 메서드가 어떤 응답을 반환하는지 직접 확인하면 API의 동작 원리를 이해할 수 있다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 어떤 API 엔드포인트가 존재하는지 (200 vs 404)
> - 어떤 메서드가 인증 없이 접근 가능한지 (200 vs 401)
> - CORS 설정이 어떻게 되어 있는지 (Access-Control-Allow-Methods)
>
> **실무 시나리오:** 모의해킹에서 "API 엔드포인트 열거" 단계에 해당한다.
> REST API는 URL 구조가 예측 가능하므로, /api/Users, /api/Products 등을
> 순서대로 호출하여 존재하는 엔드포인트를 찾는다.

```bash
# GET - 제품 목록 조회 (인증 불필요)
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -20

# HEAD - 본문 없이 헤더만 확인 (빠른 존재 여부 확인)
curl -sI http://10.20.30.80:3000/api/Products | head -5

# OPTIONS - 이 엔드포인트에서 허용되는 메서드 확인
curl -s -X OPTIONS -v http://10.20.30.80:3000/api/Products 2>&1 | grep -i "access-control"
```

**검증 완료 결과:**
```
# GET → 36개 상품 데이터 반환 (인증 없이 접근 가능)
# HEAD → 200 OK (본문 없이 헤더만)
# OPTIONS → Access-Control-Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE
#           → 모든 메서드가 허용됨! (보안 이슈: 최소한만 허용해야 함)
```

> **보안 분석:** OPTIONS 응답에서 DELETE까지 허용되어 있다. 실무에서는 필요한 메서드(GET, POST)만 허용하고 나머지는 차단해야 한다.

```bash
# POST - 사용자 등록 (JSON 본문 전송)
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","passwordRepeat":"test1234","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}' \
  | python3 -m json.tool
```

> **주의:** 이 명령은 JuiceShop에 실제로 계정을 생성한다. 같은 이메일로 두 번 실행하면 "이미 존재" 에러가 발생한다. 다른 이메일을 사용하거나 JuiceShop을 재시작하면 초기화된다.

```bash
# 각 메서드별 상태코드 확인 (한눈에 비교)
for method in GET POST PUT DELETE OPTIONS HEAD; do     # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://10.20.30.80:3000/api/Products/ 2>/dev/null)
  echo "  $method → HTTP $code"
done
```

**검증 완료 결과:**
```
  GET     → HTTP 200    ← 정상 조회
  POST    → HTTP 401    ← 인증 필요 (관리자만 제품 생성 가능)
  PUT     → HTTP 500    ← 서버 에러 (잘못된 요청 형식)
  DELETE  → HTTP 500    ← 서버 에러
  OPTIONS → HTTP 204    ← 메서드 목록만 반환 (No Content)
  HEAD    → HTTP 200    ← 헤더만 반환
```

> **이 결과에서 알 수 있는 것:**
> 1. GET은 인증 없이 접근 가능 → 누구나 제품 목록을 볼 수 있다
> 2. POST는 401(인증 필요) → 제품 생성은 관리자 토큰이 필요하다
> 3. PUT/DELETE는 500 → 서버가 에러 메시지를 반환 (정보 유출 가능)
> 4. Week 04에서 SQLi로 관리자 토큰을 획득하면 이 API들을 사용할 수 있다

---

## 3. HTTP 상태 코드

서버가 요청 처리 결과를 숫자로 알려준다.

| 범위 | 의미 | 예시 |
|------|------|------|
| **1xx** | 정보 | 100 Continue |
| **2xx** | 성공 | 200 OK, 201 Created |
| **3xx** | 리다이렉트 | 301 Moved Permanently, 302 Found |
| **4xx** | 클라이언트 오류 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| **5xx** | 서버 오류 | 500 Internal Server Error |

### 실습: 다양한 상태 코드 직접 만들기

> **이 실습을 왜 하는가?**
> 상태 코드는 서버의 "표정"이다. 200(웃음), 401(문 앞에서 막힘), 404(길을 잃음), 500(서버가 넘어짐).
> 공격자는 상태 코드의 변화를 관찰하여 공격의 성공/실패를 판단한다.
> 예: SQLi 시도 시 200→500으로 바뀌면 SQL 구문이 서버에 전달되었다는 증거이다.
>
> **실무 활용:** 자동화 점검 도구(Burp Suite, ZAP)는 응답 코드를 기준으로 취약점을 분류한다.
> 500 에러가 반환되면 "서버 에러 유발 가능" → 입력값 검증 부재의 증거로 보고서에 기재한다.

```bash
# 200 OK - 정상 응답
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/

# 404 Not Found - Apache에서 존재하지 않는 경로
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:80/nonexistent_page
# → 404 (Apache는 전통적 웹서버라 없는 페이지에 404를 반환)

# 참고: JuiceShop은 SPA(Single Page Application)라서 없는 경로에도 200을 반환한다
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/nonexistent
# → 200 (SPA는 모든 경로를 프론트엔드에서 처리하므로 항상 200)

# 401 Unauthorized - 인증 필요한 API (admin 전용)
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/api/Products/
# → 401 (POST로 제품 생성 시 인증 필요)

# 500 Internal Server Error - SQLi로 서버 오류 유발
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"'","password":"x"}'
# → 500 (SQL 구문 오류 발생)
```

> **보안 관점**: 에러 메시지에 내부 정보(스택 트레이스, DB 쿼리 등)가 포함되면 공격자에게 힌트를 준다.

---

## 4. HTTP 헤더 상세 분석

### 4.1 주요 요청 헤더

| 헤더 | 용도 | 보안 관련성 |
|------|------|-------------|
| `Host` | 대상 서버 지정 | 가상 호스트 구분 |
| `User-Agent` | 클라이언트 정보 | 브라우저 위장 가능 |
| `Cookie` | 세션 정보 전송 | 세션 하이재킹 대상 |
| `Authorization` | 인증 토큰 | Bearer JWT 등 |
| `Content-Type` | 본문 형식 | MIME 타입 조작 가능 |
| `Referer` | 이전 페이지 URL | 정보 유출 가능 |

### 4.2 주요 응답 헤더

| 헤더 | 용도 | 보안 설정 |
|------|------|-----------|
| `Server` | 서버 소프트웨어 | 버전 노출 위험 |
| `Set-Cookie` | 쿠키 설정 | HttpOnly, Secure 플래그 |
| `X-Powered-By` | 프레임워크 | 제거 권장 |
| `X-Frame-Options` | 클릭재킹 방지 | DENY 또는 SAMEORIGIN |
| `X-Content-Type-Options` | MIME 스니핑 방지 | nosniff |
| `Content-Security-Policy` | XSS 방지 | 스크립트 소스 제한 |

### 실습: 보안 헤더 분석

> **이 실습을 왜 하는가?**
> 응답 헤더는 서버의 보안 설정을 외부에서 확인할 수 있는 유일한 창구이다.
> 모의해킹 보고서에서 "보안 헤더 점검" 항목은 거의 반드시 포함된다.
> 누락된 보안 헤더 하나가 XSS, 클릭재킹 등의 공격을 가능하게 할 수 있다.
>
> **실무 시나리오:** 고객사 웹사이트의 보안 헤더를 점검하여 "X-Frame-Options 미설정으로
> 클릭재킹 공격에 취약함" 같은 발견사항을 보고서에 기재한다.
> OWASP Testing Guide의 "OTG-CONFIG-006: HTTP Security Headers" 항목에 해당한다.

```bash
# JuiceShop 보안 헤더 점검 (검증 완료)
echo "=== 보안 헤더 체크 ==="
curl -sI http://10.20.30.80:3000/ | grep -iE "x-frame|x-content|x-powered|content-security|strict-transport|x-xss|access-control"
```

**검증 완료 결과:**
```
Access-Control-Allow-Origin: *          ← ⚠️ CORS 완전 개방 (위험)
X-Content-Type-Options: nosniff         ← ✓ MIME 스니핑 방지
X-Frame-Options: SAMEORIGIN             ← ✓ 클릭재킹 방지
```

> **분석:** Content-Security-Policy(CSP)와 Strict-Transport-Security(HSTS)가 **없다**.
> CSP가 없으면 XSS 공격 시 어떤 스크립트든 실행 가능하고,
> HSTS가 없으면 HTTP로 접속 시 쿠키가 평문으로 전송될 수 있다.

```bash
# User-Agent 변경 — 서버가 클라이언트에 따라 다르게 응답하는지 확인
curl -sI -H "User-Agent: Mozilla/5.0 Chrome/120.0.0.0" http://10.20.30.80:3000/ | head -3
curl -sI -H "User-Agent: sqlmap/1.0" http://10.20.30.80:3000/ | head -3
```

> **왜 User-Agent를 변경하는가?**
> 일부 WAF/IPS는 sqlmap, nikto 같은 도구의 User-Agent를 탐지하여 차단한다.
> 공격자는 Chrome이나 Firefox의 User-Agent로 위장하여 이를 우회한다.
> Week 10(IPS 우회)에서 이 기법을 심화 학습한다.

---

## 5. HTTPS와 TLS

### 5.1 HTTP vs HTTPS

| 항목 | HTTP | HTTPS |
|------|------|-------|
| 포트 | 80 | 443 |
| 암호화 | 없음 (평문) | TLS로 암호화 |
| 도청 가능 | 가능 | 불가능 |
| URL 시작 | http:// | https:// |

### 5.2 TLS 핸드셰이크 (간소화)

HTTPS 연결이 시작될 때 클라이언트와 서버가 암호화 방법을 협상하는 과정이다:

```
1. 클라이언트 → 서버: "안녕, 나는 이런 암호화를 지원해" (ClientHello)
2. 서버 → 클라이언트: "이 방법으로 하자, 내 인증서야" (ServerHello + Certificate)
3. 클라이언트: 인증서 검증 후, 비밀 키 교환
4. 양쪽: 공유된 키로 암호화 통신 시작
```

### 실습: TLS 인증서 확인

우리 인프라에서 HTTPS를 사용하는 서비스는 **Wazuh Dashboard** (siem:443)이다.

```bash
# Wazuh Dashboard의 TLS 인증서 확인
curl -vk https://10.20.30.100:443/ 2>&1 | grep -A5 "Server certificate"

# openssl로 상세 확인
echo | openssl s_client -connect 10.20.30.100:443 2>/dev/null | openssl x509 -noout -subject -dates

# 인증서 발급자와 주체 확인
echo | openssl s_client -connect 10.20.30.100:443 2>/dev/null | openssl x509 -noout -issuer -subject
```

**예상 출력:**
```
subject=C = US, L = California, O = Wazuh, OU = Wazuh, CN = wazuh-dashboard
notBefore=Mar 24 05:23:34 2026 GMT
notAfter=Mar 21 05:23:34 2036 GMT
```

> **분석 포인트:**
> - `CN = wazuh-dashboard`: 인증서의 Common Name (도메인 대신 이름)
> - 유효기간: 10년 (자체 서명 인증서에서 흔한 설정)
> - 자체 서명(self-signed) 인증서이므로 브라우저에서 "안전하지 않음" 경고 발생
> - `-k` 옵션은 인증서 검증을 무시 (실습 환경에서만 사용, 실무에서는 위험)
>
> **참고:** JuiceShop(:3000)과 Apache(:80)는 HTTP만 사용하며 HTTPS 미설정이다.

---

## 6. 쿠키(Cookie)와 세션(Session)

### 6.1 쿠키란?

쿠키는 서버가 브라우저에 저장하는 작은 데이터 조각이다. 브라우저는 같은 서버에 요청할 때마다 쿠키를 자동으로 함께 보낸다.

**쿠키 동작 흐름:**
```
1. 브라우저 → 서버: 로그인 요청 (ID/PW)
2. 서버 → 브라우저: "로그인 성공! 이 쿠키를 저장해" (Set-Cookie 헤더)
3. 브라우저 → 서버: 이후 모든 요청에 쿠키 자동 첨부
```

### 6.2 쿠키 속성

| 속성 | 의미 | 보안 영향 |
|------|------|-----------|
| `HttpOnly` | JavaScript에서 접근 불가 | XSS로 쿠키 탈취 방지 |
| `Secure` | HTTPS에서만 전송 | 네트워크 도청 방지 |
| `SameSite` | 동일 사이트에서만 전송 | CSRF 공격 방지 |
| `Path` | 특정 경로에서만 전송 | 범위 제한 |
| `Expires/Max-Age` | 만료 시간 | 세션 수명 관리 |

### 실습: JuiceShop 인증과 쿠키/토큰

> **이 실습을 왜 하는가?**
> 웹 해킹의 핵심 목표 중 하나가 **다른 사용자의 세션을 탈취**하는 것이다.
> 세션이 쿠키로 관리되든 JWT로 관리되든, 그 메커니즘을 이해해야
> XSS(Week 05), 세션 하이재킹, CSRF(Week 06) 공격을 이해할 수 있다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - JuiceShop이 쿠키 기반인지 JWT 기반인지
> - 토큰에 어떤 정보가 포함되는지 (민감 정보 유출 여부)
> - 토큰을 탈취하면 무엇을 할 수 있는지
>
> **실무 시나리오:** 모의해킹에서 "인증/세션 관리 점검" 항목에 해당한다.
> JWT에 패스워드 해시가 포함된 것을 발견하면 "HIGH" 위험으로 보고한다.

```bash
# Step 1: 로그인하여 토큰 확인
curl -v -c /tmp/cookies.txt -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}' 2>&1 | grep -i "set-cookie\|token"  # 요청 데이터(body)

# 저장된 쿠키 확인
cat /tmp/cookies.txt 2>/dev/null
```

> **주의:** JuiceShop은 쿠키가 아닌 **JWT 토큰을 JSON 응답 본문**에 반환한다.
> Set-Cookie 헤더는 사용하지 않는다. 이는 SPA(Single Page Application)의 일반적 패턴이다.
```

**예상 출력 (쿠키 파일):**
```
# Netscape HTTP Cookie File
10.20.30.80	FALSE	/	FALSE	0	token	eyJhbGciOiJ...
```

> 아직 admin 비밀번호를 모르므로 로그인이 실패할 수 있다. Week 04에서 SQL Injection으로 우회하는 방법을 배운다.

### 6.3 세션(Session)

세션은 서버 측에서 사용자 상태를 관리하는 방식이다:

- **쿠키 기반 인증**: 세션 ID를 쿠키에 저장, 서버가 세션 데이터 보유
- **토큰 기반 인증**: JWT 토큰을 쿠키 또는 헤더에 저장, 토큰 자체에 정보 포함

---

## 7. JWT (JSON Web Token)

### 7.1 JWT란?

JWT는 JSON 형식의 자가 포함형(self-contained) 인증 토큰이다. 서버가 세션을 저장할 필요 없이, 토큰 자체에 사용자 정보가 들어 있다.

### 7.2 JWT 구조

JWT는 점(.)으로 구분된 3개 부분으로 구성된다:

```
[헤더].[페이로드].[서명]
eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhZG1pbkBqdWljZS1zaC5vcCJ9.xxxxx
```

각 부분은 Base64URL로 인코딩되어 있다.

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

**서명 (Signature):**
```
RSASHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), privateKey)
```

### 7.3 JWT 디코딩 실습

> **이 실습을 왜 하는가?**
> JWT는 암호화가 아니라 **Base64 인코딩**이므로, 누구나 내용을 읽을 수 있다.
> 서명(Signature)은 내용을 숨기는 것이 아니라 **위변조를 방지**하는 것이다.
> 많은 개발자가 이 차이를 모르고 JWT에 비밀번호, 개인정보를 넣는 실수를 한다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 토큰에 어떤 사용자 정보가 포함되는지
> - 민감한 정보(패스워드 해시)가 토큰에 포함되는 취약점 발견
> - 토큰의 역할(admin/customer)을 확인하여 권한 상승 공격 기획
>
> **실무 시나리오:** 모의해킹에서 JWT를 디코딩하여 "패스워드 해시가 토큰에 포함됨 (CRITICAL)"을
> 보고서에 기재한다. 이는 OWASP A02(Cryptographic Failures)에 해당한다.
>
> **주의:** base64 디코딩 시 패딩(=)이 누락되어 에러가 날 수 있다. Python 스크립트가 더 안정적이다.

```bash
# Step 1: 계정 생성
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}'  # 요청 데이터(body)

# Step 2: 로그인하여 JWT 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")
echo "JWT: ${TOKEN:0:50}..."

# Step 3: JWT 페이로드 디코딩 (Python — 패딩 자동 처리)
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
p = sys.stdin.read().strip()
p += '=' * (4 - len(p) % 4)  # Base64 패딩 추가
d = json.loads(base64.urlsafe_b64decode(p))
print(json.dumps(d, indent=2, ensure_ascii=False))
"
```

**검증 완료 실제 결과:**
```json
{
  "status": "success",
  "data": {
    "id": 24,
    "username": "",
    "email": "w03verify@test.com",
    "password": "c4fcbdb8c2d1d663181e4dcdccef5f65",  ← ⚠️ 패스워드 MD5 해시!
    "role": "customer",
    "deluxeToken": "",
    "lastLoginIp": "0.0.0.0",
    "isActive": true
  }
}
```

> **⚠️ CRITICAL 발견:** JWT 페이로드에 **패스워드의 MD5 해시**가 포함되어 있다!
> 이것은 JuiceShop의 **의도적 취약점**이다. 실무에서 이런 발견은 즉시 보고해야 한다.
>
> **위험도:**
> - JWT는 누구나 디코딩할 수 있으므로, 패스워드 해시가 그대로 노출
> - MD5는 레인보우 테이블로 쉽게 크래킹 가능 (https://crackstation.net 등)
> - 공격자가 다른 사용자의 JWT를 탈취하면(XSS 등), 패스워드까지 알 수 있음
>
> **교훈:** JWT에는 최소한의 정보(user_id, role, 만료시간)만 포함해야 한다.

### 7.4 JWT를 사용한 API 호출

> **이 실습을 왜 하는가?**
> JWT 토큰은 "입장권"과 같다. 이 입장권을 가진 사람은 해당 권한의 API에 접근할 수 있다.
> XSS 등으로 토큰을 탈취하면 피해자의 권한으로 모든 API를 호출할 수 있으므로,
> 토큰 보호가 매우 중요하다는 것을 체험하는 실습이다.

```bash
# JWT 토큰으로 API 호출 (인증된 상태)
curl -s http://10.20.30.80:3000/api/Feedbacks \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d.get(\"data\",[]))}개 피드백')"

# 인증 없이 같은 API 호출
curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:3000/api/Feedbacks  # silent 모드
echo " ← Feedbacks는 인증 없이도 200 반환 (JuiceShop 특성)"
```

**검증 완료:** Feedbacks API는 인증 없이도 **200 OK**를 반환한다.
이는 JuiceShop의 설계이며, 실무에서는 인증이 필요한 API에 반드시 401/403을 반환해야 한다.

```bash
# 인증이 반드시 필요한 API 예시: 사용자 목록
curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:3000/api/Users/  # silent 모드
echo " ← Users API (인증 없음)"

curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" http://10.20.30.80:3000/api/Users/  # silent 모드
echo " ← Users API (customer 토큰)"
```

> **관찰:** customer 권한의 토큰으로도 Users API에 접근이 가능할 수 있다.
> 이는 접근제어(BOLA/IDOR) 취약점으로, Week 06에서 심화 학습한다.

---

## 8. REST API 구조

### 8.1 REST란?

REST(Representational State Transfer)는 웹 API 설계 규칙이다. URL로 **자원(Resource)**을 표현하고, HTTP 메서드로 **행위(Action)**를 표현한다.

| 행위 | HTTP 메서드 | URL 예시 | 설명 |
|------|-------------|----------|------|
| 조회 | GET | /api/Products | 전체 목록 |
| 조회 | GET | /api/Products/1 | 특정 항목 |
| 생성 | POST | /api/Products | 새 항목 생성 |
| 수정 | PUT | /api/Products/1 | 항목 수정 |
| 삭제 | DELETE | /api/Products/1 | 항목 삭제 |

### 8.2 JuiceShop REST API 탐색

> **이 실습을 왜 하는가?**
> 모의해킹에서 "API 엔드포인트 열거"는 가장 중요한 정보수집 단계이다.
> 어떤 API가 존재하고, 어떤 데이터를 반환하고, 어떤 인증이 필요한지를 파악하면
> 공격 표면(attack surface)을 완전히 이해할 수 있다.
>
> **실무 활용:** API 보안 점검 보고서에서 "엔드포인트 목록 + 인증 여부 + 반환 데이터 민감도"를
> 정리한 표가 필수 항목이다. 이 실습이 그 표를 만드는 연습이다.

```bash
# 제품 전체 목록 (인증 불필요)
curl -s http://10.20.30.80:3000/api/Products | python3 -c "  # silent 모드
import sys,json; d=json.load(sys.stdin)
print(f'상품 수: {len(d.get(\"data\",[]))}')
for p in d['data'][:3]:                                # 반복문 시작
    print(f'  [{p[\"id\"]}] {p[\"name\"]} - \${p[\"price\"]}')
"

# 특정 제품 조회 (ID로 접근)
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -m json.tool | head -15  # silent 모드

# 사용자 목록 (인증 필요)
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'사용자 수: {len(d.get(\"data\",[]))}')"

# 리뷰 목록 (인증 불필요!)
curl -s http://10.20.30.80:3000/api/Feedbacks | python3 -m json.tool | head -20  # silent 모드

# 챌린지 목록 (JuiceShop 특수 API)
curl -s http://10.20.30.80:3000/api/Challenges | python3 -m json.tool | head -30  # silent 모드

# 검색 기능
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -m json.tool  # silent 모드
```

### 8.3 API 응답 구조 분석

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

---

## 9. 종합 실습: JuiceShop 완전 분석

> **이 종합 실습의 목적:**
> 지금까지 배운 HTTP 분석 기법을 모두 결합하여 JuiceShop의 전체 API 구조를 파악한다.
> 이는 실제 모의해킹의 "정보수집" 단계를 체험하는 것이며,
> 여기서 발견한 엔드포인트와 토큰 구조가 Week 04(SQLi), Week 05(XSS), Week 06(접근제어)에서
> 공격 대상이 된다.

### Step 1: API 엔드포인트 열거

> **실습 방법:** JavaScript 소스(main.js)에서 API 경로를 추출한다. SPA는 프론트엔드 코드에
> 모든 API URL이 하드코딩되어 있으므로, JS 파일 분석이 가장 효과적인 API 열거 방법이다.

```bash
# main.js에서 /api/ 경로 추출 (검증 완료: 14개 발견)
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE '/api/[A-Za-z]+' | sort -u
```

**검증 완료 결과 (14개 API 엔드포인트):**
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

> **보안 분석:** 14개 엔드포인트가 발견되었다. 각각에 대해 "인증 필요 여부"를 확인하면
> 인증 없이 접근 가능한 API(접근제어 취약점)를 찾을 수 있다.

```bash
# /rest/ 경로도 추출
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE '/rest/[A-Za-z/]+' | sort -u | head -10
```

### Step 2: 인증 토큰 분석

```bash
# 로그인 후 토큰 저장
RESPONSE=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}')  # 요청 데이터(body)

echo "$RESPONSE" | python3 -m json.tool

# 토큰에서 사용자 정보 추출
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

# 페이로드 디코딩
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
payload = sys.stdin.read().strip()
# Base64 패딩 추가
payload += '=' * (4 - len(payload) % 4)
decoded = base64.urlsafe_b64decode(payload)
print(json.dumps(json.loads(decoded), indent=2))
"
```

### Step 3: 응답 헤더 보안 분석

```bash
# 보안 관련 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -iE "x-frame|x-content|x-powered|content-security|strict-transport|x-xss"
```

**분석 체크리스트:**
- [  ] `X-Frame-Options`이 설정되어 있는가?
- [  ] `X-Content-Type-Options: nosniff`가 있는가?
- [  ] `X-Powered-By`가 노출되고 있는가? (위험)
- [  ] `Content-Security-Policy`가 있는가?
- [  ] `Strict-Transport-Security`가 있는가?

---

## 10. OpsClaw로 웹 분석 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# OpsClaw로 웹 서버 분석 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week03-http-analysis","request_text":"JuiceShop HTTP 분석","master_mode":"external"}' \
  | python3 -m json.tool

# Stage 전환 후 헤더 수집 자동화
# (프로젝트 ID를 실제 값으로 교체)
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/plan \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키

curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {"order":1, "instruction_prompt":"curl -sI http://10.20.30.80:3000/", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/api/Products | head -100", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 과제

1. JuiceShop에 계정을 생성하고 로그인하여 JWT 토큰을 획득하라
2. JWT 토큰을 디코딩하여 포함된 정보(이메일, ID, 역할 등)를 정리하라
3. JuiceShop의 REST API 엔드포인트를 최소 5개 찾아서 각각 호출 결과를 기록하라
4. 응답 헤더를 분석하여 보안상 문제가 되는 헤더를 식별하고 이유를 설명하라

---

## 핵심 요약

- HTTP는 **요청(Request)**과 **응답(Response)**으로 구성되며, 메서드/상태코드/헤더를 이해해야 한다
- **HTTPS**는 TLS를 통해 HTTP를 암호화한 것이며, 인증서로 서버 신원을 검증한다
- **쿠키**는 서버가 브라우저에 저장하는 데이터로, HttpOnly/Secure 플래그가 중요하다
- **JWT**는 Base64 인코딩된 JSON 토큰으로, 누구나 내용을 읽을 수 있다 (서명으로 위변조만 방지)
- **REST API**는 URL + HTTP 메서드로 자원을 조작하며, curl로 직접 호출할 수 있다

> **다음 주 예고**: Week 04에서는 OWASP Top 10의 첫 번째 취약점인 SQL Injection을 배우고, JuiceShop에서 관리자 로그인을 우회한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** HTTP 요청에서 데이터를 서버에 전송할 때 주로 사용하는 메서드는?
- (a) GET  (b) **POST**  (c) DELETE  (d) HEAD

**Q2.** HTTP 상태 코드 403의 의미는?
- (a) 성공  (b) 리다이렉트  (c) **접근 금지(Forbidden)**  (d) 서버 오류

**Q3.** HTTPS에서 데이터를 암호화하는 프로토콜은?
- (a) SSH  (b) **TLS**  (c) FTP  (d) SMTP

**Q4.** 쿠키(Cookie)가 저장되는 위치는?
- (a) 서버 메모리  (b) 데이터베이스  (c) **클라이언트(브라우저)**  (d) DNS 서버

**Q5.** JWT 토큰의 세 부분은?
- (a) ID, PW, Token  (b) **Header, Payload, Signature**  (c) Key, Value, Hash  (d) User, Role, Time

**Q6.** REST API에서 리소스를 삭제하는 HTTP 메서드는?
- (a) POST  (b) PUT  (c) GET  (d) **DELETE**

**Q7.** `Access-Control-Allow-Origin: *`가 보안 이슈인 이유는?
- (a) 속도 저하  (b) **모든 도메인에서 API 호출 가능**  (c) 암호화 비활성화  (d) 로그 미생성

**Q8.** HTTP 상태 코드 500은 어떤 종류의 오류인가?
- (a) 클라이언트 오류  (b) 리다이렉트  (c) **서버 내부 오류**  (d) 인증 실패

**Q9.** `curl -X POST`에서 `-X POST`의 의미는?
- (a) 프록시 설정  (b) 타임아웃 설정  (c) **HTTP 메서드를 POST로 지정**  (d) 출력 형식 설정

**Q10.** 세션 ID가 URL에 노출되면 어떤 공격이 가능한가?
- (a) SQLi  (b) **세션 하이재킹**  (c) DDoS  (d) 버퍼 오버플로

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:b, Q6:d, Q7:b, Q8:c, Q9:c, Q10:b

---
