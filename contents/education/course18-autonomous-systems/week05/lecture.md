# Week 05: GPS 보안 — GPS 스푸핑, 안티스푸핑, 대체 항법

## 학습 목표
- GPS 시스템의 동작 원리와 신호 구조를 이해한다
- GPS 스푸핑 공격의 원리와 기법을 실습할 수 있다
- GPS 재밍과 스푸핑의 차이를 설명할 수 있다
- 안티스푸핑 기술을 분석하고 구현할 수 있다
- 대체 항법 시스템(INS, 시각 항법)의 원리를 이해한다

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
| 0:00-0:30 | 이론: GPS 동작 원리와 신호 구조 (Part 1) | 강의 |
| 0:30-1:00 | 이론: GPS 스푸핑과 재밍 (Part 2) | 강의 |
| 1:00-1:10 | 휴식 | - |
| 1:10-1:50 | 실습: GPS 스푸핑 시뮬레이션 (Part 3) | 실습 |
| 1:50-2:30 | 실습: 안티스푸핑 탐지 구현 (Part 4) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 실습: 대체 항법과 센서 퓨전 (Part 5) | 실습 |
| 3:10-3:30 | 과제 안내 + 정리 | 정리 |

---

## Part 1: GPS 동작 원리와 신호 구조 (0:00-0:30)

### 1.1 GPS 시스템 구조

```
우주 부문 (Space Segment)
┌──────────────────────────────────────────────────┐
│  SV1(PRN)  SV2(PRN)  SV3(PRN)  SV4(PRN) ...    │
│  20,200km  궤도 위성 24+개                        │
│  L1(1575.42MHz), L2(1227.60MHz) 신호 송출        │
└───────────────────┬──────────────────────────────┘
                    │ 전파 (약 67ms)
┌───────────────────▼──────────────────────────────┐
│  제어 부문 (Control Segment)                      │
│  마스터 제어국, 모니터링 스테이션                   │
│  위성 궤도 보정, 시계 보정                         │
└──────────────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────┐
│  사용자 부문 (User Segment)                       │
│  GPS 수신기 → 4개+ 위성 신호 수신 → 삼변측량      │
│  드론, 자동차, 스마트폰 등                         │
└──────────────────────────────────────────────────┘
```

### 1.2 GPS 측위 원리

```
삼변측량 (Trilateration)

      SV1 ●         ● SV2
          \   d1   /
      d1   \     /  d2
            \   /
             \ /
        ──── ● 수신기 위치 ────
             /\
            /  \
      d3  /    \ d4
         /      \
   SV3 ●        ● SV4

d = c × (t_received - t_transmitted)
  = 빛의속도 × 시간차

4개 위성 필요: X, Y, Z 좌표 + 시계 오차 보정
```

### 1.3 GPS 신호 구조

| 구분 | L1 C/A | L1 P(Y) | L2 P(Y) |
|------|--------|---------|---------|
| 주파수 | 1575.42 MHz | 1575.42 MHz | 1227.60 MHz |
| 코드 | C/A (공개) | P(Y) (암호화) | P(Y) (암호화) |
| 대상 | 민간 | 군사 | 군사 |
| 칩율 | 1.023 Mcps | 10.23 Mcps | 10.23 Mcps |
| 스푸핑 | 쉬움 | 매우 어려움 | 매우 어려움 |

---

## Part 2: GPS 스푸핑과 재밍 (0:30-1:00)

### 2.1 GPS 재밍 vs 스푸핑

| 특성 | 재밍 (Jamming) | 스푸핑 (Spoofing) |
|------|---------------|-------------------|
| 목적 | GPS 수신 방해 | 가짜 위치 주입 |
| 방법 | 강한 노이즈 송출 | 위조 GPS 신호 생성 |
| 결과 | 위치 정보 상실 | 잘못된 위치로 유도 |
| 탐지 | 비교적 쉬움 (SNR 급감) | 어려움 (정상으로 보임) |
| 장비 | 저가 재머 가능 | SDR + 소프트웨어 필요 |
| 위험도 | 중 (서비스 거부) | 상 (능동적 기만) |

### 2.2 GPS 스푸핑 공격 유형

```
Type 1: 단순 스푸핑 (Simplistic)
  └─ 정적 위치를 브로드캐스트
  └─ 갑작스런 위치 변경 → 쉽게 탐지

Type 2: 정밀 스푸핑 (Sophisticated)
  └─ 기존 신호 위에 서서히 오프셋 적용
  └─ 점진적 위치 이동 → 탐지 어려움

Type 3: 중계 스푸핑 (Meaconing)
  └─ 다른 위치의 GPS 신호를 캡처하여 재방송
  └─ 리얼타임 릴레이 → 매우 탐지 어려움
```

