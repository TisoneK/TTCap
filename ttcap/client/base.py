"""Shared client plumbing: config, rate limiting, status mapping.

The sync and async clients share response/exception handling and a
minimum-interval rate limiter so a watcher cannot accidentally hammer the
service. Defaults are deliberately conservative (human-rate).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from ..constants import API_BASE
from ..errors import BlockedError, HTTPError, NotFoundError

#: Floor between any two requests, in seconds. The service is observed
#: behind Cloudflare; keep observation light and human-rate.
DEFAULT_MIN_INTERVAL = 1.0
DEFAULT_TIMEOUT = 15.0


@dataclass
class ClientConfig:
    base_url: str = API_BASE
    timeout: float = DEFAULT_TIMEOUT
    min_interval: float = DEFAULT_MIN_INTERVAL
    user_agent: Optional[str] = None
    max_retries: int = 2
    #: base backoff (seconds) applied between retries, doubled each time
    retry_backoff: float = 1.5


class RateLimiter:
    """Thread-safe minimum-interval gate (monotonic clock)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = max(0.0, min_interval)
        self._last = 0.0
        self._lock = threading.Lock()

    def wait_time(self) -> float:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            remaining = self.min_interval - elapsed
            self._last = now + max(0.0, remaining)
            return max(0.0, remaining)


def raise_for_status(status: int, url: str) -> None:
    """Map an HTTP status to a TTCap exception (no-op on success)."""
    if 200 <= status < 300:
        return
    if status == 404:
        raise NotFoundError(status, url)
    if status == 403:
        raise BlockedError(status, url)
    raise HTTPError(status, url)


def is_retryable(status: int) -> bool:
    """Transient server/edge statuses worth a backoff retry."""
    return status in (429, 500, 502, 503, 504)
