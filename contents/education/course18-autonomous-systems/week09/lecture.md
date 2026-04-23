# Week 09: 로봇 보안 — ROS2, 시리얼 통신, 펌웨어

## 학습 목표
- 로봇 시스템의 소프트웨어 아키텍처와 보안 위협을 이해한다
- ROS2의 구조와 통신 메커니즘(DDS)을 설명할 수 있다
- 시리얼 통신(UART, SPI, I2C)의 보안 취약점을 분석할 수 있다
- 로봇 펌웨어 분석과 변조 기법을 이해한다
- 가상 로봇 환경에서 통신을 분석하고 취약점을 발견할 수 있다

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
| 0:00-0:30 | 이론: 로봇 시스템 아키텍처 (Part 1) | 강의 |
| 0:30-1:00 | 이론: ROS2와 DDS 통신 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 가상 로봇 통신 시뮬레이션 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 시리얼 통신 분석 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 펌웨어 분석 기초 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: 로봇 시스템 아키텍처 (0:00-0:30)

### 1.1 로봇 소프트웨어 스택

```
┌──────────────────────────────────────────────┐
│              응용 계층 (Application)           │
│  ├── 자율 항법 (Navigation)                    │
│  ├── 객체 인식 (Perception)                    │
│  ├── 경로 계획 (Path Planning)                 │
│  └── 작업 계획 (Task Planning)                 │
├──────────────────────────────────────────────┤
│              미들웨어 (Middleware)              │
│  ├── ROS2 (Robot Operating System 2)          │
│  ├── DDS (Data Distribution Service)          │
│  └── 메시지 직렬화 (CDR)                       │
├──────────────────────────────────────────────┤
│              드라이버 계층 (Driver)             │
│  ├── 센서 드라이버 (카메라, LiDAR, IMU)        │
│  ├── 액추에이터 드라이버 (모터, 서보)           │
│  └── 통신 드라이버 (UART, SPI, CAN)           │
├──────────────────────────────────────────────┤
│              하드웨어 (Hardware)               │
│  ├── 메인 컴퓨터 (x86/ARM SoC)               │
│  ├── 마이크로컨트롤러 (STM32, ESP32)          │
│  ├── 센서/액추에이터                           │
│  └── 통신 모듈 (WiFi, BLE, Ethernet)          │
└──────────────────────────────────────────────┘
```

### 1.2 로봇 유형별 보안 위협

| 로봇 유형 | 환경 | 주요 위협 | 영향 |
|-----------|------|-----------|------|
| 산업용 로봇 | 공장 | 명령 변조, 안전 무력화 | 작업자 부상, 생산 중단 |
| 의료 로봇 | 병원 | 수술 명령 변조 | 환자 위해 |
| 서비스 로봇 | 공공 | 충돌 유발, 감시 활용 | 시민 안전, 프라이버시 |
| 군사 로봇 | 전장 | 탈취, 정보 유출 | 군사 피해 |
| 물류 로봇 | 창고 | 경로 변조, DoS | 물류 마비 |

### 1.3 시리얼 통신 프로토콜

```
UART (Universal Asynchronous Receiver/Transmitter)
├── 전이중 통신 (TX, RX)
├── 보안: 없음 (평문 전송)
├── 사용: 디버그 콘솔, GPS 모듈, 센서

SPI (Serial Peripheral Interface)
├── 마스터-슬레이브, 고속
├── 보안: 없음
├── 사용: 플래시 메모리, 디스플레이, 센서

I2C (Inter-Integrated Circuit)
├── 마스터-슬레이브, 주소 기반
├── 보안: 없음
├── 사용: 센서 버스, EEPROM, RTC
```

---

## Part 2: ROS2와 DDS 통신 (0:30-1:00)

### 2.1 ROS2 아키텍처

```
ROS2 통신 모델
┌──────────┐   토픽    ┌──────────┐
│ Publisher│ ────────▶ │Subscriber│
│ (센서)   │   /scan   │ (항법)   │
└──────────┘           └──────────┘

┌──────────┐  서비스   ┌──────────┐
│ Client   │ ◀──────▶ │ Server   │
│ (요청)   │ req/resp  │ (처리)   │
└──────────┘           └──────────┘

┌──────────┐  액션     ┌──────────┐
│ Client   │ ◀──────▶ │ Server   │
│ (목표)   │ goal/fb   │ (실행)   │
└──────────┘           └──────────┘
```

### 2.2 DDS (Data Distribution Service)

```
DDS 통신 흐름:
┌──────────────────────────────────────────┐
│            DDS Domain                     │
│                                          │
│  Publisher ──[Topic]──▶ Subscriber       │
│                                          │
│  Discovery: SPDP (Simple Participant     │
│             Discovery Protocol)          │
│  Transport: UDP Multicast/Unicast        │
│  QoS: Reliability, Durability, Deadline  │
│                                          │
│  보안 문제:                               │
│  - 기본 설정: 인증/암호화 없음             │
│  - DDS Security 플러그인 필요             │
│  - 멀티캐스트로 토픽 발견 가능             │
└──────────────────────────────────────────┘
```

