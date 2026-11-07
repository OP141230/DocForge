"""In-process sliding-window rate limiting.

Research runs and verification passes fan out to third-party services and to
Groq, so they are the expensive operations in DocForge. This limiter is
deliberately simple: a per-process dictionary of timestamps per key.

It is **not** a distributed limiter. With more than one backend worker each
worker keeps its own counters, so the effective limit multiplies by the number
of workers. For production, back this with Redis (or enforce limits in the
reverse proxy) - see docs/phase-5-research.md.
"""
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds its allowance."""

    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = max(1, retry_after_seconds)
        super().__init__(
            f"Rate limit exceeded. Try again in {self.retry_after_seconds}s."
        )


class SlidingWindowRateLimiter:
    """Count events per key inside a rolling time window."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        """Record a hit for ``key`` or raise :class:`RateLimitExceeded`."""
        if limit <= 0:
            return

        now = self._clock()
        window_start = now - window_seconds
        hits = self._hits[key]

        while hits and hits[0] <= window_start:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = int(hits[0] + window_seconds - now) + 1
            raise RateLimitExceeded(retry_after)

        hits.append(now)

    def remaining(self, key: str, limit: int, window_seconds: int = 60) -> int:
        """How many calls remain in the current window (for headers/tests)."""
        now = self._clock()
        window_start = now - window_seconds
        hits = self._hits[key]
        while hits and hits[0] <= window_start:
            hits.popleft()
        return max(0, limit - len(hits))

    def reset(self, key: str | None = None) -> None:
        """Clear counters (used by tests and after configuration reloads)."""
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)


# One limiter per process; buckets are namespaced by route + user id.
limiter = SlidingWindowRateLimiter()


def enforce(bucket: str, user_id: str, limit: int, window_seconds: int = 60) -> Tuple[int, int]:
    """Apply the limit and return ``(remaining, window_seconds)``."""
    key = f"{bucket}:{user_id}"
    limiter.check(key, limit, window_seconds)
    return limiter.remaining(key, limit, window_seconds), window_seconds
