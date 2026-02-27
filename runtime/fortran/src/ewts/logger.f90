module logger
  use, intrinsic :: iso_c_binding, only: c_char, c_int, c_null_char
  implicit none
  private

  integer, parameter, public :: EWTS_NOTSET  = 0
  integer, parameter, public :: EWTS_DEBUG   = 10
  integer, parameter, public :: EWTS_PERFORM = 15
  integer, parameter, public :: EWTS_INFO    = 20
  integer, parameter, public :: EWTS_WARNING = 30
  integer, parameter, public :: EWTS_SEVERE  = 40
  integer, parameter, public :: EWTS_FATAL   = 50

  public :: write_log, is_logger_enabled, get_log_level
  public :: logger_init

  logical :: initialized = .false.
  logical :: enabled = .true.
  integer :: level_min = EWTS_INFO
  integer :: unit_log = -1
  character(len=1024) :: path = ""
  character(len=8) :: g_ewts_id = "UNKNOWN "   ! width matches your g_ewts_id width (8)
  
#ifdef EWTS_HAVE_NGEN_BRIDGE
  interface
    subroutine ewts_ngen_log(ewts_id, level, message) bind(C, name="ewts_ngen_log")
      import :: c_char, c_int
      character(kind=c_char), dimension(*) :: ewts_id
      integer(c_int), value :: level
      character(kind=c_char), dimension(*) :: message
    end subroutine
  end interface
#endif

