# W14 — API Security Top 10 (2023) — REST + GraphQL

> OWASP API Top 10 (2023, 신규). REST + GraphQL 의 *5 vuln 매트릭스*.

## API Top 10 (2023)
- API1 BOLA (IDOR for API)
- API2 Broken Auth
- API3 Broken Property Auth
- API4 Resource Consumption (DoS)
- API5 Broken Function Auth
- API6 Sensitive Business Flow
- API7 SSRF
- API8 Misconfig
- API9 Improper Inventory (shadow API)
- API10 Unsafe Consumption

## GraphQL 5 vuln
1. introspection enabled
2. batching attack (DoS)
3. circular query
4. field suggestion (info leak)
5. mutation 의 권한 우회

## modern API 방어 5
1. *모든 endpoint* 의 *권한 검증*
2. rate limit (per user / per IP)
3. *introspection* production 거부
4. GraphQL depth limit (5+)
5. API gateway (Kong / AWS API Gateway)
