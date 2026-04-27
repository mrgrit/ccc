# Bastion Retest Progress

생성: 2026-04-27 16:00:01 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **1285/1285** (100%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 2049 | **+245** |
| fail | 1096 | 473 | -623 |
| qa_fallback | 42 | 16 | -26 |
| no_execution | 77 | 256 | +179 |

**전체 케이스** 3089 · **전체 pass율** 66.3%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **193** | 410 | 15 | 228 | - |
| qa_fallback (42) | **21** | 16 | 1 | 3 | - |
| no_execution (77) | **8** | 19 | 0 | 6 | - |
| error (70) | **23** | 28 | 0 | 19 | - |

**개선 누적**: fail/qa/noexec → pass = **245** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 129 | 19 | 0 | 0 | 72% |
| agent-ir-ai | 176 | 126 | 45 | 3 | 0 | 72% |
| ai-agent-ai | 134 | 105 | 29 | 0 | 0 | 78% |
| ai-safety-adv-ai | 134 | 90 | 44 | 0 | 0 | 67% |
| ai-safety-ai | 133 | 119 | 14 | 0 | 0 | 89% |
| ai-security-ai | 147 | 82 | 6 | 0 | 59 | 56% |
| attack-adv-ai | 235 | 134 | 56 | 0 | 42 | 57% |
| attack-ai | 240 | 120 | 17 | 0 | 9 | 50% |
| autonomous-ai | 119 | 65 | 45 | 4 | 4 | 55% |
| autonomous-systems-ai | 120 | 80 | 35 | 5 | 0 | 67% |
| battle-adv-ai | 140 | 60 | 13 | 3 | 57 | 43% |
| battle-ai | 166 | 72 | 8 | 0 | 84 | 43% |
| cloud-container-ai | 131 | 115 | 16 | 0 | 0 | 88% |
| compliance-ai | 145 | 97 | 46 | 1 | 1 | 67% |
| physical-pentest-ai | 143 | 76 | 11 | 0 | 0 | 53% |
| secops-ai | 165 | 158 | 0 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 217 | 8 | 0 | 0 | 96% |
| soc-ai | 160 | 140 | 19 | 0 | 0 | 88% |
| web-vuln-ai | 197 | 64 | 42 | 0 | 0 | 32% |

## R3 round (post-R2 잔여 비-pass 재테스트)

- 진행: **433/575** (75%)
- 잔여: 142 steps

**최근 5 step**:
```
[2026-04-27T15:46:24+09:00] R3 #430/575 agent-ir-ai w15 o11 (prev=error)
[2026-04-27T15:51:56+09:00] R3 #431/575 agent-ir-adv-ai w1 o1 (prev=fail)
[2026-04-27T15:55:46+09:00] R3 #432/575 agent-ir-adv-ai w1 o2 (prev=fail)
[2026-04-27T15:57:31+09:00] R3 #433/575 agent-ir-adv-ai w1 o3 (prev=fail)
[2026-04-27T15:59:15+09:00] R3 #434/575 agent-ir-adv-ai w2 o1 (prev=error)
```

---
*자동 생성: scripts/retest_report.py*