# Week 03 — nftables 방화벽 (2) — DNAT / SNAT / HAProxy 협업

> 본 주차는 W02 의 nftables 기초 위에 **NAT (Network Address Translation)** 을 추가
> 한다. fw 컨테이너는 L4 NAT (`ip six_nat`) 와 L7 reverse proxy (HAProxy) 둘 다를
> 운영하며, 학생은 두 기술이 어떻게 협업하는지 (혹은 어떻게 충돌하는지) 를 실습으로
> 검증한다. 동시에 `conntrack -L` / `nft monitor trace` 같은 운영 디버그 도구도 익힌다.

## 학습 목표

학습자는 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. SNAT / DNAT / MASQUERADE 의 동작 원리와 hook (prerouting/postrouting) 위치를
   화이트보드에 그릴 수 있다.
2. nftables 의 NAT 룰을 `ip six_nat` table 에 직접 추가·삭제하고 효과를 검증한다.
3. HAProxy 의 L7 라우팅 (host header ACL) 과 nftables L3/L4 NAT 의 차이·협업 관계
   를 설명한다.
4. `conntrack -L` 로 활성 conn 의 src/dst 변환을 관찰한다.
5. `nft monitor trace` 로 한 패킷이 어떤 룰들을 통과하는지 step-by-step 추적한다.
6. L4 NAT 만으로 처리 가능한 경우 vs L7 HAProxy 가 필수인 경우를 구분한다.

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용                                                                    | 유형     |
|-----------|-------------------------------------------------------------------------|----------|
| 0:00–0:25 | 이론 — NAT 의 3 종류 (SNAT/DNAT/MASQUERADE) + 운영 시나리오             | 강의     |
| 0:25–0:55 | 이론 — Netfilter NAT chain (prerouting/postrouting) + conntrack 관계   | 강의     |
| 0:55–1:05 | 휴식                                                                     | —        |
| 1:05–1:30 | 이론 — HAProxy L7 (host header / SNI) vs nftables L4 NAT 의 협업 관계   | 강의     |
| 1:30–2:00 | 실습 1, 2 — DNAT 룰 추가 (외부 포트 → 내부 백엔드)                     | 실습     |
| 2:00–2:30 | 실습 3, 4 — SNAT / MASQUERADE 룰 + conntrack -L 분석                   | 실습     |
| 2:30–2:40 | 휴식                                                                     | —        |
| 2:40–3:10 | 실습 5, 6 — nft monitor trace 로 packet 추적 + HAProxy 와 충돌 시나리오  | 실습     |
| 3:10–3:30 | 실습 7 — 영구화 (nftables.conf 수정 + entrypoint 통합)                  | 실습     |
| 3:30–3:40 | 정리 + W04 (Suricata IDS) 예고                                          | 정리     |

---

## 1. NAT 의 3 종류

NAT 는 패킷의 IP 주소 또는 port 를 변환하는 동작. Netfilter 의 NAT hook 에서 동작
하며, 한 conn 의 첫 packet 에 적용된 변환이 conntrack 에 기록되어 후속 packet 에도
일관 적용된다.

### 1.1 SNAT (Source NAT)

**packet 의 출발지 IP/port 를 변환**. 내부 → 외부 통신 시 사용.

```
[내부] 10.20.31.2  →  [fw SNAT]  →  [외부] 192.168.0.110
       src=10.20.31.2                     src=192.168.0.110 (fw 의 ext IP)
       dst=8.8.8.8                        dst=8.8.8.8
```

**nft 명령**:
```
sudo nft add rule ip six_nat postrouting oifname "eth0" ip saddr 10.20.31.0/24 \
    snat to 10.20.30.1
```

### 1.2 DNAT (Destination NAT)

**packet 의 목적지 IP/port 를 변환**. 외부 → 내부 포워딩 시 사용 (port forwarding).

