from __future__ import annotations

from app.adapters.retry import RetryPolicy, retry_call
from app.domain.models import Chunk


class CohereReranker:
    """Cohere-backed RerankerPort.

    The SDK (``cohere``) is imported lazily inside ``rerank``, never at module
    top level, so the package stays importable without the optional dependency.
    The outbound call carries a timeout and a bounded backoff retry. An empty
    ``api_key`` falls back to the SDK's environment resolution (``CO_API_KEY``).
    """

    def __init__(self, api_key: str, model: str, timeout: float, retry: RetryPolicy) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._retry = retry

    def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        if not chunks:
            return []
        import cohere

        client = cohere.Client(api_key=self._api_key or None, timeout=self._timeout)

        def _call() -> list[Chunk]:
            response = client.rerank(
                query=query,
                documents=[chunk.text for chunk in chunks],
                top_n=min(top_n, len(chunks)),
                model=self._model,
            )
            return [chunks[result.index] for result in response.results]

        return retry_call(_call, self._retry)
