#!/usr/bin/env python3
"""R3 자동 진단 스크립트 — 시간순 cluster + 5축 + ERROR 패턴 분류.

사용:
    python3 scripts/r3_diagnose.py
    python3 scripts/r3_diagnose.py --window-min 30   # 최근 N분 cluster 만

기능:
1. R3 5축 측정 (거부율 / unique skill / first_turn_retry / verdict 분포 / bastion 헬스)
2. 시간순 cluster 분석 — 30초 안에 같은 verdict 10+ 건 = transition 의심
3. ERROR 패턴 분류 — connection refused / timeout / 거부 / unknown
4. 누적 pass 추이 — R0/R2/R3 별 카운트
5. cron-friendly: 결과를 results/retest/r3_diagnose_<ts>.md 로 저장
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "results/retest/run_r3.log"
PROGRESS = ROOT / "bastion_test_progress.json"
CURSOR = ROOT / "results/retest/cursor_r3.txt"
QUEUE = ROOT / "results/retest/queue_r3.tsv"
BASTION = "http://192.168.0.103:8003/health"


def parse_log() -> list[dict]:
    """log line → events with idx, timestamp, verdict, skill, elapsed."""
    if not LOG.exists():
        return []
    events = []
    cur = None
    line_re = re.compile(
        r"\[(?P<ts>2026[\d:T+\-]+)\] R3 #(?P<idx>\d+)/\d+ (?P<course>\S+) w(?P<wk>\d+) o(?P<order>\d+) \(prev=(?P<prev>\w+)")
    verdict_re = re.compile(
        r"VERDICT: (?P<verdict>\w+)\s*(?:skill=(?P<skill>[a-z_]*))?\s*(?:elapsed=(?P<elapsed>[\d.]+)s)?")
    error_re = re.compile(r"ERROR: (.+?)(?:\(elapsed|$)")

    with open(LOG, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = line_re.search(line)
            if m:
                cur = {
                    "ts": datetime.fromisoformat(m.group("ts")),
                    "idx": int(m.group("idx")),
                    "course": m.group("course"),
                    "week": int(m.group("wk")),
                    "order": int(m.group("order")),
                    "prev": m.group("prev"),
                    "error_detail": "",
                }
                continue
            if cur is None:
                continue
            em = error_re.search(line)
            if em:
                cur["error_detail"] = em.group(1).strip()[:80]
            v = verdict_re.search(line)
            if v:
                cur["verdict"] = v.group("verdict")
                cur["skill"] = (v.group("skill") or "").strip()
                try:
                    cur["elapsed"] = float(v.group("elapsed") or 0)
                except Exception:
                    cur["elapsed"] = 0.0
                events.append(cur)
                cur = None
    return events


def detect_clusters(events: list[dict], threshold_count=10, window_sec=60) -> list[dict]:
    """30~60초 안에 같은 verdict 10+ 건 = transition cluster."""
    clusters = []
    by_verdict = defaultdict(list)
    for e in events:
        by_verdict[e["verdict"]].append(e)
    for verdict, items in by_verdict.items():
        items.sort(key=lambda e: e["ts"])
        i = 0
        while i < len(items):
            j = i
            while j + 1 < len(items) and (items[j + 1]["ts"] - items[i]["ts"]).total_seconds() <= window_sec:
                j += 1
            cnt = j - i + 1
            if cnt >= threshold_count:
                clusters.append({
                    "verdict": verdict,
                    "count": cnt,
                    "start": items[i]["ts"].isoformat(),
                    "end": items[j]["ts"].isoformat(),
                    "duration_sec": (items[j]["ts"] - items[i]["ts"]).total_seconds(),
                    "first_idx": items[i]["idx"],
                    "last_idx": items[j]["idx"],
                })
            i = j + 1
    return clusters


def classify_errors(events: list[dict]) -> dict[str, int]:
    """ERROR detail 패턴별 분류."""
    cat = Counter()
    for e in events:
        if e.get("verdict") != "error":
            continue
        d = e.get("error_detail", "").lower()
        if "connection refused" in d or "errno 111" in d:
            cat["connection_refused"] += 1
        elif "timeout" in d or "timed out" in d:
            cat["timeout"] += 1
        elif "json" in d or "decode" in d:
            cat["json_decode"] += 1
        elif d:
            cat["other"] += 1
        else:
            cat["unknown"] += 1
    return dict(cat)


def axis5(events: list[dict]) -> dict:
    """5축 측정."""
    log_text = LOG.read_text(encoding="utf-8", errors="ignore") if LOG.exists() else ""
    return {
        "거부율": len(re.findall(r"I'm sorry|cannot help|can't help", log_text)),
        "unique_skill": len(set(e["skill"] for e in events if e.get("skill"))),
        "skill_분포": dict(Counter(e["skill"] for e in events if e.get("skill")).most_common()),
        "first_turn_retry": log_text.count("first_turn_retry"),
        "verdict_분포": dict(Counter(e["verdict"] for e in events)),
    }


def cumulative_pass() -> dict:
    """R0/R2/R3 별 누적 pass."""
    if not PROGRESS.exists():
        return {}
    p = json.loads(PROGRESS.read_text())
    res = p.get("results", {})
    counts = Counter()
    for c, weeks in res.items():
        for wk, orders in weeks.items():
            for o, val in orders.items():
                if isinstance(val, dict):
                    counts[val.get("status")] += 1
    total = sum(counts.values())
    return {
        "total": total,
        "pass": counts.get("pass", 0),
        "pass_pct": round(counts.get("pass", 0) / max(total, 1) * 100, 1),
        "fail": counts.get("fail", 0),
        "no_execution": counts.get("no_execution", 0),
        "error": counts.get("error", 0),
        "qa_fallback": counts.get("qa_fallback", 0),
    }


def bastion_alive() -> bool:
    try:
        out = subprocess.check_output(
            ["curl", "-s", "--max-time", "3", BASTION], stderr=subprocess.DEVNULL).decode()
        return '"status":"ok"' in out
    except Exception:
        return False


def cursor_state() -> tuple[int, int]:
    try:
        c = int(CURSOR.read_text().strip())
    except Exception:
        c = 0
    try:
        q = int(subprocess.check_output(["wc", "-l", str(QUEUE)]).split()[0])
    except Exception:
        q = 0
    return c, q


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-min", type=int, default=0,
                        help="최근 N분만 분석 (0=전체)")
    parser.add_argument("--save", action="store_true",
                        help="results/retest/r3_diagnose_<ts>.md 로 저장")
    args = parser.parse_args()

    events = parse_log()
    if args.window_min > 0:
        cutoff = datetime.now() - timedelta(minutes=args.window_min)
        # ISO 의 tz 가 +09:00 이라 cutoff 도 동일 tz 가정 (시스템 timezone)
        events = [e for e in events
                  if e["ts"].replace(tzinfo=None) >= cutoff.replace(tzinfo=None)]

    cur, q = cursor_state()
    a5 = axis5(events)
    clusters = detect_clusters(events)
    err_cats = classify_errors(events)
    cum = cumulative_pass()
    alive = bastion_alive()

    lines = [
        f"# R3 진단 리포트 — {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"## 진행 상태",
        f"- cursor: **{cur}/{q}** ({round(cur / max(q, 1) * 100, 1)}%)",
        f"- bastion: {'✅ alive' if alive else '❌ DOWN'}",
        f"- analyzed events: {len(events)}",
        "",
        f"## 5축 측정",
        f"- 거부율: **{a5['거부율']}** (목표 0)",
        f"- unique skill: **{a5['unique_skill']}** / 33 catalog",
        f"- first_turn_retry: **{a5['first_turn_retry']}**",
        f"- skill 분포: {a5['skill_분포']}",
        f"- verdict 분포: {a5['verdict_분포']}",
        "",
        f"## ERROR 분류",
    ]
    if err_cats:
        for cat, n in err_cats.items():
            lines.append(f"- {cat}: {n}")
    else:
        lines.append("- (error 0건)")

    lines += ["", "## 시간 cluster (>=10건/60초)"]
    if clusters:
        for c in clusters:
            lines.append(
                f"- **{c['verdict']}** {c['count']}건 in {c['duration_sec']:.0f}s "
                f"(#{c['first_idx']}~#{c['last_idx']}, {c['start']} → {c['end']})")
    else:
        lines.append("- (cluster 없음)")

    lines += ["", "## 누적 pass (R0+R2+R3)"]
    if cum:
        lines.append(f"- total: {cum['total']}, pass: **{cum['pass']} ({cum['pass_pct']}%)**, "
                     f"fail: {cum['fail']}, no_exec: {cum['no_execution']}, error: {cum['error']}, qa: {cum['qa_fallback']}")

    # 자동 진단 ◆◯⚠️
    lines += ["", "## 자동 진단"]
    diag = []
    if not alive:
        diag.append("❌ bastion DOWN — 즉시 재시작 필요")
    if a5["거부율"] > 0:
        diag.append(f"⚠️ 거부 {a5['거부율']}건 — attack_mode preamble 추가 강화 필요")
    if a5["unique_skill"] < 12:
        diag.append(f"⚠️ active skill 만 {a5['unique_skill']} (33 catalog 대비 {round(a5['unique_skill']/33*100)}%) — recall 보강")
    if err_cats.get("connection_refused", 0) > 5:
        diag.append(f"⚠️ connection refused {err_cats['connection_refused']}건 — bastion 재시작 transition 또는 동시 요청 의심")
    if clusters:
        for c in clusters:
            if c["verdict"] == "error":
                diag.append(f"⚠️ ERROR cluster: #{c['first_idx']}~#{c['last_idx']} {c['count']}건 in {c['duration_sec']:.0f}s — 서비스 장애 시간대 확인")
    if not diag:
        diag.append("✅ 이상 신호 없음 — 정상 진행 중")
    for d in diag:
        lines.append(f"- {d}")

    output = "\n".join(lines)
    print(output)

    if args.save:
        ts = datetime.now().strftime("%Y%m%d-%H%M")
        out_path = ROOT / f"results/retest/r3_diagnose_{ts}.md"
        out_path.write_text(output, encoding="utf-8")
        print(f"\n→ saved: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
