# Bastion Retest Progress

생성: 2026-04-25 14:42:08 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **277/1285** (21%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 1840 | **+36** |
| fail | 1096 | 931 | -165 |
| qa_fallback | 42 | 5 | -37 |
| no_execution | 77 | 82 | +5 |

**전체 케이스** 3089 · **전체 pass율** 59.6%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **20** | 909 | 5 | 1 | - |
| qa_fallback (42) | **16** | 22 | 0 | 4 | - |
| no_execution (77) | **0** | 0 | 0 | 77 | - |
| error (70) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **36** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 127 | 16 | 0 | 5 | 71% |
| agent-ir-ai | 176 | 115 | 10 | 0 | 0 | 65% |
| ai-agent-ai | 134 | 78 | 11 | 0 | 1 | 58% |
| ai-safety-adv-ai | 134 | 67 | 3 | 0 | 1 | 50% |
| ai-safety-ai | 133 | 106 | 8 | 0 | 0 | 80% |
| ai-security-ai | 147 | 70 | 50 | 5 | 0 | 48% |
| attack-adv-ai | 235 | 113 | 101 | 0 | 21 | 48% |
| attack-ai | 240 | 104 | 118 | 0 | 18 | 43% |
| autonomous-ai | 119 | 55 | 64 | 0 | 0 | 46% |
| autonomous-systems-ai | 120 | 66 | 53 | 0 | 1 | 55% |
| battle-adv-ai | 140 | 60 | 70 | 0 | 10 | 43% |
| battle-ai | 166 | 71 | 93 | 0 | 2 | 43% |
| cloud-container-ai | 131 | 99 | 31 | 0 | 0 | 76% |
| compliance-ai | 145 | 93 | 52 | 0 | 0 | 64% |
| physical-pentest-ai | 143 | 74 | 58 | 0 | 11 | 52% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 216 | 9 | 0 | 0 | 96% |
| soc-ai | 160 | 117 | 43 | 0 | 0 | 73% |
| web-vuln-ai | 197 | 51 | 134 | 0 | 12 | 26% |

---
*자동 생성: scripts/retest_report.py*