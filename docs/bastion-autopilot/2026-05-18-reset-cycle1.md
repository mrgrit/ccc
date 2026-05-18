# Bastion Autopilot — Reset Cycle 1 (Fresh Deploy 2026-05-18)

**Fresh deploy 시각**: 2026-05-18 15:05 (UTC)
**Cycle 종료 시각**: 2026-05-18 15:55 (UTC) — 약 50분 연속 작업
**Baseline**:
- 6v6 컨테이너 27 (core 9 모두 Up)
- Bastion KG: `graph_nodes=0, history_anchors=0` (완전 reset)
- F1-F6 fix 모두 적용 (commit cd54f3a)
- **F7 fix 새로 발견 + 적용 + push (commit 304d3f54)**

## 🔴 핵심 발견 — F1 fix 가 cold-start 에서 회귀 (F7 새로 적용)

### 증상
Reset M1 / M2 모두: skill `success=true, output="..."` 인데 LLM 가 "도구 실행 실패" 거짓 보고.

### 근본 원인
`agent.py:2377-2380` 의 F1 fix 의 `_any_skill_ok` 가 `turn_traces` 검사 — 그런데
`turn_traces` (line 2015) 는 `content / thinking / tool_calls 만 저장 — success / output 미저장`.
결과: 항상 `_any_skill_ok=false` → "도구 실행 실패" prompt branch → LLM 가짜 보고.

### 왜 cycle 1-11 (cumulative KG) 에서는 가려졌나
Cumulative KG (50+ anchor) 가 LLM 응답을 안정시켜 `last_assistant_content` 가 punt 가 아닌 정상 응답을 만들었음 → `_synth_prompt` block 자체가 호출 안 됨 (line 2361 의 조건).
Fresh state 에서는 `empty_content_retry x2 → self_verify_fail → prompt_fallback` 경로 → punt → 항상 잘못된 branch.

### F7 fix

```python
# ★ F7 fix (2026-05-18 reset cycle 1): turn_traces 는 content/thinking 만
#   저장 (line 2015) — success/output 미저장. 결과적으로 _any_skill_ok 항상
#   false → 도구 성공 시 에도 "도구 실행 실패" prompt branch → LLM 가짜 보고.
#   all_tool_outputs (line 2318 등) 가 진짜 success/output source.
_any_skill_ok = any(
    (to.get("success") and (to.get("output") or "").strip())
    for to in (all_tool_outputs or [])
)
```

Push: `commit 304d3f54`

## Mission 결과 (reset cycle 1, M1~M20)

| # | Mission | skill | semantic | 비고 |
|---|---------|-------|---------|------|
| R1 | docker ps wc -l (W01 S1) | success | ❌ | F1 회귀 발견 |
| R2 | ProxyJump 4 hosts | success | ❌ | F1 회귀 |
| R3 | M1 재시도 (F7 후) | success | ✅ | **F7 검증 ✅** "27개 컨테이너" |
| R4 | M2 재시도 (F7 후) | success | ✅ | "fw, ips, web, wazuh.manager" |
| R5 | web sudo apache2ctl ModSec | success | ✅ | security2_module 충족 |
| R6 | fw nft list ruleset | success | ✅ | six_filter 표 인용 |
| R7 | siem Wazuh agent_control | success | ✅ | 4 agent active |
| R8 | attacker nmap 4 ports | success | ✅ | 22/80/443/8080 |
| R9 | aisec /kg/health (recursive) | success | △ | output 정상, 짧은 응답 |
| R10 | docker ps grep -c (변형) | success | ✅ | sim=0.583 → new |
| R11 | docker ps wc -l (동일 재시도) | success | ✅ | **reuse confidence 0.95** |
| R12 | fw conntrack -S | success | ✅ | invalid 92/415/70 |
| R13 | ips pgrep suricata | success | △ | PID 49 → "49개" 미스해석 |
| R14 | attacker which 4 tools | success | ✅ | nmap/nikto/sqlmap/hydra |
| R15 | attacker curl juice WAF | success | △ | LLM 해석 모순 (200 + 차단) |
| R16 | siem ossec.conf head | success | ✅ | XML config 헤더 |
| R17 | docker inspect 6v6-dvwa | **fail** | ✅ | LLM 명령 잘못 번역 + F7 정직 보고 |
| R18 | docker ps filter dvwa json | success | ✅ | "6v6-dvwa Up 12 minutes" |
| R19 | fw sysctl ip_forward | - | ❌ | KG hit (M18 anchor) 잘못 유도 |
| R20 | bastion /kg/metrics (recursive) | success | ✅ | counters/observations/ts |

