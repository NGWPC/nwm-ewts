# Logging Model

EWTS supports two logging modes:

- logging routed through the `ngen` integration layer
- standalone runtime logging outside `ngen`

## `ngen`-integrated logging

When `ngen` is active, the integration layer becomes the owner of logging implementation and
policy. It is responsible for:

- reading `ngen_logging.json`
- resolving effective log levels
- formatting output consistently
- exporting module-specific configuration where needed
- writing output files under `NGEN_RESULTS_DIR/logs/`

In this mode, language-specific Runtime Libraries forward log messages through the shared bridge 
code rather than deciding their own output policy.

## Lazy initialization in the integration layer

The `ngen` logger is initialized lazily on the first logging call. That first
call performs configuration loading, rank detection, and file setup.

This avoids requiring a separate logger initialization step in `ngen` itself.

## MPI behavior

EWTS writes one file per MPI rank. It does not merge all ranks into one shared
output file.

Examples:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
```

## Unified and split-by-module layouts

Under `ngen`, EWTS supports two file layout modes.

### Unified layout

Each rank writes to one log file:

```text
logs/ngen_mpi_process_0.log
```

### Split-by-module layout

Each rank writes separate files by module:

```text
logs/cfe_mpi_process_0.log
logs/ngen_mpi_process_0.log
logs/noahowp_mpi_process_0.log
logs/smp_mpi_process_0.log
```

This keeps module output separated while preserving the one-file-per-rank rule.

## Standalone runtime logging

When a runtime is used outside `ngen`, the language-specific logger is
responsible for formatting, log-level resolution, and output selection.

Typical standalone output directory priority is:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`
