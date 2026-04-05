# Week 07: 네트워크 포렌식

## 학습 목표
- Wireshark/tshark를 심화 수준으로 사용하여 패킷 분석을 수행할 수 있다
- NetFlow/sFlow 데이터를 분석하여 네트워크 트래픽 이상을 탐지할 수 있다
- PCAP 파일에서 악성 통신, 데이터 유출, C2 트래픽을 식별할 수 있다
- DNS, HTTP, TLS 프로토콜 분석으로 위협을 탐지할 수 있다
- 네트워크 포렌식 증거를 체계적으로 수집하고 보존할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 네트워크 포렌식 이론 + 증거 수집 (Part 1) | 강의 |
| 0:50-1:30 | tshark 심화 + 필터 (Part 2) | 강의/데모 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | PCAP 분석 실습 (Part 3) | 실습 |
| 2:30-3:10 | 프로토콜 심화 분석 + 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **PCAP** | Packet Capture | 네트워크 패킷 캡처 파일 | CCTV 녹화 영상 |
| **tshark** | Terminal Shark | Wireshark의 CLI 버전 | 터미널 CCTV 재생기 |
| **NetFlow** | NetFlow | 네트워크 플로우(세션) 통계 데이터 | 차량 통행량 기록 |
| **BPF** | Berkeley Packet Filter | 패킷 필터링 문법 | CCTV 검색 필터 |
| **display filter** | Display Filter | Wireshark 표시 필터 | 특정 영상만 보기 |
| **DPI** | Deep Packet Inspection | 패킷 내용까지 검사 | 소포 내용물 검사 |
| **C2** | Command and Control | 공격자의 원격 제어 통신 | 스파이의 비밀 통신 |
| **비콘** | Beacon | C2 서버에 주기적으로 접속하는 패턴 | 정기 보고 |
| **페이로드** | Payload | 패킷의 실제 데이터 부분 | 소포 내용물 |
| **핸드셰이크** | Handshake | TCP/TLS 연결 설정 과정 | 악수(인사) |

---

# Part 1: 네트워크 포렌식 이론 + 증거 수집 (50분)

## 1.1 네트워크 포렌식이란?

네트워크 포렌식은 **네트워크 트래픽을 캡처, 기록, 분석하여 보안 사고의 증거를 확보**하는 디지털 포렌식의 한 분야다.

### 네트워크 포렌식 데이터 유형

```
[Full Packet Capture (PCAP)]
  → 패킷 전체 내용 기록
  → 가장 상세하지만 용량 큼
  → 도구: tcpdump, Wireshark, tshark

[Flow Data (NetFlow/sFlow)]
  → 세션 메타데이터만 기록 (IP, 포트, 크기, 시간)
  → 용량 작음, 장기 보관 가능
  → 도구: nfdump, ntopng

[Log Data]
  → 방화벽, IDS, 프록시 로그
  → 이벤트 기반 기록
  → 도구: Wazuh, Suricata

[선택 기준]
  PCAP:    "무엇을 말했는가" (내용)
  Flow:    "누가 누구와 대화했는가" (메타)
  Log:     "무엇이 탐지되었는가" (이벤트)
```

## 1.2 증거 수집 원칙

```
[네트워크 포렌식 증거 수집 4원칙]

1. 무결성 (Integrity)
   → 캡처 파일의 해시값 즉시 기록
   → 원본은 읽기 전용으로 보존
   → 분석은 복사본으로 수행

2. 연속성 (Chain of Custody)
   → 증거 접근 기록 유지
   → 누가, 언제, 왜 접근했는지 기록

3. 적시성 (Timeliness)
   → 증거는 빨리 수집할수록 좋음
   → 네트워크 데이터는 휘발성 높음

4. 합법성 (Legality)
   → 캡처 권한 확인 (자사 네트워크)
   → 개인정보 처리 규정 준수
```

## 1.3 패킷 캡처 실습

```bash
# tcpdump로 패킷 캡처
# secu 서버(방화벽)에서 트래픽 캡처
sshpass -p1 ssh secu@10.20.30.1 << 'EOF'
echo "=== 네트워크 인터페이스 확인 ==="
ip link show | grep -E "^[0-9]+:" | awk '{print $2}' | tr -d ':'

echo ""
echo "=== 10초간 패킷 캡처 ==="
sudo timeout 10 tcpdump -i any -c 100 -w /tmp/capture.pcap \
  'net 10.20.30.0/24' 2>&1 || echo "캡처 완료"

echo ""
echo "=== 캡처 파일 정보 ==="
ls -la /tmp/capture.pcap 2>/dev/null
sudo tcpdump -r /tmp/capture.pcap -q 2>/dev/null | head -20

echo ""
echo "=== 해시값 기록 (증거 무결성) ==="
sha256sum /tmp/capture.pcap 2>/dev/null
EOF
```

