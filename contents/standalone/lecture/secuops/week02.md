# Week 02 — nftables 방화벽 (1) — 기초

> 본 주차는 **6v6-fw 컨테이너 단독** 으로 진행한다. fw 는 ext (10.20.30.0/24) ↔
> pipe (10.20.31.0/24) 사이의 라우터로 동작하며, nftables 가 모든 forward 트래픽을
> 통제한다. 학생은 fw 안에서 직접 nft 명령으로 ruleset 을 조회·수정하고, 이를 통해
> 학생 PC → bastion → 내부 컨테이너 의 진입 경로가 어떻게 보호되는지 학습한다.

## 학습 목표

본 주차 종료 시 학생은 다음을 수행할 수 있어야 한다.

1. nftables 의 4 핵심 개념 (table / chain / rule / set) 을 자기 말로 설명한다.
2. fw 의 ruleset 을 읽고 어떤 트래픽이 허용·차단되는지 결정한다.
3. `nft list ruleset` / `nft -j` (JSON) / `nft -c -f` (syntax check) 3 명령을
   상황에 맞게 구분 사용한다.
4. 새 룰 1개 추가 / 삭제 / counter 확인을 nft 명령으로 직접 수행한다.
5. 룰 변경이 도달성 (reachability) 에 미치는 영향을 tcpdump + curl 로 검증한다.
6. nftables 와 legacy iptables 의 관계를 설명하고 `iptables-translate` 로 마이그
   레이션 명령을 생성한다.

## 강의 시간 배분 (3시간 40분)

| 시간        | 내용                                                                   | 유형     |
|-------------|------------------------------------------------------------------------|----------|
| 0:00–0:25   | 이론 — Netfilter 후크 + nftables 가 iptables 후속이 된 이유             | 강의     |
| 0:25–0:55   | 이론 — table / chain / rule / set 4 개념 + family (ip / ip6 / inet)    | 강의     |
| 0:55–1:05   | 휴식                                                                    | —        |
| 1:05–1:30   | 6v6-fw 의 ruleset 분석 (실제 컨테이너 entrypoint 가 빌드한 룰)         | 강의/토론|
| 1:30–2:00   | 실습 1, 2 — ruleset 조회 + counter / JSON 변환                          | 실습     |
| 2:00–2:30   | 실습 3, 4 — 새 룰 추가 (특정 IP drop) + 삭제 + tcpdump 검증             | 실습     |
| 2:30–2:40   | 휴식                                                                    | —        |
| 2:40–3:10   | 실습 5 — iptables-translate 로 legacy 룰 마이그레이션                  | 실습     |
| 3:10–3:30   | 실습 6 — 영구화 (`/etc/nftables.conf`) vs entrypoint 컨테이너 차이      | 실습     |
| 3:30–3:40   | 정리 + 과제 안내 + W03 (DNAT/SNAT/HAProxy 협업) 예고                    | 정리     |

---

## 1. Netfilter 후크와 nftables 의 위치

### 1.1 패킷이 커널을 지나는 5 후크

리눅스 커널은 IP 패킷이 NIC 에 도착해서 빠져나갈 때까지 5 개의 hook (잡는 자리) 을
제공한다. 이는 1999년 Netfilter 프로젝트로 정의되었고, nftables / iptables 모두
같은 후크 위에 동작한다.

```
                  +------------+
NIC 진입 ───────▶ │ PREROUTING │ ──────────┐
                  +------------+           │
                                           ▼
                                  routing decision
                                           │
                                ┌──────────┴──────────┐
                                ▼                     ▼
                          +-------+            +-----------+
                          │ INPUT │            │ FORWARD   │
                          +-------+            +-----------+
                              │                     │
                              ▼                     │
                       local processes              │
                              │                     │
                              ▼                     ▼
                       +--------+              +------------+
                       │ OUTPUT │ ──────────▶ │ POSTROUTING │ ─▶ NIC 출발
                       +--------+              +------------+
```

각 hook 에서 nftables / iptables 룰이 평가되어 트래픽이 ACCEPT / DROP / REJECT /
NAT 변환된다. 어디서 잡느냐가 보안 정책의 핵심.

### 1.2 nftables 는 왜 iptables 를 대체했나?

