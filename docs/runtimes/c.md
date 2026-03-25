# C Runtime Library

The EWTS C runtime library provides logging support for C-based hydrologic
modules running either within `ngen` or as standalone applications.

## Typical use

A C module defines its EWTS module ID and uses the runtime logger API:

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

## When running under `ngen`

Initialize the module logger before the first log message, typically from the
module's BMI `Initialize` entry point. This ensures that the correct module ID
and per-module configuration are applied from the beginning of execution.

## Common log levels

| Level | Value |
|---|---:|
| `NOTSET` | 0 |
| `DEBUG` | 10 |
| `PERFORM` | 15 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `SEVERE` | 40 |
| `FATAL` | 50 |

## Developer reference

For implementation details, macros, and runtime-specific notes, see:

- `runtime/c/README.md`
