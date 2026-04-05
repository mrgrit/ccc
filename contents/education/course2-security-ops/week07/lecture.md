# Week 07: Apache+ModSecurity WAF — 웹 애플리케이션 방화벽

## 학습 목표
- WAF의 역할과 동작 원리를 이해한다
- ModSecurity Core Rule Set (CRS)의 구조를 파악한다
- 커스텀 WAF 룰을 작성할 수 있다
- 오탐 예외 처리를 수행할 수 있다
- curl을 사용하여 WAF 동작을 테스트할 수 있다

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

# Week 07: Apache+ModSecurity WAF — 웹 애플리케이션 방화벽

## 학습 목표

- WAF의 역할과 동작 원리를 이해한다
- ModSecurity Core Rule Set (CRS)의 구조를 파악한다
- 커스텀 WAF 룰을 작성할 수 있다
- 오탐 예외 처리를 수행할 수 있다
- curl을 사용하여 WAF 동작을 테스트할 수 있다

---

## 1. WAF란?

WAF(Web Application Firewall)는 HTTP/HTTPS 트래픽을 검사하여 웹 공격을 차단하는 보안 솔루션이다.

**네트워크 방화벽 vs WAF:**

| 구분 | 네트워크 방화벽 (nftables) | WAF (Apache+ModSecurity) |
|------|---------------------------|-----------------|
| 계층 | L3/L4 (IP, 포트) | **L7 (HTTP 내용)** |
| 검사 대상 | IP, 포트, 프로토콜 | URL, 헤더, 쿠키, 본문 |
| 탐지 가능 | 포트 스캔, DoS | **SQL Injection, XSS, CSRF** |
| 배치 위치 | 네트워크 경계 | 웹 서버 앞단 |

---

## 2. Apache+ModSecurity 구조

> **이 실습을 왜 하는가?**
> "BunkerWeb WAF — 웹 애플리케이션 방화벽" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 보안 솔루션 운영 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

우리 실습 환경에서 WAF는 **Apache + ModSecurity** 모듈로 구성되어 있다.
(Apache+ModSecurity은 설치되어 있으나 현재 비활성 상태이며, Apache VirtualHost가 ModSecurity CRS를 직접 적용한다.)

```
클라이언트 요청
  |
  +---------------------------+
  |                           |
  v                           v
:80 (Apache 직접)           :8082 (Apache+ModSecurity 프록시)
  - WAF 없음                  - ModSecurity CRS 검사
  - SQLi 통과!                - 정상 --> 통과 (200)
  |                           - 공격 --> 차단 (403)
  v                           |
[Apache :80]                  v
                            [JuiceShop :3000] (백엔드 앱)
```

**실습 환경 포트 정리:** web 서버(10.20.30.80)

| 포트 | 서비스 | WAF 적용 | 비고 |
|------|--------|:---:|------|
| :80 | Apache 직접 | ✗ | SQLi/XSS 통과됨 |
| :3000 | JuiceShop 직접 | ✗ | 의도적 취약 앱 |
| **:8082** | **Apache+ModSecurity → JuiceShop** | **✓** | **SQLi → 403 차단** |
| :8081 | Apache+ModSecurity → Apache | ✓ | dmshop용 (PHP 에러) |

> **핵심:** WAF 효과를 테스트하려면 **:8082**로 접속해야 한다. :3000이나 :80은 WAF를 거치지 않는다.

---

## 3. 실습 환경 접속

> **실습 목적**: web 서버의 Apache+ModSecurity WAF 환경에 접속하여 웹 방화벽 동작을 확인한다
>
> **배우는 것**: ModSecurity의 요청 검사, OWASP CRS 룰셋 동작, WAF 로그 분석 방법을 배운다
>
> **결과 해석**: 악성 요청 시 403 차단 응답과 modsec_audit.log에 차단 기록이 남으면 WAF가 정상 동작한다
>
> **실전 활용**: 웹 서비스 앞단에 WAF를 배치하여 SQLi, XSS 등 웹 공격을 1차 차단하는 것이 표준 구성이다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80
```

### 3.1 WAF 상태 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
# Apache + ModSecurity 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "  # 비밀번호 자동입력 SSH
echo '=== Apache 상태 ===' && systemctl is-active apache2
echo '=== ModSecurity 모듈 ===' && echo 1 | sudo -S apache2ctl -M 2>/dev/null | grep security
echo '=== VirtualHost (WAF 적용 포트) ===' && echo 1 | sudo -S apache2ctl -S 2>/dev/null | grep -E '808[12]|:80 '
"
```

