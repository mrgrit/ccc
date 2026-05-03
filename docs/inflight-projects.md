# In-flight Projects Tracker

> **새 세션은 이 파일을 먼저 읽고 시작한다.** 미완 프로젝트의 단일 진실원.
>
> - 각 프로젝트: **Definition of Done (DoD) 체크리스트** + **Next concrete step** + **Status**
> - DoD 모두 체크 → `## Closed` 섹션으로 이동
> - cron 자동 사이클이 in-progress 중 next step 1건 진행 후 갱신·commit

업데이트: 2026-04-30 23:55 KST (R3 fix #2/#3 deploy)

---

## In-Progress

### P19. course1 attack acceptable_methods OSS 도구 보강 [STATUS: 진행 중]

**동기**: P18 (physical-pentest) 완료 후속. course1 attack 이 학생 첫 수강 과목 + 메모리 "multi_task 재작성 — attack 6" 일부 진행 중. 동일 패턴 (도구명 → 도구 + 명령 + 출력 + 해석) 으로 재작성.

**원칙** (P18 동일):
- 병렬/스크립트/템플릿/자동화 금지
- 매 주차 instruction/script 읽고 정성껏 수기
- 한 step 당 8~9개 도구 (nonai 8, ai 9)

**진행**:
- [x] week01 nonai (544→880줄, 16 step × 8~9 method, hint 도구 우선순위/설치/fallback 포함) — 정찰 기초
- [x] week01 ai (709→987줄, 16 step × 9 method, hint 보강, multi_task RoE+Phase A/B/C)
- [x] week02 nonai (480→777줄, 16 step × 9 method, hint 보강) — 포트스캐닝: -sT/-sS/-p-/-sV/-O/-sU/NSE/http-enum/-sA/-F/-oX/vuln/포트/Idle/보고서
- [x] week02 ai (709→1012줄, 16 step × 9 method, hint 보강, multi_task ATT&CK Recon)
- [x] week03 nonai (536→840줄, 16 step × 9 method, hint 보강) — 취약점 스캐닝: Nikto/searchsploit/SQLi/SSL/dirb/admin API/header/CVE 매트릭스
- [x] week03 ai (683→1022줄, 16 step × 9 method, hint 보강, multi_task HTTP+Nikto+CVE 매트릭스)
- [x] week04 nonai (596→915줄, 16 step × 9 method, hint 보강) — 웹 공격: SQLi auth/JWT/Reflected XSS/Mass/UNION/Stored XSS/Null Byte/검증우회/CSRF/IDOR/PUT/SVG XSS/헤더 인젝션/admin panel/OWASP report
- [x] week04 ai (799→1142줄, 16 step × 9 method, hint 보강, multi_task SQLi+UNION+Mass chain)
- [x] week05 nonai (16 step × 9 method, hint 보강) — 인증 공격: user enum/manual brute/hydra SSH/john MD5/보안질문/JWT none/hashcat SHA-256/JWT secret/ED25519/credstuff/shadow/NTLM/secq query/rate limit/auth report
- [x] week05 ai (16 step × 9 method, hint 보강, multi_task H1 Bug Bounty disclosure 90일)
- [x] week06 nonai (16 step × 8 method, hint 보강) — 네트워크 공격: tcpdump/-A/ARP/nmap MAC/ARP cap/DNS cap/scapy ICMP/scapy ARP/pcap save/traceroute/ss/SYN flood/nft 원격/scapy SYN/report/STRIDE
- [x] week06 ai (16 step × 9 method, hint 보강, multi_task STRIDE Threat Model 6 카테고리)
- [x] week07 nonai (16 step × 8 method, hint 보강) — 시스템 익스플로잇: searchsploit/msf search/msf auxiliary/nc listener/bash revshell/msfvenom ELF/uname/systemctl/curl error/python portscan/msf http_login/cron/SUID/msfvenom python b64/exploit report/CTF Discord walkthrough
- [x] week07 ai (16 step × 9 method, hint 보강, multi_task CTF 동아리 walkthrough+FAQ)
- [x] week08 nonai (16 step × 8 method, hint 보강) — 권한 상승: id/sudo -l/SUID/world-writable/passwd shells/cron/capabilities/shadow/env/PATH hijack/docker.sock/internal port/bash_history/LinPEAS oneliner/privesc report/Executive Briefing
- [x] week08 ai (16 step × 9 method, hint 보강, multi_task PenTest팀 시니어 5 슬라이드 발표 - 중간고사)
- [x] week09 nonai (16 step × 8 method, hint 보강) — 지속성: SSH keys/cron/systemd/.bashrc/hidden/PAM/LD_PRELOAD/UID 0/bind shell/web shell/at job/sshd_config/trojan binary/persistence hunt/report/Purple Team Adversary Sim
- [x] week09 ai (16 step × 9 method, hint 보강, multi_task Purple Team Operator Timeline + Coverage Matrix + AAR)
- [x] week10 nonai (16 step × 8 method, hint 보강) — 측면 이동: SSH -L/-D/원격nmap/sshpass재사용/-R/known_hosts/-J jump/grep cred/ip route/socat tunnel/원격 portscan/ARP/sshuttle VPN/IoC/lateral report/Adversary Emulation Slack
- [x] week10 ai (16 step × 9 method, hint 보강, multi_task Adversary Emulation 컨설턴트 Slack DM transcript)
- [ ] week11~15 nonai
- [ ] week11~15 ai

**구조 확정** (2단계 검증):
- answer / bastion_prompt = 추상 prompt (1차 검증: 학습자/AI 능력)
- hint = 도구 우선순위 + 설치 명령 + fallback list (2차 검증)
- acceptable_methods = 도구 + 명령 + 출력 + 해석 (검증 시 다양성)

**Next concrete step**: attack-nonai/week11.yaml + attack-ai/week11.yaml 보강.

**Files**: `contents/labs/attack-nonai/week*.yaml`, `contents/labs/attack-ai/week*.yaml`

---

### P18. course16-17 physical-pentest acceptable_methods OSS 도구 보강 [STATUS: ✅ COMPLETE — week05~15 전부 완료]

**동기**: 사용자 지시 (2026-05-03) — Cyber Range = UI /labs 메뉴 = `contents/labs/` 자체.
acceptable_methods 가 도구명만 적힌 상태 → "도구 + 구체 명령 + 예상 출력 + 해석" 수준으로 재작성.
verify.semantic 의 fail-safe 다양성 확보 + 학생 자료로 직접 활용 가능한 quality.

**원칙**:
- 병렬/스크립트/템플릿/자동화 금지 (사용자 명시)
- 매 주차 instruction/script 읽고 그 주제에 딱 맞게 정성껏 수기
- 한 step 당 8~9개 도구 (nonai 8, ai 9 — 마지막 1개는 Bastion AI orchestrator/KG 활용 항목)
- 각 도구: 정확한 실행 명령 + 실제 출력 예시 + 해석/맥락

**진행**:
- [x] week05 nonai (306→342줄, 9 step × 6~8 method)
- [x] week05 ai (501줄, AI workflow 통합)
- [x] week06 nonai (308→341줄, 8 step × 8~9 method) — WPA2 PMK/사전공격/AP스캔/인터페이스/Deauth/강도평가/감사/aircrack
- [x] week06 ai (399→523줄, 9 step × 9 method, multi_task 포함)
- [x] week07 nonai (308→342줄, 8 step × 8~9 method) — Evil Twin/ARP MITM/Captive Portal/IP forward/HTTP/HSTS/ARP detect/MITM defense
- [x] week07 ai (478→524줄, 9 step × 9 method, multi_task + Bastion KG anchor 통합)
- [x] week08 nonai (286→318줄, 8 step × 8 method) — 중간 평가: nmap/sshpass/USB HID/임플란트/Findings/secu enum/Exec Summary/network map
- [x] week08 ai (452→494줄, 9 step × 9 method, multi_task E2E kill chain + Bastion 자동 보고서)
- [x] week09 nonai (308→355줄, 8 step × 8 method) — RF/SDR: 고정 코드/롤링 코드/RollJam/Sub-GHz/IoT 스캔/Flipper/RF 감사/재밍 탐지
- [x] week09 ai (501→547줄, 9 step × 9 method, multi_task RF chain + Bastion KG anchor)
- [x] week10 nonai (332→363줄, 8 step × 8 method) — CCTV/접근 통제: RTSP/웹 관리/취약점/RTSP path/default cred/access audit/keyword grep/단계별 권고
- [x] week10 ai (456→565줄, 9 step × 9 method, multi_task CCTV chain + Bastion 자동 Jira 통합)
- [x] week11 nonai (335→367줄, 8 step × 8 method) — 감시 시스템 심화: RTSP auth/ONVIF/카메라 takeover/cred brute/CVE/UPnP/감사 보고서/VLAN 설계
- [x] week11 ai (522→595줄, 9 step × 9 method, multi_task IP camera chain + Bastion KG correlation)
- [x] week12 nonai (296→327줄, 8 step × 8 method) — OSINT/물리 정보: DNS reverse/HTTP banner/SSL cert/종합 recon/Shodan 분류/clean desk/OSINT 도구/OSINT 보고서
- [x] week12 ai (459→502줄, 9 step × 9 method, multi_task OSINT chain + Bastion 다중 framework 매핑)
- [x] week13 nonai (313→345줄, 8 step × 8 method) — 보고서 자동 생성: evidence/배너/SHA256/Findings/Python 보고서/exec brief/risk matrix/QA
- [x] week13 ai (510→564줄, 9 step × 9 method, multi_task report chain + Bastion 자동 PDF + GPG + IPFS)
- [x] week14 nonai (372→411줄, 8 step × 9 method) — 물리 방어: 방화벽/이상 탐지/보안 인식 퀴즈/보안 설정 검증/보안 정책/사고 대응/ROI/체크리스트
- [x] week14 ai (572→628줄, 9 step × 9~10 method, multi_task 방어 chain + Bastion 자동 정책 + Jira 통합)
- [x] week15 nonai (376→425줄, 10 step × 9 method) — 종합 평가: 정찰/SSH/USB HID/임플란트/방어/보고서/Exec brief/역량 자가 진단/Next steps/최종 체크
- [x] week15 ai (655→676줄, 11 step × 9 method, multi_task E2E + Bastion R5 round 완료 anchor)

**최종 결과**: week05~15 (11 주차) × 2 (nonai+ai) = 22 yaml 보강 완료.
nonai: 평균 360줄, 8 step × 8~9 method.
ai: 평균 555줄, 9~11 step × 9 method, Bastion AI orchestrator + KG anchor 통합.

**Files**: `contents/labs/physical-pentest-nonai/week*.yaml`,
         `contents/labs/physical-pentest-ai/week*.yaml`

---

### P17. KG-Integrated bastion agent (R5 학습 loop) [STATUS: deployed, monitoring 첫 record]

**동기**: 사용자 지시 (2026-05-02) — bastion agent 의 모든 작업이 KG 를
*사전 참조* (context 주입) + *사후 업데이트* (결과 anchor) 하도록 영구 통합.
P15 closed 후에도 R4 결과가 KG 에 누적 안 되던 design gap 해결.

**Definition of Done**:
- [x] **Phase 1: 3 신규 module + tests** (commit 413057cc)
  - `packages/bastion/kg_context.py` — KGContextBuilder (tier-aware retrieval +
    모델별 token budget gemma1500/gpt-oss4000 + LRU 5분 캐시 + silent fallback)
  - `packages/bastion/kg_recorder.py` — KGRecorder (5종 kind: task_outcome/
    observation/finding/asset_state/playbook_exec, semantic-hash dedup,
    schema_version 1, ATT&CK ID 자동 추출)
  - `packages/bastion/kg_metrics.py` — counter + histogram (in-memory)
  - `tests/bastion/` — 39 unit + integration test 모두 pass
- [x] **Phase 2: agent.py 통합**
  - `_inject_kg_context()` — `_stream_llm` 진입 시 자동 → 모든 LLM 경로
    (planner/agent/QA/playbook) 가 자동 KG 컨텍스트 받음
  - `_persist_react_run_to_graph` 끝에 `record_task_outcome` 호출
- [x] **Phase 3: api.py 신규 endpoint**
  - `GET /kg/metrics` — counter/histogram snapshot
  - `GET /kg/anchors/recent` — 최근 anchor 검증용
- [x] **Phase 4: 양 repo push + 원격 deploy**
  - mrgrit/ccc 413057cc (b5d31b16 sync 보강 추가) push 완료
  - mrgrit/bastion 0c6d58c push 완료
  - 원격 192.168.0.103 의 /opt/bastion 까지 sync (api.py 포함, sync_to_bastion.sh 의 P15 갭 영구 fix)
  - bastion uvicorn restart, /kg/metrics + /kg/anchors/recent 200 OK
- [x] **검증 #1 — KG context 주입 작동**
  - R4 첫 chat POST 후 `kg_context_search` counter +1 (2026-05-02 19:21 KST)
  - 직접 invoke: "Wireshark CVE" 쿼리에 anchor 5건 반환 + format() 정상
  - 검색 latency: avg 6ms (예상 50ms 의 8배 빠름)
- [x] **검증 #2 — KG record 작동** (2026-05-02 19:24 KST)
  - 첫 task_outcome anchor 생성 — `anc-eb7be21c801c`
  - schema_v1 + dedup_key + asset 연결 (asset-vm-10.20.30.80) 모두 정상
  - DVWA Command Injection task, skills_used=["shell"], outcome.success=true
- [ ] **검증 #3 — 24h 운영 metrics**: anchor 누적률 / dedup rate / cache hit rate
- [ ] **paper §7.X — KG-augmented detection** (R5 round 측정 후)

**Next concrete step**: 24h 운영 후 (1) `/kg/metrics` snapshot 으로 누적률 측정,
(2) 같은 task 반복 시 dedup 효과 확인, (3) cache hit rate 측정. 효과 양호 시
P17 closed → R4 종료 후 R5 round (KG-aware) 시작.

**Files**: `packages/bastion/kg_{context,recorder,metrics}.py`,
         `apps/bastion/api.py`, `tests/bastion/test_kg_*.py`,
         `scripts/sync_to_bastion.sh`

---

### P0. 야간 자율 작업 (2026-04-28 19:30~ → 2026-04-29 21:09 V2+supplemental 종료) — ✅ COMPLETE → moved to Closed

**상세 핸드오프**: `docs/2026-04-29-session-handoff.md` 참조 (다음 세션 진입 시 필독)

**V2 round 종료** (256/256, 2026-04-29 13:23 KST):
- pass 70 (27.0%) / fail 171 / no_exec 13 / qa_fallback 4 / error 1
- battle-adv-ai 0% → **36.2%** (+36.2pt) ★★★
- battle-ai 4.3% → **32.1%** (+27.8pt) ★★
- ai-security-ai 18.2% → 25.4% (+7.2pt)

**attack-ai supplemental 종료** (94/94, 2026-04-29 21:09 KST):
- pass 32 (34.0%) / fail 60 / no_exec 2
- server crash 회복 효과 정량화 완료

**Paper §6.2 핵심 finding**: timeout 280→600s fix 가 dominant (44.8% cases >280s)

**인프라 영구 fix 17 commits**: netplan 영구화 / secu DNAT 11rule / web vuln-sites 자동배포 / Docker DNS / 외부 직접 접근 차단 / OpenCTI UUID / WAF 교안 실측 등

**V2/supplemental 종료 후 보류 항목** (다음 세션):
1. Paper §6.2 표 작성 (사용자 보류 지시)
2. siem nft reboot 검증 (영구화 확인)
3. R4 round (모든 fix 적용 후 전체 재측정)

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
- [x] **Phase C — cyber range traffic replay 스크립트** (commit 0cf9b80e, `scripts/precinct6_replay.py`): sanitized signals.parquet → syslog/firewall/JSON 변환 → ssh+scp 로 siem/secu 의 log file 에 append. PCAP 직접 replay 는 sanitized data 한계로 불가능 → log injection 대안. dry-run 검증됨, 실 주입 검증 대기.
- [x] **Phase D 1번 — battle scenario 신규** (`contents/battle-scenarios/precinct6-data-theft.yaml`): 10 missions. mo_name=Data Theft / T1041 패턴 재현.
- [x] **Phase D 2번 — Phishing scenario** (`contents/battle-scenarios/precinct6-phishing.yaml`, commit 981f6e40): 10 missions. T1566 → T1078 → T1567 chain. SEG/SPF/DKIM/DMARC + click telemetry + MFA enforce.

**제약 발견**: dataset v1.0.0 의 mo_name 분포가 빈약 (Data Theft 99.99%) — 100만 확장해도 새 MITRE technique 안 늘어남. 의미있는 다양성 위해 **`-100m` 풀 데이터셋** 필요할 수 있음 (1억건, 수십GB).

**Next concrete step**: incidents.jsonl 의 nested host/cred 메타에서 Asset 풍부화 추가 (지금 IoC 만 IP 단위, host 단위 grouping 필요).

**Files**: `scripts/import_precinct6.py`, `docs/changelog-2026-04.md` §B4

---

### P2. R2 round retest 완주  [STATUS: ✅ COMPLETE → moved to Closed]

→ Closed 섹션 참조.

---

### P3. R3 round retest  [STATUS: ✅ COMPLETE → R4 main 으로 승계 (moved to Closed)]

**최종 (2026-05-01)**: R3 누적 3,096 cases / pass 2,221 (71.7%) / fail 768 / error 61 /
qa_fallback 28 / no_execution 18. R3 main + V2 + supplemental + low3 누적.
잔존 non-pass 842 → R4 main 큐로 승계 (driver 329262, ETA 60-70h, fixture pre-hook + self_verify raw dump 검출 통합).

---

### P4. Battle scenarios semantic verify 수기 작성  [STATUS: ★ ✅ COMPLETE 192/192 → moved to Closed]

→ 모든 15 시나리오 192 미션 완료. Closed 섹션 참조.

**Definition of Done**:
- [x] 15 시나리오 × 평균 13 mission = 192 미션 (task #19 completed)
- [x] 시나리오당 1 commit (15 commits)
- [x] paper §7 Battle scenarios 결과 reflect (paper-draft.md §7.X)

**Files**: `contents/battle-scenarios/*.yaml`

---

### P5. Bastion-Bench 590 hold-out task 작성  [STATUS: ✅ COMPLETE 590/590 → moved to Closed]

**야간 long run 진행 (2026-04-26 22:00~04:00 KST)**:
- 시작: 28/590 (10 카테고리)
- 현재: 71/590 (23 카테고리)
- ★ 23/23 모두 h001+h002+h003 완비 (pentest/web-vuln 은 h004 추가)
- 신규 카테고리 13: cloud-security, forensics, threat-hunting, ot-security, mobile-security, privacy-engineering, crypto-key-management, zero-trust, redteam-ops, social-engineering, api-security, siem-engineering, email-security
- 야간 cycle 평균 5분 / commit + push 별

- [x] 5 신규 카테고리 task 작성 (web-vuln/compliance/ai-ir/ai-utilization/ai-pentest)
- [x] 10/10 카테고리 모두 ≥1 pilot task 보유
- [x] **본격 작성 590/590 완료** (2026-04-29) — `contents/papers/bastion/pilot-tasks/` 591 파일 (590 task + README), 41 카테고리 cover
- [x] **카테고리 확장** — 10 → 41 (cloud-security, forensics, threat-hunting, ot-security, mobile-security, privacy-engineering, crypto-key-management, zero-trust, redteam-ops, social-engineering, api-security, siem-engineering, email-security, blue-team, governance, data-security, iot-security, healthcare-security, financial-security, cloud-native-security, automotive-security, fraud-detection, dlp, devsecops, telecom-security, supply-chain-security, container-security, wireless-security, firmware-security, application-security, network-security, red-team-tactics 등 31 신규)
- [ ] **채점 파이프라인 실 검증** — Bastion 으로 10 task 실행 + judge 정확도 측정 (R4 후)
- [ ] **paper §6.2 결과 반영** — 측정 결과 후

**Next concrete step**: pilot 5건을 실제 Bastion 으로 1회 실행 → 채점 정확도 검증 → 기준 통과 시 590 본격 작성 시작.

**Files**: `contents/papers/bastion/01-evaluation-design.md`, `contents/papers/bastion/pilot-tasks/`

---

### P6. 외부 벤치마크 실측  [STATUS: ✅ adapter 6/6 완성, 실 측정 R4 후]

- [x] `benchmarks/cybench_adapter.py` (commit 5acf78a) — task YAML → /chat → docker exec → subtask 매칭
- [x] `benchmarks/nyu_ctf_adapter.py` (commit 7af43ab) — 6 도메인 차별 prompt + Cybench 함수 재사용
- [x] `benchmarks/intercode_adapter.py` — 멀티턴 강조 + checkpoint hint 동적 노출 + python interpreter
- [x] `benchmarks/cybersec_eval_adapter.py` — 1000+ prompt MC, classify_response (refuse/answer/classify) + safety_breach/safe_refuse/false_refusal 메트릭
- [x] `benchmarks/harmbench_adapter.py` — 100 cyber subset, ASR (Attack Success Rate) + 6 attack types (direct/dan/pair/gcg/roleplay/encoding) + partial_breach 분류
- [x] `benchmarks/agentbench_os_adapter.py` — 60 OS task subset, 8 카테고리 + ReAct (Thought/Action/Observation) + verification_cmd oracle 채점

**P6 어댑터 6/6 완성 (2026-04-26 ~)** — 실 측정 단계 진입.

**Definition of Done**:
- [x] `benchmarks/cybench_adapter.py` — Cybench 40 task adapter
- [x] `benchmarks/nyu_ctf_adapter.py` — NYU CTF subset 60
- [x] `benchmarks/intercode_adapter.py` — InterCode-CTF 100, 멀티턴 + checkpoint hint
- [x] `benchmarks/cybersec_eval_adapter.py` — 1000 prompt MC, classify_response
- [x] `benchmarks/harmbench_adapter.py` — 100 cyber subset, 6 attack types + ASR
- [x] `benchmarks/agentbench_os_adapter.py` — 60 OS task, ReAct + verification_cmd oracle
- [ ] **실 측정 #1: Cybench 40 task pilot** — bastion 큐 (R4 main 후)
- [ ] **실 측정 #2: NYU CTF / CyberSecEval / HarmBench / InterCode / AgentBench**
- [ ] paper Table 1 의 XX% 자리 채움

**Next concrete step**: R4 main 종료 후 bastion 점유 풀리면 Cybench 5 task pilot 부터.

**Files**: `benchmarks/cybench_adapter.py`, `benchmarks/nyu_ctf_adapter.py`, `benchmarks/intercode_adapter.py`, `benchmarks/cybersec_eval_adapter.py`, `benchmarks/harmbench_adapter.py`, `benchmarks/agentbench_os_adapter.py`

---

### P16. Fixture-driven cyber range — 합성 보안 데이터 사전 주입  [STATUS: 173 step apply 완료, pilot 검증 중]

**동기**: 사용자 핵심 통찰 (2026-05-01) — non-AI 학생이 grep 으로 찾는데 데이터가 없으면 교육 불가능. fixture system 으로 reproducible learning. paper 후속 연구 entry 후보.

**Definition of Done**:
- [x] **Phase 1: schema** — `fixtures` 필드 (generator/target_vm/path/params/seed) 도입, 6 generator 모듈 (lib/generators/lolbas_log/auth_log/web_access/suricata_alert/wazuh_alert/firewall_log)
- [x] **Phase 2: bulk apply** — `scripts/lab_fixture_auto_apply.py` 6 regex 룰 → 173 step 일괄 적용 (firewall_log 72 / suricata_alert 54 / wazuh_alert 28 / web_access 10 / auth_log 6 / lolbas_log 3) · 99 lab 파일 변경
- [x] **driver wrapper** — `results/retest/driver_r3_fixture_pilot.sh` lab_fixture_inject.py + sshpass scp 동기화
- [x] **bastion 배포** — /home/ccc/cyber-range/fixtures/<lab>/<order>/ 자동 mkdir + scp
- [x] **3 핵심 버그 발견·수정** (2026-05-01 15:25–15:42): (a) ai 버전 88 step 의 `bastion_prompt` 에 [FIXTURE] note 누락. (b) driver stdin race — test_step.py:597 `input()` 가 큐 stdin 소진 → 1 step 후 종료. (c) ssh/scp 도 stdin 소비. fix: `< /dev/null` + ssh `-n` + setsid 새 세션.
- [x] **3섹션 분석 요구** instruction/bastion_prompt 175 step 모두 강화 — raw cat dump 방지 (1.핵심발견 2.MITRE/위협 3.방어).
- [x] **wazuh DNS 비중 강화** 6→60 (10×) — 100501/100502/100503 DGA·NXDOMAIN·TXT rule 추가.
- [x] **seed 정책 도입** (사용자 요청 2026-05-01): 매번 random (외우기 방지) > student-id 결정론 > 명시 seed (재현). resolve_seed() + log 에 seed 기록.
- [x] **mode=append** 검증: 168 → 336 → 504 누적 (시간 흐름 시뮬레이션). default overwrite.
- [x] **/labs/start hook** — apps/ccc_api/src/main.py 에 lab_fixture_inject.py 호출 (--student-id 기반 결정론). 학생 lab 진입 시 자동 fixture 생성.
- [x] **pilot 검증 #1·#2** (lolbas/wazuh): verify_match=True 처음 달성 — agent 가 fixture path 정확히 사용. fail 원인은 raw dump.
- [x] **pilot10 (12 step) 종료** (2026-05-01 17:33): pass 1 / fail 5 / timeout 6. timeout 50% 가 새 병목. 1 PASS = agent-ir-nonai/w01/o4 lolbas (file_manage). raw dump fail 2건 → self_verify 강화로 다음 round retry.
- [x] **fix 일괄 적용** (2026-05-01 18:50–19:00): (a) order=99 multi_task fixture 26건 제거 — task 복잡도 ↑. (b) [FIXTURE] note 149건 압축 (3-4줄). (c) driver timeout 600→720s. (d) self_verify 의 raw dump 자동 검출 + retry (`type=EXECVE`/`"timestamp":`/`"rule":` 라인 ≥3 + MITRE/방어 키워드 부재 → 분석 강제 retry). (e) bastion 양 repo + 원격 sync.
- [⏳] **R4 main 진행** — driver pid 329262, 842 step (R3 non-pass 전수). ETA ~60–70시간 (2–3일). progress: bastion_test_progress.json 누적.
- [ ] **paper §7 fixture vs no-fixture 비교 metric** — R3 main 21.54% pass vs R3+fixture pass rate
- [ ] **Phase 3: Precinct 6 hybrid** — replay 와 결합 (signals.parquet 도 fixture path 로 노출)
- [ ] **Phase 4: course snapshot** — 코스별 사전 세팅 fixture pack
- [ ] **Phase 5: file_manage skill 자동 fixture path 검색** — agent 가 [FIXTURE] note 자동 인식

**Next concrete step**: pilot driver 230199 결과 확인 후 R4-fixture sample30 retest 시작 → pass rate 측정 → paper §7 보강.

**Files**: `lib/generators/`, `scripts/lab_fixture_inject.py`, `scripts/lab_fixture_auto_apply.py`, `docs/fixture-spec/README.md`, `results/retest/queue_r4_fixture_*.tsv`

---

### P7. Production trial 30일  [STATUS: fixture 작성 완료, day-by-day 실행 대기]

**동기**: paper §7.4 Track C — 4 시나리오 (월간 점검·CVE 대응·IR drill·변경 관리) × 30일 연속 운용.

**Definition of Done**:
- [x] **시나리오 4종 픽스처 작성** (commit 8064daf4) — `contents/production-trial/`:
  - A `monthly-health-check.yaml` (SLA 30min, HITL 2단계, 7-step)
  - B `cve-emergency.yaml` (SLA 120min/MTTM, HITL 1단계, 7-step + 3 CVE 시뮬)
  - C `ir-drill.yaml` (SLA 60min/MTTC≤10min, HITL 1단계, 7-step + 3 drill 시뮬)
  - D `change-management.yaml` (SLA 90min, HITL 2단계, 7-step + 3 sample CR)
  - 각 step verify.semantic 4-axis (intent/criteria/methods/negative_signs)
  - kpi_targets 명시 (wallclock / MTTM / MTTC / accuracy / FP)
- [ ] 운영자 inline review 체크리스트 정의
- [ ] day-by-day 일정 실행 (운영자 수동 트리거 + Bastion 자동)
- [ ] paper Table 4 (시나리오별 wallclock·HITL·critical errors) 채움

**Next concrete step**: 시나리오 A 1 cycle 수동 실행 → wallclock + HITL 비율 측정 → fixture 미세조정.

**Files**: `contents/production-trial/*.yaml`, `contents/papers/bastion/03-real-world-scenarios.md`

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

**✅ R3 final 분류 완료 (2026-04-28 야간)** — `results/retest/r3_paper_metrics.json`:
- attack-adv-ai: 90 case, pass 21 (23.3%) — 목표 30% 미달
- attack-ai: 135 case, pass 14 (10.4%), **error 94건 (Connection refused)** — bastion server crash 시기 (V2 wait_for_bastion 로 해결)
- battle-ai: 17 case, pass 1 (5.9%), no_exec 14 — sample 작아서 통계 의미 약함
- ai-security-ai: 66 case, no_exec 59 (89%) — **prompt_fallback fix target pattern** (45건이 6 turn planning/validating only, skill 호출 0)
- 비교 healthy: ai-agent-ai 48.2% / soc-ai 36.7% / ai-safety-ai 41.7%

**근본 원인 분류**:
1. **Server crash error** (94건) → V2 driver 의 wait_for_bastion 5-retry 로 해결
2. **prompt_fallback target** (59건 ai-security-ai) → V2 fix 적용 측정 중 (256 case 진행)
3. **harmony tool-call 거부** (battle-ai 14) → derestricted 라우팅 + harmony fix 효과 약함, sample 작음
4. **probe 잘못 선택** (attack-ai/attack-adv-ai 일부) → P10 휴리스틱 으로 일부 해결

P8 closed 후보 — V2 측정 결과 후 attack-ai/ai-security-ai 의 fix 효과 확인 후.

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

### P10. Skill 카탈로그 동적 확장  [STATUS: ✅ R3 final 15/33 → moved to Closed (2026-04-28)]

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

**✅ R3 final 결과 (2026-04-28 야간)** — `results/retest/r3_paper_metrics.json`:
- Total: 650 / pass 140 (21.5%) / exec_rate 67.7%
- **Active: 15 / 33 catalog** — paper §3.5 와 일치 (5x dormant skill 활성)
- top 5: ollama_query 95 / file_manage 93 / shell 90 / probe_all 61 / probe_host 57
- avg elapsed: pass 139s / fail 154s
- 18+ 목표 달성 못함 (history_anchor/forensic_collect/model_isolate 등 dormant). paper limitation 으로 명시.

---

---

### P12. 자율 공방전 (Autonomous Multi-team Battle)  [STATUS: Phase 1 + end-game 완료, Phase 2/3 대기]

**동기**: 현재 1v1 (Red/Blue 고정역할) 만. 다중 팀이 자기 자산으로 공격하면서 동시에
방어하는 "ffa-style" 모드 부재 → 공방전 다양성 부족.

**Definition of Done**:
- [x] DB: battle_participants + battle_attack_claims (apps/ccc_api/src/main.py:273-308)
- [x] battle_type='autonomous' + 무제한 join (line 2572~3066)
- [x] API: /battles/{bid}/auto/join, /my-targets, /my-defense, /claim-attack, /scoreboard, /finalize
- [x] semantic judge claim 채점 (attack_landed/defense_block/own_breach 점수)
- [x] Battle.tsx 자율 모드 view (line 52~651: 전체 팀 점수판 + my-targets/my-defense + incoming)
- [x] **end-game** /auto/finalize (line 3380) + UI modal (winner/MVP/timeline)
- [ ] **Phase 2: Wazuh/Suricata 자동 탐지** → defense_block 자동 점수
  - Design: `POST /battles/{bid}/auto/wazuh-poll` — 1회 polling, ssh 로 wazuh-manager(siem):/var/ossec/logs/alerts/alerts.json fetch
  - 매칭 룰: my-defense 미션의 `expected_alert.rule_id` 와 비교 → claim_type='defense' 자동 INSERT
  - 또는 background worker (Wazuh API webhook 가능 시 이상적)
  - **deferred**: R4 main 의 bastion+wazuh 점유 충돌. R4 후 1 cycle 검증 후 활성화.
- [ ] **Phase 3: AI 자율 모드** — 각 팀 Bastion 이 Red+Blue 동시 자율 (LLM 기반)
- [ ] (옵션) replay viewer / 영상 export

**Next**: R4 종료 후 Phase 2 worker 구현 + 1 battle 실측 검증.

**Files**: apps/ccc_api/src/main.py (DB+API), apps/ccc-ui/src/pages/Battle.tsx (UI)

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
- [x] **Phase 4 (2026-04-28)**: P5 web-vuln 20 task 의 vuln-site 매핑 — `docs/p5-vuln-site-mapping.yaml`
  - JuiceShop 5 / NeoBank 3 / GovPortal 2 / AdminConsole 5 / AICompanion 5 / MediForum 0 / DVWA 0
  - 학생 P5 실습 시 vuln-site 실 인프라 사용 가능 — knowledge eval + execution eval 통합

**Files**: contents/vuln-sites/{neobank,govportal,mediforum,adminconsole,aicompanion}/ · apps/ccc_api/src/main.py

---

### P15. 외부 지식 채널 + 9-tier KG 운영  [STATUS: ✅ 2026-04-28 closed — 754 SKILL + 영구 path fix]

**✅ 2026-04-28 야간 closed 후보**:
- KG path bug 영구 fix (graph.py size 우선 + sync_to_bastion BASTION_GRAPH_DB env)
- 754 SKILL.md (mukul975) 임포트 완료
- 8 source / 3,200+ anchor 누적
- bastion runtime 정상 + watchdog script 추가 (crash auto-recovery)

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

### P14. Lab 채점 흐름 재설계 (textarea → SubAgent 감시)  [STATUS: ✅ COMPLETE → moved to Closed (2026-04-30 e2e 검증)]

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

- [x] **B. SubAgent transcript 자동 캡처** (commit acd0b005 + opsclaw b63cffa)
  - apps/subagent-runtime 의 `/audit/start` / `/audit/stop`
  - 캡처: web shell + script(1)
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
- [x] C Manager 채점 prompt
- [ ] **1 lab 학생 직접 실측** (사용자 검증 필요 — production 배포 후)
- [ ] **A vs C 결과 비교 측정** (R4 후 / 학생 실측 후)
- [x] 기존 textarea 흐름 deprecated 표시 (Labs.tsx 의 "⚠ 레거시 모드" 라벨, 2026-05-01)
- [ ] paper §3.5 업데이트 (P9 와 통합 — R4 후 paper full pass 시)

**Next concrete step**: 학생 실측은 운영 배포 후. 코드 작업은 P9 / textarea deprecate 만.

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

### 2026-04-30 23:55 — R3 fix #1/#2/#3 일괄 적용 + 인프라 IP 변동 (bastion 0.115→0.103)

**진단 (R3 V2 + low-3 supplemental fail 분석)**:
- Pattern 1: agent 가 `http://10.20.30.80` (bastion-internal) 사용 → attacker 라우팅 테이블에 없어 unreachable
- Pattern 2: `curl -s` 단독 명령 → 본문만 출력되어 verify 의 status/header 매칭 실패
- Pattern 3: self_verify_completion 의 tool_summary truncation 200자 → 충족 자료 부족 → 무조건 false
- Pattern 4: self_verify_fail 후 재시도 prompt 막연한 "추가로 호출하라" → 같은 명령 6회 반복

**적용된 fix**:
- [x] **Fix #1** (commit 76d1b921) — `packages/bastion/skills.py` shell handler: target=='attacker' 시 `10.20.30.80` → `192.168.0.108` (secu DNAT) 자동 치환
- [x] **Fix #2** (commit 1625b03e) — shell handler: curl + exit_code==0 + stdout < 60자 → `-i -L` 옵션 추가 자동 retry
- [x] **Fix #3** (commit e72ae39a) — `packages/bastion/agent.py`:
  - _self_verify_completion: tool_summary 200→800자, negative_signs 블록, 5단계 판정 원칙
  - self_verify_fail 후 재시도 prompt: 미충족 success_criteria 명시 + 5개 행동 지침
  - 최종 synthesis (last_assistant_content 비었을 때): 도구 stdout 인용 + 기준별 충족/미충족 명시 강제
- [x] **Fix #4** (commit 5070990a) — `packages/bastion/agent.py` web-vuln 카테고리 prompt:
  - `target: web` shell 호출 금지 (lab 의도 아님)
  - 최종 답변 4섹션 강제: 실행 결과 인용 / 취약점 입증 / 방어 언급 / 한계·인지
- [x] **Fix #5** (commit 8e227393) — skill output truncation 1000→2500자:
  - skill_result event output[:1000] → output[:2500]
  - 다음 turn LLM 입력 stdout[:1500] → output[:3000]
  - stderr[:500] → stderr[:800]
  - Fix #2 의 curl -i -L 응답이 jdge 에 잘려서 'no-output' 판정되는 버그 차단

**인프라 fix**:
- [x] bastion process IP propagation (16 scripts: ingest_*, post_v2_chain.sh, bastion_kg_sync.sh, r3_diagnose.py, sync_to_bastion.sh 등)
- [x] ccc-api `/api/graph/*` alias (Knowledge UI 404 → 2791 nodes/8354 edges 정상 표시)
- [x] OpenCTI token UUID format runtime + code default
- [x] wazuh-manager local_rules.xml 정리 (3개 rule 활성화)
- [x] vuln-sites Docker DNS fix (8.8.8.8) + Docker DNAT 직접 접근 차단
- [x] secops/week01 lecture WAF 실측 반영
- [x] attacker VM 13 pentest tools 설치 (sqlmap·ffuf·nuclei·whatweb·hydra·gobuster·sslscan 등)

**예상 효과 (보수)**:
- 'no-output' 판정 12+건 중 ~7건 회복
- self_verify→재시도 무한 반복 패턴 차단
- low-3 supplemental 254건 중 ~25건 fail→pass 추가
- 측정 카테고리별: web-vuln-ai 5%→25%+, physical-pentest 16%→30%+, autonomous 18%→32%+

**측정 방법**:
- bastion 14:49:18 KST 재시작 후 신규 케이스 (`r3_low3_supplemental` #29 부터) 자동 적용
- 최종 정량은 R4 round (1285 step 전체 재측정) 시 산출

**Bastion 양 repo push 완료**: mrgrit/ccc (e72ae39a) + mrgrit/bastion (74b1afb)

### 2026-04-30 — P14 e2e 검증 완료 + Knowledge UI fix
- [x] **P14 Lab 채점 흐름 재설계** — A/B/C/D 사이클 모두 완료. 2026-04-30 e2e 시뮬레이션 (/tmp/p14b_e2e.py):
  - subagent_audit 모드 정상 (capture_mode=subagent_audit, audit_active=True)
  - SubAgent /a2a/audit/start → run × 3 → stop 전체 흐름 작동
  - DB lab_sessions.transcript 자동 저장
  - multi_step_judge (P14-C, gpt-oss:120b) 16 step 모두 평가 (score 0/200, fail reason+feedback 정확)
  - subagent-runtime PID 578 (4월 15일 stale) → 재시작 → audit endpoints 활성
- [x] **Knowledge UI fix** (commit 24c48db9) — `/api/graph/*` 라우트 alias + BASTION_URL 0.103 default
- [x] **R3 low-3 supplemental round 시작** — web-vuln 133 + physical-pentest 67 + autonomous 54 = 254 cases (commit ea0441fa, PID 3991712, 백그라운드)

### 2026-04-29 — P0 야간 R3 V2 + supplemental 완료 + 인프라 7 fix
- [x] V2 round 256/256, attack-ai supplemental 94/94 모두 측정 종료. paper §6.2 데이터 확보.
- [x] netplan 영구화 (모든 VM ens37 reboot 시 IP 보존)
- [x] secu 외부 NIC DNAT 11 rule (외부 IP:port → 내부 service)
- [x] web/siem 외부 직접 접근 차단 (DOCKER-USER iptables + nft input)
- [x] web 의 vuln-sites 5종 자동 배포 (onboarding tar upload + docker-compose)
- [x] Docker DNS 8.8.8.8 (vuln-sites build 시 pypi 도달)
- [x] OpenCTI token UUID 형식 (validation 통과)
- [x] secops/week01 lecture WAF 점검 실측 반영 (사용자 보고 fix)

### 2026-04-28 — P5 / P10 / P15 / P13 Phase 4
- [x] **P5 Bastion-Bench 590/590 100% COMPLETE** — 42 카테고리 + h001-h025 (책임자율 야간 long run, 2026-04-26 22:00 ~ 2026-04-28 19:00). 6 step × verify.semantic + knowledge eval (~85%) + execution eval (~15%).
- [x] **P10 Skill 카탈로그 R3 final** — Active 15/33, top 5 (ollama_query/file_manage/shell/probe_all/probe_host). 5x dormant skill 활성화 (cve_lookup/wazuh_api/garak_probe/prompt_fuzz/memory_dump/deploy_rule). paper §3.5 정량 반영.
- [x] **P15 외부 지식 채널** — 754 SKILL.md (mukul975 cybsec_skills) 임포트 + KG path bug graph.py 영구 fix (size 우선 + BASTION_GRAPH_DB env). 8 source / 3,200+ anchor 누적. watchdog daemon 추가.
- [x] **P13 Phase 4** — P5 web-vuln 20 task ↔ vuln-sites 매핑 (`docs/p5-vuln-site-mapping.yaml`).

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
