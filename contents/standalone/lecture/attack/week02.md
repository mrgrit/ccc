# Week 02 — 정찰 (Reconnaissance)

> 본 주차는 PTES 의 **2단계 Intelligence Gathering**. attacker 컨테이너에서 nmap +
> recon-ng + theHarvester + dirb 4 도구로 6v6 환경의 자산 가시화.

## 학습 목표

1. Active vs Passive 정찰 차이
2. nmap 의 5 핵심 스캔 (-sT / -sS / -sV / -O / -sU)
3. nikto / dirb 의 웹 정찰
4. recon-ng 의 OSINT 모듈
5. ATT&CK Reconnaissance Tactic (TA0043) Technique 매핑
6. 정찰 결과 정리·문서화

## 1. Active vs Passive

| 구분 | 의미 | 예 |
|------|------|-----|
| Passive | 대상에 trafic 발생 안 함 | OSINT (whois, dns) |
| Active | 대상에 직접 packet | nmap port scan |

운영 환경: passive 먼저 (탐지 안 됨) → active 마지막 (필요 시).

## 2. nmap 의 5 핵심 스캔

### 2.1 TCP Connect (`-sT`)

```
nmap -sT -p 22,80,443 10.20.30.1
```

3-way handshake 완료. 권한 불필요. detect 쉬움.

### 2.2 TCP SYN stealth (`-sS`)

```
sudo nmap -sS -p- 10.20.30.1
```

SYN/SYN-ACK 후 RST. half-open. root 필요. detect 더 어려움.

### 2.3 서비스 버전 (`-sV`)

```
nmap -sV -p 22,80 10.20.30.1
```

각 포트의 daemon banner + version.

### 2.4 OS detection (`-O`)

```
sudo nmap -O 10.20.30.1
```

TCP/IP stack fingerprint.

### 2.5 UDP (`-sU`)

```
sudo nmap -sU -p 53,123,161 10.20.30.1
```

UDP 는 stateless → 느림 + 부정확.

### 2.6 NSE (Nmap Scripting Engine)

```
nmap --script http-enum 10.20.30.1
nmap --script vuln 10.20.30.1
```

700+ script. HTTP enumeration, vuln detection, brute force.

## 3. 웹 정찰

### 3.1 nikto

```
nikto -h http://juice.6v6.lab -port 80
```

웹서버 banner + 잘못된 설정 + 알려진 취약점.

### 3.2 dirb (디렉토리 brute)

```
dirb http://juice.6v6.lab/ /usr/share/dirb/wordlists/common.txt
```

숨겨진 디렉토리 (admin, backup, .git 등) 탐색.

### 3.3 dirsearch / ffuf (모던 대안)

```
ffuf -u http://juice.6v6.lab/FUZZ -w /usr/share/dirb/wordlists/common.txt
```

## 4. recon-ng (OSINT)

```
recon-ng
[recon-ng] > marketplace install hackertarget
[recon-ng] > modules load recon/domains-hosts/hackertarget
[recon-ng] > options set SOURCE example.com
[recon-ng] > run
```

OSINT module 로 도메인 / IP / 이메일 수집.

## 5. theHarvester

```
theHarvester -d example.com -b google,bing
```

이메일 + subdomain + IP 수집.

## 6. ATT&CK Reconnaissance Tactic

| Technique | 의미 | 도구 |
|-----------|------|------|
| T1595.001 Active Scanning - IP block | -sT/-sS | nmap |
| T1595.002 Active Scanning - Vuln scan | -sV / NSE | nmap |
| T1592 Gather Victim Host | Active | nmap -O |
| T1594 Search Victim-Owned Websites | passive | nikto / dirb |
| T1589 Gather Victim Identity | passive | theHarvester |

## 7. 실습 1~5

### 1 — nmap 기본 5 스캔

