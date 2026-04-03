# CCC — Cyber Combat Commander

사이버보안 교육 플랫폼. 학생이 개별 인프라를 구축하고, 실습/CTF/대전을 수행한다.

## 아키텍처

| 컴포넌트 | 경로 | 포트 | 역할 |
|----------|------|------|------|
| ccc-api | apps/ccc-api/ | :9100 | 메인 API (학생/실습/CTF/대전) |
| ccc-ui | apps/ccc-ui/ | - | React 웹 UI |
| ccc-cli | apps/cli/ | - | 학생용 CLI |

## 패키지

| 패키지 | 역할 | 마일스톤 |
|--------|------|---------|
| student_manager | 학생 관리/진도/평가 | M7 |
| lab_engine | 실습 엔진 (YAML 시나리오) | M7 |
| ctf_client | 중앙 CTF 클라이언트 | M7 |
| battle_engine | 대전 엔진 (공방전) | M8-M10 |
| infra_bootstrap | 학생 인프라 자동 구축 | M7 |

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

## 관련 시스템

- **opsclaw** (연구용): https://github.com/mrgrit/opsclaw
- **bastion** (실무용): https://github.com/mrgrit/bastion
- **중앙서버**: opsclaw 레포 내 `apps/central-server/` (:7000)
