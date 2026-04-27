# Week 15: 종합 평가 — 전체 CPS 침투+방어

## 학습 목표
- 15주간 학습한 CPS 보안 전반을 종합적으로 복습한다
- 드론/자율주행/로봇/ICS/V2X 보안의 핵심을 정리한다
- 전체 CPS에 대한 침투 테스트와 방어를 수행한다
- 종합 평가를 통해 최종 학습 성과를 확인한다

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
| 0:00-0:40 | 종합 복습: 전체 과목 핵심 정리 (Part 1) | 강의 |
| 0:40-1:00 | 전체 공격 표면 매핑 복습 (Part 2) | 토론 |
| 1:00-1:10 | 휴식 | - |
| 1:10-2:10 | 종합 실습: CPS 침투 테스트 (Part 3) | 실습 |
| 2:10-2:20 | 휴식 | - |
| 2:20-2:50 | 종합 실습: CPS 방어 구축 (Part 4) | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:30 | 최종 평가 시험 (Part 5) | 시험 |

---

## Part 1: 전체 과목 핵심 정리 (0:00-0:40)

### 1.1 15주 커리큘럼 핵심 요약

```bash
python3 << 'PYEOF'
curriculum = {
    "전반부: 드론/자율주행 (W01-W08)": {
        "W01 CPS 보안 개론": "CPS 정의, STRIDE, Stuxnet/Triton 사례",
        "W02 드론 기초": "아키텍처, MAVLink, WiFi 제어, 가상 시뮬레이터",
        "W03 드론 해킹": "Deauth, 명령 인젝션, 하이재킹, 리플레이",
        "W04 드론 방어": "RF 탐지, 지오펜싱, 드론 IDS",
        "W05 GPS 보안": "스푸핑, 재밍, 안티스푸핑, 센서 퓨전",
        "W06 자율주행 기초": "SAE 레벨, AI 모델, 센서 퓨전",
        "W07 자율주행 공격": "적대적 패치, CAN 인젝션, OTA 변조",
        "W08 중간 평가": "드론/자율주행 보안 종합",
    },
    "후반부: 로봇/ICS/V2X (W09-W15)": {
        "W09 로봇 보안": "ROS2, 시리얼 통신, 펌웨어 분석",
        "W10 ROS2 보안": "DDS 스니핑, 토픽 인젝션, DDS Security",
        "W11 OT/ICS 보안": "PLC, Modbus, SCADA, Stuxnet 심화",
        "W12 V2X/자동차": "CAN 버스, ECU, 커넥티드카, V2X",
        "W13 AI 모델 공격": "FGSM/PGD/C&W, 로버스트니스, 방어",
        "W14 CPS IR": "사이버물리 인시던트 대응 특수성",
        "W15 종합 평가": "전체 CPS 침투+방어",
    }
}

for section, weeks in curriculum.items():
    print(f"\n{'='*60}")
    print(f"  {section}")
    print(f"{'='*60}")
    for week, summary in weeks.items():
        print(f"  {week}")
        print(f"    → {summary}")
PYEOF
```

### 1.2 핵심 기술 매트릭스

```bash
python3 << 'PYEOF'
matrix = [
    ("CPS 시스템",  "공격 기법",        "방어 기법",           "프로토콜"),
    ("─"*12,       "─"*16,            "─"*18,               "─"*12),
    ("드론",       "Deauth/하이재킹",   "MAVLink 서명/IDS",    "MAVLink"),
    ("GPS",        "스푸핑/재밍",       "멀티소스 항법/퓨전",   "NMEA/L1"),
    ("자율주행",    "적대적 패치",       "앙상블/전처리",        "CAN/Ethernet"),
    ("자동차",      "CAN 인젝션",       "SecOC/Gateway IDS",   "CAN/CAN-FD"),
    ("로봇/ROS2",  "토픽 인젝션",       "DDS Security/SROS2",  "DDS/RTPS"),
    ("ICS/SCADA",  "Modbus 변조",      "네트워크 분리/IDS",    "Modbus/DNP3"),
    ("V2X",        "메시지 위조/Sybil", "PKI 인증/SCMS",       "DSRC/C-V2X"),
    ("AI 모델",    "FGSM/PGD/C&W",    "적대적 훈련/탐지",     "─"),
]

for row in matrix:
    print(f"  {row[0]:<14} {row[1]:<18} {row[2]:<20} {row[3]:<14}")
PYEOF
```

