# W12 — A09 Security Logging and Monitoring Failures

> *log + monitor 부재* = *사고 추적 불가*. ModSec audit + Wazuh 통합 + 보존 정책.

## 표준 5 종 로그
1. 모든 인증 시도 (성공 + 실패)
2. 권한 변경
3. 데이터 접근 (sensitive)
4. system event
5. WAF 차단

## 한국 보존 정책
- 전자금융감독규정: 5 년
- 개인정보보호법: *유출 시 1 년 보고*

## 6v6 의 실 운영
- ModSec audit log = 19766 line (2026-05-16 실측)
- Wazuh alerts.json 통합

## CWE
- CWE-778 Insufficient Logging
- CWE-779 Excessive Logging (반대 — 너무 많음)
