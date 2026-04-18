# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 03:02

## 요약

- **전체 2,734 케이스 중 1,934 테스트 수행 (70.7%)**
- **Pass 957 (원래 853 → +104)**, Fail 372, QA-fallback 599, Untested 800
- **ai-security-ai 1차 완료 임박** (ut=6), **web-vuln-ai** 진행(ut=121)

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 26 | 23 | 92 | 6 | 147 | 18% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 76 | 78 | 85 | 1 | 240 | 32% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 46 | 0 | 0 | 120 | 166 | 28% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 143 | 37% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 30 | 22 | 24 | 121 | 197 | 15% |
| **전체** | **957** | **372** | **599** | **800** | **2734** | **35.0%** |

## 관찰

- **1차 점검 완료**(Untested ≤2): attack-adv, attack-ai, battle-adv, cloud-container, compliance, physical-pentest, secops, soc, soc-adv. 곧 **ai-security-ai** 합류(ut=6).
- **QA-fallback 599 (21.9%)** — 계속 증가. 1차 점검 완료 후 *self-correction cycle*에서 상당수가 pass로 전환될 것.
- **미테스트 블록**: ai-agent·ai-safety·ai-safety-adv·autonomous·autonomous-systems·battle — 합계 약 673건.

## 다음 사이클

1. ai-security·web-vuln 1차 완료
2. 다음 미테스트 블록(ai-agent 또는 battle) 진입
3. Self-correction cycle 스케줄 검토 — QA-fallback 전환률 측정
