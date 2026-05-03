#!/usr/bin/env python3
"""Mass fixture 적용 — fail step 자동 식별 + generator 매핑 + fixtures 필드 추가.

각 step 의 instruction 키워드 → 적절한 generator 매핑:
- /var/log/auth.log / sshd / brute       → auth_log
- /var/log/apache2/access.log            → web_access
- /var/log/suricata/(fast|eve).log       → suricata_alert
- alerts.json / Wazuh / DNS group        → wazuh_alert
- iptables / nftables / drop / firewall  → firewall_log
- LOLBAS / certutil / powershell.*월     → lolbas_log

사용:
    # 후보 식별만 (수정 없음)
    python3 scripts/lab_fixture_auto_apply.py --dry-run

    # Top 20 적용
    python3 scripts/lab_fixture_auto_apply.py --top 20 --apply

    # 특정 코스만
    python3 scripts/lab_fixture_auto_apply.py --course soc-adv-nonai --apply
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
LABS = ROOT / "contents" / "labs"

# generator 매핑 — (regex, generator, default_path, default_params)
RULES = [
    (re.compile(r"(LOLBAS|certutil|powershell.*개월|wmic.*분산|6개월간 cert)"),
     "lolbas_log", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/audit.log",
     {"seed": 42, "duration_days": 180,
      "binaries": {"certutil": 7, "powershell": 18, "wmic": 3}}),

    (re.compile(r"(/var/log/auth\.log|sshd.*brute|brute.*ssh|password.*spray|sudo.*실패)"),
     "auth_log", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/auth.log",
     {"seed": 42, "duration_days": 30, "burst_count": 3,
      "spray_attempts": 100, "normal_logins_per_day": 8}),

    (re.compile(r"(/var/log/apache2/access\.log|access\.log.*분석|nginx.*log|"
                r"web.*트래픽.*분석|HTTP.*request.*분석)"),
     "web_access", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/access.log",
     {"seed": 42, "duration_days": 7, "scanner_bursts": 5,
      "sqli_attempts": 12, "xss_attempts": 8}),

    (re.compile(r"(/var/log/suricata/(fast|eve)\.log|Suricata.*alert|eve\.json)"),
     "suricata_alert", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/eve.json",
     {"seed": 42, "duration_days": 7, "alerts_per_day": 30,
      "c2_beacon_count": 12, "metadata_attempt_count": 4}),

    (re.compile(r"(alerts\.json|Wazuh.*alert|DNS.*그룹|rule\.id|rule\.groups)"),
     "wazuh_alert", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/alerts.json",
     {"seed": 42, "duration_days": 7, "alerts_per_day": 50,
      "brute_force_burst": True, "ar_trigger_count": 4}),

    (re.compile(r"(nftables|iptables|firewall.*log|drop.*log|kernel.*DROP)"),
     "firewall_log", "/home/ccc/cyber-range/fixtures/{lab_id}/{order}/syslog",
     {"seed": 42, "duration_days": 7, "scan_bursts": 5,
      "egress_violations": 20, "syn_flood_count": 200}),
]


def match_generator(instruction: str):
    for regex, gen, path_tmpl, params in RULES:
        if regex.search(instruction):
            return gen, path_tmpl, dict(params)
    return None


def process_lab(lab_path: Path, apply: bool, top_limit: int | None) -> list[dict]:
    """lab YAML 의 step 들을 순회하며 fixture 매핑 후보 + 선택적 적용."""
    with lab_path.open() as f:
        d = yaml.safe_load(f)
    lab_id = d.get("lab_id") or lab_path.stem
    course = d.get("course", lab_path.parent.name)
    week = d.get("week", 0)

    results = []
    for s in d.get("steps", []) or []:
        if "fixtures" in s:
            continue
        instr = s.get("instruction", "") or ""
        m = match_generator(instr)
        if not m:
            continue
        gen, path_tmpl, params = m
        path = path_tmpl.format(lab_id=lab_id, order=s["order"])
        results.append({
            "lab_path": str(lab_path),
            "lab_id": lab_id,
            "order": s["order"],
            "generator": gen,
            "path": path,
            "params": params,
            "instruction_preview": instr[:80],
        })

    if apply and results:
        if top_limit:
            results = results[:top_limit]
        # 적용 — fixtures 필드 추가 + instruction 보강
        for r in results:
            for s in d["steps"]:
                if s.get("order") == r["order"]:
                    s["fixtures"] = [{
                        "generator": r["generator"],
                        "target_vm": s.get("target_vm", "bastion"),
                        "path": r["path"],
                        "params": r["params"],
                        "mode": "overwrite",
                        "cleanup": False,
                    }]
                    s["instruction"] = (
                        f"{s['instruction']}\n\n"
                        f"[FIXTURE] 분석 대상 합성 데이터가 `{r['path']}` 에 사전 주입됨 "
                        f"(seed={r['params']['seed']}, generator={r['generator']}). "
                        f"실 환경 데이터 없으면 위 path 활용."
                    )
        with lab_path.open("w") as f:
            yaml.safe_dump(d, f, allow_unicode=True, sort_keys=False)
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--course", help="단일 코스 (예: soc-adv-nonai)")
    p.add_argument("--top", type=int, default=None,
                    help="lab 별 적용 max 수")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    if args.course:
        targets = sorted((LABS / args.course).glob("week*.yaml"))
    else:
        targets = sorted(LABS.rglob("week*.yaml"))

    total_candidates = 0
    total_applied = 0
    by_generator: dict[str, int] = {}

    for lab in targets:
        try:
            results = process_lab(lab, apply=args.apply, top_limit=args.top)
        except Exception as e:
            print(f"  ✗ {lab}: {e}")
            continue
        if not results:
            continue
        total_candidates += len(results)
        if args.apply:
            total_applied += len(results)
        for r in results:
            by_generator[r["generator"]] = by_generator.get(r["generator"], 0) + 1
        if args.apply:
            print(f"  ✓ {lab.name}: {len(results)} fixtures applied")

    print(f"\n=== 총 후보: {total_candidates} ===")
    if args.apply:
        print(f"=== 적용: {total_applied} ===")
    print("Generator 분포:")
    for g, n in sorted(by_generator.items(), key=lambda x: -x[1]):
        print(f"  {g}: {n}")


if __name__ == "__main__":
    main()
