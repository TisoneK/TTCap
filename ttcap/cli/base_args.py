"""Common CLI arguments shared across subcommands.

These live on a *parent* parser so every subcommand accepts them after the
command name (e.g. ``ttcap live --json``).
"""

from __future__ import annotations

import argparse

from ..client.base import DEFAULT_MIN_INTERVAL, DEFAULT_TIMEOUT


def common_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--json",
        action="store_true",
        help="emit raw JSON instead of a formatted table",
    )
    parent.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="per-request timeout in seconds",
    )
    parent.add_argument(
        "--min-interval",
        type=float,
        default=DEFAULT_MIN_INTERVAL,
        dest="min_interval",
        help="minimum seconds between requests (human-rate floor)",
    )
    return parent
