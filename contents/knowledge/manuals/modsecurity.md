# ModSecurity WAF + OWASP CRS 레퍼런스

## 개요

ModSecurity는 Apache/Nginx용 오픈소스 웹 애플리케이션 방화벽(WAF)이다. OWASP Core Rule Set(CRS)과 함께 사용하여 SQL Injection, XSS, RCE 등 주요 웹 공격을 탐지/차단한다.

---

## 1. 설치

### Nginx + ModSecurity v3

```bash
# 의존성 설치
apt install libmodsecurity3 libmodsecurity-dev

# Nginx 커넥터 빌드 (또는 패키지 설치)
apt install libnginx-mod-security

# OWASP CRS 다운로드
git clone https://github.com/coreruleset/coreruleset.git /etc/modsecurity/crs
cp /etc/modsecurity/crs/crs-setup.conf.example /etc/modsecurity/crs/crs-setup.conf
```

### Nginx 설정

```nginx
# /etc/nginx/nginx.conf 또는 사이트 설정
server {
    modsecurity on;
    modsecurity_rules_file /etc/modsecurity/main.conf;
}
```

---

## 2. 핵심 설정

### main.conf

```apache
# /etc/modsecurity/main.conf
Include /etc/modsecurity/modsecurity.conf
Include /etc/modsecurity/crs/crs-setup.conf
Include /etc/modsecurity/crs/rules/*.conf
```

### modsecurity.conf 주요 지시어

```apache
# 엔진 모드
SecRuleEngine On              # 탐지 + 차단
SecRuleEngine DetectionOnly   # 탐지만 (로그 기록, 차단 안 함)
SecRuleEngine Off             # 비활성화

# 요청 본문 처리
SecRequestBodyAccess On
SecRequestBodyLimit 13107200          # 최대 요청 본문 크기 (12.5MB)
SecRequestBodyNoFilesLimit 131072     # 파일 제외 본문 크기

# 응답 본문 처리
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html text/xml application/json

# 감사 로그
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABCDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/modsecurity/audit.log

# 디버그 로그
SecDebugLog /var/log/modsecurity/debug.log
SecDebugLogLevel 0           # 0=없음, 1~9=상세

# 임시 파일 디렉토리
SecTmpDir /tmp/modsecurity
SecDataDir /tmp/modsecurity_data
```

---

## 3. SecRule 문법

### 기본 구조

```
SecRule VARIABLE "OPERATOR" "ACTIONS"
```

### 변수 (Variables)

| 변수                    | 설명                            |
|-------------------------|---------------------------------|
| `REQUEST_URI`           | 요청 URI (쿼리 포함)           |
| `REQUEST_FILENAME`      | 요청 경로 (쿼리 제외)          |
| `ARGS`                  | 모든 요청 파라미터              |
| `ARGS_GET`              | GET 파라미터                    |
| `ARGS_POST`             | POST 파라미터                   |
| `ARGS_NAMES`            | 파라미터 이름들                 |
| `REQUEST_HEADERS`       | 요청 헤더 전체                  |
| `REQUEST_HEADERS:Host`  | 특정 헤더                       |
| `REQUEST_BODY`          | 요청 본문                       |
| `REQUEST_METHOD`        | HTTP 메서드                     |
| `REQUEST_COOKIES`       | 쿠키 값들                       |
| `RESPONSE_BODY`         | 응답 본문                       |
| `RESPONSE_STATUS`       | 응답 상태 코드                  |
| `RESPONSE_HEADERS`      | 응답 헤더                       |
| `REMOTE_ADDR`           | 클라이언트 IP                   |
| `TX:anomaly_score`      | 현재 이상 점수 (CRS)           |
| `FILES`                 | 업로드 파일 이름                |
| `FILES_TMPNAMES`        | 업로드 임시 파일 경로           |

### 연산자 (Operators)

| 연산자        | 설명                    | 예시                          |
|---------------|-------------------------|-------------------------------|
| `@rx`         | 정규표현식 (기본값)     | `"@rx union.*select"`         |
| `@eq`         | 숫자 동일               | `"@eq 0"`                     |
| `@gt`         | 숫자 초과               | `"@gt 5"`                     |
| `@lt`         | 숫자 미만               | `"@lt 100"`                   |
| `@ge`         | 이상                    | `"@ge 10"`                    |
| `@contains`   | 문자열 포함             | `"@contains admin"`           |
| `@beginsWith` | 문자열 시작             | `"@beginsWith /api/"`         |
| `@endsWith`   | 문자열 끝               | `"@endsWith .php"`            |
| `@streq`      | 문자열 정확히 일치      | `"@streq GET"`                |
| `@within`     | 목록 내 존재            | `"@within GET POST"`          |
| `@ipMatch`    | IP/CIDR 매칭            | `"@ipMatch 10.20.30.0/24"`   |
| `@detectSQLi` | libinjection SQLi 탐지  | `"@detectSQLi"`               |
| `@detectXSS`  | libinjection XSS 탐지   | `"@detectXSS"`                |
| `@pm`         | 다중 패턴 매칭 (빠름)   | `"@pm cmd.exe /bin/bash"`     |

