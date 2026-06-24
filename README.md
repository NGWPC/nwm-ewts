# EWTS

## Error Warning and Trapping System

EWTS is a cross-language logging and status reporting framework used by
hydrologic and environmental modeling applications and components that
support running them. EWTS provides consistent log levels, module
identity handling, environment-driven configuration, and a common
logging API for Python, C, C++, and Fortran components while allowing
each language to retain idiomatic interfaces.

EWTS supports standalone applications as well as integration with ngen,
providing MPI-aware logging, configurable log levels, and structured
status payload messages.

## Table of Contents

-   [Features](#features)
-   [Log Levels](#log-levels)
-   [Runtime Libraries](#runtime-libraries)
-   [STATUS Payload Logging](#status-payload-logging)
-   [ngen Integration](#ngen-integration)
-   [Building ngen with EWTS](#building-ngen-with-ewts)
    -   [USE_EWTS=ON](#use_ewtson)
    -   [USE_EWTS=OFF](#use_ewtsoff)
    -   [Compile-Time Control](#compile-time-control)
    -   [Python Components](#python-components)
-   [Payload Log Files](#payload-log-files)
-   [Documentation](#documentation)
-   [Python](#python)
-   [C and C++](#c-and-c)
-   [Fortran](#fortran)

------------------------------------------------------------------------

------------------------------------------------------------------------

## Features

-   C, C++, and Fortran runtime libraries
-   Python pacakge
-   Common log levels across all languages
-   Configurable module log levels
-   MPI-aware logging
-   Unified or split log files
-   ngen integration
-   Structured STATUS payload messages
-   Dedicated payload log files
-   Environment-based configuration
-   External workflow and monitoring support

------------------------------------------------------------------------

## Log Levels

  Level     Description
  --------- ------------------------------------
  DEBUG     Detailed diagnostic information
  PERFORM   Performance and timing information
  INFO      General informational messages
  WARNING   Recoverable problems
  SEVERE    Serious errors
  FATAL     Unrecoverable errors
  STATUS    Structured payload messages

------------------------------------------------------------------------

## Runtime Libraries

EWTS provides runtime libraries for:

-   Python
-   C
-   C++
-   Fortran
-   ngen integration

Each runtime provides a native language API while preserving common log
levels and behavior.

------------------------------------------------------------------------

## STATUS Payload Logging

The STATUS log level provides structured status and progress
information.

Typical uses include:

-   Model initialization
-   Workflow progress reporting
-   Calibration status
-   External monitoring applications
-   Real-time dashboards
-   Machine-readable status updates

Example payload:

``` text
<MSG_DATA>
{
    "status": "INITIALIZING",
    "prog": 0.1,
    "msg": "Initializing UEB",
    "modnm": "ueb_bmi"
}
</MSG_DATA>
```

When running under ngen, payload messages are written to a dedicated
payload log file.

Example:

``` text
2026-06-23T23:42:36.210Z UEB_BMI STATUS <MSG_DATA>{"status":"INITIALIZING","prog":0.1,"msg":"Initializing UEB","modnm":"ueb_bmi"}</MSG_DATA>
```

Payload records are intended primarily for machine consumption but may
also be viewed directly.

------------------------------------------------------------------------

## ngen Integration

The ngen integration provides:

-   MPI rank detection
-   Unified log files
-   Split module log files
-   Per-module log levels
-   Environment configuration
-   STATUS payload logging
-   Dedicated payload logs

All C, C++, Fortran, and Python modules may log through a common ngen
logger while preserving the originating EWTS identifier.

------------------------------------------------------------------------

## Payload Log Files

Payload logs are created only when the first STATUS payload is received.

Typical file names:

``` text
ngen_payload_mpi_process_0.log
ngen_payload_mpi_process_1.log
```

Payload logs are written per MPI rank and are never split by module.

------------------------------------------------------------------------

## Documentation

Additional documentation is available in the runtime-specific READMEs.

``` text
runtime/python/ewts/README.md
runtime/c/README.md
runtime/cpp/README.md
runtime/fortran/README.md
integrations/ngen/README.md
```

------------------------------------------------------------------------

## Python

Python applications use the standard EWTS logger.

``` python
LOG.info("Initializing")

LOG.status(
    '<MSG_DATA>'
    '{"status":"INITIALIZING",'
    '"prog":0.1,'
    '"msg":"Initializing model",'
    '"modnm":"python"}'
    '</MSG_DATA>'
)
```

------------------------------------------------------------------------

## C and C++

``` c
LOG(INFO, "Initializing");

PAYLOAD_STATUS(
    "INITIALIZING",
    0.1,
    "Initializing component",
    "COMP");
```

------------------------------------------------------------------------

## Fortran

``` fortran
call write_log(
    "Initializing model",
    LOG_LEVEL_INFO)

call payload_status(
    "INITIALIZING",
    0.1d0,
    "Initializing model",
    "")
```

# Building ngen with EWTS

The top-level `USE_EWTS` CMake option controls whether EWTS support is
compiled into `ngen` and its supported submodules and components.

``` text
-DUSE_EWTS=ON
```

or

``` text
-DUSE_EWTS=OFF
```

If `USE_EWTS` is not specified, it defaults to `ON`.

## USE_EWTS=ON

When `USE_EWTS=ON`:

-   EWTS libraries are linked into ngen and participating submodules.
-   Language-specific preprocessor definitions are enabled.
-   Structured STATUS payload messages are available.
-   STATUS messages are written to dedicated payload log files.
-   Module log messages are written through the EWTS framework.
-   ngen components may participate in unified MPI-aware logging.

## USE_EWTS=OFF

When `USE_EWTS=OFF`:

-   EWTS libraries are not linked.
-   EWTS-related code paths are excluded at compile time.
-   All logging falls back to standard stdout logging.
-   STATUS payload messages are not generated.
-   Payload log files are not created.

## Compile-Time Control

Each ngen component controls EWTS support through its own build
configuration.

C and C++ modules use preprocessor definitions generated by their
`CMakeLists.txt` files, for example:

``` cmake
if(USE_EWTS)
    target_compile_definitions(cfebmi PRIVATE CFE_USE_EWTS)
endif()
```

Fortran components similarly define module-specific compilation flags
such as:

``` text
NOAHOWP_USE_EWTS
SACSMA_USE_EWTS
SNOW17_USE_EWTS
```

These definitions allow EWTS-specific code to be completely excluded
from builds when EWTS support is disabled.

## Python Components

Python modules determine EWTS availability at runtime.

The EWTS Python package must be importable:

``` python
try:
    from ewts.helper import getenv_any
    from ewts.logger import configure_existing_logger
    FORCING_USE_EWTS = True
except ImportError:
    FORCING_USE_EWTS = False
```

If the package is available, the component checks the
`EWTS_USE_NGEN_BRIDGE` environment variable.

When both conditions are satisfied:

-   The existing ngen logger is adopted.
-   Log messages participate in the ngen EWTS framework.
-   STATUS payload messages may be generated.

If the package is unavailable, or if `EWTS_USE_NGEN_BRIDGE` is not
enabled, Python components automatically fall back to standard stdout
logging.

This allows the same Python component to operate both inside and outside
of ngen without requiring code changes.
