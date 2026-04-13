# Week 08: 중간 평가 — 드론/자율주행 보안 종합

## 학습 목표
- Week 01~07의 핵심 개념을 종합적으로 복습한다
- CPS 보안의 전체 공격/방어 체계를 정리한다
- 드론과 자율주행 보안 시나리오를 통합 실습한다
- 중간 평가를 통해 학습 성과를 확인한다
- 후반부 학습(로봇, ICS, V2X)의 기초를 다진다

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
| 0:00-0:40 | 종합 복습: CPS/드론/자율주행 핵심 정리 (Part 1) | 강의 |
| 0:40-1:00 | 복습: 공격/방어 체계 매핑 (Part 2) | 토론 |
| 1:00-1:10 | 휴식 | - |
| 1:10-2:00 | 통합 실습: 드론 침투+방어 시나리오 (Part 3) | 실습 |
| 2:00-2:10 | 휴식 | - |
| 2:10-2:50 | 통합 실습: 자율주행 보안 평가 (Part 4) | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:30 | 중간 평가 시험 (Part 5) | 시험 |

---

## Part 1: 종합 복습 (0:00-0:40)

### 1.1 Week 01~07 핵심 요약

```
Week 01: CPS 보안 개론
├── CPS = 사이버 + 물리 + 네트워크
├── IT 보안과 CPS 보안의 차이 (안전성 우선)
├── STRIDE 위협 모델
└── Stuxnet, Triton 사례

Week 02: 드론 기초
├── 드론 아키텍처 (FC, 센서, 통신)
├── MAVLink 프로토콜
├── WiFi 기반 제어 구조
└── 가상 드론 시뮬레이터

Week 03: 드론 해킹
├── WiFi Deauth 공격
├── 명령어 인젝션
├── 드론 하이재킹 (SkyJack)
└── 리플레이 공격

Week 04: 드론 방어
├── 드론 탐지 (RF, 음향, 영상)
├── 지오펜싱 구현/우회
├── 안티드론 시스템
└── 드론 IDS

Week 05: GPS 보안
├── GPS 동작 원리 (삼변측량)
├── GPS 스푸핑/재밍
├── 안티스푸핑 탐지
└── 센서 퓨전 (GPS+INS)

Week 06: 자율주행 기초
├── SAE 레벨 (L0~L5)
├── 인지-판단-제어 파이프라인
├── AI 모델 (YOLO, CNN)
└── 센서 퓨전 (카메라+LiDAR+레이더)

Week 07: 자율주행 공격
├── 적대적 패치/FGSM
├── CAN 버스 인젝션
├── OTA 업데이트 변조
└── LiDAR/센서 스푸핑
```

### 1.2 핵심 개념 비교표

```bash
python3 << 'PYEOF'
concepts = [
    ("CPS vs IT 보안", "물리적 안전 우선", "기밀성 우선"),
    ("드론 통신", "MAVLink over WiFi/UDP", "HTTP/HTTPS"),
    ("GPS 공격", "스푸핑(위치 속이기)", "재밍(통신 차단)"),
    ("적대적 공격", "물리적 패치", "디지털 섭동"),
    ("CAN 버스", "인증 없음/브로드캐스트", "포인트-투-포인트/TLS"),
    ("드론 방어", "RF탐지+지오펜싱+IDS", "방화벽+IPS+SIEM"),
    ("OTA 보안", "서명+해시+롤백방지", "HTTPS+패키지서명"),
]

print("=" * 75)
print(f"{'주제':<20} {'CPS/자율시스템':<25} {'전통 IT':<25}")
print("=" * 75)
for topic, cps, it in concepts:
    print(f"{topic:<20} {cps:<25} {it:<25}")
print("=" * 75)
PYEOF
```

---

## Part 2: 공격/방어 체계 매핑 (0:40-1:00)

### 2.1 CPS 공격-방어 매트릭스

```bash
python3 << 'PYEOF'
matrix = {
    "WiFi Deauth": {
        "대상": "드론 통신",
        "영향": "제어 상실",
        "방어": "802.11w PMF, 주파수 호핑",
        "주차": "Week 03"
    },
    "GPS 스푸핑": {
        "대상": "드론/자율주행 항법",
        "영향": "위치 기만, 유도",
        "방어": "멀티소스 항법, SNR 검증",
        "주차": "Week 05"
    },
    "명령어 인젝션": {
        "대상": "MAVLink 제어",
        "영향": "드론 탈취",
        "방어": "MAVLink 서명, 인증",
        "주차": "Week 03"
    },
    "적대적 패치": {
        "대상": "카메라 AI 인식",
        "영향": "객체 오분류",
        "방어": "앙상블, 입력 전처리",
        "주차": "Week 07"
    },
    "CAN 인젝션": {
        "대상": "차량 제어",
        "영향": "조향/브레이크 탈취",
        "방어": "CAN 인증, IDS",
        "주차": "Week 07"
    },
    "OTA 변조": {
        "대상": "펌웨어",
        "영향": "백도어 설치",
        "방어": "코드서명, 롤백방지",
        "주차": "Week 07"
    },
    "LiDAR 스푸핑": {
        "대상": "3D 인지",
        "영향": "고스트 객체 생성",
        "방어": "시간 랜덤화, 퓨전 검증",
        "주차": "Week 07"
    },
}

print("=" * 80)
print("  CPS Attack-Defense Matrix (Week 01-07 Summary)")
print("=" * 80)
for attack, details in matrix.items():
    print(f"\n  [{attack}] ({details['주차']})")
    print(f"    Target:  {details['대상']}")
    print(f"    Impact:  {details['영향']}")
    print(f"    Defense: {details['방어']}")
PYEOF
```

