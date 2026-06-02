import logging
import re

import ewts.formatter as formatter
import ewts.paths as paths
from ewts import get_logger, setup_logger, bind_logger
from ewts.log_levels import LEVELS


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


def test_logger_defaults_to_stdout_when_no_log_dir(clean_ewts_env, monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("EWTS_LOG_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.info("hello stdout")

    captured = capsys.readouterr()

    assert "EWTS TROUTE using stdout logging" in captured.out
    assert "2026-01-01T01:02:03.004Z TROUTE" in captured.out
    assert "INFO" in captured.out
    assert "hello stdout" in captured.out
    assert not list(tmp_path.glob("*.log"))
    assert not (tmp_path / "run_logs").exists()


def test_logger_writes_file_with_expected_prefix_when_log_dir_set(clean_ewts_env, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))

    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(paths, "compact_utc_timestamp", lambda: "20260101T010203")

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
    assert "hello" not in capsys.readouterr().out.split("logging to")[-1]


def test_logger_uses_custom_log_file_name_from_setup_logger(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")

    lg = setup_logger(
        "TROUTE",
        log_dir=tmp_path,
        log_file_name="custom.log",
        bind_now=True,
    )

    lg.info("custom file message")

    log_file = tmp_path / "custom.log"
    assert log_file.exists()
    assert "custom file message" in log_file.read_text(encoding="utf-8")


def test_logger_includes_rank_in_default_file_name(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("EWTS_RANK", "7")
    monkeypatch.setattr(paths, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.bind()
    lg.info("ranked message")

    files = list(tmp_path.glob("TROUTE_rank_7_*.log"))
    assert len(files) == 1


def test_perform_level(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("EWTS_LOG_LEVEL", "PERFORM")

    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(paths, "compact_utc_timestamp", lambda: "20260101T010203")

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
    monkeypatch.setattr(paths, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.info("info message")

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1

    line = files[0].read_text().splitlines()[0]

    assert "INFO" in line
    assert "PERFORM" not in line


def test_messages_below_configured_level_are_filtered(clean_ewts_env, monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("EWTS_LOG_DIR", raising=False)
    monkeypatch.setenv("EWTS_LOG_LEVEL", "WARNING")

    lg = get_logger("TROUTE")
    lg.bind()

    lg.info("do not show")
    lg.warning("show warning")

    out = capsys.readouterr().out
    assert "do not show" not in out
    assert "show warning" in out


def test_disabled_logger_suppresses_messages(clean_ewts_env, monkeypatch, capsys):
    monkeypatch.setenv("EWTS_ENABLED", "false")

    lg = get_logger("TROUTE")
    lg.bind()
    lg.fatal("do not log")

    out = capsys.readouterr().out
    assert "logging is DISABLED" in out
    assert "do not log" not in out


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


def test_bind_logger_public_helper(clean_ewts_env):
    lg = bind_logger("TROUTE")

    assert lg.ewts_id == "TROUTE"
    assert get_logger("TROUTE").is_bound()
