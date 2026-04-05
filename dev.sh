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

# Docker 설치 확인/자동 설치
ensure_docker() {
  if command -v docker &>/dev/null; then
    return 0
  fi

  echo "[CCC] Docker 미설치 — 자동 설치 중..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker "$(whoami)" 2>/dev/null || true
    echo "[CCC] Docker 설치 완료. 그룹 권한 적용을 위해 재로그인이 필요할 수 있습니다."
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y docker docker-compose-plugin
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$(whoami)" 2>/dev/null || true
  else
    echo "[CCC] ERROR: 패키지 매니저를 찾을 수 없습니다. Docker를 수동 설치하세요."
    echo "  https://docs.docker.com/get-docker/"
    exit 1
  fi
}

# DB 자동 시작 + 준비 대기
ensure_db() {
  ensure_docker

  # postgres 컨테이너 시작
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q ccc.*postgres; then
    echo "[CCC] Starting PostgreSQL..."
    docker compose -f docker/docker-compose.yaml up -d postgres 2>/dev/null || \
      docker-compose -f docker/docker-compose.yaml up -d postgres
  fi

  # DB 접속 가능할 때까지 대기 (최대 15초)
  local db_port
  db_port=$(echo "${DATABASE_URL:-postgresql://ccc:ccc@127.0.0.1:5434/ccc}" | grep -oP ':\K[0-9]+(?=/)')
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