### 2.3 실제 GPS 스푸핑 사례

| 연도 | 사건 | 설명 |
|------|------|------|
| 2011 | RQ-170 드론 포획 | 이란이 미국 스텔스 드론을 GPS 스푸핑으로 포획(주장) |
| 2013 | UT Austin 시연 | 대학 연구팀이 요트를 GPS 스푸핑으로 항로 변경 |
| 2017 | 흑해 사건 | 20여 척 선박의 GPS가 동시에 오류 (러시아 의심) |
| 2019 | 이란 드론 격추 | GPS/관성항법 기만 전술 활용 |

---

## Part 3: GPS 스푸핑 시뮬레이션 (1:10-1:50)

### 3.1 가상 GPS 수신기와 스푸핑

```bash
python3 << 'PYEOF'
import math
import time
import random
import json

class GPSReceiver:
    """가상 GPS 수신기 시뮬레이터"""

    def __init__(self, true_lat, true_lon, true_alt=100):
        self.true_lat = true_lat
        self.true_lon = true_lon
        self.true_alt = true_alt
        self.reported_lat = true_lat
        self.reported_lon = true_lon
        self.reported_alt = true_alt
        self.satellites = 8
        self.spoofed = False
        self.snr = 45  # 정상 SNR (dB-Hz)

    def get_position(self):
        # 정상 GPS 오차 시뮬레이션 (CEP ~3m)
        noise_lat = random.gauss(0, 0.00003)
        noise_lon = random.gauss(0, 0.00003)
        return {
            "lat": self.reported_lat + noise_lat,
            "lon": self.reported_lon + noise_lon,
            "alt": self.reported_alt + random.gauss(0, 2),
            "satellites": self.satellites,
            "snr": self.snr + random.gauss(0, 2),
            "fix": "3D"
        }

class GPSSpoofingAttack:
    """GPS 스푸핑 공격 시뮬레이터"""

    def __init__(self, target_receiver):
        self.target = target_receiver
        self.spoof_lat = 0
        self.spoof_lon = 0

    def simple_spoof(self, fake_lat, fake_lon):
        """단순 스푸핑: 즉시 위치 변경"""
        self.target.reported_lat = fake_lat
        self.target.reported_lon = fake_lon
        self.target.spoofed = True
        self.target.snr = 52  # 스푸핑 신호가 더 강함

    def gradual_spoof(self, target_lat, target_lon, steps=5):
        """정밀 스푸핑: 점진적 위치 이동"""
        lat_step = (target_lat - self.target.reported_lat) / steps
        lon_step = (target_lon - self.target.reported_lon) / steps

        positions = []
        for i in range(steps):
            self.target.reported_lat += lat_step
            self.target.reported_lon += lon_step
            self.target.spoofed = True
            pos = self.target.get_position()
            positions.append(pos)

        return positions

# 시뮬레이션 실행
print("=" * 60)
print("  GPS SPOOFING SIMULATION")
print("=" * 60)
print()

# 드론 GPS 수신기 (서울 시청 위)
gps = GPSReceiver(37.5665, 126.9780, 100)

# 정상 GPS 데이터
print("[Phase 1] Normal GPS Operation")
for i in range(3):
    pos = gps.get_position()
    print(f"  Fix #{i+1}: Lat={pos['lat']:.6f} Lon={pos['lon']:.6f} "
          f"Alt={pos['alt']:.1f}m Sats={pos['satellites']} SNR={pos['snr']:.1f}")
print()

# 스푸핑 공격 개시
print("[Phase 2] GPS Spoofing Attack - Gradual")
attacker = GPSSpoofingAttack(gps)
target_lat, target_lon = 37.4460, 126.4531  # 인천공항으로 유도

positions = attacker.gradual_spoof(target_lat, target_lon, steps=5)
for i, pos in enumerate(positions):
    dist = math.sqrt((pos['lat'] - 37.5665)**2 + (pos['lon'] - 126.978)**2) * 111000
    print(f"  Spoof Step {i+1}: Lat={pos['lat']:.6f} Lon={pos['lon']:.6f} "
          f"Drift={dist:.0f}m")
print()

print("[Phase 3] Attack Result")
print(f"  True position:    Lat=37.5665 Lon=126.9780 (Seoul City Hall)")
print(f"  Spoofed position: Lat={target_lat:.4f} Lon={target_lon:.4f} (Incheon Airport)")
print(f"  Offset: ~40km west")
print()
print("[!] Drone believes it is over Incheon Airport")
print("[!] Geofencing bypassed - drone thinks it is in allowed zone")
PYEOF
```

