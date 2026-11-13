"""Player detail — the ``/team/{id}`` wrapper.

A player is a :class:`~ttcap.models.team.Team` of ``type:1``; the detail
route wraps it with ``pregameForm`` and ``editorEntity``. There is no
world-ranking field — Sofascore exposes none for table tennis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .team import Team


@dataclass(frozen=True)
class Player:
    team: Optional[Team]
    pregame_form: Any
    editor_entity: Optional[bool]
    raw: Any = None

    @classmethod
    def from_dict(cls, d: Any) -> "Player":
        d = d or {}
        return cls(
            team=Team.from_dict(d.get("team")) if d.get("team") else None,
            pregame_form=d.get("pregameForm"),
            editor_entity=d.get("editorEntity"),
            raw=d,
        )

    # -- convenience passthroughs ------------------------------------------

    @property
    def id(self) -> Optional[int]:
        return self.team.id if self.team else None

    @property
    def name(self) -> str:
        return self.team.display_name if self.team else "unknown"

    @property
    def country(self):  # noqa: ANN201 - Country | None
        return self.team.country if self.team else None

    @property
    def gender(self) -> Optional[str]:
        return self.team.gender if self.team else None

    @property
    def user_count(self) -> Optional[int]:
        return self.team.user_count if self.team else None
