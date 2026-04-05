# Week 09: 악성코드 분석 기초

## 학습 목표
- 정적 분석(strings, file, hexdump)으로 악성코드의 기본 특성을 파악할 수 있다
- 동적 분석(strace, ltrace)으로 악성코드의 실행 행위를 관찰할 수 있다
- 안전한 분석 환경(sandbox)을 구성하고 활용할 수 있다
- 악성코드의 주요 행위(C2 통신, 지속성 확보, 데이터 유출)를 식별할 수 있다
- 분석 결과를 IOC로 추출하고 SIEM 룰에 반영할 수 있다

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
| 0:00-0:50 | 악성코드 분석 이론 + 분류 (Part 1) | 강의 |
| 0:50-1:30 | 정적 분석 기법 (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 동적 분석 + strace 실습 (Part 3) | 실습 |
| 2:30-3:10 | IOC 추출 + SIEM 연동 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **정적 분석** | Static Analysis | 실행하지 않고 파일 자체를 분석 | X-ray 촬영 |
| **동적 분석** | Dynamic Analysis | 실행하면서 행위를 관찰 | 미행 수사 |
| **sandbox** | Sandbox | 격리된 분석 환경 | 폭탄 해체실 |
| **strings** | Strings | 바이너리에서 문자열 추출 | 편지 내용 읽기 |
| **strace** | System Trace | 시스템 콜 추적 도구 | 행동 기록기 |
| **패킹** | Packing | 실행파일 압축/암호화 (분석 방해) | 봉인된 상자 |
| **난독화** | Obfuscation | 코드를 읽기 어렵게 변환 | 암호문 |
| **드로퍼** | Dropper | 실제 악성코드를 설치하는 1단계 파일 | 택배 배달부 |
| **페이로드** | Payload | 실제 악성 기능을 수행하는 코드 | 폭발물 |
| **C2** | Command & Control | 공격자의 원격 제어 서버 | 본부 |

---

# Part 1: 악성코드 분석 이론 + 분류 (50분)

## 1.1 악성코드 분류

```
+--[악성코드 유형]--+
|                    |
| [바이러스]         | 다른 파일에 기생하여 확산
| [웜]               | 자체 복제하여 네트워크 확산
| [트로이 목마]      | 정상 소프트웨어로 위장
| [랜섬웨어]         | 파일 암호화 후 몸값 요구
| [백도어]           | 비인가 원격 접근 제공
| [루트킷]           | 시스템에 숨어 탐지 회피
| [봇넷]             | 원격 제어 좀비 네트워크
| [스파이웨어]       | 정보 수집 및 유출
| [크립토마이너]     | 암호화폐 무단 채굴
| [웹셸]             | 웹 서버 원격 제어 백도어
+--------------------+
```

## 1.2 분석 접근법

```
[분석 단계]

1단계: 기초 정적 분석 (5분)
  → file, strings, sha256sum
  → 파일 유형, 문자열, 해시 확인
  → VirusTotal 조회

2단계: 고급 정적 분석 (30분)
  → objdump, readelf, Ghidra
  → 디스어셈블리, 함수 분석
  → 임포트/익스포트 테이블

3단계: 기초 동적 분석 (30분)
  → strace, ltrace, netstat
  → sandbox에서 실행
  → 파일/레지스트리/네트워크 모니터링

4단계: 고급 동적 분석 (수시간)
  → GDB 디버깅
  → 패킹 해제, 난독화 해제
  → 프로토콜 리버싱
```

## 1.3 분석 환경 안전 수칙

```
[필수 안전 수칙]

1. 절대로 호스트 시스템에서 악성코드를 실행하지 마라
2. 분석은 반드시 격리된 VM/sandbox에서 수행
3. 네트워크는 차단하거나 가짜 서버로 리디렉션
4. 분석 완료 후 VM 스냅샷으로 롤백
5. 실수로 실행하는 것을 방지하기 위해 확장자 변경
   (.exe → .exe.malware, .elf → .elf.sample)
6. 클립보드 공유 비활성화
7. 공유 폴더 최소화
```

---

# Part 2: 정적 분석 기법 (40분)

## 2.1 기초 정적 분석 도구

> **실습 목적**: 안전한 테스트 샘플을 만들어 정적 분석 도구의 사용법을 익힌다.
>
> **배우는 것**: file, strings, hexdump, readelf, objdump 활용법

```bash
# 교육용 테스트 샘플 생성 (실제 악성코드가 아님)
cat << 'CODE' > /tmp/test_sample.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// 교육용: 악성코드가 흔히 사용하는 패턴 시뮬레이션
const char *c2_server = "http://evil.example.com:4444/beacon";
const char *user_agent = "Mozilla/5.0 (compatible; Bot/1.0)";
const char *persistence_path = "/tmp/.hidden_service";

int main() {
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    
    // C2 통신 시뮬레이션 (실제 연결 안 함)
    printf("Connecting to %s\n", c2_server);
    printf("User-Agent: %s\n", user_agent);
    printf("Hostname: %s\n", hostname);
    
    // 지속성 시뮬레이션
    FILE *f = fopen(persistence_path, "w");
    if (f) {
        fprintf(f, "#!/bin/bash\necho persistent\n");
        fclose(f);
    }
    
    // 정보 수집 시뮬레이션
    system("whoami");
    system("id");
    system("uname -a");
    
    return 0;
}
CODE

# 컴파일
gcc -o /tmp/test_sample /tmp/test_sample.c 2>/dev/null

echo "=== 1. file 명령 ==="
file /tmp/test_sample

echo ""
echo "=== 2. sha256sum (해시) ==="
sha256sum /tmp/test_sample

echo ""
echo "=== 3. strings (문자열 추출) ==="
echo "--- 주요 문자열 ---"
strings /tmp/test_sample | grep -iE "http|evil|password|shell|exec|system|tmp|hidden|beacon|agent|whoami|uname"

echo ""
echo "=== 4. strings 길이 제한 (8자 이상) ==="
strings -n 8 /tmp/test_sample | head -30

echo ""
echo "=== 5. hexdump (ELF 헤더) ==="
hexdump -C /tmp/test_sample | head -5

echo ""
echo "=== 6. readelf (ELF 정보) ==="
readelf -h /tmp/test_sample 2>/dev/null | head -15

echo ""
echo "=== 7. 임포트 함수 (동적 심볼) ==="
readelf -d /tmp/test_sample 2>/dev/null | grep NEEDED
nm -D /tmp/test_sample 2>/dev/null | grep " U " | head -15
```

> **결과 해석**:
> - strings에서 C2 URL, 명령어 문자열이 보이면 악성코드의 기능을 추정할 수 있다
> - 임포트 함수에 system(), exec(), socket() 등이 있으면 명령 실행/네트워크 기능 보유
> - ELF 헤더에서 stripped 여부로 분석 난이도를 판단
>
> **명령어 해설**:
> - `file`: 파일 유형 식별 (ELF, PE, script 등)
> - `strings -n 8`: 8자 이상 문자열만 추출 (노이즈 감소)
> - `readelf -d`: 동적 링킹 정보 (사용하는 라이브러리)
> - `nm -D`: 동적 심볼 테이블 (임포트/익스포트 함수)

## 2.2 고급 정적 분석

```bash
echo "=== 8. objdump (디스어셈블리) ==="
objdump -d /tmp/test_sample 2>/dev/null | grep -A5 "<main>" | head -30

echo ""
echo "=== 9. 섹션 분석 ==="
readelf -S /tmp/test_sample 2>/dev/null | head -20

echo ""
echo "=== 10. 엔트로피 분석 (패킹 탐지) ==="
cat << 'PYCODE' > /tmp/entropy_check.py
#!/usr/bin/env python3
import math
import sys

def entropy(data):
    if not data:
        return 0
    counter = {}
    for byte in data:
        counter[byte] = counter.get(byte, 0) + 1
    length = len(data)
    return -sum((c/length) * math.log2(c/length) for c in counter.values())

with open('/tmp/test_sample', 'rb') as f:
    data = f.read()

ent = entropy(data)
print(f"파일 크기: {len(data):,} bytes")
print(f"전체 엔트로피: {ent:.4f} / 8.0")

if ent > 7.5:
    print("[경고] 매우 높은 엔트로피 → 암호화/패킹 의심")
elif ent > 6.5:
    print("[주의] 높은 엔트로피 → 압축 또는 일부 난독화")
else:
    print("[정상] 일반적인 실행파일 엔트로피")

# 섹션별 엔트로피
chunk_size = len(data) // 10
for i in range(min(10, len(data) // chunk_size)):
    chunk = data[i*chunk_size:(i+1)*chunk_size]
    e = entropy(chunk)
    bar = '#' * int(e * 5)
    print(f"  블록 {i}: {e:.2f} {bar}")
PYCODE
python3 /tmp/entropy_check.py
```

> **배우는 것**: 엔트로피가 7.5 이상이면 패킹/암호화된 악성코드일 가능성이 높다. 정상 실행파일은 보통 5.0-6.5 범위다.

---

# Part 3: 동적 분석 + strace 실습 (50분)

## 3.1 strace를 이용한 시스콜 추적

> **실습 목적**: strace로 프로그램의 시스템 콜을 추적하여 악성코드의 행위를 분석한다.
>
> **배우는 것**: strace 옵션, 시스콜 유형별 해석, 의심 행위 식별

```bash
# strace로 테스트 샘플 분석
echo "=== strace 기본 실행 ==="
strace -f -o /tmp/strace_output.txt /tmp/test_sample 2>/dev/null

echo ""
echo "--- 파일 접근 시스콜 ---"
grep -E "^[0-9]+ +open|openat|creat|unlink|rename|chmod" /tmp/strace_output.txt 2>/dev/null | head -15

echo ""
echo "--- 네트워크 시스콜 ---"
grep -E "^[0-9]+ +socket|connect|bind|listen|sendto|recvfrom" /tmp/strace_output.txt 2>/dev/null | head -10

echo ""
echo "--- 프로세스 시스콜 ---"
grep -E "^[0-9]+ +execve|fork|clone|kill" /tmp/strace_output.txt 2>/dev/null | head -10

echo ""
echo "--- 시스콜 통계 ==="
strace -c /tmp/test_sample 2>&1 | tail -20
```

> **결과 해석**:
> - `openat("/tmp/.hidden_service", O_WRONLY|O_CREAT)`: 숨겨진 파일 생성 → 지속성 확보
> - `execve("whoami")`: 시스템 정보 수집 → 정찰 활동
> - `connect(...)`: 네트워크 연결 → C2 통신
>
> **명령어 해설**:
> - `strace -f`: 자식 프로세스도 추적
> - `strace -o`: 결과를 파일로 저장
> - `strace -c`: 시스콜 통계 요약
> - `strace -e trace=network`: 네트워크 시스콜만 추적

## 3.2 ltrace를 이용한 라이브러리 호출 추적

```bash
# ltrace로 라이브러리 함수 호출 추적
echo "=== ltrace 실행 ==="
ltrace -o /tmp/ltrace_output.txt /tmp/test_sample 2>/dev/null

echo ""
echo "--- 주요 라이브러리 호출 ---"
cat /tmp/ltrace_output.txt 2>/dev/null | head -30

echo ""
echo "--- system() 호출 ---"
grep "system(" /tmp/ltrace_output.txt 2>/dev/null

echo ""
echo "--- fopen/fwrite 호출 ---"
grep -E "fopen|fwrite|fclose" /tmp/ltrace_output.txt 2>/dev/null
```

> **배우는 것**: ltrace는 strace와 달리 glibc 수준의 함수 호출을 보여준다. system(), popen(), exec() 등 위험 함수의 인자를 확인할 수 있다.

## 3.3 네트워크 행위 분석

```bash
cat << 'SCRIPT' > /tmp/analyze_network_behavior.py
#!/usr/bin/env python3
"""악성코드 네트워크 행위 분석"""

# strace에서 추출한 네트워크 시스콜 시뮬레이션
network_calls = [
    {"syscall": "socket", "args": "AF_INET, SOCK_STREAM, 0", "result": "fd=3"},
    {"syscall": "connect", "args": "fd=3, {sa_family=AF_INET, sin_port=4444, sin_addr='203.0.113.50'}", "result": "0"},
    {"syscall": "sendto", "args": "fd=3, 'POST /beacon HTTP/1.1\\r\\n...', 256", "result": "256"},
    {"syscall": "recvfrom", "args": "fd=3, 'HTTP/1.1 200 OK\\r\\n{\"cmd\":\"id\"}', 1024", "result": "45"},
    {"syscall": "sendto", "args": "fd=3, 'uid=0(root) gid=0(root)', 32", "result": "32"},
]

print("=" * 60)
print("  네트워크 행위 분석 결과")
print("=" * 60)

for call in network_calls:
    print(f"\n  {call['syscall']}({call['args'][:60]})")
    print(f"  → 반환값: {call['result']}")

print("\n=== 분석 결론 ===")
print("  1. C2 서버: 203.0.113.50:4444")
print("  2. 프로토콜: HTTP POST (비콘)")
print("  3. 명령 수신: JSON 형식 ({\"cmd\":\"...\"})")
print("  4. 결과 전송: 명령 실행 결과를 C2로 전달")
print("  5. ATT&CK: T1071.001 (Web Protocols)")

print("\n=== 추출된 IOC ===")
print("  IP:  203.0.113.50")
print("  Port: 4444")
print("  URI: /beacon")
print("  UA:  Mozilla/5.0 (compatible; Bot/1.0)")
SCRIPT

python3 /tmp/analyze_network_behavior.py
```

## 3.4 파일 시스템 행위 분석

```bash
# inotifywait로 파일 시스템 변경 모니터링
echo "=== 파일 시스템 모니터링 ==="

# inotifywait가 있는 경우
if command -v inotifywait &>/dev/null; then
    echo "inotifywait로 /tmp 모니터링 (5초)..."
    timeout 5 inotifywait -m -r /tmp/ 2>/dev/null &
    WATCH_PID=$!
    sleep 1
    /tmp/test_sample 2>/dev/null
    sleep 2
    kill $WATCH_PID 2>/dev/null
else
    echo "inotifywait 미설치 - strace 기반 분석"
    echo ""
    echo "--- strace에서 파일 관련 시스콜 추출 ---"
    grep -E "openat|creat|write|unlink|rename|mkdir|chmod" /tmp/strace_output.txt 2>/dev/null | \
      grep -v "/proc\|/lib\|/usr\|/etc/ld" | head -15
fi

echo ""
echo "--- 생성된 파일 확인 ---"
ls -la /tmp/.hidden_service 2>/dev/null && echo "[발견] 숨겨진 파일 생성됨!" || echo "(숨겨진 파일 없음)"
cat /tmp/.hidden_service 2>/dev/null
rm -f /tmp/.hidden_service 2>/dev/null
```

---

# Part 4: IOC 추출 + SIEM 연동 (40분)

## 4.1 분석 결과에서 IOC 추출

```bash
cat << 'SCRIPT' > /tmp/extract_iocs.py
#!/usr/bin/env python3
"""악성코드 분석 결과에서 IOC 자동 추출"""
import re
import hashlib

# 테스트 샘플에서 추출할 IOC
sample_path = "/tmp/test_sample"

# 1. 파일 해시
with open(sample_path, 'rb') as f:
    data = f.read()
    md5 = hashlib.md5(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()

print("=" * 60)
print("  IOC 추출 결과")
print("=" * 60)

print(f"\n[파일 해시]")
print(f"  MD5:    {md5}")
print(f"  SHA256: {sha256}")

# 2. 문자열에서 IOC 추출
import subprocess
result = subprocess.run(['strings', sample_path], capture_output=True, text=True)
strings_output = result.stdout

# IP 주소 추출
ips = set(re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', strings_output))
print(f"\n[IP 주소] ({len(ips)}개)")
for ip in sorted(ips):
    # 내부 IP 필터링
    if not ip.startswith(('10.', '172.', '192.168.', '127.', '0.')):
        print(f"  {ip}")

# URL 추출
urls = set(re.findall(r'https?://[^\s"\'<>]+', strings_output))
print(f"\n[URL] ({len(urls)}개)")
for url in sorted(urls):
    print(f"  {url}")

# 도메인 추출
domains = set(re.findall(r'[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}', strings_output))
print(f"\n[도메인] ({len(domains)}개)")
for d in sorted(domains):
    if '.' in d and not d.replace('.','').isdigit():
        print(f"  {d}")

# 파일 경로 추출
paths = set(re.findall(r'/(?:tmp|var|etc|home|dev|opt)/[^\s"\']+', strings_output))
print(f"\n[파일 경로] ({len(paths)}개)")
for p in sorted(paths):
    print(f"  {p}")

# User-Agent 추출
uas = re.findall(r'Mozilla/[^\n"]+', strings_output)
print(f"\n[User-Agent] ({len(uas)}개)")
for ua in uas:
    print(f"  {ua[:60]}")

# YARA 룰 자동 생성
print(f"\n=== 자동 생성 YARA 룰 ===")
print(f"""rule Sample_{sha256[:8]}
{{
    meta:
        hash = "{sha256}"
        date = "2026-04-04"
    strings:
        $url = "evil.example.com" nocase
        $ua = "Bot/1.0"
        $path = "/tmp/.hidden"
        $cmd1 = "whoami"
        $cmd2 = "uname -a"
    condition:
        uint32(0) == 0x464C457F and 3 of them
}}""")
SCRIPT

python3 /tmp/extract_iocs.py
```

> **실전 활용**: 분석 결과에서 추출한 IOC를 SIEM, 방화벽, IDS에 즉시 배포하여 동일 악성코드의 재감염을 탐지/차단한다.

## 4.2 Wazuh 룰로 변환

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,malware_analysis,">

  <!-- 분석에서 추출된 C2 통신 패턴 -->
  <rule id="100800" level="14">
    <match>evil.example.com</match>
    <description>[MAL-ANALYSIS] 알려진 C2 도메인 통신: evil.example.com</description>
    <group>malware,c2,critical_alert,</group>
  </rule>

  <!-- 분석에서 추출된 UA 패턴 -->
  <rule id="100801" level="10">
    <match>Bot/1.0</match>
    <regex>Mozilla.*compatible.*Bot</regex>
    <description>[MAL-ANALYSIS] 악성코드 User-Agent 탐지</description>
    <group>malware,suspicious_ua,</group>
  </rule>

  <!-- 분석에서 추출된 지속성 패턴 -->
  <rule id="100802" level="10">
    <if_group>syscheck</if_group>
    <match>.hidden_service</match>
    <description>[MAL-ANALYSIS] 알려진 악성코드 지속성 파일 생성</description>
    <group>malware,persistence,</group>
  </rule>

</group>
RULES

sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

## 4.3 분석 보고서 생성

```bash
cat << 'SCRIPT' > /tmp/malware_report.py
#!/usr/bin/env python3
"""악성코드 분석 보고서 생성"""
import hashlib

with open('/tmp/test_sample', 'rb') as f:
    data = f.read()

report = f"""
{'='*60}
  악성코드 분석 보고서
{'='*60}

1. 샘플 정보
   MD5:    {hashlib.md5(data).hexdigest()}
   SHA256: {hashlib.sha256(data).hexdigest()}
   크기:   {len(data):,} bytes
   유형:   ELF 64-bit LSB executable

2. 정적 분석 결과
   - C2 서버 URL: http://evil.example.com:4444/beacon
   - User-Agent: Mozilla/5.0 (compatible; Bot/1.0)
   - 지속성 경로: /tmp/.hidden_service
   - 정보 수집 명령: whoami, id, uname -a
   - 엔트로피: 정상 범위 (패킹 없음)

3. 동적 분석 결과
   - 파일 생성: /tmp/.hidden_service (셸 스크립트)
   - 명령 실행: system("whoami"), system("id"), system("uname -a")
   - 네트워크: C2 서버로 HTTP POST 비콘 전송
   - 명령 수신: JSON 형식으로 명령 수신 후 실행

4. ATT&CK 매핑
   T1071.001  Application Layer Protocol: Web
   T1059.004  Command and Scripting: Unix Shell
   T1082      System Information Discovery
   T1505.003  Server Software Component: Web Shell (variant)
   T1053.003  Scheduled Task/Job: Cron (지속성)

5. IOC
   IP:     203.0.113.50 (시뮬레이션)
   Domain: evil.example.com
   URL:    http://evil.example.com:4444/beacon
   File:   /tmp/.hidden_service
   UA:     Mozilla/5.0 (compatible; Bot/1.0)

6. 권고 사항
   - 방화벽: evil.example.com 및 203.0.113.50 차단
   - SIEM: 추출된 IOC 기반 탐지 룰 배포 완료
   - 서버: /tmp/.hidden_service 파일 존재 여부 점검
   - 네트워크: User-Agent "Bot/1.0" 포함 HTTP 트래픽 모니터링
"""

print(report)
SCRIPT

python3 /tmp/malware_report.py

# 정리
rm -f /tmp/test_sample /tmp/test_sample.c /tmp/strace_output.txt \
      /tmp/ltrace_output.txt 2>/dev/null
```

---

## 체크리스트

- [ ] 악성코드의 주요 유형 10가지를 나열할 수 있다
- [ ] 정적/동적 분석의 차이와 각각의 장단점을 설명할 수 있다
- [ ] file, strings, readelf로 기초 정적 분석을 수행할 수 있다
- [ ] 엔트로피 분석으로 패킹 여부를 판단할 수 있다
- [ ] strace로 시스콜을 추적하고 파일/네트워크/프로세스 행위를 분석할 수 있다
- [ ] ltrace로 라이브러리 함수 호출을 확인할 수 있다
- [ ] 분석 결과에서 IOC(IP, 도메인, 해시, URL, 파일경로)를 추출할 수 있다
- [ ] 추출된 IOC를 Wazuh 룰로 변환할 수 있다
- [ ] 악성코드 분석 보고서를 작성할 수 있다
- [ ] 안전한 분석 환경 구성 원칙을 알고 있다

---

## 복습 퀴즈

**Q1.** 정적 분석과 동적 분석의 차이를 설명하시오.

<details><summary>정답</summary>
정적 분석은 악성코드를 실행하지 않고 파일 자체를 분석(strings, 디스어셈블리 등). 동적 분석은 격리 환경에서 실행하며 행위를 관찰(strace, 네트워크 모니터링 등). 정적은 안전하지만 난독화에 약하고, 동적은 실제 행위를 보지만 환경 의존적이다.
</details>

**Q2.** strings 명령으로 악성코드에서 무엇을 찾을 수 있는가?

<details><summary>정답</summary>
C2 서버 URL/IP, 파일 경로, 사용자 에이전트 문자열, 암호화 키, 에러 메시지, 레지스트리 키, 명령어 문자열 등을 찾을 수 있다. 난독화/패킹된 바이너리에서는 유용한 문자열이 거의 나오지 않는다.
</details>

**Q3.** 엔트로피가 7.8인 실행파일의 의미는?

<details><summary>정답</summary>
매우 높은 엔트로피로, 파일이 압축되거나 암호화(패킹)되어 있을 가능성이 높다. 정상 실행파일은 보통 5.0-6.5 범위이다. UPX 등의 패커로 처리된 악성코드일 수 있다.
</details>

**Q4.** strace -f 옵션의 역할은?

<details><summary>정답</summary>
fork/clone으로 생성된 자식 프로세스도 함께 추적한다. 악성코드가 자식 프로세스를 생성하여 실제 악성 행위를 수행하는 경우 이 옵션 없이는 핵심 행위를 놓칠 수 있다.
</details>

**Q5.** 악성코드가 system("whoami")를 호출하는 이유는?

<details><summary>정답</summary>
정보 수집(Discovery) 단계로, 현재 실행 권한과 사용자 정보를 파악하기 위해서다. ATT&CK T1033(System Owner/User Discovery)에 해당하며, 권한 상승 여부를 결정하는 기초 정찰이다.
</details>

**Q6.** 드로퍼(Dropper)와 페이로드(Payload)의 차이는?

<details><summary>정답</summary>
드로퍼는 실제 악성코드(페이로드)를 시스템에 설치하는 1단계 파일이다. 드로퍼는 페이로드를 내부에 포함하거나 외부에서 다운로드하여 설치한 후 자체를 삭제하기도 한다. 페이로드가 실제 악성 기능을 수행한다.
</details>

**Q7.** 악성코드 분석 시 네트워크를 차단해야 하는 이유는?

<details><summary>정답</summary>
1) C2 서버로의 실제 연결을 막아 공격자에게 분석 사실이 알려지는 것을 방지, 2) 추가 페이로드 다운로드 차단, 3) 내부 네트워크로의 확산 방지, 4) DDoS 등 외부 공격 참여 차단.
</details>

