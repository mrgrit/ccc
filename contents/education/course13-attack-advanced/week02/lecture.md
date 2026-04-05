# Week 02: OSINT 고급 — Shodan, Censys, 소셜미디어 정찰, 메타데이터 추출

## 학습 목표
- **OSINT(Open Source Intelligence)**의 체계적 방법론(OSINT Framework)을 이해하고 활용할 수 있다
- Shodan과 Censys를 사용하여 인터넷에 노출된 서비스와 취약점을 검색할 수 있다
- Google Dorking 고급 기법으로 민감한 정보 유출을 탐지할 수 있다
- 소셜미디어(LinkedIn, GitHub, Twitter)에서 공격 대상의 정보를 체계적으로 수집할 수 있다
- 문서 메타데이터에서 내부 사용자명, 소프트웨어 버전, 네트워크 경로 등을 추출할 수 있다
- theHarvester, Maltego, recon-ng 등 자동화 OSINT 도구를 활용할 수 있다
- MITRE ATT&CK Reconnaissance 전술의 세부 기법을 매핑하고 설명할 수 있다

## 전제 조건
- Week 01(APT 킬체인)의 정찰 단계 개념을 이해하고 있어야 한다
- 기본 nmap 스캔과 DNS 조회를 수행할 수 있어야 한다
- HTTP 프로토콜의 기본 구조(요청, 응답, 헤더)를 이해하고 있어야 한다
- curl, wget, python3 기본 사용법을 알고 있어야 한다

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 실습 기지 (공격 출발점) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | OSINT 방법론 + Shodan/Censys 이론 | 강의 |
| 0:35-1:10 | Shodan/Censys 실습 + 서비스 핑거프린팅 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:55 | Google Dorking + 소셜미디어 정찰 | 실습 |
| 1:55-2:30 | 메타데이터 추출 + 자동화 도구 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 종합 OSINT 실습 (대상 프로파일링) | 실습 |
| 3:10-3:30 | ATT&CK 매핑 + 퀴즈 + 과제 | 토론/퀴즈 |

---

# Part 1: OSINT 방법론과 체계 (35분)

## 1.1 OSINT란?

OSINT(Open Source Intelligence)는 **공개적으로 접근 가능한 출처**에서 정보를 수집하고 분석하는 정보 활동이다.

### OSINT의 5단계 사이클

```
+-----------------------------------------------------------+
|                  OSINT Intelligence Cycle                   |
+-----------------------------------------------------------+
| 1. Planning        계획: 수집 목표와 범위 정의              |
|    ↓                                                       |
| 2. Collection      수집: 다양한 소스에서 원시 데이터 확보    |
|    ↓                                                       |
| 3. Processing      처리: 수집 데이터 정리, 중복 제거         |
|    ↓                                                       |
| 4. Analysis        분석: 패턴 식별, 상관관계 도출            |
|    ↓                                                       |
| 5. Dissemination   배포: 분석 결과 보고서 작성               |
+-----------------------------------------------------------+
```

### OSINT 소스 분류

| 소스 유형 | 예시 | 수집 가능 정보 | ATT&CK |
|----------|------|--------------|--------|
| 검색 엔진 | Google, Bing, DuckDuckGo | 웹 페이지, 문서, 에러 페이지 | T1593.002 |
| 기술 DB | Shodan, Censys, ZoomEye | IP, 포트, 배너, 인증서 | T1596 |
| DNS/WHOIS | 레지스트리, crt.sh | 도메인, IP, 서브도메인 | T1596.001 |
| 소셜미디어 | LinkedIn, Twitter, GitHub | 직원, 기술스택, 내부정보 | T1593.001 |
| 코드 저장소 | GitHub, GitLab, Bitbucket | API 키, 비밀번호, 인프라 구조 | T1593.003 |
| 문서 메타데이터 | PDF, DOCX, 이미지 | 사용자명, 소프트웨어, 경로 | T1592.004 |
| 다크웹 | .onion 사이트, 포럼 | 유출 데이터, 크레덴셜 | T1597 |
| 공공 데이터 | 특허, 법원 기록, SEC 파일링 | 조직 구조, 기술 정보 | T1591 |

## 1.2 OSINT Framework 구조

OSINT Framework(osintframework.com)는 카테고리별 OSINT 도구를 체계적으로 정리한 트리 구조이다.

```
OSINT Framework
+-- Username
|   +-- KnowEm, Namechk, WhatsMyName
+-- Email Address
|   +-- Hunter.io, Phonebook.cz, Have I Been Pwned
+-- Domain Name
|   +-- WHOIS, crt.sh, SecurityTrails, DNSDumpster
+-- IP Address
|   +-- Shodan, Censys, GreyNoise, AbuseIPDB
+-- Social Networks
|   +-- LinkedIn, Twitter/X, Facebook, Instagram
+-- Search Engines
|   +-- Google Dorking, Bing, DuckDuckGo
+-- Dark Web
|   +-- Ahmia, Torch, DarkSearch
+-- Metadata
|   +-- ExifTool, FOCA, Metagoofil
+-- Geolocation
|   +-- Google Maps, Wigle.net, SunCalc
```

## 1.3 MITRE ATT&CK: Reconnaissance 세부 기법

