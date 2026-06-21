import logging

from app.observability import METRICS, record_span


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record):
        self.records.append(record)


def test_record_span_appends_span_with_duration():
    with record_span("op.test", key="val"):
        pass
    assert len(METRICS.spans) == 1
    span = METRICS.spans[0]
    assert span.name == "op.test"
    assert span.duration_ms >= 0.0
    assert span.attributes == {"key": "val"}


def test_record_span_emits_span_log():
    logger = logging.getLogger("app.observability")
    handler = _CaptureHandler()
    logger.addHandler(handler)
    previous = logger.level
    logger.setLevel(logging.INFO)
    try:
        with record_span("op.log", model="m"):
            pass
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)
    record = next(r for r in handler.records if r.getMessage() == "span")
    assert record.span == "op.log"
    assert record.model == "m"
    assert record.duration_ms >= 0.0


def test_metrics_incr_accumulates():
    METRICS.incr("counter")
    METRICS.incr("counter", 2)
    assert METRICS.counters["counter"] == 3


def test_metrics_reset_clears_counters_and_spans():
    METRICS.incr("counter")
    with record_span("op"):
        pass
    METRICS.reset()
    assert METRICS.counters == {}
    assert METRICS.spans == []
