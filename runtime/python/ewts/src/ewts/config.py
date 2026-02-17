import logging
import sys
import os

from .helper import getenv_any
from .constants import (
    MODULE_NAME,
    EV_EWTS_ENABLED,
    EV_MODULE_LOGLEVEL,
    LOG_MODULE_NAME_LEN,
)
from .formatter import CustomFormatter
from .paths import get_log_file_path

_LEVEL_NAME_TO_NUM = {
    "NONE": 0,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "WARN": 30,
    "SEVERE": 40,
    "ERROR": 40,
    "FATAL": 50,
    "CRITICAL": 50,
}

def _parse_level(v: str, default: int = 20) -> int:
    if v is None:
        return default
    s = str(v).strip()
    if not s:
        return default
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        return int(s)
    return _LEVEL_NAME_TO_NUM.get(s.upper(), default)

def _enabled() -> bool:
    raw = getenv_any(EV_EWTS_ENABLED, "").strip()
    if raw == "":
        return True  # default enabled
    try:
        return int(raw) != 0
    except Exception:
        # tolerate legacy strings: "ENABLED"/"DISABLED"
        return raw.strip().lower() != "disabled"

def force_info(handler, logger, msg, *args):
    record = logger.makeRecord(logger.name, logging.INFO, __file__, 0, msg, args, None)
    handler.emit(record)

def configure_logging():
    logger = logging.getLogger(MODULE_NAME)

    if getattr(logger, "_initialized", False):
        return logger

    if not _enabled():
        logger.disabled = True
        logger._initialized = True
        print(f"Module {MODULE_NAME} Logging DISABLED", flush=True)
        return logger

    logFilePath, appendEntries = get_log_file_path()

    handler = (
        logging.FileHandler(logFilePath, mode="a" if appendEntries else "w")
        if logFilePath
        else logging.StreamHandler(sys.stdout)
    )

    lvl_num = _parse_level(getenv_any(EV_MODULE_LOGLEVEL, "20"), default=20)
    log_level = lvl_num if lvl_num in (0,10,20,30,40,50) else 20

    module_fmt = MODULE_NAME.upper().ljust(LOG_MODULE_NAME_LEN)[:LOG_MODULE_NAME_LEN]

    formatter = CustomFormatter(
        fmt=f"%(asctime)s.%(msecs)03d {module_fmt} %(levelname_padded)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.setLevel(log_level)
    logger.addHandler(handler)

    force_info(handler, logger, "Log level set to %s", log_level)
    logger._initialized = True
    return logger
