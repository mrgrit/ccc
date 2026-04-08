# Week 06: 자율주행 기초 — AI 모델, 센서 퓨전, 의사결정

## 학습 목표
- 자율주행 시스템의 계층 구조(인지-판단-제어)를 이해한다
- 자율주행에 사용되는 AI 모델(CNN, YOLO 등)의 역할을 설명할 수 있다
- 센서 퓨전(LiDAR+카메라+레이더)의 원리를 이해한다
- 자율주행 의사결정 시스템의 보안 취약점을 분석할 수 있다
- LLM을 활용하여 자율주행 보안 위협을 평가할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM | `ssh ccc@10.20.30.100` |
| manager | 10.20.30.200 | AI/관리 (Ollama LLM) | `ssh ccc@10.20.30.200` |

**LLM API:** `${LLM_URL:-http://10.20.30.200:11434}`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 이론: 자율주행 시스템 아키텍처 (Part 1) | 강의 |
| 0:30-1:00 | 이론: AI 모델과 센서 퓨전 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 객체 인식 파이프라인 시뮬레이션 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 자율주행 의사결정 시뮬레이션 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 자율주행 보안 위협 분석 (Part 5) | 실습 |
| 3:10-3:30 | 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

## Part 1: 자율주행 시스템 아키텍처 (0:00-0:30)

### 1.1 자율주행 레벨 (SAE J3016)

| 레벨 | 이름 | 설명 | 예시 |
|------|------|------|------|
| L0 | 비자동화 | 운전자가 모든 것을 제어 | 일반 자동차 |
| L1 | 운전자 지원 | 조향 또는 가감속 중 하나 자동 | 크루즈 컨트롤 |
| L2 | 부분 자동화 | 조향+가감속 동시 자동 (운전자 감시) | Tesla Autopilot |
| L3 | 조건부 자동화 | 특정 조건에서 완전 자동 (요청 시 개입) | Honda SENSING Elite |
| L4 | 고도 자동화 | 특정 영역에서 완전 자율 | Waymo 로보택시 |
| L5 | 완전 자동화 | 모든 조건에서 완전 자율 | 아직 없음 |

### 1.2 자율주행 소프트웨어 스택

```
┌─────────────────────────────────────────────────────────┐
│                   자율주행 소프트웨어 스택                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  인지 (Perception)                                │    │
│  │  ├── 카메라 → CNN/YOLO 객체 탐지                  │    │
│  │  ├── LiDAR → 포인트 클라우드 처리                  │    │
│  │  ├── 레이더 → 속도/거리 측정                       │    │
│  │  └── 센서 퓨전 → 통합 환경 모델                    │    │
│  └─────────────────────┬───────────────────────────┘    │
│                        ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  판단 (Planning/Decision)                        │    │
│  │  ├── 경로 계획 (Route Planning)                   │    │
│  │  ├── 행동 계획 (Behavior Planning)                │    │
│  │  ├── 모션 계획 (Motion Planning)                  │    │
│  │  └── 예측 (Prediction) — 다른 차량/보행자         │    │
│  └─────────────────────┬───────────────────────────┘    │
│                        ▼                                │
│  ┌─────────────────────────────────────────────────┐    │
│  │  제어 (Control)                                   │    │
│  │  ├── 조향 제어 (Steering)                         │    │
│  │  ├── 가감속 제어 (Throttle/Brake)                 │    │
│  │  └── CAN 버스 인터페이스                           │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 1.3 자율주행 센서 비교

| 센서 | 장점 | 단점 | 보안 위협 |
|------|------|------|-----------|
| 카메라 | 색상/텍스처 인식, 저비용 | 야간/악천후 약함 | 적대적 패치, 블라인딩 |
| LiDAR | 정밀 3D 맵, 전천후 | 고비용, 반사면 오류 | 레이저 스푸핑 |
| 레이더 | 속도 측정, 전천후 | 해상도 낮음 | RF 재밍 |
| 초음파 | 근거리 정밀 | 짧은 범위 | 음파 간섭 |
| GPS/INS | 절대 위치 | 스푸핑 취약 | GPS 스푸핑/재밍 |

---

## Part 2: AI 모델과 센서 퓨전 (0:30-1:00)

### 2.1 자율주행 AI 모델

```
객체 탐지 (Object Detection)
├── YOLO (You Only Look Once) — 실시간 단일 단계 탐지
├── SSD (Single Shot Detector) — 빠른 다중 스케일 탐지
├── Faster R-CNN — 정밀 이중 단계 탐지
└── Transformer 기반 — DETR, BEVFormer

