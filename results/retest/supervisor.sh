#!/usr/bin/env bash
# Driver supervisor — driver.sh 가 죽으면 즉시 재시작.
# 큐 완료 시에는 종료. 평소 5초마다 살아있는지 체크.
SELF_DIR="$(dirname "$(readlink -f "$0")")"
DRIVER="$SELF_DIR/driver.sh"
LOG="$SELF_DIR/run.log"
SUPLOG="$SELF_DIR/supervisor.log"
QUEUE="$SELF_DIR/queue.tsv"
CURSOR="$SELF_DIR/cursor.txt"

echo "=== supervisor start $(date -Iseconds) pid=$$ ===" >> "$SUPLOG"

while true; do
    cur=$(cat "$CURSOR" 2>/dev/null || echo 0)
    total=$(wc -l < "$QUEUE" 2>/dev/null || echo 0)
    if [ "$cur" -ge "$total" ] && [ "$total" -gt 0 ]; then
        echo "[$(date -Iseconds)] queue 완료 $cur/$total — supervisor 종료" >> "$SUPLOG"
        break
    fi
    if ! pgrep -f "$DRIVER" >/dev/null 2>&1; then
        echo "[$(date -Iseconds)] driver 죽음 — 재시작 (cursor=$cur)" >> "$SUPLOG"
        bash "$DRIVER" &
        sleep 3
    fi
    sleep 5
done

echo "=== supervisor exit $(date -Iseconds) ===" >> "$SUPLOG"
