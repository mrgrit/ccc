# Week 05 — Suricata IDS (2) — 룰 작성 심화

> W04 에서 단순 content 기반 alert 룰을 작성했다면, 본 주차는 운영 환경에서 false
> positive 를 줄이고 정확도를 높이는 **고급 룰 기술 5종** 을 다룬다: pcre (정규식) /
> fast_pattern / flowbits (상태) / threshold (rate limit) / suppression (운영 튜닝).

## 학습 목표

1. pcre 정규식으로 복잡한 페이로드 매칭 룰 작성
2. fast_pattern 으로 매칭 성능 최적화
3. flowbits 로 conn 의 단계별 상태 추적 (다단계 공격 매칭)
4. threshold.config 로 룰별 rate-limit 설정 (alert flood 방지)
5. suppression 으로 특정 src/dst 의 룰을 임시 비활성화
6. 작성 → 검증 (-T) → reload → 트리거 → eve.json 분석 사이클

## 강의 시간 배분 (3시간 40분)

| 시간      | 내용 | 유형 |
|-----------|------|------|
| 0:00–0:25 | 룰 분석 — sid 매핑, content 의 modifier (nocase / depth / offset) | 강의 |
| 0:25–0:55 | pcre 정규식 + fast_pattern + content/pcre combination | 강의 |
| 0:55–1:05 | 휴식 | — |
| 1:05–1:30 | flowbits + threshold + suppression | 강의/토론 |
| 1:30–2:00 | 실습 1, 2 — pcre 정규식 룰 + nocase / depth | 실습 |
| 2:00–2:30 | 실습 3, 4 — flowbits 다단계 + fast_pattern | 실습 |
| 2:30–2:40 | 휴식 | — |
| 2:40–3:10 | 실습 5, 6 — threshold + suppression | 실습 |
| 3:10–3:30 | 실습 7 — 종합 룰셋 (5 기술 결합) | 실습 |
| 3:30–3:40 | 정리 + W06 (ModSecurity WAF) 예고 | 정리 |

---

## 1. 룰 구조 심층 분석

### 1.1 룰 한 줄의 구조

```
alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (
    msg:"6v6 SSH brute force pattern";
    content:"SSH-";
    depth:5;
    nocase;
    flow:to_server,established;
    threshold:type both,track by_src,count 5,seconds 60;
    classtype:attempted-recon;
    sid:9000010;
    rev:2;
    metadata:created_at 2026_05_11;
)
```

10개 키 분석:
- `alert` : 액션 (alert/drop/reject/pass)
- `tcp` : 프로토콜
- `$EXTERNAL_NET any -> $HOME_NET 22` : 5-tuple (sport=any, dport=22)
- `msg` : 사람이 읽는 이름
- `content` : 페이로드 매칭 패턴
- `depth:5` : 페이로드 첫 5 byte 안에서만 검사
- `nocase` : 대소문자 무관
- `flow:to_server,established` : 방향 + state
- `threshold` : rate limit
- `sid` + `rev` : 식별자 + 버전

### 1.2 content modifier 5종

| modifier | 의미 | 예 |
|----------|------|-----|
| `nocase` | 대소문자 무관 | `content:"select"; nocase;` |
| `depth:N` | 처음 N byte 안에서만 검사 | `content:"GET "; depth:4;` |
| `offset:N` | 시작 N byte skip | `content:"HTTP/1.1"; offset:2;` |
| `distance:N` | 이전 content 이후 N byte 떨어진 곳 | `content:"user="; content:"pass="; distance:0;` |
| `within:N` | 이전 content 이후 N byte 이내 | `content:"GET "; content:"/admin"; within:50;` |

### 1.3 buffer keyword (HTTP)

```
http.uri              # URL path (예: /admin)
http.method           # GET / POST / PUT ...
http.user_agent       # User-Agent header
http.host             # Host header
http.cookie           # Cookie header
http.request_body     # POST body
http.response_body    # response HTML
http.stat_code        # 응답 코드 (200 / 403 ...)
http.header           # 모든 header (raw)
```

예시:
```
alert http any any -> any any (
    msg:"SQLi pattern in POST body";
    http.request_body; content:"' OR '1'='1";
    nocase;
    sid:9000011;
)
```

---

## 2. pcre — Perl-Compatible 정규식

content 만으로 표현 불가능한 패턴은 pcre 로.

### 2.1 syntax

```
pcre:"/<regex>/<modifier>"
```

modifier: `i` (nocase) / `s` (newline match) / `R` (relative) / `U` (URI) / `H` (header)

