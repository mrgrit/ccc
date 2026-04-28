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

    # 5. 자동 재시작 + import 체인 검증 (R3-noexec 진단: import 실패해도 health=200 zombie process 발생)
    if [ "${REMOTE_RESTART:-1}" = "1" ]; then
        echo
        echo "=== 원격 bastion 자동 재시작 + import 검증 ==="
        RESTART_RESULT=$(sshpass -p "$REMOTE_PASS" ssh -o StrictHostKeyChecking=no "${REMOTE_USER}@${REMOTE_HOST}" \
          "pkill -9 -f 'apps.bastion.api' 2>/dev/null; pkill -9 -f 'uvicorn api:app' 2>/dev/null; pkill -9 -f 'uvicorn.*8003' 2>/dev/null; sleep 3; \
           # 새 로그 파일 (이전 stale log 와 분리)
           : > /tmp/bastion.log; \
           cd /opt/bastion && set -a && source /home/ccc/ccc/.env && set +a && \
           # KG path bug 방지 (2026-04-28): server cwd 따라 분기되면 KG node 손실. 명시 환경변수 export.
           export BASTION_GRAPH_DB="${BASTION_GRAPH_DB:-/home/ccc/ccc/data/bastion_graph.db}" && \
           nohup /opt/bastion/.venv/bin/python3 /opt/bastion/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8003 >> /tmp/bastion.log 2>&1 < /dev/null & disown; \
           # uvicorn startup 완료까지 대기 (chat endpoint warmup 포함)
           sleep 6; \
           # 새 startup 시 import error 체크 - 'ModuleNotFoundError|Traceback|ImportError|SyntaxError' 잡기
           if grep -qE 'ModuleNotFoundError|Traceback|ImportError|SyntaxError|cannot import|NameError' /tmp/bastion.log; then \
             echo '★IMPORT_FAIL★'; \
             grep -E 'ModuleNotFoundError|Traceback|ImportError|SyntaxError|cannot import|NameError' /tmp/bastion.log | head -5; \
             exit 1; \
           fi; \
           # health endpoint 확인
           HEALTH=\$(curl -s --max-time 3 http://localhost:8003/health); \
           echo \"HEALTH: \$HEALTH\" | head -c 200; echo; \
           # /chat lazy import 트리거 (실제 import chain 강제 로드 — 1초 timeout 으로 빠르게)
           timeout 5 curl -s -X POST http://localhost:8003/chat \
             -H 'Content-Type: application/json' \
             -d '{\"message\":\"ping\",\"stream\":false,\"course\":\"test\"}' --max-time 5 \
             > /tmp/chat_ping.log 2>&1 || true; \
           # 두 번째 import error 체크 — chat endpoint 호출 후 import 가 트리거된 경우
           if grep -qE 'ModuleNotFoundError|Traceback|ImportError|cannot import|NameError|SyntaxError' /tmp/bastion.log; then \
             echo '★CHAT_IMPORT_FAIL★'; \
             grep -E 'ModuleNotFoundError|Traceback|ImportError|cannot import|NameError|SyntaxError' /tmp/bastion.log | tail -5; \
             exit 1; \
           fi; \
           ps -ef | grep -E 'uvicorn.*8003' | grep -v grep | head -1; \
           echo '★OK★'" 2>&1)
        echo "$RESTART_RESULT" | tail -10
        if echo "$RESTART_RESULT" | grep -q "★OK★"; then
            echo "  ✓ bastion 재시작 + import chain 검증 OK"
        else
            echo "  ❌ bastion 재시작 실패 — import error 가능성 (위 로그 확인)"
            echo "  ❌ ROLLBACK: 옛 stable 코드 사용 권고 — 새 변경 review 필요"
            exit 2
        fi
    else
        echo "  ⚠️ REMOTE_RESTART=0 — 자동 재시작 건너뜀"
    fi
fi

echo
echo "다음 단계: cd $BAS && git add -A && git commit && git push"
