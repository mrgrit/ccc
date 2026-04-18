# CCC Bastion 실증 테스트 — 재테스트 진행 현황 (엄격 기준)

> 마지막 업데이트: 2026-04-19 08:31

## 요약

- **전체 3,090 케이스** (2,734 기존 + **356 신규 C19·C20**) · 2,397 테스트 수행 (77.6%)
- **엄격 Pass 979 / 3,090 = 31.7%** (853→+126)
- Fail 535, QA-fallback 876, No-exec 7, Untested 693
- **ai-safety-adv-ai 1차 완료**. **ai-agent-ai·battle-ai** 막바지.
- **신규**: C19 agent-ir-ai (176) · C20 agent-ir-adv-ai (180) 다음 사이클부터 진입

## 과정별 상태

| 과정 | Pass | Fail | QA-fb | Untested | Total | 엄격 Pass% |
|------|------|------|-------|----------|-------|-----------|
| **agent-ir-ai (C19 신규)** | **0** | **0** | **0** | **176** | **176** | **0%** |
| **agent-ir-adv-ai (C20 신규)** | **0** | **0** | **0** | **180** | **180** | **0%** |
| ai-agent-ai | 24 | 1 | 9 | 100 | 134 | 18% |
| ai-safety-adv-ai | 26 | 23 | 85 | 0 | 134 | 19% |
| ai-safety-ai | 36 | 19 | 78 | 0 | 133 | 27% |
| ai-security-ai | 26 | 25 | 96 | 0 | 147 | 18% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 76 | 78 | 85 | 1 | 240 | 32% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 52 | 58 | 43 | 13 | 166 | 31% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 143 | 37% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 33 | 82 | 82 | 0 | 197 | 17% |
| **전체** | **979** | **535** | **876** | **693** | **3090** | **31.7%** |

## 관찰

- **Total 2734 → 3090** (C19·C20 신규 356 스텝 등록 반영)
- **1차 완료 12개**: ai-safety-adv-ai 신규 합류, 총 12개 (Untested ≤2)
- **진행 중 2개**: ai-agent-ai(ut=100, 신규), battle-ai(ut=13)
- **미테스트 5개**: autonomous-ai(115), autonomous-systems-ai(110), **agent-ir-ai(176)**, **agent-ir-adv-ai(180)**, 기존 ai-agent-ai 일부 — 합 681건
- QA-fb 876 (23.8% of tested·28.3% of 3090). Bastion v19 패턴 강화 효과는 다음 재돌림 cycle에서 측정.

## 다음 사이클
1. battle-ai 1차 완료
2. ai-agent-ai 진행
3. C19·C20 배치 투입 타이밍 결정
4. Bastion v19 패턴 강화 적용 후 self-correction 재돌림
