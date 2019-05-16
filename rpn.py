#!/usr/bin/env python

import sys
import os
import math
import decimal
import builtins
import operator
import functools
import inspect
import re
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
    # Can't save readline history.
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
            ('decimal.Decimal', ('Decimal',)),
            ('math.log', ('log',)),
            ('operator.add', ('+',)),
            ('operator.eq', ('=', '==')),
            ('operator.mul', ('*',)),
            ('operator.ne', ('!=',)),
            ('operator.sub', ('-',)),
            ('operator.truediv', ('/', 'div')),
            ('builtins.bool', ('bool',)),
            ('builtins.int', ('int',)),
            ('builtins.map', ('map',)),
            ('builtins.max', ('max',)),
            ('builtins.min', ('min',)),
            ('builtins.print', ('print',)),
            ('builtins.range', ('range',)),
            ('builtins.str', ('str',)),
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
                else:
                    print(shortName, 'already known')


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
            (decimal, decimal.Decimal, 1),
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


def addConstants():
    """Add some constants (well, constant in theory) from math"""
    constants = [
            ('e', math.e),
            ('inf', math.inf),
            ('nan', math.nan),
            ('pi', math.pi),
    ]

    if sys.version_info > (3, 5):
        constants.append(('tau', math.tau))

    for name, value in constants:
        if name in variables:
            print('%r is already a variable!' % name, file=sys.stderr)
        else:
            variables[name] = value


def importCallables(module):
    moduleName = module.__name__
    exec('import ' + moduleName, globals(), variables)
    callables = inspect.getmembers(module, callable)

    for name, func in callables:
        if name.startswith('_'):
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

            if path in functions:
                if path != 'decimal.Decimal':
                    print('Function %r already exists' % path, file=sys.stderr)
                continue

            # Add the function to our functions dict along with a default
            # number of positional parameters it expects. This allows the
            # user to call it and have the arguments taken from the stack
            # (the number of arguments used can always be modified via
            # e.g., /3 on the command line).
            nArgs = len([p for p in sig.parameters.values() if
                         p.kind == inspect.Parameter.POSITIONAL_ONLY])
            # or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD])
            exec('functions["%s"] = Function("%s", "%s", %s, %d)' %
                 (path, moduleName, name, path, nArgs))

            # Import the function by name to allow the user to use it in a
            # command with an explicit argument, instead of applying it to
            # whatever is on the stack.
            if name in variables:
                # print('name %s already defined! Ignoring %s' % (name, path))
                pass
            else:
                exec('from %s import %s' % (moduleName, name), globals(),
                     variables)
                if name not in variables:
                    print('name %s not now defined!!!' % name)
                assert name not in functions
                functions[name] = functions[path]


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

    return command.strip(), set(modifiers.strip().lower()), count