```
[외부] 192.168.0.x  →  [fw DNAT]  →  [내부] 10.20.40.81 (juiceshop)
       src=192.168.0.x                     src=192.168.0.x
       dst=192.168.0.110:8080              dst=10.20.32.80:80
```

**nft 명령**:
```
sudo nft add rule ip six_nat prerouting iifname "eth0" tcp dport 8080 \
    dnat to 10.20.32.80:80
```

### 1.3 MASQUERADE

**SNAT 의 특수 형태**. outbound NIC 의 IP 가 동적으로 변할 때 (DHCP 등) `to <IP>` 를
명시하지 않고 NIC 의 현재 IP 로 자동 변환.

```
sudo nft add rule ip six_nat postrouting oifname "eth0" ip saddr 10.20.31.0/24 masquerade
```

6v6 환경에서 fw 의 ext NIC IP 는 docker bridge 가 할당하므로 fixed 지만, production
container 환경 (Kubernetes 등) 에서는 NIC IP 가 매번 다르다 → MASQUERADE 가 정석.

### 1.4 priority 와 hook 위치

| Chain | hook | priority | 역할 |
|-------|------|----------|------|
| `prerouting`  | prerouting  | -100 | inbound DNAT (routing 결정 전) |
| `postrouting` | postrouting | 100  | outbound SNAT/MASQUERADE (routing 결정 후) |
| `output`      | output      | -100 | locally-generated 의 DNAT (loopback) |
| `input`       | input       | 100  | locally-destined 의 SNAT (rare) |

priority 가 낮을수록 먼저 평가. `prerouting -100` 은 routing decision 보다 일찍
평가되어 DNAT 가 routing 에 영향.

---

## 2. Netfilter NAT chain 의 흐름

```
        [packet 진입]
              │
              ▼
   ┌─────────────────────┐
   │  prerouting (mangle, nat -100, filter -150) │  ← DNAT 평가
   └──────────┬──────────┘
              │
        routing decision
              │
        ┌─────┴─────┐
        ▼           ▼
   ┌─────────┐  ┌──────────────┐
   │ INPUT   │  │ FORWARD      │  ← filter 평가 (W02)
   └────┬────┘  └──────┬───────┘
        │              │
        ▼              ▼
   local procs       output decision
        │              │
        ▼              ▼
   ┌─────────┐  ┌──────────────────────┐
   │ OUTPUT  │  │  postrouting (nat 100) │  ← SNAT/MASQUERADE 평가
   └────┬────┘  └──────────┬───────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
            [packet 출발]
```

핵심:
- **DNAT** 는 routing decision 보다 일찍 평가되어 변환된 dst IP 로 routing.
- **SNAT** 는 routing 후 평가 (이 시점이 NIC 결정됨 → MASQUERADE 가 NIC IP 알 수 있음).
- conntrack 은 첫 packet 의 변환을 기억 → 후속 응답 패킷 (역방향) 의 NAT 도 일관 적용.

---

## 3. conntrack 의 역할

`conntrack` (connection tracking) 은 stateful firewall + NAT 의 핵심.

```
$ sudo conntrack -L | head -3
tcp 6 86400 ESTABLISHED src=10.20.30.202 dst=10.20.30.1 sport=43210 dport=80 \
    src=10.20.30.1 dst=10.20.30.202 sport=80 dport=43210 [ASSURED] mark=0 use=1
```

각 row 가 한 conn 의 양방향 (orig → reply) 변환을 기록.

- **orig** : 첫 SYN 의 방향 (`src=10.20.30.202` → `dst=10.20.30.1`)
- **reply** : 응답 (`src=10.20.30.1` → `dst=10.20.30.202`)

NAT 가 일어났다면 orig 와 reply 의 src/dst 가 다르다. 예: DNAT 가 있으면 reply 의 src 는
변환된 IP.

운영 명령:
```
sudo conntrack -L                # 전체 conn 조회
sudo conntrack -L -p tcp         # TCP 만
sudo conntrack -L --src 10.20.30.202  # 특정 src
sudo conntrack -D --src 10.20.30.202  # 특정 conn 강제 종료
sudo conntrack -F                # 전체 flush (조심)
sudo conntrack -E                # 실시간 event stream
```

