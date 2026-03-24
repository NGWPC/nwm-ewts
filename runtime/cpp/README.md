# EWTS C++ Runtime

This directory contains the developer-facing documentation for the EWTS C++
runtime library.

The C++ runtime library provides logging support for C++-based modules and shared
runtime execution within the EWTS framework.

## Directory role

The implementation in `runtime/cpp/` provides:

- the native C++ logger implementation used outside `ngen`
- generated C++ module keys and log-level constants
- shared-runtime module identity handling
- bridging support for `ngen`-integrated execution

## Design goals

The C++ runtime is structured to preserve:

- consistent behavior with the C, Fortran, and Python language-specific Runtime Libraries
- safe module identity handling when more than one module logs in the same
  process
- environment-driven configuration
- per-rank file separation for MPI execution

## Shared-runtime behavior

The C++ runtime library is used in scenarios where multiple modules may run within the
same process. Logger identity therefore needs to be module-scoped rather than
process-global.

This is especially important under `ngen`, where more than one formulation or
module may emit log messages through the same executable.

## Log levels

The C++ runtime library uses the canonical EWTS levels:

| Level | Value |
|---|---:|
| `NOTSET` | 0 |
| `DEBUG` | 10 |
| `PERFORM` | 15 |
| `INFO` | 20 |
| `WARNING` | 30 |
| `SEVERE` | 40 |
| `FATAL` | 50 |

## Runtime relationship to `ngen`

When `ngen` integration is active, the runtime library does not own final output policy.
Instead, the integration layer controls configuration loading, output location,
and file naming while the runtime continues to attribute and forward messages.

## Environment configuration

The CPP runtime participates in the same environment-driven configuration model as
other Runtime Libraries:

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | `ngen` results directory |
| `EWTS_ENABLED` | Enables or disables logging |
| `<MODULE>_LOGLEVEL` | Per-module override |
| `EWTS_LOG_DIR` | Standalone log directory |

## MPI Behavior

When running under MPI, each rank writes to a separate file, for example:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
```

This prevents file I/O collisions across ranks.

In split-by-module mode, the file stem changes but the per-rank rule remains.

---

## Standalone Mode

Outside the ngen results environment, standalone logging uses the following
directory priority:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`

---

## Related documentation

- user-facing overview: `docs/Runtime Libraries/cpp.md`
- `ngen` implementation details: `integrations/ngen/README.md`
- generated constants workflow: `tools/README.md`
