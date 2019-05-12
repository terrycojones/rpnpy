#!/usr/bin/env python

import sys
import os
import math
import builtins
import operator
import functools
import inspect
import re
from ast import literal_eval
from pprint import pprint
import readline

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
    # Can't save readline history. Oh well.
    pass
else:
    import atexit

    def saveHistory(prevHistoryLen, histfile):
        newHistoryLen = readline.get_current_history_length()
        readline.set_history_length(1000)
        readline.append_history_file(newHistoryLen - prevHistoryLen, histfile)

    atexit.register(saveHistory, historyLen, histfile)


functions = {}
variables = {}

NUMBER_RE = re.compile(r'(\d+)')


class Function:
    def __init__(self, moduleName, name, func, nArgs):
        self.moduleName = moduleName
        self.name = name
        self.func = func
        self.nArgs = nArgs

    def __call__(self, *args, **kw):
        return self.func(*args, **kw)

    def __repr__(self):
        return 'Function(%s (calls %s with %d args))' % (
            self.name, self.path, self.nArgs)

    @property
    def path(self):
        return '%s.%s' % (self.moduleName, self.name)


class Variable:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Variable(%s, current value: %r)' % (
            self.name, variables[self.name])


def addAbbrevs():
    for longName, shortNames in (
            ('math.gcd', ('gcd',)),
            ('math.log', ('log',)),
            ('math.log10', ('log10',)),
            ('math.sqrt', ('sqrt',)),
            ('operator.abs', ('abs',)),
            ('operator.add', ('+', 'add')),
            ('operator.eq', ('=', 'eq')),
            ('operator.mul', ('*', 'mul')),
            ('operator.ne', ('ne',)),
            ('operator.neg', ('neg',)),
            ('operator.pow', ('pow',)),
            ('operator.sub', ('-', 'sub')),
            ('operator.truediv', ('/', 'div')),
            ('builtins.any', ('any',)),
            ('builtins.all', ('all',)),
            ('builtins.bool', ('bool',)),
            ('builtins.hex', ('hex',)),
            ('builtins.int', ('int',)),
            ('builtins.len', ('len',)),
            ('builtins.list', ('list',)),
            ('builtins.map', ('map',)),
            ('builtins.max', ('max',)),
            ('builtins.min', ('min',)),
            ('builtins.oct', ('oct',)),
            ('builtins.print', ('print',)),
            ('builtins.range', ('range',)),
            ('builtins.str', ('str',)),
            ('builtins.ord', ('ord',)),
            ('builtins.reversed', ('reversed',)),
            ('builtins.sorted', ('sorted',)),
            ('builtins.sum', ('sum',)),
            ('functools.reduce', ('reduce',)),
    ):
        try:
            function = functions[longName]
        except KeyError:
            print('Long function name %r is unknown' % longName,
                  file=sys.stderr)
        else:
            for shortName in shortNames:
                if shortName not in functions:
                    # print('Long name %r alias %r' % (longName, shortName),
                    # file=sys.stderr)
                    functions[shortName] = function


def addSpecialCases():
    for module, func, nArgs in (
            (math, math.log, 1),
            (builtins, builtins.bool, 1),
            (builtins, builtins.int, 1),
            (builtins, builtins.map, 2),
            (builtins, builtins.max, 1),
            (builtins, builtins.min, 1),
            (builtins, builtins.print, 1),
            (builtins, builtins.str, 1),
            (builtins, builtins.range, 1),
            (functools, functools.reduce, 2),
    ):
        longName = '%s.%s' % (module.__name__, func.__name__)
        try:
            functions[longName]
        except KeyError:
            functions[longName] = Function(
                module.__name__, func.__name__, func, nArgs)
        else:
            print('Long function name %r is already set' % longName,
                  file=sys.stderr)


def addVariables():
    for name, value in (
            ('e', math.e),
            ('inf', math.inf),
            ('nan', math.nan),
            ('pi', math.pi),
            # ('tau', math.tau),  tau was only introduced in Python 3.6
            ):
        if name in variables:
            print('%r is already a variable!' % name, file=sys.stderr)
        else:
            variables[name] = value


def importCallables(module):
    moduleName = module.__name__
    exec('import ' + moduleName)
    callables = inspect.getmembers(module, callable)

    for name, func in callables:
        if name.startswith('__'):
            continue

        try:
            if issubclass(func, BaseException):
                continue
        except TypeError:
            pass

        path = '%s.%s' % (moduleName, name)
        try:
            sig = inspect.signature(func)
        except ValueError:
            # print('Could not get signature for', path, file=sys.stderr)
            pass
        else:
            nArgs = len([p for p in sig.parameters.values() if
                         p.kind == inspect.Parameter.POSITIONAL_ONLY])
            # or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD])
            exec('functions["%s"] = Function("%s", "%s", %s, %d)' % (
                path, moduleName, name, path, nArgs))


def splitInput(inputLine):
    fields = inputLine.rsplit('/', 1)
    try:
        command, modifiers = fields
    except ValueError:
        command = inputLine
        modifiers = ''
    else:
        # Special case a lone / on a line, which indicates division, not an
        # empty command with no modifiers.
        if not command and not modifiers:
            command = '/'

    match = NUMBER_RE.search(modifiers)
    if match:
        count = int(match.group(1))
        modifiers = modifiers[:match.start(1)] + modifiers[match.end(1):]
    else:
        count = None

    return command.strip().lower(), set(modifiers.strip().lower()), count


