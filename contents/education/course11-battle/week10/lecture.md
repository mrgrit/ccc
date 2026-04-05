# Week 10: 공방전 준비 -- 인프라 하드닝

## 학습 목표
- 인프라 하드닝(Hardening)의 개념과 CIS Benchmark 기반의 체계적 보안 강화 방법을 이해한다
- 불필요한 서비스와 포트를 식별하고 안전하게 제거/비활성화할 수 있다
- 운영체제, 웹 서비스, SSH 등 주요 서비스별 보안 설정을 적용할 수 있다
- 커널 보안 파라미터(sysctl)를 조정하여 네트워크 수준 방어를 강화할 수 있다
- 패치 관리 전략을 수립하고 보안 업데이트를 체계적으로 적용할 수 있다
- 백업 전략을 수립하고 복원 테스트를 수행하여 데이터 보호를 보장할 수 있다
- 공방전 Blue Team을 위한 종합 방어 체크리스트를 작성하고 활용할 수 있다

## 전제 조건
- 리눅스 시스템 관리 기본 (systemctl, apt, 파일 권한)
- nftables 방화벽 설정 경험 (Week 05~06)
- SSH 접속 및 서비스 관리 이해
- Week 09 인시던트 대응 프레임워크 복습 완료

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 하드닝 이론 + CIS Benchmark | 강의 |
| 0:40-1:10 | 패치 관리 + 백업 전략 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 서비스 제거 + SSH 하드닝 실습 | 실습 |
| 2:00-2:30 | 커널 보안 + 웹 서버 하드닝 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 백업/복원 + 방어 체크리스트 실습 | 실습 |
| 3:10-3:40 | 종합 점검 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 하드닝 이론과 CIS Benchmark (40분)

## 1.1 인프라 하드닝이란?

인프라 하드닝은 시스템의 공격 표면(Attack Surface)을 줄이고 보안 수준을 높이기 위해 불필요한 기능을 제거하고 보안 설정을 강화하는 과정이다. 공방전에서 Blue Team이 방어를 준비하는 핵심 단계이며, "방어는 공격보다 앞서야 한다"는 원칙의 실현이다.

**MITRE ATT&CK 방어 매핑:**
```
하드닝으로 차단하는 주요 공격 기법:
  +-- T1190 Exploit Public App  → 패치 적용, 불필요 서비스 제거
  +-- T1110 Brute Force         → SSH 강화, 계정 잠금 정책
  +-- T1059 Command Interpreter → 셸 접근 제한, 실행 권한 관리
  +-- T1053 Scheduled Task      → cron 접근 제어, 무결성 모니터링
  +-- T1548 Abuse Elevation     → SUID 정리, sudo 제한
  +-- T1078 Valid Accounts      → 비밀번호 정책, MFA
  +-- T1021 Remote Services     → 불필요 원격 서비스 비활성화
```

### 하드닝의 5대 원칙

| 원칙 | 설명 | 예시 |
|------|------|------|
| **최소 권한** | 필요한 최소한의 권한만 부여 | 웹 서버는 root로 실행하지 않음 |
| **최소 서비스** | 필요한 서비스만 실행 | 사용하지 않는 FTP, Telnet 제거 |
| **심층 방어** | 여러 계층에서 보안 적용 | 방화벽 + IDS + 호스트 보안 + 앱 보안 |
| **기본 거부** | 명시적으로 허용한 것만 통과 | 방화벽 기본 정책: DROP |
| **최신 상태 유지** | 보안 패치 즉시 적용 | CVE 공개 후 72시간 내 패치 |

### 공격 표면 감소 모델

```
[하드닝 전]
+--------------------------------------+
| 공격 표면                              |
| +----+ +----+ +----+ +----+ +----+ |
| |SSH | |HTTP| |FTP | |SMTP| |SNMP| |
| |:22 | |:80 | |:21 | |:25 | |:161| |
| +----+ +----+ +----+ +----+ +----+ |
| +----+ +----+ +----+                |
| |MySQL| |NFS | |X11 |                |
| |:3306| |:2049| |:6000|               |
| +----+ +----+ +----+                |
| 열린 포트: 8개, 공격 벡터: 다수        |
+--------------------------------------+

[하드닝 후]
+--------------------------------------+
| 공격 표면 (최소화)                     |
| +----+ +----+                        |
| |SSH | |HTTP|                        |
| |:22 | |:80 |  (나머지 모두 제거/차단) |
| |키인증| |WAF |                        |
| +----+ +----+                        |
| 열린 포트: 2개, 추가 보안 적용          |
+--------------------------------------+
```

## 1.2 CIS Benchmark 개요

CIS(Center for Internet Security) Benchmark는 운영체제, 서비스, 네트워크 장비 등에 대한 보안 설정 기준이다. 전 세계적으로 인정받는 보안 하드닝 표준으로, 감사(Audit)와 규정 준수(Compliance)의 기준이 된다.

### CIS Ubuntu Linux Benchmark 주요 항목

| 섹션 | 항목 | 중요도 | 내용 |
|------|------|--------|------|
| 1 | 초기 설정 | 높음 | 파일시스템 마운트 옵션, 부팅 보안 |
| 2 | 서비스 | 높음 | 불필요 서비스 비활성화 |
| 3 | 네트워크 | 높음 | 커널 네트워크 파라미터 |
| 4 | 방화벽 | 높음 | nftables/ufw 설정 |
| 5 | 접근 제어 | 높음 | SSH, PAM, sudo 설정 |
| 6 | 로깅/감사 | 중간 | auditd, syslog 설정 |
| 7 | 시스템 유지 | 중간 | 파일 권한, SUID 정리 |

### CIS Level 1 vs Level 2

| 레벨 | 특징 | 서비스 영향 | 공방전 적용 |
|------|------|-----------|-----------|
| **Level 1** | 기본 보안, 서비스 영향 최소 | 낮음 | 반드시 적용 |
| **Level 2** | 심층 보안, 성능/편의성 영향 가능 | 중간 | 선택적 적용 |

## 1.3 서비스 분류와 제거 전략

### 서비스 위험도 분류

