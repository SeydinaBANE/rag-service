import sys
import types
from types import SimpleNamespace

from app.adapters.retry import RetryPolicy
from app.adapters.voyage_embedder import VoyageEmbedder


def _install_fake_voyageai(monkeypatch, recorder=None, fail_times=0):
    state = {"calls": 0}

    class _Client:
        def __init__(self, **kwargs):
            if recorder is not None:
                recorder["client"] = kwargs

        def embed(self, texts, model, input_type):
            state["calls"] += 1
            if recorder is not None:
                recorder["embed"] = {"texts": texts, "model": model, "input_type": input_type}
            if state["calls"] <= fail_times:
                raise RuntimeError("transient")
            return SimpleNamespace(embeddings=[[1.0, 2.0] for _ in texts])

    module = types.ModuleType("voyageai")
    module.Client = _Client
    monkeypatch.setitem(sys.modules, "voyageai", module)
    return state


def test_embed_documents_returns_float_vectors(monkeypatch):
    recorder: dict[str, object] = {}
    _install_fake_voyageai(monkeypatch, recorder=recorder)
    embedder = VoyageEmbedder(api_key="k", model="m", timeout=5.0, retry=RetryPolicy(attempts=1))
    assert embedder.embed_documents(["a", "b"]) == [[1.0, 2.0], [1.0, 2.0]]
    assert recorder["embed"]["input_type"] == "document"  # type: ignore[index]


def test_embed_passes_timeout_and_disables_sdk_retries(monkeypatch):
    recorder: dict[str, object] = {}
    _install_fake_voyageai(monkeypatch, recorder=recorder)
    embedder = VoyageEmbedder(api_key="k", model="m", timeout=9.0, retry=RetryPolicy(attempts=1))
    embedder.embed_query("q")
    assert recorder["client"]["timeout"] == 9.0  # type: ignore[index]
    assert recorder["client"]["max_retries"] == 0  # type: ignore[index]
    assert recorder["embed"]["input_type"] == "query"  # type: ignore[index]


def test_embed_query_retries_transient_failure(monkeypatch):
    state = _install_fake_voyageai(monkeypatch, fail_times=1)
    embedder = VoyageEmbedder(
        api_key="k", model="m", timeout=5.0, retry=RetryPolicy(attempts=2, base_delay=0.0)
    )
    assert embedder.embed_query("q") == [1.0, 2.0]
    assert state["calls"] == 2
