#!/usr/bin/env bash
# R3-noexec V2 — post-fix verification (commit 7db733d4 의 한국어 fallback + acceptable_methods)
# 96 케이스 재실행, before/after 비교 → paper §6.2 갱신
cd /home/opsclaw/ccc
set -a; source .env 2>/dev/null; set +a

Q=results/retest/queue_r3_noexec.tsv
C=results/retest/cursor_r3_noexec_v2.txt
L=results/retest/run_r3_noexec_v2.log
H="http://192.168.0.103:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R3-noexec V2 (post-fix) start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

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

  echo "[$(date -Iseconds)] V2 #${idx}/${total} ${course} ${wk} ${order}" >> "$L"
  timeout 600 python3 -u scripts/test_step.py "${course}" "${wk#w}" "${order#o}" >> "$L" 2>&1
  echo "$idx" > "$C"
  sleep 2
done < "$Q"
echo "=== R3-noexec V2 DONE $(date -Iseconds) ===" >> "$L"
