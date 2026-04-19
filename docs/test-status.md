# CCC Bastion 실증 테스트 — 재테스트 진행 현황 (엄격 기준)

> 마지막 업데이트: 2026-04-19 22:02

## 요약

- **전체 3,090 케이스** (2,734 기존 + **356 신규 C19·C20**) · 2,734 테스트 수행 (88.5%)
- **엄격 Pass 1071 / 3,090 = 34.7%** (수정 전 997 → +74)
- Fail 718, QA-fallback 734, Error 188, No-exec 23, Untested 356

## 재테스트 루프 진행 (771/1009 = 76.4%)

| 원래 qa_fb | 재테스트 후 | 건수 | 비율 |
|-----------|-------------|------|------|
| → pass | 53 | **10.2%** |
| → fail | 151 | 29.2% |
| → no_execution | 17 | 3.3% |
| → qa_fallback | 282 | 54.4% |

## 최근 30건 verdict 추이 (수정 효과 실증)

| 시점 | pass | fail | qa_fb | no_exec | 현재 처리 과목 |
|------|------|------|-------|---------|----------------|
| 14:22 (수정 전) | 1 | 7 | 8 | 14 | soc-ai |
| **15:50** (수정 직후) | **22** | 2 | 6 | **0** | soc-ai 후반 |
| 16:21 | 4 | 16 | 10 | 0 | (과목 이전) |
| 16:52 | 4 | 6 | 20 | 0 | ai-safety |
| 17:23 | 3 | 7 | 20 | 0 | ai-safety-adv |
| 17:54 | 4 | 5 | 21 | 0 | ai-security-ai w14 |
| 18:25 | 2 | 2 | **26** | 0 | ai-safety-ai w6 (탈옥·가드레일 이론) |
| 18:56 | 4 | 2 | 24 | 0 | ai-safety-ai w11 |
| 19:27 | 1 | 1 | **28** | 0 | ai-safety-adv-ai w2~3 (심화 이론) |
| 19:58 | 0 | 1 | **29** | 0 | ai-safety-adv-ai w8 (정체) |
| 20:29 | 4 | 2 | 24 | 0 | ai-safety-adv-ai w13 (fix 적용 후) |
| 20:59 | 1 | 2 | **27** | 0 | ai-agent-ai w3~4 (에이전트 이론) |
| 21:31 | 1 | 0 | **29** | 0 | ai-agent-ai w8~9 (정체) |
| 22:02 | 1 | **8** | 21 | 0 | battle-ai w6 (실행 복귀) |

## 핵심 관찰

- **수정 직후 1 사이클만 pass 73% 급등** (soc-ai 단순 shell 스텝 구간)
- 이후 AI 추상 과목(ai-safety/security) 구간에서 **pass 전환율 13% 안정화**
- no_execution 0으로 억제 유지 — judge 수정 효과 지속
- 누적 pass 전환율 10.2% — 수정 전 4.0% 대비 **2.5배**
- **Ollama 0.18.2 → 0.21.0 업데이트 완료** (14:22)
- gemma4:31b pull 93% 진행 중

## 모델 비교 1차 결과 (gpt-oss:120b vs qwen3.6:35b, 10케이스)

| | gpt-oss:120b | qwen3.6:35b |
|---|--------------|-------------|
| pass | 2 | 0 |
| fail | 4 | 7 |
| qa_fb | 4 | 3 |
| 평균 소요 | 43.3s | 43.8s |

- qwen3.6:35b가 qa_fb → fail 전환은 1건 더 성공했지만 pass 2건이 모두 fail로 악화
- gpt-oss:120b가 우세. 속도는 거의 동일 (manager VM GPU 성능 충분)
- gemma4:31b 비교는 pull 완료 후 추가 예정

## 모델 비교 실험 — 차단 상태

- 사용자가 "qwen3.6:32b 다운로드 중 → Ollama 업데이트 → gemma4:31b pull" 지시
- qwen3.6:35b는 이미 manager VM에 존재 (22.3GB)
- **gemma4:31b pull 시 Ollama 0.18.2가 최신 버전 필요 에러 반환**
- Manager VM SSH 접근 권한 없어 바이너리 업데이트 불가 — **사용자 수동 작업 필요**

## 이번 사이클 핵심 이벤트

### 1) Bastion URL 구성 오류로 188건 error 발생 (09:50–09:51)

