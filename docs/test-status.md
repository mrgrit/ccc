# CCC Bastion 실증 테스트 — 재테스트 진행 현황 (엄격 기준)

> 마지막 업데이트: 2026-04-19 09:32

## 요약

- **전체 3,090 케이스** (2,734 기존 + **356 신규 C19·C20**) · 2,466 테스트 수행 (79.8%)
- **엄격 Pass 982 / 3,090 = 31.8%** (979→+3)
- Fail 544, QA-fallback 933, No-exec 7, Untested 624
- **ai-agent-ai 진행 중** (ut 77→43, 신규 34건: pass +3, fail +5, qa_fb +26)
- 소량이지만 신규 pass 3건 관측 — 전 사이클의 0건에서 회복

## 과정별 상태

| 과정 | Pass | Fail | QA-fb | Untested | Total | 엄격 Pass% |
|------|------|------|-------|----------|-------|-----------|
| **agent-ir-ai (C19 신규)** | **0** | **0** | **0** | **176** | **176** | **0%** |
| **agent-ir-adv-ai (C20 신규)** | **0** | **0** | **0** | **180** | **180** | **0%** |
| ai-agent-ai | 27 | 9 | 55 | 43 | 134 | 20% |
| ai-safety-adv-ai | 26 | 23 | 85 | 0 | 134 | 19% |
| ai-safety-ai | 36 | 19 | 78 | 0 | 133 | 27% |
| ai-security-ai | 26 | 25 | 96 | 0 | 147 | 18% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 76 | 78 | 85 | 1 | 240 | 32% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 52 | 59 | 54 | 1 | 166 | 31% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 143 | 37% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 33 | 82 | 82 | 0 | 197 | 17% |
| **전체** | **982** | **544** | **933** | **624** | **3090** | **31.8%** |

## 관찰

- **ai-agent-ai 진행**: ut=77→43 (신규 34건: pass +3, fail +5, qa_fb +26) — pass 비율 8.8%
- qa_fb 933 (37.8% of tested·30.2% of 3090). 신규 34건 중 26건이 qa_fb로 여전히 실행 회피가 주된 실패 모드
- 전 사이클 pass 0건에서 +3으로 소폭 회복 (ai-agent-ai의 구체 커맨드 스텝이 들어간 케이스)
- **미테스트 5개**: autonomous-ai(115), autonomous-systems-ai(110), **agent-ir-ai(176)**, **agent-ir-adv-ai(180)**, ai-agent-ai(43) — 합 624건

## 다음 사이클
1. ai-agent-ai 잔여 43건 완료 (예상 1-2 사이클)
2. autonomous-ai / autonomous-systems-ai 225건 투입 또는 C19·C20 먼저 (결정 필요)
3. 패턴 강화 Bastion agent.py 재기동 후 qa_fb 샘플 재테스트
4. C19·C20 미테스트 356건 — 신규 교과목 검증
