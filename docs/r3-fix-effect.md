# R3 Fix-Effect Report

*paper §6.2 Track A Table 의 raw data*


## Round 별 결과

| Round | Total | Pass (rate) | >280s % | avg elapsed |
|---|---|---|---|---|
| R3 main | 650 | 140 (21.5%) | 6.0% | 137s |
| R3 noexec V2 | 259 | 70 (27.0%) | 44.8% | 265s |
| attack-ai supp | 94 | 32 (34.0%) | 53.2% | 273s |
| low-3 supp (in flight) | 31 | 2 (6.5%) | 64.5% | 310s |
| R4 (예정) | — | — | — | — |

## R3 fix 적용 (2026-04-30)

| Fix | 변경 | 기대 효과 |
|---|---|---|
| #1 (76d1b921) | shell IP 자동 치환 (10.20.30.80→192.168.0.108 attacker 측) | attacker→web unreachable 차단 |
| #2 (1625b03e) | curl -s 짧은 응답 → -i -L 자동 retry | header/status 누락 차단 |
| #3 (e72ae39a) | self_verify·synthesis 프롬프트 강화 | self_verify_fail 무한 반복 차단 |
| #4 (5070990a) | 최종 답변 4섹션 강제 + target=web 금지 | judge no-output / 방어 누락 회복 |
| #5 (8e227393) | skill output truncation 1000→2500자 | curl 응답 잘림 차단 |
| #6 (db38639e) | call_bastion 네트워크 에러 1회 retry | bastion restart 시 ERROR 차단 |

## 누적 best-verdict (bastion_test_progress.json)
- pass: **2165/3090** (70.1%)
- fail: 732
- error: 149
- no_execution: 16
- qa_fallback: 28
