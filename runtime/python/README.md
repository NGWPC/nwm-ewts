
# EWTS Python Runtime

The EWTS Python runtime provides the same logging behavior as the
C, C++, and Fortran runtimes while integrating with the shared EWTS
configuration system.

The Python package lives in:

```
runtime/python/ewts
```

The source code for the package itself is located under:

```
runtime/python/ewts/src/ewts
```

---

# Installation (Editable Development)

From the repository root:

```bash
pip install -e runtime/python/ewts
```

This installs the EWTS Python runtime in editable mode so changes
to the source tree take effect immediately.

---

# Build Python Distribution

To build the Python package manually:

```bash
python -m build runtime/python/ewts
```

This produces:

```
runtime/python/ewts/dist/
    ewts-<version>.whl
    ewts-<version>.tar.gz
```

Note: when building the repository using the **top-level CMake build**,
the Python wheel is built automatically.

---

# Running Unit Tests

Python unit tests live in:

```
runtime/python/ewts/tests
```

Install the package and run the tests from the repository root:

```bash
pip install pytest
pip install -e runtime/python/ewts

pytest runtime/python/ewts/tests
```

Example:

```bash
pytest -v runtime/python/ewts/tests
```
or

```bash
pytest
```

---

# Basic Usage

```python
import ewts

LOG = ewts.get_logger(ewts.T_ROUTE_ID)

LOG("INFO", "Hello world")
```

---

# Module IDs

The EWTS Python runtime provides predefined **module identifiers**
for common NGWPC components. These are defined in:

```
runtime/python/ewts/src/ewts/modules.py
```

This file contains constants representing the canonical EWTS module IDs.
Using these constants ensures that log messages from Python components
use the same module identifiers as the C, C++, and Fortran runtimes.

Example module IDs include:

```python
ewts.LSTM_ID
ewts.T_ROUTE_ID
ewts.TOPOFLOW_GLACIER_ID
```

These constants should be used when obtaining a logger:

```python
import ewts

LOG = ewts.get_logger(ewts.T_ROUTE_ID)

LOG("INFO", "Initializing T-Route model")
```

Using the predefined module IDs ensures:

- consistent module identification across languages
- correct log-level configuration via `<MODULE>_LOGLEVEL`
- compatibility with ngen logging configuration

Developers may define custom module IDs if necessary, but using the
standard identifiers from `modules.py` is strongly recommended.

---

# Environment Configuration

The Python runtime uses the same environment variables as the other
EWTS runtimes:

| Variable | Purpose |
|--------|--------|
| `EWTS_ENABLED` | Enable or disable logging |
| `EWTS_LOG_DIR` | Standalone log directory |
| `EWTS_LOG_LEVEL` | Default log level |
| `<MODULE>_LOGLEVEL` | Module-specific log level |
| `NGEN_RESULTS_DIR` | ngen results/logging directory |

See the main project README for additional details.