| 위험도 | 서비스 | 이유 | 조치 |
|--------|--------|------|------|
| **Critical** | telnet, rsh, rlogin | 평문 전송, 인증 없음 | 즉시 제거 |
| **High** | FTP (vsftpd, proftpd) | 평문 인증 | SFTP로 대체 |
| **High** | SNMP v1/v2c | 커뮤니티 문자열 노출 | v3로 업그레이드 또는 제거 |
| **Medium** | NFS, RPC | 인증 미흡 | 불필요 시 제거 |
| **Medium** | X11 Forwarding | GUI 터널링, 정보 노출 | SSH에서 비활성화 |
| **Low** | CUPS (인쇄 서비스) | 불필요 공격 표면 | 서버 환경에서 제거 |
| **Low** | avahi-daemon | mDNS 정보 노출 | 비활성화 |

### 서비스 제거 의사결정 프로세스

```
서비스 발견
    |
    +-- 업무에 필수인가? --(예)--> 보안 강화 (설정 하드닝)
    |                                |
    |                                +-- 최신 패치 적용
    |                                +-- 접근 제어 (IP 제한)
    |                                +-- 강한 인증 설정
    |                                +-- 모니터링 추가
    |
    +-- 업무에 필수인가? --(아니오)--> 비활성화/제거
                                        |
                                        +-- systemctl stop + disable
                                        +-- apt remove (선택)
                                        +-- 방화벽에서 포트 차단
```

## 1.4 패치 관리 전략

### 패치 우선순위 매트릭스

```
           | 높은 CVSS (7.0+)    | 낮은 CVSS (<7.0)
-----------┼---------------------┼---------------------
외부 노출   | P1: 즉시 적용        | P2: 48시간 내
서비스     | (24시간 내)          |
-----------┼---------------------┼---------------------
내부 전용   | P2: 48시간 내        | P3: 다음 정기 패치
서비스     |                     | (1주 내)
-----------┼---------------------┼---------------------
비운영     | P3: 1주 내           | P4: 다음 월간 패치
시스템     |                     |
```

### 패치 적용 절차

| 단계 | 활동 | 목적 |
|------|------|------|
| 1 | 취약점 스캔/공지 확인 | 패치 필요 항목 식별 |
| 2 | 영향 분석 | 패치 적용 시 서비스 영향 평가 |
| 3 | 백업 | 롤백 준비 |
| 4 | 테스트 환경 적용 | 호환성 검증 |
| 5 | 운영 환경 적용 | 유지보수 창에서 수행 |
| 6 | 검증 | 서비스 정상 동작 확인 |
| 7 | 문서화 | 적용 이력 기록 |

## 1.5 백업 전략

### 3-2-1 백업 원칙

```
+-------------------------------------+
|          3-2-1 백업 원칙              |
|                                       |
|  3 — 데이터 사본 3개 유지              |
|     (원본 1 + 백업 2)                 |
|                                       |
|  2 — 2가지 다른 매체에 저장            |
|     (로컬 디스크 + 외부 스토리지)       |
|                                       |
|  1 — 1개는 오프사이트(원격지) 보관     |
|     (다른 물리적 위치)                 |
+-------------------------------------+
```

### 백업 유형 비교

| 유형 | 설명 | 장점 | 단점 | RPO |
|------|------|------|------|-----|
| **풀 백업** | 전체 데이터 복사 | 복원 간단 | 시간/공간 많이 소요 | 백업 시점 |
| **증분 백업** | 마지막 백업 이후 변경분만 | 빠르고 작음 | 복원 시 체인 필요 | 마지막 증분 |
| **차등 백업** | 마지막 풀 백업 이후 변경분 | 복원 비교적 간단 | 시간 경과 시 증가 | 마지막 차등 |
| **스냅샷** | 파일시스템 시점 이미지 | 즉시 생성 | 같은 디스크 사용 | 스냅샷 시점 |

---

# Part 2: 패치 관리 + 백업 전략 상세 (30분)

## 2.1 Ubuntu/Debian 보안 업데이트 관리

### 패치 관리 명령어 체계

| 명령어 | 용도 | 위험도 | 소요 시간 |
|--------|------|--------|---------|
| `apt update` | 패키지 목록 갱신 | 없음 | 10초 |
| `apt list --upgradable` | 업데이트 가능 패키지 확인 | 없음 | 즉시 |
| `apt upgrade` | 일반 업그레이드 | 낮음 | 1~5분 |
| `apt dist-upgrade` | 의존성 해결 포함 업그레이드 | 중간 | 2~10분 |
| `unattended-upgrades` | 자동 보안 패치 | 낮음 (보안만) | 자동 |
| `apt install --only-upgrade <pkg>` | 특정 패키지만 업그레이드 | 낮음 | 즉시 |

### 자동 보안 업데이트 설정

```
[unattended-upgrades 동작 흐름]

매일 자동 실행 (apt daily timer)
    |
    +-- apt update (패키지 목록 갱신)
    |
    +-- 보안 업데이트만 필터링
    |   (Ubuntu-security 소스만)
    |
    +-- 자동 설치
    |
    +-- 재부팅 필요 시 알림
    |   (/var/run/reboot-required)
    |
    +-- 로그 기록
        (/var/log/unattended-upgrades/)
```

### 보안 패치 롤백 전략

| 상황 | 방법 | 명령어 |
|------|------|--------|
| 패키지 다운그레이드 | 이전 버전 설치 | `apt install <pkg>=<version>` |
| 설정 복원 | 백업에서 복원 | `cp backup/config /etc/config` |
| 전체 롤백 | 스냅샷 복원 | `lvcreate --snapshot` → `lvconvert --merge` |

## 2.2 방어 체크리스트 설계

### 공방전 Blue Team 방어 체크리스트 구조

| 카테고리 | 항목 수 | 우선순위 | 목표 |
|---------|--------|---------|------|
| 네트워크 | 8 | 1순위 (0~5분) | 방화벽, 포트 정리 |
| 계정/인증 | 7 | 1순위 (0~5분) | SSH, 비밀번호, 키 |
| 서비스 | 6 | 2순위 (5~15분) | 불필요 서비스 제거 |
| 커널/OS | 5 | 2순위 (5~15분) | sysctl, 파일 권한 |
| 웹 서버 | 5 | 2순위 (10~20분) | Apache/Nginx 하드닝 |
| 모니터링 | 4 | 3순위 (15~25분) | 로그, IDS, 알림 |
| 백업 | 3 | 3순위 (20~30분) | 백업 확인, 복원 테스트 |

### 시간 제한 하의 하드닝 전략

