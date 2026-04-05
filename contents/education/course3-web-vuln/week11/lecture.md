# Week 11: 에러 처리 / 정보 노출 점검

## 학습 목표
- 부적절한 에러 처리가 보안에 미치는 영향을 이해한다
- 스택 트레이스, 디버그 모드에서 노출되는 정보를 분석한다
- 디렉터리 리스팅 취약점을 점검한다
- 정보 노출의 다양한 경로를 체계적으로 점검할 수 있다

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

# Week 11: 에러 처리 / 정보 노출 점검

## 학습 목표
- 부적절한 에러 처리가 보안에 미치는 영향을 이해한다
- 스택 트레이스, 디버그 모드에서 노출되는 정보를 분석한다
- 디렉터리 리스팅 취약점을 점검한다
- 정보 노출의 다양한 경로를 체계적으로 점검할 수 있다

## 전제 조건
- HTTP 응답 코드 이해 (200, 404, 500 등)
- curl 사용법

---

## 1. 정보 노출의 위험 (15분)

### 1.1 OWASP에서의 위치

**A05:2021 Security Misconfiguration** 카테고리.
잘못된 설정으로 인한 정보 노출은 공격의 첫 단추가 된다.

### 1.2 노출 가능한 정보

| 정보 유형 | 노출 경로 | 위험 |
|----------|----------|------|
| 서버 버전 | HTTP 헤더 | CVE 검색 → 공격 |
| 파일 경로 | 스택 트레이스 | 내부 구조 파악 |
| DB 정보 | SQL 에러 | SQLi 공격 보조 |
| 소스 코드 | 디버그 모드 | 로직 분석 |
| 사용자 목록 | 열거 공격 | 무차별 대입 대상 |
| API 키/토큰 | 소스 코드, 설정 파일 | 인증 우회 |

---

## 2. 스택 트레이스 / 에러 메시지 (30분)

> **이 실습을 왜 하는가?**
> "에러 처리 / 정보 노출 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 에러 유도 기법

> **실습 목적**: 에러 메시지와 HTTP 헤더를 통한 정보 노출 취약점을 점검한다
>
> **배우는 것**: 스택 트레이스, 디버그 정보, 서버 버전 등 공격에 활용 가능한 정보 노출을 탐지하는 방법을 배운다
>
> **결과 해석**: 에러 페이지에 DB 종류, 파일 경로, 프레임워크 버전이 노출되면 정보 유출 취약점이다
>
> **실전 활용**: 정보 노출은 그 자체로 위험하진 않지만, 후속 공격(SQLi, 버전별 익스플로잇)의 핵심 정보를 제공한다

```bash
# 1. 존재하지 않는 경로 (404)
echo "=== 404 에러 ==="
curl -s http://10.20.30.80:3000/nonexistent_path_xyz123 | head -10  # silent 모드
echo ""

# 2. 잘못된 파라미터 타입
echo "=== 타입 에러 ==="
curl -s http://10.20.30.80:3000/api/Products/abc | python3 -m json.tool 2>/dev/null  # silent 모드
echo ""

# 3. SQL 문법 오류 유도
echo "=== SQL 에러 ==="
curl -s "http://10.20.30.80:3000/rest/products/search?q='" | head -20  # silent 모드
echo ""

# 4. 빈 JSON body
echo "=== 빈 요청 에러 ==="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool 2>/dev/null           # 요청 데이터(body)
echo ""

# 5. 잘못된 Content-Type
echo "=== Content-Type 에러 ==="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: text/plain" \
  -d 'not json' | head -10                             # 요청 데이터(body)
echo ""

# 6. 매우 긴 입력
echo "=== 과도한 입력 ==="
LONG_INPUT=$(python3 -c "print('A'*10000)")
curl -s "http://10.20.30.80:3000/rest/products/search?q=$LONG_INPUT" | head -5  # silent 모드
```

### 2.2 스택 트레이스 분석

