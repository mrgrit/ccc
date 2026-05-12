# Week 02 — nftables 방화벽 (1) — 기초 + table/chain/rule/set

> **본 주차의 한 줄 요약**
>
> 6v6-fw 컨테이너의 **nftables** (리눅스 커널 표준 패킷 필터링 프레임워크) 를 깊이
> 해부한다. 4 핵심 개념 (table / chain / rule / set) + 5 hook (input/output/forward/
> prerouting/postrouting) + counter 분석 + 동적 룰 추가/삭제 + Red/Blue/Purple 시나리오
> (Red 가 fw:80 무차별 스캔 → Blue 가 src IP drop 룰 추가 → Purple 가 효과 측정).

---

## 학습 목표

1. nftables 의 4 핵심 개념 (table / chain / rule / set) 을 비유 없이 1분 안에 설명한다.
2. Netfilter 의 5 hook (prerouting / input / forward / output / postrouting) 의 통과
   순서를 화이트보드에 그린다.
3. 6v6-fw 의 실제 ruleset (`inet six_filter` + `ip six_nat`) 을 읽고 어떤 트래픽이
   허용·차단되는지 결정한다.
4. `nft list ruleset` / `nft -j` (JSON) / `nft -c -f` (syntax check) / `nft monitor`
   네 핵심 명령을 상황에 맞게 사용한다.
5. 임시 drop 룰 1개 추가 / counter 증가 검증 / `nft delete rule ... handle N` 으로
   삭제까지 한 cycle 수행한다.
6. iptables ↔ nftables 의 관계를 설명하고 `iptables-translate` 로 마이그레이션 명령을
   생성한다.
7. **Red/Blue/Purple 시나리오 — Red 가 fw:80 으로 무차별 스캔 → Blue 가 input chain
   에 drop 룰 추가 → Purple 가 효과 측정 후 ruleset 영구화 검토.**

---

## 강의 시간 배분 (총 3시간 40분)

| 시간      | 내용                                                                  | 유형     |
|-----------|---------------------------------------------------------------------|----------|
| 0:00–0:25 | 이론 — Netfilter 5 hook + nftables 가 iptables 후속이 된 이유          | 강의     |
| 0:25–0:55 | 이론 — table / chain / rule / set 4 개념 + family (ip / ip6 / inet)   | 강의     |
| 0:55–1:05 | 휴식                                                                  | —        |
| 1:05–1:30 | 6v6-fw 의 실제 ruleset 해부 (nftables.conf + entrypoint)              | 강의/토론 |
| 1:30–2:00 | 실습 1, 2 — ruleset 가시화 + counter / JSON 변환                       | 실습     |
| 2:00–2:30 | 실습 3, 4 — 동적 drop 룰 추가 + tcpdump 검증                          | 실습     |
| 2:30–2:40 | 휴식                                                                  | —        |
| 2:40–3:10 | 실습 5 — iptables-translate 마이그레이션 + nft monitor trace          | 실습     |
| 3:10–3:30 | 실습 6 — **R/B/P** (nmap → drop 룰 → 영구화 검토)                      | 실습     |
| 3:30–3:40 | 정리 + 과제 안내 + W03 (DNAT/SNAT/HAProxy 협업) 예고                  | 정리     |

---

## 0. 용어 해설

| 용어 | 영문 | 뜻 |
|------|------|----|
| **Netfilter** | Netfilter | Linux 커널의 packet filtering framework (1999~) |
| **nf_tables** | netfilter tables | nftables 의 커널 모듈 (2014~) |
| **xt_tables** | extension tables | iptables 의 커널 모듈 (legacy) |
| **hook** | — | 커널 packet 처리의 5 위치 (prerouting/input/forward/output/postrouting) |
| **table** | nftables table | 한 family + 한 이름의 룰 컨테이너 |
| **chain** | nftables chain | 한 table 내부의 룰 묶음, hook 에 attach |
| **rule** | nftables rule | condition (왼쪽) + action (오른쪽), 위에서 아래로 순차 평가 |
| **set** | nftables set | 여러 값을 1개 이름으로 참조 (ipset 내장) |
| **policy** | chain policy | 어느 룰도 매치 안 됐을 때 기본 동작 (accept/drop) |
| **handle** | rule handle | nft 가 룰에 부여한 고유 ID (삭제 시 사용) |
| **family** | — | 패킷의 layer 분류 (`ip` IPv4 / `ip6` IPv6 / `inet` 둘 다 / `arp` / `bridge` / `netdev`) |
| **counter** | — | 룰 단위 byte/packet 통계 |
| **conntrack** | connection tracking | 커널의 stateful inspection |
| **ct state** | — | conntrack 상태 (established / related / new / invalid / untracked) |
| **NAT** | Network Address Translation | 패킷 IP/port 변환 (W03 심화) |
| **REJECT** | — | drop + ICMP unreachable 응답 |
| **DROP** | — | 조용히 폐기 (응답 없음) |
| **iptables-nft** | — | iptables 명령을 nftables backend 로 호환 실행 |
| **atomic update** | — | 룰셋 전체를 한 번에 교체 (race 없음) |

---

## 1. Netfilter 5 hook — 모든 트래픽이 거치는 5 자리

리눅스 커널은 IP 패킷이 NIC 에 도착해서 빠져나갈 때까지 5 개 hook (잡는 자리) 을 제공한다.
이것이 1999년 Netfilter 프로젝트의 정의이며, nftables / iptables 모두 같은 hook 위에 동작한다.

```mermaid
graph LR
    NIC1[NIC 진입]
    NIC2[NIC 출발]
    PRE[prerouting<br/>nat -100<br/>filter -150]
    ROUTE{routing<br/>decision}
    IN[INPUT]
    FWD[FORWARD]
    LOCAL[local processes]
    OUT[OUTPUT]
    POST[postrouting<br/>nat 100]
    NIC1 --> PRE
    PRE --> ROUTE
    ROUTE -->|local 목적지| IN
    ROUTE -->|forward 목적지| FWD
    IN --> LOCAL
    LOCAL --> OUT
    OUT --> POST
    FWD --> POST
    POST --> NIC2
    style PRE fill:#1f6feb,color:#fff
    style ROUTE fill:#d29922,color:#fff
    style FWD fill:#3fb950,color:#fff
    style POST fill:#bc8cff,color:#fff
```