**예상 출력:**
```
=== Apache 상태 ===
active
=== ModSecurity 모듈 ===
 security2_module (shared)
=== VirtualHost (WAF 적용 포트) ===
*:80    dmshop.local (/etc/apache2/sites-enabled/dmshop.conf:1)
*:8082  127.0.1.1 (/etc/apache2/sites-enabled/juiceshop.conf:1)
*:8081  univ.local (/etc/apache2/sites-enabled/univ.conf:1)
```

> **해석:**
> - `security2_module` = ModSecurity v2 모듈이 로드됨
> - :8082 = JuiceShop 프록시 (ModSecurity CRS 적용됨)
> - :80 = dmshop (ModSecurity 미적용 또는 약한 설정)

### 3.2 WAF 차단 테스트

```bash
# :8082 (WAF 적용) vs :3000 (WAF 미적용) 비교
echo "=== :8082 (WAF ON) SQLi 테스트 ==="
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:8082/?id=1'+OR+1=1--"  # silent 모드
echo " ← 403이면 WAF가 차단"

echo "=== :3000 (WAF OFF) SQLi 테스트 ==="
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/?id=1'+OR+1=1--"  # silent 모드
echo " ← 200이면 WAF 미적용 (통과)"
```

**예상 결과:** :8082 → **403** (차단), :3000 → **200** (통과)

또는 환경 변수 확인:

```bash
echo 1 | sudo -S docker inspect apache2 | python3 -c "
import sys, json
data = json.load(sys.stdin)
env = data[0]['Config']['Env']
for e in sorted(env):                                  # 반복문 시작
    if 'MODSEC' in e.upper() or 'WAF' in e.upper() or 'SECURITY' in e.upper():
        print(e)
"
```

---

## 4. ModSecurity Core Rule Set (CRS)

CRS는 OWASP에서 관리하는 범용 WAF 룰셋이다.

### 4.1 CRS 구조

| 파일 범위 | 내용 |
|-----------|------|
| 900-xxx | 설정/초기화 |
| 910-xxx | IP 평판 검사 |
| 920-xxx | 프로토콜 위반 검사 |
| 930-xxx | 로컬 파일 포함 (LFI) |
| 931-xxx | 원격 파일 포함 (RFI) |
| 932-xxx | 원격 코드 실행 (RCE) |
| 933-xxx | PHP 공격 |
| 934-xxx | Node.js 공격 |
| 941-xxx | **XSS (Cross-Site Scripting)** |
| 942-xxx | **SQL Injection** |
| 943-xxx | 세션 고정 |
| 944-xxx | Java 공격 |
| 949-xxx | 인바운드 차단 판정 |
| 950-xxx | 아웃바운드 (데이터 유출) |

### 4.2 Anomaly Scoring

CRS는 **이상 점수(Anomaly Score)** 방식으로 동작한다:

1. 각 룰이 매칭되면 점수를 누적한다
2. 총 점수가 임계값을 초과하면 차단한다

| 심각도 | 점수 | 예 |
|--------|------|---|
| CRITICAL | 5 | SQL Injection |
| ERROR | 4 | 원격 코드 실행 |
| WARNING | 3 | 의심스러운 문자열 |
| NOTICE | 2 | 프로토콜 위반 |

**기본 차단 임계값: 5점** (CRITICAL 1개로 즉시 차단)

---

## 5. WAF 동작 테스트

> **이 실습의 핵심:**
> WAF가 실제로 공격을 차단하는지 **정상 요청과 공격 요청을 비교**하여 검증한다.
> 정상 요청은 200을 반환하고, SQLi/XSS/경로탐색 등 공격 요청은 **403(Forbidden)**을 반환해야 한다.
> 이것이 WAF의 핵심 기능이다.
>
> **중요:** 포트에 따라 WAF 적용 여부가 다르다:
> - `:80` (Apache 직접) → WAF **미적용** → SQLi가 통과됨 (200)
> - `:8082` (Apache+ModSecurity 프록시) → WAF **적용** → SQLi가 차단됨 (403)
> - `:3000` (JuiceShop 직접) → WAF **미적용** → 의도적 취약 앱

secu 서버 또는 로컬에서 web 서버로 공격 테스트를 수행한다:

### 5.1 정상 요청

```bash
# 정상 요청 (200 OK)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.20.30.80/
```

**예상 출력:**
```
HTTP 200
```

### 5.2 SQL Injection 테스트

```bash
# SQL Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?id=1%20OR%201=1"
```

**예상 출력:**
```
HTTP 403
```

### 5.3 XSS 테스트

```bash
# XSS (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?q=<script>alert(1)</script>"
```

**예상 출력:**
```
HTTP 403
```

### 5.4 디렉터리 트래버설 테스트

```bash
# Path Traversal (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/../../etc/passwd"
```

### 5.5 명령 주입 테스트

```bash
# Command Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?cmd=;cat%20/etc/passwd"
```

