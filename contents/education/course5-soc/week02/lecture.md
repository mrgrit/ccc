# Week 02: 로그 이해 (1) - 시스템 로그

## 학습 목표
- Linux 시스템 로그의 종류와 위치를 이해한다
- syslog, auth.log, journal의 구조를 분석할 수 있다
- auditd를 활용한 상세 감사 로깅을 이해한다
- 로그에서 보안 관련 이벤트를 식별할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

---

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |

---

---

## 1. 시스템 로그 개요

### 1.1 왜 로그가 중요한가?

보안관제(SOC)에서 로그는 **모든 것의 시작**이다.

```
공격 발생 → 로그에 흔적 남김 → SOC 분석원이 로그로 탐지/분석
```

- 사고 탐지의 **1차 데이터 소스**
- 포렌식 조사의 핵심 증거
- 컴플라이언스 요구사항 (ISMS-P 2.10.4: 로그 6개월 보관)

### 1.2 Linux 로그 시스템 구조

```
[애플리케이션] → [rsyslog/systemd-journal] → [로그 파일]
                                              → [원격 SIEM (Wazuh)]
```

| 구성 요소 | 역할 |
|-----------|------|
| rsyslog | 전통적 로그 수집 데몬 |
| systemd-journald | systemd 기반 로그 수집 |
| logrotate | 로그 순환(rotation) 관리 |
| Wazuh Agent | 원격 SIEM으로 로그 전송 |

---

## 2. 주요 로그 파일

> **이 실습을 왜 하는가?**
> "로그 이해 (1) - 시스템 로그" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안관제/SOC 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 로그 파일 위치와 용도

| 파일 | 용도 | SOC 관련 |
|------|------|---------|
| /var/log/syslog | 시스템 전반 이벤트 | 서비스 이상, 커널 오류 |
| /var/log/auth.log | 인증 관련 (SSH, sudo, su) | 무차별 대입, 권한 상승 |
| /var/log/kern.log | 커널 메시지 | 하드웨어 오류, 보안 모듈 |
| /var/log/dpkg.log | 패키지 설치/제거 | 비인가 소프트웨어 설치 |
| /var/log/cron.log | cron 작업 실행 | 비인가 예약 작업 |
| /var/log/faillog | 로그인 실패 기록 | 무차별 대입 공격 |

### 2.2 실습: 로그 파일 확인

> **실습 목적**: 4대 서버의 시스템 로그 파일 위치와 구조를 확인하여 로그 분석의 기초를 다진다
>
> **배우는 것**: auth.log, syslog, kern.log 등 주요 시스템 로그의 위치, 형식, 보안 관점의 의미를 이해한다
>
> **결과 해석**: 로그 파일이 존재하고 최근 기록이 있으면 로깅이 정상 동작 중이며, 파일이 없으면 로깅 설정 문제이다
>
> **실전 활용**: SOC L1 분석가의 첫 업무는 로그 소스의 정상 수집 여부를 확인하는 것이다

```bash
# 각 서버의 로그 파일 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip =========="
  ssh $srv  # srv=user@ip (아래 루프 참고) "ls -lh /var/log/syslog /var/log/auth.log /var/log/kern.log 2>/dev/null"
done
```

---

## 3. syslog 분석

### 3.1 syslog 메시지 형식

```
<날짜> <호스트명> <프로세스[PID]>: <메시지>
```

예시:
```
Mar 27 10:15:03 bastion sshd[12345]: Accepted password for user from 192.168.208.1 port 54321 ssh2
```

| 필드 | 값 | 의미 |
|------|-----|------|
| 날짜 | Mar 27 10:15:03 | 이벤트 발생 시각 |
| 호스트 | bastion | 로그를 생성한 서버 |
| 프로세스 | sshd[12345] | 프로세스명과 PID |
| 메시지 | Accepted password... | 이벤트 상세 |