| 기법 ID | 기법 이름 | 세부 | 이번 주 실습 |
|---------|---------|------|:---:|
| T1589 | Gather Victim Identity Info | 이메일, 크레덴셜, 이름 | ✓ |
| T1590 | Gather Victim Network Info | IP, 도메인, DNS, CDN | ✓ |
| T1591 | Gather Victim Org Info | 업무관계, 물리위치 | △ |
| T1592 | Gather Victim Host Info | HW, SW, 설정 | ✓ |
| T1593 | Search Open Websites/Domains | 소셜미디어, 검색엔진 | ✓ |
| T1593.001 | Social Media | 소셜미디어 정찰 | ✓ |
| T1593.002 | Search Engines | Google Dorking | ✓ |
| T1593.003 | Code Repositories | GitHub 검색 | ✓ |
| T1596 | Search Open Technical Databases | Shodan, Censys | ✓ |
| T1596.001 | DNS/Passive DNS | DNS 레코드 수집 | ✓ |
| T1596.005 | Scan Databases | CVE, NVD | △ |
| T1597 | Search Closed Sources | 다크웹, 유료DB | △ |

---

# Part 2: Shodan과 Censys 활용 (35분)

## 2.1 Shodan — "인터넷의 검색엔진"

Shodan은 인터넷에 연결된 장치와 서비스를 스캔하고 인덱싱하는 검색엔진이다. 웹 페이지가 아닌 **배너(Banner)**를 수집한다.

### Shodan 검색 문법

| 필터 | 설명 | 예시 |
|------|------|------|
| `hostname:` | 호스트명 검색 | `hostname:example.com` |
| `port:` | 포트 번호 | `port:3389` (RDP) |
| `country:` | 국가 코드 | `country:KR` |
| `city:` | 도시명 | `city:Seoul` |
| `org:` | 조직명 | `org:"Korea Telecom"` |
| `os:` | 운영체제 | `os:"Ubuntu"` |
| `product:` | 제품명 | `product:"Apache httpd"` |
| `version:` | 버전 | `version:"2.4.49"` |
| `vuln:` | CVE 번호 | `vuln:CVE-2021-44228` |
| `has_screenshot:` | 스크린샷 존재 | `has_screenshot:true` |
| `ssl.cert.subject.cn:` | SSL 인증서 CN | `ssl.cert.subject.cn:example.com` |

### Shodan 위험 검색 쿼리 예시

| 쿼리 | 발견 대상 | 위험도 |
|------|----------|--------|
| `"default password" port:80` | 기본 비밀번호 사용 장치 | 매우 높음 |
| `port:5900 authentication disabled` | VNC 인증 없음 | 매우 높음 |
| `port:27017 "MongoDB"` | MongoDB 인증 없이 노출 | 높음 |
| `"Server: Apache/2.4.49"` | CVE-2021-41773 취약 | 높음 |
| `port:9200 "elasticsearch"` | Elasticsearch 노출 | 높음 |
| `"X-Jenkins" port:8080` | Jenkins 노출 | 중간 |
| `port:23 "login:"` | Telnet 노출 | 높음 |

## 2.2 Censys — 인증서 기반 인터넷 스캔

Censys는 Shodan과 유사하지만 **TLS 인증서와 서비스 분석에 더 강점**이 있다.

### Censys vs Shodan 비교

| 항목 | Shodan | Censys |
|------|--------|--------|
| 주요 강점 | IoT, 배너 수집 | TLS 인증서, 서비스 분류 |
| 스캔 범위 | 전체 IPv4 | 전체 IPv4 + IPv6 일부 |
| 업데이트 주기 | 지속적 | 주 1회 전체 + 지속적 |
| API 무료 한도 | 제한적 | 250 query/월 |
| 특수 기능 | 스크린샷, 허니팟 탐지 | 인증서 체인, 서비스 리스크 |

### Censys 검색 문법

| 필터 | 설명 | 예시 |
|------|------|------|
| `services.port:` | 포트 | `services.port: 443` |
| `services.service_name:` | 서비스명 | `services.service_name: HTTP` |
| `services.tls.certificates.leaf.subject.common_name:` | 인증서 CN | 도메인 검색 |
| `location.country:` | 국가 | `location.country: South Korea` |
| `autonomous_system.name:` | AS 이름 | ISP/클라우드 검색 |

## 실습 2.1: 실습 환경 서비스 핑거프린팅 (Shodan 방식)

> **실습 목적**: Shodan이 수집하는 것과 동일한 배너 정보를 직접 수집하여, 인터넷 스캔 엔진의 원리를 이해한다
>
> **배우는 것**: HTTP 헤더, SSH 배너, 서비스 버전 등 배너 그래빙(Banner Grabbing) 기법을 배운다
>
> **결과 해석**: 배너에서 서비스 종류, 버전, 서버 OS 정보를 추출할 수 있다
>
> **실전 활용**: 외부 스캔 서비스 없이도 대상의 기술 스택을 파악할 수 있다
>
> **명령어 해설**: curl -I는 HTTP 헤더만 요청, nc는 원시 TCP 연결로 배너를 수집한다
>
> **트러블슈팅**: 응답이 없으면 방화벽 규칙과 서비스 상태를 확인한다

