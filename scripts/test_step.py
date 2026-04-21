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


def llm_auto_hitl_answer(step: dict, question: str, bastion_context: str) -> str:
    """자동 HITL — Claude Code(Master) 역할의 얕은·간단한 답변 생성.

    원칙 (사용자 지침):
      - **human 수준으로, 간단히** (1-2 문장)
      - 정답을 알려주는 게 아님 — 답을 맞추는데 개입하지 않음
      - **얕은 수준**에서 질문에 답하고 오류를 지적
      - 예: "그 명령 써보세요", "타겟 IP 바꿔보세요", "연결 안 되면 방화벽 확인"
      - answer_detail / acceptable_methods / semantic 사용 금지 — 공개 정보(instruction, target_vm, category)만
    """
    instruction = step.get("instruction", "")
    category = step.get("category", "")
    target = step.get("target_vm", "")
    prompt = (
        "너는 보안 엔지니어 동료다. AI 에이전트(Bastion)가 실습 중 막혀서 물어봤다. "
        "너는 **얕은 수준에서 간단히** 답해라. 정답을 찍어주지 말고, 사람처럼 한두 문장으로 힌트를 주거나 오류를 지적해라.\n"
        "- OK: '그 명령 써보세요', '타겟 IP가 맞나요?', '방화벽 정책을 확인해보세요', '권한 문제 같은데 sudo 붙여보세요'\n"
        "- NOT OK: 긴 해설, 완전한 명령/코드, 정답이 될 수 있는 지식\n\n"
        f"[대상 VM] {target}   [카테고리] {category}\n"
        f"[공개 실습 지시]\n{instruction[:400]}\n\n"
        f"[에이전트 질문]\n{question}\n\n"
        f"[에이전트가 낸 응답 일부 (마지막 300자)]\n{(bastion_context or '')[-300:]}\n\n"
        'JSON 만 출력 (코드블록 금지): {"answer": "1-2 문장의 얕은 힌트나 오류 지적"}'
    )
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/chat",
            data=json.dumps({
                "model": JUDGE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3, "num_predict": 400},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
        content = body.get("message", {}).get("content", "")
        if not content:
            return ""
        parsed = json.loads(content)
        ans = str(parsed.get("answer", "")).strip()
        # 길이 가드 — 150자 이상이면 잘라냄 (human 수준 강제)
        if len(ans) > 200:
            ans = ans[:200].rsplit(' ', 1)[0] + '...'
        return ans
    except Exception:
        return ""


def llm_semantic_judge(step: dict, answer: str) -> tuple[bool, str]:
    """LLM으로 '응답이 step 의도를 적절히 수행했는지' 판정.

    step.verify.semantic (optional, Master가 기술) 을 우선 사용:
      { intent, success_criteria[], acceptable_methods[], negative_signs[] }
    없으면 step.instruction fallback.

    반환: (pass 여부, 응답에서 뽑은 대표 keyword)
    """
    intent = step.get("instruction", "") or step.get("bastion_prompt", "")
    answer_trim = (answer or "")[-2500:]
    if not intent or not answer_trim.strip():
        return False, ""
    verify = step.get("verify") or {}
    sem = verify.get("semantic") or {}
    sem_intent = sem.get("intent", "")
    sem_success = sem.get("success_criteria") or []
    sem_methods = sem.get("acceptable_methods") or []
    sem_negative = sem.get("negative_signs") or []
    expects = verify.get("expect") or []
    if isinstance(expects, str):
        expects = [expects]
    parts = [
        "너는 보안 실습의 엄정한 채점관이다. 학생이 실습 스텝을 수행한 결과(Bastion 자동 실행 응답)를 평가한다.",
        "아래 형식의 JSON 만 출력하라(코드블록/설명 문장 금지):",
        '{"pass": true|false, "keyword": "응답에서 핵심을 대표하는 단어(한/영)", "reason": "한문장 이유"}',
        "",
        f"## 실습 스텝 instruction\n{intent}",
    ]
    if sem_intent:
        parts.append(f"\n## 의도(intent) — Master 기술\n{sem_intent}")
    if sem_success:
        parts.append("\n## 합격 기준(success_criteria) — 하나 이상 충족해야 pass")
        parts.extend(f"- {c}" for c in sem_success)
    if sem_methods:
        parts.append("\n## 허용 방법(acceptable_methods) — 이 중 아무 방법이라도 인정")
        parts.extend(f"- {m}" for m in sem_methods)
    if sem_negative:
        parts.append("\n## 불합격 신호(negative_signs)")
        parts.extend(f"- {n}" for n in sem_negative)
    if expects:
        parts.append("\n## 기대 키워드(expect) — 토픽 힌트, 정확 매치는 필수 아님")
        parts.append(", ".join(expects[:10]))
    parts.append(f"\n## 학생 응답 (끝 2500자)\n{answer_trim}")
    parts.append(
        "\n## 판정 규칙\n"
        "- success_criteria 중 하나 이상을 충족했거나, acceptable_methods 중 하나의 의도/방법이 응답에 드러나면 pass=true.\n"
        "- 응답이 전혀 다른 주제를 다루거나 negative_signs에 해당하면 pass=false.\n"
        "- 단순 무응답/에러 텍스트/도구 실행 실패는 pass=false.\n"
        "- 의도와 방법이 동일하면 출력 형식이 기대와 달라도 pass=true (예: JSON 대신 표, 영어 키워드 대신 한국어 설명)."
    )
    prompt = "\n".join(parts)
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/chat",
            data=json.dumps({
                "model": JUDGE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 800},
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
    ap.add_argument("--auto-hitl", action="store_true",
                    help="자동 HITL — ask_user 이벤트 시 LLM 이 instruction·category 기반으로 답변 생성 (answer_detail·acceptable_methods 사용 금지, 데이터 유출 방지)")
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

    # w22 HITL (interactive) / w27 auto-HITL: ask_user 이벤트 시 답변 받아 follow-up 호출
    if (args.ask or args.auto_hitl) and events:
        ask_evt = next((e for e in events if e.get("event") == "ask_user"), None)
        if ask_evt:
            question = ask_evt.get("question", "")
            context = ask_evt.get("context", "")
            print("\n" + "=" * 70)
            print(f"[ASK_USER] {question}")
            if context:
                print(f"\n[Bastion context, last 500c]:\n{context}")
            print("=" * 70)
            user_answer = ""
            if args.auto_hitl:
                # LLM 이 instruction·category 기반으로 답변 생성 (answer_detail 사용 금지)
                user_answer = llm_auto_hitl_answer(step, question, context)
                print(f"[AUTO-HITL LLM 답변] {user_answer!r}")
            else:
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
                # 2nd call: 답변을 새 message로 보냄 (history 유지)
                print(f"\n[follow-up → Bastion]: {user_answer}")
                fu_step = dict(step)
                fu_step["bastion_prompt"] = user_answer
                fu_step["instruction"] = user_answer
                fu_events, fu_elapsed, fu_err = call_bastion(fu_step, args.course, lab_id)
                if not fu_err:
                    # 원 이벤트 + 구분자 + follow-up 이벤트
                    events = events + [{"event": "hitl_followup", "auto": args.auto_hitl}] + fu_events
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
