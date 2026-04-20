#!/usr/bin/env python3
"""자동 생성된 battle/lab YAML을 Bastion 실증 검증.

대상:
- contents/labs/battle-auto/*.yaml
- contents/education/<course>/latest-threats/<CVE>/lab.yaml

각 step을 Bastion /chat에 전송해 verdict 수집.
결과: bastion_autogen_test.json

실행:
    python3 scripts/test_autogen.py --battle-auto
    python3 scripts/test_autogen.py --latest-threats
    python3 scripts/test_autogen.py --file path/to/lab.yaml
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASTION = os.getenv("BASTION_URL", "http://192.168.0.115:8003/chat")
OLLAMA = os.getenv("LLM_BASE_URL", "http://192.168.0.105:11434")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-oss:120b")
PROGRESS = ROOT / "bastion_autogen_test.json"


def _load_progress() -> dict:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text())
        except Exception:
            pass
    return {"labs": {}}


def _save_progress(d: dict):
    PROGRESS.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def call_bastion(prompt: str, lab_id: str, step_order: int, course: str) -> tuple[list, float]:
    payload = {
        "message": prompt, "auto_approve": True, "stream": False,
        "course": course, "lab_id": lab_id, "step_order": step_order,
        "test_session": "autogen",
    }
    req = urllib.request.Request(
        BASTION, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode()
    except Exception as e:
        return [{"event": "error", "msg": str(e)[:200]}], time.time() - t0
    try:
        d = json.loads(body)
        events = d.get("events") if isinstance(d, dict) and "events" in d else d
    except json.JSONDecodeError:
        events = []
        for ln in body.splitlines():
            try:
                events.append(json.loads(ln))
            except Exception:
                pass
    return events, time.time() - t0


def judge(events: list, step: dict) -> str:
    if not events:
        return "error"
    stages = [e.get("stage") for e in events if e.get("event") == "stage"]
    skill_starts = [e for e in events if e.get("event") == "skill_start"]
    skill_results = [e for e in events if e.get("event") == "skill_result"]
    skill_skips = [e for e in events if e.get("event") == "skill_skip"]
    precheck_fails = [e for e in events if e.get("event") == "precheck_fail"]
    tokens = "".join(e.get("token", "") for e in events if e.get("event") == "stream_token")
    agg = tokens
    for r in skill_results:
        agg += "\n" + str(r.get("output", "")) + "\n" + str(r.get("stdout", ""))
    executed = bool(skill_starts) or bool(skill_skips) or bool(precheck_fails)
    expect = (step.get("verify") or {}).get("expect", "")
    expects = expect if isinstance(expect, list) else ([expect] if expect else [])
    match = any(str(e).lower() in agg.lower() for e in expects if str(e).strip())
    if match and executed:
        return "pass"
    if match:
        return "pass-qa"
    if executed:
        return "fail"
    if "qa" in stages:
        return "qa_fallback"
    return "no_execution"


def test_lab_file(path: pathlib.Path, progress: dict) -> dict:
    import yaml as _y
    try:
        data = _y.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"path": str(path), "error": f"YAML 파싱 실패: {e}"}
    lab_id = data.get("lab_id", path.stem)
    course = data.get("course", "auto")
    steps = data.get("steps") or []
    print(f"\n=== {lab_id} ({len(steps)} steps) ===", flush=True)
    lab_result = {"lab_id": lab_id, "path": str(path.relative_to(ROOT)),
                  "steps": [], "summary": {}}
    import collections
    ct = collections.Counter()
    for step in steps:
        order = step.get("order", 0)
        prompt = step.get("bastion_prompt") or step.get("instruction") or ""
        if not prompt:
            continue
        events, el = call_bastion(prompt, lab_id, order, course)
        verdict = judge(events, step)
        ct[verdict] += 1
        lab_result["steps"].append({"order": order, "verdict": verdict, "elapsed": round(el, 1)})
        print(f"  step {order}: {verdict} ({el:.1f}s)", flush=True)
    lab_result["summary"] = dict(ct)
    progress["labs"][lab_id] = lab_result
    _save_progress(progress)
    return lab_result


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--battle-auto", action="store_true")
    g.add_argument("--latest-threats", action="store_true")
    g.add_argument("--file")
    args = ap.parse_args()

    progress = _load_progress()
    targets: list[pathlib.Path] = []
    if args.battle_auto:
        battle_dir = ROOT / "contents" / "labs" / "battle-auto"
        targets = sorted(battle_dir.glob("*.yaml"))
    elif args.latest_threats:
        for p in (ROOT / "contents" / "education").glob("*/latest-threats/*/lab.yaml"):
            targets.append(p)
    elif args.file:
        targets = [pathlib.Path(args.file)]

    if not targets:
        print("[ERR] 대상 없음", file=sys.stderr)
        sys.exit(1)
    print(f"[autogen-test] {len(targets)}개 YAML 검증 시작")
    for p in targets:
        test_lab_file(p, progress)

    # 총 요약
    total = collections.Counter()
    import collections  # re-import for scope
    for lab in progress["labs"].values():
        for k, v in (lab.get("summary") or {}).items():
            total[k] += v
    print(f"\n=== 전체 요약 ===")
    print(dict(total))
    total_steps = sum(total.values())
    if total_steps:
        print(f"pass율: {100*total['pass']/total_steps:.1f}% · 실행율(pass+fail): {100*(total['pass']+total['fail'])/total_steps:.1f}%")


if __name__ == "__main__":
    main()
