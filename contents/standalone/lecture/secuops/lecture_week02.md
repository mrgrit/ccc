# Week 02 — 방화벽 운영 (nftables) — fw-gui 콘솔 + 침해대응 [W02+W03 통합]

> **본 주차 한 줄 요약**
>
> 우리는 **방화벽을 만드는 엔지니어가 아니라 운영하는 사람** 의 시각으로 nftables 를 배운다.
> fw-gui 콘솔을 중심으로 — 룰 작성, 객체(그룹), NAT, stateful 연결추적, 카운터/로그, SIEM 연동 까지 —
> **공격 상황 7건** 을 직접 막아 보면서, 인프라(방화벽) 로 **공격에 대응** 하는 1차 관문을 익힌다.
> 본 주차는 기존 W02(기본) + W03(NAT) 을 **1주로 통합** 했고, 비운 한 주는 **W03 Windows 엔드포인트
> 운영** 으로 옮겼다 (운영자가 봐야 하는 가시성의 빈틈 — 엔드포인트 — 을 채우기 위해).

---

## 0. 학습 목표

본 주차가 끝나면 운영자(여러분)는 다음을 **콘솔만으로** 한다.

1. fw-gui 콘솔에서 방화벽의 인터페이스/존, 테이블(`inet six_filter`/`ip six_nat`), 룰셋, 객체, conntrack 을 읽는다.
2. 폼으로 룰을 만들고, 그것이 만들어내는 **실제 `nft` 명령** 을 함께 익힌다(콘솔 동작 = nft 명령).
3. 룰 **평가 순서**(top vs bottom, accept 의 단락 효과)와 **rate limit / ct state / 객체 참조** 를 자유롭게 조합한다.
4. **DNAT/SNAT/MASQUERADE** 를 prerouting/postrouting 에 올바르게 배치한다. **HAProxy(L7) 와 방화벽 NAT(L4) 의 역할 분담**을 이해한다.
5. **conntrack** 표를 읽어 stateful 의 의미와 운영 상황(NAT 끊김 4 패턴)을 진단한다.
6. **카운터(packets/bytes)** 와 **GUI 이벤트 로그** 를 **SIEM(Wazuh)** 으로 보낸다.
7. **침해대응 시나리오 7건** (악성 IP / 포트 스캔 / SSH brute / ICMP flood / 화이트리스트 / DNAT 위험 노출 / C2 egress 차단) 을 실제 콘솔에서 만들고 효과를 카운터로 증명한다.
8. **가시성의 한계** 를 안다 — 방화벽은 dmz 내부 엔드포인트 트래픽을 못 본다. 그래서 **엔드포인트 EDR(W03)** 과 함께 본다.

> **본 주차의 시선** — 방화벽 "벤더 엔지니어" 의 시선이 아니라 **"방화벽을 사서 운영하는 사람"** 의
> 시선이다. 모든 동작은 **GUI 가 우선**, 동시에 그 GUI 가 만드는 **명령(nft)** 을 같이 본다.
> 명령을 외울 필요는 없지만 **읽을 줄은 알아야** 운영자다.

---

## 1. 용어 8개 (꼭 알아야 할 것만)

| 용어 | 뜻 | 운영자에게 의미 |
|------|----|----------------|
| nftables | 리눅스 커널의 방화벽 도구 (iptables 후속) | 우리 6v6 방화벽의 엔진 |
| 테이블 / 체인 / 룰 | 룰의 컨테이너 / 트리거 지점 / 매칭+동작 | "룰을 어디에 두는가" 의 단위 |
| input / forward / output | 방화벽 자신에게 / 통과해 / 나가는 트래픽 | 룰 만들 때 가장 먼저 정할 칸 |
| ct state (established/related/new) | 연결의 상태 | stateful 의 핵심. new 만 검사, 응답은 자동 통과 |
| 카운터 (packets/bytes) | 룰이 매칭한 횟수·바이트 | **차단 효과의 증거** (운영자가 매일 본다) |
| named set (객체/Alias) | IP·포트의 재사용 그룹 | "악성 IP 목록 한 곳에서 관리" |
| DNAT / SNAT | 목적지 / 출발지 주소 변환 | DNAT=공개, SNAT=내부 위장 |
| HAProxy | 7계층 reverse proxy (fw 가 같이 돌림) | Host 헤더로 vhost 라우팅. 방화벽 NAT 과 역할 분담 |

