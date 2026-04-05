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
LLM_MANAGER_MODEL = os.getenv("LLM_MANAGER_MODEL", "gpt-oss:120b")
LLM_SUBAGENT_MODEL = os.getenv("LLM_SUBAGENT_MODEL", "gemma3:4b")
# bastion TUI는 manager 모델 사용
LLM_MODEL = LLM_MANAGER_MODEL
SUBAGENT_PORT = 8002
SSH_TIMEOUT = 120  # 온보딩 시 패키지 설치에 시간 필요

# ── System Prompt Sections (bastion/src/constants 참고) ──

CCC_DIR = os.getenv("CCC_DIR", os.path.join(os.path.dirname(__file__), "..", ".."))

PROMPT_SECTIONS = {
    "identity": """너는 CCC(Cyber Combat Commander)의 Bastion 운영 에이전트다.
CCC 교육 플랫폼의 **모든 운영 업무**를 담당한다.
서버 관리, 서비스 시작/중지, 인프라 관리, 모니터링, 문제 해결 등 관리자가 요청하는 모든 작업을 수행한다.""",

    "architecture": """CCC 아키텍처:
- ccc-api (:9100): FastAPI 메인 서버. ./dev.sh api 로 실행. UI도 /app/ 경로로 서빙.
- ccc-ui: React 웹 UI. npm run build로 빌드 → ccc-api가 정적 파일 서빙.
- bastion: 이 에이전트. ./dev.sh bastion 으로 실행.
- PostgreSQL (:5434): docker compose -f docker/docker-compose.yaml up -d postgres
- Ollama (LLM): 외부 또는 로컬 서버. 환경변수 LLM_BASE_URL로 설정.

핵심 파일:
- ./dev.sh: API/bastion 실행 스크립트
- .env: 환경 설정 (DATABASE_URL, LLM_BASE_URL, LLM_MODEL)
- docker/docker-compose.yaml: PostgreSQL + API 컨테이너
- apps/ccc_api/src/main.py: API 소스
- apps/ccc-ui/: React UI 소스""",

    "capabilities": """사용 가능한 스킬:
- shell: 이 서버에서 로컬 명령 실행 (서비스 시작/중지, 파일 확인, 로그 조회 등)
- service: CCC 서비스 관리 (api 시작/중지/재시작, db 시작/중지, 상태 확인)
- onboard: 학생 VM에 SSH 접속 → SubAgent 설치 + 역할별 소프트웨어 배포
- health_check: SubAgent 상태 확인 (A2A /health)
- run_command: SubAgent에 원격 명령 실행 (A2A /a2a/run_script)
- system_status: 전체 인프라 상태 요약
- diagnose: VM 문제 진단 (상태 수집 + LLM 분석)
- build_ui: UI 빌드 (npm run build)""",

    "constraints": """제약사항:
- 파괴적 작업(rm -rf /, 디스크 포맷) 금지
- 학생 데이터 임의 삭제 금지
- DB DROP TABLE 금지""",

    "roles": """학생 VM 역할:
- attacker (Kali): nmap, metasploit, hydra, sqlmap, nikto, gobuster
- secu (Security GW): nftables, suricata, sysmon, osquery, auditd (NIC 2개)
- web (Web Server): apache2, modsecurity, docker(juiceshop/dvwa)
- siem (SIEM): wazuh-manager, sigma, opencti, elasticsearch (RAM 8G+)
- windows (분석): sysmon, osquery, ghidra (OpenSSH 필요)
- manager (Manager AI): ollama, ccc-bastion subagent""",
}


def _load_ccc_md() -> str:
    """CCC.md 로드 — bastion의 장기 기억/운영 지침"""
    ccc_md = os.path.join(CCC_DIR, "CCC.md")
    if os.path.exists(ccc_md):
        try:
            with open(ccc_md, encoding="utf-8") as f:
                return f.read()[:3000]
        except Exception:
            pass
    return ""