```bash
# HTTP 배너 수집 (Shodan이 하는 것과 동일)
echo "=== HTTP 배너: web 서버 ==="
curl -sI http://10.20.30.80/ 2>/dev/null | head -10

echo ""
echo "=== HTTP 배너: Juice Shop ==="
curl -sI http://10.20.30.80:3000/ 2>/dev/null | head -10

echo ""
echo "=== SSH 배너 수집 ==="
# SSH 배너 (서버 소프트웨어 버전 노출)
echo "" | nc -w3 10.20.30.80 22 2>/dev/null | head -1
echo "" | nc -w3 10.20.30.1 22 2>/dev/null | head -1
echo "" | nc -w3 10.20.30.100 22 2>/dev/null | head -1

echo ""
echo "=== SubAgent API 배너 ==="
curl -sI http://10.20.30.80:8002/ 2>/dev/null | head -5
```

## 실습 2.2: 서비스 상세 정보 수집

> **실습 목적**: 배너에서 추출한 정보를 바탕으로 기술 스택을 완전히 프로파일링한다
>
> **배우는 것**: HTTP 응답 헤더, 에러 페이지, 특수 경로 등에서 상세 정보를 추출하는 기법을 배운다
>
> **결과 해석**: Server, X-Powered-By, Set-Cookie 등 헤더에서 기술 스택을 판별한다
>
> **실전 활용**: 수집한 기술 스택 정보로 CVE 데이터베이스에서 관련 취약점을 검색한다
>
> **명령어 해설**: curl -v는 상세 출력, --head는 HEAD 요청만 전송한다
>
> **트러블슈팅**: HTTPS 인증서 에러 시 -k 옵션으로 검증 건너뛰기

```bash
# 기술 스택 프로파일링
echo "=== 1. HTTP 응답 헤더 분석 ==="
curl -s -D- http://10.20.30.80:3000/ -o /dev/null 2>/dev/null | head -20

echo ""
echo "=== 2. robots.txt 확인 ==="
curl -s http://10.20.30.80/robots.txt 2>/dev/null || echo "robots.txt 없음"

echo ""
echo "=== 3. 에러 페이지에서 정보 추출 ==="
# 404 에러에서 서버 정보 노출 여부
curl -s http://10.20.30.80/nonexistent_page_12345 2>/dev/null | head -5

echo ""
echo "=== 4. Juice Shop API 버전 정보 ==="
curl -s http://10.20.30.80:3000/api/Challenges/ 2>/dev/null | python3 -c "
import sys,json
try:
    data=json.load(sys.stdin)
    print(f'Status: {data.get(\"status\")}')
    challenges = data.get('data', [])
    print(f'Challenge 수: {len(challenges)}')
    if challenges:
        print(f'예시: {challenges[0].get(\"name\",\"N/A\")}')
except: print('API 접근 불가')" 2>/dev/null

echo ""
echo "=== 5. 숨겨진 경로 탐색 ==="
for path in /admin /api /swagger /docs /metrics /.env /config; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000${path}" 2>/dev/null)
  echo "  $path → HTTP $CODE"
done
```

## 실습 2.3: SSL/TLS 인증서 분석 (Censys 방식)

> **실습 목적**: TLS 인증서에서 조직 정보, 서브도메인, 인증서 체인을 분석하는 기법을 배운다
>
> **배우는 것**: openssl 명령으로 인증서 정보를 추출하고 분석하는 방법을 배운다
>
> **결과 해석**: Subject, Issuer, SAN(Subject Alternative Name)에서 도메인과 조직 정보를 파악한다
>
> **실전 활용**: 와일드카드 인증서나 SAN 항목에서 숨겨진 서브도메인을 발견할 수 있다
>
> **명령어 해설**: openssl s_client로 TLS 연결 수립, x509로 인증서 디코딩한다
>
> **트러블슈팅**: 연결 거부 시 해당 포트에서 TLS가 지원되는지 확인한다

```bash
# TLS 인증서 분석
echo "=== web 서버 HTTPS 인증서 확인 ==="
echo | timeout 5 openssl s_client -connect 10.20.30.80:443 2>/dev/null | openssl x509 -noout -text 2>/dev/null | grep -E "Subject:|Issuer:|DNS:|Not Before|Not After" || echo "HTTPS 미사용 또는 접속 불가"

echo ""
echo "=== 인증서 분석 교육 예시 ==="
cat << 'CERT_ANALYSIS'
실제 Censys 인증서 분석 결과 예시:
+------------------------------------------+
| Subject CN: *.example.com                 |
| Subject O: Example Corporation            |
| Issuer: Let's Encrypt Authority X3        |
| Valid: 2025-01-01 ~ 2025-04-01            |
| SAN: example.com, *.example.com,          |
|      staging.example.com,                 |
|      api-internal.example.com  ← 발견!    |
|      dev.example.com           ← 발견!    |
+------------------------------------------+

수집 가능한 정보:
1. 서브도메인: staging, api-internal, dev → 공격 표면 확장
2. 조직명: Example Corporation → 추가 OSINT 검색어
3. 인증서 발급 주기 → 자동화 수준 추정
4. 와일드카드 사용 → 임의 서브도메인 공격 가능성
CERT_ANALYSIS
```