> **명령어 해설**:
> - `tcpdump -i any`: 모든 인터페이스에서 캡처
> - `-c 100`: 100개 패킷만 캡처
> - `-w /tmp/capture.pcap`: PCAP 파일로 저장
> - `'net 10.20.30.0/24'`: BPF 필터 (내부 네트워크만)
>
> **트러블슈팅**:
> - "Permission denied" → sudo 필요
> - "No such device" → 인터페이스 이름 확인

---

# Part 2: tshark 심화 + 필터 (40분)

## 2.1 tshark 핵심 옵션

```bash
# tshark 기본 사용법
echo "=== tshark 버전 확인 ==="
tshark --version 2>/dev/null | head -1 || echo "tshark 미설치"

# 주요 옵션 정리
echo ""
echo "=== tshark 주요 옵션 ==="
cat << 'INFO'
-i <interface>    캡처 인터페이스
-r <file>         PCAP 파일 읽기
-w <file>         PCAP 파일 쓰기
-c <count>        패킷 수 제한
-f <filter>       캡처 필터 (BPF)
-Y <filter>       표시 필터 (display filter)
-T fields         필드 출력 모드
-e <field>        출력할 필드 지정
-q                통계 모드 (quiet)
-z <stat>         통계 유형 지정
INFO
```

## 2.2 Display Filter 심화

```
[IP 필터]
ip.addr == 10.20.30.80          # 특정 IP (src/dst)
ip.src == 10.20.30.80           # 출발지
ip.dst == 10.20.30.100          # 목적지
!(ip.addr == 10.20.30.0/24)    # 내부 IP 제외

[TCP 필터]
tcp.port == 80                   # 포트 (src/dst)
tcp.dstport == 443               # 목적지 포트
tcp.flags.syn == 1               # SYN 플래그
tcp.flags.rst == 1               # RST 플래그
tcp.analysis.retransmission      # 재전송 패킷

[HTTP 필터]
http.request.method == "POST"    # POST 요청
http.response.code == 200        # 200 응답
http.request.uri contains "admin"# URI에 admin 포함
http.host == "evil.com"          # 호스트 필터

[DNS 필터]
dns.qry.name contains "evil"    # DNS 쿼리 도메인
dns.qry.type == 1               # A 레코드 쿼리
dns.flags.response == 1          # DNS 응답

[TLS 필터]
tls.handshake.type == 1          # Client Hello
tls.handshake.extensions.server_name  # SNI
ssl.handshake.ciphersuite        # 암호 스위트

[조합]
(ip.src == 10.20.30.80) && (tcp.dstport == 443)
http.request || dns.qry.name
!(arp || dns || mdns)            # 노이즈 제거
```

## 2.3 tshark 통계 분석

```bash
# PCAP 파일 생성 (실습용)
sshpass -p1 ssh secu@10.20.30.1 << 'EOF'
sudo timeout 15 tcpdump -i any -c 500 -w /tmp/forensic.pcap \
  'net 10.20.30.0/24' 2>&1
ls -la /tmp/forensic.pcap 2>/dev/null
EOF

# PCAP 파일 복사
scp -o StrictHostKeyChecking=no secu@10.20.30.1:/tmp/forensic.pcap \
  /tmp/forensic.pcap 2>/dev/null

# tshark 통계 분석 (로컬 PCAP이 있는 경우)
if [ -f /tmp/forensic.pcap ]; then
    echo "=== 프로토콜 분포 ==="
    tshark -r /tmp/forensic.pcap -q -z io,phs 2>/dev/null | head -30

    echo ""
    echo "=== 대화 상위 10 ==="
    tshark -r /tmp/forensic.pcap -q -z conv,tcp 2>/dev/null | head -15

    echo ""
    echo "=== HTTP 요청 ==="
    tshark -r /tmp/forensic.pcap -Y "http.request" \
      -T fields -e ip.src -e http.request.method -e http.host -e http.request.uri \
      2>/dev/null | head -20

    echo ""
    echo "=== DNS 쿼리 ==="
    tshark -r /tmp/forensic.pcap -Y "dns.flags.response == 0" \
      -T fields -e ip.src -e dns.qry.name \
      2>/dev/null | sort | uniq -c | sort -rn | head -15
else
    echo "PCAP 파일 없음 - tshark 명령어 예시만 표시"
    echo ""
    echo "# 프로토콜 분포"
    echo "tshark -r capture.pcap -q -z io,phs"
    echo ""
    echo "# TCP 대화 통계"
    echo "tshark -r capture.pcap -q -z conv,tcp"
    echo ""
    echo "# HTTP 요청 추출"
    echo "tshark -r capture.pcap -Y 'http.request' -T fields -e ip.src -e http.host -e http.request.uri"
fi
```

> **결과 해석**: 프로토콜 분포에서 비정상적인 프로토콜(IRC, 비표준 포트)이 보이면 C2 통신 가능성. DNS 쿼리에서 알 수 없는 도메인이 반복되면 비콘 패턴 의심.

