"""bastion — CCC 운영 관리 에이전트

Claude Code 아키텍처를 참고한 CCC 인프라/운영 관리 시스템.
시스템 프롬프트 동적 조합 + SubAgent 제어 + SSH 온보딩 + 헬스체크.

핵심 기능:
1. 인프라 온보딩 (SSH → SubAgent 설치)
2. 헬스체크 (SubAgent 상태 확인)
3. SubAgent 명령 실행 (A2A 프로토콜)
4. LLM 기반 작업 디스패치 (스킬 시스템)
5. 시스템 상태 모니터링
"""
from __future__ import annotations
import os
import json
import subprocess
from typing import Any

import httpx

# ── Config ────────────────────────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
SUBAGENT_PORT = 8002
SSH_TIMEOUT = 30

# ── System Prompt Sections (bastion/src/constants 참고) ──

PROMPT_SECTIONS = {
    "identity": """너는 CCC(Cyber Combat Commander)의 Bastion 운영 에이전트다.
사이버보안 교육 플랫폼의 인프라를 관리하고, 학생 VM에 SubAgent를 설치/관리하며,
시스템 상태를 모니터링하는 것이 주 임무다.""",

    "capabilities": """사용 가능한 스킬:
- onboard: VM에 SSH 접속하여 SubAgent 설치 + 역할별 소프트웨어 배포
- health_check: SubAgent 상태 확인 (A2A /health 엔드포인트)
- run_command: SubAgent에 명령 실행 (A2A /a2a/run_script)
- system_status: 전체 인프라 상태 요약
- diagnose: VM 문제 진단 및 해결 방안 제시""",

    "constraints": """제약사항:
- 학생 VM에 직접 SSH 접속은 온보딩 시에만 허용
- 온보딩 완료 후에는 반드시 SubAgent(A2A)를 통해서만 명령 실행
- 파괴적 작업(rm -rf, 디스크 포맷 등) 실행 금지
- 학생 데이터 삭제 금지""",

    "roles": """VM 역할별 소프트웨어:
- attacker (Kali): nmap, metasploit, hydra, sqlmap, nikto, gobuster
- secu (Security GW): nftables, suricata, sysmon, osquery, auditd
- web (Web Server): apache2, modsecurity, docker(juiceshop/dvwa)
- siem (SIEM): wazuh-manager, sigma, opencti, elasticsearch
- windows (분석): sysmon, osquery (OpenSSH 필요)
- manager (Manager AI): ollama, ccc-bastion subagent""",
}


def build_system_prompt(extra_context: str = "") -> str:
    """시스템 프롬프트 동적 조합 (bastion의 resolveSystemPromptSections 참고)"""
    sections = [PROMPT_SECTIONS[k] for k in PROMPT_SECTIONS]
    if extra_context:
        sections.append(f"현재 상황:\n{extra_context}")
    return "\n\n".join(sections)


# ── SSH Onboarding ────────────────────────────────

# 역할별 설치 스크립트
ROLE_SETUP_SCRIPTS: dict[str, list[str]] = {
    "attacker": [
        "apt-get update -y",
        "apt-get install -y nmap hydra sqlmap nikto dirb gobuster seclists",
    ],
    "secu": [
        "apt-get update -y",
        "apt-get install -y nftables suricata auditd",
        "sysctl -w net.ipv4.ip_forward=1",
        "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf",
    ],
    "web": [
        "apt-get update -y",
        "apt-get install -y apache2 docker.io",
        "systemctl enable --now docker",
        "docker pull bkimminich/juice-shop 2>/dev/null || true",
    ],
    "siem": [
        "apt-get update -y",
        "curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh 2>/dev/null || true",
    ],
    "manager": [
        "curl -fsSL https://ollama.ai/install.sh | sh",
        f"ollama pull {LLM_MODEL}",
    ],
}

