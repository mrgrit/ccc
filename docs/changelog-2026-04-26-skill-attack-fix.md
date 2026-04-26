# 2026-04-26 — Skill recall + attack-mode 일괄 개선 (R2→R3 전환점)

> **목적**: R2 retest 1180/1285 분석에서 발견한 5건 병목을 진단·수정.
> R2 종료 대기하지 않고 mid-flight 적용하여 잔여 105건 + R3 에서 효과 측정.

## 요약

| # | 영역 | 진단 | 수정 | 예상 효과 | 측정 방법 |
|---|------|------|------|-----------|-----------|
| 1 | attack/battle 거부 | derestricted 모델도 `I'm sorry, I can't help` 거부 (≥6 출현) | `attack_mode` lab-context preamble (격리 cyber range 명시) | no_execution 392 → -200~250 | 다음 사이클 `grep -c no_execution run.log` 비교 |
| 2 | dormant skill 24개 | 카테고리화 prompt 추상적 ("'IoC 추출' → ioc_export") | 5 few-shot tool_call 예시 (memory_dump/attack_simulate/prompt_fuzz/compliance_scan/history_anchor) | unique skill 9 → 15+ | `grep -oE "skill=[a-z_]+" run.log \| sort -u \| wc -l` |
| 3 | ATTACK_COURSES 누락 | web-vuln-ai (32% pass) / physical-pentest-ai / ai-security-ai 가 일반 모델 + preamble 미적용 | api.py ATTACK_COURSES 7개로 확장 | 3과목 pass율 +10~15% | `report.md` 과목별 pass율 |
| 4 | 첫 turn 도구 0 → 무효 종료 | qa_fb 22 + 일부 fail 의 직접 원인 | MAX_TURNS 6→8, FIRST_TURN_RETRY 1 (거부 감지 시 hint 추가) | qa_fb +pass 회수 | `grep -c first_turn_retry` & qa_fb 추이 |
| 5 | probe Asset Δ=0 | probe_all 의 target="" 분기로 autoscan 미실행 (P11 Phase 5a 버그) | vm_ips 전체 순회로 register_asset (probe_all 분기 신설) | assets 11 → +N (N=vm_ips 카운트) | phase5_monitor.py 의 assets count |

## 진단 데이터 (R2 1180건 시점)

```
$ grep -c "I'm sorry\|cannot help\|can't help" run.log
6                                      # 노출된 거부 메시지

$ grep -oE "skill=[a-z_]+" run.log | sort | uniq -c
    135 skill=shell                    # 압도적
     80 skill=file_manage
     70 skill=probe_all
     53 skill=ollama_query
     46 skill=probe_host
     14 skill=qa
      7 skill=docker_manage
      4 skill=check_wazuh
      4 skill=analyze_logs
                                       # 33 catalog 중 9 active만 호출 (24 dormant)

$ phase5_monitor 출력
assets=11, anchors=5, events=6 — Δ 0 (probe 17회 실행됐지만 자산 변화 0)
```

## 수정 상세

### 1. `packages/bastion/agent.py` — `_build_react_system_prompt()`
- **+attack_mode preamble** (line ~1407): 격리 lab + 합법 학습 + 거부 금지 8줄
- **+few-shot 예시 5종** (line ~1438): 실제 tool_call 패턴 보여주기
- 이전 카테고리화 prompt (commit 59cc9fe) 유지 + 위 두 추가

### 2. `packages/bastion/agent.py` — ReAct 루프
- `MAX_TURNS = 6 → 8` (line ~1545)
- `FIRST_TURN_RETRY = 1` 신설: 첫 turn tool_call 0 + tool_outputs 0 → 강제 재촉 user 메시지 push
- 거부 패턴 감지 (sorry/cannot help/can't/as an ai/decline/unethical/illegal) 시 추가 hint

### 3. `packages/bastion/agent.py` — `_update_assets_from_result` autoscan
- `probe_host`: vm_ips 우선, fallback regex
- `probe_all`: target 비어있던 분기 fix → vm_ips 전체 순회로 모든 role 등록
- 예외 시 `autoscan_error` 이벤트 발생 (silent fail 차단)

### 4. `apps/bastion/api.py`
- `ATTACK_COURSES`: 4 → 7 (web-vuln-ai/physical-pentest-ai/ai-security-ai 추가)
- `/chat` 엔드포인트: `agent.attack_mode` 플래그 swap (course 별 활성화)
- `model_routing` 이벤트에 `attack_mode` 필드 추가

## 배포

| 단계 | 결과 |
|------|------|
| CCC repo commit | ae55254 (`feat(bastion): attack_mode + few-shot + turn budget + autoscan probe_all 일괄 개선`) |
| Bastion repo commit | 46ee727 (`feat(prompt): attack_mode lab-context + few-shot tool_calls + turn budget 8`) |
| 양 repo push | ✓ |
| 원격 `/opt/bastion` git pull | ✓ (4 markers 확인) |
| 원격 `/home/ccc/ccc/apps/bastion/api.py` scp | ✓ |
| 원격 bastion 재시작 | ✓ (setsid nohup) |
| 헬스 검증 | `attack_courses=7` 확장 확인 |

## R3 측정 계획

R2 종료 (cursor 1285) → R3 자동 트리거 → 잔여 비-pass 약 800건 재테스트.
다음 측정 5축:

1. **거부율**: `grep -c "I'm sorry\|cannot help" run.log` (R2: 6 → R3 목표 0)
2. **unique skill**: `grep -oE "skill=[a-z_]+" run.log | sort -u | wc -l` (R2: 9 → R3 목표 15+)
3. **first_turn_retry 발동**: `grep -c first_turn_retry run.log` (R3 새 측정)
4. **과목별 pass 율 변화**: report.md 의 attack/battle/web-vuln/physical/ai-security 5과목 (각 +10~15% 기대)
5. **Asset Δ**: phase5_monitor 의 assets (11 → +N) — probe_all 호출 후

## 다음 사이클에서 자동 점검할 것

cron-fired 자동 사이클이 다음을 수행:
- `python3 scripts/retest_report.py` 실행
- 위 5축 grep 명령으로 효과 측정 + report.md 갱신
- `docs/inflight-projects.md` P10/P3 항목에 R3 결과 기록
- 거부율 > 0 잔존 시 → derestricted prompt 추가 강화 (LAB CONTEXT 의 거부 금지 부분 강조)
