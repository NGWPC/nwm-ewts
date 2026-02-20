! Auto-maintained EWTS Fortran integration config for module: snow17
!
! Provides:
!   - EWTS_ID parameter selecting the generated EWTS ID constant for this module.
!
! Usage:
!   use snow17_log_config, only: EWTS_ID
!   use ewts_logger

module snow17_log_config
  use ewts_module_constants, only: EWTS_ID_SNOW17
  implicit none
  public

  character(len=*), parameter :: EWTS_ID = EWTS_ID_SNOW17
end module snow17_log_config