각 hook 에서 nftables / iptables 룰이 평가되어 트래픽이 ACCEPT / DROP / REJECT / NAT
변환된다. **어디서 잡느냐가 보안 정책의 핵심**.

| hook | 언제 평가 | 어떤 트래픽 | 활용 |
|------|----------|------------|------|
| `prerouting` | NIC 진입 후 라우팅 전 | 모든 inbound | DNAT (W03) |
| `input` | 라우팅 후 local 목적지로 | fw 자체로 들어오는 | SSH/HTTP 허용·차단 |
| `forward` | 라우팅 후 다른 host 로 | fw 를 통과하는 | ext↔pipe 통제 |
| `output` | local 에서 나가는 | fw 가 생성한 패킷 | outbound 통제 |
| `postrouting` | NIC 출발 직전 | 모든 outbound | SNAT/MASQUERADE (W03) |

---

## 2. nftables 가 iptables 를 대체한 이유

| 항목 | iptables (legacy) | nftables (modern) |
|------|-------------------|--------------------|
| 도입 | 1998 (커널 2.4) | 2014 (커널 3.13) |
| backend | xt_tables 모듈 | nf_tables 모듈 |
| 명령 | iptables / ip6tables / ebtables / arptables 분리 | `nft` 단일 |
| family | ip 만 (IPv6 는 ip6tables) | ip / ip6 / inet (둘 다) / arp / bridge / netdev |
| set 자료 구조 | ipset 별도 | 내장 (`add set`) |
| 동시 atomic update | 불가 (룰별 update) | `nft -f file` 로 ruleset 통째 교체 |
| JSON 출력 | 비표준 | `nft -j` 표준 |
| 가독성 | `iptables -A INPUT -p tcp --dport 22 -j ACCEPT` | `add rule inet filter input tcp dport 22 accept` |
| 표준화 시점 | 2018 (Debian 10 / RHEL 8 부터 nftables 가 기본 backend) | |

**요점**: 2026 년 현재 신규 룰은 nftables. 그러나 legacy iptables 룰셋이 남은 환경이
많아 두 도구의 변환·해석을 동시에 알아야 한다.

---

## 3. nftables 4 핵심 개념

### 3.1 table — 한 family + 한 이름의 룰 컨테이너

6v6-fw 의 실제 table (실측 2026-05-11):

```bash
$ docker exec 6v6-fw nft list tables
table ip nat                # Docker daemon 이 자동 생성 (DNS 127.0.0.11)
table inet six_filter        # 6v6 의 정책 본체 (IPv4+IPv6 통합 family)
table ip six_nat             # 6v6 NAT stub (W03 에서 채워짐)
```

- `ip` family = IPv4 만
- `ip6` family = IPv6 만
- `inet` family = 둘 다 (IPv4+IPv6 통합)
- `arp`, `bridge`, `netdev` = 특수 (L2 또는 ingress)

> 식별자는 letter 또는 underscore 로 시작해야 한다. digit 시작 (예: `6v6_filter`) 은
> nft 파서가 syntax error 로 거부 — 6v6 가 처음 `6v6_filter` 로 했다가 silent fail
> 후 `six_filter` 로 변경한 이력.

### 3.2 chain — table 내부의 룰 묶음, hook 에 attach

6v6-fw 의 `inet six_filter` 안의 chain 들 (실측):

```
table inet six_filter {
    chain input {
        type filter hook input priority filter; policy accept;
        tcp dport 22 accept           # SSH 허용
        ip protocol icmp accept       # IPv4 ICMP 허용
        ip6 nexthdr icmpv6 accept     # IPv6 ICMP 허용
        ct state established,related accept   # 응답 path
    }
    chain forward {
        type filter hook forward priority filter; policy accept;
        ct state established,related accept   # 응답 path
        # 학생 lab 에서 룰 추가하며 학습할 위치
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

chain header 의 4 attribute:
- `type filter` : 필터 (ACCEPT/DROP/REJECT) 용 — `nat` / `route` 도 가능
- `hook input` : 어느 Netfilter hook 에 attach
- `priority filter` (= 0) : 같은 hook 에 여러 chain 이 붙을 때 평가 순서 (낮을수록 먼저)
- `policy accept` : 룰이 다 매치 안 되면 기본 accept (production 은 `drop` 권장)

### 3.3 rule — 위에서 아래로 순차 평가

```
ct state established,related accept       # 조건: ct state → action: accept
ip saddr 10.20.30.202 drop                # 조건: src IP = attacker → drop
tcp dport 22 accept                       # 조건: dst port 22 → accept
log prefix "FW-DENY: " drop               # 조건: 위 어느 룰도 안 매치 → log + drop
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
- NAT actions (W03): `dnat to ...` / `snat to ...` / `masquerade`

### 3.4 set — 여러 값을 1개 이름으로 참조

대규모 blocklist (1000+ IP) 도 set 하나로 표현 가능.

```bash
# set 생성
nft add set ip filter blocklist '{ type ipv4_addr ; }'

# element 추가
nft add element ip filter blocklist '{ 1.2.3.4, 5.6.7.8, 9.10.11.12 }'

# rule 에서 참조
nft add rule ip filter input ip saddr @blocklist drop
```

`@blocklist` 가 set 참조. set 에 추가/삭제는 ruleset 재컴파일 없이 O(1).

---

## 4. 6v6-fw 의 ruleset 해부

### 4.1 entrypoint 가 부팅마다 `/etc/nftables.conf` 적용

```bash
# /entrypoint.sh 내부 (요약)
echo "[fw] applying nftables (six_filter / six_nat tables)"
nft -f /etc/nftables.conf 2>&1 | sed 's/^/  /' || echo "[fw] WARN: nft apply failed"
```

### 4.2 nftables.conf 본체 (실제 컨테이너 파일)

