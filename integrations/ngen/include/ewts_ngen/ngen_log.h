#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* module_key: stable key like "t-route" or EWTS id like "TROUTE"
   level_num: 10/20/30/40/50
   fmt: printf-style format string
*/
void ngen_log(const char* module_key, int level_num, const char* fmt, ...);

#ifdef __cplusplus
}
#endif
