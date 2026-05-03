# Bastion Retest Progress

생성: 2026-05-04 04:00:01 (KST)
세션 시작: 2026-04-25T10:48:07
진행: **1285/1285** (100%)

## 전체 pass 추이

| 지표 | Baseline | 현재 | Δ |
|------|----------|------|---|
| pass | 1804 | 2388 | **+584** |
| fail | 1096 | 626 | -470 |
| qa_fallback | 42 | 28 | -14 |
| no_execution | 77 | 33 | -44 |

**전체 케이스** 3096 · **전체 pass율** 77.1%

## Retest 큐 플립 현황

| 이전 상태 → | pass | fail | qa_fallback | no_execution | 미진행 |
|------|------|------|-------------|--------------|--------|
| fail (1096) | **464** | 562 | 25 | 29 | - |
| qa_fallback (42) | **24** | 13 | 3 | 1 | - |
| no_execution (77) | **52** | 19 | 0 | 2 | - |
| error (70) | **43** | 26 | 0 | 1 | - |

**개선 누적**: fail/qa/noexec → pass = **583** 건

## 과목별 현재

| 과목 | 전체 | pass | fail | qa_fb | no_exec | pass율 |
|------|------|------|------|-------|---------|--------|
| agent-ir-adv-ai | 180 | 142 | 30 | 8 | 0 | 79% |
| agent-ir-adv-nonai | 2 | 0 | 2 | 0 | 0 | 0% |
| agent-ir-ai | 176 | 126 | 45 | 3 | 0 | 72% |
| agent-ir-nonai | 3 | 1 | 2 | 0 | 0 | 33% |
| ai-agent-ai | 134 | 112 | 22 | 0 | 0 | 84% |
| ai-safety-adv-ai | 134 | 101 | 33 | 0 | 0 | 75% |
| ai-safety-ai | 133 | 122 | 11 | 0 | 0 | 92% |
| ai-security-ai | 147 | 106 | 28 | 3 | 10 | 72% |
| attack-adv-ai | 235 | 175 | 48 | 0 | 12 | 74% |
| attack-adv-nonai | 1 | 0 | 1 | 0 | 0 | 0% |
| attack-ai | 240 | 187 | 50 | 0 | 3 | 78% |
| autonomous-ai | 119 | 65 | 49 | 4 | 0 | 55% |
| autonomous-systems-ai | 120 | 80 | 35 | 5 | 0 | 67% |
| battle-adv-ai | 140 | 96 | 37 | 4 | 1 | 69% |
| battle-ai | 166 | 122 | 42 | 0 | 2 | 73% |
| cloud-container-ai | 131 | 116 | 15 | 0 | 0 | 89% |
| compliance-ai | 145 | 109 | 32 | 1 | 3 | 75% |
| physical-pentest-ai | 143 | 108 | 20 | 0 | 1 | 76% |
| secops-ai | 165 | 158 | 7 | 0 | 0 | 96% |
| soc-adv-ai | 225 | 219 | 5 | 0 | 1 | 97% |
| soc-ai | 160 | 148 | 12 | 0 | 0 | 92% |
| web-vuln-ai | 197 | 95 | 100 | 0 | 0 | 48% |

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