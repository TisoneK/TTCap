"""Typed domain models for the Sofascore table-tennis data.

Every model is a frozen dataclass with a forgiving ``from_dict`` builder
that never raises on missing/null keys. Coded integer fields map to the
enums in :mod:`ttcap.models.enums`.
"""

from __future__ import annotations

from .category import CategoryList
from .common import (
    Category,
    Country,
    Season,
    Sport,
    Tournament,
    UniqueTournament,
)
from .enums import (
    FINISHED,
    IN_PROGRESS,
    NOT_STARTED,
    PointType,
    Scoring,
    Serving,
    WinnerCode,
)
from .event import Event, EventList
from .incident import Incident, Incidents
from .point_by_point import Point, PointByPoint, SetPoints, SetScore
from .relational import (
    Duel,
    H2H,
    StandingGroup,
    StandingRow,
    Standings,
    Streak,
    TeamStreaks,
)
from .score import Changes, EventTime, Periods, Score, Status
from .statistics import StatGroup, StatItem, StatPeriod, Statistics
from .team import Team, TeamColors

__all__ = [
    # common
    "Sport",
    "Country",
    "Category",
    "CategoryList",
    "UniqueTournament",
    "Season",
    "Tournament",
    # team
    "Team",
    "TeamColors",
    # score
    "Score",
    "Status",
    "Periods",
    "Changes",
    "EventTime",
    # event
    "Event",
    "EventList",
    # point-by-point
    "Point",
    "SetScore",
    "SetPoints",
    "PointByPoint",
    # statistics
    "StatItem",
    "StatGroup",
    "StatPeriod",
    "Statistics",
    # incidents
    "Incident",
    "Incidents",
    # relational
    "Duel",
    "H2H",
    "Streak",
    "TeamStreaks",
    "StandingRow",
    "StandingGroup",
    "Standings",
    # enums
    "WinnerCode",
    "Serving",
    "Scoring",
    "PointType",
    "NOT_STARTED",
    "IN_PROGRESS",
    "FINISHED",
]
