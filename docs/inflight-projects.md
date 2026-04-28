# In-flight Projects Tracker

> **새 세션은 이 파일을 먼저 읽고 시작한다.** 미완 프로젝트의 단일 진실원.
>
> - 각 프로젝트: **Definition of Done (DoD) 체크리스트** + **Next concrete step** + **Status**
> - DoD 모두 체크 → `## Closed` 섹션으로 이동
> - cron 자동 사이클이 in-progress 중 next step 1건 진행 후 갱신·commit

업데이트: 2026-04-26

---

## In-Progress

### P1. Precinct 6 dataset 통합  [STATUS: 1억 dl 완료 + incidents 1000 임포트 (KG nodes 4902, anchors 14020)]

**동기**: WitFoo Precinct 6 (Apache 2.0, 1억 signal + MITRE + incidents + graph) 로
합성 데이터 한계 해결. paper §6 의 "real-world fidelity" 보강.

**실측 발견 (2026-04-26 20:00)**:
- 실제 dataset: `witfoo/precinct6-cybersecurity` (~1.3GB) + `-100m` (1억건 풀)
- **scaffold 가정과 schema 다름**: incidents.jsonl 은 nested host/cred 메타, edges.jsonl 의 attack_techniques 컬럼은 v1.0.0 샘플에서 모두 빈 `[]`
- **실 신호** = `label_binary` + `mo_name` + `suspicion_score` + `lifecycle_stage` (160k malicious, 90k suspicion≥0.6, mo_name "Data Theft" 99.99%)
- 해결: `_MO_TO_MITRE` 수동 매핑 (Data Theft→T1041, Phishing→T1566, ...) 으로 MITRE technique 도출

**Definition of Done**:
- [x] `scripts/import_precinct6.py` 스캐폴드 + sample dry-run (5 incidents)
- [x] HistoryLayer/KG/MITRE 임포트 함수 골격
- [x] **HF 실데이터 다운로드** — 1.3GB (incidents/nodes/edges/signals.parquet)
- [x] **실 schema 확인** — edges NDJSON labels 블록, signals parquet 27 컬럼 분포 측정
- [x] **real-edges 임포트 함수** — `import_real_edges()` + `--real-edges` CLI 플래그
- [x] **첫 실데이터 임포트 검증** — 200 edges → 205 breach_record + 196 ioc + T1041 Concept 노드, history_anchors 5→401
- [x] **5000 edges 본격 임포트** — breach_record +4800 + IoC +3167 (누적 anchors 약 8000+, Asset KG 노드 ~3000+)
- [x] **signals.parquet 통계 채널** — 2.07M signals 스캔, mo_name×lifecycle 분포 (Data Theft+complete-mission 125k 압도적), message_type 분포 (security_audit 38만 / firewall_action 12만), Concept 노드 2개 (`concept:p6:Data Theft:complete-mission` 등)
- [x] **format adapter 보강 — incidents.jsonl 채널** (`import_real_incidents`): 1000 incidents → Asset +3221 / breach_pair anchor +5652 / Compliance Concept (csc/cmmc/csf/iso27001/nist80053/pci) +11 / Security Product Concept +5 (ASA/PAN/Precinct/Azure/Stealthwatch). Red(Exploiting Host) ↔ Blue(Exploiting Target) 쌍 명시.
- [!] **1억 풀 데이터 진단**: edges 메타가 1.3GB sample 보다 빈약 (label_binary + suspicion 만, mo_name/lifecycle 모두 없음). 풍부 메타는 `incidents.jsonl` (10442개) 에 집중. mo_name 다양성은 dataset 구조적 한계 (Data Theft 99.99%) — RAG 가 message_sanitized 컬럼 임베딩으로 보완 필요.
- [ ] **Top-N hot pattern (1만) RAG POC** — bge-base 임베딩 + Faiss IVF, GPU 1분
- [ ] dedup + 카테고리 sample (100만) 본격 운용 — **현재 1억건 풀 dl 백그라운드 진행 중** (`witfoo/precinct6-cybersecurity-100m` 68 files, snapshot_download max_workers=4)
- [x] `scripts/precinct6_aggregate.py` — top-N hot IoC 자동 anchor (전략 D) ✅. 1M edges 스캔 → 9482 unique → top 1000 hot_ioc anchor (anchors 14020 → 15020). 빈도 1위: 280k 회 (IP-6CRED-* sanitized alias).
- [x] **`scripts/precinct6_export_seed.py` — 배포용 seed bundle 생성** ✅: dist/precinct6-seed-vYYYY.MM/ 산출 (anchors 10657 + 3363 + concepts 48 → tar.gz **215KB / 0.2MB**). manifest + README 자동. 폐쇄망 고객사 배포 준비 완료.
- [x] `scripts/import_seed_bundle.py` — 배포처 import 명령 ✅. dry-run 검증: 14020 anchors + 48 concepts 모두 인식. dedup (is_anchored / try-except) 으로 안전 append.
- [x] paper §7.7 신설 — Real-world Dataset 통합 (Precinct 6) ✅. Table 6 통합 결과 정량 + 단조성 한계 명시 + 유의미한 효과 3 가지.

