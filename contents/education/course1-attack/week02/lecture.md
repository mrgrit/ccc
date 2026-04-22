# Week 02: 정보수집과 정찰 (Reconnaissance)

## 학습 목표
- 침투 테스트의 첫 단계인 **정보수집(Reconnaissance)**의 개념과 분류를 이해한다
- 능동적 정찰과 수동적 정찰의 차이를 설명할 수 있다
- nmap의 다양한 스캔 기법(SYN, Connect, FIN, NULL, Xmas)을 실행하고 결과를 해석할 수 있다
- DNS 조회 도구(dig, host, nslookup)를 활용하여 도메인 정보를 수집할 수 있다
- 웹 서버의 기술 스택을 파악하는 다양한 방법을 익힌다
- 디렉토리/파일 열거 기법을 사용하여 숨겨진 경로를 발견할 수 있다
- MITRE ATT&CK Reconnaissance 전술의 기법들을 매핑할 수 있다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| manager | 10.20.30.200 | Bastion 에이전트 호스트 | `ssh ccc@10.20.30.200` |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (대상) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `ssh ccc@10.20.30.100` |

이번 주는 주로 **manager**에서 web 서버를 대상으로 정찰한다. Bastion API는 `http://10.20.30.200:8003`.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 정보수집 개론 (이론) | 강의 |
| 0:30-1:10 | nmap 심화 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:50 | DNS/hosts/ARP 정보 수집 실습 | 실습 |
| 1:50-2:30 | 웹 서버 핑거프린팅 + 디렉토리 열거 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:20 | Bastion 정찰 자동화 | 실습 |
| 3:20-3:40 | ATT&CK 매핑 + 과제 안내 | 정리 |

---

# Part 1: 정보수집 개론 (30분)

## 1.1 정보수집이란?

정보수집(Reconnaissance, 약어 Recon)은 침투 테스트의 **가장 중요한 첫 단계**이다. 공격 대상에 대해 가능한 많은 정보를 수집하여 공격 표면(attack surface)을 파악한다.

```
"침투 테스트의 80%는 정보수집이다" — 보안 업계 격언
```

### 왜 중요한가?

정보수집이 부실하면:
- 존재하는 서비스를 놓쳐서 공격 기회를 상실
- 잘못된 대상을 공격하여 법적 문제 발생
- 방어 체계를 모르고 공격하여 즉시 탐지/차단
- 불필요한 시간 낭비

정보수집이 철저하면:
- 공격 표면을 완전히 파악하여 최적 공격 경로 선택
- 방어 체계의 약점을 사전 파악
- 은밀한 공격을 위한 정보 확보

## 1.2 정보수집의 분류

### 수동적 정찰 (Passive Reconnaissance)

대상 시스템에 **직접 접촉하지 않고** 정보를 수집한다. 대상이 탐지할 수 없다.

| 기법 | 도구 | 수집 정보 | ATT&CK |
|------|------|---------|--------|
| OSINT (공개 정보) | Google, Shodan, Censys | 서비스, 기술 스택 | T1593 |
| DNS 조회 | dig, host, nslookup | IP, MX, NS 레코드 | T1596.001 |
| WHOIS 조회 | whois | 등록자, 만료일 | T1596.002 |
| 소셜 미디어 | LinkedIn, GitHub | 직원 정보, 기술 스택 | T1593.001 |
| 인증서 조회 | crt.sh | 서브도메인 발견 | T1596.003 |
| 검색 엔진 | Google Dorking | 노출된 파일, 에러 메시지 | T1593.002 |

### 능동적 정찰 (Active Reconnaissance)

대상 시스템에 **직접 패킷을 보내서** 정보를 수집한다. 대상 IDS/IPS가 탐지할 수 있다.

| 기법 | 도구 | 수집 정보 | ATT&CK |
|------|------|---------|--------|
| 포트 스캔 | nmap | 열린 포트, 서비스 | T1046 |
| 서비스 핑거프린팅 | nmap -sV | 소프트웨어 버전 | T1046 |
| OS 탐지 | nmap -O | 운영체제 종류/버전 | T1046 |
| 웹 크롤링 | gobuster, dirb | 숨겨진 경로/파일 | T1595.003 |
| 배너 그래빙 | nc, curl | 서비스 배너 | T1046 |
| 취약점 스캔 | nikto, nuclei | 알려진 취약점 | T1595.002 |

> **수동 vs 능동의 판단 기준:**
> "내가 보내는 패킷이 대상 시스템에 도달하는가?"
> 도달하면 → 능동 (탐지 가능)
> 도달하지 않으면 → 수동 (탐지 불가)

## 1.3 MITRE ATT&CK: Reconnaissance 전술

| 기법 ID | 기법 이름 | 설명 | 이번 주 실습 |
|---------|---------|------|:---:|
| T1595 | Active Scanning | 능동 스캐닝 | ✓ |
| T1595.001 | Scanning IP Blocks | IP 범위 스캔 | ✓ |
| T1595.002 | Vulnerability Scanning | 취약점 스캐닝 | ✓ |
| T1595.003 | Wordlist Scanning | 디렉토리 열거 | ✓ |
| T1592 | Gather Victim Host Info | 호스트 정보 수집 | ✓ |
| T1593 | Search Open Websites | 공개 정보 검색 | △ |
| T1596 | Search Open Technical DB | WHOIS/DNS 조회 | ✓ |

