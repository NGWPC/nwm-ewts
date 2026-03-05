# EWTS Python Runtime

The EWTS Python runtime mirrors the functionality of the C/C++/Fortran
runtimes.

## Install (Editable)

pip install -e runtime/python/ewts

## Build Distribution

python -m build runtime/python/ewts

## Usage

import ewts

ewts.init("CFE") ewts.log("INFO", "Hello world")