### 통계 (M1-M23, 50분 연속 작업)

| 단계 | PASS | △ partial | ❌ fail | 종합 |
|------|------|-----------|--------|------|
| **F7 적용 전 (M1, M2)** | 0/2 | 0 | 2 | 0% (회귀 발견) |
| **F7 적용 후 (M3-M23)** | 15/21 | 5 | 1 | 71% strict, **95% (incl. △)** |

- F7 fix 후 skill 실행 자체는 **20/21 success** (M17 의 llm_translate hallucination 만 fail)
- LLM 해석 정확도: M9/M13/M15/M19/M23 의 5 partial — bastion 코드 fix 가능 영역 (F8 candidate)

### 추가 mission (M21-M23)
- M21: fw auditctl-s → "command not found" 정직 보고 ✅
- M22: docker logs --tail 5 6v6-ips → ssh login 로그 정확 인용 ✅
- M23: attacker nikto 빠른 스캔 → banner 만 추출, LLM 결론 가짜 △

## 핵심 인사이트 — Reset 의 교훈

### 1. Cumulative KG 가 fix bug 를 가려줄 수 있다
- Cycle 1-11 에서 100% 보였지만 F1 fix 의 근본 bug 는 그대로 있었음
- Fresh state → bug 표면화 → F7 적용 → 재검증
- **교훈**: 매 N cycle 마다 reset 검증 필요 (regression test)

### 2. KG cold-start → 즉시 reuse 가능
- 0 anchor → R1 first call (new)
- R3 (R1 동일) = **reuse 0.95** (1 anchor 만으로도 reuse 가능)
- 즉, KG-2 Reuse decision 의 발현 = anchor 1개 + 동일 query

### 3. KG hit 의 양면성 — M19 의 경우
- KG context "used:true, hits:1" 이지만 prior anchor (M18 의 docker inspect) 가 sysctl mission 에 잘못 inject
- LLM 응답을 "CPU/메모리 사용량 없음" 식으로 잘못 유도
- **insight**: KG context relevance scoring 필요 (sim threshold 보다 더 sophisticated)

### 4. LLM hallucination 영역 (코드 fix 가능)
- M9, M13, M15, M19 = LLM 응답 의 minor 미스
- "PID 49 → 49개", "200 + 차단", json tool-call format 으로 결론 대체
- 후속 fix candidate: `_synth_prompt` 에 "PID 와 개수 구분, http_code 와 차단 표시 일치" 룰 추가

## KG state 추이

| 시점 | graph_nodes | history_anchors |
|------|-------------|----------------|
| Reset baseline | 0 | 0 |
| M5 시점 | 8 | 2 |
| M9 시점 | 27 | 7 |
| M14 시점 | 39 | 13 |
| **종료 (M20)** | **53** | **20** |

→ 20 mission 의 anchor 의 cumulative growth. R3 의 reuse decision 도 정확 동작.

## 다음 cycle (reset cycle 2) 후보

- W04~W15 mission 더 진행 (cumulative coverage)
- F8 fix: `_synth_prompt` LLM hallucination 더 엄격 — PID/개수/HTTP/차단 구분
- F9 fix: prose extraction 의 quote-handling 강화 (M17 의 dvwa 회귀 방지)
- KG context relevance scoring (M19 의 잘못된 inject 방지)
