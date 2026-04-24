# Bastion Retest Progress

생성: 2026-04-24 16:32:44 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **1497/1644** (91%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1769 | **+293** |
| fail | 1448 | 1107 | -341 |
| qa_fallback | 144 | 115 | -29 |
| no_execution | 21 | 97 | +76 |

**전체 케이스** 3089 · **전체 pass율** 57.3%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **266** | 1062 | 85 | 35 | - |
| qa_fallback (175) | **30** | 54 | 44 | 46 | - |
| no_execution (21) | **0** | 0 | 0 | 21 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **296** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 179 | 120 | 53 | 3 | 3 | 67% |
| agent-ir-ai | 176 | 100 | 72 | 4 | 0 | 57% |
| ai-agent-ai | 134 | 70 | 46 | 18 | 0 | 52% |
| ai-safety-adv-ai | 134 | 63 | 64 | 7 | 0 | 47% |
| ai-safety-ai | 133 | 103 | 28 | 2 | 0 | 77% |
| ai-security-ai | 147 | 58 | 65 | 19 | 5 | 39% |
| attack-adv-ai | 235 | 113 | 96 | 5 | 21 | 48% |
| attack-ai | 240 | 101 | 109 | 12 | 18 | 42% |
| autonomous-ai | 119 | 49 | 58 | 12 | 0 | 41% |
| autonomous-systems-ai | 120 | 64 | 45 | 10 | 1 | 53% |
| battle-adv-ai | 140 | 59 | 69 | 3 | 9 | 42% |
| battle-ai | 166 | 71 | 91 | 2 | 2 | 43% |
| cloud-container-ai | 131 | 99 | 30 | 0 | 1 | 76% |
| compliance-ai | 145 | 93 | 48 | 4 | 0 | 64% |
| physical-pentest-ai | 143 | 74 | 48 | 8 | 13 | 52% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 216 | 6 | 3 | 0 | 96% |
| soc-ai | 160 | 113 | 31 | 0 | 16 | 71% |
| web-vuln-ai | 197 | 45 | 141 | 3 | 8 | 23% |

---
*자동 생성: scripts/retest_report.py*