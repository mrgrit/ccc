# Week 11: 1v1 공방전 실전 (1) -- 공격자 정찰 vs 방어자 탐지

## 학습 목표
- 1v1 공방전의 규칙, 시간 제한, 점수 체계를 완전히 이해하고 참여할 수 있다
- 공격자(Red) 관점에서 제한 시간 내 효율적인 정찰 전략을 수립하고 실행할 수 있다
- 방어자(Blue) 관점에서 정찰 행위를 실시간으로 탐지하고 초기 대응을 수행할 수 있다
- 공격-방어 양측의 행위를 동시에 관찰하며 공방 역학(Attack-Defense Dynamics)을 이해한다
- 공방전 환경에서 시간 압박 하에 우선순위를 정하고 의사결정하는 능력을 기른다
- 실시간 로그 모니터링과 IDS 알림을 활용하여 공격 징후를 조기에 발견할 수 있다
- 정찰 결과를 구조적으로 정리하여 후속 공격 계획을 수립할 수 있다

## 전제 조건
- Week 01~08의 공격/방어 기법 복습 완료
- Week 09 인시던트 대응 프레임워크 이해
- Week 10 하드닝 체크리스트 실행 경험
- 실습 인프라 접속 확인 (opsclaw, secu, web, siem)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 공방전 규칙/점수 체계 + 전략 브리핑 | 강의 |
| 0:30-1:00 | Red Team 정찰 전략 + Blue Team 탐지 전략 | 강의 |
| 1:00-1:10 | 휴식 + 환경 준비 | - |
| 1:10-1:50 | 1v1 공방전 Round 1 (공격자 정찰 vs 탐지) | 실습 |
| 1:50-2:30 | 1v1 공방전 Round 2 (역할 교대) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 결과 분석 + 양측 로그 비교 | 실습 |
| 3:10-3:40 | 디브리핑 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 공방전 규칙과 전략 (30분)

## 1.1 1v1 공방전 개요

1v1 공방전은 한 명의 공격자와 한 명의 방어자가 제한된 시간 내에 경쟁하는 실전 훈련이다. 공격자는 대상 시스템의 취약점을 발견하고 침투하려 하며, 방어자는 이를 탐지하고 차단한다.

**MITRE ATT&CK 매핑:**
```
공방전 Phase 1 (이번 주)에서 다루는 전술:
  +-- [Red]  TA0043 Reconnaissance — 정찰
  +-- [Red]  TA0001 Initial Access  — 초기 접근 시도
  +-- [Blue] Detection             — 탐지/알림
  +-- [Blue] Response              — 초기 대응

공방전 Phase 2 (Week 12)에서 다루는 전술:
  +-- [Red]  TA0002 Execution      — 코드 실행
  +-- [Red]  TA0003 Persistence    — 지속성
  +-- [Red]  TA0004 Privilege Escalation — 권한 상승
  +-- [Blue] Containment           — 봉쇄
  +-- [Blue] Eradication           — 근절
```

### 공방전 타임라인

```
[1v1 공방전 타임라인 — Round 1 (40분)]

0:00  시작 신호
  |   Red: 정찰 시작 (ping sweep, 포트 스캔)
  |   Blue: 모니터링 시작 (로그 관찰, IDS 확인)
  |
5:00  Red: 서비스 열거 (배너 그래빙, 버전 확인)
  |   Blue: 스캔 탐지 확인 (Suricata 알림)
  |
10:00 Red: 취약점 식별 (CVE 검색, 스크립트 스캔)
  |   Blue: 차단 결정 (IP 차단? 포트 필터?)
  |
15:00 Red: 초기 공격 시도 (웹 취약점, SSH)
  |   Blue: 차단 조치 + 증거 수집
  |
25:00 Red: 우회 전략 (다른 서비스, 다른 기법)
  |   Blue: 추가 모니터링 + 하드닝 강화
  |
35:00 Red: 마지막 공격 시도
  |   Blue: 최종 방어 상태 확인
  |
40:00 종료 — 점수 산정
```

## 1.2 점수 체계

### Red Team 점수

| 행동 | 점수 | 조건 |
|------|------|------|
| 활성 호스트 식별 | +5 | 정확한 IP별 |
| 열린 포트 식별 | +3 | 정확한 포트별 |
| 서비스 버전 식별 | +5 | 정확한 버전별 |
| OS 식별 | +5 | 정확한 OS별 |
| CVE 식별 | +10 | 실제 존재하는 CVE별 |
| 초기 접근 성공 | +30 | 셸 획득 |
| 탐지 회피 성공 | +15 | Blue가 미탐지 시 |
| 보고서 품질 | +10 | 구조적 정리 |
| **감점** | | |
| Blue 서비스 다운 (DoS) | -20 | 서비스 가용성 침해 |
| 범위 외 공격 | -30 | 규칙 위반 |

### Blue Team 점수

| 행동 | 점수 | 조건 |
|------|------|------|
| 스캔 탐지 | +10 | 5분 이내 탐지 |
| 공격자 IP 식별 | +10 | 정확한 IP |
| 공격 기법 분류 | +10 | ATT&CK 기법별 |
| 차단 조치 성공 | +15 | 효과적 차단 |
| 서비스 가용성 유지 | +10 | 서비스 정상 동작 |
| 증거 수집 | +10 | 로그 보존 |
| 인시던트 보고서 | +10 | NIST IR 형식 |
| **감점** | | |
| 서비스 오중단 | -15 | 방어 과정에서 서비스 끊김 |
| 미탐지 | -10 | 공격을 놓친 경우 |

