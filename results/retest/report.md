# Bastion Retest Progress

생성: 2026-04-23 16:47:06 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **121/1644** (7%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1498 | **+22** |
| fail | 1448 | 1489 | +41 |
| qa_fallback | 144 | 47 | -97 |
| no_execution | 21 | 54 | +33 |

**전체 케이스** 3089 · **전체 pass율** 48.5%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **0** | 1448 | 0 | 0 | - |
| qa_fallback (175) | **25** | 50 | 61 | 38 | - |
| no_execution (21) | **0** | 0 | 0 | 21 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **25** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 107 | 71 | 1 | 0 | 60% |
| agent-ir-ai | 176 | 82 | 94 | 0 | 0 | 47% |
| ai-agent-ai | 134 | 41 | 88 | 5 | 0 | 31% |
| ai-safety-adv-ai | 134 | 52 | 80 | 2 | 0 | 39% |
| ai-safety-ai | 133 | 61 | 72 | 0 | 0 | 46% |
| ai-security-ai | 147 | 50 | 85 | 7 | 5 | 34% |
| attack-adv-ai | 235 | 100 | 116 | 2 | 17 | 43% |
| attack-ai | 240 | 88 | 145 | 1 | 6 | 37% |
| autonomous-ai | 119 | 32 | 84 | 3 | 0 | 27% |
| autonomous-systems-ai | 120 | 25 | 93 | 2 | 0 | 21% |
| battle-adv-ai | 140 | 41 | 94 | 0 | 5 | 29% |
| battle-ai | 166 | 58 | 105 | 1 | 2 | 35% |
| cloud-container-ai | 131 | 88 | 41 | 0 | 1 | 67% |
| compliance-ai | 145 | 85 | 59 | 1 | 0 | 59% |
| physical-pentest-ai | 143 | 67 | 69 | 5 | 2 | 47% |
| secops-ai | 165 | 158 | 6 | 1 | 0 | 96% |
| soc-adv-ai | 225 | 214 | 5 | 6 | 0 | 95% |
| soc-ai | 160 | 110 | 34 | 0 | 16 | 69% |
| web-vuln-ai | 197 | 39 | 148 | 10 | 0 | 20% |

---
*자동 생성: scripts/retest_report.py*