---

## Part 3: 통합 실습 — 드론 침투+방어 시나리오 (1:10-2:00)

### 3.1 드론 보안 종합 실습

```bash
python3 << 'PYEOF'
import socket
import json
import hashlib

print("=" * 65)
print("  MIDTERM LAB: Drone Security Comprehensive Exercise")
print("=" * 65)
print()

# === Phase 1: 정찰 ===
print("[Phase 1] RECONNAISSANCE")
print("  Scanning drone network...")

# 네트워크 자산 식별 시뮬레이션
assets = [
    {"ip": "10.20.30.200", "ports": [9999, 11434], "type": "Drone Controller + LLM"},
    {"ip": "10.20.30.201", "ports": [22], "type": "Attacker Machine"},
    {"ip": "10.20.30.100", "ports": [443, 1514], "type": "SIEM"},
]
for asset in assets:
    print(f"  Found: {asset['ip']} Ports:{asset['ports']} Type:{asset['type']}")
print()

# === Phase 2: 취약점 분석 ===
print("[Phase 2] VULNERABILITY ANALYSIS")
vulns = [
    {"target": "Drone WiFi", "vuln": "No WPA3/PMF", "severity": "HIGH",
     "exploit": "Deauth + Hijack"},
    {"target": "MAVLink", "vuln": "No signing enabled", "severity": "CRITICAL",
     "exploit": "Command injection"},
    {"target": "GPS", "vuln": "L1 C/A only", "severity": "HIGH",
     "exploit": "GPS spoofing"},
    {"target": "Auth Key", "vuln": "Plaintext in UDP", "severity": "CRITICAL",
     "exploit": "Sniff and reuse"},
    {"target": "Telemetry", "vuln": "Unencrypted stream", "severity": "MEDIUM",
     "exploit": "Information disclosure"},
]
for v in vulns:
    print(f"  [{v['severity']:8}] {v['target']}: {v['vuln']}")
    print(f"           Exploit: {v['exploit']}")
print()

# === Phase 3: 공격 시도 ===
print("[Phase 3] EXPLOITATION (Simulated)")
attacks = [
    ("Communication Sniffing", "Captured auth key: DRONE_SECRET_2026"),
    ("Deauth Attack", "Legitimate controller disconnected"),
    ("Session Hijack", "Connected to drone, authenticated"),
    ("Command Injection", "ARM → TAKEOFF(100m) → GOTO(attacker)"),
    ("GPS Spoofing", "Drone reports false position, geofence bypassed"),
]
for attack, result in attacks:
    print(f"  [ATTACK] {attack}")
    print(f"    Result: {result}")
print()

# === Phase 4: 방어 평가 ===
print("[Phase 4] DEFENSE ASSESSMENT")
defenses = [
    ("MAVLink Signing", "MISSING", "Implement v2 signing with shared key"),
    ("Geofencing", "PRESENT (bypassable)", "Add INS cross-validation"),
    ("Drone IDS", "MISSING", "Deploy anomaly detection on commands"),
    ("RF Monitoring", "MISSING", "Add RF spectrum monitoring"),
    ("GPS Anti-Spoofing", "MISSING", "Implement multi-antenna AoA"),
    ("Encrypted Comms", "MISSING", "Enable TLS/DTLS on command channel"),
]
print(f"  {'Defense':<25} {'Status':<22} {'Recommendation'}")
print(f"  {'-'*25} {'-'*22} {'-'*30}")
for defense, status, rec in defenses:
    print(f"  {defense:<25} {status:<22} {rec}")
print()

# 보안 점수
implemented = sum(1 for _, s, _ in defenses if "PRESENT" in s)
total = len(defenses)
score = (implemented / total) * 100
print(f"  Security Score: {score:.0f}% ({implemented}/{total} controls)")
print(f"  Rating: {'POOR' if score < 30 else 'FAIR' if score < 60 else 'GOOD'}")
PYEOF
```

---

## Part 4: 통합 실습 — 자율주행 보안 평가 (2:10-2:50)

### 4.1 자율주행 보안 종합 평가

