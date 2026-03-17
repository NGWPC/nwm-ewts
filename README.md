# EWTS — Environmental Workflow Traceability System

EWTS is a lightweight, multi-language logging runtime used within the NGWPC ecosystem.
It provides consistent log formatting, module identity handling, environment-based configuration,
and optional ngen bridge integration across C, C++, Fortran, and Python.

All logging is done at single point using a bridge C log method all different languages call. 
When ngen is running it handles log entry formatting and file I/O. When modules run standalone, 
the individual language loggers handle formatting and file I/O. When running in an MPI system, 
logs are written to a rank identified log file per MPI process.

This repository supports **module-scoped logging** for shared-runtime scenarios, so multiple
modules can run in the same `ngen` process without colliding on logger identity.

---

## Quick Start

Build and install EWTS from the repository root:

```bash
cmake -B build -S .
cmake --build build -j
cmake --install build --prefix /path/to/install
```

The top-level CMake build compiles the C, C++, and Fortran runtimes and also builds the
Python package automatically.

---

## Why EWTS exists

Hydrologic formulations in `ngen` execute multiple modules in sequence across many
catchments and timesteps. EWTS gives those components a common logging layer so output is:

- consistently formatted
- attributed to the correct module ID
- configurable through environment variables
- routable either to standalone log files or the ngen bridge

---

## Key features

- **Multi-language runtimes** for C, C++, Fortran, and Python
- **Per-module logger identity** for shared-process execution
- **Common log levels**: NOTSET, DEBUG, PERFORM, INFO, WARNING, SEVERE, FATAL
- **Environment-based configuration**
- **Optional ngen integration** through `ewts_ngen_log`
- **CMake library export** for C/C++/Fortran consumers
- **Python wheel built automatically by the top-level CMake build**

---

## Repository layout

```text
runtime/
  c/          C runtime
  cpp/        C++ runtime
  fortran/    Fortran runtime
  python/     Python package
integrations/
  ngen/       logger, ngen log bridge
spec/
  module_registry.yaml
  log_levels.json
tools/
  generate_language_constants.py
docs/         MkDocs source
```

---

## Build from the repository root

```bash
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON -DEWTS_BUILD_SHARED=ON
cmake --build build -j
```

This top-level build compiles the EWTS runtime libraries and builds the Python package
using the version defined in the Python runtime source.

---

## Install

```bash
cmake --install build --prefix /path/to/install
```

The install step places the following artifacts in the install tree:

- C runtime library
- C++ runtime library
- Fortran runtime modules and library
- CMake package configuration files
- generated headers and module constants
- Python wheel for the EWTS Python runtime

The Python wheel built during the CMake build is installed alongside the other runtime artifacts.

---

## Python package

The EWTS Python package is built automatically when using the top-level CMake build.

If you want to work on the Python runtime directly, you can still install it in editable mode:

```bash
pip install -e runtime/python/ewts
```

Or build distributions manually:

```bash
python -m build runtime/python/ewts
```

In most workflows, however, the Python wheel is produced automatically by the CMake build
and installed during `cmake --install`.

---


## Running Python tests

Python unit tests are located in:

```
runtime/python/ewts/tests
```

Run them from the repository root:

```bash
pip install pytest
pip install -e runtime/python/ewts
pytest
```


## Runtime configuration

EWTS is configured primarily through environment variables:

- `EWTS_ENABLED`
- `EWTS_LOG_DIR`
- `EWTS_LOG_LEVEL`
- `<MODULE>_LOGLEVEL`
- `NGEN_RESULTS_DIR` when running with the ngen bridge

---

## Language-specific usage

See the runtime READMEs for usage patterns:

- [C runtime](runtime/c/README.md)
- [C++ runtime](runtime/cpp/README.md)
- [Fortran runtime](runtime/fortran/README.md)
- [Python runtime](runtime/python/README.md)
- [ngen bridge](integrations/ngen/README.md)

---


## Language Constants Generator

EWTS uses a **code generation step** to ensure module identifiers and log levels remain consistent across all supported runtimes (C, C++, Fortran, and Python).

Rather than manually duplicating constants in each language, EWTS defines these values in specification files and generates the language bindings automatically.

The generator is located at:

```
tools/generate_language_constants.py
```

It reads the following specifications:

- `spec/module_registry.yaml` — defines module keys, EWTS module IDs, and descriptions.
- `spec/log_levels.json` — defines the canonical EWTS log levels.

These specifications act as the **single source of truth** for the logging system.

The generator produces language‑specific constants used by the runtimes:

- C runtime headers and lookup tables
- C++ constexpr constants
- Fortran parameter modules
- Python module constants

This guarantees that:

- All runtimes use identical module identifiers
- Log levels remain synchronized across languages
- Adding a new module requires updating only the registry

To regenerate the constants:

```bash
python tools/generate_language_constants.py
```

Generated files contain a header marking them as **auto-generated** and should not be edited manually.

## Documentation site

An MkDocs site is included in this repository.
After installing the docs dependencies, serve it locally with:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Build the static site with:

```bash
mkdocs build
```

A GitHub Actions workflow can be used to publish the site to GitHub Pages.

---

## Troubleshooting quick notes

- If all log lines appear as `EWTS`, your module-specific logger binding was probably not applied.
- In C and C++, define or bind `EWTS_ID` before including the logger header when you want `Log(...)`
  or `LOG(...)` to resolve to the module-specific path.
- In Fortran, use module-specific wrapper modules that call `*_module` APIs.
- If ngen bridge symbols are missing, verify the build includes the ngen integration and that the
  bridge library is linked into the consumer.

---

## License

MIT. See [LICENSE](LICENSE).
