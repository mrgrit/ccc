#!/usr/bin/env python3
"""AgentBench OS subset → Bastion /chat 어댑터.

AgentBench (Liu et al. 2024) — 8 environments. 본 adapter 는 OS subset (60 task).
Linux 컨테이너에서 bash command 로 OS 작업 (file/process/user/permission/cron) 수행.

Cybench/InterCode 와 차이:
- CTF 가 아닌 일반 OS 작업 (예: "user 'alice' 의 home 권한 확인 및 600으로 변경")
- 멀티턴 ReAct 형식 (Thought → Action → Observation)
- 정답 채점 (oracle 기반) — task 별 expected_output 또는 verification cmd

사용:
    python3 -m benchmarks.agentbench_os_adapter --task <yaml/json>
    python3 -m benchmarks.agentbench_os_adapter --tasks-dir agentbench/os/
    python3 -m benchmarks.agentbench_os_adapter --sample
"""
from __future__ import annotations
import argparse, json, pathlib, time
from collections import Counter

from benchmarks.cybench_adapter import (
    call_bastion, extract_commands_from_events, exec_in_container,
)

# AgentBench OS task 카테고리 (paper Table 7)
CATEGORIES = {
    "file-manipulation",      # file/dir 생성/이동/권한
    "process-management",     # ps/kill/systemctl
    "user-permission",        # useradd/chmod/chown
    "system-configuration",   # /etc/* 편집
    "cron-scheduling",        # crontab/systemd-timer
    "log-analysis",           # /var/log/* 분석
    "package-management",     # apt/yum
    "network-config",         # ip/route/iptables
}

SAMPLE_TASK = {
    "task_id": "agentbench-os-001",
    "category": "user-permission",
    "description": "Find the home directory of user 'alice' and ensure it has 0700 permission. Output the final permission with stat.",
    "container_id": "agentbench_os_sample",
    "container_image": "agentbench/ubuntu:latest",
    "verification_cmd": "stat -c '%a' /home/alice",
    "expected_output_pattern": r"^700$",
    "max_turns": 5,
    "subtasks": [
        {"hint": "Identify alice's home dir", "answer_pattern": r"/home/alice|alice:.*:/home/alice"},
        {"hint": "Apply chmod 700", "answer_pattern": r"chmod (0?700|u\+rwx)|drwx-{6}"},
    ],
}


def agentbench_solve(task: dict, max_turns: int = None, dry_run: bool = False) -> dict:
    """AgentBench OS task 풀이 — ReAct 형식 + verification_cmd 로 정답 채점."""
    max_turns = max_turns or task.get("max_turns", 8)
    container = task.get("container_id", "")
    history = []
    subtasks_done: set[int] = set()
    completed = False
    t0 = time.time()
    final_check_output = ""

    for turn in range(max_turns):
        history_text = "\n".join(
            f"[turn {i+1}]\n  Action: {h['cmd']}\n  Observation: {h['output'][:400]}"
            for i, h in enumerate(history[-4:]))
        prompt = (
            f"## AgentBench OS — {task.get('category','?').upper()}\n"
            f"{task.get('description','')}\n\n"
            f"컨테이너: {container} (Linux Ubuntu)\n"
            f"채점 명령: {task.get('verification_cmd','(없음)')}\n\n"
            f"## ReAct History (최근 4)\n{history_text or '(시작)'}\n\n"
            f"## 다음 Action\n"
            f"Thought: 한 줄 추론\n"
            f"Action: shell skill 로 정확한 1개 명령\n"
            f"임무 완료라 판단되면 verification_cmd 직접 실행해서 정답 확인."
        )
        result = call_bastion(prompt, course="agentbench-eval")
        events = result.get("events", [])
        if result.get("error"):
            return {"task_id": task.get("task_id"), "category": task.get("category"),
                    "completed": False, "reason": f"bastion error: {result['error']}",
                    "turns": turn, "elapsed_sec": time.time() - t0}

        cmds = extract_commands_from_events(events)
        if not cmds:
            answer = "\n".join(e.get("token", "") for e in events if e.get("event") == "stream_token")
            history.append({"cmd": "(no exec)", "output": answer[:500]})
            continue

        for cmd in cmds[:2]:
            output = exec_in_container(container, cmd, dry_run=dry_run)
            history.append({"cmd": cmd, "output": output})
            # subtask 매칭
            import re
            for cp_idx, cp in enumerate(task.get("subtasks", [])):
                pat = cp.get("answer_pattern", "")
                if pat and cp_idx not in subtasks_done and re.search(pat, output, re.MULTILINE):
                    subtasks_done.add(cp_idx)
            # verification_cmd 가 명령에 포함됐으면 즉시 채점
            verif = task.get("verification_cmd", "")
            if verif and verif in cmd:
                final_check_output = output
                if re.search(task.get("expected_output_pattern", ""), output):
                    completed = True
                    break
        if completed: break

    # 마지막 강제 verification (LLM 이 검증 안 했으면)
    if not completed and not dry_run:
        verif = task.get("verification_cmd", "")
        if verif:
            final_check_output = exec_in_container(container, verif, dry_run=dry_run)
            import re
            if re.search(task.get("expected_output_pattern", ""), final_check_output):
                completed = True

    return {
        "task_id": task.get("task_id"),
        "category": task.get("category"),
        "completed": completed,
        "subtasks_done": sorted(subtasks_done),
        "total_subtasks": len(task.get("subtasks", [])),
        "subtask_completion_rate": round(len(subtasks_done) / max(len(task.get("subtasks", [])), 1), 3),
        "verification_output": final_check_output[:300],
        "turns": min(turn + 1, max_turns),
        "elapsed_sec": round(time.time() - t0, 1),
    }


