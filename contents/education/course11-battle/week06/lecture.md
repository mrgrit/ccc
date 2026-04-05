# Week 06: 방화벽 구축 — nftables

## 학습 목표
- 방화벽의 개념과 네트워크 보안에서의 역할을 이해한다
- nftables의 아키텍처(테이블, 체인, 규칙)를 체계적으로 설명할 수 있다
- iptables와 nftables의 차이점과 마이그레이션 방법을 이해한다
- nftables 규칙을 작성하여 네트워크 트래픽을 허용/차단할 수 있다
- 상태 추적(Stateful) 방화벽의 원리와 설정을 이해한다
- 방화벽 로깅을 설정하고 차단된 트래픽을 분석할 수 있다
- 공방전에서 Blue Team의 핵심 방어 수단으로서 방화벽을 활용할 수 있다

## 전제 조건
- Week 01-05 완료 (공격 기법 전반 이해)
- TCP/IP 네트워크 기본 (IP, 포트, 프로토콜)
- Linux 기본 명령어 및 시스템 관리

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 방화벽 이론 + nftables 아키텍처 | 강의 |
| 0:40-1:10 | nftables 규칙 문법 상세 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | nftables 기본 규칙 실습 | 실습 |
| 2:00-2:30 | 상태 추적 + 로깅 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 공방전용 방화벽 정책 설계 실습 | 실습 |
| 3:10-3:40 | 방화벽 우회 기법 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: 방화벽 이론 + nftables 아키텍처 (40분)

## 1.1 방화벽이란?

방화벽(Firewall)은 네트워크 트래픽을 미리 정의된 보안 규칙에 따라 허용하거나 차단하는 네트워크 보안 시스템이다.

**MITRE ATT&CK 관련:**
```
방어 기법:
  +-- Defense in Depth의 네트워크 계층
공격 기법:
  +-- T1562.004 — Disable or Modify System Firewall
        +-- 절차: nftables 규칙 삭제/수정으로 방화벽 무력화
```

### 방화벽 유형

| 유형 | 동작 계층 | 특징 | 예시 |
|------|---------|------|------|
| 패킷 필터링 | L3-L4 | IP/포트 기반 필터링 | nftables, iptables |
| 상태 추적 (Stateful) | L3-L4 | 연결 상태 추적 | nftables (ct state) |
| 애플리케이션 방화벽 | L7 | HTTP/DNS 등 내용 검사 | WAF, ModSecurity |
| 차세대 방화벽 (NGFW) | L3-L7 | DPI + 앱 식별 + IPS | Palo Alto, FortiGate |

### Stateless vs Stateful

```
[Stateless 방화벽]
  규칙: "포트 80 허용, 나머지 차단"
  문제: 응답 트래픽도 별도로 허용해야 함
  
[Stateful 방화벽]
  규칙: "새 연결은 포트 80만 허용, 기존 연결은 자동 허용"
  장점: 응답 트래픽을 자동으로 처리, 더 안전
```

## 1.2 nftables 아키텍처

nftables는 Linux 커널의 netfilter 프레임워크 기반 차세대 방화벽이다. iptables를 대체한다.

### 구조

```
nftables 구조:
  테이블 (Table)
    +-- 체인 (Chain)
          +-- 규칙 (Rule)
                +-- 표현식 (Expression) + 판정 (Verdict)

예시:
  table inet filter {
      chain input {
          type filter hook input priority 0; policy drop;
          ct state established,related accept    # 기존 연결 허용
          tcp dport 22 accept                     # SSH 허용
          tcp dport 80 accept                     # HTTP 허용
      }
  }
```

### 테이블 패밀리

| 패밀리 | 설명 | 대상 |
|--------|------|------|
| `ip` | IPv4 전용 | IPv4 트래픽 |
| `ip6` | IPv6 전용 | IPv6 트래픽 |
| `inet` | IPv4 + IPv6 통합 | 모든 IP 트래픽 |
| `arp` | ARP | ARP 트래픽 |
| `bridge` | 브리지 | L2 트래픽 |
| `netdev` | 장치 수준 | 인터페이스 입력 |

### 체인 타입과 훅

| 훅 | 설명 | 용도 |
|----|------|------|
| `input` | 로컬 프로세스로 향하는 패킷 | 서버 서비스 보호 |
| `output` | 로컬 프로세스에서 나가는 패킷 | 아웃바운드 제어 |
| `forward` | 다른 호스트로 전달되는 패킷 | 라우터/게이트웨이 |
| `prerouting` | 라우팅 전 | NAT, 리다이렉션 |
| `postrouting` | 라우팅 후 | SNAT, 마스커레이딩 |

