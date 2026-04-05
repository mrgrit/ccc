# Week 05: Suricata IPS (2) — 룰 작성

## 학습 목표
- Suricata 룰의 전체 문법 구조를 이해한다
- alert/drop/reject 액션의 차이를 구분한다
- content, flow, pcre 등 핵심 키워드를 사용할 수 있다
- 커스텀 룰을 작성하고 테스트할 수 있다

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

# Week 05: Suricata IPS (2) — 룰 작성

## 학습 목표

- Suricata 룰의 전체 문법 구조를 이해한다
- alert/drop/reject 액션의 차이를 구분한다
- content, flow, pcre 등 핵심 키워드를 사용할 수 있다
- 커스텀 룰을 작성하고 테스트할 수 있다

---

## 1. 룰 문법 개요

Suricata 룰은 한 줄로 구성되며, **Header**와 **Options**로 나뉜다:

```
action protocol src_ip src_port -> dst_ip dst_port (options;)
```

**예시:**
```
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"Malware download"; content:"malware.exe"; sid:1000001; rev:1;)
```

| 부분 | 예시 값 | 설명 |
|------|---------|------|
| action | `alert` | 동작 (alert/drop/reject/pass) |
| protocol | `http` | 프로토콜 |
| src_ip | `$HOME_NET` | 출발지 IP |
| src_port | `any` | 출발지 포트 |
| direction | `->` | 방향 (-> 또는 <>) |
| dst_ip | `$EXTERNAL_NET` | 목적지 IP |
| dst_port | `any` | 목적지 포트 |
| options | `(msg:...; sid:...; )` | 탐지 조건과 메타데이터 |

---

## 2. Action (동작)

> **이 실습을 왜 하는가?**
> "Suricata IPS (2) — 룰 작성" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

| Action | 설명 | IDS | IPS |
|--------|------|-----|-----|
| `alert` | 로그 기록 (경고) | O | O |
| `drop` | 패킷 차단 + 로그 | X | O |
| `reject` | RST/ICMP unreachable + 로그 | X | O |
| `pass` | 허용 (이후 룰 무시) | O | O |

> **IDS 모드**에서는 drop/reject가 alert처럼 동작한다 (차단 불가).

---

## 3. Protocol (프로토콜)

Suricata가 지원하는 프로토콜:

| 프로토콜 | 설명 |
|----------|------|
| `tcp` | TCP |
| `udp` | UDP |
| `icmp` | ICMP |
| `ip` | 모든 IP |
| `http` | HTTP (L7 파싱) |
| `tls` | TLS/SSL |
| `dns` | DNS |
| `ssh` | SSH |
| `ftp` | FTP |
| `smtp` | SMTP |

> `http`를 사용하면 Suricata가 HTTP를 파싱하여 URI, header 등을 개별 검사할 수 있다.

---

## 4. 실습 환경 접속

