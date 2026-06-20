import math

from app.adapters.fakes import FakeEmbedder, FakeGenerator, FakeReranker, InMemoryVectorStore
from app.domain.models import Chunk


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id="doc", text=text)


def test_fake_embedder_is_deterministic_and_normalized():
    embedder = FakeEmbedder(dimensions=64)
    first = embedder.embed_query("the quick brown fox")
    second = embedder.embed_query("the quick brown fox")
    assert first == second
    assert math.isclose(math.sqrt(sum(component**2 for component in first)), 1.0)


def test_fake_embedder_similarity_reflects_shared_words():
    embedder = FakeEmbedder(dimensions=256)
    query = embedder.embed_query("python web framework")
    related = embedder.embed_query("python web framework tutorial")
    unrelated = embedder.embed_query("baking sourdough bread recipes")
    similar = sum(a * b for a, b in zip(query, related, strict=True))
    different = sum(a * b for a, b in zip(query, unrelated, strict=True))
    assert similar > different


def test_in_memory_vector_store_ranks_by_similarity():
    embedder = FakeEmbedder(dimensions=256)
    store = InMemoryVectorStore()
    chunks = [_chunk("a", "cats and dogs"), _chunk("b", "stock market prices")]
    store.add(chunks, embedder.embed_documents([chunk.text for chunk in chunks]))
    results = store.search(embedder.embed_query("dogs"), top_k=2)
    assert store.count() == 2
    assert results[0].chunk.chunk_id == "a"
    assert results[0].score >= results[1].score


def test_in_memory_vector_store_rejects_length_mismatch():
    store = InMemoryVectorStore()
    try:
        store.add([_chunk("a", "x")], [])
    except ValueError as exc:
        assert "same length" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("expected ValueError")


def test_fake_reranker_orders_by_word_overlap():
    reranker = FakeReranker()
    chunks = [
        _chunk("a", "unrelated content about weather"),
        _chunk("b", "python web framework guide"),
    ]
    ranked = reranker.rerank("python framework", chunks, top_n=2)
    assert ranked[0].chunk_id == "b"


def test_fake_reranker_truncates_to_top_n():
    reranker = FakeReranker()
    chunks = [_chunk("a", "x"), _chunk("b", "y"), _chunk("c", "z")]
    assert len(reranker.rerank("q", chunks, top_n=1)) == 1


def test_fake_reranker_handles_empty_chunks():
    assert FakeReranker().rerank("q", [], top_n=3) == []


def test_fake_generator_grounds_answer_in_context():
    generator = FakeGenerator()
    answer = generator.generate("what?", [_chunk("a", "the answer is 42")])
    assert "42" in answer
    assert "1 source" in answer


def test_fake_generator_handles_empty_context():
    assert "No indexed context" in FakeGenerator().generate("q", [])
