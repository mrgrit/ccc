# Week 08: 메모리 포렌식

## 학습 목표
- Volatility3를 사용하여 Linux 메모리 덤프를 분석할 수 있다
- 메모리에서 프로세스 인젝션, 숨겨진 프로세스를 탐지할 수 있다
- 루트킷의 메모리 흔적을 식별할 수 있다
- 메모리 덤프를 수집하고 분석하는 포렌식 절차를 수행할 수 있다
- 메모리 포렌식 결과를 인시던트 대응에 활용할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 메모리 포렌식 이론 + Volatility3 (Part 1) | 강의 |
| 0:50-1:30 | 메모리 수집 + 프로세스 분석 (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 악성 프로세스 탐지 실습 (Part 3) | 실습 |
| 2:30-3:10 | 루트킷 탐지 + 인시던트 연계 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **메모리 포렌식** | Memory Forensics | RAM 내용을 분석하여 증거를 찾는 기법 | 범인의 머릿속을 읽는 것 |
| **Volatility** | Volatility Framework | 메모리 포렌식 분석 프레임워크 | 메모리 현미경 |
| **메모리 덤프** | Memory Dump | RAM 전체 내용을 파일로 저장한 것 | 뇌 스캔 이미지 |
| **프로세스 인젝션** | Process Injection | 정상 프로세스에 악성 코드를 주입 | 음식에 독 넣기 |
| **루트킷** | Rootkit | 시스템에 숨어 탐지를 회피하는 악성코드 | 투명인간 |
| **VAD** | Virtual Address Descriptor | 프로세스의 가상 메모리 영역 정보 | 프로세스의 방 배치도 |
| **커널 모듈** | Kernel Module | 커널에 로드되는 코드 모듈 | 운영체제의 플러그인 |
| **syscall** | System Call | 사용자 공간에서 커널 기능을 호출 | 민원 접수 창구 |

---

# Part 1: 메모리 포렌식 이론 + Volatility3 (50분)

## 1.1 메모리 포렌식이란?

메모리 포렌식은 **시스템 RAM의 내용을 캡처하고 분석하여 실행 중인 프로세스, 네트워크 연결, 암호화 키, 악성코드 등의 증거를 확보**하는 기법이다.

### 왜 메모리 포렌식이 필요한가?

```
[디스크 포렌식의 한계]

악성코드가 디스크에 파일을 남기지 않는 경우:
  - Fileless 악성코드 (메모리에서만 실행)
  - 프로세스 인젝션 (정상 프로세스 내부에서 실행)
  - 실행 후 자체 삭제
  - 암호화된 페이로드 (디스크에서는 판독 불가)

→ 디스크만 보면 "아무것도 없다"
→ 메모리를 보면 "악성 코드가 실행 중이다"

[메모리에서만 찾을 수 있는 것]
  - 복호화된 악성 페이로드
  - 실행 중인 프로세스의 명령줄
  - 활성 네트워크 연결
  - 입력된 비밀번호/암호화 키
  - 루트킷이 숨긴 프로세스
  - 프로세스 인젝션 흔적
```

## 1.2 Volatility3 개요

```
[Volatility3 아키텍처]

Memory Dump (.raw, .lime, .vmem)
        |
        v
+---[Volatility3 Framework]---+
|                               |
|  [Autodetection]              |
|   → OS 버전 자동 감지         |
|   → 심볼 테이블 매핑          |
|                               |
|  [Plugins]                    |
|   → linux.pslist (프로세스)   |
|   → linux.pstree (트리)      |
|   → linux.netstat (네트워크) |
|   → linux.bash (히스토리)    |
|   → linux.lsmod (모듈)      |
|   → linux.malfind (악성코드) |
|   → linux.check_syscall     |
|                               |
|  [Output]                     |
|   → 텍스트, JSON, CSV        |
+-------------------------------+
```

### 주요 Volatility3 플러그인 (Linux)

| 플러그인 | 설명 | 용도 |
|----------|------|------|
| `linux.pslist` | 프로세스 목록 | 실행 중인 프로세스 확인 |
| `linux.pstree` | 프로세스 트리 | 부모-자식 관계 확인 |
| `linux.bash` | Bash 히스토리 | 실행된 명령어 확인 |
| `linux.netstat` | 네트워크 연결 | 활성 연결 확인 |
| `linux.lsmod` | 커널 모듈 | 로드된 모듈 확인 |
| `linux.malfind` | 악성코드 탐지 | 의심스러운 메모리 영역 |
| `linux.check_syscall` | 시스콜 후킹 | 루트킷 탐지 |
| `linux.proc.Maps` | 메모리 맵 | 프로세스 메모리 레이아웃 |
| `linux.elfs` | ELF 추출 | 메모리에서 바이너리 추출 |
| `linux.envvars` | 환경변수 | 프로세스 환경변수 확인 |

## 1.3 메모리 수집 방법

### Linux 메모리 수집 도구

```
[LiME (Linux Memory Extractor)]
  가장 널리 사용되는 Linux 메모리 수집 도구
  커널 모듈 형태로 동작
  
  # 설치 및 사용
  git clone https://github.com/504ensicsLabs/LiME
  cd LiME/src && make
  sudo insmod lime-$(uname -r).ko "path=/tmp/memdump.lime format=lime"

[/dev/mem 또는 /proc/kcore]
  직접 접근 (보안상 제한적)
  
  # /proc/kcore 복사 (일부 시스템)
  sudo cp /proc/kcore /tmp/kcore_dump

[AVML (Acquire Volatile Memory for Linux)]
  Microsoft의 메모리 수집 도구
  
  sudo ./avml /tmp/memdump.raw

[dd 기반 (제한적)]
  sudo dd if=/dev/mem of=/tmp/memdump.raw bs=1M
  # 최신 커널에서는 보안상 제한됨
```

### 수집 시 주의사항

```
[메모리 수집 원칙]

1. 최소 침해
   → 수집 도구 자체가 메모리를 변경하므로 최소화
   → 네트워크 마운트 사용 (로컬 디스크 쓰기 최소화)

2. 해시 기록
   → 수집 즉시 SHA-256 해시 생성
   → 수집 로그(시각, 도구, 담당자) 기록

3. 우선순위
   → 메모리 > 디스크 > 네트워크 (휘발성 순)
   → RFC 3227 (Evidence Collection Order)

4. 실행 환경 기록
   → uname -a, uptime, date
   → 수집 전후 프로세스 목록
```

---

# Part 2: 메모리 수집 + 프로세스 분석 (40분)

## 2.1 실습 환경 메모리 정보 수집

> **실습 목적**: 라이브 시스템에서 메모리 관련 정보를 수집하여 포렌식 분석의 기초를 다진다.
>
> **배우는 것**: /proc 파일시스템 활용, 프로세스 메모리 맵 분석

```bash
# 메모리 정보 수집 (라이브 분석)
cat << 'SCRIPT' > /tmp/mem_collect.sh
#!/bin/bash
echo "============================================"
echo "  메모리 포렌식 정보 수집"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "=== 1. 시스템 정보 ==="
uname -a
echo "Uptime: $(uptime)"
echo "Memory: $(free -h | grep Mem | awk '{print $2, "total,", $3, "used,", $4, "free"}')"

echo ""
echo "=== 2. 프로세스 목록 (메모리 사용 상위) ==="
ps aux --sort=-%mem | head -15

echo ""
echo "=== 3. /proc/meminfo 요약 ==="
grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree" /proc/meminfo

echo ""
echo "=== 4. 커널 모듈 ==="
lsmod | head -20

echo ""
echo "=== 5. 프로세스별 메모리 맵 (상위 프로세스) ==="
TOP_PID=$(ps aux --sort=-%mem | awk 'NR==2{print $2}')
TOP_PROC=$(ps aux --sort=-%mem | awk 'NR==2{print $11}')
echo "상위 프로세스: PID=$TOP_PID ($TOP_PROC)"
cat /proc/$TOP_PID/maps 2>/dev/null | head -20

echo ""
echo "=== 6. 삭제된 파일을 참조하는 프로세스 ==="
ls -la /proc/*/exe 2>/dev/null | grep "(deleted)" | head -10 || echo "(없음)"

echo ""
echo "=== 7. /dev/shm 내용 (공유 메모리) ==="
ls -la /dev/shm/ 2>/dev/null | head -10
SCRIPT

bash /tmp/mem_collect.sh
```

> **결과 해석**: 삭제된 바이너리를 참조하는 프로세스가 있다면 악성코드가 실행 후 자체 삭제한 것일 수 있다. /dev/shm에 실행 파일이 있으면 파일리스 공격 의심.

## 2.2 프로세스 메모리 심화 분석

```bash
# 특정 프로세스의 메모리 상세 분석
cat << 'SCRIPT' > /tmp/proc_memory_analysis.py
#!/usr/bin/env python3
"""프로세스 메모리 분석 (라이브)"""
import os
import re

def analyze_process(pid):
    """특정 PID의 메모리 맵 분석"""
    print(f"\n=== PID {pid} 메모리 분석 ===")
    
    # 프로세스 정보
    try:
        with open(f'/proc/{pid}/comm') as f:
            name = f.read().strip()
        with open(f'/proc/{pid}/cmdline') as f:
            cmdline = f.read().replace('\x00', ' ').strip()
        with open(f'/proc/{pid}/status') as f:
            status = f.read()
        
        print(f"이름: {name}")
        print(f"명령줄: {cmdline[:80]}")
        
        # 메모리 사용량
        vm_rss = re.search(r'VmRSS:\s+(\d+)', status)
        vm_size = re.search(r'VmSize:\s+(\d+)', status)
        if vm_rss:
            print(f"RSS: {int(vm_rss.group(1)):,} kB")
        if vm_size:
            print(f"Virtual: {int(vm_size.group(1)):,} kB")
    except Exception as e:
        print(f"접근 불가: {e}")
        return
    
    # 메모리 맵 분석
    try:
        with open(f'/proc/{pid}/maps') as f:
            maps = f.readlines()
        
        regions = {"executable": 0, "writable": 0, "shared": 0, "anonymous": 0}
        suspicious = []
        
        for line in maps:
            parts = line.strip().split()
            perms = parts[1] if len(parts) > 1 else ""
            path = parts[-1] if len(parts) > 5 else "[anonymous]"
            
            if 'x' in perms:
                regions["executable"] += 1
            if 'w' in perms:
                regions["writable"] += 1
            if 's' in perms:
                regions["shared"] += 1
            if path == "":
                regions["anonymous"] += 1
            
            # 의심스러운 패턴
            if 'x' in perms and 'w' in perms:
                suspicious.append(f"  RWX: {line.strip()[:70]}")
            if '/tmp/' in path or '/dev/shm/' in path:
                suspicious.append(f"  TMP: {line.strip()[:70]}")
        
        print(f"\n메모리 영역: exec={regions['executable']}, "
              f"write={regions['writable']}, anon={regions['anonymous']}")
        
        if suspicious:
            print(f"\n[경고] 의심스러운 메모리 영역 ({len(suspicious)}건):")
            for s in suspicious[:5]:
                print(s)
        else:
            print("\n[정상] 의심스러운 메모리 영역 없음")
    except:
        print("메모리 맵 읽기 실패")

# 상위 5개 프로세스 분석
import subprocess
result = subprocess.run(['ps', 'aux', '--sort=-%mem'], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')[1:6]

for line in lines:
    pid = line.split()[1]
    analyze_process(pid)
SCRIPT

python3 /tmp/proc_memory_analysis.py
```

> **배우는 것**: RWX(읽기+쓰기+실행) 권한이 있는 메모리 영역은 프로세스 인젝션의 강력한 지표다. /tmp이나 /dev/shm에서 로드된 라이브러리도 의심 대상이다.

---

# Part 3: 악성 프로세스 탐지 실습 (50분)

## 3.1 프로세스 이상 탐지

```bash
cat << 'SCRIPT' > /tmp/detect_malicious_process.sh
#!/bin/bash
echo "============================================"
echo "  악성 프로세스 탐지"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "--- 1. 프로세스 트리에서 비정상 부모-자식 관계 ---"
ps -eo pid,ppid,user,comm --forest | while read pid ppid user comm; do
    # 웹서버에서 셸 실행
    if echo "$comm" | grep -qE "^(bash|sh|dash|zsh|python|perl|ruby|nc)$"; then
        parent_comm=$(ps -p "$ppid" -o comm= 2>/dev/null)
        if echo "$parent_comm" | grep -qE "apache|nginx|httpd|node|java|tomcat"; then
            echo "  [경고] $parent_comm(PID:$ppid) → $comm(PID:$pid) by $user"
        fi
    fi
done

echo ""
echo "--- 2. 숨겨진 프로세스 (ps vs /proc 비교) ---"
PS_PIDS=$(ps -eo pid --no-headers | sort -n)
PROC_PIDS=$(ls -d /proc/[0-9]* 2>/dev/null | sed 's|/proc/||' | sort -n)
HIDDEN=$(comm -13 <(echo "$PS_PIDS") <(echo "$PROC_PIDS"))
if [ -n "$HIDDEN" ]; then
    echo "  [경고] 숨겨진 프로세스 PID: $HIDDEN"
else
    echo "  [정상] 숨겨진 프로세스 없음"
fi

echo ""
echo "--- 3. 환경변수 LD_PRELOAD 검사 ---"
for pid in $(ls /proc/ | grep -E '^[0-9]+$' | head -50); do
    environ=$(cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep "LD_PRELOAD")
    if [ -n "$environ" ]; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "  [경고] PID $pid ($comm): $environ"
    fi
done
echo "  검사 완료"

echo ""
echo "--- 4. 비정상 네트워크 연결을 가진 프로세스 ---"
ss -tnp 2>/dev/null | grep ESTAB | while read state recv send local remote proc; do
    # 외부 연결
    remote_ip=$(echo "$remote" | rev | cut -d: -f2- | rev)
    if ! echo "$remote_ip" | grep -qE "^10\.|^172\.|^192\.168\.|^127\."; then
        pid=$(echo "$proc" | grep -oP 'pid=\K\d+')
        if [ -n "$pid" ]; then
            comm=$(ps -p "$pid" -o comm= 2>/dev/null)
            echo "  $comm(PID:$pid) → $remote"
        fi
    fi
done

echo ""
echo "--- 5. 메모리 기반 실행 (memfd_create) ---"
ls -la /proc/*/exe 2>/dev/null | grep "memfd:" | while read line; do
    pid=$(echo "$line" | grep -oP '/proc/\K\d+')
    comm=$(cat /proc/$pid/comm 2>/dev/null)
    echo "  [경고] memfd 실행: PID $pid ($comm)"
done
echo "  검사 완료"
SCRIPT

bash /tmp/detect_malicious_process.sh
```

> **결과 해석**:
> - 웹서버→셸: 웹셸 실행 가능성 (즉시 조사)
> - 숨겨진 프로세스: 루트킷 가능성 (긴급)
> - LD_PRELOAD: 라이브러리 하이재킹 (심각)
> - memfd: 파일리스 실행 (고도 위협)

## 3.2 Volatility3 사용법 (교육용 시뮬레이션)

```bash
cat << 'SCRIPT' > /tmp/vol3_simulation.py
#!/usr/bin/env python3
"""Volatility3 분석 시뮬레이션 (교육용)"""

print("=" * 60)
print("  Volatility3 Linux 플러그인 사용법")
print("=" * 60)

plugins = {
    "linux.pslist.PsList": {
        "설명": "프로세스 목록 출력",
        "명령": "vol -f memdump.lime linux.pslist.PsList",
        "분석": "PID, PPID, UID, 실행 파일명 확인",
        "의심": "비정상 PID 간격, 알 수 없는 프로세스명",
    },
    "linux.pstree.PsTree": {
        "설명": "프로세스 트리 구조",
        "명령": "vol -f memdump.lime linux.pstree.PsTree",
        "분석": "부모-자식 관계 확인",
        "의심": "apache→bash, sshd→python 등 비정상 관계",
    },
    "linux.bash.Bash": {
        "설명": "Bash 명령 히스토리 추출",
        "명령": "vol -f memdump.lime linux.bash.Bash",
        "분석": "실행된 명령어 타임라인 재구성",
        "의심": "wget, curl, nc, base64 등 공격 도구 사용",
    },
    "linux.netstat.Netstat": {
        "설명": "네트워크 연결 목록",
        "명령": "vol -f memdump.lime linux.netstat.Netstat",
        "분석": "활성 TCP/UDP 연결 확인",
        "의심": "외부 IP로의 비표준 포트 연결, C2 통신",
    },
    "linux.lsmod.Lsmod": {
        "설명": "로드된 커널 모듈",
        "명령": "vol -f memdump.lime linux.lsmod.Lsmod",
        "분석": "커널 모듈 목록과 크기 확인",
        "의심": "알 수 없는 모듈, 비정상 크기",
    },
    "linux.malfind.Malfind": {
        "설명": "악성코드 탐지 (의심 메모리 영역)",
        "명령": "vol -f memdump.lime linux.malfind.Malfind",
        "분석": "RWX 권한, 인젝션 흔적 확인",
        "의심": "실행+쓰기 권한이 동시에 있는 익명 영역",
    },
    "linux.check_syscall.Check_syscall": {
        "설명": "시스콜 테이블 후킹 탐지",
        "명령": "vol -f memdump.lime linux.check_syscall.Check_syscall",
        "분석": "시스콜 핸들러 주소가 정상 범위인지 확인",
        "의심": "커널 코드 영역 밖의 핸들러 주소",
    },
}

for name, info in plugins.items():
    print(f"\n--- {name} ---")
    print(f"  설명: {info['설명']}")
    print(f"  명령: {info['명령']}")
    print(f"  분석: {info['분석']}")
    print(f"  의심: {info['의심']}")

print("\n=== Volatility3 설치 ===")
print("pip install volatility3")
print("vol -h  # 도움말")
print("vol -f <dump> <plugin>  # 기본 실행")
SCRIPT

python3 /tmp/vol3_simulation.py
```

## 3.3 프로세스 인젝션 탐지 (라이브)

```bash
cat << 'SCRIPT' > /tmp/detect_injection.py
#!/usr/bin/env python3
"""프로세스 인젝션 탐지 (라이브 분석)"""
import os
import re

def check_injection(pid):
    """PID의 메모리 맵에서 인젝션 흔적 검색"""
    findings = []
    try:
        with open(f'/proc/{pid}/maps') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 6:
                    continue
                addr_range = parts[0]
                perms = parts[1]
                path = parts[-1] if len(parts) > 5 else ""
                
                # RWX 익명 메모리 (인젝션의 강력한 지표)
                if 'r' in perms and 'w' in perms and 'x' in perms:
                    if not path or path == '[stack]' or path == '[heap]':
                        continue  # stack/heap은 일부 정상
                    if '/lib/' not in path and '/usr/' not in path:
                        findings.append(f"RWX 비정상: {addr_range} {perms} {path}")
                
                # 삭제된 파일에서 로드된 라이브러리
                if '(deleted)' in line:
                    findings.append(f"삭제된 매핑: {line.strip()[:60]}")
                
                # /tmp, /dev/shm에서 로드된 실행 코드
                if ('x' in perms) and ('/tmp/' in path or '/dev/shm/' in path):
                    findings.append(f"TMP 실행: {path}")
                    
    except (PermissionError, FileNotFoundError):
        pass
    
    return findings

print("=" * 60)
print("  프로세스 인젝션 탐지 스캔")
print("=" * 60)

total_checked = 0
total_suspicious = 0

for pid_dir in sorted(os.listdir('/proc')):
    if not pid_dir.isdigit():
        continue
    
    pid = pid_dir
    findings = check_injection(pid)
    total_checked += 1
    
    if findings:
        total_suspicious += 1
        try:
            comm = open(f'/proc/{pid}/comm').read().strip()
        except:
            comm = "?"
        print(f"\n[의심] PID {pid} ({comm}):")
        for f in findings:
            print(f"  - {f}")

print(f"\n검사 완료: {total_checked}개 프로세스 중 {total_suspicious}개 의심")
if total_suspicious == 0:
    print("[정상] 프로세스 인젝션 흔적 없음")
SCRIPT

python3 /tmp/detect_injection.py
```

> **트러블슈팅**:
> - "Permission denied" → root 권한으로 실행 필요
> - 정상 프로세스도 표시될 수 있음 → JIT 컴파일러(Java, Node.js)는 RWX를 사용할 수 있음

---

# Part 4: 루트킷 탐지 + 인시던트 연계 (40분)

## 4.1 루트킷 흔적 탐지

```bash
cat << 'SCRIPT' > /tmp/detect_rootkit.sh
#!/bin/bash
echo "============================================"
echo "  루트킷 탐지 점검"
echo "  서버: $(hostname) / $(date)"
echo "============================================"

echo ""
echo "--- 1. 커널 모듈 이상 점검 ---"
LOADED=$(lsmod | awk 'NR>1{print $1}' | sort)
BUILTIN=$(cat /lib/modules/$(uname -r)/modules.builtin 2>/dev/null | \
  sed 's|.*/||;s|\.ko.*||' | sort)

echo "로드된 모듈 수: $(echo "$LOADED" | wc -w)"
echo "알 수 없는 모듈:"
for mod in $LOADED; do
    if ! modinfo "$mod" &>/dev/null; then
        echo "  [경고] $mod (modinfo 실패)"
    fi
done

echo ""
echo "--- 2. 시스콜 테이블 점검 ---"
# /proc/kallsyms에서 시스콜 테이블 주소 확인
if [ -r /proc/kallsyms ]; then
    echo "sys_call_table 주소:"
    grep "sys_call_table" /proc/kallsyms 2>/dev/null | head -3
else
    echo "  (kallsyms 접근 불가 - kptr_restrict)"
fi

echo ""
echo "--- 3. /etc/ld.so.preload 점검 ---"
if [ -f /etc/ld.so.preload ]; then
    echo "  [경고] ld.so.preload 존재!"
    cat /etc/ld.so.preload
else
    echo "  [정상] ld.so.preload 없음"
fi

echo ""
echo "--- 4. 숨겨진 파일 점검 (. 접두사 비정상) ---"
find /tmp /var/tmp /dev/shm -name ".*" -type f 2>/dev/null | head -10

echo ""
echo "--- 5. chkrootkit/rkhunter 존재 확인 ---"
which chkrootkit 2>/dev/null && echo "chkrootkit 설치됨" || echo "chkrootkit 미설치"
which rkhunter 2>/dev/null && echo "rkhunter 설치됨" || echo "rkhunter 미설치"

echo ""
echo "--- 6. 네트워크 인터페이스 프로미스큐어스 모드 ---"
ip link show 2>/dev/null | grep PROMISC && echo "  [경고] 프로미스큐어스 모드!" || echo "  [정상] 프로미스큐어스 모드 아님"
SCRIPT

bash /tmp/detect_rootkit.sh

echo ""
echo "=== 원격 서버 점검 ==="
for server in "secu@10.20.30.1" "web@10.20.30.80"; do
    echo ""
    echo "--- $server ---"
    sshpass -p1 ssh -o ConnectTimeout=5 "$server" 'bash -s' < /tmp/detect_rootkit.sh 2>/dev/null | \
      grep -E "\[경고\]|\[정상\]|루트킷"
done
```

## 4.2 메모리 포렌식 + 인시던트 대응 워크플로우

```bash
cat << 'SCRIPT' > /tmp/mem_forensics_workflow.py
#!/usr/bin/env python3
"""메모리 포렌식 인시던트 대응 워크플로우"""

workflow = [
    {
        "단계": "1. 메모리 수집",
        "도구": "LiME / AVML",
        "명령": [
            "sudo insmod lime.ko 'path=/evidence/memdump.lime format=lime'",
            "sha256sum /evidence/memdump.lime > /evidence/memdump.lime.sha256",
        ],
        "주의": "수집 중 시스템 변경 최소화",
    },
    {
        "단계": "2. 프로세스 분석",
        "도구": "Volatility3 linux.pslist, linux.pstree",
        "명령": [
            "vol -f memdump.lime linux.pslist.PsList",
            "vol -f memdump.lime linux.pstree.PsTree",
        ],
        "주의": "비정상 부모-자식 관계, 알 수 없는 프로세스 확인",
    },
    {
        "단계": "3. 네트워크 분석",
        "도구": "Volatility3 linux.netstat",
        "명령": [
            "vol -f memdump.lime linux.netstat.Netstat",
        ],
        "주의": "C2 통신, 외부 연결, 비표준 포트 확인",
    },
    {
        "단계": "4. 악성코드 탐지",
        "도구": "Volatility3 linux.malfind",
        "명령": [
            "vol -f memdump.lime linux.malfind.Malfind",
            "vol -f memdump.lime linux.elfs.Elfs --pid <PID>",
        ],
        "주의": "RWX 메모리, 인젝션 흔적, 의심 바이너리 추출",
    },
    {
        "단계": "5. 루트킷 점검",
        "도구": "Volatility3 linux.check_syscall, linux.lsmod",
        "명령": [
            "vol -f memdump.lime linux.check_syscall.Check_syscall",
            "vol -f memdump.lime linux.lsmod.Lsmod",
        ],
        "주의": "시스콜 후킹, 숨겨진 모듈 확인",
    },
    {
        "단계": "6. 증거 추출",
        "도구": "Volatility3 linux.bash, linux.envvars",
        "명령": [
            "vol -f memdump.lime linux.bash.Bash",
            "vol -f memdump.lime linux.envvars.Envvars --pid <PID>",
        ],
        "주의": "공격자 명령 히스토리, 환경변수 수집",
    },
]

print("=" * 60)
print("  메모리 포렌식 인시던트 대응 워크플로우")
print("=" * 60)

for step in workflow:
    print(f"\n--- {step['단계']} ---")
    print(f"  도구: {step['도구']}")
    for cmd in step['명령']:
        print(f"  $ {cmd}")
    print(f"  주의: {step['주의']}")
SCRIPT

python3 /tmp/mem_forensics_workflow.py
```

## 4.3 OpsClaw를 활용한 메모리 점검 자동화

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "memory-forensics-check",
    "request_text": "전체 서버 메모리 포렌식 점검",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "ls -la /proc/*/exe 2>/dev/null | grep -c \"deleted\" && echo DELETED_CHECK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "test -f /etc/ld.so.preload && echo LD_PRELOAD_EXISTS || echo LD_PRELOAD_CLEAN",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 체크리스트

- [ ] 메모리 포렌식이 디스크 포렌식보다 유리한 경우를 설명할 수 있다
- [ ] Volatility3의 주요 Linux 플러그인 7개를 알고 있다
- [ ] LiME을 사용한 메모리 수집 방법을 이해한다
- [ ] 메모리 수집 시 주의사항(무결성, 해시, 우선순위)을 알고 있다
- [ ] /proc 파일시스템으로 프로세스 메모리를 분석할 수 있다
- [ ] RWX 메모리 영역이 프로세스 인젝션의 지표임을 이해한다
- [ ] 루트킷의 메모리 흔적(커널 모듈, 시스콜 후킹)을 탐지할 수 있다
- [ ] LD_PRELOAD 하이재킹을 점검할 수 있다
- [ ] 메모리 포렌식 6단계 워크플로우를 설명할 수 있다
- [ ] 메모리 포렌식 결과를 인시던트 대응에 연계할 수 있다

---

## 복습 퀴즈

**Q1.** Fileless 악성코드를 디스크 포렌식으로 탐지할 수 없는 이유는?

<details><summary>정답</summary>
파일리스 악성코드는 디스크에 파일을 생성하지 않고 메모리에서만 실행된다. 프로세스 인젝션, memfd_create, PowerShell/bash 인메모리 실행 등을 사용하므로 디스크 스캔에 걸리지 않는다.
</details>

**Q2.** Volatility3의 linux.malfind 플러그인이 탐지하는 것은?

<details><summary>정답</summary>
RWX(읽기+쓰기+실행) 권한을 가진 의심스러운 메모리 영역을 탐지한다. 정상 프로세스는 대부분 RX(읽기+실행) 또는 RW(읽기+쓰기) 영역을 사용하고, RWX는 프로세스 인젝션이나 셸코드 실행의 강력한 지표다.
</details>

**Q3.** LiME으로 메모리를 수집한 후 가장 먼저 해야 할 것은?

<details><summary>정답</summary>
수집된 메모리 덤프 파일의 SHA-256 해시를 즉시 계산하고 기록한다. 이후 분석 과정에서 증거가 변조되지 않았음을 증명하는 무결성 확인의 기초 자료다.
</details>

**Q4.** /etc/ld.so.preload 파일이 존재하면 왜 위험한가?

<details><summary>정답</summary>
모든 프로세스 실행 시 이 파일에 지정된 공유 라이브러리가 먼저 로드된다. 루트킷이 악성 라이브러리를 여기에 등록하면 모든 프로세스에 악성 코드가 주입되어 시스템 전체를 장악할 수 있다.
</details>

**Q5.** ps와 /proc에서 프로세스 목록이 다를 때 의미하는 바는?

<details><summary>정답</summary>
루트킷이 ps 명령(또는 libproc)을 후킹하여 특정 프로세스를 숨기고 있을 가능성이 있다. /proc는 커널이 직접 제공하는 정보이므로 더 신뢰할 수 있다.
</details>

**Q6.** memfd_create로 실행된 프로세스의 특징은?

<details><summary>정답</summary>
/proc/<pid>/exe가 memfd:<name> 형태를 가리키며, 디스크에 파일이 존재하지 않는다. 파일리스 공격에 사용되며, 메모리에서만 실행되어 디스크 기반 탐지를 완전히 우회한다.
</details>

**Q7.** 프로세스 인젝션의 3가지 일반적 방법을 설명하시오.

<details><summary>정답</summary>
1) ptrace: 디버거 기능을 악용하여 다른 프로세스에 코드 주입, 2) LD_PRELOAD: 공유 라이브러리 사전 로딩으로 함수 후킹, 3) /proc/<pid>/mem: 프로세스 메모리에 직접 쓰기로 코드 삽입.
</details>

