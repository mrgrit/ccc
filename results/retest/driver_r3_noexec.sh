#!/usr/bin/env bash
# R3 supplemental — no_execution 96건만 재테스트.
# 새 JSON markdown parser (commit 7d4145eb) 효과 측정.
cd /home/opsclaw/ccc
set -a; source .env 2>/dev/null; set +a

Q=results/retest/queue_r3_noexec.tsv
C=results/retest/cursor_r3_noexec.txt
L=results/retest/run_r3_noexec.log
H="http://192.168.0.115:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R3 noexec supplemental start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 3 "$H" >/dev/null 2>&1; then return 0; fi
    echo "  [bastion-health] wait $i (5s)" >> "$L"
    sleep 5
  done
  return 1
}

idx=0
while IFS=$'\t' read -r course wk order; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course" ] && continue

  if ! curl -s --max-time 3 "$H" >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] bastion DOWN — wait..." >> "$L"
    wait_for_bastion || { echo "  bastion 50s 후에도 down — pause" >> "$L"; sleep 30; continue; }
  fi

  ts=$(date -Iseconds)
  echo "[$ts] R3-noexec #$idx/$total $course $wk $order" >> "$L"
  timeout 600 python3 scripts/test_step.py "$course" "${wk#w}" "${order#o}" --no-augment >> "$L" 2>&1
  rc=$?

  if grep -qE "Connection refused|Errno 111" <(tail -3 "$L"); then
    echo "  ↳ retry (connection refused detected)" >> "$L"
    wait_for_bastion
    timeout 600 python3 scripts/test_step.py "$course" "${wk#w}" "${order#o}" --no-augment >> "$L" 2>&1
    rc=$?
  fi

  [ $rc -ne 0 ] && echo "  step exited rc=$rc" >> "$L"
  echo "$idx" > "$C"
  sleep 1
done < "$Q"
echo "=== R3 noexec DONE $(date -Iseconds) ===" >> "$L"
