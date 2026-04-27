# Week 07: 자율주행 공격 — 적대적 패치, 센서 스푸핑, OTA 변조

## 학습 목표
- 적대적 패치(Adversarial Patch) 공격의 원리와 생성 기법을 이해한다
- 센서 스푸핑(LiDAR, 카메라, 레이더) 공격을 시뮬레이션할 수 있다
- OTA(Over-The-Air) 업데이트 변조 공격의 위험성을 분석할 수 있다
- CAN 버스 메시지 인젝션 공격을 실습할 수 있다
- 각 공격에 대한 방어 전략을 설계할 수 있다

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
| 0:00-0:30 | 이론: 적대적 패치 공격 원리 (Part 1) | 강의 |
| 0:30-1:00 | 이론: 센서 스푸핑과 OTA 변조 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: 적대적 입력 생성 시뮬레이션 (Part 3) | 실습 |
| 1:50-2:30 | 실습: CAN 버스 공격 시뮬레이션 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: OTA 업데이트 공격과 방어 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: 적대적 패치 공격 원리 (0:00-0:30)

### 1.1 적대적 공격의 분류

```
적대적 공격 (Adversarial Attacks)
│
├── 디지털 공격 (Digital)
│   ├── FGSM (Fast Gradient Sign Method)
│   ├── PGD (Projected Gradient Descent)
│   ├── C&W (Carlini & Wagner)
│   └── DeepFool
│
├── 물리적 공격 (Physical)
│   ├── 적대적 패치 (Adversarial Patch)
│   ├── 적대적 스티커
│   ├── 적대적 티셔츠
│   └── 도로 표면 변조
│
└── 범용 공격 (Universal)
    ├── 모든 입력에 적용 가능한 섭동
    └── 클래스 특화 범용 섭동
```

### 1.2 적대적 패치 공격 원리

```
정상 이미지                      적대적 패치 적용
┌──────────────┐                ┌──────────────┐
│              │                │   ┌─────┐    │
│   STOP       │                │   │PATCH│    │
│   ████       │   패치 부착    │   └─────┘    │
│   ████       │  ──────────▶  │   STOP       │
│              │                │   ████       │
└──────────────┘                └──────────────┘
  AI 인식: STOP SIGN              AI 인식: SPEED LIMIT 45
  신뢰도: 0.97                    신뢰도: 0.82

패치 생성 과정:
1. 목표 오분류 클래스 설정
2. 패치 영역 초기화 (랜덤 노이즈)
3. 손실 함수 최적화 (목표 클래스로 분류되도록)
4. 반복적 그래디언트 업데이트
5. 물리 환경 변환(조명, 각도) 적용
6. 인쇄 가능한 패치 생성
```

### 1.3 실제 연구 사례

| 연구 | 공격 대상 | 결과 |
|------|-----------|------|
| Eykholt et al. (2018) | 정지 표지판 | 스티커로 정지 표지판을 속도제한으로 오인 |
| Tencent Keen Lab (2020) | Tesla Autopilot | 도로 스티커로 차선 변경 유도 |
| Cao et al. (2019) | LiDAR | 레이저로 가짜 장애물 생성 |
| Nassi et al. (2020) | 드론 카메라 | 프로젝터로 가짜 이미지 투사 |

---

## Part 2: 센서 스푸핑과 OTA 변조 (0:30-1:00)

### 2.1 LiDAR 스푸핑

```
정상 LiDAR 동작:
LiDAR ── 레이저 펄스 ──▶ 물체 반사 ──▶ 수신기

스푸핑 공격:
공격자 디바이스 ── 동기화된 레이저 펄스 ──▶ LiDAR 수신기
                 (가짜 반사 신호)

결과: 포인트 클라우드에 존재하지 않는 물체 생성
     또는 실제 물체를 삭제
```

### 2.2 OTA 업데이트 공격 체인

```
정상 OTA:
제조사 서버 ─[서명된 펌웨어]─▶ 차량 ─[검증]─▶ 설치

공격 시나리오:
1. MitM: 업데이트 채널 가로채기 → 변조된 펌웨어 주입
2. 서버 해킹: 제조사 OTA 서버 침해 → 악성 업데이트 배포
3. 롤백: 구버전(취약한) 펌웨어로 다운그레이드 유도
4. 서명 우회: 코드 서명 검증 로직 취약점 악용
```

### 2.3 CAN 버스 공격

