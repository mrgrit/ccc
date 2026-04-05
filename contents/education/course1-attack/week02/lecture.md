# Week 02: 정보수집과 정찰 (Reconnaissance) — 상세 버전

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
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 정보수집 개론 (이론) | 강의 |
| 0:30-1:10 | nmap 심화 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:50 | DNS/WHOIS 정보 수집 실습 | 실습 |
| 1:50-2:30 | 웹 서버 핑거프린팅 + 디렉토리 열거 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | OpsClaw 정찰 자동화 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 복습 퀴즈 + 과제 | 토론/퀴즈 |

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

```
클라이언트                             서버

  ---- SYN --------------------->    "연결하고 싶어"
  <--- SYN/ACK ------------------    "알겠어, 나도 준비됐어"
  ---- ACK --------------------->    "확인, 연결 완료"

       [연결 수립]
```

각 nmap 스캔은 이 핸드셰이크를 어떻게 변형하느냐에 따라 다르다.

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

> **실습 목적**: nmap 포트 스캔을 통해 대상 시스템의 열린 포트와 서비스를 식별하는 정찰 기법을 직접 수행한다
>
> **배우는 것**: TCP Connect, SYN, UDP 등 스캔 방식별 동작 원리와 차이를 이해하고, 스캔 결과에서 공격 표면을 파악하는 방법을 배운다
>
> **결과 해석**: open/closed/filtered 상태가 표시되며, open 포트는 해당 서비스가 접근 가능함을 의미한다
>
> **실전 활용**: 모의해킹 초기 단계에서 대상 네트워크의 공격 표면을 체계적으로 파악하는 데 사용된다

```bash
# 가장 기본적인 스캔 (sudo 불필요)
nmap -sT -p 22,80,443,3000,8002 10.20.30.80
# 예상 출력:
# PORT     STATE  SERVICE
# 22/tcp   open   ssh
# 80/tcp   open   http
# 443/tcp  closed https
# 3000/tcp open   ppp
# 8002/tcp open   teradataordbms
```

> **왜 이렇게 하는가?**
> TCP Connect는 완전한 연결을 맺으므로 가장 정확하지만, 서버 로그에 연결이 기록된다.
> 은밀한 스캔이 필요하면 SYN 스캔을 사용한다.

## 실습 2.2: SYN 스캔 (스텔스)

```bash
# SYN 스캔 (sudo 필요, 더 빠르고 은밀)
echo 1 | sudo -S nmap -sS -p 1-1000 10.20.30.80 2>/dev/null
# 예상 출력: (TCP Connect보다 빠르게 결과 나옴)
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# ...
```

> **SYN 스캔이 "스텔스"인 이유:**
> 3-way 핸드셰이크를 완료하지 않고 RST를 보내므로, 일부 서버에서 연결 로그가 남지 않는다.
> 다만 현대 IDS/IPS(Suricata 등)는 SYN 스캔도 탐지한다.

## 실습 2.3: 서비스 버전 탐지

```bash
# 주요 포트의 서비스 버전 확인
nmap -sV -p 22,80,3000,8002 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE     VERSION
# 22/tcp   open  ssh         OpenSSH 8.9p1 Ubuntu 3ubuntu0.x (Ubuntu Linux; protocol 2.0)
# 80/tcp   open  http        Apache httpd 2.4.52 ((Ubuntu))
# 3000/tcp open  http        Node.js Express framework
# 8002/tcp open  http        Uvicorn
```

> **왜 버전이 중요한가?**
> 소프트웨어 버전을 알면 CVE 데이터베이스에서 알려진 취약점을 검색할 수 있다.
> 예: Apache 2.4.49 → CVE-2021-41773 (경로 순회 취약점)
> Week 04~07에서 이 정보를 활용한다.

## 실습 2.4: OS 탐지

```bash
echo 1 | sudo -S nmap -O 10.20.30.80 2>/dev/null | grep -A5 "OS details\|Running\|OS CPE"
# 예상 출력:
# Running: Linux 5.X|6.X
# OS CPE: cpe:/o:linux:linux_kernel:5 cpe:/o:linux:linux_kernel:6
# OS details: Linux 5.15 - 6.8
```

## 실습 2.5: 종합 스캔 (-A)

