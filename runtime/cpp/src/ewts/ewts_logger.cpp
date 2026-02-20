#include "ewts_logger.hpp"

#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <string>
#include <string_view>

#include <sys/time.h>
#include <time.h>

#ifndef EWTS_ID
#define EWTS_ID "CFE"
#endif

#ifdef EWTS_HAVE_NGEN_BRIDGE
#include "ewts_ngen/ewts_ngen_bridge.h"
#else
extern "C" void ewts_ngen_log(const char* ewts_id, int level, const char* message);
#endif

namespace ewts {

static constexpr const char* EV_NGEN_RESULTS_DIR = "NGEN_RESULTS_DIR";
static constexpr const char* EV_EWTS_ENABLED     = "EWTS_ENABLED";
static constexpr const char* EV_EWTS_LOG_DIR     = "EWTS_LOG_DIR";
static constexpr const char* EV_EWTS_LOG_LEVEL   = "EWTS_LOG_LEVEL";

static std::once_flag g_once;
static bool g_enabled = true;
static LogLevel g_level = LogLevel::INFO;

static std::mutex g_mtx;
static std::ofstream g_out;
static std::string g_path;
static std::string g_ewts_id_padded;

static bool is_ngen_active() {
    const char* v = std::getenv(EV_NGEN_RESULTS_DIR);
    return (v && *v);
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
    std::string id(EWTS_ID);
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
    std::string id(EWTS_ID);
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
    char out[48];
    std::snprintf(out, sizeof(out), "%s.%03ldZ", base, ms);
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

static void open_standalone_file() {
    if (g_out.is_open()) return;

    const char* dir = std::getenv(EV_EWTS_LOG_DIR);
    std::string log_dir;
    if (dir && *dir) log_dir = dir;
    else {
        const char* home = std::getenv("HOME");
        log_dir = (home && *home) ? (std::string(home) + "/run_logs") : "./run_logs";
    }

    std::error_code ec;
    std::filesystem::create_directories(log_dir, ec);

    g_path = log_dir + "/" + std::string(EWTS_ID) + "_" + utc_timestamp_compact() + ".log";
    g_out.open(g_path, std::ios::out | std::ios::app);
}

static void init_once() {
    g_enabled = parse_enabled(std::getenv(EV_EWTS_ENABLED));

    auto key = module_loglevel_env();
    auto lvl = parse_level(std::getenv(key.c_str()));
    if ((int)lvl != 0) g_level = lvl;
    else {
        lvl = parse_level(std::getenv(EV_EWTS_LOG_LEVEL));
        g_level = ((int)lvl != 0) ? lvl : LogLevel::INFO;
    }

    pad_id();
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

    if (is_ngen_active()) {
        std::string msg(message);
        ewts_ngen_log(EWTS_ID, (int)level, msg.c_str());
        return;
    }

    std::lock_guard<std::mutex> lk(g_mtx);
    open_standalone_file();

    const auto ts = utc_timestamp_iso_ms();
    const char* lvl = level_name_padded(level);

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

void Logf(LogLevel level, const char* fmt, ...) {
    if (!fmt) return;

    va_list ap;
    va_start(ap, fmt);
    va_list ap2;
    va_copy(ap2, ap);
    int n = std::vsnprintf(nullptr, 0, fmt, ap2);
    va_end(ap2);
    if (n < 0) { va_end(ap); return; }

    std::string buf;
    buf.resize((size_t)n);
    std::vsnprintf(buf.data(), (size_t)n + 1, fmt, ap);
    va_end(ap);

    Log(level, buf);
}

}  // namespace ewts
