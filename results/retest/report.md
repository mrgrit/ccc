# Bastion Retest Progress

생성: 2026-04-24 08:40:19 (KST)
세션 시작: 2026-04-23T14:51:58
진행: **1027/1644** (62%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1476 | 1703 | **+227** |
| fail | 1448 | 1204 | -244 |
| qa_fallback | 144 | 99 | -45 |
| no_execution | 21 | 82 | +61 |

**전체 케이스** 3089 · **전체 pass율** 55.1%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1448) | **200** | 1159 | 69 | 20 | - |
| qa_fallback (175) | **30** | 54 | 44 | 46 | - |
| no_execution (21) | **0** | 0 | 0 | 21 | - |
| error (0) | **0** | 0 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **230** 건

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
| autonomous-systems-ai | 120 | 61 | 48 | 10 | 1 | 51% |
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