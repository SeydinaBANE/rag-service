from __future__ import annotations

from typing import Any

from app.domain.models import Vector


class VoyageEmbedder:
    """Voyage AI EmbedderPort (Anthropic's recommended embeddings provider).

    The SDK (``voyageai``) is imported lazily inside the call path, never at
    module top level, so the package stays importable without the optional
    dependency. Documents and queries pass distinct ``input_type`` hints.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def _client(self) -> Any:
        import voyageai

        return voyageai.Client(api_key=self._api_key or None)

    def embed_documents(self, texts: list[str]) -> list[Vector]:
        result = self._client().embed(texts, model=self._model, input_type="document")
        return [[float(component) for component in vector] for vector in result.embeddings]

    def embed_query(self, text: str) -> Vector:
        result = self._client().embed([text], model=self._model, input_type="query")
        return [float(component) for component in result.embeddings[0]]
