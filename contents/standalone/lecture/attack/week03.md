# Week 03 — 웹 애플리케이션 구조 + Burp Suite + JuiceShop

> 웹 공격 (W04-07) 의 전제는 HTTP/HTTPS 요청·응답 흐름의 정확한 이해. 본 주차는
> Burp Suite proxy 로 6v6 의 JuiceShop 트래픽 조작 + JuiceShop 의 challenge 데이터
> 모델 학습.

## 학습 목표

1. HTTP 의 method (GET / POST / PUT / DELETE / PATCH / OPTIONS) 차이
2. HTTP header (User-Agent / Cookie / Authorization / X-Forwarded-For) 의 의미
3. Burp Suite proxy 설정 + 트래픽 intercept / modify
4. JuiceShop 의 80+ challenge + REST API 구조
5. session cookie + JWT 의 차이
6. CSP / CORS / Same-Origin Policy

## 1. HTTP method 6 종

| method | 의미 | idempotent |
|--------|------|------------|
| GET    | 자원 조회 | yes |
| POST   | 자원 생성 | no |
| PUT    | 전체 갱신 | yes |
| PATCH  | 부분 갱신 | no |
| DELETE | 삭제 | yes |
| OPTIONS | CORS preflight | yes |

## 2. 핵심 header

| header | 의미 |
|--------|------|
| User-Agent | 클라이언트 식별 |
| Cookie | session token |
| Authorization | Bearer / Basic auth |
| Content-Type | body 형식 (json/form/multipart) |
| X-Forwarded-For | 프록시 chain |
| Referer | 출처 페이지 |
| Origin | CORS 검증 |

## 3. Burp Suite Proxy

### 3.1 설치 + 설정

```
# attacker 컨테이너 안에서 (또는 학생 PC)
burpsuite                       # GUI 진입
# Proxy → Options → 127.0.0.1:8080
# 브라우저의 proxy 설정 = 127.0.0.1:8080
```

### 3.2 intercept

요청을 capture → 수정 → forward.

### 3.3 repeater

같은 요청 반복 + 변형. SQLi / XSS payload 시도.

### 3.4 intruder

automated brute / fuzzing.

## 4. JuiceShop 구조

### 4.1 80+ challenge 카테고리

- Broken Authentication (인증 우회)
- Sensitive Data Exposure (민감 데이터 노출)
- Broken Access Control (권한 우회)
- Injection (SQLi, XSS)
- Security Misconfiguration
- Cryptographic Issues
- API Security
- Improper Input Validation

### 4.2 REST API endpoints

```
GET  /api/Users               # 사용자 목록
GET  /api/Products            # 제품 목록
POST /rest/user/login         # 로그인
GET  /rest/user/whoami        # 현재 사용자
```

### 4.3 score-card

JuiceShop 의 `/#/score-board` 에 모든 challenge + 점수 + 해결 여부. 학습용 score 보드.

## 5. session cookie vs JWT

### 5.1 session cookie

```
Set-Cookie: PHPSESSID=abc123; HttpOnly; Secure; SameSite=Strict
```

server-side session store. 탈취 시 세션 hijack.

### 5.2 JWT (JSON Web Token)

```
Authorization: Bearer eyJhbGciOiJIUzI1NiI...
```

base64 인코딩된 3 부분 (header.payload.signature). server stateless.

JWT 보안 이슈:
- `alg: none` 우회 → header 변조
- 약한 secret → brute force
- payload 만 인코딩 (암호화 X) → 민감 데이터 노출

## 6. CSP / CORS

### 6.1 Content Security Policy

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-xxx'
```

XSS 차단 효과. nonce / hash 로 inline script 제어.

### 6.2 CORS

```
Access-Control-Allow-Origin: https://trusted.com
```

cross-origin 요청 허용. wildcard `*` 는 위험.

## 7. 실습 1~5

### 1 — JuiceShop 접근

```
ssh 6v6-attacker 'curl -s -H "Host: juice.6v6.lab" http://10.20.30.1/ | head -30'
ssh 6v6-attacker 'curl -s -H "Host: juice.6v6.lab" http://10.20.30.1/api/Products | head -50'
```

### 2 — score-board 발견

```
# JuiceShop 의 score-board 가 hidden URL
ssh 6v6-attacker 'curl -s -H "Host: juice.6v6.lab" "http://10.20.30.1/api/Challenges" 2>&1 | head'
```

### 3 — 로그인 시도 + JWT 받기

```
ssh 6v6-attacker 'curl -s -X POST -H "Host: juice.6v6.lab" -H "Content-Type: application/json" -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}" http://10.20.30.1/rest/user/login'
```

### 4 — JWT 디코드

```
JWT="eyJhbGc..."
echo "$JWT" | cut -d. -f1 | base64 -d 2>/dev/null  # header
echo "$JWT" | cut -d. -f2 | base64 -d 2>/dev/null  # payload
```

### 5 — Burp suite proxy 시연

(GUI 필요 → 학생 PC 의 burp + JuiceShop 접근)

## 8. 과제

A. JuiceShop API 매핑 (필수) — 10+ endpoint + method + 응답 구조
B. JWT 디코드 (심화) — JuiceShop 의 JWT header + payload + signature 분석
C. CSP 검토 (정성) — JuiceShop 의 CSP 헤더 + XSS 회피 가능성

## 9. W04 (SQLi) 예고

sqlmap + DVWA + JuiceShop 의 SQLi challenge.
