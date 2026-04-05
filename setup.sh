#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== CCC Setup ==="

# 1. 시스템 패키지
echo "[1/5] 시스템 패키지 설치..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv nodejs npm sshpass
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip nodejs npm sshpass
fi

# 2. Python 의존성
echo "[2/5] Python 의존성 설치..."
pip3 install --user -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# 3. UI 빌드
echo "[3/5] UI 빌드..."
cd apps/ccc-ui
npm install
npm run build
cd ../..

# 4. 환경 설정
echo "[4/5] 환경 설정..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  .env 생성됨 — LLM_BASE_URL과 LLM_MODEL을 환경에 맞게 수정하세요"
else
    echo "  .env 이미 존재"
fi

# 5. PostgreSQL (Docker)
echo "[5/5] PostgreSQL..."
if command -v docker &>/dev/null; then
    docker compose -f docker/docker-compose.yaml up -d postgres
    echo "  PostgreSQL 시작됨 (port ${DB_PORT:-5434})"
else
    echo "  Docker 미설치 — PostgreSQL을 수동으로 설정하세요"
    echo "  DB URL: postgresql://ccc:ccc@127.0.0.1:5434/ccc"
fi

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "실행:"
echo "  ./dev.sh api          # API 서버 (:9100)"
echo "  브라우저: http://localhost:9100/app/"
echo ""
echo "설정 (.env):"
echo "  LLM_BASE_URL=http://your-ollama-server:11434"
echo "  LLM_MODEL=gemma3:4b"
