# Week 02: 취약점 스캐닝

## 학습 목표
- 취약점 스캐닝의 개념과 모의해킹 프로세스에서의 위치를 이해한다
- 취약점과 익스플로잇의 관계, CVE/CVSS 체계를 정확히 설명할 수 있다
- nmap NSE 스크립트를 활용하여 자동화된 취약점 탐지를 수행할 수 있다
- Nikto를 사용하여 웹 서버의 보안 취약점을 스캔할 수 있다
- 취약점 스캔 결과를 분석하고 위험도를 기반으로 우선순위를 매길 수 있다
- 오탐(False Positive)과 미탐(False Negative)을 식별하고 검증하는 방법을 이해한다
- Blue Team 관점에서 취약점 스캔을 탐지하고 자산 관리에 활용하는 방법을 안다

## 전제 조건
- Week 01 정찰 기초 완료 (nmap 기본 사용법 숙지)
- TCP/IP 및 HTTP 프로토콜 기본 이해
- CVE, CVSS 기본 개념 이해

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 취약점 스캐닝 이론 + CVE/CVSS 체계 | 강의 |
| 0:40-1:10 | 취약점 스캐닝 도구 소개 + 방법론 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | nmap NSE 취약점 스캔 실습 | 실습 |
| 2:00-2:30 | Nikto 웹 취약점 스캔 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 취약점 분석 + 보고서 작성 | 실습 |
| 3:10-3:40 | 오탐 검증 + 퀴즈 + 과제 안내 | 토론/퀴즈 |

---

# Part 1: 취약점 스캐닝 이론 (40분)

## 1.1 취약점 스캐닝이란?

취약점 스캐닝(Vulnerability Scanning)은 시스템, 네트워크, 애플리케이션에서 알려진 보안 약점을 자동으로 탐지하는 과정이다. 정찰(Reconnaissance)에서 수집한 정보를 바탕으로 구체적인 취약점을 식별하는 단계에 해당한다.

**모의해킹 프로세스에서의 위치:**
```
[1] 정보 수집 (Week 01)
    ↓ 호스트, 포트, 서비스 버전 확보
[2] 취약점 스캐닝 (Week 02) ← 현재 단계
    ↓ 취약점 목록 + 위험도 분류
[3] 취약점 활용/공격 (Week 03~05)
    ↓ 실제 침투
[4] 후속 활동 (Week 05~09)
```

**MITRE ATT&CK 매핑:**
```
전술: TA0043 — Reconnaissance
  +-- T1595.002 — Vulnerability Scanning
        +-- 절차: nmap --script=vuln, Nikto, OpenVAS 등으로 알려진 취약점 탐지
```

### 취약점 스캐닝 vs 침투 테스트

| 구분 | 취약점 스캐닝 | 침투 테스트 |
|------|-------------|-----------|
| 목적 | 취약점 존재 여부 확인 | 취약점 실제 악용 가능 여부 확인 |
| 자동화 | 대부분 자동 | 수동 + 자동 혼합 |
| 위험도 | 시스템에 영향 적음 | 시스템에 영향 있을 수 있음 |
| 결과 | 잠재적 취약점 목록 | 실제 공격 성공/실패 증거 |
| 오탐률 | 높을 수 있음 | 낮음 (직접 검증) |
| 소요 시간 | 수 분~수 시간 | 수 일~수 주 |

## 1.2 CVE/CVSS 체계 상세

### CVE (Common Vulnerabilities and Exposures)

CVE는 공개적으로 알려진 보안 취약점에 고유 번호를 부여하는 시스템이다.

| 항목 | 설명 |
|------|------|
| 관리 기관 | MITRE Corporation |
| 형식 | CVE-연도-일련번호 (예: CVE-2024-12345) |
| 목적 | 취약점에 대한 공통 식별자 제공 |
| 참조 | https://cve.mitre.org |

**CVE 생명주기:**
```
[1] 취약점 발견 → [2] CVE ID 예약 → [3] 패치/공개 → [4] NVD 등록 → [5] 스캐너 시그니처 업데이트
```

**주요 CVE 사례:**

| CVE | 이름 | 영향 | CVSS | 관련 서비스 |
|-----|------|------|------|-----------|
| CVE-2021-44228 | Log4Shell | Java 앱 원격 코드 실행 | 10.0 | Log4j |
| CVE-2017-0144 | EternalBlue | Windows SMB 원격 실행 | 9.3 | SMBv1 |
| CVE-2014-0160 | Heartbleed | OpenSSL 메모리 유출 | 7.5 | OpenSSL |
| CVE-2023-25690 | HTTP Smuggling | Apache 요청 밀수 | 9.8 | Apache 2.4.x |
| CVE-2022-0847 | DirtyPipe | Linux 커널 권한 상승 | 7.8 | Linux Kernel |

