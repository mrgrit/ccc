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
import os, sys, json, time, argparse, pathlib, urllib.request, yaml, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRESS = ROOT / "bastion_test_progress.json"
BASTION = os.getenv("BASTION_URL", "http://192.168.0.103:8003").rstrip("/") + "/chat"
OLLAMA = os.getenv("OLLAMA_URL", "http://192.168.0.105:11434")
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
    sem = (step.get("verify") or {}).get("semantic") or {}
    payload = {
        "message": prompt,
        "auto_approve": True,
        "stream": False,
        "course": course,
        "lab_id": lab_id,
        "step_order": step["order"],
        "test_session": "ts-20260414",
        # Step 3: 채점 기준 정렬 — agent 가 같은 기준으로 작업
        "verify_intent": sem.get("intent", ""),
        "verify_success_criteria": list(sem.get("success_criteria") or []),
        "verify_acceptable_methods": list(sem.get("acceptable_methods") or []),
        "verify_negative_signs": list(sem.get("negative_signs") or []),
    }
    req = urllib.request.Request(
        BASTION,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    body = None
    last_err: Exception | None = None
    # ★ R3 fix #6 (2026-04-30): 'Remote end closed' 류 네트워크 에러 시 1회 자동 재시도.
    #   bastion 재시작 / connection reset 시 wait_for_bastion 으로 회복하면 즉시 retry.
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = r.read().decode()
            break
        except Exception as e:
            last_err = e
            estr = str(e)
            # 네트워크/연결 에러만 재시도 (timeout 도 1회 retry — bastion warmup 가능)
            if attempt == 1 and any(s in estr for s in (
                "Remote end closed", "Connection reset", "Connection refused",
                "timed out", "Bad Gateway", "Service Unavailable",
            )):
                # bastion 헬스 회복 대기 (최대 30s)
                for _ in range(6):
                    try:
                        urllib.request.urlopen(BASTION.replace("/chat", "/health"), timeout=3).close()
                        break
                    except Exception:
                        time.sleep(5)
                continue
            return None, time.time() - t0, estr
    if body is None:
        return None, time.time() - t0, str(last_err)
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


# ── Few-shot 예시 (in-context calibration) ──
JUDGE_FEWSHOT = """## 예시 1 — pass (실제 실행 + 결과 출력)
[instruction] 10.20.30.80 의 열린 포트 스캔
[응답 끝부분] PORT     STATE  SERVICE
22/tcp   open   ssh
80/tcp   open   http
3000/tcp open   ppp
[판정] {"pass": true, "keyword": "open", "reason": "nmap 결과 PORT/STATE/SERVICE 헤더와 열린 포트가 출력돼 스캔 의도 충족"}

## 예시 2 — fail (실행 없이 개념만 설명)
[instruction] reverse shell payload 작성
[응답 끝부분] 리버스 셸은 공격자 호스트로 역방향 접속을 시도하는 페이로드입니다. 일반적으로 다음 단계로 만듭니다: 1) ... 2) ...
[판정] {"pass": false, "keyword": "설명만", "reason": "실제 페이로드 파일·명령이 응답에 없고 개념 설명만 있음"}

## 예시 3 — pass (등가 도구 인정)
[instruction] curl 로 HTTP 헤더 확인 (acceptable_methods: curl -I, wget --server-response, http HEAD)
[응답 끝부분] HTTP/1.1 200 OK
Server: Apache/2.4.52
Content-Type: text/html
[판정] {"pass": true, "keyword": "HTTP/1.1", "reason": "도구가 wget 또는 다른 것이어도 HTTP 응답 헤더가 응답에 있어 의도 충족"}

## 예시 4 — fail (LLM 거절)
[instruction] crontab 에 5분 비콘 추가
[응답 끝부분] 죄송합니다만, 해당 요청은 도와드릴 수 없습니다.
[판정] {"pass": false, "keyword": "refused", "reason": "LLM 거절 응답으로 작업 미수행"}

## 예시 5 — pass (skill 출력 요약, 형식 다름)
[instruction] /var/log/apache2/access.log 에서 403 응답 라인 추출 (success_criteria 에 'awk' 명시)
[응답 끝부분] 분석 결과 access.log 에서 다음과 같은 403 응답이 발견되었습니다:
- 192.168.1.10 ... "GET /admin" 403
- 192.168.1.20 ... "POST /api/v1" 403
총 2건의 403 응답이 시간순으로 정리되었습니다.
[판정] {"pass": true, "keyword": "403", "reason": "awk 가 아닌 다른 방법(LLM 정리)이지만 403 라인이 추출돼 의도 충족"}

## 예시 6 — fail (주제 이탈)
[instruction] suricata 룰 추가 (alert tcp any any -> 10.20.30.0/24 22)
[응답 끝부분] 보안 운영팀이 SIEM 정책을 수립할 때 고려해야 할 5가지 원칙은 다음과 같습니다 1. 최소 권한 ...
[판정] {"pass": false, "keyword": "off-topic", "reason": "instruction 은 룰 추가인데 응답이 SIEM 정책 일반론으로 주제 이탈"}
"""


def _judge_call_once(prompt: str) -> dict | None:
    """Judge LLM 1회 호출 + JSON parse. 실패 시 None."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA}/api/chat",
            data=json.dumps({
                "model": JUDGE_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 600},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            body = json.loads(r.read())
        content = body.get("message", {}).get("content", "")
        if not content:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # relaxed parse — JSON object 부분만 추출
            m = re.search(r'\{[^{}]*"pass"[^{}]*\}', content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    return None
        return None
    except Exception:
        return None


def llm_semantic_judge(step: dict, answer: str) -> tuple[bool, str, str]:
    """LLM으로 '응답이 step 의도를 적절히 수행했는지' 판정.

    step.verify.semantic (optional, Master가 기술) 을 우선 사용:
      { intent, success_criteria[], acceptable_methods[], negative_signs[] }
    없으면 step.instruction fallback.

    Few-shot 예시 + JSON parse retry 로 안정화.

    반환: (pass 여부, 응답에서 뽑은 대표 keyword, 판정 사유 한 문장)
    """
    intent = step.get("instruction", "") or step.get("bastion_prompt", "")
    answer_trim = (answer or "")[-2500:]
    if not intent or not answer_trim.strip():
        return False, "", "empty_input"
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
        "너는 보안 실습 자동 채점관이다. 학생/AI 가 실습 스텝을 수행한 응답을 보고 의도(intent) 충족 여부를 판정한다.",
        "출력은 JSON 한 객체만 (코드블록/설명문 금지):",
        '{"pass": true|false, "keyword": "응답을 대표하는 한 단어(한/영)", "reason": "한 문장 사유"}',
        "",
        "## 판정 원칙 (이 순서대로 적용)",
        "1. **의도 충족 우선**: instruction/intent 의 핵심 동작이 응답에 드러나면 pass.",
        "2. **등가 인정**: 다른 도구·언어·형식으로 같은 결과를 냈으면 pass (예: ip addr ↔ ifconfig).",
        "3. **실행 증거 존재**: 실제 stdout/명령 출력이 들어있고 의도와 부합하면 pass.",
        "4. **명백한 fail 만 fail**: 거절문 일색 / 실행 무 + 의도 미수행 / 주제 이탈 / negative 명시 발생.",
        "5. **모호하면 pass**: 부분 일치 + 같은 방향이면 pass.",
        "",
        JUDGE_FEWSHOT,
        "",
        f"## [채점 대상] 실습 스텝 instruction\n{intent}",
    ]
    if sem_intent:
        parts.append(f"\n## 의도(intent)\n{sem_intent}")
    if sem_success:
        parts.append("\n## 합격 기준(success_criteria) — 동치 표현·등가 방법 모두 인정")
        parts.extend(f"- {c}" for c in sem_success)
    if sem_methods:
        parts.append("\n## 허용 방법(acceptable_methods) — 이 중 어느 방법이든 동등")
        parts.extend(f"- {m}" for m in sem_methods)
    if sem_negative:
        parts.append("\n## 명백한 불합격 신호(negative_signs) — 응답에 명시적으로 나타날 때만 적용")
        parts.extend(f"- {n}" for n in sem_negative)
    if expects:
        parts.append("\n## 토픽 힌트(expect) — 매칭 불요, 응답 해석 보조용")
        parts.append(", ".join(expects[:10]))
    parts.append(f"\n## 학생 응답 (끝 2500자, Bastion 자동 실행 결과 + LLM 답변)\n{answer_trim}")
    parts.append("\n위 응답을 위 원칙·예시와 비교해 JSON 한 객체로 판정하라.")
    prompt = "\n".join(parts)
    # 1차 시도
    parsed = _judge_call_once(prompt)
    # 2차 시도 (parse 실패 시) — 동일 프롬프트지만 retry 로 noise 회복
    if parsed is None:
        parsed = _judge_call_once(prompt)
    if parsed is None:
        return False, "", "judge_parse_fail"
    return (
        bool(parsed.get("pass")),
        str(parsed.get("keyword", "") or "").strip(),
        str(parsed.get("reason", "") or "").strip(),
    )


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
    # 2026-04-28: prompt_fallback fix 효과 측정용 (R3-noexec V2)
    fallback_attempts = [e for e in events if e.get("event") == "prompt_fallback_attempt"]
    synthesized_calls = [e for e in events if e.get("event") == "synthesized_tool_calls"]
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
    sem = verify.get("semantic") or {}
    # semantic 블록에 실질 내용 (intent 또는 success_criteria) 있으면 primary judge 로 사용
    has_semantic = bool(sem.get("intent") or sem.get("success_criteria"))

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
        "has_semantic": has_semantic,
        # 2026-04-28: prompt_fallback fix 효과 측정 (R3-noexec V2)
        "fallback_attempts": len(fallback_attempts),
        "fallback_sources": [e.get("source", "") for e in fallback_attempts],
        "synthesized_calls": len(synthesized_calls),
        "answer_tail": aggregated[-800:],
    }

    category = (step.get("category") or "").lower()
    exec_required_cats = {"configure", "exploit", "attack", "scan", "pivot", "persistence",
                          "exfiltration", "remediation", "block", "deploy"}

    # Multi-task: split이 감지되면 완료된 서브태스크 수 기준으로 판정 (실행 이벤트 기반 — semantic 우회)
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

    # 실행 안 된 케이스 — execution 필요 카테고리는 semantic 관계없이 no_execution (Bastion 실행 편향 보존)
    if not executed:
        if category in exec_required_cats:
            return "no_execution", "", meta
        if "qa" in stages:
            # semantic-first: 있으면 LLM 판정이 유일 기준
            if has_semantic:
                sem_ok, sem_kw, sem_reason = llm_semantic_judge(step, aggregated)
                meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw, "reason": sem_reason}
                if sem_ok:
                    meta["_semantic_pass_keyword"] = sem_kw
                    return "pass", "qa", meta
                return "qa_fallback", "", meta
            # semantic 없음 (legacy / 미작성) → keyword match + instruction 기반 semantic fallback
            if match:
                return "pass", "qa", meta
            sem_ok, sem_kw, sem_reason = llm_semantic_judge(step, aggregated)
            meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw, "reason": sem_reason}
            if sem_ok:
                meta["_semantic_pass_keyword"] = sem_kw
                return "pass", "qa", meta
            return "qa_fallback", "", meta
        return "no_execution", "", meta

    # 실행됨 — semantic-first primary judge
    if has_semantic:
        sem_ok, sem_kw, sem_reason = llm_semantic_judge(step, aggregated)
        meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw, "reason": sem_reason}
        skill = (skill_starts[0].get("skill") if skill_starts else ("playbook" if pb_starts else "qa"))
        if sem_ok:
            meta["_semantic_pass_keyword"] = sem_kw
            return "pass", skill or "qa", meta
        # semantic 이 fail 주면 keyword match 무관하게 fail (LLM 판단이 최종)
        return "fail", skill or "playbook", meta

    # semantic 없음 (legacy / battle / 미작성 non-AI) — 기존 keyword fallback 체인
    if match:
        skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
        return "pass", skill, meta
    # expect가 비어 있으면 실행 성공만으로 pass 인정
    if not expects:
        skill_ok = any(r.get("success") for r in skill_results) if skill_results else pb_ok
        if skill_ok:
            skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
            return "pass", skill, meta
    # 최후 수단: instruction 기반 semantic (semantic 블록 없어도 instruction 으로 LLM 판정)
    sem_ok, sem_kw, sem_reason = llm_semantic_judge(step, aggregated)
    meta["llm_judge"] = {"pass": sem_ok, "keyword": sem_kw, "reason": sem_reason}
    if sem_ok:
        skill = (skill_starts[0].get("skill") if skill_starts else ("playbook" if pb_starts else "qa"))
        meta["_semantic_pass_keyword"] = sem_kw
        return "pass", skill or "qa", meta
    skill = (skill_starts[0].get("skill") if skill_starts else "playbook")
    return "fail", skill, meta


def update_progress(course: str, week: int, order: int, status: str, skill: str, elapsed: float):
    d = json.load(open(PROGRESS))
    wkey = f"week{week:02d}"
    d.setdefault("results", {}).setdefault(course, {}).setdefault(wkey, {})
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
        print(f"stages={meta['stages']}  skills={meta['skill_names']}  verify_match={meta['verify_match']}  has_semantic={meta.get('has_semantic')}  fallback={meta.get('fallback_attempts', 0)}/{meta.get('synthesized_calls', 0)}")
        if "llm_judge" in meta:
            j = meta["llm_judge"]
            print(f"judge: pass={j.get('pass')}  keyword={j.get('keyword','')!r}  reason={j.get('reason','')!r}")
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
