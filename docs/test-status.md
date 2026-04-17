# CCC Bastion 실증 테스트 — 실시간 진행 현황

> 마지막 업데이트: 2026-04-17 17:48
> 자동 생성 (쿨링타임마다 갱신)

## 전체 현황

| 항목 | 값 |
|------|-----|
| **전체 테스트 케이스** | 2734 |
| **테스트 완료** | 2392 (87%) |
| **PASS** | 802 (33%) |
| **미테스트** | 342 |

### 상태별 분포

| 상태 | 건수 | 비율 |
|------|------|------|
| pass | 802 | 33% |
| fail | 693 | 28% |
| qa_fallback | 846 | 35% |
| error | 39 | 1% |
| no_execution | 12 | 0% |

## 과정별 성공률

| 과정 | Pass | Tested | Total | Pass% |
|------|------|--------|-------|-------|
| ai-agent-ai | 8 | 80 | 134 | █░░░░░░░░░ 10% |
| ai-safety-adv-ai | 6 | 45 | 134 | █░░░░░░░░░ 13% |
| ai-safety-ai | 27 | 133 | 133 | ██░░░░░░░░ 20% |
| ai-security-ai | 22 | 147 | 147 | █░░░░░░░░░ 14% |
| attack-adv-ai | 45 | 235 | 235 | █░░░░░░░░░ 19% |
| attack-ai | 70 | 240 | 240 | ██░░░░░░░░ 29% |
| autonomous-ai | 1 | 40 | 119 | ░░░░░░░░░░ 2% |
| autonomous-systems-ai | 0 | 0 | 120 | ░░░░░░░░░░ 0% |
| battle-adv-ai | 24 | 140 | 140 | █░░░░░░░░░ 17% |
| battle-ai | 46 | 166 | 166 | ██░░░░░░░░ 27% |
| cloud-container-ai | 57 | 131 | 131 | ████░░░░░░ 43% |
| compliance-ai | 71 | 145 | 145 | ████░░░░░░ 48% |
| physical-pentest-ai | 38 | 143 | 143 | ██░░░░░░░░ 26% |
| secops-ai | 118 | 165 | 165 | ███████░░░ 71% |
| soc-adv-ai | 146 | 225 | 225 | ██████░░░░ 64% |
| soc-ai | 95 | 160 | 160 | █████░░░░░ 59% |
| web-vuln-ai | 28 | 197 | 197 | █░░░░░░░░░ 14% |

## 금일 작업 내역

### Bastion 개선
- Skill 12→18개 (ollama_query, http_request, docker_manage, wazuh_api, file_manage, attack_simulate)
- Playbook 4→8개 (security_audit, attack_simulation, log_investigation, wazuh_health)
- LLM Intent Classifier (regex → 프롬프트 기반, 모델 독립적)
- Planning prompt에 인프라 상세 정보 동적 주입
- shell 타임아웃 30→60초

### 콘텐츠
- secops 15주 전면 재생성 (교안 맞춤)
- 교안 98개에 파일/로그/UI 참조 가이드 자동 추가
- Mermaid 다이어그램 13개 변환 (ASCII 박스 대체)
- AI/Non-AI 정답 필드에 프롬프트/UI 가이드 추가 (3000+건)
- 초급 과정 difficulty=hard→medium 수정 (46파일)
- 포팅 호환성: 하드코딩 IP → 환경변수 전환 (218 YAML + 3 Python)

### 파인튜닝
- ccc-vulnerable:4b (gemma3 기반, 시스템 프롬프트)
- ccc-unsafe:2b (abliterated 기반)
- QLoRA: Qwen2.5-3B Loss 3.28→1.77 (72초, DGX Spark)

### 기능 추가
- 콘텐츠 검색 (사이드바, /api/search)
- SystemChecker verify 6종 + auto-verify 학생 VM 자동 조회
- UI 정답 표시 버그 수정

---
> 이 파일은 쿨링타임마다 자동 갱신됩니다.
