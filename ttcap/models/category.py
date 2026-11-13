"""List wrappers for category discovery responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from .common import Category


@dataclass(frozen=True)
class CategoryList:
    categories: List[Category] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Any) -> "CategoryList":
        d = d or {}
        return cls(categories=[Category.from_dict(c) for c in (d.get("categories") or [])])

    def __iter__(self):
        return iter(self.categories)

    def __len__(self) -> int:
        return len(self.categories)
