# Week 14: 취약점 점검 보고서 작성법

## 학습 목표
- CVSS v3.1 점수 체계를 이해하고 취약점에 적용할 수 있다
- 재현 가능한 취약점 증명(PoC) 절차를 작성할 수 있다
- 전문적인 취약점 점검 보고서를 작성할 수 있다
- 권고사항을 위험도와 구현 난이도 기준으로 우선순위화한다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| bastion | 10.20.30.201 | Control Plane (Bastion) | `ssh ccc@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `ssh ccc@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `ssh ccc@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh Dashboard:443, OpenCTI:8080) | `ssh ccc@10.20.30.100` |

**Bastion API:** `http://localhost:9100` / Key: `ccc-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + Bastion 연동 (Part 5) | 실습 |
| 3:20-3:40 | 정리 + 과제 안내 | 정리 |

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

## 전제 조건
- Week 01~13 취약점 점검 실습 완료
- 기본적인 보고서 작성 경험

---

## 1. 취약점 점검 보고서 구조 (15분)

### 1.1 표준 보고서 구성

```
1. 표지 (프로젝트명, 일시, 점검 범위, 점검자)
2. 요약 (Executive Summary)
   - 점검 결과 요약 (통계)
   - 주요 발견사항 (Top 3)
   - 전체 위험도 평가
3. 점검 범위 및 방법론
   - 대상 시스템 목록
   - 사용 도구
   - 점검 방법론 (OWASP Testing Guide)
4. 발견사항 상세
   - 취약점별 상세 기술
5. 권고사항 (우선순위별)
6. 부록 (도구 출력, 스크린샷, 참고자료)
```

### 1.2 좋은 보고서 vs 나쁜 보고서

| 항목 | 좋은 보고서 | 나쁜 보고서 |
|------|-----------|-----------|
| 재현성 | 단계별 재현 가능 | "취약점 있음"만 기술 |
| 증거 | 스크린샷 + 요청/응답 | 도구 출력 복사 |
| 영향 | 비즈니스 영향 설명 | 기술 용어만 나열 |
| 권고사항 | 구체적 코드/설정 제시 | "보안 강화 필요" |
| 대상 독자 | 경영진 + 개발팀 분리 | 단일 기술 문서 |

---

## 2. CVSS v3.1 점수 체계 (25분)

> **이 실습을 왜 하는가?**
> "취약점 점검 보고서 작성법" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 CVSS 기본 지표 (Base Metrics)

| 지표 | 값 | 설명 |
|------|-----|------|
| Attack Vector (AV) | N/A/L/P | 네트워크/인접/로컬/물리 |
| Attack Complexity (AC) | L/H | 낮음/높음 |
| Privileges Required (PR) | N/L/H | 없음/낮음/높음 |
| User Interaction (UI) | N/R | 없음/필요 |
| Scope (S) | U/C | 변경없음/변경됨 |
| Confidentiality (C) | N/L/H | 없음/낮음/높음 |
| Integrity (I) | N/L/H | 없음/낮음/높음 |
| Availability (A) | N/L/H | 없음/낮음/높음 |

### 2.2 심각도 등급

| 점수 | 등급 | 색상 |
|------|------|------|
| 0.0 | None | - |
| 0.1 - 3.9 | Low | 녹색 |
| 4.0 - 6.9 | Medium | 황색 |
| 7.0 - 8.9 | High | 주황 |
| 9.0 - 10.0 | Critical | 적색 |

### 2.3 실습: JuiceShop 취약점 CVSS 산출

