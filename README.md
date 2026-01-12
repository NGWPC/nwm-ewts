# EWTS — Error, Warning, and Trapping System

EWTS is a lightweight, multi-language **logging and error-handling system** designed for scientific and engineering software.  
It provides consistent semantics across **Python, C++, C, and Fortran**, while remaining idiomatic within each language ecosystem.

The goal of EWTS is **clarity, portability, and predictability**, not feature bloat.

---

## Features

- Consistent log levels across languages
- UTC timestamps with optional millisecond precision
- Configurable output destinations (console, file)
- Environment-variable–driven configuration
- Minimal dependencies
- Suitable for HPC, CI, and long-running simulations

---

## Repository Structure
The repository contains the following directories:

- python/     : Python package, pip-installable
- cpp/        : C++ library, built with CMake
- c/          : C library, built with CMake
- fortran/    : Fortran module, built with CMake
- docs/       : Cross-language documentation
- LICENSE     : License for the repository

Each language implementation is self-contained and documented in its own subdirectory.

## Python

Located in python/ewts.

### Install (from Git):

    pip install git+https://github.com/NGWPC/nwm-ewts.git#subdirectory=python

### Usage:
```
from ewts.logger import configure_logger
LOG = configure_logger("LSTM")
LOG.info("Hello from EWTS")
```
### Development:

    cd python/ewts
    pip install -e .[dev]
    pytest

## C++

Located in cpp/.

### Usage with CMake FetchContent:
```
include(FetchContent)

FetchContent_Declare(
    ewts
    GIT_REPOSITORY https://github.com/NGWPC/nmm-ewts.git
    GIT_TAG v1.0.0
    SOURCE_SUBDIR cpp
)

FetchContent_MakeAvailable(ewts)

target_link_libraries(my_app PRIVATE ewts::logger)
```
### Usage:
```
#include <ewts/logger.hpp>

```
## C

Located in c/.

### Usage:
```
#include <ewts/logger.h>

```
## Fortran

Located in fortran/.

Usage:
```
use ewts_logger
```

# Design Philosophy
-----------------

- Consistency across languages, not identical implementations
- Explicit configuration, primarily via environment variables
- Minimal global state
- No hidden I/O
- Easy to embed, easy to remove

# License
-------
This project is licensed under the terms of the LICENSE file.

# Status
------

EWTS is under active development. APIs are stabilizing but may change prior to a 1.0 release.