```bash
# -A = -sV + -O + -sC + --traceroute (종합)
echo 1 | sudo -S nmap -A -p 22,80,3000 10.20.30.80 2>/dev/null
# 이 명령은 모든 것을 한 번에 수행:
# - 서비스 버전 (-sV)
# - OS 탐지 (-O)
# - 기본 스크립트 (-sC): HTTP 타이틀, SSH 키 등
# - traceroute
```

## 실습 2.6: nmap 스크립트 엔진 (NSE)

```bash
# HTTP 관련 스크립트 실행
nmap --script=http-title,http-headers,http-robots.txt -p 80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 80/tcp   open  http
# | http-title: Apache2 Ubuntu Default Page: It works
# | http-headers:
# |   Server: Apache/2.4.52 (Ubuntu)
# | http-robots.txt: ...
# 3000/tcp open  ppp
# | http-title: OWASP Juice Shop

# 취약점 스캔 스크립트
nmap --script=vuln -p 80,3000 10.20.30.80 2>/dev/null | head -30
```

> **NSE 스크립트 카테고리:**
> - `auth`: 인증 관련 (기본 패스워드 확인)
> - `default`: 기본 실행 스크립트
> - `discovery`: 서비스 발견
> - `vuln`: 취약점 탐지
> - `exploit`: 취약점 악용 (주의!)

## 실습 2.7: 전체 내부 네트워크 스캔

```bash
# 10.20.30.0/24 네트워크에서 살아있는 호스트 발견
nmap -sn 10.20.30.0/24
# 예상 출력:
# Nmap scan report for 10.20.30.1 (secu)
# Host is up (0.001s latency).
# Nmap scan report for 10.20.30.80 (web)
# Host is up (0.001s latency).
# Nmap scan report for 10.20.30.100 (siem)
# Host is up (0.001s latency).
# Nmap scan report for 10.20.30.201 (opsclaw)
# Host is up (0.0001s latency).
```

> **-sn 옵션:** 포트 스캔 없이 호스트 발견만 수행 (ping sweep)
> 네트워크에 어떤 서버가 있는지 먼저 파악하는 것이 정보수집의 첫걸음이다.

---

# Part 3: DNS/WHOIS 정보 수집 (30분)

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

## 실습 3.1: dig 명령어

```bash
# A 레코드 조회 (실습 환경에는 DNS가 없으므로 외부 예시)
# 내부 네트워크의 역방향 조회
dig -x 10.20.30.80 @10.20.30.1 2>/dev/null || echo "DNS 서버 없음 (실습 환경)"

# 외부 도메인 예시 (인터넷 연결 시)
dig google.com A +short 2>/dev/null || echo "외부 DNS 접근 불가"
dig google.com MX +short 2>/dev/null || echo "외부 DNS 접근 불가"
dig google.com TXT +short 2>/dev/null || echo "외부 DNS 접근 불가"
```

> **실습 환경 참고:** 우리 내부 네트워크(10.20.30.0/24)에는 별도 DNS 서버가 없다.
> 실제 모의해킹에서는 DNS 조회가 중요한 정보수집 방법이지만,
> 이 실습에서는 IP 기반으로 직접 접근한다.

## 실습 3.2: /etc/hosts 파일 분석

```bash
# 각 서버의 hosts 파일 확인
echo "=== opsclaw ===" && cat /etc/hosts | grep -v "^#" | grep -v "^$"
echo "=== web ===" && sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "cat /etc/hosts | grep -v '^#' | grep -v '^$'" 2>/dev/null
echo "=== secu ===" && sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 "cat /etc/hosts | grep -v '^#' | grep -v '^$'" 2>/dev/null
echo "=== siem ===" && sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "cat /etc/hosts | grep -v '^#' | grep -v '^$'" 2>/dev/null
```

> **왜 hosts 파일을 확인하는가?**
> /etc/hosts는 로컬 DNS 오버라이드이다. 여기에 내부 서버명과 IP가 매핑되어 있으면
> 네트워크 구조를 파악하는 데 유용한 정보를 제공한다.

## 실습 3.3: ARP 테이블로 내부 호스트 발견

