#include "ewts_ngen/ewts_ngen_bridge.h"
#include "ewts_ngen/logger.hpp"

void ewts_ngen_log(const char* ewts_id, int level, const char* message)
{
    if (!ewts_id || !message) return;

    auto log_level = static_cast<LogLevel>(level);

    if (log_level == LogLevel::STATUS) {
        Logger::LogPayload(message);
        return;
    }
    // The API is a static Logger::Log(...) (no instance required)
    Logger::Log(std::string(ewts_id), static_cast<LogLevel>(level), std::string(message));
}


void ewts_ngen_payload_status(const char* status,
                              double prog,
                              const char* msg,
                              const char* modnm)
{
    Logger::LogPayload(
        status ? status : "",
        prog,
        msg ? msg : "",
        modnm ? modnm : "");
}