> **버려도 되는 깊이**: Netfilter 5 hook 의 hook 우선순위 내부, conntrack helper 모듈 목록,
> iptables-translate 같은 마이그레이션 도구, nft 의 internal data structure — 이런 건 운영자가
> 외울 필요 없다. 매뉴얼이 있다. 본 강의의 시간은 "운영" 에 쓴다.

---

## 2. 방화벽 콘솔(`fw-gui.6v6.lab`) 둘러보기

운영자의 첫 화면은 항상 콘솔이다.

| 메뉴 | 운영자가 매일 보는 것 |
|------|----------------------|
| 📊 대시보드 | 인터페이스·테이블·룰 수·연결 수 (한 눈에 건강 상태) |
| 🔌 인터페이스 | `eth0`(ext, 외부) / `eth1`(pipe, ips 로 가는 통로) — fw 의 양다리 |
| 📜 룰 관리 | 룰 만들기(폼→**nft 명령 미리보기**→적용) + 현재 룰셋 |
| 📦 객체 | **그룹(Alias)** — 악성 IP 묶음, 관리 포트 묶음 |
| 🔁 NAT | DNAT/SNAT 만들기 (six_nat 테이블) |
| 🔗 Stateful | conntrack 테이블 — 살아있는 연결 |
| 📈 로그·활동 | 룰별 카운터, 이벤트 로그 |
| 🛰️ SIEM 연동 | events.log → Wazuh 매니저(10.20.32.100) |
| 🎯 침해대응 훈련 | 시나리오 11건 (이 강의에서 7건 정도 소화) |

> 콘솔의 **변경은 `inet six_filter` / `ip six_nat`** 두 테이블에만 적용된다. Docker 가 쓰는
> `ip nat` 는 콘솔이 보호한다 — 운영자가 무심코 망을 망가뜨리지 않는다.

---

## 3. 네트워크/존, 그리고 가시성의 한계

본 6v6 의 4 존을 다시 본다 (운영자의 관점).

| 존 | 대역 | 무엇이 있나 | fw 의 시야 |
|----|------|-------------|-----------|
| ext | 10.20.30.0/24 | 공격자(10.20.30.202), fw eth0 | fw 가 직접 본다 |
| pipe | 10.20.31.0/24 | fw eth1 ↔ ips eth0 (좁은 통로) | fw 가 본다(통과 트래픽) |
| dmz | 10.20.32.0/24 | ips eth1, **web/WAF**(10.20.32.80), **SIEM**(.100), **Windows 사용자 PC(.60)** | fw **는 dmz 내부 통신은 못 본다** |
| int | 10.20.40.0/24 | 백엔드 앱 (JuiceShop 등) | fw 가 못 본다 |

**가시성의 한계 — 매우 중요**: 직원 PC(Windows 10.20.32.60) 가 같은 dmz 안의 웹서버에 접속하는
트래픽은 **fw 를 거치지 않는다**(같은 구역 스위칭). 즉 fw 는 외부에서 들어오는 트래픽을 다루는
**경계 장비** 다. "내부 PC 가 무엇을 보고 무엇을 했는가" 는 fw 가 못 본다 — 그건 **WAF(웹 요청)** 과
**엔드포인트 EDR(Sysmon/Wazuh)** 의 일이다. 다음 주차 W03 (Windows 엔드포인트 운영) 에서 본격적으로 다룬다.

