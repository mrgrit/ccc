# Bastion Retest Progress

생성: 2026-04-25 06:32:47 (KST)
세션 시작: 2026-04-25T02:33:00
진행: **167/1311** (12%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1778 | 1792 | **+14** |
| fail | 1113 | 1184 | +71 |
| qa_fallback | 122 | 35 | -87 |
| no_execution | 75 | 77 | +2 |

**전체 케이스** 3089 · **전체 pass율** 58.0%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1113) | **0** | 1108 | 3 | 2 | - |
| qa_fallback (122) | **14** | 76 | 32 | 0 | - |
| no_execution (75) | **0** | 0 | 0 | 75 | - |
| error (1) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **14** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 120 | 49 | 5 | 5 | 67% |
| agent-ir-ai | 176 | 101 | 75 | 0 | 0 | 57% |
| ai-agent-ai | 134 | 73 | 51 | 10 | 0 | 54% |
| ai-safety-adv-ai | 134 | 63 | 70 | 1 | 0 | 47% |
| ai-safety-ai | 133 | 104 | 29 | 0 | 0 | 78% |
| ai-security-ai | 147 | 60 | 84 | 3 | 0 | 41% |
| attack-adv-ai | 235 | 113 | 101 | 0 | 21 | 48% |
| attack-ai | 240 | 104 | 118 | 1 | 17 | 43% |
| autonomous-ai | 119 | 50 | 60 | 9 | 0 | 42% |
| autonomous-systems-ai | 120 | 65 | 53 | 1 | 1 | 54% |
| battle-adv-ai | 140 | 60 | 70 | 1 | 9 | 43% |
| battle-ai | 166 | 71 | 93 | 1 | 1 | 43% |
| cloud-container-ai | 131 | 99 | 31 | 0 | 0 | 76% |
| compliance-ai | 145 | 93 | 52 | 0 | 0 | 64% |
| physical-pentest-ai | 143 | 74 | 57 | 1 | 11 | 52% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 216 | 9 | 0 | 0 | 96% |
| soc-ai | 160 | 118 | 42 | 0 | 0 | 74% |
| web-vuln-ai | 197 | 50 | 133 | 2 | 12 | 25% |

---
*자동 생성: scripts/retest_report.py*