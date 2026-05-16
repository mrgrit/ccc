#!/usr/bin/env bash
# R5 main driver — R4 종료 후 잔여 676 비-pass 재테스트.
# fix #8 (agent: stdout 코드블록 강제) + fix #9 (judge: format 단독 fail 금지) 적용 후.
cd /home/opsclaw/ccc
Q=results/retest/queue_r5_main.tsv
C=results/retest/cursor_r5_main.txt
L=results/retest/run_r5_main.log
H="${BASTION_HEALTH:-http://192.168.0.110:9200/health}"
O="http://192.168.0.109:11434/api/tags"

[ -f "$C" ] || echo 0 > "$C"
cur=$(cat "$C")
total=$(wc -l < "$Q")
echo "=== R5 main driver start $(date -Iseconds) cursor=$cur total=$total pid=$$ ===" >> "$L"

wait_for_bastion() {
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 30 "$H" >/dev/null 2>&1; then return 0; fi
    echo "  [bastion-health] wait $i (5s)" >> "$L"
    sleep 5
  done
  return 1
}

# Ollama LLM 백엔드 (192.168.0.109) 무한 대기 — 다운 시 step timeout 누적 방지.
# 5월9일 #200~#250 Ollama 호스트 다운 51 case 손실 후 추가.
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

idx=0
while IFS=$'\t' read -r course_path order; do
  idx=$((idx+1))
  if [ "$idx" -le "$cur" ]; then continue; fi
  [ -z "$course_path" ] && continue

  course=$(dirname "$course_path")
  course=${course#contents/labs/}
  week_yaml=$(basename "$course_path")
  wk=$(echo "$week_yaml" | sed 's/week//;s/\.yaml//;s/^0*//')
  [ -z "$wk" ] && wk=0

  if ! curl -s --max-time 30 "$H" >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] bastion DOWN — wait..." >> "$L"
    wait_for_bastion || { echo "  bastion down — skip" >> "$L"; continue; }
  fi
  # ★ Ollama (LLM 백엔드) 다운 시 step timeout 누적 방지 — 부활까지 무한 대기
  wait_for_ollama

  ts=$(date -Iseconds)
  echo "[$ts] R5-MAIN #$idx/$total $course w$wk o$order" >> "$L"

  # ★ Fixture pre-hook (R4 와 동일)
  lab_file="contents/labs/$course/week$(printf '%02d' "$wk").yaml"
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
    echo "  [fixture-inject] $course/week$(printf '%02d' "$wk").yaml o=$order" >> "$L"
    python3 scripts/lab_fixture_inject.py < /dev/null \
      --lab "$lab_file" --order "$order" --local-only >> "$L" 2>&1
    lab_id="${course}-week$(printf '%02d' "$wk")"
    if [ -d "data/cyber-range-fixtures/$lab_id/$order" ]; then
      sshpass -p 1 ssh -n -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
        ccc@192.168.0.110 "mkdir -p /home/ccc/cyber-range/fixtures/$lab_id/$order" 2>>"$L"
      sshpass -p 1 scp -o StrictHostKeyChecking=no -r \
        "data/cyber-range-fixtures/$lab_id/$order"/* \
        "ccc@192.168.0.110:/home/ccc/cyber-range/fixtures/$lab_id/$order/" >> "$L" 2>&1
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
echo "=== R5 main DONE $(date -Iseconds) ===" >> "$L"
