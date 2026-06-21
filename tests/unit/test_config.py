import pytest

from app.config import (
    EmbedderProvider,
    GeneratorProvider,
    GreeterProvider,
    RerankerProvider,
    Settings,
    get_settings,
)


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


def test_settings_cohere_without_key_fails_fast(monkeypatch):
    monkeypatch.delenv("CO_API_KEY", raising=False)
    with pytest.raises(ValueError, match="COHERE_API_KEY"):
        Settings(reranker_provider=RerankerProvider.COHERE, cohere_api_key="")


def test_settings_invalid_log_level_fails_fast():
    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings(log_level="verbose")


def test_settings_api_key_mapping_parses_pairs():
    settings = Settings()
    assert settings.api_key_mapping["dev-key-operator"] == "operator"
    assert settings.api_key_mapping["dev-key-viewer"] == "viewer"


def test_settings_empty_api_keys_fails_fast():
    with pytest.raises(ValueError, match="API_KEYS"):
        Settings(api_keys=())


def test_settings_invalid_rate_limit_fails_fast():
    with pytest.raises(ValueError, match="RATE_LIMIT_MAX_REQUESTS"):
        Settings(rate_limit_max_requests=0)


def test_settings_fallback_claude_without_key_fails_fast(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GENERATOR_FALLBACK_PROVIDER"):
        Settings(generator_fallback_provider=GeneratorProvider.CLAUDE, anthropic_api_key="")


def test_get_settings_returns_cached_singleton():
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()


def test_get_settings_cache_clear_yields_fresh_instance():
    first = get_settings()
    get_settings.cache_clear()
    assert get_settings() is not first
    get_settings.cache_clear()
