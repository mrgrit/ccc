"""CCC CLI — Cyber Combat Commander CLI"""
import argparse
import json
import os
import httpx

API_URL = os.getenv("CCC_API_URL", "http://localhost:9100")
API_KEY = os.getenv("CCC_API_KEY", "ccc-api-key-2026")

def _h():
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def cmd_students(args):
    r = httpx.get(f"{API_URL}/students", headers=_h())
    for s in r.json().get("students", []):
        print(f"{s['student_id']:<12} {s['name']:<15} grp={s.get('grp','')} score={s['score']}")

def cmd_register(args):
    body = {"student_id": args.sid, "name": args.name, "email": args.email or "", "group": args.group or ""}
    r = httpx.post(f"{API_URL}/students", json=body, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def cmd_progress(args):
    r = httpx.get(f"{API_URL}/students/{args.sid}/progress", headers=_h())
    d = r.json()
    print(f"Labs completed: {d['labs']['completed']}/{d['labs']['total']}")
    print(f"CTF solved: {d['ctf']['solved']}")
    print(f"Battles: {d['battles']['total']}")

def cmd_lab_start(args):
    r = httpx.post(f"{API_URL}/labs/start", json={"student_id": args.sid, "lab_id": args.lab}, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def cmd_lab_submit(args):
    r = httpx.post(f"{API_URL}/labs/submit", json={"student_id": args.sid, "lab_id": args.lab}, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def cmd_ctf_submit(args):
    r = httpx.post(f"{API_URL}/ctf/submit", json={"student_id": args.sid, "challenge_id": args.cid, "flag": args.flag}, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def cmd_battle(args):
    body = {"challenger_id": args.sid, "mode": args.mode or "manual"}
    r = httpx.post(f"{API_URL}/battles", json=body, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def cmd_leaderboard(args):
    r = httpx.get(f"{API_URL}/leaderboard", params={"category": args.cat or "total"}, headers=_h())
    for i, e in enumerate(r.json().get("leaderboard", []), 1):
        print(f"#{i} {e.get('name','?'):<15} {e.get('student_id','')}")

def cmd_dashboard(args):
    r = httpx.get(f"{API_URL}/dashboard", headers=_h())
    d = r.json()
    print(f"Students: {d['students']}  Infras: {d['infras']}")
    print(f"Labs done: {d['labs_completed']}  CTF solved: {d['ctf_solved']}")
    print(f"Battles: {d['battles']}  Blocks: {d['blockchain_blocks']}")

def cmd_ai_task(args):
    body = {"student_id": args.sid, "instruction": args.instruction}
    r = httpx.post(f"{API_URL}/ai/task", json=body, headers=_h())
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def main():
    p = argparse.ArgumentParser(prog="ccc", description="Cyber Combat Commander")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("students", help="학생 목록")
    sub.add_parser("dashboard", help="대시보드")

    pr = sub.add_parser("register", help="학생 등록")
    pr.add_argument("sid"); pr.add_argument("name")
    pr.add_argument("--email", default=""); pr.add_argument("--group", default="")

    pp = sub.add_parser("progress", help="진도 확인")
    pp.add_argument("sid")

    pl = sub.add_parser("lab-start", help="실습 시작")
    pl.add_argument("sid"); pl.add_argument("lab")

    ps = sub.add_parser("lab-submit", help="실습 제출")
    ps.add_argument("sid"); ps.add_argument("lab")

    pc = sub.add_parser("ctf-submit", help="CTF 플래그 제출")
    pc.add_argument("sid"); pc.add_argument("cid"); pc.add_argument("flag")

    pb = sub.add_parser("battle", help="대전 요청")
    pb.add_argument("sid"); pb.add_argument("--mode", default="manual")

    plb = sub.add_parser("leaderboard", help="리더보드")
    plb.add_argument("--cat", default="total")

    pa = sub.add_parser("ai-task", help="AI 작업 요청")
    pa.add_argument("sid"); pa.add_argument("instruction")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    cmds = {
        "students": cmd_students, "register": cmd_register, "progress": cmd_progress,
        "lab-start": cmd_lab_start, "lab-submit": cmd_lab_submit,
        "ctf-submit": cmd_ctf_submit, "battle": cmd_battle,
        "leaderboard": cmd_leaderboard, "dashboard": cmd_dashboard, "ai-task": cmd_ai_task,
    }
    cmds[args.cmd](args)

if __name__ == "__main__":
    main()
