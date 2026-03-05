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

// Optional: call before first Log to set EWTS ID; otherwise defaults to EWTS.
void EwtsInit(const char* ewts_id, bool ewts_ngen);

void Log(LogLevel level, const char* fmt, ...);
LogLevel GetLogLevel(void);
bool IsLoggingEnabled(void);

#ifdef __cplusplus
}
#endif

#endif /* EWTS_LOGGER_H */
