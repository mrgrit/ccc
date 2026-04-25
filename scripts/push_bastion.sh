#!/usr/bin/env bash
# bastion 코드 변경분을 CCC + mrgrit/bastion 양쪽 repo 에 push 하는 원클릭 스크립트.
# CCC 측 commit 은 미리 해두고 이 스크립트는 sync + bastion repo push 만 처리.
# 사용:
#   ./scripts/push_bastion.sh "sync from CCC — <commit msg>"
set -euo pipefail
cd "$(dirname "$0")/.."

MSG="${1:-sync from CCC}"
CCC=$(pwd)
BAS=/home/opsclaw/bastion

if [ ! -d "$BAS/.git" ]; then
    echo "✗ $BAS 에 git repo 없음. 먼저 clone 필요." >&2
    exit 1
fi

# 1. sync — CCC → bastion
echo "[1/3] sync_to_bastion.sh"
bash "$CCC/scripts/sync_to_bastion.sh"

# 2. bastion repo commit
cd "$BAS"
if git diff --quiet HEAD 2>/dev/null; then
    echo "[2/3] bastion repo 변경 없음 — skip"
else
    echo "[2/3] bastion repo commit"
    git add api.py main.py bastion/*.py 2>/dev/null || true
    git commit -m "$MSG" -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
fi

# 3. push
echo "[3/3] push origin main"
git push origin main

echo
echo "=== 완료 ==="
echo "  CCC repo:     $(cd $CCC && git rev-parse --short HEAD)"
echo "  bastion repo: $(cd $BAS && git rev-parse --short HEAD)"
echo "  운영 서버 반영: cd /opt/bastion && ./upgrade.sh"
