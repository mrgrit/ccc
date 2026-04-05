#!/usr/bin/env python3
"""bastion — CCC 운영 관리 에이전트

Claude Code + Ollama 오픈모델 기반.
자체 경량 프록시로 Ollama를 Anthropic Messages API 호환으로 변환.

Usage:
    python -m apps.bastion.main
    ./dev.sh bastion
"""
import os
import sys
import subprocess
import time
import threading

CCC_DIR = os.path.join(os.path.dirname(__file__), "..", "..")

# .env 로드
ENV_PATH = os.path.join(CCC_DIR, ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
PROXY_PORT = int(os.getenv("BASTION_PROXY_PORT", "4100"))
PROXY_URL = f"http://127.0.0.1:{PROXY_PORT}"


def start_proxy():
    """자체 경량 프록시 시작 (Ollama → Anthropic API)"""
    # 이미 떠있는지 확인
    try:
        import httpx
        r = httpx.get(f"{PROXY_URL}/health", timeout=2.0)
        if r.status_code == 200:
            print(f"[bastion] 프록시 이미 실행 중 ({PROXY_URL})")
            return
    except Exception:
        pass

    # 백그라운드 스레드로 프록시 실행
    from apps.bastion.proxy import run as run_proxy
    t = threading.Thread(target=run_proxy, args=(PROXY_PORT,), daemon=True)
    t.start()

    # 준비 대기
    print(f"[bastion] 프록시 시작 (Ollama {LLM_BASE_URL} → Anthropic API)...", end="", flush=True)
    for _ in range(10):
        time.sleep(0.5)
        try:
            import httpx
            r = httpx.get(f"{PROXY_URL}/health", timeout=1.0)
            if r.status_code == 200:
                print(" ready")
                return
        except Exception:
            pass
        print(".", end="", flush=True)

    print("\n[bastion] ERROR: 프록시 시작 실패")
    sys.exit(1)


def main():
    # claude CLI 확인/설치
    claude_path = os.popen("which claude 2>/dev/null").read().strip()
    if not claude_path:
        print("[bastion] Claude Code CLI 설치 중...")
        subprocess.run(["sudo", "npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
        claude_path = os.popen("which claude 2>/dev/null").read().strip()
        if not claude_path:
            print("[bastion] ERROR: claude CLI 설치 실패")
            sys.exit(1)

    # 프록시 시작
    start_proxy()

    # CCC.md 시스템 프롬프트
    ccc_md = os.path.join(CCC_DIR, "CCC.md")
    system_prompt = ""
    if os.path.exists(ccc_md):
        with open(ccc_md, encoding="utf-8") as f:
            system_prompt = f.read()

    # Claude Code 실행
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = PROXY_URL
    env["ANTHROPIC_API_KEY"] = "sk-dummy"

    cmd = [claude_path]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    print(f"[bastion] Claude Code 시작 (모델: {LLM_MODEL})")
    print(f"[bastion] CCC 경로: {CCC_DIR}")
    print()

    try:
        proc = subprocess.run(cmd, env=env, cwd=CCC_DIR)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
