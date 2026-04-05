# Week 01: 정찰 기초 — 네트워크 스캐닝

## 학습 목표
- 네트워크 정찰(Reconnaissance)의 개념과 공방전에서의 전략적 중요성을 이해한다
- MITRE ATT&CK 프레임워크에서 정찰 전술(TA0043)의 기법들을 분류하고 설명할 수 있다
- nmap의 다양한 스캔 기법(SYN, Connect, UDP, FIN, NULL, Xmas)의 동작 원리와 차이를 이해한다
- ping sweep, ARP 스캔, TCP 포트 스캔을 활용하여 네트워크 내 활성 호스트와 서비스를 체계적으로 식별할 수 있다
- 서비스 배너 그래빙과 OS 핑거프린팅으로 대상 시스템의 상세 정보를 수집할 수 있다
- 스캔 결과를 구조적으로 정리하여 공격 표면 분석 보고서를 작성할 수 있다
- Blue Team 관점에서 스캔 행위를 탐지하고 대응하는 방법을 이해한다

## 전제 조건
- 리눅스 터미널 기본 명령어 (ls, cd, cat, grep, awk)
- TCP/IP 네트워크 기본 개념 (IP 주소, 서브넷, 포트, 프로토콜)
- SSH 접속 경험 및 실습 인프라 접속 확인 완료
- 3-way handshake (SYN → SYN-ACK → ACK) 동작 원리 이해

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 네트워크 정찰 이론 + ATT&CK 매핑 | 강의 |
| 0:40-1:10 | nmap 스캔 기법 상세 분석 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 호스트 탐색 + 포트 스캐닝 실습 | 실습 |
| 2:00-2:30 | 서비스/OS 탐지 + 결과 분석 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 정찰 실습 + 공격 표면 보고서 | 실습 |
| 3:10-3:40 | Blue Team 대응 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 네트워크 정찰 이론 (40분)

## 1.1 정찰(Reconnaissance)이란?

정찰은 공격의 첫 번째 단계로, 대상 시스템과 네트워크에 대한 정보를 체계적으로 수집하는 과정이다. 모든 성공적인 공격은 철저한 정찰에서 시작되며, 방어 역시 자산에 대한 정확한 이해에서 출발한다.

**MITRE ATT&CK 매핑:**
```
전술: TA0043 — Reconnaissance (정찰)
  +-- T1595 — Active Scanning (능동 스캐닝)
  |     +-- T1595.001 — Scanning IP Blocks
  |     +-- T1595.002 — Vulnerability Scanning
  +-- T1592 — Gather Victim Host Information
  |     +-- T1592.001 — Hardware
  |     +-- T1592.002 — Software
  |     +-- T1592.004 — Client Configurations
  +-- T1590 — Gather Victim Network Information
  |     +-- T1590.001 — Domain Properties
  |     +-- T1590.004 — Network Topology
  |     +-- T1590.005 — IP Addresses
  +-- T1593 — Search Open Websites/Domains
```

### 왜 정찰이 중요한가?

공방전에서 정찰은 **승패를 결정짓는 핵심 단계**이다. 모의해킹의 킬 체인(Kill Chain)에서 정찰이 실패하면 이후 단계가 모두 비효율적이거나 불가능해진다.

```
정찰 → 무기화 → 전달 → 악용 → 설치 → C2 → 목표달성
 ↑
 여기서 실패하면 이후 단계 전부 차질
```

**통계 기반 근거:**
- 성공한 침투 테스트의 80% 이상은 정찰 단계에서 핵심 정보를 확보한 경우 (SANS 2024)
- 평균 정찰 소요 시간: 전체 모의해킹 기간의 40~60%
- Red Team 작전에서 정찰 미흡으로 실패한 비율: 35% (MITRE 2023 보고서)

### 정찰의 분류

| 유형 | 설명 | 기법 예시 | 탐지 난이도 | ATT&CK 매핑 |
|------|------|---------|------------|-------------|
| **수동 정찰 (Passive)** | 대상과 직접 통신하지 않음 | OSINT, DNS 조회, WHOIS, Google Dork | 매우 어려움 | T1593, T1596 |
| **능동 정찰 (Active)** | 대상에 직접 패킷 전송 | 포트 스캔, 배너 그래빙, 취약점 스캔 | 탐지 가능 | T1595 |
| **반수동 정찰 (Semi-passive)** | 간접적 통신 | DNS 역방향 조회, Shodan 검색 | 어려움 | T1596.005 |

### 공방전에서의 정찰 역할

| 역할 | 정찰 목표 | 활용 방법 |
|------|---------|---------|
| **Red Team (공격)** | 대상의 공격 표면 파악 | 열린 포트, 서비스 버전, 취약점 식별 → 침투 경로 설계 |
| **Blue Team (방어)** | 자산 목록과 노출 서비스 파악 | 불필요한 포트 차단, 패치 우선순위 설정, 모니터링 강화 |
| **Purple Team (통합)** | 양측의 시야 확보 | 공격자 관점 + 방어자 관점 동시 평가 |

## 1.2 네트워크 정찰의 단계별 접근

체계적인 정찰은 다음 단계로 진행된다:

```
[Phase 1] 호스트 탐색 (Host Discovery)
    "이 네트워크에 어떤 기계가 있는가?"
    ↓
[Phase 2] 포트 스캐닝 (Port Scanning)
    "각 기계에서 어떤 서비스가 동작하는가?"
    ↓
[Phase 3] 서비스 탐지 (Service Enumeration)
    "각 서비스의 정확한 버전과 설정은?"
    ↓
[Phase 4] OS 핑거프린팅 (OS Fingerprinting)
    "어떤 운영체제를 사용하는가?"
    ↓
[Phase 5] 취약점 매핑 (Vulnerability Mapping)
    "알려진 취약점(CVE)이 있는가?"
```

### 공격 표면(Attack Surface) 개념

공격 표면은 공격자가 시스템에 접근할 수 있는 모든 지점의 합이다.

| 공격 표면 요소 | 설명 | 정찰로 확인 가능 여부 |
|--------------|------|-------------------|
| 열린 TCP 포트 | 수신 대기 중인 서비스 | 포트 스캔으로 확인 |
| 열린 UDP 포트 | DNS, SNMP 등 | UDP 스캔으로 확인 |
| 웹 애플리케이션 | HTTP/HTTPS 서비스 | 배너 그래빙, 디렉토리 스캔 |
| 인증 인터페이스 | SSH, FTP, 관리 콘솔 | 서비스 탐지로 확인 |
| API 엔드포인트 | REST/GraphQL API | HTTP 응답 분석 |
| SSL/TLS 설정 | 인증서, 암호 스위트 | SSL 스캔으로 확인 |

## 1.3 TCP/IP 기초 복습 — 스캐닝 이해를 위한 필수 지식

### TCP 3-way Handshake

포트 스캔을 이해하려면 TCP 연결 수립 과정을 정확히 알아야 한다.

```
클라이언트                    서버
    |                          |
    |---- SYN (seq=100) ------>|   1단계: 연결 요청
    |                          |
    |<-- SYN-ACK (seq=200,     |   2단계: 요청 수락
    |    ack=101) -------------|
    |                          |
    |---- ACK (ack=201) ------>|   3단계: 연결 확립
    |                          |
    |===== 데이터 교환 ========|   연결 완료
```