**Q8.** 임포트 테이블에서 socket(), connect(), send()가 있으면?

<details><summary>정답</summary>
네트워크 통신 기능이 있다는 의미다. C2 통신, 데이터 유출, 추가 페이로드 다운로드 등을 수행할 수 있다. 동적 분석에서 실제 연결 대상과 전송 데이터를 확인해야 한다.
</details>

**Q9.** 분석에서 추출한 IOC를 SIEM에 배포하는 이유는?

<details><summary>정답</summary>
동일한 악성코드가 다른 시스템에 감염되었거나 향후 감염될 경우 즉시 탐지하기 위해서다. C2 IP/도메인을 방화벽에, 파일 해시를 FIM에, 행위 패턴을 SIEM 룰에 반영한다.
</details>

**Q10.** /tmp/.hidden_service 파일이 발견되면 어떤 ATT&CK 기법인가?

<details><summary>정답</summary>
T1564.001(Hidden Files and Directories) - 점(.) 접두사로 파일을 숨기는 기법과, T1053.003(Cron) 또는 T1543.002(Systemd Service) - 지속성 확보 기법에 해당한다.
</details>

---

## 과제

### 과제 1: 악성코드 정적+동적 분석 보고서 (필수)

교육용 테스트 샘플(또는 자체 작성 샘플)에 대해:
1. 기초 정적 분석 (file, strings, 해시, 엔트로피)
2. 동적 분석 (strace 시스콜 분석)
3. IOC 추출 (IP, 도메인, 해시, 파일경로, UA)
4. ATT&CK 매핑
5. Wazuh 탐지 룰 1개 이상 작성

