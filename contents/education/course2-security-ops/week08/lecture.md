# Week 08: 중간고사 — 방화벽 + IPS 구성 실기

## 학습 목표

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 시험 개요

- **유형**: 실기 시험 (hands-on practical exam)
- **시간**: 90분
- **범위**: Week 02~07 (nftables, Suricata IPS, Apache+ModSecurity WAF)
- **환경**: secu(10.20.30.1), web(10.20.30.80)
- **배점**: 총 100점

---

## 시험 환경 접속 정보

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| secu | 10.20.30.1 | 방화벽 + IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | WAF + 웹 앱 | `ssh ccc@10.20.30.80` |

---

## Part 1: nftables 방화벽 구성 (40점)

### 문제 1-1: 기본 방화벽 구성 (20점)

secu 서버에 다음 조건의 방화벽을 구성하라.

**테이블 이름**: `inet exam_filter`

**요구사항:**

1. (4점) 기본 정책: INPUT=drop, FORWARD=drop, OUTPUT=accept
2. (4점) 수립된 연결(established, related) 허용, invalid 패킷 차단
3. (2점) 루프백 인터페이스(lo) 허용
4. (4점) 허용 서비스:
   - SSH (22/tcp)
   - HTTP (80/tcp)
   - HTTPS (443/tcp)
   - ICMP ping
5. (3점) 내부 네트워크(10.20.30.0/24)에서만 8000/tcp 허용
6. (3점) 차단되는 패킷에 `[EXAM-DROP]` prefix로 로깅

**정답 예시:**

> **실습 목적**: 중간고사로 방화벽과 IPS 구성을 시간 내에 직접 수행하여 실무 역량을 검증한다
>
> **배우는 것**: nftables 규칙 작성과 Suricata 룰 구성을 시험 환경에서 독립적으로 완수하는 능력을 평가한다
>
> **결과 해석**: 요구사항대로 트래픽이 허용/차단되고, IPS 알림이 정상 발생하면 구성이 올바른 것이다
>
> **실전 활용**: 보안 장비 긴급 구성은 실무에서 보안 사고 대응 시 시간 압박 속에 수행해야 하는 핵심 기술이다

```bash
ssh ccc@10.20.30.1  # 비밀번호 자동입력 SSH

# 테이블 및 체인 생성
echo 1 | sudo -S nft add table inet exam_filter

echo 1 | sudo -S nft add chain inet exam_filter input \
  '{ type filter hook input priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet exam_filter forward \
  '{ type filter hook forward priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet exam_filter output \
  '{ type filter hook output priority 0; policy accept; }'

# conntrack
echo 1 | sudo -S nft add rule inet exam_filter input ct state established,related accept
echo 1 | sudo -S nft add rule inet exam_filter input ct state invalid drop

# 루프백
echo 1 | sudo -S nft add rule inet exam_filter input iif lo accept

# 허용 서비스
echo 1 | sudo -S nft add rule inet exam_filter input tcp dport 22 accept
echo 1 | sudo -S nft add rule inet exam_filter input tcp dport { 80, 443 } accept
echo 1 | sudo -S nft add rule inet exam_filter input icmp type echo-request accept

# 내부 네트워크에서만 8000
echo 1 | sudo -S nft add rule inet exam_filter input \
  ip saddr 10.20.30.0/24 tcp dport 8000 accept         # IP 주소 조회

# 차단 로깅
echo 1 | sudo -S nft add rule inet exam_filter input \
  log prefix "[EXAM-DROP] " level warn
```

**검증:**

```bash
# 룰셋 확인
echo 1 | sudo -S nft list table inet exam_filter
echo '---'
# 외부에서 8000 차단 검증 (10.20.30.0/24 외부)
curl -s -o /dev/null --max-time 2 -w "외부→8000: %{http_code}\n" http://10.20.30.1:8000/ || echo "외부→8000: 차단됨 (정상)"
# SSH 연결 유지 확인
echo 1 | sudo -S ss -tlnp | grep ':22 '
```