### TCP 플래그 요약

| 플래그 | 약자 | 의미 | 스캔에서의 용도 |
|--------|------|------|---------------|
| SYN | S | 연결 요청 | SYN 스캔의 핵심 |
| ACK | A | 수신 확인 | ACK 스캔 (방화벽 탐지) |
| FIN | F | 연결 종료 | FIN 스캔 (스텔스) |
| RST | R | 연결 강제 종료 | 포트 닫힘 표시 |
| PSH | P | 즉시 전달 | - |
| URG | U | 긴급 데이터 | - |
| NULL | - | 플래그 없음 | NULL 스캔 |
| Xmas | FPU | FIN+PSH+URG | Xmas 스캔 |

### 포트 상태 해석

| nmap 표시 | 의미 | TCP 응답 | 해석 |
|-----------|------|---------|------|
| `open` | 서비스 수신 대기 중 | SYN-ACK 수신 | 공격 가능 지점 |
| `closed` | 포트 닫힘 | RST 수신 | 호스트 살아 있음 확인 |
| `filtered` | 방화벽에 의해 차단 | 응답 없음 또는 ICMP 도달불가 | 방화벽 존재 추정 |
| `unfiltered` | ACK 스캔에서 접근 가능 | RST 수신 (ACK 스캔 시) | 방화벽 통과 확인 |
| `open|filtered` | 열린지 필터링인지 불확실 | 응답 없음 (UDP 스캔 등) | 추가 확인 필요 |

---

# Part 2: nmap 스캔 기법 상세 분석 (30분)

## 2.1 호스트 탐색(Host Discovery) 기법

### ICMP 기반 탐색

```
스캐너 ---- ICMP Echo Request ----> 대상 호스트
          ← ICMP Echo Reply ------
결과: 호스트 활성 확인

주의: 많은 방화벽이 ICMP를 차단함 → 이것만으로는 부족
```

### ARP 기반 탐색 (같은 서브넷)

```
스캐너 ---- ARP Request (who has 10.20.30.80?) ----> 브로드캐스트
          ← ARP Reply (10.20.30.80 is at AA:BB:CC:DD:EE:FF) --
결과: 호스트 활성 + MAC 주소 확인

장점: 방화벽으로 차단 불가 (Layer 2)
단점: 같은 서브넷에서만 동작
```

### TCP 기반 탐색

```
스캐너 ---- TCP SYN (포트 80) ----> 대상 호스트
          ← TCP SYN-ACK --------- (포트 열림)
          ← TCP RST ------------ (포트 닫힘, 그러나 호스트 존재)
결과: ICMP 차단 환경에서도 호스트 확인 가능
```

### nmap 호스트 탐색 옵션 비교

| 옵션 | 기법 | 장점 | 단점 | 사용 시나리오 |
|------|------|------|------|-------------|
| `-sn` | Ping Sweep (ICMP+ARP+TCP) | 빠름, 복합 프로브 | 방화벽 환경에서 미탐 | 초기 전체 스캔 |
| `-sn -PR` | ARP Only | L2 방화벽 우회 | 같은 서브넷만 | 내부 네트워크 |
| `-sn -PE` | ICMP Echo Only | 단순, 빠름 | 많이 차단됨 | ICMP 허용 환경 |
| `-sn -PS80,443` | TCP SYN Ping | 방화벽 우회 | 특정 포트에 의존 | ICMP 차단 환경 |
| `-sn -PA80,443` | TCP ACK Ping | Stateful FW 우회 | 결과 해석 주의 | 엄격한 방화벽 |
| `-Pn` | 탐색 건너뜀 (모두 up 가정) | 놓치는 호스트 없음 | 매우 느림 | 방화벽 강한 환경 |

## 2.2 TCP 포트 스캔 기법 상세

### SYN 스캔 (Half-Open Scan) — `-sS`

가장 널리 사용되는 스캔 기법이다. 완전한 연결을 수립하지 않아 로그에 남기 어렵다.

```
[포트 열림 (open)]
스캐너 -- SYN --> 대상
        ← SYN-ACK --
스캐너 -- RST --> 대상    ← 연결 완료하지 않고 즉시 종료
결과: open

[포트 닫힘 (closed)]
스캐너 -- SYN --> 대상
        ← RST ----
결과: closed

[필터링 (filtered)]
스캐너 -- SYN --> 대상
        (응답 없음 / ICMP 도달불가)
결과: filtered
```

**특징:**
- root/sudo 권한 필요 (raw socket 사용)
- 완전한 연결을 수립하지 않으므로 애플리케이션 레벨 로그에 남지 않음
- 하지만 방화벽/IDS에서는 SYN 패킷을 탐지할 수 있음
- nmap의 기본 스캔 방식 (sudo 실행 시)

### TCP Connect 스캔 — `-sT`

```
[포트 열림 (open)]
스캐너 -- SYN --> 대상
        ← SYN-ACK --
스캐너 -- ACK --> 대상    ← 완전한 3-way handshake
스캐너 -- RST --> 대상    ← 즉시 연결 해제
결과: open — 애플리케이션 로그에 기록됨

[포트 닫힘 (closed)]
스캐너 -- SYN --> 대상
        ← RST ----
결과: closed
```

**특징:**
- 일반 사용자 권한으로 실행 가능 (시스템 connect() 함수 사용)
- 완전한 연결을 수립하므로 대상 애플리케이션의 로그에 기록됨
- SYN 스캔보다 느리고 탐지되기 쉬움
- sudo 없이 nmap 실행 시 기본 방식

### FIN/NULL/Xmas 스캔 — 스텔스 스캔

이 스캔들은 RFC 793의 동작을 이용한다: 닫힌 포트에는 RST로 응답하지만, 열린 포트에는 응답하지 않는다.

```
[FIN 스캔 (-sF)]
스캐너 -- FIN --> 대상 (열린 포트)
        (응답 없음)           → open|filtered

스캐너 -- FIN --> 대상 (닫힌 포트)
        ← RST ----           → closed

[NULL 스캔 (-sN)]
스캐너 -- (플래그 없음) --> 대상 (열린 포트)
        (응답 없음)               → open|filtered

[Xmas 스캔 (-sX)]
스캐너 -- FIN+PSH+URG --> 대상 (열린 포트)
        (응답 없음)              → open|filtered
```

**주의사항:**
- Windows 시스템에서는 제대로 동작하지 않음 (RFC 비준수)
- 결과가 `open|filtered`로 불확실할 수 있음
- 방화벽 우회 가능성이 있지만, 현대 IDS는 이 패턴도 탐지함

### UDP 스캔 — `-sU`

```
[UDP 포트 열림]
스캐너 -- UDP 패킷 --> 대상
        (응답 없음 또는 UDP 응답)   → open 또는 open|filtered

[UDP 포트 닫힘]
스캐너 -- UDP 패킷 --> 대상
        ← ICMP Port Unreachable -- → closed
```

**특징:**
- 매우 느림 (응답 없음 = 타임아웃 대기)
- DNS(53), SNMP(161), DHCP(67/68) 등 UDP 서비스 탐지에 필수
- `-sU`와 `-sS`를 함께 사용하면 TCP+UDP 동시 스캔 가능

