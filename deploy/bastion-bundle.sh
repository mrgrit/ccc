#!/usr/bin/env bash
# Bastion 독립 배포 번들 생성
# CCC 서버에서 실행하여 /tmp/bastion-bundle.tar.gz 생성
set -euo pipefail

BUNDLE_DIR="/tmp/bastion-bundle"
CCC_DIR="$(cd "$(dirname "$0")/.." && pwd)"

rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"/{packages/bastion,apps/bastion,contents/playbooks}

# 필요한 파일만 복사
cp "$CCC_DIR/packages/bastion/__init__.py" "$BUNDLE_DIR/packages/bastion/"
cp "$CCC_DIR/packages/bastion/agent.py" "$BUNDLE_DIR/packages/bastion/"
cp "$CCC_DIR/packages/bastion/skills.py" "$BUNDLE_DIR/packages/bastion/"
cp "$CCC_DIR/packages/bastion/playbook.py" "$BUNDLE_DIR/packages/bastion/"
cp "$CCC_DIR/packages/bastion/prompt.py" "$BUNDLE_DIR/packages/bastion/"
cp "$CCC_DIR/packages/bastion/verify.py" "$BUNDLE_DIR/packages/bastion/"
touch "$BUNDLE_DIR/packages/__init__.py"

cp "$CCC_DIR/apps/bastion/main.py" "$BUNDLE_DIR/apps/bastion/"
touch "$BUNDLE_DIR/apps/__init__.py"
touch "$BUNDLE_DIR/apps/bastion/__init__.py"

cp "$CCC_DIR/contents/playbooks/"*.yaml "$BUNDLE_DIR/contents/playbooks/" 2>/dev/null || true

# 최소 requirements
cat > "$BUNDLE_DIR/requirements.txt" << 'EOF'
httpx>=0.28
pyyaml>=6.0
rich>=14.0
pydantic>=2.0
EOF

# 실행 스크립트
cat > "$BUNDLE_DIR/bastion.sh" << 'RUNEOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] || python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -q 2>/dev/null
[ -f .env ] && set -a && source .env && set +a
export PYTHONPATH="$(pwd)"
python3 apps/bastion/main.py
RUNEOF
chmod +x "$BUNDLE_DIR/bastion.sh"

# CCC.md (운영 지침)
cp "$CCC_DIR/CCC.md" "$BUNDLE_DIR/" 2>/dev/null || true

# tar
cd /tmp
tar czf bastion-bundle.tar.gz -C bastion-bundle .
echo "Bundle created: /tmp/bastion-bundle.tar.gz ($(du -sh /tmp/bastion-bundle.tar.gz | cut -f1))"
echo "Deploy: scp bastion-bundle.tar.gz user@manager-vm:/opt/ && ssh user@manager-vm 'mkdir -p /opt/bastion && tar xzf /opt/bastion-bundle.tar.gz -C /opt/bastion && /opt/bastion/bastion.sh'"
