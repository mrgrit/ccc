#!/bin/bash
# eg-6v6 deploy on 192.168.0.110
# 사용자 (Admin) 가 0.110 으로 SSH 후 실행. CCC repo 에서 rsync 또는 0.110 에서 직접 git pull.

set -euo pipefail

EG_HOST="${EG_HOST:-192.168.0.110}"
EG_USER="${EG_USER:-ccc}"
EG_ROOT="${EG_ROOT:-/home/ccc/eg-6v6}"
EG_DB="${EG_DB:-$EG_ROOT/data/eg-6v6.db}"
ADMIN_TOKEN="${EG_ADMIN_TOKEN:-}"

if [ -z "$ADMIN_TOKEN" ]; then
  echo "[ERROR] EG_ADMIN_TOKEN 환경변수 필수 (운영자 인증 토큰)"
  exit 1
fi

cmd="$1"; shift || true

case "$cmd" in
  bootstrap)
    # 0.110 에서 1 회 실행 — 디렉토리 + 6bq5 clone + Python venv
    echo "[bootstrap] $EG_ROOT 준비"
    mkdir -p "$EG_ROOT"/{data,logs}
    cd "$EG_ROOT"
    if [ ! -d 6bq5 ]; then
      git clone https://github.com/mrgrit/6bq5.git
    else
      cd 6bq5 && git pull && cd ..
    fi
    cd 6bq5
    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    .venv/bin/pip install -q -r backend/requirements.txt pyyaml
    echo "[bootstrap] OK"
    ;;

  sync-catalog)
    # CCC 머신에서 카탈로그 / 스크립트 0.110 으로 rsync
    echo "[sync-catalog] CCC → $EG_HOST:$EG_ROOT/"
    rsync -avz contents/eg-catalog/ "$EG_USER@$EG_HOST:$EG_ROOT/eg-catalog/"
    rsync -avz scripts/eg/ "$EG_USER@$EG_HOST:$EG_ROOT/scripts/"
    ;;

  init-db)
    # 0.110 에서 실행 — eg-6v6.db 초기화 + catalog import
    cd "$EG_ROOT/6bq5"
    EG_DB="$EG_DB" .venv/bin/python "$EG_ROOT/scripts/init_db.py" --force
    EG_DB="$EG_DB" .venv/bin/python "$EG_ROOT/scripts/import_catalog.py" \
      --catalog "$EG_ROOT/eg-catalog"
    echo "[init-db] OK — $EG_DB"
    ;;

  patch-auth)
    # 0.110 에서 1 회 실행 — 6bq5 main.py 에 admin auth middleware 적용
    cd "$EG_ROOT/6bq5"
    if grep -q "X-Admin-Token" backend/main.py 2>/dev/null; then
      echo "[patch-auth] 이미 적용됨"
    else
      cp "$EG_ROOT/scripts/admin_auth.py" backend/admin_auth.py
      python3 "$EG_ROOT/scripts/inject_auth.py" backend/main.py
      echo "[patch-auth] OK"
    fi
    ;;

  start)
    # 0.110 에서 uvicorn 시작 — bind 0.0.0.0:8500
    cd "$EG_ROOT/6bq5"
    export KG_DB="$EG_DB"
    export EG_ADMIN_TOKEN="$ADMIN_TOKEN"
    nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8500 \
      > "$EG_ROOT/logs/uvicorn.log" 2>&1 &
    echo "[start] PID $! · log: $EG_ROOT/logs/uvicorn.log"
    ;;

  stop)
    pkill -f "uvicorn backend.main:app --host 0.0.0.0 --port 8500" || true
    echo "[stop] OK"
    ;;

  status)
    echo "=== uvicorn ==="
    pgrep -f "uvicorn backend.main:app --host 0.0.0.0 --port 8500" || echo "  (not running)"
    echo "=== DB stats ==="
    .venv/bin/python -c "
import sqlite3
c=sqlite3.connect('$EG_DB')
print('  Mission:', c.execute(\"SELECT COUNT(*) FROM nodes WHERE type='Mission'\").fetchone()[0])
print('  Skill:  ', c.execute(\"SELECT COUNT(*) FROM nodes WHERE type='Skill'\").fetchone()[0])
print('  Concept:', c.execute(\"SELECT COUNT(*) FROM nodes WHERE type='Concept'\").fetchone()[0])
print('  Plan:   ', c.execute(\"SELECT COUNT(*) FROM nodes WHERE type='Plan'\").fetchone()[0])
print('  Experience:', c.execute(\"SELECT COUNT(*) FROM nodes WHERE type='Experience'\").fetchone()[0])
"
    ;;

  *)
    cat <<USAGE
eg-6v6 deploy 절차 (192.168.0.110 에서 실행)

  EG_ADMIN_TOKEN=<token> bash deploy.sh bootstrap     # 1 회: dir + 6bq5 clone + venv
  EG_ADMIN_TOKEN=<token> bash deploy.sh sync-catalog  # (CCC 측에서) rsync
  EG_ADMIN_TOKEN=<token> bash deploy.sh init-db       # eg-6v6.db + catalog import
  EG_ADMIN_TOKEN=<token> bash deploy.sh patch-auth    # X-Admin-Token middleware
  EG_ADMIN_TOKEN=<token> bash deploy.sh start         # uvicorn :8500
  EG_ADMIN_TOKEN=<token> bash deploy.sh stop
  EG_ADMIN_TOKEN=<token> bash deploy.sh status

env:
  EG_HOST   = $EG_HOST
  EG_USER   = $EG_USER
  EG_ROOT   = $EG_ROOT
  EG_DB     = $EG_DB
USAGE
    ;;
esac
