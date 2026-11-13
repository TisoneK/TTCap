"""Team / player model.

In table tennis a *player* is a ``team`` of ``type:1``; a doubles pair is
also a team. The same shape covers both, so the model is named ``Team``
with a convenience :pyattr:`Team.is_player`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ._parse import as_int
from .common import Country, Sport


@dataclass(frozen=True)
class TeamColors:
    primary: Optional[str]
    secondary: Optional[str]
    text: Optional[str]

    @classmethod
    def from_dict(cls, d: Any) -> "TeamColors":
        d = d or {}
        return cls(primary=d.get("primary"), secondary=d.get("secondary"), text=d.get("text"))


@dataclass(frozen=True)
class Team:
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    short_name: Optional[str]
    full_name: Optional[str]
    name_code: Optional[str]
    gender: Optional[str]
    type: Optional[int]
    national: Optional[bool]
    country: Optional[Country]
    sport: Optional[Sport]
    colors: Optional[TeamColors]

    @classmethod
    def from_dict(cls, d: Any) -> "Team":
        d = d or {}
        return cls(
            id=as_int(d.get("id")),
            name=d.get("name"),
            slug=d.get("slug"),
            short_name=d.get("shortName"),
            full_name=d.get("fullName"),
            name_code=d.get("nameCode"),
            gender=d.get("gender"),
            type=as_int(d.get("type")),
            national=d.get("national"),
            country=Country.from_dict(d.get("country")) if d.get("country") else None,
            sport=Sport.from_dict(d.get("sport")) if d.get("sport") else None,
            colors=TeamColors.from_dict(d.get("teamColors")) if d.get("teamColors") else None,
        )

    @property
    def is_player(self) -> bool:
        """``type == 1`` is a single player (vs. a doubles pair / club)."""
        return self.type == 1

    @property
    def display_name(self) -> str:
        return self.name or self.full_name or self.short_name or (
            f"#{self.id}" if self.id is not None else "unknown"
        )