### 과제 2: YARA 룰 작성 (선택)

분석 결과를 기반으로:
1. 해당 악성코드를 탐지하는 YARA 룰 작성
2. 양성/음성 테스트 샘플로 검증
3. Wazuh FIM + YARA 연동 설정

---

## 보충: 악성코드 분석 고급 기법

### Sandbox 환경 구성 가이드

```bash
cat << 'SCRIPT' > /tmp/sandbox_guide.py
#!/usr/bin/env python3
"""악성코드 분석 Sandbox 구성 가이드"""

print("""
================================================================
  악성코드 분석 Sandbox 구성 가이드
================================================================

1. VM 기반 Sandbox (권장)

   [호스트 시스템]
        |
   [VirtualBox/KVM]
        |
   +----+----+
   |         |
   [분석 VM]  [네트워크 시뮬레이터]
   Ubuntu 22.04   inetsim/fakenet
   YARA, strings  DNS/HTTP/SMTP 가짜 서버
   strace, ltrace
   Ghidra

   네트워크 설정:
   - NAT 모드 (인터넷 차단)
   - Host-Only + inetsim (가짜 응답)

2. Docker 기반 (간단한 분석용)

   docker run --rm --network none \\
     -v /samples:/samples:ro \\
     remnux/remnux-distro \\
     strings /samples/malware.bin

3. 클라우드 Sandbox 서비스
   - VirusTotal (무료, 해시 업로드)
   - Any.Run (무료 tier, 인터랙티브)
   - Hybrid Analysis (무료, 자동 분석)
   - Joe Sandbox (상용, 상세 분석)

4. REMnux 배포판 (추천)
   - 악성코드 분석 전용 Linux 배포판
   - 도구 100+ 사전 설치
   - https://remnux.org/
""")

# 분석 도구 체크리스트
tools = [
    ("file", "파일 유형 식별", "file sample.bin"),
    ("strings", "문자열 추출", "strings -n 8 sample.bin"),
    ("sha256sum", "해시 계산", "sha256sum sample.bin"),
    ("readelf", "ELF 분석", "readelf -a sample.bin"),
    ("objdump", "디스어셈블리", "objdump -d sample.bin"),
    ("strace", "시스콜 추적", "strace -f -o log.txt ./sample.bin"),
    ("ltrace", "라이브러리 추적", "ltrace -o log.txt ./sample.bin"),
    ("yara", "패턴 매칭", "yara rules.yar sample.bin"),
    ("hexdump", "헥스 뷰어", "hexdump -C sample.bin | head"),
    ("upx", "패킹 해제", "upx -d sample.bin"),
    ("gdb", "디버거", "gdb ./sample.bin"),
    ("Ghidra", "디컴파일러", "ghidraRun (GUI)"),
]

print("\n=== 분석 도구 체크리스트 ===")
print(f"{'도구':12s} {'용도':20s} {'명령 예시':40s}")
print("-" * 75)
for tool, purpose, cmd in tools:
    print(f"{tool:12s} {purpose:20s} {cmd:40s}")
SCRIPT

python3 /tmp/sandbox_guide.py
```

