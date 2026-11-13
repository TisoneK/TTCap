"""Command handlers for the TTCap CLI.

Each handler takes the parsed args and a live :class:`SofascoreClient`.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Any

from ..capture import LiveMatchWatcher
from ..client import SofascoreClient
from ..errors import NotFoundError, TTCapError
from . import render


def _today() -> str:
    return _date.today().isoformat()


def cmd_categories(args: Any, client: SofascoreClient) -> int:
    if getattr(args, "date", None):
        cats = client.categories_on(args.date, args.tz)
    else:
        cats = client.categories()
    if args.json:
        render.dump_json([c.__dict__ for c in cats.categories])
        return 0
    rows = [[c.id or "", c.name or "", c.alpha2 or "", c.priority if c.priority is not None else ""]
            for c in sorted(cats.categories, key=lambda c: (-(c.priority or 0), c.name or ""))]
    render.table("Table-tennis categories", ["id", "name", "cc", "priority"], rows)
    return 0


def cmd_live(args: Any, client: SofascoreClient) -> int:
    events = client.live_events()
    if args.json:
        render.dump_json([e.raw for e in events.events])
        return 0
    if not len(events):
        render.out("No live table-tennis matches right now.")
        return 0
    render.events_table(f"Live table tennis ({len(events)})", list(events.events))
    return 0


def _apply_status(events, status: str):
    if status == "live":
        return events.live()
    if status == "scheduled":
        return events.scheduled()
    if status in ("finished", "results"):
        return events.finished()
    return events


def cmd_fixtures(args: Any, client: SofascoreClient) -> int:
    date = args.date or _today()
    if args.tournament:
        events = client.tournament_scheduled_events(args.tournament, date)
        title = f"Fixtures — tournament {args.tournament} · {date}"
    else:
        events = client.fixtures(date, max_tournaments=args.max_tournaments)
        title = f"Fixtures — table tennis · {date}"
    events = _apply_status(events, getattr(args, "status", "all")).sorted_by_start()
    if args.json:
        render.dump_json([e.raw for e in events.events])
        return 0
    if not len(events):
        render.out(f"No fixtures for {date} ({getattr(args, 'status', 'all')}).")
        return 0
    render.events_table(f"{title} ({len(events)})", list(events.events))
    return 0


def cmd_results(args: Any, client: SofascoreClient) -> int:
    date = args.date or _today()
    events = client.results(date, max_tournaments=args.max_tournaments).sorted_by_start()
    if args.json:
        render.dump_json([e.raw for e in events.events])
        return 0
    if not len(events):
        render.out(f"No finished matches for {date}.")
        return 0
    render.events_table(f"Results — table tennis · {date} ({len(events)})", list(events.events))
    return 0


def cmd_today(args: Any, client: SofascoreClient) -> int:
    date = _today()
    live = client.live_events()
    render.events_table(f"Live now ({len(live)})", list(live.events))
    fixtures = client.fixtures(date)
    scheduled = fixtures.scheduled().sorted_by_start()
    finished = fixtures.finished()
    render.out(
        f"\nToday {date}: {len(fixtures)} matches — "
        f"{len(scheduled)} upcoming, {len(live)} live, {len(finished)} finished."
    )
    if len(scheduled):
        render.events_table("Upcoming today", list(scheduled.events)[:25])
    return 0


def cmd_event(args: Any, client: SofascoreClient) -> int:
    ev = client.event(args.event_id)
    if args.json:
        render.dump_json(ev.raw)
        return 0
    render.out(f"[bold]{ev.label()}[/bold]" if render._HAS_RICH else ev.label())
    tour = ev.tournament.name if ev.tournament else "?"
    season = ev.season.name if ev.season else "?"
    render.out(f"{tour} · season {season} · {render.event_status(ev)}")
    render.out(f"Sets: {ev.score_line()}    Points by set: {' '.join(ev.set_scores()) or '—'}")
    if ev.winner.value:
        render.out(f"Winner: {ev.winner.name.lower()}")
    if ev.changes and ev.changes.fields:
        render.out(f"Last changed: {', '.join(ev.changes.fields)} @ {ev.changes.timestamp}")
    return 0


def cmd_pbp(args: Any, client: SofascoreClient) -> int:
    try:
        pbp = client.point_by_point(args.event_id)
    except NotFoundError:
        render.out("No point-by-point for this event (404 — header-gated or absent).")
        return 0
    if args.json:
        render.dump_json([s.__dict__ for s in pbp.sets])
        return 0
    for s in pbp.in_play_order():
        score = s.score
        serve = score.serving.name.lower() if score else "?"
        head = f"Set {s.set_number}: {score.home_score}-{score.away_score}" if score else f"Set {s.set_number}"
        render.out(f"\n{head}  (serving: {serve}, rallies: {s.rally_count})")
        last = s.points[-5:]
        for p in last:
            render.out(f"   {p.home_point}-{p.away_point}  (won: {p.winner or '—'})")
    render.out(f"\nTotal rallies: {pbp.total_rallies}")
    return 0


def cmd_stats(args: Any, client: SofascoreClient) -> int:
    try:
        stats = client.statistics(args.event_id)
    except NotFoundError:
        render.out("No statistics for this event (404).")
        return 0
    if args.json:
        render.dump_json([p.__dict__ for p in stats.periods])
        return 0
    period = stats.period(args.period)
    if period is None:
        render.out(f"No '{args.period}' period in statistics.")
        return 0
    rows = []
    for group in period.groups:
        for it in group.items:
            rows.append([group.name or "", it.name or it.key or "", it.home or "", it.away or ""])
    render.table(f"Statistics — period {period.period}", ["group", "stat", "home", "away"], rows)
    return 0


def cmd_h2h(args: Any, client: SofascoreClient) -> int:
    h = client.h2h(args.event_id)
    if args.json:
        render.dump_json(h.team_duel.__dict__ if h.team_duel else {})
        return 0
    if h.team_duel:
        d = h.team_duel
        render.out(f"Head-to-head — home {d.home_wins} : {d.away_wins} away  (draws {d.draws})")
    else:
        render.out("No head-to-head summary available.")
    return 0


def cmd_player(args: Any, client: SofascoreClient) -> int:
    player = client.player(args.player_id)
    if args.json:
        render.dump_json(player.raw)
        return 0
    team = player.team
    if team:
        country = team.country.name if team.country else "?"
        render.out(f"[bold]{player.name}[/bold]" if render._HAS_RICH else player.name)
        bits = [f"id {player.id}", f"country {country}"]
        if team.gender:
            bits.append(f"gender {team.gender}")
        if team.user_count is not None:
            bits.append(f"followers {team.user_count}")
        render.out(" · ".join(bits))
    # recent form
    try:
        recent = client.player_last_events(args.player_id, args.page)
        render.events_table(f"Recent results (page {args.page})", list(recent.events))
    except NotFoundError:
        render.out("No recent results available.")
    return 0


def cmd_standings(args: Any, client: SofascoreClient) -> int:
    try:
        standings = client.standings(args.tournament_id, args.season_id)
    except NotFoundError:
        render.out("No standings — this competition has no group phase (404).")
        return 0
    if args.json:
        render.dump_json([g.__dict__ for g in standings.groups])
        return 0
    for group in standings.groups:
        rows = [[r.position or "", r.team.display_name if r.team else "", r.matches or 0,
                 r.wins or 0, r.losses or 0, r.points or 0] for r in group.rows]
        render.table(group.group_name or "Standings", ["#", "player", "P", "W", "L", "Pts"], rows)
    return 0


def cmd_watch(args: Any, client: SofascoreClient) -> int:
    watcher = LiveMatchWatcher(
        client,
        args.event_id,
        interval=args.interval,
        max_cycles=args.max_cycles,
    )
    render.out(f"Watching event {args.event_id} (interval {watcher.interval:.0f}s). Ctrl-C to stop.")
    try:
        for snapshot, diff in watcher.iter_updates():
            ev = snapshot.event
            parts = [ev.label(), ev.score_line()]
            if ev.set_scores():
                parts.append(f"[{' '.join(ev.set_scores())}]")
            parts.append(render.event_status(ev))
            if diff.new_rallies:
                parts.append(f"+{diff.new_rallies} rallies")
            render.out("  ".join(str(p) for p in parts))
            if diff.newly_finished:
                render.out("Match finished.")
    except KeyboardInterrupt:
        render.out("\nStopped.")
    return 0


HANDLERS = {
    "categories": cmd_categories,
    "live": cmd_live,
    "fixtures": cmd_fixtures,
    "schedule": cmd_fixtures,  # alias
    "results": cmd_results,
    "today": cmd_today,
    "event": cmd_event,
    "pbp": cmd_pbp,
    "stats": cmd_stats,
    "h2h": cmd_h2h,
    "player": cmd_player,
    "standings": cmd_standings,
    "watch": cmd_watch,
}


def dispatch(args: Any) -> int:
    from ..client import ClientConfig

    config = ClientConfig(
        timeout=args.timeout,
        min_interval=args.min_interval,
    )
    handler = HANDLERS[args.command]
    try:
        with SofascoreClient(config) as client:
            return handler(args, client)
    except TTCapError as exc:
        render.out(f"Error: {exc}")
        return 1
