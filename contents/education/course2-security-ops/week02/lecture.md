# Week 02: nftables 방화벽 (1) — 기초

## 학습 목표
- nftables의 기본 구조(Table, Chain, Rule)를 이해한다
- inet filter 테이블과 INPUT/FORWARD/OUTPUT 체인의 역할을 구분한다
- 실습 서버에서 방화벽 룰을 조회, 추가, 삭제할 수 있다

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

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |

---

# Week 02: nftables 방화벽 (1) — 기초

## 학습 목표

- nftables의 기본 구조(Table, Chain, Rule)를 이해한다
- inet filter 테이블과 INPUT/FORWARD/OUTPUT 체인의 역할을 구분한다
- 실습 서버에서 방화벽 룰을 조회, 추가, 삭제할 수 있다

---

## 1. 방화벽이란?

방화벽(Firewall)은 네트워크 트래픽을 필터링하는 보안 장비(또는 소프트웨어)이다.
허용된 트래픽만 통과시키고, 나머지는 차단한다.

**리눅스 방화벽의 역사:**

| 도구 | 커널 버전 | 상태 |
|------|-----------|------|
| ipchains | 2.2 | 폐기 |
| iptables | 2.4~5.x | 레거시 (아직 많이 사용) |
| **nftables** | 3.13+ | **현재 표준** |

nftables는 iptables를 대체하는 리눅스 공식 패킷 필터링 프레임워크이다.

---

## 2. nftables 기본 구조

nftables는 3단계 계층 구조를 가진다:

```
Table (테이블)
  +-- Chain (체인)
       +-- Rule (룰)
```

### 2.1 Table (테이블)

테이블은 체인을 담는 컨테이너이다. **address family**를 지정한다:

| Family | 설명 |
|--------|------|
| `ip` | IPv4만 |
| `ip6` | IPv6만 |
| `inet` | IPv4 + IPv6 동시 처리 (**권장**) |
| `arp` | ARP |
| `bridge` | 브리지 |
| `netdev` | 네트워크 디바이스 레벨 |

### 2.2 Chain (체인)

체인은 룰을 담는 컨테이너이다. **base chain**은 hook point를 가진다:

| Hook | 설명 | 용도 |
|------|------|------|
| `input` | 이 서버로 들어오는 패킷 | 서비스 접근 제어 |
| `forward` | 이 서버를 경유하는 패킷 | 라우터/게이트웨이 |
| `output` | 이 서버에서 나가는 패킷 | 아웃바운드 제어 |

### 2.3 Rule (룰)

룰은 조건(match)과 동작(verdict)으로 구성된다:

| Verdict | 설명 |
|---------|------|
| `accept` | 허용 |
| `drop` | 조용히 차단 |
| `reject` | 거부 메시지와 함께 차단 |
| `log` | 로그 기록 |
| `counter` | 카운터 증가 |

---

## 3. 실습 환경 접속

> **이 실습을 왜 하는가?**
> nftables는 Linux의 **기본 방화벽**이다. 모든 Linux 서버 관리자와 보안 엔지니어가 반드시 알아야 한다.
> 방화벽은 네트워크 보안의 **첫 번째 방어선**으로, 잘못된 설정 하나가 전체 네트워크를 노출시킬 수 있다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 현재 서버에 어떤 방화벽 규칙이 적용되어 있는지
> - 어떤 포트가 열려 있고, 어떤 트래픽이 차단되는지
> - 새로운 규칙을 추가/수정하는 방법
>
> **실무 활용:**
> - 서버 셋업 시 기본 방화벽 구성 (SSH만 허용, 나머지 DROP)
> - 보안 감사에서 "불필요한 포트가 열려 있지 않은가?" 점검
> - 인시던트 대응 시 공격자 IP를 긴급 차단
>
> **주의:**
> - 방화벽 실습 시 SSH(22) 포트를 차단하면 **접속이 끊길 수 있다**
> - 반드시 SSH를 먼저 허용한 후 다른 룰을 설정한다
> - 실습용 테이블(`lab_filter`)을 사용하고, 기존 `filter` 테이블은 수정하지 않는다
>
> **검증 완료:** secu 서버에 `inet filter`, `ip nat` 2개 테이블이 존재함

실습 서버 `secu` (방화벽/IPS 서버)에 접속한다:

