#!/usr/bin/env python3
"""bastion — CCC 운영 관리 에이전트

open-interpreter + Ollama 기반. Claude Code 스타일 대화형 에이전트.
자연어로 CCC 플랫폼 운영, 인프라 관리, 파일 편집, 코드 실행 가능.

Usage:
    python -m apps.bastion.main
    ./dev.sh bastion
"""
import os
import sys
import subprocess

CCC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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


def load_system_prompt() -> str:
    """CCC.md + 운영 컨텍스트를 시스템 프롬프트로"""
    parts = []

    ccc_md = os.path.join(CCC_DIR, "CCC.md")
    if os.path.exists(ccc_md):
        with open(ccc_md, encoding="utf-8") as f:
            parts.append(f.read())

    parts.append(f"""
현재 환경:
- CCC 경로: {CCC_DIR}
- LLM: {LLM_BASE_URL} / {LLM_MODEL}
- OS: {os.popen('uname -a 2>/dev/null || ver').read().strip()}

너는 CCC(Cyber Combat Commander) 사이버보안 교육 플랫폼의 운영 관리 에이전트다.
서버 관리, 서비스 시작/중지, 인프라 관리, 파일 편집, 코드 실행, 문제 해결 등
관리자가 요청하는 모든 작업을 수행한다.

CCC 서비스 관리:
- API 시작: cd {CCC_DIR} && ./dev.sh api
- API 중지: pkill -f 'uvicorn apps.ccc_api'
- DB 시작: docker compose -f {CCC_DIR}/docker/docker-compose.yaml up -d postgres
- UI 빌드: cd {CCC_DIR}/apps/ccc-ui && npm run build
- 배포: cd {CCC_DIR} && git pull && ./upgrade.sh

파괴적 작업(rm -rf /, DROP TABLE) 금지. 위험 명령 실행 전 사용자 확인.
""")

    return "\n\n".join(parts)


def main():
    # open-interpreter 설치 확인
    try:
        import interpreter
    except ImportError:
        print("[bastion] open-interpreter 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "open-interpreter", "-q"], check=True)
        import interpreter

    from interpreter import interpreter as oi

    # Ollama 설정
    oi.llm.model = f"ollama/{LLM_MODEL}"
    oi.llm.api_base = LLM_BASE_URL
    oi.llm.api_key = "dummy"

    # 시스템 프롬프트
    oi.system_message = load_system_prompt()

    # 설정
    oi.auto_run = False          # 코드 실행 전 확인
    oi.loop = True               # 대화 루프
    oi.offline = True            # 인터넷 체크 스킵

    print(f"[bastion] CCC 운영 에이전트")
    print(f"[bastion] 모델: {LLM_MODEL} ({LLM_BASE_URL})")
    print(f"[bastion] CCC: {CCC_DIR}")
    print()

    # 대화 시작
    oi.chat()


if __name__ == "__main__":
    main()
