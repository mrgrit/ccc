# Week 13: 자동화 점검 도구 활용

## 학습 목표
- OWASP ZAP을 사용한 자동 취약점 스캔을 수행한다
- nikto를 활용한 웹서버 보안 점검을 수행한다
- 자동화 도구의 한계와 수동 점검의 필요성을 이해한다
- 스캔 결과를 분석하고 오탐을 필터링한다

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

## 용어 해설 (웹취약점 점검 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **취약점 점검** | Vulnerability Assessment | 시스템의 보안 약점을 체계적으로 찾는 활동 | 건물 안전 진단 |
| **모의해킹** | Penetration Testing | 실제 공격자처럼 취약점을 악용하여 검증 | 소방 훈련 (실제로 불을 피워봄) |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 0~10점 (9.0+ Critical) | 질병 위험 등급표 |
| **SQLi** | SQL Injection | SQL 쿼리에 악성 입력 삽입 | 주문서에 가짜 지시를 끼워넣기 |
| **XSS** | Cross-Site Scripting | 웹페이지에 악성 스크립트 삽입 | 게시판에 함정 쪽지 붙이기 |
| **CSRF** | Cross-Site Request Forgery | 사용자 모르게 요청을 위조 | 누군가 내 이름으로 송금 요청 |
| **SSRF** | Server-Side Request Forgery | 서버가 내부 자원에 요청하도록 조작 | 직원에게 기밀 문서를 가져오라 속이기 |
| **LFI** | Local File Inclusion | 서버의 로컬 파일을 읽는 취약점 | 사무실 서류함을 몰래 열람 |
| **RFI** | Remote File Inclusion | 외부 파일을 서버에 로드하는 취약점 | 외부에서 악성 서류를 사무실에 반입 |
| **RCE** | Remote Code Execution | 원격에서 서버 코드 실행 | 전화로 사무실 컴퓨터 조작 |
| **WAF 우회** | WAF Bypass | 웹 방화벽의 탐지를 피하는 기법 | 보안 검색대를 우회하는 비밀 통로 |
| **인코딩** | Encoding | 데이터를 다른 형식으로 변환 (URL, Base64 등) | 택배 재포장 (내용물은 같음) |
| **난독화** | Obfuscation | 코드를 읽기 어렵게 변환 (탐지 회피) | 범인이 변장하는 것 |
| **세션** | Session | 서버가 사용자를 식별하는 상태 정보 | 카페 단골 인식표 |
| **쿠키** | Cookie | 브라우저에 저장되는 작은 데이터 | 가게에서 받은 스탬프 카드 |
| **Burp Suite** | Burp Suite | 웹 보안 점검 프록시 도구 (PortSwigger) | 우편물 검사 장비 |
| **OWASP ZAP** | OWASP ZAP | 오픈소스 웹 보안 스캐너 | 무료 보안 검사 장비 |
| **점검 보고서** | Assessment Report | 발견된 취약점과 대응 방안을 정리한 문서 | 건물 안전 진단 보고서 |

---

# Week 13: 자동화 점검 도구 활용

## 학습 목표
- OWASP ZAP을 사용한 자동 취약점 스캔을 수행한다
- nikto를 활용한 웹서버 보안 점검을 수행한다
- 자동화 도구의 한계와 수동 점검의 필요성을 이해한다
- 스캔 결과를 분석하고 오탐을 필터링한다

## 전제 조건
- Week 01~12 취약점 점검 기법 이해
- HTTP 프록시(Burp Suite, ZAP) 기본 사용법

---

## 1. 자동화 점검 도구 개요 (15분)

### 1.1 자동화 도구의 위치

```
수동 점검 (깊이) <-----------> 자동화 점검 (넓이)
  +-- 로직 취약점 발견         +-- 대량 URL 스캔
  +-- 비즈니스 로직 우회       +-- 알려진 패턴 매칭
  +-- 체인 공격               +-- 반복 점검 효율화
```

### 1.2 주요 자동화 도구 비교

| 도구 | 유형 | 라이선스 | 강점 |
|------|------|---------|------|
| OWASP ZAP | DAST (동적) | 오픈소스 | 무료, API, CI 연동 |
| Burp Suite Pro | DAST | 상용 | 정밀도, 확장성 |
| nikto | 웹서버 스캐너 | 오픈소스 | 빠른 설정 점검 |
| sqlmap | SQLi 특화 | 오픈소스 | SQL Injection 자동화 |
| Nuclei | 템플릿 기반 | 오픈소스 | 커스텀 템플릿 |

