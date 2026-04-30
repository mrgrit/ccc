#!/usr/bin/env bash
# low-3 supplemental 종료 감지 후 R4 round 자동 시작.
# 1분 주기 체크: cursor_r3_low3_supplemental.txt == queue_r3_low3_supplemental.tsv 행수 → 종료.
cd /home/opsclaw/ccc
LOG=results/retest/r4_trigger.log
LOW3_CURSOR=results/retest/cursor_r3_low3_supplemental.txt
LOW3_QUEUE=results/retest/queue_r3_low3_supplemental.tsv
R4_DRIVER=results/retest/driver_r4.sh
R4_LOG=results/retest/run_r4.log

echo "=== r4_auto_trigger start $(date -Iseconds) pid=$$ ===" >> "$LOG"

while true; do
  if [ ! -f "$LOW3_CURSOR" ]; then sleep 60; continue; fi
  cur=$(cat "$LOW3_CURSOR")
  total=$(wc -l < "$LOW3_QUEUE")
  if [ "$cur" -ge "$total" ]; then
    # low-3 done — rebuild R4 queue (low-3 회복분 제외) + start R4
    if pgrep -f "driver_r4.sh" >/dev/null 2>&1; then
      echo "[$(date -Iseconds)] R4 already running, exit" >> "$LOG"
      exit 0
    fi
    echo "[$(date -Iseconds)] low-3 done (cursor=$cur/$total) — rebuilding R4 queue" >> "$LOG"
    # progress.json 의 최신 상태로 R4 queue 재생성 (low-3 pass 회복분 제외)
    python3 scripts/build_r4_queue.py >> "$LOG" 2>&1 || true
    # 기존 cursor 초기화 (queue 재생성됐으니 처음부터)
    : > results/retest/cursor_r4.txt
    echo "[$(date -Iseconds)] starting R4" >> "$LOG"
    nohup bash "$R4_DRIVER" >> "$R4_LOG" 2>&1 &
    R4_PID=$!
    disown
    echo "[$(date -Iseconds)] R4 started pid=$R4_PID" >> "$LOG"
    exit 0
  fi
  sleep 60
done
