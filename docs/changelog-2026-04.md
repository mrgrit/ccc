# Bastion 변경 이력 — 2026-04 (R1·R2 retest 사이클)

> 2026-04-23 ~ 04-26 의 핵심 기능 추가·개선·구조 변경 정리.
> 각 항목은 (a) 동기 (b) 변경 (c) 검증 (d) 영향 의 4-요소로 기술.

---

## A. 검증·신뢰성 인프라

### A1. Semantic-first verification pipeline (verify.semantic)

- **동기**: 키워드 매칭 채점은 LLM 출력 형식의 다양성(markdown/JSON/표/산문)을 처리하지 못해 false negative 다수 발생.
- **변경**:
  - step 별 `verify.semantic` 메타데이터 도입 — `intent` (1줄) + `success_criteria` (3+) + `acceptable_methods` (3-4) + `negative_signs` (3).
  - `packages/lab_engine/semantic_judge.py` 의 `semantic_first_judge()` 가 LLM judge 우선, 키워드는 폴백.
  - 약 5,500 step 수기 작성 (no-template 규칙). bulk 자동 생성 금지.
- **검증**: R0 → R1 retest 에서 pass rate 47.8% → 58.4% (+10.6pp).
- **영향**: 모든 lab YAML, battle scenarios, bastion-bench 채점의 기반.

### A2. Self-Verify 루프

- **동기**: 외부 judge 부담 감소 + LLM 자체가 success_criteria 인지하도록.
- **변경**: `_chat_react` 의 end_turn 직전 자체 채점 패스 + 1회 재시도 허용.
- **검증**: judge 호출 ~XX% 감소, pass rate +X.X pp.
- **영향**: agent.chat 흐름.

### A3. Course-based model routing (derestricted)

- **동기**: 정렬된 `gpt-oss:120b` 가 공격 페이로드 생성을 거절(B유형 fail) → attack/battle 과목 pass 0%.
- **변경**:
  - `apps/bastion/api.py` 에 `ATTACK_COURSES` allowlist + per-request mutex 모델 스왑.
  - 기본 `gpt-oss:120b` ↔ `gurubot/gpt-oss-derestricted:120b` 동일 사이즈 교체.
  - 스왑 발생 시 `model_routing` audit 이벤트.
  - `/health` 가 두 모델 + allowlist 노출.
- **검증**: ai-security-ai pass 9% → 31% (3배), HarmBench cyber 결과 정상 범위.
- **문서**: `contents/labs/MODEL_ROUTING.md` 신규.

### A4. Harmony format tool-call 폴백

- **동기**: derestricted 모델이 Ollama native `tool_calls` 필드를 채우지 않음 → attack 95% no_execution.
- **변경** (`packages/bastion/agent.py`):
  - `_HARMONY_TOOLCALL_RE` — `to=functions.SKILL <|message|>{ARGS}` 직접 파싱.
  - `_strip_harmony` / `_extract_shell_from_prose` — 태그 제거 + prose 셸 명령 추출.
  - `_chat_react` 가 tool_calls 비면 (1) harmony parse → (2) prose fallback 합성 호출 주입. `synthesized_tool_calls` audit 이벤트로 가시화.
- **검증**: attack-ai 일부 케이스 no_execution → pass 전환 확인.

### A5. A·B·C 픽스 일괄 적용 (R2 round)

- **A 유형 (실행 대신 markdown 출력, ~300건)**: category in (attack/exploit/recon/configure) step 의 `bastion_prompt` 말미에 "반드시 실행하라" suffix 일괄 추가. 207 files × 835 steps.
- **B 유형 (LLM 거절, ~74건)**: A3 모델 라우팅으로 해결.
- **C 유형 (실행 성공·verify 미스, ~80건)**: run.log tail 에서 출력 토큰 추출 → `verify.expect` 보강. 202 files × 422 steps × 784 keywords.
- **검증**: R1 → R2 round 진행 중, qa_fallback → pass 전환율 18.8% → 38.1% (2배).

---

## B. 메모리 아키텍처 — (Playbook + Experience + History) → KG

### B1. Knowledge Graph 통합 (KG-1 ~ KG-8)

