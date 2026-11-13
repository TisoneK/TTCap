from __future__ import annotations

import httpx

from ttcap.client import ClientConfig, SofascoreClient
from ttcap.models import EventList, Player


def make_client(handler):
    return SofascoreClient(
        ClientConfig(min_interval=0.0, max_retries=0),
        transport=httpx.MockTransport(handler),
    )


def test_from_schedule_flattens_and_dedupes(schedule_grouped):
    events = EventList.from_schedule(schedule_grouped)
    # three event entries, but two share id 60002002 -> deduped to 2
    assert len(events) == 2
    ids = {e.id for e in events}
    assert ids == {60001002, 60002002}


def test_from_schedule_handles_flat_events(live_events):
    events = EventList.from_schedule(live_events)
    assert len(events) == 2


def test_eventlist_status_filters(schedule_grouped):
    events = EventList.from_schedule(schedule_grouped)
    assert len(events.scheduled()) == 1
    assert len(events.finished()) == 1
    assert len(events.live()) == 0
    assert events.scheduled().events[0].is_scheduled is True


def test_eventlist_by_tournament_and_sort(schedule_grouped):
    events = EventList.from_schedule(schedule_grouped)
    assert len(events.by_unique_tournament(50001)) == 1
    assert len(events.by_category(9002)) == 1
    starts = [e.start_timestamp for e in events.sorted_by_start()]
    assert starts == sorted(starts)


def test_player_model(player):
    p = Player.from_dict(player)
    assert p.id == 111111
    assert p.name == "Alpha Ada"
    assert p.gender == "F"
    assert p.user_count == 2518
    assert p.team.player_team_info_id == 26173
    assert p.team.category.id == 88
    assert p.team.is_player is True


def test_client_fixtures_and_results(schedule_grouped):
    def handler(request: httpx.Request) -> httpx.Response:
        if "scheduled-tournaments" in request.url.path:
            return httpx.Response(200, json=schedule_grouped)
        return httpx.Response(404)

    with make_client(handler) as client:
        fx = client.fixtures("2026-11-12")
        assert len(fx) == 2
        res = client.results("2026-11-12")
        assert len(res) == 1
        assert res.events[0].is_finished


def test_client_player_typed(player):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/team/111111":
            return httpx.Response(200, json=player)
        return httpx.Response(404)

    with make_client(handler) as client:
        p = client.player(111111)
        assert isinstance(p, Player)
        assert p.name == "Alpha Ada"
