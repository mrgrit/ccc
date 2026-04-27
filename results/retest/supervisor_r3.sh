#!/usr/bin/env bash
# R3 supervisor — driver_r3 죽으면 재시작.
SELF_DIR="$(dirname "$(readlink -f "$0")")"
DRIVER="$SELF_DIR/driver_r3.sh"
SUPLOG="$SELF_DIR/supervisor_r3.log"
QUEUE="$SELF_DIR/queue_r3.tsv"
CURSOR="$SELF_DIR/cursor_r3.txt"

echo "=== r3 supervisor start $(date -Iseconds) pid=$$ ===" >> "$SUPLOG"

while true; do
    cur=$(cat "$CURSOR" 2>/dev/null || echo 0)
    total=$(wc -l < "$QUEUE" 2>/dev/null || echo 0)
    if [ "$cur" -ge "$total" ] && [ "$total" -gt 0 ]; then
        echo "[$(date -Iseconds)] queue 완료 $cur/$total — supervisor 종료" >> "$SUPLOG"
        break
    fi
    if ! pgrep -f "$DRIVER" >/dev/null 2>&1; then
        echo "[$(date -Iseconds)] driver_r3 죽음 — 재시작 (cursor=$cur)" >> "$SUPLOG"
        bash "$DRIVER" >> "$SELF_DIR/run_r3.log" 2>&1 &
        sleep 3
    fi
    sleep 5
done

echo "=== r3 supervisor exit $(date -Iseconds) ===" >> "$SUPLOG"
