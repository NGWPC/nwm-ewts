# ngen Integration

The EWTS `ngen` integration routes log messages from all supported language-specific Runtime Libraries
through a shared logger implementation used by `ngen` runs.

## What the integration does

When active, the integration layer is responsible for:

- detecting the `ngen` results environment
- reading `ngen_logging.json`
- determining effective log levels
- applying consistent log formatting
- writing output into `NGEN_RESULTS_DIR/logs/`
- preserving per-rank file separation for MPI runs

## Initialization behavior

The integration logger is initialized lazily on the first log call. Modules do
not need to call a separate initialization routine in `ngen` itself.

## File layout modes

EWTS supports two file layout modes under `ngen`.

### Unified mode

Each rank writes to a single file:

```text
logs/ngen_rank_0.log
```

### Split-by-module mode

Each rank writes separate files by module:

```text
logs/cfe_rank_0.log
logs/ngen_rank_0.log
logs/noahowp_rank_0.log
logs/smp_rank_0.log
```

Enable split mode in `ngen_logging.json`:

```json
{
  "split_logs_by_module": true
}
```

## Runtime relationship

The Runtime Libraries remain responsible for creating and forwarding log
messages, but under `ngen` they do not own the final output policy.

## Developer reference

For implementation details in this repository, see:

- `integrations/ngen/README.md`
