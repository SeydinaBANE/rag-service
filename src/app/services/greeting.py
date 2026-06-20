from __future__ import annotations

from app.domain.models import EmptyRecipientError, Greeting
from app.ports.greeter import GreeterPort


class GreetingService:
    """Application orchestration. Depends only on ports, never on adapters."""

    def __init__(self, greeter: GreeterPort) -> None:
        self._greeter = greeter

    def build_greeting(self, recipient: str, locale: str) -> Greeting:
        cleaned = recipient.strip()
        if not cleaned:
            raise EmptyRecipientError
        message = self._greeter.greet(cleaned, locale)
        return Greeting(recipient=cleaned, message=message, locale=locale)
