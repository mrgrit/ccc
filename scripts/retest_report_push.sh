#!/usr/bin/env bash
# 2시간 주기 retest 리포트 자동 갱신 + commit + push
# crontab 등록: 0 */2 * * * /home/opsclaw/ccc/scripts/retest_report_push.sh >> /home/opsclaw/ccc/results/retest/report_cron.log 2>&1
set -euo pipefail
cd /home/opsclaw/ccc

TS="$(date -Iseconds)"
echo "=== retest_report_push start $TS ==="

# 1. report 생성
python3 scripts/retest_report.py

# 2. 활성 round + cursor 진행 추출 (R5 → R4 → R3 우선순위)
ROUND=""
CUR=0
TOT=0
for r in r5 r4 r3; do
  q="results/retest/queue_${r}_main.tsv"
  c="results/retest/cursor_${r}_main.txt"
  [ -f "$q" ] || continue
  [ -f "$c" ] || continue
  ROUND="$r"
  CUR=$(cat "$c" 2>/dev/null || echo 0)
  TOT=$(wc -l < "$q" 2>/dev/null || echo 0)
  break
done
[ -z "$ROUND" ] && { ROUND="r5"; CUR=0; TOT=676; }
PASS=$(grep -E '^\| pass \|' results/retest/report.md | head -1 | awk -F'|' '{print $4}' | tr -d ' ')

# 3. git stage
git add results/retest/report.md bastion_test_progress.json 2>/dev/null

# 4. 변경 없으면 skip
if git diff --staged --quiet; then
  echo "  [no changes — skip commit]"
  exit 0
fi

# 5. commit + push
git commit -m "chore(retest): 진행 리포트 업데이트 ${CUR}/${TOT} (pass=${PASS}) ${ROUND^^}

자동 생성 (cron 2h 주기): scripts/retest_report_push.sh
"

git push origin main

echo "=== retest_report_push done $(date -Iseconds) ==="
