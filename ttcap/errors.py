"""Exception types raised by TTCap."""

from __future__ import annotations


class TTCapError(Exception):
    """Base class for all TTCap errors."""


class TransportError(TTCapError):
    """A network-level failure (connection, timeout, DNS)."""


class HTTPError(TTCapError):
    """The server returned a non-success status code.

    ``status`` is the HTTP status; ``url`` is the request URL.
    """

    def __init__(self, status: int, url: str, message: str | None = None) -> None:
        self.status = status
        self.url = url
        super().__init__(message or f"HTTP {status} for {url}")


class NotFoundError(HTTPError):
    """A 404 — the resource does not exist, or is header-gated.

    Several Sofascore table-tennis sub-resources (notably
    ``/event/{id}/point-by-point``) return 404 to a bare request and only
    200 with the SPA's ``Referer``/headers. TTCap sends those headers by
    default, but a genuine absence (e.g. a finished event with no
    incidents) also surfaces here.
    """


class BlockedError(HTTPError):
    """A 403 — most often Cloudflare blocking a non-browser client.

    Plain requests are frequently blocked (HTTP 403). If you hit this,
    slow down, respect the service, and consider capturing through a real
    browser session instead of automating against the service.
    """


class ParseError(TTCapError):
    """A response could not be parsed into the expected shape."""
