# Week 14: CPS 인시던트 대응 — 사이버물리 인시던트 특수성

## 학습 목표
- CPS 인시던트 대응의 특수성을 이해한다
- 물리적 안전과 사이버 대응의 우선순위를 판단할 수 있다
- CPS 사고 조사 프레임워크를 적용할 수 있다
- 드론/자율주행/ICS 인시던트 시나리오를 분석하고 대응할 수 있다
- 인시던트 대응 플레이북을 작성할 수 있다

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
| 0:00-0:30 | 이론: CPS 인시던트 특수성 (Part 1) | 강의 |
| 0:30-1:00 | 이론: CPS IR 프레임워크 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 드론 인시던트 대응 (Part 3) | 실습 |
| 1:50-2:30 | 실습: ICS 인시던트 대응 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 인시던트 대응 플레이북 작성 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: CPS 인시던트 특수성 (0:00-0:30)

### 1.1 IT IR vs CPS IR 비교

| 차원 | IT 인시던트 | CPS 인시던트 |
|------|------------|--------------|
| 최우선 조치 | 격리/차단 | 물리적 안전 확보 |
| 영향 범위 | 데이터/서비스 | 물리 세계 (인명, 환경) |
| 격리 방법 | 네트워크 분리 | 수동 모드 전환 (불가능할 수 있음) |
| 포렌식 | 디스크/메모리/로그 | + 물리 센서 데이터, PLC 메모리 |
| 복구 | 백업 복원 | 물리 장치 점검 + 프로세스 재시작 |
| 법적 체계 | 정보통신법 | + 항공법, 산업안전법, 원자력법 |
| 전문성 | IT/보안 | + 제어공학, 물리공정 지식 |

### 1.2 CPS IR 핵심 원칙

```
원칙 1: 안전 최우선 (Safety First)
  └─ 사이버 대응보다 물리적 안전이 항상 우선
  └─ 인명 피해 방지 > 증거 보전 > 시스템 복구

원칙 2: 물리적 영향 평가 (Physical Impact Assessment)
  └─ 사이버 공격이 물리 프로세스에 미치는 영향 즉시 평가
  └─ 안전 한계값 초과 여부 확인

원칙 3: 수동 전환 준비 (Manual Override)
  └─ 자동화 시스템 신뢰 불가 시 수동 제어로 전환
  └─ 운영자가 수동 조작할 준비 항상 유지

원칙 4: 다학제 대응팀 (Multidisciplinary Team)
  └─ IT/OT 보안 + 제어공학 + 안전관리 + 법무
  └─ 물리 프로세스 전문가가 반드시 참여

원칙 5: 최소 영향 대응 (Minimal Disruption)
  └─ 가능하면 프로세스 중단 없이 대응
  └─ 격리 시 물리적 파급 효과 사전 평가
```

### 1.3 CPS 인시던트 유형

```
유형 1: 사이버 → 물리 (Cyber-to-Physical)
  예: PLC 해킹 → 밸브 오작동 → 유출 사고
  대응: 물리 안전 확보 → 사이버 격리

유형 2: 물리 → 사이버 (Physical-to-Cyber)
  예: 센서 스푸핑 → 잘못된 자동 대응 → 연쇄 사고
  대응: 센서 신뢰도 평가 → 수동 모드 전환

유형 3: 사이버+물리 동시 (Combined)
  예: 통신 재밍 + 물리적 침입
  대응: 양면 동시 대응팀 운영
```

---

## Part 2: CPS IR 프레임워크 (0:30-1:00)

### 2.1 CPS 인시던트 대응 6단계

