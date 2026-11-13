"""The sport-wide daily schedule index.

``/sport/table-tennis/scheduled-tournaments/{date}/page/{n}`` (pages are
**1-indexed** — page 0 is a 404) returns the *tournaments* that have
events on a date, each with a per-timezone event **count** — it does
**not** carry the events themselves:

```json
{
  "scheduled": [
    { "tournament": { ..., "uniqueTournament": {"id": 2122} },
      "timezoneEventCount": { "0": 30, "-28800": 30, ... } }
  ],
  "hasNextPage": false
}
```

To get the actual matches for a date, fetch each tournament's
``/unique-tournament/{uniqueTournament.id}/scheduled-events/{date}``.
:meth:`ttcap.client.SofascoreClient.fixtures` does exactly that.

Verified against the live API on 2026-11-13.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ._parse import as_int
from .common import Tournament


@dataclass(frozen=True)
class ScheduledTournament:
    tournament: Optional[Tournament]
    #: event count keyed by timezone offset in seconds (e.g. 0 = UTC, -28800 = PST-8)
    timezone_event_count: Dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Any) -> "ScheduledTournament":
        d = d or {}
        counts: Dict[int, int] = {}
        raw = d.get("timezoneEventCount") or {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                ik = as_int(k)
                iv = as_int(v)
                if ik is not None and iv is not None:
                    counts[ik] = iv
        return cls(
            tournament=Tournament.from_dict(d.get("tournament")) if d.get("tournament") else None,
            timezone_event_count=counts,
        )

    @property
    def unique_tournament_id(self) -> Optional[int]:
        return self.tournament.unique_tournament_id if self.tournament else None

    @property
    def name(self) -> Optional[str]:
        return self.tournament.name if self.tournament else None

    def event_count(self, tz_offset: int = 0) -> int:
        """Events on the date for a timezone offset (seconds). Falls back
        to UTC (0), then to the max across offsets, then 0."""
        if tz_offset in self.timezone_event_count:
            return self.timezone_event_count[tz_offset]
        if 0 in self.timezone_event_count:
            return self.timezone_event_count[0]
        return max(self.timezone_event_count.values(), default=0)


@dataclass(frozen=True)
class ScheduledTournaments:
    scheduled: List[ScheduledTournament] = field(default_factory=list)
    has_next_page: bool = False

    @classmethod
    def from_dict(cls, d: Any) -> "ScheduledTournaments":
        d = d or {}
        return cls(
            scheduled=[ScheduledTournament.from_dict(s) for s in (d.get("scheduled") or [])],
            has_next_page=bool(d.get("hasNextPage")),
        )

    def unique_tournament_ids(self) -> List[int]:
        """Distinct uniqueTournament ids on the page, first-seen order."""
        out: List[int] = []
        seen: set = set()
        for s in self.scheduled:
            utid = s.unique_tournament_id
            if utid is not None and utid not in seen:
                seen.add(utid)
                out.append(utid)
        return out

    def total_events(self, tz_offset: int = 0) -> int:
        return sum(s.event_count(tz_offset) for s in self.scheduled)

    def __iter__(self):
        return iter(self.scheduled)

    def __len__(self) -> int:
        return len(self.scheduled)