def build_system_prompt(extra_context: str = "") -> str:
    """시스템 프롬프트 동적 조합 (bastion의 resolveSystemPromptSections 참고)"""
    sections = [PROMPT_SECTIONS[k] for k in PROMPT_SECTIONS]
    # CCC.md 장기 기억 주입
    ccc_md = _load_ccc_md()
    if ccc_md:
        sections.append(f"[CCC 운영 지침]\n{ccc_md}")
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
        f"ollama pull {LLM_MANAGER_MODEL}",
        f"ollama pull {LLM_SUBAGENT_MODEL}",
        # bastion 설치 (CCC 레포 clone + venv)
        "apt-get update -y && apt-get install -y python3 python3-pip python3-venv git",
        "if [ ! -d /opt/ccc ]; then git clone https://github.com/mrgrit/ccc.git /opt/ccc; fi",
        "cd /opt/ccc && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -q",
        # bastion용 .env 생성
        f"cat > /opt/ccc/.env << 'ENVEOF'\n"
        f"LLM_BASE_URL=http://localhost:11434\n"
        f"LLM_MANAGER_MODEL={LLM_MANAGER_MODEL}\n"
        f"LLM_SUBAGENT_MODEL={LLM_SUBAGENT_MODEL}\n"
        f"ENVEOF",
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


def ssh_run(ip: str, user: str, password: str, commands: list[str], timeout: int = None) -> dict:
    """SSH로 명령 실행 — scp로 스크립트 업로드 후 실행 (이스케이핑/stdin 문제 원천 해결)"""
    import tempfile
    script = "#!/bin/bash\nset -e\n" + "\n".join(commands) + "\n"
    t = timeout or SSH_TIMEOUT
    ssh_opts = ["-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]

    try:
        # 1. 로컬에 임시 스크립트 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            local_path = f.name

        remote_path = f"/tmp/ccc_onboard_{os.getpid()}.sh"

        # 2. scp로 스크립트 업로드
        scp_cmd = ["sshpass", "-p", password, "scp", *ssh_opts, local_path, f"{user}@{ip}:{remote_path}"]
        scp_r = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30, errors="replace")
        os.unlink(local_path)

        if scp_r.returncode != 0:
            return {"success": False, "stdout": "", "stderr": f"scp failed: {scp_r.stderr[:500]}"}

        # 3. ssh로 스크립트 실행 (sudo -S로 비밀번호 전달)
        run_cmd = [
            "sshpass", "-p", password,
            "ssh", *ssh_opts, f"{user}@{ip}",
            f"echo '{password}' | sudo -S bash {remote_path}; rm -f {remote_path}",
        ]
        r = subprocess.run(run_cmd, capture_output=True, text=True, timeout=t, errors="replace")
        stderr = "\n".join(l for l in r.stderr.splitlines()
                           if "password" not in l.lower() and "setlocale" not in l.lower())
        return {"success": r.returncode == 0, "stdout": r.stdout[:5000], "stderr": stderr[:2000]}

    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"SSH timeout ({t}s)"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}


# 내부 IP 고정 (API의 INTERNAL_IPS와 동일)
INTERNAL_IPS = {
    "attacker": "10.20.30.201",
    "secu":     "10.20.30.1",
    "web":      "10.20.30.80",
    "siem":     "10.20.30.100",
    "manager":  "10.20.30.200",
    "windows":  "10.20.30.50",
}
INTERNAL_SUBNET = "10.20.30.0/24"
SECU_GW = INTERNAL_IPS["secu"]  # Security Gateway = 기본 게이트웨이