### 스캔 기법 비교 종합표

| 기법 | 옵션 | 권한 | 속도 | 정확도 | 탐지 용이성 | 로그 기록 |
|------|------|------|------|--------|------------|---------|
| SYN | `-sS` | root | 빠름 | 높음 | 중간 | 패킷 로그만 |
| Connect | `-sT` | 일반 | 보통 | 높음 | 높음 | 애플리케이션 로그 |
| FIN | `-sF` | root | 보통 | 낮음 | 낮음 | 패킷 로그만 |
| NULL | `-sN` | root | 보통 | 낮음 | 낮음 | 패킷 로그만 |
| Xmas | `-sX` | root | 보통 | 낮음 | 낮음 | 패킷 로그만 |
| UDP | `-sU` | root | 매우 느림 | 중간 | 낮음 | 패킷 로그만 |
| ACK | `-sA` | root | 빠름 | 방화벽용 | 중간 | 패킷 로그만 |

## 2.3 서비스 탐지와 OS 핑거프린팅

### 서비스 배너 그래빙 (Banner Grabbing)

서비스 버전 탐지는 공격자가 알려진 취약점(CVE)을 검색하기 위한 핵심 단계이다.

```
스캐너 -- 연결 --> 대상 포트 22
        ← "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
결과: OpenSSH 8.9p1 → CVE 검색 가능

스캐너 -- HTTP GET --> 대상 포트 80
        ← "Server: Apache/2.4.52 (Ubuntu)"
결과: Apache 2.4.52 → CVE-2023-XXXXX 등 확인
```

### nmap 서비스 탐지 옵션

| 옵션 | 기능 | 상세 |
|------|------|------|
| `-sV` | 서비스 버전 탐지 | 배너 그래빙 + 프로브 전송 |
| `--version-intensity 0-9` | 탐지 강도 조절 | 0=가벼움, 9=모든 프로브 |
| `-sC` | 기본 NSE 스크립트 실행 | 추가 정보 수집 |
| `-A` | 종합 탐지 | -sV -O -sC --traceroute |

### OS 핑거프린팅

nmap은 TCP/IP 스택의 미묘한 차이를 분석하여 OS를 추정한다.

| OS | TTL 기본값 | Window Size | DF 비트 | TCP 옵션 순서 |
|----|-----------|-------------|---------|-------------|
| Linux 5.x+ | 64 | 다양 | 설정됨 | MSS, WS, TS, NOP |
| Windows 10/11 | 128 | 65535 | 설정됨 | MSS, NOP, WS, NOP, NOP, TS |
| macOS | 64 | 65535 | 설정됨 | MSS, NOP, WS, NOP, NOP, TS |
| FreeBSD | 64 | 65535 | 설정됨 | MSS, NOP, WS, SACK, TS |

## 2.4 nmap 타이밍과 성능 옵션

| 옵션 | 템플릿 | 지연 시간 | 사용 시나리오 |
|------|--------|---------|-------------|
| `-T0` | Paranoid | 5분/프로브 | IDS 회피 (실전) |
| `-T1` | Sneaky | 15초/프로브 | IDS 회피 |
| `-T2` | Polite | 0.4초/프로브 | 부하 최소화 |
| `-T3` | Normal | 기본값 | 일반 스캔 |
| `-T4` | Aggressive | 병렬, 빠름 | CTF/실습 |
| `-T5` | Insane | 최대 병렬 | 빠른 결과 필요 시 |

## 2.5 nmap NSE (Nmap Scripting Engine)

NSE는 nmap의 기능을 크게 확장하는 스크립트 엔진이다.

| 카테고리 | 설명 | 스크립트 예시 |
|---------|------|-------------|
| `auth` | 인증 관련 | `ssh-auth-methods` |
| `broadcast` | 브로드캐스트 탐색 | `broadcast-dhcp-discover` |
| `default` | 기본 실행 (`-sC`) | `http-title`, `ssh-hostkey` |
| `discovery` | 추가 정보 수집 | `dns-brute`, `smb-os-discovery` |
| `exploit` | 취약점 공격 | `http-shellshock` |
| `vuln` | 취약점 검사 | `ssl-heartbleed`, `smb-vuln-ms17-010` |
| `safe` | 안전한 스크립트 | 대부분의 정보 수집 |

---

# Part 3: 호스트 탐색 + 포트 스캐닝 실습 (40분)

## 실습 3.1: Ping Sweep로 활성 호스트 탐색

### Step 1: 기본 ICMP ping으로 개별 호스트 확인

> **실습 목적**: 가장 기본적인 네트워크 연결 확인 방법을 익히고, ping 응답에서 얻을 수 있는 정보를 분석한다.
>
> **배우는 것**: ICMP Echo Request/Reply 동작 원리, TTL 값 해석, 응답 시간 분석

```bash
# web 서버 연결 확인
ping -c 4 10.20.30.80
# 예상 출력:
# PING 10.20.30.80 (10.20.30.80) 56(84) bytes of data.
# 64 bytes from 10.20.30.80: icmp_seq=1 ttl=64 time=0.882 ms
# 64 bytes from 10.20.30.80: icmp_seq=2 ttl=64 time=0.654 ms
# 64 bytes from 10.20.30.80: icmp_seq=3 ttl=64 time=0.712 ms
# 64 bytes from 10.20.30.80: icmp_seq=4 ttl=64 time=0.698 ms
# --- 10.20.30.80 ping statistics ---
# 4 packets transmitted, 4 received, 0% packet loss, time 3005ms
# rtt min/avg/max/mdev = 0.654/0.736/0.882/0.085 ms

# secu 서버 연결 확인
ping -c 4 10.20.30.1
# 예상 출력:
# 64 bytes from 10.20.30.1: icmp_seq=1 ttl=64 time=0.453 ms

# siem 서버 연결 확인
ping -c 4 10.20.30.100
# 예상 출력:
# 64 bytes from 10.20.30.100: icmp_seq=1 ttl=64 time=0.512 ms
```

> **결과 해석**:
> - `ttl=64`: TTL(Time To Live)이 64이면 Linux 시스템 (Windows는 128, Cisco는 255)
> - `time=0.882 ms`: 왕복 시간. 1ms 미만이면 같은 네트워크 세그먼트
> - `0% packet loss`: 모든 패킷이 정상 전달됨
> - `rtt min/avg/max/mdev`: 최소/평균/최대/표준편차 — 네트워크 안정성 지표
>
> **실전 활용**: TTL 값으로 OS를 추정할 수 있다. 경유하는 라우터마다 TTL이 1씩 감소하므로, TTL이 63이면 라우터 1개를 경유한 Linux 시스템이다.
>
> **명령어 해설**:
> - `-c 4`: 4개 패킷만 전송 후 종료 (없으면 무한 반복)
> - `56(84) bytes`: 56바이트 ICMP 데이터 + 28바이트 헤더 = 84바이트
>
> **트러블슈팅**:
> - "Destination Host Unreachable": 대상까지의 경로가 없음, 라우팅 확인 필요
> - "Request timeout": 방화벽이 ICMP를 차단하고 있을 수 있음 → TCP ping 시도
> - 100% packet loss: 호스트가 다운이거나 방화벽 차단