**예상 출력**:
```
table inet exam_filter {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        ct state invalid drop
        iif "lo" accept
        tcp dport 22 accept
        tcp dport { 80, 443 } accept
        icmp type echo-request accept
        ip saddr 10.20.30.0/24 tcp dport 8000 accept
        log prefix "[EXAM-DROP] " level warn
    }
    ...
}
---
외부→8000: 차단됨 (정상)
LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=...))
```

> **해석 — 채점 4 항목 검증**:
> - **policy drop** = 기본 차단 = 화이트리스트 방식 (4점).
> - **ct state established,related accept + invalid drop** = 양호 conntrack 패턴 (4점).
> - **tcp dport { 80, 443 } accept** = anonymous set 사용 = nft 모던 syntax (4점).
> - **`ip saddr 10.20.30.0/24 tcp dport 8000`** = 내부 네트워크만 8000 허용 (3점).
> - **log prefix "[EXAM-DROP] "** = drop 로그 = `journalctl -k | grep EXAM-DROP` 으로 확인 가능 (3점).
> - SSH 연결 유지 = 첫 룰에 SSH 허용 X 였다면 즉시 끊김 → **시험 fail**.

---

### 문제 1-2: NAT 및 포트 포워딩 (20점)

secu 서버에 다음 NAT 설정을 구성하라.

**테이블 이름**: `inet exam_nat`

**요구사항:**

1. (6점) 내부 네트워크(10.20.30.0/24) → 외부: masquerade
2. (8점) 외부에서 secu:8080 → web(10.20.30.80):80 포트 포워딩
3. (6점) forward 체인에서 포워딩 트래픽 허용:
   - 10.20.30.0/24에서 나가는 트래픽 허용
   - 수립된 연결의 응답 허용

**정답 예시:**

```bash
# NAT 테이블
echo 1 | sudo -S nft add table inet exam_nat

# prerouting (DNAT)
echo 1 | sudo -S nft add chain inet exam_nat prerouting \
  '{ type nat hook prerouting priority -100; policy accept; }'

# postrouting (SNAT)
echo 1 | sudo -S nft add chain inet exam_nat postrouting \
  '{ type nat hook postrouting priority 100; policy accept; }'

# masquerade
echo 1 | sudo -S nft add rule inet exam_nat postrouting \
  ip saddr 10.20.30.0/24 masquerade                    # IP 주소 조회

# 포트 포워딩
echo 1 | sudo -S nft add rule inet exam_nat prerouting \
  tcp dport 8080 dnat to 10.20.30.80:80

# forward 허용 (exam_filter 테이블에 추가)
echo 1 | sudo -S nft add rule inet exam_filter forward \
  ct state established,related accept
echo 1 | sudo -S nft add rule inet exam_filter forward \
  ip saddr 10.20.30.0/24 accept                        # IP 주소 조회

# IP 포워딩 활성화
echo 1 | sudo -S sysctl -w net.ipv4.ip_forward=1
```

### 1-2-1 NAT 검증 — DNAT/SNAT/forwarding 동작 확인

```bash
# 1. NAT 룰 적재 확인
echo 1 | sudo -S nft list table inet exam_nat
# 2. ip_forward 활성 확인
sysctl net.ipv4.ip_forward
# 3. DNAT 동작 — 외부에서 secu:8080 호출 → web:80 응답 받기
curl -s -o /dev/null --max-time 3 -w "DNAT(8080→web:80): HTTP=%{http_code} time=%{time_total}s\n" http://10.20.30.1:8080/
# 4. SNAT 검증 — web 서버 access.log 의 src IP = secu(10.20.30.1) 인지
ssh ccc@10.20.30.80 "tail -1 /var/log/apache2/access.log" | awk '{print "web 본 src IP:", $1}'
```

