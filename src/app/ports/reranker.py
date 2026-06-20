from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import Chunk


@runtime_checkable
class RerankerPort(Protocol):
    """Outbound port: reorders retrieved chunks by relevance to the query.

    Sits between retrieval and generation — the vector store returns a broad
    candidate set, the reranker narrows it to the most relevant ``top_n``.
    Implementations live in adapters/ and import their SDK lazily; the default
    fake is deterministic.
    """

    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]: ...
