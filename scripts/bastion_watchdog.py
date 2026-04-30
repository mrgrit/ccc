#!/usr/bin/env python3
"""bastion server watchdog — health check + auto-restart on failure.

R3 main 측정 시 attack-ai 94 ERROR (Connection refused) 발생.
원인: bastion server crash + driver 가 retry 안 함.

사용:
    python3 scripts/bastion_watchdog.py --interval 60 --restart-cmd 'sshpass -p 1 ssh ccc@192.168.0.103 ...'

5번 연속 health fail 시:
1. bastion process kill
2. server restart
3. health check 재시도
4. 결과 log

Cron 또는 systemd 와 통합 가능.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import time
import urllib.request
import urllib.error
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG = ROOT / "results/retest/bastion_watchdog.log"
HEALTH_URL = os.getenv("BASTION_HEALTH", "http://192.168.0.103:8003/health")
RESTART_HOST = os.getenv("BASTION_HOST", "192.168.0.103")
RESTART_USER = os.getenv("BASTION_USER", "ccc")
RESTART_PASS = os.getenv("BASTION_PASS", "1")


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    print(line, end="", flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(line)


def check_health(timeout: float = 5.0) -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
        return False


def restart_server() -> bool:
    """SSH + restart bastion. 비동기 안전 — 5분 timeout."""
    cmd = (
        f"pkill -9 -f 'uvicorn api:app' 2>/dev/null; sleep 3; "
        f"cd /opt/bastion && set -a && source /home/ccc/ccc/.env && set +a && "
        f"export BASTION_GRAPH_DB=/opt/bastion/data/bastion_graph.db && "
        f"nohup ./.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8003 "
        f"> /tmp/bastion.log 2>&1 & disown; sleep 8; "
        f"curl -s --max-time 5 http://localhost:8003/health"
    )
    full = ["sshpass", "-p", RESTART_PASS, "ssh",
            "-o", "StrictHostKeyChecking=no",
            f"{RESTART_USER}@{RESTART_HOST}", cmd]
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=300)
        out = (r.stdout + r.stderr).strip()
        ok = '"status":"ok"' in out
        log(f"restart {'OK' if ok else 'FAIL'}: {out[:200]}")
        return ok
    except subprocess.TimeoutExpired:
        log("restart TIMEOUT (5min)")
        return False
    except Exception as e:
        log(f"restart EXCEPTION: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60, help="check interval (s)")
    ap.add_argument("--threshold", type=int, default=5, help="consecutive fails before restart")
    ap.add_argument("--once", action="store_true", help="single check, no loop")
    args = ap.parse_args()

    log(f"watchdog start: interval={args.interval}s threshold={args.threshold} url={HEALTH_URL}")
    fails = 0
    while True:
        ok = check_health()
        if ok:
            if fails > 0:
                log(f"recovered after {fails} fails")
            fails = 0
        else:
            fails += 1
            log(f"health fail #{fails}/{args.threshold}")
            if fails >= args.threshold:
                log(f"threshold reached → restart")
                if restart_server():
                    fails = 0
                else:
                    log(f"restart failed, will retry next cycle")
                    fails = args.threshold - 1  # don't spam

        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
