# In-flight Projects Tracker

> **새 세션은 이 파일을 먼저 읽고 시작한다.** 미완 프로젝트의 단일 진실원.
>
> - 각 프로젝트: **Definition of Done (DoD) 체크리스트** + **Next concrete step** + **Status**
> - DoD 모두 체크 → `## Closed` 섹션으로 이동
> - cron 자동 사이클이 in-progress 중 next step 1건 진행 후 갱신·commit

업데이트: 2026-04-26

---

## In-Progress

### P1. Precinct 6 dataset 통합  [STATUS: scaffold only]

**동기**: WitFoo Precinct 6 (Apache 2.0, 1억 signal + MITRE + incidents + graph) 로
합성 데이터 한계 해결. paper §6 의 "real-world fidelity" 보강.

**Definition of Done**:
- [x] `scripts/import_precinct6.py` 스캐폴드 + sample dry-run (5 incidents)
- [x] HistoryLayer/KG/MITRE 임포트 함수 골격
- [ ] HF 실데이터 1 파일 다운로드 → 실제 schema 확인 (parquet vs jsonl 등)
- [ ] format adapter 실 schema 로 보강 + 검증
- [ ] **Top-N hot pattern (1만) RAG POC** — bge-base 임베딩 + Faiss IVF, GPU 1분
- [ ] dedup + 카테고리 sample (100만) 본격 운용
- [ ] `scripts/precinct6_aggregate.py` — top-N IoC 자동 anchor 등록 (전략 D)
- [ ] paper §6 Track B 에 Precinct 결과 추가

**Next concrete step**: HF 외부 접근 1회 — `huggingface-cli download witfoo/precinct-6 --include "incidents*"`. 파일 1개로 schema 결정 → adapter fix.

**Files**: `scripts/import_precinct6.py`, `docs/changelog-2026-04.md` §B4

---

### P2. R2 round retest 완주  [STATUS: ✅ COMPLETE → moved to Closed]

→ Closed 섹션 참조.

---

### P3. R3 round retest  [STATUS: in progress (cursor 111/1261, +93 재큐, driver v2 health-check)]

