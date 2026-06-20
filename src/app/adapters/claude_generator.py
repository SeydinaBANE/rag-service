from __future__ import annotations

from typing import Any

from app.adapters.retry import RetryPolicy, retry_call
from app.domain.models import Chunk

_SYSTEM = (
    "You are a retrieval-augmented assistant. Answer the question using only the "
    "provided context. If the context does not contain the answer, say so plainly. "
    "Be concise and cite the source ids you relied on."
)


def _format_context(context: list[Chunk]) -> str:
    if not context:
        return "(no context retrieved)"
    return "\n\n".join(f"[{chunk.chunk_id}] {chunk.text}" for chunk in context)


def _build_prompt(question: str, context: list[Chunk]) -> str:
    return f"Context:\n{_format_context(context)}\n\nQuestion: {question}"


class ClaudeGenerator:
    """Claude-backed GeneratorPort.

    The SDK (``anthropic``) is imported lazily inside ``generate``, never at
    module top level, so the package stays importable without the optional
    dependency. The outbound call carries a timeout and a bounded backoff retry
    (the SDK's own retries are disabled so the project's ``RetryPolicy`` governs
    them). An empty ``api_key`` falls back to the SDK's environment resolution
    (``ANTHROPIC_API_KEY``).
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        timeout: float,
        retry: RetryPolicy,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._retry = retry

    def generate(self, question: str, context: list[Chunk]) -> str:
        import anthropic

        client = anthropic.Anthropic(
            api_key=self._api_key or None,
            timeout=self._timeout,
            max_retries=0,
        )

        def _call() -> str:
            response: Any = client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM,
                messages=[{"role": "user", "content": _build_prompt(question, context)}],
            )
            return "".join(block.text for block in response.content if block.type == "text")

        return retry_call(_call, self._retry)