> **실습 목적**: secu 서버에서 Suricata 커스텀 탐지 룰을 직접 작성하고 테스트한다
>
> **배우는 것**: Suricata 룰 문법(action, protocol, src/dst, options)을 이해하고, 특정 공격 패턴을 탐지하는 룰을 작성한다
>
> **결과 해석**: 공격 트래픽 발생 후 fast.log에 해당 룰의 알림이 기록되면 룰이 정상 동작하는 것이다
>
> **실전 활용**: 제로데이 공격이나 조직 특화 위협에 대응하기 위해 커스텀 IPS 룰을 작성한다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
```

룰 파일 위치 확인:

```bash
echo 1 | sudo -S cat /etc/suricata/rules/local.rules 2>/dev/null
```

---

## 5. 핵심 옵션 키워드

### 5.1 msg (메시지)

알림에 표시되는 설명:

```
msg:"SQL Injection attempt detected";
```

### 5.2 sid / rev (고유 ID / 리비전)

모든 룰에 필수. sid는 고유해야 한다:

```
sid:9000001; rev:1;
```

| sid 범위 | 용도 |
|----------|------|
| 1~999999 | Snort/ET 공식 룰 |
| 1000000~1999999 | ET Open |
| **9000000~** | **커스텀 룰 (실습용)** |

### 5.3 content (내용 매칭)

패킷 페이로드에서 문자열을 검색:

```
content:"admin"; nocase;          # 대소문자 무시
content:"|0d 0a|";                # 16진수 매칭
content:"GET"; offset:0; depth:3; # 처음 3바이트에서만 검색
```

**content 수정자:**

| 수정자 | 설명 |
|--------|------|
| `nocase` | 대소문자 무시 |
| `offset` | 검색 시작 위치 |
| `depth` | 검색 깊이 (offset부터) |
| `distance` | 이전 content 매칭 이후 거리 |
| `within` | distance 이후 검색 범위 |

### 5.4 flow (흐름)

연결 방향과 상태를 지정:

```
flow:to_server,established;   # 클라이언트 → 서버, 연결 수립됨
flow:to_client,established;   # 서버 → 클라이언트
flow:established;              # 양방향 수립된 연결
```

### 5.5 http 키워드

HTTP 프로토콜 파싱 활용:

```
http.method;          # GET, POST 등
http.uri;             # 요청 URI
http.host;            # Host 헤더
http.user_agent;      # User-Agent 헤더
http.request_body;    # POST 본문
http.stat_code;       # 응답 상태 코드
http.response_body;   # 응답 본문
```

### 5.6 pcre (정규표현식)

```
pcre:"/admin.*password/i";    # 정규식 매칭 (i: 대소문자 무시)
```

### 5.7 threshold (임계값)

```
threshold:type threshold, track by_src, count 10, seconds 60;
# 같은 출발지에서 60초 내 10회 이상 매칭 시 알림
```

### 5.8 classtype / priority

```
classtype:web-application-attack;
priority:1;    # 1(높음) ~ 4(낮음)
```

---

## 6. 커스텀 룰 작성 실습

> **이 실습의 목적:**
> Suricata의 기본 ET 룰셋(65,000+)은 범용적이다. 우리 환경에 특화된 위협을 탐지하려면
> **커스텀 룰을 직접 작성**해야 한다. 이 실습에서 5개의 대표적 공격 유형에 대한 룰을 작성하며,
> 각 룰의 옵션이 왜 그렇게 설정되는지를 이해한다.
>
> **실무 활용:** SOC에서 새로운 위협이 보고되면 분석가가 커스텀 룰을 작성하여 배포한다.
> 예: "특정 C2 서버 IP에서 오는 트래픽 탐지" → 긴급 룰 추가 → Suricata 리로드

### 6.1 룰 1: SQL Injection 탐지

> **왜 이 룰이 필요한가?**
> UNION SELECT는 SQL Injection에서 다른 테이블의 데이터를 추출하는 핵심 기법이다.
> HTTP URI에서 "union"과 "select"가 가까이 나타나면 SQLi 시도로 판단한다.
>
> **룰 해석:**
> - `http.uri`: HTTP 요청의 URI 부분만 검사 (본문 제외)
> - `content:"union"; nocase;`: 대소문자 무시하고 "union" 검색
> - `distance:0;`: 이전 매칭("union") 바로 다음부터 "select" 검색
> - `classtype:web-application-attack`: 공격 분류
> - `sid:9000010`: 커스텀 룰 범위(9000000+)의 고유 ID

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - SQL Injection in URI (union select)"; flow:to_server,established; http.uri; content:"union"; nocase; content:"select"; nocase; distance:0; classtype:web-application-attack; sid:9000010; rev:1;)
EOF
```

### 6.2 룰 2: XSS 탐지

