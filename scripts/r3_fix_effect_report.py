#!/usr/bin/env python3
"""R3 fix-effect 정량 리포트 — paper §6.2 Table 의 데이터 채움.

R3 round 의 각 fix (timeout, KG path, Korean negative, acceptable_methods,
shell IP, curl auto-retry, self_verify 강화, 4-section answer, output trunc, retry)
가 회복한 step 수를 measurement log 에서 추출.

입력:
  results/retest/run_r3_*.log (V2, supplemental, low-3, R4)
출력:
  docs/r3-fix-effect.md (markdown table)
"""
from __future__ import annotations
import re
from pathlib import Path
from collections import Counter
import json

CCC = Path(__file__).resolve().parent.parent
RETEST = CCC / "results/retest"
OUT = CCC / "docs/r3-fix-effect.md"


def parse_log(log: Path) -> dict[str, int]:
    """log 파일에서 verdict 카운트 추출."""
    if not log.exists():
        return {}
    counts = Counter()
    elapsed_pct = []  # >280s percentage
    text = log.read_text(errors="ignore")
    for m in re.finditer(r"^VERDICT:\s+(\w+)\s+skill=\S*\s+elapsed=(\d+\.\d+)s",
                          text, re.MULTILINE):
        counts[m.group(1)] += 1
        elapsed_pct.append(float(m.group(2)))
    over_280 = sum(1 for e in elapsed_pct if e > 280) if elapsed_pct else 0
    return {
        "total": sum(counts.values()),
        "pass": counts.get("pass", 0),
        "fail": counts.get("fail", 0),
        "error": counts.get("error", 0),
        "no_execution": counts.get("no_execution", 0),
        "over_280_pct": (over_280 / len(elapsed_pct) * 100) if elapsed_pct else 0,
        "elapsed_avg": (sum(elapsed_pct) / len(elapsed_pct)) if elapsed_pct else 0,
    }


def main() -> None:
    rounds = {
        "R3 main": RETEST / "run_r3.log",
        "R3 noexec V2": RETEST / "run_r3_noexec_v2.log",
        "attack-ai supp": RETEST / "run_r3_attack_supplemental.log",
        "low-3 supp (in flight)": RETEST / "run_r3_low3_supplemental.log",
        "R4 (예정)": RETEST / "run_r4.log",
    }
    rows = []
    for name, log in rounds.items():
        stats = parse_log(log)
        if not stats:
            rows.append((name, "—", "—", "—", "—"))
            continue
        total = stats["total"]
        passed = stats["pass"]
        rate = (passed / total * 100) if total else 0
        rows.append((
            name,
            f"{total}",
            f"{passed} ({rate:.1f}%)",
            f"{stats['over_280_pct']:.1f}%",
            f"{stats['elapsed_avg']:.0f}s",
        ))

    # progress.json 누적 통계
    prog = CCC / "bastion_test_progress.json"
    cumulative = ""
    if prog.exists():
        try:
            d = json.loads(prog.read_text())
            res = d.get("results", {})
            cnts = Counter()
            for c, ws in res.items():
                for w, ss in ws.items():
                    for o, s in ss.items():
                        if isinstance(s, dict):
                            cnts[s.get("status", "unk")] += 1
            tot = sum(cnts.values())
            psd = cnts.get("pass", 0)
            cumulative = (
                f"\n## 누적 best-verdict (bastion_test_progress.json)\n"
                f"- pass: **{psd}/{tot}** ({psd/tot*100:.1f}%)\n"
                f"- fail: {cnts.get('fail',0)}\n"
                f"- error: {cnts.get('error',0)}\n"
                f"- no_execution: {cnts.get('no_execution',0)}\n"
                f"- qa_fallback: {cnts.get('qa_fallback',0)}\n"
            )
        except Exception:
            pass

    md = ["# R3 Fix-Effect Report\n",
          "*paper §6.2 Track A Table 의 raw data*\n",
          "\n## Round 별 결과\n",
          "| Round | Total | Pass (rate) | >280s % | avg elapsed |",
          "|---|---|---|---|---|"]
    for r in rows:
        md.append("| " + " | ".join(r) + " |")
    md.append("")
    md.append("## R3 fix 적용 (2026-04-30)")
    md.append("")
    md.append("| Fix | 변경 | 기대 효과 |")
    md.append("|---|---|---|")
    md.append("| #1 (76d1b921) | shell IP 자동 치환 (10.20.30.80→192.168.0.108 attacker 측) | attacker→web unreachable 차단 |")
    md.append("| #2 (1625b03e) | curl -s 짧은 응답 → -i -L 자동 retry | header/status 누락 차단 |")
    md.append("| #3 (e72ae39a) | self_verify·synthesis 프롬프트 강화 | self_verify_fail 무한 반복 차단 |")
    md.append("| #4 (5070990a) | 최종 답변 4섹션 강제 + target=web 금지 | judge no-output / 방어 누락 회복 |")
    md.append("| #5 (8e227393) | skill output truncation 1000→2500자 | curl 응답 잘림 차단 |")
    md.append("| #6 (db38639e) | call_bastion 네트워크 에러 1회 retry | bastion restart 시 ERROR 차단 |")
    md.append(cumulative)
    OUT.write_text("\n".join(md))
    print(f"Wrote {OUT}")
    print("\n".join(md[:30]))


if __name__ == "__main__":
    main()
