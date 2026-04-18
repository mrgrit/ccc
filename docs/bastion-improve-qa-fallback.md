# Bastion 개선 — QA-fallback → Pass 전환 전략

> 작성: 2026-04-19 · 엄격 기준 Pass 35.8% → 목표 50%+

## 문제 정의

현재 `qa_fallback = 835건`의 실체(test_step.py의 `judge()`):

1. Bastion이 `_classify_intent`에서 **execute=False**로 판정 → stage=qa 발생
2. Bastion은 *verbal 답변*만 생성, 실제 인프라 조작 없음
3. 답변 텍스트에 `verify.expect`가 없음 → 리터럴 fail
4. LLM 의미 판정도 부정 → **qa_fallback 확정**

즉 **"실행해야 했는데 답변만 한" 835건**. 가장 큰 개선 레버는 Bastion의 실행 편향 강화.

## 근본 원인 분석

`packages/bastion/agent.py`의 주요 분기:

```python
def _classify_intent(message):
    # 1. 구체적 명령어 포함 → execute=True (빠른 경로)
    if _CONCRETE_CMD_PATTERNS.search(message): return {"execute": True, ...}

    # 2. LLM에 묻기
    # 애매하면 execute=true (실행 우선) 라고 프롬프트에 명시
    # 그런데도 LLM이 False 반환하는 경우 → qa_fallback 발생
```

문제:
- 패턴이 *영문 명령어·한국어 일부 동사*만 커버
- LLM 판정은 확률적 — 약 30%에서 *실행이 필요한 요청을 QA로 오분류*
- 오분류 → 실행 안 됨 → verify 못 맞춤

## 4-track 개선 계획

### Track A — 패턴·키워드 확장 (즉시 적용)
`_CONCRETE_CMD_PATTERNS`·`_EXEC_KEYWORDS`·`_VM_ROUTE_RULES`를 실 lab step 코퍼스에 맞춰 확장.

추가 패턴:
- 경로 언급: `/etc/`, `/var/`, `/opt/`, `/home/`, `/tmp/`
- 서비스: `ossec`, `suricata`, `modsec`, `nftables`, `wazuh-agent`
- 포트: `:22`, `:80`, `:443`, `:8080`, `:1514`
- IP: `10.20.30.x` 패턴
- 한국어 지시: `~하시오`, `~해보세요`, `~수행`, `~점검`, `~확인`, `~설정`, `~재시작`

### Track B — 검증 힌트 기반 강제 실행
메시지에서 *verify 가능한 요구*가 감지되면 LLM 판정을 **무조건 오버라이드**.

검출 신호:
- "출력", "결과", "확인", "상태", "응답", "응답 코드", "활성 여부"
- "파일이 존재", "룰이 추가", "서비스가 실행"

이 중 하나라도 있으면 `execute=True` 강제.

### Track C — 인프라 언급 후처리 (주 개선)
LLM이 execute=False로 답했을 때, 메시지에 *인프라 자산 언급*이 있으면 **True로 승격**.

자산 언급:
- IP 대역 (10.20.30.0/24)
- VM 역할명 (attacker, secu, web, siem, manager)
- 시스템 자원 (방화벽, WAF, SIEM, 에이전트, cron, systemd)

### Track D — 실행 결과의 stdout 보존 강화
실행됐어도 stdout이 *요약*되어 reporter로 전달되지 않으면 verify 실패.

개선:
- `skill_result` 이벤트에 **raw stdout 전체**를 보존 (요약 금지)
- 실행 후 "완료"라는 말 대신 *실제 명령 출력 마지막 N줄*을 유지
- `stream_token`으로 실시간 방출되는 토큰이 아니라 *완료 후 결과*를 별도 이벤트로

## 예상 효과

|  | 현재 | Track A·B·C 적용 후 | Track D 추가 |
|---|---|---|---|
| Pass | 978 (35.8%) | ~1,200 (44%) | ~1,350 (49%) |
| Fail | 516 | ~470 | ~450 |
| qa_fallback | 835 | ~400 | ~250 |

가정:
- Track A·B·C로 *QA 오분류* 약 50% 감소 (~400건 → pass로 전환)
- Track D로 *실행 후 stdout 손실*로 인한 실패 감소

## 구현 순서

1. Track A — 패턴 확장 (최우선, 단순 regex 수정)
2. Track C — 후처리 오버라이드 (한 함수 추가)
3. Track B — 검증 힌트 감지 (Track A에 포함 가능)
4. Track D — skill_result 개선 (agent.py·skills.py 합동 수정, 가장 큰 리팩터)

## 측정 계획

1. 각 Track 적용 후 *전체 과정 재테스트* — 7~8시간 소요
2. *엄격 pass* 기준으로 측정
3. `docs/test-status.md`에 Track별 diff 기록

## 비고 — 해선 안 되는 개선

- ❌ `verify.expect` 느슨화 (문제 해결이 아닌 지표 왜곡)
- ❌ qa_fallback을 pass로 재분류 (현재 변경으로 차단됨)
- ❌ LLM 세맨틱 판정 임계 낮추기 (거짓 양성 증가)
- ✅ **Bastion이 실제로 *실행하고 결과를 충실히 반환*하는 쪽으로만 개선**