> **실습 목적**: nftables 방화벽이 설치된 secu 서버에 접속하여, 실제 운영 중인 방화벽 환경을 직접 다루는 첫 단계이다.
>
> **배우는 것**: 방화벽 서버에 SSH로 접속하고, nftables 버전과 현재 룰셋 구조를 확인하는 방법을 익힌다.
>
> **결과 해석**: `nft --version`에서 v1.0.x가 출력되면 nftables가 정상 설치된 것이다. 접속 실패 시 SSH 포트(22)가 차단되었을 수 있다.
>
> **실전 활용**: 보안 사고 발생 시 방화벽 서버에 즉시 접속하여 공격 IP를 차단하는 것이 초동 대응의 핵심이다.

```bash
# 실습 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
```

접속 후 nftables 버전을 확인한다:

```bash
echo 1 | sudo -S nft --version
```

**예상 출력:**
```
nftables v1.0.6 (Lester Gooch)
```

---

## 4. 현재 룰셋 조회

> **이 실습의 목적:**
> 방화벽을 설정하기 전에 **현재 어떤 규칙이 적용되어 있는지** 반드시 확인해야 한다.
> 기존 규칙을 모르고 새 규칙을 추가하면 충돌이 발생하거나 SSH가 차단될 수 있다.
> `nft list ruleset`은 **방화벽 관리의 첫 번째 명령**이다.
>
> **결과 읽는 법:**
> - `table inet filter`: IPv4+IPv6 통합 필터 테이블
> - `chain input`: 서버로 **들어오는** 트래픽 규칙
> - `chain forward`: 서버를 **경유하는** 트래픽 규칙 (NAT/라우팅)
> - `chain output`: 서버에서 **나가는** 트래픽 규칙
> - `policy accept/drop`: 규칙에 매칭되지 않는 트래픽의 기본 처리

### 4.1 전체 룰셋 보기

```bash
# 현재 적용된 모든 방화벽 규칙 확인 (검증 완료: inet filter + ip nat 테이블 존재)
echo 1 | sudo -S nft list ruleset
```

**예상 출력 (예시):**
```
table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
        ct state established,related accept
        iif "lo" accept
        tcp dport 22 accept
    }
    chain forward {
        type filter hook forward priority 0; policy accept;
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### 4.2 특정 테이블만 보기

```bash
echo 1 | sudo -S nft list table inet filter
```

### 4.3 특정 체인만 보기

```bash
echo 1 | sudo -S nft list chain inet filter input
```

---

## 5. 테이블 생성과 삭제

> **왜 실습용 테이블을 별도로 만드는가?**
> 기존 `inet filter` 테이블은 **운영 중인 방화벽**이다.
> 여기서 실수하면 SSH가 차단되어 서버에 접속할 수 없게 된다.
> 따라서 `lab_filter`라는 **별도 테이블**에서 연습하고, 끝나면 삭제한다.
> 이것은 실무에서도 동일하다 — 운영 규칙을 수정하기 전에 테스트 환경에서 먼저 검증한다.

### 5.1 테이블 생성

```bash
# inet family 테이블 생성 (실습용 — 운영 filter 테이블은 건드리지 않음)
echo 1 | sudo -S nft add table inet lab_filter
```

### 5.2 테이블 확인

```bash
echo 1 | sudo -S nft list tables
```

**예상 출력:**
```
table inet filter
table inet lab_filter
```

### 5.3 테이블 삭제

```bash
echo 1 | sudo -S nft delete table inet lab_filter
```

---

## 6. 체인 생성

> **체인의 역할과 hook 포인트:**
> 체인은 **패킷이 처리되는 시점(hook)**을 결정한다:
> - `input`: 이 서버로 **들어오는** 패킷 (SSH 접속, HTTP 요청 등)
> - `output`: 이 서버에서 **나가는** 패킷 (DNS 조회, 외부 다운로드 등)
> - `forward`: 이 서버를 **경유하는** 패킷 (NAT 게이트웨이 역할 시)
>
> `priority`는 같은 hook에 여러 체인이 있을 때의 실행 순서이다 (낮을수록 먼저).
> `policy`는 어떤 규칙에도 매칭되지 않은 패킷의 기본 처리 방법이다:
> - `accept`: 통과 (기본값, 허용적)
> - `drop`: 차단 (보안적, **화이트리스트 방식**)

base chain을 만들 때는 `type`, `hook`, `priority`, `policy`를 지정한다:

```bash
# 먼저 테이블 생성
echo 1 | sudo -S nft add table inet lab_filter

