"""
A small in-memory rate limiter (sliding window per client IP and bucket).

Good for a single server process (the default deployment). If you run several
instances behind a load balancer, put the limits in Redis or at the proxy instead.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import settings

_UNITS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
_lock = threading.Lock()
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def parse(rule: str) -> tuple[int, int]:
    """'10/minute' -> (10, 60)"""
    count, unit = rule.split("/")
    return int(count), _UNITS[unit.strip().rstrip("s")]


def client_ip(request: Request) -> str:
    # Behind Render/Railway/most proxies the real client is the first X-Forwarded-For entry.
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(bucket: str, rule: str, key: str) -> None:
    limit, window = parse(rule)
    now = time.monotonic()
    with _lock:
        q = _hits[(bucket, key)]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            retry = int(window - (now - q[0])) + 1
            raise HTTPException(429, f"Too many requests. Please wait {retry} seconds and try again.",
                                headers={"Retry-After": str(retry)})
        q.append(now)


def reset() -> None:
    with _lock:
        _hits.clear()


def limiter(bucket: str):
    """FastAPI dependency factory: Depends(limiter("auth"))."""
    def dep(request: Request) -> None:
        rule = {"auth": settings.rate_limit_auth, "ai": settings.rate_limit_ai, "code": settings.rate_limit_code}[bucket]
        check(bucket, rule, client_ip(request))
    return dep
