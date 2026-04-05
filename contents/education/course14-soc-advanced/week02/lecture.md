# Week 02: SIEM 고급 상관분석

## 학습 목표
- Wazuh 상관 룰(correlation rule)의 구조와 작성법을 이해한다
- 다중 소스(방화벽, IPS, 웹서버, OS) 이벤트를 연계한 복합 탐지를 구현할 수 있다
- frequency, same_source_ip, if_matched_sid 등 고급 룰 요소를 활용할 수 있다
- 임계치(threshold) 기반 탐지와 시간 윈도우 설정을 수행할 수 있다
- 오탐을 줄이기 위한 룰 튜닝 기법을 적용할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | 상관분석 이론 + Wazuh 룰 구조 (Part 1) | 강의 |
| 0:50-1:30 | 고급 룰 요소 + 다중 소스 연계 (Part 2) | 강의/토론 |
| 1:30-1:40 | 휴식 | - |
| 1:40-2:30 | 상관 룰 작성 실습 (Part 3) | 실습 |
| 2:30-3:10 | 룰 튜닝 + OpsClaw 자동화 (Part 4) | 실습 |
| 3:10-3:20 | 복습 퀴즈 + 과제 안내 | 정리 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **상관분석** | Correlation Analysis | 다수 이벤트를 연계하여 패턴을 찾는 분석 기법 | 여러 CCTV 영상을 교차 확인 |
| **frequency** | Frequency | 특정 시간 내 이벤트 발생 횟수 기반 탐지 | "10분에 5번 이상 출입 시도" |
| **if_matched_sid** | Conditional Match | 선행 룰이 매칭된 후에만 동작하는 조건 | "화재 경보 후 스프링클러 작동" |
| **same_source_ip** | Same Source IP | 동일 출발지 IP로부터의 이벤트 그룹핑 | 같은 차량 번호판 추적 |
| **timeframe** | Time Frame | 이벤트 상관분석 시간 윈도우 | "5분 이내에 발생한 일" |
| **composite rule** | Composite Rule | 여러 조건을 결합한 복합 룰 | 여러 단서를 종합한 프로파일링 |
| **임계치** | Threshold | 경보를 발생시키는 기준값 | 온도계의 경고 눈금 |
| **enrichment** | Enrichment | 경보에 추가 컨텍스트를 덧붙이는 것 | 수배서에 전과 기록 추가 |
| **decoder** | Decoder | 로그를 파싱하여 필드를 추출하는 구성 요소 | 외국어 통역사 |

---

# Part 1: 상관분석 이론 + Wazuh 룰 구조 (50분)

## 1.1 상관분석이란?

상관분석(Correlation Analysis)은 **개별 이벤트로는 의미 없지만, 여러 이벤트를 연계하면 위협을 탐지**할 수 있는 고급 분석 기법이다.

### 단일 이벤트 vs 상관분석

```
[단일 이벤트 탐지]
  SSH 로그인 실패 1건 → 의미 없음 (오타 가능)
  방화벽 차단 1건 → 의미 없음 (일상적)
  웹 404 에러 1건 → 의미 없음 (링크 깨짐)

[상관분석 탐지]
  같은 IP에서 5분 내:
    SSH 로그인 실패 10건 + 방화벽 차단 5건 + 포트스캔 탐지
    → "무차별 대입 공격 + 네트워크 정찰" → Critical Alert!
```

### 상관분석의 유형

```
+--[시간 기반]--+   +--[소스 기반]--+   +--[패턴 기반]--+
| - frequency    |   | - same_source  |   | - sequence     |
| - timeframe    |   | - same_dest    |   | - chain        |
| - 슬라이딩윈도 |   | - cross-source |   | - state machine|
+----------------+   +----------------+   +----------------+

+--[통계 기반]--+   +--[행위 기반]--+
| - threshold    |   | - baseline     |
| - anomaly      |   | - deviation    |
| - percentile   |   | - profile      |
+----------------+   +----------------+
```

## 1.2 Wazuh 룰 구조 기초

### 기본 룰 구조

```xml
<!-- /var/ossec/etc/rules/local_rules.xml -->
<group name="custom_correlation,">

  <!-- 기본 룰: 단일 이벤트 매칭 -->
  <rule id="100001" level="5">
    <decoded_as>sshd</decoded_as>
    <match>Failed password</match>
    <description>SSH 로그인 실패</description>
    <group>authentication_failed,</group>
  </rule>

</group>
```

### 핵심 XML 요소