```mermaid
flowchart LR
  ATK[공격자<br/>10.20.30.202<br/><b>ext</b>]:::ext
  FW[방화벽 fw<br/>eth0:.30.1 / eth1:.31.1<br/>nft + HAProxy<br/><b>경계 장비</b>]:::fw
  IPS[IPS<br/>eth0:.31.2 / eth1:.32.1]:::ips
  WEB[웹/WAF<br/>10.20.32.80<br/><b>dmz</b>]:::svc
  WIN[Windows 사용자 PC<br/>10.20.32.60<br/><b>dmz</b>]:::win
  SIEM[SIEM<br/>10.20.32.100]:::svc
  APP[백엔드 앱<br/>10.20.40.x<br/><b>int</b>]:::int

  ATK -- ext --> FW -- pipe --> IPS -- dmz --> WEB
  WIN -. 직접 .-> WEB
  WEB --> APP
  FW -. events.log .-> SIEM

  classDef ext fill:#fee,stroke:#c33
  classDef fw fill:#fff5d6,stroke:#c80
  classDef ips fill:#e8e8ff,stroke:#55c
  classDef svc fill:#e8f8e8,stroke:#494
  classDef win fill:#e0eef8,stroke:#369
  classDef int fill:#f4e8f8,stroke:#849
```

> 점선 화살표(`WIN -. .-> WEB`) 가 **fw 가 못 보는 트래픽** 이다. 운영자가 머릿속에 늘 그려 둘 그림.

---

## 4. 디렉토리·설정·로그 (운영자가 알아야 할 위치)

| 항목 | 위치 | 운영자가 만지는가 |
|------|------|------------------|
| 명령 | `/usr/sbin/nft` | 거의 콘솔로 대체. 단 `nft list ruleset` 정도는 익숙해질 것 |
| 설정파일(영구) | `/etc/nftables.conf` | 콘솔로 만든 룰을 영구화할 때 (재부팅 후에도 유지) |
| 연결추적 | `/usr/sbin/conntrack` | `conntrack -L` 로 살아있는 연결 보기 |
| 콘솔 이벤트 로그 | `/var/log/nft_edu/events.log` | SIEM 으로 가는 원천 |
| nft native log | 커널 ring buffer (컨테이너에선 파일 미보존) | 그래서 **카운터** 가 운영자의 주된 증거 |

> **두 가지 룰의 집** — 메모리에 올라간 룰(즉시 적용, 재부팅 시 사라짐) vs `/etc/nftables.conf` (영구).
> 콘솔의 "적용" 은 즉시. 운영에선 검증 후 설정파일에도 반영해 재부팅 안전을 확보한다.

---

## 5. 룰 작성 — 폼이 만들어내는 진짜 명령

운영자의 시간은 룰 관리 메뉴에서 가장 많이 쓴다.

### 5.1 체인 3개와 평가 순서

| 체인 | 트래픽 | 룰의 위치를 어떻게 정할까 |
|------|--------|--------------------------|
| `input` | 방화벽 **자신에게** 오는 | 관리 포트(22, 9100) 허용, 외부 직접 접근 차단 |
| `forward` | 방화벽을 **통과해** 내부로 | 차단 룰의 본거지 (대부분의 보안 정책) |
| `output` | 방화벽이 **나가는** | C2 egress 차단 등 (적게 쓰지만 중요) |

룰은 **위에서 아래로** 평가되고 **accept/drop 을 만나면 끝**난다. 그래서 "차단은 top, 일반 허용은
bottom" 이 보통이다. 콘솔의 **위치(top/bottom)** 선택이 이 차이를 만든다.

### 5.2 룰 한 줄을 읽는다

콘솔 폼에 — 체인 `forward`, 출발지 `10.20.30.202`, 동작 `drop`, 위치 `top` → 미리보기:

```
nft insert rule inet six_filter forward ip saddr 10.20.30.202 counter drop
```

각 부분의 의미를 운영자 언어로:

| 토큰 | 의미 |
|------|----|
| `insert` | 체인 **맨 위** 에 넣는다 (위치 top). 가장 먼저 평가됨 |
| `inet six_filter forward` | 우리 정책 테이블의 forward 체인에 |
| `ip saddr 10.20.30.202` | **출발지 IP** 가 이것이면 |
| `counter` | 매칭한 packets/bytes 를 센다 (운영자의 증거) |
| `drop` | 조용히 버린다 (응답 없음) |

> 운영자가 외울 단어 4개: `add/insert rule`, `ip saddr/daddr`, `counter`, `drop/accept/reject`.

