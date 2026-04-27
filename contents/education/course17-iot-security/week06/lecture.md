# Week 06: 무선 프로토콜 해킹

## 학습 목표
- SDR(Software Defined Radio)의 개념과 IoT 보안에서의 활용을 이해한다
- LoRa 패킷 캡처 및 분석 기법을 학습한다
- Zigbee 스니핑 및 프로토콜 분석을 실습한다
- 무선 프로토콜의 리플레이/재밍 공격 원리를 파악한다
- 가상 환경에서 무선 프로토콜 시뮬레이션을 수행한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 서비스 호스트 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

> 물리 SDR 장비 없이 Python 시뮬레이션으로 무선 프로토콜을 학습합니다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | SDR 및 무선 보안 이론 (Part 1) | 강의 |
| 0:40-1:10 | LoRa/Zigbee 프로토콜 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | LoRa 시뮬레이션 실습 (Part 3) | 실습 |
| 2:00-2:40 | Zigbee 시뮬레이션 실습 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 리플레이/재밍 공격 시뮬레이션 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: SDR 및 무선 보안 이론 (40분)

### 1.1 SDR(Software Defined Radio) 개요

SDR은 전통적으로 하드웨어로 구현되던 무선 통신 기능을 소프트웨어로 구현하는 기술이다.

**SDR 하드웨어:**

| 장비 | 주파수 범위 | 용도 | 가격 |
|------|-----------|------|------|
| RTL-SDR | 24-1766 MHz | 수신 전용, 입문 | ~$25 |
| HackRF One | 1-6000 MHz | 송수신, 범용 | ~$300 |
| YARD Stick One | Sub-GHz | 315/433/868/915 MHz | ~$100 |
| Ubertooth One | 2.4 GHz | BLE 전용 | ~$120 |
| BladeRF | 47-6000 MHz | 고급 SDR | ~$400 |
| USRP | 다양 | 연구용 | ~$1000+ |

### 1.2 IoT 무선 주파수 대역

```
┌─────────────────────────────────────────────┐
│                 주파수 대역                   │
├──────┬──────┬──────┬──────┬────────┬────────┤
│ 315  │ 433  │ 868  │ 915  │ 2400   │ 5800   │
│ MHz  │ MHz  │ MHz  │ MHz  │ MHz    │ MHz    │
├──────┼──────┼──────┼──────┼────────┼────────┤
│차고문│리모컨│LoRa  │LoRa  │WiFi    │WiFi    │
│열쇠  │무선  │(EU)  │(US)  │BLE     │5GHz    │
│      │센서  │Zigbee│      │Zigbee  │        │
└──────┴──────┴──────┴──────┴────────┴────────┘
```

### 1.3 무선 공격 분류

| 공격 유형 | 설명 | 난이도 |
|-----------|------|--------|
| 스니핑 | 무선 신호 도청 | 낮음 |
| 리플레이 | 캡처한 신호 재전송 | 낮음 |
| 재밍 | 주파수 방해 | 낮음 |
| 인젝션 | 악성 패킷 주입 | 중간 |
| 스푸핑 | 디바이스 위장 | 중간 |
| MitM | 중간자 공격 | 높음 |
| 퍼징 | 변형 패킷으로 크래시 유발 | 높음 |
| 키 추출 | 암호화 키 복원 | 높음 |

### 1.4 무선 신호 분석 기초

```
신호 분석 파이프라인:

RF 수신 → ADC → I/Q 데이터 → 복조 → 디코딩 → 프로토콜 분석
                    ↓
            주파수 분석 (FFT)
            시간 도메인 분석
            변조 방식 식별
```

**변조 방식:**
- ASK/OOK: 진폭 변조 (차고문, 리모컨)
- FSK: 주파수 변조 (LoRa의 CSS는 FSK 변형)
- GFSK: 가우시안 FSK (BLE)
- O-QPSK: 오프셋 직교 위상 변조 (Zigbee)

---

## Part 2: LoRa/Zigbee 프로토콜 심화 (30분)

### 2.1 LoRaWAN 프레임 구조