---

# Part 2: nmap 심화 실습 (40분)

## 2.1 nmap 스캔 유형

### TCP 3-Way Handshake 복습

포트 스캔은 TCP 핸드셰이크를 어떻게 변형하느냐에 따라 분류된다.

```
클라이언트                             서버

  ---- SYN --------------------->    "연결하고 싶어"
  <--- SYN/ACK ------------------    "알겠어, 나도 준비됐어"
  ---- ACK --------------------->    "확인, 연결 완료"

       [연결 수립]
```

### 스캔 유형별 비교

| 스캔 유형 | 플래그 | 동작 | 장점 | 단점 |
|----------|--------|------|------|------|
| **TCP Connect** (-sT) | SYN→SYN/ACK→ACK | 완전한 3-way | 권한 불필요 | 느림, 로그 남음 |
| **SYN (Half-open)** (-sS) | SYN→SYN/ACK→RST | 연결 미완료 | 빠름, 로그 덜 남음 | sudo 필요 |
| **FIN** (-sF) | FIN만 전송 | 닫힌 포트→RST | 방화벽 우회 가능 | 비표준, 느림 |
| **NULL** (-sN) | 플래그 없음 | 닫힌 포트→RST | 방화벽 우회 | 비표준, 부정확 |
| **Xmas** (-sX) | FIN+PSH+URG | 닫힌 포트→RST | 방화벽 우회 | Windows 미지원 |
| **UDP** (-sU) | UDP 패킷 | 응답 유무로 판단 | UDP 서비스 발견 | 매우 느림 |
| **ACK** (-sA) | ACK만 전송 | 방화벽 규칙 확인 | 방화벽 매핑 | 포트 상태 불명 |

## 실습 2.1: TCP Connect 스캔 (기본)

**이것은 무엇인가?** `-sT`는 운영체제의 일반 소켓 API (connect())로 TCP 연결을 완전히 맺는 스캔이다. 가장 기본적이고 안전하다 (sudo 불필요).

**왜 이것부터 배우는가?** 실제 운영 환경에서 비특권 계정으로 빠르게 확인할 때 유용하며, 모든 스캔 방식을 이해하는 기준점이 된다.

```bash
nmap -sT -p 22,80,443,3000,8002 10.20.30.80
```

**명령 분해:**
- `-sT`: TCP Connect 스캔
- `-p 22,80,443,3000,8002`: 지정된 5개 포트만 스캔 (속도 확보)
- `10.20.30.80`: 대상 IP

**예상 출력:**
```
PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
443/tcp  closed https
3000/tcp open   ppp
8002/tcp open   teradataordbms
```

**결과 해석:**
- `open`: 포트가 열려있고 서비스 응답 중
- `closed`: 포트는 닫혀있으나 호스트는 살아있음 (RST 응답)
- `filtered`: 방화벽이 패킷을 차단 (응답 없음)
- `SERVICE` 컬럼의 이름은 포트 번호 기반 추정일 뿐 — 실제 서비스는 `-sV`로 확인 필요 (`3000/tcp ppp`는 잘못된 추정, 실제는 Node.js)

**이 스캔이 서버에 남기는 흔적:**
- web 서버 access 로그에 원격 IP 연결 시도 기록
- Suricata 같은 IPS가 탐지 (다수 포트 연속 접근 패턴)

## 실습 2.2: SYN 스캔 (스텔스)

**이것은 무엇인가?** `-sS`는 SYN만 보내고 SYN/ACK를 받으면 즉시 RST로 끊는다. 3-way가 완성되지 않으므로 일부 로깅 시스템에 기록이 남지 않는다.

**왜 "스텔스"라 부르는가?** 옛날 서버는 완료된 연결만 로그했다. 현대 IDS/IPS(Suricata 등)는 SYN 스캔 패턴(대량 SYN)을 탐지하므로 완전한 스텔스는 아니다.

```bash
# sudo 필요 (raw socket)
echo 1 | sudo -S nmap -sS -p 1-1000 10.20.30.80 2>/dev/null
```

**명령 분해:**
- `echo 1 | sudo -S`: "1"을 표준입력으로 sudo에 전달 (실습 환경 비밀번호)
- `-sS`: SYN 스캔
- `-p 1-1000`: 1번부터 1000번까지 전 포트

**예상 출력:**
```
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
3000/tcp open  ppp
```

**결과 해석:** `-sT`와 동일한 포트 리스트가 나와야 한다. 차이는 **속도**와 **로그**: SYN 스캔이 2-3배 빠르다.

## 실습 2.3: 서비스 버전 탐지

**이것은 무엇인가?** `-sV`는 열린 포트에 실제로 연결하여 "뭐라고 응답하는지"를 분석하고 서비스 종류와 버전을 식별한다.

**왜 버전이 중요한가?** 버전이 특정되면 해당 버전의 알려진 취약점(CVE)을 검색할 수 있다. 예: `Apache 2.4.49` → **CVE-2021-41773**(경로 순회). 이 정보가 Week 04~07 공격 실습의 출발점이 된다.

```bash
nmap -sV -p 22,80,3000,8002 10.20.30.80
```

