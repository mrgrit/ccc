"""웹 access log generator (Apache combined / nginx 형식).

bot/scanner/SQLi/XSS/path-traversal 패턴 + 정상 트래픽 혼합.
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Iterator


_NORMAL_PATHS = ["/", "/index.html", "/login", "/api/products", "/static/css/main.css",
                 "/static/js/app.js", "/api/cart", "/checkout", "/about"]
_SCANNER_PATHS = ["/admin", "/wp-admin/", "/.env", "/.git/HEAD", "/phpmyadmin/",
                  "/backup.sql", "/.aws/credentials", "/api-docs", "/swagger.json",
                  "/.git/config", "/wp-login.php", "/server-status"]
_SQLI_PATTERNS = ["?id=1' OR '1'='1", "?q=' UNION SELECT * FROM users--",
                  "?search=admin'/**/OR/**/1=1--", "?user=' or 1=1#"]
_XSS_PATTERNS = ["?q=<script>alert(1)</script>", "?name=<img src=x onerror=alert(1)>",
                 "?msg=javascript:alert(document.cookie)"]
_PATH_TRAV = ["?file=../../etc/passwd", "?path=....//etc/shadow",
              "?include=%2e%2e%2fetc%2fpasswd"]
_USER_AGENTS_NORMAL = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/120.0",
]
_USER_AGENTS_SCANNER = [
    "Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)",
    "Nikto/2.5.0",
    "sqlmap/1.7.10#stable (https://sqlmap.org)",
    "dirbuster",
    "gobuster/3.6",
    "Mozilla/5.0 (compatible; Baiduspider/2.0)",
]
_NORMAL_IPS = ["10.20.30.5", "10.20.30.10", "203.0.113.42", "198.51.100.99"]
_SCANNER_IPS = ["192.0.2.77", "203.0.113.155", "198.51.100.200"]


def _ts(start: datetime, day: int, hour: int, rng: random.Random) -> datetime:
    return start + timedelta(days=day, hours=hour, minutes=rng.randint(0, 59),
                              seconds=rng.randint(0, 59))


def _apache_line(ts: datetime, ip: str, method: str, path: str, status: int,
                 size: int, referer: str, ua: str) -> str:
    """Apache combined log format."""
    ts_str = ts.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return (f'{ip} - - [{ts_str}] "{method} {path} HTTP/1.1" {status} {size} '
            f'"{referer}" "{ua}"')


def generate(seed: int = 42,
             duration_days: int = 7,
             normal_requests_per_day: int = 200,
             scanner_bursts: int = 5,
             scanner_paths_per_burst: int = 30,
             sqli_attempts: int = 12,
             xss_attempts: int = 8,
             path_traversal_attempts: int = 6,
             format: str = "apache",
             start: datetime | None = None) -> Iterator[str]:
    """Web access log 생성.

    학습 목표: 정상 트래픽 분포 + 스캐너 burst 식별 + 공격 패턴 (SQLi/XSS/LFI) 분리.
    """
    start = start or (datetime.utcnow() - timedelta(days=duration_days))
    rng = random.Random(seed)
    events: list[tuple[datetime, str]] = []

    # 1) 정상 트래픽
    for d in range(duration_days):
        for _ in range(normal_requests_per_day):
            hour = rng.choices(range(24), weights=[1]*7+[3]*2+[5]*4+[3]*2+[5]*5+[3]*2+[1]*2)[0]
            ts = _ts(start, d, hour, rng)
            ip = rng.choice(_NORMAL_IPS)
            path = rng.choice(_NORMAL_PATHS)
            method = "GET"
            status = rng.choices([200, 304, 301, 404], weights=[80, 10, 5, 5])[0]
            size = rng.randint(500, 50000)
            ua = rng.choice(_USER_AGENTS_NORMAL)
            events.append((ts, _apache_line(ts, ip, method, path, status, size,
                                              "-", ua)))

    # 2) 스캐너 burst
    for _ in range(scanner_bursts):
        burst_day = rng.randint(0, duration_days - 1)
        burst_hour = rng.randint(0, 23)
        scanner_ip = rng.choice(_SCANNER_IPS)
        scanner_ua = rng.choice(_USER_AGENTS_SCANNER)
        for i in range(scanner_paths_per_burst):
            ts = _ts(start, burst_day, burst_hour, rng) + timedelta(seconds=i)
            path = rng.choice(_SCANNER_PATHS)
            status = rng.choices([404, 403, 200], weights=[80, 15, 5])[0]
            events.append((ts, _apache_line(ts, scanner_ip, "GET", path, status,
                                              rng.randint(150, 5000), "-", scanner_ua)))

    # 3) SQLi 시도 (스캐너 IP 또는 정상 IP 위장)
    for _ in range(sqli_attempts):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        ip = rng.choice(_SCANNER_IPS + _NORMAL_IPS[2:])
        path = "/api/products" + rng.choice(_SQLI_PATTERNS)
        status = rng.choice([403, 500, 200])
        ua = rng.choice(_USER_AGENTS_SCANNER + _USER_AGENTS_NORMAL[:1])
        events.append((ts, _apache_line(ts, ip, "GET", path, status,
                                          rng.randint(200, 3000), "-", ua)))

    # 4) XSS 시도
    for _ in range(xss_attempts):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        ip = rng.choice(_SCANNER_IPS)
        path = "/search" + rng.choice(_XSS_PATTERNS)
        events.append((ts, _apache_line(ts, ip, "GET", path, 200,
                                          rng.randint(500, 8000), "-",
                                          rng.choice(_USER_AGENTS_NORMAL))))

    # 5) Path traversal
    for _ in range(path_traversal_attempts):
        d = rng.randint(0, duration_days - 1)
        ts = _ts(start, d, rng.randint(0, 23), rng)
        ip = rng.choice(_SCANNER_IPS)
        path = "/api/file" + rng.choice(_PATH_TRAV)
        events.append((ts, _apache_line(ts, ip, "GET", path, 403,
                                          rng.randint(150, 800), "-",
                                          rng.choice(_USER_AGENTS_SCANNER))))

    events.sort(key=lambda e: e[0])
    for _, line in events:
        yield line


if __name__ == "__main__":
    for line in list(generate(seed=42, duration_days=7))[:5]:
        print(line)
