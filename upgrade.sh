#!/usr/bin/env bash
# CCC 업그레이드 — DB 보존하면서 코드 업데이트 + 재시작
set -euo pipefail
cd "$(dirname "$0")"

echo "=== CCC Upgrade ==="

# docker 권한
_docker() {
    if docker info &>/dev/null; then docker "$@"; else sudo docker "$@"; fi
}

# 1. 서비스 중지
echo "[1/5] 서비스 중지..."
pkill -f 'uvicorn apps.ccc_api' 2>/dev/null && echo "  API 중지됨" || echo "  API 미실행"

# 2. DB 백업 (보존)
echo "[2/5] DB 백업..."
mkdir -p db_backup
BACKUP_FILE="db_backup/backup_$(date +%Y%m%d_%H%M%S).sql"
if _docker ps --format '{{.Names}}' 2>/dev/null | grep -q postgres; then
    _docker exec "$(_docker ps -qf name=postgres)" pg_dump -U ccc ccc > "$BACKUP_FILE" 2>/dev/null && \
        echo "  백업 완료: $BACKUP_FILE" || echo "  백업 실패 (계속 진행)"
else
    echo "  DB 컨테이너 미실행 (스킵)"
fi

# 3. 코드 업데이트
echo "[3/5] 코드 업데이트..."
git stash 2>/dev/null || true
git pull --ff-only
git stash pop 2>/dev/null || true

# 4. 의존성 + UI 빌드
echo "[4/5] 의존성 + UI 빌드..."
[ -f .venv/bin/activate ] && source .venv/bin/activate
pip install -r requirements.txt -q
pip install open-interpreter --no-deps -q 2>/dev/null || true
cd apps/ccc-ui && npm install --silent && npm run build && cd ../..

# 5. 서비스 재시작
echo "[5/5] 서비스 재시작..."
source .venv/bin/activate 2>/dev/null || true
set -a; [ -f .env ] && source .env; set +a
export PYTHONPATH="$(pwd)"

# DB 컨테이너 확인/시작
if ! _docker ps --format '{{.Names}}' 2>/dev/null | grep -q postgres; then
    if _docker compose version &>/dev/null; then
        _docker compose -f docker/docker-compose.yaml up -d postgres
    else
        sudo docker-compose -f docker/docker-compose.yaml up -d postgres
    fi
    echo -n "  DB 대기..."
    for i in $(seq 1 15); do
        if bash -c "echo >/dev/tcp/127.0.0.1/${DB_PORT:-5434}" 2>/dev/null; then
            echo " ready"; break
        fi
        echo -n "."; sleep 1
    done
fi

# API 시작 (PYTHONPATH 명시)
PYTHONPATH="$(pwd)" nohup .venv/bin/python3 -m uvicorn apps.ccc_api.src.main:app --host 0.0.0.0 --port 9100 > /tmp/ccc-api.log 2>&1 &
sleep 2

if curl -s http://localhost:9100/api/health > /dev/null 2>&1; then
    echo "  API 정상 기동 (PID: $!)"
else
    echo "  API 시작 실패 — 로그 확인: tail /tmp/ccc-api.log"
fi

echo ""
echo "=== 업그레이드 완료 ==="
echo "  백업: $BACKUP_FILE"
echo "  접속: http://$(hostname -I | awk '{print $1}'):9100/app/"
