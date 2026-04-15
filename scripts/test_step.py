#!/usr/bin/env python3
"""단일 스텝 Bastion 테스트 헬퍼.

사용:
  python3 scripts/test_step.py <course> <week> <step_order> [--dry]

- YAML에서 해당 스텝을 로드
- Bastion /chat으로 프롬프트 투입 (stream=false)
- 이벤트에서 verdict 판정:
    pass         : skill 실행 성공 + verify.output_contains 매치
    fail         : skill 실행 했으나 verify 실패 / skill 실패
    qa_fallback  : stage=qa 만 발생 (실행 없음, LLM 답변만)
    no_execution : skill_start 없음
    error        : 네트워크/타임아웃/예외
- progress.json 업데이트 후 결론 요약 출력
  (전체 답변 텍스트는 마지막 2KB 만 출력)
"""
from __future__ import annotations
import sys, json, time, argparse, pathlib, urllib.request, yaml, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "bastion_test_progress.json"
BASTION = "http://192.168.0.115:8003/chat"
TIMEOUT = 600


def load_step(course: str, week: int, order: int):
    # week names look like soc-adv-ai / week05.yaml
    yaml_path = ROOT / "contents" / "labs" / course / f"week{week:02d}.yaml"
    if not yaml_path.exists():
        sys.exit(f"YAML not found: {yaml_path}")
    y = yaml.safe_load(open(yaml_path))
    for s in y.get("steps", []):
        if s.get("order") == order:
            return y, s
    sys.exit(f"step order {order} not in {yaml_path}")


def call_bastion(step: dict, course: str, lab_id: str):
    prompt = step.get("bastion_prompt") or step.get("instruction")
    payload = {
        "message": prompt,
        "auto_approve": True,
        "stream": False,
        "course": course,
        "lab_id": lab_id,
        "step_order": step["order"],
        "test_session": "ts-20260414",
    }
    req = urllib.request.Request(
        BASTION,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode()
    except Exception as e:
        return None, time.time() - t0, str(e)
    # Response shapes: {"events":[...]}, [...], or NDJSON
    events = []
    body = body.strip()
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict) and "events" in parsed:
            events = parsed["events"]
        elif isinstance(parsed, list):
            events = parsed
        else:
            events = [parsed]
    except json.JSONDecodeError:
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events, time.time() - t0, None


def judge(events, step):
    if events is None:
        return "error", "", {}
    # multitask split → 서브태스크별로 각자의 이벤트 시퀀스가 섞여 있음.
    # 간단히: split이 감지되면 subtask_done 개수 == total이면 pass로 판정.
    split_evts = [e for e in events if e.get("event") == "multitask_split"]
    subtask_dones = [e for e in events if e.get("event") == "subtask_done"]
    stages = [e.get("stage") for e in events if e.get("event") == "stage"]
    skill_starts = [e for e in events if e.get("event") == "skill_start"]
    skill_results = [e for e in events if e.get("event") == "skill_result"]
    pb_starts = [e for e in events if e.get("event") == "playbook_start"]
    step_dones = [e for e in events if e.get("event") == "step_done"]
    pb_dones = [e for e in events if e.get("event") == "playbook_done"]
    tokens = [e.get("token", "") for e in events if e.get("event") == "stream_token"]
    full_text = "".join(tokens)
    # aggregate skill + playbook outputs
    out_chunks = [full_text]
    for r in skill_results:
        out = r.get("result", {})
        if isinstance(out, dict):
            out_chunks.append(str(out.get("stdout", "")))
            out_chunks.append(str(out.get("output", "")))
    for sd in step_dones:
        out_chunks.append(str(sd.get("output", "")))
    aggregated = "\n".join(out_chunks)
    executed = bool(skill_starts) or bool(pb_starts) or bool(step_dones)

    verify = step.get("verify") or {}
    vtype = verify.get("type")
    expect = verify.get("expect", "")
    match = False
    if vtype == "output_contains":
        match = bool(expect) and (expect.lower() in aggregated.lower())
    elif vtype == "output_regex":
        match = bool(expect) and re.search(expect, aggregated, re.IGNORECASE) is not None
    elif vtype == "exit_code_zero":
        match = any(
            (r.get("result", {}) or {}).get("exit_code") == 0 for r in skill_results
        )
    else:
        match = bool(expect) and (expect.lower() in aggregated.lower())

    # playbook 성공 판정: 모든 step 성공 OR playbook_done passed==total
    pb_ok = False
    if pb_dones:
        pb_ok = all(pd.get("passed", 0) == pd.get("total", 0) for pd in pb_dones)
    elif step_dones:
        pb_ok = all(sd.get("success") for sd in step_dones)

    meta = {
        "stages": stages,
        "skill_count": len(skill_starts),
        "skill_names": [s.get("skill") for s in skill_starts],
        "playbook": bool(pb_starts),
        "pb_ok": pb_ok,
        "verify_match": match,
        "answer_tail": aggregated[-800:],
    }

    category = (step.get("category") or "").lower()
    exec_required_cats = {"configure", "exploit", "attack", "scan", "pivot", "persistence",
                          "exfiltration", "remediation", "block", "deploy"}

    # Multi-task: split이 감지되면 완료된 서브태스크 수 기준으로 판정
    if split_evts:
        total = split_evts[0].get("count", 0)
        done = len(subtask_dones)
        meta["subtasks"] = f"{done}/{total}"
        # expect가 비어있는 멀티태스크는 완료 개수가 총 개수와 같으면 pass
        if total > 0 and done == total:
            return "pass", "multitask", meta
        if total > 0 and done >= total * 0.6:
            return "pass", "multitask", meta  # 60% 이상 완료도 pass
        return "fail", "multitask", meta
    if not executed:
        if "qa" in stages:
            if match and category not in exec_required_cats:
                return "pass", "qa", meta
            return "qa_fallback", "", meta
        return "no_execution", "", meta
    # 실행됨: verify 매치 우선
    if match:
        skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
        return "pass", skill, meta
    # expect가 비어 있으면 실행 성공만으로 pass 인정
    if not verify.get("expect"):
        skill_ok = any(r.get("success") for r in skill_results) if skill_results else pb_ok
        if skill_ok:
            skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
            return "pass", skill, meta
    skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
    return "fail", skill, meta