```nft
#!/usr/sbin/nft -f
# 6v6 fw — edge router firewall (ext <-> pipe).
# docker NAT 룰 (table ip nat) 은 보존하고, 우리 정책 테이블만 정의.
# 식별자는 letter/_ 로 시작 (digit 시작은 nft 파서가 거부).

add table inet six_filter
flush table inet six_filter

table inet six_filter {
    chain input {
        type filter hook input priority 0
        policy accept
        tcp dport 22 accept
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept
        ct state established,related accept
    }
    chain forward {
        type filter hook forward priority 0
        policy accept
        ct state established,related accept
    }
    chain output {
        type filter hook output priority 0
        policy accept
    }
}

add table ip six_nat
flush table ip six_nat
table ip six_nat {
    chain prerouting {
        type nat hook prerouting priority -100
        policy accept
    }
    chain postrouting {
        type nat hook postrouting priority 100
        policy accept
    }
}
```

핵심 디자인 결정:
- `inet six_filter` 가 IPv4+IPv6 통합 → 룰 1번만 작성하면 두 family 모두 적용
- `flush table inet six_filter` 가 idempotent 보장 (부팅마다 깨끗한 상태)
- `ip six_nat` 는 chain 만 정의 + 룰 없음 → W03 에서 학생이 NAT 룰 추가하며 학습
- `policy accept` (학습용). production 은 `policy drop` + 명시적 화이트리스트가 정석.

---

## 5. nft 명령 cheat sheet

| 목적 | 명령 |
|------|------|
| 전체 ruleset 출력 | `sudo nft list ruleset` |
| filter table 만 | `sudo nft list table inet six_filter` |
| 특정 chain 만 | `sudo nft list chain inet six_filter forward` |
| **handle 포함** | `sudo nft -a list chain inet six_filter forward` |
| JSON 출력 | `sudo nft -j list ruleset \| jq .` |
| syntax 검증 | `sudo nft -c -f /etc/nftables.conf && echo OK` |
| 룰 추가 (위) | `sudo nft insert rule inet six_filter forward position 0 <cond> <action>` |
| 룰 추가 (아래) | `sudo nft add rule inet six_filter forward <cond> <action>` |
| 룰 삭제 | `sudo nft delete rule inet six_filter forward handle <N>` |
| counter reset | `sudo nft reset counters table inet six_filter` |
| 룰셋 통째 교체 | `sudo nft -f /tmp/new-ruleset.nft` (atomic) |
| 룰셋 fully flush | `sudo nft flush table inet six_filter` (6v6 정책만, docker NAT 보존) |
| 실시간 모니터 | `sudo nft monitor` (변경 감시) |
| 실시간 trace | `sudo nft monitor trace` (룰 통과 추적) |

---

## 6. iptables ↔ nftables 마이그레이션 (3 도구)

### 6.1 iptables-translate — 한 줄 변환

```bash
$ echo "iptables -A INPUT -p tcp --dport 22 -j ACCEPT" | iptables-translate
nft add rule ip filter INPUT tcp dport 22 counter accept
```

> ⚠️ STDIN 으로 받는 게 안 되는 경우 (Ubuntu 22.04 의 일부 버전): `iptables-translate
> -A INPUT -p tcp --dport 22 -j ACCEPT` 처럼 argv 로 전달.

### 6.2 iptables-restore-translate — 전체 룰셋 변환

```bash
sudo iptables-save > /tmp/legacy.rules
sudo iptables-restore-translate -f /tmp/legacy.rules > /tmp/new.nft
sudo nft -c -f /tmp/new.nft && echo "변환 OK"
```

### 6.3 iptables-nft — 호환 backend (자동)

Debian/Ubuntu/RHEL 의 `iptables` 명령은 이미 nftables backend 호환 모드.

```bash
$ readlink /etc/alternatives/iptables
/usr/sbin/iptables-nft     # nftables backend (마이그레이션 표준)
```

`iptables -L` 의 결과는 사실 nftables `table ip filter` 의 INPUT/FORWARD/OUTPUT chain.

---

## 7. 영구화: 컨테이너 vs systemd

### 7.1 시스템 호스트 (운영 표준)

```bash
sudo nft list ruleset > /etc/nftables.conf
sudo systemctl enable nftables
sudo systemctl restart nftables
```

부팅 시 `nftables.service` 가 `/etc/nftables.conf` 를 atomic load.

### 7.2 컨테이너 (6v6 의 방식)

도커 컨테이너는 stateless 라 부팅마다 `entrypoint.sh` 가 ruleset 을 재구성한다.

```bash
docker exec 6v6-fw sudo cat /entrypoint.sh | grep -E "^nft|^iptables"
# nft -f /etc/nftables.conf 2>&1 | sed 's/^/  /' || echo "[fw] WARN: nft apply failed"
```

학생이 컨테이너 안에서 `nft add rule ...` 으로 추가한 룰은 컨테이너 재시작 시 사라
진다. 영구화 하려면 `entrypoint.sh` 또는 `nftables.conf` 수정 + 이미지 재빌드 + push
+ 컨테이너 recreate.

---

## 8. 정책 설계 원칙 — Deny by Default

운영 환경의 정석은 두 원칙.

1. **Default deny** — chain policy 를 `drop` 으로 설정한 뒤 필요한 트래픽만 명시 허용
2. **Specific before general** — 더 구체적인 룰을 위에. set 으로 큰 그룹을 한 줄로.

production-grade chain 예:

```
chain forward {
    type filter hook forward priority 0; policy drop;     # ← default deny

    ct state established,related accept                   # ← 가장 빈번 (early-exit)
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

## 9. 실습 시나리오 (4 축 설명)

### 실습 1 — fw ruleset 가시화 (10분)

> **이 실습을 왜 하는가?** — fw 의 현재 정책이 무엇인지 파악. 운영 인수의 첫 명령.
>
> **이걸 하면 무엇을 알 수 있는가?** — 3 table (ip nat / inet six_filter / ip six_nat)
> 의 존재 + chain header 의 4 attribute + 활성 룰의 정확한 syntax.
>
> **결과 해석** — table 3 표시 + chain header 의 type/hook/priority/policy 모두 명시
> + counter 0 (트래픽 미발생 또는 reset 직후).
>
> **실전 활용** — 운영 인수 첫 5분 명령. 정책 분석.

```bash
ssh 6v6-fw 'sudo nft list ruleset 2>&1 | grep -v "^XT"'
ssh 6v6-fw 'sudo nft list table inet six_filter'
ssh 6v6-fw 'sudo nft -j list ruleset | jq ".nftables | length"'
```

**실측 결과** (2026-05-11):
```
table ip nat
table inet six_filter
table ip six_nat
```

`XT match tcp not found` 같은 경고는 docker 의 ipset 호환 모듈 부재로 인한 출력 잡음
이며 우리 정책 동작과 무관.

### 실습 2 — counter 분석 (10분)

> **이 실습을 왜 하는가?** — 룰별 byte/packet 통계 가시화. 어느 룰이 빈번한지 확인.
>
> **결과 해석** — 활성 트래픽 발생 시 counter 가 증가. 0 이면 룰 미매치 (불필요한 룰?).
>
> **실전 활용** — 룰 효율 측정. 한 번도 매치 안 되는 룰은 candidate for removal.

```bash
ssh 6v6-fw 'sudo nft -a list chain inet six_filter forward'    # handle 포함
ssh 6v6-fw 'sudo nft reset counters table inet six_filter'     # counter 0 으로
ssh 6v6-fw 'sudo nft list chain inet six_filter forward | grep -B1 counter'
```

**실측 결과**:
```
chain forward { # handle 2
    type filter hook forward priority filter; policy accept;
    ct state established,related accept # handle 8
}
```

`# handle 2` (chain 자체의 handle) + `# handle 8` (룰의 handle). 삭제 시 사용.