## 1.3 Red Team 정찰 전략

### 시간 관리 전략

```
[40분 정찰 시간 배분]

Phase 1: 빠른 탐색 (0~5분)
+-- Ping sweep: 전체 서브넷 스캔
+-- Top 100 포트 빠른 스캔
+-- 목표: 호스트/포트 리스트 확보

Phase 2: 심층 열거 (5~15분)
+-- 식별된 호스트의 전체 포트 스캔
+-- 서비스 버전 탐지 (-sV)
+-- OS 핑거프린팅 (-O)
+-- 목표: 서비스 목록 + 버전 정보

Phase 3: 취약점 매핑 (15~25분)
+-- CVE 검색 (서비스 버전 기반)
+-- NSE 취약점 스크립트
+-- 웹 서비스 디렉토리 탐색
+-- 목표: 공격 가능 벡터 목록

Phase 4: 초기 접근 시도 (25~40분)
+-- 가장 유망한 취약점 공격
+-- SSH 브루트포스 (제한적)
+-- 웹 취약점 공격 (SQLi, XSS)
+-- 목표: 초기 셸 획득
```

### 탐지 회피 기법

| 기법 | 방법 | 효과 | 위험 |
|------|------|------|------|
| 느린 스캔 | `-T1` / `-T2` | IDS 임계값 회피 | 시간 소모 |
| Decoy | `-D RND:5` | 진짜 IP 숨김 | 대역폭 소모 |
| 단편화 | `-f` | IDS 패킷 분석 우회 | 현대 IDS는 탐지 |
| 소스 포트 위장 | `--source-port 53` | 방화벽 규칙 우회 | 제한적 효과 |
| 비표준 스캔 | `-sF`, `-sN` | 로그 회피 | 정확도 낮음 |

## 1.4 Blue Team 탐지 전략

### 모니터링 우선순위

```
[Blue Team 모니터링 체크리스트]

즉시 시작 (0~2분):
+-- IDS 대시보드 확인 (Suricata fast.log)
+-- 방화벽 로그 모니터링 시작 (dmesg | grep nft)
+-- auth.log 실시간 모니터링 (tail -f)

지속 관찰 (2~40분):
+-- 네트워크 트래픽 이상 관찰 (ss -tn)
+-- 새로운 연결/포트 활동 감시
+-- 파일 시스템 변경 감시 (inotifywait)
+-- 프로세스 이상 감시 (ps)

대응 (탐지 즉시):
+-- 공격자 IP 기록
+-- 차단 여부 결정 (관찰 vs 차단)
+-- 증거 보존
+-- 추가 모니터링 강화
```

### 탐지 소스와 기법

| 소스 | 위치 | 탐지 대상 | 모니터링 명령 |
|------|------|---------|------------|
| Suricata | secu | 네트워크 IDS 알림 | `tail -f /var/log/suricata/fast.log` |
| nftables | secu | 방화벽 차단 로그 | `dmesg -w \| grep nft` |
| auth.log | web | SSH 인증 시도 | `tail -f /var/log/auth.log` |
| access.log | web | HTTP 요청 | `tail -f /var/log/apache2/access.log` |
| Wazuh | siem | 통합 보안 알림 | Wazuh Dashboard |
| ss/netstat | web | 현재 네트워크 연결 | `watch -n5 'ss -tn'` |

### 방어 의사결정 매트릭스

```
공격 활동 탐지
    |
    +-- 정찰 단계인가?
    |   +-- 예 → 관찰 + 로그 기록 (차단 보류)
    |   |        이유: 공격자의 전체 전략/범위 파악 가능
    |   |
    |   +-- 아니오 → 다음 단계 확인
    |
    +-- 공격 시도인가?
    |   +-- 예 → 즉시 차단 + 증거 수집
    |   |
    |   +-- 아니오 → 계속 관찰
    |
    +-- 침투 성공 가능성?
        +-- 높음 → 격리 + IR 프로세스 (Week 09)
        +-- 낮음 → 하드닝 강화 + 모니터링
```

---

# Part 2: 정찰 전략과 탐지 전략 상세 (30분)

## 2.1 Red Team: 효율적 정찰 워크플로우

### 자동화된 정찰 흐름

```
[정찰 자동화 파이프라인]

Input: 대상 네트워크 CIDR (10.20.30.0/24)
    |
    +- Phase 1: Host Discovery
    |   nmap -sn -T4 → alive_hosts.txt
    |
    +- Phase 2: Port Scan
    |   nmap -sS -T4 -p- → open_ports.txt
    |
    +- Phase 3: Service Enumeration
    |   nmap -sV -sC → services.txt
    |
    +- Phase 4: Vulnerability Mapping
    |   nmap --script=vuln → vulns.txt
    |   searchsploit <service version> → exploits.txt
    |
    +- Output: 공격 우선순위 보고서
        (서비스별 위험도 + CVE + 공격 경로)
```

### 서비스별 정찰 심화

