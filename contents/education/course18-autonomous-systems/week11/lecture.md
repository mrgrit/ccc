# Week 11: OT/ICS 보안 — PLC, Modbus, SCADA, Stuxnet

## 학습 목표
- OT/ICS 시스템의 구조와 IT 시스템과의 차이를 이해한다
- PLC, HMI, SCADA의 역할과 통신 프로토콜을 설명할 수 있다
- Modbus 프로토콜의 구조와 보안 취약점을 분석할 수 있다
- Python pymodbus로 Modbus 통신을 실습할 수 있다
- Stuxnet 등 ICS 공격 사례를 심층 분석할 수 있다

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
| 0:00-0:30 | 이론: OT/ICS 시스템 구조 (Part 1) | 강의 |
| 0:30-1:00 | 이론: Modbus/SCADA 프로토콜 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: Modbus 시뮬레이터와 통신 (Part 3) | 실습 |
| 1:50-2:30 | 실습: Modbus 공격 시뮬레이션 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: ICS 보안 모니터링 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: OT/ICS 시스템 구조 (0:00-0:30)

### 1.1 Purdue 모델 (ICS 아키텍처)

```
Level 5: Enterprise Network (ERP, Email)
──────────────── DMZ ────────────────────
Level 4: Business Planning (MES)
──────────── IT/OT 경계 ────────────────
Level 3: Operations (SCADA Server, Historian)
Level 2: Supervisory (HMI, Engineering WS)
Level 1: Control (PLC, RTU, DCS)
Level 0: Process (Sensors, Actuators, Valves)
```

### 1.2 ICS 주요 구성 요소

| 구성 요소 | 역할 | 보안 위협 |
|-----------|------|-----------|
| **PLC** | 프로그래밍 가능 논리 제어기 | 로직 변조, 펌웨어 교체 |
| **HMI** | 인간-기계 인터페이스 | 화면 조작, 잘못된 표시 |
| **SCADA** | 감시 제어 및 데이터 수집 | 원격 접근, 명령 위조 |
| **RTU** | 원격 단말 장치 | 통신 가로채기 |
| **DCS** | 분산 제어 시스템 | 네트워크 공격 |
| **Historian** | 데이터 기록 서버 | 데이터 변조, 정보 유출 |
| **EWS** | 엔지니어링 워크스테이션 | 프로젝트 파일 감염 |

### 1.3 OT vs IT 보안

| 차원 | IT | OT |
|------|----|----|
| 우선순위 | CIA (기밀성 우선) | AIC (가용성 우선) |
| 생명주기 | 3-5년 | 15-25년 |
| 패치 | 수시 | 연 1-2회 (다운타임 필요) |
| 프로토콜 | TCP/IP | Modbus, DNP3, OPC-UA |
| OS | 최신 Windows/Linux | 레거시 (XP, 2000) |
| 실시간성 | 최선 노력 | 경성 실시간 |

---

## Part 2: Modbus/SCADA 프로토콜 (0:30-1:00)

### 2.1 Modbus 프로토콜

```
Modbus TCP 프레임
┌────────────────────────────────────────────────┐
│ MBAP Header (7 bytes)  │ PDU (Function + Data) │
├────────┬────────┬──────┼──────┬────────────────┤
│ Trans  │Protocol│Length│ Unit │ FC │ Data       │
│ ID (2B)│ ID (2B)│(2B) │ (1B) │(1B)│ (variable) │
└────────┴────────┴──────┴──────┴────┴────────────┘

주요 Function Code:
  0x01: Read Coils (DO)
  0x02: Read Discrete Inputs (DI)
  0x03: Read Holding Registers
  0x04: Read Input Registers
  0x05: Write Single Coil
  0x06: Write Single Register
  0x0F: Write Multiple Coils
  0x10: Write Multiple Registers

보안 취약점:
  - 인증 없음
  - 암호화 없음
  - 무결성 검증 없음
  - 모든 클라이언트의 명령 수락
```

### 2.2 주요 ICS 프로토콜 비교

