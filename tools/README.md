
# EWTS Language Constants Generator

This tool generates **language-specific constants and lookup tables** used by the EWTS runtimes for C, C++, Fortran, and Python.

The generator ensures that:

- Module identifiers are **consistent across all languages**
- Log levels remain **synchronized across runtimes**
- The EWTS system has a **single source of truth** for module metadata

The generator script is:

```
tools/generate_language_constants.py
```

The generator reads two specification files:

- Module registry: `spec/module_registry.yaml`
- Log levels: `spec/log_levels.json`

These specifications define all module identifiers and log level definitions used by the EWTS system.

Example module registry entry:

```yaml
- key: smp
  ewts_id: SMP
  description: "Soil Moisture Profiles Model"
```

Example log level entry:

```json
"INFO": 20
```

The generator reads these definitions and produces language‑specific constants for:

- C
- C++
- Fortran
- Python

---

# Why this tool exists

Hydrologic workflows in **ngen** execute multiple modules within the same process.
To ensure logging remains consistent across languages and modules, EWTS uses a **central specification** for module IDs and log levels.

Instead of duplicating these definitions manually in every language runtime, this generator:

- reads the canonical specification
- produces language‑specific source files
- guarantees the runtimes stay synchronized

---

# Inputs

## Module Registry

Defined in:

```
spec/module_registry.yaml
```

This file defines:

- module key
- EWTS module ID
- description

Example entries include modules such as:

- ngen
- smp
- sft
- t-route
- noah-owp-modular

These map module keys to EWTS module identifiers used in logging. fileciteturn21file2

---

## Log Level Specification

Defined in:

```
spec/log_levels.json
```

This file defines the canonical EWTS log levels:

- NOTSET
- DEBUG
- PERFORM
- INFO
- WARNING
- SEVERE
- FATAL

Each level maps to an integer value used across all runtimes. fileciteturn21file3

---

# Running the Generator

From the repository root:

```bash
python tools/generate_language_constants.py
```

The script automatically detects the repository root and reads the specification files.

Optional arguments allow overriding paths:

```bash
python tools/generate_language_constants.py     --registry spec/module_registry.yaml     --log-levels spec/log_levels.json
```

The generator prints all files it produces during execution.

---

# Generated Files

The generator creates the following files:

## C Runtime

```
runtime/c/include/ewts/module_keys.h
runtime/c/include/ewts/log_levels.h
runtime/c/include/ewts/module_constants.h
runtime/c/src/ewts/module_keys.c
```

## C++ Runtime

```
runtime/cpp/include/ewts/module_keys.hpp
runtime/cpp/include/ewts/log_levels.hpp
runtime/cpp/include/ewts/module_constants.hpp
```

## Fortran Runtime

```
runtime/fortran/src/ewts/module_keys.f90
runtime/fortran/src/ewts/log_levels.f90
runtime/fortran/src/ewts/module_constants.f90
```

## Python Runtime

```
runtime/python/ewts/src/ewts/module_keys.py
runtime/python/ewts/src/ewts/log_levels.py
runtime/python/ewts/src/ewts/modules.py
```

---

# Important Notes

The generated files include a header like:

```
AUTO-GENERATED FILE. DO NOT EDIT.
```

These files should **never be modified manually**.

If module IDs or log levels need to change:

1. Update the specification file
2. Re-run the generator

---

# Design Benefits

This approach provides:

- **Single source of truth** for module identifiers
- **Cross-language consistency**
- **Elimination of manual duplication**
- **Automatic regeneration when specs change**
