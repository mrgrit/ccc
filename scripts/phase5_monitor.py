#!/usr/bin/env python3
"""Phase 5 (5a Asset autoscan + 5e KPI 자동 record + 5f IoC anchor 매칭)
실시간 동작 확인 도구.

매 cron 사이클이 호출하면 baseline 과 비교해 변화량을 출력.
변화 없으면 "왜 안 늘어났나" 가능성을 자동 진단.

상태는 results/retest/phase5_baseline.json 에 영구 보관 (재시작 안전).
"""
from __future__ import annotations

import json
import os
import sys
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
env = ROOT / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BASELINE_FILE = ROOT / "results/retest/phase5_baseline.json"
RUN_LOG = ROOT / "results/retest/run.log"
OUT_REPORT = ROOT / "results/retest/phase5_report.md"


def measure() -> dict:
    """현재 상태 측정."""
    out: dict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    # Asset
    try:
        from packages.bastion.asset_domain import list_assets
        assets = list_assets(limit=1000)
        out["asset_count"] = len(assets)
        kinds: dict = {}
        for a in assets:
            k = (a.get("meta") or {}).get("kind", "unknown")
            kinds[k] = kinds.get(k, 0) + 1
        out["asset_kinds"] = kinds
    except Exception as e:
        out["asset_error"] = str(e)
    # KPI
    try:
        from packages.bastion.work_domain import strategic_dashboard
        d = strategic_dashboard()
        out["kpi_history_depth"] = {
            k["name"]: len(k.get("trend", []))
            for k in d.get("kpis", []) if "retest" in k.get("id", "")
        }
        out["kpi_latest"] = {
            k["name"]: (k.get("latest") or {}).get("value")
            for k in d.get("kpis", []) if "retest" in k.get("id", "")
        }
    except Exception as e:
        out["kpi_error"] = str(e)
    # History
    try:
        from packages.bastion.history import HistoryLayer
        h = HistoryLayer()
        with h._conn() as c:
            out["anchors"] = c.execute("SELECT COUNT(*) FROM history_anchors").fetchone()[0]
            out["events"] = c.execute("SELECT COUNT(*) FROM history_events").fetchone()[0]
            out["events_recent"] = c.execute(
                "SELECT COUNT(*) FROM history_events WHERE ts > datetime('now', '-2 hour')"
            ).fetchone()[0]
            out["narratives"] = c.execute("SELECT COUNT(*) FROM history_narratives").fetchone()[0]
    except Exception as e:
        out["history_error"] = str(e)
    # run.log 마커 (event print 안 되어도 카운트는 가능)
    if RUN_LOG.exists():
        log = RUN_LOG.read_text(errors="ignore")[-500_000:]  # 마지막 500KB만
        out["log_asset_autoregistered"] = log.count("asset_autoregistered")
        out["log_repeat_ioc_match"] = log.count("repeat_ioc_match")
        # probe 계열 실행 카운트
        out["log_probe_skill"] = len(re.findall(
            r"skill=(?:probe_host|probe_all)", log))
        out["log_total_steps"] = len(re.findall(r"VERDICT:", log))
    return out