**예상 출력:**
```
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.9p1 Ubuntu 3ubuntu0.x (Ubuntu Linux; protocol 2.0)
80/tcp   open  http        Apache httpd 2.4.52 ((Ubuntu))
3000/tcp open  http        Node.js Express framework
8002/tcp open  http        Uvicorn
```

**결과 해석:**
- `OpenSSH 8.9p1`: Ubuntu 22.04 기본 SSH 서버. 브루트포스 시도 대상
- `Apache 2.4.52`: 표준 웹 서버. CVE 검색 → 해당 버전의 취약점 확인
- `Node.js Express`: JuiceShop — 100+ 웹 취약점 실습용 앱
- `Uvicorn`: Python ASGI 서버. **:8002는 SubAgent** (Bastion 원격 실행용) — 외부 공격 대상 아님

## 실습 2.4: OS 탐지

**이것은 무엇인가?** `-O`는 TCP/IP 스택의 동작 차이(TTL, 윈도우 크기, 플래그 순서 등)를 지문(fingerprint)으로 사용하여 운영체제를 추정한다.

```bash
echo 1 | sudo -S nmap -O 10.20.30.80 2>/dev/null | grep -A5 "OS details\|Running\|OS CPE"
```

**예상 출력:**
```
Running: Linux 5.X|6.X
OS CPE: cpe:/o:linux:linux_kernel:5 cpe:/o:linux:linux_kernel:6
OS details: Linux 5.15 - 6.8
```

**결과 해석:**
- `Linux 5.15 - 6.8` 범위로 좁혀진다 (정확한 버전은 `uname`이 필요)
- OS가 확정되면 해당 OS 고유 공격(커널 권한상승, OS 명령 등) 경로가 열린다

## 실습 2.5: 종합 스캔

**이것은 무엇인가?** `-A`는 "공격적(Aggressive)" 종합 스캔. 한 번에 여러 기능을 실행한다.

**-A에 포함되는 것:**
- `-sV`: 서비스 버전 탐지
- `-O`: OS 탐지
- `-sC`: 기본 NSE 스크립트 (HTTP 타이틀, SSH 키 등)
- `--traceroute`: 경로 추적

```bash
echo 1 | sudo -S nmap -A -p 22,80,3000 10.20.30.80 2>/dev/null
```

**언제 -A를 쓰고 언제 쓰지 말아야 하는가?**
- **사용 권장:** 허가받은 단일 타깃을 철저히 조사할 때
- **사용 자제:** 대량 호스트 스캔, 은밀성 필요, IDS 회피 시 → 개별 옵션을 선택적으로 사용

## 실습 2.6: NSE (Nmap Script Engine)

NSE는 Lua 스크립트로 작성된 nmap 확장 기능이다. 약 600개의 공식 스크립트가 있다.

```bash
# HTTP 관련 정보 수집
nmap --script=http-title,http-headers,http-robots.txt -p 80,3000 10.20.30.80
```

**예상 출력:**
```
80/tcp   open  http
| http-title: Apache2 Ubuntu Default Page: It works
| http-headers:
|   Server: Apache/2.4.52 (Ubuntu)
3000/tcp open  http
| http-title: OWASP Juice Shop
```

**NSE 스크립트 카테고리:**
- `auth`: 인증 관련 (기본 패스워드 확인)
- `default`: 기본 실행 스크립트
- `discovery`: 서비스/자산 발견
- `vuln`: 알려진 취약점 탐지 (비공격적)
- `exploit`: 취약점 실제 악용 (⚠️ 허가 없이 사용 금지)

```bash
# 취약점 스캐닝 (보고만, 악용하지 않음)
nmap --script=vuln -p 80,3000 10.20.30.80 2>/dev/null | head -30
```

## 실습 2.7: 네트워크 전체 호스트 발견

```bash
nmap -sn 10.20.30.0/24
```

**명령 분해:**
- `-sn`: ping sweep. 포트 스캔을 하지 않고 "살아있는 호스트"만 식별
- `10.20.30.0/24`: 10.20.30.0~10.20.30.255 범위

**예상 출력:**
```
Nmap scan report for 10.20.30.1 (secu)
Host is up (0.001s latency).
Nmap scan report for 10.20.30.80 (web)
Host is up (0.001s latency).
Nmap scan report for 10.20.30.100 (siem)
Host is up (0.001s latency).
Nmap scan report for 10.20.30.200 (manager)
Host is up (0.0001s latency).
```

**왜 이것을 먼저 하는가?** 수백~수천 IP가 있는 네트워크에서 "어디가 살아있는지" 모르고 전체 포트 스캔하면 시간 낭비. 먼저 호스트 발견으로 목록을 좁힌다.

---

# Part 3: DNS/hosts/ARP 정보 수집 (30분)

## 3.1 DNS 기초 개념

DNS(Domain Name System)는 도메인 이름을 IP 주소로 변환하는 시스템이다.

```
사용자 → "www.example.com 접속하려면?"
           ↓
DNS 서버 → "IP는 93.184.216.34야"
           ↓
사용자 → 93.184.216.34에 접속
```

### DNS 레코드 유형