---

# Part 3: Google Dorking과 소셜미디어 정찰 (35분)

## 3.1 Google Dorking 고급

Google Dorking은 검색 엔진의 고급 연산자를 활용하여 **의도치 않게 노출된 민감 정보**를 발견하는 기법이다.

### Google 고급 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `site:` | 특정 도메인 한정 | `site:example.com` |
| `intitle:` | 제목에 포함 | `intitle:"index of /"` |
| `inurl:` | URL에 포함 | `inurl:admin` |
| `intext:` | 본문에 포함 | `intext:"password"` |
| `filetype:` | 파일 형식 | `filetype:pdf` |
| `ext:` | 파일 확장자 | `ext:sql` |
| `cache:` | 캐시된 버전 | `cache:example.com` |
| `link:` | 링크 포함 | `link:example.com` |
| `-` | 제외 | `site:example.com -www` |
| `"..."` | 정확한 구문 | `"error on line"` |
| `OR` / `|` | 또는 | `admin OR login` |

### Google Dorking 공격 시나리오

| 목적 | 쿼리 | 발견 대상 |
|------|------|----------|
| 디렉토리 목록 | `intitle:"index of /" site:target.com` | 파일 목록 노출 |
| 설정 파일 | `filetype:env site:target.com` | .env 파일 |
| 데이터베이스 | `filetype:sql "INSERT INTO" site:target.com` | SQL 덤프 |
| 로그인 페이지 | `inurl:admin inurl:login site:target.com` | 관리자 로그인 |
| 에러 메시지 | `"Warning:" "mysql_" site:target.com` | PHP/MySQL 에러 |
| API 문서 | `inurl:swagger OR inurl:api-docs site:target.com` | API 노출 |
| 백업 파일 | `ext:bak OR ext:old OR ext:backup site:target.com` | 백업 파일 |
| 민감 문서 | `filetype:pdf "confidential" site:target.com` | 기밀 문서 |

### Google Hacking Database (GHDB)

Exploit-DB에서 관리하는 Google Dorking 쿼리 데이터베이스로, 카테고리별 수천 개의 검증된 쿼리를 제공한다.

| 카테고리 | 예시 수 | 설명 |
|---------|--------|------|
| Footholds | 200+ | 초기 접근 포인트 |
| Files containing passwords | 300+ | 비밀번호 포함 파일 |
| Sensitive directories | 100+ | 민감 디렉토리 |
| Web server detection | 150+ | 서버 종류 식별 |
| Vulnerable files | 200+ | 취약한 파일 |
| Error messages | 100+ | 정보 노출 에러 |

## 실습 3.1: 웹 서버 OSINT 수집

> **실습 목적**: Google Dorking과 유사한 기법으로 웹 서버에서 정보를 체계적으로 수집한다
>
> **배우는 것**: 디렉토리 열거, 파일 발견, 에러 메시지 분석 등 웹 기반 OSINT 기법을 배운다
>
> **결과 해석**: HTTP 200 응답은 해당 경로가 존재함을, 403은 접근 제한이 있지만 존재함을 의미한다
>
> **실전 활용**: 모의해킹 초기 단계에서 대상 웹 서버의 구조를 파악하는 데 활용한다
>
> **명령어 해설**: curl -o /dev/null -w "%{http_code}"는 응답 본문을 버리고 상태 코드만 출력한다
>
> **트러블슈팅**: 모든 경로가 200이면 WAF가 커스텀 에러 페이지를 반환하는 것일 수 있다

```bash
# 웹 서버 디렉토리/파일 탐색 (Google Dorking 로컬 버전)
echo "=== 민감 파일 탐색 ==="
TARGETS=(".env" ".git/config" "wp-config.php" "config.php" "database.yml"
         ".htaccess" ".htpasswd" "web.config" "phpinfo.php" "info.php"
         "backup.sql" "dump.sql" ".DS_Store" "Thumbs.db")

for file in "${TARGETS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80/$file" 2>/dev/null)
  if [ "$CODE" != "404" ] && [ "$CODE" != "000" ]; then
    echo "  [!] /$file → HTTP $CODE (발견!)"
  fi
done

echo ""
echo "=== Juice Shop 민감 경로 탐색 ==="
PATHS=("/ftp" "/api-docs" "/metrics" "/b2bOrder" "/profile" "/administration"
       "/accounting" "/support/logs" "/encryptionkeys" "/assets/public/images/uploads")

for path in "${PATHS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path" 2>/dev/null)
  if [ "$CODE" != "404" ] && [ "$CODE" != "000" ]; then
    echo "  [!] $path → HTTP $CODE"
  fi
done
```

## 3.2 소셜미디어 정찰

소셜미디어는 APT 그룹이 가장 선호하는 OSINT 소스 중 하나이다. 직원 개인 계정에서 조직의 내부 정보가 유출되는 경우가 빈번하다.

### 소셜미디어 정찰 대상

