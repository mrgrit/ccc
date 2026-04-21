# CCC — Cyber Combat Commander

> 사이버보안 교육 훈련 플랫폼 — **20개 교과목**, 600개 실습, AI 에이전트(Bastion), 공방전, 블록체인 성과 관리
> Bastion 실증 테스트 **3,090 케이스 · 45.5% pass rate (자동, 단일 모델, single-shot)**

## Quick Start

```bash
# 1. 설치 (시스템 패키지 + Python + Node.js + Docker + PostgreSQL)
bash setup.sh

# 2. 실행
./dev.sh api          # http://<IP>:9100/app/
# 관리자: admin / admin1234

# 3. Bastion 에이전트 (독립 운영용)
./dev.sh bastion      # http://<IP>:8003

# 4. 업그레이드
bash upgrade.sh

# 5. Docker 독립 배포
docker compose -f docker/docker-compose.yaml up -d
```

---

## 아키텍처

```
학생 (브라우저)
    |
    v
CCC Central (:9100)
    ├── Training (교안 + Non-AI/AI 실습)
    ├── Cyber Range (과제 풀이 + 자동 채점)
    ├── Battlefield (Red vs Blue 공방전)
    ├── CCCNet (블록체인 성과 추적)
    ├── CTF (AI 자동 출제)
    ├── AI Tutor (챗봇)
    ├── Admin (그룹/학생/승급/콘텐츠 검수)
    └── My Infra (VM 온보딩 + 자동 검수)
          |
          v
    학생 개별 인프라 (5~6대 VM, VMware)
    ├── attacker (10.20.30.201) — nmap, hydra, sqlmap, nikto, metasploit
    ├── secu    (10.20.30.1)   — nftables, Suricata IDS/IPS
    ├── web     (10.20.30.80)  — Apache, ModSecurity CRS, JuiceShop, DVWA
    ├── siem    (10.20.30.100) — Wazuh Manager/Indexer/Dashboard, OpenCTI
    ├── manager (10.20.30.200) — Ollama LLM, Bastion Agent
    └── windows (10.20.30.50)  — 선택사항
```

### 트래픽 흐름
```
Attacker ──→ SECU (nftables → Suricata NFQUEUE) ──→ WEB (ModSecurity → Apache)
                                                         │
SIEM (Wazuh) ◄──────── rsyslog / agent ◄────────────────┘
     │
OpenCTI (CTI feed → IOC → nftables blocklist)
```

### Bastion AI 에이전트
```
                    ┌─────────────────────────────────┐
                    │         Bastion Agent            │
                    │  Planning → Executing → Analysis │
                    │  18 Skills / 8 Playbooks         │
                    │  Experience Layer + Auto-Promote  │
                    └────────┬───────────┬────────────┘
                             │           │
          ┌──────────────────┤           ├──────────────────┐
          ▼                  ▼           ▼                  ▼
   ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌────────────┐
   │ SubAgent    │  │ SubAgent     │  │ SubAgent    │  │ SubAgent   │
   │ (secu)      │  │ (web)        │  │ (siem)      │  │ (attacker) │
   └─────────────┘  └──────────────┘  └─────────────┘  └────────────┘
```

---

## 교과목 (20개)

| 그룹 | 과목 | 주차 | Non-AI | AI | 최소 랭크 |
|------|------|------|--------|-----|----------|
| **공격 기술** | 사이버 공격 기초 | 15 | 15 | 15 | rookie |
| | 사이버 공격 심화 | 15 | 15 | 15 | expert |
| | 웹 취약점 | 15 | 15 | 15 | rookie |
| **방어 운영** | 보안 솔루션 운영 | 15 | 15 | 15 | rookie |
| | 컴플라이언스 | 15 | 15 | 15 | rookie |
| | SOC 기초 | 15 | 15 | 15 | rookie |
| | SOC 심화 | 15 | 15 | 15 | skilled |
| | 클라우드/컨테이너 | 15 | 15 | 15 | skilled |
| **AI 보안** | AI/LLM 보안 | 15 | 15 | 15 | skilled |
| | AI Safety 기초 | 15 | 15 | 15 | skilled |
| | AI Safety 심화 | 15 | 15 | 15 | expert |
| | AI 에이전트 보안 | 15 | 15 | 15 | expert |
| | 자율 보안 | 15 | 15 | 15 | expert |
| | 자율 시스템 보안 | 15 | 15 | 15 | expert |
| | IoT 보안 | 15 | 15 | 15 | skilled |
| **실전** | 공방전 기초 | 15 | 15 | 15 | rookie |
| | 공방전 심화 | 15 | 15 | 15 | expert |
| | 물리 보안/모의해킹 | 15 | 15 | 15 | skilled |
| **AI 에이전트 IR** | 에이전트 침해대응 | 15 | 15 | 15 | expert |
| | 에이전트 침해대응 심화 | 15 | 15 | 15 | master |

