#include "ewts_ngen_bridge.h"
#include "Logger.hpp"

using ewts::Logger;

void ewts_ngen_log(const char* ewts_id, int level, const char* message)
{
    if (!ewts_id || !message) return;
    Logger& logger = Logger::GetInstance();
    logger.Log(ewts_id, level, message);
}
