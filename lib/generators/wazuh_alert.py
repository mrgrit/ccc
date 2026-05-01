"""Wazuh alerts.json generator.

Wazuh manager 의 /var/ossec/logs/alerts/alerts.json 형식. rule.id 매칭 학습 + Active Response
trigger 분석 학습용.
"""
from __future__ import annotations
import json
import random
from datetime import datetime, timedelta
from typing import Iterator


_RULES = [
    # (rule_id, level, description, group)
    (5710, 5, "sshd: Attempt to login using a non-existent user", "authentication_failed,sshd"),
    (5712, 10, "sshd: brute force trying to get access to the system", "authentication_failed,sshd,brute_force"),
    (5503, 5, "PAM: User login failed.", "syslog,pam,authentication_failed"),
    (5402, 3, "Successful sudo to ROOT executed", "syslog,sudo"),
    (5403, 5, "First time user executed sudo", "syslog,sudo"),
    (100200, 12, "Custom: SUID binary modification detected", "syscheck,attack"),
    (100400, 10, "Custom: Suspicious payment-app field anomaly", "json_decoder,attack"),
    (100500, 8, "Custom: DNS query length > 100 bytes (possible exfil)", "dns,exfiltration"),
    (594, 10, "Multiple authentication failures", "authentication_failures"),
    (5104, 7, "FIM: Configuration file changed", "syscheck,config_change"),
    (550, 7, "FIM: File added to monitored directory", "syscheck"),
    (533, 5, "Listened ports status changed", "syslog"),
    (87213, 12, "VirusTotal: Malware detected", "virustotal,malware"),
]
_AGENTS = [
    {"id": "001", "name": "web-prod-01", "ip": "10.20.30.80"},
    {"id": "002", "name": "secu-fw-01", "ip": "10.20.30.1"},
    {"id": "003", "name": "siem-collector", "ip": "10.20.30.100"},
]


def _ts(start: datetime, day: int, hour: int, rng: random.Random) -> datetime:
    return start + timedelta(days=day, hours=hour, minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def generate(seed: int = 42,
             duration_days: int = 7,
             alerts_per_day: int = 50,
             brute_force_burst: bool = True,
             malware_detection_count: int = 2,
             ar_trigger_count: int = 4,
             start: datetime | None = None) -> Iterator[str]:
    """Wazuh alerts.json 이벤트 생성.

    Args:
        brute_force_burst: brute force burst (rule 5712 + AR trigger).
        malware_detection_count: VirusTotal hit (rule 87213).
        ar_trigger_count: Active Response trigger 표시.
    """
    start = start or (datetime.utcnow() - timedelta(days=duration_days))
    rng = random.Random(seed)
    events: list[tuple[datetime, str]] = []
    seq = 1000000

    # 1) 일반 alert mix
    for d in range(duration_days):
        for _ in range(alerts_per_day):
            ts = _ts(start, d, rng.randint(0, 23), rng)
            rule = rng.choices(_RULES,
                                weights=[20, 5, 15, 12, 4, 1, 1, 2, 3, 8, 6, 5, 1])[0]
            agent = rng.choice(_AGENTS)
            seq += 1
            src_ip = rng.choice(["203.0.113.42", "198.51.100.99", "10.20.30.5"])
            events.append((ts, _wazuh_json(ts, rule, agent, seq, src_ip, rng)))

    # 2) Brute force burst (rule 5712)
    if brute_force_burst:
        burst_day = rng.randint(0, duration_days - 1)
        burst_hour = rng.choice([3, 14, 23])
        attacker = "203.0.113.42"
        for i in range(15):
            ts = _ts(start, burst_day, burst_hour, rng) + timedelta(seconds=i * 4)
            seq += 1
            events.append((ts, _wazuh_json(ts, _RULES[1], _AGENTS[0], seq, attacker, rng)))

    # 3) VirusTotal malware
    for _ in range(malware_detection_count):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        seq += 1
        events.append((ts, _wazuh_json(ts, _RULES[12], _AGENTS[0], seq, None, rng,
                                          extra_data={"virustotal": {
                                              "malicious": 12,
                                              "permalink": "https://virustotal.com/x"}})))

    # 4) Active Response trigger
    for i in range(ar_trigger_count):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        seq += 1
        events.append((ts, _wazuh_json(ts, _RULES[1], _AGENTS[0], seq,
                                          "203.0.113.42", rng,
                                          extra_data={"active_response": {
                                              "command": "firewall-drop",
                                              "parameters": "203.0.113.42 60"}})))

    events.sort(key=lambda e: e[0])
    for _, line in events:
        yield line


def _wazuh_json(ts: datetime, rule: tuple, agent: dict, seq: int,
                src_ip: str | None, rng: random.Random,
                extra_data: dict | None = None) -> str:
    """Wazuh alerts.json 한 줄."""
    rule_id, level, desc, group = rule
    obj = {
        "timestamp": ts.isoformat() + "+0900",
        "rule": {
            "level": level,
            "description": desc,
            "id": str(rule_id),
            "groups": group.split(","),
        },
        "agent": agent,
        "manager": {"name": "siem-manager"},
        "id": str(seq),
        "decoder": {"name": "sshd" if "sshd" in group else "syslog"},
        "data": {},
    }
    if src_ip:
        obj["data"]["srcip"] = src_ip
        obj["data"]["srcuser"] = rng.choice(["root", "admin", "ccc", "test"])
    if extra_data:
        obj["data"].update(extra_data)
    obj["full_log"] = (f"{ts.strftime('%b %d %H:%M:%S')} {agent['name']} sshd: {desc} "
                       f"from {src_ip or 'localhost'}")
    obj["location"] = "/var/log/auth.log" if "auth" in group else "/var/log/syslog"
    return json.dumps(obj)


if __name__ == "__main__":
    for line in list(generate(seed=42, duration_days=7))[:3]:
        print(line)
