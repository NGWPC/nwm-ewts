#
# nwm-ewts/CMakeLists.txt
#

cmake_minimum_required(VERSION 3.20)

# Top-level build that includes EWTS runtime
#
# Build example (same knobs as before, now from repo root):
#   cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DEWTS_WITH_NGEN=ON -DEWTS_BUILD_SHARED=OFF
#   cmake --build build -j
#   cmake --install build --prefix /tmp/ewts_install
#
project(ewts-superbuild LANGUAGES C CXX Fortran)

# Build/install/export the core runtime libraries + package config.
add_subdirectory(runtime)
