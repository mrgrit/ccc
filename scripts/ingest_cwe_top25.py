"""CWE Top 25 (2024) → KG anchor (kind=cwe_top25)

외부 지식 5번째 채널 (P15). 수기.

Source: https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse

CWE_TOP25_2024 = [
    ("CWE-79", "Cross-site Scripting", "Improper Neutralization of Input During Web Page Generation"),
    ("CWE-787", "Out-of-bounds Write", "Memory write outside intended buffer"),
    ("CWE-89", "SQL Injection", "Improper Neutralization of Special Elements used in SQL Command"),
    ("CWE-352", "Cross-Site Request Forgery", "CSRF — 사용자 동의 없이 인증된 요청 발송"),
    ("CWE-22", "Path Traversal", "Improper Limitation of a Pathname to a Restricted Directory"),
    ("CWE-125", "Out-of-bounds Read", "Memory read outside intended buffer"),
    ("CWE-78", "OS Command Injection", "Improper Neutralization of Special Elements used in OS Command"),
    ("CWE-416", "Use After Free", "Memory referenced after release"),
    ("CWE-862", "Missing Authorization", "권한 검증 누락"),
    ("CWE-434", "Unrestricted Upload", "Unrestricted Upload of File with Dangerous Type"),
    ("CWE-94", "Code Injection", "Improper Control of Generation of Code"),
    ("CWE-20", "Improper Input Validation", "입력 검증 부재"),
    ("CWE-77", "Command Injection", "Improper Neutralization of Special Elements used in a Command"),
    ("CWE-287", "Improper Authentication", "인증 약점"),
    ("CWE-269", "Improper Privilege Management", "권한 관리 결함"),
    ("CWE-502", "Deserialization of Untrusted Data", "신뢰 안 되는 직렬화 데이터 처리"),
    ("CWE-200", "Information Exposure", "정보 노출"),
    ("CWE-863", "Incorrect Authorization", "잘못된 권한 부여"),
    ("CWE-918", "Server-Side Request Forgery (SSRF)", "SSRF — 서버가 사용자 제공 URL 페치"),
    ("CWE-119", "Improper Restriction of Operations within a Buffer", "버퍼 경계 검증 부재"),
    ("CWE-476", "NULL Pointer Dereference", "NULL 포인터 역참조"),
    ("CWE-798", "Use of Hard-coded Credentials", "하드코딩 자격증명"),
    ("CWE-190", "Integer Overflow", "정수 오버플로우"),
    ("CWE-400", "Uncontrolled Resource Consumption", "리소스 무제한 소비 (DoS)"),
    ("CWE-306", "Missing Authentication for Critical Function", "중요 기능 인증 누락"),
]


def import_to_bastion(bastion_url: str) -> dict:
    added, errors = 0, 0
    for code, name, desc in CWE_TOP25_2024:
        payload = {
            "kind": "cwe_top25",
            "label": code,
            "body": f"name: {name}\ndescription: {desc}\nyear: 2024",
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

    print(f"=== CWE Top 25 (2024) — {len(CWE_TOP25_2024)} 항목 ===")
    if args.via_bastion:
        r = import_to_bastion(args.bastion_url)
        print(f"  added={r['added']}, errors={r['errors']}")


if __name__ == "__main__":
    main()
