#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/sshd_setup.sh

# /opt/ccc 가 마운트되어 있어야 함 (compose volumes).
if [ ! -f /opt/ccc/apps/bastion/api.py ]; then
    echo "[bastion] /opt/ccc 마운트 누락 — sshd 만 띄우고 대기"
    exec /usr/sbin/sshd -D -e
fi

# .env 자동 생성 (호스트 .env 의 일부 키만 bastion 이 사용).
mkdir -p /opt/ccc/apps/bastion
cat > /opt/ccc/apps/bastion/.env <<EOF
LLM_BASE_URL=${LLM_BASE_URL:-http://host.docker.internal:11434}
LLM_MANAGER_MODEL=${LLM_MANAGER_MODEL:-gpt-oss:120b}
LLM_SUBAGENT_MODEL=${LLM_SUBAGENT_MODEL:-gemma3:4b}
CCC_API_KEY=${CCC_API_KEY:-ccc-api-key-2026}
JWT_SECRET=${JWT_SECRET:-ccc-jwt-secret-2026}
EOF

# sshd 백그라운드, bastion API 포어그라운드.
/usr/sbin/sshd -e
echo "[bastion] uvicorn :8003"
cd /opt/ccc
exec python3 -m uvicorn apps.bastion.api:app --host 0.0.0.0 --port 8003
