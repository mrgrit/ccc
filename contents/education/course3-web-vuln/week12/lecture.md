# Week 12: API 보안 점검

## 학습 목표
- REST API의 보안 위협을 이해한다
- API 인증/인가를 점검할 수 있다
- Rate Limiting의 필요성과 점검 방법을 익힌다
- Swagger/OpenAPI 문서 노출의 위험을 파악한다

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

# Week 12: API 보안 점검

## 학습 목표
- REST API의 보안 위협을 이해한다
- API 인증/인가를 점검할 수 있다
- Rate Limiting의 필요성과 점검 방법을 익힌다
- Swagger/OpenAPI 문서 노출의 위험을 파악한다

## 전제 조건
- REST API 기본 개념 (HTTP 메서드, JSON)
- JWT 인증 (Week 04)

---

## 1. API 보안 개요 (15분)

### 1.1 OWASP API Security Top 10 (2023)

| 순위 | 위협 | 설명 |
|------|------|------|
| API1 | Broken Object Level Authorization | IDOR (Week 09) |
| API2 | Broken Authentication | 인증 우회 |
| API3 | Broken Object Property Level Authorization | 과도한 데이터 노출 |
| API4 | Unrestricted Resource Consumption | Rate Limit 부재 |
| API5 | Broken Function Level Authorization | 권한 상승 |
| API6 | Unrestricted Access to Sensitive Business Flows | 비즈니스 로직 악용 |
| API7 | Server Side Request Forgery | SSRF |
| API8 | Security Misconfiguration | 설정 오류 |
| API9 | Improper Inventory Management | API 문서 관리 부재 |
| API10 | Unsafe Consumption of APIs | 외부 API 신뢰 |

### 1.2 API vs 웹 페이지 점검 차이

| 항목 | 웹 페이지 | API |
|------|----------|-----|
| 인터페이스 | HTML 폼, 브라우저 | JSON/XML, 직접 호출 |
| 인증 | 세션 쿠키 | API Key, JWT, OAuth |
| 입력 | 폼 필드 | JSON body, Query params |
| 문서 | 사용자 매뉴얼 | Swagger/OpenAPI |
| Rate Limit | 덜 중요 | 매우 중요 |

---

## 2. JuiceShop API 구조 파악 (20분)

> **이 실습을 왜 하는가?**
> "API 보안 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 API 엔드포인트 전체 탐색

> **실습 목적**: REST API 엔드포인트의 인증, 권한, 입력값 검증 등 API 보안을 점검한다
>
> **배우는 것**: API 엔드포인트 열거, 인증 우회 시도, 과도한 데이터 노출 확인 등 API 특화 점검 기법을 배운다
>
> **결과 해석**: 인증 없이 API 접근이 가능하거나 응답에 불필요한 필드가 포함되면 API 보안 취약점이다
>
> **실전 활용**: 마이크로서비스 환경에서 API 보안은 OWASP API Top 10으로 별도 관리될 만큼 중요하다

```bash
# JuiceShop API 엔드포인트 목록 수집
echo "=== API 엔드포인트 탐색 ==="

# HTML/JS에서 API 경로 추출
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS에서 발견된 API 경로:"
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '"/api/[^"]*"|"/rest/[^"]*"' | sort -u | head -30  # silent 모드
fi

echo ""
echo "=== 직접 탐색 ==="
# REST API 엔드포인트
ENDPOINTS=(
  "api/Products" "api/Products/1" "api/Users" "api/Users/1"
  "api/Feedbacks" "api/Feedbacks/1" "api/Challenges" "api/Complaints"
  "api/Recycles" "api/SecurityQuestions" "api/Quantitys"
  "rest/products/search?q=test" "rest/user/login" "rest/user/whoami"
  "rest/user/change-password" "rest/basket/1" "rest/track-order/1"
  "rest/saveLoginIp" "rest/deluxe-membership" "rest/memories"
  "rest/chatbot/status" "rest/chatbot/respond" "rest/languages"
  "rest/repeat-notification" "rest/continue-code" "rest/continue-code/apply"
  "rest/wallet/balance" "rest/order-history"
  "b2b/v2/orders" "profile" "file-upload"
  "promotion" "video" "redirect" "snippets"
)

printf "%-45s %s\n" "엔드포인트" "코드"
printf "%-45s %s\n" "---" "---"
for ep in "${ENDPOINTS[@]}"; do                        # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$ep")
  if [ "$code" != "404" ]; then
    printf "%-45s %s\n" "/$ep" "$code"
  fi
done
```

