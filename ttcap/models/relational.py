"""Relational views — head-to-head, form streaks, standings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ._parse import as_int
from .team import Team


# --- head-to-head ----------------------------------------------------------

@dataclass(frozen=True)
class Duel:
    home_wins: Optional[int]
    away_wins: Optional[int]
    draws: Optional[int]

    @classmethod
    def from_dict(cls, d: Any) -> "Duel":
        d = d or {}
        return cls(
            home_wins=as_int(d.get("homeWins")),
            away_wins=as_int(d.get("awayWins")),
            draws=as_int(d.get("draws")),
        )


@dataclass(frozen=True)
class H2H:
    team_duel: Optional[Duel]

    @classmethod
    def from_dict(cls, d: Any) -> "H2H":
        d = d or {}
        td = d.get("teamDuel")
        return cls(team_duel=Duel.from_dict(td) if td else None)


# --- form streaks ----------------------------------------------------------

@dataclass(frozen=True)
class Streak:
    name: Optional[str]
    value: Any
    team: Optional[str]       # "home" / "away"
    continued: Optional[bool]

    @classmethod
    def from_dict(cls, d: Any) -> "Streak":
        d = d or {}
        return cls(
            name=d.get("name"),
            value=d.get("value"),
            team=d.get("team"),
            continued=d.get("continued"),
        )


@dataclass(frozen=True)
class TeamStreaks:
    general: List[Streak] = field(default_factory=list)
    head2head: List[Streak] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "TeamStreaks":
        d = d or {}
        return cls(
            general=[Streak.from_dict(s) for s in (d.get("general") or [])],
            head2head=[Streak.from_dict(s) for s in (d.get("head2head") or [])],
        )


# --- standings (group-stage only) -----------------------------------------

@dataclass(frozen=True)
class StandingRow:
    team: Optional[Team]
    position: Optional[int]
    matches: Optional[int]
    wins: Optional[int]
    losses: Optional[int]
    points: Optional[int]
    promotion: Any

    @classmethod
    def from_dict(cls, d: Any) -> "StandingRow":
        d = d or {}
        return cls(
            team=Team.from_dict(d.get("team")) if d.get("team") else None,
            position=as_int(d.get("position")),
            matches=as_int(d.get("matches")),
            wins=as_int(d.get("wins")),
            losses=as_int(d.get("losses")),
            points=as_int(d.get("points")),
            promotion=d.get("promotion"),
        )


@dataclass(frozen=True)
class StandingGroup:
    is_group: Optional[bool]
    group_name: Optional[str]
    rows: List[StandingRow] = field(default_factory=list)
    updated_at: Optional[int] = None

    @classmethod
    def from_dict(cls, d: Any) -> "StandingGroup":
        d = d or {}
        return cls(
            is_group=d.get("isGroup"),
            group_name=d.get("groupName"),
            rows=[StandingRow.from_dict(r) for r in (d.get("rows") or [])],
            updated_at=as_int(d.get("updatedAtTimestamp")),
        )


@dataclass(frozen=True)
class Standings:
    groups: List[StandingGroup] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "Standings":
        d = d or {}
        return cls(groups=[StandingGroup.from_dict(g) for g in (d.get("standings") or [])])

    def __iter__(self):
        return iter(self.groups)

    def __len__(self) -> int:
        return len(self.groups)
