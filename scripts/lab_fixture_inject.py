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
    # task 1개 fixture 주입 (local only)
    python3 scripts/lab_fixture_inject.py \\
        --lab contents/labs/secops-ai/week08.yaml --order 9

    # 모든 lab 의 fixtures 일괄 생성 (local)
    python3 scripts/lab_fixture_inject.py --all --local-only

    # ssh 가능 환경에서 target VM 에 실 주입
    python3 scripts/lab_fixture_inject.py --lab ... --order ... --ssh
"""
from __future__ import annotations
import argparse
import importlib
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


def generate_to_local(spec: dict, lab_id: str, order: int) -> Path:
    """fixture spec 처리 → local 파일에 저장. Path 반환."""
    gen_name = spec["generator"]
    params = spec.get("params", {}) or {}
    generator = load_generator(gen_name)

    out_dir = FIXTURE_DIR / lab_id / str(order)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(spec["path"]).name
    out_file = out_dir / filename

    with out_file.open("w") as f:
        count = 0
        for line in generator(**params):
            f.write(line + "\n")
            count += 1

    print(f"  ✓ {gen_name} → {out_file} ({count} lines)")
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
                local_only: bool = False, dry_run: bool = False) -> int:
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
                local_file = generate_to_local(spec, lab_id, order)
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
    print(f"=== Fixture Inject {datetime.now().isoformat()} (local_only={local_only}) ===")
    for lab in targets:
        total += process_lab(lab, only_order=args.order,
                              local_only=local_only, dry_run=args.dry_run)
    print(f"=== Total fixtures processed: {total} ===")


if __name__ == "__main__":
    main()