```bash
# 에러 응답에서 민감 정보 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q='" | python3 -c "  # silent 모드
import sys, json

data = sys.stdin.read()
try:
    parsed = json.loads(data)
    error = parsed.get('error', {})
    if isinstance(error, dict):
        message = error.get('message', '')
        stack = error.get('stack', '')
    else:
        message = str(error)
        stack = ''
except:
    message = data[:500]
    stack = ''

print('=== 에러 메시지 분석 ===')
print(f'메시지: {message[:200]}')

if stack:
    print(f'\n스택 트레이스 (처음 5줄):')
    for i, line in enumerate(stack.split('\n')[:5]):   # 반복문 시작
        print(f'  {line.strip()}')

# 노출된 정보 식별
info_found = []
full_text = message + stack
if 'SQLITE' in full_text.upper() or 'sqlite' in full_text:
    info_found.append('DB 종류: SQLite')
if '/app/' in full_text or '/home/' in full_text:
    info_found.append('파일 경로 노출')
if 'node_modules' in full_text:
    info_found.append('Node.js 사용 확인')
if 'at ' in full_text and '.js:' in full_text:
    info_found.append('JS 파일명 + 줄번호')

print(f'\n노출된 정보: {info_found if info_found else \"없음\"}')" 2>/dev/null
```

### 2.3 에러 응답 비교 (JuiceShop vs Apache)

```bash
echo "=== JuiceShop 에러 응답 ==="
curl -sI http://10.20.30.80:3000/nonexistent | head -5
echo ""
curl -s http://10.20.30.80:3000/nonexistent | head -5  # silent 모드

echo ""
echo "=== Apache 에러 응답 ==="
curl -sI http://10.20.30.80:80/nonexistent | head -5
echo ""
curl -s http://10.20.30.80:80/nonexistent | head -10   # silent 모드

# Apache 에러 페이지에 버전 정보가 노출되는지 확인
curl -s http://10.20.30.80:80/nonexistent | grep -i "apache\|server at\|port"  # silent 모드
```

---

## 3. 디버그 모드 점검 (20분)

### 3.1 디버그 엔드포인트 탐색

```bash
# 일반적인 디버그/상태 엔드포인트
echo "=== 디버그 엔드포인트 탐색 ==="
for path in \
  "debug" "console" "status" "health" "healthcheck" \
  "info" "env" "config" "metrics" "trace" \
  "actuator" "actuator/env" "actuator/health" \
  "_debug" "__debug__" "phpinfo.php" \
  "server-status" "server-info" \
  "elmah.axd" "trace.axd" \
  ".env" "config.json" "package.json"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

### 3.2 JuiceShop 메트릭 엔드포인트

```bash
# /metrics 엔드포인트가 노출되면 내부 정보 확인 가능
echo "=== /metrics 내용 ==="
curl -s http://10.20.30.80:3000/metrics | head -30

# 메트릭에서 추출 가능한 정보:
# - 요청 수, 에러 수
# - 메모리 사용량
# - Node.js 버전
# - 프로세스 정보
```

### 3.3 소스맵 파일 노출

```bash
# Angular 앱의 소스맵(.map) 파일이 노출되는지 확인
# 소스맵이 있으면 프론트엔드 원본 소스 코드를 복원할 수 있음
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS 파일: $MAIN_JS"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/${MAIN_JS}.map")
  echo "소스맵 ($MAIN_JS.map): HTTP $code"
  if [ "$code" = "200" ]; then
    echo "소스맵 노출됨! 소스 코드 복원 가능"
    curl -s "http://10.20.30.80:3000/${MAIN_JS}.map" | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin)
sources = data.get('sources', [])
print(f'소스 파일 수: {len(sources)}')
for s in sources[:10]:                                 # 반복문 시작
    print(f'  {s}')
if len(sources) > 10:
    print(f'  ... 외 {len(sources)-10}개')
" 2>/dev/null
  fi
