# Bastion Retest Progress

생성: 2026-04-23 18:40:23 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **233/1644** (14%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1520 | **+44** |
| fail | 1448 | 1471 | +23 |
| qa_fallback | 144 | 32 | -112 |
| no_execution | 21 | 65 | +44 |

**전체 케이스** 3089 · **전체 pass율** 49.2%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **17** | 1426 | 2 | 3 | - |
| qa_fallback (175) | **30** | 54 | 44 | 46 | - |
| no_execution (21) | **0** | 0 | 0 | 21 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **47** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 120 | 53 | 3 | 3 | 67% |
| agent-ir-ai | 176 | 86 | 90 | 0 | 0 | 49% |
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
| compliance-ai | 145 | 85 | 60 | 0 | 0 | 59% |
| physical-pentest-ai | 143 | 68 | 69 | 0 | 6 | 48% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 215 | 7 | 3 | 0 | 96% |
| soc-ai | 160 | 110 | 34 | 0 | 16 | 69% |
| web-vuln-ai | 197 | 42 | 148 | 3 | 4 | 21% |

---
*자동 생성: scripts/retest_report.py*