| 플랫폼 | 수집 정보 | 공격 활용 |
|--------|----------|----------|
| LinkedIn | 직원 목록, 직책, 기술 스택 | 스피어피싱 대상 선정, 기술 추정 |
| GitHub | 소스코드, API 키, 인프라 구조 | 크레덴셜 탈취, 취약점 발견 |
| Twitter/X | 기술 토론, 장애 보고, 내부 도구 | 기술 스택 파악, 타이밍 공격 |
| Stack Overflow | 에러 메시지, 코드 스니펫 | 내부 구조 파악 |
| Glassdoor | 기업 문화, 보안 수준 | 소셜 엔지니어링 소재 |
| Instagram | 사무실 사진, 배지, 화면 | 물리 보안 정보 |

### GitHub OSINT 검색 쿼리

```
# API 키/비밀 탈취
"api_key" OR "apikey" filename:.env
"password" filename:config.yml org:target-org
"AWS_SECRET_ACCESS_KEY" language:python
"PRIVATE KEY" filename:id_rsa

# 인프라 정보
"10.0.0" OR "172.16" OR "192.168" filename:config
"jdbc:mysql://" filename:application.properties
"mongodb://" filename:.env
```

## 실습 3.2: GitHub 코드 검색 기반 정보 수집

> **실습 목적**: GitHub에서 실수로 노출된 크레덴셜과 인프라 정보를 검색하는 기법을 배운다
>
> **배우는 것**: GitHub 고급 검색 문법, 코드에서 민감 정보를 식별하는 패턴을 배운다
>
> **결과 해석**: API 키, 비밀번호, 내부 IP 등이 발견되면 정보 유출이 확인된 것이다
>
> **실전 활용**: Bug Bounty, 모의해킹에서 크레덴셜 유출을 통한 초기 접근에 활용한다
>
> **명령어 해설**: grep -rn은 재귀적으로 파일을 검색하며 라인 번호를 표시한다
>
> **트러블슈팅**: 결과가 많으면 조직명이나 도메인으로 범위를 좁힌다

```bash
# 로컬 환경에서 GitHub 스타일 시크릿 스캔 시뮬레이션
echo "=== 시크릿 패턴 검색 (로컬 저장소 시뮬레이션) ==="

# 테스트용 샘플 코드 생성
mkdir -p /tmp/osint_demo
cat > /tmp/osint_demo/config.py << 'SAMPLE'
# 이 파일이 GitHub에 올라가면 노출되는 정보들
DATABASE_URL = "postgresql://admin:password123@10.20.30.100:5432/production"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
SLACK_TOKEN = "xoxb-EXAMPLE-TOKEN-REDACTED"
API_KEY = "sk-proj-abcdef1234567890"
INTERNAL_NETWORK = "10.20.30.0/24"
SAMPLE

# 시크릿 패턴 검색
echo "--- 비밀번호 패턴 ---"
grep -n "password\|passwd\|secret" /tmp/osint_demo/config.py

echo ""
echo "--- AWS 키 패턴 ---"
grep -n "AKIA\|aws_secret" /tmp/osint_demo/config.py

echo ""
echo "--- 내부 IP 패턴 ---"
grep -nE "10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+" /tmp/osint_demo/config.py

echo ""
echo "--- API 키 패턴 ---"
grep -n "api.key\|token\|sk-" /tmp/osint_demo/config.py

# 정리
rm -rf /tmp/osint_demo
echo ""
echo "[시크릿 스캔 완료 - 실제로는 truffleHog, git-secrets 등 전용 도구 사용]"
```

## 실습 3.3: theHarvester를 이용한 자동화 수집

> **실습 목적**: 이메일, 서브도메인, IP 등을 자동으로 수집하는 OSINT 자동화 도구를 사용한다
>
> **배우는 것**: theHarvester의 다양한 데이터 소스 활용법과 결과 분석 방법을 배운다
>
> **결과 해석**: 수집된 이메일은 스피어피싱 대상, 서브도메인은 추가 공격 표면이다
>
> **실전 활용**: 모의해킹 정찰 단계에서 대량의 OSINT 데이터를 신속하게 수집하는 데 활용한다
>
> **명령어 해설**: -d는 대상 도메인, -b는 데이터 소스(google, bing 등), -l은 결과 수 제한이다
>
> **트러블슈팅**: API 키가 없으면 일부 소스가 동작하지 않는다. 무료 소스만 사용하라

```bash
# theHarvester 설치 확인 및 실행 (인터넷 필요)
which theHarvester 2>/dev/null && echo "theHarvester 설치됨" || echo "theHarvester 미설치 - pip install theHarvester"

# 설치된 경우 실행 예시 (인터넷 연결 필요)
# theHarvester -d target-domain.com -b google,bing,crtsh -l 100

# 오프라인 환경 시뮬레이션
echo "=== theHarvester 시뮬레이션 결과 ==="
cat << 'RESULT'
[*] Target: example-corp.com
[*] Sources: google, bing, crtsh, linkedin

[*] Emails found: 8
-------------------
admin@example-corp.com
hr@example-corp.com
security@example-corp.com
john.smith@example-corp.com
jane.doe@example-corp.com
it-support@example-corp.com
ciso@example-corp.com
devops@example-corp.com

[*] Hosts found: 6
-------------------
mail.example-corp.com: 203.0.113.10
vpn.example-corp.com: 203.0.113.11
gitlab.example-corp.com: 203.0.113.20
jenkins.example-corp.com: 203.0.113.21
staging.example-corp.com: 203.0.113.30
api.example-corp.com: 203.0.113.40

분석:
1. 이메일 패턴: firstname.lastname@domain → 다른 직원 이메일 추측 가능
2. 인프라: gitlab, jenkins 노출 → CI/CD 파이프라인 공격 가능
3. 환경: staging 서버 노출 → 보안이 약한 스테이징 환경 공격 가능
4. 보안팀: ciso, security 이메일 존재 → 보안 인식이 있는 조직
RESULT
```