차선 탐지 (Lane Detection)
├── LaneNet — 인스턴스 세그멘테이션
├── SCNN — 공간 CNN
└── Ultra Fast Lane Detection

깊이 추정 (Depth Estimation)
├── Monocular Depth — 단일 카메라 깊이 추정
└── Stereo Vision — 스테레오 카메라 깊이

의미 분할 (Semantic Segmentation)
├── SegNet
├── DeepLab
└── PSPNet
```

### 2.2 센서 퓨전 구조

```
Early Fusion:     센서 데이터 → [결합] → 단일 AI 모델 → 결과
Mid-level Fusion: 센서 데이터 → 각각 특징 추출 → [특징 결합] → 결과
Late Fusion:      센서 데이터 → 각각 결과 도출 → [결과 결합] → 최종
```

### 2.3 보안 관점에서의 AI 파이프라인

```
입력 공격 표면:
[센서 입력] → [전처리] → [AI 추론] → [후처리] → [의사결정]
     ▲            ▲           ▲           ▲           ▲
     │            │           │           │           │
  센서 스푸핑   데이터 주입  모델 공격  결과 변조  명령 탈취
  적대적 패치   노이즈 주입  적대적 샘플  NMS 교란  CAN 인젝션
```

---

## Part 3: 객체 인식 파이프라인 시뮬레이션 (1:10-1:50)

### 3.1 가상 객체 인식 시뮬레이션

```bash
python3 << 'PYEOF'
import random
import json

class VirtualObjectDetector:
    """가상 자율주행 객체 인식 시스템"""

    def __init__(self):
        self.classes = {
            0: "car", 1: "truck", 2: "pedestrian", 3: "bicycle",
            4: "traffic_sign", 5: "traffic_light", 6: "stop_sign"
        }

    def detect(self, scene_objects, adversarial=False):
        """객체 탐지 시뮬레이션"""
        results = []
        for obj in scene_objects:
            confidence = random.uniform(0.75, 0.99)
            detected_class = obj["class"]

            if adversarial and obj.get("has_adversarial_patch"):
                # 적대적 패치가 있으면 오분류
                confidence = random.uniform(0.60, 0.85)
                wrong_classes = [c for c in self.classes.values() if c != obj["class"]]
                detected_class = random.choice(wrong_classes)

            results.append({
                "true_class": obj["class"],
                "detected_class": detected_class,
                "confidence": round(confidence, 3),
                "bbox": obj["bbox"],
                "correct": detected_class == obj["class"]
            })
        return results

# 시뮬레이션 장면
scene = [
    {"class": "car", "bbox": [100, 200, 250, 350], "has_adversarial_patch": False},
    {"class": "pedestrian", "bbox": [400, 180, 450, 380], "has_adversarial_patch": False},
    {"class": "stop_sign", "bbox": [600, 100, 650, 160], "has_adversarial_patch": True},
    {"class": "traffic_light", "bbox": [300, 50, 340, 120], "has_adversarial_patch": False},
    {"class": "bicycle", "bbox": [500, 250, 570, 400], "has_adversarial_patch": True},
]

detector = VirtualObjectDetector()

