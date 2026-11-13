"""Synchronous Sofascore table-tennis client."""

from __future__ import annotations

import time
from typing import Any, List, Optional

import httpx

from .. import endpoints as ep
from ..errors import NotFoundError, TransportError
from ..models import (
    CategoryList,
    Event,
    EventList,
    H2H,
    Incidents,
    Player,
    PointByPoint,
    ScheduledTournaments,
    Standings,
    Statistics,
    TeamStreaks,
)
from .base import ClientConfig, RateLimiter, is_retryable, raise_for_status
from .headers import default_headers


class SofascoreClient:
    """A respectful, typed HTTP client for the TT backend.

    Use as a context manager so the underlying connection pool is closed::

        with SofascoreClient() as client:
            for ev in client.live_events():
                print(ev.label(), ev.score_line())
    """

    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        *,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.config = config or ClientConfig()
        self._limiter = RateLimiter(self.config.min_interval)
        self._http = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=default_headers(self.config.user_agent) if self.config.user_agent
            else default_headers(),
            transport=transport,
            follow_redirects=True,
        )

    # -- lifecycle ----------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SofascoreClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- low level ----------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        attempt = 0
        while True:
            delay = self._limiter.wait_time()
            if delay:
                time.sleep(delay)
            try:
                resp = self._http.request(method, path, **kwargs)
            except httpx.HTTPError as exc:  # transport-level
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_backoff * (2 ** attempt))
                    attempt += 1
                    continue
                raise TransportError(str(exc)) from exc
            if is_retryable(resp.status_code) and attempt < self.config.max_retries:
                time.sleep(self.config.retry_backoff * (2 ** attempt))
                attempt += 1
                continue
            return resp

    def get_json(self, path: str, **kwargs: Any) -> Any:
        """GET ``path`` and return parsed JSON, raising on non-2xx."""
        resp = self._request("GET", path, **kwargs)
        raise_for_status(resp.status_code, str(resp.request.url))
        return resp.json()

    def head(self, path: str, **kwargs: Any) -> int:
        """Cheap freshness check — returns the status code (no body)."""
        resp = self._request("HEAD", path, **kwargs)
        return resp.status_code

    # -- discovery ----------------------------------------------------------

    def categories(self) -> CategoryList:
        """Every category (country/region) carrying TT events."""
        return CategoryList.from_dict(self.get_json(ep.discovery.categories_all()))

    def categories_on(self, date: str, tz_offset: int = 0) -> CategoryList:
        """Categories that have TT events on a date (tz offset in seconds)."""
        return CategoryList.from_dict(
            self.get_json(ep.discovery.categories_on_date(date, tz_offset))
        )

    def live_tournaments(self) -> dict:
        """Raw ``{tournamentId: liveEventCount}`` map."""
        return self.get_json(ep.discovery.live_tournaments()) or {}

    def live_events(self) -> EventList:
        """All table-tennis matches currently in progress."""
        return EventList.from_dict(self.get_json(ep.discovery.live_events()))

    def scheduled_tournaments(self, date: str, page: int = 1) -> ScheduledTournaments:
        """The daily schedule index: tournaments active on a date with
        per-timezone event counts (pages are 1-indexed). Not the events —
        use :meth:`fixtures` for those."""
        return ScheduledTournaments.from_dict(
            self.get_json(ep.discovery.scheduled_tournaments(date, page))
        )

    def scheduled_tournament_ids(self, date: str, max_pages: int = 10) -> List[int]:
        """Every distinct uniqueTournament id with events on ``date``,
        paging until ``hasNextPage`` is false (bounded by ``max_pages``)."""
        ids: List[int] = []
        seen: set = set()
        page = 1
        while page <= max_pages:
            index = self.scheduled_tournaments(date, page)
            for utid in index.unique_tournament_ids():
                if utid not in seen:
                    seen.add(utid)
                    ids.append(utid)
            if not index.has_next_page:
                break
            page += 1
        return ids

    # -- fixtures (the core: every match on a date) -------------------------

    def fixtures(self, date: str, *, max_tournaments: Optional[int] = None,
                 max_pages: int = 10) -> EventList:
        """All TT matches on ``date`` (YYYY-MM-DD), any status.

        Two-step, mirroring the web client: read the schedule index for the
        date, then fetch each tournament's ``scheduled-events`` and merge
        (de-duped by id). This makes one request per tournament, so it is
        paced by the client's rate limiter; cap it with ``max_tournaments``.
        Combine with :meth:`EventList.scheduled`/``.live``/``.finished``.
        """
        ids = self.scheduled_tournament_ids(date, max_pages=max_pages)
        if max_tournaments is not None:
            ids = ids[:max_tournaments]
        lists: List[EventList] = []
        for utid in ids:
            try:
                lists.append(self.tournament_scheduled_events(utid, date))
            except NotFoundError:
                continue
        return EventList.merge(lists)

    def results(self, date: str, **kwargs: Any) -> EventList:
        """Finished TT matches on a date."""
        return self.fixtures(date, **kwargs).finished()

    # -- tournament ---------------------------------------------------------

    def tournament_scheduled_events(self, unique_tournament_id: int, date: str) -> EventList:
        return EventList.from_dict(
            self.get_json(ep.tournament.scheduled_events(unique_tournament_id, date))
        )

    def standings(self, unique_tournament_id: int, season_id: int) -> Standings:
        """Group-stage standings (raises NotFoundError for non-group comps)."""
        return Standings.from_dict(
            self.get_json(ep.tournament.standings_total(unique_tournament_id, season_id))
        )

    # -- event --------------------------------------------------------------

    def event(self, event_id: int) -> Event:
        data = self.get_json(ep.event.detail(event_id))
        return Event.from_dict(data.get("event") if isinstance(data, dict) else None)

    def event_change_timestamp(self, event_id: int) -> Optional[int]:
        """Only the live ``changes.changeTimestamp`` — the change signal."""
        return self.event(event_id).change_timestamp

    def incidents(self, event_id: int) -> Incidents:
        return Incidents.from_dict(self.get_json(ep.event.incidents(event_id)))

    def point_by_point(self, event_id: int) -> PointByPoint:
        return PointByPoint.from_dict(self.get_json(ep.event.point_by_point(event_id)))

    def statistics(self, event_id: int) -> Statistics:
        return Statistics.from_dict(self.get_json(ep.event.statistics(event_id)))

    def h2h(self, event_id: int) -> H2H:
        return H2H.from_dict(self.get_json(ep.event.h2h(event_id)))

    def h2h_events(self, custom_id: str) -> EventList:
        """Prior meetings — keyed by customId (the numeric id 404s)."""
        return EventList.from_dict(self.get_json(ep.event.h2h_events(custom_id)))

    def team_streaks(self, event_id: int) -> TeamStreaks:
        return TeamStreaks.from_dict(self.get_json(ep.event.team_streaks(event_id)))

    # -- player -------------------------------------------------------------

    def player(self, player_id: int) -> Player:
        """Player (a ``team`` of type 1) detail."""
        return Player.from_dict(self.get_json(ep.player.detail(player_id)))

    def player_unique_tournaments(self, player_id: int) -> Any:
        """Raw list of competitions the player has appeared in."""
        return self.get_json(ep.player.unique_tournaments(player_id))

    def player_standings_seasons(self, player_id: int) -> Any:
        """Which competitions/seasons expose a standings table for the player."""
        return self.get_json(ep.player.standings_seasons(player_id))

    def player_last_events(self, player_id: int, page: int = 0) -> EventList:
        return EventList.from_dict(self.get_json(ep.player.last_events(player_id, page)))

    def player_next_events(self, player_id: int, page: int = 0) -> EventList:
        """Upcoming events (raises NotFoundError when none scheduled)."""
        return EventList.from_dict(self.get_json(ep.player.next_events(player_id, page)))
