#!/usr/bin/env bash
# CCC 의 bastion 코드를 /home/opsclaw/bastion (mrgrit/bastion 클론) 으로 동기화.
# import 경로 변환: packages.bastion → bastion
set -euo pipefail
CCC=/home/opsclaw/ccc
BAS=/home/opsclaw/bastion

echo "=== CCC → bastion 동기화 ==="

# 1. apps/bastion/{api.py,main.py} → bastion/{api.py,main.py}
for f in api.py main.py; do
    sed 's|packages\.bastion\.agent|bastion.agent|g; s|packages\.bastion|bastion|g' \
        "$CCC/apps/bastion/$f" > "$BAS/$f"
    echo "  ✓ $f"
done

# 2. packages/bastion/* → bastion/bastion/*
for f in $(ls "$CCC/packages/bastion/"*.py); do
    name=$(basename "$f")
    sed 's|packages\.bastion\.|bastion.|g; s|from packages\.bastion |from bastion |g' \
        "$f" > "$BAS/bastion/$name"
    echo "  ✓ bastion/$name"
done

# 3. diff 요약
echo
echo "=== 변경 사항 ==="
cd "$BAS" && git status --short

echo
echo "다음 단계: cd $BAS && git add -A && git commit && git push"
