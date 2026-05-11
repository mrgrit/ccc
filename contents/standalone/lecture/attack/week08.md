# Week 08 — 중간고사 — CTF 형식 (90분)

> 본 주차는 attack W01-W07 의 종합 평가. CTF (Capture The Flag) 형식으로 진행.
> 8 vuln 사이트 중 무작위 3 challenge 제공, 각 30점 + 시간 보너스 10점 = 100점.

## 시험 규칙

- 시간: 90분 (정시 종료)
- 학생 PC + Burp / sqlmap / ffuf 등 모든 도구 사용 가능
- 답 = flag (각 challenge 의 hidden string)
- AI 어시스턴트 / 다른 학생 통신 금지
- 본인 작업 history (bash_history 또는 .ZSH_history) 제출

## CTF Challenge 예시

### Challenge 1 (30점) — Reflected XSS bypass

> juice.6v6.lab 의 search field 에 ModSec 941 룰을 우회하는 XSS payload 를 보내고
> alert(1) 이 실행되도록 한다. flag = 본인 payload 의 SHA256.

### Challenge 2 (30점) — SQLi data exfil

> dvwa.6v6.lab 의 SQLi (low 수준) 에서 user 테이블의 모든 컬럼 + row 추출. flag =
> admin 사용자의 password hash.

### Challenge 3 (30점) — IDOR + JWT

> JuiceShop 의 /api/Users/N (N=1~5) 접근 시도. 다른 사용자의 데이터 발견 + JWT
> 변조로 admin 권한 획득. flag = admin@juice-sh.op 의 wallet balance.

### 시간 보너스 (10점)

- 45분 안에 3 challenge 모두 해결 → +10점
- 60분 안에 → +5점

## 평가 매트릭스

| 점수 | 의미 |
|------|------|
| 90+ | A — W09 advanced track |
| 70-89 | B — W09 표준 진행 |
| 50-69 | C — W01-07 부분 재시험 |
| 50 미만 | F — 재수강 |

## 시험 후 정리

본인 환경에서 추가한 룰 / 파일 모두 cleanup. 다른 학생에 영향 없도록 30분 안에 정리.