---

# Part 3: PCAP 분석 실습 (50분)

## 3.1 실시간 트래픽 캡처 + 분석

> **실습 목적**: 실습 환경의 실시간 트래픽을 캡처하고 분석하여 네트워크 포렌식 기법을 익힌다.
>
> **배우는 것**: tcpdump/tshark 실전 활용, BPF 필터, 트래픽 패턴 분석

```bash
# 웹서버로 트래픽을 발생시키면서 캡처
echo "=== Step 1: 트래픽 발생 ==="
# 백그라운드로 웹 요청 생성
for i in $(seq 1 10); do
    curl -s -o /dev/null http://10.20.30.80/ 2>/dev/null &
    curl -s -o /dev/null "http://10.20.30.80/api/test?id=1 OR 1=1" 2>/dev/null &
done
wait

echo ""
echo "=== Step 2: secu에서 캡처된 트래픽 분석 ==="
sshpass -p1 ssh secu@10.20.30.1 << 'REMOTE'
# 방화벽에서 최근 패킷 분석
if [ -f /tmp/forensic.pcap ]; then
    echo "--- IP 주소별 패킷 수 ---"
    sudo tcpdump -r /tmp/forensic.pcap -nn 2>/dev/null | \
      awk '{print $3}' | cut -d. -f1-4 | sort | uniq -c | sort -rn | head -10
    
    echo ""
    echo "--- 포트별 분포 ---"
    sudo tcpdump -r /tmp/forensic.pcap -nn 'tcp' 2>/dev/null | \
      awk '{print $5}' | rev | cut -d. -f1 | rev | sort | uniq -c | sort -rn | head -10
    
    echo ""
    echo "--- SYN 스캔 탐지 (SYN without ACK) ---"
    sudo tcpdump -r /tmp/forensic.pcap 'tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) == 0' -nn 2>/dev/null | wc -l
    echo "건 (SYN-only 패킷)"
fi
REMOTE
```

## 3.2 C2 비콘 패턴 분석

```bash
cat << 'SCRIPT' > /tmp/detect_beacon.py
#!/usr/bin/env python3
"""C2 비콘 패턴 탐지 시뮬레이션"""
import random
import statistics
from datetime import datetime, timedelta

# C2 비콘 시뮬레이션 데이터
# 정상 트래픽: 랜덤 간격
normal_intervals = [random.uniform(1, 600) for _ in range(20)]

# C2 비콘: 일정한 간격 (~60초 + 약간의 지터)
c2_intervals = [60 + random.uniform(-3, 3) for _ in range(20)]

def analyze_intervals(name, intervals):
    mean = statistics.mean(intervals)
    stdev = statistics.stdev(intervals)
    cv = stdev / mean  # 변동 계수 (Coefficient of Variation)
    
    print(f"\n--- {name} ---")
    print(f"  평균 간격: {mean:.1f}초")
    print(f"  표준편차:  {stdev:.1f}초")
    print(f"  변동계수:  {cv:.3f}")
    
    if cv < 0.1:
        print(f"  [경고] 매우 규칙적 → C2 비콘 가능성 높음!")
    elif cv < 0.3:
        print(f"  [주의] 비교적 규칙적 → 추가 분석 필요")
    else:
        print(f"  [정상] 불규칙적 → 정상 트래픽 패턴")

print("=" * 50)
print("  C2 비콘 패턴 분석")
print("=" * 50)

analyze_intervals("정상 HTTP 트래픽", normal_intervals)
analyze_intervals("C2 비콘 의심 트래픽", c2_intervals)

print("\n=== 탐지 기준 ===")
print("  변동계수(CV) < 0.1: C2 비콘 가능성 매우 높음")
print("  변동계수(CV) < 0.3: 추가 분석 필요")
print("  변동계수(CV) > 0.3: 정상 트래픽")
SCRIPT

python3 /tmp/detect_beacon.py
```

> **배우는 것**: C2 통신의 특징인 "일정한 간격의 비콘"을 통계적으로 탐지하는 방법. 변동계수(CV)가 낮을수록 규칙적인 통신으로 C2 의심도가 높다.

## 3.3 DNS 터널링 탐지

