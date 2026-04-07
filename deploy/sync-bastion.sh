#!/usr/bin/env bash
# CCC → bastion 레포 동기화
# CCC의 packages/bastion/ 코드를 bastion 독립 레포로 복사 + push
set -euo pipefail

CCC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASTION_REPO="${BASTION_REPO:-/home/ccc/bastion}"
GITHUB_URL="https://github.com/mrgrit/bastion.git"

echo "=== CCC → Bastion 동기화 ==="
echo "  CCC: $CCC_DIR"
echo "  Bastion: $BASTION_REPO"

# bastion 레포 없으면 clone
if [ ! -d "$BASTION_REPO/.git" ]; then
    echo "  Cloning bastion repo..."
    git clone "$GITHUB_URL" "$BASTION_REPO"
fi

# 1. 코어 코드 복사 (CCC → bastion)
echo "[1/4] 코어 코드 동기화..."
for f in __init__.py agent.py skills.py playbook.py prompt.py verify.py lab_verify.py rag.py; do
    src="$CCC_DIR/packages/bastion/$f"
    dst="$BASTION_REPO/bastion/$f"
    if [ -f "$src" ]; then
        cp "$src" "$dst"
        # import 경로 변환: packages.bastion → bastion
        sed -i 's|from packages\.bastion import|from bastion import|g' "$dst"
        sed -i 's|from packages\.bastion\.|from bastion.|g' "$dst"
    fi
done

# 2. TUI 복사
echo "[2/4] TUI 동기화..."
cp "$CCC_DIR/apps/bastion/main.py" "$BASTION_REPO/main.py"
sed -i 's|from packages\.bastion|from bastion|g' "$BASTION_REPO/main.py"

# 3. Playbook 동기화
echo "[3/4] Playbook 동기화..."
mkdir -p "$BASTION_REPO/contents/playbooks"
cp "$CCC_DIR/contents/playbooks/"*.yaml "$BASTION_REPO/contents/playbooks/" 2>/dev/null || true

# 4. CCC.md
cp "$CCC_DIR/CCC.md" "$BASTION_REPO/" 2>/dev/null || true

# 변경사항 확인
cd "$BASTION_REPO"
CHANGES=$(git status --short | wc -l)
if [ "$CHANGES" -eq 0 ]; then
    echo "  이미 동기화됨 (변경 없음)"
    exit 0
fi

echo "[4/4] Commit + Push..."
git add -A
git commit -m "sync: CCC → bastion 코드 동기화 ($(date +%Y-%m-%d))"

# push (토큰이 있으면)
if [ -n "${GITHUB_TOKEN:-}" ]; then
    git push "https://${GITHUB_TOKEN}@github.com/mrgrit/bastion.git" main
    echo "  Push 완료"
else
    echo "  Push 필요: cd $BASTION_REPO && git push"
fi

echo "=== 동기화 완료 ($CHANGES files) ==="