def onboard_vm(ip: str, role: str, user: str = "ccc", password: str = "1") -> dict:
    """VM 온보딩 (외부 IP로 SSH 접속)
    1. SubAgent 설치
    2. 역할별 소프트웨어 설치
    3. 내부 NIC에 고정 IP 설정
    4. Security GW 제외 — NAT disable + 기본 게이트웨이를 Security GW로 변경
    5. 헬스체크
    """
    internal_ip = INTERNAL_IPS.get(role, "10.20.30.250")
    results = {"ip": ip, "internal_ip": internal_ip, "role": role, "steps": []}

    # 1. SubAgent 설치 (외부 IP로 SSH — 인터넷 필요)
    install_script = SUBAGENT_INSTALL_SCRIPT.replace("{role}", role)
    r = ssh_run(ip, user, password, [install_script], timeout=120)
    results["steps"].append({"step": "subagent_install", **r})

    # 2. 역할별 소프트웨어 설치 (인터넷 필요)
    role_cmds = ROLE_SETUP_SCRIPTS.get(role, [])
    if role_cmds:
        r = ssh_run(ip, user, password, role_cmds)
        results["steps"].append({"step": "role_setup", **r})

    # 3. 내부 NIC IP 설정 — 단일 스크립트로 전달
    internal_script = f"""
IFACE=$(ip -o link show | grep -v 'lo\\|docker\\|veth' | awk '{{print $2}}' | tr -d ':' | tail -1)
if [ -n "$IFACE" ]; then
    ip addr add {internal_ip}/24 dev $IFACE 2>/dev/null || true
    ip link set $IFACE up
    echo "Internal NIC: $IFACE = {internal_ip}"
else
    echo "WARN: second NIC not found"
fi
"""
    r = ssh_run(ip, user, password, [internal_script])
    results["steps"].append({"step": "internal_ip_setup", "ip": internal_ip, **r})

    # 4. NAT disable + Security GW 경유
    if role != "secu":
        nat_script = f"""
ip route del default 2>/dev/null || true
ip route add default via {SECU_GW} 2>/dev/null || true
echo "Default gateway set to {SECU_GW}"
"""
        r = ssh_run(ip, user, password, [nat_script])
        results["steps"].append({"step": "nat_disable_gw_route", "gateway": SECU_GW, **r})
    else:
        secu_script = """
sysctl -w net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
EXTERNAL=$(ip -o link show | grep -v 'lo\\|docker\\|veth' | awk '{print $2}' | tr -d ':' | head -1)
nft add table nat 2>/dev/null || true
nft 'add chain nat postrouting { type nat hook postrouting priority 100; }' 2>/dev/null || true
nft add rule nat postrouting oifname "$EXTERNAL" masquerade 2>/dev/null || true
echo "NAT masquerade on $EXTERNAL"
"""
        r = ssh_run(ip, user, password, [secu_script])
        results["steps"].append({"step": "secu_nat_forward", **r})

    # 5. 헬스체크 — SubAgent 시작 대기 후 확인 (외부 IP 우선)
    import time as _t
    health = {"status": "unreachable"}
    for attempt in range(5):
        _t.sleep(2)
        health = health_check(ip)  # 외부 IP로 확인
        if health.get("status") == "healthy":
            break
    if health.get("status") != "healthy":
        health = health_check(internal_ip)  # 외부 안되면 내부 시도
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
    "ccc": {
        "description": "CCC 플랫폼 관리 — action: start, stop, restart, status, logs, build_ui, start_api, stop_api, restart_api, start_db, stop_db, reset_db, backup_db, env, set_env, update, deploy, create_admin, student_list, firewall_open, firewall_close, check_port",
        "requires": ["action"],
    },
    "shell": {
        "description": "이 서버에서 로컬 쉘 명령 실행 (파일 조회, 패키지 설치, 프로세스 관리 등 ccc 스킬에 없는 모든 작업)",
        "requires": ["command"],
    },
    "onboard": {
        "description": "학생 VM에 SubAgent 설치 및 역할별 소프트웨어 배포",
        "requires": ["ip", "role", "ssh_user", "ssh_password"],
    },
    "health_check": {
        "description": "SubAgent 상태 확인",
        "requires": ["ip"],
    },
    "run_command": {
        "description": "원격 VM의 SubAgent에 명령 실행 (A2A 프로토콜)",
        "requires": ["ip", "script"],
    },
    "system_status": {
        "description": "전체 학생 인프라 상태 요약",
        "requires": ["infras"],
    },
    "diagnose": {
        "description": "VM 문제 진단 — 상태 수집 + LLM 분석 + 해결 방안",
        "requires": ["ip", "symptoms"],
    },
}


# ── Local Shell ───────────────────────────────────

def shell_exec(command: str, timeout: int = 60) -> dict:
    """로컬 쉘 명령 실행"""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=CCC_DIR,
        )
        return {"exit_code": r.returncode, "stdout": r.stdout[:10000], "stderr": r.stderr[:5000]}
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}