**4 활용처 (★ 사용자 지시 2026-04-26 21:10)**:
- [x] **Phase A — 교안 case study 자동 주입** (`scripts/inject_lecture_cases.py`): course5-soc 15주 pilot 적용 완료. 한계: 모든 week 가 동일 T1041 case 2개만 (mo_name 다양성 부족) — RAG POC 후 week별 키워드 매칭으로 다양화 필요. 19 코스 × 15주 확장 대기.
- [x] **Phase B — lab 부록 markdown 자동 생성** (`scripts/inject_lab_cases.py`): 20 lab course 디렉토리에 `precinct6_cases.md` 생성. lab YAML 무수정 (verify 무결성 보호). technique 매칭 case + Red↔Blue pair anchor 동시 노출.
- [ ] **Phase C — cyber range traffic replay** (`scripts/precinct6_replay.py`): sanitized signals.parquet → PCAP → tcpreplay → web/siem 에 real alert 분포 발생.
- [x] **Phase D — battle scenario 신규** (`contents/battle-scenarios/precinct6-data-theft.yaml`): 10 missions (Red 5 + Blue 5). Precinct 10442 incident 의 가장 빈번 패턴 (mo_name=Data Theft, lifecycle=complete-mission, T1041) 재현. SQLi → lateral → staging → C2 → exfil vs baseline → anomaly → staging detect → containment → forensic evidence. semantic verify 4-축 모두 작성.
- [ ] Phase D 추가: 다른 mo_name (Phishing 등) 기반 시나리오 1-2개 더 (dataset 한계로 다양성 빈약).

**제약 발견**: dataset v1.0.0 의 mo_name 분포가 빈약 (Data Theft 99.99%) — 100만 확장해도 새 MITRE technique 안 늘어남. 의미있는 다양성 위해 **`-100m` 풀 데이터셋** 필요할 수 있음 (1억건, 수십GB).

**Next concrete step**: incidents.jsonl 의 nested host/cred 메타에서 Asset 풍부화 추가 (지금 IoC 만 IP 단위, host 단위 grouping 필요).

**Files**: `scripts/import_precinct6.py`, `docs/changelog-2026-04.md` §B4

---

### P2. R2 round retest 완주  [STATUS: ✅ COMPLETE → moved to Closed]

→ Closed 섹션 참조.

---

### P3. R3 round retest  [STATUS: in progress (cursor 286/575, secu VM 복구 후 supplemental 예정)]

