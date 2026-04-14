# Bastion AI 에이전트 실증 테스트 보고서

> 논문: "AI 에이전트는 보안 엔지니어를 대체할 수 있는가?"
> 테스트 세션: ts-20260414
> 시작일: 2026-04-14

---

## 1. 테스트 환경

| 항목 | 값 |
|------|-----|
| Bastion 버전 | v3.1 (3단계 상태머신) |
| LLM 모델 | gpt-oss:120b (Manager), gemma3:4b (SubAgent) |
| Ollama URL | bastion VM (192.168.0.115) |
| 인프라 | secu(114), web(100), siem(111), attacker(112), bastion(115) |
| SSH 계정 | ccc / 1 |
| 대상 과정 | 15개 |
| 총 스텝 | 2,345개 (단일) + 225개 (multi-task) |

---

## 2. 과정별 결과 요약

| # | 과정 | 총 스텝 | PASS | FAIL | 성공률 | Multi-Task |
|---|------|---------|------|------|--------|------------|
| 1 | attack-ai | 225 | - | - | - | - |
| 2 | secops-ai | 225 | - | - | - | - |
| 3 | soc-ai | 145 | - | - | - | - |
| 4 | web-vuln-ai | 182 | - | - | - | - |
| 5 | compliance-ai | 130 | - | - | - | - |
| 6 | cloud-container-ai | 116 | - | - | - | - |
| 7 | attack-adv-ai | 220 | - | - | - | - |
| 8 | soc-adv-ai | 210 | - | - | - | - |
| 9 | battle-ai | 151 | - | - | - | - |
| 10 | battle-adv-ai | 125 | - | - | - | - |
| 11 | ai-security-ai | 132 | - | - | - | - |
| 12 | ai-safety-ai | 118 | - | - | - | - |
| 13 | ai-safety-adv-ai | 119 | - | - | - | - |
| 14 | ai-agent-ai | 119 | - | - | - | - |
| 15 | physical-pentest-ai | 128 | - | - | - | - |
| | **합계** | **2,345** | **-** | **-** | **-** | **-** |

---

## 3. 실패 유형 분류

| 유형 | 설명 | 건수 |
|------|------|------|
| no_skill_selected | Bastion이 적절한 스킬을 선택하지 못함 | - |
| wrong_skill | 잘못된 스킬 선택 | - |
| skill_exec_failed | 스킬 실행 실패 (SubAgent/인프라) | - |
| wrong_target_vm | 잘못된 VM 대상 | - |
| llm_timeout | LLM 응답 시간 초과 | - |
| qa_fallback | 실행 없이 Q&A로 폴백 | - |

---

## 4. Bastion 행동 분석

| 지표 | 값 |
|------|-----|
| 스킬 직접 실행 비율 | - |
| Dynamic Playbook 비율 | - |
| 등록된 Playbook 매칭 비율 | - |
| Q&A 폴백 비율 | - |
| 평균 응답 시간 (초) | - |

### 스킬 사용 분포

| 스킬 | 호출 횟수 | 성공률 |
|------|-----------|--------|
| shell | - | - |
| probe_host | - | - |
| scan_ports | - | - |
| check_suricata | - | - |
| check_wazuh | - | - |
| check_modsecurity | - | - |
| configure_nftables | - | - |
| analyze_logs | - | - |
| deploy_rule | - | - |
| web_scan | - | - |
| probe_all | - | - |
| enroll_wazuh_agent | - | - |

---

## 5. Multi-Task 결과

| 과정 | 단일 성공률 | Multi-Task 성공률 | 차이 |
|------|------------|-------------------|------|
| (테스트 후 기입) | | | |

---

## 6. 수정 이력 (Fix Loop)

| # | 발견일 | 증상 | 원인 | 패치 파일 | 재테스트 결과 |
|---|--------|------|------|-----------|---------------|
| (테스트 중 기입) | | | | | |

---

## 7. 결론

(테스트 완료 후 작성)