| 서비스 | 정찰 방법 | 찾을 정보 | 공격 연결 |
|--------|---------|---------|---------|
| SSH (22) | 배너, auth-methods | 버전, 인증 방법 | 브루트포스, CVE |
| HTTP (80/443) | 헤더, 디렉토리, robots.txt | 기술 스택, 숨겨진 경로 | SQLi, XSS, LFI |
| JuiceShop (3000) | API 엔드포인트 탐색 | 취약한 기능 | OWASP Top 10 |
| SubAgent (8002) | API 문서, 인증 확인 | API 인증 방식 | 인증 우회, RCE |

## 2.2 Blue Team: 실시간 탐지 워크플로우

### 탐지 임계값 설정

| 이벤트 | 임계값 | 탐지 방법 | 대응 |
|--------|--------|---------|------|
| 포트 스캔 | 10초 내 10포트 이상 | Suricata ET SCAN | 로그 + 관찰 |
| SSH 실패 | 5분 내 5회 이상 | auth.log 분석 | IP 차단 |
| 웹 디렉토리 스캔 | 1분 내 404 20회 이상 | access.log 분석 | Rate limit |
| 취약점 스캔 | NSE 스크립트 패턴 | Suricata 시그니처 | 즉시 차단 |

## 2.3 공방전 환경 설정

### 네트워크 토폴로지

```
[1v1 공방전 네트워크]

                +----------+
                |  opsclaw  | ← 심판/관리 서버
                |10.20.30.201|
                +----+-----+
                     |
        +------------┼------------+
        |            |            |
   +----+----+  +----+----+  +----+----+
   |  secu   |  |   web   |  |  siem   |
   |10.20.30.1|  |10.20.30.80| |10.20.30.100|
   |게이트웨이|  |공격 대상|  |모니터링|
   |IDS/방화벽|  |웹+취약앱|  |Wazuh   |
   +---------+  +---------+  +---------+

Red Team: opsclaw에서 web을 공격
Blue Team: secu + siem에서 web을 방어
```

### 역할별 접근 권한

| 역할 | 접근 가능 서버 | 제한 사항 |
|------|-------------|---------|
| Red Team | opsclaw (공격 기지) | web 직접 SSH 금지 (침투로만 접근) |
| Blue Team | secu, siem, web | opsclaw 접근 금지 |
| 심판 | 전체 서버 | 점수 기록, 규칙 집행 |

---

# Part 3: 1v1 공방전 실습 Round 1 (40분)

## 실습 3.1: Red Team 정찰 실행

### Step 1: Phase 1 -- 빠른 호스트 탐색

> **실습 목적**: 제한 시간 내 대상 네트워크의 활성 호스트를 신속하게 식별한다. 공방전의 첫 1분이 승부를 좌우한다.
>
> **배우는 것**: 시간 효율적인 호스트 탐색, 결과를 즉시 활용 가능한 형태로 저장

```bash
# === Red Team: Phase 1 — 빠른 호스트 탐색 ===
echo "[$(date +%H:%M:%S)] Red Team Phase 1 시작: 호스트 탐색"

# 전체 서브넷 ping sweep (빠른 탐색)
echo 1 | sudo -S nmap -sn -T4 10.20.30.0/24 2>/dev/null | \
  grep "Nmap scan report" | awk '{print $5}' > /tmp/red_targets.txt

echo "[$(date +%H:%M:%S)] 활성 호스트 발견:"
cat /tmp/red_targets.txt
# 예상 출력:
# 10.20.30.1
# 10.20.30.80
# 10.20.30.100
# 10.20.30.201

echo "호스트 수: $(wc -l < /tmp/red_targets.txt)"
echo "[$(date +%H:%M:%S)] Phase 1 완료 (소요 시간: ~3초)"
```

> **결과 해석**:
> - 4개 호스트 발견: secu(1), web(80), siem(100), opsclaw(201)
> - 이 중 공격 대상은 web(80)이 주 목표이다
> - `-T4`로 빠르게 스캔하면 약 2~3초 내에 완료된다
>
> **실전 활용**: 공방전 시작 직후 가장 먼저 수행해야 할 작업이다. 결과를 파일로 저장하여 후속 스캔의 입력으로 사용한다.
>
> **명령어 해설**:
> - `-sn -T4`: Ping Scan만 수행, Aggressive 타이밍
> - `grep "Nmap scan report" | awk '{print $5}'`: IP 주소만 추출하여 파일로 저장
>
> **트러블슈팅**:
> - 호스트가 적게 발견되는 경우: ICMP 차단 → `-Pn` 옵션으로 재스캔
> - nmap 없는 환경: `for i in $(seq 1 254); do ping -c1 -W1 10.20.30.$i &>/dev/null && echo 10.20.30.$i; done`

### Step 2: Phase 2 -- 포트 스캔 및 서비스 열거

> **실습 목적**: 식별된 호스트의 열린 포트와 서비스를 체계적으로 파악한다. 공격 벡터를 결정하는 핵심 단계이다.
>
> **배우는 것**: 시간 효율적인 포트 스캔 전략, 서비스 버전 탐지, 결과 파싱

