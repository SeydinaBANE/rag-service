from __future__ import annotations

import hashlib
import math

from app.domain.models import Chunk, ScoredChunk, Vector

_TEMPLATES: dict[str, str] = {
    "en": "Hello, {recipient}!",
    "fr": "Bonjour, {recipient} !",
}


class FakeGreeter:
    """Deterministic in-memory GreeterPort used by default and in tests.

    Keeps the package importable and the test suite runnable with no external
    services or heavy SDKs installed.
    """

    def greet(self, recipient: str, locale: str) -> str:
        template = _TEMPLATES.get(locale, _TEMPLATES["en"])
        return template.format(recipient=recipient)


def _hashed_bucket(token: str, dimensions: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % dimensions


def _normalize(vector: list[float]) -> Vector:
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        return vector
    return [component / norm for component in vector]


class FakeEmbedder:
    """Deterministic bag-of-words hashing embedder used by default and in tests.

    Tokens are hashed into a fixed-width vector and the result is L2-normalised,
    so texts that share words land close together under cosine similarity. No
    external service or model download required.
    """

    def __init__(self, dimensions: int) -> None:
        self._dimensions = dimensions

    def _embed(self, text: str) -> Vector:
        vector = [0.0] * self._dimensions
        for token in text.lower().split():
            vector[_hashed_bucket(token, self._dimensions)] += 1.0
        return _normalize(vector)

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> Vector:
        return self._embed(text)


def _cosine(left: Vector, right: Vector) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


class InMemoryVectorStore:
    """In-memory VectorStorePort used by default and in tests.

    Stores chunks alongside their vectors and ranks by cosine similarity. A
    production adapter would back this with pgvector, Qdrant, or similar.
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._vectors: list[Vector] = []

    def add(self, chunks: list[Chunk], vectors: list[Vector]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)

    def search(self, query: Vector, top_k: int) -> list[ScoredChunk]:
        scored = [
            ScoredChunk(chunk=chunk, score=_cosine(query, vector))
            for chunk, vector in zip(self._chunks, self._vectors, strict=True)
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        return len(self._chunks)

    def ready(self) -> bool:
        return True


def _word_overlap(query: str, text: str) -> int:
    return len(set(query.lower().split()) & set(text.lower().split()))


class FakeReranker:
    """Deterministic RerankerPort used by default and in tests.

    Reorders chunks by word overlap with the query and keeps the top ``top_n``.
    Stable sort preserves the original order on ties. Zero I/O.
    """

    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        ranked = sorted(chunks, key=lambda chunk: _word_overlap(query, chunk.text), reverse=True)
        return ranked[:top_n]


class FakeGenerator:
    """Deterministic GeneratorPort used by default and in tests.

    Echoes a grounded answer built from the retrieved context so the full RAG
    pipeline is exercisable with no LLM call.
    """

    def generate(self, question: str, context: list[Chunk]) -> str:
        if not context:
            return f"No indexed context is available to answer: {question}"
        joined = " ".join(chunk.text for chunk in context)
        return f"Answer to {question!r} based on {len(context)} source(s): {joined[:200]}"