---

## 4. HAProxy L7 vs nftables L4 NAT

같은 "외부 포트 → 내부 백엔드" 라우팅이지만 두 도구는 동작 layer 가 다르다.

| 측면 | nftables DNAT (L4) | HAProxy (L7) |
|------|--------------------|--------------|
| 동작 layer | L3/L4 (IP + port) | L7 (HTTP host header / TLS SNI) |
| TCP termination | 없음 (pass-through) | termination + 새 backend conn |
| host header 라우팅 | 불가 (single backend per port) | 가능 (1 port → N backend) |
| TLS termination | 불가 (그냥 forward) | 가능 (cert 보유 시) |
| 부하 분산 | 단순 (1:1 또는 random) | 풍부 (roundrobin, leastconn, source) |
| 헬스체크 | 없음 | check + 자동 failover |
| 로깅 | nftables log prefix (kernel) | HAProxy access log (rsyslog) |
| 처리 비용 | 낮음 (커널 패킷 변환만) | 높음 (user space + TCP 두 번) |
| 운영 가시성 | counter / conntrack | stats socket / web UI |

### 4.1 협업 시나리오 1: HAProxy 가 80/443 만, 나머지는 nftables DNAT

```
외부 80 / 443         →  HAProxy L7 (host header 라우팅)
외부 9100 (Bastion)    →  HAProxy (단일 backend)  ← 또는 nftables DNAT
외부 2222 (학생 SSH)  →  nftables DNAT → 10.20.30.201:22 (bastion)
```

L7 가 필요한 트래픽 (host header) 만 HAProxy 가 처리, 단순한 1:1 port forwarding 은
nftables 가 더 효율적.

### 4.2 협업 시나리오 2: HAProxy 가 DNAT 결과를 받음

```
외부 → nftables DNAT (port 변환만) → HAProxy → backend
```

이 경우 HAProxy 입장에서는 항상 같은 backend conn → L7 라우팅이 hostname 으로 일관.
6v6 는 이 패턴을 사용 (외부 80 → fw eth0:80 의 docker NAT 가 HAProxy 에 도달).

### 4.3 충돌 시나리오: DNAT 와 HAProxy 가 같은 포트

```
nftables prerouting: tcp dport 80 dnat to 10.20.32.80:80   ← juiceshop 직접
HAProxy frontend: bind *:80                                   ← HAProxy 도 80
```

두 룰이 동시에 활성이면, prerouting 의 DNAT 가 먼저 평가되어 패킷이 10.20.40.81 로
변환된다. → HAProxy 는 패킷을 못 받음 → HAProxy 로그에 아무것도 안 남음.

검증: `conntrack -L` 로 dst 가 어디인지 확인.

---

## 5. 6v6-fw 의 NAT 정책 (현재 비어 있음)

W02 에서 본 것처럼 6v6 의 `ip six_nat` table 은 chain 만 정의되어 있고 룰이 비어 있다.

```
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

이는 fw 가 ext ↔ pipe 사이 direct routing 으로 동작하고 (NAT 불필요), L7 라우팅은
HAProxy 에 위임했기 때문. 학생은 본 주차에 학습용으로 NAT 룰을 추가하며 효과를 검증
한 후 삭제한다.

---

## 6. 실습 시나리오 1~7

### 실습 1 — DNAT 룰 추가 (외부 포트 → juiceshop 직접)

목표: fw 의 ext NIC 의 8888/tcp 로 들어온 트래픽을 directly juiceshop (10.20.32.80:80)
로 전달.

```
ssh 6v6-fw 'sudo nft add rule ip six_nat prerouting iifname "eth0" tcp dport 8888 \
    counter dnat to 10.20.32.80:80'

