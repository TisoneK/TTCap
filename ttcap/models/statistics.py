"""Per-set and ALL statistic groups."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ._parse import as_float, as_int


@dataclass(frozen=True)
class StatItem:
    key: Optional[str]
    name: Optional[str]
    home: Optional[str]            # display string, e.g. "16/37 (43%)"
    away: Optional[str]
    home_value: Optional[float]
    away_value: Optional[float]
    home_total: Optional[float]   # present on valueType == "team"
    away_total: Optional[float]
    value_type: Optional[str]
    statistics_type: Optional[str]
    compare_code: Optional[int]

    @classmethod
    def from_dict(cls, d: Any) -> "StatItem":
        d = d or {}
        return cls(
            key=d.get("key"),
            name=d.get("name"),
            home=d.get("home"),
            away=d.get("away"),
            home_value=as_float(d.get("homeValue")),
            away_value=as_float(d.get("awayValue")),
            home_total=as_float(d.get("homeTotal")),
            away_total=as_float(d.get("awayTotal")),
            value_type=d.get("valueType"),
            statistics_type=d.get("statisticsType"),
            compare_code=as_int(d.get("compareCode")),
        )


@dataclass(frozen=True)
class StatGroup:
    name: Optional[str]
    items: List[StatItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "StatGroup":
        d = d or {}
        return cls(
            name=d.get("groupName"),
            items=[StatItem.from_dict(i) for i in (d.get("statisticsItems") or [])],
        )


@dataclass(frozen=True)
class StatPeriod:
    """``period`` is 'ALL', '1ST', '2ND', …"""

    period: Optional[str]
    groups: List[StatGroup] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "StatPeriod":
        d = d or {}
        return cls(
            period=d.get("period"),
            groups=[StatGroup.from_dict(g) for g in (d.get("groups") or [])],
        )

    def item(self, key: str) -> Optional[StatItem]:
        for group in self.groups:
            for it in group.items:
                if it.key == key:
                    return it
        return None


@dataclass(frozen=True)
class Statistics:
    periods: List[StatPeriod] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "Statistics":
        d = d or {}
        return cls(periods=[StatPeriod.from_dict(p) for p in (d.get("statistics") or [])])

    def period(self, name: str = "ALL") -> Optional[StatPeriod]:
        for p in self.periods:
            if (p.period or "").upper() == name.upper():
                return p
        return None

    def __iter__(self):
        return iter(self.periods)

    def __len__(self) -> int:
        return len(self.periods)
