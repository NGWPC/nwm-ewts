! Auto-maintained EWTS Fortran integration config for module: sac-sma
!
! Provides:
!   - EWTS_ID parameter selecting the generated EWTS ID constant for this module.
!
! Usage:
!   use sac_sma_log_config, only: EWTS_ID
!   use ewts_logger

module sac_sma_log_config
  use ewts_module_constants, only: EWTS_ID_SAC_SMA
  implicit none
  public

  character(len=*), parameter :: EWTS_ID = EWTS_ID_SAC_SMA
end module sac_sma_log_config