### Step 2: nmap Ping Sweep로 전체 서브넷 스캔

> **실습 목적**: 네트워크 전체의 활성 호스트를 한 번에 식별한다. 공방전 시작 직후 가장 먼저 수행해야 할 작업이다.
>
> **배우는 것**: nmap의 호스트 탐색 기능과 복합 프로브 메커니즘

```bash
# nmap ping sweep (ICMP + ARP + TCP 복합)
echo 1 | sudo -S nmap -sn 10.20.30.0/24
# 예상 출력:
# Starting Nmap 7.94 ( https://nmap.org )
# Nmap scan report for 10.20.30.1
# Host is up (0.00045s latency).
# MAC Address: XX:XX:XX:XX:XX:XX (VMware)
# Nmap scan report for 10.20.30.80
# Host is up (0.00088s latency).
# MAC Address: XX:XX:XX:XX:XX:XX (VMware)
# Nmap scan report for 10.20.30.100
# Host is up (0.00051s latency).
# MAC Address: XX:XX:XX:XX:XX:XX (VMware)
# Nmap scan report for 10.20.30.201
# Host is up.
# Nmap done: 256 IP addresses (4 hosts up) scanned in 2.03 seconds
```

> **결과 해석**:
> - `256 IP addresses (4 hosts up)`: /24 서브넷의 256개 IP 중 4개가 활성
> - `latency`: 응답 시간 — 낮을수록 가까운 네트워크
> - `MAC Address`: ARP로 얻은 물리 주소 — VMware 등 가상화 환경 식별 가능
> - 자기 자신(10.20.30.201)은 MAC 없이 표시됨
>
> **실전 활용**: 공방전에서 이 결과로 공격 대상 목록(Target List)을 만든다. 4개 호스트의 IP를 파일로 저장하여 후속 스캔에 활용한다.
>
> **명령어 해설**:
> - `-sn`: Ping Scan (포트 스캔 없이 호스트 탐색만)
> - `10.20.30.0/24`: CIDR 표기. 10.20.30.0~10.20.30.255 범위
> - sudo 사용: ARP 스캔을 위해 raw socket 필요
>
> **트러블슈팅**:
> - "Note: Host seems down": ICMP가 차단된 경우 → `-Pn` 옵션 사용
> - MAC 주소가 표시되지 않음: 다른 서브넷이거나 일반 사용자 권한으로 실행

### Step 3: ARP 전용 스캔과 TCP Ping 비교

> **실습 목적**: 다양한 호스트 탐색 기법을 비교하여 환경에 맞는 최적 기법을 선택할 수 있다.
>
> **배우는 것**: ARP, TCP SYN, TCP ACK ping의 차이와 적용 시나리오

```bash
# ARP 전용 스캔 (같은 서브넷에서 가장 정확)
echo 1 | sudo -S nmap -sn -PR 10.20.30.0/24
# 예상 출력: ARP 기반으로 4개 호스트 탐색 (ICMP 차단 여부와 무관)

# TCP SYN Ping (포트 80, 443으로 SYN 전송)
echo 1 | sudo -S nmap -sn -PS80,443 10.20.30.0/24
# 예상 출력: TCP SYN에 응답한 호스트만 표시

# TCP ACK Ping (Stateful 방화벽 우회 가능)
echo 1 | sudo -S nmap -sn -PA80,443 10.20.30.0/24
# 예상 출력: TCP ACK에 RST로 응답한 호스트 표시

# 결과를 파일로 저장
echo 1 | sudo -S nmap -sn 10.20.30.0/24 -oN /tmp/host_discovery.txt
cat /tmp/host_discovery.txt | grep "Host is up"
# 예상 출력:
# Host is up (0.00045s latency).
# Host is up (0.00088s latency).
# Host is up (0.00051s latency).
# Host is up.
```

> **결과 해석**:
> - ARP 스캔은 Layer 2에서 동작하므로 IP 방화벽으로 차단할 수 없다
> - TCP SYN Ping은 지정한 포트가 열린 호스트만 발견한다
> - TCP ACK Ping은 Stateful 방화벽을 우회할 수 있다 (ACK는 기존 연결로 간주)
>
> **실전 활용**: ICMP가 차단된 환경에서는 TCP Ping이 필수. 공방전에서 Blue Team이 ICMP를 차단하면 Red Team은 TCP/ARP ping으로 전환한다.

### Step 4: 타겟 리스트 생성

> **실습 목적**: 호스트 탐색 결과를 체계적으로 정리하여 후속 스캔에 활용할 수 있는 파일을 만든다.
>
> **배우는 것**: nmap의 입력/출력 파일 활용법

```bash
# 활성 호스트 IP만 추출하여 파일 저장
echo 1 | sudo -S nmap -sn 10.20.30.0/24 -oG /tmp/ping_sweep.gnmap
grep "Status: Up" /tmp/ping_sweep.gnmap | awk '{print $2}' > /tmp/targets.txt
cat /tmp/targets.txt
# 예상 출력:
# 10.20.30.1
# 10.20.30.80
# 10.20.30.100
# 10.20.30.201

# 타겟 파일을 이용한 후속 스캔 준비
wc -l /tmp/targets.txt
# 예상 출력: 4
```

> **결과 해석**: `/tmp/targets.txt`에 4개 활성 호스트의 IP가 저장되었다. 이 파일을 `-iL` 옵션으로 후속 스캔에 활용한다.
>
> **명령어 해설**:
> - `-oG`: Grepable 출력 포맷 (스크립트 파싱에 최적화)
> - `grep "Status: Up"`: 활성 호스트 행만 필터링
> - `awk '{print $2}'`: 두 번째 필드(IP 주소)만 추출

## 실습 3.2: TCP 포트 스캔 실습

### Step 1: 기본 포트 스캔 (상위 1000개 포트)

> **실습 목적**: 대상 호스트의 열린 포트를 식별하여 실행 중인 서비스를 파악한다.
>
> **배우는 것**: nmap 기본 포트 스캔의 동작과 결과 해석

```bash
# web 서버 기본 포트 스캔
echo 1 | sudo -S nmap 10.20.30.80
# 예상 출력:
# Starting Nmap 7.94 ( https://nmap.org )
# Nmap scan report for 10.20.30.80
# Host is up (0.00088s latency).
# Not shown: 993 closed tcp ports (reset)
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 3000/tcp open  ppp
# 8002/tcp open  teradataordbms
# 8081/tcp open  blackice-icecap
# 8082/tcp open  blackice-alerts
# MAC Address: XX:XX:XX:XX:XX:XX (VMware)
#
# Nmap done: 1 IP address (1 host up) scanned in 0.25 seconds
```