```bash
cat << 'SCRIPT' > /tmp/detect_dns_tunnel.py
#!/usr/bin/env python3
"""DNS 터널링 탐지"""
import random
import string

# 정상 DNS 쿼리
normal_dns = [
    "www.google.com", "mail.naver.com", "api.github.com",
    "cdn.example.com", "update.microsoft.com",
]

# DNS 터널링 쿼리 (긴 서브도메인, 인코딩된 데이터)
tunnel_dns = [
    f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=50))}.evil.example.com"
    for _ in range(5)
]

print("=" * 60)
print("  DNS 터널링 탐지 분석")
print("=" * 60)

print("\n--- 정상 DNS 쿼리 ---")
for q in normal_dns:
    labels = q.split('.')
    max_label = max(len(l) for l in labels)
    entropy = len(set(q)) / len(q)
    print(f"  {q:40s} 최대라벨: {max_label:2d}자 엔트로피: {entropy:.3f}")

print("\n--- DNS 터널링 의심 쿼리 ---")
for q in tunnel_dns:
    labels = q.split('.')
    max_label = max(len(l) for l in labels)
    entropy = len(set(q)) / len(q)
    flag = "[경고]" if max_label > 30 or entropy > 0.6 else ""
    print(f"  {q[:40]:40s}... 최대라벨: {max_label:2d}자 엔트로피: {entropy:.3f} {flag}")

print("\n=== 탐지 기준 ===")
print("  라벨 길이 > 30자: DNS 터널링 의심")
print("  쿼리 엔트로피 > 0.6: 인코딩된 데이터 의심")
print("  단일 도메인 쿼리 빈도 > 100/분: 비정상")
SCRIPT

python3 /tmp/detect_dns_tunnel.py
```

## 3.4 HTTP 페이로드 분석

```bash
# tshark로 HTTP 요청/응답 상세 분석
echo "=== HTTP 페이로드 분석 명령어 ==="

cat << 'INFO'
# HTTP POST 요청 본문 추출
tshark -r capture.pcap -Y "http.request.method == POST" \
  -T fields -e ip.src -e http.host -e http.request.uri \
  -e http.file_data

# HTTP 응답에서 파일 다운로드 추출
tshark -r capture.pcap --export-objects http,/tmp/http_objects/

# SQL Injection 시도 탐지
tshark -r capture.pcap -Y "http.request.uri contains \"OR 1=1\" || http.request.uri contains \"UNION SELECT\"" \
  -T fields -e ip.src -e http.request.uri

# User-Agent 분석 (비정상 UA 탐지)
tshark -r capture.pcap -Y "http.request" \
  -T fields -e http.user_agent | sort | uniq -c | sort -rn

# 대용량 응답 탐지 (데이터 유출 의심)
tshark -r capture.pcap -Y "http.response and http.content_length > 1000000" \
  -T fields -e ip.src -e ip.dst -e http.content_length
INFO
```

---

# Part 4: 프로토콜 심화 분석 + 자동화 (40분)

## 4.1 TLS 핸드셰이크 분석

```bash
cat << 'SCRIPT' > /tmp/tls_analysis.py
#!/usr/bin/env python3
"""TLS 핸드셰이크 분석 포인트"""

analysis_points = [
    {
        "항목": "SNI (Server Name Indication)",
        "정상": "알려진 도메인 (google.com, naver.com)",
        "의심": "IP 직접 접속, DGA 도메인, 무료 TLD (.tk, .ml)",
        "tshark": "tshark -r cap.pcap -Y 'tls.handshake.type==1' -T fields -e tls.handshake.extensions_server_name"
    },
    {
        "항목": "JA3 해시 (TLS 핑거프린트)",
        "정상": "알려진 브라우저/앱 JA3",
        "의심": "알려진 악성코드 JA3 매칭",
        "tshark": "tshark -r cap.pcap -Y 'tls.handshake.type==1' -T fields -e tls.handshake.ja3"
    },
    {
        "항목": "인증서 발급자",
        "정상": "알려진 CA (DigiCert, Let's Encrypt)",
        "의심": "자체 서명, 알 수 없는 CA",
        "tshark": "tshark -r cap.pcap -Y 'tls.handshake.type==11' -T fields -e x509ce.dNSName"
    },
    {
        "항목": "TLS 버전",
        "정상": "TLS 1.2 / 1.3",
        "의심": "TLS 1.0, SSL 3.0 (구형)",
        "tshark": "tshark -r cap.pcap -Y 'tls.handshake.type==1' -T fields -e tls.handshake.version"
    },
]

print("=" * 60)
print("  TLS 핸드셰이크 분석 가이드")
print("=" * 60)

for point in analysis_points:
    print(f"\n--- {point['항목']} ---")
    print(f"  정상: {point['정상']}")
    print(f"  의심: {point['의심']}")
    print(f"  명령: {point['tshark']}")
SCRIPT

python3 /tmp/tls_analysis.py
```

## 4.2 Suricata PCAP 분석

```bash
# Suricata로 PCAP 파일 분석
sshpass -p1 ssh secu@10.20.30.1 << 'REMOTE'
if [ -f /tmp/forensic.pcap ]; then
    echo "=== Suricata 오프라인 PCAP 분석 ==="
    sudo suricata -r /tmp/forensic.pcap -l /tmp/suricata_analysis/ \
      --set outputs.0.fast.enabled=yes 2>/dev/null
    
    echo ""
    echo "--- Suricata 탐지 결과 ---"
    cat /tmp/suricata_analysis/fast.log 2>/dev/null | head -20 || echo "(탐지 없음)"
    
    echo ""
    echo "--- EVE JSON 로그 ---"
    cat /tmp/suricata_analysis/eve.json 2>/dev/null | \
      python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            print(f\"  Alert: {e['alert']['signature']} ({e['src_ip']}:{e.get('src_port','')} -> {e['dest_ip']}:{e.get('dest_port','')})\")
    except: pass
" | head -10 || echo "(EVE 로그 없음)"
    
    rm -rf /tmp/suricata_analysis/
else
    echo "캡처 파일 없음"
fi
REMOTE
```

