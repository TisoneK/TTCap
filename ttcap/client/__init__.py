"""HTTP clients for the Sofascore table-tennis backend.

Two clients share configuration, rate limiting and exception mapping:

* :class:`SofascoreClient` — synchronous (``httpx.Client``).
* :class:`AsyncSofascoreClient` — asynchronous (``httpx.AsyncClient``).
"""

from __future__ import annotations

from .async_client import AsyncSofascoreClient
from .base import ClientConfig, RateLimiter
from .headers import DEFAULT_USER_AGENT, default_headers
from .sync_client import SofascoreClient

__all__ = [
    "SofascoreClient",
    "AsyncSofascoreClient",
    "ClientConfig",
    "RateLimiter",
    "default_headers",
    "DEFAULT_USER_AGENT",
]
