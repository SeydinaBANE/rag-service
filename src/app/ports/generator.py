from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import Chunk


@runtime_checkable
class GeneratorPort(Protocol):
    """Outbound port: synthesises an answer grounded in retrieved chunks.

    Implementations live in adapters/ and import their SDK lazily. The default
    fake is deterministic; the real adapter calls Claude.
    """

    def generate(self, question: str, context: list[Chunk]) -> str: ...
