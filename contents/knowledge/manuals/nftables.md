# nftables 방화벽 레퍼런스

## 개요

nftables는 Linux 커널의 패킷 필터링 프레임워크로, iptables를 대체한다. 단일 도구(`nft`)로 IPv4, IPv6, ARP, 브리지 필터링을 모두 처리한다.

---

## 1. 기본 구조

nftables는 **테이블 → 체인 → 룰** 계층 구조를 갖는다.

```
table (주소 패밀리)
 └── chain (훅 포인트, 우선순위)
      └── rule (매칭 조건 + 액션)
```

### 주소 패밀리 (Address Family)

| 패밀리   | 설명                |
|----------|---------------------|
| `ip`     | IPv4 전용           |
| `ip6`    | IPv6 전용           |
| `inet`   | IPv4 + IPv6 통합    |
| `arp`    | ARP                 |
| `bridge` | 브리지 프레임       |
| `netdev` | 인그레스 단계       |

---

## 2. 테이블 관리

```bash
# 테이블 생성
nft add table inet filter

# 테이블 목록 조회
nft list tables

# 특정 테이블 상세 조회
nft list table inet filter

# 테이블 삭제
nft delete table inet filter

# 테이블 내 모든 룰 삭제 (테이블/체인 구조 유지)
nft flush table inet filter
```

---

## 3. 체인 (Chain)

### 베이스 체인 유형

| 유형       | 훅 포인트   | 설명                          |
|------------|-------------|-------------------------------|
| `filter`   | input       | 로컬 호스트로 들어오는 패킷   |
| `filter`   | output      | 로컬 호스트에서 나가는 패킷   |
| `filter`   | forward     | 라우팅되어 통과하는 패킷      |
| `nat`      | prerouting  | DNAT (포트 포워딩)            |
| `nat`      | postrouting | SNAT / 마스커레이드           |

### 체인 생성

```bash
# input 필터 체인 (우선순위 0, 기본 정책 drop)
nft add chain inet filter input \
  '{ type filter hook input priority 0; policy drop; }'

# output 필터 체인
nft add chain inet filter output \
  '{ type filter hook output priority 0; policy accept; }'

# forward 체인
nft add chain inet filter forward \
  '{ type filter hook forward priority 0; policy drop; }'

# NAT 체인
nft add chain ip nat prerouting \
  '{ type nat hook prerouting priority -100; }'
nft add chain ip nat postrouting \
  '{ type nat hook postrouting priority 100; }'
```

### 일반 체인 (비베이스)

```bash
# 훅 없는 일반 체인 — jump/goto 대상으로 사용
nft add chain inet filter tcp_chain
```

---

## 4. 매칭 조건 (Match Expressions)

### IP 관련

```bash
ip saddr 10.20.30.0/24       # 출발지 IP/서브넷
ip daddr 10.20.30.10         # 목적지 IP
ip protocol tcp               # 프로토콜
```

### 포트 관련

```bash
tcp dport 22                  # TCP 목적지 포트
tcp dport { 80, 443 }        # 다중 포트 (세트)
tcp dport 1024-65535          # 포트 범위
udp sport 53                  # UDP 출발지 포트
tcp sport != 80               # 부정 매칭
```

### 인터페이스

```bash
iifname "eth0"                # 수신 인터페이스
oifname "eth1"                # 송신 인터페이스
```

### 연결 추적 (Connection Tracking)

```bash
ct state established,related  # 기존 연결 허용
ct state new                  # 새 연결
ct state invalid              # 유효하지 않은 패킷
```

### 기타

```bash
meta l4proto icmp             # ICMP 프로토콜
icmp type echo-request        # ping 요청
limit rate 10/second          # 속도 제한
```

---

## 5. 액션 (Verdicts)

| 액션           | 설명                                    |
|----------------|-----------------------------------------|
| `accept`       | 패킷 허용                               |
| `drop`         | 패킷 조용히 폐기                        |
| `reject`       | 패킷 거부 (ICMP 에러 반환)              |
| `log`          | 커널 로그에 기록                         |
| `counter`      | 패킷/바이트 카운터                       |
| `jump <chain>` | 다른 체인으로 이동 (복귀 가능)           |
| `goto <chain>` | 다른 체인으로 이동 (복귀 없음)           |
| `masquerade`   | 출발지 IP를 나가는 인터페이스 IP로 변환  |
| `dnat to`      | 목적지 NAT                              |
| `snat to`      | 출발지 NAT                              |

### log 옵션