```
CAN 버스 구조:
ECU1 ── ECU2 ── ECU3 ── ECU4
   └──────┴──────┴──────┘
         CAN 버스 (공유)

취약점:
- 인증 없음: 누구나 메시지 전송 가능
- 암호화 없음: 모든 ECU가 모든 메시지를 볼 수 있음
- 우선순위 기반: 낮은 ID가 높은 우선순위

공격 유형:
1. 메시지 인젝션: 조향/브레이크 명령 위조
2. 메시지 퍼징: 랜덤 CAN 프레임 대량 전송
3. Bus-off 공격: 특정 ECU를 에러 상태로 유도
4. 리플레이: 캡처한 메시지 재전송
```

---

## Part 3: 적대적 입력 생성 시뮬레이션 (1:10-1:50)

### 3.1 FGSM 공격 시뮬레이션

```bash
python3 << 'PYEOF'
import random
import math

class AdversarialSimulator:
    """적대적 공격 시뮬레이션 (수치 기반)"""

    def __init__(self):
        # 간소화된 분류기: 특징 벡터 → 클래스
        self.classes = ["stop_sign", "speed_limit", "yield", "no_entry", "pedestrian_crossing"]

    def classify(self, features):
        """간소화된 분류 (특징 벡터의 가중합)"""
        scores = {}
        # 각 클래스별 가중치 (시뮬레이션)
        weights = {
            "stop_sign": [0.9, -0.3, 0.5, -0.2, 0.1],
            "speed_limit": [-0.2, 0.8, -0.1, 0.6, -0.3],
            "yield": [0.1, -0.1, 0.7, 0.2, 0.5],
            "no_entry": [0.3, 0.4, -0.2, -0.5, 0.8],
            "pedestrian_crossing": [-0.4, 0.2, 0.3, 0.7, -0.1],
        }
        for cls, w in weights.items():
            score = sum(f * wi for f, wi in zip(features, w))
            scores[cls] = 1 / (1 + math.exp(-score))  # sigmoid

        total = sum(scores.values())
        probs = {k: v/total for k, v in scores.items()}
        best = max(probs, key=probs.get)
        return best, probs[best], probs

    def fgsm_attack(self, features, target_class, epsilon=0.3):
        """FGSM 스타일 적대적 섭동"""
        # 그래디언트 방향 시뮬레이션
        weights = {
            "stop_sign": [0.9, -0.3, 0.5, -0.2, 0.1],
            "speed_limit": [-0.2, 0.8, -0.1, 0.6, -0.3],
        }
        target_w = weights.get(target_class, [0.5]*5)

        # 목표 클래스 방향으로 섭동
        perturbation = [epsilon * (1 if w > 0 else -1) for w in target_w]
        adv_features = [f + p for f, p in zip(features, perturbation)]
        return adv_features, perturbation

sim = AdversarialSimulator()

# 정상 정지 표지판 특징
original_features = [0.8, -0.2, 0.4, -0.1, 0.1]

print("=== Adversarial Attack Simulation (FGSM-style) ===")
print()

# 정상 분류
cls, conf, probs = sim.classify(original_features)
print(f"[Original] Classified as: {cls} (conf: {conf:.3f})")
print(f"  All probabilities:")
for c, p in sorted(probs.items(), key=lambda x: -x[1]):
    bar = "#" * int(p * 50)
    print(f"    {c:25} {p:.3f} {bar}")
print()

# 적대적 공격: 정지 표지판 → 속도제한 표지판
for eps in [0.1, 0.2, 0.3, 0.5]:
    adv_features, perturbation = sim.fgsm_attack(original_features, "speed_limit", eps)
    cls, conf, probs = sim.classify(adv_features)
    success = "SUCCESS" if cls == "speed_limit" else "FAILED"
    print(f"[FGSM eps={eps}] → {cls} (conf: {conf:.3f}) [{success}]")
    print(f"  Perturbation: {[f'{p:+.2f}' for p in perturbation]}")

print()
print("[!] With epsilon=0.3+, stop sign is misclassified as speed_limit")
print("[!] In physical world: adversarial sticker on stop sign")
PYEOF
```

---

## Part 4: CAN 버스 공격 시뮬레이션 (1:50-2:30)

### 4.1 python-can 가상 CAN 버스

