# Bastion Retest Progress

생성: 2026-04-26 02:32:50 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **677/1285** (52%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 1874 | **+70** |
| fail | 1096 | 649 | -447 |
| qa_fallback | 42 | 18 | -24 |
| no_execution | 77 | 317 | +240 |

**전체 케이스** 3089 · **전체 pass율** 60.7%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **54** | 627 | 18 | 236 | - |
| qa_fallback (42) | **16** | 22 | 0 | 4 | - |
| no_execution (77) | **0** | 0 | 0 | 77 | - |
| error (70) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **70** 건

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
| battle-adv-ai | 140 | 60 | 42 | 1 | 37 | 43% |
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