"""Rally-by-rally feed: one object per set, newest set first."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ._parse import as_int
from .enums import PointType, Scoring, Serving


@dataclass(frozen=True)
class Point:
    """One rally: the running score after it, plus each side's outcome."""

    home_point: Optional[int]
    away_point: Optional[int]
    home_point_type: PointType
    away_point_type: PointType

    @classmethod
    def from_dict(cls, d: Any) -> "Point":
        d = d or {}
        return cls(
            home_point=as_int(d.get("homePoint")),
            away_point=as_int(d.get("awayPoint")),
            home_point_type=PointType.from_code(d.get("homePointType")),
            away_point_type=PointType.from_code(d.get("awayPointType")),
        )

    @property
    def winner(self) -> Optional[str]:
        if self.home_point_type.is_won:
            return "home"
        if self.away_point_type.is_won:
            return "away"
        return None


@dataclass(frozen=True)
class SetScore:
    home_score: Optional[int]
    away_score: Optional[int]
    serving: Serving
    scoring: Scoring

    @classmethod
    def from_dict(cls, d: Any) -> "SetScore":
        d = d or {}
        return cls(
            home_score=as_int(d.get("homeScore")),
            away_score=as_int(d.get("awayScore")),
            serving=Serving.from_code(d.get("serving")),
            scoring=Scoring.from_code(d.get("scoring")),
        )


@dataclass(frozen=True)
class SetPoints:
    set_number: Optional[int]
    points: List[Point] = field(default_factory=list)
    score: Optional[SetScore] = None

    @classmethod
    def from_dict(cls, d: Any) -> "SetPoints":
        d = d or {}
        return cls(
            set_number=as_int(d.get("set")),
            points=[Point.from_dict(p) for p in (d.get("points") or [])],
            score=SetScore.from_dict(d.get("score")) if d.get("score") else None,
        )

    @property
    def rally_count(self) -> int:
        return len(self.points)


@dataclass(frozen=True)
class PointByPoint:
    sets: List[SetPoints] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "PointByPoint":
        d = d or {}
        return cls(sets=[SetPoints.from_dict(s) for s in (d.get("pointByPoint") or [])])

    def __iter__(self):
        return iter(self.sets)

    def __len__(self) -> int:
        return len(self.sets)

    def in_play_order(self) -> List[SetPoints]:
        """Sets oldest-first (the feed delivers newest-first)."""
        return sorted(self.sets, key=lambda s: s.set_number or 0)

    @property
    def total_rallies(self) -> int:
        return sum(s.rally_count for s in self.sets)