## 4.3 OpsClaw 자동화 네트워크 분석

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "network-forensics",
    "request_text": "네트워크 트래픽 포렌식 분석",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 전체 서버 네트워크 상태 수집
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "ss -tnp 2>/dev/null | grep ESTAB | wc -l && ss -tnp 2>/dev/null | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "ss -tnp 2>/dev/null | grep ESTAB | wc -l && ss -tnp 2>/dev/null | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

## 4.4 네트워크 포렌식 타임라인

```bash
cat << 'SCRIPT' > /tmp/network_timeline.py
#!/usr/bin/env python3
"""네트워크 포렌식 타임라인 생성"""
from datetime import datetime, timedelta

events = [
    {"time": "02:00:00", "type": "SCAN", "src": "203.0.113.50", "dst": "10.20.30.80",
     "detail": "포트 스캔 (22,80,443,3306,8080)"},
    {"time": "02:05:23", "type": "ATTACK", "src": "203.0.113.50", "dst": "10.20.30.80:80",
     "detail": "SQL Injection 시도 (/api/products?id=1 OR 1=1)"},
    {"time": "02:05:45", "type": "ATTACK", "src": "203.0.113.50", "dst": "10.20.30.80:80",
     "detail": "웹셸 업로드 시도 (POST /upload shell.php)"},
    {"time": "02:06:10", "type": "ACCESS", "src": "203.0.113.50", "dst": "10.20.30.80:80",
     "detail": "웹셸 접근 (GET /uploads/shell.php?cmd=id)"},
    {"time": "02:06:30", "type": "C2", "src": "10.20.30.80", "dst": "203.0.113.50:4444",
     "detail": "리버스 셸 연결 (TCP SYN)"},
    {"time": "02:07:00", "type": "LATERAL", "src": "10.20.30.80", "dst": "10.20.30.100:22",
     "detail": "내부 SSH 접근 시도"},
    {"time": "02:10:00", "type": "EXFIL", "src": "10.20.30.100", "dst": "203.0.113.50:443",
     "detail": "대량 데이터 전송 (15MB TLS)"},
    {"time": "02:15:00", "type": "DETECT", "src": "10.20.30.100", "dst": "-",
     "detail": "Wazuh 경보: 비정상 아웃바운드 트래픽"},
]

print("=" * 80)
print("  네트워크 포렌식 타임라인")
print("=" * 80)
print(f"\n{'시각':>10s} {'유형':>8s} {'출발지':>16s} → {'목적지':>20s}  설명")
print("-" * 80)

for e in events:
    type_color = {
        "SCAN": "SCAN", "ATTACK": "ATTACK", "ACCESS": "ACCESS",
        "C2": "C2", "LATERAL": "LATERAL", "EXFIL": "EXFIL", "DETECT": "DETECT"
    }
    print(f"{e['time']:>10s} [{e['type']:>7s}] {e['src']:>16s} → {e['dst']:>20s}  {e['detail']}")

print("\n=== Kill Chain 매핑 ===")
print("  정찰(02:00) → 무기화+침투(02:05) → 설치(02:06)")
print("  → C2(02:06) → 측면이동(02:07) → 유출(02:10) → 탐지(02:15)")
SCRIPT

python3 /tmp/network_timeline.py
```

---

## 체크리스트

- [ ] 네트워크 포렌식의 3가지 데이터 유형(PCAP/Flow/Log)을 구분할 수 있다
- [ ] 증거 수집 4원칙(무결성, 연속성, 적시성, 합법성)을 알고 있다
- [ ] tcpdump로 패킷을 캡처하고 BPF 필터를 적용할 수 있다
- [ ] tshark display filter를 사용하여 패킷을 필터링할 수 있다
- [ ] tshark 통계 기능(-z)으로 트래픽 분석을 할 수 있다
- [ ] C2 비콘 패턴을 통계적으로 탐지할 수 있다
- [ ] DNS 터널링의 특징을 알고 탐지할 수 있다
- [ ] TLS 핸드셰이크 분석 포인트(SNI, JA3, 인증서)를 알고 있다
- [ ] Suricata로 PCAP 오프라인 분석을 수행할 수 있다
- [ ] 네트워크 포렌식 타임라인을 구성할 수 있다

---

## 복습 퀴즈

**Q1.** PCAP과 NetFlow의 차이와 각각의 장단점을 설명하시오.

