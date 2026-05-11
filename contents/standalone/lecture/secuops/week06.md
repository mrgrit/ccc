# Week 06 — Apache + ModSecurity v2 + OWASP CRS (WAF)

> 본 주차는 **6v6-web** 컨테이너의 **Apache 2.4 + mod_security2 + OWASP Core Rule Set
> (CRS)** 가 학습 대상. fw / ips 의 L3-L4 통제 (W02-05) 가 IP/port + 페이로드 시그니처
> 매칭에 집중했다면, ModSecurity 는 HTTP application 계층 (L7) 에 특화된 검사.

## 학습 목표

1. ModSecurity v2 vs v3 + Apache vs Nginx backend 차이 이해
2. SecRuleEngine 의 3 모드 (On / DetectionOnly / Off) 차이
3. OWASP CRS 의 paranoia level (1~4) + inbound/outbound anomaly threshold
4. modsec_audit.log JSON 형식 파싱 + 룰별 매칭 분석
5. false-positive 가 잦은 CRS 룰의 exception 작성 (`SecRuleRemoveById`,
   `SecRuleUpdateTargetById`)
6. ModSec audit log → Wazuh agent → manager 통합 흐름 (W10 예고)

## 강의 시간 배분

| 시간 | 내용 |
|------|------|
| 0:00–0:30 | 이론 — WAF 의 자리 / Apache vs Nginx + ModSec v2 vs v3 |
| 0:30–1:00 | 이론 — OWASP CRS 구조 (REQUEST-9xx / RESPONSE-9xx) |
| 1:00–1:10 | 휴식 |
| 1:10–1:30 | 6v6-web 의 실제 구성 (Apache + ModSec + 11 vhost reverse proxy) |
| 1:30–2:00 | 실습 1, 2 — 설정 파일 + audit log 형식 |
| 2:00–2:30 | 실습 3, 4 — 공격 시뮬레이션 (XSS / SQLi / LFI) + 차단 검증 |
| 2:30–2:40 | 휴식 |
| 2:40–3:10 | 실습 5, 6 — CRS paranoia 튜닝 + 룰 exception |
| 3:10–3:30 | 실습 7 — 종합 audit log 분석 |
| 3:30–3:40 | 정리 + W07 (osquery 호스트 가시화) 예고 |

---

## 1. WAF 의 자리

WAF (Web Application Firewall) 는 HTTP/HTTPS 요청·응답에 특화된 방어 도구. 다음 5
시나리오에서 다른 도구로 잡을 수 없는 공격을 잡는다.

| 공격 | 잡는 도구 |
|------|-----------|
| TCP SYN flood | nftables (fw) |
| 포트 스캔 | Suricata (ips) + nftables |
| SQL Injection | **ModSecurity** + Suricata HTTP decoder |
| Stored XSS | **ModSecurity** + browser CSP |
| Command Injection | **ModSecurity** + 서비스 측 검증 |
| HTTP request smuggling | **ModSecurity** + HAProxy strict mode |
| L7 DoS (slowloris) | **ModSecurity** + mod_reqtimeout |

ModSec 의 강점은 **payload context aware** — content-type 별 다른 디코딩 (form-encoded
/ JSON / multipart) + parameter 별 분리 검사 + transaction state 유지.

---

## 2. ModSec v2 vs v3

| 항목 | v2 | v3 |
|------|----|----|
| 출시 | 2002 (Apache 모듈) | 2017 (libmodsecurity 라이브러리) |
| backend | Apache 전용 | Apache / Nginx / IIS |
| 표준화 | mod_security2 패키지 | libmodsecurity + connector |
| OWASP CRS | v3.x 호환 | v4.x 호환 |
| 성능 | Apache 의 process per request | Nginx 의 event-driven |
| 6v6 사용 | ✓ (Ubuntu 22.04 패키지) | × |

6v6 는 Apache 2.4 + mod_security2 (v2.9.x) 조합. 운영 환경에서 Nginx 기반이라면 v3 +
libmodsecurity 권장.

