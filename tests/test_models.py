from __future__ import annotations

from ttcap.models import (
    CategoryList,
    Event,
    EventList,
    H2H,
    PointByPoint,
    Standings,
    Statistics,
)
from ttcap.models.enums import IN_PROGRESS, PointType, Scoring, Serving, WinnerCode


def test_event_parses_score_model(event_detail):
    ev = Event.from_dict(event_detail["event"])
    assert ev.id == 60001001
    assert ev.custom_id == "ABCdef123"
    assert ev.is_live is True
    assert ev.status.type == IN_PROGRESS
    # current = sets won; periodN = points in each set
    assert ev.home_score.current == 1
    assert ev.home_score.set_points(1) == 11
    assert ev.away_score.set_points(1) == 9
    assert ev.score_line() == "1 - 1"
    assert ev.set_scores() == ["11-9", "7-8"]
    assert ev.change_timestamp == 1800000100
    assert "homeScore.period2" in ev.changes.fields
    assert ev.winner is WinnerCode.UNKNOWN


def test_event_winner_and_labels(event_detail):
    ev = Event.from_dict(event_detail["event"])
    assert "Alpha A." in ev.label()
    assert ev.home_team.is_player is True
    assert ev.tournament.unique_tournament_id == 50001


def test_event_list(live_events):
    events = EventList.from_dict(live_events)
    assert len(events) == 2
    assert all(e.is_live for e in events)
    assert events.events[0].away_team.display_name == "Beta B."


def test_point_by_point(point_by_point):
    pbp = PointByPoint.from_dict(point_by_point)
    assert len(pbp) == 2
    # feed is newest-first; in_play_order sorts ascending
    assert [s.set_number for s in pbp.in_play_order()] == [1, 2]
    set1 = pbp.in_play_order()[0]
    assert set1.score.serving is Serving.NONE
    assert set1.score.scoring is Scoring.HOME
    # the deciding rally carries a set-point type
    last = set1.points[-1]
    assert last.home_point_type is PointType.SET_POINT_WON
    assert last.home_point_type.is_won is True
    assert last.winner == "home"
    assert pbp.total_rallies == 4


def test_statistics(statistics):
    stats = Statistics.from_dict(statistics)
    all_period = stats.period("ALL")
    assert all_period is not None
    item = all_period.item("servicePointsAccuracy")
    assert item.value_type == "team"
    assert item.home_total == 19.0
    assert all_period.item("pointsWon").home_value == 20.0
    assert stats.period("1ST") is not None


def test_categories(categories):
    cats = CategoryList.from_dict(categories)
    assert len(cats) == 2
    names = {c.name for c in cats}
    assert "International" in names


def test_standings(standings):
    st = Standings.from_dict(standings)
    assert len(st) == 1
    group = st.groups[0]
    assert group.is_group is True
    assert group.rows[0].team.display_name == "Alpha A."
    assert group.rows[0].points == 6


def test_h2h(h2h):
    h = H2H.from_dict(h2h)
    assert h.team_duel.home_wins == 4
    assert h.team_duel.draws == 0


def test_parsers_tolerate_empty():
    # never raise on empty/None
    assert Event.from_dict(None).id is None
    assert len(EventList.from_dict({})) == 0
    assert len(PointByPoint.from_dict(None)) == 0
    assert Statistics.from_dict({}).period("ALL") is None
