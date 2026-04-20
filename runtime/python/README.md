# EWTS Python Runtime

This directory contains the developer-facing documentation for the EWTS Python
runtime.

The Python runtime provides the Python package implementation of EWTS while
matching the same general logging model used by the native language-specific Runtime Libraries.

## Package layout

The Python package lives under:

```text
runtime/python/ewts
```

The importable source code is located in:

```text
runtime/python/ewts/src/ewts
```

and is imported as:

```python
import ewts
```

## Installation for development

Editable install:

```bash
pip install -e runtime/python/ewts
```

Build a distribution manually:

```bash
python -m build runtime/python/ewts
```

Install a built wheel:

```bash
pip install runtime/python/ewts/dist/ewts-<version>-py3-none-any.whl
```

## Using EWTS from another Python repository

A different Python repository does not automatically gain access to EWTS just
because the top-level repository was built or installed elsewhere. The consuming
Python environment still needs to install the EWTS wheel or package.

Typical example:

```bash
cd /path/to/other-repo
python -m venv .venv
source .venv/bin/activate
pip install "ewts @ git+https://github.com/NGWPC/nwm-ewts.git@development#subdirectory=runtime/python/ewts"
pip install -e .
```
Within Dockerfile
```bash
ARG GH_ORG=NGWPC
ARG EWTS_REF=development
RUN --mount=type=cache,target=/root/.cache/pip,id=pip-cache \
    echo "EWTS cache bust: ${EWTS_CACHE_BUST}" && \
    set -eux && \
    ewts_dir="$(mktemp -d)" && \
    git clone "https://github.com/${GH_ORG}/nwm-ewts.git" "${ewts_dir}" && \
    cd "${ewts_dir}" && \
    git checkout "${EWTS_REF}" && \
    pip install "${ewts_dir}/runtime/python/ewts" && \
    rm -rf "${ewts_dir}"
```

After that, the consuming repository can simply:

```python
import ewts
```

# EWTS Python Runtime

## Lazy binding model

The Python runtime uses lazy binding so a module can declare a logger at import
time without fully initializing the runtime too early.

### ngen module

```python
import ewts

LOG = ewts.get_logger(ewts.FORCING_ID)
```

`get_logger()` returns a proxy logger. Before any logging calls are made, it must be bound. This is typically done at the start of BMI initialization:

```python
LOG.bind()
LOG.info("Initializing BMI forcing")
```

### Standalone component
Standalone components do not require lazy binding because they are not executed
within the `ngen` embedded Python interpreter. In these cases, setting `bind_now=True` 
will return a fully initialized (bound) logger instead of a proxy.

```python
ewts.logger.setup_logger(
        ewts.CAL_MGR_ID,
        level=log_level,
        log_dir=resolved_log_dir,
        log_file_name=resolved_log_file_name,
        running_in_ngen=False,
        enabled=enabled_override,
        bind_now=True,
    )
```

## Why Lazy Binding Exists

The EWTS Python runtime uses a **lazy binding model** due to how `ngen` executes Python.

`ngen` is a C++ application that embeds a Python interpreter and **imports Python modules before they are actually executed**. This creates two key problems:

### 1. Premature Initialization

If logging were initialized at import time:
- Loggers would be created before runtime configuration is complete
- Environment variables (log level, paths, MPI rank) may not yet be available
- Incorrect log destinations or levels could be used

### 2. Embedded Python Environment Variables

In embedded Python, environment variables set from C/C++ (like `ngen`) are not always visible via `os.environ`.

To solve this, EWTS uses:

- **Lazy binding** → delay logger creation until explicitly requested
- **getenv_any()** → fallback to `libc getenv()` when Python cannot see env vars

### Result

- Modules can safely declare loggers at import time
- Logging is only initialized when the runtime is ready
- Environment variables from `ngen` are correctly honored

### Key Takeaways

- Lazy binding avoids incorrect initialization during import
- Required for embedded Python in `ngen`
- Ensures correct environment configuration
- `getenv_any()` guarantees env visibility from C++ runtime

## Runtime relationship to `ngen`

When `ngen` integration is active, the Python runtime forwards messages through
the same broader EWTS model used by the native Runtime Libraries. Outside `ngen`, the
Python runtime handles standalone logging behavior directly.

## Environment Configuration

### Set by Calling Workflow or CLI (before running `ngen`)

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | Directory for `ngen` output results. |
| Optional:| |
| `EWTS_ENABLED` | Enables or disables logging. (True if undefined) Used in standalone mode or when no `ngen` logging configuration is provided. |
| `EWTS_LOG_DIR` | Standalone log directory (checked when `NGEN_RESULTS_DIR` is not defined) |
| `EWTS_LOG_LEVEL` | Default log level (INFO if undefined) |
| `<MODULE>_LOGLEVEL` | Per-module log level override (e.g., `TROUTE_LOGLEVEL`). Environment values are used by default, but `ngen` logging configuration takes precedence when present. |

---

### Set by `ngen` (runtime environment)

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enables or disables logging based on the `ngen` logging configuration. **Takes precedence over the environment variable when present.** Defaults to enabled. |
| `EWTS_RANK` | MPI rank assigned by `ngen`; used to separate log output per process. If unset, assumes non-MPI execution. |
| `<MODULE>_LOGLEVEL` | Per-module log level override (e.g., `TROUTE_LOGLEVEL`) |

