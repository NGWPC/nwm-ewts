# EWTS Python Runtime

The EWTS Python runtime provides the Python implementation of the NWM EWTS
(Error and Warning Trapping System) logging interface. It mirrors the
logging behavior used by the C, C++, and Fortran runtimes while fitting normal
Python package workflows.

---

# Table of Contents

- [Package Location](#package-location)
- [What Gets Installed](#what-gets-installed)
- [Installation](#installation)
- [Using EWTS From Another Python Repository](#using-ewts-from-another-python-repository)
- [Running Unit Tests](#running-unit-tests)
- [Logger Model and Lazy Binding](#logger-model-and-lazy-binding)
- [Basic Usage](#basic-usage)
- [Module IDs](#module-ids)
- [Environment Configuration](#environment-configuration)
- [Standalone vs ngen Logging](#standalone-vs-ngen-logging)
- [Notes for ngen Integrations](#notes-for-ngen-integrations)

---

# Package location

The Python package lives in:

```text
runtime/python/ewts
```

The package source code is located under:

```text
runtime/python/ewts/src/ewts
```

The published/imported package name is:

```python
import ewts
```

---

# What Gets Installed

When the repository is built and installed with CMake, the Python wheel is
built and installed as an artifact under the install prefix. For example:

```bash
cmake -S . -B cmake_build -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON -DEWTS_BUILD_SHARED=ON
cmake --build cmake_build -j
cmake --install cmake_build --prefix /tmp/ewts_install
```

This produces a wheel similar to:

```text
/tmp/ewts_install/python/dist/ewts-<version>-py3-none-any.whl
```

Important: placing the wheel under `/tmp/ewts_install` does **not** by itself
make the package importable. A Python environment must still install that wheel
with `pip`.

---

# Installation

## Editable Development Install

From the repository root:

```bash
pip install -e runtime/python/ewts
```

This installs the EWTS Python runtime in editable mode, so changes to the
source tree take effect immediately in that Python environment.

## Build a Python Distribution Manually

To build the Python package manually:

```bash
python -m build runtime/python/ewts
```

This produces:

```text
runtime/python/ewts/dist/
    ewts-<version>.whl
    ewts-<version>.tar.gz
```

## Install the Built Wheel

To install the built wheel into the active virtual environment:

```bash
pip install runtime/python/ewts/dist/ewts-<version>-py3-none-any.whl
```

Or, after a top-level CMake install:

```bash
pip install /tmp/ewts_install/python/dist/ewts-<version>-py3-none-any.whl
```

You can confirm where Python is importing the package from with:

```bash
python -c "import ewts; print(ewts.__file__)"
```

---

# Using EWTS From Another Python Repository

A different Python repository does not automatically see EWTS just because the
framework was installed to `/tmp/ewts_install`. The consuming repository must
install the EWTS wheel into its own active Python environment.

Typical example:

```bash
cd /path/to/other-repo
python -m venv .venv
source .venv/bin/activate

pip install /tmp/ewts_install/python/dist/ewts-<version>-py3-none-any.whl
pip install -e .
```

After that, the consuming repository can simply do:

```python
import ewts
```

A consuming project *can* also reference a local wheel in `pyproject.toml`,
for example:

```toml
[project]
dependencies = [
    "ewts @ file:///tmp/ewts_install/python/dist/ewts-<version>-py3-none-any.whl"
]
```

However, this is usually best reserved for local testing because it hardcodes a
machine-specific path.

---

# Running Unit Tests

Python unit tests live in:

```text
runtime/python/ewts/tests
```

Install the package and run the tests from the repository root:

```bash
pip install pytest
pip install -e runtime/python/ewts

pytest runtime/python/ewts/tests
```

Examples:

```bash
pytest -v runtime/python/ewts/tests
```

or simply:

```bash
pytest
```

---

# Logger Model and Lazy Binding

The Python EWTS logger now uses **lazy binding**.

Calling `ewts.get_logger(...)` returns a proxy object immediately, but the real
EWTS logger is **not** initialized until `bind()` is called. This allows
modules to define a logger at import time without triggering EWTS
initialization too early.

This is especially useful when the runtime environment is not fully configured
until the application entry point or BMI `Initialize()` method.

## Recommended Pattern

At module scope:

```python
import ewts
LOG = ewts.get_logger(ewts.FORCING_ID)
```

Then, before the first log message, bind it explicitly from the runtime entry
point:

```python
if hasattr(LOG, "bind"):
    LOG.bind()
```
or simply:
```python
LOG.bind()
```


After binding, use the logger normally:

```python
LOG.info("Initializing forcing downloader")
LOG.warning("Using fallback configuration")
```

## Important Rule

Do **not** log before calling `bind()`.

If a log method is called before the logger has been bound, the runtime raises
an error explaining that the EWTS logger has not yet been initialized.

This is intentional. It prevents accidental early initialization during module
import and makes runtime setup explicit.

## ⚠️ Important: Avoid Logging at Import Time

EWTS Python loggers use **lazy initialization** and must be explicitly initialized at runtime using:

```python
LOG.bind()
```

### ❌ Do NOT log at module import time

Avoid placing log statements at the top level of a module, such as:

```python
import ewts
LOG = ewts.get_logger(ewts.FORCING_ID)

LOG.debug("Initializing module")  # ❌ This runs at import time
```

In Python, module-level code executes immediately when the module is imported — *before* your application has initialized the logging system.

This can lead to:
- logging before `LOG.bind()` is called
- messages being dropped or misrouted
- unexpected initialization behavior

---

## Why This Pattern Exists

This behavior allows code such as:

```python
import ewts
LOG = ewts.get_logger(ewts.FORCING_ID)
```

without forcing EWTS to determine at import time whether it should:

- use ngen logging through the bridge, or
- fall back to standalone file logging

That decision is deferred until `LOG.bind()` is called.

---

# Basic Usage

## Preferred Usage

```python
import ewts
LOG = ewts.get_logger(ewts.FORCING_ID)
```
In the BMI Initilize or class `__init__` method:
```
LOG.bind()
```
Then within methods (not at the module level): 
```
LOG.info("Hello from EWTS")
LOG.perform("Finished a timed operation")
LOG.severe("Something failed")
```

## Standard Logging-Style Usage

The EWTS logger also supports familiar `logging.Logger`-style methods:

```python
LOG.debug("debug message")
LOG.info("info message")
LOG.warning("warning message")
LOG.error("maps to SEVERE")
LOG.critical("maps to FATAL")
```

The Python `PERFORM` level is also registered and maps to the EWTS perform
level:

```python
LOG.perform("perform message")
```
---

# Module IDs

The EWTS Python runtime provides predefined **module identifier** constants for
common NGWPC components. These are generated from the shared module registry and
exported from the package.

The generated definitions live in:

```text
runtime/python/ewts/src/ewts/modules.py
```

These constants should be used when obtaining a logger so that log messages use
canonical EWTS identifiers shared across languages.

Examples include:

```python
ewts.FORCING_ID
ewts.LSTM_ID
ewts.T_ROUTE_ID
ewts.TOPOFLOW_GLACIER_ID
```

Example:

```python
import ewts
LOG = ewts.get_logger(ewts.FORCING_ID)
```

Using the predefined IDs ensures:

- consistent module identification across languages
- correct module-specific log-level lookup through `<MODULE>_LOGLEVEL`
- compatibility with ngen bridge logging
- alignment with the shared generated module registry

Developers may define custom identifiers if necessary, but using the generated
constants from `modules.py` is strongly recommended.

---

# Environment Configuration

The Python runtime uses the same environment variables as the other EWTS
runtimes.

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enable or disable EWTS logging |
| `EWTS_LOG_DIR` | Directory used for standalone file logging |
| `EWTS_LOG_LEVEL` | Default global log level |
| `<MODULE>_LOGLEVEL` | Module-specific log level override |
| `NGEN_RESULTS_DIR` | ngen results/logging directory |
| `EWTS_NGEN_BRIDGE_LIB` | Optional explicit path to the ngen bridge shared library |
| `EWTS_DEBUG` | Enables bridge load diagnostics printed to stdout |

In ngen mode, the Python runtime attempts to load the EWTS ngen bridge shared
library and route messages through ngen logging.

If ngen logging is not active or the bridge cannot be loaded, the Python runtime
falls back to standalone file logging.

---

# Standalone vs ngen Logging

## ngen Mode

When ngen logging is active, the Python runtime sends messages through the EWTS
ngen bridge shared library.

## Standalone Mode

When not running under ngen, the Python runtime writes to a standalone log file
using the same EWTS-style formatted prefixes as the other runtimes.

The standalone log file path is created automatically by the runtime.

---

# Notes for ngen Integrations

When running inside ngen, initialize the module logger before the first log
message. In practice, this is typically done from the module runtime entry point
or BMI `Initialize()` implementation.

Recommended pattern:

```python
import ewts

LOG = ewts.get_logger(ewts.FORCING_ID)

class SomeModel:
    def Initialize(self, *args, **kwargs):
        if hasattr(LOG, "bind"):
            LOG.bind()
        LOG.info("Initialize called")
```

This keeps the existing module-level `LOG = ewts.get_logger(...)` pattern while
ensuring initialization happens at the correct time.
