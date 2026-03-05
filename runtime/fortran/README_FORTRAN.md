# EWTS Fortran Runtime

The EWTS Fortran runtime provides logging bindings compatible with the C
runtime.

## Build

cmake -B build -S runtime -DCMAKE_BUILD_TYPE=Release cmake --build build
-j

## Notes

-   Built as free-form Fortran
-   Module files (.mod) are installed under include/ewts/fortran
-   Environment-driven log level control
