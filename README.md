# CCC — Cyber Combat Commander

> 사이버보안 교육 플랫폼: CTF, 실습, 대전

## Features

- **실습 엔진**: YAML 기반 시나리오, 자동 검증, 블록체인 기록
- **CTF**: 중앙서버 연동 CTF (공격/방어/인프라/AI)
- **대전 모드**: 학생 인프라 간 공방전, 실시간 시각화, 관전
- **리더보드**: 실습 + CTF + 대전 종합 랭킹
- **Non-AI / AI**: 수동 실습 + bastion AI 에이전트 연동

## Quick Start

```bash
# DB
docker compose -f docker/docker-compose.yaml up -d

# API
cp .env.example .env
./dev.sh api

# 학생 등록
curl -X POST http://localhost:9100/students \
  -H "X-API-Key: ccc-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"student_id":"2026001","name":"홍길동"}'
```

## Architecture

```
CCC Central (:9100)
├── Students → 학생 등록/관리/진도
├── Labs     → 실습 시작/제출/검증 → PoW 블록
├── CTF      → 중앙서버 연동 문제/제출/스코어보드
├── Battle   → 대전 생성/시작/종료 → WebSocket 실시간
└── AI       → bastion 연동 AI 실습 (M9)
```

## License

MIT
