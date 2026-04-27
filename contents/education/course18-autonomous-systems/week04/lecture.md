# Week 04: 드론 방어 — 드론 탐지, RF 분석, 지오펜싱

## 학습 목표
- 드론 탐지 기술(RF, 레이더, 음향, 영상)의 원리를 이해한다
- RF 신호 분석을 통한 드론 식별 기법을 실습할 수 있다
- 지오펜싱의 구현 원리와 우회 가능성을 분석할 수 있다
- 드론 통신 보안 강화 방안을 구현할 수 있다
- 안티드론 시스템의 종류와 한계를 평가할 수 있다

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
| 0:00-0:30 | 이론: 드론 탐지 기술 개요 (Part 1) | 강의 |
| 0:30-1:00 | 이론: 지오펜싱과 안티드론 시스템 (Part 2) | 강의/토론 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: RF 신호 분석 시뮬레이션 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 지오펜싱 구현 및 우회 분석 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 드론 IDS 구축 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: 드론 탐지 기술 개요 (0:00-0:30)

### 1.1 드론 탐지 기술 분류

```
드론 탐지 기술
│
├── RF 탐지 (Radio Frequency)
│   ├── 주파수 스캐닝 (2.4GHz, 5.8GHz)
│   ├── 시그니처 매칭 (프로토콜 핑거프린팅)
│   └── 방향 탐지 (Direction Finding)
│
├── 레이더 탐지
│   ├── 마이크로 도플러 분석
│   ├── 소형 목표 탐지 레이더
│   └── FMCW 레이더
│
├── 음향 탐지
│   ├── 프로펠러 음향 시그니처
│   ├── 마이크 어레이
│   └── 기계학습 분류
│
├── 영상/광학 탐지
│   ├── CCTV + AI 객체 탐지
│   ├── 적외선 카메라
│   └── YOLO/SSD 기반 실시간 탐지
│
└── 융합 탐지 (Sensor Fusion)
    └── RF + 레이더 + 음향 + 영상 통합
```

### 1.2 RF 탐지 원리

| 주파수 대역 | 용도 | 탐지 대상 |
|------------|------|-----------|
| 2.4 GHz | WiFi 제어 | 소비자 드론 (DJI, Parrot) |
| 5.8 GHz | FPV 영상, WiFi 5G | 레이싱 드론, 고급 상용 |
| 900 MHz | 장거리 제어 | 군사/산업용 |
| 1575.42 MHz | GPS L1 | GPS 수신기 |
| 433 MHz | RC 제어 | 저가 RC 드론 |

### 1.3 안티드론 대응 기술

```
안티드론 대응
│
├── 소프트 킬 (Soft Kill)
│   ├── RF 재밍 → 드론 통신 차단 → RTL/착륙
│   ├── GPS 스푸핑 → 위치 혼란 → 유도
│   └── 프로토콜 해킹 → 제어권 탈취
│
├── 하드 킬 (Hard Kill)
│   ├── 레이저 무기
│   ├── 그물/포획 드론
│   └── 재래식 사격
│
└── 규제적 대응
    ├── 지오펜싱 (소프트웨어)
    ├── 비행 금지 구역 DB
    └── 원격 ID (Remote ID)
```

---

## Part 2: 지오펜싱과 안티드론 시스템 (0:30-1:00)

### 2.1 지오펜싱 원리

```
지오펜싱 (Geofencing)
┌────────────────────────────────────────┐
│         ┌──────────────────┐           │
│         │  비행 금지 구역   │           │
│         │  (공항, 군사지역) │           │
│         │                  │           │
│    ──▶  │  ╳ 진입 불가     │ ◀──       │
│  드론   │                  │  드론      │
│  접근   └──────────────────┘  접근      │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  지오펜스 경계 (위도/경도 다각형) │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘

동작 원리:
1. 드론 GPS로 현재 위치 확인
2. 위치를 지오펜스 DB와 비교
3. 금지 구역 접근 시: 진입 거부 / 자동 회피
4. 이미 진입한 경우: 강제 착륙 / RTL
```

### 2.2 지오펜싱의 한계

