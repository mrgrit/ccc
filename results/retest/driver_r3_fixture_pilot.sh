#!/usr/bin/env bash
# R3 fixture pilot driver — task 시작 직전 fixture inject + retest.
# fixtures 필드 있는 step 만 대상. 일반 driver 와 동일하지만 fixture pre-hook 추가.
cd /home/opsclaw/ccc
Q=results/retest/queue_r3_fixture_pilot.tsv
C=results/retest/cursor_r3_fixture_pilot.txt
L=results/retest/run_r3_fixture_pilot.log
H="http://192.168.0.103:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R3 fixture pilot driver start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 3 "$H" >/dev/null 2>&1; then return 0; fi
    echo "  [bastion-health] wait $i (5s)" >> "$L"
    sleep 5
  done
  return 1
}

idx=0
while IFS=$'\t' read -r course_path order; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course_path" ] && continue

  course=$(dirname "$course_path")
  week_yaml=$(basename "$course_path")
  wk=$(echo "$week_yaml" | sed 's/week//')

  if ! curl -s --max-time 3 "$H" >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] bastion DOWN — wait..." >> "$L"
    wait_for_bastion || { echo "  bastion down — skip" >> "$L"; continue; }
  fi

  ts=$(date -Iseconds)
  echo "[$ts] FIXTURE-PILOT #$idx/$total $course w$wk o$order" >> "$L"

  # ★ Fixture pre-hook — local generation + bastion sync
  echo "  [fixture-inject] $course/week${wk}.yaml order=$order" >> "$L"
  python3 scripts/lab_fixture_inject.py \
    --lab "contents/labs/$course/week${wk}.yaml" \
    --order "$order" --local-only >> "$L" 2>&1

  # bastion 으로 fixture sync (sshpass + scp)
  lab_id="${course}-week${wk}"
  if [ -d "data/cyber-range-fixtures/$lab_id/$order" ]; then
    sshpass -p 1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
      ccc@192.168.0.103 "mkdir -p /home/ccc/cyber-range/fixtures/$lab_id/$order" 2>>"$L"
    sshpass -p 1 scp -o StrictHostKeyChecking=no -r \
      "data/cyber-range-fixtures/$lab_id/$order"/* \
      "ccc@192.168.0.103:/home/ccc/cyber-range/fixtures/$lab_id/$order/" >> "$L" 2>&1
    echo "  [fixture-sync] bastion sync OK ($lab_id/$order)" >> "$L"
  fi

  timeout 600 python3 scripts/test_step.py "$course" "$wk" "$order" --no-augment >> "$L" 2>&1
  rc=$?

  if grep -qE "Connection refused|Errno 111" <(tail -3 "$L"); then
    echo "  ↳ retry (connection refused detected)" >> "$L"
    wait_for_bastion
    timeout 600 python3 scripts/test_step.py "$course" "$wk" "$order" --no-augment >> "$L" 2>&1
    rc=$?
  fi

  [ $rc -ne 0 ] && echo "  step exited rc=$rc" >> "$L"
  echo "$idx" > "$C"
  sleep 1
done < "$Q"
echo "=== R3 fixture pilot DONE $(date -Iseconds) ===" >> "$L"