```
[공방전 시작 후 첫 30분 하드닝 로드맵]

0~5분:   비밀번호 변경 + SSH 키 확인 + 방화벽 기본 정책
5~10분:  불필요 서비스 중지 + 불필요 포트 차단
10~15분: SSH 하드닝 + 커널 파라미터 설정
15~20분: 웹 서버 설정 점검 + 로그 백업
20~25분: 모니터링 시작 (IDS + 로그)
25~30분: 전체 상태 점검 + 기준선 스냅샷
```

---

# Part 3: 서비스 제거 + SSH 하드닝 실습 (40분)

## 실습 3.1: 불필요 서비스 식별 및 제거

### Step 1: 현재 실행 중인 서비스 조사

> **실습 목적**: 현재 시스템에서 실행 중인 모든 서비스를 식별하고 불필요한 것을 분류한다. 하드닝의 첫 번째 단계는 "무엇이 실행되고 있는지 파악하는 것"이다.
>
> **배우는 것**: systemctl을 이용한 서비스 감사, 열린 포트-서비스 매핑, 서비스 필요성 판단

```bash
# 실행 중인 서비스 전체 목록 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "systemctl list-units --type=service --state=running --no-pager 2>/dev/null"
# 예상 출력:
# UNIT                    LOAD   ACTIVE SUB     DESCRIPTION
# apache2.service         loaded active running The Apache HTTP Server
# docker.service          loaded active running Docker Application Container Engine
# ssh.service             loaded active running OpenBSD Secure Shell server
# ...

# 열린 포트와 서비스 매핑
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S ss -tlnp 2>/dev/null"
# 예상 출력:
# State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
# LISTEN 0      128    *:22                *:*              users:(("sshd",...))
# LISTEN 0      128    *:80                *:*              users:(("apache2",...))
# LISTEN 0      128    *:3000              *:*              users:(("node",...))
# LISTEN 0      128    *:8002              *:*              users:(("python",...))

# 부팅 시 자동 시작되는 서비스 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "systemctl list-unit-files --type=service --state=enabled --no-pager 2>/dev/null | head -20"

# 불필요할 가능성이 있는 서비스 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "for svc in cups avahi-daemon bluetooth rpcbind nfs-server telnet.socket ftp xinetd; do \
     systemctl is-active \$svc 2>/dev/null && echo \"실행중: \$svc\" || true; \
   done"
# 예상 출력: 실행 중인 불필요 서비스가 있다면 표시
```

> **결과 해석**:
> - 실행 중인 서비스 수가 많을수록 공격 표면이 넓다
> - 열린 포트와 서비스를 매핑하여 각 포트의 필요성을 판단한다
> - `cups`, `avahi`, `bluetooth` 등은 서버 환경에서 대부분 불필요하다
>
> **실전 활용**: 공방전 시작 전 첫 10분 안에 이 조사를 완료하고, 불필요 서비스를 비활성화해야 한다.
>
> **명령어 해설**:
> - `systemctl list-units --state=running`: 현재 실행 중인 유닛만 표시
> - `systemctl list-unit-files --state=enabled`: 부팅 시 자동 시작되는 서비스
> - `ss -tlnp`: TCP LISTEN 상태의 포트와 프로세스 표시
>
> **트러블슈팅**:
> - 서비스가 너무 많이 보이는 경우: `--type=service`로 서비스만 필터링
> - root 프로세스가 안 보이는 경우: sudo 필요 → `echo 1 | sudo -S ss -tlnp`

### Step 2: 서비스 비활성화

> **실습 목적**: 불필요한 서비스를 안전하게 중지하고 부팅 시 자동 시작을 비활성화한다.
>
> **배우는 것**: systemctl을 이용한 서비스 비활성화, 영향도 검증, mask 명령

```bash
# 불필요 서비스 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "for svc in cups avahi-daemon bluetooth rpcbind; do \
     STATUS=\$(systemctl is-active \$svc 2>/dev/null); \
     ENABLED=\$(systemctl is-enabled \$svc 2>/dev/null); \
     echo \"  \$svc: active=\$STATUS enabled=\$ENABLED\"; \
   done"
# 예상 출력:
#   cups: active=inactive enabled=disabled (또는 active=active)
#   avahi-daemon: active=inactive enabled=disabled
#   ...

# 비활성화 예시 (cups가 실행 중인 경우)
# sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
#   "echo 1 | sudo -S systemctl stop cups 2>/dev/null && \
#    echo 1 | sudo -S systemctl disable cups 2>/dev/null && \
#    echo 'cups 비활성화 완료'"

# 비활성화 전후 포트 수 비교
echo "=== 하드닝 전 열린 포트 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tln 2>/dev/null | grep LISTEN | wc -l"

# 강력한 비활성화 (mask — 재활성화 방지)
echo "=== systemctl mask 예시 ==="
echo "systemctl mask <service>  → 서비스를 /dev/null에 링크하여 시작 자체를 불가능하게 함"
echo "systemctl unmask <service> → mask 해제"
echo "mask는 disable보다 강력: 수동 시작도 차단됨"
```

> **결과 해석**:
> - `systemctl stop`: 즉시 서비스 중지 (현재 세션에만 적용)
> - `systemctl disable`: 부팅 시 자동 시작 비활성화 (영구적)
> - `systemctl mask`: 서비스를 완전히 차단 (수동 시작도 불가)
> - 두 명령(stop + disable)을 함께 사용해야 완전한 비활성화가 된다
>
> **실전 활용**: 공방전에서 서비스를 끄기 전에 영향도를 확인해야 한다. 실수로 필수 서비스를 끄면 감점될 수 있다. 확실하지 않으면 방화벽에서 포트만 차단하는 것이 안전하다.
>
> **명령어 해설**:
> - `systemctl is-active <service>`: 서비스 실행 상태 확인 (종료코드 0=실행중)
> - `systemctl stop <service>`: 서비스 즉시 중지
> - `systemctl disable <service>`: 부팅 시 자동 시작 비활성화
> - `systemctl mask <service>`: 서비스 완전 차단 (/dev/null에 심볼릭 링크)
>
> **트러블슈팅**:
> - 의존성 오류: 다른 서비스가 이 서비스에 의존 → `systemctl list-dependencies --reverse <service>`
> - 재시작해도 살아나는 서비스: socket-activated 서비스일 수 있음 → 소켓도 disable 필요

## 실습 3.2: SSH 하드닝

### Step 1: SSH 현재 설정 감사