**예상 출력**:
```
table inet exam_nat {
    chain prerouting { type nat hook prerouting priority -100; policy accept; tcp dport 8080 dnat to 10.20.30.80:80 }
    chain postrouting { type nat hook postrouting priority 100; policy accept; ip saddr 10.20.30.0/24 masquerade }
}
net.ipv4.ip_forward = 1
DNAT(8080→web:80): HTTP=200 time=0.034s
web 본 src IP: 10.20.30.1
```

> **해석 — 채점 4 항목 검증**:
> - **net.ipv4.ip_forward = 1** = 커널 forwarding 활성 = NAT 동작 전제 (6점 중 일부).
> - **DNAT HTTP=200** = `secu:8080` → `web:80` 패킷 포워딩 성공 = `tcp dport 8080 dnat to 10.20.30.80:80` 룰 동작 (8점).
> - **web access.log src=10.20.30.1** = masquerade 가 src IP 를 secu 의 IP 로 변환 = SNAT 정상 (6점).
> - **만약 src=원본 외부 IP** = masquerade 미동작 = NAT 룰 적재 실패 → 시험 감점.
> - 추가 검증: `conntrack -L | grep dnat` 으로 NAT translation entry 확인 가능.

---

## Part 2: Suricata IPS 룰 (35점)

### 문제 2-1: 탐지 룰 작성 (20점)

`/etc/suricata/rules/local.rules`에 다음 공격을 탐지하는 룰을 작성하라.

1. (5점) HTTP URI에서 `../` 패턴 탐지 (디렉터리 트래버설)
2. (5점) HTTP URI에서 `<script` 패턴 탐지 (XSS)
3. (5점) HTTP User-Agent에 `nikto` 또는 `sqlmap` 포함 시 탐지
4. (5점) SSH(22번 포트)에 60초 내 10회 이상 연결 시도 탐지

**정답 예시:**

```bash
ssh ccc@10.20.30.1  # 비밀번호 자동입력 SSH

echo 1 | sudo -S tee /etc/suricata/rules/local.rules << 'EOF'
# 1. 디렉터리 트래버설
alert http $HOME_NET any -> any any (msg:"EXAM - Directory Traversal"; flow:to_server,established; http.uri; content:"../"; classtype:web-application-attack; sid:9100001; rev:1;)

# 2. XSS
alert http $HOME_NET any -> any any (msg:"EXAM - XSS script tag"; flow:to_server,established; http.uri; content:"<script"; nocase; classtype:web-application-attack; sid:9100002; rev:1;)

# 3. 스캐너 탐지
alert http any any -> $HOME_NET any (msg:"EXAM - Scanner detected (nikto)"; flow:to_server,established; http.user_agent; content:"nikto"; nocase; classtype:web-application-attack; sid:9100003; rev:1;)
alert http any any -> $HOME_NET any (msg:"EXAM - Scanner detected (sqlmap)"; flow:to_server,established; http.user_agent; content:"sqlmap"; nocase; classtype:web-application-attack; sid:9100004; rev:1;)

# 4. SSH 브루트포스
alert tcp any any -> $HOME_NET 22 (msg:"EXAM - SSH brute force"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 10, seconds 60; classtype:attempted-admin; sid:9100005; rev:1;)
EOF
```

### 문제 2-2: 룰 검증 및 테스트 (15점)

1. (3점) `suricata -T`로 설정 검증 통과
2. (4점) 룰 리로드 실행
3. (8점) 각 룰별 테스트 트래픽을 생성하고 탐지 결과를 확인

**정답 예시:**

```bash
# 검증
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml

# 리로드
echo 1 | sudo -S kill -USR2 $(pidof suricata)
sleep 3

# 테스트
curl -s "http://10.20.30.80/../../etc/passwd" > /dev/null  # silent 모드
curl -s "http://10.20.30.80/?q=%3Cscript%3Ealert(1)%3C/script%3E" > /dev/null  # silent 모드
curl -s -A "nikto/2.1.6" "http://10.20.30.80/" > /dev/null  # silent 모드
curl -s -A "sqlmap/1.0" "http://10.20.30.80/" > /dev/null  # silent 모드

# 결과 확인
echo 1 | sudo -S tail -10 /var/log/suricata/fast.log
```

