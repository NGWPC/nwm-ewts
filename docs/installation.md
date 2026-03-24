# Installation

This page describes common build and installation paths for EWTS.

## Requirements

EWTS typically requires:

- CMake 3.16 or newer
- a C/C++ compiler
- a Fortran compiler when building the Fortran runtime
- Python 3 for the Python runtime and generator tooling

## Build the full repository

```bash
cmake -B cmake_buld -S . -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON -DEWTS_BUILD_SHARED=ON
cmake --build cmake_buld -j
```

This top-level build compiles the native language-specific Runtime Libraries and builds the Python package.

## Install

```bash
cmake --install cmake_buld --prefix /path/to/install
```

A typical install includes:

- native EWTS Runtime Libraries
- generated constants and headers
- the `ngen` integration library when enabled
- CMake package configuration files
- the Python wheel produced by the top-level build

## Build Runtime Libraries only

```bash
cmake -B cmake_buld -S runtime -DCMAKE_BUILD_TYPE=Release
cmake --build cmake_buld -j
```

## Editable Python install

For direct Python runtime development:

```bash
pip install -e runtime/python/ewts
```

## Build a Python distribution manually

```bash
python -m build runtime/python/ewts
```

## Run Python tests

```bash
pip install pytest
pip install -e runtime/python/ewts
```
```bash
pytest runtime/python/ewts/tests
```
or

```bash
pytest
```

## Next steps

After installation, continue with:

- [Logging model](architecture/logging-model.md)
- [Configuration](architecture/configuration.md)
- [ngen integration](integrations/ngen.md)