---

## Part 4: 안티스푸핑 탐지 구현 (1:50-2:30)

### 4.1 GPS 스푸핑 탐지 알고리즘

```bash
python3 << 'PYEOF'
import math
import random

class GPSSpoofDetector:
    """GPS 스푸핑 탐지 시스템"""

    def __init__(self):
        self.history = []
        self.max_speed = 50  # m/s (드론 최대 속도)
        self.snr_baseline = 45
        self.alerts = []

    def add_reading(self, lat, lon, alt, snr, timestamp):
        reading = {"lat": lat, "lon": lon, "alt": alt, "snr": snr, "ts": timestamp}
        self.history.append(reading)

        if len(self.history) >= 2:
            self._check_speed_anomaly()
            self._check_snr_anomaly()
            self._check_position_jump()
            self._check_altitude_consistency()

    def _check_speed_anomaly(self):
        """속도 이상 탐지: 물리적으로 불가능한 이동"""
        prev = self.history[-2]
        curr = self.history[-1]
        dist = math.sqrt((curr['lat']-prev['lat'])**2 + (curr['lon']-prev['lon'])**2) * 111000
        dt = curr['ts'] - prev['ts']
        if dt > 0:
            speed = dist / dt
            if speed > self.max_speed:
                self.alerts.append(f"SPEED_ANOMALY: {speed:.1f} m/s > max {self.max_speed} m/s")

    def _check_snr_anomaly(self):
        """SNR 이상 탐지: 스푸핑 신호는 비정상적으로 강함"""
        curr = self.history[-1]
        if curr['snr'] > self.snr_baseline + 10:
            self.alerts.append(f"SNR_ANOMALY: {curr['snr']:.1f} dB-Hz (baseline: {self.snr_baseline})")

    def _check_position_jump(self):
        """위치 점프 탐지: 갑작스런 위치 변경"""
        if len(self.history) < 3:
            return
        prev2 = self.history[-3]
        prev1 = self.history[-2]
        curr = self.history[-1]

        d1 = math.sqrt((prev1['lat']-prev2['lat'])**2 + (prev1['lon']-prev2['lon'])**2)
        d2 = math.sqrt((curr['lat']-prev1['lat'])**2 + (curr['lon']-prev1['lon'])**2)
        if d2 > d1 * 10 and d1 > 0:
            self.alerts.append(f"POSITION_JUMP: sudden direction/speed change")

    def _check_altitude_consistency(self):
        """고도 일관성 검사: GPS vs 기압계"""
        curr = self.history[-1]
        baro_alt = curr['alt'] + random.gauss(0, 1)
        diff = abs(curr['alt'] - baro_alt)
        if diff > 20:
            self.alerts.append(f"ALT_MISMATCH: GPS={curr['alt']:.1f} Baro={baro_alt:.1f}")

# 탐지 시뮬레이션
print("=== GPS Spoofing Detection System ===")
print()

detector = GPSSpoofDetector()

# 정상 비행 데이터
print("[Normal Flight Data]")
normal_data = [
    (37.5665, 126.978, 100, 44, 0),
    (37.5666, 126.978, 101, 45, 1),
    (37.5667, 126.978, 100, 43, 2),
    (37.5668, 126.978, 102, 46, 3),
]
for d in normal_data:
    detector.add_reading(*d)
    print(f"  t={d[4]}: Lat={d[0]:.4f} Lon={d[1]:.3f} → Alerts: {len(detector.alerts)}")

print()
print("[Spoofed Flight Data - Attack at t=4]")
spoofed_data = [
    (37.5669, 126.978, 100, 44, 4),   # 정상
    (37.5800, 126.990, 100, 55, 5),   # 갑자기 이동 + SNR 높음
    (37.6000, 127.010, 100, 56, 6),   # 계속 이동
]
for d in spoofed_data:
    prev_alerts = len(detector.alerts)
    detector.add_reading(*d)
    new_alerts = detector.alerts[prev_alerts:]
    status = "SPOOFING DETECTED!" if new_alerts else "OK"
    print(f"  t={d[4]}: Lat={d[0]:.4f} Lon={d[1]:.3f} SNR={d[3]} → {status}")
    for a in new_alerts:
        print(f"    [!] {a}")

print()
print(f"=== Total Alerts: {len(detector.alerts)} ===")
for a in detector.alerts:
    print(f"  - {a}")
PYEOF
```

---

## Part 5: 대체 항법과 센서 퓨전 (2:40-3:10)

