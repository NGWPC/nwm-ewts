#include "ewts_ngen/logger.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <mpi.h>
#include <map>
#include <mutex>
#include <sstream>
#include <sys/stat.h>

#define BOOST_BIND_GLOBAL_PLACEHOLDERS // intentionally want the old behavior
#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "ewts_ngen/ngen_module_keys.hpp"
#include "ewts/log_levels.hpp"

namespace {

static const char* const kEnvResultsDir    = "NGEN_RESULTS_DIR";
static const char* const kEnvEwtsLogDir    = "EWTS_LOG_DIR";
static const char* const kConfigFilename   = "ngen_logging.json";
static const char* const kEnvEwtsEnabled   = "EWTS_ENABLED";
static const char* const kDefaultRunLogsDirName = "run_logs";

inline bool IsDigitString(const std::string& s) {
    if (s.empty()) return false;
    for (char c : s) {
        if (c < '0' || c > '9') return false;
    }
    return true;
}

inline std::string ToUpper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

inline std::string ToLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

inline LogLevel ClampCanonicalLevel(int v) {
    // Canonical allowed numeric levels: 10/20/30/40/50 (and 0).
    if (v <= 0)  return LogLevel::NOTSET;
    if (v <= 10) return LogLevel::DEBUG;
    if (v <= 15) return LogLevel::PERFORM;
    if (v <= 20) return LogLevel::INFO;
    if (v <= 30) return LogLevel::WARNING;
    if (v <= 40) return LogLevel::SEVERE;
    return LogLevel::FATAL;
}

constexpr std::size_t EWTS_ID_WIDTH = 8;

inline std::string PadEwtsId(const std::string& id) {
    std::string s = ToUpper(id);
    if (s.size() >= EWTS_ID_WIDTH) return s.substr(0, EWTS_ID_WIDTH);
    s.append(EWTS_ID_WIDTH - s.size(), ' ');
    return s;
}

inline bool mpi_is_initialized() {
    int flag = 0;
    MPI_Initialized(&flag);
    return flag != 0;
}

} // namespace

Logger* Logger::GetLogger() {
    static Logger instance;   // C++11: initialized once, thread-safe
    return &instance;
}

void Logger::InitIfNeeded() {
    static std::once_flag once;
    std::call_once(once, [this]() {

        std::string ngenResultsDir;

        // Determine results dir
        const char* rd = std::getenv(kEnvResultsDir);
        if (rd && std::strlen(rd) > 0) {
            ngenResultsDir = std::string(rd);
        }

        // Determine module EWTS id (for log message prefix)
        // moduleKey is stable key (lowercase)
        const char* id_c = ewts_ngen::EwtsIdFromKey(moduleKey.c_str());
        if (id_c) {
            ewtsId = std::string(id_c);
        }

        // Read config only when NGEN_RESULTS_DIR is set, per requirements.
        bool loaded = false;
        if (!ngenResultsDir.empty()) {
            loaded = ReadConfigFromResultsDir(ngenResultsDir);
        }

        if (!loaded) {
            // Defaults when no results dir
            loggingEnabled = true;
            splitLogsByModule = false;
            // Prepopulate defaults for known modules (INFO) when generated registry is available.
            moduleLogLevels.clear();
            for (const auto& e : ewts_ngen::kModules) {
                if (e.key && *e.key) {                 // non-null and not ""
                    moduleLogLevels[std::string(e.key)] = LogLevel::INFO;
                }
            }
            moduleLogLevels[moduleKey] = LogLevel::INFO;
            logLevel = LogLevel::INFO;
        }

        ApplyEnvVars(true);

        // Determine MPI rank (optional)
        if (mpi_is_initialized()) {
            std::cout << "EWTS ngen running with MPI" << std::endl;
            int r = 0;
            MPI_Comm_rank(MPI_COMM_WORLD, &r);
            g_mpiRank = r;
        } else {
            std::cout << "EWTS ngen running WITHOUT MPI" << std::endl;
            g_mpiRank = 0;
        }

        SetupLogFile(ngenResultsDir);
    });
}