**예상 출력**:
```
05/06/2026-09:32:18  [**] [1:9100001:1] EXAM - Directory Traversal [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.201:54321 -> 10.20.30.80:80
05/06/2026-09:32:25  [**] [1:9100002:1] EXAM - XSS script tag [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.201:54322 -> 10.20.30.80:80
05/06/2026-09:32:30  [**] [1:9100003:1] EXAM - Scanner detected (nikto) [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.201:54323 -> 10.20.30.80:80
05/06/2026-09:32:35  [**] [1:9100004:1] EXAM - Scanner detected (sqlmap) [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.201:54324 -> 10.20.30.80:80
```

> **해석 — 채점 (시나리오별 2점)**:
> - **9100001 매치** = `/../../etc/passwd` URI 에서 `../` content 매치 = ★ 정답 (2점).
> - **9100002 매치** = `<script` URI 매치 = ★ 정답 (2점).
> - **9100003 매치** = `User-Agent: nikto/2.1.6` content 매치 = ★ 정답 (2점).
> - **9100004 매치** = `User-Agent: sqlmap/1.0` content 매치 = ★ 정답 (2점).
> - **9100005 (SSH brute force) 미매치** = 정상. threshold = 10/60s 라 단일 시도는 매치 X. 추가 검증: `for i in $(seq 1 15); do nc -zv 10.20.30.1 22; done` → 9100005 매치.
> - **만점 8/8 (4 명시 + 4 검증)**.

### 2-2-1 룰 검증 — `suricata -T` 통과 출력

```bash
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml 2>&1 | grep -E "Notice|Error" | tail -5
```

**예상 출력**:
```
26/05/06 09:30:15 - <Notice> - Configuration provided was successfully loaded. Exiting.
```

> **해석 — `-T` (test mode) 통과 = 채점 3점**:
> - 'successfully loaded' = 5 룰 syntax 모두 OK.
> - Error 출력 시: `Error: Failed to parse rule "alert http..." at line N` = 해당 룰 syntax 오류 → 시험 감점.

---

## Part 3: 종합 문제 (25점)

### 문제 3-1: 보안 아키텍처 서술 (10점)

다음 질문에 답하라 (텍스트 파일 작성):

1. (3점) nftables, Suricata IPS, Apache+ModSecurity WAF 각각의 역할과 보호 범위를 설명하라
2. (3점) 패킷이 외부에서 web 서버에 도달하기까지 거치는 보안 장비의 순서를 설명하라
3. (4점) SQL Injection 공격이 각 보안 장비에서 어떻게 처리되는지 설명하라

**정답 예시:**

```bash
cat << 'EOF' > /tmp/exam_answer.txt
1. 역할과 보호 범위
- nftables: L3/L4 방화벽. IP, 포트 기반으로 접근 제어.
  허용된 IP/포트만 통과시키고 나머지 차단.
- Suricata IPS: L3~L7 침입방지. 패킷 내용(페이로드)을 검사하여
  알려진 공격 패턴을 탐지/차단. NFQUEUE 모드로 인라인 동작.
- Apache+ModSecurity WAF: L7 웹 방화벽. HTTP 요청/응답을 파싱하여
  SQL Injection, XSS 등 웹 공격을 차단.

2. 트래픽 경로
  외부 → nftables(L3/L4 필터링) → Suricata IPS(페이로드 검사)
  → Apache+ModSecurity WAF(HTTP 검사) → 백엔드 웹 앱(JuiceShop)

3. SQL Injection 처리
- nftables: 80/tcp 포트만 허용하므로, HTTP를 통한 접근은 통과됨.
  nftables는 페이로드를 검사하지 않으므로 SQL Injection 자체는 탐지 불가.
- Suricata IPS: HTTP URI에서 "union select", "OR 1=1" 등
  SQL Injection 패턴을 content 매칭으로 탐지. alert 또는 drop.
- Apache+ModSecurity WAF: ModSecurity CRS 942xxx 룰이 HTTP 파라미터를
  파싱하여 SQL 구문을 탐지. Anomaly Score 5점 이상이면 403 차단.
EOF
```

