#!/usr/bin/env python3
"""Phase B — 각 lab course 디렉토리에 precinct6_cases.md 생성.

lab YAML 자체는 수정하지 않음 (verify 무결성 보호). 별도 markdown 파일로
"이 코스의 lab 들과 관련된 real-world incidents" 부록 제공.

Phase A 와 동일한 COURSE_TECHNIQUE_MAP 사용 + breach_pair anchor fallback.

사용:
  python3 scripts/inject_lab_cases.py --all
  python3 scripts/inject_lab_cases.py --course attack-ai --dry-run
"""
from __future__ import annotations
import argparse, sys, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DB = ROOT / "data" / "bastion_graph.db"


# lab course 명 (Phase A 의 course 명과 다름, ai/non-ai suffix 분리)
COURSE_TECHNIQUE_MAP = {
    "attack-ai":          ["T1041","T1190","T1059"],
    "attack-adv-ai":      ["T1041","T1078","T1110"],
    "secops-ai":          ["T1530","T1078"],
    "soc-ai":             ["T1041","T1530"],
    "soc-adv-ai":         ["T1041","T1078","T1530"],
    "web-vuln-ai":        ["T1190","T1059"],
    "compliance-ai":      ["T1530"],
    "cloud-container-ai": ["T1530","T1078"],
    "ai-security-ai":     ["T1530"],
    "ai-safety-ai":       ["T1530"],
    "ai-safety-adv-ai":   ["T1530"],
    "autonomous-ai":      ["T1190"],
    "autonomous-systems-ai": ["T1190"],
    "ai-agent-ai":        ["T1041"],
    "battle-ai":          ["T1041","T1190","T1078"],
    "battle-adv-ai":      ["T1041","T1078","T1110"],
    "agent-ir-ai":        ["T1041","T1530"],
    "agent-ir-adv-ai":    ["T1041","T1530","T1078"],
    "physical-pentest-ai":["T1078","T1110"],
    "iot-security-ai":    ["T1190","T1078"],
}


def load_breach_pair_anchors(limit: int = 5) -> list[dict]:
    if not GRAPH_DB.exists(): return []
    out = []
    con = sqlite3.connect(GRAPH_DB); cur = con.cursor()
    rows = cur.execute(
        "SELECT label, body FROM history_anchors WHERE kind='breach_record' "
        "AND label LIKE 'breach_pair:%' ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    for label, body in rows:
        out.append({"label": label, "body": body, "technique": "T1041 (Data Theft)"})
    con.close()
    return out


def load_breach_anchors_for_techniques(techniques: list[str], limit: int = 3) -> list[dict]:
    if not GRAPH_DB.exists(): return []
    out = []
    con = sqlite3.connect(GRAPH_DB); cur = con.cursor()
    for tech in techniques:
        like = f"%:{tech}"
        rows = cur.execute(
            "SELECT label, body FROM history_anchors WHERE kind='breach_record' "
            "AND label LIKE ? ORDER BY id DESC LIMIT ?", (like, limit)
        ).fetchall()
        for label, body in rows:
            out.append({"label": label, "body": body, "technique": tech})
    con.close()
    return out


def render(course: str, cases: list[dict], pairs: list[dict]) -> str:
    lines = [
        f"# Real-world Cases — {course}",
        "",
        "> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)",
        "> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화",
        "",
        "이 코스의 lab 들이 다루는 위협 카테고리와 연관된 실제 incident 기록입니다.",
        "각 lab 시작 전 해당 케이스를 참고해 어떤 패턴을 재현·탐지·대응할지 미리 가늠하세요.",
        "",
        "---",
        "",
    ]
    if cases:
        lines.append("## Technique 별 사례")
        lines.append("")
        seen = set()
        for c in cases[:6]:
            if c["label"] in seen: continue
            seen.add(c["label"])
            lines.append(f"### `{c['technique']}` 패턴")
            lines.append("")
            lines.append("```")
            for ln in c["body"].split("\n")[:6]:
                lines.append(ln)
            lines.append("```")
            lines.append("")
    if pairs:
        lines.append("## Red ↔ Blue 공격 쌍 (실제 incident 기반)")
        lines.append("")
        lines.append("아래는 실제 보안 운영 환경에서 관찰된 공격자(Exploiting Host) → 피해자(Exploiting Target) 쌍입니다.")
        lines.append("battle 시나리오 또는 attack/defense lab 에서 동일 구조로 재현 가능합니다.")
        lines.append("")
        for p in pairs[:3]:
            lines.append(f"- `{p['label']}`")
            for ln in p['body'].split("\n")[:2]:
                lines.append(f"  > {ln}")
            lines.append("")
    return "\n".join(lines)


def inject(course_dir: Path, dry_run: bool = False) -> dict:
    course = course_dir.name
    techs = COURSE_TECHNIQUE_MAP.get(course, ["T1041"])
    out_path = course_dir / "precinct6_cases.md"
    cases = load_breach_anchors_for_techniques(techs, limit=3)
    pairs = load_breach_pair_anchors(limit=3)
    if not cases and not pairs:
        return {"status": "skip_no_data", "course": course}
    md = render(course, cases, pairs)
    if dry_run:
        return {"status": "would_write", "course": course, "chars": len(md),
                "cases": len(cases), "pairs": len(pairs)}
    out_path.write_text(md, encoding="utf-8")
    return {"status": "written", "course": course, "path": str(out_path),
            "cases": len(cases), "pairs": len(pairs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", help="single course (e.g. attack-ai)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = ROOT / "contents" / "labs"
    courses = []
    if args.course:
        courses = [base / args.course]
    elif args.all:
        # AI 변형만 (-ai suffix). nonai 는 skip.
        courses = sorted([p for p in base.iterdir() if p.is_dir() and p.name.endswith("-ai")])
    else:
        sys.exit("ERROR: --course 또는 --all 필요")
    print(f"target courses: {len(courses)}")
    counts = {"written": 0, "would_write": 0, "skip_no_data": 0}
    for c in courses:
        if not c.is_dir(): continue
        r = inject(c, dry_run=args.dry_run)
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] in ("written", "would_write"):
            print(f"  ✓ {c.name}: {r['status']} (cases={r['cases']} pairs={r['pairs']})")
    print("\n=== summary ===")
    for k, v in counts.items():
        if v: print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