bool Logger::ReadConfigFromResultsDir(const std::string& resultsDir) {
    // Defaults
    loggingEnabled = true;
    splitLogsByModule = false;
    moduleLogLevels[moduleKey] = LogLevel::INFO;

    const std::string cfg = JoinPath(resultsDir, kConfigFilename);
    if (!FileExists(cfg)) {
        std::cout << "WARNING: EWTS config file " << cfg << " NOT FOUND. Defaults will be used" << std::endl;
        // No config file: keep defaults, but still export log level environment variables.
        logLevel = moduleLogLevels[moduleKey];
        return false;
    }

    std::cout << "EWTS config file " << cfg << std::endl;

    boost::property_tree::ptree pt;
    try {
        boost::property_tree::read_json(cfg, pt);
    } catch (const std::exception& e) {
        // If config is malformed, fall back to defaults but keep logging enabled.
        logLevel = moduleLogLevels[moduleKey];
        std::cerr << "WARNING: failed to parse " << cfg << ": " << e.what() << std::endl;
        return false;
    }

    // EWTS/logging enabled
    // Prefer explicit "ewts_enabled" if present; else use "logging_enabled".
    bool enabled = true;
    auto opt_ewts_enabled = pt.get_optional<bool>("ewts_enabled");
    if (opt_ewts_enabled) {
        enabled = *opt_ewts_enabled;
    } else {
        auto opt_logging_enabled = pt.get_optional<bool>("logging_enabled");
        if (opt_logging_enabled) enabled = *opt_logging_enabled;
    }
    loggingEnabled = enabled;
    std::cout << "EWTS logging " << ((loggingEnabled)? "ENABLED":"DISABLED") << std::endl;

    // split_logs_by_module (optional)
    auto opt_split = pt.get_optional<bool>("split_logs_by_module");
    if (opt_split) splitLogsByModule = *opt_split;
    std::cout << "EWTS logging to "
              << (splitLogsByModule ? "<MODULE>" : "a UNIFIED ngen")
              << " per rank file" << std::endl;

    // split_logs_by_module (optional)
    auto modules_child = pt.get_child_optional("modules");
    if (modules_child) {
        for (const auto& kv : *modules_child) {
            const std::string key = TrimString(kv.first);
            const std::string raw = TrimString(kv.second.get_value<std::string>());
            std::cout << "EWTS " << key << " log level read by ngen "
                      << ToUpper(raw) << std::endl;

            LogLevel lvl = LogLevel::INFO;
            if (IsDigitString(raw)) {
                lvl = ClampCanonicalLevel(std::atoi(raw.c_str()));
            } else {
                lvl = ParseLevel(raw);
            }
            moduleLogLevels[key] = lvl;
        }
    }

    // This module's effective level
    auto it = moduleLogLevels.find(moduleKey);
    logLevel = (it != moduleLogLevels.end()) ? it->second : LogLevel::INFO;
    return true;
}

void Logger::ApplyEnvVars(bool set) {
    if (!set) return;

    // EWTS_ENABLED=0|1 (default 1)
#if defined(_WIN32)
    // (Not expected for ngen build; no-op)
    (void)set;
#else
    ::setenv(kEnvEwtsEnabled, loggingEnabled ? "1" : "0", 1);
#endif

    // <MODULE>_LOGLEVEL=<10|15|20|30|40|50>
    for (const auto& kv : moduleLogLevels) {
        const std::string mod_key = kv.first;
        const LogLevel lvl = kv.second;
        const std::string ident = EnvVarIdentFromModuleKey(mod_key);
        if (ident.empty()) continue;

        const std::string env_name = ident + "_LOGLEVEL";
        const std::string env_val  = std::to_string(static_cast<int>(lvl));
#if !defined(_WIN32)
        ::setenv(env_name.c_str(), env_val.c_str(), 1);
#endif
        std::cout << "EWTS " << env_name << " set to "
                  << LevelToFixedString(lvl) << std::endl;
    }
}

std::string Logger::GetStandaloneBaseDir() {
    const char* ewts_log_dir = std::getenv(kEnvEwtsLogDir);
    if (ewts_log_dir && std::strlen(ewts_log_dir) > 0) {
        return std::string(ewts_log_dir);
    }

    const std::string home = GetHomeDir();
    if (!home.empty() && home != ".") {
        return JoinPath(home, kDefaultRunLogsDirName);
    }

    return JoinPath(".", kDefaultRunLogsDirName);
}

