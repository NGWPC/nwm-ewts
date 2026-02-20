#ifndef EWTS_C_LOGGER_H
#define EWTS_C_LOGGER_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * EWTS C Logger Adapter (submodule-side)
 *
 * Routing:
 *   - If NGEN_RESULTS_DIR is set/non-empty, treat as "ngen active" and route via
 *       ewts_ngen_log(ewts_id, level, message)
 *     so formatting/routing remains in the ngen C++ Logger.
 *
 *   - Otherwise, write standalone logs to:
 *       $EWTS_LOG_DIR/<EWTSID>_<YYYYMMDDTHHMMSS>.log
 *     default: ~/run_logs/<...>
 *
 * Standalone line format:
 *   <YYYY-MM-DDTHH:MM:SS.mmmZ> <EWTSID padded to 8> <LEVEL padded to 7> <message>
 *
 * Env vars:
 *   - NGEN_RESULTS_DIR         : if set/non-empty => ngen active
 *   - EWTS_ENABLED             : if set to 0/false/no/off/disabled => logging disabled
 *   - EWTS_LOG_DIR             : standalone log directory (default: ~/run_logs)
 *   - EWTS_LOG_LEVEL           : global default level
 *   - <EWTSID>_LOGLEVEL        : per-module override (e.g., CFE_LOGLEVEL)
 *
 * Module identity:
 *   - Prefer generated constants:
 *       #include "ewts/module_constants.h"
 *       #define EWTS_ID EWTS_ID_CFE
 *   - Or compile with: -DEWTS_ID=\"CFE\"
 */

typedef enum {
    EWTS_NOTSET  = 0,
    EWTS_DEBUG   = 10,
    EWTS_PERFORM = 15,
    EWTS_INFO    = 20,
    EWTS_WARNING = 30,
    EWTS_SEVERE  = 40,
    EWTS_FATAL   = 50
} LogLevel;

void Log(LogLevel level, const char* fmt, ...);
LogLevel GetLogLevel(void);
bool IsLoggingEnabled(void);

#ifdef __cplusplus
}
#endif

#endif /* EWTS_C_LOGGER_H */
