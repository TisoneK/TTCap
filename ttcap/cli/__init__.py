"""TTCap command-line interface (backend operator tool)."""

from __future__ import annotations

from .app import build_parser, main

__all__ = ["main", "build_parser"]