### CVSS (Common Vulnerability Scoring System)

CVSS는 취약점의 심각도를 0.0~10.0 점수로 수치화하는 표준이다.

**CVSS v3.1 점수 분류:**

| 등급 | 점수 범위 | 색상 | 대응 시급도 |
|------|---------|------|-----------|
| None | 0.0 | 회색 | 참고 |
| Low | 0.1-3.9 | 녹색 | 계획 시 반영 |
| Medium | 4.0-6.9 | 황색 | 다음 패치 주기 |
| High | 7.0-8.9 | 주황 | 빠른 대응 필요 |
| Critical | 9.0-10.0 | 적색 | 즉시 대응 |

**CVSS v3.1 기본 메트릭:**

| 메트릭 | 약어 | 설명 | 값 예시 |
|--------|------|------|--------|
| Attack Vector | AV | 공격 경로 | Network/Adjacent/Local/Physical |
| Attack Complexity | AC | 공격 복잡도 | Low/High |
| Privileges Required | PR | 필요 권한 | None/Low/High |
| User Interaction | UI | 사용자 개입 | None/Required |
| Scope | S | 영향 범위 | Unchanged/Changed |
| Confidentiality | C | 기밀성 영향 | None/Low/High |
| Integrity | I | 무결성 영향 | None/Low/High |
| Availability | A | 가용성 영향 | None/Low/High |

**CVSS 벡터 문자열 예시:**
```
CVE-2021-44228 (Log4Shell):
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H = 10.0 (Critical)

해석:
- AV:N (Network)    — 네트워크를 통해 원격 공격 가능
- AC:L (Low)        — 공격 복잡도 낮음 (간단한 문자열 전송)
- PR:N (None)       — 권한 불필요
- UI:N (None)       — 사용자 개입 불필요
- S:C (Changed)     — 다른 컴포넌트까지 영향
- C:H/I:H/A:H      — 기밀성/무결성/가용성 모두 완전 손상
```

## 1.3 CWE (Common Weakness Enumeration)

CWE는 취약점의 **유형(카테고리)**을 분류하는 체계이다. CVE가 "특정 제품의 특정 취약점"이라면, CWE는 "그 취약점이 속하는 약점 유형"이다.

**CWE Top 25 (2024) 중 실습 관련:**

| 순위 | CWE | 이름 | 설명 | 실습 주차 |
|------|-----|------|------|---------|
| 1 | CWE-79 | Cross-site Scripting (XSS) | 스크립트 삽입 | Week 03 |
| 2 | CWE-89 | SQL Injection | SQL 쿼리 삽입 | Week 03 |
| 3 | CWE-787 | Out-of-bounds Write | 버퍼 오버플로 | - |
| 6 | CWE-22 | Path Traversal | 경로 탈출 | Week 03 |
| 8 | CWE-862 | Missing Authorization | 인가 누락 | Week 05 |
| 13 | CWE-269 | Improper Privilege Mgmt | 권한 관리 부실 | Week 05 |
| 15 | CWE-434 | Unrestricted Upload | 파일 업로드 | Week 03 |

## 1.4 취약점 스캐닝 도구 분류

| 도구 | 유형 | 대상 | 라이선스 | 특징 |
|------|------|------|---------|------|
| **nmap NSE** | 네트워크/서비스 | 호스트, 포트, 서비스 | 오픈소스 | 유연한 스크립팅, 가벼움 |
| **Nikto** | 웹 서버 | HTTP/HTTPS | 오픈소스 | 6,700+ 항목 검사 |
| **OpenVAS** | 종합 | 네트워크 전체 | 오픈소스 | 50,000+ 취약점 시그니처 |
| **Nessus** | 종합 | 네트워크 전체 | 상용 | 산업 표준, 정확도 높음 |
| **Nuclei** | 웹/네트워크 | 다양 | 오픈소스 | YAML 템플릿 기반 |
| **WPScan** | 웹 (WordPress) | WordPress | 오픈소스 | WordPress 전용 |

### 도구 선택 기준

```
간단한 서비스 취약점 확인 → nmap NSE (--script=vuln)
웹 서버 설정 오류 확인    → Nikto
전체 인프라 종합 평가     → OpenVAS / Nessus
특정 취약점 타겟 확인     → Nuclei (YAML 템플릿)
WordPress 사이트         → WPScan
```