```bash
# === Red Team: Phase 2 — 포트 스캔 + 서비스 열거 ===
echo "[$(date +%H:%M:%S)] Phase 2 시작: 포트 스캔"

# 주 공격 대상(web)에 대한 전체 포트 스캔
echo 1 | sudo -S nmap -sS -sV -T4 -p- --min-rate=1000 10.20.30.80 \
  -oN /tmp/red_web_full.txt 2>/dev/null

echo "[$(date +%H:%M:%S)] web 서버 스캔 결과:"
grep "open" /tmp/red_web_full.txt | grep -v "^#"
# 예상 출력:
# 22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu-3ubuntu0.6
# 80/tcp   open  http    Apache httpd 2.4.52 ((Ubuntu))
# 3000/tcp open  ppp     Node.js (Express middleware)
# 8002/tcp open  teradataordbms?

# 다른 호스트 빠른 스캔 (상위 포트만)
echo 1 | sudo -S nmap -sS -sV -T4 --top-ports 100 10.20.30.1 10.20.30.100 \
  -oN /tmp/red_others.txt 2>/dev/null

echo "[$(date +%H:%M:%S)] 기타 호스트:"
grep "open" /tmp/red_others.txt | grep -v "^#"

echo "[$(date +%H:%M:%S)] Phase 2 완료"
```

> **결과 해석**:
> - web 서버에 4개 포트 오픈: SSH(22), HTTP(80), JuiceShop(3000), SubAgent(8002)
> - HTTP 서비스가 2개(80, 3000)이므로 웹 공격 벡터가 가장 유망하다
> - `--min-rate=1000`: 초당 최소 1000 패킷으로 빠른 전체 포트 스캔
>
> **실전 활용**: 전체 포트(-p-)를 스캔하면 비표준 포트의 서비스도 발견할 수 있다. 관리자가 비표준 포트를 사용하는 경우가 많으므로 전체 스캔이 중요하다.
>
> **명령어 해설**:
> - `-sS`: SYN 스캔 (스텔스, root 필요)
> - `-sV`: 서비스 버전 탐지
> - `-p-`: 1~65535 전체 포트
> - `--min-rate=1000`: 최소 전송 속도 보장 (빠른 스캔)
> - `-oN`: 일반 텍스트 형태로 결과 저장
>
> **트러블슈팅**:
> - 스캔이 너무 오래 걸리는 경우: `--top-ports 1000`으로 제한
> - filtered 포트가 많은 경우: 방화벽 존재 → ACK 스캔(`-sA`)으로 규칙 파악

### Step 3: Phase 3 -- 취약점 매핑 및 공격 벡터 정리

> **실습 목적**: 발견된 서비스의 취약점을 식별하고 공격 우선순위를 결정한다.
>
> **배우는 것**: NSE 스크립트를 이용한 취약점 스캔, 수동 정찰 기법, 공격 계획 수립

```bash
# === Red Team: Phase 3 — 취약점 매핑 ===
echo "[$(date +%H:%M:%S)] Phase 3 시작: 취약점 매핑"

# HTTP 서비스 상세 조사
echo 1 | sudo -S nmap -sV --script=http-title,http-headers,http-methods \
  -p 80,3000 10.20.30.80 2>/dev/null | grep -A3 "http-"
# 예상 출력:
# | http-title: BunkerWeb (또는 Apache 기본)
# | http-methods: GET HEAD POST OPTIONS
# | http-title: OWASP Juice Shop

# 웹 서비스 수동 정찰
curl -sI http://10.20.30.80:80 2>/dev/null | head -10
# 예상: Server: Apache/2.4.52 (Ubuntu)

curl -sI http://10.20.30.80:3000 2>/dev/null | head -10
# 예상: X-Powered-By: Express

# SSH 인증 방법 확인
echo 1 | sudo -S nmap --script=ssh-auth-methods -p 22 10.20.30.80 2>/dev/null | \
  grep -A3 "ssh-auth"
# 예상: publickey, password ← 비밀번호 인증 가능

# robots.txt 확인
curl -s http://10.20.30.80:80/robots.txt 2>/dev/null
curl -s http://10.20.30.80:3000/robots.txt 2>/dev/null

# 정찰 결과 정리
cat << 'RECON'
=== 공격 벡터 우선순위 ===
1. [HIGH]   JuiceShop (3000) — OWASP 취약 웹 앱
   → SQLi, XSS, 인증 우회, 파일 업로드
2. [MEDIUM] Apache (80)      — 2.4.52 버전
   → CVE 확인, 디렉토리 트래버설, 설정 오류
3. [MEDIUM] SSH (22)         — 비밀번호 인증 허용
   → 브루트포스 (hydra, 제한적 시도)
4. [LOW]    SubAgent (8002)  — API 서비스
   → API 문서 탐색, 인증 우회 시도
RECON

echo "[$(date +%H:%M:%S)] Phase 3 완료"
```

> **결과 해석**:
> - JuiceShop(3000)은 OWASP에서 만든 의도적으로 취약한 웹 앱 → 가장 유망한 공격 벡터
> - SSH가 비밀번호 인증을 허용 → 브루트포스 공격 가능 (단, 시간 소모)
> - `robots.txt`에서 숨겨진 경로를 발견할 수 있다
>
> **실전 활용**: 공격 벡터를 우선순위로 정리하면 제한 시간을 효율적으로 활용할 수 있다.
>
> **명령어 해설**:
> - `--script=http-title,http-headers,http-methods`: 여러 NSE 스크립트 동시 실행
> - `curl -sI`: HTTP HEAD 요청으로 헤더만 수집 (빠름, 로그에 적게 남음)
>
> **트러블슈팅**:
> - NSE 스크립트 오류: `nmap --script-updatedb`로 DB 업데이트
> - curl 타임아웃: `--connect-timeout 3`으로 제한