| 우회 방법 | 설명 | 난이도 |
|-----------|------|--------|
| GPS 스푸핑 | 가짜 GPS 신호로 드론 위치를 속임 | 중 |
| 펌웨어 수정 | 지오펜싱 코드를 제거/비활성화 | 고 |
| 오픈소스 FC | 지오펜싱 없는 FC 사용 | 하 |
| GPS 차단 | GPS 신호를 차단하여 위치 확인 불가 | 중 |

### 2.3 원격 ID (Remote ID)

```
Remote ID 시스템
┌──────────┐    브로드캐스트    ┌──────────────┐
│  드론    │ ──────────────▶  │  수신기/앱    │
│          │  (BLE/WiFi)      │              │
│ ID: ABC  │                  │ 드론 ID: ABC │
│ 위치     │                  │ 위치 확인    │
│ 고도     │                  │ 소유자 조회  │
│ 속도     │                  │              │
└──────────┘                  └──────────────┘
```

---

## Part 3: RF 신호 분석 시뮬레이션 (1:10-1:50)

### 3.1 가상 RF 스펙트럼 분석

```bash
python3 << 'PYEOF'
import random
import time

print("=" * 65)
print("  RF Spectrum Analyzer - Drone Detection Simulation")
print("=" * 65)
print()

# 2.4GHz 대역 시뮬레이션
channels = {
    1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432,
    6: 2437, 7: 2442, 8: 2447, 9: 2452, 10: 2457,
    11: 2462
}

# 배경 노이즈 + 드론 신호 시뮬레이션
print("[2.4 GHz Band Scan]")
print(f"{'CH':>3} {'Freq':>6} {'Power':>8} {'Signal':>40} {'Detection'}")
print("-" * 65)

drone_channels = [6, 7]  # 드론이 사용하는 채널

for ch, freq in channels.items():
    if ch in drone_channels:
        power = random.randint(-45, -35)
        bar = "#" * (90 + power)
        detection = "<< DRONE SIGNAL"
    else:
        power = random.randint(-85, -70)
        bar = "#" * (90 + power)
        detection = ""

    print(f"{ch:>3} {freq:>5}MHz {power:>5} dBm  {bar:<40} {detection}")

print()
print("[Analysis Results]")
print(f"  Detected drone signal on channels: {drone_channels}")
print(f"  Protocol signature: WiFi (802.11n)")
print(f"  Estimated distance: 50-100m")
print(f"  Signal pattern: Consistent with DJI/Parrot drone")

# 시그니처 매칭
print()
print("[Protocol Fingerprinting]")
signatures = {
    "DJI Phantom": {"freq": "2.4GHz", "pattern": "OFDM, 20MHz BW", "ports": "2233, 9003"},
    "Parrot AR.Drone": {"freq": "2.4GHz", "pattern": "WiFi AP mode", "ports": "5556, 5554"},
    "ArduPilot": {"freq": "2.4GHz/433MHz", "pattern": "MAVLink UDP", "ports": "14550, 14555"},
}
for name, sig in signatures.items():
    print(f"  {name}: freq={sig['freq']}, pattern={sig['pattern']}")
PYEOF
```

### 3.2 네트워크 기반 드론 탐지

```bash
# 네트워크에서 드론 관련 서비스 탐지
nmap -sV -p 5556,5554,14550,9999,2233,9003 10.20.30.0/24 2>/dev/null

# 드론 OUI(MAC 벤더) 확인 시뮬레이션
python3 -c "
drone_ouis = {
    '60:60:1F': 'DJI Technology',
    'A0:14:3D': 'Parrot SA',
    '90:03:B7': 'Parrot SA',
    '00:12:1C': 'Parrot SA',
    '00:26:7E': '3DR (3D Robotics)',
}
print('=== Drone OUI Database ===')
for oui, vendor in drone_ouis.items():
    print(f'  {oui} -> {vendor}')
print()
print('[*] Checking ARP table for drone MACs...')
print('[SIM] No physical drones on network (virtual lab)')
"
```

---

## Part 4: 지오펜싱 구현 및 우회 분석 (1:50-2:30)

### 4.1 Python 지오펜싱 구현

