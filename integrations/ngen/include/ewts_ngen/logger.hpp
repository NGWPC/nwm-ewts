#ifndef EWTS_NGEN_LOGGER_HPP
#define EWTS_NGEN_LOGGER_HPP

#include <cstdarg>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>

/*
 * NGEN integration logger.
 *
 * - Owns all logging policy (config/env/file/format) in Logger.cpp
 * - Reads <NGEN_RESULTS_DIR>/ngen_logging.json when NGEN_RESULTS_DIR is set
 * - Exports EWTS_ENABLED and <MODULE>_LOGLEVEL environment variables
 * - Supports optional MPI rank suffix (compile with -DNGEN_WITH_MPI)
 */

enum class LogLevel : int {
    NOTSET  = 0,
    DEBUG   = 10,
    PERFORM = 15,
    INFO    = 20,
    WARNING = 30,
    SEVERE  = 40,
    FATAL   = 50,
};

class Logger {
  public:
    static Logger* GetLogger();

    // Backwards-compatible overloads
    static void Log(const std::string& message, LogLevel messageLevel = LogLevel::INFO);
    static void Log(LogLevel messageLevel, const std::string& message);
    static void Log(LogLevel messageLevel, const char* message, ...);

    // New ewtsID-aware overloads
    static void Log(const std::string& moduleName, LogLevel messageLevel, const std::string& message);
    static void Log(const std::string& moduleName, LogLevel messageLevel, const char* message, ...);

    static inline void LogAndThrow(const std::string& message) {
        Log(message, LogLevel::SEVERE);
        throw std::runtime_error(message);
    }

    bool IsLoggingEnabled() const { return loggingEnabled; }
    LogLevel GetLogLevel() const { return logLevel; }

  private:
    Logger() = default;
    ~Logger() = default;
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    // init/policy
    void InitIfNeeded();
    bool ReadConfigFromResultsDir(const std::string& resultsDir);
    void ApplyEnvVars(bool set);

    // log file
    void SetupLogFile(const std::string& resultsDir);
    bool LogFileReady() const;

    // helpers
    static std::string CreateTimestamp(bool append_ms = true, bool iso = true);
    static std::string CreateCompactTimestampUTC();  // YYYYMMDDTHHMMSS
    static std::string LevelToFixedString(LogLevel level);
    static LogLevel ParseLevel(const std::string& value);
    static std::string TrimString(const std::string& str);

    static bool FileExists(const std::string& path);
    static bool DirectoryExists(const std::string& path);
    static bool CreateDirectory(const std::string& path);

    static std::string GetHomeDir();
    static std::string JoinPath(const std::string& a, const std::string& b);
    static std::string EnvVarIdentFromModuleKey(const std::string& key);

    int GetRank() const { return mpiRank; }

    // state
    bool        loggingEnabled  = true;
    bool        splitLogsByModule = false;

    std::fstream logFile;
    std::string  logFileDir;
    std::string  logFilePath;

    // module identity (stable key is lower case; ewts_id is upper case for log messages)
    std::string  moduleKey = "ngen";
    std::string  ewtsId    = "NGEN";

    LogLevel     logLevel = LogLevel::INFO;

    // config-derived per-module levels (stable key -> LogLevel)
    std::unordered_map<std::string, LogLevel> moduleLogLevels;

    // environment
    

    // mpi
    int mpiRank = 0;
};

#endif /* EWTS_NGEN_LOGGER_HPP */
