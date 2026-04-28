# CCC — Cyber Combat Commander

> **단일 GPU 폐쇄망에서 운용 가능한 사이버보안 LLM 에이전트 + 교육·대전 플랫폼**
>
> 핵심: **Bastion** — Master·Manager·SubAgent 3계층 + LangGraph 8단계 lifecycle +
> **(Playbook + Experience + History) → Knowledge Graph** 통합 메모리 + Asset/Work
> 9-tier 도메인. DGX-Spark 1대 + `gpt-oss:120b` 만으로 종단 간 운용.
>
> **3,089 step 실증** R0 47.8% → **R2 완료 64% / R3 진행 중 (1,261 잔여 비-pass 재테스트, 9.5% 진행)** · 30일 production trial 치명적 운영 오류 0건 (R3 진행).

---

## TL;DR — 4가지 핵심 기여

1. **폐쇄망 운영성** — DGX-Spark 1대 위 오픈 가중치 모델로 외부 클라우드 의존 0건. Master·Manager·SubAgent 3계층 + LangGraph 8단계 state machine + 5-endpoint A2A 프로토콜 + 해시 체인 감사.
2. **운영 신뢰성·안정성** — LLM 의 본질적 비결정성·과잉 창의성을 결정적 상태 기계 + skill 위험도 게이트 + KG reuse/adapt/new 결정으로 구조적 억제. step 분산 대폭 감소.
3. **장기 컨텍스트 보존** — (Playbook + Experience + History) → KG 의 3-source 통합 메모리. anchor 면역 압축으로 5년+ 운영 컨텍스트 유실 원천 차단.
4. **다양한 실증** — 17 카테고리 3,089 step 개발 corpus + 590 hold-out task (Bastion-Bench) + 6 외부 벤치 (Cybench/CyberSecEval/NYU CTF/InterCode/HarmBench/AgentBench OS) + 30일 production trial.

상세: [`docs/changelog-2026-04.md`](docs/changelog-2026-04.md), [`docs/inflight-projects.md`](docs/inflight-projects.md), [`contents/papers/bastion/paper-draft.md`](contents/papers/bastion/paper-draft.md) (로컬 전용).

---

## Quick Start

```bash
# 1. 설치 (시스템 패키지 + Python + Node.js + Docker + PostgreSQL)
bash setup.sh

# 2. 실행
./dev.sh api          # http://<IP>:9100/app/  (관리자 admin/admin1234)
./dev.sh bastion      # http://<IP>:8003       (Bastion 에이전트 단독)

# 3. 업그레이드
bash upgrade.sh

# 4. Docker 독립 배포
docker compose -f docker/docker-compose.yaml up -d
```

---

## 시스템 아키텍처

```
                        Master (off-net authoring)
                               │   playbook · 평가 task · 정책
                               ▼
   ┌─────────────────────────────────────────────────────┐
   │              Manager  (gpt-oss:120b)                │
   │  자연어 → 플래닝 → skill 디스패치 → 결과 분석           │
   │  ── LangGraph 8단계 lifecycle ──                      │
   │  intake → plan → select_assets → resolve_targets    │
   │       → [approval_gate] → execute → validate        │
   │       → report → close                              │
   └────────────┬─────────────────────┬──────────────────┘
                │ A2A 프로토콜 (5 endpoint) │
   ┌────────────┴──┐ ┌──────────────┐ ┌─┴───────┐ ┌─────────┐
   │ SubAgent secu │ │ SubAgent web │ │ siem    │ │ attacker│
   │ (gemma3:4b)   │ │              │ │         │ │         │
   └───────────────┘ └──────────────┘ └─────────┘ └─────────┘
                          │ run_script · invoke_llm · install_tool
                          │ analyze · mission (자율 red/blue)
                          ▼
                   학생/SOC 인프라 (5 VM 표준)
```

### 메모리 — (Asset+Architecture) × (Work) → Knowledge Graph

