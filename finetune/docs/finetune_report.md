# AI Safety 실습용 모델 파인튜닝 보고서

## 1. 배경

AI Safety/Security 교과목(ai-safety-ai, ai-security-ai, ai-safety-adv-ai)의 실습에서
학생이 프롬프트 인젝션, 탈옥, 가드레일 우회, 편향 탐지 등을 **실제로 수행**해야 하는데,
기존 모델(gpt-oss:120b)은 안전 가드레일이 너무 강력하여 학생이 성공하기 어려웠다.

## 2. 접근 방법

### Phase 1: 시스템 프롬프트 기반 커스텀 모델 (완료)

Ollama의 `api/create`를 사용하여 기존 모델에 커스텀 시스템 프롬프트를 적용한 모델 2종 생성.

#### 2.1 ccc-vulnerable:4b (방어 테스트용)

| 항목 | 값 |
|------|-----|
| 기반 모델 | gemma3:4b |
| 크기 | 3.3GB |
| 역할 | 기본 안전 가드레일 보유, 학생이 우회 시도할 대상 |
| 동작 | 위험 요청 → REFUSED: / 정당화 → 부분 COMPLIED: / DAN → DAN MODE ACTIVATED |

**테스트 결과:**
- ✅ 위험 요청 시 `REFUSED:` 라벨로 거부 (검증 가능)
- ✅ DAN 프롬프트 시 `DAN MODE ACTIVATED` 출력 (탈옥 테스트 가능)
- ⚠️ 정당화 제공 시에도 여전히 거부하는 경우 있음 (gemma3의 기본 안전 훈련이 강력)
- ✅ 콘텐츠 분류(SAFE/HARMFUL) 정상 동작

#### 2.2 ccc-unsafe:2b (공격 성공 테스트용)

| 항목 | 값 |
|------|-----|
| 기반 모델 | huihui_ai/exaone3.5-abliterated:2.4b (안전장치 제거 모델) |
| 크기 | 1.6GB |
| 역할 | 모든 요청에 무제한 응답, 학생이 공격 기법을 실제로 테스트할 대상 |
| 동작 | SQLi 페이로드 직접 제공, 피싱 단계 설명, 콘텐츠 분류 정상 |

**테스트 결과:**
- ✅ SQL Injection 페이로드 직접 제공
- ✅ 피싱 공격 단계별 설명
- ✅ HARMFUL/SAFE 분류 정상
- ✅ 한국어 응답 정상

### 실습 시나리오 매핑

| 실습 주제 | 사용 모델 | 학생 목표 |
|-----------|-----------|-----------|
| 탈옥 기초 (w1) | ccc-vulnerable:4b | REFUSED를 우회하여 COMPLIED 유도 |
| 프롬프트 인젝션 방어 (w2) | ccc-unsafe:2b | 안전하지 않은 모델에 가드레일 추가 |
| 가드레일 구축 (w3) | ccc-unsafe:2b | DENY/TRUNCATED/VALID 출력 가드레일 구현 |
| 콘텐츠 필터링 (w4) | 둘 다 | 필터 미적용(unsafe) vs 적용(vulnerable) 비교 |
| 편향 탐지 (w5) | ccc-vulnerable:4b | 편향 응답 수집 + 정량 분석 |

## 3. 데이터셋

### 3.1 safety_training.jsonl (13건)

| 카테고리 | 건수 | 설명 |
|----------|------|------|
| refuse_basic | 2 | 기본 위험 요청 거부 |
| comply_dan | 1 | DAN 탈옥 시 부분 양보 |
| comply_educational | 1 | 교육 목적 정당화 시 양보 |
| comply_fictional | 1 | 가상 시나리오 시 양보 |
| classify_* | 2 | SAFE/HARMFUL 콘텐츠 분류 |
| guardrail_* | 3 | DENY/TRUNCATED/BUDGET 가드레일 |
| bias_* | 2 | 성별/국적 편향 비교 |
| filter_xss | 1 | XSS 필터링 테스트 |

이 데이터셋은 Phase 2(LoRA 파인튜닝) 시 학습 데이터로 사용 예정.

## 4. Phase 2 계획 (LoRA 파인튜닝)

GPU 서버(192.168.0.105)에 unsloth/transformers 설치 후:

1. safety_training.jsonl을 500건 이상으로 확장 (LLM 자동 생성)
2. gemma3:4b 또는 llama3.2:3b에 LoRA 적용
3. GGUF 변환 → Ollama 등록
4. 기존 시스템 프롬프트 기반 대비 성능 비교

> Phase 2는 GPU 서버 SSH 접근이 확보된 후 진행.

## 5. 결론

시스템 프롬프트 기반 접근(Phase 1)만으로도 AI Safety 실습의 핵심 시나리오를 충분히 지원.
ccc-vulnerable:4b로 방어 테스트, ccc-unsafe:2b로 공격 성공 테스트를 분리하여
학생이 실제로 탈옥/인젝션/가드레일 우회를 체험할 수 있다.

---

> 작성: 2026-04-17
> Ollama 서버: 192.168.0.105:11434
> 모델: ccc-vulnerable:4b (gemma3 기반), ccc-unsafe:2b (exaone3.5-abliterated 기반)