### 1.3 DAST vs SAST vs IAST

| 항목 | DAST | SAST | IAST |
|------|------|------|------|
| 분석 대상 | 실행 중인 앱 | 소스코드 | 런타임 + 코드 |
| 장점 | 실제 동작 검증 | 개발 초기 발견 | 정확도 높음 |
| 단점 | 코드 위치 모름 | 오탐 많음 | 에이전트 필요 |
| 이번 주 | 실습 대상 | - | - |

---

## 2. OWASP ZAP 기본 설정 (20분)

> **이 실습을 왜 하는가?**
> "자동화 점검 도구 활용" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 ZAP Docker 컨테이너 준비

> **실습 목적**: ZAP 등 자동화 도구를 활용하여 대규모 웹 취약점 스캔을 수행한다
>
> **배우는 것**: 자동화 스캐너의 설정, 실행, 결과 분석 방법과 수동 점검과의 차이를 이해한다
>
> **결과 해석**: 스캔 결과에서 High/Medium 등급 발견 항목은 수동 검증 후 보고서에 포함한다
>
> **실전 활용**: 실무에서는 자동화 스캔으로 1차 탐색 후, 수동 점검으로 오탐 제거와 심화 분석을 수행한다

```bash
# web 서버에서 ZAP 컨테이너 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 \
  "docker ps -a | grep zap 2>/dev/null; echo '---'; which zaproxy 2>/dev/null || echo 'ZAP not installed locally'"

# ZAP이 없는 경우 Python ZAP 클라이언트로 API 모드 사용
# 여기서는 ZAP CLI/API 대신 커맨드라인 도구 조합으로 동일 효과 달성
```

### 2.2 대상 정보 수집 (스파이더링 대체)

원격 서버에 접속하여 명령을 실행합니다.

```bash
# JuiceShop 엔드포인트 자동 수집 (API 기반 스파이더링)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== JuiceShop 엔드포인트 수집 ==="

# 메인 페이지에서 링크 추출
curl -s http://localhost:3000/ | grep -oP 'href="[^"]*"' | sort -u | head -20  # silent 모드
echo "---"

# API 엔드포인트 탐색
for ep in rest/products search api/SecurityQuestions rest/user/whoami; do  # 반복문 시작
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$ep)
  echo "$ep -> $STATUS"
done

echo "---"

# Swagger/OpenAPI 문서 존재 확인
for path in api-docs swagger.json openapi.json; do     # 반복문 시작
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  echo "$path -> $STATUS"
done
ENDSSH
```

### 2.3 디렉토리 브루트포스

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 일반적인 관리 경로 점검
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 디렉토리/파일 존재 점검 ==="

PATHS=(
  "admin" "administrator" "console" "debug"
  "api" "api-docs" "swagger-ui" "graphql"
  ".env" ".git" "robots.txt" "sitemap.xml"
  "backup" "dump" "test" "staging"
  "wp-admin" "phpmyadmin" "server-status"
)

for p in "${PATHS[@]}"; do                             # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 3 http://localhost:3000/$p)
  if [ "$CODE" != "404" ] && [ "$CODE" != "000" ]; then
    echo "[${CODE}] /$p"
  fi
done
ENDSSH
```

---

## 3. nikto 웹서버 점검 (25분)

### 3.1 nikto 기본 스캔

원격 서버에 접속하여 명령을 실행합니다.

```bash
# nikto가 설치된 환경에서 실행 (또는 Docker)
# 여기서는 nikto 대체로 수동 헤더/설정 점검 수행

sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 웹서버 보안 헤더 점검 (nikto 스타일) ==="

