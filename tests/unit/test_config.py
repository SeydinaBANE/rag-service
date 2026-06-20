import pytest

from app.config import EmbedderProvider, GeneratorProvider, GreeterProvider, Settings


def test_settings_defaults_boot_offline():
    settings = Settings()
    assert settings.greeter_provider is GreeterProvider.FAKE
    assert settings.embedder_provider is EmbedderProvider.FAKE
    assert settings.generator_provider is GeneratorProvider.FAKE
    assert settings.allowed_locales


def test_settings_http_without_base_url_fails_fast():
    with pytest.raises(ValueError, match="GREETER_BASE_URL"):
        Settings(greeter_provider=GreeterProvider.HTTP, greeter_base_url="")


def test_settings_empty_locales_fails_fast():
    with pytest.raises(ValueError, match="ALLOWED_LOCALES"):
        Settings(allowed_locales=[])


def test_settings_voyage_without_key_fails_fast(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="VOYAGE_API_KEY"):
        Settings(embedder_provider=EmbedderProvider.VOYAGE, voyage_api_key="")


def test_settings_claude_without_key_fails_fast(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        Settings(generator_provider=GeneratorProvider.CLAUDE, anthropic_api_key="")


def test_settings_invalid_chunk_overlap_fails_fast():
    with pytest.raises(ValueError, match="CHUNK_OVERLAP"):
        Settings(chunk_size=10, chunk_overlap=10)
