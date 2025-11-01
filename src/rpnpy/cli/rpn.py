#!/usr/bin/env python

import argparse
import os
import sys
from io import StringIO

from textual.theme import BUILTIN_THEMES

from rpnpy import Calculator, __version__
from rpnpy.utils import interactive

DEFAULT_THEME = "nord"


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            "An RPN calculator for Python that reads commands from some combination of "
            "standard input, command line arguments, files, or interactively. When "
            "run non-interactively, the final stack is (normally) printed to standard "
            "output before exiting. Use --help for more details."
        ),
    )

    parser.add_argument(
        "--prompt",
        default="--> ",
        help="The prompt to print at the start of each line when interactive.",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "Files to read input from. If you use this option and you also "
            "want standard input to also be read at some point, use '-' as a "
            "name in the list of file names."
        ),
    )

    parser.add_argument(
        "--separator",
        metavar="CHAR",
        help=(
            "The character to use to split lines of standard input into "
            "separate commands (unless --noSplit is given)."
        ),
    )

    parser.add_argument(
        "--noColor",
        action="store_false",
        dest="color",
        help="Do not color interactive output.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print verbose information about how commands are run.",
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print the result of each command.",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the version number and exit.",
    )

    parser.add_argument(
        "--noSplit",
        action="store_false",
        dest="splitLines",
        help=(
            "Do not split lines read from standard input into "
            "separate commands, treat each line as an entire command."
        ),
    )

    parser.add_argument(
        "--noFinalPrint",
        action="store_false",
        dest="finalPrint",
        help=(
            "Do not print the stack after processing all commands from standard input."
        ),
    )

    parser.add_argument(
        "--stdin",
        action="store_true",
        help=(
            "If arguments on the command line are passed as input to "
            "the calculator, you can use this option to additionally read commands "
            "from standard input once the command line has been executed."
        ),
    )

    parser.add_argument(
        "--startupFile",
        metavar="FILE",
        help=(
            "A Python file to be executed at startup. This can be used to define "
            "custom functions and variables. Defaults to "
            f"{Calculator.DEFAULT_STARTUP_FILE!r} in the "
            f"{Calculator.DEFAULT_CONFIG_DIR!r} directory in your home directory."
        ),
    )

    parser.add_argument(
        "--noStartup",
        action="store_true",
        help="Do not load the start-up file.",
    )

    parser.add_argument(
        "--historyFile",
        metavar="FILE",
        help=(
            f"A file to read/write to maintain rpnpy command history. Defaults to "
            f"{Calculator.DEFAULT_HISTORY_FILE!r} in the "
            f"{Calculator.DEFAULT_CONFIG_DIR!r} directory in your home directory."
        ),
    )

    parser.add_argument(
        "--noHistory",
        action="store_true",
        help="Do not read or write the readline history file.",
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch the Terminal User Interface (TUI) mode.",
    )

    parser.add_argument(
        "--theme",
        metavar="THEME",
        default=DEFAULT_THEME,
        choices=tuple(sorted(BUILTIN_THEMES)),
        help=(
            "Textual theme to use for TUI mode. Note that if you use this to select a "
            "non-default theme, --tui will be implied. Choices are: "
            + ", ".join(sorted(BUILTIN_THEMES))
        ),
    )

    parser.add_argument(
        "--listThemes",
        action="store_true",
        help="List available Textual themes (for use with --tui) and exit.",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the rpnpy CLI."""
    args = parseArgs()

    if args.version:
        print(__version__)
        sys.exit(0)

    interact = interactive()

    # Set TUI mode if a theme has been given. This is not foolproof, because --tui will
    # be needed if you want to use the TUI with the default theme.
    if args.theme != DEFAULT_THEME:
        args.tui = True

    # For TUI mode, disable color so we can capture error messages properly
    # and always use splitLines=False. Also create error buffer for TUI.
    if args.tui:
        color = splitLines = False
        errorBuffer = StringIO()
    else:
        color = args.color and interact
        splitLines = args.splitLines
        errorBuffer = sys.stderr

    calc = Calculator(
        autoPrint=args.print,
        splitLines=splitLines,
        separator=args.separator,
        color=color,
        debug=args.debug,
        errfp=errorBuffer,
        startupFile=args.startupFile,
        noStartup=args.noStartup,
        historyFile=args.historyFile,
        noHistory=args.noHistory,
    )

    if args.tui:
        from rpnpy.tui import run_tui

        run_tui(calc, errorBuffer, theme=args.theme)
        return

    if args.files:
        if all(os.path.exists(f) or f == "-" for f in args.files):
            # All arguments are existing files (or are '-', for stdin).
            for filename in args.files:
                if filename == "-":
                    calc.repl(args.prompt)
                else:
                    with open(filename) as fp:
                        calc.batch(fp, False)
        else:
            # Execute the command line as a set of commands, following
            # great suggestion by David Pattinson.
            calc.batch((" ".join(args.files),), args.finalPrint)
            if args.stdin:
                calc.repl(args.prompt)

    elif interact:
        calc.repl(args.prompt)

    else:
        calc.batch(sys.stdin, args.finalPrint)


if __name__ == "__main__":
    main()