**진단 (2026-04-26 14:40)**: 사용자 가설 적중 — bastion 단일 워커 + driver+내 background curl 동시 호출 → connection refused 35건 (14:19~14:20:36 cluster).
**수정 v2 (commit pending)**:
- driver_r3.sh: bastion 헬스 wait_for_bastion() + connection refused 시 1회 retry
- 잃은 93 step 재큐 → queue_r3.tsv 1168 → 1261
- 안정화 후 (#103~#110) 8건: 0 error / 4 fail / 3 pass / 1 fail = **37.5% pass rate**
  - cve_lookup skill 호출 발견 (신규 dormant skill 첫 활성화 ✓)

**동기**: P2 완료 후 잔존 fail 을 한 번 더 retest 해서 누적 개선 확인.

**Definition of Done**:
- [ ] P2 완료 대기
- [ ] 잔존 fail 추출 → 새 supplemental queue
- [ ] driver 재가동
- [ ] R3 최종 리포트
- [ ] paper §7 Figure 1 (R0→R1→R2→R3 evolution chart) 데이터 채움

**Next concrete step**: P2 완료 시 자동 트리거. 별도 액션 불필요.

---

### P4. Battle scenarios semantic verify 수기 작성  [STATUS: 23/192 (sqli-vs-waf + xss-vs-filter 완료)]

**동기**: battle-scenarios YAML 의 verify 가 keyword only. semantic-first judge 가 작동하려면 수기 작성 필수.

**Definition of Done**:
- [ ] 15 시나리오 × 평균 13 mission = 192 미션
- [ ] 시나리오당 1 commit (15 commits)
- [ ] 한 사이클에 1~2 시나리오만 (스크립트/템플릿 금지)
- [ ] paper §7 Battle scenarios 결과 reflect

**Next concrete step**: `contents/battle-scenarios/apt-phase1.yaml` 부터 미션별 instruction+hint+target_vm 읽고 4-요소 (intent/success_criteria/acceptable_methods/negative_signs) 작성.

**Files**: `contents/battle-scenarios/*.yaml`

---

### P5. Bastion-Bench 590 hold-out task 작성  [STATUS: 5/590]

**동기**: paper §6 Track B 의 핵심. 개발 corpus (3,089 step) 와 완전 분리 신규 task.

**Definition of Done (카테고리별)**:
- [x] Pilot 5건 (각 카테고리 1건) 작성 + format 확정 — `pilot-tasks/`
- [ ] pentest (80) — 0/80
- [ ] soc-ops (80) — 1/80
- [ ] web-vuln (60) — 0/60
- [ ] compliance (60) — 0/60
- [ ] incident-response (60) — 1/60
- [ ] secops (60) — 1/60
- [ ] ai-safety (60) — 1/60
- [ ] ai-ir (50) — 0/50
- [ ] ai-utilization (40) — 0/40
- [ ] ai-pentest (40) — 0/40
- [ ] 채점 파이프라인 검증 (judge 결과 vs manual review ≥80% 일치)

**Next concrete step**: pilot 5건을 실제 Bastion 으로 1회 실행 → 채점 정확도 검증 → 기준 통과 시 590 본격 작성 시작.

**Files**: `contents/papers/bastion/01-evaluation-design.md`, `contents/papers/bastion/pilot-tasks/`

---

### P6. 외부 벤치마크 실측  [STATUS: not started]

**동기**: paper Table 1 의 Cybench/CyberSecEval/NYU CTF/InterCode-CTF/HarmBench/AgentBench-OS 6 종 실측 → 클라우드 모델 baseline 과 비교.

**Definition of Done**:
- [ ] `benchmarks/common/bastion_client.py` — 공통 어댑터
- [ ] Cybench 40 task pilot — adapter + 5 task 실행
- [ ] Cybench 전체 40 + NYU CTF subset 60
- [ ] CyberSecEval 1,000 prompt
- [ ] HarmBench cyber subset (~100)
- [ ] InterCode-CTF 100 (turn-count 측정)
- [ ] AgentBench OS subset 60
- [ ] paper Table 1 의 XX% 자리 채움

**Next concrete step**: `benchmarks/cybench/` 디렉토리 생성 + 외부 mirror 에서 Cybench repo clone → adapter 작성.

**Files**: 미생성 (`benchmarks/`)

---

### P7. Production trial 30일  [STATUS: not started]

**동기**: paper §7.4 Track C — 4 시나리오 (월간 점검·CVE 대응·IR drill·변경 관리) × 30일 연속 운용.

**Definition of Done**:
- [ ] 시나리오 4종 픽스처 작성 (CVE feed · IR drill · 변경 CR)
- [ ] 운영자 inline review 체크리스트 정의
- [ ] day-by-day 일정 실행
- [ ] paper Table 4 (시나리오별 wallclock·HITL·critical errors) 채움

**Next concrete step**: `contents/papers/bastion/03-real-world-scenarios.md` 의 시나리오 fixture 를 실제 실행 가능 형태로 변환.

**Files**: `contents/papers/bastion/03-real-world-scenarios.md`

---

### P8. attack-adv-ai / battle-ai 추가 진단  [STATUS: partial — harmony fix 적용]

**동기**: R2 에서 attack-adv-ai 0%, battle-ai 0% 정체. harmony format 폴백 추가했으나 일부만 효과.

**Definition of Done**:
- [x] derestricted 모델 라우팅 (P14) — done
- [x] harmony format tool-call 폴백 (P15) — done
- [ ] R2 종료 후 attack/battle 4 과목 fail 패턴 재분류
- [ ] 새 fail 유형이 보이면 신규 skill 또는 prompt 보강
- [ ] R3 round 에서 attack/battle pass rate ≥30% 목표 달성

**Next concrete step**: P2 완료 후 run.log 의 attack/battle fail 만 추출 → 패턴 분류 → fix.

---

### P9. Paper 실험 수치 채우기  [STATUS: structure done, numbers XXX]

**동기**: paper-draft.md v0.3 모든 표·수치가 XXX placeholder.

**Definition of Done**:
- [ ] R0/R1/R2/R3 결과 → §7.5 Family table
- [ ] Bastion-Bench 카테고리별 결과 → §7.3 Table 2
- [ ] reuse rate / step variance → §7.3 Table 3
- [ ] L4 History ablation → §7.3 Table 4
- [ ] Production trial 결과 → §7.4 Table 5
- [ ] 외부 벤치 (P6) → §7.2 Table 1
- [ ] Abstract / Conclusion 의 X.X 자리 채움

**Next concrete step**: P3 완료 시 R3 수치부터 채움. 이후 P5/P6/P7 결과 누적.

**Files**: `contents/papers/bastion/paper-draft.md`

---

### P10. Skill 카탈로그 동적 확장  [STATUS: 33 baseline, recall 문제 발견]

**동기**: feedback_dynamic_skill_add.md 정책. retest fail 패턴에서 카테고리 부족 skill 발견 시 즉시 추가.

**Definition of Done**:
- [x] 18 → 33 1차 확장
- [x] R2 retest 결과 모니터 (1150/1285) — **신규 missing skill 0건**, 그러나 agent 가 9 skills 만 사용 (shell/ollama_query/probe_*/file_manage/docker_manage/analyze_logs/check_wazuh/qa)
- [x] **신규 finding (2026-04-26)**: 33 catalog 중 24개 (IR forensic·AI prompt_fuzz/garak·pentest cve_lookup·compliance·history) **호출 0건** → router/prompt 가 신규 skill 추천을 안 함
- [x] **수정 (commit 59cc9fe + bastion 7b48d29)**: skills.py 에 SKILL_CATEGORIES (9 카테고리 + trigger 키워드) 추가, agent.py `_build_react_system_prompt` 가 skill 을 카테고리 그룹핑 + 14 휴리스틱 매핑 + shell fallback 금지 가드. **bastion remote 재시작 완료** (skills=33 헬스 확인).
- [x] **2차 수정 (commit ae55254 + bastion 46ee727, 2026-04-26 13:30)**: attack_mode lab-context preamble + 5 few-shot tool_call 예시 + MAX_TURNS 6→8 + FIRST_TURN_RETRY (거부 감지 hint) + ATTACK_COURSES 7개 확장 (web-vuln/physical/ai-security 추가) + probe_all autoscan 버그 fix. 상세: `docs/changelog-2026-04-26-skill-attack-fix.md`.
- [ ] R3 자동 사이클에서 측정 5축 적용:
  - 거부율 `grep -c "I'm sorry\|cannot help" run.log` (R2: 6 → 목표 0)
  - unique skill `grep -oE "skill=[a-z_]+" run.log | sort -u | wc -l` (R2: 9 → 목표 15+)
  - first_turn_retry 발동 횟수
  - 과목별 pass율 (attack/battle/web-vuln/physical/ai-security 5개)
  - Asset Δ (probe_all autoscan 후 assets 11 → +N)
- [ ] paper §3.5 의 "33 skills" → "33 catalog · N active (cat+few-shot 유도 후)" 정량 보고

**Next concrete step**: R2 잔여 105건 + R3 진행 중 위 5축 측정. 다음 자동 사이클(13:37 fire)에서 첫 데이터.

---

---

### P12. 자율 공방전 (Autonomous Multi-team Battle)  [STATUS: Phase 1 in progress]

**동기**: 현재 1v1 (Red/Blue 고정역할) 만. 다중 팀이 자기 자산으로 공격하면서 동시에
방어하는 "ffa-style" 모드 부재 → 공방전 다양성 부족.

**Definition of Done**:
- [ ] DB: battle_participants (per-team) + battle_attack_claims (per-attempt)
- [ ] battle_type='autonomous' 지원 + 무제한 join (team_# 자동 할당)
- [ ] API: /battles/{bid}/my-targets, /my-defense, /claim-attack, /claim-defense, /incoming-attacks, /scoreboard
- [ ] semantic judge 가 claim 채점 (attack_landed +10 / defense_block +5 / own_breach −10)
- [ ] Battle.tsx 자율 모드 view (전체 팀 점수판 + 내 공격 미션 + 내 방어 미션 + incoming attacks)
- [ ] Phase 2: Wazuh/Suricata 자동 탐지 → defense_block 자동 점수
- [ ] Phase 3: AI 자율 모드 — 각 팀 Bastion 이 Red+Blue 동시 자율

**Next**: DB 스키마 + 4 API + 자율 모드 UI 컴포넌트.

**Files**: apps/ccc_api/src/main.py, apps/ccc-ui/src/pages/Battle.tsx

---

### P13. VulnSite Catalog (다양한 취약 사이트 + 3 난이도)  [STATUS: Phase 1+2 완료, Phase 3 대기]

**동기**: JuiceShop 단조로움. 사이트 7종 × easy/normal/hard 3 모드 → 공방전 다양성.
**Rich vulnerability 강조**: 사이트당 22~30 취약점, 다단계 chain 포함, 공방전이 오래 지속되도록.

**카탈로그**:
- 기존: JuiceShop (e-com, 50+ vuln) · DVWA (PHP 학습, 12~20 vuln)
- 신규 5종 (Phase 2): NeoBank · GovPortal · MediForum · AdminConsole · AICompanion = **130 vuln 총**

**Definition of Done**:
- [x] **Phase 1**: 카탈로그 DB (vuln_sites, vuln_site_modes) + admin selector UI. 7 사이트 + 9 mode seed.
- [x] **Phase 2 (신규 5종)**: 각 Flask 단일 파일 + 디자인 테마 + 풍부한 vuln + smoke 검증 + DB promote
  - [x] NeoBank (금융, port 3001) — 30 vuln (IDOR·JWT·race·뱅킹 BAC). 잭팟/transfer race PoC 검증
  - [x] GovPortal (정부, port 3002) — 25 vuln (SAML 우회/JIT, JWT none, 권한 상승, audit tampering, mass assign)
  - [x] MediForum (의료, port 3003) — 22 vuln (stored XSS post/comment/profile/DM/SVG, PII bulk, IDOR). V07/V08/V10/V17/V22 PoC 검증
  - [x] AdminConsole (DevOps, port 3004) — 28 vuln (cmd inject·SSRF·eval RCE·pickle·yaml·LFI+log poison·weak reset·JWT none·secrets IDOR). V07/V11/V14/V15/V16/V20/V04 PoC 검증
  - [x] AICompanion (LLM, port 3005) — 25 vuln (OWASP LLM Top 10: prompt inject·RAG poison·jailbreak·tool abuse·excessive agency·model theft). mock + ollama 백엔드. V01/V03/V04/V05/V09/V10/V13/V14/V18 PoC 검증
- [x] **Phase 3 (5 사이트 hard mode)**: 각 5 chain seed-hard.md (4-6 step + MITRE + BLUE 가이드 + 점수)
  - [x] NeoBank hard (Chain CCAT/Arbitrage/JWT/SSRF/WebShell, +310점)
  - [x] GovPortal hard (Chain SAML/Auth3중/XXE/PII+CSRF/webshell, +280점)
  - [x] MediForum hard (Chain 의사DM/SVG→Admin/SSN→사회공학/APIToken/pickle, +290점)
  - [x] AdminConsole hard (Chain cmdRCE/SSRFCloud/Reset→exec/pickle/Upload+JWT, +340점)
  - [x] AICompanion hard (Chain RAGpoison/Stored→admin/Tool→exfil/Jailbreak/CSRFpersistent, +320점)
  - [x] DB seed: 5 사이트 hard mode available=TRUE (vuln_site_modes 갱신)
- [ ] **Phase 4**: Bastion-Bench web-vuln 카테고리 task 분포 (사이트당 5~10 task)

**Files**: contents/vuln-sites/{neobank,govportal,mediforum,adminconsole,aicompanion}/ · apps/ccc_api/src/main.py

---

### P11. Asset/Architecture + Work 9-tier hierarchy  [STATUS: Phase 1-5 구현 완료]

**Definition of Done**:
- [x] graph.py NODE_TYPES + EDGE_TYPES 확장 (Mission/Vision/Goal/Strategy/KPI/Plan/Todo/Asset/Narrative/Anchor + relates_to/derives_from/connects_to/data_flows_to/manages/realizes/measures/contributes_to)
- [x] packages/bastion/asset_domain.py — register_asset/list_assets/link_assets/architecture_topology/architecture_packet_flow/autoscan_register
- [x] packages/bastion/work_domain.py — Strategic 5(add_mission/vision/goal/strategy/kpi+record_kpi) + Tactical 2(add_plan/add_todo) + update_status + trace_to_mission + strategic_dashboard
- [x] apps/bastion/api.py — /assets/register · /list · /link · /architecture/topology · /flow · /work/{mission,vision,goal,strategy,kpi,kpi/record,plan,todo,status,trace/{id},dashboard} 등 16 endpoints
- [x] Knowledge UI 도메인 토글 (전체/Asset/Architecture/Work/Operational) + 새 노드 색상 9종
- [ ] (옵션) Architecture 전용 토폴로지 view (현재는 같은 cytoscape에서 필터로)
- [ ] (옵션) Strategic dashboard 별도 페이지 (KPI 차트)
- [ ] paper §4 도식 + Asset/Architecture/Work 단락 추가

**Next**: 옵션 항목은 운영 시작 후 필요시. seed 데이터 (mission/vision/goal/strategy/kpi 1세트) production 배포 시 1회 등록.


## Closed (누적 완료)

### 2026-04 초중반
- [x] verify.semantic 6,188 step 수기 작성 (605 lab YAML, 20 과목 × 평균 15주)
- [x] Course 교안 전수 감사 (300/300 lecture.md)
- [x] derestricted course-based routing (4 → 7 attack courses)
- [x] A·B·C 일괄 픽스 (suffix · expect 보강 · 모델 swap)
- [x] L4 History layer 구현 + 통합 + UI
- [x] Skill 18 → 33 확장
- [x] Battle solo + admin Battles 탭
- [x] PE-KG-H 4계층 메모리 paper 정렬
- [x] docs/changelog-2026-04.md 정리
- [x] **P11 Asset/Architecture/Work 9-tier hierarchy** (Phase 1-5)
- [x] **P12 자율 공방전 MVP** (autonomous multi-team)
- [x] **P13 Phase 1+2 — VulnSite 카탈로그 + 5 신규 사이트** (NeoBank/GovPortal/MediForum/AdminConsole/AICompanion = 130 vuln)

### 2026-04-26 후반 (R2→R3 전환 + 5건 일괄 개선)
- [x] **P2 R2 retest 완주** — 1285/1285, +118 pass (R0 1,476 → R2 1,922 = 62.2%)
- [x] **5건 일괄 prompt 개선** (commit ae55254/46ee727 + retro 7bf21aa/f5d72c4)
  - attack_mode lab-context preamble (격리 cyber range, 거부 금지 명시)
  - 5 few-shot tool_call 예시 (memory_dump/attack_simulate/prompt_fuzz/compliance_scan/history_anchor)
  - MAX_TURNS 6, FIRST_TURN_RETRY 1 (거부 감지 hint 추가)
  - probe_all autoscan 버그 fix (vm_ips 전체 순회)
  - ATTACK_COURSES 4 → 7 (web-vuln-ai/physical-pentest-ai/ai-security-ai 추가)
- [x] **#4 Tools spec 키워드 필터** (33→top 12, 19KB→7KB, dormant skill 활성화 cve_lookup 첫 사례)
- [x] **R3 ERROR 35 cluster 진단 + driver v2 healthcheck** (사용자 가설 적중: 동시 요청 → connection refused)
- [x] **sync_to_bastion.sh runtime 양 경로** (`/opt/bastion/` + `/home/ccc/ccc/packages/bastion/`)
- [x] **Knowledge UI fullscreen + flexible** (App.tsx useLocation + html/body/#root height 100%)
- [x] **#6 vuln-sites/up.sh 자동화** — 5 사이트 일괄 배포 + 10/10 PoC smoke
- [x] **GovPortal 한글 dash 인코딩 버그 fix** (latin-1)
- [x] **#9 R3 자동 진단 스크립트** — `scripts/r3_diagnose.py` (5축 + cluster + ERROR 분류 + ◆◯⚠️)
- [x] **#11 README 갱신** (R0→R2 완료 → R3 진행, 5 vuln-site 섹션, 자율공방)
- [x] **#2 Paper draft v0.4** — 7→1 XXX 채움 (semantic 6188 / 모델 78%vs41% / DGX cost / Bastion-Bench 590) (local only, gitignore)
- [x] **#3 Paper §3.5 정량 분석** — 33 카탈로그 9 카테고리 표 + R2 active 9 → mitigation + lookup reuse 25%/adapt 46% (local only)

---

## 새 세션 진입 프로토콜

1. 이 파일 (`docs/inflight-projects.md`) 부터 읽는다
2. 사용자 요청이 in-flight 프로젝트와 연결되면 → 해당 P# 의 Next step 부터 시작
3. 새 작업이 끝나면 → DoD 체크박스 업데이트 + commit
4. 모든 체크박스 완료 → `Closed` 섹션으로 이동

## Cron 사이클 통합

매 2시간 cron 이 retest 보고 후 추가 동작:
- in-progress 중 *blocked 아닌* 첫 프로젝트의 next step 1건 진행
- inflight-projects.md 갱신 + commit
- 단, 한 사이클 한 작업 (큰 작업은 분할)