### 5.3 더 운영자스러운 룰 패턴 4가지

#### (a) Rate limit — SSH brute force 완화 (가용성 보존)

```
nft insert rule inet six_filter input tcp dport 22 ct state new \
    limit rate over 10/minute counter drop
```

분당 10회를 **초과** 하는 신규 연결만 drop. 정상 사용자는 통과. 22번을 통째로 막는 것보다 백배 낫다.

#### (b) 그룹(객체, Alias) — 악성 IP 묶음

콘솔 **객체** 메뉴에서 IP 그룹 `blocklist` 생성 → 룰에서 `@blocklist` 참조:

```
nft add set inet six_filter blocklist { type ipv4_addr ; }
nft add element inet six_filter blocklist { 10.20.30.202, 10.20.30.250 }
nft insert rule inet six_filter forward ip saddr @blocklist counter drop
```

**왜 좋은가** — CTI 에서 새 악성 IP 가 오면 **룰은 그대로 두고** 그룹에만 추가하면 모든 참조 룰에 즉시
반영된다. 운영 일관성 + 빠른 반응. 룰 100개를 만들지 말고 **그룹 1개를 살찌워라**.

#### (c) stateful — 응답 자동 통과

input/forward 체인 맨 위엔 항상 있는 룰:

```
ct state established,related accept
```

한 번 허용된 연결의 **응답 패킷** 은 자동 통과. 운영자는 룰 작성 시 "신규(new) 연결" 만 신경 쓰면 된다.
새 룰의 매치에 `ct state new` 를 추가하면 더 정확하다.

#### (d) 로그 + 차단 + 카운터 — 침해 증거 보존

```
nft insert rule inet six_filter input ip saddr 10.20.30.202 \
    counter log prefix "EDU-BLOCK: " drop
```

`log prefix` 는 커널 ring buffer 로 가서 컨테이너 환경에선 파일에 안 남지만, **`counter`** 가
운영자의 가장 확실한 증거다. 적용 후 공격을 재현하면 `nft -a list chain ...` 에서 packets 값이 올라간다.

---

## 6. NAT — DNAT / SNAT / MASQUERADE

NAT 은 **주소를 바꿔치기** 한다. 운영자가 자주 하는 세 종류.

### 6.1 DNAT — 내부 서비스를 외부에 공개

콘솔 **NAT** → DNAT, iif `eth0`, tcp dport `8088`, 대상 `10.20.32.80:80` → 미리보기:

```
nft add rule ip six_nat prerouting iifname "eth0" tcp dport 8088 \
    counter dnat to 10.20.32.80:80
```

외부의 `방화벽:8088` → 내부 웹서버(10.20.32.80:80). **prerouting**(라우팅 결정 전)에서 일어난다.
**내부 IP 는 노출되지 않는다.**

### 6.2 SNAT / MASQUERADE — 출발지 위장

내부 호스트가 외부로 나갈 때 출발지 IP 를 방화벽 IP 로 위장(NAT). **postrouting**(라우팅 후)에서.

```
nft add rule ip six_nat postrouting oifname "eth1" ip saddr 10.20.40.0/24 \
    counter snat to 10.20.31.1
```

또는 `masquerade`(자동 SNAT, 인터페이스 IP 사용). MASQUERADE 는 인터페이스 IP 가 동적일 때 쓴다.

### 6.3 prerouting vs postrouting (외우는 법)

> "**어디로 갈지 정하기 전에 목적지(D)를 바꾸고, 다 정한 뒤 출발지(S)를 바꾼다.**" — DNAT=prerouting,
> SNAT/MASQUERADE=postrouting.

### 6.4 HAProxy(L7) ↔ 방화벽 NAT(L4) — 역할 분담

6v6 의 fw 컨테이너는 **HAProxy 도 같이** 돌린다. 둘은 같은 호스트지만 역할이 다르다.