> **실습 목적**: 발견된 취약점의 CVSS 점수를 산출하고 전문적인 점검 보고서를 작성한다
>
> **배우는 것**: CVSS 벡터 계산법, 취약점별 심각도 분류, 보고서 구성 요소와 작성 방법을 배운다
>
> **결과 해석**: CVSS 점수가 9.0 이상이면 Critical, 7.0-8.9은 High로 긴급 조치가 필요한 등급이다
>
> **실전 활용**: 점검 보고서의 품질이 곧 컨설팅 회사의 역량 지표이며, CVSS 산출 능력은 필수이다

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
# CVSS v3.1 간이 계산기
def cvss_score(av, ac, pr, ui, scope, c, i, a):
    """CVSS v3.1 Base Score 간이 계산"""
    av_val = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
    ac_val = {"L": 0.77, "H": 0.44}

    # Scope Unchanged
    pr_u = {"N": 0.85, "L": 0.62, "H": 0.27}
    # Scope Changed
    pr_c = {"N": 0.85, "L": 0.68, "H": 0.50}

    ui_val = {"N": 0.85, "R": 0.62}
    cia_val = {"N": 0, "L": 0.22, "H": 0.56}

    pr_val = pr_c if scope == "C" else pr_u

    exploitability = 8.22 * av_val[av] * ac_val[ac] * pr_val[pr] * ui_val[ui]
    impact_sub = 1 - ((1 - cia_val[c]) * (1 - cia_val[i]) * (1 - cia_val[a]))

    if scope == "U":
        impact = 6.42 * impact_sub
    else:
        impact = 7.52 * (impact_sub - 0.029) - 3.25 * (impact_sub - 0.02) ** 15

    if impact <= 0:
        return 0.0

    if scope == "U":
        score = min(impact + exploitability, 10)
    else:
        score = min(1.08 * (impact + exploitability), 10)

    import math
    return math.ceil(score * 10) / 10

# JuiceShop 취약점별 CVSS 산출
vulns = [
    {
        "name": "SQL Injection (로그인 우회)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        "params": ("N", "L", "N", "N", "U", "H", "H", "N"),
    },
    {
        "name": "Stored XSS (상품 리뷰)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N",
        "params": ("N", "L", "L", "R", "C", "L", "L", "N"),
    },
    {
        "name": "IDOR (주문 정보 접근)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
        "params": ("N", "L", "L", "N", "U", "H", "N", "N"),
    },
    {
        "name": "보안 헤더 누락 (CSP)",
        "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N",
        "params": ("N", "H", "N", "R", "U", "L", "L", "N"),
    },
]

print(f"{'취약점':<35} {'CVSS':<6} {'등급':<10}")
print("-" * 55)

for v in vulns:                                        # 반복문 시작
    score = cvss_score(*v["params"])
    if score >= 9.0: grade = "Critical"
    elif score >= 7.0: grade = "High"
    elif score >= 4.0: grade = "Medium"
    elif score > 0: grade = "Low"
    else: grade = "None"
    print(f"{v['name']:<35} {score:<6.1f} {grade:<10}")
    print(f"  Vector: {v['vector']}")

PYEOF
ENDSSH
```

---

## 3. 취약점 상세 기술 작성 (25분)

### 3.1 취약점 카드 템플릿

```
[V-XXX] 취약점 제목
================================================================
심각도: Critical / High / Medium / Low
CVSS: X.X (벡터 문자열)
CWE: CWE-XXX (분류명)
OWASP: A01:2021 - 카테고리명
================================================================

1. 설명
   (취약점의 기술적 설명, 2-3문장)

2. 영향
   (비즈니스/기술적 영향, 구체적으로)

3. 재현 절차
   Step 1: ...
   Step 2: ...
   Step 3: ...

4. 증거
   (요청/응답 원문, 스크린샷)

5. 권고사항
   (구체적 수정 방법, 코드 예시 포함)

6. 참고자료
   (CWE, OWASP, CVE 링크)
================================================================
```

### 3.2 실습: SQL Injection 취약점 카드 작성

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
echo "=== 취약점 카드 작성 실습 ==="

# 재현 증거 수집
echo "--- Step 1: 정상 로그인 시도 ---"
curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"wrongpassword"}' | python3 -m json.tool 2>/dev/null || echo "JSON 파싱 실패"  # 요청 데이터(body)

echo ""
echo "--- Step 2: SQLi 페이로드 로그인 ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}")  # 요청 데이터(body)
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

echo ""
echo "--- Step 3: 응답 분석 ---"
echo "$RESULT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if 'authentication' in d:
        auth = d['authentication']
        print(f'인증 토큰 발급됨: {auth.get(\"token\",\"\")[:50]}...')
        print(f'사용자 이메일: {auth.get(\"umail\",\"N/A\")}')
        print('=> SQL Injection으로 인증 우회 확인')
    else:
        print(f'응답: {str(d)[:200]}')
except:
    print('응답 파싱 불가')
" 2>/dev/null
ENDSSH
```