```
1. 탐지/알림 (Detection)
   ├── 사이버 IDS/IPS 경고
   ├── 물리 프로세스 이상 감지
   ├── 안전 시스템(SIS) 트리거
   └── 운영자 관찰

2. 물리 안전 확보 (Physical Safety)
   ├── 인명 대피 (필요시)
   ├── 위험 프로세스 안전 정지
   ├── 수동 제어 전환
   └── 안전 계장 시스템(SIS) 확인

3. 격리/봉쇄 (Containment)
   ├── 영향받은 네트워크 세그먼트 분리
   ├── 침해된 ECU/PLC 격리
   ├── 백업 시스템으로 전환
   └── (주의: 격리가 물리 안전에 미치는 영향 평가)

4. 조사/분석 (Investigation)
   ├── 사이버 포렌식 (로그, 패킷, 메모리)
   ├── 물리 포렌식 (센서 데이터, PLC 로직)
   ├── 타임라인 재구성
   └── 공격 벡터 확인

5. 제거/복구 (Eradication & Recovery)
   ├── 악성코드/변조 코드 제거
   ├── PLC/펌웨어 알려진 안전 버전으로 복원
   ├── 물리 장비 점검 후 재시작
   └── 단계적 정상 운영 복구

6. 사후 분석 (Post-Incident)
   ├── 근본 원인 분석 (Root Cause)
   ├── 보안 개선 조치
   ├── 규제 보고 (해당 시)
   └── 대응 절차 업데이트
```

---

## Part 3: 드론 인시던트 대응 (1:10-1:50)

### 3.1 드론 인시던트 시나리오 실습

```bash
python3 << 'PYEOF'
import json
import time

class DroneIncidentResponse:
    """드론 보안 인시던트 대응 시뮬레이터"""

    def __init__(self):
        self.timeline = []
        self.severity = "UNKNOWN"
        self.status = "ACTIVE"

    def log(self, time_str, event, action, priority="NORMAL"):
        entry = {"time": time_str, "event": event, "action": action, "priority": priority}
        self.timeline.append(entry)
        return entry

    def print_timeline(self):
        for e in self.timeline:
            marker = "[!]" if e["priority"] == "CRITICAL" else "[ ]"
            print(f"  {marker} {e['time']} | {e['event']}")
            print(f"       Action: {e['action']}")

# 시나리오: 배달 드론 하이재킹 인시던트
ir = DroneIncidentResponse()

print("=" * 65)
print("  INCIDENT RESPONSE: Delivery Drone Hijack Scenario")
print("=" * 65)
print()

# Phase 1: 탐지
print("[Phase 1: DETECTION]")
ir.log("14:23:00", "IDS Alert: Unknown source sending commands to drone fleet",
       "Notify SOC and drone operations team", "CRITICAL")
ir.log("14:23:15", "Drone D-042 deviating from planned route",
       "Verify with GCS telemetry", "CRITICAL")
ir.log("14:23:30", "GPS anomaly detected on D-042: SNR spike to 55 dB-Hz",
       "Flag as potential GPS spoofing", "CRITICAL")
ir.print_timeline()
print()

# Phase 2: 안전 확보
ir.timeline.clear()
print("[Phase 2: PHYSICAL SAFETY]")
ir.log("14:24:00", "D-042 heading toward restricted airspace",
       "Attempt Return-To-Launch (RTL) command", "CRITICAL")
ir.log("14:24:15", "RTL command rejected — control channel compromised",
       "Activate geofence kill switch if available", "CRITICAL")
ir.log("14:24:30", "Notify airspace authorities (ATC) of rogue drone",
       "Alert ground personnel in projected path", "CRITICAL")
ir.log("14:25:00", "D-042 payload weight: 2.5kg — assess collision risk",
       "Evacuate potential impact area", "CRITICAL")
ir.print_timeline()
print()

# Phase 3: 봉쇄
ir.timeline.clear()
print("[Phase 3: CONTAINMENT]")
ir.log("14:26:00", "Isolate drone fleet communication channel",
       "Switch remaining drones to secondary encrypted channel")
ir.log("14:26:30", "Ground all other drones in fleet",
       "Issue fleet-wide RTL on secure channel")
ir.log("14:27:00", "Block attacker IP at network perimeter",
       "Update firewall rules on secu (10.20.30.1)")
ir.log("14:27:30", "Revoke compromised authentication keys",
       "Rotate all drone fleet API keys")
ir.print_timeline()
print()

# Phase 4: 조사
ir.timeline.clear()
print("[Phase 4: INVESTIGATION]")
ir.log("14:30:00", "Collect GCS logs, drone telemetry, network captures",
       "Preserve evidence chain of custody")
ir.log("14:35:00", "Analyze attack vector: sniffed auth key via plaintext UDP",
       "Confirm lack of MAVLink signing")
ir.log("14:40:00", "Attacker IP traced to 10.20.30.201 (known test machine)",
       "Check for unauthorized access")
ir.log("14:45:00", "GPS spoofing confirmed: deauth + reconnect + GPS fake",
       "Full attack chain documented")
ir.print_timeline()
print()

# 요약
print("[INCIDENT SUMMARY]")
print(f"  Severity: CRITICAL")
print(f"  Type: Drone hijacking via communication channel compromise")
print(f"  Attack vector: Plaintext auth key sniffing + GPS spoofing")
print(f"  Physical impact: Drone deviated ~2km from planned route")
print(f"  Resolution: Drone recovered after battery depletion landing")
print(f"  Root cause: No encryption on command channel, no MAVLink signing")
PYEOF
```

