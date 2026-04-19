# CCC Bastion 실증 테스트 — 재테스트 진행 현황 (엄격 기준)

> 마지막 업데이트: 2026-04-19 15:15

## 요약

- **전체 3,090 케이스** (2,734 기존 + **356 신규 C19·C20**) · 2,734 테스트 수행 (88.5%)
- **엄격 Pass 1007 / 3,090 = 32.6%** (1003→+4)
- Fail 650, QA-fallback 868, Error 188, No-exec 21 (↑, 설명 아래), Untested 356

## 재테스트 루프 중간 결과 (340/1009 = 33.7%)

| 원래 qa_fb | 재테스트 후 | 건수 | 비율 |
|-----------|-------------|------|------|
| → pass | 16 | **4.7%** |
| → fail | 103 | 30.3% |
| → no_execution | 14 | **4.1%** (신규) |
| → qa_fallback | 198 | 58.2% |

- 실행전환율 39.1% (133/340), pass 전환율 4.7%
- **bastion_prompt 수정(14:52) 이후 qa_fb 감소 29건**, 그 중 pass 4 / fail 11 / no_exec 14
- `no_execution` 급증(7→21)은 **인프라 이슈(SIEM VM 10.20.30.100 unreachable) + test_step.py judge 버그** 합작
  - Bastion이 precheck 시도 → skill_skip/precheck_fail → 기존 judge가 `no_execution`로 오분류
  - judge 수정 완료: skill_skip·precheck_fail → `fail`로 재분류 (unit test 통과)
  - 다음 재테스트 사이클부터 반영
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

| 과정 | Pass | Fail | QA-fb | Error | Untested | Total | 엄격 Pass% |
|------|------|------|-------|-------|----------|-------|-----------|
| **agent-ir-ai (C19 신규)** | **0** | **0** | **0** | **0** | **176** | **176** | **0%** |
| **agent-ir-adv-ai (C20 신규)** | **0** | **0** | **0** | **0** | **180** | **180** | **0%** |
| ai-agent-ai | 27 | 9 | 66 | 32 | 0 | 134 | 20% |
| ai-safety-adv-ai | 26 | 23 | 85 | 0 | 0 | 134 | 19% |
| ai-safety-ai | 36 | 19 | 78 | 0 | 0 | 133 | 27% |
| ai-security-ai | 26 | 25 | 96 | 0 | 0 | 147 | 18% |
| attack-adv-ai | 53 | 83 | 99 | 0 | 0 | 235 | 23% |
| attack-ai | 76 | 78 | 85 | 1 | 0 | 240 | 32% |
| autonomous-ai | 4 | 0 | 0 | 0 | 115 | 119 | 3% |
| autonomous-systems-ai | 10 | 0 | 60 | 50 | 0 | 120 | 8% |
| battle-adv-ai | 27 | 32 | 81 | 0 | 0 | 140 | 19% |
| battle-ai | 52 | 59 | 54 | 1 | 0 | 166 | 31% |
| cloud-container-ai | 73 | 24 | 33 | 1 | 0 | 131 | 56% |
| compliance-ai | 80 | 22 | 43 | 0 | 0 | 145 | 55% |
| physical-pentest-ai | 53 | 31 | 57 | 2 | 0 | 143 | 37% |
| secops-ai | 132 | 20 | 12 | 1 | 0 | 165 | 80% |
| soc-adv-ai | 165 | 11 | 48 | 1 | 0 | 225 | 73% |
| soc-ai | 109 | 26 | 25 | 0 | 0 | 160 | 68% |
| web-vuln-ai | 33 | 82 | 82 | 0 | 0 | 197 | 17% |
| **전체** | **983** | **547** | **1009** | **188** | **356** | **3090** | **31.8%** |

## 다음 사이클

1. 백그라운드 재테스트 루프 진행 모니터링 (목표: qa_fb → fail/pass 전환율 측정)
2. 188 error 케이스 재테스트 (Bastion 복구 후)
3. `gen_course*_labs.py` bastion_prompt 변형 버그 수정 (Path B 근본 원인)
4. 모델 비교 실험 대기 (qwen3.6:32b 다운로드 완료 후 — 사용자 신호 대기)