| 요소 | 설명 | 예시 |
|------|------|------|
| `<rule id>` | 룰 고유 번호 (100000-109999 커스텀) | `id="100001"` |
| `<level>` | 경보 심각도 (0-15) | `level="10"` |
| `<decoded_as>` | 디코더 매칭 | `<decoded_as>sshd</decoded_as>` |
| `<match>` | 로그 문자열 매칭 | `<match>Failed password</match>` |
| `<regex>` | 정규표현식 매칭 | `<regex>error \d+</regex>` |
| `<srcip>` | 출발지 IP 매칭 | `<srcip>10.20.30.0/24</srcip>` |
| `<dstip>` | 목적지 IP 매칭 | `<dstip>10.20.30.80</dstip>` |
| `<if_sid>` | 선행 룰 ID 기반 매칭 | `<if_sid>100001</if_sid>` |
| `<frequency>` | 반복 횟수 기반 매칭 | `<frequency>5</frequency>` |
| `<timeframe>` | 시간 윈도우 (초) | `<timeframe>300</timeframe>` |
| `<same_source_ip/>` | 동일 출발지 IP 조건 | `<same_source_ip/>` |
| `<description>` | 경보 설명 | 한글/영문 가능 |
| `<group>` | 룰 그룹 태그 | `<group>brute_force,</group>` |
| `<options>` | 추가 옵션 | `<options>no_email_alert</options>` |

### 레벨 기준

```
Level  0: 무시 (룰 비활성화)
Level  1: 없음
Level  2: 시스템 저수준 알림
Level  3: 성공 이벤트
Level  4: 시스템 저수준 에러
Level  5: 사용자 생성 에러
Level  6: 낮은 관련성 공격
Level  7: "나쁜 단어" 매칭
Level  8: 첫 번째 이벤트
Level  9: 비정상 소스 에러
Level 10: 다수 사용자 에러
Level 11: 무결성 검사 경고
Level 12: 높은 중요도 이벤트 (High)
Level 13: 비정상 에러 (높은 중요도)
Level 14: 높은 중요도 보안 이벤트
Level 15: 심각한 공격 (Critical)
```

## 1.3 상관 룰 핵심 패턴

### 패턴 1: Frequency (빈도 기반)

```xml
<!-- 같은 IP에서 5분 내 SSH 실패 10회 → 무차별 대입 공격 -->
<rule id="100010" level="10" frequency="10" timeframe="300">
  <if_matched_sid>100001</if_matched_sid>
  <same_source_ip/>
  <description>SSH 무차별 대입 공격 탐지 (10회/5분)</description>
  <group>brute_force,correlation,</group>
</rule>
```

### 패턴 2: Chain (체인 연결)

```xml
<!-- SSH 무차별 대입 후 로그인 성공 → 계정 탈취 의심 -->
<rule id="100011" level="13">
  <if_sid>100010</if_sid>
  <match>Accepted password</match>
  <same_source_ip/>
  <description>무차별 대입 후 SSH 로그인 성공 - 계정 탈취 의심!</description>
  <group>credential_compromise,correlation,</group>
</rule>
```

### 패턴 3: Cross-Source (다중 소스)

```xml
<!-- IPS 탐지 + 방화벽 차단 + SSH 시도 = 조직적 공격 -->
<rule id="100020" level="14" frequency="3" timeframe="600">
  <if_matched_group>attack</if_matched_group>
  <same_source_ip/>
  <description>다중 소스 연계: 조직적 공격 탐지</description>
  <group>apt,multi_source_correlation,</group>
</rule>
```

### 패턴 4: Negation (부정 조건)

```xml
<!-- VPN 접속 없이 내부 서버 접근 시도 → 비정상 접근 -->
<rule id="100030" level="12">
  <if_sid>18101</if_sid>
  <match>Accepted</match>
  <srcip>!10.20.30.0/24</srcip>
  <description>외부 IP에서 직접 SSH 접근 - VPN 우회 의심</description>
  <group>policy_violation,</group>
</rule>
```

## 1.4 상관분석 아키텍처

```
[로그 소스들]          [Wazuh Manager]         [경보 출력]
                       상관분석 엔진
+--------+            +----------------+       +----------+
| syslog | ---------> |                |       |          |
+--------+            | 1. Decoder     |       | alerts   |
+--------+            |    (로그 파싱)  | ----> | .json    |
| Apache | ---------> |                |       |          |
+--------+            | 2. Rule Match  |       | alerts   |
+--------+            |    (단일 매칭)  | ----> | .log     |
| Suricata| --------> |                |       |          |
+--------+            | 3. Correlation |       | Wazuh    |
+--------+            |    (상관분석)   | ----> | Dashboard|
| nftables| --------> |                |       |          |
+--------+            | 4. Active Resp |       | API      |
+--------+            |    (자동 대응)  | ----> | Output   |
| auth.log| --------> |                |       |          |
+--------+            +----------------+       +----------+
```