---

# Part 2: 취약점 스캐닝 방법론 (30분)

## 2.1 체계적 취약점 스캐닝 워크플로

```
[1] 스코프 정의
    +-- 대상 IP/포트 범위 확인
    +-- 스캔 허용 시간대 확인
    +-- 제외 대상 목록 확인
    ↓
[2] 사전 정보 활용
    +-- Week 01 정찰 결과 로딩 (/tmp/full_scan.xml)
    +-- 서비스 버전 목록 확인
    +-- 알려진 CVE 사전 조사
    ↓
[3] 자동화 스캔 실행
    +-- nmap NSE vuln 카테고리
    +-- Nikto (웹 서버)
    +-- 서비스별 특화 스크립트
    ↓
[4] 결과 분석
    +-- 오탐/미탐 필터링
    +-- CVSS 기반 우선순위 부여
    +-- 검증 테스트 실행
    ↓
[5] 보고서 작성
    +-- 취약점 목록 (CVSS 내림차순)
    +-- 재현 방법
    +-- 권장 대응 방안
```

## 2.2 nmap NSE 취약점 스크립트 상세

### vuln 카테고리 스크립트 주요 목록

| 스크립트 | 대상 | 탐지하는 취약점 | CVE 참조 |
|---------|------|---------------|---------|
| `ssl-heartbleed` | SSL/TLS | Heartbleed 메모리 유출 | CVE-2014-0160 |
| `ssl-poodle` | SSLv3 | POODLE 패딩 오라클 | CVE-2014-3566 |
| `http-shellshock` | HTTP CGI | Shellshock bash 취약점 | CVE-2014-6271 |
| `smb-vuln-ms17-010` | SMB | EternalBlue | CVE-2017-0144 |
| `http-sql-injection` | HTTP | SQL 삽입 | CWE-89 |
| `http-xssed` | HTTP | 반사형 XSS | CWE-79 |
| `http-vuln-cve2017-5638` | Struts | Apache Struts RCE | CVE-2017-5638 |
| `ssl-cert` | SSL | 인증서 정보 노출 | - |
| `ssl-enum-ciphers` | SSL/TLS | 약한 암호 스위트 | - |

### safe 카테고리 vs vuln 카테고리

| 카테고리 | 안전성 | 대상 영향 | 사용 시나리오 |
|---------|--------|---------|-------------|
| `safe` | 높음 | 없음 | 운영 환경에서 안전하게 정보 수집 |
| `default` | 높음 | 미미 | 기본 정보 수집 (`-sC`) |
| `vuln` | 중간 | 약간 | 알려진 취약점 탐지 (일부 침입적) |
| `exploit` | 낮음 | 있음 | 실제 공격 시도 (사전 허가 필수) |
| `intrusive` | 낮음 | 있음 | 서비스 중단 가능 |

## 2.3 Nikto 웹 스캐너 상세

Nikto는 웹 서버의 알려진 취약점, 설정 오류, 위험한 파일 등을 자동으로 검사하는 도구이다.

**검사 항목:**

| 카테고리 | 검사 내용 | 항목 수 |
|---------|---------|--------|
| 서버 설정 | 디렉토리 리스팅, 기본 파일, 헤더 | ~1,250 |
| 알려진 취약점 | CVE 기반 취약점 | ~6,700 |
| 버전별 취약점 | 소프트웨어 버전 매칭 | ~1,200 |
| 위험 파일 | 백업, 설정, 로그 노출 | ~900 |
| CGI 취약점 | CGI 스크립트 관련 | ~400 |

**Nikto 주요 옵션:**

| 옵션 | 설명 | 예시 |
|------|------|------|
| `-h` | 대상 호스트 | `-h 10.20.30.80` |
| `-p` | 대상 포트 | `-p 80,3000` |
| `-o` | 결과 저장 | `-o /tmp/nikto_result.txt` |
| `-Format` | 출력 포맷 | `-Format htm` (HTML 보고서) |
| `-Tuning` | 검사 유형 선택 | `-Tuning 1234` |
| `-ssl` | SSL/TLS 사용 | `-ssl` |
| `-timeout` | 타임아웃 | `-timeout 10` |

**Tuning 값:**

| 값 | 검사 유형 |
|----|---------|
| 1 | 흥미로운 파일/로그 |
| 2 | 설정 오류 |
| 3 | 정보 유출 |
| 4 | XSS/Script Injection |
| 5 | 원격 파일 검색 |
| 6 | DoS (위험) |
| 7 | 원격 파일 획득 |
| 8 | 명령 실행 |
| 9 | SQL Injection |
| 0 | 파일 업로드 |