```
┌───────┬──────┬──────────┬───────────┬─────┐
│ PHY   │ MAC  │ Frame    │ Payload   │ MIC │
│Header │Header│ Header   │(encrypted)│     │
│(1B)   │(7B)  │(1-22B)   │(0-222B)   │(4B) │
└───────┴──────┴──────────┴───────────┴─────┘
```

**LoRaWAN 보안 키:**
```
OTAA (Over-The-Air Activation):
  AppKey → Join Request/Accept → NwkSKey + AppSKey

ABP (Activation By Personalization):
  DevAddr, NwkSKey, AppSKey (사전 설정)
  → 리플레이 공격에 취약 (프레임 카운터 리셋 시)
```

### 2.2 Zigbee 프레임 구조

```
┌──────┬───────┬─────────┬──────────┬─────┐
│ Frame│Sequence│ Address │ Payload  │ FCS │
│Control│Number│ Fields  │          │     │
│(2B)  │(1B)   │(0-20B)  │(variable)│(2B) │
└──────┴───────┴─────────┴──────────┴─────┘
```

**Zigbee 보안 레이어:**
```
┌────────────────────────────┐
│ Application Layer (APS Key)│ ← 앱 레벨 암호화
├────────────────────────────┤
│ Network Layer (Network Key)│ ← 네트워크 레벨 암호화
├────────────────────────────┤
│ MAC Layer                  │ ← 프레임 무결성
└────────────────────────────┘

Trust Center Link Key (TCLK): ZigBeeAlliance09 (공개!)
```

### 2.3 Zigbee 공격 시나리오

1. **키 스니핑:** 디바이스 조인 시 네트워크 키 평문 전송 캡처
2. **리플레이:** 캡처한 명령 재전송 (조명 on/off)
3. **인젝션:** 네트워크 키 획득 후 악성 명령 주입
4. **퍼징:** 변형 ZCL 명령으로 디바이스 크래시

---

## Part 3: LoRa 시뮬레이션 실습 (40분)

### 3.1 LoRa 패킷 시뮬레이터