**Q8.** RFC 3227에서 정의한 증거 수집 우선순위는?

<details><summary>정답</summary>
휘발성이 높은 순서대로: 1) 레지스터/캐시 → 2) 라우팅 테이블/ARP/프로세스 → 3) 메모리(RAM) → 4) 임시 파일 → 5) 디스크 → 6) 원격 로그/모니터링. 메모리는 디스크보다 먼저 수집해야 한다.
</details>

**Q9.** 커널 모듈 루트킷과 사용자 공간 루트킷의 차이는?

<details><summary>정답</summary>
커널 모듈 루트킷은 커널 영역에서 동작하여 시스콜 테이블을 직접 수정하며 탐지가 매우 어렵다. 사용자 공간 루트킷은 LD_PRELOAD나 라이브러리 후킹으로 동작하며, 커널 수준 분석으로 탐지 가능하다.
</details>

**Q10.** 메모리 포렌식 결과에서 apache 프로세스가 외부 IP와 4444 포트로 연결되어 있다면?

<details><summary>정답</summary>
리버스 셸 가능성이 매우 높다. 4444는 Metasploit 기본 리스너 포트이며, 웹서버가 외부로 아웃바운드 연결을 하는 것은 비정상이다. 즉시 해당 연결을 차단하고 웹서버의 웹셸 존재 여부를 확인해야 한다.
</details>

