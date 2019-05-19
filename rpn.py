#!/usr/bin/env python

from __future__ import print_function

import sys
import os
import readline
import argparse

from rpnpy import Calculator


def setupReadline():
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


def parseArgs():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'An RPN calculator for Python. Reads commands from standard input '
            'or interactively with a read-eval-print loop and (optionally) '
            'writes the final stack to standard output.'))

    parser.add_argument(
        '--prompt', default='--> ',
        help='The prompt to print at the start of each line when interactive.')

    parser.add_argument(
        '--separator',
        help=('The character to use to split lines of standard input into '
              'separate commands (unless --noSplit is given).'))

    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='Print verbose information about how commandsa are run.')

    parser.add_argument(
        '--version', action='store_true', default=False,
        help='Print the version number and exit.')

    parser.add_argument(
        '--noSplit', action='store_false', default=True, dest='splitLines',
        help=('If given, do not split lines read from standard input into '
              'separate commands, treat each line as an entire command.'))

    parser.add_argument(
        '--noPrint', action='store_false', default=True, dest='print',
        help=('If given, do not print the stack after processing all commands '
              'from standard input.'))

    return parser.parse_args()


def stdin(calc, print_):
    """
    Read and execute commands from stdin.

    @param calc: A C{Calculator} instance.
    @param print_: If C{True}, print the stack after all commands are run.
    """
    for line in sys.stdin:
        try:
            calc.execute(line)
        except EOFError:
            break
    if print_ and calc.stack:
        calc.printStack(-1 if len(calc) == 1 else None)


def repl(calc, prompt):
    """
    Interactive read-eval-print loop.

    @param calc: A C{Calculator} instance.
    @param prompt: The C{str} prompt to print at the start of each line.
    """
    while True:
        try:
            calc.execute(input(prompt))
        except KeyboardInterrupt:
            print()
        except EOFError:
            break


if __name__ == '__main__':
    args = parseArgs()

    if args.version:
        from rpnpy import __version__
        print(__version__)
    else:
        setupReadline()
        calc = Calculator(splitLines=args.splitLines, separator=args.separator,
                          debug=args.debug)

        if os.isatty(0):
            repl(calc, args.prompt)
        else:
            stdin(calc, args.print)