| 도구 | 계층 | 어떻게 라우팅하나 | 예 |
|------|-----|-------------------|-----|
| HAProxy | L7 (HTTP) | **Host 헤더** | `juice.6v6.lab` → web waf backend |
| nft NAT | L4 (TCP/IP) | **포트** | tcp 8088 → 10.20.32.80:80 |

**규칙**: 같은 외부 포트(80/443)에 둘이 동시에 못 붙는다(충돌). 운영 패턴은 — **HTTP 는 HAProxy** 로
호스트 라우팅, **비 HTTP / 다른 포트의 노출** 은 nft DNAT 으로 분담. 흔한 실수는 nft DNAT 으로 80 을
잡아버려 HAProxy 가 못 뜨는 것. **NAT 만들기 전 `ss -ltn` 으로 충돌 확인**.

### 6.5 NAT 는 방화벽이 아니다 (흔한 오해)

**NAT 이 켜졌다고 그 트래픽이 보안적으로 검사된다는 뜻이 아니다.** NAT 은 주소 변환일 뿐, 콘텐츠
검사를 안 한다. NAT 으로 공개한 8088 도 똑같이 **차단 룰** 의 적용 대상이어야 안전하다. (DNAT 을
켰다면 그 대상 IP/포트에 대한 forward 차단 룰을 함께 검토할 것.)

---

## 7. Stateful — conntrack 표 읽기

**Stateful** 메뉴에서 보는 연결 추적 표.

```
proto  state         src                dst                  flags
tcp    ESTABLISHED   10.20.31.1:40428   10.20.32.120:5601    [ASSURED]
```

- `proto` = TCP/UDP/ICMP
- `state` = TCP 상태(NEW/SYN_SENT/ESTABLISHED/TIME_WAIT 등)
- `[ASSURED]` = 양방향 패킷이 오간, "확실한" 연결 (커널이 잘 안 지운다)
- `[UNREPLIED]` = 한쪽 방향만 — SYN flood / NAT 실패 / 응답 누락의 신호

### 7.1 conntrack 으로 진단할 수 있는 NAT 끊김 4 패턴

| 증상 | conntrack 의 신호 | 원인 |
|------|------------------|------|
| 연결은 되는데 응답이 안 옴 | `[UNREPLIED]` 다수 | 응답 경로가 다른 방향(asymmetric routing) — NAT 비대칭 |
| 잠시 후 끊긴다 | `TIME_WAIT` 폭증, 새 연결이 같은 5-tuple 재사용 못함 | 짧은 timeout, 포트 고갈 |
| 일부 클라이언트만 안 됨 | 그 클라이언트만 conntrack 없음 | 룰이 그 출발지 drop |
| 갑자기 모든 새 연결 안 됨 | conntrack table FULL | 용량 초과(`nf_conntrack_max`) |

운영자는 평소에 `Stateful` 메뉴의 **count + 분포** 만 보면 이상을 빠르게 잡는다.

### 7.2 conntrack table 용량 — 6v6 에선 신경 안 써도 되지만

운영망에서는 `nf_conntrack_max` 초과 시 새 연결이 안 만들어진다. **트래픽 폭증 사고의 단골 원인**.
운영 환경에선 모니터링 + sysctl 튜닝이 필요하지만, 본 강의 6v6 규모에선 발생하지 않는다.

---

## 8. 카운터 · 이벤트 로그 · SIEM 연동

### 8.1 카운터 — 운영자의 가장 정직한 증거

**로그·활동** 메뉴에서 룰마다 packets/bytes 가 보인다. 차단 룰의 packets 가 0 → 4 → ... 로 늘면
**그 룰이 실제로 트래픽을 막고 있다** 는 100% 증거다. 어떤 보고서보다 강력하다. **카운터 리셋** 으로
주기적 측정도 가능.

### 8.2 콘솔 이벤트 로그

콘솔이 적용/삭제/리셋한 모든 동작은 `/var/log/nft_edu/events.log` 에 JSON 한 줄씩 남는다 —
**누가 언제 무엇을 바꿨나** 의 감사 자료. 침해 후 "방화벽 설정을 누가 바꿨는지" 가 핵심 추적 단서가 된다.

### 8.3 SIEM(Wazuh) 연동

