"""EWTS Python logging helpers.

Public API:
  - get_logger(module_key_or_ewts_id) -> EwtsLogger
  - EwtsLogger methods: debug/info/warning/error/severe/fatal/perform/log
"""
# This unused-looking import is deliberate — it’s part of the public API.
from .logger import get_logger, EwtsLogger  # noqa: F401
