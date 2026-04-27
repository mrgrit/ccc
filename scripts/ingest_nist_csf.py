"""NIST CSF 2.0 (6 function + 23 category) → KG anchor (kind=nist_csf)

외부 지식 네 번째 채널 (P15). 수기 정리.

NIST Cybersecurity Framework 2.0 (2024):
  Govern (GV) / Identify (ID) / Protect (PR) / Detect (DE) / Respond (RS) / Recover (RC)
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse

CSF_DATA = {
    "Govern (GV)": [
        ("GV.OC", "Organizational Context", "조직 mission/stakeholder/legal 환경 이해"),
        ("GV.RM", "Risk Management Strategy", "위험 식별·평가·완화 전략 수립"),
        ("GV.RR", "Roles, Responsibilities, and Authorities", "역할·책임 명확화"),
        ("GV.PO", "Policy", "정보보안 정책 문서화·승인·갱신"),
        ("GV.OV", "Oversight", "거버넌스 감독 + 메트릭 평가"),
        ("GV.SC", "Cybersecurity Supply Chain Risk Management", "공급망 위험 관리 (SBOM/벤더 평가)"),
    ],
    "Identify (ID)": [
        ("ID.AM", "Asset Management", "하드웨어·소프트웨어·데이터·인력 자산 인벤토리"),
        ("ID.RA", "Risk Assessment", "위협·취약점·비즈니스 영향 평가"),
        ("ID.IM", "Improvement", "지속적 개선 절차"),
    ],
    "Protect (PR)": [
        ("PR.AA", "Identity Management, Authentication, and Access Control",
         "ID/MFA/RBAC/least privilege/network segmentation"),
        ("PR.AT", "Awareness and Training", "직원 보안 교육 + 시뮬레이션"),
        ("PR.DS", "Data Security", "암호화 (at-rest/in-transit) + DLP + classification"),
        ("PR.PS", "Platform Security", "OS/펌웨어/network device 하드닝"),
        ("PR.IR", "Technology Infrastructure Resilience", "BCP/DR + capacity"),
    ],
    "Detect (DE)": [
        ("DE.CM", "Continuous Monitoring", "SIEM/IDS/IPS/EDR 실시간 감시"),
        ("DE.AE", "Adverse Event Analysis", "알림 분석 + 인시던트 분류 + ATT&CK 매핑"),
    ],
    "Respond (RS)": [
        ("RS.MA", "Incident Management", "IR plan + 훈련"),
        ("RS.AN", "Incident Analysis", "근본 원인 분석 + 영향 평가"),
        ("RS.CO", "Incident Response Reporting and Communication", "이해관계자 보고"),
        ("RS.MI", "Incident Mitigation", "containment/eradication"),
    ],
    "Recover (RC)": [
        ("RC.RP", "Incident Recovery Plan Execution", "복구 계획 수행"),
        ("RC.CO", "Incident Recovery Communications", "복구 소통"),
    ],
}


def import_to_bastion(bastion_url: str) -> dict:
    added, errors = 0, 0
    for func, cats in CSF_DATA.items():
        # function 자체도 anchor
        try:
            req = urllib.request.Request(
                f"{bastion_url}/history/anchors",
                data=json.dumps({
                    "kind": "nist_csf",
                    "label": func.split('(')[1].rstrip(')'),  # GV/ID/PR/DE/RS/RC
                    "body": f"function: {func}\nlevel: function (top)",
                    "related_ids": [], "valid_from": "", "valid_until": "",
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10).read()
            added += 1
        except Exception:
            errors += 1
        for code, name, desc in cats:
            payload = {
                "kind": "nist_csf",
                "label": code,
                "body": f"function: {func}\nname: {name}\ndescription: {desc}",
                "related_ids": [f"function:{func.split('(')[1].rstrip(')')}"],
                "valid_from": "", "valid_until": "",
            }
            try:
                req = urllib.request.Request(
                    f"{bastion_url}/history/anchors",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=10).read()
                added += 1
            except Exception:
                errors += 1
    return {"added": added, "errors": errors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--via-bastion", action="store_true")
    ap.add_argument("--bastion-url", default=os.getenv("BASTION_URL", "http://192.168.0.115:8003"))
    args = ap.parse_args()

    print("=== NIST CSF 2.0 ===")
    total = sum(1 + len(c) for c in CSF_DATA.values())  # function + categories
    print(f"6 function + 23 category = {total} anchor")

    if args.via_bastion:
        print(f"\n[mode] {args.bastion_url}")
        r = import_to_bastion(args.bastion_url)
        print(f"  added={r['added']}, errors={r['errors']}")


if __name__ == "__main__":
    main()
