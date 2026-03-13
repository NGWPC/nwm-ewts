# EWTS C Runtime

The EWTS C runtime provides a lightweight logging API for C-based hydrologic
components running within **ngen** or as standalone applications.

It is designed to provide:

- module-scoped logging
- consistent log formatting across languages
- environment-driven configuration
- optional integration with the ngen logging bridge

The runtime is implemented under:

```text
runtime/c/
```

and installs headers under:

```text
include/ewts/
```

---

## Design Goals

The C runtime was designed with the following requirements:

- **No module ID collisions** when multiple modules run in the same process
- **Safe logging behavior in MPI environments**
- **Minimal dependencies**
- **Consistency with the C++, Fortran, and Python runtimes**

Each module logger is keyed by a unique **EWTS module ID**.

---

## Important: Initialization When Running with ngen

When EWTS is used within **ngen**, it is important to initialize the module
logger **before the first log message is written**.

The recommended place to do this is inside the module’s **BMI `Initialize`**
method.

This ensures:

- the correct **module ID** is bound to the logger
- module-specific environment configuration such as `<MODULE>_LOGLEVEL` is applied
- logging is routed correctly when the **ngen bridge** is active
- log messages are attributed to the correct module from the first line

If logging occurs **before** the module logger is initialized, messages may be
written using the default fallback logger instead of the intended module ID.

Example:

```c
#include "ewts/module_constants.h"
#define EWTS_ID EWTS_ID_CFE
#include "ewts/logger.h"

int Initialize(void)
{
    EwtsInit(EWTS_ID, true);
    LOG(INFO, "In CFE Initialize()");
    return 0;
}
```

---

## Basic Usage

Typical usage in a C module:

```c
#include "ewts/module_constants.h"
#define EWTS_ID EWTS_ID_CFE
#include "ewts/logger.h"

int main(void)
{
    EwtsInit(EWTS_ID, false);

    LOG(INFO, "In CFE Initialize()");
    LOG(DEBUG, "Debug information");

    return 0;
}
```

The `EWTS_ID` macro ensures that `Log(...)` and `LOG(...)` resolve to the
module-specific logger.

---

## Log Levels

EWTS defines common log levels shared across all runtimes:

| Level | Value |
|---|---:|
| `NOTSET` | 0 |
| `DEBUG` | 10 |
| `PERFORM` | 15 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `SEVERE` | 40 |
| `FATAL` | 50 |

Example:

```c
LOG(WARNING, "Parameter value outside expected range");
```

---

## Environment Configuration

The runtime is controlled by environment variables:

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enable or disable logging |
| `EWTS_LOG_LEVEL` | Default log level |
| `<MODULE>_LOGLEVEL` | Module-specific override |
| `EWTS_LOG_DIR` | Standalone logging directory |
| `NGEN_RESULTS_DIR` | ngen results directory |

---

## MPI Behavior

When running within MPI, each rank writes to its own file, for example:

```text
logs/ngen_rank_0.log
logs/ngen_rank_1.log
logs/ngen_rank_2.log
```

This avoids file write contention and message interleaving across ranks.

---

## Standalone Mode

If the runtime is not running inside an ngen results environment, standalone
logging uses the following directory priority:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`

---

## Integration with ngen

When the ngen bridge is linked, log messages are routed through:

```text
ewts_ngen_log
```

This allows ngen to collect and manage log output consistently across modules.

---

## Thread Safety and Runtime Model

The C runtime avoids:

- global unguarded string buffers
- unsafe concatenation
- process-global module identity

Instead, module loggers are maintained in an internal registry keyed by
**module ID**.