---

# Part 2: 고급 룰 요소 + 다중 소스 연계 (40분)

## 2.1 고급 frequency 활용

### 슬라이딩 윈도우 개념

```
시간축: --|----|----|----|----|----|----|-->
이벤트:   E1   E2   E3   E4   E5   E6

[고정 윈도우] 5분 단위:
  |-- 윈도우1 --|-- 윈도우2 --|
  E1 E2 E3       E4 E5 E6
  → 각 윈도우에서 3건 → 임계치 5 미만 → 미탐지

[슬라이딩 윈도우] 5분 간격:
  |-- 윈도우 --|
     |-- 윈도우 --|
        |-- 윈도우 --|
  → E2~E6 = 5건 → 임계치 5 도달 → 탐지!

Wazuh의 frequency + timeframe = 슬라이딩 윈도우 방식
```

### 고급 frequency 예시

```xml
<!-- 로그인 실패 후 성공 패턴 (Credential Stuffing) -->
<rule id="100040" level="12" frequency="20" timeframe="120">
  <if_matched_sid>5716</if_matched_sid>
  <same_source_ip/>
  <description>2분 내 SSH 인증 실패 20회 - Credential Stuffing</description>
  <mitre>
    <id>T1110.004</id>
  </mitre>
  <group>credential_stuffing,</group>
</rule>

<!-- 다른 계정으로의 반복 실패 (Password Spraying) -->
<rule id="100041" level="13" frequency="5" timeframe="300">
  <if_matched_sid>5716</if_matched_sid>
  <same_source_ip/>
  <not_same_user/>
  <description>5분 내 서로 다른 계정 SSH 실패 5회 - Password Spraying</description>
  <mitre>
    <id>T1110.003</id>
  </mitre>
  <group>password_spraying,</group>
</rule>
```

## 2.2 if_matched_sid / if_matched_group

### 체인 룰 설계

```
[공격 시나리오: 측면 이동 탐지]

Step 1: 포트 스캔 탐지 (Rule 100050)
    ↓
Step 2: 포트 스캔 후 서비스 접근 (Rule 100051)
    ↓
Step 3: 서비스 접근 후 권한 상승 시도 (Rule 100052)
    ↓
Step 4: 종합 → "측면 이동 공격" 판정 (Rule 100053)
```

```xml
<!-- Step 1: 포트 스캔 -->
<rule id="100050" level="6">
  <if_group>scan</if_group>
  <description>포트 스캔 활동 탐지</description>
  <group>recon,step1,</group>
</rule>

<!-- Step 2: 스캔 후 서비스 접근 -->
<rule id="100051" level="8">
  <if_matched_sid>100050</if_matched_sid>
  <match>connection accepted</match>
  <same_source_ip/>
  <timeframe>600</timeframe>
  <description>포트 스캔 후 서비스 접근 시도</description>
  <group>recon,step2,</group>
</rule>

<!-- Step 3: 접근 후 권한 상승 -->
<rule id="100052" level="12">
  <if_matched_sid>100051</if_matched_sid>
  <match>sudo|su |privilege</match>
  <same_source_ip/>
  <timeframe>1800</timeframe>
  <description>서비스 접근 후 권한 상승 시도</description>
  <group>privilege_escalation,step3,</group>
</rule>

<!-- Step 4: 종합 판정 -->
<rule id="100053" level="14">
  <if_matched_sid>100052</if_matched_sid>
  <same_source_ip/>
  <description>측면 이동 공격 체인 탐지 (스캔→접근→권한상승)</description>
  <mitre>
    <id>T1021</id>
  </mitre>
  <group>lateral_movement,critical_chain,</group>
</rule>
```

## 2.3 다중 소스 이벤트 연계

### 소스별 룰 ID 매핑

```
[Suricata IPS]          [nftables 방화벽]      [Wazuh HIDS]
Rule 86601-86700        Rule 88001-88100        Rule 5501-5600
                    \          |           /
                     \         |          /
                      v        v         v
              [상관분석 룰: 100100-100199]
              → 다중 소스 종합 판정
```

```xml
<!-- Suricata 경고 + nftables 차단 + SSH 시도 = 조직적 침투 시도 -->
<rule id="100100" level="14" frequency="3" timeframe="600">
  <if_matched_group>ids,firewall,authentication_failed</if_matched_group>
  <same_source_ip/>
  <description>다중 보안장비 연계: 조직적 침투 시도 탐지</description>
  <group>apt_attempt,multi_vector,</group>
</rule>
```

## 2.4 임계치 설계 원칙

