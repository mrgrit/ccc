"""MITRE ATT&CK Enterprise STIX → KG anchor (kind=mitre_technique)

외부 지식 두 번째 채널 (P15). KEV 와 동일 패턴.

Source: https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json
형식: STIX 2.1 bundle. objects 에 attack-pattern (technique) + tactic + ...

CLI:
  python3 scripts/ingest_mitre_attck.py [--via-bastion] [--limit N] [--dry-run] [--from-file path.json]
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ATTACK_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"
ATTACK_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "mitre_attack_enterprise.json")


def fetch_attack(force_refresh: bool = False) -> dict:
    import time
    if not force_refresh and os.path.isfile(ATTACK_CACHE):
        age = time.time() - os.path.getmtime(ATTACK_CACHE)
        if age < 7 * 24 * 3600:  # 1주 캐시
            print(f"[cache] {ATTACK_CACHE} (age {age/3600:.1f}h)")
            with open(ATTACK_CACHE) as f:
                return json.load(f)
    print(f"[fetch] {ATTACK_URL}")
    req = urllib.request.Request(ATTACK_URL, headers={"User-Agent": "CCC/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    os.makedirs(os.path.dirname(ATTACK_CACHE), exist_ok=True)
    with open(ATTACK_CACHE, "w") as f:
        json.dump(data, f)
    print(f"[cached] {len(data.get('objects',[]))} STIX objects")
    return data


def extract_techniques(data: dict) -> list[dict]:
    """STIX bundle 에서 attack-pattern 만 추출. revoked/deprecated 제외."""
    techniques = []
    for obj in data.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue
        # MITRE ATT&CK ID 추출
        tid = ""
        for ref in obj.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id", "")
                break
        if not tid:
            continue
        # tactics (kill_chain_phases)
        tactics = [p.get("phase_name", "") for p in obj.get("kill_chain_phases", [])
                   if p.get("kill_chain_name") == "mitre-attack"]
        techniques.append({
            "id": tid,
            "name": obj.get("name", ""),
            "description": (obj.get("description") or "")[:600],
            "tactics": tactics,
            "platforms": obj.get("x_mitre_platforms", []),
            "data_sources": obj.get("x_mitre_data_sources", []),
            "is_subtechnique": obj.get("x_mitre_is_subtechnique", False),
            "permissions_required": obj.get("x_mitre_permissions_required", []),
        })
    return techniques


def import_to_bastion(techniques: list[dict], bastion_url: str, *, limit: int | None = None) -> dict:
    if limit:
        techniques = techniques[:limit]
    added, errors = 0, 0
    for t in techniques:
        body_text = (
            f"name: {t['name']}\n"
            f"tactics: {', '.join(t['tactics'])}\n"
            f"platforms: {', '.join(t['platforms'])}\n"
            f"data_sources: {', '.join(t['data_sources'][:5])}\n"
            f"description: {t['description']}\n"
            f"subtechnique: {t['is_subtechnique']}\n"
            f"permissions: {', '.join(t['permissions_required'])}"
        )
        related = [f"tactic:{tac}" for tac in t["tactics"]] + \
                  [f"platform:{p}" for p in t["platforms"][:5]]
        payload = {
            "kind": "mitre_technique",
            "label": t["id"],
            "body": body_text,
            "related_ids": related,
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
    return {"added": added, "errors": errors, "total": len(techniques)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="통계만")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--from-file")
    ap.add_argument("--force-refresh", action="store_true")
    ap.add_argument("--via-bastion", action="store_true",
                    help="bastion REST /history/anchors 로 등록")
    ap.add_argument("--bastion-url", default=os.getenv("BASTION_URL", "http://192.168.0.103:8003"))
    args = ap.parse_args()

    if args.from_file:
        with open(args.from_file) as f:
            data = json.load(f)
    else:
        try:
            data = fetch_attack(force_refresh=args.force_refresh)
        except Exception as e:
            print(f"FETCH FAILED: {e}")
            sys.exit(1)

    techniques = extract_techniques(data)
    print(f"\nattack-pattern 총 (revoked 제외): {len(techniques)}")
    subs = sum(1 for t in techniques if t["is_subtechnique"])
    print(f"  sub-technique: {subs}")
    print(f"  parent: {len(techniques) - subs}")
    from collections import Counter
    by_tactic = Counter()
    for t in techniques:
        for tac in t["tactics"]:
            by_tactic[tac] += 1
    print(f"  by tactic:")
    for tac, n in by_tactic.most_common(8):
        print(f"    {tac:25s} {n}")

    if args.dry_run:
        print(f"\n[dry-run] 적재 X")
        return

    if args.via_bastion:
        print(f"\n[mode] bastion REST → {args.bastion_url}")
        result = import_to_bastion(techniques, args.bastion_url, limit=args.limit)
        print(f"\n=== 결과 ===")
        for k, v in result.items():
            print(f"  {k:10s} {v}")


if __name__ == "__main__":
    main()