```bash
cat << 'PYEOF' > /tmp/lora_simulator.py
#!/usr/bin/env python3
"""LoRaWAN 패킷 시뮬레이터 및 분석기"""
import struct
import hashlib
import hmac
import json
import time
import random
import binascii

class LoRaWANPacket:
    # Message Types
    JOIN_REQUEST = 0x00
    JOIN_ACCEPT = 0x01
    UNCONFIRMED_DATA_UP = 0x02
    UNCONFIRMED_DATA_DOWN = 0x03
    CONFIRMED_DATA_UP = 0x04
    
    def __init__(self):
        self.mhdr = 0
        self.dev_addr = b'\x00\x00\x00\x00'
        self.fctrl = 0
        self.fcnt = 0
        self.fport = 1
        self.payload = b''
        self.mic = b'\x00\x00\x00\x00'
    
    @staticmethod
    def create_uplink(dev_addr, fcnt, payload, nwk_skey, app_skey):
        pkt = LoRaWANPacket()
        pkt.mhdr = (LoRaWANPacket.UNCONFIRMED_DATA_UP << 5) | 0x00
        pkt.dev_addr = struct.pack('<I', dev_addr)
        pkt.fcnt = fcnt
        pkt.fport = 1
        
        # 페이로드 암호화 (간소화)
        key = hashlib.sha256(app_skey + struct.pack('<I', fcnt)).digest()[:len(payload)]
        pkt.payload = bytes(a ^ b for a, b in zip(payload, key))
        
        # MIC 계산 (간소화)
        mic_data = struct.pack('B', pkt.mhdr) + pkt.dev_addr + \
                   struct.pack('<BH', pkt.fctrl, pkt.fcnt) + \
                   struct.pack('B', pkt.fport) + pkt.payload
        pkt.mic = hmac.new(nwk_skey, mic_data, hashlib.sha256).digest()[:4]
        
        return pkt
    
    def to_bytes(self):
        return struct.pack('B', self.mhdr) + self.dev_addr + \
               struct.pack('<BH', self.fctrl, self.fcnt) + \
               struct.pack('B', self.fport) + self.payload + self.mic
    
    def to_hex(self):
        return binascii.hexlify(self.to_bytes()).decode()
    
    @staticmethod
    def parse(data):
        pkt = LoRaWANPacket()
        pkt.mhdr = data[0]
        pkt.dev_addr = data[1:5]
        pkt.fctrl = data[5]
        pkt.fcnt = struct.unpack('<H', data[6:8])[0]
        pkt.fport = data[8]
        pkt.payload = data[9:-4]
        pkt.mic = data[-4:]
        
        msg_type = (pkt.mhdr >> 5) & 0x07
        types = {0:'JOIN_REQ', 1:'JOIN_ACCEPT', 2:'UNCONF_UP', 3:'UNCONF_DOWN', 4:'CONF_UP'}
        
        print(f"=== LoRaWAN Packet Analysis ===")
        print(f"  MHDR: 0x{pkt.mhdr:02X} (Type: {types.get(msg_type, 'Unknown')})")
        print(f"  DevAddr: {binascii.hexlify(pkt.dev_addr).decode()}")
        print(f"  FCtrl: 0x{pkt.fctrl:02X}")
        print(f"  FCnt: {pkt.fcnt}")
        print(f"  FPort: {pkt.fport}")
        print(f"  Payload: {binascii.hexlify(pkt.payload).decode()} ({len(pkt.payload)} bytes)")
        print(f"  MIC: {binascii.hexlify(pkt.mic).decode()}")
        return pkt


# 시뮬레이션 실행
print("=" * 50)
print("LoRaWAN 패킷 시뮬레이션")
print("=" * 50)

# 키 설정
NWK_SKEY = b'\x01' * 16
APP_SKEY = b'\x02' * 16
DEV_ADDR = 0x26011234

# 센서 데이터 전송 시뮬레이션
for i in range(5):
    temp = 20 + random.uniform(-5, 15)
    humidity = 40 + random.uniform(0, 40)
    sensor_data = json.dumps({"t": round(temp,1), "h": round(humidity,1)}).encode()
    
    pkt = LoRaWANPacket.create_uplink(DEV_ADDR, i, sensor_data, NWK_SKEY, APP_SKEY)
    raw = pkt.to_bytes()
    
    print(f"\n--- Packet #{i} (FCnt={i}) ---")
    print(f"  Raw: {pkt.to_hex()}")
    print(f"  Original: {sensor_data.decode()}")
    
    # 패킷 파싱
    LoRaWANPacket.parse(raw)
    
    time.sleep(0.5)

# 리플레이 공격 데모
print("\n" + "=" * 50)
print("리플레이 공격 시뮬레이션")
print("=" * 50)
print("[*] 패킷 #2를 캡처하여 재전송...")
replay_pkt = LoRaWANPacket.create_uplink(DEV_ADDR, 2, b'{"t":99.9,"h":0}', NWK_SKEY, APP_SKEY)
print(f"[*] 원본 FCnt=2, 리플레이 FCnt=2")
print(f"[!] 서버가 FCnt를 검증하면 거부됨 (현재 FCnt > 2)")
print(f"[!] ABP 모드에서 리셋 시 FCnt=0부터 다시 시작 → 리플레이 가능")
PYEOF

python3 /tmp/lora_simulator.py
```

### 3.2 LoRa 트래픽 분석