### 판정(Verdict)

| 판정 | 설명 |
|------|------|
| `accept` | 패킷 허용 |
| `drop` | 패킷 무시 (응답 없음) |
| `reject` | 패킷 거부 (ICMP 응답 전송) |
| `log` | 로그 기록 후 다음 규칙 진행 |
| `counter` | 카운터 증가 후 다음 규칙 진행 |
| `jump chain_name` | 다른 체인으로 이동 |
| `return` | 이전 체인으로 복귀 |

### nftables vs iptables 비교

| 항목 | iptables | nftables |
|------|---------|---------|
| 구문 | `-A INPUT -p tcp --dport 22 -j ACCEPT` | `tcp dport 22 accept` |
| 테이블 | 고정 (filter, nat, mangle) | 사용자 정의 |
| 패밀리 | ip, ip6 별도 | inet으로 통합 가능 |
| 성능 | 선형 규칙 탐색 | 세트/맵 기반 최적화 |
| 트랜잭션 | 없음 | 원자적 규칙 교체 |
| JSON | 없음 | nft -j로 JSON 출력 |

---

# Part 2: nftables 규칙 문법 상세 (30분)

## 2.1 기본 명령어

```bash
# 현재 규칙 전체 보기
nft list ruleset

# 테이블 생성
nft add table inet filter

# 체인 생성 (input, 기본 정책 drop)
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'

# 규칙 추가
nft add rule inet filter input tcp dport 22 accept

# 규칙 삽입 (맨 앞에)
nft insert rule inet filter input tcp dport 80 accept

# 규칙 삭제 (핸들 번호로)
nft -a list chain inet filter input  # 핸들 확인
nft delete rule inet filter input handle 5

# 전체 규칙 초기화
nft flush ruleset

# 규칙 파일에서 로드
nft -f /etc/nftables.conf
```

## 2.2 매칭 표현식

| 표현식 | 설명 | 예시 |
|--------|------|------|
| `ip saddr` | 소스 IP | `ip saddr 10.20.30.0/24` |
| `ip daddr` | 목적지 IP | `ip daddr 10.20.30.80` |
| `tcp dport` | 목적지 TCP 포트 | `tcp dport 22` |
| `tcp sport` | 소스 TCP 포트 | `tcp sport 1024-65535` |
| `udp dport` | 목적지 UDP 포트 | `udp dport 53` |
| `ct state` | 연결 상태 | `ct state established,related` |
| `iifname` | 입력 인터페이스 | `iifname "eth0"` |
| `oifname` | 출력 인터페이스 | `oifname "eth1"` |
| `meta l4proto` | L4 프로토콜 | `meta l4proto icmp` |
| `tcp flags` | TCP 플래그 | `tcp flags & syn == syn` |

## 2.3 세트(Set)와 맵(Map)

```bash
# 세트: 여러 값을 하나의 규칙으로 처리
nft add set inet filter allowed_ports '{ type inet_service; }'
nft add element inet filter allowed_ports '{ 22, 80, 443, 8002 }'
nft add rule inet filter input tcp dport @allowed_ports accept

# 맵: 값에 따라 다른 판정 적용
nft add map inet filter port_policy '{ type inet_service : verdict; }'
nft add element inet filter port_policy '{ 22 : accept, 80 : accept, 3306 : drop }'
nft add rule inet filter input tcp dport vmap @port_policy
```

## 2.4 로깅

```bash
# 로그 + 차단
nft add rule inet filter input tcp dport 23 log prefix "TELNET_BLOCKED: " drop

# 로그만 (다음 규칙 계속 진행)
nft add rule inet filter input log prefix "ALL_INPUT: " counter

# 로그 확인
dmesg | grep "TELNET_BLOCKED"
journalctl -k | grep "nft"
```

---

# Part 3: nftables 기본 규칙 실습 (40분)

## 실습 3.1: 방화벽 규칙 확인 및 기본 설정

### Step 1: 현재 방화벽 상태 확인

> **실습 목적**: secu 서버의 현재 nftables 설정을 확인하고 이해한다.
>
> **배우는 것**: nftables 규칙 읽기와 현재 방화벽 상태 파악

