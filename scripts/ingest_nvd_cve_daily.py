"""NVD CVE 일일 갱신 → KG anchor (kind=nvd_cve)

외부 지식 7번째 채널 (P15). NVD API 2.0 (https://services.nvd.nist.gov/rest/json/cves/2.0).

CISA KEV 와 다름:
- KEV = 실제 exploit 된 CVE (1,583)
- NVD = 모든 등록 CVE (200K+, 일일 ~30 신규)

본 script 는 *최근 24h 의 신규 CVE 만* 페치 → 점진 누적.
폐쇄망: NVD API 미접속 시 graceful skip.

CLI:
  python3 scripts/ingest_nvd_cve_daily.py [--via-bastion] [--lookback-hours 24] [--max 100]

Cron:
  0 6 * * * /usr/bin/python3 /home/opsclaw/ccc/scripts/ingest_nvd_cve_daily.py --via-bastion >> /home/opsclaw/ccc/results/nvd_cron.log 2>&1
"""
from __future__ import annotations
import sys, os, json, urllib.request, urllib.parse, argparse
from datetime import datetime, timedelta, timezone

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def fetch_recent_cves(lookback_hours: int = 24, max_results: int = 100) -> list:
    """Fetch CVEs published in the last N hours from NVD API."""
    now = datetime.now(timezone.utc)
    pub_start = now - timedelta(hours=lookback_hours)

    # NVD API 2.0 ISO 8601 format with milliseconds
    params = {
        "pubStartDate": pub_start.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "resultsPerPage": min(max_results, 2000),
    }
    url = f"{NVD_API}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CCC-Bastion/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  NVD fetch failed: {e}", file=sys.stderr)
        return []

    return data.get("vulnerabilities", [])[:max_results]


def cve_to_anchor(cve_item: dict) -> dict:
    """Convert NVD CVE item → KG anchor payload."""
    cve = cve_item.get("cve", {})
    cve_id = cve.get("id", "CVE-UNKNOWN")
    descriptions = cve.get("descriptions", [])
    en_desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")

    # CVSS score (try v3.1 first, fall back to v3.0, v2.0)
    metrics = cve.get("metrics", {})
    cvss = "N/A"
    severity = "UNKNOWN"
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if key in metrics and metrics[key]:
            cvss_data = metrics[key][0].get("cvssData", {})
            cvss = str(cvss_data.get("baseScore", "N/A"))
            severity = cvss_data.get("baseSeverity", "UNKNOWN")
            break

    cwe_ids = []
    for weakness in cve.get("weaknesses", []):
        for desc in weakness.get("description", []):
            v = desc.get("value", "")
            if v.startswith("CWE-"):
                cwe_ids.append(v)

    pub_date = cve.get("published", "")[:10]

    body_lines = [
        f"id: {cve_id}",
        f"cvss: {cvss} ({severity})",
        f"cwe: {','.join(cwe_ids) if cwe_ids else 'N/A'}",
        f"published: {pub_date}",
        f"description: {en_desc[:300]}",
    ]

    return {
        "kind": "nvd_cve",
        "label": cve_id,
        "body": "\n".join(body_lines),
        "related_ids": cwe_ids + [f"severity:{severity}"],
        "valid_from": pub_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "valid_until": "",
    }


def import_to_bastion(bastion_url: str, anchors: list) -> dict:
    added, errors = 0, 0
    for anchor in anchors:
        try:
            req = urllib.request.Request(
                f"{bastion_url}/history/anchors",
                data=json.dumps(anchor).encode(),
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
    ap.add_argument("--lookback-hours", type=int, default=24)
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"=== NVD CVE — last {args.lookback_hours}h (max {args.max}) ===")
    cves = fetch_recent_cves(args.lookback_hours, args.max)
    print(f"  fetched: {len(cves)} CVEs")

    if not cves:
        print("  (no new CVEs or fetch failed)")
        return

    anchors = [cve_to_anchor(c) for c in cves]
    if args.dry_run:
        for a in anchors[:3]:
            print(f"  - {a['label']}: {a['body'].splitlines()[1]}")
        print(f"  ... + {len(anchors)-3} more")
        return

    if args.via_bastion:
        r = import_to_bastion(args.bastion_url, anchors)
        print(f"  added={r['added']}, errors={r['errors']}")
    else:
        print(f"  prepared {len(anchors)} anchors (use --via-bastion to import)")


if __name__ == "__main__":
    main()
