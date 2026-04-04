#!/usr/bin/env bash
# CCC (Cyber Combat Commander) — 독립 설치 스크립트
# Usage: curl -sL https://raw.githubusercontent.com/mrgrit/ccc/main/install.sh | bash
set -euo pipefail

echo "========================================"
echo "  CCC — Cyber Combat Commander"
echo "  독립 설치 스크립트"
echo "========================================"

# 1. 요구사항 확인
echo "[1/5] 요구사항 확인..."
command -v docker >/dev/null || { echo "ERROR: docker 필요. https://docs.docker.com/get-docker/"; exit 1; }
command -v docker compose >/dev/null 2>&1 || command -v docker-compose >/dev/null || { echo "ERROR: docker compose 필요"; exit 1; }

# 2. 레포 클론
echo "[2/5] CCC 다운로드..."
if [ -d "ccc" ]; then
  echo "  기존 ccc 디렉토리 발견 — git pull"
  cd ccc && git pull
else
  git clone https://github.com/mrgrit/ccc.git
  cd ccc
fi

# 3. 환경 설정
echo "[3/5] 환경 설정..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  .env 생성 완료 (필요 시 수정)"
fi

# 4. Docker 기동
echo "[4/5] Docker 컨테이너 기동..."
docker compose -f docker/docker-compose.yaml up -d --build

# 5. 초기 관리자 계정
echo "[5/5] 초기 관리자 계정 생성..."
sleep 5
curl -s -X POST http://localhost:9100/auth/create-admin \
  -H "Content-Type: application/json" \
  -d '{"student_id":"admin","name":"관리자","password":"admin2026"}' > /dev/null 2>&1 || echo "  (관리자 이미 존재)"

echo ""
echo "========================================"
echo "  CCC 설치 완료!"
echo ""
echo "  접속: http://localhost:9100"
echo "  관리자: admin / admin2026"
echo ""
echo "  교안 경로: contents/education/"
echo "  실습 경로: contents/labs/"
echo "========================================"