# 응답 헤더 전체 수집
HEADERS=$(curl -sI http://localhost:3000/)
echo "$HEADERS"
echo "---"

# 보안 헤더 존재 여부 점검
echo "=== 보안 헤더 점검 ==="
for hdr in "X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection" \
           "Content-Security-Policy" "Strict-Transport-Security" \
           "Referrer-Policy" "Permissions-Policy"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    VALUE=$(echo "$HEADERS" | grep -i "$hdr" | head -1)
    echo "[OK] $VALUE"
  else
    echo "[MISSING] $hdr"
  fi
done
ENDSSH
```

### 3.2 서버 정보 노출 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 서버 정보 노출 점검 ==="

# Server 헤더
SERVER=$(curl -sI http://localhost:3000/ | grep -i "^server:")
echo "Server 헤더: ${SERVER:-'노출 없음'}"

# X-Powered-By 헤더
POWERED=$(curl -sI http://localhost:3000/ | grep -i "x-powered-by")
echo "X-Powered-By: ${POWERED:-'노출 없음'}"

# 에러 페이지에서 정보 노출
echo "---"
echo "=== 에러 페이지 정보 노출 ==="
curl -s http://localhost:3000/nonexistent-page-12345 | head -5  # silent 모드

echo "---"
echo "=== 특수 경로 점검 ==="
# 흔한 정보 노출 경로
for path in ".git/HEAD" ".env" ".htaccess" "web.config" "package.json" \
            "Dockerfile" "docker-compose.yml"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  if [ "$CODE" = "200" ]; then
    echo "[EXPOSED] /$path"
  fi
done
ENDSSH
```

### 3.3 HTTP 메서드 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== HTTP 메서드 점검 ==="

# OPTIONS 메서드로 허용 메서드 확인
ALLOW=$(curl -sI -X OPTIONS http://localhost:3000/ | grep -i "allow:")
echo "Allow: ${ALLOW:-'OPTIONS 응답 없음'}"

# 위험한 메서드 테스트
for method in PUT DELETE TRACE CONNECT PATCH; do       # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:3000/)
  echo "$method -> $CODE"
done
ENDSSH
```

---

## 4. sqlmap 자동화 SQL Injection 점검 (25분)

### 4.1 sqlmap 기본 사용법

원격 서버에 접속하여 명령을 실행합니다.

```bash
# SQL Injection 점검 자동화 (sqlmap 스타일의 수동 점검)
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== SQL Injection 자동 점검 ==="

# 1. 검색 파라미터 테스트
PAYLOADS=(
  "' OR '1'='1"
  "1 UNION SELECT 1,2,3--"
  "1' AND SLEEP(2)--"
  "1; DROP TABLE test--"
  "admin'--"
)

echo "--- 검색 엔드포인트 ---"
for payload in "${PAYLOADS[@]}"; do                    # 반복문 시작
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/rest/products/search?q=${ENCODED}")
  echo "Payload: $payload -> HTTP $CODE"
done

echo ""
echo "--- 로그인 엔드포인트 ---"
# 로그인 SQL Injection 테스트
for email in "' OR 1=1--" "admin'--" "' UNION SELECT 1,2,3,4,5,6,7,8,9--"; do  # 반복문 시작
  RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"test\"}" | python3 -c "  # 요청 데이터(body)
import json,sys
try:
  d = json.load(sys.stdin)
  if 'authentication' in d:
    print('VULNERABLE - 로그인 성공')
  elif 'error' in str(d):
    print('차단됨')
  else:
    print(str(d)[:80])
except: print('파싱 오류')
" 2>/dev/null)
  echo "Email: $email -> $RESULT"
done
ENDSSH
```

### 4.2 자동 점검 스크립트 작성

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 종합 자동 점검 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
cat << 'SCRIPT' > /tmp/auto_scan.sh
#!/bin/bash
TARGET="http://localhost:3000"
REPORT="/tmp/scan_report_$(date +%Y%m%d_%H%M%S).txt"

echo "=== 자동 취약점 점검 보고서 ===" > $REPORT
echo "대상: $TARGET" >> $REPORT
echo "일시: $(date)" >> $REPORT
echo "---" >> $REPORT

# 1. 보안 헤더 점검
echo "[1] 보안 헤더 점검" >> $REPORT
HEADERS=$(curl -sI $TARGET)
for hdr in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" \
           "Strict-Transport-Security" "X-XSS-Protection"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    echo "  [PASS] $hdr 존재" >> $REPORT
  else
    echo "  [FAIL] $hdr 누락" >> $REPORT
  fi
done

# 2. 정보 노출 점검
echo "[2] 정보 노출 점검" >> $REPORT
for path in ".git/HEAD" ".env" "package.json" "api-docs" "swagger.json"; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" $TARGET/$path)
  if [ "$CODE" = "200" ]; then
    echo "  [FAIL] /$path 노출 (HTTP $CODE)" >> $REPORT
  else
    echo "  [PASS] /$path 비노출 (HTTP $CODE)" >> $REPORT
  fi
done

# 3. SQLi 기본 점검
echo "[3] SQL Injection 기본 점검" >> $REPORT
SQLI_RESP=$(curl -s -X POST $TARGET/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}')       # 요청 데이터(body)
if echo "$SQLI_RESP" | grep -q "authentication"; then
  echo "  [CRITICAL] 로그인 SQLi 취약" >> $REPORT
else
  echo "  [PASS] 로그인 SQLi 차단" >> $REPORT
fi

# 4. XSS 반사형 점검
echo "[4] XSS 반사형 점검" >> $REPORT
XSS_RESP=$(curl -s "$TARGET/rest/products/search?q=<script>alert(1)</script>")
if echo "$XSS_RESP" | grep -q "<script>alert(1)</script>"; then
  echo "  [HIGH] 검색 XSS 반사 취약" >> $REPORT
else
  echo "  [PASS] 검색 XSS 필터링" >> $REPORT
fi

echo "---" >> $REPORT
echo "점검 완료: $(date)" >> $REPORT
cat $REPORT
SCRIPT

chmod +x /tmp/auto_scan.sh                             # 파일 권한 변경
bash /tmp/auto_scan.sh
ENDSSH
```

---

## 5. 스캔 결과 분석과 오탐 필터링 (20분)

### 5.1 오탐(False Positive) 판별 기준

| 판별 기준 | 정탐 가능성 높음 | 오탐 가능성 높음 |
|----------|----------------|----------------|
| 응답 변화 | 페이로드에 따라 응답 내용 변화 | 모든 입력에 동일 응답 |
| 에러 메시지 | DB 에러 메시지 노출 | 커스텀 에러 페이지 |
| 응답 시간 | 시간 기반 페이로드에 지연 발생 | 일정한 응답 시간 |
| 상태 코드 | 비정상 상태 코드 반환 | 항상 200 OK |

### 5.2 오탐 검증 실습

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 오탐 검증: 시간 기반 SQLi ==="

# 정상 요청 응답 시간 측정
NORMAL_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
  "http://localhost:3000/rest/products/search?q=apple")
echo "정상 요청: ${NORMAL_TIME}s"

# 시간 기반 SQLi 페이로드
SQLI_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
  "http://localhost:3000/rest/products/search?q=apple'+AND+SLEEP(3)--")
