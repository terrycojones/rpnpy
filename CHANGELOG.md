# 3.0.11 November 1, 2025

Updated `pyproject.toml` keywords.

# 3.0.10 November 1, 2025

Updated `pyproject.toml`.

# 3.0.9 November 1, 2025

Make it so tests of the calculator do not try to read the start-up or readline
history files.

# 3.0.8 November 1, 2025

Various admin iterations with claude CLI to make `bump-my-version` work,
including committing `uv.lock`.

# 3.0.2 November 1, 2025

Minor simplifications of Claude code in tui.py.

# 3.0.1 November 1, 2025

Updated README.

# 3.0.0 November 1, 2025

Fix reading of start-up file so imported modules work and newly-defined
functions are interrogated and registered so they can automatically be given
the correct number of arguments from the stack. Make calculator do the work
of reading the start-up and history files instead of having it in `rpn.py`.
Changed the default location of the history to '~/.rpnpy/history'. Added a
default startup file location, '~/.rpnpy/startup.py'. Removed Python 3.8
typing hints.

# 2.4.2 October 31, 2025

Improved button positioning and coloring.

# 2.4.1 November 31, 2025

Improved speed at which button click events can be handled.

# 2.4.0 November 31, 2025

Added a TUI (terminal UI). Invoke it with `--tui` and set your theme via
`--theme`. Use `--list-themes` to see theme names.

# 2.3.0 October 31, 2025

Added colored (when interactive) output. Disable with `--noColor`.

# 2.2.3 October 31, 2025

Various small/cosmetic changes. Added 'self' as a variable, for fun.

# 2.2.2 October 31, 2025

Minor changes to `--help` text.

# 2.2.1 October 30, 2025

Added (Python 3.8+ compatible) typing hints.

# 2.2.0 October 30, 2025

Add `version` command.

# 2.1.1 October 30, 2025

Small cleanups from `ruff`.

# 2.1.0 October 30, 2025

Added `v` (square root) abbreviation, to match `dc`.

# 2.0.1 October 30, 2025

Use `gnureadline` when possible to work around annoying OS X `readline`
incompatibility that was producing cryptic `OSError` (errno 22) errors
when calling `readline.read_history_file`.

# 2.0.0 October 30, 2025

Modernized to use `uv` and `pyproject.toml`. The `rpn.py` script is now in
`src/rpnpy/cli/rpn.py` and can be run from the top level by `uv run rpypy`.
The package now installs an `rpypy` command. You can also run the calculator
without installing anything, via `uvx rpnpy`.

If you can't live without the old `rpn.py` command, things should work if you
make a symbolic link to `src/rpnpy/cli/rpn.py` (or put `src/rpnpy/cli` in
your shell's PATH).

# 1.0.31 December 2, 2020

Added special `store` command to save stack values into a variable,
following suggestion from @nfraprado.

# 1.0.30 October 26, 2020

Added support for engineering notation for numbers by using the
`engineering_notation` python package. It is now a dependency of `rpnpy`. (by
@nfraprado)

# 1.0.29 October 24, 2020

Added support for passing a python file to be parsed at startup through the
`--startupFile` flag. Fixed a bug with argument counting for user
functions. (Both by @nfraprado)

# 1.0.28 June 23, 2019

Added `packages` to `setup.py`, maybe thereby fixing
https://github.com/terrycojones/rpnpy/issues/1

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
