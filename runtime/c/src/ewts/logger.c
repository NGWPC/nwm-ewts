#include "ewts/logger.h"

#include <ctype.h>
#include <errno.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

/* Optional NGEN bridge. Present only when linked into an NGEN build. */
#if defined(__GNUC__) || defined(__clang__)
__attribute__((weak))
#endif
void ewts_ngen_log(const char* ewts_id, int level, const char* message);

#define EV_NGEN_RESULTS_DIR "NGEN_RESULTS_DIR"
#define EV_EWTS_ENABLED     "EWTS_ENABLED"
#define EV_EWTS_LOG_DIR     "EWTS_LOG_DIR"
#define EV_EWTS_LOG_LEVEL   "EWTS_LOG_LEVEL"

#ifndef EWTS_ID
#define EWTS_ID "EWTS"
#endif
static char g_ewts_id[64] = EWTS_ID;   /* runtime module id */
static bool g_use_ngen = false;

static pthread_mutex_t g_log_mutex = PTHREAD_MUTEX_INITIALIZER;

static int g_initialized = 0;
static int g_enabled = 1;
static LogLevel g_level = INFO;

static FILE* g_file = NULL;
static char g_path[1024] = {0};
static char g_ewts_id_padded[9] = {0}; /* 8 + NUL */

static int streq_ci(const char* a, const char* b) {
    if (!a || !b) return 0;
    while (*a && *b) {
        if (toupper((unsigned char)*a) != toupper((unsigned char)*b)) return 0;
        ++a; ++b;
    }
    return *a == '\0' && *b == '\0';
}

static void trim_copy(const char* in, char* out, size_t out_sz) {
    if (!out || out_sz == 0) return;
    out[0] = '\0';
    if (!in) return;
    while (isspace((unsigned char)*in)) ++in;

    size_t len = strlen(in);
    while (len > 0 && isspace((unsigned char)in[len - 1])) --len;
    if (len >= out_sz) len = out_sz - 1;
    memcpy(out, in, len);
    out[len] = '\0';
}

static int is_ngen_active(void) {
    const char* v = getenv(EV_NGEN_RESULTS_DIR);
    return (v && v[0] != '\0');
}

static int parse_enabled(const char* v) {
    if (!v || v[0] == '\0') return 1;
    char s[32];
    trim_copy(v, s, sizeof(s));
    if (s[0] == '\0') return 1;

    if (streq_ci(s, "0") || streq_ci(s, "false") || streq_ci(s, "no") ||
        streq_ci(s, "off") || streq_ci(s, "disabled")) {
        return 0;
    }
    return 1;
}

static void build_module_loglevel_env(char* out, size_t out_sz) {
    size_t n = 0;
    for (const char* p = g_ewts_id; *p && n + 1 < out_sz; ++p) {
        out[n++] = (char)toupper((unsigned char)*p);
    }
    const char* suffix = "_LOGLEVEL";
    for (const char* p = suffix; *p && n + 1 < out_sz; ++p) out[n++] = *p;
    out[n] = '\0';
}

static void pad_ewts_id(void) {
    size_t i = 0;
    for (; i < 8 && g_ewts_id[i] != '\0'; ++i) g_ewts_id_padded[i] = (char)toupper((unsigned char)g_ewts_id[i]);
    for (; i < 8; ++i) g_ewts_id_padded[i] = ' ';
    g_ewts_id_padded[8] = '\0';
}

static void utc_timestamp_iso_ms(char* buf, size_t sz) {
    if (!buf || sz == 0) return;

    struct timeval tv;
    gettimeofday(&tv, NULL);

    struct tm tm_utc;
    gmtime_r(&tv.tv_sec, &tm_utc);

    // Need at least "YYYY-MM-DDTHH:MM:SS.mmmZ" + NUL = 25 bytes
    if (sz < 25) {
        buf[0] = '\0';
        return;
    }

    size_t n = strftime(buf, sz, "%Y-%m-%dT%H:%M:%S", &tm_utc);
    if (n == 0) {
        buf[0] = '\0';
        return;
    }

    unsigned int ms = (unsigned int)(tv.tv_usec / 1000);
    if (ms > 999) ms = 999;

    // Append ".mmmZ"
    buf[n++] = '.';
    buf[n++] = (char)('0' + (ms / 100) % 10);
    buf[n++] = (char)('0' + (ms / 10)  % 10);
    buf[n++] = (char)('0' + (ms % 10));
    buf[n++] = 'Z';
    buf[n]   = '\0';
}

