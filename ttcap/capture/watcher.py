"""Poll a live match the way the SPA does: HTTP polling keyed on the
``changes.changeTimestamp`` signal (there is no websocket/SSE).

The watcher fetches the event detail each cycle and only re-fetches the
heavier sub-resources (point-by-point, statistics, incidents) when the
change signal moves — exactly the client's own freshness discipline,
kept human-rate by the client's rate limiter plus the poll ``interval``.
"""

from __future__ import annotations

import time
from typing import Callable, Iterator, List, Optional, Sequence

from ..client import SofascoreClient
from ..errors import NotFoundError
from .snapshot import MatchSnapshot, SnapshotDiff, diff_snapshots

#: default sub-resources to refresh when the change signal moves
DEFAULT_RESOURCES: Sequence[str] = ("point-by-point", "statistics")

#: never poll faster than this (seconds), regardless of requested interval
MIN_POLL_INTERVAL = 5.0


class LiveMatchWatcher:
    """Watch one event and yield a snapshot whenever it changes.

    Example::

        with SofascoreClient() as client:
            watcher = LiveMatchWatcher(client, event_id=17540687)
            for snapshot, diff in watcher.iter_updates():
                print(snapshot.event.score_line(), diff.new_rallies)
    """

    def __init__(
        self,
        client: SofascoreClient,
        event_id: int,
        *,
        interval: float = 15.0,
        resources: Sequence[str] = DEFAULT_RESOURCES,
        stop_when_finished: bool = True,
        max_cycles: Optional[int] = None,
    ) -> None:
        self.client = client
        self.event_id = event_id
        self.interval = max(MIN_POLL_INTERVAL, interval)
        self.resources = tuple(resources)
        self.stop_when_finished = stop_when_finished
        self.max_cycles = max_cycles
        self._last_change_ts: Optional[int] = None
        self._last_snapshot: Optional[MatchSnapshot] = None

    # -- one cycle ----------------------------------------------------------

    def poll_once(self, force_resources: bool = False) -> MatchSnapshot:
        """Fetch the event; refresh sub-resources if the signal moved."""
        event = self.client.event(self.event_id)
        changed = force_resources or event.change_timestamp != self._last_change_ts
        self._last_change_ts = event.change_timestamp

        snapshot = MatchSnapshot(event=event)
        if changed:
            if "point-by-point" in self.resources:
                snapshot.point_by_point = self._safe(self.client.point_by_point)
            if "statistics" in self.resources:
                snapshot.statistics = self._safe(self.client.statistics)
            if "incidents" in self.resources:
                snapshot.incidents = self._safe(self.client.incidents)
        elif self._last_snapshot is not None:
            # carry forward the last known sub-resources when nothing moved
            snapshot.point_by_point = self._last_snapshot.point_by_point
            snapshot.statistics = self._last_snapshot.statistics
            snapshot.incidents = self._last_snapshot.incidents
        return snapshot

    def _safe(self, fn: Callable[[int], object]) -> Optional[object]:
        """Call a sub-resource fetch, tolerating per-event 404s."""
        try:
            return fn(self.event_id)  # type: ignore[arg-type]
        except NotFoundError:
            return None

    # -- streaming ----------------------------------------------------------

    def iter_updates(self) -> Iterator["tuple[MatchSnapshot, SnapshotDiff]"]:
        """Yield ``(snapshot, diff)`` on the first cycle and each change."""
        cycles = 0
        first = True
        while True:
            snapshot = self.poll_once(force_resources=first)
            diff = diff_snapshots(self._last_snapshot, snapshot)
            if first or diff.has_changes:
                self._last_snapshot = snapshot
                yield snapshot, diff
            first = False

            cycles += 1
            if self.stop_when_finished and snapshot.event.is_finished:
                return
            if self.max_cycles is not None and cycles >= self.max_cycles:
                return
            time.sleep(self.interval)

    def run(
        self,
        on_update: Callable[[MatchSnapshot, SnapshotDiff], None],
    ) -> MatchSnapshot:
        """Drive the loop, calling ``on_update`` each time; return the last."""
        last: Optional[MatchSnapshot] = None
        for snapshot, diff in self.iter_updates():
            on_update(snapshot, diff)
            last = snapshot
        if last is None:  # pragma: no cover - loop always yields once
            last = self.poll_once(force_resources=True)
        return last

    def changed_feed_fields(self) -> List[str]:
        """The ``changes.changes`` field paths from the last snapshot."""
        if self._last_snapshot and self._last_snapshot.event.changes:
            return list(self._last_snapshot.event.changes.fields)
        return []
