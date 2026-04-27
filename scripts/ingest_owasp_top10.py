"""OWASP Top 10 (Web 2021 + API 2023 + LLM 2025) → KG anchor (kind=owasp_top10)

외부 지식 세 번째 채널 (P15).

소스 데이터는 수기 정리 (외부 fetch 없음 — 표준은 안정적):
  Web Top 10 2021: A01~A10
  API Top 10 2023: API1~API10
  LLM Top 10 2025: LLM01~LLM10

CLI:
  python3 scripts/ingest_owasp_top10.py [--via-bastion] [--dry-run]
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse

OWASP_DATA = {
    "Web 2021": [
        ("A01:2021", "Broken Access Control",
         "권한 검증 부재. 파일 직접 IDOR / URL 변조 / privilege escalation. 사용자 가 자기 권한 외 자원 접근."),
        ("A02:2021", "Cryptographic Failures",
         "암호화 부재 또는 약함. 평문 저장 / 약한 알고리즘 (MD5/SHA1) / 잘못된 키 관리. 형이 'Sensitive Data Exposure'."),
        ("A03:2021", "Injection",
         "신뢰되지 않은 데이터가 명령/쿼리에 포함. SQL/NoSQL/Cmd/LDAP/XPath/ORM 인젝션. parameterized query / escape 필수."),
        ("A04:2021", "Insecure Design",
         "보안 설계 결함. threat modeling/secure design pattern 부재. *구현 결함*과 다름 — 설계 단계의 결함."),
        ("A05:2021", "Security Misconfiguration",
         "기본 설정/cloud 권한/heading/feature flag 등 잘못된 구성. CSP/HSTS 미적용, 디버그 노출, 디폴트 패스워드."),
        ("A06:2021", "Vulnerable and Outdated Components",
         "취약 라이브러리/프레임워크 사용. SBOM 부재 / CVE 추적 안 함. KEV 매칭 핵심 영역."),
        ("A07:2021", "Identification and Authentication Failures",
         "약한 패스워드 / 세션 고정 / brute force / credential stuffing. MFA 부재. 형이 'Broken Authentication'."),
        ("A08:2021", "Software and Data Integrity Failures",
         "코드/인프라 무결성 검증 부재. CI/CD 공급망 / unsigned update / insecure deserialization."),
        ("A09:2021", "Security Logging and Monitoring Failures",
         "로깅/감사 부재 → 침해 탐지 불가. SIEM 부재 / 로그 보존 정책 부재 / alert 무시."),
        ("A10:2021", "Server-Side Request Forgery (SSRF)",
         "서버가 사용자 제공 URL 페치. 내부 자원 (metadata 169.254.169.254 등) 노출. cloud 환경에서 critical."),
    ],
    "API 2023": [
        ("API1:2023", "Broken Object Level Authorization",
         "객체 단위 권한 검증 부재 (BOLA / IDOR). API 요청의 object id 변조 → 다른 사용자 자원 접근."),
        ("API2:2023", "Broken Authentication",
         "인증 메커니즘 결함. JWT none alg / weak signature / missing rate limit / credential stuffing."),
        ("API3:2023", "Broken Object Property Level Authorization",
         "객체 속성 단위 권한 결함. mass assignment / excessive data exposure (모든 필드 반환)."),
        ("API4:2023", "Unrestricted Resource Consumption",
         "rate limit / payload size / pagination 부재. DoS 가능 / 비용 증가."),
        ("API5:2023", "Broken Function Level Authorization",
         "function 단위 권한. admin endpoint 가 normal user role 으로 접근 가능."),
        ("API6:2023", "Unrestricted Access to Sensitive Business Flows",
         "비즈니스 로직 abuse. 무료 trial 무한 생성 / 자동 매크로 / scalper bot."),
        ("API7:2023", "Server-Side Request Forgery",
         "API 가 외부 URL fetch. Web SSRF 와 동일 — 내부 자원 노출."),
        ("API8:2023", "Security Misconfiguration",
         "API gateway / CORS / TLS / versioning 잘못된 설정."),
        ("API9:2023", "Improper Inventory Management",
         "shadow API / undocumented endpoint / staging exposed / version sprawl."),
        ("API10:2023", "Unsafe Consumption of APIs",
         "외부 API 응답 신뢰 → injection. third-party API 결과 검증 없이 사용."),
    ],
    "LLM 2025": [
        ("LLM01:2025", "Prompt Injection",
         "사용자 입력이 system prompt 우회 / 역할 변경. direct (jailbreak) + indirect (RAG 문서, 웹 페이지)."),
        ("LLM02:2025", "Sensitive Information Disclosure",
         "system prompt / 학습 데이터 / 사용자 데이터 유출. memorization 공격 / context 누출."),
        ("LLM03:2025", "Supply Chain",
         "모델 / 라이브러리 / 학습 데이터 / RAG 소스 의 공급망 공격. 백도어 모델 / 오염 dataset."),
        ("LLM04:2025", "Data and Model Poisoning",
         "학습 / fine-tuning / RLHF 데이터 의도적 오염. backdoor 트리거 / 편향 주입."),
        ("LLM05:2025", "Improper Output Handling",
         "LLM 출력을 신뢰하고 downstream 시스템에 전달 (XSS, SQLi, code exec). output validation 필수."),
        ("LLM06:2025", "Excessive Agency",
         "LLM 에이전트에 과도한 권한 (function call 무제한). 시스템 명령 / DB write / 외부 API 호출 등."),
        ("LLM07:2025", "System Prompt Leakage",
         "사용자가 system prompt 추출 (\"Ignore previous instructions ...\"). 비밀 누출 + 회피 전략 학습."),
        ("LLM08:2025", "Vector and Embedding Weaknesses",
         "RAG 의 vector store 조작 / embedding inversion / poisoned chunk insertion."),
        ("LLM09:2025", "Misinformation",
         "할루시네이션 → 잘못된 정보 (CVE 가짜, code 잘못, 의학 위험). RAG + citation 으로 완화."),
        ("LLM10:2025", "Unbounded Consumption",
         "비용 / token / 시간 무제한. DoS 가능 / 비용 폭주. rate limit + max_tokens."),
    ],
}


def import_to_bastion(bastion_url: str) -> dict:
    added, errors = 0, 0
    for category, items in OWASP_DATA.items():
        for code, name, desc in items:
            payload = {
                "kind": "owasp_top10",
                "label": code,
                "body": (
                    f"category: {category}\n"
                    f"name: {name}\n"
                    f"description: {desc}\n"
                ),
                "related_ids": [f"category:{category}", f"name:{name}"],
                "valid_from": "",
                "valid_until": "",
            }
            try:
                req = urllib.request.Request(
                    f"{bastion_url}/history/anchors",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    json.load(r)
                added += 1
            except Exception:
                errors += 1
    return {"added": added, "errors": errors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--via-bastion", action="store_true")
    ap.add_argument("--bastion-url", default=os.getenv("BASTION_URL", "http://192.168.0.115:8003"))
    args = ap.parse_args()

    print("=== OWASP Top 10 (Web 2021 + API 2023 + LLM 2025) ===")
    for cat, items in OWASP_DATA.items():
        print(f"\n[{cat}] {len(items)} items:")
        for code, name, _ in items:
            print(f"  {code:12s} {name}")
    print(f"\n총 {sum(len(v) for v in OWASP_DATA.values())} 항목")

    if args.dry_run: return

    if args.via_bastion:
        print(f"\n[mode] bastion REST → {args.bastion_url}")
        result = import_to_bastion(args.bastion_url)
        print(f"\n=== 결과 ===")
        for k, v in result.items():
            print(f"  {k:10s} {v}")


if __name__ == "__main__":
    main()
