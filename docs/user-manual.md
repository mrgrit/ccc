# CCC 사용자 매뉴얼

> Cyber Combat Commander — 사이버보안 교육 훈련 플랫폼
> 버전: 2026.04 | 최종 업데이트: 2026-04-18

---

## 목차

1. [시스템 소개](#1-시스템-소개)
2. [CCC 설치](#2-ccc-설치)
3. [초기 인프라 구축](#3-초기-인프라-구축)
4. [사용법 — 학생](#4-사용법--학생)
5. [사용법 — 강사/관리자](#5-사용법--강사관리자)
6. [Bastion AI 에이전트](#6-bastion-ai-에이전트)
7. [문제 해결](#7-문제-해결)

---

## 1. 시스템 소개

### CCC란?

CCC(Cyber Combat Commander)는 사이버보안 실무 능력을 체계적으로 훈련하는 교육 플랫폼입니다.

학생은 자신의 PC에 가상 인프라(VM)를 구축하고, 17개 교과목의 교안을 학습하며, 실제 서버에서 방화벽 설정, 침입 탐지, 공격 시뮬레이션, 로그 분석 등을 직접 수행합니다.

### 핵심 특징

| 특징 | 설명 |
|------|------|
| **실습 중심** | 510개 실습 과제 — 명령어를 직접 입력하고 결과를 확인 |
| **AI 에이전트** | Bastion에 프롬프트를 입력하면 AI가 보안 작업 수행 |
| **개별 인프라** | 학생마다 자신의 VM 환경을 구축하여 자유롭게 실습 |
| **자동 채점** | 학생 인프라에 직접 접속하여 실제 설정 반영 여부 검증 |
| **블록체인 성과** | 실습/CTF/공방전 활동이 블록체인에 기록되어 투명한 평가 |
| **공방전** | Red Team vs Blue Team 실시간 대전 |

### 교과목 구성 (17개)

| 그룹 | 교과목 | 난이도 |
|------|--------|--------|
| **공격 기술** | 사이버 공격 기초, 사이버 공격 심화, 웹 취약점 | 초급~고급 |
| **방어 운영** | 보안 솔루션 운영, 컴플라이언스, SOC 기초/심화, 클라우드/컨테이너 | 초급~중급 |
| **AI 보안** | AI/LLM 보안, AI Safety 기초/심화, AI 에이전트, 자율보안/시스템 | 중급~고급 |
| **실전** | 공방전 기초/심화, 물리보안/모의해킹 | 초급~고급 |

각 교과목은 **15주차**로 구성되며, 주차별로:
- 📖 **교안** (Markdown) — 이론 + 실습 가이드
- 📝 **Non-AI 실습** — 학생이 직접 CLI/UI로 수행
- 🤖 **AI 실습** — Bastion에 프롬프트를 입력하여 AI가 수행

### 시스템 구조

```
학생 (브라우저)
    │
    ▼
CCC 서버 (:9100)
    ├── Training     — 교안 + 실습
    ├── Cyber Range  — 과제 풀이 + 자동 채점
    ├── Battlefield  — Red vs Blue 공방전
    ├── Leaderboard  — 순위표
    ├── My Infra     — VM 온보딩
    └── 검색         — 키워드로 전체 콘텐츠 검색

학생 VM 인프라 (VMware)
    ├── attacker  — 공격 도구 (nmap, hydra, sqlmap)
    ├── secu      — 방화벽 + IDS (nftables, Suricata)
    ├── web       — 웹서버 + WAF (Apache, ModSecurity, JuiceShop)
    ├── siem      — SIEM + CTI (Wazuh, OpenCTI)
    └── manager   — AI 에이전트 (Bastion, Ollama)
```

---

## 2. CCC 설치

### 2.1 시스템 요구사항

**CCC 서버 (강사/관리자용)**

| 항목 | 최소 | 권장 |
|------|------|------|
| OS | Ubuntu 22.04+ | Ubuntu 24.04 |
| CPU | 4코어 | 8코어 |
| RAM | 8GB | 16GB |
| 디스크 | 50GB | 100GB |
| Python | 3.10+ | 3.12 |
| Node.js | 18+ | 20+ |
| Docker | 필수 | 최신 |
| PostgreSQL | 15+ | 15+ (Docker) |

**학생 PC (실습 인프라용)**

| 항목 | 최소 | 권장 |
|------|------|------|
| CPU | 8코어 | 12코어+ |
| RAM | 16GB | 32GB+ |
| 디스크 | 100GB 여유 | 200GB+ |
| 가상화 | VMware Workstation/Player | VMware Workstation Pro |
| 네트워크 | CCC 서버 접근 가능 | 같은 네트워크 |

**GPU 서버 (AI 기능용, 선택)**

| 항목 | 최소 | 권장 |
|------|------|------|
| GPU | NVIDIA 8GB+ VRAM | NVIDIA 24GB+ |
| 소프트웨어 | Ollama | Ollama + CUDA |
| 모델 | gemma3:4b (3.3GB) | gpt-oss:120b (65GB) |

### 2.2 CCC 서버 설치

```bash
# 1. 저장소 클론
git clone https://github.com/mrgrit/ccc.git
cd ccc

# 2. 자동 설치 (Python, Node.js, Docker, PostgreSQL 포함)
bash setup.sh

# 3. 환경 설정
cp .env.example .env
# .env 파일을 열어 다음을 수정:
#   DATABASE_URL    — PostgreSQL 연결 정보
#   LLM_BASE_URL    — Ollama 서버 주소
#   JWT_SECRET      — JWT 비밀키 (운영 환경에서 반드시 변경)

# 4. PostgreSQL 시작
docker compose -f docker/docker-compose.yaml up -d postgres

# 5. CCC 서버 시작
./dev.sh api
# → http://서버IP:9100/app/ 에서 접속
```

### 2.3 관리자 계정 생성

```bash
# 초기 관리자 계정 생성
curl -X POST http://localhost:9100/api/auth/create-admin \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ccc-api-key-2026" \
  -d '{"student_id": "admin", "password": "admin1234", "name": "관리자"}'
```

브라우저에서 `http://서버IP:9100/app/` 접속 → admin / admin1234 로 로그인.

### 2.4 Ollama (AI 기능) 설치

AI 실습, AI 튜터, Bastion 에이전트를 사용하려면 Ollama가 필요합니다.

```bash
# GPU 서버 또는 CCC 서버에서:
curl -fsSL https://ollama.com/install.sh | sh

# 모델 다운로드 (용량에 따라 선택)
ollama pull gemma3:4b      # 3.3GB — 최소 모델
ollama pull qwen3:8b       # 5.2GB — SubAgent용
# ollama pull gpt-oss:120b # 65GB — 고성능 (GPU 24GB+ 필요)

# .env에 설정
# LLM_BASE_URL=http://GPU서버IP:11434
# LLM_MANAGER_MODEL=gemma3:4b
# LLM_SUBAGENT_MODEL=qwen3:8b
```

### 2.5 Docker 배포 (운영 환경)

```bash
# Docker Compose로 전체 배포
docker compose -f docker/docker-compose.yaml up -d

# 또는 개별 빌드
docker build -t ccc-api .
docker run -d -p 9100:9100 --env-file .env ccc-api
```

---

## 3. 초기 인프라 구축

### 3.1 VM 준비

학생은 VMware에 5~6대의 VM을 생성합니다. 각 VM은 역할별로 다른 보안 솔루션이 설치됩니다.

**VM 생성 순서:**

| 순서 | VM 이름 | OS | 역할 | RAM | 디스크 |
|------|---------|-----|------|-----|--------|
| 1 | secu | Ubuntu 22.04 | 방화벽 + IDS | 2GB | 20GB |
| 2 | web | Ubuntu 22.04 | 웹서버 + WAF | 2GB | 20GB |
| 3 | siem | Ubuntu 22.04 | SIEM + CTI | 4GB | 40GB |
| 4 | attacker | Kali Linux | 공격 도구 | 2GB | 30GB |
| 5 | manager | Ubuntu 22.04 | Bastion + Ollama | 2GB | 20GB |

### 3.2 네트워크 설정

각 VM에 **2개의 네트워크 인터페이스**를 설정합니다:

| 인터페이스 | 유형 | 용도 | IP 대역 |
|-----------|------|------|---------|
| ens33 | NAT/Bridged | 외부 통신 (SSH, 패키지 설치) | 192.168.x.x (DHCP) |
| ens37 | Host-Only | 실습 내부 네트워크 | 10.20.30.x (고정) |

**내부 IP 할당:**

| VM | 내부 IP | 설정 방법 |
|----|---------|----------|
| secu | 10.20.30.1 | `sudo ip addr add 10.20.30.1/24 dev ens37` |
| web | 10.20.30.80 | `sudo ip addr add 10.20.30.80/24 dev ens37` |
| siem | 10.20.30.100 | `sudo ip addr add 10.20.30.100/24 dev ens37` |
| attacker | 10.20.30.201 | `sudo ip addr add 10.20.30.201/24 dev ens37` |
| manager | 10.20.30.200 | `sudo ip addr add 10.20.30.200/24 dev ens37` |

> IP 대역은 `.env`에서 변경 가능합니다 (`VM_SECU_IP`, `VM_WEB_IP` 등).

### 3.3 CCC 온보딩

VM이 준비되면 CCC 웹에서 **자동 온보딩**을 실행합니다.

1. **CCC 로그인** → **My Infra** 메뉴
2. **VM 등록**: 각 VM의 외부 IP, SSH 계정/비밀번호 입력
3. **온보딩 시작**: "온보딩" 버튼 클릭

온보딩이 자동으로 수행하는 작업:

| VM | 설치되는 솔루션 |
|----|----------------|
| secu | nftables 방화벽, Suricata IDS, NAT 설정, Wazuh Agent |
| web | Apache, ModSecurity CRS, JuiceShop, DVWA, Wazuh Agent |
| siem | Wazuh Manager/Indexer/Dashboard, OpenCTI, rsyslog 수집 |
| attacker | nmap, hydra, sqlmap, nikto (대부분 Kali에 기본 포함) |
| manager | SubAgent, Bastion API |

4. **검수**: 42개 항목 자동 체크 (서비스 상태, 네트워크 연결, 로그 수집 등)

### 3.4 온보딩 후 확인

```bash
# 각 VM에서 확인
# secu
ssh ccc@secu_ip
sudo nft list tables          # nftables 테이블 확인
sudo systemctl status suricata  # Suricata 상태

# siem
ssh ccc@siem_ip
sudo systemctl status wazuh-manager  # Wazuh 상태
# 브라우저: https://siem_ip:443 (admin/admin)

# web
ssh ccc@web_ip
sudo systemctl status apache2      # Apache 상태
curl http://localhost:3000          # JuiceShop 접속
```

---

## 4. 사용법 — 학생

### 4.1 회원가입 및 로그인

1. 브라우저에서 `http://CCC서버IP:9100/app/` 접속
2. **Register** 탭에서 학번, 이름, 비밀번호 입력하여 가입
3. (Google 계정 연동이 설정된 경우) **Google로 로그인** 버튼 사용 가능

### 4.2 Training (교안 + 실습)

1. 왼쪽 메뉴 **Training** 클릭
2. 교과목 카드에서 원하는 과목 선택
3. 주차별 목록에서:
   - 📖 **교안** — 이론 학습 + 실습 가이드 읽기
   - 📝 **Non-AI 실습** — 직접 명령어 입력하여 수행
   - 🤖 **AI 실습** — Bastion 프롬프트가 표시됨

**Non-AI 실습 수행 방법:**
- 교안의 명령어를 해당 VM의 터미널에서 직접 실행
- 결과를 확인하고 다음 단계 진행
- UI가 있는 도구(Wazuh Dashboard, OpenCTI)는 브라우저에서 조작

**AI 실습 수행 방법:**
- 각 스텝에 초록색 박스로 표시된 **bastion_prompt**를 복사
- Bastion 채팅(또는 API)에 붙여넣기
- Bastion이 실행한 결과를 확인

### 4.3 Cyber Range (과제 풀이)

1. 왼쪽 메뉴 **Cyber Range** 클릭
2. 교과목 → 실습 선택
3. 각 스텝의 문제를 읽고 답을 입력
4. **5스텝씩 그룹 제출** → 자동 채점
5. 채점 시 **학생 인프라에 직접 접속**하여 실제 설정 반영 여부 확인

### 4.4 Battlefield (공방전)

1. 왼쪽 메뉴 **Battlefield** 클릭
2. 대전 목록에서 참가 또는 개설
3. **Red Team**: 주어진 시간 내 대상 시스템 공격
4. **Blue Team**: 공격을 탐지하고 차단
5. 판정: 공격 성공/탐지/차단 여부로 점수 산정

### 4.5 검색

왼쪽 사이드바 상단의 **검색창**에 키워드 입력:
- 2글자 이상 입력 → 🔍 클릭 또는 Enter
- 교안/AI실습/Non-AI실습 전체에서 검색
- 결과 클릭 시 해당 페이지로 바로 이동

### 4.6 승급 시스템

| 랭크 | 조건 | 접근 가능 교과목 |
|------|------|-----------------|
| **Rookie** | 가입 시 기본 | 초급 과목 (공격 기초, SOC 기초 등) |
| **Skilled** | Lab 10개+ 완료 | 중급 과목 (AI 보안, 클라우드 등) |
| **Expert** | Lab 30개+ 완료 + CTF 5개+ | 고급 과목 (공격 심화, 공방전 심화 등) |
| **Elite** | Expert + Battle 10승+ | 모든 교과목 |

---

## 5. 사용법 — 강사/관리자

### 5.1 Admin 페이지

왼쪽 메뉴 **Admin** (admin 계정만 표시):

| 기능 | 설명 |
|------|------|
| **학생 관리** | 학생 목록, 그룹 배정, 승급/강등 |
| **그룹 관리** | 반/조 생성, 학생 배정 |
| **콘텐츠 검수** | Lab 콘텐츠 자동 검증 실행 |
| **정답 보기** | Training/Cyber Range에서 각 스텝의 정답 확인 (admin 전용) |

### 5.2 정답 확인

1. **Training** 또는 **Cyber Range**에서 실습 열기
2. 상단에 **Answers (Admin)** 버튼이 표시됨
3. 클릭하면 각 스텝의 정답이 표시:
   - 🤖 **프롬프트**: AI 실습용 bastion_prompt
   - 📎 **참고 (CLI)**: 명령어 기반 정답
   - 🖥️ **UI**: UI에서 확인하는 방법

### 5.3 교안 수정

교안은 `contents/education/과목명/weekNN/lecture.md` 파일입니다.

```bash
# 교안 편집
vi contents/education/course2-security-ops/week01/lecture.md

# 다이어그램은 Mermaid 문법 사용 가능
# ```mermaid
# graph LR
#     A --> B --> C
# ```
```

### 5.4 실습 수정

실습은 `contents/labs/과목-ai/weekNN.yaml` 파일입니다.

```yaml
# YAML 구조
lab_id: secops-ai-week01
title: 보안 솔루션 인프라 점검 (AI 지원)
steps:
  - order: 1
    instruction: "secu VM의 nftables 테이블 목록을 확인하시오."
    bastion_prompt: "secu VM의 nftables 테이블 목록을 확인해줘"
    verify:
      type: output_contains
      expect: table
    target_vm: secu
```

---

## 6. Bastion AI 에이전트

### 6.1 Bastion이란?

Bastion은 프롬프트 하나로 보안 운영 작업을 수행하는 AI 에이전트입니다.

```
학생: "Suricata 상태 확인해줘"
     ↓
Bastion: Planning → Skill 선택(check_suricata) → secu VM 실행 → 결과 분석
     ↓
학생에게: "Suricata active, 최근 알림 5건, ..."
```

### 6.2 사용 방법

**TUI (터미널):**
```bash
cd /path/to/ccc
./dev.sh bastion
# 대화형 인터페이스에서 프롬프트 입력
```

**API:**
```bash
curl -X POST http://bastion:8003/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "방화벽 룰셋 확인해줘", "auto_approve": true}'
```

### 6.3 할 수 있는 작업 (18개 Skill)

| 카테고리 | 예시 프롬프트 |
|----------|-------------|
| **인프라 점검** | "전체 인프라 상태 확인해줘" |
| **방화벽** | "SSH 포트만 허용하고 나머지 차단해줘" |
| **IDS/IPS** | "Suricata에 SQL Injection 탐지 룰 추가해줘" |
| **SIEM** | "Wazuh 최근 알림 분석해줘" |
| **WAF** | "ModSecurity 상태 확인해줘" |
| **공격 시뮬레이션** | "web VM에 SQL Injection 시도해줘" |
| **로그 분석** | "suricata eve.json에서 의심 활동 분석해줘" |
| **LLM 테스트** | "temperature 0.0으로 프롬프트 전송해줘" |

### 6.4 자기 수정 기능

Bastion은 실행이 실패하면 **자동으로 에러를 분석하고 수정된 명령으로 재시도**합니다.

```
1차 시도: cat /etc/suricata2/suricata.yaml → 실패 (경로 없음)
     ↓ LLM이 에러 분석
2차 시도: cat /etc/suricata/suricata.yaml → 성공!
```

---

## 7. 문제 해결

### 7.1 자주 묻는 질문

**Q: CCC 서버에 접속이 안 됩니다**
```bash
# 서버 상태 확인
ps -ef | grep uvicorn
# 포트 확인
ss -tlnp | grep 9100
# 재시작
./dev.sh api
```

**Q: VM 온보딩이 실패합니다**
```bash
# SSH 접속 확인
ssh ccc@VM_IP
# SubAgent 상태 확인
curl http://VM_IP:8002/health
# 수동 재설치
bash setup_subagent.sh VM_IP
```

**Q: Bastion이 응답하지 않습니다**
```bash
# Bastion 상태
curl http://bastion:8003/health
# Ollama 상태
curl http://GPU_IP:11434/api/tags
# 재시작
./dev.sh bastion
```

**Q: Wazuh Dashboard에 접속이 안 됩니다**
- 브라우저: `https://SIEM_IP:443`
- 기본 계정: admin / admin
- 자체 서명 인증서 → "계속" 클릭

**Q: 실습에서 IP가 틀립니다**
- `.env` 파일에서 `VM_*_IP` 환경변수를 자신의 인프라에 맞게 수정
- 실습 instruction의 `{{SECU_IP}}` 등은 자동으로 치환됨

### 7.2 로그 위치

| 컴포넌트 | 로그 위치 |
|----------|----------|
| CCC API | 터미널 stdout (uvicorn) |
| Bastion | `/tmp/bastion_api.log` |
| Suricata | `/var/log/suricata/eve.json` (secu VM) |
| Wazuh | `/var/ossec/logs/alerts/alerts.json` (siem VM) |
| ModSecurity | `/var/log/apache2/modsec_audit.log` (web VM) |
| Apache | `/var/log/apache2/access.log` (web VM) |

### 7.3 지원

- GitHub Issues: https://github.com/mrgrit/ccc/issues
- 이메일: mrgrit@ync.ac.kr

---

> CCC — 프롬프트 하나로 보안 운영을 배우는 새로운 방법
