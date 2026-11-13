"""Default request headers.

Some sub-resources (notably ``/event/{id}/point-by-point``) return 404 to
a bare request and 200 only with the SPA's ``Referer`` and browser-like
headers. These defaults reproduce that context. They are **not** an
attempt to defeat anti-bot protection — if you are challenged, stop and
respect the service.
"""

from __future__ import annotations

from typing import Dict

from ..constants import WEB_BASE

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def default_headers(user_agent: str = DEFAULT_USER_AGENT) -> Dict[str, str]:
    return {
        "User-Agent": user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"{WEB_BASE}/",
        "Origin": WEB_BASE,
        "Cache-Control": "no-cache",
    }
