# Configuration

EWTS is configured through environment variables and, when running under
`ngen`, through `ngen_logging.json`.

## Environment variables

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | `ngen` results directory and home of `ngen_logging.json` |
| `EWTS_ENABLED` | Enables or disables logging |
| `EWTS_LOG_LEVEL` | Default log level (INFO if undefined) |
| `EWTS_RANK` | MPI rank (set by ngen) for submodules to read; if unset, assumes non-MPI |
| `<MODULE>_LOGLEVEL` | Per-module log-level override |
| `EWTS_LOG_DIR` | Standalone output directory |

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

### Under `ngen`

Logs are written in either logs, the Run subdirectory or the worker:

```text
<NGEN_RESULTS_DIR>/logs/
<NGEN_RESULTS_DIR>/Calibration_Run
<NGEN_RESULTS_DIR>/Validation_Run
<NGEN_RESULTS_DIR>/Validation_Run/ngen_<worker name>_worker
<NGEN_RESULTS_DIR>/Forecast_Run
<NGEN_RESULTS_DIR>/Forecast_Run/Verification_Run/Verification_<job ID>
```

### Components that support `ngen`
Components support the preparation of the data required for an ngen run. 
They operate in standalone mode within EWTS and store their logs in the 
directories listed above. These components include the Model Setup 
Workflow Manager, Calibration Manager, and Forecast Manager.

### Outside `ngen`

For ngen submodlues and components that run standalone, the code checks the
`NGEN_RESULTS_DIR` enrironment variable. If it is not set, EWTS falls back
to standalone directory selection using `EWTS_LOG_DIR`, `$HOME/run_logs`, 
and `./run_logs`.