fi
```

---

## 4. 디렉터리 리스팅 (25분)

### 4.1 디렉터리 리스팅이란?

디렉터리 리스팅은 웹 서버가 디렉터리의 파일 목록을 보여주는 기능이다.
개발/테스트 환경에서는 편리하지만, 운영 환경에서는 보안 위험이다.

### 4.2 디렉터리 리스팅 점검

```bash
# JuiceShop 디렉터리 리스팅
echo "=== JuiceShop 디렉터리 리스팅 ==="
for dir in "/" "/ftp" "/ftp/" "/assets" "/assets/" "/public" "/encryptionkeys"; do  # 반복문 시작
  result=$(curl -s "http://10.20.30.80:3000$dir" | head -3)
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$dir")
  echo "[$code] $dir"
  if echo "$result" | grep -qi "index of\|listing\|directory"; then
    echo "  → 디렉터리 리스팅 활성화!"
  fi
done

echo ""
echo "=== Apache 디렉터리 리스팅 ==="
for dir in "/" "/icons/" "/manual/" "/cgi-bin/"; do    # 반복문 시작
  result=$(curl -s "http://10.20.30.80:80$dir" | head -5)
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80$dir")
  echo "[$code] $dir"
  if echo "$result" | grep -qi "index of\|listing\|directory"; then
    echo "  → 디렉터리 리스팅 활성화!"
  fi
done
```

### 4.3 JuiceShop /ftp 상세 탐색

```bash
# /ftp 디렉터리의 파일 목록과 내용 확인
echo "=== /ftp 파일 목록 ==="
curl -s http://10.20.30.80:3000/ftp/ | python3 -c "    # silent 모드
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for f in data:                                 # 반복문 시작
            print(f'  {f}')
    elif isinstance(data, dict):
        for f in data.get('data', data.get('files', [])):  # 반복문 시작
            if isinstance(f, str):
                print(f'  {f}')
            else:
                print(f'  {f.get(\"name\", f)}')
except:
    print(sys.stdin.read()[:500])
" 2>/dev/null

# 각 파일 내용 확인
echo ""
echo "=== 주요 파일 내용 ==="
for file in "legal.md" "acquisitions.md" "package.json.bak" "coupons_2013.md.bak" "eastere.gg"; do  # 반복문 시작
  echo "--- $file ---"
  curl -s "http://10.20.30.80:3000/ftp/$file" 2>/dev/null | head -5  # silent 모드
  echo ""
done
```

---

## 5. 사용자 열거 (User Enumeration) (20분)

### 5.1 열거 공격이란?

에러 메시지의 차이를 이용하여 유효한 사용자명/이메일을 알아내는 공격이다.

```
존재하는 계정: "비밀번호가 틀렸습니다" ← 계정 존재 확인!
미존재 계정: "계정을 찾을 수 없습니다" ← 계정 없음 확인!

안전한 메시지: "이메일 또는 비밀번호가 올바르지 않습니다"
                (존재 여부를 알 수 없음)
```

### 5.2 JuiceShop 사용자 열거 테스트

```bash
# 로그인 에러 메시지 비교
echo "=== 사용자 열거 테스트 ==="

# 존재하는 이메일 + 잘못된 비밀번호
echo "존재하는 계정:"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('error','')[:100])" 2>/dev/null  # 요청 데이터(body)

# 존재하지 않는 이메일
echo "미존재 계정:"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@nowhere.com","password":"wrong"}' | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('error','')[:100])" 2>/dev/null  # 요청 데이터(body)

echo ""
echo "두 메시지가 다르면 → 사용자 열거 가능 (취약)"
echo "두 메시지가 같으면 → 사용자 열거 불가 (양호)"
```

### 5.3 회원가입에서의 열거

```bash
# 이미 존재하는 이메일로 가입 시도
echo ""
echo "=== 회원가입 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null  # 요청 데이터(body)

echo ""
echo "새 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"brand_new_user@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null  # 요청 데이터(body)
```

### 5.4 비밀번호 찾기에서의 열거

```bash
# 비밀번호 재설정 기능에서 열거
echo ""
echo "=== 비밀번호 재설정 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3  # 요청 데이터(body)