static void utc_timestamp_compact(char* buf, size_t sz) {
    time_t t = time(NULL);
    struct tm tm_utc;
    gmtime_r(&t, &tm_utc);
    strftime(buf, sz, "%Y%m%dT%H%M%S", &tm_utc);
}

static const char* level_name_padded(LogLevel lvl) {
    switch ((int)lvl) {
        case DEBUG:   return "DEBUG  ";
        case PERFORM: return "PERFORM";
        case INFO:    return "INFO   ";
        case WARNING: return "WARNING";
        case SEVERE:  return "SEVERE ";
        case FATAL:   return "FATAL  ";
        default:           return "NOTSET ";
    }
}

static LogLevel parse_level(const char* v) {
    if (!v || v[0] == '\0') return NOTSET;
    char s[32];
    trim_copy(v, s, sizeof(s));
    if (s[0] == '\0') return NOTSET;

    char* end = NULL;
    long num = strtol(s, &end, 10);
    if (end && *end == '\0' && num >= 0) return (LogLevel)num;

    if (streq_ci(s, "DEBUG"))   return DEBUG;
    if (streq_ci(s, "PERFORM")) return PERFORM;
    if (streq_ci(s, "INFO"))    return INFO;
    if (streq_ci(s, "WARN") || streq_ci(s, "WARNING")) return WARNING;
    if (streq_ci(s, "ERROR") || streq_ci(s, "SEVERE")) return SEVERE;
    if (streq_ci(s, "FATAL") || streq_ci(s, "CRITICAL")) return FATAL;
    if (streq_ci(s, "NOTSET") || streq_ci(s, "NONE")) return NOTSET;

    return NOTSET;
}

static int dir_exists(const char* path) {
    struct stat st;
    return (stat(path, &st) == 0) && S_ISDIR(st.st_mode);
}

static int mkdir_p(const char* path) {
    if (!path || path[0] == '\0') return 0;
    char tmp[1024];
    snprintf(tmp, sizeof(tmp), "%s", path);
    size_t len = strlen(tmp);
    if (len == 0) return 0;
    if (tmp[len - 1] == '/') tmp[len - 1] = '\0';

    for (char* p = tmp + 1; *p; ++p) {
        if (*p == '/') {
            *p = '\0';
            if (!dir_exists(tmp)) {
                if (mkdir(tmp, 0775) != 0 && errno != EEXIST) return 0;
            }
            *p = '/';
        }
    }
    if (!dir_exists(tmp)) {
        if (mkdir(tmp, 0775) != 0 && errno != EEXIST) return 0;
    }
    return 1;
}

static void open_standalone_file(void) {
    if (g_file) return;

    const char* dir = getenv(EV_EWTS_LOG_DIR);
    char log_dir[1024];

    if (dir && dir[0] != '\0') {
        snprintf(log_dir, sizeof(log_dir), "%s", dir);
    } else {
        const char* home = getenv("HOME");
        if (home && home[0] != '\0')
            snprintf(log_dir, sizeof(log_dir), "%s/run_logs", home);
        else
            snprintf(log_dir, sizeof(log_dir), "./run_logs");
    }

    (void)mkdir_p(log_dir);

    char ts[32];
    utc_timestamp_compact(ts, sizeof(ts));

    int n = snprintf(g_path, sizeof(g_path), "%s/%s_%s.log", log_dir, g_ewts_id, ts);
    if (n < 0 || (size_t)n >= sizeof(g_path)) {
        n = snprintf(g_path, sizeof(g_path), "%s/%s.log", log_dir, g_ewts_id);
        if (n < 0 || (size_t)n >= sizeof(g_path)) {
            fprintf(stderr,
                    "EWTS ERROR: Log path too long (dir='%s', id='%s'). Falling back to stdout.\n",
                    log_dir, g_ewts_id);
            g_path[0] = '\0';
            g_file = stdout;   /* ensure Log() has somewhere to write */
            return;
        } else {
            fprintf(stderr,
                    "EWTS WARNING: Log path truncated using shorter filename '%s'.\n",
                    g_path);
        }
    }

    g_file = fopen(g_path, "a");
    if (!g_file) {
        fprintf(stderr,
                "EWTS ERROR: Failed to open log file '%s'. Falling back to stdout.\n",
                g_path);
        g_file = stdout;
    }
}

