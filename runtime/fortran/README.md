# EWTS Fortran Runtime

The EWTS Fortran runtime provides logging support for Fortran modules running
standalone or under `ngen`.

The runtime implementation is located under:

```text
runtime/fortran/
```

## Public API

The EWTS `logger` module exports module-aware logging entry points:

```fortran
call logger_init(id)
call logger_init_module(id)

call write_log(msg, lvl)
call write_log_module(id, msg, lvl)

enabled = is_logger_enabled()
enabled = is_logger_enabled_module(id)

lvl = get_log_level()
lvl = get_log_level_module(id)

call payload_status(ewts_id, status, prog, msg, modnm)
```

For `ngen` execution, prefer the module-specific APIs that take an EWTS ID.

## Log levels

| Level | Value |
|---|---:|
| `EWTS_NOTSET` | 0 |
| `EWTS_DEBUG` | 10 |
| `EWTS_PERFORM` | 15 |
| `EWTS_INFO` | 20 |
| `EWTS_WARNING` | 30 |
| `EWTS_SEVERE` | 40 |
| `EWTS_FATAL` | 50 |
| `EWTS_STATUS` | 60 |

`EWTS_STATUS` is reserved for structured payload messages.

## Direct EWTS usage

A Fortran module can use EWTS directly:

```fortran
use logger
use ewts_module_constants

call logger_init_module(EWTS_ID_NOAH_OWP_MODULAR)

call write_log_module( &
    EWTS_ID_NOAH_OWP_MODULAR, &
    "Initializing NOAHOWP BMI", &
    EWTS_INFO)
```

Initialize the module logger before the first log message. The BMI `Initialize`
routine is usually the best location.

## Submodule logger wrapper pattern

Most Fortran model submodules should not call EWTS directly throughout the model
code. Instead, each submodule should provide a small module-specific logger
wrapper that hides whether EWTS was compiled in.

The wrapper should:

- import EWTS only when the submodule was built with EWTS support
- expose the logging API expected by the submodule
- map local log-level names to EWTS levels when EWTS is enabled
- provide fallback log-level constants when EWTS is not enabled
- initialize EWTS once before the first forwarded log message
- forward standard log messages with `write_log_module(...)`
- forward payload messages with `payload_status(...)`
- make payload logging a no-op when EWTS is not enabled

A minimal wrapper structure is:

```fortran
module mymodel_log_module

#ifdef MYMODEL_USE_EWTS
  use logger, only: ewts_write_log_module => write_log_module, &
                    ewts_payload_status => payload_status, &
                    ewts_is_logger_enabled_module => is_logger_enabled_module, &
                    ewts_get_log_level_module => get_log_level_module, &
                    ewts_logger_init_module => logger_init_module, &
                    EWTS_NOTSET, EWTS_DEBUG, EWTS_PERFORM, EWTS_INFO, &
                    EWTS_WARNING, EWTS_SEVERE, EWTS_FATAL, EWTS_STATUS
  use ewts_module_constants, only: EWTS_ID_MYMODEL
#endif

  implicit none
  private

#ifdef MYMODEL_USE_EWTS
  integer, parameter, public :: NOTSET            = EWTS_NOTSET
  integer, parameter, public :: LOG_LEVEL_DEBUG   = EWTS_DEBUG
  integer, parameter, public :: LOG_LEVEL_PERFORM = EWTS_PERFORM
  integer, parameter, public :: LOG_LEVEL_INFO    = EWTS_INFO
  integer, parameter, public :: LOG_LEVEL_WARNING = EWTS_WARNING
  integer, parameter, public :: LOG_LEVEL_SEVERE  = EWTS_SEVERE
  integer, parameter, public :: LOG_LEVEL_FATAL   = EWTS_FATAL
  integer, parameter, public :: LOG_LEVEL_STATUS  = EWTS_STATUS
#else
  integer, parameter, public :: NOTSET            = 0
  integer, parameter, public :: LOG_LEVEL_DEBUG   = 10
  integer, parameter, public :: LOG_LEVEL_PERFORM = 15
  integer, parameter, public :: LOG_LEVEL_INFO    = 20
  integer, parameter, public :: LOG_LEVEL_WARNING = 30
  integer, parameter, public :: LOG_LEVEL_SEVERE  = 40
  integer, parameter, public :: LOG_LEVEL_FATAL   = 50
#endif

  public :: write_log
  public :: payload_status
  public :: is_logger_enabled
  public :: get_log_level

#ifdef MYMODEL_USE_EWTS
  logical, save :: did_init = .false.
#endif

contains

#ifdef MYMODEL_USE_EWTS
  subroutine ensure_init()
    if (.not. did_init) then
      call ewts_logger_init_module(EWTS_ID_MYMODEL)
      did_init = .true.
    end if
  end subroutine ensure_init
#endif

  subroutine write_log(message, level)
    character(len=*), intent(in) :: message
    integer, intent(in) :: level

#ifdef MYMODEL_USE_EWTS
    call ensure_init()
    call ewts_write_log_module(EWTS_ID_MYMODEL, trim(message), level)
#else
    write(*, '(A)') trim(message)
#endif
  end subroutine write_log

  subroutine payload_status(status, prog, msg, modnm)
    character(len=*), intent(in) :: status
    real(8), intent(in) :: prog
    character(len=*), intent(in) :: msg
    character(len=*), intent(in) :: modnm

#ifdef MYMODEL_USE_EWTS
    character(len=32) :: payload_modnm

    call ensure_init()

    if (len_trim(modnm) > 0) then
      payload_modnm = trim(modnm)
    else
      payload_modnm = EWTS_ID_MYMODEL
    end if

    call ewts_payload_status( &
        EWTS_ID_MYMODEL, &
        trim(status), &
        prog, &
        trim(msg), &
        trim(payload_modnm))
#else
    ! No payload support in fallback logger.
#endif
  end subroutine payload_status

  logical function is_logger_enabled()
#ifdef MYMODEL_USE_EWTS
    call ensure_init()
    is_logger_enabled = ewts_is_logger_enabled_module(EWTS_ID_MYMODEL)
#else
    is_logger_enabled = .true.
#endif
  end function is_logger_enabled

  integer function get_log_level()
#ifdef MYMODEL_USE_EWTS
    call ensure_init()
    get_log_level = ewts_get_log_level_module(EWTS_ID_MYMODEL)
#else
    get_log_level = LOG_LEVEL_INFO
#endif
  end function get_log_level

end module mymodel_log_module
```

