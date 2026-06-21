from collections.abc import Callable

import pytest

from app.domain.models import Chunk
from app.middleware import reset_rate_limiter
from app.observability import METRICS


class _ScriptedGenerator:
    """Deterministic GeneratorPort returning a fixed reply (records call count)."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0

    def generate(self, question: str, context: list[Chunk]) -> str:
        self.calls += 1
        return self.reply


class _FailingGenerator:
    """GeneratorPort that always raises (for fallback/resilience tests)."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, question: str, context: list[Chunk]) -> str:
        self.calls += 1
        raise RuntimeError("generator unavailable")


@pytest.fixture(autouse=True)
def _reset_state():
    METRICS.reset()
    reset_rate_limiter()
    yield
    METRICS.reset()
    reset_rate_limiter()


@pytest.fixture
def scripted_generator() -> Callable[[str], _ScriptedGenerator]:
    """Factory for a deterministic generator that always returns ``reply``."""
    return lambda reply: _ScriptedGenerator(reply)


@pytest.fixture
def failing_generator() -> Callable[[], _FailingGenerator]:
    """Factory for a generator that always fails."""
    return _FailingGenerator
