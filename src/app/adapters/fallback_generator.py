from __future__ import annotations

from app.domain.models import Chunk
from app.logging import get_logger
from app.ports.generator import GeneratorPort

_logger = get_logger("app.adapters.fallback_generator")


class FallbackGenerator:
    """GeneratorPort that tries a primary generator, then a fallback on failure.

    Delivers multi-model resilience while satisfying the existing synchronous
    ``GeneratorPort`` contract, so ``RagService`` is unaffected. Any failure of
    the primary (after its own timeout/retry) is logged and the fallback is
    tried; if the fallback also fails, its exception propagates.
    """

    def __init__(self, primary: GeneratorPort, fallback: GeneratorPort) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(self, question: str, context: list[Chunk]) -> str:
        try:
            return self._primary.generate(question, context)
        except Exception as exc:
            _logger.warning(
                "generator_primary_failed",
                extra={"error": str(exc), "error_type": type(exc).__name__},
            )
            return self._fallback.generate(question, context)