contains

  subroutine logger_init(id)
    character(len=*), intent(in) :: id
    ! store as fixed-width 8 chars (pad/truncate)
    g_ewts_id = "        "
    g_ewts_id(1:min(len_trim(id),len(g_ewts_id))) = id(1:min(len_trim(id),len(g_ewts_id)))
  end subroutine logger_init

  subroutine upper_inplace(s)
    character(len=*), intent(inout) :: s
    integer :: i, c
    do i = 1, len(s)
      c = iachar(s(i:i))
      if (c >= iachar('a') .and. c <= iachar('z')) s(i:i) = achar(c - 32)
    end do
  end subroutine upper_inplace

  logical function is_ngen_active()
    integer :: lenv
    lenv = 0
    call get_environment_variable("NGEN_RESULTS_DIR", length=lenv)
    is_ngen_active = (lenv > 0)
  end function is_ngen_active

  logical function parse_enabled(v)
    character(len=*), intent(in) :: v
    character(len=32) :: s
    s = adjustl(trim(v))
    call upper_inplace(s)
    if (len_trim(s) == 0) then
      parse_enabled = .true.
    else if (trim(s) == "0" .or. trim(s) == "FALSE" .or. trim(s) == "NO" .or. trim(s) == "OFF" .or. trim(s) == "DISABLED") then
      parse_enabled = .false.
    else
      parse_enabled = .true.
    end if
  end function parse_enabled

  integer function parse_level(v)
    character(len=*), intent(in) :: v
    character(len=32) :: s
    integer :: iostat, num
    s = adjustl(trim(v))
    if (len_trim(s) == 0) then
      parse_level = EWTS_NOTSET
      return
    end if

    read(s, *, iostat=iostat) num
    if (iostat == 0 .and. num >= 0) then
      parse_level = num
      return
    end if

    call upper_inplace(s)
    select case (trim(s))
    case ("DEBUG");   parse_level = EWTS_DEBUG
    case ("PERFORM"); parse_level = EWTS_PERFORM
    case ("INFO");    parse_level = EWTS_INFO
    case ("WARN","WARNING"); parse_level = EWTS_WARNING
    case ("ERROR","SEVERE"); parse_level = EWTS_SEVERE
    case ("FATAL","CRITICAL"); parse_level = EWTS_FATAL
    case ("NOTSET","NONE"); parse_level = EWTS_NOTSET
    case default; parse_level = EWTS_NOTSET
    end select
  end function parse_level

  character(len=7) function level_name_padded(lvl)
    integer, intent(in) :: lvl
    select case (lvl)
    case (EWTS_DEBUG); level_name_padded = "DEBUG  "
    case (EWTS_PERFORM); level_name_padded = "PERFORM"
    case (EWTS_INFO); level_name_padded = "INFO   "
    case (EWTS_WARNING); level_name_padded = "WARNING"
    case (EWTS_SEVERE); level_name_padded = "SEVERE "
    case (EWTS_FATAL); level_name_padded = "FATAL  "
    case default; level_name_padded = "NOTSET "
    end select
  end function level_name_padded

  character(len=8) function ewts_id_padded()
    character(len=64) :: s
    integer :: n
    s = adjustl(trim(g_ewts_id))
    call upper_inplace(s)
    n = len_trim(s)
    if (n >= 8) then
      ewts_id_padded = s(1:8)
    else
      ewts_id_padded = s(1:n)//repeat(" ", 8-n)
    end if
  end function ewts_id_padded

  subroutine utc_timestamp_iso_ms(ts)
    character(len=*), intent(out) :: ts
    integer :: values(8)
    integer :: zone_min
    integer :: y, mo, d, h, mi, sec, ms
    call date_and_time(values=values)
    zone_min = values(4)
    y=values(1); mo=values(2); d=values(3)
    h=values(5); mi=values(6); sec=values(7); ms=values(8)
    call adjust_utc(y, mo, d, h, mi, zone_min)
    write(ts, "(I4.4,'-',I2.2,'-',I2.2,'T',I2.2,':',I2.2,':',I2.2,'.',I3.3,'Z')") y,mo,d,h,mi,sec,ms
  end subroutine utc_timestamp_iso_ms

  subroutine utc_timestamp_compact(ts)
    character(len=*), intent(out) :: ts
    integer :: values(8)
    integer :: zone_min
    integer :: y, mo, d, h, mi, sec
    call date_and_time(values=values)
    zone_min = values(4)
    y=values(1); mo=values(2); d=values(3)
    h=values(5); mi=values(6); sec=values(7)
    call adjust_utc(y, mo, d, h, mi, zone_min)
    write(ts, "(I4.4,I2.2,I2.2,'T',I2.2,I2.2,I2.2)") y,mo,d,h,mi,sec
  end subroutine utc_timestamp_compact

  subroutine adjust_utc(y, mo, d, h, mi, zone_min)
    integer, intent(inout) :: y, mo, d, h, mi
    integer, intent(in)    :: zone_min
    integer :: total_min
    total_min = h*60 + mi - zone_min
    do while (total_min < 0)
      total_min = total_min + 1440
      call dec_day(y, mo, d)
    end do
    do while (total_min >= 1440)
      total_min = total_min - 1440
      call inc_day(y, mo, d)
    end do
    h = total_min / 60
    mi = mod(total_min, 60)
  end subroutine adjust_utc

  subroutine inc_day(y, mo, d)
    integer, intent(inout) :: y, mo, d
    integer :: dim
    dim = days_in_month(y, mo)
    d = d + 1
    if (d > dim) then
      d = 1
      mo = mo + 1
      if (mo > 12) then
        mo = 1
        y = y + 1
      end if
    end if
  end subroutine inc_day

  subroutine dec_day(y, mo, d)
    integer, intent(inout) :: y, mo, d
    if (d > 1) then
      d = d - 1
    else
      mo = mo - 1
      if (mo < 1) then
        mo = 12
        y = y - 1
      end if
      d = days_in_month(y, mo)
    end if
  end subroutine dec_day

  integer function days_in_month(y, mo)
    integer, intent(in) :: y, mo
    logical :: leap
    leap = (mod(y,4) == 0 .and. (mod(y,100) /= 0 .or. mod(y,400) == 0))
    select case (mo)
    case (1,3,5,7,8,10,12); days_in_month = 31
    case (4,6,9,11); days_in_month = 30
    case (2); days_in_month = merge(29, 28, leap)
    case default; days_in_month = 30
    end select
  end function days_in_month

  function env_key() result(k)
    character(len=64) :: k
    character(len=64) :: s
    s = adjustl(trim(g_ewts_id))
    call upper_inplace(s)
    k = trim(s)//"_LOGLEVEL"
  end function env_key

  subroutine init_once()
    integer :: lenv
    character(len=256) :: v
    if (initialized) return
    initialized = .true.

    lenv = 0
    call get_environment_variable("EWTS_ENABLED", length=lenv)
    if (lenv > 0) then
      call get_environment_variable("EWTS_ENABLED", v)
      enabled = parse_enabled(v)
    else
      enabled = .true.
    end if

    if (trim(adjustl(g_ewts_id)) /= "UNKNOWN") then
      lenv = 0
      call get_environment_variable(trim(env_key()), length=lenv)
      if (lenv > 0) then
        call get_environment_variable(trim(env_key()), v)
        level_min = parse_level(v)
      else
        level_min = EWTS_NOTSET
      end if
    end if

    if (level_min == EWTS_NOTSET) then
      lenv = 0
      call get_environment_variable("EWTS_LOG_LEVEL", length=lenv)
      if (lenv > 0) then
        call get_environment_variable("EWTS_LOG_LEVEL", v)
        level_min = parse_level(v)
      else
        level_min = EWTS_INFO
      end if
      if (level_min == EWTS_NOTSET) level_min = EWTS_INFO
    end if
  end subroutine init_once

  logical function is_logger_enabled()
    call init_once()
    is_logger_enabled = enabled
  end function is_logger_enabled

  integer function get_log_level()
    call init_once()
    get_log_level = level_min
  end function get_log_level

  subroutine open_standalone_file()
    integer :: lenv, ios
    character(len=1024) :: dir
    character(len=15) :: ts
    if (unit_log > 0) return

    lenv = 0
    call get_environment_variable("EWTS_LOG_DIR", length=lenv)
    if (lenv > 0) then
      call get_environment_variable("EWTS_LOG_DIR", dir)
      dir = adjustl(trim(dir))
    else
      call get_environment_variable("HOME", length=lenv)
      if (lenv > 0) then
        call get_environment_variable("HOME", dir)
        dir = adjustl(trim(dir))//"/run_logs"
      else
        dir = "./run_logs"
      end if
    end if

    call execute_command_line("mkdir -p " // trim(dir), wait=.true.)
    call utc_timestamp_compact(ts)
    path = trim(dir)//"/"//trim(g_ewts_id)//"_"//ts//".log"

    open(newunit=unit_log, file=trim(path), status="unknown", position="append", action="write", iostat=ios)
    if (ios /= 0) unit_log = -1
  end subroutine open_standalone_file

  subroutine call_bridge(lvl, msg)
    use, intrinsic :: iso_c_binding, only: c_char, c_int, c_null_char
    integer, intent(in) :: lvl
    character(len=*), intent(in) :: msg
    character(kind=c_char), allocatable :: cid(:), cmsg(:)
    integer :: n1, n2, i

    n1 = len_trim(g_ewts_id)
    n2 = len_trim(msg)

    allocate(cid(n1+1))
    allocate(cmsg(n2+1))

    do i = 1, n1
      cid(i) = transfer(g_ewts_id(i:i), cid(i))
    end do
    cid(n1+1) = c_null_char

    do i = 1, n2
      cmsg(i) = transfer(msg(i:i), cmsg(i))
    end do
    cmsg(n2+1) = c_null_char

    call ewts_ngen_log(cid, int(lvl, c_int), cmsg)

    deallocate(cid, cmsg)
  end subroutine call_bridge

  subroutine write_log(lvl, msg)
    integer, intent(in) :: lvl
    character(len=*), intent(in) :: msg
    character(len=32) :: ts
    character(len=8) :: id8
    character(len=7) :: lv7

    call init_once()
    if (.not. enabled) return
    if (lvl < level_min) return

#ifdef EWTS_HAVE_NGEN_BRIDGE
    if (is_ngen_active()) then
      call call_bridge(lvl, msg)
      return
    end if
#endif

    call open_standalone_file()
    call utc_timestamp_iso_ms(ts)
    id8 = ewts_id_padded()
    lv7 = level_name_padded(lvl)

    if (unit_log > 0) then
      write(unit_log, "(A,' ',A,' ',A,' ',A)") trim(ts), id8, lv7, trim(msg)
      flush(unit_log)
    else
      write(*, "(A,' ',A,' ',A,' ',A)") trim(ts), id8, lv7, trim(msg)
    end if
  end subroutine write_log

end module logger
