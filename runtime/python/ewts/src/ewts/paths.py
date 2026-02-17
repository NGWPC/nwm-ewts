import os
from datetime import datetime, timezone

from .helper import getenv_any
from .constants import (
    MODULE_NAME,
    EV_EWTS_LOG_DIR,
    EV_EWTS_RANK,
    EV_EWTS_SPLIT_BY_MOD,
    DS,
    LOG_DIR_DEFAULT,
    LOG_FILE_EXT,
)

def create_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

def _in_ngen():
    d = getenv_any(EV_EWTS_LOG_DIR, "").strip()
    r = getenv_any(EV_EWTS_RANK, "").strip()
    return bool(d) and bool(r)

def get_log_file_path():
    appendEntries = True
    logFilePath = ""

    if _in_ngen():
        log_dir = getenv_any(EV_EWTS_LOG_DIR, "").strip()
        rank = int(getenv_any(EV_EWTS_RANK, "0").strip())
        split = int(getenv_any(EV_EWTS_SPLIT_BY_MOD, "0").strip() or "0")

        os.makedirs(log_dir, exist_ok=True)

        if split == 0:
            logFilePath = f"{log_dir}{DS}ngen_{rank}.{LOG_FILE_EXT}"
        else:
            # module-specific per-rank file
            safe_mod = MODULE_NAME.replace(" ", "_")
            logFilePath = f"{log_dir}{DS}{safe_mod}_{rank}.{LOG_FILE_EXT}"

        # in ngen, always append
        appendEntries = True

    else:
        # standalone: always user home directory
        baseDir = f"{os.path.expanduser('~')}{DS}{LOG_DIR_DEFAULT}"
        os.makedirs(baseDir, exist_ok=True)

        logFilePath = f"{baseDir}{DS}{MODULE_NAME}_{create_timestamp()}.{LOG_FILE_EXT}"
        appendEntries = False  # new file per run

    # Validate file can be opened
    try:
        mode = "a" if appendEntries else "w"
        with open(logFilePath, mode):
            pass
    except Exception:
        logFilePath = ""  # causes stdout fallback in config.py

    return logFilePath, appendEntries
