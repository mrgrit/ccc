# Week 07: IDS/IPS 구축 — Suricata

## 학습 목표
- IDS(침입 탐지 시스템)와 IPS(침입 방지 시스템)의 차이를 이해한다
- Suricata의 아키텍처와 동작 원리를 설명할 수 있다
- Suricata 룰 문법을 이해하고 커스텀 룰을 작성할 수 있다
- 네트워크 공격(포트 스캔, SQLi, XSS)을 탐지하는 룰을 작성할 수 있다
- Suricata 로그(fast.log, eve.json)를 분석하여 공격을 식별할 수 있다
- IDS/IPS 모드의 차이를 이해하고 환경에 맞게 선택할 수 있다
- 공방전에서 Blue Team의 핵심 탐지 수단으로 Suricata를 활용할 수 있다

## 전제 조건
- Week 06 방화벽 구축 완료
- TCP/IP 네트워크 및 HTTP 프로토콜 이해
- nmap, SQL Injection, XSS 등 공격 기법 이해 (Week 01-05)

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | IDS/IPS 이론 + Suricata 아키텍처 | 강의 |
| 0:40-1:10 | Suricata 룰 문법 상세 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 포트 스캔 탐지 룰 작성 실습 | 실습 |
| 2:00-2:30 | 웹 공격 탐지 룰 작성 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 IDS 모니터링 실습 | 실습 |
| 3:10-3:40 | IDS 우회 기법 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: IDS/IPS 이론 + Suricata 아키텍처 (40분)

## 1.1 IDS vs IPS

| 항목 | IDS | IPS |
|------|-----|-----|
| 약자 | Intrusion Detection System | Intrusion Prevention System |
| 동작 | 탐지 + 경보 (수동) | 탐지 + 차단 (능동) |
| 배치 | 미러 포트/TAP (패킷 복사) | 인라인 (트래픽 경유) |
| 성능 영향 | 없음 | 있음 (지연 가능) |
| 오탐 위험 | 경보만 (서비스 영향 없음) | 정상 트래픽 차단 위험 |
| 사용 시나리오 | 모니터링, 사후 분석 | 실시간 방어 |

### 탐지 방식

| 방식 | 설명 | 장점 | 단점 |
|------|------|------|------|
| 시그니처 기반 | 알려진 공격 패턴 매칭 | 정확, 빠름 | 제로데이 미탐 |
| 이상 탐지 | 정상 기준 대비 이상 행위 | 제로데이 탐지 가능 | 오탐 많음 |
| 프로토콜 분석 | 프로토콜 규격 위반 탐지 | 프로토콜 악용 탐지 | 복잡 |
| 하이브리드 | 위 방식 조합 | 종합 탐지 | 리소스 사용 |

## 1.2 Suricata 아키텍처

```
네트워크 트래픽
     ↓
[패킷 캡처] — AF_PACKET / PCAP / NFQUEUE
     ↓
[패킷 디코더] — L2/L3/L4 헤더 파싱
     ↓
[스트림 재조합] — TCP 스트림 재구성
     ↓
[애플리케이션 디코더] — HTTP, DNS, TLS, SSH 등
     ↓
[탐지 엔진] — 시그니처 매칭 (멀티스레드)
     ↓
[출력] — fast.log, eve.json, pcap 저장
```

### Suricata 주요 설정 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| 메인 설정 | `/etc/suricata/suricata.yaml` | 전체 설정 |
| 룰 파일 | `/etc/suricata/rules/*.rules` | 탐지 룰 |
| fast.log | `/var/log/suricata/fast.log` | 간단한 경보 로그 |
| eve.json | `/var/log/suricata/eve.json` | JSON 상세 로그 |

## 1.3 Suricata 룰 문법

### 룰 구조

```
action protocol src_ip src_port -> dst_ip dst_port (options;)

예시:
alert tcp any any -> $HOME_NET 80 (msg:"SQL Injection 시도"; content:"UNION SELECT"; nocase; sid:1000001; rev:1;)
```

### 액션(Action)

