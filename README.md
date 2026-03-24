# EWTS — Error and Warning Trapping System

EWTS is a multi-language logging framework for hydrologic modules running either
within `ngen` or as standalone applications. It provides consistent log levels,
module identity handling, environment-driven configuration, and a common bridge
model across C, C++, Fortran, and Python.

Under `ngen`, EWTS routes log messages through the `ngen` integration layer so
configuration, formatting, and output location are controlled centrally. In
standalone mode, each runtime applies the same general policy while handling its
own file output.

## Repository purpose

This repository provides:

- runtime logging libraries for C, C++, Fortran, and Python
- the `ngen` integration bridge and logger implementation
- generated module constants and log-level definitions
- generator tooling that keeps constants synchronized across languages
- MkDocs content for user-facing documentation

## Logging model summary

EWTS supports two execution contexts:

1. **`ngen`-integrated logging**
   - the `ngen` integration layer owns configuration and output policy
   - logging configuration is read from `ngen_logging.json`
   - output is written beneath `NGEN_RESULTS_DIR/logs/`
   - files are generated per MPI rank
   - output can be unified or split by module

2. **Standalone runtime logging**
   - each language runtime writes its own log output
   - runtime behavior is controlled by environment variables such as
     `EWTS_ENABLED`, `EWTS_LOG_LEVEL`, and `EWTS_LOG_DIR`
   - output falls back through `EWTS_LOG_DIR`, `$HOME/run_logs`, and `./run_logs`

## Repository layout

```text
runtime/
  c/          C Runtime Library
  cpp/        C++ Runtime Library
  fortran/    Fortran Runtime Library
  python/     Python package
integrations/
  ngen/       ngen bridge and logger integration
spec/
  module_registry.yaml
  log_levels.json
tools/
  generate_language_constants.py
docs/         MkDocs source
```

## Build from the repository root

```bash
cmake -B cmake_buld -S . -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON -DEWTS_BUILD_SHARED=ON
cmake --build cmake_buld -j
```

The top-level build compiles the native language-specific Runtime Libraries and builds the Python package.

## Install

```bash
cmake --install cmake_buld --prefix /path/to/install
```

The install tree includes:

- C Runtime Library and headers
- C++ Runtime Library and headers
- Fortran Runtime Library and module files
- generated constants for supported languages
- `ngen` integration library when enabled
- CMake package configuration files
- Python wheel output from the top-level build

## Python runtime development

For direct Python development:

```bash
pip install -e runtime/python/ewts
```

To build a wheel manually:

```bash
python -m cmake_buld runtime/python/ewts
```

## Generated constants

EWTS uses specification files as the single source of truth for module metadata
and log levels:

- `spec/module_registry.yaml`
- `spec/log_levels.json`

Regenerate language-specific constants with:

```bash
python tools/generate_language_constants.py
```

Generated files should be treated as derived artifacts and should not be edited
by hand.

## Documentation split

This repository uses two documentation audiences:

- `docs/` contains **user-facing MkDocs content** intended to explain the
  framework, runtime behavior, and integration model.
- directory-local `README.md` files contain **developer-facing documentation**
  intended for contributors working in that part of the repository.

## Developer entry points

For implementation details, start with:

- `runtime/c/README.md`
- `runtime/cpp/README.md`
- `runtime/fortran/README.md`
- `runtime/python/README.md`
- `integrations/ngen/README.md`
- `tools/README.md`
