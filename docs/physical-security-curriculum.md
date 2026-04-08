# 물리 보안 교육과정 제안서

> CCC 사이버보안 훈련 플랫폼 — 물리 기자재 연동 교육과정

## 1. 기존 15과목에 물리보안 실습 추가

### course1-attack (사이버 공격)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 5 | 인증 공격 | WiFi 핸드셰이크 캡처+크래킹 | WiFi 어댑터 |
| 9 | 웹셸/백도어 | USB Rubber Ducky 페이로드 작성 | Rubber Ducky |
| 14 | 소셜 엔지니어링 | Flipper Zero RFID 복제 시연 | Flipper Zero |

### course2-security-ops (보안 솔루션 운영)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 3 | 네트워크 보안 | VLAN 구성 + 포트 미러링 | L2/L3 스위치 |
| 7 | IDS/IPS | 포트 미러링 → Suricata 연동 실습 | 관리형 스위치 |
| 12 | 보안 감사 | USB 포트 차단 정책 + 물리 접근 점검 | USB Killer(시연) |

### course7-ai-security (AI/LLM 보안)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 10 | 배포 보안 | 자율주행 AI 적대적 입력 공격 | Donkey Car |
| 13 | 거버넌스 | AI 모델 물리적 보호 (HSM) | Nitrokey HSM2 |

### course8-ai-safety (AI Safety)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 5 | 편향 탐지 | 센서 데이터 변조 → AI 판단 오류 | JetBot |
| 8 | 정렬 | 로봇 안전 매커니즘 우회 시연 | Arduino 로봇 팔 |

### course9-autonomous (자율보안시스템)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 3 | 자율 스캐닝 | 드론 자율 정찰 프로그래밍 | Tello EDU |
| 7 | 팀 조율 | 드론 탐지+방어 시스템 구축 | SDR + WiFi 어댑터 |

### course13-attack-adv (공격 심화)
| 주차 | 기존 주제 | 물리보안 추가 실습 | 기자재 |
|------|----------|------------------|--------|
| 6 | AD 공격 | LAN Turtle 네트워크 침투 | LAN Turtle |
| 10 | 안티포렌식 | O.MG Cable 키로거 시연 | O.MG Cable |
| 14 | 공급망 공격 | 펌웨어 변조 + 백도어 삽입 | Bus Pirate |

---

## 2. 신규 과정 제안

### 과정 A: 물리 침투 테스트 (Physical Penetration Testing)
> 15주 과정 — 물리적 접근으로 IT 시스템을 공격하는 기법

| 주차 | 주제 | 기자재 | 실습 |
|------|------|--------|------|
| 1 | 물리 보안 개론 | - | 물리 보안 위협 분류, 위험 평가 |
| 2 | 사회공학 기초 | - | 프리텍스팅, 테일게이팅 시나리오 |
| 3 | RFID/NFC 해킹 | Proxmark3, Flipper Zero | 출입카드 복제, Mifare 크래킹 |
| 4 | HID 공격 | Rubber Ducky, Bash Bunny | 키스트로크 인젝션 페이로드 작성 |
| 5 | 네트워크 임플란트 | LAN Turtle, Shark Jack | 물리 접근 후 네트워크 백도어 설치 |
| 6 | 무선 해킹 기초 | WiFi 어댑터 | WPA2 크래킹, Evil Twin AP |
| 7 | 무선 해킹 심화 | WiFi Pineapple | MITM, 크레덴셜 캡처 |
| 8 | 중간 평가 | 전체 | 물리 침투 시나리오 실행 |
| 9 | RF 해킹 | HackRF One | Sub-GHz 신호 캡처, 리플레이 공격 |
| 10 | 잠금장치 우회 | Lock Pick Set | 물리적 잠금 해제 기법 |
| 11 | 감시 시스템 해킹 | IP Camera | CCTV 스트림 가로채기, 기본 비밀번호 |
| 12 | 물리적 정보 수집 | - | 덤프스터 다이빙, 숄더 서핑, 사진 촬영 |
| 13 | 물리 침투 보고서 | - | 전문 물리 침투 테스트 보고서 작성 |
| 14 | 방어 대책 | 전체 | 물리 보안 강화 방안 구현 |
| 15 | 종합 평가 | 전체 | 전체 킬체인 물리 침투 시나리오 |

### 과정 B: IoT/임베디드 보안 (IoT & Embedded Security)
> 15주 과정 — IoT 디바이스 해킹과 보안

