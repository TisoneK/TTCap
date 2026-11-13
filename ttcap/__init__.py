"""TTCap — Table Tennis Capture.

A small, respectful client and live-capture toolkit for the table-tennis
data served by the Sofascore backend. The package is organized as focused
subpackages:

* :mod:`ttcap.endpoints` — URL path builders for the TT route subset.
* :mod:`ttcap.models` — typed, forgiving domain models.
* :mod:`ttcap.client` — sync and async HTTP clients (rate-limited).
* :mod:`ttcap.capture` — a live-match polling watcher and snapshots.

This project is an independent, original implementation. It is not
affiliated with, endorsed by, or connected to Sofascore. Use it
observationally and human-rate; respect the service's Terms and
``robots.txt``. See the README's "Responsible use" section.
"""

from __future__ import annotations

from . import endpoints
from .capture import LiveMatchWatcher, MatchSnapshot, SnapshotDiff
from .client import AsyncSofascoreClient, ClientConfig, SofascoreClient
from .constants import API_BASE, SPORT, SPORT_ID, WEB_BASE
from .errors import (
    BlockedError,
    HTTPError,
    NotFoundError,
    ParseError,
    TransportError,
    TTCapError,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "SofascoreClient",
    "AsyncSofascoreClient",
    "ClientConfig",
    "LiveMatchWatcher",
    "MatchSnapshot",
    "SnapshotDiff",
    "endpoints",
    "SPORT",
    "SPORT_ID",
    "API_BASE",
    "WEB_BASE",
    "TTCapError",
    "HTTPError",
    "NotFoundError",
    "BlockedError",
    "TransportError",
    "ParseError",
]