### 5.6 User-Agent 스캐너 테스트

```bash
# 스캐너 User-Agent (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -A "sqlmap/1.0" \
  "http://10.20.30.80/"
```

### 5.7 차단 응답 확인

```bash
# 차단 시 응답 본문 확인
curl -s "http://10.20.30.80/?id=1%20UNION%20SELECT%201"
```

**예상 출력:**
```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
</body>
</html>
```

---

## 6. WAF 로그 분석

### 6.1 ModSecurity 감사 로그

로그나 설정에서 특정 패턴을 검색합니다.

```bash
# Apache+ModSecurity 컨테이너 내 로그 확인
echo 1 | sudo -S docker exec apache2 cat /var/log/apache2/error.log | \
  grep "ModSecurity" | tail -10                        # 패턴 검색
```

### 6.2 Nginx 접근 로그

```bash
echo 1 | sudo -S docker exec apache2 cat /var/log/apache2/access.log | tail -20
```

### 6.3 차단된 요청 필터링

```bash
# 403 응답만 추출
echo 1 | sudo -S docker exec apache2 cat /var/log/apache2/access.log | \
  awk '$9 == 403' | tail -10                           # 텍스트 필드 처리
```

---

## 7. 커스텀 WAF 룰

### 7.1 ModSecurity 룰 문법

```
SecRule VARIABLES "OPERATOR" "ACTIONS"
```

| 부분 | 설명 | 예시 |
|------|------|------|
| VARIABLES | 검사 대상 | `REQUEST_URI`, `ARGS`, `REQUEST_HEADERS` |
| OPERATOR | 비교 연산 | `@rx` (정규식), `@contains`, `@eq` |
| ACTIONS | 동작 | `deny`, `log`, `id:xxx` |

### 7.2 커스텀 룰 작성

Apache+ModSecurity에서 커스텀 ModSecurity 룰을 추가하는 방법:

```bash
# 커스텀 룰 파일 생성
echo 1 | sudo -S tee /tmp/custom-waf-rules.conf << 'EOF'
# 관리자 페이지 외부 접근 차단
SecRule REQUEST_URI "@beginsWith /admin" \
  "id:10001,phase:1,deny,status:403,log,msg:'Admin access blocked'"

# 특정 파일 확장자 업로드 차단
SecRule FILES_NAMES "@rx \.(exe|bat|cmd|sh|php)$" \
  "id:10002,phase:2,deny,status:403,log,msg:'Dangerous file upload blocked'"

# 요청 본문 크기 제한 (10MB)
SecRule REQUEST_BODY_LENGTH "@gt 10485760" \
  "id:10003,phase:2,deny,status:413,log,msg:'Request body too large'"

# 특정 국가 차단 (GeoIP 필요)
# SecRule GEO:COUNTRY_CODE "@rx ^(CN|RU|KP)$" \
#   "id:10004,phase:1,deny,status:403,log,msg:'Country blocked'"
EOF
```

### 7.3 Apache+ModSecurity에 룰 적용

Apache+ModSecurity은 Docker 환경 변수 또는 설정 파일로 커스텀 룰을 적용한다:

```bash
# Apache+ModSecurity 설정 디렉터리 확인
echo 1 | sudo -S ls /opt/apache2/configs/ 2>/dev/null || \
echo 1 | sudo -S ls /etc/apache2/ 2>/dev/null || \
echo "설정 디렉터리를 확인하세요"
```

---

## 8. 예외 처리 (False Positive)

### 8.1 예외가 필요한 경우

- 정상적인 API 요청이 SQL Injection으로 오인될 때
- 관리 도구의 요청이 차단될 때
- 특정 경로에서 파일 업로드가 필요할 때

### 8.2 예외 룰 작성

```bash
# 특정 경로에서 SQL Injection 룰 비활성화
echo 1 | sudo -S tee /tmp/waf-exceptions.conf << 'EOF'
# /api/ 경로에서 SQL Injection 룰 예외
SecRule REQUEST_URI "@beginsWith /api/" \
  "id:10010,phase:1,pass,nolog,ctl:ruleRemoveById=942100-942999"

# 특정 파라미터에서 XSS 룰 예외
SecRule ARGS_NAMES "@eq search_query" \
  "id:10011,phase:1,pass,nolog,ctl:ruleRemoveTargetById=941100-941999;ARGS:search_query"

# 특정 IP에서 모든 룰 예외 (모니터링 서버)
SecRule REMOTE_ADDR "@eq 10.20.30.100" \
  "id:10012,phase:1,pass,nolog,ctl:ruleEngine=Off"
EOF
```

### 8.3 예외 적용 시 주의사항

