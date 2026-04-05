# Week 10: 암호화 / 통신 보안 점검

## 학습 목표
- HTTPS의 동작 원리와 TLS 핸드셰이크를 이해한다
- SSL/TLS 인증서를 점검하고 문제를 식별할 수 있다
- 약한 암호 스위트(Cipher Suite)를 판별할 수 있다
- 웹 애플리케이션의 암호화 구현을 점검한다

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

# Week 10: 암호화 / 통신 보안 점검

## 학습 목표
- HTTPS의 동작 원리와 TLS 핸드셰이크를 이해한다
- SSL/TLS 인증서를 점검하고 문제를 식별할 수 있다
- 약한 암호 스위트(Cipher Suite)를 판별할 수 있다
- 웹 애플리케이션의 암호화 구현을 점검한다

## 전제 조건
- HTTP vs HTTPS 차이 이해
- 공개키/대칭키 암호화 기본 개념

---

## 1. HTTPS와 TLS 개요 (20분)

### 1.1 HTTPS가 보호하는 것

| 보호 항목 | 설명 | 위협 |
|----------|------|------|
| **기밀성** | 통신 내용 암호화 | 도청 (Eavesdropping) |
| **무결성** | 데이터 변조 방지 | 중간자 공격 (MITM) |
| **인증** | 서버 신원 확인 | 피싱, DNS 스푸핑 |

### 1.2 TLS 핸드셰이크 과정

```
클라이언트                                      서버

  ---- ClientHello (지원 암호목록) ----------->
  <--- ServerHello (선택 암호) ----------------
  <--- Certificate (인증서) -------------------
  <--- ServerHelloDone ------------------------

  ---- ClientKeyExchange --------------------->
  ---- ChangeCipherSpec ---------------------->
  ---- Finished ------------------------------>

  <--- ChangeCipherSpec -----------------------
  <--- Finished -------------------------------

  ========= 암호화된 통신 시작 ================
```

### 1.3 TLS 버전별 보안

| 버전 | 상태 | 비고 |
|------|------|------|
| SSL 2.0 | 폐기 | 심각한 취약점 |
| SSL 3.0 | 폐기 | POODLE 공격 |
| TLS 1.0 | 폐기 | BEAST 공격 |
| TLS 1.1 | 폐기 | 약한 암호 |
| **TLS 1.2** | **사용** | 현재 최소 기준 |
| **TLS 1.3** | **권장** | 최신, 가장 안전 |

---

## 2. 실습 환경 통신 보안 점검 (20분)

> **이 실습을 왜 하는가?**
> "암호화 / 통신 보안 점검" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> 웹 취약점 점검 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

### 2.1 HTTP/HTTPS 지원 확인

> **실습 목적**: HTTPS 적용 여부, TLS 버전, 암호화 스위트 등 통신 보안을 점검한다
>
> **배우는 것**: SSL/TLS 설정의 적정성, 인증서 유효성, 평문 전송 여부를 확인하는 방법을 배운다
>
> **결과 해석**: HTTP만 지원하거나 취약한 TLS 버전(1.0/1.1)을 사용하면 통신 보안 취약점이다
>
> **실전 활용**: 금융/의료 등 규제 산업에서 TLS 1.2 이상과 강력한 암호화 스위트는 필수 요구사항이다

```bash
# JuiceShop - HTTP
echo "=== JuiceShop (포트 3000) ==="
curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://10.20.30.80:3000

# JuiceShop - HTTPS 시도
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://10.20.30.80:3000 2>/dev/null || echo "HTTPS: 미지원"

# Apache - HTTP
echo ""
echo "=== Apache (포트 80) ==="
curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://10.20.30.80:80

# Apache - HTTPS (포트 443)
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://10.20.30.80:443 2>/dev/null || echo "HTTPS: 미지원"
```

### 2.2 HTTP → HTTPS 리다이렉트 확인

```bash
# HTTP 요청 시 HTTPS로 리다이렉트하는지 확인
echo "=== 리다이렉트 확인 ==="
curl -sI http://10.20.30.80:80 | grep -i "location"
curl -sI http://10.20.30.80:3000 | grep -i "location"

# 리다이렉트가 없으면 → 평문 통신 가능 (취약)
```

### 2.3 HSTS(HTTP Strict Transport Security) 점검

```bash
# HSTS 헤더 확인
echo "=== HSTS 헤더 ==="
curl -sI http://10.20.30.80:80 | grep -i "strict-transport"
curl -sI http://10.20.30.80:3000 | grep -i "strict-transport"

# HSTS가 없으면:
# - 사용자가 http://로 접속하면 평문 통신
# - SSL 스트리핑 공격에 취약
```

---

## 3. SSL/TLS 인증서 점검 (30분)

### 3.1 openssl로 인증서 분석

