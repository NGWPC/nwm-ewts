# Contributing

This documentation site is intentionally concise. Repository contributors should
also use the developer-facing `README.md` files in each implementation
subdirectory when making changes.

## Development expectations

When contributing to EWTS, try to preserve:

- cross-language consistency in runtime behavior
- the generated-constants model as the single source of truth
- shared-runtime safety for modules running in the same process
- compatibility with both `ngen`-integrated and standalone execution

## Typical development workflow

```bash
cmake -B cmake_buld -S . -DCMAKE_BUILD_TYPE=Release
cmake --build cmake_buld -j
```

For Python work:

```bash
pip install -e runtime/python/ewts
pytest runtime/python/ewts/tests
```

## Before opening a pull request

Review whether your change affects:

- generated constants
- runtime configuration behavior
- `ngen` integration behavior
- per-language README documentation
- user-facing MkDocs pages

## Developer references

For implementation-specific guidance, see:

- `runtime/c/README.md`
- `runtime/cpp/README.md`
- `runtime/fortran/README.md`
- `runtime/python/README.md`
- `integrations/ngen/README.md`
- `tools/README.md`