```bash
# LoRa 패킷 캡처 파일 분석
cat << 'PYEOF' > /tmp/lora_analyzer.py
#!/usr/bin/env python3
"""LoRa 트래픽 분석기"""
import json
import time
import random
import binascii

# 시뮬레이션된 캡처 데이터
captured_packets = []
for i in range(20):
    pkt = {
        "timestamp": time.time() + i * 30,
        "rssi": random.randint(-120, -40),
        "snr": round(random.uniform(-5, 15), 1),
        "freq": random.choice([868.1, 868.3, 868.5, 915.0]),
        "sf": random.choice([7, 8, 9, 10, 11, 12]),
        "bw": random.choice([125, 250, 500]),
        "dev_addr": f"{random.randint(0, 0xFFFFFFFF):08x}",
        "fcnt": i,
        "payload_hex": binascii.hexlify(bytes(random.getrandbits(8) for _ in range(random.randint(5, 50)))).decode(),
    }
    captured_packets.append(pkt)

print("=== LoRa 트래픽 분석 보고서 ===\n")

# 디바이스 식별
devices = {}
for p in captured_packets:
    addr = p['dev_addr']
    if addr not in devices:
        devices[addr] = {"count": 0, "rssi_avg": 0, "first_seen": p['timestamp']}
    devices[addr]["count"] += 1
    devices[addr]["rssi_avg"] += p['rssi']

print(f"[+] 탐지된 디바이스: {len(devices)}개")
for addr, info in devices.items():
    avg_rssi = info['rssi_avg'] / info['count']
    print(f"  DevAddr: {addr} | 패킷: {info['count']}개 | 평균 RSSI: {avg_rssi:.0f} dBm")

# SF 분포
print(f"\n[+] Spreading Factor 분포:")
sf_dist = {}
for p in captured_packets:
    sf = p['sf']
    sf_dist[sf] = sf_dist.get(sf, 0) + 1
for sf in sorted(sf_dist.keys()):
    print(f"  SF{sf}: {sf_dist[sf]}개 ({'#' * sf_dist[sf]})")

# 보안 분석
print(f"\n[+] 보안 분석:")
print(f"  - 평문 전송: 페이로드 암호화 여부 확인 필요")
print(f"  - FCnt 연속성: 프레임 카운터 점프 확인")
print(f"  - 재전송 패턴: 동일 FCnt 중복 확인")
PYEOF

python3 /tmp/lora_analyzer.py
```

---

## Part 4: Zigbee 시뮬레이션 실습 (40분)

### 4.1 Zigbee 패킷 시뮬레이터

```bash
cat << 'PYEOF' > /tmp/zigbee_simulator.py
#!/usr/bin/env python3
"""Zigbee 패킷 시뮬레이터"""
import struct
import random
import binascii
import hashlib

class ZigbeeFrame:
    # Frame Types
    BEACON = 0x00
    DATA = 0x01
    ACK = 0x02
    CMD = 0x03
    
    # ZCL Cluster IDs
    ON_OFF = 0x0006
    LEVEL_CONTROL = 0x0008
    COLOR_CONTROL = 0x0300
    TEMPERATURE = 0x0402
    
    def __init__(self, frame_type=DATA):
        self.frame_type = frame_type
        self.seq_num = random.randint(0, 255)
        self.dst_pan = 0x1234
        self.dst_addr = 0x0000
        self.src_addr = 0x0001
        self.cluster_id = self.ON_OFF
        self.payload = b''
    
    def create_zcl_on_off(self, on=True):
        """조명 On/Off ZCL 명령"""
        self.cluster_id = self.ON_OFF
        cmd = 0x01 if on else 0x00  # On=1, Off=0
        self.payload = struct.pack('BBB', 0x01, self.seq_num, cmd)
        return self
    
    def create_zcl_temp_report(self, temp_c):
        """온도 센서 리포트"""
        self.cluster_id = self.TEMPERATURE
        temp_val = int(temp_c * 100)
        self.payload = struct.pack('<BBHH', 0x18, self.seq_num, 0x0000, temp_val)
        return self
    
    def to_bytes(self):
        fc = (self.frame_type & 0x07) | (0x08)  # Security disabled
        header = struct.pack('<BH', self.seq_num, self.dst_pan)
        header += struct.pack('<HH', self.dst_addr, self.src_addr)
        header += struct.pack('<H', self.cluster_id)
        return struct.pack('<H', fc) + header + self.payload
    
    def to_hex(self):
        return binascii.hexlify(self.to_bytes()).decode()

# 시뮬레이션
print("=" * 50)
print("Zigbee 패킷 시뮬레이션")
print("=" * 50)

# 스마트 조명 제어 시뮬레이션
print("\n[1] 조명 ON 명령:")
frame_on = ZigbeeFrame()
frame_on.dst_addr = 0x0002
frame_on.create_zcl_on_off(on=True)
print(f"  Raw: {frame_on.to_hex()}")
print(f"  Cluster: On/Off (0x0006)")
print(f"  Command: ON")

print("\n[2] 조명 OFF 명령:")
frame_off = ZigbeeFrame()
frame_off.dst_addr = 0x0002
frame_off.create_zcl_on_off(on=False)
print(f"  Raw: {frame_off.to_hex()}")
print(f"  Cluster: On/Off (0x0006)")
print(f"  Command: OFF")

print("\n[3] 온도 센서 리포트:")
frame_temp = ZigbeeFrame()
frame_temp.src_addr = 0x0003
frame_temp.create_zcl_temp_report(23.5)
print(f"  Raw: {frame_temp.to_hex()}")
print(f"  Cluster: Temperature (0x0402)")
print(f"  Value: 23.5C")

# 키 스니핑 시뮬레이션
print("\n" + "=" * 50)
print("Zigbee 네트워크 키 스니핑 시뮬레이션")
print("=" * 50)

# 기본 Trust Center Link Key
TCLK = b'ZigBeeAlliance09'
print(f"\n[*] Trust Center Link Key: {TCLK.decode()}")
print(f"[*] 디바이스 조인 시 네트워크 키 전송 모니터링...")

# 조인 과정 시뮬레이션
network_key = bytes(random.getrandbits(8) for _ in range(16))
print(f"[*] Network Key (평문): {binascii.hexlify(network_key).decode()}")

# TCLK로 암호화된 네트워크 키 (간소화)
encrypted_key = bytes(a ^ b for a, b in zip(network_key, TCLK))
print(f"[*] Network Key (TCLK 암호화): {binascii.hexlify(encrypted_key).decode()}")

# 복호화
decrypted_key = bytes(a ^ b for a, b in zip(encrypted_key, TCLK))
print(f"[+] Network Key (복호화): {binascii.hexlify(decrypted_key).decode()}")
print(f"[!] TCLK가 공개되어 있으므로 네트워크 키 복원 가능!")
PYEOF

python3 /tmp/zigbee_simulator.py
```

