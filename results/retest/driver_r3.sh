#!/usr/bin/env bash
# R3 driver — R2 후 잔여 비-pass 1168건 재테스트.
# 5건 개선 (attack_mode preamble, few-shot, FIRST_TURN_RETRY, autoscan, ATTACK_COURSES 7) 효과 측정.
# v2 (14:46): bastion connection refused 시 health-check + 백오프 retry (단일 워커 + 동시 요청 대응)
cd /home/opsclaw/ccc
Q=results/retest/queue_r3.tsv
C=results/retest/cursor_r3.txt
L=results/retest/run_r3.log
H="http://192.168.0.115:8003/health"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R3 driver v2 start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

# bastion 헬스 대기 — connection refused 시 백오프 retry
wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 3 "$H" >/dev/null 2>&1; then return 0; fi
    echo "  [bastion-health] wait $i (5s)" >> "$L"
    sleep 5
  done
  return 1
}

idx=0
while IFS=$'\t' read -r course wk order prev; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course" ] && continue

  # bastion alive 확인 (connection refused 방지)
  if ! curl -s --max-time 3 "$H" >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] bastion DOWN — wait..." >> "$L"
    wait_for_bastion || { echo "  bastion 50s 후에도 down — pause" >> "$L"; sleep 30; continue; }
  fi

  ts=$(date -Iseconds)
  echo "[$ts] R3 #$idx/$total $course w$wk o$order (prev=$prev)" >> "$L"
  timeout 600 python3 scripts/test_step.py "$course" "$wk" "$order" --no-augment >> "$L" 2>&1
  rc=$?

  # connection refused 패턴 잡으면 1회 재시도 (대기 + 다시)
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
echo "=== R3 driver DONE $(date -Iseconds) ===" >> "$L"