## 실습 3.2: Blue Team 탐지 실행

### Step 1: 실시간 모니터링 구축

> **실습 목적**: 공격자의 정찰 활동을 실시간으로 탐지하기 위한 모니터링 체계를 구축한다.
>
> **배우는 것**: 다중 로그 소스 동시 모니터링, 이상 징후 식별

```bash
# === Blue Team: 모니터링 시작 ===
echo "[$(date +%H:%M:%S)] Blue Team 모니터링 시작"

# 모니터링 창 설명 (별도 터미널에서 각각 실행)
echo "=== 모니터링 창 구성 ==="
echo "창 1: IDS 알림     → sshpass -p1 ssh secu@10.20.30.1 'tail -f /var/log/suricata/fast.log'"
echo "창 2: SSH 인증     → sshpass -p1 ssh web@10.20.30.80 'tail -f /var/log/auth.log'"
echo "창 3: 웹 로그      → sshpass -p1 ssh web@10.20.30.80 'tail -f /var/log/apache2/access.log'"
echo "창 4: 네트워크 연결 → sshpass -p1 ssh web@10.20.30.80 'watch -n5 ss -tn'"
echo ""

# 한 번에 상태 스냅샷 확인
echo "=== 현재 상태 스냅샷 ==="
echo "[Suricata 최근 알림]"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "tail -5 /var/log/suricata/fast.log 2>/dev/null || echo 'Suricata 로그 없음'"

echo ""
echo "[web 서버 현재 연결]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tn 2>/dev/null | grep -v 'State' | head -10"

echo ""
echo "[web 서버 SSH 최근 로그]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "tail -5 /var/log/auth.log 2>/dev/null || echo '로그 없음'"

echo ""
echo "[서비스 가용성 확인]"
curl -s -o /dev/null -w "Apache(80): %{http_code}  " http://10.20.30.80:80/
curl -s -o /dev/null -w "Juice(3000): %{http_code}\n" http://10.20.30.80:3000/

echo "[$(date +%H:%M:%S)] 모니터링 상태 확인 완료"
```

> **결과 해석**:
> - Suricata 알림: 포트 스캔 탐지 시 "ET SCAN" 패턴의 알림이 표시된다
> - `ss -tn`: 현재 TCP 연결. 비정상적으로 많은 연결이 있으면 스캔 진행 중
> - auth.log: SSH 인증 시도가 급증하면 브루트포스 공격 의심
>
> **실전 활용**: 공방전에서는 최소 3~4개 모니터링 창을 동시에 열어두어야 한다. 하나의 소스만 보면 다른 채널의 공격을 놓칠 수 있다.
>
> **명령어 해설**:
> - `tail -f`: 파일 끝에 추가되는 내용을 실시간으로 출력
> - `watch -n5 'ss -tn'`: 5초마다 TCP 연결 상태 갱신 표시
>
> **트러블슈팅**:
> - Suricata 로그가 없는 경우: 서비스 상태 확인 → `systemctl status suricata`
> - 로그가 너무 많은 경우: `tail -f ... | grep -E 'SCAN|ALERT|Failed'`로 필터링

### Step 2: 스캔 탐지 및 분석

> **실습 목적**: 공격자의 포트 스캔을 탐지하고 유형과 강도를 분석한다.
>
> **배우는 것**: IDS 알림 해석, 스캔 유형 식별, 공격자 프로파일링

```bash
# === Blue Team: 스캔 탐지 분석 ===
echo "[$(date +%H:%M:%S)] 스캔 탐지 분석 시작"

# Suricata 알림에서 스캔 관련 이벤트 추출
echo "[IDS 스캔 탐지 이벤트]"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "grep -iE 'scan|portscan|nmap' /var/log/suricata/fast.log 2>/dev/null | tail -20"
# 예상 출력:
# 04/03/2026-14:10:05 [**] [1:2010936:3] ET SCAN Suspicious inbound to mySQL port 3306 [**]
# 04/03/2026-14:10:05 [**] [1:2002911:6] ET SCAN Potential VNC Scan [**]

# 공격자 IP 식별 (알림에서 가장 빈번한 소스 IP)
echo ""
echo "[공격 소스 IP 분석]"
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "grep -oP '\d+\.\d+\.\d+\.\d+' /var/log/suricata/fast.log 2>/dev/null | \
   sort | uniq -c | sort -rn | head -5"
# 예상 출력:
# 45 10.20.30.201   ← 공격자 (가장 많은 알림)
# 12 10.20.30.80    ← 대상 서버 (응답)

# web 서버에서 연결 패턴 분석
echo ""
echo "[web 서버 연결 패턴]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "ss -tn 2>/dev/null | awk '{print \$5}' | cut -d: -f1 | \
   sort | uniq -c | sort -rn | head -5"

# HTTP 로그에서 비정상 요청 확인
echo ""
echo "[웹 비정상 요청]"
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "tail -100 /var/log/apache2/access.log 2>/dev/null | \
   awk '{print \$9}' | sort | uniq -c | sort -rn"
# 예상 출력: HTTP 상태 코드별 빈도 (404가 많으면 디렉토리 스캔)

echo "[$(date +%H:%M:%S)] 분석 완료"
```

