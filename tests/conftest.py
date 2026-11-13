"""Shared test fixtures.

All sample payloads here are **synthetic** — hand-written to match the
documented response *shapes*, not copied from any captured dataset. They
exercise the parsers and clients without redistributing real data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def event_detail() -> dict:
    return load("event_detail.json")


@pytest.fixture
def live_events() -> dict:
    return load("live_events.json")


@pytest.fixture
def point_by_point() -> dict:
    return load("point_by_point.json")


@pytest.fixture
def statistics() -> dict:
    return load("statistics.json")


@pytest.fixture
def categories() -> dict:
    return load("categories.json")


@pytest.fixture
def standings() -> dict:
    return load("standings.json")


@pytest.fixture
def h2h() -> dict:
    return load("h2h.json")


@pytest.fixture
def player() -> dict:
    return load("player.json")


@pytest.fixture
def schedule_grouped() -> dict:
    return load("schedule_grouped.json")
