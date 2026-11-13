"""Shared reference entities in the TT hierarchy.

The chain the client assembles::

    sport -> category -> uniqueTournament -> season -> tournament -> event
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ._parse import as_int, as_str


@dataclass(frozen=True)
class Sport:
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]

    @classmethod
    def from_dict(cls, d: Any) -> "Sport":
        d = d or {}
        return cls(id=as_int(d.get("id")), name=d.get("name"), slug=d.get("slug"))


@dataclass(frozen=True)
class Country:
    alpha2: Optional[str]
    alpha3: Optional[str]
    name: Optional[str]

    @classmethod
    def from_dict(cls, d: Any) -> "Country":
        d = d or {}
        return cls(alpha2=d.get("alpha2"), alpha3=d.get("alpha3"), name=d.get("name"))


@dataclass(frozen=True)
class Category:
    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    flag: Optional[str]
    alpha2: Optional[str]
    priority: Optional[int]
    sport: Optional[Sport]

    @classmethod
    def from_dict(cls, d: Any) -> "Category":
        d = d or {}
        return cls(
            id=as_int(d.get("id")),
            name=d.get("name"),
            slug=d.get("slug"),
            flag=d.get("flag"),
            alpha2=d.get("alpha2"),
            priority=as_int(d.get("priority")),
            sport=Sport.from_dict(d.get("sport")) if d.get("sport") else None,
        )


@dataclass(frozen=True)
class UniqueTournament:
    """The recurring competition (e.g. TT Elite Series 19041)."""

    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    user_count: Optional[int]

    @classmethod
    def from_dict(cls, d: Any) -> "UniqueTournament":
        d = d or {}
        return cls(
            id=as_int(d.get("id")),
            name=d.get("name"),
            slug=d.get("slug"),
            user_count=as_int(d.get("userCount")),
        )


@dataclass(frozen=True)
class Season:
    id: Optional[int]
    name: Optional[str]
    year: Optional[str]

    @classmethod
    def from_dict(cls, d: Any) -> "Season":
        d = d or {}
        return cls(id=as_int(d.get("id")), name=d.get("name"), year=as_str(d.get("year")))


@dataclass(frozen=True)
class Tournament:
    """The season-scoped instance (e.g. 99281) — note the two ids."""

    id: Optional[int]
    name: Optional[str]
    slug: Optional[str]
    priority: Optional[int]
    is_live: Optional[bool]
    is_group: Optional[bool]
    competition_type: Optional[int]
    category: Optional[Category]
    unique_tournament: Optional[UniqueTournament]

    @classmethod
    def from_dict(cls, d: Any) -> "Tournament":
        d = d or {}
        return cls(
            id=as_int(d.get("id")),
            name=d.get("name"),
            slug=d.get("slug"),
            priority=as_int(d.get("priority")),
            is_live=d.get("isLive"),
            is_group=d.get("isGroup"),
            competition_type=as_int(d.get("competitionType")),
            category=Category.from_dict(d.get("category")) if d.get("category") else None,
            unique_tournament=(
                UniqueTournament.from_dict(d.get("uniqueTournament"))
                if d.get("uniqueTournament")
                else None
            ),
        )

    @property
    def unique_tournament_id(self) -> Optional[int]:
        return self.unique_tournament.id if self.unique_tournament else None
