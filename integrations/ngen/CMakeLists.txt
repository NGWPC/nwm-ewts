add_library(ewts_ngen_bridge
  src/ewts_ngen/ewts_ngen_bridge.cpp
  src/ewts_ngen/logger.cpp
)

target_include_directories(ewts_ngen_bridge
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_LIST_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_compile_features(ewts_ngen_bridge PUBLIC cxx_std_17)
set_target_properties(ewts_ngen_bridge PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_library(ewts::ngen_bridge ALIAS ewts_ngen_bridge)

install(TARGETS ewts_ngen_bridge
  EXPORT ewtsTargets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