> **결과 해석**:
> - `993 closed tcp ports (reset)`: 993개 포트가 RST로 응답 → 닫힘
> - `22/tcp open ssh`: SSH 서비스 → 원격 접속 가능
> - `80/tcp open http`: HTTP 서비스 → 웹 서버 동작 중
> - `3000/tcp open ppp`: 실제로는 JuiceShop (nmap이 ppp로 잘못 추정)
> - `8002/tcp open teradataordbms`: 실제로는 OpsClaw SubAgent
>
> **실전 활용**: 이 결과에서 공격 가능한 서비스를 식별한다. HTTP(80, 3000)는 웹 공격, SSH(22)는 브루트포스 대상이다.
>
> **명령어 해설**:
> - 옵션 없이 실행 시 상위 1000개 포트를 SYN 스캔 (sudo 시) 또는 Connect 스캔 (일반 사용자)
>
> **트러블슈팅**:
> - "All 1000 scanned ports are filtered": 방화벽이 모든 포트를 차단 → `-Pn`으로 재시도
> - 스캔이 매우 느림: `-T4` 옵션 추가로 속도 향상

### Step 2: 전체 포트 스캔 (1-65535)

> **실습 목적**: 상위 1000개 포트에 포함되지 않은 비표준 포트의 서비스를 발견한다.
>
> **배우는 것**: 전체 포트 스캔의 필요성과 시간 대비 효과 분석

```bash
# 전체 포트 스캔 (시간 약 20-60초)
echo 1 | sudo -S nmap -p- -T4 10.20.30.80
# 예상 출력:
# PORT      STATE SERVICE
# 22/tcp    open  ssh
# 80/tcp    open  http
# 3000/tcp  open  ppp
# 8002/tcp  open  teradataordbms
# 8081/tcp  open  blackice-icecap
# 8082/tcp  open  blackice-alerts
# (추가 포트가 있을 수 있음)

# secu 서버 전체 포트 스캔
echo 1 | sudo -S nmap -p- -T4 10.20.30.1
# 예상 출력:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 8002/tcp open  teradataordbms

# siem 서버 전체 포트 스캔
echo 1 | sudo -S nmap -p- -T4 10.20.30.100
# 예상 출력:
# PORT      STATE SERVICE
# 22/tcp    open  ssh
# 443/tcp   open  https       (Wazuh Dashboard)
# 1514/tcp  open  fujitsu-dtc (Wazuh Agent)
# 1515/tcp  open  iChat       (Wazuh Registration)
# 8002/tcp  open  teradataordbms
# 9400/tcp  open  ...         (OpenCTI)
# 55000/tcp open  unknown     (Wazuh API)
```

> **결과 해석**:
> - 전체 스캔에서 기본 스캔보다 더 많은 포트를 발견할 수 있다
> - siem 서버에서 443(Wazuh Dashboard), 55000(Wazuh API)은 공격 표면이 넓은 서비스
> - 비표준 포트(8002, 9400)의 서비스는 `-sV`로 정확히 식별해야 한다
>
> **실전 활용**: 공방전에서 전체 포트 스캔은 시간이 걸리므로, 먼저 기본 스캔으로 빠른 결과를 얻고 백그라운드에서 전체 스캔을 돌린다.

### Step 3: 다양한 스캔 기법 비교 실습

> **실습 목적**: SYN, Connect, FIN 스캔의 차이를 직접 체험하고 결과를 비교한다.
>
> **배우는 것**: 각 스캔 기법의 실제 동작과 탐지 특성

```bash
# SYN 스캔 (스텔스, sudo 필요)
echo 1 | sudo -S nmap -sS -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 3000/tcp open  ppp

# Connect 스캔 (일반 사용자, 로그 남음)
nmap -sT -p 22,80,3000 10.20.30.80
# 예상 출력: (동일한 결과이지만 대상 서버의 로그에 기록됨)

# FIN 스캔 (스텔스)
echo 1 | sudo -S nmap -sF -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE         SERVICE
# 22/tcp   open|filtered ssh
# 80/tcp   open|filtered http
# 3000/tcp open|filtered ppp

# ACK 스캔 (방화벽 매핑)
echo 1 | sudo -S nmap -sA -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE      SERVICE
# 22/tcp   unfiltered ssh
# 80/tcp   unfiltered http
# 3000/tcp unfiltered ppp
```

> **결과 해석**:
> - SYN 스캔: 정확한 `open` 결과, 가장 신뢰할 수 있음
> - Connect 스캔: 동일 결과이지만 대상의 `/var/log/auth.log` 등에 연결 기록 남음
> - FIN 스캔: `open|filtered`로 불확실 — Linux에서는 열린 포트가 FIN에 응답하지 않음
> - ACK 스캔: `unfiltered`는 방화벽이 해당 포트를 차단하지 않음을 의미 (open 여부는 알 수 없음)
>
> **명령어 해설**:
> - `-sS`: SYN 스캔 (half-open)
> - `-sT`: TCP Connect 스캔 (full connection)
> - `-sF`: FIN 스캔
> - `-sA`: ACK 스캔 (방화벽 규칙 매핑용)
> - `-p 22,80,3000`: 특정 포트만 스캔
>
> **트러블슈팅**:
> - "You requested a SYN scan but are not root": sudo 없이 실행한 경우
> - FIN 스캔에서 모두 `open|filtered`: Linux 대상에서는 정상 (RST가 안 오면 열린 것으로 추정)

## 실습 3.3: 서비스 버전 탐지 + OS 핑거프린팅

### Step 1: 서비스 버전 상세 탐지

> **실습 목적**: 각 열린 포트에서 실행 중인 서비스의 정확한 소프트웨어명과 버전을 식별한다.
>
> **배우는 것**: 배너 그래빙의 원리와 CVE 검색을 위한 버전 정보 수집법

```bash
# web 서버 서비스 버전 탐지
echo 1 | sudo -S nmap -sV -p 22,80,3000,8002 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE VERSION
# 22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6 (Ubuntu Linux; protocol 2.0)
# 80/tcp   open  http    Apache httpd 2.4.52 ((Ubuntu))
# 3000/tcp open  http    Node.js Express framework
# 8002/tcp open  http    Uvicorn
# MAC Address: XX:XX:XX:XX:XX:XX (VMware)
# Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

# secu 서버 서비스 버전 탐지
echo 1 | sudo -S nmap -sV 10.20.30.1
# 예상 출력:
# PORT     STATE SERVICE VERSION
# 22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6
# 8002/tcp open  http    Uvicorn

# siem 서버 서비스 버전 탐지
echo 1 | sudo -S nmap -sV -p 22,443,1514,1515,8002,55000 10.20.30.100
# 예상 출력:
# PORT      STATE SERVICE  VERSION
# 22/tcp    open  ssh      OpenSSH 8.9p1 Ubuntu 3ubuntu0.6
# 443/tcp   open  ssl/http OpenSearch Dashboards
# 1514/tcp  open  unknown  Wazuh agent
# 1515/tcp  open  unknown  Wazuh registration
# 8002/tcp  open  http     Uvicorn
# 55000/tcp open  ssl/http Wazuh API
```

