# Week 09: 네트워크 공격 기초

## 학습 목표
- TCP/IP 네트워크 계층 모델을 이해한다
- 포트 스캐닝 기법(SYN, Connect, UDP)의 원리와 차이를 설명할 수 있다
- tcpdump로 네트워크 패킷을 캡처하고 분석할 수 있다
- ARP 스푸핑의 개념과 위험성을 이해한다
- 실습 환경에서 스캔과 패킷 캡처를 직접 수행한다

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

# Week 09: 네트워크 공격 기초

## 학습 목표

- TCP/IP 네트워크 계층 모델을 이해한다
- 포트 스캐닝 기법(SYN, Connect, UDP)의 원리와 차이를 설명할 수 있다
- tcpdump로 네트워크 패킷을 캡처하고 분석할 수 있다
- ARP 스푸핑의 개념과 위험성을 이해한다
- 실습 환경에서 스캔과 패킷 캡처를 직접 수행한다

---

## 1. 네트워크 계층 모델

### 1.1 OSI 7계층 vs TCP/IP 4계층

```
OSI 7계층                          TCP/IP 4계층
-------------------------------    -------------------
7. 응용 (Application)    ]
6. 표현 (Presentation)   ]--->     응용 계층 (HTTP, DNS, SSH)
5. 세션 (Session)        ]
4. 전송 (Transport)      --->      전송 계층 (TCP, UDP)
3. 네트워크 (Network)    --->      인터넷 계층 (IP, ICMP, ARP)
2. 데이터링크 (Link)     ]
1. 물리 (Physical)       ]--->     네트워크 접근 계층 (Ethernet)
```

### 1.2 핵심 프로토콜 정리

| 프로토콜 | 계층 | 역할 | 포트 |
|----------|------|------|------|
| TCP | 전송 | 연결 지향, 신뢰성 보장 | - |
| UDP | 전송 | 비연결, 빠른 전송 | - |
| IP | 인터넷 | 주소 지정, 라우팅 | - |
| ARP | 인터넷 | IP → MAC 주소 변환 | - |
| ICMP | 인터넷 | 오류 보고, ping | - |
| HTTP | 응용 | 웹 통신 | 80/443 |
| SSH | 응용 | 암호화 원격 접속 | 22 |
| DNS | 응용 | 도메인 → IP 변환 | 53 |

### 1.3 TCP 3-Way Handshake

TCP 연결이 수립되는 과정이다. 공격자가 이 과정을 악용하여 스캔을 수행한다.

```
클라이언트                             서버

  1단계: 연결 요청
    ---- SYN (seq=100) ----------->

  2단계: 요청 수락
    <--- SYN+ACK (seq=200, ack=101) --

  3단계: 연결 확립
    ---- ACK (ack=201) ----------->
```

- **SYN**: "연결하고 싶다" (SYNchronize)
- **SYN+ACK**: "알겠다, 나도 준비됐다"
- **ACK**: "확인했다, 통신 시작하자" (ACKnowledge)

### 1.4 ARP (Address Resolution Protocol)

같은 네트워크 내에서 IP 주소를 MAC 주소로 변환하는 프로토콜이다.

```
ARP 요청 (브로드캐스트):
  "10.20.30.80의 MAC 주소를 아는 사람?"

ARP 응답 (유니캐스트):
  "내가 10.20.30.80이다. MAC은 AA:BB:CC:DD:EE:FF"
```

**문제점**: ARP에는 인증이 없다. 누구나 거짓 ARP 응답을 보낼 수 있다.

---

## 2. 포트 스캐닝 기법

### 2.1 포트 스캐닝이란?

> **이 실습을 왜 하는가?**
> 포트 스캐닝은 침투 테스트의 **가장 기본적인 정찰 활동**이다.
> "열린 포트 = 실행 중인 서비스 = 잠재적 공격 표면"이다.
> 22번(SSH), 80번(HTTP), 3306(MySQL) 등 각 포트에 대응하는 서비스를 파악하면
> 어떤 공격을 시도할 수 있는지 판단할 수 있다.
>
> **실무 활용:** 모의해킹 보고서의 첫 섹션은 항상 "포트 스캔 결과"이다.
> nmap 결과를 기반으로 공격 우선순위를 정한다.
>
> **주의:** 허가 없는 포트 스캐닝은 **불법**이다. 실습 환경(10.20.30.0/24)에서만 수행한다.
>
> **검증 완료:** web 서버(10.20.30.80)에서 22, 80, 3000, 8002 포트 열림 확인.

