# EWTS C Runtime

The EWTS C runtime provides:

-   `void EwtsInit(const char* ewts_id);`
-   `void Log(LogLevel level, const char* fmt, ...);`
-   Environment-driven configuration

## Build

Built via the root CMake configuration:

cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release cmake --build build
-j

## Thread Safety

Logging operations are protected via mutex to ensure safe multi-threaded
use.

## Environment Variables

-   EWTS_ENABLED
-   EWTS_LOG_DIR
-   `<MODULE>`{=html}\_LOGLEVEL
