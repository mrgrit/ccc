#!/usr/bin/env bash
# R4 round — Fix #1/#2/#3/#4/#5 모두 적용 후 non-pass step 926 재측정.
# error 150 + no_execution 16 + qa_fallback 28 + fail 732 = 926.
# 평균 6분/case (timeout 600s) → 예상 ~92 시간 (약 4일).
# 짧은 estimate 위해 timeout 600→500 로 축소.
cd /home/opsclaw/ccc
set -a; source .env 2>/dev/null; set +a

Q=results/retest/queue_r4.tsv
C=results/retest/cursor_r4.txt
L=results/retest/run_r4.log
H="http://192.168.0.103:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R4 start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8; do
    if curl -s --max-time 3 "$H" >/dev/null 2>&1; then return 0; fi
    sleep 5
  done
  return 1
}

idx=0
while IFS=$'\t' read -r course wk order; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course" ] && continue

  if ! wait_for_bastion; then
    echo "  [health-fail] $idx ${course} ${wk} ${order}" >> "$L"
    continue
  fi

  echo "[$(date -Iseconds)] R4 #${idx}/${total} ${course} ${wk} ${order}" >> "$L"
  timeout 500 python3 -u scripts/test_step.py "${course}" "${wk#week}" "${order#o}" >> "$L" 2>&1
  echo "$idx" > "$C"
  sleep 2
done < "$Q"
echo "=== R4 DONE $(date -Iseconds) ===" >> "$L"
