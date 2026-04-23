# Bastion Retest Progress

생성: 2026-04-23 14:55:01 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **0/1613** (0%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1476 | **+0** |
| fail | 1448 | 1449 | +1 |
| qa_fallback | 144 | 143 | -1 |
| no_execution | 21 | 21 | +0 |

**전체 케이스** 3089 · **전체 pass율** 47.8%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **0** | 1448 | 0 | 0 | - |
| qa_fallback (144) | **0** | 1 | 143 | 0 | - |
| no_execution (21) | **0** | 0 | 0 | 21 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **0** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 106 | 71 | 2 | 0 | 59% |
| agent-ir-ai | 176 | 79 | 91 | 6 | 0 | 45% |
| ai-agent-ai | 134 | 39 | 83 | 12 | 0 | 29% |
| ai-safety-adv-ai | 134 | 52 | 78 | 4 | 0 | 39% |
| ai-safety-ai | 133 | 61 | 72 | 0 | 0 | 46% |
| ai-security-ai | 147 | 49 | 83 | 15 | 0 | 33% |
| attack-adv-ai | 235 | 94 | 94 | 47 | 0 | 40% |
| attack-ai | 240 | 88 | 143 | 8 | 1 | 37% |
| autonomous-ai | 119 | 26 | 83 | 10 | 0 | 22% |
| autonomous-systems-ai | 120 | 24 | 92 | 4 | 0 | 20% |
| battle-adv-ai | 140 | 39 | 94 | 7 | 0 | 28% |
| battle-ai | 166 | 58 | 104 | 3 | 1 | 35% |
| cloud-container-ai | 131 | 88 | 40 | 2 | 1 | 67% |
| compliance-ai | 145 | 85 | 59 | 1 | 0 | 59% |
| physical-pentest-ai | 143 | 67 | 69 | 5 | 2 | 47% |
| secops-ai | 165 | 158 | 6 | 1 | 0 | 96% |
| soc-adv-ai | 225 | 214 | 5 | 6 | 0 | 95% |
| soc-ai | 160 | 110 | 34 | 0 | 16 | 69% |
| web-vuln-ai | 197 | 39 | 148 | 10 | 0 | 20% |

---
*자동 생성: scripts/retest_report.py*