| 항목 | iptables (legacy) | nftables (modern) |
|------|-------------------|--------------------|
| 도입 | 1998 (커널 2.4)   | 2014 (커널 3.13)   |
| backend | xt_tables 모듈     | nf_tables 모듈      |
| 명령 | iptables, ip6tables, ebtables, arptables 분리 | nft 단일 |
| family | ip 만, IPv6 는 ip6tables 별도 | ip / ip6 / inet (둘 다) / arp / bridge / netdev |
| set 자료 구조 | ipset 별도 | 내장 (`add set`) |
| 동시 atomic update | 불가 (룰별 update) | `nft -f file` 로 ruleset 통째 교체 |
| JSON 출력 | 비표준 | `nft -j` 표준 |
| 가독성 | `iptables -A INPUT -p tcp --dport 22 -j ACCEPT` | `add rule inet filter input tcp dport 22 accept` |
| 표준화 시점 | 2018: Debian 10, RHEL 8 부터 nftables 가 기본 backend |

요점: **2026년에 신규 룰을 쓴다면 nftables**. 그러나 legacy iptables 룰셋이 남아
있는 환경이 여전히 많으므로 두 도구의 변환·해석을 동시에 알아야 한다.

### 1.3 6v6-fw 컨테이너의 nftables 배치

```
                  학생 PC LAN (외부)
                        │
                        ▼  VM_IP:80
                  ┌──────────────────┐
                  │   Linux Host     │
                  │ (Docker daemon)  │
                  └────────┬─────────┘
                           │
                           ▼  docker NAT (iptables backend)
                  ┌────────────────┐
                  │   6v6-ext      │ bridge
                  │ 10.20.30.0/24  │
                  └────────┬───────┘
                           │
                           ▼  fw eth0 (10.20.30.1)
                  ╔════════════════╗
                  ║  6v6-fw        ║
                  ║                ║
                  ║  nftables      ║  ← 본 주차의 학습 대상
                  ║   • filter:    ║
                  ║      forward   ║
                  ║      input     ║
                  ║   • nat:       ║
                  ║      postrouting (masquerade)
                  ║                ║
                  ║  HAProxy       ║
                  ║                ║
                  ╚════════════════╝
                           │
                           ▼  fw eth1 (10.20.31.1)
                  ┌────────────────┐
                  │   6v6-pipe     │ bridge
                  │ 10.20.31.0/24  │
                  └────────────────┘
                           │
                           ▼  ips eth0 (10.20.31.2)
                  ╔════════════════╗
                  ║  6v6-ips       ║  (W04~05 대상)
                  ║  Suricata      ║
                  ╚════════════════╝
```

fw 안의 nftables 는 두 가지 일을 한다.
1. **filter** : forward chain 에서 어떤 src → dst 트래픽을 허용·차단할지 결정.
2. **nat (postrouting)** : 컨테이너 outbound 가 docker NAT 의 NAT 또는 자체
   masquerade 로 출발지 IP 를 변환.

학생이 본 주차에 다루는 것은 **filter** 가 메인.

---

## 2. nftables 4 핵심 개념

### 2.1 table

**한 family + 한 이름의 룰 컨테이너**. 6v6-fw 의 실제 table:

```
$ sudo nft list tables
table ip nat                # Docker daemon 자동 생성 (DNS 127.0.0.11 등)
table inet six_filter       # 6v6 의 정책 본체 (IPv4+IPv6 통합 family)
table ip six_nat            # 6v6 NAT stub — W03 에서 채워질 prerouting/postrouting
```

- `ip` family = IPv4 만. `ip6` = IPv6, `inet` = 둘 다 (IPv4+IPv6 합본).
- 6v6 는 `inet six_filter` + `ip six_nat` 두 table 을 학습 대상으로 사용.
- 식별자 이름은 letter / underscore 로 시작해야 한다. digit 시작 (예: `6v6_filter`) 은
  nft 파서가 syntax error 로 거부한다.

### 2.2 chain

**한 table 내부의 룰 묶음. 특정 hook 에 attach 되어 패킷 처리에 참여**.