> **결과 해석**:
> - `OpenSSH 8.9p1`: 정확한 버전 → `searchsploit OpenSSH 8.9` 또는 CVE DB 검색
> - `Apache httpd 2.4.52`: Apache 웹 서버 버전 확인 → 알려진 취약점 유무 확인
> - `Node.js Express framework`: JuiceShop이 Express 기반임을 확인
> - `Uvicorn`: Python ASGI 서버 → OpsClaw SubAgent
> - `CPE: cpe:/o:linux:linux_kernel`: CPE 표기로 자동화 도구 연동 가능
>
> **실전 활용**: 버전 정보로 exploit-db, NVD에서 CVE를 검색한다. 예: Apache 2.4.52에 CVE-2023-25690(HTTP Request Smuggling)이 있으면 공격 가능 여부를 평가한다.
>
> **명령어 해설**:
> - `-sV`: 서비스 프로브 전송으로 정확한 버전 탐지
> - `--version-intensity 9`: 모든 프로브를 전송 (느리지만 정확)
>
> **트러블슈팅**:
> - 서비스가 "tcpwrapped"로 표시: 서비스가 연결 후 즉시 끊음 → 인증 필요 가능성
> - 버전이 표시되지 않음: 배너가 비활성화된 경우 → NSE 스크립트로 추가 시도

### Step 2: OS 핑거프린팅

> **실습 목적**: 대상 시스템의 운영체제를 식별하여 커널 취약점 등을 검색할 수 있도록 한다.
>
> **배우는 것**: TCP/IP 스택 핑거프린팅의 원리와 OS 추정 방법

```bash
# web 서버 OS 탐지
echo 1 | sudo -S nmap -O 10.20.30.80
# 예상 출력:
# ...
# Device type: general purpose
# Running: Linux 5.X
# OS CPE: cpe:/o:linux:linux_kernel:5
# OS details: Linux 5.4 - 5.15
# Network Distance: 1 hop

# 종합 스캔 (-A = -sV -O -sC --traceroute)
echo 1 | sudo -S nmap -A -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE VERSION
# 22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.6
# |_ssh-hostkey:
# |   256 xx:xx:xx:... (ECDSA)
# |   256 xx:xx:xx:... (ED25519)
# 80/tcp   open  http    Apache httpd 2.4.52 ((Ubuntu))
# |_http-title: Apache2 Ubuntu Default Page: It works
# |_http-server-header: Apache/2.4.52 (Ubuntu)
# 3000/tcp open  http    Node.js Express framework
# |_http-title: OWASP Juice Shop
# OS details: Linux 5.4 - 5.15
# TRACEROUTE
# HOP RTT     ADDRESS
# 1   0.88 ms 10.20.30.80
```

> **결과 해석**:
> - `Linux 5.4 - 5.15`: OS 버전 범위 추정 — 정확한 커널은 별도 확인 필요
> - `ssh-hostkey`: SSH 호스트 키 정보 — 서버 식별 및 MITM 탐지에 활용
> - `http-title: OWASP Juice Shop`: NSE 스크립트가 웹 페이지 제목을 자동 수집
> - `Network Distance: 1 hop`: 라우터 경유 없이 직접 연결 (같은 서브넷)
>
> **실전 활용**: OS 버전으로 커널 취약점(DirtyPipe, DirtyCow 등)의 적용 가능성을 평가한다.

### Step 3: NSE 스크립트를 활용한 추가 정보 수집

> **실습 목적**: nmap의 스크립트 엔진을 활용하여 기본 스캔 이상의 상세 정보를 수집한다.
>
> **배우는 것**: NSE 스크립트 카테고리와 활용법

```bash
# 기본 스크립트 스캔 (안전한 정보 수집)
echo 1 | sudo -S nmap -sC -p 22,80,3000 10.20.30.80
# 예상 출력: ssh-hostkey, http-title 등 기본 정보

# HTTP 관련 스크립트 모음
echo 1 | sudo -S nmap --script=http-headers,http-methods,http-title -p 80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 80/tcp   open  http
# | http-headers:
# |   Date: ...
# |   Server: Apache/2.4.52 (Ubuntu)
# |   Content-Type: text/html
# | http-methods:
# |   Supported Methods: GET HEAD POST OPTIONS
# 3000/tcp open  ppp
# | http-title: OWASP Juice Shop

# 취약점 카테고리 스크립트 (주의: 침입적일 수 있음)
echo 1 | sudo -S nmap --script=vuln -p 80 10.20.30.80
# 예상 출력: 발견된 취약점 목록 (있는 경우)

# SSH 인증 방법 확인
echo 1 | sudo -S nmap --script=ssh-auth-methods -p 22 10.20.30.80
# 예상 출력:
# | ssh-auth-methods:
# |   Supported authentication methods:
# |     publickey
# |_    password
```

> **결과 해석**:
> - `Supported Methods: GET HEAD POST OPTIONS`: HTTP 메서드 확인 — PUT, DELETE가 있으면 위험
> - `ssh-auth-methods: password`: 비밀번호 인증 허용 → 브루트포스 공격 가능
> - vuln 스크립트: 알려진 취약점을 자동 검사하지만 오탐 가능성 있음
>
> **실전 활용**: 공방전에서 `--script=vuln`은 빠른 취약점 발견에 유용하지만, Blue Team의 IDS에 탐지될 수 있다.
>
> **트러블슈팅**:
> - "NSE: Script not found": 스크립트 이름 오타 → `ls /usr/share/nmap/scripts/ | grep http`로 확인
> - 스크립트 실행이 너무 오래 걸림: `--script-timeout 30s`로 타임아웃 설정

---

# Part 4: 종합 정찰 실습 + 공격 표면 보고서 (30분)

## 실습 4.1: 전체 인프라 종합 스캔

### Step 1: 타겟 파일 기반 일괄 스캔

> **실습 목적**: 이전 단계에서 생성한 타겟 리스트를 활용하여 전체 인프라를 체계적으로 스캔한다.
>
> **배우는 것**: nmap의 입력 파일 활용, 출력 포맷 관리, 대규모 스캔 전략

```bash
# 타겟 파일 확인
cat /tmp/targets.txt
# 예상 출력:
# 10.20.30.1
# 10.20.30.80
# 10.20.30.100
# 10.20.30.201

# 전체 타겟 종합 스캔 (서비스 버전 + OS + 기본 스크립트)
echo 1 | sudo -S nmap -sV -O -sC -T4 -iL /tmp/targets.txt -oA /tmp/full_scan
# 예상 출력: 4개 호스트의 종합 스캔 결과
# (시간: 약 30-90초)

# 결과 파일 확인
ls -la /tmp/full_scan.*
# 예상 출력:
# /tmp/full_scan.gnmap   (grepable 포맷)
# /tmp/full_scan.nmap    (일반 텍스트)
# /tmp/full_scan.xml     (XML 포맷)
```

> **결과 해석**:
> - `.nmap`: 사람이 읽기 좋은 텍스트 형태
> - `.gnmap`: grep으로 파싱하기 좋은 형태 (스크립트 활용)
> - `.xml`: Metasploit, OpenVAS 등 도구와 연동 가능
>
> **명령어 해설**:
> - `-iL /tmp/targets.txt`: 파일에서 타겟 IP 목록을 읽음
> - `-oA /tmp/full_scan`: 3가지 포맷으로 동시 저장 (.nmap, .gnmap, .xml)
> - `-T4`: 빠른 스캔 (실습 환경에 적합)

### Step 2: 스캔 결과 분석 스크립트

> **실습 목적**: 스캔 결과를 자동으로 파싱하여 공격 표면을 정리한다.
>
> **배우는 것**: grep/awk를 활용한 스캔 결과 분석 기법