> **실습 목적**: SSH 서비스의 현재 보안 설정을 감사하고 취약한 설정을 식별한다.
>
> **배우는 것**: sshd_config 분석, SSH 보안 기준, 설정 유효 값 확인

```bash
# SSH 현재 유효 설정 전체 확인 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S sshd -T 2>/dev/null | grep -E \
   'permitrootlogin|passwordauthentication|maxauthtries|pubkeyauthentication|x11forwarding|permitemptypasswords|logingracetime|clientaliveinterval'"
# 예상 출력:
# permitrootlogin prohibit-password
# passwordauthentication yes      ← 취약: 비밀번호 인증 허용
# maxauthtries 6                  ← 취약: 6회까지 허용 (3회 권장)
# pubkeyauthentication yes
# x11forwarding yes               ← 취약: X11 포워딩 허용
# permitemptypasswords no
# logingracetime 120              ← 120초 (30초 권장)
# clientaliveinterval 0           ← 비활성 세션 관리 없음

# SSH 버전 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ssh -V 2>&1"
# 예상 출력: OpenSSH_8.9p1 Ubuntu-3ubuntu0.6, OpenSSL 3.0.x

# SSH 인증 방법 확인 (원격에서)
echo 1 | sudo -S nmap --script=ssh-auth-methods -p 22 10.20.30.80 2>/dev/null | \
  grep -A5 "ssh-auth-methods"
# 예상 출력:
# | ssh-auth-methods:
# |   Supported authentication methods:
# |     publickey
# |_    password    ← 비밀번호 인증 활성화됨

# 취약점 요약
echo "=== SSH 취약점 요약 ==="
echo "[경고] PasswordAuthentication yes → 브루트포스 가능"
echo "[경고] MaxAuthTries 6 → 높은 시도 횟수"
echo "[경고] X11Forwarding yes → 불필요 기능 활성"
echo "[경고] LoginGraceTime 120 → 너무 긴 연결 유지"
echo "[정상] PubkeyAuthentication yes"
echo "[정상] PermitEmptyPasswords no"
```

> **결과 해석**:
> - `PasswordAuthentication yes`: 브루트포스 공격에 취약. 키 기반 인증으로 변경해야 한다
> - `PermitRootLogin prohibit-password`: root 키 인증은 허용. `no`로 변경 권장
> - `X11Forwarding yes`: 서버에서 불필요한 GUI 터널링. 비활성화해야 한다
> - `sshd -T`: 실제 적용되는 전체 설정을 출력 (파일에 명시 안 된 기본값 포함)
>
> **실전 활용**: SSH는 가장 일반적인 원격 접근 방법이므로, 하드닝의 최우선 대상이다. 공방전에서 약한 SSH 설정은 가장 먼저 공격당한다.
>
> **명령어 해설**:
> - `sshd -T`: SSH 서버의 전체 유효 설정 출력 (테스트 모드, 기본값 포함)
> - `grep -E 'pattern1|pattern2'`: 여러 패턴을 동시에 검색
>
> **트러블슈팅**:
> - `sshd -T` 실행 오류: root 권한 필요 → `sudo sshd -T`
> - 설정 파일이 여러 개인 경우: `/etc/ssh/sshd_config.d/*.conf` 디렉토리도 확인

### Step 2: SSH 보안 설정 적용

> **실습 목적**: SSH 서버의 보안 설정을 강화하여 브루트포스와 무단 접근을 방지한다.
>
> **배우는 것**: sshd_config 보안 설정, 경고 배너, 암호 스위트 제한

```bash
# SSH 보안 설정 강화 (web 서버에서 수행)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'SSHCMD'
# 현재 설정 백업
echo 1 | sudo -S cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d)
echo "설정 백업 완료: sshd_config.backup.$(date +%Y%m%d)"

# 보안 설정 확인 (적용하지 않고 확인만)
echo ""
echo "=== SSH 하드닝 권장 설정 ==="
echo "PermitRootLogin no              # root 로그인 완전 차단"
echo "MaxAuthTries 3                  # 최대 인증 시도 3회"
echo "LoginGraceTime 30               # 로그인 제한 시간 30초"
echo "X11Forwarding no                # X11 포워딩 비활성화"
echo "AllowTcpForwarding no           # TCP 포워딩 비활성화"
echo "PermitEmptyPasswords no         # 빈 비밀번호 차단"
echo "ClientAliveInterval 300         # 5분 비활성 시 체크"
echo "ClientAliveCountMax 2           # 2회 응답 없으면 연결 해제"
echo "Banner /etc/ssh/banner          # 경고 배너 표시"
echo ""
echo "=== 강한 암호 스위트 ==="
echo "Ciphers aes256-gcm@openssh.com,chacha20-poly1305@openssh.com,aes128-gcm@openssh.com"
echo "MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com"
echo "KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org"
SSHCMD

# SSH 경고 배너 생성
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S bash -c 'cat > /etc/ssh/banner << EOF
************************************************************
*  WARNING: Authorized Access Only                          *
*  All activities are monitored and recorded.               *
*  Unauthorized access is prohibited and will be prosecuted.*
************************************************************
EOF'"
echo "SSH 경고 배너 생성 완료"

# 설정 문법 검증 (적용 전 필수)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S sshd -t 2>&1 && echo 'SSH 설정 문법 정상' || echo 'SSH 설정 오류!'"
```

> **결과 해석**:
> - `sshd -t`: 설정 파일의 문법을 검증한다. 오류가 있으면 재시작 시 SSH가 중단될 수 있다
> - `MaxAuthTries 3`: 3회 실패 시 연결 종료 → 브루트포스 속도를 크게 낮춘다
> - 경고 배너: 법적 효력을 갖는 접근 경고 메시지로, 기업 환경에서 필수이다
> - 강한 암호 스위트: 약한 알고리즘을 비활성화하여 다운그레이드 공격을 방지한다
>
> **실전 활용**: 공방전에서 SSH 설정 변경 후 반드시 `sshd -t`로 검증하고, 별도 세션으로 재접속 테스트를 해야 한다. 잘못된 설정으로 SSH가 끊기면 서버를 관리할 수 없다. 항상 현재 세션을 유지한 상태에서 새 세션으로 테스트한다.
>
> **명령어 해설**:
> - `sshd -t`: SSH 설정 문법 테스트 (test 모드, 서비스 영향 없음)
> - `cp ... .backup.$(date +%Y%m%d)`: 날짜 포함 백업 파일 생성
>
> **트러블슈팅**:
> - SSH 접속 불가: 설정 오류 → 콘솔 접근으로 `/etc/ssh/sshd_config.backup*`에서 복원
> - "Could not load host key": 키 파일 권한 확인 → `chmod 600 /etc/ssh/ssh_host_*_key`

