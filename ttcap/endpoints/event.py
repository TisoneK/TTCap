"""Event (match) routes and their sub-resources.

A match is addressed two ways:

* numeric ``event_id`` — most sub-resources.
* ``custom_id`` (e.g. ``"LWcesplbj"``) — required by ``/h2h/events``; the
  numeric form 404s there.
"""

from __future__ import annotations


def detail(event_id: int) -> str:
    """Single-event detail (carries the live ``changes`` diff block)."""
    return f"/event/{event_id}"


def incidents(event_id: int) -> str:
    """Set-boundary markers. Per-event availability — may 404."""
    return f"/event/{event_id}/incidents"


def point_by_point(event_id: int) -> str:
    """Rally-by-rally feed. Header-gated: needs the SPA Referer/headers."""
    return f"/event/{event_id}/point-by-point"


def statistics(event_id: int) -> str:
    """Per-set and ALL statistic groups."""
    return f"/event/{event_id}/statistics"


def h2h(event_id: int) -> str:
    """Head-to-head summary (``teamDuel`` wins/draws)."""
    return f"/event/{event_id}/h2h"


def h2h_events(custom_id: str) -> str:
    """Prior meetings — keyed by customId; the numeric id 404s here."""
    return f"/event/{custom_id}/h2h/events"


def team_streaks(event_id: int) -> str:
    """Current form streaks for both players."""
    return f"/event/{event_id}/team-streaks"


def votes(event_id: int) -> str:
    """Crowd votes."""
    return f"/event/{event_id}/votes"