**2026-04-27 secu 복구**: 사용자 보고 — R3 진행 중 secu VM (10.20.30.1) 다운 →
복구 완료. driver 가 그 시점 step 들을 fail/no_execution 처리했을 가능성.
secu 의존 과목 (secops/soc/soc-adv/agent-ir/agent-ir-adv 일부) 의 최근 fail
은 인프라 원인일 수 있음. **R3 main queue 완료 후 secu 의존 step
supplemental retest 필요**.



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

### P4. Battle scenarios semantic verify 수기 작성  [STATUS: ★ ✅ COMPLETE 192/192 (15/15 시나리오) → moved to Closed]

→ 모든 15 시나리오 192 미션 완료. Closed 섹션 참조.

**동기**: battle-scenarios YAML 의 verify 가 keyword only. semantic-first judge 가 작동하려면 수기 작성 필수.

**Definition of Done**:
- [ ] 15 시나리오 × 평균 13 mission = 192 미션
- [ ] 시나리오당 1 commit (15 commits)
- [ ] 한 사이클에 1~2 시나리오만 (스크립트/템플릿 금지)
- [ ] paper §7 Battle scenarios 결과 reflect

**Next concrete step**: `contents/battle-scenarios/apt-phase1.yaml` 부터 미션별 instruction+hint+target_vm 읽고 4-요소 (intent/success_criteria/acceptable_methods/negative_signs) 작성.

**Files**: `contents/battle-scenarios/*.yaml`

---

### P5. Bastion-Bench 590 hold-out task 작성  [STATUS: **101/590** ★ — 24 카테고리 + h004 19 + h005 5 + h005 5 (pentest/web-vuln/IR/ai-safety/soc-ops 신규 추가 2026-04-28)]

**야간 long run 진행 (2026-04-26 22:00~04:00 KST)**:
- 시작: 28/590 (10 카테고리)
- 현재: 71/590 (23 카테고리)
- ★ 23/23 모두 h001+h002+h003 완비 (pentest/web-vuln 은 h004 추가)
- 신규 카테고리 13: cloud-security, forensics, threat-hunting, ot-security, mobile-security, privacy-engineering, crypto-key-management, zero-trust, redteam-ops, social-engineering, api-security, siem-engineering, email-security
- 야간 cycle 평균 5분 / commit + push 별

- [x] 5 신규 카테고리 task 작성 (web-vuln/compliance/ai-ir/ai-utilization/ai-pentest)
- [x] 10/10 카테고리 모두 ≥1 pilot task 보유
- [ ] 채점 파이프라인 실 검증 — Bastion 으로 10 task 실행 + judge 정확도 측정
- [ ] 본격 작성 (카테고리당 평균 59 task = 590 - 10 = 580 잔여)
- [ ] paper §6.2 결과 반영

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

### P6. 외부 벤치마크 실측  [STATUS: Cybench adapter 작성, 다른 5 벤치 어댑터 대기]

- [x] `benchmarks/cybench_adapter.py` (commit 5acf78a) — task YAML → /chat → docker exec → subtask 매칭
- [x] `benchmarks/nyu_ctf_adapter.py` (commit 7af43ab) — 6 도메인 차별 prompt + Cybench 함수 재사용
- [x] `benchmarks/intercode_adapter.py` — 멀티턴 강조 + checkpoint hint 동적 노출 + python interpreter
- [x] `benchmarks/cybersec_eval_adapter.py` — 1000+ prompt MC, classify_response (refuse/answer/classify) + safety_breach/safe_refuse/false_refusal 메트릭
- [x] `benchmarks/harmbench_adapter.py` — 100 cyber subset, ASR (Attack Success Rate) + 6 attack types (direct/dan/pair/gcg/roleplay/encoding) + partial_breach 분류
- [x] `benchmarks/agentbench_os_adapter.py` — 60 OS task subset, 8 카테고리 + ReAct (Thought/Action/Observation) + verification_cmd oracle 채점

