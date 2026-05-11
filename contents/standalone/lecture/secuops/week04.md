# Week 04 — Suricata IDS / IPS (1) — 구성과 운영

> 본 주차의 학습 대상은 **6v6-ips** 컨테이너의 **Suricata 6.0.4**. fw 가 L3/L4 통제를
> 담당했다면 (W02–W03), ips 는 같은 패킷을 페이로드 단위로 검사한다. 학생은 Suricata
> 의 데몬 가동 상태 / af-packet 캡처 / 룰셋 / eve.json / suricatasc 5 영역을 단계별
> 검증하고, 새 alert 룰 1개를 추가하여 직접 트리거한다.

## 학습 목표

학습자는 본 주차 종료 시 다음을 수행할 수 있어야 한다.

1. Suricata 의 4 핵심 모듈 (capture / decode / detect / output) 의 데이터 흐름을 화이트
   보드에 그릴 수 있다.
2. af-packet 의 promiscuous capture / clustering / runmode (autofp / workers / single)
   세 옵션 차이를 설명한다.
3. ETOpen 룰셋과 사용자 정의 룰의 위치·우선순위·suricata-update 관리 방법을 이해한다.
4. `eve.json` 의 event_type 별 (alert / http / dns / flow / tls / fileinfo / stats) 의미
   를 구분하고 jq 로 분석한다.
5. `suricatasc -c <command>` 로 데몬 메트릭을 실시간 조회한다.
6. 새 alert 룰을 작성·로드·트리거하여 alert 발생부터 jq 분석까지 한 사이클 수행한다.

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용                                                                | 유형     |
|-----------|---------------------------------------------------------------------|----------|
| 0:00–0:25 | 이론 — Suricata = "오픈소스 IDS/IPS/NSM" + 동료 (Snort/Zeek/PaloAlto) | 강의     |
| 0:25–0:55 | 이론 — 4 모듈 + 데이터 흐름 (capture → decode → detect → output)     | 강의     |
| 0:55–1:05 | 휴식                                                                 | —        |
| 1:05–1:30 | 6v6-ips 의 실제 구성 (af-packet 두 NIC + autofp + eve.json)         | 강의/토론|
| 1:30–2:00 | 실습 1, 2 — 데몬 상태 + suricata.yaml 핵심 키 분석                  | 실습     |
| 2:00–2:30 | 실습 3, 4 — eve.json 의 event_type 분포 + alert 추출                | 실습     |
| 2:30–2:40 | 휴식                                                                 | —        |
| 2:40–3:10 | 실습 5, 6 — suricatasc 메트릭 + 새 alert 룰 작성·트리거             | 실습     |
| 3:10–3:30 | 실습 7 — suricata-update + ETOpen 룰셋 관리                          | 실습     |
| 3:30–3:40 | 정리 + W05 (룰 작성 심화) 예고                                       | 정리     |

---

## 1. Suricata 란?

**오픈소스 NSM (Network Security Monitoring) 엔진**. 2009년 OISF (Open Information
Security Foundation) 가 Snort 를 기반으로 분기하여 멀티스레드 + 모던 프로토콜 디코더
+ JSON event 를 갖추고 출시. 2026년 현재 v7.x 가 stable, 본 lab 의 Ubuntu 22.04 패키지
는 6.0.4.

### 1.1 IDS 와 IPS 두 모드

| 모드 | 동작 | 6v6 구성 |
|------|------|----------|
| IDS  | passive sniff → alert (트래픽에 개입 X) | 6v6-ips 의 기본 모드 (af-packet) |
| IPS  | NFQUEUE 또는 af-packet inline → drop 가능 | 본 lab 에서는 사용 안 함 |

운영 환경의 표준은 IDS + 별도 firewall 로 자동 차단 (Wazuh Active Response 등) 분리.
Suricata 자체 IPS 모드는 throughput 영향이 크다.

### 1.2 4 모듈

```
[NIC]
   │
   ▼
┌─────────────┐
│  capture    │  af-packet / pcap / NFQUEUE
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  decode     │  Ethernet → IP → TCP/UDP → HTTP/TLS/DNS/SSH/SMB ...
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  detect     │  ETOpen 룰 70,000+ × packet 매칭 (multi-threaded)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  output     │  eve.json, alert.fast, pcap, stats.log, unified2, ...
└─────────────┘
```

각 단계가 thread pool 로 병렬화. capture 의 패킷이 detect 에 도달하기 전 decoder 가
프로토콜 식별 (HTTP request / TLS handshake / DNS query) → http/tls/dns event 가 alert
와 별도로 생성된다.

### 1.3 동료 도구 비교