### 3.3 보고서 자동 생성 스크립트

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
from datetime import datetime

report = f"""
================================================================
        웹 취약점 점검 보고서
================================================================
프로젝트: JuiceShop 보안 점검
점검 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
점검 대상: http://localhost:3000 (OWASP JuiceShop)
점검 방법: OWASP Testing Guide v4.2
점검 도구: curl, Python, 수동 점검
================================================================

1. 요약 (Executive Summary)
----------------------------------------------------------------
총 발견 취약점: 5건
  - Critical: 1건
  - High:     1건
  - Medium:   2건
  - Low:      1건

주요 발견사항:
  1) SQL Injection을 통한 인증 우회 (Critical)
  2) 저장형 XSS 공격 가능 (High)
  3) 불충분한 접근제어 (Medium)

전체 위험도 평가: 높음
  → SQL Injection으로 전체 데이터 유출 및 관리자 접근 가능

2. 점검 범위
----------------------------------------------------------------
  - 웹 애플리케이션: JuiceShop (Node.js + Angular)
  - API: REST API (/rest/*, /api/*)
  - 인증/세션 관리
  - 입력값 검증
  - 접근제어
  - 보안 설정

3. 발견사항 상세
----------------------------------------------------------------
[V-001] SQL Injection - 로그인 인증 우회
  심각도: Critical (CVSS 9.8)
  CWE: CWE-89 (SQL Injection)
  OWASP: A03:2021 - Injection

  설명: 로그인 API의 email 파라미터에서 SQL Injection이
  가능하여 인증을 우회할 수 있다.

  영향: 임의의 사용자(관리자 포함) 계정으로 로그인 가능.
  전체 고객 데이터, 주문 정보, 결제 정보 유출 위험.

  재현 절차:
    1. POST /rest/user/login
    2. Body: {{"email":"' OR 1=1--","password":"x"}}
    3. 결과: 인증 토큰 발급됨

  권고사항:
    - Parameterized Query(PreparedStatement) 사용
    - ORM 활용 (Sequelize 등)
    - 입력값 화이트리스트 검증

[V-002] Stored XSS - 상품 리뷰
  심각도: High (CVSS 6.1)
  CWE: CWE-79 (Cross-site Scripting)
  OWASP: A03:2021 - Injection

  설명: 상품 리뷰 작성 시 HTML/JavaScript 코드가
  필터링 없이 저장되어 다른 사용자에게 실행된다.

  권고사항:
    - 출력 시 HTML 엔티티 인코딩
    - CSP 헤더 적용
    - DOMPurify 라이브러리 적용

================================================================
보고서 끝
================================================================
"""

print(report)

# 파일로 저장
with open("/tmp/vuln_report.txt", "w") as f:
    f.write(report)
print("보고서 저장: /tmp/vuln_report.txt")

PYEOF
ENDSSH
```

---

## 4. 권고사항 작성과 우선순위화 (20분)

### 4.1 권고사항 우선순위 매트릭스

```
              구현 난이도
           낮음         높음
         +-------------------------+
  높음   | 즉시     | 계획     |  위
  위험도 | 시행     | 수립     |  험
         +----------+----------+  도
  낮음   | 일반     | 장기     |
  위험도 | 개선     | 과제     |
         +-------------------------+
