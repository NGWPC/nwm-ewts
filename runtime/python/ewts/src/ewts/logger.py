from __future__ import annotations

import ctypes
import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_level_for_ewts_id, load_config, set_runtime_override
from .formatter import format_prefix, split_lines
from .helper import getenv_any
from .log_levels import parse_log_level
from .paths import make_log_path

# Register EWTS PERFORM level with Python logging
logging.addLevelName(15, "PERFORM")

try:
    from .module_keys import ewts_id_from_key
except Exception:
    ewts_id_from_key = None  # type: ignore

try:
    from .log_levels import LEVELS
except Exception:
    LEVELS = {
        "NOTSET": 0,
        "DEBUG": 10,
        "PERFORM": 15,
        "INFO": 20,
        "WARNING": 30,
        "SEVERE": 40,
        "FATAL": 50,
    }

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
            except Exception as e:
                last_err = e
                continue

        if getenv_any("EWTS_DEBUG", ""):
            print("EWTS: failed to load ngen bridge:", last_err, flush=True)

        return None

    def log(self, ewts_id: str, level: int, message: str) -> None:
        b_id = ewts_id.encode("utf-8")
        b_msg = (message or "").encode("utf-8")
        self.fn(b_id, int(level), b_msg)


class EwtsHandler(logging.Handler):
    """
    Logging handler that routes standard Python logging records
    into the EWTS backend.
    """

    def __init__(self, ewts_logger: "EwtsLogger"):
        super().__init__(level=logging.NOTSET)
        self.ewts_logger = ewts_logger

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = self.ewts_logger._map_python_level_to_ewts(record.levelno)
            self.ewts_logger._write(level, msg)
        except Exception:
            self.handleError(record)