# ── CCC Platform Management ───────────────────────

_VENV = f"source {CCC_DIR}/.venv/bin/activate 2>/dev/null"
_ENVLOAD = f"set -a; [ -f {CCC_DIR}/.env ] && source {CCC_DIR}/.env; set +a; export PYTHONPATH={CCC_DIR}"
_API_START = f"{_VENV}; {_ENVLOAD}; nohup python3 -m uvicorn apps.ccc_api.src.main:app --host 0.0.0.0 --port 9100 > /tmp/ccc-api.log 2>&1 & echo \"API started (pid: $!)\""
_API_KEY = os.getenv("CCC_API_KEY", "ccc-api-key-2026")


def ccc_manage(action: str, params: dict = None) -> dict:
    """CCC 플랫폼 통합 관리"""
    params = params or {}
    actions = {
        # ── 서비스 시작/중지 ──
        "start": f"cd {CCC_DIR} && docker compose -f docker/docker-compose.yaml up -d postgres && sleep 2 && {_API_START}",
        "stop": f"pkill -f 'uvicorn apps.ccc_api' 2>/dev/null; cd {CCC_DIR} && docker compose -f docker/docker-compose.yaml stop; echo 'All stopped'",
        "restart": f"pkill -f 'uvicorn apps.ccc_api' 2>/dev/null; sleep 1; cd {CCC_DIR} && {_API_START}",
        "start_api": f"cd {CCC_DIR} && {_API_START}",
        "stop_api": "pkill -f 'uvicorn apps.ccc_api' && echo 'API stopped' || echo 'API not running'",
        "restart_api": f"pkill -f 'uvicorn apps.ccc_api' 2>/dev/null; sleep 1; cd {CCC_DIR} && {_API_START}",
        "start_db": f"cd {CCC_DIR} && docker compose -f docker/docker-compose.yaml up -d postgres && echo 'DB started'",
        "stop_db": f"cd {CCC_DIR} && docker compose -f docker/docker-compose.yaml stop postgres && echo 'DB stopped'",

        # ── 상태/로그 ──
        "status":
            "echo '=== CCC Platform Status ==='; echo; "
            "echo '-- Processes --'; "
            "(pgrep -fa 'uvicorn apps.ccc_api' && echo '  API: RUNNING') || echo '  API: STOPPED'; "
            "(docker ps --format '  DB:  RUNNING ({{.Names}} {{.Status}})' 2>/dev/null | grep postgres) || echo '  DB:  STOPPED'; "
            "echo; echo '-- Health --'; "
            f"curl -s -o /dev/null -w '  API response: %{{http_code}}' http://localhost:9100/api/dashboard -H 'X-API-Key: {_API_KEY}' 2>/dev/null; echo; "
            f"curl -s -o /dev/null -w '  LLM response: %{{http_code}}' {LLM_BASE_URL}/api/tags 2>/dev/null; echo; "
            "echo; echo '-- Resources --'; "
            "df -h / | tail -1 | awk '{print \"  Disk: \" $3 \"/\" $2 \" (\" $5 \" used)\"}'; "
            "free -h | awk '/Mem/{print \"  RAM:  \" $3 \"/\" $2}'; "
            f"echo; echo '-- Config --'; "
            f"echo '  CCC_DIR: {CCC_DIR}'; "
            f"echo '  LLM: {LLM_BASE_URL} / {LLM_MODEL}'; "
            f"echo '  DB: {os.getenv('DATABASE_URL', 'postgresql://ccc:ccc@127.0.0.1:5434/ccc')}'",
        "logs": "tail -100 /tmp/ccc-api.log 2>/dev/null || echo 'No API log file. Start API first.'",
        "logs_follow": "tail -f /tmp/ccc-api.log 2>/dev/null || echo 'No API log file'",
        "logs_error": "grep -i 'error\\|traceback\\|exception' /tmp/ccc-api.log 2>/dev/null | tail -30 || echo 'No errors found'",

        # ── UI 빌드/배포 ──
        "build_ui": f"cd {CCC_DIR}/apps/ccc-ui && npm run build 2>&1 && echo 'UI build complete'",
        "deploy": f"cd {CCC_DIR} && git pull && "
            f"cd apps/ccc-ui && npm install && npm run build && cd ../.. && "
            f"{_VENV} && pip install -r requirements.txt -q && "
            f"pkill -f 'uvicorn apps.ccc_api' 2>/dev/null; sleep 1 && {_API_START} && echo 'Deploy complete'",
        "update": f"cd {CCC_DIR} && git pull && echo 'Code updated. Run: ccc restart'",

        # ── DB 관리 ──
        "reset_db": f"cd {CCC_DIR} && docker compose -f docker/docker-compose.yaml stop postgres && "
            "docker compose -f docker/docker-compose.yaml rm -f postgres && "
            "docker volume rm docker_ccc-pgdata 2>/dev/null; "
            "docker compose -f docker/docker-compose.yaml up -d postgres && echo 'DB reset complete. Restart API to recreate tables.'",
        "backup_db": f"mkdir -p {CCC_DIR}/db_backup && docker exec $(docker ps -qf name=postgres) pg_dump -U ccc ccc > {CCC_DIR}/db_backup/backup_$(date +%Y%m%d_%H%M%S).sql && echo 'Backup saved'",
        "db_shell": f"docker exec -it $(docker ps -qf name=postgres) psql -U ccc ccc",

        # ── 환경 설정 ──
        "env": f"cat {CCC_DIR}/.env 2>/dev/null || echo 'No .env file'",
        "set_env": _set_env_cmd(params),

        # ── 사용자 관리 ──
        "create_admin": f"cd {CCC_DIR} && {_VENV}; {_ENVLOAD}; python3 -c \""
            f"import httpx; r=httpx.post('http://localhost:9100/api/auth/create-admin', json={{"
            f"'student_id':'{params.get('id', 'admin')}','name':'{params.get('name', 'Admin')}','password':'{params.get('password', 'admin')}'}},"
            f"headers={{'X-API-Key':'{_API_KEY}'}}); print(r.json())\"",
        "student_list": f"curl -s http://localhost:9100/api/students -H 'X-API-Key: {_API_KEY}' 2>/dev/null | python3 -m json.tool || echo 'API unreachable'",

        # ── 네트워크/방화벽 ──
        "firewall_open": f"sudo ufw allow {params.get('port', '9100')}/tcp && echo 'Port {params.get('port', '9100')} opened'",
        "firewall_close": f"sudo ufw deny {params.get('port', '9100')}/tcp && echo 'Port {params.get('port', '9100')} closed'",
        "check_port": f"ss -tlnp | grep ':{params.get('port', '9100')}' || echo 'Port {params.get('port', '9100')} not listening'",
        "firewall_status": "sudo ufw status verbose 2>/dev/null || echo 'ufw not available'",
    }
    cmd = actions.get(action)
    if not cmd:
        available = ", ".join(sorted(actions.keys()))
        return {"exit_code": 1, "stdout": "", "stderr": f"Unknown action: {action}\nAvailable: {available}"}
    return shell_exec(cmd, timeout=60)


def _set_env_cmd(params: dict) -> str:
    """환경 변수 설정 명령 생성"""
    key = params.get("key", "")
    value = params.get("value", "")
    if not key:
        return "echo 'key 파라미터 필요'"
    return (
        f"grep -q '^{key}=' {CCC_DIR}/.env 2>/dev/null && "
        f"sed -i 's|^{key}=.*|{key}={value}|' {CCC_DIR}/.env || "
        f"echo '{key}={value}' >> {CCC_DIR}/.env; "
        f"echo '{key}={value} saved. Restart API to apply.'"
    )


# 하위호환
def service_manage(action: str) -> dict:
    return ccc_manage(action)


def dispatch_skill(skill_name: str, params: dict) -> dict:
    """스킬 디스패치 — bastion의 tool dispatch 패턴 참고"""
    if skill_name == "shell":
        return shell_exec(params.get("command", "echo 'no command'"), params.get("timeout", 60))
    elif skill_name in ("ccc", "service"):
        return ccc_manage(params.get("action", "status"), params)
    elif skill_name == "onboard":
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
