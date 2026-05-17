#!/usr/bin/env bash
# P2 Track B — standalone 6v6 lab bastion 자율 테스트 driver.
#
# Queue: results/retest/queue_p2_standalone.tsv (contents/standalone/lab/{secuops,attack,aisec})
# Cursor: results/retest/cursor_p2_standalone.txt
# Log:    results/retest/run_p2_standalone.log
# Progress: standalone_test_progress.json (R5 의 bastion_test_progress.json 과 분리)
#
# fix #8/#9 그대로 적용 (test_step.py 의 기본). test_step.py --standalone 플래그 사용.
cd /home/opsclaw/ccc
Q=results/retest/queue_p2_standalone.tsv
C=results/retest/cursor_p2_standalone.txt
L=results/retest/run_p2_standalone.log
H="${BASTION_HEALTH:-http://192.168.0.110:9200/health}"
O="http://192.168.0.109:11434/api/tags"

[ -f "$Q" ] || { echo "[$(date -Iseconds)] queue 없음: $Q (build_p2_standalone_queue.py 실행 필요)" >> "$L"; exit 1; }
[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== P2 standalone driver start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 30 "$H" >/dev/null 2>&1; then return 0; fi
    echo "  [bastion-health] wait $i (5s)" >> "$L"
    sleep 5
  done
  return 1
}

wait_for_ollama() {
  local n=0
  while ! curl -s --max-time 5 "$O" >/dev/null 2>&1; do
    n=$((n+1))
    if [ $((n % 6)) -eq 1 ]; then
      echo "[$(date -Iseconds)] [ollama-down] 192.168.0.109:11434 unreachable — wait 30s (try $n)" >> "$L"
    fi
    sleep 30
  done
  [ $n -gt 0 ] && echo "[$(date -Iseconds)] [ollama-up] recovered after $n tries" >> "$L"
}

# 외부 SIGTERM (cron 의 timeout 55m) 받으면 즉시 종료 (현재 step 은 끝까지 진행).
trap 'echo "[$(date -Iseconds)] SIGTERM — graceful stop after current step" >> "$L"; STOP=1' TERM

STOP=0
idx=0
while IFS=$'\t' read -r course_path order; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course_path" ] && continue
  [ "$STOP" = "1" ] && { echo "[$(date -Iseconds)] STOP flag — break" >> "$L"; break; }

  # course_path = contents/standalone/lab/<course>/weekNN.yaml
  course=$(basename "$(dirname "$course_path")")
  week_yaml=$(basename "$course_path")
  wk=$(echo "$week_yaml" | sed 's/week//;s/\.yaml//;s/^0*//')
  [ -z "$wk" ] && wk=0

  if ! curl -s --max-time 30 "$H" >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] bastion DOWN — wait..." >> "$L"
    wait_for_bastion || { echo "  bastion down — skip" >> "$L"; continue; }
  fi
  wait_for_ollama

  ts=$(date -Iseconds)
  echo "[$ts] P2-STANDALONE #$idx/$total $course w$wk o$order" >> "$L"

  timeout 480 python3 scripts/test_step.py "$course" "$wk" "$order" \
        --standalone --no-augment < /dev/null >> "$L" 2>&1
  rc=$?

  if grep -qE "Connection refused|Errno 111" <(tail -3 "$L"); then
    echo "  ↳ retry (connection refused)" >> "$L"
    wait_for_bastion
    timeout 720 python3 scripts/test_step.py "$course" "$wk" "$order" \
          --standalone --no-augment < /dev/null >> "$L" 2>&1
    rc=$?
  fi

  [ $rc -ne 0 ] && echo "  step exited rc=$rc" >> "$L"
  echo "$idx" > "$C"
  sleep 1
done < "$Q"
echo "=== P2 standalone driver done $(date -Iseconds) cursor=$(cat $C) ===" >> "$L"
