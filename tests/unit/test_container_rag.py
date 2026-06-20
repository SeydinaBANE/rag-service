from app.adapters.claude_generator import ClaudeGenerator, _build_prompt
from app.adapters.fakes import FakeEmbedder, FakeGenerator, InMemoryVectorStore
from app.adapters.voyage_embedder import VoyageEmbedder
from app.config import EmbedderProvider, GeneratorProvider, Settings
from app.container import build_embedder, build_generator, build_vector_store
from app.domain.models import Chunk


def test_build_embedder_defaults_to_fake():
    assert isinstance(build_embedder(Settings()), FakeEmbedder)


def test_build_embedder_voyage_when_configured():
    settings = Settings(embedder_provider=EmbedderProvider.VOYAGE, voyage_api_key="vk-test")
    assert isinstance(build_embedder(settings), VoyageEmbedder)


def test_build_generator_defaults_to_fake():
    assert isinstance(build_generator(Settings()), FakeGenerator)


def test_build_generator_claude_when_configured():
    settings = Settings(generator_provider=GeneratorProvider.CLAUDE, anthropic_api_key="sk-test")
    assert isinstance(build_generator(settings), ClaudeGenerator)


def test_build_vector_store_is_in_memory():
    assert isinstance(build_vector_store(Settings()), InMemoryVectorStore)


def test_claude_build_prompt_includes_context_ids_and_question():
    prompt = _build_prompt("how?", [Chunk(chunk_id="d1:0", doc_id="d1", text="because reasons")])
    assert "d1:0" in prompt
    assert "because reasons" in prompt
    assert "how?" in prompt


def test_claude_build_prompt_handles_no_context():
    assert "no context retrieved" in _build_prompt("q", [])