> **결과 해석**:
> - Suricata "ET SCAN" 알림: 포트 스캔이 탐지됨
> - 가장 많은 알림을 발생시킨 IP가 공격자이다
> - HTTP 404가 다수: 디렉토리/파일 열거 시도 (gobuster, dirb 패턴)
>
> **실전 활용**: 공격자 IP를 식별한 후 차단 여부를 결정해야 한다. 즉시 차단하면 공격자의 전체 전략을 파악할 수 없고, 너무 늦으면 침투당할 수 있다.
>
> **명령어 해설**:
> - `grep -oP '\d+\.\d+\.\d+\.\d+'`: IP 주소 패턴만 추출 (Perl 정규식)
> - `sort | uniq -c | sort -rn`: 빈도순 정렬 (가장 많은 것 먼저)
>
> **트러블슈팅**:
> - IP가 여러 개인 경우: Decoy 스캔 가능성 → 시간 패턴으로 진짜 IP 식별

### Step 3: 차단 조치 실행

> **실습 목적**: 식별된 공격에 대해 적절한 차단 조치를 수행한다.
>
> **배우는 것**: 상황별 차단 전략 선택, nftables 동적 규칙, Rate Limiting

```bash
# === Blue Team: 차단 조치 ===
echo "[$(date +%H:%M:%S)] 차단 전략 결정"

ATTACKER_IP="10.20.30.201"

# 전략 1: Rate Limiting (정찰 단계 — 관찰 유지하면서 속도 제한)
echo "=== 전략 1: Rate Limiting (권장 — 정찰 단계) ==="
echo "nft add rule inet filter input ip saddr $ATTACKER_IP limit rate 10/second accept"
echo "nft add rule inet filter input ip saddr $ATTACKER_IP drop"
echo "효과: 초당 10개 패킷만 허용, 스캔 속도 대폭 감소"

# 전략 2: 선별 차단 (특정 공격만 차단)
echo ""
echo "=== 전략 2: 선별 차단 (취약 서비스 보호) ==="
echo "nft add rule inet filter input ip saddr $ATTACKER_IP tcp dport 3000 drop"
echo "효과: JuiceShop만 차단, SSH/HTTP는 관찰 유지"

# 전략 3: 완전 차단 (공격 시도 확인 후)
echo ""
echo "=== 전략 3: 완전 차단 (공격 확인 후) ==="
echo "nft add rule inet filter input ip saddr $ATTACKER_IP drop"
echo "효과: 모든 트래픽 차단 — 공격 완전 중단"

# 서비스 가용성 확인 (차단 후)
echo ""
echo "=== 서비스 가용성 확인 ==="
HTTP_80=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:80/)
HTTP_3000=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:3000/)
echo "Apache(80):     $HTTP_80"
echo "JuiceShop(3000): $HTTP_3000"

echo ""
echo "[$(date +%H:%M:%S)] 차단 전략 시뮬레이션 완료"
echo "실제 차단은 상황 판단 후 적용 (서비스 가용성 유지 필수)"
```

> **결과 해석**:
> - Rate Limiting: 스캔 속도를 제한하면서도 정상 접근은 허용. 정찰 단계에서 최적
> - 선별 차단: 가장 취약한 서비스만 보호. 서비스 가용성에 영향 최소화
> - 완전 차단: 확실한 방어이지만, 공격자가 IP를 바꾸면 무력화됨
>
> **실전 활용**: 공방전에서는 상황에 따라 차단 수준을 단계적으로 높여야 한다. 정찰 → Rate Limiting, 공격 시도 → 선별 차단, 침투 시도 → 완전 차단.
>
> **명령어 해설**:
> - `nft add rule ... limit rate 10/second accept`: 초당 10패킷 이하만 수락
> - 뒤에 오는 `drop` 규칙이 초과분을 차단한다
>
> **트러블슈팅**:
> - 자기 IP를 차단한 경우: 콘솔 접근으로 `nft delete rule ...` 또는 `nft flush ruleset`
> - Rate Limiting 효과 없음: 공격자가 매우 느린 스캔 사용 → 임계값을 1/second로 낮춤

---

# Part 4: 결과 분석 + 디브리핑 (30분)

## 실습 4.1: 양측 로그 비교 분석

### Step 1: Red Team 활동 기록 정리

> **실습 목적**: Red Team의 정찰 활동을 시간순으로 정리하고 성과를 평가한다.
>
> **배우는 것**: 정찰 결과의 체계적 정리, 공격 보고서 작성, 점수 자가 평가

