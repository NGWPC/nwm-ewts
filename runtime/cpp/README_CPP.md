# EWTS C++ Runtime

The EWTS C++ runtime provides:

-   `void ewts::EwtsInit(std::string_view ewts_id);`
-   `void ewts::Log(LogLevel level, std::string_view message);`
-   `void ewts::Logf(LogLevel level, const char* fmt, ...);`

## Build

Built via the root CMake configuration:

cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release cmake --build build
-j

## Features

-   std::call_once initialization
-   std::filesystem directory handling
-   Optional NGEN integration
