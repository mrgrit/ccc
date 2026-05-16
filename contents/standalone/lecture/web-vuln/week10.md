# W10 — A07 Identification and Authentication Failures

> *brute force + weak password + MFA bypass + session fixation*.

## 5 대표 패턴
1. **brute force** — rate limit 부재
2. **weak password** — 12 char 미만 + 단순 dictionary
3. **MFA bypass** — recovery code 약함 / TOTP secret 노출
4. **session fixation** — login 전 session 재사용
5. **credential stuffing** — 외부 유출 의 credential 의 *재시도*

## NIST SP 800-63B (2017 update)
- *min length 12+* (이전 8)
- *복잡도 강제 X* — *length 가 더 중요*
- *no forced rotation* (이전 90일 마다)
- *해킹 데이터베이스* 비교 (HaveIBeenPwned API)

## MFA 표준
- SMS / 이메일 — *약함* (SIM swap / phishing)
- TOTP (Google Authenticator) — *권장*
- FIDO2 / WebAuthn — *최고* (hardware key)
- 생체 — *Apple/Android* 표준

## 자기 점검
```
[ ] 5 패턴 응답?
[ ] NIST 의 *2017 변경* 응답?
[ ] MFA 4 표준 + 위험도 응답?
```