| 레코드 | 용도 | 예시 | 보안 관점 |
|--------|------|------|---------|
| A | 도메인→IPv4 | example.com → 93.184.216.34 | 서버 IP 파악 |
| AAAA | 도메인→IPv6 | example.com → 2606:2800:... | IPv6 서버 발견 |
| MX | 메일 서버 | example.com → mail.example.com | 메일 서버 위치 |
| NS | 네임서버 | example.com → ns1.example.com | DNS 구조 파악 |
| TXT | 텍스트 정보 | SPF, DKIM 설정 | 보안 설정 확인 |
| CNAME | 별칭 | www → example.com | 실제 도메인 파악 |
| PTR | IP→도메인 (역방향) | 93.184.216.34 → example.com | 서버 용도 확인 |
| SOA | 권한 시작 | 도메인 관리 정보 | DNS 관리자 정보 |

## 실습 3.1: dig 명령어 (외부 DNS 접근 가능한 경우)

**이것은 무엇인가?** `dig`는 Domain Information Groper. DNS 조회의 표준 도구이다.

```bash
# 내부 네트워크(10.20.30.0/24)에는 DNS 서버가 없으므로 외부 예시
dig google.com A +short 2>/dev/null || echo "외부 DNS 접근 불가"
dig google.com MX +short 2>/dev/null
dig google.com TXT +short 2>/dev/null
```

**명령 분해:**
- `dig 도메인 레코드타입`: 해당 레코드만 조회
- `+short`: 간결 출력 (답만)

**예상 출력 (인터넷 가능 시):**
```
142.250.66.46
10 smtp.google.com.
"v=spf1 include:_spf.google.com ~all"
```

**결과 해석:**
- A 레코드: 도메인의 IPv4 주소
- MX 레코드: 메일 서버. 우선순위(10) + FQDN
- TXT 레코드: SPF (메일 발송 정책) — 스푸핑 방어 설정 확인

> **실습 환경 참고:** 내부망에는 DNS가 없어 dig로 실습할 대상이 없다. 대신 `/etc/hosts`와 ARP로 대체한다.

## 실습 3.2: /etc/hosts 파일 분석

**이것은 무엇인가?** `/etc/hosts`는 DNS 질의 전에 참조되는 로컬 호스트 매핑 파일이다. 공격자/방어자 모두에게 네트워크 구조의 단서가 된다.

```bash
# 각 서버의 hosts 파일 확인 (주석과 빈 줄 제거)
for host in "localhost" "10.20.30.1" "10.20.30.80" "10.20.30.100"; do
    if [ "$host" = "localhost" ]; then
        echo "=== $(hostname) ==="
        cat /etc/hosts | grep -v "^#" | grep -v "^$"
    else
        echo "=== $host ==="
        ssh ccc@$host "cat /etc/hosts | grep -v '^#' | grep -v '^$'" 2>/dev/null
    fi
    echo
done
```

**예상 출력:**
```
=== manager ===
127.0.0.1  localhost
10.20.30.1    secu
10.20.30.80   web
10.20.30.100  siem
10.20.30.200  manager

=== 10.20.30.80 ===
127.0.0.1  localhost
127.0.1.1  web
...
```

**결과 해석:**
- manager의 hosts에 전체 서버 맵이 있음 → 침투 성공 시 공격자가 확보할 첫 정보
- 실제 운영 환경에서는 내부 DNS로 옮기거나, hosts에 민감 매핑을 두지 않아야 한다

## 실습 3.3: ARP 테이블로 내부 호스트 발견

**이것은 무엇인가?** ARP(Address Resolution Protocol)는 IP를 MAC 주소로 변환한다. ARP 테이블은 "최근 통신한 이웃 노드" 목록이다.

```bash
arp -a 2>/dev/null || ip neigh show
```

**예상 출력:**
```
? (10.20.30.1) at xx:xx:xx:xx:xx:xx [ether] on ens37
? (10.20.30.80) at xx:xx:xx:xx:xx:xx [ether] on ens37
? (10.20.30.100) at xx:xx:xx:xx:xx:xx [ether] on ens37
```

**왜 ARP가 정찰에 유용한가?**
- ping sweep으로 인해 호스트 존재가 ARP 테이블에 쌓임
- MAC 주소 OUI(앞 3바이트)로 **제조사** 식별 가능 (VMware, 실제 하드웨어 구분)
- `52:54:00:xx:xx:xx` → KVM/QEMU 가상머신 지문

---

# Part 4: 웹 서버 핑거프린팅 + 디렉토리 열거 (40분)

## 4.1 HTTP 헤더 분석

### 실습 4.1: curl로 헤더 분석

**이것은 무엇인가?** HTTP 응답 헤더는 웹 서버의 기술 스택을 알려주는 첫 단서다. `-I` 옵션은 HEAD 요청만 보내 본문 없이 헤더만 받는다.

```bash
echo "=== JuiceShop (3000) ==="
curl -s -I http://10.20.30.80:3000

echo "=== Apache (80) ==="
curl -s -I http://10.20.30.80:80
```

**예상 출력 (JuiceShop):**
```
HTTP/1.1 200 OK
X-Powered-By: Express
Access-Control-Allow-Origin: *
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Feature-Policy: payment 'self'
```

**보안 이슈 분석:**
| 헤더 | 값 | 위험도 | 이유 |
|------|------|--------|------|
| `X-Powered-By` | `Express` | 낮음 | 기술 스택 노출 → 표적 공격 용이 |
| `Access-Control-Allow-Origin` | `*` | **높음** | 모든 도메인에서 API 호출 허용 → CSRF/탈취 |
| `Server` (Apache) | `Apache/2.4.52` | 중간 | 버전 노출 → CVE 검색 가능 |