### 실습 3 — 동적 drop 룰 추가 + 효과 검증 (15분)

> **이 실습을 왜 하는가?** — 실 운영 시 incident 대응 (특정 IP 즉시 차단) 의 핵심.
>
> **이걸 하면 무엇을 알 수 있는가?** — `nft insert rule ... position 0` 의 효과 + chain
> evaluation 순서 + log prefix 의 kernel ring buffer 기록.
>
> **결과 해석** — 룰 추가 후 attacker 의 fw 진입이 timeout (응답 없음). dmesg 에
> `DROP-ATTACKER: ...` 라인.
>
> **실전 활용** — incident response 시 분 단위 IP block. 영구화는 ruleset 수정.

```bash
# 룰 추가 (input chain — fw 자체로 들어오는 트래픽 차단)
ssh 6v6-fw 'sudo nft insert rule inet six_filter input position 0 ip saddr 10.20.30.202 counter log prefix "DROP-ATTACKER: " drop'

# attacker 가 fw:80 시도 → timeout
ssh 6v6-attacker 'timeout 5 curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" http://10.20.30.1/'
# 응답: 000 (timeout)

# kernel log 의 prefix
ssh 6v6-fw 'sudo dmesg | tail -5 | grep DROP-ATTACKER'

# 룰 삭제 (handle 식별 후)
HANDLE=$(ssh 6v6-fw 'sudo nft -a list chain inet six_filter input | grep DROP-ATTACKER | grep -oE "handle [0-9]+" | head -1 | awk "{print \$2}"')
ssh 6v6-fw "sudo nft delete rule inet six_filter input handle $HANDLE"
```

> **핵심 인사이트**: fw 자체로 들어오는 트래픽 (HAProxy 가 80 으로 받는) 은 `input`
> chain. fw 를 통과만 하는 트래픽 (ext → pipe forward) 은 `forward` chain. 같은 src
> IP 라도 어느 chain 의 drop 인지에 따라 효과가 다르다.

### 실습 4 — tcpdump 로 drop 검증 (15분)

```bash
# 한 터미널 (학생 PC) — 패킷 캡처
ssh 6v6-fw 'sudo timeout 10 tcpdump -ni eth0 host 10.20.30.202 -c 5'

# 다른 터미널 — 트래픽 발생
ssh 6v6-attacker 'curl -H "Host: juice.6v6.lab" http://10.20.30.1/'
```

drop 룰 있을 때: SYN 만 보이고 SYN-ACK 없음 → 3-way handshake 미완성. 룰 삭제 후:
SYN + SYN-ACK + ACK 정상 표시.

### 실습 5 — iptables-translate + nft monitor (15분)

```bash
# iptables 명령을 nft 로 변환
ssh 6v6-fw 'iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT'
ssh 6v6-fw 'iptables-translate -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT'

# nft monitor — 실시간 변경 + trace
ssh 6v6-fw 'sudo timeout 5 nft monitor 2>&1 | head -10'
```

`nft monitor` 은 운영 시 누가 룰 추가/삭제하는지 audit + race 검출에 유용.

### 실습 6 — **R/B/P 통합 시나리오** (25분)

```mermaid
graph LR
    R["Red — attacker 가<br/>nmap 무차별 스캐닝"] -->|fw port 80 SYN flood| FW[fw nftables]
    FW -->|log + drop| B["Blue — input chain<br/>drop 룰 추가"]
    B -->|효과 측정| P["Purple — counter +<br/>tcpdump + 영구화 검토"]
    P -->|nftables.conf patch| FW
    style R fill:#f85149,color:#fff
    style B fill:#1f6feb,color:#fff
    style P fill:#bc8cff,color:#fff
```

**Red — nmap 무차별 스캐닝**:
```bash
ssh 6v6-attacker 'sudo nmap -sS -p 22,80,443,9100 10.20.30.1 2>&1 | tail -10'
```

**Blue — drop 룰 + log 추가**:
```bash
ssh 6v6-fw 'sudo nft insert rule inet six_filter input position 0 ip saddr 10.20.30.202 counter log prefix "RBP-DROP: " drop'
```

**Red — 다시 시도 (timeout 예상)**:
```bash
ssh 6v6-attacker 'sudo nmap -sS -p 22,80,443,9100 10.20.30.1 2>&1 | tail -10'
# 모든 포트 filtered 또는 closed
```

**Purple — 효과 측정**:
```bash
ssh 6v6-fw 'sudo nft -a list chain inet six_filter input | head -5'
# counter packets N bytes M 가 0 → 증가 (drop 적중)
ssh 6v6-fw 'sudo dmesg | tail -20 | grep RBP-DROP | head -5'
```

**Purple — 영구화 검토** (학습용 시뮬):
```bash
# 본인이 nftables.conf 에 적용한다고 가정한 patch
cat <<'EOF'
# /etc/nftables.conf 의 chain input 끝에 추가
table inet six_filter {
    chain input {
        ...
        ip saddr 10.20.30.202 counter log prefix "PERSIST-DROP: " drop
    }
}
EOF
```

production 환경은 위 patch 를 git PR 검토 후 image 재빌드 + rolling restart.