```bash
# ARP 테이블 확인 (같은 네트워크의 MAC 주소)
arp -a
# 예상 출력:
# ? (10.20.30.1) at xx:xx:xx:xx:xx:xx [ether] on ens37
# ? (10.20.30.80) at xx:xx:xx:xx:xx:xx [ether] on ens37
# ? (10.20.30.100) at xx:xx:xx:xx:xx:xx [ether] on ens37

# 또는 ip neigh show
ip neigh show
```

---

# Part 4: 웹 서버 핑거프린팅 + 디렉토리 열거 (40분)

## 4.1 HTTP 헤더 분석

### 실습 4.1: curl로 헤더 분석

```bash
# JuiceShop 헤더 분석
echo "=== JuiceShop (3000) ==="
curl -s -I http://10.20.30.80:3000 2>/dev/null
# 예상 출력:
# HTTP/1.1 200 OK
# X-Powered-By: Express          ← Node.js Express 프레임워크
# Access-Control-Allow-Origin: * ← CORS 완전 개방 (보안 이슈!)
# X-Content-Type-Options: nosniff
# X-Frame-Options: SAMEORIGIN
# Feature-Policy: payment 'self'

echo ""
echo "=== Apache (80) ==="
curl -s -I http://10.20.30.80:80 2>/dev/null
# 예상 출력:
# HTTP/1.1 200 OK
# Server: Apache/2.4.52 (Ubuntu) ← 서버 소프트웨어+버전 노출
```

> **보안 분석 포인트:**
> - `X-Powered-By: Express` → 기술 스택 노출 (제거 권장)
> - `Access-Control-Allow-Origin: *` → 모든 도메인에서 API 호출 가능 (위험)
> - `Server: Apache/2.4.52` → 버전 노출 → CVE 검색 가능

### 실습 4.2: 상세 핑거프린팅

```bash
# JuiceShop 설정 파일 접근 시도
curl -s http://10.20.30.80:3000/rest/admin/application-configuration 2>/dev/null | python3 -m json.tool | head -30
# 예상 출력: 서버 설정 JSON (DB URL, OAuth 키 등 민감 정보 노출)

# JuiceShop API 엔드포인트 발견
curl -s http://10.20.30.80:3000/api/SecurityQuestions 2>/dev/null | python3 -m json.tool | head -20
# 예상 출력: 보안 질문 목록

# robots.txt 확인
curl -s http://10.20.30.80:3000/robots.txt 2>/dev/null
# 예상 출력: Disallow 경로들 (숨기려는 페이지들)

curl -s http://10.20.30.80:80/robots.txt 2>/dev/null
```

## 4.2 디렉토리/파일 열거

### 실습 4.3: 수동 경로 탐색

```bash
# 일반적인 경로들을 curl로 확인
PATHS=("/admin" "/login" "/api" "/ftp" "/backup" "/.git" "/.env" "/wp-admin" "/phpmyadmin" "/robots.txt" "/sitemap.xml" "/swagger.json" "/api-docs")

echo "=== JuiceShop (3000) 경로 탐색 ==="
for path in "${PATHS[@]}"; do                          # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path" 2>/dev/null)
  if [ "$code" != "404" ] && [ "$code" != "000" ]; then
    echo "  $path → HTTP $code"
  fi
done

echo ""
echo "=== Apache (80) 경로 탐색 ==="
for path in "${PATHS[@]}"; do                          # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80$path" 2>/dev/null)
  if [ "$code" != "404" ] && [ "$code" != "000" ]; then
    echo "  $path → HTTP $code"
  fi
done
```

> **왜 이렇게 하는가?**
> 웹 서버에는 일반 사용자에게는 보이지 않지만 URL을 직접 입력하면 접근 가능한
> 관리자 페이지, API 문서, 백업 파일 등이 있을 수 있다.
> /ftp/, /.git/, /.env 등은 자주 노출되는 민감 경로이다.

### 실습 4.4: FTP 디렉토리 열거

```bash
# JuiceShop FTP 디렉토리 (Week 01에서 발견)
curl -s http://10.20.30.80:3000/ftp/ 2>/dev/null | python3 -c "  # silent 모드
import sys, json
try:
    data = json.load(sys.stdin)
    for item in data:                                  # 반복문 시작
        print(f'  {item}')
except:
    print(sys.stdin.read()[:500])
"

# FTP 내 파일 하나씩 접근
curl -s http://10.20.30.80:3000/ftp/acquisitions.md 2>/dev/null | head -10  # silent 모드
curl -s http://10.20.30.80:3000/ftp/legal.md 2>/dev/null | head -10  # silent 모드
```

