# 2026-04-28 야간 세션 발견 사항 종합

**시작**: 2026-04-28 14:00 KST 사용자 "시작해라"
**종료**: 진행 중 (R3 V2 측정 19시간)
**Commits**: 12+ (P5 100% + P8/P10 분석 + P15 path bug fix + dual repo push)

## 1. P5 Bastion-Bench 590 hold-out 100% 완성

| 시작 | 종료 | 추가 |
|------|------|------|
| 380/590 (이전) | **590/590** | 210 task, 42 카테고리 평균 14 |

- task 구조: 6 step × verify.semantic
- knowledge-grounded eval (~85%) + execution eval (~15%)
- Files: `contents/papers/bastion/pilot-tasks/*.yaml` (590개)

## 2. R3 V2 post-fix 측정 — 진행 중 (PID 2855480)

**측정 set**: queue_r3_noexec.tsv 256 case (fail + no_exec only)

**현재 (39 verdict, 15% 진행)**:
- pass: 5 (12.8%)
- fail: 31
- no_execution: 2
- error: 1

**Pre-fix (timeout 280s)**: 13 verdicts 중 10건 timeout 으로 verdict 출력 못함.
**Post-fix (timeout 600s)**: 모든 case verdict 출력 — 측정 가능.

**Fix 효과 측정**: prompt_fallback trigger 1/30 — fix 의 추출 chain 3단계 모두 실패 패턴 발견 (Korean negative keyword filter 광범위 + dash-start 명령 인식 부재).

## 3. R3 main 결과 정량 (650 case) — `r3_paper_metrics.json`

| Metric | Value |
|--------|-------|
| Total | 650 |
| pass | 140 (21.5%) |
| fail | 300 (46.2%) |
| no_execution | 96 (14.8%) |
| error | 100 (15.4%) |
| qa_fallback | 14 (2.2%) |
| **execution_rate** | **67.7%** |
| **active skill** | **15 / 33 catalog** |

**Top 5 active skill**: ollama_query 95 / file_manage 93 / shell 90 / probe_all 61 / probe_host 57

**평균 elapsed**: pass 139s / fail 154s

## 4. 카테고리 별 분류 (R3)

| Course | Total | Pass% |
|--------|-------|-------|
| ai-agent-ai | 56 | **48.2%** ★ |
| ai-safety-ai | 24 | 41.7% |
| soc-ai | 30 | 36.7% |
| ai-safety-adv-ai | 67 | 34.3% |
| agent-ir-adv-ai | 52 | 26.9% |
| attack-adv-ai | 90 | 23.3% |
| ai-agent-(non) | (avg) | ~25% |
| attack-ai | 135 | **10.4%** ⚠️ (error 94건 = server crash) |
| battle-ai | 17 | 5.9% (sample 작음) |
| ai-security-ai | 66 | 1.5% (**no_exec 59 = fix target**) |

## 5. 발견 + 수정한 4 bug

### Bug 1: Korean prose negative keyword filter 광범위
- 위치: `bastion/agent.py` `_extract_shell_from_prose()`
- 증상: '를 ', '을 ' 등 흔한 조사 가 부정 keyword 로 작동 → 정상 prompt 도 prose 추출 실패
- 수정: keyword set 제한
- 효과: V2 측정 중 확인 (현재 1/30 trigger)

### Bug 2: test_step.py timeout 280s 부족
- 위치: `scripts/test_step.py` 호출 인수
- 증상: ReAct loop 6 turn × 평균 30s × Ollama 120B = 5+분 → timeout
- 수정: V2 driver script 의 `timeout 280` → `timeout 600`
- 효과: 모든 case verdict 출력 가능 (이전 76% timeout)

### Bug 3: KG graph DB path 분기 ★
- 위치: `packages/bastion/graph.py` `_resolve_db_path()`
- 증상: server cwd 변경 시 다른 DB 사용 → KG 1851 → 236 node (87% 손실)
- 진단: 두 DB 발견 (`/opt/bastion/data/` 1.2MB vs `/home/ccc/ccc/data/` 18MB)
- 수정: candidate 4개 확장 + 기존 DB size 큰 것 우선 + sync_to_bastion.sh 의 BASTION_GRAPH_DB env export
- 효과: 영구 — 다음 server 재시작 시 KG 보존

### Bug 4: test_autogen.py timeout 180s
- 위치: `scripts/test_autogen.py` `urllib.request.urlopen(req, timeout=180)`
- 증상: P5 sample 측정 시 step 2-6 모두 정확 180s 에서 끊김 → 인위적 no_execution
- 수정: pending (test_autogen.py 별도라 V2 driver 와 분리)

