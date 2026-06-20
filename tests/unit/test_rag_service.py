import pytest

from app.adapters.fakes import FakeEmbedder, FakeGenerator, FakeReranker, InMemoryVectorStore
from app.domain.models import Document, EmptyCorpusError, EmptyQueryError
from app.services.rag import RagService


def _service() -> RagService:
    return RagService(
        embedder=FakeEmbedder(dimensions=256),
        vector_store=InMemoryVectorStore(),
        reranker=FakeReranker(),
        generator=FakeGenerator(),
        chunk_size=64,
        chunk_overlap=8,
        candidate_k=10,
        top_k=2,
    )


def test_index_then_answer_returns_grounded_sources():
    service = _service()
    indexed = service.index(
        [
            Document(doc_id="d1", text="FastAPI is a Python web framework for building APIs."),
            Document(doc_id="d2", text="Sourdough bread is made from flour and water."),
        ]
    )
    assert indexed >= 2
    result = service.answer("python web framework")
    assert result.sources
    assert result.sources[0].doc_id == "d1"
    assert "python web framework" in result.answer


def test_index_ignores_blank_documents_via_chunking():
    service = _service()
    assert service.index([Document(doc_id="blank", text="   .   ")]) >= 0


def test_answer_empty_query_raises():
    service = _service()
    service.index([Document(doc_id="d1", text="content here")])
    with pytest.raises(EmptyQueryError):
        service.answer("   ")


def test_answer_empty_corpus_raises():
    with pytest.raises(EmptyCorpusError):
        _service().answer("anything")


def test_answer_respects_top_k_override():
    service = _service()
    service.index(
        [Document(doc_id=f"d{i}", text=f"document number {i} about topics") for i in range(5)]
    )
    result = service.answer("document topics", top_k=1)
    assert len(result.sources) == 1