---

## Part 2: 전체 공격 표면 매핑 (0:40-1:00)

### 2.1 CPS 통합 공격 표면

```bash
python3 << 'PYEOF'
attack_surface = {
    "Communication Layer": [
        ("WiFi/RF", "드론 제어", "Deauth, 스니핑, 하이재킹"),
        ("GPS", "항법", "스푸핑, 재밍"),
        ("CAN Bus", "차량 내부", "인젝션, DoS, 리플레이"),
        ("DDS/ROS2", "로봇 통신", "토픽 인젝션, 스니핑"),
        ("Modbus", "ICS 제어", "레지스터 변조, 명령 위조"),
        ("V2X", "차량간 통신", "메시지 위조, Sybil"),
    ],
    "Sensor/Perception Layer": [
        ("Camera", "영상 인식", "적대적 패치, 블라인딩"),
        ("LiDAR", "3D 인지", "레이저 스푸핑"),
        ("GPS", "위치 결정", "스푸핑"),
        ("IMU", "자세 측정", "음향 공격"),
        ("Modbus Sensors", "프로세스 측정", "값 변조"),
    ],
    "Software/AI Layer": [
        ("AI Model", "객체 탐지", "FGSM/PGD 적대적 공격"),
        ("Firmware", "장치 소프트웨어", "변조, 백도어"),
        ("OTA Update", "원격 업데이트", "MitM, 롤백"),
        ("PLC Logic", "제어 로직", "로직 변조"),
    ],
    "Physical Layer": [
        ("Debug Port", "UART/JTAG", "물리적 접근 → 루트 셸"),
        ("OBD-II", "차량 진단", "직접 CAN 접근"),
        ("USB", "미디어/업데이트", "악성 펌웨어 주입"),
    ],
}

total = 0
print("=== Comprehensive CPS Attack Surface ===")
for layer, attacks in attack_surface.items():
    print(f"\n[{layer}]")
    for interface, target, attack in attacks:
        print(f"  {interface:<16} → {target:<16} | {attack}")
        total += 1
print(f"\nTotal attack vectors: {total}")
PYEOF
```

---

## Part 3: CPS 침투 테스트 종합 실습 (1:10-2:10)

### 3.1 전체 CPS 환경 침투 테스트