### 패킹/난독화 탐지 기법

```bash
cat << 'SCRIPT' > /tmp/packing_detection.py
#!/usr/bin/env python3
"""패킹/난독화 탐지 기법"""
import math
import os

def file_entropy(filepath):
    """파일 엔트로피 계산"""
    with open(filepath, 'rb') as f:
        data = f.read()
    if not data:
        return 0
    counter = {}
    for byte in data:
        counter[byte] = counter.get(byte, 0) + 1
    length = len(data)
    return -sum((c/length) * math.log2(c/length) for c in counter.values())

def section_entropy(filepath, num_sections=8):
    """섹션별 엔트로피 분석"""
    with open(filepath, 'rb') as f:
        data = f.read()
    chunk_size = max(len(data) // num_sections, 1)
    results = []
    for i in range(num_sections):
        chunk = data[i*chunk_size:(i+1)*chunk_size]
        if chunk:
            results.append(file_entropy_data(chunk))
    return results

def file_entropy_data(data):
    if not data:
        return 0
    counter = {}
    for byte in data:
        counter[byte] = counter.get(byte, 0) + 1
    length = len(data)
    return -sum((c/length) * math.log2(c/length) for c in counter.values())

# 분석 대상
targets = {
    "/tmp/test_sample": "교육용 샘플",
    "/bin/ls": "시스템 바이너리 (정상)",
    "/bin/bash": "Bash 셸 (정상)",
}

print("=" * 60)
print("  패킹/난독화 탐지 - 엔트로피 분석")
print("=" * 60)

for filepath, desc in targets.items():
    if not os.path.exists(filepath):
        continue
    
    ent = file_entropy(filepath)
    size = os.path.getsize(filepath)
    
    # 판정
    if ent > 7.5:
        verdict = "[경고] 암호화/패킹 가능성 매우 높음"
    elif ent > 6.8:
        verdict = "[주의] 패킹 또는 압축 가능"
    elif ent > 5.0:
        verdict = "[정상] 일반 실행파일 범위"
    else:
        verdict = "[정상] 낮은 엔트로피"
    
    print(f"\n  {filepath} ({desc})")
    print(f"    크기: {size:,} bytes")
    print(f"    엔트로피: {ent:.4f} / 8.0")
    print(f"    판정: {verdict}")
    
    # 시각화
    bar_len = int(ent * 6)
    bar = "#" * bar_len + "." * (48 - bar_len)
    print(f"    [{bar}] {ent:.2f}")

print("""
=== 패킹 탐지 추가 지표 ===
  1. 섹션 이름 이상: UPX0, .packed, .crypted
  2. 임포트 테이블이 비정상적으로 작음 (5개 미만)
  3. 엔트리포인트가 마지막 섹션에 위치
  4. 섹션 크기 불일치 (raw size << virtual size)
  5. 문자열이 거의 추출되지 않음
""")
SCRIPT

python3 /tmp/packing_detection.py
```

