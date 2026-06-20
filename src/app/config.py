from __future__ import annotations

import os
from enum import StrEnum

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GreeterProvider(StrEnum):
    FAKE = "fake"
    HTTP = "http"


class EmbedderProvider(StrEnum):
    FAKE = "fake"
    VOYAGE = "voyage"


class GeneratorProvider(StrEnum):
    FAKE = "fake"
    CLAUDE = "claude"


class RerankerProvider(StrEnum):
    FAKE = "fake"
    COHERE = "cohere"


_VALID_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})


class Settings(BaseSettings):
    """Environment-driven configuration (prefix APP_).

    Defaults run fully offline. A model validator refuses to boot on unsafe
    combinations — fail fast at startup, not on the first request.
    """

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    greeter_provider: GreeterProvider = GreeterProvider.FAKE
    greeter_base_url: str = ""
    request_timeout: float = 5.0
    retry_attempts: int = 2
    allowed_locales: list[str] = Field(default_factory=lambda: ["en", "fr"])
    max_recipient_length: int = 128
    log_level: str = "INFO"
    log_json: bool = True

    embedder_provider: EmbedderProvider = EmbedderProvider.FAKE
    generator_provider: GeneratorProvider = GeneratorProvider.FAKE
    reranker_provider: RerankerProvider = RerankerProvider.FAKE
    embedding_dimensions: int = 256
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_candidates: int = 20
    retrieval_top_k: int = 4
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"
    anthropic_api_key: str = ""
    generator_model: str = "claude-opus-4-8"
    generator_max_tokens: int = 1024
    cohere_api_key: str = ""
    rerank_model: str = "rerank-v3.5"

    @model_validator(mode="after")
    def _validate_production_safety(self) -> Settings:
        if not self.allowed_locales:
            raise ValueError("APP_ALLOWED_LOCALES must list at least one locale.")
        if self.greeter_provider is GreeterProvider.HTTP and not self.greeter_base_url:
            raise ValueError("APP_GREETER_PROVIDER=http requires APP_GREETER_BASE_URL.")
        if self.request_timeout <= 0:
            raise ValueError("APP_REQUEST_TIMEOUT must be positive.")
        if self.log_level.upper() not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"APP_LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}."
            )
        self._validate_rag()
        return self

    def _validate_rag(self) -> None:
        if self.embedding_dimensions <= 0:
            raise ValueError("APP_EMBEDDING_DIMENSIONS must be positive.")
        if self.chunk_size <= 0:
            raise ValueError("APP_CHUNK_SIZE must be positive.")
        if not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError("APP_CHUNK_OVERLAP must be in [0, APP_CHUNK_SIZE).")
        if self.retrieval_top_k <= 0:
            raise ValueError("APP_RETRIEVAL_TOP_K must be positive.")
        if self.retrieval_candidates <= 0:
            raise ValueError("APP_RETRIEVAL_CANDIDATES must be positive.")
        if self.embedder_provider is EmbedderProvider.VOYAGE and not (
            self.voyage_api_key or os.getenv("VOYAGE_API_KEY")
        ):
            raise ValueError("APP_EMBEDDER_PROVIDER=voyage requires APP_VOYAGE_API_KEY.")
        if self.generator_provider is GeneratorProvider.CLAUDE and not (
            self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        ):
            raise ValueError("APP_GENERATOR_PROVIDER=claude requires APP_ANTHROPIC_API_KEY.")
        if self.reranker_provider is RerankerProvider.COHERE and not (
            self.cohere_api_key or os.getenv("CO_API_KEY")
        ):
            raise ValueError("APP_RERANKER_PROVIDER=cohere requires APP_COHERE_API_KEY.")
