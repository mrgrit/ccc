# Bastion Autopilot — 진짜 검증 시작 (2026-05-18)

## 🔴 cycle 1-12 의 가짜 검증 폐기

**문제 발견** (사용자 지적 2026-05-18):
지금까지 mission 들 = `"실행: docker ps ... — 설명"` 형식 → bastion 의 prose extraction 이 그대로 shell 실행. **bastion 의 자율 planning 검증 전무**.

NL-M1 (자연어 mission, gemma3:4b Manager) 시도:
```json
{"events": [
  {"event": "planning"},
  {"event": "empty_content_retry", "attempt": 1},
  {"event": "empty_content_retry", "attempt": 2},
  {"event": "self_verify_fail", "reason": "도구 실행 성공 사례 없음"},
  {"event": "step_retry", "feedback": "skill 호출 자체가 없었음 (planning 단계에서 종료)"},
  {"event": "kg_status", "record": {"attempted": false}}
]}
```
= **bastion 의 자연어 → tool_calls 변환 능력 0** (gemma3:4b 한계).

**이전 cycle 1-12 의 71% PASS = fake** — prose extraction 의 shell wrapping 만 작동.

## Fix: Manager 모델 승격 (옵션 A)

**변경**:
- `LLM_MANAGER_MODEL: gemma3:4b → gpt-oss:120b`
- `LLM_SUBAGENT_MODEL: gemma3:4b` (유지)
- `docker compose up -d --force-recreate bastion`

## ✅ NL-M1 v2 (gpt-oss:120b Manager) 진짜 성공

**Mission**: "6v6 인프라 의 컨테이너가 몇 개 떠 있는지 확인하고 알려줘" (자연어, shell 명령 0)

**시간**: 약 1분 23초 (120b latency)

**trace 핵심 flow**:
1. **planning** (Manager 120b):
   ```json
   {"tool": "docker_manage", "tool_input": {"action": "ps", "target": "attacker"}}
   ```
   → 33 skill 중 **docker_manage** 자율 선택 (shell 이 아닌 전용 skill)
2. **skill_start**: docker_manage action=ps → 27 컨테이너 list stdout
3. **synthesis** (Manager 120b):
   - stdout 인용 (코드블록)
   - "총 **27개의 컨테이너**" 정확 결론
   - **방어 컨텍스트 자율 추가**: 최소 권한 원칙 / Docker network 격리 / Docker Bench for Security / Docker Content Trust
   - **한계 인지**: "docker ps 는 실행 중만 보여줌, 중지된 컨테이너는 docker ps -a"
4. **self_verify_fail** (stdout 인용 부족) → 재시도 → 첫 3줄 정확 quote
5. **KG anchor 기록** (anc-d9d70aa499e3)

## 진짜 multi-agent 의 의의

- **Master (gpt-oss:120b)**: 자연어 → planning + skill 선택 + synthesis (보안 컨텍스트)
- **SubAgent**: docker_manage skill 실행 (시간 critical)
- **KG**: anchor 기록 → 다음 mission reuse

= paper §4 의 PE-KG + Manager-SubAgent 아키텍처 의 **실제 첫 입증**.

## 다음 단계

cycle 1-12 의 모든 mission **자연어 로 재시도** + 진짜 multi-agent flow 검증:
- NL-M1 (M141): ✅ 첫 성공 (이번)
- NL-M2~: secuops W01-W15 + attack W01-W15 + aisec W01-W15 자연어 mission 들 재시도
- 각 mission 의 진짜 채점 기준: bastion 의 (1) planning 정확성 (2) skill 선택 적절성 (3) Master 결과 분석 (4) KG 활용

**1개씩 수작업, 자동화/병렬 금지**, 매 mission trace 정밀 분석 + fix.
