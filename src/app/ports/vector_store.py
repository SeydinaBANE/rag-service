from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.models import Chunk, ScoredChunk, Vector


@runtime_checkable
class VectorStorePort(Protocol):
    """Outbound port: persists chunk embeddings and serves nearest-neighbour search.

    Implementations live in adapters/. The default fake keeps everything in
    memory; a production adapter would back this with pgvector, Qdrant, etc.
    """

    def add(self, chunks: list[Chunk], vectors: list[Vector]) -> None: ...

    def search(self, query: Vector, top_k: int) -> list[ScoredChunk]: ...

    def count(self) -> int: ...