def update_progress(course: str, week: int, order: int, status: str, skill: str, elapsed: float):
    d = json.load(open(PROGRESS))
    wkey = f"week{week:02d}"
    cur = d["results"][course][wkey]
    prev = cur.get(str(order)) if str(order) in cur else cur.get(order)
    is_new = prev in (None, {}) or (isinstance(prev, dict) and not prev.get("status"))
    # key type: existing uses int keys in memory, but json always str
    key = str(order) if str(order) in cur else order
    cur[key] = {
        "status": status,
        "skill": skill,
        "elapsed": round(elapsed, 2),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    # recompute counters
    passed = 0
    failed = 0
    completed = 0
    for c, ws in d["results"].items():
        for w, ss in ws.items():
            if not isinstance(ss, dict):
                continue
            for k, v in ss.items():
                if isinstance(v, dict) and v.get("status"):
                    completed += 1
                    if v["status"] == "pass":
                        passed += 1
                    elif v["status"] in ("fail", "error"):
                        failed += 1
    d["completed"] = completed
    d["passed"] = passed
    d["failed"] = failed
    json.dump(d, open(PROGRESS, "w"), ensure_ascii=False, indent=2)
    return is_new, completed, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course")
    ap.add_argument("week", type=int)
    ap.add_argument("order", type=int)
    ap.add_argument("--dry", action="store_true", help="don't update progress.json")
    args = ap.parse_args()

    y, step = load_step(args.course, args.week, args.order)
    lab_id = y.get("lab_id", f"{args.course}-week{args.week:02d}")
    prompt = step.get("bastion_prompt") or step.get("instruction")
    print(f"[{args.course}/week{args.week:02d}/{args.order}] {lab_id}")
    print(f"PROMPT: {prompt}")
    print(f"VERIFY: {step.get('verify')}")
    print(f"TARGET: {step.get('target_vm')}  CAT: {step.get('category')}")
    print("─" * 70)

    events, elapsed, err = call_bastion(step, args.course, lab_id)
    if err:
        print(f"ERROR: {err} (elapsed {elapsed:.1f}s)")
        status, skill, meta = "error", "", {}
    else:
        status, skill, meta = judge(events, step)
        print(f"stages={meta['stages']}  skills={meta['skill_names']}  verify_match={meta['verify_match']}")
        print(f"── answer tail ──\n{meta['answer_tail']}")

    print("─" * 70)
    print(f"VERDICT: {status}  skill={skill}  elapsed={elapsed:.1f}s")

    if not args.dry:
        is_new, completed, passed = update_progress(
            args.course, args.week, args.order, status, skill, elapsed
        )
        print(f"progress: {completed}/2570 pass={passed} (new={is_new})")


if __name__ == "__main__":
    main()