### 4.2 Zigbee 네트워크 스캐너 시뮬레이션

```bash
cat << 'PYEOF' > /tmp/zigbee_scanner.py
#!/usr/bin/env python3
"""Zigbee 네트워크 스캐너 시뮬레이션"""
import random
import time

print("=== Zigbee Network Scanner ===\n")
print("[*] Scanning channels 11-26 (2.4 GHz)...\n")

networks = [
    {"channel": 15, "pan_id": "0x1234", "ext_pan": "00:11:22:33:44:55:66:77", "coord": "0x0000", "profile": "Home Automation", "devices": 8},
    {"channel": 20, "pan_id": "0x5678", "ext_pan": "AA:BB:CC:DD:EE:FF:00:11", "coord": "0x0000", "profile": "Smart Energy", "devices": 3},
    {"channel": 25, "pan_id": "0xABCD", "ext_pan": "12:34:56:78:9A:BC:DE:F0", "coord": "0x0000", "profile": "Light Link", "devices": 12},
]

for net in networks:
    time.sleep(0.5)
    print(f"[+] Network Found:")
    print(f"    Channel: {net['channel']} ({2405 + (net['channel']-11)*5} MHz)")
    print(f"    PAN ID: {net['pan_id']}")
    print(f"    Extended PAN: {net['ext_pan']}")
    print(f"    Coordinator: {net['coord']}")
    print(f"    Profile: {net['profile']}")
    print(f"    Devices: {net['devices']}")
    print(f"    Security: {'Enabled' if random.random() > 0.3 else 'DISABLED (!)'}")
    print()

print(f"\n[+] Scan complete: {len(networks)} networks found")
print(f"[!] 보안 비활성화 네트워크 주의!")
PYEOF

python3 /tmp/zigbee_scanner.py
```

---

## Part 5: 리플레이/재밍 공격 시뮬레이션 (30분)

### 5.1 리플레이 공격