```

### 4.2 권고사항 상세 작성 실습

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
recommendations = [
    {
        "vuln": "V-001 SQL Injection",
        "priority": "즉시 시행",
        "risk": "Critical",
        "effort": "Low",
        "recommendation": "Parameterized Query 적용",
        "code_before": "db.query('SELECT * FROM users WHERE email=\"' + email + '\"')",
        "code_after": "db.query('SELECT * FROM users WHERE email = ?', [email])",
    },
    {
        "vuln": "V-002 Stored XSS",
        "priority": "즉시 시행",
        "risk": "High",
        "effort": "Low",
        "recommendation": "출력 인코딩 + CSP 헤더",
        "code_before": "element.innerHTML = userReview",
        "code_after": "element.textContent = userReview  // 또는 DOMPurify.sanitize()",
    },
    {
        "vuln": "V-003 IDOR",
        "priority": "계획 수립",
        "risk": "Medium",
        "effort": "Medium",
        "recommendation": "서버사이드 권한 검증",
        "code_before": "GET /api/orders/:id  (id만 확인)",
        "code_after": "GET /api/orders/:id  (id + 세션 사용자 소유 확인)",
    },
]

print("=" * 70)
print("권고사항 상세")
print("=" * 70)

for idx, r in enumerate(recommendations, 1):           # 반복문 시작
    print(f"\n[R-{idx:03d}] {r['vuln']}")
    print(f"  우선순위: {r['priority']}")
    print(f"  위험도: {r['risk']} / 구현 난이도: {r['effort']}")
    print(f"  권고: {r['recommendation']}")
    print(f"  수정 전: {r['code_before']}")
    print(f"  수정 후: {r['code_after']}")

PYEOF
ENDSSH
```

---

## 5. LLM을 활용한 보고서 자동화 (20분)

### 5.1 취약점 설명 자동 생성