### 액션 (Actions)

| 액션                  | 설명                            |
|-----------------------|---------------------------------|
| `id:N`                | 룰 고유 ID (필수)               |
| `phase:N`             | 처리 단계 (1~5)                 |
| `deny`                | 요청 차단                       |
| `drop`                | 연결 끊기                       |
| `pass`                | 다음 룰로 진행                  |
| `allow`               | 요청 허용 (이후 룰 무시)       |
| `log`                 | 에러 로그에 기록                |
| `auditlog`            | 감사 로그에 기록                |
| `msg:'text'`          | 로그 메시지                     |
| `severity:N`          | 심각도 (0=긴급 ~ 7=디버그)     |
| `tag:'text'`          | 태그                            |
| `setvar:tx.score=+5`  | 변수 설정/증가                  |
| `chain`               | 다음 룰과 AND 조건              |
| `skip:N`              | N개 룰 건너뜀                   |
| `status:403`          | 차단 시 응답 코드               |
| `t:lowercase`         | 변환 (정규화)                   |
| `t:urlDecode`         | URL 디코딩                      |
| `t:htmlEntityDecode`  | HTML 엔티티 디코딩              |
| `t:removeWhitespace`  | 공백 제거                       |
| `ctl:ruleRemoveById`  | 특정 요청에서 룰 비활성화       |

### 처리 단계 (Phase)

| 단계 | 이름                | 시점                    |
|------|---------------------|-------------------------|
| 1    | Request Headers     | 요청 헤더 수신 후       |
| 2    | Request Body        | 요청 본문 수신 후       |
| 3    | Response Headers    | 응답 헤더 수신 후       |
| 4    | Response Body       | 응답 본문 수신 후       |
| 5    | Logging             | 로깅 단계               |

---

## 4. OWASP CRS 룰 카테고리

CRS는 **이상 점수(Anomaly Scoring)** 모델을 사용한다. 각 룰이 점수를 누적하고, 임계값을 초과하면 차단한다.

### 점수 임계값 설정 (crs-setup.conf)

```apache
SecAction "id:900110,phase:1,pass,nolog,\
  setvar:tx.inbound_anomaly_score_threshold=5,\
  setvar:tx.outbound_anomaly_score_threshold=4"
```

### 주요 룰 파일

| 파일 번호 | 카테고리              | 설명                          |
|-----------|-----------------------|-------------------------------|
| 910       | Scanner Detection     | 스캐너/봇 탐지               |
| 911       | Method Enforcement    | 허용 HTTP 메서드 제한         |
| 913       | Scanner Detection     | 크롤러/스캐너 UA 탐지        |
| 920       | Protocol Enforcement  | HTTP 프로토콜 위반            |
| 921       | Protocol Attack       | HTTP 요청 스머글링            |
| 930       | **LFI**               | 로컬 파일 포함 공격           |
| 931       | **RFI**               | 원격 파일 포함 공격           |
| 932       | **RCE**               | 원격 명령 실행                |
| 933       | PHP Injection         | PHP 코드 삽입                 |
| 934       | Node.js Injection     | Node.js 코드 삽입             |
| 941       | **XSS**               | 크로스사이트 스크립팅         |
| 942       | **SQLi**              | SQL 인젝션                    |
| 943       | Session Fixation      | 세션 고정 공격                |
| 944       | Java Attack           | Java 역직렬화 공격            |
| 949       | Blocking Evaluation   | 인바운드 점수 평가/차단       |
| 959       | Blocking Evaluation   | 아웃바운드 점수 평가/차단     |

---

## 5. 예외 처리

### 특정 룰 비활성화

```apache
# 특정 룰 ID 제거 (전역)
SecRuleRemoveById 942100

# 여러 룰 제거
SecRuleRemoveById 942100 942200 942300

# 범위로 제거
SecRuleRemoveById "942100-942999"

# 특정 경로에서만 제거
SecRule REQUEST_URI "@beginsWith /api/upload" \
  "id:10001,phase:1,pass,nolog,\
   ctl:ruleRemoveById=942100"

# 특정 파라미터에서 룰 제외
SecRuleUpdateTargetById 942100 "!ARGS:description"
SecRuleUpdateTargetById 942100 "!REQUEST_COOKIES:session"

# 특정 IP에서 WAF 비활성화
SecRule REMOTE_ADDR "@ipMatch 10.20.30.1" \
  "id:10002,phase:1,pass,nolog,\
   ctl:ruleEngine=Off"
```

