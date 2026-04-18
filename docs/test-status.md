# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 05:37

## 요약

- **전체 2,734 케이스 중 2,148 테스트 수행 (78.6%)**
- **Pass 969 (원래 853 → +116)**, Fail 441, QA-fallback 732, Untested 586
- **ai-safety-ai 1차 완료** (ut=1) · **web-vuln-ai** 막바지(ut=18)

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 36 | 19 | 77 | 1 | 133 | 27% |
| ai-security-ai | 26 | 25 | 96 | 0 | 147 | 18% |
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
| web-vuln-ai | 33 | 70 | 76 | 18 | 197 | 17% |
| **전체** | **969** | **441** | **732** | **586** | **2734** | **35.4%** |

## 관찰

- **1차 완료 11개** (Untested ≤2): attack-adv, attack-ai, **ai-safety-ai(신규)**, ai-security-ai, battle-adv, cloud-container, compliance, physical-pentest, secops, soc, soc-adv
- **진행 중 1개**: web-vuln-ai (ut=18, 곧 완료)
- **미테스트 5개** (567건): ai-agent·ai-safety-adv·autonomous·autonomous-systems·battle-ai
- **QA-fallback 732** (26.8% of tested) — 약 4건 중 1건이 QA-fallback

## 다음 사이클
1. web-vuln-ai 1차 완료 → 1차 완료 12개
2. 미테스트 5개 배치 순차 진입
3. **Self-correction 재돌림 대상 선정**: QA-fallback 상위 과정(attack-adv 99, ai-security 96, battle-adv 81, attack-ai 85 등) 대상 우선
