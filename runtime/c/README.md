# EWTS C Runtime

The EWTS C runtime provides logging support for C modules running either
standalone or under `ngen`.

Installed headers are exposed under `include/ewts/`.

## Public API

```c
void EwtsInit(const char* ewts_id, bool ewts_ngen);
void Log(LogLevel level, const char* fmt, ...);
LogLevel GetLogLevel(void);
bool IsLoggingEnabled(void);

void EwtsLogModule(const char* ewts_id, LogLevel level, const char* fmt, ...);
LogLevel EwtsGetLogLevelModule(const char* ewts_id);
bool EwtsIsLoggingEnabledModule(const char* ewts_id);

void EwtsPayloadStatus(
    const char* ewts_id,
    const char* status,
    double prog,
    const char* msg,
    const char* modnm);

#define PAYLOAD_STATUS(ewts_id, status, prog, msg, modnm) \
    EwtsPayloadStatus((ewts_id), (status), (prog), (msg), (modnm))
```

## Log levels

| Level | Value |
|---|---:|
| `NOTSET` | 0 |
| `DEBUG` | 10 |
| `PERFORM` | 15 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `SEVERE` | 40 |
| `FATAL` | 50 |
| `STATUS` | 60 |

`STATUS` is reserved for structured payload messages when running under `ngen`.

## Standard logging

```c
#include "ewts/logger.h"
#include "ewts/module_constants.h"

int Initialize(void)
{
    EwtsInit(EWTS_ID_CFE, true);

    EwtsLogModule(EWTS_ID_CFE, INFO, "Initializing CFE");

    return 0;
}
```

The compatibility `Log(...)` API remains available, but new or updated code should
prefer the explicit per-module APIs so messages are attributed to the correct
EWTS ID.

## Payload logging

C modules can write structured STATUS payloads with `PAYLOAD_STATUS(...)`:

```c
PAYLOAD_STATUS(
    EWTS_ID_CFE,
    "INITIALIZING",
    0.1,
    "In bmi_cfe::Initialize()",
    "CFE");
```

Arguments:

| Argument | Meaning |
|---|---|
| `ewts_id` | EWTS ID used in the payload log prefix |
| `status` | Payload status value, such as `INITIALIZING` or `IN_PROGRESS` |
| `prog` | Progress value, usually `0.0` through `1.0` |
| `msg` | Human-readable payload message |
| `modnm` | Module/component name written into the JSON payload |

Payload logging is active only when `ngen` is active and the `ewts_ngen_payload_status`
bridge symbol is available. Outside that environment, the C runtime simply does
not emit payload records.

## Environment configuration

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | Enables `ngen` integration when set |
| `EWTS_ENABLED` | Enables or disables logging |
| `EWTS_LOG_LEVEL` | Default log level; INFO if undefined |
| `EWTS_RANK` | MPI rank exported by `ngen` for runtime libraries |
| `<MODULE>_LOGLEVEL` | Per-module log level override |
| `EWTS_LOG_DIR` | Standalone log directory |

## Standalone behavior

Outside `ngen`, the C runtime writes to `EWTS_LOG_DIR` when that environment
variable is set. If `EWTS_LOG_DIR` is not set, standard log messages are written
to stdout.

Standalone file names use:

```text
<EWTS_ID>_<timestamp>.log
```

Payload logs are an `ngen` integration feature and are not written by the C
runtime in standalone mode.

## CMake

```cmake
find_package(ewts CONFIG REQUIRED)

target_link_libraries(<target> PRIVATE ewts::ewts_c)

target_link_libraries(<target> PRIVATE ewts::ewts_ngen_bridge)
target_compile_definitions(<target> PRIVATE EWTS_HAVE_NGEN_BRIDGE)

set_target_properties(<target> PROPERTIES
    C_STANDARD 99
    C_STANDARD_REQUIRED ON)
```

## Related documentation

- `integrations/ngen/README.md`
