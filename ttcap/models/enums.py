"""Enumerations for the coded integer fields in the TT data model.

Codes are documented from observation; ``*.from_code`` never raises — an
unrecognized code becomes ``UNKNOWN`` so forward-compatibility holds.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from ._parse import as_int


class _Coded(IntEnum):
    @classmethod
    def from_code(cls, value: Any) -> "_Coded":
        code = as_int(value)
        try:
            return cls(code)  # type: ignore[arg-type]
        except ValueError:
            return cls.UNKNOWN  # type: ignore[attr-defined]


class WinnerCode(_Coded):
    """``event.winnerCode`` — which side won the match."""

    UNKNOWN = 0
    HOME = 1
    AWAY = 2


class Serving(_Coded):
    """``point-by-point score.serving`` — who serves the set."""

    NONE = -1      # none / completed set
    UNKNOWN = 0
    HOME = 1
    AWAY = 2


class Scoring(_Coded):
    """``point-by-point score.scoring`` — who won the set."""

    UNKNOWN = 0
    HOME = 1
    AWAY = 2


class PointType(_Coded):
    """``homePointType`` / ``awayPointType`` — the outcome of a rally.

    ``WON``/``LOST`` are the ordinary pair; ``SET_POINT_WON`` and
    ``MATCH_POINT_WON`` appear on the set-deciding rally.
    """

    UNKNOWN = 0
    WON = 1
    SET_POINT_WON = 3
    MATCH_POINT_WON = 4
    LOST = 5

    @property
    def is_won(self) -> bool:
        return self in (PointType.WON, PointType.SET_POINT_WON, PointType.MATCH_POINT_WON)


class StatusType(str):
    """``status.type`` string values (not an IntEnum — the field is a string).

    Known: ``notstarted``, ``inprogress``, ``finished``. Use the module
    constants below for comparisons.
    """


NOT_STARTED = "notstarted"
IN_PROGRESS = "inprogress"
FINISHED = "finished"