```bash
python3 << 'PYEOF'
import math
import json

class Geofence:
    """다각형 기반 지오펜싱 시스템"""

    def __init__(self):
        self.zones = {}

    def add_zone(self, name, polygon, zone_type="no_fly"):
        """비행 금지 구역 추가 (polygon: [(lat, lon), ...])"""
        self.zones[name] = {"polygon": polygon, "type": zone_type}

    def point_in_polygon(self, lat, lon, polygon):
        """Ray Casting 알고리즘으로 점이 다각형 내부인지 확인"""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            if ((polygon[i][1] > lon) != (polygon[j][1] > lon) and
                lat < (polygon[j][0] - polygon[i][0]) * (lon - polygon[i][1]) /
                (polygon[j][1] - polygon[i][1]) + polygon[i][0]):
                inside = not inside
            j = i
        return inside

    def check_position(self, lat, lon):
        """현재 위치가 금지 구역에 있는지 확인"""
        violations = []
        for name, zone in self.zones.items():
            if self.point_in_polygon(lat, lon, zone["polygon"]):
                violations.append(name)
        return violations

# 지오펜싱 시스템 구성
gf = Geofence()

# 비행 금지 구역 등록 (서울 주요 시설)
gf.add_zone("Incheon Airport", [
    (37.44, 126.43), (37.48, 126.43),
    (37.48, 126.47), (37.44, 126.47)
])
gf.add_zone("Blue House", [
    (37.585, 126.974), (37.590, 126.974),
    (37.590, 126.980), (37.585, 126.980)
])
gf.add_zone("Military Base", [
    (37.50, 126.90), (37.52, 126.90),
    (37.52, 126.93), (37.50, 126.93)
])

# 비행 경로 테스트
print("=== Geofencing System Test ===")
print()
test_positions = [
    (37.5665, 126.978, "Seoul City Hall"),
    (37.587, 126.977, "Near Blue House"),
    (37.460, 126.450, "Incheon Airport"),
    (37.510, 126.915, "Military Base Area"),
    (37.550, 127.000, "Gangnam Station"),
]

for lat, lon, name in test_positions:
    violations = gf.check_position(lat, lon)
    if violations:
        print(f"  [BLOCKED] {name} ({lat}, {lon})")
        print(f"           Violated zones: {', '.join(violations)}")
        print(f"           Action: REJECT FLIGHT / FORCE RTL")
    else:
        print(f"  [ALLOWED] {name} ({lat}, {lon})")
    print()

print("=== Geofence bypass analysis ===")
print("  1. GPS spoofing: Report false position outside geofence")
print("  2. Firmware mod: Remove geofence check from flight controller")
print("  3. No-GPS mode: Disable GPS → geofence cannot function")
PYEOF
```

### 4.2 지오펜싱 우회 시뮬레이션

```bash
python3 << 'PYEOF'
print("=== Geofencing Bypass Simulation ===")
print()

# GPS 스푸핑으로 지오펜싱 우회
real_position = (37.587, 126.977)    # 청와대 근처 (금지구역)
spoofed_position = (37.550, 127.000) # 강남역 (허용구역)

print(f"[Real Position]    Lat:{real_position[0]}, Lon:{real_position[1]}")
print(f"[Spoofed Position] Lat:{spoofed_position[0]}, Lon:{spoofed_position[1]}")
print()
print("[*] Geofence check with real GPS:    BLOCKED (No-fly zone)")
print("[*] Geofence check with spoofed GPS: ALLOWED (Clear zone)")
print("[!] Drone enters no-fly zone undetected!")
print()

# 방어 대책
print("=== Defense Countermeasures ===")
defenses = [
    ("Multi-source positioning", "GPS + 관성항법 + 시각 위치추정 크로스체크"),
    ("GPS signal validation", "수신 신호 강도/도플러 이상 탐지"),
    ("Remote ID enforcement", "지상 관제 시스템이 독립적 위치 확인"),
    ("Firmware integrity", "서명된 펌웨어만 실행 허용"),
    ("Network-based geofence", "지상국에서 위치 검증 후 명령 승인"),
]
for name, desc in defenses:
    print(f"  [{name}]")
    print(f"    {desc}")
    print()
PYEOF
```

