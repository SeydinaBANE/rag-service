from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class GreeterPort(Protocol):
    """Outbound port: turns a recipient name into a localized greeting string.

    Implementations live in adapters/ and import their SDK lazily. No SDK or
    framework import belongs in this module — the domain depends on nothing.
    """

    def greet(self, recipient: str, locale: str) -> str: ...