void Logger::SetupLogFile(const std::string& resultsDir) {
    // Determine output directory
    if (!resultsDir.empty()) {
        logFileDir = JoinPath(resultsDir, "logs");
    } else {
        logFileDir = GetStandaloneBaseDir();
    }

    (void)CreateDirectory(logFileDir);

    if (splitLogsByModule) {
        // In split mode, the destination file is selected per log call from the
        // incoming EWTS id, so only the directory is initialized here.
        logFilePath.clear();
        std::cout << "EWTS split log files under " << logFileDir << std::endl;
        return;
    }

    // Determine file name
    std::string stem = "ngen";

    std::string rank_part;
    if (mpi_is_initialized()) {
        rank_part = "_rank_" + std::to_string(GetLogger()->GetRank());
    }

    // Optional timestamp suffix (only when no results dir)
    std::string ts_part;
    if (resultsDir.empty()) {
        ts_part = "_" + CreateCompactTimestampUTC();
    }

    const std::string filename = stem + rank_part + ts_part + ".log";
    logFilePath = JoinPath(logFileDir, filename);

    // Open file (append)
    logFile.open(logFilePath.c_str(), std::ios::out | std::ios::app);

    std::cout << "EWTS log file " << logFilePath << std::endl;
}

bool Logger::LogFileReady() const {
    return logFile.is_open() && logFile.good();
}

void Logger::Log(LogLevel messageLevel, const std::string& message) {
    Logger* logger = GetLogger();
    Log(logger->ewtsId, messageLevel, message);
}

void Logger::Log(const std::string& moduleName, LogLevel messageLevel, const char* message, ...) {
    if (!message) return;

    Logger* logger = GetLogger();
    logger->InitIfNeeded();
    if (!logger->loggingEnabled) return;

    // For bridged/per-module logging, filter using the effective level for the
    // incoming moduleName, not the singleton logger instance's own module level.
    LogLevel effectiveLevel = logger->logLevel;
    bool foundEffectiveLevel = false;
    for (const auto& e : ewts_ngen::kModules) {
        if (e.ewts_id && moduleName == e.ewts_id) {
            if (e.key && *e.key) {
                auto it = logger->moduleLogLevels.find(std::string(e.key));
                if (it != logger->moduleLogLevels.end()) {
                    effectiveLevel = it->second;
                    foundEffectiveLevel = true;
                }
            }
            break;
        }
    }
    if (!foundEffectiveLevel && moduleName == logger->ewtsId) {
        effectiveLevel = logger->logLevel;
        foundEffectiveLevel = true;
    }
    if (!foundEffectiveLevel) {
        effectiveLevel = LogLevel::INFO;
    }
    if (static_cast<int>(messageLevel) < static_cast<int>(effectiveLevel)) return;

    // Format varargs into a std::string
    va_list args1;
    va_start(args1, message);
    va_list args2;
    va_copy(args2, args1);

    const int needed = std::vsnprintf(nullptr, 0, message, args1);
    va_end(args1);
    if (needed < 0) {
        va_end(args2);
        return;
    }

    std::string buf(static_cast<std::size_t>(needed) + 1U, '\0');
    std::vsnprintf(&buf[0], buf.size(), message, args2);
    va_end(args2);

    // remove trailing null
    if (!buf.empty() && buf.back() == '\0') buf.pop_back();

    Log(moduleName, messageLevel, buf);
}

void Logger::Log(LogLevel messageLevel, const char* message, ...) {
    if (!message) return;

    Logger* logger = GetLogger();
    logger->InitIfNeeded();
    if (!logger->loggingEnabled) return;
    if (static_cast<int>(messageLevel) < static_cast<int>(logger->logLevel)) return;

    // Format varargs into a std::string
    va_list args1;
    va_start(args1, message);
    va_list args2;
    va_copy(args2, args1);

    const int needed = std::vsnprintf(nullptr, 0, message, args1);
    va_end(args1);
    if (needed < 0) {
        va_end(args2);
        return;
    }

    std::string buf(static_cast<std::size_t>(needed) + 1U, '\0');
    std::vsnprintf(&buf[0], buf.size(), message, args2);
    va_end(args2);

    // remove trailing null
    if (!buf.empty() && buf.back() == '\0') buf.pop_back();

    Log(logger->ewtsId, messageLevel, buf);
}