```
┌────────────────────────────────────────────────────────────────┐
│                  Knowledge Graph (통합 layer)                    │
└──────────────┬──────────────────────────┬──────────────────────┘
               │                          │
       ┌───────┴────────┐         ┌───────┴────────┐
       │  ASSET DOMAIN  │         │  WORK DOMAIN   │
       └───────┬────────┘         └───────┬────────┘
   ┌───────────┴───────────┐    ┌──────────┴──────────────┐
   │ Asset · Architecture   │    │ Strategic (영구)         │
   │  (host/app/model/      │    │  Mission · Vision        │
   │   topology/flow)       │    │  Goal · Strategy · KPI   │
   └────────────────────────┘    ├──────────────────────────┤
                                  │ Tactical (분기·월)        │
                                  │  Plan · Todo             │
                                  ├──────────────────────────┤
                                  │ Operational (PE-KG-H)    │
                                  │  Playbook · Experience   │
                                  │  History (Event ·        │
                                  │  Narrative · Anchor)     │
                                  └──────────────────────────┘
```

**3-source 통합**: Playbook (정적·자동승격) + Experience (per-task ReAct trace) + History (시계열·내러티브·압축 면역 anchor·자산 changelog) → KG. Manager 가 매 작업마다 **reuse / adapt / new** 결정.

---

## Bastion — 보안 운영 AI 에이전트

### Skill (33종)

| 카테고리 | Skill |
|---|---|
| **점검·정찰** | probe_host · probe_all · scan_ports · dns_recon · cve_lookup |
| **보안시스템 운영** | check_suricata · check_wazuh · check_modsecurity · configure_nftables · deploy_rule · enroll_wazuh_agent · wazuh_api · docker_manage |
| **분석** | analyze_logs · file_manage · http_request · shell |
| **공격** | web_scan · attack_simulate · password_attack ⚠️ |
| **AI 보안** | ollama_query · prompt_fuzz · garak_probe · model_isolate ⚠️ · rag_corpus_check |
| **IR (침해 대응)** | memory_dump ⚠️ · process_kill ⚠️⚠️ · forensic_collect ⚠️ · ioc_export (STIX 2.1) |
| **컴플라이언스** | compliance_scan · secret_scan |
| **History** | history_anchor · history_narrative |

⚠️ = `danger`, ⚠️⚠️ = `danger-danger` (HITL 승인 강제)

### Playbook + Experience 자동 승격
정적 8 + 동적 (Experience compaction → auto-promote) 누적 200+. Knowledge Graph 위 *reuse / adapt / new* 2-stage 결정으로 반복 작업 일관성 + 신규 작업 적응성 동시 달성.

### LLM 라우팅

| 컨텍스트 | 모델 | 비고 |
|---|---|---|
| Manager (기본) | `gpt-oss:120b` | 정렬된 safety, 방어/SOC/분석 적합 |
| Manager (공격·대전) | `gurubot/gpt-oss-derestricted:120b` | 동일 사이즈, course allowlist 기반 per-request 자동 스왑 |
| SubAgent | `gemma3:4b` | 호스트별 경량 executor |
| 실습용 취약 모델 | `ccc-vulnerable:4b` · `ccc-unsafe:2b` | AI 보안 실습 타겟 |

### Verification — Semantic-first
모든 step 의 `verify.semantic` 메타 (`intent` + `success_criteria` 3+ + `acceptable_methods` 3-4 + `negative_signs` 3) 를 LLM judge 가 우선 적용, 키워드는 폴백. 약 5,500 step 수기 작성. 자체 검증 (self-verify) 루프.

---

## 교육 + 대전 플랫폼

### 교과목 (20개 × 15주 = 300주, 600 lab)

| 그룹 | 과목 (요약) |
|---|---|
| **공격** | 사이버 공격 기초·심화 / 웹 취약점 |
| **방어 운영** | 보안 솔루션 운영 / 컴플라이언스 / SOC 기초·심화 / 클라우드/컨테이너 |
| **AI 보안** | AI/LLM 보안 / AI Safety 기초·심화 / AI 에이전트 보안 / 자율 보안 / 자율 시스템 / IoT |
| **실전** | 공방전 기초·심화 / 물리 보안/모의해킹 |
| **AI 침해대응** | 에이전트 침해대응 / 침해대응 심화 |