| 주차 | 주제 | 기자재 | 실습 |
|------|------|--------|------|
| 1 | IoT 보안 개론 | Raspberry Pi | IoT 아키텍처, 공격 표면 |
| 2 | 네트워크 프로토콜 | WiFi 어댑터 | Zigbee, BLE, WiFi 분석 |
| 3 | 하드웨어 인터페이스 | Bus Pirate, Logic Analyzer | UART, SPI, I2C, JTAG |
| 4 | 펌웨어 분석 | Bus Pirate | 덤프, binwalk, 리버싱 |
| 5 | 웹 인터페이스 공격 | Raspberry Pi (서버) | IoT 대시보드 SQLi, XSS |
| 6 | 무선 프로토콜 해킹 | HackRF, RTL-SDR | LoRa, Zigbee 패킷 캡처 |
| 7 | BLE 해킹 | nRF52 동글 | BLE 스니핑, 스푸핑 |
| 8 | 중간 평가 | - | IoT 디바이스 침투 테스트 |
| 9 | IP Camera 해킹 | IP Camera | RTSP, 펌웨어, 기본 비밀번호 |
| 10 | 스마트홈 해킹 | Flipper Zero + RPi | IR, NFC, Sub-GHz 공격 |
| 11 | 허니팟 구축 | Raspberry Pi | Cowrie, Dionaea IoT 허니팟 |
| 12 | OT/SCADA 기초 | OpenPLC + RPi | Modbus 프로토콜, PLC 공격 |
| 13 | 자동차 보안 | CANbus Shield | CAN 버스 스니핑, 인젝션 |
| 14 | IoT 보안 가이드라인 | - | OWASP IoT Top 10, 보안 설계 |
| 15 | 종합 평가 | 전체 | IoT 디바이스 전체 침투+보안 |

### 과정 C: 드론/로봇/자율시스템 보안 (Autonomous Systems Security)
> 15주 과정 — CPS(사이버물리시스템) 보안

| 주차 | 주제 | 기자재 | 실습 |
|------|------|--------|------|
| 1 | CPS 보안 개론 | - | 사이버물리시스템 위협 모델 |
| 2 | 드론 기초 | Tello EDU | 드론 제어, WiFi 구조 분석 |
| 3 | 드론 해킹 | Tello EDU + WiFi 어댑터 | deauth, 명령어 인젝션 |
| 4 | 드론 방어 | SDR + Python | 드론 탐지 시스템 구축 |
| 5 | GPS 보안 | HackRF (시뮬레이션) | GPS 스푸핑 원리, 방어 |
| 6 | 자율주행 기초 | Donkey Car | AI 모델 학습, 자율주행 구현 |
| 7 | 자율주행 공격 | Donkey Car | 적대적 패치, 센서 스푸핑 |
| 8 | 중간 평가 | - | 드론/자율주행 보안 평가 |
| 9 | 로봇 보안 기초 | Arduino 로봇 팔 | 시리얼 통신, 펌웨어 분석 |
| 10 | ROS2 보안 | TurtleBot3 (시뮬레이션) | 토픽 스니핑, 명령 인젝션 |
| 11 | OT/ICS 보안 | OpenPLC | PLC 공격, Modbus 취약점 |
| 12 | V2X/자동차 보안 | CANbus Shield | CAN 프로토콜 공격/방어 |
| 13 | AI 모델 공격/방어 | JetBot | 적대적 입력, 모델 로버스트니스 |
| 14 | CPS 인시던트 대응 | 전체 | 사이버물리 인시던트 시나리오 |
| 15 | 종합 평가 | 전체 | 전체 CPS 침투+방어 시나리오 |

---

## 3. 교육 패키지 구성

### 패키지 1: 기본 물리보안 (~150만원)
```
기존 15과목에 물리 실습 추가
├── Flipper Zero × 2
├── USB Rubber Ducky × 3
├── WiFi 어댑터 × 5
├── Raspberry Pi 5 × 5
├── 관리형 스위치 × 1
└── Proxmark3 × 1
```

### 패키지 2: IoT 전문 과정 (~250만원)
```
과정 B (IoT/임베디드 보안) 운영
├── 패키지 1 전체
├── Bus Pirate × 3
├── Logic Analyzer × 2
├── HackRF One × 1
├── IP Camera × 2
├── OpenPLC (RPi) × 2
└── CANbus Shield × 2
```

### 패키지 3: 자율시스템 전문 과정 (~400만원)
```
과정 C (드론/로봇/자율시스템) 운영
├── 패키지 2 전체
├── Tello EDU × 3
├── Donkey Car × 2
├── Arduino 로봇 팔 × 2
├── JetBot × 1
└── RTL-SDR × 3
```

### 패키지 4: 풀 세트 (~600만원)
```
과정 A+B+C 전체 운영
├── 패키지 3 전체
├── WiFi Pineapple × 1
├── Bash Bunny × 2
├── O.MG Cable × 1
├── LAN Turtle × 2
├── Lock Pick Set × 3
├── Write Blocker × 1
├── YubiKey × 5
└── Nitrokey HSM2 × 1
```

---

## 4. CCC 시스템 연동

### bastion 연동
- 물리 기자재의 결과를 bastion으로 보고
- 예: "드론 WiFi 캡처 결과 분석해줘" → bastion이 pcap 분석
- Raspberry Pi를 SubAgent로 등록 → bastion에서 관리

### 인프라 확장
- Raspberry Pi를 추가 VM처럼 사용
- 물리 기자재 전용 VLAN 구성
- bastion에서 물리 장비 상태 모니터링

### Lab YAML 확장
```yaml
# 물리보안 Lab 예시
lab_id: "physical-week03"
title: "RFID 카드 복제 실습"
version: "non-ai"
requires_hardware:
  - proxmark3
  - flipper_zero
steps:
  - order: 1
    instruction: "Proxmark3로 125kHz RFID 카드를 읽어라"
    hardware: proxmark3
    answer: "proxmark3> lf search"
    verify:
      type: output_contains
      expect: "EM410x"
```