The model code then uses only the local wrapper:

```fortran
use mymodel_log_module, only: write_log, payload_status, LOG_LEVEL_INFO

call write_log("Initializing model", LOG_LEVEL_INFO)

call payload_status( &
    "INITIALIZING", &
    0.1d0, &
    "Initializing model", &
    "")
```

This keeps the model source independent of the EWTS build option. When EWTS is
enabled, messages are forwarded to EWTS. When EWTS is not enabled, the wrapper
uses its fallback behavior.

## Payload logging

Payload messages use:

```fortran
call payload_status(ewts_id, status, prog, msg, modnm)
```

Arguments:

| Argument | Meaning |
|---|---|
| `ewts_id` | EWTS ID used in the payload log prefix |
| `status` | Payload status value, such as `INITIALIZING` or `IN_PROGRESS` |
| `prog` | Progress value, usually `0.0d0` through `1.0d0` |
| `msg` | Human-readable payload message |
| `modnm` | Module/component name written into the JSON payload |

When the `ngen` bridge is active, payload messages are written to the payload log
as STATUS records:

```text
2026-06-23T23:42:36.219Z NOAHOWP  STATUS  <MSG_DATA>{"status":"INITIALIZING","prog":0.1,"msg":"Initializing NOAHOWP BMI","modnm":"NOAHOWP"}</MSG_DATA>
```

Payload logs are an `ngen` integration feature. The Fortran runtime does not
write payload records in standalone mode.

## Environment configuration

| Variable | Purpose |
|---|---|
| `NGEN_RESULTS_DIR` | `ngen` results directory |
| `EWTS_ENABLED` | Enables or disables logging |
| `EWTS_LOG_LEVEL` | Default log level; INFO if undefined |
| `EWTS_RANK` | MPI rank exported by `ngen` |
| `<MODULE>_LOGLEVEL` | Per-module log level override |
| `EWTS_LOG_DIR` | Standalone log directory |

## Standalone behavior

Outside the `ngen` results environment, standard Fortran log messages are written
to the standalone EWTS log location. If the module provides its own wrapper
fallback and EWTS is not compiled in, fallback behavior is controlled by that
wrapper.

## CMake

A Fortran target using the EWTS runtime should link the Fortran runtime library:

```cmake
find_package(ewts CONFIG REQUIRED)

target_link_libraries(<target> PRIVATE ewts::ewts_fortran)
```

If the target should use the `ngen` bridge, also link the bridge and define the
bridge compile definition:

```cmake
target_link_libraries(<target> PRIVATE ewts::ewts_ngen_bridge)
target_compile_definitions(<target> PRIVATE EWTS_HAVE_NGEN_BRIDGE)
```

A submodule-specific wrapper usually also needs its own build flag, for example:

```cmake
target_compile_definitions(<target> PRIVATE MYMODEL_USE_EWTS)
```

That flag controls whether the wrapper imports EWTS or uses fallback behavior.

## Related documentation

- `runtime/c/README.md`
- `runtime/cpp/README.md`
- `runtime/python/README.md`
- `integrations/ngen/README.md`