### 5.1 GPS 대체 항법 시스템

```
대체 항법 시스템
│
├── 관성 항법 시스템 (INS)
│   ├── 가속도계 + 자이로스코프
│   ├── GPS 없이 상대 위치 추정
│   └── 시간 경과 시 오차 누적 (드리프트)
│
├── 시각 항법 (Visual Navigation)
│   ├── 카메라 기반 위치 추정 (Visual Odometry)
│   ├── SLAM (동시 위치추정 및 지도작성)
│   └── 특징점 매칭으로 이동 추정
│
├── 지자기 항법
│   ├── 지구 자기장 패턴 매칭
│   └── 실내/GPS 불가 환경
│
└── 센서 퓨전 (Kalman Filter)
    ├── GPS + INS + 시각 정보 결합
    ├── 각 센서의 강점 활용
    └── GPS 스푸핑/재밍 시 자동 전환
```

### 5.2 칼만 필터 기반 센서 퓨전 시뮬레이션

```bash
python3 << 'PYEOF'
import math
import random

class SimpleKalmanFusion:
    """간소화된 GPS+INS 센서 퓨전"""

    def __init__(self, init_lat, init_lon):
        self.lat = init_lat
        self.lon = init_lon
        self.gps_weight = 0.7
        self.ins_weight = 0.3
        self.gps_trusted = True

    def update(self, gps_lat, gps_lon, ins_lat, ins_lon, gps_snr):
        # GPS 신뢰도 평가
        if gps_snr > 55 or gps_snr < 20:
            self.gps_trusted = False
            self.gps_weight = 0.1
            self.ins_weight = 0.9
        else:
            self.gps_trusted = True
            self.gps_weight = 0.7
            self.ins_weight = 0.3

        # 가중 평균으로 위치 추정
        self.lat = self.gps_weight * gps_lat + self.ins_weight * ins_lat
        self.lon = self.gps_weight * gps_lon + self.ins_weight * ins_lon

        return {
            "fused_lat": self.lat,
            "fused_lon": self.lon,
            "gps_trusted": self.gps_trusted,
            "gps_weight": self.gps_weight,
        }

# 시뮬레이션
fusion = SimpleKalmanFusion(37.5665, 126.978)

print("=== Sensor Fusion: GPS + INS ===")
print()
print(f"{'Time':>4} {'GPS Lat':>10} {'INS Lat':>10} {'Fused Lat':>10} {'GPS OK':>7} {'Weight':>10}")
print("-" * 60)

# 시나리오: t=3에서 GPS 스푸핑 시작
scenarios = [
    # (gps_lat, gps_lon, ins_lat, ins_lon, snr)
    (37.5666, 126.978, 37.5666, 126.978, 44),  # 정상
    (37.5667, 126.978, 37.5667, 126.978, 45),  # 정상
    (37.5668, 126.978, 37.5668, 126.978, 43),  # 정상
    (37.5900, 126.990, 37.5669, 126.978, 56),  # GPS 스푸핑!
    (37.6100, 127.010, 37.5670, 126.978, 57),  # GPS 스푸핑 계속
    (37.6300, 127.030, 37.5671, 126.978, 58),  # GPS 스푸핑 계속
]

for t, (glat, glon, ilat, ilon, snr) in enumerate(scenarios):
    result = fusion.update(glat, glon, ilat, ilon, snr)
    trusted = "YES" if result['gps_trusted'] else "NO"
    print(f"{t:>4} {glat:>10.4f} {ilat:>10.4f} {result['fused_lat']:>10.4f} "
          f"{trusted:>7} GPS:{result['gps_weight']:.1f}/INS:{1-result['gps_weight']:.1f}")

print()
print("[Result] When GPS spoofing detected (SNR anomaly):")
print("  → System automatically shifts weight to INS")
print("  → Fused position follows INS (true position)")
print("  → GPS spoofing attack mitigated by sensor fusion")
PYEOF
```

---

## Part 6: 과제 안내 (3:10-3:30)

### 과제

**과제:** GPS 스푸핑 탐지 시스템을 개선하시오.
- 다중 안테나 기반 도래각(AoA) 검증 시뮬레이션 추가
- GPS+GLONASS 교차 검증 로직 구현
- 스푸핑 탐지 시 자동 대응 (RTL, INS 전환) 구현

---

## 참고 자료

- GPS.gov: https://www.gps.gov/
- "GPS Spoofing: How It Works" - UT Austin Todd Humphreys
- GNSS 스푸핑 대응 기술 동향 - ETRI
- "All Your GPS Are Belong To Us" - DEF CON presentation

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

