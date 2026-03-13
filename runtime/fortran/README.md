# EWTS Fortran Runtime

The EWTS Fortran runtime provides logging support for Fortran-based hydrologic
models running within **ngen** or as standalone applications.

It provides:

- consistent log formatting
- module-specific log identities
- environment-configurable logging
- compatibility with legacy Fortran code

The runtime implementation is located under:

```text
runtime/fortran/
```

---

## Important: Initialization When Running with ngen

When EWTS is used within **ngen**, it is important to initialize the module
logger **before the first log message is written**.

The recommended place to do this is inside the module’s **BMI `Initialize`**
routine.

This ensures:

- the correct **module ID** is bound to the logger
- module-specific configuration such as `<MODULE>_LOGLEVEL` is applied
- the first log lines are attributed to the intended module
- logging routes correctly when ngen integration is active

If logging occurs before initialization, messages may be associated with the
default fallback logger rather than the intended module.

Example:

```fortran
subroutine initialize()
  use logger
  use ewts_module_constants

  call logger_init_module(EWTS_ID_SMP)
  call write_log("Initializing Soil Moisture Profiles module", EWTS_INFO)
end subroutine initialize
```

For legacy wrappers, the wrapper should ensure the module-specific init occurs
before the first forwarded log call.

---

## Basic Usage

Typical usage inside a Fortran module:

```fortran
use logger
use ewts_module_constants

call logger_init_module(EWTS_ID_NOAH_OWP_MODULAR)
call write_log("Initializing NOAHOWP BMI", EWTS_INFO)
```

---

## Legacy Compatibility

Many legacy Fortran models use wrapper modules such as:

```text
noahowp_log_module
```

These wrappers forward logging calls into the EWTS runtime so older code does
not have to change its logging interface.

Example:

```fortran
use noahowp_log_module

call write_log("Starting Noah OWP model", LOG_LEVEL_INFO)
```

In this pattern, the wrapper should call the module-specific EWTS APIs under
the hood so logging remains module-safe.

---

## Log Levels

The Fortran runtime uses the same log level values as the other runtimes:

| Level | Value |
|---|---:|
| `EWTS_NOTSET` | 0 |
| `EWTS_DEBUG` | 10 |
| `EWTS_PERFORM` | 15 |
| `EWTS_INFO` | 20 |
| `EWTS_WARNING` | 30 |
| `EWTS_SEVERE` | 40 |
| `EWTS_FATAL` | 50 |

Example:

```fortran
call write_log("Some value below threshold. Using default of 1", EWTS_WARNING)
```

---

## Initialization Model

The Fortran runtime supports module-specific entry points such as:

- `logger_init_module(id)`
- `write_log_module(id, msg, lvl)`
- `get_log_level_module(id)`
- `is_logger_enabled_module(id)`

These should be preferred for true multi-module safety.

The older fallback APIs remain available, but they route through the generic
fallback logger and are less suitable for shared-runtime ngen scenarios.

---

## Environment Configuration

Logging behavior is controlled by environment variables:

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enable logging |
| `EWTS_LOG_LEVEL` | Default log level |
| `<MODULE>_LOGLEVEL` | Module override |
| `EWTS_LOG_DIR` | Standalone logging directory |
| `NGEN_RESULTS_DIR` | ngen results directory |

---

## MPI Behavior

When running under MPI, each rank writes to a separate file, for example:

```text
logs/ngen_rank_0.log
logs/ngen_rank_1.log
```

This prevents file I/O collisions across ranks.

---

## Standalone Mode

Outside the ngen results environment, standalone logging uses the following
directory priority:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`

---

## ngen Integration

When ngen integration is active, the Fortran runtime can route messages through
the EWTS → ngen bridge so log output follows the same behavior as the C, C++,
and Python runtimes.
