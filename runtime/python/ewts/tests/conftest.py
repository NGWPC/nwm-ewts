import logging
import os
import pytest

import ewts.logger as logger


@pytest.fixture
def clean_ewts_env(monkeypatch):
    monkeypatch.delenv("EWTS_ENABLED", raising=False)
    monkeypatch.delenv("EWTS_LOG_DIR", raising=False)
    monkeypatch.delenv("EWTS_LOG_LEVEL", raising=False)
    monkeypatch.delenv("TROUTE_LOGLEVEL", raising=False)
    monkeypatch.delenv("NGEN_RESULTS_DIR", raising=False)

    logger._LOGGER_CACHE.clear()
    logger._init_printed.clear()

    # remove handlers from stdlib loggers created during tests
    for name in list(logging.root.manager.loggerDict.keys()):
        if name.startswith("ewts."):
            log = logging.getLogger(name)
            log.handlers.clear()
