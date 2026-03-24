# Python Runtime

The EWTS Python runtime provides the Python package implementation of EWTS.

## Package location

The package source lives under:

```text
runtime/python/ewts/src/ewts
```

and is imported as:

```python
import ewts
```

## Typical use

```python
import ewts

LOG = ewts.get_logger(ewts.FORCING_ID)
LOG.bind()
LOG.info("Initializing forcing workflow")
```

## Runtime behavior

The Python runtime mirrors the same general EWTS behavior used by the native
language-specific Runtime Libraries, including canonical log levels and support for `ngen` integration when
that environment is active.

## Developer reference

For packaging details, lazy binding, testing, and integration notes, see:

- `runtime/python/README.md`