### 실습 4.5: gobuster 디렉토리 열거 (설치되어 있는 경우)

```bash
# gobuster가 없으면 간단한 bash 스크립트로 대체
WORDLIST=("admin" "api" "backup" "config" "console" "dashboard" "db" "debug" "docs" "download" "ftp" "git" "help" "images" "js" "login" "logout" "metrics" "panel" "portal" "private" "public" "rest" "search" "secret" "server-status" "setup" "static" "status" "swagger" "test" "upload" "users" "vendor" "wp-admin")

echo "=== 디렉토리 열거: JuiceShop ==="
for dir in "${WORDLIST[@]}"; do                        # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$dir" 2>/dev/null)
  if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ] || [ "$code" = "403" ]; then
    echo "  /$dir → HTTP $code"
  fi
done
```

## 4.3 nikto — 웹 취약점 스캐너

```bash
# nikto가 설치되어 있으면 실행 (없으면 건너뜀)
which nikto >/dev/null 2>&1 && {
  echo "=== nikto 스캔 (Apache) ==="
  nikto -h http://10.20.30.80:80 -maxtime 60s 2>/dev/null | head -30  # 웹 서버 취약점 스캐너
} || echo "nikto 미설치 — 건너뜀"
```

---

# Part 5: OpsClaw로 정찰 자동화 (30분)

## 실습 5.1: OpsClaw 정찰 프로젝트

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week02-recon","request_text":"Week 02: 정보수집 자동화","master_mode":"external"}')  # 요청 데이터(body)
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null  # silent 모드 / POST 요청 / API 인증 / OpsClaw 프로젝트
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null  # silent 모드 / POST 요청 / API 인증 / OpsClaw 프로젝트

# 정찰 태스크 병렬 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {"order":1,"title":"네트워크 호스트 발견","instruction_prompt":"nmap -sn 10.20.30.0/24 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"web 포트스캔","instruction_prompt":"nmap -sV -p 22,80,443,3000,8002,8080,8081,8082 10.20.30.80 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"JuiceShop 헤더","instruction_prompt":"curl -s -I http://10.20.30.80:3000","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":4,"title":"JuiceShop FTP 열거","instruction_prompt":"curl -s http://10.20.30.80:3000/ftp/","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":5,"title":"siem 포트 확인","instruction_prompt":"nmap -sV -p 22,443,1514,9400,55000 10.20.30.100 2>/dev/null","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]} (성공:{d[\"tasks_ok\"]}, 실패:{d[\"tasks_failed\"]})')
for t in d.get('task_results',[]):                     # 반복문 시작
    print(f'  [{t[\"order\"]}] {t[\"title\"]} → {t[\"status\"]}')
"
```

### 결과 확인

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
# Evidence 요약
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "  # API 인증 키
import sys,json; d=json.load(sys.stdin)
print(f'증적: {d[\"total\"]}건, 성공률: {d[\"success_rate\"]*100:.0f}%')
"

# Replay 타임라인
curl -s "http://localhost:8000/projects/$PID/replay" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -c "  # API 인증 키
import sys,json; d=json.load(sys.stdin)
print(f'총 보상: {d[\"total_reward\"]}')
for s in d['timeline']:                                # 반복문 시작
    print(f'  [{s[\"task_order\"]}] {s[\"task_title\"]:25s} reward={s[\"total_reward\"]}')
"
```

> **직접 실행 vs OpsClaw 비교:**
> 위 5개 정찰 태스크를 직접 SSH로 실행하면 → 아무 기록도 남지 않음
> OpsClaw로 실행하면 → 5건 evidence + 5건 PoW 블록 + 5건 reward + replay 가능

---

# Part 6: ATT&CK 매핑 + 복습 + 과제 (20분)

## 6.1 오늘 실습의 ATT&CK 매핑

