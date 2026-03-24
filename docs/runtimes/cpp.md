# C++ Runtime

The EWTS C++ runtime provides logging support for C++-based modules and shared
runtime execution.

## Typical use

A module typically binds a module ID and logs through the runtime logger API.
Under `ngen`, the integration layer owns final output policy, while the C++
runtime remains responsible for creating correctly attributed log messages.

## Shared-runtime behavior

The C++ runtime is designed so multiple modules can run in the same process
without colliding on logger identity. This is important for `ngen` execution,
where more than one module may log within the same runtime context.

## Common log levels

The C++ runtime uses the same canonical EWTS log levels as the other language-specific Runtime Libraries.

## Developer reference

For implementation details and repository-local usage, see:

- `runtime/cpp/README.md`