# 검증 — fw 의 ext NIC 에서 8888 으로 접근
# (학생 PC 또는 attacker 컨테이너)
ssh 6v6-attacker 'curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.1:8888/'
```

결과 200 이면 DNAT 동작. 단, fw 의 input chain 도 8888/tcp 를 허용해야 함:

```
ssh 6v6-fw 'sudo nft insert rule inet six_filter input position 0 tcp dport 8888 accept'
```

### 실습 2 — DNAT 효과 확인

```
ssh 6v6-fw 'sudo conntrack -L 2>/dev/null | grep dport=8888'
# orig: src=<attacker> dst=10.20.30.1 dport=8888
# reply: src=10.20.40.81 dst=<attacker> sport=3000
```

reply 의 src=10.20.40.81 → DNAT 가 dst 를 변환했음 가시화.

### 실습 3 — MASQUERADE 룰 추가

목표: ips/web/siem 등 dmz/int 의 컨테이너가 외부로 outbound 갈 때 fw 의 ext IP 로 masq.

```
ssh 6v6-fw 'sudo nft add rule ip six_nat postrouting oifname "eth0" \
    ip saddr 10.20.31.0/24 masquerade'
ssh 6v6-fw 'sudo nft add rule ip six_nat postrouting oifname "eth0" \
    ip saddr 10.20.32.0/24 masquerade'
ssh 6v6-fw 'sudo nft add rule ip six_nat postrouting oifname "eth0" \
    ip saddr 10.20.40.0/24 masquerade'
```

검증: dmz 의 컨테이너에서 외부로 ping (docker host NAT 가 받는 IP 가 fw IP 로 변환됨).

### 실습 4 — `conntrack -L` 분석

```
ssh 6v6-fw 'sudo conntrack -L 2>/dev/null | head -10'
# tcp 6 86400 ESTABLISHED src=<student> dst=<vm_ip> sport=xx dport=80 ...
```

각 컬럼의 의미를 한글로 1줄씩 분석 (orig/reply 양 방향, 상태, timeout).

### 실습 5 — `nft monitor trace` 로 packet 추적

```
# 한 패킷의 trace 활성화
ssh 6v6-fw 'sudo nft add rule inet six_filter prerouting iifname "eth0" tcp dport 80 \
    meta nftrace set 1'

# 다른 터미널에서 trace event 수신
ssh 6v6-fw 'sudo nft monitor trace 2>&1 | head -20'

# 또 다른 터미널에서 curl 발생
ssh 6v6-attacker 'curl -s -H "Host: juice.6v6.lab" http://10.20.30.1/'
```

trace event 가 각 룰 통과 단계를 출력 → 정책 디버깅의 황금 도구.

### 실습 6 — HAProxy 충돌 시나리오 시연

```
# fw 의 80/tcp 를 직접 DNAT 으로 juiceshop 으로 라우팅
ssh 6v6-fw 'sudo nft insert rule ip six_nat prerouting position 0 iifname "eth0" \
    tcp dport 80 counter dnat to 10.20.32.80:80'

# attacker → 80 시도
ssh 6v6-attacker 'curl -s -H "Host: juice.6v6.lab" http://10.20.30.1/ -o /dev/null \
    -w "%{http_code}\n"'

# HAProxy log 확인 (이 트래픽이 HAProxy 안 거침을 검증)
ssh 6v6-fw 'sudo tail -5 /var/log/haproxy.log 2>/dev/null || \
    sudo journalctl -u haproxy --since "1m ago" | tail -5'

# 실습 끝나면 룰 삭제
HANDLE=$(ssh 6v6-fw 'sudo nft -a list chain ip six_nat prerouting | grep "dport 80" | \
    grep -oE "handle [0-9]+" | head -1 | awk "{print \$2}"')
