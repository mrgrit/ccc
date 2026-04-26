# Bastion Retest Progress

생성: 2026-04-27 08:47:22 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **1285/1285** (100%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 2014 | **+210** |
| fail | 1096 | 428 | -668 |
| qa_fallback | 42 | 13 | -29 |
| no_execution | 77 | 262 | +185 |

**전체 케이스** 3089 · **전체 pass율** 65.2%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **161** | 360 | 13 | 234 | - |
| qa_fallback (42) | **18** | 21 | 0 | 3 | - |
| no_execution (77) | **8** | 19 | 0 | 6 | - |
| error (70) | **23** | 28 | 0 | 19 | - |

**개선 누적**: fail/qa/noexec → pass = **210** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 128 | 20 | 0 | 0 | 72% |
| agent-ir-ai | 176 | 115 | 10 | 0 | 0 | 65% |
| ai-agent-ai | 134 | 86 | 18 | 0 | 0 | 64% |
| ai-safety-adv-ai | 134 | 90 | 44 | 0 | 0 | 67% |
| ai-safety-ai | 133 | 119 | 14 | 0 | 0 | 89% |
| ai-security-ai | 147 | 82 | 6 | 0 | 59 | 56% |
| attack-adv-ai | 235 | 134 | 56 | 0 | 42 | 57% |
| attack-ai | 240 | 120 | 17 | 0 | 9 | 50% |
| autonomous-ai | 119 | 62 | 47 | 3 | 7 | 52% |
| autonomous-systems-ai | 120 | 80 | 34 | 6 | 0 | 67% |
| battle-adv-ai | 140 | 60 | 13 | 3 | 57 | 43% |
| battle-ai | 166 | 71 | 7 | 0 | 87 | 43% |
| cloud-container-ai | 131 | 115 | 16 | 0 | 0 | 88% |
| compliance-ai | 145 | 97 | 46 | 1 | 1 | 67% |
| physical-pentest-ai | 143 | 76 | 11 | 0 | 0 | 53% |
| secops-ai | 165 | 158 | 0 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 217 | 8 | 0 | 0 | 96% |
| soc-ai | 160 | 140 | 19 | 0 | 0 | 88% |
| web-vuln-ai | 197 | 64 | 42 | 0 | 0 | 32% |

---
*자동 생성: scripts/retest_report.py*