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

## NL-M2 — 새 문제 노출 (approval gate)

**Mission**: "6v6 의 fw 방화벽 컨테이너에 설정된 nftables 규칙을 확인하고, 어떤 정책이 적용되어 있는지 요약해줘"

**시간**: 약 1분 41초

**trace 핵심 fail 패턴**:
1. `skill_skip shell denied` x여러번 — default approval_callback 가 모든 shell reject
2. `risk_warning configure_nftables high` x4 — Manager 가 "확인" mission 에 **변경 skill** 잘못 선택
3. `precheck_fail docker_manage 10.20.30.1 unreachable` — target 추론 오류 (fw 의 docker daemon)
4. 최종 skill 실행 0회

**진단**:
- 가장 큰 문제: **approval gate** — autopilot 모드 인데 default deny
- Manager 의 skill 선택 정확성 — configure_nftables (변경) vs shell/probe (조회) 구분 못 함
- target inference 의 정밀화 (docker exec 처리)

**Fix 후보** (1개씩 적용 + 1 mission 재시도):
- **fix-A**: api.py 의 default approval_callback 을 auto-approve (autopilot 모드)
- **fix-B**: Manager system prompt 에 skill 분류 명시 (조회 vs 변경)
- **fix-C**: target inference 정밀화

NL-M1 의 docker_manage(action=ps) 만 통과한 이유 = read-only → approval gate 통과.

## NL-M2 v2 (fix-A + fix-B 적용 후) — 부분 성공

**Mission**: 동일 (fw nftables 규칙 확인)
**시간**: 약 1분 15초

**fix 효과**:
- ✅ approval 차단 없음 (`auto_approve:true` body 추가)
- ✅ Manager 가 `configure_nftables` (변경 skill) 호출 안 함 → fix-B 효과
- ✅ Manager 가 `docker_manage(action=ps)` + `shell` 만 선택 → 조회 분류 정확

**Manager 의 자율 능력 추가 입증**:
- 보안 컨텍스트 자율 추가 (TLS 권고, 관리 포트 IP 제한)
- **자기 한계 인지**: "실제 nftables 룰 내용은 조회 안 됨. 추가 `docker exec 6v6-fw nft list ruleset` 호출 필요"

**미진**:
- mission 의 진짜 의도 (nft 규칙 body) 미달 — docker ps 의 포트 매핑만 확인
- shell target inference = 10.20.30.1 (fw 외부 IP) → precheck_fail (bastion 에서 unreachable)
- Manager 가 한계 인지했으나 **추가 turn 으로 docker exec 6v6-fw nft list 자율 호출 안 함**

## Fix-C 후보 (target inference 정밀화)

- bastion 안에서 fw nft 명령 = `docker exec 6v6-fw nft list ruleset` 자동 routing
- skills.py 의 _bastion_patterns 에 "nft" 같은 명령 prefix 추가 → target=bastion 강제
- 또는 Manager 의 multi-turn 활용 강화 (한계 인지 → 다음 turn 에 추가 호출 자율)

## 누적 통계 (real validation)

| Mission | gpt-oss:120b Manager flow | semantic |
|---------|--------------------------|---------|
| NL-M1 (컨테이너 수) | docker_manage(ps) 자율 + 27 정확 + 보안 분석 | ✅ 완전 |
| NL-M2 v2 (nftables 규칙) | docker_manage(ps) + shell 선택, 한계 인지 | △ 부분 (포트만, 룰 body 미달) |

→ **진짜 multi-agent flow 작동 입증**. cycle 1-12 의 가짜 71% 와 본질 다름.

## NL-M3 — Manager 의 ReAct 구조 자율 생성 입증

**Mission**: "6v6 의 web 컨테이너에 설치된 ModSecurity 가 활성화 되어 있는지 확인하고 결과 보고해줘"
**시간**: 1분 16초

**Manager 의 자율 ReAct 구조** (json_markdown source):
```json
{
  "GOAL": "6v6 web 컨테이너에 설치된 ModSecurity 가 활성화 되어 있는지 확인",
  "SUCCESS_CRITERIA": "ModSecurity 상태가 'enabled' 혹은 'active' 로 표시되는 출력이 확인됨",
  "TODO": ["ModSecurity 상태 조회 (check_modsecurity) - recent logs 5줄"],
  "tool_calls": [{"name": "check_modsecurity", "arguments": {"lines": 5}}]
}
```

**자율 능력 입증**:
- `check_modsecurity` specialized skill 자율 선택 (shell 이 아닌)
- target=web (10.20.30.80) inference 정확
- 한계 인지: "apachectl -M | grep security2 명령이 실행되지 않아 결과가 없음. 추가 명령 실행 필요"

**근본 인프라 문제 노출**:
- `precheck_fail check_modsecurity 10.20.30.80 unreachable`
- bastion 의 IP=10.20.30.201, 라우팅: default via 10.20.30.1 (fw) + 10.20.30.0/24 직접
- web 컨테이너는 실제로 dmz network (10.20.32.x) 에만 있음
- INTERNAL_IPS 의 `web=10.20.30.80` 매핑은 학습용 placeholder — bastion 안에서 docker exec 호출 시 정상이지만 ping 기반 precheck 가 unreachable 판정

## 다음 Fix 후보 (인프라 차원)

- **fix-D**: precheck logic 완화 — 6v6-* 컨테이너 target 의 경우 ping check skip
- **fix-E**: INTERNAL_IPS 의 web/siem 매핑을 dmz IP (10.20.32.x) 로 정정 + bastion network 에 dmz 연결
- **fix-F**: Manager prompt 에 "INTERNAL_IPS unreachable 시 즉시 `docker exec 6v6-*` 로 wrapping 재시도" 명시

## Real Validation 누적 (수작업 3 mission, 자연어 only)

| # | Mission | Manager flow | semantic | fix 후 |
|---|---------|-------------|---------|-------|
| NL-M1 | 컨테이너 수 | docker_manage(ps) + 27 정확 + 보안 분석 | ✅ | - |
| NL-M2 v2 | fw nftables 규칙 | docker_manage(ps) + 한계 인지 (nft list 필요) | △ | fix-A+B |
| NL-M3 | web ModSec | check_modsecurity 자율 + ReAct 구조 + 한계 인지 | △ | - |

**Manager (gpt-oss:120b) 의 핵심 능력 입증**:
1. 자연어 → tool_calls 변환 ✅
2. specialized skill (check_modsecurity) 자율 선택 ✅
3. GOAL/SUCCESS/TODO/tool_calls ReAct 구조 자율 생성 ✅
4. 보안 컨텍스트 자율 추가 (TLS 권고, Docker security) ✅
5. 한계 인지 + 추가 명령 필요 보고 ✅

**미해결**: bastion 컨테이너 의 네트워크 reachability (인프라 차원 fix 필요)
