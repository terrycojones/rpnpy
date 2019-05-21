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
