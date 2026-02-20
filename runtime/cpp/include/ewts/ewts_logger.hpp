#pragma once

#include <string_view>

namespace ewts {

enum class LogLevel : int {
    NOTSET  = 0,
    DEBUG   = 10,
    PERFORM = 15,
    INFO    = 20,
    WARNING = 30,
    SEVERE  = 40,
    FATAL   = 50
};

bool IsLoggingEnabled();
LogLevel GetLogLevel();
void Log(LogLevel level, std::string_view message);
void Logf(LogLevel level, const char* fmt, ...);

}  // namespace ewts