# input 체인: 서버로 들어오는 트래픽 제어
echo 1 | sudo -S nft add chain inet lab_filter input \
  '{ type filter hook input priority 0; policy accept; }'

# output 체인 생성
echo 1 | sudo -S nft add chain inet lab_filter output \
  '{ type filter hook output priority 0; policy accept; }'

# forward 체인 생성
echo 1 | sudo -S nft add chain inet lab_filter forward \
  '{ type filter hook forward priority 0; policy accept; }'
```

**확인:**
```bash
echo 1 | sudo -S nft list table inet lab_filter
```

**예상 출력:**
```
table inet lab_filter {
    chain input {
        type filter hook input priority filter; policy accept;
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
    chain forward {
        type filter hook forward priority filter; policy accept;
    }
}
```

---

## 7. 룰 추가

> **룰 추가의 핵심 원칙:**
> 방화벽 룰은 **위에서 아래로 순서대로** 평가된다 (first-match).
> 먼저 매칭되는 룰이 적용되므로, **허용 룰을 차단 룰보다 위에** 배치해야 한다.
> 예: SSH 허용 → HTTP 허용 → 나머지 전부 DROP

### 7.1 기본 문법

```
nft add rule <family> <table> <chain> <match> <verdict>
# 예: inet 패밀리, lab_filter 테이블, input 체인에
#     TCP 22번 포트로 오는 트래픽을 accept(허용)
```

### 7.2 SSH 허용 룰

> **왜 SSH를 가장 먼저 허용하는가?**
> policy를 drop으로 변경하기 전에 SSH를 허용하지 않으면,
> **자신의 SSH 연결이 즉시 끊긴다.** 이것이 방화벽 설정에서 가장 흔한 실수이다.
> 반드시 SSH(22) → 기타 서비스 → default drop 순서를 지킨다.

```bash
# SSH 허용 (가장 먼저!)
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 22 accept
```

### 7.3 ICMP(ping) 허용 룰

> **왜 ping을 허용하는가?**
> 네트워크 트러블슈팅에서 `ping`은 가장 기본적인 진단 도구이다.
> ping이 차단되면 "서버가 죽었는지 네트워크가 막힌 건지" 구분이 어려워진다.
> 보안상 ping을 차단하는 곳도 있지만, 실습 환경에서는 허용하는 것이 편리하다.

```bash
# ICMP echo-request(ping) 허용
echo 1 | sudo -S nft add rule inet lab_filter input icmp type echo-request accept
```

### 7.4 특정 IP에서 오는 트래픽 차단

> **이 룰의 용도:**
> 공격이 감지된 IP를 긴급 차단할 때 사용한다.
> 인시던트 대응에서 "격리(Containment)" 단계의 핵심 조치이다.

```bash
# 10.20.30.80(web 서버)에서 오는 트래픽 차단
echo 1 | sudo -S nft add rule inet lab_filter input ip saddr 10.20.30.80 drop
```

### 7.5 포트 범위 허용

> **포트 범위가 필요한 경우:**
> 동적 포트(ephemeral port) 또는 여러 서비스를 한 번에 허용할 때 사용.
> 예: 8000~8100 범위에 여러 마이크로서비스가 동작하는 경우.

```bash
# 8000~8100 포트 범위 허용
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 8000-8100 accept
```

### 7.6 룰 확인 (핸들 번호 포함)

```bash
echo 1 | sudo -S nft -a list chain inet lab_filter input
```

**예상 출력:**
```
table inet lab_filter {
    chain input {
        type filter hook input priority filter; policy accept;
        tcp dport 22 accept # handle 4
        icmp type echo-request accept # handle 5
        ip saddr 10.20.30.80 drop # handle 6
        tcp dport 8000-8100 accept # handle 7
    }
}
```

> **핵심**: `-a` 옵션으로 handle 번호를 확인한다. 삭제 시 필요하다.

---

## 8. 룰 삭제

handle 번호를 사용하여 특정 룰을 삭제한다:

```bash
# handle 6번 룰 삭제 (10.20.30.80 차단 룰)
echo 1 | sudo -S nft delete rule inet lab_filter input handle 6
```

**삭제 확인:**
```bash
echo 1 | sudo -S nft -a list chain inet lab_filter input
```

---

## 9. Connection Tracking (conntrack)

conntrack은 이미 수립된 연결의 패킷을 자동으로 허용하는 기능이다.
방화벽 룰 작성 시 가장 먼저 추가해야 한다:

```bash
# 이미 수립된/관련된 연결 허용
echo 1 | sudo -S nft add rule inet lab_filter input ct state established,related accept

# 잘못된(invalid) 패킷 차단
echo 1 | sudo -S nft add rule inet lab_filter input ct state invalid drop
```

**ct state 종류:**

| State | 설명 |
|-------|------|
| `new` | 새 연결의 첫 패킷 |
| `established` | 수립된 연결의 패킷 |
| `related` | 기존 연결과 관련된 새 연결 (예: FTP data) |
| `invalid` | 추적 불가능한 패킷 |

---

## 10. 실습 과제

### 과제 1: 기본 방화벽 구성

아래 조건을 만족하는 방화벽을 `inet lab_filter` 테이블에 구성하라:

1. 이미 수립된 연결은 허용 (`ct state established,related`)
2. 루프백 인터페이스(lo) 허용
3. SSH(22번 포트) 허용
4. ICMP ping 허용
5. HTTP(80번), HTTPS(443번) 허용
6. 나머지 전부 차단(drop)하려면 → policy를 drop으로 변경하지 말고, 마지막에 drop 룰 추가

```bash
# 1. conntrack
echo 1 | sudo -S nft add rule inet lab_filter input ct state established,related accept
echo 1 | sudo -S nft add rule inet lab_filter input ct state invalid drop

# 2. 루프백
echo 1 | sudo -S nft add rule inet lab_filter input iif lo accept

# 3. SSH
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 22 accept

# 4. ICMP
echo 1 | sudo -S nft add rule inet lab_filter input icmp type echo-request accept

# 5. HTTP/HTTPS
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport { 80, 443 } accept

# 6. 나머지 차단
echo 1 | sudo -S nft add rule inet lab_filter input drop
```

### 과제 2: 테스트

web 서버에서 secu 서버로 접근 테스트:

```bash
# web 서버에 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# ping 테스트 (허용되어야 함)
ping -c 2 10.20.30.1

# SSH 테스트 (허용되어야 함)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 hostname

# 차단된 포트 테스트 (연결 안 됨)
nc -zv 10.20.30.1 8888
```

### 과제 3: 정리

실습이 끝나면 테이블을 삭제한다:

```bash
echo 1 | sudo -S nft delete table inet lab_filter
```

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| Table | 체인을 담는 컨테이너 (inet family 권장) |
| Chain | 룰을 담는 컨테이너 (hook point: input/forward/output) |
| Rule | 조건 + 동작 (accept/drop/reject) |
| conntrack | 수립된 연결 자동 허용 |
| handle | 룰의 고유 번호 (삭제 시 필요) |
| `nft list ruleset` | 전체 룰 조회 |
| `nft -a list` | handle 번호 포함 조회 |
| `nft add rule` | 룰 추가 (체인 끝에) |
| `nft delete rule` | handle로 룰 삭제 |

---

## 다음 주 예고

Week 03에서는 nftables의 실전 기능을 다룬다:
- NAT (Network Address Translation)
- 포트 포워딩
- 화이트리스트 정책
- 로깅
- 룰셋 저장/복원

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** nftables에서 policy drop의 의미는?
- (a) 모든 트래픽 허용  (b) **명시적으로 허용하지 않은 모든 트래픽 차단**  (c) 로그만 기록  (d) 특정 IP만 차단

**Q2.** Suricata가 nftables와 다른 핵심 차이는?
- (a) IP만 검사  (b) **패킷 페이로드(내용)까지 검사**  (c) 포트만 검사  (d) MAC 주소만 검사

**Q3.** Wazuh에서 level 12 경보의 의미는?
- (a) 정보성 이벤트  (b) **높은 심각도 — 즉시 분석 필요**  (c) 정상 활동  (d) 시스템 시작

**Q4.** ModSecurity CRS의 Anomaly Scoring이란?
- (a) 모든 요청 차단  (b) **규칙 매칭 점수를 누적하여 임계값 초과 시 차단**  (c) IP 기반 차단  (d) 시간 기반 차단

**Q5.** 보안 솔루션 배치 순서(외부→내부)는?
- (a) WAF → 방화벽 → IPS  (b) **방화벽 → IPS → WAF → 애플리케이션**  (c) IPS → WAF → 방화벽  (d) 애플리케이션 → WAF

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