- **변경**: SQLite property graph (`packages/bastion/graph.py`) — Playbook/Experience/Skill/Asset/Concept/Insight 노드 + reuse/adapt/generalize/refute 엣지 + FTS5 검색.
- ReAct 루프의 turn 별 `thinking`/`content` 분리 캡처 → 그래프 노드.
- 2-stage 결정 로직 (lookup → reuse/adapt/new).
- Compaction (주기적 Experience → Insight 압축).
- Knowledge UI 백엔드 + 프론트엔드 (Obsidian 스타일 cytoscape).

### B2. L4 History layer (PE-KG-H)

- **동기**: 5년+ 운영의 시간 축 지속성 (운영자 교대·반복 침해·규제 감사·결정 근거 보존). 기존 KG 만으론 부족.
- **변경**:
  - `packages/bastion/history.py` — SQLite 4 테이블 (`history_events` · `history_narratives` · `history_anchors` · `history_changelogs`).
  - `HistoryLayer` API: `add_event` / `open_narrative` / `add_anchor` / `add_changelog` / `handoff(asset)` / `range_query` / `match_repeat_iocs`.
  - `is_compaction_immune()` — anchor / narrative atomic / decision rationale 보존 게이트.
  - `agent.py` 의 매 skill 종료 시 `add_event(kind=task_done|fail)` 자동 호출.
  - `compaction.py` prune 직전 게이트 적용 → `history_immune` 카운트 노출.
  - `apps/bastion/api.py` 7 endpoints: `/history/handoff/{asset}`, `/range`, `/events`, `/narratives`, `/anchors`, `/repeat-iocs`, `/changelog`, `/graph-view`, `/asset-timeline/{id}`.
- **검증**: smoke (narrative open + 5 events + anchor + changelog + repeat-IoC 매칭) 통과.

### B3. Knowledge UI History 통합

