# W13 — A10 SSRF (Server-Side Request Forgery)

> 서버 의 *공격자 의도* 의 *내부 요청*. cloud metadata 노출 의 *주 원인*.

## 표준 cloud metadata
- AWS: `169.254.169.254/latest/meta-data/`
- GCP: `metadata.google.internal/`
- Azure: `169.254.169.254/metadata/instance`

## 5 방어
1. whitelist URL
2. DNS rebind 방어
3. schema 제한 (http/https 만)
4. port 제한 (80/443)
5. redirect 추적 X

## 한국 사례 (2024-02)
- 공공 기관 SSRF → AWS metadata → IAM → S3 의 주민등록번호 노출