### 스크립트 기반 악성코드 분석

```bash
# 스크립트 악성코드 분석 (Python, Bash, PowerShell)
cat << 'SCRIPT' > /tmp/script_malware_analysis.py
#!/usr/bin/env python3
"""스크립트 악성코드 분석 기법"""

print("=" * 60)
print("  스크립트 악성코드 분석 기법")
print("=" * 60)

script_types = {
    "Python 악성코드": {
        "특징": [
            "import socket, subprocess, os",
            "base64.b64decode() 사용 (난독화)",
            "exec(), eval() 사용 (동적 실행)",
            "os.system(), subprocess.Popen()",
            "urllib/requests로 C2 통신",
        ],
        "분석법": "1) 문자열 추출 2) import 분석 3) base64 디코딩 4) 실행 흐름 추적",
        "도구": "strings, python3 -c (디코딩), strace",
    },
    "Bash 악성코드": {
        "특징": [
            "curl/wget으로 페이로드 다운로드",
            "eval $(base64 -d <<< 'encoded')",
            "/dev/tcp/ 리버스 셸",
            "crontab에 지속성 등록",
            "history 삭제, unset HISTFILE",
        ],
        "분석법": "1) cat으로 내용 확인 2) base64 디코딩 3) 변수 추적 4) 실행 경로 확인",
        "도구": "cat, base64 -d, bash -x (디버그 모드)",
    },
    "PHP 웹셸": {
        "특징": [
            "eval($_GET/POST/REQUEST)",
            "system(), exec(), passthru()",
            "base64_decode() 난독화",
            "preg_replace('/e', ...) 실행",
            "assert() 동적 실행",
        ],
        "분석법": "1) grep 위험 함수 2) 난독화 해제 3) 입력 변수 추적 4) 실행 결과 확인",
        "도구": "strings, php -r (디코딩), YARA",
    },
}

for script_type, info in script_types.items():
    print(f"\n  --- {script_type} ---")
    print(f"  특징:")
    for feat in info["특징"]:
        print(f"    - {feat}")
    print(f"  분석법: {info['분석법']}")
    print(f"  도구: {info['도구']}")
SCRIPT

python3 /tmp/script_malware_analysis.py
```