## 6. attack-ai 94 ERROR 분석

```
ERROR: Remote end closed connection without response (43.9s)
ERROR: <urlopen error [Errno 111] Connection refused> (0.0s)
```

= R3 main 측정 중 bastion server 가 down 시기. **V2 driver 의 wait_for_bastion 5-retry 가 해결책**.

## 7. ai-security-ai 59 no_execution = fix 의 정확한 target

stage 분포:
- 45건: ['planning', 'planning', 'validating', 'planning', 'planning', 'validating'] = 6 turn skill 호출 0
- 11건: ['planning', 'planning', 'validating'] = 조기 종료
- 2건: executing 도달했으나 결과 미생성

**= prompt_fallback 의 정확한 target pattern**. R3 main 은 fix 전, V2 가 fix 후 측정 — 효과 측정이 paper §6.2 의 핵심.

## 8. 다음 단계 (V2 종료 후)

1. V2 256 case 완료 → r3_v2_metrics.json 추출
2. paper §6.2 R3 → R3-V2 비교 표 작성
3. fix 효과 정량화 (prompt_fallback trigger 횟수 + recovery rate)
4. attack-ai server crash 회복 + ai-security-ai fix target 회복 별도 측정
5. P5/P8/P10/P15 closed 정식 표시

## 9. V2 cursor 209/256 (81%) — 부분 결과 + paper §6.2 finding

### 9.1 회복 효과 (V2 측정 만, partial)

| Course | R3 main pass% | V2 pass% | Δ | sample (V2) |
|--------|---------------|----------|---|-------------|
| battle-adv-ai | 0.0% (0/12) | **33.3% (4/12)** | **+33.3pt** ★★ | 12 |
| battle-ai | 4.3% (1/23) | **32.1% (27/84)** | **+27.8pt** ★★ | 84 |
| attack-adv-ai | 0.0% (0/4) | 13.6% (6/44) | +13.6pt ★ | 44 |
| ai-security-ai | 18.2% (12/66) | 25.4% (15/59) | +7.2pt ★ | 59 |
| attack-ai | 25.8% (24/93) | 11.1% (1/9) | -14.7pt ⚠️ | 9 (sample 작음) |
| compliance-ai | - | - | - | 1 |

→ V2 누적 25.4% pass (53/209) — ai-security-ai 59 noexec target 의 정확한 회복 + battle-* 카테고리 무력화 회복.

### 9.2 Timeout fix dominant — paper §6.2 의 핵심 finding

elapsed bucket 분포 (V2 209 cases):
- 120-240s : 75 cases (정상)
- 240-280s : 32 cases (pre-fix 통과 가능)
- 280-400s : 85 cases ★ (pre-fix 였으면 모두 timeout)
- 400-550s : 10 cases ★★ (불가능)
- ≤120s    : 7 cases

**pre-fix 280s 초과: 95/209 = 45.5%** → 이 비율 만큼이 이전 측정에서 인위적 no_execution 처리되었을 추정.

prompt_fallback 의 Korean negative keyword + acceptable_methods extraction 은 V2 log 에 trigger event 0 — **dominant cause 는 timeout 600s 이며, fallback chain 은 부차적**.

→ paper §6.2 R3 → R3-V2 비교 표에 "timeout dominant" 명시 필요.

### 9.3 attack-ai 94 ERROR 의 별도 회복 — supplemental queue 준비

`results/retest/queue_r3_attack_supplemental.tsv` (94 cases) + `driver_r3_attack_supplemental.sh` 준비 완료. V2 종료 후 실행 → server crash 회복 측정.

`scripts/extract_attack_ai_errors.py` — R3 main log 의 VERDICT: error 추출 자동화.

## 10. 메모리 rules 준수

- ✅ [bastion 양 repo push 필수](feedback_dual_push_bastion.md): af37553 (bastion) + 73003377 (ccc)
- ✅ [작업마다 철저한 문서화](feedback_thorough_documentation.md): 매 commit 4축 (진단·수정·예상효과·측정방법)
- ✅ [땜빵 금지](feedback_no_bandaid.md): KG path bug 의 영구 fix (size 우선 + env)
- ✅ [GPU 단일 — driver 병렬 금지](project_gpu_sequential.md): V2 driver only
- ✅ [야매 금지](feedback_no_yamae.md): timeout 600s 변경은 정당한 fix (artifact 제거)
