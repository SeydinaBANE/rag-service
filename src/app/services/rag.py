from __future__ import annotations

from app.domain.models import Chunk, Document, EmptyCorpusError, EmptyQueryError, RagAnswer
from app.ports.embedder import EmbedderPort
from app.ports.generator import GeneratorPort
from app.ports.reranker import RerankerPort
from app.ports.vector_store import VectorStorePort
from app.services.chunking import chunk_text


class RagService:
    """Application orchestration for retrieval-augmented generation.

    Depends only on ports, never on adapters. Indexing splits documents into
    chunks, embeds them, and stores them; answering embeds the query, retrieves
    a candidate pool, reranks it down to the most relevant chunks, and asks the
    generator to synthesise a grounded answer.
    """

    def __init__(
        self,
        embedder: EmbedderPort,
        vector_store: VectorStorePort,
        reranker: RerankerPort,
        generator: GeneratorPort,
        chunk_size: int,
        chunk_overlap: int,
        candidate_k: int,
        top_k: int,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._reranker = reranker
        self._generator = generator
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._candidate_k = candidate_k
        self._top_k = top_k

    def index(self, documents: list[Document]) -> int:
        chunks = [
            Chunk(
                chunk_id=f"{document.doc_id}:{position}",
                doc_id=document.doc_id,
                text=piece,
                metadata=document.metadata,
            )
            for document in documents
            for position, piece in enumerate(
                chunk_text(document.text, self._chunk_size, self._chunk_overlap)
            )
        ]
        if not chunks:
            return 0
        vectors = self._embedder.embed_documents([chunk.text for chunk in chunks])
        self._vector_store.add(chunks, vectors)
        return len(chunks)

    def answer(self, question: str, top_k: int | None = None) -> RagAnswer:
        cleaned = question.strip()
        if not cleaned:
            raise EmptyQueryError
        if self._vector_store.count() == 0:
            raise EmptyCorpusError
        final_k = top_k or self._top_k
        query_vector = self._embedder.embed_query(cleaned)
        retrieved = self._vector_store.search(query_vector, max(self._candidate_k, final_k))
        candidates = [scored.chunk for scored in retrieved]
        sources = self._reranker.rerank(cleaned, candidates, final_k)
        message = self._generator.generate(cleaned, sources)
        return RagAnswer(answer=message, sources=sources)
