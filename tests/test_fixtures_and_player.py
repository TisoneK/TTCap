from __future__ import annotations

import httpx

from ttcap.client import ClientConfig, SofascoreClient
from ttcap.models import EventList, Player, ScheduledTournaments


def make_client(handler):
    return SofascoreClient(
        ClientConfig(min_interval=0.0, max_retries=0),
        transport=httpx.MockTransport(handler),
    )


# --- the daily schedule index (real shape) --------------------------------

def test_scheduled_tournaments_shape(scheduled_tournaments):
    index = ScheduledTournaments.from_dict(scheduled_tournaments)
    assert len(index) == 2
    assert index.has_next_page is False
    assert index.unique_tournament_ids() == [50001, 50002]
    first = index.scheduled[0]
    assert first.name == "Sample Series"
    assert first.event_count(0) == 3
    assert first.event_count(-28800) == 3
    assert first.event_count(3600) == 2
    # unknown offset falls back to UTC (0)
    assert first.event_count(999999) == 3
    assert index.total_events(0) == 5


# --- fixtures() two-step flow ---------------------------------------------

def _events_payload(*events):
    return {"events": list(events)}


def _event(eid, status_type, ut_id):
    return {
        "id": eid,
        "status": {"code": 100 if status_type == "finished" else 0,
                   "type": status_type, "description": status_type},
        "homeTeam": {"name": "H", "type": 1, "id": 1},
        "awayTeam": {"name": "A", "type": 1, "id": 2},
        "homeScore": {"current": 3}, "awayScore": {"current": 1},
        "startTimestamp": 1800000000 + eid,
        "tournament": {"id": ut_id * 10, "uniqueTournament": {"id": ut_id}, "category": {"id": 9000 + ut_id}},
    }


def test_client_fixtures_two_step(scheduled_tournaments):
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if "scheduled-tournaments" in p:
            assert p.endswith("/page/1")  # 1-indexed
            return httpx.Response(200, json=scheduled_tournaments)
        if "/unique-tournament/50001/scheduled-events/" in p:
            return httpx.Response(200, json=_events_payload(
                _event(1001, "notstarted", 50001),
                _event(1002, "finished", 50001),
            ))
        if "/unique-tournament/50002/scheduled-events/" in p:
            return httpx.Response(200, json=_events_payload(
                _event(1003, "finished", 50002),
                _event(1001, "notstarted", 50001),  # duplicate id across tournaments
            ))
        return httpx.Response(404)

    with make_client(handler) as client:
        index = client.scheduled_tournaments("2026-11-13")  # default page 1
        assert index.unique_tournament_ids() == [50001, 50002]

        fx = client.fixtures("2026-11-13")
        assert len(fx) == 3                 # 4 fetched, 1 duplicate dropped
        assert len(fx.finished()) == 2
        assert len(fx.scheduled()) == 1
        assert len(fx.by_unique_tournament(50002)) == 1

        res = client.results("2026-11-13")
        assert len(res) == 2

        capped = client.fixtures("2026-11-13", max_tournaments=1)
        assert len(capped) == 2             # only the first tournament fetched


def test_fixtures_skips_tournament_404(scheduled_tournaments):
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if "scheduled-tournaments" in p:
            return httpx.Response(200, json=scheduled_tournaments)
        if "/unique-tournament/50001/" in p:
            return httpx.Response(200, json=_events_payload(_event(1001, "finished", 50001)))
        return httpx.Response(404)  # 50002 404s
    with make_client(handler) as client:
        fx = client.fixtures("2026-11-13")
        assert len(fx) == 1


# --- EventList filters (independent of transport) -------------------------

def test_eventlist_filters_and_merge():
    a = EventList.from_dict(_events_payload(_event(1, "finished", 50001), _event(2, "notstarted", 50001)))
    b = EventList.from_dict(_events_payload(_event(2, "notstarted", 50001), _event(3, "inprogress", 50002)))
    merged = EventList.merge([a, b])
    assert len(merged) == 3
    assert len(merged.finished()) == 1
    assert len(merged.live()) == 1
    assert len(merged.scheduled()) == 1
    assert len(merged.by_category(59002)) == 1
    starts = [e.start_timestamp for e in merged.sorted_by_start()]
    assert starts == sorted(starts)


# --- player model ---------------------------------------------------------

def test_player_model(player):
    p = Player.from_dict(player)
    assert p.id == 111111
    assert p.name == "Alpha Ada"
    assert p.gender == "F"
    assert p.user_count == 2518
    assert p.team.player_team_info_id == 26173
    assert p.team.category.id == 88
    assert p.team.is_player is True


def test_client_player_typed(player):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/team/111111":
            return httpx.Response(200, json=player)
        return httpx.Response(404)

    with make_client(handler) as client:
        p = client.player(111111)
        assert isinstance(p, Player)
        assert p.name == "Alpha Ada"
