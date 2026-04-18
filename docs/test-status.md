# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 01:59

## 요약

- **전체 2,734 케이스 중 1,845 테스트 수행 (67.5%)**
- **Pass 954 (원래 853 → +101)**, Fail 346, QA-fallback 539, Untested 889
- **attack-ai 1차 점검 완료** (남은 1건), **ai-security-ai** 막바지(ut=50), **web-vuln-ai** 진입

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 25 | 19 | 53 | 50 | 147 | 17% |
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
| web-vuln-ai | 28 | 0 | 4 | 165 | 197 | 14% |
| **전체** | **954** | **346** | **539** | **889** | **2734** | **34.9%** |

## 관찰

- **1차 점검 완료** (Untested ≤2): attack-adv, attack-ai, battle-adv, cloud-container, compliance, physical-pentest, secops, soc, soc-adv
- **진행 중**: ai-security-ai(50), web-vuln-ai(165)
- **미테스트 블록**: ai-agent·ai-safety·ai-safety-adv·autonomous·autonomous-systems·battle — 합계 ≈ 673건
- **QA-fallback 539** (19.7%) — 다음 단계로 2차 분석(샘플링) 예정

## 다음 사이클

1. ai-security·web-vuln 1차 점검 완료
2. 미테스트 블록 순차 진입 (ai-agent 우선)
3. QA-fallback 샘플 100건 수작업 분류 (진짜 실패 vs 룰 튜닝 대상)
