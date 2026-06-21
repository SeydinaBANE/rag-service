import pytest

from app.adapters.fallback_generator import FallbackGenerator
from app.domain.models import Chunk
from app.observability import METRICS


def _chunk(text: str) -> Chunk:
    return Chunk(chunk_id="c1", doc_id="d", text=text)


class _StubGenerator:
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def generate(self, question, context):
        self.calls += 1
        return self.answer


class _FailingGenerator:
    def __init__(self):
        self.calls = 0

    def generate(self, question, context):
        self.calls += 1
        raise RuntimeError("primary down")


def test_fallback_uses_primary_when_it_succeeds():
    primary = _StubGenerator("primary answer")
    fallback = _StubGenerator("fallback answer")
    gen = FallbackGenerator(primary=primary, fallback=fallback)
    assert gen.generate("q", [_chunk("x")]) == "primary answer"
    assert fallback.calls == 0
    assert METRICS.counters["generator.primary.success"] == 1


def test_fallback_uses_fallback_when_primary_fails():
    primary = _FailingGenerator()
    fallback = _StubGenerator("fallback answer")
    gen = FallbackGenerator(primary=primary, fallback=fallback)
    assert gen.generate("q", [_chunk("x")]) == "fallback answer"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert METRICS.counters["generator.primary.failure"] == 1
    assert METRICS.counters["generator.fallback.success"] == 1


def test_fallback_propagates_when_both_fail():
    gen = FallbackGenerator(primary=_FailingGenerator(), fallback=_FailingGenerator())
    with pytest.raises(RuntimeError, match="primary down"):
        gen.generate("q", [_chunk("x")])
