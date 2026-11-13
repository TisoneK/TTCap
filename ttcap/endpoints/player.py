"""Player routes and SPA page URLs.

A player is a ``team`` of ``type:1``; its routes live under ``/team/{id}``.
There is no world-ranking route for table tennis (the cross-sport
rankings API 404s for TT players) — the nearest thing is group-stage
standings plus ``userCount`` popularity.
"""

from __future__ import annotations

from ..constants import SPORT, WEB_BASE


def detail(player_id: int) -> str:
    """Player detail (``team`` + ``pregameForm`` + ``editorEntity``)."""
    return f"/team/{player_id}"


def last_events(player_id: int, page: int = 0) -> str:
    """Recent results, paginated (newest first)."""
    return f"/team/{player_id}/events/last/{page}"


def next_events(player_id: int, page: int = 0) -> str:
    """Upcoming events; 404 when the player has none scheduled."""
    return f"/team/{player_id}/events/next/{page}"


def unique_tournaments(player_id: int) -> str:
    """Competitions the player has appeared in."""
    return f"/team/{player_id}/unique-tournaments/all"


def featured_event(player_id: int) -> str:
    return f"/team/{player_id}/featured-event"


def standings_seasons(player_id: int) -> str:
    """Which competitions/seasons expose a standings table for the player."""
    return f"/team/{player_id}/standings/seasons"


# --- SPA page URLs (useful as a Referer for header-gated routes) ----------

def match_page(custom_id: str) -> str:
    return f"{WEB_BASE}/{SPORT}/match/{custom_id}"


def sport_page() -> str:
    return f"{WEB_BASE}/{SPORT}"
