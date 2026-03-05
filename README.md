# EWTS -- Environmental Workflow Traceability System

EWTS is a lightweight, multi-language logging runtime used within the
National Water Model (NWM) ecosystem.

It provides consistent log formatting, module identity handling,
environment-based configuration, and optional NGEN integration across:

-   C
-   C++
-   Fortran
-   Python

------------------------------------------------------------------------

## Repository Structure

- runtime/c
- runtime/cpp
- runtime/fortran
- runtime/python

------------------------------------------------------------------------

## Build (C / C++ / Fortran)

cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release cmake --build build -j

### With NGEN integration enabled

cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON
cmake --build build -j

------------------------------------------------------------------------

## Install (CMake)

cmake --install build --prefix `<install_dir>`{=html}

------------------------------------------------------------------------

## Python Package

Install in editable mode (recommended for development):

pip install -e runtime/python/ewts

Build distribution artifacts:

python -m build runtime/python/ewts

------------------------------------------------------------------------

## Runtime Configuration

Environment variables:

-   EWTS_ENABLED
-   EWTS_LOG_DIR
-   `<MODULE>`{=html}\_LOGLEVEL
-   NGEN_RESULTS_DIR (when integrated with NGEN)

------------------------------------------------------------------------

## Initialization

Each language runtime supports explicit initialization:

-   C: EwtsInit(const char\* ewts_id)
-   C++: ewts::EwtsInit(std::string_view ewts_id)
-   Python: ewts.init(...)

If not explicitly initialized, EWTS defaults to "EWTS" as the module
identifier.