```bash
# -sT TCP connect — 3-way handshake 완료. 권한 불필요. detect 쉬움.
#   장점: 일반 사용자 권한 OK
#   단점: 완전한 conn → Suricata / Wazuh detection 즉시
ssh 6v6-attacker 'nmap -sT -p 22,80,443 10.20.30.1'
# 예상 출력:
#   PORT     STATE  SERVICE
#   22/tcp   closed ssh        (fw 의 input chain 이 22 허용하지 않음)
#   80/tcp   open   http       (HAProxy frontend)
#   443/tcp  open   https      (HAProxy frontend TLS)

# -sV 서비스 버전 — 각 포트의 daemon banner + version 추출
#   nmap 의 nmap-service-probes DB (10000+ signature) 사용
ssh 6v6-attacker 'sudo nmap -sV -p 80 10.20.30.1'
# 예상 출력: 80/tcp open http HAProxy 2.4.x

# -O OS detection — TCP/IP stack fingerprint 분석
#   root 권한 필요 (raw socket)
ssh 6v6-attacker 'sudo nmap -O 10.20.30.1 2>&1 | head -20'
# 예상 출력: OS detection: Linux 6.x kernel
```

### 2 — 6v6 환경의 전체 IP block 스캔

```bash
# -sn ping sweep — port scan 안 함, 살아 있는 host 만 식별
#   ICMP echo + TCP SYN to 443 + TCP ACK to 80 + ICMP timestamp 4 방법 동시
#   /24 = 254 host (네트워크/브로드캐스트 제외) → 보통 10초 안에 완료
ssh 6v6-attacker 'nmap -sn 10.20.30.0/24 2>&1 | head -20'
# 예상 출력 (ext 의 활성 host):
#   Nmap scan report for 10.20.30.1     (fw)
#   Nmap scan report for 10.20.30.201   (bastion)
#   Nmap scan report for 10.20.30.202   (attacker — 자신)
#   Nmap done: 254 IP addresses (3 hosts up)
```

### 3 — nikto (웹 취약점 스캐너)

```bash
# nikto — 6700+ 알려진 web vuln + 1250 outdated server + 270 backdoor 점검
#   -h: 타겟 URL
#   -port: 포트 명시
#   -host: Host header (vhost 라우팅)
ssh 6v6-attacker 'nikto -h http://10.20.30.1 -port 80 -host juice.6v6.lab 2>&1 | head -30' || true
# 예상 출력:
#   + Server: HAProxy
#   + X-Frame-Options header is not set (clickjacking 가능)
#   + /admin found (potentially interesting)
# 단점: 시그니처 기반 → ModSec (W06) 의 403 차단으로 false-positive 다수
```

### 4 — dirb (디렉토리 brute force)

```bash
# dirb — wordlist 기반 path enumeration
#   common.txt (4000+ word) 가 기본 wordlist
#   각 path 에 GET 요청 → 200/302/401/403 응답이면 발견 출력
ssh 6v6-attacker 'dirb http://10.20.30.1/ -H "Host: juice.6v6.lab" 2>&1 | head -30' || true
# 예상 출력:
#   + http://10.20.30.1/admin (CODE:200)
#   + http://10.20.30.1/api (CODE:200)
#   ==> DIRECTORY: http://10.20.30.1/assets/
# 운영 측 detection: Suricata 의 ET SCAN dirb 룰 + Wazuh 5710 (Apache 404 burst)
```

### 5 — 결과 정리

```
# 발견 자산 표 작성
| host | port | service | version |
|------|------|---------|---------|
| 10.20.30.1 | 80 | http | HAProxy |
| 10.20.30.1 | 443 | https | HAProxy |
...
```

## 8. 과제

A. 정찰 보고서 (필수) — 6v6 환경의 모든 살아 있는 host + port + service 표
B. ATT&CK 매핑 (심화) — 각 도구의 ATT&CK Technique ID
C. 정찰 detection 측면 (정성) — Suricata / Wazuh 가 본 정찰을 어떻게 탐지하는가

## 9. W03 (웹 앱 구조) 예고

Burp Suite proxy + JuiceShop 의 요청·응답 흐름 분석.