대상 시스템에서 열려 있는 포트(서비스)를 찾는 정찰 기법이다. 침투 테스트의 첫 단계이다.

### 2.2 TCP SYN 스캔 (Half-Open Scan)

```
공격자                               대상

  ---- SYN --------------------->
  <--- SYN+ACK (포트 열림) ------    --> 열려 있다!
  ---- RST --------------------->    --> 연결 완료하지 않고 끊음

  <--- RST (포트 닫힘) ----------    --> 닫혀 있다!
```

- 3-Way Handshake를 완료하지 않아 로그에 기록되지 않을 수 있다
- root 권한 필요 (raw socket 사용)

### 2.3 TCP Connect 스캔

```
공격자                               대상

  ---- SYN --------------------->
  <--- SYN+ACK ------------------    --> 열려 있다!
  ---- ACK --------------------->    --> 완전한 연결 수립
  ---- RST --------------------->    --> 연결 종료
```

- 완전한 TCP 연결을 수립하므로 로그에 기록된다
- 일반 사용자 권한으로 실행 가능

### 2.4 UDP 스캔

```
공격자                               대상

  ---- UDP 패킷 ----------------->
  <--- ICMP Port Unreachable -----   --> 닫혀 있다!
       (응답 없음)                   --> 열려 있거나 필터됨
```

- UDP는 비연결이므로 응답이 없으면 열림/필터 구분이 어렵다
- 스캔 속도가 매우 느리다 (ICMP rate limiting)

### 2.5 nmap 포트 스캔 명령어

> **실습 목적**: nmap을 사용한 다양한 포트 스캔 기법으로 네트워크 공격의 기초인 서비스 열거를 수행한다
>
> **배우는 것**: SYN/UDP/ACK 스캔 등 각 방식의 TCP 플래그 동작과 방화벽 우회 특성을 이해한다
>
> **결과 해석**: open/closed/filtered 결과에서 방화벽 규칙과 실제 서비스 동작 상태를 유추할 수 있다
>
> **실전 활용**: 네트워크 침투 테스트에서 방화벽 뒤의 서비스를 식별하고 공격 경로를 설계하는 데 활용된다

```bash
# SYN 스캔 (기본, root 필요)
nmap -sS 10.20.30.80

# Connect 스캔 (일반 사용자 가능)
nmap -sT 10.20.30.80

# UDP 스캔
nmap -sU 10.20.30.80

# 특정 포트만 스캔
nmap -p 22,80,3000 10.20.30.80

# 전체 포트 스캔 + 서비스 버전
nmap -sV -p- 10.20.30.80

# OS 탐지
nmap -O 10.20.30.80

# 빠른 스캔 (상위 100개 포트)
nmap -F 10.20.30.80
```

---

## 3. tcpdump 패킷 캡처

### 3.1 tcpdump 기본 사용법

tcpdump는 네트워크 인터페이스를 통과하는 패킷을 실시간으로 캡처하는 도구이다.

```bash
# 기본 캡처 (모든 패킷)
sudo tcpdump -i eth0

# 특정 호스트 필터
sudo tcpdump -i eth0 host 10.20.30.80

# 특정 포트 필터
sudo tcpdump -i eth0 port 22

# TCP SYN 패킷만 캡처
sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'

# 패킷 내용 출력 (hex + ASCII)
sudo tcpdump -i eth0 -X port 80

# 파일로 저장
sudo tcpdump -i eth0 -w /tmp/capture.pcap

# 저장된 파일 읽기
sudo tcpdump -r /tmp/capture.pcap

# 패킷 수 제한
sudo tcpdump -i eth0 -c 50 host 10.20.30.80
```

### 3.2 tcpdump 출력 해석

