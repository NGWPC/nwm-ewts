## Addressing Prior Logging Limitations

EWTS has been redesigned to address limitations observed in earlier logging
implementations, particularly in multi-language and parallel execution
environments.

### Safe and Configurable File Handling

Logging output is no longer tied to a single hardcoded path. Instead, EWTS
selects log locations based on the execution environment. When running under
`ngen`, log output is routed using integration-aware locations such as the
`ngen` results directory, currently defined by an enviroment variable. In 
standalone mode, EWTS also uses an enviroment variable when set, otherwise
falls back to user-scoped locations such as `$HOME/run_logs`. This provides
safer and more portable behavior across standalone, scheduled, and integrated
execution environments.

### Thread-Safe and Process-Safe Design

Previous implementations relied on global, unguarded buffers and shared state.
EWTS eliminates these patterns by:

- avoiding global mutable buffers
- using well-defined, scoped logging interfaces
- ensuring safe behavior across threads and processes

This prevents segmentation faults and undefined behavior caused by unsafe memory usage.

### Reliable String Handling

String construction and formatting are handled safely within each language-specific
Runtime Library, avoiding unsafe concatenation patterns and shared string state.
This ensures consistent and stable log message construction across all supported
languages.

### MPI-Aware Logging

EWTS is designed for parallel execution:

- each MPI rank writes to its own log file
- shared file writes are avoided
- log output remains deterministic and non-interleaved

This eliminates file I/O collisions and issues observed on distributed file systems
such as Lustre.

### Consistent and Robust Python Integration

The Python Runtime Library uses standard logging patterns and avoids overriding
core logging configuration in unsafe ways. Logging handlers are properly
initialized and attached, and file handling is managed to prevent descriptor leaks
and runtime errors.

### Centralized and Reusable Logging Behavior

Logging functionality is implemented once within the Runtime Libraries and reused
across modules and workflow components. This:

- eliminates duplicated logging implementations
- ensures consistent behavior across languages
- simplifies maintenance and future enhancements

---

Together, these improvements provide a robust, scalable, and maintainable logging
framework suitable for both standalone execution and complex, distributed workflows.