```bash
log prefix "[NFT-DROP] " level warn  # 로그 접두어와 레벨 지정
log flags all                        # 모든 메타데이터 포함
```

---

## 6. 룰 관리

```bash
# 룰 추가 (체인 끝에)
nft add rule inet filter input tcp dport 22 accept

# 룰 삽입 (체인 앞에)
nft insert rule inet filter input tcp dport 443 accept

# 특정 위치에 삽입 (핸들 번호 기준)
nft list table inet filter -a         # 핸들 번호 확인
nft add rule inet filter input position 5 tcp dport 8080 accept

# 룰 삭제 (핸들 번호로)
nft delete rule inet filter input handle 7

# 체인 내 모든 룰 삭제
nft flush chain inet filter input
```

---

## 7. 세트 (Sets)와 맵 (Maps)

```bash
# 명명된 세트 생성
nft add set inet filter blocked_ips '{ type ipv4_addr; }'
nft add element inet filter blocked_ips '{ 10.20.30.50, 10.20.30.51 }'

# 세트를 룰에서 참조
nft add rule inet filter input ip saddr @blocked_ips drop

# 타임아웃이 있는 세트 (자동 만료)
nft add set inet filter rate_limit \
  '{ type ipv4_addr; flags timeout; timeout 60s; }'

# 맵 (verdict map)
nft add map inet filter port_policy \
  '{ type inet_service : verdict; }'
nft add element inet filter port_policy \
  '{ 22 : accept, 80 : accept, 443 : accept }'
nft add rule inet filter input tcp dport vmap @port_policy
```

---

## 8. 룰셋 저장 및 복원

```bash
# 현재 전체 룰셋 저장
nft list ruleset > /etc/nftables.conf

# 룰셋 복원
nft -f /etc/nftables.conf

# 시스템 시작 시 자동 로드
systemctl enable nftables
```

---

## 9. 실습 예제

### 예제 1: CCC 기본 방화벽 설정

```bash
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;

    # 루프백 허용
    iifname "lo" accept

    # 기존 연결 허용
    ct state established,related accept

    # 유효하지 않은 패킷 차단
    ct state invalid drop

    # ICMP 허용 (ping)
    meta l4proto icmp accept

    # SSH (관리용, 10.20.30.0/24 내부만)
    ip saddr 10.20.30.0/24 tcp dport 22 accept

    # HTTP/HTTPS
    tcp dport { 80, 443 } accept

    # 나머지 로그 후 드롭
    log prefix "[NFT-INPUT-DROP] " counter drop
  }

  chain forward {
    type filter hook forward priority 0; policy drop;
    ct state established,related accept
    ct state invalid drop
  }

  chain output {
    type filter hook output priority 0; policy accept;
  }
}
```

### 예제 2: NAT (마스커레이드)

```bash
table ip nat {
  chain postrouting {
    type nat hook postrouting priority 100;

    # 내부 → 외부 마스커레이드
    ip saddr 10.20.30.0/24 oifname "eth0" masquerade
  }
}
```

### 예제 3: 포트 포워딩 (DNAT)

```bash
table ip nat {
  chain prerouting {
    type nat hook prerouting priority -100;

    # 외부 8080 → 내부 웹서버 10.20.30.10:80
    tcp dport 8080 dnat to 10.20.30.10:80
  }

  chain postrouting {
    type nat hook postrouting priority 100;
    ip daddr 10.20.30.10 tcp dport 80 masquerade
  }
}

# forward 체인에서 허용 필요
nft add rule inet filter forward ip daddr 10.20.30.10 tcp dport 80 accept
```

### 예제 4: 속도 제한 (Rate Limiting)

```bash
# SSH 브루트포스 방지 — 분당 5회 초과 시 드롭
nft add rule inet filter input \
  tcp dport 22 ct state new \
  limit rate 5/minute accept

nft add rule inet filter input \
  tcp dport 22 ct state new \
  log prefix "[SSH-BRUTE] " drop
```

---

## 10. 디버깅

```bash
# 전체 룰셋 확인 (핸들 포함)
nft -a list ruleset

# 카운터 확인
nft list chain inet filter input

# 실시간 트레이스
nft add rule inet filter input meta nftrace set 1
nft monitor trace

# iptables 호환 명령으로 확인
iptables-nft -L -v -n
```

---

## 참고

- 공식 위키: https://wiki.nftables.org
- nft 매뉴얼: `man nft`
- iptables → nftables 변환: `iptables-translate`
