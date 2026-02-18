from __future__ import annotations

from pathlib import Path

from .formatter import compact_utc_timestamp

def default_run_logs_dir() -> Path:
    return Path.home() / "run_logs"

def make_log_path(ewts_id: str, log_dir: Path) -> Path:
    # ~/run_logs/<EWTSID>_<YYYYMMDDTHHMMSS>.log
    ts = compact_utc_timestamp()
    safe_id = (ewts_id or "UNKNOWN").upper()
    return log_dir / f"{safe_id}_{ts}.log"