---

## 과제

### 과제 1: 라이브 메모리 분석 보고서 (필수)

실습 환경 전체 서버에 대해 라이브 메모리 분석을 수행하고:
1. 프로세스 인젝션 흔적 점검 결과
2. 루트킷 탐지 점검 결과
3. LD_PRELOAD / memfd 점검 결과
4. 발견 사항 및 권고 사항

### 과제 2: Volatility3 분석 계획서 (선택)

가상의 침해사고 시나리오를 설정하고:
1. 메모리 수집 계획 (도구, 절차, 주의사항)
2. 분석 계획 (사용할 플러그인, 분석 순서)
3. 예상 결과 및 대응 절차
4. 증거 보존 계획

---

## 보충: 메모리 포렌식 고급 분석 기법

### 프로세스 환경변수 분석

```bash
cat << 'SCRIPT' > /tmp/env_analysis.py
#!/usr/bin/env python3
"""프로세스 환경변수 포렌식 분석"""
import os

suspicious_vars = [
    "LD_PRELOAD", "LD_LIBRARY_PATH", "HISTFILE", "HISTSIZE",
    "http_proxy", "https_proxy", "PROMPT_COMMAND",
]

print("=" * 60)
print("  프로세스 환경변수 포렌식 분석")
print("=" * 60)

checked = 0
found = 0

for pid_dir in sorted(os.listdir('/proc')):
    if not pid_dir.isdigit():
        continue
    
    pid = pid_dir
    try:
        with open(f'/proc/{pid}/environ', 'rb') as f:
            environ = f.read().decode('utf-8', errors='ignore')
        
        env_vars = environ.split('\x00')
        comm = open(f'/proc/{pid}/comm').read().strip()
        checked += 1
        
        for var in env_vars:
            for susp in suspicious_vars:
                if var.startswith(f'{susp}='):
                    found += 1
                    print(f"\n  [경고] PID {pid} ({comm}):")
                    print(f"    {var[:80]}")
                    
                    if susp == "LD_PRELOAD":
                        print(f"    → 라이브러리 하이재킹 가능!")
                    elif susp == "HISTFILE":
                        if "/dev/null" in var:
                            print(f"    → 명령 히스토리 비활성화 (은닉 시도)!")
                    elif susp == "HISTSIZE" and "0" in var:
                        print(f"    → 히스토리 크기 0 (은닉 시도)!")
                    elif susp == "PROMPT_COMMAND":
                        print(f"    → 프롬프트 실행 후킹 가능!")
                        
    except (PermissionError, FileNotFoundError, UnicodeDecodeError):
        continue

print(f"\n검사: {checked}개 프로세스, 의심: {found}건")
if found == 0:
    print("[정상] 의심스러운 환경변수 없음")
SCRIPT

python3 /tmp/env_analysis.py
```

