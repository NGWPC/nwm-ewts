
# EWTS ngen Integration

This directory contains the integration layer that allows the EWTS logging
framework to route messages into the ngen runtime environment.

The integration provides a bridge between EWTS language runtimes
(C, C++, Fortran, and Python) and the ngen logging/results infrastructure.

---

## Table of Contents

- [Purpose](#purpose)
- [Initialization Behavior](#initialization-behavior)
- [Log File Modes](#log-file-modes)
  - [Unified log file (default)](#unified-log-file-default)
  - [Split log files by module](#split-log-files-by-module)
  - [Enabling split logs](#enabling-split-logs)
  - [Full example](#full-example)
  - [Behavior details](#behavior-details)
- [Build](#build)
- [Runtime Behavior](#runtime-behavior)
- [Standalone Fallback](#standalone-fallback)
- [Environment Variables](#environment-variables)
- [Architecture](#architecture)
- [Notes](#notes)

---

## Purpose

When ngen executes hydrologic formulations, multiple BMI modules may run
within the same process and across many MPI ranks. The EWTS ngen integration
ensures that:

- log messages from all EWTS runtimes are routed through ngen when available
- logs are written into the ngen results directory structure
- logging configuration is read from `ngen_logging.json`
- when running in an MPI system, logs are written to a rank identified log file per MPI process.

---



## Initialization Behavior

The `logger.cpp` implementation used by the ngen integration **does not require
an explicit initialization call** from ngen.

Instead, the logger uses a **lazy initialization pattern**.

The first time any module calls the EWTS logger (for example through
`LOG(...)`, `Log(...)`, or the module-specific wrappers), the logger performs
its initialization automatically. This initialization typically includes:

1. Detecting whether ngen integration is active.
2. Checking for the `NGEN_RESULTS_DIR` environment variable.
3. Reading logging configuration from:

```
<NGEN_RESULTS_DIR>/ngen_logging.json
```

4. Exporting module-specific log level environment variables.
5. Determining the MPI rank if MPI has been initialized.
6. Opening the appropriate log file.

Because initialization happens on the **first logging call**, modules do not
need to explicitly call an initialization routine. This keeps the integration
simple and avoids requiring ngen or BMI modules to manage logger lifecycle.

In practice the flow looks like:

```
BMI module executes
        │
        ▼
First call to LOG(...) or Log(...)
        │
        ▼
EWTS logger initializes automatically
        │
        ▼
Subsequent log calls reuse the initialized logger
```

This approach guarantees:

- initialization happens exactly once
- no explicit initialization dependency in ngen
- safe behavior even when multiple modules log during startup

---

## Log File Modes

EWTS supports two log file modes when running under ngen.

---

### Unified log file (default)

All log messages are written to:

```
logs/ngen_rank_<rank>.log
```

---

### Split log files by module

When enabled, logs are written per module:

```
logs/ngen_rank_0.log
logs/CFE_rank_0.log
logs/NOAHOWP_rank_0.log
logs/SFT_rank_0.log
logs/SMP_rank_0.log
logs/TROUTE_rank_0.log
```

---

### Enabling split logs

Edit:

```
<NGEN_RESULTS_DIR>/ngen_logging.json
```

Add:

```json
{
  "split_logs_by_module": true
}
```

---

### Full example

```json
{
    "logging_enabled": true,
    "split_logs_by_module": true,
    "modules": {
        "cfe-s": "info",
        "sft": "info",
        "smp": "info",
        "t-route": "debug",
        "ngen": "info",
        "forcing": "info",
        "noah-owp-modular": "info"
    }
}
```

---

### Behavior details

- Logs routed by EWTS ID passed into log call
- Files created lazily
- File handles remain open
- One set per MPI rank

---

## Build

The ngen integration is built automatically when EWTS is configured with:

```bash
cmake -DEWTS_WITH_NGEN=ON
```

and compiled as part of the normal EWTS build:

```bash
cmake --build cmakebuild
```

---

## Runtime Behavior

When ngen integration is enabled and `NGEN_RESULTS_DIR` is set:

```
<NGEN_RESULTS_DIR>/ngen_logging.json
<NGEN_RESULTS_DIR>/logs/
```

EWTS will:

1. Read configuration from `ngen_logging.json`
2. Export module log level environment variables
3. Write logs to rank-specific files:

```
logs/ngen_rank_<rank>.log
```

If MPI is not initialized, a single log file is used.

---

## Standalone Fallback

If `NGEN_RESULTS_DIR` is not defined, EWTS falls back to standalone logging:

1. `EWTS_LOG_DIR`
2. `$HOME/run_logs`
3. `./run_logs`

---

## Environment Variables

| Variable | Purpose |
|--------|--------|
| `NGEN_RESULTS_DIR` | ngen results directory containing `ngen_logging.json` |
| `EWTS_LOG_DIR` | Standalone logging directory |
| `EWTS_LOG_LEVEL` | Default log level |
| `EWTS_ENABLED` | Enable/disable EWTS logging |

---

## Architecture

```
BMI Modules
     │
     ▼
Language Runtimes
(C / C++ / Fortran / Python)
     │
     ▼
EWTS Runtime Logger
     │
     ▼
ngen Bridge (this directory)
     │
     ▼
ngen results logging
```

---

## Notes

- The integration layer does **not** control standalone logging behavior.
- It only routes logs when ngen runtime configuration is active.
- Standalone behavior is implemented in the language runtime loggers.
