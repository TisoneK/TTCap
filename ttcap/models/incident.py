"""Incidents — for table tennis these are set-boundary markers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ._parse import as_int


@dataclass(frozen=True)
class Incident:
    incident_type: Optional[str]   # "period" for a completed set
    text: Optional[str]            # e.g. "1. set"
    home_score: Optional[int]
    away_score: Optional[int]

    @classmethod
    def from_dict(cls, d: Any) -> "Incident":
        d = d or {}
        return cls(
            incident_type=d.get("incidentType"),
            text=d.get("text"),
            home_score=as_int(d.get("homeScore")),
            away_score=as_int(d.get("awayScore")),
        )


@dataclass(frozen=True)
class Incidents:
    incidents: List[Incident] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "Incidents":
        d = d or {}
        return cls(incidents=[Incident.from_dict(i) for i in (d.get("incidents") or [])])

    def __iter__(self):
        return iter(self.incidents)

    def __len__(self) -> int:
        return len(self.incidents)