ssh 6v6-fw "sudo nft delete rule ip six_nat prerouting handle $HANDLE"
```

### 실습 7 — 영구화 시뮬레이션

```
# 본인이 추가한 룰을 nftables.conf 에 영구화한다 가정하여 patch 작성
cat <<'EOF' > /tmp/six_nat_patch.nft
add table ip six_nat
flush table ip six_nat
table ip six_nat {
    chain prerouting {
        type nat hook prerouting priority -100
        policy accept
        iifname "eth0" tcp dport 8888 counter dnat to 10.20.32.80:80
    }
    chain postrouting {
        type nat hook postrouting priority 100
        policy accept
        oifname "eth0" ip saddr 10.20.31.0/24 masquerade
        oifname "eth0" ip saddr 10.20.32.0/24 masquerade
        oifname "eth0" ip saddr 10.20.40.0/24 masquerade
    }
}
EOF

# syntax 검증
sudo nft -c -f /tmp/six_nat_patch.nft && echo "VALID"

# production 환경이면 git PR + 검토 후 배포
```

---

## 7. 용어 해설

| 용어 | 영문 | 설명 |
|------|------|------|
| **NAT** | Network Address Translation | 패킷의 IP/port 변환 |
| **SNAT** | Source NAT | 출발지 변환 (outbound) |
| **DNAT** | Destination NAT | 목적지 변환 (inbound port forwarding) |
| **MASQUERADE** | — | SNAT 의 특수 형태, NIC IP 자동 |
| **conntrack** | connection tracking | stateful 추적 (orig/reply 매핑) |
| **prerouting** | — | routing decision 전 hook (DNAT 위치) |
| **postrouting** | — | routing decision 후 hook (SNAT 위치) |
| **L7 reverse proxy** | — | 응용 계층 (HTTP/TLS) 으로 라우팅 |
| **TCP termination** | — | 한 TCP conn 을 종료하고 새 conn 으로 backend 연결 |
| **PAT** | Port Address Translation | port 도 변환하는 NAT (실무에서 SNAT/DNAT 의 부분) |
| **trace** | nft monitor trace | packet 이 어떤 룰들을 지나는지 실시간 가시화 |
| **SNI** | Server Name Indication | TLS handshake 에서 host name 표시 (L7 라우팅 키) |

---

## 8. 과제

### A. NAT 룰셋 작성 (필수)

다음 시나리오를 nftables 룰셋으로 작성하여 검증:

- 외부 9999/tcp 로 들어온 트래픽을 portal (10.20.32.50:8000) 로 전달.
- pipe (10.20.31.0/24) 의 모든 outbound 가 fw 의 ext NIC IP 로 SNAT.
- prerouting 에 trace 활성화 룰 추가 후 한 conn 의 trace 로그 첨부.

### B. HAProxy vs nftables 비교 (필수)

다음 표 채우기:

| 시나리오 | nftables 만 가능 | HAProxy 만 가능 | 둘 다 가능 |
|----------|-------------------|-------------------|-----------|
| 외부 80 → 단일 backend | | | |
| host header 별 다른 backend | | | |
| TLS termination | | | |
| 부하 분산 (roundrobin) | | | |
| TCP port forwarding | | | |

각 항목에 √ + 1줄 이유.

### C. conntrack 분석 (심화)

`conntrack -L` 출력 10건을 캡처하고, 각 row 의 orig vs reply 의 src/dst 변환이 어떤
NAT 룰에 의한 것인지 분석 (없으면 "변환 없음").

---

## 9. 평가 기준

| 항목 | 비중 | 평가 |
|------|------|------|
| NAT 룰셋 (A) | 40% | 정확도 + trace 첨부 + 검증 출력 |
| 비교 표 (B) | 30% | 5 항목 완성 + 이유 합리성 |
| conntrack 분석 (C) | 30% | 10 row 의 변환 해석 |

---

## 10. W04 (Suricata IDS) 예고

다음 주차는 **6v6-ips** 컨테이너의 Suricata 7.x 가 주제다. 본 주차의 fw L3/L4 통제가
시그니처 기반 L7 검사 (Suricata) 와 어떻게 협업하는지를 다룬다. 선수: Suricata
공식 문서의 "Suricata 5분 시작" 통독.
