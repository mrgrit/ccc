#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

set -a; [ -f .env ] && source .env; set +a
export PYTHONPATH="$(pwd)"

case "${1:-api}" in
  api)
    echo "[CCC] Starting ccc-api on :9100..."
    python -m uvicorn apps.ccc-api.src.main:app --host 0.0.0.0 --port 9100 --reload
    ;;
  *)
    echo "Usage: ./dev.sh [api]"
    ;;
esac
