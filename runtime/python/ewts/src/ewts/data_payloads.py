"""Classes to enable sending structured data payloads through log file entries."""

import re
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

MSG_PAYLOAD_SENTINEL_START = "<MSG_DATA>"
MSG_PAYLOAD_SENTINEL_END = "</MSG_DATA>"
EXTRACT_PATTERN = re.compile(
    rf"{MSG_PAYLOAD_SENTINEL_START}(.*?){MSG_PAYLOAD_SENTINEL_END}"
)


class Status(StrEnum):
    """Status enum for log JSON payload."""

    NULL = "NULL"
    INITTING = "INITIALIZING"
    INITTED = "INITIALIZED"
    STARTING = "STARTING"
    INPROG = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class Payload(BaseModel):
    """Log payload class for status reporting via logs.
    __init__ is defined simply to allow positional arguments within Pydantic BaseModel framework."""

    status: Status = Field(description="Status")
    prog: float | None = Field(
        default=None, ge=0, le=1, description="Progress (0.0 to 1.0)"
    )
    msg: str | None = Field(default=None, description="Message")
    modnm: str | None = Field(default=None, description="Module name")

    def __init__(
        self,
        status: Status,
        prog: float | None = None,
        msg: str | None = None,
        modnm: str | None = None,
    ):
        """__init__ is defined simply to allow positional arguments within Pydantic BaseModel framework."""
        super().__init__(status=status, prog=prog, msg=msg, modnm=modnm)

    @property
    def json(self) -> str:
        """A json string (dict) representation for logging."""
        return self.model_dump_json()

    @property
    def json_wrapped(self) -> str:
        """A json string (dict) representation for logging, wrapped with sentinel strings."""
        return f"{MSG_PAYLOAD_SENTINEL_START}{self.json}{MSG_PAYLOAD_SENTINEL_END}"

    def __str__(self) -> str:
        """String representation of the Payload. JSON wrapped with sentinel strings for logging."""
        return self.json_wrapped

    def __format__(self, format_spec) -> str:
        """String representation of the Payload. JSON wrapped with sentinel strings for logging."""
        return self.__str__()


def payload_of_log_msg(log_msg: str) -> Payload | None:
    """Extract a Payload object from a log message, if it contains the sentinel. Otherwise, return None.
    Requires that the provided string is one line (Payloads should have escape newline chars via Pydantic model_dump_json()).

    Parameters
    ----------
    log_msg : str
        The log message to extract the payload from.

    Returns
    -------
    Payload | None
        The extracted Payload object if sentinel wrapping found, else None.

    Raises
    ----------
    ValueError
        If the log message contains a sentinel string wrapping but the content between cannot be parsed into a Payload instance.
        If the log message contains multiple sentinel string wrappings.
    """
    matches = EXTRACT_PATTERN.findall(log_msg)
    if matches:
        if len(matches) != 1:
            raise ValueError(
                f"{len(matches)} payloads detected in log message. Expected 1. Full message: {log_msg}"
            )
        payload_raw_str = matches[0]
        try:
            payload = Payload.model_validate_json(payload_raw_str)
        except Exception as e:
            raise ValueError(
                f"Payload was detected in log message, but failed to parse as JSON into a Payload instance. Full message: {repr(log_msg)}. Payload raw string: {repr(payload_raw_str)}. Exception: {e}"
            ) from e
        return payload
    else:
        return None


class LogParts(BaseModel):
    dt: datetime
    module: str
    level: str
    msg: str
    payload: Payload | None


def parts_of_log_line(line: str) -> LogParts:
    parts = line.split(None, 3)
    if len(parts) < 4:
        raise ValueError(f"Could not parse log line: {repr(line)}")
    timestamp_str, module, level, msg = parts
    dt = datetime.fromisoformat(timestamp_str)
    if dt.tzinfo is None or dt.tzinfo != timezone.utc:
        raise ValueError(
            f"Expected timezone {timezone.utc}, got: {dt.tzinfo}. Full line: {repr(line)}"
        )
    payload = payload_of_log_msg(msg)
    return LogParts(dt=dt, module=module, level=level, msg=msg, payload=payload)
