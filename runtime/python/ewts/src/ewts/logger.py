from __future__ import annotations

import os
import sys

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any
import traceback

import logging

# Register EWTS PERFORM level with Python logging
logging.addLevelName(15, "PERFORM")

from .config import load_config, get_level_for_ewts_id
from .formatter import format_prefix, split_lines
from .paths import make_log_path
from .helper import getenv_any

try:
    from .module_keys import ewts_id_from_key
except Exception:
    ewts_id_from_key = None  # type: ignore

try:
    from .log_levels import LEVELS
except Exception:
    LEVELS = {"NOTSET": 0, "DEBUG": 10, "PERFORM": 15, "INFO": 20, "WARNING": 30, "SEVERE": 40, "FATAL": 50}

# Reverse lookup for printing level names
_LEVEL_NAMES = {v: k for k, v in LEVELS.items()}

_init_printed = set()

def _level_name(level: int) -> str:
    return _LEVEL_NAMES.get(level, str(level))

def _resolve_ewts_id(module_key_or_ewts_id: str) -> str:
    s = (module_key_or_ewts_id or "").strip()
    if not s:
        return "UNKNOWN"
    if ewts_id_from_key is not None:
        v = ewts_id_from_key(s)
        if v:
            return v
    return s.upper()

@dataclass
class _NgenBridge:
    lib: ctypes.CDLL
    fn: object

    @staticmethod
    def try_load() -> Optional["_NgenBridge"]:
        # Optional override path (use getenv_any for embedded python correctness)
        so_path = getenv_any("EWTS_NGEN_BRIDGE_LIB", "").strip()
        candidates = []
        if so_path:
            candidates.append(so_path)
        # Soname candidates (adjust to your build/install)
        candidates.extend(["libewts_ngen_bridge.so",])

        last_err = None
        for cand in candidates:
            try:
                lib = ctypes.CDLL(cand)
                fn = lib.ewts_ngen_log
                fn.argtypes = (ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
                fn.restype = None
                return _NgenBridge(lib=lib, fn=fn)
            except Exception:
                continue
        
        if getenv_any("EWTS_DEBUG", ""):
            print("EWTS: failed to load ngen bridge:", last_err)

        return None

    def log(self, ewts_id: str, level: int, message: str) -> None:
        b_id = ewts_id.encode("utf-8")
        b_msg = (message or "").encode("utf-8")
        self.fn(b_id, int(level), b_msg)

class EwtsLogger:
    """Logger keyed strictly by ewts_id."""

    def __init__(self, ewts_id: str):
        self.ewts_id = ewts_id.upper()
        self._bridge: Optional[_NgenBridge] = None
        self._log_path: Optional[Path] = None
        self._min_level: int = LEVELS.get("INFO", 20)
        self._init()

    def _init(self) -> None:

        cfg = load_config(self.ewts_id)
        self._min_level = cfg.default_level

        if not cfg.enabled:
            if self.ewts_id not in _init_printed:
                print(f"EWTS {self.ewts_id} logging is DISABLED")
            self._min_level = 999
            _init_printed.add(self.ewts_id)
            return

        if self.ewts_id not in _init_printed:    
            print(f"EWTS {self.ewts_id} logging is ENABLED")

            env_key = f"{self.ewts_id}_LOGLEVEL"
            env_val = getenv_any(env_key, "").strip()

            if env_val:
                if env_val.isdigit():
                    env_level_name = _level_name(int(env_val))
                else:
                    env_level_name = env_val.upper()
                print(f"EWTS {self.ewts_id} log level from env var {env_key} is {env_level_name}")
            else:
                print(f"EWTS {self.ewts_id} log level from default EWTS_LOG_LEVEL")

            print(f"EWTS {self.ewts_id} log level set to {_level_name(self._min_level)}")

        if cfg.ngen_active:
            self._bridge = _NgenBridge.try_load()
            # If the bridge isn't available, we still fall back to standalone.
            if self._bridge is not None:
                if self.ewts_id not in _init_printed:
                    print(f"EWTS {self.ewts_id} using ngen for logging")
                _init_printed.add(self.ewts_id)
                return

        # Standalone file sink
        if self.ewts_id not in _init_printed:
            print(f"EWTS {self.ewts_id} using standalone file logging")
        self._log_path = make_log_path(self.ewts_id, cfg.log_dir)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.ewts_id not in _init_printed:
            print(f"EWTS {self.ewts_id} log file: {self._log_path}")
        _init_printed.add(self.ewts_id)

    @staticmethod
    def _format_msg(msg: Any, args: tuple[Any, ...]) -> str:
        s = "" if msg is None else str(msg)
        if not args:
            return s
        try:
            return s % args
        except Exception:
            # Don't crash logging if formatting is wrong
            return f"{s} {args}"

    @staticmethod
    def _maybe_add_exc(text: str, exc_info) -> str:
        if not exc_info:
            return text
        if exc_info is True:
            return text + "\n" + traceback.format_exc()
        # exc_info can be (type, value, tb)
        try:
            return text + "\n" + "".join(traceback.format_exception(*exc_info))
        except Exception:
            return text
    
    def set_level_from_env(self) -> None:
        # Allow user to change at runtime (e.g., after ngen sets env vars)
        self._min_level = get_level_for_ewts_id(self.ewts_id)
        print(f"EWTS {self.ewts_id} log level set to ")

    def log(self, level: int, msg, *args, exc_info=None, **kwargs) -> None:
        if int(level) < int(self._min_level):
            return

        text = self._format_msg(msg, args)
        text = self._maybe_add_exc(text, exc_info)

        if self._bridge is not None:
            self._bridge.log(self.ewts_id, int(level), text)
            return

        assert self._log_path is not None
        prefix = format_prefix(self.ewts_id, int(level))
        with self._log_path.open("a", encoding="utf-8") as f:
            for line in split_lines(text):
                f.write(f"{prefix} {line}\n")

    # Convenience methods
    def debug(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("DEBUG", 10), msg, *args, **kwargs)

    def perform(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("PERFORM", 15), msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("INFO", 20), msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("WARNING", 30), msg, *args, **kwargs)

    def severe(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("SEVERE", 40), msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs) -> None:
        self.log(LEVELS.get("FATAL", 50), msg, *args, **kwargs)

    # Aliases
    def error(self, msg, *args, **kwargs) -> None:
        self.severe(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs) -> None:
        self.fatal(msg, *args, **kwargs)

_LOGGER_CACHE: Dict[str, EwtsLogger] = {}

def get_logger(module_key_or_ewts_id: str) -> EwtsLogger:
    """Return a cached logger keyed by ewts_id."""
    ewts_id = _resolve_ewts_id(module_key_or_ewts_id)
    lg = _LOGGER_CACHE.get(ewts_id)
    if lg is not None:
        return lg
    lg = EwtsLogger(ewts_id)
    _LOGGER_CACHE[ewts_id] = lg
    return lg