**Cleanup** (실험 종료):
```bash
HANDLE=$(ssh 6v6-fw 'sudo nft -a list chain inet six_filter input | grep RBP-DROP | grep -oE "handle [0-9]+" | head -1 | awk "{print \$2}"')
ssh 6v6-fw "sudo nft delete rule inet six_filter input handle $HANDLE"
```

---

## 9.5 R/B/P 공격 분석 케이스 확장 (본 주차 추가)

### 9.5.0 R/B/P 일상 비유 — 출입문 무인 경비원

본 절은 nftables 를 출입문의 무인 경비원에 비유해서 시작한다.

학생이 사는 아파트의 정문 출입문을 떠올려보자. 정문에는 무인 경비원이 한 명 서 있고, 출입 규칙이 정리된 매뉴얼을 들고 있다. 매뉴얼에는 다음과 같은 규칙이 적혀 있다.

- 입주민 카드를 가진 사람은 통과시킨다.
- 택배 기사는 평일 09시~18시에만 통과시킨다.
- 같은 사람이 1분 안에 5번 이상 시도하면 차단한다.
- 매뉴얼에 없는 경우는 일단 차단한다 (deny by default).

무인 경비원이 출입 시도를 기록하면 카운터가 올라간다. 시도가 비정상적으로 많으면 보안실에서 알람이 울린다. 보안실 관리자는 매뉴얼에 새 규칙을 추가하거나 기존 규칙을 강화한다.

| 일상 비유 | nftables |
|-----------|----------|
| 무인 경비원 매뉴얼 | nftables.conf 의 ruleset |
| 매뉴얼 페이지 (입주민, 택배) | table 의 chain |
| 한 줄 규칙 | rule |
| 차단 명단 | set |
| 시도 카운터 | counter |
| 보안실 알람 | log prefix |
| 매뉴얼 검토 + 강화 | Purple 의 rule 보완 |

본 절은 nftables 의 set / counter / log / rate limit 같은 기능을 실제 공격에 대응하는 흐름으로 학습한다. 세 케이스를 다룬다.

- 케이스 1 — ICMP flood 를 counter + dynamic set 으로 분석 + 차단한다.
- 케이스 2 — TCP SYN flood 를 nft monitor trace + rate limit 으로 분석 + 대응한다.
- 케이스 3 — forwarded chain 우회 시도를 policy drop + log prefix 로 가시화한다.

본 절의 핵심 원칙 네 가지는 W01 의 5.7 절과 동일하다.

- **재현 가능성** — 학생이 attacker VM (192.168.0.112) 에서 직접 공격을 발생시킨다.
- **도구 위주 분석** — `nft list ruleset`, `nft monitor`, `conntrack -L` 같은 표준 도구만 사용한다.
- **신입생 친화** — 명령의 옵션을 한 줄씩 설명한다.
- **윤리 강제** — 학습 환경 안 (192.168.0.0/24) 에서만 시도한다.

### 9.5.1 케이스 1 — ICMP flood 의 분석 + dynamic set 차단

**0. 일상 비유 — 도둑이 초인종을 1초에 100번 누르기.**

도둑이 아파트 정문 초인종을 1초에 100번 누른다. 정상 입주민은 보통 하루에 몇 번만 누른다. 무인 경비원이 매뉴얼 페이지를 펴면 "분당 60회 초과 시 5분간 차단" 같은 규칙이 적혀 있다. 도둑이 임계치를 넘어서면 명단에 자동 등록되고, 5분 동안 같은 사람의 시도는 모두 차단된다.

이 비유를 ICMP flood 에 그대로 옮긴다.

| 일상 비유 | ICMP flood |
|-----------|-----------|
| 초인종 누르기 | ping (ICMP echo request) |
| 분당 60회 초과 | nft rate limit 의 임계치 |
| 자동 차단 명단 | nft dynamic set |
| 5분간 차단 유지 | set element 의 timeout |
| 매뉴얼의 명단 페이지 | `nft list set inet six_filter blacklist` |

본 케이스의 학습 목표는 nftables 의 동적 set + timeout 의 동작을 실제 ICMP flood 로 직접 확인하는 것이다.

**0a. 사용 도구 사전 안내.**

- **ping** — ICMP echo request 를 보내는 표준 도구다. `-f` (flood), `-c N` (개수), `-i 0.001` (간격) 옵션을 함께 쓰면 부하 시뮬레이션이 가능하다.
- **nft set** — nftables 의 set 자료구조다. IP 주소나 포트 번호를 묶어서 한 이름으로 참조하게 한다. `flags timeout` 을 붙이면 자동 만료가 가능해진다.
- **nft counter** — rule 안에서 `counter` keyword 를 쓰면 packets + bytes 가 자동으로 누적된다.

**1. Red — 공격 재현.**

학생이 attacker VM (192.168.0.112) 에 들어간 뒤 fw 외부 IP 로 ICMP flood 를 보낸다. 학습 환경 안에서만 실행해야 한다.

```bash
ssh ccc@192.168.0.112
# password: 1
```

attacker VM 내부에서 fw 의 외부 IP (예: 192.168.0.103) 로 ping flood 를 보낸다.

```bash
# attacker VM 내부 (학습 환경 한정)
sudo ping -f -c 500 192.168.0.103
```

각 옵션의 의미는 다음과 같다.

- `sudo` — flood 옵션은 root 권한이 필요하다.
- `-f` — flood. 응답을 기다리지 않고 가능한 빨리 보낸다.
- `-c 500` — 500개만 보내고 종료한다.
- `192.168.0.103` — target IP. 학습 환경 내부.

500개를 짧은 시간에 보내므로 fw 의 input chain counter 가 급격히 올라간다.

**2. 발생하는 로그/아티팩트.**

먼저 fw 의 nft input chain counter 가 증가한다. ICMP 를 별도로 카운트하는 룰이 있으면 그 룰의 counter 가 크게 뛴다. 다음으로 dmesg 에 log prefix 가 찍히는 룰이 있으면 kernel ring buffer 에 흔적이 남는다.

Wazuh agent 가 dmesg 또는 `/var/log/kern.log` 를 모니터링하기 때문에, 같은 사건이 Wazuh manager 에도 alert 로 다시 기록될 수 있다.

