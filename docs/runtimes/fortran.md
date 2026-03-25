# Fortran Runtime Library

The EWTS Fortran runtime library provides logging support for Fortran-based hydrologic
models running either within `ngen` or as standalone applications.

## Typical use

A Fortran module initializes its module logger and writes messages through the
EWTS runtime:

```fortran
use logger
use ewts_module_constants

call logger_init_module(EWTS_ID_NOAH_OWP_MODULAR)
call write_log("Initializing NOAHOWP BMI", EWTS_INFO)
```

## Legacy wrapper compatibility

Many existing Fortran modules use wrapper modules such as `noahowp_log_module`
so large call sites do not need to change all at once.

A wrapper can preserve legacy names such as `LOG_LEVEL_INFO` while mapping them
to canonical EWTS values such as `EWTS_INFO`.

## When running under `ngen`

Initialize the module logger before the first log message, ideally in the BMI
`Initialize` routine. This ensures that the correct module identity and
per-module configuration are applied from the start of execution.

## Developer reference

For implementation details, initialization guidance, and backward-compatibility
patterns, see:

- `runtime/fortran/README.md`