### 문제 3-2: 트러블슈팅 (15점)

다음 상황을 해결하라:

**상황**: web 서버(10.20.30.80)의 HTTP 서비스에 접근이 안 된다.

**진단 절차 (각 5점):**

1. nftables에서 80번 포트가 허용되어 있는지 확인
2. Suricata가 정상 동작 중인지 확인 (패킷 드롭 없는지)
3. Apache+ModSecurity이 정상 동작 중인지 확인

**정답 예시:**

```bash
# 1. nftables 확인
echo 1 | sudo -S nft list ruleset | grep "dport 80"
# 출력이 없으면 → 80 포트 허용 룰 추가 필요

# 2. Suricata 확인
echo 1 | sudo -S systemctl is-active suricata
echo 1 | sudo -S grep "kernel_drops" /var/log/suricata/stats.log | tail -1
# drops이 급증하면 → Suricata 성능 문제
# fail-open이 아니면 → Suricata 정지 시 트래픽 차단

# 3. Apache+ModSecurity 확인
ssh ccc@10.20.30.80
systemctl is-active apache2
echo 1 | sudo -S apache2ctl -M 2>/dev/null | grep security
# security2_module이 로드되어 있으면 ModSecurity 정상
# WAF 테스트: curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:8082/?id=1'+OR+1=1--"
# 403이면 WAF 정상 동작
```

### 3-2-1 진단 결과 — 3 layer 정상성 통합 출력

```bash
# 1. nftables — 80 허용 룰 + 패킷 카운터
echo 1 | sudo -S nft list ruleset | grep -E "dport (80|443)" | head -3
# 2. Suricata — active + kernel_drops 추세
echo 1 | sudo -S systemctl is-active suricata
echo 1 | sudo -S grep "capture.kernel_drops" /var/log/suricata/stats.log | tail -1
# 3. Apache + ModSecurity — security2 module + WAF block 테스트
ssh ccc@10.20.30.80 "systemctl is-active apache2 && apache2ctl -M 2>/dev/null | grep security2"
curl -s -o /dev/null -w "WAF SQLi 테스트: %{http_code}\n" "http://10.20.30.80:8082/?id=1%27+OR+1%3D1--"
```

**예상 출력**:
```
                tcp dport { 80, 443 } accept
active
capture.kernel_drops                          | Total                     | 0
active
 security2_module (shared)
WAF SQLi 테스트: 403
```

> **해석 — 채점 3 항목 (각 5점)**:
> - **nft `tcp dport { 80, 443 } accept`** = 80/443 허용 룰 적재됨 (5점). 미출력 시 → `nft add rule inet exam_filter input tcp dport 80 accept` 추가.
> - **suricata active + kernel_drops=0** = IPS 가동 + 패킷 누락 X (5점). drops>0 시 → `af-packet threads` 증설 또는 NIC ring buffer 확장.
> - **security2_module + WAF=403** = ModSecurity 가 SQLi 차단 (5점). 200 응답 시 → `SecRuleEngine On` 확인 + CRS 942100 룰 활성화 점검.
> - **3 layer 모두 PASS** = 트러블슈팅 만점 15/15. 한 layer fail 시 해당 layer 의 stderr/journalctl 로 root cause 추적.

---

## 채점 기준 요약