```bash
python3 << 'PYEOF'
import json
import socket

print("=" * 65)
print("  FINAL LAB: Comprehensive CPS Penetration Test")
print("=" * 65)
print()

# ===== Phase 1: 정찰 =====
print("[PHASE 1] RECONNAISSANCE")
print("─" * 50)

# 네트워크 스캔
targets = {
    "10.20.30.1":   {"name": "Firewall/IPS", "ports": [22]},
    "10.20.30.80":  {"name": "Web Server", "ports": [22, 80, 3000]},
    "10.20.30.100": {"name": "SIEM", "ports": [22, 443, 1514]},
    "10.20.30.200": {"name": "Manager/LLM + PLC Sim", "ports": [22, 502, 9999, 11434]},
    "10.20.30.201": {"name": "Attacker", "ports": [22]},
}

for ip, info in targets.items():
    print(f"  {ip:<16} {info['name']:<25} Ports: {info['ports']}")

print()

# ===== Phase 2: 드론 침투 =====
print("[PHASE 2] DRONE PENETRATION TEST")
print("─" * 50)
drone_results = [
    ("Port Scan", "9999/UDP open — Virtual Drone Simulator", "INFO"),
    ("Auth Sniff", "Plaintext auth key visible in traffic", "CRITICAL"),
    ("Command Injection", "ARM/TAKEOFF accepted without auth", "CRITICAL"),
    ("GPS Spoofing", "GPS position manipulated successfully", "HIGH"),
    ("Geofence Bypass", "Bypassed via GPS spoofing", "HIGH"),
]
for test, result, severity in drone_results:
    print(f"  [{severity:8}] {test}: {result}")
print()

# ===== Phase 3: ICS/Modbus 침투 =====
print("[PHASE 3] ICS/MODBUS PENETRATION TEST")
print("─" * 50)
ics_results = [
    ("Modbus Scan", "Port 502 open — Modbus TCP service", "INFO"),
    ("Register Read", "All registers readable without auth", "HIGH"),
    ("Register Write", "Process values writable from any IP", "CRITICAL"),
    ("Coil Control", "Actuators (pumps, valves) controllable", "CRITICAL"),
    ("HMI Deception", "Fake values sent to operator display", "CRITICAL"),
]
for test, result, severity in ics_results:
    print(f"  [{severity:8}] {test}: {result}")
print()

# ===== Phase 4: ROS2 침투 =====
print("[PHASE 4] ROS2/ROBOT PENETRATION TEST")
print("─" * 50)
ros2_results = [
    ("DDS Discovery", "All nodes/topics discoverable", "HIGH"),
    ("Topic Sniffing", "Sensor data captured without auth", "HIGH"),
    ("cmd_vel Injection", "Velocity commands injectable", "CRITICAL"),
    ("Parameter Tampering", "Robot parameters modifiable", "HIGH"),
    ("UART Debug", "Root shell via debug port", "CRITICAL"),
]
for test, result, severity in ros2_results:
    print(f"  [{severity:8}] {test}: {result}")
print()

# ===== Phase 5: AI/자율주행 침투 =====
print("[PHASE 5] AI/AUTONOMOUS VEHICLE PENETRATION TEST")
print("─" * 50)
av_results = [
    ("Adversarial Patch", "Stop sign misclassified (FGSM eps=0.3)", "CRITICAL"),
    ("CAN Injection", "Steering/brake commands injectable", "CRITICAL"),
    ("OTA Verification", "Signature check present but rollback possible", "HIGH"),
    ("V2X Spoofing", "Fake V2V messages accepted", "HIGH"),
]
for test, result, severity in av_results:
    print(f"  [{severity:8}] {test}: {result}")
print()

# ===== 종합 결과 =====
print("=" * 65)
print("  PENETRATION TEST SUMMARY")
print("=" * 65)
all_results = drone_results + ics_results + ros2_results + av_results
critical = sum(1 for _, _, s in all_results if s == "CRITICAL")
high = sum(1 for _, _, s in all_results if s == "HIGH")
total = len(all_results)
print(f"  Total findings: {total}")
print(f"  CRITICAL: {critical}")
print(f"  HIGH:     {high}")
print(f"  INFO:     {total - critical - high}")
print(f"  Overall Risk: {'CRITICAL' if critical > 5 else 'HIGH'}")
PYEOF
```

---

## Part 4: CPS 방어 구축 종합 (2:20-2:50)

### 4.1 전체 방어 체계 구축