| 도구 | 라이선스 | 주력 | 6v6 사용 |
|------|----------|------|---------|
| Suricata | GPL  | IDS/IPS + NSM | ✓ ips |
| Snort 3  | GPL  | IDS/IPS (legacy 룰 호환) | × |
| Zeek (Bro) | BSD | NSM (스크립트 기반) | × (W14 에서 비교) |
| PaloAlto / Cisco FTD | 상용 | NGFW + IPS | × |

Zeek 은 "패킷이 무엇인가" (메타데이터 추출) 에 강점, Suricata 는 "패킷이 악성인가"
(시그니처 매칭) 에 강점. 둘이 보완 관계 → production 운영에서 동시에 깔기도 한다.

---

## 2. 6v6-ips 의 실제 구성

### 2.1 컨테이너 + 네트워크

```
                    ┌─── pipe (10.20.31.0/24)
                    │      eth0  10.20.31.2
   6v6-ips  ◀──────┤
   (Suricata)       │      eth1  10.20.32.1
                    └─── dmz (10.20.32.0/24)
```

ips 는 두 NIC 모두에서 promisc capture. fw → pipe → ips → dmz → web/siem 의 모든 트래픽
이 ips 의 두 NIC 를 통과한다 (양쪽 모두 forward path 의 hop).

### 2.2 데몬 시작 옵션 (entrypoint.sh)

```
suricata -i eth1 -i eth0 -c /etc/suricata/suricata.yaml \
    --runmode autofp -l /var/log/suricata
```

- `-i eth0 -i eth1` : 두 NIC 동시 sniff (af-packet thread group 자동 분리)
- `-c` : config 파일
- `--runmode autofp` : auto flow-pinned (한 flow 가 한 thread 에 고정 → cache 친화 + lock-free)
- `-l` : 로그 디렉토리 (`eve.json`, `suricata.log`, `stats.log`)

다른 runmode:
- `workers` : 모든 thread 가 packet pool 공유 (high-throughput 우선)
- `single` : single thread 디버그 모드

### 2.3 룰셋

```
/var/lib/suricata/rules/
├── suricata.rules     # ETOpen 통합 룰셋 (suricata-update 가 빌드)
├── classification.config
├── app-layer-events.rules
├── decoder-events.rules
├── dns-events.rules
├── http-events.rules
├── tls-events.rules
└── ...
```

- **ETOpen** (Emerging Threats Open) : 무료 오픈 룰셋. 70,000+ 룰. 매일 자동 갱신.
- **사용자 정의 룰** : `/etc/suricata/rules/local.rules` 에 작성 후 `rule-files:` 에 등록.

### 2.4 eve.json (메인 분석 대상)

```
{
  "timestamp": "2026-05-11T11:06:44.421882+0000",
  "flow_id": 1284584860047176,
  "in_iface": "eth0",
  "event_type": "http",
  "src_ip": "10.20.30.202",
  "src_port": 43210,
  "dest_ip": "10.20.32.1",
  "dest_port": 80,
  "http": {
    "hostname": "juice.6v6.lab",
    "url": "/",
    "http_user_agent": "curl/8.5",
    "http_method": "GET",
    "protocol": "HTTP/1.1",
    "status": 200
  }
}
```

한 줄 = 한 event. `event_type` 가 7+ 종류 (alert / http / dns / flow / tls / fileinfo /
stats / ssh / smtp / smb / quic / dnp3 등).

---

## 3. 4 핵심 명령

### 3.1 데몬 가동 상태

```
pgrep -a Suricata
ps -ef | grep Suricata
suricatasc -c version
suricatasc -c uptime
```

### 3.2 eve.json 분석 (jq)

```
# 최근 100 event 의 type 분포
tail -100 /var/log/suricata/eve.json | jq -r .event_type | sort | uniq -c | sort -rn

# alert 만 추출
grep '"event_type":"alert"' /var/log/suricata/eve.json | jq '{ts:.timestamp,sig:.alert.signature,sev:.alert.severity}'

# HTTP request 의 hostname 별 빈도
grep '"event_type":"http"' /var/log/suricata/eve.json | jq -r .http.hostname | sort | uniq -c | sort -rn

# DNS 쿼리 의 query name
grep '"event_type":"dns"' /var/log/suricata/eve.json | jq '{q:.dns.rrname,t:.dns.type}'
```

### 3.3 통계 (suricatasc / stats.log)

```
suricatasc -c uptime                       # 데몬 시작 후 초
suricatasc -c dump-counters | jq '.message | with_entries(select(.value>0)) | to_entries[:20]'
cat /var/log/suricata/stats.log | tail -30
```