---

# Part 4: 메타데이터 추출과 종합 OSINT (35분)

## 4.1 문서 메타데이터 분석

문서 파일(PDF, DOCX, XLSX, 이미지 등)에는 **작성자, 소프트웨어, 생성 일시, 수정 기록** 등의 메타데이터가 포함된다.

### 메타데이터에서 추출 가능한 정보

| 메타데이터 | 정보 | 공격 활용 |
|-----------|------|----------|
| Author | 사용자명 | 계정 이름 추측, 스피어피싱 |
| Creator/Producer | 소프트웨어 버전 | 취약점 검색 |
| Title | 문서 제목 | 조직 구조, 프로젝트 정보 |
| Subject | 주제 | 내부 업무 파악 |
| CreateDate | 생성 일시 | 업무 시간 패턴 |
| GPS Coordinates | 촬영 위치 | 물리 위치 확인 |
| Camera Model | 카메라/폰 모델 | 장치 정보 |
| ModifyDate | 수정 기록 | 문서 이력 |
| Custom Properties | 내부 경로, 프린터 이름 | 네트워크 구조 |

## 실습 4.1: ExifTool을 이용한 메타데이터 추출

> **실습 목적**: 문서와 이미지 파일에서 숨겨진 메타데이터를 추출하는 기법을 배운다
>
> **배우는 것**: ExifTool 사용법, 메타데이터 분석 포인트, 정보 유출 위험성을 배운다
>
> **결과 해석**: Author, Creator, GPS 좌표 등이 추출되면 해당 정보를 OSINT에 활용할 수 있다
>
> **실전 활용**: 대상 조직의 공개 문서에서 내부 사용자명, 소프트웨어 버전, 네트워크 정보를 수집한다
>
> **명령어 해설**: exiftool은 250+ 파일 형식의 메타데이터를 읽고 쓸 수 있는 도구이다
>
> **트러블슈팅**: exiftool이 없으면 apt install libimage-exiftool-perl로 설치한다

```bash
# ExifTool 설치 확인
which exiftool 2>/dev/null && echo "exiftool 설치됨" || echo "exiftool 미설치 - apt install libimage-exiftool-perl"

# 테스트 PDF 생성 및 메타데이터 확인
mkdir -p /tmp/meta_demo

# Python으로 메타데이터 포함 테스트 파일 생성
python3 << 'PYEOF'
import json

# 메타데이터 시뮬레이션 (실제 PDF 없이)
sample_metadata = {
    "FileName": "quarterly_report_2025.pdf",
    "FileType": "PDF",
    "Author": "john.smith",
    "Creator": "Microsoft Word 2019",
    "Producer": "Microsoft: Print To PDF",
    "CreateDate": "2025:12:15 09:30:22+09:00",
    "ModifyDate": "2025:12:20 17:45:11+09:00",
    "Title": "Q4 2025 보안 감사 보고서",
    "Subject": "내부감사/정보보안",
    "Keywords": "보안감사, SOC, 취약점, 패치관리",
    "CustomProperties": {
        "Company": "Example Corp",
        "Department": "정보보안팀",
        "PrinterName": "\\\\fileserver01\\HP_LaserJet_4F",
        "SavePath": "C:\\Users\\john.smith\\Documents\\Audit\\2025_Q4\\"
    }
}

print("=== ExifTool 메타데이터 추출 결과 (시뮬레이션) ===")
for key, value in sample_metadata.items():
    if isinstance(value, dict):
        print(f"\n--- {key} ---")
        for k, v in value.items():
            print(f"  {k}: {v}")
    else:
        print(f"  {key}: {value}")

print("\n=== OSINT 분석 ===")
print("1. 사용자명: john.smith → AD 계정 이름 추측")
print("2. 소프트웨어: Word 2019 → CVE 검색 대상")
print("3. 프린터: \\\\fileserver01\\ → 내부 파일서버 이름 노출")
print("4. 경로: C:\\Users\\john.smith\\ → Windows 환경 확인")
print("5. 시간대: +09:00 → 한국 표준시")
print("6. 업무시간: 09:30~17:45 → 공격 타이밍 참고")
PYEOF

# 정리
rm -rf /tmp/meta_demo
```

## 실습 4.2: 웹 서버에서 메타데이터 자동 수집

> **실습 목적**: 대상 웹 서버에서 공개된 문서 파일을 찾아 메타데이터를 일괄 추출한다
>
> **배우는 것**: 웹 크롤링과 메타데이터 추출을 결합한 자동화 OSINT 기법을 배운다
>
> **결과 해석**: 다수의 문서에서 동일 패턴의 사용자명이 나오면 신뢰도가 높은 정보이다
>
> **실전 활용**: 대규모 OSINT 수집에서 자동화 도구(metagoofil, FOCA)가 이 방식으로 동작한다
>
> **명령어 해설**: curl로 파일을 다운로드하고 exiftool이나 python으로 메타데이터를 추출한다
>
> **트러블슈팅**: 파일 다운로드가 차단되면 User-Agent를 브라우저로 변경한다

