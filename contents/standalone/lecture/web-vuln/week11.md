# W11 — A08 Software and Data Integrity Failures — Supply chain + Deserialization

> 공급망 + 무결성 검증 부재. 2024 xz-utils + Log4Shell 의 *역대 최대 사고*.

## 핵심
- **공급망 공격** = 신뢰 받은 source 의 *변조*
- **deserialization** = `pickle.loads()` 등 의 *임의 코드 실행*

## modern 표준 (SLSA + Sigstore + SBOM)
- SLSA 1-4 level (Google + Linux Foundation)
- Sigstore — keyless signing
- SBOM — CycloneDX / SPDX

## CWE
- CWE-502 Deserialization of Untrusted Data
- CWE-829 Inclusion of Functionality from Untrusted Sphere
- CWE-1357 Reliance on Insufficiently Trustworthy Component
