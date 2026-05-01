# Bastion Retest Progress

생성: 2026-05-02 02:00:01 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **1285/1285** (100%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 2253 | **+449** |
| fail | 1096 | 745 | -351 |
| qa_fallback | 42 | 28 | -14 |
| no_execution | 77 | 19 | -58 |

**전체 케이스** 3096 · **전체 pass율** 72.8%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **358** | 655 | 25 | 17 | - |
| qa_fallback (42) | **23** | 14 | 3 | 1 | - |
| no_execution (77) | **37** | 30 | 0 | 1 | - |
| error (70) | **30** | 40 | 0 | 0 | - |

**개선 누적**: fail/qa/noexec → pass = **448** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 180 | 142 | 30 | 8 | 0 | 79% |
| agent-ir-adv-nonai | 2 | 0 | 2 | 0 | 0 | 0% |
| agent-ir-ai | 176 | 126 | 45 | 3 | 0 | 72% |
| agent-ir-nonai | 3 | 1 | 2 | 0 | 0 | 33% |
| ai-agent-ai | 134 | 105 | 29 | 0 | 0 | 78% |
| ai-safety-adv-ai | 134 | 90 | 44 | 0 | 0 | 67% |
| ai-safety-ai | 133 | 119 | 14 | 0 | 0 | 89% |
| ai-security-ai | 147 | 97 | 40 | 3 | 7 | 66% |
| attack-adv-ai | 235 | 140 | 88 | 0 | 4 | 60% |
| attack-adv-nonai | 1 | 0 | 1 | 0 | 0 | 0% |
| attack-ai | 240 | 179 | 56 | 0 | 3 | 75% |
| autonomous-ai | 119 | 65 | 49 | 4 | 0 | 55% |
| autonomous-systems-ai | 120 | 80 | 35 | 5 | 0 | 67% |
| battle-adv-ai | 140 | 81 | 46 | 4 | 2 | 58% |
| battle-ai | 166 | 99 | 65 | 0 | 0 | 60% |
| cloud-container-ai | 131 | 115 | 16 | 0 | 0 | 88% |
| compliance-ai | 145 | 97 | 47 | 1 | 0 | 67% |
| physical-pentest-ai | 143 | 108 | 20 | 0 | 1 | 76% |
| secops-ai | 165 | 158 | 0 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 217 | 8 | 0 | 0 | 96% |
| soc-ai | 160 | 140 | 19 | 0 | 0 | 88% |
| web-vuln-ai | 197 | 94 | 89 | 0 | 2 | 48% |

## R3 round (post-R2 잔여 비-pass 재테스트)

- 진행: **575/575** (100%)
- 잔여: 0 steps

**최근 5 step**:
```
[2026-04-27T17:38:58+09:00] R3 #571/575 attack-ai ww12 oo7 (prev=no_execution)
[2026-04-27T17:39:00+09:00] R3 #572/575 attack-ai ww12 oo8 (prev=no_execution)
[2026-04-27T17:39:01+09:00] R3 #573/575 attack-ai ww12 oo9 (prev=no_execution)
[2026-04-27T17:39:03+09:00] R3 #574/575 attack-ai ww12 oo10 (prev=no_execution)
[2026-04-27T17:39:04+09:00] R3 #575/575 attack-ai ww12 oo11 (prev=no_execution)
```

---
*자동 생성: scripts/retest_report.py*