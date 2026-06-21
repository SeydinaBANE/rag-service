"""Lightweight observability: in-memory metric counters and span traces.

Abstracts Langfuse/Prometheus so the service stays runnable offline and testable.
In production, rebind ``record_span`` to a Langfuse span and export
``METRICS.counters`` to Prometheus — the API stays the same.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from app.logging import get_logger

_logger = get_logger("app.observability")


@dataclass(frozen=True)
class Span:
    """Trace of one operation: name, duration and attributes."""

    name: str
    duration_ms: float
    attributes: dict[str, str]


@dataclass
class Metrics:
    """Counters and span observations aggregated in memory."""

    counters: dict[str, int] = field(default_factory=lambda: defaultdict[str, int](int))
    spans: list[Span] = field(default_factory=list)

    def incr(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    def reset(self) -> None:
        self.counters.clear()
        self.spans.clear()


METRICS = Metrics()


@contextmanager
def record_span(name: str, **attributes: str) -> Iterator[None]:
    """Record the wall-clock duration of a block and append it to the spans."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        METRICS.spans.append(Span(name=name, duration_ms=duration_ms, attributes=attributes))
        _logger.info(
            "span",
            extra={"span": name, "duration_ms": round(duration_ms, 2), **attributes},
        )