```bash
# === 결과 분석: Red Team 정찰 보고서 ===
echo "================================================="
echo "  Red Team 정찰 보고서"
echo "  작성 시간: $(date)"
echo "================================================="

# 발견한 호스트
echo ""
echo "[호스트 식별 (+5점 x N)]"
if [ -f /tmp/red_targets.txt ]; then
  HOSTS=$(wc -l < /tmp/red_targets.txt)
  cat /tmp/red_targets.txt
  echo "  총 ${HOSTS}개 → $(( HOSTS * 5 ))점"
else
  echo "  타겟 파일 없음"
fi

# 발견한 서비스
echo ""
echo "[서비스 식별 (+3점/포트, +5점/버전)]"
if [ -f /tmp/red_web_full.txt ]; then
  grep "open" /tmp/red_web_full.txt | grep -v "^#" | \
    awk '{printf "  %-15s %-10s %s\n", $1, $3, $4" "$5}'
  PORTS=$(grep "open" /tmp/red_web_full.txt | grep -v "^#" | wc -l)
  echo "  포트: ${PORTS}개 → $(( PORTS * 3 ))점"
  echo "  버전: ${PORTS}개 → $(( PORTS * 5 ))점 (정확도에 따라)"
fi

# 점수 요약
echo ""
echo "[점수 요약 (자가 평가)]"
HOSTS=${HOSTS:-0}
PORTS=${PORTS:-0}
TOTAL=$(( HOSTS * 5 + PORTS * 3 + PORTS * 5 ))
echo "  호스트:     $HOSTS x 5 = $(( HOSTS * 5 ))점"
echo "  포트:       $PORTS x 3 = $(( PORTS * 3 ))점"
echo "  버전:       $PORTS x 5 = $(( PORTS * 5 ))점"
echo "  보고서:     +10점 (구조적 작성)"
echo "  -----------------------------"
echo "  예상 합계:  $(( TOTAL + 10 ))점+"
```

> **결과 해석**:
> - 호스트당 5점, 포트당 3점, 버전 식별당 5점으로 기본 점수를 산정한다
> - 보고서를 구조적으로 작성하면 추가 10점
> - 탐지를 회피했다면 +15점 보너스
>
> **실전 활용**: 정찰 보고서는 후속 공격(Week 12)의 계획서가 된다. 발견한 모든 정보를 빠짐없이 기록한다.

### Step 2: Blue Team 탐지 기록 정리

> **실습 목적**: Blue Team의 탐지 활동을 시간순으로 정리하고 방어 성과를 평가한다.
>
> **배우는 것**: 탐지 보고서 작성, 방어 효과 측정

```bash
# === 결과 분석: Blue Team 탐지 보고서 ===
echo "================================================="
echo "  Blue Team 탐지 보고서"
echo "  작성 시간: $(date)"
echo "================================================="

# IDS 탐지 이벤트 수
echo ""
echo "[IDS 탐지 (+10점)]"
IDS_COUNT=$(sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "grep -c 'ET SCAN' /var/log/suricata/fast.log 2>/dev/null || echo 0")
echo "  Suricata 스캔 탐지 이벤트: ${IDS_COUNT}건"
[ "$IDS_COUNT" -gt 0 ] && echo "  → 스캔 탐지 성공 (+10점)" || echo "  → 탐지 실패 (-10점)"

# 공격자 IP 식별
echo ""
echo "[공격자 IP 식별 (+10점)]"
echo "  식별된 공격자: 10.20.30.201 (opsclaw)"

# 서비스 가용성 확인
echo ""
echo "[서비스 가용성 (+10점)]"
HTTP_80=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:80/)
HTTP_3000=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://10.20.30.80:3000/)
echo "  Apache(80):     HTTP $HTTP_80"
echo "  JuiceShop(3000): HTTP $HTTP_3000"
if [ "$HTTP_80" = "200" ] || [ "$HTTP_80" = "403" ]; then
  echo "  → 서비스 가용성 유지 (+10점)"
else
  echo "  → 서비스 이상 감지 (-15점)"
fi

# 점수 요약
echo ""
echo "[점수 요약 (자가 평가)]"
echo "  스캔 탐지:     +10점"
echo "  IP 식별:       +10점"
echo "  서비스 유지:   +10점"
echo "  증거 수집:     +10점 (로그 보존)"
echo "  보고서:        +10점"
echo "  -----------------------------"
echo "  예상 합계:     50점+"
```

> **실전 활용**: Blue Team 보고서는 NIST IR 형식으로 작성하면 추가 점수를 받을 수 있다. 탐지-분석-대응의 전 과정을 시간순으로 문서화한다.

### Step 3: 양측 비교 분석 및 교훈

> **실습 목적**: Red Team과 Blue Team의 활동을 대조하여 공방 역학을 분석한다.
>
> **배우는 것**: 공격-방어 타임라인 대조, 탐지 갭 분석, 상호 개선점 도출

```bash
# === 공방 비교 분석 ===
cat << 'ANALYSIS'
=== 공방전 Round 1 비교 분석 ===

시간    Red Team 활동              Blue Team 탐지          결과
------------------------------------------------------------
0:00    Ping sweep 시작           모니터링 시작            -
0:01    호스트 4개 발견            (탐지 안 됨)            미탐지
0:02    SYN 스캔 시작              IDS: ET SCAN 알림       탐지 (2분)
0:05    서비스 버전 탐지            (정상 연결처럼 보임)     미탐지
0:08    HTTP 헤더 수집             access.log: 요청 확인    탐지
0:10    NSE 스크립트               IDS: Nmap 시그니처      탐지
0:15    취약점 매핑 완료            차단 검토 시작          -
0:20    JuiceShop 접근 시도         access.log: 비정상      탐지
0:25    SSH 접속 시도               auth.log: Failed        탐지
0:30    공격 전략 수립              방어 체계 강화          -

탐지율:          70% (7/10 활동 탐지)
평균 탐지 시간:   2.5분
미탐지 활동:      Ping sweep, 서비스 버전 탐지 (정상 트래픽과 유사)

=== 양측 교훈 ===

Red Team 교훈:
  1. 빠른 스캔(-T4)은 IDS에 즉시 탐지됨 → -T2 또는 Decoy 필요
  2. 웹 정찰(curl)은 정상 트래픽과 유사하여 탐지 어려움 → 활용 가치 높음
  3. NSE 스크립트는 시그니처가 알려져 있어 탐지됨 → 수동 대안 필요

Blue Team 교훈:
  1. Ping sweep 탐지를 위한 추가 Suricata 규칙 필요
  2. 서비스 버전 탐지는 정상 연결과 구분 어려움 → 행위 기반 분석 필요
  3. 자동화된 알림/차단 시스템이 없으면 대응이 늦음
ANALYSIS
```