**P6 100% 완성** — 6/6 외부 벤치 adapter (Cybench / NYU CTF / InterCode / CyberSecEval / HarmBench / AgentBench OS). 다음 단계: 실 측정 (외부 데이터셋 다운로드 후).
- [ ] cybersec_eval_adapter.py (1000 prompt MC)
- [ ] harmbench_adapter.py (cyber subset)
- [ ] agentbench_os_adapter.py (60 task)
- [ ] 실 측정 — Cybench 40 task 부터

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
- [x] **3차 수정 (commit 071a471 + bastion fc44b22, 2026-04-26 18:55)**: attack-mode probe 가드레일 추가 — recon vs exploit 분리. R3 fail 패턴 분석 결과 attack-ai/attack-adv-ai 모든 fail 이 probe_all/probe_host 잘못 선택 (NFS LPE/WAF SQLi/Suricata 분석/nmap 시그니처 등 익스플로잇 prompt). 휴리스틱에 7개 attack 키워드→shell/qa 매핑 + ★ probe_all/probe_host 익스플로잇·페이로드·분석 호출 금지 명시. ⚠️ 원격 bastion 재시작은 ssh key 미인식으로 수동 필요.
- [x] **R3 자동 사이클 측정 5축 1차 정량 (2026-04-27 cursor 48/575 기준)**:
  - 거부율 = **0** ✓ (R2:6 → R3:0, 목표 0 달성, attack_mode preamble 효과)
  - unique skill = **11** ⚠️ (R2:9 → R3:11, 목표 15+ 미달. dormant `cve_lookup`/`wazuh_api` 첫 활성화 ✓)
  - first_turn_retry 발동 = **0** (소프트 prompt + minimal example 시점 이후 발동 안 함)
  - 과목별 본 큐 처리: soc-ai 30 / soc-adv-ai 9 / compliance-ai 2 (총 41건, infra-blocked 686 분리 후)
  - Asset 노드 = **4815** ✅ (P1 Precinct6 임포트 효과, baseline 11 → +4804)
- [x] paper §3.5 의 "33 skills" → "33 catalog · 15 active" R3 측정 정량 반영 (2026-04-27, R3 cursor 469/575 81.6% 시점, 신규 활성 6: cve_lookup/wazuh_api/garak_probe/prompt_fuzz/memory_dump/deploy_rule, 6/9 카테고리 활성)

**Next concrete step**: R3 종료 시 active 카운트 18+ 확인 (history_anchor / forensic_collect / model_isolate 추가 활성 후보). 효과 검증 시 P10 closed 후보.

---

---

### P12. 자율 공방전 (Autonomous Multi-team Battle)  [STATUS: Phase 1 + end-game 완료]

- [x] Phase 1 MVP (battle_participants/claims schema + 7 endpoints + UI)
- [x] **end-game** — `/auto/finalize` endpoint + UI modal (winner/MVP/timeline)
- [ ] (옵션) replay viewer / 영상 export

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

### P15. 외부 지식 채널 + 9-tier KG 운영  [STATUS: 7 source, bastion runtime 응답 없음]

**✅ 2026-04-27 18:30경 복구**: bastion runtime 재시작 완료.
- 원인 1: sync_to_bastion 가 /opt/bastion/api.py 미동기화 (rsync target 경로 누락)
- 원인 2: /opt/bastion/data/bastion_graph.db (빈 db) vs /home/ccc/ccc/data/bastion_graph.db (정상)
- 해결: `BASTION_GRAPH_DB=/home/ccc/ccc/data/bastion_graph.db` env + scp 변환된 api.py
- CIS Controls 18 재실행 완료 (added=18). /knowledge/concept POST smoke OK.
- 7 source / 2,468 anchor / Concept 20 (test 1 추가)

**TODO sync_to_bastion.sh 보강** — /opt/bastion 경로 빠짐. 원격 자동 재시작 시
BASTION_GRAPH_DB env 도 잡아야 함.



