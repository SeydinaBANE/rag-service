import sys
import types
from types import SimpleNamespace

from app.adapters.claude_generator import ClaudeGenerator
from app.adapters.retry import RetryPolicy
from app.domain.models import Chunk


def _chunk(text: str) -> Chunk:
    return Chunk(chunk_id="c1", doc_id="d", text=text)


def _install_fake_anthropic(monkeypatch, recorder=None, fail_times=0):
    state = {"calls": 0}

    class _Messages:
        def create(self, **kwargs):
            state["calls"] += 1
            if recorder is not None:
                recorder["create"] = kwargs
            if state["calls"] <= fail_times:
                raise RuntimeError("transient")
            return SimpleNamespace(
                content=[
                    SimpleNamespace(type="text", text="grounded "),
                    SimpleNamespace(type="thinking", text="ignored"),
                    SimpleNamespace(type="text", text="answer"),
                ]
            )

    class _Anthropic:
        def __init__(self, **kwargs):
            if recorder is not None:
                recorder["client"] = kwargs
            self.messages = _Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = _Anthropic
    monkeypatch.setitem(sys.modules, "anthropic", module)
    return state


def test_generate_joins_text_blocks(monkeypatch):
    recorder: dict[str, object] = {}
    _install_fake_anthropic(monkeypatch, recorder=recorder)
    generator = ClaudeGenerator(
        api_key="k", model="m", max_tokens=64, timeout=5.0, retry=RetryPolicy(attempts=1)
    )
    assert generator.generate("q", [_chunk("alpha")]) == "grounded answer"


def test_generate_passes_timeout_and_disables_sdk_retries(monkeypatch):
    recorder: dict[str, object] = {}
    _install_fake_anthropic(monkeypatch, recorder=recorder)
    generator = ClaudeGenerator(
        api_key="k", model="m", max_tokens=64, timeout=7.5, retry=RetryPolicy(attempts=1)
    )
    generator.generate("q", [_chunk("alpha")])
    assert recorder["client"]["timeout"] == 7.5  # type: ignore[index]
    assert recorder["client"]["max_retries"] == 0  # type: ignore[index]


def test_generate_retries_transient_failure(monkeypatch):
    state = _install_fake_anthropic(monkeypatch, fail_times=1)
    generator = ClaudeGenerator(
        api_key="k",
        model="m",
        max_tokens=64,
        timeout=5.0,
        retry=RetryPolicy(attempts=3, base_delay=0.0),
    )
    assert generator.generate("q", [_chunk("alpha")]) == "grounded answer"
    assert state["calls"] == 2