## 2.4 취약점 스캔 결과 해석 프레임워크

### 오탐(False Positive)과 미탐(False Negative)

| 유형 | 정의 | 위험성 | 대응 |
|------|------|--------|------|
| 오탐 (FP) | 취약점이 없는데 있다고 보고 | 시간 낭비, 리소스 낭비 | 수동 검증 |
| 미탐 (FN) | 취약점이 있는데 탐지 못함 | 보안 위협 지속 | 다중 도구 사용 |
| 참양성 (TP) | 실제 취약점을 정확히 탐지 | 없음 (바람직) | 즉시 대응 |
| 참음성 (TN) | 취약점 없음을 정확히 판단 | 없음 (바람직) | - |

### 오탐 검증 방법

```
[1] 수동 확인: 해당 서비스에 직접 접근하여 취약점 재현 시도
[2] 버전 비교: 스캐너가 탐지한 버전과 실제 버전 대조
[3] 패치 확인: 해당 CVE의 패치가 적용되었는지 확인
[4] 교차 검증: 다른 도구로 동일 취약점 재탐지
[5] 설정 확인: 취약한 기능이 실제로 활성화되어 있는지 확인
```

---

# Part 3: nmap NSE 취약점 스캔 실습 (40분)

## 실습 3.1: vuln 카테고리 스크립트 실행

### Step 1: web 서버 종합 취약점 스캔

> **실습 목적**: nmap의 vuln 카테고리 스크립트로 web 서버의 알려진 취약점을 자동 탐지한다.
>
> **배우는 것**: NSE vuln 스크립트의 실행 방법과 결과 해석

```bash
# web 서버 vuln 스크립트 전체 실행
echo 1 | sudo -S nmap --script=vuln -p 22,80,3000 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# | vulners:
# |   cpe:/a:openbsd:openssh:8.9p1:
# |     CVE-2023-xxxxx  7.5  https://vulners.com/cve/CVE-2023-xxxxx
# 80/tcp   open  http
# | http-csrf:
# |   Spidering limited to: maxdepth=3; maxpagecount=20
# |   Found potential CSRF ...
# | http-enum:
# |   /icons/: Potentially interesting folder
# |   /server-status: Apache server-status (protected)
# 3000/tcp open  ppp
# | http-xssed:
# |   OSVDB-XXXXX
# |_  Description: Potential XSS vulnerability
```

> **결과 해석**:
> - `vulners`: 서비스 버전과 매칭되는 CVE 목록 자동 표시
> - `http-csrf`: CSRF(Cross-Site Request Forgery) 가능성 탐지
> - `http-enum`: 흥미로운 디렉토리/파일 발견
> - `http-xssed`: XSS 취약점 가능성 탐지 (오탐 가능, 검증 필요)
>
> **실전 활용**: vuln 스크립트의 결과는 "가능성"이다. 실제 공격 가능 여부는 Week 03에서 수동 검증한다.
>
> **명령어 해설**:
> - `--script=vuln`: vuln 카테고리의 모든 스크립트 실행
> - 실행 시간: 포트당 30초~2분 소요될 수 있음
>
> **트러블슈팅**:
> - 스크립트 실행이 매우 오래 걸림: `--script-timeout 60s`로 타임아웃 설정
> - "Script Pre-scanning": 정상 동작, 스크립트 초기화 단계

### Step 2: SSL/TLS 취약점 스캔

> **실습 목적**: HTTPS 서비스의 SSL/TLS 설정 취약점을 탐지한다.
>
> **배우는 것**: SSL 관련 NSE 스크립트와 암호 스위트 분석

```bash
# siem 서버의 Wazuh Dashboard SSL 검사
echo 1 | sudo -S nmap --script=ssl-cert,ssl-enum-ciphers -p 443 10.20.30.100
# 예상 출력:
# PORT    STATE SERVICE
# 443/tcp open  https
# | ssl-cert:
# |   Subject: commonName=wazuh-dashboard/...
# |   Issuer: commonName=wazuh-root-ca/...
# |   Not valid before: 2024-xx-xxT...
# |   Not valid after:  2025-xx-xxT...
# | ssl-enum-ciphers:
# |   TLSv1.2:
# |     ciphers:
# |       TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (ecdh_x25519) - A
# |       TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (ecdh_x25519) - A
# |   TLSv1.3:
# |     ciphers:
# |       TLS_AES_256_GCM_SHA384 (ecdh_x25519) - A
# |   least strength: A

# Heartbleed 취약점 확인
echo 1 | sudo -S nmap --script=ssl-heartbleed -p 443 10.20.30.100
# 예상 출력:
# PORT    STATE SERVICE
# 443/tcp open  https
# | ssl-heartbleed:
# |   VULNERABLE: (또는 NOT VULNERABLE)

# POODLE 취약점 확인
echo 1 | sudo -S nmap --script=ssl-poodle -p 443 10.20.30.100
# 예상 출력: SSLv3 지원 여부에 따라 취약/안전 표시
```