### 2.2 HTTP 메서드별 응답 확인

```bash
# 각 API의 지원 메서드 확인
echo "=== Products API 메서드 ==="
for method in GET POST PUT DELETE PATCH OPTIONS; do    # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" http://10.20.30.80:3000/api/Products/)
  echo "  $method: HTTP $code"
done

echo ""
echo "=== Users API 메서드 ==="
for method in GET POST PUT DELETE PATCH OPTIONS; do    # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" http://10.20.30.80:3000/api/Users/)
  echo "  $method: HTTP $code"
done
```

---

## 3. API 인증 점검 (30분)

### 3.1 인증 없는 접근 테스트

```bash
# 인증 토큰 없이 각 API 호출
echo "=== 인증 없는 접근 테스트 ==="
python3 << 'PYEOF'                                     # Python 스크립트 실행
import requests

BASE = "http://10.20.30.80:3000"
endpoints = {
    "GET /api/Products": f"{BASE}/api/Products",
    "GET /api/Users": f"{BASE}/api/Users",
    "GET /api/Feedbacks": f"{BASE}/api/Feedbacks",
    "GET /api/Challenges": f"{BASE}/api/Challenges",
    "GET /api/Complaints": f"{BASE}/api/Complaints",
    "GET /rest/user/whoami": f"{BASE}/rest/user/whoami",
    "GET /rest/basket/1": f"{BASE}/rest/basket/1",
    "GET /rest/wallet/balance": f"{BASE}/rest/wallet/balance",
    "GET /rest/order-history": f"{BASE}/rest/order-history",
    "POST /api/Feedbacks": f"{BASE}/api/Feedbacks",
}

print(f"{'API':<35} {'인증없음':>10} {'결과':>10}")
print("-" * 60)

for name, url in endpoints.items():                    # 반복문 시작
    method = name.split()[0]
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json={}, timeout=5)
        status = "공개" if r.status_code == 200 else "보호"
        print(f"{name:<35} {r.status_code:>10} {status:>10}")
    except Exception as e:
        print(f"{name:<35} {'ERROR':>10}")
PYEOF
```

### 3.2 토큰 조작 테스트

```bash
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

echo "=== 토큰 조작 테스트 ==="

# 정상 토큰
echo "정상 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user',{}).get('email','실패'))" 2>/dev/null  # 인증 토큰

# 만료된 토큰 (한 글자 변경)
TAMPERED="${TOKEN:0:-5}XXXXX"
echo "변조 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TAMPERED" | head -3       # 인증 토큰

# 빈 토큰
echo "빈 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer " | head -3                # 인증 토큰

# 다른 인증 스킴
echo "Basic 인증 시도:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Basic YWRtaW46YWRtaW4=" | head -3  # 인증 토큰
```

### 3.3 API 키 노출 점검

```bash
# 소스 코드에서 API 키/시크릿 패턴 검색
echo "=== 소스 코드 내 시크릿 검색 ==="
if [ -n "$MAIN_JS" ]; then
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oiE \
    "(api[_-]?key|secret|token|password|auth)['\"]?\s*[:=]\s*['\"][^'\"]{8,}" | head -10
fi

# HTML에서 시크릿 검색
curl -s http://10.20.30.80:3000 | grep -oiE \
  "(api[_-]?key|secret|token)['\"]?\s*[:=]\s*['\"][^'\"]{8,}" | head -5
```