| 액션 | 설명 | 모드 |
|------|------|------|
| `alert` | 경보 생성 | IDS/IPS |
| `pass` | 통과 허용 | IDS/IPS |
| `drop` | 패킷 차단 | IPS만 |
| `reject` | 차단 + RST/ICMP 응답 | IPS만 |
| `log` | 로그만 기록 | IDS/IPS |

### 주요 룰 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `msg` | 경보 메시지 | `msg:"포트 스캔 탐지";` |
| `content` | 페이로드 내용 매칭 | `content:"UNION SELECT";` |
| `nocase` | 대소문자 무시 | `nocase;` |
| `pcre` | 정규식 매칭 | `pcre:"/select.*from/i";` |
| `sid` | 시그니처 ID (고유) | `sid:1000001;` |
| `rev` | 룰 리비전 | `rev:1;` |
| `classtype` | 분류 유형 | `classtype:web-application-attack;` |
| `priority` | 우선순위 (1=높음) | `priority:1;` |
| `flow` | 트래픽 방향 | `flow:to_server,established;` |
| `threshold` | 임계값 | `threshold:type threshold,track by_src,count 10,seconds 60;` |
| `http_uri` | HTTP URI 매칭 | `http_uri; content:"/admin";` |
| `http_header` | HTTP 헤더 매칭 | `http_header; content:"User-Agent";` |

---

# Part 2: Suricata 룰 문법 상세 (30분)

## 2.1 콘텐츠 매칭 상세

```
# 단순 문자열 매칭
content:"UNION SELECT"; nocase;

# 16진수 매칭
content:"|0d 0a 0d 0a|";  # CRLF CRLF

# 오프셋/깊이
content:"GET"; offset:0; depth:3;  # 처음 3바이트에서만

# 거리/이내
content:"HTTP"; distance:0; within:10;  # 이전 매칭 후 10바이트 내

# 부정 매칭
content:!"normal"; # "normal" 포함하지 않는 경우
```

## 2.2 HTTP 키워드

```
# HTTP URI 매칭
alert http any any -> $HOME_NET any (
    msg:"SQLi in URI";
    flow:to_server,established;
    http_uri;
    content:"UNION"; nocase;
    content:"SELECT"; nocase;
    sid:1000010; rev:1;
)

# HTTP 메서드 매칭
alert http any any -> $HOME_NET any (
    msg:"HTTP PUT 시도";
    flow:to_server,established;
    http_method;
    content:"PUT";
    sid:1000011; rev:1;
)
```

## 2.3 임계값(Threshold)과 비율 기반 탐지

```
# 60초 내 동일 소스에서 10회 이상 → 1회만 경보
alert tcp any any -> $HOME_NET any (
    msg:"포트 스캔 탐지";
    flags:S;
    threshold:type threshold,track by_src,count 10,seconds 60;
    sid:1000020; rev:1;
)

# 30초 내 동일 소스에서 5회 이상 SSH 시도
alert tcp any any -> $HOME_NET 22 (
    msg:"SSH 브루트포스 시도";
    flow:to_server;
    threshold:type threshold,track by_src,count 5,seconds 30;
    sid:1000021; rev:1;
)
```

---

# Part 3: 포트 스캔/웹 공격 탐지 룰 실습 (40분)

## 실습 3.1: 포트 스캔 탐지 룰 작성

### Step 1: 커스텀 룰 파일 생성

> **실습 목적**: Suricata에 커스텀 탐지 룰을 작성하여 포트 스캔을 탐지한다.
>
> **배우는 것**: Suricata 룰 작성과 적용 방법