> **결과 해석**:
> - `ssl-cert`: 인증서 정보 — 발급자, 유효 기간, CN(Common Name) 확인
> - `ssl-enum-ciphers`: 지원하는 암호 스위트 — A등급이면 안전, C/F면 취약
> - `ssl-heartbleed`: Heartbleed(CVE-2014-0160) 취약 여부 — 최신 OpenSSL은 안전
> - 자체 서명 인증서(self-signed)는 보안 경고이나 실습 환경에서는 정상
>
> **실전 활용**: SSL/TLS 설정 오류는 가장 흔한 취약점 중 하나이다. PCI-DSS 등 컴플라이언스에서 TLSv1.0/1.1 비활성화를 요구한다.
>
> **명령어 해설**:
> - `ssl-cert`: 인증서 상세 정보 추출
> - `ssl-enum-ciphers`: 지원 암호 스위트를 강도별로 분류
> - `ssl-heartbleed`: OpenSSL Heartbleed 취약점 전용 검사
>
> **트러블슈팅**:
> - "connection refused": 443 포트가 열려 있지 않거나 SSL이 아닌 경우
> - cipher 등급이 표시되지 않음: nmap 버전이 오래된 경우 업데이트 필요

### Step 3: SSH 취약점 스캔

> **실습 목적**: SSH 서비스의 보안 설정과 알려진 취약점을 점검한다.
>
> **배우는 것**: SSH 보안 감사의 주요 점검 항목

```bash
# SSH 인증 방법 확인
echo 1 | sudo -S nmap --script=ssh-auth-methods -p 22 10.20.30.80
# 예상 출력:
# | ssh-auth-methods:
# |   Supported authentication methods:
# |     publickey
# |_    password    ← 비밀번호 인증 허용 (보안 취약)

# SSH 호스트 키 확인
echo 1 | sudo -S nmap --script=ssh-hostkey -p 22 10.20.30.80
# 예상 출력:
# | ssh-hostkey:
# |   256 xx:xx:xx:... (ECDSA)
# |_  256 xx:xx:xx:... (ED25519)

# SSH 알고리즘 감사
echo 1 | sudo -S nmap --script=ssh2-enum-algos -p 22 10.20.30.80
# 예상 출력:
# | ssh2-enum-algos:
# |   kex_algorithms:
# |     curve25519-sha256
# |     ecdh-sha2-nistp256
# |   encryption_algorithms:
# |     aes256-gcm@openssh.com
# |     aes128-gcm@openssh.com
# |     chacha20-poly1305@openssh.com
```

> **결과 해석**:
> - `password` 인증 허용: 브루트포스 공격 가능 → Week 04에서 공격 시도
> - `curve25519-sha256`: 최신 키 교환 알고리즘, 안전
> - `chacha20-poly1305`: 최신 대칭 암호, 안전
>
> **실전 활용**: SSH는 서버 관리의 핵심이므로 보안 설정 감사가 중요하다. 비밀번호 인증 비활성화, 키 기반 인증만 허용하는 것이 모범 사례이다.

### Step 4: HTTP 서비스 상세 취약점 스캔

> **실습 목적**: 웹 서비스에 특화된 NSE 스크립트로 다양한 웹 취약점을 탐지한다.
>
> **배우는 것**: HTTP 관련 NSE 스크립트 활용법

```bash
# HTTP 메서드 확인 (PUT, DELETE 등 위험한 메서드)
echo 1 | sudo -S nmap --script=http-methods -p 80,3000 10.20.30.80
# 예상 출력:
# | http-methods:
# |   Supported Methods: GET HEAD POST OPTIONS
# |_  Potentially risky methods: NONE

# HTTP 디렉토리 열거
echo 1 | sudo -S nmap --script=http-enum -p 80,3000 10.20.30.80
# 예상 출력:
# | http-enum:
# |   /icons/: Potentially interesting folder
# |   /server-status/: Apache server status (protected)

# SQL Injection 탐지
echo 1 | sudo -S nmap --script=http-sql-injection -p 3000 10.20.30.80
# 예상 출력: SQL 삽입 가능 파라미터 (있는 경우)

# 쿠키 보안 속성 확인
echo 1 | sudo -S nmap --script=http-cookie-flags -p 3000 10.20.30.80
# 예상 출력: HttpOnly, Secure 플래그 누락 여부
```

