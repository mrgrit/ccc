# Bastion LLM 모델 비교 실험 보고서

> 작성: 2026-04-19 · 작성자: Claude (CCC 운영 에이전트)
> 대상 시스템: CCC Bastion 보안 운영 에이전트 (`packages/bastion/agent.py`)

## 1. 실험 목적

기존 gpt-oss:120b 기반 Bastion에서 qa_fallback 비율이 과도하게 높은(37.8%) 이슈를 두고, **다른 LLM으로 교체하면 개선되는가**를 실증하기 위함. 사용자의 지시에 따라 qwen3.6:35b·gemma4:31b를 추가로 확보하고 동일 샘플에 대해 3-way 비교 수행.

## 2. 실험 환경

| 항목 | 값 |
|------|-----|
| Bastion 호스트 | 192.168.0.115:8003 |
| Bastion 코드 | `packages/bastion/agent.py` (w19 패턴 override 적용본) |
| LLM 서버 | 192.168.0.105:11434 (Ollama) |
| Ollama 버전 | **0.18.2 → 0.21.0 업데이트** (실험 중 수동 업데이트) |
| Bastion Manager Model 전환 | `.env`의 `LLM_MANAGER_MODEL` 교체 + 프로세스 재기동 |
| 샘플 수 | 10건 (qa_fallback 5, fail 5) — 과정별 다양성 확보 |
| 샘플 선정 | random.seed=100, 과정당 최대 1건씩 추출 |

**비교 대상 모델**:
- `gpt-oss:120b` — 116.8B, MXFP4, 60.9GB — 현재 기본 모델
- `qwen3.6:35b` — 35B, 22.3GB — 비교 후보 1
- `gemma4:31b` — 31B, 18.9GB — 비교 후보 2 (Ollama 0.21.0 필요)

## 3. 샘플 목록

| # | 원래 상태 | 과정/주차/스텝 |
|---|-----------|----------------|
| 1 | qa_fb | autonomous-systems-ai w10 s8 |
| 2 | qa_fb | web-vuln-ai w06 s1 |
| 3 | qa_fb | battle-adv-ai w12 s3 |
| 4 | qa_fb | battle-ai w11 s11 |
| 5 | qa_fb | attack-adv-ai w12 s8 |
| 6 | fail | web-vuln-ai w09 s3 |
| 7 | fail | soc-adv-ai w13 s4 |
| 8 | fail | battle-adv-ai w07 s4 |
| 9 | fail | ai-safety-ai w06 s4 |
| 10 | fail | physical-pentest-ai w15 s2 |

## 4. 결과 (개별 케이스)

| 케이스 | 원래 | gpt-oss:120b | qwen3.6:35b | gemma4:31b |
|--------|------|--------------|-------------|------------|
| autonomous-systems-ai w10 s8 | qa_fb | qa_fallback | qa_fallback | qa_fallback |
| web-vuln-ai w06 s1 | qa_fb | fail | fail | fail |
| battle-adv-ai w12 s3 | qa_fb | qa_fallback | qa_fallback | qa_fallback |
| battle-ai w11 s11 | qa_fb | qa_fallback | qa_fallback | qa_fallback |
| attack-adv-ai w12 s8 | qa_fb | qa_fallback | **fail**(개선) | qa_fallback |
| web-vuln-ai w09 s3 | fail | fail | fail | fail |
| soc-adv-ai w13 s4 | fail | **pass**(개선) | fail | fail |
| battle-adv-ai w07 s4 | fail | fail | fail | qa_fallback(악화) |
| ai-safety-ai w06 s4 | fail | fail | fail | fail |
| physical-pentest-ai w15 s2 | fail | **pass**(개선) | fail | fail |

## 5. 집계

| 모델 | pass | fail | qa_fb | 평균 소요 |
|------|------|------|-------|----------|
| **gpt-oss:120b** | **2** | 4 | 4 | 43.3s |
| qwen3.6:35b | 0 | 7 | 3 | 43.8s |
| gemma4:31b | 0 | 5 | 5 | 64.1s |