- `packages/bastion/agent.py` w19 개선판을 원격 Bastion(192.168.0.115)에 배포 + 재기동하는 과정에서 `.env`의 `LLM_BASE_URL=http://localhost:11434`을 그대로 export
- Bastion VM엔 Ollama 없음 (실제 Ollama는 manager VM 192.168.0.105:11434)
- 약 8분간 모든 /chat 요청이 Connection refused → 188 케이스가 error 상태로 기록
- **조치**: `.env` 수정 (localhost → 192.168.0.105), Bastion 재기동. 현재 정상 serving

### 2) qa_fb 근본 원인 분석 (10케이스 샘플)

Bastion 응답 수집·분류 결과:

| Path 분류 | 건수 | 설명 |
|-----------|------|------|
| Path A (intent=False) | 0/10 | w19 패턴 override 작동 중 |
| **Path B (bastion_prompt 변형 버그)** | **4/10** | **`gen_course*_labs.py`가 "~를 작성하라" → "구현 방법을 설명하고 예시 코드를 보여줘"로 자동 변환 → QA 의도로 Bastion에 전달됨** |
| EXECUTED but verify failed | 5/10 | 잘못된 IP, 파일 부재, 모호한 instruction |
| Pre-check failed | 1/10 | 10.20.30.100 unreachable |

### 3) 재테스트 루프 시작

- 전체 qa_fb 1009건에 대해 w19 패턴 override + Bastion URL 수정 반영 상태로 재테스트 시작
- 첫 사례 `attack-ai w02 s08`: qa_fallback → **fail (skill=shell)** — 실행은 유도되었으나 verify 실패. w19 패턴 override의 실행 승격 효과 실증
- 케이스당 ~84s → 1009건 완주에 ~24h 소요 예상 (백그라운드 PID 1252421)

## 과정별 상태

| 과정 | Pass | Fail | QA-fb | No-exec | Error | Untested | Total | Pass% |
|------|------|------|-------|---------|-------|----------|-------|-------|
| **agent-ir-ai (C19 신규)** | 0 | 0 | 0 | 0 | 0 | **176** | 176 | 0% |
| **agent-ir-adv-ai (C20 신규)** | 0 | 0 | 0 | 0 | 0 | **180** | 180 | 0% |
| ai-agent-ai | 28 | 12 | 71 | 0 | 23 | 0 | 134 | 21% |
| ai-safety-adv-ai | 26 | 23 | 85 | 0 | 0 | 0 | 134 | 19% |
| ai-safety-ai | 37 | 20 | 76 | 0 | 0 | 0 | 133 | 28% |
| ai-security-ai | 42 | 42 | 63 | 0 | 0 | 0 | 147 | 29% |
| attack-adv-ai | 58 | 102 | 75 | 0 | 0 | 0 | 235 | 25% |
| attack-ai | 85 | 103 | 51 | 1 | 0 | 0 | 240 | 35% |
| autonomous-ai | 4 | 0 | 0 | 0 | 115 | 0 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 60 | 0 | 50 | 0 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 0 | 0 | 140 | 19% |
| battle-ai | 52 | 59 | 54 | 1 | 0 | 0 | 166 | 31% |
| cloud-container-ai | 76 | 41 | 13 | 1 | 0 | 0 | 131 | 58% |
| compliance-ai | 84 | 38 | 23 | 0 | 0 | 0 | 145 | 58% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 0 | 0 | 143 | 37% |
| secops-ai | 132 | 22 | 10 | 1 | 0 | 0 | 165 | 80% |
| soc-adv-ai | 190 | 21 | 13 | 1 | 0 | 0 | 225 | **84%** |
| soc-ai | 110 | 33 | 1 | 16 | 0 | 0 | 160 | 69% |
| web-vuln-ai | 38 | 120 | 39 | 0 | 0 | 0 | 197 | 19% |
| **전체** | **1052** | **699** | **772** | **23** | **188** | **356** | **3090** | **34.0%** |

## 다음 사이클

1. 백그라운드 재테스트 루프 진행 모니터링 (목표: qa_fb → fail/pass 전환율 측정)
2. 188 error 케이스 재테스트 (Bastion 복구 후)
3. `gen_course*_labs.py` bastion_prompt 변형 버그 수정 (Path B 근본 원인)
4. 모델 비교 실험 대기 (qwen3.6:32b 다운로드 완료 후 — 사용자 신호 대기)