# SubAgent 설치 스크립트 (공통)
SUBAGENT_INSTALL_SCRIPT = """#!/bin/bash
set -e
mkdir -p /opt/ccc-subagent
cat > /opt/ccc-subagent/agent.py << 'AGENT_EOF'
#!/usr/bin/env python3
\"\"\"CCC SubAgent — A2A 프로토콜 기반 경량 에이전트\"\"\"
import json, subprocess, os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SubAgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            info = {
                "status": "healthy",
                "hostname": os.uname().nodename,
                "role": os.getenv("CCC_ROLE", "unknown"),
            }
            self.wfile.write(json.dumps(info).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/a2a/run_script":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            script = body.get("script", "echo ok")
            timeout = body.get("timeout", 60)
            try:
                r = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=timeout)
                result = {"exit_code": r.returncode, "stdout": r.stdout[:10000], "stderr": r.stderr[:5000]}
            except subprocess.TimeoutExpired:
                result = {"exit_code": -1, "stdout": "", "stderr": "timeout"}
            except Exception as e:
                result = {"exit_code": -1, "stdout": "", "stderr": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress logs

if __name__ == "__main__":
    port = int(os.getenv("SUBAGENT_PORT", "8002"))
    print(f"CCC SubAgent listening on :{port}")
    HTTPServer(("0.0.0.0", port), SubAgentHandler).serve_forever()
AGENT_EOF

cat > /etc/systemd/system/ccc-subagent.service << 'SVC_EOF'
[Unit]
Description=CCC SubAgent
After=network.target
[Service]
Type=simple
Environment=CCC_ROLE={role}
ExecStart=/usr/bin/python3 /opt/ccc-subagent/agent.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
SVC_EOF

systemctl daemon-reload
systemctl enable --now ccc-subagent
"""


def ssh_run(ip: str, user: str, password: str, commands: list[str]) -> dict:
    """SSH로 명령 실행 (subprocess + sshpass 사용)"""
    script = " && ".join(commands)
    cmd = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
        f"{user}@{ip}", f"sudo bash -c '{script}'"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=SSH_TIMEOUT)
        return {"success": r.returncode == 0, "stdout": r.stdout[:5000], "stderr": r.stderr[:2000]}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "SSH timeout"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}


def onboard_vm(ip: str, role: str, user: str = "ccc", password: str = "1") -> dict:
    """VM 온보딩: SubAgent 설치 + 역할별 소프트웨어 설치"""
    results = {"ip": ip, "role": role, "steps": []}

    # 1. SubAgent 설치
    install_script = SUBAGENT_INSTALL_SCRIPT.replace("{role}", role)
    r = ssh_run(ip, user, password, [f"bash -c '{install_script}'"])
    results["steps"].append({"step": "subagent_install", **r})

    # 2. 역할별 소프트웨어 설치
    role_cmds = ROLE_SETUP_SCRIPTS.get(role, [])
    if role_cmds:
        r = ssh_run(ip, user, password, role_cmds)
        results["steps"].append({"step": "role_setup", **r})

    # 3. 헬스체크 확인
    health = health_check(ip)
    results["healthy"] = health.get("status") == "healthy"
    results["steps"].append({"step": "health_check", "success": results["healthy"], "detail": health})

    return results


# ── SubAgent Communication (A2A) ─────────────────

def health_check(ip: str) -> dict:
    """SubAgent 헬스체크"""
    try:
        r = httpx.get(f"http://{ip}:{SUBAGENT_PORT}/health", timeout=5.0)
        return r.json()
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


def run_command(ip: str, script: str, timeout: int = 60) -> dict:
    """SubAgent에 명령 실행 (A2A)"""
    try:
        r = httpx.post(
            f"http://{ip}:{SUBAGENT_PORT}/a2a/run_script",
            json={"script": script, "timeout": timeout},
            timeout=float(timeout + 5),
        )
        return r.json()
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}


def system_status(infras: list[dict]) -> dict:
    """전체 인프라 상태 요약"""
    status = {"total": len(infras), "healthy": 0, "unreachable": 0, "details": []}
    for infra in infras:
        ip = infra.get("ip", "")
        h = health_check(ip)
        is_healthy = h.get("status") == "healthy"
        if is_healthy:
            status["healthy"] += 1
        else:
            status["unreachable"] += 1
        status["details"].append({"ip": ip, "role": infra.get("role", ""), **h})
    return status


# ── LLM 기반 스킬 디스패치 (bastion의 skill system 참고) ──

SKILLS = {
    "onboard": {
        "description": "VM에 SubAgent 설치 및 역할별 소프트웨어 배포",
        "requires": ["ip", "role", "ssh_user", "ssh_password"],
    },
    "health_check": {
        "description": "SubAgent 상태 확인",
        "requires": ["ip"],
    },
    "run_command": {
        "description": "SubAgent에 명령 실행",
        "requires": ["ip", "script"],
    },
    "system_status": {
        "description": "전체 인프라 상태 요약",
        "requires": ["infras"],
    },
    "diagnose": {
        "description": "VM 문제 진단 — LLM이 상태를 분석하고 해결 방안 제시",
        "requires": ["ip", "symptoms"],
    },
}