```bash
# secu 서버의 현재 방화벽 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S nft list ruleset 2>/dev/null"
# 예상 출력: 현재 적용된 nftables 규칙

# 방화벽 서비스 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S systemctl status nftables 2>/dev/null | head -10"
```

> **결과 해석**:
> - 규칙이 비어 있으면 방화벽이 설정되지 않은 상태
> - 규칙이 있으면 각 체인의 정책(policy)과 개별 규칙을 확인
>
> **명령어 해설**:
> - `nft list ruleset`: 현재 적용된 모든 규칙 표시
> - `systemctl status nftables`: 방화벽 서비스 상태 확인
>
> **트러블슈팅**:
> - "nft: command not found": nftables 패키지 설치 필요
> - "Error: Could not process rule": 문법 오류, 규칙 확인

### Step 2: 기본 방화벽 정책 설정

> **실습 목적**: 기본 방화벽 정책(허용/차단)을 설정하고 동작을 확인한다.
>
> **배우는 것**: 화이트리스트(기본 차단) vs 블랙리스트(기본 허용) 정책

```bash
# secu 서버에서 방화벽 설정 (sudo)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'FIREWALL'
echo 1 | sudo -S bash -c '
# 기존 규칙 초기화
nft flush ruleset

# 테이블 생성
nft add table inet filter

# input 체인 (기본 정책: drop)
nft add chain inet filter input "{ type filter hook input priority 0; policy drop; }"

# 기본 허용 규칙
nft add rule inet filter input ct state established,related accept   # 기존 연결 허용
nft add rule inet filter input iifname "lo" accept                   # 루프백 허용
nft add rule inet filter input ip protocol icmp accept               # ICMP 허용
nft add rule inet filter input tcp dport 22 accept                   # SSH 허용
nft add rule inet filter input tcp dport 8002 accept                 # SubAgent 허용

# 결과 확인
nft list ruleset
' 2>/dev/null
FIREWALL
# 예상 출력: 설정된 방화벽 규칙 목록
```

> **결과 해석**:
> - `policy drop`: 규칙에 매칭되지 않는 모든 패킷 차단 (화이트리스트 정책)
> - `ct state established,related accept`: 이미 수립된 연결의 응답 트래픽 자동 허용
> - `iifname "lo" accept`: 로컬 루프백(localhost) 트래픽 허용
> - `tcp dport 22 accept`: SSH 접속 허용 (이것이 없으면 SSH 연결 끊김!)
>
> **실전 활용**: 공방전에서 Blue Team은 이 기본 정책을 먼저 설정한 후, 필요한 서비스만 추가 허용한다.
>
> **트러블슈팅**:
> - SSH 연결이 끊김: SSH(22번 포트) 허용 규칙을 먼저 추가해야 함
> - "Error: chain already exists": `nft flush ruleset`으로 초기화 후 재시도

### Step 3: 포트별 접근 제어

> **실습 목적**: 특정 포트에 대해 소스 IP 기반 접근 제어를 설정한다.
>
> **배우는 것**: 소스 IP 필터링과 세분화된 접근 제어

```bash
# 특정 IP에서만 SSH 허용 (opsclaw에서만)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S nft add rule inet filter input ip saddr 10.20.30.201 tcp dport 22 accept 2>/dev/null"

# 내부 네트워크에서만 SubAgent 접근 허용
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S nft add rule inet filter input ip saddr 10.20.30.0/24 tcp dport 8002 accept 2>/dev/null"

# 외부에서의 접근은 로그 후 차단
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S nft add rule inet filter input log prefix '"BLOCKED: "' counter drop 2>/dev/null"

# 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S nft list chain inet filter input 2>/dev/null"
```

> **결과 해석**:
> - `ip saddr 10.20.30.201`: opsclaw 서버 IP에서만 허용
> - `ip saddr 10.20.30.0/24`: 내부 서브넷 전체 허용
> - `log prefix "BLOCKED:" counter drop`: 차단된 패킷을 로그에 기록
>
> **실전 활용**: 공방전에서 불필요한 포트를 모두 차단하고, 필수 서비스만 내부 IP에서 허용하는 것이 핵심 전략이다.

## 실습 3.2: 상태 추적 + 로깅

### Step 1: 연결 상태 추적 확인

> **실습 목적**: Stateful 방화벽의 연결 상태 추적 메커니즘을 이해한다.
>
> **배우는 것**: ct state의 각 상태와 활용법

