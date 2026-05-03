#!/usr/bin/env python3
"""Lab task fixture loader — task 시작 직전 합성 보안 데이터 주입.

Lab YAML 의 `fixtures` 필드를 읽어서 lib/generators/* 호출 → 결과를
(a) bastion local 디렉토리 `data/cyber-range-fixtures/<lab>/<order>/` 에 저장,
(b) ssh 가 가능하면 target_vm 의 명세된 path 에 추가 주입 (rsync/scp).

Schema (lab YAML 의 step 내):
    fixtures:
      - generator: lolbas_log    # lib/generators/<name>.py
        target_vm: web            # ssh 주입 대상 (local 만 하려면 'local')
        path: /var/log/audit/audit.log  # target VM 의 절대 경로
        params:
          seed: 42
          duration_days: 180
          binaries: {certutil: 7, powershell: 18, wmic: 3}
        mode: append                # append | overwrite
        cleanup: false              # task 종료 후 삭제 여부

사용:
    # task 1개 fixture 주입 (local only, 매번 random seed)
    python3 scripts/lab_fixture_inject.py \\
        --lab contents/labs/secops-ai/week08.yaml --order 9

    # 학생 id 결정론 (같은 학생/같은 task = 같은 데이터)
    python3 scripts/lab_fixture_inject.py --lab ... --order ... \\
        --student-id alice@ync.ac.kr

    # 명시 seed 재현 (디버깅·결과 재현)
    python3 scripts/lab_fixture_inject.py --lab ... --order ... --seed 42

    # 모든 lab 의 fixtures 일괄 생성 (local, random)
    python3 scripts/lab_fixture_inject.py --all --local-only

    # ssh 가능 환경에서 target VM 에 실 주입
    python3 scripts/lab_fixture_inject.py --lab ... --order ... --ssh

Seed 정책 (resolve_seed):
  --seed N        > --student-id S        > random
  명시 (재현)    > 학생별 결정론        > 매번 다름 (외우기 방지)

Mode (lab YAML 의 fixtures[].mode):
  overwrite (기본) — 매 호출 시 파일 덮어쓰기. 결정론적 학습.
  append          — 기존 파일에 새 events 누적. 시간 흐름 시뮬레이션.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import random
import sys
import yaml
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "lib" / "generators"
FIXTURE_DIR = ROOT / "data" / "cyber-range-fixtures"

VM_HOSTS = {
    "web": "10.20.30.80",
    "secu": "10.20.30.1",
    "siem": "10.20.30.100",
    "attacker": "10.20.30.201",
    "bastion": "10.20.30.200",
}


def load_generator(name: str):
    """lib.generators.<name> import."""
    sys.path.insert(0, str(ROOT))
    module = importlib.import_module(f"lib.generators.{name}")
    return module.generate


def resolve_seed(spec: dict, lab_id: str, order: int,
                  student_id: str | None, override_seed: int | None) -> int:
    """seed 결정 정책.

    우선순위: --seed N > --student-id S (deterministic per student) > params.seed (legacy) > random.

    student_id 결정론은 hash(student_id|lab_id|order) — 같은 학생/같은 task 는 같은 데이터.
    """
    if override_seed is not None:
        return override_seed
    if student_id:
        h = hashlib.sha256(f"{student_id}|{lab_id}|{order}".encode()).hexdigest()
        return int(h[:8], 16) % (2 ** 31 - 1)
    # legacy params.seed 무시 — 매번 random (외우기 방지)
    return random.randint(1, 2 ** 31 - 1)


def generate_to_local(spec: dict, lab_id: str, order: int,
                       seed: int) -> Path:
    """fixture spec 처리 → local 파일에 저장. Path 반환."""
    gen_name = spec["generator"]
    params = dict(spec.get("params", {}) or {})
    params["seed"] = seed  # 결정된 seed 로 override
    generator = load_generator(gen_name)

    out_dir = FIXTURE_DIR / lab_id / str(order)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(spec["path"]).name
    out_file = out_dir / filename

    mode = spec.get("mode", "overwrite")  # default overwrite (재현)
    file_mode = "a" if mode == "append" else "w"

    with out_file.open(file_mode) as f:
        count = 0
        for line in generator(**params):
            f.write(line + "\n")
            count += 1

    final_lines = sum(1 for _ in out_file.open()) if mode == "append" else count
    print(f"  ✓ {gen_name} → {out_file} (+{count} lines, mode={mode}, seed={seed}, total={final_lines})")
    return out_file


def inject_to_vm(spec: dict, local_file: Path, dry_run: bool = False) -> bool:
    """ssh 로 target_vm 에 주입 (append/overwrite)."""
    target = spec.get("target_vm", "local")
    if target == "local":
        return True
    if target not in VM_HOSTS:
        print(f"  ✗ unknown target_vm: {target}")
        return False

    host = VM_HOSTS[target]
    remote_path = spec["path"]
    mode = spec.get("mode", "append")

    if dry_run:
        print(f"  DRY: ssh ccc@{host} {mode} {local_file} → {remote_path}")
        return True

    import subprocess
    if mode == "append":
        cmd = (f"cat {local_file} | ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
               f"ccc@{host} 'sudo tee -a {remote_path} > /dev/null'")
    else:
        cmd = (f"cat {local_file} | ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
               f"ccc@{host} 'sudo tee {remote_path} > /dev/null'")
    rc = subprocess.call(cmd, shell=True, timeout=30)
    if rc == 0:
        print(f"  ✓ injected to {target}({host}):{remote_path} ({mode})")
        return True
    print(f"  ✗ ssh failed (rc={rc}) — local fixture preserved")
    return False


def process_lab(lab_path: Path, only_order: int | None = None,
                local_only: bool = False, dry_run: bool = False,
                student_id: str | None = None,
                override_seed: int | None = None) -> int:
    """lab YAML 의 fixtures 처리. 처리한 fixture 수 반환."""
    with lab_path.open() as f:
        lab = yaml.safe_load(f)
    lab_id = lab.get("lab_id") or lab_path.stem

    n_processed = 0
    for step in lab.get("steps", []):
        order = step.get("order")
        if only_order is not None and order != only_order:
            continue
        fixtures = step.get("fixtures") or []
        if not fixtures:
            continue
        print(f"[{lab_id}/{order}] fixtures: {len(fixtures)}")
        for spec in fixtures:
            try:
                seed = resolve_seed(spec, lab_id, order, student_id, override_seed)
                local_file = generate_to_local(spec, lab_id, order, seed)
                if not local_only:
                    inject_to_vm(spec, local_file, dry_run=dry_run)
                n_processed += 1
            except Exception as e:
                print(f"  ✗ {spec.get('generator')}: {e}")
    return n_processed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lab", help="lab YAML 경로")
    p.add_argument("--order", type=int, help="특정 order 만")
    p.add_argument("--all", action="store_true", help="전체 lab 처리")
    p.add_argument("--local-only", action="store_true",
                    help="ssh 주입 안 함, local generation 만")
    p.add_argument("--ssh", action="store_true",
                    help="ssh 주입 시도 (기본은 local-only)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--seed", type=int, default=None,
                    help="명시 seed (재현용). 없으면 random 또는 student-id 결정론.")
    p.add_argument("--student-id",
                    help="학생 ID (있으면 hash(id|lab|order) 결정론). 학생 lab 시작 시 사용.")
    args = p.parse_args()

    local_only = args.local_only or not args.ssh

    targets: list[Path] = []
    if args.all:
        targets = sorted((ROOT / "contents" / "labs").rglob("week*.yaml"))
    elif args.lab:
        targets = [Path(args.lab)]
    else:
        p.error("--lab 또는 --all 필요")

    total = 0
    seed_policy = (
        f"seed={args.seed}" if args.seed is not None
        else f"student={args.student_id}" if args.student_id
        else "random"
    )
    print(f"=== Fixture Inject {datetime.now().isoformat()} "
          f"(local_only={local_only}, policy={seed_policy}) ===")
    for lab in targets:
        total += process_lab(lab, only_order=args.order,
                              local_only=local_only, dry_run=args.dry_run,
                              student_id=args.student_id,
                              override_seed=args.seed)
    print(f"=== Total fixtures processed: {total} ===")


if __name__ == "__main__":
    main()
