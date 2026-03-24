# Configuration

EWTS is configured through environment variables and, when running under
`ngen`, through `ngen_logging.json`.

## Environment variables

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | `ngen` results directory and home of `ngen_logging.json` |
| `EWTS_ENABLED` | Enables or disables logging |
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

Logs are written beneath:

```text
<NGEN_RESULTS_DIR>/logs/
```

### Outside `ngen`

If `NGEN_RESULTS_DIR` is not set, EWTS falls back to standalone directory
selection using `EWTS_LOG_DIR`, `$HOME/run_logs`, and `./run_logs`.