### CRS 제외 (crs-setup.conf 또는 별도 파일)

```apache
# /etc/modsecurity/crs/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf
# 특정 URI에서 SQLi 룰 비활성화
SecRule REQUEST_URI "@beginsWith /api/search" \
  "id:10010,phase:1,pass,nolog,\
   ctl:ruleRemoveTargetById=942100;ARGS:query,\
   ctl:ruleRemoveTargetById=942200;ARGS:query"
```

---

## 6. 로그 분석

### 에러 로그

```bash
# /var/log/nginx/error.log 또는 /var/log/apache2/error.log
# ModSecurity 관련 항목 필터
grep "ModSecurity" /var/log/nginx/error.log

# 차단된 요청 확인
grep "Access denied" /var/log/nginx/error.log
```

### 에러 로그 형식 예시

```
ModSecurity: Warning. Matched "Operator `Rx' with parameter
`(?i:union.*select)' against variable `ARGS:id' (Value: `1 union select 1,2,3')
[file "/etc/modsecurity/crs/rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf"]
[line "100"] [id "942100"] [rev "1"] [msg "SQL Injection Attack"]
[severity "CRITICAL"] [tag "attack-sqli"]
```

### 감사 로그 구조

```
# /var/log/modsecurity/audit.log
# 파트별 내용:
# A — 감사 로그 헤더
# B — 요청 헤더
# C — 요청 본문
# D — (예약)
# E — 응답 본문 (중간)
# F — 응답 헤더
# H — 감사 로그 트레일러 (매칭 룰 정보)
# Z — 감사 로그 종료
```

```bash
# 특정 트랜잭션 상세 확인
grep -A 50 "unique_id" /var/log/modsecurity/audit.log

# 차단된 요청만 필터
grep "Action: Intercepted" /var/log/modsecurity/audit.log

# SID별 통계
grep -oP 'id "\K[0-9]+' /var/log/modsecurity/audit.log \
  | sort | uniq -c | sort -rn | head -20
```

---

## 7. 실습 예제

### 예제 1: 커스텀 IP 차단 룰

```apache
# 특정 IP 차단
SecRule REMOTE_ADDR "@ipMatch 192.168.1.100,192.168.1.101" \
  "id:100001,phase:1,deny,status:403,log,\
   msg:'Blocked IP',tag:'custom/ip-block'"
```

### 예제 2: 특정 경로 보호

```apache
# /admin 경로는 내부 네트워크만 접근 허용
SecRule REQUEST_URI "@beginsWith /admin" \
  "id:100002,phase:1,chain,deny,status:403,log,\
   msg:'Admin access from external network'"
SecRule REMOTE_ADDR "!@ipMatch 10.20.30.0/24"
```

### 예제 3: 파일 업로드 확장자 제한

```apache
SecRule FILES_NAMES "@rx \.(php|jsp|asp|exe|sh|py)$" \
  "id:100003,phase:2,deny,status:403,log,\
   msg:'Dangerous file upload blocked',\
   tag:'custom/file-upload',severity:2"
```

### 예제 4: 요청 속도 제한

```apache
# IP별 분당 100회 초과 시 차단
SecAction "id:100010,phase:1,pass,nolog,\
  initcol:ip=%{REMOTE_ADDR},\
  setvar:ip.request_count=+1,\
  deprecatevar:ip.request_count=100/60"

SecRule IP:REQUEST_COUNT "@gt 100" \
  "id:100011,phase:1,deny,status:429,log,\
   msg:'Rate limit exceeded',tag:'custom/rate-limit'"
```

### 예제 5: 응답에서 정보 유출 차단

```apache
# 서버 에러 메시지에서 DB 정보 유출 방지
SecRule RESPONSE_BODY "@rx (mysql_|ORA-[0-9]+|PostgreSQL|SQLSTATE)" \
  "id:100020,phase:4,deny,status:500,log,\
   msg:'Database error information leakage',\
   tag:'custom/info-leak',severity:3"
```

---

## 8. 성능 튜닝

```apache
# 정적 파일 제외
SecRule REQUEST_FILENAME "@rx \.(css|js|png|jpg|gif|ico|woff2?)$" \
  "id:100100,phase:1,pass,nolog,\
   ctl:ruleEngine=Off"

# 큰 파일 업로드 경로 제외
SecRule REQUEST_URI "@beginsWith /api/files/upload" \
  "id:100101,phase:1,pass,nolog,\
   ctl:requestBodyAccess=Off"

# PCRE 매칭 제한
SecPcreMatchLimit 100000
SecPcreMatchLimitRecursion 100000
```

---

## 참고

- ModSecurity v3: https://github.com/owasp-modsecurity/ModSecurity
- OWASP CRS: https://coreruleset.org
- CRS 문서: https://coreruleset.org/docs/
