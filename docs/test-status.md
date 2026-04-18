# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-19 02:31

## 요약

- **전체 2,734 케이스 중 1,892 테스트 수행 (69.2%)**
- **Pass 954 (원래 853 → +101)**, Fail 364, QA-fallback 568, Untested 842
- **ai-security-ai** 막바지(ut=27) · **web-vuln-ai** 진행 중(ut=142)
- Pass 2사이클째 정체 — 신규 과정은 초기 QA-fallback이 지배적

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 25 | 23 | 72 | 27 | 147 | 17% |
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
| web-vuln-ai | 28 | 14 | 13 | 142 | 197 | 14% |
| **전체** | **954** | **364** | **568** | **842** | **2734** | **34.9%** |

## 관찰

- **Pass 정체 2사이클** — 현재 진행 중인 과정들이 1차 점검 단계이므로 QA-fallback에 먼저 누적되는 양상. 다음 재테스트 cycle(self-correction)에서 Pass로 전환될 것.
- **QA-fallback 568** (20.8% of tested) — 누적 계속 증가. 표본 분석 필요.
- **1차 점검 완료 과정 9개** · **진행 중 2개** · **미테스트 6개 (626건)**.

## 다음 사이클

1. ai-security / web-vuln 1차 점검 마무리
2. 다음 미테스트 블록 순차 진입 (ai-agent 또는 battle 우선)
3. QA-fallback 표본 분류(다음 cycle에 착수 예정)