### 2.2 예시

```
# 16자 신용카드번호 패턴
pcre:"/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}/"

# email 패턴
pcre:"/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/"

# SQL UNION 패턴
pcre:"/\bunion\b\s+\bselect\b/i"

# 한국 주민번호 패턴
pcre:"/\d{6}-[1-4]\d{6}/"
```

### 2.3 content + pcre 결합 패턴 (성능)

pcre 만 쓰면 모든 packet 에 정규식 평가 → 느림. content 로 prefilter 후 pcre 로 정밀.

```
alert http any any -> any any (
    msg:"UNION SELECT injection";
    http.uri;
    content:"union";                  ← prefilter (fast_pattern 자동)
    nocase;
    pcre:"/\bunion\b\s+\bselect\b/i"; ← 정밀 매치
    sid:9000012;
)
```

---

## 3. fast_pattern — 매칭 성능 최적화

Suricata 의 multi-pattern matcher (hyperscan) 는 룰의 **여러 content 중 1개를
fast_pattern 으로 선택** 하여 prefilter. 자동 선택은 가장 긴 content 가 우선이지만,
명시적으로 지정 가능.

```
alert http any any -> any any (
    msg:"sqlmap UA";
    http.user_agent;
    content:"sqlmap"; fast_pattern;       ← 명시
    content:"/1.0";
    sid:9000013;
)
```

production 운영 시 모든 룰에 fast_pattern 을 명시하면 cache hit rate 향상. ETOpen 룰 대부분이
이미 적용.

---

## 4. flowbits — 다단계 공격 추적

한 conn 에서 여러 단계 (예: login 시도 → 성공 후 admin 접근) 를 추적하려면 flowbits 변수
사용.

### 4.1 set / isset / unset

```
# 단계 1: login 실패 시 fp1 flag set
alert http any any -> any any (
    msg:"step1 login fail";
    http.uri; content:"/login";
    http.stat_code; content:"401";
    flowbits:set,login_failed;
    flowbits:noalert;          ← 이 룰 자체로는 alert 없음, 상태만 set
    sid:9000020;
)

# 단계 2: login 실패 후 같은 conn 에서 admin 접근
alert http any any -> any any (
    msg:"step2 unauth admin access after failed login";
    http.uri; content:"/admin";
    flowbits:isset,login_failed;  ← step1 flag 가 켜진 경우만
    sid:9000021;
)
```

이로써 단순 패턴 매칭으론 잡기 힘든 multi-step 공격 시나리오 룰화.

---

## 5. threshold — rate limit

같은 alert 가 1초에 1000번 발생하면 SOC 분석가가 멘붕. threshold 로 제한.

### 5.1 룰 내부 threshold

```
alert tcp any any -> any 22 (
    msg:"SSH brute force";
    flow:to_server,established;
    threshold:type both, track by_src, count 5, seconds 60;
    sid:9000030;
)
```

- `type both` : 5번에 도달했을 때 1번만 alert (rate-limit) — `limit` / `threshold` / `both` 3 mode
- `track by_src` : 같은 src IP 기준 (by_dst / by_rule 도 가능)
- `count 5, seconds 60` : 60초에 5번

### 5.2 threshold.config (전역 설정)

```
# /etc/suricata/threshold.config
suppress gen_id 1, sig_id 2003020                  # 특정 룰 완전 비활성
suppress gen_id 1, sig_id 2003020, track by_src, ip 10.20.30.99   # 특정 src 만 비활성
event_filter gen_id 1, sig_id 2010001, type rate_filter, track by_src, count 10, seconds 60   # rate-limit
```

룰을 수정하지 않고 운영 환경에서 동적 튜닝.

---

## 6. suppression — 운영 튜닝

threshold.config 의 `suppress` 가 곧 suppression. false-positive 룰의 영향 차단.

### 6.1 시나리오: 모니터링 시스템이 알려진 패턴 트래픽 발생 → 매번 alert

```
# /etc/suricata/threshold.config
# 운영 모니터링 서버 (10.20.32.50 = portal) 의 health check 가 ET POLICY 룰 매치 →
# 운영자가 false-positive 로 판단 → suppress
suppress gen_id 1, sig_id 2010001, track by_src, ip 10.20.32.50
```

reload 후 portal IP 에서 발생하는 sid 2010001 alert 만 차단. 다른 src 는 정상 alert.

---

## 7. 룰 검증 명령

