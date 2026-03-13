# EWTS C++ Runtime

The EWTS C++ runtime provides logging facilities for C++ components running
within **ngen hydrologic workflows** or as standalone applications.

It shares the same configuration system and module identity model as the C,
Fortran, and Python runtimes.

The runtime implementation is located under:

```text
runtime/cpp/
```

---

## Key Concepts

The C++ runtime uses a **module-scoped logger model**.

Each module obtains a logger bound to a unique EWTS module ID. This prevents
collisions when multiple modules run inside the same `ngen` process.

---

## Important: Initialization When Running with ngen

When EWTS is used within **ngen**, it is important to initialize the module
logger **before the first log call**.

The recommended place to do this is inside the module’s **BMI `Initialize()`**
method.

This ensures:

- the correct **module ID** is bound before any message is emitted
- module-specific configuration such as `<MODULE>_LOGLEVEL` is applied
- logging is correctly routed through the ngen bridge when active
- the first log lines are attributed to the intended module

If a module logs before initialization, the message may be attributed to the
default fallback logger rather than the correct module.

Example:

```cpp
#include "ewts/module_constants.hpp"
#define EWTS_ID ewts::modules::EWTS_ID_SFT
#include "ewts/logger.hpp"

void bmi_model::Initialize()
{
    ewts::EwtsInit(EWTS_ID, true);
    LOG(ewts::LogLevel::INFO, "Initializing Soil Freeze Thaw module");
}
```

---

## Basic Usage

Example usage in a C++ module:

```cpp
#include "ewts/module_constants.hpp"
#define EWTS_ID ewts::modules::EWTS_ID_SFT
#include "ewts/logger.hpp"

int main()
{
    ewts::EwtsInit(EWTS_ID, false);

    LOG(ewts::LogLevel::INFO, "Initializing Soil Freeze Thaw module");
    LOG(ewts::LogLevel::DEBUG, "Debug information");

    return 0;
}
```

The `LOG(...)` macro routes messages to the module-specific logger.

---

## Logger Initialization Model

The C++ runtime uses a **lazy initialization pattern** internally:

- the logger is created on first use
- configuration is read from environment variables
- the logger instance is stored in a registry keyed by module ID

Even with lazy initialization, ngen modules should still call `EwtsInit(...)`
during BMI `Initialize()` so the correct module is bound before the first log.

---

## Example Log Output

```text
2026-03-12T12:41:03.123Z SFT      INFO    Initializing Soil Freeze Thaw module
```

---

## Log Levels

```cpp
ewts::LogLevel::DEBUG
ewts::LogLevel::PERFORM
ewts::LogLevel::INFO
ewts::LogLevel::WARNING
ewts::LogLevel::SEVERE
ewts::LogLevel::FATAL
```

Example:

```cpp
LOG(ewts::LogLevel::WARNING, "Calibration parameter out of range");
```

---

## Environment Variables

The same configuration variables are used across runtimes:

| Variable | Purpose |
|---|---|
| `EWTS_ENABLED` | Enable logging |
| `EWTS_LOG_LEVEL` | Default level |
| `<MODULE>_LOGLEVEL` | Module override |
| `EWTS_LOG_DIR` | Standalone logging directory |
| `NGEN_RESULTS_DIR` | ngen results directory |

---

## MPI Support

When running under MPI, the logger writes to rank-specific files such as:

```text
logs/ngen_rank_0.log
logs/ngen_rank_1.log
```

This avoids cross-rank file collisions.

---

## ngen Integration

When linked with the ngen integration library, logs are forwarded through the
ngen bridge and written according to ngen runtime configuration.

---

## Runtime Safety

The C++ runtime avoids:

- process-global module identity
- unsafe global string buffers
- unsafe string concatenation

Instead, it uses a **module-ID keyed logger registry** plus guarded writes.
