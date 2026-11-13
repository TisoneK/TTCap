# TTCap — Table Tennis Capture

A small, respectful **backend** client for *all* table-tennis data served
by the Sofascore backend — **fixtures, results, tournaments, players,
standings, head-to-head and statistics** — with live scores as one piece
of it, not the whole story. TTCap is a data layer, not an app: typed
Python models, sync + async HTTP clients, a date-based **fixtures** layer,
and an optional live-match watcher.

> **Independent project.** TTCap is an original implementation. It is not
> affiliated with, endorsed by, or connected to Sofascore. All tournament,
> competition and player names belong to their respective owners. See
> [Responsible use](#responsible-use).

## Why

Table tennis on this backend is a clean, self-contained slice of one
cross-sport data model:

```
sport (table-tennis, id 20)
└── category            country/region
    └── uniqueTournament    the recurring competition (e.g. 19041)
        └── season             an edition (e.g. "2026")
            └── tournament         season-scoped instance (e.g. 99281)
                └── event              a single match (id + customId)
                    ├── homeTeam / awayTeam   a player (type 1) or pair
                    ├── homeScore / awayScore  sets (current) + per-set points
                    ├── incidents             one marker per completed set
                    ├── point-by-point        rally-by-rally per set
                    └── statistics            per-set + ALL stat groups
```

TTCap models this chain faithfully and exposes it as a clean API.

## Install

```bash
pip install -e ".[cli]"      # editable, with the rich-powered CLI
# or just the library:
pip install -e .
```

Requires Python 3.9+. The only runtime dependency is
[`httpx`](https://www.python-httpx.org/); the CLI additionally uses
[`rich`](https://rich.readthedocs.io/) for tables (it degrades to plain
text if `rich` is absent).

## Library usage

### Fixtures & results (the core)

```python
from ttcap import SofascoreClient

with SofascoreClient() as client:
    # every match on a date, then slice by status
    day = client.fixtures("2026-11-12")
    print(len(day), "matches",
          len(day.scheduled()), "upcoming",
          len(day.live()), "live",
          len(day.finished()), "finished")

    for ev in client.results("2026-11-12"):          # finished only
        print(ev.label(), ev.score_line(), ev.set_scores())

    # scope to one competition
    for ev in client.tournament_scheduled_events(19041, "2026-11-12"):
        print(ev.tournament.name, ev.label())

    # the raw daily index: which tournaments play, with per-tz event counts
    index = client.scheduled_tournaments("2026-11-12")   # pages are 1-indexed
    for st in index:
        print(st.name, st.event_count(tz_offset=0))
```

`fixtures(date)` is two-step, mirroring the web client: it reads the daily
schedule *index* (`scheduled_tournaments`, which lists the tournaments
playing that day plus per-timezone event **counts** — not the events),
then fetches each tournament's `scheduled-events` and merges them. That's
one request per tournament, so it is paced by the rate limiter; pass
`max_tournaments=N` to cap it.

`EventList` carries the filters: `.scheduled()`, `.live()`, `.finished()`,
`.by_unique_tournament(id)`, `.by_category(id)`, `.sorted_by_start()`.

### Catalogue: tournaments, players, standings

```python
with SofascoreClient() as client:
    for cat in client.categories():                  # countries + International
        print(cat.name, cat.id)

    p = client.player(218149)                         # player = a 'team' of type 1
    print(p.name, p.country.name, p.gender, p.user_count)
    for ev in client.player_last_events(218149):      # recent form
        print(ev.label(), ev.score_line())

    standings = client.standings(1964, 92027)         # group-stage only
    for group in standings:
        for row in group.rows:
            print(group.group_name, row.position, row.team.display_name, row.points)
```

### A single match in full

```python
with SofascoreClient() as client:
    ev = client.event(17540687)
    print(ev.is_live, ev.status.description, ev.winner, ev.set_scores())

    pbp = client.point_by_point(17540687)   # header-gated route handled for you
    print("rallies:", pbp.total_rallies)

    stats = client.statistics(17540687)
    print(stats.period("ALL").item("pointsWon").home_value)

    h2h = client.h2h(17540687)
    print(h2h.team_duel.home_wins, "-", h2h.team_duel.away_wins)
```

### Watch a live match (optional)

```python
from ttcap import SofascoreClient, LiveMatchWatcher

with SofascoreClient() as client:
    watcher = LiveMatchWatcher(client, event_id=17540687, interval=15.0)
    for snapshot, diff in watcher.iter_updates():
        print(snapshot.event.score_line(), f"+{diff.new_rallies} rallies")
        if diff.newly_finished:
            break
```

The watcher polls `/event/{id}`, reads `changes.changeTimestamp` (the
server-side diff signal), and only re-fetches the heavier sub-resources
(point-by-point, statistics, incidents) when that signal moves — kept
human-rate by the client's rate limiter plus the poll interval.

### Async

```python
import asyncio
from ttcap import AsyncSofascoreClient

async def main():
    async with AsyncSofascoreClient() as client:
        events = await client.live_events()
        print(len(events), "live matches")

asyncio.run(main())
```

## CLI

A thin operator CLI over the same client (`ttcap` or `python -m ttcap`):

```bash
ttcap today                      # live + today's fixtures overview
ttcap fixtures 2026-11-12        # every match on a date
ttcap fixtures 2026-11-12 --status scheduled   # upcoming only
ttcap fixtures 2026-11-12 --tournament 19041   # scope to one competition
ttcap results 2026-11-12         # finished matches on a date
ttcap live                       # live matches
ttcap categories                 # countries/regions (add --date to scope)
ttcap player 218149              # player detail + recent results
ttcap standings 1964 92027       # group-stage standings (404 for non-group comps)
ttcap event 17540687             # one match: sets, per-set points, status
ttcap pbp 17540687               # point-by-point (last rallies per set)
ttcap stats 17540687 --period 1ST
ttcap h2h 17540687               # head-to-head summary
ttcap watch 17540687 --interval 20             # poll a live match until it ends
```

Add `--json` to any command for the raw payload, and `--min-interval`
to set the human-rate floor between requests.

## Package layout

```
ttcap/
├── constants.py        # sport id/slug, base URLs
├── endpoints/          # URL path builders (discovery / tournament / event / player)
├── models/             # typed, forgiving dataclasses (+ coded-field enums)
├── client/             # sync + async HTTP clients (rate-limited, retrying)
├── capture/            # LiveMatchWatcher + snapshot diffing
└── cli/                # argparse CLI (rich rendering, plain-text fallback)
```

Each subpackage has focused modules; `from_dict` parsers never raise on
missing or null keys, so a model built from a partial payload is still
usable. Coded integer fields (`winnerCode`, `serving`, point types, …)
map to the enums in `ttcap/models/enums.py`.

## Data notes (what the model encodes)

- **Score:** `current`/`display` = **sets won**; `period1…period7` =
  **points** in each set; `normaltime` = sets in normal time.
- **Point types:** `1` won, `5` lost; `3`/`4` on the set/match-deciding
  rally. `serving`: `1` home, `2` away, `-1` none. `scoring`: set winner.
- **Two tournament ids:** `uniqueTournament.id` (recurring competition,
  used in `/unique-tournament/{id}/…`) vs. `tournament.id` (season
  instance, used by live counts). TTCap keeps them distinct.
- **Daily schedule index** (verified live 2026-11-13): `scheduled-tournaments/{date}/page/{n}`
  is **1-indexed** (page 0 → 404) and returns
  `{scheduled: [{tournament, timezoneEventCount}], hasNextPage}` — the
  tournaments playing that day with per-timezone-offset event *counts*, not
  the events. The sport-wide `scheduled-events/{date}` route does **not**
  exist (404); events come per tournament. TTCap's `fixtures()` handles the
  two-step join for you.
- **customId vs numeric id:** prior meetings (`/h2h/events`) are keyed by
  `customId`; the numeric id 404s there.
- **Per-event availability:** `point-by-point` is gated behind the SPA's
  headers (sent by default); `incidents` and `next-events` can legitimately
  404. The client raises `NotFoundError`; the watcher tolerates it.
- **No push channel:** live updates are HTTP polling + conditional HEAD;
  there is no websocket/SSE. The watcher reflects this.
- **No rankings for TT:** the cross-sport rankings routes 404 for table
  tennis; the nearest signals are group-stage standings and `userCount`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The test suite runs fully offline — the HTTP tests use `httpx`'s
`MockTransport`, and all fixtures are **synthetic** (hand-written to match
the documented response shapes, never captured data).

## Responsible use

TTCap is for light, observational, human-rate use of a public service:

- The client enforces a **minimum interval between requests** and caps
  retries. Keep `--min-interval` sane; don't lower it to hammer the API.
- **No bulk scraping, no load testing, no dataset redistribution.**
  Respect the service's Terms and `robots.txt`.
- The service sits behind Cloudflare. Plain non-browser requests are often
  blocked (HTTP 403 → `BlockedError`). If you hit challenges, **stop** —
  TTCap does not and will not attempt to defeat anti-bot protection.
- The default browser-like headers exist only because some endpoints
  require the SPA's `Referer` to return data; they are not an evasion
  mechanism.

## License

[MIT](LICENSE) © Tisone Kironget