**반대로 "좋은" 헤더 (JuiceShop은 일부만 적용):**
- `Strict-Transport-Security`: HTTPS 강제
- `Content-Security-Policy`: XSS 방어
- `X-Frame-Options: DENY`: 클릭재킹 방어

### 실습 4.2: 민감 API 노출 확인

**이것은 무엇인가?** JuiceShop은 의도적으로 `/rest/admin/application-configuration` 같은 **인증 없이 접근 가능한 설정 API**가 있다. 실제 서비스에도 종종 발견되는 실수 패턴이다.

```bash
# 애플리케이션 설정 노출
curl -s http://10.20.30.80:3000/rest/admin/application-configuration | python3 -m json.tool | head -30

# API 엔드포인트 확인
curl -s http://10.20.30.80:3000/api/SecurityQuestions | python3 -m json.tool | head -20

# robots.txt
curl -s http://10.20.30.80:3000/robots.txt
curl -s http://10.20.30.80:80/robots.txt
```

**결과 해석:**
- `application-configuration` JSON에 OAuth 키, DB URL 등이 보이면 → **심각한 정보 노출**
- `robots.txt`의 `Disallow` 경로는 "숨기고 싶은" 페이지 — 역설적으로 공격 우선 대상

## 4.2 디렉토리/파일 열거

### 실습 4.3: 수동 경로 탐색

**이것은 무엇인가?** 알려진 관리자 경로 리스트를 순회하며 HTTP 상태 코드로 존재 여부를 판단한다.

**상태 코드 판단 기준:**
- `200 OK`: 페이지 존재, 열림
- `301/302`: 리다이렉트 (존재함)
- `401/403`: 페이지 있으나 권한 필요 (존재함, 보호됨)
- `404`: 존재하지 않음

```bash
PATHS=("/admin" "/login" "/api" "/ftp" "/backup" "/.git" "/.env" "/wp-admin" "/phpmyadmin" "/robots.txt" "/sitemap.xml" "/swagger.json" "/api-docs")

echo "=== JuiceShop (3000) 경로 탐색 ==="
for path in "${PATHS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path")
  if [ "$code" != "404" ] && [ "$code" != "000" ]; then
    echo "  $path → HTTP $code"
  fi
done
```

**명령 분해:**
- `curl -o /dev/null`: 본문은 버린다 (상태만 보면 됨)
- `-w "%{http_code}"`: 상태 코드만 stdout에 출력
- if 조건: 404도 000(연결실패)도 아니면 "뭔가 있음"

**예상 출력:**
```
  /api → HTTP 200
  /ftp → HTTP 200
  /robots.txt → HTTP 200
  /swagger.json → HTTP 200
```

**결과 해석:**
- `/ftp → 200`: **디렉토리 리스팅 활성** (매우 위험) → 실습 4.4에서 파고든다
- `/swagger.json`: API 문서 공개 → 전체 엔드포인트 구조 노출
- `/api → 200`: API 루트 응답 → 하위 경로 열거 대상

### 실습 4.4: FTP 디렉토리 파일 확인

**이것은 무엇인가?** JuiceShop의 `/ftp` 경로는 Week 05 경로 순회(Path Traversal) 실습의 포석이다. 파일 리스트가 JSON으로 노출된다.

```bash
# 디렉토리 리스팅
curl -s http://10.20.30.80:3000/ftp/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for item in data:
        print(f'  {item}')
except:
    print(sys.stdin.read()[:500])
"
```

**예상 출력 (일부):**
```
  {'name': 'acquisitions.md', 'type': 'file', 'size': 1050}
  {'name': 'eastere.gg', 'type': 'file', ...}
  {'name': 'legal.md', ...}
  ...
```

**파일 내용 확인:**
```bash
curl -s http://10.20.30.80:3000/ftp/acquisitions.md | head -10
curl -s http://10.20.30.80:3000/ftp/legal.md | head -10
```

**결과 해석:** 정상 파일도 있지만, 이 중 일부는 **"확장자 필터 우회"**로 금지된 파일(.key 등)에 접근하는 챌린지로 연결된다. Week 05에서 `%00`, `%2500` 인코딩 트릭으로 공략한다.

### 실습 4.5: 단어 목록 기반 디렉토리 열거

**이것은 무엇인가?** `gobuster`, `dirb`, `ffuf` 같은 전용 도구가 쓰는 방식의 축약판. 단어 목록을 순회하며 응답 상태로 존재 여부를 추정한다.

```bash
WORDLIST=("admin" "api" "backup" "config" "console" "dashboard" "db" "debug" "docs" "download" "ftp" "git" "help" "images" "js" "login" "logout" "metrics" "panel" "portal" "private" "public" "rest" "search" "secret" "server-status" "setup" "static" "status" "swagger" "test" "upload" "users" "vendor" "wp-admin")

echo "=== 디렉토리 열거: JuiceShop ==="
for dir in "${WORDLIST[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$dir")
  if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ] || [ "$code" = "403" ]; then
    echo "  /$dir → HTTP $code"
  fi
done
```

