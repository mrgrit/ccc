# CCC — Cyber Combat Commander

> 사이버보안 교육 훈련 플랫폼 — 15개 교과목, 450개 실습, 공방전, 블록체인 성과 관리

## Quick Start

```bash
# 1. 설치 (시스템 패키지 + Python + Node.js + Docker + PostgreSQL)
bash setup.sh

# 2. 실행
./dev.sh api          # http://<IP>:9100/app/
# 관리자: admin / admin1234

# 3. 업그레이드
bash upgrade.sh

# 4. Docker 독립 배포
docker compose -f docker/docker-compose.yaml up -d
```

## 아키텍처

```
학생 (브라우저)
    |
    v
CCC Central (:9100)
    ├── Training (교안 + 실습 통합)
    ├── Labs (시험 모드)
    ├── Battle (공방전 Red vs Blue)
    ├── CCCNet (블록체인 성과)
    ├── CTF (AI 자동 출제)
    ├── AI Tutor (챗봇)
    ├── Admin (그룹/학생/승급/검수)
    └── My Infra (VM 온보딩 + 검수)
          |
          v
    학생 인프라 (5~6대 VM)
    ├── attacker (10.20.30.201) — nmap, metasploit, sqlmap, hydra
    ├── secu    (10.20.30.1)   — nftables, suricata IDS
    ├── web     (10.20.30.80)  — apache2, modsecurity, JuiceShop, DVWA
    ├── siem    (10.20.30.100) — wazuh-manager, 로그 수집
    ├── manager (10.20.30.200) — Ollama LLM, bastion
    └── windows (10.20.30.50)  — 선택사항
```

### 트래픽 흐름
```
Attacker → SECU(nftables → suricata) → WEB(modsecurity → apache) → SIEM(wazuh)
```

## 교과목 (15개)

| 그룹 | 과목 | 랭크 |
|------|------|------|
| **공격 기술** | 사이버 공격, 웹 취약점, 공격 심화 | rookie / rookie / expert |
| **방어 운영** | 보안 솔루션, 컴플라이언스, SOC, SOC 심화 | rookie |
| **AI 보안** | AI/LLM 보안, AI Safety, 자율보안, AI 에이전트, AI Safety 심화 | skilled / expert |
| **실전** | 공방전 기초, 공방전 심화 | rookie / expert |

- 15주 × 15과목 = **225주** 교안 (Markdown)
- 15주 × 15과목 × 2(Non-AI + AI) = **450개** 실습 (YAML)
- 과목별 최소 랭크 — `rookie` → `skilled` → `expert`

## 주요 기능

### V1: 그룹 / 역할 / 승급
- 역할: Commander(admin), Trainer, Trainee(rookie→elite)
- 자동 승급: Lab/CTF/Battle 완료 → 조건 충족 시 자동 승급
- Admin 페이지: 그룹 관리, 학생 배정, 승급 실행

### V2: AI 피드백
- Dashboard "AI 피드백 받기" → 학습 분석 + 개인화 추천
- `/user/stats` (종합 통계) + `/user/ai-feedback` (LLM 분석)

### V3: CCCNet 블록체인
- 활동별 자동 블록 생성: lab_complete(50pt), ctf_solve, battle_join(20pt), battle_win(50pt), rank_up(1000pt), bug_report(100pt)
- 블록 검증, 리더보드, 통계

### V4: 인프라
- 온보딩: UI에서 IP 입력 → 자동 설정 (secu→siem→web→attacker→manager 순서)
- 보안 스택: nftables + suricata + modsecurity + wazuh + rsyslog
- 온보딩 검수: 42개 항목 자동 체크 (서비스 상태, 룰, 로그, 네트워크 E2E)

### V5: Manager AI
- Ollama LLM 연동 (`/manager/execute`)
- 시스템 프롬프트 동적 조합 + 학생별 컨텍스트 주입

### V6: CTF 자동 출제
- `/ctf/generate` — LLM이 교안 기반으로 CTF 문제 생성
- 블록체인 참가 자격 (최소 블록 수)

### V7: Training + Labs 통합
- Training: 교안 읽기 + 실습 제출 통합 (과목 카드에 랭크 뱃지)
- Labs: 시험 모드 (5 step 그룹별 부분 제출)

### V8: AI 챗봇
- 모든 페이지 우하단 플로팅 챗봇
- 사용법 안내, 학습 질의응답

### V9: 독립 배포
- Multi-stage Dockerfile (Node.js UI 빌드 → Python API)
- `docker-compose.yaml` (PostgreSQL + API)

## Lab 검증

배포 후 품질 확인:

```
Admin > Lab Verify > Run Lab Verify
→ week 1, 8, 15 샘플 자동 검증
→ 비AI 10과목 88% 통과 (312/355)
```

## API 엔드포인트

| 카테고리 | Method | Path | 기능 |
|---------|--------|------|------|
| **인증** | POST | `/auth/register` | 회원가입 |
| | POST | `/auth/login` | 로그인 (JWT) |
| | POST | `/auth/create-admin` | 관리자 생성 |
| **Training** | GET | `/training/courses` | 교과목 (min_rank 포함) |
| | GET | `/training/courses/{id}/weeks` | 주차별 교안+실습 |
| | GET | `/training/lecture/{id}/{week}` | 교안 Markdown |
| **Labs** | GET | `/labs/catalog` | 실습 목록 |
| | POST | `/labs/evaluate` | 채점 |
| | POST | `/labs/auto-verify` | SubAgent 자동 검증 |
| | POST | `/labs/verify-all` | Lab 콘텐츠 검증 (SSE) |
| **Battle** | POST | `/battles/create` | 대전 개설 |
| | POST | `/battles/{id}/end` | 종료 + 블록체인 |
| **CCCNet** | GET | `/cccnet/blocks` | 블록 조회 |
| | GET | `/cccnet/stats` | 통계 |
| | GET | `/cccnet/verify` | 체인 검증 |
| **승급** | GET | `/rank/check/{id}` | 승급 조건 확인 |
| | POST | `/rank/promote/{id}` | 승급 실행 |
| **인프라** | POST | `/infras/setup` | VM 등록 |
| | POST | `/infras/onboard` | 온보딩 (SSE) |
| | POST | `/infras/verify` | 인프라 검수 (SSE) |
| **AI** | POST | `/chat` | AI 튜터 챗봇 |
| | POST | `/ctf/generate` | CTF 자동 출제 |
| | GET | `/user/ai-feedback` | AI 학습 피드백 |

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Frontend | React 19, TypeScript, Vite |
| Database | PostgreSQL 15 (Docker) |
| LLM | Ollama (외부/로컬) |
| Security | nftables, Suricata, ModSecurity, Wazuh |
| Auth | JWT (HS256) + API Key |
| Content | YAML (Lab), Markdown (Lecture) |
| Blockchain | CCCNet (SHA256, difficulty=3) |
| Container | Docker, docker-compose |

## 파일 구조

```
apps/
  ccc_api/src/main.py    — FastAPI API (2500+ lines)
  ccc-ui/src/            — React UI
  bastion/               — 관리 에이전트 (open-interpreter)
  cli/                   — CLI 도구
packages/
  lab_engine/            — YAML Lab 실행/검증 엔진
  battle_engine/         — 대전 로직
  bastion/               — 온보딩, 검수, Lab 검증
  manager_ai/            — LLM 연동
contents/
  education/             — 15과목 × 15주 강의 (Markdown)
  labs/                  — 15과목 × 15주 × 2(nonai/ai) 실습 (YAML)
docker/
  docker-compose.yaml    — PostgreSQL + API
```

## License

MIT
