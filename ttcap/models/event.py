"""The event (match) — the central entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from ._parse import as_int
from .common import Season, Tournament
from .enums import WinnerCode
from .score import Changes, EventTime, Periods, Score, Status
from .team import Team


@dataclass(frozen=True)
class Event:
    id: Optional[int]
    custom_id: Optional[str]
    slug: Optional[str]
    tournament: Optional[Tournament]
    season: Optional[Season]
    status: Optional[Status]
    winner_code: Optional[int]
    home_team: Optional[Team]
    away_team: Optional[Team]
    home_score: Optional[Score]
    away_score: Optional[Score]
    start_timestamp: Optional[int]
    time: Optional[EventTime]
    periods: Optional[Periods]
    changes: Optional[Changes]
    default_period_count: Optional[int]
    has_bet365_live_stream: Optional[bool]
    feed_locked: Optional[bool]
    #: the untouched source object, for fields the model doesn't surface
    raw: Any = None

    @classmethod
    def from_dict(cls, d: Any) -> "Event":
        d = d or {}
        return cls(
            id=as_int(d.get("id")),
            custom_id=d.get("customId"),
            slug=d.get("slug"),
            tournament=Tournament.from_dict(d.get("tournament")) if d.get("tournament") else None,
            season=Season.from_dict(d.get("season")) if d.get("season") else None,
            status=Status.from_dict(d.get("status")) if d.get("status") else None,
            winner_code=as_int(d.get("winnerCode")),
            home_team=Team.from_dict(d.get("homeTeam")) if d.get("homeTeam") else None,
            away_team=Team.from_dict(d.get("awayTeam")) if d.get("awayTeam") else None,
            home_score=Score.from_dict(d.get("homeScore")) if d.get("homeScore") else None,
            away_score=Score.from_dict(d.get("awayScore")) if d.get("awayScore") else None,
            start_timestamp=as_int(d.get("startTimestamp")),
            time=EventTime.from_dict(d.get("time")) if d.get("time") else None,
            periods=Periods.from_dict(d.get("periods")) if d.get("periods") else None,
            changes=Changes.from_dict(d.get("changes")) if d.get("changes") else None,
            default_period_count=as_int(d.get("defaultPeriodCount")),
            has_bet365_live_stream=d.get("hasBet365LiveStream"),
            feed_locked=d.get("feedLocked"),
            raw=d,
        )

    # -- convenience --------------------------------------------------------

    @property
    def winner(self) -> WinnerCode:
        return WinnerCode.from_code(self.winner_code)

    @property
    def is_live(self) -> bool:
        return bool(self.status and self.status.is_live)

    @property
    def is_finished(self) -> bool:
        return bool(self.status and self.status.is_finished)

    @property
    def is_scheduled(self) -> bool:
        return bool(self.status and self.status.is_scheduled)

    @property
    def change_timestamp(self) -> Optional[int]:
        return self.changes.timestamp if self.changes else None

    def score_line(self) -> str:
        """A compact ``3 - 1`` sets line, best-effort."""
        h = self.home_score.current if self.home_score else None
        a = self.away_score.current if self.away_score else None
        return f"{h if h is not None else '-'} - {a if a is not None else '-'}"

    def label(self) -> str:
        home = self.home_team.display_name if self.home_team else "?"
        away = self.away_team.display_name if self.away_team else "?"
        return f"{home} vs {away}"

    def set_scores(self) -> List[str]:
        """Per-set point lines like ``11-5`` in set order."""
        out: List[str] = []
        hp = self.home_score.periods if self.home_score else {}
        ap = self.away_score.periods if self.away_score else {}
        for i in sorted(set(hp) | set(ap)):
            out.append(f"{hp.get(i, '-')}-{ap.get(i, '-')}")
        return out


@dataclass(frozen=True)
class EventList:
    """Wrapper for the many ``{"events": [...]}`` list responses.

    Also carries fixture/status filters, since the same list shape backs
    schedules, results, live lists and a player's recent games.
    """

    events: List[Event]

    @classmethod
    def from_dict(cls, d: Any) -> "EventList":
        d = d or {}
        return cls(events=[Event.from_dict(e) for e in (d.get("events") or [])])

    @classmethod
    def merge(cls, lists: "List[EventList]") -> "EventList":
        """Concatenate several lists, de-duplicating by event id."""
        seen: set = set()
        events: List[Event] = []
        for lst in lists:
            for ev in lst.events:
                if ev.id is not None and ev.id in seen:
                    continue
                if ev.id is not None:
                    seen.add(ev.id)
                events.append(ev)
        return cls(events=events)

    # -- filters ------------------------------------------------------------

    def live(self) -> "EventList":
        return EventList([e for e in self.events if e.is_live])

    def scheduled(self) -> "EventList":
        return EventList([e for e in self.events if e.is_scheduled])

    def finished(self) -> "EventList":
        return EventList([e for e in self.events if e.is_finished])

    def by_unique_tournament(self, unique_tournament_id: int) -> "EventList":
        return EventList([
            e for e in self.events
            if e.tournament and e.tournament.unique_tournament_id == unique_tournament_id
        ])

    def by_category(self, category_id: int) -> "EventList":
        out = []
        for e in self.events:
            cat = e.tournament.category if e.tournament else None
            if cat and cat.id == category_id:
                out.append(e)
        return EventList(out)

    def sorted_by_start(self) -> "EventList":
        return EventList(sorted(self.events, key=lambda e: e.start_timestamp or 0))

    def __iter__(self):
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)