```
[임계치가 너무 낮으면]
  threshold = 3회/5분
  → 정상 사용자의 오타도 경보 → 오탐 폭증
  → 경보 피로 → 분석가가 무시하기 시작
  → 실제 공격도 놓침

[임계치가 너무 높으면]
  threshold = 100회/5분
  → 느린 공격(Low & Slow) 탐지 불가
  → 공격자가 탐지 회피 가능
  → 미탐 증가

[적정 임계치 설정 방법]
  1. 베이스라인 측정: 정상 상태 이벤트 빈도 파악
  2. 표준편차 적용: 평균 + 2~3 시그마
  3. 테스트: 과거 데이터로 검증
  4. 튜닝: 오탐/미탐 비율 모니터링 후 조정
```

| 공격 유형 | 권장 frequency | 권장 timeframe | 근거 |
|-----------|---------------|---------------|------|
| SSH 무차별 대입 | 10회 | 300초 | 정상 사용자 3회 이하 |
| 웹 스캔 | 30회 | 60초 | 정상 웹 요청 빈도 대비 |
| Password Spraying | 5회 | 300초 | 계정 수 기준 |
| DDoS | 1000회 | 60초 | 네트워크 기준선 대비 |
| 포트 스캔 | 20포트 | 120초 | 정상 서비스 접근 패턴 |

---

# Part 3: 상관 룰 작성 실습 (50분)

## 3.1 SSH 무차별 대입 + 성공 탐지 룰

> **실습 목적**: 가장 기본적인 상관 룰인 "반복 실패 후 성공" 패턴을 작성한다.
>
> **배우는 것**: frequency, timeframe, same_source_ip, if_matched_sid 활용법
>
> **실전 활용**: 이 패턴은 SSH뿐 아니라 웹 로그인, VPN, RDP 등 모든 인증 시스템에 적용 가능

```bash
# siem 서버 접속
sshpass -p1 ssh siem@10.20.30.100

# 커스텀 룰 파일 백업
sudo cp /var/ossec/etc/rules/local_rules.xml \
        /var/ossec/etc/rules/local_rules.xml.bak.$(date +%Y%m%d)

# SSH 상관 룰 작성
sudo tee /var/ossec/etc/rules/local_rules.xml << 'RULES'
<group name="local,sshd,correlation,">

  <!-- SSH 로그인 실패 (기본 룰 5716 기반) -->
  <rule id="100001" level="5">
    <if_sid>5716</if_sid>
    <description>SSH 인증 실패 탐지</description>
    <group>authentication_failed,ssh,</group>
  </rule>

  <!-- SSH 무차별 대입: 5분 내 10회 실패 -->
  <rule id="100002" level="10" frequency="10" timeframe="300">
    <if_matched_sid>100001</if_matched_sid>
    <same_source_ip/>
    <description>[상관] SSH 무차별 대입 공격 (10회/5분)</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>brute_force,ssh,correlation,</group>
  </rule>

  <!-- 무차별 대입 후 SSH 로그인 성공 = 계정 탈취! -->
  <rule id="100003" level="14">
    <if_matched_sid>100002</if_matched_sid>
    <decoded_as>sshd</decoded_as>
    <match>Accepted</match>
    <same_source_ip/>
    <description>[CRITICAL] 무차별 대입 후 SSH 로그인 성공 - 계정 탈취!</description>
    <mitre>
      <id>T1078</id>
    </mitre>
    <group>credential_compromise,ssh,critical_alert,</group>
  </rule>

</group>
RULES

# 룰 문법 검사
sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"
```

> **명령어 해설**:
> - `wazuh-analysisd -t`: 룰 문법 검증 (서비스 재시작 없이 테스트)
> - `if_matched_sid`: 선행 룰이 발동된 상태에서만 이 룰을 검사
> - `frequency="10"`: 선행 룰이 10번 매칭되어야 발동
> - `same_source_ip/`: 모든 이벤트가 같은 출발지 IP에서 온 경우만
>
> **트러블슈팅**:
> - "Duplicated rule id" → 기존 local_rules.xml에 같은 ID가 있는지 확인
> - "Invalid rule" → XML 태그 닫힘 확인, 특수문자 이스케이프 확인

## 3.2 룰 테스트 - 공격 시뮬레이션