**전용 도구와의 차이:**
- 전용 도구는 SecLists 같은 **수만 단어**의 대형 사전을 쓴다
- 전용 도구는 **병렬 스레드**로 수십 배 빠르다
- 위 스크립트는 개념 이해용 — 실무에선 gobuster/ffuf 사용

## 4.3 nikto — 웹 취약점 스캐너

**이것은 무엇인가?** nikto는 6,700개 이상의 알려진 웹 취약점(오래된 CGI, 기본 파일, 서버 잘못된 설정)을 체크하는 전용 스캐너다.

```bash
# nikto 설치 여부 확인
which nikto >/dev/null 2>&1 && {
  echo "=== nikto 스캔 (Apache) ==="
  nikto -h http://10.20.30.80:80 -maxtime 60s 2>/dev/null | head -30
} || echo "nikto 미설치 — apt install nikto로 설치 가능"
```

**-maxtime의 의미:** 60초 제한으로 테스트 시간 제한. 전체 스캔은 10분 이상 걸릴 수 있음.

**nikto 결과의 한계:**
- **FP(False Positive) 많음**: "오래된 취약점 가능성"을 폭넓게 보고
- 수동 검증 필수
- IPS가 즉시 차단 (패턴 매우 뚜렷)

---

# Part 5: Bastion로 정찰 자동화 (40분)

## 5.1 왜 자동화인가?

위에서 학생이 수동으로 실행한 정찰 단계들을:
1. `nmap -sn 10.20.30.0/24` — 호스트 발견
2. `nmap -sV` — 서비스 버전
3. `curl -I` — HTTP 헤더
4. 경로 탐색
5. robots.txt/swagger.json 수집

이 작업을 매번 타이핑하는 대신 **Bastion에게 자연어로 한 번 지시**하면, Bastion가 필요한 Skill들을 선택하여 순차/병렬 실행하고 모든 결과를 evidence로 남긴다.

## 실습 5.1: Bastion 헬스 + Skill 확인

먼저 Bastion이 어떤 정찰용 Skill을 보유하고 있는지 확인한다.

```bash
# Bastion 헬스
curl -s http://10.20.30.200:8003/health | python3 -m json.tool

# 보유 Skill 목록
curl -s http://10.20.30.200:8003/skills | python3 -c "
import sys, json
skills = json.load(sys.stdin)
for s in skills:
    print(f\"  [{s.get('name','?'):25s}] {s.get('description','')[:60]}\")
"
```

**확인 포인트:** `skills` 목록에 `nmap`, `curl`, `ssh_exec`, `http_probe` 등 정찰 관련 Skill이 있는가?

## 실습 5.2: 자연어 정찰 지시 (/ask)

**이것은 무엇인가?** `/ask`는 간단한 질문-답변 API. Bastion가 내부에서 필요한 Skill을 실행하고 자연어 요약을 반환한다.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "10.20.30.0/24 네트워크의 살아있는 호스트를 전부 찾아서 IP와 역할(secu/web/siem/manager)을 표로 정리해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답 (자연어):**
```
10.20.30.0/24 네트워크 호스트 스캔 결과:

| IP             | 역할      | 상태   |
|----------------|-----------|--------|
| 10.20.30.1     | secu      | up     |
| 10.20.30.80    | web       | up     |
| 10.20.30.100   | siem      | up     |
| 10.20.30.200   | manager   | up     |
```

**내부 동작:** Bastion의 LLM이 "호스트 발견" 의도를 인식 → `nmap -sn` Skill 실행 → 결과를 자연어로 요약 → evidence DB에 기록.

## 실습 5.3: 복합 정찰 지시

더 복잡한 요청도 한 번에 가능하다.

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "web 서버(10.20.30.80)의 주요 포트(22, 80, 3000)에서 서비스 버전을 탐지하고, HTTP 응답에서 X-Powered-By와 Server 헤더를 추출해서 공격 표면 요약 보고서를 만들어줘. 발견된 보안 이슈가 있으면 표시해줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

**예상 응답 (요약):**
```
web 서버 공격 표면 요약 (10.20.30.80)

포트 스캔 결과:
- 22/tcp: OpenSSH 8.9p1
- 80/tcp: Apache httpd 2.4.52 (Ubuntu)
- 3000/tcp: Node.js Express (JuiceShop)

HTTP 헤더 분석:
- :80 → Server: Apache/2.4.52 (Ubuntu)
- :3000 → X-Powered-By: Express, Access-Control-Allow-Origin: *

보안 이슈:
1. 서버 버전 노출 (:80 Server 헤더)
2. CORS 완전 개방 (:3000 Access-Control-Allow-Origin: *)
3. Express 프레임워크 노출 (기술 스택 식별 가능)
```

## 실습 5.4: Evidence 확인

이전 두 요청이 evidence DB에 기록되어 있다.

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=10" | python3 -c "
import sys, json
events = json.load(sys.stdin)
for e in events[:10]:
    msg = e.get('user_message','')[:60]
    skill = e.get('skill','?')
    success = e.get('success', False)
    marker = '✓' if success else '✗'
    print(f'  {marker} [{skill:15s}] {msg}')