void Logger::Log(const std::string& moduleName, LogLevel messageLevel, const std::string& message) {
    Logger* logger = GetLogger();
    logger->InitIfNeeded();

    if (!logger->loggingEnabled) return;

    // For bridged/per-module logging, filter using the effective level for the
    // incoming moduleName, not the singleton logger instance's own module level.
    LogLevel effectiveLevel = logger->logLevel;
    bool foundEffectiveLevel = false;
    for (const auto& e : ewts_ngen::kModules) {
        if (e.ewts_id && moduleName == e.ewts_id) {
            if (e.key && *e.key) {
                auto it = logger->moduleLogLevels.find(std::string(e.key));
                if (it != logger->moduleLogLevels.end()) {
                    effectiveLevel = it->second;
                    foundEffectiveLevel = true;
                }
            }
            break;
        }
    }
    if (!foundEffectiveLevel && moduleName == logger->ewtsId) {
        effectiveLevel = logger->logLevel;
        foundEffectiveLevel = true;
    }
    if (!foundEffectiveLevel) {
        effectiveLevel = LogLevel::INFO;
    }
    if (static_cast<int>(messageLevel) < static_cast<int>(effectiveLevel)) return;

    const std::string level_str = LevelToFixedString(messageLevel);

    // Prefix: <ISO timestamp> <EWTS_ID padded> <LEVEL padded>
    const std::string prefix = CreateTimestamp(true, true) + " " +
                               PadEwtsId(moduleName) + " " + level_str;

    std::istringstream in(message);
    std::string line;

    if (logger->splitLogsByModule) {
        static std::mutex splitLogMutex;
        static std::map<std::string, std::ofstream> splitLogFiles;

        // Route the message to the file for the EWTS id passed in this log call.
        std::lock_guard<std::mutex> lock(splitLogMutex);

        auto it = splitLogFiles.find(moduleName);
        if (it == splitLogFiles.end()) {
            std::string rank_part;
            if (mpi_is_initialized()) {
                rank_part = "_rank_" + std::to_string(logger->GetRank());
            }

            // Optional timestamp suffix (only when no results dir)
            std::string ts_part;
            const char* rd = std::getenv(kEnvResultsDir);
            if (!(rd && std::strlen(rd) > 0)) {
                ts_part = "_" + CreateCompactTimestampUTC();
            }

            const std::string filename = moduleName + rank_part + ts_part + ".log";
            const std::string path = JoinPath(logger->logFileDir, filename);

            std::ofstream& splitFile = splitLogFiles[moduleName];
            splitFile.open(path.c_str(), std::ios::out | std::ios::app);
            std::cout << "EWTS split log file " << path << std::endl;
            it = splitLogFiles.find(moduleName);
        }

        if (it != splitLogFiles.end() && it->second.is_open() && it->second.good()) {
            while (std::getline(in, line)) {
                it->second << prefix << " " << line << std::endl;
            }
            it->second.flush();
            return;
        }
    }

    if (logger->LogFileReady()) {
        while (std::getline(in, line)) {
            logger->logFile << prefix << " " << line << std::endl;
        }
        logger->logFile.flush();
    } else {
        while (std::getline(in, line)) {
            std::cout << prefix << " " << line << std::endl;
        }
        std::cout << std::flush;
    }
}

void Logger::Log(const std::string& message, LogLevel messageLevel) {
    Logger* logger = GetLogger();
    Log(logger->ewtsId, messageLevel, message);
}

std::string Logger::LevelToFixedString(LogLevel level) {
    const std::string name = std::string(ewts::LogLevelName(static_cast<int>(level)));
    // pad/truncate to 7 chars
    std::string out = name;
    if (out.size() < 7) out.append(7 - out.size(), ' ');
    if (out.size() > 7) out = out.substr(0, 7);
    return out;
}