echo "SQLi 페이로드: ${SQLI_TIME}s"

# 판별
python3 -c "                                           # Python 코드 실행
normal = float('$NORMAL_TIME')
sqli = float('$SQLI_TIME')
diff = sqli - normal                                   # 파일 차이 비교
print(f'응답 시간 차이: {diff:.2f}s')
if diff > 2.5:
    print('판정: 정탐 가능성 높음 (SLEEP 실행된 것으로 추정)')
else:
    print('판정: 오탐 가능성 높음 (응답 시간 차이 미미)')
"
ENDSSH
```

### 5.3 결과 정리 및 우선순위 분류

원격 서버에 접속하여 명령을 실행합니다.

```bash
# 스캔 결과를 CVSS 기반으로 분류
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
findings = [
    {"id": "V-001", "name": "SQL Injection (로그인)", "cvss": 9.8, "severity": "Critical"},
    {"id": "V-002", "name": "보안 헤더 누락 (CSP)", "cvss": 4.3, "severity": "Medium"},
    {"id": "V-003", "name": "서버 정보 노출", "cvss": 5.3, "severity": "Medium"},
    {"id": "V-004", "name": "package.json 노출", "cvss": 3.1, "severity": "Low"},
    {"id": "V-005", "name": "디버그 정보 노출", "cvss": 5.3, "severity": "Medium"},
]

findings.sort(key=lambda x: x["cvss"], reverse=True)

print(f"{'ID':<8} {'취약점':<30} {'CVSS':<6} {'심각도':<10}")
print("-" * 60)
for f in findings:                                     # 반복문 시작
    print(f"{f['id']:<8} {f['name']:<30} {f['cvss']:<6} {f['severity']:<10}")

print(f"\n총 {len(findings)}건 발견")
print(f"  Critical: {sum(1 for f in findings if f['severity']=='Critical')}")
print(f"  High:     {sum(1 for f in findings if f['severity']=='High')}")
print(f"  Medium:   {sum(1 for f in findings if f['severity']=='Medium')}")
print(f"  Low:      {sum(1 for f in findings if f['severity']=='Low')}")
PYEOF
ENDSSH
```

---

## 6. Nuclei 템플릿 기반 점검 (20분)

### 6.1 Nuclei 스타일 커스텀 템플릿

원격 서버에 접속하여 명령을 실행합니다.

```bash
# Nuclei YAML 템플릿 스타일의 점검 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
import json, subprocess, urllib.request, urllib.parse