- 15주 × 20과목 = **300주** 교안 (Markdown, 파일 참조 가이드 포함)
- 15주 × 20과목 × 2(Non-AI + AI) = **600개** 실습 (YAML)
- AI 실습: Bastion에 프롬프트를 입력하여 AI 에이전트가 작업 수행
- Non-AI 실습: 학생이 직접 CLI/UI로 수행

---

## Bastion — 보안 운영 AI 에이전트

프롬프트 하나로 서버 점검, 방화벽 설정, 침입 탐지, 로그 분석, 공격 시뮬레이션까지 수행하는 보안 운영 특화 AI 에이전트.

### Skill System (18종)

| Skill | 역할 | 대상 VM |
|-------|------|---------|
| `probe_host` | 호스트 상태 점검 (uptime/disk/memory) | auto |
| `probe_all` | 전체 인프라 일괄 점검 | local |
| `scan_ports` | nmap 포트 스캔 | attacker |
| `check_suricata` | Suricata IDS 상태 + 최근 알림 | secu |
| `check_wazuh` | Wazuh SIEM 상태 + 에이전트 + 알림 | siem |
| `check_modsecurity` | ModSecurity WAF 상태 + 차단 로그 | web |
| `configure_nftables` | 방화벽 테이블/체인/set/룰 구조화 관리 | secu |
| `deploy_rule` | Suricata/Wazuh 탐지 룰 배포 | auto |
| `analyze_logs` | 로그 수집 + LLM 분석 | auto |
| `web_scan` | nikto/curl 기반 웹 취약점 점검 | attacker |
| `shell` | 임의 셸 명령 실행 (fallback) | auto |
| `enroll_wazuh_agent` | Wazuh 에이전트 자동 등록 | siem |
| `ollama_query` | Ollama LLM API 직접 호출 | local |
| `http_request` | HTTP 요청 (GET/POST, 헤더/바디 커스텀) | attacker |
| `docker_manage` | Docker 컨테이너 관리 (ps/logs/exec/stats) | auto |
| `wazuh_api` | Wazuh REST API 호출 | siem |
| `file_manage` | 파일 읽기/쓰기/검색 | auto |
| `attack_simulate` | 공격 시뮬레이션 (SQLi/XSS/brute-force) | attacker |

### Playbook System (8 정적 + 자동 승격)

| Playbook | 설명 |
|----------|------|
| `hardening` | 시스템 경화 체크리스트 |
| `incident_response` | 인시던트 대응 절차 (탐지→억제→분석→복구) |
| `probe_all` | 전체 인프라 상태 점검 |
| `vuln_scan` | 포트 + 웹 취약점 스캔 |
| `security_audit` | 방화벽/IDS/WAF/SIEM 종합 감사 |
| `attack_simulation` | Red Team 공격 체인 (정찰→스캔→SQLi→XSS) |
| `log_investigation` | 의심 활동 로그 교차 분석 |
| `wazuh_health` | Wazuh Manager/Agent/룰/알림 종합 점검 |

추가로 **Experience Layer**가 반복 성공 패턴을 자동 학습하여 Playbook으로 승격 (현재 19개 자동 생성).

### LLM 설정

| 항목 | 값 |
|------|-----|
| Manager 모델 | gpt-oss:120b (DGX Spark 서빙) |
| SubAgent 모델 | qwen3:8b (경량 판단) |
| 실습용 취약 모델 | ccc-vulnerable:4b, ccc-unsafe:2b |
| Ollama 서버 | 폐쇄망 내부 GPU 서버 |

### 의도 분류 (Intent Classifier)

regex 대신 **LLM 자체가 "실행 vs 답변"을 판단**하는 프롬프트 기반 설계. 모델이 바뀌어도 동작.

---

## 주요 기능