**SIEM 연동** 메뉴 → "연동 켜기" → fw 의 Wazuh 에이전트가 events.log 를 tail → 매니저(10.20.32.100)
로 전송. 그러면 SIEM 한 화면에서 **방화벽 변경 이력 + IPS alert + WAF 차단 + Windows Sysmon 이벤트**
를 시간순으로 함께 본다 — **인프라 전체로 공격에 대응** 하는 출발점.

> SIEM 연동된 다음부터 운영자의 일상은 콘솔보다 **Wazuh 대시보드** 가 중심이 된다. 방화벽 콘솔은
> "변경" 의 도구, SIEM 은 "관제" 의 도구.

---

## 9. 침해대응 시나리오 7건 (R/B/P)

**침해대응 훈련** 메뉴에 11건이 있다. 본 강의에선 핵심 7건을 직접 풀어 본다. 각 시나리오는
**Red(공격 재현) → Blue(룰 작성·적용) → Purple(검증·증거 보존)** 패턴을 따른다.

### 9.1 fw-s01 — 악성 IP 즉시 차단 (수동 대응)

- Red: `for i in $(seq 1 50); do curl -s -m1 http://10.20.30.1/ >/dev/null; done`
- Blue: forward 체인 top 에 `ip saddr 10.20.30.202 drop`.
- Purple: 카운터 packets ≥ 50 + 콘솔 검증 ✔.
- 교훈: 단일 IP 차단은 가장 빠른 1차 대응. 단 출발지가 분산되면 무력해진다 → fw-s11 (객체)로 진화.

### 9.2 fw-s02 — 닫혀야 할 관리 포트 보호

- Red: `nc -vz 10.20.30.1 9999`.
- Blue: input 체인에 `tcp dport 9999 drop`.
- Purple: nc 응답 timeout + counter 증가.
- 교훈: 최소권한. "쓰지 않는 포트는 닫는다"가 보안의 기본.

### 9.3 fw-s03 — SSH brute force 완화

- Red: `for i in $(seq 1 60); do nc -w1 10.20.30.1 22 </dev/null; done`
- Blue: `tcp dport 22 ct state new limit rate over 10/minute drop`.
- Purple: 정상 SSH 는 통과, 폭주만 drop (carrier-grade 패턴).
- 교훈: 가용성 보존형 방어 — 22 를 통째로 막지 않는다.

### 9.4 fw-s04 — ICMP flood 제한

- Red: `ping -f -c 500 10.20.30.1` (flood ping).
- Blue: `ip protocol icmp limit rate over 5/second drop`.
- Purple: 정상 ping 통과, flood drop.
- 교훈: 진단(ping) 가용성을 해치지 않는 방어.

### 9.5 fw-s07 — 화이트리스트 (관리망만 허용)

- Red: 외부에서 `nc -vz 10.20.30.1 9100`.
- Blue: input top 에 `ip saddr 10.20.31.0/24 tcp dport 9100 accept`, 그 아래 `tcp dport 9100 drop`.
- Purple: 관리망(pipe)에서만 9100 도달, 외부는 막힘.
- 교훈: **허용 먼저, 거부 나중** — 순서가 바뀌면 관리망도 막힌다. 화이트리스트 설계의 정석.

### 9.6 fw-s08 — DNAT 으로 안전한 공개

- Red: 공격자가 `방화벽:8088` 접속 시도 (적용 전엔 closed).
- Blue: NAT 메뉴에서 DNAT 8088 → 10.20.32.80:80.
- Purple: 접속 OK (200), 내부 IP 미노출.
- 교훈: NAT 으로 공개 = **내부 주소 은닉** + 외부 노출 표면 제어. 단 NAT 만으로는 보안 X — 차단 정책과 함께.

### 9.7 fw-s11 — 객체(그룹)로 다중 차단 + CTI 운영

- Red: CTI 에서 악성 IP 5개 식별, 한 번에 차단 필요.
- Blue: 객체 메뉴에서 `blocklist` 그룹 생성 → IP 5개 등록 → forward 룰 `@blocklist drop` 1줄.
- Purple: 5 IP 모두 차단, 새 악성 IP 발견 시 그룹에만 추가 → 룰 무수정 즉시 적용.
- 교훈: **운영 일관성 + 빠른 반응**. 룰의 수를 늘리지 말고 **객체** 로 데이터를 늘려라.