### 2.3 ROS2 보안 취약점

| 취약점 | 설명 | 영향 |
|--------|------|------|
| 토픽 스니핑 | 멀티캐스트로 모든 토픽 도청 가능 | 센서 데이터/명령 유출 |
| 토픽 인젝션 | 인증 없이 토픽에 메시지 게시 | 가짜 센서 데이터/명령 |
| 서비스 사칭 | 서비스 서버를 위장 | 잘못된 응답 제공 |
| 파라미터 변조 | 로봇 파라미터 무단 수정 | 동작 변경 |
| DDS Discovery | 참여자/토픽 자동 발견 | 네트워크 정찰 |

---

## Part 3: 가상 로봇 통신 시뮬레이션 (1:10-1:50)

### 3.1 ROS2 토픽 통신 시뮬레이터

```bash
python3 << 'PYEOF'
import json
import time
import random
import threading
from collections import defaultdict

class ROS2Simulator:
    """ROS2 토픽 기반 통신 시뮬레이터"""

    def __init__(self):
        self.topics = defaultdict(list)
        self.subscribers = defaultdict(list)
        self.log = []

    def publish(self, topic, msg, publisher="unknown"):
        entry = {
            "topic": topic,
            "data": msg,
            "publisher": publisher,
            "timestamp": len(self.log) * 0.1
        }
        self.topics[topic].append(entry)
        self.log.append(entry)
        return entry

    def get_messages(self, topic, count=5):
        return self.topics[topic][-count:]

    def list_topics(self):
        return {t: len(msgs) for t, msgs in self.topics.items()}

    def discover_participants(self):
        participants = set()
        for entries in self.topics.values():
            for e in entries:
                participants.add(e['publisher'])
        return participants

# ROS2 시뮬레이션
ros2 = ROS2Simulator()

# 정상 로봇 통신 시뮬레이션
print("=== ROS2 Robot Communication Simulation ===")
print()

# 센서 데이터 발행
print("[Normal Operation] Robot sensors publishing...")
for i in range(3):
    ros2.publish("/scan", {"ranges": [random.uniform(0.5, 5.0) for _ in range(5)]}, "lidar_node")
    ros2.publish("/camera/image", {"width": 640, "height": 480, "encoding": "rgb8"}, "camera_node")
    ros2.publish("/imu/data", {"ax": random.gauss(0, 0.1), "ay": random.gauss(0, 0.1), "gz": random.gauss(0, 0.01)}, "imu_node")
    ros2.publish("/odom", {"x": 1.0+i*0.1, "y": 0.5, "theta": 0.1}, "odom_node")

ros2.publish("/cmd_vel", {"linear": {"x": 0.5}, "angular": {"z": 0.0}}, "navigation_node")
ros2.publish("/robot_status", {"battery": 85, "state": "NAVIGATING"}, "status_node")

# 토픽 목록
print()
print("[Topic Discovery] (DDS SPDP Equivalent)")
topics = ros2.list_topics()
for topic, count in topics.items():
    print(f"  {topic:<25} Messages: {count}")

# 참여자 발견
print()
print("[Participant Discovery]")
participants = ros2.discover_participants()
for p in sorted(participants):
    print(f"  Node: {p}")

# 보안 분석
print()
print("[Security Analysis]")
print("  [!] All topics discoverable via DDS multicast")
print("  [!] No authentication on publishers")
print("  [!] /cmd_vel topic exposed - velocity commands injectable")
print("  [!] Sensor data transmitted without encryption")
PYEOF
```

---

## Part 4: 시리얼 통신 분석 (1:50-2:30)

### 4.1 UART 통신 시뮬레이션

```bash
python3 << 'PYEOF'
import json

class UARTSimulator:
    """UART 시리얼 통신 시뮬레이터"""

    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.buffer = []
        self.log = []

    def send(self, data, source="host"):
        frame = {
            "source": source,
            "data": data,
            "raw_hex": data.encode().hex() if isinstance(data, str) else data.hex(),
            "baudrate": self.baudrate,
        }
        self.buffer.append(frame)
        self.log.append(frame)
        return frame

    def receive(self):
        if self.buffer:
            return self.buffer.pop(0)
        return None

# UART 디버그 콘솔 시뮬레이션
uart = UARTSimulator(115200)

print("=== UART Debug Console Analysis ===")
print(f"  Baudrate: {uart.baudrate}")
print()

# 로봇 부팅 시 UART 출력 시뮬레이션
boot_messages = [
    "U-Boot 2024.01 (Jan 15 2024)",
    "DRAM: 2 GiB",
    "Loading kernel from mmc...",
    "Starting kernel ...",
    "[    0.000000] Linux version 5.15.0-robot",
    "[    1.234567] Robot firmware v2.3.1 initialized",
    "[    1.500000] WiFi: Connected to RobotNet (192.168.1.100)",
    "[    1.600000] ROS2: Starting nodes...",
    "[    2.000000] Robot ready. Default password: robot123",
    "robot-arm login: ",
]

print("[Boot Log Capture]")
for msg in boot_messages:
    frame = uart.send(msg, "robot")
    if "password" in msg.lower():
        print(f"  [VULN] {msg}")
        print(f"         >>> DEFAULT CREDENTIAL LEAKED IN BOOT LOG!")
    elif "version" in msg.lower() or "firmware" in msg.lower():
        print(f"  [INFO] {msg}")
        print(f"         >>> Firmware version disclosed")
    else:
        print(f"  [LOG]  {msg}")

print()

# UART 명령 인젝션
print("[UART Command Injection Test]")
injections = [
    ("root", "Login attempt as root"),
    ("cat /etc/shadow", "Password file access"),
    ("id", "User identification"),
    ("fw_printenv", "Firmware environment dump"),
    ("setenv bootargs init=/bin/sh", "Boot argument manipulation"),
]
for cmd, desc in injections:
    uart.send(cmd, "attacker")
    print(f"  [INJECT] '{cmd}' — {desc}")

print()
print("[Security Findings]")
print("  1. UART debug port accessible without authentication")
print("  2. Default credentials exposed in boot log")
print("  3. Root shell accessible via UART")
print("  4. Firmware environment modifiable")
print("  5. No secure boot — boot arguments can be manipulated")
PYEOF
```