### Training + Cyber Range
- **Training**: 교안(Markdown) 읽기 + 실습(YAML) 제출 통합
- **Cyber Range**: 과제 풀이 모드, 5스텝 그룹별 부분 제출, 자동 채점
- **AI 실습**: Bastion에 프롬프트 입력 → AI 에이전트가 실제 인프라에서 작업 수행
- **Non-AI 실습**: CLI/UI 명령어 직접 수행, Wazuh Dashboard 등 UI 기반 안내
- **정답 표시**: admin 로그인 시 각 스텝의 프롬프트/CLI/UI 정답 확인 가능

### 시스템 상태 검증 (SystemChecker)
- 학생이 "제출"하면 **SubAgent가 학생 인프라에 직접 접속**하여 실제 설정 반영 여부 확인
- 검증 타입: file_contains, nft_rule_exists, service_active, port_open, log_contains, command_output
- 학생 VM 자동 조회 (`student_infras` DB → role별 SubAgent URL 매핑)

### 인프라 온보딩
- UI에서 VM IP 입력 → 자동 설정 (secu→siem→web→attacker→manager 순서)
- 보안 스택 자동 설치: nftables + Suricata + ModSecurity + Wazuh + rsyslog
- 42개 항목 자동 검수 (서비스 상태, 룰, 로그, 네트워크 E2E)

### CCCNet 블록체인
- 활동별 자동 블록 생성: lab_complete(50pt), ctf_solve, battle_win(50pt), rank_up(1000pt)
- 블록 검증, 리더보드, 승급 조건 연동

### AI Safety 실습용 모델 파인튜닝
- **ccc-vulnerable:4b**: 약한 안전 가드레일 (REFUSED/COMPLIED/DAN MODE 라벨)
- **ccc-unsafe:2b**: 안전장치 제거 (모든 요청에 응답)
- **ccc-safety-qlora:4b**: QLoRA 파인튜닝 결과 (30 샘플, unsloth, 3 epoch)
- 재현성 가이드: [`contents/education/shared/ai-safety-model-setup.md`](contents/education/shared/ai-safety-model-setup.md)
- 데이터셋·스크립트: `finetune/dataset/` · `finetune/scripts/qlora_finetune.py`
- Phase 1 (Modelfile 10분) + Phase 2 (QLoRA 30~60분) + 재파인튜닝 사이클 명세

### Semantic Verify 시스템
학생·Bastion 응답을 **의도·방법 매칭** 으로 판정하는 LLM 채점관:

- **구조**: 각 lab step 의 `verify.semantic` 필드 — `intent`, `success_criteria[]`, `acceptable_methods[]`, `negative_signs[]`
- **판정기**: `scripts/test_step.py` 의 `llm_semantic_judge` — gpt-oss:120b 기반 JSON 출력
- **안전장치**: 위험 payload 자동 SHA256 hash 처리 (RCE, reverse shell, SQLi UNION 등)
  - 원본 격리: `contents/.sensitive/<hash>.txt` (gitignored)
  - admin-only API: `GET /admin/sensitive/{hash}`
- **커버리지 (현재)**:
  - attack-adv-ai 220/220 (100%)
  - web-vuln-ai 182/182 (100%)
  - autonomous-systems-ai 120/120 (100%)

---

## 실증 테스트

> 논문: "AI 에이전트는 보안 엔지니어를 대체할 수 있는가?"

| 항목 | 값 |
|------|-----|
| 총 테스트 케이스 | **3,090개 (20개 과정, 15주차)** |
| 완료 | 3,089 (99.9%) |
| **엄격 Pass** | **1,406 (45.5%)** — 자동, 단일 모델, single-shot |
| Fail | 1,520 (49.2%) |
| QA-fallback | 140 (4.5%) — 876 → 140 (**−84%**) |
| Pass rate 개선 | 초기 32.3% → 45.5% (**+13.2%p**) |

### 개선 히스토리

| 세대 | 내용 | 효과 |
|------|------|------|
| w19 | intent classifier 패턴 override | 실행 분기 진입율 상승 |
| w20 | skill 성공 후 LLM semantic 검증 + retry | |
| w21 | QA 응답 정규식 파싱 + 파괴 명령 차단 | qa→exec 전환율 0→20% |
| w22 | ask_user HITL 이벤트 모드 | HITL 40% pass 전환 실증 |
| w23 | SubAgent(gemma3:4b) 명령 추출 fallback | 20→60% |
| w24 | SubAgent 명령 생성 fallback | 60→75% |
| w25 | `verify.semantic` 필드 + LLM 판정기 | 엄정한 의도 기반 채점 |
| w26 | num_predict 120→800 버그 수정 | 판정기 JSON 빈 응답 버그 |

