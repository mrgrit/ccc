#!/usr/bin/env bash
# deploy-ccc.sh — CCC 배포
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[CCC] Stopping..."
fuser -k 9100/tcp 2>/dev/null || true
sleep 1

echo "[CCC] Building UI..."
cd apps/ccc-ui && npm install --silent && npm run build && cd ../..

echo "[CCC] Starting ccc-api on :9100..."
set -a && [ -f .env ] && source .env; set +a
export PYTHONPATH="$(pwd)"
export DATABASE_URL="${DATABASE_URL:-postgresql://opsclaw:opsclaw@127.0.0.1:5432/ccc}"
export CCC_API_KEY="${CCC_API_KEY:-ccc-api-key-2026}"
nohup python3.11 -m uvicorn apps.ccc-api.src.main:app \
  --host 0.0.0.0 --port 9100 --log-level warning > /tmp/ccc.log 2>&1 &

sleep 2
curl -s http://localhost:9100/health && echo " [OK]"