---

## Part 4: ICS 인시던트 대응 (1:50-2:30)

### 4.1 ICS 인시던트 대응 시뮬레이션

```bash
python3 << 'PYEOF'
print("=" * 65)
print("  INCIDENT RESPONSE: Water Treatment Plant SCADA Compromise")
print("=" * 65)
print()

# Phase 1: 탐지
print("[Phase 1: DETECTION]")
alerts = [
    ("09:15:00", "SIEM", "Modbus write from unauthorized IP (10.20.30.201)"),
    ("09:15:05", "PLC IDS", "Holding register 0 changed: 250→999 (water level)"),
    ("09:15:10", "Process Alarm", "Water level HIGH HIGH alarm triggered"),
    ("09:15:15", "PLC IDS", "Coil 10 (emergency stop) written by external source"),
    ("09:15:20", "HMI", "Operator reports: display shows normal but alarms firing"),
]
for t, src, msg in alerts:
    print(f"  [{t}] {src}: {msg}")
print()

# Phase 2: 안전 확보
print("[Phase 2: PHYSICAL SAFETY — IMMEDIATE ACTIONS]")
safety_actions = [
    ("09:16:00", "Switch to MANUAL control — do NOT trust HMI readings"),
    ("09:16:10", "Operator physically checks water level gauge → CONFIRMS overflow risk"),
    ("09:16:20", "Manually close inlet valve to prevent overflow"),
    ("09:16:30", "Verify pump status at physical location"),
    ("09:16:45", "Chemical dosing: manually check pH level at sampling point"),
    ("09:17:00", "Confirm all Safety Instrumented Systems (SIS) functioning"),
]
for t, action in safety_actions:
    print(f"  [{t}] {action}")
print()

# Phase 3: 봉쇄
print("[Phase 3: CONTAINMENT]")
containment = [
    "Disconnect compromised PLC from network (physical ethernet unplug)",
    "Block Modbus port 502 at IT/OT firewall",
    "Switch to backup PLC if available",
    "Isolate historian server to preserve logs",
    "Activate incident response team (IT + OT + Safety)",
]
for i, action in enumerate(containment, 1):
    print(f"  {i}. {action}")
print()

# Phase 4: 조사
print("[Phase 4: INVESTIGATION]")
findings = [
    ("Attack entry", "Modbus TCP from 10.20.30.201 (no auth required)"),
    ("Attack method", "Direct register/coil write via Function Code 0x06, 0x05"),
    ("HMI deception", "Attacker sent normal values to HMI while modifying PLC"),
    ("Duration", "~15 minutes before detection"),
    ("Impact", "Water level exceeded safe limit, pH dropped to 2.0"),
    ("Root cause", "No Modbus authentication, flat OT network"),
]
for finding, detail in findings:
    print(f"  {finding}: {detail}")
print()

# 교훈
print("[LESSONS LEARNED]")
lessons = [
    "1. Implement Modbus/TCP authentication (or migrate to OPC-UA Secure)",
    "2. Segment OT network — PLC should not be reachable from IT",
    "3. Deploy ICS-specific IDS (e.g., Suricata with Modbus rules)",
    "4. HMI integrity: cross-check with independent sensor readings",
    "5. Regular OT security assessments and penetration testing",
    "6. Operator training: recognize cyber-physical attack indicators",
]
for l in lessons:
    print(f"  {l}")
PYEOF
```