```bash
# opsclaw 서버에서 SSH 무차별 대입 시뮬레이션
# (siem 서버의 Wazuh가 탐지하도록)

# 먼저 siem에서 Wazuh 재시작 (새 룰 적용)
sshpass -p1 ssh siem@10.20.30.100 "sudo systemctl restart wazuh-manager"

# 5초 대기
sleep 5

# SSH 실패 시뮬레이션 (존재하지 않는 계정으로 시도)
echo "=== SSH 무차별 대입 시뮬레이션 시작 ==="
for i in $(seq 1 15); do
    sshpass -p wrong_password ssh -o StrictHostKeyChecking=no \
        -o ConnectTimeout=3 fake_user@10.20.30.100 \
        "echo test" 2>/dev/null
    echo "시도 $i/15 완료"
done

echo "=== 시뮬레이션 완료, 경보 확인 중... ==="
sleep 3

# siem에서 경보 확인
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'
echo "=== 최근 SSH 관련 경보 ==="
tail -50 /var/ossec/logs/alerts/alerts.log 2>/dev/null | \
  grep -A2 "Rule: 100" || echo "(커스텀 룰 경보 없음 - 기본 룰 확인)"

echo ""
echo "=== 최근 경보 (JSON) ==="
tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        rule = alert.get('rule', {})
        print(f\"Rule {rule.get('id','?'):>6s} (L{rule.get('level','?'):>2s}): {rule.get('description','?')}\")
    except: pass
"
EOF
```

> **결과 해석**: Rule 100002가 발동했다면 frequency+timeframe 상관분석이 정상 작동하는 것이다. Rule 100003이 발동했다면 체인 룰도 정상이다 (실제 성공 로그가 있어야 함).
>
> **트러블슈팅**:
> - 경보가 안 나오면 → `wazuh-manager` 재시작 확인, 로그 수집 경로 확인
> - 기본 룰만 나오면 → `local_rules.xml` 문법 확인, Rule ID 충돌 확인

## 3.3 웹 공격 상관 룰

```bash
# siem 서버에서 웹 공격 상관 룰 추가
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# 웹 공격 상관 룰 추가
sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,web,correlation,">

  <!-- 웹 디렉토리 스캔: 1분 내 404 에러 30회 -->
  <rule id="100101" level="8" frequency="30" timeframe="60">
    <if_sid>31101</if_sid>
    <same_source_ip/>
    <description>[상관] 웹 디렉토리 스캔 탐지 (404 x 30/1분)</description>
    <mitre>
      <id>T1595.002</id>
    </mitre>
    <group>web_scan,recon,correlation,</group>
  </rule>

  <!-- SQL Injection 시도 반복: 5분 내 5회 -->
  <rule id="100102" level="12" frequency="5" timeframe="300">
    <if_sid>31103,31104,31105</if_sid>
    <same_source_ip/>
    <description>[상관] SQL Injection 반복 시도 (5회/5분)</description>
    <mitre>
      <id>T1190</id>
    </mitre>
    <group>sqli,web_attack,correlation,</group>
  </rule>

  <!-- XSS 시도 후 세션 탈취 의심 -->
  <rule id="100103" level="13">
    <if_matched_group>xss</if_matched_group>
    <match>Set-Cookie|session|token</match>
    <same_source_ip/>
    <description>[상관] XSS 후 세션 탈취 의심</description>
    <mitre>
      <id>T1189</id>
    </mitre>
    <group>xss,session_hijack,correlation,</group>
  </rule>

  <!-- 웹 스캔 + SQL Injection = 체계적 웹 공격 -->
  <rule id="100104" level="14">
    <if_matched_sid>100101</if_matched_sid>
    <if_matched_sid>100102</if_matched_sid>
    <same_source_ip/>
    <timeframe>1800</timeframe>
    <description>[CRITICAL] 체계적 웹 공격 탐지 (스캔+SQLi)</description>
    <group>web_attack,apt_web,critical_alert,</group>
  </rule>

</group>
RULES

# 룰 문법 검사
sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"

REMOTE
```

> **실습 목적**: 웹 공격 시나리오에 맞는 다단계 상관 룰을 작성하여, 단순 스캔과 실제 공격을 구분한다.

## 3.4 다중 소스 연계 룰 - Suricata + Wazuh

```bash
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE'

# 다중 소스 상관 룰
sudo tee -a /var/ossec/etc/rules/local_rules.xml << 'RULES'

<group name="local,multi_source,correlation,">

  <!-- Suricata IPS 경고 후 방화벽 차단 = 공격 시도 확인 -->
  <rule id="100201" level="10">
    <if_group>ids</if_group>
    <match>Drop|BLOCK|denied</match>
    <same_source_ip/>
    <timeframe>120</timeframe>
    <description>[다중소스] IPS 탐지 + 방화벽 차단 연계</description>
    <group>ids_fw_correlation,</group>
  </rule>

  <!-- IPS 탐지 + 방화벽 차단 실패(통과) = 침투 성공 의심 -->
  <rule id="100202" level="14">
    <if_group>ids</if_group>
    <match>Accept|ALLOW|pass</match>
    <same_source_ip/>
    <timeframe>120</timeframe>
    <description>[CRITICAL] IPS 탐지되었으나 방화벽 통과 - 침투 의심!</description>
    <group>fw_bypass,critical_alert,</group>
  </rule>

  <!-- 외부 IP에서 IPS + 웹서버 + SSH 동시 접근 = APT 의심 -->
  <rule id="100203" level="15" frequency="5" timeframe="900">
    <if_matched_group>ids,web_attack,authentication_failed</if_matched_group>
    <same_source_ip/>
    <srcip>!10.20.30.0/24</srcip>
    <description>[APT] 외부 IP 다중 벡터 공격 탐지</description>
    <mitre>
      <id>T1190</id>
    </mitre>
    <group>apt,multi_vector,critical_alert,</group>
  </rule>

</group>
RULES

sudo /var/ossec/bin/wazuh-analysisd -t
echo "Exit code: $?"
sudo systemctl restart wazuh-manager

REMOTE
```