```bash
# 모든 호스트의 열린 포트 요약
echo "=== 열린 포트 요약 ==="
grep "open" /tmp/full_scan.gnmap | while read line; do
    host=$(echo "$line" | awk '{print $2}')
    ports=$(echo "$line" | grep -oP '\d+/open/tcp//[^/]+' | tr '\n' ', ')
    echo "  $host: $ports"
done
# 예상 출력:
#   10.20.30.1: 22/open/tcp//ssh, 8002/open/tcp//unknown,
#   10.20.30.80: 22/open/tcp//ssh, 80/open/tcp//http, 3000/open/tcp//http, ...
#   10.20.30.100: 22/open/tcp//ssh, 443/open/tcp//https, ...
#   10.20.30.201: 22/open/tcp//ssh, 8000/open/tcp//http, ...

# HTTP 서비스만 필터링 (웹 공격 대상)
echo "=== HTTP 서비스 ==="
grep -E "80/open|443/open|3000/open|8000/open|8080/open" /tmp/full_scan.gnmap
# 예상 출력: HTTP 서비스가 있는 호스트와 포트 목록

# SSH 서비스 목록 (브루트포스 대상)
echo "=== SSH 서비스 ==="
grep "22/open" /tmp/full_scan.gnmap | awk '{print $2}'
# 예상 출력:
# 10.20.30.1
# 10.20.30.80
# 10.20.30.100
# 10.20.30.201
```

> **결과 해석**: gnmap 포맷은 스크립트 파싱에 최적화되어 있다. 열린 포트를 서비스 유형별로 분류하면 공격 우선순위를 결정할 수 있다.
>
> **실전 활용**: Red Team은 이 결과로 "어떤 서비스를 먼저 공격할 것인가"를 결정한다. 일반적으로 웹 서비스(HTTP) → 인증 서비스(SSH) → 관리 API 순으로 공격한다.

### Step 3: 수동 배너 그래빙 비교

> **실습 목적**: nmap 외에 수동으로 배너를 수집하는 방법을 익혀, 도구가 없는 환경에서도 정찰할 수 있다.
>
> **배우는 것**: netcat, curl을 이용한 수동 배너 그래빙 기법

```bash
# netcat으로 SSH 배너 수집
echo "" | nc -w3 10.20.30.80 22
# 예상 출력: SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6

# curl로 HTTP 헤더 수집
curl -sI http://10.20.30.80:80 | head -10
# 예상 출력:
# HTTP/1.1 200 OK
# Date: ...
# Server: Apache/2.4.52 (Ubuntu)
# ...

# curl로 JuiceShop 헤더 수집
curl -sI http://10.20.30.80:3000 | head -10
# 예상 출력:
# HTTP/1.1 200 OK
# X-Powered-By: Express
# Access-Control-Allow-Origin: *
# X-Content-Type-Options: nosniff
# ...

# bash /dev/tcp로 포트 확인 (nmap 없이)
for port in 22 80 443 3000 8002; do
    timeout 1 bash -c "echo >/dev/tcp/10.20.30.80/$port" 2>/dev/null \
      && echo "10.20.30.80:$port OPEN" \
      || echo "10.20.30.80:$port closed"
done
# 예상 출력:
# 10.20.30.80:22 OPEN
# 10.20.30.80:80 OPEN
# 10.20.30.80:443 closed
# 10.20.30.80:3000 OPEN
# 10.20.30.80:8002 OPEN
```

> **결과 해석**:
> - netcat 배너: nmap `-sV`와 동일한 정보를 수동으로 획득
> - HTTP 헤더: `Server`, `X-Powered-By` 등에서 기술 스택 정보 유출
> - bash /dev/tcp: 아무 도구 없이 포트를 확인하는 "Living off the Land" 기법
>
> **실전 활용**: 침투 후 대상 시스템에서 nmap을 설치할 수 없을 때, bash와 netcat만으로 내부 네트워크를 정찰한다.

## 실습 4.2: 공격 표면 보고서 작성

### Step 1: OpsClaw를 활용한 자동화된 정찰

> **실습 목적**: OpsClaw Manager API를 통해 여러 서버의 정찰을 자동화하고 증적을 기록한다.
>
> **배우는 것**: OpsClaw execute-plan으로 멀티 호스트 정찰을 오케스트레이션하는 방법

```bash
# OpsClaw 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week01-recon","request_text":"네트워크 정찰 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 4개 서버 동시 정찰
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"secu 포트스캔","instruction_prompt":"nmap -sV -T4 10.20.30.1 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"web 포트스캔","instruction_prompt":"nmap -sV -T4 10.20.30.80 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"siem 포트스캔","instruction_prompt":"nmap -sV -T4 10.20.30.100 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":4,"title":"opsclaw 포트스캔","instruction_prompt":"nmap -sV -T4 localhost 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} → {t[\"status\"]}')
"
# 예상 출력:
# 결과: success
#   [1] secu 포트스캔          → ok
#   [2] web 포트스캔           → ok
#   [3] siem 포트스캔          → ok
#   [4] opsclaw 포트스캔       → ok
```

> **결과 해석**: OpsClaw를 통해 실행하면 모든 스캔 결과가 evidence로 자동 기록된다. 이후 `/evidence/summary`로 확인 가능하다.
>
> **실전 활용**: 실무에서는 정찰 작업도 증적으로 남겨야 감사 대응이 가능하다. OpsClaw는 이를 자동화한다.

### Step 2: 공격 표면 분석 보고서 템플릿

> **실습 목적**: 수집한 정보를 체계적인 보고서 형태로 정리하는 습관을 기른다.
>
> **배우는 것**: 모의해킹 보고서의 정찰 섹션 작성법

```bash
# 보고서 템플릿 생성
cat << 'REPORT'
=== 공격 표면 분석 보고서 ===

1. 대상 네트워크: 10.20.30.0/24
2. 스캔 일시: $(date)
3. 스캔 도구: nmap 7.94

4. 호스트 목록:
   - 10.20.30.1   (secu)  — 네트워크 보안 장비
   - 10.20.30.80  (web)   — 웹 서버 + 취약 앱
   - 10.20.30.100 (siem)  — 보안 모니터링
   - 10.20.30.201 (opsclaw) — 관리 플랫폼

5. 서비스 목록:
   [secu] SSH(22), SubAgent(8002)
   [web]  SSH(22), HTTP(80), JuiceShop(3000), SubAgent(8002)
   [siem] SSH(22), HTTPS(443), Wazuh(1514,1515,55000), SubAgent(8002)
   [opsclaw] SSH(22), Manager(8000), SubAgent(8002)

6. 공격 우선순위:
   (1) web:3000  — OWASP JuiceShop (알려진 취약 앱) → SQLi, XSS
   (2) web:80    — Apache 2.4.52 → CVE 확인 필요
   (3) siem:443  — Wazuh Dashboard → 인증 우회 시도
   (4) *:22      — SSH 비밀번호 인증 허용 → 브루트포스

7. 방어 관찰:
   - ICMP: 허용 (ping 응답)
   - 방화벽: secu에 nftables 존재 (추가 확인 필요)
   - IDS/IPS: Suricata 존재 (추가 확인 필요)
REPORT
```

