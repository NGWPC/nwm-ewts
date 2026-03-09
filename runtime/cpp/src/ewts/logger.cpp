#include "ewts/logger.hpp"

#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <iostream>
#include <string>
#include <string_view>

#include <sys/time.h>
#include <time.h>

#include <dlfcn.h>
#include <iostream>

/* Optional NGEN bridge. Present only when linked into an NGEN build. */
#if defined(__GNUC__) || defined(__clang__)
__attribute__((weak))
#endif
void ewts_ngen_log(const char* ewts_id, int level, const char* message);

namespace ewts {

static constexpr const char* EV_NGEN_RESULTS_DIR = "NGEN_RESULTS_DIR";
static constexpr const char* EV_EWTS_ENABLED     = "EWTS_ENABLED";
static constexpr const char* EV_EWTS_LOG_DIR     = "EWTS_LOG_DIR";
static constexpr const char* EV_EWTS_LOG_LEVEL   = "EWTS_LOG_LEVEL";

#ifndef EWTS_ID
#define EWTS_ID "EWTS"
#endif
static std::string g_ewts_id = EWTS_ID;
static bool g_use_ngen = false;

static std::once_flag g_once;
static bool g_enabled = true;
static LogLevel g_level = LogLevel::INFO;

static std::mutex g_init_mtx;
static std::string g_requested_ewts_id;

static std::mutex g_mtx;
static std::ofstream g_out;
static std::string g_path;
static std::string g_ewts_id_padded;

static bool is_ngen_active() {
    const char* v = std::getenv(EV_NGEN_RESULTS_DIR);
    return (v && *v);
}

using ewts_ngen_log_fn = void(*)(const char*, int, const char*);
static ewts_ngen_log_fn g_ngen_log = nullptr;

// Resolve ewts_ngen_log dynamically because ngen loads model plugins
// with dlopen(), which may hide symbols from RTLD_DEFAULT depending
// on loader flags. Using dlsym ensures we can find the bridge even
// if it wasn't linked as a hard dependency.
static ewts_ngen_log_fn resolve_ngen_log()
{
    if (void* sym = dlsym(RTLD_DEFAULT, "ewts_ngen_log"))
        return reinterpret_cast<ewts_ngen_log_fn>(sym);
    return nullptr;
}

static inline bool have_ngen_bridge()
{
    return g_use_ngen && is_ngen_active() && (g_ngen_log != nullptr);
}

static bool parse_enabled(const char* v) {
    if (!v || !*v) return true;
    std::string s(v);
    auto l = s.find_first_not_of(" \t\r\n");
    auto r = s.find_last_not_of(" \t\r\n");
    s = (l == std::string::npos) ? "" : s.substr(l, r - l + 1);
    for (auto& c : s) c = (char)std::toupper((unsigned char)c);
    if (s.empty()) return true;
    return !(s == "0" || s == "FALSE" || s == "NO" || s == "OFF" || s == "DISABLED");
}

static std::string module_loglevel_env() {
    std::string id = g_ewts_id;
    for (auto& c : id) c = (char)std::toupper((unsigned char)c);
    return id + "_LOGLEVEL";
}

static LogLevel parse_level(const char* v) {
    if (!v || !*v) return LogLevel::NOTSET;
    std::string s(v);
    auto l = s.find_first_not_of(" \t\r\n");
    auto r = s.find_last_not_of(" \t\r\n");
    s = (l == std::string::npos) ? "" : s.substr(l, r - l + 1);
    if (s.empty()) return LogLevel::NOTSET;

    char* end = nullptr;
    long num = std::strtol(s.c_str(), &end, 10);
    if (end && *end == '\0' && num >= 0) return (LogLevel)num;

    for (auto& c : s) c = (char)std::toupper((unsigned char)c);

    if (s == "DEBUG") return LogLevel::DEBUG;
    if (s == "PERFORM") return LogLevel::PERFORM;
    if (s == "INFO") return LogLevel::INFO;
    if (s == "WARN" || s == "WARNING") return LogLevel::WARNING;
    if (s == "ERROR" || s == "SEVERE") return LogLevel::SEVERE;
    if (s == "FATAL" || s == "CRITICAL") return LogLevel::FATAL;
    if (s == "NOTSET" || s == "NONE") return LogLevel::NOTSET;

    return LogLevel::NOTSET;
}

static void pad_id() {
    std::string id = g_ewts_id;
    for (auto& c : id) c = (char)std::toupper((unsigned char)c);
    if (id.size() >= 8) g_ewts_id_padded = id.substr(0, 8);
    else g_ewts_id_padded = id + std::string(8 - id.size(), ' ');
}

static std::string utc_timestamp_iso_ms() {
    timeval tv{};
    gettimeofday(&tv, nullptr);
    tm tm_utc{};
    gmtime_r(&tv.tv_sec, &tm_utc);
    char base[32];
    std::strftime(base, sizeof(base), "%Y-%m-%dT%H:%M:%S", &tm_utc);
    long ms = tv.tv_usec / 1000;
    unsigned ms3 = static_cast<unsigned>(ms) % 1000u;
    char out[48];
    int n = std::snprintf(out, sizeof(out), "%s.%03uZ", base, ms3);
    std::snprintf(out, sizeof(out), "%s.%03uZ", base, ms3);
    if (n < 0 || static_cast<std::size_t>(n) >= sizeof(out)) {
        // Should never happen with these buffer sizes, but keeps compilers happy + safe.
        return std::string("0000-00-00T00:00:00.000Z");
    }
    return std::string(out);
}

static std::string utc_timestamp_compact() {
    std::time_t t = std::time(nullptr);
    tm tm_utc{};
    gmtime_r(&t, &tm_utc);
    char out[32];
    std::strftime(out, sizeof(out), "%Y%m%dT%H%M%S", &tm_utc);
    return std::string(out);
}

static const char* level_name_padded(LogLevel lvl) {
    switch ((int)lvl) {
        case 10: return "DEBUG  ";
        case 15: return "PERFORM";
        case 20: return "INFO   ";
        case 30: return "WARNING";
        case 40: return "SEVERE ";
        case 50: return "FATAL  ";
        default: return "NOTSET ";
    }
}

static void open_standalone_file()
{
    if (g_out.is_open()) return;

    const char* dir = std::getenv(EV_EWTS_LOG_DIR);
    std::string log_dir;

    if (dir && *dir) {
        log_dir = dir;
    }
    else {
        const char* home = std::getenv("HOME");
        log_dir = (home && *home)
                    ? (std::string(home) + "/run_logs")
                    : "./run_logs";
    }

    std::error_code ec;
    std::filesystem::create_directories(log_dir, ec);
    if (ec) {
        std::cerr << "EWTS WARNING: Failed to create log directory '"
                  << log_dir << "': " << ec.message()
                  << ". Falling back to stdout.\n";
        return;
    }

    std::string ts = utc_timestamp_compact();
    g_path = log_dir + "/" + g_ewts_id + "_" + ts + ".log";

    g_out.open(g_path, std::ios::out | std::ios::app);

    if (!g_out.is_open()) {
        std::cerr << "EWTS ERROR: Failed to open log file '"
                  << g_path << "'. Falling back to stdout.\n";

        /* Optional fallback to shorter filename */
        g_path = log_dir + "/" + g_ewts_id + ".log";
        g_out.open(g_path, std::ios::out | std::ios::app);

        if (!g_out.is_open()) {
            std::cerr << "EWTS ERROR: Fallback log file also failed. "
                      << "Logging will go to std::out.\n";
        }
        else {
            std::cerr << "EWTS WARNING: Using fallback log file '"
                      << g_path << "'.\n";
        }
    }
}

static void init_once() {
    {
        std::lock_guard<std::mutex> lk(g_init_mtx);
        if (!g_requested_ewts_id.empty()) g_ewts_id = g_requested_ewts_id;
    }    
    
    g_enabled = parse_enabled(std::getenv(EV_EWTS_ENABLED));
    std::cout << "EWTS " << g_ewts_id << " logging is " << ((g_enabled)?"ENABLED":"DISABLED") << std::endl;
    fflush(stdout);

    auto key = module_loglevel_env();
    auto lvl = parse_level(std::getenv(key.c_str()));
    std::cout << "EWTS " << g_ewts_id << " log level from env var " << key << " is " << level_name_padded(lvl) << std::endl;
    fflush(stdout);
    if ((int)lvl != 0) {
        g_level = lvl;
        std::cout << "EWTS " << g_ewts_id << " log level set to " << level_name_padded(g_level) << std::endl;
    } 
    else {
        lvl = parse_level(std::getenv(EV_EWTS_LOG_LEVEL));
        g_level = ((int)lvl != 0) ? lvl : LogLevel::INFO;
        std::cout << "EWTS " << g_ewts_id << " using default log level = " << level_name_padded(g_level) << std::endl;
    }
    fflush(stdout);

    pad_id();

    // Set the bridge method
    g_ngen_log = resolve_ngen_log();

    if (have_ngen_bridge()) {
        std::cout << "EWTS " << g_ewts_id << " using ngen for logging " << std::endl;
    }
    else {
        std::cout << "EWTS " << g_ewts_id << " logging standalone " << std::endl;
    }



}

void EwtsInit(std::string_view ewts_id, bool ewts_ngen) {
    {
        g_use_ngen = ewts_ngen;
        std::lock_guard<std::mutex> lk(g_init_mtx);
        if (!ewts_id.empty()) g_requested_ewts_id = std::string(ewts_id);
    }
    std::call_once(g_once, init_once);
}

bool IsLoggingEnabled() {
    std::call_once(g_once, init_once);
    return g_enabled;
}

LogLevel GetLogLevel() {
    std::call_once(g_once, init_once);
    return g_level;
}

void Log(LogLevel level, std::string_view message) {
    std::call_once(g_once, init_once);
    if (!g_enabled) return;
    if ((int)level < (int)g_level) return;

    if (have_ngen_bridge()) {
        std::string msg(message);
        g_ngen_log(g_ewts_id.c_str(), (int)level, msg.c_str());
        return;
    }

    const auto ts = utc_timestamp_iso_ms();
    const char* lvl = level_name_padded(level);

    std::lock_guard<std::mutex> lk(g_mtx); // Automatically unlocks g_mtx when lk goes out of scope
    open_standalone_file();

    std::string msg(message);
    size_t start = 0;
    while (true) {
        size_t pos = msg.find('\n', start);
        std::string line = (pos == std::string::npos) ? msg.substr(start) : msg.substr(start, pos - start);

        std::ostream& out = g_out.is_open() ? g_out : std::cout;
        out << ts << " " << g_ewts_id_padded << " " << lvl << " " << line << "\n";
        out.flush();

        if (pos == std::string::npos) break;
        start = pos + 1;
    }
}

void Log(std::string_view message, LogLevel level) {
    Log(level, message);
}

void Log(LogLevel level, const char* fmt, ...) {
    if (!fmt) return;

    va_list ap;
    va_start(ap, fmt);
    va_list ap2;
    va_copy(ap2, ap);
    int n = std::vsnprintf(nullptr, 0, fmt, ap2);
    va_end(ap2);
    if (n < 0) { va_end(ap); return; }

    std::string buf;
    buf.resize((size_t)n + 1);
    std::vsnprintf(buf.data(), (size_t)n + 1, fmt, ap);
    buf.resize((size_t)n); // drop the trailing '\0'
    va_end(ap);

    Log(level, buf);
}

}  // namespace ewts
