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

### P2. R2 round retest 완주  [STATUS: in progress ~68%]

**동기**: B+A+C 픽스 효과 정량화 → paper §7 의 R0→R3 진화 데이터.

**Definition of Done**:
- [x] supplemental queue 1,285 건 생성 + driver 가동
- [ ] 1,285 건 모두 처리 (현재 ~877/1,285)
- [ ] R2 최종 리포트 (pass rate · 카테고리별 개선율 · 새 fail 패턴)
- [ ] R2 baseline.json 갱신 → R3 시작점 확정

**Next concrete step**: cron 이 매 2시간 진행. 외부 개입 불필요 — supervisor 자동 재시작.

**Files**: `results/retest/queue.tsv`, `results/retest/cursor.txt`, `results/retest/report.md`

---

### P3. R3 round retest  [STATUS: blocked on P2]

**동기**: P2 완료 후 잔존 fail 을 한 번 더 retest 해서 누적 개선 확인.

**Definition of Done**:
- [ ] P2 완료 대기
- [ ] 잔존 fail 추출 → 새 supplemental queue
- [ ] driver 재가동
- [ ] R3 최종 리포트
- [ ] paper §7 Figure 1 (R0→R1→R2→R3 evolution chart) 데이터 채움

**Next concrete step**: P2 완료 시 자동 트리거. 별도 액션 불필요.

---

### P4. Battle scenarios semantic verify 수기 작성  [STATUS: 0/192]

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

### P10. Skill 카탈로그 동적 확장  [STATUS: 33 baseline, 자동 보강 정책 등록]

**동기**: feedback_dynamic_skill_add.md 정책. retest fail 패턴에서 카테고리 부족 skill 발견 시 즉시 추가.

**Definition of Done**:
- [x] 18 → 33 1차 확장
- [ ] R2/R3 결과에서 새 fail 카테고리 발견 시 추가
- [ ] paper §3.5 의 "XX skills" 자동 갱신

**Next concrete step**: 매 retest 사이클 보고 시 신규 fail 패턴 모니터.

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
- [ ] **Phase 3 (사이트별 hard mode)**: 추가 chain 깊이 + auth bypass 강화 + cyber range task 1종/사이트
- [ ] **Phase 4**: Bastion-Bench web-vuln 카테고리 task 분포 (사이트당 5~10 task)

**Next**: Phase 3 — 우선순위 NeoBank hard (금융 race chain), AdminConsole hard (RCE chain), AICompanion hard (LLM jailbreak chain).

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


## Closed (이번 세션 완료)

- [x] verify.semantic 5,500 step 수기 작성 (40 과목)
- [x] Course 교안 전수 감사 (300/300 lecture.md)
- [x] derestricted course-based routing
- [x] A·B·C 일괄 픽스 (suffix · expect 보강 · 모델 swap)
- [x] L4 History layer 구현 + 통합 + UI
- [x] Skill 18 → 33 확장
- [x] Battle solo + admin Battles 탭
- [x] PE-KG-H 4계층 메모리 paper 정렬
- [x] docs/changelog-2026-04.md 정리

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