### Step 3: 비밀번호 정책 강화

> **실습 목적**: 시스템의 비밀번호 정책을 강화하여 약한 비밀번호 사용을 방지한다.
>
> **배우는 것**: PAM 모듈 설정, 비밀번호 복잡도, 계정 잠금 정책

```bash
# 현재 비밀번호 정책 확인 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_WARN_AGE|^PASS_MIN_LEN' /etc/login.defs 2>/dev/null"
# 예상 출력:
# PASS_MAX_DAYS   99999   ← 취약: 비밀번호 만료 없음
# PASS_MIN_DAYS   0
# PASS_WARN_AGE   7

# 로그인 가능한 계정의 비밀번호 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S chage -l web 2>/dev/null"
# 예상 출력:
# Last password change                    : Mar 20, 2026
# Password expires                        : never  ← 만료 없음
# Maximum number of days between password change : 99999

# 비밀번호 해시 알고리즘 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S grep '^web' /etc/shadow 2>/dev/null | cut -d: -f2 | cut -c1-3"
# 예상 출력: $6$ (SHA-512) 또는 $y$ (yescrypt)

# 권장 설정 확인
echo "=== 비밀번호 정책 권장 ==="
echo "/etc/login.defs:"
echo "  PASS_MAX_DAYS  90     # 90일마다 변경"
echo "  PASS_MIN_DAYS  7      # 최소 7일 유지 (자주 변경 방지)"
echo "  PASS_WARN_AGE  14     # 14일 전 경고"
echo ""
echo "PAM pam_pwquality (/etc/security/pwquality.conf):"
echo "  minlen = 12            # 최소 12자"
echo "  dcredit = -1           # 숫자 최소 1개"
echo "  ucredit = -1           # 대문자 최소 1개"
echo "  lcredit = -1           # 소문자 최소 1개"
echo "  ocredit = -1           # 특수문자 최소 1개"
echo "  maxrepeat = 3          # 동일 문자 연속 최대 3회"
```

> **결과 해석**:
> - `PASS_MAX_DAYS 99999`: 사실상 비밀번호 만료가 없음 → 90일로 변경 권장
> - `$6$`: SHA-512 해시 사용 중 (양호). `$1$`이면 MD5로 취약
> - PAM `pam_pwquality`: 비밀번호 복잡도를 강제하는 모듈
>
> **실전 활용**: 비밀번호 정책은 브루트포스 공격의 성공 확률을 크게 낮춘다. 특히 공방전에서 약한 비밀번호는 가장 먼저 공격당한다.
>
> **명령어 해설**:
> - `chage -l <user>`: 사용자의 비밀번호 만료 정보 표시
> - `chage -M 90 <user>`: 최대 비밀번호 유효 기간을 90일로 설정
>
> **트러블슈팅**:
> - pam_pwquality 미설치: `apt install libpam-pwquality`
> - 정책 적용 후 비밀번호 변경 불가: 현재 비밀번호가 새 정책을 충족하지 못함 → 관리자가 직접 변경

---

# Part 4: 커널 보안 + 백업 + 방어 체크리스트 실습 (30분)

## 실습 4.1: 커널 보안 파라미터 설정

### Step 1: sysctl 네트워크 보안 파라미터

> **실습 목적**: 커널 수준의 네트워크 보안 파라미터를 설정하여 IP 스푸핑, ICMP 공격 등을 차단한다.
>
> **배우는 것**: sysctl을 이용한 커널 네트워크 보안 강화, CIS Benchmark 기반 설정

```bash
# 현재 네트워크 보안 파라미터 확인 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S sysctl -a 2>/dev/null | grep -E \
   'ip_forward|icmp_echo_ignore|accept_redirects|accept_source_route|rp_filter|log_martians|tcp_syncookies'"
# 예상 출력:
# net.ipv4.ip_forward = 0
# net.ipv4.icmp_echo_ignore_all = 0          ← ping 응답 활성
# net.ipv4.conf.all.accept_redirects = 1     ← 취약: ICMP 리다이렉트 허용
# net.ipv4.conf.all.accept_source_route = 0
# net.ipv4.conf.all.rp_filter = 1
# net.ipv4.conf.all.log_martians = 0         ← 비활성: 의심 패킷 로깅 없음
# net.ipv4.tcp_syncookies = 1

# CIS Benchmark 기반 권장 보안 파라미터
cat << 'SYSCTL_GUIDE'
=== 커널 네트워크 보안 파라미터 (CIS Benchmark) ===

# IP 포워딩 비활성화 (라우터가 아닌 경우)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# ICMP 리다이렉트 거부 (MITM 방지)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# 소스 라우팅 거부 (IP 스푸핑 방지)
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Reverse Path Filtering (IP 스푸핑 탐지)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# SYN Flood 방어 (TCP SYN Cookies)
net.ipv4.tcp_syncookies = 1

# 의심스러운 패킷 로깅 (Martian Packets)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# ICMP 브로드캐스트 무시 (Smurf 공격 방지)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# 보안 ICMP 리다이렉트 거부
net.ipv4.conf.all.secure_redirects = 0
SYSCTL_GUIDE

# 현재 값과 권장값 비교
echo "=== 현재 vs 권장 비교 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 'accept_redirects: '$(sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null)' (권장: 0)'; \
   echo 'log_martians: '$(sysctl -n net.ipv4.conf.all.log_martians 2>/dev/null)' (권장: 1)'; \
   echo 'tcp_syncookies: '$(sysctl -n net.ipv4.tcp_syncookies 2>/dev/null)' (권장: 1)'; \
   echo 'rp_filter: '$(sysctl -n net.ipv4.conf.all.rp_filter 2>/dev/null)' (권장: 1)'"
```

