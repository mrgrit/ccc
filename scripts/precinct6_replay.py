#!/usr/bin/env python3
"""Precinct 6 traffic replay — signals.parquet → SIEM 이벤트 주입.

P1 Phase C 구현체. Precinct 6 dataset 의 sanitized signals 를 syslog/JSON 형식으로
변환해 cyber range 의 siem(10.20.30.100) 또는 Wazuh manager 에 주입한다.

## 데이터 한계
signals.parquet (2.07M rows) 는 event-level metadata 만 있음 (packet content 없음):
- timestamp, src_ip, dst_ip, dst_port, message_type, vendor_code, severity, mo_name
- protocol/dst_port 대부분 None (sanitized 로 인해)
→ raw PCAP replay 불가능.
→ 대안: syslog/JSON 라인으로 변환 → siem 의 입력 채널에 주입 (Wazuh agent /var/ossec/queue/logcollector,
  firewall log file tail, Logstash beat input 등).

## 사용
    # dry-run: 첫 100 행을 stdout 으로
    python3 scripts/precinct6_replay.py --src data/precinct6 --max 100 --dry-run

    # mo_name 필터 + JSON output 파일
    python3 scripts/precinct6_replay.py --src data/precinct6 --filter "Data Theft" \\
        --max 1000 --format json --out /tmp/replay.jsonl

    # 실 주입 — siem 의 /var/log/precinct6_replay.log 에 append (ssh 필요)
    python3 scripts/precinct6_replay.py --src data/precinct6 --filter Phishing \\
        --max 500 --format syslog --inject siem

## 주입 결과
- /var/log/precinct6_replay.log 에 append (rsyslog tail 으로 Wazuh 가 읽음)
- 예상: Wazuh alert.log 에서 Data Theft 또는 Phishing 패턴 매칭 alert 발생

## 폐쇄망 호환
- pyarrow 만 의존 (이미 설치됨)
- ssh 통신: scripts/sync_to_bastion.sh 와 동일 방식 (sshpass)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

CCC = Path(__file__).resolve().parent.parent

# Wazuh-friendly syslog format. RFC 5424 lite — Wazuh logcollector 가 잘 파싱.
# format: <PRI>TIMESTAMP HOST PROCESS[PID]: KEY=VALUE ...
SYSLOG_TEMPLATE = (
    "<{pri}>{iso_ts} replay-bastion precinct6_replay[{pid}]: "
    "type={message_type} src={src_ip} dst={dst_ip}:{dst_port} "
    "vendor={vendor_code} severity={severity} mo={mo_name} "
    "techniques={attack_techniques}"
)

# Firewall log format (iptables LOG style)
FIREWALL_TEMPLATE = (
    "{iso_ts} replay-bastion kernel: [{pid}.000000] [PRECINCT6-REPLAY] "
    "IN=eth0 OUT= MAC= SRC={src_ip} DST={dst_ip} PROTO={protocol} "
    "SPT={src_port} DPT={dst_port} ACTION={action} "
    "VENDOR={vendor_code} MO=\"{mo_name}\""
)

# Severity to syslog priority (facility=local0=16)
SEVERITY_PRI = {
    "critical": 16 * 8 + 2,  # local0.crit
    "high": 16 * 8 + 3,      # local0.err
    "medium": 16 * 8 + 4,    # local0.warning
    "low": 16 * 8 + 6,       # local0.info
}


def load_signals(src: Path, max_rows: int, filter_mo: str | None):
    import pyarrow.parquet as pq
    p = src / "signals" / "signals.parquet"
    if not p.exists():
        sys.exit(f"ERROR: {p} not found")
    cols = [
        "timestamp", "message_type", "src_ip", "dst_ip",
        "src_port", "dst_port", "protocol",
        "vendor_code", "severity", "action",
        "mo_name", "attack_techniques", "lifecycle_stage",
        "username", "src_host", "dst_host",
    ]
    # 큰 파일이라 batch 로 읽고 filter
    pf = pq.ParquetFile(p)
    out = []
    for batch in pf.iter_batches(batch_size=10000, columns=cols):
        df = batch.to_pandas()
        if filter_mo:
            df = df[df["mo_name"].astype(str).str.contains(filter_mo, case=False, na=False)]
        for _, row in df.iterrows():
            out.append(row.to_dict())
            if len(out) >= max_rows:
                return out
    return out


def to_syslog(row: dict, pid: int) -> str:
    ts = row.get("timestamp", time.time())
    if hasattr(ts, "isoformat"):
        iso = ts.isoformat()
    else:
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(float(ts)))
    sev = (row.get("severity") or "low").lower()
    pri = SEVERITY_PRI.get(sev, SEVERITY_PRI["low"])
    techs = row.get("attack_techniques") or []
    if hasattr(techs, "tolist"):
        techs = techs.tolist()
    return SYSLOG_TEMPLATE.format(
        pri=pri, iso_ts=iso, pid=pid,
        message_type=row.get("message_type", "?"),
        src_ip=row.get("src_ip", "?"), dst_ip=row.get("dst_ip", "?"),
        dst_port=row.get("dst_port") or "0",
        vendor=str(row.get("vendor_code", "?"))[:60],
        vendor_code=str(row.get("vendor_code", "?"))[:60],
        severity=sev, mo_name=row.get("mo_name", "?"),
        attack_techniques=",".join(techs) if techs else "-",
    )


def to_firewall(row: dict, pid: int) -> str:
    ts = row.get("timestamp", time.time())
    if hasattr(ts, "isoformat"):
        iso = ts.isoformat()
    else:
        iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(float(ts)))
    return FIREWALL_TEMPLATE.format(
        iso_ts=iso, pid=pid,
        src_ip=row.get("src_ip", "0.0.0.0"),
        dst_ip=row.get("dst_ip", "0.0.0.0"),
        protocol=str(row.get("protocol") or "TCP"),
        src_port=row.get("src_port") or "0",
        dst_port=row.get("dst_port") or "0",
        action=row.get("action") or "ACCEPT",
        vendor_code=str(row.get("vendor_code", "?"))[:40],
        mo_name=row.get("mo_name", "?"),
    )


def to_json(row: dict) -> str:
    # Wazuh JSON-formatted log (decoder=json) 호환
    out = {}
    for k, v in row.items():
        if hasattr(v, "tolist"):
            v = v.tolist()
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        out[k] = v
    out["_source"] = "precinct6_replay"
    out["_replayed_at"] = time.time()
    return json.dumps(out, ensure_ascii=False, default=str)


def emit(rows: list, fmt: str, out_path: Path | None) -> int:
    pid = os.getpid()
    fh = open(out_path, "a") if out_path else sys.stdout
    n = 0
    for row in rows:
        if fmt == "syslog":
            line = to_syslog(row, pid)
        elif fmt == "firewall":
            line = to_firewall(row, pid)
        elif fmt == "json":
            line = to_json(row)
        else:
            sys.exit(f"unknown format: {fmt}")
        fh.write(line + "\n")
        n += 1
    if out_path:
        fh.close()
    return n


def inject_remote(out_path: Path, target: str, remote_path: str) -> int:
    """ssh + scp 로 remote 에 append. inject 모드용."""
    import subprocess
    targets = {
        "siem": ("ccc", "10.20.30.100"),
        "secu": ("ccc", "10.20.30.1"),
    }
    if target not in targets:
        sys.exit(f"unknown target: {target}")
    user, ip = targets[target]
    pw = os.environ.get("REMOTE_PASS", "1")
    # scp the file then cat >> remote log
    cp = subprocess.run(
        ["sshpass", "-p", pw, "scp", "-o", "StrictHostKeyChecking=no",
         str(out_path), f"{user}@{ip}:/tmp/p6_replay.tmp"],
        capture_output=True, text=True, timeout=60,
    )
    if cp.returncode != 0:
        sys.exit(f"scp failed: {cp.stderr}")
    cmd = subprocess.run(
        ["sshpass", "-p", pw, "ssh", "-o", "StrictHostKeyChecking=no",
         f"{user}@{ip}",
         f"sudo bash -c 'cat /tmp/p6_replay.tmp >> {remote_path} && rm /tmp/p6_replay.tmp'"],
        capture_output=True, text=True, timeout=30,
    )
    if cmd.returncode != 0:
        sys.exit(f"remote append failed: {cmd.stderr}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(CCC / "data/precinct6"),
                   help="Precinct 6 mirror directory")
    p.add_argument("--max", type=int, default=100, help="max rows to replay")
    p.add_argument("--filter", default="", help="filter by mo_name (substring)")
    p.add_argument("--format", choices=["syslog", "firewall", "json"], default="syslog")
    p.add_argument("--out", default="", help="output file path (default stdout)")
    p.add_argument("--dry-run", action="store_true",
                   help="print to stdout regardless of --out (DB/remote 미접속)")
    p.add_argument("--inject", choices=["siem", "secu"],
                   help="remote VM 으로 ssh+scp 주입 (--out 필수)")
    p.add_argument("--remote-path", default="/var/log/precinct6_replay.log",
                   help="remote log file path")
    args = p.parse_args()

    src = Path(args.src)
    rows = load_signals(src, args.max, args.filter or None)
    print(f"# loaded {len(rows)} rows from {src}", file=sys.stderr)

    out_path = Path(args.out) if args.out and not args.dry_run else None
    n = emit(rows, args.format, out_path)
    print(f"# emitted {n} lines (format={args.format})", file=sys.stderr)

    if args.inject:
        if not out_path:
            sys.exit("--inject 사용 시 --out 필수")
        rc = inject_remote(out_path, args.inject, args.remote_path)
        print(f"# injected → {args.inject}:{args.remote_path} rc={rc}", file=sys.stderr)


if __name__ == "__main__":
    main()
