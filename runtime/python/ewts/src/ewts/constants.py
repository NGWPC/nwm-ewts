# Values unique to each ngen module (example shown; you’ll generate these per module)
MODULE_NAME           = "T-Route"
EV_MODULE_LOGLEVEL    = "TROUTE_LOGLEVEL"      # numeric (10/20/30/40/50). default INFO=20

# Common EWTS variables
EV_EWTS_ENABLED       = "EWTS_ENABLED"                 # 0/1, default 1
EV_EWTS_LOG_DIR       = "EWTS_LOG_DIR"                 # set by ngen when in-ngen
EV_EWTS_RANK          = "EWTS_RANK"                    # set by ngen when in-ngen
EV_EWTS_SPLIT_BY_MOD  = "EWTS_SPLIT_LOGS_BY_MODULE"    # 0/1, default 0

DS                    = "/"
LOG_DIR_DEFAULT       = "run_logs"     # (you requested ~/run_logs for standalone)
LOG_FILE_EXT          = "log"
LOG_MODULE_NAME_LEN   = 8

