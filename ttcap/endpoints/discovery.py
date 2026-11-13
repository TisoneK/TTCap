"""Sport-level discovery routes (categories, live, schedule)."""

from __future__ import annotations

from ..constants import SPORT


def categories_all() -> str:
    """All categories (countries + 'International') carrying TT events."""
    return f"/sport/{SPORT}/categories/all"


def categories_on_date(date: str, tz_offset: int) -> str:
    """Categories active on ``date`` (YYYY-MM-DD) for a tz offset in seconds."""
    return f"/sport/{SPORT}/{date}/{tz_offset}/categories"


def live_tournaments() -> str:
    """Map of ``{tournamentId: liveEventCount}`` for TT."""
    return f"/sport/{SPORT}/live-tournaments"


def live_events() -> str:
    """All live TT events as full event objects."""
    return f"/sport/{SPORT}/events/live"


def scheduled_tournaments(date: str, page: int = 0) -> str:
    """Tournaments (with their events) scheduled on a date, paginated."""
    return f"/sport/{SPORT}/scheduled-tournaments/{date}/page/{page}"


def default_unique_tournaments(country_code: str) -> str:
    """Editorially featured tournaments for a country (alpha2, lowercased)."""
    return f"/config/default-unique-tournaments/{country_code.lower()}/{SPORT}"
