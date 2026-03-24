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
Python environment still needs to install the EWTS wheel or editable package.

Typical example:

```bash
cd /path/to/other-repo
python -m venv .venv
source .venv/bin/activate
pip install /tmp/ewts_install/python/dist/ewts-<version>-py3-none-any.whl
pip install -e .
```

After that, the consuming repository can simply:

```python
import ewts
```

## Lazy binding model

The Python runtime uses lazy binding so a module can declare a logger at import
time without fully initializing the runtime too early.

Typical pattern:

```python
import ewts

LOG = ewts.get_logger(ewts.FORCING_ID)
LOG.bind()
LOG.info("Initializing forcing workflow")
```

This is useful when the environment is not fully configured until application
startup or BMI initialization.

## Runtime relationship to `ngen`

When `ngen` integration is active, the Python runtime forwards messages through
the same broader EWTS model used by the native Runtime Libraries. Outside `ngen`, the
Python runtime handles standalone logging behavior directly.

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

- user-facing overview: `docs/Runtime Libraries/python.md`
- framework installation: `docs/installation.md`
- generator details: `tools/README.md`
