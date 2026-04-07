#!/usr/bin/env python3
"""Bastion 실전 시나리오 테스트 — bastion VM에서 에이전트 대화 실행"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.bastion import run_command

VM_IP = "192.168.136.140"
LLM_URL = os.getenv("LLM_BASE_URL", "http://211.170.162.139:10534")

def bastion_chat(msg: str) -> str:
    """bastion VM에서 agent.chat() 실행하고 결과 반환"""
    # 테스트 스크립트를 파일로 생성
    test_code = f'''
import os, sys
sys.path.insert(0, "/opt/bastion")
os.environ["LLM_BASE_URL"] = "{LLM_URL}"
os.environ["LLM_MANAGER_MODEL"] = "gpt-oss:120b"
from bastion.agent import BastionAgent
agent = BastionAgent(
    vm_ips={{"attacker":"10.20.30.201","secu":"10.20.30.1","web":"10.20.30.80","siem":"10.20.30.100","manager":"10.20.30.200"}},
    knowledge_dir="/opt/bastion/knowledge"
)
for evt in agent.chat("{msg}"):
    e = evt.get("event","")
    if e == "skill_start":
        skill = evt.get("skill","")
        print(f"  >> [skill] {{skill}} ...")
    elif e == "skill_result":
        ok = "ok" if evt.get("success") else "fail"
        out = str(evt.get("output",""))[:250]
        print(f"  [{{ok}}] {{out}}")
    elif e == "message":
        print(evt.get("content","")[:400])
    elif e == "error":
        print(f"  ERROR: {{evt.get('content','')}}")
'''
    r = run_command(VM_IP,
        f"cat > /tmp/bastion_test_run.py << 'PYEOF'\n{test_code}\nPYEOF\n"
        f"/opt/bastion/.venv/bin/python3 /tmp/bastion_test_run.py",
        timeout=90)
    out = r.get("stdout", "")
    err = r.get("stderr", "")
    if err and not out:
        return f"ERROR: {err[:200]}"
    return out


scenarios = [
    ("인프라 점검", "전체 인프라 상태 확인해줘"),
    ("Suricata 확인", "suricata에서 최근 알림 확인해줘"),
    ("Wazuh 확인", "wazuh 상태 확인하고 등록된 에이전트 목록 보여줘"),
    ("교육 질문", "nftables에서 특정 IP를 차단하는 룰은 어떻게 작성해?"),
    ("웹 스캔", "web 서버를 nmap으로 포트 스캔해줘"),
]

print("=" * 60)
print("  Bastion 실전 시나리오 테스트")
print("=" * 60)

passed = 0
for name, msg in scenarios:
    print(f"\n--- {name} ---")
    print(f"[학생] {msg}")
    result = bastion_chat(msg)
    print(result[:500])

    # 결과 검증
    has_output = len(result.strip()) > 10 and "ERROR" not in result
    status = "PASS" if has_output else "FAIL"
    if has_output:
        passed += 1
    print(f"[{status}]")

print(f"\n{'='*60}")
print(f"  Result: {passed}/{len(scenarios)} scenarios passed")
print(f"{'='*60}")
