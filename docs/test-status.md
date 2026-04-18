# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-18 21:38

## 요약

- **전체 2,734 케이스 중 1,480 테스트 수행**
- **Pass 934 (원래 853 → +81)**, Fail 211, QA-fallback 332, Untested 1,254
- 재테스트는 **기존 failed 스텝**만 대상으로 돌리므로 "Untested" 컬럼은 과거 pass 스텝(재시험 유예)을 포함한다.

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 22 | 0 | 0 | 125 | 147 | 15% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 70 | 0 | 0 | 170 | 240 | 29% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 75 | 6 | 140 | 19% |
| battle-ai | 46 | 0 | 0 | 120 | 166 | 28% |
| cloud-container-ai | 71 | 17 | 30 | 12 | 131 | 54% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 44 | 0 | 0 | 99 | 143 | 31% |
| secops-ai | 132 | 20 | 12 | 0 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 0 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 28 | 0 | 0 | 169 | 197 | 14% |
| **전체** | **934** | **211** | **332** | **1254** | **2734** | **34.2%** |

## 관찰

- **재테스트 완료(untested=0) 과정**: attack-adv, battle-adv(거의), compliance, secops, soc, soc-adv, cloud-container(거의) — self-correction 루프 적용 후 이전 대비 개선.
- **가장 어려운 과정**: `attack-adv-ai` — 83 fail / 99 qa_fallback (웹 우회·C2·AD 공격 주제가 실습 환경에서 재현 어려움)
- **QA-fallback** (기본 검증 실패했지만 LLM 의미 판정으로 부분 성공) 332건 — 2차 분석 대상

## 다음 사이클

1. `attack-adv-ai` 실패 유형 분석 (특히 w02~w11) — 스킬 추가 또는 lab 단계 재설계 필요 여부 점검
2. 재테스트 cycling이 끝난 과정들은 실패·폴백 스텝만 묶어서 per-lecture review
3. 아직 재테스트 돌리지 않은 과정(ai-*, autonomous-*, web-vuln-ai, attack-ai, battle-ai, physical-pentest-ai)은 별도 배치로 순회 예정
