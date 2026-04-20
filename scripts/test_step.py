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
OLLAMA = "http://192.168.0.105:11434"
JUDGE_MODEL = "gpt-oss:120b"
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


def llm_semantic_judge(step: dict, answer: str) -> tuple[bool, str]:
    """LLM으로 '응답이 step 의도를 적절히 수행했는지' 판정.

    반환: (pass 여부, 응답에서 뽑은 대표 keyword)
    """
    intent = step.get("instruction", "") or step.get("bastion_prompt", "")
    answer_trim = (answer or "")[-1500:]
    if not intent or not answer_trim.strip():
        return False, ""
    prompt = (
        "너는 보안 실습 채점관이다. 학생이 실습 스텝을 수행한 결과를 평가한다.\n"
        "아래 형식의 JSON 만 출력하라(코드블록 금지):\n"
        '{"pass": true|false, "keyword": "응답에서 핵심을 대표하는 한 단어(한글/영문 가능)", "reason": "간단한 이유"}\n\n'
        f"실습 의도:\n{intent}\n\n"
        f"학생(Bastion) 응답:\n{answer_trim}\n\n"
        "기준: 응답이 의도한 작업을 수행·설명했고 현저한 오류가 없으면 pass=true. "
        "한두 단어 수준의 키워드는 의도와 합치하면 인정. 엉뚱한 주제/에러/무응답은 pass=false."
    )
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/chat",
            data=json.dumps({
                "model": JUDGE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 120},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            body = json.loads(r.read())
        content = body.get("message", {}).get("content", "")
        parsed = json.loads(content)
        return bool(parsed.get("pass")), str(parsed.get("keyword", "") or "").strip()
    except Exception:
        return False, ""


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
    skill_skips = [e for e in events if e.get("event") == "skill_skip"]
    precheck_fails = [e for e in events if e.get("event") == "precheck_fail"]
    pb_starts = [e for e in events if e.get("event") == "playbook_start"]
    step_dones = [e for e in events if e.get("event") == "step_done"]
    pb_dones = [e for e in events if e.get("event") == "playbook_done"]
    tokens = [e.get("token", "") for e in events if e.get("event") == "stream_token"]
    full_text = "".join(tokens)
    # aggregate skill + playbook outputs
    out_chunks = [full_text]
    for r in skill_results:
        # skill_result 는 top-level 에 output/stdout/stderr 을 가진다
        out_chunks.append(str(r.get("output", "")))
        out_chunks.append(str(r.get("stdout", "")))
        out_chunks.append(str(r.get("stderr", "")))
        # 드물게 result 서브딕트인 경우도 방어적으로 처리
        nested = r.get("result")
        if isinstance(nested, dict):
            out_chunks.append(str(nested.get("stdout", "")))
            out_chunks.append(str(nested.get("output", "")))
    for sd in step_dones:
        out_chunks.append(str(sd.get("output", "")))
    aggregated = "\n".join(c for c in out_chunks if c)
    # Bastion이 실행을 시도했으면 executed=True (skill_skip·precheck_fail 포함 — 이는 인프라 문제로
    # skill이 실제 실행은 못 했지만 Bastion은 plan/precheck까지 수행한 상태. no_execution(Bastion 무응답)과 구분)
    executed = bool(skill_starts) or bool(pb_starts) or bool(step_dones) or bool(skill_skips) or bool(precheck_fails)

    verify = step.get("verify") or {}
    vtype = verify.get("type")
    expect = verify.get("expect", "")
    # expect can be str OR list of acceptable alternatives
    expects = expect if isinstance(expect, list) else ([expect] if expect else [])
    expects = [str(e) for e in expects if str(e).strip()]

    def _any_contains(needles: list[str]) -> bool:
        low = aggregated.lower()
        return any(n.lower() in low for n in needles)

    match = False
    if vtype == "output_contains":
        match = bool(expects) and _any_contains(expects)
    elif vtype == "output_regex":
        match = bool(expects) and any(
            re.search(e, aggregated, re.IGNORECASE) is not None for e in expects
        )
    elif vtype == "exit_code_zero":
        match = any(
            (r.get("result", {}) or {}).get("exit_code") == 0 for r in skill_results
        )
    else:
        match = bool(expects) and _any_contains(expects)

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
            # 리터럴 매치 실패 → LLM 세맨틱 판정
            sem_ok, sem_kw = llm_semantic_judge(step, aggregated)
            meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw}
            if sem_ok:
                meta["_semantic_pass_keyword"] = sem_kw
                return "pass", "qa", meta
            return "qa_fallback", "", meta
        return "no_execution", "", meta
    # 실행됨: verify 매치 우선
    if match:
        skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
        return "pass", skill, meta
    # expect가 비어 있으면 실행 성공만으로 pass 인정
    if not expects:
        skill_ok = any(r.get("success") for r in skill_results) if skill_results else pb_ok
        if skill_ok:
            skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
            return "pass", skill, meta
    # 리터럴 매치 실패 → LLM 세맨틱 판정 폴백
    sem_ok, sem_kw = llm_semantic_judge(step, aggregated)
    meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw}
    if sem_ok:
        skill = (skill_starts[0].get("skill") if skill_starts else ("playbook" if pb_starts else "qa"))
        meta["_semantic_pass_keyword"] = sem_kw
        return "pass", skill or "qa", meta
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


