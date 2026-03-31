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
| `NGEN_RESULTS_DIR` | `ngen` results directory |
| `EWTS_ENABLED` | Enables or disables logging |
| `EWTS_LOG_LEVEL` | Default log level (INFO if undefined) |
| `EWTS_RANK` | MPI rank (set by ngen) for submodules to read; if unset, assumes non-MPI |
| `<MODULE>_LOGLEVEL` | Per-module override |
| `EWTS_LOG_DIR` | Standalone log directory |

---

## MPI Behavior

When running under MPI, each rank writes to a separate file, for example:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
```

This prevents file I/O collisions across ranks.


In split-by-module mode, the file stem changes but the per-rank rule remains.

---

## Module CMakeList Update
```
# --- EWTS (installed from nwm-ewts) ---
find_package(ewts CONFIG REQUIRED)

# Always use EWTS runtime logger for Fortran
target_link_libraries(<cmake lib name> PRIVATE ewts::ewts_fortran)

# Built with ngen bridge
target_link_libraries(<cmake lib name> PRIVATE ewts::ewts_ngen_bridge)
target_compile_definitions(<cmake lib name> PRIVATE EWTS_HAVE_NGEN_BRIDGE)
```

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

---

# Backward Compatibility with Existing Modules

Many existing Fortran modules use legacy log level constants such as:

- `LOG_LEVEL_DEBUG`
- `LOG_LEVEL_INFO`
- `LOG_LEVEL_WARNING`
- `LOG_LEVEL_ERROR`
- `LOG_LEVEL_FATAL`

To avoid modifying large amounts of existing code, modules can define lightweight wrappers or aliases that map legacy names to EWTS levels.

---

## Recommended Mapping

Modules should map their legacy constants to EWTS equivalents:

```fortran
integer, parameter :: LOG_LEVEL_DEBUG   = EWTS_DEBUG
integer, parameter :: LOG_LEVEL_INFO    = EWTS_INFO
integer, parameter :: LOG_LEVEL_WARNING = EWTS_WARNING
integer, parameter :: LOG_LEVEL_ERROR   = EWTS_SEVERE
integer, parameter :: LOG_LEVEL_FATAL   = EWTS_FATAL
```

Optional (if used):

```fortran
integer, parameter :: LOG_LEVEL_PERFORM = EWTS_PERFORM
```

---

## Rationale

This approach:

- Preserves existing module code without widespread edits
- Maintains a **single source of truth** for log levels (EWTS runtime)
- Ensures consistent behavior across:
  - Fortran
  - C / C++
  - Python
- Allows gradual migration to native EWTS constants if desired

---

## Usage Guidance

- New code should prefer `EWTS_*` constants directly
- Existing code may continue using `LOG_LEVEL_*` via mappings
- Avoid redefining numeric values independently in modules

---

## Summary

| Legacy Name        | EWTS Equivalent |
|-------------------|-----------------|
| LOG_LEVEL_DEBUG   | EWTS_DEBUG      |
| LOG_LEVEL_INFO    | EWTS_INFO       |
| LOG_LEVEL_WARNING | EWTS_WARNING    |
| LOG_LEVEL_ERROR   | EWTS_SEVERE     |
| LOG_LEVEL_FATAL   | EWTS_FATAL      |

---

## Notes

- `EWTS_SEVERE` is equivalent to traditional `ERROR`
- `EWTS_PERFORM` is an optional intermediate level for performance logging
- All numeric values align with EWTS cross-language standards

## Documentation

For a user-focused overview and integration guidance, see:

- MkDocs: `docs/runtimes/fortran.md`
