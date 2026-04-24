# Bastion Retest Progress

생성: 2026-04-24 20:32:47 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **1644/1644** (100%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1778 | **+302** |
| fail | 1448 | 1113 | -335 |
| qa_fallback | 144 | 122 | -22 |
| no_execution | 21 | 75 | +54 |

**전체 케이스** 3089 · **전체 pass율** 57.6%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **271** | 1046 | 92 | 39 | - |
| qa_fallback (175) | **28** | 68 | 42 | 36 | - |
| no_execution (21) | **5** | 15 | 1 | 0 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **304** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 120 | 53 | 3 | 3 | 67% |
| agent-ir-ai | 176 | 100 | 72 | 4 | 0 | 57% |
| ai-agent-ai | 134 | 69 | 45 | 20 | 0 | 51% |
| ai-safety-adv-ai | 134 | 63 | 65 | 6 | 0 | 47% |
| ai-safety-ai | 133 | 103 | 28 | 2 | 0 | 77% |
| ai-security-ai | 147 | 58 | 72 | 17 | 0 | 39% |
| attack-adv-ai | 235 | 113 | 96 | 5 | 21 | 48% |
| attack-ai | 240 | 101 | 110 | 12 | 17 | 42% |
| autonomous-ai | 119 | 49 | 58 | 12 | 0 | 41% |
| autonomous-systems-ai | 120 | 64 | 45 | 10 | 1 | 53% |
| battle-adv-ai | 140 | 59 | 69 | 3 | 9 | 42% |
| battle-ai | 166 | 71 | 92 | 2 | 1 | 43% |
| cloud-container-ai | 131 | 99 | 31 | 0 | 0 | 76% |
| compliance-ai | 145 | 93 | 48 | 4 | 0 | 64% |
| physical-pentest-ai | 143 | 74 | 49 | 9 | 11 | 52% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 216 | 6 | 3 | 0 | 96% |
| soc-ai | 160 | 118 | 42 | 0 | 0 | 74% |
| web-vuln-ai | 197 | 50 | 125 | 10 | 12 | 25% |

---
*자동 생성: scripts/retest_report.py*