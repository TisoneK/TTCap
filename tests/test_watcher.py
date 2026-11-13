from __future__ import annotations

import copy

import httpx

from ttcap.capture import LiveMatchWatcher, diff_snapshots
from ttcap.client import ClientConfig, SofascoreClient


def make_client(handler):
    return SofascoreClient(
        ClientConfig(min_interval=0.0, max_retries=0),
        transport=httpx.MockTransport(handler),
    )


def test_watcher_first_cycle_fetches_subresources(event_detail, point_by_point, statistics):
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p.endswith("/point-by-point"):
            return httpx.Response(200, json=point_by_point)
        if p.endswith("/statistics"):
            return httpx.Response(200, json=statistics)
        if "/event/" in p:
            return httpx.Response(200, json=event_detail)
        return httpx.Response(404)

    with make_client(handler) as client:
        watcher = LiveMatchWatcher(client, 60001001, max_cycles=1)
        updates = list(watcher.iter_updates())

    assert len(updates) == 1
    snapshot, diff = updates[0]
    assert snapshot.point_by_point is not None
    assert snapshot.statistics is not None
    assert snapshot.total_rallies == 4
    assert diff.new_rallies == 4  # from empty -> 4 on first cycle


def test_watcher_stops_when_finished(event_detail, point_by_point, statistics, monkeypatch):
    import ttcap.capture.watcher as watcher_mod

    monkeypatch.setattr(watcher_mod.time, "sleep", lambda *_: None)

    finished = copy.deepcopy(event_detail)
    finished["event"]["status"] = {"code": 100, "description": "Ended", "type": "finished"}
    finished["event"]["changes"] = {"changes": ["status.type"], "changeTimestamp": 1800000999}

    state = {"event_calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p.endswith("/point-by-point"):
            return httpx.Response(200, json=point_by_point)
        if p.endswith("/statistics"):
            return httpx.Response(200, json=statistics)
        if "/event/" in p:
            state["event_calls"] += 1
            # first poll live, second poll finished
            return httpx.Response(200, json=event_detail if state["event_calls"] == 1 else finished)
        return httpx.Response(404)

    with make_client(handler) as client:
        watcher = LiveMatchWatcher(client, 60001001, interval=0.0)
        updates = list(watcher.iter_updates())

    # one update for the live cycle, one for the finished cycle
    assert len(updates) == 2
    assert updates[-1][1].newly_finished is True
    assert updates[-1][0].event.is_finished is True


def test_watcher_tolerates_missing_pbp(event_detail):
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p.endswith("/point-by-point"):
            return httpx.Response(404)  # header-gated / absent
        if p.endswith("/statistics"):
            return httpx.Response(404)
        if "/event/" in p:
            return httpx.Response(200, json=event_detail)
        return httpx.Response(404)

    with make_client(handler) as client:
        watcher = LiveMatchWatcher(client, 60001001, max_cycles=1)
        snapshot, _ = next(watcher.iter_updates())
    assert snapshot.point_by_point is None
    assert snapshot.event.id == 60001001