```bash
# Ollama LLM으로 취약점 설명 자동 생성
curl -s http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 컨설턴트입니다. 취약점 점검 보고서를 작성합니다. 한국어로 전문적이고 간결하게 작성하세요."},
      {"role": "user", "content": "다음 취약점의 보고서 항목을 작성하세요:\n\n취약점: SQL Injection\n위치: POST /rest/user/login (email 파라미터)\n페이로드: {\"email\":\"'"'"' OR 1=1--\",\"password\":\"x\"}\n결과: 인증 토큰 발급 (관리자 계정 포함)\n\n[설명], [영향], [권고사항]을 각각 2-3문장으로 작성하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 5.2 권고사항 코드 자동 생성

```bash
curl -s http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{                                                # 요청 데이터(body)
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Node.js/Express 보안 전문가입니다. 취약점 수정 코드를 제시합니다."},
      {"role": "user", "content": "SQL Injection 취약점이 있는 로그인 코드를 Sequelize ORM으로 안전하게 수정하는 코드를 보여주세요.\n\n취약한 코드:\nconst query = \"SELECT * FROM Users WHERE email = '"'"'\" + req.body.email + \"'"'"'\";\ndb.query(query)\n\n수정된 코드를 작성하세요."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 보고서 품질 체크리스트 (10분)

### 6.1 자가 점검 항목

원격 서버에 접속하여 명령을 실행합니다.

```bash
ssh ccc@10.20.30.80 << 'ENDSSH'  # 비밀번호 자동입력 SSH
python3 << 'PYEOF'                                     # Python 스크립트 실행
checklist = [
    ("표지", "프로젝트명, 일시, 점검 범위, 점검자 정보"),
    ("요약", "비기술 경영진도 이해할 수 있는 수준"),
    ("통계", "심각도별 취약점 수 그래프/표"),
    ("재현성", "모든 취약점에 단계별 재현 절차"),
    ("증거", "요청/응답 원문 또는 스크린샷 첨부"),
    ("CVSS", "모든 취약점에 CVSS 벡터 + 점수"),
    ("CWE", "모든 취약점에 CWE ID 부여"),
    ("영향", "비즈니스 관점 영향 분석"),
    ("권고", "구체적 코드/설정 수정 방법 제시"),
    ("우선순위", "위험도 + 난이도 기반 우선순위"),
    ("참고자료", "OWASP, CWE, CVE 링크"),
    ("맞춤법", "전문 용어 통일, 오타 없음"),
]

print("취약점 점검 보고서 품질 체크리스트")
print("=" * 55)
for idx, (item, desc) in enumerate(checklist, 1):      # 반복문 시작
    print(f"  [ ] {idx:2d}. {item:<10} - {desc}")

print(f"\n총 {len(checklist)}개 항목")

PYEOF
ENDSSH
```

---

## 핵심 정리

1. 취약점 보고서는 재현성, 증거, 비즈니스 영향이 핵심이다
2. CVSS v3.1로 객관적 심각도를 산출하고 우선순위를 결정한다
3. 권고사항은 구체적 코드/설정 수준으로 제시해야 한다
4. 경영진용(요약)과 개발팀용(상세)을 분리하여 작성한다
5. LLM을 활용하면 보고서 초안 작성 효율을 높일 수 있다
6. 품질 체크리스트로 보고서 완성도를 검증한다

---

## 다음 주 예고
- Week 15: 기말 종합 웹취약점 점검 프로젝트

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### 보고서 도구 (CVSS 계산기·Markdown·ReportLab)
> **역할:** 취약점 보고서 표준화  
> **실행 위치:** `작업 PC`  
> **접속/호출:** FIRST CVSS 계산기 https://www.first.org/cvss/calculator/3.1

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `reports/<project>/` | 재현 스크린샷·증적 저장 |
| `template.md / template.docx` | 표준 템플릿 |

**핵심 설정·키**

- `CVSS 3.1 벡터 예: AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` — Critical 9.8
- `CWE ID + 권고 (remediation)` — 보고서 필수 항목

**UI / CLI 요점**

- MermaidJS 공격 흐름도 — 교안/보고서 공통 도식
- Pandoc `md → docx/pdf` — 포맷 변환

> **해석 팁.** 보고서 가치는 **재현 절차의 완결성**에 달려 있다. 스크린샷·요청/응답 전체·시간 기록을 포함해야 고객이 독립 검증 가능.

---

## 실제 사례 (WitFoo Precinct 6)

> **출처**: [WitFoo Precinct 6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity) (Apache 2.0)
> **익명화**: RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 sanitized

본 주차 (14주차) 학습 주제와 직접 연관된 *실제* incident:

### Data Theft (T1041) — 99.99% 의 dataset 패턴

> **출처**: WitFoo Precinct 6 / `complete-mission cluster` (anchor: `anc-a0364e702393`) · sanitized
> **시점**: 다중 (전체 99.99%)

**관찰**: Precinct 6 의 incident 10,442건 중 mo_name=Data Theft + lifecycle=complete-mission 이 99.99%. T1041 (Exfiltration over C2 Channel).

**MITRE ATT&CK**: **T1041 (Exfiltration over C2 Channel)**

**IoC**:
  - `다양한 src→dst (sanitized)`
  - `suspicion≥0.7`

**학습 포인트**:
- *가장 많이 일어나는 공격* 의 baseline — 모든 IR 시나리오의 출발점
- C2 채널 (HTTP/HTTPS/DNS) 에 데이터 mixed → 정상 트래픽 위장
- 탐지: outbound 에 데이터 흐름 모니터링 (bytes_out 분포), CTI feed 매칭
- 방어: DLP (Data Loss Prevention), egress filter, 데이터 분류·암호화


**본 강의와의 연결**: 위 사례는 강의의 핵심 개념이 어떻게 *실제 운영 환경*에서 일어나는지 보여준다. 학생은 이 패턴을 (1) 공격자 입장에서 재현 가능한가 (2) 방어자 입장에서 탐지 가능한가 (3) 자기 인프라에서 동일 신호가 있는지 검색 가능한가 — 3 관점에서 평가한다.

---

> 더 많은 사례 (총 5 anchor + 외부 표준 7 source) 는 KG (Knowledge Graph) 페이지에서 검색 가능.
> Cyber Range 실습 중 학습 포인트 박스 (📖) 에 동일 anchor 가 자동 노출된다.