> **결과 해석**:
> - `Supported Methods: PUT DELETE`: PUT으로 파일 업로드, DELETE로 파일 삭제 가능 → 심각
> - `http-enum` 결과: 노출된 디렉토리와 파일에서 정보 유출 가능
> - `http-cookie-flags`: HttpOnly 없으면 XSS로 쿠키 탈취 가능
>
> **실전 활용**: 웹 취약점은 가장 흔한 공격 벡터이다. NSE 스크립트로 빠르게 취약 포인트를 식별하고, 수동 테스트로 검증한다.
>
> **트러블슈팅**:
> - http-enum 결과가 없음: 워드리스트가 매칭되지 않는 경우 → 커스텀 워드리스트 사용
> - http-sql-injection이 느림: `--script-args http-sql-injection.maxpagecount=10`

---

# Part 4: Nikto 웹 취약점 스캔 + 종합 분석 (30분)

## 실습 4.1: Nikto 웹 서버 스캔

### Step 1: Apache 웹 서버 스캔

> **실습 목적**: Nikto를 사용하여 Apache 웹 서버의 알려진 취약점과 설정 오류를 종합 검사한다.
>
> **배우는 것**: Nikto의 사용법과 결과 해석, 웹 서버 보안 감사 관점

```bash
# Apache 웹 서버 스캔 (포트 80)
nikto -h http://10.20.30.80:80 -o /tmp/nikto_apache.txt
# 예상 출력:
# - Nikto v2.5.0
# + Target IP:          10.20.30.80
# + Target Hostname:    10.20.30.80
# + Target Port:        80
# + Start Time:         2026-xx-xx xx:xx:xx (GMT+9)
# + Server: Apache/2.4.52 (Ubuntu)
# + /: The anti-clickjacking X-Frame-Options header is not present.
# + /: The X-Content-Type-Options header is not set.
# + /icons/README: Apache default file found.
# + /server-status: Apache server-status page found (protected).
# + /: Server may leak inodes via ETags, header found with file /, inode: ...
# + x findings (x items)

# 결과 파일 확인
cat /tmp/nikto_apache.txt | head -30
```

> **결과 해석**:
> - `X-Frame-Options header is not present`: Clickjacking 공격에 취약
> - `X-Content-Type-Options header is not set`: MIME 타입 스니핑 공격 가능
> - `Apache default file found`: 기본 설치 파일 미삭제 → 정보 유출
> - `server-status page found`: 서버 상태 페이지 노출 → 내부 정보 유출 가능
> - `ETags leak inodes`: inode 번호 유출로 파일 시스템 정보 노출
>
> **실전 활용**: Nikto 결과에서 보안 헤더 누락은 거의 항상 발견된다. Apache 설정(httpd.conf)에서 헤더를 추가하는 것이 권장된다.
>
> **명령어 해설**:
> - `-h`: 대상 URL 지정
> - `-o`: 결과를 파일로 저장
> - `-Format csv`: CSV 형태로 저장 (스프레드시트 분석용)
>
> **트러블슈팅**:
> - "Error: no host specified": `-h` 옵션에 http:// 포함 확인
> - 스캔이 매우 오래 걸림: `-Tuning 12` 등으로 검사 범위 축소

### Step 2: JuiceShop 스캔

> **실습 목적**: 의도적으로 취약한 JuiceShop 애플리케이션에서 다수의 취약점을 탐지한다.
>
> **배우는 것**: 취약한 웹 애플리케이션에서 발견되는 전형적인 취약점 패턴

```bash
# JuiceShop 스캔 (포트 3000)
nikto -h http://10.20.30.80:3000 -o /tmp/nikto_juiceshop.txt
# 예상 출력:
# + Server: Express
# + /: The X-Content-Type-Options header is not set.
# + No CGI Directories found
# + /api: Potentially interesting API endpoint
# + /ftp: Potentially interesting directory
# + /assets: Static assets directory
# + Multiple potential XSS/SQLi points detected
# + x findings

# 결과에서 취약점만 필터링
grep -E "OSVDB|CVE|vuln" /tmp/nikto_juiceshop.txt
# 예상 출력: OSVDB/CVE 참조가 있는 항목들

# 높은 위험도 항목만 확인
grep -i "injection\|xss\|disclosure\|upload" /tmp/nikto_juiceshop.txt
```

