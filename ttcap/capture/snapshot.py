"""A point-in-time snapshot of a match and simple diffing between two."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from ..models import Event, Incidents, PointByPoint, Statistics


@dataclass
class MatchSnapshot:
    """What a watcher captured on one poll cycle."""

    event: Event
    point_by_point: Optional[PointByPoint] = None
    statistics: Optional[Statistics] = None
    incidents: Optional[Incidents] = None
    captured_at: float = field(default_factory=time.time)

    @property
    def change_timestamp(self) -> Optional[int]:
        return self.event.change_timestamp

    @property
    def total_rallies(self) -> int:
        return self.point_by_point.total_rallies if self.point_by_point else 0


@dataclass
class SnapshotDiff:
    """Difference between a previous and a current snapshot."""

    changed_fields: List[str] = field(default_factory=list)
    new_rallies: int = 0
    score_changed: bool = False
    status_changed: bool = False
    newly_finished: bool = False

    @property
    def has_changes(self) -> bool:
        return bool(
            self.changed_fields
            or self.new_rallies
            or self.score_changed
            or self.status_changed
            or self.newly_finished
        )


def diff_snapshots(prev: Optional[MatchSnapshot], cur: MatchSnapshot) -> SnapshotDiff:
    """Compute what changed from ``prev`` to ``cur`` (prev may be None)."""
    diff = SnapshotDiff()
    if prev is None:
        diff.new_rallies = cur.total_rallies
        diff.score_changed = True
        diff.status_changed = True
        diff.newly_finished = cur.event.is_finished
        if cur.event.changes:
            diff.changed_fields = list(cur.event.changes.fields)
        return diff

    if cur.event.changes:
        diff.changed_fields = list(cur.event.changes.fields)

    diff.new_rallies = max(0, cur.total_rallies - prev.total_rallies)
    diff.score_changed = cur.event.score_line() != prev.event.score_line()

    prev_status = prev.event.status.type if prev.event.status else None
    cur_status = cur.event.status.type if cur.event.status else None
    diff.status_changed = prev_status != cur_status
    diff.newly_finished = (not prev.event.is_finished) and cur.event.is_finished
    return diff
