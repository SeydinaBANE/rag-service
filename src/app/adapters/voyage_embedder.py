from __future__ import annotations

from typing import Any

from app.adapters.retry import RetryPolicy, retry_call
from app.domain.models import Vector


class VoyageEmbedder:
    """Voyage AI EmbedderPort (Anthropic's recommended embeddings provider).

    The SDK (``voyageai``) is imported lazily inside the call path, never at
    module top level, so the package stays importable without the optional
    dependency. Outbound calls carry a timeout and a bounded backoff retry (the
    SDK's own retries are disabled so the project's ``RetryPolicy`` governs
    them). Documents and queries pass distinct ``input_type`` hints.
    """

    def __init__(self, api_key: str, model: str, timeout: float, retry: RetryPolicy) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._retry = retry

    def _client(self) -> Any:
        import voyageai

        return voyageai.Client(
            api_key=self._api_key or None,
            timeout=self._timeout,
            max_retries=0,
        )

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        def _call() -> list[Vector]:
            result = self._client().embed(texts, model=self._model, input_type="document")
            return [[float(component) for component in vector] for vector in result.embeddings]

        return retry_call(_call, self._retry)

    def embed_query(self, text: str) -> Vector:
        def _call() -> Vector:
            result = self._client().embed([text], model=self._model, input_type="query")
            return [float(component) for component in result.embeddings[0]]

        return retry_call(_call, self._retry)