### 3.2 syslog 심각도 (Severity)

| 코드 | 이름 | 의미 |
|------|------|------|
| 0 | Emergency | 시스템 사용 불가 |
| 1 | Alert | 즉시 조치 필요 |
| 2 | Critical | 치명적 상황 |
| 3 | Error | 오류 발생 |
| 4 | Warning | 경고 |
| 5 | Notice | 정상이지만 주목할 사항 |
| 6 | Info | 정보성 메시지 |
| 7 | Debug | 디버그 메시지 |

### 3.3 실습: syslog 분석

```bash
# 최근 syslog 확인
ssh ccc@10.20.30.201 "tail -20 /var/log/syslog"

# 오류 메시지만 필터링
ssh ccc@10.20.30.201 "grep -i 'error\|fail\|critical' /var/log/syslog | tail -10"

# 특정 서비스의 로그만 추출
ssh ccc@10.20.30.201 "grep 'sshd' /var/log/syslog | tail -10"

# rsyslog 설정 확인
ssh ccc@10.20.30.201 "cat /etc/rsyslog.conf | grep -v '^#' | grep -v '^$' | head -20"
```

---

## 4. auth.log 분석

### 4.1 auth.log의 중요성

auth.log는 SOC 분석원이 **가장 먼저 확인**하는 로그이다.

기록 내용:
- SSH 로그인 성공/실패
- sudo 명령 실행
- su (사용자 전환) 시도
- PAM 인증 이벤트

### 4.2 실습: SSH 로그인 분석

```bash
# SSH 로그인 성공
ssh ccc@10.20.30.201 "grep 'Accepted' /var/log/auth.log | tail -10"

# SSH 로그인 실패
ssh ccc@10.20.30.201 "grep 'Failed password' /var/log/auth.log | tail -10"

# 실패한 사용자명 통계
ssh ccc@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"for\") print \$(i+1)}' | sort | uniq -c | sort -rn | head -10"

# 실패한 출발지 IP 통계
ssh ccc@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -10"
```

### 4.3 실습: sudo 사용 분석

```bash
# sudo 명령 실행 이력
ssh ccc@10.20.30.201 "grep 'sudo:' /var/log/auth.log | tail -10"

# sudo 실패 (권한 없는 사용자의 시도)
ssh ccc@10.20.30.201 "grep 'NOT in sudoers' /var/log/auth.log 2>/dev/null"

# su 명령 사용 이력
ssh ccc@10.20.30.201 "grep 'su:' /var/log/auth.log | tail -5"
```

### 4.4 실습: 무차별 대입 공격 패턴 식별

```bash
# 1분 내 동일 IP에서 5회 이상 실패 = 무차별 대입 의심
ssh ccc@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$1,\$2,substr(\$3,1,5),\$(NF-3)}' | sort | uniq -c | sort -rn | head -10"

# 존재하지 않는 사용자로 시도 (Invalid user)
ssh ccc@10.20.30.201 "grep 'Invalid user' /var/log/auth.log 2>/dev/null | tail -10"
```

---

## 5. systemd journal 분석

### 5.1 journalctl 기본 사용법

```bash
# 최근 로그 확인
ssh ccc@10.20.30.201 "journalctl --no-pager | tail -20"

# 특정 서비스의 로그
ssh ccc@10.20.30.201 "journalctl -u sshd --no-pager | tail -10"

# 시간 범위로 필터링
ssh ccc@10.20.30.201 "journalctl --since '1 hour ago' --no-pager | tail -20"

# 부팅 이후 로그
ssh ccc@10.20.30.201 "journalctl -b --no-pager | tail -10"

# 우선순위별 필터링 (err 이상)
ssh ccc@10.20.30.201 "journalctl -p err --no-pager | tail -10"

# 커널 메시지만
ssh ccc@10.20.30.201 "journalctl -k --no-pager | tail -10"
```

### 5.2 journal vs syslog 비교

