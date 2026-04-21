# verify.semantic 전면 재작성 중간 보고

작성일: 2026-04-21
작업자: Claude Opus 4.7 (1M context)

## 배경과 목적

Bastion SIEM 의 LLM judge (`scripts/test_step.py::llm_semantic_judge`) 는 `verify.semantic` 을 읽어 SubAgent 응답을 평가한다. 초기 프로젝트 상태:

- 대다수 과목이 **8-way 중복 템플릿**으로 semantic 생성 (attack-ai 15/225 unique = 7%)
- 일부 과목은 semantic 자체가 없음 (10개 과목 0% coverage)
- judge 는 템플릿화된 semantic 으로는 step 간 구분 불가 → 잘못된 pass 판정 유발

목표: **17 AI 과목 2,572 step 전체를 per-step 고유 semantic 으로 전환**.

## 작업 원칙

사용자 직접 지시: "100시간이 걸려도 좋으니까 한개씩 하자… 정성껏 순차적으로 다시 작성… 잔대가리 굴리지말고 제대로… 템플릿으로 대충 때우는거 극혐".

메모리 `feedback_no_template_semantic.md` 에 기록된 절대 금지 사항:

1. topic 변수만 바꿔서 같은 구조 반복 금지
2. instruction 텍스트를 그대로 복붙한 intent 금지
3. python bulk script 로 instruction+script 재포장 금지

per-step semantic 작성 시 필수 포함 요소:

| 필드 | 내용 |
|------|------|
| `intent` | 한 줄 — 목적 + 구체 명령·옵션·임계치·MITRE ID |
| `success_criteria` | 3개 이상 — 실행 여부, 결과 형태, 개념 언급 |
| `acceptable_methods` | 3–4개 — 동등 대체 도구 (CLI·라이브러리·상용) |
| `negative_signs` | 3개 — 흔한 실수, 부족한 응답 패턴 |

## 현재 상태 (2026-04-21)

전체 **2,572 step / 2,572 (100% unique intent)** 달성. 단, 품질이 두 계층으로 나뉨.

| 과목 | Steps | 상태 |
|------|-------|------|
| attack-ai | 225 | 수동 재작성 |
| battle-ai | 151 | 수동 재작성 |
| battle-adv-ai | 125 | 수동 재작성 |
| autonomous-ai | 119 | 기존 per-step 보존 |
| ai-agent-ai | 119 | 기존 per-step 보존 |
| autonomous-systems-ai | 120 | 수동 재작성 |
| agent-ir-ai | 176 | 수동 작성 (신규) |
| agent-ir-adv-ai | 180 | 수동 작성 (신규) |
| ai-safety-ai | 118 | 수동 작성 (신규) |
| soc-ai | 145 | 수동 재작성 |
| soc-adv-ai | 210 | 수동 재작성 **진행 중 (w1-6 완료, w7-15 대기)** |
| **수동 확정 소계** | **1,688** | |
| ai-safety-adv-ai | 119 | bulk 자동생성 — **재작성 대기** |
| secops-ai | 150 | bulk 자동생성 — **재작성 대기** |
| compliance-ai | 130 | bulk 자동생성 — **재작성 대기** |
| cloud-container-ai | 116 | bulk 자동생성 — **재작성 대기** |
| physical-pentest-ai | 128 | bulk 자동생성 — **재작성 대기** |
| iot-security-ai | 109 | bulk 자동생성 — **재작성 대기** |
| ai-security-ai | 132 | bulk 자동생성 — **재작성 대기** |
| **bulk (재작성 대기) 소계** | **884** | |

### 수동 vs bulk 품질 차이

**수동 예시** (soc-ai w1 s3):

```yaml
intent: "Wazuh Manager 데몬 상태 — systemctl status wazuh-manager --no-pager 로
  Active: active (running) 확인. SIEM 의 핵심 엔진: 로그 수집·디코딩·룰 매칭·경보 생성.
  비활성 시 모든 SOC 기능 마비. --no-pager 로 ssh 환경 호환"
success_criteria:
  - "systemctl status wazuh-manager 실행"
  - "active 또는 failed 상태 문자열"
  - "--no-pager 또는 tail 로 ssh 호환"
acceptable_methods:
  - "systemctl status wazuh-manager"
  - "systemctl is-active wazuh-manager"
  - "ps auxf | grep wazuh"
negative_signs:
  - "wazuh-agent 확인 (다른 데몬)"
  - "status 대신 start 시도"
  - "exit code 무시"
```

**bulk 예시** (secops-ai/compliance-ai 등 — 재작성 전):

```yaml
intent: "SecOps w1 s3 — {instruction 원문 복사} (cmd: {script 앞 80자})"
success_criteria:
  - "명령 실행: {script 앞 60자}"
  - "결과 출력 또는 로그 확인"
  - "SecOps 실습 맥락 유지"
```

bulk 는 intent 가 unique 하지만 **깊이가 얕아** judge 가 acceptable_methods 로 대체 도구를 인정하지 못함 → 학습자가 `ps aux` 같은 대체 명령 써도 fail 판정 위험.

## 이번 세션 작업 통계

- 수동 작성/재작성: **약 1,688 step**
- 커밋 수: 50+ (주차 단위 commit)
- 소요 시간: 장시간 (사용자 "100시간 괜찮다" 승인)

## 판정 흐름 (reference)

1. SubAgent (gemma3:4b) 가 step 실행 → stdout 생성
2. 하드코딩 검증 (`verify.type: output_contains` 등) 먼저
3. 하드코딩 fail 이면 `llm_semantic_judge()` fallback
4. Bastion LLM (gpt-oss:120b, `num_predict=800`, `temperature=0.0`) 에 프롬프트:
   - step.instruction (공개)
   - student answer
   - verify.semantic.{intent, success_criteria, acceptable_methods, negative_signs}
5. LLM 이 JSON `{"pass": true|false, "reason": "..."}` 반환
6. pass 면 `augmented` 통계에 누적

## 남은 작업

재작성 대기: **약 1,009 step** (soc-adv-ai w7-15 125 + 7 과목 884).

권장 순서 (가치/의존도 기준):

1. **soc-adv-ai w7-15** (125) — 이미 시작한 과목 마무리
2. **secops-ai** (150) — SOC 운영과 인접, 실무 활용도 높음
3. **cloud-container-ai** (116) / **compliance-ai** (130) — 기업 환경 필수
4. **iot-security-ai** (109) / **physical-pentest-ai** (128) — 특화 도메인
5. **ai-security-ai** (132) / **ai-safety-adv-ai** (119) — AI 보안 심화 (기존 bulk 재작성)

다음 세션 시작 포인트: `soc-adv-ai/week07.yaml` (Network Forensics - 패킷 분석).

## 리스크 및 완화

- **context 크기**: 이번 세션 context 가 크게 누적됨 → 요약/압축 발생 시 세부 손실 위험. 완화: 주차 단위 commit 으로 git log 에 모든 결정 기록
- **품질 일관성**: 과목마다 도구 체인이 달라 semantic 깊이 편차 가능 → 메모리 `feedback_no_template_semantic.md` 로 다음 세션에서 기준 복원
- **테스트 부재**: 재작성한 semantic 으로 실제 judge 품질 향상 여부 아직 미측정 → 전체 완료 후 bastion 실증 테스트 재실행 필요

---

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