```bash
# 실습 서버가 HTTPS를 지원하는 경우 인증서 분석
# (실습 서버가 HTTP만 지원하면 외부 사이트로 개념 학습)

# 인증서 기본 정보 확인
echo "=== 실습 서버 인증서 확인 ==="
echo | openssl s_client -connect 10.20.30.80:443 -servername 10.20.30.80 2>/dev/null | openssl x509 -noout -text 2>/dev/null | head -30 || echo "TLS 미지원 - 외부 사이트로 실습"

# 개념 학습용: 공개 사이트 인증서 분석
echo ""
echo "=== 공개 사이트 인증서 분석 (학습용) ==="
echo | openssl s_client -connect www.google.com:443 -servername www.google.com 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>/dev/null
```

### 3.2 인증서 점검 항목

| 점검 항목 | 정상 | 취약 |
|----------|------|------|
| 유효기간 | 만료 전 | 만료됨 |
| 발급자 | 신뢰 CA (DigiCert, Let's Encrypt 등) | 자체 서명 |
| CN/SAN | 도메인 일치 | 불일치 |
| 키 길이 | RSA 2048+ / ECDSA 256+ | RSA 1024 이하 |
| 서명 알고리즘 | SHA-256+ | SHA-1, MD5 |
| 인증서 체인 | 완전한 체인 | 중간 인증서 누락 |

### 3.3 인증서 점검 스크립트

```bash
# 인증서 종합 점검 스크립트 (HTTPS 지원 사이트 대상)
python3 << 'PYEOF'                                     # Python 스크립트 실행
import subprocess, re, sys
from datetime import datetime

target = "www.google.com"  # HTTPS 지원 사이트
port = 443

print(f"=== {target}:{port} 인증서 점검 ===\n")

# 인증서 정보 추출
cmd = f"echo | openssl s_client -connect {target}:{port} -servername {target} 2>/dev/null"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

# 인증서 상세 정보
cmd2 = f"{cmd} | openssl x509 -noout -subject -issuer -dates -serial -fingerprint"
result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
print(result2.stdout)

# 키 길이 확인
cmd3 = f"{cmd} | openssl x509 -noout -text | grep 'Public-Key'"
result3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
print(f"키 길이: {result3.stdout.strip()}")

# TLS 버전 확인
cmd4 = f"echo | openssl s_client -connect {target}:{port} 2>/dev/null | grep 'Protocol'"
result4 = subprocess.run(cmd4, shell=True, capture_output=True, text=True)
print(f"TLS 버전: {result4.stdout.strip()}")

# 서명 알고리즘
cmd5 = f"{cmd} | openssl x509 -noout -text | grep 'Signature Algorithm' | head -1"
result5 = subprocess.run(cmd5, shell=True, capture_output=True, text=True)
print(f"서명 알고리즘: {result5.stdout.strip()}")
PYEOF
```

---

## 4. 암호 스위트 점검 (30분)

### 4.1 Cipher Suite란?

Cipher Suite는 TLS 통신에서 사용되는 암호화 알고리즘의 조합이다.

```
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384

각 필드 설명:
  TLS      --> 프로토콜
  ECDHE    --> 키 교환
  RSA      --> 인증
  AES      --> 암호화 알고리즘
  256      --> 키 크기
  GCM      --> 블록 모드
  SHA384   --> MAC (무결성)
```

### 4.2 약한 암호 스위트 목록

| 암호 | 문제 | 권장 |
|------|------|------|
| RC4 | 바이어스 공격 | 사용 금지 |
| DES / 3DES | 짧은 키 길이 | 사용 금지 |
| MD5 | 충돌 공격 | SHA-256+ 사용 |
| SHA-1 | 충돌 공격 (2017) | SHA-256+ 사용 |
| CBC 모드 | BEAST, Lucky13 | GCM 모드 사용 |
| RSA 키 교환 | PFS 미지원 | ECDHE 사용 |
| NULL 암호화 | 암호화 안함 | 절대 사용 금지 |

### 4.3 서버의 암호 스위트 점검

```bash
# 서버가 지원하는 암호 스위트 확인 (HTTPS 사이트 대상)
echo "=== 지원 암호 스위트 확인 ==="

# nmap을 이용한 점검 (설치되어 있다면)
which nmap > /dev/null 2>&1 && \
  nmap --script ssl-enum-ciphers -p 443 www.google.com 2>/dev/null | head -40 || \
  echo "nmap 미설치 - openssl로 수동 점검"

# openssl로 특정 암호 스위트 테스트
echo ""
echo "=== 약한 암호 스위트 개별 테스트 ==="

WEAK_CIPHERS=("RC4" "DES" "3DES" "NULL" "EXPORT" "MD5")
for cipher in "${WEAK_CIPHERS[@]}"; do                 # 반복문 시작
  result=$(echo | openssl s_client -connect www.google.com:443 -cipher "$cipher" 2>&1 | head -1)
  if echo "$result" | grep -q "CONNECTED"; then
    echo "[취약] $cipher 지원됨!"
  else
    echo "[양호] $cipher 미지원"
  fi
done
```

### 4.4 TLS 버전별 지원 확인

```bash
# 각 TLS 버전 지원 여부 확인
echo "=== TLS 버전 지원 확인 (google.com) ==="

for version in ssl3 tls1 tls1_1 tls1_2 tls1_3; do      # 반복문 시작
  result=$(echo | openssl s_client -connect www.google.com:443 -$version 2>&1 | grep "Protocol")
  if echo "$result" | grep -qi "protocol"; then
    echo "[지원] $version: $result"
  else
    echo "[미지원] $version"
  fi
done 2>/dev/null
```

---

## 5. 웹 애플리케이션 암호화 점검 (20분)

### 5.1 비밀번호 저장 방식

```bash
# JuiceShop 사용자 비밀번호 해시 확인
# SQLi로 해시 추출 (Week 05에서 학습)
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users+LIMIT+3--" | python3 -c "  # silent 모드
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    for item in data:                                  # 반복문 시작
        name = str(item.get('name', ''))
        desc = str(item.get('description', ''))
        if '@' in name:
            # 해시 형식 분석
            hash_val = desc
            if len(hash_val) == 32:
                algo = 'MD5 (취약!)'
            elif len(hash_val) == 40:
                algo = 'SHA-1 (취약!)'
            elif len(hash_val) == 64:
                algo = 'SHA-256'
            elif hash_val.startswith('\$2'):
                algo = 'bcrypt (양호)'
            else:
                algo = f'알 수 없음 (길이={len(hash_val)})'
            print(f'{name}: {hash_val[:20]}... → {algo}')
except:
    print('데이터 추출 실패')
" 2>/dev/null
```

### 5.2 민감 정보 평문 전송 확인

```bash
# 로그인 요청이 HTTP(평문)로 전송되는지 확인
echo "=== 로그인 API 프로토콜 ==="
echo "현재 로그인 URL: http://10.20.30.80:3000/rest/user/login"
echo "프로토콜: HTTP (암호화 안됨)"
echo ""
echo "문제: 비밀번호가 네트워크에서 평문으로 전송됨"
echo "권고: HTTPS 적용 필수"

# API 응답에 민감 정보가 포함되는지 확인
echo ""
echo "=== API 응답 민감 정보 확인 ==="
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)  # 요청 데이터(body)

# 로그인 응답에 비밀번호 해시가 포함되는지
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "  # 요청 데이터(body)
import sys, json
data = json.load(sys.stdin)
auth = data.get('authentication', {})
print('로그인 응답 필드:')
for key in auth.keys():                                # 반복문 시작
    val = str(auth[key])
    if key == 'token':
        val = val[:30] + '...'
    print(f'  {key}: {val}')
" 2>/dev/null
```

### 5.3 쿠키 보안 속성

```bash
echo "=== 쿠키 보안 속성 점검 ==="
curl -sI http://10.20.30.80:3000 | grep -i "set-cookie" | while read -r line; do
  echo "쿠키: $line"
  echo "$line" | grep -qi "secure" && echo "  Secure: 설정됨" || echo "  Secure: 미설정 (HTTP로 전송 가능)"
  echo "$line" | grep -qi "httponly" && echo "  HttpOnly: 설정됨" || echo "  HttpOnly: 미설정 (JS 접근 가능)"
  echo "$line" | grep -qi "samesite" && echo "  SameSite: 설정됨" || echo "  SameSite: 미설정 (CSRF 위험)"
  echo ""
done
```

---

## 6. 실습 과제

### 과제 1: 통신 보안 점검
1. 실습 서버(JuiceShop, Apache)의 HTTP/HTTPS 지원 현황을 정리하라
2. HSTS, 리다이렉트 설정 여부를 확인하라
3. 점검 결과를 기반으로 통신 보안 개선 권고를 작성하라

### 과제 2: 인증서 분석
1. 공개 웹사이트 3개의 인증서를 분석하라 (발급자, 유효기간, 키 길이, 서명 알고리즘)
2. 분석 결과를 비교표로 정리하라
3. 인증서 관련 모범 사례(Best Practice)를 3가지 이상 서술하라

### 과제 3: 암호화 종합 점검
1. JuiceShop의 비밀번호 해시 알고리즘을 확인하라
2. 쿠키의 보안 속성(Secure, HttpOnly, SameSite)을 점검하라
3. 민감 정보가 평문으로 전송/저장되는 곳을 찾아 보고하라

---

## 7. 요약

| 점검 항목 | 도구 | 양호 기준 |
|----------|------|----------|
| HTTPS 지원 | curl | 모든 페이지 HTTPS 필수 |
| TLS 버전 | openssl | TLS 1.2 이상만 허용 |
| 인증서 | openssl | 신뢰 CA, 유효기간 내, SHA-256+ |
| 암호 스위트 | nmap, openssl | RC4/DES/NULL 미사용 |
| HSTS | curl -I | 헤더 설정됨 |
| 비밀번호 해시 | SQLi 결과 분석 | bcrypt/scrypt/Argon2 |
| 쿠키 보안 | curl -I | Secure+HttpOnly+SameSite |

**다음 주 예고**: Week 11 - 에러 처리/정보 노출. 스택 트레이스, 디버그 모드, 디렉터리 리스팅을 학습한다.

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
