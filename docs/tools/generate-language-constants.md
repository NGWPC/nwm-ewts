# Language Constants Generator

The EWTS language constants generator creates language-specific module and
log-level definitions from repository specification files.

## Purpose

The generator keeps module identifiers and log levels synchronized across:

- C
- C++
- Fortran
- Python
- the `ngen` integration layer

## Inputs

The generator reads:

- `spec/module_registry.yaml`
- `spec/log_levels.json`

These files act as the single source of truth for generated constants.

## Outputs

The script writes generated files into the runtime and integration directories.
Runtime outputs are filtered by language, while the `ngen` integration receives
aggregate headers spanning all registered modules.

## Run the generator

```bash
python tools/generate_language_constants.py
```

## Developer reference

For validation rules, generated output locations, and implementation details,
see:

- `tools/README.md`