**동기**: 사용자 지적 (2026-04-27) — KG 가 *내부 작업* (playbook/experience) 만.
외부 지식 채널 + 9-tier (Mission/Vision/Goal/Strategy/KPI/Plan/Todo/Asset/
Architecture) 모두 비어있음.

**진행**:
- [x] **9-tier KG 풀 seed** (commit b71ad3e3 → 20c5d90e, 8 commits):
  - Mission 35 / Vision 25 / Goal 54 / Strategy 21 / KPI 62 / Plan 33 / Todo 34
  - 20 과목 + 5 도메인 + 8 외부 표준 + 12 Architecture + 12 운영 P#
  - bastion runtime REST API (`scripts/seed_9tier_kg.py` BASTION_URL 모드)

- [x] **case_study +5건 보강** (commit 164aed43): 누적 25건
  - compliance NIST/GDPR + secops Wazuh AR + soc 악성코드/자동화 + web-vuln 자동화

- [x] **외부 지식 5 source 활성** (P15 핵심):
  - CISA KEV 1583 anchor (commit a24b3b8c) — `ingest_cisa_kev.py --via-bastion`
  - MITRE ATT&CK 691 anchor (commit 3874de8e) — `ingest_mitre_attck.py`
  - OWASP Top 10 (Web/API/LLM) 30 anchor (commit bcb3334f) — `ingest_owasp_top10.py`
  - NIST CSF 2.0 28 anchor (commit 7a98310c) — `ingest_nist_csf.py`
  - CWE Top 25 25 anchor (commit 397c3a3a) — `ingest_cwe_top25.py`
  - **누적 2357 외부 지식 anchor** (전부 bastion runtime KG)

**Definition of Done**:
- [x] 9-tier 풀 seed (20 과목 + 외부 + Architecture + 운영)
- [x] 외부 지식 5 source 첫 backfill
- [x] case_study 보강 (25건)
- [x] ISO 27001 Annex A 93 통제 ingest 완료 (2026-04-27, 93 anchor 추가, kind=iso27001_annex_a)
- [x] NVD CVE 일일 갱신 cron 설정 (2026-04-27, ingest_nvd_cve_daily.py + crontab 06:00 KST, 30 CVE 첫 ingest 완료)
- [x] bastion api 에 /knowledge/concept POST endpoint 추가 (apps/bastion/api.py:379, ConceptBody 으로 idempotent 등록)
- [x] paper §7.8 외부 지식 채널 단락 (Table 7 + 6 source 누적 2,450 anchor)

**Files**: `scripts/seed_9tier_kg.py`, `scripts/ingest_cisa_kev.py`,
         `scripts/ingest_mitre_attck.py`, `scripts/ingest_owasp_top10.py`,
         `scripts/ingest_nist_csf.py`, `scripts/ingest_cwe_top25.py`

### **다음 외부 지식 채널 후보 — Anthropic-Cybersecurity-Skills (mukul975)**

저장: 2026-04-27 — 사용자 지시로 다음 차수 작업으로 보류.

**대상 repo**: https://github.com/mukul975/Anthropic-Cybersecurity-Skills (Apache 2.0)
- 754 SKILL.md (YAML frontmatter + workflow)
- 26 보안 도메인 (cloud 60 / threat-hunting 55 / threat-intel 50 / web-app 42 / network 40 / malware 39 / forensics 37 / SOC ops 36 / IAM 35 / SOC 33 / container 30 / ICS 28 / API 28 / vuln-mgmt 25 / IR 25 / red-team 24 / pentest 23 / endpoint 17 / DevSecOps 17 / phishing-defense 16 / crypto 14 / zero-trust 13 / mobile 12 / ransomware 7 / compliance 5 / deception 2)
- 5 framework 매핑 (MITRE ATT&CK v18 + NIST CSF 2.0 + ATLAS v5.4 + D3FEND v1.3 + NIST AI RMF 1.0)

**적용 검토 결론** (2026-04-27 분석):