---

## 4. Rate Limiting 점검 (25분)

### 4.1 Rate Limiting이란?

Rate Limiting은 특정 시간 내 요청 수를 제한하여 무차별 대입, DoS, 스크래핑을 방지한다.

### 4.2 로그인 API Rate Limiting 테스트

```bash
echo "=== 로그인 API Rate Limiting 테스트 ==="
echo "30회 연속 잘못된 로그인 시도:"

for i in $(seq 1 30); do                               # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"wrong$i\"}")  # 요청 데이터(body)
  if [ "$code" = "429" ]; then
    echo "시도 $i: HTTP $code (Rate Limited!)"
    echo "Rate Limiting 활성화됨 ($i 회째에서 차단)"
    break
  elif [ "$i" -eq 10 ] || [ "$i" -eq 20 ] || [ "$i" -eq 30 ]; then
    echo "시도 $i: HTTP $code"
  fi
done

echo ""
echo "30회 모두 401이면 → Rate Limiting 없음 (취약)"
echo "429가 나오면 → Rate Limiting 있음 (양호)"
```

### 4.3 검색 API Rate Limiting 테스트

```bash
echo "=== 검색 API Rate Limiting 테스트 ==="
echo "50회 연속 검색 요청:"

blocked=0
for i in $(seq 1 50); do                               # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/rest/products/search?q=test$i")
  if [ "$code" = "429" ]; then
    echo "시도 $i: Rate Limited!"
    blocked=1
    break
  fi
done

if [ $blocked -eq 0 ]; then
  echo "50회 모두 정상 응답 → Rate Limiting 없음"
fi
```

### 4.4 Rate Limiting 우회 시도

```bash
# X-Forwarded-For 헤더로 IP 위장
echo "=== Rate Limiting 우회 (IP 위장) ==="
for i in $(seq 1 5); do                                # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 1.2.3.$i" \
    -d '{"email":"admin@juice-sh.op","password":"wrong"}')  # 요청 데이터(body)
  echo "IP 1.2.3.$i: HTTP $code"
done
```

---

## 5. Swagger / OpenAPI 문서 노출 (20분)

### 5.1 Swagger UI 탐색

```bash
# Swagger/OpenAPI 문서 경로 탐색
echo "=== Swagger/API 문서 탐색 ==="
for path in \
  "swagger" "swagger-ui" "swagger-ui.html" "swagger.json" "swagger.yaml" \
  "api-docs" "api/docs" "v1/api-docs" "v2/api-docs" "v3/api-docs" \
  "openapi.json" "openapi.yaml" "docs" "redoc" \
  "graphql" "graphiql" "playground" \
  "api/swagger" "api/openapi" "_api" "api/v1" "api/v2"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

### 5.2 Swagger 문서가 노출된 경우의 위험

API 문서가 외부에 노출되면:

1. **모든 API 엔드포인트가 공개됨** → 공격 표면 확대
2. **파라미터/데이터 타입이 공개됨** → 정밀한 공격 가능
3. **인증 방식이 공개됨** → 우회 시도 용이
4. **숨겨진 관리자 API도 노출 가능** → 권한 상승 위험

### 5.3 API 문서에서 공격 대상 추출

```bash
# Swagger JSON이 있다면 파싱하여 엔드포인트 추출
SWAGGER_URL="http://10.20.30.80:3000/swagger.json"
result=$(curl -s -o /dev/null -w "%{http_code}" "$SWAGGER_URL")

if [ "$result" = "200" ]; then
  echo "Swagger 문서 발견! 엔드포인트 추출:"
  curl -s "$SWAGGER_URL" | python3 -c "                # silent 모드
