"""CIS Critical Security Controls v8.1 (18) → KG anchor (kind=cis_controls)

외부 지식 7번째 채널 (P15). 수기.

Source: https://www.cisecurity.org/controls/v8
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse

CIS_CONTROLS_V8 = [
    ("CIS-1", "Inventory and Control of Enterprise Assets",
     "엔터프라이즈 자산 (laptop/server/IoT/network device) 인벤토리 + 비인가 자산 차단"),
    ("CIS-2", "Inventory and Control of Software Assets",
     "소프트웨어 인벤토리 (OS/앱/라이브러리) + 비인가 소프트웨어 실행 차단 (allowlist)"),
    ("CIS-3", "Data Protection",
     "데이터 분류 / 보관 / 처분 / 암호화. 데이터 lifecycle 통제."),
    ("CIS-4", "Secure Configuration of Enterprise Assets and Software",
     "엔터프라이즈 자산·소프트웨어 보안 설정 baseline + 자동화 + drift 탐지"),
    ("CIS-5", "Account Management",
     "사용자·관리자·서비스 계정 관리 + 비활성 정리 + MFA"),
    ("CIS-6", "Access Control Management",
     "RBAC + least privilege + just-in-time access"),
    ("CIS-7", "Continuous Vulnerability Management",
     "지속 취약점 평가 + 패치 + KEV 우선 + zero-day 대응"),
    ("CIS-8", "Audit Log Management",
     "감사 로그 수집·저장·분석. SIEM 통합. 보존 기간 정책."),
    ("CIS-9", "Email and Web Browser Protections",
     "이메일·웹 브라우저 보호 (SEG / DNS filter / link rewrite)"),
    ("CIS-10", "Malware Defenses",
     "AV / EDR / 행위 기반 탐지 + 자동 차단 + 격리"),
    ("CIS-11", "Data Recovery",
     "백업 + 복구 절차 + offsite + 정기 테스트"),
    ("CIS-12", "Network Infrastructure Management",
     "네트워크 device (router/switch/firewall) 관리 + 분리 + 모니터링"),
    ("CIS-13", "Network Monitoring and Defense",
     "IDS / IPS / NetFlow / DNS query log + 비정상 탐지"),
    ("CIS-14", "Security Awareness and Skills Training",
     "직원 보안 교육 + 시뮬레이션 (피싱/USB drop) + 측정"),
    ("CIS-15", "Service Provider Management",
     "외부 서비스 (SaaS/cloud) 관리 + 리스크 평가 + 계약 보안 조항"),
    ("CIS-16", "Application Software Security",
     "SDLC + secure coding + SAST/DAST/IAST + 외부 라이브러리 SCA"),
    ("CIS-17", "Incident Response Management",
     "IR plan + IR team + tabletop exercise + post-incident review"),
    ("CIS-18", "Penetration Testing",
     "정기 외부·내부 펜테스트 + Red Team + 발견 사항 추적"),
]


def import_to_bastion(bastion_url: str) -> dict:
    added, errors = 0, 0
    for code, name, desc in CIS_CONTROLS_V8:
        payload = {
            "kind": "cis_controls",
            "label": code,
            "body": f"name: {name}\ndescription: {desc}\nversion: v8.1\ncategory: critical_security_control",
            "related_ids": [f"name:{name}"],
            "valid_from": "2024-01-01", "valid_until": "",
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

    print(f"=== CIS Critical Security Controls v8.1 — {len(CIS_CONTROLS_V8)} 항목 ===")
    if args.via_bastion:
        r = import_to_bastion(args.bastion_url)
        print(f"  added={r['added']}, errors={r['errors']}")


if __name__ == "__main__":
    main()
