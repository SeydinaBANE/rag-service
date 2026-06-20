from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import Vector


@runtime_checkable
class EmbedderPort(Protocol):
    """Outbound port: turns text into dense vectors.

    Implementations live in adapters/ and import their SDK lazily. Documents and
    queries are embedded through distinct methods because some providers (e.g.
    Voyage) take an ``input_type`` hint that improves retrieval quality.
    """

    def embed_documents(self, texts: list[str]) -> list[Vector]: ...

    def embed_query(self, text: str) -> Vector: ...