| 항목 | syslog (rsyslog) | journal (systemd) |
|------|-----------------|-------------------|
| 형식 | 텍스트 파일 | 바이너리 |
| 조회 | grep, awk | journalctl |
| 구조화 | 비구조화 | 구조화 (필드) |
| 보관 | logrotate | 자체 관리 |
| 장점 | 단순, 호환성 | 검색 강력, 메타데이터 풍부 |

### 5.3 실습: journal 고급 검색

```bash
# JSON 형식으로 출력 (필드 확인)
ssh ccc@10.20.30.201 "journalctl -u sshd -o json --no-pager | tail -1 | python3 -m json.tool 2>/dev/null"

# 특정 PID의 로그
ssh ccc@10.20.30.201 "journalctl _PID=1 --no-pager | tail -5"

# 디스크 사용량 확인
ssh ccc@10.20.30.201 "journalctl --disk-usage 2>/dev/null"
```

---

## 6. auditd (감사 로깅)

### 6.1 auditd란?

Linux Audit System은 **커널 수준**에서 시스템 호출(syscall)을 감시한다.
일반 로그보다 훨씬 상세한 정보를 기록할 수 있다.

- 파일 접근 감시
- 시스템 호출 추적
- 사용자 명령 기록
- 네트워크 연결 추적

### 6.2 실습: auditd 상태 확인

```bash
# auditd 설치 여부 확인
for srv in "ccc@10.20.30.201" "ccc@10.20.30.1" "ccc@10.20.30.80" "ccc@10.20.30.100"; do
  echo "=== $srv ==="
  ssh $srv  # srv=user@ip (아래 루프 참고) "systemctl is-active auditd 2>/dev/null || echo 'auditd 미설치'"
  ssh $srv  # srv=user@ip (아래 루프 참고) "which auditctl 2>/dev/null || echo 'auditctl 없음'"
done
```

### 6.3 auditd 규칙 예시

만약 auditd가 설치되어 있다면:

```bash
# 현재 감사 규칙 확인
ssh ccc@10.20.30.201 "sudo auditctl -l 2>/dev/null || echo '규칙 없음 또는 auditd 미설치'"

# /etc/passwd 파일 변경 감시 규칙 (예시)
# sudo auditctl -w /etc/passwd -p wa -k passwd_changes

# /etc/shadow 파일 접근 감시 규칙 (예시)
# sudo auditctl -w /etc/shadow -p r -k shadow_access

# audit 로그 확인
ssh ccc@10.20.30.201 "tail -10 /var/log/audit/audit.log 2>/dev/null || echo 'audit 로그 없음'"
```

### 6.4 auditd 로그 형식

```
type=SYSCALL msg=audit(1648389600.123:456): arch=c000003e syscall=2
  success=yes exit=3 a0=7fff5a8b4e90 ... pid=12345 uid=0 ...
  comm="cat" exe="/usr/bin/cat" key="shadow_access"
```

| 필드 | 의미 |
|------|------|
| type | 이벤트 유형 (SYSCALL, PATH 등) |
| msg | 타임스탬프와 시리얼 번호 |
| syscall | 시스템 호출 번호 |
| pid | 프로세스 ID |
| uid | 사용자 ID |
| comm | 실행 명령 |
| key | 감사 규칙의 태그 |

---

## 7. 로그 분석 실전

### 7.1 종합 분석 스크립트

