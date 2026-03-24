# EWTS ngen Integration

This directory contains the developer-facing documentation for the EWTS `ngen`
integration layer.

The integration provides the bridge that allows EWTS language-specific Runtime Libraries in C,
C++, Fortran, and Python to route messages through a shared `ngen`-aware logger.

## Directory role

The `integrations/ngen/` code is responsible for:

- detecting whether `ngen` integration is active
- loading configuration from `ngen_logging.json`
- determining effective module log levels
- exporting environment settings needed by downstream Runtime Libraries
- selecting output files under `NGEN_RESULTS_DIR/logs/`
- preserving per-rank separation in MPI runs

## Initialization behavior

The integration logger uses lazy initialization.

On the first logging call, it performs work such as:

1. checking for `NGEN_RESULTS_DIR`
2. locating and reading `ngen_logging.json`
3. resolving effective log levels
4. determining the MPI rank when MPI is initialized
5. opening the appropriate output file or files

This avoids requiring an explicit logger initialization call from `ngen`.

## File layout modes

EWTS supports two file layout modes under `ngen`.

### Unified mode

All log messages for a rank are written to one file:

```text
logs/ngen_rank_0.log
```

### Split-by-module mode

When enabled, each rank writes separate files by module:

```text
logs/cfe_rank_0.log
logs/noahowp_rank_0.log
logs/smp_rank_0.log
```

Enable split mode with:

```json
{
  "split_logs_by_module": true
}
```

## Runtime behavior summary

When `NGEN_RESULTS_DIR` is set, the integration layer becomes the owner of
logging policy. Runtime libraries still create and forward messages, but final
formatting, location, and file naming are controlled here.

If `NGEN_RESULTS_DIR` is not set, Runtime Libraries fall back to standalone logging
behavior.

## Build

Configure EWTS with `ngen` support enabled:

```bash
cmake -B cmake_buld -S . -DEWTS_WITH_NGEN=ON
cmake --build cmake_buld -j
```

## Related documentation

- user-facing overview: `docs/integrations/ngen.md`
- framework configuration: `docs/architecture/configuration.md`
- top-level repository context: `README.md`
