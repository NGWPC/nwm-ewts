#ifndef LOGGER_H
#define LOGGER_H

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    EWTS_NOTSET  = 0,
    EWTS_DEBUG   = 10,
    EWTS_PERFORM = 15,
    EWTS_INFO    = 20,
    EWTS_WARNING = 30,
    EWTS_SEVERE  = 40,
    EWTS_FATAL   = 50
} LogLevel;

// Optional: call before first Log to set EWTS ID; otherwise defaults to EWTS.
void EwtsInit(const char* ewts_id);

void Log(LogLevel level, const char* fmt, ...);
LogLevel GetLogLevel(void);
bool IsLoggingEnabled(void);

#ifdef __cplusplus
}
#endif

#endif /* LOGGER_H */
