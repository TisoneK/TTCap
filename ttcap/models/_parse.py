"""Small, forgiving helpers for parsing backend JSON into models.

The backend evolves and ships optional fields; parsers here never raise on
a missing or null key. They coerce defensively so a model built from a
partial object is still usable.
"""

from __future__ import annotations

from typing import Any, Optional


def get(d: Any, *keys: str, default: Any = None) -> Any:
    """Nested-safe get: ``get(obj, "a", "b")`` ~ ``obj["a"]["b"]`` or default."""
    cur = d
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key, default if key == keys[-1] else None)
        if cur is None:
            return default
    return cur


def as_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Coerce to int; handles numeric strings (point scores are strings)."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def as_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_str(value: Any, default: Optional[str] = None) -> Optional[str]:
    if value is None:
        return default
    return str(value)
