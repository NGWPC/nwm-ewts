import logging
from pathlib import Path

import pytest

from ewts.config import (
    is_ngen_active,
    get_log_dir,
    get_default_level,
    get_level_for_ewts_id,
    load_config,
)
from ewts.log_levels import LEVELS


def test_is_ngen_active(clean_ewts_env, monkeypatch):
    assert is_ngen_active() is False
    monkeypatch.setenv("NGEN_RESULTS_DIR", "/tmp/results")
    assert is_ngen_active() is True


def test_get_log_dir_env_override(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    assert get_log_dir() == tmp_path


def test_get_log_dir_default_is_home_run_logs(clean_ewts_env, monkeypatch, tmp_path):
    # Patch Path.home() so we don't depend on the actual user home
    monkeypatch.delenv("EWTS_LOG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert get_log_dir() == tmp_path / "run_logs"


@pytest.mark.parametrize(
    "val,expected",
    [
        ("", LEVELS.get("INFO", 20)),
        ("INFO", LEVELS["INFO"]),
        (" debug ", LEVELS["DEBUG"]),
        ("15", 15),
        ("SeVeRe", LEVELS["SEVERE"]),
        ("bogus", LEVELS.get("INFO", 20)),
    ],
)
def test_get_default_level_parsing(clean_ewts_env, monkeypatch, val, expected):
    if val == "":
        monkeypatch.delenv("EWTS_LOG_LEVEL", raising=False)
    else:
        monkeypatch.setenv("EWTS_LOG_LEVEL", val)
    assert get_default_level() == expected


def test_get_level_for_ewts_id_override(clean_ewts_env, monkeypatch):
    monkeypatch.setenv("EWTS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TROUTE_LOGLEVEL", "FATAL")
    assert get_level_for_ewts_id("TROUTE") == LEVELS["FATAL"]


def test_load_config_fields(clean_ewts_env, monkeypatch, tmp_path):
    monkeypatch.setenv("EWTS_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("EWTS_LOG_LEVEL", "WARNING")
    cfg = load_config("TROUTE")
    assert cfg.running_in_ngen is False
    assert cfg.log_dir == tmp_path
    assert cfg.default_level == LEVELS["WARNING"]
