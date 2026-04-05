#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== CCC Setup ==="

# 1. 시스템 패키지 + Node.js 22 LTS
echo "[1/5] 시스템 패키지 설치..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv sshpass ca-certificates curl gnupg \
        locales fonts-nanum fonts-noto-cjk fbterm

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

    # fbterm 권한 설정 (일반 유저가 framebuffer 접근)
    sudo chmod u+s /usr/bin/fbterm 2>/dev/null || true
    sudo usermod -aG video "$(whoami)" 2>/dev/null || true

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

# Claude Code CLI 설치 (bastion용)
if ! command -v claude &>/dev/null; then
    echo "  Claude Code CLI 설치..."
    npm install -g @anthropic-ai/claude-code 2>/dev/null || true
fi

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

# 5. Docker + PostgreSQL
echo "[5/5] Docker + PostgreSQL..."
if ! command -v docker &>/dev/null; then
    echo "  Docker 설치 중..."
    if command -v apt-get &>/dev/null; then
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
          https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
          sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update -y
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y docker docker-compose-plugin
        sudo systemctl enable --now docker
    fi
    sudo usermod -aG docker "$(whoami)" 2>/dev/null || true
    # 재로그인 없이 현재 세션에 그룹 적용
    newgrp docker <<NEWGRP
echo "  Docker 그룹 적용됨"
NEWGRP
    echo "  Docker 설치 완료"
fi

# docker 권한 확인 — sudo 없이 안 되면 sudo로 실행
_docker() {
    if docker info &>/dev/null; then
        docker "$@"
    else
        sudo docker "$@"
    fi
}

if _docker compose version &>/dev/null; then
    _docker compose -f docker/docker-compose.yaml up -d postgres
elif sudo docker-compose version &>/dev/null; then
    sudo docker-compose -f docker/docker-compose.yaml up -d postgres
else
    echo "  ERROR: docker compose를 실행할 수 없습니다."
    exit 1
fi
echo "  PostgreSQL 시작됨 (port ${DB_PORT:-5434})"

# 6. API 시작 + 관리자 계정 생성
echo "[6/6] 초기 관리자 계정 생성..."
source .venv/bin/activate
set -a; [ -f .env ] && source .env; set +a
export PYTHONPATH="$(pwd)"

# API 임시 시작 (백그라운드)
python3 -m uvicorn apps.ccc_api.src.main:app --host 0.0.0.0 --port 9100 > /tmp/ccc-api-setup.log 2>&1 &
API_PID=$!

# API 준비 대기
echo -n "  API 시작 대기..."
for i in $(seq 1 15); do
    if curl -s http://localhost:9100/api/health > /dev/null 2>&1; then
        echo " ready"
        break
    fi
    echo -n "."
    sleep 1
done

# admin 계정 생성
ADMIN_RESULT=$(curl -s -X POST http://localhost:9100/api/auth/create-admin \
    -H "Content-Type: application/json" \
    -d '{"student_id":"admin","name":"관리자","password":"admin1234"}' 2>/dev/null)

if echo "$ADMIN_RESULT" | grep -q '"role":"admin"'; then
    echo "  관리자 계정 생성 완료: admin / admin1234"
else
    echo "  관리자 계정이 이미 존재하거나 생성 실패"
fi

# 임시 API 종료
kill $API_PID 2>/dev/null
wait $API_PID 2>/dev/null

echo ""
echo "========================================"
echo "  CCC 설치 완료"
echo "========================================"
echo ""
echo "  실행:  ./dev.sh api"
echo "  접속:  http://$(hostname -I | awk '{print $1}'):9100/app/"
echo "  관리자: admin / admin1234"
echo ""
echo "  Bastion: ./dev.sh bastion"
echo ""
echo "  설정 (.env):"
echo "    LLM_BASE_URL=http://your-ollama-server:11434"
echo "    LLM_MODEL=gemma3:4b"
echo "========================================"