```
$ sudo nft list table inet six_filter
table inet six_filter {
  chain forward {
    type filter hook forward priority 0; policy accept;
    ct state established,related accept
    ct state invalid drop
    ip saddr 10.20.30.0/24 ip daddr 10.20.31.0/24 accept
    ...
  }
  chain input {
    type filter hook input priority 0; policy accept;
    ...
  }
}
```

- `type filter` : 필터 (ACCEPT/DROP/REJECT) 용
- `hook forward` : 어느 Netfilter hook 에 붙는지 (forward / input / output / prerouting / postrouting)
- `priority 0` : 같은 hook 에 여러 chain 이 붙을 때 평가 순서 (낮은 priority 먼저)
- `policy accept` : 룰이 다 매치 안 되면 기본 accept (production 은 drop 권장)

### 2.3 rule

**chain 안의 한 줄. condition (왼쪽) + action (오른쪽).** 위에서 아래로 순차 평가.

```
ct state established,related accept       ← 조건: conntrack 상태가 established 또는 related → action: accept
ip saddr 10.20.30.202 drop                ← 조건: src IP = attacker → drop
tcp dport 22 accept                       ← 조건: dst port 22 (SSH) → accept
log prefix "FW-DENY: " drop               ← 조건: 위 어느 룰도 안 매치 → log + drop
```

자주 쓰는 condition:
- `ip saddr <IP>` / `ip daddr <IP>` / `ip protocol tcp`
- `tcp dport 80` / `tcp dport { 80, 443, 8080 }` (set)
- `ct state {established, related, new, invalid}`
- `iifname "eth0"` (입력 인터페이스) / `oifname "eth1"` (출력)
- `meta mark 0x100` (skb mark)

자주 쓰는 action:
- `accept` : 즉시 통과
- `drop` : 조용히 폐기 (응답 없음, 스캐너 탐지 어려움)
- `reject` : ICMP unreachable 또는 TCP RST 응답 (사용자 친화)
- `log prefix "TAG: "` : kernel log 에 기록 (`dmesg` 또는 journald)
- `counter` : 통계 누적 (byte/packet)
- `jump <chain>` : 사용자 정의 chain 으로 분기
- `nat: dnat to ...` / `snat to ...` / `masquerade` (W03)

### 2.4 set

**여러 값을 묶어 1개 이름으로 참조** (ipset 기능 내장). 예: blocklist 1000개 IP.

```
nft add set inet six_filter blocklist { type ipv4_addr \; }
nft add element inet six_filter blocklist { 1.2.3.4, 5.6.7.8, 9.10.11.12 }
nft add rule inet six_filter input ip saddr @blocklist drop
```

`@blocklist` 가 set 참조. set 에 추가/삭제는 ruleset 재컴파일 없이 O(1).

---

## 3. 6v6-fw 의 실제 ruleset 해부

6v6-fw 의 실제 ruleset 은 `/etc/nftables.conf` (이미지에 COPY 된 정적 파일) 가 정의
하며, entrypoint.sh 가 부팅 시 `nft -f /etc/nftables.conf` 로 atomic load 한다. 실제
파일 내용은 다음과 같이 **의도적으로 단순화** 되어 있다 — 학생이 룰을 추가하며 학습할 수
있도록 비워둔 운영 정책의 뼈대.

```
#!/usr/sbin/nft -f
# 6v6 fw — edge router firewall (ext <-> pipe).
# 'flush ruleset' 회피 — docker DNS 보존 위해 우리 테이블만 정의.

add table inet six_filter
flush table inet six_filter

table inet six_filter {
    chain input {
        type filter hook input priority 0; policy accept;
        tcp dport 22 accept                  # SSH 허용
        ip protocol icmp accept              # IPv4 ICMP
        ip6 nexthdr icmpv6 accept            # IPv6 ICMP
        ct state established,related accept  # 응답 path
    }

    chain forward {
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
        # ─── 학생이 룰을 insert/add 하며 학습하는 위치 ───
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# NAT 테이블 (학습 목적 — 6v6 의 ext↔pipe 는 direct routing 이므로 비어 있음)
add table ip six_nat
flush table ip six_nat
table ip six_nat {
    chain prerouting  { type nat hook prerouting  priority -100; }
    chain postrouting { type nat hook postrouting priority 100; }
}
```

