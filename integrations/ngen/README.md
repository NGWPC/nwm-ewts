# EWTS ngen Integration

The `integrations/ngen/` layer routes EWTS runtime messages from C, C++,
Fortran, and Python through a shared `ngen`-aware logger.

## Responsibilities

The `ngen` integration layer:

- reads `ngen_logging.json` when `NGEN_RESULTS_DIR` is set
- determines effective module log levels
- exports `EWTS_ENABLED` and `<MODULE>_LOGLEVEL` environment variables
- formats standard log records
- supports unified and split-by-module log files
- creates one log file per MPI rank
- writes structured STATUS payload records to a dedicated payload log file

## Bridge API

```c
void ewts_ngen_log(
    const char* ewts_id,
    int level,
    const char* message);

void ewts_ngen_payload_status(
    const char* ewts_id,
    const char* status,
    double prog,
    const char* msg,
    const char* modnm);
```

`ewts_ngen_log(...)` is used for standard runtime log messages. If `level` is
`STATUS`, the message is treated as a payload message.

`ewts_ngen_payload_status(...)` is used by C, C++, and Fortran runtime helpers to
write structured payloads directly.

## Initialization

The `ngen` logger initializes on the first log or payload call. Initialization:

1. checks `NGEN_RESULTS_DIR`
2. determines MPI rank when MPI is initialized
3. reads `ngen_logging.json` when available
4. exports runtime environment variables
5. opens the standard log file when needed
6. opens the payload log file on receipt of the first payload message

No explicit logger initialization call is required from `ngen`.

## Standard log files

Unified mode writes one standard log file per rank:

```text
ngen_mpi_process_<rank>.log
```

Split-by-module mode writes one standard log file per EWTS ID per rank:

```text
cfe_mpi_process_<rank>.log
noahowp_mpi_process_<rank>.log
ueb_bmi_mpi_process_<rank>.log
```

Enable split mode with:

```json
{
  "split_logs_by_module": true
}
```

If `NGEN_LOG_FILE_PREFIX` is set, the prefix is prepended to the file stem.

## Payload log file

Payload records are written to one payload file per rank:

```text
ngen_payload_mpi_process_<rank>.log
```

The payload file is not split by module. It is created only after the first
payload message is received.

If `NGEN_LOG_FILE_PREFIX` is set, the prefix is prepended to the payload file
stem.

## Payload record format

Payload records are formatted like standard log records:

```text
timestamp EWTS_ID STATUS  <MSG_DATA>{json}</MSG_DATA>
```

Example:

```text
2026-06-23T23:42:36.219Z NOAHOWP STATUS  <MSG_DATA>{"status":"INITIALIZING","prog":"0.10000000000000001","msg":"Initializing NOAHOWP BMI","modnm":"NOAHOWP"}</MSG_DATA>
```

The JSON payload contains:

| Field | Meaning |
|---|---|
| `status` | Payload status value |
| `prog` | Progress value |
| `msg` | Human-readable message |
| `modnm` | Module/component name |

The `<MSG_DATA>` and `</MSG_DATA>` sentinels are retained for downstream payload
consumers.

## STATUS messages from Python

Python modules can emit payload records by logging a STATUS message containing
sentinel-wrapped JSON:

```python
import json

LOG.status(
    "<MSG_DATA>"
    + json.dumps(
        {
            "status": "INITIALIZING",
            "prog": 0.1,
            "msg": "Creating network of type NHF",
            "modnm": "t-route",
        },
        separators=(",", ":"),
    )
    + "</MSG_DATA>"
)
```

The bridge extracts the JSON, validates it, and writes the payload record to the
payload log.

## Structured payload calls from C, C++, and Fortran

C and C++ runtimes expose:

```c
PAYLOAD_STATUS(ewts_id, status, prog, msg, modnm)
```

The Fortran runtime exposes:

```fortran
call payload_status(ewts_id, status, prog, msg, modnm)
```

All of these paths call `ewts_ngen_payload_status(...)` and produce the same
payload log format.

## Malformed payload handling

If a STATUS payload message is malformed, the bridge writes an ERROR payload
record instead of dropping the message. Missing sentinels and invalid JSON are
reported in the payload `msg` field.

## Build

Configure EWTS with `ngen` support enabled:

```bash
cmake -B cmake_build -S . -DEWTS_WITH_NGEN=ON
cmake --build cmake_build -j
```

## Related documentation

- `runtime/c/README.md`
- `runtime/cpp/README.md`
- `runtime/fortran/README.md`
- `runtime/python/README.md`
