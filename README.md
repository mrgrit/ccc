# CCC — Cyber Combat Commander

> 사이버보안 교육 플랫폼 — 교안, 실습, CTF, 공방전

CCC는 사이버보안 교육을 위한 통합 플랫폼이다. 12개 교과목의 교안과 360개 실습(Non-AI/AI), 시나리오 기반 공방전, 블록체인 실습 검증, 자동 채점을 제공한다.

## 주요 기능

### Education (교안 + 실습)
- **12개 교과목**: 공격, 보안운영, 웹취약점, 컴플라이언스, SOC, 클라우드, AI보안, AI안전, 자율보안, AI에이전트, 공방전 기초/심화
- **180개 교안**: 주차별 이론 + 실습 가이드 (25K~83K자)
- **360개 실습 YAML**: Non-AI (수동) + AI (자동) 각 15스텝, 정답 포함
- **4개 그룹**: 공격 기술 / 방어 운영 / AI 보안 / 실전

### Labs (문제 풀이 + 채점)
- 교과목별 문제 선택 → 15문제 풀기 → 자동 채점 → 점수
- 자동 검증: SubAgent로 학생 인프라 직접 확인 (조작 방지)
- 블록체인 기록: 검증 통과 시 PoW 블록 자동 생성
- 정답: admin만 열람 가능

### Battle (공방전)
- **시나리오 기반**: Red vs Blue 미션 수행
- **플로우**: 개설 → 참가(Red/Blue) → Ready → 미션 수행 → 채점 → 승패
- **실시간**: 타이머, 점수판, 이벤트 피드
- **블록체인**: 대전 결과 PoW 기록

### 인증
- 회원가입/로그인 (JWT)
- 역할: student / instructor / admin
- admin 전용: 정답 확인, 대전 개설

## 아키텍처

```
학생 (브라우저)
    |
    v
ccc-api (:9100)
    |-- Auth (JWT)
    |-- Education (교안 로드)
    |-- Labs (YAML 실습 + 채점)
    |-- Battle (시나리오 + 미션 + 점수)
    |-- Blockchain (PoW)
    |-- Leaderboard
    |
    v
student VM (SubAgent :8002)  -- 자동 검증
```

## 교과목 구성

| 그룹 | 과목 |
|------|------|
| **공격 기술** | 사이버 공격, 웹 취약점 |
| **방어 운영** | 보안 솔루션, 컴플라이언스, SOC, 클라우드 |
| **AI 보안** | AI/LLM 보안, AI Safety, 자율보안, AI 에이전트 |
| **실전** | 공방전 기초, 공방전 심화 |

각 과목: 15주 x Non-AI 실습 + AI 실습 = 30개 YAML (15스텝/주)

## Quick Start

```bash
# DB
docker compose -f docker/docker-compose.yaml up -d

# API
cp .env.example .env
./dev.sh api    # http://localhost:9100

# 관리자 계정 생성
curl -X POST http://localhost:9100/auth/create-admin \
  -H "Content-Type: application/json" \
  -d '{"student_id":"admin","name":"관리자","password":"admin2026"}'

# 접속: http://localhost:9100
```

## API

| Method | Path | 기능 |
|--------|------|------|
| POST | `/auth/register` | 회원가입 |
| POST | `/auth/login` | 로그인 (JWT) |
| GET | `/auth/me` | 내 프로필 |
| GET | `/education/courses` | 교과목 목록 (그룹별) |
| GET | `/education/courses/{id}/weeks` | 주차별 교안+실습 |
| GET | `/education/lecture/{id}/{week}` | 교안 내용 (markdown) |
| GET | `/labs/catalog` | 실습 목록 |
| GET | `/labs/catalog/{lab_id}` | 실습 상세 (?admin=true로 정답) |
| POST | `/labs/evaluate` | 실습 채점 |
| POST | `/labs/auto-verify` | SubAgent 자동 검증 |
| GET | `/battles/scenarios` | 대전 시나리오 |
| POST | `/battles/create` | 대전 개설 |
| POST | `/battles/{id}/join` | 참가 (Red/Blue) |
| POST | `/battles/{id}/ready` | Ready (양측 ready -> 시작) |
| GET | `/battles/{id}/my-missions` | 내 미션 + 점수 |
| POST | `/battles/{id}/submit-mission` | 미션 제출 |
| GET | `/leaderboard` | 리더보드 |

## 관련 시스템

| 시스템 | 역할 |
|--------|------|
| [OpsClaw](https://github.com/mrgrit/opsclaw) | 연구/개발 + 중앙서버 |
| [Bastion](https://github.com/mrgrit/bastion) | 실무 운영/보안 에이전트 |

## 기술 스택

Python 3.11 / FastAPI / PostgreSQL / React / YAML / JWT

## License

MIT