---

## Part 5: 드론 IDS 구축 (2:40-3:10)

### 5.1 드론 통신 침입 탐지 시스템

```bash
python3 << 'PYEOF'
import json
import time

class DroneIDS:
    """드론 통신 침입 탐지 시스템"""

    def __init__(self):
        self.rules = []
        self.alerts = []
        self.cmd_history = []
        self.known_controllers = {"10.20.30.201"}

    def add_rule(self, name, check_fn, severity):
        self.rules.append({"name": name, "check": check_fn, "severity": severity})

    def analyze(self, packet):
        self.cmd_history.append(packet)
        for rule in self.rules:
            result = rule["check"](packet, self)
            if result:
                alert = {
                    "rule": rule["name"],
                    "severity": rule["severity"],
                    "detail": result,
                    "packet": packet
                }
                self.alerts.append(alert)
                print(f"  [ALERT-{rule['severity']}] {rule['name']}: {result}")

# IDS 규칙 정의
ids = DroneIDS()

# 규칙 1: 알 수 없는 출발지
ids.add_rule("Unknown Source",
    lambda pkt, ids: f"Unknown source: {pkt['src']}"
        if pkt.get('src') not in ids.known_controllers else None,
    "HIGH")

# 규칙 2: 인증 없는 비행 명령
ids.add_rule("Unauthenticated Flight CMD",
    lambda pkt, ids: f"Flight cmd without auth: {pkt['data'].get('action')}"
        if pkt['data'].get('action') in ('ARM','TAKEOFF','GOTO') and not pkt.get('authenticated') else None,
    "CRITICAL")

# 규칙 3: 급격한 좌표 변경
ids.add_rule("Sudden Position Change",
    lambda pkt, ids: f"Large coordinate jump detected"
        if pkt['data'].get('action') == 'GOTO' and
           abs(pkt['data'].get('lat',0) - 37.5665) > 1 else None,
    "MEDIUM")

# 규칙 4: 비정상 명령 빈도
ids.add_rule("Command Flooding",
    lambda pkt, ids: f"Too many commands: {len(ids.cmd_history)} in short time"
        if len(ids.cmd_history) > 8 else None,
    "HIGH")

# 테스트 패킷
print("=== Drone IDS - Analyzing Traffic ===")
print()

test_traffic = [
    {"src": "10.20.30.201", "data": {"action": "AUTH", "key": "xxx"}, "authenticated": True},
    {"src": "10.20.30.201", "data": {"action": "ARM"}, "authenticated": True},
    {"src": "10.20.30.201", "data": {"action": "TAKEOFF", "altitude": 50}, "authenticated": True},
    {"src": "10.20.30.99", "data": {"action": "GOTO", "lat": 37.57, "lon": 126.98}, "authenticated": False},
    {"src": "10.20.30.99", "data": {"action": "ARM"}, "authenticated": False},
    {"src": "10.20.30.99", "data": {"action": "GOTO", "lat": 40.00, "lon": 130.00}, "authenticated": False},
]

for i, pkt in enumerate(test_traffic):
    print(f"[PKT {i+1}] src={pkt['src']} action={pkt['data'].get('action','?')}")
    ids.analyze(pkt)
    print()

print(f"=== Summary: {len(ids.alerts)} alerts generated ===")
for a in ids.alerts:
    print(f"  [{a['severity']}] {a['rule']}")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** 드론 IDS 규칙을 5개 이상 추가하고, 테스트 트래픽으로 검증하시오.
- 비행 고도 제한 초과 탐지
- 배터리 부족 시 비행 명령 차단
- 야간 비행 탐지
- 동일 드론에 대한 다중 컨트롤러 연결 탐지
- 비정상 비행 패턴(급선회, 급상승) 탐지

---

## 참고 자료

- DJI AeroScope: 드론 탐지 시스템
- FAA Remote ID Rule: https://www.faa.gov/uas/getting_started/remote_id
- "Counter-Drone Systems" - RAND Corporation
- "Anti-UAV Defense System" - IEEE Survey

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