| 영역 | 배점 | 핵심 체크포인트 |
|------|------|-----------------|
| 기본 방화벽 | 20점 | policy drop, conntrack, 서비스별 허용, 로깅 |
| NAT/포워딩 | 20점 | masquerade, DNAT, forward 허용, ip_forward |
| Suricata 룰 | 20점 | 올바른 문법, content/flow/threshold, sid 고유 |
| 룰 테스트 | 15점 | 검증 통과, 리로드, 테스트 결과 |
| 서술형 | 10점 | 정확한 역할 구분, 트래픽 흐름 이해 |
| 트러블슈팅 | 15점 | 체계적 진단, 해결 방안 |

---

## 시험 종료 후 정리

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 시험 설정 제거
ssh ccc@10.20.30.1  # 비밀번호 자동입력 SSH
echo 1 | sudo -S nft delete table inet exam_filter 2>/dev/null
echo 1 | sudo -S nft delete table inet exam_nat 2>/dev/null
echo 1 | sudo -S sed -i '/EXAM/d' /etc/suricata/rules/local.rules 2>/dev/null
echo 1 | sudo -S kill -USR2 $(pidof suricata) 2>/dev/null
```

---

## 참고: 자주 하는 실수

| 실수 | 결과 | 해결 |
|------|------|------|
| SSH 허용 전 policy drop | SSH 연결 끊김 | 콘솔 접속하여 복구 |
| conntrack 미설정 | 기존 연결 끊김 | 첫 번째 룰로 conntrack 추가 |
| Suricata sid 중복 | 룰 로드 실패 | 고유한 sid 부여 |
| ip_forward 미활성화 | NAT 미동작 | sysctl 설정 |
| 룰 리로드 안 함 | 새 룰 미적용 | kill -USR2 실행 |

---

> **실습 환경 검증 완료** (2026-03-28): nftables(inet filter+ip nat), Suricata 8.0.4(65K룰), Apache+ModSecurity(:8082→403), Wazuh v4.11.2(local_rules 62줄), OpenCTI(200)

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### nftables
> **역할:** Linux 커널 기반 상태 기반 방화벽 (iptables 후속)  
> **실행 위치:** `secu (10.20.30.1)`  
> **접속/호출:** `sudo nft ...` CLI + `/etc/nftables.conf` 영속 설정

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/etc/nftables.conf` | 부팅 시 로드되는 영속 룰셋 |
| `/var/log/kern.log` | `log prefix` 룰의 패킷 드롭 로그 |

**핵심 설정·키**

- `table inet filter` — IPv4/IPv6 공통 필터 테이블
- `chain input { policy drop; }` — 기본 차단 정책
- `ct state established,related accept` — 응답 트래픽 허용

**로그·확인 명령**

- `journalctl -t kernel -g 'nft'` — 룰에서 `log prefix` 지정한 패킷 드롭

**UI / CLI 요점**

- `sudo nft list ruleset` — 현재 로드된 전체 룰 출력
- `sudo nft -f /etc/nftables.conf` — 설정 파일 재적용
- `sudo nft list set inet filter blacklist` — 집합(set) 내용 조회

> **해석 팁.** 룰은 **위→아래 첫 매칭 우선**. `accept`는 해당 체인만 종료, 상위 훅은 계속 평가된다. 변경 후 `nft list ruleset`로 실제 적용 여부 확인.

### Suricata IDS/IPS
> **역할:** 시그니처 기반 네트워크 침입 탐지/차단 엔진  
> **실행 위치:** `secu (10.20.30.1)`  
> **접속/호출:** `systemctl status suricata` / `suricatasc` 소켓 / `suricata -T`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `/etc/suricata/suricata.yaml` | 메인 설정 (HOME_NET, af-packet, rule-files) |
| `/etc/suricata/rules/local.rules` | 사용자 커스텀 탐지 룰 |
| `/var/lib/suricata/rules/suricata.rules` | `suricata-update` 병합 룰 |
| `/var/log/suricata/eve.json` | JSON 이벤트 (alert/flow/http/dns/tls) |
| `/var/log/suricata/fast.log` | 알림 1줄 텍스트 로그 |
| `/var/log/suricata/stats.log` | 엔진 성능 통계 |

