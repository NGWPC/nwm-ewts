import sys
from pathlib import Path

import pytest

# Ensure 'src' is importable when package isn't installed (editable install not assumed).
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def clean_ewts_env(monkeypatch):
    """Clean EWTS-related environment variables and clear logger cache."""
    # Core EWTS env vars
    monkeypatch.delenv("NGEN_RESULTS_DIR", raising=False)
    monkeypatch.delenv("EWTS_LOG_DIR", raising=False)
    monkeypatch.delenv("EWTS_LOG_LEVEL", raising=False)
    monkeypatch.delenv("EWTS_NGEN_BRIDGE_LIB", raising=False)

    # Common per-module overrides used in tests/examples
    for k in [
        "TROUTE_LOGLEVEL",
        "CFE_LOGLEVEL",
        "NGEN_LOGLEVEL",
        "FORCING_LOGLEVEL",
    ]:
        monkeypatch.delenv(k, raising=False)

    # Clear in-process cache
    try:
        from ewts import logger as _logger_mod  # type: ignore
        _logger_mod._LOGGER_CACHE.clear()  # pylint: disable=protected-access
    except Exception:
        pass

    yield

    # Defensive cleanup
    try:
        from ewts import logger as _logger_mod  # type: ignore
        _logger_mod._LOGGER_CACHE.clear()  # pylint: disable=protected-access
    except Exception:
        pass
