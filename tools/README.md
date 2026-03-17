# `generate_language_constants.py`

## Table of Contents

- [Overview](#generate_language_constantspy)
- [What the Script Generates](#what-the-script-generates)
  - [Runtime Outputs](#runtime-outputs)
    - [C](#c)
    - [C++ (runtime)](#c-runtime)
    - [Fortran](#fortran)
    - [Python](#python)
  - [ngen-specific Outputs](#ngen-specific-outputs)
- [Input Files](#input-files)
  - [Module Registry YAML](#1-module-registry-yaml)
    - [Registry Rules](#registry-rules)
  - [Log Levels JSON](#2-log-levels-json)
- [Repository Layout Assumptions](#repository-layout-assumptions)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
  - [Default Usage](#default-usage)
  - [Specify Explicit Input Paths](#specify-explicit-input-paths)
  - [Specify Repo Root Explicitly](#specify-repo-root-explicitly)
- [How Filtering Works](#how-filtering-works)
  - [C Modules](#c-modules)
  - [C++ Modules](#c-modules-runtime)
  - [Fortran Modules](#fortran-modules)
  - [Python Modules](#python-modules)
  - [ngen Outputs](#ngen-outputs)
- [Expected Generated Content Examples](#expected-generated-content-examples)
  - [Example: C++ Runtime Constants](#example-c-runtime-constants)
  - [Example: Python Runtime Constants](#example-python-runtime-constants)
  - [Example: ngen Aggregate Constants](#example-ngen-aggregate-constants)
  - [Example: ngen Aggregate Module Key Helpers](#example-ngen-aggregate-module-key-helpers)
- [Typical Usage in ngen Code](#typical-usage-in-ngen-code)
- [Typical Usage in Runtime Code](#typical-usage-in-runtime-code)
- [Script Behavior Summary](#script-behavior-summary)
- [Notes](#notes)



This script generates EWTS module key, module constant, and log-level files for the supported runtime languages, plus aggregate ngen-specific headers for the `integrations/ngen` code.

This tool generates **language-specific constants and lookup tables** used by the EWTS runtimes for C, C++, Fortran, and Python.

It reads:
- a module registry YAML file
- a log levels JSON file

and writes generated files into the repository under `runtime/...` and `integrations/ngen/...`.

The generator ensures that:

- Module identifiers are **consistent across all languages**
- Log levels remain **synchronized across runtimes**
- The EWTS system has a **single source of truth** for module metadata

## What the script generates

### Runtime outputs
The script filters runtime module outputs by the `language` field in `module_registry.yaml`.

That means:
- C runtime files get only modules where `language: c`
- C++ runtime files get only modules where `language: cpp`
- Fortran runtime files get only modules where `language: fortran`
- Python runtime files get only modules where `language: python`

Generated runtime files include:

### C
- `runtime/c/include/ewts/module_keys.h`
- `runtime/c/src/ewts/module_keys.c`
- `runtime/c/include/ewts/module_constants.h`
- `runtime/c/include/ewts/log_levels.h`

### C++
- `runtime/cpp/include/ewts/module_keys.hpp`
- `runtime/cpp/include/ewts/module_constants.hpp`
- `runtime/cpp/include/ewts/log_levels.hpp`

### Fortran
- `runtime/fortran/src/ewts/module_keys.f90`
- `runtime/fortran/src/ewts/module_constants.f90`
- `runtime/fortran/src/ewts/log_levels.f90`

### Python
- `runtime/python/ewts/src/ewts/module_keys.py`
- `runtime/python/ewts/src/ewts/modules.py`
- `runtime/python/ewts/src/ewts/log_levels.py`

## ngen-specific outputs
In addition to the runtime outputs, the script generates aggregate ngen headers containing **all** modules from the registry, regardless of language. This allows the ngen integration code to avoid depending on the runtime C++ headers.

Generated ngen files:
- `integrations/ngen/include/ewts_ngen/ngen_module_constants.hpp`
- `integrations/ngen/include/ewts_ngen/ngen_module_keys.hpp`

These are intended for use only by `integrations/ngen` code.

## Input files

## 1. Module registry YAML
The module registry must be a YAML mapping with a top-level `modules` list. Each module entry must define:
- `key`
- `ewts_id`
- `language`
- optionally `description`

Example from the attached registry:

```yaml
version: 1
modules:
  - key: ngen
    ewts_id: NGEN
    language: cpp
    description: "ngen framework"
  - key: cfe-s
    ewts_id: CFE
    language: c
    description: "Conceptual Functional Equivalent to the National Water Model (Schaake)"
  - key: forcing
    ewts_id: FORCING
    language: python
    description: "Forcing Engine"
```

### Registry rules
The script enforces the following:
- `modules` must exist and be a list
- `key` must be non-empty
- `ewts_id` must be non-empty
- `language` must be one of:
  - `c`
  - `cpp`
  - `fortran`
  - `python`
- `ewts_id` must be uppercase
- `ewts_id` must be at most 8 characters long
- module `key` values must be unique
- duplicate `ewts_id` values are allowed

Duplicate `ewts_id` values are useful for aliases. For example, the attached registry maps `cfe-s`, `cfe-x`, and `cfe` to the same `ewts_id: CFE`.

## 2. Log levels JSON
The log levels file must be a JSON object with a non-empty `levels` mapping:

```json
{
  "version": 1,
  "levels": {
    "NOTSET": 0,
    "DEBUG": 10,
    "PERFORM": 15,
    "INFO": 20,
    "WARNING": 30,
    "SEVERE": 40,
    "FATAL": 50
  }
}
```

The script uses this file to generate log-level helpers for C, C++, Fortran, and Python.

## Repository layout assumptions
By default, the script assumes it lives at:

```text
tools/generate_language_constants.py
```

and infers the repository root as the parent of the `tools` directory.

It also assumes default spec paths relative to the repository root:
- `spec/module_registry.yaml`
- `spec/log_levels.json`

## Requirements
- Python 3
- `PyYAML`

Install dependency:

```bash
pip install pyyaml
```

If `PyYAML` is missing, the script exits with an error message.

## How to run

### Default usage
Run from anywhere:

```bash
python tools/generate_language_constants.py
```

This uses:
- `spec/module_registry.yaml`
- `spec/log_levels.json`
- inferred repo root

### Specify explicit input paths

```bash
python tools/generate_language_constants.py \
  --registry spec/module_registry.yaml \
  --log-levels spec/log_levels.json
```

### Specify repo root explicitly

```bash
python tools/generate_language_constants.py \
  --repo-root /path/to/repo \
  --registry spec/module_registry.yaml \
  --log-levels spec/log_levels.json
```

Supported command-line arguments are defined in the script's `argparse` setup. 
S
## How filtering works
Given the attached `module_registry.yaml`, the runtime outputs are filtered like this:

### C modules
These entries go into the C runtime outputs:
- `cfe-s`
- `cfe-x`
- `cfe`
- `pet`
- `topmodel` SW

### C++ modules
These entries go into the C++ runtime outputs:
- `ngen`
- `lasam`
- `sft`
- `smp`
- `ueb` 

### Fortran modules
These entries go into the Fortran runtime outputs:
- `noah-owp-modular`
- `sac-sma`
- `snow-17`

### Python modules
These entries go into the Python runtime outputs:
- `forcing`
- `lstm`
- `topoflow-glacier`
- `t-route`

### ngen outputs
The ngen headers include **all** modules from the registry, across all languages. The script generates those through separate ngen-specific functions and writes them to `integrations/ngen/include/ewts_ngen`. 

## Expected generated content examples

## Example: C++ runtime constants
For a C++ module such as `ueb`, the generated runtime C++ constants header will contain entries like:

```cpp
inline constexpr const char* EWTS_KEY_UEB = "ueb";
inline constexpr const char* EWTS_ID_UEB  = "UEB_BMI";
```

This comes from the `ueb` registry entry.

## Example: Python runtime constants
For a Python module such as `t-route`, the generated Python constants file will contain entries like:

```python
T_ROUTE_KEY = "t-route"
T_ROUTE_ID = "TROUTE"
```

This comes from the `t-route` registry entry.

## Example: ngen aggregate constants
The ngen constants header will include all modules, such as both `t-route` and `ueb`, even though those belong to different runtime languages:

```cpp
namespace ewts_ngen {
namespace modules {
inline constexpr const char* EWTS_KEY_T_ROUTE = "t-route";
inline constexpr const char* EWTS_ID_T_ROUTE  = "TROUTE";

inline constexpr const char* EWTS_KEY_UEB = "ueb";
inline constexpr const char* EWTS_ID_UEB  = "UEB_BMI";
}
}
```

The script generates this separately from the runtime C++ constants so ngen does not need to include the runtime header. 

## Example: ngen aggregate module key helpers
The ngen key helper header includes lookup helpers such as:
- `EwtsIdFromKey`
- `DescriptionFromKey`
- `KeysFromEwtsId`
- `DescriptionsFromEwtsId`
- `FirstKeyFromEwtsId`
- `FirstDescriptionFromEwtsId` 

These are scoped under `namespace ewts_ngen`.

## Typical usage in ngen code

### Include the ngen-specific headers

```cpp
#include "ewts_ngen/ngen_module_constants.hpp"
#include "ewts_ngen/ngen_module_keys.hpp"
```

### Use constants

```cpp
const char* module_key = ewts_ngen::modules::EWTS_KEY_T_ROUTE;
const char* module_id  = ewts_ngen::modules::EWTS_ID_T_ROUTE;
```

### Use lookup helpers

```cpp
const char* ewts_id = ewts_ngen::EwtsIdFromKey("cfe-s");
const char* desc = ewts_ngen::DescriptionFromKey("cfe-s");
```

## Typical usage in runtime code
Existing runtime code can continue to include the runtime-specific generated files, for example:

```cpp
#include "ewts/module_constants.hpp"
#include "ewts/module_keys.hpp"
```

and those files will contain only the modules for the runtime language being generated.

## Script behavior summary
- Runtime outputs are language-filtered.
- ngen outputs are aggregate across all languages.
- Runtime and ngen headers are separate so you can change only `integrations/ngen` include usage without touching existing runtime module includes.
- Log levels are generated from `log_levels.json` and are not filtered by module language. 

## Notes
- The script prints the input spec paths, versions, generation timestamp, and a list of generated files when it runs. 
- Generated files include provenance banners showing when they were generated and which spec files were used. 
- The repository version field in the module registry is optional, but helpful for traceability. 
