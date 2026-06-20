import sys
import types
from types import SimpleNamespace

from app.adapters.cohere_reranker import CohereReranker
from app.adapters.retry import RetryPolicy
from app.domain.models import Chunk


def _chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id="doc", text=text)


def _install_fake_cohere(monkeypatch, indices, recorder=None):
    class _Client:
        def __init__(self, **kwargs):
            if recorder is not None:
                recorder.update(kwargs)

        def rerank(self, query, documents, top_n, model):
            if recorder is not None:
                recorder["call"] = {"top_n": top_n, "model": model, "documents": documents}
            return SimpleNamespace(results=[SimpleNamespace(index=i) for i in indices])

    module = types.ModuleType("cohere")
    module.Client = _Client
    monkeypatch.setitem(sys.modules, "cohere", module)


def test_rerank_maps_sdk_indices_back_to_chunks(monkeypatch):
    chunks = [_chunk("a", "alpha"), _chunk("b", "beta"), _chunk("c", "gamma")]
    _install_fake_cohere(monkeypatch, indices=[2, 0])
    reranker = CohereReranker(api_key="k", model="m", timeout=5.0, retry=RetryPolicy(attempts=1))
    result = reranker.rerank("q", chunks, top_n=2)
    assert [chunk.chunk_id for chunk in result] == ["c", "a"]


def test_rerank_caps_top_n_to_chunk_count(monkeypatch):
    recorder: dict[str, object] = {}
    chunks = [_chunk("a", "alpha"), _chunk("b", "beta")]
    _install_fake_cohere(monkeypatch, indices=[0, 1], recorder=recorder)
    reranker = CohereReranker(api_key="k", model="m", timeout=5.0, retry=RetryPolicy(attempts=1))
    reranker.rerank("q", chunks, top_n=10)
    assert recorder["call"]["top_n"] == 2  # type: ignore[index]


def test_rerank_empty_chunks_skips_sdk(monkeypatch):
    monkeypatch.delitem(sys.modules, "cohere", raising=False)
    reranker = CohereReranker(api_key="k", model="m", timeout=5.0, retry=RetryPolicy(attempts=1))
    assert reranker.rerank("q", [], top_n=3) == []
