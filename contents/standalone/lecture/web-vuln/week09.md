# W09 — A06 Vulnerable Components

> 외부 lib 의 *알려진 vuln 사용*. *직접 코드 X*. SCA + SBOM 의 *2 표준* 으로 audit.

## 핵심 사례 (역대 최대)
- **Log4Shell** (CVE-2021-44228) — Log4j JNDI, CVSS 10.0
- **Spring4Shell** (CVE-2022-22965) — Spring RCE, CVSS 9.8
- **xz-utils** (CVE-2024-3094) — Jia Tan 2년 social, CVSS 10.0

## SCA 5 도구
- npm audit / yarn audit (Node)
- pip-audit (Python)
- Snyk / Dependabot (다언어)
- retire.js (client JS)
- OWASP Dependency-Check (Java)

## SBOM (Software Bill of Materials)
- **CycloneDX** (OWASP) — XML/JSON
- **SPDX** (Linux Foundation) — RDF
- *모든 component + version + license + hash* 의 표준

## 방어 4 표준
1. *모든 dependency* 의 *최신 stable* 유지
2. *주 1 회* SCA 자동 (CI 통합)
3. *direct + transitive* dependency 모두 audit
4. *unmaintained* lib (last update > 1 년) 의 *교체*

## 자기 점검
```
[ ] Log4Shell + Spring4Shell + xz-utils 의 *5 항목* 응답?
[ ] SCA 5 도구 + SBOM 2 표준 응답?
[ ] direct vs transitive dependency 응답?
```
