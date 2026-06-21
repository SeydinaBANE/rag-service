import pytest

from app.adapters.fallback_generator import FallbackGenerator
from app.domain.models import Chunk
from app.observability import METRICS


def _chunk(text: str) -> Chunk:
    return Chunk(chunk_id="c1", doc_id="d", text=text)


def test_fallback_uses_primary_when_it_succeeds(scripted_generator):
    primary = scripted_generator("primary answer")
    fallback = scripted_generator("fallback answer")
    gen = FallbackGenerator(primary=primary, fallback=fallback)
    assert gen.generate("q", [_chunk("x")]) == "primary answer"
    assert fallback.calls == 0
    assert METRICS.counters["generator.primary.success"] == 1


def test_fallback_uses_fallback_when_primary_fails(failing_generator, scripted_generator):
    primary = failing_generator()
    fallback = scripted_generator("fallback answer")
    gen = FallbackGenerator(primary=primary, fallback=fallback)
    assert gen.generate("q", [_chunk("x")]) == "fallback answer"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert METRICS.counters["generator.primary.failure"] == 1
    assert METRICS.counters["generator.fallback.success"] == 1


def test_fallback_propagates_when_both_fail(failing_generator):
    gen = FallbackGenerator(primary=failing_generator(), fallback=failing_generator())
    with pytest.raises(RuntimeError, match="generator unavailable"):
        gen.generate("q", [_chunk("x")])
