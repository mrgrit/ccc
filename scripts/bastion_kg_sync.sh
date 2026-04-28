#!/usr/bin/env bash
# bastion KG dual-DB 동기화 (2026-04-28 KG drop bug 후속)
#
# 두 DB:
#   /opt/bastion/data/bastion_graph.db (active server, V2 추가분 누적)
#   /home/ccc/ccc/data/bastion_graph.db (legacy backup)
#
# server 가 size 큰 우선 사용 (graph.py fix). 둘 다 18MB+ 이면 분기 가능.
# 이 script 가 active → legacy 단방향 sync (cron 1h).
#
# 사용:
#   ./scripts/bastion_kg_sync.sh        # 한 번 실행
#   ./scripts/bastion_kg_sync.sh check  # check only (no sync)
#   crontab -e 에:
#     0 * * * * cd /home/opsclaw/ccc && ./scripts/bastion_kg_sync.sh >> /tmp/bastion_kg_sync.log 2>&1

set -e

ACTIVE="/opt/bastion/data/bastion_graph.db"
BACKUP="/home/ccc/ccc/data/bastion_graph.db"
HOST="${BASTION_HOST:-192.168.0.115}"
USER="${BASTION_USER:-ccc}"
PASS="${BASTION_PASS:-1}"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

# 두 DB size 비교
SIZES=$(sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "${USER}@${HOST}" \
  "stat -c '%s %Y %n' $ACTIVE $BACKUP 2>/dev/null" 2>&1 | grep -v setlocale)

ACT_SIZE=$(echo "$SIZES" | grep "$ACTIVE" | awk '{print $1}')
ACT_MTIME=$(echo "$SIZES" | grep "$ACTIVE" | awk '{print $2}')
BAK_SIZE=$(echo "$SIZES" | grep "$BACKUP" | awk '{print $1}')
BAK_MTIME=$(echo "$SIZES" | grep "$BACKUP" | awk '{print $2}')

echo "[$(ts)] active: ${ACT_SIZE} bytes (mtime $ACT_MTIME)"
echo "[$(ts)] backup: ${BAK_SIZE} bytes (mtime $BAK_MTIME)"

if [ "${1:-}" = "check" ]; then
  echo "check-only mode, exit"
  exit 0
fi

# active 가 더 새로 / 더 크면 → backup 으로 cp
if [ -z "$ACT_MTIME" ] || [ -z "$BAK_MTIME" ]; then
  echo "[$(ts)] error: missing DB info"
  exit 2
fi

if [ "$ACT_MTIME" -gt "$BAK_MTIME" ]; then
  echo "[$(ts)] active newer → sync to backup"
  sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "${USER}@${HOST}" \
    "cp $ACTIVE $BACKUP && echo synced" 2>&1 | grep -v setlocale | tail -3
elif [ "$ACT_MTIME" -lt "$BAK_MTIME" ]; then
  echo "[$(ts)] backup newer (unusual) → manual review needed"
  exit 1
else
  echo "[$(ts)] same mtime, no sync needed"
fi