두 시스템 *경쟁 아니라 보완*:
- mukul975 754 = 지식/플레이북 가이드 (descriptive)
- Bastion 33 = 실행 단위 (executable via SubAgent A2A)

**Phase A (0.5d, low effort)**: KG anchor 임포트
- `scripts/ingest_cybsec_skills.py` 추가 — 기존 7 ingester 패턴
- 754 SKILL.md → kind=cybsec_skill anchor
- MITRE/NIST ID 를 related_ids 로 → 기존 anchor 자동 cross-link

**Phase B (1d, medium)**: Bastion 33 ↔ 754 매핑 표
- `data/bastion/skill_to_cybsec_map.json`
- LLM plan 시 Bastion skill + 대응 SKILL.md workflow 동시 prompt

**Phase C (3~5d, high)**: selective playbook 변환
- top 50 SKILL.md → Bastion `playbook.yaml` (수기 검증)
- digital-forensics 37 + IR 25 + threat-hunting 55 우선

**주의**:
- 754 모두 *Bastion 운영 검증* 된 것 아님 — Phase A 는 지식 참조만
- D3FEND / NIST AI RMF 매핑은 현재 Bastion 미보유 차원 → Knowledge UI 확장 필요
- submodule + 정기 sync 권장 (upstream v1.2 → 미래 update)
- NOTICE 파일에 mukul975 license 명시 (현재 미보유)

**즉시 가능한 첫 step**: Phase A PoC — deception 2 + compliance 5 = 7건 시범 임포트 후 26 도메인 확장.

**완료 (2026-04-27)**: `scripts/ingest_cybsec_skills.py` 작성 + **Phase A → Phase B 풀 임포트 완료** — 26 도메인 **754 skills** 모두 anchor (kind=cybsec_skill, errors=0). related_ids 에 NIST CSF / MITRE ATT&CK / ATLAS / D3FEND IDs 자동 cross-link.

---

### P14. Lab 채점 흐름 재설계 (textarea → SubAgent 감시)  [STATUS: A/D/B/C 완료, 1 lab 실측만 잔여]

**동기**: 학생이 textarea 에 답변 작성 → judge 채점 = "글로 다시 쓰는" 부담.
실제 *행위* (명령 실행) 기반 채점이 진짜 학습 가까움. 사용자 지시 (2026-04-27).

**4 사이클 (D→B→C 순서, 흐지부지 금지)**:

- [x] **A. DB schema + API + input_mode 추론** (commit be3a5d89)
  - `lab_sessions` 테이블 + 3 index
  - 4 endpoint: start / end / get / list
  - 두 모드 동시 채점: transcript (commands) + answers (text per step)
  - `_step_input_mode()` 자동 분류
  - `step.input_mode` hint 를 lab catalog 응답에 포함

- [x] **D. UI 완성** ✅ (Labs.tsx 통합 완료, 2026-04-27)
  - [x] Labs.tsx — [Lab 시작] / [Lab 완료] 버튼 + retrySession
  - [x] step 별: instruction + 학습포인트 + textarea + transcript paste
  - [x] 세션 활성 표시 (T0 부터 경과 시간 fmtElapsed)
  - [x] 결과 카드: step별 ✓/✗ + input_mode + graded_via + reason
  - [x] 재시도 버튼 (새 session)
  - [x] 기존 textarea 흐름 fallback 유지
  - [x] **input_mode badge** (cycle 추가): step 헤더에 ⌨ transcript / ✎ text hint, 학생이 무엇을 입력할지 즉시 인지

- [ ] **B. SubAgent transcript 자동 캡처**
  - apps/subagent-runtime 에 `/audit/start` / `/audit/stop` 추가
  - 캡처 방법: web shell (xterm.js + ws) 또는 script(1)
  - DB lab_sessions.transcript 자동 채움
  - paste 모드 fallback 유지