### VirusTotal API 연동

```bash
cat << 'SCRIPT' > /tmp/vt_check.py
#!/usr/bin/env python3
"""VirusTotal 해시 조회 시뮬레이션"""
import hashlib

# 시뮬레이션 (실제 API 키 필요)
print("=" * 60)
print("  VirusTotal 조회 가이드")
print("=" * 60)

print("""
# VirusTotal API v3 사용법

## 해시로 파일 조회
curl -s -H "x-apikey: YOUR_API_KEY" \\
  "https://www.virustotal.com/api/v3/files/SHA256_HASH" | \\
  python3 -c "
import sys, json
data = json.load(sys.stdin)
stats = data.get('data',{}).get('attributes',{}).get('last_analysis_stats',{})
print(f'탐지: {stats.get(\"malicious\",0)}/{sum(stats.values())}')
print(f'이름: {data[\"data\"][\"attributes\"].get(\"meaningful_name\",\"?\")}')" 

## IP 주소 평판 조회
curl -s -H "x-apikey: YOUR_API_KEY" \\
  "https://www.virustotal.com/api/v3/ip_addresses/203.0.113.50"

## 도메인 조회
curl -s -H "x-apikey: YOUR_API_KEY" \\
  "https://www.virustotal.com/api/v3/domains/evil.example.com"

## 파일 업로드 (주의: 파일이 공개됨)
curl -s -H "x-apikey: YOUR_API_KEY" \\
  -F "file=@sample.bin" \\
  "https://www.virustotal.com/api/v3/files"

주의사항:
  - 무료 API: 분당 4회 제한
  - 업로드된 파일은 전체 공개됨 (민감 파일 업로드 금지)
  - 해시 조회만으로 파일 내용 노출 없이 확인 가능
""")

# 테스트 샘플 해시
if __import__('os').path.exists('/tmp/test_sample'):
    with open('/tmp/test_sample', 'rb') as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"\n교육용 샘플 SHA256: {sha256}")
    print(f"VT 조회 URL: https://www.virustotal.com/gui/file/{sha256}")
SCRIPT

python3 /tmp/vt_check.py
```