**3. Blue — nft 도구로 직접 분석.**

학생이 fw 에 들어가서 nft 명령으로 상태를 본다. ProxyJump 가 설정되어 있으면 한 줄로 가능하다.

```bash
ssh 6v6-fw
# fw 내부
sudo nft list chain inet six_filter input
```

화면에 chain 의 모든 rule 이 나열된다. counter 가 붙은 rule 의 첫 줄에 `packets N bytes M` 형태로 누적값이 보인다. ICMP flood 직전과 직후의 counter 값을 비교하면 변화량이 즉시 드러난다.

다음으로 동적 set 의 내용을 확인한다.

```bash
sudo nft list set inet six_filter blacklist
```

학습 환경에서는 ICMP rate limit rule 이 set 에 element 를 추가하도록 미리 구성되어 있다. set 안에 `192.168.0.112 timeout 5m` 같은 항목이 보이면 자동 차단이 동작한 것이다.

마지막으로 `nft monitor trace` 로 실시간 packet 흐름을 본다.

```bash
sudo nft monitor trace
```

다른 터미널에서 attacker VM 으로부터 다시 ping 을 보내면, fw 의 nft monitor 가 한 줄씩 packet 의 처리 과정을 출력한다. drop verdict 가 보이면 rule 이 적중한 것이다.

**4. Blue — 대응 의사결정.**

학생이 분석을 마친 뒤 다음 세 가지를 판단한다.

- **set timeout 적정성.** 5분이 너무 길거나 짧지 않은지 본다. 학습 환경에서는 1~5분이 적절하다.
- **임계치 적정성.** 분당 60회가 너무 관대하지 않은지 본다. 정상 헬스체크가 분당 몇 번인지 함께 본다.
- **로깅 충분성.** drop rule 에 `log prefix` 가 붙어 있는지 본다. 로그가 없으면 사후 분석이 어렵다.

**5. Purple — 보완.**

분석 결과를 바탕으로 nftables.conf 를 다음 세 가지 방향으로 보완한다.

- **set timeout 조정.** `flags timeout` 의 기본 timeout 을 5m 에서 운영 정책에 맞게 정한다.
- **카운터 분리.** ICMP / TCP SYN / UDP 의 counter 를 별도 rule 로 나누면 다음 분석이 쉬워진다.
- **log prefix 표준화.** "ICMP-FLOOD: ", "SYN-FLOOD: " 같이 접두어를 명확히 정해서 Wazuh / Suricata 가 파싱하기 쉽게 만든다.

한 케이스 cycle 은 약 20분 정도다.

### 9.5.2 케이스 2 — TCP SYN flood 의 분석 + rate limit 대응

**0. 일상 비유 — 가짜 손님이 입구를 막기.**

식당 입구에 가짜 손님 1000명이 동시에 들어와 자리를 잡지 않고 그냥 서 있다고 상상해보자. 진짜 손님은 자리를 못 찾고 돌아간다. 식당 매니저는 "한 사람당 10초 안에 자리 못 잡으면 나가달라고 안내" 같은 규칙을 추가한다. 이로써 진짜 손님의 자리가 확보된다.

이 비유를 TCP SYN flood 에 그대로 옮긴다.

| 일상 비유 | TCP SYN flood |
|-----------|---------------|
| 가짜 손님이 자리만 차지 | SYN 만 보내고 ACK 안 보냄 (half-open) |
| 진짜 손님이 자리 못 잡음 | 정상 client 의 connection 거부 |
| 매니저의 시간 제한 규칙 | conntrack 의 SYN_SENT timeout |
| 안내 직원 추가 | nft rate limit rule 추가 |

**0a. 사용 도구 사전 안내.**

- **hping3** — TCP / UDP / ICMP packet 을 임의로 만들어 보내는 도구다. attacker VM 에 미리 설치되어 있다.
- **conntrack -L** — 현재 fw 의 connection tracking table 을 보는 명령이다. SYN_SENT / ESTABLISHED / TIME_WAIT 같은 state 별 connection 수를 보여준다.
- **nft rate limit** — `limit rate 100/second` 같은 형식으로 초당 / 분당 packet 수를 제한하는 rule 옵션이다.

**1. Red — 공격 재현.**

attacker VM 에서 hping3 으로 SYN flood 를 보낸다. 학습 환경 안에서만 실행해야 한다.

```bash
ssh ccc@192.168.0.112
# password: 1

# attacker VM 내부 (학습 환경 한정)
sudo hping3 -S -p 80 --flood -c 200 192.168.0.103
```

각 옵션의 의미는 다음과 같다.

- `-S` — SYN flag 만 set. half-open 시도를 만든다.
- `-p 80` — target port 80 (HTTP).
- `--flood` — 응답을 기다리지 않고 최대 속도로 보낸다.
- `-c 200` — 200개만 보내고 종료한다.

`--flood` 와 `-c` 를 함께 쓰면 짧은 시간에 200개를 폭주시킬 수 있다.

**2. 발생하는 로그/아티팩트.**

fw 의 conntrack table 이 갑자기 부풀어 오른다. SYN_SENT state 의 entry 가 다수 생긴다. nft input chain 의 counter 도 즉시 증가한다. 학습 환경의 ips 컨테이너 Suricata 가 같은 traffic 을 packet sniff 하기 때문에 `eve.json` 에도 `ET SCAN` 또는 `ET DOS` 계열 signature 가 함께 발생할 수 있다.

**3. Blue — conntrack 와 nft 로 직접 분석.**

fw 에 들어간 뒤 conntrack 상태를 본다.

```bash
ssh 6v6-fw
sudo conntrack -L -p tcp --dport 80 2>/dev/null | head -20
```

각 라인은 다음 형식이다.

```
tcp 6 30 SYN_SENT src=192.168.0.112 dst=192.168.0.103 sport=54321 dport=80 ...
```

SYN_SENT state entry 가 200개 가까이 있으면 SYN flood 의 직접 흔적이다. 정상 traffic 은 ESTABLISHED state 가 대부분이다.

다음으로 state 별 통계를 본다.

```bash
sudo conntrack -L 2>/dev/null | awk '{print $4}' | sort | uniq -c | sort -rn | head
```

`SYN_SENT` 가 비정상적으로 많이 나오면 flood 의 증거다.