| 프로토콜 | 포트 | 인증 | 암호화 | 용도 |
|----------|------|------|--------|------|
| Modbus TCP | 502 | 없음 | 없음 | PLC 제어 |
| DNP3 | 20000 | 선택적 | 선택적 | 전력 시스템 |
| OPC-UA | 4840 | 있음 | 있음 | 산업 통합 |
| EtherNet/IP | 44818 | 없음 | 없음 | PLC 통신 |
| S7comm | 102 | 없음 | 없음 | Siemens PLC |
| BACnet | 47808 | 없음 | 없음 | 빌딩 자동화 |

### 2.3 ICS 공격 사례

```
Stuxnet (2010): 이란 핵시설 - PLC 로직 변조
BlackEnergy (2015): 우크라이나 전력망 - HMI 접근
Triton/TRISIS (2017): 석유화학 - 안전 시스템(SIS) 공격
CrashOverride (2016): 우크라이나 전력망 - IEC 61850 악용
Pipedream/INCONTROLLER (2022): 다중 ICS 프로토콜 공격 프레임워크
```

---

## Part 3: Modbus 시뮬레이터와 통신 (1:10-1:50)

### 3.1 Python Modbus 시뮬레이터

```bash
python3 << 'PYEOF'
import struct
import socket
import json

class ModbusSimulator:
    """Modbus TCP 서버/클라이언트 시뮬레이터"""

    def __init__(self):
        # PLC 메모리 시뮬레이션
        self.coils = [False] * 100          # 디지털 출력
        self.discrete_inputs = [False] * 100 # 디지털 입력
        self.holding_registers = [0] * 100   # 아날로그 출력
        self.input_registers = [0] * 100     # 아날로그 입력

        # 공정 시뮬레이션 (수처리 시설)
        self.holding_registers[0] = 250   # 수위 (25.0 cm)
        self.holding_registers[1] = 350   # 온도 (35.0 C)
        self.holding_registers[2] = 700   # pH (7.00)
        self.holding_registers[3] = 1000  # 유량 (100.0 L/min)
        self.holding_registers[4] = 150   # 압력 (15.0 bar)
        self.coils[0] = True              # 펌프 1 ON
        self.coils[1] = False             # 펌프 2 OFF
        self.coils[2] = True              # 밸브 1 OPEN
        self.coils[3] = False             # 밸브 2 CLOSED
        self.coils[10] = False            # 긴급 정지 OFF

    def process_request(self, fc, data):
        """Modbus 요청 처리"""
        if fc == 0x03:  # Read Holding Registers
            addr = data.get('address', 0)
            count = data.get('count', 1)
            values = self.holding_registers[addr:addr+count]
            return {"fc": fc, "values": values}

        elif fc == 0x01:  # Read Coils
            addr = data.get('address', 0)
            count = data.get('count', 1)
            values = self.coils[addr:addr+count]
            return {"fc": fc, "values": values}

        elif fc == 0x06:  # Write Single Register
            addr = data.get('address', 0)
            value = data.get('value', 0)
            old = self.holding_registers[addr]
            self.holding_registers[addr] = value
            return {"fc": fc, "address": addr, "old": old, "new": value}

        elif fc == 0x05:  # Write Single Coil
            addr = data.get('address', 0)
            value = data.get('value', False)
            old = self.coils[addr]
            self.coils[addr] = value
            return {"fc": fc, "address": addr, "old": old, "new": value}

        return {"fc": fc, "error": "Unsupported function"}

# Modbus 시뮬레이션
plc = ModbusSimulator()

print("=== Modbus TCP PLC Simulator (Water Treatment Plant) ===")
print()

# 현재 상태 읽기
print("[Read] Holding Registers (FC 0x03) — Process Values")
reg_names = {0: "Water Level (cm/10)", 1: "Temperature (C/10)",
             2: "pH (x100)", 3: "Flow Rate (L/min/10)", 4: "Pressure (bar/10)"}
resp = plc.process_request(0x03, {"address": 0, "count": 5})
for i, val in enumerate(resp['values']):
    name = reg_names.get(i, f"Register {i}")
    real_val = val / 10.0 if i != 2 else val / 100.0
    print(f"  [{i}] {name}: {val} (={real_val})")
print()

# Coil 상태 읽기
print("[Read] Coils (FC 0x01) — Actuator States")
coil_names = {0: "Pump 1", 1: "Pump 2", 2: "Valve 1", 3: "Valve 2", 10: "Emergency Stop"}
resp = plc.process_request(0x01, {"address": 0, "count": 11})
for i, val in enumerate(resp['values']):
    if i in coil_names:
        state = "ON/OPEN" if val else "OFF/CLOSED"
        print(f"  [{i:2d}] {coil_names[i]}: {state}")
print()

# 정상 쓰기 명령
print("[Write] Normal Operation — Adjust flow rate")
resp = plc.process_request(0x06, {"address": 3, "value": 1200})
print(f"  Register {resp['address']}: {resp['old']} → {resp['new']} (120.0 L/min)")
PYEOF
```