---

## Part 5: 인시던트 대응 플레이북 작성 (2:40-3:10)

### 5.1 CPS IR 플레이북 생성기

```bash
python3 << 'PYEOF'
import json

def generate_playbook(scenario):
    """CPS 인시던트 대응 플레이북 생성"""
    playbook = {
        "title": scenario["title"],
        "severity": scenario["severity"],
        "category": scenario["category"],
        "phases": {
            "detection": {
                "indicators": scenario["indicators"],
                "tools": scenario["detection_tools"],
            },
            "safety": {
                "immediate_actions": scenario["safety_actions"],
                "escalation": scenario["escalation"],
            },
            "containment": {
                "network": scenario["containment_network"],
                "physical": scenario["containment_physical"],
            },
            "investigation": {
                "evidence": scenario["evidence_sources"],
                "analysis": scenario["analysis_steps"],
            },
            "recovery": {
                "steps": scenario["recovery_steps"],
                "validation": scenario["validation"],
            },
        }
    }
    return playbook

# 드론 하이재킹 플레이북
drone_scenario = {
    "title": "Drone Fleet Hijacking Response",
    "severity": "CRITICAL",
    "category": "CPS-UAV",
    "indicators": [
        "Unauthorized command source detected by IDS",
        "Drone deviation from planned route",
        "GPS SNR anomaly (spoofing indicator)",
        "Communication channel authentication failure",
    ],
    "detection_tools": ["Drone IDS", "GCS Telemetry", "RF Monitor", "SIEM"],
    "safety_actions": [
        "Issue RTL to all fleet drones",
        "Activate geofence enforcement",
        "Notify airspace authorities",
        "Alert ground personnel in projected path",
    ],
    "escalation": ["SOC Lead", "Drone Operations Manager", "Aviation Authority"],
    "containment_network": [
        "Switch to backup encrypted command channel",
        "Revoke compromised API keys",
        "Block attacker source at firewall",
    ],
    "containment_physical": [
        "Ground all fleet drones",
        "Physical recovery of hijacked drone",
    ],
    "evidence_sources": [
        "GCS logs", "Drone flight recorder", "Network pcap",
        "RF spectrum recordings", "SIEM alerts",
    ],
    "analysis_steps": [
        "Reconstruct attack timeline",
        "Identify attack vector (WiFi/GPS/command)",
        "Determine compromised credentials",
        "Assess physical damage/risk",
    ],
    "recovery_steps": [
        "Rotate all fleet authentication keys",
        "Enable MAVLink v2 signing",
        "Implement encrypted command channel",
        "Update geofencing database",
    ],
    "validation": [
        "Test drone communication integrity",
        "Verify geofence enforcement",
        "Conduct penetration test on new controls",
    ],
}

playbook = generate_playbook(drone_scenario)

print("=== CPS Incident Response Playbook ===")
print()
print(f"Title: {playbook['title']}")
print(f"Severity: {playbook['severity']}")
print(f"Category: {playbook['category']}")
print()

for phase, content in playbook['phases'].items():
    print(f"[{phase.upper()}]")
    for key, items in content.items():
        print(f"  {key}:")
        if isinstance(items, list):
            for item in items:
                print(f"    - {item}")
        else:
            print(f"    {items}")
    print()
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** 다음 3가지 CPS 시나리오 중 1개를 선택하여 인시던트 대응 플레이북을 작성하시오.
1. 자율주행 차량 원격 조향 탈취
2. 산업 로봇 안전 펜스 우회 공격
3. 스마트 그리드 SCADA 변전소 공격

---

## 참고 자료

- NIST SP 800-61: Computer Security Incident Handling Guide
- ICS-CERT: Industrial Control Systems Cyber Emergency Response Team
- MITRE ATT&CK for ICS
- "Incident Response for ICS/SCADA" - SANS

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

