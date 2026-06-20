import json
import logging

from app.logging import JsonFormatter, configure_logging, get_logger


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_emits_core_fields():
    payload = json.loads(JsonFormatter().format(_record()))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_json_formatter_merges_extra_context():
    payload = json.loads(JsonFormatter().format(_record(request_id="abc", status_code=200)))
    assert payload["request_id"] == "abc"
    assert payload["status_code"] == 200


def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = _record()
        record.exc_info = sys.exc_info()
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exc_info"]


def test_configure_logging_sets_single_handler_and_level():
    configure_logging("DEBUG", json_format=True)
    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_configure_logging_plain_format_uses_text_formatter():
    configure_logging("INFO", json_format=False)
    formatter = logging.getLogger().handlers[0].formatter
    assert not isinstance(formatter, JsonFormatter)


def test_get_logger_returns_named_logger():
    assert get_logger("app.x").name == "app.x"