"
```

**결과 해석:**
- 방금 수행한 정찰 작업들이 `user_message`, `skill`, `success`로 기록되어 있음
- 감사 시 "누가 언제 무엇을 했는지" 완전 추적 가능
- 성공/실패율, 사용된 Skill 빈도 등으로 Bastion 활용도 측정 가능

## 실습 5.5: 수동 vs Bastion 비교 (15분)

학생이 직접 수동으로 nmap + curl 5개를 실행한 뒤, Bastion 한 번의 `/ask`와 비교한다.

| 비교 항목 | 수동 실행 | Bastion 경유 |
|----------|-----------|--------------|
| 타이핑 명령 수 | 5+ | 1 |
| 기록 | 쉘 히스토리만 | evidence DB에 영구 저장 |
| 재현성 | 수동 재입력 | evidence에서 재실행 가능 |
| 결과 요약 | 직접 수작업 | LLM이 자연어 요약 |
| 협업 | 공유 어려움 | evidence 공유로 즉시 공유 |
| 단점 | 빠름, 세밀 제어 | LLM 해석 오차 가능 |

**결론:** 빠른 1회성 확인은 수동, 반복/기록/공유가 필요하면 Bastion.

---

# Part 6: ATT&CK 매핑 정리 (20분)

## 6.1 오늘 실습의 ATT&CK 매핑

| 실습 | ATT&CK 기법 | 전술 |
|------|------------|------|
| nmap 포트 스캔 (-sT, -sS) | T1046 Network Service Scanning | Discovery |
| nmap -sV 서비스 탐지 | T1046 | Discovery |
| nmap -O OS 탐지 | T1046 | Discovery |
| nmap -sn 네트워크 호스트 발견 | T1046 / T1018 | Discovery |
| HTTP 헤더 분석 | T1592 Gather Victim Host Info | Reconnaissance |
| robots.txt / swagger.json 확인 | T1595.003 Wordlist Scanning | Reconnaissance |
| FTP 디렉토리 열거 | T1595.003 | Reconnaissance |
| 설정 API 무인증 접근 | T1592.004 Client Configurations | Reconnaissance |
| /etc/hosts 조회 | T1016 System Network Configuration | Discovery |
| ARP 테이블 조회 | T1016 | Discovery |
| Bastion 자연어 정찰 | (여러 기법 조합) | Reconnaissance |

## 6.2 탐지 관점 (Blue Team의 시각)

오늘 실습한 공격 기법들을 방어자는 어떻게 탐지하는가?

| 공격 | 탐지 로그/신호 | 탐지 도구 |
|------|---------------|----------|
| nmap SYN 스캔 | 짧은 시간 내 다수 포트 SYN 패킷 | Suricata alert (포트 스캔 서명) |
| nmap -A | 비표준 패킷 조합 (FIN/XMAS) | Suricata rule (malformed flags) |
| 경로 브루트포스 | 대량 404 응답 | Apache access log 분석 |
| /robots.txt, /admin 연속 접근 | 웹 크롤링 패턴 | ModSecurity OWASP CRS |

Week 08 이후 (SOC 과정) 에서 이 탐지를 실습한다.

---

## 과제 (다음 주까지)

### 과제 1: 종합 정보수집 보고서 (60점)

web 서버(10.20.30.80)에 대해 다음 정보를 수집하고 md 보고서를 작성하라.

| 항목 | 수집 방법 | 배점 |
|------|---------|------|
| 열린 포트 + 서비스 버전 | `nmap -sV` | 15점 |
| OS 정보 | `nmap -O` 또는 HTTP 헤더 추론 | 5점 |
| HTTP 응답 헤더 분석 (:80, :3000) | `curl -I` | 10점 |
| 발견된 웹 경로 (최소 10개) | 수동 탐색 또는 스크립트 | 15점 |
| FTP 디렉토리 내용 | `curl /ftp/` | 5점 |
| 보안 이슈 식별 (최소 3개) | 위 결과 분석 | 10점 |

**보안 이슈 예시:**
- 서버 버전 노출 (Server 헤더)
- CORS 완전 개방 (`Access-Control-Allow-Origin: *`)
- FTP 디렉토리 리스팅
- 관리자 설정 API 무인증 접근 (`/rest/admin/application-configuration`)

### 과제 2: Bastion 자연어 정찰 (40점)

Bastion `/ask` API로 정찰을 수행하고 evidence를 제출하라.

**요구사항 (각 10점):**
1. 자연어 1회 요청으로 **네트워크 전체 호스트 발견** 결과 제출
2. 자연어 1회 요청으로 **web 서버 공격 표면 요약** 결과 제출
3. 자연어 1회 요청으로 **secu/web/siem 3대 서버의 SSH 버전 비교** 결과 제출
4. 위 3개 요청이 `/evidence`에 기록된 스크린샷

---

## 다음 주 예고
**Week 03: 웹 애플리케이션 구조 이해**
- HTTP 프로토콜 심층 분석 (메서드, 상태코드, 쿠키, 세션)
- 웹 아키텍처 (프론트엔드/백엔드, REST API, DB)
- JuiceShop 구조 분석
- 브라우저 개발자 도구 활용
- Burp Suite/ZAP 프록시 기초

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **정찰** | Reconnaissance | 대상 시스템에 대한 정보를 수집하는 단계 | 건물 주변 답사 |
| **수동 정찰** | Passive Recon | 대상에 패킷을 보내지 않고 정보 수집 | 건물 외부 관찰만 |
| **능동 정찰** | Active Recon | 대상에 직접 패킷을 보내 정보 수집 | 건물 안에 들어가 확인 |
| **OSINT** | Open Source Intelligence | 공개된 정보를 수집·분석 | 신문·뉴스로 정보 수집 |
| **DNS** | Domain Name System | 도메인을 IP로 변환하는 시스템 | 전화번호부 |
| **ARP** | Address Resolution Protocol | IP를 MAC 주소로 변환 | 방 호수 → 사람 얼굴 |
| **NSE** | Nmap Scripting Engine | nmap의 Lua 스크립트 확장 | nmap 플러그인 |
| **배너 그래빙** | Banner Grabbing | 서비스 연결 시 나오는 안내 문자열 수집 | 가게 간판 촬영 |
| **핑거프린팅** | Fingerprinting | 지문으로 대상 시스템 식별 | 필체 감정 |
| **디렉토리 열거** | Directory Enumeration | 웹 서버의 숨겨진 경로를 순차 시도 | 문 하나씩 두드려보기 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 실제로 조작하는 솔루션의 기능·경로·파일·설정 요점.

### Nmap

> **역할:** 포트 스캔·서비스 탐지·OS 탐지·NSE 스크립트
> **실행 위치:** manager (10.20.30.200) 또는 학생 PC
> **호출:** `nmap` CLI

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/usr/share/nmap/scripts/` | NSE Lua 스크립트 모음 (vuln, default, discovery 등) |
| `/usr/share/nmap/nmap-services` | 포트↔서비스 이름 매핑 (추정용 — 실제 서비스는 -sV로 확인) |
| `/usr/share/nmap/nmap-os-db` | OS 탐지용 TCP/IP 스택 지문 DB |