# 정상 탐지
print("=== Normal Detection (No Attack) ===")
results = detector.detect(scene, adversarial=False)
for r in results:
    status = "OK" if r["correct"] else "MISCLASSIFIED"
    print(f"  [{status}] True: {r['true_class']:15} Detected: {r['detected_class']:15} Conf: {r['confidence']}")

print()

# 적대적 공격 하에서 탐지
print("=== Detection Under Adversarial Attack ===")
results = detector.detect(scene, adversarial=True)
for r in results:
    status = "OK" if r["correct"] else "ATTACK!"
    print(f"  [{status:7}] True: {r['true_class']:15} Detected: {r['detected_class']:15} Conf: {r['confidence']}")

misclassified = [r for r in results if not r["correct"]]
print(f"\n  [!] {len(misclassified)} objects misclassified due to adversarial patches")
if any(r['true_class'] == 'stop_sign' for r in misclassified):
    print("  [CRITICAL] Stop sign misclassified — vehicle may not stop!")
PYEOF
```

---

## Part 4: 자율주행 의사결정 시뮬레이션 (1:50-2:30)

### 4.1 행동 계획 시뮬레이터

```bash
python3 << 'PYEOF'
import json

class AutonomousDrivingPlanner:
    """자율주행 의사결정 시뮬레이터"""

    def __init__(self):
        self.speed = 60  # km/h
        self.max_speed = 100

    def plan_action(self, detections, road_state):
        """인지 결과를 기반으로 행동 결정"""
        actions = []

        for det in detections:
            obj = det["detected_class"]
            conf = det["confidence"]
            dist = det.get("distance", 50)

            if obj == "stop_sign" and dist < 30:
                actions.append({"action": "STOP", "reason": f"Stop sign at {dist}m", "priority": 1})
            elif obj == "pedestrian" and dist < 20:
                actions.append({"action": "EMERGENCY_BRAKE", "reason": f"Pedestrian at {dist}m", "priority": 0})
            elif obj == "traffic_light" and det.get("color") == "red":
                actions.append({"action": "STOP", "reason": "Red light", "priority": 1})
            elif obj == "car" and dist < 15:
                actions.append({"action": "BRAKE", "reason": f"Vehicle ahead at {dist}m", "priority": 2})
            elif obj == "bicycle" and dist < 10:
                actions.append({"action": "SLOW_DOWN", "reason": f"Bicycle at {dist}m", "priority": 3})

        if road_state.get("speed_limit"):
            if self.speed > road_state["speed_limit"]:
                actions.append({"action": "SLOW_DOWN", "reason": f"Speed limit {road_state['speed_limit']}km/h", "priority": 4})

        if not actions:
            actions.append({"action": "MAINTAIN_SPEED", "reason": "Clear road", "priority": 10})

        actions.sort(key=lambda x: x["priority"])
        return actions[0]

planner = AutonomousDrivingPlanner()

# 시나리오 1: 정상 인식
print("=== Scenario 1: Normal Detection ===")
normal_detections = [
    {"detected_class": "stop_sign", "confidence": 0.95, "distance": 25},
    {"detected_class": "car", "confidence": 0.92, "distance": 40},
]
action = planner.plan_action(normal_detections, {"speed_limit": 60})
print(f"  Decision: {action['action']} — {action['reason']}")
print(f"  [OK] Vehicle correctly stops at stop sign")
print()

# 시나리오 2: 적대적 공격으로 오분류
print("=== Scenario 2: Adversarial Attack on Stop Sign ===")
attacked_detections = [
    {"detected_class": "speed_limit_45", "confidence": 0.78, "distance": 25},
    {"detected_class": "car", "confidence": 0.92, "distance": 40},
]
action = planner.plan_action(attacked_detections, {"speed_limit": 60})
print(f"  Decision: {action['action']} — {action['reason']}")
print(f"  [DANGER] Stop sign misclassified as speed limit sign!")
print(f"  [DANGER] Vehicle does NOT stop at intersection!")
print()