---

## 3. OWASP CRS 구조

CRS 는 OWASP 의 공식 ruleset (오픈소스, 무료). 6v6 의 `/usr/share/modsecurity-crs/rules/`
에 30+ 파일.

### 3.1 파일 명명

```
REQUEST-901-INITIALIZATION.conf       ← 변수 초기화
REQUEST-905-COMMON-EXCEPTIONS.conf    ← 공통 예외 (브라우저 정상 헤더 등)
REQUEST-910-IP-REPUTATION.conf        ← IP 평판
REQUEST-911-METHOD-ENFORCEMENT.conf   ← 허용 method (GET/POST/...)
REQUEST-913-SCANNER-DETECTION.conf    ← 스캐너 (nmap, sqlmap 등)
REQUEST-920-PROTOCOL-ENFORCEMENT.conf ← HTTP 프로토콜 위반
REQUEST-921-PROTOCOL-ATTACK.conf      ← HTTP smuggling / request splitting
REQUEST-930-APPLICATION-ATTACK-LFI.conf  ← Local File Inclusion
REQUEST-931-APPLICATION-ATTACK-RFI.conf  ← Remote File Inclusion
REQUEST-932-APPLICATION-ATTACK-RCE.conf  ← Remote Code Execution
REQUEST-933-APPLICATION-ATTACK-PHP.conf  ← PHP 특화
REQUEST-934-APPLICATION-ATTACK-NODEJS.conf
REQUEST-941-APPLICATION-ATTACK-XSS.conf  ← Cross-Site Scripting
REQUEST-942-APPLICATION-ATTACK-SQLI.conf ← SQL Injection
REQUEST-943-APPLICATION-ATTACK-SESSION-FIXATION.conf
RESPONSE-950-DATA-LEAKAGES.conf        ← 응답에 sensitive data 노출
RESPONSE-951-DATA-LEAKAGES-SQL.conf    ← SQL 에러 메시지 노출
...
```

번호 prefix:
- `9xx` : 핵심 카테고리
- `94x` : application attack (XSS=941, SQLi=942 등)
- `95x` : response (data leakage)
- `99x` : finalization (anomaly score 평가 + block decision)

### 3.2 paranoia level

CRS 의 검사 강도. 1 (느슨) ~ 4 (엄격).

| Level | 효과 | trade-off |
|-------|------|-----------|
| 1 (기본) | 보편적 패턴만 | false-positive 적음, 새 공격 놓침 |
| 2 | + 흔한 우회 (encoding 등) | FP 약간 증가 |
| 3 | + 정교한 공격 (regex 변형) | FP 더 증가, 튜닝 필요 |
| 4 (가장 엄격) | 모든 의심 차단 | FP 많음, 운영 시 매우 신중히 |

운영 환경의 시작은 `tx.paranoia_level=1` 권장. 그 후 application 별 튜닝.

### 3.3 inbound/outbound anomaly threshold

CRS 는 매칭 룰의 anomaly score 를 누적 → threshold 도달 시 block.

```
tx.inbound_anomaly_score_threshold = 5   ← 기본
tx.outbound_anomaly_score_threshold = 4
```

각 룰의 score:
- critical (XSS / SQLi confirmed) : 5
- error (suspicious) : 4
- warning : 3
- notice : 2

예: XSS critical 1건 매치 → score 5 → threshold 5 도달 → 403.

---

## 4. 6v6-web 의 실제 구성

```
/etc/modsecurity/
├── modsecurity.conf          ← 메인 설정
├── modsecurity.conf-recommended

/usr/share/modsecurity-crs/
├── crs-setup.conf            ← CRS 변수 정의 (paranoia, threshold)
└── rules/                    ← 30+ 룰 파일

/etc/apache2/sites-enabled/
├── 000-landing.conf
├── juice.6v6.lab.conf        ← reverse proxy + SecRuleEngine On
├── dvwa.6v6.lab.conf
└── ... (11 vhost)

/var/log/apache2/
├── access.log
├── error.log
└── modsec_audit.log          ← JSON 형식 audit log (Wazuh ingest)
```