```bash
# python-can 설치 확인 및 가상 CAN 버스 시뮬레이션
python3 << 'PYEOF'
import struct
import time

class VirtualCANBus:
    """가상 CAN 버스 시뮬레이터"""

    def __init__(self):
        self.messages = []
        self.ecus = {
            "engine_ecu": {"id": 0x100, "desc": "엔진 제어"},
            "brake_ecu":  {"id": 0x200, "desc": "브레이크 제어"},
            "steer_ecu":  {"id": 0x300, "desc": "조향 제어"},
            "airbag_ecu": {"id": 0x400, "desc": "에어백 제어"},
            "adas_ecu":   {"id": 0x500, "desc": "ADAS 제어"},
        }

    def send(self, arb_id, data, source="unknown"):
        msg = {
            "timestamp": len(self.messages) * 0.01,
            "arb_id": arb_id,
            "data": data,
            "dlc": len(data),
            "source": source
        }
        self.messages.append(msg)
        return msg

    def sniff(self, count=None):
        msgs = self.messages[-count:] if count else self.messages
        return msgs

class CANAttacker:
    """CAN 버스 공격 시뮬레이터"""

    def __init__(self, bus):
        self.bus = bus

    def inject_brake(self, enable=True):
        """브레이크 명령 인젝션"""
        data = bytes([0x01 if enable else 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        return self.bus.send(0x200, data, "attacker")

    def inject_steering(self, angle):
        """조향 명령 인젝션"""
        angle_bytes = struct.pack('>h', angle)
        data = angle_bytes + bytes(6)
        return self.bus.send(0x300, data, "attacker")

    def dos_attack(self, count=10):
        """CAN 버스 DoS (높은 우선순위 프레임 대량 전송)"""
        results = []
        for i in range(count):
            data = bytes([0xFF] * 8)
            results.append(self.bus.send(0x001, data, "attacker"))
        return results

    def replay_attack(self, captured_msgs):
        """리플레이 공격: 캡처된 메시지 재전송"""
        results = []
        for msg in captured_msgs:
            results.append(self.bus.send(msg['arb_id'], msg['data'], "attacker(replay)"))
        return results

# 시뮬레이션 실행
bus = VirtualCANBus()
attacker = CANAttacker(bus)

print("=== CAN Bus Attack Simulation ===")
print()

# 정상 트래픽 생성
print("[Phase 1] Normal CAN Traffic")
bus.send(0x100, bytes([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), "engine_ecu")
bus.send(0x200, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), "brake_ecu")
bus.send(0x300, bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]), "steer_ecu")
bus.send(0x500, bytes([0x01, 0x00, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00]), "adas_ecu")

for msg in bus.sniff(4):
    print(f"  ID:0x{msg['arb_id']:03X} Data:{msg['data'].hex()} Src:{msg['source']}")
print()

# 공격 1: 브레이크 인젝션
print("[Phase 2] Attack: Brake Injection")
msg = attacker.inject_brake(True)
print(f"  [INJECTED] ID:0x{msg['arb_id']:03X} Data:{msg['data'].hex()}")
print(f"  [!] Fake brake command sent — vehicle may brake unexpectedly!")
print()

# 공격 2: 조향 인젝션
print("[Phase 3] Attack: Steering Injection")
msg = attacker.inject_steering(450)  # 45도 우회전
print(f"  [INJECTED] ID:0x{msg['arb_id']:03X} Data:{msg['data'].hex()}")
print(f"  [!] Fake steering command — vehicle turns right 45 degrees!")
print()

# 공격 3: DoS
print("[Phase 4] Attack: CAN Bus DoS")
results = attacker.dos_attack(5)
print(f"  [DOS] Sent {len(results)} high-priority frames (ID:0x001)")
print(f"  [!] Legitimate ECU messages blocked by arbitration!")
print()

# 통계
print("=== Attack Summary ===")
total = len(bus.messages)
attack_msgs = [m for m in bus.messages if 'attacker' in m['source']]
print(f"  Total messages: {total}")
print(f"  Attack messages: {len(attack_msgs)} ({len(attack_msgs)/total*100:.0f}%)")
print(f"  Attack types: Injection, DoS, Replay")
PYEOF
```

---

## Part 5: OTA 업데이트 공격과 방어 (2:40-3:10)

### 5.1 OTA 업데이트 보안 검증