# 시나리오 3: 센서 스푸핑
print("=== Scenario 3: LiDAR Spoofing - Ghost Object ===")
spoofed_detections = [
    {"detected_class": "pedestrian", "confidence": 0.82, "distance": 5},
]
action = planner.plan_action(spoofed_detections, {"speed_limit": 60})
print(f"  Decision: {action['action']} — {action['reason']}")
print(f"  [ATTACK] Fake pedestrian causes emergency brake on highway!")
print(f"  [DANGER] Could cause rear-end collision")
PYEOF
```

---

## Part 5: 자율주행 보안 위협 분석 (2:40-3:10)

### 5.1 LLM 활용 위협 분석

```bash
curl -s ${LLM_URL:-http://10.20.30.200:11434}/api/chat \
  -d '{
    "model":"gemma3:4b",
    "messages":[
      {"role":"system","content":"You are an autonomous vehicle security expert."},
      {"role":"user","content":"List the top 5 attack vectors against autonomous vehicles perception systems. For each, describe the attack method, impact, and defense."}
    ],
    "stream":false,
    "options":{"num_predict":300}
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['message']['content'])"
```

### 5.2 공격 표면 매핑

```bash
python3 << 'PYEOF'
attack_surface = {
    "Perception": {
        "Camera": ["Adversarial patches", "Blinding (laser/IR)", "Projector attack"],
        "LiDAR": ["Laser spoofing", "Relay attack", "Saturation"],
        "Radar": ["RF jamming", "Ghost target injection"],
        "GPS": ["Spoofing", "Jamming"],
    },
    "Communication": {
        "V2X": ["Message forgery", "Replay attack", "DoS"],
        "Cellular": ["Man-in-the-middle", "Fake base station"],
        "WiFi": ["Deauth", "Evil twin"],
        "CAN bus": ["Message injection", "Bus-off attack"],
    },
    "Software": {
        "OTA Update": ["Firmware manipulation", "Rollback attack"],
        "AI Model": ["Model poisoning", "Evasion attack"],
        "OS/Middleware": ["Privilege escalation", "Buffer overflow"],
    },
}

print("=" * 70)
print("  AUTONOMOUS VEHICLE ATTACK SURFACE MAP")
print("=" * 70)
total = 0
for category, targets in attack_surface.items():
    print(f"\n[{category}]")
    for target, attacks in targets.items():
        print(f"  {target}:")
        for a in attacks:
            print(f"    - {a}")
            total += 1
print(f"\n{'='*70}")
print(f"Total attack vectors identified: {total}")
PYEOF
```

---

## Part 6: 퀴즈 + 과제 안내 (3:10-3:30)

### 퀴즈 (10문항)

1. 자율주행 레벨 L2와 L4의 차이점은?
2. 자율주행 인지-판단-제어 파이프라인을 설명하시오
3. YOLO 모델의 동작 원리를 간단히 설명하시오
4. 센서 퓨전의 세 가지 방식(Early/Mid/Late)의 차이는?
5. 적대적 패치가 정지 표지판 인식에 미치는 영향은?
6. LiDAR 스푸핑 공격의 원리는?
7. 자율주행에서 CAN 버스의 역할은?
8. OTA 업데이트의 보안 위험은?
9. V2X 통신이 필요한 이유와 보안 위험은?
10. 카메라 블라인딩 공격의 방어 방법은?

### 과제

**과제:** 자율주행 시나리오 3개를 설계하고, 각 시나리오에서 적대적 공격의 영향을 분석하시오.
- 고속도로 합류, 교차로 진입, 보행자 횡단 시나리오
- 각 시나리오에서 가능한 공격과 결과 분석

---

## 참고 자료

- SAE J3016: Taxonomy of Driving Automation
- "Adversarial Examples in the Physical World" - Kurakin et al.
- Tesla Autopilot Security Research - Tencent Keen Lab
- "Robust Physical-World Attacks on Deep Learning Models" - Eykholt et al.
