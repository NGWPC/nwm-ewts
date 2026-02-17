#include "ewts_ngen/ngen_log.h"
#include "Logger.hpp"
#include <cstdarg>

extern "C" void ngen_log(const char* module_key, int level_num, const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);

    // Call a Logger overload that accepts module_key + va_list (new overload)
    Logger::Log(module_key, level_num, fmt, ap);

    va_end(ap);
}
