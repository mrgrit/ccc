# Week 08: 로그 분석

## 학습 목표
- 리눅스 시스템 로그의 종류, 위치, 형식을 체계적으로 파악할 수 있다
- auth.log, syslog, kern.log 등 핵심 로그를 분석하여 침입 시도를 식별할 수 있다
- 로그 기반 타임라인(Timeline)을 구성하여 공격 경로를 재구성할 수 있다
- IOC(Indicator of Compromise)를 로그에서 추출하고 분류할 수 있다
- Wazuh SIEM과 연동하여 중앙 집중식 로그 분석을 수행할 수 있다
- 로그 조작/삭제 시도를 탐지하는 방법을 이해한다
- 공방전에서 Blue Team의 핵심 탐지 활동으로서 로그 분석을 수행할 수 있다

## 전제 조건
- Week 01-07 완료 (공격 기법 + 방화벽 + IDS 이해)
- Linux 기본 명령어 (grep, awk, sort, uniq)
- 정규 표현식 기초

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 로그 분석 이론 + 로그 종류/위치 | 강의 |
| 0:40-1:10 | 로그 분석 기법 + IOC 추출 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | auth.log/syslog 분석 실습 | 실습 |
| 2:00-2:30 | 타임라인 구성 + Wazuh 연동 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 로그 분석 시나리오 실습 | 실습 |
| 3:10-3:40 | 안티포렌식 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 로그 분석 이론 (40분)

## 1.1 로그 분석의 중요성

로그 분석은 보안 모니터링, 사고 대응, 포렌식의 핵심이다. 공격자의 모든 활동은 어딘가에 흔적을 남기며, 이 흔적을 찾는 것이 방어자의 핵심 역량이다.

**MITRE ATT&CK 매핑:**
```
방어 활동:
  +-- 탐지(Detection) — 로그 기반 공격 식별
  +-- 대응(Response) — 로그 기반 사고 범위 파악

공격 활동 (로그 회피):
  +-- T1070 — Indicator Removal
        +-- T1070.001 — Clear Windows Event Logs
        +-- T1070.002 — Clear Linux or Mac System Logs
        +-- T1070.003 — Clear Command History
```

### 로그 분석이 답하는 질문

```
WHO   — 누가? (사용자, IP, 프로세스)
WHAT  — 무엇을? (명령, 파일 접근, 네트워크 활동)
WHEN  — 언제? (타임스탬프, 시간대)
WHERE — 어디서? (소스 IP, 인터페이스, 호스트)
HOW   — 어떻게? (공격 기법, 도구, 취약점)
WHY   — 왜? (동기, 목표)
```

## 1.2 리눅스 로그 종류와 위치

### 핵심 로그 파일

| 로그 | 경로 | 내용 | 보안 관련성 |
|------|------|------|-----------|
| **auth.log** | `/var/log/auth.log` | 인증/인가 이벤트 | SSH 로그인, sudo, su |
| **syslog** | `/var/log/syslog` | 시스템 전반 이벤트 | 서비스 시작/중지, 에러 |
| **kern.log** | `/var/log/kern.log` | 커널 메시지 | 방화벽 로그, 하드웨어 |
| **apache** | `/var/log/apache2/access.log` | 웹 접근 기록 | SQLi, XSS, 스캐닝 |
| **apache error** | `/var/log/apache2/error.log` | 웹 에러 | 공격 실패 흔적 |
| **suricata** | `/var/log/suricata/fast.log` | IDS 경보 | 공격 탐지 |
| **suricata eve** | `/var/log/suricata/eve.json` | IDS 상세 | 공격 상세 분석 |
| **wazuh alerts** | `/var/ossec/logs/alerts/alerts.log` | SIEM 경보 | 통합 보안 이벤트 |
| **lastlog** | `/var/log/lastlog` | 마지막 로그인 | 계정 활동 추적 |
| **wtmp** | `/var/log/wtmp` | 로그인 기록 | 접속 이력 |
| **btmp** | `/var/log/btmp` | 실패한 로그인 | 브루트포스 탐지 |
| **cron** | `/var/log/cron.log` | cron 작업 기록 | 백도어 cron 탐지 |

### auth.log 형식 상세