def _augment_verify_expect(course: str, week: int, order: int, new_kw: str):
    """semantic pass 시 YAML verify.expect 에 새 키워드를 누적.

    - 기존이 str 이면 list 로 승격 [old, new]
    - list 이면 append (중복 제외)
    - 같은 step 의 non-ai 짝도 동기화
    """
    if not new_kw:
        return
    for variant in ("ai", "nonai"):
        path = ROOT / "contents" / "labs" / f"{course.replace('-ai','')}-{variant}" / f"week{week:02d}.yaml"
        if not path.exists():
            continue
        try:
            y = yaml.safe_load(open(path))
        except Exception:
            continue
        changed = False
        for s in y.get("steps", []):
            if s.get("order") != order:
                continue
            v = s.get("verify") or {}
            if v.get("type") not in ("output_contains", None):
                continue
            cur = v.get("expect", "")
            if isinstance(cur, list):
                lst = list(cur)
            elif cur:
                lst = [cur]
            else:
                lst = []
            if new_kw not in lst:
                lst.append(new_kw)
                v["expect"] = lst
                s["verify"] = v
                changed = True
        if changed:
            yaml.safe_dump(y, open(path, "w"), allow_unicode=True,
                           sort_keys=False, default_flow_style=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course")
    ap.add_argument("week", type=int)
    ap.add_argument("order", type=int)
    ap.add_argument("--dry", action="store_true", help="don't update progress.json")
    ap.add_argument("--no-augment", action="store_true", help="semantic pass 시 YAML 업데이트 금지")
    ap.add_argument("--ask", action="store_true",
                    help="인터랙티브 HITL 모드 — ask_user 이벤트 시 stdin에서 답변 대기")
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

    # w22 HITL: ask_user 이벤트 시 stdin에서 사람 답변 받아 follow-up 호출
    if args.ask and events:
        ask_evt = next((e for e in events if e.get("event") == "ask_user"), None)
        if ask_evt:
            print("\n" + "=" * 70)
            print(f"[ASK_USER] {ask_evt.get('question', '')}")
            if ask_evt.get("context"):
                print(f"\n[Bastion context, last 500c]:\n{ask_evt['context']}")
            print("=" * 70)
            print("사람처럼 답변 입력 (빈 줄 입력으로 완료, 'skip'으로 포기):")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line == "":
                    break
                lines.append(line)
            user_answer = "\n".join(lines).strip()
            if user_answer and user_answer.lower() != "skip":
                # 2nd call: 사람 답변을 새 message로 보냄 (history 유지)
                print(f"\n[follow-up → Bastion]: {user_answer}")
                fu_step = dict(step)
                fu_step["bastion_prompt"] = user_answer
                fu_step["instruction"] = user_answer
                fu_events, fu_elapsed, fu_err = call_bastion(fu_step, args.course, lab_id)
                if not fu_err:
                    # 원 이벤트 + 구분자 + follow-up 이벤트
                    events = events + [{"event": "hitl_followup"}] + fu_events
                    elapsed += fu_elapsed
                    print(f"follow-up {len(fu_events)} events, +{fu_elapsed:.1f}s")

    if err:
        print(f"ERROR: {err} (elapsed {elapsed:.1f}s)")
        status, skill, meta = "error", "", {}
    else:
        status, skill, meta = judge(events, step)
        print(f"stages={meta['stages']}  skills={meta['skill_names']}  verify_match={meta['verify_match']}")
        print(f"── answer tail ──\n{meta['answer_tail']}")

    print("─" * 70)
    print(f"VERDICT: {status}  skill={skill}  elapsed={elapsed:.1f}s")

    # 세맨틱 pass 시 verify.expect 누적 (YAML 자동 확장)
    if not args.no_augment and status == "pass" and not err:
        meta_dict = locals().get("meta", {})
        kw = (meta_dict or {}).get("_semantic_pass_keyword", "")
        if kw:
            _augment_verify_expect(args.course, args.week, args.order, kw)
            print(f"verify.expect augmented with: {kw!r}")

    if not args.dry:
        is_new, completed, passed = update_progress(
            args.course, args.week, args.order, status, skill, elapsed
        )
        print(f"progress: {completed}/2570 pass={passed} (new={is_new})")


if __name__ == "__main__":
    main()