> **결과 해석**:
> - JuiceShop은 의도적으로 취약하므로 많은 항목이 발견된다
> - `/ftp` 디렉토리: 파일 접근 가능 → 정보 유출
> - `/api` 엔드포인트: REST API 노출 → 인증 우회 시도 가능
>
> **실전 활용**: 실제 모의해킹에서도 Nikto로 빠르게 "낮은 과일"(쉽게 발견되는 취약점)을 수확한 후, 수동 테스트로 심층 분석한다.

### Step 3: 수동 취약점 검증

> **실습 목적**: 자동 스캔 결과의 오탐 여부를 수동으로 검증하는 방법을 익힌다.
>
> **배우는 것**: 오탐 판별과 수동 검증 기법

```bash
# 검증 1: 보안 헤더 누락 확인
curl -sI http://10.20.30.80:80 | grep -iE "x-frame|x-content|strict-transport|content-security"
# 예상 출력: (아무것도 없거나 일부만 표시)
# → 보안 헤더가 없으면 Nikto의 탐지가 정확(참양성)

# 검증 2: 서버 버전 정보 노출 확인
curl -sI http://10.20.30.80:80 | grep Server
# 예상 출력: Server: Apache/2.4.52 (Ubuntu)
# → 서버 버전이 헤더에 노출됨 (정보 유출, 참양성)

# 검증 3: 디렉토리 리스팅 확인
curl -s http://10.20.30.80/icons/ | head -5
# 예상 출력: <html>... Index of /icons ... (또는 403 Forbidden)

# 검증 4: JuiceShop FTP 디렉토리 접근
curl -s http://10.20.30.80:3000/ftp/ | head -10
# 예상 출력: 파일 목록 또는 JSON 응답

# 검증 5: server-status 접근
curl -s http://10.20.30.80/server-status | head -5
# 예상 출력: 403 Forbidden (또는 서버 상태 페이지)
```

> **결과 해석**:
> - 수동 검증으로 각 항목이 참양성(TP)인지 오탐(FP)인지 판별
> - 보안 헤더 누락은 거의 항상 참양성
> - server-status가 403이면 접근은 차단되었으나 페이지 존재 자체가 정보
>
> **실전 활용**: 모의해킹 보고서에서 "자동 스캔에서 발견, 수동 검증으로 확인"이라고 기술하면 보고서의 신뢰도가 높아진다.

## 실습 4.2: 종합 취약점 분석 보고서

### Step 1: 전체 인프라 취약점 스캔 자동화

> **실습 목적**: OpsClaw를 활용하여 전체 인프라의 취약점 스캔을 자동화하고 증적을 기록한다.
>
> **배우는 것**: 멀티 호스트 취약점 스캔 오케스트레이션

```bash
# OpsClaw 프로젝트 생성
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week02-vulnscan","request_text":"취약점 스캐닝 실습","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 멀티 타겟 취약점 스캔
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"web nmap-vuln","instruction_prompt":"nmap --script=vuln -p 22,80,3000 10.20.30.80 2>/dev/null | tail -50","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"web nikto","instruction_prompt":"nikto -h http://10.20.30.80:80 -maxtime 60s 2>/dev/null | tail -30","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":3,"title":"siem ssl-check","instruction_prompt":"nmap --script=ssl-cert,ssl-enum-ciphers -p 443 10.20.30.100 2>/dev/null | tail -30","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":4,"title":"secu ssh-audit","instruction_prompt":"nmap --script=ssh-auth-methods,ssh2-enum-algos -p 22 10.20.30.1 2>/dev/null | tail -20","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }' | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'결과: {d[\"overall\"]}')
for t in d.get('task_results',[]):
    print(f'  [{t[\"order\"]}] {t[\"title\"]:20s} → {t[\"status\"]}')
"
# 예상 출력:
# 결과: success
#   [1] web nmap-vuln          → ok
#   [2] web nikto              → ok
#   [3] siem ssl-check         → ok
#   [4] secu ssh-audit         → ok
```

### Step 2: 취약점 요약 보고서 작성

> **실습 목적**: 스캔 결과를 CVSS 기반으로 정리하여 전문적인 취약점 보고서를 작성한다.
>
> **배우는 것**: 취약점 보고서의 표준 형식과 우선순위 결정 방법