> **배우는 것**: `if_group`으로 여러 그룹(ids, web_attack, authentication_failed)의 이벤트를 동시에 조건으로 거는 방법. 이것이 진정한 다중 소스 상관분석이다.

## 3.5 wazuh-logtest로 룰 검증

```bash
# siem 서버에서 logtest 도구로 룰 매칭 검증
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'

# 테스트 로그 입력으로 룰 매칭 확인
echo 'Apr  4 10:15:23 web sshd[12345]: Failed password for invalid user admin from 192.168.1.100 port 54321 ssh2' | \
  sudo /var/ossec/bin/wazuh-logtest -q 2>/dev/null | tail -20

echo "---"

echo 'Apr  4 10:15:23 web sshd[12345]: Accepted password for root from 192.168.1.100 port 54322 ssh2' | \
  sudo /var/ossec/bin/wazuh-logtest -q 2>/dev/null | tail -20

EOF
```

> **명령어 해설**: `wazuh-logtest`는 실제 로그를 넣어서 어떤 디코더와 룰이 매칭되는지 확인하는 디버깅 도구다. 새 룰을 작성한 후 반드시 이 도구로 검증해야 한다.

---

# Part 4: 룰 튜닝 + OpsClaw 자동화 (40분)

## 4.1 오탐 분석 및 튜닝

```bash
# 최근 경보에서 오탐 패턴 분석
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'
echo "=== 최근 24시간 경보 Rule ID 분포 ==="
cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
  python3 -c "
import sys, json
from collections import Counter

rule_counter = Counter()
for line in sys.stdin:
    try:
        alert = json.loads(line.strip())
        rid = alert.get('rule', {}).get('id', 'unknown')
        desc = alert.get('rule', {}).get('description', 'unknown')
        rule_counter[f'{rid}: {desc[:40]}'] += 1
    except:
        pass

print(f'총 고유 룰: {len(rule_counter)}개')
print(f'총 경보: {sum(rule_counter.values())}건')
print()
for rule, count in rule_counter.most_common(15):
    pct = count / sum(rule_counter.values()) * 100
    bar = '#' * min(int(pct), 40)
    print(f'  {count:5d} ({pct:5.1f}%) {rule} {bar}')
"
EOF
```

> **결과 해석**: 상위 3개 룰이 전체 경보의 50% 이상을 차지하면 해당 룰의 임계치를 조정하거나, 정상 패턴을 화이트리스트에 추가해야 한다.

### 화이트리스트 룰 작성

```xml
<!-- 오탐 제거: 내부 모니터링 시스템의 반복 접근 제외 -->
<rule id="100900" level="0">
  <if_sid>100002</if_sid>
  <srcip>10.20.30.201</srcip>
  <description>화이트리스트: OpsClaw 모니터링 SSH 접근</description>
</rule>

<!-- 오탐 제거: 스케줄 작업의 정기 점검 제외 -->
<rule id="100901" level="0">
  <if_sid>100101</if_sid>
  <srcip>10.20.30.201</srcip>
  <time>02:00-04:00</time>
  <description>화이트리스트: 새벽 자동 점검 웹 스캔</description>
</rule>
```

## 4.2 룰 성능 모니터링

```bash
# 룰 매칭 성능 확인
sshpass -p1 ssh siem@10.20.30.100 << 'EOF'
echo "=== Wazuh 분석 엔진 상태 ==="
sudo /var/ossec/bin/wazuh-analysisd -s 2>/dev/null | head -30

echo ""
echo "=== 처리량 (events/sec) ==="
sudo cat /var/ossec/var/run/wazuh-analysisd.state 2>/dev/null | \
  grep -E "events_received|events_dropped|alerts_written" || \
  echo "(상태 파일 없음)"

echo ""
echo "=== 경보 로그 크기 ==="
du -sh /var/ossec/logs/alerts/ 2>/dev/null
ls -la /var/ossec/logs/alerts/alerts.json 2>/dev/null
EOF
```