```
Mar 25 14:32:01 web sshd[12345]: Accepted password for web from 10.20.30.201 port 54321 ssh2
|              |    |     |        |                        |                  |
|              |    |     |        |                        |                  +-- 소스 포트
|              |    |     |        |                        +-- 소스 IP
|              |    |     |        +-- 인증 결과 + 사용자
|              |    |     +-- PID
|              |    +-- 프로세스
|              +-- 호스트명
+-- 타임스탬프
```

### 주요 auth.log 이벤트 패턴

| 이벤트 | 로그 패턴 | 의미 |
|--------|---------|------|
| SSH 성공 | `Accepted password for` | 비밀번호 인증 성공 |
| SSH 실패 | `Failed password for` | 비밀번호 틀림 |
| SSH 무효 사용자 | `Invalid user` | 존재하지 않는 사용자 |
| sudo 성공 | `sudo:.*COMMAND=` | sudo 명령 실행 |
| sudo 실패 | `sudo:.*authentication failure` | sudo 인증 실패 |
| su 전환 | `su:.*session opened` | 사용자 전환 |
| 계정 잠금 | `pam_unix.*account locked` | 계정 잠금 발동 |

## 1.3 IOC (Indicator of Compromise)

IOC는 침해 사고의 존재를 나타내는 증거이다.

### IOC 유형

| 유형 | 설명 | 로그에서의 추출 | 예시 |
|------|------|---------------|------|
| IP 주소 | 공격자/C2 서버 IP | auth.log, apache log | 192.168.1.100 |
| 도메인 | 악성 도메인 | DNS 로그, HTTP 로그 | evil.attacker.com |
| URL | 악성 URL | 웹 접근 로그 | /admin/shell.php |
| 파일 해시 | 악성 파일 식별자 | FIM 로그, AV 로그 | MD5, SHA256 |
| 사용자 에이전트 | 공격 도구 식별 | HTTP 로그 | sqlmap, Nikto |
| 명령어 패턴 | 악성 명령 | auth.log, audit 로그 | cat /etc/shadow |
| 포트 | 비정상 포트 사용 | 방화벽 로그 | 4444 (Metasploit) |

---

# Part 2: 로그 분석 기법 (30분)

## 2.1 명령줄 로그 분석 도구

| 도구 | 용도 | 예시 |
|------|------|------|
| `grep` | 패턴 검색 | `grep "Failed password" auth.log` |
| `awk` | 필드 추출 | `awk '{print $1,$2,$3,$11}' auth.log` |
| `sort` | 정렬 | `sort -t' ' -k3 auth.log` |
| `uniq -c` | 중복 카운트 | `sort \| uniq -c \| sort -rn` |
| `cut` | 필드 잘라내기 | `cut -d' ' -f1-3,11` |
| `wc -l` | 라인 수 | `grep "Failed" auth.log \| wc -l` |
| `tail -f` | 실시간 모니터링 | `tail -f /var/log/auth.log` |
| `jq` | JSON 파싱 | `jq '.alert.signature' eve.json` |

## 2.2 타임라인 구성 방법

```
타임라인 구성 프로세스:
[1] 관련 로그 수집 (auth.log, access.log, suricata 등)
[2] 타임스탬프 통일 (UTC 또는 KST)
[3] 시간순 정렬
[4] 주요 이벤트 표시
[5] 공격 단계 매핑

예시 타임라인:
  14:30:00  [suricata]  포트 스캔 탐지 (10.20.30.201 → 10.20.30.80)
  14:31:15  [auth.log]  SSH 로그인 시도 실패 x5 (web@10.20.30.80)
  14:31:45  [auth.log]  SSH 로그인 성공 (web@10.20.30.80, password)
  14:32:00  [auth.log]  sudo su 실행 (web → root)
  14:32:30  [kern.log]  nftables 규칙 변경
  14:33:00  [access.log] SQLi 시도 (UNION SELECT)
```

---

# Part 3: auth.log/syslog 분석 실습 (40분)

## 실습 3.1: auth.log 분석 — SSH 브루트포스 탐지

### Step 1: SSH 로그인 시도 분석

> **실습 목적**: auth.log에서 SSH 로그인 시도를 분석하여 브루트포스 공격을 식별한다.
>
> **배우는 것**: auth.log 파싱, 패턴 분석, IP별 통계

