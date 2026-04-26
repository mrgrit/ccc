# Bastion Retest Progress

생성: 2026-04-26 10:32:50 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **1054/1285** (82%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 1905 | **+101** |
| fail | 1096 | 369 | -727 |
| qa_fallback | 42 | 21 | -21 |
| no_execution | 77 | 431 | +354 |

**전체 케이스** 3089 · **전체 pass율** 61.7%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **85** | 347 | 21 | 350 | - |
| qa_fallback (42) | **16** | 22 | 0 | 4 | - |
| no_execution (77) | **0** | 0 | 0 | 77 | - |
| error (70) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **101** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 127 | 16 | 0 | 5 | 71% |
| agent-ir-ai | 176 | 115 | 10 | 0 | 0 | 65% |
| ai-agent-ai | 134 | 78 | 11 | 0 | 1 | 58% |
| ai-safety-adv-ai | 134 | 67 | 3 | 0 | 1 | 50% |
| ai-safety-ai | 133 | 106 | 8 | 0 | 0 | 80% |
| ai-security-ai | 147 | 81 | 37 | 7 | 0 | 55% |
| attack-adv-ai | 235 | 113 | 7 | 0 | 115 | 48% |
| attack-ai | 240 | 106 | 8 | 1 | 125 | 44% |
| autonomous-ai | 119 | 62 | 47 | 3 | 7 | 52% |
| autonomous-systems-ai | 120 | 80 | 33 | 6 | 1 | 67% |
| battle-adv-ai | 140 | 60 | 13 | 3 | 64 | 43% |
| battle-ai | 166 | 71 | 7 | 0 | 88 | 43% |
| cloud-container-ai | 131 | 112 | 18 | 0 | 0 | 85% |
| compliance-ai | 145 | 97 | 46 | 1 | 1 | 67% |
| physical-pentest-ai | 143 | 76 | 11 | 0 | 11 | 53% |
| secops-ai | 165 | 158 | 0 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 216 | 0 | 0 | 0 | 96% |
| soc-ai | 160 | 129 | 8 | 0 | 0 | 81% |
| web-vuln-ai | 197 | 51 | 86 | 0 | 12 | 26% |

---
*자동 생성: scripts/retest_report.py*