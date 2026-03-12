from pathlib import Path

from ewts.paths import default_run_logs_dir, make_log_path
import ewts.paths as paths_mod


def test_default_run_logs_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert default_run_logs_dir() == tmp_path / "run_logs"


def test_make_log_path_uses_compact_timestamp(monkeypatch, tmp_path):
    # paths.py imports compact_utc_timestamp into its module namespace; patch there.
    monkeypatch.setattr(paths_mod, "compact_utc_timestamp", lambda: "20260101T010203")
    p = make_log_path("TROUTE", tmp_path)
    assert p == tmp_path / "TROUTE_20260101T010203.log"
