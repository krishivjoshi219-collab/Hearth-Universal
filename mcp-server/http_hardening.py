"""Cross-cutting HTTP hardening for every app FastMCP serves.

Production concerns that do not belong in any single route live here:

* **Correlation** — every response carries ``X-Request-Id`` (a client-supplied
  id is not trusted; we always mint our own) so logs and client bug reports
  can be tied together.
* **Honest failures** — an uncaught exception becomes a JSON 500 with a
  request id instead of a bare ``Internal Server Error``, and the traceback
  goes to the server log, never to the caller.
* **Anti-caching** — ``/api/*`` responses are dynamic and may contain
  household state, so they always get ``Cache-Control: no-store``. Static
  assets are served with ``no-cache`` plus validators; this middleware also
  answers ``If-None-Match`` with an empty ``304`` (Starlette's ``FileResponse``
  does not evaluate conditional headers when files are served directly).

The middleware is pure ASGI: it only appends headers on ``http.response.start``
and never buffers or rewrites bodies, so streaming MCP transports are safe.
"""

from __future__ import annotations

import json
import traceback
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def _header(scope: Scope, name: bytes) -> str:
    """First value of a request header, or '' (headers are bytes pairs)."""
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("latin-1")
    return ""


def _etag_matches(if_none_match: str, etag: str) -> bool:
    if not if_none_match or not etag:
        return False
    if if_none_match.strip() == "*":
        return True
    target = etag.strip().removeprefix("W/")
    return any(
        candidate.strip().removeprefix("W/") == target
        for candidate in if_none_match.split(",")
    )


class RequestHardeningMiddleware:
    """Request ids, no-cache APIs, and non-leaky JSON 500s."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:12]
        path = scope.get("path", "")
        response_started = False
        not_modified = False
        body_sent = False
        if_none_match = _header(scope, b"if-none-match")

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started, not_modified, body_sent
            if message["type"] == "http.response.start":
                response_started = True
                headers = MutableHeaders(scope=message)
                headers.setdefault("x-request-id", request_id)
                headers.setdefault("x-content-type-options", "nosniff")
                headers.setdefault("referrer-policy", "no-referrer")
                if path.startswith("/api/"):
                    headers.setdefault("cache-control", "no-store")
                if (
                    scope.get("method") in ("GET", "HEAD")
                    and message.get("status") == 200
                    and _etag_matches(if_none_match, headers.get("etag", ""))
                ):
                    not_modified = True
                    message["status"] = 304
                    if "content-length" in headers:
                        del headers["content-length"]
            if message["type"] == "http.response.body" and not_modified:
                if not body_sent:
                    body_sent = True
                    await send({"type": "http.response.body", "body": b"", "more_body": False})
                return
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:  # last line of defence: log the traceback, never leak it
            if response_started:
                # Headers are already on the wire: the only correct move is to
                # let the server abort the connection.
                raise
            traceback.print_exc()
            body = json.dumps(
                {
                    "ok": False,
                    "error": "Internal server error",
                    "request_id": request_id,
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                        (b"cache-control", b"no-store"),
                        (b"x-request-id", request_id.encode("ascii")),
                        (b"x-content-type-options", b"nosniff"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})


def install_hardening(mcp) -> None:
    """Wrap FastMCP's app factory so tests and production get the same stack.

    ``FastMCP.streamable_http_app()`` builds a fresh Starlette app per call and
    is what ``mcp.run(transport="streamable-http")`` uses internally. Wrapping
    the factory (rather than only the production entrypoint) means the test
    suite exercises exactly the middleware production runs.
    """
    if getattr(mcp, "_hearth_hardened", False):
        return

    original = mcp.streamable_http_app

    def hardened_streamable_http_app(*args, **kwargs):
        app = original(*args, **kwargs)
        app.add_middleware(RequestHardeningMiddleware)
        return app

    mcp.streamable_http_app = hardened_streamable_http_app
    mcp._hearth_hardened = True