> **배우는 것**: HISTFILE=/dev/null이나 HISTSIZE=0은 공격자가 명령 히스토리를 남기지 않기 위한 은닉 기법이다. LD_PRELOAD는 라이브러리 인젝션의 지표다.

### 파일 디스크립터 분석

```bash
cat << 'SCRIPT' > /tmp/fd_analysis.sh
#!/bin/bash
echo "============================================"
echo "  파일 디스크립터 포렌식 분석"
echo "============================================"

echo ""
echo "--- 1. 삭제된 파일을 열고 있는 프로세스 ---"
for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$' | head -100); do
    ls -la /proc/$pid/fd 2>/dev/null | grep "(deleted)" | while read line; do
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "  PID $pid ($comm): $line"
    done
done | head -10
echo "  (검사 완료)"

echo ""
echo "--- 2. 네트워크 소켓을 열고 있는 프로세스 ---"
for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$' | head -50); do
    sockets=$(ls -la /proc/$pid/fd 2>/dev/null | grep -c "socket:")
    if [ "$sockets" -gt 5 ] 2>/dev/null; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "  PID $pid ($comm): 소켓 ${sockets}개"
    fi
done | head -10

echo ""
echo "--- 3. /tmp, /dev/shm 파일을 열고 있는 프로세스 ---"
for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$' | head -100); do
    tmp_fds=$(ls -la /proc/$pid/fd 2>/dev/null | grep -E "/tmp/|/dev/shm/" | head -3)
    if [ -n "$tmp_fds" ]; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "  PID $pid ($comm):"
        echo "$tmp_fds" | while read line; do echo "    $line"; done
    fi
done | head -15

echo ""
echo "--- 4. 파이프/FIFO를 사용하는 프로세스 ---"
for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$' | head -50); do
    pipes=$(ls -la /proc/$pid/fd 2>/dev/null | grep -c "pipe:")
    if [ "$pipes" -gt 10 ] 2>/dev/null; then
        comm=$(cat /proc/$pid/comm 2>/dev/null)
        echo "  PID $pid ($comm): 파이프 ${pipes}개 (프로세스간 통신)"
    fi
done | head -10
SCRIPT

bash /tmp/fd_analysis.sh
```