| 실습 | ATT&CK 기법 | 전술 |
|------|------------|------|
| nmap 포트 스캔 | T1046 Network Service Scanning | Discovery |
| nmap -sV 서비스 탐지 | T1046 | Discovery |
| nmap -O OS 탐지 | T1046 | Discovery |
| 네트워크 호스트 발견 | T1046 | Discovery |
| HTTP 헤더 분석 | T1592 Gather Victim Host Info | Reconnaissance |
| robots.txt 확인 | T1595.003 Wordlist Scanning | Reconnaissance |
| FTP 디렉토리 열거 | T1595.003 | Reconnaissance |
| 설정 파일 접근 | T1592.004 Client Configurations | Reconnaissance |

## 자가 점검 퀴즈 (10문항)

**Q1.** 수동적 정찰과 능동적 정찰의 가장 큰 차이는?
- (a) 속도  (b) 대상 시스템에 패킷 도달 여부  (c) 도구의 종류  (d) 법적 허용 여부

**Q2.** nmap -sS 스캔의 특징은?
- (a) UDP 스캔  (b) TCP 3-way 완료  (c) SYN만 보내고 RST  (d) FIN만 전송

**Q3.** HTTP 헤더의 `X-Powered-By: Express`는 무엇을 의미하는가?
- (a) 전원 공급  (b) Node.js Express 사용  (c) 보안 기능  (d) 캐시 설정

**Q4.** nmap에서 서비스 버전을 탐지하는 옵션은?
- (a) -sS  (b) -O  (c) -sV  (d) -sn

**Q5.** robots.txt의 보안 관점에서의 의미는?
- (a) 검색 엔진 최적화  (b) 숨기려는 경로 정보 노출  (c) 방화벽 설정  (d) 서버 성능

**Q6.** T1046은 어떤 ATT&CK 기법인가?
- (a) SQL Injection  (b) Network Service Scanning  (c) 피싱  (d) 랜섬웨어

**Q7.** `Access-Control-Allow-Origin: *`가 보안 이슈인 이유는?
- (a) 느려짐  (b) 모든 도메인에서 API 호출 가능  (c) 암호화 비활성  (d) 로그 미생성

**Q8.** ARP 테이블에서 확인할 수 있는 정보는?
- (a) DNS 레코드  (b) 같은 네트워크의 MAC 주소  (c) SSL 인증서  (d) 방화벽 룰

**Q9.** nmap -sn 10.20.30.0/24의 용도는?
- (a) 포트 스캔  (b) 취약점 스캔  (c) 호스트 발견 (ping sweep)  (d) OS 탐지

**Q10.** 정보수집 단계에서 가장 중요한 것은?
- (a) 빠른 공격  (b) 공격 표면 파악  (c) 데이터 삭제  (d) 권한 상승

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:b, Q6:b, Q7:b, Q8:b, Q9:c, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 종합 정보수집 보고서 (60점)

web 서버(10.20.30.80)에 대해 다음 정보를 수집하고 보고서를 작성하라.

| 항목 | 수집 방법 | 배점 |
|------|---------|------|
| 열린 포트 + 서비스 버전 | nmap -sV | 15점 |
| OS 정보 | nmap -O 또는 기타 | 5점 |
| HTTP 응답 헤더 분석 (80, 3000) | curl -I | 10점 |
| 발견된 웹 경로 (최소 10개) | 수동 탐색 or 스크립트 | 15점 |
| FTP 디렉토리 내용 | curl /ftp/ | 5점 |
| 보안 이슈 식별 (최소 3개) | 위 결과 분석 | 10점 |

**보안 이슈 예시:**
- 서버 버전 노출 (Server 헤더)
- CORS 완전 개방
- FTP 디렉토리 리스팅
- 관리자 설정 API 무인증 접근

### 과제 2: OpsClaw 자동화 (40점)

OpsClaw execute-plan으로 과제 1의 정보수집을 자동화하라.

- 최소 5개 태스크, parallel=true — 20점
- evidence/summary 결과 캡처 — 10점
- replay 결과에서 ATT&CK 기법 매핑 — 10점

---

## 다음 주 예고
**Week 03: 웹 애플리케이션 구조 이해**
- HTTP 프로토콜 심층 분석 (메서드, 상태코드, 쿠키, 세션)
- 웹 아키텍처 (프론트엔드/백엔드, REST API, DB)
- JuiceShop 구조 분석
- 브라우저 개발자 도구 활용
- Burp Suite/ZAP 프록시 기초

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

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