```bash
# Juice Shop의 공개 파일에서 메타데이터 수집
echo "=== Juice Shop 공개 파일 탐색 ==="

# FTP 디렉토리 (Juice Shop의 알려진 취약 경로)
curl -s http://10.20.30.80:3000/ftp/ 2>/dev/null | python3 -c "
import sys
content = sys.stdin.read()
if content:
    # HTML에서 파일명 추출
    import re
    files = re.findall(r'href=\"([^\"]+)\"', content)
    if files:
        print('발견된 파일:')
        for f in files:
            if not f.startswith('/') and not f.startswith('#'):
                print(f'  {f}')
    else:
        print('파일 목록을 파싱할 수 없음')
else:
    print('FTP 디렉토리 접근 불가')" 2>/dev/null

echo ""
echo "=== HTTP 헤더에서 메타데이터 수집 ==="
# 서버 응답 헤더 자체도 메타데이터
for target in "10.20.30.80:80" "10.20.30.80:3000" "10.20.30.1:8002" "10.20.30.100:8002"; do
  echo "--- $target ---"
  curl -sI "http://$target/" 2>/dev/null | grep -iE "server:|x-powered|x-frame|content-security|x-request-id|etag" || echo "  정보 없음"
done
```

## 실습 4.3: 종합 OSINT 프로파일 작성

> **실습 목적**: 수집한 모든 OSINT 정보를 종합하여 대상의 완전한 프로파일을 작성한다
>
> **배우는 것**: OSINT 결과를 구조화하고, 공격 계획에 활용 가능한 형태로 정리하는 방법을 배운다
>
> **결과 해석**: 프로파일이 완성되면 각 정보의 신뢰도와 공격 활용 가능성을 평가한다
>
> **실전 활용**: 모의해킹 보고서의 정찰 단계 섹션 작성에 직접 활용한다
>
> **명령어 해설**: 모든 수집 결과를 JSON 구조로 종합하여 분석한다
>
> **트러블슈팅**: 정보가 부족하면 추가 소스를 탐색하거나 능동 정찰로 전환한다

```bash
# 실습 환경 종합 OSINT 프로파일
echo "============================================================"
echo "            OSINT 종합 프로파일 — 10.20.30.0/24               "
echo "============================================================"
echo ""

echo "[1] 네트워크 토폴로지"
nmap -sn 10.20.30.0/24 2>/dev/null | grep "report\|Host is"

echo ""
echo "[2] 서비스 매핑"
for host in 10.20.30.1 10.20.30.80 10.20.30.100 10.20.30.201; do
  echo "--- $host ---"
  nmap -sV --open -p 22,80,443,3000,8002,9200,5601 "$host" 2>/dev/null | grep "open" || echo "  스캔 결과 없음"
done

echo ""
echo "[3] 기술 스택 요약"
echo "  secu (10.20.30.1): nftables 방화벽, Suricata IPS"
echo "  web (10.20.30.80): Apache/Nginx, Juice Shop (Node.js), SubAgent"
echo "  siem (10.20.30.100): Wazuh 4.11.2, SubAgent"
echo "  opsclaw (10.20.30.201): Python FastAPI, PostgreSQL, OpsClaw"

echo ""
echo "[4] 공격 표면 평가"
echo "  높은 위험: Juice Shop (알려진 취약 앱) - port 3000"
echo "  중간 위험: SubAgent API (인증 여부 확인 필요) - port 8002"
echo "  낮은 위험: SSH (키 인증 시) - port 22"

echo ""
echo "[5] 추천 공격 경로"
echo "  1순위: web:3000 → Juice Shop 취약점 → 웹셸/RCE"
echo "  2순위: web:8002 → SubAgent API 악용 → 명령 실행"
echo "  3순위: secu:22 → SSH 브루트포스 → 방화벽 장악"
echo ""
echo "============================================================"
```

---

## 검증 체크리스트

| 번호 | 검증 항목 | 확인 명령 | 기대 결과 |
|------|---------|----------|----------|
| 1 | OSINT 5단계 이해 | 구두 설명 | 계획→수집→처리→분석→배포 |
| 2 | HTTP 배너 수집 | curl -I | Server 헤더 확인 |
| 3 | SSH 배너 수집 | nc 접속 | OpenSSH 버전 확인 |
| 4 | 민감 파일 탐색 | curl 경로 스캔 | 비-404 응답 발견 |
| 5 | SSL 인증서 분석 | openssl | Subject/SAN 추출 |
| 6 | 시크릿 패턴 검색 | grep | API 키/패스워드 패턴 |
| 7 | 메타데이터 분석 | exiftool 또는 python | 작성자/소프트웨어 추출 |
| 8 | 서비스 프로파일링 | nmap -sV | 4개 호스트 서비스 매핑 |
| 9 | Google Dorking 이해 | 쿼리 작성 | 5개 이상 쿼리 |
| 10 | 종합 프로파일 | 보고서 | 구조화된 OSINT 결과 |