```
14:23:01.123456 IP 10.20.30.201.45678 > 10.20.30.80.22: Flags [S], seq 12345

각 필드 설명:
  14:23:01.123456    --> 타임스탬프
  IP                 --> 프로토콜
  10.20.30.201.45678 --> 출발지 IP:포트
  10.20.30.80.22     --> 목적지 IP:포트
  Flags [S]          --> TCP 플래그 (S=SYN)
  seq 12345          --> 시퀀스 번호
```

**TCP 플래그 기호:**
- `[S]` = SYN
- `[S.]` = SYN+ACK
- `[.]` = ACK
- `[R]` = RST
- `[F]` = FIN
- `[P.]` = PUSH+ACK

---

## 4. ARP 스푸핑 개념

### 4.1 ARP 스푸핑 원리

공격자가 거짓 ARP 응답을 보내 자신의 MAC 주소를 다른 호스트의 IP에 연결시킨다.

```
정상 상태:
  PC-A (10.20.30.201) → 게이트웨이 (10.20.30.1)
  ARP 테이블: 10.20.30.1 = GW의 실제 MAC

공격 후:
  PC-A (10.20.30.201) → 공격자 (10.20.30.xxx) → 게이트웨이 (10.20.30.1)
  ARP 테이블: 10.20.30.1 = 공격자의 MAC  ← 조작됨!
```

### 4.2 ARP 스푸핑의 영향

- **도청(Sniffing)**: 중간에서 모든 트래픽을 볼 수 있다
- **변조(Tampering)**: 패킷 내용을 수정할 수 있다
- **세션 하이재킹**: 로그인 세션을 탈취할 수 있다
- **서비스 거부(DoS)**: 트래픽을 전달하지 않으면 통신 불가

### 4.3 ARP 테이블 확인

```bash
# 현재 ARP 테이블 확인
arp -a

# 또는
ip neigh show

# 예시 출력:
# 10.20.30.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
# 10.20.30.80 dev eth0 lladdr 11:22:33:44:55:66 STALE
```

### 4.4 방어 방법

- **정적 ARP 엔트리**: `arp -s 10.20.30.1 aa:bb:cc:dd:ee:ff`
- **Dynamic ARP Inspection (DAI)**: 스위치 레벨에서 검증
- **ARP 감시 도구**: arpwatch, arpalert

> **주의**: 실습 환경에서만 ARP 스푸핑을 수행한다. 실제 네트워크에서는 불법이다.

---

## 5. 실습

### 실습 환경

| 서버 | IP | 역할 |
|------|-----|------|
| opsclaw | 10.20.30.201 | 공격자 (스캔 수행) |
| secu | 10.20.30.1 | 방화벽/IPS (패킷 모니터링) |
| web | 10.20.30.80 | 대상 서버 (JuiceShop) |
| siem | 10.20.30.100 | SIEM (로그 수집) |

### 실습 1: secu 서버에서 tcpdump로 패킷 모니터링 준비

secu 서버에 SSH 접속 후 패킷 캡처를 시작한다.

```bash
# 터미널 1: secu 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# 네트워크 인터페이스 확인
ip addr show

# 10.20.30.0/24 네트워크 인터페이스에서 캡처 시작
# (인터페이스 이름은 환경에 따라 다를 수 있음: eth0, ens18 등)
sudo tcpdump -i eth0 host 10.20.30.80 -nn -c 100

# 출력 예시:
# tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
# listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
# (패킷 대기 중...)
```

### 실습 2: opsclaw에서 web 서버 포트 스캔

다른 터미널을 열고 opsclaw에서 스캔을 수행한다.

```bash
# 터미널 2: opsclaw에서 실행

# 2-1. 기본 ping 테스트 (ICMP)
ping -c 3 10.20.30.80

# 예상 출력:
# PING 10.20.30.80 (10.20.30.80) 56(84) bytes of data.
# 64 bytes from 10.20.30.80: icmp_seq=1 ttl=64 time=0.5 ms
# 64 bytes from 10.20.30.80: icmp_seq=2 ttl=64 time=0.4 ms
# 64 bytes from 10.20.30.80: icmp_seq=3 ttl=64 time=0.4 ms

# 2-2. TCP Connect 스캔 (상위 포트)
nmap -sT -F 10.20.30.80

# 예상 출력:
# Starting Nmap 7.94 ...
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 3000/tcp open  ppp
# Nmap done: 1 IP address (1 host up) scanned in 1.23 seconds

# 2-3. SYN 스캔 (root 필요)
sudo nmap -sS -p 22,80,3000,443,8080 10.20.30.80

# 예상 출력:
# PORT     STATE  SERVICE
# 22/tcp   open   ssh
# 80/tcp   open   http
# 443/tcp  closed https
# 3000/tcp open   ppp
# 8080/tcp closed http-proxy

# 2-4. 서비스 버전 탐지
nmap -sV -p 22,80,3000 10.20.30.80

# 예상 출력:
# PORT     STATE SERVICE VERSION
# 22/tcp   open  ssh     OpenSSH 8.x
# 80/tcp   open  http    nginx
# 3000/tcp open  http    Node.js (OWASP Juice Shop)
```