class Calculation:
    def __init__(self):
        self.stack = []
        self.previousStack = self.previousVariables = None

    def printStack(self, n=None):
        if n is None:
            pprint(self.stack)
        else:
            try:
                pprint(self.stack[n])
            except IndexError:
                print('Cannot print stack item %d (stack contains only '
                      '%d item%s)' %
                      (n, len(self.stack),
                       '' if len(self.stack) == 1 else 's'), file=sys.stderr)

    def saveState(self):
        self.previousStack = self.stack.copy()
        self.previousVariables = variables.copy()

    def do(self, command):

        global variables

        command, modifiers, count = splitInput(command)

        if not command:
            # print('Empty command')
            return

        push_ = '!' in modifiers
        list_ = 'l' in modifiers
        forceCommand = 'c' in modifiers
        preserveStack = '=' in modifiers
        iterate = 'i' in modifiers

        try:
            function = functions[command]
        except KeyError:
            try:
                value = literal_eval(command)
            except (ValueError, SyntaxError):

                if command in variables and not forceCommand:
                    self.saveState()
                    if push_:
                        self.stack.append(Variable(command))
                    else:
                        self.stack.append(variables[command])
                elif command == 'quit' or command == 'q':
                    raise EOFError()
                elif command == 'pop':
                    if self.stack:
                        self.saveState()
                        self.stack.pop()
                    else:
                        print('Cannot pop (stack is empty)', file=sys.stderr)
                elif command == 'functions':
                    for name, func in sorted(functions.items()):
                        print(func)
                elif command == 'stack' or command == 's' or command == 'f':
                    self.printStack()
                elif command == 'clear' or command == 'c':
                    self.saveState()
                    self.stack = []
                elif command == 'dup' or command == 'd':
                    if self.stack:
                        self.saveState()
                        self.stack.append(self.stack[-1])
                    else:
                        print('Cannot duplicate (stack is empty)',
                              file=sys.stderr)
                elif command == 'undo' or command == 'u':
                    if self.previousStack is None:
                        print('Nothing to undo.', file=sys.stderr)
                    else:
                        self.stack = self.previousStack.copy()
                        variables = self.previousVariables.copy()
                elif command == 'print' or command == 'p':
                    self.printStack(-1)
                elif command == 'none':
                    self.saveState()
                    self.stack.append(None)
                elif command == 'true':
                    self.saveState()
                    self.stack.append(True)
                elif command == 'false':
                    self.saveState()
                    self.stack.append(False)
                else:
                    # print('exec', command)
                    currentVars = set(variables)
                    self.saveState()
                    try:
                        exec(command, globals(), variables)
                    except Exception as e:
                        print('Exception: %s' % e, file=sys.stderr)
                        variables = self.previousVariables
                        self.stack = self.previousStack
                    else:
                        self.saveState()
                        for variable in set(variables) - currentVars:
                            if push_:
                                self.stack.append(Variable(variable))
                            else:
                                if iterate:
                                    for i in variables[variable]:
                                        self.stack.append(i)
                                else:
                                    self.stack.append(variables[variable])
            else:
                if list_:
                    value = list(value)
                self.saveState()
                if iterate:
                    for i in value:
                        self.stack.append(i)
                else:
                    self.stack.append(value)
        else:
            if count is None:
                if '*' in modifiers:
                    nArgs = len(self.stack)
                else:
                    nArgs = function.nArgs
            else:
                nArgs = int(count)
                if '*' in modifiers:
                    if len(self.stack) != nArgs:
                        print('/modifiers cannot contain both a count and a *',
                              file=sys.stderr)
                        return

            if push_:
                self.saveState()
                self.stack.append(function.func)
            elif len(self.stack) < function.nArgs:
                print('Not enough args on stack! (%s needs %d arg%s, stack '
                      'has %d item%s)' %
                      (command, nArgs, '' if nArgs == 1 else 's',
                       len(self.stack), '' if len(self.stack) == 1 else 's'),
                      file=sys.stderr)
            else:
                args = []
                for arg in self.stack[-nArgs:]:
                    if isinstance(arg, Function):
                        args.append(arg.func)
                    elif isinstance(arg, Variable):
                        args.append(variables[arg.name])
                    else:
                        args.append(arg)

                self.saveState()
                if not preserveStack:
                    self.stack = self.stack[:-nArgs]
                try:
                    # print('Calling', function.name, 'with', tuple(args))
                    result = function.func(*args)
                except Exception as e:
                    print('Exception:', e, file=sys.stderr)
                    variables = self.previousVariables
                    self.stack = self.previousStack
                else:
                    if not preserveStack:
                        if list_:
                            result = list(result)
                        if iterate:
                            for i in result:
                                self.stack.append(i)
                        else:
                            self.stack.append(result)


def stdin():
    calc = Calculation()

    for command in sys.stdin.read().split():
        try:
            calc.do(command)
        except EOFError:
            break
    if len(calc.stack):
        calc.printStack(-1)


def repl():
    calc = Calculation()

    while True:
        try:
            calc.do(input('--> '))
        except KeyboardInterrupt:
            print()
        except EOFError:
            break


if __name__ == '__main__':
    importCallables(math)
    importCallables(operator)
    importCallables(builtins)
    importCallables(functools)
    addSpecialCases()
    addAbbrevs()
    addVariables()
    if os.isatty(0):
        repl()
    else:
        stdin()