```bash
python3 << 'PYEOF'
print("=" * 65)
print("  MIDTERM LAB: Autonomous Vehicle Security Assessment")
print("=" * 65)
print()

# 공격 시나리오별 위험도 평가
scenarios = [
    {
        "name": "적대적 패치 → 정지 표지판 오인식",
        "likelihood": 0.6,
        "impact": 0.95,
        "affected": ["인지 시스템", "의사결정"],
        "defense_status": "Partial (ensemble detection)",
        "mitigation": "입력 전처리, 다중 모델 검증, 센서 퓨전"
    },
    {
        "name": "CAN 버스 인젝션 → 조향 탈취",
        "likelihood": 0.4,
        "impact": 1.0,
        "affected": ["제어 시스템", "CAN 네트워크"],
        "defense_status": "Weak (no CAN auth)",
        "mitigation": "CAN 인증(SecOC), IDS, 게이트웨이 분리"
    },
    {
        "name": "GPS 스푸핑 → 경로 변경",
        "likelihood": 0.5,
        "impact": 0.7,
        "affected": ["항법 시스템", "경로 계획"],
        "defense_status": "Moderate (INS fallback)",
        "mitigation": "멀티소스 항법, 스푸핑 탐지, 맵 매칭"
    },
    {
        "name": "OTA 변조 → 악성 펌웨어",
        "likelihood": 0.2,
        "impact": 1.0,
        "affected": ["전체 시스템"],
        "defense_status": "Good (code signing)",
        "mitigation": "Uptane 프레임워크, 롤백 방지, 무결성 검증"
    },
    {
        "name": "LiDAR 스푸핑 → 고스트 장애물",
        "likelihood": 0.3,
        "impact": 0.8,
        "affected": ["인지 시스템", "모션 계획"],
        "defense_status": "Weak",
        "mitigation": "타이밍 랜덤화, 카메라 교차 검증"
    },
]

print("[Risk Assessment Matrix]")
print(f"{'Scenario':<45} {'Risk':>6} {'L×I':>6} {'Defense':<25}")
print("-" * 85)
for s in scenarios:
    risk = s['likelihood'] * s['impact']
    level = "CRIT" if risk > 0.5 else "HIGH" if risk > 0.3 else "MED"
    print(f"{s['name']:<45} {level:>6} {risk:>5.2f} {s['defense_status']:<25}")

print()

# LLM을 활용한 종합 평가
print("[Comprehensive Score]")
total_risk = sum(s['likelihood'] * s['impact'] for s in scenarios) / len(scenarios)
security_posture = (1 - total_risk) * 100
print(f"  Average Risk Score: {total_risk:.2f}")
print(f"  Security Posture: {security_posture:.0f}%")
print(f"  Priority Actions:")

# 위험도 순 정렬
sorted_scenarios = sorted(scenarios, key=lambda s: s['likelihood']*s['impact'], reverse=True)
for i, s in enumerate(sorted_scenarios[:3], 1):
    print(f"    {i}. {s['name']}")
    print(f"       Mitigation: {s['mitigation']}")
PYEOF
```

---

## Part 5: 중간 평가 시험 (3:00-3:30)

### 필기 시험 (50점)

**A. 객관식 (각 2점, 20점)**

1. CPS 보안에서 최우선 가치는?
   - a) 기밀성  b) 무결성  c) 가용성/안전성  d) 부인방지

2. MAVLink v2에서 추가된 보안 기능은?
   - a) TLS  b) 메시지 서명  c) AES 암호화  d) OAuth

3. GPS 삼변측량에 필요한 최소 위성 수는?
   - a) 2개  b) 3개  c) 4개  d) 6개

4. 자율주행 레벨 L4의 특징은?
   - a) 운전자 보조  b) 부분 자동화  c) 특정 영역 완전 자율  d) 완전 자동화

5. CAN 버스의 보안 취약점이 아닌 것은?
   - a) 인증 없음  b) 브로드캐스트  c) 고속 통신  d) 암호화 없음

**B. 서술형 (각 6점, 30점)**

6. SkyJack 드론 하이재킹 공격의 5단계를 설명하시오
7. GPS 스푸핑과 재밍의 차이점, 각각의 방어 방법을 설명하시오
8. 적대적 패치가 자율주행에 미치는 위험과 방어 전략을 서술하시오
9. OTA 업데이트 보안에서 검증해야 할 항목 4가지와 이유를 설명하시오
10. 드론 IDS가 탐지해야 하는 이상 패턴 5가지를 쓰시오

### 실기 시험 (50점)

LLM과 Python을 활용하여 다음을 수행하시오:

1. (15점) 가상 드론에 접속하여 보안 취약점 3개 이상 발견
2. (15점) 발견된 취약점을 활용한 공격 시연 (명령 인젝션 or 하이재킹)
3. (20점) 해당 공격에 대한 방어 메커니즘 구현 (IDS 규칙 또는 인증 로직)

---

## 참고 자료

- Week 01~07 강의 노트 전체
- 실습 YAML 가이드 (week01~week07)
- CPS 보안 공격/방어 매트릭스 (Part 2)