EWTS resolves the log directory in the following order:
1. `NGEN_RESULTS_DIR`, if defined (when running under `ngen`)
2. `EWTS_LOG_DIR`, if defined
3. `$HOME/run_logs`, if $HOME defined
4. `./run_logs` (default fallback)

If the log directory cannot be created, logs are written to stdout

# Logging API

## setup_logger(...)

Configures logging for a specific EWTS ID.

```python
def setup_logger(
    module_key_or_ewts_id: str,
    *,
    level: str | int | None = None,
    log_dir: str | Path | None = None,
    log_file_name: str | None = None,
    running_in_ngen: bool | None = None,
    enabled: bool | None = None,
    bind_now: bool = False,
) -> BoundEwtsLoggerProxy | EwtsLogger
```

### Required
- `module_key_or_ewts_id: str`

### Optional (with defaults)
- `level: str | int | None = None`  
  → Uses environment/default config if not provided

- `log_dir: str | Path | None = None`  
  → Uses `EWTS_LOG_DIR` or internal default

- `log_file_name: str | None = None`  
  → Auto-generated via `make_log_path(...)`

- `running_in_ngen: bool | None = None`  
  → Determined from runtime/environment

- `enabled: bool | None = None`  
  → Uses `EWTS_ENABLED` or defaults to enabled

- `bind_now: bool = False`  
  → Returns proxy unless explicitly set True

### Behavior
- Calls `reset_logger()` first
- Applies overrides via `set_runtime_override()`
- Returns:
  - Proxy (`bind_now=False`)
  - Bound logger (`bind_now=True`)

---

## get_logger(module_key_or_ewts_id)

```python
def get_logger(module_key_or_ewts_id: str) -> BoundEwtsLoggerProxy
```

### Required
- `module_key_or_ewts_id: str`

### Optional
- None

### Returns
- `BoundEwtsLoggerProxy`

---

## bind_logger(module_key_or_ewts_id)

```python
def bind_logger(module_key_or_ewts_id: str) -> EwtsLogger
```

### Required
- `module_key_or_ewts_id: str`

### Optional
- None

### Returns
- `EwtsLogger`

---

## reset_logger(module_key_or_ewts_id)

```python
def reset_logger(module_key_or_ewts_id: str) -> None
```

### Required
- `module_key_or_ewts_id: str`

### Optional
- None

### Returns
- `None`

### Behavior

- Removes all logging handlers
- Resets Python logger state
- Clears the bound EWTS logger
- Resets initialization tracking
- Does **not** remove the logger from the cache
- Does **not** reset all loggers globally
- Only affects the specified EWTS ID

### When to use
- To change the log file name for a specific `ewts_id` logger.
- Particularly useful during a bootstrap phase, when log messages are generated
  before the final job log directory and filename are known.

---

## Valid EWTS Module Identifiers

Use the following constants when working with EWTS loggers.  
You may pass either the module id or key to `get_logger()` or `setup_logger()`.

> Internally, module keys are automatically resolved to their corresponding EWTS IDs.

| Module/Component | ID Constant | Key Constant | Value |
|------------------|-------------|-------------|-------|
| Forcing | `FORCING_ID` | `FORCING_KEY` | `"FORCING"` |
| LSTM | `LSTM_ID` | `LSTM_KEY` | `"LSTM"` |
| TopoFlow Glacier | `TOPOFLOW_GLACIER_ID` | `TOPOFLOW_GLACIER_KEY` | `"TFGLACR"` |
| T-Route | `T_ROUTE_ID` | `T_ROUTE_KEY` | `"TROUTE"` |
| Calibration Manager | `CAL_MGR_ID` | `CAL_MGR_KEY` | `"CALMGR"` |
| Evaluation Manager | `EVAL_MGR_ID` | `EVAL_MGR_KEY` | `"EVALMGR"` |
| Forecast Manager | `FCST_MGR_ID` | `FCST_MGR_KEY` | `"FCSTMGR"` |
| MSW Manager | `MSW_MGR_ID` | `MSW_MGR_KEY` | `"MSWMGR"` |

### Example

```python
import ewts

# Using ID constant
LOG = ewts.get_logger(ewts.FORCING_ID)

# Using KEY constant (automatically resolved)
LOG = ewts.get_logger(ewts.FORCING_KEY)
```

## MPI Behavior

When running under MPI, each rank writes to a separate file, for example:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
```

This prevents file I/O collisions across ranks.

In `split-by-module` mode, the file stem changes but the per-rank rule remains.

In a formulation containing t-route example:

```text
logs/ngen_mpi_process_0.log
logs/ngen_mpi_process_1.log
logs/troute_mpi_process_0.log
logs/troute_mpi_process_1.log
```

## Tests

Python tests are located under:

```text
runtime/python/ewts/tests
```

Run them with:

```bash
pip install pytest
pip install -e runtime/python/ewts
pytest runtime/python/ewts/tests
```

## Related documentation

- user-facing overview: `docs/runtimes/python.md`
- framework installation: `docs/installation.md`
- generator details: `tools/README.md`