> **실전 활용**: 삭제된 파일의 FD가 열려있다면 공격자가 실행 후 바이너리를 삭제한 것이다. `/proc/<pid>/fd/<n>`에서 해당 파일의 내용을 복구할 수 있다:
> `cp /proc/<pid>/fd/<n> /tmp/recovered_binary`

### Volatility3 분석 자동화 스크립트

```bash
cat << 'SCRIPT' > /tmp/vol3_auto_analysis.sh
#!/bin/bash
# Volatility3 자동 분석 스크립트 (메모리 덤프가 있을 때 사용)
# Usage: ./vol3_auto_analysis.sh <memory_dump>

DUMP=${1:-"memdump.lime"}
OUTPUT_DIR="/tmp/vol3_results/$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$DUMP" ]; then
    echo "메모리 덤프 파일이 없습니다: $DUMP"
    echo "사용법: $0 <memory_dump_file>"
    echo ""
    echo "=== 분석 순서 가이드 (메모리 덤프가 있을 때) ==="
    echo ""
    echo "1단계: 기본 정보"
    echo "  vol -f \$DUMP linux.pslist.PsList > pslist.txt"
    echo "  vol -f \$DUMP linux.pstree.PsTree > pstree.txt"
    echo ""
    echo "2단계: 네트워크"
    echo "  vol -f \$DUMP linux.netstat.Netstat > netstat.txt"
    echo ""
    echo "3단계: 악성코드 탐지"
    echo "  vol -f \$DUMP linux.malfind.Malfind > malfind.txt"
    echo ""
    echo "4단계: 커널 점검"
    echo "  vol -f \$DUMP linux.lsmod.Lsmod > lsmod.txt"
    echo "  vol -f \$DUMP linux.check_syscall.Check_syscall > syscall.txt"
    echo ""
    echo "5단계: 히스토리"
    echo "  vol -f \$DUMP linux.bash.Bash > bash_history.txt"
    echo ""
    echo "6단계: 증거 추출"
    echo "  vol -f \$DUMP linux.elfs.Elfs --pid <suspicious_pid> --dump"
    exit 0
fi

mkdir -p "$OUTPUT_DIR"
echo "분석 시작: $DUMP"
echo "결과 디렉토리: $OUTPUT_DIR"

# 자동 실행
for plugin in linux.pslist.PsList linux.pstree.PsTree linux.netstat.Netstat \
              linux.malfind.Malfind linux.lsmod.Lsmod linux.bash.Bash; do
    name=$(echo "$plugin" | rev | cut -d. -f1 | rev)
    echo "  실행: $plugin..."
    vol -f "$DUMP" "$plugin" > "$OUTPUT_DIR/${name}.txt" 2>/dev/null
done

echo ""
echo "=== 분석 완료 ==="
ls -la "$OUTPUT_DIR/"
SCRIPT

chmod +x /tmp/vol3_auto_analysis.sh
bash /tmp/vol3_auto_analysis.sh
```

---

## 다음 주 예고

**Week 09: 악성코드 분석 기초**에서는 정적/동적 분석 기법으로 악성코드를 분석한다. strings, strace, sandbox 환경을 활용한 안전한 분석 방법을 학습한다.
