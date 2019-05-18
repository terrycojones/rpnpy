from __future__ import print_function, division

import sys
import inspect
import math
import decimal
import operator
import functools
from pprint import pprint

try:
    import builtins
except ImportError:
    if sys.version_info < (3,):
        print('The calculator only runs under Python 3.', file=sys.stderr)
        sys.exit(1)
    else:
        raise

from rpnpy.io import splitInput


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
    def __init__(self, name, variables):
        self.name = name
        self._variables = variables

    def __repr__(self):
        return 'Variable(%s, current value: %r)' % (
            self.name, self._variables[self.name])


class Calculator:
    def __init__(self, outfp=sys.stdout, errfp=sys.stderr, debug=False):
        self._outfp = outfp
        self._errfp = errfp
        self._debug = debug
        self.stack = []
        self._previousStack = self._previousVariables = None
        self._functions = {}
        self._variables = {}

        self.addSpecialCases()
        for module in math, operator, builtins, functools, decimal:
            self.importCallables(module)
        self.addAbbrevs()
        self.addConstants()

    def __len__(self):
        return len(self.stack)

    def report(self, *args, **kw):
        print(*args, file=self._outfp, **kw)

    def err(self, *args, **kw):
        print(*args, file=self._errfp, **kw)

    def debug(self, *args, **kw):
        if self._debug:
            print(*args, file=self._errfp, **kw)

    def pprint(self, *args, **kw):
        pprint(*args, stream=self._outfp, **kw)

    def register(self, moduleName, name, func, nArgs):
        if name in self._functions:
            self.debug('Registering new functionality for already known '
                       'function named %r.' % name)
        self._functions[name] = Function(moduleName, name, func, nArgs)

    def addAbbrevs(self):
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
                function = self._functions[longName]
            except KeyError:
                self.err('Long function name %r is unknown' % longName)
            else:
                for shortName in shortNames:
                    if shortName not in self._functions:
                        # self.err('Long name %r alias %r' %
                        # (longName, shortName))
                        self._functions[shortName] = function
                    else:
                        self.report(shortName, 'already known')

    def addSpecialCases(self):
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
                self._functions[longName]
            except KeyError:
                self._functions[longName] = Function(
                    module.__name__, func.__name__, func, nArgs)
            else:
                self.err('Long function name %r is already set' % longName)

    def addConstants(self):
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
            if name in self._variables:
                self.err('%r is already a variable!' % name)
            else:
                self._variables[name] = value

    def importCallables(self, module):
        moduleName = module.__name__
        exec('import ' + moduleName, globals(), self._variables)
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
                # self.err('Could not get signature for', path)
                pass
            else:

                if path in self._functions:
                    if path != 'decimal.Decimal':
                        self.err('Function %r already exists' % path)
                    continue

                # Add the function to our functions dict along with a default
                # number of positional parameters it expects. This allows the
                # user to call it and have the arguments taken from the stack
                # (the number of arguments used can always be modified via
                # e.g., /3 on the command line).
                nArgs = len([p for p in sig.parameters.values() if
                             p.kind == inspect.Parameter.POSITIONAL_ONLY])
                exec('self._functions["%s"] = Function("%s", "%s", %s, %d)' %
                     (path, moduleName, name, path, nArgs))

                # Import the function by name to allow the user to use it in a
                # command with an explicit argument, instead of applying it to
                # whatever is on the stack.
                if name in self._variables:
                    self.debug('name %s already defined! Ignoring %s' %
                               (name, path))
                else:
                    exec('from %s import %s' % (moduleName, name), globals(),
                         self._variables)
                    if name not in self._variables:
                        self.err('name %s not now defined!!!' % name)
                    assert name not in self._functions
                    self._functions[name] = self._functions[path]

    def printStack(self, n=None):
        """
        Print the stack or some item(s) from it.

        @param n: Either an C{int} or a slice specifying what part
            of the stack to print.
        """
        if n is None:
            pprint(self.stack)
        else:
            try:
                pprint(self.stack[n])
            except IndexError:
                self.err(
                    'Cannot print stack item %d (stack has only %d item%s)' %
                    (n, len(self), '' if len(self) == 1 else 's'))

    def saveState(self):
        self._previousStack = self.stack.copy()
        self._previousVariables = self._variables.copy()

    def _finalize(self, result, list_, print_, iterate, preserveStack,
                  stateAlreadySaved=False):
        """
        """
        if list_:
            result = list(result)
        if iterate:
            if print_:
                for i in result:
                    self.report(i)
            elif not preserveStack:
                if not stateAlreadySaved:
                    self.saveState()
                self.stack.extend(result)
        else:
            if print_:
                self.report(result)
            elif not preserveStack:
                if not stateAlreadySaved:
                    self.saveState()
                self.stack.append(result)

    def execute(self, command):

        command, modifiers, count = splitInput(command)

        if not command:
            self.debug('Empty command')
            return

        push_ = '!' in modifiers
        list_ = 'l' in modifiers
        forceCommand = 'c' in modifiers
        preserveStack = '=' in modifiers
        iterate = 'i' in modifiers
        # Just print the result, do not put it onto the stack.
        print_ = 'p' in modifiers
        all_ = '*' in modifiers

        # Test for incompatible modifiers.
        if push_:
            if preserveStack:
                self.err('/= (preserve stack) makes no sense with /! (push)')
                return

        try:
            function = self._functions[command]
        except KeyError:
            self.debug('%s is not a known function' % (command,))

            lcommand = command.lower()
            if command in self._variables and not forceCommand:
                if push_:
                    self._finalize(Variable(command, self._variables),
                                   list_, print_, iterate, preserveStack)
                else:
                    self._finalize(self._variables[command],
                                   list_, print_, iterate, preserveStack)
            elif lcommand == 'quit' or lcommand == 'q':
                raise EOFError()
            elif lcommand == 'pop':
                if self.stack:
                    self.saveState()
                    result = self.stack.pop()
                    if print_:
                        self.report(result)
                else:
                    self.err('Cannot pop (stack is empty)')
            elif lcommand == 'functions':
                for name, func in sorted(self._functions.items()):
                    self.report(name, func)
            elif lcommand == 'stack' or lcommand == 's' or lcommand == 'f':
                self.printStack()
            elif lcommand == 'variables' or lcommand == 'v':
                for name, value in sorted(self._variables.items()):
                    self.report('%s: %r' % (name, value))
            elif lcommand == 'clear' or lcommand == 'c':
                self.saveState()
                self.stack = []
            elif lcommand == 'dup' or lcommand == 'd':
                if self.stack:
                    if preserveStack:
                        self.err('The /= modifier makes no sense with %s' %
                                 command)
                    else:
                        self._finalize(self.stack[-1],
                                       list_, print_, iterate, preserveStack)
                else:
                    self.err('Cannot duplicate (stack is empty)')
            elif lcommand == 'undo' or lcommand == 'u':
                if self._previousStack is None:
                    self.err('Nothing to undo.')
                elif preserveStack:
                    self.err('The /= modifier makes no sense with %s' %
                             command)
                elif print_:
                    self.err('The /p modifier makes no sense with %s' %
                             command)
                else:
                    self.stack = self._previousStack.copy()
                    self._variables = self._previousVariables.copy()
            elif lcommand == 'print' or lcommand == 'p':
                self.printStack(-1)
            elif lcommand == 'none':
                self._finalize(None, list_, print_, iterate, preserveStack)
            elif lcommand == 'true':
                self._finalize(True, list_, print_, iterate, preserveStack)
            elif lcommand == 'false':
                self._finalize(False, list_, print_, iterate, preserveStack)
            else:
                try:
                    value = eval(command, globals(), self._variables)
                except Exception as e:
                    self.debug('Could not eval(%r): %s' % (command, e))
                    self.saveState()
                    try:
                        exec(command, globals(), self._variables)
                    except Exception as e:
                        self.err('Could not exec(%r): %s' % (command, e))
                        self._variables = self._previousVariables
                        self.stack = self._previousStack
                    else:
                        self.debug('exec worked.')
                else:
                    self.debug('eval %s worked: %r' % (command, value))
                    self._finalize(value, list_, print_, iterate,
                                   preserveStack)
        else:
            self.debug('Found function %r' % command)
            if count is None:
                nArgs = len(self) if all_ else function.nArgs
            else:
                nArgs = int(count)
                if all_:
                    if len(self) != nArgs:
                        self.err('/modifiers cannot have both a count and a *')
                        return

            if push_:
                self._finalize(function.func, list_, print_, iterate,
                               preserveStack)
            elif len(self) < function.nArgs:
                self.err(
                    'Not enough args on stack! (%s needs %d arg%s, stack has '
                    '%d item%s)' %
                    (command, nArgs, '' if nArgs == 1 else 's',
                     len(self), '' if len(self) == 1 else 's'))
            else:
                args = []
                for arg in self.stack[-nArgs:]:
                    if isinstance(arg, Function):
                        args.append(arg.func)
                    elif isinstance(arg, Variable):
                        args.append(self._variables[arg.name])
                    else:
                        args.append(arg)

                if not preserveStack:
                    self.saveState()
                    self.stack = self.stack[:-nArgs]

                try:
                    self.debug('Calling %s with %r' % (function.name,
                                                       tuple(args)))
                    result = function.func(*args)
                except Exception as e:
                    self.err('Exception:', e)
                    self._variables = self._previousVariables
                    self.stack = self._previousStack
                else:
                    self._finalize(
                        result, list_, print_, iterate, preserveStack,
                        stateAlreadySaved=(not preserveStack))
