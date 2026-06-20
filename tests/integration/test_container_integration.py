import pytest

from app.container import build_container

pytestmark = pytest.mark.integration


def test_container_wires_greeting_service():
    container = build_container()
    greeting = container.greeting.build_greeting("Ada", "en")
    assert greeting.message == "Hello, Ada!"
