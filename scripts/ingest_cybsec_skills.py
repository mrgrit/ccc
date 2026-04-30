"""Anthropic-Cybersecurity-Skills (mukul975, Apache 2.0) → KG anchor (kind=cybsec_skill)

외부 지식 8번째 채널 (P15 Phase A PoC).

Source: https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- 754 SKILL.md (YAML frontmatter + workflow)
- 26 보안 도메인 + 5 framework 매핑

Phase A PoC: deception 3 + compliance 4 + digital-forensics 5 = 12건 시범
Phase B (확장 시): 26 도메인 754건 풀 임포트 (몇 시간 작업).

CLI:
  python3 scripts/ingest_cybsec_skills.py --repo-path /tmp/Anthropic-Cybersecurity-Skills [--via-bastion] [--all]
"""
from __future__ import annotations
import sys, os, json, urllib.request, argparse, re
from pathlib import Path

# Phase A: 시범 도메인 (검증용)
PHASE_A_SUBDOMAINS = {"deception", "compliance", "digital-forensics"}


def parse_skill_md(md_path: Path) -> dict | None:
    """SKILL.md 의 YAML frontmatter + 본문 파싱."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    # frontmatter (--- ... ---)
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return None
    fm_text = m.group(1)
    body = m.group(2)

    # naive YAML parse — flat key:value + list
    fm = {}
    cur_list_key = None
    for line in fm_text.split("\n"):
        if not line.strip():
            cur_list_key = None
            continue
        if line.startswith("- "):
            if cur_list_key:
                fm.setdefault(cur_list_key, []).append(line[2:].strip())
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v == "":
                cur_list_key = k
            else:
                fm[k] = v.strip("'\"")
                cur_list_key = None

    # body 의 첫 100자만
    body_short = body.strip()[:300].replace("\n", " ")

    return {
        "name": fm.get("name", md_path.parent.name),
        "description": fm.get("description", ""),
        "domain": fm.get("domain", ""),
        "subdomain": fm.get("subdomain", ""),
        "tags": fm.get("tags", []),
        "nist_csf": fm.get("nist_csf", []),
        "mitre_attck": fm.get("mitre_attck", []),
        "atlas": fm.get("atlas", []),
        "d3fend": fm.get("d3fend", []),
        "version": fm.get("version", "1.0"),
        "author": fm.get("author", ""),
        "license": fm.get("license", "Apache-2.0"),
        "body_excerpt": body_short,
    }


def skill_to_anchor(skill: dict) -> dict:
    related_ids = []
    for k in ("nist_csf", "mitre_attck", "atlas", "d3fend"):
        related_ids += list(skill.get(k, []))
    if skill.get("subdomain"):
        related_ids.append(f"subdomain:{skill['subdomain']}")

    body_lines = [
        f"name: {skill['name']}",
        f"subdomain: {skill.get('subdomain', '')}",
        f"description: {skill['description'][:200]}",
        f"tags: {','.join(skill.get('tags', [])[:8])}",
        f"frameworks: csf={len(skill.get('nist_csf', []))}, attck={len(skill.get('mitre_attck', []))}, atlas={len(skill.get('atlas', []))}, d3fend={len(skill.get('d3fend', []))}",
        f"author: {skill.get('author', '')} (license: {skill.get('license', 'Apache-2.0')})",
    ]

    return {
        "kind": "cybsec_skill",
        "label": skill["name"],
        "body": "\n".join(body_lines),
        "related_ids": related_ids[:20],  # bastion API limit
        "valid_from": "2025-01-01",
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
    ap.add_argument("--repo-path", default="/tmp/Anthropic-Cybersecurity-Skills")
    ap.add_argument("--via-bastion", action="store_true")
    ap.add_argument("--bastion-url", default=os.getenv("BASTION_URL", "http://192.168.0.103:8003"))
    ap.add_argument("--all", action="store_true", help="전체 754 임포트 (Phase B)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_path)
    skills_dir = repo / "skills"
    if not skills_dir.exists():
        print(f"  ERROR: skills dir not found at {skills_dir}", file=sys.stderr)
        return

    md_paths = sorted(skills_dir.glob("*/SKILL.md"))
    print(f"=== Anthropic-Cybersecurity-Skills (mukul975) ===")
    print(f"  total SKILL.md found: {len(md_paths)}")

    skills = []
    for p in md_paths:
        s = parse_skill_md(p)
        if s:
            skills.append(s)

    if args.all:
        target = skills
        print(f"  Phase B (전체) — {len(target)} skills")
    else:
        target = [s for s in skills if s.get("subdomain") in PHASE_A_SUBDOMAINS]
        print(f"  Phase A (deception/compliance/digital-forensics) — {len(target)} skills")

    anchors = [skill_to_anchor(s) for s in target]

    if args.dry_run:
        for a in anchors[:5]:
            print(f"  - {a['label']}")
            print(f"    related_ids: {a['related_ids'][:5]}")
        if len(anchors) > 5:
            print(f"  ... + {len(anchors)-5} more")
        return

    if args.via_bastion:
        r = import_to_bastion(args.bastion_url, anchors)
        print(f"  added={r['added']}, errors={r['errors']}")
    else:
        print(f"  prepared {len(anchors)} anchors (use --via-bastion to import)")


if __name__ == "__main__":
    main()
