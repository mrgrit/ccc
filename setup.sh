#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== CCC Setup ==="

# 1. 시스템 패키지 + Node.js 22 LTS
echo "[1/5] 시스템 패키지 설치..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv sshpass ca-certificates curl gnupg \
        locales fonts-nanum fonts-noto-cjk

    # 한국어 로케일 설정 (UTF-8)
    sudo locale-gen ko_KR.UTF-8 2>/dev/null || true
    sudo update-locale LANG=ko_KR.UTF-8 LC_ALL=ko_KR.UTF-8 2>/dev/null || true

    # 현재 세션 + 이후 세션에도 적용
    for rc in ~/.bashrc ~/.profile; do
        if [ -f "$rc" ] && ! grep -q 'export LANG=ko_KR.UTF-8' "$rc" 2>/dev/null; then
            echo 'export LANG=ko_KR.UTF-8' >> "$rc"
            echo 'export LC_ALL=ko_KR.UTF-8' >> "$rc"
        fi
    done
    export LANG=ko_KR.UTF-8
    export LC_ALL=ko_KR.UTF-8

    # Node.js 22 LTS (Vite 8 요구: >=20.19 or >=22.12)
    NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v\([0-9]*\).*/\1/' || echo "0")
    if [ "$NODE_MAJOR" -lt 22 ]; then
        echo "  Node.js 22 LTS 설치 중 (현재: $(node --version 2>/dev/null || echo '없음'))..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
        sudo apt-get install -y nodejs
        echo "  Node.js $(node --version) 설치 완료"
    else
        echo "  Node.js $(node --version) OK"
    fi
elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip python3-virtualenv sshpass
    curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
    sudo dnf install -y nodejs
fi

# 2. Python venv + 의존성
echo "[2/5] Python 가상환경 + 의존성 설치..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. UI 빌드
echo "[3/5] UI 빌드..."
cd apps/ccc-ui
npm install
npm run build
cd ../..

# 4. 환경 설정
echo "[4/5] 환경 설정..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  .env 생성됨 — LLM_BASE_URL과 LLM_MODEL을 환경에 맞게 수정하세요"
else
    echo "  .env 이미 존재"
fi

# 5. PostgreSQL (Docker)
echo "[5/5] PostgreSQL..."
if command -v docker &>/dev/null; then
    docker compose -f docker/docker-compose.yaml up -d postgres
    echo "  PostgreSQL 시작됨 (port ${DB_PORT:-5434})"
else
    echo "  Docker 미설치 — PostgreSQL을 수동으로 설정하세요"
    echo "  DB URL: postgresql://ccc:ccc@127.0.0.1:5434/ccc"
fi

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "실행:"
echo "  source .venv/bin/activate"
echo "  ./dev.sh api              # API 서버 (:9100)"
echo "  ./dev.sh bastion          # Bastion 에이전트 (TUI)"
echo "  브라우저: http://localhost:9100/app/"
echo ""
echo "설정 (.env):"
echo "  LLM_BASE_URL=http://your-ollama-server:11434"
echo "  LLM_MODEL=gemma3:4b"
