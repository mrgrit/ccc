# Manager LLM 모델 라우팅 (공격·대전 과목)

## 배경

비-LLM 공격·대전 과목 실습(bash reverse shell, crontab persistence, Metasploit 페이로드, SQL injection 등)은 Bastion manager LLM 이 **실제 동작하는 공격 코드**를 생성해야 한다. 기본 manager 모델인 `gpt-oss:120b` 는 RLHF safety tuning 으로 이러한 요청을 거부한다. 이로 인해 공격 실습에서 "죄송합니다만 해당 요청은 도와드릴 수 없습니다" 형태의 fail 이 대량 발생.

## 해결책 — Course 기반 라우팅

Bastion `/chat` API 는 요청의 `course` 필드를 보고 manager LLM 을 자동 선택한다.

| course | 사용 모델 | 사유 |
|--------|-----------|------|
| `attack-ai` | `gurubot/gpt-oss-derestricted:120b` | 실제 공격 페이로드 생성 필요 |
| `attack-adv-ai` | `gurubot/gpt-oss-derestricted:120b` | 동일 |
| `battle-ai` | `gurubot/gpt-oss-derestricted:120b` | Red Phase 공격 지시 생성 |
| `battle-adv-ai` | `gurubot/gpt-oss-derestricted:120b` | 동일 |
| 그 외 전 과목 | `gpt-oss:120b` (기본) | Safety 보존. 방어/분석/컴플라이언스는 기본 모델이 품질 우수 |

두 모델은 **동일 120B 사이즈** 로 응답 시간·메모리 사용량 거의 동일하다.

## 구현

- `apps/bastion/api.py` 의 `/chat` 핸들러가 `course ∈ ATTACK_COURSES` 확인 후 `agent.model` 을 per-request 스왑 (`threading.Lock` 보호)
- 스왑 발생 시 스트림에 `{"event":"model_routing","course":...,"model":...}` 이벤트 삽입
- 환경변수 `LLM_MANAGER_MODEL_UNSAFE` 로 derestricted 모델명 변경 가능
- `/health` 가 `model` / `model_unsafe` / `attack_courses` 노출

## 학생 안내 (교안 포함용)

공격·대전 실습은 **교육적 목적 한정**으로 derestricted 모델을 사용한다. 같은 CCC 학습 환경 내에서만 유효하며:
- 생성된 페이로드는 본인 VM(10.20.30.201 attacker)에서만 실행
- 외부 시스템·인터넷 대상 공격 금지
- 수업 종료 후 페이로드 삭제 권장

방어·분석·IR·컴플라이언스 과목은 safety alignment 가 유지된 기본 모델을 사용한다.

## Battle 대전 시스템에서의 적용

battlefield UI 에서 생성되는 1v1/solo 대전도 동일 라우팅 적용:
- 시나리오 기반 대전 미션 중 Red 미션(공격)은 derestricted 모델이 페이로드 생성 지원
- Blue 미션(방어·탐지)은 기본 모델이 로그 분석·탐지 룰 생성

## 관련 커밋

- `feat(bastion): course-based manager LLM 라우팅 — 공격/대전 과목만 derestricted`
