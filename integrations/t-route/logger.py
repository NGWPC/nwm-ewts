"""
t_route.logger
==============

Centralized logging entry point for t-route.

Usage in t-route source files:
    from t_route.logger import LOG

    LOG.info("starting routing")
    LOG.perform("JIT Preprocessing time %s seconds." % (time.time() - start_time))
    LOG.severe("routing failed")

Behavior:
- If the EWTS runtime package (`ewts`) is available:
    * LOG is an EWTS logger bound to the T-Route module key.
    * Messages are routed through EWTS and, when applicable, through ngen.
    * Log formatting, routing, and splitting are handled by EWTS.

- If the EWTS package is NOT available:
    * LOG falls back to a standard Python logging adapter.
    * Messages are written to stderr with a timestamp, logger name, and level.
    * EWTS-specific methods (e.g., perform(), severe()) are mapped to
      appropriate standard logging levels.

Environment variables (standalone / fallback mode):
- T_ROUTE_LOGLEVEL or TROUTE_LOGLEVEL
    Sets the minimum log level for t-route when EWTS is not installed.
    Accepted values (case-insensitive):
        DEBUG, PERFORM, INFO, WARNING/WARN, ERROR/SEVERE, FATAL/CRITICAL
        or a numeric value (e.g., 10, 15, 20, 40).

    Default: INFO

Notes:
- Call sites should never import or configure Python's logging module directly.
- All logging in t-route should go through this LOG object.
- The call surface is identical regardless of whether EWTS is present.
"""

from __future__ import annotations

import logging
import os


# -----------------------------------------------------------------------------
# Fallback: add a real PERFORM level to Python's logging so it prints as "PERFORM"
# -----------------------------------------------------------------------------
PERFORM_LEVEL = 15

# Register the level name only once
if logging.getLevelName(PERFORM_LEVEL) != "PERFORM":
    logging.addLevelName(PERFORM_LEVEL, "PERFORM")


def _parse_level(value: str | None) -> int | None:
    """
    Parse an environment log level value.

    Accepts (case-insensitive):
      DEBUG, PERFORM, INFO, WARNING/WARN, ERROR/SEVERE, FATAL/CRITICAL
    Also accepts numeric values like 10, 15, 20, 40.
    """
    if not value:
        return None

    s = value.strip().upper()
    if not s:
        return None

    if s.isdigit():
        try:
            return int(s)
        except Exception:
            return None

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
    }.get(s)


class _StdLoggerAdapter:
    """
    Minimal adapter so t-route logging calls work whether EWTS is installed or not.

    Provides: debug/perform/info/warning/severe/error/fatal
    """

    def __init__(self, name: str):
        self._log = logging.getLogger(name)

        # Avoid duplicating handlers if this module is imported multiple times
        if not self._log.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._log.addHandler(handler)

        # Apply env-controlled level (standalone fallback only)
        level = (
            _parse_level(os.getenv("T_ROUTE_LOGLEVEL"))
            or _parse_level(os.getenv("TROUTE_LOGLEVEL"))  # optional alias
            or logging.INFO
        )
        self._log.setLevel(level)

    def debug(self, msg: str) -> None:
        self._log.debug(msg)

    def perform(self, msg: str) -> None:
        # Emit at the custom PERFORM level so it prints as "PERFORM"
        self._log.log(PERFORM_LEVEL, msg)

    def info(self, msg: str) -> None:
        self._log.info(msg)

    def warning(self, msg: str) -> None:
        self._log.warning(msg)

    def severe(self, msg: str) -> None:
        # EWTS SEVERE maps to ERROR in stdlib logging
        self._log.error(msg)

    # Alias
    def error(self, msg: str) -> None:
        self.severe(msg)

    def fatal(self, msg: str) -> None:
        # EWTS FATAL maps to CRITICAL in stdlib logging
        self._log.critical(msg)


# -----------------------------------------------------------------------------
# Preferred: EWTS runtime logger (if available). Fallback: stdlib adapter.
# -----------------------------------------------------------------------------
try:
    from ewts import get_logger
    from ewts.modules import T_ROUTE_KEY

    LOG = get_logger(T_ROUTE_KEY)

except ImportError:
    LOG = _StdLoggerAdapter("t-route")