```bash
#!/bin/bash
# 시스템 로그 보안 분석 스크립트
echo "============================================"
echo " 시스템 로그 보안 분석 - $(date)"
echo "============================================"

IP=$1
if [ -z "$IP" ]; then IP=10.20.30.201; fi

echo ""
echo "[1] SSH 로그인 통계"
echo "  성공: $(sshpass -p1 ssh ccc@$IP 'grep -c "Accepted" /var/log/auth.log 2>/dev/null || echo 0')"
echo "  실패: $(sshpass -p1 ssh ccc@$IP 'grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo 0')"

echo ""
echo "[2] 무차별 대입 의심 IP (10회 이상 실패)"
sshpass -p1 ssh ccc@$IP "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | awk '\$1>=10 {print \"  \" \$1 \"회: \" \$2}'"  # 텍스트 필드 처리

echo ""
echo "[3] sudo 사용 현황"
sshpass -p1 ssh ccc@$IP "grep 'sudo:' /var/log/auth.log 2>/dev/null | wc -l | xargs -I{} echo '  총 {}건'"  # 비밀번호 자동입력 SSH

echo ""
echo "[4] 시스템 오류"
sshpass -p1 ssh ccc@$IP "grep -i 'error\|critical\|emergency' /var/log/syslog 2>/dev/null | wc -l | xargs -I{} echo '  총 {}건'"  # 비밀번호 자동입력 SSH

echo ""
echo "[5] 최근 패키지 변경"
sshpass -p1 ssh ccc@$IP "tail -5 /var/log/dpkg.log 2>/dev/null || echo '  dpkg 로그 없음'"  # 비밀번호 자동입력 SSH
```

### 7.2 실습: 4개 서버 로그 비교 분석

```bash
# 모든 서버에서 로그 요약 수집
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip =========="
  echo -n "SSH 실패: "
  ssh $srv  # srv=user@ip (아래 루프 참고) "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "SSH 성공: "
  ssh $srv  # srv=user@ip (아래 루프 참고) "grep -c 'Accepted' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "sudo 사용: "
  ssh $srv  # srv=user@ip (아래 루프 참고) "grep -c 'sudo:' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "에러 수: "
  ssh $srv  # srv=user@ip (아래 루프 참고) "grep -ci 'error' /var/log/syslog 2>/dev/null || echo '0'"
done
```

---

## 8. 핵심 정리

1. **auth.log** = SOC 분석의 최우선 로그 (SSH, sudo, 인증)
2. **syslog** = 시스템 전반 이벤트 (서비스 장애, 커널)
3. **journalctl** = systemd 기반 구조화된 로그 검색
4. **auditd** = 커널 수준 상세 감사 (syscall, 파일 접근)
5. **패턴 식별** = 무차별 대입, 권한 상승, 비정상 접근

---

## 과제

1. 4개 서버의 auth.log를 분석하여 무차별 대입 공격 의심 IP를 보고하시오
2. journalctl을 사용하여 최근 1시간의 경고(warning) 이상 이벤트를 수집하시오
3. 로그 분석 스크립트를 작성하여 4개 서버의 보안 상태를 한눈에 파악할 수 있게 하시오

---

## 참고 자료

- Linux System Administration: Log Management
- SANS Logging Cheat Sheet
- auditd Configuration Guide

---

---

## 웹 UI 실습: Wazuh Dashboard 탐색

> **목적**: CLI에서 분석한 시스템 로그를 Wazuh Dashboard에서 검색하고 시각화하는 방법을 익힌다.

### 접속

1. 브라우저에서 `https://10.20.30.100` 접속
2. 자체 서명 인증서 경고 → "고급" → "계속 진행"
3. admin / 비밀번호 입력

### 실습 1: Dashboard 메뉴 구조 탐색

1. 로그인 후 좌측 메뉴 전체를 펼쳐 확인
2. 다음 메뉴 경로를 순서대로 클릭하여 각 화면이 무엇을 보여주는지 파악:
   - **Wazuh** > **Overview**: 전체 현황 대시보드
   - **Wazuh** > **Events**: 보안 이벤트 목록 (검색/필터)
   - **Wazuh** > **Agents**: 에이전트 목록 및 상태
   - **Wazuh** > **MITRE ATT&CK**: ATT&CK 매핑 뷰
   - **Management** > **Rules**: 탐지 규칙 관리
3. 각 화면의 역할을 메모

