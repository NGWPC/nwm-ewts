#include "ewts_ngen/ewts_ngen_bridge.h"
#include "ewts_ngen/logger.hpp"

void ewts_ngen_log(const char* ewts_id, int level, const char* message)
{
    if (!ewts_id || !message) return;

    // The API is a static Logger::Log(...) (no instance required)
    Logger::Log(std::string(ewts_id), static_cast<LogLevel>(level), std::string(message));
}