### 추가 (egress) — C2 콜백 차단 (fw-s06)

내부 호스트가 알려진 C2 IP 로 나가는 콜백을 차단:
- Blue: output 체인 top 에 `ip daddr <C2 IP> drop`.
- 교훈: **egress filtering** — 침해 후 데이터 유출/명령 수신을 끊는 마지막 보루. 흔히 잊는다.

---

## 10. 운영 트러블슈팅 — 자주 보는 4 가지

| 증상 | 확인 | 처치 |
|------|------|------|
| "차단했는데 통과한다" | 카운터 = 0 → 룰이 안 평가됨 (위에 accept 가 먼저) | **위치 top** 또는 위 accept 제거/수정 |
| "정상 사용자가 막혔다" | 카운터 = 정상 IP, 응답코드 timeout | 룰의 매칭 범위 좁히기 (출발지 CIDR 정확히) |
| "NAT 가 안 먹는다" | conntrack `[UNREPLIED]` | 응답 경로 / DNAT 대상 도달성 / 충돌 포트 |
| "방화벽이 갑자기 모든 새 연결 거부" | dmesg `nf_conntrack: table full` | `nf_conntrack_max` 증가 (운영에서) |

---

## 11. 핵심 정리 (8 줄)

1. 운영자는 **콘솔 + nft 명령 읽기** 만으로 충분하다. 엔지니어가 아니다.
2. **체인은 input/forward/output 3개**, 평가는 **위에서 아래**, accept/drop 에서 끝난다.
3. 자주 쓰는 패턴: **stateful(established,related accept) + rate limit + 객체(@group)**.
4. **DNAT=prerouting**, **SNAT/MASQUERADE=postrouting**. HAProxy(L7) 와 nft NAT(L4) 의 역할 분담.
5. **카운터** 가 차단 효과의 정직한 증거. 콘솔 이벤트 로그가 감사 자료.
6. **SIEM(Wazuh) 연동** 으로 방화벽이 단독이 아니라 인프라 전체의 일부가 된다.
7. 침해대응은 **R/B/P** 1 cycle: 공격 재현 → 룰 → 카운터 증거.
8. 방화벽은 **경계** 만 본다 — dmz 내부 엔드포인트(Windows)는 W03 의 **EDR** 이 본다.

---

## 12. 과제

1. 시나리오 fw-s01 / s03 / s07 / s08 / s11 다섯 건의 콘솔 검증 화면(✔ 통과) 캡처를 제출하라.
2. fw-s07 (화이트리스트) 에서 "허용을 아래에 둘 때" 어떻게 망가지는지 시연하고 1문단 설명하라.
3. fw-s08 DNAT 룰을 만들고 적용 전·후의 `ss -ltn` / 공격자 `curl` 결과를 비교하라.
4. SIEM 연동을 켠 뒤 룰을 한 건 적용·삭제하고 Wazuh 대시보드에 그 이벤트가 도달했는지 확인한 화면을 제출하라.
5. (생각) 방화벽이 **못 보는 트래픽 3가지** 를 우리 6v6 구조에서 구체적으로 들고, 각각을 누가 봐 주는지 쓰라.

---

## 13. 다음 주차 (W03) 예고 — Windows 엔드포인트 운영·침해대응

방화벽은 경계의 문지기다. 안에 있는 **사용자 PC(엔드포인트)** 가 무엇을 보고 무엇을 실행하는지는
못 본다. 다음 주차는 우리 6v6 에 새로 들어온 **Windows 11 사용자 PC(10.20.32.60)** 를 **victim 직원
PC** 와 **analyst 보안담당 PC** 두 페르소나로 운영하며, **Sysmon + Wazuh 에이전트 + Windows 보안로그**
를 SIEM 으로 흘려보내 분석한다. 방화벽으로 못 막은 일을 엔드포인트가 잡는다.
