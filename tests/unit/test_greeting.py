import pytest

from app.adapters.fakes import FakeGreeter
from app.domain.models import EmptyRecipientError
from app.services.greeting import GreetingService


def test_build_greeting_nominal():
    service = GreetingService(FakeGreeter())
    greeting = service.build_greeting("Ada", "fr")
    assert greeting.recipient == "Ada"
    assert greeting.message == "Bonjour, Ada !"
    assert greeting.locale == "fr"


def test_build_greeting_unknown_locale_falls_back_to_en():
    service = GreetingService(FakeGreeter())
    greeting = service.build_greeting("Ada", "zz")
    assert greeting.message == "Hello, Ada!"


def test_build_greeting_empty_recipient_raises():
    service = GreetingService(FakeGreeter())
    with pytest.raises(EmptyRecipientError):
        service.build_greeting("   ", "en")
