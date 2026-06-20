import httpx
import pytest

from app.adapters.http_greeter import HttpGreeter
from app.adapters.retry import RetryPolicy, retry_call


def test_retry_call_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    assert retry_call(flaky, RetryPolicy(attempts=3, base_delay=0.0)) == "ok"
    assert calls["n"] == 2


def test_retry_call_exhausts_and_raises():
    def always_fail():
        raise RuntimeError("down")

    with pytest.raises(RuntimeError, match="down"):
        retry_call(always_fail, RetryPolicy(attempts=2, base_delay=0.0))


def test_http_greeter_parses_message(monkeypatch):
    def fake_get(url, params, timeout):
        request = httpx.Request("GET", url)
        return httpx.Response(200, json={"message": "Hi, Ada!"}, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    greeter = HttpGreeter("http://x", timeout=1.0, retry=RetryPolicy(attempts=1))
    assert greeter.greet("Ada", "en") == "Hi, Ada!"
