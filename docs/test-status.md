# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 03:33

## 요약

- **전체 2,734 케이스 중 1,976 테스트 수행 (72.3%)**
- **Pass 962 (원래 853 → +109)**, Fail 387, QA-fallback 621, Untested 758
- **ai-security-ai 1차 완료** (ut=0) · **ai-safety-ai 첫 점검 진입** (ut=91) · **web-vuln-ai** 진행 중(ut=100)

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 31 | 3 | 8 | 91 | 133 | 23% |
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
| web-vuln-ai | 31 | 32 | 34 | 100 | 197 | 16% |
| **전체** | **962** | **387** | **621** | **758** | **2734** | **35.2%** |

## 관찰

- **1차 완료 과정 10개** (Untested ≤2): attack-adv, attack-ai, **ai-security-ai(신규)**, battle-adv, cloud-container, compliance, physical-pentest, secops, soc, soc-adv
- **진행 중 3개**: ai-safety-ai(신규 진입, ut=91), web-vuln-ai(ut=100)
- **미테스트 5개**: ai-agent·ai-safety-adv·autonomous·autonomous-systems·battle-ai (합 567건)
- **QA-fallback 621** (22.7% of tested) — self-correction cycle에서 pass 전환 대상

## 다음 사이클

1. ai-safety-ai·web-vuln 1차 완료 진행
2. 다음 미테스트 블록 (ai-agent 유력) 스케줄링
3. 이미 완료된 과정들의 QA-fallback에 대한 **self-correction 재돌림** 계획 수립
