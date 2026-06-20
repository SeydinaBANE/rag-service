from __future__ import annotations

from app.adapters.retry import RetryPolicy, retry_call


class HttpGreeter:
    """Example HTTP-backed GreeterPort.

    The SDK (`httpx`) is imported lazily inside the method, never at module top
    level, so the package stays importable without the optional dependency.
    Outbound calls carry a timeout and a bounded backoff retry.
    """

    def __init__(self, base_url: str, timeout: float, retry: RetryPolicy) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retry = retry

    def greet(self, recipient: str, locale: str) -> str:
        import httpx

        def _call() -> str:
            response = httpx.get(
                f"{self._base_url}/greet",
                params={"recipient": recipient, "locale": locale},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return str(response.json()["message"])

        return retry_call(_call, self._retry)
