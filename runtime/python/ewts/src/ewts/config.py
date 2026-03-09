from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .helper import getenv_any
from .log_levels import LEVELS

_DEFAULT_LOG_DIR_NAME = "run_logs"

@dataclass(frozen=True)
class EwtsConfig:
    enabled: bool
    ngen_active: bool
    log_dir: Path
    default_level: int

def _env_bool(name: str, default: bool = True) -> bool:
    v = getenv_any(name, None)
    if v is None:
        return default
    return str(v).strip().lower() not in ("0", "false", "off", "no")

def is_ngen_active() -> bool:
    # ngen provides NGEN_RESULTS_DIR when running within ngen.
    return bool(getenv_any("NGEN_RESULTS_DIR", "").strip())

def get_log_dir() -> Path:
    v = getenv_any("EWTS_LOG_DIR", "").strip()
    if v:
        return Path(v).expanduser()
    return Path.home() / _DEFAULT_LOG_DIR_NAME

def _parse_level_value(v: str) -> int | None:
    s = (v or "").strip()
    if not s:
        return None
    # numeric
    if s.isdigit():
        try:
            return int(s)
        except Exception:
            return None
    # named
    key = s.upper()
    # accept common aliases
    if key == "WARN":
        key = "WARNING"
    if key == "CRITICAL":
        key = "FATAL"
    if key == "NONE":
        key = "NOTSET"
    return LEVELS.get(key)

def get_default_level() -> int:
    v = getenv_any("EWTS_LOG_LEVEL", "").strip()
    parsed = _parse_level_value(v)
    # Default to INFO if unset/invalid
    return parsed if parsed is not None else LEVELS.get("INFO", 20)

def get_level_for_ewts_id(ewts_id: str) -> int:
    # Per-module override: <EWTSID>_LOGLEVEL, e.g. TROUTE_LOGLEVEL
    key = f"{ewts_id.upper()}_LOGLEVEL"
    v = getenv_any(key, "").strip()
    parsed = _parse_level_value(v)
    if parsed is not None:
        return parsed
    return get_default_level()

def load_config(ewts_id: str) -> EwtsConfig:
    ngen = is_ngen_active()
    enabled = _env_bool("EWTS_ENABLED", True)
    # Only used for standalone; safe to compute always.
    log_dir = get_log_dir()
    default_level = get_level_for_ewts_id(ewts_id)
    return EwtsConfig(ngen_active=ngen, enabled=enabled, log_dir=log_dir, default_level=default_level)
