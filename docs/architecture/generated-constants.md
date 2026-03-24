# Generated Constants

EWTS uses generated constants so module identifiers and log levels stay aligned
across C, C++, Fortran, Python, and the `ngen` integration layer.

## Single source of truth

Generated outputs are derived from:

- `spec/module_registry.yaml`
- `spec/log_levels.json`

These specification files define the canonical module registry and log-level
values for the framework.

## Why generated constants matter

The generated model helps ensure that:

- language-specific Runtime Libraries use the same module identifiers
- log levels remain synchronized across languages
- new modules are introduced through the registry rather than by duplicating
  constants manually
- `ngen` can consume its own generated aggregate headers without depending on a
  runtime-specific constant set

## Regenerating files

```bash
python tools/generate_language_constants.py
```

Generated files should be treated as derived artifacts and should not be edited
by hand.

## Related documentation

- [Language constants generator](../tools/generate-language-constants.md)
