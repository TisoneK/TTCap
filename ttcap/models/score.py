"""Score, status, periods, time and the live ``changes`` diff block.

The score model (per the reconstruction):

* ``current`` / ``display`` = **sets won** (the match score).
* ``period1``…``period7`` = **points** scored in each set.
* ``normaltime`` = sets won in normal time (= ``current`` for TT).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ._parse import as_int
from .enums import FINISHED, IN_PROGRESS, NOT_STARTED

MAX_SETS = 7  # best-of-7 ceiling seen in the period labels


@dataclass(frozen=True)
class Score:
    current: Optional[int]
    display: Optional[int]
    normaltime: Optional[int]
    #: points per set, index 1..7 -> value (missing sets omitted)
    periods: Dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Any) -> "Score":
        d = d or {}
        periods: Dict[int, int] = {}
        for i in range(1, MAX_SETS + 1):
            val = as_int(d.get(f"period{i}"))
            if val is not None:
                periods[i] = val
        return cls(
            current=as_int(d.get("current")),
            display=as_int(d.get("display")),
            normaltime=as_int(d.get("normaltime")),
            periods=periods,
        )

    @property
    def sets_won(self) -> Optional[int]:
        return self.current

    def set_points(self, set_number: int) -> Optional[int]:
        return self.periods.get(set_number)

    @property
    def completed_sets(self) -> int:
        return len(self.periods)


@dataclass(frozen=True)
class Status:
    code: Optional[int]
    description: Optional[str]
    type: Optional[str]

    @classmethod
    def from_dict(cls, d: Any) -> "Status":
        d = d or {}
        return cls(
            code=as_int(d.get("code")),
            description=d.get("description"),
            type=d.get("type"),
        )

    @property
    def is_live(self) -> bool:
        return self.type == IN_PROGRESS

    @property
    def is_finished(self) -> bool:
        return self.type == FINISHED

    @property
    def is_scheduled(self) -> bool:
        return self.type == NOT_STARTED


@dataclass(frozen=True)
class Periods:
    """Human labels for each period, e.g. ``{1: '1st set'}``."""

    labels: Dict[int, str] = field(default_factory=dict)
    current: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Any) -> "Periods":
        d = d or {}
        labels: Dict[int, str] = {}
        for i in range(1, MAX_SETS + 1):
            label = d.get(f"period{i}")
            if label:
                labels[i] = label
        return cls(labels=labels, current=d.get("current"))


@dataclass(frozen=True)
class Changes:
    """The server-side diff naming exactly which fields last changed."""

    fields: List[str] = field(default_factory=list)
    timestamp: Optional[int] = None

    @classmethod
    def from_dict(cls, d: Any) -> "Changes":
        d = d or {}
        return cls(
            fields=list(d.get("changes") or []),
            timestamp=as_int(d.get("changeTimestamp")),
        )


@dataclass(frozen=True)
class EventTime:
    current_period_start: Optional[int]

    @classmethod
    def from_dict(cls, d: Any) -> "EventTime":
        d = d or {}
        return cls(current_period_start=as_int(d.get("currentPeriodStartTimestamp")))