> **실전 활용**: 이 비교 분석은 양측이 서로의 전략을 이해하고 Week 12의 침투/차단에 대비하는 핵심 자료이다.

## 실습 4.2: OpsClaw 결과 기록

### Step 1: 공방전 결과 기록

> **실습 목적**: 공방전 결과를 OpsClaw에 기록하여 추적 가능하게 한다.
>
> **배우는 것**: OpsClaw completion-report를 이용한 결과 문서화

```bash
# 공방전 프로젝트 생성 + 보고서
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week11-battle-r1","request_text":"1v1 공방전 Phase 1","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "1v1 공방전 Phase 1 완료 — 정찰 vs 탐지",
    "outcome": "success",
    "work_details": [
      "Red: Ping sweep -> 포트 스캔 -> 서비스 열거 -> 취약점 매핑",
      "Blue: IDS 모니터링 -> 스캔 탐지 -> 공격자 IP 식별 -> 차단 전략",
      "탐지율: 70%, 평균 탐지 시간: 2.5분",
      "교훈: 빠른 스캔은 탐지됨, 웹 정찰은 회피 용이, 자동 알림 필요"
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'보고서: {d.get(\"status\",\"ok\")}')"
```

> **결과 해석**: OpsClaw에 공방전 결과가 기록되어 이후 분석과 개선에 활용할 수 있다.

---

## 검증 체크리스트
- [ ] 1v1 공방전의 Red/Blue 점수 체계를 이해하고 설명할 수 있는가
- [ ] Red Team 정찰의 4단계(탐색→스캔→열거→매핑)를 시간 내에 수행할 수 있는가
- [ ] nmap 결과를 공격 우선순위 보고서로 정리할 수 있는가
- [ ] Blue Team 다중 소스 모니터링(IDS, auth.log, access.log)을 설정할 수 있는가
- [ ] IDS 알림에서 공격자 IP를 식별하고 스캔 유형을 분류할 수 있는가
- [ ] 상황에 적절한 차단 전략(Rate Limiting/선별/완전)을 선택할 수 있는가
- [ ] Red Team과 Blue Team의 활동을 시간순으로 대조 분석할 수 있는가
- [ ] 공방 결과에서 양측의 교훈을 도출하고 문서화할 수 있는가

## 자가 점검 퀴즈

1. 공방전에서 Red Team이 첫 5분 내에 수행해야 할 정찰 활동을 순서대로 나열하라.

2. Blue Team이 정찰 단계에서 즉시 차단하지 않고 관찰을 유지하는 전략적 이유를 설명하라.

3. SYN 스캔(-sS)이 Suricata에 탐지되는 메커니즘과, Red Team이 이를 회피하는 방법 2가지를 설명하라.

4. nftables Rate Limiting의 원리와 한계를 설명하라. Red Team이 이를 우회하는 방법은?

5. "탐지율"과 "탐지 지연 시간"이 각각 왜 중요한지 설명하라.

6. Red Team의 "Decoy 스캔"을 Blue Team이 식별하는 방법을 설명하라.

7. 공방전에서 서비스 가용성 점수가 존재하는 이유를 설명하라.

8. `--min-rate=1000`과 `-T5` 옵션의 차이를 설명하라.

9. Blue Team이 동시에 모니터링해야 할 로그 소스 5가지와 각각의 탐지 대상을 설명하라.

10. Round 1에서 배운 교훈을 바탕으로 Week 12에서 양측이 개선해야 할 점을 각각 3가지씩 제시하라.

## 과제

### 과제 1: 공방전 보고서 (필수)
- Round 1 또는 Round 2의 역할에서 수행한 활동을 시간순으로 정리
- 사용한 명령어, 결과, 의사결정 근거를 포함
- 점수 자가 평가와 다음 라운드 개선 계획을 포함
- 최소 1,000자 이상

### 과제 2: 자동화 정찰 스크립트 (선택)
- 대상 네트워크를 입력받아 Phase 1~3 정찰을 자동 수행하는 bash 스크립트 작성
- 결과를 공격 우선순위 보고서 형태로 자동 출력
- 시간 제한(timeout) 기능 포함

### 과제 3: 자동화 탐지/대응 스크립트 (도전)
- 다중 로그 소스를 동시에 모니터링하는 스크립트 작성
- 스캔 탐지 시 자동 알림 + IP 기록
- 임계값 초과 시 자동 Rate Limiting 적용 옵션
- 활동 기록을 타임라인 형태로 자동 저장