```bash
# secu 서버에 커스텀 룰 작성
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'RULES'
echo 1 | sudo -S bash -c 'cat > /etc/suricata/rules/custom.rules << "EOF"
# === 포트 스캔 탐지 ===
alert tcp any any -> $HOME_NET any (msg:"[CUSTOM] TCP SYN 스캔 탐지"; flags:S,12; threshold:type threshold,track by_src,count 20,seconds 10; classtype:attempted-recon; sid:9000001; rev:1;)

# === SSH 브루트포스 탐지 ===
alert tcp any any -> $HOME_NET 22 (msg:"[CUSTOM] SSH 브루트포스 시도"; flow:to_server; threshold:type threshold,track by_src,count 5,seconds 30; classtype:attempted-admin; sid:9000002; rev:1;)

# === SQL Injection 탐지 ===
alert http any any -> $HOME_NET any (msg:"[CUSTOM] SQL Injection - UNION SELECT"; flow:to_server,established; http_uri; content:"UNION"; nocase; content:"SELECT"; nocase; classtype:web-application-attack; sid:9000003; rev:1;)

alert http any any -> $HOME_NET any (msg:"[CUSTOM] SQL Injection - OR 1=1"; flow:to_server,established; http_uri; content:"OR"; nocase; content:"1=1"; classtype:web-application-attack; sid:9000004; rev:1;)

# === XSS 탐지 ===
alert http any any -> $HOME_NET any (msg:"[CUSTOM] XSS - script 태그"; flow:to_server,established; http_uri; content:"<script"; nocase; classtype:web-application-attack; sid:9000005; rev:1;)

alert http any any -> $HOME_NET any (msg:"[CUSTOM] XSS - onerror"; flow:to_server,established; http_uri; content:"onerror"; nocase; classtype:web-application-attack; sid:9000006; rev:1;)

# === ICMP 플러딩 탐지 ===
alert icmp any any -> $HOME_NET any (msg:"[CUSTOM] ICMP 플러딩"; threshold:type threshold,track by_src,count 50,seconds 10; classtype:attempted-dos; sid:9000007; rev:1;)
EOF
'
RULES

# 룰 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S cat /etc/suricata/rules/custom.rules 2>/dev/null"
```

> **결과 해석**:
> - `sid:9000001`: 커스텀 룰 ID (9000000번대 사용)
> - `flags:S,12`: SYN 플래그가 설정된 패킷 (포트 스캔 특징)
> - `threshold`: 임계값 기반으로 대량 시도만 탐지 (오탐 방지)
> - `http_uri`: HTTP URI에서만 매칭 (정확도 향상)

### Step 2: Suricata 재시작 및 룰 적용

> **실습 목적**: 작성한 룰을 Suricata에 적용하고 정상 동작을 확인한다.
>
> **배우는 것**: Suricata 룰 적용 프로세스

```bash
# suricata.yaml에 커스텀 룰 경로 추가 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S grep 'custom.rules' /etc/suricata/suricata.yaml 2>/dev/null"

# Suricata 룰 검증
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -5"
# 예상 출력: Configuration provided was successfully loaded.

# Suricata 재시작
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S systemctl restart suricata 2>/dev/null; echo 1 | sudo -S systemctl status suricata 2>/dev/null | head -5"
```

> **트러블슈팅**:
> - "Failed to parse rule": 룰 문법 오류 → sid, rev 등 필수 옵션 확인
> - "Suricata failed to start": suricata.yaml 설정 오류 → `-T` 옵션으로 검증

### Step 3: 공격 시뮬레이션 + 탐지 확인

> **실습 목적**: 실제 공격을 수행하고 Suricata가 탐지하는지 확인한다.
>
> **배우는 것**: IDS 경보 확인과 로그 분석

```bash
# 공격 1: 포트 스캔
echo 1 | sudo -S nmap -sS -p 1-100 10.20.30.1 2>/dev/null > /dev/null

# 공격 2: SQLi 시도 (web 서버 경유)
curl -s "http://10.20.30.80:3000/rest/products/search?q=UNION%20SELECT%201,2,3" > /dev/null

# 공격 3: XSS 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E" > /dev/null

# Suricata 경보 확인
sleep 3
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S tail -20 /var/log/suricata/fast.log 2>/dev/null"
# 예상 출력:
# [**] [1:9000001:1] [CUSTOM] TCP SYN 스캔 탐지 [**] ...
# [**] [1:9000003:1] [CUSTOM] SQL Injection - UNION SELECT [**] ...
# [**] [1:9000005:1] [CUSTOM] XSS - script 태그 [**] ...

# eve.json에서 상세 정보 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1   "echo 1 | sudo -S tail -5 /var/log/suricata/eve.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"
```

