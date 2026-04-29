#!/usr/bin/env bash
# V2 driver 종료 감지 → 자동 chain:
# 1. v2_paper_metrics 재생성
# 2. OWASP prompt sync_to_bastion (agent.py 동기화 + 재시작)
# 3. attack-ai 94 ERROR supplemental driver 시작
# 4. 결과 commit + push
#
# 사용: nohup bash scripts/post_v2_chain.sh > /tmp/post_v2_chain.log 2>&1 &
set -eu
ROOT=/home/opsclaw/ccc
cd "$ROOT"

V2_LOG="$ROOT/results/retest/run_r3_noexec_v2.log"
SUPP_LOG="$ROOT/results/retest/run_r3_attack_supplemental.log"

echo "=== post_v2_chain start $(date -Iseconds) ==="

# 1. V2 종료 대기 (poll 5분 간격)
while true; do
  if grep -q "=== R3-noexec V2 DONE" "$V2_LOG" 2>/dev/null; then
    echo "[$(date -Iseconds)] V2 DONE detected"
    break
  fi
  if ! ps -ef | grep -v grep | grep -q "driver_r3_noexec_v2.sh"; then
    # process 없으면 강제 종료된 것
    echo "[$(date -Iseconds)] V2 driver not running (crashed?)"
    break
  fi
  sleep 300
done

# 2. v2 paper metrics 재생성
echo "[$(date -Iseconds)] regenerating v2_paper_metrics"
python3 scripts/r3_v2_paper_metrics.py 2>&1 | tail -30
git add results/retest/v2_paper_metrics.json
git commit -m "chore(P0): V2 종료 — paper §6.2 metric 최종화

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>" 2>&1 | tail -3 || true

# 3. OWASP prompt sync_to_bastion + 재시작
echo "[$(date -Iseconds)] sync_to_bastion (OWASP fix deploy)"
if [ -x scripts/sync_to_bastion.sh ]; then
  bash scripts/sync_to_bastion.sh 2>&1 | tail -10
else
  # Fallback: rsync + ssh restart
  BASTION_HOST="${BASTION_HOST:-192.168.0.103}"
  sshpass -p 1 rsync -av packages/bastion/agent.py ccc@${BASTION_HOST}:/opt/bastion/bastion/agent.py 2>&1 | tail -5
  sshpass -p 1 ssh -o StrictHostKeyChecking=no ccc@${BASTION_HOST} "cd /opt/bastion && pkill -9 -f 'uvicorn api:app' 2>/dev/null; sleep 3; set -a && source /home/ccc/ccc/.env && set +a && export BASTION_GRAPH_DB=/opt/bastion/data/bastion_graph.db && nohup ./.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8003 > /tmp/bastion.log 2>&1 & disown" 2>&1 | tail -5
  sleep 10
  curl -s --max-time 8 http://${BASTION_HOST}:8003/health
fi

# 4. attack-ai 94 ERROR supplemental driver 시작
echo "[$(date -Iseconds)] starting attack-ai supplemental driver"
nohup bash results/retest/driver_r3_attack_supplemental.sh > /tmp/attack_supp.log 2>&1 &
SUPP_PID=$!
echo "supplemental driver PID=$SUPP_PID"

echo "=== post_v2_chain done $(date -Iseconds) ==="
