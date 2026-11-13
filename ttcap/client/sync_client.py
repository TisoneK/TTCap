"""Synchronous Sofascore table-tennis client."""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from .. import endpoints as ep
from ..errors import TransportError
from ..models import (
    CategoryList,
    Event,
    EventList,
    H2H,
    Incidents,
    PointByPoint,
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
        return CategoryList.from_dict(self.get_json(ep.discovery.categories_all()))

    def live_tournaments(self) -> dict:
        """Raw ``{tournamentId: liveEventCount}`` map."""
        return self.get_json(ep.discovery.live_tournaments()) or {}

    def live_events(self) -> EventList:
        return EventList.from_dict(self.get_json(ep.discovery.live_events()))

    def scheduled_tournaments(self, date: str, page: int = 0) -> Any:
        return self.get_json(ep.discovery.scheduled_tournaments(date, page))

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

    def player(self, player_id: int) -> Any:
        return self.get_json(ep.player.detail(player_id))

    def player_last_events(self, player_id: int, page: int = 0) -> EventList:
        return EventList.from_dict(self.get_json(ep.player.last_events(player_id, page)))

    def player_next_events(self, player_id: int, page: int = 0) -> EventList:
        """Upcoming events (raises NotFoundError when none scheduled)."""
        return EventList.from_dict(self.get_json(ep.player.next_events(player_id, page)))