마지막으로 nft input chain 의 counter 변화를 본다.

```bash
sudo nft list chain inet six_filter input | grep -A1 "tcp dport 80"
```

counter 의 packets 값이 급증한 것을 확인한다.

**4. Blue — 대응 의사결정.**

학생이 다음 세 가지를 판단한다.

- **rate limit 임계치.** 정상 HTTP request 가 초당 몇 건인지 baseline 을 확인한다. flood 가 그보다 훨씬 큰 값인지 본다.
- **연결 차단 vs rate limit.** 즉시 차단보다 rate limit 이 더 안전한 경우가 많다. 정상 client 의 영향을 최소화한다.
- **conntrack timeout 조정.** SYN_SENT timeout 을 60초에서 30초로 줄이면 half-open entry 가 빨리 정리된다.

**5. Purple — 보완.**

다음 세 가지를 nftables.conf 에 반영한다.

- **rate limit rule 추가.** input chain 의 tcp dport 80 앞에 `limit rate 100/second burst 50 packets` 를 추가한다. 정상 traffic 은 거의 영향이 없고 flood 만 차단된다.
- **counter 분리.** `tcp dport 80 syn` 의 counter 를 별도 rule 로 분리하면 SYN flood 의 baseline 을 직접 측정할 수 있다.
- **conntrack 모니터링 cron 추가.** SYN_SENT 가 100 이상이면 알람이 뜨도록 간단한 shell script 를 cron 에 등록한다.

### 9.5.3 케이스 3 — forwarded chain 우회 시도의 분석

**0. 일상 비유 — 정문 대신 비상구로 들어가려는 시도.**

도둑이 아파트 정문에서 막히면 비상구로 우회를 시도한다. 비상구에도 경비원이 있어야 한다. 비상구의 경비원도 매뉴얼이 있어야 하고, 매뉴얼이 비어 있으면 도둑이 그냥 통과해버린다.

이 비유를 nftables 의 forward chain 에 옮긴다. input chain 은 정문이고 forward chain 은 비상구다. forward chain 의 policy 가 accept 면 6v6 의 다른 서브넷으로 우회가 가능해진다.

| 일상 비유 | forward chain |
|-----------|---------------|
| 정문 | input chain |
| 비상구 | forward chain |
| 비상구의 경비원 매뉴얼 | forward chain 의 rule |
| 비상구 매뉴얼 비어 있음 | policy accept |
| 비상구 매뉴얼 채움 | policy drop + 명시 rule |

**0a. 사용 도구 사전 안내.**

- **nmap -Pn -sS --reason** — `-Pn` 은 host discovery 생략, `--reason` 은 각 port 결과의 이유 (예: `syn-ack`, `reset`, `no-response`) 를 함께 출력한다.
- **nft policy** — chain 의 default verdict 를 정한다. `policy drop` 이면 매칭되는 rule 이 없을 때 자동 차단된다.
- **`log prefix`** — rule 에 붙이면 kernel ring buffer 에 prefix 가 찍힌 로그가 남는다.

**1. Red — 공격 재현.**

attacker VM 에서 fw 너머의 dmz 또는 int 자산에 직접 packet 을 보낸다. fw 가 NAT / forwarding 을 처리하는 경로다.

```bash
ssh ccc@192.168.0.112
# password: 1

# attacker VM 내부 (학습 환경 한정)
nmap -Pn -sS --reason -p 22,80,3306,5432 192.168.0.108
```

각 옵션의 의미는 다음과 같다.

- `-Pn` — host discovery 생략. ICMP block 환경에서 유용하다.
- `-sS` — SYN scan.
- `--reason` — 각 port 의 결과 이유를 함께 출력한다.
- `-p 22,80,3306,5432` — SSH, HTTP, MySQL, PostgreSQL 표준 port.
- `192.168.0.108` — dmz VM 의 IP. fw 너머의 자산이다.

예상 결과는 두 가지로 갈린다. forward chain policy 가 drop 이면 모든 port 가 `filtered` 로 표시된다. policy 가 accept 면 일부 port 가 `open` 또는 `closed` 로 표시되며, 이는 우회 가능성을 의미한다.

**2. 발생하는 로그/아티팩트.**

fw 의 nft forward chain counter 가 증가한다. dmesg 에 forward chain 의 log prefix 가 찍힌다. Suricata 가 같은 traffic 을 packet sniff 해서 eve.json 에 alert 가 함께 발생한다.

**3. Blue — nft 와 dmesg 로 직접 분석.**

fw 에 들어가서 forward chain 의 policy 와 rule 을 본다.

```bash
ssh 6v6-fw
sudo nft list chain inet six_filter forward
```

화면 첫 줄에 `policy drop` 또는 `policy accept` 가 표시된다. policy drop 이면 deny by default 가 적용되는 안전한 상태다. policy accept 면 모든 forwarded packet 이 그냥 통과한다.

다음으로 counter 변화량을 확인한다. attacker 시도 전후의 packets 값을 비교한다.

dmesg 에서 log prefix 가 찍힌 라인을 확인한다.

```bash
sudo dmesg --ctime | grep "FWD-DROP" | tail -20
```

각 라인에 source IP, destination IP, port 가 함께 기록된다. 이로부터 어떤 우회 시도가 있었는지 즉시 식별할 수 있다.

**4. Blue — 대응 의사결정.**

학생이 다음 세 가지를 판단한다.

- **forward policy 의 안전성.** policy drop 이 기본이어야 한다. policy accept 면 즉시 drop 으로 바꿔야 한다.
- **로깅 충분성.** log prefix 가 forward chain 의 drop rule 에 붙어 있는지 확인한다.
- **dmz / int 으로 가는 정상 traffic 식별.** 차단으로 인해 정상 운영이 끊기지 않는지 본다.

**5. Purple — 보완.**

nftables.conf 에 다음 세 가지를 적용한다.

- **policy drop 강제.** forward chain 의 첫 줄을 `type filter hook forward priority 0; policy drop;` 로 설정한다.
- **명시적 accept rule.** 정상 운영에 필요한 traffic (예: bastion → dmz 의 SSH) 만 명시적으로 accept 한다.
- **drop 직전 log rule.** 모든 forward drop 의 직전에 `log prefix "FWD-DROP: "` 를 둔다.