```bash
python3 << 'PYEOF'
print("=" * 65)
print("  CPS DEFENSE ARCHITECTURE - Implementation Plan")
print("=" * 65)
print()

defenses = {
    "Network Security": [
        ("OT/IT 네트워크 분리", "Purdue 모델 기반 세그멘테이션", "CRITICAL"),
        ("방화벽 규칙", "Modbus/CAN/DDS 포트별 접근 제어", "CRITICAL"),
        ("IDS/IPS", "Suricata + CPS 전용 규칙셋", "CRITICAL"),
        ("암호화 통신", "TLS/DTLS for command channels", "HIGH"),
    ],
    "Drone Security": [
        ("MAVLink v2 Signing", "명령 무결성 보장", "CRITICAL"),
        ("암호화 제어 채널", "DTLS over UDP", "HIGH"),
        ("GPS 안티스푸핑", "멀티소스 항법 + SNR 검증", "HIGH"),
        ("지오펜싱 강화", "서버 측 위치 검증", "MEDIUM"),
        ("드론 IDS", "명령 패턴 이상 탐지", "HIGH"),
    ],
    "ICS/SCADA Security": [
        ("Modbus 인증", "OPC-UA Secure 마이그레이션", "CRITICAL"),
        ("PLC 무결성", "로직 해시 검증", "HIGH"),
        ("HMI 독립 검증", "독립 센서로 교차 검증", "HIGH"),
        ("안전 시스템(SIS) 분리", "SIS 독립 네트워크", "CRITICAL"),
    ],
    "Robot/ROS2 Security": [
        ("DDS Security", "인증+암호화+접근제어", "CRITICAL"),
        ("토픽 ACL", "노드별 발행/구독 권한", "HIGH"),
        ("Secure Boot", "펌웨어 서명 검증", "HIGH"),
        ("UART 비활성화", "프로덕션에서 디버그 포트 차단", "MEDIUM"),
    ],
    "Vehicle Security": [
        ("CAN 인증(SecOC)", "ECU 메시지 인증", "CRITICAL"),
        ("Gateway 방화벽", "도메인 간 메시지 필터링", "CRITICAL"),
        ("V2X PKI", "SCMS 기반 인증서 체계", "HIGH"),
        ("OTA Uptane", "안전한 업데이트 프레임워크", "HIGH"),
        ("CAN IDS", "메시지 빈도/패턴 이상 탐지", "HIGH"),
    ],
    "AI Model Security": [
        ("적대적 훈련", "FGSM/PGD 적대적 예시 학습", "HIGH"),
        ("입력 검증", "센서 퓨전 교차 검증", "CRITICAL"),
        ("앙상블 추론", "다중 모델 투표", "MEDIUM"),
        ("모델 무결성", "추론 모델 서명 검증", "HIGH"),
    ],
    "Incident Response": [
        ("CPS IR 플레이북", "시나리오별 대응 절차", "CRITICAL"),
        ("물리 안전 우선", "자동 안전 모드 전환", "CRITICAL"),
        ("포렌식 준비", "OT 로그 + 물리 센서 기록", "HIGH"),
        ("훈련/연습", "정기 CPS 사이버 훈련", "HIGH"),
    ],
}

total_controls = 0
implemented = 0
for category, controls in defenses.items():
    print(f"[{category}]")
    for control, desc, priority in controls:
        total_controls += 1
        status = "[ ]"
        print(f"  {status} [{priority:8}] {control}")
        print(f"               {desc}")
    print()

print(f"Total security controls: {total_controls}")
critical_controls = sum(1 for _, controls in defenses.items()
                       for _, _, p in controls if p == "CRITICAL")
print(f"Critical controls: {critical_controls}")
print(f"Implementation priority: Address all CRITICAL controls first")
PYEOF
```

### 4.2 LLM 활용 보안 평가 보고서

```bash
curl -s ${LLM_URL:-http://localhost:8003}/api/chat \
  -d '{
    "model":"gemma3:4b",
    "messages":[
      {"role":"system","content":"You are a CPS security consultant writing an executive summary."},
      {"role":"user","content":"Write a 5-sentence executive summary of a CPS security assessment that found critical vulnerabilities in drone control (no MAVLink signing), ICS (unauthenticated Modbus), robot systems (no DDS security), and autonomous vehicles (CAN bus injection). Include risk rating and top 3 recommendations."}
    ],
    "stream":false,
    "options":{"num_predict":250}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
```

---

## Part 5: 최종 평가 시험 (3:00-3:30)

### 필기 시험 (50점)

**A. 객관식 (각 2점, 20점)**

1. CPS에서 물리적 안전보다 사이버 격리를 우선해야 하는 경우는?
   - a) 항상  b) 인명 위험이 없을 때  c) 없음(항상 안전 우선)  d) 경영진 판단

2. MAVLink v2 서명이 보호하는 것은?
   - a) 기밀성  b) 무결성  c) 가용성  d) 부인방지

3. Modbus TCP와 OPC-UA의 가장 큰 차이는?
   - a) 속도  b) 포트 번호  c) 내장 보안(인증/암호화)  d) 데이터 크기

4. 자율주행에서 적대적 패치가 위험한 근본 이유는?
   - a) AI 모델의 입력 공간이 고차원  b) 카메라 해상도  c) 속도  d) 네트워크

5. ROS2 DDS에서 토픽 인젝션이 가능한 이유는?
   - a) TCP 사용  b) 기본 보안 비활성화  c) QoS  d) 토픽 이름

