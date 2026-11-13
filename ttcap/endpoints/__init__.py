"""URL path builders for the table-tennis slice of the Sofascore backend.

Builders return *paths* (joined to :data:`ttcap.constants.API_BASE` by the
client), except the SPA page URLs in :mod:`.player`, which are absolute.

The builders are grouped into submodules by concern and also re-exported
here as namespaces, so both styles work::

    from ttcap import endpoints
    endpoints.event.detail(123)
    endpoints.discovery.live_events()
"""

from __future__ import annotations

from ..constants import API_BASE, SPORT, SPORT_ID, WEB_BASE
from . import discovery, event, player, tournament

__all__ = [
    "discovery",
    "event",
    "player",
    "tournament",
    "API_BASE",
    "WEB_BASE",
    "SPORT",
    "SPORT_ID",
]