import sys, json
doc = json.load(sys.stdin)
paths = doc.get('paths', {})
for path, methods in paths.items():                    # 반복문 시작
    for method in methods:                             # 반복문 시작
        if method.upper() in ['GET','POST','PUT','DELETE','PATCH']:
            auth = '인증필요' if any('security' in str(methods[method]) for _ in [1]) else '공개'
            print(f'  {method.upper():6} {path}')
" 2>/dev/null
else
  echo "Swagger 문서 없음 (HTTP $result)"
fi
```

---

## 6. 데이터 과다 노출 점검 (20분)

### 6.1 불필요한 필드 노출

```bash
# API 응답에 불필요한 민감 정보가 포함되는지 확인
echo "=== 데이터 과다 노출 점검 ==="

TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# Users API 응답 분석
echo "=== /api/Users/1 응답 필드 ==="
curl -s http://10.20.30.80:3000/api/Users/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "     # 인증 토큰
import sys, json
try:
    data = json.load(sys.stdin).get('data', {})
    sensitive_keywords = ['password', 'hash', 'secret', 'token', 'ssn', 'card', 'credit']
    print('포함된 필드:')
    for key, val in data.items():                      # 반복문 시작
        is_sensitive = any(k in key.lower() for k in sensitive_keywords)
        marker = ' <<< 민감 정보!' if is_sensitive else ''
        print(f'  {key}: {str(val)[:60]}{marker}')
except Exception as e:
    print(f'파싱 실패: {e}')
" 2>/dev/null

echo ""
echo "=== /api/Products/1 응답 필드 ==="
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -c "  # silent 모드
import sys, json
try:
    data = json.load(sys.stdin).get('data', {})
    print('포함된 필드:')
    for key, val in data.items():                      # 반복문 시작
        print(f'  {key}: {str(val)[:60]}')
except:
    print('파싱 실패')
" 2>/dev/null
```

### 6.2 대량 데이터 조회 (Pagination 부재)

```bash
# 전체 데이터 조회 시 페이지네이션 여부
echo "=== 페이지네이션 점검 ==="

# 전체 사용자 조회
result=$(curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN")                   # 인증 토큰
count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "Users API: ${count}건 반환 (제한 없이 전체?)"

# 전체 상품 조회
result=$(curl -s http://10.20.30.80:3000/api/Products/)
count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "Products API: ${count}건 반환"
```

---

## 7. 실습 과제

### 과제 1: API 인벤토리 작성
1. JuiceShop의 모든 API 엔드포인트를 탐색하여 목록을 작성하라
2. 각 API의 지원 메서드(GET/POST/PUT/DELETE)를 확인하라
3. 인증 필요 여부를 표시하라

### 과제 2: Rate Limiting 점검
1. 로그인 API에 대한 Rate Limiting 존재 여부를 확인하라
2. 검색, 회원가입 등 다른 API에도 Rate Limiting이 있는지 테스트하라
3. Rate Limiting이 없는 API에서 가능한 공격 시나리오를 서술하라

### 과제 3: API 보안 종합 보고서
1. JuiceShop API의 인증, 인가, Rate Limiting, 데이터 노출을 종합 점검하라
2. OWASP API Security Top 10 기준으로 취약점을 분류하라
3. 각 취약점에 대한 개선 권고를 작성하라

---

## 8. 요약

| 점검 항목 | 도구 | 기대 결과 |
|----------|------|----------|
| API 인증 | curl (토큰 제외) | 인증 필요 API → 401/403 |
| Rate Limiting | curl 반복 호출 | 과도한 요청 → 429 |
| Swagger 노출 | 경로 탐색 | 404 (비공개) |
| 데이터 과다 노출 | 응답 필드 분석 | 최소 필드만 반환 |
| HTTP 메서드 | 메서드 변경 | 불필요 메서드 → 405 |

**다음 주 예고**: Week 13 - OWASP ZAP 자동화 점검. ZAP 자동 스캔, 보고서 생성을 학습한다.

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
