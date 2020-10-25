#!/usr/bin/env python

from __future__ import print_function

import sys
import os
import readline
import argparse

from rpnpy import Calculator


def setupReadline():
    """Initialize the readline library and command history.

    @return: A C{bool} to indicate whether standard input is a terminal
        (and therefore interactive).
    """
    if not os.isatty(0):
        # Standard input is closed or is a pipe etc. So there's no user
        # typing at us, and so no point in setting up readline.
        return False

    # Readline code from https://docs.python.org/3.7/library/readline.html
    histfile = os.path.join(os.path.expanduser('~'), '.pycalc_history')

    try:
        readline.read_history_file(histfile)
        historyLen = readline.get_current_history_length()
    except FileNotFoundError:
        open(histfile, 'wb').close()
        historyLen = 0

    try:
        readline.append_history_file
    except AttributeError:
        # We won't be able to save readline history. This can happen on
        # Python 3.5 at least - not sure why.
        pass
    else:
        import atexit

        def saveHistory(prevHistoryLen, histfile):
            newHistoryLen = readline.get_current_history_length()
            readline.set_history_length(1000)
            readline.append_history_file(newHistoryLen - prevHistoryLen,
                                         histfile)

        atexit.register(saveHistory, historyLen, histfile)

    return True


def parseArgs():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'An RPN calculator for Python. Reads commands from standard input '
            'and/or files or interactively with a read-eval-print loop and '
            '(optionally) writes the final stack to standard output.'))

    parser.add_argument(
        '--prompt', default='--> ',
        help='The prompt to print at the start of each line when interactive.')

    parser.add_argument(
        'files', nargs='*',
        help=('Files to read input from. If you use this option and you also '
              'want standard input to be read at some point, use "-" as a '
              'name in the list of file names.'))

    parser.add_argument(
        '--separator',
        help=('The character to use to split lines of standard input into '
              'separate commands (unless --noSplit is given).'))

    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='Print verbose information about how commandsa are run.')

    parser.add_argument(
        '--print', action='store_true', default=False,
        help='Print the result of each command')

    parser.add_argument(
        '--version', action='store_true', default=False,
        help='Print the version number and exit.')

    parser.add_argument(
        '--noSplit', action='store_false', default=True, dest='splitLines',
        help=('If given, do not split lines read from standard input into '
              'separate commands, treat each line as an entire command.'))

    parser.add_argument(
        '--noFinalPrint', action='store_false', default=True,
        dest='finalPrint',
        help=('If given, do not print the stack after processing all commands '
              'from standard input.'))

    parser.add_argument(
        '--stdin', action='store_true', default=False,
        help=('If the arguments on the command line are passed as input to '
              'the calculator, you can use this option to also read commands '
              'from standard input once the command line has been executed.'))

    parser.add_argument(
        '--startupFile',
        help=('Python file to be parsed at startup. Usually used to define '
              'custom functions'))

    return parser.parse_args()


if __name__ == '__main__':
    args = parseArgs()

    if args.version:
        from rpnpy import __version__
        print(__version__)
    else:
        calc = Calculator(autoPrint=args.print, splitLines=args.splitLines,
                          separator=args.separator, debug=args.debug)

        if args.startupFile:
            try:
                with open(args.startupFile) as f:
                    exec(f.read(), globals(), calc._variables)
            except FileNotFoundError:
                calc.err('Startup file %s not found' % args.startupFile)

        interactive = setupReadline()

        if args.files:
            if all(os.path.exists(f) or f == '-' for f in args.files):
                # All arguments are existing files (or are '-', for stdin).
                for filename in args.files:
                    if filename == '-':
                        calc.repl(args.prompt)
                    else:
                        with open(filename) as fp:
                            calc.batch(fp, False)
            else:
                # Execute the command line as a set of commands, following
                # great suggestion by David Pattinson.
                calc.batch((' '.join(args.files),), args.finalPrint)
                if args.stdin:
                    calc.repl(args.prompt)
        elif interactive:
            calc.repl(args.prompt)
        else:
            calc.batch(sys.stdin, args.finalPrint)
