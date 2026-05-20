"""Classes to enable sending structured data payloads through log file entries.
Some of the syntax would be simpler with pydantic, but that libray was not part
of nwm-ewts dependencies when this was written."""

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum

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


@dataclass
class Payload:
    """Log payload class for status reporting via logs.

    Parameters
    ----------
    status : Status
        Module status.
    prog : float, optional
        Module progress (0.0 to 1.0), by default None.
    msg : str, optional
        Message.
    modnm : str, optional
        Module name.

    Raises
    ----------
    ValueError
        If there is a validation error with the provided inputs.
    """

    status: Status
    prog: float | None = None
    msg: str | None = None
    modnm: str | None = None

    def __post_init__(self):
        errs: list[Exception] = []
        if not isinstance(self.status, Status):
            errs.append(TypeError(f"status: expect {Status}, got {type(self.status)}"))
        if isinstance(self.prog, float):
            if not (0.0 <= self.prog <= 1.0):
                errs.append(
                    ValueError(
                        f"prog: expect value between 0.0 and 1.0, got {self.prog}"
                    )
                )
        elif self.prog is not None:
            errs.append(
                TypeError(f"prog: expect {float} or None, got {type(self.prog)}")
            )
        if not isinstance(self.msg, (str, type(None))):
            errs.append(TypeError(f"msg: expect {str} or None, got {type(self.msg)}"))
        if not isinstance(self.modnm, (str, type(None))):
            errs.append(
                TypeError(f"modnm: expect {str} or None, got {type(self.modnm)}")
            )
        if errs:
            raise ValueError(f"Errors constructing Payload: {errs}")

    @property
    def json(self) -> str:
        """A json string (dict) representation for logging."""
        return json.dumps(asdict(self))

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
    """Factory for Payload object.

    Construct and return a Payload from a log message, if it contains the sentinel. Otherwise, return None.
    Requires that the provided string is one line (Payloads should have escape newline chars via json.dumps(asdict(self))).

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
            d = json.loads(payload_raw_str)
            d["status"] = Status(d["status"])
            payload = Payload(**d)
        except Exception as e:
            raise ValueError(
                f"Payload was detected in log message, but it failed to parse. Full message: {repr(log_msg)}. Payload raw string: {repr(payload_raw_str)}. Exception: {e}"
            ) from e
        return payload
    else:
        return None


@dataclass
class LogParts:
    """Parts of a log line, optionally with structured Payload substructure.

    Parameters
    ----------
    dt : datetime
        The timestamp of the log line.
    module : str
        The module that sent the message.
    level : str
        The log level of the message.
    msg : str
        The message (may include raw payload string).
    payload : Payload | None
        The extracted Payload if the message contains a structured payload (wrapped in sentinel strings), else None.

    Raises
    ----------
    ValueError
        If there is a validation error with the provided inputs.
    """

    dt: datetime
    module: str
    level: str
    msg: str
    payload: Payload | None

    def __post_init__(self):
        errs: list[Exception] = []
        if not isinstance(self.dt, datetime):
            errs.append(TypeError(f"dt: expect {datetime}, got {type(self.dt)}"))
        if not isinstance(self.module, str):
            errs.append(TypeError(f"module: expect {str}, got {type(self.module)}"))
        if not isinstance(self.level, str):
            errs.append(TypeError(f"level: expect {str}, got {type(self.level)}"))
        if not isinstance(self.msg, str):
            errs.append(TypeError(f"msg: expect {str}, got {type(self.msg)}"))
        if not isinstance(self.payload, (Payload, type(None))):
            errs.append(
                TypeError(
                    f"payload: expect {Payload} or None, got {type(self.payload)}"
                )
            )
        if errs:
            raise ValueError(f"Errors constructing LogParts: {errs}")


def parts_of_log_line(line: str) -> LogParts:
    """Factory for LogParts object.

    Construct and return a LogParts instance by parsing a log line (split on whitespace).
    Asserts that the log line has at least 4 whitespace-delimited parts:
    timestamp (datetime ISO string), module name, log level name, message.

    The message may contain whitespace (it is at the end).

    The message may include a Payload JSON string wrapped in the sentinel strings
    MSG_PAYLOAD_SENTINEL_START and MSG_PAYLOAD_SENTINEL_END. If it does include the
    sentinel strings, then the payload JSON dictionary between them will be parsed into
    a Payload instance and included as attribute of the returned LogParts. If not, the
    payload attribute of the returned LogParts will be None.

    Parameters
    ----------
    line : str
        The log line to parse.

    Returns
    -------
    LogParts
        The constructed LogParts instance.

    Raises
    ----------
    ValueError
        If the line has less than 4 parts after splitting on whitespace.
        If the timestamp part does not use UTC timezone.
    """
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
