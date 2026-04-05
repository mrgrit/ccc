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

# DB 자동 시작 + 준비 대기
ensure_db() {
  # docker 필수
  if ! command -v docker &>/dev/null; then
    echo "[CCC] ERROR: docker가 설치되어 있지 않습니다."
    echo "  설치: https://docs.docker.com/get-docker/"
    exit 1
  fi

  # postgres 컨테이너 시작
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q ccc.*postgres; then
    echo "[CCC] Starting PostgreSQL..."
    docker compose -f docker/docker-compose.yaml up -d postgres 2>/dev/null || \
      docker-compose -f docker/docker-compose.yaml up -d postgres
  fi

  # DB 접속 가능할 때까지 대기 (최대 15초)
  local db_host="${DATABASE_URL:-postgresql://ccc:ccc@127.0.0.1:5434/ccc}"
  local db_port=$(echo "$db_host" | grep -oP ':\K[0-9]+(?=/)')
  db_port="${db_port:-5434}"

  echo -n "[CCC] Waiting for PostgreSQL (port $db_port)..."
  for i in $(seq 1 15); do
    if pg_isready -h 127.0.0.1 -p "$db_port" -q 2>/dev/null || \
       bash -c "echo >/dev/tcp/127.0.0.1/$db_port" 2>/dev/null; then
      echo " ready"
      return 0
    fi
    echo -n "."
    sleep 1
  done
  echo " TIMEOUT"
  echo "[CCC] ERROR: PostgreSQL이 $db_port 포트에서 응답하지 않습니다."
  echo "  확인: docker ps | grep postgres"
  echo "  로그: docker logs \$(docker ps -qf name=postgres)"
  exit 1
}

case "${1:-api}" in
  api)
    ensure_db
    echo "[CCC] Starting ccc-api on :9100..."
    python3 -m uvicorn apps.ccc_api.src.main:app --host 0.0.0.0 --port 9100 --reload
    ;;
  bastion)
    ensure_db
    python3 -m apps.bastion.main
    ;;
  *)
    echo "Usage: ./dev.sh [api|bastion]"
    ;;
esac