**핵심 설정·키**

- `HOME_NET` — 내부 대역 — 틀리면 내부/외부 판별 실패
- `af-packet.interface` — 캡처 NIC — 트래픽이 흐르는 인터페이스와 일치해야 함
- `rule-files: ["local.rules"]` — 로드할 룰 파일 목록

**로그·확인 명령**

- `jq 'select(.event_type=="alert")' eve.json` — 알림만 추출
- `grep 'Priority: 1' fast.log` — 고위험 탐지만 빠르게 확인

**UI / CLI 요점**

- `suricata -T -c /etc/suricata/suricata.yaml` — 설정/룰 문법 검증
- `suricatasc -c stats` — 실시간 통계 조회 (런타임 소켓)
- `suricata-update` — 공개 룰셋 다운로드·병합

> **해석 팁.** `stats.log`의 `kernel_drops > 0`이면 누락 발생 → `af-packet threads` 증설. 커스텀 룰 `sid`는 **1,000,000 이상** 할당 권장.

---

## 실제 사례 (WitFoo Precinct 6 — w02-w07 7주 검수 reference)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *중간고사 — 방화벽 + IPS 구성 실기* — 학생 본인 setup 의 *완성도 검증* 을 dataset 의 운영 환경 baseline 으로.

### Case 1: 학생 setup 검수 — dataset baseline 5축 비교 표

| 검수 축 | dataset baseline | 학생 setup 목표 |
|---------|-----------------|----------------|
| **Firewall block ratio** | 4.7% (5,826 / 124,177) | 본인 환경 측정 → ±2%p 내 |
| **WAF GET outcome=200 비율** | 99% (4018/4018 모두 200/302) | 정상 트래픽이 WAF 통과 (block 0건) |
| **Suricata flow event/min** | ~3.9 events/min (정상) | 본인 환경 동등 baseline |
| **multi-vendor evidence** | host 1개당 2 product (Precinct + Cisco) | nft + Suricata + ModSec 3 vendor |
| **CEF 출력 표준** | WAF/Cisco 모두 CEF | 본인 환경의 모든 출력이 CEF 또는 JSON 표준 |

### Case 2: dataset 의 *공격 시나리오* 재현 — 시험 채점 기준

dataset 의 *대표 공격* 패턴을 학생 setup 에 *재생* 하여 차단 가능 여부:

| 공격 패턴 | 본 dataset 의 record | 시험 검수 항목 |
|----------|--------------------|--------------|
| 1초 burst 정찰 (30 host × 54 port) | src=100.64.20.230 | nft block ratio 확인 |
| WAF SQLi POST (JSESSIONID 노출) | 100.64.1.67 → 10.0.145.98 | ModSec rule 942100 발동 확인 |
| Email Phishing block | dst=100.64.28.102, phishScore=100 | (이메일 layer — 본 시험 범위 외) |
| NTLM 4776 빠른 재인증 | USER-0012 host hopping | Wazuh 관련 외 — 다음 주차 |

**해석 — 본 lecture (중간고사) 와의 매핑**

| 시험 채점 학습 항목 | 본 record 의 시사점 |
|-------------------|---------------------|
| **5축 baseline 비교** | dataset 의 5 축 metric 을 학생 setup 에 동일 측정 — 일치 정도 (±2%p) 점수화 |
| **공격 재현 가능성** | dataset 의 burst 패턴 (100.64.20.230) 을 nmap 으로 재현 → 학생 nft 가 차단하는지 시험 |
| **출력 표준화** | dataset 모든 출력이 CEF/JSON — 학생 setup 도 동일 표준 (수기 grep 가능 X, 자동 SIEM 통합 가능) |
| **multi-vendor** | dataset host 가 2 vendor — 학생도 *최소 3 vendor* (nft + Suricata + ModSec) 통합 |