class EwtsLogger:
    """Logger keyed strictly by ewts_id, with Python logging compatibility."""

    def __init__(self, ewts_id: str):
        self.ewts_id = ewts_id.upper()
        self._bridge: Optional[_NgenBridge] = None
        self._log_path: Optional[Path] = None
        self._min_level: int = LEVELS.get("INFO", 20)

        self._init()

        # Backing Python logger for compatibility with logging.Logger API
        self._logger = logging.getLogger(f"ewts.{self.ewts_id}")
        self._logger.propagate = False

        # Replace any existing EWTS handler so it always points at *this* EwtsLogger.
        # This is important because logging.getLogger(name) returns the same named
        # Python logger object process-wide, and an older EwtsHandler may still be
        # attached from an earlier initialization attempt.
        for h in list(self._logger.handlers):
            if isinstance(h, EwtsHandler):
                self._logger.removeHandler(h)

        handler = EwtsHandler(self)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

        # Keep Python logger level aligned with EWTS min level
        self._logger.setLevel(self._min_level)

    def _init(self) -> None:
        cfg = load_config(self.ewts_id)
        self._min_level = cfg.default_level
        self._mpi_rank = cfg.mpi_rank

        self._prefix = f"[rank {self._mpi_rank}] EWTS" if self._mpi_rank >= 0 else "EWTS"

        if not cfg.enabled:
            if self.ewts_id not in _init_printed:
                print(f"{self._prefix} {self.ewts_id} logging is DISABLED", flush=True)
            self._min_level = 999
            _init_printed.add(self.ewts_id)
            return

        if self.ewts_id not in _init_printed:
            print(f"{self._prefix} {self.ewts_id} logging is ENABLED", flush=True)

            module_env_key = f"{self.ewts_id}_LOGLEVEL"
            module_env_val = getenv_any(module_env_key, "").strip()

            default_env_key = "EWTS_LOG_LEVEL"
            default_env_val = getenv_any(default_env_key, "").strip()

            if module_env_val:
                env_level_name = (
                    _level_name(int(module_env_val))
                    if module_env_val.isdigit()
                    else module_env_val.upper()
                )
                print(
                    f"{self._prefix} {self.ewts_id} log level from env var "
                    f"{module_env_key} is {env_level_name}",
                    flush=True,
                )
            elif default_env_val:
                env_level_name = (
                    _level_name(int(default_env_val))
                    if default_env_val.isdigit()
                    else default_env_val.upper()
                )
                print(
                    f"{self._prefix} {self.ewts_id} log level from env var "
                    f"{default_env_key} is {env_level_name}",
                    flush=True,
                )
            else:
                print(
                    f"{self._prefix} {self.ewts_id} no module-specific or default EWTS log "
                    f"level env var found; defaulting to INFO",
                    flush=True,
                )

            print(f"{self._prefix} {self.ewts_id} log level set to {_level_name(self._min_level)}", flush=True,)

        if cfg.running_in_ngen:
            self._bridge = _NgenBridge.try_load()
            # If the bridge isn't available, we still fall back to standalone.
            if self._bridge is not None:
                if self.ewts_id not in _init_printed:
                    print(f"{self._prefix} {self.ewts_id} using ngen for logging", flush=True)
                _init_printed.add(self.ewts_id)
                return

        # Standalone file sink
        if self.ewts_id not in _init_printed:
            print(f"{self._prefix} {self.ewts_id} using standalone file logging", flush=True)

        if cfg.log_file_name:
            self._log_path = Path(cfg.log_dir) / cfg.log_file_name
        else:
            self._log_path = make_log_path(self.ewts_id, cfg.log_dir)

        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.ewts_id not in _init_printed:
            print(f"{self._prefix} {self.ewts_id} log file: {self._log_path}", flush=True)
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

    @staticmethod
    def _map_python_level_to_ewts(level: int) -> int:
        if level >= logging.CRITICAL:
            return LEVELS.get("FATAL", 50)
        if level >= logging.ERROR:
            return LEVELS.get("SEVERE", 40)
        if level >= logging.WARNING:
            return LEVELS.get("WARNING", 30)
        if level >= logging.INFO:
            return LEVELS.get("INFO", 20)
        if level >= LEVELS.get("PERFORM", 15):
            return LEVELS.get("PERFORM", 15)
        return LEVELS.get("DEBUG", 10)

    def _write(self, level: int, text: str) -> None:
        if int(level) < int(self._min_level):
            return

        if self._bridge is not None:
            self._bridge.log(self.ewts_id, int(level), text)
            return

        assert self._log_path is not None
        prefix = format_prefix(self.ewts_id, int(level))
        with self._log_path.open("a", encoding="utf-8") as f:
            for line in split_lines(text):
                f.write(f"{prefix} {line}\n")

    def set_level_from_env(self) -> None:
        self._min_level = get_level_for_ewts_id(self.ewts_id)
        self._logger.setLevel(self._min_level)
        print(f"{self._prefix} {self.ewts_id} log level set to {_level_name(self._min_level)}", flush=True)

    def log(self, level: int, msg, *args, exc_info=None, **kwargs) -> None:
        text = self._format_msg(msg, args)
        text = self._maybe_add_exc(text, exc_info)
        self._write(int(level), text)

    # Convenience methods route through the Python logger so any user-added
    # handlers also receive records.
    def debug(self, msg, *args, **kwargs) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def perform(self, msg, *args, **kwargs) -> None:
        self._logger.log(LEVELS.get("PERFORM", 15), msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def severe(self, msg, *args, **kwargs) -> None:
        self._logger.error(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs) -> None:
        self._logger.critical(msg, *args, **kwargs)

    # Aliases
    def error(self, msg, *args, **kwargs) -> None:
        self.severe(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs) -> None:
        self.fatal(msg, *args, **kwargs)

    # Compatibility properties/methods for standard logging patterns
    @property
    def handlers(self):
        return self._logger.handlers

    @property
    def name(self) -> str:
        return self._logger.name

    @property
    def propagate(self) -> bool:
        return self._logger.propagate

    @propagate.setter
    def propagate(self, value: bool) -> None:
        self._logger.propagate = value

    def addHandler(self, handler: logging.Handler) -> None:
        self._logger.addHandler(handler)

    def removeHandler(self, handler: logging.Handler) -> None:
        self._logger.removeHandler(handler)

    def setLevel(self, level: int) -> None:
        self._min_level = int(level)
        self._logger.setLevel(int(level))

    def getEffectiveLevel(self) -> int:
        return self._logger.getEffectiveLevel()

    def isEnabledFor(self, level: int) -> bool:
        return int(level) >= int(self._min_level)

    def hasHandlers(self) -> bool:
        return self._logger.hasHandlers()


class BoundEwtsLoggerProxy:
    """
    Proxy returned by get_logger() so module-level logger creation does not
    trigger EWTS initialization during import time.

    The real EwtsLogger is created only when bind() is called explicitly.
    """

    def __init__(self, ewts_id: str):
        self.ewts_id = ewts_id.upper()
        self._real_logger: Optional[EwtsLogger] = None

    def bind(self) -> EwtsLogger:
        if self._real_logger is None:
            self._real_logger = EwtsLogger(self.ewts_id)
        return self._real_logger

    def is_bound(self) -> bool:
        return self._real_logger is not None
    
    def get_bound_logger(self) -> EwtsLogger:
        if self._real_logger is None:
            raise RuntimeError(
                f"EWTS logger {self.ewts_id} has not been bound yet."
            )
        return self._real_logger

    def _require_bound(self) -> EwtsLogger:
        if self._real_logger is None:
            raise RuntimeError(
                f"EWTS logger {self.ewts_id} has not been bound yet. "
                f"Call ewts.bind_logger('{self.ewts_id}') or LOG.bind() "
                f"from the runtime entry point before logging."
            )
        return self._real_logger

    def __getattr__(self, name):
        return getattr(self._require_bound(), name)

    @property
    def handlers(self):
        return self._require_bound().handlers

    @property
    def name(self) -> str:
        return self._require_bound().name

    @property
    def propagate(self) -> bool:
        return self._require_bound().propagate

    @propagate.setter
    def propagate(self, value: bool) -> None:
        self._require_bound().propagate = value

    def addHandler(self, handler: logging.Handler) -> None:
        self._require_bound().addHandler(handler)

    def removeHandler(self, handler: logging.Handler) -> None:
        self._require_bound().removeHandler(handler)

    def setLevel(self, level: int) -> None:
        self._require_bound().setLevel(level)

    def getEffectiveLevel(self) -> int:
        return self._require_bound().getEffectiveLevel()

    def isEnabledFor(self, level: int) -> bool:
        return self._require_bound().isEnabledFor(level)

    def hasHandlers(self) -> bool:
        return self._require_bound().hasHandlers()


_LOGGER_CACHE: Dict[str, BoundEwtsLoggerProxy] = {}


def get_logger(module_key_or_ewts_id: str) -> BoundEwtsLoggerProxy:
    """Return a cached logger keyed by ewts_id."""
    ewts_id = _resolve_ewts_id(module_key_or_ewts_id)
    lg = _LOGGER_CACHE.get(ewts_id)
    if lg is not None:
        return lg
    lg = BoundEwtsLoggerProxy(ewts_id)
    _LOGGER_CACHE[ewts_id] = lg
    return lg


def bind_logger(module_key_or_ewts_id: str) -> EwtsLogger:
    """
    Explicitly initialize and bind the logger for the given ewts_id.
    Safe to call multiple times; it returns the same bound logger per process.
    """
    return get_logger(module_key_or_ewts_id).bind()


def setup_logger(
    module_key_or_ewts_id: str,
    *,
    level: str | int | None = None,
    log_dir: str | Path | None = None,
    log_file_name: str | None = None,
    running_in_ngen: bool | None = None,
    enabled: bool | None = None,
    bind_now: bool = False,
) -> BoundEwtsLoggerProxy | EwtsLogger:
    """
    Configure runtime overrides for an EWTS logger.

    This does not have to bind immediately. For ngen/BMI use, callers can
    leave bind=False and explicitly call bind_logger() later during init.
    For standalone manager scripts, bind=True is convenient.
    """
    ewts_id = _resolve_ewts_id(module_key_or_ewts_id)
    parsed_level = parse_log_level(level) if level is not None else None

    set_runtime_override(
        ewts_id,
        running_in_ngen=running_in_ngen,
        enabled=enabled,
        log_dir=log_dir,
        default_level=parsed_level,
        log_file_name=log_file_name,
    )

    if bind_now:
        return bind_logger(ewts_id)

    return get_logger(ewts_id)