<details><summary>정답</summary>
PCAP: 패킷 전체 내용을 기록. 장점: 페이로드까지 분석 가능. 단점: 용량이 크고 장기 보관 어려움. NetFlow: 세션 메타데이터만 기록. 장점: 용량 작고 장기 보관 가능. 단점: 패킷 내용을 볼 수 없음.
</details>

**Q2.** BPF 필터 `tcp port 80 and host 10.20.30.80`의 의미는?

<details><summary>정답</summary>
TCP 포트 80(HTTP)이면서 IP 주소가 10.20.30.80인 패킷만 캡처한다. host는 src/dst 모두 해당한다.
</details>

**Q3.** C2 비콘의 변동계수(CV)가 0.05라면 어떤 의미인가?

<details><summary>정답</summary>
통신 간격이 매우 규칙적이라는 의미로, C2 비콘 가능성이 매우 높다. CV < 0.1은 인간이 아닌 자동화된 프로그램의 통신 패턴이다.
</details>

**Q4.** DNS 터널링을 탐지하는 3가지 지표를 나열하시오.

<details><summary>정답</summary>
1) 비정상적으로 긴 서브도메인(30자 이상), 2) 높은 쿼리 엔트로피(인코딩된 데이터), 3) 단일 도메인에 대한 과도한 쿼리 빈도.
</details>

**Q5.** JA3 해시의 용도를 설명하시오.

<details><summary>정답</summary>
TLS Client Hello 메시지의 특정 필드(버전, 암호 스위트, 확장 등)를 해시하여 클라이언트 소프트웨어를 핑거프린팅하는 기법이다. 동일한 악성코드는 동일한 JA3 해시를 생성하므로 IOC로 활용할 수 있다.
</details>

**Q6.** tshark -T fields -e ip.src -e http.host의 출력 의미는?

<details><summary>정답</summary>
각 패킷에서 출발지 IP와 HTTP Host 헤더만 추출하여 탭으로 구분하여 출력한다. 대량 PCAP에서 특정 필드만 빠르게 추출할 때 유용하다.
</details>

**Q7.** 네트워크 포렌식에서 "증거 연속성(Chain of Custody)"이 중요한 이유는?

<details><summary>정답</summary>
법적 증거로 사용하려면 증거가 수집된 후 누가 언제 접근했는지 추적 가능해야 한다. 연속성이 끊기면 증거가 변조되었을 가능성이 있어 법정에서 증거 능력을 잃는다.
</details>

**Q8.** Suricata의 오프라인 PCAP 분석이 유용한 경우는?

<details><summary>정답</summary>
1) 사후 분석: 사고 후 수집된 PCAP을 최신 IDS 룰로 재분석, 2) 새 룰 테스트: 새 탐지 룰을 과거 트래픽에 적용하여 효과 검증, 3) 교육: 실제 공격 PCAP으로 분석 훈련.
</details>

**Q9.** 자체 서명 TLS 인증서가 발견되면 어떤 추가 분석이 필요한가?

<details><summary>정답</summary>
1) 목적지 IP/도메인 확인, 2) 트래픽 빈도와 패턴(비콘 여부) 분석, 3) SNI와 실제 인증서 도메인 불일치 확인, 4) 해당 IP의 IOC 조회, 5) 내부 서비스의 정상 자체 서명인지 확인.
</details>

**Q10.** Kill Chain의 7단계를 네트워크 포렌식 관점에서 설명하시오.

<details><summary>정답</summary>
1) 정찰: 포트 스캔 패킷, 2) 무기화: 악성 페이로드 다운로드, 3) 전달: 피싱 이메일/악성 URL, 4) 익스플로잇: 취약점 공격 패킷, 5) 설치: 악성코드 다운로드 트래픽, 6) C2: 비콘 통신, 7) 행동: 데이터 유출 트래픽.
</details>

---

## 과제

### 과제 1: 트래픽 캡처 + 분석 (필수)

실습 환경에서 15분간 트래픽을 캡처하고:
1. 프로토콜 분포 분석
2. 상위 통신 쌍(conversation) 식별
3. 비정상 패턴 1개 이상 식별
4. 네트워크 포렌식 타임라인 작성

### 과제 2: C2 통신 탐지 (선택)

시뮬레이션된 C2 비콘 패턴을 생성하고:
1. tshark로 비콘 간격 추출
2. 변동계수로 규칙성 분석
3. DNS/HTTP/TLS 관점 분석
4. Suricata 탐지 룰 작성

---

## 보충: NetFlow 분석 + 고급 tshark 활용

### NetFlow 데이터 시뮬레이션 분석

