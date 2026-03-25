# C++ Runtime Library

The EWTS C++ library provides logging support for C++-based hydrologic
modules running either within `ngen` or as standalone applications.

## Typical use

A module typically binds a module ID and logs through the runtime logger API.
Under `ngen`, the integration layer owns final output policy, while the C++
runtime remains responsible for creating correctly attributed log messages.

```cpp
#ifndef SFT_LOGGER_HPP
#define SFT_LOGGER_HPP

#include "ewts/module_constants.hpp"

// Provide the constant in the global namespace
inline constexpr const char* EWTS_ID_SFT = ewts::modules::EWTS_ID_SFT;

// Bind this module's logger identity
#define EWTS_ID EWTS_ID_SFT

#include "ewts/logger.hpp"

using ewts::EwtsInit;
using ewts::LogLevel;

#endif /* SFT_LOGGER_HPP */
```

```cpp
void BmiSoilFreezeThaw::
Initialize (std::string config_file)
{
  // Initialize the Error, Warning and Trapping System
#ifdef EWTS_HAVE_NGEN_BRIDGE    
  EwtsInit(EWTS_ID_SFT, true);
#else
  EwtsInit(EWTS_ID_SFT, false);
#endif
  LOG(LogLevel::INFO, "Initializing SFT");

  if (config_file.compare("") != 0 )
      this->state = new soilfreezethaw::SoilFreezeThaw(config_file);

    verbosity= this->state->verbosity;
}
```

## Shared-runtime behavior

The C++ runtime library is designed so multiple modules can run in the same process
without colliding on logger identity. This is important for `ngen` execution,
where more than one module may log within the same runtime context.

## Common log levels

The C++ runtime uses the same canonical EWTS log levels as the other language-specific Runtime Libraries.

## Developer reference

For implementation details and repository-local usage, see:

- `runtime/cpp/README.md`
