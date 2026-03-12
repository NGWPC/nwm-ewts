import re
from pathlib import Path

import ewts.formatter as formatter
from ewts import get_logger
from ewts.log_levels import LEVELS


def test_get_logger_caches_and_resolves_module_key(clean_ewts_env, monkeypatch):
    # Force standalone mode
    monkeypatch.delenv("NGEN_RESULTS_DIR", raising=False)

    a = get_logger("t-route")   # module key in registry
    b = get_logger("TROUTE")    # ewts id
    assert a is b
    assert a.ewts_id == "TROUTE"


def test_logger_writes_file_with_expected_prefix(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(formatter, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("t-route")
    lg.info("hello")

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1

    line = files[0].read_text(encoding="utf-8").splitlines()[0]
    # "<ts> <EWTS_ID padded> <LEVEL padded> <msg>"
    assert line.startswith("2026-01-01T01:02:03.004Z ")
    assert "TROUTE" in line
    assert re.search(r"\bINFO\b", line)
    assert line.rstrip().endswith("hello")


def test_logger_respects_min_level(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("TROUTE_LOGLEVEL", "WARNING")
    monkeypatch.setattr(formatter, "iso_utc_timestamp_ms", lambda: "2026-01-01T01:02:03.004Z")
    monkeypatch.setattr(formatter, "compact_utc_timestamp", lambda: "20260101T010203")

    lg = get_logger("TROUTE")
    lg.info("nope")       # below WARNING -> should not write
    lg.warning("yep")     # should write

    files = list(tmp_path.glob("TROUTE_*.log"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].rstrip().endswith("yep")