---

## Part 4: Modbus 공격 시뮬레이션 (1:50-2:30)

### 4.1 Modbus 공격 시나리오

```bash
python3 << 'PYEOF'
import json

class ModbusPLC:
    def __init__(self):
        self.holding_registers = [250, 350, 700, 1000, 150] + [0]*95
        self.coils = [True, False, True, False] + [False]*6 + [False] + [False]*89

    def read_register(self, addr):
        return self.holding_registers[addr]

    def write_register(self, addr, val):
        old = self.holding_registers[addr]
        self.holding_registers[addr] = val
        return old, val

    def write_coil(self, addr, val):
        old = self.coils[addr]
        self.coils[addr] = val
        return old, val

plc = ModbusPLC()

print("=" * 60)
print("  MODBUS ATTACK SIMULATION - Water Treatment Plant")
print("=" * 60)
print()

# 공격 1: 정찰 — 레지스터 스캔
print("[Attack 1] RECONNAISSANCE - Register Scanning")
print("  Scanning all holding registers 0-4...")
for i in range(5):
    val = plc.read_register(i)
    print(f"  Register[{i}] = {val}")
print("  [!] All process values disclosed — no authentication required")
print()

# 공격 2: 프로세스 값 변조
print("[Attack 2] PROCESS VALUE MANIPULATION")
attacks = [
    (0, 999, "Water level set to dangerous 99.9cm (overflow risk)"),
    (1, 900, "Temperature set to 90C (equipment damage)"),
    (2, 200, "pH set to 2.00 (highly acidic — corrosion)"),
    (4, 500, "Pressure set to 50 bar (pipe burst risk)"),
]
for addr, val, desc in attacks:
    old, new = plc.write_register(addr, val)
    print(f"  [TAMPER] Reg[{addr}]: {old} → {new}")
    print(f"           {desc}")
print()

# 공격 3: 액추에이터 변조
print("[Attack 3] ACTUATOR MANIPULATION")
coil_attacks = [
    (0, False, "Pump 1 OFF — water supply stopped"),
    (2, False, "Valve 1 CLOSED — flow blocked"),
    (10, True, "Emergency stop TRIGGERED — plant shutdown"),
]
for addr, val, desc in coil_attacks:
    old, new = plc.write_coil(addr, val)
    state = "ON" if new else "OFF"
    print(f"  [TAMPER] Coil[{addr}]: {old} → {new} ({state})")
    print(f"           {desc}")
print()

# 공격 4: Stuxnet 스타일 — HMI 기만
print("[Attack 4] STUXNET-STYLE - HMI Deception")
print("  1. Read real values from PLC")
print("  2. Modify PLC process (dangerous values)")
print("  3. Send fake 'normal' values to HMI")
print("  4. Operator sees normal display while plant is damaged")
print()
print("  Real PLC state:  Level=99.9 Temp=90C pH=2.0 Pressure=50bar")
print("  HMI display:     Level=25.0 Temp=35C pH=7.0 Pressure=15bar")
print("  [CRITICAL] Operator unaware of dangerous conditions!")

print()
print("[!] All attacks succeeded because Modbus has:")
print("    - No authentication")
print("    - No encryption")
print("    - No integrity checking")
print("    - No access control")
PYEOF
```

---

## Part 5: ICS 보안 모니터링 (2:40-3:10)

### 5.1 ICS 네트워크 모니터링

