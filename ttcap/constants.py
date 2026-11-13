"""Shared constants for the table-tennis slice of the Sofascore backend."""

from __future__ import annotations

#: Sport slug and numeric id. Table tennis is sport 20 in one cross-sport
#: route table; every TTCap route is the sport-20 subset of it.
SPORT = "table-tennis"
SPORT_ID = 20

#: The API is served same-origin (no separate ``api.`` host).
API_BASE = "https://www.sofascore.com/api/v1"
WEB_BASE = "https://www.sofascore.com"
IMG_BASE = "https://img.sofascore.com"
