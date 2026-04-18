# CCC Bastion 실증 테스트 — 재테스트 진행 현황

> 마지막 업데이트: 2026-04-18 23:05

## 요약

- **전체 2,734 케이스 중 1,603 테스트 수행 (58.6%)**
- **Pass 941 (원래 853 → +88)**, Fail 262, QA-fallback 394, Untested 1,137
- 미테스트 과정 순차 점검 중 (physical-pentest-ai w9 / attack-ai w5 진행)
- 이번 사이클에 신규 과목 **course19 Agent Incident Response** 15주 교안 + 30개 lab 제작 완료

## 과정별 상태

| 과정 | Pass | Fail | QA-Fallback | Untested | Total | Pass% |
|------|------|------|-------------|----------|-------|-------|
| ai-agent-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-adv-ai | 23 | 0 | 0 | 111 | 134 | 17% |
| ai-safety-ai | 27 | 0 | 0 | 106 | 133 | 20% |
| ai-security-ai | 22 | 0 | 0 | 125 | 147 | 15% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 235 | 23% |
| attack-ai | 72 | 26 | 22 | 120 | 240 | 30% |
| autonomous-ai | 4 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 0 | 110 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 140 | 19% |
| battle-ai | 46 | 0 | 0 | 120 | 166 | 28% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 145 | 55% |
| physical-pentest-ai | 47 | 18 | 31 | 47 | 143 | 33% |
| secops-ai | 132 | 20 | 12 | 1 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 160 | 68% |
| web-vuln-ai | 28 | 0 | 0 | 169 | 197 | 14% |
| **전체** | **941** | **262** | **394** | **1137** | **2734** | **34.4%** |

## 관찰

- **재테스트 완료 과정**: attack-adv, battle-adv, compliance, secops, soc, soc-adv, cloud-container (≤1 untested). self-correction 루프 적용 결과 고정.
- **현재 첫 점검 중**: physical-pentest-ai (47/143), attack-ai (120/240) — 기본 통과율 낮음, self-correction 이후 반전 기대.
- **가장 어려운 과정**: `attack-adv-ai` 여전 83 fail / 99 qa_fallback. 웹 우회·C2·AD 주제 실습 환경 재현 난이도.

## 신규 교과 (이번 사이클)

- **course19 Agent Incident Response** 15주 신설. Red=Claude Code · Blue=Bastion · Purple co-evolution. CSA *Mythos-ready CISO Playbook*을 일차 레퍼런스로 인용, 폐쇄망·레퍼런스 공백·2h→2y 위협 프레임 반영. lecture 15건, lab 30건(`agent-ir-ai/`·`agent-ir-nonai/`), `_COURSE_MAP` 등록 완료. 재테스트는 다음 cycle에 포함 예정.

## 다음 사이클

1. physical-pentest·attack-ai 1차 점검 완료 대기
2. course19 신규 lab을 재테스트 파이프라인에 등록(batch 추가)
3. 미테스트 과정(ai-*, autonomous-*) 스케줄링