### 실습 3: secu에서 캡처된 패킷 분석

터미널 1로 돌아가서 캡처된 패킷을 확인한다.

```bash
# secu의 tcpdump 출력 예시:
# 14:30:01.123 IP 10.20.30.201.45678 > 10.20.30.80.22: Flags [S], seq 1234
# 14:30:01.124 IP 10.20.30.80.22 > 10.20.30.201.45678: Flags [S.], seq 5678, ack 1235
# 14:30:01.125 IP 10.20.30.201.45678 > 10.20.30.80.22: Flags [.], ack 5679
# 14:30:01.200 IP 10.20.30.201.45679 > 10.20.30.80.80: Flags [S], seq 2345
# ...
```

**분석 포인트:**
1. SYN 스캔과 Connect 스캔의 패킷 차이를 비교한다
2. 열린 포트와 닫힌 포트의 응답 차이를 확인한다
3. 스캔 속도(패킷 간격)를 관찰한다

### 실습 4: TCP SYN 패킷만 필터링

```bash
# secu에서 SYN 패킷만 캡처
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0' -nn -c 30"

# 동시에 opsclaw에서 스캔 실행
nmap -sS -p 1-100 10.20.30.80
```

### 실습 5: ARP 테이블 확인

```bash
# opsclaw에서 ARP 테이블 확인
ip neigh show

# 예상 출력:
# 10.20.30.1 dev eth0 lladdr xx:xx:xx:xx:xx:xx REACHABLE
# 10.20.30.80 dev eth0 lladdr yy:yy:yy:yy:yy:yy STALE

# web 서버에서도 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "ip neigh show"
```

### 실습 6: OpsClaw로 스캔 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# OpsClaw 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "name": "week09-network-scan",
    "request_text": "네트워크 스캔 실습",
    "master_mode": "external"
  }' | python3 -m json.tool

# 프로젝트 ID 확인 후 (예: id=1)
# Stage 전환
curl -s -X POST http://localhost:8000/projects/1/plan \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키
curl -s -X POST http://localhost:8000/projects/1/execute \
  -H "X-API-Key: opsclaw-api-key-2026"                 # API 인증 키

# nmap 스캔 실행
curl -s -X POST http://localhost:8000/projects/1/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sT -F 10.20.30.80",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/1/evidence/summary | python3 -m json.tool
```

---

## 6. 실습 과제

1. **패킷 분석 보고서**: secu에서 캡처한 패킷에서 SYN 스캔과 Connect 스캔의 차이점을 5가지 이상 서술하라.
2. **포트 스캔 결과 정리**: web 서버(10.20.30.80)의 열린 포트 목록과 각 서비스를 표로 정리하라.
3. **ARP 테이블 분석**: 각 서버의 ARP 테이블을 수집하고, ARP 스푸핑 시 어떤 항목이 변경될지 설명하라.

---

## 7. 핵심 정리

| 스캔 유형 | 원리 | 장점 | 단점 |
|-----------|------|------|------|
| SYN 스캔 | 반개방 연결 | 빠름, 은밀 | root 필요 |
| Connect 스캔 | 완전 연결 | 권한 불필요 | 로그 기록됨 |
| UDP 스캔 | UDP 패킷 전송 | UDP 서비스 발견 | 매우 느림 |

**다음 주 예고**: Week 10에서는 IPS/방화벽 우회 기법을 학습한다. secu의 nftables와 Suricata 규칙을 분석하고, 이를 우회하는 다양한 기법을 실습한다.

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
