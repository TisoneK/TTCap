"""Argument parser for the TTCap CLI (a backend operator tool)."""

from __future__ import annotations

import argparse
from typing import List, Optional

from .. import __version__
from .base_args import common_parent
from .commands import dispatch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ttcap",
        description="TTCap — Table Tennis Capture. A respectful backend "
                    "client for the Sofascore table-tennis data surface.",
    )
    parser.add_argument("--version", action="version", version=f"ttcap {__version__}")

    parent = common_parent()
    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.required = True

    # --- fixtures & catalogue (the core) ---
    for name, helptext in (
        ("fixtures", "all matches on a date (any status)"),
        ("schedule", "alias of 'fixtures'"),
    ):
        p_fx = sub.add_parser(name, parents=[parent], help=helptext)
        p_fx.add_argument("date", nargs="?", help="YYYY-MM-DD (default: today)")
        p_fx.add_argument("--tournament", type=int, help="unique-tournament id to scope to")
        p_fx.add_argument("--status", choices=["all", "live", "scheduled", "finished"],
                          default="all", help="filter by match status")
        p_fx.add_argument("--page", type=int, default=0)

    p_res = sub.add_parser("results", parents=[parent], help="finished matches on a date")
    p_res.add_argument("date", nargs="?", help="YYYY-MM-DD (default: today)")
    p_res.add_argument("--page", type=int, default=0)

    sub.add_parser("today", parents=[parent], help="live + today's fixtures overview")
    sub.add_parser("live", parents=[parent], help="list live table-tennis matches")

    p_cat = sub.add_parser("categories", parents=[parent], help="list table-tennis categories")
    p_cat.add_argument("--date", help="only categories active on this date (YYYY-MM-DD)")
    p_cat.add_argument("--tz", type=int, default=0, help="tz offset in seconds (with --date)")

    p_event = sub.add_parser("event", parents=[parent], help="show a single match")
    p_event.add_argument("event_id", type=int)

    p_pbp = sub.add_parser("pbp", parents=[parent], help="point-by-point for a match")
    p_pbp.add_argument("event_id", type=int)

    p_stats = sub.add_parser("stats", parents=[parent], help="statistics for a match")
    p_stats.add_argument("event_id", type=int)
    p_stats.add_argument("--period", default="ALL", help="ALL, 1ST, 2ND, …")

    p_h2h = sub.add_parser("h2h", parents=[parent], help="head-to-head summary for a match")
    p_h2h.add_argument("event_id", type=int)

    p_player = sub.add_parser("player", parents=[parent], help="player detail + recent results")
    p_player.add_argument("player_id", type=int)
    p_player.add_argument("--page", type=int, default=0)

    p_stand = sub.add_parser("standings", parents=[parent], help="group-stage standings")
    p_stand.add_argument("tournament_id", type=int, help="unique-tournament id")
    p_stand.add_argument("season_id", type=int)

    p_watch = sub.add_parser("watch", parents=[parent], help="poll a live match until it ends")
    p_watch.add_argument("event_id", type=int)
    p_watch.add_argument("--interval", type=float, default=15.0, help="poll seconds (floor 5)")
    p_watch.add_argument("--max-cycles", type=int, default=None, dest="max_cycles")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return dispatch(args)