```bash
cat << 'PYEOF' > /tmp/replay_attack.py
#!/usr/bin/env python3
"""무선 리플레이 공격 시뮬레이션"""
import time
import binascii
import random

print("=== 무선 리플레이 공격 시뮬레이션 ===\n")

# 1단계: 패킷 캡처
print("[Phase 1] 패킷 캡처 (스니핑)")
captured = []
signals = [
    {"type": "차고문 열기", "freq": "433.92 MHz", "mod": "OOK", "data": "AA55FF00CC"},
    {"type": "차 잠금 해제", "freq": "315 MHz", "mod": "ASK", "data": "DEADBEEF01"},
    {"type": "조명 ON", "freq": "2.4 GHz", "mod": "O-QPSK", "data": "01020006000101"},
]

for i, sig in enumerate(signals):
    time.sleep(0.3)
    print(f"  [{i+1}] Captured: {sig['type']}")
    print(f"      Freq: {sig['freq']} | Mod: {sig['mod']}")
    print(f"      Data: {sig['data']}")
    captured.append(sig)

# 2단계: 분석
print(f"\n[Phase 2] 패킷 분석")
print(f"  - 롤링 코드 사용 여부 확인")
print(f"  - 시퀀스 번호 확인")
print(f"  - 타임스탬프 확인")

# 3단계: 리플레이
print(f"\n[Phase 3] 리플레이 공격")
for sig in captured:
    time.sleep(0.3)
    has_rolling = random.random() > 0.5
    if has_rolling:
        print(f"  [X] {sig['type']}: 리플레이 실패 (롤링 코드 보호)")
    else:
        print(f"  [!] {sig['type']}: 리플레이 성공! 명령 실행됨")

# 대책
print(f"\n[+] 리플레이 공격 대책:")
print(f"  1. 롤링 코드 (KeeLoq, AUT64)")
print(f"  2. 타임스탬프 검증")
print(f"  3. 시퀀스 번호 + 카운터")
print(f"  4. Challenge-Response 프로토콜")
print(f"  5. 암호화 + 인증 (AES-CCM)")
PYEOF

python3 /tmp/replay_attack.py
```

### 5.2 재밍 공격 이론

```
재밍 유형:
┌─────────────────────────────────────┐
│ Constant Jamming  │ 연속 방해 신호  │ → 탐지 쉬움
│ Random Jamming    │ 불규칙 방해     │ → 에너지 효율적
│ Deceptive Jamming │ 유효 패킷 위장  │ → 탐지 어려움
│ Reactive Jamming  │ 통신 감지 시 방해│ → 가장 효과적
└─────────────────────────────────────┘

대책:
- 주파수 도약 (Frequency Hopping)
- 확산 스펙트럼 (Spread Spectrum)
- 채널 전환
- 재밍 탐지 + 경고
```

---

## Part 6: 과제 안내 (20분)

### 과제

- LoRa 패킷 시뮬레이터를 확장하여 Join Request/Accept 과정을 구현하시오
- Zigbee 네트워크 키 스니핑 시뮬레이션에서 AES-CCM 복호화를 추가하시오
- 리플레이 공격에 대한 롤링 코드 방어 메커니즘을 Python으로 구현하시오

---

## 참고 자료

- GNU Radio: https://www.gnuradio.org/
- HackRF 문서: https://greatscottgadgets.com/hackrf/
- KillerBee (Zigbee): https://github.com/riverloopsec/killerbee
- LoRa 보안 분석: "LoRaWAN Security" (Things Network)

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (6주차) 학습 주제와 직접 연관된 *실제* incident:

### Data Theft (T1041) — 99.99% 의 dataset 패턴

> **출처**: WitFoo Precinct 6 / `complete-mission cluster` (anchor: `anc-a0364e702393`) · sanitized
> **시점**: 다중 (전체 99.99%)

**관찰**: Precinct 6 의 incident 10,442건 중 mo_name=Data Theft + lifecycle=complete-mission 이 99.99%. T1041 (Exfiltration over C2 Channel).

**MITRE ATT&CK**: **T1041 (Exfiltration over C2 Channel)**

**IoC**:
  - `다양한 src→dst (sanitized)`
  - `suspicion≥0.7`

**학습 포인트**:
- *가장 많이 일어나는 공격* 의 baseline — 모든 IR 시나리오의 출발점
- C2 채널 (HTTP/HTTPS/DNS) 에 데이터 mixed → 정상 트래픽 위장
- 탐지: outbound 에 데이터 흐름 모니터링 (bytes_out 분포), CTI feed 매칭
- 방어: DLP (Data Loss Prevention), egress filter, 데이터 분류·암호화


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