---

## Part 5: 펌웨어 분석 기초 (2:40-3:10)

### 5.1 펌웨어 구조 분석

```bash
python3 << 'PYEOF'
import hashlib
import struct

class FirmwareAnalyzer:
    """로봇 펌웨어 분석 시뮬레이터"""

    def __init__(self):
        self.sections = {}

    def parse_header(self, firmware_data):
        """펌웨어 헤더 파싱"""
        # 시뮬레이션된 펌웨어 헤더
        header = {
            "magic": "RBTFW",
            "version": "2.3.1",
            "build_date": "2024-01-15",
            "arch": "ARM Cortex-A53",
            "size": 16777216,
            "checksum": hashlib.md5(b"firmware_data").hexdigest(),
            "sections": [
                {"name": "bootloader", "offset": 0x0000, "size": 0x10000, "encrypted": False},
                {"name": "kernel", "offset": 0x10000, "size": 0x400000, "encrypted": False},
                {"name": "rootfs", "offset": 0x410000, "size": 0xA00000, "encrypted": False},
                {"name": "config", "offset": 0xE10000, "size": 0x100000, "encrypted": True},
                {"name": "keys", "offset": 0xF10000, "size": 0x10000, "encrypted": True},
            ]
        }
        return header

    def find_strings(self, section_name):
        """문자열 추출 시뮬레이션"""
        strings_db = {
            "bootloader": [
                "U-Boot", "autoboot", "mmc read", "bootargs=",
                "setenv", "saveenv", "DRAM init"
            ],
            "rootfs": [
                "/etc/passwd", "/etc/shadow", "root:$6$hash",
                "robot123", "192.168.1.1", "ssh_host_rsa_key",
                "API_KEY=sk-robot-2026", "/dev/ttyUSB0",
                "ros2 launch", "cmd_vel", "/scan"
            ],
            "config": [
                "[ENCRYPTED SECTION]",
                "WiFi SSID, password, API keys..."
            ]
        }
        return strings_db.get(section_name, ["No strings found"])

# 분석 실행
analyzer = FirmwareAnalyzer()

print("=== Robot Firmware Analysis ===")
print()

# 헤더 분석
header = analyzer.parse_header(None)
print("[Firmware Header]")
print(f"  Magic:    {header['magic']}")
print(f"  Version:  {header['version']}")
print(f"  Build:    {header['build_date']}")
print(f"  Arch:     {header['arch']}")
print(f"  Size:     {header['size']/1024/1024:.1f} MB")
print(f"  Checksum: {header['checksum']}")
print()

# 섹션 분석
print("[Firmware Sections]")
for sec in header['sections']:
    enc = "ENCRYPTED" if sec['encrypted'] else "PLAINTEXT"
    print(f"  {sec['name']:<12} Offset:0x{sec['offset']:06X} Size:0x{sec['size']:06X} [{enc}]")
print()

# 문자열 추출
print("[String Extraction - rootfs]")
strings = analyzer.find_strings("rootfs")
for s in strings:
    if any(kw in s.lower() for kw in ['password', 'key', 'secret', 'robot123']):
        print(f"  [SENSITIVE] {s}")
    else:
        print(f"  [STRING]    {s}")

print()
print("[Security Findings]")
print("  1. Bootloader and kernel sections NOT encrypted")
print("  2. Default credentials found in rootfs: robot123")
print("  3. API key hardcoded: API_KEY=sk-robot-2026")
print("  4. SSH host key embedded in firmware")
print("  5. No secure boot signature verification")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** ROS2 보안 정책을 설계하시오.
- 토픽별 접근 제어 규칙 정의
- DDS Security 설정 (인증, 암호화, 접근제어)
- 펌웨어 보안 강화 방안 (Secure Boot, 암호화)

---

## 참고 자료

- ROS2 Documentation: https://docs.ros.org/
- DDS Security Specification: OMG
- "Robot Security" - OWASP
- "Hacking Robots Before Skynet" - IOActive
