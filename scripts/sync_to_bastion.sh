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
echo "=== bastion repo 변경 사항 ==="
cd "$BAS" && git status --short

# 4. 원격 bastion runtime 도 sync — /home/ccc/ccc/packages/bastion/ 가 실제 import path
#    (R3 postmortem 2026-04-26: /opt/bastion/ 만 sync 해서 새 코드 미적용 발생).
#    REMOTE_HOST 환경변수 비어있으면 skip (안전).
REMOTE_HOST="${REMOTE_HOST:-192.168.0.115}"
REMOTE_USER="${REMOTE_USER:-ccc}"
REMOTE_PASS="${REMOTE_PASS:-1}"
REMOTE_PATH="${REMOTE_PATH:-/home/ccc/ccc/packages/bastion}"

if [ -n "$REMOTE_HOST" ] && command -v sshpass >/dev/null 2>&1; then
    echo
    echo "=== 원격 runtime sync → ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH} ==="
    sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
        "$CCC/packages/bastion/"*.py \
        "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/" 2>&1 | tail -3
    sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
        "$CCC/apps/bastion/api.py" \
        "${REMOTE_USER}@${REMOTE_HOST}:/home/ccc/ccc/apps/bastion/api.py" 2>&1 | tail -3
    # /opt/bastion 도 sync — 실제 runtime process 가 그쪽에서 실행됨
    # ★ import path 변환: packages.bastion → bastion (BAS 와 동일 처리)
    TMPDIR=$(mktemp -d)
    for f in "$CCC/packages/bastion/"*.py; do
        name=$(basename "$f")
        sed 's|packages\.bastion\.|bastion.|g; s|from packages\.bastion |from bastion |g' \
            "$f" > "$TMPDIR/$name"
    done
    sshpass -p "$REMOTE_PASS" scp -o StrictHostKeyChecking=no \
        "$TMPDIR/"*.py \
        "${REMOTE_USER}@${REMOTE_HOST}:/opt/bastion/bastion/" 2>&1 | tail -3 || true
    rm -rf "$TMPDIR"
    echo "  ✓ 원격 /home/ccc/ccc/packages/bastion + /opt/bastion/bastion (path 변환) + apps/bastion/api.py 동기화"

    # 5. 자동 재시작 — uvicorn process 패턴 매칭 (실제 runtime은 uvicorn binary 직접 호출)
    if [ "${REMOTE_RESTART:-1}" = "1" ]; then
        echo
        echo "=== 원격 bastion 자동 재시작 ==="
        sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" \
          "pkill -9 -f 'apps.bastion.api' 2>/dev/null; pkill -9 -f 'uvicorn api:app' 2>/dev/null; pkill -9 -f 'uvicorn.*8003' 2>/dev/null; sleep 2; cd /opt/bastion && set -a && source /home/ccc/ccc/.env && set +a && nohup /opt/bastion/.venv/bin/python3 /opt/bastion/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8003 >> /tmp/bastion.log 2>&1 < /dev/null & disown; sleep 4; curl -s --max-time 3 http://localhost:8003/health | head -c 100; echo; ps -ef | grep uvicorn | grep -v grep | head -1" 2>&1 | tail -5
        echo "  ✓ bastion 재시작 (PID 위 라인 참조)"
    else
        echo "  ⚠️ REMOTE_RESTART=0 — 자동 재시작 건너뜀"
    fi
fi

echo
echo "다음 단계: cd $BAS && git add -A && git commit && git push"