각 과목 15주 × Markdown 교안 + Non-AI/AI 실습 YAML (자동 채점).

### Battle (공방전) — 1v1 + Solo + 자율 다팀
- 시나리오 15종 (APT 3단계 / 침해 대응 / SQLi vs WAF / Lateral vs Segmentation 등)
  + 미션별 `verify.semantic` 4축 (intent / success_criteria / acceptable_methods / negative_signs) — 23/192 수기
- **Solo 모드**: 1명이 Red+Blue 동시 점유 (시점 토글)
- **자율 모드**: N팀 ffa-style, 자기 자산 방어하면서 타 팀 자산 공격
- **Admin 관리**: 강제 종료 · 삭제 · 이벤트 30건 상세

### Vuln-site 카탈로그 (P13) — 7 사이트 + 3 난이도
- **JuiceShop** (e-com, 50+ vuln) · **DVWA** (PHP 학습)
- **NeoBank** :3001 (금융, 30 vuln) · **GovPortal** :3002 (정부, 25) · **MediForum** :3003 (의료, 22)
- **AdminConsole** :3004 (DevOps, 28) · **AICompanion** :3005 (LLM 챗봇, 25 — OWASP LLM Top 10)
- 일괄 배포: `bash contents/vuln-sites/up.sh up` / 자동 검증: `... smoke` (10/10 PoC)
- Battle 생성 시 admin 이 site + difficulty 선택, 충분한 취약점으로 공방전 장기 지속

### CCCNet 블록체인
활동 자동 블록 (lab_complete · battle_win · rank_up). SHA256 chain.

---

## 실증 테스트 (논문 R0 → R3 4 라운드)

### 누적 결과 (R3 진행 중)

| Round | Pass / 3,089 | Pass율 | 누적 변화 | 핵심 변화 |
|---|---|---|---|---|
| R0 baseline | 1,476 | 47.8% | — | 키워드 매칭만 |
| R1 | 1,804 | **58.4%** | +328 (+22.2%) | verify.semantic **6,188 블록 수기** 도입 |
| R2 (B+A+C 픽스 완료) | 1,922 | **62.2%** | +118 | course routing + 실행 강제 suffix + expect 보강 + harmony format 폴백 |
| R3 (진행 중 9.5%) | 1,930+ | **62.5%+** | +N | **카테고리화 prompt + tools 필터 (33→top12, 19KB→7KB) + first_turn_retry + attack_mode lab-context preamble + driver v2 healthcheck** |

R3 새 코드 적용 후 (cursor 111+): `cve_lookup` 등 **dormant skill 활성화 첫 사례** 확인. ERROR cluster 자동 진단 (`scripts/r3_diagnose.py`).

### Fail 분류 5종

| 유형 | 원인 | 픽스 |
|---|---|---|
| A | markdown 설명만, skill 미실행 | bastion_prompt 실행 강제 suffix |
| B | aligned 모델 공격 거절 | course-based derestricted 라우팅 |
| C | 실행됐으나 verify keyword 미스 | tail 토큰 → expect 보강 |
| D | 빈 응답·타임아웃 | 인프라 안정화 |
| E | 카테고리 attack 인데 skill 미발동 | category-aware execution gate + harmony format 폴백 |

### Bastion-Bench (별도 hold-out, **590/590 ✅ 100% 완성** 2026-04-28)
**42 카테고리 × 평균 14 task** (h001~h025). 8 메트릭 (success rate · **reuse rate** · MTTC · hallucination rate · step efficiency · audit completeness · safety violation · self-correction). 각 task = 6 step + verify.semantic.

