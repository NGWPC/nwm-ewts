# Error and Warning Trapping System (EWTS)

The EWTS is a multi-language logging framework for hydrologic modules that run
within `ngen` or as standalone applications. It provides consistent log levels,
module identities, and environment-driven configuration across C, C++, Fortran,
and Python.

## What EWTS provides

- consistent log formatting across supported language-specific Runtime Libraries
- stable module identifiers generated from a shared registry
- centralized logging behavior when running under `ngen`
- standalone runtime logging outside the `ngen` environment
- per-rank log files for MPI execution
- unified or split-by-module log output under `ngen`

## Choose the right documentation

This documentation site is user-facing. It focuses on behavior, configuration,
and runtime usage.

For implementation details and repository-local development guidance, use the
`README.md` files located in the corresponding runtime, integration, or tooling
subdirectory.

## Documentation map

### Getting started

- [Installation](installation.md)
- [Contributing](contributing.md)

### Architecture

- [Logging model](architecture/logging-model.md)
- [Configuration](architecture/configuration.md)
- [Generated constants](architecture/generated-constants.md)

### Integrations

- [ngen integration](integrations/ngen.md)

### Runtime Libraries

- [C runtime library](runtimes/c.md)
- [C++ runtime library](runtimes/cpp.md)
- [Fortran runtime library](runtimes/fortran.md)
- [Python runtime package](runtimes/python.md)

### Tools

- [Language constants generator](tools/generate-language-constants.md)
