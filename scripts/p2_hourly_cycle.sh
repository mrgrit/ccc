#!/usr/bin/env bash
# CCC P2 bastion test hourly cycle (Track B 통합 v2)
#
# - cron: 0 * * * *  → 매 시 정각 시작
# - timeout 55m (cron 측에서)
# - 내부 budget:
#     work 45m (driver_p2_standalone.sh 가 bastion 자율 lab 수행)
#     report+push  ~1m
#     cooling 5m (GPU 회복)
# - flock 으로 중복 실행 방지
# - log: results/p2_hourly_cron.log + results/retest/run_p2_standalone.log
set -uo pipefail
cd /home/opsclaw/ccc

LOCK=/tmp/p2_hourly_cycle.lock
exec 9>"$LOCK"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] another instance running, skip"
  exit 0
fi

START_TS="$(date -Iseconds)"
START_EPOCH="$(date +%s)"
HOUR_TAG="$(date +%Y%m%d-%H%M)"
REPORT_DIR="contents/standalone/bastion-test-reports"
REPORT="$REPORT_DIR/$HOUR_TAG.md"
DRIVER=results/retest/driver_p2_standalone.sh
DRIVER_LOG=results/retest/run_p2_standalone.log
P2_CURSOR=results/retest/cursor_p2_standalone.txt
P2_QUEUE=results/retest/queue_p2_standalone.tsv
PROG=standalone_test_progress.json
WORK_BUDGET=$((45 * 60))   # 45 분 driver
COOL_SEC=$((5 * 60))       # 5 분 cooling

echo "=== p2_hourly_cycle v2 start $START_TS hour_tag=$HOUR_TAG ==="

# Phase A — bastion + ollama health
HEALTH_URL="${BASTION_HEALTH:-http://192.168.0.110:9200/health}"
HEALTH_JSON="$(curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null || echo '{"status":"DOWN"}')"
HEALTH_STATUS="$(echo "$HEALTH_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','UNKNOWN'))" 2>/dev/null || echo "PARSE_ERR")"
KG_STATUS="$(curl -fsS --max-time 5 "${HEALTH_URL%/health}/kg/health" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('all_modules_loaded') else 'DEGRADED')" 2>/dev/null || echo "?")"

# Phase B — pre-cycle progress snapshot
PRE_CURSOR=$(cat "$P2_CURSOR" 2>/dev/null || echo 0)
PRE_PASS=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('passed',0))" 2>/dev/null || echo 0)
PRE_FAIL=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('failed',0))" 2>/dev/null || echo 0)
PRE_DONE=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('completed',0))" 2>/dev/null || echo 0)
QUEUE_TOTAL=$(wc -l < "$P2_QUEUE" 2>/dev/null || echo 0)

# Phase C — driver 실행 (bastion 살아있고 queue 남아있을 때만)
DRIVER_RAN="no"
if [ "$HEALTH_STATUS" != "ok" ]; then
  echo "[$(date -Iseconds)] bastion not ok ($HEALTH_STATUS) — driver skip"
elif [ "$PRE_CURSOR" -ge "$QUEUE_TOTAL" ]; then
  echo "[$(date -Iseconds)] queue done ($PRE_CURSOR/$QUEUE_TOTAL) — driver skip"
else
  echo "[$(date -Iseconds)] launching driver (budget ${WORK_BUDGET}s)..."
  /usr/bin/timeout --kill-after=30s "${WORK_BUDGET}s" bash "$DRIVER" || true
  DRIVER_RAN="yes"
fi

# Phase D — post-cycle progress snapshot
POST_CURSOR=$(cat "$P2_CURSOR" 2>/dev/null || echo 0)
POST_PASS=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('passed',0))" 2>/dev/null || echo 0)
POST_FAIL=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('failed',0))" 2>/dev/null || echo 0)
POST_DONE=$(python3 -c "import json; d=json.load(open('$PROG')); print(d.get('completed',0))" 2>/dev/null || echo 0)
DELTA_DONE=$((POST_DONE - PRE_DONE))
DELTA_PASS=$((POST_PASS - PRE_PASS))
DELTA_FAIL=$((POST_FAIL - PRE_FAIL))

