"""Rendering helpers. Uses ``rich`` when available, else plain text."""

from __future__ import annotations

import json as _json
from typing import Any, Iterable, List, Optional, Sequence

try:  # optional pretty output
    from rich.console import Console
    from rich.table import Table

    _console: Optional["Console"] = Console()
    _HAS_RICH = True
except Exception:  # pragma: no cover - rich is optional
    _console = None
    _HAS_RICH = False

from ..models import Event


def out(text: str = "") -> None:
    if _HAS_RICH and _console is not None:
        _console.print(text)
    else:
        print(text)


def dump_json(obj: Any) -> None:
    print(_json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def table(title: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    rows = [list(r) for r in rows]
    if _HAS_RICH and _console is not None:
        t = Table(title=title, header_style="bold cyan", title_style="bold")
        for col in columns:
            t.add_column(str(col))
        for row in rows:
            t.add_row(*[str(c) for c in row])
        _console.print(t)
        return
    # plain fallback
    widths = [len(str(c)) for c in columns]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    if title:
        print(f"\n{title}")
    header = "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(columns))
    print(header)
    print("  ".join("-" * widths[i] for i in range(len(columns))))
    for row in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))


def event_status(ev: Event) -> str:
    if ev.status is None:
        return "?"
    if ev.is_live:
        return f"LIVE · {ev.status.description or ''}".strip(" ·")
    if ev.is_finished:
        return "Ended"
    return ev.status.description or ev.status.type or "scheduled"


def events_table(title: str, events: Sequence[Event]) -> None:
    rows: List[Sequence[Any]] = []
    for ev in events:
        tour = ev.tournament.name if ev.tournament else ""
        rows.append([
            ev.id or "",
            tour or "",
            ev.label(),
            ev.score_line(),
            " ".join(ev.set_scores()),
            event_status(ev),
        ])
    table(title, ["id", "tournament", "match", "sets", "points", "status"], rows)
