from __future__ import annotations

import json

import httpx
import pytest

from ttcap.client import ClientConfig, SofascoreClient
from ttcap.errors import BlockedError, NotFoundError


def make_client(handler, **overrides):
    config = ClientConfig(min_interval=0.0, max_retries=0, **overrides)
    return SofascoreClient(config, transport=httpx.MockTransport(handler))


def test_live_events_and_event(live_events, event_detail):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/events/live"):
            return httpx.Response(200, json=live_events)
        if path == "/api/v1/event/60001001":
            return httpx.Response(200, json=event_detail)
        return httpx.Response(404, json={"error": "not found"})

    with make_client(handler) as client:
        events = client.live_events()
        assert len(events) == 2
        ev = client.event(60001001)
        assert ev.custom_id == "ABCdef123"
        assert ev.change_timestamp == 1800000100


def test_headers_include_referer(live_events):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["referer"] = request.headers.get("referer")
        captured["ua"] = request.headers.get("user-agent")
        return httpx.Response(200, json=live_events)

    with make_client(handler) as client:
        client.live_events()
    assert captured["referer"].startswith("https://www.sofascore.com")
    assert "Mozilla" in captured["ua"]


def test_not_found_maps_to_exception():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with make_client(handler) as client:
        with pytest.raises(NotFoundError):
            client.point_by_point(1)


def test_forbidden_maps_to_blocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="cloudflare")

    with make_client(handler) as client:
        with pytest.raises(BlockedError):
            client.live_events()


def test_retries_then_succeeds(live_events):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json=live_events)

    config = ClientConfig(min_interval=0.0, max_retries=2, retry_backoff=0.0)
    with SofascoreClient(config, transport=httpx.MockTransport(handler)) as client:
        events = client.live_events()
    assert calls["n"] == 2
    assert len(events) == 2