## 4.3 OpsClaw를 활용한 상관 룰 배포 자동화

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 프로젝트 생성 - 상관 룰 배포
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "correlation-rule-deploy",
    "request_text": "SIEM 상관 룰 배포 및 검증",
    "master_mode": "external"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project: $PROJECT_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 다중 서버 점검 자동화
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "wazuh-analysisd -t 2>&1 | tail -5 && echo RULE_CHECK_OK",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "grep -c \"<rule id\" /var/ossec/etc/rules/local_rules.xml && echo CUSTOM_RULES_COUNT",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "tail -20 /var/ossec/logs/alerts/alerts.log | grep -c \"Rule:\" && echo RECENT_ALERTS",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://10.20.30.100:8002"
  }'

# 결과 확인
sleep 3
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool
```

> **실전 활용**: 상관 룰 변경을 OpsClaw 프로젝트로 관리하면 변경 이력(evidence)이 자동 기록되어 감사 추적이 가능하다. 여러 SIEM에 동일 룰을 배포할 때 일관성을 보장한다.

## 4.4 상관분석 효과 측정

```bash
cat << 'SCRIPT' > /tmp/correlation_effectiveness.py
#!/usr/bin/env python3
"""상관분석 룰 효과 측정"""

# 시뮬레이션 데이터
data = {
    "단일 룰만 사용": {
        "전체_경보": 5000,
        "오탐": 4200,
        "실제_위협_탐지": 50,
        "미탐": 30,
    },
    "상관분석 추가": {
        "전체_경보": 800,
        "오탐": 150,
        "실제_위협_탐지": 72,
        "미탐": 8,
    },
}

print("=" * 65)
print("  상관분석 도입 전후 효과 비교")
print("=" * 65)
print(f"\n{'지표':20s} {'단일 룰':>12s} {'상관분석':>12s} {'개선':>10s}")
print("-" * 60)

for metric in ["전체_경보", "오탐", "실제_위협_탐지", "미탐"]:
    before = data["단일 룰만 사용"][metric]
    after = data["상관분석 추가"][metric]
    change = (after - before) / before * 100
    sign = "+" if change > 0 else ""
    print(f"{metric:20s} {before:>12,d} {after:>12,d} {sign}{change:>8.1f}%")

# KPI 계산
for scenario, d in data.items():
    fp_rate = d["오탐"] / d["전체_경보"] * 100
    detect_rate = d["실제_위협_탐지"] / (d["실제_위협_탐지"] + d["미탐"]) * 100
    precision = d["실제_위협_탐지"] / (d["전체_경보"] - d["오탐"]) * 100 if (d["전체_경보"] - d["오탐"]) > 0 else 0

    print(f"\n--- {scenario} ---")
    print(f"  오탐률:  {fp_rate:.1f}%")
    print(f"  탐지율:  {detect_rate:.1f}%")
    print(f"  정밀도:  {precision:.1f}%")

print("\n→ 상관분석 도입으로 경보 84% 감소, 탐지율 10%p 향상")
SCRIPT

