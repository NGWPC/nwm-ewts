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

## Terminology: Integrations vs Runtime Libraries

EWTS separates its functionality into two distinct layers to support both 
modules and the systems that run or prepare them.

### Runtime Libraries

**Runtime Libraries** are language-specific libraries used directly by module
implementations. As development continues, these libraries are intended for
broader reuse across workflow components to minimize duplication and ensure
consistent behavior. Initial development has focused on hydrologic modules
used by ngen.

These are the components that:

- are linked or imported into module code (Fortran, C, C++, Python)
- provide logging APIs such as `write_log(...)`
- manage module identity and log levels
- operate in both standalone and integrated environments

Examples:

- Fortran modules using `use logger`
- C/C++ code calling EWTS logging APIs
- Python packages importing EWTS logging utilities

---

### Integrations

**Integrations** provide the bridge between EWTS and higher-level systems that
run, coordinate, or prepare module executions.

These components:

- connect EWTS logging to a system’s execution module
- route log messages into system-specific outputs
- configure behavior based on the runtime environment
- coordinate logging across multiple modules and MPI ranks (when applicable)
- ensure consistent logging across the entire workflow

Examples include:

- Integration with **ngen** for executing hydrologic modules
- Future integration of workflow components such as:
    - Model Setup Workflow Manager
    - Calibration Manager
    - Evaluation Manager

These workflow systems prepare inputs, manage runs, or analyze results
without being part of ngen itself, but still use EWTS to ensure consistent
logging behavior.

---

### Why This Separation Exists

This separation allows EWTS to:

- support multiple programming languages consistently
- run both **inside ngen** and **standalone**
- support end-to-end workflows beyond just module execution
- avoid coupling module code to any specific framework
- provide a single, consistent logging interface across all components

---

### Summary

| Layer | Used By | Purpose |
|------|--------|--------|
| Runtime Libraries | modules | Provide logging APIs and behavior |
| Integrations | Systems and workflow components | Connect EWTS to execution and workflow environments |


## Documentation map

### Getting started

- [Installation](installation.md)
- [Contributing](contributing.md)

### Architecture

- [Logging module](architecture/logging-model.md)
- [Configuration](architecture/configuration.md)
- [Generated constants](architecture/generated-constants.md)

### Integrations

- [ngen integration](integrations/ngen.md)

### Libraries and Package

- [C library](runtimes/c.md)
- [C++ library](runtimes/cpp.md)
- [Fortran library](runtimes/fortran.md)
- [Python package](runtimes/python.md)

### Tools

- [Language constants generator](tools/generate-language-constants.md)