```bash
# web 서버의 auth.log에서 SSH 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S cat /var/log/auth.log 2>/dev/null | grep sshd | tail -20"
# 예상 출력: SSH 관련 로그 (성공/실패)

# 실패한 로그인 시도 카운트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
# 예상 출력: 실패 횟수

# IP별 실패 횟수 (브루트포스 탐지)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'Failed password' /var/log/auth.log 2>/dev/null | grep -oP 'from \K[\d.]+' | sort | uniq -c | sort -rn | head -10"
# 예상 출력:
#  50 10.20.30.201   ← Week 04 hydra 브루트포스 흔적

# 성공한 로그인 목록
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'Accepted' /var/log/auth.log 2>/dev/null | tail -10"
# 예상 출력: 성공한 SSH 로그인 기록
```

> **결과 해석**:
> - 동일 IP에서 다수의 `Failed password` → 브루트포스 공격
> - `Invalid user`가 포함된 시도 → 사전 기반 사용자명 추측
> - `Accepted password` 직후 `sudo` → 권한 상승 시도 가능성
>
> **실전 활용**: 공방전에서 Blue Team은 auth.log를 실시간으로 모니터링하여 브루트포스를 조기 탐지한다.
>
> **명령어 해설**:
> - `grep -oP 'from \K[\d.]+'`: Perl 정규식으로 "from " 다음의 IP만 추출
> - `sort | uniq -c | sort -rn`: 중복 카운트 후 내림차순 정렬

### Step 2: sudo 사용 분석

> **실습 목적**: sudo 로그를 분석하여 권한 상승 시도를 식별한다.
>
> **배우는 것**: sudo 로그 패턴과 비정상 활동 식별

```bash
# sudo 사용 내역
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -15"
# 예상 출력:
# web : TTY=pts/0 ; PWD=/home/web ; USER=root ; COMMAND=/bin/bash

# 실행된 sudo 명령 목록
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'COMMAND=' /var/log/auth.log 2>/dev/null | grep -oP 'COMMAND=\K.*' | sort | uniq -c | sort -rn | head -10"

# 위험한 sudo 명령 식별
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "echo 1 | sudo -S grep 'COMMAND=' /var/log/auth.log 2>/dev/null | grep -iE 'shadow|passwd|bash|sh|nft|iptables'"
```

> **결과 해석**:
> - `COMMAND=/bin/bash`: root 셸 획득 시도
> - `COMMAND=/usr/bin/cat /etc/shadow`: 비밀번호 해시 탈취 시도
> - `COMMAND=nft flush ruleset`: 방화벽 규칙 삭제 시도

## 실습 3.2: 웹 로그 분석 — 공격 탐지

### Step 1: Apache 접근 로그 분석

> **실습 목적**: 웹 서버 접근 로그에서 공격 흔적을 식별한다.
>
> **배우는 것**: HTTP 로그 분석과 웹 공격 패턴 식별

```bash
# Apache 접근 로그에서 SQLi 흔적
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "cat /var/log/apache2/access.log 2>/dev/null | grep -iE 'union|select|or%201|1=1' | tail -10"

# XSS 흔적
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "cat /var/log/apache2/access.log 2>/dev/null | grep -iE 'script|alert|onerror' | tail -10"

# Nikto/스캐너 흔적 (User-Agent)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "cat /var/log/apache2/access.log 2>/dev/null | grep -iE 'nikto|sqlmap|nmap|dirbuster' | tail -10"

# HTTP 상태 코드별 통계
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80   "cat /var/log/apache2/access.log 2>/dev/null | awk '{print \$9}' | sort | uniq -c | sort -rn | head -5"
# 예상 출력:
#  500 200    (정상)
#  100 404    (존재하지 않는 페이지)
#   50 403    (접근 거부)
#   10 500    (서버 에러 — 공격 흔적 가능)
```

> **결과 해석**:
> - 404 다수 → 디렉토리/파일 브루트포스 (gobuster, dirbuster 등)
> - 500 다수 → 서버 에러 유발 공격 시도 (SQLi, 잘못된 입력)
> - 공격 도구 User-Agent → 자동화 스캐닝 도구 사용 확인

## 실습 3.3: 타임라인 구성 + 종합 분석

### Step 1: OpsClaw를 활용한 로그 수집 자동화

