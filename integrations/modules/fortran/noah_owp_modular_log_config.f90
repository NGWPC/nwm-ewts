! Auto-maintained EWTS Fortran integration config for module: noah-owp-modular
!
! Provides:
!   - EWTS_ID parameter selecting the generated EWTS ID constant for this module.
!
! Usage:
!   use noah_owp_modular_log_config, only: EWTS_ID
!   use ewts_logger

module noah_owp_modular_log_config
  use ewts_module_constants, only: EWTS_ID_NOAH_OWP_MODULAR
  implicit none
  public

  character(len=*), parameter :: EWTS_ID = EWTS_ID_NOAH_OWP_MODULAR
end module noah_owp_modular_log_config