---

## 자가 점검 퀴즈

**Q1.** OSINT의 5단계 Intelligence Cycle을 순서대로 나열하라.

<details><summary>정답</summary>
1. Planning(계획) → 2. Collection(수집) → 3. Processing(처리) → 4. Analysis(분석) → 5. Dissemination(배포)
</details>

**Q2.** Shodan과 Censys의 주요 차이점은?

<details><summary>정답</summary>
Shodan은 IoT 장치와 서비스 배너 수집에 강점이 있고, Censys는 TLS 인증서 분석과 서비스 분류에 강점이 있다. Censys는 IPv6 일부도 스캔하며, 주 1회 전체 스캔을 수행한다.
</details>

**Q3.** Google Dorking 쿼리 `intitle:"index of /" filetype:sql site:target.com`이 검색하는 것은?

<details><summary>정답</summary>
target.com 도메인에서 디렉토리 목록이 노출된 페이지 중 SQL 파일이 있는 것을 검색한다. 데이터베이스 덤프 파일이 웹 서버에 노출된 경우를 발견할 수 있다.
</details>

**Q4.** GitHub에서 AWS 크레덴셜이 유출되었는지 확인하는 검색 쿼리를 작성하라.

<details><summary>정답</summary>
`"AKIA" filename:.env` 또는 `"AWS_SECRET_ACCESS_KEY" org:target-org` — AWS Access Key ID는 항상 "AKIA"로 시작하므로 이 패턴으로 검색한다.
</details>

**Q5.** 문서 메타데이터에서 추출한 프린터 이름 `\\fileserver01\HP_LaserJet_4F`가 공격자에게 유용한 이유는?

<details><summary>정답</summary>
내부 파일서버 이름(fileserver01)이 노출되어 내부 네트워크 구조를 파악할 수 있고, 프린터 공유 이름에서 층수(4F)와 같은 물리 위치 정보를 추정할 수 있다. 또한 SMB 공유가 존재함을 확인할 수 있다.
</details>

**Q6.** 수동 정찰과 능동 정찰을 구분하는 기준은?

<details><summary>정답</summary>
"내가 보내는 패킷/요청이 대상 시스템에 직접 도달하는가?" 이다. 도달하면 능동 정찰(대상이 탐지 가능), 도달하지 않으면 수동 정찰(대상이 탐지 불가)이다. 예를 들어 Shodan 검색은 수동(이미 수집된 데이터 조회), nmap 스캔은 능동이다.
</details>

**Q7.** OSINT Framework의 주요 카테고리 5가지를 나열하라.

<details><summary>정답</summary>
1. Username — 사용자명 기반 검색
2. Email Address — 이메일 주소 조회
3. Domain Name — 도메인 관련 정보
4. IP Address — IP 기반 검색
5. Social Networks — 소셜미디어 정보
(추가: Dark Web, Metadata, Geolocation, Search Engines 등)
</details>

**Q8.** Juice Shop의 /ftp 경로가 OSINT 관점에서 중요한 이유는?

<details><summary>정답</summary>
/ftp 경로에는 법적 문서, 내부 파일 등이 노출되어 있어 조직의 내부 정보를 수집할 수 있다. 이는 디렉토리 열거(Directory Listing) 취약점으로, 서버 설정 미흡으로 인한 정보 노출이다.
</details>

**Q9.** MITRE ATT&CK에서 T1593.003의 기법명과 설명을 제시하라.

<details><summary>정답</summary>
T1593.003 — Search Open Websites/Domains: Code Repositories. 공개 코드 저장소(GitHub, GitLab 등)에서 대상 조직의 소스코드, 설정 파일, 크레덴셜 등을 검색하는 기법이다.
</details>

**Q10.** 실습 환경(10.20.30.0/24)에 대한 OSINT 프로파일에서 가장 위험한 공격 표면과 그 이유는?

<details><summary>정답</summary>
가장 위험한 공격 표면은 web 서버(10.20.30.80:3000)의 Juice Shop이다. 이유: 1) 알려진 취약점이 다수 존재하는 의도적 취약 애플리케이션, 2) SQL Injection 등 고위험 취약점 포함, 3) /ftp 등 민감 경로 노출, 4) API가 인증 없이 접근 가능.
</details>

---

## 과제

### 과제 1: OSINT 도구 비교 보고서 (개인)
theHarvester, Maltego, recon-ng 세 도구를 비교하는 보고서를 작성하라. 각 도구의 특징, 무료/유료 기능 차이, 데이터 소스, 장단점을 포함할 것.

### 과제 2: 실습 환경 종합 OSINT 보고서 (팀)
10.20.30.0/24 네트워크에 대한 완전한 OSINT 보고서를 작성하라. 배너 수집, 서비스 핑거프린팅, 기술 스택 분석, 공격 표면 평가, 추천 공격 경로를 포함할 것. MITRE ATT&CK 매핑을 반드시 포함할 것.

### 과제 3: OSINT 방어 가이드 (개인)
조직이 OSINT를 통한 정보 유출을 방지하기 위한 가이드라인을 작성하라. 메타데이터 제거, GitHub 시크릿 스캔, 직원 교육, 노출 모니터링 등을 포함할 것.