static void load_env_preferences(void) {
    g_enabled = parse_enabled(getenv(EV_EWTS_ENABLED));
    printf("EWTS %s logging is %s\n", g_ewts_id, ((g_enabled)?"ENABLED":"DISABLED"));
    
    char key[64];
    build_module_loglevel_env(key, sizeof(key));
    LogLevel lvl = parse_level(getenv(key));
    fprintf(stdout, "EWTS %s log level from env var %s is %s\n", g_ewts_id, key, level_name_padded(lvl));
    fflush(stdout);
    if ((int)lvl != NOTSET) { 
        g_level = lvl;
        fprintf(stdout, "EWTS %s log level set to %s\n", g_ewts_id, level_name_padded(g_level));
        fflush(stdout);
        return;
    }

    lvl = parse_level(getenv(EV_EWTS_LOG_LEVEL));
    g_level = ((int)lvl != NOTSET) ? lvl : INFO;
    fprintf(stdout, "EWTS %s using default log level = %s\n", g_ewts_id, level_name_padded(lvl));
    fflush(stdout);

}

static void init_once(void) {
    if (g_initialized) return;
    g_initialized = 1;
    pad_ewts_id();
    load_env_preferences();
    if (g_use_ngen && is_ngen_active() && ewts_ngen_log) {
        printf("EWTS %s using ngen for logging\n", g_ewts_id);
    }
    else {
        printf("EWTS %s logging standalone\n", g_ewts_id);
    }

}

void EwtsInit(const char* ewts_id, bool ewts_ngen) {
    /* Allow caller to set EWTS id before first use. */
    pthread_mutex_lock(&g_log_mutex);

    if (!g_initialized) {
        g_use_ngen = ewts_ngen;
        if (ewts_id && ewts_id[0] != '\0') {
            /* trim/copy into g_ewts_id */
            trim_copy(ewts_id, g_ewts_id, sizeof(g_ewts_id));
        }
        /* run existing init */
        init_once();
    }

    pthread_mutex_unlock(&g_log_mutex);
}

LogLevel GetLogLevel(void) {
    init_once();
    return g_level;
}

bool IsLoggingEnabled(void) {
    init_once();
    return g_enabled ? true : false;
}

void Log(LogLevel level, const char* fmt, ...) {
    if (!fmt) return;

    init_once();
    if (!g_enabled) return;
    if ((int)level < (int)g_level) return;

    va_list ap;
    va_start(ap, fmt);
    va_list ap2;
    va_copy(ap2, ap);
    int n = vsnprintf(NULL, 0, fmt, ap2);
    va_end(ap2);
    if (n < 0) { va_end(ap); return; }

    char* msg = (char*)malloc((size_t)n + 1);
    if (!msg) { va_end(ap); return; }
    vsnprintf(msg, (size_t)n + 1, fmt, ap);
    va_end(ap);

    if (g_use_ngen && is_ngen_active() && ewts_ngen_log) {
        ewts_ngen_log(g_ewts_id, (int)level, msg);
        free(msg);
        return;
    }

    char ts[32];
    utc_timestamp_iso_ms(ts, sizeof(ts));
    const char* lvl_str = level_name_padded(level);

    pthread_mutex_lock(&g_log_mutex);
    open_standalone_file();

    FILE* out = g_file ? g_file : stdout;

    char* saveptr = NULL;
    char* line = strtok_r(msg, "\n", &saveptr);

    if (!line) {
        fprintf(out, "%s %s %s\n", ts, g_ewts_id_padded, lvl_str);
    } else {
        while (line) {
            fprintf(out, "%s %s %s %s\n", ts, g_ewts_id_padded, lvl_str, line);
            line = strtok_r(NULL, "\n", &saveptr);
        }
    }

    fflush(out);
    pthread_mutex_unlock(&g_log_mutex);
    free(msg);
}