```bash
python3 << 'PYEOF'
import hashlib
import json
import hmac

class OTAUpdateSystem:
    """OTA 업데이트 시스템 (보안 검증 포함)"""

    def __init__(self):
        self.signing_key = b"manufacturer_secret_key_2026"
        self.current_version = "2.1.0"
        self.min_version = "2.0.0"

    def create_update(self, version, firmware_data, legitimate=True):
        """펌웨어 업데이트 패키지 생성"""
        firmware_hash = hashlib.sha256(firmware_data.encode()).hexdigest()

        if legitimate:
            signature = hmac.new(self.signing_key, firmware_data.encode(), hashlib.sha256).hexdigest()
        else:
            signature = hmac.new(b"fake_key", firmware_data.encode(), hashlib.sha256).hexdigest()

        return {
            "version": version,
            "firmware_hash": firmware_hash,
            "signature": signature,
            "size": len(firmware_data),
            "data": firmware_data
        }

    def verify_update(self, package):
        """업데이트 패키지 보안 검증"""
        results = {"checks": [], "passed": True}

        # 1. 서명 검증
        expected_sig = hmac.new(self.signing_key, package['data'].encode(), hashlib.sha256).hexdigest()
        sig_valid = package['signature'] == expected_sig
        results["checks"].append(("Signature Verification", sig_valid))
        if not sig_valid:
            results["passed"] = False

        # 2. 해시 검증
        computed_hash = hashlib.sha256(package['data'].encode()).hexdigest()
        hash_valid = computed_hash == package['firmware_hash']
        results["checks"].append(("Hash Integrity", hash_valid))
        if not hash_valid:
            results["passed"] = False

        # 3. 버전 검증 (롤백 방지)
        version_valid = package['version'] > self.current_version
        results["checks"].append(("Version Check (anti-rollback)", version_valid))
        if not version_valid:
            results["passed"] = False

        # 4. 최소 버전 검증
        min_valid = package['version'] >= self.min_version
        results["checks"].append(("Minimum Version", min_valid))

        return results

ota = OTAUpdateSystem()

print("=== OTA Update Security Verification ===")
print()

# 테스트 1: 정상 업데이트
print("[Test 1] Legitimate Update v2.2.0")
pkg1 = ota.create_update("2.2.0", "legitimate_firmware_binary_v220", legitimate=True)
result = ota.verify_update(pkg1)
for check, passed in result["checks"]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}")
print(f"  Result: {'INSTALL' if result['passed'] else 'REJECT'}")
print()

# 테스트 2: 변조된 업데이트 (잘못된 서명)
print("[Test 2] Tampered Update (fake signature)")
pkg2 = ota.create_update("2.3.0", "malicious_firmware_with_backdoor", legitimate=False)
result = ota.verify_update(pkg2)
for check, passed in result["checks"]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}")
print(f"  Result: {'INSTALL' if result['passed'] else 'REJECT'}")
print()

# 테스트 3: 롤백 공격
print("[Test 3] Rollback Attack (v1.9.0)")
pkg3 = ota.create_update("1.9.0", "old_vulnerable_firmware", legitimate=True)
result = ota.verify_update(pkg3)
for check, passed in result["checks"]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}")
print(f"  Result: {'INSTALL' if result['passed'] else 'REJECT'}")
print()

# 테스트 4: 해시 변조
print("[Test 4] Hash Manipulation")
pkg4 = ota.create_update("2.4.0", "normal_firmware", legitimate=True)
pkg4['firmware_hash'] = "0" * 64  # 해시 변조
result = ota.verify_update(pkg4)
for check, passed in result["checks"]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {check}")
print(f"  Result: {'INSTALL' if result['passed'] else 'REJECT'}")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** CAN 버스 IDS를 구현하시오.
- 정상 트래픽 패턴 학습 (메시지 주기, ID 빈도)
- 인젝션 공격 탐지 (비정상 ID, 비정상 주기)
- DoS 공격 탐지 (메시지 빈도 이상)
- 탐지 시 경고 발생 및 로그 기록

---

## 참고 자료

- "Robust Physical-World Attacks on Deep Learning Models" - Eykholt et al.
- "Illusion and Dazzle: Adversarial Optical Channel Exploits Against LiDAR"
- "Experimental Security Analysis of a Modern Automobile" - Koscher et al.
- "Uptane: Securing Software Updates for Automobiles"

---

## 실제 사례 (WitFoo Precinct 6 — Smart Grid)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *Smart Grid* 학습 항목 매칭.

### Smart Grid 의 dataset 흔적 — "SCADA + IEC 61850"

dataset 의 정상 운영에서 *SCADA + IEC 61850* 신호의 baseline 을 알아두면, *Smart Grid* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — 전력망 보안.

```mermaid
graph LR
    SCENE["Smart Grid 시나리오"]
    TRACE["dataset 흔적<br/>SCADA + IEC 61850"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | SCADA + IEC 61850 |
| 정량 baseline | 전력망 보안 |
| 학습 매핑 | grid cyber |

**자세한 해석**: grid cyber. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | SCADA + IEC 61850 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **Smart Grid = SCADA + IEC 61850 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — 전력망 보안.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: grid sim.