def run_batch(tasks_dir: pathlib.Path, output_dir: pathlib.Path, dry_run: bool = False):
    import yaml
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(tasks_dir.glob("*.yaml")) + sorted(tasks_dir.glob("*.json")):
        if path.suffix == ".yaml":
            task = yaml.safe_load(path.read_text())
        else:
            task = json.loads(path.read_text())
        print(f"▶ {task.get('task_id', path.stem)} [{task.get('category','?')}]", flush=True)
        r = agentbench_solve(task, dry_run=dry_run)
        results.append(r)
        (output_dir / f"{task.get('task_id', path.stem)}.json").write_text(json.dumps(r, indent=2))
        print(f"  → {'✅' if r['completed'] else '○'} subtasks {len(r['subtasks_done'])}/{r['total_subtasks']} "
              f"turns={r['turns']} {r['elapsed_sec']}s", flush=True)

    by_cat = Counter(r["category"] for r in results)
    pass_by_cat = Counter(r["category"] for r in results if r["completed"])
    summary = {
        "total_tasks": len(results),
        "completed": sum(1 for r in results if r["completed"]),
        "pass_rate": round(sum(1 for r in results if r["completed"]) / max(len(results), 1), 3),
        "avg_subtask_rate": round(sum(r["subtask_completion_rate"] for r in results) / max(len(results), 1), 3),
        "avg_turns": round(sum(r["turns"] for r in results) / max(len(results), 1), 1),
        "avg_elapsed_sec": round(sum(r["elapsed_sec"] for r in results) / max(len(results), 1), 1),
        "by_category": {c: {"total": by_cat[c], "passed": pass_by_cat[c],
                           "rate": round(pass_by_cat[c]/max(by_cat[c],1), 3)} for c in CATEGORIES if by_cat[c]},
    }
    (output_dir / "_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n=== AgentBench OS 종합 ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task")
    p.add_argument("--tasks-dir")
    p.add_argument("--output", default="results/agentbench_os/")
    p.add_argument("--max-turns", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()

    if args.sample:
        r = agentbench_solve(SAMPLE_TASK, max_turns=args.max_turns, dry_run=True)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    if args.task:
        import yaml
        task = yaml.safe_load(open(args.task)) if args.task.endswith(".yaml") else json.loads(open(args.task).read())
        print(json.dumps(agentbench_solve(task, max_turns=args.max_turns, dry_run=args.dry_run), indent=2, ensure_ascii=False))
    elif args.tasks_dir:
        run_batch(pathlib.Path(args.tasks_dir), pathlib.Path(args.output), dry_run=args.dry_run)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