### 3.4 룰셋 관리

```
suricata-update list-sources               # 가용 룰 소스
suricata-update list-enabled-sources       # 활성 소스
sudo suricata-update                       # 룰셋 다운로드 + 빌드
sudo suricatasc -c reload-rules            # 데몬에 reload signal
```

---

## 4. 새 alert 룰 작성

local.rules 에 한 줄 룰 작성 → reload → 트리거 → eve.json 에 alert 출현 확인.

### 4.1 룰 문법

```
alert <proto> <src> <sport> -> <dst> <dport> ( msg:"..." ; content:"..." ; sid:<int> ; rev:<int> ; )
```

핵심 키워드:
- `alert` : 액션 (alert / drop / reject / pass)
- `tcp / udp / icmp / http / dns / tls / ssh` : 프로토콜
- `$EXTERNAL_NET / any` : 출발지
- `$HOME_NET / any` : 목적지
- `msg:"..."` : 사람이 읽는 시그니처 이름
- `content:"..."` : 페이로드 매칭
- `sid:<int>` : signature ID (사용자 정의 룰은 1000000+)
- `rev:<int>` : revision

### 4.2 예시 — User-Agent 가 "curl" 인 HTTP 요청에 alert

```
alert http any any -> $HOME_NET any (msg:"6v6 detected curl UA"; http.user_agent; content:"curl"; sid:9000001; rev:1;)
```

이 룰을 `/etc/suricata/rules/local.rules` 에 추가하고 `rule-files:` 에 등록 후 reload.

### 4.3 트리거

```
ssh 6v6-attacker 'curl -s -o /dev/null -A "curl/8.5" http://juice.6v6.lab/'
# 또는 fw 의 80 으로 직접
ssh 6v6-attacker 'curl -s -o /dev/null -A "curl/8.5" -H "Host: juice.6v6.lab" http://10.20.30.1/'
```

3초 후 eve.json 에 alert 출현:

```
ssh 6v6-ips 'sudo tail -50 /var/log/suricata/eve.json | grep -m1 sid.:9000001 | jq'
```

---

## 5. ETOpen 룰셋 관리

ETOpen 은 매일 갱신. 운영 환경은 cron 으로 자동 update + reload.

```
# /etc/cron.daily/suricata-update
#!/bin/bash
suricata-update --no-test
suricatasc -c reload-rules
```

ETOpen 의 룰 카테고리 (top 10):
- ET SCAN  : 포트 스캐닝, OS detect, dirb 등
- ET WEB_SERVER : 웹서버 공격 (PHP/Apache/Nginx exploit)
- ET WEB_CLIENT : 악성 JS, drive-by
- ET TROJAN : 알려진 트로이목마 C2 통신
- ET POLICY : 정책 위반 (P2P, Bittorrent, Tor)
- ET INFO : 정보성 (low-severity)
- ET MALWARE : 모바일/크로스 플랫폼 악성코드
- ET CURRENT_EVENTS : 최신 캠페인 (단기 룰)
- ET DNS : 악성 도메인 쿼리
- ET TLS : TLS handshake anomaly

`sid` 의 prefix 로 카테고리 분류 가능 (예: ET SCAN 룰은 2000xxx, ET WEB 은 2010xxx).

---

## 6. 용어 해설

| 용어 | 영문 | 설명 |
|------|------|------|
| **af-packet** | Linux Layer 2 capture | 커널의 promiscuous capture 방식 (libpcap 후속) |
| **runmode** | — | Suricata 의 thread 모델 (autofp / workers / single) |
| **flow** | — | 한 conn (5-tuple) 의 양방향 패킷 묶음 |
| **flow_id** | — | flow 의 고유 ID (eve.json 의 모든 event 가 같은 flow_id 공유) |
| **app-layer** | — | application layer 디코더 (HTTP/TLS/DNS/SSH/SMB...) |
| **eve.json** | EVE | Extensible Event Format (JSON 기반 표준) |
| **sid** | Signature ID | 룰의 고유 정수 |
| **rev** | revision | 룰 버전 |
| **ETOpen** | Emerging Threats Open | 무료 오픈 룰셋 (제공: Proofpoint) |
| **ETPro** | Emerging Threats Pro | 상용 룰셋 (라이선스) |
| **NSM** | Network Security Monitoring | "탐지" 보다 "관측" 에 중점 — Zeek 의 슬로건 |
| **detect engine** | — | Suricata 의 룰 매칭 코어 (multi-pattern matcher, hyperscan) |
| **hyperscan** | — | Intel 의 SIMD 기반 multi-pattern 매처 |
| **classification.config** | — | 룰의 클래스 (대분류) 와 priority 매핑 |
| **threshold.config** | — | 룰별 alert rate-limit (예: 10초에 1건만) |

