# 1.0.27 June 23, 2019

Switch to putting the version number into `setup.py`. Not sure what the
issue is in reading it from `rpnpy/__init__.py`. See
https://github.com/terrycojones/rpnpy/issues/1

# 1.0.25 May 28, 2019

When a new function is defined (via `def`) and then used, it should be
executed (it was being pushed onto the stack, not run).

# 1.0.24 May 27, 2019

Removed extra `print` command. Updated README.

# 1.0.23 May 27, 2019

Added `map` as a special command. Updated README.

# 1.0.22 May 26, 2019

Make sure processing of stack items converts them all from `Variable` and
`Function` instances to the right thing for special commands. Added more
tests. Improved README.

# 1.0.21 May 26, 2019

Improved error handling / reporting. Added `--print` option to auto-print
results of operations.

# 1.0.20 May 24, 2019

Use new `findStringAndArgs` and `findCallableAndArgs` utility functions to
find strings (for `join`) and callables (for `map`, `apply`, etc) plus
their arguments on the stack

# 1.0.19 May 22, 2019

Added `join` special function and `:r` (reverse args) modifier, plus
tests. Updated README.

# 1.0.18 May 21, 2019

Make `rpn.py` execute the command line args if they are not all existing
files (or '-' to indicate stdin).  Added `--stdin` option to go with this
so that `stdin` is read after the command line is executed.

# 1.0.17 May 21, 2019

Improved error output. Updated README with function examples.

# 1.0.16 May 21, 2019

Added `count` processing to `dup`. Made debugging output more useful when
(perhaps) whitespace is in a command and line splitting is on. Stop
executing commands on a line if an error is encountered.

# 1.0.15 May 21, 2019

Added toggling of debug.

# 1.0.14 May 21, 2019

Updated README examples, added more debug printing.

# 1.0.13 May 21, 2019

Make `apply` examine the function it is about to run for its number of
arguments.

## 1.0.12 May 20, 2019

Tons of small improvements.

## 1.0.11 May 20, 2019

Updated README.md

## 1.0.10 May 19, 2019

Ongoing development. Many things added, rearranged, etc.

## 1.0.9 May 18, 2019

Refactored to use classes, added tests, added register function.

## 1.0.0 - 1.0.8

Unreleased hackery getting things more or less working.
