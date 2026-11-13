"""Tournament- and season-scoped routes.

Two tournament ids are distinct and must not be confused:

* ``unique_tournament_id`` — the recurring competition (e.g. TT Elite
  Series, 19041). Used by ``/unique-tournament/{id}/…`` routes.
* ``tournament_id`` — the season-scoped instance (e.g. 99281). Used by
  the live-count maps from :mod:`ttcap.endpoints.discovery`.
"""

from __future__ import annotations


def scheduled_events(unique_tournament_id: int, date: str) -> str:
    """A unique tournament's events on a date (YYYY-MM-DD)."""
    return f"/unique-tournament/{unique_tournament_id}/scheduled-events/{date}"


def standings_total(unique_tournament_id: int, season_id: int) -> str:
    """Group-stage standings.

    Present only for group-phase competitions; 404 for rolling series and
    single-elimination knockouts.
    """
    return (
        f"/unique-tournament/{unique_tournament_id}"
        f"/season/{season_id}/standings/total"
    )


def cup_trees(unique_tournament_id: int, season_id: int) -> str:
    """Knockout bracket. No rendered TT bracket observed — typically 404."""
    return f"/unique-tournament/{unique_tournament_id}/season/{season_id}/cuptrees"