- [x] **C. Manager AI grading prompt** (commit pending)
  - manager-api 우회 — ccc 안 lab_engine.semantic_judge.multi_step_judge() 신규
  - 1회 LLM 호출로 모든 step 채점 (Ollama gpt-oss:120b, 4000 num_predict)
  - 출력: step_results [{order, passed, reason, feedback, graded_via}] + overall_feedback
  - ccc-api sessions/end: multi_step 우선 → 실패 시 step별 fallback
  - UI: 종합 피드백 박스 + step별 reason+feedback 노출

**Definition of Done**:
- [x] A 사이클 commit + push (be3a5d89)
- [x] D UI 완성 (df7ef14b)
- [x] B SubAgent capture (acd0b005 + opsclaw b63cffa)
- [x] C Manager 채점 prompt (commit pending)
- [ ] 1 lab 학생 직접 실측 (사용자 검증 필요)
- [ ] A vs C 결과 비교 측정
- [ ] 기존 textarea 흐름 deprecated 표시
- [ ] paper §3.5 업데이트

**Next concrete step**: D 사이클 — Labs.tsx 의 lab 보기 모드 전면 개편.

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
- [x] paper §4.2 노드/엣지 표에 Architecture + 9-tier work nodes (Mission/Vision/Goal/Strategy/KPI/Plan/Todo) + 4 신규 엣지 (connects_to/data_flows_to/manages/derives_from/realizes/measures/contributes_to) 추가 (2026-04-27)

**Next**: 옵션 항목은 운영 시작 후 필요시. seed 데이터 (mission/vision/goal/strategy/kpi 1세트) production 배포 시 1회 등록.


## Closed (누적 완료)

### 2026-04-27 — 사용자 지적 3 갭 + P14·P15
- [x] **사용자 지적 #1 갭** — KG 9-tier 풀 seed (28 Mission + 27 Vision + 60 Goal +
      30 Strategy + 68 KPI + 33 Plan + 34 Todo + 12 Architecture).
      `scripts/seed_9tier_kg.py` BASTION_URL 모드.
- [x] **사용자 지적 #1 외부 지식** — P15 6 source 활성: KEV 1583 + MITRE 691 +
      OWASP 30 + NIST CSF 28 + CWE 25 + ISO 27001 93 = 2,450 anchor.
      6 ingest_*.py 스크립트.
- [x] **사용자 지적 #2 1억건 활용** — case_study 25건 (Precinct 6 anchor 5종 +
      Data Theft 패턴). lecture-lab cross 매핑.
- [x] **사용자 지적 #3 정합성** — D-B 매핑 20/20 과목 + cross-course (curriculum/
      `*-mapping.yaml`) + Cyber Range startswith 버그 fix.
- [x] **P14 Lab 채점 흐름 A/D/B/C** — DB schema + UI + SubAgent /a2a/audit/* +
      multi_step_judge. 1 lab 학생 실측만 잔여.
- [x] **bastion api /knowledge/concept POST** — 외부 지식 Concept 등록 endpoint
      (anchor 외 graph 핵심 객체).
- [x] **옵션 B Lab/Cyber Range 학생 노출 풍부화** — intent + success_criteria +
      primary_method + negative_signs UI 박스.

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

### 2026-04-26 후반 (R2→R3 전환 + 5건 일괄 개선 + P4 100% 완수)
- [x] **★ P4 Battle scenarios verify.semantic ✅ COMPLETE 192/192 (15/15 시나리오)** — sqli/xss/apt-phase1/IR/apt-phase2/recon/exfil/privesc/dos/lateral/webshell/bruteforce/apt-phase3/championship/purple-team. MITRE ATT&CK + OWASP + NIST IR 4축 (intent/criteria/methods/negative_signs) 정성 작성.
- [x] P5 Bastion-Bench 19/590 — 10/10 카테고리 second task (h001 + h002) 작성 완료
- [x] P6 외부 벤치 6/6 adapter 완성 (Cybench/NYU CTF/InterCode/CyberSecEval/HarmBench/AgentBench OS)

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
