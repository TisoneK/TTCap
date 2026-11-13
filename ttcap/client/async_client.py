"""Asynchronous Sofascore table-tennis client (mirrors the sync one)."""

from __future__ import annotations

import asyncio
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


class AsyncSofascoreClient:
    """Async variant of :class:`ttcap.client.SofascoreClient`.

    ::

        async with AsyncSofascoreClient() as client:
            events = await client.live_events()
    """

    def __init__(
        self,
        config: Optional[ClientConfig] = None,
        *,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.config = config or ClientConfig()
        self._limiter = RateLimiter(self.config.min_interval)
        self._http = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers=default_headers(self.config.user_agent) if self.config.user_agent
            else default_headers(),
            transport=transport,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncSofascoreClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    # -- low level ----------------------------------------------------------

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        attempt = 0
        while True:
            delay = self._limiter.wait_time()
            if delay:
                await asyncio.sleep(delay)
            try:
                resp = await self._http.request(method, path, **kwargs)
            except httpx.HTTPError as exc:
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_backoff * (2 ** attempt))
                    attempt += 1
                    continue
                raise TransportError(str(exc)) from exc
            if is_retryable(resp.status_code) and attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_backoff * (2 ** attempt))
                attempt += 1
                continue
            return resp

    async def get_json(self, path: str, **kwargs: Any) -> Any:
        resp = await self._request("GET", path, **kwargs)
        raise_for_status(resp.status_code, str(resp.request.url))
        return resp.json()

    async def head(self, path: str, **kwargs: Any) -> int:
        resp = await self._request("HEAD", path, **kwargs)
        return resp.status_code

    # -- discovery ----------------------------------------------------------

    async def categories(self) -> CategoryList:
        return CategoryList.from_dict(await self.get_json(ep.discovery.categories_all()))

    async def live_tournaments(self) -> dict:
        return (await self.get_json(ep.discovery.live_tournaments())) or {}

    async def live_events(self) -> EventList:
        return EventList.from_dict(await self.get_json(ep.discovery.live_events()))

    async def scheduled_tournaments(self, date: str, page: int = 0) -> Any:
        return await self.get_json(ep.discovery.scheduled_tournaments(date, page))

    # -- tournament ---------------------------------------------------------

    async def tournament_scheduled_events(self, unique_tournament_id: int, date: str) -> EventList:
        return EventList.from_dict(
            await self.get_json(ep.tournament.scheduled_events(unique_tournament_id, date))
        )

    async def standings(self, unique_tournament_id: int, season_id: int) -> Standings:
        return Standings.from_dict(
            await self.get_json(ep.tournament.standings_total(unique_tournament_id, season_id))
        )

    # -- event --------------------------------------------------------------

    async def event(self, event_id: int) -> Event:
        data = await self.get_json(ep.event.detail(event_id))
        return Event.from_dict(data.get("event") if isinstance(data, dict) else None)

    async def event_change_timestamp(self, event_id: int) -> Optional[int]:
        return (await self.event(event_id)).change_timestamp

    async def incidents(self, event_id: int) -> Incidents:
        return Incidents.from_dict(await self.get_json(ep.event.incidents(event_id)))

    async def point_by_point(self, event_id: int) -> PointByPoint:
        return PointByPoint.from_dict(await self.get_json(ep.event.point_by_point(event_id)))

    async def statistics(self, event_id: int) -> Statistics:
        return Statistics.from_dict(await self.get_json(ep.event.statistics(event_id)))

    async def h2h(self, event_id: int) -> H2H:
        return H2H.from_dict(await self.get_json(ep.event.h2h(event_id)))

    async def h2h_events(self, custom_id: str) -> EventList:
        return EventList.from_dict(await self.get_json(ep.event.h2h_events(custom_id)))

    async def team_streaks(self, event_id: int) -> TeamStreaks:
        return TeamStreaks.from_dict(await self.get_json(ep.event.team_streaks(event_id)))

    # -- player -------------------------------------------------------------

    async def player(self, player_id: int) -> Any:
        return await self.get_json(ep.player.detail(player_id))

    async def player_last_events(self, player_id: int, page: int = 0) -> EventList:
        return EventList.from_dict(await self.get_json(ep.player.last_events(player_id, page)))

    async def player_next_events(self, player_id: int, page: int = 0) -> EventList:
        return EventList.from_dict(await self.get_json(ep.player.next_events(player_id, page)))