python3 /tmp/correlation_effectiveness.py
```

---

## 체크리스트

- [ ] 상관분석의 개념과 단일 이벤트 탐지의 한계를 설명할 수 있다
- [ ] Wazuh 룰 XML 구조의 핵심 요소를 알고 있다
- [ ] frequency + timeframe 조합으로 빈도 기반 룰을 작성할 수 있다
- [ ] if_matched_sid를 사용하여 체인 룰을 구성할 수 있다
- [ ] same_source_ip의 역할과 사용 시점을 이해한다
- [ ] 다중 소스(IPS+방화벽+HIDS) 연계 룰을 설계할 수 있다
- [ ] 임계치 설정 원칙(베이스라인, 시그마, 테스트, 튜닝)을 알고 있다
- [ ] wazuh-logtest로 룰 매칭을 검증할 수 있다
- [ ] 화이트리스트 룰로 오탐을 제거할 수 있다
- [ ] OpsClaw로 룰 배포를 자동화할 수 있다

---

## 복습 퀴즈

**Q1.** 상관분석(Correlation)이 단일 이벤트 탐지보다 우수한 이유 2가지를 설명하시오.

<details><summary>정답</summary>
1) 개별로는 무해한 이벤트들의 조합에서 위협을 탐지할 수 있다 (예: 실패 10회 + 성공 1회 = 계정 탈취).
2) 오탐을 줄일 수 있다 - 다중 조건을 만족해야 경보가 발생하므로 정밀도가 높아진다.
</details>

**Q2.** Wazuh 룰에서 `frequency="10" timeframe="300"`의 의미는?

<details><summary>정답</summary>
300초(5분) 시간 윈도우 내에서 선행 룰(if_matched_sid로 지정)이 10회 이상 매칭되면 이 룰이 발동한다는 의미다.
</details>

**Q3.** `same_source_ip/`를 빼면 어떤 문제가 생기는가?

<details><summary>정답</summary>
서로 다른 IP의 이벤트도 합산되어 카운트된다. 예를 들어 10개의 서로 다른 IP에서 각 1회 실패해도 합산 10회로 경보가 발생하여 오탐이 크게 늘어난다.
</details>

**Q4.** Rule level 0의 용도는?

<details><summary>정답</summary>
해당 룰을 비활성화(사실상 무시)하는 것이다. 주로 화이트리스트 용도로, 특정 조건의 이벤트를 경보에서 제외할 때 사용한다. level="0"인 룰은 경보를 생성하지 않는다.
</details>

**Q5.** 임계치를 너무 높게 설정하면 어떤 공격을 놓칠 수 있는가?

<details><summary>정답</summary>
Low & Slow 공격(느린 공격)을 놓칠 수 있다. 공격자가 탐지를 피하기 위해 의도적으로 시도 간격을 넓히면 임계치 이하로 유지되어 탐지가 안 된다.
</details>

**Q6.** 다중 소스 상관분석에서 IPS 경고와 방화벽 로그를 연계할 때 가장 중요한 공통 필드는?

<details><summary>정답</summary>
출발지 IP(source IP)이다. same_source_ip 조건으로 동일 공격자의 행위를 여러 보안 장비에서 추적할 수 있다. 시간대(timestamp)도 중요한 연계 기준이다.
</details>

**Q7.** `wazuh-logtest`의 용도를 설명하시오.

<details><summary>정답</summary>
테스트 로그를 입력하여 Wazuh의 디코더와 룰 매칭 결과를 확인하는 디버깅 도구다. 새 룰을 작성한 후 실제 서비스에 적용하기 전에 이 도구로 기대한 대로 동작하는지 검증해야 한다.
</details>

**Q8.** 체인 룰(chain rule)이 유용한 공격 시나리오를 1개 설명하시오.

<details><summary>정답</summary>
측면 이동(Lateral Movement) 탐지: 포트 스캔(Rule A) → 서비스 접근(Rule B, if_matched_sid=A) → 권한 상승(Rule C, if_matched_sid=B). 각 단계는 단독으로 위협이 아니지만 순서대로 발생하면 공격 체인이다.
</details>

**Q9.** 오탐률이 84%인 상태에서 가장 먼저 해야 할 조치는?

<details><summary>정답</summary>
경보 빈도가 가장 높은 상위 3-5개 룰을 식별하여, 1) 정상 패턴을 화이트리스트(level="0")로 제외하고, 2) frequency/timeframe 임계치를 상향 조정하고, 3) 베이스라인 대비 비정상 패턴만 탐지하도록 조건을 추가한다.
</details>

**Q10.** Wazuh 커스텀 룰 ID의 권장 범위와 그 이유는?

<details><summary>정답</summary>
100000-109999 범위를 사용한다. Wazuh 기본 룰이 1-99999를 사용하므로, 커스텀 룰은 100000번대를 써야 기본 룰과 충돌하지 않는다. 업데이트 시 기본 룰은 덮어쓰기되지만 커스텀 룰은 보존된다.
</details>

---

## 과제

### 과제 1: 브루트포스 연계 상관 룰 세트 (필수)

다음 시나리오를 탐지하는 상관 룰 세트를 작성하라:
1. SSH 무차별 대입 탐지 (10회/5분)
2. 무차별 대입 성공 후 sudo 사용 탐지
3. sudo 사용 후 민감 파일(/etc/shadow, /etc/passwd) 접근 탐지
4. 전체 체인을 연결한 "계정 탈취 + 권한 상승" 종합 룰

**제출물**: local_rules.xml 파일 + wazuh-logtest 검증 결과 스크린샷

### 과제 2: 오탐 분석 보고서 (선택)

실습 환경에서 24시간 동안 발생한 경보를 분석하여:
1. 상위 5개 경보 룰과 발생 건수
2. 각 룰의 오탐 여부 판단 (증거 포함)
3. 오탐 제거를 위한 화이트리스트 룰 제안
4. 예상 오탐률 개선 효과

---

## 다음 주 예고

**Week 03: SIGMA 룰 심화**에서는 SIEM 벤더에 독립적인 SIGMA 룰의 고급 문법을 학습하고, Wazuh/Splunk/ELK용으로 변환하는 방법을 실습한다.
