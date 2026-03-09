#ifndef EWTS_LOGGER_HPP
#define EWTS_LOGGER_HPP

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

// Optional: call before first Log to set EWTS ID; otherwise defaults to EWTS.
void EwtsInit(std::string_view ewts_id, bool ewts_ngen = true);

bool IsLoggingEnabled();
LogLevel GetLogLevel();
void Log(LogLevel level, std::string_view message);
void Log(LogLevel level, const char* fmt, ...);
void Log(std::string_view message, LogLevel level);

}  // namespace ewts

// Placed here to ensure the class is declared before setting this preprocessor symbol
#define LOG ::ewts::Log

#endif /* EWTS_LOGGER_HPP */