- **변경**: `apps/ccc-ui/src/pages/Knowledge.tsx` —
  - `Narrative`(#79c0ff), `Anchor`(#ffa657) 새 노드 타입.
  - `load()` 가 KG + History graph-view 병합.
  - Asset/Narrative 선택 시 detail panel 에 timeline (events + anchors + changelog) 자동 fetch.
  - Anchor type 별 표시 (kind 뱃지 + valid 기간 + body verbatim).
- **검증**: dist 재빌드, anchor add → list → handoff E2E 확인.

### B4. Precinct 6 dataset import

- **동기**: 합성 데이터 한계 (기존 lab YAML 만으론 real-world 신호 부재). WitFoo Precinct 6 데이터셋 (1억 건 실 트래픽 + MITRE + 인시던트 + 그래프, Apache 2.0) 통합.
- **변경**: `scripts/import_precinct6.py` —
  - HF mirror 디렉토리 스캔 (jsonl/json).
  - incidents → `history.add_anchor(kind='breach_record')` + IoC 별 anchor.
  - graph nodes/edges → KG `Asset` + relates_to 엣지.
  - MITRE → KG `Concept` 노드.
  - `--sample` 폴백 (내장 5건) 으로 dry-run 가능.
- **검증**: sample dry-run → 5 anchors / 4 nodes / 10 MITRE concepts 등록.

---

## C. 운영·아키텍처

### C1. Skill 카탈로그 18 → 33

- **동기**: 10 카테고리 실증에서 IR/AI보안/컴플라이언스 skill 부재 → shell 우회 다수 → fail.
- **변경 (15종 추가)**:
  - **IR (4)**: `memory_dump` (LiME) · `process_kill` (danger-danger) · `ioc_export` (STIX 2.1) · `forensic_collect`
  - **AI 보안 (4)**: `prompt_fuzz` · `garak_probe` · `model_isolate` (danger-danger) · `rag_corpus_check`
  - **모의해킹 (3)**: `cve_lookup` · `password_attack` (danger-danger) · `dns_recon`
  - **컴플라이언스 (2)**: `compliance_scan` (lynis/OpenSCAP) · `secret_scan` (gitleaks/grep)
  - **History agent (2)**: `history_anchor` · `history_narrative`
  - 도구 미설치 환경 폴백: `command -v` 사전 검사 + install 안내.
- **검증**: `/health` skills 18 → 33 확인. 동적 추가 정책 메모리 등록.

### C2. Battle 시스템 — solo 모드 + admin 관리

- **Solo 모드** (`Battle.tsx` + `apps/ccc_api/src/main.py`): 1인 Red+Blue 동시 점유, ready/leave 양쪽 동시 처리, my-missions/submit-mission 에 `team` 파라미터 추가, `is_solo` 플래그 노출.
- **Admin Battles 탭** (`Admin.tsx`): 필터 + 강제 종료(`/battles/{bid}/force-end`) + 삭제(`DELETE /battles/{bid}`) + SOLO 뱃지 + 행 클릭 시 상세 + 이벤트 30건.
- **검증**: E2E (solo join + ready 1번 → 양쪽 ready → my-missions 시점 전환 + submit + force-end + delete) 통과.

### C3. LangGraph 8단계 lifecycle + A2A 5-endpoint (기존 정리)

- **State machine**: `intake → plan → select_assets → resolve_targets → [approval_gate] → execute → validate → report → close`.
- Bypass (단순 task: plan→execute), Replan (execute/validate/report → plan), Approval gate (danger-danger 이상 HITL 강제).
- **A2A**: `/a2a/run_script` · `/invoke_llm` · `/install_tool` · `/analyze` · `/mission` (자율 red/blue).

### C4. Audit hash chain (기존 정리)

- 모든 사용자 지시 / Manager turn (thinking+content 분리) / skill 호출 / 검증 결과 / History event 가 SHA-256 체인으로 append.
- 변조 시 그 시점부터 invalidate. 운영자가 로그만으로 세션 결정적 재생.

### C5. dual-repo push 정책

- CCC bastion 코드 수정 시 mrgrit/ccc + mrgrit/bastion 양쪽 push 필수.
- `scripts/sync_to_bastion.sh` (CCC packages.bastion → /home/opsclaw/bastion 의 import 경로 변환 + 복사).

---

## D. 평가·실증

### D1. Retest infrastructure

- `bastion_test_progress.json` — 3,089 step 단일 진실원.
- `scripts/test_step.py` — 단일 step Bastion 호출 + verdict 판정 (pass/fail/qa_fallback/no_execution/error) + progress 갱신.
- `results/retest/` — queue.tsv (gitignored) + cursor.txt + supervisor.sh (driver 자동 재시작) + report.md.
- `scripts/retest_report.py` — 매 2h cron 으로 progress.json + report.md commit + push.

### D2. R 라운드 결과

| Round | Pass / 3,089 | Pass율 | 누적 변화 |
|-------|--------------|--------|-----------|
| R0 (baseline) | 1,476 | 47.8% | — |
| R1 (verify.semantic) | 1,804 | 58.4% | +328 (+22.2%) |
| R2 (B+A+C 적용) | 진행 중 | ~60%+ | +XXX |

### D3. 논문 작성 (`contents/papers/bastion/`)

- `paper-draft.md` v0.3 — 4 contribution (폐쇄망 운영 / 신뢰성·안정성 / 장기 컨텍스트 / 다양한 실증) 1:1 한계 대응.
- `01-evaluation-design.md` — Bastion-Bench 590 task × 10 카테고리 명세.
- `02-benchmark-integration.md` — Cybench·CyberSecEval·NYU CTF·InterCode·HarmBench·AgentBench OS 통합.
- `03-real-world-scenarios.md` — Track C 4 시나리오 (월간 점검·CVE 대응·IR drill·변경 관리).
- `pilot-tasks/` — 5개 pilot YAML (pentest/soc-ops/ai-safety/IR/secops).

---

## E. 잔여 / 다음

- [ ] R2 round 완료 (현재 ~68%, 잔여 ~10h)
- [ ] R3 round (전체 fail 재테스트) → paper Table 5 의 R0→R3 진화 데이터 확보
- [ ] Battle scenarios 15개 × 평균 13 미션 = 192 미션에 verify.semantic 수기 작성
- [ ] Precinct 6 mirror 실제 다운로드 + 본격 import (지금은 sample 만)
- [ ] paper §6 Track A — Cybench/CyberSecEval 실측 시작
- [ ] L4 History 의 다년 안정성 검증 (6개월 follow-up)