```bash
cat << 'REPORT'
=== 취약점 스캔 보고서 ===

1. 스캔 범위: 10.20.30.0/24 (secu, web, siem, opsclaw)
2. 스캔 도구: nmap 7.94 (NSE), Nikto 2.5.0
3. 스캔 일시: $(date)

4. 취약점 요약 (CVSS 내림차순):

| # | 대상 | 취약점 | CVSS | 유형 | 상태 |
|---|------|--------|------|------|------|
| 1 | web:3000 | SQL Injection (JuiceShop) | 9.8 | CWE-89 | 확인됨 |
| 2 | web:3000 | XSS (JuiceShop) | 6.1 | CWE-79 | 확인됨 |
| 3 | *:22 | SSH 비밀번호 인증 허용 | 5.3 | CWE-287 | 확인됨 |
| 4 | web:80 | 보안 헤더 누락 | 4.3 | CWE-693 | 확인됨 |
| 5 | web:80 | 서버 버전 정보 노출 | 2.6 | CWE-200 | 확인됨 |
| 6 | web:80 | Apache 기본 파일 노출 | 2.6 | CWE-538 | 확인됨 |

5. 권장 대응:
   (1) JuiceShop SQLi/XSS → 입력값 검증, WAF 규칙 추가 (Week 06)
   (2) SSH 비밀번호 인증 → 키 기반 인증으로 전환
   (3) 보안 헤더 → Apache 설정에서 헤더 추가
   (4) 서버 버전 노출 → ServerTokens Prod 설정
REPORT
```

---

## 검증 체크리스트
- [ ] nmap NSE vuln 스크립트로 web 서버 취약점을 스캔했는가
- [ ] SSL/TLS 취약점 스크립트로 siem 서버를 검사했는가
- [ ] SSH 보안 설정을 감사했는가 (인증 방법, 알고리즘)
- [ ] Nikto로 Apache와 JuiceShop을 스캔했는가
- [ ] 자동 스캔 결과의 오탐 여부를 수동으로 검증했는가 (최소 3건)
- [ ] OpsClaw를 통해 멀티 타겟 취약점 스캔을 실행했는가
- [ ] CVSS 기반 취약점 요약 보고서를 작성했는가

## 자가 점검 퀴즈

1. 취약점 스캐닝과 침투 테스트의 핵심 차이 3가지를 설명하라.

2. CVSS v3.1에서 AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H 벡터의 의미를 각 메트릭별로 해석하라.

3. CVE와 CWE의 관계를 예시를 들어 설명하라.

4. nmap NSE의 `vuln` 카테고리와 `safe` 카테고리의 차이점과 각 사용 시나리오를 설명하라.

5. Nikto 스캔에서 "X-Frame-Options header is not present"라는 결과의 보안적 의미와 대응 방법을 설명하라.

6. 오탐(False Positive)이 발생하는 원인 3가지와 검증 방법을 설명하라.

7. SSH 서비스에서 `password` 인증이 허용되어 있을 때의 보안 위험과 대응 방법을 설명하라.

8. `ssl-enum-ciphers` 결과에서 등급이 'C' 또는 'F'인 암호 스위트가 발견되면 어떤 공격이 가능한가?

9. 취약점 스캔 결과의 우선순위를 결정할 때 CVSS 점수 외에 고려해야 할 요소 3가지를 설명하라.

10. Blue Team 관점에서 취약점 스캐닝 결과를 자산 관리에 어떻게 활용할 수 있는지 설명하라.

## 과제

### 과제 1: 전체 인프라 취약점 보고서 (필수)
- 4개 서버에 대해 nmap NSE vuln 스캔 + Nikto 스캔 수행
- 발견된 모든 취약점을 CVSS 기반으로 정리 (최소 10건)
- 각 취약점에 대해 오탐/참양성 판별 결과와 근거 기술
- 대응 권장사항을 취약점별로 작성

### 과제 2: CVE 심층 분석 (선택)
- 스캔에서 발견된 서비스 버전 중 하나를 선택 (예: OpenSSH 8.9p1)
- 해당 버전의 알려진 CVE를 NVD에서 검색하여 3개 이상 분석
- 각 CVE의 CVSS 벡터를 해석하고, 실습 환경에서의 공격 가능성을 평가

### 과제 3: 커스텀 NSE 스크립트 (도전)
- nmap NSE 스크립트 문법을 학습하여 간단한 커스텀 스크립트 작성
- 예: 특정 HTTP 응답 헤더를 검사하는 스크립트
- 스크립트를 실행하여 결과를 확인하고, 스크립트 코드와 함께 제출