**평가 방식**:
- Knowledge eval (~85%): bastion agent 응답 텍스트를 verify.semantic 의 success_criteria 와 매칭. AWS console 안 가고 텍스트 채점 (paper §6.2 limitation 명시)
- Execution eval (~15%): target_vm: web/manager 의 일부 step 만 실 명령 실행

**카테고리 (42)**:
공격: pentest / web-vuln / redteam-ops / red-team-tactics / attack
방어: soc-ops / blue-team / siem-engineering / email-security / threat-hunting
인프라: cloud-security / cloud-native-security / container-security / network-security / iot-security / ot-security / wireless-security / firmware-security / mobile-security / automotive-security / telecom-security
거버넌스: compliance / governance / data-security / privacy-engineering / dlp / fraud-detection / financial-security / healthcare-security
AI: ai-safety / ai-pentest / ai-ir / ai-utilization
응급: incident-response / forensics
신뢰: zero-trust / api-security / supply-chain-security / application-security / crypto-key-management / social-engineering / devsecops / secops

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, LangGraph |
| Frontend | React 19, TypeScript, Vite, cytoscape (Knowledge UI) |
| Database | PostgreSQL 15 + SQLite (Knowledge Graph + History) |
| LLM | Ollama — gpt-oss:120b · gurubot/gpt-oss-derestricted:120b · gemma3:4b · ccc-vulnerable:4b · ccc-unsafe:2b |
| Fine-tuning | unsloth + PEFT QLoRA + bitsandbytes |
| Security Stack | nftables · Suricata · ModSecurity CRS · Wazuh · OpenCTI |
| Audit | SHA-256 hash chain (turn-level 결정적 재생) |
| Container | Docker, docker-compose |

---

## 파일 구조

```
apps/
  ccc_api/src/main.py     — 메인 API (battle/training/lab/admin/work·assets/...)
  ccc-ui/src/             — React UI (Knowledge graph + battle + admin)
  bastion/                — Bastion HTTP API (:8003)
  cli/                    — CLI 도구
packages/
  lab_engine/             — Lab 실행·검증 + semantic_judge
  battle_engine/          — 공방전 로직
  bastion/
    agent.py              — ReAct + harmony fallback + 자동 history event
    skills.py             — 33 skill 카탈로그
    history.py            — L4 History (Event/Narrative/Anchor/Changelog)
    asset_domain.py       — Asset + Architecture (P11)
    work_domain.py        — Mission/Vision/Goal/Strategy/KPI/Plan/Todo (P11)
    graph.py              — KG schema (16 노드 타입 + 28 엣지 타입)
    compaction.py         — Insight 압축 + anchor 면역 게이트
    lookup.py             — reuse/adapt/new 2-stage 결정
contents/
  education/              — 20 과목 × 15주 교안 (300/300 감사 완료)
  labs/                   — 20 과목 × 15주 × 2 (Non-AI/AI) lab YAML
  battle-scenarios/       — 15 시나리오
  playbooks/              — 정적 + 자동 승격
docs/
  changelog-2026-04.md    — 4월 세션 변경 이력 (24 항목)
  inflight-projects.md    — 미완 프로젝트 단일 추적기 (P1~P12)
  bastion-introduction.md — Bastion 소개
scripts/
  test_step.py            — 단일 step Bastion 호출 + verdict 판정
  retest_report.py        — 매 2h cron 보고 (KPI 자동 record)
  phase5_monitor.py       — Asset autoscan + KPI + IoC 매칭 모니터
  import_precinct6.py     — WitFoo Precinct 6 (1억 건) → KG/History 임포터
  sync_to_bastion.sh      — CCC packages.bastion → mrgrit/bastion 동기화
finetune/                 — QLoRA 데이터셋 + 스크립트
results/retest/           — retest 진행 상태 + report.md
```

---

## 관련 저장소

- **mrgrit/ccc** (이 저장소) — CCC 플랫폼 + Bastion 통합
- **mrgrit/bastion** — Bastion 에이전트 단독 배포 (CCC 의 packages.bastion 동기화)

---

## License

MIT
