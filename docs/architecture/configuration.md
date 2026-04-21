# Configuration

EWTS is configured through environment variables and, when running under
`ngen`, through `ngen_logging.json`.

## Environment variables

### Set by Calling Workflow or CLI (before running `ngen`)

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | Directory for `ngen` output results. |
| Optional:| |
| `NGEN_LOG_FILE_PREFIX` | Prefix applied to ngen-generated log filenames when defined. |
| `EWTS_ENABLED` | Enables or disables logging (defaults to enabled if undefined). Used in standalone mode or when no `ngen` logging configuration is provided. |
| `EWTS_LOG_DIR` | Standalone log directory (used when `NGEN_RESULTS_DIR` is not defined). |
| `EWTS_LOG_LEVEL` | Default log level (INFO if undefined). |
| `<MODULE>_LOGLEVEL` | Per-module log level override (e.g., `TROUTE_LOGLEVEL`). Environment values are used by default, but `ngen` logging configuration takes precedence when present. |

---

### Set by `ngen` (runtime environment)

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enables or disables logging based on the `ngen` logging configuration. **Takes precedence over the environment variable when present.** Defaults to enabled. |
| `EWTS_RANK` | MPI rank assigned by `ngen`; used to separate log output per process. If unset, assumes non-MPI execution. |
| `<MODULE>_LOGLEVEL` | Per-module log level override (e.g., `TROUTE_LOGLEVEL`) |

## `ngen_logging.json`

When `NGEN_RESULTS_DIR` is set, EWTS reads configuration from:

```text
<NGEN_RESULTS_DIR>/ngen_logging.json
```

Typical fields include:

- `logging_enabled`
- `split_logs_by_module`
- `modules`, which maps stable module keys to effective log levels

Example:

```json
{
  "logging_enabled": true,
  "split_logs_by_module": true,
  "modules": {
    "ngen": "info",
    "cfe-s": 20,
    "noah-owp-modular": "DEBUG",
    "smp": "warning"
  }
}
```

## Output location behavior

EWTS resolves the log directory in the following order:

1. `NGEN_RESULTS_DIR`, if defined (only used when running under `ngen`)
2. `EWTS_LOG_DIR`, if defined
3. `$HOME/run_logs`, if $HOME defined
4. `./run_logs` (default fallback)

If the log directory cannot be created, logs are written to stdout

### Under `ngen`

Logs are written in either the `logs`, the `<run_type>_Run` subdirectory, or the worker:

```text
<NGEN_RESULTS_DIR>/logs/
<NGEN_RESULTS_DIR>/Calibration_Run
<NGEN_RESULTS_DIR>/Validation_Run
<NGEN_RESULTS_DIR>/Validation_Run/ngen_<worker name>_worker
<NGEN_RESULTS_DIR>/Forecast_Run
<NGEN_RESULTS_DIR>/Forecast_Run/Verification_Run/Verification_<job ID>
```

If the environment variable `NGEN_LOG_FILE_PREFIX` is defined, its value is
prepended to ngen-generated log filenames.

### Standalone Modules

Submodules running in standalone mode use the same log directory resolution
order shown above.

### Components
Components operate in standalone mode within the EWTS framework and may explicitly
specify the log directory during setup.

If a log directory is not specified, the same resolution order above is used.

Components typically write logs to directories consistent with those used under
`ngen` (e.g., `Calibration_Run`, `Validation_Run`, etc.).

Currently supported components include:

- Model Setup Workflow Manager
- Calibration Manager
- Forecast Manager
