#!/usr/bin/env python3
"""bastion — CCC 운영 관리 에이전트

Claude Code + Ollama 오픈모델 기반.
litellm 프록시로 Ollama를 Anthropic API 호환으로 변환 후
Claude Code CLI를 CCC 운영 시스템 프롬프트로 실행.

Usage:
    python -m apps.bastion.main
    ./dev.sh bastion
"""
import os
import sys
import subprocess
import signal
import time

CCC_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
ENV_PATH = os.path.join(CCC_DIR, ".env")

# .env 로드
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
LITELLM_PORT = int(os.getenv("LITELLM_PORT", "4100"))
PROXY_URL = f"http://localhost:{LITELLM_PORT}"

litellm_proc = None


def start_litellm():
    """litellm 프록시 시작 — Ollama를 Anthropic API 호환으로"""
    global litellm_proc

    # 이미 떠있는지 확인
    try:
        import httpx
        r = httpx.get(f"{PROXY_URL}/health", timeout=2.0)
        if r.status_code == 200:
            print(f"[bastion] litellm 프록시 이미 실행 중 ({PROXY_URL})")
            return True
    except Exception:
        pass

    print(f"[bastion] litellm 프록시 시작 (Ollama {LLM_BASE_URL} → Anthropic API)...")
    print(f"[bastion] 모델: ollama/{LLM_MODEL}")

    litellm_proc = subprocess.Popen(
        [sys.executable, "-m", "litellm",
         "--model", f"ollama/{LLM_MODEL}",
         "--api_base", LLM_BASE_URL,
         "--port", str(LITELLM_PORT),
         "--drop_params",
         ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 프록시 준비 대기
    for i in range(15):
        time.sleep(1)
        try:
            import httpx
            r = httpx.get(f"{PROXY_URL}/health", timeout=2.0)
            if r.status_code == 200:
                print(f"[bastion] litellm 프록시 ready ({PROXY_URL})")
                return True
        except Exception:
            pass
        print(".", end="", flush=True)

    print(f"\n[bastion] ERROR: litellm 프록시 시작 실패")
    return False


def stop_litellm():
    global litellm_proc
    if litellm_proc:
        litellm_proc.terminate()
        litellm_proc.wait(timeout=5)
        litellm_proc = None


def main():
    # litellm 설치 확인
    try:
        import litellm
    except ImportError:
        print("[bastion] litellm 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "litellm", "-q"], check=True)

    # claude CLI 확인/설치
    claude_path = os.popen("which claude 2>/dev/null").read().strip()
    if not claude_path:
        print("[bastion] Claude Code CLI 설치 중...")
        subprocess.run(["npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
        claude_path = os.popen("which claude 2>/dev/null").read().strip()
        if not claude_path:
            print("[bastion] ERROR: claude CLI 설치 실패")
            sys.exit(1)

    # litellm 프록시 시작
    if not start_litellm():
        sys.exit(1)

    # CCC.md를 시스템 프롬프트로 사용
    ccc_md = os.path.join(CCC_DIR, "CCC.md")
    system_prompt = ""
    if os.path.exists(ccc_md):
        with open(ccc_md, encoding="utf-8") as f:
            system_prompt = f.read()

    # Claude Code 실행 — Ollama 백엔드
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = PROXY_URL
    env["ANTHROPIC_API_KEY"] = "sk-dummy"  # litellm 프록시는 키 검증 안 함
    env["CLAUDE_CODE_USE_BEDROCK"] = ""
    env["CLAUDE_CODE_USE_VERTEX"] = ""

    cmd = [claude_path]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    print(f"[bastion] Claude Code 시작 (모델: {LLM_MODEL} via litellm)")
    print(f"[bastion] CCC 경로: {CCC_DIR}")
    print()

    try:
        proc = subprocess.run(cmd, env=env, cwd=CCC_DIR)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        pass
    finally:
        stop_litellm()


if __name__ == "__main__":
    main()
