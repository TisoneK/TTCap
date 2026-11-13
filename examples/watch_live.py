"""Watch a live table-tennis match and print each change.

Usage:
    python examples/watch_live.py <event_id>

Pick an ``event_id`` from ``ttcap live`` (or ``python -m ttcap live``).
"""

from __future__ import annotations

import sys

from ttcap import LiveMatchWatcher, SofascoreClient


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python examples/watch_live.py <event_id>")
        return 2
    event_id = int(sys.argv[1])

    with SofascoreClient() as client:
        watcher = LiveMatchWatcher(client, event_id, interval=15.0)
        for snapshot, diff in watcher.iter_updates():
            ev = snapshot.event
            line = f"{ev.label():40s}  {ev.score_line()}  [{' '.join(ev.set_scores())}]"
            if diff.new_rallies:
                line += f"  (+{diff.new_rallies} rallies)"
            print(line)
            if diff.newly_finished:
                print(f"Finished — winner: {ev.winner.name.lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
