"""CISA KEV (Known Exploited Vulnerabilities) → KG Concept 노드 임포트

외부 지식 자동 수집 첫 채널 (P15).

Source: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
형식: {"catalogVersion", "dateReleased", "count", "vulnerabilities": [...]}
각 vuln: {cveID, vendorProject, product, vulnerabilityName, dateAdded,
         shortDescription, requiredAction, dueDate, knownRansomwareCampaignUse, notes, cwes}

KG 매핑:
  Concept(concept:cve:CVE-2024-XXXX) — name = CVE-2024-XXXX
  content: {description, vendor, product, vulnerability_name, kev_added,
            due_date, cwes, ransomware_use, source: "CISA KEV"}

CLI:
  python3 scripts/ingest_cisa_kev.py [--dry-run] [--limit N] [--from-file path.json]
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
KEV_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "data", "cisa_kev_latest.json")


def fetch_kev(force_refresh: bool = False) -> dict:
    """KEV JSON 가져오기. 캐시 우선 (24h)."""
    import time
    if not force_refresh and os.path.isfile(KEV_CACHE):
        age = time.time() - os.path.getmtime(KEV_CACHE)
        if age < 24 * 3600:
            print(f"[cache] {KEV_CACHE} (age {age/3600:.1f}h)")
            with open(KEV_CACHE) as f:
                return json.load(f)
    print(f"[fetch] {KEV_URL}")
    req = urllib.request.Request(KEV_URL, headers={"User-Agent": "CCC/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    os.makedirs(os.path.dirname(KEV_CACHE), exist_ok=True)
    with open(KEV_CACHE, "w") as f:
        json.dump(data, f)
    print(f"[cached] {len(data.get('vulnerabilities',[]))} vulns")
    return data


def import_to_kg(data: dict, *, dry_run: bool = False, limit: int | None = None) -> dict:
    """Concept 노드로 KG 적재. dry-run 이면 통계만."""
    vulns = data.get("vulnerabilities", [])
    if limit:
        vulns = vulns[:limit]

    if dry_run:
        # 통계만
        from collections import Counter
        years = Counter(v.get("dateAdded", "")[:4] for v in vulns)
        vendors = Counter(v.get("vendorProject", "") for v in vulns)
        ransom = sum(1 for v in vulns if (v.get("knownRansomwareCampaignUse") or "").lower() == "known")
        print(f"\n=== Dry-run statistics ===")
        print(f"  total vulns: {len(vulns)}")
        print(f"  ransomware-use known: {ransom}")
        print(f"  top years (added):")
        for y, n in sorted(years.items())[-5:]:
            print(f"    {y}: {n}")
        print(f"  top vendors:")
        for v, n in vendors.most_common(8):
            print(f"    {v:25s} {n}")
        return {"dry_run": True, "total": len(vulns), "ransomware": ransom}

    from packages.bastion.graph import get_graph
    g = get_graph()
    added, skipped, updated = 0, 0, 0
    for v in vulns:
        cve = v.get("cveID", "").strip()
        if not cve:
            continue
        nid = f"concept:cve:{cve}"
        existing = g.get_node(nid)
        content = {
            "cve_id": cve,
            "description": (v.get("shortDescription") or "")[:600],
            "vendor": v.get("vendorProject", ""),
            "product": v.get("product", ""),
            "vulnerability_name": (v.get("vulnerabilityName") or "")[:200],
            "kev_added": v.get("dateAdded", ""),
            "due_date": v.get("dueDate", ""),
            "required_action": (v.get("requiredAction") or "")[:400],
            "cwes": v.get("cwes", []),
            "ransomware_use": v.get("knownRansomwareCampaignUse", ""),
            "source": "CISA KEV",
        }
        meta = {
            "source": "CISA-KEV",
            "kev_catalog_version": data.get("catalogVersion", ""),
            "imported_at": data.get("dateReleased", ""),
        }
        if existing:
            # update content (refresh)
            g.add_node(nid, "Concept", cve, content=content, meta=meta)
            updated += 1
        else:
            g.add_node(nid, "Concept", cve, content=content, meta=meta)
            added += 1
    return {"total": len(vulns), "added": added, "updated": updated, "skipped": skipped}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="통계만, KG 적재 X")
    ap.add_argument("--limit", type=int, default=None, help="첫 N건만")
    ap.add_argument("--from-file", help="로컬 JSON 파일 (네트워크 우회)")
    ap.add_argument("--force-refresh", action="store_true", help="캐시 무시 + 재다운로드")
    args = ap.parse_args()

    if args.from_file:
        with open(args.from_file) as f:
            data = json.load(f)
        print(f"[file] {args.from_file}: {len(data.get('vulnerabilities',[]))} vulns")
    else:
        try:
            data = fetch_kev(force_refresh=args.force_refresh)
        except Exception as e:
            print(f"FETCH FAILED: {e}")
            print(f"  → 인터넷 접근 불가 시: --from-file <KEV.json> 사용")
            sys.exit(1)

    print(f"\nKEV catalog version: {data.get('catalogVersion','?')}")
    print(f"KEV count (header):   {data.get('count','?')}")
    print(f"vulns in payload:     {len(data.get('vulnerabilities',[]))}")

    result = import_to_kg(data, dry_run=args.dry_run, limit=args.limit)
    print(f"\n=== 결과 ===")
    for k, v in result.items():
        print(f"  {k:12s} {v}")

    if not args.dry_run:
        # KG 의 cve concept 총 갯수
        from packages.bastion.graph import get_graph
        g = get_graph()
        cve_concepts = [n for n in g.find_nodes("Concept") if (n.get("id") or "").startswith("concept:cve:")]
        print(f"\nKG concept:cve:* total: {len(cve_concepts)}")


if __name__ == "__main__":
    main()