```bash
# 연결 추적 테이블 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S conntrack -L 2>/dev/null | head -20"
# 예상 출력: 현재 추적 중인 연결 목록
# tcp 6 431999 ESTABLISHED src=10.20.30.201 dst=10.20.30.1 sport=54321 dport=22 ...

# 연결 상태별 카운트
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S conntrack -L 2>/dev/null | awk '{print \$4}' | sort | uniq -c | sort -rn"
# 예상 출력:
#   5 ESTABLISHED
#   2 TIME_WAIT
#   1 SYN_SENT
```

> **결과 해석**:
> - `ESTABLISHED`: 연결이 수립된 상태 (양방향 통신 중)
> - `NEW`: 새로운 연결 시도 (SYN 패킷)
> - `RELATED`: 기존 연결과 관련된 새 연결 (FTP data 등)
> - `INVALID`: 비정상 패킷 (스캔, 공격 가능)

### Step 2: 방화벽 로깅 설정 및 분석

> **실습 목적**: 차단된 트래픽을 로그로 기록하고 분석한다.
>
> **배우는 것**: 방화벽 로그 설정과 분석 기법

```bash
# 차단 로그가 있는지 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S dmesg 2>/dev/null | grep 'BLOCKED' | tail -10"

# 포트 스캔 탐지 시뮬레이션 (opsclaw에서 secu로 스캔)
echo 1 | sudo -S nmap -sS -p 1-100 10.20.30.1 2>/dev/null | head -10

# 스캔 후 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S dmesg 2>/dev/null | grep 'BLOCKED' | tail -20"
# 예상 출력: 차단된 포트 스캔 시도 로그
```

> **결과 해석**:
> - `BLOCKED:` 접두사가 있는 로그가 차단된 패킷
> - 짧은 시간에 다수의 차단 로그 → 포트 스캔 탐지 가능
> - 소스 IP, 목적지 포트, 프로토콜 등 세부 정보 확인 가능

## 실습 3.3: 공방전용 방화벽 정책 설계

### Step 1: 종합 방화벽 정책 설정

