from __future__ import annotations

from dataclasses import dataclass

from app.adapters.claude_generator import ClaudeGenerator
from app.adapters.cohere_reranker import CohereReranker
from app.adapters.fakes import (
    FakeEmbedder,
    FakeGenerator,
    FakeGreeter,
    FakeReranker,
    InMemoryVectorStore,
)
from app.adapters.fallback_generator import FallbackGenerator
from app.adapters.http_greeter import HttpGreeter
from app.adapters.retry import RetryPolicy
from app.adapters.voyage_embedder import VoyageEmbedder
from app.config import (
    EmbedderProvider,
    GeneratorProvider,
    GreeterProvider,
    RerankerProvider,
    Settings,
    get_settings,
)
from app.ports.embedder import EmbedderPort
from app.ports.generator import GeneratorPort
from app.ports.greeter import GreeterPort
from app.ports.reranker import RerankerPort
from app.ports.vector_store import VectorStorePort
from app.services.greeting import GreetingService
from app.services.rag import RagService


def build_greeter(settings: Settings) -> GreeterPort:
    if settings.greeter_provider is GreeterProvider.HTTP:
        return HttpGreeter(
            base_url=settings.greeter_base_url,
            timeout=settings.request_timeout,
            retry=RetryPolicy(attempts=settings.retry_attempts),
        )
    return FakeGreeter()


def build_embedder(settings: Settings) -> EmbedderPort:
    if settings.embedder_provider is EmbedderProvider.VOYAGE:
        return VoyageEmbedder(
            api_key=settings.voyage_api_key,
            model=settings.voyage_model,
            timeout=settings.request_timeout,
            retry=RetryPolicy(attempts=settings.retry_attempts),
        )
    return FakeEmbedder(dimensions=settings.embedding_dimensions)


def build_vector_store(settings: Settings) -> VectorStorePort:
    return InMemoryVectorStore()


def _build_generator_for(
    settings: Settings, provider: GeneratorProvider, model: str
) -> GeneratorPort:
    if provider is GeneratorProvider.CLAUDE:
        return ClaudeGenerator(
            api_key=settings.anthropic_api_key,
            model=model,
            max_tokens=settings.generator_max_tokens,
            timeout=settings.request_timeout,
            retry=RetryPolicy(attempts=settings.retry_attempts),
        )
    return FakeGenerator()


def build_generator(settings: Settings) -> GeneratorPort:
    primary = _build_generator_for(settings, settings.generator_provider, settings.generator_model)
    if settings.generator_fallback_provider is None:
        return primary
    fallback = _build_generator_for(
        settings, settings.generator_fallback_provider, settings.generator_fallback_model
    )
    return FallbackGenerator(primary=primary, fallback=fallback)


def build_reranker(settings: Settings) -> RerankerPort:
    if settings.reranker_provider is RerankerProvider.COHERE:
        return CohereReranker(
            api_key=settings.cohere_api_key,
            model=settings.rerank_model,
            timeout=settings.request_timeout,
            retry=RetryPolicy(attempts=settings.retry_attempts),
        )
    return FakeReranker()


def build_rag(settings: Settings) -> RagService:
    return RagService(
        embedder=build_embedder(settings),
        vector_store=build_vector_store(settings),
        reranker=build_reranker(settings),
        generator=build_generator(settings),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        candidate_k=settings.retrieval_candidates,
        top_k=settings.retrieval_top_k,
    )


@dataclass(frozen=True)
class Container:
    settings: Settings
    greeting: GreetingService
    rag: RagService


def build_container(settings: Settings | None = None) -> Container:
    resolved = settings or get_settings()
    greeter = build_greeter(resolved)
    return Container(
        settings=resolved,
        greeting=GreetingService(greeter),
        rag=build_rag(resolved),
    )