```bash
cat << 'SCRIPT' > /tmp/netflow_analysis.py
#!/usr/bin/env python3
"""NetFlow 데이터 분석 시뮬레이션"""
import random
from datetime import datetime, timedelta
from collections import defaultdict

# NetFlow 레코드 시뮬레이션
flows = []
base_time = datetime(2026, 4, 4, 10, 0, 0)

# 정상 트래픽
for i in range(50):
    flows.append({
        "start": base_time + timedelta(seconds=random.randint(0, 3600)),
        "src": "10.20.30.201",
        "dst": f"10.20.30.{random.choice([1, 80, 100])}",
        "sport": random.randint(32768, 65535),
        "dport": random.choice([22, 80, 443, 8000]),
        "bytes": random.randint(100, 50000),
        "packets": random.randint(1, 100),
        "protocol": "TCP",
    })

# 의심 트래픽: C2 비콘
for i in range(20):
    flows.append({
        "start": base_time + timedelta(seconds=60 * i + random.randint(-2, 2)),
        "src": "10.20.30.80",
        "dst": "203.0.113.50",
        "sport": random.randint(32768, 65535),
        "dport": 443,
        "bytes": random.randint(200, 500),
        "packets": random.randint(3, 8),
        "protocol": "TCP",
    })

# 의심 트래픽: 대량 데이터 전송
flows.append({
    "start": base_time + timedelta(seconds=1800),
    "src": "10.20.30.100",
    "dst": "203.0.113.50",
    "sport": 54321,
    "dport": 443,
    "bytes": 15_000_000,  # 15MB
    "packets": 10000,
    "protocol": "TCP",
})

print("=" * 70)
print("  NetFlow 분석 결과")
print("=" * 70)

# 1. 상위 통신량 쌍
print("\n--- 상위 통신량 (바이트 기준) ---")
pair_bytes = defaultdict(int)
for f in flows:
    key = f"{f['src']} → {f['dst']}:{f['dport']}"
    pair_bytes[key] += f['bytes']

for pair, total in sorted(pair_bytes.items(), key=lambda x: -x[1])[:10]:
    mb = total / 1_000_000
    print(f"  {pair:45s} {mb:8.2f} MB")

# 2. 외부 IP 통신
print("\n--- 외부 IP 통신 ---")
external_flows = [f for f in flows if not f['dst'].startswith('10.')]
for f in sorted(external_flows, key=lambda x: -x['bytes'])[:5]:
    print(f"  {f['src']:16s} → {f['dst']:16s}:{f['dport']} "
          f"({f['bytes']:>10,} bytes, {f['packets']} pkts)")

# 3. 비콘 패턴 탐지
print("\n--- 비콘 패턴 분석 ---")
beacon_flows = [f for f in flows if f['dst'] == '203.0.113.50' and f['bytes'] < 1000]
if len(beacon_flows) > 5:
    intervals = []
    sorted_beacons = sorted(beacon_flows, key=lambda x: x['start'])
    for i in range(1, len(sorted_beacons)):
        diff = (sorted_beacons[i]['start'] - sorted_beacons[i-1]['start']).total_seconds()
        intervals.append(diff)
    
    import statistics
    mean_interval = statistics.mean(intervals)
    stdev_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
    cv = stdev_interval / mean_interval if mean_interval > 0 else 0
    
    print(f"  10.20.30.80 → 203.0.113.50:443")
    print(f"  플로우 수: {len(beacon_flows)}개")
    print(f"  평균 간격: {mean_interval:.1f}초")
    print(f"  변동계수: {cv:.3f}")
    if cv < 0.1:
        print(f"  [경고] 매우 규칙적 통신 → C2 비콘 의심!")
    
# 4. 대량 전송 탐지
print("\n--- 대량 데이터 전송 (1MB 이상) ---")
large_flows = [f for f in flows if f['bytes'] > 1_000_000]
for f in large_flows:
    mb = f['bytes'] / 1_000_000
    print(f"  [경고] {f['src']} → {f['dst']}:{f['dport']} ({mb:.1f} MB)")
    print(f"          → 데이터 유출 의심!")
SCRIPT

python3 /tmp/netflow_analysis.py
```

> **결과 해석**: NetFlow에서 외부 IP로의 규칙적 소량 통신(비콘)과 대량 전송(유출)을 식별하는 것이 핵심이다. PCAP 없이도 Flow 데이터만으로 C2/유출을 탐지할 수 있다.

### tshark 고급 통계 활용

