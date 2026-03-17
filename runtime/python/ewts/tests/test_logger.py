import logging
import re

import ewts.formatter as formatter
from ewts import get_logger


def test_get_logger_caches_proxy(clean_ewts_env):
    a = get_logger("t-route")
    b = get_logger("TROUTE")

    assert a is b


def test_bind_creates_real_logger(clean_ewts_env):
    lg = get_logger("TROUTE")

    assert not lg.is_bound()

    lg.bind()

    assert lg.is_bound()


def test_double_bind_safe(clean_ewts_env):
    lg = get_logger("TROUTE")

    lg.bind()
    first = lg._real_logger

    lg.bind()
    second = lg._real_logger

    assert first is second


def test_logging_requires_bind(clean_ewts_env):
    lg = get_logger("TROUTE")

    try:
        lg.info("hello")
        assert False, "Expected RuntimeError when logging before bind"
    except RuntimeError:
        pass


def test_logger_writes_file_with_expected_prefix(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))

    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(formatter, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.info("hello")

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1

    line = files[0].read_text(encoding="utf-8").splitlines()[0]

    assert line.startswith("2026-01-01T01:02:03.004Z ")
    assert "TROUTE" in line
    assert re.search(r"\bINFO\b", line)
    assert line.rstrip().endswith("hello")


def test_perform_level(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("EWTS_LOG_LEVEL", "PERFORM")

    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(formatter, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.perform("perf message")

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1

    line = files[0].read_text().splitlines()[0]

    assert "PERFORM" in line


def test_info_not_mapped_to_perform(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))

    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(formatter, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.info("info message")

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1

    line = files[0].read_text().splitlines()[0]

    assert "INFO" in line
    assert "PERFORM" not in line


def test_logger_supports_additional_python_handler(clean_ewts_env, monkeypatch):
    seen = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            seen.append(record.getMessage())

    lg = get_logger("TROUTE")
    lg.bind()

    lg.addHandler(ListHandler())

    lg.info("hello from extra handler")

    assert "hello from extra handler" in seen
