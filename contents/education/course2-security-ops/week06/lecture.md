# Week 06: Suricata IPS (3) — 운영

## 학습 목표
- eve.json과 fast.log를 분석할 수 있다
- Suricata 성능을 모니터링하고 튜닝할 수 있다
- 오탐(False Positive)을 식별하고 관리할 수 있다

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
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---

---

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |

---

# Week 06: Suricata IPS (3) — 운영

## 학습 목표

- eve.json과 fast.log를 분석할 수 있다
- Suricata 성능을 모니터링하고 튜닝할 수 있다
- 오탐(False Positive)을 식별하고 관리할 수 있다

---

## 1. 로그 파일 구조

| 로그 파일 | 형식 | 용도 |
|-----------|------|------|
| `eve.json` | JSON | **핵심 로그** — 모든 이벤트를 구조화된 형식으로 기록 |
| `fast.log` | 텍스트 | 알림 한 줄 요약 (빠른 확인용) |
| `stats.log` | 텍스트 | 엔진 통계 |
| `suricata.log` | 텍스트 | 엔진 상태/오류 |

---

## 2. 실습 환경 접속

> **이 실습을 왜 하는가?**
> "Suricata IPS (3) — 운영" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

> **실습 목적**: Suricata IPS의 운영 관리 - 룰 업데이트, 성능 튜닝, 오탐 억제를 실습한다
>
> **배우는 것**: ET 룰셋 업데이트, threshold 설정으로 오탐 억제, 성능 모니터링 방법을 배운다
>
> **결과 해석**: threshold 적용 후 반복 알림이 줄어들고, stats.log에서 패킷 처리량이 정상 범위이면 튜닝이 효과적이다
>
> **실전 활용**: SOC 운영에서 오탐 관리(Alert Fatigue 방지)는 IPS 운영의 가장 큰 과제이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
```

---

## 3. fast.log 분석

> **이 실습의 목적:**
> Suricata의 `fast.log`는 **모든 알림을 한 줄씩 기록**하는 핵심 로그 파일이다.
> SOC 분석가의 일상은 이 로그를 모니터링하고 분석하는 것에서 시작한다.
> 로그의 각 필드(시간, SID, 메시지, IP)를 읽는 법을 익히면,
> "언제, 어떤 공격이, 어디서 왔는지"를 즉시 파악할 수 있다.
>
> **실무 활용:**
> - 실시간 모니터링: `tail -f fast.log`로 알림을 실시간 관찰
> - 빈도 분석: 어떤 룰이 가장 많이 트리거되는지 → 오탐 조정 또는 공격 패턴 파악
> - 특정 IP 추적: 공격 의심 IP의 알림 이력 검색
>
> **주의:** fast.log는 빠르게 커질 수 있다. 운영 환경에서는 logrotate로 관리한다.

### 3.1 기본 확인

> **이 명령을 왜 실행하는가?**
> 가장 최근 20건의 알림을 확인하여 현재 어떤 위협이 탐지되고 있는지 한눈에 파악한다.
> 정상 운영 시 대부분은 ET 기본 룰의 정보성 알림이고, 커스텀 룰(SID 9000000+)이 보이면 주목해야 한다.

```bash
echo 1 | sudo -S tail -20 /var/log/suricata/fast.log
```

**예상 출력:**
```
03/27/2026-10:15:22.456789  [**] [1:2024897:4] ET WEB_SERVER SQL Injection Attempt [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.80:45678 -> 10.20.30.1:80
03/27/2026-10:15:23.123456  [**] [1:9000010:1] CUSTOM - SQL Injection in URI [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.80:45679 -> 10.20.30.1:80
```

**각 필드 의미:**

```
날짜-시간  [**] [gid:sid:rev] 메시지 [**] [분류] [우선순위] {프로토콜} 출발지 -> 목적지
```

### 3.2 빈도 분석

```bash
# 가장 많이 발생한 알림 TOP 10
echo 1 | sudo -S cat /var/log/suricata/fast.log | \
  awk -F'\\]' '{print $2}' | sort | uniq -c | sort -rn | head -10  # 텍스트 필드 처리
```

### 3.3 특정 SID 검색

```bash
# SID 9000010 (SQL Injection) 알림만 확인
echo 1 | sudo -S grep "9000010" /var/log/suricata/fast.log | tail -5
```

### 3.4 출발지 IP별 알림 수

로그나 설정에서 특정 패턴을 검색합니다.

```bash
echo 1 | sudo -S cat /var/log/suricata/fast.log | \
  grep -oP '\d+\.\d+\.\d+\.\d+:\d+ ->' | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -10  # 텍스트 필드 처리
```

---

## 4. eve.json 분석

eve.json은 구조화된 JSON 형식으로, 훨씬 풍부한 정보를 제공한다.

### 4.1 이벤트 타입 확인

```bash
# 이벤트 타입별 개수
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
types = {}
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        t = e.get('event_type','unknown')
        types[t] = types.get(t,0) + 1
    except: pass
for t,c in sorted(types.items(), key=lambda x:-x[1]):  # 반복문 시작
    print(f'{c:>8}  {t}')
"
```

**예상 출력:**
```
   15234  flow
    3456  http
     892  dns
     234  alert
      45  tls
      12  stats
```

### 4.2 알림(alert) 이벤트 상세 보기

```bash
# 최근 알림 5개를 보기 좋게 출력
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
alerts = []
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            alerts.append(e)
    except: pass
for a in alerts[-5:]:                                  # 반복문 시작
    al = a['alert']
    print(f\"[{a['timestamp']}] SID:{al['signature_id']} {al['signature']}\")
    print(f\"  {a.get('src_ip','?')}:{a.get('src_port','?')} -> {a.get('dest_ip','?')}:{a.get('dest_port','?')}\")
    print(f\"  Severity: {al.get('severity','?')} Category: {al.get('category','?')}\")
    if 'http' in a:
        print(f\"  HTTP: {a['http'].get('http_method','?')} {a['http'].get('hostname','?')}{a['http'].get('url','?')}\")
    print()
"
```

**예상 출력:**
```
[2026-03-27T10:15:22.456789+0000] SID:9000010 CUSTOM - SQL Injection in URI (union select)
  10.20.30.80:45678 -> 10.20.30.1:80
  Severity: 1 Category: Web Application Attack
  HTTP: GET 10.20.30.80/?q=1 union select 1,2,3
```

### 4.3 jq를 사용한 분석

```bash
# jq가 설치되어 있는 경우
echo 1 | sudo -S tail -100 /var/log/suricata/eve.json | \
  jq 'select(.event_type=="alert") | {
    time: .timestamp,
    sig: .alert.signature,
    sid: .alert.signature_id,
    src: .src_ip,
    dst: .dest_ip,
    severity: .alert.severity
  }' 2>/dev/null | head -30
```

### 4.4 HTTP 트래픽 분석

```bash
# HTTP 요청 로그 (공격과 무관한 정상 트래픽 포함)
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'http':
            h = e['http']
            print(f\"{e['timestamp'][:19]} {h.get('http_method','?'):6} {h.get('hostname','?')}{h.get('url','?')[:80]} [{h.get('status','-')}]\")
    except: pass
" | tail -20
```

---

## 5. 성능 모니터링

### 5.1 Suricata 엔진 통계

```bash
echo 1 | sudo -S cat /var/log/suricata/stats.log | tail -40
```

**주요 지표:**

| 지표 | 설명 | 정상 범위 |
|------|------|-----------|
| `capture.kernel_packets` | 커널에서 받은 패킷 | 증가 추세 |
| `capture.kernel_drops` | **커널 드롭** | 0에 가까워야 함 |
| `decoder.pkts` | 디코딩 패킷 | 증가 추세 |
| `detect.alert` | 탐지 알림 수 | 환경에 따라 다름 |
| `flow.memuse` | 플로우 메모리 사용량 | 설정된 max 이하 |
| `tcp.sessions` | TCP 세션 수 | 환경에 따라 다름 |

### 5.2 드롭 확인 (가장 중요)

```bash
# 커널 드롭 확인
echo 1 | sudo -S cat /var/log/suricata/stats.log | grep "kernel_drops" | tail -5
```

**예상 출력 (정상):**
```
capture.kernel_drops             | Total: 0        | Per min: 0
```

> 커널 드롭이 발생하면 패킷을 분석하지 못하고 놓치는 것이다. **즉시 튜닝 필요**.

### 5.3 실시간 통계 (eve.json)

```bash
echo 1 | sudo -S tail -f /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'stats':
            s = e['stats']
            cap = s.get('capture',{})
            det = s.get('detect',{})
            print(f\"Pkts: {cap.get('kernel_packets',0):>10} Drops: {cap.get('kernel_drops',0):>6} Alerts: {det.get('alert',0):>6}\")
    except: pass
" &
```

Ctrl+C로 종료한다.

---

## 6. 성능 튜닝

### 6.1 NFQUEUE 설정 최적화

`/etc/suricata/suricata.yaml`:

```yaml
nfq:
  mode: accept
  batchcount: 20       # 한 번에 처리할 패킷 수 (기본 1, 늘리면 성능 향상)
  fail-open: yes
```

### 6.2 메모리 설정

```yaml
# 플로우 관련 메모리
flow:
  memcap: 128mb        # 플로우 메모리 상한
  hash-size: 65536
  prealloc: 10000

# 스트림 메모리
stream:
  memcap: 256mb
  reassembly:
    memcap: 256mb
    depth: 1mb         # 재조합 깊이 (줄이면 성능 향상)
```

### 6.3 룰 프로파일링

어떤 룰이 성능에 영향을 주는지 확인:

```yaml
# suricata.yaml에 추가
profiling:
  rules:
    enabled: yes
    filename: rule_perf.log
    sort: avgticks
    limit: 20
```

```bash
# 프로파일링 결과 확인 (재시작 후)
echo 1 | sudo -S cat /var/log/suricata/rule_perf.log | head -30
```

### 6.4 불필요한 프로토콜 파서 비활성화

사용하지 않는 프로토콜 파서를 끄면 성능이 향상된다:

```yaml
app-layer:
  protocols:
    ftp:
      enabled: no      # FTP 미사용 시
    smtp:
      enabled: no      # SMTP 미사용 시
    smb:
      enabled: no
```

---

## 7. 오탐(False Positive) 관리

### 7.1 오탐이란?

| 용어 | 의미 | 예시 |
|------|------|------|
| True Positive (TP) | 실제 공격을 탐지 | SQL Injection 차단 |
| **False Positive (FP)** | **정상을 공격으로 오인** | 검색어가 SQL 문법 포함 |
| False Negative (FN) | 공격을 탐지 못함 | 우회 공격 |
| True Negative (TN) | 정상을 정상으로 판단 | 일반 웹 접근 |

### 7.2 오탐 식별

```bash
# 가장 많이 발생하는 알림 확인 (오탐 후보)
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
sigs = {}
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            key = f\"{e['alert']['signature_id']}:{e['alert']['signature']}\"
            sigs[key] = sigs.get(key,0) + 1
    except: pass
for s,c in sorted(sigs.items(), key=lambda x:-x[1])[:10]:  # 반복문 시작
    print(f'{c:>6}  {s}')
"
```

### 7.3 오탐 처리 방법

**방법 1: 룰 비활성화 (suricata-update)**

```bash
# 특정 SID 비활성화
echo "2024897" | sudo tee -a /etc/suricata/disable.conf
echo 1 | sudo -S suricata-update
echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

**방법 2: suppress (특정 조건에서만 무시)**

`/etc/suricata/threshold.config`:

```bash
# 특정 IP에서 오는 특정 SID 무시
echo 'suppress gen_id 1, sig_id 2024897, track by_src, ip 10.20.30.80' | \
  sudo tee -a /etc/suricata/threshold.config           # 표준 출력 + 파일 저장
```

**방법 3: pass 룰 (특정 트래픽 허용)**

```bash
# 모니터링 도구의 트래픽을 허용
echo 'pass http 10.20.30.100 any -> any any (msg:"Allow SIEM health check"; content:"/health"; http.uri; sid:9000099; rev:1;)' | \
  sudo tee -a /etc/suricata/rules/local.rules          # 표준 출력 + 파일 저장
```

> pass 룰은 다른 룰보다 먼저 평가된다.

### 7.4 오탐 관리 워크플로우

```
1. 빈발 알림 목록 작성
2. 각 알림의 실제 트래픽 확인 (eve.json)
3. 정상 트래픽인지 공격인지 판단
4. 오탐이면:
   a. 특정 조건만 해당 → suppress
   b. 룰 자체가 불필요 → disable
   c. 일부만 허용 → pass 룰
5. 변경 후 모니터링
```

---

## 8. 로그 로테이션

### 8.1 logrotate 설정

```bash
echo 1 | sudo -S cat /etc/logrotate.d/suricata 2>/dev/null
```

설정이 없으면 생성:

```bash
echo 1 | sudo -S tee /etc/logrotate.d/suricata << 'EOF'
/var/log/suricata/*.log /var/log/suricata/*.json {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 root root
    postrotate
        /bin/kill -HUP $(cat /var/run/suricata.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
```

### 8.2 디스크 사용량 확인

```bash
echo 1 | sudo -S du -sh /var/log/suricata/
echo 1 | sudo -S ls -lh /var/log/suricata/
```

---

## 9. 운영 체크리스트

일일 점검:

```bash
# 1. 서비스 상태
echo 1 | sudo -S systemctl is-active suricata

# 2. 커널 드롭 확인
echo 1 | sudo -S grep "kernel_drops" /var/log/suricata/stats.log | tail -1

# 3. 최근 24시간 알림 수
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(hours=24)
cnt = 0
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            cnt += 1
    except: pass
print(f'최근 알림 수: {cnt}')
"

# 4. 디스크 사용량
echo 1 | sudo -S du -sh /var/log/suricata/

# 5. 높은 심각도 알림
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "                                         # Python 코드 실행
import sys, json
for line in sys.stdin:                                 # 반복문 시작
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert' and e['alert'].get('severity',4) <= 2:
            print(f\"{e['timestamp'][:19]} [{e['alert']['severity']}] {e['alert']['signature']}\")
    except: pass
" | tail -10
```

---

## 10. 실습 과제

### 과제 1: 로그 분석

1. fast.log에서 가장 많이 발생한 알림 TOP 5를 구하라
2. eve.json에서 severity 1인 알림만 출력하라
3. 특정 출발지 IP의 알림 이력을 추적하라

### 과제 2: 오탐 처리

1. 실습 중 발생한 알림 중 오탐을 식별하라
2. suppress 설정으로 오탐을 처리하라
3. 처리 후 알림이 발생하지 않는 것을 확인하라

### 과제 3: 성능 확인

1. stats.log에서 커널 드롭 수를 확인하라
2. 현재 메모리 사용량을 확인하라
3. 불필요한 프로토콜 파서를 비활성화하라

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| eve.json | 구조화된 JSON 이벤트 로그 (핵심) |
| fast.log | 한 줄 요약 알림 로그 |
| kernel_drops | 패킷 드롭 수 (0이어야 정상) |
| False Positive | 정상을 공격으로 오인 |
| suppress | 특정 조건에서 알림 무시 |
| disable.conf | 룰 비활성화 |
| pass 룰 | 특정 트래픽 허용 |
| batchcount | NFQUEUE 배치 크기 (성능) |
| logrotate | 로그 자동 순환 |

---

## 다음 주 예고

Week 07에서는 Apache+ModSecurity WAF를 다룬다:
- ModSecurity Core Rule Set (CRS)
- 커스텀 WAF 룰
- 예외 처리
- web 서버(10.20.30.80)에서 실습

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** nftables에서 policy drop의 의미는?
- (a) 모든 트래픽 허용  (b) **명시적으로 허용하지 않은 모든 트래픽 차단**  (c) 로그만 기록  (d) 특정 IP만 차단

**Q2.** Suricata가 nftables와 다른 핵심 차이는?
- (a) IP만 검사  (b) **패킷 페이로드(내용)까지 검사**  (c) 포트만 검사  (d) MAC 주소만 검사

**Q3.** Wazuh에서 level 12 경보의 의미는?
- (a) 정보성 이벤트  (b) **높은 심각도 — 즉시 분석 필요**  (c) 정상 활동  (d) 시스템 시작

**Q4.** ModSecurity CRS의 Anomaly Scoring이란?
- (a) 모든 요청 차단  (b) **규칙 매칭 점수를 누적하여 임계값 초과 시 차단**  (c) IP 기반 차단  (d) 시간 기반 차단

**Q5.** 보안 솔루션 배치 순서(외부→내부)는?
- (a) WAF → 방화벽 → IPS  (b) **방화벽 → IPS → WAF → 애플리케이션**  (c) IPS → WAF → 방화벽  (d) 애플리케이션 → WAF

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): nftables(inet filter+ip nat), Suricata 8.0.4(65K룰), Apache+ModSecurity(:8082→403), Wazuh v4.11.2(local_rules 62줄), OpenCTI(200)