본 절의 세 케이스가 끝나면 nftables 의 set / counter / rate limit / forward policy / log 의 운영을 전부 한 번씩 직접 경험한 셈이다.

### 9.5.4 본 절 정리

본 절은 W02 의 nftables 학습을 실제 공격 분석 cycle 에 연결했다. 학생이 다음을 능력으로 갖춘다.

- attacker VM 에서 ICMP / SYN / forwarded 우회 시도를 직접 재현한다.
- nft list, counter, monitor trace 명령으로 흔적을 직접 분석한다.
- conntrack -L 로 connection state 를 직접 본다.
- 분석 결과를 바탕으로 set timeout, rate limit, policy drop, log prefix 를 자기 손으로 보완한다.

다음 주차 W03 에서는 NAT + HAProxy 의 같은 R/B/P cycle 을 학습한다.

---

## 10. 사례 분석 — ISMS-P / KISA / NIST

### 10.1 ISMS-P 2.6.1 (네트워크 접근통제)

본 주차의 fw nftables 가 ISMS-P 2.6.1 의 3 sub-control 모두 만족:

| Sub-control | 본 주차 활동 |
|------------|-------------|
| 2.6.1.1 외부→내부 접근 통제 | nftables filter table 의 input/forward chain |
| 2.6.1.2 정책 변경 승인·기록 | git audit (`6v6/fw/nftables.conf`) |
| 2.6.1.3 로그 1년 보관 | `log prefix` + rsyslog → SIEM 1년 retention |

### 10.2 KISA 보호나라 — 2025 침해사고 사례

KISA "2025 Q1 침해사고" 의 사례 중 **인터넷 노출 관리콘솔** 카테고리 (35%) 의 사고
패턴:

```
공격: 인터넷에 노출된 PostgreSQL 5432 → 무차별 대입 → 데이터 유출
방어: fw input chain 에서 5432/tcp 차단 + IP whitelist
```

본 주차의 실습 3 과 동일한 패턴. 실제 운영에 그대로 적용 가능.

### 10.3 NIST CSF — Protect.AC-4 (Access Permissions)

```mermaid
graph LR
    AC4[NIST PR.AC-4<br/>Access Permissions]
    AC4 --> NFT[nftables<br/>네트워크 접근 통제]
    AC4 --> RBAC[RBAC<br/>사용자 권한]
    AC4 --> MFA[MFA<br/>다요소 인증]
    NFT --> CHAIN[chain 별 정책]
    NFT --> SET[set 으로 그룹화]
    NFT --> LOG[log + counter]
    style AC4 fill:#1f6feb,color:#fff
    style NFT fill:#3fb950,color:#fff
```

본 과목 W02-W03 가 PR.AC-4 의 네트워크 측면 구현.

---

## 11. 과제

### A. 정책 강화 시뮬레이션 (필수, 40점)

6v6-fw 의 현재 `policy accept` 를 `policy drop` 으로 바꾸면 어떤 트래픽이 끊기는가?
다음 4 단계 진행:

1. **변경 전**: 4 vhost (juice / siem / portal / bastion) 모두 200/302 응답 확인
2. **policy drop 적용**: `ssh 6v6-fw 'sudo nft chain inet six_filter forward "{ policy drop ; }"'`
3. **영향 측정**: 4 vhost 응답 코드 재측정 + 어느 것이 끊겼는지 분석
4. **복구**: `policy accept` 복귀 + 정상 응답 확인

보고서: 1페이지 — 4 단계 출력 + 끊긴 트래픽 + 끊기지 않은 트래픽 + 이유 분석.

### B. iptables → nftables 마이그레이션 (심화, 30점)

다음 legacy iptables 룰 3건을 `iptables-translate` 로 변환 + 의미 한글 해설:

```
iptables -A INPUT -s 192.168.1.0/24 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT
```

### C. R/B/P 보고서 (정성, 30점)

실습 6 의 R/B/P 사이클 결과 + 다음 4 항목 포함 1페이지 보고서:

- attacker 의 nmap 결과 (filtered / closed / open 분포)
- fw counter 의 packets/bytes 증가량
- dmesg 의 RBP-DROP 라인 수
- production 환경에서 본 룰을 영구화한다면 어떤 절차 (git PR / 이미지 재빌드 / canary)

---

## 12. 평가 기준

| 항목 | 비중 | 평가 방법 |
|------|------|----------|
| 정책 강화 (A) | 40% | 4 단계 정확도 + 끊긴 트래픽 분석 |
| 마이그레이션 (B) | 30% | 3 변환 결과 + 한글 해설 |
| R/B/P 보고서 (C) | 30% | nmap 결과 + counter + dmesg + 영구화 절차 |

---

## 13. 핵심 정리 (1줄씩)

1. **Netfilter 5 hook** — prerouting / input / forward / output / postrouting. 어디서
   잡느냐가 정책의 핵심.
2. **nftables 4 핵심 개념** — table / chain / rule / set. 식별자는 letter/_ 로 시작.
3. **6v6-fw 의 실제 정책** — `inet six_filter` (정책) + `ip six_nat` (NAT stub, W03).
4. **drop vs reject** — drop 은 응답 없음 (스캐너 회피), reject 는 ICMP unreachable
   (사용자 친화).
5. **iptables ↔ nftables** — `iptables-translate` 가 표준 변환 도구. iptables-nft 가
   호환 backend.
6. **R/B/P 운영** — Red 가 공격 → Blue 가 룰 추가 → Purple 가 효과 측정 후 영구화 검토.

---

## 14. 다음 주차 (W03) 예고

- **주제**: nftables 방화벽 (2) — DNAT / SNAT / HAProxy 협업
- **실습 환경**: `6v6-fw` + `6v6-attacker` + `6v6-web`
- **핵심**: HAProxy 가 L7 라우팅 담당해도, nftables 의 `ip six_nat` table 이 어떻게
  보조 (외부 포트 ↔ 내부 컨테이너 매핑) 하는지, masquerade 가 응답 path 에 어떤 영향을
  미치는지.
- **R/B/P 시나리오**: Red 가 fw:8888 DNAT 통해 직접 web 접근 시도 → Blue 가 HAProxy
  와 nftables 동시 라우팅 충돌 시뮬 → Purple 가 priority + ACL 정리.
