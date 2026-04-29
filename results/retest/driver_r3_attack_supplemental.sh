#!/usr/bin/env bash
# R3-attack-ai supplemental — 94 ERROR (Connection refused) 재측정
# V2 driver 완료 후 실행. wait_for_bastion 5-retry 로 server crash 재현 방지.
cd /home/opsclaw/ccc
set -a; source .env 2>/dev/null; set +a

Q=results/retest/queue_r3_attack_supplemental.tsv
C=results/retest/cursor_r3_attack_supplemental.txt
L=results/retest/run_r3_attack_supplemental.log
H="http://192.168.0.103:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R3-attack-supplemental start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5; do
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

  echo "[$(date -Iseconds)] SUPP #${idx}/${total} ${course} ${wk} ${order}" >> "$L"
  timeout 600 python3 -u scripts/test_step.py "${course}" "${wk#w}" "${order#o}" >> "$L" 2>&1
  echo "$idx" > "$C"
  sleep 2
done < "$Q"
echo "=== R3-attack-supplemental DONE $(date -Iseconds) ===" >> "$L"