LogLevel Logger::ParseLevel(const std::string& value) {
    std::string v = ToLower(TrimString(value));
    if (v == "debug") return LogLevel::DEBUG;
    if (v == "performance" || v == "perform") return LogLevel::PERFORM;
    if (v == "info") return LogLevel::INFO;
    if (v == "warning" || v == "warn") return LogLevel::WARNING;
    if (v == "error" || v == "severe") return LogLevel::SEVERE;
    if (v == "fatal" || v == "critical") return LogLevel::FATAL;
    if (v == "notset" || v == "none") return LogLevel::NOTSET;
    // Also accept "10"/"20"... (handled earlier), but in case:
    if (IsDigitString(v)) return ClampCanonicalLevel(std::atoi(v.c_str()));
    return LogLevel::INFO;
}

std::string Logger::TrimString(const std::string& str) {
    const char* ws = " \t\n\r\f\v";
    const size_t first = str.find_first_not_of(ws);
    if (first == std::string::npos) return "";
    const size_t last = str.find_last_not_of(ws);
    return str.substr(first, last - first + 1);
}

std::string Logger::CreateTimestamp(bool append_ms, bool iso) {
    using namespace std::chrono;
    const auto now = system_clock::now();
    const auto secs = time_point_cast<seconds>(now);
    const auto ms = duration_cast<milliseconds>(now - secs).count();

    std::time_t t = system_clock::to_time_t(now);
    std::tm tm_utc;
#if defined(_WIN32)
    gmtime_s(&tm_utc, &t);
#else
    gmtime_r(&t, &tm_utc);
#endif

    std::ostringstream oss;
    if (iso) {
        oss << std::put_time(&tm_utc, "%Y-%m-%dT%H:%M:%S");
        if (append_ms) {
            oss << "." << std::setw(3) << std::setfill('0') << ms;
        }
        oss << "Z";
    } else {
        oss << std::put_time(&tm_utc, "%Y-%m-%d %H:%M:%S");
        if (append_ms) {
            oss << "." << std::setw(3) << std::setfill('0') << ms;
        }
    }
    return oss.str();
}

std::string Logger::CreateCompactTimestampUTC() {
    using namespace std::chrono;
    const auto now = system_clock::now();
    std::time_t t = system_clock::to_time_t(now);
    std::tm tm_utc;
#if defined(_WIN32)
    gmtime_s(&tm_utc, &t);
#else
    gmtime_r(&t, &tm_utc);
#endif
    std::ostringstream oss;
    oss << std::put_time(&tm_utc, "%Y%m%dT%H%M%S");
    return oss.str();
}

bool Logger::FileExists(const std::string& path) {
    struct stat st;
    return ::stat(path.c_str(), &st) == 0 && S_ISREG(st.st_mode);
}

bool Logger::DirectoryExists(const std::string& path) {
    struct stat st;
    return ::stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode);
}

bool Logger::CreateDirectory(const std::string& path) {
    if (path.empty()) return false;
    if (DirectoryExists(path)) return true;

    const std::string cmd = "mkdir -p \"" + path + "\"";
    const int status = std::system(cmd.c_str());
    if (status == -1) return false;

    // status is shell-dependent; treat nonzero as failure
    return DirectoryExists(path);
}

std::string Logger::GetHomeDir() {
    const char* h = std::getenv("HOME");
    if (h && std::strlen(h) > 0) return std::string(h);
    return ".";
}

std::string Logger::JoinPath(const std::string& a, const std::string& b) {
    if (a.empty()) return b;
    if (b.empty()) return a;
    if (a.back() == '/') return a + b;
    return a + "/" + b;
}

std::string Logger::EnvVarIdentFromModuleKey(const std::string& key) {
    if (key.empty()) return "";

    // First try exact match
    if (const char* id = ewts_ngen::EwtsIdFromKey(key.c_str())) {
        return std::string(id);
    }

    // Then try lowercased key (registry keys are typically lowercase)
    std::string lower = key;
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char c){ return static_cast<char>(std::tolower(c)); });

    if (const char* id = ewts_ngen::EwtsIdFromKey(lower.c_str())) {
        return std::string(id);
    }
    return "";
}
