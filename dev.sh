#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# UTF-8 + venv
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8
export PYTHONIOENCODING=utf-8
[ -f .venv/bin/activate ] && source .venv/bin/activate

set -a; [ -f .env ] && source .env; set +a
export PYTHONPATH="$(pwd)"

case "${1:-api}" in
  api)
    echo "[CCC] Starting ccc-api on :9100..."
    python3 -m uvicorn apps.ccc-api.src.main:app --host 0.0.0.0 --port 9100 --reload
    ;;
  bastion)
    python3 -m apps.bastion.main
    ;;
  *)
    echo "Usage: ./dev.sh [api|bastion]"
    ;;
esac