> **결과 해석**:
> - fast.log: 간단한 경보 (시간, SID, 메시지, 소스/목적지)
> - eve.json: JSON 형식의 상세 로그 (전체 패킷 정보)
> - 커스텀 룰이 정상 동작하면 [CUSTOM] 접두사가 있는 경보가 표시됨

---

# Part 4: 종합 IDS 모니터링 실습 (30분)

## 실습 4.1: 실시간 모니터링 시뮬레이션

### Step 1: OpsClaw 기반 IDS 모니터링

> **실습 목적**: OpsClaw를 활용하여 IDS 경보를 자동 수집하고 분석한다.
>
> **배우는 것**: IDS 모니터링 자동화

```bash
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week07-ids","request_text":"IDS/IPS 구축 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"Suricata 상태 확인","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S systemctl status suricata 2>/dev/null | head -5\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"최근 경보 확인","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S tail -10 /var/log/suricata/fast.log 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"커스텀 룰 수","instruction_prompt":"sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \"echo 1 | sudo -S wc -l /etc/suricata/rules/custom.rules 2>/dev/null\"","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:25s} → {t[\"status\"]}')
"
```

## 4.2 IDS 우회 기법 이해

| 기법 | 설명 | 방어 |
|------|------|------|
| 인코딩 우회 | URL/유니코드 인코딩 | 디코딩 후 매칭 |
| 패킷 단편화 | IP 패킷 분할 | 스트림 재조합 |
| 대소문자 변환 | `UnIoN SeLeCt` | nocase 옵션 |
| 주석 삽입 | `UNI/**/ON SEL/**/ECT` | 정규식 매칭 |
| 느린 스캔 | 시간 기반 임계값 회피 | 장기 기록 분석 |
| 암호화 | HTTPS로 페이로드 은닉 | SSL/TLS 복호화 |

---

## 검증 체크리스트
- [ ] IDS와 IPS의 차이를 설명할 수 있는가
- [ ] Suricata 룰 문법(action, protocol, options)을 이해했는가
- [ ] 포트 스캔 탐지 룰을 작성하고 테스트했는가
- [ ] SQL Injection/XSS 탐지 룰을 작성하고 테스트했는가
- [ ] SSH 브루트포스 탐지 룰을 작성했는가
- [ ] fast.log과 eve.json을 분석할 수 있는가
- [ ] OpsClaw를 통해 IDS 모니터링을 자동화했는가
- [ ] IDS 우회 기법을 이해했는가

## 자가 점검 퀴즈

1. IDS와 IPS의 배치 위치(인라인 vs 미러 포트)와 각각의 장단점을 설명하라.

2. Suricata 룰에서 `flow:to_server,established`의 의미를 설명하라.

3. `threshold:type threshold,track by_src,count 10,seconds 60`의 동작을 설명하라.

4. HTTP URI에서 SQL Injection을 탐지하는 Suricata 룰을 작성하라.

5. `content` 매칭에서 `offset`, `depth`, `distance`, `within`의 차이를 설명하라.

6. eve.json 로그에서 특정 SID의 경보만 필터링하는 명령어를 작성하라.

7. Suricata를 IPS 모드로 운영할 때의 위험과 주의사항을 설명하라.

8. 공격자가 IDS를 우회하기 위해 인코딩을 사용할 때, 이를 탐지하는 방법을 설명하라.

9. 시그니처 기반 탐지의 한계와 이를 보완하는 방법을 설명하라.

10. 공방전에서 Blue Team이 Suricata로 탐지해야 할 공격 유형 5가지와 각각의 룰을 설명하라.

## 과제

### 과제 1: 커스텀 IDS 룰셋 작성 (필수)
- Week 01-05에서 수행한 공격(포트 스캔, SQLi, XSS, 브루트포스, 권한 상승)을 탐지하는 룰 작성
- 각 룰의 탐지 원리와 테스트 결과를 문서화

### 과제 2: IDS 로그 분석 (선택)
- Suricata eve.json 로그를 분석하여 공격 타임라인 구성
- 공격 유형별 통계를 산출하고 시각화

### 과제 3: IDS 우회 실험 (도전)
- 작성한 IDS 룰을 우회하는 페이로드 개발
- 우회에 성공한 경우 룰을 개선하여 재탐지
