#ifndef EWTS_LOGGER_H
#define EWTS_LOGGER_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    NOTSET  = 0,
    DEBUG   = 10,
    PERFORM = 15,
    INFO    = 20,
    WARNING = 30,
    SEVERE  = 40,
    FATAL   = 50
} LogLevel;

/* Compatibility API */
void EwtsInit(const char* ewts_id, bool ewts_ngen);
void Log(LogLevel level, const char* fmt, ...);
LogLevel GetLogLevel(void);
bool IsLoggingEnabled(void);

/* Explicit per-module API */
void EwtsLogModule(const char* ewts_id, LogLevel level, const char* fmt, ...);
LogLevel EwtsGetLogLevelModule(const char* ewts_id);
bool EwtsIsLoggingEnabledModule(const char* ewts_id);

#ifdef __cplusplus
}
#endif

/*
 * Optional convenience rebinding:
 *
 * If a module defines EWTS_ID before including this header, calls such as
 *   Log(INFO, "message");
 * are redirected to the per-module implementation:
 *   EwtsLogModule(EWTS_ID, INFO, "message");
 *
 * This preserves existing call sites while avoiding process-global collisions.
 */
#ifdef EWTS_ID
#define Log(level, ...)               EwtsLogModule(EWTS_ID, (level), __VA_ARGS__)
#define GetLogLevel()                 EwtsGetLogLevelModule(EWTS_ID)
#define IsLoggingEnabled()            EwtsIsLoggingEnabledModule(EWTS_ID)

/* Optional uppercase convenience */
#define LOG(level, ...)               EwtsLogModule(EWTS_ID, (level), __VA_ARGS__)
#else
/* Fallback compatibility path */
#define LOG(level, ...)               Log((level), __VA_ARGS__)
#endif

#endif /* EWTS_LOGGER_H */
