cmake_minimum_required(VERSION 3.20)
project(ewts LANGUAGES C CXX Fortran)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

option(EWTS_BUILD_C       "Build EWTS C runtime"       ON)
option(EWTS_BUILD_CPP     "Build EWTS C++ runtime"     ON)
option(EWTS_BUILD_FORTRAN "Build EWTS Fortran runtime" ON)
option(EWTS_WITH_NGEN     "Build EWTS ngen bridge"     OFF)
option(EWTS_BUILD_SHARED  "Build shared libs"          ON)

# ----- Install Fortran config sources (your preferred approach) -----
# These are the per-module *_log_config.f90 files that export EWTS_ID.
set(EWTS_FORTRAN_CONFIG_INSTALL_DIR "${CMAKE_INSTALL_DATADIR}/ewts/fortran/config")

install(
  DIRECTORY "${CMAKE_CURRENT_LIST_DIR}/../integrations/modules/fortran/"
  DESTINATION "${EWTS_FORTRAN_CONFIG_INSTALL_DIR}"
  FILES_MATCHING PATTERN "*_log_config.f90"
)

# Provide this path to consumers via the package config file.
set(EWTS_FORTRAN_CONFIG_DIR "\${PACKAGE_PREFIX_DIR}/${EWTS_FORTRAN_CONFIG_INSTALL_DIR}")

# ----- Targets -----
if(EWTS_BUILD_C)
  add_subdirectory(c)
endif()

if(EWTS_BUILD_CPP)
  add_subdirectory(cpp)
endif()

if(EWTS_BUILD_FORTRAN)
  add_subdirectory(fortran)
endif()

if(EWTS_WITH_NGEN)
  add_subdirectory(../integrations/ngen integrations_ngen_build)
endif()

# ----- Package export -----
# Collect and export targets created in subdirectories.
install(EXPORT ewtsTargets
  NAMESPACE ewts::
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ewts"
)

configure_package_config_file(
  "${CMAKE_CURRENT_LIST_DIR}/cmake/ewtsConfig.cmake.in"
  "${CMAKE_CURRENT_BINARY_DIR}/ewtsConfig.cmake"
  INSTALL_DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ewts"
)

write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/ewtsConfigVersion.cmake"
  VERSION 0.1.0
  COMPATIBILITY SameMajorVersion
)

install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/ewtsConfig.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/ewtsConfigVersion.cmake"
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ewts"
)