**핵심 옵션**

| 옵션 | 의미 | 사용 시점 |
|------|------|----------|
| `-sT` | TCP Connect 스캔 | sudo 없이 기본 스캔 |
| `-sS` | SYN 스캔 (스텔스) | sudo 가능 + 은밀성 필요 시 |
| `-sV` | 서비스 버전 탐지 | CVE 매칭 필요 시 |
| `-O` | OS 탐지 | 타깃 OS 확정 필요 시 |
| `-A` | 종합 스캔 (sV+O+sC+traceroute) | 단일 타깃 정밀 조사 |
| `--script vuln` | 취약점 카테고리 | 알려진 취약점 확인 |
| `-T0..T5` | 타이밍 (느림↔빠름) | T2는 IDS 회피, T4는 실습 기본 |
| `-oA 파일명` | 3포맷 저장 (.nmap/.gnmap/.xml) | 결과 보관·스크립트 파싱 |
| `-p 범위` | 특정 포트만 (예: 1-1000, 22,80) | 속도 확보 |
| `-p-` | 전 포트(1-65535) | 철저한 조사 |

**결과 해석 포인트**

- `open`: 서비스 응답 중
- `closed`: 호스트는 살아있으나 포트 닫힘 (RST 응답)
- `filtered`: 방화벽 차단 (응답 없음)
- SERVICE 컬럼은 포트 기반 추정 → 실제는 -sV로 확인
- -sV의 `fingerprint` 출력은 DB에 없는 서비스 지문 (nmap dev에 제출 가능)

**실습 환경 주의**

- secu(10.20.30.1)에 Suricata가 떠 있어 대량/빠른 스캔은 alert 발생
- `-T2` + `--max-retries 1`로 느리게 + 재전송 최소화하면 탐지 회피 가능 (Week 09 주제)

### curl

> **역할:** HTTP 클라이언트 (GET/POST/HEAD 등)
> **실행 위치:** manager 또는 학생 PC
> **호출:** `curl` CLI

**핵심 옵션**

| 옵션 | 의미 |
|------|------|
| `-s` | silent (진행률 숨김) |
| `-I` | HEAD 요청 (헤더만) |
| `-X METHOD` | HTTP 메서드 지정 (GET/POST/PUT/DELETE) |
| `-H "헤더: 값"` | 커스텀 헤더 추가 |
| `-d '본문'` | 요청 본문 전송 (POST/PUT) |
| `-o 파일` | 응답 저장 |
| `-w "포맷"` | 상태 코드·응답시간 등 정보만 출력 |
| `-k` | SSL 인증서 검증 무시 (실습 환경) |
| `-L` | 리다이렉트 자동 따라감 |

**정찰에 자주 쓰는 패턴**

```bash
# 상태 코드만
curl -s -o /dev/null -w "%{http_code}" URL

# 응답 시간 측정
curl -s -o /dev/null -w "%{time_total}s\n" URL

# 리다이렉트 체인
curl -s -I -L URL | grep -i '^HTTP\|^Location'
```

### Bastion API (:8003)

이번 주 사용하는 엔드포인트만 정리.

| 메서드 | 경로 | 용도 |
|--------|------|------|
| GET | `/health` | Bastion 가동 확인 |
| GET | `/skills` | 사용 가능한 Skill 목록 |
| POST | `/ask` | 자연어 질문 (단답형) |
| GET | `/evidence?limit=N` | 최근 N건 작업 기록 |

> `/chat`, `/playbooks`, `/assets`, `/onboard`는 이번 주 사용하지 않음.

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