```bash
python3 << 'PYEOF'
class ICSMonitor:
    """ICS 네트워크 트래픽 모니터링 시스템"""

    def __init__(self):
        self.baseline = {
            "allowed_sources": {"10.20.30.200", "10.20.30.100"},
            "allowed_fc": {0x01, 0x02, 0x03, 0x04, 0x05, 0x06},
            "register_limits": {
                0: (100, 400),   # 수위: 10-40cm
                1: (200, 500),   # 온도: 20-50C
                2: (500, 900),   # pH: 5.0-9.0
                3: (500, 2000),  # 유량: 50-200 L/min
                4: (50, 250),    # 압력: 5-25 bar
            },
            "max_writes_per_minute": 10,
        }
        self.alerts = []
        self.write_count = 0

    def analyze(self, packet):
        src = packet.get("source", "")
        fc = packet.get("function_code", 0)
        addr = packet.get("address", -1)
        value = packet.get("value", 0)

        # 규칙 1: 허용되지 않은 출발지
        if src not in self.baseline["allowed_sources"]:
            self.alerts.append(("CRITICAL", f"Unauthorized source: {src}"))

        # 규칙 2: 비정상 Function Code
        if fc not in self.baseline["allowed_fc"]:
            self.alerts.append(("HIGH", f"Unusual function code: 0x{fc:02X}"))

        # 규칙 3: 쓰기 명령의 값 범위 검사
        if fc in (0x05, 0x06, 0x10) and addr in self.baseline["register_limits"]:
            low, high = self.baseline["register_limits"][addr]
            if value < low or value > high:
                self.alerts.append(("CRITICAL", f"Out-of-range write: Reg[{addr}]={value} (valid: {low}-{high})"))

        # 규칙 4: 쓰기 빈도 초과
        if fc in (0x05, 0x06, 0x0F, 0x10):
            self.write_count += 1
            if self.write_count > self.baseline["max_writes_per_minute"]:
                self.alerts.append(("HIGH", f"Write rate exceeded: {self.write_count}/min"))

        # 규칙 5: 긴급 정지 코일 접근
        if fc == 0x05 and addr == 10:
            self.alerts.append(("CRITICAL", f"Emergency stop coil accessed from {src}"))

        return len(self.alerts)

monitor = ICSMonitor()

print("=== ICS Security Monitor — Modbus Traffic Analysis ===")
print()

traffic = [
    {"source": "10.20.30.200", "function_code": 0x03, "address": 0, "value": 0, "desc": "Normal read"},
    {"source": "10.20.30.200", "function_code": 0x06, "address": 3, "value": 1100, "desc": "Normal write"},
    {"source": "10.20.30.201", "function_code": 0x03, "address": 0, "value": 0, "desc": "Recon from attacker"},
    {"source": "10.20.30.201", "function_code": 0x06, "address": 0, "value": 999, "desc": "Dangerous write"},
    {"source": "10.20.30.201", "function_code": 0x06, "address": 1, "value": 900, "desc": "Temp manipulation"},
    {"source": "10.20.30.201", "function_code": 0x05, "address": 10, "value": 1, "desc": "Emergency stop"},
    {"source": "10.20.30.201", "function_code": 0x2B, "address": 0, "value": 0, "desc": "Device ID scan"},
]

for pkt in traffic:
    prev_alerts = len(monitor.alerts)
    monitor.analyze(pkt)
    new_alerts = monitor.alerts[prev_alerts:]
    status = "ALERT" if new_alerts else "OK"

    print(f"  [{status:5}] Src:{pkt['source']} FC:0x{pkt['function_code']:02X} — {pkt['desc']}")
    for sev, msg in new_alerts:
        print(f"         [{sev}] {msg}")

print()
print(f"=== Total Alerts: {len(monitor.alerts)} ===")
by_severity = {}
for sev, msg in monitor.alerts:
    by_severity.setdefault(sev, []).append(msg)
for sev in ["CRITICAL", "HIGH", "MEDIUM"]:
    if sev in by_severity:
        print(f"  {sev}: {len(by_severity[sev])}")
        for msg in by_severity[sev]:
            print(f"    - {msg}")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** pymodbus를 사용하여 Modbus 보안 실습 환경을 구축하시오.
- Modbus TCP 서버 (가상 PLC) 구현
- 정상/비정상 트래픽 생성기 구현
- Modbus IDS 규칙 10개 이상 작성
- 탐지 결과 리포트 출력

---

## 참고 자료

- NIST SP 800-82 Rev 3: Guide to OT Security
- MITRE ATT&CK for ICS
- Modbus Protocol Specification
- "Industrial Network Security" - Knapp & Langill

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (11주차) 학습 주제와 직접 연관된 *실제* incident:

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