**중간고사 채점 권고**:
- 5축 baseline ±2%p 일치 = 5축 × 5점 = 25점
- dataset 공격 재현 차단 = 20점 (4 시나리오 × 5점)
- CEF/JSON 표준 출력 = 15점
- 보고서 (1-pager Bastion 통합) = 20점
- 발표 (3분) = 20점



---

## 부록: 학습 OSS 도구 매트릭스 (Course2 SecOps — Week 08 중간고사 종합)

8주차 중간고사는 **2-7주차에서 익힌 도구의 통합 운용** 평가이다.

| 영역 | 핵심 도구 |
|------|----------|
| 방화벽 | nftables / fail2ban / crowdsec / conntrack |
| IPS | Suricata / Snort3 / suricata-update / evebox |
| WAF | ModSecurity + OWASP CRS / Coraza / wafw00f (점검) |
| 통합 모니터링 | jq / lnav / Prometheus + Grafana |
| 룰 변환 | Sigma / pysigma / sigma-cli |
| 테스트 | go-ftw / tcpreplay / suricata-verify / curl |

### 평가 시나리오에서 사용할 도구 흐름

```bash
# 시나리오 1: nftables 룰 작성 + Suricata 알람 검증
sudo nft add rule inet filter input tcp dport 23 drop                     # telnet 차단
sudo systemctl reload suricata
curl -A "Nikto/2.1.5" http://10.20.30.80/                                  # 알람 트리거
sudo jq -r 'select(.event_type=="alert") | .alert.signature' /var/log/suricata/eve.json | tail -5

# 시나리오 2: ModSec 활성화 + 우회 시도 + 차단 확인
curl -i "http://10.20.30.80/?q='OR'1'='1"
sudo tail /var/log/apache2/modsec_audit.log

# 시나리오 3: 통합 dashboard
sudo systemctl status nftables suricata apache2
sudo evebox-cli --addr http://localhost:5636 alerts                        # 콘솔 dashboard
```

### 시나리오 1 검증 — Nikto 알람 트리거 결과

```bash
ssh ccc@10.20.30.1 "echo 1 | sudo -S jq -r 'select(.event_type==\"alert\") | [.timestamp, .alert.signature_id, .alert.signature, .src_ip] | @tsv' /var/log/suricata/eve.json | tail -3"
ssh ccc@10.20.30.1 "echo 1 | sudo -S grep 'EXAM' /var/log/suricata/fast.log | wc -l"
```

**예상 출력**:
```
2026-05-06T11:14:22.318712+0900    9100003    EXAM - Scanner detected (nikto)    10.20.30.201
2026-05-06T11:14:23.041208+0900    9100003    EXAM - Scanner detected (nikto)    10.20.30.201
2026-05-06T11:14:23.812447+0900    9100003    EXAM - Scanner detected (nikto)    10.20.30.201
3
```

> **해석 — 통합 운용 동작 검증**:
> - **3 건 알람** = `User-Agent: Nikto/2.1.5` 헤더가 3 패킷 (curl 3 요청) 모두 sid 9100003 매치 = nft 23 차단 룰 통과 + Suricata 7 layer 검사 정상.
> - **`signature_id=9100003`** = lecture § 2-1 작성한 학생 룰이 운영 환경 (eve.json) 에 적재됨 = "통합 운용" 평가 합격.
> - **`src_ip=10.20.30.201`** = bastion 에서 발송한 nmap/curl 트래픽 = 학생 attacker host 출처 일치.
> - 매트릭스 평가: 학생이 **2주차 nft + 5주차 sid 9100003 + 7주차 jq 추출** 의 3 도구를 한 흐름에 결합 = 8주차 평가 핵심.

학생은 8주차에서 **2-7주차의 모든 도구를 흐름에 따라 사용**해 종합 보안 인프라를 운영한다.