6. CAN 버스에서 우선순위를 결정하는 것은?
   - a) 데이터 길이  b) 중재 ID (낮을수록 높은 우선순위)  c) 전송 시간  d) ECU 종류

7. GPS 스푸핑 탐지에 효과적인 방법은?
   - a) 신호 강도(SNR) 이상 탐지  b) 안테나 크기  c) 위성 수  d) 주파수

8. Stuxnet이 운영자를 기만한 방법은?
   - a) HMI에 정상 값 표시  b) 경보 끄기  c) 카메라 차단  d) 네트워크 차단

9. CPS IR에서 다학제 팀이 필요한 이유는?
   - a) 인력 부족  b) 사이버+물리 전문지식 모두 필요  c) 비용  d) 규정

10. Uptane 프레임워크의 목적은?
    - a) CAN 보안  b) 안전한 자동차 OTA 업데이트  c) V2X 통신  d) GPS 보안

**B. 서술형 (각 6점, 30점)**

11. 드론, 자율주행차, 산업 로봇 각각에서 가장 위험한 공격 벡터를 하나씩 선택하고, 공격 원리와 방어 방법을 설명하시오.

12. Modbus 기반 수처리 시설이 해킹당했을 때의 인시던트 대응 절차를 6단계로 작성하시오.

13. ROS2 DDS Security를 적용하지 않은 로봇 시스템의 위험을 3가지 공격 시나리오로 설명하고, 각 대응 방안을 쓰시오.

14. CAN 버스에 인증이 없는 역사적 이유를 설명하고, 현재 사용 가능한 인증 기술(SecOC)의 원리를 서술하시오.

15. AI 모델 적대적 공격에서 FGSM, PGD, C&W의 장단점을 비교하고, CPS 환경에서 가장 현실적 위협이 되는 것과 그 이유를 쓰시오.

### 실기 시험 (50점)

주어진 가상 CPS 환경에서 다음을 수행하시오:

1. (10점) 네트워크 정찰 — CPS 자산과 서비스 식별
2. (15점) 취약점 발견 및 공격 — 드론 OR ICS 택1 침투
3. (15점) 방어 구축 — 발견한 취약점에 대한 IDS 규칙 작성
4. (10점) 인시던트 보고서 — 공격 타임라인, 영향, 대응 방안

---

## 과목 마무리

### 핵심 메시지

> CPS 보안은 사이버 세계와 물리 세계의 교차점에 있다.
> 코드 한 줄의 취약점이 물리적 파괴와 인명 사고로 이어질 수 있다.
> "안전(Safety)"과 "보안(Security)"은 CPS에서 분리될 수 없다.

### 향후 학습 경로

```
CPS 보안 전문가 경로:
├── 심화: ICS/SCADA 보안 전문 (GICSP 자격)
├── 심화: 자동차 사이버보안 (ISO/SAE 21434)
├── 심화: 드론/UAV 보안 연구
├── 심화: AI 보안/적대적 ML
└── 실무: CPS 침투 테스트/보안 컨설팅
```

---

## 참고 자료

- 전체 강의 자료 (Week 01-14)
- NIST Cybersecurity Framework for CPS
- MITRE ATT&CK for ICS
- ISO/SAE 21434: Automotive Cybersecurity
- IEC 62443: Industrial Automation Security

---

## 실제 사례 (WitFoo Precinct 6 — 종합 Autonomous Eval)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *종합 Autonomous Eval* 학습 항목 매칭.

### 종합 Autonomous Eval 의 dataset 흔적 — "전체 시스템"

dataset 의 정상 운영에서 *전체 시스템* 신호의 baseline 을 알아두면, *종합 Autonomous Eval* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — 5축 평가.

```mermaid
graph LR
    SCENE["종합 Autonomous Eval 시나리오"]
    TRACE["dataset 흔적<br/>전체 시스템"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | 전체 시스템 |
| 정량 baseline | 5축 평가 |
| 학습 매핑 | 최종 평가 |

**자세한 해석**: 최종 평가. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | 전체 시스템 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **종합 Autonomous Eval = 전체 시스템 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — 5축 평가.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: 종합 보고.