def diagnose(prev: dict, cur: dict) -> list[str]:
    """변화 분석 + 가능성 진단."""
    msgs = []
    # Asset 증가
    da = cur.get("asset_count", 0) - prev.get("asset_count", 0)
    if da > 0:
        msgs.append(f"✅ Asset +{da} (5a 작동)")
    else:
        ps = cur.get("log_probe_skill", 0) - prev.get("log_probe_skill", 0)
        if ps > 0:
            msgs.append(f"⚠️ probe skill {ps}회 실행됐는데 Asset 변화 없음 — output 에서 IP 추출 실패 또는 등록 실패")
        else:
            msgs.append(f"○ probe skill 실행 0건 (큐에 probe 류 없음)")

    # KPI history depth 증가
    pkd = prev.get("kpi_history_depth", {}) or {}
    ckd = cur.get("kpi_history_depth", {}) or {}
    if any(ckd.get(k, 0) > pkd.get(k, 0) for k in ckd):
        gains = {k: ckd[k] - pkd.get(k, 0) for k in ckd}
        msgs.append(f"✅ KPI history +{max(gains.values())} (5e 작동) — {gains}")
    else:
        msgs.append("○ KPI history 무변화 (retest_report.py 호출 안 됨? cron fire 확인)")

    # IoC 매칭 (repeat_ioc_match 이벤트 + anchors 증가)
    irm = cur.get("log_repeat_ioc_match", 0) - prev.get("log_repeat_ioc_match", 0)
    da_anc = cur.get("anchors", 0) - prev.get("anchors", 0)
    if irm > 0:
        msgs.append(f"✅ repeat_ioc_match +{irm} (5f 작동, 과거 IoC 매칭)")
    if da_anc > 0:
        msgs.append(f"✅ Anchor +{da_anc}")
    if irm == 0 and prev.get("anchors", 0) < 10:
        msgs.append("○ Anchor 풀이 작아 매칭 가능성 낮음 (Precinct 6 import 또는 history_anchor skill 호출 후 의미)")

    # 이벤트 증가
    de = cur.get("events", 0) - prev.get("events", 0)
    if de > 0:
        msgs.append(f"✅ History events +{de} (agent 자동 기록)")
    else:
        ts = cur.get("log_total_steps", 0) - prev.get("log_total_steps", 0)
        if ts > 0:
            msgs.append(f"⚠️ {ts}건 처리됐는데 events 0 — 원격 bastion 이 새 코드 안 도는 가능성 (재확인)")

    return msgs


def main():
    cur = measure()
    prev = {}
    if BASELINE_FILE.exists():
        try:
            prev = json.loads(BASELINE_FILE.read_text())
        except Exception:
            prev = {}
    diag = diagnose(prev, cur)

    # 보고서 작성
    lines = [
        f"# Phase 5 Monitor — {cur['ts']}",
        "",
        "## 진단",
        *[f"- {m}" for m in diag],
        "",
        "## 현재 측정",
        f"- Asset 노드: **{cur.get('asset_count', '?')}** (kinds={cur.get('asset_kinds', {})})",
        f"- History anchors: **{cur.get('anchors', '?')}** · events: **{cur.get('events', '?')}** · 최근 2h events: **{cur.get('events_recent', '?')}** · narratives: **{cur.get('narratives', '?')}**",
        f"- KPI history depth: {cur.get('kpi_history_depth', {})}",
        f"- KPI latest: {cur.get('kpi_latest', {})}",
        "",
        "## run.log 누적 마커",
        f"- `asset_autoregistered` 이벤트: **{cur.get('log_asset_autoregistered', 0)}**",
        f"- `repeat_ioc_match` 이벤트: **{cur.get('log_repeat_ioc_match', 0)}**",
        f"- probe 계열 skill 실행: **{cur.get('log_probe_skill', 0)}** / 전체 steps: **{cur.get('log_total_steps', 0)}**",
        "",
        "## 이전 측정과의 차이",
        f"- Asset Δ: {cur.get('asset_count', 0) - prev.get('asset_count', 0):+d}" if prev else "- (baseline 없음 — 다음 사이클부터 비교)",
    ]
    if prev:
        lines.append(f"- Anchors Δ: {cur.get('anchors', 0) - prev.get('anchors', 0):+d}")
        lines.append(f"- Events Δ: {cur.get('events', 0) - prev.get('events', 0):+d}")
        lines.append(f"- Steps Δ: {cur.get('log_total_steps', 0) - prev.get('log_total_steps', 0):+d}")
    OUT_REPORT.write_text("\n".join(lines))

    # baseline 갱신
    BASELINE_FILE.write_text(json.dumps(cur, indent=2, ensure_ascii=False))

    # 콘솔 한줄 요약
    print(f"phase5: assets={cur.get('asset_count')}, kpi_depth={cur.get('kpi_history_depth', {})}, "
          f"anchors={cur.get('anchors')}, events={cur.get('events')}; "
          f"new: ar={cur.get('log_asset_autoregistered',0)}, irm={cur.get('log_repeat_ioc_match',0)}")
    for m in diag:
        print(f"  {m}")


if __name__ == "__main__":
    main()