### 실습 2: 알림 조회 및 필터링

1. **Wazuh** > **Events** 이동
2. 시간 범위를 "Last 24 hours"로 설정
3. 검색창에 다음 필터를 하나씩 입력하여 결과 비교:
   - `rule.groups: sshd` → SSH 관련 이벤트만 표시
   - `rule.level >= 8` → 높은 위험도 알림만 표시
   - `agent.name: bastion` → bastion 서버 이벤트만 표시
4. CLI의 `grep 'Failed password' auth.log` 결과와 Dashboard의 SSH 실패 이벤트 수를 비교

### 실습 3: 시각화 차트 읽기

1. **Overview** 화면에서 "Alert level evolution" 그래프 확인
2. 시간대별 알림 급증 구간이 있는지 확인 → 급증 시간대를 클릭하여 상세 이벤트 조회
3. "Top 5 agents" 차트에서 알림이 가장 많은 에이전트 확인
4. CLI에서 `wc -l`로 센 에이전트별 알림 수와 비교

> **핵심**: Dashboard의 검색 기능은 CLI의 `grep | sort | uniq -c`와 같은 역할을 하지만,
> 시각화를 통해 패턴을 더 빠르게 파악할 수 있다.

---
---

> **실습 환경 검증 완료** (2026-03-28): Wazuh alerts.json/logtest/agent_control, SIGMA 룰, 경보 분석

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Wazuh SIEM (4.11.x)
> **역할:** 에이전트 기반 로그·FIM·SCA 통합 분석 플랫폼  
> **실행 위치:** `siem (10.20.30.100)`  
> **접속/호출:** Dashboard `https://10.20.30.100` (admin/admin), Manager API `:55000`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/var/ossec/etc/ossec.conf` | Manager 메인 설정 (원격, 전송, syscheck 등) |
| `/var/ossec/etc/rules/local_rules.xml` | 커스텀 룰 (id ≥ 100000) |
| `/var/ossec/etc/decoders/local_decoder.xml` | 커스텀 디코더 |
| `/var/ossec/logs/alerts/alerts.json` | 실시간 JSON 알림 스트림 |
| `/var/ossec/logs/archives/archives.json` | 전체 이벤트 아카이브 |
| `/var/ossec/logs/ossec.log` | Manager 데몬 로그 |
| `/var/ossec/queue/fim/db/fim.db` | FIM 기준선 SQLite DB |

**핵심 설정·키**

- `<rule id='100100' level='10'>` — 커스텀 룰 — level 10↑은 고위험
- `<syscheck><directories>...` — FIM 감시 경로
- `<active-response>` — 자동 대응 (firewall-drop, restart)

**로그·확인 명령**

- `jq 'select(.rule.level>=10)' alerts.json` — 고위험 알림만
- `grep ERROR ossec.log` — Manager 오류 (룰 문법 오류 등)

**UI / CLI 요점**

- Dashboard → Security events — KQL 필터 `rule.level >= 10`
- Dashboard → Integrity monitoring — 변경된 파일 해시 비교
- `/var/ossec/bin/wazuh-logtest` — 룰 매칭 단계별 확인 (Phase 1→3)
- `/var/ossec/bin/wazuh-analysisd -t` — 룰·설정 문법 검증

> **해석 팁.** Phase 3에서 원하는 `rule.id`가 떠야 커스텀 룰 정상. `local_rules.xml` 수정 후 `systemctl restart wazuh-manager`, 문법 오류가 있으면 **분석 데몬 전체가 기동 실패**하므로 `-t`로 먼저 검증.

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041` 패턴

```
src=100.64.4.210 dst=172.22.195.168 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.84
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041` 패턴

```
src=172.22.36.156 dst=100.64.9.98 tech=T1041 mo_name=Data Theft
tactic=TA0010 (Exfiltration) suspicion=0.92
lifecycle=complete-mission
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