> **결과 해석**:
> - `accept_redirects = 1`: ICMP 리다이렉트를 수락 → MITM 공격 가능 → 0으로 변경
> - `log_martians = 0`: 의심스러운 패킷을 로깅하지 않음 → 1로 변경
> - `tcp_syncookies = 1`: SYN Flood 방어가 활성화되어 있음 (양호)
>
> **실전 활용**: 공방전에서 이 파라미터들은 Red Team의 네트워크 수준 공격을 크게 어렵게 만든다. 특히 SYN Cookies와 RP Filter는 기본 네트워크 방어의 핵심이다.
>
> **명령어 해설**:
> - `sysctl -a`: 모든 커널 파라미터 출력
> - `sysctl -w <param>=<value>`: 즉시 적용 (재부팅 시 초기화)
> - `/etc/sysctl.d/*.conf`: 영구 설정 파일 위치
> - `sysctl -p`: 설정 파일 재로드
>
> **트러블슈팅**:
> - sysctl 값이 적용되지 않는 경우: `sysctl -p`로 설정 재로드
> - Docker 네트워크 문제: Docker 사용 시 ip_forward=1 유지 필요

### Step 2: 파일 시스템 보안 감사

> **실습 목적**: 파일 권한, SUID/SGID 비트, 임시 디렉토리 설정을 점검하여 권한 상승 공격을 방지한다.
>
> **배우는 것**: SUID 감사, /tmp 보안, 중요 파일 권한 검증

```bash
# SUID 비트가 설정된 파일 전체 조사 (web 서버)
echo "=== SUID 파일 감사 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find / -perm -4000 -type f 2>/dev/null | sort"
# 예상 출력:
# /usr/bin/chfn
# /usr/bin/chsh
# /usr/bin/gpasswd
# /usr/bin/mount
# /usr/bin/newgrp
# /usr/bin/passwd
# /usr/bin/su
# /usr/bin/sudo
# /usr/bin/umount

# World-writable 파일 확인 (보안 위험)
echo ""
echo "=== World-Writable 파일 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find / -perm -002 -type f \
   ! -path '/proc/*' ! -path '/sys/*' ! -path '/run/*' 2>/dev/null | head -20"

# 중요 파일 권한 확인
echo ""
echo "=== 중요 파일 권한 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ls -la /etc/passwd /etc/shadow /etc/group /etc/gshadow /etc/ssh/sshd_config 2>/dev/null"
# 기대값:
# /etc/passwd:       644 (rw-r--r--)
# /etc/shadow:       640 (rw-r-----)  root:shadow
# /etc/group:        644 (rw-r--r--)
# /etc/gshadow:      640 (rw-r-----)  root:shadow
# /etc/ssh/sshd_config: 644 (rw-r--r--)

# 비표준 경로의 SUID 확인 (백도어 의심)
echo ""
echo "=== 비표준 SUID (백도어 의심) ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S find / -perm -4000 -type f \
   ! -path '/usr/*' ! -path '/bin/*' ! -path '/sbin/*' ! -path '/snap/*' 2>/dev/null"
# 예상 출력: (비표준 경로의 SUID가 있다면 경고)
```

> **결과 해석**:
> - 표준 SUID 파일(`su`, `sudo`, `passwd` 등)은 정상이다
> - `/tmp`, `/var`, `/home` 등 비표준 경로의 SUID 파일은 백도어 의심
> - World-writable 실행 파일은 누구나 수정 가능하므로 악성코드 주입 위험
> - `/etc/shadow` 권한이 644이면 비밀번호 해시가 모든 사용자에게 노출됨 (심각)
>
> **실전 활용**: 공방전에서 Red Team은 SUID 바이너리를 악용한 권한 상승을 자주 시도한다. 불필요한 SUID를 미리 제거하면 이를 방지할 수 있다.
>
> **명령어 해설**:
> - `find / -perm -4000`: SUID 비트가 설정된 파일 검색
> - `find / -perm -002`: 기타 사용자(others)에 쓰기 권한이 있는 파일
> - `chmod u-s <file>`: SUID 비트 제거
>
> **트러블슈팅**:
> - SUID 제거 후 sudo가 안 되는 경우: `/usr/bin/sudo`의 SUID는 반드시 유지
> - /etc/shadow 권한 복구: `chmod 640 /etc/shadow && chown root:shadow /etc/shadow`

## 실습 4.2: 백업 및 복원 테스트

### Step 1: 설정 파일 백업

> **실습 목적**: 공방전 시작 전 시스템 설정 파일을 백업하여 침해 시 신속한 복원을 보장한다.
>
> **배우는 것**: tar를 이용한 설정 백업, 백업 무결성 검증, 원격 복사

```bash
# web 서버 설정 백업
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S tar czf /tmp/config_backup_$(date +%Y%m%d).tar.gz \
    /etc/ssh/sshd_config \
    /etc/passwd \
    /etc/shadow \
    /etc/group \
    /etc/crontab \
    /etc/apache2/ \
    /etc/sysctl.conf \
    2>/dev/null && echo '백업 완료' && ls -lh /tmp/config_backup_*.tar.gz"
# 예상 출력:
# 백업 완료
# -rw-r--r-- 1 root root 15K ... /tmp/config_backup_20260403.tar.gz

# 백업 파일 해시 기록
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sha256sum /tmp/config_backup_*.tar.gz 2>/dev/null"

# 백업 내용 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "tar tzf /tmp/config_backup_*.tar.gz 2>/dev/null | head -20"

# 백업을 관리 서버(opsclaw)로 복사 (오프사이트 보관)
sshpass -p1 scp -o StrictHostKeyChecking=no \
  web@10.20.30.80:/tmp/config_backup_*.tar.gz /tmp/ 2>/dev/null
echo "백업 파일 원격 복사 완료"
ls -lh /tmp/config_backup_*.tar.gz 2>/dev/null
```

> **결과 해석**:
> - `tar czf`: 압축된 아카이브 생성 (c=생성, z=gzip, f=파일명)
> - SHA-256 해시: 백업 무결성 확인용. 복원 전에 해시를 비교한다
> - 원격 복사: 3-2-1 원칙에 따라 백업을 다른 서버에도 보관한다
>
> **실전 활용**: 공방전에서 침해당한 설정 파일을 이 백업에서 즉시 복원할 수 있다.
>
> **명령어 해설**:
> - `tar czf <output> <files>`: 지정된 파일들을 gzip 압축 아카이브로 생성
> - `tar tzf <archive>`: 아카이브 내용 목록 확인 (압축 해제 없이)
> - `scp`: SSH를 통한 안전한 파일 복사
>
> **트러블슈팅**:
> - 권한 오류: `/etc/shadow` 등은 root만 읽을 수 있음 → sudo 필수
> - 공간 부족: `df -h /tmp`으로 여유 공간 확인

### Step 2: 복원 테스트