### 4.1 modsecurity.conf 핵심 키

```
SecRuleEngine On                      # 룰 평가 활성 (DetectionOnly = 차단 안 함)
SecAuditEngine RelevantOnly           # 룰 매치 시만 audit log
SecAuditLogFormat JSON                # Wazuh decoder 친화
SecAuditLog /var/log/apache2/modsec_audit.log
SecDefaultAction "phase:2,log,auditlog,deny,status:403"
SecRequestBodyAccess On               # POST body 검사
SecResponseBodyAccess On              # 응답 검사
```

### 4.2 audit log JSON 구조

```
{
  "transaction": {
    "client_ip": "10.20.30.202",
    "time_stamp": "...",
    "request": {
      "method": "GET",
      "uri": "/?q=<script>alert(1)</script>",
      "headers": {...}
    },
    "response": {
      "http_code": 403,
      "headers": {...}
    },
    "messages": [
      {
        "id": "941100",
        "msg": "XSS Attack Detected via libinjection",
        "data": "Matched Data: <script>",
        "severity": "2",
        "tags": ["application-multi", "language-multi", "platform-multi", "OWASP_CRS", "attack-xss"]
      }
    ]
  }
}
```

한 줄 = 한 transaction. messages 배열에 매치된 룰 ID + 페이로드 + tags.

### 4.3 룰 ID 매핑

| ID range | 카테고리 |
|----------|----------|
| 920xxx | Protocol enforcement |
| 921xxx | Protocol attack |
| 930xxx | LFI |
| 931xxx | RFI |
| 932xxx | RCE |
| 933xxx | PHP |
| 941xxx | XSS |
| 942xxx | SQLi |
| 950xxx | Data leakage (response) |
| 951xxx | SQL error leak |

---

## 5. 룰 exception (false-positive 튜닝)

운영 시 정상 트래픽이 CRS 룰 매치 시 exception 추가.

### 5.1 룰 전체 비활성 (SecRuleRemoveById)

```
SecRuleRemoveById 941100              # XSS 룰 1개 전체 비활성 (위험 — 검토 필수)
```

### 5.2 특정 URL/parameter 만 예외 (SecRuleUpdateTargetById)

```
SecRuleUpdateTargetById 941100 "!ARGS:legit_param"
# 941100 룰을 적용하되, ARGS:legit_param 은 검사 제외
```

### 5.3 vhost / location 별 예외

```
<LocationMatch "/api/legacy/">
    SecRuleRemoveById 941100
</LocationMatch>
```

### 5.4 운영 권장

1. exception 은 가능한 좁은 범위 (특정 vhost + 특정 param)
2. 모든 exception 은 git audit + 추가 사유 주석
3. exception 누적 시 분기별 리뷰 (실제 공격 가려지는지)

---

## 6. 용어 해설

| 용어 | 설명 |
|------|------|
| **WAF** | Web Application Firewall |
| **CRS** | OWASP Core Rule Set |
| **paranoia level** | CRS 검사 강도 (1~4) |
| **anomaly scoring** | 룰 매치 점수 누적 → threshold 도달 시 block |
| **SecRuleEngine** | ModSec 룰 평가 모드 (On/DetectionOnly/Off) |
| **DetectionOnly** | 룰 평가 + log 만, block 안 함 (운영 초기 권장) |
| **transaction** | 한 HTTP request/response 쌍 (audit log 1 row) |
| **libinjection** | SQL/XSS 정교한 매칭 라이브러리 (CRS 가 사용) |
| **phase 1~5** | ModSec 처리 단계 (1=request headers, 2=request body, 3=response headers, 4=response body, 5=logging) |

---

## 7. 실습 1~7

### 실습 1 — 설정 가시화

```
ssh 6v6-web 'sudo grep -E "^SecRuleEngine|^SecAuditLog|^SecDefaultAction|^SecRequestBody" /etc/modsecurity/modsecurity.conf'
```