echo ""
echo "미존재 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@test.com","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3  # 요청 데이터(body)
```

---

## 6. 종합 정보 노출 점검 스크립트 (20분)

```bash
# 자동 점검 스크립트
python3 << 'PYEOF'                                     # Python 스크립트 실행
import requests, json

BASE = "http://10.20.30.80:3000"
findings = []

print("=" * 60)
print("정보 노출 종합 점검")
print("=" * 60)

# 1. 서버 헤더
r = requests.head(BASE, timeout=5)
for header in ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]:  # 반복문 시작
    val = r.headers.get(header)
    if val:
        findings.append(f"헤더 정보 노출: {header}: {val}")
        print(f"[!] {header}: {val}")

# 2. 보안 헤더 미설정
for header in ["X-Frame-Options", "X-Content-Type-Options",  # 반복문 시작
               "Content-Security-Policy", "Strict-Transport-Security"]:
    if header not in r.headers:
        findings.append(f"보안 헤더 미설정: {header}")
        print(f"[-] {header}: 미설정")

# 3. 에러 정보 노출
r = requests.get(f"{BASE}/rest/products/search?q='", timeout=5)
try:
    err = r.json()
    if "error" in err:
        error_msg = str(err["error"])
        if "SQLITE" in error_msg.upper() or "stack" in error_msg.lower():
            findings.append("에러 메시지에 DB/스택 정보 노출")
            print(f"[!] 에러에 내부 정보 포함")
except:
    pass

# 4. 디렉터리/파일 노출
sensitive_paths = ["ftp", "metrics", ".env", "package.json", "encryptionkeys"]
for path in sensitive_paths:                           # 반복문 시작
    r = requests.get(f"{BASE}/{path}", timeout=5)
    if r.status_code == 200:
        findings.append(f"민감 경로 접근 가능: /{path}")
        print(f"[!] /{path}: 접근 가능 (HTTP {r.status_code})")

# 5. 요약
print(f"\n{'=' * 60}")
print(f"총 발견 사항: {len(findings)}건")
for i, f in enumerate(findings, 1):                    # 반복문 시작
    print(f"  {i}. {f}")
PYEOF
```

---

## 7. 실습 과제

### 과제 1: 에러 메시지 분석
1. 다양한 방법으로 JuiceShop에 에러를 유발하라 (최소 5가지)
2. 각 에러 응답에서 노출되는 정보를 분석하라
3. 가장 많은 정보를 노출하는 에러 패턴을 보고하라

### 과제 2: 정보 노출 점검
1. JuiceShop과 Apache의 디렉터리 리스팅 상태를 비교하라
2. 디버그/상태 엔드포인트를 모두 탐색하라
3. 소스맵 파일 노출 여부를 확인하라

### 과제 3: 사용자 열거
1. 로그인, 회원가입, 비밀번호 재설정에서 사용자 열거가 가능한지 테스트하라
2. 열거 가능/불가능한 기능을 구분하고 에러 메시지를 비교하라
3. 안전한 에러 메시지 예시를 제안하라

---

## 8. 요약

| 취약점 | 확인 방법 | 위험도 | 방어 |
|--------|----------|--------|------|
| 스택 트레이스 노출 | 에러 유도 | 중 | 운영 환경 에러 숨김 |
| 서버 버전 노출 | 헤더 확인 | 하 | 헤더 제거/변경 |
| 디렉터리 리스팅 | 디렉터리 URL 접근 | 중 | Options -Indexes |
| 디버그 모드 | 엔드포인트 탐색 | 상 | 운영 환경 비활성화 |
| 소스맵 노출 | .map 파일 접근 | 중 | 운영 빌드에서 제거 |
| 사용자 열거 | 에러 메시지 비교 | 중 | 일관된 에러 메시지 |

**다음 주 예고**: Week 12 - API 보안 점검. REST API 인증, Rate Limiting, Swagger 노출을 학습한다.

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