```bash
echo "=== tshark 고급 통계 명령어 ==="

cat << 'INFO'
# 1. 시간대별 트래픽 분포 (1분 단위)
tshark -r capture.pcap -q -z io,stat,60

# 2. HTTP 요청 메서드 분포
tshark -r capture.pcap -q -z http,tree

# 3. DNS 도메인별 쿼리 수
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head -20

# 4. TLS SNI(Server Name) 목록
tshark -r capture.pcap -Y "tls.handshake.type == 1" \
  -T fields -e tls.handshake.extensions_server_name | sort -u

# 5. TCP 재전송 분석 (네트워크 이상)
tshark -r capture.pcap -q -z io,stat,10,"tcp.analysis.retransmission"

# 6. 특정 IP의 세션 추적
tshark -r capture.pcap -Y "ip.addr == 203.0.113.50" \
  -T fields -e frame.time -e ip.src -e ip.dst -e tcp.dstport -e frame.len

# 7. HTTP 응답 크기 Top 10 (데이터 유출 탐지)
tshark -r capture.pcap -Y "http.response" \
  -T fields -e ip.dst -e http.content_length | \
  sort -t$'\t' -k2 -rn | head -10

# 8. 비표준 포트 HTTP 트래픽
tshark -r capture.pcap -Y "http && !(tcp.port == 80 || tcp.port == 443 || tcp.port == 8080)"

# 9. ICMP 터널링 의심
tshark -r capture.pcap -Y "icmp && frame.len > 100" \
  -T fields -e ip.src -e ip.dst -e frame.len

# 10. 패킷 크기 분포
tshark -r capture.pcap -T fields -e frame.len | \
  sort -n | uniq -c | sort -rn | head -15
INFO
```

> **실전 활용**: 위 명령어를 스크립트로 묶어 "네트워크 포렌식 초기 분석 킷"으로 사용할 수 있다. 새 PCAP을 받으면 이 스크립트를 먼저 실행하여 전체 윤곽을 파악한 후 세부 분석에 진입한다.

### HTTP 객체 추출 + 파일 분석

```bash
echo "=== HTTP 객체 추출 기법 ==="

cat << 'INFO'
# tshark로 HTTP 파일 추출
tshark -r capture.pcap --export-objects http,/tmp/http_export/
ls -la /tmp/http_export/

# 추출된 파일 유형 확인
file /tmp/http_export/*

# 추출된 파일 해시 계산
sha256sum /tmp/http_export/*

# 의심 파일 YARA 스캔
yara /path/to/rules.yar /tmp/http_export/

# SMB 파일 추출 (내부 측면 이동 시)
tshark -r capture.pcap --export-objects smb,/tmp/smb_export/

# FTP 전송 파일 추출
tshark -r capture.pcap -Y "ftp-data" \
  -T fields -e tcp.payload > /tmp/ftp_data.bin
INFO

echo ""
echo "→ HTTP 객체 추출은 웹셸 다운로드, 악성코드 전달 등을 확인하는 핵심 기법이다."
```

### 포렌식 PCAP 보고서 자동 생성

```bash
cat << 'SCRIPT' > /tmp/pcap_report.py
#!/usr/bin/env python3
"""네트워크 포렌식 PCAP 분석 보고서 자동 생성"""

report = {
    "case_id": "NF-2026-0404-001",
    "pcap_file": "capture_secu_20260404.pcap",
    "capture_start": "2026-04-04 10:00:00",
    "capture_end": "2026-04-04 10:15:00",
    "total_packets": 15234,
    "total_bytes": 8_543_210,
    "protocols": {
        "TCP": 12500, "UDP": 2200, "ICMP": 300, "ARP": 234
    },
    "top_talkers": [
        ("10.20.30.201", "10.20.30.80", 3500),
        ("10.20.30.80", "203.0.113.50", 1200),
        ("10.20.30.201", "10.20.30.100", 800),
    ],
    "findings": [
        {"severity": "Critical", "finding": "10.20.30.80 → 203.0.113.50:443 규칙적 통신 (비콘 의심)"},
        {"severity": "High", "finding": "10.20.30.100 → 203.0.113.50:443 15MB 대량 전송 (유출 의심)"},
        {"severity": "Medium", "finding": "203.0.113.50 → 10.20.30.80:80 SQL Injection 패턴"},
    ],
}

print("=" * 60)
print(f"  네트워크 포렌식 분석 보고서")
print(f"  Case: {report['case_id']}")
print("=" * 60)

print(f"\n파일: {report['pcap_file']}")
print(f"기간: {report['capture_start']} ~ {report['capture_end']}")
print(f"패킷: {report['total_packets']:,}개 / {report['total_bytes']:,} bytes")

print(f"\n프로토콜 분포:")
for proto, count in report['protocols'].items():
    pct = count / report['total_packets'] * 100
    bar = '#' * int(pct / 2)
    print(f"  {proto:6s}: {count:6d} ({pct:5.1f}%) {bar}")

print(f"\n상위 통신 쌍:")
for src, dst, count in report['top_talkers']:
    print(f"  {src:16s} → {dst:16s}: {count:,} 패킷")

print(f"\n발견 사항:")
for f in report['findings']:
    print(f"  [{f['severity']:8s}] {f['finding']}")
SCRIPT

python3 /tmp/pcap_report.py
```

---

## 다음 주 예고

**Week 08: 메모리 포렌식**에서는 Volatility3를 사용하여 메모리 덤프에서 악성 프로세스, 인젝션, 루트킷을 탐지하는 방법을 학습한다.
