#!/usr/bin/env bash
# student-setup.sh — 학생 PC에서 CCC 실습 인프라를 자동 구축하는 스크립트
# Usage: curl -sL https://ccc-server/scripts/student-setup.sh | bash -s -- <student-id> <ccc-server-url>
set -euo pipefail

STUDENT_ID="${1:?학생 ID를 입력하세요}"
CCC_SERVER="${2:-http://localhost:9100}"
API_KEY="${CCC_API_KEY:-ccc-api-key-2026}"

echo "========================================"
echo "  Cyber Combat Commander — 인프라 구축"
echo "  학생: $STUDENT_ID"
echo "  서버: $CCC_SERVER"
echo "========================================"

# 1. 시스템 요구사항 확인
echo "[1/5] 시스템 요구사항 확인..."
command -v python3 >/dev/null || { echo "ERROR: python3 필요"; exit 1; }
command -v ssh >/dev/null || { echo "ERROR: ssh 필요"; exit 1; }

# 2. Python 의존성 설치
echo "[2/5] Python 의존성 설치..."
pip3 install --quiet httpx psycopg2-binary paramiko 2>/dev/null || pip install --quiet httpx psycopg2-binary paramiko

# 3. SubAgent 설치
echo "[3/5] SubAgent 설치..."
SUBAGENT_DIR="$HOME/.ccc/subagent"
mkdir -p "$SUBAGENT_DIR"
# TODO: 중앙서버에서 SubAgent 패키지 다운로드
echo "  SubAgent 디렉토리: $SUBAGENT_DIR (M7에서 자동 다운로드 구현)"

# 4. 인프라 등록
echo "[4/5] 중앙서버에 인프라 등록..."
MY_IP=$(hostname -I | awk '{print $1}')
curl -s -X POST "$CCC_SERVER/infras" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$STUDENT_ID\",\"infra_name\":\"$(hostname)\",\"ip\":\"$MY_IP\"}" | python3 -m json.tool

# 5. 헬스체크
echo "[5/5] 헬스체크..."
echo "  IP: $MY_IP"
echo "  SubAgent: http://$MY_IP:8002 (설치 완료 후 활성화)"

echo ""
echo "========================================"
echo "  인프라 구축 완료!"
echo "  CCC CLI: ccc progress $STUDENT_ID"
echo "========================================"
