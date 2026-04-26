#!/usr/bin/env python3
"""Phase A — 교안 (lectures) 에 Precinct 6 real incident case study 자동 주입.

각 week 의 lecture.md 의 학습 목표·제목 키워드를 Precinct breach_record / IoC anchor 와
간단한 keyword/MITRE 매칭하여 가장 관련 깊은 1-2 개 case 를 "## 실제 사례 (WitFoo Precinct 6)"
섹션으로 추가한다.

원칙:
- 기존 본문 수정 X. 섹션 미존재 시에만 append.
- sanitized 데이터 그대로 (RFC5737 TEST-NET, ORG-NNNN, HOST-NNNN).
- 출처 명시 (witfoo/precinct6-cybersecurity Apache 2.0).
- dry-run / pilot 우선 — 한 번에 1 course 만.

사용:
  # 단일 파일 dry-run
  python3 scripts/inject_lecture_cases.py --file contents/education/course5-soc/week01/lecture.md --dry-run
  # 한 코스만
  python3 scripts/inject_lecture_cases.py --course course5-soc
  # 전체 (주의)
  python3 scripts/inject_lecture_cases.py --all
"""
from __future__ import annotations
import argparse, os, sys, re, sqlite3, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DB = ROOT / "data" / "bastion_graph.db"
SECTION_HEADER = "## 실제 사례 (WitFoo Precinct 6)"


# week 번호 + 과목 키워드 → MITRE technique 매칭 (수동 큐레이션, 추후 RAG 로 대체)
COURSE_TECHNIQUE_MAP = {
    "course1-attack":          ["T1041","T1190","T1059"],   # exfil/exploit/exec
    "course13-attack-advanced":["T1041","T1078","T1110"],   # exfil/cred/brute
    "course2-security-ops":    ["T1530","T1078"],            # data-from-cloud, valid-acct
    "course5-soc":             ["T1041","T1530"],            # exfil patterns SOC sees
    "course14-soc-advanced":   ["T1041","T1078","T1530"],
    "course3-web-vuln":        ["T1190","T1059"],
    "course4-compliance":      ["T1530"],
    "course6-cloud-container": ["T1530","T1078"],
    "course7-ai-security":     ["T1530"],
    "course8-ai-safety":       ["T1530"],
    "course9-autonomous-security": ["T1190"],
    "course10-ai-security-agent":  ["T1041"],
    "course11-battle":         ["T1041","T1190","T1078"],
    "course12-battle-advanced":["T1041","T1078","T1110"],
    "course15-ai-safety-advanced": ["T1530"],
    "course16-physical-pentest":   ["T1078","T1110"],
    "course17-iot-security":   ["T1190","T1078"],
    "course18-autonomous-systems": ["T1190"],
    "course19-agent-incident-response": ["T1041","T1530"],
    "course20-agent-ir-advanced":       ["T1041","T1530","T1078"],
}


def load_breach_pair_anchors(limit: int = 2) -> list[dict]:
    """KG history_anchors 에서 breach_record 중 breach_pair (Red↔Blue) prefix anchor 추출."""
    if not GRAPH_DB.exists():
        return []
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


def load_breach_anchors_for_techniques(techniques: list[str], limit: int = 2) -> list[dict]:
    """KG history_anchors 에서 breach_record kind 중 해당 technique 매칭 anchor 추출."""
    if not GRAPH_DB.exists():
        return []
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


def render_section(cases: list[dict]) -> str:
    """case list → markdown section. 최대 2개만."""
    if not cases:
        return ""
    lines = [SECTION_HEADER, ""]
    lines.append("> 출처: WitFoo Precinct 6 Cybersecurity Dataset (Apache 2.0)")
    lines.append("> Sanitized — RFC5737 TEST-NET / ORG-NNNN / HOST-NNNN 으로 익명화됨.")
    lines.append("")
    seen_labels = set()
    cnt = 0
    for c in cases:
        if c["label"] in seen_labels:
            continue
        seen_labels.add(c["label"])
        cnt += 1
        if cnt > 2:
            break
        # parse body (label/body 단순 텍스트)
        lines.append(f"### Case {cnt}: `{c['technique']}` 패턴")
        lines.append("")
        lines.append("```")
        for ln in c["body"].split("\n")[:6]:
            lines.append(ln)
        lines.append("```")
        lines.append("")
        lines.append(f"**해석**: 위 데이터는 실제 incident 의 sanitized 기록이다. "
                     f"`{c['technique']}` MITRE technique 의 행동 패턴이며, "
                     f"본 강의의 학습 주제와 동일한 운영 맥락에서 발생한다.")
        lines.append("")
    return "\n".join(lines)


def inject(file_path: Path, dry_run: bool = False) -> dict:
    text = file_path.read_text(encoding="utf-8")
    if SECTION_HEADER in text:
        return {"status": "skip_already_injected", "file": str(file_path)}

    # course detect
    course = None
    for part in file_path.parts:
        if part.startswith("course"):
            course = part; break
    if not course:
        return {"status": "skip_no_course", "file": str(file_path)}

    techs = COURSE_TECHNIQUE_MAP.get(course, ["T1041"])  # 매핑 없어도 T1041 fallback
    if not techs:
        techs = ["T1041"]

    cases = load_breach_anchors_for_techniques(techs, limit=2)
    if not cases:
        # technique 매칭 anchor 없으면 breach_pair anchor (Red↔Blue) fallback
        cases = load_breach_pair_anchors(limit=2)
    if not cases:
        return {"status": "skip_no_cases", "file": str(file_path), "course": course, "techs": techs}

    section = render_section(cases)
    new_text = text.rstrip() + "\n\n---\n\n" + section + "\n"

    if dry_run:
        return {"status": "would_inject", "file": str(file_path), "cases": len(cases),
                "section_chars": len(section)}

    file_path.write_text(new_text, encoding="utf-8")
    return {"status": "injected", "file": str(file_path), "cases": len(cases),
            "delta_chars": len(new_text) - len(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="single lecture.md file")
    ap.add_argument("--course", help="single course directory name")
    ap.add_argument("--all", action="store_true", help="모든 lecture (주의)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = []
    if args.file:
        files = [Path(args.file).resolve()]
    elif args.course:
        base = ROOT / "contents" / "education" / args.course
        files = sorted(base.glob("week*/lecture.md"))
    elif args.all:
        files = sorted((ROOT / "contents" / "education").glob("course*/week*/lecture.md"))
    else:
        sys.exit("ERROR: --file / --course / --all 중 하나 필요")

    print(f"target files: {len(files)}")
    counts = {"injected": 0, "would_inject": 0, "skip_already_injected": 0,
              "skip_no_cases": 0, "skip_no_course": 0, "skip_no_tech_map": 0}
    for f in files:
        if not f.exists(): continue
        r = inject(f, dry_run=args.dry_run)
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] in ("injected", "would_inject"):
            print(f"  ✓ {f.relative_to(ROOT)}: {r['status']} ({r.get('cases')} cases)")
    print(f"\n=== summary ===")
    for k, v in counts.items():
        if v: print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
