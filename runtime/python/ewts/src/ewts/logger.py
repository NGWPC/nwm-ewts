from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

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
        candidates.extend(["libewts_ngen_logger.so", "libewts_ngen.so"])

        for cand in candidates:
            try:
                lib = ctypes.CDLL(cand)
                fn = lib.ewts_ngen_log
                fn.argtypes = (ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
                fn.restype = None
                return _NgenBridge(lib=lib, fn=fn)
            except Exception:
                continue
        return None

    def log(self, ewts_id: str, level: int, message: str) -> None:
        b_id = ewts_id.encode("utf-8")
        b_msg = (message or "").encode("utf-8")
        self.fn(b_id, int(level), b_msg)

class EwtsLogger:
    """Logger keyed strictly by ewts_id (no __name__ anywhere)."""

    def __init__(self, ewts_id: str):
        self.ewts_id = ewts_id.upper()
        self._bridge: Optional[_NgenBridge] = None
        self._log_path: Optional[Path] = None
        self._min_level: int = LEVELS.get("INFO", 20)
        self._init()

    def _init(self) -> None:
        cfg = load_config(self.ewts_id)
        self._min_level = cfg.default_level

        if cfg.ngen_active:
            self._bridge = _NgenBridge.try_load()
            # If the bridge isn't available, we still fall back to standalone.
            if self._bridge is not None:
                return

        # Standalone file sink
        self._log_path = make_log_path(self.ewts_id, cfg.log_dir)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def set_level_from_env(self) -> None:
        # Allow user to change at runtime (e.g., after ngen sets env vars)
        self._min_level = get_level_for_ewts_id(self.ewts_id)

    def log(self, level: int, message: str) -> None:
        if int(level) < int(self._min_level):
            return

        if self._bridge is not None:
            self._bridge.log(self.ewts_id, int(level), message)
            return

        # Standalone write
        assert self._log_path is not None
        prefix = format_prefix(self.ewts_id, int(level))
        with self._log_path.open("a", encoding="utf-8") as f:
            for line in split_lines(message):
                f.write(f"{prefix} {line}\n")

    # Convenience methods
    def debug(self, msg: str) -> None:
        self.log(LEVELS.get("DEBUG", 10), msg)

    def perform(self, msg: str) -> None:
        self.log(LEVELS.get("PERFORM", 15), msg)

    def info(self, msg: str) -> None:
        self.log(LEVELS.get("INFO", 20), msg)

    def warning(self, msg: str) -> None:
        self.log(LEVELS.get("WARNING", 30), msg)

    def severe(self, msg: str) -> None:
        self.log(LEVELS.get("SEVERE", 40), msg)

    # Alias
    def error(self, msg: str) -> None:
        self.severe(msg)

    def fatal(self, msg: str) -> None:
        self.log(LEVELS.get("FATAL", 50), msg)

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