def dispatch_skill(skill_name: str, params: dict) -> dict:
    """스킬 디스패치 — bastion의 tool dispatch 패턴 참고"""
    if skill_name == "onboard":
        return onboard_vm(
            ip=params["ip"], role=params["role"],
            user=params.get("ssh_user", "ccc"),
            password=params.get("ssh_password", "1"),
        )
    elif skill_name == "health_check":
        return health_check(params["ip"])
    elif skill_name == "run_command":
        return run_command(params["ip"], params["script"], params.get("timeout", 60))
    elif skill_name == "system_status":
        return system_status(params["infras"])
    elif skill_name == "diagnose":
        return diagnose_vm(params["ip"], params.get("symptoms", ""))
    else:
        return {"error": f"Unknown skill: {skill_name}"}


def diagnose_vm(ip: str, symptoms: str) -> dict:
    """VM 문제 진단 — 상태 수집 후 LLM 분석"""
    # 1. 상태 수집
    health = health_check(ip)
    collected = {"health": health, "symptoms": symptoms}

    if health.get("status") == "healthy":
        # SubAgent가 살아있으면 추가 정보 수집
        collected["uptime"] = run_command(ip, "uptime")
        collected["disk"] = run_command(ip, "df -h /")
        collected["memory"] = run_command(ip, "free -h")
        collected["services"] = run_command(ip, "systemctl list-units --failed --no-pager")

    # 2. LLM 분석
    prompt = build_system_prompt(f"진단 대상 VM: {ip}\n수집된 상태:\n{json.dumps(collected, ensure_ascii=False, indent=2)}")
    try:
        r = httpx.post(f"{LLM_BASE_URL}/api/chat", json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"이 VM의 문제를 진단하고 해결 방안을 제시하세요.\n증상: {symptoms}"},
            ],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 800},
        }, timeout=60.0)
        diagnosis = r.json().get("message", {}).get("content", "진단 실패")
    except Exception as e:
        diagnosis = f"LLM 연결 실패: {e}"

    return {"ip": ip, "collected": collected, "diagnosis": diagnosis}


# ── Agent Task 실행 (LLM + 스킬 연동) ────────────

def execute_task(instruction: str, context: dict = None) -> dict:
    """자연어 지시 → LLM이 스킬 선택 → 실행 → 결과 반환

    bastion의 query loop 패턴을 단순화:
    1. 사용자 지시 + 컨텍스트를 LLM에 전달
    2. LLM이 실행할 스킬과 파라미터를 JSON으로 응답
    3. 스킬 실행 후 결과를 반환
    """
    context = context or {}
    skill_list = json.dumps(SKILLS, ensure_ascii=False, indent=2)

    prompt = build_system_prompt(f"사용 가능한 스킬:\n{skill_list}\n\n컨텍스트: {json.dumps(context, ensure_ascii=False)}")

    try:
        r = httpx.post(f"{LLM_BASE_URL}/api/chat", json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""지시: {instruction}

반드시 아래 JSON 형식으로만 응답:
{{"skill": "스킬명", "params": {{...}}, "reason": "선택 이유"}}

스킬이 필요없으면:
{{"skill": "none", "params": {{}}, "reason": "직접 답변", "answer": "답변 내용"}}"""},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }, timeout=30.0)
        reply = r.json().get("message", {}).get("content", "{}")
    except Exception as e:
        return {"error": f"LLM 연결 실패: {e}", "instruction": instruction}

    # JSON 파싱
    try:
        # LLM 응답에서 JSON 추출
        import re
        match = re.search(r'\{[\s\S]*\}', reply)
        if match:
            plan = json.loads(match.group())
        else:
            return {"error": "LLM 응답 파싱 실패", "raw": reply}
    except json.JSONDecodeError:
        return {"error": "JSON 파싱 실패", "raw": reply}

    skill_name = plan.get("skill", "none")
    if skill_name == "none":
        return {"answer": plan.get("answer", reply), "reason": plan.get("reason", "")}

    # 스킬 실행
    result = dispatch_skill(skill_name, plan.get("params", {}))
    return {"skill": skill_name, "reason": plan.get("reason", ""), "result": result}