```
# syntax 검증
sudo suricata -T -S /etc/suricata/rules/local.rules

# 룰 로드 통계
sudo suricatasc -c ruleset-stats

# reload (재시작 없음)
sudo suricatasc -c reload-rules

# 트리거 + alert 확인
ssh 6v6-attacker 'curl -A "sqlmap/1.5" http://...'
sleep 3
sudo grep sid.:9000XX /var/log/suricata/eve.json | jq
```

---

## 8. 용어 해설

| 용어 | 설명 |
|------|------|
| **pcre** | Perl Compatible Regex |
| **fast_pattern** | multi-pattern matcher 의 prefilter 패턴 (성능) |
| **hyperscan** | Intel 의 SIMD 기반 multi-pattern matcher (Suricata default) |
| **flowbits** | conn 의 boolean flag (다단계 추적) |
| **flow** | conn 의 방향 + state (to_server / to_client / established / stateless) |
| **threshold** | 룰의 rate-limit (count / seconds / track) |
| **suppression** | 특정 src/dst/룰의 alert 차단 |
| **classtype** | 룰의 클래스 (`attempted-recon`, `web-application-attack` 등 — classification.config) |
| **metadata** | 룰의 부가 정보 (created_at, mitre tactic 등) |

---

## 9. 실습 시나리오 1~7

각 실습은 룰 작성 → -T 검증 → reload → 트리거 → eve.json 확인 사이클.

### 실습 1 — pcre 정규식 룰 (한국 주민번호 패턴)

```
alert http any any -> any any (
    msg:"6v6 RRN pattern in POST body";
    http.request_body;
    pcre:"/\d{6}-[1-4]\d{6}/";
    classtype:policy-violation;
    sid:9000040;
)
```

트리거: attacker 가 POST body 에 가짜 주민번호 (예: 901231-1234567) 포함하여 요청.

### 실습 2 — http.uri + nocase + depth

```
alert http any any -> any any (
    msg:"admin path access";
    http.uri;
    content:"/admin"; depth:6; nocase;
    sid:9000041;
)
```

### 실습 3 — flowbits 다단계

(위 4.1 의 step1 + step2 룰)

### 실습 4 — fast_pattern 명시

```
alert http any any -> any any (
    msg:"sqlmap UA";
    http.user_agent;
    content:"sqlmap"; fast_pattern; nocase;
    sid:9000042;
)
```

### 실습 5 — threshold rate limit

```
alert tcp any any -> any 22 (
    msg:"SSH probe (rate-limited)";
    flow:to_server;
    threshold:type both, track by_src, count 5, seconds 30;
    sid:9000050;
)
```

attacker 에서 30초에 6번 SSH 시도 → 1 alert 만.

### 실습 6 — suppression

`/etc/suricata/threshold.config` 에:

```
suppress gen_id 1, sig_id 9000041, track by_src, ip 10.20.30.202
```

attacker (10.20.30.202) 에서는 sid 9000041 alert 발생 안 함. 다른 src 는 발생.

### 실습 7 — 종합 룰셋

5 기술 결합 1개 룰:

```
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"6v6 sqlmap SQLi attempt (rate-limited)";
    flow:to_server,established;
    http.user_agent; content:"sqlmap"; fast_pattern; nocase;
    http.request_body; pcre:"/\bunion\b\s+\bselect\b/i";
    threshold:type limit, track by_src, count 1, seconds 60;
    classtype:web-application-attack;
    sid:9000099; rev:1;
    metadata:created_at 2026_05_11, mitre_tactic_id TA0001;
)
```

---

## 10. 과제

### A. 4 룰 작성 (필수) — 각 룰의 sid + 트리거 + eve.json 결과

1. SQL UNION SELECT (pcre)
2. /admin 접근 (http.uri + nocase + depth)
3. 다단계: 401 응답 후 /admin 접근 (flowbits)
4. SSH 30초 5회 시도 (threshold)

### B. false-positive 분석 (심화)

ETOpen 룰셋에서 본 lab 환경에서 false-positive 가 잦은 룰 1개를 찾아 suppression
설정 + 정당화 근거.

### C. 룰 작성 가이드 정리 (정성)

본인 만의 룰 작성 5 원칙 한글 작성 (예: "fast_pattern 은 항상 명시", "sid 는 9M+
범위 사용" 등).

---

## 11. W06 (ModSecurity WAF) 예고

다음 주차는 6v6-web 의 Apache + ModSecurity v2 + OWASP CRS. L7 HTTP 검사. Suricata 의
http event 와 어떻게 다른지 (in-line vs sniff), CRS 룰셋의 paranoia level 등 핵심 학습.