**해석**:
- `inet` family 는 IPv4+IPv6 동시에 처리할 수 있는 nftables 의 통합 family.
- `flush table` 은 부팅마다 동일 table 을 비우고 새로 채우는 idempotent 패턴.
- `chain forward` 가 거의 비어 있어서 default `policy accept` 만으로 모든 forward 가
  허용된다. 이는 학습용 환경 — production 운영자는 `policy drop` + 화이트리스트가 정석.
- `6v6_nat` 의 두 chain 은 정의만 있고 룰 없음 — direct routing 이라 NAT 불필요. W03
  에서 학생이 직접 DNAT/SNAT 룰을 추가하며 배운다.

> 별도로 docker daemon 이 자체적으로 `table ip nat` (DOCKER chain 등) 을 생성한다. 이는
> 학생이 건드릴 영역이 아니며, `nft list ruleset` 출력에 `XT match tcp not found` 같은
> 경고가 나오는 것은 컨테이너에 xt_match 호환 모듈이 없어 docker 의 ipset 룰 일부가
> 디스플레이만 깨지는 현상이다. 정책 동작에는 영향 없음.

---

## 4. nft 명령 cheat sheet

| 목적 | 명령 |
|------|------|
| 전체 ruleset 출력 | `sudo nft list ruleset` |
| filter table 만 | `sudo nft list table inet six_filter` |
| 특정 chain 만 | `sudo nft list chain inet six_filter forward` |
| JSON 출력 | `sudo nft -j list ruleset \| jq .` |
| syntax 검증 | `sudo nft -c -f /etc/nftables.conf && echo OK` |
| 룰 추가 (위) | `sudo nft insert rule inet six_filter forward position 0 <condition> <action>` |
| 룰 추가 (아래) | `sudo nft add rule inet six_filter forward <condition> <action>` |
| 룰 삭제 | `sudo nft delete rule inet six_filter forward handle <N>` (`-a` 로 handle 확인) |
| handle 보기 | `sudo nft -a list table inet six_filter` |
| counter reset | `sudo nft reset counters table inet six_filter` |
| 룰셋 통째 교체 | `sudo nft -f /tmp/new-ruleset.nft` (atomic) |
| 룰셋 전체 flush | `sudo nft flush table inet six_filter` (6v6 정책만 비움, docker NAT 보존) |

---

## 5. iptables ↔ nftables 마이그레이션

레거시 iptables 룰을 nftables 로 옮겨야 할 때 유용한 3 도구.

### 5.1 iptables-translate

`iptables -A INPUT -p tcp --dport 22 -j ACCEPT` → 동등한 nft 명령으로 출력.

```
$ echo "iptables -A INPUT -p tcp --dport 22 -j ACCEPT" | iptables-translate
nft add rule inet six_filter INPUT tcp dport 22 counter accept
```

### 5.2 iptables-restore-translate

`iptables-save` 결과를 nftables 룰셋으로 변환.

```
$ sudo iptables-save > /tmp/legacy.rules
$ sudo iptables-restore-translate -f /tmp/legacy.rules > /tmp/new.nft
$ sudo nft -c -f /tmp/new.nft && echo "변환 OK"
```

### 5.3 iptables-nft (호환 모드)

Debian/Ubuntu/RHEL 의 `iptables` 명령은 이미 nftables backend 를 호환 모드로
사용한다. `iptables -L` 의 결과는 사실 nftables `table inet six_filter` 의 INPUT/FORWARD/
OUTPUT chain. 이는 마이그레이션 기간 동안 두 명령 모두 동작하게 하는 호환 레이어.

**확인 방법**:
```
$ readlink /etc/alternatives/iptables
/usr/sbin/iptables-nft        ← nftables backend
# 또는 /usr/sbin/iptables-legacy 면 legacy backend
```

---

## 6. 영구화: 컨테이너 vs systemd

### 6.1 시스템 호스트 (운영)

```
$ sudo nft list ruleset > /etc/nftables.conf
$ sudo systemctl enable nftables
$ sudo systemctl restart nftables
```

부팅 시 `nftables.service` 가 `/etc/nftables.conf` 를 atomic load.

### 6.2 컨테이너 (6v6)

도커 컨테이너는 stateless 라 부팅마다 `entrypoint.sh` 가 ruleset 을 재 구성한다.