1. **최소 권한 원칙**: 가능한 좁은 범위로 예외를 설정한다
2. **특정 룰 ID만 제외**: 전체 비활성화보다 특정 ID만 제외한다
3. **로그 기록 유지**: 예외 적용해도 로그는 남기는 것을 권장한다
4. **정기적 재검토**: 예외가 여전히 필요한지 주기적으로 확인한다

---

## 9. Anomaly Score 조정

### 9.1 차단 임계값 변경

```bash
# 임계값을 10으로 높이기 (더 관대하게)
# Apache+ModSecurity 환경 변수 방식:
# MODSECURITY_INBOUND_ANOMALY_SCORE_THRESHOLD=10
```

### 9.2 Paranoia Level 조정

| 레벨 | 설명 | 오탐 가능성 |
|------|------|-------------|
| PL 1 | 기본 (보수적) | 낮음 |
| PL 2 | 추가 룰 활성화 | 중간 |
| PL 3 | 공격적 탐지 | 높음 |
| PL 4 | 최대 탐지 | 매우 높음 |

```bash
# Paranoia Level 설정
# MODSECURITY_SEC_RULE_ENGINE=On
# CRS_PARANOIA_LEVEL=1
```

---

## 10. 종합 테스트 스크립트

다양한 공격을 한번에 테스트하는 스크립트:

```bash
cat << 'TESTEOF' > /tmp/waf_test.sh
#!/bin/bash
TARGET="http://10.20.30.80"
echo "=== WAF 테스트 시작 ==="

tests=(
  "정상 요청|/"
  "SQL Injection (OR)|/?id=1 OR 1=1"
  "SQL Injection (UNION)|/?id=1 UNION SELECT 1,2,3"
  "XSS (script)|/?q=<script>alert(1)</script>"
  "XSS (onerror)|/?q=<img src=x onerror=alert(1)>"
  "LFI (traversal)|/../../etc/passwd"
  "RCE (cmd injection)|/?cmd=;ls -la"
  "Scanner (sqlmap)|/ -A sqlmap/1.0"
)

for test in "${tests[@]}"; do                          # 반복문 시작
  IFS='|' read -r name path <<< "$test"
  if [[ "$name" == *"Scanner"* ]]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -A "sqlmap/1.0" "${TARGET}/")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET}${path}")
  fi
  if [ "$code" == "403" ]; then
    result="BLOCKED"
  elif [ "$code" == "200" ]; then
    result="PASSED"
  else
    result="HTTP $code"
  fi
  printf "%-30s %s (%s)\n" "$name" "$result" "$code"
done

echo "=== 테스트 완료 ==="
TESTEOF
chmod +x /tmp/waf_test.sh                              # 파일 권한 변경
bash /tmp/waf_test.sh
```

**예상 출력:**
```
=== WAF 테스트 시작 ===
정상 요청                       PASSED (200)
SQL Injection (OR)             BLOCKED (403)
SQL Injection (UNION)          BLOCKED (403)
XSS (script)                   BLOCKED (403)
XSS (onerror)                  BLOCKED (403)
LFI (traversal)                BLOCKED (403)
RCE (cmd injection)            BLOCKED (403)
Scanner (sqlmap)               BLOCKED (403)
=== 테스트 완료 ===
```

---

## 11. 실습 과제

### 과제 1: WAF 동작 확인

1. 위 테스트 스크립트를 실행하여 모든 공격이 차단되는지 확인하라
2. 차단된 요청의 로그를 분석하라
3. 응답 본문에 어떤 내용이 포함되어 있는지 확인하라

### 과제 2: 커스텀 룰 작성

1. `/backup` 경로 접근을 차단하는 룰을 작성하라
2. `.sql` 파일 다운로드를 차단하는 룰을 작성하라
3. 작성한 룰을 테스트하라

### 과제 3: 예외 처리

1. `/api/search` 경로에서 `q` 파라미터의 XSS 룰을 예외 처리하라
2. 예외 처리 후 정상적인 검색이 가능한지 확인하라
3. 동시에 다른 경로에서는 여전히 XSS가 차단되는지 확인하라

---

## 12. 핵심 정리

| 개념 | 설명 |
|------|------|
| WAF | L7 계층 웹 공격 차단 |
| ModSecurity | 오픈소스 WAF 엔진 |
| CRS | OWASP 핵심 룰셋 |
| Anomaly Score | 이상 점수 누적 방식 |
| Paranoia Level | 탐지 민감도 (1~4) |
| SecRule | ModSecurity 룰 문법 |
| ctl:ruleRemoveById | 특정 룰 예외 처리 |
| 403 Forbidden | WAF 차단 응답 |

---

## 다음 주 예고

Week 08은 **중간고사**이다:
- nftables 방화벽 + Suricata IPS를 조합하여
- 실제 보안 인프라를 구성하는 실기 시험

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