### 실습 2 — CRS 룰 파일 + paranoia

```
ssh 6v6-web 'sudo ls /usr/share/modsecurity-crs/rules/ | wc -l'
ssh 6v6-web 'sudo find / -name "crs-setup.conf" 2>/dev/null'
ssh 6v6-web 'sudo grep "tx.paranoia_level\|inbound_anomaly_score_threshold" $(sudo find / -name "crs-setup.conf" 2>/dev/null | head -1)'
```

### 실습 3 — XSS 공격 + 차단

```
ssh 6v6-attacker 'curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" "http://10.20.30.1/?q=<script>alert(1)</script>"'
# 403 응답 예상

# audit log 의 마지막 transaction
ssh 6v6-web 'sudo tail -1 /var/log/apache2/modsec_audit.log | jq ".transaction.messages[] | {id, msg, data}"'
```

### 실습 4 — SQLi 공격 + 차단

```
ssh 6v6-attacker "curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: juice.6v6.lab' \"http://10.20.30.1/?q=1' OR '1'='1\""
ssh 6v6-web 'sudo tail -1 /var/log/apache2/modsec_audit.log | jq ".transaction.messages[] | select(.id | startswith(\"942\")) | {id, msg}"'
```

### 실습 5 — paranoia 변경 시뮬레이션

```
# 현재 paranoia level 확인
ssh 6v6-web 'sudo grep "tx.paranoia_level" $(sudo find / -name "crs-setup.conf" 2>/dev/null | head -1)'

# vhost 단위로 paranoia 2 설정 (시연용 — 적용은 reload 필요)
# Apache .conf 에:
#   SecAction "id:9001,phase:1,nolog,pass,setvar:tx.paranoia_level=2"
```

### 실습 6 — 룰 exception 작성

```
# 941100 (XSS) 룰을 특정 URI 에서만 비활성
cat <<'EOF' | sudo tee /etc/apache2/conf-available/modsec-exception.conf
<LocationMatch "/api/legacy/comments">
    SecRuleRemoveById 941100
</LocationMatch>
EOF
sudo a2enconf modsec-exception
sudo systemctl reload apache2
```

(컨테이너 환경에선 시연용)

### 실습 7 — audit log 분석 종합

```
# 1시간 audit log 의 룰 ID top 10
ssh 6v6-web 'sudo grep -oE ''"id":"[0-9]+"'' /var/log/apache2/modsec_audit.log | sort | uniq -c | sort -rn | head -10'

# 차단 (403) vs 통과 비율
ssh 6v6-web 'sudo cat /var/log/apache2/modsec_audit.log | jq -r .transaction.response.http_code 2>/dev/null | sort | uniq -c'

# 가장 자주 매치된 룰 1개의 매칭 paydata 5개
ssh 6v6-web 'sudo cat /var/log/apache2/modsec_audit.log | jq -r ".transaction.messages[] | select(.id==\"941100\") | .data" 2>/dev/null | head -5'
```

---

## 8. 과제

### A. 공격 패턴 매트릭스 (필수)

OWASP Top 10 의 5 카테고리 (A03 Injection / A07 Identification 등) 각각 1개 공격
페이로드 작성 + ModSec 가 차단하는지 검증 + audit log 의 매칭 룰 ID 정리.

### B. paranoia 영향 분석 (심화)

paranoia level 1 → 2 변경 시 false-positive 가 증가하는 정상 트래픽 1가지 예측 + 검증.

### C. exception 작성 (정성)

본 lab 환경에서 false-positive 라 판단되는 룰 1개 선택 + exception 작성 + git audit
의도 1줄.

---

## 9. W07 (osquery) 예고

다음 주차부터 **호스트 가시화** — osquery 로 OS 내부 (프로세스, 파일, 사용자, 소켓) 를
SQL 로 추상화. WAF / IPS / 방화벽이 다 통과한 후의 호스트 행위 추적 마지막 안전망.