---

## 7. 실습 시나리오 1~7

### 실습 1 — 데몬 가동 상태

```
ssh 6v6-ips 'pgrep -a Suricata'
ssh 6v6-ips 'sudo suricatasc -c version'
ssh 6v6-ips 'sudo suricatasc -c uptime'
```

### 실습 2 — suricata.yaml 핵심 키 분석

```
ssh 6v6-ips 'sudo grep -A5 "af-packet:" /etc/suricata/suricata.yaml | head -20'
ssh 6v6-ips 'sudo grep -E "default-rule-path|rule-files:" /etc/suricata/suricata.yaml'
ssh 6v6-ips 'sudo grep -A3 "outputs:" /etc/suricata/suricata.yaml | head -10'
```

### 실습 3 — eve.json event_type 분포

```
ssh 6v6-ips 'sudo tail -200 /var/log/suricata/eve.json | jq -r .event_type | sort | uniq -c | sort -rn'
```

### 실습 4 — HTTP event 의 hostname 분석

```
ssh 6v6-ips 'sudo grep ''"event_type":"http"'' /var/log/suricata/eve.json | jq -r .http.hostname 2>/dev/null | sort | uniq -c | sort -rn | head'
```

### 실습 5 — suricatasc 메트릭

```
ssh 6v6-ips 'sudo suricatasc -c dump-counters 2>&1 | jq ".message" | head -40'
ssh 6v6-ips 'sudo cat /var/log/suricata/stats.log | tail -50'
```

### 실습 6 — 새 alert 룰 작성·트리거

```
# 룰 추가
ssh 6v6-ips 'echo ''alert http any any -> any any (msg:"6v6 curl UA detected"; http.user_agent; content:"curl"; sid:9000001; rev:1;)'' | sudo tee -a /etc/suricata/rules/local.rules'

# yaml 의 rule-files: 에 local.rules 추가 (이미 있으면 생략)
ssh 6v6-ips 'sudo grep "local.rules" /etc/suricata/suricata.yaml || sudo sed -i ''/rule-files:/a\  - local.rules'' /etc/suricata/suricata.yaml'

# reload
ssh 6v6-ips 'sudo suricatasc -c reload-rules'

# 트리거
ssh 6v6-attacker 'curl -s -o /dev/null -A "curl/8.5" -H "Host: juice.6v6.lab" http://10.20.30.1/'
sleep 3

# alert 확인
ssh 6v6-ips 'sudo tail -100 /var/log/suricata/eve.json | grep "sid.:9000001" | jq'
```

### 실습 7 — suricata-update + ETOpen 룰셋 관리

```
ssh 6v6-ips 'sudo suricata-update list-sources 2>&1 | head -10'
ssh 6v6-ips 'sudo suricata-update list-enabled-sources 2>&1'
# (실행은 시간 소요, 시연으로 생략 가능)
# ssh 6v6-ips 'sudo suricata-update --no-test'
```

---

## 8. 과제

### A. 룰 작성 (필수)

다음 3 alert 룰을 local.rules 에 작성하여 각각 트리거 확인. 한 줄 룰 + 트리거 curl
+ alert eve.json 의 jq 결과 첨부.

1. User-Agent 가 "sqlmap" 인 HTTP 요청 → alert
2. URL path 에 "/admin" 이 포함된 HTTP 요청 → alert
3. ICMP echo-request 가 10초에 5번 초과 → alert (threshold.config)

### B. eve.json 분석 (필수)

지난 1시간의 eve.json 을 분석하여 다음 통계 제출:

- 총 event 수 + event_type 별 분포
- 가장 자주 나오는 hostname (top 5)
- 가장 자주 나오는 alert.signature (top 5)
- flow 의 src_ip 별 packet count top 5

### C. ETOpen 룰 분석 (심화)

ETOpen 룰셋 1개 카테고리 (예: ET SCAN) 선택. 본 lab 환경에서 가장 자주 매치되는
룰 5개 + 각 룰의 의도 + 매치 packet 의 페이로드 일부 분석.

---

## 9. 평가 기준

| 항목 | 비중 |
|------|------|
| 룰 작성 (A) | 40% |
| eve.json 분석 (B) | 35% |
| ETOpen 룰 분석 (C) | 25% |

---

## 10. W05 (룰 작성 심화) 예고

- pcre / fast_pattern / hyperscan 사용
- threshold.config 로 alert rate-limit
- 룰의 false-positive 감소 기법
- production 환경의 룰셋 튜닝 절차