### 과정별 현재 성공률 (상위)

| 과정 | Pass% |
|------|-------|
| 보안 솔루션 운영 (secops-ai) | **82%** |
| SOC 심화 (soc-adv-ai) | **86%** |
| SOC 기초 (soc-ai) | 69% |
| AI 에이전트 IR 심화 (agent-ir-adv-ai) | **58%** |
| 컴플라이언스 | 58% |
| 클라우드/컨테이너 | 59% |

---

## API 엔드포인트

| 카테고리 | Method | Path | 기능 |
|---------|--------|------|------|
| **인증** | POST | `/auth/register` | 회원가입 |
| | POST | `/auth/login` | 로그인 (JWT) |
| **Training** | GET | `/training/courses` | 교과목 (랭크 제한 포함) |
| | GET | `/training/lecture/{id}/{week}` | 교안 Markdown |
| **Labs** | GET | `/labs/catalog/{lab_id}` | 실습 상세 (?admin=1 시 정답 포함) |
| | POST | `/labs/evaluate` | 채점 (텍스트 매치) |
| | POST | `/labs/auto-verify` | SubAgent 자동 검증 (실제 인프라 확인) |
| **Bastion** | POST | `/chat` | Bastion 프롬프트 실행 (NDJSON 스트림) |
| | GET | `/health` | Bastion 상태 |
| | GET | `/skills` | Skill 목록 |
| | GET | `/playbooks` | Playbook 목록 |
| **Battle** | POST | `/battles/create` | 대전 개설 |
| **CCCNet** | GET | `/cccnet/blocks` | 블록 조회 |
| **인프라** | POST | `/infras/setup` | VM 등록 |
| | POST | `/infras/onboard` | 온보딩 (SSE) |
| | POST | `/infras/verify` | 인프라 검수 (SSE) |

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Frontend | React 19, TypeScript, Vite |
| Database | PostgreSQL 15 (Docker) |
| LLM | Ollama (gpt-oss:120b, qwen3:8b, gemma3:4b) |
| Fine-tuning | unsloth, PEFT (QLoRA), trl, bitsandbytes |
| Security Stack | nftables, Suricata, ModSecurity CRS, Wazuh, OpenCTI |
| Auth | JWT (HS256) + API Key |
| Content | YAML (Lab 510개), Markdown (Lecture 255개) |
| Blockchain | CCCNet (SHA256, difficulty=3) |
| Container | Docker, docker-compose |
| AI Agent | Bastion (18 Skills, 8 Playbooks, Experience Layer) |

## 파일 구조

```
apps/
  ccc_api/src/main.py    — FastAPI API (2500+ lines)
  ccc-ui/src/            — React UI (Training, Cyber Range, Battle, Admin)
  bastion/               — Bastion Agent API (:8003)
  cli/                   — CLI 도구
packages/
  lab_engine/            — Lab 실행/검증 엔진 (SystemChecker 포함)
  battle_engine/         — 공방전 로직
  bastion/               — Agent 핵심 (18 Skills, Playbook, Experience, Prompt)
  manager_ai/            — LLM 연동
  student_manager/       — 학생 관리/진도/평가
contents/
  education/             — 17과목 × 15주 강의 (Markdown + 파일 참조 가이드)
  labs/                  — 17과목 × 15주 × 2 실습 (YAML, bastion_prompt 포함)
  playbooks/             — 정적 Playbook (8개 YAML)
  knowledge/             — RAG 지식 베이스
finetune/
  dataset/               — 파인튜닝 데이터셋 (safety_training, comprehensive_safety)
  scripts/               — QLoRA 파인튜닝 스크립트
  docs/                  — 파인튜닝 보고서
scripts/
  test_step.py           — Bastion 단일 스텝 검증 도구 (LLM 세맨틱 판정 포함)
  regen_secops_labs.py   — secops 실습 재생성기
  enrich_lectures.py     — 교안 파일 참조 가이드 자동 추가
  sync_nonai_to_ai.py    — Non-AI → AI 콘텐츠 동기화
docs/
  bastion-introduction.md    — Bastion 소개 (1페이지)
  bastion-test-report.md     — 실증 테스트 보고서
  ccc-v2-roadmap.md          — 로드맵
```

## License

MIT