```
# 6v6-fw entrypoint.sh 의 핵심
nft "add table ip six_nat" 2>/dev/null || true
nft "add chain ip six_nat postrouting { type nat hook postrouting priority 100 ; }"
nft "add rule ip six_nat postrouting oifname \"eth0\" ip saddr 10.20.31.0/24 masquerade"
# filter 룰도 동일하게
```

학생이 컨테이너 안에서 `nft add rule ...` 로 추가한 룰은 컨테이너 재시작 시 사라
진다. 영구화 하려면 `entrypoint.sh` 수정 + 컨테이너 재빌드 필요 (W03 에서 다룸).

---

## 7. 정책 설계 원칙 (Deny by default)

운영 환경에서는 다음 두 원칙을 동시에 적용.

1. **Default deny** : chain policy 를 `drop` 으로 설정한 뒤 필요한 트래픽만 명시
   허용.
2. **Specific before general** : 더 구체적인 룰을 위에. set 으로 큰 그룹을 한 줄로.

```
chain forward {
    type filter hook forward priority 0; policy drop;     ← default deny

    ct state established,related accept                   ← 가장 빈번 (early-exit)
    ct state invalid drop

    # 화이트리스트
    ip saddr 10.20.30.0/24 ip daddr 10.20.31.0/24 accept  # ext → pipe
    ip saddr 10.20.31.0/24 ip daddr 10.20.30.0/24 accept  # pipe → ext

    # log fallback (policy drop 직전 가시화)
    log prefix "FWD-DROP: " counter
}
```

6v6 의 실제 ruleset 은 시연 환경 단순화를 위해 `policy accept` 다. 학생이 본 주차의
과제로 `policy drop` 으로 강화하는 변형을 작성한다.

---

## 8. 용어 해설

| 용어 | 영문 | 설명 |
|------|------|------|
| **Netfilter** | Netfilter | Linux 커널의 packet filtering framework (1999~) |
| **nf_tables** | netfilter tables | nftables 의 커널 모듈 (2014~) |
| **xt_tables** | extension tables | iptables 의 커널 모듈 (legacy) |
| **conntrack** | connection tracking | 커널의 stateful inspection (established/related/new/invalid) |
| **policy** | chain policy | 어느 룰도 안 매치 시 기본 동작 (accept/drop) |
| **handle** | rule handle | nft 가 룰에 부여한 ID (삭제 시 사용) |
| **atomic ruleset** | — | 룰셋 전체를 한 번에 교체 (race 없음) |
| **conntrack zone** | — | 한 conntrack 테이블 안의 분리된 namespace (네트워크 격리 시) |
| **NAT** | Network Address Translation | 패킷 IP/port 변환 |
| **SNAT** | Source NAT | 출발지 IP 변환 (보통 outbound) |
| **DNAT** | Destination NAT | 목적지 IP 변환 (보통 inbound 포트 포워딩) |
| **MASQUERADE** | — | SNAT 의 특수 형태, outbound NIC IP 로 자동 변환 |
| **REJECT** | — | drop + ICMP unreachable / TCP RST 응답 |

---

## 9. 실습 시나리오 (실습 1~6)

### 실습 1 — fw ruleset 조회

```
ssh 6v6-fw 'sudo nft list ruleset'
ssh 6v6-fw 'sudo nft list table inet six_filter'
ssh 6v6-fw 'sudo nft -j list ruleset | jq ".nftables | length"'
```

검증: table 3개 (filter/nat/nat6v6) + forward chain + 핵심 룰 5+ 출력.

### 실습 2 — counter 확인 + reset

```
ssh 6v6-fw 'sudo nft list chain inet six_filter forward | grep -B1 counter'
ssh 6v6-fw 'sudo nft reset counters table inet six_filter'
ssh 6v6-fw 'sudo nft list chain inet six_filter forward | grep -B1 counter'   # 0 으로 reset 됨
```

### 실습 3 — 특정 IP drop 룰 추가 + 검증

학생 PC 또는 attacker 컨테이너가 web 에 접근 못 하게 한 줄 추가.

