"""
integrations.python.logger
==========================

Shared Python logger implementation for EWTS-enabled projects.

Pattern:
- Each Python submodule provides a tiny <module>_log_config.py that defines:
    EWTS_MODULE_KEY  (stable module key for ewts.get_logger)
    EWTS_MODULE_ID   (uppercase EWTS ID used in log line prefix + env vars)

- Each submodule then exposes a local LOG by binding this shared implementation:
    from integrations.python import logger as ewts_logger
    from integrations.python.t_route_log_config import EWTS_MODULE_KEY, EWTS_MODULE_ID

    class _Cfg:
        EWTS_MODULE_KEY = EWTS_MODULE_KEY
        EWTS_MODULE_ID  = EWTS_MODULE_ID

    LOG = ewts_logger.build_logger(_Cfg)

Behavior:
- If the EWTS runtime package (`ewts`) is available:
    returns ewts.get_logger(EWTS_MODULE_KEY)
    (EWTS handles ngen routing/formatting/writing.)

- If `ewts` is NOT available:
    uses a standalone adapter that writes to:
        $EWTS_LOG_DIR/<EWTS_MODULE_ID>_<YYYYMMDDTHHMMSS>.log
    default:
        ~/run_logs/<...>.log

    Standalone line format:
        <YYYY-MM-DDTHH:MM:SS.mmmZ> <EWTSID padded to 8> <LEVEL padded to 7> <message>

Env vars (standalone):
    - EWTS_ENABLED            : 0/false/no/off/disabled => disabled; otherwise enabled (default enabled)
    - EWTS_LOG_DIR            : log directory (default: ~/run_logs)
    - EWTS_LOG_LEVEL          : global default level
    - <EWTSID>_LOGLEVEL       : per-module override (e.g., TROUTE_LOGLEVEL)
    - NGEN_RESULTS_DIR        : (optional) if set, indicates ngen context; used only for parity/diagnostics
                                (when ewts is installed, EWTS itself uses this for routing decisions)

Note on getenv_any:
    EWTS provides ewts.helper.getenv_any() because ngen can set env vars from C/C++
    after the Python interpreter starts (embedded Python). This module always uses getenv_any
    when ewts is available; otherwise it falls back to os.environ.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

# -------------------------------------------------------------------------
# Standalone: add a real PERFORM level so it prints as "PERFORM"
# -------------------------------------------------------------------------
PERFORM_LEVEL = 15
if logging.getLevelName(PERFORM_LEVEL) != "PERFORM":
    logging.addLevelName(PERFORM_LEVEL, "PERFORM")


class _CfgProto(Protocol):
    EWTS_MODULE_KEY: str
    EWTS_MODULE_ID: str


def _get_getenv_any():
    """
    Return a getenv function with signature (key, default="") -> str.

    If ewts is installed, use ewts.helper.getenv_any.
    Otherwise fall back to os.environ.get.
    """
    try:
        from ewts.helper import getenv_any  # type: ignore
        return getenv_any
    except Exception:
        return lambda key, default="": os.environ.get(key, default)


def _parse_enabled(getenv_any, key: str = "EWTS_ENABLED") -> bool:
    v = (getenv_any(key, "") or "").strip()
    if not v:
        return True
    s = v.strip().lower()
    return s not in ("0", "false", "no", "off", "disabled")


def _parse_level(getenv_any, module_id: str) -> int:
    """
    Determine effective level:
        1) <EWTSID>_LOGLEVEL (e.g., TROUTE_LOGLEVEL)
        2) EWTS_LOG_LEVEL
        3) default INFO
    Accepts case-insensitive names or numeric.
    """
    def parse_one(val: str) -> Optional[int]:
        if not val:
            return None
        s = val.strip()
        if not s:
            return None
        if s.isdigit():
            try:
                return int(s)
            except Exception:
                return None
        u = s.upper()
        return {
            "DEBUG": logging.DEBUG,
            "PERFORM": PERFORM_LEVEL,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "SEVERE": logging.ERROR,
            "FATAL": logging.CRITICAL,
            "CRITICAL": logging.CRITICAL,
            "NOTSET": logging.NOTSET,
            "NONE": logging.NOTSET,
        }.get(u)

    env_key = f"{module_id.upper()}_LOGLEVEL"
    lvl = parse_one(getenv_any(env_key, ""))
    if lvl is not None:
        return lvl
    lvl = parse_one(getenv_any("EWTS_LOG_LEVEL", ""))
    if lvl is not None:
        return lvl
    return logging.INFO


class _EwtsLineFormatter(logging.Formatter):
    """
    Format lines like EWTS:
        <YYYY-MM-DDTHH:MM:SS.mmmZ> <EWTSID padded to 8> <LEVEL padded to 7> <message>
    """
    def __init__(self, ewts_id: str):
        super().__init__()
        ewts_id = (ewts_id or "").upper()
        self._id8 = (ewts_id[:8]).ljust(8)

    @staticmethod
    def _utc_now_iso_ms() -> str:
        now = datetime.now(timezone.utc)
        # milliseconds precision + Z
        return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(now.microsecond/1000):03d}Z"

    @staticmethod
    def _level7(record: logging.LogRecord) -> str:
        name = (record.levelname or "NOTSET").upper()
        # ensure PERFORM name displays
        if record.levelno == PERFORM_LEVEL:
            name = "PERFORM"
        return name[:7].ljust(7)

    def format(self, record: logging.LogRecord) -> str:
        ts = self._utc_now_iso_ms()
        lvl7 = self._level7(record)
        msg = record.getMessage()

        # Split multiline messages to one EWTS-prefixed line per line
        lines = msg.splitlines() or [""]
        out_lines = []
        for line in lines:
            out_lines.append(f"{ts} {self._id8} {lvl7} {line}")
        return "\n".join(out_lines)


def _standalone_log_path(getenv_any, module_id: str) -> Path:
    log_dir = (getenv_any("EWTS_LOG_DIR", "") or "").strip()
    if not log_dir:
        home = (getenv_any("HOME", "") or "").strip() or str(Path.home())
        log_dir = str(Path(home) / "run_logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return Path(log_dir) / f"{module_id}_{ts}.log"


class _StdLoggerAdapter:
    """
    Adapter providing EWTS-style methods on top of stdlib logging,
    and writing EWTS-style formatted lines to a per-run file.
    """
    def __init__(self, module_id: str, getenv_any):
        self._module_id = (module_id or "UNKNOWN").upper()
        self._getenv_any = getenv_any

        self._enabled = _parse_enabled(getenv_any)
        self._level = _parse_level(getenv_any, self._module_id)

        self._logger = logging.getLogger(self._module_id)
        self._logger.setLevel(self._level)
        self._logger.propagate = False

        # Avoid duplicate handlers if imported multiple times
        if not self._logger.handlers:
            path = _standalone_log_path(getenv_any, self._module_id)
            handler = logging.FileHandler(path, mode="a", encoding="utf-8")
            handler.setLevel(self._level)
            handler.setFormatter(_EwtsLineFormatter(self._module_id))
            self._logger.addHandler(handler)

    def is_enabled(self) -> bool:
        return bool(self._enabled)

    def _log(self, levelno: int, msg: str) -> None:
        if not self._enabled:
            return
        self._logger.log(levelno, msg)

    def debug(self, msg: str) -> None:
        self._log(logging.DEBUG, msg)

    def perform(self, msg: str) -> None:
        self._log(PERFORM_LEVEL, msg)

    def info(self, msg: str) -> None:
        self._log(logging.INFO, msg)

    def warning(self, msg: str) -> None:
        self._log(logging.WARNING, msg)

    def severe(self, msg: str) -> None:
        self._log(logging.ERROR, msg)

    def error(self, msg: str) -> None:
        self.severe(msg)

    def fatal(self, msg: str) -> None:
        self._log(logging.CRITICAL, msg)

    # Some call sites may use .log(level, msg)
    def log(self, levelno: int, msg: str) -> None:
        self._log(levelno, msg)


def build_logger(cfg: _CfgProto):
    """
    Build a LOG object for a given module identity.

    Returns:
        - EWTS logger (ewts.get_logger) if ewts is installed
        - otherwise a standalone adapter with the same call surface
    """
    module_key = getattr(cfg, "EWTS_MODULE_KEY")
    module_id = getattr(cfg, "EWTS_MODULE_ID")

    getenv_any = _get_getenv_any()

    # If ewts exists, prefer it (ngen routing/formatting stays in EWTS)
    try:
        from ewts import get_logger  # type: ignore
        return get_logger(module_key)
    except Exception:
        return _StdLoggerAdapter(module_id, getenv_any)