> **실습 목적**: 공방전에서 사용할 종합적인 방화벽 정책을 설계하고 적용한다.
>
> **배우는 것**: 실전 방화벽 정책 설계 방법론

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'POLICY'
echo 1 | sudo -S bash -c '
nft flush ruleset
nft -f - << "NFT"
table inet filter {
    set internal_nets {
        type ipv4_addr
        flags interval
        elements = { 10.20.30.0/24 }
    }
    
    set allowed_services {
        type inet_service
        elements = { 22, 8002 }
    }
    
    chain input {
        type filter hook input priority 0; policy drop;
        
        # 기존 연결 허용
        ct state established,related accept
        ct state invalid drop
        
        # 루프백 허용
        iifname "lo" accept
        
        # ICMP 허용 (ping)
        ip protocol icmp accept
        
        # 내부 네트워크에서 허용된 서비스
        ip saddr @internal_nets tcp dport @allowed_services accept
        
        # 차단 로깅
        log prefix "NFT_DROP: " counter drop
    }
    
    chain forward {
        type filter hook forward priority 0; policy drop;
        ct state established,related accept
        log prefix "NFT_FWD_DROP: " counter drop
    }
    
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
NFT
nft list ruleset
' 2>/dev/null
POLICY
```

> **결과 해석**:
> - `set internal_nets`: 내부 네트워크 IP 세트 (확장 용이)
> - `set allowed_services`: 허용된 서비스 포트 세트
> - `ct state invalid drop`: 비정상 패킷 즉시 차단
> - `forward chain drop`: 라우팅 트래픽 차단 (게이트웨이 보호)
>
> **실전 활용**: 공방전에서 이 정책은 기본 방어의 시작점이다. Red Team의 스캔과 공격을 차단하면서 필요한 서비스만 허용한다.

### Step 2: OpsClaw를 활용한 방화벽 감사

> **실습 목적**: OpsClaw로 방화벽 상태를 자동 점검한다.
>
> **배우는 것**: 방화벽 감사 자동화

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects   -H "Content-Type: application/json"   -H "X-API-Key: opsclaw-api-key-2026"   -d '{"name":"week06-firewall","request_text":"방화벽 구축 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"secu 방화벽 규칙","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S nft list ruleset 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"secu 차단 로그","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S dmesg 2>/dev/null | grep NFT_DROP | tail -5\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"포트 스캔 테스트","instruction_prompt":"nmap -sS -p 22,80,443 10.20.30.1 2>/dev/null | grep -E \"open|filtered|closed\"","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:25s} → {t[\"status\"]}')
"
```

---

# Part 4: 방화벽 우회 기법 이해 (30분)

## 4.1 방화벽 우회 기법 (Red Team 관점)

| 기법 | 설명 | 방어 |
|------|------|------|
| 포트 터널링 | 허용된 포트(80, 443)로 다른 트래픽 | DPI (심층 패킷 검사) |
| 패킷 단편화 | IP 패킷을 분할하여 규칙 우회 | 패킷 재조합 규칙 |
| 소스 포트 조작 | DNS(53), HTTP(80) 포트에서 발신 | Stateful 검사 |
| IPv6 터널링 | IPv6 트래픽으로 IPv4 방화벽 우회 | IPv6 규칙도 설정 |
| DNS 터널링 | DNS 쿼리로 데이터 은닉 전송 | DNS 트래픽 모니터링 |
| HTTP 터널링 | HTTP 요청에 데이터 은닉 | 프록시 검사 |

## 4.2 공방전에서의 방화벽 전략

### Red Team 전략
```
[1] 방화벽 규칙 탐색 (어떤 포트가 열렸는지)
    → nmap -sS -p- 대상IP
[2] 허용된 포트로 트래픽 터널링
    → ssh -L 또는 HTTP 터널
[3] 방화벽 규칙 삭제 시도 (권한 상승 후)
    → nft flush ruleset
```

### Blue Team 전략
```
[1] 최소 허용 원칙 (Whitelist)
    → 필요한 포트만 허용, 나머지 전부 차단
[2] 로깅 + 모니터링
    → 차단 로그 실시간 감시
[3] 규칙 무결성 확인
    → 주기적으로 규칙 해시 검증
[4] 아웃바운드 필터링
    → 나가는 트래픽도 제어 (데이터 유출 방지)
```

---

## 검증 체크리스트
- [ ] nftables의 테이블/체인/규칙 구조를 설명할 수 있는가
- [ ] 기본 방화벽 정책(기본 차단)을 설정했는가
- [ ] 상태 추적(ct state) 규칙을 이해하고 설정했는가
- [ ] 소스 IP 기반 접근 제어를 설정했는가
- [ ] 방화벽 로깅을 설정하고 로그를 분석했는가
- [ ] 세트(Set)를 활용한 효율적인 규칙을 작성했는가
- [ ] 공방전용 종합 방화벽 정책을 설계했는가
- [ ] 포트 스캔이 방화벽에서 차단되는 것을 확인했는가
- [ ] 방화벽 우회 기법을 이해했는가

## 자가 점검 퀴즈

1. Stateless 방화벽과 Stateful 방화벽의 핵심 차이를 설명하라.

2. nftables에서 `ct state established,related accept` 규칙이 필요한 이유를 설명하라.

3. `policy drop`과 `policy accept`의 보안적 차이와 각각의 사용 시나리오를 설명하라.

4. nftables의 세트(Set)를 사용하면 어떤 장점이 있는지 설명하라.

5. 방화벽에서 `reject`와 `drop`의 차이를 공격자 관점에서 설명하라.

6. `inet` 패밀리를 사용하면 `ip`/`ip6` 패밀리 대비 어떤 장점이 있는가?

7. 공방전에서 Blue Team이 설정해야 할 최소 방화벽 규칙 5가지를 나열하라.

8. Red Team이 방화벽을 우회하기 위해 사용할 수 있는 기법 3가지를 설명하라.

9. 방화벽 로그에서 포트 스캔을 식별하는 패턴을 설명하라.

10. output 체인에서 트래픽을 제어하는 것이 중요한 이유를 설명하라.

## 과제

### 과제 1: 방화벽 정책 설계 보고서 (필수)
- secu 서버에 종합 방화벽 정책을 설계하고 적용
- 허용/차단 규칙과 각 규칙의 근거를 문서화
- 포트 스캔 및 공격 시도가 차단되는 것을 검증

### 과제 2: 방화벽 우회 실험 (선택)
- Red Team 관점에서 설정한 방화벽을 우회하는 방법 탐색
- 성공/실패한 우회 시도를 기록하고 분석

### 과제 3: iptables → nftables 마이그레이션 (도전)
- iptables 규칙 세트를 nftables로 변환하는 스크립트 작성
- 변환 전후의 규칙 비교 및 동작 검증