```
# 룰 추가
ssh 6v6-fw 'sudo nft insert rule inet six_filter forward position 0 ip saddr 10.20.30.202 counter drop'

# attacker → web 시도
ssh 6v6-attacker 'timeout 3 curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" http://10.20.30.1/'
# 결과: 000 (timeout)
# 또는 fw kernel log:
ssh 6v6-fw 'sudo dmesg | tail -5 | grep FW-FWD'

# 룰 삭제
ssh 6v6-fw 'sudo nft -a list chain inet six_filter forward | grep 10.20.30.202'
# handle 4 출력되면:
ssh 6v6-fw 'sudo nft delete rule inet six_filter forward handle 4'
```

### 실습 4 — tcpdump 로 drop 검증

```
# 두 터미널 동시
# T1
ssh 6v6-fw 'sudo timeout 10 tcpdump -ni eth1 host 10.20.30.202 -c 5'
# T2
ssh 6v6-attacker 'curl -H "Host: juice.6v6.lab" http://10.20.30.1/'
```

검증: 룰 추가 시 eth1 (pipe NIC) 에 패킷 안 보임 (fw 가 forward 단계에서 drop). 룰 삭제 후 다시 보임.

### 실습 5 — iptables-translate 마이그레이션

```
echo "iptables -A INPUT -s 10.20.30.0/24 -p tcp --dport 9100 -j ACCEPT" | iptables-translate
# 출력: nft add rule inet six_filter INPUT ip saddr 10.20.30.0/24 tcp dport 9100 counter accept
```

추가 케이스 3개를 본인이 만들어 변환해보고 의미 분석.

### 실습 6 — 영구화 비교

```
# 호스트 (강사 시연)
sudo nft list ruleset > /tmp/nftables.conf
sudo nft -c -f /tmp/nftables.conf && echo "valid"

# 컨테이너 (6v6-fw)
ssh 6v6-fw 'cat /entrypoint.sh | grep -E "^nft|^iptables" | head -10'
```

차이점 토론: production 운영 시 어느 쪽이 더 안전한가? (atomic update 가능성, 부팅 정책,
gitops audit, ...)

---

## 10. 과제

### A. 룰셋 작성 (필수)

본인이 운영자라 가정하고, 다음 정책을 만족하는 nftables ruleset 을 작성해 제출.

- ext (10.20.30.0/24) 의 학생 PC (10.20.30.202 = attacker) 에서 pipe (10.20.31.0/24)
  로 가는 트래픽 중 TCP 80/443 만 허용. 나머지는 log + drop.
- ext → pipe 가 ICMP ping 은 허용 (트러블슈팅).
- pipe → ext 의 반환 트래픽은 established/related 만 허용.

`nft list ruleset` 형식으로 제출. 6v6-fw 에 직접 적용하여 검증 출력 포함.

### B. 마이그레이션 (필수)

다음 legacy iptables 룰 3건을 nft 명령으로 변환해 제출 (`iptables-translate` 사용).

```
iptables -A INPUT -s 192.168.1.0/24 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
```

각 룰의 의미를 1줄씩 한글 주석.

### C. 정책 강화 시나리오 (심화)

6v6-fw 의 현재 `policy accept` 정책이 `policy drop` 으로 바뀌면 어떤 트래픽이 끊기는지
예측 + 검증 + 필요한 추가 허용 룰 작성. 1페이지 보고서.

---

## 11. 평가 기준

| 항목 | 비중 | 평가 방법 |
|------|------|----------|
| 룰셋 작성 (A) | 40% | 정책 정확도 + nft 명령 정확도 + 검증 출력 |
| 마이그레이션 (B) | 30% | 3 변환 결과 + 한글 해석 |
| 정책 강화 (C) | 30% | 영향 분석 + 추가 룰의 합리성 |

---

## 12. 다음 주차 (W03) 예고

- **주제**: nftables 방화벽 (2) — DNAT/SNAT/HAProxy 협업
- **실습 환경**: `6v6-fw` + `6v6-attacker` + `6v6-web`
- **핵심**: HAProxy 가 L7 라우팅을 담당해도, nftables 의 nat table 이 어떻게 보조 (외부
  포트 ↔ 내부 컨테이너 매핑) 하는지, masquerade 가 응답 path 에 어떤 영향을 미치는지.
- **선수 학습**: nftables wiki 의 NAT 섹션 통독.
