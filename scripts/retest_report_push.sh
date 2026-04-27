#!/usr/bin/env bash
# 2시간 주기 retest 리포트 자동 갱신 + commit + push
# crontab 등록: 0 */2 * * * /home/opsclaw/ccc/scripts/retest_report_push.sh >> /home/opsclaw/ccc/results/retest/report_cron.log 2>&1
set -euo pipefail
cd /home/opsclaw/ccc

TS="$(date -Iseconds)"
echo "=== retest_report_push start $TS ==="

# 1. report 생성
python3 scripts/retest_report.py

# 2. cursor 진행 추출
R3_CUR=$(cat results/retest/cursor_r3.txt 2>/dev/null || echo 0)
R3_TOT=$(wc -l < results/retest/queue_r3.tsv 2>/dev/null || echo 575)
PASS=$(grep -E '^\| pass \|' results/retest/report.md | head -1 | awk -F'|' '{print $4}' | tr -d ' ')

# 3. git stage
git add results/retest/report.md bastion_test_progress.json 2>/dev/null

# 4. 변경 없으면 skip
if git diff --staged --quiet; then
  echo "  [no changes — skip commit]"
  exit 0
fi

# 5. commit + push
git commit -m "chore(retest): 진행 리포트 업데이트 ${R3_CUR}/${R3_TOT} (pass=${PASS}) round3

자동 생성 (cron 2h 주기): scripts/retest_report_push.sh
"

git push origin main

echo "=== retest_report_push done $(date -Iseconds) ==="
