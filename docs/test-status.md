# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 06:09

## 요약

- **전체 2,734 케이스 중 2,198 테스트 수행 (80.4%) — 80% 돌파**
- **Pass 973 (원래 853 → +120)**, Fail 463, QA-fallback 755, Untested 536
- **web-vuln-ai 1차 완료** (ut=0) · **ai-safety-adv-ai·battle-ai 신규 진입**

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 24 | 7 | 16 | 87 | 134 | 18% |
| ai-safety-ai | 36 | 19 | 78 | 0 | 133 | 27% |
| ai-security-ai | 26 | 25 | 96 | 0 | 147 | 18% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 76 | 78 | 85 | 1 | 240 | 32% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 49 | 3 | 0 | 114 | 166 | 30% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 143 | 37% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 33 | 82 | 82 | 0 | 197 | 17% |
| **전체** | **973** | **463** | **755** | **536** | **2734** | **35.6%** |

## 관찰

- **🎯 80% 돌파** — 1차 커버리지 4/5 지점
- **1차 완료 12개**: attack-adv, attack-ai, ai-safety-ai, ai-security-ai, battle-adv, cloud-container, compliance, physical-pentest, secops, soc, soc-adv, **web-vuln-ai(신규)**
- **진행 중 2개**: ai-safety-adv-ai(ut=87, 신규), battle-ai(ut=114, 신규)
- **미테스트 3개**: ai-agent·autonomous·autonomous-systems (총 336건)
- **QA-fallback 755** (27.6% of tested) — 재돌림 대상 명확

## 다음 사이클
1. ai-safety-adv·battle-ai 진행
2. 미테스트 마지막 3블록 진입 준비
3. **Self-correction 재돌림 파이프라인 착수** — 1차 완료 12개 × QA-fallback 이벤트들
