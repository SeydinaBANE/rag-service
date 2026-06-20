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

    def ready(self) -> bool:
        """Cheap reachability check for the readiness probe.

        Must not raise: implementations catch their own connection errors and
        return ``False`` when the backend is unreachable. A real adapter
        (pgvector, Qdrant) issues a lightweight ping (e.g. ``SELECT 1``).
        """
        ...
