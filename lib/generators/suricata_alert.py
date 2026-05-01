"""Suricata IDS alert generator (eve.json 형식).

Suricata alert 이벤트 패턴 — 정찰 / exploit / C2 / exfil 카테고리.
"""
from __future__ import annotations
import json
import random
from datetime import datetime, timedelta
from typing import Iterator


_SIGNATURES = [
    # (sid, signature, severity, category, classtype)
    (2010935, "ET SCAN Nmap Scripting Engine User-Agent Detected", 2, "scan", "attempted-recon"),
    (2008070, "ET SCAN Possible WordPress xmlrpc.php Brute Force", 2, "scan", "attempted-admin"),
    (2018959, "ET WEB_SERVER SQL Injection - SELECT FROM", 1, "exploit", "web-application-attack"),
    (2024792, "ET WEB_SERVER Cross-Site Scripting Attempt", 1, "exploit", "web-application-attack"),
    (2032567, "ET TROJAN Generic SSL Cert Self Signed C2 Beacon", 1, "c2", "trojan-activity"),
    (2026847, "ET INFO Suspicious Outbound to Cloud Metadata 169.254.169.254", 2, "exfil", "policy-violation"),
    (2023883, "ET POLICY DNS Query for .onion proxy domain", 2, "c2", "policy-violation"),
    (2014819, "ET POLICY GNU/Linux APT User-Agent Outbound Likely Related to Package Management", 3, "info", "not-suspicious"),
    (2027865, "ET MALWARE Cobalt Strike DNS Beacon Activity", 1, "c2", "trojan-activity"),
    (2018470, "ET INFO Possible Kali Linux hostname in DHCP Request", 2, "scan", "attempted-recon"),
]
_INTERNAL_IPS = ["10.20.30.5", "10.20.30.10", "10.20.30.80", "10.20.30.100"]
_EXTERNAL_IPS = ["203.0.113.42", "198.51.100.99", "192.0.2.77", "203.0.113.155",
                 "169.254.169.254"]


def _ts(start: datetime, day: int, hour: int, rng: random.Random) -> datetime:
    return start + timedelta(days=day, hours=hour, minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def generate(seed: int = 42,
             duration_days: int = 7,
             alerts_per_day: int = 30,
             c2_beacon_count: int = 12,
             metadata_attempt_count: int = 4,
             start: datetime | None = None) -> Iterator[str]:
    """Suricata eve.json alert 이벤트 생성.

    Args:
        alerts_per_day: 일별 alert 수 (혼합 — scan/exploit/policy).
        c2_beacon_count: C2 beacon 패턴 (정기 간격).
        metadata_attempt_count: 클라우드 metadata 접근 시도.
    """
    start = start or (datetime.utcnow() - timedelta(days=duration_days))
    rng = random.Random(seed)
    events: list[tuple[datetime, str]] = []
    flow_id_counter = 1000000

    # 1) 일반 alert mix
    for d in range(duration_days):
        for _ in range(alerts_per_day):
            ts = _ts(start, d, rng.randint(0, 23), rng)
            sig = rng.choices(_SIGNATURES, weights=[15, 10, 8, 8, 5, 3, 4, 30, 5, 12])[0]
            sid, msg, severity, cat, classtype = sig
            src = rng.choice(_EXTERNAL_IPS)
            dst = rng.choice(_INTERNAL_IPS)
            flow_id_counter += rng.randint(100, 1000)
            events.append((ts, _eve_alert(ts, src, dst, sid, msg, severity, cat,
                                            classtype, flow_id_counter, rng)))

    # 2) C2 beacon (정기 간격 — 30분)
    if c2_beacon_count > 0:
        beacon_day = rng.randint(2, duration_days - 1)
        beacon_start_hour = rng.randint(8, 16)
        beacon_src = rng.choice(_INTERNAL_IPS)
        beacon_dst = "203.0.113.99"  # 가상 C2
        for i in range(c2_beacon_count):
            ts = (start + timedelta(days=beacon_day, hours=beacon_start_hour) +
                   timedelta(minutes=30 * i, seconds=rng.randint(-30, 30)))
            flow_id_counter += rng.randint(50, 500)
            events.append((ts, _eve_alert(ts, beacon_src, beacon_dst, 2032567,
                                            "ET TROJAN Generic SSL Cert Self Signed C2 Beacon",
                                            1, "c2", "trojan-activity",
                                            flow_id_counter, rng)))

    # 3) Cloud metadata 접근 시도 (SSRF chain)
    for _ in range(metadata_attempt_count):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(8, 18), rng)
        src = rng.choice(_INTERNAL_IPS)
        flow_id_counter += rng.randint(100, 1000)
        events.append((ts, _eve_alert(ts, src, "169.254.169.254", 2026847,
                                        "ET INFO Suspicious Outbound to Cloud Metadata "
                                        "169.254.169.254",
                                        2, "exfil", "policy-violation",
                                        flow_id_counter, rng)))

    events.sort(key=lambda e: e[0])
    for _, line in events:
        yield line


def _eve_alert(ts: datetime, src: str, dst: str, sid: int, msg: str,
               severity: int, category: str, classtype: str, flow_id: int,
               rng: random.Random) -> str:
    """Suricata eve.json alert 한 줄."""
    sport = rng.randint(40000, 65000)
    dport = rng.choice([80, 443, 8080, 53])
    proto = "TCP" if dport != 53 else "UDP"
    return json.dumps({
        "timestamp": ts.isoformat() + "+0000",
        "flow_id": flow_id,
        "in_iface": "eth0",
        "event_type": "alert",
        "src_ip": src,
        "src_port": sport,
        "dest_ip": dst,
        "dest_port": dport,
        "proto": proto,
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": sid,
            "rev": 1,
            "signature": msg,
            "category": category,
            "severity": severity,
            "classtype": classtype,
        },
    })


if __name__ == "__main__":
    for line in list(generate(seed=42, duration_days=7))[:3]:
        print(line)
