#!/usr/bin/env bash
# R4 main driver — R3 non-pass 842 재테스트 + fixture pre-hook.
# fix: timeout 600→720, fixture inject (해당 step 만), self_verify raw-dump 검출, ssh -n stdin 격리.
cd /home/opsclaw/ccc
Q=results/retest/queue_r4_main.tsv
C=results/retest/cursor_r4_main.txt
L=results/retest/run_r4_main.log
H="http://192.168.0.103:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R4 main driver start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

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
  echo "[$ts] R4-MAIN #$idx/$total $course w$wk o$order" >> "$L"

  # ★ Fixture pre-hook — fixtures 필드 있으면 inject + bastion sync. 없으면 skip.
  lab_file="contents/labs/$course/week${wk}.yaml"
  has_fix=$(python3 -c "
import yaml,sys
try: d=yaml.safe_load(open('$lab_file'))
except: print(0); sys.exit()
for s in d.get('steps',[]):
    if s.get('order')==int('$order') and s.get('fixtures'):
        print(1); sys.exit()
print(0)
" 2>/dev/null)
  if [ "$has_fix" = "1" ]; then
    echo "  [fixture-inject] $course/week${wk}.yaml o=$order" >> "$L"
    python3 scripts/lab_fixture_inject.py < /dev/null \
      --lab "$lab_file" --order "$order" --local-only >> "$L" 2>&1
    lab_id="${course}-week${wk}"
    if [ -d "data/cyber-range-fixtures/$lab_id/$order" ]; then
      sshpass -p 1 ssh -n -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
        ccc@192.168.0.103 "mkdir -p /home/ccc/cyber-range/fixtures/$lab_id/$order" 2>>"$L"
      sshpass -p 1 scp -o StrictHostKeyChecking=no -r \
        "data/cyber-range-fixtures/$lab_id/$order"/* \
        "ccc@192.168.0.103:/home/ccc/cyber-range/fixtures/$lab_id/$order/" >> "$L" 2>&1
      echo "  [fixture-sync] OK ($lab_id/$order)" >> "$L"
    fi
  fi

  timeout 720 python3 scripts/test_step.py "$course" "$wk" "$order" --no-augment < /dev/null >> "$L" 2>&1
  rc=$?

  if grep -qE "Connection refused|Errno 111" <(tail -3 "$L"); then
    echo "  ↳ retry (connection refused)" >> "$L"
    wait_for_bastion
    timeout 720 python3 scripts/test_step.py "$course" "$wk" "$order" --no-augment < /dev/null >> "$L" 2>&1
    rc=$?
  fi

  [ $rc -ne 0 ] && echo "  step exited rc=$rc" >> "$L"
  echo "$idx" > "$C"
  sleep 1
done < "$Q"
echo "=== R4 main DONE $(date -Iseconds) ===" >> "$L"