# Phase E — 이번 cycle 의 verdict 분포 (driver log 의 마지막 N 라인)
RECENT_VERDICTS=$(grep -E "^VERDICT: " "$DRIVER_LOG" 2>/dev/null | tail -50 | awk '{print $2}' | sort | uniq -c | awk '{print "  - " $2 ": " $1}' | head -10)

# Phase F — 보고서 작성
mkdir -p "$REPORT_DIR"
{
  echo "# P2 Bastion Test Report — $(date '+%Y-%m-%d %H:%M KST')"
  echo
  echo "> Track B (bastion 자율 lab) hourly cycle. v2 — driver 실제 실행 + 통계 누적."
  echo ">"
  echo "> Bastion \`$HEALTH_URL\` → **$HEALTH_STATUS** · KG **$KG_STATUS**"
  echo
  echo "## 본 cycle 결과"
  echo
  echo "| 항목 | pre | post | Δ |"
  echo "|------|-----|------|---|"
  echo "| cursor | $PRE_CURSOR | $POST_CURSOR | +$((POST_CURSOR - PRE_CURSOR)) / $QUEUE_TOTAL |"
  echo "| completed | $PRE_DONE | $POST_DONE | +$DELTA_DONE |"
  echo "| pass | $PRE_PASS | $POST_PASS | +$DELTA_PASS |"
  echo "| fail | $PRE_FAIL | $POST_FAIL | +$DELTA_FAIL |"
  echo
  if [ "$DRIVER_RAN" = "yes" ]; then
    if [ "$DELTA_DONE" -gt 0 ]; then
      pass_pct=$(( DELTA_PASS * 100 / (DELTA_DONE > 0 ? DELTA_DONE : 1) ))
      echo "본 cycle pass rate: **${pass_pct}%** ($DELTA_PASS / $DELTA_DONE)"
    else
      echo "본 cycle 진행 없음 (driver 가 step 시작 못 함 — bastion/ollama 상태 확인)"
    fi
  else
    echo "_driver 미실행 (skip)_"
  fi
  echo
  echo "## 본 cycle 의 verdict 분포 (최근 50)"
  echo
  if [ -n "$RECENT_VERDICTS" ]; then
    echo '```'
    echo "$RECENT_VERDICTS"
    echo '```'
  else
    echo "(verdict 없음)"
  fi
  echo
  echo "## 누적 P2 통계"
  echo
  echo "- queue total: $QUEUE_TOTAL steps"
  echo "- cursor: $POST_CURSOR / $QUEUE_TOTAL ($(( POST_CURSOR * 100 / (QUEUE_TOTAL > 0 ? QUEUE_TOTAL : 1) ))%)"
  echo "- completed: $POST_DONE · pass $POST_PASS · fail $POST_FAIL"
  if [ "$POST_DONE" -gt 0 ]; then
    cum_pct=$(( POST_PASS * 100 / POST_DONE ))
    echo "- 누적 pass rate: **${cum_pct}%**"
  fi
  echo
  echo "## Cycle meta"
  echo
  echo "- start: $START_TS"
  echo "- driver budget: 45 분 · cooling: 5 분"
  echo "- driver log tail: \`$DRIVER_LOG\`"
  echo "- lock: \`$LOCK\`"
} > "$REPORT"

# Phase G — commit + push
git add "$REPORT" "$PROG" "$P2_CURSOR" 2>/dev/null
if git diff --staged --quiet; then
  echo "[$(date -Iseconds)] no changes — skip commit"
else
  git commit -m "chore(p2): bastion test cycle $HOUR_TAG — pass +$DELTA_PASS / fail +$DELTA_FAIL (cursor $POST_CURSOR/$QUEUE_TOTAL)" --quiet
  if git push origin main >/dev/null 2>&1; then
    echo "[$(date -Iseconds)] push ok"
  else
    echo "[$(date -Iseconds)] push failed"
  fi
fi

ELAPSED=$(( $(date +%s) - START_EPOCH ))
echo "[$(date -Iseconds)] cycle elapsed=${ELAPSED}s · cooling ${COOL_SEC}s ..."
sleep "$COOL_SEC"
echo "=== p2_hourly_cycle v2 done $(date -Iseconds) ==="
