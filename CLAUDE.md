# CCC — Cyber Combat Commander

사이버보안 교육 플랫폼. 학생이 개별 인프라를 구축하고, 실습/CTF/대전을 수행한다.

## 아키텍처

| 컴포넌트 | 경로 | 포트 | 역할 |
|----------|------|------|------|
| ccc-api | apps/ccc-api/ | :9100 | 메인 API (학생/실습/CTF/대전) |
| ccc-ui | apps/ccc-ui/ | - | React 웹 UI |
| ccc-cli | apps/cli/ | - | 학생용 CLI |

## 패키지

| 패키지 | 역할 |
|--------|------|
| bastion | CCC 운영 관리 에이전트 (인프라 온보딩/헬스체크/SubAgent 통신) |
| manager_ai | Manager AI 시스템 (LLM 기반 분석/피드백) |
| student_manager | 학생 관리/진도/평가 |
| lab_engine | 실습 엔진 (YAML 시나리오) |
| battle_engine | 대전 엔진 (공방전) |

## 개발

```bash
# PostgreSQL
docker compose -f docker/docker-compose.yaml up -d

# API 서버
cp .env.example .env
./dev.sh api

# CLI
export PYTHONPATH=$(pwd)
python -m apps.cli.main students
```

## API 인증

모든 API 호출에 `X-API-Key` 헤더 필요.
기본 키: `ccc-api-key-2026`

## LLM 설정

```bash
LLM_BASE_URL=http://localhost:11434   # Ollama 서버 주소
LLM_MODEL=gemma3:4b                   # 사용 모델명
```