class Calculation:
    def __init__(self):
        self.stack = []
        self.previousStack = self.previousVariables = None
        self.debug = False

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
            if self.debug:
                print('Empty command')
            return

        push_ = '!' in modifiers
        list_ = 'l' in modifiers
        forceCommand = 'c' in modifiers
        preserveStack = '=' in modifiers
        iterate = 'i' in modifiers
        # Just print the result, do not put it onto the stack.
        print_ = 'p' in modifiers

        # Test for incompatible modifiers.
        if push_:
            if print_:
                print('/p (print) makes no sense with /! (push)',
                      file=sys.stderr)
                return
            if preserveStack:
                print('/= (preserve stack) makes no sense with /! (push)',
                      file=sys.stderr)
                return

        try:
            function = functions[command]
        except KeyError:
            if self.debug:
                print('%s is not a known function' % (command,))

            lcommand = command.lower()
            if command in variables and not forceCommand:
                if push_:
                    self.saveState()
                    self.stack.append(Variable(command))
                else:
                    if print_:
                        pprint(variables[command])
                    else:
                        self.saveState()
                        self.stack.append(variables[command])
            elif lcommand == 'quit' or lcommand == 'q':
                raise EOFError()
            elif lcommand == 'pop':
                if self.stack:
                    self.saveState()
                    self.stack.pop()
                else:
                    print('Cannot pop (stack is empty)', file=sys.stderr)
            elif lcommand == 'functions':
                for name, func in sorted(functions.items()):
                    print(func)
            elif lcommand == 'stack' or lcommand == 's' or lcommand == 'f':
                self.printStack()
            elif lcommand == 'variables' or lcommand == 'v':
                for name, value in sorted(variables.items()):
                    print(name, end=': ')
                    pprint(value)
            elif lcommand == 'clear' or lcommand == 'c':
                self.saveState()
                self.stack = []
            elif lcommand == 'dup' or lcommand == 'd':
                if self.stack:
                    if preserveStack:
                        print('The /= modifier makes no sense with %s' %
                              command, file=sys.stderr)
                    elif print_:
                        print('The /p modifier makes no sense with %s' %
                              command, file=sys.stderr)
                    else:
                        self.saveState()
                        self.stack.append(self.stack[-1])
                else:
                    print('Cannot duplicate (stack is empty)',
                          file=sys.stderr)
            elif lcommand == 'undo' or lcommand == 'u':
                if self.previousStack is None:
                    print('Nothing to undo.', file=sys.stderr)
                elif preserveStack:
                    print('The /= modifier makes no sense with %s' %
                          command, file=sys.stderr)
                elif print_:
                    print('The /p modifier makes no sense with %s' %
                          command, file=sys.stderr)
                else:
                    self.stack = self.previousStack.copy()
                    variables = self.previousVariables.copy()
            elif lcommand == 'print' or lcommand == 'p':
                self.printStack(-1)
            elif lcommand == 'none':
                if print_:
                    print(None)
                else:
                    self.saveState()
                    self.stack.append(None)
            elif lcommand == 'true':
                if print_:
                    print(True)
                else:
                    self.saveState()
                    self.stack.append(True)
            elif lcommand == 'false':
                if print_:
                    print(False)
                else:
                    self.saveState()
                    self.stack.append(False)
            else:
                try:
                    value = eval(command, globals(), variables)
                except Exception as e:
                    if self.debug:
                        print('Could not eval %s: %s' % (command, e))
                        print('Trying exec.')
                    # currentVars = variables.copy()
                    self.saveState()
                    try:
                        exec(command, globals(), variables)
                    except Exception as e:
                        print('Exception: %s' % e, file=sys.stderr)
                        variables = self.previousVariables
                        self.stack = self.previousStack
                    else:
                        pass
                        # self.saveState()
                        # for var in variables:
                        #     # Add all new or changed variables.
                        #     if (var not in currentVars or
                        #             variables[var] != currentVars[var]):
                        #         if push_:
                        #             self.stack.append(Variable(var))
                        #         else:
                        #             if iterate:
                        #                 for i in variables[var]:
                        #                     self.stack.append(i)
                        #             else:
                        #                 self.stack.append(variables[var])
                else:
                    if self.debug:
                        print('eval %s worked: %r' % (command, value))
                    if list_:
                        value = list(value)
                    self.saveState()
                    if iterate:
                        for i in value:
                            if print_:
                                pprint(i)
                            else:
                                self.stack.append(i)
                    else:
                        if print_:
                            pprint(value)
                        else:
                            self.stack.append(value)
        else:
            if self.debug:
                print('Found variable', command)
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
                    if self.debug:
                        print('Calling', function.name, 'with', tuple(args))
                    result = function.func(*args)
                except Exception as e:
                    print('Exception:', e, file=sys.stderr)
                    variables = self.previousVariables
                    self.stack = self.previousStack
                else:
                    if list_:
                        result = list(result)
                    if iterate:
                        for i in result:
                            if print_:
                                pprint(i)
                            elif not preserveStack:
                                self.stack.append(i)
                    else:
                        if print_:
                            pprint(result)
                        elif not preserveStack:
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
    addSpecialCases()
    importCallables(math)
    importCallables(operator)
    importCallables(builtins)
    importCallables(functools)
    importCallables(decimal)
    addAbbrevs()
    addConstants()
    if os.isatty(0):
        repl()
    else:
        stdin()