> **실전 활용**: 이 보고서 형태는 실제 모의해킹 보고서의 "정찰 결과" 섹션에 해당한다. Week 15에서 최종 보고서를 작성할 때 이 데이터를 활용한다.

## 실습 4.3: Blue Team 관점 — 스캔 탐지

### Step 1: 방어자의 스캔 탐지 방법

> **실습 목적**: 공격자의 스캔 행위가 방어 시스템에서 어떻게 보이는지 이해한다.
>
> **배우는 것**: IDS 로그, 방화벽 로그에서 스캔 흔적을 찾는 방법

```bash
# Suricata IDS 로그에서 스캔 탐지 확인 (secu 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "cat /var/log/suricata/fast.log 2>/dev/null | tail -20"
# 예상 출력: 포트 스캔 탐지 이벤트 (있는 경우)

# nftables 방화벽 로그 확인 (secu 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "dmesg | grep -i nft | tail -10"
# 예상 출력: 방화벽에서 차단된 패킷 로그

# 시스템 인증 로그에서 스캔 흔적 (web 서버)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "cat /var/log/auth.log 2>/dev/null | tail -10"
# 예상 출력: SSH 연결 시도 기록 (Connect 스캔의 흔적)
```

> **결과 해석**:
> - Suricata는 짧은 시간 내 다수 포트 접근을 "portscan"으로 탐지할 수 있다
> - nftables 로그에서 차단된 패킷을 확인할 수 있다
> - `/var/log/auth.log`에는 SSH 연결 시도가 기록된다
>
> **실전 활용**: Blue Team은 이러한 로그를 실시간 모니터링하여 정찰 행위를 조기에 발견한다. Week 07(IDS/IPS)에서 탐지 룰을 직접 작성한다.

### Step 2: 스캔 회피 기법 이해

> **실습 목적**: 공격자가 사용하는 회피 기법을 이해하여 방어에 활용한다.
>
> **배우는 것**: Decoy, 단편화, 타이밍 조절 등의 회피 기법

```bash
# Decoy 스캔 (가짜 소스 IP 추가)
echo 1 | sudo -S nmap -D RND:5 -p 80 10.20.30.80
# 해석: 5개의 랜덤 IP를 디코이로 추가. 방화벽 로그에 6개의 소스 IP가 표시됨

# 느린 스캔 (IDS 임계값 회피)
echo 1 | sudo -S nmap -T1 -p 22,80 10.20.30.80
# 해석: 15초 간격으로 프로브 전송. IDS의 시간 기반 탐지를 회피

# 소스 포트 지정 (방화벽 규칙 우회)
echo 1 | sudo -S nmap --source-port 53 -p 80 10.20.30.80
# 해석: DNS 포트(53)에서 보낸 것처럼 위장. 일부 방화벽은 DNS 트래픽을 허용

# 패킷 단편화 (IDS 우회)
echo 1 | sudo -S nmap -f -p 80 10.20.30.80
# 해석: IP 패킷을 작은 단편으로 분할. 일부 IDS가 재조합에 실패할 수 있음
```

> **결과 해석**:
> - Decoy: 방어자가 진짜 공격자를 식별하기 어려워짐
> - 느린 스캔: IDS의 "N초 내 M개 포트 접근" 임계값을 회피
> - 소스 포트 위장: stateless 방화벽 규칙을 우회할 수 있음
> - 단편화: 오래된 IDS에서 우회 가능하지만 현대 시스템은 재조합 지원
>
> **실전 활용**: 공방전에서 Red Team은 이 기법들을 조합하여 Blue Team의 탐지를 회피한다. Blue Team은 이 기법들을 알아야 탐지 룰을 강화할 수 있다.

---

## 검증 체크리스트
- [ ] nmap으로 10.20.30.0/24 서브넷의 활성 호스트를 모두 식별했는가 (4개)
- [ ] ping sweep, ARP 스캔, TCP ping의 차이를 설명할 수 있는가
- [ ] SYN, Connect, FIN 스캔의 동작 원리와 차이를 이해했는가
- [ ] 각 호스트의 열린 포트와 서비스 버전을 확인하고 기록했는가
- [ ] OS 핑거프린팅으로 대상 OS를 식별했는가
- [ ] 스캔 결과를 파일로 저장하고 분석 스크립트로 정리했는가
- [ ] OpsClaw를 통한 자동화된 정찰을 수행했는가
- [ ] Blue Team 관점에서 스캔 탐지 로그를 확인했는가
- [ ] 공격 표면 보고서를 작성했는가

## 자가 점검 퀴즈

1. TCP SYN 스캔(`-sS`)이 TCP Connect 스캔(`-sT`)보다 스텔스한 이유를 3-way handshake 관점에서 설명하라.

2. nmap에서 `-sn` 옵션은 정확히 어떤 동작을 수행하는가? ARP, ICMP, TCP 각각의 프로브를 설명하라.

3. 포트 상태가 `filtered`로 표시되는 경우는 어떤 상황이며, `closed`와의 차이는 무엇인가?

4. 방어자가 포트 스캔을 탐지할 수 있는 방법 3가지를 설명하라.

5. nmap의 `-oA` 옵션으로 저장 시 생성되는 파일 3가지의 확장자와 각 용도를 설명하라.

6. OS 핑거프린팅에서 TTL 값이 64인 호스트와 128인 호스트는 각각 어떤 OS일 가능성이 높은가?

7. FIN 스캔(`-sF`)이 Windows 시스템에서 제대로 동작하지 않는 이유를 RFC 793 관점에서 설명하라.

8. Decoy 스캔(`-D`)의 원리와 한계를 설명하라. 방어자가 Decoy를 식별하는 방법은?

9. 서비스 배너 그래빙(Banner Grabbing)으로 얻은 버전 정보를 실제 공격에 어떻게 활용하는지 단계별로 설명하라.

10. 공방전에서 Red Team이 정찰을 수행할 때 Blue Team에게 탐지되지 않기 위한 전략 3가지를 제시하라.

## 과제

### 과제 1: 전체 인프라 정찰 보고서 (필수)
- 4개 서버(secu, web, siem, opsclaw)에 대해 종합 스캔(-A) 수행
- 각 서버별 열린 포트, 서비스 버전, OS 정보를 표 형태로 정리
- 공격 우선순위를 정하고 그 근거를 서술 (최소 500자)
- nmap 결과 파일(.nmap, .xml) 첨부

### 과제 2: 스캔 탐지 분석 (선택)
- 다른 학생과 짝을 이루어, 한 명은 스캔, 한 명은 방어자 역할
- 방어자는 Suricata 로그와 시스템 로그에서 스캔 흔적을 찾아 보고
- 어떤 스캔 기법이 탐지되었고, 어떤 것이 탐지되지 않았는지 비교 분석

### 과제 3: bash 기반 스캐너 작성 (도전)
- nmap 없이 bash만으로 호스트 탐색 + 포트 스캔 스크립트를 작성
- `/dev/tcp`와 `ping`을 활용하여 10.20.30.0/24 대역의 활성 호스트와 상위 20개 포트를 확인
- 결과를 CSV 형태로 출력하는 스크립트 작성
