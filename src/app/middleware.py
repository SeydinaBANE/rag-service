"""ASGI hardening middleware: per-IP sliding-window rate limiting.

Correlation-ID handling lives in ``api/app.py`` (the request-logging middleware,
which honours an incoming ``X-Request-ID`` and echoes it on the response).
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

_RATE_LIMITED_PATHS = frozenset({"/rag/query", "/rag/index"})
_request_timestamps: dict[str, list[float]] = defaultdict(list)


def reset_rate_limiter() -> None:
    """Clear all recorded request timestamps (test isolation)."""
    _request_timestamps.clear()


def setup_rate_limiting(app: FastAPI, max_requests: int, window_sec: int) -> None:
    """Register a per-IP sliding-window rate limiter on the costly RAG paths."""

    @app.middleware("http")
    async def _rate_limit(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in _RATE_LIMITED_PATHS:
            client = request.client
            key = client.host if client is not None else "unknown"
            now = time.time()
            cutoff = now - window_sec
            recent = [stamp for stamp in _request_timestamps[key] if stamp > cutoff]
            if len(recent) >= max_requests:
                _request_timestamps[key] = recent
                return JSONResponse(
                    status_code=429,
                    content={"detail": "too many requests, try again later"},
                )
            recent.append(now)
            _request_timestamps[key] = recent
        return await call_next(request)
