"""nftables / iptables drop log generator.

방화벽 차단 로그 — port scan / SYN flood / egress allowlist 위반 패턴.
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Iterator


_HOSTNAME = "secu-fw-01"
_INTERNAL_IPS = ["10.20.30.5", "10.20.30.10", "10.20.30.80", "10.20.30.100"]
_EXTERNAL_IPS = ["203.0.113.42", "198.51.100.99", "192.0.2.77", "203.0.113.155",
                  "172.16.0.50", "169.254.169.254"]
_TARGETED_PORTS = [22, 23, 80, 443, 3306, 3389, 8080, 9200, 5432, 6379, 27017,
                   8443, 5984, 9000]


def _ts(start: datetime, day: int, hour: int, rng: random.Random) -> datetime:
    return start + timedelta(days=day, hours=hour, minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def _nft_drop(ts: datetime, src: str, dst: str, sport: int, dport: int,
              proto: str, prefix: str = "DROP") -> str:
    """nftables drop log (kernel.log 형식)."""
    ts_str = ts.strftime("%b %d %H:%M:%S")
    return (f"{ts_str} {_HOSTNAME} kernel: [{int(ts.timestamp())}.{rng_us()}] "
            f"{prefix}: IN=eth0 OUT= MAC=02:00:00:00:00:01:02:00:00:00:00:02:08:00 "
            f"SRC={src} DST={dst} LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF "
            f"PROTO={proto} SPT={sport} DPT={dport} WINDOW=64240 RES=0x00 SYN URGP=0")


_RNG_US_COUNTER = [0]


def rng_us() -> str:
    _RNG_US_COUNTER[0] = (_RNG_US_COUNTER[0] + 7333) % 1000000
    return f"{_RNG_US_COUNTER[0]:06d}"


def generate(seed: int = 42,
             duration_days: int = 7,
             scan_bursts: int = 5,
             scan_ports_per_burst: int = 50,
             egress_violations: int = 20,
             syn_flood_count: int = 200,
             benign_drops_per_day: int = 10,
             start: datetime | None = None) -> Iterator[str]:
    """nftables drop log 생성.

    Args:
        scan_bursts: 외부에서 들어오는 port scan burst 수.
        scan_ports_per_burst: burst 별 시도 포트 수.
        egress_violations: 내부→외부 egress allowlist 위반 (악성 outbound 의심).
        syn_flood_count: SYN flood (동일 출처 다수 SYN) 패킷.
        benign_drops_per_day: 일반적 drop (잘못 보낸 패킷).
    """
    start = start or (datetime.utcnow() - timedelta(days=duration_days))
    rng = random.Random(seed)
    events: list[tuple[datetime, str]] = []

    # 1) Inbound port scan bursts
    for _ in range(scan_bursts):
        burst_day = rng.randint(0, duration_days - 1)
        burst_hour = rng.randint(0, 23)
        attacker = rng.choice(_EXTERNAL_IPS)
        target = rng.choice(_INTERNAL_IPS)
        for i in range(scan_ports_per_burst):
            ts = _ts(start, burst_day, burst_hour, rng) + timedelta(seconds=i)
            sport = rng.randint(40000, 65000)
            dport = rng.choice(_TARGETED_PORTS + list(range(20, 200)))
            events.append((ts, _nft_drop(ts, attacker, target, sport, dport, "TCP",
                                          "INBOUND-SCAN")))

    # 2) SYN flood (동일 출처 다수 SYN 짧은 시간)
    if syn_flood_count > 0:
        flood_day = rng.randint(0, duration_days - 1)
        flood_hour = rng.randint(2, 4)  # 새벽
        attacker = rng.choice(_EXTERNAL_IPS)
        target = rng.choice(_INTERNAL_IPS)
        for i in range(syn_flood_count):
            ts = (start + timedelta(days=flood_day, hours=flood_hour) +
                   timedelta(milliseconds=i * 50))
            spoofed_src = f"{rng.randint(1, 254)}.{rng.randint(0, 254)}.{rng.randint(0, 254)}.{rng.randint(1, 254)}"
            events.append((ts, _nft_drop(ts, spoofed_src, target,
                                          rng.randint(1024, 65535), 80, "TCP",
                                          "SYN-FLOOD")))

    # 3) Egress allowlist 위반 (내부→외부 의심 outbound)
    for _ in range(egress_violations):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        src = rng.choice(_INTERNAL_IPS)
        dst = rng.choice(["203.0.113.99", "198.51.100.55", "169.254.169.254",
                           "100.64.1.10"])  # 가상 C2 / metadata / CGN
        dport = rng.choice([443, 4444, 8080, 53, 6667])
        events.append((ts, _nft_drop(ts, src, dst, rng.randint(40000, 65000),
                                      dport, "TCP", "EGRESS-VIOLATION")))

    # 4) 일반 drop (background noise)
    for d in range(duration_days):
        for _ in range(benign_drops_per_day):
            ts = _ts(start, d, rng.randint(0, 23), rng)
            src = rng.choice(_EXTERNAL_IPS + _INTERNAL_IPS)
            dst = rng.choice(_INTERNAL_IPS)
            events.append((ts, _nft_drop(ts, src, dst, rng.randint(40000, 65000),
                                          rng.choice([23, 135, 445, 3389]), "TCP",
                                          "DROP")))

    events.sort(key=lambda e: e[0])
    for _, line in events:
        yield line


if __name__ == "__main__":
    for line in list(generate(seed=42, duration_days=7))[:3]:
        print(line)