TARGET = "http://localhost:3000"

# Nuclei 스타일 템플릿 정의
templates = [
    {
        "id": "exposed-gitconfig",
        "name": ".git/config 노출",
        "severity": "medium",
        "path": "/.git/config",
        "match_status": 200,
        "match_body": "[core]"
    },
    {
        "id": "exposed-env",
        "name": ".env 파일 노출",
        "severity": "high",
        "path": "/.env",
        "match_status": 200,
        "match_body": "="
    },
    {
        "id": "exposed-package-json",
        "name": "package.json 노출",
        "severity": "low",
        "path": "/package.json",
        "match_status": 200,
        "match_body": "dependencies"
    },
    {
        "id": "admin-panel",
        "name": "관리자 패널 접근",
        "severity": "high",
        "path": "/#/administration",
        "match_status": 200,
        "match_body": ""
    },
    {
        "id": "swagger-exposed",
        "name": "Swagger UI 노출",
        "severity": "medium",
        "path": "/api-docs",
        "match_status": 200,
        "match_body": ""
    },
]

print(f"{'템플릿 ID':<25} {'심각도':<10} {'결과':<10}")
print("-" * 50)

for t in templates:                                    # 반복문 시작
    try:
        req = urllib.request.Request(TARGET + t["path"])
        resp = urllib.request.urlopen(req, timeout=5)
        code = resp.getcode()
        body = resp.read().decode("utf-8", errors="ignore")

        if code == t["match_status"]:
            if not t["match_body"] or t["match_body"] in body:
                print(f"{t['id']:<25} {t['severity']:<10} {'FOUND':<10}")
                continue
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")
    except Exception as e:
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")

PYEOF
ENDSSH
```

---

## 7. WAF 탐지와 우회 점검 (15분)

### 7.1 WAF 존재 여부 확인

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== WAF 탐지 점검 ==="

# 1. 일반 요청 vs 악성 요청 응답 비교
echo "--- 일반 요청 ---"
curl -sI "http://localhost:3000/rest/products/search?q=apple" | head -3

echo "--- SQLi 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=' OR 1=1--" | head -3

echo "--- XSS 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=<script>alert(1)</script>" | head -3

# 2. Apache+ModSecurity WAF 시그니처 확인
echo "---"
echo "=== Apache+ModSecurity 응답 헤더 ==="
curl -sI http://localhost:3000/ | grep -iE "server|x-apache2|modsecurity|x-waf"
ENDSSH
```

---

## 핵심 정리

1. OWASP ZAP, nikto, sqlmap은 취약점 자동 점검의 핵심 도구다
2. 자동 도구는 넓은 범위를 빠르게 점검하지만 로직 취약점은 놓친다
3. 오탐 판별은 응답 변화, 시간 차이, 에러 메시지를 기준으로 한다
4. Nuclei 스타일 템플릿으로 반복 가능한 점검을 구성할 수 있다
5. WAF가 있어도 우회 가능성을 항상 점검해야 한다
6. 자동 스캔 + 수동 검증의 조합이 최선의 점검 방법이다

---

## 다음 주 예고
- Week 14: 취약점 점검 보고서 작성법 - CVSS 점수, 재현 절차, 권고사항

---

---

## 자가 점검 퀴즈 (5문항)

이번 주차의 핵심 기술 내용을 점검한다.

**Q1.** CVSS 9.8은 어떤 심각도 등급인가?
- (a) High  (b) **Critical**  (c) Medium  (d) Low

**Q2.** 취약점 점검 시 가장 먼저 수행하는 단계는?
- (a) 익스플로잇 실행  (b) **대상 범위 확인 및 정보 수집**  (c) 보고서 작성  (d) 패치 적용

**Q3.** SQLi 취약점의 CWE 번호는?
- (a) CWE-79  (b) **CWE-89**  (c) CWE-352  (d) CWE-22

**Q4.** 점검 보고서에서 취약점의 '재현 절차'가 중요한 이유는?
- (a) 분량을 늘리기 위해  (b) **고객이 직접 확인하고 수정할 수 있도록**  (c) 법적 요건  (d) 점검 시간 기록

**Q5.** WAF(:8082)가 SQLi를 차단할 때 반환하는 HTTP 코드는?
- (a) 200 OK  (b) **403 Forbidden**  (c) 500 Internal Error  (d) 301 Redirect

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b

---
---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성
