"""SSH/sudo 인증 로그 generator.

/var/log/auth.log 형식. brute force / spray / 정상 로그인 / sudo 실패 패턴 혼합.

학습 목표: 시간 분석 (window 기반 brute) + IP enum + 사용자 enum 분리.
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Iterator


_HOSTNAME = "web-prod-01"
_USERS_VALID = ["webadmin", "ccc", "appuser", "svc-monitor"]
_USERS_BRUTE = ["root", "admin", "ubuntu", "test", "oracle", "postgres", "www-data"]
_PASSWORDS_TRIED = ["", "password", "123456", "admin", "P@ssw0rd", "qwerty"]


def _ts(start: datetime, day_offset: int, hour: int, rng: random.Random) -> datetime:
    return start + timedelta(days=day_offset, hours=hour,
                              minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def _syslog_prefix(ts: datetime) -> str:
    """syslog 형식 prefix: 'Apr 26 14:23:01 web-prod-01 sshd[12345]:'"""
    return ts.strftime("%b %d %H:%M:%S") + f" {_HOSTNAME} sshd"


def generate(seed: int = 42,
             duration_days: int = 30,
             brute_attempts_per_burst: int = 50,
             burst_count: int = 3,
             spray_attempts: int = 100,
             normal_logins_per_day: int = 8,
             sudo_failures: int = 5,
             attacker_ips: list[str] | None = None,
             start: datetime | None = None) -> Iterator[str]:
    """SSH 인증 + sudo 로그 생성.

    Args:
        brute_attempts_per_burst: 단일 burst 의 시도 횟수 (집중 brute force).
        burst_count: 별도 burst 발생 횟수.
        spray_attempts: 분산된 password spray (다른 사용자 시도).
        normal_logins_per_day: 정상 로그인 (일별).
        sudo_failures: 의심 sudo 실패 (privilege escalation 시도).
        attacker_ips: brute force 출처 IP (None = 자동 생성).

    Yields:
        syslog 형식 한 줄.
    """
    attacker_ips = attacker_ips or ["203.0.113.42", "198.51.100.99", "192.0.2.77"]
    start = start or (datetime.utcnow() - timedelta(days=duration_days))

    rng = random.Random(seed)
    events: list[tuple[datetime, str]] = []
    pid = 5000

    # 1) brute force bursts — 짧은 시간대 다수 시도
    for _ in range(burst_count):
        burst_day = rng.randint(0, duration_days - 1)
        burst_hour = rng.choice([2, 3, 4, 14, 23])  # 새벽 / 점심 / 야간
        attacker = rng.choice(attacker_ips)
        for i in range(brute_attempts_per_burst):
            ts = _ts(start, burst_day, burst_hour, rng) + timedelta(seconds=i * 2)
            user = rng.choice(_USERS_BRUTE)
            pid += 1
            events.append((ts, f"{_syslog_prefix(ts)}[{pid}]: "
                                f"Failed password for invalid user {user} from {attacker} port "
                                f"{rng.randint(40000, 65000)} ssh2"))

    # 2) password spray — 분산된 시도 (rate limit 우회 패턴)
    for _ in range(spray_attempts):
        day = rng.randint(0, duration_days - 1)
        ts = _ts(start, day, rng.randint(0, 23), rng)
        user = rng.choice(_USERS_VALID + _USERS_BRUTE)
        attacker = rng.choice(attacker_ips)
        pid += 1
        events.append((ts, f"{_syslog_prefix(ts)}[{pid}]: "
                            f"Failed password for {user} from {attacker} port "
                            f"{rng.randint(40000, 65000)} ssh2"))

    # 3) 정상 로그인 (background noise)
    for d in range(duration_days):
        for _ in range(normal_logins_per_day):
            ts = _ts(start, d, rng.randint(8, 19), rng)
            user = rng.choice(_USERS_VALID)
            src = rng.choice(["10.20.30.5", "10.20.30.10", "10.20.30.201"])
            pid += 1
            events.append((ts, f"{_syslog_prefix(ts)}[{pid}]: "
                                f"Accepted publickey for {user} from {src} port "
                                f"{rng.randint(40000, 65000)} ssh2: RSA SHA256:abc123def456..."))

    # 4) sudo 실패 (privilege escalation 시도)
    for _ in range(sudo_failures):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(8, 22), rng)
        user = rng.choice(_USERS_VALID)
        cmd = rng.choice(["/bin/bash", "/usr/bin/cat /etc/shadow", "/usr/sbin/iptables -F",
                          "/usr/bin/dd if=/dev/sda"])
        events.append((ts, ts.strftime("%b %d %H:%M:%S") + f" {_HOSTNAME} sudo: "
                       f"{user} : 3 incorrect password attempts ; TTY=pts/0 ; PWD=/home/{user} ; "
                       f"USER=root ; COMMAND={cmd}"))

    events.sort(key=lambda e: e[0])
    for _, line in events:
        yield line


if __name__ == "__main__":
    for line in list(generate(seed=42, duration_days=30))[:5]:
        print(line)