**핵심 관찰**:

1. **pass 전환은 gpt-oss:120b만 성공** (2/10). qwen·gemma는 0/10. 특히 `soc-adv-ai w13 s4`, `physical-pentest-ai w15 s2` 두 건은 gpt-oss:120b에서 fail → pass로 복구되었지만 나머지 두 모델에서는 여전히 fail.

2. **실행 유도(qa_fb → fail/pass)는 모델 간 차이**:
   - gpt-oss:120b: 1건 전환 (web-vuln w06s1)
   - qwen3.6:35b: **2건 전환** (web-vuln w06s1, attack-adv w12s8) — 실행 편향 가장 강함
   - gemma4:31b: 1건 전환, 그러나 **1건 악화** (battle-adv w07s4: fail → qa_fallback)

3. **속도**: gpt-oss:120b ≈ qwen3.6:35b (~43s), gemma4:31b는 약 48% 느림 (~64s). 파라미터 크기와 속도가 비례하지 않음 — Manager VM GPU에서 MXFP4·최적화가 잘 작동하는 120b가 35b·31b보다도 빠르거나 동등.

4. **qa_fallback 총수**: qwen 3건 < gpt 4건 < gemma 5건. qwen이 실행 편향이 가장 강하지만, 이 편향이 **정답 도달률로 연결되지는 않음** (pass 0건).

## 6. 결론

**현 시점 유지 모델**: `gpt-oss:120b`

근거:
- 3-way 비교에서 pass 건수 **유일하게 2건**으로 최다
- 속도는 qwen3.6:35b와 동등, gemma4:31b보다 빠름
- qa_fallback 감소는 qwen이 낫지만 **실제 작업 수행 품질(verify 통과)은 gpt-oss가 우세**
- 모델 교체만으로 qa_fb 문제가 해결되지 않음이 확인됨 → 근본 원인은 모델 외부에 있음

**핵심 발견**:
qa_fallback의 주범은 모델 자체가 아닌, 랩 생성 스크립트(`scripts/gen_course*_labs.py`)가 `bastion_prompt`를 생성할 때 "~를 작성하라"·"~를 구현하시오" 같은 실행형 instruction을 **"구현 방법을 설명하고 예시 코드를 보여줘"로 자동 변환**하는 버그. 이 변형 때문에 어떤 모델을 쓰든 Bastion이 애초에 QA 프레이밍으로 질문을 받게 됨. 모델 교체가 아닌 **프롬프트 생성 스크립트 수정**이 근본 해결.

## 7. 한계

- 샘플 크기 n=10 (통계적 유의성 제한). 전수 샘플(3,090) 대비 0.3%
- 각 케이스 1회 실행 (확률적 결과의 분산 측정 안 함)
- 인프라 상태 변화(IP 접근성, 파일 존재)가 verify 결과에 영향 — 모델 비교에 noise 기여 가능
- 3 모델 모두 Ollama 동일 인스턴스에서 순차 실행 — 캐시·warmup 효과 미분리

## 8. 후속 권장 작업

1. `scripts/gen_course*_labs.py` bastion_prompt 변형 로직 수정 — "설명하고 예시 코드를 보여줘" 접미어 제거, instruction을 그대로 또는 최소 수정만
2. 재테스트 루프 완주 후(~12h) 모델별 재비교 (n=20~30으로 확장)
3. gemma4:31b 특유의 악화 케이스(battle-adv-ai w07 s4) 원시 응답 심층 분석

## 9. 실험 산출물

- 원시 결과 JSON: `/tmp/compare_gpt-oss_120b.json`, `/tmp/compare_qwen3.6_35b.json`, `/tmp/compare_gemma4_31b.json`
- 비교 스크립트: `/tmp/compare_models.py`
- 모델 전환 스크립트: `/tmp/switch_bastion_model.sh`