> **실습 목적**: 백업에서 실제로 파일을 복원하여 백업의 유효성을 검증한다. "테스트하지 않은 백업은 백업이 아니다."
>
> **배우는 것**: tar 복원, 선택적 파일 추출, 복원 후 무결성 검증

```bash
# 복원 테스트 디렉토리 생성
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "mkdir -p /tmp/restore_test"

# 백업에서 특정 파일 추출 (전체 복원이 아닌 선택적 복원)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 1 | sudo -S tar xzf /tmp/config_backup_*.tar.gz \
    -C /tmp/restore_test \
    etc/ssh/sshd_config 2>/dev/null && \
   echo '선택적 복원 완료'"

# 원본과 비교
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "diff /etc/ssh/sshd_config /tmp/restore_test/etc/ssh/sshd_config 2>/dev/null && \
   echo '원본과 백업 동일 (무결성 확인)' || \
   echo '차이 발견 — 설정 변경됨'"

# 전체 복원 시뮬레이션 (실제로는 수행하지 않음)
echo "=== 긴급 복원 명령 (필요 시 사용) ==="
echo "tar xzf /tmp/config_backup_*.tar.gz -C / etc/ssh/sshd_config"
echo "systemctl restart sshd"
echo "→ 백업에서 SSH 설정을 복원하고 서비스 재시작"

# 테스트 디렉토리 정리
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "rm -rf /tmp/restore_test && echo '테스트 정리 완료'"
```

> **결과 해석**:
> - `diff` 결과가 없으면 원본과 백업이 동일하다 (무결성 확인)
> - 선택적 복원: 전체 복원이 아닌 특정 파일만 추출 가능
> - 실제 긴급 상황에서는 `tar xzf ... -C /` 명령으로 즉시 복원
>
> **실전 활용**: 공방전 중 SSH 설정이 변조되면 백업에서 즉시 복원하고 `systemctl restart sshd`로 적용한다.
>
> **명령어 해설**:
> - `tar xzf <archive> -C <dir> <file>`: 아카이브에서 특정 파일만 지정 디렉토리에 추출
> - `diff <file1> <file2>`: 두 파일 비교 (차이 없으면 종료코드 0)
>
> **트러블슈팅**:
> - 파일 경로 불일치: tar는 절대경로에서 `/`를 제거함 → `tar tzf`로 경로 확인

## 실습 4.3: 종합 방어 체크리스트

### Step 1: 공방전 Blue Team 방어 체크리스트 실행

> **실습 목적**: 공방전 시작 전 모든 하드닝 항목을 체계적으로 점검하는 스크립트를 실행한다.
>
> **배우는 것**: 자동화된 보안 점검, 체크리스트 기반 감사, 결과 해석

```bash
# 종합 보안 점검 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'AUDIT'
echo "========================================="
echo "  공방전 방어 체크리스트 — $(hostname)"
echo "  점검 시간: $(date)"
echo "========================================="

echo ""
echo "[1] SSH 보안"
echo -n "  Root 로그인: "
sshd -T 2>/dev/null | grep -q "permitrootlogin no" && echo "차단 (OK)" || echo "허용 (경고)"
echo -n "  비밀번호 인증: "
sshd -T 2>/dev/null | grep -q "passwordauthentication no" && echo "비활성 (OK)" || echo "활성 (주의)"
echo -n "  X11 포워딩: "
sshd -T 2>/dev/null | grep -q "x11forwarding no" && echo "비활성 (OK)" || echo "활성 (주의)"
echo -n "  MaxAuthTries: "
sshd -T 2>/dev/null | grep "maxauthtries" | awk '{print $2}'

echo ""
echo "[2] 네트워크 보안"
echo -n "  SYN Cookies: "
sysctl -n net.ipv4.tcp_syncookies 2>/dev/null | grep -q 1 && echo "활성 (OK)" || echo "비활성 (경고)"
echo -n "  ICMP 리다이렉트: "
sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null | grep -q 0 && echo "거부 (OK)" || echo "허용 (경고)"
echo -n "  소스 라우팅: "
sysctl -n net.ipv4.conf.all.accept_source_route 2>/dev/null | grep -q 0 && echo "거부 (OK)" || echo "허용 (경고)"
echo -n "  RP Filter: "
sysctl -n net.ipv4.conf.all.rp_filter 2>/dev/null | grep -q 1 && echo "활성 (OK)" || echo "비활성 (경고)"

echo ""
echo "[3] 파일 시스템"
echo -n "  /etc/shadow 권한: "
SHADOW_PERM=$(stat -c %a /etc/shadow 2>/dev/null)
[ "$SHADOW_PERM" = "640" ] && echo "640 (OK)" || echo "$SHADOW_PERM (확인 필요)"
echo -n "  비표준 SUID: "
SUID=$(find / -perm -4000 -type f ! -path "/usr/*" ! -path "/bin/*" ! -path "/sbin/*" ! -path "/snap/*" 2>/dev/null | wc -l)
[ "$SUID" -eq 0 ] && echo "없음 (OK)" || echo "${SUID}개 발견 (경고)"

echo ""
echo "[4] 서비스"
echo -n "  실행 서비스 수: "
systemctl list-units --type=service --state=running --no-pager 2>/dev/null | grep -c "\.service"
echo -n "  열린 TCP 포트 수: "
ss -tln 2>/dev/null | grep -c LISTEN

echo ""
echo "[5] 사용자 계정"
echo -n "  로그인 가능 계정: "
grep -cv "nologin\|false" /etc/passwd
echo -n "  UID 0 계정: "
awk -F: '$3==0 {printf "%s ", $1}' /etc/passwd
echo ""
echo -n "  빈 비밀번호: "
EMPTY=$(echo 1 | sudo -S awk -F: '($2=="") {print $1}' /etc/shadow 2>/dev/null | wc -w)
[ "$EMPTY" -eq 0 ] && echo "없음 (OK)" || echo "${EMPTY}개 (경고!)"

echo ""
echo "========================================="
echo "  점검 완료"
echo "========================================="
AUDIT
```