### 악성코드 분류 체계

```bash
cat << 'SCRIPT' > /tmp/malware_classification.py
#!/usr/bin/env python3
"""악성코드 분류 체계 + 행위 분석 프레임워크"""

behaviors = {
    "파일 시스템": {
        "indicators": [
            "임시 디렉토리에 파일 생성 (/tmp, /dev/shm)",
            "숨김 파일 생성 (.으로 시작)",
            "시스템 파일 수정 (/etc/passwd, /etc/crontab)",
            "자기 자신 삭제",
            "파일 암호화 (랜섬웨어)",
        ],
        "syscalls": ["openat", "creat", "unlink", "rename", "chmod"],
    },
    "네트워크": {
        "indicators": [
            "외부 IP로 연결 (C2 통신)",
            "DNS 쿼리 (도메인 해석)",
            "HTTP POST (데이터 전송)",
            "비표준 포트 사용",
            "암호화 통신 (TLS)",
        ],
        "syscalls": ["socket", "connect", "sendto", "recvfrom", "bind"],
    },
    "프로세스": {
        "indicators": [
            "자식 프로세스 생성 (fork/clone)",
            "다른 프로그램 실행 (execve)",
            "프로세스 인젝션 (ptrace)",
            "시그널 조작 (kill, sigaction)",
            "데몬화 (setsid, daemon)",
        ],
        "syscalls": ["clone", "execve", "ptrace", "kill", "setsid"],
    },
    "정보 수집": {
        "indicators": [
            "시스템 정보 조회 (uname, hostname)",
            "사용자 정보 (whoami, id)",
            "네트워크 정보 (ifconfig, ip)",
            "디스크 정보 (df, lsblk)",
            "프로세스 목록 (ps)",
        ],
        "syscalls": ["uname", "getuid", "gethostname"],
    },
}

print("=" * 60)
print("  악성코드 행위 분석 프레임워크")
print("=" * 60)

for category, info in behaviors.items():
    print(f"\n  [{category}]")
    print(f"    행위 지표:")
    for ind in info["indicators"]:
        print(f"      - {ind}")
    print(f"    관련 시스콜: {', '.join(info['syscalls'])}")
SCRIPT

python3 /tmp/malware_classification.py
```

---

## 다음 주 예고

**Week 10: SOAR 자동화**에서는 플레이북 기반 자동 대응을 설계하고, API 연동과 Wazuh Active Response를 활용한 SOC 자동화를 구현한다.
