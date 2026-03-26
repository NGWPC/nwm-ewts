# EWTS C Runtime

This directory contains the developer-facing documentation for the EWTS C
runtime library.

The C runtime library provides a lightweight logging API for C-based hydrologic modules
running either within `ngen` or as standalone applications.

## Directory role

The implementation in `runtime/c/` provides:

- the C logging API and macros
- generated C module keys and module constants
- standalone runtime logging support
- forwarding into the `ngen` bridge when that environment is active

Installed headers are typically exposed under `include/ewts/`.

## Design goals

The C runtime library is designed to preserve:

- module-scoped logger identity
- consistency with the other EWTS language-specific Runtime Libraries
- safe behavior in MPI environments
- low-friction use from existing C modules

## Typical usage

```c
#include "ewts/module_constants.h"
#define EWTS_ID EWTS_ID_CFE
#include "ewts/logger.h"

int Initialize(void)
{
    EwtsInit(EWTS_ID, true);
    LOG(INFO, "Initializing CFE");
    return 0;
}
```

The `EWTS_ID` macro binds convenience macros such as `LOG(...)` to a specific
module identity.

## Initialization under `ngen`

When a C module runs under `ngen`, initialize the module logger before the first
log message. The best location is typically the BMI `Initialize` entry point.

This ensures that:

- the correct module ID is bound before logging starts
- `<MODULE>_LOGLEVEL` overrides are applied correctly
- the first log lines are attributed to the intended module
- runtime messages route correctly when the bridge is active

If a module logs before initialization, messages may be attributed to the
fallback logger rather than the intended module-specific logger.

## Log levels

The C runtime uses the same canonical EWTS levels as the rest of the framework:

| Level | Value |
|---|---:|
| `NOTSET` | 0 |
| `DEBUG` | 10 |
| `PERFORM` | 15 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `SEVERE` | 40 |
| `FATAL` | 50 |

## Environment configuration

The C runtime participates in the same environment-driven configuration model as
other Runtime Libraries:

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | `ngen` results directory |
| `EWTS_ENABLED` | Enables or disables logging |
| `EWTS_LOG_LEVEL` | Default log level (INFO if undefined) |
| `<MODULE>_LOGLEVEL` | Per-module override |
| `EWTS_LOG_DIR` | Standalone log directory |

## MPI behavior

EWTS writes one log file per MPI rank. It does not merge all ranks into a single
shared file.

Examples under `ngen` include:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
```

This prevents file I/O collisions across ranks.

In split-by-module mode, the file stem changes but the per-rank rule remains.


## Module CMakeList Update

```
# --- EWTS (installed from nwm-ewts) ---
find_package(ewts CONFIG REQUIRED)

# Always use EWTS runtime logger for C
target_link_libraries(<cmake lib name> PRIVATE ewts::ewts_c)

# Built with ngen bridge
target_link_libraries(<cmake lib name> PRIVATE ewts::ewts_ngen_bridge)
target_compile_definitions(<cmake lib name> PRIVATE EWTS_HAVE_NGEN_BRIDGE)

# Code requires minimum of C99 standard to compile
set_target_properties(<cmake lib name> PROPERTIES C_STANDARD 99 C_STANDARD_REQUIRED ON)
```

## Standalone Mode

Outside the ngen results environment, standalone logging uses the following
directory priority:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`

## Related documentation

- user-facing overview: `docs/runtimes/c.md`
- framework-level configuration: `docs/architecture/configuration.md`
- `ngen` integration details: `integrations/ngen/README.md`