> **왜 이 룰이 필요한가?**
> `<script` 태그가 HTTP 요청에 포함되면 XSS(Cross-Site Scripting) 시도로 판단한다.
> 공격자는 검색창이나 URL 파라미터에 스크립트를 삽입하여 다른 사용자의 브라우저에서 실행시킨다.
>
> **한계:** `<script>` 외에도 `<img onerror=`, `javascript:` 등 다양한 XSS 벡터가 있으므로,
> 실무에서는 여러 개의 룰을 조합해야 한다.

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - XSS attempt (script tag)"; flow:to_server,established; http.uri; content:"<script"; nocase; classtype:web-application-attack; sid:9000011; rev:1;)
EOF
```

### 6.3 룰 3: 디렉터리 트래버설 탐지

> **왜 이 룰이 필요한가?**
> `../`는 디렉터리 트래버설(경로 탐색) 공격의 핵심 패턴이다.
> 공격자가 `../../etc/passwd`를 URI에 넣어 서버의 시스템 파일을 읽으려 시도한다.
>
> **오탐 가능성:** 일부 정상 URL에도 `../`가 포함될 수 있다.
> 실무에서는 `../../../`(3단계 이상)으로 조건을 강화하거나, 특정 경로(/etc/, /proc/)와 조합한다.

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - Directory Traversal attempt"; flow:to_server,established; http.uri; content:"../"; classtype:web-application-attack; sid:9000012; rev:1;)
EOF
```

### 6.4 룰 4: SSH 브루트포스 탐지

> **왜 이 룰이 필요한가?**
> SSH 브루트포스는 가장 흔한 네트워크 공격이다. 같은 IP에서 짧은 시간에 여러 번
> SSH 연결을 시도하면 비밀번호 추측 공격으로 판단한다.
>
> **룰 해석:**
> - `tcp ... -> $HOME_NET 22`: SSH 포트(22)로 향하는 TCP 트래픽
> - `flags:S`: SYN 패킷만 카운트 (연결 시도)
> - `threshold:type threshold, track by_src, count 5, seconds 60`:
>   **동일 소스 IP에서 60초 내 5회 이상** SYN 패킷이 오면 경보
>
> **조정 팁:** count를 낮추면 오탐이 증가하고, 높이면 느린 브루트포스를 놓칠 수 있다.
> 실무에서는 5~10회/분이 일반적이다.

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert tcp any any -> $HOME_NET 22 (msg:"CUSTOM - SSH brute force attempt"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 5, seconds 60; classtype:attempted-admin; sid:9000013; rev:1;)
EOF
```

### 6.5 룰 5: 차단 룰 (IPS용, drop)

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
drop http any any -> $HOME_NET any (msg:"CUSTOM - Block /etc/passwd access"; flow:to_server,established; http.uri; content:"/etc/passwd"; classtype:web-application-attack; sid:9000014; rev:1;)
EOF
```

### 6.6 작성한 룰 확인

```bash
echo 1 | sudo -S cat /etc/suricata/rules/local.rules
```

---

## 7. 룰 검증과 리로드

### 7.1 설정 검증

```bash
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml
```

오류가 있으면 해당 룰의 문법을 수정한다.

### 7.2 룰 리로드 (재시작 없이)

```bash
echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

### 7.3 리로드 확인

```bash
echo 1 | sudo -S tail -5 /var/log/suricata/suricata.log
```

**예상 출력:**
```
<Notice> - rule reload starting
<Notice> - rule reload complete
```

---

## 8. 룰 테스트

### 8.1 SQL Injection 테스트

```bash
# web 서버(JuiceShop)에 SQL Injection 패턴 요청
curl -s "http://10.20.30.80/?q=1%20union%20select%201,2,3" > /dev/null

# 알림 확인
echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

**예상 출력:**
```
03/27/2026-11:00:01.123  [**] [1:9000010:1] CUSTOM - SQL Injection in URI (union select) [**] ...
```

### 8.2 XSS 테스트

```bash
curl -s "http://10.20.30.80/?q=%3Cscript%3Ealert(1)%3C/script%3E" > /dev/null  # silent 모드

echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

### 8.3 디렉터리 트래버설 테스트

```bash
curl -s "http://10.20.30.80/../../etc/passwd" > /dev/null  # silent 모드

echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

### 8.4 eve.json으로 상세 확인

```bash
# 마지막 alert 이벤트 상세 보기
echo 1 | sudo -S tail -20 /var/log/suricata/eve.json | \
  python3 -m json.tool | grep -A 5 '"alert"'           # Python 스크립트 실행
```

---

## 9. 룰 작성 팁

### 9.1 방향 연산자

```
->    출발지에서 목적지 방향만
<>    양방향 (요청과 응답 모두)
```

### 9.2 변수 활용

```
$HOME_NET        내부 네트워크
$EXTERNAL_NET    외부 네트워크
$HTTP_SERVERS    웹 서버
$HTTP_PORTS      웹 포트
```

### 9.3 여러 content 조합

AND 조건으로 동작한다 (모든 content가 매칭되어야 알림 발생):

```
alert http any any -> any any (
  msg:"Multi content match";
  content:"admin"; nocase;
  content:"password"; nocase; distance:0;
  sid:9000020; rev:1;
)
```

### 9.4 부정(NOT) 매칭

```
content:!"safe_string";    # "safe_string"이 없을 때 매칭
```

### 9.5 flowbits (상태 추적)

```
# 첫 번째 룰: 로그인 페이지 접근 감지
alert http any any -> any any (msg:"Login page"; content:"/login"; http.uri; flowbits:set,login_attempt; sid:9000030; rev:1;)

# 두 번째 룰: 로그인 후 admin 접근
alert http any any -> any any (msg:"Admin after login"; content:"/admin"; http.uri; flowbits:isset,login_attempt; sid:9000031; rev:1;)
```

---

## 10. 실습 과제

### 과제 1: 탐지 룰 작성

다음 공격을 탐지하는 룰을 `/etc/suricata/rules/local.rules`에 추가하라:

1. HTTP 요청에서 `cmd=` 파라미터 탐지 (명령 주입)
2. User-Agent에 `nikto`가 포함된 요청 탐지 (스캐너)
3. HTTP 응답에서 `root:x:0:0` 탐지 (passwd 유출)

**힌트:**
```
# 1번
alert http ... (msg:"Command Injection"; http.uri; content:"cmd="; sid:9000040; rev:1;)

# 2번
alert http ... (msg:"Nikto Scanner"; http.user_agent; content:"nikto"; nocase; sid:9000041; rev:1;)

# 3번
alert http ... (msg:"Passwd Leak"; flow:to_client,established; http.response_body; content:"root:x:0:0"; sid:9000042; rev:1;)
```

### 과제 2: 차단 룰 작성

다음을 **차단(drop)**하는 룰을 작성하라:

1. URI에 `wp-admin`이 포함된 요청 (WordPress 관리자 페이지 차단)
2. `.php.bak` 파일 요청 차단

### 과제 3: 테스트

작성한 룰을 검증(`suricata -T`)하고, curl로 테스트 트래픽을 발생시켜 동작을 확인하라.

### 정리

```bash
# 실습 룰 정리 (원하는 룰만 남기기)
echo 1 | sudo -S cp /etc/suricata/rules/local.rules /tmp/local.rules.bak
```

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| alert/drop/reject/pass | 룰 동작 (IPS에서 drop 가능) |
| content | 페이로드 문자열 매칭 |
| nocase | 대소문자 무시 |
| flow | 연결 방향/상태 지정 |
| http.uri | HTTP URI 전용 매칭 |
| pcre | 정규표현식 매칭 |
| threshold | 임계값 기반 알림 |
| flowbits | 상태 추적 (다단계 탐지) |
| sid | 룰 고유 ID (커스텀은 9000000+) |
| `kill -USR2` | 재시작 없이 룰 리로드 |

---

## 다음 주 예고

Week 06에서는 Suricata 운영을 다룬다:
- eve.json/fast.log 분석
- 성능 튜닝
- 오탐(False Positive) 관리

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