> **결과 해석**:
> - "OK" 항목: 보안 기준 충족
> - "경고"/"주의" 항목: 하드닝이 필요한 항목
> - UID 0 계정이 root 외에 있으면 백도어 의심
> - 빈 비밀번호 계정은 인증 없이 접근 가능한 심각한 취약점
>
> **실전 활용**: 이 체크리스트를 공방전 시작 전에 모든 서버에서 실행하고, "경고" 항목을 우선 조치한다. 스크립트로 만들어 두면 반복 실행이 쉽다.
>
> **명령어 해설**:
> - `sshd -T`: SSH 유효 설정 출력 (sudo 필요)
> - `stat -c %a`: 파일의 8진수 권한 표시
> - `awk -F: '$3==0'`: /etc/passwd에서 UID가 0인 사용자 검색
>
> **트러블슈팅**:
> - sshd -T 권한 오류: root 권한 필요 → `echo 1 | sudo -S sshd -T`
> - 일부 확인이 실패하는 경우: sudo 없이 실행한 항목 → `echo 1 | sudo -S` 추가

### Step 2: OpsClaw 자동화 멀티 호스트 점검

> **실습 목적**: OpsClaw를 활용하여 여러 서버의 보안 상태를 동시에 점검한다.
>
> **배우는 것**: OpsClaw execute-plan을 이용한 멀티 호스트 보안 감사 자동화

```bash
# OpsClaw 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week10-hardening","request_text":"인프라 하드닝 점검","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 멀티 호스트 보안 점검
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"web SSH 설정","instruction_prompt":"sshd -T 2>/dev/null | grep -E \"permitrootlogin|passwordauthentication|x11forwarding|maxauthtries\"","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"title":"secu SSH 설정","instruction_prompt":"sshd -T 2>/dev/null | grep -E \"permitrootlogin|passwordauthentication|x11forwarding|maxauthtries\"","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":3,"title":"web 열린 포트","instruction_prompt":"ss -tln 2>/dev/null | grep LISTEN","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":4,"title":"web sysctl 보안","instruction_prompt":"sysctl net.ipv4.tcp_syncookies net.ipv4.conf.all.accept_redirects net.ipv4.conf.all.rp_filter 2>/dev/null","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":5,"title":"web 비표준 SUID","instruction_prompt":"find / -perm -4000 -type f ! -path \"/usr/*\" ! -path \"/bin/*\" ! -path \"/sbin/*\" ! -path \"/snap/*\" 2>/dev/null | head -10 || echo none","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} -> {t[\"status\"]}')
"
# 예상 출력:
# 결과: success
#   [1] web SSH 설정         -> ok
#   [2] secu SSH 설정        -> ok
#   [3] web 열린 포트         -> ok
#   [4] web sysctl 보안      -> ok
#   [5] web 비표준 SUID      -> ok
```

> **결과 해석**: OpsClaw를 통한 점검 결과는 evidence로 기록되어 나중에 확인할 수 있다. 전체 인프라의 보안 상태를 한 번에 파악할 수 있다.
>
> **실전 활용**: 공방전 시작 전에 이 자동화 점검을 실행하여 모든 서버의 보안 상태를 빠르게 확인하고, 취약한 항목을 우선 조치한다.

---

## 검증 체크리스트
- [ ] CIS Benchmark의 Level 1/Level 2 차이를 설명할 수 있는가
- [ ] 불필요한 서비스를 식별하고 안전하게 비활성화(stop+disable)할 수 있는가
- [ ] SSH 보안 설정(root 차단, MaxAuthTries, X11 비활성화)을 적용할 수 있는가
- [ ] sshd_config 변경 후 문법 검증(`sshd -t`)을 수행할 수 있는가
- [ ] sysctl 커널 파라미터를 조정하여 네트워크 보안을 강화할 수 있는가
- [ ] SUID 비트 파일을 감사하고 비표준 항목을 식별할 수 있는가
- [ ] 설정 파일을 tar로 백업하고 해시로 무결성을 검증할 수 있는가
- [ ] 백업에서 선택적으로 파일을 복원하고 원본과 비교할 수 있는가
- [ ] 자동화된 보안 점검 스크립트를 실행하고 결과를 해석할 수 있는가
- [ ] 공방전 방어 체크리스트를 작성하고 시간 내 우선순위를 설정할 수 있는가

## 자가 점검 퀴즈

1. 인프라 하드닝의 5가지 핵심 원칙을 나열하고 각각 1줄로 설명하라.

2. CIS Benchmark Level 1과 Level 2의 차이를 설명하라. 공방전에서는 어떤 레벨까지 적용하는 것이 적절한가?

3. `systemctl stop`과 `systemctl disable`의 차이를 설명하라. 왜 두 명령을 함께 사용해야 하는가?

4. SSH에서 `PermitRootLogin prohibit-password`와 `PermitRootLogin no`의 차이를 설명하라.

5. `net.ipv4.tcp_syncookies = 1`이 SYN Flood 공격을 어떻게 방어하는지 동작 원리를 설명하라.

6. SUID 비트가 설정된 `/usr/bin/passwd`가 정상인 이유와, `/tmp/myshell`에 SUID가 설정되면 위험한 이유를 설명하라.

7. 3-2-1 백업 원칙의 각 숫자가 의미하는 바를 설명하라.

8. `sshd -t` 명령의 중요성을 설명하라. 이 검증 없이 sshd를 재시작하면 어떤 위험이 있는가?

9. 패치 우선순위 매트릭스에서 P1(즉시)과 P3(1주)의 기준 차이를 설명하라.

10. 공방전에서 Blue Team이 첫 10분 안에 수행해야 할 하드닝 작업 5가지를 우선순위 순으로 나열하라.

## 과제

### 과제 1: 서버별 하드닝 보고서 (필수)
- web, secu, siem 3개 서버에 대해 보안 점검 스크립트를 실행하라
- 각 서버별 발견된 취약점과 조치 사항을 표 형태로 정리
- 최소 5개 항목에 대해 하드닝을 적용하고 전후 비교 결과를 제출
- CIS Benchmark 항목 번호를 참조하여 매핑

### 과제 2: 공방전 방어 체크리스트 작성 (선택)
- 30개 이상의 체크리스트 항목을 카테고리별로 작성
- 각 항목에 대해 확인 명령어, 기대값, 조치 명령어를 포함
- 체크리스트를 자동 실행하는 bash 스크립트를 작성하여 제출

### 과제 3: 자동 하드닝 스크립트 (도전)
- 서버에 접속하여 자동으로 주요 하드닝을 적용하는 스크립트를 작성
- SSH, 커널, 파일 권한, 서비스 정리를 포함
- 적용 전 백업, 적용 후 검증 기능을 포함
- `--dry-run` 옵션으로 변경 사항을 미리 확인하는 기능 구현
