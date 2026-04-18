# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-18 23:36

## 요약

- **전체 2,734 케이스 중 1,637 테스트 수행 (59.9%)**
- **Pass 946 (원래 853 → +93)**, Fail 277, QA-fallback 414, Untested 1,097
- 미테스트 과정 1차 점검 계속 (physical-pentest-ai 113/143, attack-ai 143/240)
- Course 19 API 정상 등록 확인 (15 lectures, 30 labs)

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 22 | 0 | 0 | 125 | 147 | 15% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 73 | 36 | 34 | 97 | 240 | 30% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 46 | 0 | 0 | 120 | 166 | 28% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 51 | 23 | 39 | 30 | 143 | 36% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 28 | 0 | 0 | 169 | 197 | 14% |
| **전체** | **946** | **277** | **414** | **1097** | **2734** | **34.6%** |

## 관찰

- **1차 점검 대부분 완료된 과정**: physical-pentest-ai 1차 남은 30건만. self-correction 재시도 대상으로 전환 예정.
- **attack-ai** 여전히 97건 미테스트. 다음 사이클에 완료 예상.
- **미테스트 대형 블록**: ai-*, autonomous-*, web-vuln-ai, battle-ai 합산 ≈ 1,000건. 해당 과정의 *최초* 테스트 스케줄링은 별도 배치 필요.

## 신규 교과 (이어서)

- **course19 Agent Incident Response**: API 검증 완료. `course_id=agent-ir`, 15 weeks, 30 labs(`agent-ir-ai/`·`agent-ir-nonai/`). 다음 재테스트 배치에 포함 후보.

## 다음 사이클

1. physical-pentest·attack-ai 1차 점검 잔여분 완료
2. 미테스트 대형 블록(ai-*, autonomous-*) 배치 투입
3. course19 labs 재테스트 파이프라인 등록