> **실습 목적**: 여러 서버의 로그를 자동으로 수집하고 분석한다.
>
> **배우는 것**: 멀티 호스트 로그 수집 자동화

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week08-log-analysis","request_text":"로그 분석 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"web SSH 실패 분석","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"echo 1 | sudo -S grep Failed /var/log/auth.log 2>/dev/null | wc -l\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"web sudo 분석","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \"echo 1 | sudo -S grep COMMAND /var/log/auth.log 2>/dev/null | tail -5\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"secu 방화벽 로그","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S dmesg 2>/dev/null | grep NFT | tail -5\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":4,"title":"secu IDS 경보","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S tail -5 /var/log/suricata/fast.log 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:25s} → {t[\"status\"]}')
"
```

---

# Part 4: 안티포렌식 이해 + 방어 (30분)

## 4.1 안티포렌식 기법

| 기법 | 명령 | 탐지 방법 |
|------|------|---------|
| 로그 삭제 | `> /var/log/auth.log` | 파일 크기 급감 모니터링 |
| 로그 편집 | `sed -i '/공격IP/d' auth.log` | 로그 무결성 해시 |
| 히스토리 삭제 | `history -c` | .bash_history 백업 |
| 타임스탬프 조작 | `touch -t 202601010000 file` | MAC time 불일치 |
| 원격 로깅 우회 | 로컬 로그만 삭제 | 중앙 로그 서버 (Wazuh) |

## 4.2 로그 보호 전략

```
[1] 중앙 로그 서버 (Wazuh/rsyslog)
    → 로컬 삭제해도 중앙에 사본 보존
[2] 로그 무결성 해시
    → 주기적 SHA256 해시로 변조 탐지
[3] 불변 로그 (append-only)
    → chattr +a /var/log/auth.log
[4] 로그 크기 모니터링
    → 급감 시 경보 (Wazuh rule)
[5] 원격 syslog
    → rsyslog로 실시간 중앙 전송
```

---

## 검증 체크리스트
- [ ] auth.log에서 SSH 브루트포스를 식별했는가
- [ ] IP별/시간별 로그인 실패 통계를 산출했는가
- [ ] sudo 사용 내역을 분석하고 위험한 명령을 식별했는가
- [ ] 웹 접근 로그에서 SQLi/XSS 흔적을 찾았는가
- [ ] HTTP 상태 코드 통계로 비정상 활동을 식별했는가
- [ ] 타임라인을 구성하여 공격 경로를 재구성했는가
- [ ] OpsClaw를 통해 멀티 호스트 로그 수집을 자동화했는가
- [ ] IOC를 추출하고 분류했는가
- [ ] 안티포렌식 기법을 이해하고 방어 방법을 알고 있는가

## 자가 점검 퀴즈

1. auth.log에서 SSH 브루트포스를 탐지하기 위한 grep 명령과 통계 산출 방법을 설명하라.
2. `Failed password for invalid user admin from 192.168.1.100`에서 추출할 수 있는 IOC를 모두 나열하라.
3. Apache access.log에서 SQL Injection 시도를 탐지하기 위한 패턴 3가지를 제시하라.
4. 로그 기반 타임라인 구성의 5단계를 설명하라.
5. auth.log에서 sudo 명령 중 위험한 것을 식별하는 기준 3가지를 설명하라.
6. 공격자가 `/var/log/auth.log`를 삭제한 경우, 이를 탐지하는 방법 3가지를 설명하라.
7. Wazuh 중앙 로그 서버를 사용하면 어떤 보안 이점이 있는지 설명하라.
8. HTTP 상태 코드 404가 대량 발생하는 것의 보안적 의미를 설명하라.
9. 로그 분석에서 정규 표현식이 중요한 이유를 예시와 함께 설명하라.
10. 공방전에서 Blue Team이 실시간으로 모니터링해야 할 로그 파일 5가지를 우선순위 순으로 나열하라.

## 과제

### 과제 1: 로그 분석 보고서 (필수)
- web 서버의 auth.log, apache access.log를 분석
- 발견된 보안 이벤트를 IOC로 분류하고 타임라인 구성
- 공격 경로를 재구성하여 보고서 작성

### 과제 2: 실시간 모니터링 스크립트 (선택)
- bash 스크립트로 auth.log를 실시간 모니터링
- SSH 실패 5회 이상 시 경보 출력
- IP별 실패 카운트 자동 산출

### 과제 3: 로그 상관 분석 (도전)
- 여러 로그 소스(auth.log, access.log, suricata)를 통합 분석
- 동일 공격자의 활동을 교차 확인하여 종합 타임라인 구성
