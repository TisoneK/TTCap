from __future__ import annotations

from ttcap import endpoints as ep


def test_discovery_paths():
    assert ep.discovery.live_events() == "/sport/table-tennis/events/live"
    assert ep.discovery.live_tournaments() == "/sport/table-tennis/live-tournaments"
    assert ep.discovery.categories_all() == "/sport/table-tennis/categories/all"
    assert ep.discovery.scheduled_tournaments("2026-11-12", 2) == (
        "/sport/table-tennis/scheduled-tournaments/2026-11-12/page/2"
    )
    assert ep.discovery.categories_on_date("2026-11-12", -28800) == (
        "/sport/table-tennis/2026-11-12/-28800/categories"
    )
    assert ep.discovery.default_unique_tournaments("PL") == (
        "/config/default-unique-tournaments/pl/table-tennis"
    )


def test_event_paths():
    assert ep.event.detail(17539466) == "/event/17539466"
    assert ep.event.point_by_point(1) == "/event/1/point-by-point"
    assert ep.event.incidents(1) == "/event/1/incidents"
    assert ep.event.statistics(1) == "/event/1/statistics"
    # h2h/events is keyed by customId, not the numeric id
    assert ep.event.h2h_events("LWcesplbj") == "/event/LWcesplbj/h2h/events"


def test_tournament_and_player_paths():
    assert ep.tournament.scheduled_events(19041, "2026-11-12") == (
        "/unique-tournament/19041/scheduled-events/2026-11-12"
    )
    assert ep.tournament.standings_total(1964, 1) == (
        "/unique-tournament/1964/season/1/standings/total"
    )
    assert ep.player.last_events(218149, 0) == "/team/218149/events/last/0"
    assert ep.player.detail(218149) == "/team/218149"
    assert ep.player.match_page("ABCdef123").endswith("/table-tennis/match/ABCdef123")
